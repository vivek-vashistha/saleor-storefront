from abc import ABC

from sqlalchemy.orm import Session

from backend.infrastructure.connections.interface import (
    IDatabaseConnection,
)


class IPostgresConnection(IDatabaseConnection[Session], ABC):
    """Interface for PostgreSQL database connections."""

    pass
