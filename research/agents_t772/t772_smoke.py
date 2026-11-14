"""T-772 smoke test (owner PROCEED_PLAN_2026-11-14 'Reject' -> a two-hour smoke test): the ONE manifest-driven command
tools/urban_boq_run.py on the training villa's decoded Drive drawings, compared with the committed candidate index.

    bash scripts/agent_env.sh run --tree task-T-772 research/agents_t772/t772_smoke.py <plan.dxf> <structural.dxf> \
        --out <private>/t772

Writes the run manifest into --out (outside the repository): the drawings by role, the generic rule set
(engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json), the project's route G profile and facts exactly as the
candidate chain uses them (research/agents_t131 / research/urban_engine_m4_correctness, unchanged), no inputs sheet
(T-782 not built: an exception), compare = research/agents_t770/out/LINE_INDEX_V3_0_83.json + the family master
1.83.0. Prints counts, item codes, family codes and units only (no coordinates, no names, no drawing content).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t131"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import alsenan_v30_run as T131  # noqa: E402

PROFILE = ROOT / "research/urban_engine_m4_correctness/profile_st7757_m4.json"
INDEX = ROOT / "research/agents_t770/out/LINE_INDEX_V3_0_83.json"
MASTER = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.83.0.json"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("structural")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from tools import urban_boq_run as R
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    facts = out / "facts.json"
    facts.write_text(json.dumps(T131.facts(Path(a.plan).name), ensure_ascii=False), encoding="utf-8")
    man = {"schema": R.MANIFEST_SCHEMA, "project_id": T131.PID,
           "drawings": {"plan": str(Path(a.plan).resolve()), "structural": str(Path(a.structural).resolve())},
           "rules": {"conventions": str(T131.CONV), "profile": str(PROFILE), "facts": str(facts)},
           "data_objects": {},
           "compare": {"candidate_index": str(INDEX), "family_master": str(MASTER)}}
    mp = out / "RUN_MANIFEST.json"
    mp.write_text(json.dumps(man, indent=1), encoding="utf-8")
    rc = R.main(["--manifest", str(mp), "--out", str(out / "run")])
    run = out / "run"
    fams = json.loads((run / "REACH_BY_FAMILY.json").read_text(encoding="utf-8"))["by_family"]
    print("family | lines | direct | geom-restated | fill-restated | overlay-only | fill-only | reached")
    for f in fams:
        print(f"{f['family']} | {f['lines']} | {f['GEOMETRY_DIRECT']} | {f['GEOMETRY_RESTATED']} | "
              f"{f['FILL_RESTATED']} | {f['OVERLAY_ONLY']} | {f['FILL_ONLY']} | {f['reached_share']}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
