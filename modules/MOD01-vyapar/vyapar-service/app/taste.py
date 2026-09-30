# [Recommendations that learn, 2026-09-30] A member's learned taste — the
# pure model (no database, no I/O), shared by the live service
# (app/services/taste.py), the feed, alerts, profile search, and the offline
# evaluation (scripts/eval_recommendations.py), so what is measured is exactly
# what runs.
#
# What it learns from: the member's OWN actions only —
#   hired (strongest), applied / sent a proposal or quote, "More like this",
#   marked done, saved, shared, opened the source, opened the detail (weak);
#   "Not interested" with its reason, and an application they withdrew.
# What it learns over: CONTENT attributes of the post or profile acted on —
#   skill, trade category, kind of post, work mode, distance band, pay band,
#   shift, experience band, and trade words in the title. A title word is
#   learned only when it is trade vocabulary (a skill's name or alias in
#   en/hi/te, or a short list of work words): a free title word can be a
#   business or family name ("Kapoor Caterers") and a surname can stand for a
#   community, so it is never learned.
# What it never learns over: who posted (id, name, community, gender,
#   religion, badges, verification), and never anybody else's behaviour — no
#   popularity, no "people like you". Those inputs do not exist in this file:
#   `post_features()` reads only the content keys listed in CONTENT_KEYS.
#
# Every action is weighted and decays with a 30-day half-life. Per post, the
# strongest action counts fully and each further positive action adds a
# little; "Not interested" overrides everything else on that post (hiding a
# post you saved means you changed your mind).
#
# Hard negatives act at once, as soft filters (the post is moved to the end,
# never removed, and all of it is reversible through the taste API):
#   "Not my skill" (not_my_capability) -> that skill is avoided;
#   "Too far"                           -> a nearer distance limit, never below 3 km;
#   "Pay too low"                       -> a pay floor used by value_fit.
#
# taste_fit (0..1) is a weighted overlap between a post's features and the
# learned weights, per feature group, with negative weights pulling it down.
# It enters ranking scaled by confidence: 0 with no history, full after 10
# meaningful actions — so a member with no history ranks exactly as before.
# Traces to: FR19, FR20, FR21, FR38, FR55, TR019, TR020, SP019
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from app.text_fold import words as fold_words

HALF_LIFE_DAYS = 30.0
WINDOW_DAYS = 365
FULL_CONFIDENCE_ACTIONS = 10
MIN_DISTANCE_LIMIT_KM = 3.0
AVOID_WINDOW_DAYS = 180

# Positive and negative weights of each action.
EVENT_WEIGHTS: dict[str, float] = {
    "hired": 5.0,
    "completed": 4.0,
    "applied": 3.0,
    "contacted": 3.0,        # a business or work profile the member asked for a price / contacted
    "more_like_this": 3.0,
    "saved": 2.0,
    "shared": 1.5,
    "external_opened": 1.5,
    "viewed": 0.5,
    "withdrawn": -1.5,
    "hidden": -3.0,
}
MEANINGFUL = frozenset(EVENT_WEIGHTS) - {"viewed"}
# The phrase a positive feature is explained with ("Like jobs you applied to").
SOURCE_OF = {"hired": "applied", "applied": "applied", "contacted": "applied", "completed": "applied", "more_like_this": "more_like_this",
             "saved": "saved", "shared": "saved", "external_opened": "other", "viewed": "other"}

# Which features a "Not interested" reason speaks about. A reason that says
# nothing about the content (already filled) teaches nothing.
REASON_GROUPS: dict[str, tuple[str, ...] | None] = {
    "not_my_capability": ("skill", "cat", "word"),      # "wrong trade"
    "too_far": ("dist",),
    "value_too_low": ("pay",),
    "wrong_type": ("type", "mode", "shift", "exp"),       # "not my kind of work"
    "wrong_timing": ("shift",),
    "already_found": (),                                  # "already filled"
    "not_interested": None,                               # all groups, gently
}
REASON_SCALE = {"not_interested": 0.4}

# How much each group counts in taste_fit.
GROUP_IMPORTANCE: dict[str, float] = {
    "skill": 0.30, "cat": 0.15, "word": 0.15, "type": 0.10, "pay": 0.10,
    "dist": 0.08, "mode": 0.05, "shift": 0.04, "exp": 0.03,
}
LISTING_GROUP_IMPORTANCE: dict[str, float] = {"lskill": 0.5, "lcat": 0.3, "ldist": 0.15, "lkind": 0.05}

