from backend.infrastructure.repositories.prompt_repository.interface import IPromptRepository


class PromptRepository(IPromptRepository):
    """Repository for storing and retrieving prompts."""

    def __init__(self):
        """Initialize the prompt repository with default prompts."""
        self.prompts = {}

    def get_prompt(self, prompt_name: str) -> str:
        """Get a prompt by name.

        Args:
            prompt_name: Name of the prompt to retrieve

        Returns:
            Prompt string

        """
        return self.prompts.get(prompt_name, "")
