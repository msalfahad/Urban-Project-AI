"""S8.7 (research/alsenan_stairs_s8_7): staircases and landings - population, geometry, concrete and bars.

The checks re-derive the package from its outputs, the frozen stages and, when the private drawings are restored,
the drawings themselves through independent tools (ezdxf directly, shapely):

- every earlier stage still verifies; the package is frozen before any comparison; PRE-S8 is read through column
  whitelists; the one inadvertent exposure of the survey is recorded;
- four physical stair elements (two staircases, two step flights) from five PRE-S8 zones; every tread run assigned;
- the stair zones are tiled exactly; the two ground-level regions are partitioned exactly;
- the S7 stair-adjacent top steel is recomputed run by run;
- every released plate and bar is recomputed by hand; nothing else is released;
- with the drawings: a byte-identical rebuild, and the released outlines, the riser counts in conflict and the
  printed dimensions read again with ezdxf, without the S1 reader or the builder."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_stairs_s8_7"
MANIFEST = PKG / "17_S8_7_FREEZE_MANIFEST.json"
OUTPUTS = ["00_README.md", "01_STAIR_POPULATION_CENSUS.csv", "02_TREAD_RUN_CENSUS.csv",
           "03_ASSEMBLY_FLIGHT_LANDING_CROSSWALK.csv", "04_GROUND_LEVEL_REGION_RECONCILIATION.csv",
           "05_LEVEL_REGISTER.csv", "06_PLAN_AND_INCLINED_GEOMETRY.csv", "07_CONCRETE_QTO.csv",
           "08_REBAR_ANNOTATION_BINDING.csv", "09_REBAR_QTO.csv", "10_OWNERSHIP_AUDIT.csv",
           "11_S7_STAIR_ADJACENT_RECOMPUTE.csv", "12_BLOCKED_AND_CONFLICTS.csv", "13_PRE_S8_CONDITION_RESOLUTION.csv",
           "14_PROVENANCE.jsonl", "15_CONSERVATION_CHECKS.csv", "16_S8_7_SUMMARY.json"]
ARCH = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
ST = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
needs_inputs = pytest.mark.skipif(not (ARCH.exists() and ST.exists()),
                                  reason="private client drawings not restored in data/inputs/by_sha256")
LANES = {"SOURCE_DERIVED_PHYSICAL", "PROJECT_BASIS_QTO", "BLOCKED_UNQUANTIFIED", "SOURCE_CONFLICT", "NOT_IN_SOURCE"}
RELEASED = {"SOURCE_DERIVED_PHYSICAL", "PROJECT_BASIS_QTO"}
HYG = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
UM16 = 16 ** 2 / 162


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name):
    with open(PKG / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def F(v):
    return float(v) if v not in ("", None) else None


@pytest.fixture(scope="module")
def s():
    return J(PKG / "16_S8_7_SUMMARY.json")


# ------------------------------------------------------------------ freeze and blindness
def test_frozen_before_comparison():
    m = J(MANIFEST)
    assert m["round"] == "S8_7" and m["state"] == "FROZEN_BEFORE_COMPARISON" and m["references_read"] == []
    assert set(m["outputs"]) == set(OUTPUTS) and m["baseline"] == "3bdc894"
    assert "CONCRETE_STATES" in m["inadvertent_exposure"]["what"] and m["inadvertent_exposure"]["use"].startswith("none")
    DR.verify_frozen(MANIFEST, ROOT)


def test_every_earlier_stage_still_verifies(s):
    assert len(s["frozen_baselines"]) == 24 and {"S7", "S7A", "PRE-S8", "S8.1A", "S8.6", "S8.6A"} <= set(
        s["frozen_baselines"])
    for mp in sorted((ROOT / "research").glob("*/*_MANIFEST.json")):
        m = J(mp)
        if m.get("state") in ("FROZEN_BEFORE_COMPARISON", "DATED_CORRECTION_LAYER") and mp != MANIFEST:
            DR.verify_frozen(mp, ROOT)
    assert len(s["register_indexes"]) == 4 and s["s8_3_errata_sha256"]


def test_pre_s8_whitelists_and_registry():
    m = J(MANIFEST)
    read = [c for cols in m["pre_s8_columns_read"].values() for c in cols]
    for bad in ("CONCRETE_QUANTITY_STATE", "CONCRETE_STATES", "CONCRETE", "BARS_OWNED", "URBAN_LINES"):
        assert bad not in read
    assert not [c for c in read if c.startswith(("V3B_", "CR_"))]
    assert not [p for p in m["inputs"] if re.search(r"06_S8_CANDIDATE|03_CONCRETE_COVERAGE|04_REBAR_COVERAGE", p)]
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    for p in ("engine/source/stair_geometry.py", "research/alsenan_stairs_s8_7/build_s8_7.py"):
        assert f'"{p}"' in reg


# ------------------------------------------------------------------ population
def test_four_physical_stair_elements_from_five_zones(s):
    pop = s["physical_population"]
    assert pop["staircases_count"] == 2 and pop["step_flights_count"] == 2 and pop["pre_s8_zones"] == 5
    census = rows("01_STAIR_POPULATION_CENSUS.csv")
    top = {r["ELEMENT_ID"]: r for r in census if r["ROW_KIND"] in ("STAIRCASE", "STEP_FLIGHT") and not r["PARENT"]}
    assert set(top) == {"ST-A", "ST-B", "ST-C", "ST-D"}
    assert json.loads(top["ST-A"]["S1_PRE_S8_ZONES"]) == ["SP-GF_ROOF_SLAB-03", "SP-1F_ROOF_SLAB-01"]
    assert json.loads(top["ST-C"]["S1_PRE_S8_ZONES"]) == ["SP-GF_ROOF_SLAB-21", "SP-GF_ROOF_SLAB-28"]
    assert top["ST-D"]["IN_S1_PRE_S8"].startswith("NO (omitted")
    cross = rows("03_ASSEMBLY_FLIGHT_LANDING_CROSSWALK.csv")
    spc = [r for r in cross if r["SOURCE_RECORD"].startswith("SPC-STAIR-")]
    assert Counter(r["ELEMENT"] for r in spc) == {"ST-A": 2, "ST-C": 3}


def test_every_tread_run_is_assigned():
    tr = rows("02_TREAD_RUN_CENSUS.csv")
    assert tr and all(r["ASSIGNED_ELEMENT"] != "NONE" or r["VIEW_ROLE"].startswith("UNEXPLAINED") for r in tr)
    roles = Counter((r["ASSIGNED_ELEMENT"], r["VIEW_ROLE"]) for r in tr)
    assert roles[("A1-F1", "REPEATED_VIEW")] == 1 and roles[("C-F1", "REPEATED_VIEW")] == 1    # GBP copies
    assert {r["ASSIGNED_ELEMENT"] for r in tr if r["SOURCE"] == "ST7757" and r["VIEW"] == "SFRS"} == set()


def test_riser_counts_as_drawn():
    g = {r["ELEMENT_ID"]: r for r in rows("06_PLAN_AND_INCLINED_GEOMETRY.csv")}
    want = {"A1-F1": ("12", "10", "SOURCE_CONFLICT"), "A1-F2": ("12", "11", "SOURCE_CONFLICT"),
            "A1-W1": ("4", "4", "AGREED"), "A2-F1": ("12", "12", "AGREED"), "A2-F2": ("11", "11", "SOURCE_CONFLICT"),
            "A2-W1": ("1", "4", "SOURCE_CONFLICT"), "B-F1": ("4", "4", "AGREED"), "C-F1": ("23", "23", "AGREED"),
            "C-F2": ("5", "5", "AGREED"), "D-F1": ("5", "5", "AGREED")}
    for el, (st, ar, state) in want.items():
        assert (g[el]["RISERS_STRUCTURAL_PLAN"], g[el]["RISERS_ARCH_PLAN"], g[el]["RISER_COUNT_STATE"]) == \
            (st, ar, state), el
    assert g["A1-F2"]["RISERS_SECTION_A_A"] == "12" and g["A2-F2"]["RISERS_SECTION_A_A"] == "12"
    assert F(g["B-F1"]["RISER_HEIGHT_MM"]) == pytest.approx(175.0)
    assert F(g["D-F1"]["RISER_HEIGHT_MM"]) == pytest.approx(170.0)
    assert [el for el, r in g.items() if r["RISER_HEIGHT_MM"]] == ["B-F1", "D-F1"]


def test_levels_bound_as_printed():
    lv = {r["LEVEL_ID"]: r for r in rows("05_LEVEL_REGISTER.csv")}
    assert F(lv["SECTION-AA-HALF_LANDING_GF_1F"]["VALUE_M"]) == 3.5
    assert lv["SECTION-AA-HALF_LANDING_1F_2F"]["STATE"] == "NOT_PRINTED"
    assert lv["P16-TYPICAL-LEVELS"]["STATE"] == "TYPICAL_NOT_PROJECT"
    assert lv["ELEMENT-A1-L1"]["STATE"].startswith("DERIVED_FROM_PRINTED")
    assert lv["ELEMENT-A2-L1"]["STATE"] == "NOT_PRINTED / NOT_PRINTED"
    assert lv["ELEMENT-C-L1"]["STATE"] == "NOT_PRINTED / NOT_PRINTED"


# ------------------------------------------------------------------ zones and ground-level regions
def test_stair_zones_tiled_exactly():
    cross = rows("03_ASSEMBLY_FLIGHT_LANDING_CROSSWALK.csv")
    for z in ("SP-GF_ROOF_SLAB-03", "SP-1F_ROOF_SLAB-01", "SP-GF_ROOF_SLAB-21", "SP-GF_ROOF_SLAB-28"):
        part = [r for r in cross if r["SOURCE_RECORD"] == z]
        assert abs(sum(F(r["AREA_M2"]) for r in part) - F(part[0]["S1_AREA_M2"])) < 1e-6, z
    void = [r for r in cross if r["RELATION"] == "VOID_OPEN_TO_BELOW"]
    assert len(void) == 1 and void[0]["SOURCE_RECORD"] == "SP-GF_ROOF_SLAB-21"


def test_ground_level_regions_partitioned_and_never_double_counted():
    g = rows("04_GROUND_LEVEL_REGION_RECONCILIATION.csv")
    rg = [r for r in g if r["PART_ID"].startswith("RG02")]
    g12 = [r for r in g if r["PART_ID"].startswith("GBP12")]
    assert abs(sum(F(r["AREA_M2"]) for r in rg) - 11.52) < 1e-6
    assert abs(sum(F(r["AREA_M2"]) for r in g12) - 8.37232788) < 1e-6
    assert all(F(r["OVERLAP_WITH_S8_1_FACES_M2"]) == 0 for r in g)
    assert all(r["QUANTIFIED_IN_ANY_STAGE"] == "False" for r in g)
    assert [r["PART_ID"] for r in rg if r["CLASS"] == "B-F1"] == ["RG02-P09"]


# ------------------------------------------------------------------ S7 interface
def test_s7_stair_adjacent_top_steel_recomputed_run_by_run():
    s7 = rows("11_S7_STAIR_ADJACENT_RECOMPUTE.csv")
    assert len(s7) == 75 and all(r["STATE"] == "OWNED_ONCE_BY_S7" for r in s7)
    assert all(F(r["S8_7_TOP_STEEL_AT_THIS_SUPPORT"]) == 0 for r in s7)
    runs = list(csv.DictReader(open(ROOT / "research/alsenan_slab_rebar_s7/04_S7_BAR_RUNS.csv", encoding="utf-8")))
    aud = [a for a in csv.DictReader(open(ROOT / "research/alsenan_slab_rebar_s7a_qa/08_END_CONDITION_AUDIT.csv",
                                          encoding="utf-8")) if "STAIR" in a["UNRESOLVED_REASON"]]
    keys = {(a["STRIP_ID"], a["END"]) for a in aud}
    mine = math.fsum(float(r["KG"]) for r in runs if r["BAR_ROLE"] == "TOP_OVER_SUPPORT_EXTENSION"
                     and (r["STRIP_ID"], "END" if r["END_USED"] == "END" else "START") in keys)
    assert abs(mine - math.fsum(F(r["KG_FROM_BAR_RUNS"]) for r in s7)) < 1e-9
    assert abs(mine - 71.895327413) < 1e-8
    assert {d for r in s7 for d in json.loads(r["DIAMETER_MM"])} == {"10"}


# ------------------------------------------------------------------ quantities
def test_concrete_released_only_where_outline_level_and_thickness_hold(s):
    c = {r["ELEMENT_ID"]: r for r in rows("07_CONCRETE_QTO.csv")}
    assert all(r["LANE"] in LANES for r in c.values())
    rel = {el for el, r in c.items() if r["LANE"] in RELEASED}
    assert rel == {"A1-L1", "A2-T1", "C-T1"}
    assert not [el for el, r in c.items() if r["KIND"].startswith(("FLIGHT", "WINDER", "STEP")) and r["LANE"] in RELEASED]
    assert F(c["A1-L1"]["CONCRETE_M3"]) == pytest.approx(1.2 * 1.2 * 0.16)
    assert F(c["A2-T1"]["CONCRETE_M3"]) == pytest.approx(1.2 * 0.1 * 0.16)
    t1 = [(26707.904, 11411.856), (27907.904, 11411.856), (27660.991, 12961.856), (26707.904, 12961.856)]
    area = abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(t1, t1[1:] + t1[:1]))) / 2 / 1e6
    assert F(c["C-T1"]["CONCRETE_M3"]) == pytest.approx(area * 0.16, abs=1e-6)
    assert s["released"]["concrete_m3"] == pytest.approx(math.fsum(F(c[e]["CONCRETE_M3"]) for e in rel), abs=1e-9)
    for el in ("A2-L1", "C-L1"):
        assert c[el]["LANE"] == "BLOCKED_UNQUANTIFIED" and "level" in c[el]["REASON"]


def test_bars_released_by_hand(s):
    b = rows("09_REBAR_QTO.csv")
    rel = [r for r in b if r["QUANTITY_STATE"] in RELEASED]
    c = {r["ELEMENT_ID"]: F(r["PLAN_AREA_M2"]) for r in rows("07_CONCRETE_QTO.csv")}
    assert sorted((r["FLIGHT_OR_LANDING_ID"], r["PHYSICAL_BAR_ROLE"]) for r in rel) == [
        ("A1-L1", "LANDING_BOTTOM_LONGITUDINAL"), ("A1-L1", "LANDING_BOTTOM_TRANSVERSE"),
        ("A2-T1", "LANDING_BOTTOM_LONGITUDINAL"), ("C-T1", "LANDING_BOTTOM_LONGITUDINAL")]
    for r in rel:
        assert r["BAR_DIAMETER_MM"] == "16" and r["SPACING_OR_COUNT"] == "8/m"
        assert F(r["KG"]) == pytest.approx(8 * c[r["FLIGHT_OR_LANDING_ID"]] * UM16, abs=1e-8)
    assert s["released"]["kg"] == pytest.approx(math.fsum(F(r["KG"]) for r in rel), abs=1e-9)
    assert s["released"]["kg_by_diameter"] == {"16": s["released"]["kg"]}
    assert not [r for r in rel if "p.16" in r["SOURCE_HANDLE"]]
    assert not [r for r in b if r["PHYSICAL_BAR_ROLE"] == "ANCHORAGE_AND_CONTINUATION" and r["QUANTITY_STATE"] in RELEASED]


def test_p16_callouts_each_given_a_role():
    bnd = rows("08_REBAR_ANNOTATION_BINDING.csv")
    p16 = [r for r in bnd if r["BINDING_ID"].startswith("P16-")]
    assert len(p16) == 10 and all(r["PHYSICAL_BAR_ROLE"] for r in p16)
    assert {r["TEXT"] for r in p16} >= {"8Ø16/m", "6Ø14/m", "6Ø12/m", "Ø12/20cm", "Ø8/15"}
    assert [r["TEXT"] for r in p16 if r["APPLICABILITY"] != "TYPICAL_ONLY"] == ["8Ø16/m"]
    plan = [r for r in bnd if r["APPLICABILITY"] == "PLAN_CALLOUT"]
    assert len(plan) == 9 and all(r["TEXT"].upper() == "8%%C16/M" for r in plan)


def test_ownership_and_conservation(s):
    own = rows("10_OWNERSHIP_AUDIT.csv")
    assert all(F(r["QUANTITY_MOVED"]) == 0 for r in own)
    assert all(v == "PASS" for v in s["conservation"].values()) and len(s["conservation"]) == 15
    q = {r["ITEM"] for r in rows("12_BLOCKED_AND_CONFLICTS.csv") if r["STATE"] == "QUESTION_FOR_THE_ENGINEER"}
    assert q == set(s["questions"]) and len(q) == 12


def test_hygiene():
    for name in OUTPUTS:
        assert not HYG.search((PKG / name).read_text(encoding="utf-8")), name


# ------------------------------------------------------------------ with the private drawings
@needs_inputs
def test_rebuild_byte_identical():
    m = J(MANIFEST)
    subprocess.run([sys.executable, "-I", str(PKG / "build_s8_7.py")], check=True, cwd=ROOT, capture_output=True)
    for o, h in m["outputs"].items():
        assert hashlib.sha256((PKG / o).read_bytes()).hexdigest() == h, o


@needs_inputs
def test_released_outlines_and_conflicts_read_again_with_ezdxf():
    """the structural DXF read directly (global coordinates, no S1 reader): the released plates' edges; the
    architectural DXF read directly: the printed run and landing dimensions and the riser lines per column."""
    import ezdxf
    from shapely.geometry import Polygon
    st = ezdxf.readfile(str(ST))
    db = st.entitydb

    def pts(h):
        e = db[h]
        return (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)
    # the GFRS sheet: lines 279 (bay north edge), 25A (central wall east face), 25B (last riser of the upper flight)
    (n0, n1), (w0, w1), (r0, r1) = pts("279"), pts("25A"), pts("25B")
    assert abs(n0[0] - w0[0] - 1200) < 0.01 and abs(n0[1] - r0[1] - 1200) < 0.01
    # top arrival of the light-well stair: void edge 2CF, east edge 289, north edge 2CE, last riser 315
    (v0, v1), (e0, e1), (k0, k1), (s0, s1) = pts("2CF"), pts("289"), pts("2CE"), pts("315")
    poly = Polygon([(v0[0], s0[1]), (e1[0], s0[1]), (k1[0], k1[1]), (v0[0], k0[1])])
    assert abs(e1[1] - s0[1]) < 0.01                                  # the east edge ends at the last riser
    c = {r["ELEMENT_ID"]: F(r["PLAN_AREA_M2"]) for r in rows("07_CONCRETE_QTO.csv")}
    assert abs(poly.area / 1e6 - c["C-T1"]) < 1e-6
    # the architectural plans: printed '3300' and '1200' on 1F and 2F; riser pairs per column on GF and 1F
    ar = ezdxf.readfile(str(ARCH)).modelspace()
    dims = Counter(round(float(d.get_measurement())) for d in ar if d.dxftype() == "DIMENSION")
    assert dims[3300] >= 2 and dims[1200] >= 6 and dims[2500] >= 3
    T = {r["FLOOR"]: (float(r["TX_MM"]), float(r["TY_MM"])) for r in
         csv.DictReader(open(ROOT / "research/alsenan_lintels_s8_6/03_ARCH_STRUCTURAL_REGISTRATION.csv",
                             encoding="utf-8")) if r["RECORD"] == "FLOOR"}

    def positions(fl, x0, x1, layers=("2", "5"), hidden=None):
        tx, ty = T[fl]
        ys = []
        for e in ar:
            if e.dxftype() != "LINE" or e.dxf.layer not in layers:
                continue
            a, b = (e.dxf.start.x + tx, e.dxf.start.y + ty), (e.dxf.end.x + tx, e.dxf.end.y + ty)
            if abs(a[1] - b[1]) < 0.5 and 1100 < abs(a[0] - b[0]) < 1200 and x0 <= min(a[0], b[0]) and \
                    max(a[0], b[0]) <= x1 and 15500 < a[1] < 19500:
                ys.append(a[1])
        out = []
        for y in sorted(ys):
            if out and y - out[-1][-1] <= 60:
                out[-1].append(y)
            else:
                out.append([y])
        return len(out)
    assert positions("1F", 17000, 18300) == 12 and positions("1F", 18400, 19600) == 11
    assert positions("GF", 17000, 18300) == 10                                   # vs 12 on the structural sheet
    assert positions("GF", 18400, 19600, layers=("2",)) == 11                    # upper flight (hidden lines)
