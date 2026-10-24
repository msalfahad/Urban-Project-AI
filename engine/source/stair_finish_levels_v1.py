"""STAIR FINISH LEVELS V1 - the owner's finish-level method for stairs (UP-STAIR-016, URBAN_RULES 1.7.0) as an
opt-in check and takeoff module: finished and structural levels of every riser from the per-surface finishes, riser /
going counts per flight from the drawn surfaces, going alternatives, coordination findings, a design-scenario report
for stairs the drawings do not define, and per-component quantities (concrete, marble, nosing, rail, bars) from ONE
stair record (generic; T-267).

Wired into no method (DEFAULT_GUARD_CLASS UNWIRED_PRODUCER): no released or candidate quantity reads it. It wraps the
frozen stair functions and never edits them: stair_riser_schedule.first_last / counts_in_range (closed-form check and
riser counts), stair_fit_checks.max_risers / going_to_fit (fit), stair_geometry.polygon_area / is_simple /
straight_flight (areas and the flight profile).

What it never does (owner 2026-10-24, OWNER_RULE_STAIRS_2026-10-24.md):
  - choose a value: an unknown finish (F0, F1, any tread / landing finish S), waist, width, polygon or level is HELD,
    never 100 mm, 30 mm or 0; a HELD quantity is blank in the measured export, never 0, never a range;
  - change a drawn stair: the owner ranges (finished riser 150 - 170 mm, going 280 - 300 mm) are CHECKS on a drawn
    stair (finding OUTSIDE_OWNER_PREFERENCE), never a replacement;
  - assume N - 1 goings: goings are the drawn tread surfaces of each flight; a landing is never a going;
  - use a rectangle formula for a landing: landing areas are the drawn polygons (arcs exactly, by their bulge);
  - generate winders or any off-axis line for winder treads; winder treads are measured from their drawn polygons only,
    an undrawn stair that would need winders is UNSUPPORTED;
  - read a run of unknown type as a maximum (RUN_TYPE_UNKNOWN gives labelled scenarios only);
  - select a design alternative or release its quantities: scenarios live in their own report schema, which the
    measured-export loader refuses;
  - claim regulatory conformity: code applicability is reported per source, CODE_NOT_VERIFIED until a clause is read.

Record (lengths and levels in mm; plan coordinates in mm, polygons as (x, y) or (x, y, bulge) vertices, DXF bulge
convention on the edge leaving the vertex):
    stair_id, ffl_bottom_mm, ffl_top_mm               finished floor levels (S-3: the riser basis is FFL to FFL)
    floor_bottom_finish_mm (F0), floor_top_finish_mm (F1)   FFL - structural slab top at each floor, or None
    slab_bottom_top_mm, slab_top_top_mm               structural slab tops if separately printed (consistency only)
    surfaces  [ {id, kind TREAD | LANDING | WINDER, flight, finish_mm (S), rises (default True: a riser leads onto
               it; False: same level as the previous surface, e.g. a tread drawn before its landing), going_mm,
               width_mm, riser_length_mm, polygon, thickness_mm (landing plate), depth_mm (landing, drawn)} ] in the
               order of ascent, excluding both floors
    floor_landings [ {id, floor BOTTOM | TOP, polygon} ]   floor-level landings: floor finish, never stair marble
    flights   {flight_id: {waist_mm, width_mm, rail_sides (list or None), run_mm, run_type, end_limit_mm,
               top_edge_mm}}  (run / alignment positions along the flight from its first riser line)
    riser_counts {source: n}                          independent readings (plan, section, ...): any difference is a
                                                      CONFLICT, never resolved here
    structural_risers_mm [..]                         drawn concrete risers (section), to test the finished ones
    cross_readings [ {item, arch, struct} ]           the same dimension read on two disciplines
    overhead  [ {id, flight, s_from_mm, s_to_mm, soffit_mm} ]  members over a flight (positions along the flight)
    stair_finish {material, source} | None            the stair finish material (marble) or None (HELD)
    arrival_nosing_mm                                 finish material thickness at the arrival edge, or None
    nosing {specified: bool, source}                  nosing is a line only where specified
    bar_detail  str | None                            the printed bar detail reference (bars are never computed here)
    limits {headroom_min_mm | landing_depth_min_mm: {value, source, verified}}
    building_type  PRIVATE_HOUSE | DWELLING_DEVELOPMENT | None (from the project manifest)

Stdlib + frozen engine.source stair modules only. No project data.
"""

from __future__ import annotations

import csv
import io
import json
import math
from decimal import Decimal

from engine.source import stair_fit_checks as SF
from engine.source import stair_geometry as SG
from engine.source import stair_riser_schedule as SR

POLICY_ID = "STAIR_FINISH_LEVELS_V1"
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"      # T-212: computes quantities, wired nowhere; guard due at integration
RULE_ID = "UP-STAIR-016"
RULE_SET = "URBAN_RULES 1.7.0"
SOURCE = "docs/agents/OWNER_RULE_STAIRS_2026-10-24.md (agents/control); " + RULE_SET + " " + RULE_ID

PREF_RISER_MM = (150.0, 170.0)                # owner preference (finished riser), a check on drawn stairs
PREF_GOING_MM = (280.0, 300.0)                # owner preference (going), a check on drawn stairs; S-6: an interval
ILLUSTRATIVE = {"riser_mm": 160.0, "going_mm": 300.0,
                "label": "ILLUSTRATIVE ONLY (owner S-4 point 7): the former 16 cm / 30 cm pair, never a measurement default"}
DRAWING_TOL_MM = 10.0                         # reading tolerance between two drawn values (T-214 TOL_DRAWN)
LEVEL_TOL_MM = 0.5                            # arithmetic tolerance on derived levels
OVERLAP_TOL_MM2 = 1.0                         # two surface polygons overlapping more than this is a double count
ARC_STEP = 2.0 * math.pi / 256.0              # arc subdivision for the overlap test only (areas are exact)

TREAD, LANDING, WINDER = "TREAD", "LANDING", "WINDER"
KINDS = (TREAD, LANDING, WINDER)
FIXED, MAXIMUM, UNKNOWN = "FIXED", "MAXIMUM", "RUN_TYPE_UNKNOWN"
RUN_TYPES = (FIXED, MAXIMUM, UNKNOWN)

MEASURED, HELD, UNSUPPORTED, NOT_SPECIFIED = "MEASURED", "HELD", "UNSUPPORTED", "NOT_SPECIFIED"
CODE_NOT_VERIFIED = "CODE_NOT_VERIFIED"
FINDINGS = ("PROJECTION", "MISALIGNED_TOP", "EXTRA_OR_MISSING_STEP", "LANDING_DEPTH", "HEADROOM",
            "ARCH_STRUCT_DISAGREE", "OUTSIDE_OWNER_PREFERENCE", "UNEQUAL_FINISHED_RISERS", "LEVEL_INCONSISTENT",
            "SURFACE_OVERLAP", "CONCRETE_STEP_AT_SAME_LEVEL")
