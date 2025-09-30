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
                logger.info(f"Deep agent stream event: {event}")
                
                # Handle different event types based on logs analysis
                event_type = self._get_event_type(event)
                logger.info(f"Event type: {event_type}")
                
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
                    logger.info(f"Unhandled event type: {event_type}")
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
        elif "tools" in event:
            return "tool_result"
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
        
        # Handle tools event structure from logs (e.g., {'tools': {'messages': [ToolMessage(...)]}})
        if "tools" in event and "messages" in event["tools"]:
            for tool_message in event["tools"]["messages"]:
                if hasattr(tool_message, 'content') and tool_message.content:
                    try:
                        # Parse the tool result content
                        import json
                        tool_data = json.loads(tool_message.content)
                        logger.info(f"Parsed tool data: {type(tool_data)} - {tool_data}")
                        
                        # Handle product search results (list of products)
                        if isinstance(tool_data, list) and len(tool_data) > 0:
                            # Check if it's a list of products
                            if "product_id" in tool_data[0]:
                                from backend.domain.entities.product import Product
                                product_objects = [Product.model_validate(p) for p in tool_data]
                                # Create a proper ProductRecommendationMessage instead of storing in state
                                state.add_ai_message_with_products(product_objects)
                                logger.info(f"Added {len(product_objects)} products as recommendation message")
                            
                            # Check if it's a list of bundles
                            elif "bundle_id" in tool_data[0]:
                                from backend.domain.entities.product_bundle import ProductBundle
                                bundle_objects = [ProductBundle.model_validate(b) for b in tool_data]
                                # Create a proper ProductBundleRecommendationMessage instead of storing in state
                                state.add_ai_message_with_product_bundles(bundle_objects)
                                logger.info(f"Added {len(bundle_objects)} bundles as recommendation message")
                        
                        # Handle single bundle object (not in a list)
                        elif isinstance(tool_data, dict):
                            # Check if it's a single bundle
                            if "bundle_id" in tool_data:
                                from backend.domain.entities.product_bundle import ProductBundle
                                bundle_object = ProductBundle.model_validate(tool_data)
                                # Create a proper ProductBundleRecommendationMessage instead of storing in state
                                state.add_ai_message_with_product_bundles([bundle_object])
                                logger.info(f"Added 1 bundle as recommendation message")
                            
                            # Check if it's a single product
                            elif "product_id" in tool_data:
                                from backend.domain.entities.product import Product
                                product_object = Product.model_validate(tool_data)
                                # Create a proper ProductRecommendationMessage instead of storing in state
                                state.add_ai_message_with_products([product_object])
                                logger.info(f"Added 1 product as recommendation message")
                    
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.warning(f"Could not parse tool result: {e}")
                        continue
        
        # Check if this is a tool result that contains products or bundles
        elif "tool_result" in event:
            tool_result = event["tool_result"]
            if isinstance(tool_result, dict):
                # Handle product search results
                if "products" in tool_result and tool_result["products"]:
                    products = tool_result["products"]
                    if isinstance(products[0], dict):
                        from backend.domain.entities.product import Product
                        products = [Product(**p) for p in products]
                    # Create a proper ProductRecommendationMessage instead of storing in state
                    state.add_ai_message_with_products(products)
                    logger.info(f"Added {len(products)} products as recommendation message")
                
                # Handle product bundle results
                if "bundles" in tool_result and tool_result["bundles"]:
                    bundles = tool_result["bundles"]
                    if isinstance(bundles[0], dict):
                        from backend.domain.entities.product_bundle import ProductBundle
                        bundles = [ProductBundle(**b) for b in bundles]
                    # Create a proper ProductBundleRecommendationMessage instead of storing in state
                    state.add_ai_message_with_product_bundles(bundles)
                    logger.info(f"Added {len(bundles)} bundles as recommendation message")
                
                # Handle emit_recommendations tool result (return_direct=True)
                if "message" in tool_result:
                    # This is likely from emit_recommendations tool
                    state.add_message(tool_result["message"], is_human=False)
                    
                    # Update state with products and bundles from the tool result
                    if "products" in tool_result and tool_result["products"]:
                        products = tool_result["products"]
                        if isinstance(products[0], dict):
                            from backend.domain.entities.product import Product
                            products = [Product(**p) for p in products]
                        state.set_referenced_products(products)
                        logger.info(f"Set {len(products)} products from emit_recommendations in state")
                    
                    if "bundles" in tool_result and tool_result["bundles"]:
                        bundles = tool_result["bundles"]
                        if isinstance(bundles[0], dict):
                            from backend.domain.entities.product_bundle import ProductBundle
                            bundles = [ProductBundle(**b) for b in bundles]
                        state.set_product_bundles(bundles)
                        logger.info(f"Set {len(bundles)} product bundles from emit_recommendations in state")
        
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
                
                # Update state fields directly with products and bundles
                if "products" in final_response and final_response["products"]:
                    # Convert dict products to Product objects if needed
                    products = final_response["products"]
                    if isinstance(products[0], dict):
                        from backend.domain.entities.product import Product
                        products = [Product(**p) for p in products]
                    state.set_referenced_products(products)
                    logger.info(f"Set {len(products)} products in state")
                
                if "bundles" in final_response and final_response["bundles"]:
                    # Convert dict bundles to ProductBundle objects if needed
                    bundles = final_response["bundles"]
                    if isinstance(bundles[0], dict):
                        from backend.domain.entities.product_bundle import ProductBundle
                        bundles = [ProductBundle(**b) for b in bundles]
                    state.set_product_bundles(bundles)
                    logger.info(f"Set {len(bundles)} product bundles in state")
            
            
