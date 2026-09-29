# [IMP42 — Refactor C (AI)] AI adapter seam.
#
#   base.py                AiProvider interface, AiResult, AiUnavailable, ImageInput
#   config.py              AI_PROVIDER, ANTHROPIC_API_KEY, VYAPAR_AI_MODEL, AI_DAILY_LIMIT ...
#   vocab.py               closed vocabularies + the validators every answer passes
#   anthropic_provider.py  Claude (structured JSON, vision), chosen by AI_PROVIDER=anthropic
#   rules_provider.py      keyword/ranking-signal engine, no network, always available
#
# The service (app/services/ai.py) asks get_ai_provider() for the configured
# provider and get_rules_provider() for the fallback. A host that has its own
# model gateway implements AiProvider and calls set_ai_provider() at startup.
from __future__ import annotations

from app.integrations.ai.base import AiProvider, AiResult, AiUnavailable, ImageInput
from app.integrations.ai.config import AiSettings, get_ai_settings
from app.integrations.ai.rules_provider import RulesProvider

_provider: AiProvider | None = None
_rules = RulesProvider()


def get_rules_provider() -> RulesProvider:
    return _rules


def get_ai_provider() -> AiProvider:
    """The configured provider: AnthropicProvider when AI_PROVIDER=anthropic
    and a real key is set, otherwise the rules engine."""
    global _provider
    if _provider is None:
        if get_ai_settings().provider_name == "anthropic":
            from app.integrations.ai.anthropic_provider import AnthropicProvider

            _provider = AnthropicProvider()
        else:
            _provider = _rules
    return _provider


def set_ai_provider(provider: AiProvider | None) -> None:
    """For a host wiring its own provider at startup (None re-reads config)."""
    global _provider
    _provider = provider


__all__ = [
    "AiProvider", "AiResult", "AiSettings", "AiUnavailable", "ImageInput",
    "get_ai_provider", "get_ai_settings", "get_rules_provider", "set_ai_provider",
]
