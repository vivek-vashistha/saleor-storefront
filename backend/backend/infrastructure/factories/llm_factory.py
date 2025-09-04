from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from backend.domain.enums import LLMType


class LLMFactory:
    """Factory class for creating language models."""

    @staticmethod
    def create_llm(llm_type: LLMType, api_key: str) -> BaseChatModel:
        """Creates a language model based on the provided type and API key.

        Args:
            llm_type (LLMType): The type of language model to create.
            api_key (str): The API key for the language model.

        Returns:
            BaseChatModel: The created language model.

        """
        if llm_type == LLMType.GPT4:
            return ChatOpenAI(
                model="gpt-4",
                temperature=1,
                top_p=1,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                api_key=api_key,
            )

        if llm_type == LLMType.GPT4o:
            return ChatOpenAI(
                model="gpt-4o",
                temperature=1,
                top_p=1,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                api_key=api_key,
            )

        raise ValueError(f"Unsupported LLM type: {llm_type}")
