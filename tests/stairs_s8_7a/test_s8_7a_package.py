"""S8.7A (research/alsenan_stairs_s8_7a): stair riser, finishing and structural-geometry correction audit.

The checks re-derive the layer from its outputs, the frozen S8.7 package and, when the private drawings are restored,
the architectural DXF itself with ezdxf (no builder code):

- S8.7 is unchanged and its release stands; the layer is dated, frozen before any comparison and releases nothing;
- the riser counts per view, flight and turn; the owner scenarios against them;
- every riser schedule closes; the first / last concrete risers follow the closed form;
- scenario concrete and bars recomputed by hand; S8.7's released quantities reproduced exactly;
- with the drawings: a byte-identical rebuild, and the architectural riser pairs, winder lines and closing risers
  counted again with ezdxf."""

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
PKG = ROOT / "research" / "alsenan_stairs_s8_7a"
S87 = ROOT / "research" / "alsenan_stairs_s8_7"
MANIFEST = PKG / "15_S8_7A_CORRECTION_MANIFEST.json"
OUTPUTS = ["00_README.md", "01_RISER_COUNT_COMPARISON.csv", "02_RISER_LINE_EVIDENCE.csv",
           "03_RISER_ELEVATION_SCHEDULE.csv", "04_FIRST_LAST_RISER_FINISH_ADJUSTMENT.csv",
           "05_WAIST_AND_LANDING_GEOMETRY.csv", "06_CONCRETE_QUANTITY_SCENARIOS.csv",
           "07_REINFORCEMENT_QUANTITY_SCENARIOS.csv", "08_BEAM_AND_S6_S7_OWNERSHIP_RECONCILIATION.csv",
           "09_SOURCE_CONFLICT_REGISTER.csv", "10_ENGINEER_RFI_LIST.csv", "11_S8_7_REPRODUCTION_AND_CORRECTIONS.csv",
           "12_RELEASE_SUMMARY.json", "13_PROVENANCE.jsonl", "14_CONSERVATION_CHECKS.csv"]
ARCH = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
ST = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
needs_inputs = pytest.mark.skipif(not (ARCH.exists() and ST.exists()),
                                  reason="private client drawings not restored in data/inputs/by_sha256")
