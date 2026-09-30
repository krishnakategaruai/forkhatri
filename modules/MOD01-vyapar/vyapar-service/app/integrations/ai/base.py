# [IMP42 — Refactor C (AI)] The AiProvider seam. app/services/ai.py talks to
# ONE interface; AnthropicProvider (Claude) and RulesProvider (keywords and
# ranking signals, no network) both implement it and return the same raw
# shapes. Nothing a provider returns is trusted: app/integrations/ai/vocab.py
# validates every answer against the closed vocabularies before the service
# hands it to a caller, and nothing is ever written to the database by a
# provider — the person confirms in the UI.
#
# Inputs are plain dicts/strings so a provider can be swapped or mocked
# without importing pydantic models from the service layer.
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class AiUnavailable(Exception):
    """The provider cannot answer this request (no key, network, refusal, or a
    capability only Claude has). `reason` is a stable code the service maps
    to an outcome and, where the fallback cannot help, to an error."""

    def __init__(self, reason: str, message: str = "") -> None:
        super().__init__(message or reason)
        self.reason = reason


@dataclass(slots=True)
class ImageInput:
    """One image or PDF to read. Exactly one of `url` / `data` is set."""

    media_type: str
    url: str | None = None
    data_base64: str | None = None


@dataclass(slots=True)
class AiResult:
    """A provider's raw answer plus what it cost. `data` is unvalidated."""

    data: dict[str, Any]
    provider: str
    model: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    notes: list[str] = field(default_factory=list)


class AiProvider(Protocol):
    name: str

    async def draft_opportunity(self, text: str, language: str, entry: str, capability_terms: list[dict[str, Any]]) -> AiResult: ...

    async def read_opportunity_image(self, image: ImageInput, language: str, capability_terms: list[dict[str, Any]]) -> AiResult: ...

    async def shortlist(self, opportunity: dict[str, Any], applicants: list[dict[str, Any]], language: str) -> AiResult: ...

    async def posting_tips(self, draft: dict[str, Any], rule_tips: list[dict[str, Any]], language: str) -> AiResult: ...

    async def improve_proposal(self, opportunity: dict[str, Any], text: str, applicant: dict[str, Any], language: str) -> AiResult: ...

    # [Voice interview] optional: providers without it are simply not asked
    # (the service checks with getattr). Returns {"understood", "canonical"}.
    # async def interpret_answer(self, field, question_en, question, text, language) -> AiResult: ...
