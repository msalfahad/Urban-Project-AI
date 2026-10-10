"""Run the material-role overlap audit over the four frozen trace cases.

    python3 -m research.qs_wall_treatment_01.run_overlap_audit
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine import material_role_audit as A
from research.qs_wall_treatment_01 import declarations as D
from research.qs_wall_treatment_01 import protocol as P


def run() -> dict:
    reg = json.loads(Path(P.TRACE_REGISTER).read_text("utf-8"))
    out = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "OVERLAP_AUDIT",
           "TRACE_REGISTER_SHA256": hashlib.sha256(
               Path(P.TRACE_REGISTER).read_bytes()).hexdigest(),
           "AUDIT_RULE_VERSION": A.AUDIT_RULE_VERSION,
           "THE_RULE": "TRACE OVERLAP != MATERIAL OVERLAP",
           "DECLARATIONS": {"OBJECT_MAP": D.OBJECT_MAP,
                            "ROLE_OVERRIDES": D.ROLE_OVERRIDES,
                            "SOLID_BASE_OF": D.SOLID_BASE_OF,
                            "SAME_PROJECTION_PAIRS": D.SAME_PROJECTION_PAIRS},
           "PER_CASE": {}}
    for cid in P.CASES:
        traces = [t for t in reg["TRACES"] if t["CASE_ID"] == cid]
        res = A.overlap_audit(
            traces, object_map=D.OBJECT_MAP.get(cid),
            role_overrides=D.ROLE_OVERRIDES.get(cid),
            solid_base_of=D.SOLID_BASE_OF.get(cid),
            same_projection_pairs=D.SAME_PROJECTION_PAIRS.get(cid))
        out["PER_CASE"][cid] = res
    out["TOTALS"] = {r: sum(c["COUNTS"][r] for c in out["PER_CASE"].values())
                     for r in A.OVERLAP_RELATIONS}
    out["MATERIAL_CONTRADICTIONS_TOTAL"] = sum(
        len(c["MATERIAL_CONTRADICTIONS"]) for c in out["PER_CASE"].values())
    p = Path(P.OUT_DIR) / "OVERLAP_AUDIT.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"OVERLAP_AUDIT_SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "TOTALS": out["TOTALS"],
            "CONTRADICTIONS": out["MATERIAL_CONTRADICTIONS_TOTAL"]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
