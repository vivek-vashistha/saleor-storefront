from pydantic_settings import BaseSettings, SettingsConfigDict


class MongoDBSettings(BaseSettings):
    """Configuration settings for MongoDB.

    Attributes:
        MONGODB_HOST (str): The MongoDB host.
        MONGODB_PORT (int): The MongoDB port. (default: 27017)
        MONGODB_USER (str): The MongoDB user.
        MONGODB_PASS (str): The MongoDB password.
        MONGODB_NAME (str): The name of the database.
    """

    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_USER: str = "admin"
    MONGODB_PASS: str = "password"
    MONGODB_NAME: str = "conversational_commerce"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def get_connection_uri(self) -> str:
        """Return the connection URI for MongoDB."""
        return f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASS}@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_NAME}"
