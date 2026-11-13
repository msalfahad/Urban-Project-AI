"""T-314 r3: the package summary from a finished v3079_run.py output folder (item codes, units, states, quantities and
line ids only; no coordinate, no name): out/T314_SUMMARY.json, out/V3_0_79_INTEGRATION_LEDGER.csv and out/V3_0_79_DIFF.csv.

    python3 -I research/agents_t314/t314_summary.py <run dir holding V3_0_78 / V3_0_79_* files>
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(argv=None):
    d = Path((sys.argv[1:] if argv is None else argv)[0])
    run = json.loads((d / "V3_0_79_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    sha = {v: hashlib.sha256((d / f"V3_0_{v}_BOQ_LINES.json").read_bytes()).hexdigest() for v in ("78", "79")}
    out = {"method": run["method"], "extends": run["extends"], "released_default": run["released_default"],
           "lines_sha256": {"V3_0_78": sha["78"], "V3_0_79": sha["79"]},
           "identity": {k: v for k, v in ident.items() if k not in ("census_before", "census_after")},
           "census_before": ident["census_before"], "census_after": ident["census_after"],
           "totals_moved_by_code": run["totals_moved_by_code"], "waiting_pieces": run["waiting_pieces"]}
    (HERE / "out" / "T314_SUMMARY.json").write_text(json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                                    encoding="utf-8")
    shutil.copyfile(d / "V3_0_79_INTEGRATION_LEDGER.csv", HERE / "out" / "V3_0_79_INTEGRATION_LEDGER.csv")
    shutil.copyfile(d / "V3_0_79_DIFF.csv", HERE / "out" / "V3_0_79_DIFF.csv")
    print("V3_0_78", sha["78"][:8], "-> V3_0_79", sha["79"][:8], "lines", ident["v3_0_79_lines"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
