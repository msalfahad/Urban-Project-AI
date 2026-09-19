"""A canonical group registry for tests, and a parse helper that uses it.

Every semantic record now needs a registry to validate its identifiers against.
Tests share one rather than each building its own, so a change to what a
canonical id looks like breaks in one place.
"""

from __future__ import annotations

from agents.a1_extractor.semantic import SemanticOutput
from engine.group_registry import APARTMENT, ZONE, CanonicalGroup, GroupRegistry

REG = GroupRegistry(
    project="TEST",
    apartments={
        "APT-001": CanonicalGroup(
            id="APT-001", kind=APARTMENT,
            definition="the dwelling reached from the main stair landing",
            provenance="OWNER_SCOPE_BRIEF"),
        "APT-002": CanonicalGroup(
            id="APT-002", kind=APARTMENT,
            definition="the staff block reached from the service corridor",
            provenance="OWNER_SCOPE_BRIEF"),
    },
    zone_not_defined_reason="no approved zone ontology for the test project",
)

ZONED = GroupRegistry(
    project="TEST-ZONED",
    apartments=dict(REG.apartments),
    zones={
        "ZONE-001": CanonicalGroup(
            id="ZONE-001", kind=ZONE, definition="wet core",
            provenance="DETERMINISTIC_TOPOLOGY"),
        "ZONE-002": CanonicalGroup(
            id="ZONE-002", kind=ZONE, definition="dry rooms",
            provenance="DETERMINISTIC_TOPOLOGY"),
    },
)


def parse(data, registry: GroupRegistry = REG) -> SemanticOutput:
    return SemanticOutput.from_dict(data, registry=registry)
