"""T-152 hand ledger: Alsenan suspended-slab steel by bar population, per panel and direction (lane S, gate 3;
NO REPO CODE task).

A research script that only does the arithmetic of a hand table typed from the drawings; it imports nothing from engine/
and changes no released quantity.

    python3 -I research/agents_t152/t152_slab_steel.py --check
    python3 -I research/agents_t152/t152_slab_steel.py build <faces.json> <T-139 PANELS.csv> <out T152_INPUT.csv>
    python3 -I research/agents_t152/t152_slab_steel.py ledger [T152_INPUT.csv] [out dir]

Inputs:
  * LABELS below: the slab bar labels of ST7757.pdf p.4 (GF roof), p.5 (1F roof), p.6 (2F roof), read by eye at 200 dpi
    this run and matched to the T-139 slab panels (agents/task-T-139 6f84281, PANELS.csv: 62 slab rows). A label written
    horizontally sits on a horizontal bar line = bars running in x (count across the y extent); a label written
    vertically = bars running in y. 'n ø d/m' = n bars per metre run (DRAWING-CONFIRMED by contrast in T-155: the same
    set prints a count as 'n ø d' and a spacing as 'ø d/s cm'). '(T&B)' = the same mesh top and bottom.
  * Sheet note 2 on p.4 / p.5 / p.6 (paraphrase): top bars 5 ø 10 per metre over the beams of the slabs, for a length of
    one third of the span, in both directions. Whether that length is the whole bar (centred on the beam) or the
    extension into each panel is NOT printed: both readings are carried, HELD.
  * p.8 general note 9 (development / lap length not less than 70 d in tension, 40 d in compression) and note 22 (cover
    not less than 2.5 cm in slabs: a minimum, so no cover is deducted from a panel; the bars run on into the beams).
  * T152_INPUT.csv (built from the private faces of the three slab sheets with the T-139 helper slab_faces.py; numbers
    only): per panel and direction the extent across which the bars are spread and the chord length of every bar line
    under count readings A and B.

  * ST p.15 TYP. SLAB ON BEAMS DETAIL (read at 200 dpi this run): bottom bars, 50 % stop 0.125 L from the face of a
    continuous support, the balance continuous; top 0.30 x the larger adjacent clear span over a continuous support,
    0.25 L1 at a non-continuous support; temperature-bar schedule rows 150 / 175 mm only (no 160 mm row).

Count of bars from a per-metre rate: no Urban rule (owner Q-71, OPEN). Readings carried side by side:
  A  N = ceil(rate x H) bars, one in the middle of each of N equal strips across the extent H;
  B  N + 1 bars, the first and last on the panel edges (spacing H / N);
  C  rate x H kept fractional, x the mean face-to-face chord (information for Q-71 only).
Bottom bar length = the chord of each bar line across the panel, face to face (T-139 panel geometry,
URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1), less the p.15 curtailment at each continuous end (a support with another slab
panel within 0.80 m beyond the face), plus the continuing half across that beam (shared half to each side).
HELD, never 0: bar extension into edge beams and development / laps (note 9: 2 x 40 d .. 2 x 70 d per bar); top bars
over the supports (sheet note 2 against p.15: two project drawings in conflict, three readings carried); the (T&B)
panels' note-2 top bars; temperature bars at 160 mm; labels without '/m'; panels with no printed bars.
kg = count x length x d^2/162 (URBAN-REBAR-NET-AND-PROCUREMENT@v1; never kg/m3).
"""

import csv
import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
EPS = 1e-9
DEV_K = (40, 70)          # p.8 note 9
NOTE2 = (5.0, 10)         # sheet note 2: 5 bars per metre, ø 10, top, over the beams
STOCK_M = 12.0            # URBAN-REBAR-NET-AND-PROCUREMENT@v1 stock length: no slab bar here reaches it


def kgm(d_mm):
    """unit mass d^2 / 162 (the project method, rebar_unit_mass D2_OVER_162)."""
    return d_mm * d_mm / 162.0


# ---------------------------------------------------------------- the printed labels, panel by panel (read by eye)
# panel -> list of (direction, label as printed, rate per m or None, diameter, layers, note)
# direction 'x' = label written horizontally (bars run in x); 'y' = written vertically. layers 1 = normal mesh,
# 2 = '(T&B)'. rate None = the label prints no '/m' (count or truncated rate: both readings, HELD).
def L(d, txt, rate, dia, layers=1, note=""):
    return dict(dir=d, label=txt, rate=rate, d=dia, layers=layers, note=note)


