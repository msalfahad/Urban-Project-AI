"""Freeze SEMANTIC_EDGE_EXPERIMENT_01: source, code, selection, crops,
prompts, inputs, outputs - each bound to its own hash.

Nothing is scored here. The freeze records what was asked, what was shown
and what came back, so that an independent scorer can later grade it
without being able to change the question.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.semantic_edge_experiment_01 import a19 as A19
from research.semantic_edge_experiment_01 import protocol as P

OUT = Path("data/experiments/SEMANTIC_EDGE_EXPERIMENT_01")
CODE = Path("research/semantic_edge_experiment_01")
SOURCE = ("data/runs/cad_convert/P7757_ARCHITECTURAL.json",
          "data/runs/7757/blind/A18-GF-001/images/page-01.jpeg",
          "data/runs/7757/blind/A18-GF-001/A18_PASS_D_CANDIDATES.json")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _tree(root: Path, skip=()) -> dict:
    out = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(root))
        if any(rel.startswith(s) for s in skip):
            continue
        out[rel] = _sha(p)
    return out


def _j(name):
    p = OUT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    feat = _j("a19/PASS_A_FEATURE_ASSERTIONS.json")
    ent = _j("a19/PASS_A_ENTITY_ASSERTIONS.json")
    rel = _j("a19/PASS_A_RELATIONS.json")
    chal = _j("a19/PASS_B_CHALLENGE.json")
    chk = _j("optional_checker/CHECKER_COMPARISON.json")
    ext = _j("external/EXTERNAL_DETECTOR_TEST_SPEC.json")
    sel = _j("01_SAMPLE_SELECTION.json")
    grp = _j("02_FEATURE_GROUP_REGISTER.json")
    crop = _j("03_CROP_REGISTER.json")

    dist = feat.get("FEATURE_ASSEMBLY_TYPE_DISTRIBUTION", {})
    body = {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "EXPERIMENT_CLASS": P.EXPERIMENT_CLASS,
        "PROTOCOL_HASH": P.protocol_hash(),
        "A19_BRIEF_HASH": A19.brief_hash(),
        "E1_4_IS_NOT_MODIFIED": True,
        "E1_4_RUN_HASH": P.E1_4_RUN_HASH,

        "THE_HYPOTHESIS": P.THE_HYPOTHESIS,
        "THE_THREE_AUTHORITIES": list(P.THE_THREE_AUTHORITIES),
        "ai_is_never_the_geometry_owner": P.AI_IS_NEVER_THE_GEOMETRY_OWNER,
        "nothing_is_fed_back": P.NOTHING_IS_FED_BACK,
        "nothing_is_scored_here": P.NOTHING_IS_SCORED_HERE,
        "no_benchmark_and_no_known_geometry":
            P.NO_BENCHMARK_AND_NO_KNOWN_GEOMETRY,
        "THE_LATER_SCORER_EVALUATES_TWO_LEVELS":
            list(P.THE_LATER_SCORER_EVALUATES_TWO_LEVELS),

        "UNSCORED_RESULTS": {
            "intervals_on_the_floor": sel.get("intervals_on_the_floor"),
            "eligible_seeds": sel.get("eligible_seeds"),
            "eligible_by_stratum": sel.get("eligible_by_stratum"),
            "seeds_selected": sel.get("selected"),
            "feature_groups": grp.get("feature_groups"),
            "seed_collisions": len(sel.get("SEED_COLLISIONS", [])),
            "crops": crop.get("crops"),
            "groups_answered_pass_a": feat.get("groups_answered"),
            "pass_a_answers_refused": feat.get("answers_refused"),
            "FEATURE_ASSEMBLY_TYPE_DISTRIBUTION": dist,
            "ASSEMBLY_CONFIDENCE_DISTRIBUTION":
                feat.get("ASSEMBLY_CONFIDENCE_DISTRIBUTION"),
            "ENTITY_SUB_ROLE_DISTRIBUTION":
                ent.get("SUB_ROLE_DISTRIBUTION"),
            "ENTITY_CONFIDENCE_DISTRIBUTION":
                ent.get("CONFIDENCE_DISTRIBUTION"),
            "entity_assertions": ent.get("entity_assertions"),
            "RELATION_DISTRIBUTION": rel.get("RELATION_DISTRIBUTION"),
            "relations": rel.get("relations"),
            "FENESTRATION_READING_DISTRIBUTION":
                feat.get("FENESTRATION_READING_DISTRIBUTION"),
            "CURVE_FAMILY_ANSWER_DISTRIBUTION":
                feat.get("CURVE_FAMILY_ANSWER_DISTRIBUTION"),
            "candidate_fenestration_assemblies":
                dist.get(P.WINDOW_OR_GLAZING_ASSEMBLY, 0),
            "candidate_door_assemblies": dist.get(P.DOOR_ASSEMBLY, 0),
            "wall_assemblies": dist.get(P.WALL_ASSEMBLY, 0),
            "counter_or_cabinet_assemblies":
                dist.get(P.COUNTER_OR_CABINET_ASSEMBLY, 0),
            "pool_or_curve_assemblies": dist.get(P.POOL_OR_WATER_FEATURE, 0),
            "groups_needing_more_context": (
                feat.get("NEEDS_MORE_CONTEXT_DISTRIBUTION", {}) or {}
            ).get("True", 0),
            "PASS_B_STATUS_DISTRIBUTION": chal.get("STATUS_DISTRIBUTION"),
            "pass_b_groups_answered": chal.get("groups_answered"),
            "pass_b_answers_refused": chal.get("answers_refused"),
            "CHECKER_STATUS": (
                "RUN" if chk.get("groups_checked") else "NOT_RUN"),
            "CHECKER_GROUPS": chk.get("groups_checked", 0),
            "CHECKER_COMPARISON_DISTRIBUTION":
                chk.get("COMPARISON_DISTRIBUTION"),
            "EXTERNAL_DETECTOR_STATUS": ext.get("STATUS"),
        },

        "NO_ACCURACY_IS_REPORTED": (
            "not one number above says whether a reading is right. "
            "Nothing in this experiment was compared to a known answer, "
            "and nothing that would allow that comparison was opened"),

        "HASHES": {
            "SOURCE": {s: _sha(Path(s)) for s in SOURCE if Path(s).exists()},
            "CODE": _tree(CODE, skip=("__pycache__",)),
            "SELECTION_AND_REGISTERS": {
                n: _sha(OUT / n) for n in
                ("00_PROTOCOL.json", "01_SAMPLE_SELECTION.json",
                 "02_FEATURE_GROUP_REGISTER.json", "03_CROP_REGISTER.json",
                 "04_E1_4_BASELINE.json") if (OUT / n).exists()},
            "CROPS": _tree(OUT / "crops") if (OUT / "crops").exists() else {},
            "PROMPTS_AND_INPUTS_AND_OUTPUTS": _tree(OUT / "a19"),
            "OPTIONAL_CHECKER": (_tree(OUT / "optional_checker")
                                 if (OUT / "optional_checker").exists()
                                 else {}),
            "EXTERNAL": (_tree(OUT / "external")
                         if (OUT / "external").exists() else {}),
            "OVERLAYS": (_tree(OUT / "overlays")
                         if (OUT / "overlays").exists() else {}),
        },
    }
    p = OUT / "FREEZE.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    counted = sum(len(v) for v in body["HASHES"].values())
    print(json.dumps({**body["UNSCORED_RESULTS"],
                      "artifacts_hashed": counted,
                      "FREEZE_SHA256": _sha(p)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
