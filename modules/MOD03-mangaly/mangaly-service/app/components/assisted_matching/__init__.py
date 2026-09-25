"""Assisted Matching component — a named relationship manager (DEC-V1-032).

Owns `mangaly_operations.relationship_manager`, `rm_assignment`,
`rm_suggestion` and `rm_interaction` (migration 052). To be merged with the
operator concept (`mangaly_operations.operator`, migration 048 stream) later.

# [MODULE-ARCHITECTURE-STANDARD §3 / CODING-GUIDE.md §2] This package exposes
# exactly ONE public module other components may import: `interface.py`.
"""
