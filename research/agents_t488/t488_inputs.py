"""T-488: the URBAN_V3055_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.55 (engine.source.arch_v3055), built ONLY from
pinned, merged files (an edited file stops the build):

  research/agents_t482/out/T482_CONDITIONS.json   T-482 blockwork wiring conditions (MERGED 10e3afad, Verifier Gate A
      2026-11-03 12:02: own SFRS read, no level on the roof-only plate; section A-A; CB2 drawn 0.25; 12A7 straight):
      the 8 roof-storey walls U - L x b_r (D-39), GF-W22 CONFLICT [12.9311, 12.9439] (D-27), GF-W34 U 10.4121, parapet
      runs NW-2 [0, 3.1672] and NE-6x [0, 0.25999];
  research/agents_t449/round3/out/CORRECTION_REGISTER_BLOCKWORK_T449.json   T-449 r3 register (MERGED 72053020,
      Verifier 2026-11-03 02:14): each wall's evidence status (or its established part's) and thickness.

Nothing is typed: every figure comes from the two files; arch_v3055 asserts each against the candidate's pieces.

    python3 -I research/agents_t488/t488_inputs.py [project_id]      # prints the inputs summary
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

COND = ROOT / "research/agents_t482/out/T482_CONDITIONS.json"
REG = ROOT / "research/agents_t449/round3/out/CORRECTION_REGISTER_BLOCKWORK_T449.json"
PINS = {COND: "ddb013b0e8c8bb3a994c5e4a0734ab1b9811fcef91a079078541bb2f79ff3b4c",
        REG: "4f1c794c4906a49dc796ca8630df7032e8b45afe95dbcaf958d0c502ae877803"}
SOURCES = {
    "T-482": {"task": "T-482", "file": "research/agents_t482/out/T482_CONDITIONS.json", "sha256": PINS[COND],
              "merge_commit": "10e3afad",
              "checker_run": "Verifier 2026-11-03T12:02Z Gate A PASS: own SFRS read (no level on the roof-only plate) "
                             "+ section A-A raster (roof band 0.054 m = drafting band, refused by T-321) AGREE: 2F "
                             "roof-storey walls HELD U - L x b_r (D-39); CB2 drawn 0.25 and 12A7 11.600 m straight AGREE; "
                             "3 of 4 conditions re-measured"},
    "T-449R3": {"task": "T-449 r3", "file": "research/agents_t449/round3/out/CORRECTION_REGISTER_BLOCKWORK_T449.json",
                "sha256": PINS[REG], "merge_commit": "72053020",
                "checker_run": "Verifier 2026-11-03T02:14Z Gate A PASS: own sheet-10 section A-A 450/420/420 AGREE; "
                               "register rebuilt byte-identical, 76 walls, rule 499.3007 vs carried 499.3040 m2"},
}
WHAT_IF_BUILDUP_M = 0.05      # the build-up the carried 2F storey 4.20 implies (T-482: residual 0.0000 on all 8 walls)


def _load(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.name}: sha256 differs from the pinned file (edited input)")
    return json.loads(b.decode("utf-8"))


def _ev(s):
    return (s or "").replace("—", "-").replace("–", "-")


def build(project_id=None):
    c, r = _load(COND), _load(REG)
    reg = {(e["element_id"], e["item_code"]): e for e in r["entries"] if e.get("item_code") == "MAS.BLOCK" and e.get("element_id")}
    walls = []
    for w in c["roof_walls_2F"]:
        if w["t482_state"] != "ROOF_DATUM":
            continue          # 2F-W00 stays HELD as the fill holds it (never 0)
        e = reg[(w["wall_id"], "MAS.BLOCK")]
        ps = e["patch"].get("part_status") if w["part"] else e["patch"]["status"]
        walls.append({"wall_id": w["wall_id"], "parent_line_id": w["line_id"], "thickness_m": e["thickness_m"],
                      "carried_m2": w["carried_m2"], "upper_m2": w["upper_m2_at_b0"], "length_m": w["datum_length_m"],
                      "kind": "ESTABLISHED_PART" if w["part"] else "WHOLE", "evidence_status": _ev(ps),
                      "formula": w["formula"], "source_task": "T-482"})
    conf, drops = [], []
    for x in c["width_conflicts"]:
        e = reg[(x["element_id"], "MAS.BLOCK")]
        if "range_m2" in x:
            conf.append({"wall_id": x["element_id"], "parent_line_id": x["line_id"], "thickness_m": e["thickness_m"],
                         "carried_m2": x["carried_m2"], "range_m2": x["range_m2"], "item": "D-27",
                         "low_reading": x["low_reading"], "high_reading": x["high_reading"], "source_task": "T-482"})
        else:
            drops.append({"wall_id": x["element_id"], "parent_line_id": x["line_id"], "thickness_m": e["thickness_m"],
                          "carried_upper_m2": x["carried_U_m2"], "upper_m2": x["U_m2"], "item": "D-27",
                          "source_task": "T-482"})
    pars = [{"run": p["element_id"].split(":")[-1], "element_id": p["element_id"],
             "t482_line_id": p["line_id"],
             "before_m2": p.get("carried_m2"), "after_m2": p["range_m2"], "centreline_m": p["centreline_m"],
             "height_m": p["height_m"], "why": (p.get("carried_refused") or p.get("evidence"))[:200],
             "source_task": "T-482"} for p in c["parapets"]]
    return {"schema": "URBAN_V3055_INPUTS_V1", "project": project_id, "sources": SOURCES,
            "roof_datum": {"item": "D-39", "plate": "roof-only plate (top = finished roof - b_r, not printed)",
                           "what_if_buildup_m": WHAT_IF_BUILDUP_M, "walls": walls},
            "conflicts": conf, "drop_upper": drops, "parapets": pars}


if __name__ == "__main__":
    d = build(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps({"roof_walls": len(d["roof_datum"]["walls"]), "conflicts": len(d["conflicts"]),
                      "drops": len(d["drop_upper"]), "parapets": [p["run"] for p in d["parapets"]]}))
