"""T-174 Alsenan check: STRAP_BEAM_TAKEOFF_V1 on the structural DXF (Drive "Alsenan chalet project", "ST7757 dxf.dxf").

    .work/venv/bin/python -I research/agents_t174/run_t174_alsenan.py <structural.dxf> [--out <dir>]

Everything geometric is read from the drawing by DXF handle (nothing typed): the strap edge lines (S-FOOTINGS LINEs,
the same handles the frozen S5 strap register and T-073 / T-141 name), the footing outlines (S-FOOTINGS polylines; an
OPEN outline is closed by its chord, which is where the strap enters; the 'F' block inserts exploded), the column
outlines (S-COL.BON) at the strap ends. Printed values passed in with their source: the strap sections and bars from
ST7757.pdf p.10 "Schedule of Simple Beams" (SB1 70 x 50, 7 T16 bottom, 13 T18 top, 8 T8/m; SB2 100 x 50, 10 T16 / 20
T18, 10 T8/m (D-38 open: an off-sheet 80 x 50 row); SB3 50 x 40, 5 T16 / 5 T18, 7 T8/m), the footing thicknesses from
p.9 "Schedule of Footings" (F3 30, F6 50, F8 50, F10 50, F11 50, F15 40 cm), the development range 40 d .. 70 d from
p.8 note 9 (D-36: zone and end shape not printed, HELD). Unit mass: the project method D2_OVER_162 (rebar_unit_mass).
Writes T174_STRAPS.json (ids, lengths, quantities; no coordinates) next to this file or into --out.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from engine.source import rebar_unit_mass as UM  # noqa: E402
from engine.source import strap_beam_takeoff_v1 as SB  # noqa: E402

DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
ANCH = (40, 70)                                # p.8 note 9, HELD range (D-36)
STRAPS = [  # mark, edge handles, footing outlines (handle, schedule type, H m), column outline handles, printed section
    {"mark": "SB1", "edges": ("1689", "1B1C"), "footings": [("1B24", "F8", 0.50), ("1B1B", "F10+F", None)],
     "columns": ("10D0", "10E8"), "B": 0.70, "D": 0.50,
     "bars": [("BOTTOM", 7, 16), ("TOP", 13, 18)], "links": (8, 8)},
    {"mark": "SB2", "edges": ("1B08", "1B09"), "footings": [("1B07", "F11", 0.50), ("1B19", "F6", 0.50)],
     "columns": ("10DD", "10C2"), "B": 1.00, "D": 0.50,
     "bars": [("BOTTOM", 10, 16), ("TOP", 20, 18)], "links": (10, 8)},
    {"mark": "SB3", "edges": ("1B26", "1B27"), "footings": [("1B2A", "F15", 0.40), ("166B", "F3", 0.30)],
     "columns": ("10AE", "10B1"), "B": 0.50, "D": 0.40,
     "bars": [("BOTTOM", 5, 16), ("TOP", 5, 18)], "links": (7, 8)},
]
# F10 + F (1B1B): one open outline drawn around two schedule footings (owner Q-31: HELD); thickness F10 0.50 / F 0.30


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def outline(doc, h):
    e = doc.entitydb.get(h)
    if e.dxftype() == "LWPOLYLINE":
        return [tuple(map(float, p))[:2] for p in e.get_points("xy")]
    if e.dxftype() == "INSERT":
        for v in e.virtual_entities():
            if v.dxftype() == "LWPOLYLINE":
                return [tuple(map(float, p))[:2] for p in v.get_points("xy")]
    raise SystemExit(f"{h}: no outline")


def run(path):
    import ezdxf
    if sha(path) != DXF_SHA:
        raise SystemExit("structural DXF sha differs from the one this check was written for")
    doc = ezdxf.readfile(path)
    um = {"method": UM.D2_OVER_162, "authority": "Urban project default (R3)"}
    out = []
    for s in STRAPS:
        edges = []
        for h in s["edges"]:
            e = doc.entitydb.get(h)
            edges.append((tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]))
        feet = [{"support_id": f"{t} ({h})", "polygon": outline(doc, h), "H_m": H} for h, t, H in s["footings"]]
        cols = [{"support_id": h, "polygon": outline(doc, h)} for h in s["columns"]]
        st = {"strap_id": s["mark"], "mark": s["mark"], "edges": edges, "B_m": s["B"], "D_m": s["D"],
              "bars": [{"position": p, "count": c, "dia_mm": d} for p, c, d in s["bars"]],
              "links": {"per_m": s["links"][0], "dia_mm": s["links"][1]}, "anchorage_d": ANCH}
        out.append(SB.takeoff_strap(st, feet, cols, units="mm", unit_mass=lambda d: UM.kg_per_m(d, um)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("--out", default=HERE)
    a = ap.parse_args()
    res = run(a.dxf)
    with open(os.path.join(a.out, "T174_STRAPS.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    for r in res:
        L = r.get("lengths", {})
        print(r["mark"], r["status"], L.get("axis_face_to_face_m"), L.get("edge_face_to_face_m"),
              L.get("projection_gap_m"), L.get("corner_overreach_m"), r.get("concrete"), r["held"], r["flags"])
        print("   in footings:", r.get("concrete_in_footings"))
        print("   bars:", [(b["position"], b.get("kg_lb"), b.get("anchorage_kg")) for b in r["bars"]["groups"]],
              r["bars"]["links"] and r["bars"]["links"]["count_range"])
        print("   formwork:", r.get("formwork", {}).get("side_faces_m2"), r.get("footing_face_covered"))


if __name__ == "__main__":
    main()
