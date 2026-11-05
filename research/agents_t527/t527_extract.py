"""T-527 drawing reader (research only, NOT engine code): every lintel end of the T-516 census re-measured under
LINTEL_BEARING_V1 (T-516, reproduced as a control), V2 (T-519, its first DXF run) and V3 (this task: curved bays read from
the drawn face arcs). Masonry, columns and gaps are the T-516 construction (research/agents_t516/t516_extract.storey,
imported read-only); V3 changes only the curved-bay stretches.

Inputs (outside the repository, never committed): <scratch>/t125_inputs.pkl and <scratch>/t125_v2.json (the merged
research/agents_t125 capture of Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf, sha ab54dd55).
Outputs: NUMBERS ONLY (lengths along a wall from a jamb or from the wall's own start, radii, ids; no drawing coordinate).
Run by tests/t527_lintel_bearing_v3/test_dxf_rerun.py, which writes only into <checkout>/.work/private/t527.
"""
from __future__ import annotations

import csv
import json
import math
import pickle
import sys
from pathlib import Path

from shapely.geometry import LineString, Point

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "agents_t516"))
sys.path.insert(0, str(HERE.parent / "agents_t519"))
import lintel_bearing_v2 as V2  # noqa: E402  (read only)
import lintel_bearing_v3 as V3  # noqa: E402
import t516_extract as X1  # noqa: E402  (read only: CASES, CENSUS_OF, storey, reach, flat_of)

OUT = HERE / "out" / "JAMB_EVIDENCE_V3_T527.csv"
BAYS_NAME = "CURVED_BAYS_T527.csv"
BAY_KEYS = ["storey", "band", "wall_t_m", "status", "chord_from_m", "chord_to_m", "r_in_m", "r_out_m", "window_arcs",
            "face_minus_cross_m", "face_plus_cross_m", "drawn_open_from_m", "drawn_open_to_m",
            "chord_from_minus_drawn_m", "drawn_to_minus_chord_m", "face_minus_line_end_mm", "face_plus_line_end_mm",
            "why"]


def mm3(x):
    return f"{math.floor(x * 1000 + 1e-9) / 1000:.3f}"


def arcs_of(F):
    """the storey's arcs in metres with their layer role and CCW start / end angles."""
    u = F["unit_m"]
    roles = F["roles"]
    out = []
    for e in F["ents"].get("arcs") or ():
        if "s" not in e or "e" not in e:
            continue
        c = (e["c"][0] * u, e["c"][1] * u)
        p0 = (e["s"][0] * u, e["s"][1] * u)
        p1 = (e["e"][0] * u, e["e"][1] * u)
        a0 = math.atan2(p0[1] - c[1], p0[0] - c[0])
        a1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
        if str(e.get("dir", "CCW")).upper() == "CW":
            a0, a1 = a1, a0
        out.append({"c": c, "r": e["r"] * u, "role": roles.get(e.get("layer"), "OTHER"), "a0": a0, "a1": a1})
    return out


def face_line_ends(F, a, ux, uy, n_face, crossings, tol=0.0005):
    """distance (mm) from each inner-arc crossing of one band face to the nearest end of a WALL-role line drawn ON that
    face (parallel, within 0.5 mm of the face); 'none' when no drawn face line ends within 5 mm: the drawn evidence that
    the masonry face stops at the arc."""
    u = F["unit_m"]
    ends = []
    for e in F["ents"].get("segments") or ():
        if F["roles"].get(e.get("layer")) != "WALL" or e.get("a") is None or e.get("b") is None:
            continue
        pts = [((p[0] * u - a[0]) * ux + (p[1] * u - a[1]) * uy, -(p[0] * u - a[0]) * uy + (p[1] * u - a[1]) * ux)
               for p in (e["a"], e["b"])]
        if all(abs(n - n_face) <= tol for _s, n in pts):
            ends += [s_ for s_, _n in pts]
    out = []
    for x in crossings:
        d = min((abs(s_ - x) for s_ in ends), default=None)
        out.append("none" if d is None or d > 0.005 else f"{d * 1000:.1f}")
    return ";".join(out)


def gap_id(fl, g):
    return X1.CENSUS_OF.get((fl, g[1], g[0]), f"{g[1]}:{g[0]}")


