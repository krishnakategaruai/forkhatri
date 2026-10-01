"""AI assists discovery; it never is the marketplace. A natural-language need
becomes structured filters (area, duration, budget, keywords), then the
deterministic search does the matching. `rules` is the built-in parser;
`anthropic` asks Claude for the same structure and falls back to rules."""

from __future__ import annotations

import json
import re

from app.settings import get_settings

AREA_HINTS = {
    "business": ["startup", "business", "founder", "entrepreneur", "saas", "product strategy", "pricing", "go to market", "pitch", "व्यवसाय", "వ్యాపారం"],
    "career": ["career", "job", "interview", "resume", "cv", "promotion", "switch", "करियर", "కెరీర్"],
    "freelancing": ["freelanc", "upwork", "client", "creator", "youtube channel", "portfolio"],
    "technology": ["software", "code", "app", "website", "cloud", "developer", "engineer", "architecture review", "ai", "data"],
    "agriculture": ["farm", "crop", "soil", "seed", "irrigation", "खेती", "వ్యవసాయ"],
    "education": ["exam", "study", "college", "admission", "phd", "university", "study abroad"],
    "legal": ["lawyer", "legal", "court", "contract", "notice", "property dispute", "divorce", "कानून", "వకీలు", "advocate"],
    "finance": ["tax", "gst", "itr", "ca ", "chartered", "accounting", "audit", "income tax", "tds", "lut", "invoice", "टैक्स", "పన్ను"],
    "investment": ["invest", "mutual fund", "insurance", "sip", "portfolio review", "retire", "बीमा", "पेट్టుబడి"],
    "health": ["doctor", "medical", "diagnosis", "symptom", "second opinion", "डॉक्टर", "వైద్యు"],
    "mental-health": ["anxiety", "stress", "therapy", "counsell", "depress", "burnout"],
    "nutrition": ["diet", "nutrition", "weight", "meal plan"],
    "fitness": ["fitness", "gym", "marathon", "training plan", "sport"],
    "architecture": ["house plan", "construction", "architect", "interior", "vastu"],
    "property": ["property", "real estate", "flat", "plot", "rent agreement", "registration of land"],
    "design": ["design", "ux", "ui", "logo", "brand"],
    "media": ["content", "video", "podcast", "social media", "instagram growth"],
    "travel": ["trek", "travel", "visa", "trip", "himalaya"],
    "trades": ["electrician", "plumb", "carpent", "welding", "mechanic"],
    "manufacturing": ["factory", "manufactur", "machine", "production line"],
    "logistics": ["logistics", "supply chain", "export", "import", "shipping"],
    "food": ["restaurant", "cloud kitchen", "recipe", "catering", "hotel"],
    "personal": ["confidence", "public speaking", "habit", "productivity", "life coach"],
    "community": ["ngo", "social work", "trust registration", "community"],
    "science": ["research", "paper", "lab", "thesis"],
}

STOP = set("i need someone who can help me with my a an the to for and of in on about want looking find some please review discuss talk chat minutes minute mins hour hours has have built build under below budget".split())


def rules_parse(text: str) -> dict:
    t = text.lower()
    padded = f" {t} "
    scored = [(sum(1 for h in hints if f" {h}" in padded), a) for a, hints in AREA_HINTS.items()]
    # Regulated/specific areas outrank broad ones on a tie (GST beats "freelance").
    specificity = {"finance": 2, "legal": 2, "health": 2, "investment": 2, "mental-health": 2, "agriculture": 1, "travel": 1}
    areas = [a for n, a in sorted(scored, key=lambda x: (-x[0], -specificity.get(x[1], 0))) if n > 0]
    m = re.search(r"(\d{2,3})\s*(min|minute)", t)
    duration = int(m.group(1)) if m else (60 if "hour" in t else None)
    b = re.search(r"(?:under|below|upto|up to|max|budget|₹|rs\.?|inr)\s*₹?\s*(\d[\d,]{2,})", t)
    budget = int(b.group(1).replace(",", "")) if b else None
    keywords = [w for w in re.findall(r"[a-zऀ-ॿఀ-౿]{3,}", t) if w not in STOP][:6]
    return {"areas": areas[:2], "duration_max": duration, "max_price": budget, "keywords": keywords, "source": "rules"}


async def summarise(notes: str) -> str | None:
    """Three to five plain bullet points from the shared notes, only when Claude is configured."""
    s = get_settings()
    if not (s.ai_provider == "anthropic" and s.anthropic_api_key and "CHANGE_ME" not in s.anthropic_api_key):
        return None
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": s.anthropic_api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": s.counsel_ai_model, "max_tokens": 400, "messages": [{"role": "user", "content":
                      "Summarise these consultation notes in 3-5 short bullet points: decisions first, then next steps. Use only what is written.\n\n" + notes[:8000]}]},
            )
        if r.status_code == 200:
            return "".join(part.get("text", "") for part in r.json().get("content", [])).strip() or None
    except Exception:
        return None
    return None


async def understand(text: str) -> dict:
    s = get_settings()
    if s.ai_provider == "anthropic" and s.anthropic_api_key and "CHANGE_ME" not in s.anthropic_api_key:
        try:
            import httpx
            prompt = (
                "Turn this request for a paid consultation into JSON with keys areas (list of up to 2 slugs from: "
                + ", ".join(AREA_HINTS) + "), duration_max (minutes or null), max_price (INR or null), keywords (up to 6 short words). "
                "Answer with JSON only.\n\nRequest: " + text
            )
            async with httpx.AsyncClient(timeout=20) as c:
                r = await c.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": s.anthropic_api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                    json={"model": s.counsel_ai_model, "max_tokens": 300, "messages": [{"role": "user", "content": prompt}]},
                )
            if r.status_code == 200:
                content = "".join(part.get("text", "") for part in r.json().get("content", []))
                data = json.loads(content[content.find("{"): content.rfind("}") + 1])
                data["source"] = "anthropic"
                return data
        except Exception:
            pass
    return rules_parse(text)
