from abc import ABC, abstractmethod
from typing import Generic

from typing_extensions import TypeVar

from backend.application.interfaces.workflow import IWorkflow

StateT = TypeVar("StateT")


class IChatWorkflow(Generic[StateT], IWorkflow, ABC):
    """Interface for chat evaluation workflows.

    This interface extends the base IWorkflow with methods specific
    to chat evaluation workflows, which process user queries to produce
    conversational responses.

    """

    @abstractmethod
    async def run(self, query: StateT) -> StateT:
        """Process a chat query using the workflow.

        Args:
            query: The chat query from the user

        Returns:
            The chat response containing the message and any additional data

        """
        pass
