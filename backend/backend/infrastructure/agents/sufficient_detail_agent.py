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
                    """You are an expert at analyzing conversations about health, wellness, and consumer products.
                    Your task is to determine if a conversation contains sufficient detail to generate
                    a meaningful product search query for vitamins, supplements, health products, personal care, and general consumer goods.

                    A conversation has sufficient detail if it includes at least 2 of the following:
                    1. Specific product types (e.g., probiotics, vitamin B12, backpack, hiking boots, skincare, supplements)
                    2. Key features or requirements (e.g., sugar-free, vegan, waterproof, lightweight, age-appropriate)
                    3. Use cases or health goals (e.g., gut health, energy, sleep, children's products, outdoor activities)
                    4. User characteristics (e.g., age, health conditions, dietary restrictions, activity level)
                    5. User preferences (e.g., budget-friendly, premium quality, brand preferences, specific needs)

                    IMPORTANT: Even simple requests like "probiotics for gut health" 
                    should be considered sufficient detail as they contain clear product type and target user information.

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
            
            # Add debug logging
            logger.info(f"[SUFFICIENT_DETAIL] Analysis result: {sufficiency_response.is_sufficient}")
            logger.info(f"[SUFFICIENT_DETAIL] User profile context: health_conditions={getattr(state.user_profile, 'health_conditions', [])}, product_preferences={getattr(state.user_profile, 'product_preferences', [])}")
            
            return state
        except Exception as e:
            raise ServiceError(detail=f"Error in SufficientDetailAgent.process: {e}")
