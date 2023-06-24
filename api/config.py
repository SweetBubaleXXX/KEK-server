from pydantic import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./db.sqlite3?check_same_thread=False"
    user_is_activated_default: bool = False
    user_storage_size_limit: int = 0

    class Config:
        env_file = ".config"


settings = Settings()
