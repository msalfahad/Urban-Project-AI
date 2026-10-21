"""M7 held-out validation - the M7 engine as frozen (00_ENGINE_FREEZE.json) on synthetic seeds 301-340, generated for
the first time by this script, against the M6 engine state (conventions V4) on the same drawings. Run once.

    python3 -I research/urban_engine_m7_reliability/heldout_run.py freeze COMMIT   # write 00_ENGINE_FREEZE.json
    python3 -I research/urban_engine_m7_reliability/heldout_run.py run              # the held-out runs (once)

run refuses unless every frozen file still has its frozen sha256 (the engine evaluated is the engine frozen).
Runs, each under V4 and V5:
    Q-A / Q-B   quantities against the design truth (tools/m7_evaluate): mixed defects, hard, V2 cases; development
                vocabulary / held-out vocabulary
    C-A / C-B   completeness detection (tools/m6_evaluate): the M6 configurations A2 / B2. A REGION_EXCLUDED finding on
                the design's own opening bay (the generator's VOID + X across bay (0, 0)) is counted apart as a correct
                large-void flag: the M6 truth lists injected elements only
    P           metamorphic properties (tools/m7_metamorphic) on seeds 301-310, every operation
    K           clean M2 villas (tools/m7_evaluate --clean) on seeds 301-320
Writes heldout/*.json and heldout/HELDOUT_SUMMARY.json. Synthetic drawings share the generator's drafting
assumptions: this is evidence that rules hold across arrangements, names, sizes and placements, not real-drawing
accuracy.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FROZEN_FILES = ("tools/urban_intake.py", "tools/urban_boq_m2.py", "tools/m7_metamorphic.py", "tools/m7_evaluate.py",
                "tools/m7_independent.py", "tools/urban_project_run.py", "tools/m6_evaluate.py",
                "tools/synthetic_villa.py", "tools/synthetic_villa_m6.py",
                "engine/source/drawing_model.py", "engine/source/generic_route.py", "engine/source/member_detection.py",
                "engine/source/slab_engine.py", "engine/source/continuous_beams.py",
                "engine/source/concrete_completeness.py", "engine/source/topology.py", "engine/source/cad_heal.py",
                "engine/source/schedule_reader.py", "engine/source/provisional_estimate.py",
                "engine/source/quantity_release.py", "engine/source/boq_reconcile.py",
                "engine/profiles/URBAN_M5_GENERIC_CONVENTIONS_V4.json",
                "engine/profiles/URBAN_M7_GENERIC_CONVENTIONS_V5.json")
SEEDS = list(range(301, 341))
V4 = "engine/profiles/URBAN_M5_GENERIC_CONVENTIONS_V4.json"
V5 = "engine/profiles/URBAN_M7_GENERIC_CONVENTIONS_V5.json"
OUT = PKG / "heldout"


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def freeze(commit):
    rec = {"engine": "URBAN_M7_ENGINE", "commit": commit, "conventions": V5, "before": V4,
           "files_sha256": {f: sha(f) for f in FROZEN_FILES},
           "git_blob_matches_commit": {},
           "rule": "the held-out seeds 301-340 are generated only after this record is committed"}
    for f in FROZEN_FILES:
        blob = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{f}"], capture_output=True, check=True).stdout
        rec["git_blob_matches_commit"][f] = hashlib.sha256(blob).hexdigest() == rec["files_sha256"][f]
    if not all(rec["git_blob_matches_commit"].values()):
        raise SystemExit("the working tree is not the commit for: " +
                         ", ".join(k for k, v in rec["git_blob_matches_commit"].items() if not v))
    (PKG / "00_ENGINE_FREEZE.json").write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return rec


def check_freeze():
    rec = json.loads((PKG / "00_ENGINE_FREEZE.json").read_text(encoding="utf-8"))
    bad = [f for f, h in rec["files_sha256"].items() if sha(f) != h]
    if bad:
        raise SystemExit("engine changed since the freeze: " + ", ".join(bad))
    return rec


def _q(conv, extra):
    from tools import m7_evaluate as EV
    recs = []
    with tempfile.TemporaryDirectory() as td:
        for sd in SEEDS:
            recs.append(EV.evaluate(sd, td, defects=sd % 2 == 1, vocabulary="heldout" if "heldout" in extra else "dev",
                                    hard=True, m6v2=True, conventions=conv))
    return {"summary": EV.summarise(recs), "drawings": recs}


def _clean(conv):
    from tools import m7_evaluate as EV
    recs = []
    with tempfile.TemporaryDirectory() as td:
        for sd in SEEDS[:20]:
            recs.append(EV.evaluate(sd, td, defects=sd % 2 == 1, conventions=conv, clean=True))
    return {"summary": EV.summarise(recs), "drawings": recs}


def _opening_bay_flag(seed, f):
    from tools import synthetic_villa as SV
    D = SV.design(seed)
    if f.get("kind") != "REGION_EXCLUDED" or not D["var"].get("opening"):
        return False
    bay = (D["xs"][0] + 4, D["ys"][0] + 4, D["xs"][1] + 4, D["ys"][1] + 4)
    b = f.get("box") or [0, 0, 0, 0]
    return bay[0] - 0.01 <= b[0] and b[2] <= bay[2] + 0.01 and bay[1] - 0.01 <= b[1] and b[3] <= bay[3] + 0.01


def _c(conv, heldout):
    from tools import m6_evaluate as M6E
    recs = []
    with tempfile.TemporaryDirectory() as td:
        for sd in SEEDS:
            recs.append(M6E.evaluate(sd, td, defects=sd % 2 == 1, conventions=conv,
                                     vocabulary="heldout" if heldout else "dev", hard=heldout, m6v2=True))
    det = sum(sum(1 for e in r.get("elements", []) if e.get("detected")) for r in recs if r.get("ok"))
    inj = sum(len(r.get("elements", [])) for r in recs if r.get("ok"))
    false, flags = [], []
    for r in recs:
        for f in r.get("false_findings", []):
            (flags if _opening_bay_flag(r["seed"], f) else false).append({"seed": r["seed"], **f})
    fam = Counter(e.get("family_state") for r in recs for e in r.get("elements", []))
    return {"summary": {"drawings": len(recs), "crashed": [r["seed"] for r in recs if not r.get("ok")],
                        "injected": inj, "detected": det, "false_findings": len(false),
                        "false_by_kind": dict(Counter(f["kind"] for f in false)),
                        "design_opening_bay_flags": len(flags), "family_states": dict(fam)},
            "false_findings": false, "opening_bay_flags": flags, "drawings": recs}


def _p(conv):
    from tools import m7_metamorphic as MM
    from tools import synthetic_villa_m6 as SM6
    out = {}
    with tempfile.TemporaryDirectory() as td:
        for sd in SEEDS[:10]:
            dxf = SM6.generate(td, sd, defects=sd % 2 == 1, hard=True, m6v2=True)
            r = MM.run(dxf, profile=str(Path(td) / f"villa_m6_{sd}.profile.json"), conventions=conv, work=td)
            out[sd] = {op: {"ok": v.get("ok"), "n_differences": v.get("n_differences"), "error": v.get("error"),
                            "first": (v.get("differences") or [])[:3]} for op, v in r["ops"].items()}
    tally = defaultdict(lambda: [0, 0])
    for sd, ops in out.items():
        for op, v in ops.items():
            tally[op][0 if (v["ok"] and not v["n_differences"]) else 1] += 1
    return {"summary": {op: {"pass": a, "fail": b} for op, (a, b) in sorted(tally.items())}, "drawings": out}


def run():
    fr = check_freeze()
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "HELDOUT_SUMMARY.json").exists():
        raise SystemExit("the held-out set was already run (heldout/HELDOUT_SUMMARY.json): it is run once")
    res, t0 = {}, time.perf_counter()
    for tag, conv in (("V4", V4), ("V5", V5)):
        for name, fn in ((f"Q_A_{tag}", lambda c=conv: _q(c, "dev")), (f"Q_B_{tag}", lambda c=conv: _q(c, "heldout")),
                         (f"C_A_{tag}", lambda c=conv: _c(c, False)), (f"C_B_{tag}", lambda c=conv: _c(c, True)),
                         (f"P_{tag}", lambda c=conv: _p(c)), (f"K_{tag}", lambda c=conv: _clean(c))):
            r = fn()
            (OUT / f"{name}.json").write_text(json.dumps(r, indent=1, default=str) + "\n", encoding="utf-8")
            res[name] = r["summary"]
            print(name, json.dumps({k: v for k, v in r["summary"].items() if k != "silent"})[:400], flush=True)
    summ = {"engine_commit": fr["commit"], "seeds": [SEEDS[0], SEEDS[-1]], "seconds": round(time.perf_counter() - t0),
            "runs": res,
            "files_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob("*.json"))}}
    (OUT / "HELDOUT_SUMMARY.json").write_text(json.dumps(summ, indent=1, sort_keys=True, default=str) + "\n",
                                              encoding="utf-8")
    return summ


if __name__ == "__main__":
    if sys.argv[1:2] == ["freeze"]:
        print(json.dumps({k: v for k, v in freeze(sys.argv[2]).items() if k != "files_sha256"}, indent=1)[:600])
    elif sys.argv[1:2] == ["run"]:
        run()
    else:
        print(__doc__)
