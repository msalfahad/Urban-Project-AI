"""S6 generic engine (engine/source/superstructure_beam_rebar.py) on synthetic simple and continuous beams.

Every expected value is computed here from first principles (count x straight run x D^2/162, ceil(rate x run)) -
never from a project total or a reference. Covers the S6 brief section 31 list.
"""

from __future__ import annotations

import copy
import math
import re
from pathlib import Path

import pytest

from engine.source import accurate_boq_rebar as AR
from engine.source import beam_rebar_readiness as BR
from engine.source import superstructure_beam_rebar as SB

ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 64
CTX = {"PROJECT_ID": "SYNTH", "DRAWING_ID": "S-01", "DRAWING_SHA": SHA, "REVISION": "R0", "ENGINE_COMMIT": "test",
       "REGISTER_VERSION": "TEST_V1", "CALCULATION_ROUND": "TEST", "unit_mass": {"method": "D2_OVER_162"}}
NE = SB.NOT_ESTABLISHED


def kgm(d):
    return d * d / 162.0


def rules(**over):
    r = {"typical": {
        "T:EXT75": {"state": "BOUND", "kind": "FIXED_EXTENSION_M", "value": 0.075, "applies_to": ["BOTTOM_MAIN"],
                    "text": "7.5cm"},
        "T:MID22": {"state": "BOUND", "kind": "FACTOR_OF_SPAN", "value": 0.22, "span_basis": "AXIS_TO_AXIS",
                    "applies_to": ["MID_TOP"], "text": "0.22 Ln"},
        "T:015L": {"state": "UNRESOLVED", "kind": None, "value": None, "applies_to": [], "text": "0.15L",
                   "why": "dimension not bound to a bar"},
        "T:03LN2": {"state": "UNRESOLVED", "kind": "FACTOR_OF_SPAN", "value": 0.3, "applies_to": [],
                    "text": "0.3 Ln2", "why": "Ln2 names no span"}},
        "span_symbols": {"Ln": "AXIS_TO_AXIS", "L": "FACE_TO_FACE", "authority": "SOURCE_DERIVED_HIGH_CONFIDENCE"},
        "development": {"state": NE, "why": "no beam development rule"},
        "bar_end_hooks": {"state": NE, "why": "no hook source"},
        "stirrup_hooks": {"state": NE, "why": "not printed"},
        "stirrup_topology": {"state": NE, "why": "legs not printed"},
        "side_bar_semantics": {"state": NE, "why": "'/30cm' semantics not established"},
        "hanger": {"state": NE, "why": "unlabelled second top row"}, "openings_checked": 0}
    r.update(over)
    return r


def tok(fam, norm, tid=None, terminal="PARSED_BOUND", grammar="COUNT_DIA"):
    return {"token_id": tid or f"TK:{fam}:{norm}", "field_family": fam, "grammar": grammar, "terminal": terminal,
            "normalised": norm, "raw": norm}


def _identity(oid, **over):
    idn = {"SOURCE_HANDLES": [f"TAG-{oid}"], "GEOMETRY_HANDLES": [f"BAND-{oid}"], "TAG_HANDLES": [f"TAG-{oid}"],
           "SCHEDULE_HANDLES": ["ROW1"], "START_SUPPORT": {"kind": "COLUMN", "refs": ["C1"]},
           "END_SUPPORT": {"kind": "COLUMN", "refs": ["C2"]}, "DRAWN_WIDTH_MM": 200, "SCHEDULE_WIDTH_MM": 200,
           "WIDTH_MATCH_STATE": "MATCH", "DETAIL_ID": "SBT:ROW1", "DETAIL_CANDIDATES": ["SBT:ROW1"],
           "SCHEDULE_ROW": "ROW1", "BINDING_STATE": "BOUND_VERIFIED", "AUTHORITY_STATE": "SOURCE_DERIVED_HIGH_CONFIDENCE",
           "GEOMETRY_OBJECTS": [f"SPAN:{oid}"]}
    idn.update(over)
    return idn


def _run(oid, comp, n, d, segments, *, rid=None, fam=None, **over):
    run = {"BAR_RUN_ID": rid or f"{oid}:{comp}", "component": comp, "count": n, "dia_mm": d, "segments": segments,
           "register_run_m": sum(s["length_m"] for s in segments) if segments else None,
           "source_tokens": [tok(fam or comp, f"{n}Ø{d}", tid=f"TK:{oid}:{comp}:{rid}")] if n else [],
           "authority": "SOURCE_DERIVED_HIGH_CONFIDENCE", "missing": [], "source_block": None,
           "spans_crossed": [1], "intermediate_supports": [], "source_extent": {}}
    run.update(over)
    return run


def simple(oid="S1", *, top=(2, 12), bottom=(2, 14), run_m=3.0, blocks=(), rate=6, side=None, hanger="ABSENT",
           extra=None, openings=(), idn=None):
    seg = [{"length_m": run_m, "state": "VERIFIED"}]
    status = {c: {"state": "NOT_APPLICABLE", "why": "not scheduled"} for c in
              ("TOP_SUPPORT", "BOTTOM_SUPPORT", "MID_TOP", "MID_BOTTOM")}
    status["OTHER_EXPLICIT_EXTRA"] = extra or {"state": "NOT_APPLICABLE", "why": "none"}
    return {"occurrence_id": oid, "subfamily": SB.SIMPLE_BEAM, "mark": "B1", "drawing_sha": SHA, "sheet": "SH1",
            "floor": "F1", "identity": idn or _identity(oid), "geometry": {"clear_face_to_face_m": run_m},
            "cb": None, "blocks": list(blocks),
            "bar_runs": [_run(oid, "TOP_MAIN", *top, seg), _run(oid, "BOTTOM_MAIN", *bottom, seg)],
            "stirrups": [{"SPAN_INDEX": 1, "dia_mm": 8, "mode": "BARS_PER_METRE", "value": rate,
                          "distribution_m": run_m, "register_count": None,
                          "source_tokens": [tok("STIRRUP", f"{rate}Ø8", tid=f"TK:{oid}:STR")],
                          "core_path_missing": ["LEGS / TOPOLOGY UNRESOLVED"]}],
            "status": status, "side": side, "hanger": {"state": hanger, "why": "no hanger field"},
            "openings": list(openings), "questions": {}, "flags": []}


