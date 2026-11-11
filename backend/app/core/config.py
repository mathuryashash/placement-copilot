"""Application settings loaded from environment variables."""
from __future__ import annotations

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://copilot:copilot@localhost:18401/placement_copilot"
    groq_api_key: str = ""
    gemini_api_key: str = ""
    cors_origins: str = "http://localhost:18402,http://localhost:3000"
    fake_llm: bool = False
    llm_cache_dir: str = "./llm_cache"
    hf_home: str = "./hf_cache"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
# Point fastembed / HF to our cache dir
os.environ.setdefault("HF_HOME", settings.hf_home)
