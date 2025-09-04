from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SaleorSettings(BaseSettings):
    """Saleor API configuration settings."""

    SALEOR_HOST: str = Field(default="localhost", description="Saleor API server host")
    SALEOR_PORT: int = Field(default=8002, description="Saleor API server port")
    SALEOR_TIMEOUT: int = Field(default=30, description="Request timeout in seconds")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
