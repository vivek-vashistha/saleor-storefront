"""Enhanced memory integration service for Deep Agents."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from backend.application.services.hybrid_memory_service import HybridMemoryService
from backend.application.services.background_memory_manager import BackgroundMemoryManager

logger = logging.getLogger("conversational_commerce.memory_integration")


class MemoryIntegrationService:
    """Enhanced memory service for Deep Agents integration."""

    def __init__(
        self,
        semantic_memory_service,
        background_memory_manager: BackgroundMemoryManager
    ):
        """Initialize the memory integration service.

        Args:
            semantic_memory_service: Semantic memory service
            background_memory_manager: Background memory manager
        """
        self.semantic_memory_service = semantic_memory_service
        self.background_memory_manager = background_memory_manager

    async def retrieve_contextual_memories(
        self,
        user_id: str,
        query: str,
        context_type: str = "general",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve memories with context type filtering.

        Args:
            user_id: The user's ID
            query: The search query
            context_type: Type of context to retrieve
            limit: Maximum number of memories to retrieve

        Returns:
            List of relevant memories
        """
        try:
            logger.info(f"Retrieving contextual memories for user {user_id}: {query[:50]}...")
            
            # Retrieve memories using semantic memory service
            memories = await self.semantic_memory_service.retrieve_relevant_memories(
                user_id=user_id,
                query=query,
                limit=limit
            )
            
            # Filter by context type if needed
            if context_type != "general":
                filtered_memories = []
                for memory in memories:
                    metadata = memory.get('metadata', {})
                    if metadata.get('context_type') == context_type:
                        filtered_memories.append(memory)
                memories = filtered_memories
            
            logger.info(f"Retrieved {len(memories)} contextual memories for user {user_id}")
            return memories
            
        except Exception as e:
            logger.error(f"Error retrieving contextual memories for user {user_id}: {e}")
            return []

    async def store_conversation_memory(
        self,
        user_id: str,
        conversation_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Store conversation as memory with proper categorization.

        Args:
            user_id: The user's ID
            conversation_data: Conversation data to store

        Returns:
            Dictionary with storage results
        """
        try:
            logger.info(f"Storing conversation memory for user {user_id}")
            
            # Determine memory type based on conversation content
            memory_type = self._determine_memory_type(conversation_data)
            
            # Store memory using semantic memory service
            result = await self.semantic_memory_service.hybrid_memory.store_memory(
                user_id=user_id,
                content=conversation_data['content'],
                memory_type=memory_type,
                metadata=conversation_data.get('metadata', {})
            )
            
            logger.info(f"Stored conversation memory for user {user_id}: {memory_type}")
            return result
            
        except Exception as e:
            logger.error(f"Error storing conversation memory for user {user_id}: {e}")
            return {"error": str(e)}

    async def update_user_profile_with_memory(
        self,
        user_id: str,
        profile_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user profile with new information from memory.

        Args:
            user_id: The user's ID
            profile_updates: Profile updates to apply

        Returns:
            Dictionary with update results
        """
        try:
            logger.info(f"Updating user profile with memory for user {user_id}")
            
            # Store profile updates as memory
            await self.store_conversation_memory(
                user_id=user_id,
                conversation_data={
                    "content": f"Profile updated: {profile_updates}",
                    "metadata": {
                        "type": "profile_update",
                        "updates": profile_updates,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            )
            
            # Schedule background memory consolidation
            await self.background_memory_manager.schedule_memory_consolidation(
                user_id=user_id,
                session_id="profile_update",
                priority=2
            )
            
            logger.info(f"Updated user profile with memory for user {user_id}")
            return {
                "status": "updated",
                "updates": profile_updates,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error updating user profile with memory for user {user_id}: {e}")
            return {
                "status": "error",
                "updates": profile_updates,
                "user_id": user_id,
                "error": str(e)
            }

    async def get_user_context_for_deep_agent(
        self,
        user_id: str,
        query: str,
        include_conversation_history: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive user context for Deep Agent processing.

        Args:
            user_id: The user's ID
            query: The current query
            include_conversation_history: Whether to include conversation history

        Returns:
            Dictionary with comprehensive user context
        """
        try:
            logger.info(f"Getting user context for Deep Agent: user {user_id}")
            
            # Retrieve relevant memories
            memories = await self.retrieve_contextual_memories(
                user_id=user_id,
                query=query,
                limit=5
            )
            
            # Get user profile information using hybrid memory service
            user_profile = await self.semantic_memory_service.hybrid_memory.get_user_profile_with_memories(
                user_id=user_id,
                include_semantic_context=True
            )
            
            # Get conversation history if requested (using hybrid memory service)
            conversation_history = []
            if include_conversation_history:
                # For now, we'll get conversation context from hybrid memory
                conversation_history = await self.semantic_memory_service.hybrid_memory.search_conversation_context(
                    user_id=user_id,
                    query="conversation history",
                    limit=10
                )
            
            # Get consolidated insights
            insights = await self.semantic_memory_service.consolidate_memories(
                user_id=user_id
            )
            
            context = {
                "user_id": user_id,
                "memories": memories,
                "user_profile": user_profile,
                "conversation_history": conversation_history,
                "insights": insights,
                "query": query
            }
            
            logger.info(f"Retrieved comprehensive context for user {user_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error getting user context for Deep Agent: {e}")
            return {
                "user_id": user_id,
                "memories": [],
                "user_profile": None,
                "conversation_history": [],
                "insights": None,
                "query": query,
                "error": str(e)
            }

    async def store_deep_agent_interaction(
        self,
        user_id: str,
        interaction_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Store Deep Agent interaction as memory.

        Args:
            user_id: The user's ID
            interaction_data: Interaction data to store

        Returns:
            Dictionary with storage results
        """
        try:
            logger.info(f"Storing Deep Agent interaction for user {user_id}")
            
            # Store interaction as memory
            result = await self.store_conversation_memory(
                user_id=user_id,
                conversation_data={
                    "content": interaction_data.get("content", ""),
                    "metadata": {
                        "type": "deep_agent_interaction",
                        "sub_agent_used": interaction_data.get("sub_agent_used"),
                        "tools_used": interaction_data.get("tools_used", []),
                        "confidence": interaction_data.get("confidence", 0.0),
                        "timestamp": datetime.now().isoformat()
                    }
                }
            )
            
            logger.info(f"Stored Deep Agent interaction for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error storing Deep Agent interaction for user {user_id}: {e}")
            return {"error": str(e)}

    async def consolidate_memories_for_deep_agent(
        self,
        user_id: str,
        force_consolidation: bool = False
    ) -> Dict[str, Any]:
        """Consolidate memories specifically for Deep Agent optimization.

        Args:
            user_id: The user's ID
            force_consolidation: Whether to force consolidation

        Returns:
            Dictionary with consolidation results
        """
        try:
            logger.info(f"Consolidating memories for Deep Agent: user {user_id}")
            
            # Use background memory manager for consolidation
            result = await self.background_memory_manager.schedule_memory_consolidation(
                user_id=user_id,
                session_id="deep_agent_consolidation",
                priority=1
            )
            
            logger.info(f"Consolidated memories for Deep Agent: user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error consolidating memories for Deep Agent: {e}")
            return {"error": str(e)}

    def _determine_memory_type(self, conversation_data: Dict[str, Any]) -> str:
        """Determine appropriate memory type based on conversation content.

        Args:
            conversation_data: The conversation data

        Returns:
            Memory type string
        """
        try:
            content = conversation_data.get('content', '').lower()
            
            # Determine memory type based on content
            if any(keyword in content for keyword in ['order', 'purchase', 'bought']):
                return 'order_history'
            elif any(keyword in content for keyword in ['health', 'condition', 'medication']):
                return 'health_context'
            elif any(keyword in content for keyword in ['prefer', 'like', 'dislike']):
                return 'user_preference'
            elif any(keyword in content for keyword in ['product', 'recommend', 'search']):
                return 'product_preference'
            else:
                return 'conversation_context'
                
        except Exception as e:
            logger.error(f"Error determining memory type: {e}")
            return 'conversation_context'

    async def get_memory_statistics_for_user(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get memory statistics for a user.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary with memory statistics
        """
        try:
            logger.info(f"Getting memory statistics for user {user_id}")
            
            # Get memory statistics from hybrid memory service with error handling
            try:
                stats = await self.semantic_memory_service.hybrid_memory.mongodb.get_memory_stats(user_id)
            except Exception as e:
                logger.warning(f"Could not get memory stats for user {user_id}: {e}")
                stats = {"total_memories": 0, "memory_types": {}}
            
            # Get consolidated insights
            insights = await self.semantic_memory_service.consolidate_memories(
                user_id=user_id
            )
            
            statistics = {
                "user_id": user_id,
                "total_memories": stats.get("total_memories", 0),
                "memory_types": stats.get("memory_types", {}),
                "consolidated_insights": insights,
                "last_updated": stats.get("last_updated")
            }
            
            logger.info(f"Retrieved memory statistics for user {user_id}")
            return statistics
            
        except Exception as e:
            logger.error(f"Error getting memory statistics for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "total_memories": 0,
                "memory_types": {},
                "consolidated_insights": None,
                "last_updated": None,
                "error": str(e)
            }
