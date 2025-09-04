import logging

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.domain.entities import ChatState
from backend.domain.exceptions import ServiceError
from backend.infrastructure.agents.interfaces import IAgent

logger = logging.getLogger("conversational_commerce")


class SufficiencyResponse(BaseModel):
    """Represents a sufficiency response."""

    is_sufficient: bool = Field(description="Boolean indicating if the conversation has sufficient detail")


class SufficientDetailAgent(IAgent[ChatState]):
    """Agent for determining if a conversation has sufficient detail for product search."""

    async def has_sufficient_detail(self, messages: list[dict]) -> SufficiencyResponse:
        """Determine if the conversation has sufficient detail for product search.

        Args:
            messages: A list of conversation messages in string format

        Returns:
            A SufficiencyResponse object indicating if the conversation has sufficient detail.

        """
        # Create a prompt for determining if the conversation has sufficient detail
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert at analyzing conversations about outdoor gear and equipment.
                    Your task is to determine if a conversation contains sufficient detail to generate
                    a meaningful product search query.

                    A conversation has sufficient detail if it includes at least 2 of the following:
                    1. Specific product types (e.g., tent, backpack, hiking boots)
                    2. Key features or requirements (e.g., waterproof, lightweight, durable)
                    3. Activities or use cases (e.g., hiking, camping, climbing)
                    4. Environmental conditions (e.g., winter, rainy, hot)
                    5. User preferences (e.g., budget-friendly, premium quality)

                    Respond with ONLY 'true' if the conversation has sufficient detail, or 'false' if more information is needed.
                    """,
                )
            ]
            + [(message["type"], message["content"]) for message in messages if message["type"] in {"human", "ai"}]
        )

        chain = prompt | self.llm.with_structured_output(SufficiencyResponse)
        sufficiency_response = await chain.ainvoke({})
        return sufficiency_response

    async def process(self, state: ChatState) -> ChatState:
        """Process the agent state to determine if the conversation has sufficient detail.

        Args:
            state: The current agent state

        Returns:
            The updated agent state
        """
        try:
            # Determine if the conversation has sufficient detail
            sufficiency_response = await self.has_sufficient_detail(state.messages)
            state.is_detail_sufficient = sufficiency_response.is_sufficient
            return state
        except Exception as e:
            raise ServiceError(detail=f"Error in SufficientDetailAgent.process: {e}")
