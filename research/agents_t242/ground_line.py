"""T-242 GROUND_LINE_V1 (research, unwired, stdlib only): the CONC.GROUND line closed run by run.

Physical elements (structural set ST7757 p.13 "Ground Beams" sections, p.14 "TYPICAL BOUNDARY WALL", p.3 ground-beams
plan; merged records T-141 spans, T-205 necks, T-214 / T-221 structural tops, T-230 ends):

- GROUND BEAM (tie beam) RUN: the solid b x D x L of one beam between the faces of the members it physically meets
  in 3-D (neck / column, the lift pit ring, another ground beam); top = the GF structural slab top it carries.
  * INTERIOR run: the p.13 typical sections by span length: more than 5 m 0.30 x 0.60, less than 5 m 0.30 x 0.40,
    less than 2.5 m 0.30 x 0.30 (the first two printed "without concentrated load").
  * EXTERIOR run (slab on one side, outside ground on the other): p.13 "for exterior walls", 0.30 wide, depth
    "FOLLOW ARCH." from "Ground Floor slab level" (top) to "Outer Normal ground level" (underside): D = top - ground.
  * COURT run: outside ground on both sides (no slab): no printed section applies.
- CURVED run: the same, its plan area between the two drawn arcs net of the supports and straight bands.
- BOUNDARY-WALL GROUND BEAM at natural ground (p.14: "GROUND BEAM (20x40)", section A-A dimension 40, top at N.G.):
  plan band x 0.40; the boundary columns inside it (20 x 30, "SEE ARCH PLAN") are not drawn on any plan.
- GROUND SLAB: a keyed component of the same reference line (STR.CONC.GROUND_SLAB), measured elsewhere.

Rules applied: R-CONC-OWN-1 (the member billed through a junction owns it; one owner per piece), the T-230 end rule (a
run ends only at a member it meets in 3-D; a footing outline below the soffit is never an end), Q-74 (axis length),
the T-205 lesson (a design limit is never a member length), UP-QTY-STATUS-001 (released / held / unsupported; missing
never 0), the no-assumptions rule (no default depth: an unprinted depth stays HELD as the range the printed datums
give, or with no value when they give none).

Statuses: CALCULATED (every input printed, one reading), HELD (a named open item; a range, or no value), CONFLICT (two
printed sources disagree; a range, never one end). Every function returns plain dicts; nothing becomes 0 silently.
"""
from __future__ import annotations

POLICY_ID = "GROUND_LINE_V1"
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"   # research module: no released or candidate method imports it

CALCULATED = "CALCULATED"
HELD = "HELD"
CONFLICT = "CONFLICT"

EXTERIOR = "EXTERIOR"
INTERIOR = "INTERIOR"
COURT = "COURT"
CANDIDATES = "CANDIDATES"

# p.13 typical sections (title -> depth m); the titles name length classes, see `title_depths`
P13_DEPTH = {"P13-GB-GT5M": 0.60, "P13-GB-LT5M": 0.40, "P13-GB-LT2_5M": 0.30}
P13_WIDTH = 0.30
MIN_TYPICAL_DEPTH = min(P13_DEPTH.values())

OUTSIDE_LEVELS = {"+0.15", "BEYOND"}          # the court level printed on the sheet, or beyond the plot line
INSIDE_LEVELS = {"+1.00", "+0.30"}            # finished floor levels of the two building parts


class GroundLineError(ValueError):
    pass


def _num(v, name, lo=None):
    if v is None:
        raise GroundLineError(f"{name} missing (never 0)")
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise GroundLineError(f"{name} must be a number in metres")
    if lo is not None and v <= lo:
        raise GroundLineError(f"{name} must be > {lo}")
    return float(v)


def metres(v, unit):
    """Lengths enter in m; cm / mm are converted explicitly (a unit is never guessed)."""
    k = {"m": 1.0, "cm": 0.01, "mm": 0.001}.get(unit)
    if k is None:
        raise GroundLineError(f"unknown unit {unit!r}")
    return _num(v, "length") * k


# ------------------------------------------------------------------------------------------- 1. exterior / interior
def side_reading(levels):
    """One side of a beam from its probe levels: OUT (court or beyond the plot), IN (a floor level), UNK (no mark)."""
    s = set(levels)
    if s & OUTSIDE_LEVELS:
        return "OUT"
    if any(any(m in x.split("/") for m in INSIDE_LEVELS) for x in s):
        return "IN"
    return "UNK"


def s1_reading(side_a, side_b):
    """S1, the structural sheet's own level marks on both sides: EXTERIOR(strong / weak), INTERIOR, COURT, UNKNOWN."""
    a, b = side_reading(side_a), side_reading(side_b)
    if a == "OUT" and b == "OUT":
        return COURT, "both sides outside"
    if "OUT" in (a, b):
        other = b if a == "OUT" else a
        return EXTERIOR, ("strong" if other == "IN" else "weak")
    if a == "IN" and b == "IN":
        return INTERIOR, "both sides inside"
    return "UNKNOWN", f"{a}/{b}"