LABELS = {
    # ---- GF roof slab, ST p.4
    "GF-015": [L("y", "5ø10/m", 5, 10), L("x", "5ø10/m", 5, 10)],
    "GF-016": [L("x", "5ø10/m", 5, 10), L("y", "5ø10/m", 5, 10)],
    "GF-018": [L("x", "5ø10/m", 5, 10), L("y", "5ø10/m", 5, 10)],
    "GF-020": [L("x", "5ø10/m", 5, 10), L("y", "5ø10", None, 10, note="vertical label prints no '/m' (0.62 m strip "
                                          "above the B7 ring): 5 bars in all, or 5 per metre: designer item")],
    "GF-027": [L("y", "5ø10/m", 5, 10), L("x", "5ø10/m", 5, 10)],
    "GF-032": [L("x", "6ø10/m", 6, 10), L("y", "5ø10/m", 5, 10)],
    "GF-039": [L("x", "5ø10/m", 5, 10), L("y", "6ø10/m", 6, 10)],
    "GF-052": [L("y", "5ø10/m", 5, 10), L("x", "5ø10/m", 5, 10)],
    "GF-076": [L("y", "5ø10/m", 5, 10), L("x", "5ø10", None, 10, note="horizontal label prints no '/m': designer item")],
    "GF-077": [L("x", "5ø10/m", 5, 10), L("y", "5ø10/m", 5, 10)],
    "GF-078": [L("x", "6ø10/m", 6, 10), L("y", "7ø12/m", 7, 12)],
    "GF-079": [L("y", "5ø10/m", 5, 10), L("x", "5ø10/m", 5, 10)],
    "GF-081": [L("x", "5ø10/m", 5, 10), L("y", "5ø10/m", 5, 10)],
    "GF-098": [L("x", "6ø10/m", 6, 10), L("y", "7ø10/m", 7, 10)],
    "GF-101": [L("y", "5ø10/m", 5, 10), L("x", "5ø10/m", 5, 10)],
    "GF-105": [L("x", "5ø10/m", 5, 10), L("y", "6ø10/m", 6, 10)],
    "GF-124": [L("x", "7ø10/m", 7, 10), L("y", "6ø10/m", 6, 10)],
    "GF-126": [L("x", "7ø10/m", 7, 10, note="a second horizontal bar '6ø14/m' (hooked at its west end) is drawn in "
                                            "the south part of this panel by the round stair; its zone is not "
                                            "delimited: HELD as its own line (designer item); 7ø10/m measured over "
                                            "the panel as printed"),
               L("y", "6ø10/m", 6, 10)],
    "GF-128": [L("y", "5ø10/m", 5, 10), L("x", "5ø10/m", 5, 10)],
    "GF-134": [L("y", "5ø10/m", 5, 10), L("x", "6ø10/m", 6, 10, note="label written on the B26 band (face GF-133); "
                                                                      "its bar line runs into this strip (by eye)")],
    "GF-135": [L("x", "7ø10/m", 7, 10), L("y", "6ø10/m", 6, 10)],
    "GF-137": [L("x", "7ø10/m", 7, 10), L("y", "6ø10/m", 6, 10)],
    "GF-139": [L("x", "7ø10/m", 7, 10), L("y", "6ø10/m", 6, 10)],
    "GF-141": [L("x", "6ø10/m", 6, 10), L("y", "5ø10/m", 5, 10)],
    "GF-169": [L("x", "5ø10/m", 5, 10), L("y", "5ø10/m", 5, 10)],
    "GF-172": [L("x", "5ø10/m", 5, 10), L("y", "5ø10/m", 5, 10)],
    "GF-173": [L("x", "5ø10/m", 5, 10), L("y", "5ø10/m", 5, 10)],
    "GF-176": [L("x", "5ø10/m", 5, 10), L("y", "5ø10/m", 5, 10)],
    # ---- 1F roof slab, ST p.5
    "1F-018": [L("y", "5ø10/m", 5, 10), L("x", "5ø10/m", 5, 10)],
    "1F-020": [L("x", "6ø10/m", 6, 10), L("y", "5ø10/m", 5, 10)],
    "1F-023": [L("x", "7ø10/m", 7, 10), L("y", "6ø10/m", 6, 10)],
    "1F-025": [L("x", "7ø10/m", 7, 10), L("y", "6ø10/m", 6, 10)],
    "1F-041": [L("x", "5ø10/m", 5, 10), L("y", "5ø10", None, 10, note="vertical label prints no '/m' (0.785 m strip "
                                          "above the west dome): designer item")],
    "1F-057": [L("x", "5ø10/m", 5, 10), L("y", "5ø10/m", 5, 10, note="label written on the B25 face band (face "
                                                                      "1F-066); its bar line is in this strip (by eye)")],
    "1F-062": [L("x", "5ø10/m", 5, 10), L("y", "6ø10/m", 6, 10)],
    "1F-063": [L("x", "5ø10/m", 5, 10), L("y", "5ø10/m", 5, 10)],
    "1F-065": [L("y", "5ø10/m", 5, 10), L("x", "5ø10/m", 5, 10)],
    "1F-084": [L("x", "8ø10/m", 8, 10), L("y", "7ø10/m", 7, 10)],
    "1F-086": [L("x", "6ø10/m", 6, 10), L("y", "5ø10/m", 5, 10)],
    "1F-088": [L("x", "6ø10/m", 6, 10), L("y", "5ø10/m", 5, 10)],
    "1F-094": [L("x", "5ø10/m", 5, 10), L("y", "5ø10/m", 5, 10)],
    "1F-096": [L("x", "5ø10/m", 5, 10), L("y", "5ø10/m", 5, 10)],
    # ---- 2F roof slab, ST p.6
    "2F-011": [L("x", "7ø14/m (T&B)", 7, 14, 2), L("y", "6ø14/m (T&B)", 6, 14, 2)],
    "2F-013": [L("y", "6ø12/m (T&B)", 6, 12, 2), L("x", "6ø12/m (T&B)", 6, 12, 2)],
    "2F-016": [L("x", "7ø10/m", 7, 10), L("y", "6ø10/m", 6, 10)],
    "2F-025": [L("y", "5ø10/m", 5, 10), L("x", "5ø10/m", 5, 10)],
    "2F-033": [L("x", "6ø10/m", 6, 10), L("y", "5ø10/m", 5, 10)],
    "2F-045": [L("x", "5ø10/m", 5, 10), L("y", "5ø10/m", 5, 10)],
    "2F-047": [L("x", "5ø10/m", 5, 10), L("y", "5ø10/m", 5, 10)],
}

