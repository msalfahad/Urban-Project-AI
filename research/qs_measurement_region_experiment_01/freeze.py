"""Freeze QS_MEASUREMENT_REGION_EXPERIMENT_01 and stop."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_measurement_region_experiment_01 import protocol as P
from research.qs_measurement_region_experiment_01.build import OUT, sha_file


def main() -> int:
    rev = json.loads((OUT / "REVERSIBILITY_TEST.json").read_text("utf-8"))
    met = json.loads((OUT / "METRIC_SEPARATION.json").read_text("utf-8"))

    files = {str(p.relative_to(OUT)): sha_file(p)
             for p in sorted(OUT.rglob("*"))
             if p.is_file() and p.name != "FREEZE.json"}
    freeze = hashlib.sha256(json.dumps(
        {k: files[k] for k in sorted(files)}, sort_keys=True).encode()
    ).hexdigest()

    body = {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "EXPERIMENT_CLASS": P.EXPERIMENT_CLASS,
        "PROTOCOL_HASH": P.protocol_hash(),
        "THE_PURPOSE": P.THE_PURPOSE,
        "WHAT_THIS_IS_NOT": P.WHAT_THIS_IS_NOT,
        "REVERSIBILITY_VERDICT": rev["VERDICT"],
        "HASH_A_EQUALS_HASH_C": rev["HASH_A_EQUALS_HASH_C"],
        "STATE_A_HASH": rev["STATE_A_HASH"],
        "STATE_C_HASH": rev["STATE_C_HASH"],
        "METRICS": {k: met[k] for k in P.METRICS_REPORTED_SEPARATELY},
        "NO_GENERIC_CLOSED_ROOMS_METRIC": P.NO_GENERIC_CLOSED_ROOMS_METRIC,
        "NO_AREA_IS_COMPUTED": P.NO_AREA_IS_COMPUTED,
        "NOTHING_IS_WRITTEN_BACK": P.NOTHING_IS_WRITTEN_BACK,
        "STANDING_PROHIBITIONS_HELD": [
            "E1.4 was read and not modified",
            "E1.5 was not created",
            "E2 was not started",
            "A19 was not run and no A19 answer was read",
            "A19 scoring was not reopened",
            "no Excel or manual benchmark quantity was opened",
            "no known P7757 target m2 was calculated or reconciled",
            "nothing was tuned to a known room area",
            "no plaster m2 and no floor m2 was calculated",
            "A21 and A22 were not implemented",
        ],
        "files": len(files),
        "FREEZE_SHA256": freeze,
        "FILES": {k: files[k] for k in sorted(files)},
    }
    (OUT / "FREEZE.json").write_text(
        json.dumps(body, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(json.dumps({"FREEZE_SHA256": freeze, "files": len(files),
                      "REVERSIBILITY": rev["VERDICT"],
                      "METRICS": body["METRICS"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
