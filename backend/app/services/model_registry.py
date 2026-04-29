from app.core.config import settings
from app.schemas.common import ModelStatusResponse


def get_model_status() -> ModelStatusResponse:
    model_path = settings.model_path

    if not model_path.exists():
        return ModelStatusResponse(
            ok=False,
            model_path=str(model_path),
            exists=False,
            size_bytes=None,
            message="模型文件不存在，当前后端不会加载模型。",
        )

    return ModelStatusResponse(
        ok=True,
        model_path=str(model_path),
        exists=True,
        size_bytes=model_path.stat().st_size,
        message="模型文件存在；当前结构基线仅检查文件状态，不执行加载或推理。",
    )