def storey_v3(fl, F, c1):
    """-> (M3, bays [(stretch id, region)], bay records, held [(gap id, chord polygon)])."""
    W, ax, M, cols, gaps, rects = c1
    groups = V3.arc_groups(arcs_of(F))
    M3, bays, recs, held = M, [], [], []
    for g in gaps:
        if g[0] != V3.CURVED:
            continue
        band = g[1]
        a, b, L, (ux, uy) = ax[band]
        half = float(W[band]["t_m"]) / 2
        band_rect = [p for k, p in rects if k == band][0]
        rec = {"storey": fl, "band": band, "wall_t_m": W[band]["t_m"], "chord_from_m": f"{g[2]:.6f}",
               "chord_to_m": f"{g[3]:.6f}"}
        grp, region = V3.match_bay(groups, band_rect, g[4])
        if grp is None:
            held.append((gap_id(fl, g), g[4]))
            recs.append(dict(rec, status=V3.NO_DRAWN_END, why=region))
            continue
        others = [x[4] for x in gaps if x[1] == band and x is not g]
        M3 = V3.masonry_v3(M3, band, band_rect, g[4], region, cols, others)
        bays.append((gap_id(fl, g), region))
        fc = V3.face_crossings(grp, a, ux, uy, half)
        cr = [v for v in fc.values() if v]
        d_from = min(v[0] for v in cr)
        d_to = max(v[1] for v in cr)
        rec.update(status="DRAWN", r_in_m=f"{grp['wall_r'][0]:.4f}", r_out_m=f"{grp['wall_r'][-1]:.4f}",
                   window_arcs=len(grp["window"]),
                   face_minus_cross_m=";".join(f"{x:.6f}" for x in fc["face_minus"]) if fc["face_minus"] else "",
                   face_plus_cross_m=";".join(f"{x:.6f}" for x in fc["face_plus"]) if fc["face_plus"] else "",
                   drawn_open_from_m=f"{d_from:.4f}", drawn_open_to_m=f"{d_to:.4f}",
                   chord_from_minus_drawn_m=f"{g[2] - d_from:.4f}", drawn_to_minus_chord_m=f"{d_to - g[3]:.4f}",
                   face_minus_line_end_mm=face_line_ends(F, a, ux, uy, -half, fc["face_minus"] or ()),
                   face_plus_line_end_mm=face_line_ends(F, a, ux, uy, half, fc["face_plus"] or ()))
        recs.append(rec)
    return M3, bays, recs, held


def end_record(band, how, W, ax, v2fl, jamb, sign, e, capped, stop, stop_id):
    """T-516's per-end fields (own band part, junction class, walls passed) for a reach e."""
    a, b, L, (ux, uy) = ax[band]
    t = float(W[band]["t_m"])
    seg = LineString([(a[0] + ux * jamb, a[1] + uy * jamb),
                      (a[0] + ux * (jamb + sign * e), a[1] + uy * (jamb + sign * e))])
    thru = sorted(k for k in W if k != band and seg.length > 0 and
                  LineString([ax[k][0], ax[k][1]]).buffer(float(W[k]["t_m"]) / 2, cap_style=3)
                  .intersection(seg).length > 1e-4)
    to_end = max(0.0, jamb if sign < 0 else L - jamb)
    junction = ""
    dwy = [x for x in v2fl["doorways"] if x["wall_id"] == band] if how == "DOORWAY" else []
    if dwy and sign < 0:
        to = dwy[0]["to_wall"]
        junction = ("DOORWAY_STUB_THEN_" + ("ORTHOGONAL" if abs(ux * ax[to][3][0] + uy * ax[to][3][1]) < 0.01
                                            else "OBLIQUE") + ":" + to)
    elif e > to_end + 1e-3:
        endp = a if sign < 0 else b
        met = [j for j in W if j != band and X1.flat_of(W, ax, j).distance(Point(endp)) < t / 2 + 0.22]
        held = any(x.get("what") == "JUNCTION" and x["wall_id"].split("#")[0] == band and
                   x["end"] == (0 if sign < 0 else 1) for x in v2fl["held"])
        obl = [j for j in met if 0.01 < abs(ux * ax[j][3][0] + uy * ax[j][3][1]) < 0.99]
        junction = ("HELD_JUNCTION" if held else "OBLIQUE" if obl else
                    "UNCLASSIFIED" if not met else "ORTHOGONAL") + (":" + ";".join(sorted(met)) if met else "")
    return {"available_m": mm3(e), "search_capped": "YES" if capped else "", "own_band_m": mm3(min(e, to_end)),
            "beyond_band_end": junction, "stopper": stop, "stopper_id": stop_id, "through_walls": ";".join(thru)}


