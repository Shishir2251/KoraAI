from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import json

class Settings(BaseSettings):
    #Application
    APP_NAME: str = "KoraAI"
    APP_VERSION: str = "1.0.0"
    DEBUG:  bool = False
    ENVIRONMENT: str = "production"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
 
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
 
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
 
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
 
    # Anthropic
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    ANTHROPIC_MAX_TOKENS: int = 4096
 
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
 
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
 
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v
 
    class Config:
        env_file = ".env"
        case_sensitive = True
 
 
settings = Settings()