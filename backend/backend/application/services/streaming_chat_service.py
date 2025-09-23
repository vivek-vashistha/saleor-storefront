"""Streaming chat service for real-time WebSocket communication."""

import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from backend.presentation.api.websocket import manager

logger = logging.getLogger("conversational_commerce.streaming_chat")


class StreamingChatService:
    """Service for handling streaming chat responses with WebSocket updates."""

    def __init__(self, session_id: str):
        """Initialize the streaming chat service.

        Args:
            session_id: The chat session ID
        """
        self.session_id = session_id

    async def send_thinking_update(self, thinking: str) -> None:
        """Send a thinking update to the frontend.

        Args:
            thinking: The current thinking status
        """
        await manager.send_thinking_update(self.session_id, thinking)

    async def send_tool_call_update(
        self, 
        tool_name: str, 
        status: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send a tool call update to the frontend.

        Args:
            tool_name: The name of the tool being called
            status: The status of the tool call (started, completed, error)
            data: Additional data about the tool call
        """
        await manager.send_tool_call_update(self.session_id, tool_name, status, data)

    async def send_message_chunk(self, chunk: str, is_final: bool = False) -> None:
        """Send a message chunk to the frontend.

        Args:
            chunk: The message chunk
            is_final: Whether this is the final chunk
        """
        await manager.send_message_chunk(self.session_id, chunk, is_final)

    async def send_error(self, error_message: str) -> None:
        """Send an error message to the frontend.

        Args:
            error_message: The error message
        """
        await manager.send_error(self.session_id, error_message)

    async def stream_response(self, response_text: str, chunk_size: int = 50) -> None:
        """Stream a response text in chunks.

        Args:
            response_text: The complete response text
            chunk_size: The size of each chunk
        """
        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i + chunk_size]
            is_final = (i + chunk_size >= len(response_text))
            
            await self.send_message_chunk(chunk, is_final)
            
            # Small delay for streaming effect
            await asyncio.sleep(0.05)

    async def simulate_tool_calls(self, tool_calls: list) -> None:
        """Simulate tool call execution with updates.

        Args:
            tool_calls: List of tool calls to simulate
        """
        for tool_call in tool_calls:
            tool_name = tool_call.get('name', 'unknown_tool')
            
            # Send tool started update
            await self.send_tool_call_update(
                tool_name, 
                'started', 
                {'description': tool_call.get('description', 'Processing...')}
            )
            
            # Simulate tool execution time
            await asyncio.sleep(1)
            
            # Send tool completed update
            await self.send_tool_call_update(
                tool_name, 
                'completed', 
                {'result': tool_call.get('result', 'Success')}
            )

    async def process_with_streaming(
        self, 
        process_function, 
        *args, 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Process a function with streaming updates.

        Args:
            process_function: The function to process
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function

        Yields:
            str: Chunks of the response
        """
        try:
            # Send thinking update
            await self.send_thinking_update("Starting processing...")
            
            # Simulate some tool calls
            sample_tools = [
                {'name': 'search_products', 'description': 'Searching for relevant products'},
                {'name': 'analyze_query', 'description': 'Analyzing user query'},
                {'name': 'generate_response', 'description': 'Generating response'}
            ]
            
            await self.simulate_tool_calls(sample_tools)
            
            # Process the actual function
            await self.send_thinking_update("Processing your request...")
            result = await process_function(*args, **kwargs)
            
            # Stream the result
            if isinstance(result, str):
                await self.stream_response(result)
            else:
                # Handle other result types
                await self.send_message_chunk(str(result), is_final=True)
                
        except Exception as e:
            logger.error(f"Error in streaming processing: {e}")
            await self.send_error(f"Processing error: {str(e)}")
            raise
