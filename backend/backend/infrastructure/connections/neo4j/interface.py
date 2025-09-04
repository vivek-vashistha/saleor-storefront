from abc import ABC

from neo4j import Driver

from backend.infrastructure.connections.interface import (
    IDatabaseConnection,
)


class INeo4jConnection(IDatabaseConnection[Driver], ABC):
    """Interface for Neo4j graph database connections."""

    pass
