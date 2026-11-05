"""T-520 drawing reader (research only, NOT engine code): what a block wall's census run MEETS at each of its two ends.

Why: the T-274 run pieces cut each run at every column outline the run CROSSES, so a column inside the run is known.
A run that ends on the face of another wall (T_STEM, L) or stops (FREE_END) does not say what lies just beyond its end
face: the met wall's masonry, an RC column standing in the met wall, or nothing. The perimeter mortar joint at a
column face (T-520) exists only where the block end touches concrete, so every end is read here from the drawing.

Method (exact geometry, no tolerance on the drawn outlines): the end face strip [end, end + 0.02 m] beyond the run end
point, across the wall thickness inset 0.5 mm each side, is intersected with (a) every column outline of the storey's
architectural plan (the wall stage's own outlines, t125 capture) and (b) the storey masonry M of T-516 (every census
wall rectangle with junction caps, less columns and opening gaps). The covered fractions are written; the class is
COLUMN (column cover >= 0.999), PARTIAL_COLUMN (0 < cover < 0.999: HELD by the engineer), MASONRY (masonry cover >=
0.999), NONE (nothing: a free end) or MIXED. A run whose first / last T-274 piece is a COLUMN is reported as such.

Inputs (outside the repository, never committed): <scratch>/t125_inputs.pkl, <scratch>/t125_v2.json (T-125 tools on
Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf sha ab54dd55) and <scratch>/t274_runs.json
(research/agents_t274/t274_runs.py). Output: research/agents_t520/out/END_CONDITIONS_T520.csv, numbers and ids only.

    python3 -I research/agents_t520/t520_extract.py <scratch>
"""
import csv
import json
import math
import pickle
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "agents_t516"))
import t516_extract as T516  # noqa: E402
from shapely.geometry import Polygon  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

OUT = HERE / "out" / "END_CONDITIONS_T520.csv"
PROBE = 0.02
INSET = 0.0005
# the black walls of the T-367 / T-506 set (24 walls / pieces) and their census runs (register v2 'V2 run', T-274)
WALLS = {
    "GF-W01": ["GF|WB-FL0001-FL0002#2"], "GF-W19": ["GF|WB-FL0059-FL0060"], "GF-W21": ["GF|WB-FL0063-FL0064#1"],
    "GF-W22": ["GF|WB-FL0070-FL0072"], "GF-W28": ["GF|WB-FL0030-FL0031"], "GF-W29": ["GF|WB-FL0038-FL0039"],
    "GF-W33": ["GF|WB-FL0046-FL0047"], "1F-W02": ["1F|WB-FL0059-FL0061"], "1F-W03": ["1F|WB-FL0068-FL0070"],
    "1F-W09": ["1F|WB-FL0024-FL0025"], "1F-W12": ["1F|WB-FL0011-FL0012"], "1F-W13": ["1F|WB-FL0013-FL0014"],
    "1F-W17": ["1F|WB-FL0043-FL0044"], "1F-W18": ["1F|WB-FL0046-FL0047"], "1F-W19": ["1F|WB-FL0050-FL0051"],
    "1F-W20": ["1F|WB-FL0054-FL0055#1", "1F|WB-FL0054-FL0055#2"], "1F-W21": ["1F|WB-FL0059-FL0060"],
    "1F-W22": ["1F|WB-FL0063-FL0065"], "1F-W23": ["1F|WB-FL0074-FL0075"], "1F-W24": ["1F|WB-FL0078-FL0079"],
    "2F-W01": ["2F|WB-FL0006-FL0007"], "2F-W05": ["2F|WB-FL0024-FL0026"], "2F-W06": ["2F|WB-FL0031-FL0032"],
    "2F-W08": ["2F|WB-FL0024-FL0025"],
}


def probe(a, ux, uy, s0, s1, half):
    return T516.strip(a, ux, uy, min(s0, s1), max(s0, s1), half - INSET)


def main(scratch):
    S = Path(scratch)
    d = pickle.load(open(S / "t125_inputs.pkl", "rb"))
    v = json.load(open(S / "t125_v2.json"))
    runs = json.load(open(S / "t274_runs.json"))
    pieces = defaultdict(list)
    for x in csv.DictReader(open(ROOT / "research/agents_t274/T274_RUN_PIECES.csv")):
        pieces[x["run_key"]].append(x)
    cache, rows = {}, []
    for wid, rks in WALLS.items():
        for rk in rks:
            fl = rk.split("|")[0]
            if fl not in cache:
                cache[fl] = T516.storey(d["floors"][fl], v["floors"][fl]["v2"])
            W, ax, M, cols, gaps, _r = cache[fl]
            R = runs[rk]
            (a, b), L, t = R["segment"], R["seg_len"], float(R["t_m"])
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            ps = pieces[rk]
            colU = unary_union(cols)
            for end, s, sign in ((0, 0.0, -1), (1, L, +1)):
                P = probe(a, ux, uy, s, s + sign * PROBE, t / 2)
                cc = P.intersection(colU).area / P.area
                mm = P.intersection(M).area / P.area
                inner = ps[0] if end == 0 else ps[-1]
                if inner["kind"] == "COLUMN":
                    cls = "COLUMN_PIECE_IN_RUN"
                elif cc >= 0.999:
                    cls = "COLUMN"
                elif cc > 1e-6:
                    cls = "PARTIAL_COLUMN"
                elif mm >= 0.999:
                    cls = "MASONRY"
                elif mm <= 1e-6:
                    cls = "NONE"
                else:
                    cls = "MIXED"
                rows.append({"wall_id": wid, "run": rk, "end": end, "run_end_type": R["ends"][end],
                             "run_ext_m": f"{R['ext'][end]:.4f}", "inner_piece": inner["kind"],
                             "column_cover": f"{cc:.4f}", "masonry_cover": f"{mm:.4f}", "class": cls})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r["wall_id"], r["run"], r["end"], r["run_end_type"], r["inner_piece"], r["column_cover"],
              r["masonry_cover"], r["class"])


if __name__ == "__main__":
    main(sys.argv[1])
