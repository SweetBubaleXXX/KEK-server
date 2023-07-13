from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./db.sqlite3?check_same_thread=False"
    USER_IS_ACTIVATED_DEFAULT: bool = False
    USER_STORAGE_SIZE_LIMIT: int = 0
    SESSION_STORAGE_MAX_SIZE: int = 1_000_000
    SESSION_TTL: int = 600

    class Config:
        env_file = ".config"


settings = Settings()
