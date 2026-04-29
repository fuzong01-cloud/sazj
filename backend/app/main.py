from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.advice import router as advice_router
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.model import router as model_router
from app.api.model_configs import router as model_configs_router
from app.api.predict import router as predict_router
from app.core.config import settings


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
    app.include_router(model_router, prefix=settings.api_prefix)
    app.include_router(model_configs_router, prefix=settings.api_prefix)
    app.include_router(predict_router, prefix=settings.api_prefix)
    app.include_router(advice_router, prefix=settings.api_prefix)
    app.include_router(chat_router, prefix=settings.api_prefix)

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
