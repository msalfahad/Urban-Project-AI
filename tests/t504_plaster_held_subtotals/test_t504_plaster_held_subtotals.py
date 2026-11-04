"""T-504: PLASTER_MATERIALS_TABLE_V3, R-T504-1 (R-T499-1 on plaster coats): a coat subtotal over any row with no exact
figure is HELD, its known part AT_LEAST with the bound / held rows listed; determinate subtotals = V1 / V2 exactly.

Hand fixture villa P (synthetic, not the training villa). Values: wall plaster 0.020 m (V1 reference, level 4), render
0.015 m printed MINIMUM, bond coat no thickness (HELD), synthetic project mix 1:4 for WALL_PLASTER only (render mix
HELD). Q-53 C conversion 1:4 = 7.6608 bags + 1.064 m3 sand per m3; 1:3 = 9.576 bags.
  P-1 dry 50.00 m2, P-2 dry 30.00 m2              wall plaster 80.00 x 0.020 = 1.600 m3 -> 12.25728 bags, 1.7024 m3 sand
  P-3 wet 20.00 m2                                 render 20.00 x 0.015 = >= 0.300 m3 (bound only), mix HELD
  P-4 dry, area HELD (stair hall height)           no figure in any coat
Normal (P-1, P-2): every wall-plaster subtotal COMPUTED = V1 / V2 (80.00 m2, 1.600 m3, 12.25728 bags).
Adverse (P-1 .. P-4): wall plaster area >= 80.00, mortar >= 1.600 (V1 printed 1.6 as the total), bags >= 12.25728,
  all HELD with P-4 listed; render mortar HELD >= 0.300 bound-complete; bond coat area >= 100.00, mortar None (not 0).
"""

import copy
import importlib.util
import re
from pathlib import Path

import pytest

from engine.source import plaster_materials_table_v1 as V1
from engine.source import plaster_materials_table_v2 as V2
from engine.source import plaster_materials_table_v3 as V3

ROOT = Path(__file__).resolve().parents[2]
SPEC = "synthetic project specification, clause 09200-2.3 (test only)"
MIX = {"WALL_PLASTER": {"sand_parts": 4, "source": SPEC, "level": 1}}

P = [
    {"id": "P-1", "class": V1.DRY, "area_m2": 50.00, "area_label": V1.PNET},
    {"id": "P-2", "class": V1.DRY, "area_m2": 30.00, "area_label": V1.PNET},
    {"id": "P-3", "class": V1.WET, "area_m2": 20.00, "area_label": V1.PNET},
    {"id": "P-4", "class": V1.DRY, "area_m2": None, "area_reason": "stair hall height HELD"},
]


def test_subtotal_rule_cases():
    assert V3.subtotal([])["status"] == V3.NO_ROWS and V3.subtotal([])["value"] is None
    ok = V3.subtotal([("a", 1.5, None), ("b", 2.0, None)])
    assert ok["status"] == V3.OK and ok["value"] == 3.5 and ok["at_least"] is None
    mixed = V3.subtotal([("a", 1.5, None), ("b", None, 0.5), ("c", None, None)])
    assert mixed["value"] is None and mixed["status"] == V3.HELD and mixed["at_least"] == 2.0
    assert mixed["exact_part"] == 1.5 and mixed["bound_part"] == 0.5
    assert mixed["bound_rows"] == ["b"] and mixed["held_rows"] == ["c"] and mixed["bound_complete"] is False
    none = V3.subtotal([("a", None, None), ("b", None, None)])
    assert none["value"] is None and none["at_least"] is None and none["status"] == V3.HELD     # never 0.0
    bnd = V3.subtotal([("a", None, 0.3)])
    assert bnd["status"] == V3.HELD and bnd["at_least"] == 0.3 and bnd["bound_complete"] is True


def test_normal_determinate_subtotals_equal_v1_and_v2_exactly():
    t = V3.table(P[:2], mix=MIX)
    w = t["sums"]["WALL_PLASTER"]
    v1, v2 = V1.table(P[:2])["sums"]["WALL_PLASTER"], V2.table(P[:2], mix=MIX)["sums"]["WALL_PLASTER"]
    assert w["area_m2"]["status"] == V3.OK and w["area_m2"]["value"] == v1["area_m2"] == pytest.approx(80.0)
    assert w["mortar_m3"]["value"] == v1["mortar_m3"] == pytest.approx(1.6)
    assert w["cement_bags"]["value"] == v2["cement_bags"] == pytest.approx(12.25728)
    assert w["sand_m3"]["value"] == v2["sand_m3"] == pytest.approx(1.7024)
    assert w["sensitivity_not_a_quantity"]["1:3"]["cement_bags"]["value"] == pytest.approx(15.3216)
    # the thickness is a level-4 estimate: arithmetic COMPUTED, evidence status still s.5 HELD (never VERIFIED)
    assert w["s5_status"] == V2.S5_HELD
    assert t["status_changes"] == [c for c in t["status_changes"] if c["coat"] == "BOND_COAT"]


def test_adverse_held_area_holds_every_wall_plaster_subtotal_with_its_known_part():
    t = V3.table(P, mix=MIX)
    w = t["sums"]["WALL_PLASTER"]
    assert V1.table(P)["sums"]["WALL_PLASTER"]["mortar_m3"] == pytest.approx(1.6)   # the V1 defect, reproduced
    for key, known in (("area_m2", 80.0), ("mortar_m3", 1.6), ("cement_bags", 12.25728), ("sand_m3", 1.7024)):
        rec = w[key]
        assert rec["value"] is None and rec["status"] == V3.HELD, key
        assert rec["at_least"] == pytest.approx(known) and rec["held_rows"] == ["P-4"] and rec["rows"] == 3, key
    assert w["sensitivity_not_a_quantity"]["1:3"]["cement_bags"]["at_least"] == pytest.approx(15.3216)
    keys = {(c["coat"], c["key"]) for c in t["status_changes"]}
    assert ("WALL_PLASTER", "mortar_m3") in keys and ("WALL_PLASTER", "area_m2") in keys


