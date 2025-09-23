from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel, Field, computed_field
from langgraph.store.memory import InMemoryStore

from backend.domain.entities.product import Product
from backend.domain.entities.product_bundle import ProductBundle
from backend.domain.entities.search_query import SearchQuery
from backend.domain.enums import AgentType
from backend.domain.entities.chat import UserProfile

logger = logging.getLogger("conversational_commerce.enhanced_chat")


class EnhancedUserProfile(UserProfile):
    """Enhanced user profile with Langmem integration."""
    
    # Additional fields for semantic memory
    conversation_themes: List[str] = Field(
        default_factory=list,
        description="Recurring themes and topics from conversations"
    )
    interaction_patterns: Optional[Dict[str, str]] = Field(
        default=None,
        description="Patterns in user interaction behavior"
    )
    product_affinities: List[str] = Field(
        default_factory=list,
        description="Product categories and brands user shows affinity for"
    )
    communication_style: Optional[str] = Field(
        default=None,
        description="User's preferred communication style"
    )
    decision_factors: List[str] = Field(
        default_factory=list,
        description="Key factors that influence user's purchasing decisions"
    )
    
    def update_semantic_context(self, context: Dict[str, Any]) -> None:
        """Update profile with semantic context from conversations."""
        if "themes" in context:
            self.conversation_themes.extend(context["themes"])
            self.conversation_themes = list(set(self.conversation_themes))  # Remove duplicates
        
        if "patterns" in context:
            if self.interaction_patterns is None:
                self.interaction_patterns = {}
            self.interaction_patterns.update(context["patterns"])
        
        if "affinities" in context:
            self.product_affinities.extend(context["affinities"])
            self.product_affinities = list(set(self.product_affinities))
        
        if "communication_style" in context:
            self.communication_style = context["communication_style"]
        
        if "decision_factors" in context:
            self.decision_factors.extend(context["decision_factors"])
            self.decision_factors = list(set(self.decision_factors))


class MemoryComponents:
    """Container for Langmem components that are not serialized."""
    
    def __init__(self):
        self.memory_store: Optional[InMemoryStore] = None
        self.memory_manager: Optional[Any] = None
        self.store_manager: Optional[Any] = None


