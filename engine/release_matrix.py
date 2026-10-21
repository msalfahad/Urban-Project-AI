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
# Is this polygon the WHOLE of that space, and ONLY that space? Region identity
# and physical topology are different questions and the workbook proved it:
# WSH-01's region is the shaft beside the washroom (identity fails), while
# BED-04's region is a real bedroom with an unseparated bathroom inside it
# (identity holds, topology fails). Both must block a quantity ATTRIBUTED TO A
# PHYSICAL SPACE, and neither may block a raw region observation.
PHYSICAL_TOPOLOGY = "physical_topology"
CLOSED_BOUNDARY = "closed_boundary"          # does the outline close?
PHYSICAL_WALL_SPLIT = "physical_wall_split"  # masonry vs doorway closure known?
EXTERNAL_SPLIT = "external_split"            # internal vs external established?
OPENINGS = "openings"                        # openings identified and typed?
WALL_THICKNESS = "wall_thickness"            # proven, not assumed
FLOOR_AREA = "floor_area"
# A ceiling is not a floor seen from below. A void, a shaft, a double-height
# room, a drop or a bulkhead all break the equality, and the audit that found
# this had CEILING reporting READY on 15 spaces while ceiling_height was
# HEIGHT_REQUIRED and no ceiling geometry existed at all. Nothing in the engine
# had ever established ceiling area; the use was simply reading floor area.
CEILING_GEOMETRY = "ceiling_geometry"
HEIGHT = "height"                            # a releasable height for this trade
TRADE_RULE = "trade_rule"                    # a rule covering this space type
OPENING_RULE = "opening_rule"                # how THIS trade deducts openings
SCOPE = "scope"                              # the space is in the job
# Which stretches of boundary carry skirting at all. SKIRTING_ELIGIBLE_LENGTH
# is RULE_REQUIRED in the length ontology and nothing derives it: a door
# threshold, a fitted wardrobe, a kitchen run and a ceramic dado may each
# remove skirting, and only a signed project rule says which. Until one
# exists the length is NOT_ESTABLISHED — which is not zero and not the
# material length.
SKIRTING_ELIGIBILITY_RULE = "skirting_eligibility_rule"

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
    Use("GROSS_PERIMETER", (SCOPE, REGION_IDENTITY, PHYSICAL_TOPOLOGY,
                            CLOSED_BOUNDARY),
        "the closed outline of a space, open transitions included"),

    Use("GROSS_WALL_AREA", (SCOPE, REGION_IDENTITY, PHYSICAL_TOPOLOGY,
                            CLOSED_BOUNDARY, HEIGHT),
        "applicable wall length x a trade height, before any deduction"),

    Use("SKIRTING", (SCOPE, REGION_IDENTITY, PHYSICAL_TOPOLOGY,
                     CLOSED_BOUNDARY, SKIRTING_ELIGIBILITY_RULE, OPENINGS,
                     TRADE_RULE, OPENING_RULE),
        "linear metres along the SKIRTING-ELIGIBLE boundary, never derived "
        "from floor area and never from the space boundary: the eligible "
        "length needs a signed rule before it exists at all"),

    Use("GROSS_CERAMIC_WALL", (SCOPE, REGION_IDENTITY, PHYSICAL_TOPOLOGY,
                               CLOSED_BOUNDARY, HEIGHT, TRADE_RULE),
        "wet-room wall area before opening deductions",
        gross_of="NET_CERAMIC_WALL"),

    Use("NET_CERAMIC_WALL", (SCOPE, REGION_IDENTITY, PHYSICAL_TOPOLOGY,
                             CLOSED_BOUNDARY, HEIGHT, TRADE_RULE, OPENINGS,
                             OPENING_RULE),
        "ceramic wall area after this trade's opening rule"),

    Use("GROSS_PLASTER", (SCOPE, REGION_IDENTITY, PHYSICAL_TOPOLOGY,
                          CLOSED_BOUNDARY, HEIGHT, TRADE_RULE),
        "plaster area before deductions", gross_of="NET_PLASTER"),

    Use("NET_PLASTER", (SCOPE, REGION_IDENTITY, PHYSICAL_TOPOLOGY,
                        CLOSED_BOUNDARY, HEIGHT, TRADE_RULE, OPENINGS,
                        OPENING_RULE),
        "plaster area after this trade's opening rule"),

    Use("PAINT", (SCOPE, REGION_IDENTITY, PHYSICAL_TOPOLOGY, CLOSED_BOUNDARY,
                  HEIGHT, TRADE_RULE, OPENINGS, OPENING_RULE),
        "computed independently of plaster: ceramic, stone or cladding may "
        "cover surfaces plaster covered"),

    Use("BLOCKWORK", (SCOPE, REGION_IDENTITY, PHYSICAL_TOPOLOGY,
                      CLOSED_BOUNDARY, PHYSICAL_WALL_SPLIT, EXTERNAL_SPLIT,
                      HEIGHT, OPENINGS, OPENING_RULE, WALL_THICKNESS),
        "masonry only: a doorway closure is not a wall, and thickness decides "
        "the block type"),

    Use("EXTERNAL_FINISH", (SCOPE, REGION_IDENTITY, PHYSICAL_TOPOLOGY,
                            CLOSED_BOUNDARY, EXTERNAL_SPLIT, HEIGHT,
                            TRADE_RULE),
        "anything priced differently outside than in"),

    Use("WATERPROOFING_HORIZONTAL", (SCOPE, REGION_IDENTITY,
                                     PHYSICAL_TOPOLOGY, FLOOR_AREA,
                                     TRADE_RULE),
        "wet floors, terraces, roofs — an area, not a wall run"),

    Use("WATERPROOFING_VERTICAL", (SCOPE, REGION_IDENTITY, PHYSICAL_TOPOLOGY,
                                   CLOSED_BOUNDARY, HEIGHT, TRADE_RULE),
        "upstand height x applicable boundary, from the project specification"),

    Use("CEILING", (SCOPE, REGION_IDENTITY, PHYSICAL_TOPOLOGY,
                    CEILING_GEOMETRY, TRADE_RULE),
        "requires an established ceiling geometry source. Floor area is NOT a "
        "substitute: a void, shaft, double-height room, drop or bulkhead breaks "
        "the equality, and nothing may assume it silently"),
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


