import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from backend.infrastructure.repositories.memory_repository.mongodb_memory_repository import (
    MongoDBMemoryRepository, MemoryMetadata, UserProfileData, ConsolidatedInsights
)
from backend.infrastructure.repositories.memory_repository.qdrant_memory_repository import (
    QdrantMemoryRepository
)

logger = logging.getLogger("conversational_commerce.hybrid_memory")


class HybridMemoryService:
    """Service that orchestrates both MongoDB and Qdrant for comprehensive memory management."""

    def __init__(
        self,
        mongodb_repository: MongoDBMemoryRepository,
        qdrant_repository: QdrantMemoryRepository
    ):
        """Initialize the hybrid memory service.

        Args:
            mongodb_repository: MongoDB repository for structured data
            qdrant_repository: Qdrant repository for vector operations
        """
        self.mongodb = mongodb_repository
        self.qdrant = qdrant_repository

    async def store_memory(
        self,
        user_id: str,
        memory_content: str,
        memory_type: str,
        session_id: Optional[str] = None,
        confidence: float = 1.0,
        importance_score: float = 0.5,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Store memory in both MongoDB and Qdrant.

        Args:
            user_id: The user's ID
            memory_content: The memory content
            memory_type: Type of memory (preference, interaction, theme)
            session_id: Optional session ID
            confidence: Confidence score for the memory
            importance_score: Importance score for the memory
            additional_metadata: Additional metadata

        Returns:
            Dictionary containing both MongoDB and Qdrant IDs
        """
        try:
            # Store vector embedding in Qdrant
            vector_id = await self.qdrant.store_memory_embedding(
                user_id=user_id,
                memory_content=memory_content,
                memory_type=memory_type,
                metadata=additional_metadata or {}
            )

            # Store structured metadata in MongoDB
            memory_metadata = MemoryMetadata(
                user_id=user_id,
                session_id=session_id,
                memory_type=memory_type,
                content={"content": memory_content, **(additional_metadata or {})},
                qdrant_vector_id=vector_id,
                confidence=confidence,
                importance_score=importance_score
            )
            
            mongodb_id = await self.mongodb.store_memory_metadata(memory_metadata)

            logger.info(f"Stored memory for user {user_id} - MongoDB: {mongodb_id}, Qdrant: {vector_id}")
            
            return {
                "mongodb_id": mongodb_id,
                "qdrant_id": vector_id,
                "memory_type": memory_type
            }

        except Exception as e:
            logger.error(f"Error storing memory for user {user_id}: {e}")
            raise

    async def search_memories(
        self,
        user_id: str,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 5,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Search for memories using semantic similarity.

        Args:
            user_id: The user's ID
            query: The search query
            memory_type: Optional memory type filter
            limit: Maximum number of results
            include_metadata: Whether to include MongoDB metadata

        Returns:
            List of memories with scores and metadata
        """
        try:
            # Get semantic search results from Qdrant
            semantic_results = await self.qdrant.search_similar_memories(
                user_id=user_id,
                query=query,
                memory_type=memory_type,
                limit=limit
            )

            if not include_metadata:
                return semantic_results

            # Enhance with MongoDB metadata
            enhanced_results = []
            for result in semantic_results:
                enhanced_result = result.copy()
                
                # Get MongoDB metadata if vector_id is available
                if "metadata" in result and "qdrant_vector_id" in result["metadata"]:
                    # This would require a reverse lookup - for now, return semantic results
                    pass
                
                enhanced_results.append(enhanced_result)

            logger.info(f"Found {len(enhanced_results)} memories for user {user_id}")
            return enhanced_results

        except Exception as e:
            logger.error(f"Error searching memories for user {user_id}: {e}")
            return []

    async def get_user_profile_with_memories(
        self,
        user_id: str,
        include_semantic_context: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive user profile with memory insights.

        Args:
            user_id: The user's ID
            include_semantic_context: Whether to include semantic search context

        Returns:
            Comprehensive user profile with memory data
        """
        try:
            # Get structured profile from MongoDB
            user_profile = await self.mongodb.get_user_profile(user_id)
            
            # Get consolidated insights from MongoDB
            insights = await self.mongodb.get_consolidated_insights(user_id)
            
            # Get memory statistics from both stores
            mongodb_stats = await self.mongodb.get_memory_stats(user_id)
            
            # Get Qdrant stats with error handling (collection might not exist)
            try:
                qdrant_stats = await self.qdrant.get_memory_stats(user_id)
            except Exception as e:
                logger.warning(f"Could not get Qdrant stats for user {user_id}: {e}")
                qdrant_stats = {"total_memories": 0, "error": str(e)}
            
            profile_data = {
                "user_id": user_id,
                "profile": user_profile.model_dump() if user_profile else None,
                "insights": insights.model_dump() if insights else None,
                "memory_stats": {
                    "mongodb": mongodb_stats,
                    "qdrant": qdrant_stats
                }
            }

            if include_semantic_context:
                # Get recent semantic memories for context
                recent_memories = await self.search_memories(
                    user_id=user_id,
                    query="recent preferences and interactions",
                    limit=3
                )
                profile_data["recent_semantic_memories"] = recent_memories

            return profile_data

        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {e}")
            return {"user_id": user_id, "error": str(e)}

    async def consolidate_user_memories(
        self,
        user_id: str,
        force_consolidation: bool = False
    ) -> Dict[str, Any]:
        """Consolidate user memories and generate insights.

        Args:
            user_id: The user's ID
            force_consolidation: Whether to force consolidation regardless of threshold

        Returns:
            Consolidation results and insights
        """
        try:
            # Get memory statistics
            stats = await self.mongodb.get_memory_stats(user_id)
            total_memories = stats.get("total_memories", 0)
            
            # Check if consolidation is needed
            if not force_consolidation and total_memories < 10:
                return {
                    "status": "insufficient_memories",
                    "total_memories": total_memories,
                    "message": "Not enough memories for consolidation"
                }

            # Get all memories for analysis
            all_memories = await self.mongodb.get_memory_metadata(user_id)
            
            # Group memories by type for analysis
            memory_groups = {}
            for memory in all_memories:
                memory_type = memory.memory_type
                if memory_type not in memory_groups:
                    memory_groups[memory_type] = []
                memory_groups[memory_type].append(memory)

            # Generate consolidated insights
            consolidated_patterns = await self._generate_consolidated_patterns(memory_groups)
            
            # Create consolidated insights
            insights = ConsolidatedInsights(
                user_id=user_id,
                consolidated_patterns=consolidated_patterns,
                memory_summary=self._generate_memory_summary(consolidated_patterns),
                confidence_score=self._calculate_confidence_score(consolidated_patterns)
            )

            # Store consolidated insights
            insights_id = await self.mongodb.store_consolidated_insights(insights)

            logger.info(f"Consolidated memories for user {user_id} - insights ID: {insights_id}")
            
            return {
                "status": "success",
                "insights_id": insights_id,
                "total_memories": total_memories,
                "consolidated_patterns": consolidated_patterns,
                "confidence_score": insights.confidence_score
            }

        except Exception as e:
            logger.error(f"Error consolidating memories for user {user_id}: {e}")
            return {"status": "error", "message": str(e)}

    async def search_conversation_context(
        self,
        user_id: str,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for relevant conversation context.

        Args:
            user_id: The user's ID
            query: The search query
            session_id: Optional session ID filter
            limit: Maximum number of results

        Returns:
            List of relevant conversation contexts
        """
        try:
            return await self.qdrant.search_conversation_context(
                user_id=user_id,
                query=query,
                session_id=session_id,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error searching conversation context for user {user_id}: {e}")
            return []

    async def store_conversation_chunk(
        self,
        user_id: str,
        session_id: str,
        conversation_chunk: str,
        message_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store conversation chunk for context retrieval.

        Args:
            user_id: The user's ID
            session_id: The session ID
            conversation_chunk: The conversation content
            message_type: Type of message (user, assistant)
            metadata: Additional metadata

        Returns:
            The vector ID of the stored conversation
        """
        try:
            return await self.qdrant.store_conversation_embedding(
                user_id=user_id,
                session_id=session_id,
                conversation_chunk=conversation_chunk,
                message_type=message_type,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f"Error storing conversation chunk for user {user_id}: {e}")
            raise

    async def cleanup_old_memories(
        self,
        user_id: str,
        days_old: int = 90
    ) -> Dict[str, int]:
        """Clean up old memories from both stores.

        Args:
            user_id: The user's ID
            days_old: Number of days old to consider for deletion

        Returns:
            Dictionary with cleanup results
        """
        try:
            # Clean up MongoDB
            mongodb_deleted = await self.mongodb.delete_old_memories(user_id, days_old)
            
            # Note: Qdrant cleanup would require more complex logic
            # For now, we'll just log the MongoDB cleanup
            logger.info(f"Cleaned up {mongodb_deleted} old memories for user {user_id}")
            
            return {
                "mongodb_deleted": mongodb_deleted,
                "qdrant_deleted": 0,  # Not implemented yet
                "total_deleted": mongodb_deleted
            }

        except Exception as e:
            logger.error(f"Error cleaning up memories for user {user_id}: {e}")
            return {"error": str(e)}

    async def _generate_consolidated_patterns(self, memory_groups: Dict[str, List]) -> Dict[str, Any]:
        """Generate consolidated patterns from memory groups."""
        patterns = {
            "themes": [],
            "preferences": [],
            "interaction_patterns": {},
            "decision_factors": []
        }

        # Analyze each memory type
        for memory_type, memories in memory_groups.items():
            if memory_type == "user_preference":
                # Extract preference patterns
                for memory in memories:
                    content = memory.content
                    if "preference" in content:
                        patterns["preferences"].append(content["preference"])
            
            elif memory_type == "conversation_theme":
                # Extract theme patterns
                for memory in memories:
                    content = memory.content
                    if "theme" in content:
                        patterns["themes"].append(content["theme"])

        # Remove duplicates and limit
        patterns["themes"] = list(set(patterns["themes"]))[:5]
        patterns["preferences"] = list(set(patterns["preferences"]))[:10]

        return patterns

    def _generate_memory_summary(self, patterns: Dict[str, Any]) -> str:
        """Generate a summary from consolidated patterns."""
        themes = patterns.get("themes", [])
        preferences = patterns.get("preferences", [])
        
        summary_parts = []
        
        if themes:
            summary_parts.append(f"Interested in: {', '.join(themes[:3])}")
        
        if preferences:
            summary_parts.append(f"Prefers: {', '.join(preferences[:3])}")
        
        return ". ".join(summary_parts) if summary_parts else "No clear patterns identified"

    def _calculate_confidence_score(self, patterns: Dict[str, Any]) -> float:
        """Calculate confidence score for consolidated patterns."""
        theme_count = len(patterns.get("themes", []))
        preference_count = len(patterns.get("preferences", []))
        
        # Simple confidence calculation based on pattern richness
        total_patterns = theme_count + preference_count
        if total_patterns == 0:
            return 0.0
        
        # Normalize to 0-1 range
        confidence = min(total_patterns / 10.0, 1.0)
        return round(confidence, 2)
