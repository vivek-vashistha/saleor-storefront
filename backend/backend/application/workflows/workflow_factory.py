"""Workflow factory for managing different workflow types."""

import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime

from langchain_openai import ChatOpenAI

from backend.domain.entities.chat import ChatState
from backend.domain.entities.enhanced_chat import EnhancedChatState
from backend.application.interfaces import IChatWorkflow
from backend.application.services.feature_flag_service import feature_flag_service, WorkflowType
from backend.application.services.hybrid_memory_service import HybridMemoryService
from backend.application.services.semantic_memory_service import SemanticMemoryService, SemanticMemoryConfig
from backend.application.services.product_service import ProductService
from backend.application.services.order_graph_service import OrderGraphService
from backend.application.services.background_memory_manager import BackgroundMemoryManager
from backend.application.workflows.enhanced_search_query_workflow import EnhancedSearchQueryWorkflow
from backend.application.workflows.deep_agents_workflow import DeepAgentsWorkflow
from backend.settings.deep_agents import deep_agents_config

logger = logging.getLogger("conversational_commerce.workflow_factory")


class WorkflowFactory:
    """Factory for creating and managing different workflow types."""

    def __init__(
        self,
        llm: ChatOpenAI,
        memory_service: HybridMemoryService,
        product_service: ProductService,
        order_graph_service: Optional[OrderGraphService] = None,
        background_memory_manager: Optional[BackgroundMemoryManager] = None,
        agent_factory=None
    ):
        """Initialize the workflow factory.

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
        
        # Initialize workflows
        self._initialize_workflows()
        
        logger.info("Workflow factory initialized")

    def _initialize_workflows(self) -> None:
        """Initialize available workflows."""
        try:
            # Create SemanticMemoryService for consistent memory handling
            semantic_memory_config = SemanticMemoryConfig(
                openai_api_key="dummy_key",  # Will be overridden by actual config
                embedding_model="text-embedding-3-small",
                llm_model="gpt-4o-mini"
            )
            semantic_memory_service = SemanticMemoryService(
                config=semantic_memory_config,
                hybrid_memory_service=self.memory_service
            )
            
            # Initialize legacy workflow
            self.legacy_workflow = EnhancedSearchQueryWorkflow(
                llm=self.llm,
                semantic_memory_service=semantic_memory_service,
                background_memory_manager=self.background_memory_manager,
                agent_factory=self.agent_factory
            )
            
            # Initialize Deep Agents workflow with SemanticMemoryService
            self.deep_agents_workflow = DeepAgentsWorkflow(
                llm=self.llm,
                memory_service=semantic_memory_service,
                product_service=self.product_service,
                order_graph_service=self.order_graph_service,
                background_memory_manager=self.background_memory_manager
            )
            
            logger.info("Workflows initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing workflows: {e}")
            raise

    def get_workflow_for_user(self, user_id: str) -> IChatWorkflow:
        """Get the appropriate workflow for a user.

        Args:
            user_id: The user's ID

        Returns:
            The appropriate workflow instance
        """
        try:
            # Get workflow type from feature flags
            workflow_type = feature_flag_service.get_workflow_type(user_id)
            
            logger.info(f"Selected workflow for user {user_id}: {workflow_type.value}")
            
            if workflow_type == WorkflowType.DEEP_AGENTS:
                return self.deep_agents_workflow
            else:
                return self.legacy_workflow
                
        except Exception as e:
            logger.error(f"Error getting workflow for user {user_id}: {e}")
            # Check if fallback is enabled
            if deep_agents_config.fallback_to_legacy:
                logger.warning(f"Falling back to legacy workflow for user {user_id}")
                return self.legacy_workflow
            else:
                logger.error(f"No fallback enabled, raising error for user {user_id}")
                raise

    async def process_message(
        self,
        state: Union[ChatState, EnhancedChatState],
        user_id: str,
        message_content: str,
        referenced_product_ids: Optional[list] = None
    ) -> Union[ChatState, EnhancedChatState]:
        """Process a message using the appropriate workflow.

        Args:
            state: The chat state
            user_id: The user's ID
            message_content: The message content
            referenced_product_ids: Optional referenced product IDs

        Returns:
            Updated chat state
        """
        try:
            logger.info(f"Processing message for user {user_id} with workflow factory")
            
            # Get the appropriate workflow
            workflow = self.get_workflow_for_user(user_id)
            
            # Add the user message to the state
            state.add_message(message_content)
            
            # Handle referenced products if provided
            if referenced_product_ids:
                referenced_products = await self.product_service.get_products_by_ids(referenced_product_ids)
                state.referenced_products = referenced_products
            else:
                state.referenced_products = []
            
            # Process with the selected workflow
            result_state = await workflow.run(state)
            
            # Log workflow metrics
            await self._log_workflow_metrics(user_id, workflow, result_state)
            
            logger.info(f"Message processed for user {user_id}")
            return result_state
            
        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            
            # Check if fallback is enabled
            if deep_agents_config.fallback_to_legacy:
                logger.info(f"Falling back to legacy workflow for user {user_id}")
                try:
                    fallback_result = await self.legacy_workflow.run(state)
                    return fallback_result
                except Exception as fallback_error:
                    logger.error(f"Fallback workflow also failed for user {user_id}: {fallback_error}")
                    # Add error message to state
                    state.add_message(
                        "I'm sorry, I encountered an error processing your request. Please try again.",
                        is_human=False
                    )
                    return state
            else:
                logger.error(f"No fallback enabled, raising error for user {user_id}")
                # Add error message to state
                state.add_message(
                    "I'm sorry, I encountered an error processing your request. Please try again.",
                    is_human=False
                )
                return state

    async def _log_workflow_metrics(
        self,
        user_id: str,
        workflow: IChatWorkflow,
        result_state: Union[ChatState, EnhancedChatState]
    ) -> None:
        """Log workflow metrics for monitoring.

        Args:
            user_id: The user's ID
            workflow: The workflow used
            result_state: The result state
        """
        try:
            if deep_agents_config.metrics_enabled:
                metrics = {
                    "user_id": user_id,
                    "workflow_type": workflow.__class__.__name__,
                    "message_count": len(result_state.messages),
                    "has_user_profile": hasattr(result_state, 'user_profile') and result_state.user_profile is not None,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Add Deep Agents specific metrics
                if hasattr(workflow, 'get_workflow_metrics'):
                    workflow_metrics = await workflow.get_workflow_metrics(result_state)
                    metrics.update(workflow_metrics)
                
                logger.info(f"Workflow metrics for user {user_id}: {metrics}")
                
        except Exception as e:
            logger.error(f"Error logging workflow metrics for user {user_id}: {e}")

    def get_workflow_info(self, user_id: str) -> Dict[str, Any]:
        """Get information about the workflow for a user.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary with workflow information
        """
        try:
            workflow_type = feature_flag_service.get_workflow_type(user_id)
            feature_flags = feature_flag_service.get_feature_flags(user_id)
            
            info = {
                "user_id": user_id,
                "workflow_type": workflow_type.value,
                "feature_flags": feature_flags,
                "available_workflows": ["legacy", "deep_agents"],
                "fallback_enabled": deep_agents_config.fallback_to_legacy,
                "timestamp": datetime.now().isoformat()
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting workflow info for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "workflow_type": "legacy",
                "error": str(e)
            }

    def force_user_workflow(self, user_id: str, workflow_type: WorkflowType) -> bool:
        """Force a user to use a specific workflow type.

        Args:
            user_id: The user's ID
            workflow_type: The workflow type to force

        Returns:
            True if successful, False otherwise
        """
        try:
            success = feature_flag_service.force_user_to_workflow(user_id, workflow_type)
            
            if success:
                logger.info(f"Forced user {user_id} to {workflow_type.value} workflow")
            else:
                logger.warning(f"Failed to force user {user_id} to {workflow_type.value} workflow")
            
            return success
            
        except Exception as e:
            logger.error(f"Error forcing user {user_id} to workflow {workflow_type}: {e}")
            return False

    def get_ab_test_metrics(self) -> Dict[str, Any]:
        """Get A/B testing metrics.

        Returns:
            Dictionary with A/B test metrics
        """
        try:
            return feature_flag_service.get_ab_test_metrics()
            
        except Exception as e:
            logger.error(f"Error getting A/B test metrics: {e}")
            return {"error": str(e)}

    def reset_ab_test(self) -> bool:
        """Reset A/B testing.

        Returns:
            True if successful, False otherwise
        """
        try:
            success = feature_flag_service.reset_ab_test()
            
            if success:
                logger.info("A/B testing reset successfully")
            else:
                logger.warning("Failed to reset A/B testing")
            
            return success
            
        except Exception as e:
            logger.error(f"Error resetting A/B test: {e}")
            return False

    async def optimize_workflow_for_user(
        self,
        user_id: str,
        optimization_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Optimize workflow for a specific user.

        Args:
            user_id: The user's ID
            optimization_data: Data for optimization

        Returns:
            Dictionary with optimization results
        """
        try:
            logger.info(f"Optimizing workflow for user {user_id}")
            
            # Get the current workflow
            workflow = self.get_workflow_for_user(user_id)
            
            # Optimize if the workflow supports it
            if hasattr(workflow, 'optimize_for_user'):
                result = await workflow.optimize_for_user(user_id, optimization_data or {})
                logger.info(f"Workflow optimized for user {user_id}")
                return result
            else:
                logger.info(f"Workflow {workflow.__class__.__name__} does not support optimization")
                return {
                    "user_id": user_id,
                    "optimization_applied": False,
                    "reason": "Workflow does not support optimization"
                }
                
        except Exception as e:
            logger.error(f"Error optimizing workflow for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "optimization_applied": False,
                "error": str(e)
            }
