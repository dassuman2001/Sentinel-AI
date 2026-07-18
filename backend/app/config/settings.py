import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "dev"
    PROJECT_NAME: str = "Sentinel AI"
    
    # Database Configuration
    # Default local development points to host port 3308 for MySQL
    DATABASE_URL: str = "mysql+pymysql://sentinel_user:sentinel_password@127.0.0.1:3308/sentinel_db"
    
    # Redis Configuration (Celery & cache)
    # Default local development points to host port 6380 for Redis
    REDIS_URL: str = "redis://127.0.0.1:6380/0"
    
    # Security Configurations
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Auth0 Configurations
    AUTH0_DOMAIN: str = ""
    AUTH0_CLIENT_ID: str = ""
    
    # Google OAuth Configurations
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # CORS Origins
    # Can be a comma-separated string in environment variables
    BACKEND_CORS_ORIGINS: Union[List[str], str] = ["*"]

    @field_validator("BACKEND_CORS_ORIGINS")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
