"""Safety component.

Component package for MangalyService. Traces to: BR14, BR20-reporting.
Owns the `mangaly_safety` schema.

Its repository layer must have NO method capable of reading Home Circle or Trust/Verification
tables at all — an absence, not an unused method (TR064, CODING-GUIDE.md §7).

# [MODULE-ARCHITECTURE-STANDARD §3 / CODING-GUIDE.md §2] This package exposes
# exactly ONE public module other components may import: `interface.py`.
# Everything else here (`models.py`, repositories, private services) is internal
# to this component. Cross-component side effects go through the event bus
# (`app/events/bus.py`), never a direct import of another component's internals.
# Every `interface.py` method that reads or writes consequential data takes an
# already-resolved `AuthzContext` — never a bare actor id (CODING-GUIDE.md §3).
"""
