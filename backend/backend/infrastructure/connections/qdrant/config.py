class QdrantConfig:
    """A class to hold Qdrant vector database configuration parameters."""

    def __init__(
        self,
        host: str,
        port: int,
        api_key: str | None,
        collection: str,
        vector_size: int,
        prefer_grpc: bool = True,
        timeout: int = 10,
    ):
        """Initialize the QdrantConfig with the provided settings.

        Args:
            host (str): The Qdrant server host.
            port (int): The Qdrant server port.
            api_key (str): The Qdrant API key. (optional)
            collection (str): The name of the Qdrant collection.
            vector_size (int): The size of the embedding vectors.
            prefer_grpc (bool): Whether to prefer gRPC over HTTP. (default: True)
            timeout (int): Connection timeout in seconds. (default: 10)

        """
        self.host = host
        self.port = port
        self.api_key = api_key
        self.collection_name = collection
        self.vector_size = vector_size
        self.prefer_grpc = prefer_grpc
        self.timeout = timeout

    def get_connection_url(self) -> str:
        """Get the connection URL for the Qdrant server.

        Returns:
            str: The connection URL.
        """
        return f"{self.host}:{self.port}"
