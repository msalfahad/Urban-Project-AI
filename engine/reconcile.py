"""E30 — Benchmark Reconciler.

An audit layer, and only an audit layer. It compares what the drawing says,
what the site survey says, and what was agreed commercially, and it explains
every difference. It never writes back into E23 or E25, because the moment a
geometry engine starts tuning itself toward a site measurement it stops
reporting what the approved drawing actually contains.

The three truths are kept apart on purpose:

    DESIGN       what the approved drawings say
    SITE         what the qiyal / as-built survey says
    COMMERCIAL   what Urban Projects agreed to charge or pay

A difference between them is information, not an error.

The diagnostic that makes this useful is pairing area with perimeter. For a
rectangle, area and perimeter together determine the sides: they are the roots
of x^2 - (P/2)x + A. Solving that on a site row recovers the dimensions the
surveyor effectively measured, which is how a mis-mapped room is caught — a row
whose implied sides do not resemble any drawn room is not that room. The
inverse is NOT proof: a real room may not be rectangular, and floor and wall
quantities may not even share a measurement basis. So the derived pair is
evidence for challenging a mapping, never grounds for changing geometry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

# Classifications. Only ENGINE_ERROR is the engine's fault and blocks release.
MATCH = "MATCH"
ENGINE_ERROR = "ENGINE_ERROR"
DESIGN_VS_SITE = "DESIGN_VS_SITE"
SCOPE_DIFFERENCE = "SCOPE_DIFFERENCE"
SEMANTIC_MAPPING = "SEMANTIC_MAPPING"
MEASUREMENT_BASIS_DIFFERENCE = "MEASUREMENT_BASIS_DIFFERENCE"
UNRESOLVED = "UNRESOLVED"

CONFIRMED, PROBABLE, AMBIGUOUS = "CONFIRMED", "PROBABLE", "AMBIGUOUS"

# Sanity thresholds. Starting controls, not Urban Projects standards, and the
# data is never tuned to fit them.
PASS_PCT = Decimal("2")
REVIEW_PCT = Decimal("5")


def _sqrt(x: Decimal) -> Decimal:
    return x.sqrt()


def derived_sides(area: Decimal, perimeter: Decimal) -> tuple[Decimal, Decimal] | None:
    """The rectangle sides implied by an area/perimeter pair, if one exists.

    Returns None when no real rectangle has this pair — which is itself a
    finding: the row is not a simple rectangle, or one of the two numbers was
    taken on a different basis from the other.
    """
    half = perimeter / 2
    disc = half * half - 4 * area
    if disc < 0:
        return None
    try:
        r = _sqrt(disc)
    except InvalidOperation:
        return None
    return ((half + r) / 2, (half - r) / 2)


def variance_pct(got: Decimal | None, want: Decimal | None) -> Decimal | None:
    if got is None or want is None or want == 0:
        return None
    return (got - want) / want * 100


def sanity(variance: Decimal | None) -> str:
    """PASS / REVIEW / CHALLENGE on a single variance percentage."""
    if variance is None:
        return UNRESOLVED
    v = abs(variance)
    if v <= PASS_PCT:
        return "PASS"
    if v <= REVIEW_PCT:
        return "REVIEW"
    return "CHALLENGE"


@dataclass
class Quantities:
    """One space's numbers on one basis.

    `basis` is not decoration. Comparing a clear-internal area against a
    printed-dimension area and calling the difference an error is the mistake
    this field exists to prevent.
    """

    area_m2: Decimal | None = None
    perimeter_m: Decimal | None = None
    source: str = ""
    basis: str = "UNKNOWN"
    note: str = ""

    def __post_init__(self) -> None:
        from engine.geometry import check_basis
        check_basis(self.basis)

    def comparable_with(self, other: "Quantities") -> bool:
        """Two quantities on different bases are not directly comparable."""
        return (self.basis == other.basis
                and self.basis != "UNKNOWN")


@dataclass
class Reconciliation:
    """One space compared across the three truths."""

    space_id: str
    design: Quantities = field(default_factory=Quantities)
    site: Quantities = field(default_factory=Quantities)
    commercial: Quantities = field(default_factory=Quantities)
    engine: Quantities = field(default_factory=Quantities)
    mapping_confidence: str = AMBIGUOUS
    classification: str = UNRESOLVED
    explanation: str = ""

    # --- engine vs design is the only pair that can indict the engine
    @property
    def engine_area_variance_pct(self) -> Decimal | None:
        return variance_pct(self.engine.area_m2, self.design.area_m2)

    @property
    def engine_perimeter_variance_pct(self) -> Decimal | None:
        return variance_pct(self.engine.perimeter_m, self.design.perimeter_m)

    @property
    def engine_status(self) -> str:
        """The worse of the two engine-vs-design checks."""
        order = {"PASS": 0, "REVIEW": 1, "CHALLENGE": 2, UNRESOLVED: 3}
        a = sanity(self.engine_area_variance_pct)
        p = sanity(self.engine_perimeter_variance_pct)
        return a if order[a] >= order[p] else p

    # --- design vs site is information, never an engine fault
    @property
    def site_area_variance_pct(self) -> Decimal | None:
        return variance_pct(self.site.area_m2, self.design.area_m2)

    @property
    def site_perimeter_variance_pct(self) -> Decimal | None:
        return variance_pct(self.site.perimeter_m, self.design.perimeter_m)

    @property
    def site_derived_sides(self) -> tuple[Decimal, Decimal] | None:
        if self.site.area_m2 is None or self.site.perimeter_m is None:
            return None
        return derived_sides(self.site.area_m2, self.site.perimeter_m)

    def implied_uniform_offset_m(self) -> Decimal | None:
        """The t that would make (L+t)(W+t) equal the site area.

        If the qiyal measured to wall centrelines or outer faces, one constant t
        should explain every room. Whether it also explains the perimeters is
        the test of that hypothesis — and on this project it does not, which is
        why the hypothesis stays a hypothesis.
        """
        d = self.design
        if d.area_m2 is None or d.perimeter_m is None or self.site.area_m2 is None:
            return None
        sides = derived_sides(d.area_m2, d.perimeter_m)
        if sides is None:
            return None
        L, W = sides
        # t^2 + (L+W)t + LW - site_area = 0
        b = L + W
        c = L * W - self.site.area_m2
        disc = b * b - 4 * c
        if disc < 0:
            return None
        return (-b + _sqrt(disc)) / 2


@dataclass
class BenchmarkReport:
    rows: list[Reconciliation] = field(default_factory=list)

    def total(self, basis: str, field_name: str) -> Decimal:
        out = Decimal(0)
        for r in self.rows:
            v = getattr(getattr(r, basis), field_name)
            if v is not None:
                out += v
        return out

    @property
    def engine_errors(self) -> list[Reconciliation]:
        return [r for r in self.rows if r.classification == ENGINE_ERROR]

    @property
    def unresolved(self) -> list[Reconciliation]:
        return [r for r in self.rows if r.classification == UNRESOLVED]

    @property
    def ready_for_agents(self) -> bool:
        """Design/site differences never block. Engine defects always do."""
        return not self.engine_errors and not self.unresolved
