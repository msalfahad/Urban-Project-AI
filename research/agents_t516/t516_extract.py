"""T-516 hand-reading helper (research only, NOT engine code): the masonry available beside each jamb of a lintel opening.

Physical element: the lintel end rests on the masonry beside the opening. The masonry a lintel end can bear on is the
built wall material along the opening's own wall line, across the FULL wall thickness, from the jamb outward, until the
first of: an RC column outline (no masonry: the lintel would abut / enter the column), another opening or glazed
stretch (the next jamb), or the end of the masonry (a free end, or the far face of a wall the line runs into). A wall
crossing or meeting the line on the way is masonry the lintel can bear on (it is built material at that point).

Method (exact, no tolerance on the drawn geometry):
  masonry M = union of every census wall rectangle of the storey (centreline +- t/2; an end that meets another wall gets
              a square cap of t/2 so the corner / junction square is built material; a free end stops at its end)
              + every doorway jamb stub (V2 jamb_stubs: 'wall, in the run') - every column outline - every opening /
              glazing / doorway gap (V2 stretches and doorways) as a rectangle across its band.
  available(side) = the largest e (0.1 mm bisection, searched to SEARCH_M) with the strip [jamb, jamb +- e] x full
              thickness (0.5 mm lateral inset) inside M; the stopper is what lies just beyond (COLUMN / OPENING <ref> /
              END_OF_MASONRY) and the walls the strip passed through are listed.
Inputs (outside the repository, never committed): <scratch>/t125_inputs.pkl (research/agents_t125/alsenan_v2_dump.py on
Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf) and <scratch>/t125_v2.json
(research/agents_t125/alsenan_v2_run.py). Output: research/agents_t516/out/JAMB_EVIDENCE_T516.csv, NUMBERS ONLY
(lengths along the wall measured from the jamb; wall / column / opening ids; no drawing coordinate).

    python3 -I research/agents_t516/t516_extract.py <scratch>
"""
import csv
import json
import math
import pickle
import sys
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "JAMB_EVIDENCE_T516.csv"
SEARCH_M = 3.0
INSET = 0.0005
EPS_AREA = 2e-5                 # m2: 0.13 mm of a 0.15 m strip; closes float hairlines where two drawn faces touch

# opening -> (storey, band, engine ref or how the V2 run records it): the T-175 host table (research/agents_t175)
CASES = {
    "D-1F-02": ("1F", "WB-FL0074-FL0075", "OP-020"),
    "D-1F-03": ("1F", "WB-FL0011-FL0012", "DOORWAY"),
    "D-1F-04": ("1F", "WB-FL0074-FL0075", "DOORWAY"),
    "D-1F-07": ("1F", "WB-FL0050-FL0051", "OP-019"),
    "D-1F-08": ("1F", "WB-FL0013-FL0014", "OP-005"),
    "D-1F-10": ("1F", "WB-FL0043-FL0044", "OP-018"),
    "D-2F-01": ("2F", "WB-FL0002-FL0003", "OP-001"),
    "D-2F-03": ("2F", "WB-FL0024-FL0025", "OP-006"),
    "D-GF-06": ("GF", "WB-FL0017-FL0018", "OP-008"),
    "D-GF-10": ("GF", "WB-FL0038-FL0039", "DOORWAY"),
    "D-GF-11": ("GF", "WB-FL0048-FL0049", "OP-017"),
    "D-GF-12": ("GF", "WB-FL0048-FL0049", "OP-018"),
    "D-GF-13": ("GF", "WB-FL0030-FL0031", "OP-012"),
    "W14": ("1F", "WB-FL0082-FL0083", "OP-022"),
    "W15": ("1F", "WB-FL0041-FL0042", "OP-016"),
    "W18": ("1F", "WB-FL0041-FL0042", "GLAZING_IN_BAND"),
}
# engine refs of the census openings that can share a pier with the 16 (T-175 host table)
CENSUS_OF = {("1F", "WB-FL0013-FL0014", "OP-006"): "D-1F-09", ("1F", "WB-FL0041-FL0042", "OP-017"): "W16",
             ("GF", "WB-FL0048-FL0049", "OP-017"): "D-GF-11", ("GF", "WB-FL0048-FL0049", "OP-018"): "D-GF-12",
             ("1F", "WB-FL0074-FL0075", "OP-020"): "D-1F-02", ("1F", "WB-FL0041-FL0042", "OP-016"): "W15",
             ("1F", "WB-FL0041-FL0042", "GLAZING_IN_BAND"): "W18", ("1F", "WB-FL0074-FL0075", "DOORWAY"): "D-1F-04"}


