import logging
from collections.abc import AsyncGenerator, Callable, Mapping
from contextlib import asynccontextmanager
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from backend.infrastructure.connections.mongodb.config import MongoDBConfig
from backend.infrastructure.connections.mongodb.interface import IMongoDBConnection

logger = logging.getLogger("conversational_commerce")


class MongoDBConnection(IMongoDBConnection):
    """A class for establishing a connection to a MongoDB database."""

    def __init__(self, config: MongoDBConfig):
        """Initialize the MongoDBConnection with the provided configuration.

        Args:
            config: The MongoDB configuration.
        """
        self.config = config
        self.client = AsyncIOMotorClient(
            self.config.get_connection_uri(),
            maxPoolSize=10,
            minPoolSize=1,
        )
        self.database = self.client[self.config.database]

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[AsyncIOMotorDatabase[Mapping[str, Any] | Any], None]:
        """A context manager for managing database connections.

        Yields:
            AsyncIOMotorDatabase: A MongoDB database instance.
        """
        try:
            yield self.database
        except Exception as e:
            logger.error(f"MongoDB error: {str(e)}")
            raise

    async def execute_db_operation(
        self,
        operation: Callable[[AsyncIOMotorDatabase[Mapping[str, Any]]], Any],
        error_message: str = "MongoDB operation error",
    ) -> Any:
        """Execute a MongoDB operation and handle any errors.

        Args:
            operation: The MongoDB operation to execute.
            error_message: The error message to display if the operation fails.

        Returns:
            The result of the MongoDB operation.

        Raises:
            Exception: If the MongoDB operation fails.
        """
        try:
            async with self.get_connection() as database:
                return await operation(database)
        except Exception as e:
            logger.error(f"{error_message}: {str(e)}")
            raise Exception(f"{error_message}: {str(e)}") from e
