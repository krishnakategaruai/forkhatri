# [IMP42 — Refactor C (AI)] AI settings, read from the same vyapar-service/.env
# as app/config.py. They live in their own settings object because this
# workstream owns only new files; a later tidy-up may fold them into
# app.config.Settings without changing any key name.
#
#   AI_PROVIDER         anthropic | rules   (rules = keyword engine, no key needed)
#   ANTHROPIC_API_KEY   CHANGE_ME placeholder keeps the rules engine in use
#   VYAPAR_AI_MODEL     Claude model id (Claude Sonnet 5 by default, for cost)
#   AI_DAILY_LIMIT      AI calls a member may make per day (all five endpoints)
#   AI_TIMEOUT_SECONDS  one Claude call's wall-clock budget
#   AI_MAX_INPUT_CHARS  longest text accepted by draft/proposal endpoints
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ai_provider: str = "rules"
    anthropic_api_key: str = "CHANGE_ME"
    vyapar_ai_model: str = "claude-sonnet-5"
    ai_daily_limit: int = 50
    ai_timeout_seconds: float = 45.0
    ai_max_input_chars: int = 6000

    @property
    def has_anthropic_key(self) -> bool:
        key = self.anthropic_api_key.strip()
        return bool(key) and not key.startswith("CHANGE_ME")

    @property
    def provider_name(self) -> str:
        """The provider actually used: `anthropic` needs a real key, otherwise rules."""
        name = self.ai_provider.strip().lower()
        if name == "anthropic" and self.has_anthropic_key:
            return "anthropic"
        return "rules"


@lru_cache
def get_ai_settings() -> AiSettings:
    return AiSettings()
