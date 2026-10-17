"""S8.4 (research/alsenan_water_tank_s8_4): water-tank roof region, concrete and reinforcement QTO.

The checks re-derive the package from its outputs, the frozen stages and, when the private drawings are restored, the
drawings themselves through independent tools (ezdxf, shapely):

- every earlier stage still verifies; the package is frozen before any comparison and is blind;
- two slab panels and one use-zone parent; no tank base, wall or member is invented;
- T 18 is a 180 mm thickness, never a bar; each (T&B) callout gives two faces of its own direction only;
- concrete and steel recomputed by hand from the printed figures and the drawn faces;
- S7's 3,802.015 kg is untouched, the 20.087 kg of S7 top steel at the tank edges stays S7, and every S7 item and
  PRE-S7.1 transfer of the region lands on exactly one S8.4 row; every blocked portion is listed."""

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
PKG = ROOT / "research" / "alsenan_water_tank_s8_4"
MANIFEST = PKG / "15_S8_4_FREEZE_MANIFEST.json"
OUTPUTS = ["00_README.md", "01_SOURCE_REGISTER.csv", "02_POPULATION_AND_OWNERSHIP.csv",
           "03_THICKNESS_AND_CALLOUT_REGISTER.csv", "04_CONCRETE_QTO.csv", "05_REINFORCEMENT_QTO.csv",
           "06_REINFORCEMENT_BANDS.csv", "07_S7_OWNERSHIP_RECONCILIATION.csv", "08_BLOCKED_COMPONENTS.csv",
           "09_SOURCE_CONFLICTS_AND_QUESTIONS.csv", "10_INTERFACE_AUDIT.csv", "11_SENSITIVITY_CASES.csv",
           "12_CONSERVATION_CHECKS.csv", "13_PROVENANCE.jsonl", "14_S8_4_SUMMARY.json"]
BY_SHA = ROOT / "data/inputs/by_sha256"
ST = BY_SHA / "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
AR = BY_SHA / "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
needs_inputs = pytest.mark.skipif(not (ST.exists() and AR.exists()),
                                  reason="private client drawings not restored in data/inputs/by_sha256")
