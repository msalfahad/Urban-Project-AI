"""T-478 read-only run: ARCH_TAKEOFF_V3.0.45 (the CONC.BLINDING package) on the candidate of record, from a finished
research/agents_t350/v3043_run.py run on the development villa's Drive copies (its V3_0_43_BOQ_LINES.json = the
candidate of record 6f534d5e; asserted by sha256 prefix). Built WITHOUT the hub's shared files (Lead merge-order rule
2026-11-02 20:17: T-422 and T-478 build without each other; the hub wiring is added when the second rebases).
Every output goes to --out (outside the repository); printed: codes, units, states, quantities, ids only.

    .work/venv/bin/python -I research/agents_t478/v3045_run.py --v3043 <private>/t350 --released <v29 BOQ_LINES.json>
        --out <private>/t478 [--base-sha 6f534d5e]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import t478_inputs as IN  # noqa: E402
from engine.source import arch_v3045 as M  # noqa: E402

BASE_SHA = "6f534d5e"            # V3_0_43_BOQ_LINES.json of the candidate of record (T-350 Gate B, merge 3077469a)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--v3043", required=True, help="a finished v3043_run.py --out directory")
    ap.add_argument("--released", required=True, help="the released V2.9 BOQ_LINES.json of the same run")
    ap.add_argument("--out", required=True)
    ap.add_argument("--base-sha", default=BASE_SHA)
    a = ap.parse_args(argv)
    src = Path(a.v3043).resolve()
    lp = src / "v3043" / "V3_0_43_BOQ_LINES.json"
    raw = lp.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if not sha.startswith(a.base_sha):
        raise SystemExit(f"base candidate {sha[:8]} is not {a.base_sha} (not the candidate of record)")
    prev = json.loads(raw)
    released = json.loads(Path(a.released).read_text(encoding="utf-8"))
    inp24 = json.loads((src / "v3024_inputs.json").read_text(encoding="utf-8"))
    fl24 = [x["line_id"] for x in inp24.get("for_lead") or ()]
    pid = prev[0]["project"]["project_id"]
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    doc = IN.build(pid)
    (out / "v3045_inputs.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    d = M.load_inputs(doc, pid)
    ch, log = M.changes_for(d, prev)
    names, ident, _led = M.write(out, prev, ch, log, released, fl24, doc=d)
    run = json.loads((out / "V3_0_45_RUN.json").read_text(encoding="utf-8"))
    new = (out / "V3_0_45_BOQ_LINES.json").read_bytes()
    print("base:", sha[:8], "lines", len(prev), "-> V3_0_45_BOQ_LINES.json", hashlib.sha256(new).hexdigest()[:8],
          "lines", ident["v3_0_45_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows",
                                                          "outside_rows_identical_to_base", "blinding", "diff")},
                                  sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    print("plate:", json.dumps(run["plate"], indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
