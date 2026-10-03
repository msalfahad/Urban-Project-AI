"""E24R — Canonical group registry: apartments and zones.

Run 0 compared `apartment_id` and `zone_id` by string equality while both were
free text the model chose for itself. A1 wrote APT-EAST / ZONE-EAST-RESIDENTIAL,
A2 wrote APT-01 / BEDROOM_WING_NORTH, and E32 scored 0% agreement on both. That
number measured the schema, not the agents: the two may denote the same rooms at
different granularity, and nothing in the comparison could tell.

The fix is not fuzzy matching. It is to stop asking a language model for an
identifier at all. The deterministic layer issues canonical ids BEFORE either
agent runs, and the agents may only choose among them:

    APT-001 / APT-002 / ... / UNKNOWN / AMBIGUOUS

A group carries a DEFINITION — the criterion that decides membership — and its
PROVENANCE. It may also carry an authoritative member list, in which case the
agents are being asked to reproduce a known answer rather than to derive one;
on Project 23010 it deliberately does not, because apartment membership is part
of what the acceptance test measures.

The second half of this module is the part that says no. A registry that cannot
define zones says NOT_DEFINED, and then the only zone_id any agent may return is
UNKNOWN. Manufacturing ZONE-001..ZONE-003 so a metric has something to compare
would make the test pass by making it meaningless: "apartment membership" and
"zone segmentation" are different concepts, and an ontology has to exist before
a field about it can be scored.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

APARTMENT = "APARTMENT"
ZONE = "ZONE"
KINDS = (APARTMENT, ZONE)

# A group hierarchy that does not exist. Never a synonym for "empty but usable".
NOT_DEFINED = "NOT_DEFINED"

# The two answers that are always available, and always mean something precise.
# UNKNOWN: the evidence does not place this space in any group.
# AMBIGUOUS: the evidence places it in more than one and cannot choose.
UNKNOWN = "UNKNOWN"
AMBIGUOUS = "AMBIGUOUS"
RESERVED = (UNKNOWN, AMBIGUOUS)

_ID_PATTERN = {APARTMENT: re.compile(r"^APT-\d{3}$"), ZONE: re.compile(r"^ZONE-\d{3}$")}

# Where a group definition is allowed to come from. DETERMINISTIC_TOPOLOGY is
# the one the architecture wants; the others are honest about being human.
PROVENANCE = {
    "DETERMINISTIC_TOPOLOGY",   # derived by the engine from door/wall connectivity
    "APPROVED_DRAWING",         # printed on the approved sheet
    "OWNER_SCOPE_BRIEF",        # the owner's written instruction for this project
    "HUMAN_APPROVED",           # an engineer decided and signed it
}


class GroupRegistryError(RuntimeError):
    """A group id, definition or assignment that the registry will not accept."""


@dataclass(frozen=True)
class CanonicalGroup:
    """One canonical group. The id is the identity; the text is commentary."""

    id: str
    kind: str
    definition: str
    provenance: str
    # Authoritative membership, when it is known independently of the agents.
    # None means "the agents are being asked to derive this" — which is not the
    # same as an empty tuple, which would mean "known to contain nothing".
    member_space_ids: tuple[str, ...] | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise GroupRegistryError(f"{self.id}: kind {self.kind!r} is not one of {KINDS}")
        if self.id in RESERVED:
            raise GroupRegistryError(
                f"{self.id} is reserved — it is an answer, not a group")
        if not _ID_PATTERN[self.kind].match(self.id):
            raise GroupRegistryError(
                f"{self.id!r} is not a canonical {self.kind} id "
                f"(expected {_ID_PATTERN[self.kind].pattern}). Free text is exactly "
                "the defect this registry exists to remove.")
        if not self.definition.strip():
            raise GroupRegistryError(
                f"{self.id}: a group needs a definition — the criterion that decides "
                "membership. Without one nobody can say whether an assignment is right.")
        if self.provenance not in PROVENANCE:
            raise GroupRegistryError(
                f"{self.id}: provenance {self.provenance!r} is not one of "
                f"{sorted(PROVENANCE)}")

    @property
    def membership_is_authoritative(self) -> bool:
        return self.member_space_ids is not None


@dataclass
class GroupRegistry:
    """Every canonical group for one project, plus what is honestly missing."""

    project: str
    apartments: dict[str, CanonicalGroup] = field(default_factory=dict)
    # A dict of zones, or the NOT_DEFINED sentinel. Nothing in between.
    zones: dict[str, CanonicalGroup] | str = NOT_DEFINED
    zone_not_defined_reason: str = ""
    version: str = "1.0"
    effective_from: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        if self.zones == NOT_DEFINED and not self.zone_not_defined_reason.strip():
            raise GroupRegistryError(
                f"{self.project}: zones are NOT_DEFINED but no reason is recorded. "
                "A missing ontology is a finding, so it gets written down.")
        for kind, groups in ((APARTMENT, self.apartments), (ZONE, self.zones)):
            if isinstance(groups, str):
                continue
            for gid, g in groups.items():
                if gid != g.id:
                    raise GroupRegistryError(f"{gid} is keyed under the wrong id ({g.id})")
                if g.kind != kind:
                    raise GroupRegistryError(f"{gid} is a {g.kind} filed under {kind}")

    # ---- what an agent is allowed to say -------------------------------------

    @property
    def zone_ontology_defined(self) -> bool:
        return self.zones != NOT_DEFINED

    def groups(self, kind: str) -> dict[str, CanonicalGroup]:
        if kind == APARTMENT:
            return self.apartments
        if kind == ZONE:
            return {} if not self.zone_ontology_defined else self.zones  # type: ignore[return-value]
        raise GroupRegistryError(f"unknown kind {kind!r}")

    def allowed(self, kind: str) -> set[str]:
        """The complete set of values an agent may return for this field.

        With no ontology the only permitted answer is UNKNOWN — not AMBIGUOUS,
        because there is nothing to be ambiguous BETWEEN. That distinction keeps
        "we never defined zones" from being filed as "the drawing was unclear".
        """
        if kind == ZONE and not self.zone_ontology_defined:
            return {UNKNOWN}
        return set(self.groups(kind)) | set(RESERVED)

    def validate_assignment(self, kind: str, value: str, *, space_id: str = "") -> None:
        where = f"{space_id}: " if space_id else ""
        allowed = self.allowed(kind)
        if value not in allowed:
            if kind == ZONE and not self.zone_ontology_defined:
                raise GroupRegistryError(
                    f"{where}zone_id must be {UNKNOWN} on project {self.project}: no "
                    f"zone ontology is defined ({self.zone_not_defined_reason}). "
                    f"{value!r} would be an invented hierarchy.")
            raise GroupRegistryError(
                f"{where}{kind.lower()}_id {value!r} is not a canonical id for project "
                f"{self.project}. Allowed: {sorted(allowed)}")

    def scorable(self, kind: str) -> tuple[bool, str]:
        """May this field enter the acceptance metric, and if not, why not."""
        if kind == ZONE and not self.zone_ontology_defined:
            return False, f"no zone ontology for {self.project}: {self.zone_not_defined_reason}"
        if not self.groups(kind):
            return False, f"no canonical {kind.lower()} groups defined for {self.project}"
        return True, ""

    # ---- loading -------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "GroupRegistry":
        def build(kind: str, raw) -> dict[str, CanonicalGroup] | str:
            if raw == NOT_DEFINED or raw is None:
                return NOT_DEFINED
            return {
                gid: CanonicalGroup(
                    id=gid,
                    kind=kind,
                    definition=g.get("definition", ""),
                    provenance=g.get("provenance", ""),
                    member_space_ids=(tuple(g["member_space_ids"])
                                      if g.get("member_space_ids") is not None else None),
                    note=g.get("note", ""),
                )
                for gid, g in raw.items()
            }

        apartments = build(APARTMENT, data.get("apartments", {}))
        if isinstance(apartments, str):
            raise GroupRegistryError(
                f"{data.get('project')}: apartments cannot be NOT_DEFINED — a floor "
                "belongs to at least one dwelling. Define the groups or the agents "
                "have nowhere to put a space.")
        return cls(
            project=data["project"],
            apartments=apartments,
            zones=build(ZONE, data.get("zones", NOT_DEFINED)),
            zone_not_defined_reason=data.get("zone_not_defined_reason", ""),
            version=data.get("version", "1.0"),
            effective_from=data.get("effective_from", ""),
            source=data.get("source", ""),
        )

    @classmethod
    def load(cls, path: str | Path) -> "GroupRegistry":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def membership(spaces, kind: str) -> dict[str, set[str]]:
    """group id -> the set of space ids assigned to it.

    Set membership is what `apartment_id` actually MEANS. Comparing the sets is
    the migration diagnostic that would have shown Run 0's APT-EAST and APT-01
    to be the same apartment; canonical ids are what production compares.
    """
    attr = {APARTMENT: "apartment_id", ZONE: "zone_id"}[kind]
    out: dict[str, set[str]] = {}
    for s in spaces:
        out.setdefault(getattr(s, attr), set()).add(s.space_id)
    return out