# slab panels with no printed bar label (sheets searched: p.4 / p.5 / p.6 plans, p.7 dome and pool details,
# p.8 notes, p.16 stair details): HELD, designer item; never a typical value
NO_LABEL = {
    "GF-034": "pool-court bay corner outside the B7 ring (T-127 / T-139)",
    "GF-036": "pool-court bay corner outside the B7 ring",
    "GF-059": "pool-court bay corner outside the B7 ring",
    "GF-061": "pool-court bay corner outside the B7 ring",
    "GF-146": "wedge east of the round-stair flight edge",
    "1F-060": "west dome square corner outside the ring r 2.4111 (p.7 details the dome shell only)",
    "1F-073/c0": "west dome square corner", "1F-073/c1": "west dome square corner",
    "1F-076/c0": "east dome square corner", "1F-076/c1": "east dome square corner",
    "1F-090": "west dome square corner", "1F-091": "east dome square corner", "1F-092": "east dome square corner",
}

# printed bars on the slab sheets that are NOT a panel mesh (listed so nothing is silently dropped)
OTHER_BARS = [
    ("GF", "GF-126", "6ø14/m", "extra bottom bar in the south part of panel GF-126 (hooked west end), zone not delimited",
     "HELD (designer item: extent of the 6ø14/m zone)"),
    ("1F", "1F-084", "3ø14 x 4 corners", "corner reinforcement (legend 'Corner Reinforcement') at the four corners of "
     "the 'T 16' panel: 12 bars ø14, length not printed", "HELD (length; count 12 printed)"),
    ("GF", "GF-025 / GF-130", "8ø16/m", "main and round stair zones", "stair ledger (T-111), not slab"),
    ("1F", "1F-016", "8ø16/m", "main stair zone", "stair ledger (T-111), not slab"),
    ("GF", "CB6 / B7 / B4 joint", "3ø16/Top", "hooked top bar at the curved B7 end over B4", "beam lane (T-149)"),
    ("2F", "B8 east end", "4ø16/Top", "hooked top bar along B8 at the hatched east end", "beam lane (T-149)"),
    ("2F", "B7 east face", "5ø18/Top", "hooked top bar along B7 at the hatched east strip", "beam lane (T-149)"),
    ("ALL", "every 16 cm panel", "p.15 temperature schedule", "temperature bars where a beam runs parallel to the "
     "main bars (p.15 note 2): the schedule prints 150 and 175 mm rows only", "HELD (no 160 mm row; no interpolation)"),
    ("1F", "1F-023", "P.C 20x50 8ø16", "planted column on the slab", "column ledger (T-148), not slab"),
    ("GF", "south edge", "P.C 20x70 10ø16 / P.C 20x50 8ø16", "planted columns", "column ledger (T-148), not slab"),
]


