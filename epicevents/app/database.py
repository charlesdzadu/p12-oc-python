from sqlmodel import SQLModel, Session, create_engine
from contextlib import contextmanager
from typing import Generator
from .config import settings


engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)


def create_db_and_tables():
    # Import all models to ensure relationships are properly defined
    from .auth.models import User, Department
    from .models import Client, Contract, Event

    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def init_database():
    create_db_and_tables()
