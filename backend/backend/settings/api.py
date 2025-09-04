from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.domain.enums import LLMType
from backend.domain.enums.embedding_type import EmbeddingModelType


class AISettings(BaseSettings):
    """Configuration settings for AI services.

    Attributes:
        MODEL_NAME (LLMType): The LLM model type to use.
        OPENAI_API_KEY (str): The OpenAI API key.
    """

    MODEL_NAME: LLMType = Field(default=LLMType.GPT4o)
    EMBEDDING_MODEL_NAME: EmbeddingModelType = Field(default=EmbeddingModelType.OPENAI_SMALL)

    OPENAI_API_KEY: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", env_parse_enums=True)


class WeatherSettings(BaseSettings):
    """Configuration settings for weather API services.

    Attributes:
        WEATHER_API_KEY (str): The weather API key.
    """

    WEATHER_API_KEY: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
