"""Authorization component.

Component package for MangalyService. Traces to: BR04, BR05.
Owns the `mangaly_authz` schema.

The chokepoint. The only component permitted to resolve the BR04 chain and the only one that
sets `mangaly.authz_context` (CODING-GUIDE.md §3).

# [MODULE-ARCHITECTURE-STANDARD §3 / CODING-GUIDE.md §2] This package exposes
# exactly ONE public module other components may import: `interface.py`.
# Everything else here (`models.py`, repositories, private services) is internal
# to this component. Cross-component side effects go through the event bus
# (`app/events/bus.py`), never a direct import of another component's internals.
# Every `interface.py` method that reads or writes consequential data takes an
# already-resolved `AuthzContext` — never a bare actor id (CODING-GUIDE.md §3).
"""
