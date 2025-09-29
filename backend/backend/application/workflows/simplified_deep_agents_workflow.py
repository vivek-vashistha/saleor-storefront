"""Simplified Deep Agents workflow that directly uses the Deep Agent."""

import logging
from typing import Union

from backend.domain.entities.chat import ChatState
from backend.domain.entities.enhanced_chat import EnhancedChatState
from backend.application.interfaces import IChatWorkflow
from backend.application.agents.conversational_commerce_deep_agent import ConversationalCommerceDeepAgent

logger = logging.getLogger("conversational_commerce.simplified_deep_agents_workflow")


class SimplifiedDeepAgentsWorkflow(IChatWorkflow[Union[ChatState, EnhancedChatState]]):
    """Simplified Deep Agents workflow that directly uses the Deep Agent."""

    def __init__(self, deep_agent: ConversationalCommerceDeepAgent):
        """Initialize the simplified workflow.
        
        Args:
            deep_agent: The Deep Agent instance to use
        """
        self.deep_agent = deep_agent
        logger.info("Simplified Deep Agents workflow initialized")

    def _build_graph(self):
        """No graph needed - we use the Deep Agent directly."""
        return None

    async def run(self, state: Union[ChatState, EnhancedChatState]) -> Union[ChatState, EnhancedChatState]:
        """Process a chat query using the Deep Agent directly.
        
        Args:
            state: The current chat state
            
        Returns:
            Updated chat state with Deep Agent response
        """
        try:
            logger.info(f"Processing Deep Agents workflow for user {state.user_id}")
            
            # Extract user message from state
            user_message = self._extract_user_message(state)
            if not user_message:
                logger.warning("No user message found for processing")
                return state
            
            # Process with Deep Agent pipeline
            logger.info(f"🔍 DeepAgent: Processing message: {user_message[:50]}...")
            response_text = await self.deep_agent._deep_agent_processing_pipeline(
                user_message, state.user_id, getattr(state, 'session_id', None), state.messages
            )
            
            # Add the response to the state
            if response_text:
                state.add_message(response_text, is_human=False)
                logger.info("🔍 DeepAgent: Response added to state successfully")
            else:
                logger.warning("🔍 DeepAgent: No response content found")
                fallback_response = "I'm sorry, I didn't receive a proper response. Please try again."
                state.add_message(fallback_response, is_human=False)
                logger.info("🔍 DeepAgent: Added fallback response")
            
            logger.info(f"Deep Agents workflow completed for user {state.user_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error in Deep Agents workflow: {e}")
            # Fallback response
            state.add_message(
                "I'm sorry, I encountered an error processing your request. Please try again.",
                is_human=False
            )
            return state

    def _extract_user_message(self, state: Union[ChatState, EnhancedChatState]) -> str:
        """Extract the latest user message from the state.
        
        Args:
            state: The chat state
            
        Returns:
            The latest user message
        """
        try:
            for msg in reversed(state.messages):
                if msg.get('type') == 'human':
                    content = msg.get('content', '')
                    if isinstance(content, list):
                        content = ' '.join(str(item) for item in content)
                    return str(content)
            return ""
        except Exception as e:
            logger.error(f"Error extracting user message: {e}")
            return ""
