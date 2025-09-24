import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.infrastructure.connections import IMongoDBConnection
from backend.infrastructure.repositories.memory_repository.interface import (
    IMemoryRepository, MemoryMetadata, UserProfileData, ConsolidatedInsights
)

logger = logging.getLogger("conversational_commerce.memory_repository")


class MongoDBMemoryRepository(IMemoryRepository):
    """Repository for memory operations using MongoDB for structured data."""

    def __init__(self, connection: IMongoDBConnection):
        """Initialize the MongoDBMemoryRepository with the provided connection.

        Args:
            connection: The MongoDB connection.
        """
        self.connection = connection
        self.memory_metadata_collection = "memory_metadata"
        self.user_profiles_collection = "user_profiles"
        self.consolidated_insights_collection = "consolidated_insights"

    async def _get_memory_metadata_collection(self, db: AsyncIOMotorDatabase):
        """Get the memory metadata collection."""
        return db[self.memory_metadata_collection]

    async def _get_user_profiles_collection(self, db: AsyncIOMotorDatabase):
        """Get the user profiles collection."""
        return db[self.user_profiles_collection]

    async def _get_consolidated_insights_collection(self, db: AsyncIOMotorDatabase):
        """Get the consolidated insights collection."""
        return db[self.consolidated_insights_collection]

    async def store_memory_metadata(self, memory_metadata: MemoryMetadata) -> str:
        """Store memory metadata in MongoDB.

        Args:
            memory_metadata: The memory metadata to store

        Returns:
            The ID of the stored memory metadata
        """
        async def _store_metadata(db: AsyncIOMotorDatabase) -> str:
            collection = await self._get_memory_metadata_collection(db)
            result = await collection.insert_one(memory_metadata.model_dump())
            return str(result.inserted_id)

        return await self.connection.execute_db_operation(
            _store_metadata, "Failed to store memory metadata"
        )

    async def get_memory_metadata(self, user_id: str, memory_type: Optional[str] = None) -> List[MemoryMetadata]:
        """Get memory metadata for a user.

        Args:
            user_id: The user's ID
            memory_type: Optional memory type filter

        Returns:
            List of memory metadata
        """
        async def _get_metadata(db: AsyncIOMotorDatabase) -> List[MemoryMetadata]:
            collection = await self._get_memory_metadata_collection(db)
            
            query = {"user_id": user_id}
            if memory_type:
                query["memory_type"] = memory_type
            
            cursor = collection.find(query).sort("created_at", -1)
            metadata_list = []
            
            async for document in cursor:
                metadata_list.append(MemoryMetadata.model_validate(document))
            
            return metadata_list

        return await self.connection.execute_db_operation(
            _get_metadata, f"Failed to get memory metadata for user {user_id}"
        )

    async def update_memory_access(self, memory_id: str) -> None:
        """Update memory access information.

        Args:
            memory_id: The memory metadata ID
        """
        async def _update_access(db: AsyncIOMotorDatabase) -> None:
            collection = await self._get_memory_metadata_collection(db)
            await collection.update_one(
                {"_id": ObjectId(memory_id)},
                {
                    "$set": {"last_accessed": datetime.now()},
                    "$inc": {"access_count": 1}
                }
            )

        await self.connection.execute_db_operation(
            _update_access, f"Failed to update memory access for {memory_id}"
        )

    async def store_user_profile(self, user_profile: UserProfileData) -> str:
        """Store or update user profile data.

        Args:
            user_profile: The user profile data

        Returns:
            The ID of the stored user profile
        """
        async def _store_profile(db: AsyncIOMotorDatabase) -> str:
            collection = await self._get_user_profiles_collection(db)
            
            # Use upsert to update or create
            result = await collection.replace_one(
                {"user_id": user_profile.user_id},
                user_profile.model_dump(),
                upsert=True
            )
            
            if result.upserted_id:
                return str(result.upserted_id)
            else:
                # Find the existing document
                existing = await collection.find_one({"user_id": user_profile.user_id})
                return str(existing["_id"])

        return await self.connection.execute_db_operation(
            _store_profile, f"Failed to store user profile for {user_profile.user_id}"
        )

    async def get_user_profile(self, user_id: str) -> Optional[UserProfileData]:
        """Get user profile data.

        Args:
            user_id: The user's ID

        Returns:
            User profile data if found, None otherwise
        """
        async def _get_profile(db: AsyncIOMotorDatabase) -> Optional[UserProfileData]:
            collection = await self._get_user_profiles_collection(db)
            document = await collection.find_one({"user_id": user_id})
            
            if document:
                return UserProfileData.model_validate(document)
            return None

        return await self.connection.execute_db_operation(
            _get_profile, f"Failed to get user profile for {user_id}"
        )

    async def store_consolidated_insights(self, insights: ConsolidatedInsights) -> str:
        """Store consolidated memory insights.

        Args:
            insights: The consolidated insights

        Returns:
            The ID of the stored insights
        """
        async def _store_insights(db: AsyncIOMotorDatabase) -> str:
            collection = await self._get_consolidated_insights_collection(db)
            
            # Use upsert to update or create
            result = await collection.replace_one(
                {"user_id": insights.user_id},
                insights.model_dump(),
                upsert=True
            )
            
            if result.upserted_id:
                return str(result.upserted_id)
            else:
                # Find the existing document
                existing = await collection.find_one({"user_id": insights.user_id})
                return str(existing["_id"])

        return await self.connection.execute_db_operation(
            _store_insights, f"Failed to store consolidated insights for {insights.user_id}"
        )

    async def get_consolidated_insights(self, user_id: str) -> Optional[ConsolidatedInsights]:
        """Get consolidated memory insights.

        Args:
            user_id: The user's ID

        Returns:
            Consolidated insights if found, None otherwise
        """
        async def _get_insights(db: AsyncIOMotorDatabase) -> Optional[ConsolidatedInsights]:
            collection = await self._get_consolidated_insights_collection(db)
            document = await collection.find_one({"user_id": user_id})
            
            if document:
                return ConsolidatedInsights.model_validate(document)
            return None

        return await self.connection.execute_db_operation(
            _get_insights, f"Failed to get consolidated insights for {user_id}"
        )

    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics for a user.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary containing memory statistics
        """
        async def _get_stats(db: AsyncIOMotorDatabase) -> Dict[str, Any]:
            collection = await self._get_memory_metadata_collection(db)
            
            # Get total count
            total_memories = await collection.count_documents({"user_id": user_id})
            
            # Get count by type
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": "$memory_type", "count": {"$sum": 1}}}
            ]
            type_counts = {}
            async for doc in collection.aggregate(pipeline):
                type_counts[doc["_id"]] = doc["count"]
            
            # Get recent activity
            recent_memories = await collection.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)}
            })
            
            return {
                "total_memories": total_memories,
                "type_counts": type_counts,
                "recent_memories": recent_memories,
                "last_updated": datetime.now()
            }

        return await self.connection.execute_db_operation(
            _get_stats, f"Failed to get memory stats for {user_id}"
        )

    async def delete_old_memories(self, user_id: str, days_old: int = 90) -> int:
        """Delete old memories for a user.

        Args:
            user_id: The user's ID
            days_old: Number of days old to consider for deletion

        Returns:
            Number of memories deleted
        """
        async def _delete_old(db: AsyncIOMotorDatabase) -> int:
            collection = await self._get_memory_metadata_collection(db)
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            result = await collection.delete_many({
                "user_id": user_id,
                "created_at": {"$lt": cutoff_date}
            })
            
            return result.deleted_count

        return await self.connection.execute_db_operation(
            _delete_old, f"Failed to delete old memories for {user_id}"
        )
