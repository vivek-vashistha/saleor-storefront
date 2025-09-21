import logging
from typing import Any, Dict

from langgraph.constants import END, START
from langgraph.graph.state import CompiledStateGraph, StateGraph
from langchain_openai import ChatOpenAI

from backend.domain.entities.enhanced_chat import EnhancedChatState, MemoryComponents
from backend.domain.enums import AgentType
from backend.application.interfaces import IChatWorkflow
from backend.infrastructure.agents.enhanced_user_profile_extraction_agent import EnhancedUserProfileExtractionAgent
from backend.application.services.semantic_memory_service import SemanticMemoryService, SemanticMemoryConfig
from backend.application.services.background_memory_manager import BackgroundMemoryManager

logger = logging.getLogger("conversational_commerce.enhanced_workflow")


class EnhancedSearchQueryWorkflow(IChatWorkflow[EnhancedChatState]):
    """Enhanced workflow with Langmem integration for long-term memory."""

    def __init__(
        self,
        llm: ChatOpenAI,
        semantic_memory_service: SemanticMemoryService,
        background_memory_manager: BackgroundMemoryManager,
        agent_factory=None,
        **kwargs
    ):
        """Initialize the enhanced workflow.

        Args:
            llm: The language model to use
            semantic_memory_service: Service for semantic memory operations
            background_memory_manager: Manager for background memory processing
            agent_factory: Factory for creating agents (optional, for fallback)
            **kwargs: Additional arguments for other agents
        """
        # Call parent constructor if agent_factory is provided
        if agent_factory:
            super().__init__(agent_factory)
        
        self.llm = llm
        self.semantic_memory_service = semantic_memory_service
        self.background_memory_manager = background_memory_manager
        self.agent_factory = agent_factory
        
        # Initialize enhanced agents
        self.enhanced_user_profile_extraction_agent = EnhancedUserProfileExtractionAgent(
            llm=llm,
            semantic_memory_service=semantic_memory_service
        )
        
        # Initialize other agents using the factory if available
        if agent_factory:
            self.agents = {
                AgentType.SEARCH_QUERY: agent_factory.create_agent(AgentType.SEARCH_QUERY),
                AgentType.SUFFICIENT_DETAIL: agent_factory.create_agent(AgentType.SUFFICIENT_DETAIL),
                AgentType.CONVERSATION_ENRICHMENT: agent_factory.create_agent(AgentType.CONVERSATION_ENRICHMENT),
                AgentType.CONVERSATION_SATURATION: agent_factory.create_agent(AgentType.CONVERSATION_SATURATION),
                AgentType.GREETING_DETECTION: agent_factory.create_agent(AgentType.GREETING_DETECTION),
                AgentType.PRODUCT_REFERENCE: agent_factory.create_agent(AgentType.PRODUCT_REFERENCE),
            }
        else:
            # If no agent_factory, initialize empty agents dict
            self.agents = {}
        
        self.graph = self._build_graph()

    def _convert_to_regular_chat_state(self, state: EnhancedChatState):
        """Convert EnhancedChatState to regular ChatState for agent processing.
        
        Args:
            state: The enhanced chat state
            
        Returns:
            Regular ChatState for agent processing
        """
        from backend.domain.entities.chat import ChatState, UserProfile
        
        return ChatState(
            messages=state.messages,
            search_queries=state.search_queries,
            next_agent=state.next_agent,
            weather_info=state.weather_info,
            is_detail_sufficient=state.is_detail_sufficient,
            is_conversation_saturated=state.is_conversation_saturated,
            is_greeting=state.is_greeting,
            user_id=state.user_id,
            referenced_products=state.referenced_products,
            user_profile=UserProfile(
                name=state.user_profile.name,
                email=state.user_profile.email,
                age=state.user_profile.age,
                location=state.user_profile.location,
                health_conditions=state.user_profile.health_conditions,
                dietary_restrictions=state.user_profile.dietary_restrictions,
                medications=state.user_profile.medications,
                activity_preferences=state.user_profile.activity_preferences,
                product_preferences=state.user_profile.product_preferences,
                budget_range=state.user_profile.budget_range,
                fitness_goals=state.user_profile.fitness_goals,
                adventure_plans=state.user_profile.adventure_plans,
                experience_level=state.user_profile.experience_level,
                frequency_of_use=state.user_profile.frequency_of_use,
                physical_limitations=state.user_profile.physical_limitations,
                time_constraints=state.user_profile.time_constraints,
                group_size=state.user_profile.group_size,
                family_considerations=state.user_profile.family_considerations,
                climate_conditions=state.user_profile.climate_conditions,
                storage_limitations=state.user_profile.storage_limitations,
                last_updated=state.user_profile.last_updated
            )
        )

    def _update_enhanced_state_from_regular(self, enhanced_state: EnhancedChatState, regular_state) -> None:
        """Update enhanced state with results from regular state processing.
        
        Args:
            enhanced_state: The enhanced chat state to update
            regular_state: The regular chat state with results
        """
        enhanced_state.messages = regular_state.messages
        enhanced_state.search_queries = regular_state.search_queries
        enhanced_state.next_agent = regular_state.next_agent
        enhanced_state.is_detail_sufficient = regular_state.is_detail_sufficient
        enhanced_state.is_conversation_saturated = regular_state.is_conversation_saturated
        enhanced_state.is_greeting = regular_state.is_greeting
        enhanced_state.referenced_products = regular_state.referenced_products

    async def _call_agent_with_fallback(self, state: EnhancedChatState, agent_type: AgentType) -> EnhancedChatState:
        """Call an agent with fallback handling.
        
        Args:
            state: The enhanced chat state
            agent_type: The type of agent to call
            
        Returns:
            The updated enhanced chat state
        """
        try:
            logger.info(f"[ENHANCED_WORKFLOW] Starting {agent_type.value} for user {state.user_id}")
            
            # Convert to regular ChatState for agent processing
            regular_state = self._convert_to_regular_chat_state(state)
            
            # Call the agent if available
            if agent_type in self.agents:
                agent = self.agents[agent_type]
                regular_state = await agent.process(regular_state)
                
                # Update the enhanced state with results
                self._update_enhanced_state_from_regular(state, regular_state)
                
                # Add debug logging for specific agents
                if agent_type == AgentType.SUFFICIENT_DETAIL:
                    logger.info(f"[ENHANCED_WORKFLOW] SUFFICIENT_DETAIL result: is_detail_sufficient={state.is_detail_sufficient}")
                elif agent_type == AgentType.CONVERSATION_SATURATION:
                    logger.info(f"[ENHANCED_WORKFLOW] CONVERSATION_SATURATION result: is_conversation_saturated={state.is_conversation_saturated}")
                elif agent_type == AgentType.SEARCH_QUERY:
                    logger.info(f"[ENHANCED_WORKFLOW] SEARCH_QUERY result: search_queries_count={len(state.search_queries)}")
            else:
                logger.warning(f"[ENHANCED_WORKFLOW] {agent_type.value} agent not available, skipping")
            
            logger.info(f"[ENHANCED_WORKFLOW] {agent_type.value} completed for user {state.user_id}")
            return state
            
        except Exception as e:
            logger.error(f"[ENHANCED_WORKFLOW] Error in {agent_type.value} agent: {e}")
            return state

    def _build_graph(self) -> CompiledStateGraph:
        """Build the enhanced workflow graph with Langmem integration.

        Returns:
            The compiled workflow graph
        """
        builder = StateGraph(EnhancedChatState)

        # Add all agent nodes (using enhanced versions where available)
        builder.add_node(AgentType.SUFFICIENT_DETAIL, self.call_sufficient_detail_agent)
        builder.add_node(AgentType.CONVERSATION_ENRICHMENT, self.call_conversation_enrichment_agent)
        builder.add_node(AgentType.CONVERSATION_SATURATION, self.call_conversation_saturation_agent)
        builder.add_node(AgentType.SEARCH_QUERY, self.call_search_agent)
        builder.add_node(AgentType.GREETING_DETECTION, self.call_greeting_detection_agent)
        builder.add_node(AgentType.PRODUCT_REFERENCE, self.call_product_reference_agent)
        builder.add_node(AgentType.USER_PROFILE_EXTRACTION, self.call_enhanced_user_profile_extraction_agent)

        # Always start with greeting detection
        builder.add_edge(START, AgentType.GREETING_DETECTION)

        # After greeting detection, extract user profile information with semantic memory
        builder.add_edge(AgentType.GREETING_DETECTION, AgentType.USER_PROFILE_EXTRACTION)

        # Conditionally proceed based on greeting detection result
        builder.add_conditional_edges(
            AgentType.USER_PROFILE_EXTRACTION,
            self.route_after_greeting_detection,
            {
                "is_greeting": END,
                "not_greeting": "PRODUCT_CHECK",
            },
        )

        # Add a node to check for product references
        builder.add_node("PRODUCT_CHECK", self.start_normal_flow)

        # Check if there are referenced products and handle them
        builder.add_conditional_edges(
            "PRODUCT_CHECK",
            self.check_for_referenced_products,
            {
                "has_referenced_products": AgentType.PRODUCT_REFERENCE,
                "no_referenced_products": "DETAIL_CHECK",
            },
        )

        # After handling referenced products, go directly to search
        builder.add_edge(AgentType.PRODUCT_REFERENCE, END)

        # Add a node for detail sufficiency check
        builder.add_node("DETAIL_CHECK", self.continue_normal_flow)

        # Conditionally start with SufficientDetailAgent or skip to ConversationSaturation
        builder.add_conditional_edges(
            "DETAIL_CHECK",
            self.determine_start_agent,
            {
                "start_with_sufficient_detail": AgentType.SUFFICIENT_DETAIL,
                "start_with_saturation": AgentType.CONVERSATION_SATURATION,
            },
        )

        # Add conditional branching based on sufficient detail check
        builder.add_conditional_edges(
            AgentType.SUFFICIENT_DETAIL,
            self.route_after_sufficient_detail,
            {
                "insufficient": AgentType.CONVERSATION_ENRICHMENT,
                "sufficient": AgentType.CONVERSATION_SATURATION,
            },
        )

        # If details are insufficient, the enrichment agent ends the flow
        builder.add_edge(AgentType.CONVERSATION_ENRICHMENT, END)

        # Add conditional branching based on conversation saturation
        builder.add_conditional_edges(
            AgentType.CONVERSATION_SATURATION,
            self.route_after_saturation_check,
            {
                "not_saturated": "PARALLEL_ENRICHMENT_SEARCH",
                "saturated": AgentType.SEARCH_QUERY,
            },
        )

        # Add a parallel branch for enrichment and search when not saturated
        builder.add_node("PARALLEL_ENRICHMENT_SEARCH", self.parallel_enrichment_and_search)
        builder.add_edge("PARALLEL_ENRICHMENT_SEARCH", END)

        # SearchQueryAgent ends the flow
        builder.add_edge(AgentType.SEARCH_QUERY, END)

        return builder.compile()

    async def call_enhanced_user_profile_extraction_agent(self, state: EnhancedChatState) -> EnhancedChatState:
        """Call the enhanced user profile extraction agent with semantic memory.

        Args:
            state: The current enhanced chat state

        Returns:
            The updated enhanced chat state
        """
        try:
            logger.info(f"[ENHANCED_WORKFLOW] Starting user profile extraction for user {state.user_id}")
            # Initialize memory components if not already done
            if not state.memory_components and state.user_id:
                memory_components = await self.semantic_memory_service.initialize_user_memory(state.user_id)
                memory_components_obj = MemoryComponents()
                memory_components_obj.memory_store = memory_components["store"]
                memory_components_obj.memory_manager = memory_components["memory_manager"]
                memory_components_obj.store_manager = memory_components["store_manager"]
                state.set_memory_components(memory_components_obj)
                logger.info(f"[ENHANCED_WORKFLOW] Initialized memory components for user {state.user_id}")

            # Process with enhanced agent
            logger.debug(f"[ENHANCED_WORKFLOW] Processing user profile extraction with enhanced agent")
            updated_state = await self.enhanced_user_profile_extraction_agent.process(state)
            logger.info(f"[ENHANCED_WORKFLOW] User profile extraction completed for user {state.user_id}")
            
            # Schedule memory consolidation if needed
            if updated_state.memory_consolidation_pending and updated_state.user_id:
                await self.background_memory_manager.schedule_memory_consolidation(
                    user_id=updated_state.user_id,
                    session_id=getattr(updated_state, 'session_id', 'unknown'),
                    priority=1
                )
                updated_state.clear_memory_consolidation_pending()
                logger.info(f"[ENHANCED_WORKFLOW] Scheduled memory consolidation for user {updated_state.user_id}")

            return updated_state

        except Exception as e:
            logger.error(f"[ENHANCED_WORKFLOW] Error in enhanced user profile extraction: {e}")
            # Fallback to basic processing
            return await self.enhanced_user_profile_extraction_agent.process(state)

    async def call_sufficient_detail_agent(self, state: EnhancedChatState) -> EnhancedChatState:
        """Call the sufficient detail agent with memory context."""
        return await self._call_agent_with_fallback(state, AgentType.SUFFICIENT_DETAIL)

    async def call_conversation_enrichment_agent(self, state: EnhancedChatState) -> EnhancedChatState:
        """Call the conversation enrichment agent with memory context."""
        return await self._call_agent_with_fallback(state, AgentType.CONVERSATION_ENRICHMENT)

    async def call_conversation_saturation_agent(self, state: EnhancedChatState) -> EnhancedChatState:
        """Call the conversation saturation agent with memory context."""
        return await self._call_agent_with_fallback(state, AgentType.CONVERSATION_SATURATION)

    async def call_search_agent(self, state: EnhancedChatState) -> EnhancedChatState:
        """Call the search agent with memory-enhanced context."""
        return await self._call_agent_with_fallback(state, AgentType.SEARCH_QUERY)

    async def call_greeting_detection_agent(self, state: EnhancedChatState) -> EnhancedChatState:
        """Call the greeting detection agent."""
        return await self._call_agent_with_fallback(state, AgentType.GREETING_DETECTION)

    async def call_product_reference_agent(self, state: EnhancedChatState) -> EnhancedChatState:
        """Call the product reference agent with memory context."""
        result = await self._call_agent_with_fallback(state, AgentType.PRODUCT_REFERENCE)
        # Clear search queries for product reference as per original workflow
        result.search_queries = []
        return result

    # Routing methods (same as original workflow)
    def route_after_greeting_detection(self, state: EnhancedChatState) -> str:
        """Route after greeting detection."""
        route = "is_greeting" if state.is_greeting else "not_greeting"
        logger.info(f"[ENHANCED_WORKFLOW] Routing after greeting detection: {route} (is_greeting={state.is_greeting})")
        return route

    def check_for_referenced_products(self, state: EnhancedChatState) -> str:
        """Check for referenced products."""
        route = "has_referenced_products" if state.has_referenced_products else "no_referenced_products"
        logger.debug(f"[ENHANCED_WORKFLOW] Product reference check: {route}")
        return route

    def determine_start_agent(self, state: EnhancedChatState) -> str:
        """Determine which agent to start with."""
        route = "start_with_sufficient_detail" if not state.is_detail_sufficient else "start_with_saturation"
        logger.info(f"[ENHANCED_WORKFLOW] Determining start agent: {route} (is_detail_sufficient={state.is_detail_sufficient})")
        return route

    def route_after_sufficient_detail(self, state: EnhancedChatState) -> str:
        """Route after sufficient detail check."""
        route = "insufficient" if not state.is_detail_sufficient else "sufficient"
        logger.info(f"[ENHANCED_WORKFLOW] Routing after sufficient detail: {route} (is_detail_sufficient={state.is_detail_sufficient})")
        return route

    def route_after_saturation_check(self, state: EnhancedChatState) -> str:
        """Route after saturation check."""
        route = "not_saturated" if not state.is_conversation_saturated else "saturated"
        logger.info(f"[ENHANCED_WORKFLOW] Routing after saturation check: {route} (is_conversation_saturated={state.is_conversation_saturated})")
        return route

    async def start_normal_flow(self, state: EnhancedChatState) -> EnhancedChatState:
        """Start the normal conversation flow."""
        logger.debug(f"[ENHANCED_WORKFLOW] Starting normal flow for user {state.user_id}")
        return state

    async def continue_normal_flow(self, state: EnhancedChatState) -> EnhancedChatState:
        """Continue the normal conversation flow."""
        logger.debug(f"[ENHANCED_WORKFLOW] Continuing normal flow for user {state.user_id}")
        return state

    async def parallel_enrichment_and_search(self, state: EnhancedChatState) -> EnhancedChatState:
        """Handle parallel enrichment and search."""
        try:
            logger.info(f"[ENHANCED_WORKFLOW] Starting parallel enrichment and search for user {state.user_id}")
            
            # Convert to regular ChatState for agent processing
            regular_state = self._convert_to_regular_chat_state(state)

            # First run enrichment (this will add the question)
            if AgentType.CONVERSATION_ENRICHMENT in self.agents:
                enrichment_agent = self.agents[AgentType.CONVERSATION_ENRICHMENT]
                enriched_state = await enrichment_agent.process(regular_state)
                
                # Save the enrichment messages to preserve the question
                enrichment_messages = enriched_state.messages.copy()
                
                # Then run search on the original state (not using the enriched state)
                if AgentType.SEARCH_QUERY in self.agents:
                    search_agent = self.agents[AgentType.SEARCH_QUERY]
                    search_state = await search_agent.process(regular_state)
                    
                    # Use enriched state as base but get the search queries from search state
                    # This prevents search agent from adding its own messages/questions
                    enriched_state.search_queries = search_state.search_queries
                    
                    # IMPORTANT: Ensure we only use the messages from the enrichment agent
                    # This prevents multiple questions from appearing
                    enriched_state.messages = enrichment_messages
                    
                    # Update the enhanced state with results
                    self._update_enhanced_state_from_regular(state, enriched_state)
                else:
                    logger.warning(f"[ENHANCED_WORKFLOW] Search agent not available for parallel processing")
                    self._update_enhanced_state_from_regular(state, enriched_state)
            else:
                logger.warning(f"[ENHANCED_WORKFLOW] Enrichment agent not available for parallel processing")
                # Just run search if enrichment is not available
                if AgentType.SEARCH_QUERY in self.agents:
                    search_agent = self.agents[AgentType.SEARCH_QUERY]
                    search_state = await search_agent.process(regular_state)
                    self._update_enhanced_state_from_regular(state, search_state)
            
            logger.info(f"[ENHANCED_WORKFLOW] Parallel enrichment and search completed for user {state.user_id}")
            return state
            
        except Exception as e:
            logger.error(f"[ENHANCED_WORKFLOW] Error in parallel enrichment and search: {e}")
            return state

    async def run(self, state) -> EnhancedChatState:
        """Process a chat query and return a response.

        Args:
            state: The current chat state (can be ChatState or EnhancedChatState)

        Returns:
            The updated enhanced chat state with the response
        """
        try:
            # Convert ChatState to EnhancedChatState if needed
            if not isinstance(state, EnhancedChatState):
                logger.info(f"[ENHANCED_WORKFLOW] Converting ChatState to EnhancedChatState for user {state.user_id}")
                enhanced_state = EnhancedChatState.from_chat_state(state)
            else:
                enhanced_state = state
            
            logger.info(f"[ENHANCED_WORKFLOW] Processing enhanced workflow for user {enhanced_state.user_id}")
            
            # Process through the graph
            logger.debug(f"[ENHANCED_WORKFLOW] Invoking workflow graph for user {enhanced_state.user_id}")
            result = await self.graph.ainvoke(enhanced_state)
            logger.debug(f"[ENHANCED_WORKFLOW] Workflow graph processing completed for user {enhanced_state.user_id}")
            
            # The graph returns a dict, so we need to convert it back to EnhancedChatState
            if isinstance(result, dict):
                logger.debug(f"[ENHANCED_WORKFLOW] Converting graph result dict to EnhancedChatState")
                result = EnhancedChatState.model_validate(result)
            
            # Final memory recording if needed (only for EnhancedChatState)
            if isinstance(result, EnhancedChatState) and result.memory_store and result.user_id and not result.memory_consolidation_pending:
                logger.info(f"[ENHANCED_WORKFLOW] Recording conversation memory for user {result.user_id}")
                await result.record_conversation_memory(self.semantic_memory_service)
                result.mark_memory_consolidation_pending()
                
                # Schedule background consolidation
                logger.info(f"[ENHANCED_WORKFLOW] Scheduling background memory consolidation for user {result.user_id}")
                await self.background_memory_manager.schedule_memory_consolidation(
                    user_id=result.user_id,
                    session_id=getattr(result, 'session_id', 'unknown'),
                    priority=2
                )
                result.clear_memory_consolidation_pending()
                logger.info(f"[ENHANCED_WORKFLOW] Memory consolidation scheduled for user {result.user_id}")
            elif not isinstance(result, EnhancedChatState) and enhanced_state.user_id:
                # For regular ChatState, we need to handle memory recording differently
                # Since we can't store memory components in regular ChatState, we'll record directly
                logger.info(f"[ENHANCED_WORKFLOW] Recording conversation memory directly for user {enhanced_state.user_id}")
                try:
                    # Record conversation using the enhanced state's memory components
                    if enhanced_state.memory_store and enhanced_state.user_id:
                        await enhanced_state.record_conversation_memory(self.semantic_memory_service)
                        
                        # Schedule background consolidation
                        logger.info(f"[ENHANCED_WORKFLOW] Scheduling background memory consolidation for user {enhanced_state.user_id}")
                        await self.background_memory_manager.schedule_memory_consolidation(
                            user_id=enhanced_state.user_id,
                            session_id=getattr(enhanced_state, 'session_id', 'unknown'),
                            priority=2
                        )
                        logger.info(f"[ENHANCED_WORKFLOW] Memory consolidation scheduled for user {enhanced_state.user_id}")
                except Exception as e:
                    logger.error(f"[ENHANCED_WORKFLOW] Error recording memory for regular ChatState: {e}")
            
            logger.info(f"[ENHANCED_WORKFLOW] Enhanced workflow processing completed for user {enhanced_state.user_id}")
            
            # If the input was a regular ChatState, convert back to maintain compatibility
            if not isinstance(state, EnhancedChatState):
                logger.info(f"[ENHANCED_WORKFLOW] Converting EnhancedChatState back to ChatState for compatibility")
                # Create a regular ChatState with the enhanced profile data
                from backend.domain.entities.chat import ChatState, UserProfile
                
                # Convert EnhancedUserProfile back to UserProfile
                # Handle both EnhancedUserProfile and regular UserProfile
                if hasattr(result.user_profile, 'health_conditions') and isinstance(result.user_profile.health_conditions, list):
                    # It's already a UserProfile or has the right structure
                    regular_profile = UserProfile(
                        name=getattr(result.user_profile, 'name', None),
                        email=getattr(result.user_profile, 'email', None),
                        age=getattr(result.user_profile, 'age', None),
                        location=getattr(result.user_profile, 'location', None),
                        health_conditions=getattr(result.user_profile, 'health_conditions', []),
                        dietary_restrictions=getattr(result.user_profile, 'dietary_restrictions', []),
                        medications=getattr(result.user_profile, 'medications', []),
                        activity_preferences=getattr(result.user_profile, 'activity_preferences', []),
                        product_preferences=getattr(result.user_profile, 'product_preferences', []),
                        budget_range=getattr(result.user_profile, 'budget_range', None),
                        fitness_goals=getattr(result.user_profile, 'fitness_goals', []),
                        adventure_plans=getattr(result.user_profile, 'adventure_plans', []),
                        experience_level=getattr(result.user_profile, 'experience_level', None),
                        frequency_of_use=getattr(result.user_profile, 'frequency_of_use', None),
                        physical_limitations=getattr(result.user_profile, 'physical_limitations', []),
                        time_constraints=getattr(result.user_profile, 'time_constraints', []),
                        group_size=getattr(result.user_profile, 'group_size', None),
                        family_considerations=getattr(result.user_profile, 'family_considerations', []),
                        climate_conditions=getattr(result.user_profile, 'climate_conditions', []),
                        storage_limitations=getattr(result.user_profile, 'storage_limitations', []),
                        last_updated=getattr(result.user_profile, 'last_updated', None)
                    )
                else:
                    # Fallback to original state's user profile
                    regular_profile = state.user_profile
                
                # Create regular ChatState
                regular_state = ChatState(
                    messages=result.messages,
                    search_queries=result.search_queries,
                    next_agent=result.next_agent,
                    weather_info=result.weather_info,
                    is_detail_sufficient=result.is_detail_sufficient,
                    is_conversation_saturated=result.is_conversation_saturated,
                    is_greeting=result.is_greeting,
                    user_id=result.user_id,
                    referenced_products=result.referenced_products,
                    user_profile=regular_profile
                )
                
                return regular_state
            else:
                return EnhancedChatState.model_validate(result)

        except Exception as e:
            logger.error(f"[ENHANCED_WORKFLOW] Error in enhanced workflow processing: {e}")
            raise


