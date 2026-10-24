"""T-248: values-only digest of the STR.CONC.COLUMN / STR.CONC.NECK lines of the released baseline A run and of the
V3.0.9 candidate.

    python3 -I research/agents_t248/t248_released_a.py <run dir of tools/release_baseline.py run
        research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json> [--write]
    python3 -I research/agents_t248/t248_released_a.py --v309 <dir v309 of a research/agents_t211/v309_run.py run> [--write]

Writes RELEASED_A_COLUMN_LINES.json: line id, floor, mark, evidence state, rfi, schedule section, bounds (no
coordinates, no element ids). Asserts the run is the pinned baseline (BOQ_LINES.csv sha256 b96185d4...).
"""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIN = "b96185d468524743e600f1992d4e4b2028193ff4a379961bc5686c9662f8c115"
PIN_V309 = "63b350cf270110bf76f86f2f6da5ea515bf8ba796bbd7f6917a1050c469d600f"   # V3_0_9_BOQ_LINES.csv, own run


def digest(run: Path, stem: str = "BOQ_LINES", pin: str = PIN, baseline: str = "V29_ROUTEG_NO_PROFILE") -> dict:
    assert hashlib.sha256((run / f"{stem}.csv").read_bytes()).hexdigest() == pin, f"not the pinned {baseline} run"
    lines = json.loads((run / f"{stem}.json").read_text(encoding="utf-8"))
    lines = lines["lines"] if isinstance(lines, dict) else lines
    out = []
    for ln in lines:
        if ln["item_code"] not in ("STR.CONC.COLUMN", "STR.CONC.NECK"):
            continue
        eid = ln["location"]["element_id"] or ""
        m = re.search(r":(C\d*|CN|PC[^@]*)@", eid)
        dims = (ln.get("calculation") or {}).get("inputs", {}).get("dimensions", {}) or {}
        br = ln.get("bounded_range") or {}
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"]["floor"],
                    "mark": m.group(1) if m else "", "state": ln["evidence_state"],
                    "rfi": (ln.get("rfi") or {}).get("question", ""), "section_m": dims.get("section_m"),
                    "measured_net": ln.get("measured_net"),
                    "bounded": [br.get("low"), br.get("high")] if br else None})
    out.sort(key=lambda r: (r["item_code"], r["floor"], r["mark"], r["line_id"]))
    counts = Counter((r["item_code"], r["floor"], r["state"]) for r in out)
    return {"schema": "T248_RELEASED_A_V1", "baseline": baseline, "boq_lines_csv_sha256": pin,
            "counts": {"|".join(k): v for k, v in sorted(counts.items())}, "lines": out}


if __name__ == "__main__":
    if sys.argv[1] == "--v309":
        d = digest(Path(sys.argv[2]), "V3_0_9_BOQ_LINES", PIN_V309, "ARCH_TAKEOFF_V3.0.9 candidate (NOT RELEASED)")
        name = "CANDIDATE_V309_COLUMN_LINES.json"
    else:
        d = digest(Path(sys.argv[1]))
        name = "RELEASED_A_COLUMN_LINES.json"
    if "--write" in sys.argv:
        (HERE / name).write_text(json.dumps(d, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(d["counts"], indent=0))
    print(Counter((r["floor"], r["mark"]) for r in d["lines"] if r["item_code"] == "STR.CONC.COLUMN"))