SPANS = {"1": {"cc_m": 5.0, "clear_m": 4.6}, "2": {"cc_m": 4.0, "clear_m": 3.6}}


def cb_runs(oid, bot1=(3, 16), bot2=(3, 16), mid=(4, 18), sup=0.4):
    b1 = [{"kind": "CLEAR_SPAN", "length_m": 4.6, "span": 1, "state": "VERIFIED"},
          {"kind": "THROUGH_SUPPORT", "length_m": sup, "support": 1, "state": "VERIFIED"},
          {"kind": "BEYOND_FAR_FACE", "length_m": 0.075, "rule_id": "T:EXT75", "support": 1, "state": "VERIFIED"}]
    b2 = [{"kind": "CLEAR_SPAN", "length_m": 3.6, "span": 2, "state": "VERIFIED"},
          {"kind": "THROUGH_SUPPORT", "length_m": sup, "support": 1, "state": "VERIFIED"},
          {"kind": "BEYOND_FAR_FACE", "length_m": 0.075, "rule_id": "T:EXT75", "support": 1, "state": "VERIFIED"}]
    m = [{"kind": "INTO_SPAN_LEFT", "length_m": 0.22 * 5.0, "rule_id": "T:MID22", "span": 1, "state": "VERIFIED"},
         {"kind": "THROUGH_SUPPORT", "length_m": sup, "support": 1, "state": "VERIFIED"},
         {"kind": "INTO_SPAN_RIGHT", "length_m": 0.22 * 4.0, "rule_id": "T:MID22", "span": 2, "state": "VERIFIED"}]
    top = _run(oid, "TOP_MAIN", 2, 12, [], rid=f"{oid}:TOP:F1", fam="TOP",
               source_block="interior end drawn N.T.S.; no bound extent rule",
               source_extent={"frame_handle": "F1"})
    return [_run(oid, "BOTTOM_MAIN", *bot1, b1, rid=f"{oid}:BOTTOM:B1", fam="BOTTOM", spans_crossed=[1, 2],
                 intermediate_supports=[1], source_extent={"frame_handle": "B1"}),
            _run(oid, "BOTTOM_MAIN", *bot2, b2, rid=f"{oid}:BOTTOM:B2", fam="BOTTOM", spans_crossed=[1, 2],
                 intermediate_supports=[1], source_extent={"frame_handle": "B2"}),
            _run(oid, "MID_TOP", *mid, m, rid=f"{oid}:MID:M1", fam="MID", spans_crossed=[1, 2],
                 intermediate_supports=[1], source_extent={"frame_handle": "M1"}), top]


def cb(oid="C1", *, reading="FORWARD", runs=None, blocks=(), rates=(7, 7), spans=None, hanger="DETAILED_UNLABELLED",
       stir_interp=None):
    spans = spans or SPANS
    status = {"TOP_SUPPORT": {"state": "BLOCKED", "why": "typical end-support bar '0.3 Ln2' unresolved",
                              "question_id": "Q2"},
              "BOTTOM_SUPPORT": {"state": "NOT_APPLICABLE", "why": "not scheduled"},
              "MID_BOTTOM": {"state": "NOT_APPLICABLE", "why": "not scheduled"},
              "OTHER_EXPLICIT_EXTRA": {"state": "NOT_APPLICABLE", "why": "none"}}
    runs = runs if runs is not None else cb_runs(oid)
    for c in ("TOP_MAIN", "BOTTOM_MAIN", "MID_TOP"):
        if not any(r["component"] == c for r in runs):
            status[c] = {"state": "BLOCKED", "why": "no bar run established", "question_id": "R3"}
    stirrups = []
    for k, r in zip(sorted(spans), rates):
        s = {"SPAN_INDEX": int(k), "dia_mm": 8, "mode": "BARS_PER_METRE", "value": r,
             "distribution_m": spans[k]["clear_m"], "register_count": None,
             "source_tokens": [tok("STIRRUP", f"{r}Ø8", tid=f"TK:{oid}:STR{k}")], "core_path_missing": []}
        if stir_interp:
            s["interpretations"] = stir_interp(int(k))
        stirrups.append(s)
    return {"occurrence_id": oid, "subfamily": SB.CONTINUOUS_BEAM, "mark": "CB1", "drawing_sha": SHA,
            "sheet": "SH1", "floor": "F1", "identity": _identity(oid, DRAWN_WIDTH_MM=[200, 200],
                                                                 WIDTH_MATCH_STATE=["MATCH", "MATCH"],
                                                                 DETAIL_ID="C-BEAM:ROW1"),
            "geometry": {"spans": spans},
            "cb": {"CB_GROUP_ID": oid, "SPAN_SEQUENCE": [{"SPAN_INDEX": int(k)} for k in sorted(spans)],
                   "READING_DIRECTION_STATE": reading, "SEQUENCE_STATE": "MATCH", "spans": spans},
            "blocks": list(blocks), "bar_runs": runs, "stirrups": stirrups,
            "status": status, "side": None, "hanger": {"state": hanger, "why": "unlabelled second top row"},
            "openings": [], "questions": {"reading_direction": "R4"}, "flags": []}


