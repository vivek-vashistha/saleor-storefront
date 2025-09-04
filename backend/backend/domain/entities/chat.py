from typing import Any, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel, Field, computed_field

from backend.domain.entities.product import Product
from backend.domain.entities.product_bundle import ProductBundle
from backend.domain.entities.search_query import SearchQuery
from backend.domain.enums import AgentType


class UserProfile(BaseModel):
    """Represents user profile information extracted from conversations."""
    
    # Identity & Profile
    name: Optional[str] = Field(default=None, description="User's name")
    email: Optional[str] = Field(default=None, description="User's email address")
    age: Optional[int] = Field(default=None, description="User's age")
    location: Optional[str] = Field(default=None, description="User's location")
    
    # Health & Medical Information
    health_conditions: List[str] = Field(default_factory=list, description="Health conditions like diabetes, allergies, etc.")
    dietary_restrictions: List[str] = Field(default_factory=list, description="Dietary restrictions or preferences")
    medications: List[str] = Field(default_factory=list, description="Current medications")
    
    # Preferences
    activity_preferences: List[str] = Field(default_factory=list, description="Preferred outdoor activities")
    product_preferences: List[str] = Field(default_factory=list, description="Product preferences like brands, materials, etc.")
    budget_range: Optional[str] = Field(default=None, description="Budget range for purchases")
    
    # Goals & Aspirations
    fitness_goals: List[str] = Field(default_factory=list, description="Fitness or activity goals")
    adventure_plans: List[str] = Field(default_factory=list, description="Planned adventures or trips")
    
    # Behavior & Habits
    experience_level: Optional[str] = Field(default=None, description="Experience level in outdoor activities")
    frequency_of_use: Optional[str] = Field(default=None, description="How often they use outdoor gear")
    
    # Constraints & Boundaries
    physical_limitations: List[str] = Field(default_factory=list, description="Physical limitations or disabilities")
    time_constraints: List[str] = Field(default_factory=list, description="Time-related constraints")
    
    # Relationships & Social
    group_size: Optional[str] = Field(default=None, description="Typical group size for activities")
    family_considerations: List[str] = Field(default_factory=list, description="Family-related considerations")
    
    # Practical Information
    climate_conditions: List[str] = Field(default_factory=list, description="Typical climate conditions they face")
    storage_limitations: List[str] = Field(default_factory=list, description="Storage or space limitations")
    
    # Metadata
    last_updated: Optional[str] = Field(default=None, description="When the profile was last updated")
    
    def update_profile(self, new_info: dict[str, Any]) -> None:
        """Update profile with new information."""
        for key, value in new_info.items():
            if hasattr(self, key):
                if isinstance(value, list) and isinstance(getattr(self, key), list):
                    # Merge lists, avoiding duplicates
                    current_list = getattr(self, key)
                    if isinstance(value[0], str):
                        # For string lists, merge and deduplicate
                        current_list.extend(value)
                        setattr(self, key, list(set(current_list)))
                    else:
                        # For other types, just extend
                        current_list.extend(value)
                else:
                    setattr(self, key, value)
        
        from datetime import datetime
        self.last_updated = datetime.now().isoformat()
    
    def get_relevant_context(self, query_type: str = "general") -> str:
        """Get relevant context based on query type.

        If query_type == 'general', include a broad summary of key profile fields
        so downstream agents always receive useful context.
        """
        context_parts = []

        if query_type == "general":
            # Identity (non-sensitive display)
            if self.name:
                context_parts.append(f"Name: {self.name}")
            if self.email:
                context_parts.append(f"Email: {self.email}")

            # Health & dietary
            if self.health_conditions:
                context_parts.append(f"Health conditions: {', '.join(self.health_conditions)}")
            if self.dietary_restrictions:
                context_parts.append(f"Dietary restrictions: {', '.join(self.dietary_restrictions)}")

            # Activities & habits
            if self.activity_preferences:
                context_parts.append(f"Preferred activities: {', '.join(self.activity_preferences)}")
            if self.experience_level:
                context_parts.append(f"Experience level: {self.experience_level}")
            if self.climate_conditions:
                context_parts.append(f"Climate conditions: {', '.join(self.climate_conditions)}")

            # Product preferences & budget
            if self.product_preferences:
                context_parts.append(f"Product preferences: {', '.join(self.product_preferences)}")
            if self.budget_range:
                context_parts.append(f"Budget range: {self.budget_range}")

            return "; ".join(context_parts)

        # Category-specific contexts
        
        if query_type in ["health", "dietary", "medical"]:
            if self.health_conditions:
                context_parts.append(f"Health conditions: {', '.join(self.health_conditions)}")
            if self.dietary_restrictions:
                context_parts.append(f"Dietary restrictions: {', '.join(self.dietary_restrictions)}")
            if self.medications:
                context_parts.append(f"Medications: {', '.join(self.medications)}")
        
        if query_type in ["activity", "gear", "equipment"]:
            if self.activity_preferences:
                context_parts.append(f"Preferred activities: {', '.join(self.activity_preferences)}")
            if self.experience_level:
                context_parts.append(f"Experience level: {self.experience_level}")
            if self.climate_conditions:
                context_parts.append(f"Climate conditions: {', '.join(self.climate_conditions)}")
        
        if query_type in ["preferences", "recommendations"]:
            if self.product_preferences:
                context_parts.append(f"Product preferences: {', '.join(self.product_preferences)}")
            if self.budget_range:
                context_parts.append(f"Budget range: {self.budget_range}")
        
        return "; ".join(context_parts) if context_parts else ""


