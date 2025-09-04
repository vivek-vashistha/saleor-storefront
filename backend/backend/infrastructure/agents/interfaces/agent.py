from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from langchain_core.language_models import BaseChatModel

StateT = TypeVar("StateT")


class IAgent(Generic[StateT], ABC):
    """Interface for agents in the conversation system."""

    def __init__(self, llm: BaseChatModel):
        """Initialize the agent.

        Args:
            llm: LLM service to use for the agent

        """
        self.llm = llm

    @abstractmethod
    async def process(self, state: StateT) -> StateT:
        """Process the current state and update it.

        Args:
            state: The current state of the conversation

        Returns:
            The updated state

        """
        pass
