"""PA04 shared helpers: CAD primitives in the tuple form used by
engine.plan_regions, output directory, timing / metrics."""

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

from engine import cad_adapter as CA
from research.qs_wall_treatment_01 import protocol as P

PHASE = "PA04_MULTI_DOMAIN_QS_EXPANSION"
OUT = Path(P.OUT_DIR)
OUT4 = OUT / "pa04"
KIT = Path("/tmp/claude-0/-home-user-Urban-Project-AI/93607c01-16a4-590f-af7c-1c2701c3b240/scratchpad/kit")
DECODE = "data/runs/cad_convert/P7757_ARCHITECTURAL.json"
GF2FF = -44852.65
ROOF2GF = 89705.3
COPIES = {"GF": 0.0, "FF": GF2FF, "ROOF": -ROOF2GF}       # x shift from GF-copy coordinates
LEVELS = {"GF_FFL": 1.00, "FF_SLAB": 5.50, "ROOF_SLAB": 9.70, "TOWER_SLAB": 13.90, "TOWER_TOP": 14.40, "ANNEX_ROOF": 4.30, "GROUND": 0.00, "STAIR_FOOT": 0.30}
METRICS = {}
_N = {"cache": None}


def norm():
    if _N["cache"] is None:
        _N["cache"] = CA.normalize(json.loads(Path(DECODE).read_text("utf-8")), source_file="P7757_ARCHITECTURAL.dwg")
    return _N["cache"]


def prims(n=None):
    n = n or norm()
    out = []
    for p in n.primitives:
        if p.kind == "SEGMENT":
            out.append(("SEGMENT", p.object_id, p.provenance.layer, p.x1, p.y1, p.x2, p.y2, None, None, None, None, None))
        elif p.kind == "ARC":
            out.append(("ARC", p.object_id, p.provenance.layer, None, None, None, None, p.cx, p.cy, p.radius, p.start_angle, p.end_angle))
        elif p.kind == "CIRCLE":
            out.append(("CIRCLE", p.object_id, p.provenance.layer, None, None, None, None, p.cx, p.cy, p.radius, None, None))
    return out


def texts(n=None):
    n = n or norm()
    return [{"text": t.text, "x": t.x, "y": t.y} for t in n.texts] if hasattr(n.texts[0], "text") else [dict(t) for t in n.texts]


def timed(name):
    def deco(fn):
        def wrap(*a, **k):
            t = time.perf_counter()
            r = fn(*a, **k)
            METRICS.setdefault(name, {})["RUNTIME_S"] = round(time.perf_counter() - t, 2)
            return r
        return wrap
    return deco


def write(name, body):
    OUT4.mkdir(parents=True, exist_ok=True)
    p = OUT4 / name
    body = dict({"PHASE_ID": P.PHASE_ID, "BATCH": PHASE}, **body)
    p.write_text(json.dumps(body, indent=2, default=str) + "\n", encoding="utf-8")
    METRICS.setdefault("ARTIFACTS", []).append(name)
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def read(name, base=None):
    return json.loads(((base or OUT4) / name).read_text("utf-8"))


def seg_len(p):
    return math.hypot(p[5] - p[3], p[6] - p[4])
