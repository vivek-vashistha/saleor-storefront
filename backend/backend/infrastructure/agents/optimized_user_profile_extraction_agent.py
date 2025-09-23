import logging
import re
from typing import Dict, Any, List, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.domain.entities.enhanced_chat import EnhancedChatState
from backend.domain.exceptions import ServiceError
from backend.infrastructure.agents.interfaces import IAgent
from backend.application.services.semantic_memory_service import SemanticMemoryService

logger = logging.getLogger("conversational_commerce")


class UnifiedProfileExtraction(BaseModel):
    """Unified extraction model that captures both profile data and semantic context in one LLM call."""
    
    # === BASIC PROFILE FIELDS ===
    name: str = Field(default="", description="User's name if mentioned")
    email: str = Field(default="", description="User's email if mentioned")
    age: str = Field(default="", description="User's age if mentioned")
    location: str = Field(default="", description="User's location if mentioned")
    
    # === HEALTH & MEDICAL INFORMATION ===
    health_conditions: List[str] = Field(default_factory=list, description="Health conditions mentioned")
    dietary_restrictions: List[str] = Field(default_factory=list, description="Dietary restrictions mentioned")
    medications: List[str] = Field(default_factory=list, description="Medications mentioned")
    
    # === PREFERENCES ===
    activity_preferences: List[str] = Field(default_factory=list, description="Activity preferences mentioned")
    product_preferences: List[str] = Field(default_factory=list, description="Product preferences mentioned")
    budget_range: str = Field(default="", description="Budget range if mentioned")
    
    # === GOALS & ASPIRATIONS ===
    fitness_goals: List[str] = Field(default_factory=list, description="Fitness goals mentioned")
    adventure_plans: List[str] = Field(default_factory=list, description="Adventure plans mentioned")
    
    # === BEHAVIOR & HABITS ===
    experience_level: str = Field(default="", description="Experience level if mentioned")
    frequency_of_use: str = Field(default="", description="Frequency of use if mentioned")
    
    # === CONSTRAINTS & BOUNDARIES ===
    physical_limitations: List[str] = Field(default_factory=list, description="Physical limitations mentioned")
    time_constraints: List[str] = Field(default_factory=list, description="Time constraints mentioned")
    
    # === SOCIAL & PRACTICAL ===
    group_size: str = Field(default="", description="Group size if mentioned")
    family_considerations: List[str] = Field(default_factory=list, description="Family considerations mentioned")
    climate_conditions: List[str] = Field(default_factory=list, description="Climate conditions mentioned")
    storage_limitations: List[str] = Field(default_factory=list, description="Storage limitations mentioned")
    
    # === SEMANTIC CONTEXT FIELDS ===
    conversation_themes: List[str] = Field(default_factory=list, description="Main themes and topics discussed")
    interaction_patterns: Optional[Dict[str, str]] = Field(default=None, description="User's interaction patterns and behavior")
    communication_style: str = Field(default="", description="User's communication style (direct/indirect, detailed/concise, etc.)")
    decision_factors: List[str] = Field(default_factory=list, description="Key factors that influence user's decision-making")
    product_affinities: List[str] = Field(default_factory=list, description="Product categories and brands the user shows interest in")


