"""Runtime configuration (environment variables prefixed with ZENTREND_)."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ZENTREND_", env_file=ROOT / ".env", extra="ignore")

    data_dir: Path = ROOT / "data"
    model: str = "claude-opus-5-5"
    effort: str = "medium"
    max_agent_turns: int = 8
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "Xenova/ms-marco-MiniLM-L-6-v2"
    use_dense: bool = True
    use_reranker: bool = True
    cors_origins: list[str] = ["http://localhost:3000"]
    # Force the deterministic offline analyst even if an API key is present (tests, demos).
    offline: bool = False

    @property
    def corpus_dir(self) -> Path:
        return self.data_dir / "corpus"

    @property
    def index_dir(self) -> Path:
        return self.data_dir / "index"

    @property
    def survey_dir(self) -> Path:
        return self.data_dir / "survey"

    @property
    def llm_enabled(self) -> bool:
        if self.offline:
            return False
        return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


settings = Settings()