# ---------------------------------------------------------------- bar lines with their support ends
PROBE = 0.80     # m: the widest beam band between two slab faces on these sheets is 0.65 m (B26)
P15_STOP = 0.125  # p.15 TYP. SLAB ON BEAMS DETAIL: 50 % of the bottom bars stop 0.125 L from a continuous support face
P15_TOP_CONT, P15_TOP_END = 0.30, 0.25   # p.15: top 0.30 x max(L1, L2) over a continuous support, 0.25 L1 at an end


def _segments(poly, axis, c, e=1e-5):
    """bar-line segments inside the polygon at coordinate c (the panel side of a line on an edge, as _chord2)."""
    from shapely.geometry import LineString
    x0, y0, x1, y1 = poly.bounds
    best = None
    for cc in (c - e, c + e):
        ln = LineString([(x0 - 1, cc), (x1 + 1, cc)]) if axis == "x" else LineString([(cc, y0 - 1), (cc, y1 + 1)])
        g = poly.intersection(ln)
        segs = [q for q in getattr(g, "geoms", [g]) if q.geom_type == "LineString" and q.length > 1e-6]
        if best is None or sum(q.length for q in segs) > sum(q.length for q in best):
            best = segs
    return best or []


def _probe(pt, u, others):
    """from a bar end, look past the support face along the bar: (continuous, gap to the next slab face, that slab's
    chord on the same line) or (False, None, None) when no slab face lies within PROBE (an edge / end support)."""
    from shapely.geometry import LineString, Point
    ray = LineString([pt, (pt[0] + u[0] * PROBE, pt[1] + u[1] * PROBE)])
    best = None
    for oid, og in others:
        if not ray.intersects(og):
            continue
        hit = ray.intersection(og)
        d = min(Point(pt).distance(Point(q)) for g in getattr(hit, "geoms", [hit]) for q in g.coords) \
            if not hit.is_empty else None
        if d is not None and d > 1e-4 and (best is None or d < best[0]):
            best = (d, oid, og)
    if best is None:
        return (False, None, None)
    d, oid, og = best
    q = (pt[0] + u[0] * (d + 2e-4), pt[1] + u[1] * (d + 2e-4))
    axis = "x" if abs(u[0]) > 0.5 else "y"
    c = pt[1] if axis == "x" else pt[0]
    nb = [s_ for s_ in _segments(og, axis, c) if s_.distance(Point(q)) < 1e-3]
    return (True, round(d, 4), round(nb[0].length, 4) if nb else None)


def line_table(poly, axis, rate, others):
    """per reading A / B: list of bar lines, each a list of segments [length, end_lo, end_hi]; end = [cont, gap, nb]."""
    x0, y0, x1, y1 = poly.bounds
    lo, hi = (y0, y1) if axis == "x" else (x0, x1)
    H = hi - lo
    n = int(math.ceil(rate * H - EPS))
    if n < 1:
        raise ValueError("empty extent")
    pos = {"A": [lo + (k + 0.5) * H / n for k in range(n)], "B": [lo + k * H / n for k in range(n + 1)]}
    out = {}
    for tag, cs in pos.items():
        lines = []
        for c in cs:
            segs = []
            for sg in _segments(poly, axis, c):
                (ax, ay), (bx, by) = sg.coords[0], sg.coords[-1]
                if (bx - ax) + (by - ay) < 0:
                    ax, ay, bx, by = bx, by, ax, ay
                u = (1.0, 0.0) if axis == "x" else (0.0, 1.0)
                e_lo = _probe((ax, ay), (-u[0], -u[1]), others)
                e_hi = _probe((bx, by), u, others)
                segs.append([round(sg.length, 4), list(e_lo), list(e_hi)])
            lines.append(segs)
        out[tag] = lines
    return round(H, 4), out


