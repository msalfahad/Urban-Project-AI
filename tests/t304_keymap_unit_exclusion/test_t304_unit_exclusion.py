"""T-304: a candidate line in a unit no reference line can use is EXCLUDED with reason UNIT_NOT_IN_REFERENCE
(tools/alsenan_keymap.py, "T-304"); it never stops the whole run, is never converted, summed or scored.

Synthetic villa N304 (not Alsenan); hand calculation written before the run:

  CONCRETE m3, reference CONC 5.500
    C1 footing F1   2.00 x 2.00 x 0.50 = 2.000   MEASURED
    C2 footing F2   2.00 x 2.00 x 0.50 = 2.000   MEASURED
    C3 strap S1     6.00 x 0.40 x 0.50 = 1.200   SOURCE_DERIVED
    engine 5.200, error -0.300, WAPE 0.300 / 5.500 = 0.054545
  FLOOR_AREA m2, reference FLR 120.000
    F1 living 8.00 x 10.00 = 80.000 MEASURED
    F2 bath   2.50 x 3.00  =  7.500 BLOCKED_RFI, measured_net blank -> the key is HELD, never 80.000, never 0
  WATERPROOFING m2, reference WP 60.000
    W1 membrane 6.00 x 8.00 = 48.000 MEASURED
    W2 WP.FOUNDATION.PROCUREMENT 'item' BLOCKED_RFI blank, no key       -> excluded UNIT_NOT_IN_REFERENCE, unmapped
    W3 WP.MEMBRANE in 'item', 3 (rolls), keyed by item code into the m2 key -> excluded, key named, never 3 m2
    WP compared on W1 alone: 48.000 vs 60.000, error -12.000
  REBAR t, reference RB 2.000
    R1 1,850.0 kg  -> refused (kg is not t; never 1.850 t here: kg -> t belongs to the export boundary)
    R2 1.850 t     -> compared, error -0.150
Before T-304 the 'item' lines stopped engine_rows + score with "unknown unit 'item'" (F-SCORE-01).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools import alsenan_keymap as K
from tools import alsenan_scoreboard as S

TOL = 1e-6


def ln(lid, code, net, ev="MEASURED", unit="m3", el=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "evidence_state": ev, "measured_net": net,
            "trade": "X", "location": {"element_id": el or f"{lid}:el", "room_id": None},
            "calculation": {"inputs": {}}}


def villa():
    return [
        ln("C1", "STR.CONC.FOOTING", 2.0 * 2.0 * 0.5),
        ln("C2", "STR.CONC.FOOTING", 2.0 * 2.0 * 0.5),
        ln("C3", "STR.CONC.STRAP", 6.0 * 0.4 * 0.5, "SOURCE_DERIVED"),
        ln("F1", "FIN.FLOOR.PORCELAIN", 8.0 * 10.0, unit="m2"),
        ln("F2", "FIN.FLOOR.WET_TILE", None, "BLOCKED_RFI", unit="m2"),
        ln("W1", "WP.MEMBRANE", 6.0 * 8.0, unit="m2"),
        ln("W2", "WP.FOUNDATION.PROCUREMENT", None, "BLOCKED_RFI", unit="item"),
        ln("W3", "WP.MEMBRANE", 3.0, unit="item"),
        ln("R2", "STR.REBAR.MAIN", 1.85, unit="t"),
    ]


def km():
    return {"SCHEMA": "URBAN_ALSENAN_KEY_MAP_V1", "keys": [
        {"key": "CONC", "trade": "CONCRETE", "reference_id": "CONC", "item_codes": ["STR.CONC.FOOTING", "STR.CONC.STRAP"]},
        {"key": "FLR", "trade": "FLOOR_AREA", "reference_id": "FLR",
         "item_codes": ["FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE"]},
        {"key": "WP", "trade": "WATERPROOFING", "reference_id": "WP", "item_codes": ["WP.MEMBRANE"]},
        {"key": "RB", "trade": "REBAR", "reference_id": "RB", "item_codes": ["STR.REBAR.MAIN", "STR.REBAR.KG"]}]}


REF = [{"id": "CONC", "trade": "CONCRETE", "unit": "m3", "qty": 5.5, "key": "CONC"},
       {"id": "FLR", "trade": "FLOOR_AREA", "unit": "m2", "qty": 120.0, "key": "FLR"},
       {"id": "WP", "trade": "WATERPROOFING", "unit": "m2", "qty": 60.0, "key": "WP"},
       {"id": "RB", "trade": "REBAR", "unit": "t", "qty": 2.0, "key": "RB"}]


def scored(lines, kmd=None):
    rows, rep = K.engine_rows(lines, None, kmd or km())
    res = S.score(rows, REF)
    return {x["ref_id"]: x for x in res["lines"]}, rows, rep, res


def test_before_t304_an_item_line_stopped_the_whole_score():
    # the scorer itself is unchanged and still refuses the unit: the map must keep such a line out of its rows
    with pytest.raises(ValueError, match="unknown unit 'item'"):
        S.score([{"id": "W2", "trade": "X", "unit": "item", "qty": None, "status": "HELD", "key": None}], REF)


def test_normal_villa_scores_every_trade_and_lists_the_item_lines():
    by, rows, rep, res = scored(villa())
    c = by["CONC"]
    assert c["outcome"] == S.OUT_COMPARED and abs(c["engine_qty"] - 5.2) < TOL and abs(c["signed_error"] + 0.3) < TOL
    b = {(x["trade"], x["unit"]): x for x in res["buckets"]}
    assert abs(b[("CONCRETE", "m3")]["wape"] - 0.3 / 5.5) < TOL
    assert by["FLR"]["outcome"] == S.OUT_HELD and by["FLR"]["engine_qty"] is None
    w = by["WP"]
    assert w["outcome"] == S.OUT_COMPARED and w["engine_ids"] == ["W1"] and abs(w["signed_error"] + 12.0) < TOL
    assert by["RB"]["outcome"] == S.OUT_COMPARED and abs(by["RB"]["signed_error"] + 0.15) < TOL
    ex = rep["excluded_unit_not_in_reference"]
    assert [x["line_id"] for x in ex] == ["W2", "W3"]
    assert all(x["reason"] == K.UNIT_NOT_IN_REFERENCE and x["unit"] == "item" for x in ex)
    w2, w3 = ex
    assert w2 == {"line_id": "W2", "item_code": "WP.FOUNDATION.PROCUREMENT", "unit": "item", "measured_net": None,
                  "evidence_state": "BLOCKED_RFI", "scorer_class": "HELD", "key": None, "reason": "UNIT_NOT_IN_REFERENCE"}
    assert w3["key"] == "WP" and w3["measured_net"] == 3.0 and w3["scorer_class"] == "RELEASED"
    assert rep["keys_with_unit_excluded_lines"] == ["WP"]
    assert not {"W2", "W3"} & {r["id"] for r in rows}
    # the excluded lines are no unmapped engine rows and no false positives (they are not rows at all)
    assert res["false_positives"] == [] and all(u["unit"] != "item" for u in rep["unmapped_by_item"])


def test_item_line_keyed_into_an_m2_reference_is_never_summed_into_it():
    by = scored(villa())[0]
    assert abs(by["WP"]["engine_qty"] - 48.0) < TOL          # never 48 + 3 = 51
    only = [x for x in villa() if x["line_id"] != "W1"]
    by2, _, rep2, _ = scored(only)
    assert by2["WP"]["outcome"] == S.OUT_SILENT and by2["WP"]["engine_qty"] is None   # never 3 m2, never 0
    assert rep2["keys_with_unit_excluded_lines"] == ["WP"]


def test_no_unknown_unit_keeps_the_report_byte_identical():
    base = [x for x in villa() if x["unit"] != "item"]
    rows_a, rep_a = K.engine_rows(base, None, km())
    rows_b, rep_b = K.engine_rows(villa(), None, km())
    assert "excluded_unit_not_in_reference" not in rep_a and "keys_with_unit_excluded_lines" not in rep_a
    assert rows_a == rows_b
    rep_b = {k: v for k, v in rep_b.items() if k not in ("excluded_unit_not_in_reference",
                                                         "keys_with_unit_excluded_lines")}
    assert json.dumps(rep_a, sort_keys=True) == json.dumps(rep_b, sort_keys=True)
    assert K.unit_excluded_markdown([("A", rep_a)]) == ""


def test_kg_and_t_are_never_mixed_or_converted():
    v = villa() + [ln("R1", "STR.REBAR.KG", 1850.0, unit="kg")]
    by, _, rep, _ = scored(v)
    assert by["RB"]["refused_engine_ids"] == ["R1"] and abs(by["RB"]["engine_qty"] - 1.85) < TOL
    assert "R1" not in [x["line_id"] for x in rep["excluded_unit_not_in_reference"]]   # kg is a scorer unit
    kg_only = [x for x in v if x["line_id"] != "R2"]
    assert scored(kg_only)[0]["RB"]["outcome"] == S.OUT_UNIT_MISMATCH                  # never 1.850 t


def test_held_lines_are_never_scored_as_a_value():
    v = villa()
    v[7] = ln("W3", "WP.MEMBRANE", None, "BLOCKED_RFI", unit="item")
    by, rows, rep, _ = scored(v)
    w3 = [x for x in rep["excluded_unit_not_in_reference"] if x["line_id"] == "W3"][0]
    assert w3["measured_net"] is None and w3["scorer_class"] == "HELD"
    f2 = [r for r in rows if r["id"] == "F2"][0]
    assert f2["status"] == "HELD" and f2["qty"] is None and by["FLR"]["engine_qty"] is None


def test_excluded_state_wins_before_the_unit_check():
    v = villa()
    v[6] = ln("W2", "WP.FOUNDATION.PROCUREMENT", None, "NOT_APPLICABLE_WITH_EVIDENCE", unit="item")
    v[7] = ln("W3", "WP.MEMBRANE", None, "EXCLUDED_WITH_REASON", unit="item")
    _, _, rep, _ = scored(v)
    assert "excluded_unit_not_in_reference" not in rep and rep["excluded_lines_by_key"] == {"WP": 1}


def test_other_unknown_units_and_blank_units():
    v = villa() + [ln("Z1", "MISC.SET", 2.0, unit="set"), ln("Z2", "MISC.LS", 1.0, unit="L.S.")]
    _, _, rep, _ = scored(v)
    assert [x["line_id"] for x in rep["excluded_unit_not_in_reference"]] == ["W2", "W3", "Z1", "Z2"]
    # an absent unit is the scorer's own '(missing)' bucket, not an exclusion (path unchanged)
    assert K.scorer_unit_known(None) and K.scorer_unit_known("") and K.scorer_unit_known(" M² ")
    assert not K.scorer_unit_known("item") and not K.scorer_unit_known("lump sum")


def test_line_order_and_mirror_change_nothing():
    a = scored(villa())
    rev = list(reversed(copy.deepcopy(villa())))
    for x in rev:
        x["location"]["element_id"] = "mirror:" + x["location"]["element_id"]
    b = scored(rev)
    assert a[2]["excluded_unit_not_in_reference"] == b[2]["excluded_unit_not_in_reference"]
    for k in ("CONC", "FLR", "WP", "RB"):
        assert a[0][k]["outcome"] == b[0][k]["outcome"] and a[0][k]["engine_qty"] == b[0][k]["engine_qty"]


def test_typed_v2_map_takes_the_same_exclusion():
    kmd = km()
    kmd["SCHEMA"] = K.KEY_MAP_V2_SCHEMA
    kmd["typed_records"] = ["floor_scope_v3014"]
    kmd["keys"][1]["typed_lines"] = [{"item_code": "ARCH.SPACE", "field": "floor_key", "equals": "FLOOR.INTERNAL",
                                      "source": "synthetic"}]
    v = villa()
    s = ln("S1", "ARCH.SPACE", 1.0, "PROVISIONAL", unit="item")
    s["calculation"]["inputs"]["floor_scope_v3014"] = {"floor_key": "FLOOR.INTERNAL"}
    v.append(s)
    _, _, rep, _ = scored(v, kmd)
    s1 = [x for x in rep["excluded_unit_not_in_reference"] if x["line_id"] == "S1"][0]
    assert s1["key"] == "FLR" and rep["keys_with_unit_excluded_lines"] == ["FLR", "WP"]


def _write_run(tmp_path, lines):
    run = tmp_path / "run"
    run.mkdir()
    (run / "BOQ_LINES.json").write_text(json.dumps(lines), encoding="utf-8")
    ref = {"records": [dict(r, row_kind="COVER_TOTAL") for r in REF]}
    (tmp_path / "ref.json").write_text(json.dumps(ref), encoding="utf-8")
    (tmp_path / "km.json").write_text(json.dumps(km()), encoding="utf-8")
    return run


def test_cli_run_and_candidate_side_list_the_exclusions(tmp_path):
    run = _write_run(tmp_path, [x for x in villa() if x["unit"] != "item"])
    cand = tmp_path / "CAND_BOQ_LINES.json"
    cand.write_text(json.dumps(villa()), encoding="utf-8")
    (tmp_path / "v.json").write_text(json.dumps({"schema": "URBAN_SCOREBOARD_CHECKER_VERDICTS_V1", "verdicts": []}),
                                     encoding="utf-8")
    out, md, v2, v2md = (tmp_path / n for n in ("o.json", "o.md", "v2.json", "v2.md"))
    rc = K.main(["--run", str(run), "--reference", str(tmp_path / "ref.json"), "--key-map", str(tmp_path / "km.json"),
                 "--out", str(out), "--markdown", str(md), "--v2-out", str(v2), "--v2-markdown", str(v2md),
                 "--v2-label", "A", "--v2-verdicts", str(tmp_path / "v.json"), "--v2-candidate-lines", str(cand),
                 "--v2-candidate-label", "CAND"])
    assert rc == 0
    assert "UNIT_NOT_IN_REFERENCE" not in md.read_text(encoding="utf-8")        # the run side has no such line
    assert "excluded_unit_not_in_reference" not in json.loads(out.read_text(encoding="utf-8"))["adapter"]
    t = v2md.read_text(encoding="utf-8")
    assert "| CAND | W2 | WP.FOUNDATION.PROCUREMENT | item | blank | BLOCKED_RFI | unmapped |" in t
    assert "| CAND | W3 | WP.MEMBRANE | item | 3.000000 | MEASURED | WP |" in t
    sides = json.loads(v2.read_text(encoding="utf-8"))["sides"]
    assert [x["line_id"] for x in sides[1]["adapter"]["excluded_unit_not_in_reference"]] == ["W2", "W3"]
    assert "excluded_unit_not_in_reference" not in sides[0]["adapter"]
