"""Specialized sub-agents for Deep Agent architecture."""

import logging
from typing import Any, Dict, List, Optional, TypedDict, Literal
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger("conversational_commerce.sub_agents")


class SubAgentConfig(TypedDict):
    """Configuration for a sub-agent following Deep Agents framework pattern."""
    name: str
    description: str
    prompt: str
    tools: List[str]
    model: Optional[str]
    middleware: Optional[List[str]]


class SubAgentState(TypedDict):
    """State schema for sub-agents."""
    user_id: str
    memories: List[Dict[str, Any]]
    context: Dict[str, Any]
    tools_used: List[str]
    confidence: float


class SubAgentResponse(BaseModel):
    """Response structure for sub-agents."""
    response: str = Field(description="The sub-agent's response")
    tools_used: List[str] = Field(description="Tools used by the sub-agent")
    confidence: float = Field(description="Confidence score")
    reasoning: str = Field(description="Reasoning behind the response")


class SubAgentRegistry:
    """Registry for managing sub-agents following Deep Agents framework pattern."""
    
    def __init__(self):
        self.sub_agents: Dict[str, SubAgentConfig] = {}
        self._register_default_sub_agents()
    
    def _register_default_sub_agents(self):
        """Register default sub-agents for conversational commerce."""
        self.sub_agents = {
            "product_expert": SubAgentConfig(
                name="product_expert",
                description="Specialized for product discovery, recommendations, and bundling for health & wellness products",
                prompt="""You are a product expert specializing in health & wellness products.
                Focus on: product recommendations, bundling, availability, pricing.
                Always consider user's health conditions and preferences.
                Use memory context to personalize recommendations.
                Provide detailed product information and create intelligent bundles when appropriate.""",
                tools=["search_products", "get_product_details", "create_bundles", "check_availability"],
                model=None,
                middleware=None
            ),
            "order_specialist": SubAgentConfig(
                name="order_specialist", 
                description="Handles order status, tracking, returns, and order-related inquiries",
                prompt="""You are an order specialist handling order status, tracking, and returns.
                Focus on: order lookup, shipment tracking, refund processing.
                Always verify user identity and order details.
                Use memory to provide personalized order assistance.
                Be helpful and provide clear order information.""",
                tools=["check_order_status", "track_shipment", "process_refund", "get_order_history"],
                model=None,
                middleware=None
            ),
            "health_advisor": SubAgentConfig(
                name="health_advisor",
                description="Provides health and wellness advice, supplement recommendations, and drug interaction checks",
                prompt="""You are a health advisor providing wellness guidance.
                Focus on: supplement advice, drug interactions, dosage recommendations.
                Always recommend consulting healthcare providers for medical advice.
                Use user's health history from memory for personalized advice.
                Be cautious and responsible with health recommendations.""",
                tools=["get_health_advice", "check_interactions", "dosage_advice", "wellness_recommendations"],
                model=None,
                middleware=None
            ),
            "memory_manager": SubAgentConfig(
                name="memory_manager",
                description="Manages user personalization, memory retrieval, and profile updates",
                prompt="""You are a memory manager responsible for user personalization.
                Focus on: retrieving relevant memories, storing new information,
                updating user profiles, consolidating memories.
                Always maintain user privacy and data accuracy.
                Use memories to provide personalized context.""",
                tools=["retrieve_memories", "store_memory", "update_user_profile", "consolidate_memories"],
                model=None,
                middleware=None
            )
        }
    
    def get_sub_agent_config(self, name: str) -> Optional[SubAgentConfig]:
        """Get configuration for a specific sub-agent."""
        return self.sub_agents.get(name)
    
    def get_available_sub_agents(self) -> List[str]:
        """Get list of available sub-agent names."""
        return list(self.sub_agents.keys())
    
    def get_sub_agent_descriptions(self) -> List[str]:
        """Get descriptions of all sub-agents for task delegation."""
        return [f"- {config['name']}: {config['description']}" for config in self.sub_agents.values()]


