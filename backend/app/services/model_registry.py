from app.core.config import settings
from app.schemas.common import ModelStatusResponse


def get_model_status() -> ModelStatusResponse:
    model_path = settings.model_path

    return ModelStatusResponse(
        ok=True,
        model_path=str(model_path),
        exists=model_path.exists(),
        size_bytes=model_path.stat().st_size if model_path.exists() else None,
        message="本地 CNN 模型仅作为 legacy 资料记录，新系统预测不加载该文件。",
    )
