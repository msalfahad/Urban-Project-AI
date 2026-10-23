"""PLANTED_COLUMN_V1 (T-220, unwired, stdlib only; rollback: delete the folder).

A planted column (legend 'P.C') starts on a beam of the slab below instead of on a column or a neck. This module
turns the drawing evidence of one planted column into one element record, keeping the physical solid, the owner's
manual method and the ownership of every junction apart (ERS s.2-s.3, R-CONC-OWN-1 proposed in T-189, R-SECTION-
CONFLICT-1 proposed in T-217, owner rule URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1 and URBAN-NON-OVERLAPPING-SLAB-
BEAM-MODEL@v1 as applied in the T-119 r2 column ledger).

Physical element (drawing-derived method):
    base  = top of the supporting beam (the beam runs continuous under the column; ST7757.pdf p.15 'BEAM CARRYING
            PLANTED COL. DETAIL' draws exactly this). Never the beam bottom and never the storey level below the beam.
    top   = structural top of the slab above, when every member framing into the column at the top is measured net
            of the column (the column owns the joint, precedence column > beam);
            soffit of the deepest member that is billed THROUGH the column footprint (that member owns the joint).
    solid = A x (top - base)
Owner manual method (column ledger basis): column = A x (interval - D_ctrl), joint = A x (D_ctrl - t), slab part =
A x t, where D_ctrl is the deepest member framing into the column at the top; reported beside the solid, never mixed.

Ownership checks (one owner per intersection, sum of owned = union):
    - the supporting beam line must contain the column footprint (its line is billed through): if its basis excludes
      the footprint the beam line is SHORT by A x D_beam (BEAM_LINE_SHORT: the beam keeps it, it is the element that
      would lose it; the column never starts lower to 'catch' it);
    - a member billed through the column at the top owns the joint: a ledger joint for that column is DOUBLE.

Sections: orientation-free (sorted pair), m / cm / mm; one printed source against a different drawn outline with no
dimension chain is carried as a CONFLICT range (Checker ruling on T-217 PC:77B; lessons row 2026-10-23 'four sources');
the range is never collapsed to an end. Missing evidence -> HELD with the missing item named; a quantity is None, never 0.

Existence of a released storey line: BUILT only on drawing evidence; NOT_DRAWN only when every required sheet was
searched and none draws the member (a consultant item, never a verified 0); otherwise UNKNOWN.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

SCHEMA = "PLANTED_COLUMN_V1"
UNITS = {"m": 1.0, "cm": 0.01, "mm": 0.001}
TOL = 1e-6
THROUGH_MIN = 0.95      # share of the footprint inside a member's billed plan for 'billed through' (rest named)
NET_MAX = 0.01          # share at or below which the member is measured net of the footprint


class Refused(ValueError):
    """A request the rules refuse (the message names the rule)."""


def to_m(v, unit):
    if v is None:
        return None
    if unit not in UNITS:
        raise Refused(f"UNKNOWN_UNIT: {unit!r}")
    return float(v) * UNITS[unit]


# ---------------------------------------------------------------- plan geometry (convex polygons, stdlib only)
def _area(p):
    return 0.5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))


def _ccw(p):
    return p if _area(p) > 0 else list(reversed(p))


def _clip(subject, clipper):
    """Sutherland-Hodgman: intersection of a polygon with a convex polygon (both lists of (x, y))."""
    out = list(subject)
    c = _ccw(clipper)
    for i in range(len(c)):
        a, b = c[i], c[(i + 1) % len(c)]
        inside = lambda q: (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0]) >= -1e-12
        def cut(p, q):
            dx, dy = q[0] - p[0], q[1] - p[1]
            den = (b[0] - a[0]) * dy - (b[1] - a[1]) * dx
            t = ((b[0] - a[0]) * (a[1] - p[1]) - (b[1] - a[1]) * (a[0] - p[0])) / den
            return (p[0] + t * dx, p[1] + t * dy)
        inp, out = out, []
        for j in range(len(inp)):
            p, q = inp[j - 1], inp[j]
            if inside(q):
                if not inside(p):
                    out.append(cut(p, q))
                out.append(q)
            elif inside(p):
                out.append(cut(p, q))
        if not out:
            return []
    return out


def overlap_share(footprint, member_plan):
    """Share of the footprint's area inside a member's billed plan (convex member plan)."""
    a = abs(_area(footprint))
    if a <= 0:
        raise Refused("EMPTY_FOOTPRINT")
    inter = _clip(_ccw(footprint), member_plan)
    return (abs(_area(inter)) if len(inter) >= 3 else 0.0) / a


def billing_basis(footprint, member_plans):
    """'THROUGH' when one billed piece of the member contains the footprint, 'NET' when none overlaps it, else
    'PARTIAL' (undetermined: never guessed)."""
    s = sum(overlap_share(footprint, m) for m in member_plans)
    if s >= THROUGH_MIN:
        return "THROUGH", s
    if s <= NET_MAX:
        return "NET", s
    return "PARTIAL", s


def rect(cx, cy, w, d, angle_deg=0.0, mirror=False):
    """Rectangle corners (for fixtures): centre, width along x, depth along y, rotated, optionally mirrored in x."""
    t = math.radians(angle_deg)
    pts = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        x, y = sx * w / 2, sy * d / 2
        x, y = x * math.cos(t) - y * math.sin(t), x * math.sin(t) + y * math.cos(t)
        pts.append(((-1 if mirror else 1) * (cx + x), cy + y))
    return _ccw(pts)


# ---------------------------------------------------------------- section sources
@dataclass
class Source:
    kind: str          # TEXT | DIM | SCHEDULE | DRAWN
    a: float
    b: float
    unit: str
    ref: str = ""

    def pair(self):
        return tuple(sorted((to_m(self.a, self.unit), to_m(self.b, self.unit))))


def section(sources):
    """Section record from its sources kept apart. Returns status, candidate pairs and the area range (m2)."""
    printed = [s for s in sources if s.kind in ("TEXT", "DIM", "SCHEDULE")]
    drawn = [s for s in sources if s.kind == "DRAWN"]
    if not printed:
        return {"status": "HELD", "why": "NO_PRINTED_SECTION (a drawn outline alone is not a section)",
                "area_lo": None, "area_hi": None, "candidates": []}
    pp = {s.pair() for s in printed}
    dp = {s.pair() for s in drawn}
    same = lambda p, q: abs(p[0] - q[0]) < 1e-6 and abs(p[1] - q[1]) < 1e-6
    pp_u = []
    for p in pp:
        if not any(same(p, q) for q in pp_u):
            pp_u.append(p)
    cands = list(pp_u) + [q for q in dp if not any(same(q, p) for p in pp_u)]
    kinds = {s.kind for s in printed}
    if len(pp_u) > 1:
        status, why = "CONFLICT", "PRINTED_VS_PRINTED"
    elif len(cands) == 1:
        status, why = "AGREE", ""
    elif {"TEXT", "DIM"} <= kinds:
        # the drawing prints the section twice (text + dimension chain): an undimensioned outline is a drafting note
        status, why, cands = "DRAFTING_NOTE", "drawn outline differs from the printed text AND dimensions", pp_u
    else:
        status, why = "CONFLICT", "PRINTED_VS_DRAWN (one printed source, no dimension chain)"
    areas = [p[0] * p[1] for p in cands]
    return {"status": status, "why": why, "candidates": [list(p) for p in cands],
            "area_lo": min(areas), "area_hi": max(areas)}


# ---------------------------------------------------------------- members
@dataclass
class Member:
    id: str
    depth_m: float | None       # None = depth not printed (HELD)
    basis: str                  # THROUGH | NET | PARTIAL | UNKNOWN (how its BOQ line treats the column footprint)
    line_m3_over_footprint: float | None = None   # informational


@dataclass
class PlantedColumn:
    id: str
    storey: str
    sources: list
    support: Member                         # the beam it stands on
    support_top: float | None               # structural top of the supporting beam (m)
    slab_top: float | None                  # structural top of the slab above at the column (m); None = HELD
    slab_top_upper: float | None = None     # physical upper bound when the top is HELD (e.g. the finished level)
    slab_t: float | None = None
    top_members: list = field(default_factory=list)
    interval: float | None = None           # owner-method storey interval (structural top to structural top)
    ledger_joint_m3: float | None = None    # a column ledger's joint for this column (checked for DOUBLE)
    bars: str | None = None                 # printed main bars, e.g. '8 x 16' (count only; links / laps not printed)
    notes: list = field(default_factory=list)


def _mul(a, h):
    return None if a is None or h is None else a * h


def evaluate(pc: PlantedColumn) -> dict:
    sec = section(pc.sources)
    rec = {"schema": SCHEMA, "id": pc.id, "storey": pc.storey, "section": sec, "holds": [], "ownership": [],
           "bars": pc.bars}
    a_lo, a_hi = sec["area_lo"], sec["area_hi"]
    if sec["status"] == "HELD":
        rec["holds"].append("SECTION: " + sec["why"])
    if sec["status"] == "CONFLICT":
        rec["holds"].append("SECTION_CONFLICT: " + sec["why"] + " (range kept, designer)")
    # base: top of the supporting beam
    base = pc.support_top
    if base is None:
        rec["holds"].append("BASE: supporting beam top not established")
    sb = pc.support.basis
    if sb == "NET":
        if pc.support.depth_m is None:
            rec["ownership"].append({"pair": f"{pc.support.id} / {pc.id}", "result": "BEAM_LINE_SHORT",
                                     "beam_short_m3": None, "owner": pc.support.id})
        else:
            rec["ownership"].append({"pair": f"{pc.support.id} / {pc.id}", "result": "BEAM_LINE_SHORT",
                                     "beam_short_m3": [_mul(a_lo, pc.support.depth_m), _mul(a_hi, pc.support.depth_m)],
                                     "owner": pc.support.id,
                                     "note": "the beam keeps the volume under the column (the element that would lose "
                                             "it); the column still starts on the beam top"})
    elif sb == "THROUGH":
        rec["ownership"].append({"pair": f"{pc.support.id} / {pc.id}", "result": "PASS", "owner": pc.support.id})
    else:
        rec["ownership"].append({"pair": f"{pc.support.id} / {pc.id}", "result": "UNDETERMINED", "owner": None})
        rec["holds"].append(f"BASE_OWNERSHIP: {pc.support.id} basis {sb}")
    # top
    through = [m for m in pc.top_members if m.basis == "THROUGH"]
    unknown = [m for m in pc.top_members if m.basis not in ("THROUGH", "NET")]
    if unknown:
        rec["holds"].append("TOP_OWNERSHIP: " + ", ".join(f"{m.id} basis {m.basis}" for m in unknown))
    top_owner = None
    if through:
        if any(m.depth_m is None for m in through):
            top_cut = None
            rec["holds"].append("TOP: depth of a member billed through the column not printed")
        else:
            top_owner = max(through, key=lambda m: m.depth_m)
            top_cut = top_owner.depth_m
    else:
        top_cut = 0.0
    if pc.slab_top is None:
        rec["holds"].append("TOP: structural top of the slab above not printed")
    top = None if (pc.slab_top is None or top_cut is None) else pc.slab_top - top_cut
    h = None if (top is None or base is None) else top - base
    if h is not None and h <= 0:
        raise Refused(f"NON_POSITIVE_HEIGHT {h}")
    h_up = None
    if h is None and pc.slab_top_upper is not None and base is not None and top_cut is not None:
        h_up = pc.slab_top_upper - top_cut - base
    rec["base"] = base
    rec["top"] = top
    rec["top_owner"] = top_owner.id if top_owner else ("column (members framing in are measured net)" if top_cut == 0.0
                                                       and not unknown else None)
    rec["height_m"] = h
    rec["solid_m3"] = None if h is None or a_lo is None else [a_lo * h, a_hi * h]
    rec["solid_upper_bound_m3"] = None if h_up is None or a_hi is None else a_hi * h_up
    for m in through:
        if pc.ledger_joint_m3:
            rec["ownership"].append({"pair": f"{m.id} / {pc.id}", "result": "DOUBLE",
                                     "double_m3": pc.ledger_joint_m3, "owner": m.id,
                                     "note": "member billed through the column footprint and a ledger joint for the "
                                             "same volume"})
        else:
            rec["ownership"].append({"pair": f"{m.id} / {pc.id}", "result": "PASS", "owner": m.id})
    for m in pc.top_members:
        if m.basis == "NET":
            rec["ownership"].append({"pair": f"{m.id} / {pc.id}", "result": "PASS", "owner": pc.id})
    # owner manual method (column to the controlling member + joint + slab part)
    om = {"rule": "URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1 + URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1"}
    depths = [m.depth_m for m in pc.top_members]
    if pc.interval is None or a_lo is None:
        om["status"] = "HELD"
        om["why"] = "interval not established" if pc.interval is None else "no printed section"
    elif not depths or any(d is None for d in depths):
        known = [d for d in depths if d is not None]
        om["status"] = "HELD"
        om["why"] = "depth of a framing member not printed: column is an UPPER bound, joint a LOWER bound"
        if known and a_hi is not None:
            om["column_m3_upper"] = a_hi * (pc.interval - max(known))
    else:
        d = max(depths)
        t = pc.slab_t
        om["status"] = "CALCULATED" if sec["status"] in ("AGREE", "DRAFTING_NOTE") else "HELD"
        om["D_ctrl"] = d
        om["column_m3"] = [a_lo * (pc.interval - d), a_hi * (pc.interval - d)]
        if through:
            om["joint_m3"] = [0.0, 0.0]
            om["note"] = "joint owned by the member billed through the column (R-CONC-OWN-1)"
        elif t is not None:
            om["joint_m3"] = [a_lo * (d - t), a_hi * (d - t)]
            om["slab_part_m3"] = [a_lo * t, a_hi * t]
        if pc.slab_top is None:
            om["status"] = "HELD"
            om["why"] = ("structural top above not established: the interval is the finished-level convention, the "
                         "column inherits the held datum")
    rec["owner_method"] = om
    rec["status"] = ("HELD" if rec["holds"] or any(o["result"] in ("DOUBLE", "UNDETERMINED") for o in rec["ownership"])
                     else "DRAWING-CONFIRMED")
    rec["release"] = "NOT RELEASED"
    return rec


def single_value(rec, which="solid_m3"):
    """The one quantity a line may carry: only when nothing is held and the range is one value. Never an end."""
    v = rec.get(which)
    if v is None:
        raise Refused(f"HELD: {which} has no value ({'; '.join(rec['holds']) or 'missing'}); never 0")
    if abs(v[0] - v[1]) > TOL:
        raise Refused(f"RANGE_NOT_COLLAPSED: {which} {v[0]:.4f} .. {v[1]:.4f} (never the larger or the smaller end)")
    if rec["status"] != "DRAWING-CONFIRMED":
        raise Refused(f"NOT_CONFIRMED: status {rec['status']}")
    return v[0]


def check_claim(rec, claimed_m3, tol=1e-4):
    """Refuse the known wrong readings of a planted column volume."""
    sol = rec["solid_m3"]
    if sol is not None and claimed_m3 > sol[1] + tol:
        raise Refused(f"ABOVE_PHYSICAL: {claimed_m3:.4f} > solid {sol[1]:.4f} (column through the supporting beam or "
                      "the larger section end)")
    if sol is not None and abs(sol[0] - sol[1]) > TOL and abs(claimed_m3 - sol[1]) <= tol:
        raise Refused("LARGER_END: the section range was collapsed to its larger end")
    if sol is None and claimed_m3 == 0:
        raise Refused("MISSING_AS_ZERO")
    return True


# ---------------------------------------------------------------- existence of a released storey line
def classify_existence(drawn_on: list, searched: list, required: list) -> dict:
    """drawn_on: sheets that draw the member at the position; searched: sheets read at the position (format named);
    required: sheets that must be read before an absence counts."""
    if drawn_on:
        return {"class": "BUILT", "evidence": drawn_on}
    missing = [s for s in required if s not in searched]
    if missing:
        return {"class": "UNKNOWN", "unsearched": missing}
    return {"class": "NOT_DRAWN", "searched": searched,
            "note": "consultant item; the released line is a carried convention; never a verified 0"}


def released_line_state(line_m3, existence):
    """What a released line becomes: BUILT keeps its value; NOT_DRAWN / UNKNOWN keep no value (None) and a status."""
    c = existence["class"]
    if c == "BUILT":
        return {"m3": line_m3, "status": "BUILT"}
    return {"m3": None, "status": c, "released_was": line_m3}


def keep_as_built(existence):
    if existence["class"] != "BUILT":
        raise Refused(f"CONVENTION_AS_BUILT: a line is kept as built only on drawing evidence ({existence['class']})")
    return True
