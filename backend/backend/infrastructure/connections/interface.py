from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Generic, TypeVar

T = TypeVar("T")  # Type variable for the connection type


class IDatabaseConnection(ABC, Generic[T]):
    """An abstract base class for database connections."""

    @abstractmethod
    def get_connection(self) -> T:
        """Get a database connection."""
        pass

    @abstractmethod
    async def execute_db_operation(
        self, operation: Callable[[Any], Any], error_message: str = "Database operation error"
    ) -> Any:
        """Execute a database operation within a session and handle any errors.

        Args:
            operation (Callable[[Any], Any]): The database operation to execute.
            error_message (str): The error message to display if the operation fails.
                Defaults to "Database operation error".

        Returns:
            Any: The result of the database operation.
        """
        pass
