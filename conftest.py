"""Session-level determinism guard (R8.6 §15-§16).

Invariant: same committed tree + same declared fixture set = same test result on the first and the second
execution. The guard enforces its precondition: NO test may create, modify or delete a file under the truth
roots (the fixture data and the test tree). A test that rewrites its own expected truth makes a first run
differ from a second; that is a failure of the run, not something a re-run is allowed to clear.

The snapshot is (size, mtime_ns) of every file under the roots, taken before collection and compared after the
session; any difference fails the session (exit status 1) and lists the files. Writes into pytest's tmp_path
are outside the roots and unaffected.

URBAN_DETERMINISM_GUARD=report  only prints the list (diagnosis);  =off  disables it.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRUTH_ROOTS = ("data", "tests")
SKIP_DIRS = {"__pycache__", ".pytest_cache"}


def truth_snapshot(root: Path = ROOT, roots=TRUTH_ROOTS) -> dict:
    out = {}
    for r in roots:
        base = root / r
        for dp, dn, fs in os.walk(base):
            dn[:] = [d for d in dn if d not in SKIP_DIRS]
            for f in fs:
                p = os.path.join(dp, f)
                try:
                    st = os.stat(p)
                except FileNotFoundError:
                    continue
                out[os.path.relpath(p, root)] = (st.st_size, st.st_mtime_ns)
    return out


def snapshot_diff(before: dict, after: dict) -> dict:
    return {"created": sorted(set(after) - set(before)),
            "deleted": sorted(set(before) - set(after)),
            "modified": sorted(k for k in set(before) & set(after) if before[k] != after[k])}


def pytest_sessionstart(session):
    session.config._urban_truth_snapshot = truth_snapshot()


def pytest_sessionfinish(session, exitstatus):
    mode = os.environ.get("URBAN_DETERMINISM_GUARD", "enforce")
    before = getattr(session.config, "_urban_truth_snapshot", None)
    if mode == "off" or before is None:
        return
    d = snapshot_diff(before, truth_snapshot())
    if not any(d.values()):
        return
    tr = session.config.pluginmanager.get_plugin("terminalreporter")
    lines = [f"DETERMINISM GUARD: the test session wrote to the truth roots {TRUTH_ROOTS}"]
    for k, v in d.items():
        lines += [f"  {k}: {p}" for p in v[:50]] + ([f"  {k}: ... {len(v) - 50} more"] if len(v) > 50 else [])
    for line in lines:
        (tr.write_line(line) if tr else print(line))
    if mode == "enforce":
        session.exitstatus = 1
