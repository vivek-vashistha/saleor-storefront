from abc import ABC

from qdrant_client import QdrantClient

from backend.infrastructure.connections.interface import (
    IDatabaseConnection,
)


class IQdrantConnection(IDatabaseConnection[QdrantClient], ABC):
    """Interface for Qdrant vector database connections."""

    pass
