"""R8.5 follow-up — MIGRATION ROUND 1 SCOPE (design input only; nothing is migrated).

Derives, from the R8.5 value shadow, the narrowest first migration round the evidence supports: the
Qortuba FINAL rows whose value is a plain sum of room floor-polygon areas AND that the canonical method
reproduces exactly (VALUE_EXACT_MATCH). For that scope it lists the rooms, the canonical quantities, the
source observations they rest on, and the capability signatures those observations exercise — i.e. the
signatures an independent-parser qualification must cover before the round can execute.

Reads the gitignored R8.5 outputs; writes the scope register under tests/r8_5/registers.

    python3 research/external_engine_lab/r8_5_migration_round1_scope.py [register_path]
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from engine.source import qualification as Q                                   # noqa: E402
from engine.source.cad import libredwg_map as L                                # noqa: E402

from r8_4_qualification import SOURCES, full_source_sha, load                  # noqa: E402

R85 = ROOT / "research/external_engine_lab/outputs/r8_5"
OUT = ROOT / "tests/r8_5/registers/R8_MIGRATION_ROUND1_SCOPE.json"
PROJECT = "QORTUBA"


def main(out: Path = OUT):
    diff = json.loads((R85 / "SHADOW_VALUE_DIFF.json").read_text())[PROJECT]
    cq = json.loads((R85 / "CANONICAL_SHADOW_QUANTITIES.json").read_text())[PROJECT]
    status = json.loads((R85 / "REAL_PROJECT_R8_5_STATUS.json").read_text())[PROJECT]
    rows = [r for r in diff["rows"] if r["value_class"] == "VALUE_EXACT_MATCH" and r["current_status"] == "FINAL"]
    excluded = Counter(r["value_class"] for r in diff["rows"] if r not in rows)

    by_name = {}
    for rm in diff["rooms"]:
        by_name.setdefault(rm["room"], []).append(rm)
    rooms_used, row_recs = {}, []
    for r in rows:
        refs, pool = [], {k: list(v) for k, v in by_name.items()}
        for inp in r["current_inputs"]:
            cand = [x for x in pool.get(inp["room"], []) if abs(x["current_area_m2"] - inp["value"]) < 1e-9]
            assert len(cand) >= 1, (r["row_id"], inp)
            rm = cand[0]
            pool[inp["room"]].remove(rm)
            refs.append(rm["room_id"])
            rooms_used[rm["room_id"]] = rm
        row_recs.append({"row_id": r["row_id"], "unit": r["unit"], "rules": r["rules"],
                         "current_value": r["current_value"], "canonical_preview_value": r["canonical_preview_value"],
                         "abs_delta": r["abs_delta"], "room_ids": refs})

    area_q = {q["geometry_ids"][0]: q for q in cq if q["kind"] == "ROOM_FLOOR_AREA"}
    obs = sorted({o for rid in rooms_used for o in area_q[rid]["source_observation_ids"]},
                 key=lambda s: int(s.split(":")[1]))

    src = full_source_sha(PROJECT)
    path = next(ROOT / d for d in SOURCES[PROJECT]["decodes"] if (ROOT / d).exists())
    doc = L.to_document(load(path), source_sha256=src)
    sigs = Q.capability_signatures(doc)
    want = set(obs)
    required = {sg: sorted({k[0] for k in keys if k[0] in want}) for sg, keys in sigs.items()}
    required = {sg: v for sg, v in required.items() if v}
    covered = {o for v in required.values() for o in v}

    reg = {
        "SCHEMA": "URBAN_R8_5_MIGRATION_ROUND1_SCOPE_V1",
        "status": "DESIGN_ONLY_NOT_EXECUTED",
        "project": PROJECT, "source_sha256": src,
        "selection_rule": ("FINAL rows whose value is a sum of room floor-polygon areas and that the canonical method "
                           "reproduces exactly from the current inputs (VALUE_EXACT_MATCH); nothing else"),
        "rows": row_recs,
        "rows_excluded_by_class": dict(excluded),
        "rooms": [{"room_id": rid, "room": rm["room"], "current_area_m2": rm["current_area_m2"],
                   "canonical_area_m2": rm["canonical_area_m2"], "max_edge_residual_mm": rm["max_edge_residual_mm"],
                   "canonical_quantity_id": area_q[rid]["quantity_id"], "method_id": area_q[rid]["method_id"],
                   "frame_id": area_q[rid]["frame_id"]} for rid, rm in sorted(rooms_used.items())],
        "source_observations": obs,
        "source_observations_without_signature": sorted(want - covered),
        "required_signatures": [{"signature": sg, "observations": len(v)} for sg, v in sorted(required.items())],
        "required_signature_count": len(required),
        "project_signature_count": len(sigs),
        "current_gate_state": {"unit": status["unit"], "region": status["region"], "frame": status["frame"],
                               "release": status["release"], "V-CAD-5": status["V-CAD-5"],
                               "designation_review": status["designation_review"]["designation"]["review_status"],
                               "qualified_required_signatures": 0,
                               "independent_real_reconciliation": "BLOCKED_EXTERNAL_INPUT"},
        "execution_ready": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reg, indent=1, ensure_ascii=False) + "\n")
    print(len(row_recs), "rows,", len(rooms_used), "rooms,", len(obs), "observations,",
          len(required), "of", len(sigs), "signatures required")
    for s in reg["required_signatures"]:
        print("  ", s["observations"], s["signature"])
    return reg


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT)