MEASURED_SCHEMA = "STAIR_MEASURED_ROWS_V1"
SCENARIO_SCHEMA = "STAIR_SCENARIO_REPORT_V1"
EXPORT_COLUMNS = ("row_kind", "stair_id", "component", "part", "unit", "quantity", "status", "basis", "missing")
NO_CONFLICT_STATEMENT = "no conflict found against verified clauses (verified clauses: none)"

UDC = ("Kuwait Universal Design Code, October 2017, section 4 (printed page 10): scope excludes private houses; "
       "its provisions may apply to public areas of dwelling developments (owner reading 2026-10-24 13:50, "
       "SOURCE-VERIFIED SCOPE STATEMENT)")
KM = "Kuwait Municipality private / model housing building requirements and amendments incl. MD 288/2024"
KFF = "Kuwait Fire Force stair requirements"


class StairFinishError(ValueError):
    pass


# ------------------------------------------------------------------ polygons with arcs
def _pt(v):
    if len(v) == 2:
        return float(v[0]), float(v[1]), 0.0
    if len(v) == 3:
        return float(v[0]), float(v[1]), float(v[2] or 0.0)
    raise StairFinishError("a vertex is (x, y) or (x, y, bulge)")


def bulge_area(points):
    """exact area of a closed outline whose edges are straight or circular arcs (DXF bulge = tan(angle / 4) on the
    edge leaving the vertex; positive = counter-clockwise arc)."""
    pts = [_pt(v) for v in points]
    if len(pts) < 2 or (len(pts) < 3 and all(p[2] == 0.0 for p in pts)):
        raise StairFinishError("an outline needs three vertices, or two joined by arcs")
    signed = 0.0
    for (x0, y0, b), (x1, y1, _) in zip(pts, pts[1:] + pts[:1]):
        signed += (x0 * y1 - x1 * y0) / 2.0
        if b:
            th = 4.0 * math.atan(abs(b))
            c = math.hypot(x1 - x0, y1 - y0)
            r = c / (2.0 * math.sin(th / 2.0))
            signed += math.copysign(r * r / 2.0 * (th - math.sin(th)), b)
    if len(pts) >= 3 and all(p[2] == 0.0 for p in pts):
        straight = SG.polygon_area([(p[0], p[1]) for p in pts])           # frozen shoelace, same value
        if abs(straight - abs(signed)) > 1e-6 * max(1.0, straight):
            raise StairFinishError("area check failed")
    return abs(signed)


def densify(points, step=ARC_STEP):
    """the outline as straight points; an arc is subdivided at a fixed angular step, so two outlines sharing an arc
    produce the same points (used for the overlap test only)."""
    pts = [_pt(v) for v in points]
    out = []
    for (x0, y0, b), (x1, y1, _) in zip(pts, pts[1:] + pts[:1]):
        out.append((x0, y0))
        if not b:
            continue
        th = 4.0 * math.atan(abs(b))
        mx, my, dx, dy = (x0 + x1) / 2.0, (y0 + y1) / 2.0, x1 - x0, y1 - y0
        d = math.hypot(dx, dy)
        nlx, nly = -dy / d, dx / d
        k = (d / 2.0) / math.tan(th / 2.0) * (1.0 if b > 0 else -1.0)
        cx, cy = mx + nlx * k, my + nly * k
        r = math.hypot(x0 - cx, y0 - cy)
        a0 = math.atan2(y0 - cy, x0 - cx)
        n = max(1, int(math.ceil(th / step - 1e-9)))
        sgn = 1.0 if b > 0 else -1.0
        for i in range(1, n):
            a = a0 + sgn * th * i / n
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def _signed(poly):
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1])) / 2.0


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _in_tri(p, a, b, c):
    return _cross(a, b, p) > 1e-9 and _cross(b, c, p) > 1e-9 and _cross(c, a, p) > 1e-9


def triangulate(poly):
    """ear clipping of a simple polygon (no holes) into counter-clockwise triangles."""
    p = [tuple(v) for v in poly]
    if _signed(p) < 0:
        p.reverse()
    tris, guard = [], 0
    while len(p) > 3 and guard < 10000:
        guard += 1
        n = len(p)
        for i in range(n):
            a, b, c = p[i - 1], p[i], p[(i + 1) % n]
            cr = _cross(a, b, c)
            if abs(cr) <= 1e-9 * max(1.0, math.dist(a, c) ** 2):            # collinear vertex: drop it
                del p[i]
                break
            if cr < 0:
                continue
            if any(_in_tri(q, a, b, c) for q in p if q not in (a, b, c)):
                continue
            tris.append((a, b, c))
            del p[i]
            break
        else:
            raise StairFinishError("outline cannot be triangulated (not simple?)")
    if len(p) == 3 and abs(_signed(p)) > 1e-9:
        tris.append(tuple(p))
    return tris


def _clip_convex(subject, clip):
    out = list(subject)
    for a, b in zip(clip, clip[1:] + clip[:1]):
        if not out:
            break
        inp, out = out, []
        for p, q in zip(inp, inp[1:] + inp[:1]):
            pin, qin = _cross(a, b, p) >= -1e-12, _cross(a, b, q) >= -1e-12
            if pin and qin:
                out.append(q)
            elif pin or qin:
                den = (p[0] - q[0]) * (a[1] - b[1]) - (p[1] - q[1]) * (a[0] - b[0])
                if abs(den) > 1e-15:
                    t = ((p[0] - a[0]) * (a[1] - b[1]) - (p[1] - a[1]) * (a[0] - b[0])) / den
                    out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
                if qin:
                    out.append(q)
    return out


def overlap_area(poly_a, poly_b):
    """area common to two simple outlines (arcs subdivided), by triangle-triangle clipping."""
    ta, tb = triangulate(densify(poly_a)), triangulate(densify(poly_b))
    tot = 0.0
    for t1 in ta:
        for t2 in tb:
            c = _clip_convex(list(t1), list(t2))
            if len(c) >= 3:
                tot += abs(_signed(c))
    return tot


# ------------------------------------------------------------------ helpers
def _blank(v):
    return v is None


def _line(component, part, unit, qty, status, basis, missing=()):
    if status != MEASURED:
        qty = None                                         # HELD / UNSUPPORTED / NOT_SPECIFIED: blank, never 0
    return {"component": component, "part": part, "unit": unit, "quantity": qty, "status": status, "basis": basis,
            "missing": list(missing)}


def riser_count_exact(rise, riser):
    """the riser count when `rise` / `riser` is a whole number in exact decimal arithmetic (4.48 / 0.16 = 28),
    else None; never rounded up or down."""
    q = Decimal(str(rise)) / Decimal(str(riser))
    return int(q) if q == q.to_integral_value() else None


def _finding(code, where, detail, values=None, conflict=False):
    if code not in FINDINGS:
        raise StairFinishError(f"unknown finding {code}")
    return {"code": code, "where": where, "detail": detail, "values": values or {},
            "kind": "CONFLICT" if conflict else "FINDING", "changes_geometry": False}


def _limit(rec, name):
    lim = (rec.get("limits") or {}).get(name)
    if not lim or lim.get("value") is None:
        return None
    return lim


