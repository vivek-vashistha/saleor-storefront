import logging

from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.domain.entities import ChatState
from backend.domain.exceptions import ServiceError
from backend.infrastructure.agents.interfaces import IAgent

logger = logging.getLogger("conversational_commerce")


class GreetingResponse(BaseModel):
    """Represents a greeting response."""

    is_greeting: bool = Field(description="Boolean indicating if the message is a greeting")


class GreetingDetectionAgent(IAgent[ChatState]):
    """Agent for detecting greeting messages and providing appropriate responses."""

    async def _classify_greeting_with_llm(self, message: str) -> GreetingResponse:
        """Use LLM to classify whether a message is a greeting.

        Args:
            message: The user's message

        Returns:
            A GreetingResponse object indicating if the message is a greeting

        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a classifier that determines if a message is a greeting or not.
                    Respond with ONLY 'true' if the message is a pure greeting without asking about products or services.
                    Respond with ONLY 'false' if the message is asking about products or services.
                    """,
                ),
                ("human", "{message}"),
            ]
        )

        chain = prompt | self.llm.with_structured_output(GreetingResponse)
        greeting_response = await chain.ainvoke({"message": message})
        return greeting_response

    async def generate_greeting_response(self, message: str) -> str:
        """Generate a greeting response with information about the assistant's capabilities.

        Args:
            message (str): The user's message'

        Returns:
            A friendly greeting response string
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a friendly assistant for an health and wellness store (vitamins, supplements, sports nutrition, beauty, personal care, grocery).
                    Craft a warm greeting that:
                    1. Welcomes the user
                    2. Naturally flows after the user's greeting/message
                    3. Briefly explains that you can help find products (e.g., probiotics for gut health, magnesium for sleep, collagen for skin, vitamin B12 for energy, keto baking flour)
                    4. Provides 1-2 examples of what users can ask about.
                    5. Keeps the message concise (under 75 words) and conversational

                    Respond with just the greeting message, no additional text.
                    """,
                ),
                ("human", message),
            ]
        )

        try:
            chain = prompt | self.llm | StrOutputParser()
            response = await chain.ainvoke({})
            return response.strip()
        except Exception as e:
            logger.error(f"Error generating greeting response: {e}")
            return "Hello! I'm your product assistant. What health goals or products can I help you with today?"

    async def process(self, state: ChatState) -> ChatState:
        """Process the agent state to detect greetings and provide responses.

        Args:
            state: The current agent state

        Returns:
            The updated agent state with greeting response if applicable
        """
        try:
            # Get the last human message
            # human_messages = [msg for msg in state.messages if msg.get("type", "").lower() == "human"]
            human_messages = [msg for msg in state.messages if msg["type"].lower() == "human"]

            if not human_messages:
                return state

            last_message = human_messages[-1]["content"]
            state.is_greeting = False

            # Check if it's a greeting
            is_greeting_response = await self._classify_greeting_with_llm(last_message)

            if is_greeting_response.is_greeting:
                # Generate greeting response
                greeting_response = await self.generate_greeting_response(last_message)

                # Add the greeting response to the state
                state.messages.append(AIMessage(content=greeting_response).model_dump())

                # Mark that we've already handled this as a greeting
                state.is_greeting = True

            return state
        except Exception as e:
            raise ServiceError(detail=f"Error in GreetingDetectionAgent.process: {e}")
