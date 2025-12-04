from pydantic_settings import BaseSettings
import os
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Math Visualizer API"
    API_V1_STR: str = "/api/v1"
    # Default to localhost for dev, override in prod
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/math_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