# ------------------------------------------------------------------ levels
def levels(rec):
    """finished and structural level of every surface and riser; structural riser heights by the owner method
    (riser i = R + S(i-1) - S(i), first = R + F0 - S1, last = R + S(last) - F1), each one None where a finish it
    depends on is unknown."""
    surf = list(rec.get("surfaces") or [])
    for s in surf:
        if s.get("kind") not in KINDS:
            raise StairFinishError(f"surface {s.get('id')}: kind must be one of {KINDS}")
    if surf and surf[0].get("rises", True) is False:
        raise StairFinishError("the first surface must be reached by a riser (a floor-level landing goes in floor_landings)")
    b, t = rec.get("ffl_bottom_mm"), rec.get("ffl_top_mm")
    n = sum(1 for s in surf if s.get("rises", True)) + 1                 # + the riser onto the upper floor
    out = {"n_risers": n, "rise_mm": None, "riser_mm": None, "surfaces": [], "risers": [], "missing": [],
           "closure": None, "count_conflict": None}
    rc = rec.get("riser_counts") or {}
    gov = rec.get("riser_count_governs")
    if len(set(rc.values())) > 1 or (rc and n not in rc.values()):
        if gov is not None and gov in rc and rc[gov] == n:
            out["count_conflict"] = {"readings": dict(rc), "governs": gov, "held": False}
        else:
            out["count_conflict"] = {"readings": dict(rc), "governs": None, "held": True}
            out["missing"].append("riser count CONFLICT between the drawings (no governing decision)")
    h = None
    if b is None or t is None:
        out["missing"].append("finished floor level (bottom / top)")
    else:
        rise = float(t) - float(b)
        if rise <= 0:
            raise StairFinishError("the upper finished floor must be above the lower one")
        out["rise_mm"] = rise
        if not (out["count_conflict"] or {}).get("held"):
            h = rise / n
    out["riser_mm"] = h
    f0, f1 = (rec.get("floor_bottom_finish_mm"), rec.get("floor_top_finish_mm")) if h is not None else (None, None)
    k = 0
    for s in surf:
        if s.get("rises", True):
            k += 1
        fin = None if h is None else float(b) + k * h
        sf = s.get("finish_mm")
        out["surfaces"].append({"id": s["id"], "kind": s["kind"], "level_no": k, "finished_mm": fin,
                                "finish_mm": sf, "concrete_mm": None if (sf is None or fin is None) else fin - sf})
    # nodes: every distinct level with the surface a riser leaves (last at that level) and the one it reaches (first)
    bottom = {"id": "FLOOR_BOTTOM", "finished_mm": None if h is None else float(b),
              "finish_mm": rec.get("floor_bottom_finish_mm"),
              "concrete_mm": None if (f0 is None or h is None) else float(b) - f0}
    top = {"id": "FLOOR_TOP", "finished_mm": None if h is None else float(t), "finish_mm": rec.get("floor_top_finish_mm"),
           "concrete_mm": None if (f1 is None or h is None) else float(t) - f1}
    by_level = {}
    for s in out["surfaces"]:
        by_level.setdefault(s["level_no"], []).append(s)
    for j in range(1, n + 1):
        leave = bottom if j == 1 else by_level[j - 1][-1]
        onto = top if j == n else by_level[j][0]
        conc = None if (leave["concrete_mm"] is None or onto["concrete_mm"] is None) \
            else onto["concrete_mm"] - leave["concrete_mm"]
        miss = [f"finish of {x['id']}" for x in (leave, onto) if x["finish_mm"] is None] + list(out["missing"])
        out["risers"].append({"riser": j, "from": leave["id"], "onto": onto["id"], "finished_riser_mm": h,
                              "finished_mm": onto["finished_mm"], "structural_riser_mm": conc,
                              "status": MEASURED if conc is not None else HELD, "missing": miss})
    for lv, ss in by_level.items():
        cs = [x["concrete_mm"] for x in ss]
        if len(ss) > 1 and None not in cs and max(cs) - min(cs) > LEVEL_TOL_MM:
            out.setdefault("same_level_steps", []).append({"level_no": lv, "surfaces": [x["id"] for x in ss],
                                                           "concrete_mm": cs})
    if f0 is not None and f1 is not None and all(r["structural_riser_mm"] is not None for r in out["risers"]):
        tot = sum(r["structural_riser_mm"] for r in out["risers"])
        want = (float(t) - f1) - (float(b) - f0)
        jumps = sum(ss[-1]["concrete_mm"] - ss[0]["concrete_mm"] for ss in by_level.values())
        out["closure"] = {"sum_structural_risers_mm": tot, "slab_to_slab_mm": want,
                          "same_level_concrete_steps_mm": jumps, "closes": abs(tot + jumps - want) <= LEVEL_TOL_MM}
    finishes = {s.get("finish_mm") for s in surf}
    if f0 is not None and f1 is not None and len(finishes) == 1 and None not in finishes and n >= 2:
        s_ = finishes.pop()
        first, last = SR.first_last(h, f0, f1, s_)                        # frozen closed form, same convention
        out["closed_form"] = {"first": first, "last": last,
                              "agrees": abs(first - out["risers"][0]["structural_riser_mm"]) <= LEVEL_TOL_MM
                              and abs(last - out["risers"][-1]["structural_riser_mm"]) <= LEVEL_TOL_MM}
    return out


# ------------------------------------------------------------------ flights and goings
def flights(rec):
    """flights from the drawn surfaces: risers onto a flight's treads (and the riser that leaves its last tread
    for a landing or the upper floor) belong to it; its goings are its drawn TREAD / WINDER surfaces. A riser between
    two landings (or a floor and a landing) belongs to no flight (TRANSITION)."""
    surf = list(rec.get("surfaces") or [])
    lv = levels(rec)
    n = lv["n_risers"]
    groups, order = {}, []
    for s in surf:
        if s["kind"] in (TREAD, WINDER):
            f = s.get("flight")
            if f is None:
                raise StairFinishError(f"tread {s['id']} names no flight")
            if f not in groups:
                groups[f] = {"flight": f, "treads": [], "risers": [], "kinds": set()}
                order.append(f)
            groups[f]["treads"].append(s)
            groups[f]["kinds"].add(s["kind"])
    kind_of = {s["id"]: s for s in surf}
    transitions = []
    for r in lv["risers"]:
        onto, frm = kind_of.get(r["onto"]), kind_of.get(r["from"])
        if onto is not None and onto["kind"] in (TREAD, WINDER):
            groups[onto["flight"]]["risers"].append(r["riser"])
        elif frm is not None and frm["kind"] in (TREAD, WINDER):
            groups[frm["flight"]]["risers"].append(r["riser"])
        else:
            transitions.append(r["riser"])
    out = []
    for f in order:
        g = groups[f]
        straight = g["kinds"] == {TREAD}
        goings = [s.get("going_mm") for s in g["treads"]]
        last_t = g["treads"][-1]["id"]
        leaves_last = any(r["from"] == last_t for r in lv["risers"])
        out.append({"flight": f, "risers": len(g["risers"]), "riser_ids": g["risers"], "goings": len(g["treads"]),
                    "going_basis": "drawn tread surfaces of the flight (a landing is never a going)",
                    "configuration": ("LAST_RISER_ONTO_NEXT_LEVEL" if leaves_last else "LAST_TREAD_AT_LANDING_LEVEL"),
                    "straight": straight, "has_winders": WINDER in g["kinds"], "going_mm": goings,
                    "tread_ids": [s["id"] for s in g["treads"]]})
    return {"flights": out, "transition_risers": transitions, "n_risers": n}


