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
        description="List of questions to ask the user to get more details to better understand their needs "
        "for the products (vitamins, supplements, sports nutrition, beauty, personal care, grocery)."
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
        
        # Derive a lightweight ORDER CONTEXT from state cache or prior conversation
        order_context = ""
        try:
            # Prefer cached order summary if present on state
            if getattr(user_profile, "last_order_summary", None):
                order_context = f"\nORDER CONTEXT:\n{user_profile.last_order_summary}\n"
            ai_msgs = [m.get("content", "") for m in messages if m.get("type") == "ai"]
            # Flatten lists of content
            flat_msgs: list[str] = []
            for c in ai_msgs:
                if isinstance(c, list):
                    flat_msgs.extend([str(x) for x in c])
                else:
                    flat_msgs.append(str(c))
            recent_order_msgs = [s for s in flat_msgs if any(k in s.lower() for k in ["order", "fulfilled", "shipment", "tracking", "status"])]
            if not order_context and recent_order_msgs:
                # Keep the most recent concise line
                last = recent_order_msgs[-1]
                order_context = f"\nORDER CONTEXT:\n{last}\n"
        except Exception:
            pass

        # Create a prompt for generating questions to enrich the conversation
        prompt = ChatPromptTemplate.from_messages(
            [
               (
                    "system",
                    f"""You are an expert at analyzing conversations about health, wellness and products (vitamins, supplements, sports nutrition, beauty, personal care, grocery).
                    Your task is to generate 2-3 specific questions to gather more information from the user
                    to better understand their needs for products.

                    Personalization (ALWAYS apply when USER CONTEXT is available):
                    - Begin with a short, friendly one-sentence response that acknowledges ONE relevant detail from the USER CONTEXT (e.g., a goal like better sleep, a form preference like capsules/powders, a budget like budget-friendly, or a category preference like probiotics/magnesium). Keep it subtle; do not repeat the whole profile.
                    - Then ask 2 concise questions tailored to the user’s context to efficiently progress toward good recommendations.
                    - Never reveal private/sensitive data; keep it lightweight and helpful.

                    Ask questions about:
                    1. Specific product types (e.g., probiotics, magnesium, collagen, vitamin B12)
                    2. Key needs or constraints (e.g., sugar-free, vegan, allergen-free, capsule vs. powder vs. gummy)
                    3. Use cases or health goals (e.g., gut health, sleep, energy, skin, sports recovery)
                    4. Dietary or medical considerations (e.g., diabetes, pregnancy, medications)
                    5. Preferences like budget range, brand preferences, flavors, quantity/size.
                    Make your questions conversational, specific, and contextually appropriate based on what the user has already shared.

                    USER CONTEXT:
                    {user_context}

                    ORDER CONTEXT (past purchases, allergens, forms, brands, budgets, results, returns):
                    {order_context}

                    How to use ORDER CONTEXT
                    - If prior purchases exist, reference them lightly (e.g., “since you tried X…”). Focus on what worked/didn’t and why.
                    - If ORDER CONTEXT conflicts with USER CONTEXT, ask a brief clarifying question.
                    - If ORDER CONTEXT is empty, do not mention it.

                    Health safety: If the user mentions conditions (e.g., diabetes), make sure your questions consider those needs.
                    Output MUST include a short natural “response” and a list of 2-3 “questions”.
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
