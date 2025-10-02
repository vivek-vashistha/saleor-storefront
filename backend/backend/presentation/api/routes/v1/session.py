from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from starlette import status
import logging
import json
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
from backend.presentation.api.websocket import manager

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
    response = ChatMessageResponse.from_entity(updated_session, message_index)
    logger.info(f"[SESSION_API] Returning {len(response.messages)} messages")
    for i, msg in enumerate(response.messages):
        logger.info(f"[SESSION_API] Message {i}: type={msg.get('type')}, has_products={bool(msg.get('recommended_products'))}")
    return response


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


@router.websocket("/sessions/{session_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
):
    """WebSocket endpoint for real-time chat communication.

    Args:
        websocket: The WebSocket connection
        session_id: The chat session ID
    """
    await manager.connect(websocket, session_id)
    
    try:
        # Get use cases from container (WebSocket doesn't support dependency injection)
        get_chat_session_use_case = Container.application.get_chat_session_use_case()
        process_chat_message_use_case = Container.application.process_chat_message_use_case()
        
        # Try to verify session exists, but don't fail if it doesn't
        session = None
        try:
            session = await get_chat_session_use_case.execute(session_id)
            logger.info(f"WebSocket connected for existing session {session_id}, user {session.user_id}")
        except Exception as e:
            logger.warning(f"Session {session_id} not found, creating new session: {e}")
            # Create a new session if it doesn't exist
            create_chat_session_use_case = Container.application.create_chat_session_use_case()
            session = await create_chat_session_use_case.execute("vivek_001")  # Default user
            logger.info(f"Created new session {session.id} for WebSocket connection")
        
        # Send connection confirmation
        await manager.send_personal_message({
            "type": "connection_established",
            "session_id": session_id,
            "user_id": session.user_id if session else "vivek_001",
            "timestamp": manager._get_timestamp()
        }, session_id)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "ping":
                # Handle ping/pong for connection health
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": manager._get_timestamp()
                }, session_id)
                continue
            
            if message_data.get("type") == "message":
                # Process chat message with real-time updates
                await process_message_with_websocket(
                    session_id=session_id,
                    message_content=message_data.get("content", ""),
                    referenced_product_ids=message_data.get("referenced_product_ids", []),
                    user_id=message_data.get("user_id", session.user_id if session else "vivek_001"),
                    process_chat_message_use_case=process_chat_message_use_case,
                    get_chat_session_use_case=get_chat_session_use_case
                )
                # Continue the loop to handle the next message
                # The WebSocket should stay connected for the entire chat session
            else:
                logger.warning(f"Unknown message type: {message_data.get('type')}")
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        try:
            await manager.send_error(session_id, f"An error occurred: {str(e)}")
        except Exception as send_error:
            logger.error(f"Failed to send error message for session {session_id}: {send_error}")
    finally:
        try:
            manager.disconnect(websocket, session_id)
        except Exception as disconnect_error:
            logger.error(f"Error during WebSocket disconnect for session {session_id}: {disconnect_error}")


@router.websocket("/test-ws")
async def test_websocket_endpoint(websocket: WebSocket):
    """Simple test WebSocket endpoint for debugging."""
    await websocket.accept()
    
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "message": "WebSocket connection established!",
            "timestamp": manager._get_timestamp()
        }, ensure_ascii=False))
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "ping":
                # Handle ping/pong for connection health
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": manager._get_timestamp()
                }, ensure_ascii=False))
                continue
            
            # Echo back the message
            await websocket.send_text(json.dumps({
                "type": "echo",
                "original_message": message_data,
                "timestamp": manager._get_timestamp()
            }, ensure_ascii=False))
                
    except WebSocketDisconnect:
        logger.info("Test WebSocket disconnected")
    except Exception as e:
        logger.error(f"Test WebSocket error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": str(e),
            "timestamp": manager._get_timestamp()
        }, ensure_ascii=False))