def build(faces_json, panels_csv, out_csv):
    """T-139 faces (slab_faces.py output) + T-139 PANELS.csv -> T152_INPUT.csv (numbers only, no drawing content)."""
    from shapely import wkt
    from shapely.geometry import Point
    faces = json.load(open(faces_json))
    geo = {f["id"]: wkt.loads(f["wkt"]) for fl in faces.values() for f in fl}
    # dome corners: T-139 slab_ledger.py DOME_SPLIT (1F sheet, ring r 2.4111 about the two dome centres)
    split = {"1F-073": (16.380, 41.651, 2.4111), "1F-076": (30.828, 41.651, 2.4111)}
    for fid, (cx, cy, r_out) in split.items():
        parts = geo[fid].difference(Point(cx, cy).buffer(r_out, quad_segs=256))
        k = 0
        for c in getattr(parts, "geoms", [parts]):
            if c.area >= 0.02:
                geo["%s/c%d" % (fid, k)] = c
                k += 1
    slab = [r for r in csv.DictReader(open(panels_csv)) if r["cls"] == "SLAB"]
    assert len(slab) == 62, len(slab)
    assert set(LABELS) | set(NO_LABEL) == {r["id"] for r in slab}, "every slab panel has labels or a HELD reason"
    assert not set(LABELS) & set(NO_LABEL)
    for r in slab:
        assert abs(geo[r["id"]].area - float(r["area"])) < 0.001, r["id"]
    rows = []
    for r in slab:
        if r["id"] in NO_LABEL:
            continue
        g = geo[r["id"]]
        others = [(q["id"], geo[q["id"]]) for q in slab if q["floor"] == r["floor"] and q["id"] != r["id"]]
        for lab in LABELS[r["id"]]:
            rate = lab["rate"] if lab["rate"] is not None else 5.0     # geometry for the per-metre reading
            H, mesh = line_table(g, lab["dir"], rate, others)
            H2, top = line_table(g, lab["dir"], NOTE2[0], others)
            rows.append(dict(panel=r["id"], floor=r["floor"], area=r["area"], t=r["t"], dir=lab["dir"], H=H,
                             mesh=json.dumps(mesh, separators=(",", ":")), top=json.dumps(top, separators=(",", ":"))))
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("written", out_csv, len(rows), "rows")


# ---------------------------------------------------------------- arithmetic on the bar lines
def bottom_len(lines):
    """(face to face, p.15 curtailed, continuing-half crossing) lengths of the bottom bars of one reading.
    p.15: at a continuous support 50 % of the bars stop 0.125 L short of the face (L = the local clear span of the
    bar line = its segment), the other 50 % run on across the beam: the crossing is shared, half to each panel."""
    full = curt = cross = 0.0
    for segs in lines:
        for ln, e0, e1 in segs:
            full += ln
            nc = int(e0[0]) + int(e1[0])
            curt += ln - 0.5 * P15_STOP * ln * nc
            cross += sum(0.5 * e[1] / 2.0 for e in (e0, e1) if e[0])
    return full, curt, cross


def top_len(lines):
    """top bars over the supports of one reading (rate 5 / m lines), lengths into this panel at both ends:
    note-2 reading i (L/6 per end), reading ii (L/3 per end), p.15 (0.30 max(L1, L2) continuous, 0.25 L1 end);
    plus the crossing over continuous supports (half the beam gap per end)."""
    i = ii = p15 = cross = 0.0
    for segs in lines:
        for ln, e0, e1 in segs:
            for e in (e0, e1):
                i += ln / 6.0
                ii += ln / 3.0
                if e[0]:
                    p15 += P15_TOP_CONT * max(ln, e[2] if e[2] is not None else ln)
                    cross += e[1] / 2.0
                else:
                    p15 += P15_TOP_END * ln
    return i, ii, p15, cross


def ends(lines):
    n = c = 0
    for segs in lines:
        for ln, e0, e1 in segs:
            n += 2
            c += int(e0[0]) + int(e1[0])
    return n, c


