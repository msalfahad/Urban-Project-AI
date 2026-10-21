"""E45 — room templates and trade assemblies, versioned and approved.

The PlanSwift idea worth copying is the assembly: a named, reusable definition
of what a trade needs before it can measure something. The part NOT worth
copying is that in those tools an assembly silently supplies defaults. Here it
supplies REQUIREMENTS. An assembly that cannot find its inputs blocks; it never
fills them in.

    NULL RULE SET MUST NEVER MEAN DEFAULT RULE.

A room template says what trades COULD apply to a kind of room. It does not say
they do apply to this room on this project — scope decides that — and it never
invents a quantity. A bathroom template naming CERAMIC_WALL means "ask the
ceramic rule about this room", not "this room has ceramic".

VERSIONING IS THE POINT. A future project must be able to say "BATHROOM
template V3", and a historical run must still reproduce with the version it
actually used. So a version is never edited in place: a change makes a new
version, and the old one stays readable forever.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

DRAFT = "DRAFT"
APPROVED = "APPROVED"
SUPERSEDED = "SUPERSEDED"
WITHDRAWN = "WITHDRAWN"

# Only an APPROVED version may be applied to a quantity. A draft is a proposal.
APPLICABLE_STATUSES = (APPROVED,)

VERSION = re.compile(r"^V(\d+)$")


class TemplateError(RuntimeError):
    """A template was applied that nobody approved, or that invents a value."""


@dataclass(frozen=True)
class Versioned:
    """The provenance every rule, template and assembly must carry.

    An LLM may propose one of these. It may not approve one — approval is a
    human act with a name and a date attached, and the engine checks for both.
    """

    version: str
    approval_status: str = DRAFT
    approved_by: str = ""
    approved_on: str = ""
    source: str = ""
    supersedes: str = ""

    def __post_init__(self):
        if not VERSION.match(self.version):
            raise TemplateError(
                f"version {self.version!r} must look like V1, V2, V3. "
                "'bathroom rule' is not a version and cannot be reproduced")
        if self.approval_status == APPROVED and not (
                self.approved_by and self.approved_on):
            raise TemplateError(
                "an APPROVED version needs approved_by and approved_on. An "
                "approval with nobody's name on it is not an approval")

    @property
    def applicable(self) -> bool:
        return self.approval_status in APPLICABLE_STATUSES

    def record(self) -> dict:
        return {"version": self.version, "approval_status": self.approval_status,
                "approved_by": self.approved_by, "approved_on": self.approved_on,
                "source": self.source, "supersedes": self.supersedes}


@dataclass(frozen=True)
class RoomTemplate:
    """What trades COULD apply to a kind of room, and what they would need.

    Possible, not actual. The template is a question to ask, never an answer.
    """

    template_id: str
    room_type: str
    versioned: Versioned
    possible_trades: tuple[str, ...] = ()
    required_inputs: tuple[str, ...] = ()
    review_required: tuple[str, ...] = ()
    notes: str = ""

    def applies_to(self, room_type: str) -> bool:
        return self.room_type == room_type and self.versioned.applicable

    def record(self) -> dict:
        return {"template_id": self.template_id, "room_type": self.room_type,
                "possible_trades": list(self.possible_trades),
                "required_inputs": list(self.required_inputs),
                "review_required": list(self.review_required),
                "notes": self.notes, **self.versioned.record()}


@dataclass(frozen=True)
class TradeAssembly:
    """One trade's recipe for WHAT IT NEEDS — never for what it produces.

    `formula_reference` names the engine function that computes the quantity.
    It is a reference on purpose: the assembly must not be able to carry an
    arithmetic expression, because then the assembly would be a second place
    quantities come from.
    """

    assembly_id: str
    trade: str
    versioned: Versioned
    required_geometry: tuple[str, ...] = ()
    required_rules: tuple[str, ...] = ()
    required_heights: tuple[str, ...] = ()
    required_openings: bool = False
    formula_reference: str = ""
    unit: str = ""
    waste_rule_id: str = ""      # declared, deliberately unused until later
    notes: str = ""

    def __post_init__(self):
        for bad in ("*", "+", "/", "=") if self.formula_reference else ():
            if bad in self.formula_reference:
                raise TemplateError(
                    f"{self.assembly_id}: formula_reference must NAME an engine "
                    "function, not carry arithmetic. An assembly that can "
                    "compute is a second source of truth for a quantity")

    def missing(self, established: dict) -> list[str]:
        """What this assembly still needs. Nothing is assumed present."""
        out = [g for g in self.required_geometry if not established.get(g)]
        out += [r for r in self.required_rules if not established.get(r)]
        out += [h for h in self.required_heights if not established.get(h)]
        if self.required_openings and not established.get("openings"):
            out.append("openings")
        return out

    def record(self) -> dict:
        return {"assembly_id": self.assembly_id, "trade": self.trade,
                "required_geometry": list(self.required_geometry),
                "required_rules": list(self.required_rules),
                "required_heights": list(self.required_heights),
                "required_openings": self.required_openings,
                "formula_reference": self.formula_reference, "unit": self.unit,
                "waste_rule_id": self.waste_rule_id, "notes": self.notes,
                **self.versioned.record()}


@dataclass
class TemplateLibrary:
    """Every template and assembly a run used, with its version."""

    rooms: list[RoomTemplate] = field(default_factory=list)
    assemblies: list[TradeAssembly] = field(default_factory=list)

    def room_template(self, room_type: str) -> RoomTemplate | None:
        """The approved template for a room type, or None.

        None means no approved template exists. It does NOT mean "use a
        default" — there is no default, and a caller that treats None as one is
        the failure mode this whole library is built against.
        """
        for t in self.rooms:
            if t.applies_to(room_type):
                return t
        return None

    def assembly(self, assembly_id: str) -> TradeAssembly | None:
        for a in self.assemblies:
            if a.assembly_id == assembly_id and a.versioned.applicable:
                return a
        return None

    def coverage(self, room_types) -> dict:
        """Which room types on this project have an approved template."""
        have, missing = [], []
        for rt in sorted(set(room_types)):
            (have if self.room_template(rt) else missing).append(rt)
        return {"room_types": len(have) + len(missing),
                "with_approved_template": have,
                "without_approved_template": missing}

    def summary(self) -> dict:
        return {
            "room_templates": len(self.rooms),
            "approved_room_templates": sum(
                1 for t in self.rooms if t.versioned.applicable),
            "assemblies": len(self.assemblies),
            "approved_assemblies": sum(
                1 for a in self.assemblies if a.versioned.applicable),
            "by_status": dict(Counter(
                [t.versioned.approval_status for t in self.rooms]
                + [a.versioned.approval_status for a in self.assemblies])),
        }


# The room types this business actually builds. Declared as a vocabulary, not
# as templates: naming a room type is not approving a rule for it, and the
# library above is empty until somebody signs one.
ROOM_TYPES = (
    "BATHROOM", "MASTER_BATHROOM", "KITCHEN", "DIRTY_KITCHEN", "BEDROOM",
    "MASTER_BEDROOM", "SALON", "DINING", "OPEN_PLAN_LIVING", "IRON_ROOM",
    "LAUNDRY", "STORE", "CORRIDOR", "TERRACE", "STAIR", "WASHROOM",
    "MAID_ROOM", "SHAFT", "SALOON",
)

# The assemblies the trades will need, named so the gap is visible. Each is a
# SLOT, not a definition: an assembly exists when somebody approves one.
PLANNED_ASSEMBLIES = (
    "CERAMIC_WALL_STANDARD", "PLASTER_INTERNAL", "BLOCKWORK_STANDARD",
    "WATERPROOFING_BATHROOM", "SKIRTING_STANDARD", "PAINT_INTERNAL",
    "CEILING_STANDARD", "EXTERNAL_FINISH_STANDARD",
)