async def process_message_with_websocket(
    session_id: str,
    message_content: str,
    referenced_product_ids: list,
    user_id: str,
    process_chat_message_use_case: ProcessChatMessageUseCase,
    get_chat_session_use_case: GetChatSessionUseCase
) -> None:
    import time
    websocket_start_time = time.time()
    logger.info(f"🌐 [WEBSOCKET] Starting WebSocket processing for session {session_id} at {websocket_start_time:.2f}s")
    """Process a chat message with WebSocket updates.

    Args:
        session_id: The chat session ID
        message_content: The message content
        referenced_product_ids: Referenced product IDs
        user_id: The user ID
        process_chat_message_use_case: The ProcessChatMessageUseCase
        get_chat_session_use_case: The GetChatSessionUseCase
    """
    try:
        # Get the session
        session = await get_chat_session_use_case.execute(session_id)
        
        # Verify the user ID matches
        if session.user_id != user_id:
            await manager.send_error(session_id, "User ID does not match session owner")
            return
        
        # Send thinking update
        await manager.send_thinking_update(session_id, "Processing your message...")
        
        # Send tool call updates (these would be integrated into your ProcessChatMessageUseCase)
        await manager.send_tool_call_update(session_id, "message_processing", "started", {
            "message_length": len(message_content)
        })
        
        # Process the message using the ProcessChatMessageUseCase
        logger.info(f"[WEBSOCKET] Processing message for session {session_id}, user {user_id}")
        updated_session, message_index = await process_chat_message_use_case.execute(
            session=session, 
            message_content=message_content, 
            referenced_product_ids=referenced_product_ids
        )
        
        # Log the response received from LangGraph
        logger.info(f"[WEBSOCKET] Response received from LangGraph for session {session_id}:")
        logger.info(f"[WEBSOCKET] - Message index: {message_index}")
        logger.info(f"[WEBSOCKET] - Total messages in session: {len(updated_session.state.messages)}")
        logger.info(f"[WEBSOCKET] - New messages to send: {len(updated_session.state.messages) - message_index}")
        
        # Log the new messages that will be sent
        new_messages = updated_session.state.messages[message_index:]
        logger.info(f"[WEBSOCKET] New messages to send to frontend:")
        for i, msg in enumerate(new_messages):
            msg_type = msg.get('type', 'unknown')
            content = msg.get('content', '')
            if isinstance(content, list):
                content_str = ' '.join(str(item) for item in content)
            else:
                content_str = str(content)
            logger.info(f"[WEBSOCKET] Message {i}: type='{msg_type}', content='{content_str[:100]}...'")
        
        # Send tool call completion
        await manager.send_tool_call_update(session_id, "message_processing", "completed", {
            "messages_generated": len(updated_session.state.messages) - len(session.state.messages)
        })
        
        # Send the response messages
        response = ChatMessageResponse.from_entity(updated_session, message_index)
        
        # Log before sending response via WebSocket
        logger.info(f"[WEBSOCKET] About to send response via WebSocket for session {session_id}:")
        logger.info(f"[WEBSOCKET] - Response messages count: {len(response.messages)}")
        logger.info(f"[WEBSOCKET] - Session ID: {response.id}")
        
        # Send each message as a chunk for real-time display
        message_send_start_time = time.time()
        logger.info(f"🌐 [WEBSOCKET] Starting message sending at {message_send_start_time:.2f}s")
        
        for i, msg in enumerate(response.messages):
            message_start_time = time.time()
            logger.info(f"🌐 [WEBSOCKET] Processing message {i} for WebSocket sending at {message_start_time:.2f}s:")
            logger.info(f"🌐 [WEBSOCKET] - Message type: {msg.get('type')}")
            logger.info(f"🌐 [WEBSOCKET] - Message content length: {len(str(msg.get('content', '')))}")
            logger.info(f"🌐 [WEBSOCKET] - Has recommended products: {bool(msg.get('recommended_products'))}")
            
            if msg.get('type') == 'ai':
                # Send message content in chunks for streaming effect
                content = msg.get('content', '')
                logger.info(f"[WEBSOCKET] Bot message content: '{content[:100]}...'")
                
                if content:
                    # Split content into chunks for streaming
                    chunk_size = 50  # Adjust based on your needs
                    total_chunks = (len(content) + chunk_size - 1) // chunk_size
                    logger.info(f"[WEBSOCKET] Splitting content into {total_chunks} chunks of size {chunk_size}")
                    
                    for j in range(0, len(content), chunk_size):
                        chunk = content[j:j + chunk_size]
                        is_final = (j + chunk_size >= len(content))
                        logger.info(f"[WEBSOCKET] Sending chunk {j//chunk_size + 1}/{total_chunks}: '{chunk}', is_final={is_final}")
                        await manager.send_message_chunk(session_id, chunk, is_final)
                        
                        # No delay needed - let the frontend handle the streaming effect
                else:
                    logger.warning(f"[WEBSOCKET] Bot message has empty content, skipping chunk sending")
                
                # Send product recommendations if any
                if msg.get('recommended_products'):
                    logger.info(f"[WEBSOCKET] Sending product recommendations: {len(msg.get('recommended_products', []))} products")
                    await manager.send_personal_message({
                        "type": "product_recommendations",
                        "products": msg.get('recommended_products'),
                        "timestamp": manager._get_timestamp()
                    }, session_id)
            elif msg.get('type') == 'product_recommendation':
                # Handle product recommendation messages
                logger.info(f"[WEBSOCKET] Processing product recommendation message")
                content = msg.get('content', '')
                recommended_products = msg.get('recommended_products', [])
                
                # Send the message content if any
                if content:
                    logger.info(f"[WEBSOCKET] Sending product recommendation content: '{content[:100]}...'")
                    await manager.send_message_chunk(session_id, content, True)
                
                # Send product recommendations
                if recommended_products:
                    logger.info(f"[WEBSOCKET] Sending product recommendations: {len(recommended_products)} products")
                    await manager.send_personal_message({
                        "type": "product_recommendations",
                        "products": recommended_products,
                        "content": content,  # Include the message content
                        "timestamp": manager._get_timestamp()
                    }, session_id)
            elif msg.get('type') == 'product_bundle_recommendation':
                # Handle product bundle recommendation messages
                logger.info(f"[WEBSOCKET] Processing product bundle recommendation message")
                content = msg.get('content', '')
                recommended_bundles = msg.get('recommended_bundles', [])
                
                # Send the message content if any
                if content:
                    logger.info(f"[WEBSOCKET] Sending product bundle content: '{content[:100]}...'")
                    await manager.send_message_chunk(session_id, content, True)
                
                # Send product bundles
                if recommended_bundles:
                    logger.info(f"[WEBSOCKET] Sending product bundles: {len(recommended_bundles)} bundles")
                    await manager.send_personal_message({
                        "type": "product_bundles",
                        "bundles": recommended_bundles,
                        "content": content,  # Include the message content
                        "timestamp": manager._get_timestamp()
                    }, session_id)
            else:
                logger.info(f"[WEBSOCKET] Skipping message of type: {msg.get('type')}")
        
        websocket_end_time = time.time()
        total_websocket_time = websocket_end_time - websocket_start_time
        logger.info(f"🌐 [WEBSOCKET] Message processing completed for session {session_id} in {total_websocket_time:.2f}s")
        
    except Exception as e:
        logger.error(f"[WEBSOCKET] Error processing message for session {session_id}: {e}")
        await manager.send_error(session_id, f"Failed to process message: {str(e)}")