PANELS = ("SP-2F_ROOF_SLAB-01", "SP-2F_ROOF_SLAB-02")
KG = {d: d * d / 162.0 for d in (10, 12, 14)}


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name, base=PKG):
    with open(base / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def s():
    return J(PKG / "14_S8_4_SUMMARY.json")


# ------------------------------------------------------------------ freeze and blindness
def test_frozen_before_comparison():
    m = J(MANIFEST)
    assert m["round"] == "S8_4" and m["state"] == "FROZEN_BEFORE_COMPARISON" and m["references_read"] == []
    assert set(m["outputs"]) == set(OUTPUTS)
    DR.verify_frozen(MANIFEST, ROOT)


def test_every_earlier_stage_still_verifies(s):
    assert len(s["frozen_baselines"]) == 20 and {"S7", "S7A", "PRE-S8", "S8.3", "S8.3A"} <= set(s["frozen_baselines"])
    found = {}
    for mp in sorted((ROOT / "research").glob("*/*FREEZE_MANIFEST.json")):
        found.setdefault(hashlib.sha256(mp.read_bytes()).hexdigest(), mp)
    for k, h in s["frozen_baselines"].items():
        assert h in found, k                                            # the manifest itself is unchanged
        DR.verify_frozen(found[h], ROOT)                                # and so is everything it pins
    m = J(MANIFEST)
    for rel, h in m["inputs"].items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == h, rel
    for name, h in s["s8_3_errata_sha256"].items():
        assert hashlib.sha256((ROOT / "research/alsenan_dome_ring_s8_3/errata" / name).read_bytes()).hexdigest() == h


def test_builder_and_engine_are_blind():
    for src in (PKG / "build_s8_4.py", ROOT / "engine/source/slab_layered_mesh.py"):
        text = src.read_text(encoding="utf-8")
        for tok in ("BOQ_LINES", "registers_v3b", "V3b", "coverage_recovery", "freelancer", "donor", "christ", "U-C4N",
                    "kg/m3", "benchmark", "post_freeze", "02_STRUCTURAL_ELEMENT_CENSUS", "03_CONCRETE_COVERAGE",
                    "04_REBAR_COVERAGE", "08_SOURCE_CONFLICT_REGISTER", "control_plane", "multi_engine"):
            assert tok not in text, (src.name, tok)
    assert not any("pre_s8" in k for k in J(MANIFEST)["inputs"])          # PRE-S8 is verified, never read


def test_registry_declares_the_builder_and_engine():
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "research/alsenan_water_tank_s8_4/build_s8_4.py" in RP.ACCURATE_BUILDERS
    assert "engine/source/slab_layered_mesh.py" in RP.ACCURATE_MODULES


# ------------------------------------------------------------------ population
def test_two_panels_one_parent_and_no_invented_tank(s):
    pop = {r["ROW_ID"]: r for r in rows("02_POPULATION_AND_OWNERSHIP.csv")}
    phys = [r for r in pop.values() if r["ROW_KIND"] == "PHYSICAL_SLAB_PANEL"]
    assert sorted(r["OBJECT"] for r in phys) == list(PANELS) and all(r["PARENT"] == "SPC-WATER_TANK-SFRS" for r in phys)
    assert pop["P-ZONE"]["ROW_KIND"] == "USE_ZONE_PARENT" and pop["P-ZONE"]["AREA_M2"] == ""
    absent = {r["OBJECT"] for r in pop.values() if r["ROW_KIND"] == "NOT_IN_SOURCE"}
    assert absent == {"TANK_BASE", "TANK_WALLS", "TANK_LOCAL_REINFORCEMENT", "TANK_OPENINGS"}
    assert s["confirmed_physical_elements"]["tank_base"] == s["confirmed_physical_elements"]["tank_walls"] == "NOT_IN_SOURCE"
    conc = rows("04_CONCRETE_QTO.csv")
    assert all(r["VOLUME_M3"] == "" for r in conc if r["LANE"] == "NOT_IN_SOURCE")


def test_starting_population_matches_pre_s8_ids_only():
    """PRE-S8's candidate register names the same three objects (only the id column is read: other columns carry
    earlier figures)."""
    with open(ROOT / "research/pre_s8_structural_completeness/06_S8_CANDIDATE_REGISTER.csv", encoding="utf-8") as fh:
        ids = [json.loads(r["ELEMENT_IDS"]) for r in csv.DictReader(fh) if r["S8_FAMILY"] == "WATER_TANK"]
    assert len(ids) == 1 and sorted(ids[0]) == sorted(J(PKG / "14_S8_4_SUMMARY.json")["starting_population"])


# ------------------------------------------------------------------ thickness and callouts
def test_t18_is_a_180_mm_thickness_never_a_bar(s):
    reg = rows("03_THICKNESS_AND_CALLOUT_REGISTER.csv")
    tags = [r for r in reg if r["KIND"] == "THICKNESS_TAG"]
    assert sorted(r["PANEL"] for r in tags) == list(PANELS) and all(r["READING"] == "slab thickness 180 mm" for r in tags)
    assert all(r["DIA_MM"] == "" for r in tags)
    assert not any(r["DIA_MM"] == "18" for r in rows("05_REINFORCEMENT_QTO.csv"))
    assert s["thickness_mm"] == {p: 180 for p in PANELS}


def test_each_t_and_b_callout_gives_two_faces_of_its_own_direction_only():
    reg = [r for r in rows("03_THICKNESS_AND_CALLOUT_REGISTER.csv") if r["KIND"] == "RATE_CALLOUT"]
    assert Counter((r["PANEL"], r["DIRECTION"]) for r in reg) == Counter({(p, d): 1 for p in PANELS for d in "XY"})
    assert all(json.loads(r["LAYERS"]) == ["BOTTOM", "TOP"] for r in reg)
    fam = rows("05_REINFORCEMENT_QTO.csv")
    for r in reg:
        f = [x for x in fam if x["CALLOUT"] == r["ROW_ID"][2:]]
        assert sorted(x["LAYER"] for x in f) == ["BOTTOM", "TOP"] and {x["DIRECTION"] for x in f} == {r["DIRECTION"]}
    assert {(r["ROW_ID"][2:], r["DIA_MM"], r["RATE_PER_M"]) for r in reg} == \
        {("7A7", "14", "7"), ("7A8", "14", "6"), ("798", "12", "6"), ("796", "12", "6")}


# ------------------------------------------------------------------ quantities by hand
def test_concrete_by_hand(s):
    """Panel 01: 2.50 x 3.30 less the 0.05 x 0.30 column notch; panel 02: 1.80 x 3.00; t = 0.180 m."""
    c = {r["PANEL_ID"]: r for r in rows("04_CONCRETE_QTO.csv") if r["RELEASED"] == "True"}
    a1, a2 = 2.5 * 3.3 - 0.05 * 0.3, 1.8 * 3.0
    assert float(c[PANELS[0]]["NET_AREA_M2"]) == pytest.approx(a1) and float(c[PANELS[1]]["NET_AREA_M2"]) == pytest.approx(a2)
    assert float(c[PANELS[0]]["VOLUME_M3"]) == pytest.approx(a1 * 0.18) and float(c[PANELS[1]]["VOLUME_M3"]) == pytest.approx(a2 * 0.18)
    assert s["released"]["concrete_m3"] == pytest.approx((a1 + a2) * 0.18)
    assert all(r["LANE"] == "PROJECT_BASIS_QTO" for r in c.values())


def test_reinforcement_by_hand(s):
    """Full layer = rate x area. Bottom stop zones (blocked) = 0.125 x 0.5 x rate x (width x local run) at each end on
    a continuous or continuity-unresolved beam: 01-X at BL003 over 3.0 m of 2.5 m runs; 01-Y at BL008 over 2.45 m of
    3.3 m runs; 02-X at BL003 and BL002 over 3.0 m of 1.8 m runs; 02-Y at BL011 over 1.8 m of 3.0 m runs."""
    a1, a2 = 2.5 * 3.3 - 0.05 * 0.3, 1.8 * 3.0
    full = {("01", "X"): (7, 14, a1), ("01", "Y"): (6, 14, a1), ("02", "X"): (6, 12, a2), ("02", "Y"): (6, 12, a2)}
    stop = {("01", "X"): 0.0625 * 7 * 3.0 * 2.5, ("01", "Y"): 0.0625 * 6 * 2.45 * 3.3,
            ("02", "X"): 2 * 0.0625 * 6 * 3.0 * 1.8, ("02", "Y"): 0.0625 * 6 * 1.8 * 3.0}
    fam = {r["ITEM_ID"]: r for r in rows("05_REINFORCEMENT_QTO.csv")}
    tot = blocked = 0.0
    for (p, d), (n, dia, a) in full.items():
        b, t = fam[f"S8.4-R-{p}-{d}-B"], fam[f"S8.4-R-{p}-{d}-T"]
        assert float(t["RELEASED_LENGTH_M"]) == pytest.approx(n * a) and float(t["STOP_ZONE_LENGTH_M"]) == 0
        assert float(b["FULL_LENGTH_M"]) == pytest.approx(n * a)
        assert float(b["STOP_ZONE_LENGTH_M"]) == pytest.approx(stop[(p, d)])
        assert float(b["RELEASED_KG"]) == pytest.approx((n * a - stop[(p, d)]) * KG[dia])
        tot += (2 * n * a - stop[(p, d)]) * KG[dia]
        blocked += stop[(p, d)] * KG[dia]
    assert s["released"]["reinforcement_kg"] == pytest.approx(tot)
    assert s["blocked_stop_zone_kg"] == pytest.approx(blocked)
    assert s["by_diameter_kg"]["14"] + s["by_diameter_kg"]["12"] == pytest.approx(tot)
    assert all(r["LANE"] == "PROJECT_BASIS_QTO" and r["PHYSICAL_BBS_COUNT"] == "UNRESOLVED" for r in fam.values())
    stops = [r for r in rows("08_BLOCKED_COMPONENTS.csv") if r["BLOCKED_ID"].startswith("BL-STOP-")]
    assert math.fsum(float(r["SENSITIVITY_KG"]) for r in stops) == pytest.approx(blocked)
    assert all(r["KG"] == "" and r["STATE"] == "BLOCKED_UNQUANTIFIED" for r in stops)


def test_bands_cover_each_panel_exactly():
    bands = rows("06_REINFORCEMENT_BANDS.csv")
    fam = {r["ITEM_ID"]: r for r in rows("05_REINFORCEMENT_QTO.csv")}
    for fid, f in fam.items():
        b = [x for x in bands if x["ITEM_ID"] == fid]
        assert math.fsum(float(x["INTEGRAL_M2"]) for x in b) == pytest.approx(float(f["PANEL_AREA_M2"]))
        assert math.fsum(float(x["STOP_ZONE_M"]) for x in b) == pytest.approx(float(f["STOP_ZONE_LENGTH_M"]))


# ------------------------------------------------------------------ S7 interface (mandatory conservation gate)
def test_s7_is_untouched_and_its_adjacent_steel_stays_s7(s):
    s7 = J(ROOT / "research/alsenan_slab_rebar_s7/09_S7_PROJECT_SUMMARY.json")
    assert s7["totals_kg"]["RESTRICTED_S7_PROJECT_BASIS_KG"] == pytest.approx(3802.015, abs=5e-4)
    DR.verify_frozen(ROOT / "research/alsenan_slab_rebar_s7/12_S7_FREEZE_MANIFEST.json", ROOT)
    with open(ROOT / "research/alsenan_slab_rebar_s7a_qa/08_END_CONDITION_AUDIT.csv", encoding="utf-8") as fh:
        ends = [r for r in csv.DictReader(fh) if "WATER_TANK" in r["UNRESOLVED_REASON"]]
    assert len(ends) == 10 and math.fsum(float(r["S7_TOP_EXTENSION_KG_AT_END"]) for r in ends) == pytest.approx(20.087448558)
    rec = [r for r in rows("07_S7_OWNERSHIP_RECONCILIATION.csv") if r["ROW_KIND"] == "S7_RELEASED_ADJACENT_STRIP_END"]
    assert sorted(r["S7_STRIP_OR_COMPONENT"] for r in rec) == sorted(r["STRIP_ID"] for r in ends)
    assert all(r["WHERE"] not in PANELS and r["S8_4_TERMINAL"].startswith("STAYS_WITH_S7") for r in rec)
    assert s["s7"]["tank_adjacent_released_kg"] == pytest.approx(20.087448558)
    with open(ROOT / "research/alsenan_slab_rebar_s7/01_S7_RELEASE_ITEMS.csv", encoding="utf-8") as fh:
        s7_items = {r["S7_ITEM_ID"]: r for r in csv.DictReader(fh)}
    assert {s7_items[r["S7_ID"]]["PANEL_ID"] for r in rec} <= {"SP-2F_ROOF_SLAB-03", "SP-2F_ROOF_SLAB-04",
                                                                "SP-2F_ROOF_SLAB-06"}
    assert not [i for i in s7_items.values() if i["PANEL_ID"] in PANELS]          # S7 owns nothing in the tank panels


def test_s8_4_releases_nothing_on_a_support_or_beyond_a_face():
    fam = rows("05_REINFORCEMENT_QTO.csv")
    assert len(fam) == 8 and all(r["RUN_BASIS"].startswith("face to face") for r in fam)
    assert not any(r["CALLOUT"] in ("EB",) or "SUP-" in r["ITEM_ID"] for r in fam)


def test_every_s7_item_and_transfer_of_the_region_lands_once():
    with open(ROOT / "research/alsenan_slab_rebar_s7/02_S7_BLOCKED_ITEMS.csv", encoding="utf-8") as fh:
        s7b = [r for r in csv.DictReader(fh) if r["S8_REGION"] == "WATER_TANK_SUPPORT_REGION"]
    with open(ROOT / "research/alsenan_slab_rebar_pre_s7_1/02_OWNERSHIP_TRANSFERS.csv", encoding="utf-8") as fh:
        tr = [r for r in csv.DictReader(fh) if r["region"] == "WATER_TANK_SUPPORT_REGION"]
    rec = rows("07_S7_OWNERSHIP_RECONCILIATION.csv")
    ex = Counter(r["S7_ID"] for r in rec if r["ROW_KIND"] == "S7_EXCLUDED_ITEM")
    assert len(s7b) == 22 and ex == Counter(r["S7_BLOCKED_ID"] for r in s7b)
    tt = Counter(r["ROW_ID"] for r in rec if r["ROW_KIND"] == "PRE_S7_1_TRANSFER")
    assert len(tr) == 33 and tt == Counter(r["TRANSFER_ID"] for r in tr)
    targets = {r["ITEM_ID"] for r in rows("05_REINFORCEMENT_QTO.csv")} | \
        {r["ITEM_ID"] for r in rows("04_CONCRETE_QTO.csv")} | {r["BLOCKED_ID"] for r in rows("08_BLOCKED_COMPONENTS.csv")}
    for r in rec:
        if r["ROW_KIND"] != "S7_RELEASED_ADJACENT_STRIP_END":
            row = r["S8_4_ROW"]
            got = json.loads(row) if row.startswith("[") else [row]
            assert got and set(got) <= targets, r["ROW_ID"]
    fam = [r for r in rec if r["ROW_KIND"] == "S7_EXCLUDED_ITEM" and r["BAR_ROLE"] == "TRANSFERRED_FAMILY"]
    assert len(fam) == 8 and all(r["S8_4_TERMINAL"] == "RELEASED_S8_4" for r in fam)     # nothing excluded is omitted


def test_blocked_components_are_named_with_their_reasons(s):
    bl = rows("08_BLOCKED_COMPONENTS.csv")
    ids = [r["BLOCKED_ID"] for r in bl]
    assert len(ids) == len(set(ids))
    kinds = Counter(r["BLOCKED_ID"].split("-")[1] for r in bl)
    assert kinds["ANCH"] == 8 and kinds["NOTE2"] == 11 and kinds["TEMP"] == 4 and kinds["CONT"] == 2 and kinds["BBS"] == 2
    assert all(r["WHY"] and r["KG"] == "" for r in bl)
    note2 = [r for r in bl if r["BLOCKED_ID"].startswith("BL-NOTE2-S7B")]
    assert math.fsum(float(r["SENSITIVITY_KG"]) for r in note2 if r["SENSITIVITY_KG"]) == \
        pytest.approx(s["note2_tank_side_sensitivity_kg"])
    assert s["note2_tank_side_sensitivity_kg"] == pytest.approx(89.4 * KG[10])       # 5 /m x 1/3 run, every beam edge
    assert {r["STATE"] for r in bl if r["BLOCKED_ID"].startswith("BL-TEMP")} == {"NOT_ADDED"}
    assert {r["STATE"] for r in bl if r["BLOCKED_ID"].startswith("BL-TANK")} == {"NOT_IN_SOURCE"}


def test_sensitivity_is_never_released(s):
    sens = {r["CASE_ID"]: r for r in rows("11_SENSITIVITY_CASES.csv")}
    assert all(r["LANE"] == "SENSITIVITY_ONLY" for r in sens.values())
    assert float(sens["SA-01"]["KG"]) == pytest.approx(s["released"]["reinforcement_kg"] + s["blocked_stop_zone_kg"])
    assert float(sens["SA-03"]["DELTA_KG"]) == pytest.approx(s["note2_tank_side_sensitivity_kg"])
    assert s["released"]["lane"] == "PROJECT_BASIS_QTO"


def test_conservation_and_hygiene(s):
    assert all(v == "PASS" for v in s["conservation"].values()) and len(s["conservation"]) == 17
    assert not [p for p in PKG.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf", ".dxf", ".dwg")]
    for o in OUTPUTS:
        text = (PKG / o).read_text(encoding="utf-8")
        assert not re.search(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}", text), o


# ------------------------------------------------------------------ independent checks on the drawings
@needs_inputs
def test_drawing_handles_with_ezdxf():
    import ezdxf
    doc = ezdxf.readfile(ST)
    db = doc.entitydb
    assert db["1A85"].dxf.text.strip() == "WATER TANK PLACE"
    for h, t in (("7B3", "T"), ("7B4", "18"), ("1A7D", "T"), ("1A7E", "18"), ("7AF", "(T&B)"), ("7B0", "(T&B)"),
                 ("1A7F", "(T&B)"), ("1A80", "(T&B)")):
        assert db[h].dxf.text.strip() == t, h
    for h, t in (("7A7", "7%%C14/m"), ("7A8", "6%%c14/m"), ("798", "6%%c12/m"), ("796", "6%%c12/m")):
        assert db[h].dxf.text.strip() == t, h
    tank = [e.dxf.handle for e in doc.modelspace().query("TEXT MTEXT")
            if "TANK" in (e.dxf.text if e.dxftype() == "TEXT" else e.text).upper()]
    assert tank == ["1A85"]


@needs_inputs
def test_cloud_and_panels_against_shapely():
    shapely = pytest.importorskip("shapely")
    from shapely.geometry import Polygon
    import ezdxf
    doc = ezdxf.readfile(ST)
    frame = None
    for e in doc.modelspace().query('LWPOLYLINE[layer=="DEFPOINTS"]'):
        if e.dxf.handle == "B6":
            pts = list(e.get_points("xy"))
            frame = (min(p[0] for p in pts), min(p[1] for p in pts))
    cloud = Polygon([(x - frame[0], y - frame[1]) for x, y in doc.entitydb["1A81"].get_points("xy")])
    pan = {r["panel_id"]: Polygon(r["polygon_mm"]) for r in
           J(ROOT / "research/alsenan_structural_census_s1/SLAB_PANEL_REGISTER.json")["rows"] if r["panel_id"] in PANELS}
    assert all(cloud.contains(p.centroid) for p in pan.values())
    assert pan[PANELS[0]].area / 1e6 == pytest.approx(8.235) and pan[PANELS[1]].area / 1e6 == pytest.approx(5.4)
    assert pan[PANELS[0]].intersection(pan[PANELS[1]]).area == 0


@needs_inputs
def test_rebuild_is_byte_identical():
    names = OUTPUTS + [MANIFEST.name]
    before = {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in names}
    subprocess.run([sys.executable, "-I", str(PKG / "build_s8_4.py")], check=True, cwd=ROOT, capture_output=True)
    after = {o: hashlib.sha256((PKG / o).read_bytes()).hexdigest() for o in names}
    assert before == after
