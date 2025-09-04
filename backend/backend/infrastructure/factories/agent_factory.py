from langchain_core.language_models import BaseChatModel

from backend.domain.enums.agent_type import AgentType
from backend.infrastructure.agents import (
    ConversationEnrichmentAgent,
    ConversationSaturationAgent,
    GreetingDetectionAgent,
    ProductReferenceAgent,
    SearchQueryAgent,
    SufficientDetailAgent,
)
from backend.infrastructure.agents.user_profile_extraction_agent import UserProfileExtractionAgent
from backend.infrastructure.agents.interfaces import IAgent


class AgentFactory:
    """Factory for creating agents."""

    def __init__(self, llm: BaseChatModel) -> None:
        """Initialize the agent factory.

        Args:
            llm: LLM service to use for the agents

        """
        self.llm = llm

    def create_agent(self, agent_type: AgentType) -> IAgent:
        """Create an agent based on the specified type.

        Args:
            agent_type: The type of agent to create

        Returns:
            An agent instance of the specified type

        Raises:
            ValueError: If an invalid agent type is provided
        """
        if agent_type == AgentType.SEARCH_QUERY:
            return SearchQueryAgent(self.llm)

        if agent_type == AgentType.SUFFICIENT_DETAIL:
            return SufficientDetailAgent(self.llm)

        if agent_type == AgentType.CONVERSATION_ENRICHMENT:
            return ConversationEnrichmentAgent(self.llm)

        if agent_type == AgentType.CONVERSATION_SATURATION:
            return ConversationSaturationAgent(self.llm)

        if agent_type == AgentType.GREETING_DETECTION:
            return GreetingDetectionAgent(self.llm)

        if agent_type == AgentType.PRODUCT_REFERENCE:
            return ProductReferenceAgent(self.llm)

        if agent_type == AgentType.USER_PROFILE_EXTRACTION:
            return UserProfileExtractionAgent(self.llm)

        raise ValueError(f"Invalid agent type: {agent_type}")
