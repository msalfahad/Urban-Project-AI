"""M5 engine fix (Phase 8): planted columns labelled on a slab plan ('P.C 20x70') become columns of the storey above,
only under the M5 conventions (V4 = V3 + PLANTED_COLUMN_LABELS). V3 - the frozen M4 behaviour and the CLI default -
is unchanged."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.source import generic_route as GR          # noqa: E402
from engine.source import provisional_estimate as PE   # noqa: E402

V3 = ROOT / "engine/profiles/URBAN_M4_GENERIC_CONVENTIONS_V3.json"
V4 = ROOT / "engine/profiles/URBAN_M5_GENERIC_CONVENTIONS_V4.json"
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
ARCH = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"


def _conv(path):
    return PE.load_conventions(path)


def test_v4_is_v3_plus_one_convention_and_the_cli_default_stays_v3():
    a = {c["id"]: c for c in json.loads(V3.read_text())["conventions"]}
    b = {c["id"]: c for c in json.loads(V4.read_text())["conventions"]}
    assert set(b) - set(a) == {"PLANTED_COLUMN_LABELS"} and set(a) <= set(b)
    assert all(a[k] == b[k] for k in a)
    from tools import urban_boq_m2 as CLI
    assert CLI.GENERIC_CONVENTIONS.endswith("URBAN_M4_GENERIC_CONVENTIONS_V3.json")


def _model(texts, columns=()):
    """A minimal two-sheet model: a GF slab plan holding the labels, a column plan holding `columns`."""
    return {"unit_m": 0.001, "sheets": {
        "SH06": {"sheet": {"role": "SLAB_PLAN", "storey": "GF", "origin": (1000.0, 0.0)}, "texts": texts},
        "SH12": {"sheet": {"role": "COLUMN_PLAN", "storey": "ALL", "origin": (50000.0, 0.0)}, "columns": list(columns)},
    }}


def _run(D, conv, heights, occ=()):
    items, register, risk = [], [], []

    def reg(cid, fam, st, state, reason, kg=None):
        register.append({"COMPONENT_ID": cid, "FAMILY": fam, "STOREY": st, "REBAR_STATE": state, "REASON": reason})
    GR._planted_column_items(D, items, reg, risk, conv, heights, list(occ), "x.dxf", D["unit_m"])
    return items, register, risk


def test_label_section_times_the_storey_above():
    D = _model([{"id": "T1", "value": "P.C 20x70", "x": 5000.0, "y": 3000.0, "layer": "S-TEXT-SLAB"},
                {"id": "T2", "value": "PC 25 X 50", "x": 9000.0, "y": 3000.0, "layer": "S-TEXT-SLAB"},
                {"id": "T3", "value": "C 20x70", "x": 9000.0, "y": 8000.0, "layer": "S-TEXT-SLAB"}])
    items, register, risk = _run(D, _conv(V4), {"GF": 4.5, "1F": 4.2, "2F": 4.2})
    v = sorted(round(i["base"], 6) for i in items)
    assert v == sorted([round(0.2 * 0.7 * 4.2, 6), round(0.25 * 0.5 * 4.2, 6)])           # hand-derived; 'C 20x70' ignored
    assert all(i["storey"] == "1F" and i["category"] == "PROVISIONAL" and i["family"] == "COLUMNS" for i in items)
    assert all(r["REBAR_STATE"] == "MISSING_DATA" for r in register)              # bars never by ratio


def test_no_storey_above_is_unresolved_never_zero():
    D = _model([{"id": "T1", "value": "P.C 20x50", "x": 5000.0, "y": 3000.0}])
    D["sheets"]["SH06"]["sheet"]["storey"] = "2F"
    items, register, _ = _run(D, _conv(V4), {"GF": 4.5, "1F": 4.2, "2F": 4.2})
    assert len(items) == 1 and items[0]["category"] == "UNRESOLVED" and items[0]["base"] is None


def test_a_label_on_a_counted_column_is_not_counted_twice():
    D = _model([{"id": "T1", "value": "P.C 20x70", "x": 5000.0, "y": 3000.0}])
    occ = [{"piece_id": "C", "mark": "C1", "box": (53900.0, 2900.0, 54100.0, 3100.0), "sheet": "SH12"}]
    import engine.source.member_detection as MD
    orig = MD.column_storeys
    MD.column_storeys = lambda occ_, heights: [dict(o, storey="1F", state="MEASURED") for o in occ_]
    try:
        items, _, risk = _run(D, _conv(V4), {"GF": 4.5, "1F": 4.2}, occ)
    finally:
        MD.column_storeys = orig
    assert not items and risk and risk[0]["KIND"] == "PLANTED_COLUMN_ALREADY_COUNTED"


@pytest.mark.skipif(not (DXF.exists() and ARCH.exists()), reason="prerequisite: the private ST7757 drawings")
def test_st7757_v4_adds_exactly_the_three_planted_columns():
    from tools import urban_boq_m2 as CLI
    kw = dict(profile=str(ROOT / "research/urban_engine_m4_correctness/profile_st7757_m4.json"), route="G",
              evidence=str(ROOT / "research/urban_engine_m3_recovery/evidence/DETAIL_EVIDENCE.json"), arch=[str(ARCH)],
              evidence_review=str(ROOT / "research/urban_engine_m4_correctness/evidence/OCR_INDEPENDENT_READINGS.json"))
    a = {i["item_id"]: i for i in CLI.compute([str(DXF)], **kw)["items"]}
    b = {i["item_id"]: i for i in CLI.compute([str(DXF)], conventions=str(V4), **kw)["items"]}
    assert set(a) <= set(b)
    assert all(a[k]["base"] == b[k]["base"] and a[k].get("exposure_high") == b[k].get("exposure_high") for k in a)
    new = [b[k] for k in set(b) - set(a)]
    assert len(new) == 3 and {i["storey"] for i in new} == {"1F", "2F"}
    assert abs(sum(i["base"] for i in new) - (0.2 * 0.7 * 4.2 + 2 * 0.2 * 0.5 * 4.2)) < 1e-9
