"""T-426: ground-beam SECTION class per run, frame by frame, against the line that bills it.

Villa V426 (hand fixture, not Alsenan). Printed sections as a p.13-style sheet: interior > 5 m 30 x 60, < 5 m 30 x 40,
< 2.5 m 30 x 30 (the first two 'without concentrated load'); exterior 30 x depth by levels; court: none.
  Band P (Y): face lines drawn 8.00 m, founded neck N1 0.30 at 3.85 .. 4.15 m (the plan outline is buffered 0.5 mm in
    the read, so the read cut is 3.8495 .. 4.1505). Runs P#1 = 3.85, P#2 = 3.85 m -> LT5M each -> 0.40.
    The candidate line bills the whole band at the 8.00 m class (0.60): section term on the runs
    = 0.30 x (3.85 + 3.85) x (0.60 - 0.40) = 0.462 m3 (DIFFERS; the 0.30 neck length is a LENGTH term, not here).
  Run Q: 4.98 m on the ground-beam plan, 5.03 m on the foundation plan (neck drawn 50 mm further) -> LT5M / GT5M
    -> RANGE 0.40 .. 0.60; a line at 0.60 over 4.98 m stakes 0 .. 0.30 x 4.98 x 0.20 = 0.2988 m3 (INSIDE_RANGE).
  Run R: 2.00 m -> 'less than 2.5 m' and 'less than 5 m' both hold literally -> 0.30 .. 0.40; a line at 0.40 stakes
    0 .. 0.30 x 2.00 x 0.10 = 0.060 m3.
  Run S: exactly 5.000 m -> ON_LIMIT, 0.40 .. 0.60, HELD.
  Exterior run E 3.00 m, printed depth 0.95 (two levels): line at 0.95 AGREE; line at 0.40 DIFFERS
    0.30 x 3.00 x (0.40 - 0.95) = -0.495 m3.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t426"
sys.path.insert(0, str(HERE))
import t426_rules as R  # noqa: E402
import t426_spans as S  # noqa: E402


def _band(drawn=8.0, cut=(3.8495, 4.1505), end_columns=()):
    col = {"handle": "N1", "a_m": cut[0], "b_m": cut[1], "m": round(cut[1] - cut[0], 4), "at_end": False}
    fr = {k: {"columns": [dict(col)]} for k in ("GBP", "FP", "CAP")}
    return {"id": "P", "dir": "Y", "drawn_m": drawn, "frames": fr, "supports": {"rings": [], "junctions": []},
            "end_columns": list(end_columns)}


# ---------------- normal cases (hand figures in the module docstring)

def test_titles_by_span():
    assert R.titles_for_span(6.00) == ("GT5M",)
    assert R.titles_for_span(4.20) == ("LT5M",)
    assert R.titles_for_span(2.00) == ("LT2_5M", "LT5M")
    assert R.titles_for_span(5.000) == ("ON_LIMIT",)
    assert R.titles_for_span(4.9996) == ("ON_LIMIT",)
    assert R.titles_for_span(4.9990) == ("LT5M",)


def test_band_split_by_neck_exact_cuts():
    segs = S.band_segments(_band(), "GBP")
    assert [s[2] for s in segs] == [3.85, 3.85]


def test_band_split_mirror_invariant():
    b = _band(cut=(8.0 - 4.1505, 8.0 - 3.8495))
    assert sorted(s[2] for s in S.band_segments(b, "GBP")) == [3.85, 3.85]


def test_end_column_frame_shift():
    b = _band(end_columns=[{"end": 0, "handle": "C9", "net_shift_m": {"FP": 0.05, "CAP": 0.0}}])
    sp = S.spans_by_frame(b)
    assert [s[2] for s in sp["GBP"]] == [3.85, 3.85]
    assert [s[2] for s in sp["FP"]] == [3.90, 3.85]


def test_line_over_neck_split_runs_differs():
    runs = [{"L_m": 3.85, "section": R.run_section("INTERIOR", {"GBP": 3.85})},
            {"L_m": 3.85, "section": R.run_section("INTERIOR", {"GBP": 3.85})}]
    stake, verdict = R.line_stake(0.30, 0.60, runs)
    assert verdict == "DIFFERS"
    assert stake == (0.462, 0.462)


def test_frames_differ_give_range():
    sec = R.run_section("INTERIOR", {"GBP": 4.98, "FP": 5.03})
    assert sec["status"] == "RANGE" and sec["frames_differ"] is True
    assert sec["D_m"] == (0.40, 0.60)
    stake, verdict = R.line_stake(0.30, 0.60, [{"L_m": 4.98, "section": sec}])
    assert verdict == "INSIDE_RANGE"
    assert stake == (0.0, 0.2988)


def test_d34_both_titles_kept():
    sec = R.run_section("INTERIOR", {"GBP": 2.00})
    assert sec["D_m"] == (0.30, 0.40) and sec["status"] == "RANGE"
    stake, verdict = R.line_stake(0.30, 0.40, [{"L_m": 2.00, "section": sec}])
    assert verdict == "INSIDE_RANGE" and stake == (0.0, 0.06)


def test_on_limit_held_both_depths():
    sec = R.run_section("INTERIOR", {"GBP": 5.000})
    assert sec["status"] == "ON_LIMIT" and sec["D_m"] == (0.40, 0.60)


def test_exterior_by_levels():
    sec = R.run_section("EXTERIOR", {}, (0.95, 0.95))
    assert R.line_stake(0.30, 0.95, [{"L_m": 3.0, "section": sec}]) == ((0.0, 0.0), "AGREE")
    assert R.line_stake(0.30, 0.40, [{"L_m": 3.0, "section": sec}]) == ((-0.495, -0.495), "DIFFERS")


def test_load_qualifier_status():
    assert R.run_section("INTERIOR", {"GBP": 3.85}, loaded=True)["d33_held"] is True
    assert R.run_section("INTERIOR", {"GBP": 3.85}, loaded=False)["d33_held"] is False
    assert R.LOAD_QUALIFIED == {"GT5M": True, "LT5M": True, "LT2_5M": False}


def test_derived_depth_within_half_mm_is_the_printed_depth():
    sec = R.run_section("INTERIOR", {"GBP": 4.2723})
    assert R.line_stake(0.30, 0.399999, [{"L_m": 4.2723, "section": sec}]) == ((0.0, 0.0), "AGREE")
    stake, verdict = R.line_stake(0.30, 0.399, [{"L_m": 4.2723, "section": sec}])
    assert verdict == "DIFFERS"


def test_run_order_invariant():
    a = {"L_m": 3.85, "section": R.run_section("INTERIOR", {"GBP": 3.85})}
    b = {"L_m": 6.0, "section": R.run_section("INTERIOR", {"GBP": 6.0})}
    assert R.line_stake(0.30, 0.60, [a, b]) == R.line_stake(0.30, 0.60, [b, a])


# ---------------- adverse cases

def test_adverse_section_borrowed_from_band_refused():
    # the 0.60 depth belongs to the 8.00 m band (or a > 5 m neighbour), not to the 3.85 m run
    assert R.borrowed_section_refused(3.85, 8.00, 0.60) is True
    assert R.borrowed_section_refused(3.85, 8.00, 0.40) is False


def test_adverse_held_line_never_valued_zero():
    sec = R.run_section("INTERIOR", {"GBP": 3.85})
    stake, verdict = R.line_stake(0.30, None, [{"L_m": 3.85, "section": sec}])
    assert stake is None and verdict == "HELD_LINE"


def test_adverse_no_printed_section_never_zero():
    for sec in (R.run_section("COURT", {}), R.run_section("EXTERIOR", {}, None)):
        stake, verdict = R.line_stake(0.30, 0.30, [{"L_m": 2.0, "section": sec}])
        assert stake is None and verdict == "NO_PRINTED_SECTION"


def test_adverse_missing_span_and_units():
    with pytest.raises(R.CensusError):
        R.titles_for_span(None)
    with pytest.raises(R.CensusError):
        R.titles_for_span(4200)          # mm given as m
    with pytest.raises(R.CensusError):
        R.run_section("INTERIOR", {})
    with pytest.raises(R.CensusError):
        R.run_section("EXTERIOR", {}, (950, 950))
    with pytest.raises(R.CensusError):
        R.line_stake(300, 0.40, [{"L_m": 1.0, "section": R.run_section("INTERIOR", {"GBP": 1.0})}])
    with pytest.raises(R.CensusError):
        R.line_stake(0.30, 0.40, [])
    with pytest.raises(R.CensusError):
        R.run_section("BASEMENT", {})


def test_adverse_one_frame_never_chosen():
    # the class is the union over the frames, never the GBP frame alone
    sec = R.run_section("INTERIOR", {"GBP": 4.98, "FP": 5.03, "CAP": 4.98})
    assert set(sec["titles"]) == {"LT5M", "GT5M"}


# ---------------- Alsenan pins (committed inputs only; no private file)

def test_alsenan_census_reproduces_and_pins():
    import t426_alsenan as A
    doc = A.census()
    assert json.loads((HERE / "CENSUS_T426.json").read_text(encoding="utf-8")) == json.loads(
        json.dumps(doc, sort_keys=True))
    ids = [r["line_id"] for r in doc["lines"]]
    assert len(ids) == 58 and len(set(ids)) == 58
    assert doc["gbp_section_marks"] == 0
    differs = {r["line_id"]: r["stake_m3"] for r in doc["lines"] if r["verdict"] == "DIFFERS"}
    assert {k[:10] for k in differs} == {"L-fe78ae28", "L-0e30aadb"}
    for v in differs.values():
        assert v == [0.423, 0.423]
    assert doc["candidate"] == "ARCH_TAKEOFF_V3.0.36"
    assert doc["candidate_json_sha256"].startswith("d462203f")
    # the 9 lines the Checker's D-34 record holds (DG-a31a0d7e, bound to their content) are HELD, never valued
    dg = [r for r in doc["lines"] if r["downgrade"] == "DG-a31a0d7e9dd564ad"]
    assert len(dg) == 9 and all(r["state"] == "HELD" and r["stake_m3"] is None for r in dg)
    held = [r for r in doc["lines"] if r["state"] == "HELD"]
    assert all(r["stake_m3"] is None for r in held)


def test_alsenan_read_has_no_coordinate():
    d = json.loads((HERE / "ALSENAN_T426_READ.json").read_text(encoding="utf-8"))

    def keys(o):
        if isinstance(o, dict):
            for k, v in o.items():
                yield k
                yield from keys(v)
        elif isinstance(o, list):
            for v in o:
                yield from keys(v)
    assert not ({"x", "y", "insert", "start", "end", "center"} & set(keys(d)))
    assert d["gbp_text_census"]["section_marks"] == 0
