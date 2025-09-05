"""
CopilotKit Runtime Endpoint for Conversational Commerce Backend
This endpoint provides the CopilotKit runtime interface for the chat popup
"""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends, Request
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
from backend.application.workflows.search_query_workflow import SearchQueryWorkflow
from backend.infrastructure.factories import AgentFactory

logger = logging.getLogger("conversational_commerce")

router = APIRouter()

# Store session IDs for CopilotKit users
copilot_sessions: Dict[str, str] = {}


class ChatMessage(BaseModel):
    """CopilotKit chat message format"""
    role: str
    content: str


class ChatChoice(BaseModel):
    """CopilotKit chat choice format"""
    index: int
    message: ChatMessage
    finish_reason: str


class UsageInfo(BaseModel):
    """CopilotKit usage info format"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


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
    choices: List[ChatChoice]
    usage: UsageInfo


@router.post("/v1/chat/completions")
@inject
async def chat_completions(
    request: Request,
    create_session_use_case: CreateChatSessionUseCase = Depends(
        Provide[Container.application.create_chat_session_use_case]
    ),
    get_session_use_case: GetChatSessionUseCase = Depends(
        Provide[Container.application.get_chat_session_use_case]
    ),
    process_message_use_case: ProcessChatMessageUseCase = Depends(
        Provide[Container.application.process_chat_message_use_case]
    ),
):
    """
    CopilotKit runtime endpoint for chat completions.
    This bridges to your existing conversational commerce API.
    """
    try:
        # Get the raw request body
        body = await request.json()
        logger.info(f"Raw request body: {body}")
        
        # Handle CopilotKit GraphQL requests
        if "operationName" in body and "query" in body:
            logger.info("Detected CopilotKit GraphQL request")
            operation_name = body.get("operationName")
            
            if operation_name == "availableAgents":
                logger.info("Handling availableAgents query")
                return {
                    "data": {
                        "availableAgents": {
                            "agents": [
                                {
                                    "name": "Shopping Assistant",
                                    "id": "shopping-assistant",
                                    "description": "AI-powered shopping assistant for product search and recommendations",
                                    "__typename": "Agent"
                                }
                            ],
                            "__typename": "AvailableAgents"
                        }
                    }
                }
            elif operation_name == "generateCopilotResponse":
                logger.info("Handling generateCopilotResponse mutation")
                variables = body.get("variables", {})
                data = variables.get("data", {})
                messages = data.get("messages", [])
                
                # Extract the actual user message from CopilotKit format
                user_message = ""
                for msg in messages:
                    if msg.get("textMessage", {}).get("role") == "user":
                        user_message = msg.get("textMessage", {}).get("content", "")
                        break
                
                logger.info(f"Extracted user message: '{user_message}'")
                
                if not user_message or user_message.strip() == "":
                    # Return a simple greeting response
                    greeting_response = "Hello! 👋 I'm your AI shopping assistant. I can help you find products, check order status, and provide personalized recommendations. What can I help you with today?"
                    return {
                        "data": {
                            "generateCopilotResponse": {
                                "threadId": "copilot-thread-123",
                                "runId": "copilot-run-123",
                                "extensions": {
                                    "openaiAssistantAPI": {
                                        "runId": "copilot-run-123",
                                        "threadId": "copilot-thread-123"
                                    }
                                },
                                "status": {
                                    "code": "SUCCESS"
                                },
                                "messages": [
                                    {
                                        "__typename": "TextMessageOutput",
                                        "id": "msg-greeting",
                                        "createdAt": "2025-09-04T13:00:00.000Z",
                                        "status": {
                                            "code": "SUCCESS"
                                        },
                                        "content": greeting_response,
                                        "role": "assistant",
                                        "parentMessageId": None
                                    }
                                ]
                            }
                        }
                    }
                
                # Process the user message and return GraphQL format
                last_message = user_message
                model = "gpt-4"  # Set default model for GraphQL requests
                
                # Generate response using LangGraph agents
                try:
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
                    
                    # Process the message using LangGraph agents
                    updated_session, message_index = await process_message_use_case.execute(
                        session=session, 
                        message_content=last_message,
                        referenced_product_ids=[]
                    )
                    
                    # Get the latest AI message from the session
                    ai_messages = [msg for msg in updated_session.state.messages if msg.get("type") == "ai"]
                    latest_ai_message = ai_messages[-1] if ai_messages else None
                    
                    logger.info(f"LangGraph processed message. AI messages found: {len(ai_messages)}")
                    logger.info(f"Latest AI message: {latest_ai_message}")
                    
                    if latest_ai_message:
                        response_content = latest_ai_message.get("content", "I'm here to help you find the perfect products!")
                        
                        # Handle different message types from LangGraph agents
                        if isinstance(response_content, list):
                            response_content = " ".join(str(item) for item in response_content)
                        
                        logger.info(f"Using LangGraph agent response: {response_content}")
                        
                        # Check if we have product recommendations to include
                        product_recommendations = []
                        if updated_session.state.has_search_query:
                            # Get products from the session state
                            for search_query in updated_session.state.search_queries:
                                # Use the product service to get products for this query
                                from backend.application.services import ProductService
                                product_service = ProductService(
                                    product_repository=Container.infrastructure.neo4j_product_repository(),
                                    saleor_service=Container.application.saleor_service()
                                )
                                products = await product_service.get_products_for_query(search_query, max_num_results=3)
                                product_recommendations.extend(products)
                        
                        # If we have product recommendations, include them in the response
                        if product_recommendations:
                            # Remove duplicates
                            seen_ids = set()
                            unique_products = []
                            for product in product_recommendations:
                                if product.product_id not in seen_ids:
                                    unique_products.append(product)
                                    seen_ids.add(product.product_id)
                            
                            # Format product recommendations
                            product_text = "\n\n**Product Recommendations:**\n"
                            for i, product in enumerate(unique_products[:3], 1):
                                product_text += f"{i}. **{product.name}** - ${product.price}\n"
                                product_text += f"   Category: {product.category}\n"
                                product_text += f"   Description: {product.description[:100]}...\n\n"
                            
                            response_content += product_text
                            logger.info(f"Added {len(unique_products)} product recommendations to response")
                        
                    else:
                        # Generate a simple response based on the user message
                        if "hello" in last_message.lower() or "hi" in last_message.lower():
                            response_content = "Hello! 👋 I'm your AI shopping assistant. I can help you find products, check order status, and provide personalized recommendations. What can I help you with today?"
                        else:
                            response_content = f"Thanks for your message: '{last_message}'. I'm here to help you with your shopping needs. What are you looking for today?"
                        logger.info(f"Generated fallback response: {response_content}")
                    
                    # Return in GraphQL format for CopilotKit with proper streaming structure
                    from datetime import datetime
                    current_time = datetime.now().isoformat() + "Z"
                    
                    response_data = {
                        "data": {
                            "generateCopilotResponse": {
                                "threadId": data.get("threadId", "copilot-thread-123"),
                                "runId": f"run-{uuid.uuid4().hex[:8]}",
                                "extensions": {
                                    "openaiAssistantAPI": {
                                        "runId": f"run-{uuid.uuid4().hex[:8]}",
                                        "threadId": data.get("threadId", "copilot-thread-123")
                                    }
                                },
                                "status": {
                                    "code": "SUCCESS",
                                    "__typename": "BaseResponseStatus"
                                },
                                "messages": [
                                    {
                                        "__typename": "TextMessageOutput",
                                        "id": f"msg-{uuid.uuid4().hex[:8]}",
                                        "createdAt": current_time,
                                        "status": {
                                            "code": "SUCCESS",
                                            "__typename": "SuccessMessageStatus"
                                        },
                                        "content": response_content,
                                        "role": "assistant",
                                        "parentMessageId": None
                                    }
                                ],
                                "metaEvents": [],
                                "__typename": "CopilotResponse"
                            }
                        }
                    }
                    
                    logger.info(f"Returning GraphQL response with content length: {len(response_content)}")
                    logger.info(f"Response content preview: {response_content[:200]}...")
                    return response_data
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    from datetime import datetime
                    current_time = datetime.now().isoformat() + "Z"
                    
                    return {
                        "data": {
                            "generateCopilotResponse": {
                                "threadId": data.get("threadId", "copilot-thread-123"),
                                "runId": f"run-error-{uuid.uuid4().hex[:8]}",
                                "extensions": {
                                    "openaiAssistantAPI": {
                                        "runId": f"run-error-{uuid.uuid4().hex[:8]}",
                                        "threadId": data.get("threadId", "copilot-thread-123")
                                    }
                                },
                                "status": {
                                    "code": "SUCCESS",
                                    "__typename": "BaseResponseStatus"
                                },
                                "messages": [
                                    {
                                        "__typename": "TextMessageOutput",
                                        "id": f"msg-error-{uuid.uuid4().hex[:8]}",
                                        "createdAt": current_time,
                                        "status": {
                                            "code": "SUCCESS",
                                            "__typename": "SuccessMessageStatus"
                                        },
                                        "content": "I'm here to help you find the perfect products! What are you looking for today?",
                                        "role": "assistant",
                                        "parentMessageId": None
                                    }
                                ],
                                "metaEvents": [],
                                "__typename": "CopilotResponse"
                            }
                        }
                    }
            else:
                logger.info(f"Unknown CopilotKit operation: {operation_name}")
                return {
                    "id": "chatcmpl-copilot-unknown",
                    "object": "chat.completion",
                    "created": 1234567890,
                    "model": "gpt-4",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "I'm here to help with your shopping needs!"
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 10,
                        "total_tokens": 10
                    }
                }
        else:
            # Parse the request manually to handle different formats
            messages = body.get("messages", [])
            model = body.get("model", "gpt-4")
            stream = body.get("stream", False)
            
            logger.info(f"Parsed messages: {messages}")
            logger.info(f"Parsed model: {model}")
            logger.info(f"Parsed stream: {stream}")
            
            # Get the last message from the conversation
            last_message = messages[-1].get("content", "") if messages else ""
            logger.info(f"Last message content: '{last_message}'")
        
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
        
        # Process the message using LangGraph agents
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
            content = ai_message.get("content", "I'm here to help with your shopping needs!")
            # Handle case where content might be a list
            if isinstance(content, list):
                assistant_message = " ".join(str(item) for item in content)
            else:
                assistant_message = str(content)
            
            # Check if we have product recommendations to include
            product_recommendations = []
            if updated_session.state.has_search_query:
                # Get products from the session state
                for search_query in updated_session.state.search_queries:
                    # Use the product service to get products for this query
                    from backend.application.services import ProductService
                    product_service = ProductService(
                        product_repository=Container.infrastructure.neo4j_product_repository(),
                        saleor_service=Container.application.saleor_service()
                    )
                    products = await product_service.get_products_for_query(search_query, max_num_results=3)
                    product_recommendations.extend(products)
            
            # If we have product recommendations, include them in the response
            if product_recommendations:
                # Remove duplicates
                seen_ids = set()
                unique_products = []
                for product in product_recommendations:
                    if product.product_id not in seen_ids:
                        unique_products.append(product)
                        seen_ids.add(product.product_id)
                
                # Format product recommendations
                product_text = "\n\n**Product Recommendations:**\n"
                for i, product in enumerate(unique_products[:3], 1):
                    product_text += f"{i}. **{product.name}** - ${product.price}\n"
                    product_text += f"   Category: {product.category}\n"
                    product_text += f"   Description: {product.description[:100]}...\n\n"
                
                assistant_message += product_text
                logger.info(f"Added {len(unique_products)} product recommendations to response")
        else:
            assistant_message = "I received your message and I'm here to help with your shopping needs!"
        
        # Return OpenAI-compatible format for CopilotKit
        return ChatResponse(
            id=f"chatcmpl-{hash(last_message) % 1000000}",
            created=1234567890,
            model=model,
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
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@router.post("/v1/chat/completions/stream")
@inject
async def chat_completions_stream(
    request: Request,
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
            # Get the raw request body
            body = await request.json()
            logger.info(f"Streaming request body: {body}")
            
            # Handle CopilotKit GraphQL requests
            if "operationName" in body and "query" in body:
                logger.info("Detected CopilotKit GraphQL request in streaming")
                operation_name = body.get("operationName")
                
                if operation_name == "generateCopilotResponse":
                    logger.info("Handling generateCopilotResponse mutation in streaming")
                    variables = body.get("variables", {})
                    data = variables.get("data", {})
                    messages = data.get("messages", [])
                    
                    # Extract the actual user message from CopilotKit format
                    user_message = ""
                    for msg in messages:
                        if msg.get("textMessage", {}).get("role") == "user":
                            user_message = msg.get("textMessage", {}).get("content", "")
                            break
                    
                    logger.info(f"Extracted user message in streaming: '{user_message}'")
                    
                    if not user_message or user_message.strip() == "":
                        # Stream a greeting message
                        greeting = "Hello! I'm your AI shopping assistant. I can help you find products, check order status, and provide personalized recommendations. What can I help you with today?"
                        for chunk in greeting.split():
                            yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk + ' '}}]})}\n\n"
                            await asyncio.sleep(0.05)  # Small delay for streaming effect
                        yield "data: [DONE]\n\n"
                        return
                    
                    # Process the user message
                    last_message = user_message
                else:
                    # For other GraphQL operations, return empty stream
                    yield "data: [DONE]\n\n"
                    return
            
            # Parse the request manually
            messages = body.get("messages", [])
            model = body.get("model", "gpt-4")
            
            # Get the last message from the conversation
            last_message = messages[-1].get("content", "") if messages else ""
            
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
                content = ai_message.get("content", "I'm here to help with your shopping needs!")
                # Handle case where content might be a list
                if isinstance(content, list):
                    assistant_message = " ".join(str(item) for item in content)
                else:
                    assistant_message = str(content)
                
                # Check if we have product recommendations to include
                product_recommendations = []
                if updated_session.state.has_search_query:
                    # Get products from the session state
                    for search_query in updated_session.state.search_queries:
                        # Use the product service to get products for this query
                        from backend.application.services import ProductService
                        product_service = ProductService(
                            product_repository=Container.infrastructure.neo4j_product_repository(),
                            saleor_service=Container.application.saleor_service()
                        )
                        products = await product_service.get_products_for_query(search_query, max_num_results=3)
                        product_recommendations.extend(products)
                
                # If we have product recommendations, include them in the response
                if product_recommendations:
                    # Remove duplicates
                    seen_ids = set()
                    unique_products = []
                    for product in product_recommendations:
                        if product.product_id not in seen_ids:
                            unique_products.append(product)
                            seen_ids.add(product.product_id)
                    
                    # Format product recommendations
                    product_text = "\n\n**Product Recommendations:**\n"
                    for i, product in enumerate(unique_products[:3], 1):
                        product_text += f"{i}. **{product.name}** - ${product.price}\n"
                        product_text += f"   Category: {product.category}\n"
                        product_text += f"   Description: {product.description[:100]}...\n\n"
                    
                    assistant_message += product_text
                    logger.info(f"Added {len(unique_products)} product recommendations to streaming response")
            else:
                assistant_message = "I received your message and I'm here to help with your shopping needs!"
            
            # Stream the response
            response_id = f"chatcmpl-{hash(last_message) % 1000000}"
            
            # Send initial chunk
            initial_chunk = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": 1234567890,
                "model": model,
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
                    "model": model,
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
                "model": model,
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


@router.get("/v1/actions")
async def get_actions():
    """Return available actions for CopilotKit."""
    return {
        "actions": [
            {
                "name": "search_products",
                "description": "Search for products based on a query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query for products"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "check_order_status",
                "description": "Check the status of orders for a user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_email": {
                            "type": "string",
                            "description": "Email address of the user"
                        }
                    },
                    "required": ["user_email"]
                }
            },
            {
                "name": "get_product_recommendations",
                "description": "Get personalized product recommendations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_preferences": {
                            "type": "string",
                            "description": "User preferences and requirements"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of recommendations",
                            "default": 5
                        }
                    },
                    "required": ["user_preferences"]
                }
            }
        ]
    }


@router.post("/v1/actions/search_products")
@inject
async def execute_search_products(
    request: Dict[str, Any],
    get_products_from_chat_use_case = Depends(
        Provide[Container.application.get_products_from_chat_use_case]
    ),
    create_session_use_case: CreateChatSessionUseCase = Depends(
        Provide[Container.application.create_chat_session_use_case]
    ),
    get_session_use_case: GetChatSessionUseCase = Depends(
        Provide[Container.application.get_chat_session_use_case]
    ),
    process_message_use_case: ProcessChatMessageUseCase = Depends(
        Provide[Container.application.process_chat_message_use_case]
    ),
):
    """Execute the search_products action using LangGraph agents."""
    try:
        query = request.get("query", "")
        max_results = request.get("max_results", 5)
        
        logger.info(f"CopilotKit action: Searching products with query: '{query}' using LangGraph agents")
        
        # Use a fixed user ID for CopilotKit actions
        copilot_user_id = "copilot-action-user-123"
        
        # Check if we have an existing session for this user
        session_id = copilot_sessions.get(copilot_user_id)
        
        if not session_id:
            # Create a new session
            session = await create_session_use_case.execute(copilot_user_id)
            session_id = session.id
            copilot_sessions[copilot_user_id] = session_id
            logger.info(f"Created new CopilotKit action session: {session_id}")
        
        # Get the session
        session = await get_session_use_case.execute(session_id)
        
        # Process the search query using LangGraph agents
        updated_session, message_index = await process_message_use_case.execute(
            session=session,
            message_content=query,
            referenced_product_ids=[]
        )
        
        # Extract products from the session state
        all_products = []
        
        # Get products from search queries if available
        if updated_session.state.has_search_query:
            for search_query in updated_session.state.search_queries:
                # Use the product service to get products for this query
                from backend.application.services import ProductService
                product_service = ProductService(
                    product_repository=Container.infrastructure.neo4j_product_repository(),
                    saleor_service=Container.application.saleor_service()
                )
                products = await product_service.get_products_for_query(search_query, max_num_results=max_results)
                all_products.extend(products)
        
        # Remove duplicates based on product_id
        seen_ids = set()
        unique_products = []
        for product in all_products:
            if product.product_id not in seen_ids:
                unique_products.append(product)
                seen_ids.add(product.product_id)
        
        return {
            "success": True,
            "result": {
                "products": [
                    {
                        "id": product.product_id,
                        "name": product.name,
                        "price": product.price,
                        "category": product.category,
                        "description": product.description,
                        "image_url": product.image_url,
                        "review_score": product.review_score,
                        "best_for": product.best_for
                    }
                    for product in unique_products[:max_results]
                ],
                "total_found": len(unique_products),
                "search_queries_used": [sq.query for sq in updated_session.state.search_queries]
            }
        }
    except Exception as e:
        logger.error(f"Error in search_products action: {e}")
        return {"success": False, "error": str(e)}


@router.post("/v1/actions/check_order_status")
@inject
async def execute_check_order_status(
    request: Dict[str, Any],
    get_orders_use_case = Depends(
        Provide[Container.application.get_orders_use_case]
    ),
):
    """Execute the check_order_status action."""
    try:
        user_email = request.get("user_email", "")
        
        logger.info(f"CopilotKit action: Checking order status for email: '{user_email}'")
        
        # Get orders using the existing use case
        orders = await get_orders_use_case.execute(user_email)
        
        return {
            "success": True,
            "result": {
                "orders": [
                    {
                        "order_id": order.order_id,
                        "status": order.status.value,
                        "total_amount": order.total_amount,
                        "items": [
                            {
                                "product_id": item.product_id,
                                "quantity": item.quantity,
                                "price": item.price
                            }
                            for item in order.items
                        ]
                    }
                    for order in orders
                ],
                "total_orders": len(orders)
            }
        }
    except Exception as e:
        logger.error(f"Error in check_order_status action: {e}")
        return {"success": False, "error": str(e)}


@router.post("/v1/actions/get_product_recommendations")
@inject
async def execute_get_product_recommendations(
    request: Dict[str, Any],
    get_products_from_chat_use_case = Depends(
        Provide[Container.application.get_products_from_chat_use_case]
    ),
):
    """Execute the get_product_recommendations action."""
    try:
        user_preferences = request.get("user_preferences", "")
        max_results = request.get("max_results", 5)
        
        logger.info(f"CopilotKit action: Getting recommendations for preferences: '{user_preferences}'")
        
        # Create a mock chat state for the recommendations
        from backend.domain.entities import ChatState, SearchQuery, UserProfile
        chat_state = ChatState(
            messages=[],
            search_queries=[SearchQuery(query=user_preferences, categories=[])],
            agent_routing={},
            user_profile=UserProfile(
                email="",
                health_conditions=[],
                activity_preferences=[],
                product_preferences=[],
                budget_range=""
            )
        )
        
        # Get products using the existing use case
        updated_state, bundles = await get_products_from_chat_use_case.execute(chat_state)
        
        # Extract products from bundles
        all_products = []
        for bundle in bundles:
            all_products.extend(bundle.products)
        
        return {
            "success": True,
            "result": {
                "recommendations": [
                    {
                        "id": product.product_id,
                        "name": product.name,
                        "price": product.price,
                        "category": product.category,
                        "description": product.description,
                        "image_url": product.image_url,
                        "reason": f"Recommended based on your preferences: {user_preferences}"
                    }
                    for product in all_products[:max_results]
                ],
                "total_recommendations": len(all_products)
            }
        }
    except Exception as e:
        logger.error(f"Error in get_product_recommendations action: {e}")
        return {"success": False, "error": str(e)}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "copilot-runtime"}


@router.post("/debug")
async def debug_endpoint(request: Request):
    """Debug endpoint to see what CopilotKit is sending."""
    try:
        body = await request.json()
        logger.info(f"DEBUG: Received request body: {body}")
        logger.info(f"DEBUG: Request headers: {dict(request.headers)}")
        return {"received": body, "status": "ok"}
    except Exception as e:
        logger.error(f"DEBUG: Error processing request: {e}")
        return {"error": str(e), "status": "error"}


@router.post("/")
async def root_post():
    """Handle POST requests to root endpoint - CopilotKit discovery."""
    logger.info("Received POST request to CopilotKit root endpoint")
    return {
        "name": "Conversational Commerce Backend",
        "version": "1.0.0",
        "description": "AI-powered shopping assistant with product search and recommendations",
        "endpoints": {
            "chat": "/v1/chat/completions",
            "models": "/v1/models",
            "actions": "/v1/actions"
        }
    }


@router.post("/v1/copilot/runtime")
@inject
async def copilot_runtime(
    request: Request,
    create_session_use_case: CreateChatSessionUseCase = Depends(
        Provide[Container.application.create_chat_session_use_case]
    ),
    get_session_use_case: GetChatSessionUseCase = Depends(
        Provide[Container.application.get_chat_session_use_case]
    ),
    process_message_use_case: ProcessChatMessageUseCase = Depends(
        Provide[Container.application.process_chat_message_use_case]
    ),
):
    """CopilotKit Runtime endpoint that processes messages through LangGraph agents."""
    try:
        # Get the raw request body
        body = await request.json()
        logger.info(f"CopilotKit runtime request: {body}")
        
        # Extract the message from the request
        messages = body.get("messages", [])
        if not messages:
            return {"error": "No messages provided"}
        
        # Get the last user message
        last_message = None
        for message in reversed(messages):
            if message.get("role") == "user":
                last_message = message.get("content", "")
                break
        
        if not last_message:
            return {"error": "No user message found"}
        
        logger.info(f"Processing message through LangGraph agents: '{last_message}'")
        
        # Use a fixed user ID for CopilotKit
        copilot_user_id = "copilot-user-123"
        
        # Check if we have an existing session for this user
        session_id = copilot_sessions.get(copilot_user_id)
        
        if not session_id:
            # Create a new session
            session = await create_session_use_case.execute(copilot_user_id)
            session_id = session.id
            copilot_sessions[copilot_user_id] = session_id
            logger.info(f"Created new session for CopilotKit user: {session_id}")
        else:
            # Get existing session
            session = await get_session_use_case.execute(session_id)
            if not session:
                # Create a new session if the old one doesn't exist
                session = await create_session_use_case.execute(copilot_user_id)
                session_id = session.id
                copilot_sessions[copilot_user_id] = session_id
                logger.info(f"Recreated session for CopilotKit user: {session_id}")
        
        # Process the message using LangGraph agents
        updated_session, message_index = await process_message_use_case.execute(
            session=session,
            message_content=last_message,
            referenced_product_ids=[]
        )
        
        # Get the AI response from the updated session
        ai_message = None
        if updated_session.state.messages and len(updated_session.state.messages) > message_index:
            ai_message = updated_session.state.messages[message_index]
        
        # Format the response for CopilotKit
        if ai_message:
            content = ai_message.get("content", "I'm here to help with your shopping needs!")
            # Handle case where content might be a list
            if isinstance(content, list):
                assistant_message = " ".join(str(item) for item in content)
            else:
                assistant_message = str(content)
            
            # Check if we have product recommendations to include
            product_recommendations = []
            if updated_session.state.has_search_query:
                # Get products from the session state
                for search_query in updated_session.state.search_queries:
                    # Use the product service to get products for this query
                    from backend.application.services import ProductService
                    product_service = ProductService(
                        product_repository=Container.infrastructure.neo4j_product_repository(),
                        saleor_service=Container.application.saleor_service()
                    )
                    products = await product_service.get_products_for_query(search_query, max_num_results=3)
                    product_recommendations.extend(products)
            
            # Add product recommendations to the response if available
            if product_recommendations:
                product_text = "\n\n**Recommended Products:**\n"
                for i, product in enumerate(product_recommendations[:3], 1):
                    product_text += f"{i}. **{product.name}** - ${product.price}\n"
                    if product.description:
                        product_text += f"   {product.description[:100]}...\n"
                assistant_message += product_text
            
            logger.info(f"LangGraph agent response: {assistant_message}")
        else:
            assistant_message = "I received your message and I'm here to help with your shopping needs!"
        
        # Return the response in CopilotKit format
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": assistant_message
                }
            }]
        }
        
    except Exception as e:
        logger.error(f"Error in CopilotKit runtime: {str(e)}", exc_info=True)
        return {
            "error": f"Error processing message: {str(e)}",
            "choices": [{
                "message": {
                    "role": "assistant", 
                    "content": "I'm here to help you find the perfect products! What are you looking for today?"
                }
            }]
        }


@router.get("/")
async def root_get():
    """Handle GET requests to root endpoint - CopilotKit discovery."""
    return {
        "name": "Conversational Commerce Backend",
        "version": "1.0.0",
        "description": "AI-powered shopping assistant with product search and recommendations",
        "endpoints": {
            "chat": "/v1/chat/completions",
            "runtime": "/v1/copilot/runtime",
            "models": "/v1/models",
            "actions": "/v1/actions"
        }
    }
