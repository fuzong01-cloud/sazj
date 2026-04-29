from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    disease_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    suggestions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_content_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