def test_adverse_render_minimum_is_a_complete_bound_and_held_mix_stays_held():
    r = V3.table(P, mix=MIX)["sums"]["LEVELLING_RENDER"]
    m = r["mortar_m3"]
    assert m["value"] is None and m["status"] == V3.HELD and m["at_least"] == pytest.approx(0.3)
    assert m["bound_rows"] == ["P-3"] and m["held_rows"] == [] and m["bound_complete"] is True
    assert m["exact_part"] is None and m["bound_part"] == pytest.approx(0.3)
    assert r["cement_bags"]["value"] is None and r["cement_bags"]["at_least"] is None   # no mix: no number, not 0
    assert r["area_m2"]["status"] == V3.OK and r["area_m2"]["value"] == pytest.approx(20.0)


def test_adverse_bond_coat_no_thickness_and_all_held_is_none_never_zero():
    b = V3.table(P, mix=MIX)["sums"]["BOND_COAT"]
    assert b["area_m2"]["status"] == V3.HELD and b["area_m2"]["at_least"] == pytest.approx(100.0)
    assert b["area_m2"]["held_rows"] == ["P-4"]
    for key in ("mortar_m3", "cement_bags", "sand_m3"):
        assert b[key]["value"] is None and b[key]["at_least"] is None and b[key]["exact_part"] is None
        assert len(b[key]["held_rows"]) == 4
    allheld = V3.table([P[3]])["sums"]
    for ly, s in allheld.items():
        for key in V3.KEYS:
            assert s[key]["value"] is None and s[key]["at_least"] is None, (ly, key)


def test_adverse_unclassified_face_area_is_beside_never_in_a_coat():
    els = P[:2] + [{"id": "P-X", "class": None, "area_m2": 10.0, "area_label": V1.PNET}]
    w = V3.table(els, mix=MIX)["sums"]["WALL_PLASTER"]
    assert w["area_m2"]["status"] == V3.HELD and w["area_m2"]["at_least"] == pytest.approx(80.0)
    assert w["area_m2"]["held_rows"] == ["P-X"]


def test_rows_are_v2_rows_byte_identical_and_v1_rows_work_too():
    v2 = V2.table(P, mix=MIX)
    t = V3.apply(copy.deepcopy(v2))
    assert t["rows"] == v2["rows"] and t["v2_sums"] == v2["sums"]
    s1 = V3.sums(V1.table(P)["rows"])            # V1 rows (no mix stage) give the same area / mortar records
    assert s1["WALL_PLASTER"]["mortar_m3"] == t["sums"]["WALL_PLASTER"]["mortar_m3"]
    assert "s5_status" not in s1["WALL_PLASTER"]


def test_module_unwired_without_family_terms_and_v1_v2_untouched():
    assert V3.DEFAULT_GUARD_CLASS == "UNWIRED_PRODUCER" and V3.SUPERSEDES is None
    assert V1.METHOD_ID == "PLASTER_MATERIALS_TABLE_V1" and V2.METHOD_ID == "PLASTER_MATERIALS_TABLE_V2"
    src = (ROOT / "engine/source/plaster_materials_table_v3.py").read_text(encoding="utf-8")
    assert '"FIN.' not in src and '"MAS.' not in src
    assert not re.search(r"\b(alsenan|7757)\b", src, re.I)
    defs = re.findall(r"^\s*def\s+(\w+)", src, re.M)
    assert not [d for d in defs for term in ("spatter", "mortar", "glue", "dash_coat") if term in d.lower()]


# ------------------------------------------------------------- the merged T-454 / T-489 ledger (committed pinned inputs)
def _reader():
    spec = importlib.util.spec_from_file_location("t489_for_t504", ROOT / "research/agents_t489/t489_plaster_mix.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_ledger_reproduces_f_t499_1_and_lists_every_status_change():
    led = _reader().build()
    t = V3.apply(led["table"])
    w = t["sums"]["WALL_PLASTER"]
    # F-T499-1: V1 printed 4.726962 m3 over 25 of 52 rows as the total; V3 holds it with that known part
    assert t["v1_sums"]["WALL_PLASTER"]["mortar_m3"] == pytest.approx(4.726962)
    assert w["rows"] == 52 and len(w["mortar_m3"]["held_rows"]) == 27
    assert w["mortar_m3"]["value"] is None and w["mortar_m3"]["at_least"] == pytest.approx(4.726962)
    assert w["sensitivity_not_a_quantity"]["1:3"]["cement_bags"]["at_least"] == pytest.approx(45.265391)
    r = t["sums"]["LEVELLING_RENDER"]["mortar_m3"]
    assert r["at_least"] == pytest.approx(5.104557) and len(r["bound_rows"]) == 12 and len(r["held_rows"]) == 22
    b = t["sums"]["BOND_COAT"]["area_m2"]
    assert b["at_least"] == pytest.approx(576.6519) and len(b["held_rows"]) == 33
    assert t["rows"] == led["table"]["rows"]
    ch = {(c["coat"], c["key"]) for c in t["status_changes"]}
    assert len(t["status_changes"]) == 17
    assert {("BOND_COAT", "area_m2"), ("WALL_PLASTER", "area_m2"), ("WALL_PLASTER", "mortar_m3"),
            ("LEVELLING_RENDER", "area_m2"), ("LEVELLING_RENDER", "mortar_m3_at_least")} <= ch
    assert all(s["s5_status"] == V2.S5_HELD for s in t["sums"].values())
