import logging
import os
import time
from threading import Event, Thread
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.database import Base, SessionLocal, engine
from app.events.outbox_publisher import run_publisher_loop
from app.models import MetricEvent, User
from app.rate_limiter import limiter
from app.routes import admin, users, meals, notifications

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("nutriguard.backend")

Base.metadata.create_all(bind=engine)

with engine.begin() as connection:
    connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)"))
    connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false"))
    connection.execute(text("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS goals JSON"))
    connection.execute(text("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS deficiencies JSON"))
    connection.execute(text("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS health_conditions_text TEXT"))
    connection.execute(text("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS deficiencies_text TEXT"))
    connection.execute(text("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS health_report_text TEXT"))
    connection.execute(text("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS health_report_filename VARCHAR(255)"))
    connection.execute(text("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS supplements_text TEXT"))
    connection.execute(text("ALTER TABLE meal_logs ADD COLUMN IF NOT EXISTS foods_text TEXT"))
    connection.execute(text("ALTER TABLE meal_logs ADD COLUMN IF NOT EXISTS drinks_text TEXT"))
    connection.execute(text("ALTER TABLE meal_logs ADD COLUMN IF NOT EXISTS supplements_text TEXT"))
    connection.execute(text("ALTER TABLE meal_logs ADD COLUMN IF NOT EXISTS notes_text TEXT"))
    connection.execute(text("ALTER TABLE meal_logs ADD COLUMN IF NOT EXISTS meal_type VARCHAR(50)"))
    connection.execute(text("ALTER TABLE meal_logs ADD COLUMN IF NOT EXISTS meal_time TIMESTAMP WITH TIME ZONE"))
    connection.execute(text("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'unread'"))
    connection.execute(text("ALTER TABLE report_feedback ADD COLUMN IF NOT EXISTS category VARCHAR(40) DEFAULT 'suggestions'"))
    connection.execute(text("ALTER TABLE report_feedback ADD COLUMN IF NOT EXISTS source VARCHAR(40) DEFAULT 'daily_report'"))
    connection.execute(text("ALTER TABLE metric_events ADD COLUMN IF NOT EXISTS source VARCHAR(80)"))
    connection.execute(text("ALTER TABLE metric_events ADD COLUMN IF NOT EXISTS payload JSON"))
    connection.execute(text("ALTER TABLE rag_eval_runs ADD COLUMN IF NOT EXISTS source VARCHAR(80) DEFAULT 'local_ragas'"))
    connection.execute(text("ALTER TABLE rag_eval_runs ADD COLUMN IF NOT EXISTS average_hit_rate FLOAT"))
    connection.execute(text("ALTER TABLE rag_eval_runs ADD COLUMN IF NOT EXISTS total_cases INTEGER DEFAULT 0"))
    connection.execute(text("ALTER TABLE rag_eval_runs ADD COLUMN IF NOT EXISTS passed_cases INTEGER DEFAULT 0"))
    connection.execute(text("ALTER TABLE rag_eval_runs ADD COLUMN IF NOT EXISTS metrics JSON"))
    connection.execute(text("UPDATE report_feedback SET category = 'suggestions' WHERE category IS NULL"))
    if engine.dialect.name == "postgresql":
        connection.execute(text("ALTER TABLE report_feedback DROP CONSTRAINT IF EXISTS uq_report_feedback_user_meal"))
        connection.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname = 'uq_report_feedback_user_meal_category'
                    ) THEN
                        ALTER TABLE report_feedback
                        ADD CONSTRAINT uq_report_feedback_user_meal_category
                        UNIQUE (user_id, meal_log_id, category);
                    END IF;
                END $$;
                """
            )
        )


def seed_admin_user():
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.email == "admin@nutrigaurd").first()
        if not admin_user:
            admin_user = User(
                name="NutriGuard Admin",
                email="admin@nutrigaurd",
                password_hash=users.hash_password("Admin123"),
                is_admin=True,
            )
            db.add(admin_user)
        else:
            admin_user.name = "NutriGuard Admin"
            admin_user.password_hash = users.hash_password("Admin123")
            admin_user.is_admin = True
        db.commit()
    finally:
        db.close()


seed_admin_user()

app = FastAPI(title="NutriGuard Backend API")

# Attach the rate limiter to app state and register the 429 handler.
# slowapi reads `app.state.limiter` to find the active limiter instance.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
publisher_stop_event = Event()
publisher_thread = None

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]
allow_all_cors = "*" in cors_origins


def add_local_cors_headers(response: Response, origin: str | None, request_headers: str | None = None):
    if origin and (allow_all_cors or origin in cors_origins):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = request_headers or "authorization, content-type"
        response.headers["Vary"] = "Origin"
    return response


def record_api_request_metric(request: Request, response: Response, duration_ms: float, request_id: str):
    if request.method == "OPTIONS" or request.url.path in {"/health", "/admin/metrics"}:
        return

    db = SessionLocal()
    try:
        db.add(
            MetricEvent(
                name="api_request",
                source="backend-api",
                payload={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("api_metric_record_failed request_id=%s", request_id)
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_cors else cors_origins,
    allow_origin_regex=".*" if allow_all_cors else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def force_local_cors_headers(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    start_time = time.perf_counter()
    logger.info(
        "request_started request_id=%s method=%s path=%s client=%s",
        request_id,
        request.method,
        request.url.path,
        request.client.host if request.client else "",
    )
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["x-request-id"] = request_id
    record_api_request_metric(request, response, duration_ms, request_id)
    logger.info(
        "request_completed request_id=%s method=%s path=%s status_code=%s duration_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return add_local_cors_headers(
        response,
        request.headers.get("origin"),
        request.headers.get("access-control-request-headers"),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )
    return add_local_cors_headers(response, request.headers.get("origin"))

app.include_router(users.router)
app.include_router(meals.router)
app.include_router(notifications.router)
app.include_router(admin.router)
app.include_router(admin.internal_router)


@app.on_event("startup")
def start_outbox_publisher():
    global publisher_thread
    if os.getenv("ENABLE_OUTBOX_PUBLISHER", "true").lower() != "true":
        return
    if publisher_thread and publisher_thread.is_alive():
        return

    publisher_stop_event.clear()
    publisher_thread = Thread(
        target=run_publisher_loop,
        args=(publisher_stop_event,),
        daemon=True,
    )
    publisher_thread.start()


@app.on_event("shutdown")
def stop_outbox_publisher():
    publisher_stop_event.set()
    if publisher_thread:
        publisher_thread.join(timeout=5)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "backend-api",
        "build_marker": "backend-deploy-probe-2026-07-02",
    }