# The ONLY post keys this model may read. There is no poster_id, name,
# community, gender or badge here — adding one is the same Critical defect
# SP019 names for RankingSignals.
CONTENT_KEYS = ("title", "type", "work_mode", "shift", "required_capabilities", "experience_min_months",
                "salary_min_paise", "salary_max_paise", "budget_min_paise", "budget_max_paise", "budget_paise")
LISTING_CONTENT_KEYS = ("kind", "capabilities", "categories")

# Work words learned from titles in addition to the taxonomy's own names and
# aliases (all three languages; folded the same way as titles).
WORK_WORDS = (
    "helper", "driver", "delivery", "cook", "chef", "sales", "accounts", "accountant", "teacher", "tutor", "nurse",
    "security", "guard", "cleaning", "housekeeping", "packing", "packer", "warehouse", "office", "data", "entry",
    "telecaller", "telecalling", "calling", "receptionist", "technician", "repair", "installation", "service",
    "wiring", "electrician", "plumber", "carpenter", "painter", "mason", "welder", "tailor", "beautician",
    "gst", "tax", "audit", "bookkeeping", "design", "designer", "website", "app", "marketing", "developer",
    "parttime", "part-time", "night", "weekend", "fresher", "trainee", "intern", "ac", "fridge",
    "डिलीवरी", "ड्राइवर", "कुक", "सेल्स", "टेलीकॉलर", "इलेक्ट्रीशियन", "प्लंबर", "दर्जी", "हेल्पर",
    "డెలివరీ", "డ్రైవర్", "వంట", "సేల్స్", "ఎలక్ట్రీషియన్", "ప్లంబర్", "టైలర్", "హెల్పర్",
)
_STOP = {"and", "for", "the", "with", "near", "need", "needed", "wanted", "required", "urgent", "job", "jobs", "work",
         "kavali", "kavalenu", "chahiye", "के", "लिए", "की", "కోసం", "కావాలి"}

DISTANCE_BANDS = ((3.0, "0_3"), (8.0, "3_8"), (15.0, "8_15"), (30.0, "15_30"), (math.inf, "30p"))
MONTHLY_BANDS = ((1_000_000, "m_lt10k"), (1_500_000, "m10_15k"), (2_000_000, "m15_20k"), (3_000_000, "m20_30k"), (math.inf, "m30k_plus"))
PROJECT_BANDS = ((500_000, "p_lt5k"), (2_000_000, "p5_20k"), (10_000_000, "p20k_1l"), (math.inf, "p1l_plus"))
PROJECT_TYPES = ("freelance", "local_service")


# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------
def _get(row: Mapping, key: str):
    try:
        return row[key]
    except (KeyError, IndexError):
        return None


def distance_band(km: float | None) -> str | None:
    if km is None:
        return None
    return next(label for top, label in DISTANCE_BANDS if km < top)


def monthly_top(row: Mapping) -> int | None:
    if _get(row, "type") != "employment":
        return None
    hi, lo = _get(row, "salary_max_paise"), _get(row, "salary_min_paise")
    return int(hi or lo) if (hi or lo) else None


def project_top(row: Mapping) -> int | None:
    if _get(row, "type") not in PROJECT_TYPES:
        return None
    v = _get(row, "budget_max_paise") or _get(row, "budget_paise") or _get(row, "budget_min_paise")
    return int(v) if v else None


def pay_band(row: Mapping) -> str | None:
    m = monthly_top(row)
    if m is not None:
        return next(label for top, label in MONTHLY_BANDS if m < top)
    p = project_top(row)
    if p is not None:
        return next(label for top, label in PROJECT_BANDS if p < top)
    return None


def experience_band(row: Mapping) -> str | None:
    if _get(row, "type") != "employment":
        return None
    months = _get(row, "experience_min_months") or 0
    return "fresher" if months == 0 else ("1_2y" if months <= 24 else "3y_plus")


_VOCAB: dict[int, dict[str, str]] = {}
_WORD_SKILL: dict[str, str] = {}  # folded trade word -> the skill it names (to show it by its taxonomy label)


