"""T-478 inputs (URBAN_V3045_INPUTS_V1) for the development villa: the CONC.BLINDING package from the Checker-verified
T-445 pieces (merged ab6bd617) and its Checker findings. Reads ONLY merged files (pinned by sha256) plus the own
plot-line clip per scenario (t478_f10_clip.py on the decoded structural DXF; values only). No drawing content, no
position, no name.

    build(project_id) -> the inputs document
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T445 = ROOT / "research/agents_t445"
LEDGER = T445 / "LEDGER_T445.csv"
INPUT = T445 / "ALSENAN_BLINDING_INPUT.json"
PINS = {LEDGER: "dd0a8b218fffc5b23490f5b270c694e87643a54cbb47f93e4cf6e5d36cd1e9cf",
        INPUT: "ed87d1043a51cd62ab5585a498d53273e82a30db0c23611deb02fb08a6e40844"}

L_FOOT, L_F10F, L_GB, L_STRAP = ("L-98eb2d58075c9eddf1b4", "L-080c97f5f6a92452cd04", "L-7a5214a334ea3559fa2d",
                                 "L-35382b18e2e362df3ae6")
# own plot-line clip per scenario (t478_f10_clip.py, 2026-11-02; DXF sha 9f9d1179): (clipped low, clipped high,
# unclipped) m3 at t = p = 0.10
F10_SCEN = {"F10_alone": (0.435, 0.45, 0.48), "F10_plus_F_rows": (0.525, 0.56, 0.59),
            "drawn_outline": (0.5025, 0.5025, 0.552)}
PLATE_M3 = 47.055               # T-433 I-01 / BL-1: the reference figure = plot line 31.37 x 15.00 x 0.10 (T-445 s.4)


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _check():
    for p, s in PINS.items():
        if _sha(p) != s:
            raise SystemExit(f"{p.name}: sha256 {_sha(p)[:12]} is not the merged {s[:12]} (stale input)")


def ledger():
    _check()
    with open(LEDGER, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def pits():
    """the 24 VERIFIED pit pieces (ids and m3 only) re-added from the merged ledger."""
    rows = [r for r in ledger() if r.get("status", "").startswith("VERIFIED")]
    return rows


SOURCES = [
    {"task": "T-445", "file": "research/agents_t445/LEDGER_T445.csv", "sha256": PINS[LEDGER],
     "merge_commit": "ab6bd617", "checker_run": "Verifier 2026-11-02 15:33 UTC (session_01E6cPneGHsVCayrDWd54dJn): "
                                                "Gate A PASS, own re-measure of all 24 pits AGREE"},
    {"task": "T-322", "file": "research/agents_t322/LEDGER_T322.csv", "sha256": "see merge d3bcd9d4",
     "merge_commit": "d3bcd9d4", "checker_run": "Checker T-322 verdict 2026-10-29 01:55 (24 pits 12.734438 VERIFIED; "
                                                "FF HELD >= 2.070)"},
    {"task": "T-233", "file": "research/agents_t233/LEDGER_T233.csv", "sha256": "see merge 2ecb5bf0",
     "merge_commit": "2ecb5bf0", "checker_run": "Verifier T-233 MERGED 2ecb5bf0 (outlines, 15.179437 union)"},
]


def build(project_id):
    d = json.loads(INPUT.read_text(encoding="utf-8"))
    _check()
    t = d["thickness_m"]
    sc = [{"name": k, "clipped_m3": v[0], "clipped_high_m3": v[1], "unclipped_m3": v[2]} for k, v in F10_SCEN.items()]
    return {
        "schema": "URBAN_V3045_INPUTS_V1", "project_id": project_id, "sources": SOURCES,
        "split": [{
            "line_id": L_FOOT, "expect": {"value": d["candidate"]["FOOTINGS"]["low"]},
            "verified": {"value": 12.734438, "area_m2": 127.344375, "t": t, "verdict": "Checker T-322 2026-10-29 "
                         "01:55 + T-445 Gate A own re-measure 2026-11-02 15:33",
                         "pieces": "24 pit footings inside the plot line by DXF outline handle (LEDGER_T445.csv)",
                         "basis": "129.430 grown - 0.195625 overlap once (to the deeper pit) - 1.890 beyond the plot "
                                  "line", "physical_element": "blinding under the 24 isolated pit footings, inside "
                                                              "the plot line", "source_tasks": ["T-445", "T-322"]},
            "held": [
                {"key": "FF_RAFT", "element_id": "P-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_LIFT_RAFT_FF",
                 "physical_element": "blinding under the FF lift raft", "low": 2.256, "high": 2.352,
                 "at_least": 2.07, "former": 2.256, "status": "AT_LEAST",
                 "blocker": "RFI S08 / S23: the FF governing detail prints the blinding without a projection "
                            "(readings 0.10 inherited from the typical isolated footing, 0.15 scaled); S08 ESTIMATED "
                            "2.352 is a label, never VERIFIED",
                 "basis": "raft 4.60 x 4.50: (L + 2p)(W + 2p) x 0.10 at p 0.10 / 0.15; at least the raft plan "
                          "x 0.10 with no projection", "source_tasks": ["T-445", "T-322"]},
                {"key": "BEYOND_PLOT", "element_id": "P-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_BEYOND_PLOT_LINE",
                 "physical_element": "blinding projection of 8 pit footings beyond the plot line",
                 "low": 0.0, "high": 0.189, "former": 0.189, "status": "HELD",
                 "blocker": "RFI S06 / D-14: whether the printed projection is built past the plot line",
                 "basis": "1.890 m2 of the grown pit plans lie beyond the plot line x 0.10",
                 "source_tasks": ["T-445"]}]}],
        "ranges": [{
            "line_id": L_F10F, "expect": {"low": d["candidate"]["F10F"]["low"], "high": d["candidate"]["F10F"]["high"]},
            "low": min(v[0] for v in F10_SCEN.values()), "high": max(v[2] for v in F10_SCEN.values()),
            "scenarios": sc, "source_tasks": ["T-445", "T-233"],
            "basis": "two-tag outline (F10 alone / F10 + F rows / drawn outline): low = the smallest scenario with the "
                     "plot-line clip, high = the largest without it",
            "why": "F-T445-2 (the owner's F10-alone scenario was outside the line) + F-C-T445-1 / F-C-S06-1 (the "
                   "outline sits on the plot corner: up to 0.0495 m3 of its grown plan lies beyond the plot line)"}],
        "netting": [{
            "line_id": L_GB, "expect": d["candidate"]["GB"], "source_tasks": ["T-445"],
            "overlap": {"method": "ROUTE_G_SCOPE_V1 blinding_scope footprint REACH",
                        "low_end": "merged: union(pit grown plans + strips) - union(pit grown plans): every m2 of a "
                                   "strip over a pit's blinding is netted (counted once, in the pit layer)",
                        "high_end": "own layer at beam level: union(strips) - column footprints; a separate layer "
                                    "above the pit layer, no plan overlap inside it",
                        "overlap_m2": None},
            "basis": "F-C-T445-2: netting by plan overlap, not by id",
            "why": "the held range already nets the strips against the pit layer geometrically at its low end; the "
                   "high end is the other detail reading (own layer), not a double count; no value until S09 / S11"}],
        "add": [{
            "key": "BW_BASE", "element_id": "P-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_BOUNDARY_WALL_BASE",
            "physical_element": "blinding under the boundary-wall pads", "floor": "FOUNDATION",
            "per_unit_at_least": 0.117, "per_unit": "per pad (1.30 x 0.90 x 0.10)", "source_tasks": ["T-445"],
            "held_items": "pad count and spacing not printed (M2, RFI S04); the band between pads is not drawn on "
                          "blinding",
            "basis": "typical boundary-wall section A-A prints the blinding 0.10 thick, 0.80 + 0.10 past the toe, "
                     "under the pads (130 x 80 x 30)"}],
        "plate": {
            "m3": PLATE_M3, "source_tasks": ["T-445"],
            "basis": "the comparison blinding item = the plot rectangle x 0.10 (T-445 s.4, own numeric identity; his "
                     "cell not opened)",
            "beside": "beyond the plot line (0 .. 0.189 pits, up to 0.0495 F10 / F) is not in his rectangle",
            "terms": [
                {"term": "24 pits VERIFIED", "line_id": L_FOOT, "cause": "valued after the SPLIT"},
                {"term": "FF raft", "key": "FF_RAFT", "cause": "RFI S08"},
                {"term": "F10 + F (inside the plot)", "line_id": L_F10F,
                 "inside_low": min(v[0] for v in F10_SCEN.values()),
                 "inside_high": max(v[1] for v in F10_SCEN.values()), "cause": "RFI S02 (scenarios), S06 clip"},
                {"term": "ground beams", "line_id": L_GB, "cause": "RFI S09 + S11"},
                {"term": "straps", "line_id": L_STRAP, "cause": "RFI S07 / D-15"}]},
    }

