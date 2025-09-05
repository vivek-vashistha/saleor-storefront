"""
CopilotKit Runtime Endpoint for Conversational Commerce Backend
This endpoint provides the CopilotKit runtime interface for the chat popup
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dependency_injector.wiring import Provide, inject

from backend.presentation.api.containers import Container
from backend.application.use_cases import (
    CreateChatSessionUseCase,
    GetChatSessionUseCase,
    ProcessChatMessageUseCase,
)
from backend.domain.entities import ChatSession

logger = logging.getLogger("conversational_commerce")

router = APIRouter()

# Store session IDs for CopilotKit users
copilot_sessions: Dict[str, str] = {}


class ChatMessage(BaseModel):
    """CopilotKit chat message format"""
    role: str
    content: str


class ChatRequest(BaseModel):
    """CopilotKit chat request format"""
    messages: List[ChatMessage]
    model: Optional[str] = "gpt-4"
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    """CopilotKit chat response format"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


@router.post("/v1/chat/completions")
@inject
async def chat_completions(
    request: ChatRequest,
    create_session_use_case: CreateChatSessionUseCase = Depends(
        Provide[Container.application.create_chat_session_use_case]
    ),
    get_session_use_case: GetChatSessionUseCase = Depends(
        Provide[Container.application.get_chat_session_use_case]
    ),
    process_message_use_case: ProcessChatMessageUseCase = Depends(
        Provide[Container.application.process_chat_message_use_case]
    ),
) -> ChatResponse:
    """
    CopilotKit runtime endpoint for chat completions.
    This bridges to your existing conversational commerce API.
    """
    try:
        # Get the last message from the conversation
        last_message = request.messages[-1].content if request.messages else ""
        
        # Use a fixed user ID for CopilotKit
        copilot_user_id = "copilot-user-123"
        
        # Check if we have an existing session for this user
        session_id = copilot_sessions.get(copilot_user_id)
        
        if not session_id:
            # Create a new session
            session = await create_session_use_case.execute(copilot_user_id)
            session_id = session.id
            copilot_sessions[copilot_user_id] = session_id
            logger.info(f"Created new CopilotKit session: {session_id}")
        
        # Get the session
        session = await get_session_use_case.execute(session_id)
        
        # Process the message using your existing use case
        updated_session, message_index = await process_message_use_case.execute(
            session=session,
            message_content=last_message,
            referenced_product_ids=[]
        )
        
        # Extract the AI response from the messages
        ai_message = None
        for msg in reversed(updated_session.state.messages[message_index:]):
            if msg.get("type") == "ai":
                ai_message = msg
                break
        
        if ai_message:
            assistant_message = ai_message.get("content", "I'm here to help with your shopping needs!")
        else:
            assistant_message = "I received your message and I'm here to help with your shopping needs!"
        
        # Return OpenAI-compatible format for CopilotKit
        return ChatResponse(
            id=f"chatcmpl-{hash(last_message) % 1000000}",
            created=1234567890,
            model=request.model or "gpt-4",
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": assistant_message,
                    },
                    "finish_reason": "stop",
                }
            ],
            usage={
                "prompt_tokens": len(last_message.split()) if last_message else 0,
                "completion_tokens": len(assistant_message.split()),
                "total_tokens": len(last_message.split()) + len(assistant_message.split()) if last_message else len(assistant_message.split()),
            }
        )
        
    except Exception as e:
        logger.error(f"Error in chat_completions: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@router.post("/v1/chat/completions/stream")
@inject
async def chat_completions_stream(
    request: ChatRequest,
    create_session_use_case: CreateChatSessionUseCase = Depends(
        Provide[Container.application.create_chat_session_use_case]
    ),
    get_session_use_case: GetChatSessionUseCase = Depends(
        Provide[Container.application.get_chat_session_use_case]
    ),
    process_message_use_case: ProcessChatMessageUseCase = Depends(
        Provide[Container.application.process_chat_message_use_case]
    ),
) -> StreamingResponse:
    """
    Streaming version of chat completions for real-time responses.
    """
    async def generate_stream():
        try:
            # Get the last message from the conversation
            last_message = request.messages[-1].content if request.messages else ""
            
            # Use a fixed user ID for CopilotKit
            copilot_user_id = "copilot-user-123"
            
            # Check if we have an existing session for this user
            session_id = copilot_sessions.get(copilot_user_id)
            
            if not session_id:
                # Create a new session
                session = await create_session_use_case.execute(copilot_user_id)
                session_id = session.id
                copilot_sessions[copilot_user_id] = session_id
                logger.info(f"Created new CopilotKit session: {session_id}")
            
            # Get the session
            session = await get_session_use_case.execute(session_id)
            
            # Process the message using your existing use case
            updated_session, message_index = await process_message_use_case.execute(
                session=session,
                message_content=last_message,
                referenced_product_ids=[]
            )
            
            # Extract the AI response from the messages
            ai_message = None
            for msg in reversed(updated_session.state.messages[message_index:]):
                if msg.get("type") == "ai":
                    ai_message = msg
                    break
            
            if ai_message:
                assistant_message = ai_message.get("content", "I'm here to help with your shopping needs!")
            else:
                assistant_message = "I received your message and I'm here to help with your shopping needs!"
            
            # Stream the response
            response_id = f"chatcmpl-{hash(last_message) % 1000000}"
            
            # Send initial chunk
            initial_chunk = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": 1234567890,
                "model": request.model or "gpt-4",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant"},
                        "finish_reason": None
                    }
                ]
            }
            yield f"data: {json.dumps(initial_chunk)}\n\n"
            
            # Stream the content word by word
            words = assistant_message.split()
            for i, word in enumerate(words):
                chunk = {
                    "id": response_id,
                    "object": "chat.completion.chunk",
                    "created": 1234567890,
                    "model": request.model or "gpt-4",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": word + " "},
                            "finish_reason": None
                        }
                    ]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)  # Small delay for streaming effect
            
            # Send final chunk
            final_chunk = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": 1234567890,
                "model": request.model or "gpt-4",
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }
                ]
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            error_chunk = {
                "error": {
                    "message": f"Error processing chat: {str(e)}",
                    "type": "server_error"
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@router.get("/v1/models")
async def get_models():
    """Return available models for CopilotKit."""
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-4",
                "object": "model",
                "created": 1234567890,
                "owned_by": "openai"
            },
            {
                "id": "gpt-4o",
                "object": "model",
                "created": 1234567890,
                "owned_by": "openai"
            }
        ]
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "copilot-runtime"}


@router.post("/")
async def root_post():
    """Handle POST requests to root endpoint."""
    logger.info("Received POST request to CopilotKit root endpoint")
    return {"message": "CopilotKit Runtime Server", "status": "running"}


@router.get("/")
async def root_get():
    """Handle GET requests to root endpoint."""
    return {"message": "CopilotKit Runtime Server", "status": "running"}