RELEASED = {"SOURCE_VERIFIED", "PROJECT_BASIS_QTO"}
HYG = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
UM16 = 16 ** 2 / 162


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name, base=PKG):
    with open(base / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def F(v):
    return float(v) if v not in ("", None) else None


@pytest.fixture(scope="module")
def s():
    return J(PKG / "12_RELEASE_SUMMARY.json")


# ------------------------------------------------------------------ correction layer
def test_dated_correction_layer_over_an_unchanged_s8_7(s):
    m = J(MANIFEST)
    assert m["round"] == "S8_7A" and m["state"] == "DATED_CORRECTION_LAYER" and m["references_read"] == []
    assert set(m["outputs"]) == set(OUTPUTS) and m["corrects"].startswith("research/alsenan_stairs_s8_7")
    assert m["s8_7_manifest_sha256"] == hashlib.sha256((S87 / "17_S8_7_FREEZE_MANIFEST.json").read_bytes()).hexdigest()
    DR.verify_frozen(MANIFEST, ROOT)
    DR.verify_frozen(S87 / "17_S8_7_FREEZE_MANIFEST.json", ROOT)
    s87 = J(S87 / "16_S8_7_SUMMARY.json")["released"]
    assert s["released"]["concrete_m3"] == s87["concrete_m3"] and s["released"]["kg"] == s87["kg"]
    assert s["released"]["new_release_by_s8_7a"] == {"concrete_m3": 0.0, "kg": 0.0}


def test_every_earlier_stage_still_verifies(s):
    assert len(s["frozen_baselines"]) == 26 and {"S7", "S8.6A", "S8.7", "S8.8"} <= set(s["frozen_baselines"])
    for mp in sorted((ROOT / "research").glob("*/*_MANIFEST.json")):
        m = J(mp)
        if m.get("state") in ("FROZEN_BEFORE_COMPARISON", "DATED_CORRECTION_LAYER"):
            DR.verify_frozen(mp, ROOT)


def test_registry_and_no_benchmark_inputs():
    m = J(MANIFEST)
    assert not [p for p in m["inputs"] if re.search(r"registers_v3b|R9_1|R5_|post_freeze|06_S8_CANDIDATE|"
                                                    r"03_CONCRETE_COVERAGE|04_REBAR_COVERAGE|Quotation|pricing", p)]
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    for p in ("engine/source/stair_riser_schedule.py", "research/alsenan_stairs_s8_7a/build_s8_7a.py"):
        assert f'"{p}"' in reg


# ------------------------------------------------------------------ counts
def test_riser_counts_per_view():
    c = {(r["STOREY_RUN"], r["VIEW"]): r for r in rows("01_RISER_COUNT_COMPARISON.csv")
         if r["KIND"].startswith("DRAWN_COUNT") and r["VIEW"] != "SECTION A-A"}
    t = lambda k: (int(c[k]["FLIGHT_1_RISERS"]), int(c[k]["TURN_RISERS"] or 0), int(c[k]["FLIGHT_2_RISERS"]),  # noqa
                   int(c[k]["TOTAL_RISERS"]))
    assert t(("A1", "GFRS")) == (12, 4, 12, 28) and t(("A1", "ARCH-GF")) == (10, 4, 11, 25)
    assert t(("A2", "ARCH-1F")) == (12, 4, 11, 27) and t(("A2", "FFRS")) == (12, 1, 11, 24)
    assert t(("A2", "ARCH-2F")) == (12, 1, 11, 24)
    assert int(c[("A1", "GFRS")]["TURN_RADIAL"]) == 3 and int(c[("A2", "FFRS")]["TURN_RADIAL"]) == 0
    assert int(c[("C", "GFRS")]["TOTAL_RISERS"]) == 28 == int(c[("C", "ARCH-1F")]["TOTAL_RISERS"])
    assert int(c[("B", "GBP")]["TOTAL_RISERS"]) == 4 and int(c[("D", "GBP")]["TOTAL_RISERS"]) == 5
    sec = [r for r in rows("01_RISER_COUNT_COMPARISON.csv") if r["VIEW"] == "SECTION A-A"]
    assert [int(r["FLIGHT_2_RISERS"]) for r in sec] == [12, 12]


def test_owner_scenarios_and_the_preferred_range(s):
    o = {(r["STOREY_RUN"], r["SOURCE"]): r for r in rows("01_RISER_COUNT_COMPARISON.csv")}
    for run, sc, n, rise in (("A1", "A", 28, 4500), ("A1", "B", 29, 4500), ("A2", "A", 27, 4200), ("A2", "B", 26, 4200)):
        r = o[(run, f"OWNER SCENARIO {sc}")]
        assert int(r["TOTAL_RISERS"]) == n and abs(F(r["UNIFORM_RISER_MM"]) - rise / n) < 1e-6
        assert r["IN_OWNER_RANGE_150_160"] == str(150 <= rise / n <= 160)
    assert json.loads(o[("A1", "counts in the owner range (150 - 160 mm)")]["TOTAL_RISERS"]) == [29, 30]
    assert json.loads(o[("A2", "counts in the owner range (150 - 160 mm)")]["TOTAL_RISERS"]) == [27, 28]
    p = s["proposed_for_confirmation"]
    assert p["A1"]["risers"] == 28 and p["A2"]["risers"] == 27 and p["A1"]["state"] == "SOURCE_CONFLICT"


# ------------------------------------------------------------------ schedules and finishes
def test_riser_schedules_close_and_are_uniform():
    sch = rows("03_RISER_ELEVATION_SCHEDULE.csv")
    by = {}
    for r in sch:
        by.setdefault(r["SCENARIO"], []).append(r)
    tops = {"A1": 5.5, "A2": 9.7, "C": 5.5}
    for sid, rs in by.items():
        h = {F(r["FINISHED_RISER_MM"]) for r in rs}
        assert len(h) == 1
        assert abs(F(rs[-1]["FINISHED_LEVEL_AFTER_M"]) - tops[sid.split("-")[0]]) < 1e-6
        assert [int(r["RISER"]) for r in rs] == list(range(1, len(rs) + 1))
    a = by["A1-OWNER_A-28"]
    assert a[15]["LANDING_AFTER"] == "A1-L1" and abs(F(a[15]["FINISHED_LEVEL_AFTER_M"]) - (1 + 16 * 4.5 / 28)) < 1e-6


def test_first_last_risers_by_hand():
    for r in rows("04_FIRST_LAST_RISER_FINISH_ADJUSTMENT.csv"):
        if r["SCENARIO"] == "GENERAL":
            assert "h + f_b - s" in r["FORMULA"]
            continue
        h, s_ = F(r["FINISHED_RISER_MM"]), F(r["STAIR_FINISH_MM"])
        if r["STATE"] == "NOT_SUPPORTED":
            assert abs(F(r["REQUIRED_FLOOR_BUILD_UP_BOTTOM_MM"]) - (200 - h + s_)) < 1e-6
            assert abs(F(r["REQUIRED_FLOOR_BUILD_UP_TOP_MM"]) - (h + s_ - 100)) < 1e-6
            continue
        f = F(r["FLOOR_BUILD_UP_MM"])
        assert abs(F(r["FIRST_CONCRETE_RISER_MM"]) - (h + f - s_)) < 1e-6
        assert abs(F(r["LAST_CONCRETE_RISER_MM"]) - (h - f + s_)) < 1e-6


# ------------------------------------------------------------------ quantities
def test_scenario_concrete_by_hand_and_nothing_released():
    c = rows("06_CONCRETE_QUANTITY_SCENARIOS.csv")
    assert not [r for r in c if r["LANE"] in RELEASED]
    f1 = next(r for r in c if r["SCENARIO"] == "A1-OWNER_A-28" and r["ELEMENT_ID"] == "A1-F1")
    n, h, g, w, t = 12, 4500 / 28, 300.0, 1200.0, 160.0
    cos = g / math.hypot(g, h)
    v = (n - 1) * g * w * (t / cos + h / 2) / 1e9
    assert abs(F(f1["CONCRETE_M3"]) - v) < 1e-9
    w1 = next(r for r in c if r["SCENARIO"] == "A1-OWNER_A-28" and r["ELEMENT_ID"] == "A1-W1")
    gw = math.pi / 2 * 600 / 4
    assert abs(F(w1["CONCRETE_M3"]) - 1.5 * (t / (gw / math.hypot(gw, h)) + h / 2) / 1000) < 1e-9
    plates = [r for r in c if r["ALREADY_RELEASED_BY_S8_7"] == "True"]
    assert {r["ELEMENT_ID"] for r in plates} == {"A1-L1", "A2-T1", "C-T1"}
    for sid in {r["SCENARIO"] for r in c if r["ELEMENT_ID"].startswith("TOTAL (whole")}:
        whole = next(F(r["CONCRETE_M3"]) for r in c if r["SCENARIO"] == sid and r["ELEMENT_ID"].startswith("TOTAL (w"))
        unrel = next(F(r["CONCRETE_M3"]) for r in c if r["SCENARIO"] == sid and r["ELEMENT_ID"].startswith("TOTAL NOT"))
        parts = [F(r["CONCRETE_M3"]) for r in c if r["SCENARIO"] == sid and not r["ELEMENT_ID"].startswith("TOTAL")
                 and r["CONCRETE_M3"]]
        assert abs(math.fsum(parts) - whole) < 1e-6 and unrel <= whole
    assert not [r for r in c if "allocation not drawn" in r["ELEMENT_ID"] and r["CONCRETE_M3"]]


def test_bars_by_hand_and_typical_families_blocked():
    b = rows("07_REINFORCEMENT_QUANTITY_SCENARIOS.csv")
    fam = {r["FAMILY"]: r for r in b if r["RECORD"] == "FAMILY"}
    assert fam["8Ø16/m"]["ASSIGNMENT"].startswith("EXPLICIT")
    for k in ("6Ø14/m", "6Ø12/m", "Ø12/20cm", "Ø8/15cm", "1Ø12", "anchorage / development / laps / bends"):
        assert fam[k]["STATE"] == "BLOCKED_UNQUANTIFIED", k
    c = {(r["SCENARIO"], r["ELEMENT_ID"]): r for r in rows("06_CONCRETE_QUANTITY_SCENARIOS.csv")}
    for r in b:
        if r["RECORD"] == "SCENARIO_KG" and r["KG"]:
            L = F(c[(r["SCENARIO"], r["ELEMENT_ID"])]["INCLINED_LENGTH_MM"])
            w = F(c[(r["SCENARIO"], r["ELEMENT_ID"])]["WIDTH_MM"])
            assert abs(F(r["KG"]) - 8 * w / 1000 * L / 1000 * UM16) < 1e-8
            assert r["LANE"] not in RELEASED


def test_s8_7_release_reproduced_and_corrections_recorded():
    rp = rows("11_S8_7_REPRODUCTION_AND_CORRECTIONS.csv")
    nums = [r for r in rp if r["AGREES"]]
    assert nums and all(r["AGREES"] == "True" for r in nums)
    tot = {r["ITEM"]: r for r in rp}
    assert F(tot["released concrete total"]["S8_7A_VALUE"]) == 0.516582788
    assert F(tot["released Ø16 total"]["S8_7A_VALUE"]) == 59.020862261
    assert {r["CORRECTION_ID"] for r in rp if r["CORRECTION_ID"]} == {f"CR-0{i}" for i in range(1, 7)}


def test_head_beams_conflicts_questions_images(s):
    hb = [r for r in rows("08_BEAM_AND_S6_S7_OWNERSHIP_RECONCILIATION.csv") if r["ROLE"].startswith("HEAD BEAM")]
    inside = {r["ROLE"]: r["LAST_RISER_INSIDE_BEAM_BAND"] for r in hb}
    assert inside == {"HEAD BEAM: last riser of A1-F2 on GFRS at y 16111.856": "True",
                      "HEAD BEAM: last riser of A1-F2 on ARCH-GF at y 16411.856": "False",
                      "HEAD BEAM: last riser of A2-F2 on FFRS at y 16411.856": "False",
                      "HEAD BEAM: last riser of A2-F2 on ARCH-1F at y 16411.856": "False"}
    cf = {r["ID"]: r for r in rows("09_SOURCE_CONFLICT_REGISTER.csv")}
    assert {f"SC-{i:02d}" for i in range(1, 13)} == set(cf) and cf["SC-12"]["STATE"] == "NOT_A_CONFLICT"
    q = {r["QUESTION_ID"] for r in rows("10_ENGINEER_RFI_LIST.csv")}
    assert q == set(s["questions"]) and len(q) == 11
    prov = [json.loads(x) for x in (PKG / "13_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len([p for p in prov if p["record"].startswith("OWNER_IMAGE:")]) == 7
    assert all(v == "PASS" for v in s["conservation"].values()) and len(s["conservation"]) == 10


def test_hygiene():
    for name in OUTPUTS + [MANIFEST.name]:
        assert not HYG.search((PKG / name).read_text(encoding="utf-8")), name


# ------------------------------------------------------------------ with the private drawings
@needs_inputs
def test_rebuild_byte_identical():
    m = J(MANIFEST)
    subprocess.run([sys.executable, "-I", str(PKG / "build_s8_7a.py")], check=True, cwd=ROOT, capture_output=True)
    for o, h in m["outputs"].items():
        assert hashlib.sha256((PKG / o).read_bytes()).hexdigest() == h, o


@needs_inputs
def test_architectural_risers_counted_again_with_ezdxf():
    """the architectural DXF read directly: per plan, the tread lines of each column paired within 60 mm, the radial
    winder lines of the NW quarter and the closing riser."""
    import ezdxf
    T = {r["FLOOR"]: (float(r["TX_MM"]), float(r["TY_MM"])) for r in
         csv.DictReader(open(ROOT / "research/alsenan_lintels_s8_6/03_ARCH_STRUCTURAL_REGISTRATION.csv",
                             encoding="utf-8")) if r["RECORD"] == "FLOOR"}
    msp = ezdxf.readfile(str(ARCH)).modelspace()
    lines = [(e.dxf.layer, e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y) for e in msp
             if e.dxftype() == "LINE" and e.dxf.layer in ("2", "5")]

    def per_floor(fl):
        tx, ty = T[fl]
        return [(L, a + tx, b + ty, c + tx, d + ty) for L, a, b, c, d in lines]

    def column(ls, x0, x1, layers=("2", "5")):
        ys = sorted(b for L, a, b, c, d in ls if L in layers and abs(b - d) < 0.5 and abs(min(a, c) - x0) < 5
                    and abs(max(a, c) - x1) < 5 and 15800 < b < 19500)
        groups = []
        for y in ys:
            if groups and y - groups[-1][-1] <= 60:
                groups[-1].append(y)
            else:
                groups.append([y])
        return groups

    def turn(ls):
        rad = set()
        for L, a, b, c, d in ls:
            if all(17057 <= x <= 18298 for x in (a, c)) and all(19451 <= y <= 20662 for y in (b, d)):
                ang = math.degrees(math.atan2(d - b, c - a)) % 180
                if (5 < ang < 85 or 95 < ang < 175) and math.hypot(c - a, d - b) > 1000:
                    rad.add(round(ang / 3))
        closing = {round(a) for L, a, b, c, d in ls if abs(a - c) < 0.5 and 18327 <= a <= 18393
                   and abs(min(b, d) - 19461.856) < 5 and abs(max(b, d) - 20611.856) < 5}
        return len(rad), len(closing)
    gf, f1, f2 = per_floor("GF"), per_floor("1F"), per_floor("2F")
    west, east = (17087.904, 18237.904), (18437.904, 19587.904)
    assert len(column(f1, *west)) == 12 and all(len(g) == 2 for g in column(f1, *west))
    assert len(column(f1, *east)) == 11 and turn(f1)[0] == 3 and turn(f1)[1] >= 1
    assert len(column(f2, *west)) == 12 and len(column(f2, *east)) == 11 and turn(f2)[0] == 0
    g = column(gf, *west)
    assert len(g) == 10 and abs(g[0][-1] - 16761.856) < 1                       # first riser face, 600 mm north
    assert len(column(gf, *east, layers=("2",))) == 11 and turn(gf)[0] == 3
    assert len(column(gf, *east, layers=("5",))) == 4                          # the lobby steps below
