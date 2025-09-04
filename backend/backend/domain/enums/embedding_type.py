from enum import Enum


class EmbeddingModelType(str, Enum):
    """Enum for different types of embedding models."""

    OPENAI_SMALL = "text-embedding-3-small"
    OPENAI_LARGE = "text-embedding-3-large"
