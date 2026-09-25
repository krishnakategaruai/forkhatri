"""The two profile lenses (DEC-V1-023): shaping only, no data access.

`build_lens()` turns `ProfileLensData` (already disclosure-filtered by
`interface.lens_data()`) into the contract's shape:
  * `biodata` → `sections[]`, conventional matrimony order
    (`config/profile_schema.BIODATA_SECTIONS`);
  * `story`   → `blocks[]`, Hinge-style interleave: photo, identity, prompt,
    photo, section, prompt, photo, section…
Labels, section titles and enum displays are localised here (ADR-010) in the
reader's language; raw values travel alongside so a client can format them
its own way.
"""

from __future__ import annotations

from typing import Any

from app.components.profile.interface import ProfileLensData
from app.config.profile_schema import (
    BIODATA_SECTIONS,
    ENUM_FACTS,
    FACT_SOURCES,
    STORY_SECTIONS,
)
from app.i18n import translate

__all__ = ["build_lens"]


def _facts(data: ProfileLensData) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    for name, sources in FACT_SOURCES.items():
        for category, key in sources:
            value = (data.attributes.get(category) or {}).get(key)
            if value not in (None, "", [], {}):
                facts[name] = value
                break
    if data.name:
        facts["name"] = data.name
    if data.age is not None:
        facts["age"] = data.age
    if data.gender:
        facts["gender"] = data.gender
    if data.locality:
        facts["locality"] = data.locality
    return facts


def _prompts(data: ProfileLensData, lang: str) -> list[dict[str, Any]]:
    prompts: list[dict[str, Any]] = []
    words = data.attributes.get("in_my_words") or {}
    for slot in ("prompt_1", "prompt_2", "prompt_3"):
        value = words.get(slot)
        if isinstance(value, dict) and value.get("a"):
            q = str(value.get("q") or "")
            question = translate(f"profile.prompt.{q}", lang) if q else ""
            if question == f"profile.prompt.{q}":
                question = q.replace("_", " ").capitalize()
            prompts.append({"key": slot, "question": question, "answer": str(value["a"])})
    # The older seed's free-text answers, if no prompt was written.
    if not prompts:
        for key in ("about_me", "i_value", "weekend"):
            answer = (data.attributes.get("self_expression") or {}).get(key)
            if answer:
                prompts.append(
                    {"key": key, "question": translate(f"profile.prompt.{key}", lang), "answer": str(answer)}
                )
    return prompts


def _humanize(value: str) -> str:
    return value.replace("_", " ").strip().capitalize()


def _display(name: str, value: Any, lang: str) -> str:
    if isinstance(value, bool):
        return translate("profile.value.bool.yes" if value else "profile.value.bool.no", lang)
    if isinstance(value, list):
        return ", ".join(_display(name, v, lang) for v in value)
    if isinstance(value, dict):
        low, high = value.get("min"), value.get("max")
        if low is not None or high is not None:
            return f"{low or ''}–{high or ''}".strip("–")
        return ", ".join(f"{k}: {v}" for k, v in value.items())
    if name == "height_cm":
        try:
            cm = int(value)
        except (TypeError, ValueError):
            return str(value)
        inches = round(cm / 2.54)
        return f"{inches // 12}'{inches % 12}\" ({cm} cm)"
    if name in ENUM_FACTS and isinstance(value, str):
        key = f"profile.value.{name}.{value}"
        text = translate(key, lang)
        return _humanize(value) if text == key else text
    return str(value)


def _item(name: str, facts: dict[str, Any], lang: str) -> dict[str, Any] | None:
    if name not in facts:
        return None
    value = facts[name]
    return {
        "key": name,
        "label": translate(f"profile.field.{name}", lang),
        "value": value,
        "display": _display(name, value, lang),
    }


def _section(key: str, names: tuple[str, ...], facts: dict[str, Any], lang: str) -> dict[str, Any] | None:
    items = [i for i in (_item(n, facts, lang) for n in names) if i is not None]
    if not items:
        return None
    return {"key": key, "title": translate(f"profile.section.{key}", lang), "items": items}


def _photo(url: str, position: int) -> dict[str, Any]:
    return {"type": "photo", "url": url, "position": position}


def build_lens(data: ProfileLensData, *, lens: str, lang: str) -> dict[str, Any]:
    facts = _facts(data)
    prompts = _prompts(data, lang)
    base: dict[str, Any] = {
        "account_id": str(data.account_id),
        "profile_id": str(data.profile_id) if data.profile_id else None,
        "lens": lens,
        "disclosed": data.disclosed,
        "searchable": data.searchable,
        "name": data.name,
        "age": data.age,
        "gender": data.gender,
        "locality": data.locality,
        "photos": [{"url": p.url, "is_primary": p.is_primary} for p in data.photos],
        "voice_intro_url": data.voice_intro_url,
        "headline": ", ".join(
            str(v)
            for v in (
                facts.get("occupation"),
                _display("highest_education_level", facts["highest_education_level"], lang)
                if "highest_education_level" in facts
                else None,
            )
            if v
        ),
    }

    if lens == "biodata":
        sections: list[dict[str, Any]] = []
        for key, names in BIODATA_SECTIONS:
            if key == "about":
                if prompts:
                    sections.append(
                        {
                            "key": "about",
                            "title": translate("profile.section.about", lang),
                            "items": [
                                {"key": p["key"], "label": p["question"], "value": p["answer"], "display": p["answer"]}
                                for p in prompts
                            ],
                        }
                    )
                continue
            section = _section(key, names, facts, lang)
            if section:
                sections.append(section)
        return {**base, "sections": sections}

    # story
    photos = [p.url for p in data.photos]
    blocks: list[dict[str, Any]] = []
    photo_index = 0
    if photos:
        blocks.append(_photo(photos[0], 0))
        photo_index = 1
    identity_items = [
        i for i in (_item(n, facts, lang) for n in ("occupation", "highest_education_level", "height_cm", "mother_tongue")) if i
    ]
    blocks.append(
        {
            "type": "identity",
            "name": data.name,
            "age": data.age,
            "locality": data.locality,
            "items": identity_items,
        }
    )
    sections_iter = iter(STORY_SECTIONS)
    prompt_iter = iter(prompts)
    # Interleave: prompt, photo, section, prompt, photo, section …
    exhausted = False
    while not exhausted:
        exhausted = True
        prompt = next(prompt_iter, None)
        if prompt:
            blocks.append({"type": "prompt", **prompt})
            exhausted = False
        if photo_index < len(photos):
            blocks.append(_photo(photos[photo_index], photo_index))
            photo_index += 1
            exhausted = False
        section_def = next(sections_iter, None)
        if section_def:
            section = _section(section_def[0], section_def[1], facts, lang)
            if section:
                blocks.append({"type": "section", **section})
            exhausted = False
    if data.voice_intro_url:
        blocks.append({"type": "voice", "url": data.voice_intro_url})
    return {**base, "blocks": blocks}
