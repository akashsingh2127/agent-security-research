"""FastAPI application factory and middleware configuration.

Handles request correlation IDs and safe exception handling.
"""

import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from target_app.database import init_db
from target_app.routes.health import router as health_router
from target_app.routes.records import router as records_router
from target_app.seed import seed_database
from target_app.database import get_connection


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialize schema and seed synthetic data if needed."""
    db_path = getattr(app.state, "db_path", None)
    init_db(db_path)
    with get_connection(db_path) as conn:
        seed_database(conn)
    yield


def create_app(db_path: Optional[str] = None) -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title="Secure Synthetic Target Application",
        description="Local evaluation target for AI agent security research.",
        version="0.1.0",
        lifespan=lifespan,
    )

    if db_path is not None:
        app.state.db_path = db_path

    # Middleware: Request ID correlation
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next) -> Response:
        req_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

    # Global fallback error handler: prevents internal trace or audit leakage
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    app.include_router(health_router)
    app.include_router(records_router)

    return app


app = create_app()