class ProductExpertSubAgent:
    """Specialized for product discovery and recommendations."""

    def __init__(self, llm: ChatOpenAI, product_tools):
        """Initialize the Product Expert sub-agent.

        Args:
            llm: Language model instance
            product_tools: Product tools for the sub-agent
        """
        self.llm = llm
        self.product_tools = product_tools
        self.instructions = """
        You are a product expert specializing in health & wellness products.
        Focus on: product recommendations, bundling, availability, pricing.
        Always consider user's health conditions and preferences.
        Use memory context to personalize recommendations.
        """

    async def process(
        self,
        user_message: str,
        user_id: str,
        memories: List[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> SubAgentResponse:
        """Process a product-related inquiry.

        Args:
            user_message: The user's message
            user_id: The user's ID
            memories: Retrieved memories
            intent: Intent analysis

        Returns:
            SubAgentResponse with product recommendations
        """
        try:
            logger.info(f"Product Expert processing: {user_message[:50]}...")
            
            # Create product expert prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.instructions),
                ("human", """
                User Message: {user_message}
                User Memories: {memories}
                Intent: {intent}
                
                Analyze the user's product needs and provide personalized recommendations.
                Consider their health conditions, preferences, and budget from memories.
                """)
            ])
            
            # Create the chain
            chain = prompt | self.llm
            
            # Generate response
            response = await chain.ainvoke({
                "user_message": user_message,
                "memories": memories,
                "intent": intent
            })
            
            # Extract response content
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            return SubAgentResponse(
                response=response_text,
                tools_used=["search_products", "get_product_details"],
                confidence=0.8,
                reasoning="Product expert analysis based on user needs and memories"
            )
            
        except Exception as e:
            logger.error(f"Error in Product Expert: {e}")
            return SubAgentResponse(
                response="I'm sorry, I had trouble processing your product request. Please try again.",
                tools_used=[],
                confidence=0.3,
                reasoning="Error occurred during product analysis"
            )


class OrderSpecialistSubAgent:
    """Specialized for order management."""

    def __init__(self, llm: ChatOpenAI, order_tools):
        """Initialize the Order Specialist sub-agent.

        Args:
            llm: Language model instance
            order_tools: Order tools for the sub-agent
        """
        self.llm = llm
        self.order_tools = order_tools
        self.instructions = """
        You are an order specialist handling order status, tracking, and returns.
        Focus on: order lookup, shipment tracking, refund processing.
        Always verify user identity and order details.
        Use memory to provide personalized order assistance.
        """

    async def process(
        self,
        user_message: str,
        user_id: str,
        memories: List[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> SubAgentResponse:
        """Process an order-related inquiry.

        Args:
            user_message: The user's message
            user_id: The user's ID
            memories: Retrieved memories
            intent: Intent analysis

        Returns:
            SubAgentResponse with order information
        """
        try:
            logger.info(f"Order Specialist processing: {user_message[:50]}...")
            
            # Create order specialist prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.instructions),
                ("human", """
                User Message: {user_message}
                User Memories: {memories}
                Intent: {intent}
                
                Help the user with their order inquiry. Check order status, tracking, or process returns as needed.
                Use any email information from memories or previous conversations.
                """)
            ])
            
            # Create the chain
            chain = prompt | self.llm
            
            # Generate response
            response = await chain.ainvoke({
                "user_message": user_message,
                "memories": memories,
                "intent": intent
            })
            
            # Extract response content
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            return SubAgentResponse(
                response=response_text,
                tools_used=["check_order_status", "track_shipment"],
                confidence=0.8,
                reasoning="Order specialist analysis based on user inquiry"
            )
            
        except Exception as e:
            logger.error(f"Error in Order Specialist: {e}")
            return SubAgentResponse(
                response="I'm sorry, I had trouble processing your order request. Please try again.",
                tools_used=[],
                confidence=0.3,
                reasoning="Error occurred during order analysis"
            )


