from app.db.base import Base
from app.db.session import engine

# Import models so SQLAlchemy registers table metadata before create_all.
from app.models import model_config  # noqa: F401


def create_db_and_tables() -> None:
    Base.metadata.create_all(bind=engine)