def classify(s1, s1_strength, s2, s3):
    """Combine three independent readings into EXTERIOR / INTERIOR / COURT / CANDIDATES.

    s1: EXTERIOR / INTERIOR / COURT / UNKNOWN (level marks of the structural sheet, the printed evidence);
    s2: EXTERIOR / INTERIOR / NOWALL (the architectural GF wall on the beam and whether one side is EXTERIOR);
    s3: EXT / EXT_OR_INT / INT / UNKNOWN (the pre-S5 register's two geometric outline tests, T-138 record).
    A reading the printed levels contradict never wins; one source alone never classifies an exterior beam.
    """
    if s1 == COURT:
        return COURT, "S1: outside ground on both sides"
    if s1 == EXTERIOR and s1_strength == "strong" and (s2 == EXTERIOR or s3 in ("EXT", "EXT_OR_INT")):
        return EXTERIOR, "S1 strong + S2/S3"
    if s1 == EXTERIOR and (s2 == EXTERIOR or s3 == "EXT"):
        return EXTERIOR, "S1 weak + S2/S3 exterior"
    if s1 == "UNKNOWN" and s2 == EXTERIOR and s3 in ("EXT", "EXT_OR_INT"):
        return EXTERIOR, "S2 + S3"
    if s1 in (INTERIOR, "UNKNOWN") and (s2 == INTERIOR and s3 in ("INT", "UNKNOWN")
                                        or s2 == "NOWALL" and s3 == "INT"):
        return INTERIOR, "no outside side; S2/S3 interior"
    return CANDIDATES, f"S1 {s1} ({s1_strength}), S2 {s2}, S3 {s3}"


# ------------------------------------------------------------------------------------------------ 2. depths
def title_depths(classes):
    """Depths of the p.13 titles that hold for a span (every title that holds on any length basis)."""
    out = set()
    for c in classes:
        if c not in P13_DEPTH:
            raise GroundLineError(f"unknown p.13 title {c!r}")
        out.add(P13_DEPTH[c])
    if not out:
        raise GroundLineError("no p.13 title holds (never a default depth)")
    return sorted(out)


def exterior_depth(tops, grounds):
    """'FOLLOW ARCH.': D = top - ground for every printed top (GF structural slab top) and ground candidate.

    Returns (lo, hi, flags). Refuses an empty top or ground list (an exterior depth is never defaulted) and a ground
    at or above the top. Flags BELOW_TYPICAL when the literal reading gives a member shallower than the shallowest
    printed ground-beam section (the drawn exterior section holds three bar layers; S5 ANNEX_DEPTH_SOURCE_CONFLICT)."""
    if not tops or not grounds:
        raise GroundLineError("exterior depth needs the printed slab top and the outer ground level (D-35): "
                              "no default depth")
    ds = []
    for t in tops:
        for g in grounds:
            t_, g_ = _num(t, "slab top"), _num(g, "outer ground")
            if t_ - g_ <= 0:
                raise GroundLineError(f"outer ground {g_} not below the slab top {t_}")
            ds.append(round(t_ - g_, 6))
    lo, hi = min(ds), max(ds)
    flags = ["BELOW_TYPICAL"] if lo < MIN_TYPICAL_DEPTH - 1e-9 else []
    return lo, hi, flags


