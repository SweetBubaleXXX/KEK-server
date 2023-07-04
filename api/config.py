from pydantic import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./db.sqlite3?check_same_thread=False"
    user_is_activated_default: bool = False
    user_storage_size_limit: int = 0
    session_storage_max_size: int = 1_000_000
    session_ttl: int = 600

    class Config:
        env_file = ".config"


settings = Settings()
