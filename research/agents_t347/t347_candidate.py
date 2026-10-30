"""T-347 candidate snapshot (read-only): from a finished ARCH_TAKEOFF_V3.0.24 run (research/agents_t338/v3024_run.py
on the Drive copies), write every line a buried-structure displacement row can bind to (STR.CONC.* of the buried
families, every WP.* line, every screed / lift-pit / pool-layer line) and the census of earthworks lines (expected:
none, B1-02 / B1-03 / B1-04 not integrated). Engine ids, item codes, states and quantities only (as T-293 / T-332).

    python3 -I research/agents_t347/t347_candidate.py <run dir of v3024_run.py> research/agents_t347/CANDIDATE_V3024_BURIED_LINES.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t289"))
import t289_extract as X  # noqa: E402

BURIED = ("STR.CONC.FOOTING", "STR.CONC.BLINDING", "STR.CONC.NECK", "STR.CONC.STRAP", "STR.CONC.GROUND_BEAM",
          "STR.CONC.POOL", "STR.CONC.BOUNDARY_WALL", "STR.CONC.LIFT", "STR.CONC.GROUND_SLAB")
EARTH = ("EXCAV", "BACKFILL", "DISPOSAL", "EARTH", "FILL.", "SOIL")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def wanted(code):
    c = (code or "").upper()
    return c.startswith(BURIED) or c.startswith("WP.") or "SCREED" in c or "LIFT" in c or "POOL" in c


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    if len(a) != 2:
        raise SystemExit(__doc__)
    run = Path(a[0])
    js = sorted(run.rglob("V3_0_24_BOQ_LINES.json"))
    cs = sorted(run.rglob("V3_0_24_BOQ_LINES.csv"))
    if len(js) != 1:
        raise SystemExit(f"expected one V3_0_24_BOQ_LINES.json under {run}, found {len(js)}")
    data = json.loads(js[0].read_text(encoding="utf-8"))
    lines = data["lines"] if isinstance(data, dict) else data
    keep, earth, codes = [], [], {}
    for l in lines:
        code = l.get("item_code") or ""
        codes[code] = codes.get(code, 0) + 1
        if wanted(code):
            s = X._slim(l)
            s["state_detail"] = {k: l.get(k) for k in ("release_status", "verification_status", "blocked_reason")
                                 if l.get(k) not in (None, "")}
            keep.append(s)
        if any(t in code.upper() for t in EARTH) or code.upper().startswith(("B1-", "SITE.")):
            earth.append({"line_id": l.get("line_id"), "item_code": code})
    out = {"schema": "T347_CANDIDATE_BURIED_LINES_V1", "candidate": "ARCH_TAKEOFF_V3.0.24",
           "candidate_lines_json_sha256": _sha(js[0]),
           "candidate_lines_csv_sha256": _sha(cs[0]) if cs else None,
           "lines_in_candidate": len(lines), "earthworks_lines_in_candidate": sorted(earth, key=lambda e: e["line_id"]),
           "item_code_census": dict(sorted(codes.items())),
           "lines": sorted(keep, key=lambda s: s["line_id"])}
    Path(a[1]).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(keep)} buried / WP lines of {len(lines)}; earthworks lines {len(earth)}; json {out['candidate_lines_json_sha256'][:8]}")


if __name__ == "__main__":
    main()
