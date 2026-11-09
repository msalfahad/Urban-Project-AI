"""T-554: statement adapters (T-543 / T-546 / T-542) + Checker corrections on the T-548 builder (read only).
Synthetic villa "S554" (not the training villa) by hand per adapter, adverse cases, then the merged training-villa
sources (committed research outputs only; no private input)."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t554"))
import statement_adapters as SA  # noqa: E402
import t554_build as B  # noqa: E402

S = SA.S
Dd = Decimal


# ---- S554 blockwork (T-543 format), by hand. Freelancer 100.00 m2. Engine: one valued line V1 40.00 (GF 0.20) and
# held lines H20 (GF t=0.20) and H15 (GF t=0.15); parapet RC line P (m3, HELD). Components: GF storey walls his 70.00,
# engine 40.00: HELD wall W2 (t 0.20) 20.00, height 4.00 RULE_DIFFERENCE, residual 6.00 UNRESOLVED (= 30.00);
# parapets his 30.00: block alternative 12.00 HELD, RC upstand 9.00 ENGINE_RIGHT, residual 9.00 UNRESOLVED (= 30.00).
# Difference 100 - 40 = 60 = 20 + 4 + 6 + 12 + 9 + 9. HELD 32, RULE_DIFF 4, ENGINE_RIGHT 9, UNRESOLVED 15.
def s554_blockwork():
    d = {"candidate": "S554", "unit": "m2", "freelancer_total": "100.00", "engine_valued_total": "40.00",
         "by_cause": {}, "rows": [
             {"name": "GF storey walls (net of openings)", "cause": "SPLIT", "engine_valued_m2": "40.00",
              "decomposition": {"rows": [
                  {"name": "HELD walls: held opening", "cause": "HELD", "delta": "20.00", "walls": ["GF-W2"]},
                  {"name": "height convention: flat vs clear", "cause": "RULE_DIFFERENCE", "delta": "4.00",
                   "walls": []},
                  {"name": "RESIDUAL: wall-length census", "cause": "UNRESOLVED", "delta": "6.00", "walls": []}]}},
             {"name": "parapets (three rows)", "cause": "SPLIT", "engine_valued_m2": None,
              "decomposition": {"rows": [
                  {"name": "parapet face above the RC upstand: block", "cause": "HELD", "delta": "12.00"},
                  {"name": "RC upstand 0.30 m above the slab", "cause": "ENGINE_RIGHT", "delta": "9.00"},
                  {"name": "RESIDUAL: parapet height below the finished roof", "cause": "UNRESOLVED",
                   "delta": "9.00"}]}}]}
    lines = [{"line_id": "V1", "element_id": "GF-WALLS:walls t=0.20#X", "class": "RELEASED", "qty": "40.00"},
             {"line_id": "H20", "element_id": "GF-WALLS:walls t=0.20", "class": "HELD", "qty": None},
             {"line_id": "H15", "element_id": "GF-WALLS:walls t=0.15", "class": "HELD", "qty": None}]
    walls = [{"wall_id": "GF-W1", "floor": "GF", "t_m": "0.2"}, {"wall_id": "GF-W2", "floor": "GF", "t_m": "0.2"}]
    return d, lines, walls


def s554_parapet_correction(sec_id="S554/blockwork"):
    return {"id": "F-C-S554", "section_id": sec_id, "row": "parapets: RC upstand", "delta": "9.00",
            "class": "ENGINE_RIGHT", "annotate": {"depends_on": "H1", "note_add": "rests on H1 (S554)"}}


def blockwork_section():
    d, lines, walls = s554_blockwork()
    sec = SA.t543_from(d, lines, walls, parapet_lines=[("P", "ROOF")])
    sec["section_id"] = "S554/blockwork"
    return sec


def test_s554_blockwork_by_hand():
    sec = blockwork_section()
    held = [r for r in sec["rows"] if r["class"] == "HELD"]
    assert held[0]["held_line_ids"] == ["H20"]          # wall W2 is 0.20 -> only the 0.20 held line
    assert held[1]["held_line_ids"] == ["P"]            # parapet block: cross-family hold (R-T554-1)
    st = S.build_statement([SA.for_builder(sec)])
    c = st["sections"][0]
    assert c["difference"] == "60" and c["engine_valued"] == "40"
    assert c["by_class"] == {"ENGINE_RIGHT": "9", "ENGINE_WRONG": "0", "RULE_DIFFERENCE": "4", "HELD": "32",
                             "TOLERANCE": "0", "UNRESOLVED": "15"}
    assert c["engine_bounded"]["high_open"] is True and c["engine_bounded"]["low_at_least"] == "40"


def test_s554_h1_correction_applied_and_dropped_refused():
    sec = blockwork_section()
    corr = [s554_parapet_correction()]
    st0 = S.build_statement([SA.for_builder(sec)])
    with pytest.raises(SA.AdapterError, match="dependency"):
        SA.verify_corrections(st0, corr)               # dropped class correction refused
    with pytest.raises(SA.AdapterError, match="dependency"):
        B.build_from([copy.deepcopy(sec)], {}, {}, corrections=corr)   # builder refuses the uncorrected statement
    SA.apply_corrections([sec], corr)
    st = B.build_from([sec], {"corrections_applied": ["F-C-S554"]}, {}, corrections=corr)
    r = [x for x in st["sections"][0]["rows"] if x["name"].startswith("parapets: RC upstand")][0]
    assert r["depends_on"] == "H1" and "rests on H1" in r["note"]


def test_s554_correction_on_changed_source_refused():
    sec = blockwork_section()
    c = s554_parapet_correction()
    c["delta"] = "9.50"
    with pytest.raises(SA.AdapterError, match="source changed"):
        SA.apply_corrections([sec], [c])


def test_s554_unknown_parapet_row_refused():
    d, lines, walls = s554_blockwork()
    d["rows"][1]["decomposition"]["rows"][0]["name"] = "something new"
    with pytest.raises(SA.AdapterError, match="not in the adapter table"):
        SA.t543_from(d, lines, walls, parapet_lines=[("P", "ROOF")])


def test_s554_held_line_given_zero_refused():
    sec = blockwork_section()
    sec["engine"]["held_lines"][0]["qty"] = "0"
    with pytest.raises(SA.AdapterError, match="never 0"):
        SA.refuse_held_as_zero(sec)
    d, lines, walls = s554_blockwork()
    lines[1]["qty"] = "0"
    with pytest.raises(SA.AdapterError, match="never 0"):
        SA.t543_from(d, lines, walls)


def test_s554_held_row_shown_as_zero_refused_by_builder():
    sec = blockwork_section()
    sec["rows"][0]["delta"] = "0"
    sec["rows"][2]["delta"] = "26.00"                  # keep the table closing: the guard, not closure, refuses
    with pytest.raises(S.StatementError, match="zero difference"):
        S.build_statement([SA.for_builder(sec)])


# ---- S554 wet room (T-546 format), by hand. Two rooms, one shared wall. Room A floor engine 4.00 / his 3.95
# (+0.05 ENGINE_RIGHT); room B engine 2.00 / his 2.00. Upturn rule height 0.20: A 1.40 m2 -> 7.00 lm, his perimeter
# 8.00: doorway 0.80 HELD (line TA), boundary +0.20 his short... -> 7.00 - 8.00 = -0.80 - 0.40 + 0.20.
# B 1.00 m2 -> 5.00 lm, his 5.80: doorway 0.80 with NO line -> UNRESOLVED. lm diff = (8 + 5.8) - 12 = 1.80 =
# HELD 0.80 + UNRESOLVED 0.80 + RULE_DIFF 0.40 - ENGINE_RIGHT 0.20.
def s554_wet():
    def floor_rows():
        return [{"room": "A", "engine_lines": [{"line_id": "FA", "qty": "4.00"}], "freelancer": "3.95",
                 "components": [{"name": "printed size", "qty": "0.05", "sign": 1, "cause": "ENGINE_RIGHT",
                                 "basis": "hand"}]},
                {"room": "B", "engine_lines": [{"line_id": "FB", "qty": "2.00"}], "freelancer": "2.00",
                 "components": []}]

    def upturn_rows():
        return [{"room": "A", "engine_lines": [{"line_id": "UA", "qty": "1.40", "height_source": "rule X"}],
                 "freelancer": "8.00", "components": [
                     {"name": "doorway segment 0.80 m", "qty": "0.80", "sign": -1, "cause": "HELD", "basis": "r"},
                     {"name": "edge, no wall", "qty": "0.40", "sign": -1, "cause": "RULE_DIFFERENCE", "basis": "r"},
                     {"name": "boundary", "qty": "0.20", "sign": 1, "cause": "ENGINE_RIGHT", "basis": "r"}]},
                {"room": "B", "engine_lines": [{"line_id": "UB", "qty": "1.00", "height_source": "rule X"}],
                 "freelancer": "5.80", "components": [
                     {"name": "doorway segment 0.80 m", "qty": "0.80", "sign": -1, "cause": "HELD", "basis": "r"}]},
                {"room": "C", "engine_lines": [{"line_id": "UC", "qty": None}], "freelancer": None,
                 "note": "C upturn HELD"}]
    return SimpleNamespace(floor_rows=floor_rows, upturn_rows=upturn_rows, FREELANCER_FLOOR_M2="5.95",
                           FREELANCER_UPTURN_LM="13.80", UPTURN_H="0.20", engine_floor_total=lambda: "6.00",
                           engine_upturn_lm_total=lambda: "12")


S554_HOLD = {"A": [("TA", "own door")], "B": [(None, "no transition record")]}
S554_INDEX = {"FA": {"class": "RELEASED", "measured_net": 4.0, "unit": "m2", "item_code": "FIN.WP.FLOOR"},
              "FB": {"class": "RELEASED", "measured_net": 2.0, "unit": "m2", "item_code": "FIN.WP.FLOOR"},
              "UA": {"class": "RELEASED", "measured_net": 1.4, "unit": "m2", "item_code": "FIN.WP.WALL_UPTURN"},
              "UB": {"class": "RELEASED", "measured_net": 1.0, "unit": "m2", "item_code": "FIN.WP.WALL_UPTURN"},
              "UC": {"class": "HELD", "measured_net": None, "unit": "m2", "item_code": "FIN.WP.WALL_UPTURN"},
              "TA": {"class": "HELD", "measured_net": None, "unit": "m2", "item_code": "FIN.WP.DOORWAY_TRANSITION"}}


def wet_sections():
    fl, up = SA.t546_from(s554_wet(), S554_HOLD, {"UC"})
    for x in (fl, up):
        x["section_id"] = x["section_id"].replace("T-546", "S554")
    return fl, up


def test_s554_wet_by_hand():
    fl, up = wet_sections()
    for x in (fl, up):
        SA.bind_cross_family(x, S554_INDEX)
    SA.bind_derived(up, S554_INDEX)
    st = S.build_statement([SA.for_builder(fl), SA.for_builder(up)])
    f, u = st["sections"]
    assert f["unit"] == "m2" and f["difference"] == "-0.05" and f["by_class"]["ENGINE_RIGHT"] == "-0.05"
    assert u["unit"] == "lm" and u["engine_valued"] == "12" and u["difference"] == "1.8"
    assert u["by_class"] == {"ENGINE_RIGHT": "-0.2", "ENGINE_WRONG": "0", "RULE_DIFFERENCE": "0.4", "HELD": "0.8",
                             "TOLERANCE": "0", "UNRESOLVED": "0.8"}
    rb = [r for r in u["rows"] if r["name"].startswith("B:")][0]
    assert rb["class"] == "UNRESOLVED" and rb["engine_status"] == "NONE"   # no line -> never HELD (R-T554-1 (d))
    assert u["engine_bounded"]["high_open"] is True                       # cross-family held, no bound converted
    assert len(st["totals"]) == 2                                          # m2 and lm never in one total
    with pytest.raises(S.StatementError, match="never in one total"):
        S.merge_totals(*st["totals"])


def test_s554_lm_without_height_source_refused():
    fl, up = wet_sections()
    up["engine"]["valued_lines"][0]["derived"]["height_source"] = ""
    with pytest.raises(SA.AdapterError, match="without a source"):
        SA.bind_derived(up, S554_INDEX)


def test_s554_his_multiplier_as_m2_refused():
    """His lm (perimeter x 1) presented as m2 against the engine's m2 lines: a unit never enters another total."""
    fl, up = wet_sections()
    bad = copy.deepcopy(up)
    bad["engine"]["valued_lines"] = [{"line_id": "UA", "qty": "1.40", "unit": "m2"}]
    with pytest.raises(S.StatementError, match="differs"):
        S.check_section(SA.for_builder(bad))


