"""Main Deep Agent for conversational commerce system."""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from backend.domain.entities.chat import ChatState, UserProfile
from backend.domain.entities.enhanced_chat import EnhancedChatState
from backend.application.services.hybrid_memory_service import HybridMemoryService
from backend.application.services.product_service import ProductService
from backend.application.services.order_graph_service import OrderGraphService
from backend.application.interfaces.deep_agent import IDeepAgent, DeepAgentResponse
from .sub_agents import (
    ProductExpertSubAgent,
    OrderSpecialistSubAgent,
    HealthAdvisorSubAgent,
    MemoryManagerSubAgent,
    SubAgentRegistry,
    SubAgentResponse
)
from .tools.memory_tools import MemoryTools
from .tools.product_tools import ProductTools
from .tools.order_tools import OrderTools
from .tools.health_tools import HealthTools
from .planning_engine import PlanningEngine

logger = logging.getLogger("conversational_commerce.deep_agent")


# DeepAgentResponse is now imported from interfaces


class ConversationalCommerceDeepAgent(IDeepAgent):
    """Main Deep Agent for conversational commerce implementing IDeepAgent interface."""

    def __init__(
        self,
        llm: ChatOpenAI,
        memory_service: HybridMemoryService,
        product_service: ProductService,
        order_graph_service: Optional[OrderGraphService] = None,
        **kwargs
    ):
        """Initialize the Deep Agent.

        Args:
            llm: Language model instance
            memory_service: Memory service for user context
            product_service: Product service for recommendations
            order_graph_service: Order service for order management
            **kwargs: Additional arguments
        """
        self.llm = llm
        self.memory_service = memory_service
        self.product_service = product_service
        self.order_graph_service = order_graph_service
        
        # Initialize tools
        self.memory_tools = MemoryTools(memory_service)
        self.product_tools = ProductTools(product_service, memory_service)
        self.order_tools = OrderTools(order_graph_service) if order_graph_service else None
        self.health_tools = HealthTools(memory_service)
        
        # Initialize sub-agents
        self.sub_agents = {
            "product_expert": ProductExpertSubAgent(llm, self.product_tools),
            "order_specialist": OrderSpecialistSubAgent(llm, self.order_tools) if self.order_tools else None,
            "health_advisor": HealthAdvisorSubAgent(llm, self.health_tools),
            "memory_manager": MemoryManagerSubAgent(llm, self.memory_tools)
        }
        
        # Initialize sub-agent registry
        self.sub_agent_registry = SubAgentRegistry()
        
        # Initialize planning engine
        self.planning_engine = PlanningEngine(llm, memory_service)
        
        # Get all available tools
        self.all_tools = self._get_all_tools()
        
        logger.info("Deep Agent initialized with all tools and sub-agents")
    
    async def process_message(
        self,
        user_message: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> DeepAgentResponse:
        """Process a user message using Deep Agent architecture.
        
        Args:
            user_message: The user's message
            user_id: User identifier
            context: Additional context for processing
            
        Returns:
            Deep Agent response with sub-agent information
        """
        try:
            # Retrieve relevant memories
            memories = await self.memory_service.retrieve_relevant_memories(
                user_id=user_id,
                query=user_message,
                limit=5
            )
            
            # Use planning engine to determine approach
            plan = await self.planning_engine.create_execution_plan(
                user_message=user_message,
                user_id=user_id,
                conversation_history=context.get("conversation_history", [])
            )
            
            # Determine which sub-agent to use
            sub_agent_type = self._determine_sub_agent(user_message, plan)
            
            if sub_agent_type:
                # Delegate to sub-agent
                response = await self.delegate_task(
                    task_description=user_message,
                    subagent_type=sub_agent_type,
                    user_id=user_id,
                    context=context
                )
                return response
            else:
                # Handle with main agent directly
                return await self._handle_directly(user_message, user_id, context, memories)
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return DeepAgentResponse(
                response="I apologize, but I encountered an error processing your request. Please try again.",
                sub_agent_used=None,
                tools_used=[],
                memories_retrieved=0,
                confidence=0.0,
                reasoning=f"Error in message processing: {str(e)}"
            )
    
    def get_available_sub_agents(self) -> List[str]:
        """Get list of available sub-agent types.
        
        Returns:
            List of available sub-agent type names
        """
        return self.sub_agent_registry.get_available_sub_agents()
    
    def get_sub_agent_descriptions(self) -> List[str]:
        """Get descriptions of all sub-agents for task delegation.
        
        Returns:
            List of sub-agent descriptions
        """
        return self.sub_agent_registry.get_sub_agent_descriptions()
    
    def _determine_sub_agent(self, user_message: str, plan: Dict[str, Any]) -> Optional[str]:
        """Determine which sub-agent should handle the message.
        
        Args:
            user_message: The user's message
            plan: Execution plan from planning engine
            
        Returns:
            Sub-agent type name or None for direct handling
        """
        # Simple keyword-based routing (in production, this would use ML)
        message_lower = user_message.lower()
        
        if any(keyword in message_lower for keyword in ['product', 'supplement', 'vitamin', 'buy', 'recommend']):
            return "product_expert"
        elif any(keyword in message_lower for keyword in ['order', 'track', 'shipment', 'return', 'refund']):
            return "order_specialist"
        elif any(keyword in message_lower for keyword in ['health', 'safe', 'interaction', 'dosage', 'advice']):
            return "health_advisor"
        elif any(keyword in message_lower for keyword in ['remember', 'prefer', 'profile', 'update']):
            return "memory_manager"
        
        return None
    
    async def _handle_directly(
        self,
        user_message: str,
        user_id: str,
        context: Dict[str, Any],
        memories: List[Dict[str, Any]]
    ) -> DeepAgentResponse:
        """Handle message directly without sub-agent delegation.
        
        Args:
            user_message: The user's message
            user_id: User identifier
            context: Additional context
            memories: Retrieved memories
            
        Returns:
            Direct response from main agent
        """
        # This would use the main agent's LLM directly
        # For now, return a simple response
        return DeepAgentResponse(
            response="I understand your request. Let me help you with that.",
            sub_agent_used=None,
            tools_used=["main_agent_processing"],
            memories_retrieved=len(memories),
            confidence=0.8,
            reasoning="Handled directly by main agent"
        )
    
    async def delegate_task(
        self,
        task_description: str,
        subagent_type: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> SubAgentResponse:
        """Delegate a task to a specific sub-agent following Deep Agents framework pattern.
        
        Args:
            task_description: Description of the task to delegate
            subagent_type: Type of sub-agent to use
            user_id: User ID for context
            context: Additional context for the task
            
        Returns:
            Response from the sub-agent
        """
        # Validate sub-agent type
        if subagent_type not in self.sub_agent_registry.get_available_sub_agents():
            available_agents = self.sub_agent_registry.get_available_sub_agents()
            raise ValueError(f"Invalid sub-agent type '{subagent_type}'. Available types: {available_agents}")
        
        # Get sub-agent configuration
        sub_agent_config = self.sub_agent_registry.get_sub_agent_config(subagent_type)
        if not sub_agent_config:
            raise ValueError(f"Sub-agent configuration not found for '{subagent_type}'")
        
        # Get the actual sub-agent instance
        sub_agent = self.sub_agents.get(subagent_type)
        if not sub_agent:
            raise ValueError(f"Sub-agent instance not found for '{subagent_type}'")
        
        # Retrieve relevant memories for context
        memories = await self.memory_service.retrieve_relevant_memories(
            user_id=user_id,
            query=task_description,
            limit=5
        )
        
        # Create sub-agent state
        sub_agent_state = {
            "user_id": user_id,
            "memories": memories,
            "context": context,
            "tools_used": [],
            "confidence": 0.0
        }
        
        # Delegate to sub-agent
        try:
            response = await sub_agent.process(
                user_message=task_description,
                user_id=user_id,
                memories=memories,
                intent=context.get("intent", {}),
                state=sub_agent_state
            )
            
            logger.info(f"Task delegated to {subagent_type}: {task_description[:100]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error delegating task to {subagent_type}: {str(e)}")
            return SubAgentResponse(
                response=f"I encountered an error while processing your request with the {subagent_type}.",
                tools_used=[],
                confidence=0.0,
                reasoning=f"Error in sub-agent delegation: {str(e)}"
            )

    def _get_all_tools(self) -> List[Any]:
        """Get all available tools for the main agent."""
        tools = []
        
        # Memory tools
        tools.extend([
            self.memory_tools.retrieve_memories_tool,
            self.memory_tools.store_memory_tool,
            self.memory_tools.update_user_profile_tool,
        ])
        
        # Product tools
        tools.extend([
            self.product_tools.search_products_tool,
            self.product_tools.get_product_details_tool,
            self.product_tools.create_product_bundles_tool,
        ])
        
        # Order tools (if available)
        if self.order_tools:
            tools.extend([
                self.order_tools.check_order_status_tool,
                self.order_tools.track_shipment_tool,
                self.order_tools.process_refund_tool,
            ])
        
        # Health tools
        tools.extend([
            self.health_tools.get_health_advice_tool,
            self.health_tools.check_drug_interactions_tool,
        ])
        
        return tools

    def _get_main_system_prompt(self) -> str:
        """Get the main system prompt for the Deep Agent."""
        return """
        You are a sophisticated conversational commerce assistant for a health & wellness store.

        CORE CAPABILITIES:
        - Product discovery and recommendations
        - Order status and tracking
        - Refunds and returns
        - Health and wellness advice
        - Memory and personalization

        PLANNING APPROACH:
        1. Analyze the user's intent and context
        2. Retrieve relevant user memories
        3. Determine which sub-agents and tools are needed
        4. Create a plan for the conversation
        5. Execute the plan with appropriate sub-agents
        6. Synthesize results into a coherent response

        MEMORY INTEGRATION:
        - ALWAYS retrieve relevant memories before responding
        - Use memories to personalize all interactions
        - Store new information as appropriate memories
        - Update user profiles with new insights
        - Reference past interactions naturally

        SUB-AGENT COORDINATION:
        - Use product_expert for product recommendations and discovery
        - Use order_specialist for order status, tracking, and returns
        - Use health_advisor for health and wellness guidance
        - Use memory_manager for user personalization and memory operations

        RESPONSE FORMAT:
        Always provide helpful, personalized responses that leverage user context and memories.
        Be conversational and natural while being informative and accurate.
        """

    async def process_message(
        self,
        user_message: str,
        user_id: str,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> DeepAgentResponse:
        """Process a user message using Deep Agent architecture.

        Args:
            user_message: The user's message
            user_id: The user's ID
            session_id: Optional session ID
            conversation_history: Optional conversation history

        Returns:
            DeepAgentResponse with the processed result
        """
        try:
            logger.info(f"Processing message for user {user_id}: {user_message[:100]}...")
            
            # Step 1: Create execution plan
            plan = await self.planning_engine.create_execution_plan(
                user_message=user_message,
                user_id=user_id,
                conversation_history=conversation_history or []
            )
            
            logger.info(f"Created execution plan: {plan['intent']['intent_type']}")
            
            # Step 2: Execute plan with appropriate sub-agents
            execution_result = await self._execute_plan(plan, user_message, user_id)
            
            # Step 3: Synthesize final response
            final_response = await self._synthesize_response(
                user_message=user_message,
                user_id=user_id,
                execution_result=execution_result,
                memories=plan.get('memories', [])
            )
            
            logger.info(f"Deep Agent processing completed for user {user_id}")
            return final_response
            
        except Exception as e:
            logger.error(f"Error in Deep Agent processing: {e}")
            return DeepAgentResponse(
                response="I'm sorry, I encountered an error processing your request. Please try again.",
                sub_agent_used=None,
                tools_used=[],
                memories_retrieved=0,
                confidence=0.0,
                reasoning="Error occurred during processing"
            )

    async def _execute_plan(
        self,
        plan: Dict[str, Any],
        user_message: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Execute the plan using appropriate sub-agents.

        Args:
            plan: The execution plan
            user_message: The user's message
            user_id: The user's ID

        Returns:
            Execution result from sub-agents
        """
        intent = plan.get('intent', {})
        intent_type = intent.get('intent_type', 'general')
        memories = plan.get('memories', [])
        
        logger.info(f"Executing plan for intent: {intent_type}")
        
        # Route to appropriate sub-agent based on intent
        if intent_type == 'product_inquiry':
            return await self._handle_product_inquiry(user_message, user_id, memories, intent)
        elif intent_type == 'order_inquiry':
            return await self._handle_order_inquiry(user_message, user_id, memories, intent)
        elif intent_type == 'health_advice':
            return await self._handle_health_inquiry(user_message, user_id, memories, intent)
        elif intent_type == 'general':
            return await self._handle_general_inquiry(user_message, user_id, memories, intent)
        else:
            return await self._handle_general_inquiry(user_message, user_id, memories, intent)

    async def _handle_product_inquiry(
        self,
        user_message: str,
        user_id: str,
        memories: List[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle product-related inquiries."""
        logger.info("Handling product inquiry with Product Expert sub-agent")
        
        if not self.sub_agents.get("product_expert"):
            return {"error": "Product expert not available"}
        
        # Use product expert sub-agent
        result = await self.sub_agents["product_expert"].process(
            user_message=user_message,
            user_id=user_id,
            memories=memories,
            intent=intent
        )
        
        return {
            "sub_agent": "product_expert",
            "result": result,
            "tools_used": ["search_products", "get_product_details", "create_bundles"]
        }

    async def _handle_order_inquiry(
        self,
        user_message: str,
        user_id: str,
        memories: List[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle order-related inquiries."""
        logger.info("Handling order inquiry with Order Specialist sub-agent")
        
        if not self.sub_agents.get("order_specialist"):
            return {"error": "Order specialist not available"}
        
        # Use order specialist sub-agent
        result = await self.sub_agents["order_specialist"].process(
            user_message=user_message,
            user_id=user_id,
            memories=memories,
            intent=intent
        )
        
        return {
            "sub_agent": "order_specialist",
            "result": result,
            "tools_used": ["check_order_status", "track_shipment", "process_refund"]
        }

    async def _handle_health_inquiry(
        self,
        user_message: str,
        user_id: str,
        memories: List[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle health-related inquiries."""
        logger.info("Handling health inquiry with Health Advisor sub-agent")
        
        # Use health advisor sub-agent
        result = await self.sub_agents["health_advisor"].process(
            user_message=user_message,
            user_id=user_id,
            memories=memories,
            intent=intent
        )
        
        return {
            "sub_agent": "health_advisor",
            "result": result,
            "tools_used": ["get_health_advice", "check_interactions"]
        }

    async def _handle_general_inquiry(
        self,
        user_message: str,
        user_id: str,
        memories: List[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle general inquiries."""
        logger.info("Handling general inquiry")
        
        # For general inquiries, we might use memory manager to provide context
        result = await self.sub_agents["memory_manager"].process(
            user_message=user_message,
            user_id=user_id,
            memories=memories,
            intent=intent
        )
        
        return {
            "sub_agent": "memory_manager",
            "result": result,
            "tools_used": ["retrieve_memories", "store_memory"]
        }

    async def _synthesize_response(
        self,
        user_message: str,
        user_id: str,
        execution_result: Dict[str, Any],
        memories: List[Dict[str, Any]]
    ) -> DeepAgentResponse:
        """Synthesize the final response from execution results.

        Args:
            user_message: The original user message
            user_id: The user's ID
            execution_result: Results from sub-agent execution
            memories: Retrieved memories

        Returns:
            Synthesized response
        """
        try:
            # Create synthesis prompt
            synthesis_prompt = ChatPromptTemplate.from_messages([
                ("system", self._get_main_system_prompt()),
                ("human", """
                Based on the execution results, create a natural, helpful response to the user.

                User Message: {user_message}
                Execution Results: {execution_result}
                Retrieved Memories: {memories}

                Create a response that:
                1. Directly addresses the user's question or request
                2. Incorporates relevant memories for personalization
                3. Provides helpful information or recommendations
                4. Maintains a conversational tone
                5. Includes any specific details from the execution results

                Response should be natural and helpful, not robotic.
                """)
            ])
            
            # Create the synthesis chain
            synthesis_chain = synthesis_prompt | self.llm
            
            # Generate the response
            response = await synthesis_chain.ainvoke({
                "user_message": user_message,
                "execution_result": execution_result,
                "memories": memories
            })
            
            # Extract response content
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            return DeepAgentResponse(
                response=response_text,
                sub_agent_used=execution_result.get('sub_agent'),
                tools_used=execution_result.get('tools_used', []),
                memories_retrieved=len(memories),
                confidence=0.8,  # Default confidence
                reasoning=f"Used {execution_result.get('sub_agent', 'general')} sub-agent"
            )
            
        except Exception as e:
            logger.error(f"Error synthesizing response: {e}")
            return DeepAgentResponse(
                response="I'm sorry, I had trouble processing your request. Could you please try again?",
                sub_agent_used=execution_result.get('sub_agent'),
                tools_used=execution_result.get('tools_used', []),
                memories_retrieved=len(memories),
                confidence=0.3,
                reasoning="Error occurred during response synthesis"
            )

    async def process_chat_state(self, state: Union[ChatState, EnhancedChatState]) -> Union[ChatState, EnhancedChatState]:
        """Process a chat state using Deep Agent architecture.

        Args:
            state: The chat state to process

        Returns:
            Updated chat state
        """
        try:
            # Extract user message from state
            user_message = ""
            for msg in reversed(state.messages):
                if msg.get('type') == 'human':
                    content = msg.get('content', '')
                    if isinstance(content, list):
                        content = ' '.join(str(item) for item in content)
                    user_message = str(content)
                    break
            
            if not user_message:
                logger.warning("No user message found in state")
                return state
            
            # Process with Deep Agent
            result = await self.process_message(
                user_message=user_message,
                user_id=state.user_id,
                session_id=getattr(state, 'session_id', None),
                conversation_history=state.messages
            )
            
            # Add the response to the state
            state.add_message(result.response, is_human=False)
            
            # Store memory if needed
            if result.memories_retrieved > 0:
                await self.memory_tools.store_memory_tool(
                    user_id=state.user_id,
                    content=f"User asked: {user_message}",
                    memory_type="conversation_context",
                    metadata={
                        "sub_agent_used": result.sub_agent_used,
                        "tools_used": result.tools_used,
                        "confidence": result.confidence
                    }
                )
            
            logger.info(f"Deep Agent processed chat state for user {state.user_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error processing chat state with Deep Agent: {e}")
            # Fallback response
            state.add_message(
                "I'm sorry, I encountered an error processing your request. Please try again.",
                is_human=False
            )
            return state
