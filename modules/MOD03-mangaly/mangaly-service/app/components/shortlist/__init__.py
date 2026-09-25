"""Shortlist component.

[Rework contract §3, 2026-09-17] "Save" on a Discover card. Context-scoped:
a shortlist belongs to the candidate's search it was made in and is shared
with that candidate's circle (migration 032, `mangaly_discovery.shortlist`).

# [MODULE-ARCHITECTURE-STANDARD §3 / CODING-GUIDE.md §2] This package exposes
# exactly ONE public module other components may import: `interface.py`.
"""
