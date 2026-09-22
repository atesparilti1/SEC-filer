from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Which backend generates NEW analyses. Demo filings (see app/demo_data/)
    # are served from pre-seeded cache regardless of this setting, so the app
    # is explorable with zero AI setup either way.
    ai_provider: Literal["ollama", "openai"] = "ollama"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    sec_user_agent: str = "SEC Filing Analyzer contact@example.com"

    database_url: str = "sqlite:///./sec_filing_analyzer.db"

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
