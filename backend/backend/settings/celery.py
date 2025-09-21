from pydantic_settings import BaseSettings, SettingsConfigDict


class CelerySettings(BaseSettings):
    """Configuration settings for Celery background tasks.
    
    Attributes:
        CELERY_BROKER_URL (str): Redis URL for Celery broker
        CELERY_RESULT_BACKEND (str): Redis URL for Celery results
        CELERY_TASK_SERIALIZER (str): Task serialization format
        CELERY_RESULT_SERIALIZER (str): Result serialization format
        CELERY_ACCEPT_CONTENT (list): Accepted content types
        CELERY_TIMEZONE (str): Timezone for scheduled tasks
        CELERY_ENABLE_UTC (bool): Enable UTC timezone
        CELERY_TASK_TRACK_STARTED (bool): Track task start times
        CELERY_TASK_TIME_LIMIT (int): Task time limit in seconds
        CELERY_TASK_SOFT_TIME_LIMIT (int): Task soft time limit in seconds
        CELERY_WORKER_PREFETCH_MULTIPLIER (int): Worker prefetch multiplier
    """
    
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 300  # 5 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = 240  # 4 minutes
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    def get_celery_config(self) -> dict:
        """Get Celery configuration dictionary.
        
        Returns:
            Dictionary containing Celery configuration
        """
        return {
            "broker_url": self.CELERY_BROKER_URL,
            "result_backend": self.CELERY_RESULT_BACKEND,
            "task_serializer": self.CELERY_TASK_SERIALIZER,
            "result_serializer": self.CELERY_RESULT_SERIALIZER,
            "accept_content": self.CELERY_ACCEPT_CONTENT,
            "timezone": self.CELERY_TIMEZONE,
            "enable_utc": self.CELERY_ENABLE_UTC,
            "task_track_started": self.CELERY_TASK_TRACK_STARTED,
            "task_time_limit": self.CELERY_TASK_TIME_LIMIT,
            "task_soft_time_limit": self.CELERY_TASK_SOFT_TIME_LIMIT,
            "worker_prefetch_multiplier": self.CELERY_WORKER_PREFETCH_MULTIPLIER,
        }


