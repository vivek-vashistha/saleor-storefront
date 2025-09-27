"""Deep Agents implementation for conversational commerce."""

# Import only the working V2 version to avoid dependency issues
from .simplified_deep_agent_v2 import SimplifiedConversationalCommerceAgentV2

# Conditional imports to avoid dependency issues
try:
    from .deep_agent import ConversationalCommerceDeepAgent
    from .sub_agents import (
        ProductExpertSubAgent,
        OrderSpecialistSubAgent,
        HealthAdvisorSubAgent,
        MemoryManagerSubAgent
    )
    from .tools.memory_tools import MemoryTools
    from .tools.product_tools import ProductTools
    from .tools.order_tools import OrderTools
    from .tools.health_tools import HealthTools
    from .planning_engine import PlanningEngine
    
    __all__ = [
        "ConversationalCommerceDeepAgent",
        "SimplifiedConversationalCommerceAgentV2",
        "ProductExpertSubAgent",
        "OrderSpecialistSubAgent", 
        "HealthAdvisorSubAgent",
        "MemoryManagerSubAgent",
        "MemoryTools",
        "ProductTools",
        "OrderTools",
        "HealthTools",
        "PlanningEngine"
    ]
except ImportError as e:
    # If there are dependency issues, only export the working V2 version
    __all__ = [
        "SimplifiedConversationalCommerceAgentV2"
    ]
