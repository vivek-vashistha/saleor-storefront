"""Deep Agents configuration settings."""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DeepAgentsConfig(BaseModel):
    """Configuration for Deep Agents system."""
    
    # Feature flags
    enabled: bool = Field(default=True, description="Enable Deep Agents workflow")
    a_b_testing_enabled: bool = Field(default=False, description="Enable A/B testing")
    fallback_to_legacy: bool = Field(default=True, description="Fallback to legacy workflow on error")
    
    # Performance settings
    max_memories_per_query: int = Field(default=5, description="Maximum memories to retrieve per query")
    max_conversation_history: int = Field(default=10, description="Maximum conversation history to include")
    response_timeout: int = Field(default=30, description="Response timeout in seconds")
    
    # Sub-agent settings
    product_expert_enabled: bool = Field(default=True, description="Enable Product Expert sub-agent")
    order_specialist_enabled: bool = Field(default=True, description="Enable Order Specialist sub-agent")
    health_advisor_enabled: bool = Field(default=True, description="Enable Health Advisor sub-agent")
    memory_manager_enabled: bool = Field(default=True, description="Enable Memory Manager sub-agent")
    
    # Tool settings
    memory_tools_enabled: bool = Field(default=True, description="Enable memory tools")
    product_tools_enabled: bool = Field(default=True, description="Enable product tools")
    order_tools_enabled: bool = Field(default=True, description="Enable order tools")
    health_tools_enabled: bool = Field(default=True, description="Enable health tools")
    
    # Planning engine settings
    planning_engine_enabled: bool = Field(default=True, description="Enable planning engine")
    intent_analysis_confidence_threshold: float = Field(default=0.6, description="Minimum confidence for intent analysis")
    plan_optimization_enabled: bool = Field(default=True, description="Enable plan optimization")
    
    # Memory integration settings
    memory_consolidation_enabled: bool = Field(default=True, description="Enable memory consolidation")
    background_processing_enabled: bool = Field(default=True, description="Enable background processing")
    memory_retention_days: int = Field(default=90, description="Memory retention period in days")
    
    # Monitoring settings
    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")
    logging_level: str = Field(default="INFO", description="Logging level")
    performance_monitoring: bool = Field(default=True, description="Enable performance monitoring")
    
    # A/B testing settings
    a_b_test_percentage: float = Field(default=0.5, description="Percentage of users for A/B testing")
    a_b_test_duration_days: int = Field(default=7, description="A/B test duration in days")
    
    @classmethod
    def from_env(cls) -> "DeepAgentsConfig":
        """Create configuration from environment variables."""
        return cls(
            enabled=os.getenv("DEEP_AGENTS_ENABLED", "true").lower() == "true",
            a_b_testing_enabled=os.getenv("DEEP_AGENTS_AB_TESTING", "false").lower() == "true",
            fallback_to_legacy=os.getenv("DEEP_AGENTS_FALLBACK", "true").lower() == "true",
            max_memories_per_query=int(os.getenv("DEEP_AGENTS_MAX_MEMORIES", "5")),
            max_conversation_history=int(os.getenv("DEEP_AGENTS_MAX_HISTORY", "10")),
            response_timeout=int(os.getenv("DEEP_AGENTS_TIMEOUT", "30")),
            product_expert_enabled=os.getenv("DEEP_AGENTS_PRODUCT_EXPERT", "true").lower() == "true",
            order_specialist_enabled=os.getenv("DEEP_AGENTS_ORDER_SPECIALIST", "true").lower() == "true",
            health_advisor_enabled=os.getenv("DEEP_AGENTS_HEALTH_ADVISOR", "true").lower() == "true",
            memory_manager_enabled=os.getenv("DEEP_AGENTS_MEMORY_MANAGER", "true").lower() == "true",
            memory_tools_enabled=os.getenv("DEEP_AGENTS_MEMORY_TOOLS", "true").lower() == "true",
            product_tools_enabled=os.getenv("DEEP_AGENTS_PRODUCT_TOOLS", "true").lower() == "true",
            order_tools_enabled=os.getenv("DEEP_AGENTS_ORDER_TOOLS", "true").lower() == "true",
            health_tools_enabled=os.getenv("DEEP_AGENTS_HEALTH_TOOLS", "true").lower() == "true",
            planning_engine_enabled=os.getenv("DEEP_AGENTS_PLANNING", "true").lower() == "true",
            intent_analysis_confidence_threshold=float(os.getenv("DEEP_AGENTS_CONFIDENCE_THRESHOLD", "0.6")),
            plan_optimization_enabled=os.getenv("DEEP_AGENTS_PLAN_OPTIMIZATION", "true").lower() == "true",
            memory_consolidation_enabled=os.getenv("DEEP_AGENTS_MEMORY_CONSOLIDATION", "true").lower() == "true",
            background_processing_enabled=os.getenv("DEEP_AGENTS_BACKGROUND_PROCESSING", "true").lower() == "true",
            memory_retention_days=int(os.getenv("DEEP_AGENTS_MEMORY_RETENTION", "90")),
            metrics_enabled=os.getenv("DEEP_AGENTS_METRICS", "true").lower() == "true",
            logging_level=os.getenv("DEEP_AGENTS_LOG_LEVEL", "INFO"),
            performance_monitoring=os.getenv("DEEP_AGENTS_PERFORMANCE_MONITORING", "true").lower() == "true",
            a_b_test_percentage=float(os.getenv("DEEP_AGENTS_AB_TEST_PERCENTAGE", "0.5")),
            a_b_test_duration_days=int(os.getenv("DEEP_AGENTS_AB_TEST_DURATION", "7"))
        )


# Global configuration instance
deep_agents_config = DeepAgentsConfig.from_env()
