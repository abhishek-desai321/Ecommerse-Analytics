from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379"
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    
    # Event Stream Config
    STREAM_KEY: str = "events_stream"
    CONSUMER_GROUP: str = "analytics_group"
    CONSUMER_NAME: str = "worker_1"
    
    # Window Sizes (seconds)
    WINDOW_ACTIVE_USERS: int = 300  # 5 mins
    WINDOW_PAGE_VIEWS: int = 900    # 15 mins
    WINDOW_SESSIONS: int = 300      # 5 mins
    
    # Rate Limiting
    RATE_LIMIT_PER_SECOND: int = 50
    
    # DLQ Config
    DLQ_STREAM_KEY: str = "events_dlq"

settings = Settings()
