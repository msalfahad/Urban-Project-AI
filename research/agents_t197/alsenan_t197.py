"""T-197 (residential review R4) on the development villa: curved and partial geometry completeness.

Two steps:
  extract  python -I alsenan_t197.py extract <P7757.dxf> <ST7757.dxf>   (project venv; private DXFs from Drive,
           decoded into .work/private only). Reads the curved entities of the four known elements BY HANDLE and writes
           ALSENAN_T197_INPUT.json: geometry RELATIVE to each element's own arc centre, in metres (no absolute
           coordinate, no drawing content beyond radii, sweeps and the straight pieces that close each outline).
  run      python3 -I alsenan_t197.py [--check]   (standard library + the engine check module): runs
           CURVED_GEOMETRY_CHECK_V1 on the committed input for each BOQ scenario and writes LINES_T197.csv,
           ISSUES_T197.csv, ELEMENTS_T197.json, summary.json; --check re-runs and compares byte for byte.

The ledger / candidate lines below are the values the merged ledgers and the candidate print (cited per line); the
check names the basis each value actually is. It moves no quantity.
"""

from __future__ import annotations

import csv
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INPUT = HERE / "ALSENAN_T197_INPUT.json"

# ------------------------------------------------------------------------------------------------------ extract
P_HANDLES = {"W17_OUTER": "BD2", "W17_INNER": "BCE",
             "R11": ["ACE", "B6B", "BD1", "BD2", "BD6", "C0A", "C16", "C10", "C0F", "B1C", "B1D", "B0B", "C0B",
                     "C15", "C09", "B0D"]}
S_HANDLES = {"POOL_OUTER": "7C6", "POOL_INNER": "7C5", "RING_INNER": ["5FE", "5FF"],
             "RING_OUTER": ["600", "601", "602", "603"]}


def _r6(v):
    return round(float(v), 7)


