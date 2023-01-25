import os

from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv("../.config")


class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")
    user_is_activated_default: bool = bool(os.getenv("USER_IS_ACTIVATED_DEFAULT", ""))
    user_storage_size_limit: int = int(os.getenv("USER_STORAGE_SIZE_LIMIT", "0"))  # bytes


settings = Settings()
