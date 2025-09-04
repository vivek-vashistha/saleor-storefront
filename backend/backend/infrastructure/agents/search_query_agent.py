import logging

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.domain.entities import ChatState, SearchQuery
from backend.domain.exceptions import ServiceError
from backend.infrastructure.agents.interfaces import IAgent

logger = logging.getLogger("conversational_commerce")


class SearchQueries(BaseModel):
    """Represents a collection of search queries.

    Attributes:
        queries (List[SearchQuery]): List of SearchQuery objects

    """

    queries: list[SearchQuery] = Field(description="List of search queries")


class SearchQueryAgent(IAgent[ChatState]):
    """Agent for generating search queries from conversations."""

    async def generate_search_queries(self, messages: list[dict], user_profile=None) -> list[SearchQuery]:
        """Generate search queries from conversation messages.

        Args:
            messages: A list of conversation messages in string format
            user_profile: User profile information if available

        Returns:
            A list of SearchQuery objects with search queries and their associated product categories

        """
        # Predefined list of allowed categories
        allowed_categories = [
            "tent",
            "sleeping gear",
            "backpacks",
            "camp kitchen",
            "camp hydration",
            "camp furniture",
            "lighting",
            "gadgets and gears",
            "hiking clothing",
            "hiking footwear",
            "health and safety",
            "kids camping gear",
            "camp hydration",
            "hiking clothing",
            "camp and hike deals",
            "camp electronics",
            "climbing shoes",
            "climbing harnesses",
            "climbing hardware",
            "climbing ropes",
            "webbing and cords",
            "essentials",
            "climbing clothing",
            "beverages",
        ]

        # Build user context from profile
        user_context = ""
        if user_profile and user_profile.has_user_profile:
            user_context = f"""
            
USER PROFILE CONTEXT:
{user_profile.user_profile.get_relevant_context('general')}

IMPORTANT: Use this user profile information to enhance search queries. For example:
- If they have health conditions (like diabetes), include health-related search terms
- If they have dietary restrictions, consider food-related gear needs
- If they have specific activity preferences, focus on those activities
- If they have budget constraints, consider price-related terms
- If they have experience level, tailor search terms to their expertise
"""
            logger.info(f"Using user profile context: {user_profile.user_profile.get_relevant_context('general')}")
        else:
            logger.info("No user profile context available for search query generation")

        system_prompt = f"""You are a product search expert. Your task is to analyze a conversation
and extract multiple relevant search queries for finding outdoor gear and equipment.

For each distinct product or need mentioned in the conversation, generate a separate search query.

Focus on identifying:
1. Specific product types (e.g., tent, backpack, hiking boots)
2. Key features or requirements (e.g., waterproof, lightweight, durable)
3. Activities or use cases (e.g., hiking, camping, climbing)
4. Environmental conditions (e.g., winter, rainy, hot)
5. User preferences (e.g., budget-friendly, premium quality)

You MUST ONLY use categories from this allowed list: {{categories_str}}.
If a product doesn't clearly fit into one of these categories, match it to the closest category.

IMPORTANT: For beverage-related queries (juices, drinks, beverages):
- Use the "beverages" category for actual drink products (juices, etc.)
- Use "camp hydration" for portable drink containers, water bottles, and hydration equipment
- Use "essentials" for general drink-related gear and accessories
- Use "camp kitchen" for drink preparation equipment
- If someone asks for "juices", "drinks", or "beverages", use the "beverages" category

{user_context}

CRITICAL: If the user has health conditions (like diabetes, sugar problems, etc.), 
make sure to include health-related search terms and consider their specific needs when generating queries.
"""

        # Create a prompt for generating search queries with categories from conversation
        relevant_messages = [
            (message["type"], message["content"]) for message in messages if message["type"] in {"human", "ai"}
        ]
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_prompt,
                ),
            ]
            + relevant_messages,
        )

        chain = prompt | self.llm.with_structured_output(SearchQueries)
        search_queries = await chain.ainvoke({"categories_str": ", ".join(allowed_categories)})
        logger.info(f"Generated {len(search_queries.queries)} search queries from conversation")

        # Log detailed information about each search query
        for i, query in enumerate(search_queries.queries):
            logger.info(f"Search Query {i+1}: '{query.query}' with categories: {query.categories}")

        queries = []
        taken_categories = set()
        for search_query in search_queries.queries:
            categories = frozenset(search_query.categories)  # Convert to frozenset which is hashable
            if categories not in taken_categories:
                queries.append(search_query)
                taken_categories.add(categories)
                logger.info(f"Added unique search query: '{search_query.query}' -> categories: {list(categories)}")
            else:
                logger.info(f"Skipped duplicate search query: '{search_query.query}' -> categories: {list(categories)}")

        logger.info(f"Final unique search queries: {len(queries)}")
        return queries

    async def process(self, state: ChatState) -> ChatState:
        """Process the agent state to extract multiple search queries with categories.

        Args:
            state: The current agent state

        Returns:
            The updated agent state with search queries and categories
        """
        try:
            # Generate search queries with categories, passing user profile
            search_queries = await self.generate_search_queries(state.messages, state)

            # Store the search queries in the state
            state.search_queries = search_queries

            return state
        except Exception as e:
            raise ServiceError(detail=f"Error in SearchQueryAgent: {e}")
