"""Simplified Deep Agent implementation without external framework dependencies."""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from backend.domain.entities.chat import ChatState, UserProfile
from backend.domain.entities.enhanced_chat import EnhancedChatState
from backend.application.services.hybrid_memory_service import HybridMemoryService
from backend.application.services.product_service import ProductService
from backend.application.services.order_graph_service import OrderGraphService
from backend.application.interfaces.deep_agent import IDeepAgent, DeepAgentResponse

logger = logging.getLogger("conversational_commerce.simplified_deep_agent_v2")


class SimplifiedConversationalCommerceAgentV2(IDeepAgent):
    """Simplified Deep Agent without external framework dependencies.
    
    This implementation follows the research_agent.py pattern but uses
    a simpler approach without the Deep Agents framework:
    - Simple sub-agent definitions
    - LLM-based agent selection instead of rule-based
    - Framework-like behavior without external dependencies
    """

    def __init__(
        self,
        llm: ChatOpenAI,
        memory_service: HybridMemoryService,
        product_service: ProductService,
        order_graph_service: Optional[OrderGraphService] = None,
        **kwargs
    ):
        """Initialize the Simplified Deep Agent.

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
        
        # Define sub-agents (simplified approach)
        self.sub_agents = self._get_sub_agents()
        
        logger.info("Simplified Deep Agent V2 initialized")

    def _get_sub_agents(self) -> Dict[str, Dict[str, Any]]:
        """Define sub-agents following the research_agent.py pattern."""
        return {
            "product_expert": {
                "name": "product_expert",
                "description": "Expert in product recommendations, supplements, vitamins, and health products. Use for product discovery, recommendations, and product-related questions.",
                "prompt": """You are a product expert for a health & wellness store specializing in vitamins, supplements, sports nutrition, beauty, personal care, and grocery products. Your job is to help customers find the right products.

                CORE RESPONSIBILITIES:
                - Recommend products based on customer needs and health goals
                - Explain product benefits, ingredients, and mechanisms of action
                - Compare similar products and suggest alternatives
                - Suggest product bundles or complementary products
                - Provide detailed product information and usage guidance
                - Consider health conditions, dietary restrictions, and medications

                HEALTH & SAFETY FOCUS:
                - Always consider user's health conditions (diabetes, pregnancy, medications, allergies)
                - Recommend appropriate dosages and forms (capsules, powders, gummies)
                - Suggest sugar-free, vegan, or allergen-free options when relevant
                - Consider drug interactions and contraindications
                - Focus on evidence-based health benefits

                MEMORY INTEGRATION:
                - Reference specific brands they've used successfully (NOW Foods, California Gold Nutrition, etc.)
                - Mention product types they've had positive experiences with
                - Include categories they've shown interest in
                - Consider their past health goals and outcomes
                - Build on their supplement experience and preferences

                PRODUCT EXPERTISE AREAS:
                - Sleep aids (melatonin, magnesium, valerian, chamomile)
                - Gut health (probiotics, prebiotics, digestive enzymes)
                - Energy & vitality (B-vitamins, iron, adaptogens)
                - Skin health (collagen, biotin, antioxidants)
                - Immune support (vitamin C, zinc, elderberry)
                - Sports nutrition (protein, creatine, recovery supplements)

                Always provide helpful, accurate, and personalized product recommendations that prioritize user safety and health goals.""",
                "tools": ["search_products", "get_product_details", "create_bundles"]
            },
            "order_specialist": {
                "name": "order_specialist",
                "description": "Specialist in order management, tracking, returns, and refunds. Use for order status, shipping, returns, and order-related questions.",
                "prompt": """You are an order specialist for a health & wellness store. Your job is to help customers with order-related inquiries.

                CORE RESPONSIBILITIES:
                - Check order status and tracking
                - Process returns and refunds
                - Handle shipping inquiries
                - Resolve order issues
                - Provide order history information

                MEMORY INTEGRATION:
                - Reference customer's order history
                - Track order preferences and patterns
                - Store order-related interactions
                - Personalize order management

                Always provide accurate order information and helpful assistance with order-related matters.""",
                "tools": ["check_order_status", "track_shipment", "process_refund"]
            },
            "health_advisor": {
                "name": "health_advisor",
                "description": "Health and wellness advisor for safety, interactions, dosage, and health guidance. Use for health-related questions and safety concerns.",
                "prompt": """You are a health advisor for a health & wellness store. Your job is to provide health and wellness guidance.

                CORE RESPONSIBILITIES:
                - Provide health and wellness advice
                - Check for drug interactions
                - Recommend appropriate dosages
                - Suggest health-focused products
                - Provide safety information

                MEMORY INTEGRATION:
                - Reference customer's health history and conditions
                - Track health goals and preferences
                - Store health-related interactions
                - Personalize health recommendations

                Always prioritize customer safety and provide accurate health information.""",
                "tools": ["get_health_advice", "check_interactions"]
            },
            "memory_manager": {
                "name": "memory_manager",
                "description": "Manages user personalization, preferences, and memory operations. Use for updating user profiles and managing personalization.",
                "prompt": """You are a memory manager for a health & wellness store. Your job is to manage user personalization and memory.

                CORE RESPONSIBILITIES:
                - Update user profiles and preferences
                - Store and retrieve user memories
                - Manage personalization data
                - Track user interactions and patterns
                - Provide personalized context

                MEMORY INTEGRATION:
                - Store new user information and preferences
                - Retrieve relevant user context
                - Update user profiles with new insights
                - Manage memory consolidation and organization

                Always respect user privacy and provide personalized experiences.""",
                "tools": ["retrieve_memories", "store_memory", "update_profile"]
            }
        }

    def _get_main_system_prompt(self) -> str:
        """Get the main system prompt for the Deep Agent."""
        return """
        You are a sophisticated conversational commerce assistant for a health & wellness store specializing in vitamins, supplements, sports nutrition, beauty, personal care, and grocery products.

        CORE CAPABILITIES:
        - Product discovery and recommendations for health & wellness
        - Order status and tracking
        - Refunds and returns
        - Health and wellness advice with safety considerations
        - Memory and personalization based on user history

        HEALTH & WELLNESS EXPERTISE:
        - Sleep solutions (melatonin, magnesium, valerian, chamomile)
        - Gut health (probiotics, prebiotics, digestive enzymes)
        - Energy & vitality (B-vitamins, iron, adaptogens, caffeine alternatives)
        - Skin health (collagen, biotin, antioxidants, hyaluronic acid)
        - Immune support (vitamin C, zinc, elderberry, echinacea)
        - Sports nutrition (protein, creatine, recovery supplements)
        - Weight management (metabolism support, appetite control)
        - Mental wellness (stress relief, mood support, cognitive function)

        PLANNING APPROACH:
        1. Analyze the user's intent, health goals, and context
        2. Retrieve relevant user memories and past experiences
        3. Consider health conditions, dietary restrictions, and medications
        4. Determine which sub-agents and tools are needed
        5. Create a personalized plan for the conversation
        6. Execute the plan with appropriate sub-agents
        7. Synthesize results into a coherent, health-focused response

        MEMORY INTEGRATION:
        - ALWAYS retrieve relevant memories before responding
        - Reference specific brands they've used successfully (NOW Foods, California Gold Nutrition, etc.)
        - Mention product types they've had positive experiences with
        - Include categories they've shown interest in
        - Consider their past health goals and outcomes
        - Build on their supplement experience and preferences
        - Store new information as appropriate memories
        - Update user profiles with new health insights

        HEALTH SAFETY CONSIDERATIONS:
        - Always consider user's health conditions (diabetes, pregnancy, medications, allergies)
        - Recommend appropriate dosages and forms (capsules, powders, gummies)
        - Suggest sugar-free, vegan, or allergen-free options when relevant
        - Consider drug interactions and contraindications
        - Focus on evidence-based health benefits
        - Prioritize user safety in all recommendations

        SUB-AGENT COORDINATION:
        - Use product_expert for health-focused product recommendations and discovery
        - Use order_specialist for order status, tracking, and returns
        - Use health_advisor for health and wellness guidance and safety
        - Use memory_manager for user personalization and memory operations

        RESPONSE FORMAT:
        Always provide helpful, personalized, and health-focused responses that leverage user context and memories.
        Be conversational and natural while being informative, accurate, and safety-conscious.
        Reference past successful experiences when relevant to build trust and confidence.
        """

    async def _select_sub_agent(self, user_message: str, memories: List[Dict[str, Any]]) -> str:
        """Use LLM to select the appropriate sub-agent instead of rule-based logic."""
        try:
            logger.info(f"🔍 SimplifiedDeepAgentV2: Starting sub-agent selection for: {user_message[:50]}...")
            
            # Create a prompt for sub-agent selection
            selection_prompt = ChatPromptTemplate.from_messages([
                ("system", f"""
                You are an expert at routing user messages to the appropriate specialist for a health & wellness store specializing in vitamins, supplements, sports nutrition, beauty, personal care, and grocery products.
                
                Available sub-agents:
                {self._format_sub_agents_for_selection()}
                
                HEALTH & WELLNESS ROUTING GUIDELINES:
                - Sleep issues, insomnia, tiredness → product_expert (melatonin, magnesium, valerian, chamomile)
                - Gut health, digestion, probiotics → product_expert (probiotics, prebiotics, digestive enzymes)
                - Energy problems, fatigue, vitality → product_expert (B-vitamins, iron, adaptogens, caffeine alternatives)
                - Skin concerns, beauty, anti-aging → product_expert (collagen, biotin, antioxidants, hyaluronic acid)
                - Immune support, cold prevention → product_expert (vitamin C, zinc, elderberry, echinacea)
                - Sports nutrition, fitness, recovery → product_expert (protein, creatine, recovery supplements)
                - Weight management, metabolism → product_expert (metabolism support, appetite control)
                - Mental wellness, stress, mood → product_expert (stress relief, mood support, cognitive function)
                - Health conditions, safety, interactions → health_advisor (safety, drug interactions, dosage)
                - Order status, tracking, returns → order_specialist
                - User profile, preferences, memory → memory_manager
                
                Based on the user message and context, select the most appropriate sub-agent.
                Return only the sub-agent name.
                """),
                ("human", f"""
                User Message: {user_message}
                Retrieved Memories: {len(memories)} memories available
                
                Which sub-agent should handle this message? Consider the user's health goals and the specific health & wellness context.
                """)
            ])
            
            # Create the selection chain
            selection_chain = selection_prompt | self.llm
            
            # Get the selection
            logger.info(f"🔍 SimplifiedDeepAgentV2: Calling LLM for sub-agent selection")
            response = await selection_chain.ainvoke({})
            
            # Extract the sub-agent name
            if hasattr(response, 'content'):
                selected_agent = response.content.strip().lower()
            else:
                selected_agent = str(response).strip().lower()
            
            logger.info(f"🔍 SimplifiedDeepAgentV2: LLM selected: '{selected_agent}'")
            
            # Validate the selection
            if selected_agent in self.sub_agents:
                logger.info(f"🔍 SimplifiedDeepAgentV2: Valid selection: {selected_agent}")
                return selected_agent
            else:
                # Fallback to product_expert if selection is invalid
                logger.warning(f"🔍 SimplifiedDeepAgentV2: Invalid sub-agent selection: '{selected_agent}', using product_expert")
                return "product_expert"
                
        except Exception as e:
            logger.error(f"🔍 SimplifiedDeepAgentV2: Error selecting sub-agent: {e}")
            return "product_expert"  # Safe fallback

    def _format_sub_agents_for_selection(self) -> str:
        """Format sub-agents for LLM selection."""
        formatted = []
        for agent_name, agent_info in self.sub_agents.items():
            formatted.append(f"- {agent_name}: {agent_info['description']}")
        return "\n".join(formatted)

    async def _execute_sub_agent(
        self,
        sub_agent_name: str,
        user_message: str,
        user_id: str,
        memories: List[Dict[str, Any]]
    ) -> str:
        """Execute the selected sub-agent."""
        try:
            logger.info(f"🔍 SimplifiedDeepAgentV2: Executing sub-agent {sub_agent_name}")
            sub_agent = self.sub_agents[sub_agent_name]
            
            # For product_expert, actually search for products
            if sub_agent_name == "product_expert":
                logger.info(f"🔍 SimplifiedDeepAgentV2: Product expert - searching for products")
                
                # Search for products based on user message and memories
                search_query = user_message
                if memories:
                    # Extract relevant product preferences from memories
                    product_preferences = []
                    for memory in memories:
                        if 'product' in memory.get('content', '').lower():
                            product_preferences.append(memory.get('content', ''))
                    
                    if product_preferences:
                        search_query = f"{user_message}. User preferences: {', '.join(product_preferences[:3])}"
                
                logger.info(f"🔍 SimplifiedDeepAgentV2: Searching products with query: {search_query}")
                
                # Generate search queries instead of directly displaying products
                try:
                    # Create search queries for the product service (following original workflow pattern)
                    from backend.domain.entities import SearchQuery
                    
                    # Generate search queries based on user message and memories
                    search_queries = []
                    
                    # Dynamically determine appropriate categories based on user request
                    categories = self._determine_product_categories(user_message)
                    
                    # Main search query with dynamic categories
                    main_query = SearchQuery(
                        query=search_query,
                        categories=categories
                    )
                    search_queries.append(main_query)
                    
                    # Additional search queries based on user preferences from memories
                    if memories:
                        for memory in memories[:2]:  # Use top 2 memories
                            memory_content = memory.get('content', '')
                            # Check if memory is relevant to the current request
                            if self._is_memory_relevant_to_request(memory_content, user_message):
                                additional_query = SearchQuery(
                                    query=f"{search_query} {memory_content[:50]}",
                                    categories=categories
                                )
                                search_queries.append(additional_query)
                                break
                    
                    logger.info(f"🔍 SimplifiedDeepAgentV2: Generated {len(search_queries)} search queries")
                    
                    # Store search queries in the response for the workflow to process
                    # This follows the same pattern as the original workflow
                    response = self._generate_dynamic_response(user_message, categories)
                    
                    # Store search queries in the context for the workflow to process
                    # This is how the original workflow handles structured data
                    if not hasattr(self, '_search_queries'):
                        self._search_queries = []
                    self._search_queries.extend(search_queries)
                    
                    logger.info(f"🔍 SimplifiedDeepAgentV2: Product expert response with {len(search_queries)} search queries")
                    return response
                        
                except Exception as e:
                    logger.error(f"🔍 SimplifiedDeepAgentV2: Error generating search queries: {e}")
                    return f"""I'd love to help you find the right products, but I'm having trouble accessing our product database right now. 