def axis(w, u):
    c = [(x * u, y * u) for x, y in w["centreline"]]
    a, b = c[0], c[-1]
    L = math.dist(a, b)
    return a, b, L, ((b[0] - a[0]) / L, (b[1] - a[1]) / L)


def strip(a, ux, uy, s0, s1, half):
    nx, ny = -uy, ux
    p = lambda s, o: (a[0] + ux * s + nx * o, a[1] + uy * s + ny * o)
    return Polygon([p(s0, -half), p(s1, -half), p(s1, half), p(s0, half)])


def storey(F, V):
    u = F["unit_m"]
    W = {w["wall_id"]: w for w in F["walls"]}
    ax = {k: axis(w, u) for k, w in W.items()}
    flat = {k: LineString([ax[k][0], ax[k][1]]).buffer(float(W[k]["t_m"]) / 2, cap_style=2) for k in W}
    rects, gaps = [], []
    for k, w in W.items():
        a, b, L, (ux, uy) = ax[k]
        h = float(w["t_m"]) / 2
        lo, hi = 0.0, L
        for end, p in ((0, a), (1, b)):
            for j in W:
                if j == k or flat[j].distance(Point(p)) >= h + 0.02:
                    continue
                vx, vy = ax[j][3]
                if abs(ux * vx + uy * vy) > 0.99:
                    continue                 # a collinear continuation: its own rectangle carries on
                # a wall met at this end: the junction is built material up to the met wall's far face
                ss = [(x - a[0]) * ux + (y - a[1]) * uy for x, y in flat[j].exterior.coords]
                if end == 0:
                    lo = min(lo, max(min(ss), -0.5))
                else:
                    hi = max(hi, min(max(ss), L + 0.5))
        rects.append((k, strip(a, ux, uy, lo, hi, h)))
    for js in V["jamb_stubs"]:
        if js.get("status") != "WALL":
            continue
        dw = next(x for x in V["doorways"] if x["wall_id"] == js["wall_id"] and x["end"] == js["end"])
        a, b, L, (ux, uy) = ax[dw["wall_id"]]
        h = float(W[dw["wall_id"]]["t_m"]) / 2
        s = 0.0 if dw["end"] == 0 else L
        g = dw["gap_m"] if dw["end"] == 0 else -dw["gap_m"]
        f = dw["face_to_face_m"] if dw["end"] == 0 else -dw["face_to_face_m"]
        rects.append(("STUB", strip(a, ux, uy, min(s - g, s - f), max(s - g, s - f), h)))
    cols = [Polygon(q).buffer(0) for q in F["columns_m"] if len(q) >= 3]
    for st in V["stretches"]:
        band = st["wall_id"].split("#")[0]
        a, b, L, (ux, uy) = ax[band]
        h = float(W[band]["t_m"]) / 2 + 0.01
        bb = st.get("bridged_by") or ""
        gaps.append((str(st.get("ref") if bb.startswith("OPENING") and st.get("ref") else bb or "NOT_WALL"), band, st["from_m"], st["to_m"],
                     strip(a, ux, uy, st["from_m"], st["to_m"], h)))
    for dw in V["doorways"]:
        a, b, L, (ux, uy) = ax[dw["wall_id"]]
        h = float(W[dw["wall_id"]]["t_m"]) / 2 + 0.01
        s = 0.0 if dw["end"] == 0 else L
        g = dw["gap_m"] if dw["end"] == 0 else -dw["gap_m"]
        gaps.append(("DOORWAY", dw["wall_id"], min(s, s - g), max(s, s - g), strip(a, ux, uy, min(s, s - g),
                                                                                   max(s, s - g), h)))
    # a gap removes masonry from its OWN wall only: a junction square another wall builds stays masonry
    own = [P.difference(unary_union([g[4] for g in gaps if g[1] == k] or [Polygon()])) for k, P in rects]
    M = unary_union(own).difference(unary_union(cols))
    return W, ax, M, cols, gaps, rects


def flat_of(W, ax, j):
    return LineString([ax[j][0], ax[j][1]]).buffer(float(W[j]["t_m"]) / 2, cap_style=2)


def reach(M, a, ux, uy, jamb, sign, half):
    ok = lambda e: strip(a, ux, uy, min(jamb, jamb + sign * e), max(jamb, jamb + sign * e),
                         half - INSET).difference(M).area < EPS_AREA
    if ok(SEARCH_M):
        return SEARCH_M, True
    lo, hi = 0.0, SEARCH_M
    if not ok(1e-4):
        return 0.0, False
    while hi - lo > 1e-5:
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if ok(mid) else (lo, mid)
    return lo, False