def v1_stop(fl, cols, gaps, a, ux, uy, jamb, sign, e, capped):
    """T-516's point probe on the band axis 3 mm beyond the reach (reproduced as the control)."""
    beyond = jamb + sign * (e + 0.003)
    pt = Point(a[0] + ux * beyond, a[1] + uy * beyond)
    if any(P.contains(pt) for P in cols):
        return "COLUMN", ""
    hit = [x for x in gaps if x[4].contains(pt)]
    if hit:
        return "OPENING", gap_id(fl, hit[0])
    return ("SEARCH_LIMIT", "") if capped else ("END_OF_MASONRY", "")


def main(scratch, out=None, probe=None):
    S = Path(scratch)
    d = pickle.load(open(S / "t125_inputs.pkl", "rb"))
    v = json.load(open(S / "t125_v2.json"))
    rows, bay_rows, cache = [], [], {}
    for oid, (fl, band, how) in X1.CASES.items():
        if fl not in cache:
            c1 = X1.storey(d["floors"][fl], v["floors"][fl]["v2"])
            c3 = storey_v3(fl, d["floors"][fl], c1)
            cache[fl] = (c1, c3)
            bay_rows += c3[2]
        (W, ax, M, cols, gaps, _r), (M3, bays, _recs, held3) = cache[fl]
        v2fl = v["floors"][fl]["v2"]
        a, b, L, (ux, uy) = ax[band]
        t = float(W[band]["t_m"])
        g = [x for x in gaps if x[0] == "DOORWAY" and x[1] == band] if how == "DOORWAY" else \
            [x for x in gaps if x[1] == band and x[0] == how]
        if len(g) != 1:
            raise SystemExit(f"{oid}: {len(g)} gaps for {how} on {band}")
        s0, s1 = g[0][2], g[0][3]
        named = [(gap_id(fl, x), x[4]) for x in gaps if x is not g[0]]
        held_ids = {h for h, _p in held3}
        for side, jamb, sign in (("START", s0, -1), ("END", s1, +1)):
            e1, cap1 = X1.reach(M, a, ux, uy, jamb, sign, t / 2)
            st1 = v1_stop(fl, cols, gaps, a, ux, uy, jamb, sign, e1, cap1)
            e2, cap2 = V2.reach(M, a, ux, uy, jamb, sign, t / 2)
            st2 = V2.stopper(e2, cap2, a, ux, uy, jamb, sign, t / 2, cols, named)
            named3 = [x for x in named if x[0] not in {s for s, _r in bays}]
            e3, cap3, stop3, sid3 = V3.reach_v3(M3, a, ux, uy, jamb, sign, t / 2, cols, named3, bays)
            r3 = end_record(band, how, W, ax, v2fl, jamb, sign, e3, cap3, stop3, sid3)
            if st2[0] == "OPENING" and st2[1] in held_ids:
                # V2 stops at a curved-bay stretch whose end is not drawn: HELD by name (never the chord, never 0)
                r3.update(available_m="", own_band_m="", stopper="", stopper_id=V3.NO_DRAWN_END)
            row = {"opening_id": oid, "storey": fl, "band": band, "engine_ref": how, "wall_t_m": t,
                   "clear_width_m": f"{s1 - s0:.4f}", "side": side,
                   "v1_available_m": mm3(e1), "v1_stopper": st1[0], "v1_stopper_id": st1[1],
                   "v2_available_m": mm3(e2), "v2_stopper": st2[0], "v2_stopper_id": st2[1]}
            row.update(r3)
            row["v3_available_6dp_m"] = "" if not r3["available_m"] else f"{e3:.6f}"
            row["v2_to_v3_m"] = f"{float(r3['available_m']) - float(mm3(e2)):.3f}" if r3["available_m"] else ""
            rows.append(row)
    out = Path(out) if out else OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    with open(out.parent / BAYS_NAME, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=BAY_KEYS, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(bay_rows)
    if probe:
        Path(probe).write_text(json.dumps({"bays": bay_rows}, indent=1, default=str))
    return rows
