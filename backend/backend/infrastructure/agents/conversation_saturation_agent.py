import logging

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.domain.entities import ChatState
from backend.domain.exceptions import ServiceError
from backend.infrastructure.agents.interfaces import IAgent

logger = logging.getLogger("conversational_commerce")


class SaturationResponse(BaseModel):
    """Represents a saturation response."""

    is_saturated: bool = Field(description="Boolean indicating if the conversation is saturated")


class ConversationSaturationAgent(IAgent[ChatState]):
    """Agent for determining if a conversation is saturated with enough detail."""

    async def is_conversation_saturated(self, messages: list[dict]) -> SaturationResponse:
        """Determine if the conversation is saturated with enough detail.

        Args:
            messages: A list of conversation messages in string format

        Returns:
            A SaturationResponse object indicating if the conversation is saturated.

        """
        # Create a prompt for determining if the conversation is saturated
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert at analyzing conversations about outdoor gear and equipment.
                    Your task is to determine if a conversation is saturated with enough detail to generate
                    optimal product search results, or if more information would significantly improve the results.

                    A conversation is considered saturated when it contains comprehensive information about:
                    1. Specific product types (e.g., tent, backpack, hiking boots)
                    2. Key features or requirements (e.g., waterproof, lightweight, durable)
                    3. Activities or use cases (e.g., hiking, camping, climbing)
                    4. Environmental conditions (e.g., winter, rainy, hot)
                    5. User preferences (e.g., budget-friendly, premium quality)

                    Respond with ONLY 'true' if the conversation is saturated with enough detail, or 'false' if more information
                    would significantly improve the search results.
                    """,
                ),
            ]
            + [(message["type"], message["content"]) for message in messages if message["type"] in {"human", "ai"}]
        )

        chain = prompt | self.llm.with_structured_output(SaturationResponse)
        saturation_response = await chain.ainvoke({})
        return saturation_response

    async def process(self, state: ChatState) -> ChatState:
        """Process the agent state to determine if the conversation is saturated.

        Args:
            state: The current agent state

        Returns:
            The updated agent state
        """
        try:
            saturation_response = await self.is_conversation_saturated(state.messages)
            state.is_conversation_saturated = saturation_response.is_saturated
            return state
        except Exception as e:
            raise ServiceError(detail=f"Error in ConversationSaturationAgent.process: {e}")