def test_s554_cross_family_same_unit_refused():
    fl, up = wet_sections()
    up["engine"]["held_cross_family"][0]["unit"] = "lm"
    idx = dict(S554_INDEX)
    idx["TA"] = dict(idx["TA"], unit="lm")
    with pytest.raises(SA.AdapterError, match="own held line"):
        SA.bind_cross_family(up, idx)


def test_s554_cross_family_not_held_refused():
    fl, up = wet_sections()
    idx = dict(S554_INDEX)
    idx["TA"] = dict(idx["TA"], **{"class": "RELEASED", "measured_net": 0.16})
    with pytest.raises(SA.AdapterError, match="not HELD"):
        SA.bind_cross_family(up, idx)


def test_s554_hold_table_mismatch_refused():
    with pytest.raises(SA.AdapterError, match="more doorway segments"):
        SA.t546_from(s554_wet(), {"A": [("TA", "own")]}, {"UC"})


# ---- S554 stair (T-542 format) beside a T-534-format section, by hand: wire tread T1 2.00 (line L1 1.999, polygon
# 0.001), beyond: riser R 0.50 on held line LR, landing LD 1.20 with no line -> fix T-502. Whole 3.70.
def test_s554_stair_beside_by_hand():
    d = {"rows": [
        {"key": "F", "surface": "TREAD", "bed_class": "STAIR_BED", "line_id": "L1", "in_v7_wire": True,
         "bed_m2": 2.0, "landing_class": None, "beside_m2": None, "floor_bed_line": None},
        {"key": "F", "surface": "RISER", "bed_class": "STAIR_BED", "line_id": "LR", "in_v7_wire": False,
         "bed_m2": 0.5, "landing_class": None, "beside_m2": None, "floor_bed_line": None},
        {"key": "LD", "surface": "LANDING", "bed_class": "STAIR_BED", "line_id": None, "in_v7_wire": False,
         "bed_m2": 1.2, "landing_class": "STAIR_LANDING", "beside_m2": None, "floor_bed_line": None}],
        "summary": {"whole_stair_bed": {"area_m2": 3.7}, "in_v7_wire": {"area_m2": 2.0},
                    "beyond_v7_wire": {"area_m2": 1.7}},
        "v7_wire_candidate_net": {"polygon_residual_m2": 0.001}}
    sec = {"section_id": "S554/stair", "engine": {"valued_lines": [{"line_id": "L1", "qty": "1.999"}]}}
    b = SA.t542_beside_from(d, sec, {"LR": {"class": "HELD"}})
    assert b["whole_at_least"] == "3.7" and b["beyond_wire"] == "1.7" and b["polygon_residual"] == "0.001"
    assert [(p["key"], p["state"], p["fix_row"]) for p in b["beyond_parts"]] == [
        ("F", "HELD_LINE", None), ("LD", "NO_CANDIDATE_LINE", "T-502")]
    d2 = copy.deepcopy(d)
    d2["summary"]["whole_stair_bed"]["area_m2"] = 3.8
    with pytest.raises(SA.AdapterError, match="whole"):
        SA.t542_beside_from(d2, sec, {"LR": {"class": "HELD"}})
    with pytest.raises(SA.AdapterError, match="not HELD"):
        SA.t542_beside_from(d, sec, {"LR": {"class": "RELEASED"}})


