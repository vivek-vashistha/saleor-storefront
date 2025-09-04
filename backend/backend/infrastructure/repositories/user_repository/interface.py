from abc import ABC, abstractmethod
from typing import Any


class IUserRepository(ABC):
    """Interface for user repository operations."""

    @abstractmethod
    async def get_purchase_history(self, user_id: int) -> list[int]:
        """Get the product IDs that a user has purchased.

        Args:
            user_id: The user ID

        Returns:
            List of product IDs the user has purchased
        """
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> dict[str, Any]:
        """Get user information by ID.

        Args:
            user_id: The user ID

        Returns:
            Dictionary containing user information
        """
        pass
