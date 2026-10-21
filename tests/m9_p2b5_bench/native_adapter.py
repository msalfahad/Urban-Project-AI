"""NATIVE ADAPTER - runs the Urban engine on a benchmark DXF through its own command line (a separate process, so
nothing of the engine is imported here) and reads back the rooms and openings it reports, in a common form:

    {"rooms": [{"name", "codes", "area_m2", "perimeter_m", "polygon_mm", "holes_mm", "flags"}],
     "openings": [{"kind", "width_m", "rooms"}], "status": "OK" | "BLOCKED: <stopping codes>" | "FAILED: ..."}

A run the engine's admission gate stops (exit 2, ADMISSION_BLOCKED.json: no BOQ published) is reported as BLOCKED
with its stopping finding codes, so a refusal is told apart from a crash.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
METHOD = "ARCH_TAKEOFF_V2.5"


DECLARED = ("A-WALL=WALL", "A-COL=COLUMN", "A-GLAZ=WINDOW", "A-DOOR=DOOR")


def read(dxf, out, method=METHOD, roles=None):
    """roles: None (the engine infers every layer's role) or LAYER=ROLE declarations (--layer-roles, recorded)."""
    out = Path(out)
    argv = [sys.executable, "-I", str(ROOT / "tools" / "urban_boq_m9.py"), "arch", "--drawings", str(dxf), "--out",
            str(out), "--method", method] + (["--layer-roles", *roles] if roles else [])
    r = subprocess.run(argv, capture_output=True, text=True, cwd=str(out.parent))
    blocked = out / "ADMISSION_BLOCKED.json"
    if r.returncode == 2 and blocked.exists():
        d = json.loads(blocked.read_text(encoding="utf-8"))
        codes = sorted({f["code"] for f in d.get("stopping_findings") or ()})
        return {"rooms": [], "openings": [], "status": "BLOCKED: " + ", ".join(codes),
                "boq_published": d.get("boq_published")}
    if r.returncode != 0 or not (out / "ARCH_ROOMS.json").exists():
        return {"rooms": [], "openings": [], "status": f"FAILED: exit {r.returncode}"}
    rooms = json.loads((out / "ARCH_ROOMS.json").read_text(encoding="utf-8"))["rooms"]
    ops = json.loads((out / "ARCH_OPENINGS.json").read_text(encoding="utf-8"))["openings"]
    lines = [ln for ln in (out / "BOQ_LINES.csv").read_text(encoding="utf-8").splitlines()]
    res = []
    for x in rooms:
        flags = sorted({w.split(":")[0] for ln in lines if x["room_id"] in ln for w in ln.split(",")
                        if w.startswith("ATTACHED_THROUGH_OPEN_PASSAGE")})
        res.append({"name": x.get("name_en"), "codes": x.get("codes") or [], "area_m2": x["area_m2"],
                    "obstruction_m2": x.get("obstruction_m2") or 0.0,
                    "perimeter_m": x["perimeter_lm"], "polygon_mm": [(p[0] * 1000, p[1] * 1000) for p in x["polygon_m"]],
                    "holes_mm": [[(p[0] * 1000, p[1] * 1000) for p in h] for h in x.get("hole_polygons_m") or ()],
                    "attached_m2": sum(a.get("area_m2", 0.0) for a in x.get("attached_cells") or ()),
                    "flags": flags})
    return {"rooms": res, "openings": [{"kind": o["kind"], "width_m": o["width_m"], "rooms": o["rooms"]} for o in ops],
            "status": "OK"}
