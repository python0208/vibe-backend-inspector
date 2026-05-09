from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vibe Backend Inspector"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./data/vibe_inspector.db"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    cors_origin_regex: str = r"http://(localhost|127\.0\.0\.1):\d+"

    model_config = SettingsConfigDict(env_prefix="VBI_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def ensure_data_dir() -> None:
    settings = get_settings()
    if settings.database_url.startswith("sqlite:///./"):
        relative_path = settings.database_url.replace("sqlite:///./", "", 1)
        Path(relative_path).parent.mkdir(parents=True, exist_ok=True)
