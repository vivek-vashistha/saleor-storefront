import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from backend.application.services.semantic_memory_service import SemanticMemoryService
from dependency_injector.wiring import Provide, inject

from backend.application.use_cases.memory_management import (
    GetMemoryInsightsUseCase,
    ConsolidateUserMemoriesUseCase,
    InitializeUserMemoryUseCase,
    RetrieveRelevantMemoriesUseCase,
    UpdateUserProfileWithMemoriesUseCase,
    ScheduleMemoryConsolidationUseCase
)
from backend.presentation.api.containers import Container
from backend.presentation.api.schemas.memory import (
    MemoryInsightsResponse,
    MemoryConsolidationResponse,
    MemoryInitializationResponse,
    RelevantMemoriesResponse,
    ProfileUpdateResponse,
    MemoryConsolidationScheduleResponse
)

logger = logging.getLogger("conversational_commerce")

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/users/{user_id}/insights", response_model=MemoryInsightsResponse)
@inject
async def get_memory_insights(
    user_id: str,
    get_memory_insights_use_case: GetMemoryInsightsUseCase = Depends(
        Provide[Container.application.get_memory_insights_use_case]
    ),
) -> MemoryInsightsResponse:
    """Get memory insights for a user.

    Args:
        user_id: The user's ID
        get_memory_insights_use_case: The GetMemoryInsightsUseCase for retrieving memory insights

    Returns:
        MemoryInsightsResponse containing memory insights

    Raises:
        HTTPException: If there's an error retrieving insights
    """
    try:
        insights = await get_memory_insights_use_case.execute(user_id)
        
        if insights.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=insights.get("error", "Unknown error")
            )
        
        return MemoryInsightsResponse(
            user_id=user_id,
            status=insights.get("status", "success"),
            insights=insights.get("insights", {}),
            message="Memory insights retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting memory insights for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving memory insights: {str(e)}"
        )


@router.post("/users/{user_id}/consolidate", response_model=MemoryConsolidationResponse)
@inject
async def consolidate_user_memories(
    user_id: str,
    consolidate_user_memories_use_case: ConsolidateUserMemoriesUseCase = Depends(
        Provide[Container.application.consolidate_user_memories_use_case]
    ),
) -> MemoryConsolidationResponse:
    """Consolidate memories for a user.

    Args:
        user_id: The user's ID
        consolidate_user_memories_use_case: The ConsolidateUserMemoriesUseCase for consolidating memories

    Returns:
        MemoryConsolidationResponse containing consolidation results

    Raises:
        HTTPException: If there's an error consolidating memories
    """
    try:
        result = await consolidate_user_memories_use_case.execute(user_id)
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Unknown error")
            )
        
        return MemoryConsolidationResponse(
            user_id=user_id,
            status=result.get("status", "success"),
            consolidation_result=result.get("consolidation_result", {}),
            message="Memory consolidation completed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error consolidating memories for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consolidating memories: {str(e)}"
        )


@router.post("/users/{user_id}/initialize", response_model=MemoryInitializationResponse)
@inject
async def initialize_user_memory(
    user_id: str,
    initialize_user_memory_use_case: InitializeUserMemoryUseCase = Depends(
        Provide[Container.application.initialize_user_memory_use_case]
    ),
) -> MemoryInitializationResponse:
    """Initialize memory components for a user.

    Args:
        user_id: The user's ID
        initialize_user_memory_use_case: The InitializeUserMemoryUseCase for initializing memory

    Returns:
        MemoryInitializationResponse containing initialization results

    Raises:
        HTTPException: If there's an error initializing memory
    """
    try:
        result = await initialize_user_memory_use_case.execute(user_id)
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Unknown error")
            )
        
        return MemoryInitializationResponse(
            user_id=user_id,
            status=result.get("status", "success"),
            message="Memory components initialized successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing memory for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing memory: {str(e)}"
        )