def by(res, comp, oid=None):
    return [c for c in res["components"] if c["component"] == comp and (oid is None or c["occurrence_id"] == oid)]


def one(res, comp, oid=None):
    rows = by(res, comp, oid)
    assert len(rows) == 1, (comp, len(rows))
    return rows[0]


def interp(n1, d1, n2, d2, comp="BOTTOM_MAIN", rule=("CLEAR_SPAN:", "THROUGH_SUPPORT:", "BEYOND_FAR_FACE:T:EXT75")):
    return [{"name": "FORWARD", "component": comp, "count": n1, "dia_mm": d1, "run_rule": list(rule)},
            {"name": "REVERSED", "component": comp, "count": n2, "dia_mm": d2, "run_rule": list(rule)}]


# ----------------------------------------------------------------------------------------------- simple beams
def test_simple_top_bar():
    res = SB.run([simple()], rules(), CTX)
    t = one(res, "TOP_MAIN")
    assert t["state"] == AR.LOWER_BOUND and t["kg"] == pytest.approx(2 * 3.0 * kgm(12))
    assert (t["bar_count"], t["dia_mm"], t["straight_run_m"], t["total_length_m"]) == (2, 12, 3.0, 6.0)
    assert t["known_source_segment_state"] == SB.SEGMENT_SOURCE_VERIFIED
    assert t["complete_bar_state"] == "NOT_ESTABLISHED" and "DEVELOPMENT" in t["why"]
    assert res["conservation"]["all_pass"]


def test_simple_bottom_bar_never_merged_with_top_of_the_same_diameter():
    res = SB.run([simple(top=(2, 14), bottom=(3, 14))], rules(), CTX)
    t, b = one(res, "TOP_MAIN"), one(res, "BOTTOM_MAIN")
    assert b["kg"] == pytest.approx(3 * 3.0 * kgm(14)) and t["kg"] == pytest.approx(2 * 3.0 * kgm(14))
    assert t["record_id"] != b["record_id"] and len(res["bbs"]) == 2
    assert res["occurrences"][0]["occurrence_state"] == "LOWER_BOUND"


def test_blocked_simple_beam_keeps_geometry_and_attributes_but_no_kg():
    blk = [{"reason": "WITH STAIR: p.16 detail is an unread candidate", "authority": "UNRESOLVED",
            "question_id": "Q9", "kind": "UNDEFINED_CANDIDATE_DETAIL"}]
    res = SB.run([simple(blocks=blk)], rules(), CTX)
    occ = res["occurrences"][0]
    assert occ["occurrence_state"] == "BLOCKED" and occ["known_kg"] == 0 and "WITH STAIR" in \
        occ["occurrence_blocking_reason"]
    for c in ("TOP_MAIN", "BOTTOM_MAIN", "STIRRUP_COUNT"):
        r = one(res, c)
        assert r["state"] == AR.BLOCKED_UNQUANTIFIED and r["kg"] is None
    b = one(res, "BOTTOM_MAIN")
    assert (b["bar_count"], b["dia_mm"], b["register_run_m"]) == (2, 14, 3.0)     # blocked != zero, != forgotten
    assert occ["geometry"]["clear_face_to_face_m"] == 3.0 and not res["bbs"]


def test_candidate_beam_is_blocked_never_provisional_kg():
    blk = [{"reason": "binding is a candidate", "authority": "UNRESOLVED", "question_id": "R1",
            "kind": "BINDING_CANDIDATE"}]
    res = SB.run([simple(blocks=blk, idn=_identity("S1", BINDING_STATE="BOUND_CANDIDATE"))], rules(), CTX)
    s = res["summary"]
    assert s["SIMPLE_BEAM_PROVISIONAL_KG"] == 0 and s["SIMPLE_BEAM_LOWER_BOUND_KNOWN_KG"] == 0
    assert one(res, "TOP_MAIN")["provenance"]["AUTHORITY_STATE"] == "UNRESOLVED"
    assert res["occurrences"][0]["occurrence_state"] == "BLOCKED"


# ------------------------------------------------------------------------------------------- continuous beams
def test_cb_ordered_spans_release_bottom_and_mid_once_each():
    res = SB.run([cb()], rules(), CTX)
    bots = by(res, "BOTTOM_MAIN")
    assert sorted(round(b["kg"], 9) for b in bots) == sorted(round(x, 9) for x in (
        3 * (4.6 + 0.4 + 0.075) * kgm(16), 3 * (3.6 + 0.4 + 0.075) * kgm(16)))
    for b in bots:
        pv = b["provenance"]
        assert pv["CB_GROUP_ID"] == "C1" and pv["BAR_RUN_ID"] == b["bar_run_id"] and pv["SPAN_INDEX"] == [1, 2]
        assert pv["READING_DIRECTION_STATE"] == "FORWARD" and pv["RELEASE_BASIS"] == "SOURCE_BOUND"
    top = one(res, "TOP_MAIN")
    assert top["state"] == AR.BLOCKED_UNQUANTIFIED and "N.T.S." in top["why"] and top["bar_count"] == 2
    assert res["conservation"]["checks"]["one_bar_run_per_source_frame_bar"]


