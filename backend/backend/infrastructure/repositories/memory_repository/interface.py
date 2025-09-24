from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MemoryMetadata(BaseModel):
    """Schema for memory metadata stored in MongoDB."""
    user_id: str
    session_id: Optional[str] = None
    memory_type: str  # "user_preference", "product_interaction", "conversation_theme"
    content: Dict[str, Any]
    qdrant_vector_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    importance_score: float = 0.5
    confidence: float = 1.0


class UserProfileData(BaseModel):
    """Schema for user profile data in MongoDB."""
    user_id: str
    basic_info: Dict[str, Any] = {}
    preferences: Dict[str, Any] = {}
    semantic_context: Dict[str, Any] = {}
    memory_stats: Dict[str, Any] = {}
    last_updated: datetime = Field(default_factory=datetime.now)


class ConsolidatedInsights(BaseModel):
    """Schema for consolidated memory insights."""
    user_id: str
    consolidated_patterns: Dict[str, Any] = {}
    memory_summary: str = ""
    last_updated: datetime = Field(default_factory=datetime.now)
    confidence_score: float = 0.0


class IMemoryRepository(ABC):
    """Interface for memory repository operations."""

    @abstractmethod
    async def store_memory_metadata(self, memory_metadata: MemoryMetadata) -> str:
        """Store memory metadata in the repository.

        Args:
            memory_metadata: The memory metadata to store

        Returns:
            The ID of the stored memory metadata
        """
        pass

    @abstractmethod
    async def get_memory_metadata(self, user_id: str, memory_type: Optional[str] = None) -> List[MemoryMetadata]:
        """Get memory metadata for a user.

        Args:
            user_id: The user's ID
            memory_type: Optional memory type filter

        Returns:
            List of memory metadata
        """
        pass

    @abstractmethod
    async def update_memory_access(self, memory_id: str) -> None:
        """Update memory access information.

        Args:
            memory_id: The memory metadata ID
        """
        pass

    @abstractmethod
    async def store_user_profile(self, user_profile: UserProfileData) -> str:
        """Store or update user profile data.

        Args:
            user_profile: The user profile data

        Returns:
            The ID of the stored user profile
        """
        pass

    @abstractmethod
    async def get_user_profile(self, user_id: str) -> Optional[UserProfileData]:
        """Get user profile data.

        Args:
            user_id: The user's ID

        Returns:
            User profile data if found, None otherwise
        """
        pass

    @abstractmethod
    async def store_consolidated_insights(self, insights: ConsolidatedInsights) -> str:
        """Store consolidated memory insights.

        Args:
            insights: The consolidated insights

        Returns:
            The ID of the stored insights
        """
        pass

    @abstractmethod
    async def get_consolidated_insights(self, user_id: str) -> Optional[ConsolidatedInsights]:
        """Get consolidated memory insights.

        Args:
            user_id: The user's ID

        Returns:
            Consolidated insights if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics for a user.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary containing memory statistics
        """
        pass

    @abstractmethod
    async def delete_old_memories(self, user_id: str, days_old: int = 90) -> int:
        """Delete old memories for a user.

        Args:
            user_id: The user's ID
            days_old: Number of days old to consider for deletion

        Returns:
            Number of memories deleted
        """
        pass