# ---------------------------------------------------------------------------
# Per space, per use.
#
# A project-level "GROSS_CERAMIC_WALL: READY" is too coarse to be true. On
# project 23010 the region labelled WSH-01 is not the washroom, BED-04 is still
# merged with a bathroom, and 31 of 36 spaces are BOUNDED_ERROR on external
# classification. Reporting one verdict for the villa means either one defect
# blocks every room, or the defect disappears into an average. Neither is the
# answer: the defect should block exactly the rooms it affects.
#
# So readiness is a fact about a (space, use) pair, and the project figure is a
# count of those pairs rather than a judgement of its own.

NOT_APPLICABLE = "NOT_APPLICABLE"

# Which missing dependency to name when several are missing. A caller wants the
# headline, and "region identity" is a more useful headline than "opening rule"
# when both are absent — you cannot meaningfully discuss a trade rule for a
# polygon that is not the room you think it is.
_BLOCKER_PRIORITY = (
    REGION_IDENTITY, PHYSICAL_TOPOLOGY, SCOPE, CLOSED_BOUNDARY, PHYSICAL_WALL_SPLIT, EXTERNAL_SPLIT,
    FLOOR_AREA, CEILING_GEOMETRY, WALL_THICKNESS,
    # Ahead of OPENINGS on purpose. The workbook reported skirting as blocked
    # on "openings", which reads as "find the doors and skirting is ready".
    # It is not: without the eligibility rule there is no skirting length to
    # deduct a door from.
    SKIRTING_ELIGIBILITY_RULE, OPENINGS, HEIGHT, TRADE_RULE,
    OPENING_RULE,
)


@dataclass
class SpaceUseStatus:
    """One (space, use) verdict, with the invariant that makes it readable.

    THE WORKBOOK CAUGHT THIS: rows read `release_status = READY` beside
    `primary_blocker = trade_rule`. Both cannot be true. A reader who sees a
    blocker on a READY row does not know which half to believe, and the safe
    half is the one that stops them using the number — so the contradiction
    quietly destroys the value of every READY row on the sheet.

    The three states now each have a required shape, checked on construction:

        READY           no missing dependency, and no blocker
        BLOCKED_*       at least one missing dependency
        NOT_APPLICABLE  a stated reason for not applying

    `not_applicable_reason` is required because "this trade does not apply
    here" and "nobody looked" are different facts and N/A was being used for
    both.
    """

    space_id: str
    use: str
    status: str
    missing: list[str] = field(default_factory=list)
    reasons: dict[str, str] = field(default_factory=dict)
    not_applicable_reason: str = ""

    def __post_init__(self):
        if self.status == READY and self.missing:
            raise ReleaseMatrixError(
                f"{self.space_id}/{self.use}: READY with {self.missing} still "
                "missing. A row that is ready and blocked at the same time "
                "makes every other ready row unreadable")
        if self.status.startswith(BLOCKED) and not self.missing:
            raise ReleaseMatrixError(
                f"{self.space_id}/{self.use}: {self.status} with nothing "
                "missing. A block that cannot name its cause cannot be cleared")
        if self.status == NOT_APPLICABLE and not self.not_applicable_reason:
            raise ReleaseMatrixError(
                f"{self.space_id}/{self.use}: NOT_APPLICABLE with no reason. "
                "\"this trade does not apply here\" and \"nobody looked\" are "
                "different facts and N/A must say which one it is")

    @property
    def ready(self) -> bool:
        return self.status == READY

    @property
    def applicable(self) -> bool:
        return self.status != NOT_APPLICABLE

    @property
    def primary_blocker(self) -> str:
        """The headline blocker, or "" when there is nothing blocking.

        A READY row returns "" because it has no missing dependency — the
        invariant above guarantees it, rather than this property hoping so.
        """
        for dep in _BLOCKER_PRIORITY:
            if dep in self.missing:
                return dep
        return self.missing[0] if self.missing else ""

    def explain(self) -> str:
        if self.ready:
            return f"{self.space_id} / {self.use}: READY"
        if not self.applicable:
            return f"{self.space_id} / {self.use}: {NOT_APPLICABLE}"
        blocker = self.primary_blocker
        why = self.reasons.get(blocker, "not established")
        extra = (f" (+{len(self.missing) - 1} more)" if len(self.missing) > 1 else "")
        return f"{self.space_id} / {self.use}: {self.status} — {why}{extra}"


