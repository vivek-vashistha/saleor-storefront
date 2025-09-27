"""Agent configuration for Deep Agents system."""

import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class SubAgentConfig(BaseModel):
    """Configuration for a sub-agent."""
    
    name: str = Field(description="Name of the sub-agent")
    enabled: bool = Field(default=True, description="Whether the sub-agent is enabled")
    priority: int = Field(default=1, description="Priority level (1=highest)")
    max_execution_time: int = Field(default=30, description="Maximum execution time in seconds")
    tools: List[str] = Field(default_factory=list, description="Available tools for the sub-agent")
    system_prompt: str = Field(description="System prompt for the sub-agent")


class ToolConfig(BaseModel):
    """Configuration for a tool."""
    
    name: str = Field(description="Name of the tool")
    enabled: bool = Field(default=True, description="Whether the tool is enabled")
    timeout: int = Field(default=10, description="Tool timeout in seconds")
    retry_count: int = Field(default=3, description="Number of retries on failure")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific parameters")


class AgentConfig:
    """Configuration manager for Deep Agents system."""
    
    def __init__(self):
        """Initialize agent configuration."""
        self.sub_agents = self._get_sub_agent_configs()
        self.tools = self._get_tool_configs()
        self.planning_engine = self._get_planning_engine_config()
    
    def _get_sub_agent_configs(self) -> Dict[str, SubAgentConfig]:
        """Get sub-agent configurations."""
        return {
            "product_expert": SubAgentConfig(
                name="product_expert",
                enabled=os.getenv("DEEP_AGENTS_PRODUCT_EXPERT", "true").lower() == "true",
                priority=1,
                max_execution_time=30,
                tools=["search_products", "get_product_details", "create_bundles", "check_availability"],
                system_prompt="You are a product expert specializing in health & wellness products. Focus on product recommendations, bundling, availability, and pricing. Always consider user's health conditions and preferences."
            ),
            "order_specialist": SubAgentConfig(
                name="order_specialist",
                enabled=os.getenv("DEEP_AGENTS_ORDER_SPECIALIST", "true").lower() == "true",
                priority=1,
                max_execution_time=30,
                tools=["check_order_status", "track_shipment", "process_refund", "get_order_history"],
                system_prompt="You are an order specialist handling order status, tracking, and returns. Focus on order lookup, shipment tracking, and refund processing. Always verify user identity and order details."
            ),
            "health_advisor": SubAgentConfig(
                name="health_advisor",
                enabled=os.getenv("DEEP_AGENTS_HEALTH_ADVISOR", "true").lower() == "true",
                priority=2,
                max_execution_time=30,
                tools=["get_health_advice", "check_interactions", "dosage_advice", "wellness_recommendations"],
                system_prompt="You are a health advisor providing wellness guidance. Focus on supplement advice, drug interactions, and dosage recommendations. Always recommend consulting healthcare providers for medical advice."
            ),
            "memory_manager": SubAgentConfig(
                name="memory_manager",
                enabled=os.getenv("DEEP_AGENTS_MEMORY_MANAGER", "true").lower() == "true",
                priority=3,
                max_execution_time=20,
                tools=["retrieve_memories", "store_memory", "update_user_profile", "consolidate_memories"],
                system_prompt="You are a memory manager responsible for user personalization. Focus on retrieving relevant memories, storing new information, updating user profiles, and consolidating memories."
            )
        }
    
    def _get_tool_configs(self) -> Dict[str, ToolConfig]:
        """Get tool configurations."""
        return {
            "retrieve_memories": ToolConfig(
                name="retrieve_memories",
                enabled=os.getenv("DEEP_AGENTS_MEMORY_TOOLS", "true").lower() == "true",
                timeout=10,
                retry_count=3,
                parameters={"max_memories": 5, "context_type": "general"}
            ),
            "store_memory": ToolConfig(
                name="store_memory",
                enabled=os.getenv("DEEP_AGENTS_MEMORY_TOOLS", "true").lower() == "true",
                timeout=10,
                retry_count=3,
                parameters={"memory_type": "conversation_context"}
            ),
            "search_products": ToolConfig(
                name="search_products",
                enabled=os.getenv("DEEP_AGENTS_PRODUCT_TOOLS", "true").lower() == "true",
                timeout=15,
                retry_count=2,
                parameters={"max_results": 10, "include_personalization": True}
            ),
            "get_product_details": ToolConfig(
                name="get_product_details",
                enabled=os.getenv("DEEP_AGENTS_PRODUCT_TOOLS", "true").lower() == "true",
                timeout=10,
                retry_count=2,
                parameters={"include_reviews": True, "include_alternatives": True}
            ),
            "check_order_status": ToolConfig(
                name="check_order_status",
                enabled=os.getenv("DEEP_AGENTS_ORDER_TOOLS", "true").lower() == "true",
                timeout=15,
                retry_count=3,
                parameters={"include_tracking": True, "include_items": True}
            ),
            "get_health_advice": ToolConfig(
                name="get_health_advice",
                enabled=os.getenv("DEEP_AGENTS_HEALTH_TOOLS", "true").lower() == "true",
                timeout=20,
                retry_count=2,
                parameters={"include_interactions": True, "include_dosage": True}
            )
        }
    
    def _get_planning_engine_config(self) -> Dict[str, Any]:
        """Get planning engine configuration."""
        return {
            "enabled": os.getenv("DEEP_AGENTS_PLANNING", "true").lower() == "true",
            "confidence_threshold": float(os.getenv("DEEP_AGENTS_CONFIDENCE_THRESHOLD", "0.6")),
            "optimization_enabled": os.getenv("DEEP_AGENTS_PLAN_OPTIMIZATION", "true").lower() == "true",
            "max_plan_steps": int(os.getenv("DEEP_AGENTS_MAX_PLAN_STEPS", "10")),
            "timeout": int(os.getenv("DEEP_AGENTS_PLANNING_TIMEOUT", "30"))
        }
    
    def get_sub_agent_config(self, name: str) -> Optional[SubAgentConfig]:
        """Get configuration for a specific sub-agent."""
        return self.sub_agents.get(name)
    
    def get_tool_config(self, name: str) -> Optional[ToolConfig]:
        """Get configuration for a specific tool."""
        return self.tools.get(name)
    
    def is_sub_agent_enabled(self, name: str) -> bool:
        """Check if a sub-agent is enabled."""
        config = self.get_sub_agent_config(name)
        return config.enabled if config else False
    
    def is_tool_enabled(self, name: str) -> bool:
        """Check if a tool is enabled."""
        config = self.get_tool_config(name)
        return config.enabled if config else False
    
    def get_enabled_sub_agents(self) -> List[str]:
        """Get list of enabled sub-agents."""
        return [name for name, config in self.sub_agents.items() if config.enabled]
    
    def get_enabled_tools(self) -> List[str]:
        """Get list of enabled tools."""
        return [name for name, config in self.tools.items() if config.enabled]
    
    def get_sub_agent_priority(self, name: str) -> int:
        """Get priority for a sub-agent."""
        config = self.get_sub_agent_config(name)
        return config.priority if config else 999
    
    def get_tool_timeout(self, name: str) -> int:
        """Get timeout for a tool."""
        config = self.get_tool_config(name)
        return config.timeout if config else 10


# Global configuration instance
agent_config = AgentConfig()
