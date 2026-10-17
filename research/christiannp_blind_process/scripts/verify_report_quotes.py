"""Check every REPORT_EXPLICIT item imported from the owner's quotation against the sealed report itself.

Place the file unchanged at research/christiannp_blind_process/process_log/CHRISTIANNP_ALSENAN_BLIND_FULL_BOQ.md and run

    python research/christiannp_blind_process/scripts/verify_report_quotes.py

Each check needs its anchor tokens on one line or within a few neighbouring lines (case and whitespace
insensitive). Output: process_log/REPORT_QUOTE_CHECKS.json with FOUND / NOT_FOUND per claim and the report sha256.
A NOT_FOUND claim must be downgraded before the package is used; nothing is changed automatically.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
REPORT = PKG / "process_log" / "CHRISTIANNP_ALSENAN_BLIND_FULL_BOQ.md"
OUT = PKG / "process_log" / "REPORT_QUOTE_CHECKS.json"
WINDOW = 3

CLAIMS = {
    "A1": ["A1", "0.20"], "A2": ["A2", "0.00"], "A3": ["A3", "1.00"], "A4": ["A4", "13.90"], "A5": ["A5", "0.60"],
    "A6": ["A6", "0.10"], "A7": ["A7", "gross"], "A8": ["A8", "CN"], "A9": ["A9", "stair"], "A10": ["A10", "height"],
    "A11": ["A11", "ceiling"], "A12": ["A12", "FFL"], "A13": ["A13", "2.10"], "A14": ["A14", "net"],
    "A15": ["A15", "SFRS"],
    "R1": ["R1", "span"], "R2": ["R2", "collinear"], "R3": ["R3", "2 m"], "R4": ["R4", "60 mm"], "R5": ["R5", "equal"],
    "RASTER_CELL": ["50 mm", "raster"], "RASTER_FLOOD": ["flood"], "CLASS_SLAB_LABELLED": ["SLAB_LABELLED"],
    "CLASS_BEAM_INTERIOR": ["BEAM_INTERIOR"], "CLASS_OPENING": ["OPENING"],
    "CLASS_UNRESOLVED_ENCLOSED": ["UNRESOLVED_ENCLOSED"], "CLASS_EDGE_LINE_CELLS": ["EDGE_LINE_CELLS"],
    "GBP_RAW_LINES": ["85"], "GBP_STRIPS": ["42"], "GBP_LENGTH": ["200.036"], "GB_VOLUME": ["36.006"],
    "GROUND_SLAB": ["324.038"], "NET_REBAR": ["22.916"], "BOXED": ["BOXED"], "TOP_HANGERS": ["hanger"],
    "NET_SLAB_GF": ["290.555"], "NET_SLAB_1F": ["179.325"], "NET_SLAB_2F": ["55.275"], "FOOTINGS": ["65.669"],
    "COL_GF": ["26.235"], "COL_2F": ["3.377"], "BLOCK_200": ["183.497"], "WALL_FACES": ["2364.7"],
}


def norm(s):
    return re.sub(r"\s+", " ", s).lower()


def check(lines, tokens):
    toks = [norm(t) for t in tokens]
    for i in range(len(lines)):
        block = norm(" ".join(lines[max(0, i - WINDOW): i + WINDOW + 1]))
        if all(t in block for t in toks):
            return "FOUND", i + 1
    return "NOT_FOUND", None


def main():
    if not REPORT.exists():
        print(f"report not present: {REPORT}")
        return None
    text = REPORT.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    res = {k: dict(zip(("status", "line"), check(lines, v)), tokens=v) for k, v in CLAIMS.items()}
    out = {"report": REPORT.name, "sha256": hashlib.sha256(REPORT.read_bytes()).hexdigest(), "checks": res,
           "not_found": sorted(k for k, v in res.items() if v["status"] != "FOUND")}
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"sha256": out["sha256"], "not_found": out["not_found"]}))
    return out


if __name__ == "__main__":
    sys.exit(0 if main() is not None else 1)
