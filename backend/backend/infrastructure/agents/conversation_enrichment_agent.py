import logging

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.domain.entities import ChatState
from backend.domain.exceptions import ServiceError
from backend.infrastructure.agents.interfaces import IAgent

logger = logging.getLogger("conversational_commerce")


class EnrichmentResponse(BaseModel):
    """Represents an enrichment response."""

    response: str = Field(description="Naturally flowing sentence to continue conversation before asking questions")
    questions: list[str] = Field(
        description="List of questions to ask the user to get more details to better understanding their needs "
        "for outdoor gear and equipment."
    )


class ConversationEnrichmentAgent(IAgent[ChatState]):
    """Agent for generating questions to enrich a conversation with more details."""

    async def generate_questions(self, messages: list[dict], user_profile=None) -> EnrichmentResponse:
        """Generate questions to enrich the conversation with more details.

        Args:
            messages: A list of conversation messages in string format
            user_profile: User profile information if available

        Returns:
            A list of questions to ask the user
        """
        # Build user context from profile
        user_context = ""
        if user_profile and user_profile.has_user_profile:
            user_context = f"""
            
USER PROFILE CONTEXT:
{user_profile.user_profile.get_relevant_context('general')}

IMPORTANT: Use this user profile information to personalize your questions. For example:
- If they have health conditions (like diabetes), consider dietary and health-related gear needs
- If they have specific activity preferences, focus questions on those activities
- If they have budget constraints, consider price-related questions
- If they have experience level, tailor questions to their expertise
"""
        
        # Create a prompt for generating questions to enrich the conversation
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"""You are an expert at analyzing conversations about outdoor gear and equipment.
                    Your task is to generate 2-3 specific questions to gather more information from the user
                    to better understand their needs for outdoor gear and equipment.

                    Focus on asking questions about:
                    1. Specific product types they might be interested in
                    2. Key features or requirements they need
                    3. Activities or use cases they have in mind
                    4. Environmental conditions they'll be using the gear in
                    5. User preferences like budget, brand preferences, etc.

                    Make your questions conversational, specific, and contextually appropriate based on what the user has already shared.
                    
                    {user_context}
                    
                    CRITICAL: If the user has mentioned health conditions (like diabetes, sugar problems, etc.), 
                    make sure to ask questions that consider their health needs when recommending gear or products.
                    """,
                )
            ]
            + [(message["type"], message["content"]) for message in messages if message["type"] in {"human", "ai"}]
        )

        chain = prompt | self.llm.with_structured_output(EnrichmentResponse)
        enrichment_response = await chain.ainvoke({})
        logger.info(f"Generated {len(enrichment_response.questions)} questions for conversation enrichment")
        return enrichment_response

    async def process(self, state: ChatState) -> ChatState:
        """Process the agent state to generate questions for conversation enrichment.

        Args:
            state: The current agent state

        Returns:
            The updated agent state with generated questions
        """
        try:
            # Generate questions to enrich the conversation, passing user profile
            enrichment_response = await self.generate_questions(state.messages, state)

            # Store the questions in the state
            response = enrichment_response.response
            questions = enrichment_response.questions
            content = [response, questions[0]]

            state.messages.append(AIMessage(content=content).model_dump())

            # Reset the flags to ensure we don't get stuck in loops
            state.is_detail_sufficient = True

            return state
        except Exception as e:
            raise ServiceError(detail=f"Error in ConversationEnrichmentAgent.process: {e}")
