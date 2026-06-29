import os
from threading import Event, Thread

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text
from app.database import Base, engine
from app.events.outbox_publisher import run_publisher_loop
from app.routes import users, meals

load_dotenv()

Base.metadata.create_all(bind=engine)

with engine.begin() as connection:
    connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)"))
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

app = FastAPI(title="NutriGuard Backend API")
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
    if allow_all_cors and origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = request_headers or "authorization, content-type"
        response.headers["Vary"] = "Origin"
    return response

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
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)

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
    return {"status": "ok"}
