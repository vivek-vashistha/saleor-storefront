import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from backend.application.services.semantic_memory_service import SemanticMemoryService, SemanticMemoryConfig
from backend.application.services.background_memory_manager import BackgroundMemoryManager
from backend.infrastructure.repositories import IChatSessionRepository
from backend.domain.entities.enhanced_chat import EnhancedChatState

logger = logging.getLogger("conversational_commerce")


class GetMemoryInsightsUseCase:
    """Use case for retrieving memory insights for a user."""

    def __init__(
        self,
        background_memory_manager: BackgroundMemoryManager
    ):
        """Initialize the GetMemoryInsightsUseCase.

        Args:
            background_memory_manager: Manager for background memory processing
        """
        self.background_memory_manager = background_memory_manager

    async def execute(self, user_id: str) -> Dict[str, Any]:
        """Execute the use case to get memory insights.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary containing memory insights
        """
        try:
            insights = await self.background_memory_manager.get_memory_insights(user_id)
            logger.info(f"Retrieved memory insights for user {user_id}")
            return insights

        except Exception as e:
            logger.error(f"Error getting memory insights for user {user_id}: {e}")
            return {"status": "error", "error": str(e)}


class ConsolidateUserMemoriesUseCase:
    """Use case for consolidating user memories."""

    def __init__(
        self,
        background_memory_manager: BackgroundMemoryManager
    ):
        """Initialize the ConsolidateUserMemoriesUseCase.

        Args:
            background_memory_manager: Manager for background memory processing
        """
        self.background_memory_manager = background_memory_manager

    async def execute(self, user_id: str) -> Dict[str, Any]:
        """Execute the use case to consolidate user memories.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary containing consolidation results
        """
        try:
            result = await self.background_memory_manager.force_consolidation(user_id)
            logger.info(f"Consolidated memories for user {user_id}")
            return result

        except Exception as e:
            logger.error(f"Error consolidating memories for user {user_id}: {e}")
            return {"status": "error", "error": str(e)}


class InitializeUserMemoryUseCase:
    """Use case for initializing user memory components."""

    def __init__(
        self,
        semantic_memory_service: SemanticMemoryService,
        chat_session_repository: IChatSessionRepository
    ):
        """Initialize the InitializeUserMemoryUseCase.

        Args:
            semantic_memory_service: Service for semantic memory operations
            chat_session_repository: Repository for chat sessions
        """
        self.semantic_memory_service = semantic_memory_service
        self.chat_session_repository = chat_session_repository

    async def execute(self, user_id: str) -> Dict[str, Any]:
        """Execute the use case to initialize user memory.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary containing initialization results
        """
        try:
            # Initialize memory components
            memory_components = await self.semantic_memory_service.initialize_user_memory(user_id)
            
            # Get user's latest session
            user_sessions = await self.chat_session_repository.get_user_sessions(user_id)
            if not user_sessions:
                return {"status": "no_sessions", "user_id": user_id}
            
            latest_session = max(user_sessions, key=lambda s: s.updated_at)
            
            # Update session with memory components
            if hasattr(latest_session.state, 'memory_manager'):
                latest_session.state.memory_manager = memory_components["memory_manager"]
                latest_session.state.user_state = memory_components["user_state"]
                latest_session.state.semantic_memory = memory_components["semantic_memory"]
                
                # Update the session in the repository
                await self.chat_session_repository.update_session(latest_session)
                
                logger.info(f"Initialized memory components for user {user_id}")
                return {"status": "success", "user_id": user_id}
            else:
                return {"status": "incompatible_session", "user_id": user_id}

        except Exception as e:
            logger.error(f"Error initializing memory for user {user_id}: {e}")
            return {"status": "error", "error": str(e)}


