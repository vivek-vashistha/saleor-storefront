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


class EnhancedUserProfileExtraction(BaseModel):
    """Enhanced user profile extraction with semantic context."""
    
    # Basic profile fields (same as original)
    name: str = Field(default="", description="User's name if mentioned")
    email: str = Field(default="", description="User's email if mentioned")
    age: str = Field(default="", description="User's age if mentioned")
    location: str = Field(default="", description="User's location if mentioned")
    health_conditions: List[str] = Field(default_factory=list, description="Health conditions mentioned")
    dietary_restrictions: List[str] = Field(default_factory=list, description="Dietary restrictions mentioned")
    medications: List[str] = Field(default_factory=list, description="Medications mentioned")
    activity_preferences: List[str] = Field(default_factory=list, description="Activity preferences mentioned")
    product_preferences: List[str] = Field(default_factory=list, description="Product preferences mentioned")
    budget_range: str = Field(default="", description="Budget range if mentioned")
    fitness_goals: List[str] = Field(default_factory=list, description="Fitness goals mentioned")
    adventure_plans: List[str] = Field(default_factory=list, description="Adventure plans mentioned")
    experience_level: str = Field(default="", description="Experience level if mentioned")
    frequency_of_use: str = Field(default="", description="Frequency of use if mentioned")
    physical_limitations: List[str] = Field(default_factory=list, description="Physical limitations mentioned")
    time_constraints: List[str] = Field(default_factory=list, description="Time constraints mentioned")
    group_size: str = Field(default="", description="Group size if mentioned")
    family_considerations: List[str] = Field(default_factory=list, description="Family considerations mentioned")
    climate_conditions: List[str] = Field(default_factory=list, description="Climate conditions mentioned")
    storage_limitations: List[str] = Field(default_factory=list, description="Storage limitations mentioned")
    
    # Enhanced semantic fields
    conversation_themes: List[str] = Field(default_factory=list, description="Recurring conversation themes")
    interaction_patterns: Optional[Dict[str, str]] = Field(default=None, description="User interaction patterns")
    product_affinities: List[str] = Field(default_factory=list, description="Product categories user shows affinity for")
    communication_style: str = Field(default="", description="User's communication style")
    decision_factors: List[str] = Field(default_factory=list, description="Key decision-making factors")


class EnhancedUserProfileExtractionAgent(IAgent[EnhancedChatState]):
    """Enhanced agent for extracting user profile information with semantic memory integration."""

    def __init__(self, llm, semantic_memory_service: SemanticMemoryService):
        """Initialize the EnhancedUserProfileExtractionAgent.

        Args:
            llm: The language model to use for extraction
            semantic_memory_service: Service for semantic memory operations
        """
        self.llm = llm
        self.semantic_memory_service = semantic_memory_service

    async def extract_user_profile(self, messages: List[Dict]) -> EnhancedUserProfileExtraction:
        """Extract enhanced user profile information from conversation messages.

        Args:
            messages: List of conversation messages

        Returns:
            Enhanced extracted user profile information
        """
        # Create a prompt for extracting user profile information
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are an expert at extracting comprehensive user profile information from conversations about outdoor gear and equipment.

Your task is to analyze the conversation and extract relevant user information in the following categories:

1. **Identity & Profile**: Name, email, age, location
2. **Health & Medical**: Health conditions, dietary restrictions, medications
3. **Preferences**: Activity preferences, product preferences, budget range
4. **Goals & Aspirations**: Fitness goals, adventure plans
5. **Behavior & Habits**: Experience level, frequency of use
6. **Constraints & Boundaries**: Physical limitations, time constraints
7. **Relationships & Social**: Group size, family considerations
8. **Practical Information**: Climate conditions, storage limitations
9. **Semantic Context**: Conversation themes, interaction patterns, communication style, decision factors

