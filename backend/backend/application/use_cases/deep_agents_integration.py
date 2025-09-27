"""Integration example for Deep Agents workflow."""

import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime

from langchain_openai import ChatOpenAI

from backend.domain.entities.chat import ChatState, UserProfile
from backend.domain.entities.enhanced_chat import EnhancedChatState
from backend.application.workflows.workflow_factory import WorkflowFactory
from backend.application.services.hybrid_memory_service import HybridMemoryService
from backend.application.services.product_service import ProductService
from backend.application.services.order_graph_service import OrderGraphService
from backend.application.services.background_memory_manager import BackgroundMemoryManager

logger = logging.getLogger("conversational_commerce.deep_agents_integration")


class DeepAgentsIntegration:
    """Integration class for Deep Agents workflow."""

    def __init__(
        self,
        llm: ChatOpenAI,
        memory_service: HybridMemoryService,
        product_service: ProductService,
        order_graph_service: Optional[OrderGraphService] = None,
        background_memory_manager: Optional[BackgroundMemoryManager] = None,
        agent_factory=None
    ):
        """Initialize the Deep Agents integration.

        Args:
            llm: Language model instance
            memory_service: Memory service for user context
            product_service: Product service for recommendations
            order_graph_service: Order service for order management
            background_memory_manager: Background memory manager
            agent_factory: Agent factory for legacy workflows
        """
        self.llm = llm
        self.memory_service = memory_service
        self.product_service = product_service
        self.order_graph_service = order_graph_service
        self.background_memory_manager = background_memory_manager
        self.agent_factory = agent_factory
        
        # Initialize workflow factory
        self.workflow_factory = WorkflowFactory(
            llm=llm,
            memory_service=memory_service,
            product_service=product_service,
            order_graph_service=order_graph_service,
            background_memory_manager=background_memory_manager,
            agent_factory=agent_factory
        )
        
        logger.info("Deep Agents integration initialized")

    async def process_chat_message(
        self,
        user_id: str,
        message_content: str,
        session_id: Optional[str] = None,
        referenced_product_ids: Optional[list] = None
    ) -> Dict[str, Any]:
        """Process a chat message using the appropriate workflow.

        Args:
            user_id: The user's ID
            message_content: The message content
            session_id: Optional session ID
            referenced_product_ids: Optional referenced product IDs

        Returns:
            Dictionary with processing results
        """
        try:
            logger.info(f"Processing chat message for user {user_id}: {message_content[:50]}...")
            
            # Create initial chat state
            state = ChatState(
                messages=[],
                search_queries=[],
                user_id=user_id,
                user_profile=UserProfile()
            )
            
            # Process with workflow factory
            result_state = await self.workflow_factory.process_message(
                state=state,
                user_id=user_id,
                message_content=message_content,
                referenced_product_ids=referenced_product_ids
            )
            
            # Extract response
            response = ""
            for msg in reversed(result_state.messages):
                if msg.get('type') == 'ai':
                    content = msg.get('content', '')
                    if isinstance(content, list):
                        content = ' '.join(str(item) for item in content)
                    response = str(content)
                    break
            
            # Get workflow info
            workflow_info = self.workflow_factory.get_workflow_info(user_id)
            
            result = {
                "user_id": user_id,
                "response": response,
                "workflow_used": workflow_info.get("workflow_type"),
                "message_count": len(result_state.messages),
                "has_user_profile": hasattr(result_state, 'user_profile') and result_state.user_profile is not None,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Chat message processed for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing chat message for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "response": "I'm sorry, I encountered an error processing your request. Please try again.",
                "workflow_used": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def get_user_workflow_info(self, user_id: str) -> Dict[str, Any]:
        """Get workflow information for a user.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary with workflow information
        """
        try:
            return self.workflow_factory.get_workflow_info(user_id)
            
        except Exception as e:
            logger.error(f"Error getting workflow info for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "error": str(e)
            }

    async def force_user_workflow(
        self,
        user_id: str,
        workflow_type: str
    ) -> Dict[str, Any]:
        """Force a user to use a specific workflow type.

        Args:
            user_id: The user's ID
            workflow_type: The workflow type to force

        Returns:
            Dictionary with operation results
        """
        try:
            from backend.application.services.feature_flag_service import WorkflowType
            
            # Convert string to enum
            if workflow_type.lower() == "deep_agents":
                workflow_enum = WorkflowType.DEEP_AGENTS
            else:
                workflow_enum = WorkflowType.LEGACY
            
            success = self.workflow_factory.force_user_workflow(user_id, workflow_enum)
            
            return {
                "user_id": user_id,
                "workflow_type": workflow_type,
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error forcing workflow for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "workflow_type": workflow_type,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def get_ab_test_metrics(self) -> Dict[str, Any]:
        """Get A/B testing metrics.

        Returns:
            Dictionary with A/B test metrics
        """
        try:
            return self.workflow_factory.get_ab_test_metrics()
            
        except Exception as e:
            logger.error(f"Error getting A/B test metrics: {e}")
            return {"error": str(e)}

    async def reset_ab_test(self) -> Dict[str, Any]:
        """Reset A/B testing.

        Returns:
            Dictionary with operation results
        """
        try:
            success = self.workflow_factory.reset_ab_test()
            
            return {
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error resetting A/B test: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
