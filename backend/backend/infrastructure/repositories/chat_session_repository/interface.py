from abc import ABC, abstractmethod

from backend.domain.entities import ChatSession


class IChatSessionRepository(ABC):
    """Interface for chat session repository operations."""

    @abstractmethod
    async def create_session(self, session: ChatSession) -> ChatSession:
        """Create a new chat session.

        Args:
            session: The chat session to create

        Returns:
            The created chat session with its ID
        """
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> ChatSession | None:
        """Get a chat session by its ID.

        Args:
            session_id: The ID of the chat session to retrieve

        Returns:
            The chat session if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_session(self, session: ChatSession) -> ChatSession:
        """Update an existing chat session.

        Args:
            session: The chat session to update

        Returns:
            The updated chat session
        """
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a chat session.

        Args:
            session_id: The ID of the chat session to delete

        Returns:
            True if the session was deleted, False otherwise
        """
        pass

    @abstractmethod
    async def get_user_sessions(self, user_id: str) -> list[ChatSession]:
        """Get all chat sessions for a user.

        Args:
            user_id: The ID of the user

        Returns:
            A list of chat sessions for the user
        """
        pass