def trade_vocabulary() -> dict[str, str]:
    """Folded trade word -> a readable form of it: every skill's names
    (en/hi/te) and aliases, plus WORK_WORDS. Rebuilt when the taxonomy cache
    is refreshed (its dict identity changes)."""
    from app import taxonomy_cache

    key = id(taxonomy_cache._TERMS)
    vocab = _VOCAB.get(key)
    if vocab is None:
        found: dict[str, str] = {}

        def add(text: str) -> None:
            for original in text.lower().replace("_", " ").split():
                for folded in fold_words(original):
                    if len(folded) >= 2 and folded not in _STOP and not folded.isdigit():
                        found.setdefault(folded, original.strip(".,;:()/"))

        for w in WORK_WORDS:
            add(w)
        word_skill: dict[str, str] = {}
        for (kind, slug), term in taxonomy_cache._TERMS.items():
            if kind == "capability":
                for text in [slug, *term.names.values(), *term.aliases]:
                    add(text)
                    for fw in fold_words(text.replace("_", " ")):
                        word_skill.setdefault(fw, slug)
        _WORD_SKILL.clear()
        _WORD_SKILL.update(word_skill)
        vocab = found
        _VOCAB.clear()
        _VOCAB[key] = vocab
    return vocab


def word_label(folded: str) -> str:
    return trade_vocabulary().get(folded, folded)


def word_skill(folded: str) -> str | None:
    """The skill a learned title word names (e.g. rider -> delivery), or None."""
    trade_vocabulary()
    return _WORD_SKILL.get(folded)


def title_words(title: str | None) -> set[str]:
    vocab = trade_vocabulary()
    return {w for w in fold_words(title) if w in vocab}


def skill_slugs(row: Mapping) -> set[str]:
    return {str(s) for s in (_get(row, "required_capabilities") or []) if s}


def categories_of(skills: Iterable[str]) -> set[str]:
    from app.taxonomy_cache import term_for

    out = set()
    for s in skills:
        t = term_for("capability", s)
        if t is not None and t.parent_slug:
            out.add(t.parent_slug)
    return out


def post_features(row: Mapping, distance_km: float | None) -> dict[str, set[str]]:
    """Content features of a post. Reads only CONTENT_KEYS (+ the distance the
    caller measured from the member)."""
    skills = skill_slugs(row)
    f: dict[str, set[str]] = {
        "skill": skills,
        "cat": categories_of(skills),
        "word": title_words(_get(row, "title")),
        "type": {_get(row, "type")} if _get(row, "type") else set(),
        "mode": {_get(row, "work_mode")} if _get(row, "work_mode") else set(),
        "shift": {_get(row, "shift")} if _get(row, "shift") else set(),
        "exp": set(),
        "pay": set(),
        "dist": set(),
    }
    if (e := experience_band(row)):
        f["exp"].add(e)
    if (p := pay_band(row)):
        f["pay"].add(p)
    if _get(row, "work_mode") != "remote" and (d := distance_band(distance_km)):
        f["dist"].add(d)
    return f


def listing_features(row: Mapping, distance_km: float | None) -> dict[str, set[str]]:
    """Content features of a business or work profile (skills only when shown)."""
    caps = {str(c) for c in (_get(row, "capabilities") or []) if c}
    if _get(row, "capability_visible") is False:
        caps = set()
    f = {"lskill": caps, "lcat": {str(c) for c in (_get(row, "categories") or [])} | categories_of(caps),
         "lkind": {_get(row, "kind")} if _get(row, "kind") else set(), "ldist": set()}
    if (d := distance_band(distance_km)):
        f["ldist"].add(d)
    return f


def _key(group: str, value: str) -> str:
    return f"{group}:{value}"


# ---------------------------------------------------------------------------
# Events -> model
# ---------------------------------------------------------------------------
@dataclass
class PostEvents:
    """Everything one member did with one post (or one profile)."""

    features: dict[str, set[str]]
    actions: dict[str, datetime]           # action -> when
    hidden_reason: str | None = None
    distance_km: float | None = None
    monthly: int | None = None
    project: int | None = None
    listing: bool = False


def _decay(at: datetime, now: datetime) -> float:
    age = max(0.0, (now - at).total_seconds() / 86400.0)
    return 0.5 ** (age / HALF_LIFE_DAYS)


