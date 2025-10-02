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
    
    async def run(self, state: ChatState, session_id: str = None) -> ChatState:
        """Run the deep agent workflow on the chat state."""
        import time
        start_time = time.time()
        
        try:
            logger.info("🚀 Starting deep agent workflow")
            logger.info(f"🚀 Session ID received: {session_id}")
            logger.info(f"🚀 Session ID type: {type(session_id)}")
            
            # Send initial progress message if session_id is available
            if session_id:
                try:
                    from backend.presentation.api.websocket.connection_manager import manager
                    logger.info(f"🚀 Sending initial progress update to session {session_id}")
                    await manager.send_thinking_update(session_id, "🤖 Analyzing your request...")
                    logger.info(f"🚀 Initial progress update sent successfully")
                except Exception as e:
                    logger.warning(f"Failed to send initial progress update: {e}")
            else:
                logger.warning("🚀 No session_id provided, skipping progress updates")
            
            # Convert chat state to agent format
            messages = []
            for msg in state.messages:
                if msg.get('type') == 'human':
                    messages.append({"role": "user", "content": msg.get('content', '')})
                elif msg.get('type') == 'ai':
                    messages.append({"role": "assistant", "content": msg.get('content', '')})
            
                # Create thread configuration with timestamp to ensure uniqueness
                import time
                thread_cfg = {"configurable": {"thread_id": f"user_{state.user_id}_{int(time.time())}"}}
            
            # Run the agent
            logger.info(f"🚀 Running deep agent with {len(messages)} messages")
            agent_start_time = time.time()
            
            # Send progress update if session_id is available
            if session_id:
                try:
                    logger.info(f"🚀 Sending search progress update to session {session_id}")
                    await manager.send_thinking_update(session_id, "🔍 Searching for products...")
                    logger.info(f"🚀 Search progress update sent successfully")
                except Exception as e:
                    logger.warning(f"Failed to send search progress update: {e}")
            
            # Stream the agent response and process events in real-time
            event_count = 0
            async for event in self.agent.astream({"messages": messages}, config=thread_cfg):
                event_count += 1
                event_time = time.time()
                logger.info(f"🚀 Deep agent stream event #{event_count} at {event_time - start_time:.2f}s: {event}")
                
                # Handle different event types based on logs analysis
                event_type = self._get_event_type(event)
                logger.info(f"🚀 Event type: {event_type}")
                
                # Send thinking updates immediately when tools are called
                if session_id and event_type == "model_request":
                    # Check if this is a tool call request
                    if "tool_calls" in str(event):
                        try:
                            # Extract tool calls from the event
                            if hasattr(event, 'get') and event.get('model_request'):
                                model_request = event['model_request']
                                if hasattr(model_request, 'get') and model_request.get('messages'):
                                    for message in model_request['messages']:
                                        if hasattr(message, 'tool_calls') and message.tool_calls:
                                            for tool_call in message.tool_calls:
                                                tool_name = tool_call.get('name', 'unknown')
                                                logger.info(f"🚀 Tool call detected: {tool_name}")
                                                if tool_name == 'product_search_for_query':
                                                    logger.info(f"🚀 Sending search progress update to session {session_id}")
                                                    await manager.send_thinking_update(session_id, "🔍 Searching for products...")
                                                elif tool_name == 'intelligent_product_bundles':
                                                    logger.info(f"🚀 Sending bundle creation update to session {session_id}")
                                                    await manager.send_thinking_update(session_id, "📦 Creating intelligent bundles...")
                                                elif tool_name == 'emit_recommendations':
                                                    logger.info(f"🚀 Sending finalization update to session {session_id}")
                                                    await manager.send_thinking_update(session_id, "✍️ Generating recommendations...")
                        except Exception as e:
                            logger.warning(f"Failed to send tool call progress update: {e}")
                
                # Process the event
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
                elif event_type == "tool":
                    # Handle direct tool events
                    self._handle_tool_event(event, state)
                else:
                    logger.info(f"🚀 Unhandled event type: {event_type}")
            
            agent_end_time = time.time()
            logger.info(f"🚀 Agent processing completed in {agent_end_time - agent_start_time:.2f}s")
            logger.info("🚀 Deep agent workflow completed successfully")
            
            # Send completion message if session_id is available
            if session_id:
                try:
                    logger.info(f"🚀 Sending completion update to session {session_id}")
                    await manager.send_thinking_update(session_id, "✅ Recommendations ready!")
                    logger.info(f"🚀 Completion update sent successfully")
                except Exception as e:
                    logger.warning(f"Failed to send completion update: {e}")
            
            # Ensure we have a final message if none was generated
            if not state.messages or not any(msg.get('type') == 'ai' for msg in state.messages[-3:]):
                # Generate a final message if no AI message was created
                if state.product_bundles:
                    final_message = "I've curated these intelligent product bundles for you based on your needs. Each bundle is designed to provide comprehensive support for your wellness goals."
                    state.add_message(final_message, is_human=False)
                    logger.info("Added fallback final message to state")
                elif state.referenced_products:
                    final_message = "Here are some product recommendations that align with your needs and preferences."
                    state.add_message(final_message, is_human=False)
                    logger.info("Added fallback final message to state")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in deep agent workflow: {e}", exc_info=True)
            
            # Check if it's a tool call completion error
            if "tool_call_id" in str(e) and "must be followed by tool messages" in str(e):
                logger.warning("Detected incomplete tool call error, clearing conversation and retrying")
                # Clear the conversation and retry with just the current message
                current_message = state.messages[-1] if state.messages else None
                if current_message:
                    state.messages = [current_message] # Reset messages to only the current one
                    # Use a completely fresh thread ID
                    import time
                    fresh_thread_cfg = {"configurable": {"thread_id": f"fresh_{state.user_id}_{int(time.time())}"}}
                    logger.info(f"Retrying agent with fresh thread: {fresh_thread_cfg}")
                    try:
                        async for event in self.agent.astream({"messages": messages}, config=fresh_thread_cfg):
                            logger.info(f"Deep agent retry stream event: {event}")
                            event_type = self._get_event_type(event)
                            if event_type == "model_request":
                                self._handle_model_request(event, state)
                            elif event_type == "tool_call":
                                self._handle_tool_call(event, state)
                            elif event_type == "tool_result":
                                self._handle_tool_result(event, state)
                            elif event_type == "middleware":
                                self._handle_middleware_event(event, state)
                            elif event_type == "messages":
                                self._handle_messages_event(event, state)
                            elif event_type == "response":
                                self._handle_response_event(event, state)
                            elif event_type == "tool":
                                self._handle_tool_event(event, state)
                            else:
                                logger.info(f"Unhandled event type in retry: {event_type}")
                        return state
                    except Exception as retry_e:
                        logger.error(f"Error during agent retry: {retry_e}", exc_info=True)
                        state.add_message(
                            "I'm sorry, I encountered an error even after retrying. Please try again.",
                            is_human=False
                        )
                        return state
            
            # Add error message to state for unhandled exceptions
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
        elif "tool" in event:
            return "tool"
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
    
    def _handle_tool_event(self, event: dict, state: ChatState):
        """Handle direct tool events."""
        logger.info(f"Tool event: {event}")
        # This handles direct tool events that might not be captured by other handlers
        # For now, just log the event
    
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
            
            
