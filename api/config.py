import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", 3000))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")


settings = Settings()
