from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.advice import router as advice_router
from app.api.admin_providers import router as admin_providers_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.history import router as history_router
from app.api.model import router as model_router
from app.api.model_configs import router as model_configs_router
from app.api.predict import router as predict_router
from app.api.weather import router as weather_router
from app.core.config import settings
from app.core.crypto import CryptoError
from app.core.runtime import configure_logging
from app.db.init_db import create_db_and_tables


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.3.0",
        description="薯安智检 API 驱动后端，识别和问答均通过用户配置的外部模型提供商完成。",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(model_router, prefix=settings.api_prefix)
    app.include_router(model_configs_router, prefix=settings.api_prefix)
    app.include_router(predict_router, prefix=settings.api_prefix)
    app.include_router(history_router, prefix=settings.api_prefix)
    app.include_router(advice_router, prefix=settings.api_prefix)
    app.include_router(chat_router, prefix=settings.api_prefix)
    app.include_router(weather_router, prefix=settings.api_prefix)
    app.include_router(admin_providers_router)

    @app.exception_handler(CryptoError)
    def crypto_error_handler(_request, exc: CryptoError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "message": str(exc)},
        )

    @app.on_event("startup")
    def on_startup() -> None:
        configure_logging()
        if settings.auto_create_tables:
            create_db_and_tables()

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "status": "ok",
            "docs": "/docs",
            "health": f"{settings.api_prefix}/health",
        }

    return app


app = create_app()
