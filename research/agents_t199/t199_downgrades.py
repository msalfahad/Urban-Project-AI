"""T-199: the line ids the Checker's downgrade-only records hold on the candidate of record (board file
docs/agents/verdicts/V3.0.29/DOWNGRADES.json on agents/control), copied as ids only into DOWNGRADE_BOUND_V3029.json with
the board file's sha256, so the V3.0.30 inputs can refuse a valued formwork line on a concrete line a record holds.

    python3 -I research/agents_t199/t199_downgrades.py <board>/docs/agents/verdicts/V3.0.29/DOWNGRADES.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "DOWNGRADE_BOUND_V3029.json"


def main(argv=None):
    p = Path((sys.argv[1:] if argv is None else argv)[0])
    b = p.read_bytes()
    d = json.loads(b.decode("utf-8"))
    recs = [{"downgrade_id": r["downgrade_id"], "unit": r["unit"], "state": r["state"],
             "candidate_version": r["candidate_version"], "line_content_sha256": r["line_content_sha256"],
             "line_ids": sorted(r["line_ids"])}
            for r in d["downgrades"] if str(r.get("resolved")) != "True"]
    doc = {"schema": "T199_DOWNGRADE_BOUND_LINES_V1", "source": "agents/control docs/agents/verdicts/V3.0.29/DOWNGRADES.json",
           "source_sha256": hashlib.sha256(b).hexdigest(), "records": sorted(recs, key=lambda x: x["downgrade_id"])}
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(len(recs), sum(len(r["line_ids"]) for r in recs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
