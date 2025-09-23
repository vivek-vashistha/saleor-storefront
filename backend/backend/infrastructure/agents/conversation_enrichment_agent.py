import logging

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.domain.entities import ChatState
from backend.domain.exceptions import ServiceError
from backend.infrastructure.agents.interfaces import IAgent

from typing import Any, List, Optional
import os
import json
logger = logging.getLogger("conversational_commerce")



def _escape_prompt_text(text: str) -> str:
    """Escape curly braces so ChatPromptTemplate doesn't treat JSON keys as variables."""
    try:
        return text.replace("{", "{{").replace("}", "}}")
    except Exception:
        return text

def _build_extra_instructions(raw_text: str) -> str:
    """Turn raw JSON/text into clear, actionable prompt instructions."""
    if not raw_text:
        return ""
    try:
        data = json.loads(raw_text)
    except Exception:
        # Not JSON; return escaped text as-is
        return _escape_prompt_text(raw_text)

    lines: list[str] = []
    preferences = data.get("preferences", {}) if isinstance(data, dict) else {}
    budget = data.get("budget_limits", {}) if isinstance(data, dict) else {}
    past_orders = data.get("past_orders", []) if isinstance(data, dict) else []

    preferred_brands = preferences.get("preferred_brands") or []
    categories_of_interest = preferences.get("categories_of_interest") or []
    dietary = preferences.get("dietary") or []

    if preferred_brands:
        lines.append(
            "- Preferred brands: " + ", ".join(map(str, preferred_brands)) + ". Prioritize these when proposing products."
        )
    if categories_of_interest:
        lines.append(
            "- Areas of interest: " + ", ".join(map(str, categories_of_interest)) + ". Reflect these in suggestions."
        )
    if dietary:
        lines.append("- Dietary preferences: " + ", ".join(map(str, dietary)) + ". Avoid conflicts.")

    per_item = budget.get("per_item_max_inr")
    per_order = budget.get("per_order_max_inr")
    if per_item or per_order:
        limit_parts = []
        if per_item:
            limit_parts.append(f"per-item <= {per_item} INR")
        if per_order:
            limit_parts.append(f"per-order <= {per_order} INR")
        lines.append("- Budget limits: " + ", ".join(limit_parts) + ". Stay within these when recommending.")

    if past_orders:
        try:
            brands = sorted({str(i.get("brand")) for o in past_orders for i in (o.get("items") or []) if i.get("brand")})
            if brands:
                lines.append("- Past purchase brands: " + ", ".join(brands) + ". Use as soft preference.")
        except Exception:
            pass

    # Behavioral guidance to act on preferences immediately when intent is clear
    lines.append(
        "- If the user expresses a clear product intent (e.g., 'vitamin b12'), propose top options first that match preferred brands and budget, then ask one brief follow-up only if needed."
    )

    return "\n" + "\n".join(lines) + "\n"
def _load_extra_system_prompt() -> Optional[str]:
    """Load extra system prompt instructions from JSON or raw text.

    Order of precedence:
    1) Path from env var SYSTEM_PROMPT_JSON_PATH
    2) system_prompt_extra.json in this file's directory
    3) system_prompt_extra.json one and two levels up
    Returns a non-empty string if available; otherwise None.
    """
    candidates: List[str] = []
    env_path = os.getenv("SYSTEM_PROMPT_JSON_PATH")
    if env_path:
        candidates.append(env_path)

    here = os.path.dirname(__file__)
    candidates.append(os.path.join(here, "system_prompt_extra.json"))
    candidates.append(os.path.join(os.path.dirname(here), "system_prompt_extra.json"))
    candidates.append(os.path.join(os.path.dirname(os.path.dirname(here)), "system_prompt_extra.json"))
    candidates.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(here))), "system_prompt_extra.json"))
    candidates.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(here)))), "system_prompt_extra.json"))

    for path in candidates:
        try:
            if not os.path.exists(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
            if not raw or not raw.strip():
                continue
            try:
                data = json.loads(raw)
                if isinstance(data, str):
                    text = data.strip()
                else:
                    text = json.dumps(data, ensure_ascii=False)
            except Exception:
                text = raw.strip()
            if text:
                return text
        except Exception:
            continue
    return None


# Append extra system instructions if provided via JSON/text file
extra_user_details = _load_extra_system_prompt() or ""
    # if extra:
    #     sys_prompt += "\n\n# Extra user details\n" + extra

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
        safe_extra_user_details = _build_extra_instructions(extra_user_details)
        prompt = ChatPromptTemplate.from_messages(
            [
               (
                    "system",
                    f"""You are an expert at analyzing conversations about health, wellness and products (vitamins, supplements, sports nutrition, beauty, personal care, grocery).
                    Your task is to generate 2-3 specific questions to gather more information from the user
                    to better understand their needs for products.

                    When referencing prior purchases, do NOT ask the user to list products; instead use declarative phrasing like: 'You bought items in the past ...' and proceed with forward-looking questions.

                    {safe_extra_user_details}

                    PHRASE YOUR RESPONSES TO EXPLICITLY REFERENCE CONTEXT:
                    - When proposing options or asking follow-ups, explicitly reference user context using phrases like:
                      "Based on your preferences", "Based on your past orders", or "Based on your history".
                    - Example: "Based on your preferences (Swanson, budget), here are Vitamin B12 options..."

                    Focus on asking questions about:
                    1. Specific product types they might be interested in (e.g., probiotics, magnesium, collagen, vitamin B12)
                    2. Key needs or constraints (e.g., sugar-free, vegan, allergen-free, capsule vs. powder vs. gummy)
                    3. Use cases or health goals (e.g., gut health, sleep, energy, skin, sports recovery)
                    4. Dietary or medical considerations (e.g., diabetes, pregnancy, medications)
                    5. User preferences like budget, brand preferences, flavors, etc.
                    Make your questions conversational, specific, and contextually appropriate based on what the user has already shared.
                    {user_context}

                    ORDER CONTEXT: (past purchases, allergens, forms, brands, budgets, results, returns):
                    
                    {order_context}

                    # How to use ORDER_CONTEXT
                    - If the user has prior purchases, anchor your questions to what they tried, what worked/didn’t, and why.
                    - If ORDER_CONTEXT conflicts with USER_CONTEXT, **ask a clarifying question**.
                    - If ORDER_CONTEXT is empty, **do not mention it**; just ask contextually relevant questions.

                    
                    CRITICAL: If the user has mentioned health conditions (like diabetes, sugar problems, etc.), 
                    make sure to ask questions that consider their health needs when recommending supplements or products.
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
