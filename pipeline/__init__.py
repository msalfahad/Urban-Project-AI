"""Pipelines wire the engine and (later) agents into end-to-end flows.

Phase 0 is the only one built: Excel → audit → review/approve → structured BOQ →
test-only Firestore write.
"""
