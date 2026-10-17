"""ARCHITECTURAL RUN AUDIT (Phase 2B-6) - read-only checks of a finished `urban_boq_m9.py arch` run that turn the
known silent failure modes of the room reader into explicit findings, before anyone uses the BOQ.

    python3 tools/arch_run_audit.py --run OUT_DIR [--dxf DRAWING.dxf] [--out RUN_AUDIT.json] [--strict]

It changes nothing: it reads the run's own records (ARCH_PLAN, ARCH_OPENINGS, ARCH_ROOMS, DOOR_SCHEDULE,
BOQ_LINES, DRAWING_DISCOVERY) and, with --dxf, reads the drawing with ezdxf for the two checks the engine keeps no
evidence for (A06, A07). It never writes into the run folder; --strict exits 1 when a HIGH finding is present.

    code  level   what it finds (defect)                                         effect on the BOQ
    A01   HIGH    a layer typed WINDOW that carries door swings with leaves      the swing arcs become room boundaries:
                  (D-P6-02)                                                      floor / ceiling lost, perimeter added
    A02   HIGH    a layer left OTHER with one anchored door swing (D-D1)         its doors read as passages: no door
                                                                                 set, threshold or doorway lines
    A03   MEDIUM  a layer left OTHER with one or two filled / crossed squares    the columns are not deducted
                  (D-D1)
    A04   REVIEW  a COLUMN layer inferred from small filled squares (D-P6-03)    a drain or floor box typed COLUMN is
                                                                                 deducted and its faces finished
    A05   HIGH    door frame evidence spanning far more than the opening         every door held (no door set
                  (D-P6-05: the plan inside one block occurrence)                released)
    A06   HIGH    column-size filled / crossed rectangles the inference cannot   the columns are not deducted (the
                  see - turned off the axes or drawn as four LINEs - on a layer  inference reads axis-aligned closed
                  not typed COLUMN (D-P6-04, D-P6-08)                            polylines only)
    A07   MEDIUM  concentric wall-layer arcs a wall thickness apart (D-D2)       the curved band is missing from
                                                                                 ARCH.WALL_RUN (lengths given)
    A08   INFO    a door whose symbol is narrower than its wall gap,             its width and the lines that use it
                  held for review (D-V26-06)                                     follow the wall gap
    A09   MEDIUM  a space typed wet from wash-basin blocks alone (D-P6-07)       wet scope imposed by a basin, which
                                                                                 the owner says does not make a space
                                                                                 wet: review
    A10   LOW     a zero-length waterproofing termination line (D-P6-06)        a line with no quantity
    A11   MEDIUM  a layer left OTHER whose one to three lines lie inside wall    its windows read as passages
                  gaps (D-D1)
Every finding carries its evidence and the action (usually a --layer-roles declaration). Stdlib only, plus ezdxf for
--dxf."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

SCHEMA = "URBAN_ARCH_RUN_AUDIT_V1"
LEVELS = ("HIGH", "MEDIUM", "REVIEW", "LOW", "INFO")
COLUMN_SIDE_M = (0.15, 1.2)                  # engine.source.arch_plan.COLUMN_SIDE_M
BAND_T_M = (0.10, 0.45)                      # engine.source.arch_plan.BAND_T_M
AXIS_TOL_DEG = 0.5
SINGLE_WINDOW_SHARE = 0.9                    # A11: the share of a 1 - 3 line layer inside wall gaps
FRAME_SPAN_FACTOR = 2.0                      # A05: frame span > factor x opening + 1 m


def _load(run, name):
    p = Path(run) / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _finding(code, level, msg, action, **ev):
    return {"code": code, "level": level, "message": msg, "action": action, "evidence": ev}


def _unit_m(run):
    d = _load(run, "DRAWING_DISCOVERY.json") or {}
    u = ((d.get("stages") or {}).get("4_units") or {}).get("unit_m_used")
    return float(u) if u else 0.001


def _declared(run):
    """the layers the run's --layer-roles declared (RUN_RULES ... layer_roles_override)."""
    def find(o):
        if isinstance(o, dict):
            if isinstance(o.get("layer_roles_override"), dict):
                return o["layer_roles_override"]
            for v in o.values():
                x = find(v)
                if x is not None:
                    return x
        return None
    return set(find(_load(run, "RUN_RULES.json") or {}) or {})


