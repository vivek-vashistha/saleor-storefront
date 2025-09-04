import logging
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any

import neo4j
from neo4j import Driver

from backend.infrastructure.connections.neo4j.config import Neo4jConfig
from backend.infrastructure.connections.neo4j.interface import INeo4jConnection

logger = logging.getLogger("conversational_commerce")


class Neo4jConnection(INeo4jConnection):
    """A class for establishing a connection to a Neo4j graph database."""

    def __init__(self, config: Neo4jConfig):
        """Initialize the Neo4jConnection with the provided configuration.

        Args:
            config: The Neo4j configuration.

        """
        self.config = config
        self.driver = neo4j.GraphDatabase.driver(
            self.config.get_connection_url(),
            auth=(self.config.username, self.config.password),
        )

    @contextmanager
    def get_connection(self) -> Generator[Driver, None, None]:
        """A context manager for managing Neo4j driver connections.

        Yields:
            Driver: A Neo4j driver.
        """
        try:
            yield self.driver
        except Exception as e:
            logger.error(f"Neo4j error: {str(e)}")
            raise

    def execute_db_operation(
        self, operation: Callable[[Driver], Any], error_message: str = "Neo4j operation error"
    ) -> Any:
        """Execute a Neo4j operation and handle any errors.

        Args:
            operation: The Neo4j operation to execute.
            error_message: The error message to display if the operation fails.

        Returns:
            The result of the Neo4j operation.

        Raises:
            Exception: If the Neo4j operation fails.
        """
        try:
            with self.get_connection() as driver:
                return operation(driver)
        except Exception as e:
            logger.error(f"{error_message}: {str(e)}")
            raise Exception(f"{error_message}: {str(e)}") from e

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()
