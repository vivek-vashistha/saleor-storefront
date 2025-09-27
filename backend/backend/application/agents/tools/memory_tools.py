"""Memory-related tools for Deep Agents."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from backend.application.services.hybrid_memory_service import HybridMemoryService

logger = logging.getLogger("conversational_commerce.memory_tools")


class MemoryTools:
    """Memory-related tools for Deep Agents."""

    def __init__(self, memory_service: HybridMemoryService):
        """Initialize memory tools.

        Args:
            memory_service: Memory service for operations
        """
        self.memory_service = memory_service

    async def retrieve_memories_tool(
        self,
        user_id: str,
        query: str,
        context_type: str = "general",
        limit: int = 5
    ) -> Dict[str, Any]:
        """Retrieve relevant memories for the user.

        Args:
            user_id: The user's ID
            query: The search query
            context_type: Type of context to retrieve
            limit: Maximum number of memories to retrieve

        Returns:
            Dictionary with memories and metadata
        """
        try:
            logger.info(f"Retrieving memories for user {user_id}: {query[:50]}...")
            
            # Retrieve memories using the memory service
            memories = await self.memory_service.search_memories(
                user_id=user_id,
                query=query,
                memory_type=context_type if context_type != "general" else None,
                limit=limit,
                include_metadata=True
            )
            
            logger.info(f"Retrieved {len(memories)} memories for user {user_id}")
            
            return {
                "memories": memories,
                "count": len(memories),
                "context_type": context_type,
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Error retrieving memories for user {user_id}: {e}")
            return {
                "memories": [],
                "count": 0,
                "context_type": context_type,
                "query": query,
                "error": str(e)
            }

    async def store_memory_tool(
        self,
        user_id: str,
        content: str,
        memory_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
        importance_score: float = 0.5
    ) -> Dict[str, str]:
        """Store new memory for the user.

        Args:
            user_id: The user's ID
            content: The memory content
            memory_type: Type of memory
            metadata: Additional metadata
            confidence: Confidence score for the memory
            importance_score: Importance score for the memory

        Returns:
            Dictionary with storage results
        """
        try:
            logger.info(f"Storing memory for user {user_id}: {content[:50]}...")
            
            # Store memory using the memory service
            result = await self.memory_service.store_memory(
                user_id=user_id,
                memory_content=content,
                memory_type=memory_type,
                confidence=confidence,
                importance_score=importance_score,
                additional_metadata=metadata
            )
            
            logger.info(f"Stored memory for user {user_id}: {result}")
            
            return {
                "status": "stored",
                "memory_type": memory_type,
                "mongodb_id": result.get("mongodb_id"),
                "qdrant_id": result.get("qdrant_id")
            }
            
        except Exception as e:
            logger.error(f"Error storing memory for user {user_id}: {e}")
            return {
                "status": "error",
                "memory_type": memory_type,
                "error": str(e)
            }

    async def update_user_profile_tool(
        self,
        user_id: str,
        profile_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user profile with new information.

        Args:
            user_id: The user's ID
            profile_updates: Dictionary of profile updates

        Returns:
            Dictionary with update results
        """
        try:
            logger.info(f"Updating user profile for user {user_id}")
            
            # Get current profile
            current_profile = await self.memory_service.get_user_profile_with_memories(
                user_id=user_id,
                include_semantic_context=False
            )
            
            # Update profile data
            if current_profile and "profile" in current_profile:
                # This would require implementing profile update in the memory service
                # For now, we'll store the updates as a memory
                await self.store_memory_tool(
                    user_id=user_id,
                    content=f"Profile updated: {profile_updates}",
                    memory_type="user_preference",
                    metadata=profile_updates
                )
            
            logger.info(f"Updated user profile for user {user_id}")
            
            return {
                "status": "updated",
                "updates": profile_updates,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error updating user profile for user {user_id}: {e}")
            return {
                "status": "error",
                "updates": profile_updates,
                "user_id": user_id,
                "error": str(e)
            }

    async def consolidate_memories_tool(
        self,
        user_id: str,
        force_consolidation: bool = False
    ) -> Dict[str, Any]:
        """Consolidate user memories and generate insights.

        Args:
            user_id: The user's ID
            force_consolidation: Whether to force consolidation

        Returns:
            Dictionary with consolidation results
        """
        try:
            logger.info(f"Consolidating memories for user {user_id}")
            
            # Consolidate memories using the memory service
            result = await self.memory_service.consolidate_user_memories(
                user_id=user_id,
                force_consolidation=force_consolidation
            )
            
            logger.info(f"Consolidated memories for user {user_id}: {result.get('status')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error consolidating memories for user {user_id}: {e}")
            return {
                "status": "error",
                "user_id": user_id,
                "error": str(e)
            }

    async def search_conversation_context_tool(
        self,
        user_id: str,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Search for relevant conversation context.

        Args:
            user_id: The user's ID
            query: The search query
            session_id: Optional session ID filter
            limit: Maximum number of results

        Returns:
            Dictionary with conversation context
        """
        try:
            logger.info(f"Searching conversation context for user {user_id}: {query[:50]}...")
            
            # Search conversation context using the memory service
            context = await self.memory_service.search_conversation_context(
                user_id=user_id,
                query=query,
                session_id=session_id,
                limit=limit
            )
            
            logger.info(f"Found {len(context)} conversation contexts for user {user_id}")
            
            return {
                "context": context,
                "count": len(context),
                "query": query,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error searching conversation context for user {user_id}: {e}")
            return {
                "context": [],
                "count": 0,
                "query": query,
                "session_id": session_id,
                "error": str(e)
            }
