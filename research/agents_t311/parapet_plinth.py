"""T-311 rules: PARAPETS AND PLINTH as physical elements, every component tied to ONE owner trade (every villa; pure
functions, no drawing input).

Physical element (ERS s.2.1). A PARAPET RUN is the solid that stands on a roof slab edge between the structural slab
top at that edge and the printed parapet top, t thick, L long (its centreline, T-172), plus everything applied to it.
Its components, each its own item in its own unit (ERS s.2.1, s.3):
  concrete (m3: an RC upstand, an RC cap, or the whole solid when the parapet is RC), blockwork (m2 of wall by type,
  only the part that is masonry), formwork (m2 of the cast faces), reinforcement (bar groups of the governing detail),
  exterior plaster on the outer face (m2; part of the facade faces, T-305), plaster on the inner face (m2), the top /
  coping (m2), the roof membrane turn-up on the inner face (m2, UP-WP-UPTURN-015), corners (m.l, T-172).
A PLINTH SEGMENT is the exterior face between the outer finished ground (natural ground, or the top of a paving laid on
it, R-GB-DATUM-1) and the lowest floor's F.F.L. Its substrate is read from the floor datum chain, never assumed:
  the exterior ground-beam outer face (concrete) up to the ground-beam top (= the structural slab top, T-214), then the
  wall course from that top to the F.F.L. The concrete VOLUME stays in the ground-beam line; the plinth adds faces only.

R-T311-1 (material of a parapet run; scope every villa; provenance ERS s.2.2 + ST7757 p.14 / P7757 sections read here):
  the material and build-up come from the detail KEYED to that run. When no detail is keyed to the run and the printed
  alternatives differ (here: the structural typical P1 brick on a 0.30 RC upstand under an RC cap 'as per arc.', the
  RC parapets P2 / P3, and the architectural sections that hatch every parapet like the slab and beams), the split is a
  BOUNDED HELD RANGE over the printed alternatives only: concrete between the smallest concrete part every alternative
  contains (min_rc_m above the slab top) and the whole solid; blockwork between 0 and the solid less that part. The
  solid itself is DRAWING-CONFIRMED above the finished roof level; the part between the finished roof level and the
  structural slab top at the edge is a named HELD increment (t x L per metre of build-up depth, D-39), never a default.
  Never one alternative picked; never 0 for the solid.
R-T311-2 (beam boundary): a scheduled beam depth ends at the slab top (ST p.14 P1 dimension 'AS PER SCH.' to the slab
  top, the 30 upstand dimensioned above it, its own cage). Concrete above the slab top at a roof edge is the PARAPET's
  component, never inside the beam line; booking it in both, or carrying the upstand's height again as blockwork, is a
  DOUBLE refused. (The B20 / B23 stair upstands that a beam section draws as part of the beam stay BEAM: register
  2026-10-22; that is a beam section, not a parapet detail.)
R-T311-3 (plinth substrate): plinth face = concrete part (from max(outer ground, ground-beam soffit) to the ground-beam
  top) + wall course (ground-beam top to F.F.L.), each x the face length; the substrate split needs the ground-beam top
  from the floor's own datum chain (T-214), otherwise the split is HELD while the face area stays measured; a
  ground-beam depth in CONFLICT does not change the face substrate (the beam top is above ground either way) but its
  concrete stays CONFLICT in the ground-beam line. Plaster of the plinth is one finish face (both substrates).
R-T311-4 (one owner per component): every component is booked once, to ONE trade and ONE candidate line or NO_LINE;
  a component in two lines is DOUBLE (refused); a HELD dimension is never 0 and never a default.

Statuses (WORKFLOW_CONTROLS s.5): DRAWING-CONFIRMED, HELD, UNKNOWN, CONFLICT; ledger states IN_LINE / NO_LINE /
OTHER_LINE (owned by an existing line of another family) / DOUBLE (refused).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

EPS = 1e-9
UNITS = {"m": 1.0, "mm": 0.001, "cm": 0.01}
TRADES = ("CONCRETE", "BLOCKWORK", "FORMWORK", "REBAR", "PLASTER_EXT", "PLASTER_PARAPET_INNER", "COPING_TOP",
          "WATERPROOFING", "CORNERS")


class T311Error(ValueError):
    """a booking or a value the ledger refuses (a defaulted height, a double booking, a missing value as 0)."""


@dataclass(frozen=True)
class Rng:
    """a quantity as [lo, hi]; lo == hi is a fixed value. A HELD open increment is named in `held`, never summed."""
    lo: float
    hi: float
    held: str = ""

    def __post_init__(self):
        if self.lo is None or self.hi is None:
            raise T311Error("a range needs both ends (a missing value is HELD with a reason, never None / 0)")
        if self.hi < self.lo - EPS:
            raise T311Error(f"range hi {self.hi} below lo {self.lo}")

    @property
    def fixed(self):
        return abs(self.hi - self.lo) <= EPS

    def __add__(self, o):
        held = "; ".join(x for x in (self.held, o.held) if x)
        return Rng(self.lo + o.lo, self.hi + o.hi, held)


def to_m(value, unit="m"):
    """a printed length in m / cm / mm -> metres; an unknown unit or a missing value is refused (never a default)."""
    if value is None:
        raise T311Error("a missing dimension is HELD, never converted")
    if unit not in UNITS:
        raise T311Error(f"unknown unit {unit!r}")
    return float(value) * UNITS[unit]


def polyline_length(points, closed=False):
    """centreline length of a run from its vertices (any orientation / mirror / order gives the same length)."""
    if len(points) < 2:
        raise T311Error("a run needs two points")
    pts = list(points) + ([points[0]] if closed else [])
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


# ---- parapet run -----------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Alternative:
    """one printed build-up for a parapet: rc_m = concrete height above the slab top (None = the whole solid),
    cap_m = an RC cap height (None with cap_printed False = 'as per arc.', HELD), block = whether masonry exists."""
    name: str
    rc_upstand_m: float | None      # None: the whole solid is RC
    cap_m: float | None = None
    cap_printed: bool = True
    block: bool = False
    source: str = ""


@dataclass(frozen=True)
class ParapetRun:
    chain: str
    side: str
    cl_m: float                      # centreline length (T-172: mean of the outer and inner top arrises)
    t_m: float | None                # thickness (None = HELD)
    h_above_finish_m: float | None   # printed height above the finished roof level (None = HELD)
    h_held: tuple | None = None      # (lo, hi) when the height is HELD with a drawn bound
    keyed: str | None = None         # the alternative name keyed to this run by a callout, or None
    h_datum: str = "finish"          # "finish": height printed above the finished roof (b_edge HELD below it);
                                     # "slab": height printed from the structural slab top (no increment)


def solid_volume(run: ParapetRun) -> Rng:
    """the parapet solid above the FINISHED roof level (DRAWING-CONFIRMED part) in m3; the part below the finished
    level down to the structural slab top is the named HELD increment t x L x b_edge (D-39)."""
    if run.t_m is None:
        raise T311Error(f"{run.chain} {run.side}: thickness HELD -> no solid volume (never a default)")
    held = (f"+ {run.t_m * run.cl_m:.6f} m3 per m of roof build-up depth at the edge (b_edge, D-39 HELD)"
            if run.h_datum == "finish" else "")
    if run.h_above_finish_m is not None:
        v = run.t_m * run.cl_m * run.h_above_finish_m
        return Rng(v, v, held)
    if run.h_held is None:
        raise T311Error(f"{run.chain} {run.side}: height neither printed nor bounded -> HELD, no number")
    lo, hi = run.h_held
    return Rng(run.t_m * run.cl_m * lo, run.t_m * run.cl_m * hi, held)


def material_split(run: ParapetRun, alternatives) -> dict:
    """R-T311-1: concrete m3 and blockwork m2 of one run. Keyed run -> that alternative; unkeyed -> bounded range over
    the printed alternatives. The bounds are on the WHOLE solid from the structural slab top, whose height is
    h_above_finish + b_edge: an RC upstand is dimensioned from the slab top, so it is a valid lower bound whatever
    b_edge is (h_above_finish >= the upstand on every run it is applied to); the fixed parts use h_above_finish and
    the HELD build-up depth b_edge adds t x L per metre to concrete_hi and L per metre to block_hi (named in `held`,
    never summed, never defaulted)."""
    alts = {a.name: a for a in alternatives}
    if not alts:
        raise T311Error("no printed alternative: material UNKNOWN, no split")
    if run.t_m is None:
        raise T311Error(f"{run.chain} {run.side}: thickness HELD")
    h = (run.h_above_finish_m, run.h_above_finish_m) if run.h_above_finish_m is not None else run.h_held
    if h is None:
        raise T311Error(f"{run.chain} {run.side}: height HELD with no bound")
    if run.keyed and run.keyed not in alts:
        raise T311Error(f"keyed alternative {run.keyed!r} not printed")
    use = [alts[run.keyed]] if run.keyed else list(alts.values())
    c_lo, c_hi, b_lo, b_hi = [], [], [], []
    for a in use:
        for hh in h:
            if a.rc_upstand_m is None:               # whole solid RC
                c_lo.append(hh); c_hi.append(hh); b_lo.append(0.0); b_hi.append(0.0)
                continue
            up = min(a.rc_upstand_m, hh)              # upstand measured from the slab top: above-finish part <= it
            if a.cap_printed:
                cap = a.cap_m or 0.0
                rc = min(hh, a.rc_upstand_m + cap)
                c_lo.append(rc); c_hi.append(rc)
                bl = max(0.0, hh - rc) if a.block else 0.0
                b_lo.append(bl); b_hi.append(bl)
            else:                                     # cap 'as per arc.': cap height in [0, h - upstand]
                c_lo.append(up); c_hi.append(hh)
                b_lo.append(0.0); b_hi.append(max(0.0, hh - up) if a.block else 0.0)
    held = ("+ HELD build-up depth b_edge at the edge (D-39): t x L per m to concrete hi, L per m to block hi"
            if run.h_datum == "finish" else "")
    if not (run.keyed and h[0] == h[1] and all(a.cap_printed for a in use)):
        held = "; ".join(x for x in (held, "material / cap not keyed to this run: range over the printed "
                                            "alternatives (designer item)") if x)
    return {
        "concrete_m3": Rng(min(c_lo) * run.t_m * run.cl_m, max(c_hi) * run.t_m * run.cl_m, held),
        "block_m2": Rng(min(b_lo) * run.cl_m, max(b_hi) * run.cl_m, held),
        "alternatives": [a.name for a in use],
    }


def formwork_faces(run: ParapetRun, rc_height: Rng) -> Rng:
    """cast faces of the RC part: both faces x the RC height x L (stop-ends at free ends are their own rows)."""
    return Rng(2 * rc_height.lo * run.cl_m, 2 * rc_height.hi * run.cl_m, rc_height.held)


def refuse_upstand_as_block(block_bottom_above_slab_m, upstand_m):
    """R-T311-2: blockwork measured from the slab top over an RC upstand carries the upstand twice -> refused."""
    if block_bottom_above_slab_m < upstand_m - EPS:
        raise T311Error(f"DOUBLE: blockwork starts {block_bottom_above_slab_m} m above the slab, inside the "
                        f"{upstand_m} m RC upstand")
    return True


def refuse_upstand_in_beam(beam_depth_to_slab_top_m, beam_depth_booked_m):
    """R-T311-2: a beam line deeper than its scheduled depth to the slab top would carry the upstand -> refused."""
    if beam_depth_booked_m > beam_depth_to_slab_top_m + EPS:
        raise T311Error(f"DOUBLE: beam booked {beam_depth_booked_m} m against a scheduled {beam_depth_to_slab_top_m} m "
                        f"to the slab top; concrete above the slab top is the parapet's")
    return True


# ---- plinth segment --------------------------------------------------------------------------------------------------

def plinth_split(length_m, ground_m, ffl_m, gb_top_m=None, gb_soffit_m=None):
    """R-T311-3: (concrete face m2, wall-course m2, total m2) of one plinth segment. gb_top None -> split HELD
    (the total stays measured). A ground-beam soffit above the outer ground leaves a face under the beam that is not
    the beam (refused here: that is a different element, never folded in)."""
    if None in (length_m, ground_m, ffl_m):
        raise T311Error("plinth needs length, outer ground and F.F.L. (missing -> HELD, never 0)")
    if ffl_m < ground_m - EPS:
        raise T311Error("F.F.L. below the outer ground: no plinth face")
    total = length_m * (ffl_m - ground_m)
    if gb_top_m is None:
        return None, None, total
    if gb_top_m > ffl_m + EPS:
        raise T311Error("ground-beam top above the F.F.L.")
    if gb_soffit_m is not None and gb_soffit_m > ground_m + EPS:
        raise T311Error("ground-beam soffit above the outer ground: the face below it is another element")
    conc = length_m * max(0.0, gb_top_m - ground_m)
    course = length_m * (ffl_m - max(gb_top_m, ground_m))
    return conc, course, total


# ---- one owner per component -----------------------------------------------------------------------------------------

@dataclass
class Book:
    """component key -> (trade, line id or NO_LINE). A second line for the same key is a DOUBLE and refused."""
    rows: dict = field(default_factory=dict)

    def put(self, key, trade, line, qty: Rng | None, unit, status, reason=""):
        if trade not in TRADES:
            raise T311Error(f"unknown trade {trade!r}")
        if qty is None and status not in ("HELD", "UNKNOWN", "CONFLICT"):
            raise T311Error(f"{key}: no quantity but status {status} (a missing quantity is HELD, never 0)")
        if qty is not None and status in ("HELD", "UNKNOWN") and qty.fixed and abs(qty.lo) <= EPS:
            raise T311Error(f"{key}: a HELD component booked as 0")
        if key in self.rows:
            old = self.rows[key]
            if old[1] != line or old[0] != trade:
                raise T311Error(f"DOUBLE: {key} already booked to {old[0]} / {old[1]}, now {trade} / {line}")
            raise T311Error(f"{key} booked twice")
        self.rows[key] = (trade, line, qty, unit, status, reason)
        return self.rows[key]
