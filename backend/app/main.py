from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import configure_logging
from app.routers import connection_tests, database, health, openapi, projects, tests


def create_app() -> FastAPI:
    configure_logging()
    init_db()

    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(projects.router)
    app.include_router(openapi.router)
    app.include_router(database.router)
    app.include_router(tests.router)
    app.include_router(connection_tests.router)
    return app


app = create_app()
