"""S8.7C package: the stair design resolution study (research and design comparison; not approval to change the
drawings). Values are re-derived here by hand or with code independent of the builder; passing tests prove arithmetic
and reading, not engineering approval."""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import re
import subprocess
import sys
import xml.dom.minidom
from pathlib import Path

import pytest

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_stairs_s8_7c"
MANIFEST = PKG / "13_S8_7C_FREEZE_MANIFEST.json"
S87 = ROOT / "research" / "alsenan_stairs_s8_7"
S87B = ROOT / "research" / "alsenan_stairs_s8_7b"
BY_SHA = ROOT / "data/inputs/by_sha256"
ARCH = BY_SHA / "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
ST = BY_SHA / "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
SEC_PDF = BY_SHA / "1e7087d3e61bbb682c9107193c97550a2837e5198bde0ee311319bf7f4a08459.pdf"
HYG = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
needs_inputs = pytest.mark.skipif(not (ARCH.exists() and ST.exists() and SEC_PDF.exists()),
                                  reason="private drawings not present in data/inputs/by_sha256 (never committed)")

Y_TURN, Y_LAND, B20_N, B20_S, GB_N = 19461.856, 19411.856, 16311.856, 15911.856, 15711.856
SENS, COND = "RESEARCH_SENSITIVITY_NOT_RELEASED", "CONDITIONAL_ESTIMATE_NOT_RELEASED"
ALREADY = "ALREADY_OWNED_BY_S8_7 (frozen; not counted again)"
UNRESOLVED = "OWNERSHIP_UNRESOLVED (shown, never in a total)"


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name, pkg=PKG):
    with open(pkg / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def f(v):
    return float(v)


@pytest.fixture(scope="module")
def s():
    return J(PKG / "11_RELEASE_SUMMARY.json")


@pytest.fixture(scope="module")
def gf():
    return {x["SCENARIO"]: x for x in rows("02_GF_1F_27_VS_28_GEOMETRY.csv")}


# ------------------------------------------------------------------ freeze, layering, release
def test_frozen_study_layer_over_unchanged_earlier_stages(s):
    m = J(MANIFEST)
    assert m["state"] == "FROZEN_BEFORE_COMPARISON" and m["references_read"] == [] == s["references_read"]
    DR.verify_frozen(MANIFEST, ROOT)
    assert m["s8_7b_manifest_sha256"] == hashlib.sha256((S87B / "16_S8_7B_FREEZE_MANIFEST.json").read_bytes()).hexdigest()
    assert s["release_delta"] == {"concrete_m3": 0.0, "kg": 0.0} == m["release_delta"]
    s87 = J(S87 / "16_S8_7_SUMMARY.json")["released"]
    assert s["frozen_release_unchanged"] == {"concrete_m3": s87["concrete_m3"], "kg": s87["kg"]}
    assert (s87["concrete_m3"], s87["kg"]) == (0.516582788, 59.020862261)
    assert len(s["frozen_baselines"]) == 28 and {"S7", "S8.7", "S8.7A", "S8.7B", "S8.8"} <= set(s["frozen_baselines"])
    for mp in sorted((ROOT / "research").glob("*/*_MANIFEST.json")):
        if J(mp).get("state") in ("FROZEN_BEFORE_COMPARISON", "DATED_CORRECTION_LAYER"):
            DR.verify_frozen(mp, ROOT)
    assert "not approval" in s["rule"] and "nothing approved, selected or released" in s["rule"]


def test_registry_and_no_benchmark_inputs():
    m = J(MANIFEST)
    assert not [p for p in m["inputs"] if re.search(r"registers_v3b|R9_1|R5_|post_freeze|pre_s8|Quotation|pricing|"
                                                   r"xlsx|alsenan_demo", p, re.I)]
    assert not [p for p in m["code"] if "post_freeze" in p]
    src = (PKG / "build_s8_7c.py").read_text(encoding="utf-8")
    for ref in ("BOQ_LINES_V3B", "STAIR_ARCHITECTURAL_REGISTER", "post_freeze", "02_STRUCTURAL_ELEMENT_CENSUS",
                "03_CONCRETE_COVERAGE", "04_REBAR_COVERAGE", "06_S8_CANDIDATE", "07_INTERFACE_DOUBLE", "registers_v3b"):
        assert ref not in src, ref
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    for p in ("engine/source/stair_fit_checks.py", "research/alsenan_stairs_s8_7c/build_s8_7c.py"):
        assert f'"{p}"' in reg


# ------------------------------------------------------------------ A. GF -> 1F
def test_gf_1f_scenarios_by_hand(gf, s):
    assert set(gf) == {"A-28", "A-28-M", "B-27-S", "B-27-SM", "B-27-P", "B-27-U", "REF-25"}
    for sid, x in gf.items():
        n1, nt, n2 = int(x["LOWER_FLIGHT_RISERS"]), int(x["TURN_RISERS"]), int(x["UPPER_FLIGHT_RISERS"])
        n, g2 = n1 + nt + n2, f(x["UPPER_GOING_MM"])
        h = 4500.0 / n
        assert int(x["TOTAL_RISERS"]) == n and f(x["FINISHED_RISER_MM"]) == pytest.approx(h, abs=1e-8)
        land = 1000.0 + (n1 + nt) * h
        assert f(x["LANDING_LEVEL_M"]) == pytest.approx(land / 1000, abs=1e-9)
        assert f(x["LANDING_MINUS_PRINTED_MM"]) == pytest.approx(land - 3500.0, abs=1e-5)
        assert f(x["FOOT_FIRST_RISER_Y_MM"]) == pytest.approx(Y_TURN - (n1 - 1) * 300.0, abs=1e-3)
        last = Y_LAND - (n2 - 1) * g2
        assert f(x["LAST_UPPER_RISER_Y_MM"]) == pytest.approx(last, abs=1e-3)
        assert f(x["CLEARANCE_TO_B20_MM"]) == pytest.approx(last - B20_N, abs=1e-3)
        assert json.loads(x["TURN_TREAD_LEVELS_M"]) == pytest.approx([(1000 + k * h) / 1000 for k in range(n1, n1 + nt)],
                                                                     abs=5e-4)
        assert f(x["FOOT_TO_GROUND_BEAM_NORTH_FACE_MM"]) == pytest.approx(Y_TURN - (n1 - 1) * 300.0 - GB_N, abs=1e-3)
        assert x["ARRANGEMENT_LANDS_ON_PRINTED"] == str(abs(land - 3500) < 0.5)
    # with equal risers only multiples of 9 reach the 2500 / 4500 point: 27 and 36 between 20 and 40
    assert [n for n in range(20, 41) if (2500 * n) % 4500 == 0] == [27, 36]
    a, b, bm = gf["A-28"], gf["B-27-S"], gf["B-27-SM"]
    assert f(a["LANDING_MINUS_PRINTED_MM"]) == pytest.approx(500 / 7, abs=1e-5)           # 16 x 4500/28 - 2500
    assert a["STATUS"] == "CONFLICTING" and a["COUNT_CAN_REACH_PRINTED_LANDING"] == "False"
    ca = json.loads(a["CONFLICTS"])
    assert any("vs printed +3.50" in c for c in ca) and any("200 mm inside B20" in c for c in ca)
    assert any("600 mm north" in c for c in ca)
    assert f(b["LANDING_MINUS_PRINTED_MM"]) == 0.0 and b["MATCHES_SECTION_A_A"] == "True"
    assert any("200 mm inside B20" in c for c in json.loads(b["CONFLICTS"]))         # one riser fewer: still clashes
    assert json.loads(b["FOOT_DRAWN_BY"]) == ["ARCH-GF", "GBP"] and json.loads(a["FOOT_DRAWN_BY"]) == ["GFRS"]
    assert bm["STATUS"].startswith("GEOMETRICALLY_POSSIBLE_ONLY_WITH_MODIFICATIONS") and f(bm["CLEARANCE_TO_B20_MM"]) == \
        pytest.approx(100, abs=1e-6)
    assert gf["A-28-M"]["STATUS"].startswith("CONFLICTING")
    assert s["most_consistent_gf_1f"]["scenario"] == "B-27-S"
    # the drawn arrangements carry no modification; every proposed one names its changes
    assert a["MODIFICATIONS_NEEDED"] == "" and gf["REF-25"]["MODIFICATIONS_NEEDED"] == ""
    assert all(json.loads(x["MODIFICATIONS_NEEDED"]) for k, x in gf.items() if k not in ("A-28", "REF-25"))
    chb = json.loads(b["CHANGES_TO_RESOLVE"])
    assert not [c for c in chb if c.startswith("section A-A")] and any(c.startswith("B20") for c in chb)
    assert any(c.startswith("section A-A") and "+3.50 -> +3.571" in c for c in json.loads(a["CHANGES_TO_RESOLVE"]))


def test_transition_levels_by_hand(gf):
    T = rows("03_GF_1F_TRANSITION_LEVELS.csv")
    for sid, x in gf.items():
        segs = [t for t in T if t["SCENARIO"] == sid]
        assert [t["SEGMENT"] for t in segs] == ["lower flight", "turn (winders)", "landing (NE quarter)", "upper flight"]
        h = f(x["FINISHED_RISER_MM"])
        z, k = 1.0, 0
        for t in segs:
            r = int(t["RISERS"])
            assert f(t["START_LEVEL_M"]) == pytest.approx(z, abs=1e-9)
            z, k = z + r * h / 1000, k + r
            assert f(t["END_LEVEL_M"]) == pytest.approx(z, abs=1e-9)
            if r:
                assert t["RISER_NUMBERS"] == f"{k - r + 1} - {k}"
        assert z == pytest.approx(5.5, abs=1e-9) and k == int(x["TOTAL_RISERS"])
    b = {t["SEGMENT"]: t for t in T if t["SCENARIO"] == "B-27-S"}
    assert f(b["landing (NE quarter)"]["START_LEVEL_M"]) == 3.5 and b["upper flight"]["RISER_NUMBERS"] == "16 - 27"


def test_b20_interference_comes_from_the_upper_flight(gf):
    avail = Y_LAND - B20_N
    assert avail == pytest.approx(3100.0)
    assert math.floor(avail / 300.0) + 1 == 11                         # 12 risers at 300 cannot fit
    assert 3000.0 / 11 == pytest.approx(272.727, abs=1e-3) and 3100.0 / 11 == pytest.approx(281.818, abs=1e-3)
    for x in gf.values():
        twelve_at_300 = x["UPPER_FLIGHT_RISERS"] == "12" and f(x["UPPER_GOING_MM"]) == 300.0
        assert (f(x["CLEARANCE_TO_B20_MM"]) == pytest.approx(-200.0, abs=1e-6)) == twelve_at_300
    C = rows("04_LANDING_BEAM_CLASH_AUDIT.csv")
    for c in C:
        if c["ITEM"].endswith("upper-flight head / B20"):
            g = gf[c["ITEM"].split()[0]]
            assert f(c["PLAN_CLEARANCE_MM"]) == pytest.approx(f(g["CLEARANCE_TO_B20_MM"]), abs=1e-3)
            if f(c["PLAN_CLEARANCE_MM"]) < 0:
                assert f(c["LOCAL_DROP_OF_B20_TOP_NEEDED_MM"]) == pytest.approx(f(g["FINISHED_RISER_MM"]), abs=1e-3)
                assert c["RESULT"].startswith("CLASH")
    sec = next(c for c in C if c["ITEM"] == "section A-A beam position")
    assert "neither shows nor resolves the clash" in sec["RESULT"] and sec["STATUS"].startswith("SCALED")
    col = next(c for c in C if "column 36B" in c["ITEM"])
    assert f(col["PLAN_CLEARANCE_MM"]) == pytest.approx(-50.0, abs=1e-3)


def test_section_a_a_turn_treads_and_runs(gf):
    E = {r["ID"]: r for r in rows("01_SOURCE_EVIDENCE_REGISTER.csv")}
    dashed = json.loads(E["S-06"]["VALUE"])
    assert len(dashed) == 5
    h27 = 4.5 / 27
    for k, d in zip(range(10, 15), dashed):
        assert abs(d - (1.0 + k * h27)) < 0.006                        # each tread within 6 mm of 27 equal risers
    assert all(abs((b - a) - h27) < 0.006 for a, b in zip(dashed, dashed[1:]))
    # the structural sheet's 28 has four treads in the turn, at other levels
    assert len(json.loads(gf["A-28"]["TURN_TREAD_LEVELS_M"])) == 4
    assert {k for k, x in gf.items() if x["SECTION_TURN_TREADS_MATCH"] == "True"} == {"B-27-S", "B-27-SM"}
    assert E["S-07"]["VALUE"] == "none (flat quarter)"
    assert f(E["S-01"]["VALUE"]) == pytest.approx(1200, abs=15)
    assert f(E["S-02"]["VALUE"]) == pytest.approx(3300, abs=15)
    assert f(E["S-03"]["VALUE"]) == pytest.approx(16111.856, abs=25)  # the 12-riser arrival
    assert f(E["S-04"]["VALUE"]) == pytest.approx(16761.856, abs=50)  # the architectural / ground-beam foot
    assert all(E[k]["STATUS"].startswith("SCALED") for k in ("S-01", "S-02", "S-03", "S-04", "S-05", "S-06"))
    assert E["S-09"]["STATUS"] == "PRINTED_ON_DRAWING" and f(E["S-09"]["VALUE"]) == 3.5


def test_fan_centre_of_the_drawn_radials():
    E = {r["ID"]: r for r in rows("01_SOURCE_EVIDENCE_REGISTER.csv")}
    rad = json.loads(E["G-GFRS-RADIALS"]["VALUE"])
    assert sorted(rad) == ["2F4", "2F5", "2F6"]
    angles = sorted(round(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180, 3) for a, b in rad.values())
    assert angles == [113.982, 135.0, 156.018]
    # pairwise intersections, averaged: independent of the builder's least squares
    pts = []
    for (a1, b1), (a2, b2) in itertools.combinations(rad.values(), 2):
        d1, d2 = (b1[0] - a1[0], b1[1] - a1[1]), (b2[0] - a2[0], b2[1] - a2[1])
        den = d1[0] * d2[1] - d1[1] * d2[0]
        t = ((a2[0] - a1[0]) * d2[1] - (a2[1] - a1[1]) * d2[0]) / den
        pts.append((a1[0] + t * d1[0], a1[1] + t * d1[1]))
    cx, cy = sum(p[0] for p in pts) / 3, sum(p[1] for p in pts) / 3
    fan = json.loads(E["G-GFRS-FAN"]["VALUE"])
    assert math.dist((cx, cy), fan[:2]) < 3.0 and fan[2] < 5.0
    assert 18200 < fan[0] < 18287.904 and Y_TURN < fan[1] < 19600   # at the inner corner of the turn


# ------------------------------------------------------------------ B. 1F -> 2F
def test_1f_2f_by_hand():
    W = {x["CASE"]: x for x in rows("05_1F_2F_WINDER_RECONCILIATION.csv")}
    o = W["OWNER-27"]
    assert f(o["FINISHED_RISER_MM"]) == pytest.approx(4200 / 27, abs=1e-8)
    assert f(o["LANDING_LEVEL_M"]) == pytest.approx((5500 + 16 * 4200 / 27) / 1000, abs=1e-9)
    assert f(o["CLEARANCE_TO_B23_MM"]) == pytest.approx(100, abs=1e-3) and o["STATUS"] == "PROVISIONAL_OWNER_SCENARIO"
    assert f(W["FFRS-24"]["FINISHED_RISER_MM"]) == 175 and f(W["FFRS-24"]["LANDING_LEVEL_M"]) == pytest.approx(7.775)
    sec = W["SECTION-25"]
    assert f(sec["FINISHED_RISER_MM"]) == 168 and f(sec["LANDING_LEVEL_M"]) == pytest.approx(7.684)
    assert f(sec["CLEARANCE_TO_B23_MM"]) == pytest.approx(-200, abs=1e-3)
    assert f(sec["SECTION_SCALED_LANDING_M"]) == pytest.approx(7.684, abs=0.01)
    low, up = math.floor((Y_TURN - 16161.856) / 300 + 1e-9) + 1, math.floor((Y_LAND - 16311.856) / 300 + 1e-9) + 1
    assert (low, up) == (12, 11)
    cap = W["PLAN_CAPACITY"]
    assert json.loads(cap["TOTAL_RISERS"]) == {"flat quarter": low + 1 + up, "4-winder turn": low + 4 + up} == \
        {"flat quarter": 24, "4-winder turn": 27}


# ------------------------------------------------------------------ C. round stair
def test_round_stair_rows():
    R = {x["ID"]: x for x in rows("06_ROUND_STAIR_GEOMETRY_AUDIT.csv")}
    assert sorted(R) == [f"R-{k:02d}" for k in range(1, 13)]
    assert R["R-01"]["STATUS"] == "INFERRED_NOT_PRINTED" and R["R-08"]["STATUS"] == "PRINTED_ON_DRAWING"
    assert R["R-10"]["STATUS"] == "REQUIRES_ENGINEER_CONFIRMATION" and R["R-12"]["VALUE"] == "not applied"
    assert f"+{(1000 + 23 * 4500 / 28) / 1000:.3f}" in R["R-07"]["VALUE"]
    C = rows("04_LANDING_BEAM_CLASH_AUDIT.csv")
    ca = next(c for c in C if "beam CA" in c["ITEM"])
    assert f(ca["HEADROOM_MM"]) == pytest.approx(5500 - 500 - (1000 + 15 * 4500 / 28), abs=0.1)
    assert ca["STATUS"] == "REQUIRES_ENGINEER_CONFIRMATION"


# ------------------------------------------------------------------ E. concrete
def _brute_zone(n, h, g, w, t, s0, s1, m=40000):
    drop = t * math.hypot(g, h) / g
    ds = (s1 - s0) / m
    return sum(((math.floor((s0 + (i + 0.5) * ds) / g) + 1) * h - (h / g * (s0 + (i + 0.5) * ds) - drop)) * ds
               for i in range(m)) * w / 1e9


def test_concrete_by_closed_form_and_brute_force(gf):
    C = rows("07_CONDITIONAL_CONCRETE_COMPARISON.csv")
    assert not [x for x in C if x["LANE"] in ("SOURCE_VERIFIED_RELEASED", "PROJECT_BASIS_QTO")]
    for x in C:
        if x["COMPONENT"] in ("lower flight", "upper flight"):
            n, g, t = int(x["RISERS"]), f(x["GOING_MM"]), f(x["WAIST_MM"])
            h = f(gf[x["SCENARIO"]]["FINISHED_RISER_MM"])
            closed = (n - 1) * g * 1200 * (t * math.hypot(g, h) / g + h / 2) / 1e9
            assert f(x["GROSS_M3"]) == pytest.approx(closed, abs=1e-8)
            assert f(x["WAIST_CONCRETE_M3"]) + f(x["STEP_WEDGES_M3"]) == pytest.approx(f(x["GROSS_M3"]), abs=2e-9)
            assert f(x["GROSS_M3"]) == pytest.approx(f(x["NET_M3"]) + f(x["DEDUCTIONS_M3"]), abs=5e-9)
            if x["COMPONENT"] == "upper flight" and f(gf[x["SCENARIO"]]["CLEARANCE_TO_B20_MM"]) < 0 and t == 160:
                run = (n - 1) * g
                assert f(x["DEDUCTIONS_M3"]) == pytest.approx(_brute_zone(n, h, g, 1200, t, run - 200, run), rel=1e-6)
        if x["COMPONENT"].startswith("landing A1-L1"):
            assert x["LANE"] == ALREADY and f(x["NET_M3"]) == 0
        if x["COMPONENT"].startswith("arrival strip"):
            assert x["LANE"] == UNRESOLVED and x["NET_M3"] == ""
    for sid in gf:
        nets = []
        for t in ("150", "160", "175", "200"):
            part = [x for x in C if x["SCENARIO"] == sid and x["WAIST_MM"] == t]
            tot = next(x for x in part if x["COMPONENT"].startswith("TOTAL"))
            new = [x for x in part if x["LANE"] in (SENS, COND) and not x["COMPONENT"].startswith("TOTAL")]
            assert f(tot["NET_M3"]) == pytest.approx(sum(f(x["NET_M3"]) for x in new), abs=1e-8)
            assert f(tot["GROSS_M3"]) == pytest.approx(sum(f(x["GROSS_M3"]) for x in new), abs=1e-8)
            nets.append(f(tot["NET_M3"]))
        assert nets == sorted(nets)


def test_a_28_reproduces_the_frozen_s8_7b_owner_figures():
    C = rows("07_CONDITIONAL_CONCRETE_COMPARISON.csv")
    B = rows("08_WAIST_THICKNESS_CONCRETE_SENSITIVITY.csv", S87B)
    A6 = rows("06_BEAM_INTERFERENCE_AUDIT.csv", S87B)
    zone28 = json.loads(next(x for x in A6 if x["INTERFACE"] == "A1-F2 head / B20" and
                             x["ARRANGEMENT"].startswith("OWNER-28"))["OVERLAP_ZONE_M3_BY_WAIST"])
    zone_sec = json.loads(next(x for x in A6 if x["INTERFACE"] == "A1-F2 head / B20" and
                               x["ARRANGEMENT"].startswith("section A-A"))["OVERLAP_ZONE_M3_BY_WAIST"])
    for t in ("150", "160", "175", "200"):
        mine = {x["COMPONENT"]: x for x in C if x["SCENARIO"] == "A-28" and x["WAIST_MM"] == t}
        theirs = {x["ELEMENT_ID"]: x for x in B if x["WAIST_MM"] == t and "OWNER-28" in x["STAIR"]}
        assert f(mine["lower flight"]["GROSS_M3"]) == pytest.approx(f(theirs["A1-F1"]["GROSS_M3"]), abs=1e-9)
        assert f(mine["upper flight"]["GROSS_M3"]) == pytest.approx(f(theirs["A1-F2"]["GROSS_M3"]), abs=1e-9)
        assert f(mine["upper flight"]["DEDUCTIONS_M3"]) == pytest.approx(zone28[t], abs=1e-9)
        # the column cut-out: S8.7B intersects the outlines, S8.7C uses the read bbox (same rectangle)
        assert f(mine["lower flight"]["DEDUCTIONS_M3"]) == pytest.approx(f(theirs["A1-F1"]["COLUMN_CUTOUT_M3"]), abs=1e-7)
        # S8.7B publishes its tread areas to 1e-6 m2, so the turn agrees to 1e-6 m3
        assert f(mine["turn (winders)"]["GROSS_M3"]) == pytest.approx(f(theirs["A1-W1"]["GROSS_M3"]), abs=1e-6)
        assert f(mine["turn (winders)"]["UPPER_BOUND_M3"]) == pytest.approx(f(theirs["A1-W1"]["UPPER_BOUND_M3"]), abs=1e-6)
        sec = next(x for x in C if x["SCENARIO"] == "B-27-S" and x["WAIST_MM"] == t and x["COMPONENT"] == "upper flight")
        assert f(sec["DEDUCTIONS_M3"]) == pytest.approx(zone_sec[t], abs=1e-9)


def test_reinforcement_and_ownership(gf):
    B = rows("08_REINFORCEMENT_DOUBLE_COUNT_AUDIT.csv")
    kg16 = 16 ** 2 / 162
    for x in B:
        if x["ITEM"].startswith("8Ø16/m main bottom bars"):
            g = gf[x["SCENARIO"]]
            h = f(g["FINISHED_RISER_MM"])
            n, gg = ((int(g["LOWER_FLIGHT_RISERS"]), 300.0) if "lower" in x["ITEM"] else
                     (int(g["UPPER_FLIGHT_RISERS"]), f(g["UPPER_GOING_MM"])))
            L = 8 * 1.2 * (n - 1) * math.hypot(gg, h) / 1000
            assert f(x["EQUIVALENT_LENGTH_M"]) == pytest.approx(L, abs=1e-8)
            assert f(x["KG"]) == pytest.approx(L * kg16, abs=1e-7) and x["LANE"] == SENS
    pres = {x["ITEM"]: f(x["KG"]) for x in B if x["LANE"] == "PRESERVED"}
    assert sorted(pres.values()) == [59.020862261, 71.895327413, 110.0, 145.2]
    assert len([x for x in B if x["SCENARIO"] == "ALL" and x["LANE"] == "BLOCKED_UNQUANTIFIED"]) == 10
    assert all(x["KG"] == "" for x in B if x["LANE"] == "BLOCKED_UNQUANTIFIED")
    assert {x["SCENARIO"] for x in B if "through the turn" in x["ITEM"]} == set(gf)
    assert not [x for x in B if x["LANE"] in ("SOURCE_VERIFIED_RELEASED", "PROJECT_BASIS_QTO")]


# ------------------------------------------------------------------ RFI, conservation, report, diagrams
def test_rfi_conservation_and_readme(s):
    R = rows("09_PRIORITISED_RFI.csv")
    assert [x["PRIORITY"] for x in R] == ["P1"] * 3 + ["P2"] * 3 + ["P3"] * 2 and {x["STATUS"] for x in R} == {"OPEN"}
    K = rows("10_CONSERVATION_CHECKS.csv")
    assert [x["CHECK_ID"] for x in K] == [f"C{k:02d}" for k in range(1, 16)] and {x["RESULT"] for x in K} == {"PASS"}
    md = (PKG / "00_README.md").read_text(encoding="utf-8")
    for phrase in ("**It is NOT approval to change the drawings.**", "Release delta: 0 m3 concrete, 0 kg reinforcement",
                   "most consistent with the drawings is B-27-S", "Removing one riser does **not** remove the beam",
                   "What remains subject to engineer approval", "not treated as structurally approved",
                   "keeps its own levels", "sensitivity grid only"):
        assert phrase in md, phrase


def test_diagrams_are_schematic_svg():
    for name in ("14_DIAGRAM_GF_1F_PLAN.svg", "15_DIAGRAM_GF_1F_DEVELOPED_SECTION.svg"):
        txt = (PKG / name).read_text(encoding="utf-8")
        dom = xml.dom.minidom.parseString(txt)
        assert dom.documentElement.tagName == "svg" and "<image" not in txt and "base64" not in txt
        assert "B20" in txt and "Not a drawing" in txt and "approved" in txt
    plan = (PKG / "14_DIAGRAM_GF_1F_PLAN.svg").read_text(encoding="utf-8")
    assert plan.count('stroke="#b91c1c" stroke-width="3.0"') == 2 + 1   # one red riser per panel, plus the legend
    assert plan.count('stroke-dasharray="5,3"') == 4 + 1                # the proposed four radials, plus the legend


def test_hygiene():
    m = J(MANIFEST)
    for name in list(m["outputs"]) + [MANIFEST.name]:
        assert not HYG.search((PKG / name).read_text(encoding="utf-8")), name


# ------------------------------------------------------------------ with the private drawings
@needs_inputs
def test_rebuild_byte_identical():
    m = J(MANIFEST)
    before = MANIFEST.read_bytes()
    subprocess.run([sys.executable, "-I", str(PKG / "build_s8_7c.py")], check=True, cwd=ROOT, capture_output=True)
    for name, h in m["outputs"].items():
        assert hashlib.sha256((PKG / name).read_bytes()).hexdigest() == h, name
    assert MANIFEST.read_bytes() == before


@needs_inputs
def test_turn_radials_and_b20_with_raw_ezdxf():
    """the GF roof sheet read directly: the three winder radials (layer 2) and the B20 edges (layer 1); sheet frame
    from the S1 title insert."""
    import ezdxf
    from ezdxf import bbox as BB
    doc = ezdxf.readfile(str(ST))
    msp = doc.modelspace()
    frames = [BB.extents([e]) for e in msp.query('LWPOLYLINE[layer=="DEFPOINTS"]')]
    frames = [(b.extmin.x, b.extmin.y) for b in frames if b.extmax.x - b.extmin.x > 20000 and b.extmax.y - b.extmin.y > 10000]
    p = list(msp.query('INSERT[name=="GFRS"]'))[0].dxf.insert
    fx, fy = max((x, y) for x, y in frames if x <= p.x and y <= p.y)
    L = [((e.dxf.start.x - fx, e.dxf.start.y - fy), (e.dxf.end.x - fx, e.dxf.end.y - fy), e.dxf.layer, e.dxf.handle)
         for e in msp.query("LINE")]
    rad = [(a, b, hd) for a, b, ly, hd in L if ly == "2" and all(17040 < q[0] < 18400 and 19450 < q[1] < 20700
                                                                 for q in (a, b))
           and abs(a[0] - b[0]) > 0.5 and abs(a[1] - b[1]) > 0.5 and math.dist(a, b) > 1000]
    assert sorted(hd for _, _, hd in rad) == ["2F4", "2F5", "2F6"]
    E = {r["ID"]: r for r in rows("01_SOURCE_EVIDENCE_REGISTER.csv")}
    rec = json.loads(E["G-GFRS-RADIALS"]["VALUE"])
    for a, b, hd in rad:
        assert [v for pt in rec[hd] for v in pt] == pytest.approx([a[0], a[1], b[0], b[1]], abs=1e-3)
    edges = sorted({round(a[1], 3) for a, b, ly, _ in L if ly == "1" and abs(a[1] - b[1]) < 0.5 and
                    min(a[0], b[0]) < 17200 and max(a[0], b[0]) > 19500 and 15800 < a[1] < 16400})
    assert edges == [B20_S, B20_N]
