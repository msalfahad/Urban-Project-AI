"""Which quantities may be released, and exactly what each one needs.

One global rule — "openings unresolved, so no wall quantity" — would be both too
strict and too loose. Too strict because a GROSS ceramic wall area does not need
the openings; the trade rule decides whether to deduct them, and a gross figure
with the deduction still pending is a useful, honest number. Too loose because
blockwork needs the openings AND the physical-wall split AND a thickness, and a
single "geometry is fine" flag would wave all three through.

So each quantity declares its own dependencies, and the answer to "can I release
this?" is a list of the ones that are missing rather than a boolean. A gross
figure is never presented as a net one: they are different USES with different
names, and NET_CERAMIC_WALL requires what GROSS_CERAMIC_WALL does not.

Nothing here defaults. A dependency that has not been established blocks, and the
block names itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# The things a quantity can depend on. Each is established elsewhere and asked
# about here.
REGION_IDENTITY = "region_identity"          # is this polygon the space we think?
CLOSED_BOUNDARY = "closed_boundary"          # does the outline close?
PHYSICAL_WALL_SPLIT = "physical_wall_split"  # masonry vs doorway closure known?
EXTERNAL_SPLIT = "external_split"            # internal vs external established?
OPENINGS = "openings"                        # openings identified and typed?
WALL_THICKNESS = "wall_thickness"            # proven, not assumed
FLOOR_AREA = "floor_area"
HEIGHT = "height"                            # a releasable height for this trade
TRADE_RULE = "trade_rule"                    # a rule covering this space type
OPENING_RULE = "opening_rule"                # how THIS trade deducts openings
SCOPE = "scope"                              # the space is in the job

READY = "READY"
BLOCKED = "BLOCKED"
NOT_READY = "NOT_READY"


@dataclass(frozen=True)
class Use:
    """One kind of quantity, and everything it needs before it may be released."""

    name: str
    requires: tuple[str, ...]
    description: str
    gross_of: str = ""        # the NET use this one is the undeducted form of

    @property
    def is_gross(self) -> bool:
        return bool(self.gross_of)


# The dependency graph. A GROSS use deliberately omits OPENINGS and OPENING_RULE:
# that is the whole reason it exists as a separate, releasable answer.
USES: dict[str, Use] = {u.name: u for u in (
    Use("GROSS_PERIMETER", (SCOPE, REGION_IDENTITY, CLOSED_BOUNDARY),
        "the closed outline of a space, open transitions included"),

    Use("GROSS_WALL_AREA", (SCOPE, REGION_IDENTITY, CLOSED_BOUNDARY, HEIGHT),
        "applicable wall length x a trade height, before any deduction"),

    Use("SKIRTING", (SCOPE, REGION_IDENTITY, CLOSED_BOUNDARY, OPENINGS,
                     TRADE_RULE, OPENING_RULE),
        "linear metres along applicable boundary, never derived from floor area"),

    Use("GROSS_CERAMIC_WALL", (SCOPE, REGION_IDENTITY, CLOSED_BOUNDARY, HEIGHT,
                               TRADE_RULE),
        "wet-room wall area before opening deductions",
        gross_of="NET_CERAMIC_WALL"),

    Use("NET_CERAMIC_WALL", (SCOPE, REGION_IDENTITY, CLOSED_BOUNDARY, HEIGHT,
                             TRADE_RULE, OPENINGS, OPENING_RULE),
        "ceramic wall area after this trade's opening rule"),

    Use("GROSS_PLASTER", (SCOPE, REGION_IDENTITY, CLOSED_BOUNDARY, HEIGHT,
                          TRADE_RULE),
        "plaster area before deductions", gross_of="NET_PLASTER"),

    Use("NET_PLASTER", (SCOPE, REGION_IDENTITY, CLOSED_BOUNDARY, HEIGHT,
                        TRADE_RULE, OPENINGS, OPENING_RULE),
        "plaster area after this trade's opening rule"),

    Use("PAINT", (SCOPE, REGION_IDENTITY, CLOSED_BOUNDARY, HEIGHT, TRADE_RULE,
                  OPENINGS, OPENING_RULE),
        "computed independently of plaster: ceramic, stone or cladding may "
        "cover surfaces plaster covered"),

    Use("BLOCKWORK", (SCOPE, REGION_IDENTITY, CLOSED_BOUNDARY,
                      PHYSICAL_WALL_SPLIT, EXTERNAL_SPLIT, HEIGHT, OPENINGS,
                      OPENING_RULE, WALL_THICKNESS),
        "masonry only: a doorway closure is not a wall, and thickness decides "
        "the block type"),

    Use("EXTERNAL_FINISH", (SCOPE, REGION_IDENTITY, CLOSED_BOUNDARY,
                            EXTERNAL_SPLIT, HEIGHT, TRADE_RULE),
        "anything priced differently outside than in"),

    Use("WATERPROOFING_HORIZONTAL", (SCOPE, REGION_IDENTITY, FLOOR_AREA,
                                     TRADE_RULE),
        "wet floors, terraces, roofs — an area, not a wall run"),

    Use("WATERPROOFING_VERTICAL", (SCOPE, REGION_IDENTITY, CLOSED_BOUNDARY,
                                   HEIGHT, TRADE_RULE),
        "upstand height x applicable boundary, from the project specification"),

    Use("CEILING", (SCOPE, REGION_IDENTITY, FLOOR_AREA, TRADE_RULE),
        "never assumed equal to floor area where a void, shaft, drop or double "
        "height exists"),
)}


@dataclass
class Readiness:
    use: str
    status: str
    missing: list[str] = field(default_factory=list)
    reasons: dict[str, str] = field(default_factory=dict)

    @property
    def ready(self) -> bool:
        return self.status == READY

    def explain(self) -> str:
        if self.ready:
            return f"{self.use}: READY"
        parts = [f"{d} — {self.reasons.get(d, 'not established')}"
                 for d in self.missing]
        return f"{self.use}: {self.status} (needs " + "; ".join(parts) + ")"


class ReleaseMatrixError(RuntimeError):
    """A use that does not exist, or a dependency answered with something odd."""


def assess(use: str, established: dict[str, bool], *,
           reasons: dict[str, str] | None = None) -> Readiness:
    """Can this quantity be released, and if not, precisely what is missing.

    `established` maps a dependency to True/False. A dependency that is absent
    from the mapping is NOT assumed satisfied — silence is the commonest way a
    default sneaks in, so it counts as missing and says so.
    """
    if use not in USES:
        raise ReleaseMatrixError(
            f"unknown use {use!r}. Known: {sorted(USES)}. A quantity whose "
            "dependencies nobody has written down cannot be released.")
    reasons = dict(reasons or {})
    spec = USES[use]
    missing = []
    for dep in spec.requires:
        if dep not in established:
            missing.append(dep)
            reasons.setdefault(dep, "never established — not the same as satisfied")
        elif not established[dep]:
            missing.append(dep)
    return Readiness(use, READY if not missing else NOT_READY, missing, reasons)


def matrix(established: dict[str, bool], *,
           reasons: dict[str, str] | None = None) -> dict[str, Readiness]:
    """Every use, assessed against the same set of established facts."""
    return {name: assess(name, established, reasons=reasons) for name in USES}


def gross_alternatives(use: str) -> list[str]:
    """Gross forms that could be released now while `use` waits for deductions."""
    return sorted(u.name for u in USES.values() if u.gross_of == use)
