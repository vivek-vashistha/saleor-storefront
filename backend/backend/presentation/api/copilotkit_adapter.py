"""Adapter to make SearchQueryWorkflow compatible with CopilotKit LangGraphAgent."""

import logging
from typing import Any, Dict, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from backend.domain.entities import ChatState
from backend.application.workflows.search_query_workflow import SearchQueryWorkflow

logger = logging.getLogger("copilotkit_adapter")


class ConversationalCommerceAdapter:
    """Adapter to convert between CopilotKit MessagesState and our ChatState."""
    
    def __init__(self, workflow: SearchQueryWorkflow):
        """Initialize the adapter with the SearchQueryWorkflow.
        
        Args:
            workflow: The SearchQueryWorkflow instance
        """
        self.workflow = workflow
    
    async def ainvoke(self, state: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process messages using the SearchQueryWorkflow.
        
        Args:
            state: CopilotKit state containing messages
            config: Optional configuration (unused)
            
        Returns:
            Updated state with AI response
        """
        try:
            logger.info(f"Processing state with {len(state.get('messages', []))} messages")
            
            # Convert MessagesState to ChatState
            chat_state = self._messages_state_to_chat_state(state)
            logger.info(f"Converted to ChatState with {len(chat_state.messages)} messages")
            
            # Process with our workflow
            updated_chat_state = await self.workflow.run(chat_state)
            logger.info(f"Workflow processed, now has {len(updated_chat_state.messages)} messages")
            
            # Convert back to MessagesState
            result = self._chat_state_to_messages_state(updated_chat_state, state)
            logger.info(f"Returning result with {len(result.get('messages', []))} messages")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in ConversationalCommerceAdapter: {e}", exc_info=True)
            # Return original state with error message
            error_message = AIMessage(content=f"I apologize, but I encountered an error: {str(e)}")
            return {
                "messages": state.get("messages", []) + [error_message]
            }
    
    def _messages_state_to_chat_state(self, messages_state: Dict[str, Any]) -> ChatState:
        """Convert CopilotKit state to our ChatState.
        
        Args:
            messages_state: CopilotKit state containing messages
            
        Returns:
            ChatState for our workflow
        """
        messages = []
        
        for msg in messages_state.get("messages", []):
            if isinstance(msg, HumanMessage):
                messages.append({
                    "type": "human",
                    "content": msg.content
                })
            elif isinstance(msg, AIMessage):
                messages.append({
                    "type": "ai", 
                    "content": msg.content
                })
            else:
                # Handle other message types
                content = getattr(msg, 'content', str(msg))
                messages.append({
                    "type": "ai",
                    "content": str(content)
                })
        
        return ChatState(messages=messages)
    
    def _chat_state_to_messages_state(self, chat_state: ChatState, original_state: Dict[str, Any]) -> Dict[str, Any]:
        """Convert our ChatState back to CopilotKit state.
        
        Args:
            chat_state: Our updated ChatState
            original_state: Original state to preserve structure
            
        Returns:
            Updated state
        """
        # Get the new messages that were added by our workflow
        original_message_count = len(original_state.get("messages", []))
        new_messages = chat_state.messages[original_message_count:]
        
        # Convert new messages to LangChain message format
        langchain_messages = []
        for msg in new_messages:
            if msg["type"] == "ai":
                langchain_messages.append(AIMessage(content=msg["content"]))
            elif msg["type"] == "human":
                langchain_messages.append(HumanMessage(content=msg["content"]))
        
        # Return updated state
        return {
            "messages": original_state.get("messages", []) + langchain_messages
        }
    
    def invoke(self, state: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synchronous version - not used by CopilotKit but required for compatibility."""
        import asyncio
        return asyncio.run(self.ainvoke(state, config))
