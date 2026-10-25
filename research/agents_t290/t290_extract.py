"""T-290 read-only digest of the candidate's stair / dome concrete lines (values, states and engine ids only: no
coordinates, no names).

    python3 -I research/agents_t290/t290_extract.py <run>/v3015 --out research/agents_t290

<run> is a finished research/agents_t270/v3015_run.py run on the Drive copies (after research/agents_t167/v304_run.py).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ITEMS = ("STR.CONC.STAIR", "STR.CONC.DOME")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def digest(run: Path) -> dict:
    d = json.loads((run / "V3_0_15_BOQ_LINES.json").read_text(encoding="utf-8"))
    L = d if isinstance(d, list) else d["lines"]
    sel = []
    for l in L:
        if not (l["item_code"].startswith(ITEMS) and l["unit"] == "m3"):
            continue
        inp = (l.get("calculation") or {}).get("inputs") or {}
        dg = inp.get("default_guard") or {}
        info = dg.get("info_qty_v3_0_5") or (inp.get("misread") or {}).get("info_qty_v3_0_5") or {}
        br = l.get("bounded_range") or {}
        sel.append({"line_id": l["line_id"], "item_code": l["item_code"], "floor": l["location"]["floor"],
                    "element_id": l["location"]["element_id"], "evidence_state": l["evidence_state"],
                    "measured_net": l.get("measured_net"), "bounded_low": br.get("low"), "bounded_high": br.get("high"),
                    "guard_element": dg.get("guard_element") or ({"element_id": inp.get("element"), "part": inp.get("part")}
                                                                 if inp.get("element") else None),
                    "info_qty_v3_0_5": info.get("value"), "support": inp.get("support"),
                    "formula": (l.get("calculation") or {}).get("formula")})
    return {"schema": "T290_CANDIDATE_V3015_STAIR_DOME_LINES", "candidate": "ARCH_TAKEOFF_V3.0.15",
            "candidate_lines_csv_sha256": _sha(run / "V3_0_15_BOQ_LINES.csv"), "project": L[0]["project"],
            "lines_in_candidate": len(L), "lines": sorted(sel, key=lambda x: x["line_id"])}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "CANDIDATE_V3015_STAIR_DOME_LINES.json").write_text(
        json.dumps(digest(Path(a.run)), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
