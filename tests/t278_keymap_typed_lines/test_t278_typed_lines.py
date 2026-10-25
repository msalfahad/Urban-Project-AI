"""T-278: key map V2 (URBAN_ALSENAN_KEY_MAP_V2) keys typed lines by what they ARE (tools/alsenan_keymap.py, "T-278:
typed lines"); key map V1 (T001B) unchanged. Synthetic villa, not Alsenan; hand calculation written before the run:

  FLOOR_AREA m2, reference FLR 55.000 (the villa's internal floor)
    F1 living  FIN.FLOOR.PORCELAIN  MEASURED        42.500
    F2 bath    FIN.FLOOR.WET_TILE   SOURCE_DERIVED   6.300
    S1 dressing ARCH.SPACE typed floor_key FLOOR.INTERNAL, PROVISIONAL 1.75 x 1.80 = 3.150
    S2 hall    ARCH.SPACE untyped (geometry record of F1's room)       12.000 -> never keyed
    S3 terrace ARCH.SPACE typed FLOOR.OUTDOOR                          4.800 -> never internal
  V1 map: 42.500 + 6.300 = 48.800, error -6.200, WAPE 6.200 / 55 = 0.112727
  V2 map: 42.500 + 6.300 + 3.150 = 51.950, error -3.050, WAPE 3.050 / 55 = 0.055455 (S1 keyed once)
  coverage V2: ARCH.SPACE m2 3 lines: 1 keyed FLOOR.INTERNAL (typed), 2 unkeyed (untyped 1, FLOOR.OUTDOOR 1); 0 double
Adverse: a typed internal line HELD (range) -> the key HELD, never a partial sum; a typed line with no measured_net ->
HELD, never 0; a typed line in mm -> refused unit, never converted; a typed line NOT_APPLICABLE -> excluded; a selector
code that is also a plain item code -> refused at load; a line two keys claim -> refused; records disagreeing on the
type -> refused; a selector without its source -> refused; mirrored / rotated geometry changes nothing (keying reads the
type record, not coordinates).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools import alsenan_keymap as K
from tools import alsenan_scoreboard as S

ROOT = Path(__file__).resolve().parents[2]
TOL = 1e-6


def ln(lid, code, net, ev="MEASURED", fk=None, unit="m2", room=None, rec="floor_scope_v3014", extra=None):
    d = {"line_id": lid, "item_code": code, "unit": unit, "evidence_state": ev, "measured_net": net, "trade": "X",
         "location": {"element_id": f"{lid}:el", "room_id": room}, "calculation": {"inputs": {}}}
    if fk is not None:
        d["calculation"]["inputs"][rec] = {"kind": "ENTER_FLOOR", "floor_key": fk}
    if extra:
        d["calculation"]["inputs"].update(extra)
    return d


def villa():
    return [ln("F1", "FIN.FLOOR.PORCELAIN", 42.5), ln("F2", "FIN.FLOOR.WET_TILE", 6.3, "SOURCE_DERIVED"),
            ln("S1", "ARCH.SPACE", 3.15, "PROVISIONAL", "FLOOR.INTERNAL"), ln("S2", "ARCH.SPACE", 12.0),
            ln("S3", "ARCH.SPACE", 4.8, fk="FLOOR.OUTDOOR")]


def km_v1():
    return {"SCHEMA": "URBAN_ALSENAN_KEY_MAP_V1", "keys": [
        {"key": "FLOOR.INTERNAL", "trade": "FLOOR_AREA", "reference_id": "FLR",
         "item_codes": ["FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE"]}]}


def km_v2():
    d = km_v1()
    d["SCHEMA"] = K.KEY_MAP_V2_SCHEMA
    d["typed_records"] = ["floor_scope_v3014"]
    d["keys"][0]["typed_lines"] = [{"item_code": "ARCH.SPACE", "field": "floor_key", "equals": "FLOOR.INTERNAL",
                                    "source": "synthetic"}]
    return d


REF = [{"id": "FLR", "trade": "FLOOR_AREA", "unit": "m2", "qty": 55.0, "key": "FLOOR.INTERNAL"}]


def scored(lines, km):
    rows, rep = K.engine_rows(lines, None, km)
    res = S.score(rows, REF)
    return res["lines"][0], rows, rep, res


def test_v1_does_not_key_typed_space_lines():
    line, rows, rep, _ = scored(villa(), km_v1())
    assert line["outcome"] == S.OUT_COMPARED
    assert abs(line["engine_qty"] - 48.8) < TOL and abs(line["signed_error"] + 6.2) < TOL
    assert sorted(line["engine_ids"]) == ["F1", "F2"]
    assert "coverage" not in rep
    assert rep["unmapped_by_item"] == [{"item_code": "ARCH.SPACE", "unit": "m2", "lines": 3}]


def test_v2_keys_the_typed_internal_space_once():
    line, rows, rep, res = scored(villa(), km_v2())
    assert line["outcome"] == S.OUT_COMPARED
    assert abs(line["engine_qty"] - 51.95) < TOL and abs(line["signed_error"] + 3.05) < TOL
    assert sorted(line["engine_ids"]) == ["F1", "F2", "S1"]
    assert abs(res["buckets"][0]["wape"] - 3.05 / 55.0) < 1e-9
    assert rep["unmapped_by_item"] == [{"item_code": "ARCH.SPACE", "unit": "m2", "lines": 2}]
    fam = {f["item_code"]: f for f in rep["coverage"]["families"]}
    assert fam["ARCH.SPACE"]["keyed"] == {"FLOOR.INTERNAL (typed)": 1}
    assert fam["ARCH.SPACE"]["unkeyed_by_typed_value"] == {"untyped": 1, "FLOOR.OUTDOOR": 1}
    assert fam["FIN.FLOOR.PORCELAIN"]["keyed"] == {"FLOOR.INTERNAL (item_code)": 1}
    assert rep["coverage"]["double_keyed_lines"] == 0
    assert all(f["double_keyed"] == 0 for f in rep["coverage"]["families"])
    assert [r["id"] for r in rows if r["key"] == "FLOOR.INTERNAL"].count("S1") == 1


def test_mirror_and_rotation_change_nothing():
    a = villa()
    b = copy.deepcopy(a)[::-1]                # another order, mirrored element ids
    for x in b:
        x["location"]["element_id"] = x["location"]["element_id"][::-1]
    assert abs(scored(a, km_v2())[0]["engine_qty"] - scored(b, km_v2())[0]["engine_qty"]) < TOL


def test_held_typed_internal_line_holds_the_key_never_a_partial_sum():
    v = villa()
    v[2] = ln("S1", "ARCH.SPACE", 3.15, "BOUNDED_EXPOSURE", "FLOOR.INTERNAL")
    line = scored(v, km_v2())[0]
    assert line["outcome"] == S.OUT_HELD and line["engine_qty"] is None and "S1" in line["engine_ids"]


def test_missing_quantity_is_held_never_zero():
    v = villa()
    v[2] = ln("S1", "ARCH.SPACE", None, "PROVISIONAL", "FLOOR.INTERNAL")
    line, rows, _, _ = scored(v, km_v2())
    assert line["outcome"] == S.OUT_HELD
    assert [r for r in rows if r["id"] == "S1"][0]["qty"] is None


def test_typed_line_in_mm_is_refused_never_converted():
    v = villa()
    v[2] = ln("S1", "ARCH.SPACE", 3150.0, "PROVISIONAL", "FLOOR.INTERNAL", unit="mm")
    line = scored(v, km_v2())[0]
    assert line["refused_engine_ids"] == ["S1"] and abs(line["engine_qty"] - 48.8) < TOL


def test_not_applicable_typed_line_is_excluded():
    v = villa()
    v[2] = ln("S1", "ARCH.SPACE", None, "NOT_APPLICABLE_WITH_EVIDENCE", "FLOOR.INTERNAL")
    line, _, rep, _ = scored(v, km_v2())
    assert rep["excluded_lines_by_key"] == {"FLOOR.INTERNAL": 1} and abs(line["engine_qty"] - 48.8) < TOL
    fam = {f["item_code"]: f for f in rep["coverage"]["families"]}
    assert fam["ARCH.SPACE"]["excluded"] == 1 and fam["ARCH.SPACE"]["keyed"] == {"FLOOR.INTERNAL (typed)": 1}


def test_selector_code_that_is_also_a_plain_code_is_refused():
    d = km_v2()
    d["keys"][0]["typed_lines"][0]["item_code"] = "FIN.FLOOR.PORCELAIN"
    with pytest.raises(ValueError, match="also a plain item code"):
        K.engine_rows(villa(), None, d)


def test_a_line_two_keys_claim_is_refused():
    d = km_v2()
    d["keys"].append({"key": "FLOOR.DRESSING", "trade": "FLOOR_AREA", "reference_id": "FLR2", "item_codes": [],
                      "typed_lines": [{"item_code": "ARCH.SPACE", "field": "zone", "equals": "DRESS",
                                       "source": "synthetic"}]})
    v = villa()
    v[2]["calculation"]["inputs"]["floor_scope_v3014"]["zone"] = "DRESS"
    with pytest.raises(ValueError, match="answers two keys"):
        K.engine_rows(v, None, d)


def test_records_disagreeing_on_the_type_are_refused():
    d = km_v2()
    d["typed_records"] = ["floor_scope_v3014", "floor_scope_v3099"]
    v = villa()
    v[2]["calculation"]["inputs"]["floor_scope_v3099"] = {"floor_key": "FLOOR.OUTDOOR"}
    with pytest.raises(ValueError, match="disagree"):
        K.engine_rows(v, None, d)


def test_selector_without_source_or_records_is_refused():
    d = km_v2()
    del d["keys"][0]["typed_lines"][0]["source"]
    with pytest.raises(ValueError, match="source"):
        K.engine_rows(villa(), None, d)
    d = km_v2()
    d["typed_records"] = []
    with pytest.raises(ValueError, match="typed records"):
        K.engine_rows(villa(), None, d)


def test_committed_t001c_is_t001b_plus_typed_lines_only():
    b = json.loads((ROOT / "tests/alsenan/T001B_KEY_MAP.json").read_text(encoding="utf-8"))
    c = json.loads((ROOT / "tests/alsenan/T001C_KEY_MAP.json").read_text(encoding="utf-8"))
    assert b["SCHEMA"] == "URBAN_ALSENAN_KEY_MAP_V1" and c["SCHEMA"] == K.KEY_MAP_V2_SCHEMA
    assert [k["key"] for k in b["keys"]] == [k["key"] for k in c["keys"]]
    for x, y in zip(b["keys"], c["keys"]):
        y = dict(y)
        sel = y.pop("typed_lines", None)
        assert x == y
        assert (sel is not None) == (x["key"] == "FLOOR.INTERNAL")
    by_item, _ = K.load_key_map(c)
    sels, recs = K.load_typed_selectors(c, by_item)
    assert [(k["key"], s["item_code"], s["field"], s["equals"]) for k, s in sels] == [
        ("FLOOR.INTERNAL", "ARCH.SPACE", "floor_key", "FLOOR.INTERNAL")]
    assert recs == ("floor_scope_v3014",)


def test_v1_key_map_on_v2_lines_reports_like_before():
    """the V1 path ignores type records altogether (released A and every T001B output unchanged)"""
    _, rows1, rep1, _ = scored(villa(), km_v1())
    v = villa()
    for x in v:
        x["calculation"]["inputs"].pop("floor_scope_v3014", None)
    _, rows2, rep2, _ = scored(v, km_v1())
    assert rows1 == rows2 and rep1 == rep2


def test_run_path_carries_the_coverage_report(tmp_path):
    (tmp_path / "BOQ_LINES.json").write_text(json.dumps(villa()), encoding="utf-8")
    norm = {"records": [{"id": "FLR", "unit": "m2", "qty": 55.0, "row_kind": "COVER_TOTAL"}]}
    r2 = K.run(tmp_path, norm, km_v2())
    r1 = K.run(tmp_path, norm, km_v1())
    assert abs(r2["lines"][0]["engine_qty"] - 51.95) < TOL and abs(r1["lines"][0]["engine_qty"] - 48.8) < TOL
    assert "coverage" in r2["adapter"] and "coverage" not in r1["adapter"]