class EnhancedChatState(BaseModel):
    """Enhanced chat state with Langmem integration for long-term memory."""
    
    model_config = {"arbitrary_types_allowed": True}
    
    # Core conversation state
    messages: List[Dict] = Field(
        default_factory=list,
        description="List of messages in the conversation",
    )
    search_queries: List[SearchQuery] = Field(
        default_factory=list,
        description="List of search queries with their product categories",
    )
    next_agent: AgentType | None = Field(
        default=None,
        description="The next agent to handle the conversation",
    )
    weather_info: Dict[str, Any] = Field(
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
    referenced_products: List[Product] = Field(
        default_factory=list,
        description="List of products explicitly referenced in the conversation",
    )
    
    # Enhanced user profile with semantic memory
    user_profile: EnhancedUserProfile = Field(
        default_factory=EnhancedUserProfile,
        description="Enhanced user profile with semantic memory integration",
    )
    
    # Memory components (not serialized)
    memory_components: Optional[MemoryComponents] = Field(
        default=None,
        description="Langmem components for long-term memory",
        exclude=True
    )
    
    # Memory metadata
    memory_last_updated: Optional[datetime] = Field(
        default=None,
        description="When the memory was last updated"
    )
    memory_consolidation_pending: bool = Field(
        default=False,
        description="Whether memory consolidation is pending"
    )
    
    @computed_field
    def has_search_query(self) -> bool:
        """Check if there are any search queries available."""
        return bool(self.search_queries)

    @computed_field
    def has_referenced_products(self) -> bool:
        """Check if there are any referenced products."""
        return bool(self.referenced_products)

    @computed_field
    def has_user_profile(self) -> bool:
        """Check if there is any user profile information available."""
        return (
            self.user_profile.name is not None or
            self.user_profile.email is not None or
            self.user_profile.health_conditions or
            self.user_profile.activity_preferences or
            self.user_profile.dietary_restrictions or
            self.user_profile.conversation_themes or
            self.user_profile.product_affinities
        )

    @computed_field
    def has_semantic_memory(self) -> bool:
        """Check if semantic memory has been populated."""
        if self.memory_components and self.memory_components.memory_store and self.user_id:
            try:
                memories = self.memory_components.memory_store.search(
                    ("conversations", self.user_id, "memories"),  # namespace as first positional argument
                    limit=1
                )
                return len(memories) > 0
            except:
                return False
        return False
    
    @property
    def memory_store(self) -> Optional[InMemoryStore]:
        """Get the memory store."""
        return self.memory_components.memory_store if self.memory_components else None
    
    @property
    def memory_manager(self) -> Optional[Any]:
        """Get the memory manager."""
        return self.memory_components.memory_manager if self.memory_components else None
    
    @classmethod
    def from_chat_state(cls, chat_state) -> "EnhancedChatState":
        """Convert a regular ChatState to EnhancedChatState.
        
        Args:
            chat_state: The original ChatState object
            
        Returns:
            EnhancedChatState with converted user profile
        """
        # Convert UserProfile to EnhancedUserProfile
        if hasattr(chat_state, 'user_profile') and chat_state.user_profile:
            enhanced_profile = EnhancedUserProfile(
                name=chat_state.user_profile.name,
                email=chat_state.user_profile.email,
                age=chat_state.user_profile.age,
                location=chat_state.user_profile.location,
                health_conditions=chat_state.user_profile.health_conditions,
                dietary_restrictions=chat_state.user_profile.dietary_restrictions,
                medications=chat_state.user_profile.medications,
                activity_preferences=chat_state.user_profile.activity_preferences,
                product_preferences=chat_state.user_profile.product_preferences,
                budget_range=chat_state.user_profile.budget_range,
                fitness_goals=chat_state.user_profile.fitness_goals,
                adventure_plans=chat_state.user_profile.adventure_plans,
                experience_level=chat_state.user_profile.experience_level,
                frequency_of_use=chat_state.user_profile.frequency_of_use,
                physical_limitations=chat_state.user_profile.physical_limitations,
                time_constraints=chat_state.user_profile.time_constraints,
                group_size=chat_state.user_profile.group_size,
                family_considerations=chat_state.user_profile.family_considerations,
                climate_conditions=chat_state.user_profile.climate_conditions,
                storage_limitations=chat_state.user_profile.storage_limitations,
                last_updated=chat_state.user_profile.last_updated,
                # Enhanced fields will be empty initially
                conversation_themes=[],
                interaction_patterns={},
                product_affinities=[],
                communication_style=None,
                decision_factors=[]
            )
        else:
            enhanced_profile = EnhancedUserProfile()
        
        # Create the enhanced state
        return cls(
            messages=chat_state.messages,
            search_queries=chat_state.search_queries,
            next_agent=chat_state.next_agent,
            weather_info=chat_state.weather_info,
            is_detail_sufficient=chat_state.is_detail_sufficient,
            is_conversation_saturated=chat_state.is_conversation_saturated,
            is_greeting=chat_state.is_greeting,
            user_id=chat_state.user_id,
            referenced_products=chat_state.referenced_products,
            user_profile=enhanced_profile,
            memory_components=None,
            memory_last_updated=None,
            memory_consolidation_pending=False
        )
    
    def set_memory_components(self, memory_components: MemoryComponents) -> None:
        """Set the memory components."""
        self.memory_components = memory_components
    
    def mark_memory_consolidation_pending(self) -> None:
        """Mark that memory consolidation is pending."""
        self.memory_consolidation_pending = True
    
    def clear_memory_consolidation_pending(self) -> None:
        """Clear the memory consolidation pending flag."""
        self.memory_consolidation_pending = False
    
    async def retrieve_relevant_memories(
        self, 
        query: str, 
        semantic_memory_service: Any,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for a query.
        
        Args:
            query: The query to search for
            semantic_memory_service: The semantic memory service
            limit: Maximum number of memories to return
            
        Returns:
            List of relevant memories
        """
        if not self.memory_store or not self.user_id:
            return []
        
        try:
            return await semantic_memory_service.retrieve_relevant_memories(
                user_id=self.user_id,
                query=query,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []
    
    async def record_conversation_memory(self, semantic_memory_service: Any) -> None:
        """Record the conversation in semantic memory.
        
        Args:
            semantic_memory_service: The semantic memory service
        """
        if not self.user_id or not self.messages:
            return
        
        try:
            # Extract context from the conversation
            context = {
                "search_queries": [q.model_dump() for q in self.search_queries],
                "referenced_products": [p.model_dump() for p in self.referenced_products],
                "user_profile": self.user_profile.model_dump() if self.user_profile else {}
            }
            
            await semantic_memory_service.record_conversation(
                user_id=self.user_id,
                messages=self.messages,
                context=context
            )
        except Exception as e:
            logger.error(f"Error recording conversation memory: {e}")
    
    @property
    def store_manager(self) -> Optional[Any]:
        """Get the store manager."""
        return self.memory_components.store_manager if self.memory_components else None

    def add_message(self, message_content: str, is_human: bool = True) -> None:
        """Add a message to the chat state."""
        message_class = HumanMessage if is_human else AIMessage
        self.messages.append(message_class(content=message_content).model_dump())

    def add_ai_message_with_products(self, products: List[Product]) -> None:
        """Add an AI message with product recommendations."""
        from backend.domain.entities.chat import ProductRecommendationMessage
        message = ProductRecommendationMessage(
            content="Here are some product recommendations for you:",
            recommended_products=products
        )
        self.messages.append(message.model_dump())

    def add_ai_message_with_product_bundles(self, bundles: List[ProductBundle]) -> None:
        """Add an AI message with product bundle recommendations."""
        from backend.domain.entities.chat import ProductBundleRecommendationMessage
        message = ProductBundleRecommendationMessage(
            content="Here are some product bundle recommendations for you:",
            recommended_bundles=bundles
        )
        self.messages.append(message.model_dump())

    def update_user_profile(self, profile_data: Dict[str, Any]) -> None:
        """Update the user profile with new information."""
        self.user_profile.update_profile(profile_data)
        self.memory_last_updated = datetime.now()

    def update_semantic_context(self, context: Dict[str, Any]) -> None:
        """Update semantic context in the user profile."""
        self.user_profile.update_semantic_context(context)
        self.memory_last_updated = datetime.now()

    def set_memory_components(self, memory_components: MemoryComponents) -> None:
        """Set the memory components."""
        self.memory_components = memory_components

    async def record_conversation_memory(self, semantic_memory_service) -> None:
        """Record conversation in semantic memory."""
        if self.memory_store and self.user_id:
            try:
                await semantic_memory_service.record_conversation(
                    user_id=self.user_id,
                    messages=self.messages,
                    context={
                        "products": [p.model_dump() for p in self.referenced_products],
                        "search_queries": [sq.model_dump() for sq in self.search_queries],
                        "user_profile": self.user_profile.model_dump()
                    }
                )
                self.memory_last_updated = datetime.now()
            except Exception as e:
                # Log error but don't fail the conversation
                print(f"Error recording conversation memory: {e}")

    async def retrieve_relevant_memories(self, query: str, semantic_memory_service) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for a given query."""
        if self.memory_store and self.user_id:
            try:
                memories = await semantic_memory_service.retrieve_relevant_memories(
                    user_id=self.user_id,
                    query=query,
                    limit=5
                )
                return memories
            except Exception as e:
                print(f"Error retrieving memories: {e}")
                return []
        return []

    def mark_memory_consolidation_pending(self) -> None:
        """Mark that memory consolidation is needed."""
        self.memory_consolidation_pending = True

    def clear_memory_consolidation_pending(self) -> None:
        """Clear the memory consolidation pending flag."""
        self.memory_consolidation_pending = False


