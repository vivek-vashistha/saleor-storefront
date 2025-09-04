from pydantic import BaseModel


class Neo4jConfig(BaseModel):
    """Configuration for Neo4j database connection."""

    uri: str
    username: str
    password: str
    database: str = "neo4j"
    vector_index_name: str = "productEmbedding"
    fulltext_index_name: str = "productFulltext"

    def get_connection_url(self) -> str:
        """Get the Neo4j connection URL."""
        return self.uri
