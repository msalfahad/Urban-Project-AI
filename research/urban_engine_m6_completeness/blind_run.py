"""M6 blind run: the frozen completeness engine on ST7757, written and hashed before any external record is opened.

    python3 -I research/urban_engine_m6_completeness/blind_run.py [--cache DIR] [--check]

Phase BLIND (engine/benchmark_protection): the run receives the structural and architectural drawings, the M4 profile
(printed storey heights), the M3 detail evidence and the M4 OCR review - the same inputs as the M5 engine run - and
nothing that could tell it an answer. Its registers are written to blind/ and frozen (CANDIDATE_GEOMETRY_HASH); the
reconciliation (reconcile.py) may only read them. --check rebuilds in memory and compares byte for byte.

The engine is the M6 freeze (00_ENGINE_FREEZE.json, commit 090a470); conventions V4 (the M5 set).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import benchmark_protection as bp      # noqa: E402
from tools import urban_boq_m2 as CLI              # noqa: E402
from tools import urban_structural_boq as M1       # noqa: E402

ENGINE_FREEZE = "090a470"
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
ARCH = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
INPUTS = {"profile": "research/urban_engine_m4_correctness/profile_st7757_m4.json",
          "evidence": "research/urban_engine_m3_recovery/evidence/DETAIL_EVIDENCE.json",
          "evidence_review": "research/urban_engine_m4_correctness/evidence/OCR_INDEPENDENT_READINGS.json",
          "conventions": "engine/profiles/URBAN_M5_GENERIC_CONVENTIONS_V4.json"}
FK = ["FINDING_ID", "SEVERITY", "KIND", "FAMILY", "CONFIDENCE", "SHEET", "STOREY", "BOX_M", "EVIDENCE", "MAGNITUDE",
      "VOLUME_LOW_M3", "VOLUME_HIGH_M3", "VOLUME_BASIS", "ITEMS", "REFS", "ACTION"]


def run(cache=None):
    R = CLI.compute([str(DXF)], route="G", arch=[str(ARCH)], cache_dir=cache, completeness=True,
                    **{k: str(ROOT / v) for k, v in INPUTS.items()})
    return R


def files(R):
    CR = R["generic"]["completeness"]
    sk = sorted({k for r in CR["signals"] for k in r})
    out = {
        "blind/COMPLETENESS_FINDINGS.csv": M1.csv_text([{k: f.get(k) for k in FK} for f in CR["findings"]], FK),
        "blind/COMPLETENESS_SIGNALS.csv": M1.csv_text([{k: r.get(k) for k in sk} for r in CR["signals"]], sk),
        "blind/COMPLETENESS_SCOPE.csv": M1.csv_text(CR["scope"]),
        "blind/COMPLETENESS_SUMMARY.json": M1._jdump({"policy": CR["policy"], "scores": CR["scores"],
                                                      "geometry_stats": CR["geometry_stats"],
                                                      "populations": CR["populations"], "params": {
                                                          k: v for k, v in CR["params"].items()
                                                          if not k.startswith("_")}, "rule": CR["rule"]}),
    }
    for rel in INPUTS.values():                       # nothing benchmark-shaped reached the pass (input contents)
        bp.assert_blind(json.loads((ROOT / rel).read_text(encoding="utf-8")))
    sha = {k: hashlib.sha256((ROOT / v).read_bytes()).hexdigest() for k, v in INPUTS.items()}
    payload = {"engine_commit": ENGINE_FREEZE, "inputs_sha256": sha, "findings": [{k: f.get(k) for k in FK}
                                                                                 for f in CR["findings"]],
               "scores": CR["scores"]}
    bp.assert_blind({"findings": payload["findings"], "scores": payload["scores"]})
    frozen = bp.freeze(payload)
    manifest = {"phase": bp.BLIND, "then": frozen["phase"], "CANDIDATE_GEOMETRY_HASH": frozen["CANDIDATE_GEOMETRY_HASH"],
                "engine_commit": ENGINE_FREEZE, "inputs": INPUTS, "inputs_sha256": sha,
                "drawings_sha256": [DXF.name.split(".")[0], ARCH.name.split(".")[0]],
                "files_sha256": {k: hashlib.sha256(v.encode("utf-8")).hexdigest() for k, v in sorted(out.items())},
                "findings": len(CR["findings"]), "by_severity": CR["scores"]["findings_by_severity"],
                "rule": "written before any external record (freelancer, MCP) is opened; reconcile.py reads these "
                        "files and never re-runs the engine to meet an external figure"}
    out["01_BLIND_RUN_FREEZE.json"] = json.dumps(manifest, indent=1, sort_keys=True) + "\n"
    return out


def main(argv):
    cache = argv[argv.index("--cache") + 1] if "--cache" in argv else None
    out = files(run(cache))
    if "--check" in argv:
        bad = [k for k, v in out.items() if (PKG / k).read_text(encoding="utf-8") != v]
        print(json.dumps({"files": len(out), "differ": bad}, indent=1))
        return 1 if bad else 0
    for k, v in out.items():
        (PKG / k).parent.mkdir(parents=True, exist_ok=True)
        (PKG / k).write_text(v, encoding="utf-8")
    print(json.loads(out["01_BLIND_RUN_FREEZE.json"])["CANDIDATE_GEOMETRY_HASH"], len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