def assess_space(space_id: str, use: str, established: dict[str, bool], *,
                 reasons: dict[str, str] | None = None,
                 applicable: bool = True,
                 not_applicable_reason: str = "") -> SpaceUseStatus:
    """Readiness of one quantity for one space.

    `applicable=False` is not a block. A bedroom has no ceramic wall on this
    project, and a space outside the contract is not a space whose geometry is
    broken — reporting either as BLOCKED puts it in a queue of work to do, and
    there is no work to do. They are different facts and they are counted
    separately.

    A reason is required with `applicable=False`, because N/A was being used
    both for "the trade does not apply" and for "we are not measuring this",
    and a reader cannot tell those apart from the word alone.
    """
    if use not in USES:
        raise ReleaseMatrixError(
            f"unknown use {use!r}. Known: {sorted(USES)}. A quantity whose "
            "dependencies nobody has written down cannot be released.")
    if not applicable:
        return SpaceUseStatus(
            space_id, use, NOT_APPLICABLE,
            not_applicable_reason=not_applicable_reason
            or "not applicable on this project, reason not stated")
    base = assess(use, established, reasons=reasons)
    if base.ready:
        return SpaceUseStatus(space_id, use, READY, [], base.reasons)
    status = f"BLOCKED_{SpaceUseStatus(space_id, use, NOT_READY, base.missing).primary_blocker.upper()}"
    return SpaceUseStatus(space_id, use, status, base.missing, base.reasons)


@dataclass
class UseTally:
    use: str
    ready: int = 0
    blocked: int = 0
    not_applicable: int = 0
    blocked_spaces: dict[str, str] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return self.ready + self.blocked + self.not_applicable

    def row(self) -> dict:
        return {"use": self.use, "ready": self.ready, "blocked": self.blocked,
                "not_applicable": self.not_applicable, "total": self.total,
                "blocked_spaces": dict(self.blocked_spaces)}


def project_matrix(per_space: dict[str, dict[str, bool]], *,
                   reasons: dict[str, dict[str, str]] | None = None,
                   applicable: dict[str, set[str]] | None = None,
                   uses: "tuple[str, ...] | None" = None,
                   ) -> dict[str, UseTally]:
    """Aggregate every (space, use) pair into per-use counts.

    `per_space` maps space id -> the dependencies established for it.
    `applicable` maps space id -> the set of uses that apply to that space; a
    space absent from it is treated as applicable for everything, because
    guessing that a trade does not apply is the same kind of error as guessing
    that it does.
    """
    reasons = reasons or {}
    names = uses or tuple(USES)
    out = {u: UseTally(u) for u in names}
    for space_id, established in sorted(per_space.items()):
        allowed = applicable.get(space_id) if applicable else None
        for use in names:
            st = assess_space(space_id, use, established,
                              reasons=reasons.get(space_id),
                              applicable=(allowed is None or use in allowed))
            tally = out[use]
            if st.ready:
                tally.ready += 1
            elif not st.applicable:
                tally.not_applicable += 1
            else:
                tally.blocked += 1
                tally.blocked_spaces[space_id] = st.status
    return out


def render_matrix(tallies: dict[str, UseTally]) -> str:
    """The counts table, worst coverage first."""
    lines = [f"{'USE':26} {'READY':>6} {'BLOCKED':>8} {'N/A':>5} {'TOTAL':>6}"]
    for t in sorted(tallies.values(), key=lambda t: (-t.ready, t.use)):
        lines.append(f"{t.use:26} {t.ready:6d} {t.blocked:8d} "
                     f"{t.not_applicable:5d} {t.total:6d}")
    return "\n".join(lines)
