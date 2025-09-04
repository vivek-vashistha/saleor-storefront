from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Neo4jSettings(BaseSettings):
    """Configuration settings for the Neo4j graph database.

    Attributes:
        NEO4J_URI (str): The Neo4j server URI.
        NEO4J_USERNAME (str): The Neo4j username.
        NEO4J_PASSWORD (str): The Neo4j password.
        NEO4J_DATABASE (str): The Neo4j database name. (default: neo4j)
        NEO4J_VECTOR_INDEX_NAME (str): The vector index name for embeddings. (default: productEmbedding)
        NEO4J_FULLTEXT_INDEX_NAME (str): The fulltext index name. (default: productFulltext)

    """

    NEO4J_URI: str = Field(default="bolt://localhost:7687")
    NEO4J_USERNAME: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="password")
    NEO4J_DATABASE: str = Field(default="neo4j")
    NEO4J_VECTOR_INDEX_NAME: str = Field(default="productEmbedding")
    NEO4J_FULLTEXT_INDEX_NAME: str = Field(default="productFulltext")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def get_connection_url(self) -> str:
        """Return the connection URL for the Neo4j server."""
        return self.NEO4J_URI
