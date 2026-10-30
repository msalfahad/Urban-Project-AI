"""T-377: cross-trade audit of quantities built on the edge of an ARCHED opening (research module, unwired; every villa).

The physical element (ERS 2026-10-22 s.2.1, s.3): an arched opening is a hole with straight jambs from the sill to the
SPRINGING and a curved head (the developed arch) from springing to crown. Every quantity built on a perimeter, a head or
a jamb of that hole (reveal faces, arrises / corner beads, plaster and paint returns, spatter on reveals, tile edges,
frame perimeters, bed-joint accessories cut at the opening) follows this OUTLINE, never the size-table rectangle
(width x crown, or width x band crown). Proposed rule R-T377-1 (provenance: Checker D-T326-1 2026-10-30 15:35 and its
proposed R-T326-2; T-238 UP-OPEN-ARCH-001 v1.1 A3; T-227 / Checker outline 4.3629 m2):

  R-T377-1  For an opening whose outline record is ARCHED, a quantity of kind
              REVEAL_JAMBS_HEAD (m2)  = d x (2 x springing + developed arch)
              EDGE_JAMBS_HEAD (m)     = 2 x springing + developed arch        (+ width when the sill edge is included)
              HOLE_AREA (m2)          = width x springing + segment
              HOLE_WIDTH_AT(z) (m)    = the chord of the outline at height z (= width at or below the springing)
            is valued on the outline. A value equal to the rectangle (width x crown or x band crown) is REFUSED; a
            value that depends only on the width (sill, threshold, floor-level edge, skirting break) is WIDTH_ONLY and
            accepted; the owner's window-unit measure (Q-32 A enclosing rectangle on the opening line) is a RULE
            rectangle and accepted for the window line only. A rectangular opening keeps the rectangle (normal case).
  R-T377-2  An opening whose outline is HELD (curved on plan and not developed, an arch not drawn or not dimensioned)
            carries every perimeter quantity HELD, blank, never 0 and never a rectangle figure with a non-held status,
            unless a merged ledger has developed that very quantity (named source).

Nothing here names a project, a sheet or a coordinate; every value comes from the caller.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

TOL_REL = 0.005          # 0.5 % (a figure within this of a candidate basis is that basis)
HELD_WORDS = ("HELD", "UNKNOWN", "UNRESOLVED", "BLOCKED", "PENDING")


class AuditError(ValueError):
    pass


@dataclass(frozen=True)
class Outline:
    oid: str
    width: float                  # chord at the springing (m)
    springing: float              # sill (or floor) to springing (m)
    rise: float                   # springing to crown (m)
    segment_m2: float             # area between the springing chord and the arch (m2)
    arch_len: float               # developed arch length (m)
    band: float = 0.0             # surround band outside the opening line (not the hole), m
    status: str = "DRAWING-CONFIRMED"
    profile: tuple = field(default=())   # optional ((x, z) ...) of the arch relative to the left springing point

    def __post_init__(self):
        for k in ("width", "springing", "rise", "segment_m2", "arch_len"):
            v = getattr(self, k)
            if v is None or not isinstance(v, (int, float)) or v < 0:
                raise AuditError(f"{self.oid}: {k} {v!r} is not a measured length")
        if self.width <= 0 or self.springing <= 0:
            raise AuditError(f"{self.oid}: width / springing must be > 0")
        if self.width > 20 or self.springing > 20 or self.rise > 20:
            raise AuditError(f"{self.oid}: dimension above 20 m (millimetres given as metres?)")
        if self.rise == 0:
            if self.segment_m2 != 0 or abs(self.arch_len - self.width) > 1e-9:
                raise AuditError(f"{self.oid}: a rectangular opening has segment 0 and head length = width")
        else:
            if not (self.width < self.arch_len < self.width + 2 * self.rise + 1e-9):
                raise AuditError(f"{self.oid}: arch length {self.arch_len} impossible for chord {self.width} "
                                 f"and rise {self.rise}")
            if not (0 < self.segment_m2 < self.width * self.rise):
                raise AuditError(f"{self.oid}: segment {self.segment_m2} outside (0, width x rise)")

    @property
    def crown(self):
        return self.springing + self.rise

    @property
    def arched(self):
        return self.rise > 0

    # --- outline quantities -------------------------------------------------------------------------------------
    def hole_m2(self):
        return self.width * self.springing + self.segment_m2

    def edge_jambs_head(self):
        return 2 * self.springing + self.arch_len

    def reveal_jambs_head(self, depth):
        _depth(self.oid, depth)
        return depth * self.edge_jambs_head()

    # --- the rectangles a ledger may have used -----------------------------------------------------------------
    def rect_heights(self):
        out = {"RECTANGLE (crown)": self.crown}
        if self.band:
            out["RECTANGLE (band crown)"] = self.crown + self.band
        return out

    def hole_width_at(self, z):
        """chord of the hole at height z above the sill (0 below 0 and above the crown)."""
        if z < 0 or z > self.crown:
            return 0.0
        if z <= self.springing or not self.arched:
            return self.width
        h = z - self.springing
        if self.profile:
            xs = []
            p = self.profile
            for (x1, y1), (x2, y2) in zip(p, p[1:]):
                if (y1 - h) * (y2 - h) <= 0 and y1 != y2:
                    xs.append(x1 + (h - y1) * (x2 - x1) / (y2 - y1))
            if len(xs) < 2:
                raise AuditError(f"{self.oid}: profile does not cross height {z}")
            return max(xs) - min(xs)
        r = circle_radius(self.width, self.rise)       # circular segment (only when no drawn profile is given)
        dc = self.crown - z                             # depth below the crown
        return 2 * math.sqrt(max(0.0, 2 * r * dc - dc * dc))


def _depth(oid, d):
    if d is None:
        raise AuditError(f"{oid}: reveal depth not established: HELD, never 0")
    if not isinstance(d, (int, float)) or d <= 0 or d > 1.0:
        raise AuditError(f"{oid}: reveal depth {d!r} m outside (0, 1.0]")


def circle_radius(chord, rise):
    if chord <= 0 or rise <= 0:
        raise AuditError("circular segment needs chord > 0 and rise > 0")
    return (chord * chord / 4 + rise * rise) / (2 * rise)


def circular_segment(chord, rise):
    """(area, arc length) of a circular segment; used for hand fixtures only."""
    r = circle_radius(chord, rise)
    half = 2 * math.asin(min(1.0, chord / (2 * r)))
    if rise > r:
        half = 2 * math.pi - half
    area = r * r * (half - math.sin(half)) / 2
    return area, r * half


def _near(a, b):
    return b != 0 and abs(a - b) <= TOL_REL * abs(b)


# --- R-T377-1: classify and check a claimed value ---------------------------------------------------------------
KINDS = ("REVEAL_JAMBS_HEAD", "EDGE_JAMBS_HEAD", "EDGE_WITH_SILL", "HOLE_AREA", "HOLE_WIDTH_AT", "WIDTH_ONLY",
         "WINDOW_UNIT_Q32A")


def candidates(o: Outline, kind, depth=None, z=None):
    """{basis: value} of every basis a ledger could have used for this kind of quantity."""
    if kind not in KINDS:
        raise AuditError(f"unknown kind {kind!r}")
    out = {}
    if kind == "REVEAL_JAMBS_HEAD":
        _depth(o.oid, depth)
        out["OUTLINE"] = o.reveal_jambs_head(depth)
        for k, h in o.rect_heights().items():
            out[k] = depth * (2 * h + o.width)
    elif kind in ("EDGE_JAMBS_HEAD", "EDGE_WITH_SILL"):
        add = o.width if kind == "EDGE_WITH_SILL" else 0.0
        out["OUTLINE"] = o.edge_jambs_head() + add
        for k, h in o.rect_heights().items():
            out[k] = 2 * h + o.width + add
    elif kind == "HOLE_AREA":
        out["OUTLINE"] = o.hole_m2()
        for k, h in o.rect_heights().items():
            out[k] = o.width * h
    elif kind == "HOLE_WIDTH_AT":
        if z is None:
            raise AuditError(f"{o.oid}: HOLE_WIDTH_AT needs a height")
        out["OUTLINE"] = o.hole_width_at(z)
        out["RECTANGLE (crown)"] = o.width if 0 <= z <= o.crown else 0.0
    elif kind == "WIDTH_ONLY":
        out["WIDTH_ONLY"] = o.width if depth is None else o.width * depth
    elif kind == "WINDOW_UNIT_Q32A":
        out["RULE RECTANGLE (Q-32 A)"] = o.width * o.crown
    return out


def classify(o: Outline, kind, value, depth=None, z=None):
    """basis the value was built on: OUTLINE / RECTANGLE (...) / WIDTH_ONLY / RULE RECTANGLE / UNMATCHED / HELD."""
    if value is None:
        return "HELD"
    c = candidates(o, kind, depth, z)
    # an arched outline and its rectangle can coincide only when rise = 0 (rectangular opening): outline wins
    for basis in ("OUTLINE", "WIDTH_ONLY", "RULE RECTANGLE (Q-32 A)"):
        if basis in c and _near(value, c[basis]):
            return basis
    for basis, v in c.items():
        if basis.startswith("RECTANGLE") and _near(value, v):
            return basis
    return "UNMATCHED"


def check_value(o: Outline, kind, value, depth=None, z=None):
    """R-T377-1: accept a value on the outline (or WIDTH_ONLY / the Q-32 A window measure), refuse the rectangle."""
    b = classify(o, kind, value, depth, z)
    if b == "HELD":
        raise AuditError(f"{o.oid}: no value given; a held quantity is checked by check_held")
    if o.arched and b.startswith("RECTANGLE") and not _near(candidates(o, kind, depth, z)["OUTLINE"], value):
        raise AuditError(f"{o.oid} {kind}: {value} is the {b} of an arched opening; outline "
                         f"{candidates(o, kind, depth, z)['OUTLINE']:.4f}")
    if b == "UNMATCHED":
        raise AuditError(f"{o.oid} {kind}: {value} matches no basis {candidates(o, kind, depth, z)}")
    return b


# --- R-T377-2: held outlines stay held ---------------------------------------------------------------------------
def check_held(oid, status, value, developed_source=None):
    """an opening whose outline is HELD: a figure is admissible only as HELD / blank, or from a named merged ledger
    that developed that quantity."""
    held = any(w in (status or "").upper() for w in HELD_WORDS)
    if value in (None, ""):
        if not held:
            raise AuditError(f"{oid}: blank value with status {status!r}: a blank is HELD by name")
        return "HELD"
    v = float(value)
    if held:
        if v == 0:
            raise AuditError(f"{oid}: HELD carried as 0")
        return "HELD BOUND"
    if developed_source:
        return "DEVELOPED (" + developed_source + ")"
    raise AuditError(f"{oid}: figure {v} with status {status!r} on a HELD outline and no developed source")
