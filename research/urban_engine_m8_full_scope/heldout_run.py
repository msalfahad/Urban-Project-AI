"""M8 held-out validation - the M8 engine as frozen (00_ENGINE_FREEZE.json) on synthetic seeds 401-440, generated for
the first time by this script. Run once.

    python3 -I research/urban_engine_m8_full_scope/heldout_run.py freeze COMMIT   # write 00_ENGINE_FREEZE.json
    python3 -I research/urban_engine_m8_full_scope/heldout_run.py run              # the held-out runs (once)

run refuses unless every frozen file still has its frozen sha256 (the engine evaluated is the engine frozen).
Runs:
    S_A / S_B   scope elements against their design truth (tools/m8_evaluate, conventions V6) on seeds 401-440:
                development vocabulary / held-out vocabulary, drafting distractors on (hard), V2 cases; the core
                families of the same drawings under V5 and V6; the villa's whole RC truth against the bounded total
    M7Q_A/B     the M7 quantity rows (tools/m7_evaluate, the M7 configurations Q-A / Q-B on the M7 held-out seeds
                301-340) under V6, against the stored M7 records heldout/Q_A_V5.json / Q_B_V5.json
    M7C_A/B     the M6 completeness detection (tools/m6_evaluate, the M7 configurations C-A / C-B on 301-340) under V6,
                against the stored M7 records C_A_V5.json / C_B_V5.json
    P           metamorphic properties with the completeness / scope pass (tools/m7_metamorphic --completeness, V6) on
                the M8 villas of seeds 401-410, every operation
Writes heldout/*.json and heldout/HELDOUT_SUMMARY.json. Synthetic drawings share the generator's drafting
assumptions: this is evidence that the rules hold across arrangements, names, sizes and placements, and that the
convention ranges cover the generator author's design spread - not real-drawing accuracy.
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
                "tools/synthetic_villa.py", "tools/synthetic_villa_m6.py", "tools/synthetic_villa_m8.py",
                "tools/m8_evaluate.py",
                "engine/source/drawing_model.py", "engine/source/generic_route.py", "engine/source/member_detection.py",
                "engine/source/slab_engine.py", "engine/source/continuous_beams.py",
                "engine/source/concrete_completeness.py", "engine/source/topology.py", "engine/source/cad_heal.py",
                "engine/source/schedule_reader.py", "engine/source/provisional_estimate.py",
                "engine/source/quantity_release.py", "engine/source/boq_reconcile.py",
                "engine/source/scope_quantities.py", "engine/source/family_coverage.py",
                "engine/source/stair_measure.py", "engine/source/stair_geometry.py",
                "engine/profiles/URBAN_M7_GENERIC_CONVENTIONS_V5.json",
                "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json")
M7_FREEZE = ROOT / "research/urban_engine_m7_reliability/00_ENGINE_FREEZE.json"
SEEDS = list(range(401, 441))
M7_SEEDS = list(range(301, 341))
V5 = "engine/profiles/URBAN_M7_GENERIC_CONVENTIONS_V5.json"
V6 = "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
OUT = PKG / "heldout"
M7_HELDOUT = ROOT / "research/urban_engine_m7_reliability/heldout"


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def freeze(commit):
    m7 = json.loads(M7_FREEZE.read_text(encoding="utf-8"))
    rec = {"engine": "URBAN_M8_ENGINE", "commit": commit, "conventions": V6, "before": V5,
           "files_sha256": {f: sha(f) for f in FROZEN_FILES},
           "changed_since_m7_freeze": sorted(f for f, h in m7["files_sha256"].items() if sha(f) != h),
           "git_blob_matches_commit": {},
           "rule": "the held-out seeds 401-440 are generated only after this record is committed; files changed since "
                   "the M7 freeze are exactly the M7 post-freeze fixes and the M8 engine listed here"}
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


def _s(vocabulary):
    from tools import m8_evaluate as EV
    recs = []
    with tempfile.TemporaryDirectory() as td:
        for sd in SEEDS:
            recs.append(EV.evaluate(sd, td, vocabulary=vocabulary, hard=True, conventions=V6))
    return {"summary": EV.summarise(recs), "drawings": recs}


def _rows(recs):
    return {f"{r['seed']}|{x['family']}|{x['storey']}": [x["engine_m3"], x["state"]] for r in recs if r.get("ok")
            for x in r["rows"]}


def _m7q(vocabulary, stored):
    from tools import m7_evaluate as EV
    recs = []
    with tempfile.TemporaryDirectory() as td:
        for sd in M7_SEEDS:
            recs.append(EV.evaluate(sd, td, defects=sd % 2 == 1, vocabulary=vocabulary, hard=True, m6v2=True,
                                    conventions=V6))
    a = _rows(json.loads((M7_HELDOUT / stored).read_text(encoding="utf-8"))["drawings"])
    b = _rows(recs)
    moved = [{"row": k, "V5_stored": a.get(k), "V6": b.get(k)} for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
    s = EV.summarise(recs)
    return {"summary": {"rows": len(b), "rows_moved_vs_m7_v5": len(moved), "silent_rows": s["silent_rows"],
                        "states": dict(Counter(v[1] for v in b.values())), "crashed": s["crashed"]},
            "moved": moved, "drawings": recs}


def _m7c(heldout, stored):
    from tools import m6_evaluate as M6E
    recs = []
    with tempfile.TemporaryDirectory() as td:
        for sd in M7_SEEDS:
            recs.append(M6E.evaluate(sd, td, defects=sd % 2 == 1, conventions=V6,
                                     vocabulary="heldout" if heldout else "dev", hard=heldout, m6v2=True))
    det = sum(sum(1 for e in r.get("elements", []) if e.get("detected")) for r in recs if r.get("ok"))
    inj = sum(len(r.get("elements", [])) for r in recs if r.get("ok"))
    old = json.loads((M7_HELDOUT / stored).read_text(encoding="utf-8"))["summary"]
    fam = Counter(e.get("family_state") for r in recs for e in r.get("elements", []))
    return {"summary": {"drawings": len(recs), "crashed": [r["seed"] for r in recs if not r.get("ok")],
                        "injected": inj, "detected": det, "family_states": dict(fam),
                        "m7_v5": {k: old.get(k) for k in ("injected", "detected", "family_states")}},
            "drawings": recs}


def _p():
    from tools import m7_metamorphic as MM
    from tools import synthetic_villa_m8 as SM8
    out = {}
    with tempfile.TemporaryDirectory() as td:
        for sd in SEEDS[:10]:
            dxf = SM8.generate(td, sd, vocabulary="heldout" if sd % 2 else "dev", hard=True)
            r = MM.run(dxf, profile=str(Path(td) / f"villa_m8_{sd}.profile.json"), conventions=V6, work=td,
                       completeness=True)
            out[sd] = {op: {"ok": v.get("ok"), "n_differences": v.get("n_differences"), "error": v.get("error"),
                            "first": (v.get("differences") or [])[:3]} for op, v in r["ops"].items()}
    tally = defaultdict(lambda: [0, 0])
    items_only = defaultdict(lambda: [0, 0])
    for sd, ops in out.items():
        for op, v in ops.items():
            tally[op][0 if (v["ok"] and not v["n_differences"]) else 1] += 1
            scope_only = v["ok"] and all(d["key"].startswith("SCOPE|") for d in v["first"]) and \
                (v["n_differences"] or 0) <= len(v["first"])
            items_only[op][0 if (v["ok"] and (not v["n_differences"] or scope_only)) else 1] += 1
    return {"summary": {op: {"pass": a, "fail": b, "items_invariant": items_only[op][0]}
                        for op, (a, b) in sorted(tally.items())}, "drawings": out}


def run():
    fr = check_freeze()
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "HELDOUT_SUMMARY.json").exists():
        raise SystemExit("the held-out set was already run (heldout/HELDOUT_SUMMARY.json): it is run once")
    res, t0 = {}, time.perf_counter()
    for name, fn in (("S_A", lambda: _s("dev")), ("S_B", lambda: _s("heldout")),
                     ("M7Q_A", lambda: _m7q("dev", "Q_A_V5.json")), ("M7Q_B", lambda: _m7q("heldout", "Q_B_V5.json")),
                     ("M7C_A", lambda: _m7c(False, "C_A_V5.json")), ("M7C_B", lambda: _m7c(True, "C_B_V5.json")),
                     ("P", _p)):
        r = fn()
        (OUT / f"{name}.json").write_text(json.dumps(r, indent=1, default=str) + "\n", encoding="utf-8")
        res[name] = r["summary"]
        print(name, json.dumps(r["summary"], default=str)[:600], flush=True)
    summ = {"engine_commit": fr["commit"], "seeds": [SEEDS[0], SEEDS[-1]], "m7_seeds": [M7_SEEDS[0], M7_SEEDS[-1]],
            "seconds": round(time.perf_counter() - t0), "runs": res,
            "files_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob("*.json"))}}
    (OUT / "HELDOUT_SUMMARY.json").write_text(json.dumps(summ, indent=1, sort_keys=True, default=str) + "\n",
                                              encoding="utf-8")
    return summ


if __name__ == "__main__":
    if sys.argv[1:2] == ["freeze"]:
        print(json.dumps({k: v for k, v in freeze(sys.argv[2]).items() if k != "files_sha256"}, indent=1)[:900])
    elif sys.argv[1:2] == ["run"]:
        run()
    else:
        print(__doc__)