IMPORTANT GUIDELINES:
- Only extract information that is explicitly mentioned or clearly implied
- For health conditions, be thorough (e.g., "sugar problem" = diabetes, "sugar issue" = diabetes)
- For lists, separate items with commas
- If no information is found for a category, leave it empty
- Be conservative - only extract information you're confident about
- Pay special attention to health-related information as it's crucial for recommendations
- For semantic context, focus on patterns and themes that would be useful for future conversations

Return the information in a structured format that can be parsed."""
            ),
            (
                "human",
                "Please analyze this conversation and extract comprehensive user profile information:\n\n{conversation_text}"
            )
        ])

        # Convert messages to readable text
        conversation_text = self._format_messages_for_extraction(messages)
        
        try:
            chain = prompt | self.llm.with_structured_output(EnhancedUserProfileExtraction)
            extraction_result = await chain.ainvoke({"conversation_text": conversation_text})
            
            logger.info(f"Extracted enhanced user profile information: {extraction_result}")
            return extraction_result
            
        except Exception as e:
            logger.error(f"Error extracting enhanced user profile: {e}")
            return EnhancedUserProfileExtraction()

    async def extract_semantic_context(
        self,
        messages: List[Dict],
        products: List[Any],
        search_queries: List[Any]
    ) -> Dict[str, Any]:
        """Extract semantic context using the semantic memory service.

        Args:
            messages: List of conversation messages
            products: Products mentioned or recommended
            search_queries: Search queries made

        Returns:
            Dictionary containing semantic context
        """
        try:
            semantic_context = await self.semantic_memory_service.extract_semantic_context(
                messages=messages,
                products=products,
                search_queries=search_queries
            )
            
            logger.info(f"Extracted semantic context: {semantic_context}")
            return semantic_context
            
        except Exception as e:
            logger.error(f"Error extracting semantic context: {e}")
            return {}

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

    def _extract_email_from_messages(self, messages: List[Dict]) -> str:
        """Extract email addresses from messages using regex.

        Args:
            messages: List of conversation messages

        Returns:
            First email address found, or empty string
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        for msg in messages:
            if msg.get('type') == 'human':
                content = msg.get('content', '')
                if isinstance(content, str):
                    emails = re.findall(email_pattern, content)
                    if emails:
                        return emails[0]
        
        return ""

    async def process(self, state: EnhancedChatState) -> EnhancedChatState:
        """Process the enhanced chat state to extract and update user profile information.

        Args:
            state: The current enhanced chat state

        Returns:
            The updated enhanced chat state with user profile information
        """
        try:
            # Extract enhanced user profile information from conversation
            profile_extraction = await self.extract_user_profile(state.messages)
            
            # Also extract email using regex as backup
            if not profile_extraction.email:
                profile_extraction.email = self._extract_email_from_messages(state.messages)
                if profile_extraction.email:
                    logger.info(f"Extracted email via regex: {profile_extraction.email}")
            
            # Extract semantic context
            semantic_context = await self.extract_semantic_context(
                messages=state.messages,
                products=state.referenced_products,
                search_queries=state.search_queries
            )
            
            # Convert extraction result to profile updates
            profile_updates = {}
            
            # Basic profile fields
            if profile_extraction.name:
                profile_updates['name'] = profile_extraction.name
                logger.info(f"Extracted name: {profile_extraction.name}")
            if profile_extraction.email:
                profile_updates['email'] = profile_extraction.email
                logger.info(f"Extracted email: {profile_extraction.email}")
            if profile_extraction.age:
                try:
                    profile_updates['age'] = int(profile_extraction.age)
                    logger.info(f"Extracted age: {profile_extraction.age}")
                except ValueError:
                    logger.warning(f"Invalid age value: {profile_extraction.age}")
                    pass  # Skip if age is not a valid number
            if profile_extraction.location:
                profile_updates['location'] = profile_extraction.location
                logger.info(f"Extracted location: {profile_extraction.location}")
            
            # Health and medical information
            if profile_extraction.health_conditions:
                profile_updates['health_conditions'] = profile_extraction.health_conditions
                logger.info(f"Extracted health conditions: {profile_extraction.health_conditions}")
            if profile_extraction.dietary_restrictions:
                profile_updates['dietary_restrictions'] = profile_extraction.dietary_restrictions
                logger.info(f"Extracted dietary restrictions: {profile_extraction.dietary_restrictions}")
            if profile_extraction.medications:
                profile_updates['medications'] = profile_extraction.medications
                logger.info(f"Extracted medications: {profile_extraction.medications}")
            
            # Preferences and goals
            if profile_extraction.activity_preferences:
                profile_updates['activity_preferences'] = profile_extraction.activity_preferences
                logger.info(f"Extracted activity preferences: {profile_extraction.activity_preferences}")
            if profile_extraction.product_preferences:
                profile_updates['product_preferences'] = profile_extraction.product_preferences
                logger.info(f"Extracted product preferences: {profile_extraction.product_preferences}")
            if profile_extraction.budget_range:
                profile_updates['budget_range'] = profile_extraction.budget_range
                logger.info(f"Extracted budget range: {profile_extraction.budget_range}")
            if profile_extraction.fitness_goals:
                profile_updates['fitness_goals'] = profile_extraction.fitness_goals
                logger.info(f"Extracted fitness goals: {profile_extraction.fitness_goals}")
            if profile_extraction.adventure_plans:
                profile_updates['adventure_plans'] = profile_extraction.adventure_plans
                logger.info(f"Extracted adventure plans: {profile_extraction.adventure_plans}")
            
            # Experience and behavior
            if profile_extraction.experience_level:
                profile_updates['experience_level'] = profile_extraction.experience_level
                logger.info(f"Extracted experience level: {profile_extraction.experience_level}")
            if profile_extraction.frequency_of_use:
                profile_updates['frequency_of_use'] = profile_extraction.frequency_of_use
                logger.info(f"Extracted frequency of use: {profile_extraction.frequency_of_use}")
            
            # Constraints and limitations
            if profile_extraction.physical_limitations:
                profile_updates['physical_limitations'] = profile_extraction.physical_limitations
                logger.info(f"Extracted physical limitations: {profile_extraction.physical_limitations}")
            if profile_extraction.time_constraints:
                profile_updates['time_constraints'] = profile_extraction.time_constraints
                logger.info(f"Extracted time constraints: {profile_extraction.time_constraints}")
            
            # Social and practical information
            if profile_extraction.group_size:
                profile_updates['group_size'] = profile_extraction.group_size
                logger.info(f"Extracted group size: {profile_extraction.group_size}")
            if profile_extraction.family_considerations:
                profile_updates['family_considerations'] = profile_extraction.family_considerations
                logger.info(f"Extracted family considerations: {profile_extraction.family_considerations}")
            if profile_extraction.climate_conditions:
                profile_updates['climate_conditions'] = profile_extraction.climate_conditions
                logger.info(f"Extracted climate conditions: {profile_extraction.climate_conditions}")
            if profile_extraction.storage_limitations:
                profile_updates['storage_limitations'] = profile_extraction.storage_limitations
                logger.info(f"Extracted storage limitations: {profile_extraction.storage_limitations}")
            
            # Update the user profile if we found any information
            if profile_updates:
                state.update_user_profile(profile_updates)
                logger.info(f"Updated user profile with {len(profile_updates)} fields: {list(profile_updates.keys())}")
            
            # Update semantic context
            if semantic_context:
                state.update_semantic_context(semantic_context)
                logger.info(f"Updated semantic context with {len(semantic_context)} fields: {list(semantic_context.keys())}")
            
            # Record conversation in memory if memory components are available
            if state.memory_manager and state.user_id:
                await state.record_conversation_memory(self.semantic_memory_service)
                state.mark_memory_consolidation_pending()
                logger.info("Recorded conversation in semantic memory")
            
            if not profile_updates and not semantic_context:
                logger.info("No user profile information or semantic context extracted from conversation")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in EnhancedUserProfileExtractionAgent.process: {e}")
            raise ServiceError(detail=f"Error extracting enhanced user profile: {e}")


