import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from langmem import create_memory_manager, create_memory_store_manager
from langgraph.store.memory import InMemoryStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field

from backend.domain.entities.enhanced_chat import EnhancedChatState, EnhancedUserProfile
from backend.domain.entities.product import Product

logger = logging.getLogger("conversational_commerce.semantic_memory")


class UserPreference(BaseModel):
    """Schema for user preferences and interests."""
    subject: str = Field(description="The user or entity")
    preference: str = Field(description="The preference or interest")
    context: str = Field(description="Context for the preference")
    confidence: float = Field(default=1.0, description="Confidence in this preference")


class ProductInteraction(BaseModel):
    """Schema for product interactions and feedback."""
    user: str = Field(description="The user")
    product: str = Field(description="The product or product category")
    interaction_type: str = Field(description="Type of interaction (viewed, liked, purchased, etc.)")
    feedback: str = Field(description="User feedback or sentiment")
    context: str = Field(description="Context of the interaction")


class ConversationTheme(BaseModel):
    """Schema for conversation themes and topics."""
    theme: str = Field(description="The main theme or topic")
    sentiment: str = Field(description="Overall sentiment (positive, negative, neutral)")
    importance: str = Field(description="Importance level (high, medium, low)")
    context: str = Field(description="Context and details")


class SemanticMemoryConfig(BaseModel):
    """Configuration for semantic memory service."""
    
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"
    memory_retention_days: int = 90
    max_memories_per_user: int = 1000
    consolidation_threshold: int = 10  # Number of conversations before consolidation
    
    @classmethod
    def from_ai_settings(cls, ai_settings) -> "SemanticMemoryConfig":
        """Create SemanticMemoryConfig from AISettings.
        
        Args:
            ai_settings: AISettings instance or configuration dict
            
        Returns:
            SemanticMemoryConfig instance
        """
        # Handle both AISettings object and configuration dict
        if hasattr(ai_settings, 'OPENAI_API_KEY'):
            openai_api_key = ai_settings.OPENAI_API_KEY
        else:
            # If it's a configuration dict, access the OPENAI_API_KEY directly
            openai_api_key = ai_settings['OPENAI_API_KEY']
        
        return cls(
            openai_api_key=openai_api_key,
            embedding_model="text-embedding-3-small",
            llm_model="gpt-4o-mini"
        )


