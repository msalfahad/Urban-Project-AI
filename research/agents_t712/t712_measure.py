"""T-712: drawn plan outline of every one of the 20 HELD BLANK STR.CONC.GROUND_BEAM lines of ARCH_TAKEOFF_V3.0.70,
measured from the structural DXF by entity handle (own outlines; the vertex grammar and the arc walk are T-658's
`outline()` from research/agents_t658/t658_measure_bands.py, imported read-only, not edited).

The DXF is the owner's private drawing: it is read from the path given on the command line (decoded by the wrapper into
.work/private only) and NEVER copied. This file carries no coordinate: each outline is a list of vertex rules over band /
column / face handles; the output carries only derived member figures (area m2 at 9 dp, edge lengths in m, the width)
plus the DXF sha256 prefix. The exact area (9 dp) is what the floors multiply; nothing is rounded up.

Ownership (R-CONC-OWN-1, lessons T-666 / T-669): every outline stops on a column outline of the GROUND-BEAM frame
(S-COL.BON, ST p.3) or on the face of the band that owns the junction; the junction squares are assigned in RUNS below,
one owner each, and the test checks that no two outlines and no column overlap.

Run: python -I research/agents_t712/t712_measure.py <decoded ST dxf>  -> research/agents_t712/out/T712_AREAS.json
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t658"))
import t658_measure_bands as M  # noqa: E402  (outline grammar, read only)

OUT = HERE / "out" / "T712_AREAS.json"
ARC = M.ARC_STEPS

# GB-frame columns (S-COL.BON on ST p.3) the outlines stop on: 207 / 20B / 204 / 214 / 211 / 223 / 22C (annex),
# 230 (C7), 1E8 (C4). Segment index i of a column polyline = vertex i -> i+1.
RUNS = {
    # ---- annex exterior (D-35): top +0.25 (approved), underside 'Outer Normal ground level' N.G. +-0.00 (approved)
    "BAND0015#1": {"line": "L-402dbe61d1c924144a3c", "edges": ("F8", "7D4"),        # south band, col 207 -> col 20B
                   "outline": [("X", "F8", "207#0"), ("X", "F8", "20B#2"), ("X", "7D4", "20B#2"), ("X", "7D4", "207#0")]},
    "BAND0015#2": {"line": "L-402dbe61d1c924144a3c", "edges": ("F8", "7D4"),        # col 20B -> east band inner face 7D1
                   "outline": [("X", "F8", "20B#0"), ("X", "F8", "7D1"), ("X", "7D4", "7D1"), ("X", "7D4", "20B#0")]},
    "BAND0012.1": {"line": "L-6bf14711798e5af93594", "edges": ("10B", "7D1"),       # SE corner square (T-669) -> col 22C
                   "outline": [("X", "10B", "F8"), ("X", "7D1", "F8"), ("X", "7D1", "22C#0"), ("X", "10B", "22C#0")]},
    "BAND0012.2": {"line": "L-3284f44000c02179ace7", "edges": ("10B", "7D1"),       # col 22C -> col 223
                   "outline": [("X", "10B", "22C#2"), ("X", "7D1", "22C#2"), ("X", "7D1", "223#0"), ("X", "10B", "223#0")]},
    "BAND0016": {"line": "L-4783c6e18002c3a8a37e", "edges": ("136", "7D5"),         # west band, col 207 -> col 204
                 "outline": [("X", "136", "207#1"), ("X", "7D5", "207#1"), ("X", "7D5", "204#0"), ("X", "136", "204#0")]},
    "BAND0035": {"line": "L-00465df980165c529476", "edges": ("137", "138"),         # north band, col 204 -> col 214
                 "outline": [("X", "137", "204#1"), ("X", "138", "204#1"), ("X", "138", "214#0"), ("X", "137", "214#0")]},
    "BAND0042": {"line": "L-e16c98075f69532a3dc7", "edges": None,                   # quarter ring r 1.00 .. 1.30
                 # col 214 east face meets the ring ends tangentially, so the ends are taken on that face (X) and on
                 # the drawn ends of 7D6 / 13E (both end on the ring), never by a tangent intersection
                 "outline": [("X", "138", "214#2"), ("ARC", "13A", ARC), ("E", "7D6", 1), ("E", "13E", 1),
                             ("ARC", "139", ARC), ("X", "137", "214#2")]},
    "BAND0017.2": {"line": "L-b4a13a43967ee4765662", "edges": ("13E", "7D6"),       # face 13D -> ring end (y of 13E end)
                   "outline": [("X", "13E", "13D"), ("X", "7D6", "13D"), ("E", "7D6", 1), ("E", "13E", 1)]},
    "BAND0013.2": {"line": "L-d8b98b143e293d30833b", "edges": ("13D", "7D2"),       # col 211 -> col 223
                   "outline": [("X", "13D", "211#0"), ("X", "7D2", "211#0"), ("X", "7D2", "223#3"), ("X", "13D", "223#3")]},
    "BAND0013.1": {"line": "L-be6708e07b40efa02779", "edges": ("13D", "7D2"),       # junction remainder: face 7D6 -> col 211
                   "outline": [("X", "13D", "7D6"), ("X", "7D2", "7D6"), ("X", "7D2", "211#2"), ("X", "13D", "211#2")]},
    # ---- court (yard side) exterior beams: top and underside datum not printed
    "BAND0002.1": {"line": "L-62243c74c430d383be86", "edges": ("185", "7C7"),       # col 230 (C7) -> main west face 109
                   "outline": [("X", "185", "230#0"), ("X", "7C7", "230#0"), ("X", "7C7", "109"), ("X", "185", "109")]},
    "BAND0022": {"line": "L-21795b350fbd09150c43", "edges": ("178", "7DB"),         # face 145 -> face 7C7 (col 230 above)
                 "outline": [("X", "178", "145"), ("X", "7DB", "145"), ("X", "7DB", "7C7"), ("X", "178", "7C7")]},
    "BAND0041:RUN": {"line": "L-a55bfa01b726ef11650c", "edges": ("1811", "1812"),   # col 1E8 east face -> drawn end
                     "outline": [("E", "1811", 0), ("E", "1811", 1), ("E", "1812", 1), ("X", "1812", "1E8#2")]},
    "BAND0041:STRIP": {"line": "L-a55bfa01b726ef11650c", "edges": None,             # 1812 runs on under col 1E8 to face 108
                       "outline": [("X", "1812", "1E8#2"), ("X", "1812", "108"), ("V", "1E8", 1), ("V", "1E8", 2)]},
}
# ---- loaded runs (D-33): T-658 r2 outlines re-measured here with the same handles (Verifier Gate A PASS 2026-11-10)
for k in ("BAND0037.1", "BAND0008.2", "BAND0040", "BAND0019", "BAND0010.3", "BAND0008.1", "BAND0023:7DC+7DD#1",
          "BAND0032:7E7+7E8#2"):
    RUNS[k] = dict(M.RUNS[k])
D33_LINES = {"BAND0037.1": "L-0bb78accf8c0a0fbdbaf", "BAND0008.2": "L-d53e5eb08e2c6c668254",
             "BAND0040": "L-a8c5c32c7a785c1e3f05", "BAND0019": "L-1487bdda099006e0c4ba",
             "BAND0010.3": "L-5af89b9f1e5b90daf8f5", "BAND0008.1": "L-e24946df436cbc25fca6",
             "BAND0023:7DC+7DD#1": "L-95a1f198cfe7f398d6ae", "BAND0032:7E7+7E8#2": "L-cfb4555cb26b39934bff"}
for k, lid in D33_LINES.items():
    RUNS[k]["line"] = lid

GB_FRAME_COLUMNS = ("207", "20B", "204", "214", "211", "223", "22C", "230", "1E8", "245", "23C", "7F5", "7ED", "1EF")


def _area(pts):
    return M._area(pts)


def measure(dxf_path: str) -> dict:
    import ezdxf  # noqa: PLC0415
    from shapely.geometry import Polygon  # noqa: PLC0415
    raw = Path(dxf_path).read_bytes()
    doc = ezdxf.readfile(dxf_path)
    res, polys = {}, {}
    for rid, spec in RUNS.items():
        pts = M.outline(doc, {"outline": spec["outline"]})
        a = _area(pts) / 1e6
        polys[rid] = Polygon(pts)
        r = {"line_id": spec["line"], "area_m2": f"{a:.9f}", "outline_rules": [list(map(str, v)) for v in spec["outline"]]}
        if spec.get("edges"):
            (a1, a2), (b1, b2) = M._ln(doc, spec["edges"][0]), M._ln(doc, spec["edges"][1])
            nx, ny = a2[1] - a1[1], -(a2[0] - a1[0])
            w = abs((b1[0] - a1[0]) * nx + (b1[1] - a1[1]) * ny) / math.hypot(nx, ny)
            r["width_m"] = f"{w / 1000:.6f}"
            r["length_on_width_m"] = f"{a / (w / 1000):.6f}"
        res[rid] = r
    # one owner per piece of concrete: no two outlines overlap, and no outline enters a GB-frame column
    overl = []
    keys = sorted(polys)
    for i, p in enumerate(keys):
        for q in keys[i + 1:]:
            ar = polys[p].intersection(polys[q]).area / 1e6
            if ar > 1e-9:
                overl.append([p, q, f"{ar:.9f}"])
    cols = {}
    for h in GB_FRAME_COLUMNS:
        e = doc.entitydb.get(h)
        if e is not None and e.dxftype() == "LWPOLYLINE":
            cols[h] = Polygon([tuple(v[:2]) for v in e.get_points()])
    col_hits = [[r, h, f"{polys[r].intersection(c).area / 1e6:.9f}"] for r in keys for h, c in cols.items()
                if polys[r].intersection(c).area / 1e6 > 1e-9]
    return {"schema": "T712_AREAS_V1", "source": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (ST p.3 GB frame)",
            "dxf_sha256_16": hashlib.sha256(raw).hexdigest()[:16], "units": "drawing mm -> m",
            "runs": res, "overlaps_between_outlines": overl, "outline_inside_column": col_hits,
            "columns_checked": sorted(cols)}


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: t712_measure.py <decoded ST dxf in .work/private>")
    out = measure(sys.argv[1])
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: (v["area_m2"], v.get("length_on_width_m")) for k, v in out["runs"].items()}, indent=1))
    print("overlaps", out["overlaps_between_outlines"], "in columns", out["outline_inside_column"])


if __name__ == "__main__":
    main()
