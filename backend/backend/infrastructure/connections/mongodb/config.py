class MongoDBConfig:
    """A class to hold MongoDB configuration parameters."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
    ):
        """Initialize the MongoDBConfig with the provided parameters.

        Args:
            host (str): The MongoDB host.
            port (int): The MongoDB port.
            user (str): The MongoDB user.
            password (str): The MongoDB password.
            database (str): The name of the database.

        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    def get_connection_uri(self) -> str:
        """Get the connection URI for the MongoDB instance.

        Returns:
            str: The connection URI.
        """
        uri = f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

        if self.user in {"admin", "mongo"}:
            uri += "?authSource=admin"

        return uri
