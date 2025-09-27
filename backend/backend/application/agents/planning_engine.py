"""Advanced planning engine for Deep Agents."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from backend.application.services.hybrid_memory_service import HybridMemoryService

logger = logging.getLogger("conversational_commerce.planning_engine")


class IntentAnalysis(BaseModel):
    """Intent analysis structure."""
    intent_type: str = Field(description="Type of intent (product_inquiry, order_inquiry, health_advice, general)")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    entities: List[str] = Field(description="Extracted entities from the message")
    urgency: str = Field(description="Urgency level (low, medium, high)")
    complexity: str = Field(description="Complexity level (simple, moderate, complex)")


class ExecutionPlan(BaseModel):
    """Execution plan structure."""
    steps: List[Dict[str, Any]] = Field(description="List of execution steps")
    sub_agents_needed: List[str] = Field(description="List of sub-agents needed")
    tools_needed: List[str] = Field(description="List of tools needed")
    estimated_time: int = Field(description="Estimated execution time in seconds")
    priority: str = Field(description="Priority level (low, medium, high)")


class PlanningEngine:
    """Advanced planning engine for Deep Agents."""

    def __init__(self, llm: ChatOpenAI, memory_service: HybridMemoryService):
        """Initialize the planning engine.

        Args:
            llm: Language model instance
            memory_service: Memory service for context
        """
        self.llm = llm
        self.memory_service = memory_service

    async def create_execution_plan(
        self,
        user_message: str,
        user_id: str,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create execution plan based on user intent and context.

        Args:
            user_message: The user's message
            user_id: The user's ID
            conversation_history: Previous conversation messages

        Returns:
            Dictionary with execution plan and context
        """
        try:
            logger.info(f"Creating execution plan for user {user_id}: {user_message[:50]}...")
            
            # Step 1: Retrieve relevant memories
            memories = await self._retrieve_relevant_memories(user_id, user_message)
            
            # Step 2: Analyze intent and context
            intent_analysis = await self._analyze_intent(user_message, memories, conversation_history)
            
            # Step 3: Create execution plan
            execution_plan = await self._create_plan(intent_analysis, memories, conversation_history)
            
            logger.info(f"Created execution plan for user {user_id}: {intent_analysis.intent_type}")
            
            return {
                "plan": execution_plan,
                "memories": memories,
                "intent": intent_analysis,
                "user_id": user_id,
                "message": user_message
            }
            
        except Exception as e:
            logger.error(f"Error creating execution plan for user {user_id}: {e}")
            return {
                "plan": ExecutionPlan(
                    steps=[{"action": "general_response", "description": "Provide general assistance"}],
                    sub_agents_needed=["memory_manager"],
                    tools_needed=["retrieve_memories"],
                    estimated_time=30,
                    priority="medium"
                ),
                "memories": [],
                "intent": IntentAnalysis(
                    intent_type="general",
                    confidence=0.5,
                    entities=[],
                    urgency="low",
                    complexity="simple"
                ),
                "user_id": user_id,
                "message": user_message,
                "error": str(e)
            }

    async def _retrieve_relevant_memories(
        self,
        user_id: str,
        user_message: str
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for the user.

        Args:
            user_id: The user's ID
            user_message: The user's message

        Returns:
            List of relevant memories
        """
        try:
            logger.info(f"Retrieving memories for user {user_id}")
            
            # Retrieve memories using the memory service
            memories = await self.memory_service.search_memories(
                user_id=user_id,
                query=user_message,
                limit=5,
                include_metadata=True
            )
            
            logger.info(f"Retrieved {len(memories)} memories for user {user_id}")
            return memories
            
        except Exception as e:
            logger.error(f"Error retrieving memories for user {user_id}: {e}")
            return []

    async def _analyze_intent(
        self,
        message: str,
        memories: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]]
    ) -> IntentAnalysis:
        """Analyze user intent using LLM.

        Args:
            message: The user's message
            memories: Retrieved memories
            conversation_history: Previous conversation

        Returns:
            IntentAnalysis with intent details
        """
        try:
            logger.info(f"Analyzing intent for message: {message[:50]}...")
            
            # Create intent analysis prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """
                You are an expert at analyzing user intent in conversational commerce.
                
                Analyze the user's message and determine:
                1. Intent type: product_inquiry, order_inquiry, health_advice, general
                2. Confidence score (0.0 to 1.0)
                3. Key entities mentioned
                4. Urgency level: low, medium, high
                5. Complexity level: simple, moderate, complex
                
                Consider the user's memories and conversation history for context.
                """),
                ("human", """
                User Message: {message}
                User Memories: {memories}
                Conversation History: {conversation_history}
                
                Analyze the intent and provide a structured response.
                """)
            ])
            
            # Create the analysis chain
            parser = JsonOutputParser(pydantic_object=IntentAnalysis)
            chain = prompt | self.llm | parser
            
            # Analyze intent
            intent_analysis = await chain.ainvoke({
                "message": message,
                "memories": memories,
                "conversation_history": conversation_history
            })
            
            logger.info(f"Intent analysis completed: {intent_analysis.intent_type}")
            return intent_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return IntentAnalysis(
                intent_type="general",
                confidence=0.5,
                entities=[],
                urgency="low",
                complexity="simple"
            )

    async def _create_plan(
        self,
        intent_analysis: IntentAnalysis,
        memories: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]]
    ) -> ExecutionPlan:
        """Create execution plan based on intent analysis.

        Args:
            intent_analysis: The intent analysis results
            memories: Retrieved memories
            conversation_history: Previous conversation

        Returns:
            ExecutionPlan with execution steps
        """
        try:
            logger.info(f"Creating execution plan for intent: {intent_analysis.intent_type}")
            
            # Create planning prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """
                You are an expert at creating execution plans for conversational commerce.
                
                Create a detailed execution plan based on the intent analysis.
                Consider which sub-agents and tools are needed.
                
                Available sub-agents:
                - product_expert: For product recommendations and discovery
                - order_specialist: For order status, tracking, and returns
                - health_advisor: For health and wellness advice
                - memory_manager: For user personalization and memory operations
                
                Available tools:
                - Memory tools: retrieve_memories, store_memory, update_user_profile
                - Product tools: search_products, get_product_details, create_bundles
                - Order tools: check_order_status, track_shipment, process_refund
                - Health tools: get_health_advice, check_interactions, dosage_advice
                
                Create a plan that efficiently addresses the user's needs.
                """),
                ("human", """
                Intent Analysis: {intent_analysis}
                User Memories: {memories}
                Conversation History: {conversation_history}
                
                Create an execution plan with specific steps, sub-agents, and tools needed.
                """)
            ])
            
            # Create the planning chain
            parser = JsonOutputParser(pydantic_object=ExecutionPlan)
            chain = prompt | self.llm | parser
            
            # Create execution plan
            execution_plan = await chain.ainvoke({
                "intent_analysis": intent_analysis,
                "memories": memories,
                "conversation_history": conversation_history
            })
            
            logger.info(f"Execution plan created with {len(execution_plan.steps)} steps")
            return execution_plan
            
        except Exception as e:
            logger.error(f"Error creating execution plan: {e}")
            return ExecutionPlan(
                steps=[{"action": "general_response", "description": "Provide general assistance"}],
                sub_agents_needed=["memory_manager"],
                tools_needed=["retrieve_memories"],
                estimated_time=30,
                priority="medium"
            )

    async def optimize_plan(
        self,
        plan: ExecutionPlan,
        user_context: Dict[str, Any]
    ) -> ExecutionPlan:
        """Optimize execution plan based on user context.

        Args:
            plan: The original execution plan
            user_context: Additional user context

        Returns:
            Optimized execution plan
        """
        try:
            logger.info("Optimizing execution plan")
            
            # This would implement plan optimization logic
            # For now, we'll return the original plan
            return plan
            
        except Exception as e:
            logger.error(f"Error optimizing plan: {e}")
            return plan

    async def validate_plan(
        self,
        plan: ExecutionPlan,
        available_resources: Dict[str, Any]
    ) -> bool:
        """Validate execution plan against available resources.

        Args:
            plan: The execution plan to validate
            available_resources: Available system resources

        Returns:
            True if plan is valid, False otherwise
        """
        try:
            logger.info("Validating execution plan")
            
            # Check if required sub-agents are available
            required_agents = plan.sub_agents_needed
            available_agents = available_resources.get("sub_agents", [])
            
            for agent in required_agents:
                if agent not in available_agents:
                    logger.warning(f"Required sub-agent {agent} not available")
                    return False
            
            # Check if required tools are available
            required_tools = plan.tools_needed
            available_tools = available_resources.get("tools", [])
            
            for tool in required_tools:
                if tool not in available_tools:
                    logger.warning(f"Required tool {tool} not available")
                    return False
            
            logger.info("Execution plan validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating plan: {e}")
            return False

    async def get_plan_metrics(
        self,
        plan: ExecutionPlan
    ) -> Dict[str, Any]:
        """Get metrics for the execution plan.

        Args:
            plan: The execution plan

        Returns:
            Dictionary with plan metrics
        """
        try:
            metrics = {
                "step_count": len(plan.steps),
                "sub_agent_count": len(plan.sub_agents_needed),
                "tool_count": len(plan.tools_needed),
                "estimated_time": plan.estimated_time,
                "priority": plan.priority,
                "complexity_score": self._calculate_complexity_score(plan)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating plan metrics: {e}")
            return {}

    def _calculate_complexity_score(self, plan: ExecutionPlan) -> float:
        """Calculate complexity score for the plan.

        Args:
            plan: The execution plan

        Returns:
            Complexity score from 0.0 to 1.0
        """
        try:
            # Simple complexity calculation based on plan components
            step_score = min(len(plan.steps) / 10.0, 1.0)
            agent_score = min(len(plan.sub_agents_needed) / 5.0, 1.0)
            tool_score = min(len(plan.tools_needed) / 10.0, 1.0)
            
            # Weighted average
            complexity_score = (step_score * 0.4 + agent_score * 0.3 + tool_score * 0.3)
            
            return round(complexity_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating complexity score: {e}")
            return 0.5
