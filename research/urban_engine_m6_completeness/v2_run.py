"""M6 V2 run on ST7757 - POST-DISCOVERY, not blind - and the reproduction of the frozen V1 blind run.

    python3 -I research/urban_engine_m6_completeness/v2_run.py [--cache DIR] [--check] [--reproduce-v1]

The V2 rules (02_ENGINE_FREEZE_V2.json, commit 6c20879) were written after the V1 blind run had been reconciled
against the freelancer BOQ and both MCP reports: this run shows what V2 reports on the drawing whose misses
motivated it. It is NOT blind evidence of generalisation (the held-out synthetic villas are) and it never
overwrites the V1 blind files. Same inputs as the blind run (blind_run.INPUTS: drawings, M4 profile, M3 detail
evidence, M4 OCR review, conventions V4); nothing external enters (benchmark_protection.assert_blind on the inputs
and the payload). Writes post_discovery_v2/ (findings, signals, scope, summary, the V1 -> V2 finding delta) and
03_V2_RUN_FREEZE.json; --check rebuilds in memory and compares byte for byte.

Both runs use the engine as frozen, read with git (V2 at ENGINE_FREEZE; never the working tree).
--reproduce-v1 loads the V1 engine as frozen (engine/source/concrete_completeness.py at commit 090a470, read with
git), runs the blind run with it and compares every blind/ file and 01_BLIND_RUN_FREEZE.json byte for byte.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = Path(__file__).resolve().parent
for p in (str(ROOT), str(PKG)):
    if p not in sys.path:
        sys.path.insert(0, p)

import blind_run as B                              # noqa: E402
from engine import benchmark_protection as bp      # noqa: E402
from tools import urban_boq_m2 as CLI              # noqa: E402
from tools import urban_structural_boq as M1       # noqa: E402

ENGINE_FREEZE = "6c20879"
V1_COMMIT = B.ENGINE_FREEZE
OUT = "post_discovery_v2"
POST_DISCOVERY = "POST_DISCOVERY"


def engine_at(commit):
    """the completeness engine as committed at `commit` (a module object; the working tree is not touched)."""
    src = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:engine/source/concrete_completeness.py"],
                         capture_output=True, text=True, check=True).stdout
    mod = types.ModuleType(f"concrete_completeness_{commit}")
    mod.__file__ = f"<git {commit}:engine/source/concrete_completeness.py>"
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)     # noqa: S102 - the repository's own frozen source
    return mod


def run_with(engine, cache=None):
    saved = CLI.CC
    CLI.CC = engine
    try:
        return B.run(cache)
    finally:
        CLI.CC = saved


def _delta(v1_csv, v2_findings):
    """findings by id: in V2 only, in V1 only (the same id = the same kind, place, family and references)."""
    v1 = {r["FINDING_ID"]: r for r in csv.DictReader(io.StringIO(v1_csv))}
    v2 = {f["FINDING_ID"]: f for f in v2_findings}
    rows = []
    for fid in sorted(set(v1) | set(v2)):
        if fid in v1 and fid in v2:
            continue
        f = v2.get(fid) or v1[fid]
        rows.append({"FINDING_ID": fid, "IN": "V2_ONLY" if fid in v2 else "V1_ONLY", "KIND": f["KIND"],
                     "SEVERITY": f["SEVERITY"], "FAMILY": f["FAMILY"], "SHEET": f["SHEET"], "STOREY": f["STOREY"],
                     "BOX_M": f["BOX_M"], "EVIDENCE": str(f["EVIDENCE"])[:240]})
    return rows


def files(R):
    CR = R["generic"]["completeness"]
    if CR["policy"] != "CONCRETE_COMPLETENESS_V2":
        raise ValueError(f"engine policy {CR['policy']}: the V2 run needs the V2 engine")
    sk = sorted({k for r in CR["signals"] for k in r})
    v1_csv = (PKG / "blind/COMPLETENESS_FINDINGS.csv").read_text(encoding="utf-8")
    delta = _delta(v1_csv, CR["findings"])
    out = {
        f"{OUT}/COMPLETENESS_FINDINGS.csv": M1.csv_text([{k: f.get(k) for k in B.FK} for f in CR["findings"]], B.FK),
        f"{OUT}/COMPLETENESS_SIGNALS.csv": M1.csv_text([{k: r.get(k) for k in sk} for r in CR["signals"]], sk),
        f"{OUT}/COMPLETENESS_SCOPE.csv": M1.csv_text(CR["scope"]),
        f"{OUT}/COMPLETENESS_SUMMARY.json": M1._jdump({"policy": CR["policy"], "scores": CR["scores"],
                                                       "geometry_stats": CR["geometry_stats"],
                                                       "populations": CR["populations"], "params": {
                                                           k: v for k, v in CR["params"].items()
                                                           if not k.startswith("_")}, "rule": CR["rule"]}),
        f"{OUT}/V1_V2_FINDING_DELTA.csv": M1.csv_text(delta, ["FINDING_ID", "IN", "KIND", "SEVERITY", "FAMILY",
                                                              "SHEET", "STOREY", "BOX_M", "EVIDENCE"]),
    }
    for rel in B.INPUTS.values():
        bp.assert_blind(json.loads((ROOT / rel).read_text(encoding="utf-8")))
    sha = {k: hashlib.sha256((ROOT / v).read_bytes()).hexdigest() for k, v in B.INPUTS.items()}
    payload = {"engine_commit": ENGINE_FREEZE, "inputs_sha256": sha,
               "findings": [{k: f.get(k) for k in B.FK} for f in CR["findings"]], "scores": CR["scores"]}
    bp.assert_blind({"findings": payload["findings"], "scores": payload["scores"]})
    frozen = bp.freeze(payload)
    manifest = {"phase": POST_DISCOVERY, "run_phase": POST_DISCOVERY, "then": frozen["phase"],
                "CANDIDATE_GEOMETRY_HASH": frozen["CANDIDATE_GEOMETRY_HASH"], "engine_commit": ENGINE_FREEZE,
                "v1_blind_run": {"engine_commit": V1_COMMIT, "manifest": "01_BLIND_RUN_FREEZE.json",
                                 "untouched": True},
                "inputs": B.INPUTS, "inputs_sha256": sha,
                "drawings_sha256": [B.DXF.name.split(".")[0], B.ARCH.name.split(".")[0]],
                "files_sha256": {k: hashlib.sha256(v.encode("utf-8")).hexdigest() for k, v in sorted(out.items())},
                "findings": len(CR["findings"]), "by_severity": CR["scores"]["findings_by_severity"],
                "delta_vs_v1": {"v2_only": sum(1 for r in delta if r["IN"] == "V2_ONLY"),
                                "v1_only": sum(1 for r in delta if r["IN"] == "V1_ONLY")},
                "rule": "post-discovery: the V2 rules were written after the V1 reconciliation named the misses; "
                        "this run is evidence of what V2 reports on this drawing, not of generalisation (see "
                        "heldout/HELDOUT_V2_SUMMARY.json); reconcile.py reads these files and never re-runs the "
                        "engine to meet an external figure"}
    out["03_V2_RUN_FREEZE.json"] = json.dumps(manifest, indent=1, sort_keys=True) + "\n"
    return out


def reproduce_v1(cache=None):
    """the frozen V1 blind files rebuilt with the V1 engine read from git: [] when every byte matches."""
    out = B.files(run_with(engine_at(V1_COMMIT), cache))
    return [k for k, v in out.items() if (PKG / k).read_text(encoding="utf-8") != v]


def build_v2(cache=None):
    """the V2 run with the V2 engine as frozen (read from git at ENGINE_FREEZE, whatever the working tree holds)."""
    return files(run_with(engine_at(ENGINE_FREEZE), cache))


def reproduce_v2(cache=None):
    return [k for k, v in build_v2(cache).items() if (PKG / k).read_text(encoding="utf-8") != v]


def main(argv):
    cache = argv[argv.index("--cache") + 1] if "--cache" in argv else None
    if "--reproduce-v1" in argv:
        bad = reproduce_v1(cache)
        print(json.dumps({"v1_engine": V1_COMMIT, "differ": bad}, indent=1))
        return 1 if bad else 0
    out = build_v2(cache)
    if "--check" in argv:
        bad = [k for k, v in out.items() if (PKG / k).read_text(encoding="utf-8") != v]
        print(json.dumps({"files": len(out), "differ": bad}, indent=1))
        return 1 if bad else 0
    for k, v in out.items():
        (PKG / k).parent.mkdir(parents=True, exist_ok=True)
        (PKG / k).write_text(v, encoding="utf-8")
    print(json.loads(out["03_V2_RUN_FREEZE.json"])["CANDIDATE_GEOMETRY_HASH"], len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
