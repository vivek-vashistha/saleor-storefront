from abc import ABC

from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.infrastructure.connections.interface import IDatabaseConnection


class IMongoDBConnection(IDatabaseConnection[AsyncIOMotorDatabase], ABC):
    """Interface for MongoDB connection."""

    pass
