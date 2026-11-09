"""T-653 rebuild ledger: every committed output the 18 + 1 Decimal-precision modules rebuild, sha256 per output.

Each builder runs in its OWN fresh process (python -I), so no other module's import can change its Decimal context.
Two modes per builder:
  default   the interpreter's default context (prec 28) when the builder is imported
  prec6     decimal.getcontext().prec = 6 set BEFORE the import (adverse: a caller with a different global context)
For each output the ledger records sha256 of the rebuilt text, sha256 of the committed file, whether they are equal,
and the global precision seen after the build (before T-653 the import raised it to 40 / 50; after T-653 it must be
the caller's own value). Outputs that need private inputs (.work/private) are rebuilt exactly as the module does
without them; their text is still hashed so a before / after comparison holds.

usage (via the wrapper, from the checkout root):
  bash scripts/agent_env.sh run --tree task-T-653 research/agents_t653/t653_rebuild.py [--root <tree>] [--out <json>]
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# key -> (folder, module, python expression giving [(label, text, committed path relative to the folder or None)])
J1 = "json.dumps({0}, indent=1, ensure_ascii=False, sort_keys=True) + '\\n'"
SPECS = {
    "t543": ("research/agents_t543", "t543_alsenan",
             f"[('T543_BLOCKWORK_RECONCILE.json', {J1.format('M.build()')}, 'out/T543_BLOCKWORK_RECONCILE.json')]"),
    "t550": ("research/agents_t550", "t550_alsenan",
             f"[('T550_UNRESOLVED_RESTATED.json', {J1.format('M.build()')}, 'out/T550_UNRESOLVED_RESTATED.json')]"),
    "t559": ("research/agents_t559", "t559_alsenan",
             f"[('T559_LEFTOVER.json', {J1.format('M.build(M.PRIVATE_DEFAULT)')}, 'out/T559_LEFTOVER.json')]"),
    "t568": ("research/agents_t568", "t568_alsenan",
             "[('T568_TYPE_TABLE.json', json.dumps(M.build(M.ALU_DEFAULT, M.MAS_DEFAULT), indent=1, ensure_ascii=False,"
             " default=str) + '\\n', 'out/T568_TYPE_TABLE.json')]"),
    "t573": ("research/agents_t573", "t573_alsenan", "[('T573_CEILING_RECONCILE.json', M.dump(M.build()), 'out/T573_CEILING_RECONCILE.json')]"),
    "t574": ("research/agents_t574", "t574_alsenan", "[('T574_SKIRTING_RECONCILE.json', M.dump(M.build()), 'out/T574_SKIRTING_RECONCILE.json')]"),
    "t577": ("research/agents_t577", "t577_alsenan", "[('T577_MARBLE_RECONCILE.json', M.dump(M.build()), 'out/T577_MARBLE_RECONCILE.json')]"),
    "t578": ("research/agents_t578", "t578_alsenan", "[('T578_RAIL_NOSING_RECONCILE.json', M.dump(M.build()), 'out/T578_RAIL_NOSING_RECONCILE.json')]"),
    "t584": ("research/agents_t584", "t584_alsenan", "[('T584_STEPS.json', M.dump(M.build()), 'out/T584_STEPS.json')]"),
    "t585": ("research/agents_t585", "t585_alsenan", "[('T585_SKIRTING_FOLLOWUPS.json', M.dump(M.build()), 'out/T585_SKIRTING_FOLLOWUPS.json')]"),
    "t592": ("research/agents_t592", "t592_alsenan",
             "[('T592_DOOR_STEPS.json', json.dumps(M.build(), indent=1, sort_keys=True) + '\\n', 'out/T592_DOOR_STEPS.json')]"),
    "t598": ("research/agents_t598", "t598_alsenan",
             "(lambda d: [('ALSENAN_EDGES_T598.json#result', json.dumps(M.compute(d['reading']), indent=1, sort_keys=True)"
             " + '\\n', None), ('ALSENAN_EDGES_T598.json#result==committed', str(json.dumps(M.compute(d['reading']),"
             " sort_keys=True) == json.dumps(d['result'], sort_keys=True)), None)])(json.loads(M.OUT.read_text()))"),
    "t602": ("research/agents_t602", "t602_alsenan",
             "[('T602_DOOR_STEPS.json', json.dumps(M.build(), indent=1, sort_keys=True, ensure_ascii=True) + '\\n',"
             " 'out/T602_DOOR_STEPS.json')]"),
    "t607": ("research/agents_t607", "t607_alsenan", "[('T607_SHARED_RESIDUAL.json', M.dump(M.build()), 'out/T607_SHARED_RESIDUAL.json')]"),
    "t618": ("research/agents_t618", "t618_alsenan",
             "[('T618_RESIDUALS.json', json.dumps(M.build(), indent=1, ensure_ascii=False) + '\\n', 'out/T618_RESIDUALS.json')]"),
    "t627": ("research/agents_t627", "t627_alsenan",
             "(lambda b: [('T627_ROW_EVIDENCE.json', M.dumps(b), 'out/T627_ROW_EVIDENCE.json'),"
             " ('T627_ROW_EVIDENCE.md', M.render_md(b), 'out/T627_ROW_EVIDENCE.md')])(M.build())"),
    "t645": ("research/agents_t645", "t645_alsenan",
             "(lambda b: [('STAIR_HOLD_CENSUS_T645.json', M.dumps(b), 'out/STAIR_HOLD_CENSUS_T645.json'),"
             " ('STAIR_HOLD_CENSUS_T645.md', M.render_md(b), 'out/STAIR_HOLD_CENSUS_T645.md')])(M.build())"),
    "t646": ("research/agents_t646", "t646_alsenan",
             "(lambda b: [('ROOF_FENCE_HOLD_CENSUS_T646.json', M.dumps(b), 'out/ROOF_FENCE_HOLD_CENSUS_T646.json'),"
             " ('ROOF_FENCE_HOLD_CENSUS_T646.md', M.render_md(b), 'out/ROOF_FENCE_HOLD_CENSUS_T646.md')])(M.build())"),
}

CHILD = r"""
import sys, json, decimal, hashlib
from pathlib import Path
mode, folder, mod, expr = sys.argv[1:5]
if mode == "prec6":
    decimal.getcontext().prec = 6
