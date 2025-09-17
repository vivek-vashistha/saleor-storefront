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

            # Ensure at least one assistant message appears for this turn
            try:
                original_len = len(state.get("messages", []))
                new_msgs = result.get("messages", [])[original_len:]
                has_ai = False
                from langchain_core.messages import AIMessage as _AIMessage
                for m in new_msgs:
                    try:
                        if isinstance(m, _AIMessage):
                            has_ai = True
                            break
                    except Exception:
                        pass
                if not has_ai:
                    # Fallback guidance so the UI shows a reply
                    fallback = _AIMessage(content=(
                        "I'm ready to help with outdoor gear. Could you share more details "
                        "about your activity, terrain, weather conditions, and budget?"
                    ))
                    result["messages"] = result.get("messages", []) + [fallback]
            except Exception:
                pass
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
        messages: List[Dict[str, Any]] = []

        def _to_text(value: Any) -> str:
            try:
                if value is None:
                    return ""
                if isinstance(value, str):
                    return value
                if isinstance(value, list):
                    # Join list items as lines
                    return "\n".join(_to_text(v) for v in value)
                if isinstance(value, dict):
                    import json as _json
                    return _json.dumps(value, ensure_ascii=False)
                # LangChain message-like
                if hasattr(value, "content"):
                    return _to_text(getattr(value, "content"))
                return str(value)
            except Exception:
                return str(value)

        for msg in messages_state.get("messages", []):
            # 1) Native LangChain messages
            if isinstance(msg, HumanMessage):
                messages.append({"type": "human", "content": _to_text(msg.content)})
                continue
            if isinstance(msg, AIMessage):
                messages.append({"type": "ai", "content": _to_text(msg.content)})
                continue

            # 2) Dict payloads (common in CopilotKit runtime)
            if isinstance(msg, dict):
                role = msg.get("role") or msg.get("type")  # accept either key
                content = _to_text(msg.get("content", ""))

                if role in ("user", "human"):
                    messages.append({"type": "human", "content": content})
                elif role in ("assistant", "ai"):
                    messages.append({"type": "ai", "content": content})
                else:
                    # Unknown role: treat as human input to drive the workflow
                    messages.append({"type": "human", "content": content})
                continue

            # 3) Fallback: any other object with 'content' attribute
            content = _to_text(getattr(msg, "content", msg))
            # Default to human to ensure the workflow processes input
            messages.append({"type": "human", "content": content})

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
        def _to_text(value: Any) -> str:
            try:
                if value is None:
                    return ""
                if isinstance(value, str):
                    return value
                if isinstance(value, list):
                    return "\n".join(_to_text(v) for v in value)
                if isinstance(value, dict):
                    import json as _json
                    return _json.dumps(value, ensure_ascii=False)
                if hasattr(value, "content"):
                    return _to_text(getattr(value, "content"))
                return str(value)
            except Exception:
                return str(value)

        for msg in new_messages:
            msg_type = msg.get("type")
            content = _to_text(msg.get("content", ""))

            if msg_type == "ai":
                langchain_messages.append(AIMessage(content=content))
            elif msg_type == "human":
                langchain_messages.append(HumanMessage(content=content))
            else:
                # Fallback for custom message types like product_recommendation/product_bundle_recommendation
                # Always surface the textual content to the UI
                try:
                    extra = []
                    if "recommended_products" in msg and isinstance(msg["recommended_products"], list):
                        extra.append(f"Products: {len(msg['recommended_products'])}")
                    if "recommended_bundles" in msg and isinstance(msg["recommended_bundles"], list):
                        extra.append(f"Bundles: {len(msg['recommended_bundles'])}")
                    suffix = ("\n" + "\n".join(extra)) if extra else ""
                    langchain_messages.append(AIMessage(content=f"{content}{suffix}".strip()))
                except Exception:
                    langchain_messages.append(AIMessage(content=str(content)))
        
        # Return updated state
        return {
            "messages": original_state.get("messages", []) + langchain_messages
        }
    
    def invoke(self, state: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synchronous version - not used by CopilotKit but required for compatibility."""
        import asyncio
        return asyncio.run(self.ainvoke(state, config))
