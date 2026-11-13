"""T-713 R-T713-1 PARENT_ONE_END_V1 and the V3.0.70 masonry census, from merged ledgers only.

Hand fixture 'Villa R' (not the development villa), top storey UF: plate below drawn top +3.15, roof finished +6.80
(structural top 6.80 - b_r, b_r >= 0) -> plate gap at most 3.65 m.
  - piece A, 1.20 m under an unlabelled band (depth not printed): AT_MOST 1.20 x 3.65 = 4.38 m2;
  - piece B, 0.50 m where an unlabelled member frames into a printed 0.45 band: AT_MOST 0.50 x (3.65 - 0.45) = 1.60;
  - a drop wall U = 7.125 m2 (d >= 0): AT_MOST 7.125.
  Parent 0.15 AT_MOST 13.105 m2 -> units 163.8125 pcs; mortar 13.105 x 0.0110625 = 0.1449740625 -> 0.144975 (UP);
  AAC glue 13.105 x 3.5 = 45.8675 kg; white units / perimeter HELD.
  Adverse: + a piece with no drawn end (annex datum) -> blank, blocker named, every material blank.
  One-ended low: a component with a drawn minimum 2.40 m2 beside an open one -> AT_LEAST 2.40 -> units 30.0 pcs
  (one-ended like the parent, never a range, never a point).
"""
import decimal
import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t696"))
spec = importlib.util.spec_from_file_location("t713_masonry_rest", ROOT / "research/agents_t713/t713_masonry_rest.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

PLATES = {"UF": {"below": ("3.15", "drawn", "synthetic"), "above": ("6.80", "max", "synthetic roof, b_r >= 0")}}
TXT_A = "0:H piece A in the BM-UF-001 band 1.2000 m: unlabelled band (D-04): depth not printed (Q-61 C(4))"
TXT_B = ("2:H junction BM-UF-002 0.5000 m: where the unlabelled BM-UF-002 frames into the band (D-04): the soffit "
         "is the deeper of B1 / B2 (0.45) and a member whose depth is not printed")
TXT_DROP = "drop d of the sunken panel over 1.2500 m"
TXT_ANNEX = "0:slab UF-001 4.5000 m: STOREY_HEIGHT.GF.ANNEX HELD: not declared for this project"


def comp(i, text, drop=None, floor="UF"):
    cls, cause, end = M.classify(text)
    return {"id": f"W{i}", "class": cls, "end": M.component_end(cls, end, floor, text, drop, PLATES)}


def villa_r():
    return [comp(1, TXT_A), comp(2, TXT_B), comp(3, TXT_DROP, "7.125")]


def test_piece_ends_by_hand():
    a, b, d = villa_r()
    assert a["class"] == "UNLABELLED_MEMBER" and a["end"]["upper"] == Decimal("4.38")
    assert b["end"]["upper"] == Decimal("1.60") and b["end"]["height_max_m"] == "3.20"
    assert d["class"] == "DROP" and d["end"]["upper"] == Decimal("7.125") and d["end"]["lower"] is None


def test_parent_at_most_and_materials():
    p = M.parent_bound(villa_r())
    assert p["kind"] == "AT_MOST" and Decimal(p["exact_m2"]) == Decimal("13.105") and p["printed_m2"] == 13.105
    u = M.material_follow(p, "MAS.UNITS.BLACK", "0.15", None)
    assert u["kind"] == "AT_MOST" and u["printed"] == 163.8125
    m = M.material_follow(p, "MAS.MORTAR.BLACK", "0.15", None)
    assert Decimal(m["exact"]) == Decimal("0.1449740625") and m["printed"] == 0.144975
    g = M.material_follow(p, "MAS.GLUE.AAC", "0.15", Decimal("3.5"))
    assert g["printed"] == 45.8675
    assert M.material_follow(p, "MAS.UNITS.WHITE", "0.15", None)["kind"] == "NONE"
    assert M.material_follow(p, "MAS.MORTAR.BLACK.PERIMETER", "0.15", None)["kind"] == "NONE"
    assert M.material_follow(p, "MAS.MORTAR.BLACK", "0.20", None)["printed"] == 0.193299  # 13.105 x 0.01475 up


def test_mirror_order_invariant():
    assert M.parent_bound(villa_r()[::-1])["exact_m2"] == M.parent_bound(villa_r())["exact_m2"]


def test_open_component_blanks_parent_and_materials():
    cs = villa_r() + [comp(4, TXT_ANNEX)]
    p = M.parent_bound(cs)
    assert p["kind"] == "NONE" and p["blocking_components"] == ["W4"]
    for code in ("MAS.UNITS.BLACK", "MAS.MORTAR.BLACK", "MAS.GLUE.AAC", "MAS.UNITS.WHITE"):
        assert M.material_follow(p, code, "0.15", Decimal("3.5"))["kind"] == "NONE"


def test_unprinted_height_at_least_only_and_materials_follow():
    lowc = {"id": "S1", "class": "X", "colour": "BLACK", "end": {"upper": None, "lower": Decimal("2.40")}}
    p = M.parent_bound([lowc, comp(2, TXT_ANNEX)])
    assert p["kind"] == "AT_LEAST" and p["printed_m2"] == 2.4 and p["blocking_components"] == ["S1", "W2"]
    u = M.material_follow(p, "MAS.UNITS.BLACK", "0.15", None)
    assert u["kind"] == "AT_LEAST" and u["printed"] == 30.0
    m = M.material_follow(p, "MAS.MORTAR.BLACK", "0.15", None)
    assert m["kind"] == "AT_LEAST" and m["printed"] == 0.02655  # 2.40 x 0.0110625 exact
    assert M.material_follow(p, "MAS.UNITS.WHITE", "0.15", None)["kind"] == "NONE"
    # the black minimum gives the AAC glue no minimum (colour of the drawn minimum decides)
    assert M.material_follow(p, "MAS.GLUE.AAC", "0.15", Decimal("3.5"))["kind"] == "NONE"
    # a drawn minimum of unknown colour gives no material minimum at all
    p2 = M.parent_bound([dict(lowc, colour=None), comp(2, TXT_ANNEX)])
    assert p2["kind"] == "AT_LEAST" and M.material_follow(p2, "MAS.UNITS.BLACK", "0.15", None)["kind"] == "NONE"


def test_adverse_inputs():
    with pytest.raises(ValueError):
        M.classify("something nobody classified")
    with pytest.raises(ValueError):
        M.parent_bound([])
    with pytest.raises(ValueError):                      # DROP without its U: never 0
        M.component_end("DROP", "AT_MOST_U", "UF", TXT_DROP, None, PLATES)
    with pytest.raises(ValueError):                      # mm read as m
        M.component_end("UNLABELLED_MEMBER", "AT_MOST_PLATE", "UF", TXT_A.replace("1.2000", "1200.0000"),
                        None, PLATES)
    with pytest.raises(ValueError):                      # a known member deeper than the storey
        M.component_end("UNLABELLED_MEMBER", "AT_MOST_PLATE", "UF", TXT_B.replace("(0.45)", "(4.45)"), None, PLATES)
    open_below = {"UF": {"below": ("3.15", "max", "x"), "above": ("6.80", "max", "x")}}
    assert M.component_end("UNLABELLED_MEMBER", "AT_MOST_PLATE", "UF", TXT_A, None, open_below)["upper"] is None
    assert M.component_end("UNLABELLED_MEMBER", "AT_MOST_PLATE", "ZZ", TXT_A, None, PLATES)["upper"] is None
    p = M.parent_bound(villa_r())
    assert M.material_follow(p, "MAS.GLUE.AAC", "0.40", None)["kind"] == "NONE"   # no rate: never borrowed


def test_development_villa_regression_from_merged_files():
    before = decimal.getcontext().prec
    doc = M.build()
    assert decimal.getcontext().prec == before
    c = doc["counts"]
    assert c["MAS.BLOCK | HELD blank"] == 15 and c["MAS.UNITS.WHITE | HELD blank"] == 15
    assert c["MAS.MORTAR.BLACK.LINTEL_BEARING | HELD bounded"] == 6 and c["MAS.GLUE.AAC | NOT_APPLICABLE"] == 2
    assert sum(c.values()) == 91 + 4
    ps = doc["parents"]
    assert len(ps) == 7
    p2 = ps["L-246f3c09de4c6b90efe5"]
    assert p2["bound"]["kind"] == "AT_MOST" and p2["bound"]["printed_m2"] == 1.965   # 0.1 x 4.25 + 2 x 0.2 x 3.85
    mats = {v["code"]: v for v in p2["materials"].values()}
    assert mats["MAS.UNITS.BLACK"]["printed"] == 24.5625
    assert mats["MAS.MORTAR.BLACK"]["printed"] == 0.021738                # 1.965 x 0.0110625 = 0.0217378125 up
    assert mats["MAS.GLUE.AAC"]["printed"] == 6.8775
    assert mats["MAS.UNITS.WHITE"]["kind"] == "NONE" and mats["MAS.MORTAR.BLACK.PERIMETER"]["kind"] == "NONE"
    named = p2["named_not_carried"]                                       # PART_HELD roof-datum walls: named only
    assert {n["wall"] for n in named} == {"2F-W08", "2F-W03"} and all(n["carried_by_part_lines"] for n in named)
    g = ps["L-0d9b9e89bb6455da475d"]                                      # GF-W22 moved in by R-T488-1 (PART_REDUCED)
    assert g["bound"]["kind"] == "AT_LEAST" and g["bound"]["printed_m2"] == 12.9311
    gm = {v["code"]: v for v in g["materials"].values()}
    assert gm["MAS.UNITS.BLACK"]["printed"] == 161.63875 and gm["MAS.UNITS.BLACK"]["kind"] == "AT_LEAST"
    assert gm["MAS.MORTAR.BLACK"]["printed"] == 0.14305                 # 0.14305029375 rounded DOWN
    assert gm["MAS.GLUE.AAC"]["kind"] == "NONE" and gm["MAS.UNITS.WHITE"]["kind"] == "NONE"
    for lid, p in ps.items():
        if lid not in ("L-246f3c09de4c6b90efe5", "L-0d9b9e89bb6455da475d"):
            assert p["bound"]["kind"] == "NONE" and p["bound"]["blocking_components"]
            assert all(v["kind"] == "NONE" for v in p["materials"].values())
    gf15 = ps["L-0d9b9e89bb6455da475d"]["by_class"]
    assert gf15["DROP"]["upper_m2"] == "29.410473" and gf15["ANNEX_DATUM"]["length_m"] == "16.2500"
    assert all(r["state"] != "HELD blank" or r["cause"] for r in doc["census"])


def test_tampered_index_refused(tmp_path, monkeypatch):
    bad = tmp_path / "idx.json"
    bad.write_text(M.IDX70.read_text(encoding="utf-8").replace('"MAS.BLOCK"', '"MAS.BLOCKX"', 1), encoding="utf-8")
    monkeypatch.setitem(M.PINS, bad, M.PINS[M.IDX70])
    monkeypatch.setattr(M, "IDX70", bad)
    with pytest.raises(SystemExit):
        M.build()