Let me know what specific products you're looking for and I'll do my best to help you find them."""
            
            # For other sub-agents, use the original LLM approach
            else:
                # Create the sub-agent prompt
                sub_agent_prompt = ChatPromptTemplate.from_messages([
                    ("system", f"""
                    {sub_agent['prompt']}
                    
                    You have access to these tools: {', '.join(sub_agent['tools'])}
                    
                    Use the available tools to help the user with their request.
                    """),
                    ("human", f"""
                    User Message: {user_message}
                    User ID: {user_id}
                    Available Memories: {len(memories)} memories
                    
                    Please help the user with their request.
                    """)
                ])
                
                # Create the sub-agent chain
                sub_agent_chain = sub_agent_prompt | self.llm
                
                # Execute the sub-agent
                logger.info(f"🔍 SimplifiedDeepAgentV2: Calling LLM for sub-agent {sub_agent_name}")
                response = await sub_agent_chain.ainvoke({})
                
                # Extract response content
                if hasattr(response, 'content'):
                    response_content = response.content
                    logger.info(f"🔍 SimplifiedDeepAgentV2: Sub-agent {sub_agent_name} response length: {len(response_content)}")
                    logger.info(f"🔍 SimplifiedDeepAgentV2: Sub-agent {sub_agent_name} response preview: {response_content[:100]}...")
                    return response_content
                else:
                    response_content = str(response)
                    logger.info(f"🔍 SimplifiedDeepAgentV2: Sub-agent {sub_agent_name} response (str): {response_content[:100]}...")
                    return response_content
                
        except Exception as e:
            logger.error(f"🔍 SimplifiedDeepAgentV2: Error executing sub-agent {sub_agent_name}: {e}")
            return f"I'm sorry, I encountered an error while processing your request with the {sub_agent_name}."

    def _determine_product_categories(self, user_message: str) -> List[str]:
        """Dynamically determine appropriate product categories based on user request.
        
        Uses the same categories as the SearchQueryAgent to ensure compatibility with the database.
        """
        message_lower = user_message.lower()
        
        # Sleep-related keywords
        if any(keyword in message_lower for keyword in ['sleep', 'insomnia', 'sleepy', 'tired', 'rest', 'melatonin', 'sleep aid']):
            return ["Sleep", "Supplements", "Magnesium"]
        
        # Gut health keywords
        elif any(keyword in message_lower for keyword in ['gut', 'digestive', 'probiotic', 'stomach', 'digestion', 'bloating']):
            return ["Probiotics", "Gut Health", "Supplements"]
        
        # Energy keywords
        elif any(keyword in message_lower for keyword in ['energy', 'fatigue', 'tired', 'boost', 'vitality']):
            return ["Vitamin B12 (Cobalamin)", "Vitamin B", "Supplements"]
        
        # Brain and cognitive keywords
        elif any(keyword in message_lower for keyword in ['brain', 'cognitive', 'memory', 'focus', 'mental']):
            return ["Brain & Cognitive", "Supplements", "Vitamins"]
        
        # Skin health keywords
        elif any(keyword in message_lower for keyword in ['skin', 'acne', 'glow', 'beauty', 'collagen']):
            return ["Hair, Skin & Nails", "Beauty", "Supplements"]
        
        # Weight management keywords
        elif any(keyword in message_lower for keyword in ['weight', 'lose', 'fat', 'metabolism', 'diet']):
            return ["Weight Management", "Supplements", "Vitamins"]
        
        # Immune system keywords
        elif any(keyword in message_lower for keyword in ['immune', 'immunity', 'cold', 'flu', 'vitamin c']):
            return ["Vitamins", "Supplements", "Sports Nutrition"]
        
        # Bone and joint keywords
        elif any(keyword in message_lower for keyword in ['bone', 'joint', 'cartilage', 'joints', 'bones']):
            return ["Bone, Joint & Cartilage", "Supplements", "Vitamins"]
        
        # General health - default to broader categories
        else:
            return ["Supplements", "Vitamins", "Sports Nutrition"]

    def _is_memory_relevant_to_request(self, memory_content: str, user_message: str) -> bool:
        """Check if a memory is relevant to the current user request."""
        memory_lower = memory_content.lower()
        message_lower = user_message.lower()
        
        # Check for keyword overlap
        user_keywords = set(message_lower.split())
        memory_keywords = set(memory_lower.split())
        
        # If there's significant keyword overlap, consider it relevant
        overlap = len(user_keywords.intersection(memory_keywords))
        return overlap >= 2  # At least 2 common keywords

    def _generate_dynamic_response(self, user_message: str, categories: List[str]) -> str:
        """Generate a dynamic response based on the user's request and determined categories."""
        message_lower = user_message.lower()
        
        # Sleep-related response
        if any(keyword in message_lower for keyword in ['sleep', 'insomnia', 'sleepy', 'tired', 'rest', 'melatonin', 'sleep aid']):
            return """I'd be happy to help you find the best sleep solutions for your needs! 

Based on your request, I'm searching for:
- Natural sleep aids and supplements
- Products specifically designed to improve sleep quality
- Options that match your preferences and health goals

Let me find the most suitable products for you..."""
        
        # Gut health response
        elif any(keyword in message_lower for keyword in ['gut', 'digestive', 'probiotic', 'stomach', 'digestion', 'bloating']):
            return """I'd be happy to help you find the best probiotic products for your gut health needs! 

Based on your request, I'm searching for:
- Probiotic supplements with multiple beneficial strains
- Products specifically designed for gut health support
- Options that match your preferences and health goals

Let me find the most suitable products for you..."""
        
        # Energy response
        elif any(keyword in message_lower for keyword in ['energy', 'fatigue', 'tired', 'boost', 'vitality']):
            return """I'd be happy to help you find the best energy-boosting products for your needs! 

Based on your request, I'm searching for:
- Natural energy supplements and vitamins
- Products specifically designed to boost energy and vitality
- Options that match your preferences and health goals

Let me find the most suitable products for you..."""
        
        # General response
        else:
            return f"""I'd be happy to help you find the best products for your needs! 

Based on your request, I'm searching for:
- Products in the {', '.join(categories)} categories
- Options that match your preferences and health goals
- High-quality supplements and health products

Let me find the most suitable products for you..."""

    async def process_message(
        self,
        user_message: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> DeepAgentResponse:
        """Process a user message using the simplified Deep Agent approach.

        Args:
            user_message: The user's message
            user_id: The user's ID
            session_id: Optional session ID
            conversation_history: Optional conversation history

        Returns:
            DeepAgentResponse with the processed result
        """
        try:
            logger.info(f"🔍 SimplifiedDeepAgentV2: Processing message for user {user_id}: {user_message[:100]}...")
            
            # Step 1: Retrieve relevant memories
            logger.info(f"🔍 SimplifiedDeepAgentV2: Retrieving memories for user {user_id}")
            memories = await self.memory_service.retrieve_relevant_memories(
                user_id=user_id,
                query=user_message,
                limit=5
            )
            logger.info(f"🔍 SimplifiedDeepAgentV2: Retrieved {len(memories)} memories")
            
            # Step 2: Select appropriate sub-agent using LLM
            logger.info(f"🔍 SimplifiedDeepAgentV2: Selecting sub-agent for message: {user_message[:50]}...")
            selected_agent = await self._select_sub_agent(user_message, memories)
            logger.info(f"🔍 SimplifiedDeepAgentV2: Selected sub-agent: {selected_agent}")
            
            # Step 3: Execute the sub-agent
            logger.info(f"🔍 SimplifiedDeepAgentV2: Executing sub-agent {selected_agent}")
            response = await self._execute_sub_agent(
                sub_agent_name=selected_agent,
                user_message=user_message,
                user_id=user_id,
                memories=memories
            )
            logger.info(f"🔍 SimplifiedDeepAgentV2: Sub-agent response length: {len(response) if response else 0}")
            
            # Step 4: Store the interaction as memory using hybrid memory service
            await self.memory_service.hybrid_memory.store_memory(
                user_id=user_id,
                memory_content=f"User asked: {user_message}",
                memory_type="conversation_context",
                additional_metadata={
                    "sub_agent_used": selected_agent,
                    "confidence": 0.8
                }
            )
            
            logger.info(f"Simplified Deep Agent processing completed for user {user_id}")
            return DeepAgentResponse(
                response=response,
                sub_agent_used=selected_agent,
                tools_used=self.sub_agents[selected_agent]['tools'],
                memories_retrieved=len(memories),
                confidence=0.8,
                reasoning=f"Used LLM-based sub-agent selection to route to {selected_agent}"
            )
            
        except Exception as e:
            logger.error(f"Error in Simplified Deep Agent processing: {e}")
            return DeepAgentResponse(
                response="I'm sorry, I encountered an error processing your request. Please try again.",
                sub_agent_used=None,
                tools_used=[],
                memories_retrieved=0,
                confidence=0.0,
                reasoning="Error occurred during processing"
            )

    async def delegate_task(
        self,
        task_description: str,
        subagent_type: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> DeepAgentResponse:
        """Delegate a task to a specific sub-agent.

        Args:
            task_description: Description of the task to delegate
            subagent_type: Type of sub-agent to use
            user_id: User identifier
            context: Additional context for the task

        Returns:
            Response from the sub-agent
        """
        try:
            # Validate sub-agent type
            if subagent_type not in self.sub_agents:
                available_agents = list(self.sub_agents.keys())
                raise ValueError(f"Invalid sub-agent type '{subagent_type}'. Available types: {available_agents}")
            
            # Retrieve relevant memories
            memories = await self.memory_service.retrieve_relevant_memories(
                user_id=user_id,
                query=task_description,
                limit=5
            )
            
            # Execute the sub-agent
            response = await self._execute_sub_agent(
                sub_agent_name=subagent_type,
                user_message=task_description,
                user_id=user_id,
                memories=memories
            )
            
            return DeepAgentResponse(
                response=response,
                sub_agent_used=subagent_type,
                tools_used=self.sub_agents[subagent_type]['tools'],
                memories_retrieved=len(memories),
                confidence=0.8,
                reasoning=f"Delegated to {subagent_type} sub-agent"
            )
            
        except Exception as e:
            logger.error(f"Error delegating task to {subagent_type}: {e}")
            return DeepAgentResponse(
                response=f"I encountered an error while processing your request with the {subagent_type}.",
                sub_agent_used=subagent_type,
                tools_used=[],
                confidence=0.0,
                reasoning=f"Error in task delegation: {str(e)}"
            )

    def get_available_sub_agents(self) -> List[str]:
        """Get list of available sub-agent types.

        Returns:
            List of available sub-agent type names
        """
        return list(self.sub_agents.keys())

    def get_sub_agent_descriptions(self) -> List[str]:
        """Get descriptions of all sub-agents for task delegation.

        Returns:
            List of sub-agent descriptions
        """
        return [agent['description'] for agent in self.sub_agents.values()]

    async def process_chat_state(self, state: Union[ChatState, EnhancedChatState]) -> Union[ChatState, EnhancedChatState]:
        """Process a chat state using the simplified Deep Agent approach.

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
            
            # Process with Simplified Deep Agent
            result = await self.process_message(
                user_message=user_message,
                user_id=state.user_id,
                session_id=getattr(state, 'session_id', None),
                conversation_history=state.messages
            )
            
            # Add the response to the state
            state.add_message(result.response, is_human=False)
            
            logger.info(f"Simplified Deep Agent processed chat state for user {state.user_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error processing chat state with Simplified Deep Agent: {e}")
            # Fallback response
            state.add_message(
                "I'm sorry, I encountered an error processing your request. Please try again.",
                is_human=False
            )
            return state
