import logging

from langgraph.constants import END, START
from langgraph.graph.state import CompiledStateGraph, StateGraph

from backend.application.interfaces import IChatWorkflow
from backend.domain.entities import ChatState
from backend.domain.enums import AgentType
from backend.infrastructure.factories import AgentFactory

logger = logging.getLogger("search_query_workflow")


class SearchQueryWorkflow(IChatWorkflow[ChatState]):
    """Workflow for evaluating a chat query with branching conversation logic."""

    def __init__(self, agent_factory: AgentFactory):
        """Initialize the SearchQueryWorkflow with the provided agent factory.

        Args:
            agent_factory: The factory for creating agents

        """
        super().__init__(agent_factory)
        self.agents = {
            AgentType.SEARCH_QUERY: agent_factory.create_agent(AgentType.SEARCH_QUERY),
            AgentType.SUFFICIENT_DETAIL: agent_factory.create_agent(AgentType.SUFFICIENT_DETAIL),
            AgentType.CONVERSATION_ENRICHMENT: agent_factory.create_agent(AgentType.CONVERSATION_ENRICHMENT),
            AgentType.CONVERSATION_SATURATION: agent_factory.create_agent(AgentType.CONVERSATION_SATURATION),
            AgentType.GREETING_DETECTION: agent_factory.create_agent(AgentType.GREETING_DETECTION),
            AgentType.PRODUCT_REFERENCE: agent_factory.create_agent(AgentType.PRODUCT_REFERENCE),
            AgentType.USER_PROFILE_EXTRACTION: agent_factory.create_agent(AgentType.USER_PROFILE_EXTRACTION),
        }

    def _build_graph(self) -> CompiledStateGraph:
        """Build the workflow graph with branching logic.

        Returns:
            The compiled workflow graph
        """
        builder = StateGraph(ChatState)

        # Add all agent nodes
        builder.add_node(AgentType.SUFFICIENT_DETAIL, self.call_sufficient_detail_agent)
        builder.add_node(AgentType.CONVERSATION_ENRICHMENT, self.call_conversation_enrichment_agent)
        builder.add_node(AgentType.CONVERSATION_SATURATION, self.call_conversation_saturation_agent)
        builder.add_node(AgentType.SEARCH_QUERY, self.call_search_agent)
        builder.add_node(AgentType.GREETING_DETECTION, self.call_greeting_detection_agent)
        builder.add_node(AgentType.PRODUCT_REFERENCE, self.call_product_reference_agent)
        builder.add_node(AgentType.USER_PROFILE_EXTRACTION, self.call_user_profile_extraction_agent)

        # Always start with greeting detection
        builder.add_edge(START, AgentType.GREETING_DETECTION)

        # After greeting detection, extract user profile information
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

    def route_after_greeting_detection(self, state: ChatState) -> str:
        """Determine next step based on greeting detection.

        Args:
            state: The current chat state

        Returns:
            Route string - either "is_greeting" or "not_greeting"
        """
        if state.is_greeting:
            return "is_greeting"
        return "not_greeting"

    async def start_normal_flow(self, state: ChatState) -> ChatState:
        """Placeholder node for starting the normal conversation flow.

        Args:
            state: The current chat state

        Returns:
            The unchanged chat state
        """
        return state

    def check_for_referenced_products(self, state: ChatState) -> str:
        """Check if there are referenced products in the state.

        Args:
            state: The current chat state

        Returns:
            Route string indicating whether there are referenced products
        """
        if state.has_referenced_products:
            return "has_referenced_products"
        return "no_referenced_products"

    async def continue_normal_flow(self, state: ChatState) -> ChatState:
        """Placeholder node for continuing the normal flow after checking for referenced products.

        Args:
            state: The current chat state

        Returns:
            The unchanged chat state
        """
        return state

    def determine_start_agent(self, state: ChatState) -> str:
        """Determine whether to start with sufficient detail check or skip to saturation.

        Args:
            state: The current chat state

        Returns:
            Route string indicating which agent to start with
        """
        if state.is_detail_sufficient:
            return "start_with_saturation"
        return "start_with_sufficient_detail"

    def route_after_sufficient_detail(self, state: ChatState) -> str:
        """Determine next step based on sufficient detail check.

        Args:
            state: The current chat state

        Returns:
            Route string - either "insufficient" or "sufficient"
        """
        if not state.is_detail_sufficient:
            state.is_detail_sufficient = True
            return "insufficient"
        return "sufficient"

    def route_after_saturation_check(self, state: ChatState) -> str:
        """Determine whether to do parallel enrichment+search or just search.

        Args:
            state: The current chat state

        Returns:
            Route string - either "not_saturated" or "saturated"
        """
        if not state.is_conversation_saturated:
            return "not_saturated"
        return "saturated"

    async def call_sufficient_detail_agent(self, state: ChatState) -> ChatState:
        """Call the sufficient detail agent to check if there's enough detail."""
        agent = self.agents[AgentType.SUFFICIENT_DETAIL]
        state = await agent.process(state)
        return state

    async def call_conversation_enrichment_agent(self, state: ChatState) -> ChatState:
        """Call the conversation enrichment agent to generate questions."""
        agent = self.agents[AgentType.CONVERSATION_ENRICHMENT]
        state = await agent.process(state)
        return state

    async def call_conversation_saturation_agent(self, state: ChatState) -> ChatState:
        """Call the conversation saturation agent to check if more detail would help."""
        agent = self.agents[AgentType.CONVERSATION_SATURATION]
        state = await agent.process(state)
        return state

    async def call_search_agent(self, state: ChatState) -> ChatState:
        """Call the search agent and update the state with the search queries."""
        agent = self.agents[AgentType.SEARCH_QUERY]
        state = await agent.process(state)
        return state

    async def call_greeting_detection_agent(self, state: ChatState) -> ChatState:
        """Call the greeting detection agent to check if the message is a greeting."""
        agent = self.agents[AgentType.GREETING_DETECTION]
        state = await agent.process(state)
        return state

    async def call_product_reference_agent(self, state: ChatState) -> ChatState:
        """Call the product reference agent to handle referenced products."""
        agent = self.agents[AgentType.PRODUCT_REFERENCE]
        state = await agent.process(state)
        state.search_queries = []
        return state

    async def call_user_profile_extraction_agent(self, state: ChatState) -> ChatState:
        """Call the user profile extraction agent to extract user facts."""
        agent = self.agents[AgentType.USER_PROFILE_EXTRACTION]
        state = await agent.process(state)
        return state

    async def parallel_enrichment_and_search(self, state: ChatState) -> ChatState:
        """Execute conversation enrichment and search query in parallel.

        Args:
            state: The current chat state

        Returns:
            The updated state after both operations
        """
        # First run enrichment (this will add the question)
        enrichment_agent = self.agents[AgentType.CONVERSATION_ENRICHMENT]
        enriched_state = await enrichment_agent.process(state)

        # Save the enrichment messages to preserve the question
        enrichment_messages = enriched_state.messages.copy()

        # Then run search on the original state (not using the enriched state)
        search_agent = self.agents[AgentType.SEARCH_QUERY]
        search_state = await search_agent.process(state)

        # Use enriched state as base but get the search queries from search state
        # This prevents search agent from adding its own messages/questions
        enriched_state.search_queries = search_state.search_queries

        # IMPORTANT: Ensure we only use the messages from the enrichment agent
        # This prevents multiple questions from appearing
        enriched_state.messages = enrichment_messages
        return enriched_state

    async def run(self, state: ChatState) -> ChatState:
        """Process a chat query and return a response.

        Args:
            state: The current chat state

        Returns:
            The updated chat state with the response

        """
        return ChatState.model_validate(await self.graph.ainvoke(state))
