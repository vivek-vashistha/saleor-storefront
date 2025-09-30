"""
Minimal Deep Agent Workflow
Integrates the deep agent with existing chat session system.
"""

import logging
from typing import Optional
from backend.domain.entities import ChatState
from backend.application.services import ProductService, OrderGraphService
from backend.application.services.semantic_memory_service import SemanticMemoryService
from backend.application.services.hybrid_memory_service import HybridMemoryService
from backend.application.agents.deepagents_commerce.agent import create_agent_with_model
from backend.application.agents.deepagents_commerce.tools import configure_services

logger = logging.getLogger("conversational_commerce")

class DeepAgentWorkflow:
    """Minimal workflow that uses the deep agent."""
    
    def __init__(
        self,
        product_service: ProductService,
        order_graph_service: Optional[OrderGraphService] = None,
        hybrid_memory_service: Optional[HybridMemoryService] = None,
        semantic_memory_service: Optional[SemanticMemoryService] = None,
        llm=None
    ):
        """Initialize the deep agent workflow."""
        self.product_service = product_service
        self.order_graph_service = order_graph_service
        self.hybrid_memory_service = hybrid_memory_service
        self.semantic_memory_service = semantic_memory_service
        self.llm = llm
        
        # Configure the tools with real services
        configure_services(
            product_svc=product_service,
            order_svc=order_graph_service.order_service if order_graph_service else None,
            hybrid_mem=hybrid_memory_service,
            semantic_mem=semantic_memory_service,
            llm_model=llm
        )
        
        # Create the agent with the proper model
        self.agent = create_agent_with_model(llm)
    
    async def run(self, state: ChatState) -> ChatState:
        """Run the deep agent workflow on the chat state."""
        try:
            logger.info("Starting deep agent workflow")
            
            # Convert chat state to agent format
            messages = []
            for msg in state.messages:
                if msg.get('type') == 'human':
                    messages.append({"role": "user", "content": msg.get('content', '')})
                elif msg.get('type') == 'ai':
                    messages.append({"role": "assistant", "content": msg.get('content', '')})
            
            # Create thread configuration
            thread_cfg = {"configurable": {"thread_id": f"user_{state.user_id}"}}
            
            # Run the agent
            logger.info(f"Running deep agent with {len(messages)} messages")
            
            # Stream the agent response
            for event in self.agent.stream({"messages": messages}, config=thread_cfg):
                logger.debug(f"Deep agent stream event: {event}")
                
                # Handle different event types based on logs analysis
                event_type = self._get_event_type(event)
                logger.debug(f"Event type: {event_type}")
                
                if event_type == "model_request":
                    # Handle AI model responses
                    self._handle_model_request(event, state)
                elif event_type == "tool_call":
                    # Handle tool calls (for future intermediate results)
                    self._handle_tool_call(event, state)
                elif event_type == "tool_result":
                    # Handle tool results (for future intermediate results)
                    self._handle_tool_result(event, state)
                elif event_type == "middleware":
                    # Handle middleware events (SummarizationMiddleware, HumanInTheLoopMiddleware, etc.)
                    self._handle_middleware_event(event, state)
                elif event_type == "messages":
                    # Handle direct messages
                    self._handle_messages_event(event, state)
                elif event_type == "response":
                    # Handle final response with recommendations
                    self._handle_response_event(event, state)
                else:
                    logger.debug(f"Unhandled event type: {event_type}")
            logger.info("Deep agent workflow completed successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in deep agent workflow: {e}", exc_info=True)
            # Add error message to state
            state.add_message(
                "I'm sorry, I encountered an error while processing your request. Please try again.",
                is_human=False
            )
            return state
    
    def _get_event_type(self, event: dict) -> str:
        """Determine the event type based on the event structure."""
        if "model_request" in event:
            return "model_request"
        elif "tool_call" in event or "tool_calls" in event:
            return "tool_call"
        elif "tool_result" in event or "tool_results" in event:
            return "tool_result"
        elif any(key.endswith("Middleware") for key in event.keys()):
            return "middleware"
        elif "messages" in event:
            return "messages"
        elif "response" in event:
            return "response"
        else:
            return "unknown"
    
    def _handle_model_request(self, event: dict, state: ChatState):
        """Handle model_request events (AI responses)."""
        if "messages" in event["model_request"]:
            for message in event["model_request"]["messages"]:
                if hasattr(message, 'content') and message.content:
                    state.add_message(message.content, is_human=False)
                    logger.info(f"Agent response: {message.content}")
    
    def _handle_tool_call(self, event: dict, state: ChatState):
        """Handle tool call events (for future intermediate results display)."""
        logger.info(f"Tool call event: {event}")
        # TODO: Add intermediate tool call display
        # This will be used to show what tools the agent is calling
    
    def _handle_tool_result(self, event: dict, state: ChatState):
        """Handle tool result events (for future intermediate results display)."""
        logger.info(f"Tool result event: {event}")
        # TODO: Add intermediate tool result display
        # This will be used to show tool execution results
    
    def _handle_middleware_event(self, event: dict, state: ChatState):
        """Handle middleware events (SummarizationMiddleware, HumanInTheLoopMiddleware, etc.)."""
        middleware_name = [key for key in event.keys() if key.endswith("Middleware")][0]
        logger.debug(f"Middleware event: {middleware_name}")
        # These are typically internal events, no action needed
    
    def _handle_messages_event(self, event: dict, state: ChatState):
        """Handle direct messages events."""
        for message in event["messages"]:
            if hasattr(message, 'content') and message.content:
                state.add_message(message.content, is_human=False)
                logger.info(f"Agent response: {message.content}")
    
    def _handle_response_event(self, event: dict, state: ChatState):
        """Handle final response events with recommendations."""
        final_response = event["response"]
        logger.info(f"Final agent response: {final_response}")
        
        if isinstance(final_response, dict):
            if "message" in final_response:
                # Add the main message
                state.add_message(final_response["message"], is_human=False)
                
                # Add product bundles if available
                if "bundles" in final_response and final_response["bundles"]:
                    state.add_ai_message_with_product_bundles(final_response["bundles"])
                    logger.info(f"Added {len(final_response['bundles'])} product bundles to state")
            
            
