"""S8.7B package: the owner's provisional stair scenario reconciled with the drawings. Values are re-derived here by
hand or with code independent of the builder; passing tests prove arithmetic and reading, not engineering approval."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import pytest

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_stairs_s8_7b"
MANIFEST = PKG / "16_S8_7B_FREEZE_MANIFEST.json"
S87 = ROOT / "research" / "alsenan_stairs_s8_7"
S87A = ROOT / "research" / "alsenan_stairs_s8_7a"
BY_SHA = ROOT / "data/inputs/by_sha256"
ARCH = BY_SHA / "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
ST = BY_SHA / "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
SEC_PDF = BY_SHA / "1e7087d3e61bbb682c9107193c97550a2837e5198bde0ee311319bf7f4a08459.pdf"
HYG = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
needs_inputs = pytest.mark.skipif(not (ARCH.exists() and ST.exists() and SEC_PDF.exists()),
                                  reason="private drawings not present in data/inputs/by_sha256 (never committed)")


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name):
    with open(PKG / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def f(v):
    return float(v)


@pytest.fixture(scope="module")
def s():
    return J(PKG / "14_RELEASE_SUMMARY.json")


# ------------------------------------------------------------------ freeze, layering, release
def test_frozen_scenario_layer_over_unchanged_s8_7_and_s8_7a(s):
    m = J(MANIFEST)
    assert m["state"] == "FROZEN_BEFORE_COMPARISON" and m["references_read"] == []
    DR.verify_frozen(MANIFEST, ROOT)
    assert m["s8_7_manifest_sha256"] == hashlib.sha256((S87 / "17_S8_7_FREEZE_MANIFEST.json").read_bytes()).hexdigest()
    assert m["s8_7a_manifest_sha256"] == hashlib.sha256((S87A / "15_S8_7A_CORRECTION_MANIFEST.json").read_bytes()).hexdigest()
    assert s["release_delta"] == {"concrete_m3": 0.0, "kg": 0.0} == m["release_delta"]
    s87 = J(S87 / "16_S8_7_SUMMARY.json")["released"]
    assert s["frozen_release_unchanged"] == {"concrete_m3": s87["concrete_m3"], "kg": s87["kg"]}
    assert (s87["concrete_m3"], s87["kg"]) == (0.516582788, 59.020862261)
    assert len(s["frozen_baselines"]) == 27 and {"S7", "S8.7", "S8.7A", "S8.8"} <= set(s["frozen_baselines"])
    for mp in sorted((ROOT / "research").glob("*/*_MANIFEST.json")):
        if J(mp).get("state") in ("FROZEN_BEFORE_COMPARISON", "DATED_CORRECTION_LAYER"):
            DR.verify_frozen(mp, ROOT)


def test_registry_and_no_benchmark_inputs():
    m = J(MANIFEST)
    assert not [p for p in m["inputs"] if re.search(r"registers_v3b|R9_1|R5_|post_freeze|pre_s8|Quotation|pricing", p)]
    assert not [p for p in m["code"] if "post_freeze" in p]
    src = (PKG / "build_s8_7b.py").read_text(encoding="utf-8")
    for ref in ("BOQ_LINES_V3B", "STAIR_ARCHITECTURAL_REGISTER", "post_freeze", "02_STRUCTURAL_ELEMENT_CENSUS",
                "03_CONCRETE_COVERAGE", "04_REBAR_COVERAGE", "06_S8_CANDIDATE", "07_INTERFACE_DOUBLE"):
        assert ref not in src, ref                      # firewalled until after the freeze (the PRE-S8 manifest is verified)
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    for p in ("engine/source/stair_scenario_checks.py", "research/alsenan_stairs_s8_7b/build_s8_7b.py"):
        assert f'"{p}"' in reg


def test_owner_register():
    o = {r["ID"]: r for r in rows("01_OWNER_SCENARIO_ASSUMPTION_REGISTER.csv")}
    assert (o["O-01"]["VALUE"], o["O-01"]["STATUS"]) == ("28", "PROVISIONAL_OWNER_SCENARIO")
    assert (o["O-02"]["VALUE"], o["O-02"]["STATUS"]) == ("27", "PROVISIONAL_OWNER_SCENARIO")
    assert (o["O-03"]["VALUE"], o["O-03"]["STATUS"]) == ("UNKNOWN", "REQUIRES_ENGINEER_CONFIRMATION")
    assert (o["O-04"]["VALUE"], o["O-04"]["STATUS"]) == ("30 mm", "PROVISIONAL_OWNER_SCENARIO")
    assert o["O-05"]["VALUE"] == "NOT STATED" and "never assumed" in o["O-05"]["USE_IN_S8_7B"]
    assert "NOT an approval" in o["O-09"]["USE_IN_S8_7B"]


# ------------------------------------------------------------------ risers and setting out (by hand)
def test_riser_table_by_hand():
    r = {(x["STAIR_RUN"], x["RISERS"]): x for x in rows("02_RISER_CALCULATION_TABLE.csv")}
    a1, a2, c = r[("A1", "28")], r[("A2", "27")], r[("C", "28")]
    assert f(a1["FINISHED_RISER_MM_FULL_PRECISION"]) == pytest.approx(4500 / 28, abs=1e-9)
    assert f(a2["FINISHED_RISER_MM_FULL_PRECISION"]) == pytest.approx(4200 / 27, abs=1e-9)
    assert a1["PREFERENCE_150_160"] == "TOLERANCE_DECISION_REQUIRED" and f(a1["ABOVE_PREFERRED_MAX_MM"]) == pytest.approx(
        4500 / 28 - 160, abs=1e-6)
    assert a2["PREFERENCE_150_160"] == "WITHIN_PREFERENCE"
    assert json.loads(a1["SETTING_OUT_ROUNDED_RISERS"]) == {"160": 8, "161": 20}
    assert json.loads(a2["SETTING_OUT_ROUNDED_RISERS"]) == {"155": 12, "156": 15}
    assert json.loads(a1["TOP_LEVEL_DRIFT_IF_REPEATED_MM"]) == [28 * 160 - 4500, 28 * 161 - 4500]
    assert json.loads(a2["TOP_LEVEL_DRIFT_IF_REPEATED_MM"]) == [27 * 155 - 4200, 27 * 156 - 4200]
    assert c["STATUS"] == "DRAWN_ARRANGEMENT_EVALUATED"


def test_setting_out_schedule_never_accumulates():
    sch = rows("03_RISER_SETTING_OUT_SCHEDULE.csv")
    for sid, b, t, n in (("A1-OWNER-28", 1000.0, 5500.0, 28), ("A2-OWNER-27", 5500.0, 9700.0, 27),
                         ("C-DRAWN-28", 1000.0, 5500.0, 28)):
        rs = [x for x in sch if x["SCENARIO"] == sid]
        assert len(rs) == n and rs[-1]["RISES_ONTO"] == "TOP_FLOOR"
        for k, x in enumerate(rs, 1):
            exact = b + k * (t - b) / n
            assert f(x["FINISHED_LEVEL_EXACT_M"]) * 1000 == pytest.approx(exact, abs=1e-6)
            assert int(x["SETTING_OUT_LEVEL_MM"]) == math.floor(exact + 0.5)
            assert abs(int(x["SETTING_OUT_LEVEL_MM"]) - exact) <= 0.5 + 1e-9
        assert sum(int(x["SETTING_OUT_RISER_MM"]) for x in rs) == t - b
    a1 = [x for x in sch if x["SCENARIO"] == "A1-OWNER-28"]
    assert a1[15]["RISES_ONTO"] == "LANDING" and a1[15]["SEGMENT"] == "A1-W1"          # riser 16 onto the landing


# ------------------------------------------------------------------ landings
def test_landing_reconciliation_by_hand():
    L = rows("04_LANDING_ELEVATION_RECONCILIATION.csv")
    own = next(x for x in L if x["ARRANGEMENT"].startswith("OWNER-28"))
    h = 4500 / 28
    assert (own["RISERS_BEFORE_LANDING"], own["RISERS_AFTER_LANDING"]) == ("16", "12")
    assert f(own["LANDING_IMPLIED_BY_UNIFORM_RISERS_M"]) == pytest.approx(1.0 + 16 * h / 1000, abs=1e-9)
    assert f(own["IMPLIED_MINUS_PRINTED_MM"]) == pytest.approx(1000 + 16 * h - 3500, abs=1e-6)
    assert own["PRINTED_LEVEL_REACHABLE_WITH_UNIFORM_RISERS"] == "False"
    assert json.loads(own["NEAREST_BOUNDARIES_M"]) == pytest.approx([1 + 15 * h / 1000, 1 + 16 * h / 1000], abs=1e-6)
    assert json.loads(own["UNEQUAL_RISERS_TO_KEEP_PRINTED_LEVEL_MM"]) == pytest.approx([2500 / 16, 2000 / 12], abs=1e-6)
    every = next(x for x in L if x["ARRANGEMENT"].startswith("every uniform count"))
    want = [n for n in range(20, 41) if abs(2500 * n / 4500 - round(2500 * n / 4500)) * 4500 / n < 0.5]
    assert json.loads(every["RISERS"]) == want == [27, 36]
    sec = next(x for x in L if x["STAIR_RUN"] == "A1" and x["ARRANGEMENT"].startswith("section"))
    assert sec["RESULT"] == "CONSISTENT" and sec["RISERS"] == "27"
    a2 = {x["ARRANGEMENT"]: f(x["LANDING_IMPLIED_BY_UNIFORM_RISERS_M"]) for x in L if x["STAIR_RUN"] == "A2"}
    assert a2["OWNER-27 (architectural 1F plan allocation)"] == pytest.approx(5.5 + 16 * 4.2 / 27, abs=1e-9)
    assert a2["structural 1F roof sheet / 2F plan"] == pytest.approx(5.5 + 13 * 0.175, abs=1e-9)
    assert a2["section A-A (measured)"] == pytest.approx(5.5 + 13 * 0.168, abs=1e-9)
    assert all(x["LANDING_PRINTED_M"] == "" for x in L if x["STAIR_RUN"] in ("A2", "C"))


def test_section_a_a_measurements():
    ev = rows("13_SECTION_AND_DETAIL_EVIDENCE.csv")
    fl = {x["ITEM"]: int(x["VALUE"]) for x in ev if x["RECORD"] == "SECTION_A_A_FLIGHT"}
    assert [v for k, v in sorted(fl.items())] == [15, 12, 13, 12]
    lv = {x["ITEM"]: (f(x["VALUE"]), x["STATUS"]) for x in ev if x["RECORD"] == "SECTION_A_A_LEVEL"}
    assert lv["GF -> 1F half-landing (level line)"][0] == pytest.approx(3.50, abs=0.01)
    assert lv["+0.30 lobby floor (level line)"][0] == pytest.approx(0.30, abs=0.01)
    assert lv["1F -> 2F half-landing (level line)"] == (pytest.approx(7.684, abs=0.01), "SCALED_FROM_SECTION_1_100 (indicative)")
    cal = [x for x in ev if x["RECORD"] == "SECTION_A_A_CALIBRATION"]
    px = {x["ITEM"]: f(x["PIXEL_X"]) for x in cal}
    scale = (px["extension line 13.9 (bottom chain)"] - px["extension line 0 (bottom chain)"]) / 13.9
    assert scale == pytest.approx(600 / 0.0254 / 100, rel=0.005)                      # 1:100 at 600 dpi


# ------------------------------------------------------------------ beams
def test_head_beam_clearances_and_overlap_by_brute_force():
    b = rows("06_BEAM_INTERFERENCE_AUDIT.csv")
    get = {(x["INTERFACE"], x["ARRANGEMENT"]): x for x in b}
    own28 = get[("A1-F2 head / B20", "OWNER-28 (structural GF roof sheet)")]
    assert f(own28["CLEARANCE_TO_BEAM_FACE_MM"]) == pytest.approx(16111.856 - 16311.856, abs=1e-3)
    assert own28["RESULT"].startswith("INTERFERENCE") and "neither the flight is shortened nor the beam moved" in \
        own28["RESOLUTION"]
    assert f(get[("A1-F2 head / B20", "architectural GF plan")]["CLEARANCE_TO_BEAM_FACE_MM"]) == pytest.approx(100, abs=1e-3)
    own27 = get[("A2-F2 head / B23", "OWNER-27 (architectural 1F plan)")]
    assert f(own27["CLEARANCE_TO_BEAM_FACE_MM"]) == pytest.approx(100, abs=1e-3) and own27["RESULT"].startswith("CLEAR")
    assert get[("A2-F2 head / B23", "section A-A (12 risers, 11 goings of 300)")]["RESULT"].startswith("INTERFERENCE")
    # the last 200 mm of a 12-riser flight of 4500 / 28, 300 goings, 1200 wide, 160 waist: midpoint rule
    n, h, g, w, t = 12, 4500 / 28, 300.0, 1200.0, 160.0
    drop = t * math.hypot(g, h) / g
    m, s0, s1 = 40000, 3100.0, 3300.0
    ds = (s1 - s0) / m
    vol = sum(((math.floor((s0 + (i + 0.5) * ds) / g) + 1) * h - (h / g * (s0 + (i + 0.5) * ds) - drop)) * ds
              for i in range(m)) * w / 1e9
    assert json.loads(own28["OVERLAP_ZONE_M3_BY_WAIST"])["160"] == pytest.approx(vol, rel=1e-6)


# ------------------------------------------------------------------ finishes
def test_first_last_risers_by_hand():
    F = rows("07_FIRST_LAST_RISER_FINISH_BUILDUP.csv")
    h = 4500 / 28
    for x in F:
        if x["CASE"] == "GRID" and x["SCENARIO"] == "A1-OWNER-28":
            fb, ft, sb = f(x["FLOOR_BUILD_UP_BOTTOM_MM"]), f(x["FLOOR_BUILD_UP_TOP_MM"]), f(x["TREAD_BUILD_UP_MM"])
            assert f(x["FIRST_CONCRETE_RISER_MM"]) == pytest.approx(h + fb - sb, abs=1e-6)
            assert f(x["LAST_CONCRETE_RISER_MM"]) == pytest.approx(h - ft + sb, abs=1e-6)
            assert f(x["CONCRETE_RISE_MM"]) == pytest.approx(4500 - ft + fb, abs=1e-6)
            assert x["STATUS"] == "ILLUSTRATIVE_NOT_PROJECT_FACT"
    req = [x for x in F if x["CASE"] == "200_100_REQUIREMENT" and x["SCENARIO"] == "A1-OWNER-28"]
    r30 = next(x for x in req if x["TREAD_BUILD_UP_MM"] == "30")
    assert (f(r30["FLOOR_BUILD_UP_BOTTOM_MM"]), f(r30["FLOOR_BUILD_UP_TOP_MM"])) == pytest.approx((200 - h + 30, h + 30 - 100))
    assert all(x["STATUS"] == "NOT_SUPPORTED_BY_ANY_DRAWING" for x in req)
    wk = [x for x in F if x["CASE"].startswith("WORKED_EXAMPLE")]
    assert len(wk) == 28 and len({x["FINISHED_RISER_MM"] for x in wk}) == 1
    c = [f(x["CONCRETE_RISER_MM"]) for x in wk]
    assert c[0] == pytest.approx(h + 30) and c[-1] == pytest.approx(h - 30) and all(v == pytest.approx(h) for v in c[1:-1])


# ------------------------------------------------------------------ concrete
def test_concrete_sensitivity_by_closed_form():
    C = rows("08_WAIST_THICKNESS_CONCRETE_SENSITIVITY.csv")
    for x in C:
        if x["KIND"] == "FLIGHT":
            n, h, g, w, t = int(x["RISERS"]), f(x["RISER_MM"]), f(x["GOING_MM"]), f(x["WIDTH_MM"]), f(x["WAIST_MM"])
            closed = (n - 1) * g * w * (t * math.hypot(g, h) / g + h / 2) / 1e9
            assert f(x["GROSS_M3"]) == pytest.approx(closed, abs=1e-8)
            assert f(x["GROSS_M3"]) == pytest.approx(f(x["NET_M3"]) + f(x["BEAM_OVERLAP_ZONE_M3"]) + f(x["COLUMN_CUTOUT_M3"]),
                                                     abs=5e-9)
        if x["KIND"] == "STEPS ON GRADE":
            n, h, g, w, t = int(x["RISERS"]), f(x["RISER_MM"]), f(x["GOING_MM"]), f(x["WIDTH_MM"]), f(x["WAIST_MM"])
            solid = sum(k * h * g * w for k in range(1, n)) / 1e9
            assert f(x["UPPER_BOUND_M3"]) == pytest.approx(solid + (n - 1) * g * w * t / 1e9, abs=1e-8)
    assert {x["ELEMENT_ID"] for x in C if x["ALREADY_RELEASED_BY_S8_7"] == "True"} == {"A1-L1", "A2-T1", "C-T1"}
    assert all(f(x["NET_M3"]) == 0 for x in C if x["ALREADY_RELEASED_BY_S8_7"] == "True")
    assert not [x for x in C if x["LANE"] in ("SOURCE_VERIFIED_RELEASED", "PROJECT_BASIS_QTO")]
    for w in ("150", "160", "175", "200"):
        parts = [x for x in C if x["WAIST_MM"] == w and x["KIND"] == "TOTAL" and x["STAIR"] != "ALL"]
        grand = next(x for x in C if x["WAIST_MM"] == w and x["STAIR"] == "ALL")
        assert f(grand["NET_M3"]) == pytest.approx(sum(f(p["NET_M3"]) for p in parts), abs=1e-8)
        for p in parts:
            rs = [x for x in C if x["WAIST_MM"] == w and x["STAIR"] == p["STAIR"] and x["KIND"] != "TOTAL"]
            assert f(p["NET_M3"]) == pytest.approx(sum(f(x["NET_M3"]) for x in rs), abs=1e-8)
    g = [f(next(x for x in C if x["WAIST_MM"] == w and x["STAIR"] == "ALL")["NET_M3"]) for w in ("150", "160", "175", "200")]
    assert g == sorted(g)


def test_winder_geometry():
    C = rows("08_WAIST_THICKNESS_CONCRETE_SENSITIVITY.csv")
    for el in ("A1-W1", "A2-W1"):
        for x in [r for r in C if r["ELEMENT_ID"] == el]:
            areas = json.loads(x["EVIDENCE"].split("tread areas m2 ")[1])
            assert len(areas) == 4 and sum(areas) == pytest.approx(1.3 * 1.15, abs=1e-4)
            A, h, go, t = f(x["PLAN_AREA_M2"]), f(x["RISER_MM"]), f(x["GOING_MM"]), f(x["WAIST_MM"])
            assert f(x["GROSS_M3"]) == pytest.approx(A * (t * math.hypot(go, h) / go + h / 2) / 1000, abs=1e-8)
            flat = sum(a * (i * h + t) for i, a in enumerate(areas)) / 1000
            assert f(x["UPPER_BOUND_M3"]) == pytest.approx(flat, abs=1e-5) and f(x["UPPER_BOUND_M3"]) > f(x["GROSS_M3"])
            assert x["LANE"] == "CONDITIONAL_ESTIMATE_NOT_RELEASED"
            assert 250 < go < 300


# ------------------------------------------------------------------ reinforcement and ownership
def test_reinforcement_and_ownership():
    R_ = rows("09_REINFORCEMENT_OWNERSHIP_AUDIT.csv")
    call = sorted(x["HANDLE"] for x in R_ if x["RECORD"] == "PLAN_CALLOUT")
    with open(S87 / "08_REBAR_ANNOTATION_BINDING.csv", encoding="utf-8", newline="") as fh:
        s87 = sorted(r["HANDLE"] for r in csv.DictReader(fh) if r["TEXT"] == "8%%C16/m")
    assert call == s87 and len(call) == 9
    fam = {x["FAMILY"]: x["STATE"] for x in R_ if x["RECORD"] == "FAMILY"}
    assert fam["8Ø16/m"] == "PARTLY_RELEASED"
    for k in ("6Ø14/m", "6Ø12/m", "Ø12/20cm", "Ø8/15", "1Ø12", "6Ø16/m", "anchorage / development / laps / bends"):
        assert fam[k] == "BLOCKED_UNQUANTIFIED", k
    rel = [f(x["KG"]) for x in R_ if x["RECORD"].startswith("S8_7_RELEASED")]
    assert sum(rel) == pytest.approx(59.020862261, abs=1e-9)
    s7 = next(x for x in R_ if x["RECORD"].startswith("S7_OWNED"))
    assert f(s7["KG"]) == pytest.approx(71.895327413, abs=1e-9)
    sens = [x for x in R_ if x["RECORD"] == "SENSITIVITY_KG"]
    assert all(x["LANE"] in ("RESEARCH_SENSITIVITY_NOT_RELEASED", "BLOCKED_UNQUANTIFIED") for x in sens)
    for x in sens:
        if x["KG"]:
            assert f(x["KG"]) == pytest.approx(f(x["EQUIVALENT_LENGTH_M"]) * 16 ** 2 / 162, abs=1e-8)
    s6 = [x["HANDLE"] for x in R_ if x["RECORD"] == "S6_OWNED"]
    assert len(s6) == len(set(s6)) and "BM-GF_ROOF-B20-BL020-453:b20>v" in s6 and "BM-1F_ROOF-B23-BL009-74B" in s6


def test_conflicts_questions_conservation(s):
    cm = rows("05_STRUCTURAL_ARCHITECTURAL_CONFLICT_MATRIX.csv")
    assert [x["ID"] for x in cm] == [f"CM-{i:02d}" for i in range(1, 16)]
    q = rows("10_ENGINEER_RFI_REGISTER.csv")
    assert [x["QUESTION_ID"] for x in q] == [f"Q-ST7B-{i:02d}" for i in range(1, 15)] and all(x["STATUS"] == "OPEN" for x in q)
    cons = rows("11_CONSERVATION_NO_DOUBLE_COUNT_CHECKS.csv")
    assert len(cons) == 16 and all(x["RESULT"] == "PASS" for x in cons)
    a = s["answers"]
    assert a["A1_28_landing"]["state"] == a["A1_28_B20"]["state"] == "PROVISIONAL_SCENARIO_WITH_CONFLICT"
    assert a["A2_27_winders"]["state"] == "PROVISIONAL_SCENARIO_WITH_CONFLICT" and a["A2_27_B23"]["state"] == "CLEAR"


def test_hygiene():
    m = J(MANIFEST)
    for name in list(m["outputs"]) + [MANIFEST.name]:
        assert not HYG.search((PKG / name).read_text(encoding="utf-8")), name


# ------------------------------------------------------------------ with the private drawings
@needs_inputs
def test_rebuild_byte_identical():
    m = J(MANIFEST)
    before = MANIFEST.read_bytes()
    subprocess.run([sys.executable, "-I", str(PKG / "build_s8_7b.py")], check=True, cwd=ROOT, capture_output=True)
    for name, h in m["outputs"].items():
        assert hashlib.sha256((PKG / name).read_bytes()).hexdigest() == h, name
    assert MANIFEST.read_bytes() == before


@needs_inputs
def test_structural_risers_counted_again_with_raw_ezdxf():
    """the structural sheets read directly: layer-2 tread lines across each column of the main bay, the turn lines
    and the B20 / B23 edge lines (sheet frames from the S1 title inserts)."""
    import ezdxf
    from ezdxf import bbox as BB
    doc = ezdxf.readfile(str(ST))
    msp = doc.modelspace()
    frames = [BB.extents([e]) for e in msp.query('LWPOLYLINE[layer=="DEFPOINTS"]')]
    frames = [(b.extmin.x, b.extmin.y) for b in frames if b.extmax.x - b.extmin.x > 20000 and b.extmax.y - b.extmin.y > 10000]

    def frame_of(name):
        p = list(msp.query(f'INSERT[name=="{name}"]'))[0].dxf.insert
        return max((fx, fy) for fx, fy in frames if fx <= p.x and fy <= p.y)
    for name, west, east, radial, b_lo, b_hi in (("GFRS", 12, 12, 3, 15911.856, 16311.856),
                                                 ("FFRS", 12, 11, 0, 15861.856, 16311.856)):
        fx, fy = frame_of(name)
        L = [((e.dxf.start.x - fx, e.dxf.start.y - fy), (e.dxf.end.x - fx, e.dxf.end.y - fy), e.dxf.layer)
             for e in msp.query("LINE")]

        def across(x0, x1):
            return sorted({round(a[1], 1) for a, b, ly in L if ly == "2" and abs(a[1] - b[1]) < 0.5 and
                           abs(min(a[0], b[0]) - x0) < 5 and abs(max(a[0], b[0]) - x1) < 5 and 15800 < a[1] < 19500})
        assert len(across(17087.904, 18237.904)) == west
        east_lines = across(18437.904, 19587.904)
        assert len(east_lines) == east
        rad = [1 for a, b, ly in L if ly == "2" and all(17040 < p[0] < 18400 and 19450 < p[1] < 20700 for p in (a, b))
               and abs(a[0] - b[0]) > 0.5 and abs(a[1] - b[1]) > 0.5 and math.dist(a, b) > 1000]
        assert len(rad) == radial
        edges = sorted({round(a[1], 3) for a, b, ly in L if ly == "1" and abs(a[1] - b[1]) < 0.5 and
                        min(a[0], b[0]) < 17200 and max(a[0], b[0]) > 19500 and 15800 < a[1] < 16400})
        assert edges == [b_lo, b_hi]
        assert (min(east_lines) < b_hi) == (name == "GFRS")          # only the GF roof sheet's last riser is in the band
