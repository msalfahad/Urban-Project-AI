"""BENCHMARK FIREWALL (V1) - prove what a measurement run did NOT read.

A development validation must be frozen before any benchmark is seen. Saying so is not enough: this module makes
the claim executable.

classify()      a repository / upload path -> ROLE CLASS by the FIRST matching rule (path patterns only; the file is
                never opened). Classes: SOURCE, SOURCE_DERIVED, CODE, GENERIC_TEST, HISTORICAL_PROJECT_RESULT,
                BENCHMARK_GOLD, MANUAL_BOQ, COST_DATA, PROJECT_FACT, UNRELATED_UPLOAD, UNCLASSIFIED.
census()        classify a whole path list (counts per class, every entry, the unclassified ones).
OpenAudit       context manager: records EVERY file the process opens while it is active (a process audit hook,
                installed once; inactive recorders cost nothing).
verdict()       FAIL when any opened path falls in a DENIED class; the violations are named. No path is excused.
module_verdict  FAIL when a loaded module name matches a denied module pattern.

Project-agnostic: the rules (patterns -> class) are supplied by the caller; stdlib only.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import sys
from dataclasses import dataclass

POLICY_ID = "BENCHMARK_FIREWALL_V1"
SOURCE, SOURCE_DERIVED, CODE, GENERIC_TEST = "SOURCE", "SOURCE_DERIVED", "CODE", "GENERIC_TEST"
HISTORICAL_PROJECT_RESULT, BENCHMARK_GOLD = "HISTORICAL_PROJECT_RESULT", "BENCHMARK_GOLD"
MANUAL_BOQ, COST_DATA, PROJECT_FACT = "MANUAL_BOQ", "COST_DATA", "PROJECT_FACT"
UNRELATED_UPLOAD, UNCLASSIFIED = "UNRELATED_UPLOAD", "UNCLASSIFIED"
CLASSES = (SOURCE, SOURCE_DERIVED, CODE, GENERIC_TEST, HISTORICAL_PROJECT_RESULT, BENCHMARK_GOLD, MANUAL_BOQ,
           COST_DATA, PROJECT_FACT, UNRELATED_UPLOAD, UNCLASSIFIED)
DENIED = frozenset({HISTORICAL_PROJECT_RESULT, BENCHMARK_GOLD, MANUAL_BOQ, COST_DATA, PROJECT_FACT, UNRELATED_UPLOAD})
PASS, FAIL = "PASS", "FAIL"


@dataclass(frozen=True)
class Rule:
    pattern: str        # fnmatch pattern on the POSIX path (relative to the repository root, or absolute)
    klass: str
    why: str = ""

    def __post_init__(self):
        if self.klass not in CLASSES:
            raise ValueError(f"unknown class {self.klass!r}")


def _norm(path, root=None) -> str:
    """A relative path stays relative to `root` (or as given when no root); an absolute path inside `root` becomes
    relative to it; any other absolute path stays absolute. Never resolved against the working directory."""
    p = os.path.normpath(os.fspath(path))
    if root is not None and os.path.isabs(p):
        r = os.path.normpath(os.fspath(root))
        if p == r or p.startswith(r + os.sep):
            p = os.path.relpath(p, r)
    return p.replace(os.sep, "/")


def classify(path, rules, root=None) -> tuple:
    """(class, pattern) of the first rule matching the path; (UNCLASSIFIED, None) otherwise."""
    p = _norm(path, root)
    for r in rules:
        if fnmatch.fnmatchcase(p, r.pattern):
            return r.klass, r.pattern
    return UNCLASSIFIED, None


def census(paths, rules, root=None) -> dict:
    entries = []
    for p in sorted({_norm(x, root) for x in paths}):
        k, pat = classify(p, rules, root)
        entries.append({"path": p, "class": k, "rule": pat})
    by = {}
    for e in entries:
        by[e["class"]] = by.get(e["class"], 0) + 1
    return {"policy": POLICY_ID, "files": len(entries), "by_class": dict(sorted(by.items())), "entries": entries,
            "unclassified": [e["path"] for e in entries if e["class"] == UNCLASSIFIED],
            "denied_present": sorted(e["path"] for e in entries if e["class"] in DENIED)}


_ACTIVE = []
_INSTALLED = False


def _hook(event, args):
    if not _ACTIVE or event != "open" or not args:
        return
    p = args[0]
    if isinstance(p, int):
        return
    try:
        s = os.fsdecode(p)
    except Exception:                                   # noqa: BLE001 - an undecodable name is recorded raw
        s = repr(p)
    for rec in _ACTIVE:
        rec.add(os.path.abspath(s))


class OpenAudit:
    """with OpenAudit() as a: ...   a.opened -> sorted absolute paths opened inside the block."""

    def __init__(self):
        self._seen = set()
        self.opened = ()

    def add(self, p):
        self._seen.add(p)

    def __enter__(self):
        global _INSTALLED
        if not _INSTALLED:
            sys.addaudithook(_hook)
            _INSTALLED = True
        _ACTIVE.append(self)
        return self

    def __exit__(self, *exc):
        _ACTIVE.remove(self)
        self.opened = tuple(sorted(self._seen))
        return False


def verdict(opened, rules, root=None) -> dict:
    rows, violations = [], []
    for p in sorted(set(opened)):
        k, pat = classify(p, rules, root)
        rows.append({"path": _norm(p, root), "class": k, "rule": pat})
        if k in DENIED:
            violations.append({"path": _norm(p, root), "class": k, "rule": pat})
    return {"policy": POLICY_ID, "state": FAIL if violations else PASS, "opened": len(rows),
            "by_class": {k: sum(1 for r in rows if r["class"] == k) for k in sorted({r["class"] for r in rows})},
            "violations": violations, "files": rows}


def module_verdict(module_names, denied_patterns) -> dict:
    hits = sorted(m for m in set(module_names) if any(fnmatch.fnmatchcase(m, p) for p in denied_patterns))
    return {"policy": POLICY_ID, "state": FAIL if hits else PASS, "denied_patterns": list(denied_patterns),
            "violations": hits}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "classes": list(CLASSES), "denied": sorted(DENIED),
           "rule": "a run passes only when no opened file and no loaded module falls in a denied class; files are "
                   "classified by PATH / ROLE only and never opened to be classified",
           "never": ["opening a benchmark to classify it", "excusing a denied path", "a run without its opened-file log"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
