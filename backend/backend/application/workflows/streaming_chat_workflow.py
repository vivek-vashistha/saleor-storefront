"""Streaming chat workflow for real-time WebSocket communication."""

import logging
from typing import AsyncGenerator, Dict, Any
from backend.application.services.streaming_chat_service import StreamingChatService
from backend.application.use_cases.process_chat_message_use_case import ProcessChatMessageUseCase

logger = logging.getLogger("conversational_commerce.streaming_workflow")


class StreamingChatWorkflow:
    """Workflow for processing chat messages with real-time streaming."""

    def __init__(self, process_chat_message_use_case: ProcessChatMessageUseCase):
        """Initialize the streaming chat workflow.

        Args:
            process_chat_message_use_case: The process chat message use case
        """
        self.process_chat_message_use_case = process_chat_message_use_case

    async def execute_with_streaming(
        self,
        session_id: str,
        session,
        message_content: str,
        referenced_product_ids: list = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute chat message processing with streaming updates.

        Args:
            session_id: The chat session ID
            session: The chat session
            message_content: The message content
            referenced_product_ids: Referenced product IDs

        Yields:
            Dict[str, Any]: Streaming updates and results
        """
        streaming_service = StreamingChatService(session_id)
        
        try:
            # Send initial thinking update
            await streaming_service.send_thinking_update("Analyzing your message...")
            
            # Simulate product search if referenced products
            if referenced_product_ids:
                await streaming_service.send_tool_call_update(
                    "product_search",
                    "started",
                    {"product_count": len(referenced_product_ids)}
                )
                await streaming_service.send_tool_call_update(
                    "product_search",
                    "completed",
                    {"products_found": len(referenced_product_ids)}
                )
            
            # Simulate query analysis
            await streaming_service.send_tool_call_update(
                "query_analysis",
                "started",
                {"message_length": len(message_content)}
            )
            await streaming_service.send_tool_call_update(
                "query_analysis",
                "completed",
                {"intent": "product_inquiry"}
            )
            
            # Process the actual message
            await streaming_service.send_thinking_update("Generating response...")
            
            # Call the actual use case
            updated_session, message_index = await self.process_chat_message_use_case.execute(
                session=session,
                message_content=message_content,
                referenced_product_ids=referenced_product_ids or []
            )
            
            # Send completion update
            await streaming_service.send_tool_call_update(
                "response_generation",
                "completed",
                {"messages_generated": len(updated_session.messages) - len(session.messages)}
            )
            
            # Stream the response messages
            for message in updated_session.messages[message_index:]:
                if hasattr(message, 'content') and message.content:
                    await streaming_service.stream_response(message.content)
                
                # Handle product recommendations
                if hasattr(message, 'recommended_products') and message.recommended_products:
                    from backend.presentation.api.websocket import manager
                    await manager.send_personal_message({
                        "type": "product_recommendations",
                        "products": message.recommended_products,
                        "timestamp": manager._get_timestamp()
                    }, session_id)
            
            # Yield final result
            yield {
                "type": "completion",
                "session": updated_session,
                "message_index": message_index
            }
            
        except Exception as e:
            logger.error(f"Error in streaming workflow: {e}")
            await streaming_service.send_error(f"Processing failed: {str(e)}")
            raise
