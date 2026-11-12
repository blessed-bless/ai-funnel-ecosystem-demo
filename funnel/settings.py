from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "demo"
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    database_url: str = f"sqlite:///{DATA_DIR / 'funnel.db'}"
    public_base_url: str = "http://127.0.0.1:8080"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    telegram_bot_token: str = ""
    telegram_admin_chat_id: str = ""

    @property
    def use_real_llm(self) -> bool:
        return bool(self.openai_api_key.strip())

    @property
    def bot_enabled(self) -> bool:
        return bool(self.telegram_bot_token.strip())


@lru_cache
def get_settings() -> Settings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()
