"""T-510 on the development villa: BAND_GAP_CLASSES_V1 on every plan frame of the architectural DXF through the
candidate's own robust band path (robust_geometry Geometry, ARCH_TAKEOFF_V2.7 layer roles and column shapes), with NO
project ledger, and a census diff against the released band path (every engine opening must come back ENGINE with the
same band, s0 and s1; every other record is listed by class).

usage: python3 -I research/agents_t510/t510_alsenan.py <P7757.dxf> [--write]
The DXF is the owner's private file (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip, decoded only into
.work/private). Output: widths, classes, statuses, bounds and entity handles only; no coordinate, text or name.
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
sys.path.insert(0, str(ROOT / "research" / "agents_t460"))

from engine.source import band_gap_classes_v1 as BG  # noqa: E402
import t460_alsenan as T460  # noqa: E402  (the same frame reader as the Checker-verified T-460 census)

OUT = Path(__file__).resolve().parent
COLS = ["floor", "gap_id", "cls", "kind", "status", "width_m", "wall_t_m", "start_bound", "end_bound",
        "split_at_column", "column_pieces", "engine_opening", "differs_from_engine", "glazing_m", "glazing_ids",
        "crossing_faces"]


def run(dxf):
    from engine.source import arch_plan as AP
    from engine.source import arch_rooms as AR
    from engine.source import arch_v27 as V27
    from engine.source import robust_geometry as RG
    rows, summ = [], {}
    for rid, ents, u in T460.frames(dxf):
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
        geom = RG.Geometry(u)
        geom.context = rid
        res = BG.classify(ents["segments"], u, wall_l, cols, window_layers=win_l, swings=swings, geom=geom)
        floor = rid.split(":")[-1]
        summ[floor] = res["summary"]
        for r in res["records"]:
            if r["status"] in ("ENGINE", "ENGINE_REJECTED") and not r["differs_from_engine"]:
                continue
            ev = r["evidence"]
            rows.append({"floor": floor, "gap_id": f"{floor}-{r['gap_id']}", "cls": r["cls"], "kind": r["kind"] or "",
                         "status": r["status"], "width_m": f"{r['width_m']:.6f}", "wall_t_m": f"{r['wall_t_m']:.3f}",
                         "start_bound": r["start_bound"], "end_bound": r["end_bound"],
                         "split_at_column": r["split_at_column"], "column_pieces": len(r["column_pieces"]),
                         "engine_opening": r["engine_opening"], "differs_from_engine": r["differs_from_engine"],
                         "glazing_m": ev.get("glazing_m", ""), "glazing_ids": " ".join(ev.get("glazing_ids", [])),
                         "crossing_faces": json.dumps(ev["crossing_faces"], sort_keys=True)
                         if ev.get("crossing_faces") else ""})
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
           "policy": BG.policy_record(), "frames": summ}
    txt = json.dumps(out, indent=1, sort_keys=True) + "\n"
    if "--write" in a:
        (OUT / "BAND_GAP_CLASSES_T510.csv").write_text(buf.getvalue())
        (OUT / "summary_t510.json").write_text(txt)
    print(buf.getvalue())
    print(txt)


if __name__ == "__main__":
    main()
