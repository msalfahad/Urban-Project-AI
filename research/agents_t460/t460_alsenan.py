"""T-460 item C5 on the development villa: SMALL_OPENING_CENSUS_V1 on every plan frame of the architectural DXF, through
the candidate's own robust band path (robust_geometry.openings with a Geometry, ARCH_TAKEOFF_V2.7 layer roles and column
shapes), so the ONLY difference from the engine's opening list is the 0.50 m minimum.

usage: python3 -I research/agents_t460/t460_alsenan.py <P7757.dxf> [--write]
The DXF is the owner's private file (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip, decoded only into
.work/private). The output holds widths, classes, statuses and entity handles only: no coordinate, text or name.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import small_opening_census_v1 as SC  # noqa: E402

OUT = Path(__file__).resolve().parent
COLS = ["floor", "probe_id", "cls", "status", "width_m", "wall_t_m", "start_jamb", "end_jamb", "split_at_column",
        "glazing_m", "glazing_ids", "crossing_faces", "swing", "reason"]


def frames(dxf):
    from tools import arch_intake as AI
    from tools import urban_intake as UI
    from engine.source import arch_plan as AP
    E = UI.read(str(dxf))
    A = AI.read_arch(Path(dxf), unit_m=E.get("unit_m"))
    chords = AI.ellipse_chords(E.get("ellipses") or [], E["unit_m"])
    E = dict(E, hatches=[dict(h, ring=h["rings"][0]) for h in A["hatches"] if h["rings"]], texts=A["texts"],
             inserts=A["inserts"], segments=E["segments"] + A["extra_segments"] + chords, arcs=E["arcs"] + A["extra_arcs"])
    u = E["unit_m"]
    P = AP.plan_regions(E, split="EMPTY_BANDS", frames_from_lines_fallback=True)
    for r in P["regions"]:
        ents = AP.region_entities(E, r["box"])
        b = r["box"]
        eps = max(1e-3 / u, max(b[2] - b[0], b[3] - b[1]) * 1e-6)
        ents = dict(ents, segments=[s for s in ents["segments"] if not AP._on_frame_side(s["a"], s["b"], b, eps)])
        yield r["region_id"], ents, u


def run(dxf):
    from engine.source import arch_plan as AP
    from engine.source import arch_rooms as AR
    from engine.source import arch_v27 as V27
    from engine.source import robust_geometry as RG
    rows, summ = [], {}
    for rid, ents, u in frames(dxf):
        L = V27.layer_roles(ents, u, tol="UNIT_RELATIVE", geom=RG.Geometry(u))
        if L.get("state") == "BLOCKED":
            summ[rid] = {"state": "BLOCKED"}
            continue
        roles = L["roles"]
        wall_l = sorted(k for k, v in roles.items() if v == AP.WALL)
        win_l = {k for k, v in roles.items() if v == AP.WINDOW}
        door_l = {k for k, v in roles.items() if v == AP.DOOR}
        cols = AR._columns(ents, roles, u, "UNIT_RELATIVE")
        boxes, _polys = V27.column_shapes(ents, roles, u)
        same = 1e-3 / u
        cols = cols + [x for x in boxes if not any(all(abs(p - q) <= same for p, q in zip(x, c)) for c in cols)]
        swings = AR.door_swings(ents, door_l, u, path=True)
        res = SC.census(ents["segments"], u, wall_l, cols, window_layers=win_l, swings=swings,
                        geom_factory=RG.Geometry, region_id=rid)
        # the engine's own opening list for the frame (arch_rooms.spaces, V2.7 flags of the candidate path)
        S = AR.spaces(ents, roles, u, region_id=rid, tol="UNIT_RELATIVE", geom=RG.Geometry(u), release_safety=True,
                      door_review=True, v27=True)
        floor = rid.split(":")[-1]
        summ[floor] = dict(res["summary"], spaces_openings=len([o for o in S["openings"] if not o.get("curved")]))
        for r in res["records"]:
            if not r["probe_id"]:
                continue
            ev = r["evidence"]
            rows.append({"floor": floor, "probe_id": f"{floor}-{r['probe_id']}", "cls": r["cls"], "status": r["status"],
                         "width_m": f"{r['width_m']:.4f}", "wall_t_m": f"{r['wall_t_m']:.3f}",
                         "start_jamb": r["start_jamb"], "end_jamb": r["end_jamb"],
                         "split_at_column": r["split_at_column"], "glazing_m": ev.get("glazing_m", ""),
                         "glazing_ids": " ".join(ev.get("glazing_ids", [])),
                         "crossing_faces": json.dumps(ev.get("crossing_faces", ""), sort_keys=True) if ev.get("crossing_faces") else "",
                         "swing": ev.get("swing", "") or "", "reason": r.get("reason", "")})
    return rows, summ


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    dxf = Path(a[0])
    rows, summ = run(dxf)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    out = {"source": {"file": "P7757.dxf", "sha256_8": hashlib.sha256(dxf.read_bytes()).hexdigest()[:8]},
           "frames": summ}
    txt = json.dumps(out, indent=1, sort_keys=True) + "\n"
    if "--write" in a:
        (OUT / "SMALL_OPENINGS_T460.csv").write_text(buf.getvalue())
        (OUT / "summary_c5.json").write_text(txt)
    print(buf.getvalue())
    print(txt)


if __name__ == "__main__":
    main()
