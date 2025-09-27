"""Interface for Deep Agent in conversational commerce system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DeepAgentResponse(BaseModel):
    """Response structure for Deep Agent."""
    response: str
    sub_agent_used: Optional[str] = None
    tools_used: List[str] = []
    memories_retrieved: int = 0
    confidence: float = 0.0
    reasoning: str = ""


class IDeepAgent(ABC):
    """Interface for Deep Agent implementations.
    
    This interface defines the contract for Deep Agent implementations
    in the conversational commerce system, following clean architecture principles.
    """

    @abstractmethod
    async def process_message(
        self,
        user_message: str,
        user_id: str,
        context: Dict[str, Any]
    ) -> DeepAgentResponse:
        """Process a user message using Deep Agent architecture.
        
        Args:
            user_message: The user's message
            user_id: User identifier
            context: Additional context for processing
            
        Returns:
            Deep Agent response with sub-agent information
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_available_sub_agents(self) -> List[str]:
        """Get list of available sub-agent types.
        
        Returns:
            List of available sub-agent type names
        """
        pass

    @abstractmethod
    def get_sub_agent_descriptions(self) -> List[str]:
        """Get descriptions of all sub-agents for task delegation.
        
        Returns:
            List of sub-agent descriptions
        """
        pass
