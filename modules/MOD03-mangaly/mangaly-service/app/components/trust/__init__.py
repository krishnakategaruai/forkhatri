"""Trust component.

Component package for MangalyService. Traces to: BR08.
Owns the `mangaly_trust` schema.

Six independent evidence layers. Raw verification documents are readable only by Operations (TR040).

# [MODULE-ARCHITECTURE-STANDARD §3 / CODING-GUIDE.md §2] This package exposes
# exactly ONE public module other components may import: `interface.py`.
# Everything else here (`models.py`, repositories, private services) is internal
# to this component. Cross-component side effects go through the event bus
# (`app/events/bus.py`), never a direct import of another component's internals.
# Every `interface.py` method that reads or writes consequential data takes an
# already-resolved `AuthzContext` — never a bare actor id (CODING-GUIDE.md §3).
"""
