"""T-338: the URBAN_V3024_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.24 (engine.source.arch_v3024), built ONLY from
the merged T-334 line-state check (research/agents_t334/V3_0_21_LINE_STATE_FINDINGS.csv, MERGED 39092d8d, Verifier
2026-10-29 11:42 UTC Gate A PASS), pinned by sha256: an edited findings file stops the build.

Kind by T-334 category: VALUED_WITH_HELD_TEXT -> REBAR_FORMULA (released ledger kg printing 'held: '),
HELD_WITH_FIGURE -> NA_GROSS (a NOT_APPLICABLE line keeping its gross), FORMULA_FIGURE_DISAGREES -> FORMULA_END (the
formula concludes on a gross or another element's figure). The finding ids are engine line ids of the candidate; the
V3.0.22 / V3.0.23 steps keep every one of them (V3.0.22 fills only blank FIN.PLASTER backing lines, V3.0.23 only
adds parapet lines): the module asserts each listed line still shows its finding on the V3.0.23 run and that no other
line does. The rebar unit mass is the project's method D2_OVER_162 (engine/source/rebar_unit_mass.py), the method the
merged hand ledgers T-138 r2 / T-148 / T-149 compute with (their unit-mass function d^2/162).

    python3 -I research/agents_t338/t338_inputs.py [--check]
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FINDINGS = ROOT / "research/agents_t334/V3_0_21_LINE_STATE_FINDINGS.csv"
_PIN = "8988238e3653a731810bc052e6807e7e988922603dfbb9effa0c7e0e8d549bce"   # the merged file (T-334, 39092d8d)
T334_MERGE = "39092d8d54790c63cfcf08e9dd3e18af4d510a61"
T334_CHECKER = ("Verifier 2026-10-29 11:42 UTC (T-334 Gate A PASS, MERGED 39092d8d; own run V3_0_21 be22a4e4; "
                "L-1d50c1dc 16.751 kg = 4 x 2.65 m x 1.580 kg/m reproduced)")
KIND = {"VALUED_WITH_HELD_TEXT": "REBAR_FORMULA", "HELD_WITH_FIGURE": "NA_GROSS",
        "FORMULA_FIGURE_DISAGREES": "FORMULA_END"}
UNIT_MASS = {"method": "D2_OVER_162",
             "source": "engine/source/rebar_unit_mass.py D2_OVER_162 (kg/m = d^2 / 162), the method of the merged "
                       "hand ledgers the released rebar lines come from (research/agents_t138/t138_hand_ledger.py, "
                       "research/agents_t148/t148_column_steel.py, research/agents_t149/t149_beam_steel.py: d^2/162)"}


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _rows():
    with FINDINGS.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def build(project_id=None):
    sha = _sha(FINDINGS)
    if sha != _PIN:
        raise SystemExit(f"{FINDINGS.name}: sha256 {sha[:8]} is not the merged {_PIN[:8]} (edited findings file)")
    fixes, dec = [], {k: {"lines": 0} for k in KIND.values()}
    kg, gross = 0.0, 0.0
    for r in _rows():
        k = KIND.get(r["category"])
        if k is None:
            raise SystemExit(f"{r['line_id']}: category {r['category']} has no V3.0.24 kind")
        fixes.append({"line_id": r["line_id"], "kind": k, "task": "T-334"})
        dec[k]["lines"] += 1
        if k == "REBAR_FORMULA":
            kg += float(r["measured_net"])
        if k == "NA_GROSS":
            gross += float(r["gross"])
    dec["REBAR_FORMULA"]["kg"] = round(kg, 6)
    dec["NA_GROSS"]["gross"] = round(gross, 6)
    sys.path.insert(0, str(ROOT / "research" / "agents_t193"))
    import t193_inputs as L7   # noqa: E402  (the V3.0.7 guard inputs, unchanged, as V3.0.8 .. V3.0.23)
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V3024_INPUTS_V1", "project": project_id,
            "sources": [{"file": str(FINDINGS.relative_to(ROOT)), "sha256": sha, "task": "T-334",
                         "merge_commit": T334_MERGE, "checker_run": T334_CHECKER}],
            "unit_mass": UNIT_MASS, "fixes": fixes, "for_lead": [], "declared": dec, "guard": g}



if __name__ == "__main__":
    d = build()
    print(json.dumps({"fixes": len(d["fixes"]), "declared": d["declared"]}, indent=1))
