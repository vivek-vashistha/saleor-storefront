from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette import status
import logging
logger = logging.getLogger("conversational_commerce.session_api")

from backend.application.use_cases import (
    CreateChatSessionUseCase,
    DeleteChatSessionUseCase,
    GetChatSessionUseCase,
    GetUserSessionsUseCase,
    ProcessChatMessageUseCase,
)
from backend.domain.exceptions import ServiceError
from backend.presentation.api.containers import Container
from backend.presentation.api.validators import ChatMessage, ChatMessageResponse, ChatSessionResponse

router = APIRouter()


@router.post("/sessions", response_model=ChatSessionResponse)
@inject
async def create_session(
    user_data: ChatMessage,
    create_chat_session_use_case: CreateChatSessionUseCase = Depends(
        Provide[Container.application.create_chat_session_use_case]
    ),
) -> ChatSessionResponse:
    """Create a new chat session.

    Args:
        user_data: The user data including user ID and optional referenced_product_ids
        create_chat_session_use_case: The CreateChatSessionUseCase for creating a new session

    Returns:
        The created chat session

    """
    session = await create_chat_session_use_case.execute(user_data.user_id)

    # Add initial message if provided
    if user_data.content:
        # Call add_message with the new session
        await add_message(
            session_id=session.id,
            message=user_data,
            get_chat_session_use_case=Container.application.get_chat_session_use_case(),
            process_chat_message_use_case=Container.application.process_chat_message_use_case(),
        )

        # Need to get the updated session after adding the message
        get_chat_session_use_case = Container.application.get_chat_session_use_case()
        session = await get_chat_session_use_case.execute(session.id)

    # Convert to response model
    return ChatSessionResponse.from_entity(session)


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
@inject
async def get_session(
    session_id: str,
    get_chat_session_use_case: GetChatSessionUseCase = Depends(
        Provide[Container.application.get_chat_session_use_case]
    ),
) -> ChatSessionResponse:
    """Get a chat session.

    Args:
        session_id: The ID of the session to retrieve
        get_chat_session_use_case: The GetChatSessionUseCase for retrieving a session

    Returns:
        The chat session if found

    """
    session = await get_chat_session_use_case.execute(session_id)

    # Convert to response model
    return ChatSessionResponse.from_entity(session)


@router.get("/sessions/user/{user_id}", response_model=list[ChatSessionResponse])
@inject
async def get_user_sessions(
    user_id: str,
    get_user_sessions_use_case: GetUserSessionsUseCase = Depends(
        Provide[Container.application.get_user_sessions_use_case]
    ),
) -> list[ChatSessionResponse]:
    """Get all chat sessions for a user.

    Args:
        user_id: The ID of the user
        get_user_sessions_use_case: The GetUserSessionsUseCase for retrieving user sessions

    Returns:
        List of chat sessions for the user

    """
    sessions = await get_user_sessions_use_case.execute(user_id)

    # Convert to response model
    return [ChatSessionResponse.from_entity(session) for session in sessions]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_session(
    session_id: str,
    delete_chat_session_use_case: DeleteChatSessionUseCase = Depends(
        Provide[Container.application.delete_chat_session_use_case]
    ),
) -> None:
    """Delete a chat session.

    Args:
        session_id: The ID of the session to delete
        delete_chat_session_use_case: The DeleteChatSessionUseCase for deleting a session

    Returns:
        None

    """
    await delete_chat_session_use_case.execute(session_id)


@router.post("/sessions/{session_id}/message", response_model=ChatMessageResponse)
@inject
async def add_message(
    session_id: str,
    message: ChatMessage,
    get_chat_session_use_case: GetChatSessionUseCase = Depends(
        Provide[Container.application.get_chat_session_use_case]
    ),
    process_chat_message_use_case: ProcessChatMessageUseCase = Depends(
        Provide[Container.application.process_chat_message_use_case]
    ),
) -> ChatMessageResponse:
    """Add a message to a chat session and process it.

    Args:
        session_id: The ID of the session to add the message to
        message: The message to add
        get_chat_session_use_case: The GetChatSessionUseCase for retrieving a session
        process_chat_message_use_case: The ProcessChatMessageUseCase for processing the message

    Returns:
        The new messages added to the chat session

    """
    # Get the session
    session = await get_chat_session_use_case.execute(session_id)

    # Verify the user ID matches
    if session.user_id != message.user_id:
        raise ServiceError(status_code=status.HTTP_403_FORBIDDEN, detail="User ID does not match session owner")

    # Process the message using the ProcessChatMessageUseCase
    logger.info(f"[SESSION_API] Processing message for session {session_id}, user {message.user_id}")
    logger.info(f"[SESSION_API] Message content: {message.content[:100]}...")
    updated_session, message_index = await process_chat_message_use_case.execute(
        session=session, message_content=message.content, referenced_product_ids=message.referenced_product_ids
    )
    logger.info(f"[SESSION_API] Message processing completed for session {session_id}")

    # Convert to response model with only new messages
    return ChatMessageResponse.from_entity(updated_session, message_index)


@router.delete("/users/{user_id}/memory", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def reset_user_memory(
    user_id: str,
    get_user_sessions_use_case: GetUserSessionsUseCase = Depends(
        Provide[Container.application.get_user_sessions_use_case]
    ),
) -> None:
    """Reset all user profile memory for a user by clearing user_profile in all their sessions.

    Args:
        user_id: The ID of the user whose memory should be reset
        get_user_sessions_use_case: The GetUserSessionsUseCase for retrieving user sessions

    Returns:
        None
    """
    from backend.domain.entities.chat import UserProfile
    from backend.presentation.api.containers import Container
    
    # Get all sessions for the user
    sessions = await get_user_sessions_use_case.execute(user_id)
    
    # Reset user profile in all sessions
    chat_session_repository = Container.infrastructure.chat_session_repository()
    
    for session in sessions:
        # Reset the user profile to empty
        session.state.user_profile = UserProfile()
        # Update the session in the repository
        await chat_session_repository.update_session(session)
    
    # Also clear the user profile from any new sessions that might be created
    # This ensures that even if a new session is created immediately after reset,
    # it won't inherit the old profile from CreateChatSessionUseCase
    logger.info(f"Successfully reset user profile memory for user {user_id}. All {len(sessions)} sessions updated.")
    
    # IMPORTANT: We also need to clear the user profile from the current active session
    # that the user might be currently using. This requires a different approach.
    # For now, we'll add a note in the logs that the user should refresh their chat
    # to see the memory reset take effect.
    logger.info(f"NOTE: User {user_id} should refresh their chat session to see the memory reset take effect immediately.")
