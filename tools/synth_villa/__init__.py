"""Synthetic villa generator (T-019): parametric DXF villas with a hand truth, for non-Alsenan fixtures.

    villas.py   the villa specs (local metres) and the HAND truth written from their coordinates
    build.py    write_villa(...) -> DXF + truth; truth_of(...) -> truth only (spec formulas, never the engine)
    compare.py  run the architectural engine on a villa and report answered items and silent omissions

    python3 -m tools.synth_villa OUT_DIR [--engine]   writes the first-run villas (+ the engine report)
"""