class SemanticMemoryService:
    """Service for managing semantic memory using Langmem."""
    
    def __init__(self, config: SemanticMemoryConfig):
        """Initialize the semantic memory service.
        
        Args:
            config: Configuration for the semantic memory service
        """
        self.config = config
        self.llm = ChatOpenAI(
            model=config.llm_model,
            api_key=config.openai_api_key,
            temperature=0.1
        )
        self.embeddings = OpenAIEmbeddings(
            model=config.embedding_model,
            api_key=config.openai_api_key
        )
        
        # Create memory store
        self.store = InMemoryStore(
            index={
                "dims": 1536,  # OpenAI embedding dimension
                "embed": self.embeddings,
            }
        )
        
        # Create memory manager for extraction
        self.memory_manager = create_memory_manager(
            self.llm,
            schemas=[UserPreference, ProductInteraction, ConversationTheme],
            instructions="Extract user preferences, product interactions, and conversation themes from conversations about outdoor gear and equipment. Focus on information that would be useful for future product recommendations and personalized interactions.",
            enable_inserts=True,
            enable_deletes=True,
        )
        
        # Create memory store manager for storage operations
        self.store_manager = create_memory_store_manager(
            self.llm,
            schemas=[UserPreference, ProductInteraction, ConversationTheme],
            instructions="Extract and manage user preferences, product interactions, and conversation themes for outdoor gear recommendations. Focus on information that would be useful for future product recommendations and personalized interactions.",
            enable_inserts=True,
            enable_deletes=True,
            namespace=("conversations", "{langgraph_user_id}", "memories"),
            store=self.store
        )
        
    async def initialize_user_memory(self, user_id: str) -> Dict[str, Any]:
        """Initialize memory components for a new user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary containing initialized memory components
        """
        try:
            # The store and managers are already initialized
            # We just need to return the components for this user
            logger.info(f"[SEMANTIC_MEMORY] Initialized memory for user {user_id}")
            
            return {
                "store": self.store,
                "memory_manager": self.memory_manager,
                "store_manager": self.store_manager,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"[SEMANTIC_MEMORY] Error initializing memory for user {user_id}: {e}")
            raise
    
    async def record_conversation(
        self,
        user_id: str,
        messages: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> None:
        """Record a conversation in semantic memory.
        
        Args:
            user_id: The user's ID
            messages: List of conversation messages
            context: Additional context (products, search queries, etc.)
        """
        try:
            # Convert messages to the format expected by Langmem
            formatted_messages = self._format_messages_for_langmem(messages)
            
            # Use the store_manager to handle memory extraction and storage automatically
            # The store_manager will automatically search for relevant memories, extract new ones,
            # and store them in the configured store
            await self.store_manager.ainvoke({
                "messages": formatted_messages
            }, config={"configurable": {"langgraph_user_id": user_id}})
            
            logger.info(f"[SEMANTIC_MEMORY] Recorded memories for user {user_id} using store_manager")
                
        except Exception as e:
            logger.error(f"[SEMANTIC_MEMORY] Error recording conversation for user {user_id}: {e}")
    
    def _format_messages_for_langmem(self, messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format messages for Langmem processing.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Formatted messages for Langmem
        """
        formatted = []
        for msg in messages:
            msg_type = msg.get('type', 'human')
            content = msg.get('content', '')
            
            if isinstance(content, list):
                content = ' '.join(str(item) for item in content)
            
            role = "user" if msg_type == "human" else "assistant"
            formatted.append({"role": role, "content": str(content)})
        
        return formatted
    
    async def extract_semantic_context(
        self,
        messages: List[Dict[str, Any]],
        products: List[Product],
        search_queries: List[Any]
    ) -> Dict[str, Any]:
        """Extract semantic context from conversation.
        
        Args:
            messages: List of conversation messages
            products: Products mentioned or recommended
            search_queries: Search queries made
            
        Returns:
            Dictionary containing extracted semantic context
        """
        try:
            # Format conversation for analysis
            conversation_text = self._format_conversation_for_analysis(messages)
            
            # Extract themes and patterns
            themes = await self._extract_conversation_themes(conversation_text)
            patterns = await self._extract_interaction_patterns(conversation_text)
            affinities = await self._extract_product_affinities(products, search_queries)
            communication_style = await self._analyze_communication_style(conversation_text)
            decision_factors = await self._extract_decision_factors(conversation_text)
            
            return {
                "themes": themes,
                "patterns": patterns,
                "affinities": affinities,
                "communication_style": communication_style,
                "decision_factors": decision_factors
            }
            
        except Exception as e:
            logger.error(f"[SEMANTIC_MEMORY] Error extracting semantic context: {e}")
            return {}
    
    async def retrieve_relevant_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for a query.
        
        Args:
            user_id: The user's ID
            query: The query to search for
            limit: Maximum number of memories to return
            
        Returns:
            List of relevant memories
        """
        try:
            # Search memories in the store
            # Use the store_manager to search for memories
            memories = self.store_manager.search(
                query=query,
                config={"configurable": {"langgraph_user_id": user_id}}
            )
            
            # Convert to dictionary format
            memory_list = []
            for memory in memories:
                memory_list.append({
                    "id": memory.key,
                    "content": memory.value,
                    "created_at": memory.created_at,
                    "updated_at": memory.updated_at,
                    "score": memory.score
                })
            
            logger.info(f"[SEMANTIC_MEMORY] Retrieved {len(memory_list)} relevant memories for user {user_id}")
            return memory_list
            
        except Exception as e:
            logger.error(f"[SEMANTIC_MEMORY] Error retrieving memories for user {user_id}: {e}")
            return []
    
    async def consolidate_memories(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Consolidate and summarize user memories.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary containing consolidated memory insights
        """
        try:
            # Get all memories for the user
            all_memories = self.store.search(
                ("conversations", user_id, "memories"),  # namespace as first positional argument
                limit=1000
            )
            
            if len(all_memories) < self.config.consolidation_threshold:
                return {"status": "insufficient_memories", "count": len(all_memories)}
            
            # Consolidate memories
            consolidated = await self._consolidate_memory_patterns(all_memories)
            
            logger.info(f"[SEMANTIC_MEMORY] Consolidated memories for user {user_id}")
            return consolidated
            
        except Exception as e:
            logger.error(f"[SEMANTIC_MEMORY] Error consolidating memories for user {user_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _extract_conversation_summary(
        self,
        messages: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """Extract a summary of the conversation for memory storage."""
        from langchain_core.prompts import ChatPromptTemplate
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Extract key information from this conversation for long-term memory.
            
Focus on:
1. User preferences and interests
2. Product interactions and feedback
3. Decision-making patterns
4. Important context for future conversations

Keep the summary concise but comprehensive."""),
            ("human", "Conversation:\n{conversation}\n\nContext: {context}")
        ])
        
        conversation_text = self._format_conversation_for_analysis(messages)
        context_text = str(context)
        
        chain = prompt | self.llm
        result = await chain.ainvoke({
            "conversation": conversation_text,
            "context": context_text
        })
        
        return result.content
    
    def _format_conversation_for_analysis(self, messages: List[Dict[str, Any]]) -> str:
        """Format conversation messages for analysis."""
        formatted = []
        for msg in messages:
            msg_type = msg.get('type', 'human')
            content = msg.get('content', '')
            
            if isinstance(content, list):
                content = ' '.join(str(item) for item in content)
            
            speaker = "User" if msg_type == "human" else "Assistant"
            formatted.append(f"{speaker}: {content}")
        
        return "\n".join(formatted)
    
    async def _extract_conversation_themes(self, conversation_text: str) -> List[str]:
        """Extract recurring themes from conversation."""
        from langchain_core.prompts import ChatPromptTemplate
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Identify the main themes and topics discussed in this conversation.
            Return a list of 3-5 key themes. Focus on user interests, preferences, and recurring topics."""),
            ("human", "Conversation:\n{conversation}")
        ])
        
        chain = prompt | self.llm
        result = await chain.ainvoke({"conversation": conversation_text})
        
        # Parse themes from response
        themes = []
        for line in result.content.split('\n'):
            if line.strip() and not line.startswith('#'):
                themes.append(line.strip('- ').strip())
        
        return themes[:5]  # Limit to 5 themes
    
    async def _extract_interaction_patterns(self, conversation_text: str) -> Dict[str, Any]:
        """Extract interaction patterns from conversation."""
        from langchain_core.prompts import ChatPromptTemplate
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Analyze the user's interaction patterns in this conversation.
            Identify patterns like:
            - Question style (detailed vs brief)
            - Decision-making approach
            - Communication preferences
            - Information-seeking behavior
            
            Return a JSON object with these patterns."""),
            ("human", "Conversation:\n{conversation}")
        ])
        
        chain = prompt | self.llm
        result = await chain.ainvoke({"conversation": conversation_text})
        
        try:
            import json
            return json.loads(result.content)
        except:
            return {"patterns": "Unable to parse"}
    
    async def _extract_product_affinities(self, products: List[Product], search_queries: List[Any]) -> List[str]:
        """Extract product affinities from products and search queries."""
        affinities = []
        
        # Extract from products
        for product in products:
            if hasattr(product, 'category') and product.category:
                affinities.append(product.category)
            if hasattr(product, 'brand') and product.brand:
                affinities.append(product.brand)
        
        # Extract from search queries
        for query in search_queries:
            if hasattr(query, 'categories') and query.categories:
                affinities.extend(query.categories)
        
        return list(set(affinities))  # Remove duplicates
    
    async def _analyze_communication_style(self, conversation_text: str) -> str:
        """Analyze user's communication style."""
        from langchain_core.prompts import ChatPromptTemplate
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Analyze the user's communication style from this conversation.
            Identify if they are:
            - Direct vs indirect
            - Detailed vs concise
            - Formal vs casual
            - Technical vs simple
            
            Return a brief description of their communication style."""),
            ("human", "Conversation:\n{conversation}")
        ])
        
        chain = prompt | self.llm
        result = await chain.ainvoke({"conversation": conversation_text})
        
        return result.content.strip()
    
    async def _extract_decision_factors(self, conversation_text: str) -> List[str]:
        """Extract factors that influence user's decision-making."""
        from langchain_core.prompts import ChatPromptTemplate
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Identify the key factors that influence the user's decision-making in this conversation.
            Look for mentions of:
            - Price/budget considerations
            - Quality requirements
            - Brand preferences
            - Specific features or requirements
            - Use cases or scenarios
            
            Return a list of 3-5 key decision factors."""),
            ("human", "Conversation:\n{conversation}")
        ])
        
        chain = prompt | self.llm
        result = await chain.ainvoke({"conversation": conversation_text})
        
        factors = []
        for line in result.content.split('\n'):
            if line.strip() and not line.startswith('#'):
                factors.append(line.strip('- ').strip())
        
        return factors[:5]  # Limit to 5 factors
    
    async def _consolidate_memory_patterns(self, memories: List[Any]) -> Dict[str, Any]:
        """Consolidate patterns across multiple memories."""
        from langchain_core.prompts import ChatPromptTemplate
        
        # Combine all memory content
        all_content = "\n\n".join([str(mem.value) for mem in memories])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Analyze these user memories to identify long-term patterns and preferences.
            
            Extract:
            1. Recurring themes and interests
            2. Consistent preferences
            3. Decision-making patterns
            4. Communication style evolution
            5. Product interaction patterns
            
            Return a JSON object with these consolidated insights."""),
            ("human", "Memories:\n{memories}")
        ])
        
        chain = prompt | self.llm
        result = await chain.ainvoke({"memories": all_content})
        
        try:
            import json
            return json.loads(result.content)
        except:
            return {"consolidated_patterns": "Unable to parse"}
