"""T-164: railings / balustrades and shutters as BOQ lines (any villa; research module, not wired).

Measurement (owner rules in force, rules/owner_decisions/URBAN_RULES_1.5.0.json):
- UP-STAIR-012 v2.0.0: an open-edge guard is measured along its INSTALLED 3D path: straight sloped L = sqrt(H^2 + V^2),
  horizontal L = H, curved / helical L = sqrt((r*theta)^2 + V^2); shared vertices once; without drawn rail extents the
  flight's nosing pitch line H = (n-1)*going, V = (n-1)*riser. Never the plan projection as the billed length, never
  post spacing, rail height, fabrication allowance or undrawn returns.
- UP-STAIR-013 v1.0.0: a wall-mounted handrail is measured only where shown / specified / owner-confirmed; otherwise it
  is EXCLUDED with reason WALL_HANDRAIL_NOT_SPECIFIED (never quantified).
- UP-STAIR-014 is PROPOSED only (posts / balusters / panels): not applied.
- Shutters: no owner rule (BOQ family B6-05 'Shutters pcs / m2' NOT_IMPLEMENTED). A drawn shutter is counted in
  leaves (pcs); its m2 basis (louvre panel, leaf outline or opening) is not set by any rule, so m2 stays HELD.

Statuses (WORKFLOW_CONTROLS s.5) are per run: DRAWING-CONFIRMED (every segment from the drawings), HELD (a segment or the
run's extent is not established: the run is listed, its length is None or a bounded candidate, NEVER 0), UNKNOWN (the
element's type is not established, e.g. guard or stringer). A run drawn only on a render is not a run here (s.8).

Pure functions; no file or drawing access. `python3 -I research/agents_t164/t164_railings.py --check` runs the
hand-calculated synthetic fixture (Villa T, not the development villa) with its adverse cases.
"""

from __future__ import annotations

import math
import sys

UNITS = {"m": 1.0, "cm": 0.01, "mm": 0.001}
STATUSES = ("DRAWING-CONFIRMED", "HELD", "UNKNOWN")
EPS = 1e-9


class RailInputError(ValueError):
    """A required value is missing or a unit is unknown (held, never silently 0)."""


def to_m(value, units: str = "m") -> float:
    if units not in UNITS:
        raise RailInputError(f"unknown unit {units!r}")
    if value is None:
        raise RailInputError("missing value (held, never 0)")
    return float(value) * UNITS[units]


# ---------------------------------------------------------------- segment lengths (UP-STAIR-012)

def seg_horizontal(h: float) -> float:
    if h is None or h < 0:
        raise RailInputError("horizontal segment without a plan length")
    return float(h)


def seg_sloped(h: float, v: float) -> float:
    if h is None or v is None:
        raise RailInputError("sloped segment needs both H and V (held, never 0)")
    return math.hypot(h, v)


def seg_helical(r: float, theta_rad: float, v: float) -> float:
    if r is None or theta_rad is None or v is None:
        raise RailInputError("helical segment needs r, theta and V")
    return math.hypot(r * abs(theta_rad), v)


def flight_pitch(risers: int, riser: float, going: float) -> tuple[float, float, float]:
    """UP-STAIR-012 fallback when the rail extents are not drawn: nosing pitch line of one flight -> (H, V, L)."""
    if risers is None or riser is None or going is None:
        raise RailInputError("flight needs risers, riser and going")
    if risers < 2:
        raise RailInputError("a flight needs at least two risers for a pitch line")
    h, v = (risers - 1) * going, (risers - 1) * riser
    return h, v, math.hypot(h, v)


def per_tread(plan_lengths, riser: float) -> float:
    """Variable-pitch path (winders, curved inner strings): one sloped piece per going, sum sqrt(h_i^2 + riser^2)."""
    if riser is None or any(h is None for h in plan_lengths):
        raise RailInputError("per-tread path needs every tread plan length and the riser")
    return sum(math.hypot(h, riser) for h in plan_lengths)