def test_cb_reversed_direction_uses_the_schedule_span_table():
    spans = {"1": {"cc_m": 4.0, "clear_m": 3.6}, "2": {"cc_m": 5.0, "clear_m": 4.6}}
    runs = cb_runs("C2")
    for r in runs:                       # schedule span 1 is the 3.6 m span under the resolved REVERSED reading
        for s in r["segments"]:
            if s.get("kind") == "CLEAR_SPAN":
                s["span"] = 2 if s["length_m"] == 4.6 else 1
            if s.get("kind") == "INTO_SPAN_LEFT":
                s.update(span=2)
            if s.get("kind") == "INTO_SPAN_RIGHT":
                s.update(span=1)
    res = SB.run([cb("C2", reading="REVERSED", runs=runs, spans=spans)], rules(), CTX)
    assert all(b["state"] == AR.LOWER_BOUND and b["release_basis"] == "SOURCE_BOUND" for b in by(res, "BOTTOM_MAIN"))
    assert one(res, "MID_TOP")["state"] == AR.LOWER_BOUND
    bad = cb_runs("C3")                  # the same runs read against the wrong span table: refused, not re-mapped
    with pytest.raises(SB.SuperstructureBeamRebarError):
        SB.run([cb("C3", reading="REVERSED", runs=bad, spans=spans)], rules(), CTX)


def test_cb_bidirectional_candidate_invariant_and_different():
    runs = cb_runs("C4", bot1=(3, 16), bot2=(3, 16))
    for r in runs:
        r["interpretations"] = interp(r["count"], r["dia_mm"], r["count"], r["dia_mm"], comp=r["component"])
    res = SB.run([cb("C4", reading="AMBIGUOUS", runs=runs)], rules(), CTX)
    assert all(b["state"] == AR.LOWER_BOUND and b["release_basis"] == "CANDIDATE_INVARIANT"
               for b in by(res, "BOTTOM_MAIN"))
    runs = cb_runs("C5", bot1=(4, 16), bot2=(4, 18))
    runs[0]["interpretations"] = interp(4, 16, 4, 18)
    runs[1]["interpretations"] = interp(4, 18, 4, 16)
    runs[2]["interpretations"] = interp(4, 18, 4, 18, comp="MID_TOP")
    res = SB.run([cb("C5", reading="AMBIGUOUS", runs=runs)], rules(), CTX)
    for b in by(res, "BOTTOM_MAIN"):
        assert b["state"] == AR.BLOCKED_UNQUANTIFIED and b["kg"] is None and "disagree" in b["why"]
        assert b["provenance"]["AUTHORITY_STATE"] == "SOURCE_CONFLICT"
    assert one(res, "MID_TOP")["release_basis"] == "CANDIDATE_INVARIANT"
    runs = cb_runs("C6")                 # ambiguous with no invariance evidence: nothing is chosen
    res = SB.run([cb("C6", reading="AMBIGUOUS", runs=runs)], rules(), CTX)
    assert all(c["state"] == AR.BLOCKED_UNQUANTIFIED for c in by(res, "BOTTOM_MAIN") + by(res, "MID_TOP"))


def test_candidate_invariant_needs_every_value_equal_no_averaging():
    st, val, _ = SB.candidate_invariant(interp(3, 16, 3, 16))
    assert st == "SAME" and val[1:3] == (3, 16)
    for alt in (interp(3, 16, 4, 16), interp(3, 16, 3, 18),
                interp(3, 16, 3, 16)[:1] + [dict(interp(3, 16, 3, 16)[1], run_rule=["CLEAR_SPAN:"])],
                interp(3, 16, 3, 16)[:1] + [dict(interp(3, 16, 3, 16)[1], component="TOP_MAIN")]):
        assert SB.candidate_invariant(alt)[0] == "DIFFERENT"
    assert SB.candidate_invariant([])[0] == "NONE"


def test_continuous_bar_run_across_a_support_is_one_physical_bar():
    res = SB.run([cb()], rules(), CTX)
    b1 = next(b for b in by(res, "BOTTOM_MAIN") if b["bar_run_id"].endswith("B1"))
    kinds = [s.get("kind") for s in b1["provenance"]["INPUTS"]["segments"]]
    assert kinds == ["CLEAR_SPAN", "THROUGH_SUPPORT", "BEYOND_FAR_FACE"] and b1["spans_crossed"] == [1, 2]
    assert len({c["bar_run_id"] for c in res["components"] if c["bar_run_id"]}) == 4
    dup = cb("C7")
    dup["bar_runs"].append(copy.deepcopy(dup["bar_runs"][0]))
    with pytest.raises(SB.SuperstructureBeamRebarError, match="entered twice"):
        SB.run([dup], rules(), CTX)
    split = cb("C8")                     # the same frame bar split into two runs at the support
    piece = copy.deepcopy(split["bar_runs"][0])
    piece["BAR_RUN_ID"] += ":B"
    split["bar_runs"].append(piece)
    assert not SB.run([split], rules(), CTX)["conservation"]["checks"]["one_bar_run_per_source_frame_bar"]


def test_mid_022_ln_from_the_face_straight_segment_only():
    res = SB.run([cb()], rules(), CTX)
    m = one(res, "MID_TOP")
    L = 0.22 * 5.0 + 0.4 + 0.22 * 4.0
    assert m["state"] == AR.LOWER_BOUND and m["kg"] == pytest.approx(4 * L * kgm(18))
    assert m["mid"]["factor"] == [0.22] and m["mid"]["span_basis"] == ["AXIS_TO_AXIS"]
    assert m["mid"]["spans"]["1"]["Ln_m"] == 5.0 and m["mid"]["support_width_m"] == pytest.approx(0.4)
    assert m["mid_straight_run_state"] == SB.SEGMENT_SOURCE_VERIFIED and m["complete_bar_state"] == "NOT_ESTABLISHED"
    pv = m["provenance"]
    assert pv["MID_STRAIGHT_RUN_STATE"] == "SOURCE_VERIFIED" and pv["COMPLETE_BAR_STATE"] == "NOT_ESTABLISHED"
    assert res["summary"]["MID_KNOWN_KG"] == pytest.approx(m["kg"]) and res["summary"]["CONTINUOUS_BEAM_VERIFIED_KG"] == 0


