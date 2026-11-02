"""T-458 step 1 (read-only): RUN-TIME reachability of the legacy 0.15 m wet-room upturn and the upturn door deduction.

Runs one research run script (research/agents_t167/v304_run.py, research/agents_t430/v3040_run.py, ...) in-process under
three cheap run-time probes and writes a JSON trace (module names, function names, rule ids, file names only; no
coordinates, no drawing content):

  1. IMPORTS: every module imported during the run (sys.modules after the run, filtered to engine.* / tools.*), and
     whether each SUSPECT module below was imported at all.
  2. CALLS: every function defined in a SUSPECT module is wrapped as the module finishes loading; each call is counted.
  3. RULE READS: engine.source.rule_store.rule / rule_set / rule_ref and engine.rule_library.load / resolve are wrapped;
     every call records (rule id, version asked, value returned) for UP-WP-* ids; plus an audit hook records every
     JSON file opened under rules/, data/trade_rules/, knowledge/.

    python3 -I research/agents_t458/t458_trace.py --trace <out.json> <run script> <run script args ...>

A module that is never imported cannot apply its constants; a SUSPECT function never called cannot produce a quantity.
"""

from __future__ import annotations

import functools
import importlib.abc
import importlib.machinery
import inspect
import json
import runpy
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# every engine site that still carries the legacy 0.15 m wet upturn or an upturn door deduction (T-458 census)
SUSPECT = {
    "engine.source.waterproofing_policy": "WET_UPTURN_M = 0.15; wet() deducts door widths from the upturn length",
    "engine.source.room_slice": "UPTURN_M = 0.15; wp_upturn_m2 = (perimeter - door widths) x 0.15",
    "engine.finishes_rules": "UPTURN_M = 0.15; upturn(wall_run, openings_lm=...) deducts openings",
    "engine.source.arch_quantity_truth": "waterproofing(upturn_m=0.15) default",
    "engine.source.waterproofing": "same POLICY_ID WATERPROOFING_POLICY_V1 as waterproofing_policy (no door deduction)",
    "engine.rule_library": "loads the base library 1.4.0 (UP-WP-002 = 0.15, openings deducted) with no 1.5.0 overlay",
}
WATCHED_FILES = ("rules/", "data/trade_rules/", "knowledge/")

calls: Counter = Counter()
rule_reads: Counter = Counter()
opened: Counter = Counter()


def _wrap_module(mod):
    for name, obj in list(vars(mod).items()):
        if inspect.isfunction(obj) and obj.__module__ == mod.__name__:
            def mk(f, key):
                @functools.wraps(f)
                def w(*a, **k):
                    calls[key] += 1
                    return f(*a, **k)
                return w
            setattr(mod, name, mk(obj, f"{mod.__name__}.{name}"))


def _rule_probe(mod):
    if mod.__name__ == "engine.source.rule_store":
        orig = mod.rule

        @functools.wraps(orig)
        def rule(rule_id, version=mod.LATEST_APPROVED, include_proposed=False):
            r = orig(rule_id, version, include_proposed)
            if str(rule_id).startswith("UP-WP"):
                v = r.get("value") if isinstance(r, dict) else None
                rule_reads[f"rule_store.rule {rule_id} @{version} -> {v}"] += 1
            return r
        mod.rule = rule
    if mod.__name__ == "engine.rule_library":
        orig_res = mod.resolve

        @functools.wraps(orig_res)
        def resolve(library, rule_id, *a, **k):
            r = orig_res(library, rule_id, *a, **k)
            rule_reads[f"rule_library.resolve {rule_id}"] += 1
            return r
        mod.resolve = resolve


class _Loader(importlib.abc.Loader):
    def __init__(self, inner):
        self.inner = inner

    def create_module(self, spec):
        return self.inner.create_module(spec)

    def exec_module(self, module):
        self.inner.exec_module(module)
        if module.__name__ in SUSPECT:
            _wrap_module(module)
        _rule_probe(module)


class _Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name not in SUSPECT and name not in ("engine.source.rule_store", "engine.rule_library"):
            return None
        spec = importlib.machinery.PathFinder.find_spec(name, path)
        if spec is not None and spec.loader is not None:
            spec.loader = _Loader(spec.loader)
        return spec


def _audit(event, args):
    if event == "open" and args and isinstance(args[0], (str, Path)):
        p = str(args[0])
        if p.endswith(".json"):
            rel = p.replace(str(ROOT) + "/", "")
            if rel.startswith(WATCHED_FILES):
                opened[rel] += 1


def main():
    argv = sys.argv[1:]
    assert argv[0] == "--trace"
    out, script, rest = Path(argv[1]), argv[2], argv[3:]
    sys.path.insert(0, str(ROOT))
    sys.meta_path.insert(0, _Finder())
    sys.addaudithook(_audit)
    sys.argv = [script] + rest
    status = "OK"
    try:
        runpy.run_path(script, run_name="__main__")
    except SystemExit as e:
        status = f"SystemExit {e.code}"
    mods = sorted(m for m in sys.modules if m.startswith(("engine", "tools")))
    trace = {"script": script, "status": status,
             "suspect_imported": {m: (m in sys.modules) for m in SUSPECT},
             "suspect_reason": SUSPECT,
             "suspect_calls": dict(sorted(calls.items())),
             "up_wp_rule_reads": dict(sorted(rule_reads.items())),
             "rule_files_opened": dict(sorted(opened.items())),
             "engine_modules_imported": len(mods)}
    out.write_text(json.dumps(trace, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({k: trace[k] for k in ("status", "suspect_imported", "suspect_calls", "up_wp_rule_reads",
                                             "rule_files_opened")}, indent=1))


if __name__ == "__main__":
    main()
