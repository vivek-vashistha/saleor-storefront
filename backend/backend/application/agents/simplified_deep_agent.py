"""Simplified Deep Agent implementation using the Deep Agents framework."""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from backend.domain.entities.chat import ChatState, UserProfile
from backend.domain.entities.enhanced_chat import EnhancedChatState
from backend.application.services.hybrid_memory_service import HybridMemoryService
from backend.application.services.product_service import ProductService
from backend.application.services.order_graph_service import OrderGraphService
from backend.application.interfaces.deep_agent import IDeepAgent, DeepAgentResponse

# Note: This file is kept for reference but uses the external deepagents framework
# The actual implementation uses simplified_deep_agent_v2.py which doesn't require external dependencies
# from backend.infrastructure.deepagents.graph import create_deep_agent

logger = logging.getLogger("conversational_commerce.simplified_deep_agent")


class SimplifiedConversationalCommerceAgent(IDeepAgent):
    """Simplified Deep Agent using the Deep Agents framework.
    
    This implementation follows the research_agent.py pattern:
    - Simple sub-agent definitions
    - Framework handles agent selection and coordination
    - No manual rule-based routing
    - Leverages Deep Agents middleware for planning and execution
    """

    def __init__(
        self,
        llm: ChatOpenAI,
        memory_service: HybridMemoryService,
        product_service: ProductService,
        order_graph_service: Optional[OrderGraphService] = None,
        **kwargs
    ):
        """Initialize the Simplified Deep Agent.

        Args:
            llm: Language model instance
            memory_service: Memory service for user context
            product_service: Product service for recommendations
            order_graph_service: Order service for order management
            **kwargs: Additional arguments
        """
        self.llm = llm
        self.memory_service = memory_service
        self.product_service = product_service
        self.order_graph_service = order_graph_service
        
        # Create the Deep Agent using the framework
        self.agent = self._create_deep_agent()
        
        logger.info("Simplified Deep Agent initialized")

    def _create_deep_agent(self):
        """Create the Deep Agent using the framework."""
        # Note: This requires the external deepagents framework
        # For now, this is commented out to prevent import errors
        # Use simplified_deep_agent_v2.py instead
        raise NotImplementedError("This requires the external deepagents framework. Use SimplifiedConversationalCommerceAgentV2 instead.")
        # return create_deep_agent(
        #     tools=self._get_all_tools(),
        #     instructions=self._get_main_system_prompt(),
        #     subagents=self._get_sub_agents()
        # )

    def _get_main_system_prompt(self) -> str:
        """Get the main system prompt for the Deep Agent."""
        return """
        You are a sophisticated conversational commerce assistant for a health & wellness store.

        CORE CAPABILITIES:
        - Product discovery and recommendations
        - Order status and tracking
        - Refunds and returns
        - Health and wellness advice
        - Memory and personalization

        PLANNING APPROACH:
        1. Analyze the user's intent and context
        2. Retrieve relevant user memories
        3. Determine which sub-agents and tools are needed
        4. Create a plan for the conversation
        5. Execute the plan with appropriate sub-agents
        6. Synthesize results into a coherent response

        MEMORY INTEGRATION:
        - ALWAYS retrieve relevant memories before responding
        - Use memories to personalize all interactions
        - Store new information as appropriate memories
        - Update user profiles with new insights
        - Reference past interactions naturally

        SUB-AGENT COORDINATION:
        - Use product_expert for product recommendations and discovery
        - Use order_specialist for order status, tracking, and returns
        - Use health_advisor for health and wellness guidance
        - Use memory_manager for user personalization and memory operations

        RESPONSE FORMAT:
        Always provide helpful, personalized responses that leverage user context and memories.
        Be conversational and natural while being informative and accurate.
        """

    def _get_sub_agents(self) -> List[Dict[str, Any]]:
        """Define sub-agents following the research_agent.py pattern."""
        return [
            {
                "name": "product_expert",
                "description": "Expert in product recommendations, supplements, vitamins, and health products. Use for product discovery, recommendations, and product-related questions.",
                "prompt": """You are a product expert for a health & wellness store. Your job is to help customers find the right products.

                CORE RESPONSIBILITIES:
                - Recommend products based on customer needs
                - Explain product benefits and ingredients
                - Compare similar products
                - Suggest product bundles or alternatives
                - Provide detailed product information

                MEMORY INTEGRATION:
                - Use customer's purchase history and preferences
                - Reference past product interactions
                - Store new product preferences
                - Personalize recommendations based on health goals

                Always provide helpful, accurate product information and personalized recommendations.""",
                "tools": [
                    self._create_search_products_tool(),
                    self._create_get_product_details_tool(),
                    self._create_create_bundles_tool()
                ]
            },
            {
                "name": "order_specialist",
                "description": "Specialist in order management, tracking, returns, and refunds. Use for order status, shipping, returns, and order-related questions.",
                "prompt": """You are an order specialist for a health & wellness store. Your job is to help customers with order-related inquiries.

                CORE RESPONSIBILITIES:
                - Check order status and tracking
                - Process returns and refunds
                - Handle shipping inquiries
                - Resolve order issues
                - Provide order history information

                MEMORY INTEGRATION:
                - Reference customer's order history
                - Track order preferences and patterns
                - Store order-related interactions
                - Personalize order management

                Always provide accurate order information and helpful assistance with order-related matters.""",
                "tools": [
                    self._create_check_order_status_tool(),
                    self._create_track_shipment_tool(),
                    self._create_process_refund_tool()
                ]
            },
            {
                "name": "health_advisor",
                "description": "Health and wellness advisor for safety, interactions, dosage, and health guidance. Use for health-related questions and safety concerns.",
                "prompt": """You are a health advisor for a health & wellness store. Your job is to provide health and wellness guidance.

                CORE RESPONSIBILITIES:
                - Provide health and wellness advice
                - Check for drug interactions
                - Recommend appropriate dosages
                - Suggest health-focused products
                - Provide safety information

                MEMORY INTEGRATION:
                - Reference customer's health history and conditions
                - Track health goals and preferences
                - Store health-related interactions
                - Personalize health recommendations

                Always prioritize customer safety and provide accurate health information.""",
                "tools": [
                    self._create_get_health_advice_tool(),
                    self._create_check_interactions_tool()
                ]
            },
            {
                "name": "memory_manager",
                "description": "Manages user personalization, preferences, and memory operations. Use for updating user profiles and managing personalization.",
                "prompt": """You are a memory manager for a health & wellness store. Your job is to manage user personalization and memory.

                CORE RESPONSIBILITIES:
                - Update user profiles and preferences
                - Store and retrieve user memories
                - Manage personalization data
                - Track user interactions and patterns
                - Provide personalized context

                MEMORY INTEGRATION:
                - Store new user information and preferences
                - Retrieve relevant user context
                - Update user profiles with new insights
                - Manage memory consolidation and organization

                Always respect user privacy and provide personalized experiences.""",
                "tools": [
                    self._create_retrieve_memories_tool(),
                    self._create_store_memory_tool(),
                    self._create_update_profile_tool()
                ]
            }
        ]

    def _get_all_tools(self) -> List[Any]:
        """Get all available tools for the main agent."""
        return [
            self._create_search_products_tool(),
            self._create_get_product_details_tool(),
            self._create_create_bundles_tool(),
            self._create_check_order_status_tool(),
            self._create_track_shipment_tool(),
            self._create_process_refund_tool(),
            self._create_get_health_advice_tool(),
            self._create_check_interactions_tool(),
            self._create_retrieve_memories_tool(),
            self._create_store_memory_tool(),
            self._create_update_profile_tool()
        ]

    # Tool creation methods (simplified)
    def _create_search_products_tool(self):
        """Create product search tool."""
        def search_products(query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
            """Search for products based on query and filters."""
            # Implementation would call product_service
            return []
        return search_products

    def _create_get_product_details_tool(self):
        """Create product details tool."""
        def get_product_details(product_id: str) -> Dict[str, Any]:
            """Get detailed information about a product."""
            # Implementation would call product_service
            return {}
        return get_product_details

    def _create_create_bundles_tool(self):
        """Create product bundles tool."""
        def create_bundles(products: List[str], bundle_type: str = "health_focus") -> List[Dict[str, Any]]:
            """Create product bundles based on products and type."""
            # Implementation would call product_service
            return []
        return create_bundles

    def _create_check_order_status_tool(self):
        """Create order status tool."""
        def check_order_status(order_id: str) -> Dict[str, Any]:
            """Check the status of an order."""
            # Implementation would call order_graph_service
            return {}
        return check_order_status

    def _create_track_shipment_tool(self):
        """Create shipment tracking tool."""
        def track_shipment(tracking_number: str) -> Dict[str, Any]:
            """Track a shipment."""
            # Implementation would call order_graph_service
            return {}
        return track_shipment

    def _create_process_refund_tool(self):
        """Create refund processing tool."""
        def process_refund(order_id: str, reason: str) -> Dict[str, Any]:
            """Process a refund for an order."""
            # Implementation would call order_graph_service
            return {}
        return process_refund

    def _create_get_health_advice_tool(self):
        """Create health advice tool."""
        def get_health_advice(health_condition: str, current_medications: List[str] = None) -> Dict[str, Any]:
            """Get health advice for a specific condition."""
            # Implementation would call health service
            return {}
        return get_health_advice

    def _create_check_interactions_tool(self):
        """Create drug interaction checker tool."""
        def check_interactions(medications: List[str], supplements: List[str] = None) -> Dict[str, Any]:
            """Check for drug interactions."""
            # Implementation would call health service
            return {}
        return check_interactions

    def _create_retrieve_memories_tool(self):
        """Create memory retrieval tool."""
        def retrieve_memories(user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
            """Retrieve relevant memories for a user."""
            # Implementation would call memory_service
            return []
        return retrieve_memories

    def _create_store_memory_tool(self):
        """Create memory storage tool."""
        def store_memory(user_id: str, content: str, memory_type: str, metadata: Dict[str, Any] = None) -> bool:
            """Store a new memory for a user."""
            # Implementation would call memory_service
            return True
        return store_memory

    def _create_update_profile_tool(self):
        """Create profile update tool."""
        def update_profile(user_id: str, profile_updates: Dict[str, Any]) -> bool:
            """Update user profile with new information."""
            # Implementation would call memory_service
            return True
        return update_profile

    async def process_message(
        self,
        user_message: str,
        user_id: str,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> DeepAgentResponse:
        """Process a user message using the Deep Agent framework.

        Args:
            user_message: The user's message
            user_id: The user's ID
            session_id: Optional session ID
            conversation_history: Optional conversation history

        Returns:
            DeepAgentResponse with the processed result
        """
        try:
            logger.info(f"Processing message for user {user_id}: {user_message[:100]}...")
            
            # Use the Deep Agent framework to process the message
            # The framework handles:
            # - Intent detection
            # - Sub-agent selection
            # - Tool coordination
            # - Memory integration
            # - Response synthesis
            
            response = await self.agent.ainvoke({
                "messages": [HumanMessage(content=user_message)],
                "user_id": user_id,
                "session_id": session_id,
                "conversation_history": conversation_history or []
            })
            
            # Extract response content
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            logger.info(f"Deep Agent processing completed for user {user_id}")
            return DeepAgentResponse(
                response=response_text,
                sub_agent_used="framework_managed",  # Framework handles this
                tools_used=["framework_tools"],  # Framework manages this
                memories_retrieved=0,  # Framework handles this
                confidence=0.9,  # High confidence with framework
                reasoning="Processed by Deep Agent framework with automatic sub-agent selection"
            )
            
        except Exception as e:
            logger.error(f"Error in Deep Agent processing: {e}")
            return DeepAgentResponse(
                response="I'm sorry, I encountered an error processing your request. Please try again.",
                sub_agent_used=None,
                tools_used=[],
                memories_retrieved=0,
                confidence=0.0,
                reasoning="Error occurred during processing"
            )

    async def process_chat_state(self, state: Union[ChatState, EnhancedChatState]) -> Union[ChatState, EnhancedChatState]:
        """Process a chat state using the Deep Agent framework.

        Args:
            state: The chat state to process

        Returns:
            Updated chat state
        """
        try:
            # Extract user message from state
            user_message = ""
            for msg in reversed(state.messages):
                if msg.get('type') == 'human':
                    content = msg.get('content', '')
                    if isinstance(content, list):
                        content = ' '.join(str(item) for item in content)
                    user_message = str(content)
                    break
            
            if not user_message:
                logger.warning("No user message found in state")
                return state
            
            # Process with Deep Agent
            result = await self.process_message(
                user_message=user_message,
                user_id=state.user_id,
                session_id=getattr(state, 'session_id', None),
                conversation_history=state.messages
            )
            
            # Add the response to the state
            state.add_message(result.response, is_human=False)
            
            logger.info(f"Deep Agent processed chat state for user {state.user_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error processing chat state with Deep Agent: {e}")
            # Fallback response
            state.add_message(
                "I'm sorry, I encountered an error processing your request. Please try again.",
                is_human=False
            )
            return state
