"""Notification Bridge component.

Component package for MangalyService. Traces to: FR098.
Owns the `mangaly_notification` schema.

Thin for delivery (Common Platform owns that); owns the in-app inbox record. [SP098] Inbox
payloads carry an event type and reference only — never message content or counterparty
identifying detail.

# [MODULE-ARCHITECTURE-STANDARD §3 / CODING-GUIDE.md §2] This package exposes
# exactly ONE public module other components may import: `interface.py`.
# Everything else here (`models.py`, repositories, private services) is internal
# to this component. Cross-component side effects go through the event bus
# (`app/events/bus.py`), never a direct import of another component's internals.
# Every `interface.py` method that reads or writes consequential data takes an
# already-resolved `AuthzContext` — never a bare actor id (CODING-GUIDE.md §3).
"""