def test_project_specific_ln_definition_is_the_drawings_own():
    face = cb_runs("C9")                 # a register that used the clear span (common notation) for Ln
    face[2]["segments"][0]["length_m"] = 0.22 * 4.6
    face[2]["segments"][2]["length_m"] = 0.22 * 3.6
    face[2]["register_run_m"] = sum(s["length_m"] for s in face[2]["segments"])
    with pytest.raises(SB.SuperstructureBeamRebarError, match="AXIS_TO_AXIS"):
        SB.run([cb("C9", runs=face)], rules(), CTX)
    r = rules()
    r["typical"]["T:MID22"] = dict(r["typical"]["T:MID22"], span_basis="FACE_TO_FACE")   # a drawing that says so
    res = SB.run([cb("C9", runs=face)], r, CTX)
    assert one(res, "MID_TOP")["mid"]["span_basis"] == ["FACE_TO_FACE"]


def test_edited_mid_conflict_and_empty_mid_cell_stay_blocked():
    runs = cb_runs("C10")
    runs[2]["source_block"] = "frame bar drawn asymmetric about its support: the typical extent is not shown to apply"
    res = SB.run([cb("C10", runs=runs)], rules(), CTX)
    m = one(res, "MID_TOP")
    assert m["state"] == AR.BLOCKED_UNQUANTIFIED and m["kg"] is None and m["bar_count"] == 4
    runs = cb_runs("C11")
    runs[2].update(count=None, dia_mm=None, source_tokens=[tok("MID", "", tid="EMPTY", terminal="BLOCKED_SEMANTICS",
                                                                grammar="EMPTY")])
    res = SB.run([cb("C11", runs=runs)], rules(), CTX)
    m = one(res, "MID_TOP")
    assert m["state"] == AR.BLOCKED_UNQUANTIFIED and "count / diameter" in m["why"]
    rec = copy.deepcopy(one(SB.run([cb("C12")], rules(), CTX), "MID_TOP"))
    rec["source_tokens"] = [tok("MID", "", tid="EMPTY", terminal="BLOCKED_SEMANTICS", grammar="EMPTY")]
    with pytest.raises(SB.SuperstructureBeamRebarError):
        SB.validate_record(rec)          # an empty cell can never stand behind released steel


def test_75cm_extension_only_on_the_bar_role_it_is_bound_to():
    res = SB.run([cb()], rules(), CTX)
    b1 = next(b for b in by(res, "BOTTOM_MAIN") if b["bar_run_id"].endswith("B1"))
    assert b1["straight_run_m"] == pytest.approx(4.6 + 0.4 + 0.075) and "T:EXT75" in b1["rules_used"]
    occ = simple("S2")                   # the same rule on a top bar: never generalised
    occ["bar_runs"][0]["segments"] = [{"length_m": 3.0, "state": "VERIFIED"},
                                      {"kind": "BEYOND_FAR_FACE", "length_m": 0.075, "rule_id": "T:EXT75",
                                       "state": "VERIFIED"}]
    occ["bar_runs"][0]["register_run_m"] = 3.0
    t = one(SB.run([occ], rules(), CTX), "TOP_MAIN")
    assert t["straight_run_m"] == 3.0 and any("never generalised" in m for m in t["missing"])
    runs = cb_runs("C13")
    runs[0]["segments"][2]["length_m"] = 0.08
    runs[0]["register_run_m"] = None
    with pytest.raises(SB.SuperstructureBeamRebarError, match="T:EXT75"):
        SB.run([cb("C13", runs=runs)], rules(), CTX)


def test_unresolved_015L_extension_adds_no_length():
    runs = cb_runs("C14")
    runs[1]["segments"].append({"kind": "BEYOND_FAR_FACE", "length_m": 0.15 * 3.6, "rule_id": "T:015L",
                                "support": 2, "state": "VERIFIED"})
    runs[1]["register_run_m"] = 3.6 + 0.4 + 0.075
    res = SB.run([cb("C14", runs=runs)], rules(), CTX)
    b2 = next(b for b in by(res, "BOTTOM_MAIN") if b["bar_run_id"].endswith("B2"))
    assert b2["state"] == AR.LOWER_BOUND and b2["straight_run_m"] == pytest.approx(3.6 + 0.4 + 0.075)
    assert b2["known_source_segment_state"] == SB.SEGMENT_LOWER_BOUND
    assert any("0.15L" in m and "adds no length" in m for m in b2["missing"])


def test_unresolved_03Ln2_support_bar_is_blocked():
    runs = cb_runs("C15")
    runs.append(_run("C15", "TOP_SUPPORT", 2, 12, [
        {"kind": "INTO_SPAN_RIGHT", "length_m": 0.3 * 4.0, "rule_id": "T:03LN2", "span": 1, "state": "VERIFIED"},
        {"kind": "THROUGH_SUPPORT", "length_m": 0.4, "support": 0, "state": "VERIFIED"}], rid="C15:TS", fam="TOP"))
    occ = cb("C15", runs=runs)
    del occ["status"]["TOP_SUPPORT"]
    res = SB.run([occ], rules(), CTX)
    ts = one(res, "TOP_SUPPORT")
    assert ts["state"] == AR.BLOCKED_UNQUANTIFIED and ts["kg"] is None and "0.3 Ln2" in ts["why"]


