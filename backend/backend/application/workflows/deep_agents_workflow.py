"""Deep Agents workflow for conversational commerce."""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from langchain_openai import ChatOpenAI
from langgraph.constants import END, START
from langgraph.graph.state import CompiledStateGraph, StateGraph

from backend.domain.entities.chat import ChatState, UserProfile
from backend.domain.entities.enhanced_chat import EnhancedChatState
from backend.application.interfaces import IChatWorkflow
from backend.application.services.hybrid_memory_service import HybridMemoryService
from backend.application.services.semantic_memory_service import SemanticMemoryService
from backend.application.services.product_service import ProductService
from backend.application.services.order_graph_service import OrderGraphService
from backend.application.services.memory_integration import MemoryIntegrationService
from backend.application.agents.simplified_deep_agent_v2 import SimplifiedConversationalCommerceAgentV2
from backend.infrastructure.factories import AgentFactory

logger = logging.getLogger("conversational_commerce.deep_agents_workflow")


class DeepAgentsWorkflow(IChatWorkflow[Union[ChatState, EnhancedChatState]]):
    """Deep Agents workflow for conversational commerce."""

    def __init__(
        self,
        llm: ChatOpenAI,
        memory_service: SemanticMemoryService,
        product_service: ProductService,
        order_graph_service: Optional[OrderGraphService] = None,
        agent_factory: Optional[AgentFactory] = None,
        **kwargs
    ):
        """Initialize the Deep Agents workflow.

        Args:
            llm: Language model instance
            memory_service: Memory service for user context
            product_service: Product service for recommendations
            order_graph_service: Order service for order management
            agent_factory: Agent factory for creating agents
            **kwargs: Additional arguments
        """
        # Initialize with agent factory for LangGraph compatibility
        if agent_factory:
            super().__init__(agent_factory)
        
        self.llm = llm
        self.memory_service = memory_service
        self.product_service = product_service
        self.order_graph_service = order_graph_service
        self.agent_factory = agent_factory
        
        # Store context for workflow nodes
        self._workflow_context = {}
        
        # Initialize memory integration service
        self.memory_integration = MemoryIntegrationService(
            semantic_memory_service=memory_service,
            background_memory_manager=kwargs.get('background_memory_manager')
        )
        
        # Initialize Simplified Deep Agent V2
        self.deep_agent = SimplifiedConversationalCommerceAgentV2(
            llm=llm,
            memory_service=memory_service,
            product_service=product_service,
            order_graph_service=order_graph_service
        )
        
        # Initialize the LangGraph workflow
        self.graph = self._build_graph()
        
        logger.info("Deep Agents workflow initialized")


    def _build_graph(self) -> CompiledStateGraph:
        """Build the Deep Agents workflow graph using LangGraph.
        
        This creates a graph-based workflow that integrates Deep Agent components
        with traditional workflow patterns for better orchestration and monitoring.
        
        Returns:
            Compiled LangGraph workflow
        """
        builder = StateGraph(Union[ChatState, EnhancedChatState])
        
        # Add Deep Agent nodes
        builder.add_node("deep_agent_planning", self._deep_agent_planning_node)
        builder.add_node("deep_agent_execution", self._deep_agent_execution_node)
        builder.add_node("deep_agent_memory", self._deep_agent_memory_node)
        builder.add_node("deep_agent_search_processing", self._deep_agent_search_processing_node)
        builder.add_node("deep_agent_response", self._deep_agent_response_node)
        
        # Add traditional workflow nodes for fallback
        if self.agent_factory:
            builder.add_node("greeting_detection", self._greeting_detection_node)
            builder.add_node("user_profile_extraction", self._user_profile_extraction_node)
            builder.add_node("product_reference", self._product_reference_node)
        
        # Define the workflow flow
        builder.add_edge(START, "deep_agent_planning")
        builder.add_edge("deep_agent_planning", "deep_agent_execution")
        builder.add_edge("deep_agent_execution", "deep_agent_memory")
        builder.add_edge("deep_agent_memory", "deep_agent_search_processing")
        builder.add_edge("deep_agent_search_processing", "deep_agent_response")
        builder.add_edge("deep_agent_response", END)
        
        # Add conditional edges for fallback scenarios
        if self.agent_factory:
            builder.add_conditional_edges(
                "deep_agent_planning",
                self._should_use_traditional_workflow,
                {
                    "use_deep_agents": "deep_agent_execution",
                    "use_traditional": "greeting_detection"
                }
            )
        
        return builder.compile()

    # LangGraph node implementations
    async def _deep_agent_planning_node(self, state: Union[ChatState, EnhancedChatState]) -> Union[ChatState, EnhancedChatState]:
        """Planning node for Deep Agent workflow."""
        try:
            logger.info("Deep Agent Planning: Analyzing user intent and context")
            
            # Extract user message
            user_message = self._extract_user_message(state)
            if not user_message:
                logger.warning("No user message found for planning")
                return state
            
            # Get user context for planning
            user_context = await self.memory_integration.get_user_context_for_deep_agent(
                user_id=state.user_id,
                query=user_message,
                include_conversation_history=True
            )
            
            # Store planning context in workflow instance
            self._workflow_context = {
                "user_message": user_message,
                "user_context": user_context,
                "planning_timestamp": datetime.now().isoformat()
            }
            
            logger.info("Deep Agent Planning completed")
            return state
            
        except Exception as e:
            logger.error(f"Error in deep agent planning: {e}")
            return state

    async def _deep_agent_execution_node(self, state: Union[ChatState, EnhancedChatState]) -> Union[ChatState, EnhancedChatState]:
        """Execution node for Deep Agent workflow."""
        try:
            logger.info("Deep Agent Execution: Processing with Deep Agent")
            
            # Get planning context from workflow instance
            context = self._workflow_context
            user_message = context.get('user_message', '')
            
            if not user_message:
                logger.warning("No user message found for execution")
                return state
            
            # Process with Deep Agent
            logger.info(f"🔍 DeepAgentsWorkflow: Calling deep_agent.process_message with user_message: {user_message[:50]}...")
            deep_agent_response = await self.deep_agent.process_message(
                user_message=user_message,
                user_id=state.user_id,
                context={},  # Add empty context
                session_id=getattr(state, 'session_id', None),
                conversation_history=state.messages
            )
            
            logger.info(f"🔍 DeepAgentsWorkflow: Deep agent response received:")
            logger.info(f"🔍 DeepAgentsWorkflow: - Response length: {len(deep_agent_response.response) if deep_agent_response.response else 0}")
            logger.info(f"🔍 DeepAgentsWorkflow: - Sub-agent used: {deep_agent_response.sub_agent_used}")
            logger.info(f"🔍 DeepAgentsWorkflow: - Confidence: {deep_agent_response.confidence}")
            
            # Store execution results in workflow context
            self._workflow_context['deep_agent_response'] = {
                "response": deep_agent_response.response,
                "sub_agent_used": deep_agent_response.sub_agent_used,
                "tools_used": deep_agent_response.tools_used,
                "confidence": deep_agent_response.confidence,
                "reasoning": deep_agent_response.reasoning,
                "execution_timestamp": datetime.now().isoformat()
            }
            
            # Handle search queries for product_expert (following original workflow pattern)
            if (deep_agent_response.sub_agent_used == "product_expert" and 
                hasattr(self.deep_agent, '_search_queries') and 
                self.deep_agent._search_queries):
                
                logger.info(f"🔍 DeepAgentsWorkflow: Processing {len(self.deep_agent._search_queries)} search queries")
                
                # Add search queries to state (following original workflow pattern)
                state.search_queries = self.deep_agent._search_queries
                
                # Clear the search queries from the agent
                self.deep_agent._search_queries = []
                
                logger.info(f"🔍 DeepAgentsWorkflow: Added {len(state.search_queries)} search queries to state")
            
            logger.info("🔍 DeepAgentsWorkflow: Deep Agent Execution completed")
            return state
            
        except Exception as e:
            logger.error(f"Error in deep agent execution: {e}")
            return state

    async def _deep_agent_search_processing_node(self, state: Union[ChatState, EnhancedChatState]) -> Union[ChatState, EnhancedChatState]:
        """Search processing node for Deep Agent workflow."""
        try:
            logger.info("🔍 DeepAgentsWorkflow: Processing search queries if any")
            
            # Check if there are search queries to process
            if hasattr(state, 'search_queries') and state.search_queries:
                logger.info(f"🔍 DeepAgentsWorkflow: Found {len(state.search_queries)} search queries to process")
                
                # Process each search query to get products
                all_products = []
                for i, search_query in enumerate(state.search_queries):
                    logger.info(f"🔍 DeepAgentsWorkflow: Processing search query {i+1}: '{search_query.query}' with categories: {search_query.categories}")
                    
                    try:
                        # Get products for this search query
                        products = await self.product_service.get_products_for_query(
                            search_query=search_query,
                            max_num_results=3
                        )
                        
                        if products:
                            logger.info(f"🔍 DeepAgentsWorkflow: Found {len(products)} products for query {i+1}")
                            all_products.extend(products)
                        else:
                            logger.info(f"🔍 DeepAgentsWorkflow: No products found for query {i+1}")
                            
                    except Exception as e:
                        logger.error(f"🔍 DeepAgentsWorkflow: Error processing search query {i+1}: {e}")
                
                # Store products in state for response
                if all_products:
                    logger.info(f"🔍 DeepAgentsWorkflow: Total products found: {len(all_products)}")
                    # Add products to state (this will be used by the response node)
                    state.recommended_products = all_products
                else:
                    logger.info("🔍 DeepAgentsWorkflow: No products found for any search queries")
            else:
                logger.info("🔍 DeepAgentsWorkflow: No search queries to process")
            
            logger.info("🔍 DeepAgentsWorkflow: Search processing completed")
            return state
            
        except Exception as e:
            logger.error(f"Error in deep agent search processing: {e}")
            return state

    async def _deep_agent_memory_node(self, state: Union[ChatState, EnhancedChatState]) -> Union[ChatState, EnhancedChatState]:
        """Memory node for Deep Agent workflow."""
        try:
            logger.info("Deep Agent Memory: Storing interaction and updating memory")
            
            # Get execution results
            response_data = getattr(state, 'deep_agent_response', {})
            
            if response_data:
                # Store the interaction as memory
                await self.memory_integration.store_deep_agent_interaction(
                    user_id=state.user_id,
                    interaction_data={
                        "content": response_data.get('response', ''),
                        "sub_agent_used": response_data.get('sub_agent_used'),
                        "tools_used": response_data.get('tools_used'),
                        "confidence": response_data.get('confidence'),
                        "reasoning": response_data.get('reasoning')
                    }
                )
                
                logger.info("Deep Agent Memory: Interaction stored successfully")
            else:
                logger.warning("No response data found for memory storage")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in deep agent memory: {e}")
            return state

    async def _deep_agent_response_node(self, state: Union[ChatState, EnhancedChatState]) -> Union[ChatState, EnhancedChatState]:
        """Response node for Deep Agent workflow."""
        try:
            logger.info("🔍 DeepAgentsWorkflow: Deep Agent Response: Finalizing response")
            
            # Get execution results from workflow context
            response_data = self._workflow_context.get('deep_agent_response', {})
            logger.info(f"🔍 DeepAgentsWorkflow: Response data keys: {list(response_data.keys()) if response_data else 'None'}")
            
            response_content = response_data.get('response', '')
            logger.info(f"🔍 DeepAgentsWorkflow: Response content length: {len(response_content) if response_content else 0}")
            logger.info(f"🔍 DeepAgentsWorkflow: Response content preview: {response_content[:100] if response_content else 'None'}")
            
            if response_content:
                # Add the response to the state
                state.add_message(response_content, is_human=False)
                logger.info("🔍 DeepAgentsWorkflow: Response added to state successfully")
            else:
                logger.warning("🔍 DeepAgentsWorkflow: No response content found - this will cause frontend issues")
                # Add a fallback response
                fallback_response = "I'm sorry, I didn't receive a proper response. Please try again."
                state.add_message(fallback_response, is_human=False)
                logger.info("🔍 DeepAgentsWorkflow: Added fallback response")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in deep agent response: {e}")
            return state

    def _should_use_traditional_workflow(self, state: Union[ChatState, EnhancedChatState]) -> str:
        """Determine if we should use traditional workflow as fallback."""
        try:
            # Check if Deep Agent is available and working
            if hasattr(self, 'deep_agent') and self.deep_agent:
                return "use_deep_agents"
            else:
                logger.warning("Deep Agent not available, using traditional workflow")
                return "use_traditional"
        except Exception as e:
            logger.error(f"Error determining workflow type: {e}")
            return "use_traditional"

    # Traditional workflow fallback nodes
    async def _greeting_detection_node(self, state: Union[ChatState, EnhancedChatState]) -> Union[ChatState, EnhancedChatState]:
        """Greeting detection node for fallback."""
        if self.agent_factory:
            agent = self.agent_factory.create_agent("GREETING_DETECTION")
            return await agent.process(state)
        return state

    async def _user_profile_extraction_node(self, state: Union[ChatState, EnhancedChatState]) -> Union[ChatState, EnhancedChatState]:
        """User profile extraction node for fallback."""
        if self.agent_factory:
            agent = self.agent_factory.create_agent("USER_PROFILE_EXTRACTION")
            return await agent.process(state)
        return state

    async def _product_reference_node(self, state: Union[ChatState, EnhancedChatState]) -> Union[ChatState, EnhancedChatState]:
        """Product reference node for fallback."""
        if self.agent_factory:
            agent = self.agent_factory.create_agent("PRODUCT_REFERENCE")
            return await agent.process(state)
        return state

    async def run(self, state: Union[ChatState, EnhancedChatState]) -> Union[ChatState, EnhancedChatState]:
        """Process a chat query using Deep Agents architecture.

        Args:
            state: The current chat state

        Returns:
            Updated chat state with Deep Agent response
        """
        try:
            logger.info(f"Processing Deep Agents LangGraph workflow for user {state.user_id}")
            
            # Use the compiled LangGraph workflow
            result_state = await self.graph.ainvoke(state)
            
            logger.info(f"Deep Agents LangGraph workflow completed for user {state.user_id}")
            return result_state
            
        except Exception as e:
            logger.error(f"Error in Deep Agents LangGraph workflow: {e}")
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

    async def _update_user_profile_from_interaction(
        self,
        state: Union[ChatState, EnhancedChatState],
        deep_agent_response,
        user_context: Dict[str, Any]
    ) -> None:
        """Update user profile based on Deep Agent interaction.

        Args:
            state: The chat state
            deep_agent_response: The Deep Agent response
            user_context: User context information
        """
        try:
            logger.info(f"Updating user profile from Deep Agent interaction for user {state.user_id}")
            
            # Extract profile updates from the interaction
            profile_updates = self._extract_profile_updates(
                deep_agent_response, user_context
            )
            
            if profile_updates:
                await self.memory_integration.update_user_profile_with_memory(
                    user_id=state.user_id,
                    profile_updates=profile_updates
                )
                
                logger.info(f"Updated user profile for user {state.user_id}")
            
        except Exception as e:
            logger.error(f"Error updating user profile from interaction: {e}")

    def _extract_profile_updates(
        self,
        deep_agent_response,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract profile updates from Deep Agent response.

        Args:
            deep_agent_response: The Deep Agent response
            user_context: User context information

        Returns:
            Dictionary with profile updates
        """
        try:
            profile_updates = {}
            
            # Extract updates based on sub-agent used
            if deep_agent_response.sub_agent_used == "product_expert":
                # Extract product preferences
                if "product" in deep_agent_response.response.lower():
                    profile_updates["product_preferences"] = ["recent_product_inquiry"]
            
            elif deep_agent_response.sub_agent_used == "health_advisor":
                # Extract health information
                if "health" in deep_agent_response.response.lower():
                    profile_updates["health_conditions"] = ["health_inquiry_made"]
            
            elif deep_agent_response.sub_agent_used == "order_specialist":
                # Extract order information
                if "order" in deep_agent_response.response.lower():
                    profile_updates["order_history"] = ["order_inquiry_made"]
            
            return profile_updates
            
        except Exception as e:
            logger.error(f"Error extracting profile updates: {e}")
            return {}

    async def get_workflow_metrics(self, state: Union[ChatState, EnhancedChatState]) -> Dict[str, Any]:
        """Get workflow metrics for monitoring.

        Args:
            state: The chat state

        Returns:
            Dictionary with workflow metrics
        """
        try:
            metrics = {
                "workflow_type": "deep_agents",
                "user_id": state.user_id,
                "message_count": len(state.messages),
                "has_user_profile": hasattr(state, 'user_profile') and state.user_profile is not None,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add Deep Agent specific metrics if available
            if hasattr(state, 'deep_agent_metrics'):
                metrics.update(state.deep_agent_metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting workflow metrics: {e}")
            return {
                "workflow_type": "deep_agents",
                "user_id": state.user_id,
                "error": str(e)
            }

    async def optimize_for_user(
        self,
        user_id: str,
        optimization_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize workflow for a specific user.

        Args:
            user_id: The user's ID
            optimization_data: Data for optimization

        Returns:
            Dictionary with optimization results
        """
        try:
            logger.info(f"Optimizing Deep Agents workflow for user {user_id}")
            
            # Get user memory statistics
            memory_stats = await self.memory_integration.get_memory_statistics_for_user(user_id)
            
            # Consolidate memories if needed
            if memory_stats.get("total_memories", 0) > 10:
                await self.memory_integration.consolidate_memories_for_deep_agent(
                    user_id=user_id,
                    force_consolidation=False
                )
            
            optimization_result = {
                "user_id": user_id,
                "memory_stats": memory_stats,
                "optimization_applied": True,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Optimized Deep Agents workflow for user {user_id}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Error optimizing workflow for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "optimization_applied": False,
                "error": str(e)
            }