def from_records(run):
    """A01 - A05, A08 - A11: the run's own records. A declared layer is the user's statement: no role finding."""
    out = []
    plan = _load(run, "ARCH_PLAN.json") or {"regions": []}
    declared_layers = _declared(run)
    for r in plan.get("regions", []):
        rid, roles, ev = r.get("region_id"), r.get("layer_roles") or {}, r.get("layer_evidence") or {}
        for lay, e in sorted(ev.items()):
            role = roles.get(lay)
            if lay in declared_layers:
                continue
            if role == "WINDOW" and e.get("swings_with_leaf", 0) >= 1:
                out.append(_finding("A01", "HIGH",
                                    f"layer {lay} is typed WINDOW but carries {e['swings_with_leaf']} door swing(s) "
                                    "with a leaf: the swing arcs are read as glazing and bound the rooms",
                                    f"declare the layer: --layer-roles {lay}=DOOR", region=rid, layer=lay,
                                    swings_with_leaf=e["swings_with_leaf"], anchored_swings=e.get("anchored_swings"),
                                    share_in_wall_gaps=e.get("share_in_wall_gaps")))
            elif role == "OTHER" and e.get("anchored_swings", 0) == 1 and e.get("swings_with_leaf", 0) >= 1:
                out.append(_finding("A02", "HIGH",
                                    f"layer {lay} holds one anchored door swing with its leaf and is not typed DOOR "
                                    "(the inference needs two): its doors read as passages",
                                    f"if {lay} is the door layer: --layer-roles {lay}=DOOR", region=rid, layer=lay,
                                    anchored_swings=1, swings_with_leaf=e["swings_with_leaf"]))
            elif role == "OTHER" and 1 <= e.get("segments", 0) < 4 and e.get("swings", 0) == 0 and \
                    e.get("share_in_wall_gaps", 0) >= SINGLE_WINDOW_SHARE:
                out.append(_finding("A11", "MEDIUM",
                                    f"layer {lay} has {e['segments']} line(s), {e['share_in_wall_gaps']:.0%} of them "
                                    "inside wall gaps, and is not typed WINDOW (the inference needs four lines): its "
                                    "windows read as passages",
                                    f"if {lay} is the glazing layer: --layer-roles {lay}=WINDOW", region=rid,
                                    layer=lay, segments=e["segments"], share_in_wall_gaps=e["share_in_wall_gaps"]))
            elif role == "OTHER" and 1 <= e.get("filled_or_crossed_rects", 0) < 3:
                out.append(_finding("A03", "MEDIUM",
                                    f"layer {lay} holds {e['filled_or_crossed_rects']} filled / crossed column-size "
                                    "square(s) and is not typed COLUMN (the inference needs three): not deducted",
                                    f"if they are columns: --layer-roles {lay}=COLUMN", region=rid, layer=lay,
                                    filled_or_crossed_rects=e["filled_or_crossed_rects"],
                                    small_rects=e.get("small_rects")))
            elif role == "COLUMN":
                out.append(_finding("A04", "REVIEW",
                                    f"layer {lay} was typed COLUMN from {e.get('filled_or_crossed_rects')} small "
                                    "filled / crossed squares: any such square (a drain, a floor box) is deducted as "
                                    "a column and its faces finished",
                                    f"confirm the layer: --layer-roles {lay}=COLUMN, or name it OTHER", region=rid,
                                    layer=lay, filled_or_crossed_rects=e.get("filled_or_crossed_rects"),
                                    small_rects=e.get("small_rects")))
    doors = (_load(run, "DOOR_SCHEDULE.json") or {}).get("doors") or {}
    wide = [f for f in doors.get("findings") or [] if f.get("code") == "DOOR_CLOSURE_FRAME_DISAGREE"
            and f.get("frame_m") is not None and f.get("opening_m")
            and f["frame_m"] > FRAME_SPAN_FACTOR * f["opening_m"] + 1.0]
    if wide:
        out.append(_finding("A05", "HIGH",
                            f"{len(wide)} door(s) whose frame evidence spans far beyond the opening (up to "
                            f"{max(f['frame_m'] for f in wide):.2f} m): the door symbols are read across one block "
                            "occurrence (the plan drawn inside a block?) and the doors are held",
                            "explode or unnest the plan block, or review the held doors one by one",
                            doors=[{"element_id": f.get("element_id"), "opening_m": f["opening_m"],
                                    "frame_m": f["frame_m"]} for f in wide]))
    for o in (_load(run, "ARCH_OPENINGS.json") or {}).get("openings") or []:
        if o.get("door_fit_review"):
            out.append(_finding("A08", "INFO", o["door_fit_review"],
                                "the width (and the threshold, reveal, plaster, tile, skirting and doorway "
                                "waterproofing lines) follow the wall gap until the door is reviewed",
                                opening_id=o.get("opening_id"), floor=o.get("floor"), width_m=o.get("width_m")))
    for r in (_load(run, "ARCH_ROOMS.json") or {}).get("rooms") or []:
        fx = (r.get("evidence") or {}).get("fixtures") or []
        if r.get("label_source") == "FIXTURES" and fx and {x.get("fixture") for x in fx} == {"BASIN"}:
            out.append(_finding("A09", "MEDIUM",
                                f"{r.get('room_id')} ({r.get('area_m2')} m2) has no room word and was typed "
                                f"{r.get('name_en')} from wash-basin block(s) alone",
                                "a basin alone does not make a space wet (owner statement): review the room type; "
                                "its wet scope is not established by the drawing",
                                room_id=r.get("room_id"), floor=r.get("floor"), area_m2=r.get("area_m2"),
                                blocks=sorted({x.get("block") for x in fx}),
                                fixture_layers=[x.get("layer") for x in (r.get("evidence") or {}).get("fixture_layers")
                                                or []]))
    zero = [ln for ln in _load(run, "BOQ_LINES.json") or []
            if ln.get("item_code") == "FIN.WP.TERMINATION"
            and ((ln.get("calculation") or {}).get("inputs") or {}).get("length_m") == 0.0]
    if zero:
        out.append(_finding("A10", "LOW", f"{len(zero)} waterproofing termination line(s) of zero length",
                            "ignore: a sliver edge of the room ring, no quantity",
                            line_ids=[ln.get("line_id") for ln in zero]))
    return out


