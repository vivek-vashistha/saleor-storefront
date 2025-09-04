import logging
from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.domain.entities import ChatSession
from backend.infrastructure.connections import IMongoDBConnection
from backend.infrastructure.repositories.chat_session_repository.interface import IChatSessionRepository

logger = logging.getLogger("conversational_commerce")


class MongoDBChatSessionRepository(IChatSessionRepository):
    """Repository for chat session operations using MongoDB."""

    def __init__(self, connection: IMongoDBConnection):
        """Initialize the MongoDBChatSessionRepository with the provided connection.

        Args:
            connection: The MongoDB connection.
        """
        self.connection = connection
        self.collection_name = "chat_sessions"

    async def _get_collection(self, db: AsyncIOMotorDatabase):
        """Get the collection for chat sessions.

        Args:
            db: The database connection

        Returns:
            The chat sessions collection
        """
        return db[self.collection_name]

    async def create_session(self, session: ChatSession) -> ChatSession:
        """Create a new chat session.

        Args:
            session: The chat session to create

        Returns:
            The created chat session with its ID
        """

        async def _create_session(db: AsyncIOMotorDatabase) -> ChatSession:
            # Set creation time
            session_dict = session.to_dict()
            session_dict["created_at"] = datetime.now()
            session_dict["updated_at"] = datetime.now()

            collection = await self._get_collection(db)
            result = await collection.insert_one(session_dict)

            # Set the ID on the session
            session.id = str(result.inserted_id)
            return session

        return await self.connection.execute_db_operation(_create_session, "Failed to create chat session")

    async def get_session(self, session_id: str) -> ChatSession | None:
        """Get a chat session by its ID.

        Args:
            session_id: The ID of the chat session to retrieve

        Returns:
            The chat session if found, None otherwise
        """

        async def _get_session(db: AsyncIOMotorDatabase) -> ChatSession | None:
            collection = await self._get_collection(db)
            result = await collection.find_one({"_id": ObjectId(session_id)})

            if result:
                return ChatSession.from_dict(result)
            return None

        return await self.connection.execute_db_operation(
            _get_session, f"Failed to get chat session with ID {session_id}"
        )

    async def update_session(self, session: ChatSession) -> ChatSession:
        """Update an existing chat session.

        Args:
            session: The chat session to update

        Returns:
            The updated chat session
        """
        if not session.id:
            raise ValueError("Session ID is required for update")

        async def _update_session(db: AsyncIOMotorDatabase) -> ChatSession:
            session_dict = session.model_dump()
            session_dict["updated_at"] = datetime.now()

            collection = await self._get_collection(db)
            await collection.update_one({"_id": ObjectId(session.id)}, {"$set": session_dict})

            return session

        return await self.connection.execute_db_operation(
            _update_session, f"Failed to update chat session with ID {session.id}"
        )

    async def delete_session(self, session_id: str) -> bool:
        """Delete a chat session.

        Args:
            session_id: The ID of the chat session to delete

        Returns:
            True if the session was deleted, False otherwise
        """

        async def _delete_session(db: AsyncIOMotorDatabase) -> bool:
            collection = await self._get_collection(db)
            result = await collection.delete_one({"_id": ObjectId(session_id)})
            return result.deleted_count > 0

        return await self.connection.execute_db_operation(
            _delete_session, f"Failed to delete chat session with ID {session_id}"
        )

    async def get_user_sessions(self, user_id: str) -> list[ChatSession]:
        """Get all chat sessions for a user.

        Args:
            user_id: The ID of the user

        Returns:
            A list of chat sessions for the user
        """

        async def _get_user_sessions(db: AsyncIOMotorDatabase) -> list[ChatSession]:
            collection = await self._get_collection(db)
            cursor = collection.find({"user_id": user_id})
            sessions = []

            async for document in cursor:
                sessions.append(ChatSession.from_dict(document))

            return sessions

        return await self.connection.execute_db_operation(
            _get_user_sessions, f"Failed to get chat sessions for user {user_id}"
        )
