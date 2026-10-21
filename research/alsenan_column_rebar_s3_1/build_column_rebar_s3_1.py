"""ALSENAN S3.1 - column reinforcement re-run with the generic S3.1 corrections.

Same frozen inputs and the same adapter as S3 (research/alsenan_column_rebar_s3), with four corrections:

  A. ONE project-wide unit-mass method: the project selects D2_OVER_162 - the method every other Urban reinforcement
     module already uses (engine/source/rebar_model.py). S3 used exact density for columns only; that was a second,
     hidden formula and is retired here.
  B. '/m' notation: the tie rule text is parsed; a per-metre count is RATE_PER_M -> RATE_COUNT by URBAN_OWNER_RULE
     (Mohammad, S3.1 §22B). SPACING_WITH_ENDS stays a reported sensitivity, not a method flag.
  C. COLUMN_SECTION_TRANSITION: where the section changes between storeys (or the column turns) and no transition
     detail exists, a BLOCKED_TRANSITION_DETAIL part is raised - bars are not assumed straight.
  D. Headline: VERIFIED / LOWER_BOUND / PROVISIONAL / BLOCKED_MODELLED / UNQUANTIFIED_BLOCKED separately; no single
     'final' column total.

The frozen S3 outputs are not touched. Benchmark firewall: no comparison figure is read here.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S3 = ROOT / "research" / "alsenan_column_rebar_s3"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(S3))

from engine.source import column_rebar as CR  # noqa: E402
from engine.source import rebar_model as RM  # noqa: E402
from engine.source import rebar_unit_mass as UM  # noqa: E402
import build_column_rebar_s3 as S3A  # noqa: E402

PROJECT_UNIT_MASS = {"method": RM.UNIT_MASS["method"], "selected_by": "project (Urban default, same as rebar_model)",
                     "authority": "URBAN_OWNER_RULE"}
LEVEL_POLICY = {CR.RATE_PER_M: CR.RATE_COUNT, CR.SPACING: CR.SPACING_WITH_ENDS,
                "authority": "URBAN_OWNER_RULE (S3.1 §22B: an explicit '/m' count is a rate per metre)"}

_orig_inputs = S3A.project_inputs
_orig_segments = S3A.build_segments


def project_inputs(regs, r4, claims):
    P = _orig_inputs(regs, r4, claims)
    P.pop("steel_density_kg_m3", None)
    P["unit_mass"] = dict(PROJECT_UNIT_MASS)
    P["check_section_transitions"] = True
    note = CR.parse_transverse_notation(P["tie_rule"]["raw"])
    if not note:
        raise SystemExit("tie rule notation not parsed")
    P["tie_rule"]["notation"] = note["notation"]
    P["tie_rule"]["notation_parse"] = note
    P["level_method_policy"] = dict(LEVEL_POLICY)
    return P


def build_segments(regs, flags):
    segs, joins = _orig_segments(regs, flags)
    by = {(s["chain_id"], s["storey_index"]): s for s in segs}
    chains = {c["chain_id"]: c for c in S3A.rows(regs, "COLUMN_VERTICAL_CHAIN_REGISTER")}
    closing = {"FOUNDATION": "GBP", "GF": "GFRS", "1F": "FFRS", "2F": "SFRS"}
    for s in segs:
        ab = s.get("above") or {}
        if not ab.get("exists"):
            continue
        up = by.get((s["chain_id"], s["storey_index"] + 1))
        res = next(c for c in up["candidates"] if c["type"] == up["resolved_type"]) \
            if any(c["type"] == up["resolved_type"] for c in up["candidates"]) else up["candidates"][0]
        ab["section_mm"] = [res["definition"]["B_mm"], res["definition"]["D_mm"]]
        if len(up["candidates"]) > 1:
            ab["section_by_candidate"] = {c["type"]: [c["definition"]["B_mm"], c["definition"]["D_mm"]]
                                          for c in up["candidates"]}
        turn = chains[s["chain_id"]].get("turn") or {}
        ab["orientation_change"] = bool(turn) and turn.get("sheet") == closing[s["floor"]]
        ab["transition_detail"] = None                      # ST7757 prints no section-transition detail
    return segs, joins


def build():
    S3A.project_inputs = project_inputs
    S3A.build_segments = build_segments
    try:
        R, files, s = S3A.build()
    finally:
        S3A.project_inputs = _orig_inputs
        S3A.build_segments = _orig_segments
    parts = R["res"]["parts"]
    mc = CR.mass_conservation(R["res"], lambda x: x["floor"])
    trans = [p for p in parts if p.get("transition")]
    headline = {
        "VERIFIED_KG": S3A.r3(mc["project"].get("verified", 0.0)),
        "LOWER_BOUND_KG": S3A.r3(mc["project"].get("lower_bound", 0.0)),
        "PROVISIONAL_KG": S3A.r3(mc["project"].get("provisional", 0.0)),
        "BLOCKED_MODELLED_KG": S3A.r3(mc["project"].get("blocked", 0.0)),
        "UNQUANTIFIED_BLOCKED_PARTS": sum(1 for p in parts if p["kg"] is None),
        "MODELLED_SUM_NOT_FINAL_KG": S3A.r3(mc["project"].get("total", 0.0)),
        "rule": "no single 'final column rebar' figure: the modelled sum includes provisional and blocked parts",
        "unit_mass": UM.describe(PROJECT_UNIT_MASS)}
    s31 = {"round": "S3.1", "headline": headline, "unit_mass_method": PROJECT_UNIT_MASS,
           "level_method_policy": LEVEL_POLICY, "tie_notation": R["P"]["tie_rule"]["notation_parse"],
           "section_transitions": {"segments": len({p["segment_id"] for p in trans}),
                                   "orientation_changes": sum(1 for p in trans
                                                              if p["transition"].get("orientation_change")),
                                   "kinds": dict(Counter(p["transition"]["kind"] for p in trans)),
                                   "state": "BLOCKED_TRANSITION_DETAIL (no ST7757 transition detail)"},
           "end_level_flag": R["q"]["END_LEVEL_COUNT_METHOD_REQUIRED"].get("resolved_by_policy"),
           "summary": s}
    files["COLUMN_REBAR_S3_1_SUMMARY.json"] = s31
    files.pop("COLUMN_REBAR_SUMMARY.json", None)
    return R, files, s31


def delta_vs_s3(files):
    """Effect of the corrections against the frozen S3 register (informational)."""
    s3 = json.loads((S3 / "COLUMN_MASS_CONSERVATION.json").read_text(encoding="utf-8"))["project"]
    s31 = files["COLUMN_MASS_CONSERVATION.json"]["project"]
    return {k: {"s3": s3.get(k), "s3_1": s31.get(k),
                "delta": None if s3.get(k) is None or s31.get(k) is None else round(s31[k] - s3[k], 3)}
            for k in ("verified", "lower_bound", "provisional", "blocked", "total", "unquantified_blocked_parts")}


def main(write=True):
    R, files, s31 = build()
    files["S3_TO_S3_1_DELTA.json"] = {"note": "informational: unit-mass method D2/162 (was exact density), section "
                                              "transitions blocked, rate notation by owner rule",
                                      "project_kg": delta_vs_s3(files)}
    blobs = {k: S3A.dumps(v).encode() for k, v in files.items()}
    if write:
        for k, b in blobs.items():
            (HERE / k).write_bytes(b)
        idx = {"round": "S3.1", "project_id": S3A.PROJECT_ID, "drawing_revision": S3A.REVISION,
               "outputs": {k: hashlib.sha256(b).hexdigest() for k, b in sorted(blobs.items())},
               "s1_registers_consumed": {k: R["idx"]["registers"][k]["sha256"] for k in S3A.S1_USED},
               "s2_outputs_consumed": {"ALSENAN_ENGINEERING_FLAGS.json":
                                       R["s2_idx"]["outputs"]["ALSENAN_ENGINEERING_FLAGS.json"]},
               "s3_outputs_modified": False, "benchmark_read": False, "frozen_before_comparison": True,
               "occurrences": s31["summary"]["occurrences_in"],
               "terminal_records": s31["summary"]["terminal_records_out"]}
        (HERE / "INDEX.json").write_text(S3A.dumps(idx), encoding="utf-8")
    return R, files, s31, blobs


if __name__ == "__main__":
    _, _, s31, b1 = main()
    if "--twice" in sys.argv:
        _, _, _, b2 = main(write=False)
        print("built twice identical:", all(b1[k] == b2[k] for k in b1))
    print(json.dumps({k: s31[k] for k in ("headline", "section_transitions", "end_level_flag")}, indent=1))
