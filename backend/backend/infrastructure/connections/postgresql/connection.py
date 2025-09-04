import logging
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any

import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.infrastructure.connections.postgresql.config import PostgreSQLConfig
from backend.infrastructure.connections.postgresql.interface import IPostgresConnection

logger = logging.getLogger("conversational_commerce")


class PostgreSQLConnection(IPostgresConnection):
    """A class for establishing a connection to a PostgreSQL database."""

    def __init__(self, config: PostgreSQLConfig):
        """Initialize the PostgreSQLConnection with the provided configuration.

        Args:
            config: The PostgreSQL configuration.
        """
        self.config = config
        self.engine = sqlalchemy.create_engine(
            self.config.get_connection_string(),
            pool_size=5,
            max_overflow=2,
            pool_recycle=1800,  # maximum number of seconds a connection can persist
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    @contextmanager
    def get_connection(self) -> Generator[Session, None, None]:
        """A context manager for managing database connections.

        Yields:
            Session: A SQLAlchemy session.
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            session.close()

    def execute_db_operation(
        self, operation: Callable[[Session], Any], error_message: str = "Database operation error"
    ) -> Any:
        """Execute a database operation within a session and handle any errors.

        Args:
            operation: The database operation to execute.
            error_message: The error message to display if the operation fails.

        Returns:
            The result of the database operation.

        Raises:
            Exception: If the database operation fails.
        """
        try:
            with self.get_connection() as session:
                return operation(session)
        except SQLAlchemyError as e:
            logger.error(f"{error_message}: {str(e)}")
            raise Exception(f"{error_message}: {str(e)}") from e