def _raw(dxf):
    """(segments, arcs, hatches, closed rings) per layer from the drawing, inserts exploded (depth 4); layer-0 block
    contents take the insert's layer."""
    import ezdxf
    from ezdxf.math import bulge_to_arc
    doc = ezdxf.readfile(str(dxf))
    segs, arcs, hatches, rings = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)

    def visit(e, parent=None, depth=0):
        t = e.dxftype()
        L = e.dxf.layer if e.dxf.hasattr("layer") else "0"
        if L == "0" and parent:
            L = parent
        if t == "INSERT":
            if depth < 4:
                for v in e.virtual_entities():
                    visit(v, L, depth + 1)
            return
        if t == "LINE":
            segs[L].append(((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)))
        elif t == "ARC":
            c, a0, a1 = (e.dxf.center.x, e.dxf.center.y), math.radians(e.dxf.start_angle), math.radians(e.dxf.end_angle)
            if e.dxf.extrusion.z < 0:
                c, a0, a1 = (-c[0], c[1]), math.pi - a1, math.pi - a0
            arcs[L].append((c, e.dxf.radius, a0, a1 if a1 > a0 else a1 + 2 * math.pi))
        elif t == "LWPOLYLINE":
            pts = list(e.get_points("xyb"))
            n = len(pts)
            closed = e.closed or (n > 2 and math.dist(pts[0][:2], pts[-1][:2]) < 1e-9)
            if closed and all(abs(p[2]) < 1e-12 for p in pts):
                ring = [p[:2] for p in pts]
                if len(ring) > 3 and math.dist(ring[0], ring[-1]) < 1e-9:
                    ring = ring[:-1]
                rings[L].append(ring)
            for i in range(n if e.closed else n - 1):
                (x0, y0, b), (x1, y1, _) = pts[i], pts[(i + 1) % n]
                if abs(b) > 1e-12:
                    c, sa, ea, r = bulge_to_arc((x0, y0), (x1, y1), b)
                    arcs[L].append(((c.x, c.y), r, sa, ea if ea > sa else ea + 2 * math.pi))
                else:
                    segs[L].append(((x0, y0), (x1, y1)))
        elif t == "HATCH":
            for p in e.paths:
                if hasattr(p, "vertices") and len(p.vertices) >= 3:
                    hatches[L].append([(v[0], v[1]) for v in p.vertices])

    for e in doc.modelspace():
        visit(e)
    return segs, arcs, hatches, rings