class OptimizedUserProfileExtractionAgent(IAgent[EnhancedChatState]):
    """Optimized agent that extracts both user profile and semantic context in a single LLM call."""

    def __init__(self, llm, semantic_memory_service: SemanticMemoryService):
        """Initialize the OptimizedUserProfileExtractionAgent.

        Args:
            llm: The language model to use for extraction
            semantic_memory_service: Service for semantic memory operations
        """
        self.llm = llm
        self.semantic_memory_service = semantic_memory_service

    async def extract_unified_profile(self, messages: List[Dict], products: List[Any], search_queries: List[Any]) -> UnifiedProfileExtraction:
        """Extract both user profile and semantic context in a single LLM call.

        Args:
            messages: List of conversation messages
            products: Products mentioned or recommended
            search_queries: Search queries made

        Returns:
            Unified extraction result containing both profile and semantic data
        """
        # Create a comprehensive prompt for unified extraction
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are an expert at extracting comprehensive user information from conversations about health, wellness and products (vitamins, supplements, sports nutrition, beauty, personal care, and grocery).

                Your task is to analyze the conversation and extract BOTH:
                1. **STRUCTURED USER PROFILE DATA** - factual information about the user
                2. **SEMANTIC CONTEXT** - behavioral patterns, themes, and insights

                === STRUCTURED PROFILE EXTRACTION ===
                Extract relevant user information in these categories:

                1. **Identity & Profile**: Name, email, age, location
                2. **Health & Medical**: Health conditions, dietary restrictions, medications
                3. **Preferences**: Health interests, product preferences (e.g., probiotics, magnesium, collagen), budget range
                4. **Goals & Aspirations**: Health goals (e.g., better sleep, gut health, energy)
                5. **Behavior & Habits**: Supplement experience/usage, frequency of use
                6. **Constraints & Boundaries**: Allergies, intolerances, dietary restrictions, physical limitations, time constraints
                7. **Relationships & Social**: Group size, family considerations
                8. **Practical Information**: Storage limitations, form factor preferences (capsule, powder, gummy)

                === SEMANTIC CONTEXT EXTRACTION ===
                Also analyze and extract:

                1. **Conversation Themes**: Main topics and recurring themes (3-5 key themes)
                2. **Interaction Patterns**: How the user interacts (question style, decision-making approach, communication preferences, information-seeking behavior)
                3. **Communication Style**: Direct vs indirect, detailed vs concise, formal vs casual, technical vs simple
                4. **Decision Factors**: Key factors influencing decisions (price, quality, brand, features, use cases)
                5. **Product Affinities**: Categories and brands the user shows interest in

                === IMPORTANT GUIDELINES ===
                - Only extract information that is explicitly mentioned or clearly implied
                - For health conditions, be thorough (e.g., "sugar problem" = diabetes, "sugar issue" = diabetes)
                - For lists, separate items with commas
                - If no information is found for a category, leave it empty
                - Be conservative - only extract information you're confident about
                - Pay special attention to health-related information as it's crucial for recommendations
                - For semantic context, focus on patterns that would be useful for future personalization

                Return the information in a structured format that can be parsed."""
            ),
            (
                "human",
                "Please analyze this conversation and extract comprehensive user information:\n\n{conversation_text}\n\nProducts mentioned: {products}\nSearch queries: {search_queries}"
            )
        ])

        # Format conversation for analysis
        conversation_text = self._format_messages_for_extraction(messages)
        
        # Format products and search queries for context
        products_text = self._format_products_for_context(products)
        search_queries_text = self._format_search_queries_for_context(search_queries)
        
        try:
            chain = prompt | self.llm.with_structured_output(UnifiedProfileExtraction)
            extraction_result = await chain.ainvoke({
                "conversation_text": conversation_text,
                "products": products_text,
                "search_queries": search_queries_text
            })
            
            logger.info(f"Extracted unified profile and semantic context: {extraction_result}")
            return extraction_result
            
        except Exception as e:
            logger.error(f"Error extracting unified profile: {e}")
            return UnifiedProfileExtraction()

    def _format_messages_for_extraction(self, messages: List[Dict]) -> str:
        """Format messages for profile extraction.

        Args:
            messages: List of conversation messages

        Returns:
            Formatted conversation text
        """
        formatted_messages = []
        
        for i, msg in enumerate(messages):
            msg_type = msg.get('type', 'human')
            content = msg.get('content', '')
            
            # Handle content that might be a list or string
            if isinstance(content, list):
                content_str = ' '.join(str(item) for item in content)
            else:
                content_str = str(content)
            
            # Clean up the content
            content_str = content_str.strip()
            if content_str:
                speaker = "User" if msg_type == "human" else "Assistant"
                formatted_messages.append(f"{speaker}: {content_str}")
        
        return "\n".join(formatted_messages)

    def _format_products_for_context(self, products: List[Any]) -> str:
        """Format products for context in extraction.

        Args:
            products: List of products

        Returns:
            Formatted products text
        """
        if not products:
            return "None"
        
        product_info = []
        for product in products:
            if hasattr(product, 'name') and product.name:
                product_info.append(product.name)
            elif hasattr(product, 'title') and product.title:
                product_info.append(product.title)
        
        return ", ".join(product_info) if product_info else "None"

    def _format_search_queries_for_context(self, search_queries: List[Any]) -> str:
        """Format search queries for context in extraction.

        Args:
            search_queries: List of search queries

        Returns:
            Formatted search queries text
        """
        if not search_queries:
            return "None"
        
        query_texts = []
        for query in search_queries:
            if hasattr(query, 'query') and query.query:
                query_texts.append(query.query)
            elif isinstance(query, str):
                query_texts.append(query)
        
        return ", ".join(query_texts) if query_texts else "None"

    def _extract_email_from_messages(self, messages: List[Dict]) -> str:
        """Extract email from messages using regex as backup.

        Args:
            messages: List of conversation messages

        Returns:
            Extracted email or empty string
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        for msg in messages:
            content = msg.get('content', '')
            if isinstance(content, list):
                content = ' '.join(str(item) for item in content)
            
            matches = re.findall(email_pattern, str(content))
            if matches:
                return matches[0]
        
        return ""

    async def process(self, state: EnhancedChatState) -> EnhancedChatState:
        """Process the enhanced chat state to extract and update user profile information.

        Args:
            state: The current enhanced chat state

        Returns:
            The updated enhanced chat state with user profile information
        """
        try:
            # Extract unified profile and semantic context in single LLM call
            unified_extraction = await self.extract_unified_profile(
                messages=state.messages,
                products=state.referenced_products,
                search_queries=state.search_queries
            )
            
            # Also extract email using regex as backup
            if not unified_extraction.email:
                unified_extraction.email = self._extract_email_from_messages(state.messages)
                if unified_extraction.email:
                    logger.info(f"Extracted email via regex: {unified_extraction.email}")
            
            # Convert extraction result to profile updates
            profile_updates = {}
            
            # Basic profile fields
            if unified_extraction.name:
                profile_updates['name'] = unified_extraction.name
                logger.info(f"Extracted name: {unified_extraction.name}")
            if unified_extraction.email:
                profile_updates['email'] = unified_extraction.email
                logger.info(f"Extracted email: {unified_extraction.email}")
            if unified_extraction.age:
                try:
                    profile_updates['age'] = int(unified_extraction.age)
                    logger.info(f"Extracted age: {unified_extraction.age}")
                except ValueError:
                    logger.warning(f"Invalid age value: {unified_extraction.age}")
                    pass  # Skip if age is not a valid number
            if unified_extraction.location:
                profile_updates['location'] = unified_extraction.location
                logger.info(f"Extracted location: {unified_extraction.location}")
            
            # Health and medical information
            if unified_extraction.health_conditions:
                profile_updates['health_conditions'] = unified_extraction.health_conditions
                logger.info(f"Extracted health conditions: {unified_extraction.health_conditions}")
            if unified_extraction.dietary_restrictions:
                profile_updates['dietary_restrictions'] = unified_extraction.dietary_restrictions
                logger.info(f"Extracted dietary restrictions: {unified_extraction.dietary_restrictions}")
            if unified_extraction.medications:
                profile_updates['medications'] = unified_extraction.medications
                logger.info(f"Extracted medications: {unified_extraction.medications}")
            
            # Preferences and goals
            if unified_extraction.activity_preferences:
                profile_updates['activity_preferences'] = unified_extraction.activity_preferences
                logger.info(f"Extracted activity preferences: {unified_extraction.activity_preferences}")
            if unified_extraction.product_preferences:
                profile_updates['product_preferences'] = unified_extraction.product_preferences
                logger.info(f"Extracted product preferences: {unified_extraction.product_preferences}")
            if unified_extraction.budget_range:
                profile_updates['budget_range'] = unified_extraction.budget_range
                logger.info(f"Extracted budget range: {unified_extraction.budget_range}")
            if unified_extraction.fitness_goals:
                profile_updates['fitness_goals'] = unified_extraction.fitness_goals
                logger.info(f"Extracted fitness goals: {unified_extraction.fitness_goals}")
            if unified_extraction.adventure_plans:
                profile_updates['adventure_plans'] = unified_extraction.adventure_plans
                logger.info(f"Extracted adventure plans: {unified_extraction.adventure_plans}")
            
            # Experience and behavior
            if unified_extraction.experience_level:
                profile_updates['experience_level'] = unified_extraction.experience_level
                logger.info(f"Extracted experience level: {unified_extraction.experience_level}")
            if unified_extraction.frequency_of_use:
                profile_updates['frequency_of_use'] = unified_extraction.frequency_of_use
                logger.info(f"Extracted frequency of use: {unified_extraction.frequency_of_use}")
            
            # Constraints and limitations
            if unified_extraction.physical_limitations:
                profile_updates['physical_limitations'] = unified_extraction.physical_limitations
                logger.info(f"Extracted physical limitations: {unified_extraction.physical_limitations}")
            if unified_extraction.time_constraints:
                profile_updates['time_constraints'] = unified_extraction.time_constraints
                logger.info(f"Extracted time constraints: {unified_extraction.time_constraints}")
            
            # Social and practical information
            if unified_extraction.group_size:
                profile_updates['group_size'] = unified_extraction.group_size
                logger.info(f"Extracted group size: {unified_extraction.group_size}")
            if unified_extraction.family_considerations:
                profile_updates['family_considerations'] = unified_extraction.family_considerations
                logger.info(f"Extracted family considerations: {unified_extraction.family_considerations}")
            if unified_extraction.climate_conditions:
                profile_updates['climate_conditions'] = unified_extraction.climate_conditions
                logger.info(f"Extracted climate conditions: {unified_extraction.climate_conditions}")
            if unified_extraction.storage_limitations:
                profile_updates['storage_limitations'] = unified_extraction.storage_limitations
                logger.info(f"Extracted storage limitations: {unified_extraction.storage_limitations}")
            
            # Update the user profile if we found any information
            if profile_updates:
                state.update_user_profile(profile_updates)
                logger.info(f"Updated user profile with {len(profile_updates)} fields: {list(profile_updates.keys())}")
            
            # Update semantic context
            semantic_context = {
                "themes": unified_extraction.conversation_themes,
                "patterns": unified_extraction.interaction_patterns or {},
                "affinities": unified_extraction.product_affinities,
                "communication_style": unified_extraction.communication_style,
                "decision_factors": unified_extraction.decision_factors
            }
            
            if any(semantic_context.values()):
                state.update_semantic_context(semantic_context)
                logger.info(f"Updated semantic context with {len([k for k, v in semantic_context.items() if v])} fields")
            
            # Record conversation in memory if memory components are available
            if state.memory_manager and state.user_id:
                await state.record_conversation_memory(self.semantic_memory_service)
                state.mark_memory_consolidation_pending()
                logger.info(f"Recorded conversation memory for user {state.user_id}")
            
            return state

        except Exception as e:
            logger.error(f"Error in OptimizedUserProfileExtractionAgent.process: {e}")
            raise ServiceError(detail=f"Error extracting unified profile: {e}")