def going_alternatives(n_goings, going_mm, rng=PREF_GOING_MM):
    """S-6: the continuous going interval inside the owner range applied to the ACTUAL going count of a flight, and
    the run change against the drawn goings. A report for the designer, never a change."""
    if n_goings < 1:
        return None
    run_now = sum(going_mm) if going_mm and None not in going_mm else None
    lo, hi = rng
    out = {"goings": n_goings, "run_now_mm": run_now, "going_interval_mm": [lo, hi],
           "run_interval_mm": [n_goings * lo, n_goings * hi]}
    if run_now is not None:
        out["run_change_mm"] = [n_goings * lo - run_now, n_goings * hi - run_now]
    return out


# ------------------------------------------------------------------ positions along a flight
def _positions(goings):
    """riser line positions along a straight flight from its first riser line: riser k at the sum of the goings
    before it."""
    pos, s = [0.0], 0.0
    for g in goings:
        s += g
        pos.append(s)
    return pos


def _headroom_drawn(rec, fl, lv):
    rows = []
    surf_lv = {s["id"]: s for s in lv["surfaces"]}
    lim = _limit(rec, "headroom_min_mm")
    for o in rec.get("overhead") or []:
        f = next((x for x in fl["flights"] if x["flight"] == o.get("flight")), None)
        if f is None or not f["straight"] or None in f["going_mm"] or lv["riser_mm"] is None:
            rows.append({"member": o.get("id"), "status": HELD, "clear_mm": None,
                         "missing": ["a straight flight with drawn goings under the member and its finished levels"]})
            continue
        pos = _positions(f["going_mm"])
        a, b = sorted((float(o["s_from_mm"]), float(o["s_to_mm"])))
        clears = []
        for i, tid in enumerate(f["tread_ids"]):
            if pos[i] < b and pos[i + 1] > a:
                clears.append((tid, float(o["soffit_mm"]) - surf_lv[tid]["finished_mm"]))
        if not clears:
            rows.append({"member": o["id"], "status": MEASURED, "clear_mm": None, "treads": [], "check": "NO_TREAD_UNDER"})
            continue
        mn = min(c for _, c in clears)
        row = {"member": o["id"], "status": MEASURED, "clear_mm": mn, "treads": [t for t, _ in clears]}
        if lim is None:
            row["check"] = "NO_LIMIT_GIVEN"
        elif not lim.get("verified"):
            row["check"] = CODE_NOT_VERIFIED
            row["limit"] = lim
        else:
            row["check"] = "MEETS_LIMIT" if mn + LEVEL_TOL_MM >= float(lim["value"]) else "BELOW_LIMIT"
            row["limit"] = lim
        rows.append(row)
    return rows


# ------------------------------------------------------------------ concrete
def _flight_profile(c0, treads_conc, goings, waist, leaves_last):
    """the flight's section between plumb cuts at its first and last riser lines (stair_geometry convention): the
    stepped top from the actual concrete levels, the soffit parallel to the line through the step roots, lowered by
    waist / cos. The roots must be collinear (else the soffit plane is not defined by the steps: HELD)."""
    pos = _positions(goings)
    roots = [(pos[k], treads_conc[k - 1]) for k in range(1, len(goings))]
    if leaves_last:
        roots.append((pos[-1], treads_conc[-1]))
    if len(roots) < 2:
        return None, "fewer than two step roots: the soffit plane is not defined by the steps"
    (s1, z1), (s2, z2) = roots[0], roots[-1]
    if s2 - s1 <= 0:
        return None, "step roots coincide"
    slope = (z2 - z1) / (s2 - s1)
    for s, z in roots:
        if abs(z1 + slope * (s - s1) - z) > LEVEL_TOL_MM:
            return None, "step roots not collinear (finishes or goings vary inside the flight): soffit plane not drawn"
    cos = 1.0 / math.hypot(1.0, slope)
    drop = waist / cos

    def soffit(s):
        return z1 + slope * (s - s1) - drop
    pts = [(0.0, c0)]
    for k, cz in enumerate(treads_conc):
        pts.append((pos[k], cz))
        pts.append((pos[k + 1], cz))
    pts.append((pos[-1], soffit(pos[-1])))
    pts.append((0.0, soffit(0.0)))
    if not SG.is_simple(pts):
        return None, "profile not simple (waist too thin for the steps?)"
    soff = math.hypot(pos[-1], slope * pos[-1])
    return {"outline": pts, "profile_mm2": SG.polygon_area(pts), "soffit_length_mm": soff, "slope": slope}, None


def _concrete(rec, fl, lv):
    lines = []
    conc = {s["id"]: s["concrete_mm"] for s in lv["surfaces"]}
    conc["FLOOR_BOTTOM"] = None if rec.get("floor_bottom_finish_mm") is None or rec.get("ffl_bottom_mm") is None \
        else float(rec["ffl_bottom_mm"]) - rec["floor_bottom_finish_mm"]
    first_from = {r["riser"]: r["from"] for r in lv["risers"]}
    fdat = rec.get("flights") or {}
    for f in fl["flights"]:
        d = fdat.get(f["flight"]) or {}
        miss = [d["conflict"]] if d.get("conflict") else []
        if f["has_winders"]:
            lines.append(_line("CONCRETE", f"flight {f['flight']}", "m3", None, HELD,
                               "winder turn: needs a drawn soffit; none is derived here (S-9)",
                               ["drawn winder soffit"]))
            continue
        if d.get("waist_mm") is None:
            miss.append("waist thickness")
        if d.get("width_mm") is None:
            miss.append("flight width")
        if None in f["going_mm"]:
            miss.append("drawn going of every tread")
        c0 = conc.get(first_from[f["riser_ids"][0]]) if f["riser_ids"] else None
        tc = [conc[t] for t in f["tread_ids"]]
        if c0 is None or None in tc:
            miss.append("concrete level under every surface (finishes F0 / S)")
        if lv["riser_mm"] is None:
            miss.append("finished floor levels")
        if miss:
            lines.append(_line("CONCRETE", f"flight {f['flight']}", "m3", None, HELD, "flight profile x width", miss))
            continue
        prof, why = _flight_profile(c0, tc, f["going_mm"], float(d["waist_mm"]),
                                    f["configuration"] == "LAST_RISER_ONTO_NEXT_LEVEL")
        if prof is None:
            lines.append(_line("CONCRETE", f"flight {f['flight']}", "m3", None, HELD, why, [why]))
            continue
        vol = prof["profile_mm2"] * float(d["width_mm"]) / 1e9
        lines.append(_line("CONCRETE", f"flight {f['flight']}", "m3", vol, MEASURED,
                           "section between plumb cuts at the first / last riser line x width; landing junctions "
                           "and members the flight meets are assigned by R-CONC-OWN-1 outside this module"))
    for s in rec.get("surfaces") or []:
        if s["kind"] != LANDING:
            continue
        miss = [m for m, v in (("landing outline", s.get("polygon")), ("landing plate thickness", s.get("thickness_mm")))
                if v is None]
        if miss:
            lines.append(_line("CONCRETE", f"landing {s['id']}", "m3", None, HELD, "drawn outline x plate thickness",
                               miss))
            continue
        lines.append(_line("CONCRETE", f"landing {s['id']}", "m3",
                           bulge_area(s["polygon"]) * float(s["thickness_mm"]) / 1e9, MEASURED,
                           "drawn outline (arcs exact) x plate thickness"))
    return lines


