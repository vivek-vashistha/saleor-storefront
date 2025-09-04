from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class QdrantSettings(BaseSettings):
    """Configuration settings for the Qdrant vector database.

    Attributes:
        QDRANT_HOST (str): The Qdrant server host.
        QDRANT_PORT (int): The Qdrant server port. (default: 6333)
        QDRANT_PREFER_GRPC (bool): Whether to prefer gRPC over HTTP. (default: True)
        QDRANT_TIMEOUT (int): Connection timeout in seconds. (default: 10)
        QDRANT_API_KEY (str): The API key for the Qdrant server. (default: None)

    """

    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: int = Field(default=6333)
    QDRANT_PREFER_GRPC: bool = Field(default=True)
    QDRANT_TIMEOUT: int = Field(default=10)
    QDRANT_API_KEY: str | None = Field(default=None)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def get_connection_url(self) -> str:
        """Return the connection URL for the Qdrant server."""
        return f"{self.QDRANT_HOST}:{self.QDRANT_PORT}"
