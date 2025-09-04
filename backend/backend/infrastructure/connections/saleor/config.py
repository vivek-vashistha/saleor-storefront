from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SaleorConfig(BaseSettings):
    """Configuration settings for Saleor API connection.

    Attributes:
        host (str): The Saleor API server host
        port (int): The Saleor API server port
        base_url (str): The complete base URL for the Saleor API
        timeout (int): Request timeout in seconds
    """

    host: str = Field(default="localhost", description="Saleor API server host")
    port: int = Field(default=8002, description="Saleor API server port")
    timeout: int = Field(default=30, description="Request timeout in seconds")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def base_url(self) -> str:
        """Get the complete base URL for the Saleor API."""
        return f"http://{self.host}:{self.port}"
