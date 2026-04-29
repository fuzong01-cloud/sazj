from sqlalchemy import inspect, text

from app.db.base import Base
from app.db.session import engine

# Import models so SQLAlchemy registers table metadata before create_all.
from app.models import model_config  # noqa: F401
from app.models import prediction_record  # noqa: F401
from app.models import user  # noqa: F401


def create_db_and_tables() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_prediction_records_user_id()


def _ensure_prediction_records_user_id() -> None:
    inspector = inspect(engine)
    if "prediction_records" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("prediction_records")}
    if "user_id" in columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE prediction_records ADD COLUMN user_id INTEGER"))
