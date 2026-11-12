"""T-743 arch side, read-only: every ARCH_TAKEOFF_V2.9 space of a plan with the sanitary evidence the architectural
plan itself holds (fixture blocks, WC linework, drain marks), by WET_ROOM_EVIDENCE_V1.plan_evidence, plus the insert
point of every fixture block in metres. Writes JSON to --out (outside the repository); nothing in the repo changes.
Usage: python3 -I research/agents_t743/t743_arch_dump.py <arch.dxf> --out <scratch>/t743_arch.json
Counts, block names, engine room ids and coordinates only: no client data."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t010"))


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from alsenan_wet_run import read_plan            # the T-010 reader composition (architectural route)
    from engine.source import wet_room_evidence as W
    from tools import urban_boq_m9 as M
    _boq, arch, _ = M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.9")
    ents = read_plan(a.drawing)
    u = ents["unit_m"]
    roles = {r["floor"]: r["layer_roles"] for r in arch["regions"]}
    ins = {i["id"]: i for i in ents.get("inserts") or ()}
    rows = []
    for r in arch["rooms"]:
        ev = W.plan_evidence(r["polygon"], ents, roles[r["floor"]], u, r.get("hole_polygons") or ())
        fx = []
        for f in ev["fixtures"]:
            i = ins.get(f["id"]) or {}
            b = i.get("box")
            x, y = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) if b else (i.get("x"), i.get("y"))
            fx.append({"kind": f["kind"], "block": f["block"], "layer": f.get("layer"), "id": f["id"],
                       "at_m": [round(x * u, 3), round(y * u, 3)] if x is not None else None})
        xs = [p[0] for p in r["polygon_m"]]
        ys = [p[1] for p in r["polygon_m"]]
        rows.append({"room_id": r["room_id"], "floor": r["floor"], "class": r["class"], "codes": r["codes"],
                     "area_m2": round(r["area_m2"], 4), "bbox_m": [round(min(xs), 3), round(min(ys), 3),
                                                                  round(max(xs), 3), round(max(ys), 3)],
                     "polygon_m": [[round(p[0], 4), round(p[1], 4)] for p in r["polygon_m"]],
                     "labels": ev["labels"]["codes"], "fixtures": fx,
                     "wc_linework": len(ev["wc_linework"]), "drains": [d["kind"] for d in ev["drains"]]})
    frames = [{"floor": g["floor"], **{k: g[k] for k in ("bbox_m",) if k in g}} for g in arch["regions"]]
    Path(a.out).write_text(json.dumps({"method": "ARCH_TAKEOFF_V2.9", "unit_m": u, "frames": frames,
                                       "rooms": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(x["fixtures"]) for x in rows)
    print(f"rooms {len(rows)} fixture blocks inside rooms {n} wc linework {sum(x['wc_linework'] for x in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
