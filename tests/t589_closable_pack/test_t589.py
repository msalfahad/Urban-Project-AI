"""T-589 R-T589-1: structural closable-component classification. Hand villa "K589" (not the training villa), adverse
cases, then the development villa from merged, sha-pinned repository files (no private input)."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t589"))
import t589_rules as R  # noqa: E402
import t589_alsenan as A  # noqa: E402

D = Decimal


# ---- villa "K589" (hand) -----------------------------------------------------------------------------------------
# K1: column 0.30 x 0.60 on a schedule sheet S-02, storey 3.00 slab top to slab top, all printed:
#     0.30 x 0.60 x 3.00 = 0.540 m3 -> CLOSABLE (sheet S-02 + plan S-01).
# K2: column 0.25 x 0.50 under a roof whose slab-top level is not printed (designer item D-01): HELD, no figure.
def k589():
    k1 = {"id": "K1", "section": "B10", "closure_class": "CLOSABLE_FROM_DRAWINGS", "evidence": "worker hand",
          "missing": "Checker re-measure", "sheet_refs": ["S-02 column schedule", "S-01 plan"], "pack": "PK1",
          "quantity": {"unit": "m3", "basis": "ENGINE_VALUED", "value": str(D("0.30") * D("0.60") * D("3.00"))}}
    k2 = {"id": "K2", "section": "B10", "closure_class": "DESIGNER_ITEM", "evidence": "outline drawn",
          "missing": "roof slab-top level", "designer_refs": ["D-01"],
          "quantity": {"unit": "m3", "basis": "ENGINE_HELD", "low": None, "high": None,
                       "held_item": "roof slab-top level not printed (D-01)"}}
    return k1, k2


def test_hand_two_columns_table():
    k1, k2 = k589()
    assert D(k1["quantity"]["value"]) == D("0.540")
    t = R.section_table("B10", "m3", [k1, k2])
    assert t["n"] == 2
    assert t["by_class"]["CLOSABLE_FROM_DRAWINGS"]["n"] == 1
    assert t["by_class"]["DESIGNER_ITEM"]["n"] == 1
    assert t["by_class"]["OWNER_RULE_GAP"]["n"] == 0 and t["by_class"]["VERIFIED_ON_RECORD"]["n"] == 0
    assert t["by_class"]["CLOSABLE_FROM_DRAWINGS"]["quantity"]["m3|ENGINE_VALUED"]["sum"] == "0.540000"
    held = t["by_class"]["DESIGNER_ITEM"]["quantity"]["m3|ENGINE_HELD"]
    assert held["high"] == "HELD" and held["low_held_items"] == 1  # never 0


def test_hand_split_readds():
    R.check_split("0.540", ["0.360", "0.180"])
    with pytest.raises(R.ClassError):
        R.check_split("0.540", ["0.360", "0.170"])


# ---- adverse ------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("mut", [
    lambda c: c.update(sheet_refs=[]),                 # closable without a sheet reference
    lambda c: c.update(sheet_refs=["see drawings"]),   # a reference that names no sheet / page / handle
    lambda c: c.pop("pack"),                            # closable without a pack
    lambda c: c.update(closure_class="PROBABLY_FINE"),  # unknown class
    lambda c: c["quantity"].update(unit="kg"),          # kg inside a table
    lambda c: c["quantity"].update(unit="mm"),
    lambda c: c["quantity"].update(pct="6.2"),          # % on a component
    lambda c: c["quantity"].update(value=0.54),         # float
])
def test_adverse_closable(mut):
    k1, _ = k589()
    k1 = copy.deepcopy(k1)
    mut(k1)
    with pytest.raises(R.ClassError):
        R.check_component(k1)


@pytest.mark.parametrize("mut", [
    lambda c: c.update(designer_refs=[]),
    lambda c: c.update(designer_refs=["ask the engineer"]),
    lambda c: c["quantity"].update(value="0"),         # held as a point / as 0
    lambda c: c["quantity"].update(held_item=None),     # held without low or item
])
def test_adverse_designer(mut):
    _, k2 = k589()
    k2 = copy.deepcopy(k2)
    mut(k2)
    with pytest.raises(R.ClassError):
        R.check_component(k2)


def test_adverse_verified_needs_checker_and_owner_gap_needs_rule():
    k1, _ = k589()
    v = dict(copy.deepcopy(k1), closure_class="VERIFIED_ON_RECORD", verified_by="worker says so")
    with pytest.raises(R.ClassError):
        R.check_component(v)
    R.check_component(dict(v, verified_by="Checker 2026-11-07 (own re-measure)"))
    o = dict(copy.deepcopy(k1), closure_class="OWNER_RULE_GAP")
    with pytest.raises(R.ClassError):
        R.check_component(o)
    with pytest.raises(R.ClassError):
        R.check_component(dict(o, rule_gap="no working-space rule", owner_question="Q-xx"))
    R.check_component(dict(o, rule_gap="no working-space rule"))


def test_adverse_unit_table_and_low_high():
    k1, k2 = k589()
    with pytest.raises(R.ClassError):
        R.check_component(k1, unit_table="t")
    bad = copy.deepcopy(k2)
    bad["quantity"].update(low="0.3", high="0.2")
    with pytest.raises(R.ClassError):
        R.check_component(bad)


# ---- development villa (committed, sha-pinned files) --------------------------------------------------------------
@pytest.fixture(scope="module")
def st():
    return A.build()


def test_dev_rebuild_equals_committed(st):
    committed = json.loads(A.JSON_OUT.read_text(encoding="utf-8"))
    assert json.loads(json.dumps(st, sort_keys=True)) == committed
    assert A.MD_OUT.read_text(encoding="utf-8") == A.to_markdown(st)


def test_dev_counts_and_packs(st):
    t = st["tables"]
    assert (t["B10"]["n"], t["B11"]["n"], t["B1"]["n"]) == (59, 13, 19)
    assert t["B10"]["n_by_class"] == {"VERIFIED_ON_RECORD": 10, "CLOSABLE_FROM_DRAWINGS": 30, "DESIGNER_ITEM": 19,
                                      "OWNER_RULE_GAP": 0}
    assert t["B1"]["n_by_class"]["OWNER_RULE_GAP"] == 3
    assert len(st["packs"]) >= 5
    for c in st["components"]:
        R.check_component(c)
        if c["closure_class"] == "CLOSABLE_FROM_DRAWINGS":
            assert c["pack"] in st["packs"]
    assert t["B10"]["quantity_added_across_sources"] is False


def test_dev_sections_readd_to_statement(st):
    v6 = json.loads(A.SOURCES["V6"][0].read_text(encoding="utf-8"))
    secs = {s["section_id"]: s for k in ("sections", "sections_v5") for s in v6[k]}
    for sid in ("T-545/beams", "T-551/columns", "T-551/footing-line", "T-560/rebar"):
        got = sum(D(c["quantity"]["value"]) for c in st["components"] if c["source"] == sid)
        assert got == D(secs[sid]["difference"])


def test_dev_f_c_t583_1_restated(st):
    r = st["restatement_F_C_T583_1"]
    assert r["east_row_low_t"] == ["0.122518", "0.144289"]
    assert r["bounded_rows_low_t"] == ["0.767783", "0.789554"]
    assert r["side_bars_kg_low"] == ["21.771", "43.543"]
    # 4 d14 over 8.9974 m in bay: 4 x 8.9974 x 196 / 162 = 43.543 kg (by hand)
    assert (4 * D("8.9974") * D(196) / D(162)).quantize(D("0.001")) == D("43.543")


def test_dev_findings_and_no_owner_question(st):
    ids = [f["id"] for f in st["findings"]]
    assert "F-T589-1" in ids and "F-T589-2" in ids
    f1 = [f for f in st["findings"] if f["id"] == "F-T589-1"][0]
    assert "2.176000 -> 1.960" in f1["quantity"]
    assert (D("2.80") * D("1.40") * D("0.50")) == D("1.960")
    assert all(f["owner_question"].startswith("none") for f in st["findings"])
    assert not any(c.get("owner_question") for c in st["components"])


def test_dev_unclassified_component_refused(monkeypatch):
    cat = dict(A.CAT)
    cat.pop(("T-551/columns", "columns GF: BASE"))
    monkeypatch.setattr(A, "CAT", cat)
    with pytest.raises(R.ClassError):
        A.build()


def test_dev_source_hash_pinned(monkeypatch):
    src = dict(A.SOURCES)
    p, _ = src["V6"]
    src["V6"] = (p, "0" * 64)
    monkeypatch.setattr(A, "SOURCES", src)
    with pytest.raises(R.ClassError):
        A.build()
