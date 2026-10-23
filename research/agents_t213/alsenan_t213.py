"""T-213 on the development villa: the six 'Sunken slab.' panels of the structural DXF as physical elements.

Reads the PRIVATE structural DXF (Drive "Alsenan chalet project", "ST7757 dxf.dxf", decoded into .work/private) at run
time and writes only numbers, handles and ids (no coordinates, no drawing content) to SUNKEN_PANELS_T213.json.

Reading rules (from the drawing's own legend, ST7757.pdf p.3-p.6): 'Sunken slab.' = HATCH ANSI31 at pattern scale 2000
on layer S-HAT.BAT (the 'Cantilever-portion.' hatch is ANSI31 at scale 800 on the same layer, so the scale decides).
Annotation anchors = TEXT / MTEXT insertion points and INSERT points (the slab-thickness tag 'T 16' is an INSERT).
The sheet storey of a panel is the slab sheet that draws it (DXF x range of the GF-roof-slab frame vs the 1F-roof-slab
frame, the T-139 convention); the floor it carries is the storey above.

    python3 -I research/agents_t213/alsenan_t213.py <private folder> [--write]
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import sunken_panels as S  # noqa: E402

DXF_NAME = "ST7757.dxf"
SUNKEN = {"layer": "S-HAT.BAT", "pattern": "ANSI31", "scale": 2000.0}
# Slab-sheet frames in DXF metres (x ranges of the two 31.37 m plot frames that hold the six hatches; T-139 ids
# GF-xxx / 1F-xxx follow the same split). Only used to name the sheet storey.
SHEET_X = {"GF": (40.0, 75.0), "1F": (0.0, 39.9)}
# Thickness printed for each panel (DXF text / tag; ST7757.pdf p.8 general note 18 'roof slabs 16 cm unless otherwise
# stated'): source strings are references, not quotes.
T_PRINTED = {"280": (0.16, "panel tag INSERT 't' = 'T 16' inside the panel (ST DXF / ST7757.pdf p.4)")}
T_NOTE = (0.16, "ST7757.pdf p.8 general note 18 (slab 16 cm unless stated); no other thickness printed in the panel")
# Widest scheduled beam (ST7757.pdf p.10 simple-beam schedule: B27 90 x 85, the oblique beam between 280 / 287).
MAX_BEAM_M = 0.90 + 0.05
# Every hatch edge is a beam or column face: 5 of the 6 hatch regions equal T-139's beam / column-face polygons to
# 0.0000 m2 and 298 to 0.0100 m2 (its B28 / column corner); the boundary marks are listed in BEAMS.
EDGE_BASIS = "hatch = T-139 beam / column-face polygon (5 of 6 exact, 298 -0.0100 m2); beams per BEAMS"
# Beams named on each panel's boundary (S-TEXT labels read on the plan), for lane I's beam-side adjustment.
BEAMS = {"275": "B1, B4 (+ the beam between 275 / 276)", "276": "B1 (+ the beam between 275 / 276)",
         "280": "B1, B5, CB5, B27 (oblique, shared with 287)", "287": "B1, CB4, B27 (shared with 280)",
         "298": "B4, B17, B28 (+ column at the B28 corner)", "5BF": "B2"}


def read_dxf(path):
    import ezdxf
    from ezdxf import bbox, path as P
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    ann = []
    for e in msp:
        t = e.dxftype()
        try:
            if t in ("TEXT", "MTEXT"):
                b = bbox.extents([e])
                ann.append((b.extmin.x / 1000, b.extmin.y / 1000, b.extmax.x / 1000, b.extmax.y / 1000,
                            (e.dxf.text if t == "TEXT" else e.text)[:20]))
            elif t == "INSERT":
                ins = e.dxf.insert
                ann.append((ins.x / 1000, ins.y / 1000, "INSERT:" + e.dxf.name))
        except Exception:      # an entity without an insertion point is not an anchor
            continue
    hatches = []
    for h in msp.query("HATCH"):
        if (h.dxf.layer, h.dxf.pattern_name, float(h.dxf.pattern_scale)) != (SUNKEN["layer"], SUNKEN["pattern"],
                                                                             SUNKEN["scale"]):
            continue
        loops = [[(v.x / 1000, v.y / 1000) for v in P.from_hatch_boundary_path(bp).flattening(0.5)] for bp in h.paths]
        hatches.append((h.dxf.handle, loops))
    return hatches, ann, doc.header.get("$INSUNITS")


def sheet_of(panel_poly):
    x = panel_poly.centroid.x
    for st, (a, b) in SHEET_X.items():
        if a <= x <= b:
            return st
    raise S.PanelError("panel outside both slab-sheet frames")


def t139_areas():
    f = ROOT / "research" / "agents_t139" / "PANELS.csv"
    out = {}
    with f.open() as fh:
        for r in csv.DictReader(fh):
            if "Sunken" in r["evidence"]:
                out[r["id"]] = float(r["area"])
    return out


def run(private):
    hatches, ann, units = read_dxf(Path(private) / DXF_NAME)
    if units != 4:
        raise S.PanelError(f"DXF units {units}, expected 4 (mm)")
    panels = []
    for hd, loops in hatches:
        from shapely.geometry import Polygon
        seed = max((Polygon(lp).buffer(0) for lp in loops), key=lambda p: p.area)
        panels.append(S.build_panel(hd, sheet_of(seed), loops, ann))
    edges = S.classify_edges(panels, max_beam_m=MAX_BEAM_M)
    rows = []
    for p in sorted(panels, key=lambda p: (S.STOREYS.index(p.sheet_storey), p.pid)):
        t, ts = T_PRINTED.get(p.pid, T_NOTE)
        e = edges[p.pid]
        q = S.panel_quantities(p, e, t_m=t, t_source=ts, edges_on_beams=EDGE_BASIS)
        minx, miny, maxx, maxy = p.polygon.bounds
        rows.append({
            "handle": p.pid, "sheet": f"{p.sheet_storey} roof slab", "floor_carried": S.floor_carried(p.sheet_storey),
            "area_m2": round(p.area, 4), "area_status": p.area_status, "perimeter_m": round(p.perimeter, 4),
            "P_ext_m": round(e["P_ext"], 4), "P_shared_m": round(e["P_shared"], 4),
            "shared_with": {k: round(v, 4) for k, v in e["shared_with"].items()}, "shared_gap_m": e["gap_m"],
            "bbox_m": [round(maxx - minx, 3), round(maxy - miny, 3)], "region_loops": p.region_loops,
            "annotation_islands": p.annotation_islands, "unexplained_voids": p.unexplained_voids,
            "boundary_beams": BEAMS.get(p.pid, ""), "t_m": t, "t_source": ts, "drop_m": None,
            "drop_status": "HELD (no sheet prints it; designer item D-41)", "quantities": q})
    t139 = t139_areas()
    pairs, ua, ub = S.match_sets(t139, {r["handle"]: r["area_m2"] for r in rows})
    return {"panels": rows, "t139_match": {"pairs": pairs, "unmatched_t139": ua, "unmatched_dxf": ub},
            "totals": {st: round(sum(r["area_m2"] for r in rows if r["floor_carried"] == st), 4) for st in ("1F", "2F")}}


if __name__ == "__main__":
    res = run(sys.argv[1])
    txt = json.dumps(res, indent=1, ensure_ascii=True)
    if "--write" in sys.argv:
        (HERE / "SUNKEN_PANELS_T213.json").write_text(txt + "\n")
    print(txt)
