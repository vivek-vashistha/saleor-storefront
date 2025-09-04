class PostgreSQLConfig:
    """A class to hold PostgreSQL database configuration parameters."""

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        """Initialize the PostgreSQLConfig with the provided parameters.

        Args:
            host (str): The database host.
            port (int): The database port.
            user (str): The database user.
            password (str): The database password.
            database (str): The name of the database.
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    def get_connection_string(self) -> str:
        """Get the connection string for the database.

        Returns:
            str: The connection string.
        """
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
