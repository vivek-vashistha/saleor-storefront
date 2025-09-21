import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from celery import Celery
from celery.schedules import crontab

from backend.application.services.semantic_memory_service import SemanticMemoryService, SemanticMemoryConfig
from backend.infrastructure.repositories import IChatSessionRepository
from backend.domain.entities.enhanced_chat import EnhancedChatState

logger = logging.getLogger("conversational_commerce")


@dataclass
class MemoryConsolidationTask:
    """Task for consolidating user memories."""
    user_id: str
    session_id: str
    priority: int = 1
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class BackgroundMemoryManager:
    """Manages background memory processing and consolidation."""
    
    def __init__(
        self,
        semantic_memory_service: SemanticMemoryService,
        chat_session_repository: IChatSessionRepository,
        celery_app: Optional[Celery] = None
    ):
        """Initialize the background memory manager.
        
        Args:
            semantic_memory_service: Service for semantic memory operations
            chat_session_repository: Repository for chat sessions
            celery_app: Celery app for background tasks
        """
        self.semantic_memory_service = semantic_memory_service
        self.chat_session_repository = chat_session_repository
        self.celery_app = celery_app
        self.consolidation_queue: List[MemoryConsolidationTask] = []
        
        # Register background tasks if Celery is available
        if self.celery_app:
            self._register_celery_tasks()
    
    def _register_celery_tasks(self) -> None:
        """Register Celery tasks for background processing."""
        
        @self.celery_app.task(name='consolidate_user_memories')
        def consolidate_user_memories_task(user_id: str, session_id: str) -> Dict[str, Any]:
            """Celery task for consolidating user memories."""
            return asyncio.run(self._consolidate_user_memories(user_id, session_id))
        
        @self.celery_app.task(name='process_memory_queue')
        def process_memory_queue_task() -> Dict[str, Any]:
            """Celery task for processing the memory consolidation queue."""
            return asyncio.run(self._process_memory_queue())
        
        @self.celery_app.task(name='cleanup_old_memories')
        def cleanup_old_memories_task() -> Dict[str, Any]:
            """Celery task for cleaning up old memories."""
            return asyncio.run(self._cleanup_old_memories())
        
        # Schedule periodic tasks
        self.celery_app.conf.beat_schedule.update({
            'process-memory-queue': {
                'task': 'process_memory_queue',
                'schedule': crontab(minute='*/15'),  # Every 15 minutes
            },
            'cleanup-old-memories': {
                'task': 'cleanup_old_memories',
                'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
            },
        })
    
    async def schedule_memory_consolidation(
        self,
        user_id: str,
        session_id: str,
        priority: int = 1
    ) -> None:
        """Schedule memory consolidation for a user.
        
        Args:
            user_id: The user's ID
            session_id: The session ID
            priority: Priority level (1=high, 2=medium, 3=low)
        """
        task = MemoryConsolidationTask(
            user_id=user_id,
            session_id=session_id,
            priority=priority
        )
        
        # Add to queue
        self.consolidation_queue.append(task)
        
        # If Celery is available, schedule the task
        if self.celery_app:
            consolidate_user_memories_task.delay(user_id, session_id)
        
        logger.info(f"Scheduled memory consolidation for user {user_id}")
    
    async def _consolidate_user_memories(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Consolidate memories for a specific user.
        
        Args:
            user_id: The user's ID
            session_id: The session ID
            
        Returns:
            Dictionary containing consolidation results
        """
        try:
            # Get user's sessions
            user_sessions = await self.chat_session_repository.get_user_sessions(user_id)
            
            if not user_sessions:
                return {"status": "no_sessions", "user_id": user_id}
            
            # Find the most recent session with memory components
            latest_session = None
            for session in sorted(user_sessions, key=lambda s: s.updated_at, reverse=True):
                if hasattr(session.state, 'memory_store') and session.state.memory_store:
                    latest_session = session
                    break
            
            if not latest_session:
                return {"status": "no_memory_components", "user_id": user_id}
            
            # Consolidate memories
            consolidation_result = await self.semantic_memory_service.consolidate_memories(
                user_id=user_id
            )
            
            # Update user profile with consolidated insights
            if consolidation_result.get("status") != "error":
                await self._update_user_profile_with_consolidated_memories(
                    user_id, consolidation_result
                )
            
            logger.info(f"Consolidated memories for user {user_id}")
            return {
                "status": "success",
                "user_id": user_id,
                "consolidation_result": consolidation_result
            }
            
        except Exception as e:
            logger.error(f"Error consolidating memories for user {user_id}: {e}")
            return {"status": "error", "user_id": user_id, "error": str(e)}
    
    async def _process_memory_queue(self) -> Dict[str, Any]:
        """Process the memory consolidation queue.
        
        Returns:
            Dictionary containing processing results
        """
        try:
            if not self.consolidation_queue:
                return {"status": "empty_queue"}
            
            # Sort by priority and creation time
            sorted_queue = sorted(
                self.consolidation_queue,
                key=lambda task: (task.priority, task.created_at)
            )
            
            processed_count = 0
            errors = []
            
            for task in sorted_queue[:10]:  # Process up to 10 tasks at a time
                try:
                    result = await self._consolidate_user_memories(
                        task.user_id, task.session_id
                    )
                    if result["status"] == "success":
                        processed_count += 1
                    else:
                        errors.append(f"User {task.user_id}: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    errors.append(f"User {task.user_id}: {str(e)}")
            
            # Remove processed tasks
            self.consolidation_queue = self.consolidation_queue[processed_count:]
            
            logger.info(f"Processed {processed_count} memory consolidation tasks")
            return {
                "status": "success",
                "processed_count": processed_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error processing memory queue: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _cleanup_old_memories(self) -> Dict[str, Any]:
        """Clean up old memories based on retention policy.
        
        Returns:
            Dictionary containing cleanup results
        """
        try:
            retention_days = self.semantic_memory_service.config.memory_retention_days
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Get all users with sessions
            # Note: This would need to be implemented in the repository
            # For now, we'll return a placeholder
            logger.info(f"Cleaning up memories older than {cutoff_date}")
            
            return {
                "status": "success",
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": retention_days
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old memories: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _update_user_profile_with_consolidated_memories(
        self,
        user_id: str,
        consolidation_result: Dict[str, Any]
    ) -> None:
        """Update user profile with insights from consolidated memories.
        
        Args:
            user_id: The user's ID
            consolidation_result: Results from memory consolidation
        """
        try:
            # Get user's latest session
            user_sessions = await self.chat_session_repository.get_user_sessions(user_id)
            if not user_sessions:
                return
            
            latest_session = max(user_sessions, key=lambda s: s.updated_at)
            
            # Update profile with consolidated insights
            if hasattr(latest_session.state, 'user_profile'):
                profile_updates = {}
                
                # Extract insights from consolidation result
                if "consolidated_patterns" in consolidation_result:
                    patterns = consolidation_result["consolidated_patterns"]
                    
                    if "themes" in patterns:
                        profile_updates["conversation_themes"] = patterns["themes"]
                    
                    if "preferences" in patterns:
                        profile_updates["product_preferences"] = patterns["preferences"]
                    
                    if "communication_style" in patterns:
                        profile_updates["communication_style"] = patterns["communication_style"]
                
                # Update the profile
                if profile_updates:
                    latest_session.state.user_profile.update_semantic_context(profile_updates)
                    await self.chat_session_repository.update_session(latest_session)
                    
                    logger.info(f"Updated profile for user {user_id} with consolidated insights")
            
        except Exception as e:
            logger.error(f"Error updating profile for user {user_id}: {e}")
    
    async def get_memory_insights(self, user_id: str) -> Dict[str, Any]:
        """Get memory insights for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary containing memory insights
        """
        try:
            # Get user's latest session
            user_sessions = await self.chat_session_repository.get_user_sessions(user_id)
            if not user_sessions:
                return {"status": "no_sessions"}
            
            latest_session = max(user_sessions, key=lambda s: s.updated_at)
            
            if not hasattr(latest_session.state, 'memory_store') or not latest_session.state.memory_store:
                return {"status": "no_semantic_memory"}
            
            # Get memory statistics
            memories = latest_session.state.memory_store.search(
                namespace=("conversations", user_id, "memories"),
                limit=1000
            )
            
            # Analyze memory patterns
            insights = {
                "total_memories": len(memories),
                "recent_activity": len([m for m in memories if self._is_recent(m)]),
                "conversation_themes": getattr(latest_session.state.user_profile, 'conversation_themes', []),
                "product_affinities": getattr(latest_session.state.user_profile, 'product_affinities', []),
                "communication_style": getattr(latest_session.state.user_profile, 'communication_style', None),
                "last_updated": getattr(latest_session.state, 'memory_last_updated', None)
            }
            
            return {"status": "success", "insights": insights}
            
        except Exception as e:
            logger.error(f"Error getting memory insights for user {user_id}: {e}")
            return {"status": "error", "error": str(e)}
    
    def _is_recent(self, memory: Dict[str, Any], days: int = 7) -> bool:
        """Check if a memory is recent.
        
        Args:
            memory: Memory object
            days: Number of days to consider as recent
            
        Returns:
            True if the memory is recent
        """
        try:
            if "timestamp" in memory:
                memory_date = datetime.fromisoformat(memory["timestamp"])
                return memory_date > datetime.now() - timedelta(days=days)
            return False
        except:
            return False
    
    async def force_consolidation(self, user_id: str) -> Dict[str, Any]:
        """Force immediate memory consolidation for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary containing consolidation results
        """
        try:
            # Get user's latest session
            user_sessions = await self.chat_session_repository.get_user_sessions(user_id)
            if not user_sessions:
                return {"status": "no_sessions"}
            
            latest_session = max(user_sessions, key=lambda s: s.updated_at)
            
            # Force consolidation
            result = await self._consolidate_user_memories(user_id, latest_session.id)
            
            logger.info(f"Forced consolidation for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error forcing consolidation for user {user_id}: {e}")
            return {"status": "error", "error": str(e)}