# ---- training villa: the five merged sources (committed outputs) ---------------------------------------------------
@pytest.fixture(scope="module")
def st():
    return B.build()


def sec(st, sid):
    return [x for x in st["sections"] if x["section_id"] == sid][0]


def test_every_source_closes_exactly(st):
    want = {"T-541/membrane": ("285", "209.65844", "75.34156"), "T-541/upturn": ("194", "187.83416", "6.16584"),
            "T-534/stair-bed": ("39.485", "35.4313", "4.0537"),
            "T-543/blockwork": ("1260.6895", "467.7925", "792.897"),
            "T-546/floor": ("72.01", "85.57571", "-13.56571"),
            "T-546/upturn": ("144.61", "126.072925", "18.537075")}
    for sid, (ref, eng, diff) in want.items():
        c = sec(st, sid)
        assert (c["reference_total"], c["engine_valued"], c["difference"]) == (ref, eng, diff), sid
        assert sum((Dd(v) for v in c["by_class"].values()), Dd(0)) == Dd(diff), sid
    assert sec(st, "T-534/stair-bed")["drawing_derived_beside"]["whole_at_least"] == "56.35861"


def test_ms1ld_corrected(st):
    rows = [r for r in sec(st, "T-534/stair-bed")["rows"] if r["name"].startswith("MS1-LD")]
    assert sorted((r["class"], r["delta"]) for r in rows) == [("ENGINE_WRONG", "1.4375"), ("RULE_DIFFERENCE", "0.0625")]
    assert [r["fix_row"] for r in rows if r["class"] == "ENGINE_WRONG"] == ["T-502"]
    assert sum(Dd(r["delta"]) for r in rows) == Dd("1.5")
    bc = sec(st, "T-534/stair-bed")["by_class"]
    assert bc["ENGINE_WRONG"] == "1.4375" and bc["RULE_DIFFERENCE"] == "-14.8694"
    b = sec(st, "T-534/stair-bed")["drawing_derived_beside"]
    assert b["cross_check"]["MS1-LD_drawing_m2"] == "1.4375"


