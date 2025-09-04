import logging
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from qdrant_client.http.exceptions import UnexpectedResponse

from backend.domain.entities import EmbeddingModel
from backend.infrastructure.connections.qdrant.config import QdrantConfig
from backend.infrastructure.connections.qdrant.interface import IQdrantConnection

logger = logging.getLogger("conversational_commerce")


class QdrantConnection(IQdrantConnection):
    """A class for establishing a connection to a Qdrant vector database."""

    def __init__(self, config: QdrantConfig, embeddings_model: EmbeddingModel):
        """Initialize the QdrantConnection with the provided configuration.

        Args:
            config: The Qdrant configuration.
            embeddings_model: The embeddings model to use for vector embedding.

        """
        self.config = config
        client = QdrantClient(
            url=self.config.get_connection_url(),
            api_key=self.config.api_key,
            prefer_grpc=self.config.prefer_grpc,
            timeout=self.config.timeout,
        )
        self._ensure_collection_exists(client, config.collection_name, config.vector_size)

        self.store = QdrantVectorStore(
            client=client, collection_name=config.collection_name, embedding=embeddings_model.model
        )

    @staticmethod
    def _ensure_collection_exists(client: QdrantClient, collection_name: str, vector_size: int):
        """Create the Qdrant collection if it doesn't exist."""
        collections = client.get_collections().collections
        collection_names = [collection.name for collection in collections]

        if collection_name not in collection_names:
            logger.info(f"Creating collection {collection_name}")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=rest.VectorParams(size=vector_size, distance=rest.Distance.COSINE),
            )

    @contextmanager
    def get_connection(self) -> Generator[QdrantVectorStore, None, None]:
        """A context manager for managing Qdrant client connections.

        Yields:
            QdrantVectorStore: A Qdrant client.
        """
        try:
            yield self.store
        except UnexpectedResponse as e:
            logger.error(f"Qdrant error: {str(e)}")
            raise

    def execute_db_operation(
        self, operation: Callable[[QdrantClient], Any], error_message: str = "Qdrant operation error"
    ) -> Any:
        """Execute a Qdrant operation and handle any errors.

        Args:
            operation: The Qdrant operation to execute.
            error_message: The error message to display if the operation fails.

        Returns:
            The result of the Qdrant operation.

        Raises:
            Exception: If the Qdrant operation fails.
        """
        try:
            with self.get_connection() as client:
                return operation(client)
        except Exception as e:
            logger.error(f"{error_message}: {str(e)}")
            raise Exception(f"{error_message}: {str(e)}") from e
