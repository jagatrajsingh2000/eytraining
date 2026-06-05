from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.orders import router as orders_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="E-Commerce Order Management API",
        description="A simple FastAPI project for managing e-commerce orders.",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(orders_router)
    return app


app = create_app()
