"""Freeze a blind run's artifacts: every file, by hash, in one index.

    python -m tools.a18_freeze_artifacts --run-dir <dir> --out <index>.json

An external reviewer needs two things this produces: the exact list of
what the run wrote, and a hash per file so that the thing they read is
the thing the run produced. Directories are indexed file by file rather
than as a count, because "15 overlays" is not a record of anything.

The index hashes itself last, over everything else.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine import export_provenance as prov

SKIP = {".pyc"}


def index(run_dir) -> dict:
    root = Path(run_dir)
    groups: dict = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix in SKIP:
            continue
        rel = path.relative_to(root)
        group = str(rel.parent) if str(rel.parent) != "." else "(root)"
        groups.setdefault(group, []).append({
            "file": str(rel),
            "bytes": path.stat().st_size,
            prov.RAW: prov.raw_sha256(path),
        })
    doc = {
        "MODEL": "A_FROZEN_RUN_IS_A_LIST_OF_HASHES_V1",
        "run_dir": str(root),
        "groups": groups,
        "counts": {k: len(v) for k, v in groups.items()},
        "files_total": sum(len(v) for v in groups.values()),
        "what_this_is": ("every file this run wrote, by hash, so that a "
                         "reviewer can tell that what they are reading is "
                         "what the run produced"),
    }
    doc["ARTIFACT_INDEX_HASH"] = prov.canonical_sha256(doc)
    return doc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    doc = index(a.run_dir)
    Path(a.out).write_text(json.dumps(doc, indent=2, ensure_ascii=False)
                           + "\n", encoding="utf-8")
    print(json.dumps({"files_total": doc["files_total"],
                      "counts": doc["counts"],
                      "ARTIFACT_INDEX_HASH":
                          doc["ARTIFACT_INDEX_HASH"][:16]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
