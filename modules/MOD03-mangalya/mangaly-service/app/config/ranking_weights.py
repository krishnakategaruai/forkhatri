"""DEC-V1-002's fixed, versioned Discovery ranking weights, as configuration.

# [TR026/TR028/FR028] A named list, not a rule each call site re-derives, and
# never popularity: `POPULARITY` is defined at 0.0 and no code path anywhere
# reads an engagement/view metric into this — the constant exists so a future
# read of this file states that omission explicitly rather than leaving a
# silent gap someone might "helpfully" fill in later.
# Traces to: TR026, TR028, FR026, FR028, DEC-V1-002, DEC-V1-030.
"""

from __future__ import annotations

from typing import Final

# [2026-09-28] The five DEC-V1-002 weights that used to sit here (locality,
# partner preference, reciprocity, lifestyle, evidence) were superseded by the
# AI matching engine (config/matching_engine.py, DEC-V1-031) and no code read
# them any more. Popularity is still never an input anywhere.

# DEC-V1-002's diversity re-rank: after the weighted sort, no more than
# MAX_SAME_BRACKET_RUN results in a row may share one of SCORE_BRACKETS equal
# bands of the 0-1 score.
SCORE_BRACKETS: Final[int] = 10
MAX_SAME_BRACKET_RUN: Final[int] = 3

# [DEC-V1-030] The daily stable-matching pass ("Most compatible today"): each
# proposer's list is capped at this many people, ranked by reciprocity, and
# the pass is re-run this many times so a person has fallbacks when their
# first stable choice is already connected, requested or blocked by the time
# they open Discover.
DAILY_PICK_LIST_CAP: Final[int] = 50
DAILY_PICK_ROUNDS: Final[int] = 3
# How old a stored pick may be before Discover stops showing it (the daily job
# not having run for this long is an operations problem, not a reason to show
# a week-old "today").
DAILY_PICK_MAX_AGE_DAYS: Final[int] = 3

# v2: the partner-preference term counts both people's stated preferences
# (a two-way match), and the diversity re-rank runs after the weighted sort.
# v3 (DEC-V1-030): a reciprocity term — the harmonic mean of each side's fit
# for the other — and the partner-preference checks grow height, education and
# diet preferences alongside age and locality.
# v4 (2026-09-28): the daily pick scores pairs with the AI engine's
# pair score, the same number that orders Discover.
RANKING_WEIGHTS_VERSION: Final[str] = "DEC-V1-002.v4"