# ------------------------------------------------------------------ finishes, nosing, rail, bars
def _finishes(rec, fl, lv):
    lines = []
    spec = rec.get("stair_finish")
    nospec = ["stair finish material (drawing / specification)"] if not spec or not spec.get("material") else []
    by_id = {s["id"]: s for s in rec.get("surfaces") or []}
    fdat = rec.get("flights") or {}
    for s in rec.get("surfaces") or []:
        if s["kind"] == LANDING:
            continue
        miss = list(nospec)
        if (fdat.get(s.get("flight")) or {}).get("conflict"):
            miss.append(fdat[s["flight"]]["conflict"])
        area, basis = None, ""
        if s.get("polygon") is not None:
            area, basis = bulge_area(s["polygon"]) / 1e6, "drawn tread outline"
        elif s["kind"] == TREAD and s.get("going_mm") is not None and s.get("width_mm") is not None:
            area, basis = float(s["going_mm"]) * float(s["width_mm"]) / 1e6, "drawn going x drawn width (straight tread)"
        else:
            miss.append("drawn winder outline" if s["kind"] == WINDER else "drawn tread outline or going and width")
        lines.append(_line("MARBLE_TREAD", s["id"], "m2", area, HELD if miss else MEASURED, basis, miss))
    for s in rec.get("surfaces") or []:
        if s["kind"] != LANDING:
            continue
        miss = list(nospec)
        if s.get("polygon") is None:
            miss.append("drawn landing outline")
        area = None if s.get("polygon") is None else bulge_area(s["polygon"]) / 1e6
        lines.append(_line("MARBLE_LANDING", s["id"], "m2", area, HELD if miss else MEASURED,
                           "drawn landing outline (never width x width)", miss))
    for fll in rec.get("floor_landings") or []:
        lines.append(_line("FLOOR_FINISH_NOT_STAIR", fll["id"], "m2", None, NOT_SPECIFIED,
                           f"floor-level landing at the {fll.get('floor')} floor: measured by the floor finish, not here"))
    flw = {f["flight"]: (rec.get("flights") or {}).get(f["flight"], {}).get("width_mm") for f in fl["flights"]}
    last_flight = fl["flights"][-1]["flight"] if fl["flights"] else None
    for r in lv["risers"]:
        miss = list(nospec)
        for sid in (r["from"], r["onto"]):
            c = (fdat.get((by_id.get(sid) or {}).get("flight")) or {}).get("conflict")
            if c and c not in miss:
                miss.append(c)
        onto = by_id.get(r["onto"])
        if onto is not None:
            width = onto.get("riser_length_mm") or (onto.get("width_mm") if onto["kind"] != WINDER else None)
            if width is None and onto["kind"] == TREAD:
                width = flw.get(onto.get("flight"))
            frm = by_id.get(r["from"])
            if width is None and onto["kind"] == LANDING and frm is not None and frm["kind"] == TREAD:
                width = flw.get(frm.get("flight"))              # the riser closing a flight spans that flight
            build = onto.get("finish_mm")
            bname = f"finish of {onto['id']}"
        else:
            width = flw.get(last_flight)
            build = rec.get("arrival_nosing_mm")
            bname = "finish material thickness at the arrival edge"
        if width is None:
            miss.append("riser length (drawn)")
        if build is None:
            miss.append(bname)
        h = r["finished_riser_mm"]
        if h is None:
            miss.append("finished floor levels")
        vis = None if (h is None or build is None) else h - float(build)
        area = None if (vis is None or width is None) else vis * float(width) / 1e6
        lines.append(_line("MARBLE_RISER", f"riser {r['riser']}", "m2", area, HELD if miss else MEASURED,
                           "visible riser = finished riser - build-up of the surface it rises onto (UP-STAIR-003) "
                           "x riser length", miss))
    nos = rec.get("nosing") or {}
    if not nos.get("specified"):
        lines.append(_line("NOSING", "all", "m", None, NOT_SPECIFIED, "nosing is a line only where specified"))
    else:
        tot, miss = 0.0, []
        for r in lv["risers"]:
            onto = by_id.get(r["onto"])
            if onto is None:
                continue
            w = onto.get("riser_length_mm") or onto.get("width_mm") or flw.get(onto.get("flight"))
            if w is None:
                miss.append(f"edge length of {onto['id']}")
            else:
                tot += float(w)
        lines.append(_line("NOSING", "all", "m", tot / 1000.0, HELD if miss else MEASURED,
                           "edge of every surface a riser reaches (" + str(nos.get("source")) + ")", miss))
    return lines


def _rails(rec, fl, lv):
    lines = []
    for f in fl["flights"]:
        d = (rec.get("flights") or {}).get(f["flight"]) or {}
        sides = d.get("rail_sides")
        part = f"flight {f['flight']}"
        if f["has_winders"]:
            lines.append(_line("HANDRAIL", part, "m", None, UNSUPPORTED,
                               "a rail over winders needs its drawn line; none is derived (S-9)", ["drawn rail line"]))
            continue
        miss = [d["conflict"]] if d.get("conflict") else []
        if not sides:
            miss.append("rail sides (drawing)")
        if None in f["going_mm"]:
            miss.append("drawn going of every tread")
        if lv["riser_mm"] is None:
            miss.append("finished floor levels")
        if miss:
            lines.append(_line("HANDRAIL", part, "m", None, HELD, "per side: horizontal run / cos(pitch)", miss))
            continue
        pos = _positions(f["going_mm"])
        # nosing of every riser of the flight; the run from the first to the last nosing
        n_r = f["risers"]
        run = pos[n_r - 1] if n_r - 1 < len(pos) else pos[-1]
        rise = (n_r - 1) * lv["riser_mm"]
        one = math.hypot(run, rise)
        pitch = math.atan2(rise, run) if run > 0 else None
        check = run / math.cos(pitch) if pitch is not None else None
        if check is not None and abs(check - one) > 1e-6:
            raise StairFinishError("rail length check failed")
        lines.append(_line("HANDRAIL", part, "m", one * len(sides) / 1000.0, MEASURED,
                           f"{len(sides)} side(s) x horizontal run {run:.1f} mm / cos(pitch); landing rails not derived"))
    return lines