def _line_rings(ss, tol):
    """closed four-segment loops (four LINEs end to end)."""
    key = lambda p: (round(p[0] / tol), round(p[1] / tol))        # noqa: E731
    at = defaultdict(list)
    for i, (a, b) in enumerate(ss):
        at[key(a)].append((i, b))
        at[key(b)].append((i, a))
    out, seen = [], set()
    for i, (a, b) in enumerate(ss):
        for j, c in at[key(b)]:
            for k, d in at[key(c)] if j != i else ():
                for m, e in at[key(d)] if k not in (i, j) else ():
                    if m in (i, j, k) or key(e) != key(a):
                        continue
                    ids = frozenset((i, j, k, m))
                    if ids not in seen:
                        seen.add(ids)
                        out.append([a, b, c, d])
    return out


def _inside(p, ring, tol):
    """point in a convex ring, within tol."""
    sgn = 0
    for i in range(len(ring)):
        (x0, y0), (x1, y1) = ring[i], ring[(i + 1) % len(ring)]
        L = math.hypot(x1 - x0, y1 - y0)
        c = ((x1 - x0) * (p[1] - y0) - (y1 - y0) * (p[0] - x0)) / L if L else 0.0
        if abs(c) <= tol:
            continue
        if sgn == 0:
            sgn = 1 if c > 0 else -1
        elif (c > 0) != (sgn > 0):
            return False
    return True


def _rect_shape(ring, u):
    """-> (w_m, h_m, angle_deg off the axes) for a right-angled quadrilateral, else None."""
    if len(ring) != 4:
        return None
    for i in range(4):
        p0, p1, p2 = ring[i - 1], ring[i], ring[(i + 1) % 4]
        v1, v2 = (p0[0] - p1[0], p0[1] - p1[1]), (p2[0] - p1[0], p2[1] - p1[1])
        n1, n2 = math.hypot(*v1), math.hypot(*v2)
        if n1 <= 0 or n2 <= 0 or abs(v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2) > math.sin(math.radians(1.0)):
            return None
    w, h = math.dist(ring[0], ring[1]) * u, math.dist(ring[1], ring[2]) * u
    a = math.degrees(math.atan2(ring[1][1] - ring[0][1], ring[1][0] - ring[0][0])) % 90.0
    return w, h, min(a, 90.0 - a)