def main(scratch):
    S = Path(scratch)
    d = pickle.load(open(S / "t125_inputs.pkl", "rb"))
    v = json.load(open(S / "t125_v2.json"))
    rows = []
    cache = {}
    for oid, (fl, band, how) in CASES.items():
        if fl not in cache:
            cache[fl] = storey(d["floors"][fl], v["floors"][fl]["v2"])
        W, ax, M, cols, gaps, _r = cache[fl]
        a, b, L, (ux, uy) = ax[band]
        t = float(W[band]["t_m"])
        if how == "DOORWAY":
            g = [x for x in gaps if x[0] == "DOORWAY" and x[1] == band]
        else:
            g = [x for x in gaps if x[1] == band and x[0] == how]
        if len(g) != 1:
            raise SystemExit(f"{oid}: {len(g)} gaps for {how} on {band}")
        _ref, _b, s0, s1, _P = g[0]
        others = sorted((x for x in gaps if x[1] == band and x is not g[0]), key=lambda x: x[2])
        for side, jamb, sign in (("START", s0, -1), ("END", s1, +1)):
            e, capped = reach(M, a, ux, uy, jamb, sign, t / 2)
            beyond = jamb + sign * (e + 0.003)
            pt = Point(a[0] + ux * beyond, a[1] + uy * beyond)
            if any(P.contains(pt) for P in cols):
                stop, stop_id = "COLUMN", ""
            else:
                hit = [x for x in gaps if x[4].contains(pt)]
                if hit:
                    stop = "OPENING"
                    stop_id = CENSUS_OF.get((fl, hit[0][1], hit[0][0]), f"{hit[0][1]}:{hit[0][0]}")
                else:
                    stop, stop_id = ("SEARCH_LIMIT", "") if capped else ("END_OF_MASONRY", "")
            seg = LineString([(a[0] + ux * jamb, a[1] + uy * jamb), (a[0] + ux * (jamb + sign * e),
                                                                      a[1] + uy * (jamb + sign * e))])
            thru = sorted(k for k in W if k != band and seg.length > 0 and
                          LineString([ax[k][0], ax[k][1]]).buffer(float(W[k]["t_m"]) / 2, cap_style=3)
                          .intersection(seg).length > 1e-4)
            to_end = max(0.0, jamb if sign < 0 else L - jamb)
            own = min(e, to_end)
            junction = ""
            dwy = [x for x in v["floors"][fl]["v2"]["doorways"] if x["wall_id"] == band] if how == "DOORWAY" else []
            if dwy and sign < 0:
                to = dwy[0]["to_wall"]
                junction = ("DOORWAY_STUB_THEN_" + ("ORTHOGONAL" if abs(ux * ax[to][3][0] + uy * ax[to][3][1]) < 0.01
                                                    else "OBLIQUE") + ":" + to)
            elif e > to_end + 1e-3:
                # the strip leaves the band at its end: trusted only where every wall met there is orthogonal (a clean
                # T / L) and the V2 run did not leave that junction HELD; else only the own-band part is measured
                endp = a if sign < 0 else b
                met = [j for j in W if j != band and flat_of(W, ax, j).distance(Point(endp)) < t / 2 + 0.22]
                held = any(x.get("what") == "JUNCTION" and x["wall_id"].split("#")[0] == band and
                           x["end"] == (0 if sign < 0 else 1) for x in v["floors"][fl]["v2"]["held"])
                obl = [j for j in met if 0.01 < abs(ux * ax[j][3][0] + uy * ax[j][3][1]) < 0.99]
                junction = ("HELD_JUNCTION" if held else "OBLIQUE" if obl else
                            "UNCLASSIFIED" if not met else "ORTHOGONAL") + (":" + ";".join(sorted(met)) if met else "")
            mm = lambda x: f"{math.floor(x * 1000 + 1e-9) / 1000:.3f}"
            rows.append({"opening_id": oid, "storey": fl, "band": band, "engine_ref": how, "wall_t_m": t,
                         "clear_width_m": f"{s1 - s0:.4f}", "side": side, "available_m": mm(e),
                         "search_capped": "YES" if capped else "", "own_band_m": mm(own), "beyond_band_end": junction,
                         "stopper": stop, "stopper_id": stop_id, "through_walls": ";".join(thru)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r["opening_id"], r["side"], r["clear_width_m"], r["available_m"], r["own_band_m"], r["stopper"],
              r["stopper_id"], r["beyond_band_end"])


if __name__ == "__main__":
    main(sys.argv[1])
