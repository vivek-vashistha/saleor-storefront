"""Feature flag service for A/B testing and gradual rollout."""

import logging
import hashlib
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

from backend.settings.deep_agents import deep_agents_config

logger = logging.getLogger("conversational_commerce.feature_flag")


class WorkflowType(Enum):
    """Available workflow types."""
    LEGACY = "legacy"
    DEEP_AGENTS = "deep_agents"


class FeatureFlagService:
    """Service for managing feature flags and A/B testing."""

    def __init__(self):
        """Initialize the feature flag service."""
        self.config = deep_agents_config
        self.ab_test_users = set()
        self.ab_test_start_time = None
        
        # Initialize A/B testing if enabled
        if self.config.a_b_testing_enabled:
            self._initialize_ab_testing()

    def _initialize_ab_testing(self) -> None:
        """Initialize A/B testing."""
        try:
            logger.info("Initializing A/B testing for Deep Agents")
            self.ab_test_start_time = datetime.now()
            
            # Generate random user IDs for A/B testing
            total_users = 1000  # This would come from your user database
            test_user_count = int(total_users * self.config.a_b_test_percentage)
            
            # Generate random user IDs for testing
            for _ in range(test_user_count):
                user_id = f"test_user_{random.randint(1000, 9999)}"
                self.ab_test_users.add(user_id)
            
            logger.info(f"A/B testing initialized with {len(self.ab_test_users)} test users")
            
        except Exception as e:
            logger.error(f"Error initializing A/B testing: {e}")

    def should_use_deep_agents(self, user_id: str) -> bool:
        """Determine if a user should use Deep Agents workflow.

        Args:
            user_id: The user's ID

        Returns:
            True if user should use Deep Agents, False for legacy
        """
        try:
            # Check if Deep Agents is globally enabled
            if not self.config.enabled:
                logger.info(f"Deep Agents globally disabled, using legacy for user {user_id}")
                return False
            
            # Check A/B testing
            if self.config.a_b_testing_enabled:
                return self._check_ab_test_eligibility(user_id)
            
            # Default to Deep Agents if enabled
            return True
            
        except Exception as e:
            logger.error(f"Error checking Deep Agents eligibility for user {user_id}: {e}")
            return False

    def _check_ab_test_eligibility(self, user_id: str) -> bool:
        """Check if user is eligible for A/B testing.

        Args:
            user_id: The user's ID

        Returns:
            True if user should use Deep Agents in A/B test
        """
        try:
            # Check if A/B test is still active
            if self.ab_test_start_time:
                test_duration = datetime.now() - self.ab_test_start_time
                if test_duration.days >= self.config.a_b_test_duration_days:
                    logger.info("A/B test duration expired, using Deep Agents for all users")
                    return True
            
            # Check if user is in A/B test group
            if user_id in self.ab_test_users:
                logger.info(f"User {user_id} is in A/B test group, using Deep Agents")
                return True
            
            # Use hash-based assignment for consistent user experience
            user_hash = self._hash_user_id(user_id)
            threshold = self.config.a_b_test_percentage
            
            if user_hash < threshold:
                logger.info(f"User {user_id} assigned to Deep Agents via hash")
                return True
            
            logger.info(f"User {user_id} assigned to legacy workflow")
            return False
            
        except Exception as e:
            logger.error(f"Error checking A/B test eligibility for user {user_id}: {e}")
            return False

    def _hash_user_id(self, user_id: str) -> float:
        """Generate a consistent hash for user ID.

        Args:
            user_id: The user's ID

        Returns:
            Hash value between 0 and 1
        """
        try:
            # Use SHA-256 for consistent hashing
            hash_obj = hashlib.sha256(user_id.encode())
            hash_hex = hash_obj.hexdigest()
            
            # Convert to float between 0 and 1
            hash_int = int(hash_hex[:8], 16)
            return hash_int / (16 ** 8)
            
        except Exception as e:
            logger.error(f"Error hashing user ID {user_id}: {e}")
            return random.random()

    def get_workflow_type(self, user_id: str) -> WorkflowType:
        """Get the workflow type for a user.

        Args:
            user_id: The user's ID

        Returns:
            WorkflowType enum value
        """
        try:
            if self.should_use_deep_agents(user_id):
                return WorkflowType.DEEP_AGENTS
            else:
                return WorkflowType.LEGACY
                
        except Exception as e:
            logger.error(f"Error getting workflow type for user {user_id}: {e}")
            return WorkflowType.LEGACY

    def get_feature_flags(self, user_id: str) -> Dict[str, Any]:
        """Get feature flags for a user.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary with feature flags
        """
        try:
            workflow_type = self.get_workflow_type(user_id)
            
            flags = {
                "workflow_type": workflow_type.value,
                "deep_agents_enabled": workflow_type == WorkflowType.DEEP_AGENTS,
                "ab_testing_enabled": self.config.a_b_testing_enabled,
                "fallback_enabled": self.config.fallback_to_legacy,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add Deep Agents specific flags
            if workflow_type == WorkflowType.DEEP_AGENTS:
                flags.update({
                    "product_expert_enabled": self.config.product_expert_enabled,
                    "order_specialist_enabled": self.config.order_specialist_enabled,
                    "health_advisor_enabled": self.config.health_advisor_enabled,
                    "memory_manager_enabled": self.config.memory_manager_enabled,
                    "planning_engine_enabled": self.config.planning_engine_enabled,
                    "memory_consolidation_enabled": self.config.memory_consolidation_enabled
                })
            
            return flags
            
        except Exception as e:
            logger.error(f"Error getting feature flags for user {user_id}: {e}")
            return {
                "workflow_type": "legacy",
                "deep_agents_enabled": False,
                "ab_testing_enabled": False,
                "fallback_enabled": True,
                "user_id": user_id,
                "error": str(e)
            }

    def get_ab_test_metrics(self) -> Dict[str, Any]:
        """Get A/B testing metrics.

        Returns:
            Dictionary with A/B test metrics
        """
        try:
            if not self.config.a_b_testing_enabled:
                return {"ab_testing_enabled": False}
            
            metrics = {
                "ab_testing_enabled": True,
                "test_start_time": self.ab_test_start_time.isoformat() if self.ab_test_start_time else None,
                "test_duration_days": self.config.a_b_test_duration_days,
                "test_percentage": self.config.a_b_test_percentage,
                "test_users_count": len(self.ab_test_users),
                "current_time": datetime.now().isoformat()
            }
            
            # Calculate test duration
            if self.ab_test_start_time:
                duration = datetime.now() - self.ab_test_start_time
                metrics["elapsed_days"] = duration.days
                metrics["is_expired"] = duration.days >= self.config.a_b_test_duration_days
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting A/B test metrics: {e}")
            return {"error": str(e)}

    def force_user_to_workflow(self, user_id: str, workflow_type: WorkflowType) -> bool:
        """Force a user to use a specific workflow type.

        Args:
            user_id: The user's ID
            workflow_type: The workflow type to force

        Returns:
            True if successful, False otherwise
        """
        try:
            if workflow_type == WorkflowType.DEEP_AGENTS:
                # Add user to A/B test group
                self.ab_test_users.add(user_id)
                logger.info(f"Forced user {user_id} to Deep Agents workflow")
            else:
                # Remove user from A/B test group
                self.ab_test_users.discard(user_id)
                logger.info(f"Forced user {user_id} to legacy workflow")
            
            return True
            
        except Exception as e:
            logger.error(f"Error forcing user {user_id} to workflow {workflow_type}: {e}")
            return False

    def reset_ab_test(self) -> bool:
        """Reset A/B testing.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.ab_test_users.clear()
            self.ab_test_start_time = None
            
            if self.config.a_b_testing_enabled:
                self._initialize_ab_testing()
            
            logger.info("A/B testing reset")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting A/B test: {e}")
            return False

    def get_user_assignment(self, user_id: str) -> Dict[str, Any]:
        """Get user assignment details.

        Args:
            user_id: The user's ID

        Returns:
            Dictionary with assignment details
        """
        try:
            workflow_type = self.get_workflow_type(user_id)
            user_hash = self._hash_user_id(user_id)
            
            assignment = {
                "user_id": user_id,
                "workflow_type": workflow_type.value,
                "user_hash": user_hash,
                "is_in_ab_test": user_id in self.ab_test_users,
                "ab_test_threshold": self.config.a_b_test_percentage,
                "assignment_reason": self._get_assignment_reason(user_id, user_hash)
            }
            
            return assignment
            
        except Exception as e:
            logger.error(f"Error getting user assignment for {user_id}: {e}")
            return {
                "user_id": user_id,
                "workflow_type": "legacy",
                "error": str(e)
            }

    def _get_assignment_reason(self, user_id: str, user_hash: float) -> str:
        """Get the reason for user assignment.

        Args:
            user_id: The user's ID
            user_hash: The user's hash value

        Returns:
            Assignment reason string
        """
        try:
            if not self.config.enabled:
                return "Deep Agents globally disabled"
            
            if user_id in self.ab_test_users:
                return "User in A/B test group"
            
            if user_hash < self.config.a_b_test_percentage:
                return "Hash-based assignment to Deep Agents"
            
            return "Hash-based assignment to legacy"
            
        except Exception as e:
            logger.error(f"Error getting assignment reason for {user_id}: {e}")
            return "Error determining assignment"


# Global feature flag service instance
feature_flag_service = FeatureFlagService()