def test_hanger_blocked_never_inferred():
    res = SB.run([cb()], rules(), CTX)
    h = one(res, "HANGER")
    assert h["state"] == AR.BLOCKED_UNQUANTIFIED and "not inferred" in h["why"]
    runs = cb_runs("C16") + [_run("C16", "HANGER", 2, 12, [{"kind": "CLEAR_SPAN", "length_m": 4.6, "span": 1,
                                                           "state": "VERIFIED"}], rid="C16:H", fam="TOP")]
    assert one(SB.run([cb("C16", runs=runs)], rules(), CTX), "HANGER")["kg"] is None
    with pytest.raises(SB.SuperstructureBeamRebarError, match="hanger"):
        SB.run([cb()], rules(hanger={"state": "SOURCE_ESTABLISHED", "why": "x"}), CTX)
    assert one(SB.run([simple()], rules(), CTX), "HANGER")["state"] == SB.NOT_APPLICABLE   # absent in the SBT


def test_tm_design_load_can_never_produce_steel():
    tm = tok("T/M", "3.0 t/m", tid="C-BEAM:X:T/M-1", terminal="NOT_REBAR", grammar="DESIGN_LOAD_T_PER_M")
    assert not SB.is_rebar_token(tm) and SB.token_terminal(tm, []) == "EXCLUDED_DESIGN_LOAD"
    misfiled = tok("BOTTOM", "3.0 t/m", tid="MISFILED")          # a load mis-filed under a rebar field
    assert not SB.is_rebar_token(misfiled)
    for bad in (tm, misfiled):
        occ = simple("S3")
        occ["bar_runs"][1]["source_tokens"] = [bad]
        with pytest.raises(SB.SuperstructureBeamRebarError, match="never produce steel"):
            SB.run([occ], rules(), CTX)
        occ = simple("S4")
        occ["stirrups"][0]["source_tokens"] = [bad]
        with pytest.raises(SB.SuperstructureBeamRebarError, match="never produce steel"):
            SB.run([occ], rules(), CTX)
    res = SB.run([simple("S5")], rules(), CTX)
    assert all(t["field_family"] != "T/M" for c in res["components"] for t in c.get("source_tokens") or [])
    assert SB.token_terminal(tok("SECTION", "40", terminal="NOT_REBAR", grammar="SECTION_DIMENSION_CM"),
                             []) == "EXCLUDED_NOT_REBAR"


def test_width_conflict_blocks_schedule_dependent_rebar_and_keeps_geometry():
    idn = _identity("S6", DRAWN_WIDTH_MM=200, SCHEDULE_WIDTH_MM=250, WIDTH_MATCH_STATE="SOURCE_CONFLICT",
                    BINDING_STATE="BOUND_SOURCE_CONFLICT")
    blk = [{"reason": "drawn width conflicts with the schedule width", "authority": "SOURCE_CONFLICT",
            "question_id": "R2", "kind": "WIDTH_SOURCE_CONFLICT"}]
    res = SB.run([simple("S6", blocks=blk, idn=idn)], rules(), CTX)
    for c in ("TOP_MAIN", "BOTTOM_MAIN", "STIRRUP_COUNT"):
        r = one(res, c)
        assert r["state"] == AR.BLOCKED_UNQUANTIFIED and r["provenance"]["AUTHORITY_STATE"] == "SOURCE_CONFLICT"
        assert r["provenance"]["DRAWN_WIDTH_MM"] == 200 and r["provenance"]["SCHEDULE_WIDTH_MM"] == 250
        assert r["mark"] == "B1"                                    # never re-marked
    assert any("WIDTH SOURCE_CONFLICT" in f for f in one(res, "STIRRUP_CORE_PATH")["missing_facets"])
    assert res["occurrences"][0]["geometry"]["clear_face_to_face_m"] == 3.0        # never resized


# --------------------------------------------------------------------------------------------------- stirrups
def test_stirrup_count_known_lower_bound_no_plus_one():
    res = SB.run([simple(rate=6, run_m=1.62)], rules(), CTX)
    s = one(res, "STIRRUP_COUNT")
    assert s["state"] == AR.LOWER_BOUND and s["count"] == math.ceil(6 * 1.62) == 10 and s["kg"] is None
    assert s["count_convention_not_adopted"] == 11 and s["provenance"]["LOW"] == s["provenance"]["BEST"] == 10
    occ = simple(rate=6, run_m=1.62)
    occ["stirrups"][0]["register_count"] = 11                    # a register that added the +1 end bar
    with pytest.raises(SB.SuperstructureBeamRebarError, match="count 10 != register 11"):
        SB.run([occ], rules(), CTX)
    occ = simple()
    occ["stirrups"][0]["first_last"] = {"state": "SOURCE_ESTABLISHED"}
    with pytest.raises(SB.SuperstructureBeamRebarError, match="no end bar"):
        SB.run([occ], rules(), CTX)


def test_stirrup_kg_blocked_while_legs_path_hooks_unknown():
    res = SB.run([simple()], rules(), CTX)
    cp = one(res, "STIRRUP_CORE_PATH")
    assert cp["state"] == AR.BLOCKED_UNQUANTIFIED and cp["kg"] is None and cp["stirrup_count_known"]
    assert res["summary"]["STIRRUP_MASS_KNOWN"] == {"records": 0, "kg": 0.0}
    occ = simple()
    occ["stirrups"][0]["core_path_missing"] = []
    est = {"state": "SOURCE_ESTABLISHED", "why": "x"}
    cp = one(SB.run([occ], rules(stirrup_topology=est), CTX), "STIRRUP_CORE_PATH")   # legs known, hooks not
    assert cp["state"] == AR.BLOCKED_UNQUANTIFIED and cp["missing_facets"] == ["STIRRUP HOOKS NOT_ESTABLISHED"]
    with pytest.raises(SB.SuperstructureBeamRebarError, match="stirrup_hooks"):
        SB.run([occ], rules(stirrup_topology=est, stirrup_hooks=est), CTX)


