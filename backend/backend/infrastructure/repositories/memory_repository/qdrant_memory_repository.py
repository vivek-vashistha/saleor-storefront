import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import models as qdrant_models
from qdrant_client.grpc import Filter

from backend.infrastructure.connections import IQdrantConnection
from backend.infrastructure.repositories.memory_repository.interface import IMemoryRepository

logger = logging.getLogger("conversational_commerce.memory_repository")


class QdrantMemoryRepository(IMemoryRepository):
    """Repository for memory operations using Qdrant for vector operations."""

    def __init__(self, connection: IQdrantConnection):
        """Initialize the QdrantMemoryRepository with the provided connection.

        Args:
            connection: The Qdrant connection.
        """
        self.connection = connection
        self.memories_collection = "user_memories"
        self.conversations_collection = "conversation_embeddings"

    async def store_memory_embedding(
        self, 
        user_id: str, 
        memory_content: str, 
        memory_type: str,
        metadata: Dict[str, Any],
        vector_id: Optional[str] = None
    ) -> str:
        """Store memory embedding in Qdrant.

        Args:
            user_id: The user's ID
            memory_content: The memory content to embed
            memory_type: Type of memory (preference, interaction, theme)
            metadata: Additional metadata
            vector_id: Optional vector ID, will generate if not provided

        Returns:
            The vector ID of the stored embedding
        """
        async def _store_embedding(store: QdrantVectorStore) -> str:
            # Create document for embedding
            document = Document(
                page_content=memory_content,
                metadata={
                    "user_id": user_id,
                    "memory_type": memory_type,
                    "created_at": datetime.now().isoformat(),
                    **metadata
                }
            )
            
            # Generate vector ID if not provided
            if not vector_id:
                generated_vector_id = str(uuid.uuid4())
            else:
                generated_vector_id = vector_id
            
            # Store in Qdrant
            store.add_documents([document], ids=[generated_vector_id])
            
            logger.info(f"Stored memory embedding for user {user_id} with ID {generated_vector_id}")
            return generated_vector_id

        return await self.connection.execute_db_operation(
            _store_embedding, f"Failed to store memory embedding for user {user_id}"
        )

    async def search_similar_memories(
        self, 
        user_id: str, 
        query: str, 
        memory_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar memories using vector similarity.

        Args:
            user_id: The user's ID
            query: The search query
            memory_type: Optional memory type filter
            limit: Maximum number of results

        Returns:
            List of similar memories with scores
        """
        async def _search_memories(store: QdrantVectorStore) -> List[Dict[str, Any]]:
            # Create filter for user and optional memory type
            filter_conditions = [
                qdrant_models.FieldCondition(
                    key="metadata.user_id",
                    match=qdrant_models.MatchValue(value=user_id)
                )
            ]
            
            if memory_type:
                filter_conditions.append(
                    qdrant_models.FieldCondition(
                        key="metadata.memory_type",
                        match=qdrant_models.MatchValue(value=memory_type)
                    )
                )
            
            filter_condition = qdrant_models.Filter(must=filter_conditions)
            
            # Perform similarity search
            results = await store.asimilarity_search(
                query=query,
                k=limit,
                filter=filter_condition
            )
            
            # Format results
            memories = []
            for result in results:
                memories.append({
                    "content": result.page_content,
                    "metadata": result.metadata,
                    "score": getattr(result, 'score', 0.0)
                })
            
            return memories

        return await self.connection.execute_db_operation(
            _search_memories, f"Failed to search memories for user {user_id}"
        )

    async def store_conversation_embedding(
        self,
        user_id: str,
        session_id: str,
        conversation_chunk: str,
        message_type: str,
        metadata: Dict[str, Any],
        vector_id: Optional[str] = None
    ) -> str:
        """Store conversation embedding in Qdrant.

        Args:
            user_id: The user's ID
            session_id: The session ID
            conversation_chunk: The conversation content to embed
            message_type: Type of message (user, assistant)
            metadata: Additional metadata
            vector_id: Optional vector ID, will generate if not provided

        Returns:
            The vector ID of the stored embedding
        """
        async def _store_conversation(store: QdrantVectorStore) -> str:
            # Create document for embedding
            document = Document(
                page_content=conversation_chunk,
                metadata={
                    "user_id": user_id,
                    "session_id": session_id,
                    "message_type": message_type,
                    "created_at": datetime.now().isoformat(),
                    **metadata
                }
            )
            
            # Generate vector ID if not provided
            if not vector_id:
                vector_id = f"conv_{user_id}_{session_id}_{datetime.now().timestamp()}"
            
            # Store in Qdrant
            store.add_documents([document], ids=[vector_id])
            
            logger.info(f"Stored conversation embedding for user {user_id} with ID {vector_id}")
            return vector_id

        return await self.connection.execute_db_operation(
            _store_conversation, f"Failed to store conversation embedding for user {user_id}"
        )

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
        async def _search_conversations(store: QdrantVectorStore) -> List[Dict[str, Any]]:
            # Create filter for user and optional session
            filter_conditions = [
                qdrant_models.FieldCondition(
                    key="metadata.user_id",
                    match=qdrant_models.MatchValue(value=user_id)
                )
            ]
            
            if session_id:
                filter_conditions.append(
                    qdrant_models.FieldCondition(
                        key="metadata.session_id",
                        match=qdrant_models.MatchValue(value=session_id)
                    )
                )
            
            filter_condition = qdrant_models.Filter(must=filter_conditions)
            
            # Perform similarity search
            results = await store.asimilarity_search(
                query=query,
                k=limit,
                filter=filter_condition
            )
            
            # Format results
            contexts = []
            for result in results:
                contexts.append({
                    "content": result.page_content,
                    "metadata": result.metadata,
                    "score": getattr(result, 'score', 0.0)
                })
            
            return contexts

        return await self.connection.execute_db_operation(
            _search_conversations, f"Failed to search conversation context for user {user_id}"
        )

    async def get_memory_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get memory by vector ID.

        Args:
            vector_id: The vector ID

        Returns:
            Memory data if found, None otherwise
        """
        async def _get_memory(store: QdrantVectorStore) -> Optional[Dict[str, Any]]:
            try:
                results = store.get_by_ids([vector_id])
                if results:
                    result = results[0]
                    return {
                        "content": result.page_content,
                        "metadata": result.metadata
                    }
                return None
            except Exception as e:
                logger.error(f"Error getting memory by ID {vector_id}: {e}")
                return None

        return await self.connection.execute_db_operation(
            _get_memory, f"Failed to get memory by ID {vector_id}"
        )

    async def delete_memory(self, vector_id: str) -> bool:
        """Delete memory by vector ID.

        Args:
            vector_id: The vector ID to delete

        Returns:
            True if deleted, False otherwise
        """
        async def _delete_memory(store: QdrantVectorStore) -> bool:
            try:
                # Access the underlying client to delete
                client = store.client
                client.delete(
                    collection_name=self.memories_collection,
                    points_selector=Filter(ids=[vector_id])
                )
                return True
            except Exception as e:
                logger.error(f"Error deleting memory {vector_id}: {e}")
                return False

        return await self.connection.execute_db_operation(
            _delete_memory, f"Failed to delete memory {vector_id}"
        )

    async def get_user_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics for a user from Qdrant.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary containing memory statistics
        """
        async def _get_stats(store: QdrantVectorStore) -> Dict[str, Any]:
            try:
                # Get total count of memories
                client = store.client
                total_memories = client.count(
                    collection_name=self.memories_collection,
                    count_filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="metadata.user_id",
                                match=qdrant_models.MatchValue(value=user_id)
                            )
                        ]
                    )
                )
                
                # Get count by memory type
                type_counts = {}
                for memory_type in ["user_preference", "product_interaction", "conversation_theme"]:
                    count = client.count(
                        collection_name=self.memories_collection,
                        count_filter=qdrant_models.Filter(
                            must=[
                                qdrant_models.FieldCondition(
                                    key="metadata.user_id",
                                    match=qdrant_models.MatchValue(value=user_id)
                                ),
                                qdrant_models.FieldCondition(
                                    key="metadata.memory_type",
                                    match=qdrant_models.MatchValue(value=memory_type)
                                )
                            ]
                        )
                    )
                    type_counts[memory_type] = count.count
                
                return {
                    "total_memories": total_memories.count,
                    "type_counts": type_counts,
                    "last_updated": datetime.now()
                }
            except Exception as e:
                logger.error(f"Error getting memory stats for user {user_id}: {e}")
                return {"total_memories": 0, "type_counts": {}, "last_updated": datetime.now()}

        return await self.connection.execute_db_operation(
            _get_stats, f"Failed to get memory stats for user {user_id}"
        )

    # Implement interface methods (these will delegate to MongoDB for structured data)
    async def store_memory_metadata(self, memory_metadata) -> str:
        """Store memory metadata - delegates to MongoDB repository."""
        raise NotImplementedError("Use MongoDB repository for structured metadata")

    async def get_memory_metadata(self, user_id: str, memory_type: Optional[str] = None):
        """Get memory metadata - delegates to MongoDB repository."""
        raise NotImplementedError("Use MongoDB repository for structured metadata")

    async def update_memory_access(self, memory_id: str) -> None:
        """Update memory access - delegates to MongoDB repository."""
        raise NotImplementedError("Use MongoDB repository for structured metadata")

    async def store_user_profile(self, user_profile) -> str:
        """Store user profile - delegates to MongoDB repository."""
        raise NotImplementedError("Use MongoDB repository for structured data")

    async def get_user_profile(self, user_id: str):
        """Get user profile - delegates to MongoDB repository."""
        raise NotImplementedError("Use MongoDB repository for structured data")

    async def store_consolidated_insights(self, insights) -> str:
        """Store consolidated insights - delegates to MongoDB repository."""
        raise NotImplementedError("Use MongoDB repository for structured data")

    async def get_consolidated_insights(self, user_id: str):
        """Get consolidated insights - delegates to MongoDB repository."""
        raise NotImplementedError("Use MongoDB repository for structured data")

    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics - uses Qdrant for vector stats."""
        return await self.get_user_memory_stats(user_id)

    async def delete_old_memories(self, user_id: str, days_old: int = 90) -> int:
        """Delete old memories - not implemented for Qdrant."""
        logger.warning("Delete old memories not implemented for Qdrant repository")
        return 0
