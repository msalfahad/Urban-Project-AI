"""S8.8 (research/alsenan_lift_s8_8): lift pit, shaft walls, foundation and intermediate tie beam.

The checks re-derive the package from its outputs, the frozen stages and, when the private drawings are restored,
the drawings themselves through independent tools (ezdxf directly, shapely):

- every earlier stage still verifies; the package is frozen before any comparison; PRE-S8 is read through column
  whitelists;
- one physical shaft from every view; the pool outline is not a lift;
- the wall ring, the column cut-outs and the net wall pieces close exactly; the 3.24 m2 opening is the pit's inside
  area; the S8.1A cells equal the pieces;
- the FF footing, its bars and the column starters stay with their owners and are not re-counted;
- nothing is released; every conditional coefficient is recomputed by hand;
- P8-N19 is evaluated per storey under each measure; the S6 beams on the shaft are recounted from S6;
- with the drawings: a byte-identical rebuild, and the outlines, columns, footing, schedule row, printed dimensions
  and door jambs read again with ezdxf, without the S1 reader or the builder."""

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
PKG = ROOT / "research" / "alsenan_lift_s8_8"
MANIFEST = PKG / "18_S8_8_FREEZE_MANIFEST.json"
OUTPUTS = ["00_README.md", "01_SOURCE_CENSUS.csv", "02_LIFT_POPULATION.csv", "03_REPRESENTATION_CROSSWALK.csv",
           "04_FOUNDATION_OWNERSHIP_AUDIT.csv", "05_PIT_FOOTPRINT_AND_DEPTH_EVIDENCE.csv",
           "06_WALL_GEOMETRY_AND_CONCRETE_QTO.csv", "07_REBAR_CALLOUT_REGISTER.csv", "08_REBAR_QTO.csv",
           "09_TIE_BEAM_TRIGGER_AND_OWNERSHIP.csv", "10_LIFT_OPENING_RECONCILIATION.csv",
           "11_OVERLAP_AND_DOUBLE_COUNT_CHECKS.csv", "12_OWNERSHIP_AUDIT.csv", "13_BLOCKED_AND_CONFLICTS.csv",
           "14_RFI_QUESTIONS.csv", "15_PROVENANCE.jsonl", "16_CONSERVATION_CHECKS.csv", "17_S8_8_SUMMARY.json"]
ARCH = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
ST = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
needs_inputs = pytest.mark.skipif(not (ARCH.exists() and ST.exists()),
                                  reason="private client drawings not restored in data/inputs/by_sha256")
RELEASED = {"SOURCE_DERIVED_PHYSICAL", "PROJECT_BASIS_QTO"}
SIX = {"ALREADY_OWNED_AND_MEASURED", "OWNED_BUT_UNMEASURED", "NEW_SOURCE_DERIVED", "NEW_PROJECT_BASIS_QTO",
       "BLOCKED_UNQUANTIFIED", "SOURCE_CONFLICT"}
