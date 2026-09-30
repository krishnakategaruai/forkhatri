# [IMP-B, owner 2026-09-30] "Rahul tapped Plumbers and got 0 opportunities."
#
# A trade filter must return that trade's posts however the post describes
# the trade. The one matcher every feed surface uses:
#   * a CATEGORY slug (home_repair) means every skill under it (plumbing,
#     electrical, carpenter, ...);
#   * a skill matches a post whose required skills contain its slug, OR a
#     free-text skill naming it ("plumber", "Plumbing work"), OR whose title
#     names it — using the skill's names in en/hi/te and its aliases
#     (migration 026 added the words people type: plumber, electrician, दर्जी,
#     ప్లంబర్ ...).
# ASCII words match at a word start ("plumb" never matches "plumbago"-style
# accidents inside a word); Devanagari/Telugu words match as substrings (word
# boundaries are unreliable across combining marks).
# Traces to: FR15, FR18, FR19
from __future__ import annotations

import re
from dataclasses import dataclass

from app.taxonomy_cache import children_of, term_for


@dataclass(frozen=True)
class TradeMatcher:
    slugs: frozenset[str]
    words: tuple[str, ...]
    _ascii: re.Pattern | None
    _other: tuple[str, ...]

    def matches(self, required_capabilities, title: str | None) -> bool:
        req = list(required_capabilities or [])
        if self.slugs & set(req):
            return True
        texts = [str(c).replace("_", " ").lower() for c in req] + [(title or "").lower()]
        for t in texts:
            if self._ascii is not None and self._ascii.search(t):
                return True
            if any(w in t for w in self._other):
                return True
        return False

    def sql_regex(self) -> str | None:
        """A Postgres ARE (case-insensitive with ~*) equivalent of the word test."""
        parts = [r"\m" + _pg_escape(w) for w in self.words if w.isascii()] + [_pg_escape(w) for w in self.words if not w.isascii()]
        return "(" + "|".join(parts) + ")" if parts else None


def _pg_escape(w: str) -> str:
    return re.sub(r"([.^$*+?()\[\]{}|\\])", r"\\\1", w)


def expand_slugs(slugs: list[str]) -> set[str]:
    out: set[str] = set()
    for s in slugs:
        kids = children_of(s)
        if kids:
            out.update(kids)
            out.add(s)
        else:
            out.add(s)
    return out


def trade_matcher(slugs: list[str]) -> TradeMatcher | None:
    if not slugs:
        return None
    expanded = expand_slugs(slugs)
    words: set[str] = set()
    for s in expanded:
        term = term_for("capability", s)
        words.add(s.replace("_", " ").lower())
        if term is not None:
            words.update(n.lower() for n in term.names.values() if n)
            words.update(a.lower() for a in term.aliases if a)
    words = {w.strip() for w in words if len(w.strip()) >= 3}
    ascii_words = sorted((w for w in words if w.isascii()), key=len, reverse=True)
    pattern = re.compile(r"\b(" + "|".join(re.escape(w) for w in ascii_words) + r")", re.I) if ascii_words else None
    return TradeMatcher(frozenset(expanded), tuple(sorted(words)), pattern, tuple(w for w in words if not w.isascii()))