def extract(p_path, s_path):
    import ezdxf
    P = ezdxf.readfile(p_path)
    S = ezdxf.readfile(s_path)
    mm = 0.001

    def arc(e, origin, pid, role):
        c = e.dxf.center
        assert abs(e.dxf.extrusion.z - 1.0) < 1e-12
        return {"piece_id": pid, "role": role, "centre": [_r6((c.x - origin[0]) * mm), _r6((c.y - origin[1]) * mm)],
                "radius": _r6(e.dxf.radius * mm), "start_angle": _r6(e.dxf.start_angle),
                "end_angle": _r6(e.dxf.end_angle), "handle": e.dxf.handle, "layer": e.dxf.layer}

    def rel(p, origin):
        return [_r6((p[0] - origin[0]) * mm), _r6((p[1] - origin[1]) * mm)]

    out = {"SCHEMA": "T197_ALSENAN_INPUT_V1",
           "source": "Drive 'Alsenan chalet project': P7757_DXF_COMPRESSED.zip / P7757.dxf (sha256 ab54dd55...), "
                     "'ST7757 dxf.dxf' (sha256 9f9d1179...); entities read by handle; coordinates relative to each "
                     "element's arc centre, metres",
           "elements": []}

    # W17 (1F, P7757): outer glazing arc layer W r 2.135, wall-face arc layer 5 r 1.935 (T-194 PLAN_T194.csv)
    o, i = P.entitydb[P_HANDLES["W17_OUTER"]], P.entitydb[P_HANDLES["W17_INNER"]]
    origin = (o.dxf.center.x, o.dxf.center.y)
    out["elements"].append({"element_id": "W17", "kind": "OPENING", "units": "m",
                            "ref": "P7757.dxf 1F plan: ARC BD2 (layer W, r 2135) outer glazing arc; ARC BCE (layer 5, "
                                   "r 1935) wall-face arc between the jamb ends (T-194)",
                            "pieces": [arc(o, origin, "BD2", "OUTER"), arc(i, origin, "BCE", "INNER")]})

    # 1F-11 room contour (P7757): the Checker's 16:11 verified polygon (T-128 r3 verdict), entities by handle, two
    # door gaps closed by virtual GAP lines (D-1F-10 0.80 east of the entry, the entry door 0.90 south)
    pcs = []
    for h in P_HANDLES["R11"]:
        e = P.entitydb[h]
        if e.dxftype() == "LINE":
            pcs.append({"piece_id": h, "role": "FACE", "line": [rel(e.dxf.start, origin), rel(e.dxf.end, origin)],
                        "layer": e.dxf.layer})
        else:
            pcs.append(arc(e, origin, h, "FACE"))
    gaps = [("GAP-E", P.entitydb["C10"].dxf.start, P.entitydb["C0F"].dxf.end),
            ("GAP-S", P.entitydb["B1C"].dxf.end, P.entitydb["B1D"].dxf.start)]
    for gid, a, b in gaps:
        pcs.append({"piece_id": gid, "role": "GAP", "line": [rel(a, origin), rel(b, origin)], "layer": None})
    out["elements"].append({"element_id": "1F-11", "kind": "ROOM_CONTOUR", "units": "m",
                            "ref": "P7757.dxf 1F plan: east master bed room + entry, layer 1 / W faces by handle "
                                   "(Checker T-128 r3 verdict 2026-10-22 18:05), door gaps virtual",
                            "pieces": pcs, "loops": [{"pieces": [p["piece_id"] for p in pcs]}]})

    # Pool (ST, layer S-BW): outer D 7C6 (closed), water D 7C5 (open, last vertex = first)
    po, pi = S.entitydb[S_HANDLES["POOL_OUTER"]], S.entitydb[S_HANDLES["POOL_INNER"]]
    vo = list(po.get_points("xyb"))
    k = [j for j, v in enumerate(vo) if abs(v[2]) > 1e-9][0]
    ax, ay = vo[k][0], vo[k][1]
    bx, by = vo[(k + 1) % len(vo)][0], vo[(k + 1) % len(vo)][1]
    origin = ((ax + bx) / 2.0, (ay + by) / 2.0)          # a semicircle span: its centre is the chord midpoint
    assert abs(abs(vo[k][2]) - 1.0) < 1e-9
    from engine.source.curved_geometry_check_v1 import pieces_from_polyline
    outer = pieces_from_polyline("7C6", "OUTER", [(_r6((x - origin[0]) * mm), _r6((y - origin[1]) * mm), _r6(b))
                                                  for x, y, b in vo], closed=True)
    vi = list(pi.get_points("xyb"))
    inner = pieces_from_polyline("7C5", "INNER", [(_r6((x - origin[0]) * mm), _r6((y - origin[1]) * mm), _r6(b))
                                                  for x, y, b in vi], closed=bool(pi.closed))
    for p in outer + inner:
        p["layer"] = "S-BW"
    out["elements"].append({"element_id": "POOL-GF-WALL", "kind": "POOL_WALL", "units": "m",
                            "ref": "ST7757 dxf.dxf ground beams plan, layer S-BW: LWPOLYLINE 7C6 (outer D), 7C5 "
                                   "(water D); walls 20 (ST p.7)",
                            "pieces": outer + inner,
                            "loops": [{"pieces": [p["piece_id"] for p in outer]},
                                      {"pieces": [p["piece_id"] for p in inner], "hole": True}]})
    out["elements"].append({"element_id": "POOL-GF-BASE", "kind": "POOL_WALL", "units": "m",
                            "ref": "ST7757 dxf.dxf layer S-BW: LWPOLYLINE 7C6 (outer D = base footprint, T-183 r2)",
                            "pieces": [dict(p, piece_id="B" + p["piece_id"]) for p in outer],
                            "loops": [{"pieces": ["B" + p["piece_id"] for p in outer]}]})

    # West dome ring (ST p.5 first-floor roof slab): outer arcs 600..603 (drawn only between the framing faces),
    # inner arcs 5FE / 5FF (broken at the CB10 / CB13 faces, tangent to the B6 faces at 90 / 270 deg).
    ri = [S.entitydb[h] for h in S_HANDLES["RING_INNER"]]
    ro = [S.entitydb[h] for h in S_HANDLES["RING_OUTER"]]
    c = ri[0].dxf.center
    origin = (c.x, c.y)
    rin, rout = ri[0].dxf.radius * mm, ro[0].dxf.radius * mm
    inner_parts = {"NE": (ri[0], ri[0].dxf.start_angle, 90.0), "NW": (ri[0], 90.0, ri[0].dxf.end_angle),
                   "SW": (ri[1], ri[1].dxf.start_angle, 270.0), "SE": (ri[1], 270.0, ri[1].dxf.end_angle)}
    quad = {"600": "NE", "601": "NW", "602": "SW", "603": "SE"}

    def pt(r, deg):
        return [_r6(r * math.cos(math.radians(deg))), _r6(r * math.sin(math.radians(deg)))]

    ring_pieces, ring_loops = [], []
    for e in ro:
        q = quad[e.dxf.handle]
        src, a0, a1 = inner_parts[q]
        op = arc(e, origin, f"O{q}", "OUTER")
        ip = {"piece_id": f"I{q}", "role": "INNER", "centre": [0.0, 0.0], "radius": _r6(rin), "start_angle": _r6(a0),
              "end_angle": _r6(a1), "handle": src.dxf.handle, "layer": src.dxf.layer}
        f0 = {"piece_id": f"F{q}0", "role": "FACE", "line": [pt(rout, e.dxf.start_angle), pt(rin, a0)]}
        f1 = {"piece_id": f"F{q}1", "role": "FACE", "line": [pt(rout, e.dxf.end_angle), pt(rin, a1)]}
        ring_pieces += [op, ip, f0, f1]
        ring_loops.append({"pieces": [op["piece_id"], f1["piece_id"], ip["piece_id"], f0["piece_id"]]})
        # the route band over the same outer arc: the annular sector under it (identified by area, T-179 s.5.1)
        bp = [dict(op, piece_id="o"),
              {"piece_id": "r1", "role": "FACE", "line": [pt(rout, e.dxf.end_angle), pt(rin, e.dxf.end_angle)]},
              {"piece_id": "i", "role": "INNER", "centre": [0.0, 0.0], "radius": _r6(rin),
               "start_angle": _r6(e.dxf.start_angle), "end_angle": _r6(e.dxf.end_angle), "handle": None,
               "layer": None},
              {"piece_id": "r0", "role": "FACE", "line": [pt(rout, e.dxf.start_angle), pt(rin, e.dxf.start_angle)]}]
        out["elements"].append({"element_id": f"DOME-1F-W-BAND-{q}", "kind": "RING", "units": "m",
                                "ref": f"route G 1F slab overlay arc band under ARC {e.dxf.handle} (one of "
                                       "BAND0033..0036; identified by its sector area, T-179 s.5.1)",
                                "pieces": bp, "loops": [{"pieces": ["o", "r1", "i", "r0"]}]})
    out["elements"].append({"element_id": "DOME-1F-W-RING", "kind": "RING", "units": "m",
                            "ref": "ST7757 dxf.dxf p.5: ARC 600..603 (r 2411.09, outer, drawn between the framing "
                                   "faces), ARC 5FE / 5FF (r 2211.09, inner); in-bay ring = 4 pieces between the faces "
                                   "(T-160, BM-1F-028 B4 20 x 50)",
                            "pieces": ring_pieces, "loops": ring_loops, "expected_families": ["CONC.BEAM"]})
    INPUT.write_text(json.dumps(out, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    return 0


# ------------------------------------------------------------------------------------------------------ lines
def L(lid, eid, family, measure, value, basis=None, ref="", **kw):
    d = {"line_id": lid, "element_id": eid, "family": family, "measure": measure, "value": value, "units": "m",
         "basis": basis, "ref": ref}
    d.update(kw)
    return d


BANDS = [("NE", 0.2588), ("NW", 0.3034), ("SW", 0.3034), ("SE", 0.2588)]   # plan m2 (= m3 / 0.50)


def scenarios():
    """Each scenario is one BOQ (or one ledger set): lines are only compared for double counting inside it."""
    pool_rel = [
        L("REL:POOL-WALL-BAND", "POOL-GF-WALL", "CONC.POOL", "PLAN_AREA", 1.240,
          ref="engine A pool walls 1.240 m2 x convention 1.60 = 1.984 m3 (T-183 s.7, T-180)"),
        L("REL:POOL-BASE", "POOL-GF-BASE", "CONC.POOL_BASE", "PLAN_AREA", 6.045,
          ref="engine A pool floor 6.045 m2 x convention 0.25 (T-180 Checker; ERS s.7 default-guard row)")]
    w17_rel = [L("REL:W17-COP-001", "W17", "OPENING_SUPPLY", "LENGTH", 3.2895, "OUTER_ARC",
                 ref="ARCH_TAKEOFF_V2.9 COP-001 width (owner Q-39 C; T-194 PLAN_T194.csv)")]
    dome_route = [L(f"REL:BAND-{q}", f"DOME-1F-W-BAND-{q}", "CONC.BEAM", "PLAN_AREA", a, "TRUE_AREA",
                    ref="route G 1F slab arc band (BAND0033..0036, T-179 s.5.1)") for q, a in BANDS]
    ring = L("CAND:DOME-RING-W", "DOME-1F-W-RING", "CONC.BEAM", "PLAN_AREA", 1.5105, "TRUE_AREA",
             ref="T-160 in-bay ring 1.5105 m2 x 0.50 = 0.7552 m3 VERIFIED (BM-1F-028)")
    out = {
        "RELEASED_V29_ROUTEG": pool_rel + w17_rel + dome_route,
        "CANDIDATE_V304_PLUS_RING": [dict(x, line_id=x["line_id"].replace("REL:", "C304:")) for x in
                                     pool_rel + w17_rel + dome_route] + [ring],
        "CANDIDATE_V305": [dict(x, line_id=x["line_id"].replace("REL:", "C305:")) for x in pool_rel + w17_rel]
                          + [dict(x, line_id=x["line_id"].replace("REL:", "C305:"), status="SUPERSEDED")
                             for x in dome_route] + [ring],
        "LEDGERS_MERGED": [
            L("T183:WALL-BAND", "POOL-GF-WALL", "T183:CONC.POOL", "PLAN_AREA", 2.356726, "TRUE_AREA",
              ref="T-183 r2 wall band 2.356726 m2 x 1.20 = 2.828 m3 VERIFIED"),
            L("T183:WALL-AXIS", "POOL-GF-WALL", "T183:AXIS", "LENGTH", 11.784, "CENTRELINE_ARC",
              ref="T-183 r2 wall centreline 11.784 m"),
            L("T183:FORM-OUT", "POOL-GF-WALL", "T183:FORM_OUT", "LENGTH", 12.497787, "OUTER_ARC",
              ref="T-183 r2 outer face formwork perimeter"),
            L("T183:FORM-WATER", "POOL-GF-WALL", "T183:FORM_IN", "LENGTH", 11.069469, "INNER_ARC",
              ref="T-183 r2 water face perimeter"),
            L("T183:BASE", "POOL-GF-BASE", "T183:CONC.POOL_BASE", "PLAN_AREA", 10.935564, "TRUE_AREA",
              ref="T-183 r2 base 10.936 m2 x 0.40 = 4.374 m3 VERIFIED"),
            L("T150:W17", "W17", "T150:OPENING_LIST", "LENGTH", 3.29, "OUTER_ARC",
              ref="T-150 OPENINGS_T150.csv W17 3.29 'outer arc (owner Q-39 C)'"),
            L("T159:W17-DEDUCT", "W17", "T159:FACADE_OPENING", "LENGTH", 2.977,
              ref="T-159 FACADE_SIDES_T159.csv NW-2 'COP-001 2.977' (no basis word)"),
            L("T175:W17-SILL", "W17", "T175:SILL", "LENGTH", 3.290,
              ref="T-175 T175_OPENING_CONSEQUENCES.csv W17 SILL 3.290 (no basis column)"),
            L("T194:W17-NW-CHORD", "W17", "T194:ELEVATION_ID", "LENGTH", 2.6915, "PROJECTED_CHORD",
              chord_role="INNER", purpose="IDENTITY",
              ref="T-194 NW elevation DIMENSION 2691.5 (printed '269') = chord of the r 1.935 face"),
            L("T128R2:1F-11", "1F-11", "T128R2:CONTOUR", "LENGTH", 22.350,
              ref="T-128 r2 walked contour 22.350 m (region tool, superseded by r3)"),
            L("T128R3:1F-11", "1F-11", "T128R3:CONTOUR", "LENGTH", 22.149, "FACE_ARC",
              ref="T-128 r3 contour 22.149 m on the drawn faces")],
        "FREELANCER_INFORMATION": [
            L("FL:W17", "W17", "FL:OPENING", "LENGTH", 3.15, purpose="IDENTITY",
              ref="freelancer aluminium sheet, 1F pool-side window 3.15 x 3.00 (T-175 map)")],
    }
    return out


# ------------------------------------------------------------------------------------------------------ run
def _csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in cols})
    return buf.getvalue()