def test_parapet_engine_right_rests_on_h1(st):
    r = [x for x in sec(st, "T-543/blockwork")["rows"] if x["name"].startswith("parapets: RC upstand")]
    assert len(r) == 1 and r[0]["class"] == "ENGINE_RIGHT" and r[0]["delta"] == "41.05128"
    assert r[0]["depends_on"] == "H1" and "rests on H1" in r[0]["note"]


def test_t543_classes_vs_source(st):
    """Every T-543 class total is the report's, except the one named re-class F-T554-2 (2F height on HELD walls)."""
    c = sec(st, "T-543/blockwork")
    src = json.loads(SA.T543_JSON.read_text(encoding="utf-8"))["by_cause"]
    moved = Dd("-4.476873")
    assert Dd(c["by_class"]["HELD"]) == Dd(src["HELD"]) + moved
    assert Dd(c["by_class"]["RULE_DIFFERENCE"]) == Dd(src["RULE_DIFFERENCE"]) - moved
    for k in ("ENGINE_RIGHT", "TOLERANCE", "UNRESOLVED"):
        assert Dd(c["by_class"][k]) == Dd(src[k]), k
    assert c["by_class"]["ENGINE_WRONG"] == "0"
    assert {x["unit"] for x in c["held_cross_family"]} == {"m3"}


def test_t546_upturn_lm_his_label(st):
    u = sec(st, "T-546/upturn")
    assert u["unit"] == "lm" and u["reference_label"] == "m.l"
    assert {x["unit"] for x in u["held_cross_family"]} == {"m2"}   # beside, never summed
    assert u["by_class"]["HELD"] == "13.9" and u["by_class"]["UNRESOLVED"] == "1.6"
    t = [x for x in st["totals"] if x["trade"] == "B8 wet-room waterproofing"]
    assert sorted(x["unit"] for x in t) == ["lm", "m2"]
    with pytest.raises(S.StatementError):
        S.merge_totals(*t)


def test_statement_reproduces():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t554/t554_build.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