class HealthAdvisorSubAgent:
    """Specialized for health and wellness advice."""

    def __init__(self, llm: ChatOpenAI, health_tools):
        """Initialize the Health Advisor sub-agent.

        Args:
            llm: Language model instance
            health_tools: Health tools for the sub-agent
        """
        self.llm = llm
        self.health_tools = health_tools
        self.instructions = """
        You are a health advisor providing wellness guidance.
        Focus on: supplement advice, drug interactions, dosage recommendations.
        Always recommend consulting healthcare providers for medical advice.
        Use user's health history from memory for personalized advice.
        """

    async def process(
        self,
        user_message: str,
        user_id: str,
        memories: List[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> SubAgentResponse:
        """Process a health-related inquiry.

        Args:
            user_message: The user's message
            user_id: The user's ID
            memories: Retrieved memories
            intent: Intent analysis

        Returns:
            SubAgentResponse with health advice
        """
        try:
            logger.info(f"Health Advisor processing: {user_message[:50]}...")
            
            # Create health advisor prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.instructions),
                ("human", """
                User Message: {user_message}
                User Memories: {memories}
                Intent: {intent}
                
                Provide helpful health and wellness advice based on the user's inquiry.
                Consider their health conditions and medications from memories.
                Always recommend consulting healthcare providers for medical advice.
                """)
            ])
            
            # Create the chain
            chain = prompt | self.llm
            
            # Generate response
            response = await chain.ainvoke({
                "user_message": user_message,
                "memories": memories,
                "intent": intent
            })
            
            # Extract response content
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            return SubAgentResponse(
                response=response_text,
                tools_used=["get_health_advice", "check_interactions"],
                confidence=0.8,
                reasoning="Health advisor analysis based on user inquiry and health history"
            )
            
        except Exception as e:
            logger.error(f"Error in Health Advisor: {e}")
            return SubAgentResponse(
                response="I'm sorry, I had trouble processing your health inquiry. Please try again.",
                tools_used=[],
                confidence=0.3,
                reasoning="Error occurred during health analysis"
            )


class MemoryManagerSubAgent:
    """Specialized for memory management."""

    def __init__(self, llm: ChatOpenAI, memory_tools):
        """Initialize the Memory Manager sub-agent.

        Args:
            llm: Language model instance
            memory_tools: Memory tools for the sub-agent
        """
        self.llm = llm
        self.memory_tools = memory_tools
        self.instructions = """
        You are a memory manager responsible for user personalization.
        Focus on: retrieving relevant memories, storing new information,
        updating user profiles, consolidating memories.
        Always maintain user privacy and data accuracy.
        """

    async def process(
        self,
        user_message: str,
        user_id: str,
        memories: List[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> SubAgentResponse:
        """Process a memory-related inquiry.

        Args:
            user_message: The user's message
            user_id: The user's ID
            memories: Retrieved memories
            intent: Intent analysis

        Returns:
            SubAgentResponse with memory-based context
        """
        try:
            logger.info(f"Memory Manager processing: {user_message[:50]}...")
            
            # Create memory manager prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.instructions),
                ("human", """
                User Message: {user_message}
                User Memories: {memories}
                Intent: {intent}
                
                Use the retrieved memories to provide personalized context and assistance.
                Store any new relevant information from the conversation.
                """)
            ])
            
            # Create the chain
            chain = prompt | self.llm
            
            # Generate response
            response = await chain.ainvoke({
                "user_message": user_message,
                "memories": memories,
                "intent": intent
            })
            
            # Extract response content
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            return SubAgentResponse(
                response=response_text,
                tools_used=["retrieve_memories", "store_memory"],
                confidence=0.8,
                reasoning="Memory manager analysis based on user context and memories"
            )
            
        except Exception as e:
            logger.error(f"Error in Memory Manager: {e}")
            return SubAgentResponse(
                response="I'm sorry, I had trouble processing your request. Please try again.",
                tools_used=[],
                confidence=0.3,
                reasoning="Error occurred during memory analysis"
            )