class RetrieveRelevantMemoriesUseCase:
    """Use case for retrieving relevant memories for a query."""

    def __init__(
        self,
        chat_session_repository: IChatSessionRepository,
        semantic_memory_service: SemanticMemoryService
    ):
        """Initialize the RetrieveRelevantMemoriesUseCase.

        Args:
            chat_session_repository: Repository for chat sessions
            semantic_memory_service: Service for semantic memory operations
        """
        self.chat_session_repository = chat_session_repository
        self.semantic_memory_service = semantic_memory_service

    async def execute(self, user_id: str, query: str, limit: int = 5) -> Dict[str, Any]:
        """Execute the use case to retrieve relevant memories.

        Args:
            user_id: The user's ID
            query: The query to search for
            limit: Maximum number of memories to return

        Returns:
            Dictionary containing relevant memories
        """
        try:
            # Get user's latest session to verify user exists
            user_sessions = await self.chat_session_repository.get_user_sessions(user_id)
            if not user_sessions:
                return {"status": "no_sessions", "user_id": user_id}

            # Retrieve relevant memories directly using the semantic memory service
            # The semantic memory service manages its own store, so we don't need to check session state
            memories = await self.semantic_memory_service.retrieve_relevant_memories(user_id, query, limit)
            
            logger.info(f"Retrieved {len(memories)} relevant memories for user {user_id}")
            return {
                "status": "success",
                "user_id": user_id,
                "memories": memories,
                "count": len(memories)
            }

        except Exception as e:
            logger.error(f"Error retrieving memories for user {user_id}: {e}")
            return {"status": "error", "error": str(e)}


class UpdateUserProfileWithMemoriesUseCase:
    """Use case for updating user profile with memory insights."""

    def __init__(
        self,
        chat_session_repository: IChatSessionRepository
    ):
        """Initialize the UpdateUserProfileWithMemoriesUseCase.

        Args:
            chat_session_repository: Repository for chat sessions
        """
        self.chat_session_repository = chat_session_repository

    async def execute(
        self,
        user_id: str,
        profile_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the use case to update user profile with memory insights.

        Args:
            user_id: The user's ID
            profile_updates: Dictionary containing profile updates

        Returns:
            Dictionary containing update results
        """
        try:
            # Get user's latest session
            user_sessions = await self.chat_session_repository.get_user_sessions(user_id)
            if not user_sessions:
                return {"status": "no_sessions", "user_id": user_id}

            latest_session = max(user_sessions, key=lambda s: s.updated_at)
            
            # Check if session has user profile
            if not hasattr(latest_session.state, 'user_profile'):
                return {"status": "no_user_profile", "user_id": user_id}

            # Update the profile
            latest_session.state.user_profile.update_semantic_context(profile_updates)
            
            # Update the session in the repository
            await self.chat_session_repository.update_session(latest_session)
            
            logger.info(f"Updated profile for user {user_id} with memory insights")
            return {
                "status": "success",
                "user_id": user_id,
                "updated_fields": list(profile_updates.keys())
            }

        except Exception as e:
            logger.error(f"Error updating profile for user {user_id}: {e}")
            return {"status": "error", "error": str(e)}


class ScheduleMemoryConsolidationUseCase:
    """Use case for scheduling memory consolidation."""

    def __init__(
        self,
        background_memory_manager: BackgroundMemoryManager
    ):
        """Initialize the ScheduleMemoryConsolidationUseCase.

        Args:
            background_memory_manager: Manager for background memory processing
        """
        self.background_memory_manager = background_memory_manager

    async def execute(
        self,
        user_id: str,
        session_id: str,
        priority: int = 1
    ) -> Dict[str, Any]:
        """Execute the use case to schedule memory consolidation.

        Args:
            user_id: The user's ID
            session_id: The session ID
            priority: Priority level (1=high, 2=medium, 3=low)

        Returns:
            Dictionary containing scheduling results
        """
        try:
            await self.background_memory_manager.schedule_memory_consolidation(
                user_id=user_id,
                session_id=session_id,
                priority=priority
            )
            
            logger.info(f"Scheduled memory consolidation for user {user_id}")
            return {
                "status": "success",
                "user_id": user_id,
                "session_id": session_id,
                "priority": priority
            }

        except Exception as e:
            logger.error(f"Error scheduling memory consolidation for user {user_id}: {e}")
            return {"status": "error", "error": str(e)}