def test_cb_stirrups_per_span_and_ambiguous_rates():
    res = SB.run([cb(rates=(10, 6))], rules(), CTX)
    cnt = sorted((c["span_index"], c["count"]) for c in by(res, "STIRRUP_COUNT"))
    assert cnt == [(1, math.ceil(10 * 4.6)), (2, math.ceil(6 * 3.6))]
    same = lambda k: [{"name": "FORWARD", "component": "STIRRUP_COUNT", "count": 1, "dia_mm": 8,  # noqa: E731
                       "run_rule": ["BARS_PER_METRE", 7]},
                      {"name": "REVERSED", "component": "STIRRUP_COUNT", "count": 1, "dia_mm": 8,
                       "run_rule": ["BARS_PER_METRE", 7]}]
    res = SB.run([cb(reading="AMBIGUOUS", runs=[], stir_interp=same)], rules(), CTX)
    assert all(c["state"] == AR.LOWER_BOUND and c["release_basis"] == "CANDIDATE_INVARIANT"
               for c in by(res, "STIRRUP_COUNT"))
    diff = lambda k: [same(k)[0], dict(same(k)[1], dia_mm=10)]  # noqa: E731
    res = SB.run([cb(reading="AMBIGUOUS", runs=[], stir_interp=diff)], rules(), CTX)
    assert all(c["state"] == AR.BLOCKED_UNQUANTIFIED for c in by(res, "STIRRUP_COUNT"))


# ----------------------------------------------------------------------------------- side / openings / untagged
def test_side_bar_text_retained_but_quantity_blocked():
    side = {"applicability": "PRINTED", "raw_text": "2%%C12/30cm", "count": 2, "dia_mm": 12, "spacing_cm": 30,
            "token_handles": ["1FC6"], "why": "per face or total not stated"}
    res = SB.run([simple(side=side)], rules(), CTX)
    s = one(res, "SIDE_REBAR")
    assert s["state"] == AR.BLOCKED_UNQUANTIFIED and s["kg"] is None
    assert (s["raw_text"], s["bar_count"], s["dia_mm"], s["spacing_cm"]) == ("2%%C12/30cm", 2, 12, 30)
    assert "not source-quantified" in s["why"]
    assert one(SB.run([simple()], rules(), CTX), "SIDE_REBAR")["state"] == SB.NOT_APPLICABLE
    with pytest.raises(SB.SuperstructureBeamRebarError, match="side_bar_semantics"):
        SB.run([simple(side=side)], rules(side_bar_semantics={"state": "SOURCE_ESTABLISHED", "why": "x"}), CTX)


def test_no_beam_opening_means_opening_components_not_applicable():
    res = SB.run([simple(openings=[{"opening_id": "OPN-1", "state": "NOT_APPLICABLE"}])], rules(), CTX)
    for c in SB.OPENING_COMPONENTS:
        r = one(res, c)
        assert r["state"] == SB.NOT_APPLICABLE and r["kg"] is None


def test_real_synthetic_beam_opening_activates_the_detail():
    pre = BR.opening_components([{"member": "BL1", "relation": "INSIDE_BAND"}])   # PRE-S6 classifier
    assert {p["STATE"] for p in pre} == {"CANDIDATE"}
    op = {"opening_id": "OPN-REAL", "state": "PHYSICAL_BEAM_OPENING" if any(p["STATE"] != "NOT_APPLICABLE"
                                                                           for p in pre) else "NOT_APPLICABLE"}
    active, n = SB.opening_activation([op])
    assert active and n == 1
    res = SB.run([simple(openings=[op])], rules(), CTX)
    for c in SB.OPENING_COMPONENTS:
        r = one(res, c)
        assert r["state"] == AR.BLOCKED_UNQUANTIFIED and "ACTIVATED" in r["why"] and r["activated_by"] == ["OPN-REAL"]
    assert BR.opening_components([{"member": "BL1", "relation": "LINEWORK_ENTERS_BAND"}])[0]["STATE"] == \
        "NOT_APPLICABLE"


def test_geometry_without_tag_is_conserved_never_assigned():
    ut = {"object_id": "SPAN:SH1:BL9:0-1000", "sheet": "SH1", "floor": "F1", "object_kind": "MEMBER_SPAN",
          "length_m": 1.0, "why": "no tag binds this span; the member carries B27 elsewhere"}
    res = SB.run([simple()], rules(), CTX, untagged=[ut])
    u = res["untagged"][0]
    assert u["occurrence_terminal"] == "GEOMETRY_WITHOUT_TAG" and u["occurrence_state"] == "BLOCKED_TYPE"
    assert u["mark"] == "" and u["known_kg"] is None and "never assigned from nearby marks" in \
        u["occurrence_blocking_reason"]
    assert res["summary"]["untagged_geometry"] == 1
    assert res["summary"]["final_superstructure_beam_rebar"] == "FINAL SUPERSTRUCTURE BEAM REBAR NOT ESTABLISHED"