def build():
    from engine.source import curved_geometry_check_v1 as CG
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    els = [{k: v for k, v in e.items()} for e in data["elements"]]
    for e in els:
        e["pieces"] = [{k: v for k, v in p.items() if k not in ("handle", "layer")} for p in e["pieces"]]
    lines_rows, issue_rows, summary, elements = [], [], {}, None
    for name, lines in scenarios().items():
        boq = name.startswith(("RELEASED", "CANDIDATE"))       # element coverage is a BOQ question, not a ledger's
        res = CG.check([e if boq else {k: v for k, v in e.items() if k != "expected_families"} for e in els], lines)
        elements = res["elements"]
        for r in res["lines"]:
            lines_rows.append(dict(r, scenario=name, matches=";".join(r["matches"]), codes=";".join(r["codes"]),
                                   ref=next(x["ref"] for x in lines if x["line_id"] == r["line_id"])))
        for it in res["issues"]:
            issue_rows.append(dict(it, scenario=name))
        summary[name] = res["summary"]
    files = {
        "LINES_T197.csv": _csv(lines_rows, ["scenario", "line_id", "element_id", "family", "measure", "status",
                                            "purpose", "basis", "value", "deductions", "expected", "matches",
                                            "codes", "ref"]),
        "ISSUES_T197.csv": _csv(issue_rows, ["scenario", "id", "code", "element_id", "line_ids", "detail"]),
        "ELEMENTS_T197.json": json.dumps(elements, indent=1, sort_keys=True) + "\n",
        "summary.json": json.dumps({"method": "CURVED_GEOMETRY_CHECK_V1", "input": INPUT.name,
                                    "issues_by_scenario": summary}, indent=1, sort_keys=True) + "\n"}
    return files


def main(argv):
    if argv and argv[0] == "extract":
        return extract(argv[1], argv[2])
    files = build()
    if argv and argv[0] == "--check":
        bad = [n for n, t in files.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("T-197 check:", "PASS" if not bad else f"FAIL {bad}")
        return 1 if bad else 0
    for n, t in files.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print("written:", ", ".join(files))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