# ------------------------------------------------------------------------------------------------- 3. one run
def run_volume(run_id, kind, b, L, depths=None, ext=None, d33=False, plan_m2=None, end_adjust_m2=(0.0, 0.0),
               conflict=False, note=""):
    """Volume of one run (m3). kind INTERIOR / EXTERIOR / COURT / CANDIDATES.

    depths: interior candidate depths (title_depths); ext: (lo, hi, flags) from exterior_depth; plan_m2 replaces
    b x L for a curved run; end_adjust_m2: (lo, hi) plan area added (+) or removed (-) at its ends (neck GAP / DOUBLE,
    a corner piece). Status: CALCULATED only for an interior run with one depth and no D-33 tee."""
    b_ = _num(b, "width", 0.0)
    area = _num(plan_m2, "plan area", 0.0) if plan_m2 is not None else b_ * _num(L, "length", 0.0)
    a_lo, a_hi = area + end_adjust_m2[0], area + end_adjust_m2[1]
    reasons = []
    if kind == INTERIOR:
        ds = sorted(depths or [])
        if not ds:
            raise GroundLineError(f"{run_id}: interior run without a p.13 title")
        if len(ds) > 1:
            reasons.append("D-34 title / length basis: " + " / ".join(f"{d:.2f}" for d in ds))
        if d33:
            reasons.append("D-33 a beam ends on it mid-span: printed sections are 'without concentrated load'")
        lo, hi = a_lo * ds[0], a_hi * ds[-1]
    elif kind == EXTERIOR:
        if ext is None:
            raise GroundLineError(f"{run_id}: exterior run without its D-35 depth range (never a default)")
        lo_d, hi_d, flags = ext
        reasons.append(f"D-35 FOLLOW ARCH. {lo_d:.2f} .. {hi_d:.2f}")
        if "BELOW_TYPICAL" in flags:
            conflict = True
            reasons.append("the literal reading is shallower than every printed section (source conflict)")
        lo, hi = a_lo * lo_d, a_hi * hi_d
    elif kind in (COURT, CANDIDATES):
        ds = sorted(depths or [])
        if not ds:
            return {"run_id": run_id, "status": HELD, "low_m3": None, "high_m3": None, "value_m3": None,
                    "reasons": [f"{kind}: no printed section applies; no value"], "note": note}
        reasons.append(f"{kind}: section not established, candidates " + " / ".join(f"{d:.2f}" for d in ds))
        lo, hi = a_lo * ds[0], a_hi * ds[-1]
    else:
        raise GroundLineError(f"unknown run kind {kind!r}")
    if not reasons and abs(end_adjust_m2[1] - end_adjust_m2[0]) > 1e-12:
        conflict = True
        reasons.append(f"end piece {end_adjust_m2[0]:+.4f} .. {end_adjust_m2[1]:+.4f} m2 depends on a printed "
                       "section conflict at the neck")
    status = CONFLICT if conflict else (HELD if reasons else CALCULATED)
    value = round(lo, 6) if status == CALCULATED else None
    return {"run_id": run_id, "status": status, "low_m3": round(lo, 6), "high_m3": round(hi, 6),
            "value_m3": value, "reasons": reasons, "note": note}


# ------------------------------------------------------------------------------------------------- 4. checks
def end_support(kind, vertical_gap_m=None):
    """A run ends only at a member it meets in 3-D. A footing / outline at another level is refused."""
    if kind in ("COLUMN", "NECK", "WALL", "BEAM", "BEAM_JUNCTION", "RING"):
        return True
    if kind in ("FOOTING", "FOOTING_FACE", "OUTLINE"):
        raise GroundLineError(f"{kind} is not a ground-beam end (no 3-D contact; T-230)"
                              + (f": vertical gap {vertical_gap_m:.2f} m" if vertical_gap_m is not None else ""))
    raise GroundLineError(f"unknown end kind {kind!r}")


def intersections_once(pieces):
    """pieces: [(piece_id, owner_line)]; a physical piece billed by two lines is refused (R-CONC-OWN-1)."""
    seen = {}
    for pid, owner in pieces:
        if pid in seen and seen[pid] != owner:
            raise GroundLineError(f"piece {pid} billed twice: {seen[pid]} and {owner}")
        if pid in seen:
            raise GroundLineError(f"piece {pid} listed twice in {owner}")
        seen[pid] = owner
    return True


def component_total(runs):
    """Sum the runs of one component, the CALCULATED part apart from the HELD / CONFLICT ranges (never one end)."""
    ids = [r["run_id"] for r in runs]
    if len(set(ids)) != len(ids):
        raise GroundLineError("a run entered twice")
    calc = sum(r["value_m3"] for r in runs if r["status"] == CALCULATED)
    held = [r for r in runs if r["status"] != CALCULATED]
    for r in held:
        if r["value_m3"] is not None:
            raise GroundLineError(f"{r['run_id']}: a held run carries a single value")
        if r["low_m3"] == 0 and r["high_m3"] == 0:
            raise GroundLineError(f"{r['run_id']}: held shown as 0")
    lo = sum(r["low_m3"] for r in held if r["low_m3"] is not None)
    hi = sum(r["high_m3"] for r in held if r["high_m3"] is not None)
    novalue = [r["run_id"] for r in held if r["low_m3"] is None]
    return {"runs": len(runs), "calculated_m3": round(calc, 6), "calculated_runs": len(runs) - len(held),
            "held_runs": len(held), "held_low_m3": round(lo, 6), "held_high_m3": round(hi, 6),
            "held_no_value": novalue, "conflict_runs": sum(1 for r in held if r["status"] == CONFLICT)}


def line_closable(components):
    """A keyed line is closable only when every keyed component is measured with no held part (T-233 lesson)."""
    why = []
    for name, c in components.items():
        if c.get("status") == "NOT_MEASURED":
            why.append(f"{name}: not measured here")
        elif c.get("held_runs", 0) or c.get("held_no_value"):
            why.append(f"{name}: {c.get('held_runs', 0)} held runs")
    return (not why), why


def policy_record():
    return {"policy": POLICY_ID, "guard": DEFAULT_GUARD_CLASS, "p13_depth": P13_DEPTH, "p13_width": P13_WIDTH,
            "outside_levels": sorted(OUTSIDE_LEVELS), "inside_levels": sorted(INSIDE_LEVELS)}