def _bars(rec):
    det = rec.get("bar_detail")
    if not det:
        return [_line("BARS", "all", "kg", None, HELD, "detailed bar takeoff from the printed detail",
                      ["printed bar detail of the stair"])]
    return [_line("BARS", "all", "kg", None, HELD, f"detail {det}: bar lengths and counts belong to the bar takeoff, "
                  "not to this module", ["bar takeoff from the detail (not computed here)"])]


# ------------------------------------------------------------------ findings
def _findings(rec, fl, lv):
    out = []
    cc = lv.get("count_conflict")
    if cc:
        why = ("independent readings disagree; never picked: every level and riser HELD" if cc["held"] else
               f"independent readings disagree; the count follows the governing decision {cc['governs']} "
               "(the other reading stays a designer item)")
        out.append(_finding("EXTRA_OR_MISSING_STEP", "riser count", why,
                            dict(cc["readings"], record=lv["n_risers"]), conflict=True))
    h = lv["riser_mm"]
    if h is not None and not PREF_RISER_MM[0] - LEVEL_TOL_MM <= h <= PREF_RISER_MM[1] + LEVEL_TOL_MM:
        out.append(_finding("OUTSIDE_OWNER_PREFERENCE", "finished riser", "outside 150 - 170 mm: reported, not changed",
                            {"riser_mm": h}))
    for s in rec.get("surfaces") or []:
        g = s.get("going_mm")
        if s["kind"] == TREAD and g is not None and not PREF_GOING_MM[0] - LEVEL_TOL_MM <= g <= PREF_GOING_MM[1] + LEVEL_TOL_MM:
            out.append(_finding("OUTSIDE_OWNER_PREFERENCE", s["id"], "going outside 280 - 300 mm: reported, not changed",
                                {"going_mm": g}))
    sr = rec.get("structural_risers_mm")
    if sr is not None:
        if len(sr) != lv["n_risers"]:
            out.append(_finding("EXTRA_OR_MISSING_STEP", "structural risers", "drawn concrete risers vs record count",
                                {"drawn": len(sr), "record": lv["n_risers"]}, conflict=True))
        else:
            fins = {"FLOOR_BOTTOM": rec.get("floor_bottom_finish_mm"), "FLOOR_TOP": rec.get("floor_top_finish_mm")}
            fins.update({s["id"]: s.get("finish_mm") for s in rec.get("surfaces") or []})
            fr = []
            for r, c in zip(lv["risers"], sr):
                a, b = fins.get(r["from"]), fins.get(r["onto"])
                fr.append(None if (a is None or b is None) else float(c) + b - a)
            known = [x for x in fr if x is not None]
            if known and max(known) - min(known) > DRAWING_TOL_MM:
                out.append(_finding("UNEQUAL_FINISHED_RISERS", "finished risers from the drawn concrete risers",
                                    "plausible structural risers give unequal finished risers",
                                    {"finished_mm": fr, "spread_mm": max(known) - min(known)}))
    if lv.get("closure") and not lv["closure"]["closes"]:
        out.append(_finding("LEVEL_INCONSISTENT", "risers", "structural risers do not close to slab-to-slab",
                            lv["closure"]))
    sb, st = rec.get("slab_bottom_top_mm"), rec.get("slab_top_top_mm")
    f0, f1 = rec.get("floor_bottom_finish_mm"), rec.get("floor_top_finish_mm")
    if None not in (sb, st, f0, f1) and lv["rise_mm"] is not None:
        want = lv["rise_mm"] - f1 + f0
        if abs((st - sb) - want) > LEVEL_TOL_MM:
            out.append(_finding("LEVEL_INCONSISTENT", "floor to floor",
                                "slab-to-slab differs from FFL-to-FFL less the floor build-ups",
                                {"slab_to_slab_mm": st - sb, "from_ffl_mm": want}, conflict=True))
    for x in rec.get("cross_readings") or []:
        if x.get("arch") is not None and x.get("struct") is not None and abs(x["arch"] - x["struct"]) > DRAWING_TOL_MM:
            out.append(_finding("ARCH_STRUCT_DISAGREE", x.get("item"), "architectural and structural readings differ",
                                {"arch": x["arch"], "struct": x["struct"]}, conflict=True))
    for f in fl["flights"]:
        d = (rec.get("flights") or {}).get(f["flight"]) or {}
        if None in f["going_mm"] or not f["straight"]:
            continue
        pos = _positions(f["going_mm"])
        last_line = pos[f["risers"] - 1] if f["risers"] - 1 < len(pos) else pos[-1]
        lim = d.get("end_limit_mm")
        if lim is not None and last_line > float(lim) + DRAWING_TOL_MM:
            out.append(_finding("PROJECTION", f"flight {f['flight']}", "the last riser line lies beyond the alignment",
                                {"last_riser_mm": last_line, "alignment_mm": lim, "beyond_mm": last_line - lim}))
        edge = d.get("top_edge_mm")
        if edge is not None and abs(last_line - float(edge)) > DRAWING_TOL_MM:
            out.append(_finding("MISALIGNED_TOP", f"flight {f['flight']}",
                                "the arrival riser does not meet the upper floor / landing edge",
                                {"last_riser_mm": last_line, "edge_mm": edge, "offset_mm": last_line - edge}))
    lim = _limit(rec, "landing_depth_min_mm")
    for s in rec.get("surfaces") or []:
        if s["kind"] == LANDING and s.get("depth_mm") is not None and lim is not None:
            if float(s["depth_mm"]) < float(lim["value"]):
                out.append(_finding("LANDING_DEPTH", s["id"], "landing depth below the stated limit"
                                    + ("" if lim.get("verified") else f" ({CODE_NOT_VERIFIED}: not enforced)"),
                                    {"depth_mm": s["depth_mm"], "limit": lim}))
    for row in _headroom_drawn(rec, fl, lv):
        if row.get("check") == "BELOW_LIMIT":
            out.append(_finding("HEADROOM", row["member"], "clear height below the verified limit", row))
    for st_ in lv.get("same_level_steps", []):
        out.append(_finding("CONCRETE_STEP_AT_SAME_LEVEL", ",".join(st_["surfaces"]),
                            "surfaces at one finished level with different finishes: a concrete step without a riser",
                            st_))
    polys = [(s["id"], s["polygon"]) for s in rec.get("surfaces") or [] if s.get("polygon") is not None]
    polys += [(x["id"], x["polygon"]) for x in rec.get("floor_landings") or [] if x.get("polygon") is not None]
    for i, (ia, pa) in enumerate(polys):
        for ib, pb in polys[i + 1:]:
            ov = overlap_area(pa, pb)
            if ov > OVERLAP_TOL_MM2:
                out.append(_finding("SURFACE_OVERLAP", f"{ia} / {ib}", "two surfaces share plan area: counted twice",
                                    {"overlap_mm2": ov}, conflict=True))
    return out


