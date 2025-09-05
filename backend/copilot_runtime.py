"""
CopilotKit Runtime Server - Bridge to your existing conversational commerce API
This server translates CopilotKit requests to your existing backend API
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

# Initialize FastAPI app
app = FastAPI(title="CopilotKit Runtime Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Your existing backend URL
BACKEND_URL = "http://127.0.0.1:8000"

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    message: str
    usage: Optional[Dict[str, Any]] = None

# Store session IDs for CopilotKit users
copilot_sessions: Dict[str, str] = {}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """
    CopilotKit runtime endpoint for chat completions.
    This bridges to your existing conversational commerce API.
    """
    try:
        # Get the last message from the conversation
        last_message = request.messages[-1].content if request.messages else ""
        
        # Use a fixed user ID for CopilotKit
        copilot_user_id = "copilot-user-123"
        
        async with httpx.AsyncClient() as client:
            # Check if we have an existing session for this user
            session_id = copilot_sessions.get(copilot_user_id)
            
            if not session_id:
                # Create a new session
                session_response = await client.post(
                    f"{BACKEND_URL}/v1/sessions",
                    json={
                        "user_id": copilot_user_id,
                        "content": "Hello! I'm your shopping assistant."
                    }
                )
                
                if session_response.status_code != 200:
                    raise HTTPException(status_code=500, detail="Failed to create session")
                
                session_data = session_response.json()
                session_id = session_data["id"]
                copilot_sessions[copilot_user_id] = session_id
                print(f"Created new CopilotKit session: {session_id}")
            
            # Send the message to your existing API
            message_response = await client.post(
                f"{BACKEND_URL}/v1/sessions/{session_id}/message",
                json={
                    "content": last_message,
                    "user_id": copilot_user_id,
                    "referenced_product_ids": []
                }
            )
            
            if message_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to send message")
            
            message_data = message_response.json()
            
            # Extract the AI response from the messages
            ai_message = None
            for msg in reversed(message_data.get("messages", [])):
                if msg.get("type") == "ai":
                    ai_message = msg
                    break
            
            if ai_message:
                assistant_message = ai_message.get("content", "I'm here to help with your shopping needs!")
            else:
                assistant_message = "I received your message and I'm here to help with your shopping needs!"
            
            # Return OpenAI-compatible format for CopilotKit
            return {
                "id": f"chatcmpl-{hash(last_message) % 1000000}",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "gpt-4",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": assistant_message,
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": len(last_message.split()) if last_message else 0,
                    "completion_tokens": len(assistant_message.split()),
                    "total_tokens": len(last_message.split()) + len(assistant_message.split()) if last_message else len(assistant_message.split()),
                },
            }
            
    except Exception as e:
        print(f"Error in chat_completions: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.get("/v1/models")
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
            }
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "copilot-runtime"}

@app.post("/")
async def root_post():
    """Handle POST requests to root endpoint."""
    print("Received POST request to root endpoint")
    return {"message": "CopilotKit Runtime Server", "status": "running"}

@app.get("/")
async def root_get():
    """Handle GET requests to root endpoint."""
    return {"message": "CopilotKit Runtime Server", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