HYG = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name, base=PKG):
    with open(base / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def F(v):
    return float(v) if v not in ("", None) else None


@pytest.fixture(scope="module")
def s():
    return J(PKG / "17_S8_8_SUMMARY.json")


# ------------------------------------------------------------------ freeze and blindness
def test_frozen_before_comparison():
    m = J(MANIFEST)
    assert m["round"] == "S8_8" and m["state"] == "FROZEN_BEFORE_COMPARISON" and m["references_read"] == []
    assert set(m["outputs"]) == set(OUTPUTS) and m["baseline"] == "dc2d778"
    DR.verify_frozen(MANIFEST, ROOT)


def test_every_earlier_stage_still_verifies(s):
    assert len(s["frozen_baselines"]) == 25 and {"S4", "S4.1", "S6", "S7", "PRE-S8", "S8.1A", "S8.6", "S8.6A",
                                                 "S8.7"} <= set(s["frozen_baselines"])
    for mp in sorted((ROOT / "research").glob("*/*_MANIFEST.json")):
        m = J(mp)
        if m.get("state") in ("FROZEN_BEFORE_COMPARISON", "DATED_CORRECTION_LAYER") and mp != MANIFEST:
            DR.verify_frozen(mp, ROOT)
    assert len(s["register_indexes"]) == 4 and s["s8_3_errata_sha256"]


def test_pre_s8_whitelists_registry_and_no_benchmark_inputs():
    m = J(MANIFEST)
    read = [c for cols in m["pre_s8_columns_read"].values() for c in cols]
    for bad in ("CONCRETE_QUANTITY_STATE", "CONCRETE_STATES", "CONCRETE", "BARS_OWNED", "URBAN_LINES"):
        assert bad not in read
    assert not [c for c in read if c.startswith(("V3B_", "CR_"))]
    assert not [p for p in m["inputs"] if re.search(r"06_S8_CANDIDATE|03_CONCRETE_COVERAGE|04_REBAR_COVERAGE|"
                                                    r"registers_v3b|R9_1|R5_|post_freeze", p)]
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    for p in ("engine/source/shaft_geometry.py", "research/alsenan_lift_s8_8/build_s8_8.py"):
        assert f'"{p}"' in reg


# ------------------------------------------------------------------ population
def test_one_physical_shaft(s):
    rep = rows("03_REPRESENTATION_CROSSWALK.csv")
    shafts = [r for r in rep if r["STATE"] == "ONE_PHYSICAL_SHAFT"]
    assert len(shafts) == 1 and s["physical_population"]["lift_shafts"] == 1
    assert json.loads(shafts[0]["VIEWS"]) == ["FP", "GBP", "GFRS", "FFRS", "SFRS", "ARCH-GF", "ARCH-1F", "ARCH-2F"]
    assert [r for r in rep if r["STATE"].startswith("NOT_A_LIFT")][0]["RECORDS"] == '["GBP:7C5"]'
    pop = rows("02_LIFT_POPULATION.csv")
    ids = [r["ELEMENT_ID"] for r in pop]
    assert len(ids) == len(set(ids)) and all(i.startswith("LIFT-01") for i in ids)
    kinds = {r["KIND"] for r in pop}
    assert {"FOOTING", "PIT_FLOOR", "PIT_WALL", "SHAFT_ENCLOSURE", "LANDING_DOOR", "LIFT_TIE_BEAM", "COLUMN",
            "SHAFT_BEAMS", "SHAFT_ROOF", "OVERRUN"} <= kinds
    assert next(r for r in pop if r["KIND"] == "PIT_FLOOR")["DECISION"] == "NOT_A_SEPARATE_ELEMENT"
    assert len([r for r in pop if r["KIND"] == "FOOTING"]) == 1      # no second footing, no pit base slab


def test_wall_ring_column_cutouts_and_pieces_close():
    from shapely.geometry import box
    from shapely.ops import unary_union
    rep = rows("03_REPRESENTATION_CROSSWALK.csv")
    inner = json.loads(next(r for r in rep if r["STATE"] == "ONE_PHYSICAL_SHAFT")["RECT_MM"])
    outer = [inner[0] - 200, inner[1] - 200, inner[2] + 200, inner[3] + 200]
    cols = [json.loads(r["RECT_MM"]) for r in rep if r["OBJECT"].startswith("LIFT-01-COL") and "FP" in r["VIEWS"]]
    assert len(cols) == 4
    ring = box(*outer).difference(box(*inner))
    net = ring.difference(unary_union([box(*c) for c in cols]))
    walls = [r for r in rows("06_WALL_GEOMETRY_AND_CONCRETE_QTO.csv") if r["ELEMENT_ID"] in
             {f"LIFT-01-PIT-WALL-{k}" for k in "SNWE"}]
    pieces = unary_union([box(*json.loads(r["RECT_MM"])) for r in walls])
    assert abs(ring.area - 1.6e6) < 1e-3 and abs(net.area - 1.1e6) < 1e-3
    assert abs(pieces.symmetric_difference(net).area) < 1e-3
    assert {r["SIDE"]: F(r["LENGTH_MM"]) for r in walls} == {"S": 1800.0, "N": 1800.0, "W": 1200.0, "E": 700.0}
    assert all(abs(F(r["FOOTPRINT_M2"]) - F(r["LENGTH_MM"]) * 0.2 / 1000) < 1e-9 for r in walls)


def test_opening_is_the_pit_inside_area_and_s8_1a_cells_are_the_pieces():
    reg = {r["PART_ID"]: r for r in rows("01_RECOVERED_LIFT_PIT_REGION.csv", ROOT / "research/alsenan_ground_slab_s8_1a")}
    ge = {r["ID"]: r for r in rows("05_PIT_FOOTPRINT_AND_DEPTH_EVIDENCE.csv") if r["RECORD"] == "PLAN"}
    rg04 = json.loads(reg["S8.1A-RG-04"]["POLYGON_MM"])
    xs, ys = [p[0] for p in rg04], [p[1] for p in rg04]
    assert max(abs(a - b) for a, b in zip((min(xs), min(ys), max(xs), max(ys)), json.loads(ge["GE-01"]["SOURCE"]))) \
        < 0.01
    assert F(reg["S8.1A-RG-04"]["AREA_M2"]) == F(ge["GE-01"]["VALUE"]) == 3.24
    walls = {r["SIDE"]: json.loads(r["RECT_MM"]) for r in rows("06_WALL_GEOMETRY_AND_CONCRETE_QTO.csv")
             if r["ELEMENT_ID"].startswith("LIFT-01-PIT-WALL-") and r["SIDE"] in "SNWE"}
    for part, side in (("S8.1A-RG-12", "S"), ("S8.1A-RG-13", "N"), ("S8.1A-RG-14", "W"), ("S8.1A-RG-15", "E")):
        p = json.loads(reg[part]["POLYGON_MM"])
        b = (min(q[0] for q in p), min(q[1] for q in p), max(q[0] for q in p), max(q[1] for q in p))
        assert max(abs(a - c) for a, c in zip(b, walls[side])) < 0.01, part
    assert F(ge["GE-03"]["VALUE"]) == 1.6 and F(ge["GE-06"]["VALUE"]) == 8.0


# ------------------------------------------------------------------ footing and owners
def test_footing_stays_with_its_owners(s):
    f = {r["ITEM"]: r for r in rows("04_FOUNDATION_OWNERSHIP_AUDIT.csv")}
    s4 = next(r for r in rows("FOOTING_REBAR_OCCURRENCES.csv", ROOT / "research/alsenan_footing_rebar_s4")
              if r["occurrence_id"] == "FOCC-1B2B")
    assert f["footing bars (four mats)"]["VALUE"].startswith(s4["known_kg"]) and \
        s["footing"]["bars_kg_S4_lower_bound"] == float(s4["known_kg"])
    st = [r for r in J(ROOT / "research/alsenan_column_rebar_s3_1/COLUMN_LAP_STARTER_REGISTER.json")["rows"]
          if (r.get("footing") or {}).get("ref") == "FTG-FF-18688-14112" and r["component"] == "STARTER"]
    assert abs(s["footing"]["starters_kg_S3_1"] - math.fsum(r["kg"] for r in st)) < 1e-9 and len(st) == 4
    assert abs(s["footing"]["concrete_m3_computed_not_released"] - 4.6 * 4.5 * 0.55) < 1e-9
    assert s["footing"]["concrete_state"] == "OWNED_BUT_UNMEASURED"
    assert f["drawn outline (FP 1B2B)"]["STATE"] == "MATCH" and f["pit floor"]["STATE"] == "NOT_A_SEPARATE_ELEMENT"
    t01 = next(r for r in rows("S4_1_OWNERSHIP_TRANSFERS.csv", ROOT / "research/alsenan_footing_rebar_s4_1")
               if r["TRANSFER_ID"] == "S4.1-T01")
    assert t01["TARGET_STAGE"] == "S8" and t01["KG_IN_S4_1"] == "0.0"


def test_nothing_released_and_coefficients_by_hand(s):
    assert s["released"]["concrete_m3"] == 0.0 and s["released"]["kg"] == 0.0
    walls = rows("06_WALL_GEOMETRY_AND_CONCRETE_QTO.csv")
    assert not [r for r in walls if r["LANE"] in RELEASED] and not [r for r in walls if r["CONCRETE_M3"]]
    for r in walls:
        if r["M3_PER_M_HEIGHT_CONDITIONAL"]:
            assert F(r["M3_PER_M_HEIGHT_CONDITIONAL"]) == F(r["FOOTPRINT_M2"])
    total = next(r for r in walls if r["ELEMENT_ID"] == "LIFT-01-PIT-WALLS (all)")
    assert abs(s["sensitivity_only"]["pit_walls_m3_if_ff_at_minimum_founding_and_top_at_ffl"] - 1.1 * 1.95) < 1e-9
    assert "SENSITIVITY_ONLY" in total["SENSITIVITY"] and "never released" in total["SENSITIVITY"]
    reb = rows("08_REBAR_QTO.csv")
    assert all(F(r["KG"]) == 0 and r["QUANTITY_STATE"] == "BLOCKED_UNQUANTIFIED" for r in reb)
    for r in reb:
        if r["ROLE"] == "WALL_VERTICAL":
            n = math.ceil(6 * F(r["DISTRIBUTION_LENGTH_MM"]) / 1000 - 1e-9)
            assert int(r["COUNT_ALONG_FACE"]) == n
            assert abs(F(r["KG_PER_M_BAR_LENGTH_CONDITIONAL"]) - n * 16 ** 2 / 162) < 1e-8
        if r["ROLE"] == "WALL_HORIZONTAL":
            L = float(re.search(r"straight run ([\d.]+) mm", r["BAR_LENGTH_STATE"]).group(1))
            assert abs(F(r["KG_PER_M_WALL_HEIGHT_CONDITIONAL"]) - 6 * L / 1000 * 12 ** 2 / 162) < 1e-8
    vert = {(r["ELEMENT_ID"][-1], r["FACE"]): int(r["COUNT_ALONG_FACE"]) for r in reb if r["ROLE"] == "WALL_VERTICAL"}
    assert vert == {(k, f): n for k, n in (("S", 11), ("N", 11), ("W", 8), ("E", 5)) for f in ("INNER", "OUTER")}
    assert {r["APPLICABILITY"] for r in reb if r["ELEMENT_ID"][-1] in "WE" and r["ROLE"].startswith("WALL")} == \
        {"NOT_SHOWN"}


def test_levels_blocked_or_printed():
    lv = {r["ID"]: r for r in rows("05_PIT_FOOTPRINT_AND_DEPTH_EVIDENCE.csv") if r["RECORD"] == "LEVEL"}
    assert all(lv[f"LV-0{i}"]["STATE"] == "BLOCKED_UNQUANTIFIED" and not lv[f"LV-0{i}"]["VALUE"] for i in range(1, 6))
    assert [F(lv[f"LV-0{i}"]["VALUE"]) for i in (6, 7, 8, 9)] == [1.0, 5.5, 9.7, 13.9]
    assert F(lv["LV-10"]["VALUE"]) == 8.7 and F(lv["LV-11"]["VALUE"]) == 4.2
    assert lv["LV-12"]["STATE"] == "NOT_IN_SOURCE"


# ------------------------------------------------------------------ tie beam and the S6 beams on the shaft
def test_tie_beam_trigger_per_storey_and_measure():
    t = {r["STOREY"]: r for r in rows("09_TIE_BEAM_TRIGGER_AND_OWNERSHIP.csv")}
    gf = t["GF"]
    assert F(gf["FLOOR_TO_FLOOR_M"]) == 4.5 and gf["TRIGGER_FLOOR_TO_FLOOR"] == "TRIGGERED"
    assert gf["TRIGGER_CLEAR_TO_SLAB_SOFFIT"] == "NOT_ESTABLISHED" and "40 mm" in gf["CLEAR_TO_SLAB_SOFFIT_NOTE"]
    assert gf["TRIGGER_CLEAR_TO_BEAM_SOFFIT"] == "NOT_TRIGGERED" and "3.75" in gf["CLEAR_TO_BEAM_SOFFIT_NOTE"]
    assert gf["REQUIREMENT"].startswith("NOT_ESTABLISHED") and F(gf["ELEVATION_IF_REQUIRED_M"]) == 4.0
    assert gf["SECTION"] == "NOT_STATED" and gf["QUANTITY_STATE"] == "BLOCKED_UNQUANTIFIED" and F(gf["KG"]) == 0
    for k in ("1F", "2F"):
        assert abs(F(t[k]["FLOOR_TO_FLOOR_M"]) - 4.2) < 1e-9 and t[k]["REQUIREMENT"].startswith("NOT_REQUIRED")
    assert "5.5 m" in gf["PLAN_PATH"]


def test_s6_beams_on_the_shaft_recounted_from_s6(s):
    occ = {r["occurrence_id"]: r for r in rows("SUPERSTRUCTURE_BEAM_OCCURRENCES.csv",
                                               ROOT / "research/alsenan_superstructure_beam_rebar_s6")}
    ids = s["s6_shaft_beams"]
    assert len(ids) == 12 and all(i in occ for i in ids)
    by = {}
    for i in ids:
        sh = re.match(r"SPAN:(\w+):", json.loads(occ[i]["geometry_objects"])[0]).group(1)
        by.setdefault(sh, []).append(i)
        lo, hi = map(float, re.search(r":(\d+)-(\d+)$", json.loads(occ[i]["geometry_objects"])[0]).groups())
        assert hi - lo <= 2200 + 300                              # a span along one shaft side, not beyond it
    assert {k: len(v) for k, v in by.items()} == {"GFRS": 4, "FFRS": 4, "SFRS": 4}
    own = {r["COMPONENT"]: r for r in rows("12_OWNERSHIP_AUDIT.csv") if r["PART"] == "bars"}
    for sh, lvl in (("GFRS", "GF_ROOF"), ("FFRS", "1F_ROOF"), ("SFRS", "2F_ROOF")):
        kg = math.fsum(float(occ[i]["known_kg"]) for i in by[sh])
        assert own[f"LIFT-01-BEAMS-{lvl}"]["QUANTITY_RECORD"].startswith(f"{round(kg, 9):.9f}".rstrip("0").rstrip("."))


# ------------------------------------------------------------------ openings, callouts, ownership
def test_landing_openings_reconciled():
    o = rows("10_LIFT_OPENING_RECONCILIATION.csv")
    doors = [r for r in o if r["S8_6_OPENING"] != "-"]
    assert [r["S8_6_OPENING"] for r in doors] == ["OP-GF-023", "OP-1F-012", "OP-2F-005"]
    for r in doors:
        assert F(r["WIDTH_ARCH_MM"]) == 1000 == F(r["WIDTH_S8_6_MM"]) and json.loads(r["DISTANCE_TO_INNER_CORNERS_MM"]) \
            == [400.0, 400.0]
        assert F(r["RC_WALL_DEDUCTION_M3"]) == 0 and r["WALL_OWNER"] == "ARCHITECTURAL_BLOCKWORK"
    s86 = [r for r in rows("01_OPENING_CENSUS.csv", ROOT / "research/alsenan_lintels_s8_6")
           if r["TYPE"] == "6_SERVICE_SHAFT_OPENING"]
    assert sorted(r["OPENING_ID"] for r in s86) == sorted(r["S8_6_OPENING"] for r in doors)


def test_callouts_each_given_a_role_and_owner():
    c = {r["CALLOUT_ID"]: r for r in rows("07_REBAR_CALLOUT_REGISTER.csv")}
    assert all(r["ROLE"] and r["OWNER"] and r["STATE"] for r in c.values())
    assert [c[k]["AS_PRINTED"] for k in ("P14-R01", "P14-R02", "P14-R03", "P14-R04", "P14-R05")] == \
        ["6Ø12/m", "6Ø16/m", "2 Ø16", "2 Ø16", "2Ø12"]
    assert all(c[k]["OWNER"].startswith("S8.8") and c[k]["STATE"].startswith("BLOCKED")
               for k in ("P14-R01", "P14-R02", "P14-R03", "P14-R04", "P14-R05"))
    assert c["P14-R01"]["BAR_DIRECTION"].startswith("HORIZONTAL") and c["P14-R02"]["BAR_DIRECTION"] == "VERTICAL"
    assert c["P14-R06"]["OWNER"].startswith("S4") and c["P14-X01"]["STATE"] == "NOT_LIFT"
    assert c["P14-G04"]["STATE"].startswith("BLOCKED") and c["P14-G05"]["STATE"].startswith("NOT_STRUCTURAL")


def test_ownership_states_conservation_and_questions(s):
    own = rows("12_OWNERSHIP_AUDIT.csv")
    assert own and all(r["STATE"] in SIX for r in own)
    assert [r for r in own if r["STATE"] == "SOURCE_CONFLICT"][0]["COMPONENT"] == "LIFT-01-PIT-WALL ring vs columns"
    assert all(v == "PASS" for v in s["conservation"].values()) and len(s["conservation"]) == 15
    assert all(r["RESULT"] == "PASS" for r in rows("11_OVERLAP_AND_DOUBLE_COUNT_CHECKS.csv"))
    q = {r["QUESTION_ID"] for r in rows("14_RFI_QUESTIONS.csv")}
    assert q == set(s["questions"]) and len(q) == 13
    b = {r["ID"]: r for r in rows("13_BLOCKED_AND_CONFLICTS.csv")}
    assert b["C-01"]["STATE"] == "SOURCE_CONFLICT" and b["C-04"]["STATE"] == "CORRECTED"
    assert {"PRE-S8:SPC-LIFT_PIT", "PRE-S8:SPC-LIFT_TIE_BEAM-GF", "PRE-S8:PS8-LIFT-WALLS",
            "PRE-S8-READINESS:LIFT_PIT_AND_WALLS"} <= set(b)


def test_hygiene():
    for name in OUTPUTS + ["18_S8_8_FREEZE_MANIFEST.json"]:
        assert not HYG.search((PKG / name).read_text(encoding="utf-8")), name


# ------------------------------------------------------------------ with the private drawings
@needs_inputs
def test_rebuild_byte_identical():
    m = J(MANIFEST)
    subprocess.run([sys.executable, "-I", str(PKG / "build_s8_8.py")], check=True, cwd=ROOT, capture_output=True)
    for o, h in m["outputs"].items():
        assert hashlib.sha256((PKG / o).read_bytes()).hexdigest() == h, o


@needs_inputs
def test_drawings_read_again_with_ezdxf():
    """the structural DXF read directly (global coordinates, no S1 reader): the S-BW outlines, the four columns,
    the footing outline and its schedule row; the architectural DXF: printed dimensions and door jambs."""
    import ezdxf
    from shapely.geometry import Polygon, box
    from shapely.ops import unary_union
    st = ezdxf.readfile(str(ST))
    db = st.entitydb

    def rect(h):
        p = [(q[0], q[1]) for q in db[h].get_points("xy")]
        return min(x for x, _ in p), min(y for _, y in p), max(x for x, _ in p), max(y for _, y in p)
    assert sorted(e.dxf.handle for e in st.modelspace().query('*[layer=="S-BW"]')) == \
        sorted(["10EA", "10EB", "7BE", "7C2", "7C5", "7C6"])
    for inn, out, cols in (("10EA", "10EB", ("1096", "1099", "1090", "1093")),
                           ("7BE", "7C2", ("1F2", "1F5", "1EC", "1EF"))):
        a, b = rect(inn), rect(out)
        assert abs(a[2] - a[0] - 1800) < 0.01 and abs(a[3] - a[1] - 1800) < 0.01
        assert all(abs(v - 200) < 0.01 for v in (a[0] - b[0], a[1] - b[1], b[2] - a[2], b[3] - a[3]))
        ring = box(*b).difference(box(*a))
        net = ring.difference(unary_union([box(*rect(h)) for h in cols]))
        assert abs(net.area - 1.1e6) < 1.0 and abs(ring.area - net.area - 0.5e6) < 1.0
    f = rect("1B2B")
    assert abs(f[2] - f[0] - 4600) < 0.01 and abs(f[3] - f[1] - 4500) < 0.01
    assert Polygon([(f[0], f[1]), (f[2], f[1]), (f[2], f[3]), (f[0], f[3])]).contains(box(*rect("10EB")))
    att = {x.dxf.tag: x.dxf.text for x in db["2B1E"].attribs}
    assert (att["FO-TY"], att["W"], att["H"], att["DEPHT"]) == ("FF", "460", "450", "55")
    assert (att["SH-T-B"], att["SH-B-B"], att["SH-T-D"]) == ("6", "9", "14/m")
    ar = ezdxf.readfile(str(ARCH)).entitydb
    for h, v in (("666", 1800), ("67D", 1800), ("672", 200), ("D31", 1800), ("D3D", 1800), ("D62", 200),
                 ("E94", 200), ("139A", 1800), ("13A6", 1800), ("13CB", 200), ("142F", 200), ("1538", 200)):
        assert abs(ar[h].get_measurement() - v) < 1e-6, h
    for w_in, e_in, j0, j1 in (("216", "212", "226", "227"), ("B13", "B11", "B96", "B97"),
                               ("1297", "1293", "12AE", "12AF")):
        x0, x1 = ar[w_in].dxf.start.x, ar[e_in].dxf.start.x
        a, b = sorted((ar[j0].dxf.start.x, ar[j1].dxf.start.x))
        assert abs(x1 - x0 - 1800) < 0.01 and abs(b - a - 1000) < 0.01
        assert abs(a - x0 - 400) < 0.01 and abs(x1 - b - 400) < 0.01