def ledger(inp=None, outdir=None):
    inp = inp or os.path.join(HERE, "T152_INPUT.csv")
    outdir = outdir or HERE
    rows = list(csv.DictReader(open(inp)))
    seen = defaultdict(int)
    out = []
    tot = defaultdict(lambda: defaultdict(float))
    for r in rows:
        pid, fl = r["panel"], r["floor"]
        lab = LABELS[pid][seen[pid]]
        seen[pid] += 1
        assert lab["dir"] == r["dir"], pid
        mesh, top = json.loads(r["mesh"]), json.loads(r["top"])
        H = float(r["H"])
        d, lay, u = lab["d"], lab["layers"], kgm(lab["d"])
        nA, nB = len(mesh["A"]), len(mesh["B"])
        if lab["rate"] is not None:
            assert nA == math.ceil(lab["rate"] * H - EPS) and nB == nA + 1, pid
        fA, cA, xA = bottom_len(mesh["A"])
        fB, cB, xB = bottom_len(mesh["B"])
        held = lab["rate"] is None
        if lay == 2:      # (T&B): the top layer is the same mesh, run face to face (no curtailment drawn for a top mesh)
            kg = dict(A=(fA + cA) * u, B=(fB + cB) * u, fullA=2 * fA * u, fullB=2 * fB * u)
        else:
            kg = dict(A=cA * u, B=cB * u, fullA=fA * u, fullB=fB * u)
        kg["xA"], kg["xB"] = xA * u * lay, xB * u * lay
        LC = (lab["rate"] * H * (fA / nA)) if not held else None   # Q-71 reading C, information (face to face)
        tn, tc = ends(mesh["A"])
        tiA, tiiA, tpA, txA = top_len(top["A"])
        tiB, tiiB, tpB, txB = top_len(top["B"])
        u10 = kgm(NOTE2[1])
        topk = dict(lo=min(tiA, tiiA, tpA) * u10, hi=max(tiB, tiiB, tpB) * u10, cross=(txA * u10, txB * u10),
                    i=(tiA * u10, tiB * u10), ii=(tiiA * u10, tiiB * u10), p15=(tpA * u10, tpB * u10))
        devA = (2 * DEV_K[0] * d / 1000 * nA * lay * u, 2 * DEV_K[1] * d / 1000 * nA * lay * u)
        devB = (2 * DEV_K[0] * d / 1000 * nB * lay * u, 2 * DEV_K[1] * d / 1000 * nB * lay * u)
        count_kg = 5 * (fA / nA) * u * lay if held else None
        o = dict(panel=pid, floor=fl, area_m2=r["area"], t_m=r["t"], direction=lab["dir"], printed=lab["label"],
                 d_mm=d, layers=lay, spread_m=H, bars_A=nA, bars_B=nB,
                 ends_continuous="%d/%d" % (tc, tn),
                 len_face_A_m=round(fA, 3), len_face_B_m=round(fB, 3),
                 len_p15_A_m=round(cA, 3), len_p15_B_m=round(cB, 3),
                 kg_A=round(kg["A"], 3), kg_B=round(kg["B"], 3), kg_cross_A=round(kg["xA"], 3),
                 kg_cross_B=round(kg["xB"], 3), kg_face_uncurtailed_A=round(kg["fullA"], 3),
                 kg_C_info=round(LC * u * lay, 3) if LC is not None else "",
                 dev_held_kg="%.3f..%.3f" % (devA[0], devB[1]),
                 top_held_kg="%.3f..%.3f (i %.3f..%.3f, ii %.3f..%.3f, p15 %.3f..%.3f; crossing %.3f..%.3f)" % (
                     topk["lo"], topk["hi"], *topk["i"], *topk["ii"], *topk["p15"], *topk["cross"]),
                 status="HELD_LABEL" if held else "MEASURED_NET_COUNT_HELD_Q71",
                 note=lab["note"] + ("; count reading 5 bars = %.3f kg" % count_kg if held else ""))
        out.append(o)
        T = tot[fl]
        if held:
            T["held_label_lo"] += min(count_kg, kg["A"])
            T["held_label_hi"] += max(count_kg, kg["B"] + kg["xB"])
        else:
            T["A"] += kg["A"] + kg["xA"]
            T["B"] += kg["B"] + kg["xB"]
            T["A_in_panel"] += kg["A"]; T["B_in_panel"] += kg["B"]
            T["A_crossing"] += kg["xA"]; T["B_crossing"] += kg["xB"]
            T["C_info_face"] += LC * u * lay
            T["A_uncurtailed_face"] += kg["fullA"]
            T["dev_lo"] += devA[0]; T["dev_hi"] += devB[1]
            T["by_d_A_%02d" % d] += kg["A"] + kg["xA"]
            T["by_d_B_%02d" % d] += kg["B"] + kg["xB"]
        if not held:      # the frozen S7 convention, for the engine comparison only: reading C (rate x H, unrounded)
            fC = lab["rate"] * H / nA
            T[("S7eq_TB_" if lay == 2 else "S7eq_") + "bottom"] += (kg["A"] + kg["xA"]) * fC
        ntop = len(top["A"])
        fT = NOTE2[0] * H / ntop
        T[("S7eq_TB_" if lay == 2 else "S7eq_") + "top_ii"] += (topk["ii"][0] + topk["cross"][0]) * fT
        key = "topTB_" if lay == 2 else "top_"
        T[key + "lo"] += topk["lo"]; T[key + "hi"] += topk["hi"] + topk["cross"][1]
        for nm in ("i", "ii", "p15", "cross"):
            T[key + nm + "_A"] += topk[nm][0]; T[key + nm + "_B"] += topk[nm][1]
    with open(os.path.join(outdir, "T152_SLAB_STEEL.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    summ = {fl: {k: round(v, 3) for k, v in sorted(T.items())} for fl, T in tot.items()}
    allT = defaultdict(float)
    for T in tot.values():
        for k, v in T.items():
            allT[k] += v
    summ["TOTAL"] = {k: round(v, 3) for k, v in sorted(allT.items())}
    summ["held_panels_no_label"] = sorted(NO_LABEL)
    summ["other_bars"] = [list(x) for x in OTHER_BARS]
    with open(os.path.join(outdir, "T152_SUMMARY.json"), "w") as fh:
        json.dump(summ, fh, indent=1, ensure_ascii=False)
    for fl in ("GF", "1F", "2F", "TOTAL"):
        s_ = summ[fl]
        print("%-5s bottom A %8.2f B %8.2f (C %8.2f, uncurt A %8.2f) | held labels %.2f..%.2f | top %.2f..%.2f | "
              "T&B top %.2f..%.2f | dev %.2f..%.2f" % (fl, s_.get("A", 0), s_.get("B", 0),
              s_.get("S7eq_bottom", 0) + s_.get("S7eq_TB_bottom", 0),
              s_.get("A_uncurtailed_face", 0), s_.get("held_label_lo", 0), s_.get("held_label_hi", 0),
              s_.get("top_lo", 0), s_.get("top_hi", 0), s_.get("topTB_lo", 0), s_.get("topTB_hi", 0),
              s_.get("dev_lo", 0), s_.get("dev_hi", 0)))
    return summ


# ---------------------------------------------------------------- synthetic NON-Alsenan fixture, hand-calculated
def check():
    from shapely.geometry import Polygon, box
    from shapely.affinity import rotate, scale
    ok = True

    def eq(name, got, want, tol=1e-3):
        nonlocal ok
        good = abs(got - want) <= tol
        ok &= good
        print("%-62s got %10.4f want %10.4f %s" % (name, got, want, "PASS" if good else "FAIL"))

    u12, u10 = kgm(12), kgm(10)
    # 1. two panels on one 0.20 m beam: P1 3.0 x 4.2 (x 0..3.0), P2 4.0 x 4.2 (x 3.2..7.2); P1 bars '6 ø 12 / m' in x
    P1, P2 = box(0, 0, 3.0, 4.2), box(3.2, 0, 7.2, 4.2)
    H, t = line_table(P1, "x", 6, [("P2", P2)])
    eq("P1 spread", H, 4.2)
    eq("P1 bars A = ceil(6 x 4.2) = 26", len(t["A"]), 26)
    eq("P1 bars B = 27", len(t["B"]), 27)
    eq("P1 east end continuous, gap 0.20", t["A"][0][0][2][1], 0.2)
    eq("P1 east neighbour chord 4.0", t["A"][0][0][2][2], 4.0)
    ok &= t["A"][0][0][1][0] is False
    fA, cA, xA = bottom_len(t["A"])
    eq("A face to face 26 x 3.0", fA, 78.0)
    eq("A p.15: 78 - 26 x 0.5 x 0.125 x 3.0 = 73.125", cA, 73.125)
    eq("A continuing-half crossing 26 x 0.5 x 0.20 / 2 = 1.300", xA, 1.3)
    eq("A kg (73.125 + 1.3) x 0.888889 = 66.156", (cA + xA) * u12, 66.156)
    fB, cB, xB = bottom_len(t["B"])
    eq("B face to face 27 x 3.0", fB, 81.0)
    eq("B p.15: 81 - 27 x 0.1875 = 75.9375", cB, 75.9375)
    eq("Q-71 reading C (information) 6 x 4.2 x 3.0 x 0.888889 = 67.200", 6 * 4.2 * (fA / 26) * u12, 67.2)
    H, tt = line_table(P1, "x", 5, [("P2", P2)])
    eq("top lines A = ceil(5 x 4.2) = 21 (exact multiple, no 22)", len(tt["A"]), 21)
    i_, ii_, p15, cr = top_len(tt["A"])
    eq("top note-2 i: 21 x 2 ends x 3.0 / 6 = 21.0 m", i_, 21.0)
    eq("top note-2 ii: 21 x 2 x 3.0 / 3 = 42.0 m", ii_, 42.0)
    eq("top p.15: 21 x (0.25 x 3.0 + 0.30 x max(3.0, 4.0)) = 40.95 m", p15, 40.95)
    eq("top crossing: 21 x 0.20 / 2 = 2.1 m", cr, 2.1)
    eq("top p.15 kg 40.95 x 0.617284 = 25.278", p15 * u10, 25.278)
    # mirror (P1 to the east of P2) gives the same lengths
    H, tm = line_table(scale(P1, -1, 1, origin=(0, 0)), "x", 6, [("P2", scale(P2, -1, 1, origin=(0, 0)))])
    eq("mirror: p.15 length unchanged", bottom_len(tm["A"])[1], 73.125)
    # rotation by 90 degrees: the same panel pair with the bars now running in y
    H, tr = line_table(rotate(P1, 90, origin=(0, 0)), "y", 6, [("P2", rotate(P2, 90, origin=(0, 0)))])
    eq("rotation 90: p.15 length unchanged", bottom_len(tr["A"])[1], 73.125)
    # millimetre drawings are scaled to metres before this module (metres only): 1000 x then 0.001 x is identical
    q = scale(scale(P1, 1000, 1000, origin=(0, 0)), 0.001, 0.001, origin=(0, 0))
    eq("mm -> m: face length unchanged", bottom_len(line_table(q, "x", 6, [])[1]["A"])[0], 78.0)
    # 2. L-shape 4 x 4 less the 2 x 2 top-right square, '5 ø 10 / m' in y, no neighbour (edge supports only)
    #    A: 20 lines at x = 0.1 .. 3.9: 10 x 4.0 + 10 x 2.0 = 60.0 m; B: 21 lines at x = 0, 0.2 .. 4.0: x <= 2.0
    #    (11 lines, the re-entrant line measured on the panel side) 4.0 m, 10 lines 2.0 m = 64.0 m; no curtailment
    Ls = Polygon([(0, 0), (4, 0), (4, 2), (2, 2), (2, 4), (0, 4)])
    H, tl = line_table(Ls, "y", 5, [])
    eq("L-shape A face 60.0, p.15 = face (no continuous end)", bottom_len(tl["A"])[1], 60.0)
    eq("L-shape B 64.0", bottom_len(tl["B"])[0], 64.0)
    # 3. panel 5 x 3 with a 1 x 1 opening (2..3, 1..2), '5 ø 10 / m' in x: A 15 lines at y = 0.1 .. 2.9; the five
    #    with 1 < y < 2 are cut in two (2.0 + 2.0): 10 x 5 + 5 x 4 = 70.0 m; B 16 lines, y = 1.0 / 2.0 on the opening
    #    edges taken on the panel side (5.0), y = 1.2 .. 1.8 four lines of 4.0: 80 - 4 = 76.0 m
    op = box(0, 0, 5, 3).difference(box(2, 1, 3, 2))
    H, to = line_table(op, "x", 5, [])
    eq("opening A 70.0", bottom_len(to["A"])[0], 70.0)
    eq("opening B 76.0", bottom_len(to["B"])[0], 76.0)
    #    the opening edge is not a beam support: a bar cut by the opening has no continuous end there
    eq("opening: no continuous end", ends(to["A"])[1], 0)
    # 4. missing reading: a '5 ø 10' label without '/m' on a 1.7 x 0.62 strip, bars in y: count reading 5 x 0.62 m
    H, th = line_table(box(0, 0, 1.7, 0.62), "y", 5, [])
    fA = bottom_len(th["A"])[0]
    eq("no-'/m' label: count reading 5 x 0.62 x 0.617284 = 1.914 kg (HELD)", 5 * (fA / len(th["A"])) * u10, 1.914)
    eq("no-'/m' label: rate reading ceil(5 x 1.7) = 9 bars (HELD)", len(th["A"]), 9)
    # 5. invalid input
    try:
        line_table(box(0, 0, 1, 0), "x", 5, [])
        ok = False
        print("empty extent not refused FAIL")
    except ValueError:
        print("empty extent refused PASS")
    print("CHECK", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "--check":
        sys.exit(0 if check() else 1)
    if a[0] == "build":
        build(*a[1:4])
    elif a[0] == "ledger":
        ledger(*(a[1:3]))
