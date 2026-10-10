"""Classify a full-suite run into what was proven, what could not run, and what broke; derive the project gate.

    python3 -I research/environment_recovery/classify_test_run.py <junit.xml> <out.json> [<commit>]

Every test case lands in exactly one class:
  EXECUTED_PASSED                     ran and passed (the only class that proves anything)
  SKIPPED_PREREQUISITE_UNAVAILABLE    skipped because a private input / fixture is absent (never counted as a pass)
  SKIPPED_OTHER                       skipped for any other stated reason
  EXPECTED_FAILURE                    pytest xfail (a known limitation, recorded by the test itself)
  MANDATORY_BLOCKED_BY_MISSING_DATA   failed or errored because a required file is missing (names the path)
  CODE_FAILURE                        failed or errored for any other reason
The complete-project regression gate is COMPLETE only when nothing is blocked by missing data, no prerequisite skip
remains, every locked mandatory prerequisite is present and there is no code failure. Any code failure makes it FAILED;
otherwise missing data or prerequisites keep it INCOMPLETE. Missing-data skips are never presented as passes.
Paths and test ids only: no file content, no benchmark value.
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PASSED, SKIP_PREREQ, SKIP_OTHER, XFAIL = ("EXECUTED_PASSED", "SKIPPED_PREREQUISITE_UNAVAILABLE", "SKIPPED_OTHER",
                                           "EXPECTED_FAILURE")
BLOCKED, CODE = "MANDATORY_BLOCKED_BY_MISSING_DATA", "CODE_FAILURE"
CLASSES = (PASSED, SKIP_PREREQ, SKIP_OTHER, XFAIL, BLOCKED, CODE)
MISSING_PATH = re.compile(r"No such file or directory: '([^']+)'")
PREREQ_FAILURE = re.compile(r"\brun \w+ first\b", re.I)          # a test that needs an earlier generated artefact
PREREQ_SKIP = re.compile(r"not restored|not present|not available|not on disk|not on this machine|not mounted|absent|"
                         r"missing|not found|no such|private|prerequisite|fixture|client data|not in git|"
                         r"\brun \S+ first\b|\bunset\b|input|drawing|workbook|upload", re.I)


def classify_case(tc):
    kids = [x for x in tc if x.tag in ("failure", "error", "skipped")]
    if not kids:
        return PASSED, None, None
    x = kids[0]
    msg = (x.get("message") or "") + " " + (x.text or "")
    if x.tag == "skipped":
        if (x.get("type") or "").endswith("xfail") or msg.lstrip().startswith("xfail"):
            return XFAIL, None, re.sub(r"\s+", " ", x.get("message") or "")[:160]
        reason = re.sub(r"\s+", " ", x.get("message") or "")[:200]
        return (SKIP_PREREQ if PREREQ_SKIP.search(reason) else SKIP_OTHER), None, reason
    m = MISSING_PATH.search(msg)
    if m:
        return BLOCKED, m.group(1).replace(str(ROOT) + "/", ""), None
    if PREREQ_FAILURE.search(msg):
        return BLOCKED, "(generated prerequisite: " + PREREQ_FAILURE.search(msg).group(0) + ")", None
    return CODE, None, re.sub(r"\s+", " ", x.get("message") or "")[:200]


def lock_status(lock_path):
    if not lock_path.exists():
        return {"lock": None, "entries": 0, "missing": None}
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    miss = [e["path"] for e in lock.get("entries", []) if not e["path"].startswith("/") and not (ROOT / e["path"]).exists()]
    by_store = Counter(e["store"] for e in lock.get("entries", []) if e["path"] in set(miss))
    rel = str(lock_path.relative_to(ROOT)) if lock_path.is_relative_to(ROOT) else str(lock_path)
    return {"lock": rel, "entries": len(lock.get("entries", [])), "missing": len(miss),
            "missing_by_store": dict(sorted(by_store.items()))}


def classify(xml, commit=None, lock_path=HERE / "INPUTS.lock.proposed.json"):
    cases = list(ET.parse(xml).getroot().iter("testcase"))
    out = defaultdict(list)
    blocked_paths = Counter()
    skip_reasons = Counter()
    other_reasons = Counter()
    for tc in cases:
        tid = f"{tc.get('classname')}::{tc.get('name')}"
        cls, path, reason = classify_case(tc)
        out[cls].append(tid)
        if cls == BLOCKED:
            blocked_paths["/".join(path.split("/")[:3]) if not path.startswith("(") else path] += 1
        elif cls in (SKIP_PREREQ, SKIP_OTHER):
            skip_reasons[(cls, reason)] += 1
        elif cls == CODE:
            other_reasons[reason] += 1
    counts = {c: len(out[c]) for c in CLASSES}
    lock = lock_status(lock_path)
    reasons = []
    if counts[CODE]:
        reasons.append(f"{counts[CODE]} code failures")
    if counts[BLOCKED]:
        reasons.append(f"{counts[BLOCKED]} mandatory regression tests blocked by missing data")
    if counts[SKIP_PREREQ]:
        reasons.append(f"{counts[SKIP_PREREQ]} tests skipped for an unavailable prerequisite")
    if lock["missing"]:
        reasons.append(f"{lock['missing']} locked prerequisites missing {lock['missing_by_store']}")
    gate = "FAILED" if counts[CODE] else ("INCOMPLETE" if reasons else "COMPLETE")
    return {"schema": "URBAN_TEST_GATE_V1", "commit": commit, "junit": Path(xml).name, "total": len(cases),
            "counts": counts, "complete_project_regression_gate": gate, "gate_reasons": reasons,
            "rule": "only EXECUTED_PASSED proves anything; a prerequisite skip is not a pass; the gate is COMPLETE only "
                    "with no blocked, skipped-for-prerequisite or failed test and every locked prerequisite present",
            "blocked_by_missing_path": dict(sorted(blocked_paths.items(), key=lambda kv: -kv[1])),
            "skip_reasons": [{"class": c, "reason": r, "tests": n} for (c, r), n in
                             sorted(skip_reasons.items(), key=lambda kv: -kv[1])],
            "code_failure_reasons": dict(sorted(other_reasons.items(), key=lambda kv: -kv[1])),
            "mandatory_blocked_tests": sorted(out[BLOCKED]), "code_failure_tests": sorted(out[CODE]),
            "prerequisite_skipped_tests": sorted(out[SKIP_PREREQ]), "locked_prerequisites": lock}


def main(argv):
    if len(argv) < 3:
        raise SystemExit("usage: classify_test_run.py <junit.xml> <out.json> [<commit>]")
    rep = classify(argv[1], argv[3] if len(argv) > 3 else None)
    Path(argv[2]).write_text(json.dumps(rep, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("counts", "complete_project_regression_gate", "gate_reasons")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