@router.get("/users/{user_id}/memories", response_model=RelevantMemoriesResponse)
@inject
async def get_relevant_memories(
    user_id: str,
    query: str,
    limit: int = 5,
    retrieve_relevant_memories_use_case: RetrieveRelevantMemoriesUseCase = Depends(
        Provide[Container.application.retrieve_relevant_memories_use_case]
    ),
) -> RelevantMemoriesResponse:
    """Retrieve relevant memories for a query.

    Args:
        user_id: The user's ID
        query: The query to search for
        limit: Maximum number of memories to return
        retrieve_relevant_memories_use_case: The RetrieveRelevantMemoriesUseCase for retrieving memories

    Returns:
        RelevantMemoriesResponse containing relevant memories

    Raises:
        HTTPException: If there's an error retrieving memories
    """
    try:
        result = await retrieve_relevant_memories_use_case.execute(user_id, query, limit)
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Unknown error")
            )
        
        return RelevantMemoriesResponse(
            user_id=user_id,
            query=query,
            status=result.get("status", "success"),
            memories=result.get("memories", []),
            count=result.get("count", 0),
            message="Relevant memories retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving memories for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving memories: {str(e)}"
        )


@router.put("/users/{user_id}/profile", response_model=ProfileUpdateResponse)
@inject
async def update_user_profile_with_memories(
    user_id: str,
    profile_updates: Dict[str, Any],
    update_user_profile_use_case: UpdateUserProfileWithMemoriesUseCase = Depends(
        Provide[Container.application.update_user_profile_with_memories_use_case]
    ),
) -> ProfileUpdateResponse:
    """Update user profile with memory insights.

    Args:
        user_id: The user's ID
        profile_updates: Dictionary containing profile updates
        update_user_profile_use_case: The UpdateUserProfileWithMemoriesUseCase for updating profile

    Returns:
        ProfileUpdateResponse containing update results

    Raises:
        HTTPException: If there's an error updating profile
    """
    try:
        result = await update_user_profile_use_case.execute(user_id, profile_updates)
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Unknown error")
            )
        
        return ProfileUpdateResponse(
            user_id=user_id,
            status=result.get("status", "success"),
            updated_fields=result.get("updated_fields", []),
            message="User profile updated successfully with memory insights"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )


@router.post("/users/{user_id}/consolidation/schedule", response_model=MemoryConsolidationScheduleResponse)
@inject
async def schedule_memory_consolidation(
    user_id: str,
    session_id: str,
    priority: int = 1,
    schedule_memory_consolidation_use_case: ScheduleMemoryConsolidationUseCase = Depends(
        Provide[Container.application.schedule_memory_consolidation_use_case]
    ),
) -> MemoryConsolidationScheduleResponse:
    """Schedule memory consolidation for a user.

    Args:
        user_id: The user's ID
        session_id: The session ID
        priority: Priority level (1=high, 2=medium, 3=low)
        schedule_memory_consolidation_use_case: The ScheduleMemoryConsolidationUseCase for scheduling consolidation

    Returns:
        MemoryConsolidationScheduleResponse containing scheduling results

    Raises:
        HTTPException: If there's an error scheduling consolidation
    """
    try:
        result = await schedule_memory_consolidation_use_case.execute(user_id, session_id, priority)
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Unknown error")
            )
        
        return MemoryConsolidationScheduleResponse(
            user_id=user_id,
            session_id=session_id,
            priority=priority,
            status=result.get("status", "success"),
            message="Memory consolidation scheduled successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling memory consolidation for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling memory consolidation: {str(e)}"
        )

@router.get("/debug/store/{user_id}")
@inject
async def debug_memory_store(
    user_id: str,
    semantic_memory_service: SemanticMemoryService = Depends(
        Provide[Container.application.semantic_memory_service]
    ),
) -> Dict[str, Any]:
    """Debug endpoint to check what's actually in the InMemoryStore."""
    try:
        # Get all memories for the user from the store
        all_memories = semantic_memory_service.store.search(
            ("conversations", user_id, "memories"),
            limit=1000
        )
        
        # Get store statistics
        store_stats = {
            "total_memories": len(all_memories),
            "user_id": user_id,
            "namespace": ("conversations", user_id, "memories"),
            "store_type": type(semantic_memory_service.store).__name__,
            "memories": []
        }
        
        # Add memory details
        for memory in all_memories:
            memory_info = {
                "key": getattr(memory, 'key', 'unknown'),
                "value": getattr(memory, 'value', {}),
                "created_at": getattr(memory, 'created_at', None),
                "updated_at": getattr(memory, 'updated_at', None),
                "score": getattr(memory, 'score', None)
            }
            store_stats["memories"].append(memory_info)
        
        return store_stats
        
    except Exception as e:
        return {"error": str(e), "user_id": user_id}
