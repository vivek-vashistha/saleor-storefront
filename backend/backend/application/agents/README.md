# Deep Agents Implementation

This directory contains the Deep Agents implementation for the conversational commerce system, following the migration plan outlined in the main documentation.

## Architecture Overview

The Deep Agents system implements a sophisticated conversational AI architecture that reduces LLM calls from 6-8 per interaction to 2-3 per interaction while improving planning capabilities and system extensibility.

### Core Components

1. **Main Deep Agent** (`deep_agent.py`)

   - Central orchestrator for all conversations
   - Implements single planning call approach
   - Coordinates sub-agents and tools
   - Synthesizes final responses

2. **Sub-Agents** (`sub_agents.py`)

   - **Product Expert**: Specialized for product discovery and recommendations
   - **Order Specialist**: Handles order status, tracking, and returns
   - **Health Advisor**: Provides health and wellness guidance
   - **Memory Manager**: Manages user personalization and memory operations

3. **Tools** (`tools/`)

   - **Memory Tools**: Retrieve, store, and manage user memories
   - **Product Tools**: Search products, get details, create bundles
   - **Order Tools**: Check status, track shipments, process refunds
   - **Health Tools**: Provide health advice, check interactions

4. **Planning Engine** (`planning_engine.py`)
   - Analyzes user intent and context
   - Creates execution plans
   - Optimizes workflow execution
   - Validates plan feasibility

## Key Features

### LLM Call Reduction

- **Current System**: 6-8 LLM calls per interaction
- **Deep Agents**: 2-3 LLM calls per interaction
- **Reduction**: 50-60% fewer LLM calls

### Memory Integration

- Seamless integration with existing memory systems
- Contextual memory retrieval
- Automatic memory consolidation
- User profile updates

### Sub-Agent Specialization

- Domain-specific expertise
- Intelligent tool selection
- Parallel processing capabilities
- Fallback mechanisms

### Planning Engine

- Intent analysis and classification
- Execution plan generation
- Resource optimization
- Performance monitoring

## Usage

### Basic Integration

```python
from backend.application.workflows.workflow_factory import WorkflowFactory
from backend.application.services.feature_flag_service import feature_flag_service

# Initialize workflow factory
workflow_factory = WorkflowFactory(
    llm=llm,
    memory_service=memory_service,
    product_service=product_service,
    order_graph_service=order_graph_service
)

# Get workflow for user
workflow = workflow_factory.get_workflow_for_user(user_id)

# Process message
result_state = await workflow.run(chat_state)
```

### Feature Flags

```python
# Check if user should use Deep Agents
should_use_deep_agents = feature_flag_service.should_use_deep_agents(user_id)

# Get workflow type
workflow_type = feature_flag_service.get_workflow_type(user_id)

# Force user to specific workflow
feature_flag_service.force_user_to_workflow(user_id, WorkflowType.DEEP_AGENTS)
```

### A/B Testing

```python
# Get A/B test metrics
metrics = feature_flag_service.get_ab_test_metrics()

# Reset A/B testing
feature_flag_service.reset_ab_test()
```

## Configuration

### Environment Variables

```bash
# Enable Deep Agents
DEEP_AGENTS_ENABLED=true

# Enable A/B testing
DEEP_AGENTS_AB_TESTING=true

# A/B test percentage
DEEP_AGENTS_AB_TEST_PERCENTAGE=0.5

# Sub-agent settings
DEEP_AGENTS_PRODUCT_EXPERT=true
DEEP_AGENTS_ORDER_SPECIALIST=true
DEEP_AGENTS_HEALTH_ADVISOR=true
DEEP_AGENTS_MEMORY_MANAGER=true

# Tool settings
DEEP_AGENTS_MEMORY_TOOLS=true
DEEP_AGENTS_PRODUCT_TOOLS=true
DEEP_AGENTS_ORDER_TOOLS=true
DEEP_AGENTS_HEALTH_TOOLS=true

# Planning engine
DEEP_AGENTS_PLANNING=true
DEEP_AGENTS_CONFIDENCE_THRESHOLD=0.6
```

### Configuration Files

- `backend/settings/deep_agents.py`: Main configuration
- `backend/application/agents/config.py`: Agent-specific configuration

## Performance Expectations

### Response Time

- **Current System**: 3-5 seconds average
- **Deep Agents**: 1-3 seconds average
- **Improvement**: 40-60% faster responses

### Cost Reduction

- **LLM Costs**: 50-60% reduction
- **Infrastructure**: Reduced server load
- **Maintenance**: Easier maintenance

### Scalability

- Better concurrent user handling
- More efficient memory management
- Easier addition of new capabilities

## Monitoring

### Metrics Collection

- Workflow performance metrics
- Sub-agent usage statistics
- Tool execution times
- Memory retrieval efficiency

### A/B Testing

- User assignment tracking
- Performance comparison
- Conversion rate analysis
- User satisfaction metrics

## Migration Strategy

### Phase 1: Parallel Implementation

1. Install Deep Agents dependencies
2. Create Deep Agent structure
3. Set up A/B testing
4. Implement basic tool integration

### Phase 2: Feature Parity

1. Memory integration
2. Product discovery
3. Order management
4. Comprehensive testing

### Phase 3: Advanced Features

1. Health advisory
2. Advanced planning
3. Performance optimization
4. Monitoring setup

### Phase 4: Full Migration

1. Gradual user rollout
2. Performance monitoring
3. User feedback collection
4. Legacy code cleanup

## Testing

### Unit Tests

- Sub-agent functionality
- Tool operations
- Memory integration
- Planning engine

### Integration Tests

- End-to-end workflows
- Memory persistence
- Tool coordination
- Performance testing

### A/B Testing

- User experience comparison
- Performance metrics
- Feature completeness
- Cost analysis

## Troubleshooting

### Common Issues

1. **Sub-agent not responding**

   - Check agent configuration
   - Verify tool availability
   - Review timeout settings

2. **Memory retrieval failures**

   - Check memory service connection
   - Verify user permissions
   - Review memory consolidation

3. **Planning engine errors**
   - Check LLM configuration
   - Verify intent analysis
   - Review plan validation

### Debugging

```python
# Enable debug logging
import logging
logging.getLogger("conversational_commerce.deep_agent").setLevel(logging.DEBUG)

# Check workflow info
workflow_info = workflow_factory.get_workflow_info(user_id)
print(workflow_info)

# Get A/B test metrics
metrics = feature_flag_service.get_ab_test_metrics()
print(metrics)
```

## Future Enhancements

1. **Advanced Planning**

   - Multi-step task execution
   - Dynamic plan adjustment
   - Resource optimization

2. **Enhanced Memory**

   - Semantic memory consolidation
   - Context-aware retrieval
   - Long-term memory management

3. **Sub-agent Specialization**

   - Domain-specific training
   - Custom tool development
   - Performance optimization

4. **Monitoring and Analytics**
   - Real-time performance metrics
   - User behavior analysis
   - Cost optimization

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review configuration settings
3. Enable debug logging
4. Contact the development team
