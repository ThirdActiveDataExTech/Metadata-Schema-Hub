import logging

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel

from app.config import settings

connect_args = {"check_same_thread": False}
sqlite_url: str = f"sqlite:///{settings.SQLITE_FILE_NAME}"
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    """Create db and tables."""
    try:
        SQLModel.metadata.create_all(engine)
    except SQLAlchemyError as e:
        logging.error(f"Database initialization failed while creating tables: {e}")
        raise
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        raise
