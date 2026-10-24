"""T-146 + T-247: snapshot of the candidate's slab and beam lines as ARCH_TAKEOFF_V3.0.11 carries them (research code).

Reads one finished V3.0.11 run (V3_0_11_BOQ_LINES.json, research/agents_t239/v3011_run.py on the Drive copies) and
writes CANDIDATE_V3011_BEAM_SLAB.json: per STR.CONC.SLAB / STR.CONC.BEAM line its engine element id, floor, evidence
state and figure (value, or [low, high]); the band dimensions the route prints on the line (width, length, depth, net
plan), never a coordinate, a handle or a name. The V3.0.12 inputs (t146_inputs.py) state the figure each line carries
from this file; the V3.0.12 module re-checks every one of them against the live line at run time, so a drifted run is
refused, never silently integrated.

    python3 -I research/agents_t146/snapshot_v3011.py <run>/v3011/V3_0_11_BOQ_LINES.json [--write]
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "CANDIDATE_V3011_BEAM_SLAB.json"
ITEMS = ("STR.CONC.SLAB", "STR.CONC.BEAM")


def _r(x):
    return None if x is None else round(float(x), 6)


def snapshot(path):
    raw = Path(path).read_bytes()
    lines = json.loads(raw)
    lines = lines if isinstance(lines, list) else lines["lines"]
    rows = []
    for ln in lines:
        if ln["item_code"] not in ITEMS:
            continue
        br = ln.get("bounded_range") or {}
        ev = ln["evidence_state"]
        dims = ((ln.get("calculation") or {}).get("inputs") or {}).get("dimensions") or {}
        rows.append({"item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                     "element_id": ln["location"].get("element_id"), "line_id": ln["line_id"],
                     "evidence_state": ev,
                     "value": _r(ln.get("measured_net")) if ev != "BOUNDED_EXPOSURE" else None,
                     "range": [_r(br.get("low")), _r(br.get("high"))] if ev == "BOUNDED_EXPOSURE" else None,
                     "dims": {k: dims.get(k) for k in ("width_m", "length_m", "depth_m", "net_plan_m2")
                              if dims.get(k) is not None}})
    rows.sort(key=lambda r: (r["item_code"], r["floor"] or "", r["element_id"] or ""))
    return {"schema": "T146_CANDIDATE_V3011_BEAM_SLAB_V1", "source": "V3_0_11_BOQ_LINES.json",
            "source_sha256": hashlib.sha256(raw).hexdigest(), "lines": rows}


if __name__ == "__main__":
    snap = snapshot(sys.argv[1])
    if "--write" in sys.argv[2:]:
        OUT.write_text(json.dumps(snap, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    from collections import Counter
    print(snap["source_sha256"], Counter((r["item_code"], r["floor"], r["evidence_state"]) for r in snap["lines"]))