# ------------------------------------------------------------------ code applicability (S-7, A19 - A22)
def code_applicability(building_type):
    rows = [{"source": KM, "status": CODE_NOT_VERIFIED, "clauses_read": []},
            {"source": KFF, "status": CODE_NOT_VERIFIED, "clauses_read": []}]
    if building_type == "PRIVATE_HOUSE":
        rows.append({"source": UDC, "status": "NOT_APPLICABLE", "applies_to": "none (private house)",
                     "checks_emitted": False})
        decided = True
    elif building_type == "DWELLING_DEVELOPMENT":
        rows.append({"source": UDC, "status": CODE_NOT_VERIFIED, "applies_to": "public areas only (may apply)",
                     "private_units": "NOT_APPLICABLE", "checks_emitted": False, "enforced": False})
        decided = True
    else:
        rows.append({"source": UDC, "status": CODE_NOT_VERIFIED, "applies_to": "applicability not decided",
                     "checks_emitted": False})
        decided = False
    return {"building_type": building_type, "applicability_decided": decided, "sources": rows,
            "statement": NO_CONFLICT_STATEMENT, "regulatory_status": CODE_NOT_VERIFIED}


# ------------------------------------------------------------------ the check of a stair record
def check_stair(rec):
    """the whole report for one stair record: levels, flights, the four separate fit results, findings, quantity
    lines (each component released on its own evidence), code applicability. Nothing is changed or chosen."""
    lv = levels(rec)
    fl = flights(rec)
    fdat = rec.get("flights") or {}
    fit = []
    for f in fl["flights"]:
        d = fdat.get(f["flight"]) or {}
        rt, run = d.get("run_type", UNKNOWN), d.get("run_mm")
        if rt not in RUN_TYPES:
            raise StairFinishError(f"run type must be one of {RUN_TYPES}")
        if None in f["going_mm"] or not f["straight"]:
            fit.append({"flight": f["flight"], "status": HELD, "result": None,
                        "missing": ["straight flight with every going drawn"]})
            continue
        pos = _positions(f["going_mm"])
        length = pos[f["risers"] - 1] if f["risers"] - 1 < len(pos) else pos[-1]
        row = {"flight": f["flight"], "run_type": rt, "first_to_last_riser_mm": length, "available_mm": run}
        if run is None or rt == UNKNOWN:
            row.update(status=UNKNOWN, result=None)
        elif rt == FIXED:
            row.update(status=MEASURED, result="FITS" if abs(length - run) <= DRAWING_TOL_MM else "DOES_NOT_FIT")
        else:
            row.update(status=MEASURED, result="FITS" if length <= run + DRAWING_TOL_MM else "DOES_NOT_FIT")
        fit.append(row)
    goings = [{"flight": f["flight"], "risers": f["risers"], "goings": f["goings"], "configuration": f["configuration"],
               "basis": f["going_basis"],
               "alternatives": going_alternatives(f["goings"], f["going_mm"]) if f["straight"] else None}
              for f in fl["flights"]]
    lim = _limit(rec, "landing_depth_min_mm")
    landings = []
    for s in rec.get("surfaces") or []:
        if s["kind"] != LANDING:
            continue
        landings.append({"landing": s["id"], "area_m2": None if s.get("polygon") is None else bulge_area(s["polygon"]) / 1e6,
                         "depth_mm": s.get("depth_mm"),
                         "depth_check": (None if lim is None or s.get("depth_mm") is None else
                                         (CODE_NOT_VERIFIED if not lim.get("verified") else
                                          ("MEETS_LIMIT" if s["depth_mm"] >= lim["value"] else "BELOW_LIMIT")))})
    lines = _concrete(rec, fl, lv) + _finishes(rec, fl, lv) + _rails(rec, fl, lv) + _bars(rec)
    for ln in lines:
        ln["stair_id"] = rec.get("stair_id")
    comp = {}
    for ln in lines:
        c = comp.setdefault(ln["component"], {"status": MEASURED, "missing": []})
        if ln["status"] != MEASURED:
            c["status"] = ln["status"] if c["status"] == MEASURED else c["status"]
            c["missing"] += [m for m in ln["missing"] if m not in c["missing"]]
    return {"policy_id": POLICY_ID, "rule": SOURCE, "stair_id": rec.get("stair_id"), "levels": lv, "flights": fl,
            "fit": fit, "goings": goings, "landings": landings, "headroom": _headroom_drawn(rec, fl, lv),
            "findings": _findings(rec, fl, lv), "lines": lines, "components": comp,
            "code": code_applicability(rec.get("building_type")),
            "statuses": {"software": "NOT_ESTABLISHED_HERE (Checker)", "quantity": "NOT_VERIFIED (Checker reconciles "
                         "each quantity against the drawings)", "code": CODE_NOT_VERIFIED}}


# ------------------------------------------------------------------ design scenarios (S-4 C, S-5, S-6, S-9)
def _headroom_intervals(lo, hi, n, h, bottom, overhead, limit):
    """sub-intervals of goings [lo, hi] over which every tread under each overhead member keeps the limit; the
    treads under [a, b] change only where k x g crosses a or b, so the test is exact between those breakpoints."""
    if not overhead:
        return [[lo, hi]], []
    cuts = {lo, hi}
    for o in overhead:
        for edge in (o["s_from_mm"], o["s_to_mm"]):
            for k in range(1, n):
                g = edge / k
                if lo < g < hi:
                    cuts.add(g)
    cuts = sorted(cuts)

    def ok(g):
        worst = None
        for o in overhead:
            a, b = sorted((o["s_from_mm"], o["s_to_mm"]))
            for k in range(1, n):                           # tread k (finished at bottom + k h) spans [(k-1) g, k g]
                if (k - 1) * g < b and k * g > a:
                    c = o["soffit_mm"] - (bottom + k * h)
                    worst = c if worst is None else min(worst, c)
        return worst is None or worst + LEVEL_TOL_MM >= limit, worst
    rows = []
    if len(cuts) == 1:                                       # a single going (fixed run)
        passed, worst = ok(cuts[0])
        rows.append({"going_mm": cuts[0], "min_clear_mm": worst, "meets_limit": passed})
        return ([{"from_mm": cuts[0], "to_mm": cuts[0], "from_closed": True, "to_closed": True}] if passed else []), rows
    good = []
    for a, b in zip(cuts, cuts[1:]):                         # constant tread set inside (a, b): its midpoint decides
        pm, wm = ok((a + b) / 2.0)
        pa, wa = ok(a)
        pb, wb = ok(b)
        rows.append({"piece_mm": [a, b], "min_clear_mm": wm, "meets_limit": pm,
                     "at_ends": [{"going_mm": a, "min_clear_mm": wa, "meets_limit": pa},
                                 {"going_mm": b, "min_clear_mm": wb, "meets_limit": pb}]})
        if pm:
            if good and good[-1]["to_mm"] == a and good[-1]["to_closed"]:
                good[-1].update(to_mm=b, to_closed=pb)
            else:
                good.append({"from_mm": a, "to_mm": b, "from_closed": pa, "to_closed": pb})
        elif pa and not (good and good[-1]["to_mm"] == a):
            good.append({"from_mm": a, "to_mm": a, "from_closed": True, "to_closed": True})
    if ok(cuts[-1])[0] and not (good and good[-1]["to_mm"] == cuts[-1]):
        good.append({"from_mm": cuts[-1], "to_mm": cuts[-1], "from_closed": True, "to_closed": True})
    return good, rows