class ProductRecommendationMessage(BaseMessage):
    """A message that contains product recommendations."""

    content: str
    recommended_products: list[Product] = Field(default_factory=list)
    type: str = "product_recommendation"


class ProductBundleRecommendationMessage(BaseMessage):
    """A message that contains product bundle recommendations."""

    content: str
    recommended_bundles: list[ProductBundle] = Field(default_factory=list)
    type: str = "product_bundle_recommendation"


class ChatState(BaseModel):
    """Represents the state of an agent in the conversation flow."""

    messages: list[dict] = Field(
        default_factory=list,
        description="List of messages in the conversation",
    )
    search_queries: list[SearchQuery] = Field(
        default_factory=list,
        description="List of search queries with their product categories",
    )
    next_agent: AgentType | None = Field(
        default=None,
        description="The next agent to handle the conversation",
    )
    weather_info: dict[str, Any] = Field(
        default_factory=dict,
        description="Weather information relevant to the conversation",
    )
    is_detail_sufficient: bool = Field(
        default=False,
        description="Whether the conversation has sufficient detail",
    )
    is_conversation_saturated: bool = Field(
        default=False,
        description="Whether the conversation is saturated with enough detail",
    )
    is_greeting: bool = Field(
        default=False,
        description="Whether the last message was a greeting",
    )
    user_id: str | None = Field(
        default=None,
        description="ID of the user in the conversation",
    )
    referenced_products: list[Product] = Field(
        default_factory=list,
        description="List of products explicitly referenced in the conversation",
    )
    user_profile: UserProfile = Field(
        default_factory=UserProfile,
        description="User profile information extracted from conversations",
    )

    @computed_field
    def has_search_query(self) -> bool:
        """Check if there are any search queries available.

        Returns:
            True if there are search queries, False otherwise
        """
        return bool(self.search_queries)

    @computed_field
    def has_referenced_products(self) -> bool:
        """Check if there are any referenced products available.

        Returns:
            True if there are referenced products, False otherwise
        """
        return bool(self.referenced_products)

    @computed_field
    def has_user_profile(self) -> bool:
        """Check if there is any user profile information available.

        Returns:
            True if there is user profile information, False otherwise
        """
        return (
            self.user_profile.name is not None or
            self.user_profile.email is not None or
            self.user_profile.health_conditions or
            self.user_profile.activity_preferences or
            self.user_profile.dietary_restrictions
        )

    def add_message(self, message_content: str, is_human: bool = True) -> None:
        """Add a message to the chat state.

        Args:
            message_content: The content of the message
            is_human: Whether the message is from the human (True) or AI (False)
        """
        message_class = HumanMessage if is_human else AIMessage
        self.messages.append(message_class(content=message_content).model_dump())

    def add_ai_message_with_products(self, products: list[Product]) -> None:
        """Add an AI message with product recommendations.

        Args:
            products: List of products to recommend with this message
        """
        message = ProductRecommendationMessage(
            content="Here are some product recommendations for you:", recommended_products=products
        )
        self.messages.append(message.model_dump())

    def add_ai_message_with_product_bundles(self, bundles: list[ProductBundle]) -> None:
        """Add an AI message with product bundle recommendations.

        Args:
            bundles: List of product bundles to recommend with this message
        """
        # Create a message that contains the product bundles
        message = ProductBundleRecommendationMessage(
            content="Here are some product bundles based on your needs:", recommended_bundles=bundles
        )
        self.messages.append(message.model_dump())

    def update_user_profile(self, profile_updates: dict[str, Any]) -> None:
        """Update the user profile with new information.

        Args:
            profile_updates: Dictionary containing profile updates
        """
        self.user_profile.update_profile(profile_updates)
