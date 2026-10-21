"""Report the state of every locked test prerequisite: PRESENT, MISSING or DRIFTED (sha256 differs).

    python3 -I research/environment_recovery/check_prerequisites.py [INPUTS.lock.json]

Stdlib only. Reads hashes, never prints file content. Exit 0 when nothing has drifted (missing entries are reported,
because tests skip them with a stated reason); exit 1 when a present file's sha256 differs from the lock (drift is
never absorbed).
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check(lock_path):
    lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    rows = []
    for e in lock["entries"]:
        p = ROOT / e["path"]
        if not p.exists():
            state = "MISSING"
        elif p.is_dir() or not e.get("sha256"):
            state = "PRESENT (no pinned sha256)"
        else:
            state = "PRESENT" if sha256(p) == e["sha256"] else "DRIFTED"
        rows.append({"path": e["path"], "store": e.get("store"), "state": state})
    return rows


def main(argv):
    lock = argv[1] if len(argv) > 1 else Path(__file__).with_name("INPUTS.lock.proposed.json")
    rows = check(lock)
    for r in rows:
        print(f"{r['state']:<28} {r['store'] or '':<10} {r['path']}")
    c = Counter(r["state"] for r in rows)
    print(dict(c))
    return 1 if c.get("DRIFTED") else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