def alternatives(rise_mm, run_mm, run_type, *, configuration="STRAIGHT", ffl_bottom_mm=0.0, width_mm=None,
                 overhead=None, headroom_limit=None, riser_range=PREF_RISER_MM, going_range=PREF_GOING_MM,
                 show_illustrative=False):
    """design scenarios for a stair the drawings do not define (owner S-4 C): every riser count whose finished riser
    lies in the owner range, its going count from the configuration, the continuous going interval inside the owner
    range that the run admits, headroom sub-intervals, and scenario quantities. Never selected, never measured.

    configuration: only "STRAIGHT" (one flight floor to floor, no landing: every intermediate level is a tread, so
    goings = risers - 1 is demonstrated by the configuration itself). Any other configuration needs drawn landings and
    is UNSUPPORTED here; winders are never generated (S-9)."""
    rep = {"schema": SCENARIO_SCHEMA, "row_kind": "SCENARIO",
           "label": "DESIGN SCENARIOS FOR DESIGNER APPROVAL - NOT MEASURED, NOT SELECTED, NOT FOR THE BOQ",
           "rule": SOURCE, "configuration": configuration, "run_type": run_type, "run_mm": run_mm,
           "rise_mm": rise_mm, "alternatives": [], "status": None}
    if configuration != "STRAIGHT":
        rep["status"] = UNSUPPORTED
        rep["why"] = ("winders are never generated (S-9)" if "WINDER" in str(configuration).upper() else
                      "only a single straight flight is enumerated; landings must come from drawn polygons")
        return rep
    if run_type not in RUN_TYPES:
        raise StairFinishError(f"run type must be one of {RUN_TYPES}")
    counts = SR.counts_in_range(rise_mm, *riser_range)
    lo, hi = going_range
    lim = None if headroom_limit is None else headroom_limit
    for n in counts:
        h = rise_mm / n
        g_n = n - 1
        alt = {"risers": n, "finished_riser_mm": h, "goings": g_n,
               "going_basis": "single straight flight: goings = risers - 1 by this configuration",
               "run_interval_mm": [g_n * lo, g_n * hi], "status": "PROPOSED_FOR_DESIGNER_REVIEW"}
        if run_type == UNKNOWN or run_mm is None:
            alt["feasible"] = None
            alt["going_interval_mm"] = None
            alt["why"] = "RUN_TYPE_UNKNOWN: the drawing does not establish a fixed or a maximum run"
        else:
            need = SF.going_to_fit(run_mm, n)                           # first to last riser line = (n - 1) goings
            if run_type == FIXED:
                ok = lo - 1e-9 <= need <= hi + 1e-9
                alt["going_interval_mm"] = [need, need] if ok else None
            else:
                top = min(hi, need)
                ok = top >= lo - 1e-9
                alt["going_interval_mm"] = [lo, top] if ok else None
                if ok and SF.max_risers(run_mm, lo) < n:
                    raise StairFinishError("fit cross-check failed")
            alt["feasible"] = ok
            if ok and overhead and lim is not None:
                gi, probes = _headroom_intervals(alt["going_interval_mm"][0], alt["going_interval_mm"][1], n, h,
                                                 ffl_bottom_mm, overhead, float(lim["value"]))
                alt["headroom"] = {"limit": lim, "going_intervals_meeting_limit": gi, "probes": probes,
                                   "status": "MEASURED" if lim.get("verified") else CODE_NOT_VERIFIED}
                if lim.get("verified") and not gi:
                    alt["feasible"] = False
                    alt["why"] = "headroom below the verified limit for every going in the interval"
        if width_mm is not None and alt.get("going_interval_mm"):
            a, b = alt["going_interval_mm"]
            alt["scenario_quantities"] = {"tread_m2": [g_n * a * width_mm / 1e6, g_n * b * width_mm / 1e6],
                                          "riser_count": n, "tread_count": g_n,
                                          "note": "scenario range, never a measured quantity"}
        rep["alternatives"].append(alt)
    if not counts:
        rep["status"] = "NO_COUNT_IN_RANGE"
    elif run_type == UNKNOWN or run_mm is None:
        rep["status"] = UNKNOWN
    else:
        rep["status"] = "ALTERNATIVES_LISTED" if any(a["feasible"] for a in rep["alternatives"]) else "NONE_FEASIBLE"
    if show_illustrative:
        rep["illustrative"] = dict(ILLUSTRATIVE)
    rep["selected"] = None
    return rep


# ------------------------------------------------------------------ exports
def measured_rows(result):
    rows = []
    for ln in result["lines"]:
        rows.append({"row_kind": "MEASURED", "stair_id": ln.get("stair_id"), "component": ln["component"],
                     "part": ln["part"], "unit": ln["unit"],
                     "quantity": None if ln["status"] != MEASURED else round(ln["quantity"], 6),
                     "status": ln["status"], "basis": ln["basis"], "missing": "; ".join(ln["missing"])})
    return rows


def export_csv(rows):
    """the measured export: a HELD quantity is an empty cell."""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=EXPORT_COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        if r.get("row_kind") != "MEASURED":
            raise StairFinishError("only measured rows belong to the measured export")
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in EXPORT_COLUMNS})
    return buf.getvalue()


def load_measured_rows(rows):
    """the loader of the measured export: refuses a scenario row or report, a range and a 0 on a HELD row."""
    if isinstance(rows, dict):
        raise StairFinishError("a report is not a list of measured rows")
    out = []
    for r in rows:
        if r.get("row_kind") != "MEASURED" or r.get("schema") == SCENARIO_SCHEMA:
            raise StairFinishError("scenario rows never enter the measured export")
        q = r.get("quantity")
        if isinstance(q, (list, tuple)):
            raise StairFinishError("a range is not a measured quantity")
        if r.get("status") != MEASURED and q not in (None, ""):
            raise StairFinishError("a HELD row carries no quantity")
        out.append(dict(r))
    return out


def scenario_json(report):
    if report.get("schema") != SCENARIO_SCHEMA:
        raise StairFinishError("not a scenario report")
    return json.dumps(report, indent=1, sort_keys=True)


__all__ = ["POLICY_ID", "DEFAULT_GUARD_CLASS", "RULE_ID", "RULE_SET", "PREF_RISER_MM", "PREF_GOING_MM", "ILLUSTRATIVE",
           "FIXED", "MAXIMUM", "UNKNOWN", "MEASURED", "HELD", "UNSUPPORTED", "NOT_SPECIFIED", "CODE_NOT_VERIFIED",
           "FINDINGS", "SCENARIO_SCHEMA", "MEASURED_SCHEMA", "EXPORT_COLUMNS", "NO_CONFLICT_STATEMENT",
           "StairFinishError", "bulge_area", "densify", "triangulate", "overlap_area", "riser_count_exact", "levels",
           "flights", "going_alternatives", "code_applicability", "check_stair", "alternatives", "measured_rows",
           "export_csv", "load_measured_rows", "scenario_json"]
