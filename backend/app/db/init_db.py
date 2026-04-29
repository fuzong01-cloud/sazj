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
    _ensure_model_configs_user_id()
    _ensure_users_profile_columns()


def _ensure_prediction_records_user_id() -> None:
    _ensure_nullable_integer_column("prediction_records", "user_id")


def _ensure_model_configs_user_id() -> None:
    _ensure_nullable_integer_column("model_configs", "user_id")


def _ensure_users_profile_columns() -> None:
    _ensure_nullable_text_column("users", "email", "VARCHAR(120)")
    _ensure_nullable_text_column("users", "avatar_url", "VARCHAR(500)")


def _ensure_nullable_integer_column(table_name: str, column_name: str) -> None:
    _ensure_nullable_text_column(table_name, column_name, "INTEGER")


def _ensure_nullable_text_column(table_name: str, column_name: str, column_type: str) -> None:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name in columns:
        return

    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
