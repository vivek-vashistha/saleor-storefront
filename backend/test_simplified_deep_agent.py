"""Test script for the simplified deep agent integration."""

import asyncio
import logging
from unittest.mock import Mock, AsyncMock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simplified_deep_agent_integration():
    """Test that the simplified deep agent integrates correctly."""
    try:
        # Mock the dependencies
        mock_llm = Mock()
        mock_memory_service = Mock()
        mock_product_service = Mock()
        mock_order_graph_service = Mock()
        
        # Mock the memory service methods
        mock_memory_service.retrieve_relevant_memories = AsyncMock(return_value=[])
        
        # Import the simplified agent
        from backend.application.agents.simplified_deep_agent import SimplifiedConversationalCommerceAgent
        
        # Create the agent
        agent = SimplifiedConversationalCommerceAgent(
            llm=mock_llm,
            memory_service=mock_memory_service,
            product_service=mock_product_service,
            order_graph_service=mock_order_graph_service
        )
        
        logger.info("✅ Simplified Deep Agent created successfully")
        
        # Test the agent interface
        assert hasattr(agent, 'process_message')
        assert hasattr(agent, 'process_chat_state')
        logger.info("✅ Agent has required methods")
        
        # Test sub-agent creation
        sub_agents = agent._get_sub_agents()
        assert len(sub_agents) == 4
        assert any(agent['name'] == 'product_expert' for agent in sub_agents)
        assert any(agent['name'] == 'order_specialist' for agent in sub_agents)
        assert any(agent['name'] == 'health_advisor' for agent in sub_agents)
        assert any(agent['name'] == 'memory_manager' for agent in sub_agents)
        logger.info("✅ Sub-agents created correctly")
        
        # Test tools creation
        tools = agent._get_all_tools()
        assert len(tools) > 0
        logger.info("✅ Tools created correctly")
        
        logger.info("🎉 Simplified Deep Agent integration test passed!")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.info("This is expected if the Deep Agents framework is not available")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def test_workflow_integration():
    """Test that the workflow uses the simplified agent."""
    try:
        # Mock the dependencies
        mock_llm = Mock()
        mock_memory_service = Mock()
        mock_product_service = Mock()
        mock_order_graph_service = Mock()
        
        # Import the workflow
        from backend.application.workflows.deep_agents_workflow import DeepAgentsWorkflow
        
        # Create the workflow
        workflow = DeepAgentsWorkflow(
            llm=mock_llm,
            memory_service=mock_memory_service,
            product_service=mock_product_service,
            order_graph_service=mock_order_graph_service
        )
        
        logger.info("✅ DeepAgentsWorkflow created successfully")
        
        # Check that it uses the simplified agent
        assert hasattr(workflow, 'deep_agent')
        assert workflow.deep_agent.__class__.__name__ == 'SimplifiedConversationalCommerceAgent'
        logger.info("✅ Workflow uses SimplifiedConversationalCommerceAgent")
        
        logger.info("🎉 Workflow integration test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Workflow test failed: {e}")
        return False

async def main():
    """Run all integration tests."""
    logger.info("🧪 Testing Simplified Deep Agent Integration")
    logger.info("=" * 50)
    
    # Test 1: Simplified Deep Agent
    logger.info("\n1. Testing Simplified Deep Agent...")
    agent_test_passed = await test_simplified_deep_agent_integration()
    
    # Test 2: Workflow Integration
    logger.info("\n2. Testing Workflow Integration...")
    workflow_test_passed = await test_workflow_integration()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 Test Results:")
    logger.info(f"   Simplified Deep Agent: {'✅ PASSED' if agent_test_passed else '❌ FAILED'}")
    logger.info(f"   Workflow Integration: {'✅ PASSED' if workflow_test_passed else '❌ FAILED'}")
    
    if agent_test_passed and workflow_test_passed:
        logger.info("🎉 All tests passed! Integration is working correctly.")
    else:
        logger.info("⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    asyncio.run(main())
