from pydantic import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./db.sqlite3"
    user_is_activated_default: int = 0
    user_storage_size_limit: int = 0

    class Config:
        env_file = ".config"


settings = Settings()