# ------------------------------------------------------------------------------------------- ends / unit mass
def test_development_blocked_and_no_code_default_in_the_engine():
    res = SB.run([simple()], rules(), CTX)
    for c in ("DEVELOPMENT_1", "DEVELOPMENT_2"):
        r = one(res, c)
        assert r["state"] == AR.BLOCKED_UNQUANTIFIED and r["kg"] is None and r["provenance"]["BLOCKING_REASON"]
    with pytest.raises(SB.SuperstructureBeamRebarError, match="development"):
        SB.run([simple()], rules(development={"state": "SOURCE_ESTABLISHED", "why": "40D"}), CTX)
    src = (ROOT / "engine/source/superstructure_beam_rebar.py").read_text(encoding="utf-8")
    for bad in (r"\b40D\b", r"\b70D\b", r"\bACI\b", "Eurocode", r"\bBS 8110", "christian", "freelancer", "U-C4N",
                "kg/m3"):
        assert not re.search(bad, src), bad


def test_hooks_blocked():
    res = SB.run([cb()], rules(), CTX)
    for c in ("HOOK_1", "HOOK_2"):
        assert one(res, c)["state"] == AR.BLOCKED_UNQUANTIFIED
    with pytest.raises(SB.SuperstructureBeamRebarError, match="bar_end_hooks"):
        SB.run([cb()], rules(bar_end_hooks={"state": "SOURCE_ESTABLISHED", "why": "column hook rule"}), CTX)


def test_d2_over_162_and_kg_tamper_is_refused():
    res = SB.run([simple(top=(3, 20))], rules(), CTX)
    t = one(res, "TOP_MAIN")
    assert t["kg_per_m"] == pytest.approx(400 / 162) and t["kg"] == pytest.approx(3 * 3.0 * 400 / 162)
    assert "D^2/162" in t["provenance"]["FORMULA"] and t["provenance"]["CONVENTION_ID"].endswith("D2_OVER_162")
    bad = copy.deepcopy(t)
    bad["kg"] *= 1.1
    with pytest.raises(SB.SuperstructureBeamRebarError, match="kg != count"):
        SB.validate_record(bad)


def test_mass_conservation_across_occurrences():
    res = SB.run([simple("S7"), simple("S8", top=(3, 16)), cb("C17")], rules(), CTX)
    cons = res["conservation"]
    assert cons["all_pass"], cons["checks"]
    assert cons["project_known_kg"] == pytest.approx(sum(b["net_bbs_kg"] for b in res["bbs"]))
    assert res["summary"]["known_source_derived_superstructure_beam_rebar_kg"] == pytest.approx(
        cons["project_known_kg"])
    occ_rows = copy.deepcopy(res["occurrences"])
    occ_rows[0]["known_kg"] += 1.0
    assert not SB.conservation(occ_rows, res["components"], res["parts"], res["bbs"],
                               res["summary"]["accurate_summary"])["checks"]["component_kg_equals_occurrence_known_kg"]


def test_provenance_on_every_mass_component():
    res = SB.run([simple("S9"), cb("C18")], rules(), CTX)
    need = ("PROJECT_ID", "DRAWING_ID", "DRAWING_SHA", "REVISION", "ELEMENT_OCCURRENCE_ID", "ELEMENT_MARK",
            "ELEMENT_FAMILY", "SOURCE_HANDLES", "SCHEDULE_HANDLES", "GEOMETRY_HANDLES", "SOURCE_TEXT", "DETAIL_ID",
            "RULE_ID", "CONVENTION_ID", "MEASUREMENT_STATE", "AUTHORITY_STATE", "RELEASE_STATE", "FORMULA",
            "INPUTS", "ENGINE_COMMIT", "REGISTER_VERSION", "CALCULATION_ROUND")
    for c in res["components"]:
        pv = c["provenance"]
        assert all(pv.get(k) not in (None, "") for k in need), c["record_id"]
        assert pv["ELEMENT_FAMILY"] == "BEAM" and pv["ELEMENT_SUBFAMILY"] == c["subfamily"]
        if c["subfamily"] == SB.CONTINUOUS_BEAM:
            assert pv["CB_GROUP_ID"] == "C18" and pv["READING_DIRECTION_STATE"] == "FORWARD"
        if c["bar_run_id"]:
            assert pv["BAR_RUN_ID"] == c["bar_run_id"] and "SPAN_INDEX" in pv
    for p in res["parts"]:
        SB.validate_part(p)
    rec = copy.deepcopy(by(res, "BOTTOM_MAIN", "C18")[0])
    del rec["provenance"]["BAR_RUN_ID"]
    with pytest.raises(SB.SuperstructureBeamRebarError, match="BAR_RUN_ID"):
        SB.validate_record(rec)
    rec = copy.deepcopy(one(res, "TOP_MAIN", "S9"))
    rec["provenance"]["FOOTING_MARK"] = "B1"
    with pytest.raises(SB.SuperstructureBeamRebarError):
        SB.validate_record(rec)
    rec = copy.deepcopy(one(res, "TOP_MAIN", "S9"))
    rec["state"] = rec["provenance"]["RELEASE_STATE"] = AR.VERIFIED
    with pytest.raises(SB.SuperstructureBeamRebarError, match="never calls a beam bar complete"):
        SB.validate_record(rec)


def test_blocked_components_never_disappear_and_carry_no_hidden_kg():
    res = SB.run([simple(), cb()], rules(), CTX)
    for o in res["occurrences"]:
        comps = {c["component"] for c in res["components"] if c["occurrence_id"] == o["occurrence_id"]}
        assert set(SB.COMPONENTS) <= comps
    for c in res["components"]:
        if c["state"] in (AR.BLOCKED_UNQUANTIFIED, SB.NOT_APPLICABLE):
            assert c["kg"] is None
    s = res["summary"]
    assert s["SIMPLE_BEAM_BLOCKED_MODELLED_KG"] == 0 and s["CONTINUOUS_BEAM_BLOCKED_MODELLED_KG"] == 0