def _counts(at: datetime, item: str, reset_at: datetime | None, removed: Mapping[str, datetime]) -> bool:
    if reset_at is not None and at <= reset_at:
        return False
    r = removed.get(item)
    return r is None or at > r


def build_model(events: list[PostEvents], *, now: datetime | None = None, reset_at: datetime | None = None,
                removed: Mapping[str, datetime] | None = None) -> dict[str, Any]:
    """The learned model as a JSON-able dict (stored in member_taste.model)."""
    now = now or datetime.now(timezone.utc)
    removed = dict(removed or {})
    w: dict[str, float] = {}
    src_score: dict[str, dict[str, float]] = {}
    n_posts = n_listings = 0
    too_far: list[tuple[datetime, float]] = []
    low_pay_monthly: list[tuple[datetime, int]] = []
    low_pay_project: list[tuple[datetime, int]] = []
    positives: list[tuple[datetime, PostEvents]] = []
    avoid_at: dict[str, datetime] = {}

    # [Recent negative wins] A "Not my skill" answer cancels every positive
    # learned for that skill BEFORE it (it is a correction, not one vote
    # among many); a later application to that trade counts again.
    wrong_trade_at: dict[str, datetime] = {}
    for ev in events:
        at = ev.actions.get("hidden")
        if (at is not None and ev.hidden_reason == "not_my_capability" and (reset_at is None or at > reset_at)
                and (now - at).days <= AVOID_WINDOW_DAYS):
            for sk in ev.features.get("skill", ()):
                if _counts(at, _key("skill", sk), None, removed):
                    wrong_trade_at[sk] = max(at, wrong_trade_at.get(sk, at))

    for ev in events:
        acts = {a: t for a, t in ev.actions.items() if t is not None and (now - t).days <= WINDOW_DAYS
                and (reset_at is None or t > reset_at)}
        if not acts:
            continue
        if any(a in MEANINGFUL for a in acts):
            if ev.listing:
                n_listings += 1
            else:
                n_posts += 1
        if "hidden" in acts:
            at = acts["hidden"]
            reason = ev.hidden_reason or "not_interested"
            groups = REASON_GROUPS.get(reason, None)
            if groups == ():
                continue
            scale = REASON_SCALE.get(reason, 1.0)
            weight = EVENT_WEIGHTS["hidden"] * scale * _decay(at, now)
            for group, values in ev.features.items():
                if groups is not None and group not in groups:
                    continue
                for v in values:
                    k = _key(group, v)
                    if _counts(at, k, None, removed):
                        w[k] = w.get(k, 0.0) + weight
            if reason == "not_my_capability" and (now - at).days <= AVOID_WINDOW_DAYS:
                for s in ev.features.get("skill", ()):
                    if _counts(at, _key("skill", s), None, removed):
                        avoid_at[s] = max(at, avoid_at.get(s, at))
            if reason == "too_far" and ev.distance_km is not None and _counts(at, "distance_limit", None, removed):
                too_far.append((at, ev.distance_km))
            if reason == "value_too_low" and _counts(at, "pay_floor", None, removed):
                if ev.monthly:
                    low_pay_monthly.append((at, ev.monthly))
                elif ev.project:
                    low_pay_project.append((at, ev.project))
            continue
        pos = sorted(((EVENT_WEIGHTS[a], a, t) for a, t in acts.items() if EVENT_WEIGHTS[a] > 0), reverse=True)
        neg = [(EVENT_WEIGHTS[a], a, t) for a, t in acts.items() if EVENT_WEIGHTS[a] < 0]
        contributions: list[tuple[float, str, datetime]] = []
        if pos:
            top_w, top_a, top_t = pos[0]
            contributions.append((top_w * _decay(top_t, now), top_a, top_t))
            for extra_w, extra_a, extra_t in pos[1:]:
                contributions.append((0.25 * extra_w * _decay(extra_t, now), extra_a, extra_t))
            if top_a != "viewed":
                positives.append((top_t, ev))
        for nw, na, nt in neg:
            contributions.append((nw * _decay(nt, now), na, nt))
        for value, action, at in contributions:
            for group, values in ev.features.items():
                for v in values:
                    k = _key(group, v)
                    if not _counts(at, k, None, removed):
                        continue
                    if value > 0 and group == "skill" and v in wrong_trade_at and at <= wrong_trade_at[v]:
                        continue  # cancelled by a later "Not my skill"
                    w[k] = w.get(k, 0.0) + value
                    if value > 0:
                        s = src_score.setdefault(k, {})
                        s[SOURCE_OF.get(action, "other")] = s.get(SOURCE_OF.get(action, "other"), 0.0) + value

    # A skill stays avoided only while its learned weight is negative: applying
    # to that trade again later takes it back.
    avoid = sorted(s for s, at in avoid_at.items() if w.get(_key("skill", s), 0.0) < 0)

    dist_limit = None
    if too_far:
        latest = max(t for t, _ in too_far)
        dist_limit = max(MIN_DISTANCE_LIMIT_KM, 0.85 * min(d for _, d in too_far))
        later = [ev.distance_km for t, ev in positives if t > latest and ev.distance_km is not None and not ev.listing]
        if later:
            dist_limit = max(dist_limit, max(later))
        dist_limit = round(dist_limit, 1)

    def floor_from(lows: list[tuple[datetime, int]], attr: str) -> int | None:
        if not lows:
            return None
        latest = max(t for t, _ in lows)
        floor = int(math.ceil(max(v for _, v in lows) * 1.1 / 50_000.0) * 50_000)  # to the next ₹500
        later = [getattr(ev, attr) for t, ev in positives if t > latest and getattr(ev, attr)]
        if later:
            floor = min(floor, min(later))
        return floor

    usual_km = _percentile([ev.distance_km for _, ev in positives if ev.distance_km is not None and not ev.listing], 0.75)
    usual_monthly = _percentile([ev.monthly for _, ev in positives if ev.monthly], 0.25)
    src = {k: max(v.items(), key=lambda kv: kv[1])[0] for k, v in src_score.items()}
    return {
        "v": 1,
        "w": {k: round(v, 4) for k, v in w.items() if abs(v) >= 0.01},
        "src": {k: v for k, v in src.items() if abs(w.get(k, 0.0)) >= 0.01},
        "n": n_posts,
        "ln": n_listings,
        "avoid": avoid,
        "dist_limit": dist_limit,
        "pay_floor": {"monthly": floor_from(low_pay_monthly, "monthly"), "project": floor_from(low_pay_project, "project")},
        "usual": {"km": round(usual_km, 1) if usual_km is not None else None,
                  "monthly": int(usual_monthly // 100_000 * 100_000) if usual_monthly else None},
    }


def _percentile(values: list[float], q: float) -> float | None:
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    idx = min(len(vals) - 1, max(0, int(math.ceil(q * len(vals))) - 1))
    return float(vals[idx])


# ---------------------------------------------------------------------------
# Using the model
# ---------------------------------------------------------------------------
@dataclass
class Taste:
    """A loaded model, ready for ranking. `Taste.empty()` is the cold start."""

    model: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    @classmethod
    def empty(cls, enabled: bool = True) -> "Taste":
        return cls({}, enabled)

    @property
    def weights(self) -> dict[str, float]:
        return self.model.get("w") or {}

    @property
    def confidence(self) -> float:
        if not self.enabled:
            return 0.0
        return min(1.0, (self.model.get("n") or 0) / FULL_CONFIDENCE_ACTIONS)

    @property
    def listing_confidence(self) -> float:
        if not self.enabled:
            return 0.0
        return min(1.0, (self.model.get("ln") or 0) / FULL_CONFIDENCE_ACTIONS)

    @property
    def active(self) -> bool:
        return self.confidence > 0

    @property
    def avoid(self) -> set[str]:
        return set(self.model.get("avoid") or []) if self.enabled else set()

    @property
    def distance_limit_km(self) -> float | None:
        return self.model.get("dist_limit") if self.enabled else None

    def pay_floor(self, kind: str) -> int | None:
        return (self.model.get("pay_floor") or {}).get(kind) if self.enabled else None

    # -- scoring -----------------------------------------------------------
    def _fit(self, features: dict[str, set[str]], importance: dict[str, float]) -> tuple[float, str | None]:
        w = self.weights
        if not w:
            return 0.0, None
        avoid = self.avoid
        post_skills = set(features.get("skill", ()))
        if post_skills and post_skills <= avoid:
            return 0.0, None  # no taste boost at all for a post in an avoided trade
        max_abs: dict[str, float] = {}
        for k, v in w.items():
            g = k.split(":", 1)[0]
            max_abs[g] = max(max_abs.get(g, 0.0), abs(v))
        total = denom = 0.0
        best_k, best_c = None, 0.0
        for g, imp in importance.items():
            m = max_abs.get(g)
            if not m:
                continue
            denom += imp
            # a skill the member avoids never lends a post a positive boost
            vals = [(w.get(_key(g, v), 0.0) / m, _key(g, v)) for v in features.get(g, ())
                    if not (g == "skill" and v in avoid and w.get(_key(g, v), 0.0) > 0)]
            pos = max((x for x in vals if x[0] > 0), default=(0.0, None))
            neg = min((x[0] for x in vals if x[0] < 0), default=0.0)
            total += imp * (pos[0] + neg)
            if pos[1] is not None and imp * pos[0] > best_c:
                best_c, best_k = imp * pos[0], pos[1]
        if denom == 0:
            return 0.0, None
        fit = max(0.0, min(1.0, total / denom))
        src = (self.model.get("src") or {}).get(best_k) if best_k else None
        return fit, src

    def fit(self, features: dict[str, set[str]]) -> tuple[float, str | None]:
        """(overlap 0..1, where the strongest matching feature came from)."""
        if not self.enabled:
            return 0.0, None
        return self._fit(features, GROUP_IMPORTANCE)

    def signal(self, features: dict[str, set[str]]) -> float:
        """The value of the `taste_fit` ranking signal: overlap x confidence,
        so its weight ramps from 0 (no history) to full (10 actions)."""
        if not self.active:
            return 0.0
        return round(self.fit(features)[0] * self.confidence, 4)

    def listing_signal(self, features: dict[str, set[str]]) -> float:
        if self.listing_confidence <= 0:
            return 0.0
        return round(self._fit(features, LISTING_GROUP_IMPORTANCE)[0] * self.listing_confidence, 4)

    def reason_key(self, features: dict[str, set[str]]) -> str:
        """Which "Why this?" phrase a taste match gets."""
        _, src = self.fit(features)
        return {"applied": "taste_fit_applied", "saved": "taste_fit_saved",
                "more_like_this": "taste_fit_more_like_this"}.get(src or "", "taste_fit")

    def value_fit(self, row: Mapping) -> float:
        """[Pay too low] value_fit against the member's raised pay floor; 0 when
        there is no floor for this kind of post (exactly the old behaviour)."""
        m, p = monthly_top(row), project_top(row)
        floor = self.pay_floor("monthly") if _get(row, "type") == "employment" else (
            self.pay_floor("project") if _get(row, "type") in PROJECT_TYPES else None)
        if not floor:
            return 0.0
        pay = m if m is not None else p
        if pay is None:
            return 0.3
        return 1.0 if pay >= floor else 0.0

    def is_avoided(self, row: Mapping) -> bool:
        """[Not my skill] a post whose skills are all ones the member avoided."""
        avoid = self.avoid
        if not avoid:
            return False
        skills = skill_slugs(row)
        if skills:
            return skills <= avoid
        from app.trade_match import trade_matcher

        m = trade_matcher(sorted(avoid))
        return bool(m and m.matches([], _get(row, "title")))

    def beyond_limit(self, row: Mapping, distance_km: float | None) -> bool:
        """[Too far] an on-site post farther than the member's learned limit."""
        lim = self.distance_limit_km
        return bool(lim and distance_km is not None and _get(row, "work_mode") != "remote" and distance_km > lim)

    def demoted(self, row: Mapping, distance_km: float | None) -> bool:
        return self.is_avoided(row) or self.beyond_limit(row, distance_km)

    def skill_weight(self, slug: str) -> float:
        return self.weights.get(_key("skill", slug), 0.0)

    def top(self, group: str, source: str | None = None, positive: bool = True, limit: int = 3) -> list[str]:
        src = self.model.get("src") or {}
        avoid = self.avoid if (group == "skill" and positive) else set()
        items = [(v, k.split(":", 1)[1]) for k, v in self.weights.items()
                 if k.startswith(group + ":") and ((v > 0) if positive else (v < 0))
                 and (source is None or src.get(k) == source) and k.split(":", 1)[1] not in avoid]
        items.sort(key=lambda t: (-abs(t[0]), t[1]))
        return [v for _, v in items[:limit]]
