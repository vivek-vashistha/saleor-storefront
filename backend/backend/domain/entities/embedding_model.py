from langchain_core.embeddings import Embeddings
from pydantic import BaseModel, ConfigDict


class EmbeddingModel(BaseModel):
    """Class representing an embedding model.

    Args:
        model (Embeddings): The embedding model.
        dimension (int): The dimension of the embedding model.

    """

    model: Embeddings
    dimension: int

    model_config = ConfigDict(arbitrary_types_allowed=True)
