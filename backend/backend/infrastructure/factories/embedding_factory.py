from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from backend.domain.entities import EmbeddingModel
from backend.domain.enums.embedding_type import EmbeddingModelType


class EmbeddingFactory:
    """Factory class for creating embedding services."""

    @staticmethod
    def create_embedding_model(model_type: EmbeddingModelType, api_key: str) -> EmbeddingModel:
        """Creates an embedding model based on the provided model type and API key.

        Args:
            model_type: The type of embedding model to use
            api_key: The API key for the embedding service

        Returns:
            An embedding model instance

        Raises:
            ValueError: If an unsupported model type is provided
        """
        if model_type == EmbeddingModelType.OPENAI_SMALL:
            return EmbeddingModel(
                model=OpenAIEmbeddings(model="text-embedding-3-small", api_key=SecretStr(api_key)),
                dimension=1536,
            )

        if model_type == EmbeddingModelType.OPENAI_LARGE:
            return EmbeddingModel(
                model=OpenAIEmbeddings(model="text-embedding-3-large", api_key=SecretStr(api_key)),
                dimension=3072,
            )

        raise ValueError(f"Unsupported embedding model type: {model_type}")
