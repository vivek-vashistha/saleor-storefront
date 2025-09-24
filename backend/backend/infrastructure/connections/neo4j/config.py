from pydantic import BaseModel, Field
from typing import Optional


class Neo4jConfig(BaseModel):
    """Configuration for Neo4j connection."""
    
    uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    username: str = Field(default="neo4j", description="Neo4j username")
    password: str = Field(default="password123", description="Neo4j password")
    database: str = Field(default="neo4j", description="Neo4j database name")
    max_connection_lifetime: int = Field(default=3600, description="Maximum connection lifetime in seconds")
    max_connection_pool_size: int = Field(default=50, description="Maximum connection pool size")
    connection_timeout: int = Field(default=30, description="Connection timeout in seconds")
    
    def get_connection_url(self) -> str:
        """Get the Neo4j connection URL.
        
        Returns:
            The Neo4j connection URI
        """
        return self.uri
    
    @classmethod
    def from_env(cls) -> "Neo4jConfig":
        """Create Neo4jConfig from environment variables."""
        import os
        
        return cls(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            username=os.getenv("NEO4J_USERNAME", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password123"),
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
            max_connection_lifetime=int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "3600")),
            max_connection_pool_size=int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "50")),
            connection_timeout=int(os.getenv("NEO4J_CONNECTION_TIMEOUT", "30"))
        )