from abc import ABC, abstractmethod


class IPromptRepository(ABC):
    """Interface for prompt repositories."""

    @abstractmethod
    def get_prompt(self, prompt_name: str) -> str:
        """Get a prompt by name.

        Args:
            prompt_name: Name of the prompt to retrieve

        Returns:
            Prompt string

        """
        pass
