import logging
from celery import Celery
from celery.schedules import crontab

from backend.settings.celery import CelerySettings

logger = logging.getLogger("conversational_commerce")


def create_celery_app() -> Celery:
    """Create and configure Celery application.
    
    Returns:
        Configured Celery application
    """
    # Load settings
    settings = CelerySettings()
    config = settings.get_celery_config()
    
    # Create Celery app
    celery_app = Celery("conversational_commerce")
    celery_app.config_from_object(config)
    
    # Configure periodic tasks
    celery_app.conf.beat_schedule = {
        'process-memory-queue': {
            'task': 'process_memory_queue',
            'schedule': crontab(minute='*/15'),  # Every 15 minutes
        },
        'cleanup-old-memories': {
            'task': 'cleanup_old_memories',
            'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        'consolidate-user-memories': {
            'task': 'consolidate_user_memories',
            'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
        },
    }
    
    # Configure task routes
    celery_app.conf.task_routes = {
        'consolidate_user_memories': {'queue': 'memory_consolidation'},
        'process_memory_queue': {'queue': 'memory_processing'},
        'cleanup_old_memories': {'queue': 'memory_cleanup'},
    }
    
    logger.info("Celery application configured successfully")
    return celery_app


# Create the Celery app instance
celery_app = create_celery_app()


@celery_app.task(bind=True, name='consolidate_user_memories')
def consolidate_user_memories_task(self, user_id: str, session_id: str) -> dict:
    """Celery task for consolidating user memories.
    
    Args:
        user_id: The user's ID
        session_id: The session ID
        
    Returns:
        Dictionary containing task results
    """
    try:
        # Import here to avoid circular imports
        from backend.application.services.background_memory_manager import BackgroundMemoryManager
        from backend.application.services.semantic_memory_service import SemanticMemoryService, SemanticMemoryConfig
        from backend.infrastructure.repositories import MongoDBChatSessionRepository
        from backend.infrastructure.connections.mongodb.connection import MongoDBConnection
        from backend.settings.mongodb import MongoDBSettings
        
        # Initialize dependencies
        mongodb_config = MongoDBSettings()
        mongodb_connection = MongoDBConnection(mongodb_config)
        chat_session_repository = MongoDBChatSessionRepository(mongodb_connection)
        
        # Initialize semantic memory service
        from backend.settings import AISettings
        ai_settings = AISettings()
        semantic_config = SemanticMemoryConfig.from_ai_settings(ai_settings)
        semantic_service = SemanticMemoryService(semantic_config)
        
        # Initialize background memory manager
        memory_manager = BackgroundMemoryManager(
            semantic_memory_service=semantic_service,
            chat_session_repository=chat_session_repository
        )
        
        # Run consolidation
        import asyncio
        result = asyncio.run(memory_manager._consolidate_user_memories(user_id, session_id))
        
        logger.info(f"Memory consolidation completed for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error in memory consolidation task: {e}")
        return {"status": "error", "error": str(e)}


@celery_app.task(bind=True, name='process_memory_queue')
def process_memory_queue_task(self) -> dict:
    """Celery task for processing the memory consolidation queue.
    
    Returns:
        Dictionary containing processing results
    """
    try:
        # Import here to avoid circular imports
        from backend.application.services.background_memory_manager import BackgroundMemoryManager
        from backend.application.services.semantic_memory_service import SemanticMemoryService, SemanticMemoryConfig
        from backend.infrastructure.repositories import MongoDBChatSessionRepository
        from backend.infrastructure.connections.mongodb.connection import MongoDBConnection
        from backend.settings.mongodb import MongoDBSettings
        
        # Initialize dependencies
        mongodb_config = MongoDBSettings()
        mongodb_connection = MongoDBConnection(mongodb_config)
        chat_session_repository = MongoDBChatSessionRepository(mongodb_connection)
        
        # Initialize semantic memory service
        from backend.settings import AISettings
        ai_settings = AISettings()
        semantic_config = SemanticMemoryConfig.from_ai_settings(ai_settings)
        semantic_service = SemanticMemoryService(semantic_config)
        
        # Initialize background memory manager
        memory_manager = BackgroundMemoryManager(
            semantic_memory_service=semantic_service,
            chat_session_repository=chat_session_repository
        )
        
        # Process queue
        import asyncio
        result = asyncio.run(memory_manager._process_memory_queue())
        
        logger.info("Memory queue processing completed")
        return result
        
    except Exception as e:
        logger.error(f"Error in memory queue processing task: {e}")
        return {"status": "error", "error": str(e)}


@celery_app.task(bind=True, name='cleanup_old_memories')
def cleanup_old_memories_task(self) -> dict:
    """Celery task for cleaning up old memories.
    
    Returns:
        Dictionary containing cleanup results
    """
    try:
        # Import here to avoid circular imports
        from backend.application.services.background_memory_manager import BackgroundMemoryManager
        from backend.application.services.semantic_memory_service import SemanticMemoryService, SemanticMemoryConfig
        from backend.infrastructure.repositories import MongoDBChatSessionRepository
        from backend.infrastructure.connections.mongodb.connection import MongoDBConnection
        from backend.settings.mongodb import MongoDBSettings
        
        # Initialize dependencies
        mongodb_config = MongoDBSettings()
        mongodb_connection = MongoDBConnection(mongodb_config)
        chat_session_repository = MongoDBChatSessionRepository(mongodb_connection)
        
        # Initialize semantic memory service
        from backend.settings import AISettings
        ai_settings = AISettings()
        semantic_config = SemanticMemoryConfig.from_ai_settings(ai_settings)
        semantic_service = SemanticMemoryService(semantic_config)
        
        # Initialize background memory manager
        memory_manager = BackgroundMemoryManager(
            semantic_memory_service=semantic_service,
            chat_session_repository=chat_session_repository
        )
        
        # Cleanup old memories
        import asyncio
        result = asyncio.run(memory_manager._cleanup_old_memories())
        
        logger.info("Old memories cleanup completed")
        return result
        
    except Exception as e:
        logger.error(f"Error in old memories cleanup task: {e}")
        return {"status": "error", "error": str(e)}
