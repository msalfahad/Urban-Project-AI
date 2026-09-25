"""Qortuba, sealed.

The project is finished, so it stops being work and becomes a reference: a worked example of the workflow, a
regression fixture, and the first benchmark against which a later project's method can be judged.  A benchmark that
can be edited is not a benchmark, so this module records what the finished project consists of and hashes it.  Any
later change to a sealed artifact shows up here as a broken seal rather than as a quietly different number.

It also separates what Qortuba taught from what Qortuba happens to be.  An Urban standard is a method and travels to
the next project.  A Qortuba project rule is a fact about one flat - a 3.00 m wall, a 2.20 m door, a 1.50 m window -
and travels nowhere.  Carrying the second kind across would be the most expensive mistake this system could make,
because it would look like knowledge.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
BENCHMARK_ID = "BENCHMARK_PROJECT_01"

# What the finished project consists of.  A seal over a moving file is worthless, so each of these is hashed.
SEALED = [
    ("QORTUBA_FINAL_PRE_PRICING_TAKEOFF", "the quantity set before any rate"),
    ("APPROVED_QUANTITIES", "the structured handover records, all DRAFT"),
    ("QORTUBA_RECALCULATED_QUANTITIES_V1", "every quantity with its formula, rule and status"),
    ("URBAN_OWNER_RULES_V1", "the rule store: Urban standards, Qortuba project rules, defaults, supersessions"),
    ("QORTUBA_OPENING_REGISTER_COMPLETED", "every opening with its type, dimensions and provenance"),
    ("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC", "the room workpaper behind the trade rows"),
    ("QORTUBA_BLOCKWORK_RECALC", "the wall-by-wall masonry workpaper"),
    ("QORTUBA_WALL_OBJECT_IDENTITY", "what each measured band physically is"),
    ("QORTUBA_OWNER_RULE_APPLICATION_AUDIT", "the audit that checked the rules were applied as written"),
    ("QORTUBA_QUESTION_LEDGER", "every question asked, answered and closed"),
    ("URBAN_BOQ_RULE_REGISTRY", "the historical precedent library, reference only"),
]
SEALED_BINARIES = ["QORTUBA_BOQ_CONVERSION_WORKBOOK.xlsx"]

ROLES = ["BENCHMARK_PROJECT_01", "WORKFLOW_REFERENCE", "REGRESSION_PROJECT"]


def reg(name):
    return json.loads((OUT / f"{name}.json").read_text("utf-8"))


def _sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


def carried_rules():
    """What travels to the next project, and what is barred from travelling.

    The rule store already carries the distinction; this reads it rather than restating it, so the two can never
    drift apart.  A project rule that reached a second project would be an assumption wearing a decision's clothes.
    """
    store = reg("URBAN_OWNER_RULES_V1")
    carry = [{"RULE_ID": r["RULE_ID"], "TITLE": r["TITLE"], "STATEMENT": r["STATEMENT"]}
             for r in store["URBAN_STANDARDS"]]
    bar = [{"RULE_ID": r["RULE_ID"], "PARAMETER": r["PARAMETER"], "VALUE": r["VALUE"], "UNIT": r["UNIT"]}
           for r in store["QORTUBA_PROJECT_RULES"]]
    return {
        "CARRIES_TO_THE_NEXT_PROJECT": carry,
        "CARRIES_COUNT": len(carry),
        "DOES_NOT_CARRY": bar,
        "DOES_NOT_CARRY_COUNT": len(bar),
        "WHY": "an URBAN_STANDARD is a method - how an opening is deducted, which rooms are wet, what a reveal is - "
               "and it travels.  A QORTUBA_PROJECT_RULE is a measurement of one flat: a 3.00 m wall, a 2.20 m door, "
               "a 1.500 m window.  It travels nowhere, and the next project is read or asked instead",
        "THE_EXPENSIVE_MISTAKE": "reusing a project value on a building nobody measured, because it would look like "
                                 "knowledge and read like a number",
    }


def finish():
    contents, missing = {}, []
    for name, _why in SEALED:
        p = OUT / f"{name}.json"
        (contents.setdefault(name, _sha(p)) if p.exists() else missing.append(name))
    for name in SEALED_BINARIES:
        p = OUT / name
        (contents.setdefault(name, _sha(p)) if p.exists() else missing.append(name))

    takeoff = reg("QORTUBA_FINAL_PRE_PRICING_TAKEOFF")
    export = reg("APPROVED_QUANTITIES")
    body = json.dumps(contents, sort_keys=True).encode()
    rec = {
        "ARTIFACT": "QORTUBA_BENCHMARK_SEAL",
        "BENCHMARK_ID": BENCHMARK_ID,
        "ROLES": ROLES,
        "PROJECT": "Qortuba, block 1 street 1 lane 6 - SECOND FLOOR apartment",
        "STATE": "FROZEN",
        "RULE": "Qortuba geometry, quantities, rules and comparison results are not modified unless the owner "
                "explicitly reopens the project.  A benchmark that can be edited is not a benchmark",
        "SEALED_CONTENTS": contents,
        "SEALED_COUNT": len(contents),
        "MISSING": missing,
        "SEAL_INTACT": not missing,
        "TAKEOFF_DIGEST": takeoff["DIGEST"],
        "TAKEOFF_ROWS": takeoff["COUNT"],
        "TAKEOFF_BY_STATUS": takeoff["BY_STATUS"],
        "EXPORT_DIGEST": export["DIGEST"],
        "APPROVED_COUNT": export["APPROVED_COUNT"],
        "NOTHING_IS_APPROVED": export["APPROVED_COUNT"] == 0,
        "RATES_SUPPLIED": takeoff["RATES_SUPPLIED"],
        "WASTE_APPLIED": takeoff["WASTE_APPLIED"],
        "CONTRACTOR_COMPARISON": takeoff["CONTRACTOR_COMPARISON"],
        "RULES": carried_rules(),
        "GIT_HEAD_AT_SEAL": _git("rev-parse", "--short", "HEAD"),
        "WORKING_TREE_CLEAN": _git("status", "--porcelain") == "",
        "DIGEST": hashlib.sha256(body).hexdigest()[:16],
    }
    (OUT / "QORTUBA_BENCHMARK_SEAL.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False, default=str),
                                                     "utf-8")
    return rec


def verify():
    """Re-hash the sealed set and report anything that moved.  This is the regression test the benchmark exists for."""
    sealed = json.loads((OUT / "QORTUBA_BENCHMARK_SEAL.json").read_text("utf-8"))["SEALED_CONTENTS"]
    moved, gone = [], []
    for name, want in sealed.items():
        p = OUT / (name if name.endswith(".xlsx") else f"{name}.json")
        if not p.exists():
            gone.append(name)
        elif _sha(p) != want:
            moved.append(name)
    return {"SEAL_INTACT": not moved and not gone, "CHANGED": moved, "MISSING": gone,
            "CHECKED": len(sealed)}


if __name__ == "__main__":
    r = finish()
    print(f"{BENCHMARK_ID}  seal {r['DIGEST']}  head {r['GIT_HEAD_AT_SEAL']}  clean {r['WORKING_TREE_CLEAN']}")
    print(f"sealed {r['SEALED_COUNT']} artifacts  |  takeoff {r['TAKEOFF_ROWS']} rows {r['TAKEOFF_DIGEST']}  |  "
          f"approved {r['APPROVED_COUNT']}")
    print(f"rules carried to the next project: {r['RULES']['CARRIES_COUNT']} Urban standards")
    print(f"rules barred from travelling:      {r['RULES']['DOES_NOT_CARRY_COUNT']} Qortuba project values")
    print("verify:", verify())