# ---------------------------------------------------------------- plan geometry helpers

def polyline_length(pts) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def centreline_of_pair(len_a: float, len_b: float) -> float:
    """A 50 mm railing band drawn as two parallel lines whose ends differ by the band width at a shared corner:
    the centreline is the mean (corner counted once, never the outer line of both legs)."""
    return 0.5 * (len_a + len_b)


def angle_deg(c, p) -> float:
    return math.degrees(math.atan2(p[1] - c[1], p[0] - c[0])) % 360.0


def line_circle(p, q, c, r):
    """Intersections of the infinite line p-q with the circle (c, r); returns the point nearest to q."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    fx, fy = p[0] - c[0], p[1] - c[1]
    a = dx * dx + dy * dy
    b = 2 * (fx * dx + fy * dy)
    k = fx * fx + fy * fy - r * r
    disc = b * b - 4 * a * k
    if a < EPS or disc < 0:
        raise RailInputError("riser line does not meet the rail circle")
    s = math.sqrt(disc)
    cands = [(p[0] + t * dx, p[1] + t * dy) for t in ((-b - s) / (2 * a), (-b + s) / (2 * a))]
    return min(cands, key=lambda z: math.hypot(z[0] - q[0], z[1] - q[1]))


def sweep_deg(a0: float, a1: float) -> float:
    """Smallest absolute sweep between two angles (deg); direction-free, so mirror / rotation do not change it."""
    d = abs((a1 - a0) % 360.0)
    return min(d, 360.0 - d)


def curved_tread_lengths(centre, r, riser_lines):
    """Plan lengths along a rail circle between successive riser lines (each riser given by two points)."""
    angs = [angle_deg(centre, line_circle(p, q, centre, r)) for p, q in riser_lines]
    return [r * math.radians(sweep_deg(a, b)) for a, b in zip(angs, angs[1:])], angs


def transform(pts, rot_deg=0.0, mirror=False, scale=1.0, shift=(0.0, 0.0)):
    """Rotate / mirror / scale a point list (adverse-case helper: lengths must not change except by scale)."""
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    out = []
    for x, y in pts:
        x = -x if mirror else x
        out.append((scale * (c * x - s * y) + shift[0], scale * (s * x + c * y) + shift[1]))
    return out


# ---------------------------------------------------------------- runs and census

def run(rid, kind, segments=None, status="DRAWING-CONFIRMED", height_m=None, source="", note=""):
    """One railing run. segments: list of (label, length_m or None). A None segment holds the run (never 0)."""
    if status not in STATUSES:
        raise RailInputError(f"unknown status {status!r}")
    segs = list(segments or [])
    known = [v for _, v in segs if v is not None]
    measured = round(sum(known), 6) if known else None       # nothing measured -> None, never 0
    held = [lab for lab, v in segs if v is None]
    if not segs:
        held = ["extent not established"]
    if held and status == "DRAWING-CONFIRMED":
        status = "HELD"
    return {"id": rid, "kind": kind, "segments": segs, "measured_lm": measured,
            "held_parts": held, "status": status, "height_m": height_m, "source": source, "note": note}


def wall_handrail(rid, shown: bool, length_m=None, source=""):
    """UP-STAIR-013: a wall-side handrail exists in the BOQ only where shown; otherwise excluded with reason."""
    if not shown:
        return {"id": rid, "kind": "WALL_HANDRAIL", "excluded": "WALL_HANDRAIL_NOT_SPECIFIED", "measured_lm": None,
                "status": "EXCLUDED", "source": source}
    return run(rid, "WALL_HANDRAIL", [("wall side", length_m)], source=source)


def census(runs):
    """Totals per status. Only fully drawing-confirmed runs make the confirmed total; HELD / UNKNOWN runs are counted
    and their measured parts reported apart, never added as if complete and never as 0."""
    out = {"DRAWING-CONFIRMED_lm": 0.0, "HELD_runs": [], "HELD_measured_part_lm": 0.0, "UNKNOWN_runs": [],
           "EXCLUDED": []}
    for r_ in runs:
        st = r_["status"]
        if st == "EXCLUDED":
            out["EXCLUDED"].append(r_["id"])
        elif st == "DRAWING-CONFIRMED":
            out["DRAWING-CONFIRMED_lm"] += r_["measured_lm"]
        elif st == "HELD":
            out["HELD_runs"].append(r_["id"])
            out["HELD_measured_part_lm"] += r_["measured_lm"] or 0.0
        else:
            out["UNKNOWN_runs"].append(r_["id"])
    out["DRAWING-CONFIRMED_lm"] = round(out["DRAWING-CONFIRMED_lm"], 6)
    out["HELD_measured_part_lm"] = round(out["HELD_measured_part_lm"], 6)
    return out


def shutter(opening_id, leaves_drawn, leaf_w=None, leaf_h=None, source=""):
    """Shutters of one opening. Count from the drawing; m2 HELD (no measurement basis in any owner rule)."""
    if leaves_drawn is None:
        raise RailInputError("leaf count missing")
    if leaves_drawn == 0:
        return {"opening": opening_id, "leaves_pcs": 0, "status": "NOT DRAWN", "m2": None, "source": source}
    size = None if (leaf_w is None or leaf_h is None) else (round(leaf_w, 3), round(leaf_h, 3))
    return {"opening": opening_id, "leaves_pcs": leaves_drawn, "leaf_size_m": size,
            "status": "DRAWING-CONFIRMED (count)", "m2": None, "m2_status": "HELD (no shutter m2 basis in a rule)",
            "size_status": "DRAWING-CONFIRMED" if size else "HELD (size not printed)", "source": source}


# ---------------------------------------------------------------- synthetic fixture (Villa T, not the development villa)

def _close(a, b, tol=1e-4):
    return abs(a - b) <= tol


def check() -> list[str]:
    msgs = []

    def ok(cond, text):
        if not cond:
            raise AssertionError(text)
        msgs.append("PASS " + text)

    # 1. roof terrace 6.00 x 4.00, railing on two sides as a 50 mm band: outer legs 6.05 / 4.05, inner legs 6.00 / 4.00
    #    hand: centreline 6.025 + 4.025 = 10.050 lm, corner once. ADVERSE: outer line of both legs 6.05 + 4.05 = 10.10
    #    (+0.050, the corner counted twice).
    terrace = centreline_of_pair(6.05, 6.00) + centreline_of_pair(4.05, 4.00)
    ok(_close(terrace, 10.05), "roof railing two sides = 10.050 lm (centreline, corner once)")
    ok(_close((6.05 + 4.05) - terrace, 0.05), "adverse: outer-line sum overstates by 0.050 lm")

    # 2. straight flight 10 risers 0.17 / going 0.28, one open side: H 2.52, V 1.53, L = sqrt(6.3504 + 2.3409) = 2.948101
    h, v, l_ = flight_pitch(10, 0.17, 0.28)
    ok(_close(h, 2.52) and _close(v, 1.53) and _close(l_, 2.948101), "stair guard pitch line 2.948 lm")
    ok(_close(l_ - h, 0.428101), "adverse: plan projection 2.520 billed would lose 0.428 lm (-14.5 %)")

    # 3. wall side of the same flight, handrail not shown -> excluded, never quantified
    w = wall_handrail("T-WALL", shown=False)
    ok(w["status"] == "EXCLUDED" and w["measured_lm"] is None, "wall handrail not shown: EXCLUDED, no length")

    # 4. helical inner rail r 1.50, 90 deg, V 1.80: r*theta = 2.356194, L = sqrt(5.551652 + 3.24) = 2.965072
    ok(_close(seg_helical(1.5, math.pi / 2, 1.8), 2.965072), "helical rail 2.965 lm")

    # 5. winders: treads 0.20 / 0.25 / 0.30 / 0.30, riser 0.18: 0.269072 + 0.308058 + 0.349857 x 2 (=1.276845) = 1.276845;
    #    one straight segment over the same run sqrt(1.05^2 + 0.72^2) = 1.273146 (variable pitch kept per tread)
    pt = per_tread([0.20, 0.25, 0.30, 0.30], 0.18)
    ok(_close(pt, 1.276845), "winder rail per tread 1.277 lm")
    ok(_close(seg_sloped(1.05, 0.72), 1.273146), "single-pitch comparison 1.273 lm")

    # 6. curved string from coordinates: centre (0,0), rail r 1.0, radial risers at 0, 30, 60, 90 deg (lines from
    #    r 0.5 to r 2.0): three treads of r*pi/6 = 0.523599 each -> 1.570796; invariant under rotation 37 deg,
    #    mirror and mm units (scale 1000 then /1000)
    risers = [((0.5 * math.cos(math.radians(a)), 0.5 * math.sin(math.radians(a))),
               (2.0 * math.cos(math.radians(a)), 2.0 * math.sin(math.radians(a)))) for a in (0, 30, 60, 90)]
    base, _ = curved_tread_lengths((0.0, 0.0), 1.0, risers)
    ok(_close(sum(base), math.pi / 2), "curved treads from coordinates 1.571 m plan")
    for rot, mir in ((37.0, False), (0.0, True), (211.0, True)):
        moved = [tuple(transform([p, q], rot, mir)) for p, q in risers]
        lens, _ = curved_tread_lengths((0.0, 0.0), 1.0, moved)
        ok(_close(sum(lens), math.pi / 2), f"rotation {rot} mirror {mir}: same plan length")
    mm = [tuple(transform([p, q], 0.0, False, 1000.0)) for p, q in risers]
    lens_mm, _ = curved_tread_lengths((0.0, 0.0), 1000.0, mm)
    ok(_close(sum(lens_mm) * UNITS["mm"], math.pi / 2), "mm input converted: same 1.571 m")

    # 7. undimensioned railing (drawn on an elevation only, no plan band, no dimension): HELD, length None, never 0
    und = run("T-ELEV", "GUARD", [("elevation only, not dimensioned", None)])
    ok(und["status"] == "HELD" and und["held_parts"] and und["measured_lm"] is None,
       "undimensioned railing HELD, measured None (never 0)")

    # 8. census: confirmed = terrace 10.050 + stair 2.948101 = 12.998101; held listed apart measured part None
    runs = [run("T-ROOF", "GUARD_HORIZONTAL", [("two sides", terrace)]),
            run("T-STAIR", "STAIR_GUARD", [("flight", l_)]), und, w]
    cen = census(runs)
    ok(_close(cen["DRAWING-CONFIRMED_lm"], 12.998101), "census confirmed 12.998 lm")
    ok(cen["HELD_runs"] == ["T-ELEV"] and cen["EXCLUDED"] == ["T-WALL"], "census lists held and excluded runs")

    # 9. shutters: window A 1.20 x 1.50 with two leaves 0.60 x 1.50 drawn; window B none drawn
    sa, sb = shutter("T-WA", 2, 0.60, 1.50), shutter("T-WB", 0)
    ok(sa["leaves_pcs"] == 2 and sa["m2"] is None, "shutters: 2 leaves counted, m2 HELD (no basis)")
    ok(sb["status"] == "NOT DRAWN" and sb["leaves_pcs"] == 0, "window without drawn shutters: none")

    # 10. missing data and units refused
    for bad in (lambda: flight_pitch(None, 0.17, 0.28), lambda: to_m(None), lambda: to_m(1, "ft"),
                lambda: seg_sloped(None, 1.0), lambda: shutter("x", None)):
        try:
            bad()
        except RailInputError:
            continue
        raise AssertionError("missing value or unit accepted")
    msgs.append("PASS missing values / unknown units refused (held, never 0)")
    return msgs


if __name__ == "__main__":
    if "--check" in sys.argv:
        for m in check():
            print(m)
        print("t164_railings --check: all PASS")
    else:
        print(__doc__)
