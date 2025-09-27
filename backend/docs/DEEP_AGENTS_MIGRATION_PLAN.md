# Deep Agents Migration Plan

## Conversational Commerce System Architecture Upgrade

### Document Overview

This document outlines the complete migration plan from the current LangGraph-based workflow to a Deep Agents architecture for the conversational commerce system. The migration aims to reduce LLM calls, improve planning capabilities, and create a more extensible system.

### Table of Contents

1. [Current System Analysis](#current-system-analysis)
2. [Deep Agents Architecture](#deep-agents-architecture)
3. [Implementation Plan](#implementation-plan)
4. [Code Examples](#code-examples)
5. [Migration Strategy](#migration-strategy)
6. [Testing Strategy](#testing-strategy)
7. [Performance Expectations](#performance-expectations)
8. [Rollback Plan](#rollback-plan)

---

## Current System Analysis

### Current Architecture Issues

- **High LLM Call Count**: 6-8 LLM calls per user interaction
- **Sequential Processing**: Agents run in fixed sequence regardless of need
- **Limited Planning**: No intelligent task breakdown or optimization
- **Memory Integration**: Complex state management between agents
- **Extensibility**: Difficult to add new use cases without modifying core workflow

### Current LLM Call Breakdown

```
Enhanced Workflow (6-8 calls per interaction):
1. Greeting Detection Agent (1 call)
2. Enhanced User Profile Extraction Agent (1 call)
3. Sufficient Detail Agent (1 call)
4. Conversation Enrichment Agent (1 call)
5. Conversation Saturation Agent (1 call)
6. Search Query Agent (1 call)
7. Bundling Intent Determination (1 call)
8. Intelligent Product Bundling (1 call)
```

### Current Memory Integration

- Semantic memory service integration
- Background memory consolidation
- User profile extraction and updates
- Conversation context retrieval
- Memory-aware search query generation

---

## Deep Agents Architecture

### Core Principles

1. **Single Planning Call**: Main agent analyzes intent and creates execution plan
2. **Sub-Agent Specialization**: Dedicated agents for specific domains
3. **Intelligent Tool Selection**: Dynamic tool selection based on context
4. **Memory-First Approach**: Memory retrieval before planning
5. **Result Synthesis**: Single LLM call to combine results

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Deep Agent                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Planning Engine                        │   │
│  │  • Intent Analysis                                 │   │
│  │  • Context Assessment                             │   │
│  │  • Tool Selection                                 │   │
│  │  • Execution Planning                             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼───────┐ ┌─────▼─────┐ ┌─────▼─────┐
        │ Product Expert│ │Order Spec. │ │Health Adv.│
        │ Sub-Agent     │ │Sub-Agent   │ │Sub-Agent  │
        └───────────────┘ └───────────┘ └───────────┘
                │               │               │
        ┌───────▼───────┐ ┌─────▼─────┐ ┌─────▼─────┐
        │ Memory Mgr.   │ │Shipping   │ │Expert    │
        │ Sub-Agent     │ │Sub-Agent  │ │Sub-Agent │
        └───────────────┘ └───────────┘ └───────────┘
```

### Expected LLM Call Reduction

```
Deep Agents (2-3 calls per interaction):
1. Main Planning Call (1 call) - Determines approach and sub-agents
2. Sub-Agent Execution (0-1 calls) - Only when specialized processing needed
3. Result Synthesis (1 call) - Combines results into final response
```

---

## Implementation Plan

### Phase 1: Core Deep Agent Setup (Week 1-2)

#### 1.1 Dependencies Installation

```bash
pip install deepagents
pip install langchain-mcp-adapters  # For MCP tool integration
```

#### 1.2 Main Deep Agent Configuration

**File**: `backend/backend/application/agents/deep_agent.py`

```python
from deepagents import create_deep_agent
from backend.domain.entities.deep_chat import DeepChatState
from backend.application.services.memory_integration import MemoryIntegrationService

class ConversationalCommerceDeepAgent:
    """Main Deep Agent for conversational commerce"""

    def __init__(self, llm, memory_service: MemoryIntegrationService):
        self.llm = llm
        self.memory_service = memory_service
        self.agent = self._create_main_agent()

    def _create_main_agent(self):
        """Create the main deep agent with all tools and sub-agents"""
        return create_deep_agent(
            tools=self._get_all_tools(),
            instructions=self._get_main_system_prompt(),
            sub_agents=self._get_sub_agents()
        )

    def _get_main_system_prompt(self):
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

        Use the planning tool to break down complex tasks and coordinate sub-agents effectively.
        """

    def _get_all_tools(self):
        """Get all available tools for the main agent"""
        return [
            # Memory tools
            self.retrieve_memories_tool,
            self.store_memory_tool,
            self.update_user_profile_tool,

            # Product tools
            self.search_products_tool,
            self.get_product_details_tool,
            self.create_product_bundles_tool,

            # Order tools
            self.check_order_status_tool,
            self.track_shipment_tool,
            self.process_refund_tool,

            # Health tools
            self.get_health_advice_tool,
            self.check_drug_interactions_tool
        ]

    def _get_sub_agents(self):
        """Get all sub-agents"""
        return {
            "product_expert": ProductExpertSubAgent(self.llm),
            "order_specialist": OrderSpecialistSubAgent(self.llm),
            "health_advisor": HealthAdvisorSubAgent(self.llm),
            "memory_manager": MemoryManagerSubAgent(self.llm, self.memory_service)
        }
```

#### 1.3 Sub-Agent Implementations

**File**: `backend/backend/application/agents/sub_agents.py`

```python
class ProductExpertSubAgent:
    """Specialized for product discovery and recommendations"""

    def __init__(self, llm):
        self.llm = llm
        self.tools = [
            self.search_products_tool,
            self.get_product_details_tool,
            self.create_bundles_tool,
            self.check_availability_tool
        ]
        self.instructions = """
        You are a product expert specializing in health & wellness products.
        Focus on: product recommendations, bundling, availability, pricing.
        Always consider user's health conditions and preferences.
        Use memory context to personalize recommendations.
        """

class OrderSpecialistSubAgent:
    """Specialized for order management"""

    def __init__(self, llm):
        self.llm = llm
        self.tools = [
            self.check_order_status_tool,
            self.track_shipment_tool,
            self.process_refund_tool,
            self.update_order_tool
        ]
        self.instructions = """
        You are an order specialist handling order status, tracking, and returns.
        Focus on: order lookup, shipment tracking, refund processing.
        Always verify user identity and order details.
        Use memory to provide personalized order assistance.
        """

class HealthAdvisorSubAgent:
    """Specialized for health and wellness advice"""

    def __init__(self, llm):
        self.llm = llm
        self.tools = [
            self.get_health_advice_tool,
            self.check_interactions_tool,
            self.dosage_advice_tool
        ]
        self.instructions = """
        You are a health advisor providing wellness guidance.
        Focus on: supplement advice, drug interactions, dosage recommendations.
        Always recommend consulting healthcare providers for medical advice.
        Use user's health history from memory for personalized advice.
        """

class MemoryManagerSubAgent:
    """Specialized for memory management"""

    def __init__(self, llm, memory_service):
        self.llm = llm
        self.memory_service = memory_service
        self.tools = [
            self.retrieve_memories_tool,
            self.store_memory_tool,
            self.update_user_profile_tool,
            self.consolidate_memories_tool
        ]
        self.instructions = """
        You are a memory manager responsible for user personalization.
        Focus on: retrieving relevant memories, storing new information,
        updating user profiles, consolidating memories.
        Always maintain user privacy and data accuracy.
        """
```

### Phase 2: Memory Integration (Week 2-3)

#### 2.1 Enhanced Memory Service

**File**: `backend/backend/application/services/memory_integration.py`

```python
class MemoryIntegrationService:
    """Enhanced memory service for Deep Agents integration"""

    def __init__(self, semantic_memory_service, background_memory_manager):
        self.semantic_memory_service = semantic_memory_service
        self.background_memory_manager = background_memory_manager

    async def retrieve_contextual_memories(self, user_id: str, query: str, context_type: str = "general"):
        """Retrieve memories with context type filtering"""
        memories = await self.semantic_memory_service.retrieve_relevant_memories(
            user_id=user_id, query=query, limit=5
        )

        # Filter by context type if needed
        if context_type != "general":
            memories = [m for m in memories if m.get('metadata', {}).get('context_type') == context_type]

        return memories

    async def store_conversation_memory(self, user_id: str, conversation_data: dict):
        """Store conversation as memory with proper categorization"""
        memory_type = self._determine_memory_type(conversation_data)

        await self.semantic_memory_service.store_memory(
            user_id=user_id,
            content=conversation_data['content'],
            memory_type=memory_type,
            metadata=conversation_data.get('metadata', {})
        )

    def _determine_memory_type(self, conversation_data):
        """Determine appropriate memory type based on conversation content"""
        content = conversation_data['content'].lower()

        if any(keyword in content for keyword in ['order', 'purchase', 'bought']):
            return 'order_history'
        elif any(keyword in content for keyword in ['health', 'condition', 'medication']):
            return 'health_context'
        elif any(keyword in content for keyword in ['prefer', 'like', 'dislike']):
            return 'user_preference'
        else:
            return 'conversation_context'
```

#### 2.2 Memory-Aware Tool Implementation

**File**: `backend/backend/application/agents/tools/memory_tools.py`

```python
class MemoryTools:
    """Memory-related tools for Deep Agents"""

    def __init__(self, memory_service: MemoryIntegrationService):
        self.memory_service = memory_service

    async def retrieve_memories_tool(self, user_id: str, query: str, context_type: str = "general"):
        """Retrieve relevant memories for the user"""
        memories = await self.memory_service.retrieve_contextual_memories(
            user_id=user_id, query=query, context_type=context_type
        )
        return {
            "memories": memories,
            "count": len(memories),
            "context_type": context_type
        }

    async def store_memory_tool(self, user_id: str, content: str, memory_type: str, metadata: dict = None):
        """Store new memory for the user"""
        await self.memory_service.store_conversation_memory(
            user_id=user_id,
            conversation_data={
                "content": content,
                "metadata": metadata or {}
            }
        )
        return {"status": "stored", "memory_type": memory_type}

    async def update_user_profile_tool(self, user_id: str, profile_updates: dict):
        """Update user profile with new information"""
        # This would integrate with existing user profile service
        # Implementation depends on current profile service structure
        return {"status": "updated", "updates": profile_updates}
```

### Phase 3: Tool Integration (Week 3-4)

#### 3.1 Product Discovery Tools

**File**: `backend/backend/application/agents/tools/product_tools.py`

```python
class ProductTools:
    """Product-related tools for Deep Agents"""

    def __init__(self, product_service, memory_service):
        self.product_service = product_service
        self.memory_service = memory_service

    async def search_products_tool(self, query: str, categories: list, user_id: str, memories: list = None):
        """Enhanced product search with memory context"""
        # Use memory to enhance search
        if not memories:
            memories = await self.memory_service.retrieve_contextual_memories(
                user_id, query, "product_preference"
            )

        # Generate search queries with memory context
        search_queries = await self._generate_search_queries_with_memory(
            query, categories, memories
        )

        # Execute search
        products = await self.product_service.search_products(search_queries)
        return {
            "products": products,
            "search_queries": search_queries,
            "memory_context": memories
        }

    async def create_product_bundles_tool(self, products: list, user_id: str, memories: list):
        """Create intelligent bundles using memory context"""
        bundles = await self.product_service.create_intelligent_bundles(
            products, user_id, memories
        )
        return {"bundles": bundles}

    async def _generate_search_queries_with_memory(self, query: str, categories: list, memories: list):
        """Generate search queries using memory context"""
        # This would use the existing search query generation logic
        # but enhanced with memory context
        pass
```

#### 3.2 Order Management Tools

**File**: `backend/backend/application/agents/tools/order_tools.py`

```python
class OrderTools:
    """Order-related tools for Deep Agents"""

    def __init__(self, order_service, order_graph_service):
        self.order_service = order_service
        self.order_graph_service = order_graph_service

    async def check_order_status_tool(self, user_email: str, order_id: str = None):
        """Check order status with comprehensive information"""
        if order_id:
            order = await self.order_service.get_order_by_id(order_id)
        else:
            orders = await self.order_service.get_user_orders(user_email)
            order = orders[0] if orders else None

        if order:
            order_details = await self.order_service.get_order_details(order.id)
            return {"order": order_details, "status": "found"}
        else:
            return {"error": "No orders found", "status": "not_found"}

    async def process_refund_tool(self, order_id: str, items: list, reason: str):
        """Process refund with proper validation"""
        eligibility = await self.order_service.check_refund_eligibility(order_id, items)

        if eligibility['eligible']:
            refund = await self.order_service.process_refund(order_id, items, reason)
            return {"refund": refund, "status": "processed"}
        else:
            return {"error": eligibility['reason'], "status": "not_eligible"}

    async def track_shipment_tool(self, order_id: str):
        """Track shipment for an order"""
        tracking_info = await self.order_service.get_shipment_tracking(order_id)
        return {"tracking": tracking_info}
```

### Phase 4: Advanced Features (Week 4-5)

#### 4.1 Health Advisory Integration

**File**: `backend/backend/application/agents/tools/health_tools.py`

```python
class HealthTools:
    """Health-related tools for Deep Agents"""

    def __init__(self, health_service, memory_service):
        self.health_service = health_service
        self.memory_service = memory_service

    async def get_health_advice_tool(self, user_query: str, user_id: str, memories: list):
        """Provide health advice with full context"""
        # Analyze user's health conditions from profile and memories
        health_context = await self._analyze_health_context(user_id, memories)

        # Get relevant health advice
        advice = await self.health_service.get_personalized_advice(
            user_query, health_context
        )

        # Check for drug interactions
        interactions = await self.health_service.check_interactions(
            health_context.get('medications', []),
            advice.get('supplements', [])
        )

        return {
            "advice": advice,
            "interactions": interactions,
            "health_context": health_context
        }

    async def _analyze_health_context(self, user_id: str, memories: list):
        """Analyze health context from memories and user profile"""
        # Implementation would analyze memories for health information
        # and combine with user profile data
        pass
```

#### 4.2 Sophisticated Planning Implementation

**File**: `backend/backend/application/agents/planning_engine.py`

```python
class PlanningEngine:
    """Advanced planning engine for Deep Agents"""

    def __init__(self, llm, memory_service):
        self.llm = llm
        self.memory_service = memory_service

    async def create_execution_plan(self, user_message: str, user_id: str, conversation_history: list):
        """Create execution plan based on user intent and context"""
        # Retrieve relevant memories
        memories = await self.memory_service.retrieve_contextual_memories(
            user_id, user_message
        )

        # Analyze intent and context
        intent_analysis = await self._analyze_intent(user_message, memories)

        # Create execution plan
        plan = await self._create_plan(intent_analysis, memories)

        return {
            "plan": plan,
            "memories": memories,
            "intent": intent_analysis
        }

    async def _analyze_intent(self, message: str, memories: list):
        """Analyze user intent using LLM"""
        # Use LLM to analyze intent and determine required sub-agents
        pass

    async def _create_plan(self, intent_analysis: dict, memories: list):
        """Create execution plan based on intent analysis"""
        # Create step-by-step execution plan
        pass
```

---

## Migration Strategy

### Phase 1: Parallel Implementation (Week 1-2)

1. **Install Deep Agents**: Add deepagents dependency
2. **Create Deep Agent Structure**: Implement main agent and sub-agents
3. **A/B Testing Setup**: Create feature flag for Deep Agents vs current workflow
4. **Basic Tool Integration**: Implement core tools (memory, product, order)

### Phase 2: Feature Parity (Week 3-4)

1. **Memory Integration**: Ensure all memory features work with Deep Agents
2. **Product Discovery**: Implement product search and bundling
3. **Order Management**: Implement order status and tracking
4. **Testing**: Comprehensive testing of all features

### Phase 3: Advanced Features (Week 4-5)

1. **Health Advisory**: Implement health advice capabilities
2. **Advanced Planning**: Implement sophisticated planning engine
3. **Performance Optimization**: Optimize LLM usage and response times
4. **Monitoring**: Add comprehensive monitoring and logging

### Phase 4: Full Migration (Week 5-6)

1. **Gradual Rollout**: Migrate users in batches
2. **Performance Monitoring**: Monitor performance metrics
3. **User Feedback**: Collect and analyze user feedback
4. **Legacy Cleanup**: Remove old workflow code

---

## Testing Strategy

### Unit Tests

- **Sub-Agent Tests**: Test each sub-agent independently
- **Tool Tests**: Test all tools with various inputs
- **Memory Integration Tests**: Test memory retrieval and storage
- **Planning Tests**: Test planning engine with different scenarios

### Integration Tests

- **End-to-End Tests**: Test complete user interactions
- **Memory Persistence Tests**: Test memory across sessions
- **Tool Coordination Tests**: Test sub-agent coordination
- **Performance Tests**: Test response times and LLM usage

### A/B Testing

- **User Experience**: Compare user satisfaction between old and new systems
- **Performance Metrics**: Compare response times and accuracy
- **LLM Usage**: Compare LLM call counts and costs
- **Feature Completeness**: Ensure all features work in new system

---

## Performance Expectations

### LLM Call Reduction

- **Current System**: 6-8 LLM calls per interaction
- **Deep Agents**: 2-3 LLM calls per interaction
- **Reduction**: 50-60% fewer LLM calls

### Response Time Improvement

- **Current System**: 3-5 seconds average response time
- **Deep Agents**: 1-3 seconds average response time
- **Improvement**: 40-60% faster responses

### Cost Reduction

- **LLM Costs**: 50-60% reduction in LLM API costs
- **Infrastructure**: Reduced server load due to fewer LLM calls
- **Maintenance**: Easier maintenance with cleaner architecture

### Scalability Improvements

- **Concurrent Users**: Better handling of multiple users
- **Memory Usage**: More efficient memory management
- **Tool Integration**: Easier addition of new tools and capabilities

---

## Rollback Plan

### Immediate Rollback (if critical issues)

1. **Feature Flag**: Disable Deep Agents via feature flag
2. **Route to Legacy**: Route all traffic to existing workflow
3. **Monitor**: Monitor system stability and user experience
4. **Investigate**: Investigate and fix issues in Deep Agents

### Gradual Rollback (if performance issues)

1. **Reduce Traffic**: Reduce percentage of users on Deep Agents
2. **Performance Analysis**: Analyze performance bottlenecks
3. **Optimization**: Implement performance optimizations
4. **Re-rollout**: Gradually increase traffic to Deep Agents

### Complete Rollback (if fundamental issues)

1. **Full Revert**: Revert to previous system version
2. **Data Migration**: Ensure no data loss during rollback
3. **User Communication**: Communicate changes to users
4. **Post-mortem**: Conduct post-mortem analysis

---

## Implementation Checklist

### Pre-Implementation

- [ ] Install deepagents dependency
- [ ] Set up development environment
- [ ] Create feature flags for A/B testing
- [ ] Set up monitoring and logging

### Phase 1: Core Setup

- [ ] Implement main Deep Agent
- [ ] Create sub-agent structure
- [ ] Implement basic tools
- [ ] Set up memory integration

### Phase 2: Feature Parity

- [ ] Implement product discovery tools
- [ ] Implement order management tools
- [ ] Implement health advisory tools
- [ ] Test all features

### Phase 3: Advanced Features

- [ ] Implement planning engine
- [ ] Add sophisticated memory management
- [ ] Implement advanced tool coordination
- [ ] Performance optimization

### Phase 4: Migration

- [ ] A/B testing setup
- [ ] Gradual user migration
- [ ] Performance monitoring
- [ ] Legacy code cleanup

### Post-Implementation

- [ ] Performance analysis
- [ ] User feedback collection
- [ ] Documentation updates
- [ ] Team training

---

## Key Files to Create/Modify

### New Files

- `backend/backend/application/agents/deep_agent.py`
- `backend/backend/application/agents/sub_agents.py`
- `backend/backend/application/agents/tools/memory_tools.py`
- `backend/backend/application/agents/tools/product_tools.py`
- `backend/backend/application/agents/tools/order_tools.py`
- `backend/backend/application/agents/tools/health_tools.py`
- `backend/backend/application/agents/planning_engine.py`
- `backend/backend/application/services/memory_integration.py`

### Modified Files

- `backend/backend/presentation/api/containers/application.py` (Add Deep Agent configuration)
- `backend/backend/application/use_cases/chat_session.py` (Add Deep Agent option)
- `backend/backend/application/workflows/enhanced_search_query_workflow.py` (Keep as fallback)

### Configuration Files

- `backend/backend/settings/deep_agents.py` (Deep Agents configuration)
- `backend/backend/application/agents/config.py` (Agent configuration)

---

## Success Metrics

### Technical Metrics

- **LLM Call Reduction**: Target 50% reduction in LLM calls
- **Response Time**: Target 40% improvement in response time
- **Memory Integration**: 100% feature parity with current memory system
- **Tool Coverage**: 100% coverage of current functionality

### Business Metrics

- **User Satisfaction**: Maintain or improve user satisfaction scores
- **Cost Reduction**: Achieve 50% reduction in LLM API costs
- **Feature Adoption**: Successful adoption of new use cases
- **System Reliability**: Maintain 99.9% uptime

### Development Metrics

- **Code Maintainability**: Improved code organization and maintainability
- **Feature Development**: Faster development of new features
- **Testing Coverage**: 90%+ test coverage for new components
- **Documentation**: Complete documentation for all new components

---

## Conclusion

This Deep Agents migration plan provides a comprehensive roadmap for modernizing the conversational commerce system. The new architecture will provide:

1. **Reduced Complexity**: Fewer LLM calls and better planning
2. **Improved Performance**: Faster responses and lower costs
3. **Enhanced Extensibility**: Easy addition of new use cases
4. **Better Memory Integration**: Seamless memory management
5. **Maintainable Architecture**: Cleaner, more organized code

The migration should be executed in phases with careful testing and monitoring to ensure a smooth transition and maintain system reliability.