def from_drawing(run, dxf):
    """A06 (turned column squares) and A07 (curved wall bands), read from the drawing with ezdxf."""
    u = _unit_m(run)
    plan = _load(run, "ARCH_PLAN.json") or {"regions": []}
    boxes = [(r.get("region_id"), r.get("box"), r.get("layer_roles") or {}) for r in plan.get("regions", [])]
    segs, arcs, hatches, rings = _raw(dxf)
    tol = 0.002 / u

    def region_of(p):
        for rid, b, roles in boxes:
            if b and b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]:
                return rid, roles
        return None, {}
    out = []
    turned = defaultdict(list)
    for lay in sorted(set(segs) | set(rings)):
        cand, centres = [], []
        for src, ring in [("POLYLINE", r_) for r_ in rings.get(lay, [])] + \
                [("LINES", r_) for r_ in _line_rings(segs.get(lay, []), tol)]:
            c = (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))
            if any(math.dist(c, q) < tol for q in centres):      # a polyline's own sides found again as LINEs
                continue
            centres.append(c)
            cand.append((src, ring))
        for src, ring in cand:
            sh = _rect_shape(ring, u)
            # the inference sees only axis-aligned rectangles drawn as one closed polyline
            if not sh or (sh[2] <= AXIS_TOL_DEG and src == "POLYLINE"):
                continue
            w, h, ang = sh
            if not (COLUMN_SIDE_M[0] <= w <= COLUMN_SIDE_M[1] and COLUMN_SIDE_M[0] <= h <= COLUMN_SIDE_M[1]):
                continue
            filled = any(all(_inside(p, ring, tol * 10) for p in hp) for hp in hatches.get(lay, []))

            def _edge(a, b):
                ia = next((i for i, q in enumerate(ring) if math.dist(a, q) < tol), None)
                ib = next((i for i, q in enumerate(ring) if math.dist(b, q) < tol), None)
                return ia is not None and ib is not None and (ia - ib) % 4 in (1, 3)
            crossed = any(_inside(a, ring, tol) and _inside(b, ring, tol) and math.dist(a, b) * u >= 0.5 * min(w, h)
                          and not _edge(a, b) for a, b in segs.get(lay, []))
            if not (filled or crossed):
                continue
            c = (sum(p[0] for p in ring) / 4, sum(p[1] for p in ring) / 4)
            rid, roles = region_of(c)
            if rid is None or roles.get(lay) == "COLUMN":
                continue
            turned[(rid, lay)].append({"w_m": round(w, 4), "h_m": round(h, 4), "angle_deg": round(ang, 3),
                                       "drawn_as": src})
    for (rid, lay), xs in sorted(turned.items()):
        out.append(_finding("A06", "HIGH",
                            f"layer {lay} holds {len(xs)} filled / crossed column-size rectangle(s) the role "
                            "inference cannot see (turned off the drawing axes, or drawn as four separate lines) and "
                            "is not typed COLUMN: if they are columns, they are not deducted",
                            f"if they are columns: --layer-roles {lay}=COLUMN", region=rid, layer=lay,
                            rectangles=xs[:20]))
    for rid, b, roles in boxes:
        for lay in sorted(l for l, r in roles.items() if r == "WALL"):
            A = [a for a in arcs.get(lay, []) if b and b[0] <= a[0][0] <= b[2] and b[1] <= a[0][1] <= b[3]]
            pairs, used = [], set()
            cands = []
            for i, a in enumerate(A):
                for j, c in enumerate(A):
                    if j <= i or math.dist(a[0], c[0]) > tol:
                        continue
                    t = abs(a[1] - c[1]) * u
                    if not BAND_T_M[0] <= t <= BAND_T_M[1]:
                        continue
                    best = 0.0
                    for k in (-1, 0, 1):
                        best = max(best, min(a[3], c[3] + 2 * math.pi * k) - max(a[2], c[2] + 2 * math.pi * k))
                    if best * min(a[1], c[1]) * u >= 0.3:
                        cands.append((t, i, j, best))
            for t, i, j, th in sorted(cands):
                if i in used or j in used:
                    continue
                used |= {i, j}
                r1, r2 = sorted((A[i][1], A[j][1]))
                pairs.append({"t_m": round(t, 4), "sweep_deg": round(math.degrees(th), 3),
                              "MIN_RADIUS_ARC_lm": round(r1 * th * u, 6),
                              "MID_BAND_ARC_lm": round((r1 + r2) / 2 * th * u, 6),
                              "MAX_RADIUS_ARC_lm": round(r2 * th * u, 6),
                              "strip_m2": round(th * (r2 ** 2 - r1 ** 2) / 2 * u * u, 6)})
            if pairs:
                out.append(_finding("A07", "MEDIUM",
                                    f"{len(pairs)} curved wall band(s) on layer {lay} (concentric arcs a wall "
                                    "thickness apart) are not in ARCH.WALL_RUN: "
                                    f"{sum(p['MID_BAND_ARC_lm'] for p in pairs):.3f} m on the mean radius",
                                    "add the curved run by hand until the method measures it (the mean-radius length "
                                    "keeps run x thickness = the band's plan area)", region=rid, layer=lay,
                                    bands=pairs))
    return out


def audit(run, dxf=None):
    findings = from_records(run) + (from_drawing(run, dxf) if dxf else [])
    findings.sort(key=lambda f: (LEVELS.index(f["level"]), f["code"]))
    by = defaultdict(int)
    for f in findings:
        by[f["level"]] += 1
    roles = sorted({f["action"].split("--layer-roles ", 1)[1].split()[0] for f in findings
                    if "--layer-roles " in f["action"] and f["code"] in ("A01", "A02", "A06")})
    return {"schema": SCHEMA, "run": str(Path(run).name), "drawing_read": bool(dxf),
            "summary": {lv: by.get(lv, 0) for lv in LEVELS}, "suggested_layer_roles": roles,
            "findings": findings,
            "never": ["a quantity changed", "a file written into the run folder", "a role applied without the user"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True, help="an urban_boq_m9.py arch output folder")
    ap.add_argument("--dxf", help="the drawing of that run (for A06 / A07)")
    ap.add_argument("--out", help="write the audit JSON here (default: stdout)")
    ap.add_argument("--strict", action="store_true", help="exit 1 when a HIGH finding is present")
    a = ap.parse_args(argv)
    if not (Path(a.run) / "ARCH_PLAN.json").exists():
        print(f"not an architectural run folder: {a.run}", file=sys.stderr)
        return 2
    if a.out and Path(a.out).resolve().parent == Path(a.run).resolve():
        print("refused: the audit is never written into the run folder", file=sys.stderr)
        return 2
    rep = audit(a.run, a.dxf)
    text = json.dumps(rep, indent=1, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 1 if a.strict and rep["summary"]["HIGH"] else 0


if __name__ == "__main__":
    sys.exit(main())