before = decimal.getcontext().prec
sys.path.insert(0, folder)
import importlib
try:
    M = importlib.import_module(mod)
    after_import = decimal.getcontext().prec
    outs = eval(expr)
    err = None
except Exception as e:  # a builder that needs a private input fails the same way before and after
    outs, err, after_import = [], f"{type(e).__name__}: {e}", decimal.getcontext().prec
rows = []
for label, text, committed in outs:
    c = Path(folder) / committed if committed else None
    ch = hashlib.sha256(c.read_bytes()).hexdigest() if c is not None and c.exists() else None
    th = hashlib.sha256(text.encode("utf-8")).hexdigest()
    rows.append({"output": label, "rebuilt_sha256": th, "committed_sha256": ch,
                 "equal_committed": (th == ch) if ch else None, "text": text if len(text) < 40 else None})
print(json.dumps({"prec_before": before, "prec_after_import": after_import,
                  "prec_after_build": decimal.getcontext().prec, "error": err, "outputs": rows}))
"""


def run_one(root: Path, key: str, mode: str) -> dict:
    folder, mod, expr = SPECS[key]
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, "-I", "-B", "-c", CHILD, mode, str(root / folder), mod, expr],
                           capture_output=True, text=True, cwd=tmp, env=env, timeout=900)
    if r.returncode != 0:
        return {"error": f"exit {r.returncode}: {r.stderr.strip()[-400:]}", "outputs": []}
    return json.loads(r.stdout.strip().splitlines()[-1])


def eval_fixtures(root: Path, mode: str) -> dict:
    """the S6 Investigation A script: make the synthetic fixtures, evaluate them, hash the JSON."""
    d = root / "research/urban_m9_s6/phase1/review/fixtures_investigation_A"
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    with tempfile.TemporaryDirectory() as tmp:
        fx, out = Path(tmp) / "fx", Path(tmp) / "res.json"
        a = subprocess.run([sys.executable, "-I", "-B", str(d / "make_fixtures.py"), str(fx)], capture_output=True,
                           text=True, cwd=tmp, env=env)
        pre = "import decimal; decimal.getcontext().prec = 6; " if mode == "prec6" else ""
        code = (pre + "import sys, runpy; sys.argv = [sys.argv[1]] + sys.argv[2:]; "
                "runpy.run_path(sys.argv[0], run_name='__main__'); import decimal; "
                "print('PREC_AFTER', decimal.getcontext().prec)")
        b = subprocess.run([sys.executable, "-I", "-B", "-c", code, str(d / "eval_fixtures.py"), str(root), str(fx),
                            str(out)], capture_output=True, text=True, cwd=tmp, env=env)
        if a.returncode or b.returncode or not out.exists():
            return {"error": (a.stderr + b.stderr).strip()[-400:], "outputs": []}
        text = out.read_text()
        prec_after = int([x for x in b.stdout.splitlines() if x.startswith("PREC_AFTER")][-1].split()[1])
    committed = d / "A_FIXTURE_RESULTS.json"
    th = hashlib.sha256(text.encode()).hexdigest()
    ch = hashlib.sha256(committed.read_bytes()).hexdigest() if committed.exists() else None
    return {"prec_after_build": prec_after, "error": None,
            "outputs": [{"output": "A_FIXTURE_RESULTS.json", "rebuilt_sha256": th, "committed_sha256": ch,
                         "equal_committed": th == ch if ch else None, "text": None}]}


def ledger(root: Path, keys=None) -> dict:
    res = {}
    for key in (keys or list(SPECS) + ["eval_fixtures"]):
        res[key] = {}
        for mode in ("default", "prec6"):
            res[key][mode] = eval_fixtures(root, mode) if key == "eval_fixtures" else run_one(root, key, mode)
    return res


def main(argv):
    root = Path(argv[argv.index("--root") + 1]).resolve() if "--root" in argv else ROOT
    keys = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None
    res = ledger(root, keys)
    text = json.dumps(res, indent=1, sort_keys=True) + "\n"
    if "--out" in argv:
        Path(argv[argv.index("--out") + 1]).write_text(text)
    for k, v in res.items():
        for mode, r in v.items():
            for o in r.get("outputs", []):
                print(f"{k:13s} {mode:8s} prec_after={r.get('prec_after_build')} {o['output']:42s} "
                      f"{o['rebuilt_sha256'][:16]} committed={'-' if o['equal_committed'] is None else o['equal_committed']}"
                      f"{' ' + o['text'] if o.get('text') else ''}")
            if r.get("error"):
                print(f"{k:13s} {mode:8s} ERROR {r['error'][:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
