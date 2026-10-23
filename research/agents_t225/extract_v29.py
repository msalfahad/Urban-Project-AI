"""T-225: the OLDER AUTOMATED blockwork source = the pinned released run A (V29_ROUTEG_NO_PROFILE, T-165).

Reads BOQ_LINES.csv of a run made with `tools/release_baseline.py run research/agents_t165/baselines/
V29_ROUTEG_NO_PROFILE.json --plan <P7757.dxf> --structural <ST7757 dxf.dxf> --out <dir>` and writes the MASONRY lines
(engine figures only, no drawing content) to V29_RUN_A_MASONRY_LINES.csv, with the sha256 of the run's BOQ_LINES.csv,
and its wall bands (ARCH_WALLS.json, figures only, no coordinates) to V29_RUN_A_WALL_BANDS.csv.

Usage: python3 -I extract_v29.py <run dir>            (writes the csv next to this file)
       python3 -I extract_v29.py <run dir> --check    (exit 1 if the committed csv differs)
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "V29_RUN_A_MASONRY_LINES.csv"
OUT_BANDS = HERE / "V29_RUN_A_WALL_BANDS.csv"
BAND_COLS = ["floor", "wall_id", "family", "kind", "gross_lm", "net_lm", "columns_in_wall_lm", "strip_m2", "source_count"]
EXPECTED_SHA = "b96185d468524743e600f1992d4e4b2028193ff4a379961bc5686c9662f8c115"
COLS = ["line_id", "floor", "item_code", "physical_element", "unit", "gross", "measured_net", "evidence_state",
        "rule_id", "rfi_head"]


def build(run_dir: Path) -> str:
    p = run_dir / "BOQ_LINES.csv"
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    if sha != EXPECTED_SHA:
        raise SystemExit(f"BOQ_LINES.csv sha {sha} is not the pinned run A {EXPECTED_SHA}: refused")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLS + ["boq_lines_sha256"])
    for r in csv.DictReader(p.open(encoding="utf-8")):
        if r["trade"] != "MASONRY":
            continue
        w.writerow([r["line_id"], r["floor"], r["item_code"], r["physical_element"], r["unit"], r["gross"],
                    r["measured_net"], r["evidence_state"], r["rule_id"], (r["rfi"] or "").split(":")[0], sha])
    return buf.getvalue()


def bands(run_dir: Path) -> str:
    """Run A's wall bands (ARCH_WALLS.json) without geometry: one row per band, engine figures only."""
    d = json.loads((run_dir / "ARCH_WALLS.json").read_text(encoding="utf-8"))
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(BAND_COLS)
    for fl in d["floors"]:
        for b in fl["walls"]:
            w.writerow([fl["floor"], b["wall_id"], b["family"], b["kind"], b["gross_lm"], b["net_lm"],
                        b["columns_in_wall_lm"], b["strip_m2"], len(b.get("source_ids") or [])])
    return buf.getvalue()


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    text, btext = build(Path(argv[0])), bands(Path(argv[0]))
    if "--check" in argv:
        return 0 if OUT.read_text(encoding="utf-8") == text and OUT_BANDS.read_text(encoding="utf-8") == btext else 1
    OUT.write_text(text, encoding="utf-8")
    OUT_BANDS.write_text(btext, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
