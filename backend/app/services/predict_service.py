from app.providers.vision_provider import (
    ProviderNotConfiguredError,
    VisionProviderError,
    get_enabled_vision_provider,
)
from app.schemas.predict import PredictResponse


class InvalidImageError(ValueError):
    pass


class PredictionService:
    async def predict(self, image_bytes: bytes, filename: str, content_type: str) -> PredictResponse:
        if not image_bytes:
            raise InvalidImageError("请上传一张图片")

        provider = get_enabled_vision_provider()
        return await provider.predict(
            image_bytes=image_bytes,
            filename=filename,
            content_type=content_type,
        )


_prediction_service = PredictionService()


def get_prediction_service() -> PredictionService:
    return _prediction_service
