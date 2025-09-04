from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Generic, TypeVar

from backend.application.interfaces.workflow import IWorkflow

StateT = TypeVar("StateT")


class IStreamChatWorkflow(Generic[StateT], IWorkflow, ABC):
    """Interface for chat evaluation workflows that generate responses as they are generated.

    This interface extends the base IWorkflow with methods specific
    to chat evaluation workflows that produce responses as they are generated.

    """

    @abstractmethod
    async def run(self, query: StateT) -> AsyncGenerator[StateT, None]:
        """Stream the LLM response for a chat query.

        Args:
            query: The chat query from the user

        Returns:
            An async generator yielding response content chunks as they are generated

        """
        pass
