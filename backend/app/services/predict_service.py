from app.providers.vision_provider import (
    ProviderNotConfiguredError,
    VisionProviderError,
    get_enabled_vision_provider,
)
from app.repositories.prediction_record_repository import create_prediction_record
from app.schemas.predict import PredictResponse
from app.schemas.prediction_record import PredictionRecordCreate
from app.schemas.weather import WeatherContext


class InvalidImageError(ValueError):
    pass


class PredictionService:
    async def predict(
        self,
        image_bytes: bytes,
        filename: str,
        content_type: str,
        user_id: int | None = None,
        prompt: str | None = None,
        deep_thinking: bool = False,
        weather: WeatherContext | None = None,
        provider_id: int | None = None,
    ) -> PredictResponse:
        if not image_bytes:
            raise InvalidImageError("请上传一张图片")

        provider = get_enabled_vision_provider(provider_id, deep_thinking=deep_thinking)
        result = await provider.predict(
            image_bytes=image_bytes,
            filename=filename,
            content_type=content_type,
            user_prompt=prompt,
            deep_thinking=deep_thinking,
            weather=weather,
        )
        record = create_prediction_record(
            PredictionRecordCreate(
                user_id=user_id,
                provider_name=result.provider_name,
                model_name=result.model_name,
                disease_name=result.disease_name,
                risk_level=result.risk_level,
                confidence=result.confidence,
                confidence_percent=result.confidence_percent,
                summary=result.summary,
                suggestions=result.suggestions,
                raw_text=result.raw_text,
                image_filename=filename or None,
                image_content_type=content_type or None,
            )
        )
        return result.model_copy(update={"record_id": record.id})


_prediction_service = PredictionService()


def get_prediction_service() -> PredictionService:
    return _prediction_service
