"""T-323: what the research ledgers that READ a sunken-slab hatch outline get when the outline is replaced by the panel
rebuilt from the drawn member faces (research only; nothing wired; no BOQ line moved).

Consumers re-run (their own code, unchanged; only the panel polygon handed to them differs):
  - T-213 (research/agents_t213, MERGED): A, P, P_ext, P_shared per panel -> the d-driven HELD formulas
    (step riser +P_ext d, beam side -P_ext d, fill A d, WP upturn P_ext d);
  - T-288 (research/agents_t288, MERGED): wall centreline / faces under each sunken panel (its clip region is the
    hatch region WITH the annotation-island loops united back, `_with_islands`).
Reads the PRIVATE drawings at run time (.work/private: 'ST7757 dxf.dxf' as ST7757.dxf; P7757_DXF_COMPRESSED.zip ->
P7757_DXF_COMPRESSED/P7757.dxf) and prints / writes numbers and ids only (CONSUMERS_T323.json).

    python3 -I research/agents_t323/consumers_t323.py <private folder> [--write]
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, ROOT / "research" / "agents_t139", ROOT / "research" / "agents_t213", ROOT / "research" / "agents_t288"):
    sys.path.insert(0, str(p))
import alsenan_clip_t288 as C  # noqa: E402
import alsenan_t213 as T213  # noqa: E402
import alsenan_t323 as A  # noqa: E402
import slab_hatch_edges as E  # noqa: E402
import sunken_panels as SP  # noqa: E402

SUNKEN = ("275", "276", "280", "287", "298", "5BF")


def member_panels(private):
    """{handle: (hatch region with islands as T-288 builds it, member-face panel)} for the six sunken hatches."""
    from shapely import wkt
    doc, hatches, members, frees, anns = A.read(Path(private) / A.DXF_NAME)
    faces = {sh: [wkt.loads(f["wkt"]) for f in A.T139.faces(doc, win)] for sh, win in A.T139.SHEETS.items()}
    out = {}
    for hd, pat, sc, loops in hatches:
        if hd not in SUNKEN:
            continue
        x = sum(p[0] for p in loops[0]) / len(loops[0])
        y = sum(p[1] for p in loops[0]) / len(loops[0])
        sh = A.sheet_of(x, y)
        c = E.classify_boundary(loops, member_lines=members, free_lines=frees, annotations=anns)
        reb = E.rebuild_panel(c, faces[sh], annotations=anns)
        if reb["status"] != "DRAWING-CONFIRMED":
            raise SystemExit(f"{hd}: panel not rebuilt ({reb['why']})")
        out[hd] = reb["panel"]
    return out


def t213_effect(private, panels):
    hatches, ann, _u = T213.read_dxf(Path(private) / T213.DXF_NAME)
    from shapely.geometry import Polygon
    by_hatch, by_panel = [], []
    for hd, loops in hatches:
        seed = max((Polygon(lp).buffer(0) for lp in loops), key=lambda p: p.area)
        p = SP.build_panel(hd, T213.sheet_of(seed), loops, ann)
        by_hatch.append(p)
        q = copy.copy(p)
        q.polygon = panels[hd]
        by_panel.append(q)
    eh = SP.classify_edges(by_hatch, max_beam_m=T213.MAX_BEAM_M)
    ep = SP.classify_edges(by_panel, max_beam_m=T213.MAX_BEAM_M)
    rows = {}
    for ph, pp in zip(by_hatch, by_panel):
        rows[ph.pid] = {"A_hatch_m2": round(ph.area, 4), "A_panel_m2": round(pp.area, 4),
                        "P_hatch_m": round(ph.perimeter, 4), "P_panel_m": round(pp.perimeter, 4),
                        "P_ext_hatch_m": round(eh[ph.pid]["P_ext"], 4), "P_ext_panel_m": round(ep[pp.pid]["P_ext"], 4),
                        "P_shared_hatch_m": round(eh[ph.pid]["P_shared"], 4),
                        "P_shared_panel_m": round(ep[pp.pid]["P_shared"], 4)}
    return rows


def t288_effect(private, panels):
    base = C.run(private)
    orig_with, orig_build = C._with_islands, SP.build_panel

    def build(pid, storey, loops, ann=(), anchor_tol=0.02):
        p = orig_build(pid, storey, loops, ann, anchor_tol)
        p.polygon = panels[pid]
        return p

    try:
        C._with_islands = lambda p, loops: panels[p.pid]
        C.SP.build_panel = build
        alt = C.run(private)
    finally:
        C._with_islands, C.SP.build_panel = orig_with, orig_build
    walls = {}
    for wid in sorted(set(base["walls"]) | set(alt["walls"])):
        b, a = base["walls"].get(wid, {}).get("under", {}), alt["walls"].get(wid, {}).get("under", {})
        for face in sorted(set(b) | set(a)):
            bb, aa = b.get(face, {}), a.get(face, {})
            walls[f"{wid} under {face}"] = {
                k: [bb.get(k), aa.get(k)] for k in ("axis_in_hatch_m", "hatch_to_column_gap_m", "axis_under_panel_m",
                                                    "exclusive_under_panel_m")}
    clip_area = {pid: [base["panels"][pid]["area_with_annotation_islands_m2"],
                       alt["panels"][pid]["area_with_annotation_islands_m2"]] for pid in base["panels"]}
    return {"walls_hatch_vs_panel": walls, "clip_region_m2_hatch_vs_panel": clip_area,
            "unclaimed_hatch_vs_panel": [base["unclaimed"], alt["unclaimed"]],
            "face_lines_inside_hatch_vs_panel": {pid: [base["panels"][pid]["face_lines_inside"],
                                                       alt["panels"][pid]["face_lines_inside"]] for pid in base["panels"]}}


def run(private):
    panels = member_panels(private)
    return {"t213": t213_effect(private, panels), "t288": t288_effect(private, panels)}


if __name__ == "__main__":
    res = run(sys.argv[1])
    txt = json.dumps(res, indent=1, ensure_ascii=True)
    if "--write" in sys.argv:
        (HERE / "CONSUMERS_T323.json").write_text(txt + "\n")
    print(txt)
