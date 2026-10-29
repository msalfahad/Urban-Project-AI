"""T-332 candidate snapshot (read-only): from a finished ARCH_TAKEOFF_V3.0.21 run (research/agents_t315/v3021_run.py on
the Drive copies), write every line whose item code is STR.CONC.* (the members formwork faces bind to) and the census
of formwork-trade lines (expected: none). Engine ids, item codes, states and quantities only (as the T-293 snapshot).

    python3 -I research/agents_t332/t332_candidate.py <run dir of v3021_run.py> research/agents_t332/CANDIDATE_V3021_CONCRETE_LINES.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t289"))
import t289_extract as X  # noqa: E402


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    if len(a) != 2:
        raise SystemExit(__doc__)
    run = Path(a[0])
    js = sorted(run.rglob("V3_0_21_BOQ_LINES.json"))
    cs = sorted(run.rglob("V3_0_21_BOQ_LINES.csv"))
    if len(js) != 1:
        raise SystemExit(f"expected one V3_0_21_BOQ_LINES.json under {run}, found {len(js)}")
    data = json.loads(js[0].read_text(encoding="utf-8"))
    lines = data["lines"] if isinstance(data, dict) else data
    conc, fw = [], []
    for l in lines:
        code = l.get("item_code") or ""
        if code.startswith("STR.CONC."):
            s = X._slim(l)
            s["state_detail"] = {k: l.get(k) for k in ("release_status", "verification_status", "blocked_reason")
                                 if l.get(k) not in (None, "")}
            conc.append(s)
        if "FORMWORK" in code.upper() or code.upper().startswith(("FW.", "STR.FW", "STR.FORM")) \
                or (l.get("trade") or "").upper() == "FORMWORK":
            fw.append(l.get("line_id"))
    out = {"schema": "T332_CANDIDATE_CONCRETE_LINES_V1", "candidate": "ARCH_TAKEOFF_V3.0.21",
           "candidate_lines_json_sha256": _sha(js[0]),
           "candidate_lines_csv_sha256": _sha(cs[0]) if cs else None,
           "lines_in_candidate": len(lines), "formwork_lines_in_candidate": sorted(x for x in fw if x),
           "lines": sorted(conc, key=lambda s: s["line_id"])}
    Path(a[1]).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(conc)} STR.CONC lines of {len(lines)}; formwork lines {len(fw)}; json {out['candidate_lines_json_sha256'][:8]}")


if __name__ == "__main__":
    main()
