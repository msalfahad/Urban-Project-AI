"""T-452: the project-agnostic scoreboard (tools/project_scoreboard.py).

Synthetic villa N452 (not the training villa; no client data). Hand calculation written before the run:

  CONCRETE m3                         reference   engine                                   variance (orig)
    CONC.FOOTING  R1                   20.000      L1 2.5x2.5x0.8 = 5.000 + L2 5.000
                                                   + L3 3.0x4.0x1.0 = 12.000 -> 22.000      +10.000 %
    CONC.SLAB     R2                   50.000      L4 10x12x0.2 = 24.000 + L5 24.000 = 48   -4.000 %
    trade/unit                         70.000      70.000                                    0.000 % -> OFFSETTING_ERRORS
    R8 'total concrete' 70.000 m3 is keyed by no key -> REFERENCE_ONLY (listed, never dropped)
    reconciled: CONC.SLAB VERIFIED 49.000 (STR.CONC.SLAB) -> (48 - 49) / 49 = -2.0408 %
                CONC.FOOTING VERIFIED but items FOOTING + STRAP != key's FOOTING -> SCOPE_MISMATCH, no %
  BLOCKWORK m2  BLOCK.200 R3          300.000      L6 50x3.0 = 150 + L7 49x3.0 = 147 = 297   -1.000 %
                reconciled 296.000 'PARTIALLY VERIFIED' -> NOT_VERIFIED: no reconciled %, the original NOT substituted
  PLASTER m2    R4                      0.000      L8 10x3 = 30.000                          ZERO_REFERENCE (no %, |d| 30)
  WATERPROOFING m2 R5                 120.000      no line                                   REFERENCE_ONLY
  PAINT m2      R6                    400.000      L9 NOT_APPLICABLE_WITH_EVIDENCE           SCOPE_MISMATCH
  REBAR t       R7                      5.000      L10 4,800 kg                              SCOPE_MISMATCH (unit refused)
  FLOOR m2      R9                    100.000      L11 8x10 = 80 + L12 BLOCKED_RFI blank     HELD (never 80, never 0)
  ENGINE_ONLY: L13 MEP.PIPE 25 lm (no key); L14 WP.FOUNDATION.PROCUREMENT in 'item' (UNIT_NOT_IN_REFERENCE)
  Cost, basis B1 (approved): footing 30 / m3, slab 30 / m3, block 5 / m2, plaster 2 / m2
    CONCRETE: reference 20x30 + 50x30 = 2,100; engine 22x30 + 48x30 = 2,100 -> 0.000 %
              reconciled (slab only): 49x30 = 1,470 vs 48x30 = 1,440 -> -2.0408 %
    BLOCKWORK: 300x5 = 1,500 vs 297x5 = 1,485 -> -1.000 %
    basis B2 without the block rate -> BLOCKWORK INCOMPLETE_PRICING (no figure), CONCRETE still 0.000 %
"""

from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from tools import alsenan_keymap as K
from tools import project_scoreboard as P

TOL = 1e-6
PID = "synthetic-villa-n452"


def ln(lid, code, net, unit="m3", ev="MEASURED", el=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "evidence_state": ev, "measured_net": net,
            "location": {"element_id": el or lid}}


LINES = [
    ln("L1", "STR.CONC.FOOTING", 5.0), ln("L2", "STR.CONC.FOOTING", 5.0),
    ln("L3", "STR.CONC.FOOTING", 12.0, ev="SOURCE_DERIVED"),
    ln("L4", "STR.CONC.SLAB", 24.0), ln("L5", "STR.CONC.SLAB", 24.0),
    ln("L6", "MAS.BLOCK.200", 150.0, "m2"), ln("L7", "MAS.BLOCK.200", 147.0, "m2"),
    ln("L8", "FIN.PLASTER", 30.0, "m2"),
    ln("L9", "FIN.PAINT", None, "m2", ev="NOT_APPLICABLE_WITH_EVIDENCE"),
    ln("L10", "STR.REBAR", 4800.0, "kg"),
    ln("L11", "FIN.FLOOR.TILE", 80.0, "m2"), ln("L12", "FIN.FLOOR.TILE", None, "m2", ev="BLOCKED_RFI"),
    ln("L13", "MEP.PIPE", 25.0, "lm"),
    ln("L14", "WP.FOUNDATION.PROCUREMENT", None, "item", ev="BLOCKED_RFI"),
]


def rec(rid, trade, unit, qty, kind="COVER_TOTAL"):
    return {"id": rid, "trade": trade, "unit": unit, "qty": qty, "row_kind": kind}


REFERENCE = {"records": [
    rec("R1", "Concrete", "m3", 20.0), rec("R2", "Concrete", "m3", 50.0), rec("R3", "Block", "m2", 300.0),
    rec("R4", "Plaster", "m2", 0.0), rec("R5", "WP", "m2", 120.0), rec("R6", "Paint", "m2", 400.0),
    rec("R7", "Steel", "t", 5.0), rec("R8", "CONCRETE", "m3", 70.0), rec("R9", "Floor", "m2", 100.0),
    rec("R10", "Concrete", "m3", 1.5, kind="DETAIL")]}


def key(k, trade, rid, codes):
    return {"key": k, "trade": trade, "reference_id": rid, "item_codes": codes}


KEY_MAP = {"SCHEMA": P.KEY_MAP_SCHEMA, "project_id": PID, "reference_row_kinds": ["COVER_TOTAL"], "keys": [
    key("CONC.FOOTING", "CONCRETE", "R1", ["STR.CONC.FOOTING"]), key("CONC.SLAB", "CONCRETE", "R2", ["STR.CONC.SLAB"]),
    key("BLOCK.200", "BLOCKWORK", "R3", ["MAS.BLOCK.200"]), key("PLASTER", "PLASTER", "R4", ["FIN.PLASTER"]),
    key("WP.ROOF", "WATERPROOFING", "R5", ["WP.ROOF"]), key("PAINT", "PAINT", "R6", ["FIN.PAINT"]),
    key("REBAR", "REBAR", "R7", ["STR.REBAR"]), key("FLOOR", "FLOOR", "R9", ["FIN.FLOOR.TILE"])]}

RECONCILED = {"schema": P.RECONCILED_SCHEMA, "references": [
    {"line": "CONC.SLAB", "item_code": "STR.CONC.SLAB", "unit": "m3", "project_id": PID, "value": 49.0,
     "status": "VERIFIED (WHOLE line)"},
    {"line": "CONC.FOOTING", "item_codes": ["STR.CONC.FOOTING", "STR.CONC.STRAP"], "unit": "m3", "project_id": PID,
     "value": 21.0, "status": "VERIFIED (WHOLE line)"},
    {"line": "BLOCK.200", "item_code": "MAS.BLOCK.200", "unit": "m2", "project_id": PID, "value": 296.0,
     "status": "PARTIALLY VERIFIED (1 / 2 walls)"},
    {"line": "CONC.SLAB.OTHER", "item_code": "STR.CONC.SLAB", "unit": "m3", "project_id": "another-villa",
     "value": 10.0, "status": "VERIFIED (WHOLE line)"}]}

APPROVAL = {"by": "owner (synthetic)", "date": "2026-11-02", "source": "synthetic basis for the test"}
BASIS = {"SCHEMA": P.PRICING_SCHEMA, "basis_id": "B1", "currency": "KWD", "approval": APPROVAL, "rates": [
    {"key": "CONC.FOOTING", "unit": "m3", "rate": 30.0}, {"key": "CONC.SLAB", "unit": "m3", "rate": 30.0},
    {"key": "BLOCK.200", "unit": "m2", "rate": 5.0}, {"key": "PLASTER", "unit": "m2", "rate": 2.0}]}


def write_project(tmp, lines=LINES, km=KEY_MAP, reconciled=RECONCILED, basis=BASIS, extra=None):
    run = tmp / "run"
    run.mkdir(exist_ok=True)
    (run / "BOQ_LINES.json").write_text(json.dumps(lines), encoding="utf-8")
    files = {"reference.json": REFERENCE, "key_map.json": km}
    if reconciled is not None:
        files["reconciled.json"] = reconciled
    if basis is not None:
        files["basis.json"] = basis
    for n, d in files.items():
        (tmp / n).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    m = {"SCHEMA": P.MANIFEST_SCHEMA, "project_id": PID, "label": "Synthetic villa N452", "run": "run",
         "run_label": "run A", "reference": "reference.json", "key_map": "key_map.json",
         "high_value_keys": ["CONC.FOOTING", "CONC.SLAB", "REBAR"]}
    if reconciled is not None:
        m["reconciled_reference"] = "reconciled.json"
    if basis is not None:
        m["pricing_basis"] = "basis.json"
    m.update(extra or {})
    (tmp / "manifest.json").write_text(json.dumps(m), encoding="utf-8")
    return tmp / "manifest.json"


def build(tmp, **kw):
    return P.build(P.load_manifest(write_project(tmp, **kw)))


def by_key(side):
    return {g["key"]: g for g in side["goal_b"]["lines"]}


def bucket(side, trade, unit):
    return next(b for b in side["goal_b"]["trade_units"] if b["trade"] == trade and b["unit"] == unit)


# ---- reproduction: the generic path IS the training-villa scorer ----

def test_score_block_is_alsenan_keymap_byte_for_byte(tmp_path):
    legacy = dict(KEY_MAP, SCHEMA="URBAN_ALSENAN_KEY_MAP_V1")
    legacy.pop("project_id")
    mf = write_project(tmp_path, km=legacy)
    res = P.build(P.load_manifest(mf))
    o, md = tmp_path / "k.json", tmp_path / "k.md"
    K.main(["--run", str(tmp_path / "run"), "--reference", str(tmp_path / "reference.json"),
            "--key-map", str(tmp_path / "key_map.json"), "--out", str(o), "--markdown", str(md)])
    side = res["sides"][0]
    assert json.dumps(side["score"], ensure_ascii=False, indent=1) == o.read_text(encoding="utf-8")
    assert side["score_markdown"] == md.read_text(encoding="utf-8")
    assert res["key_map"] == "legacy URBAN_ALSENAN_KEY_MAP_V1"


def test_generic_key_map_scores_like_the_legacy_one(tmp_path):
    (tmp_path / "a").mkdir()
    a = build(tmp_path / "a")
    legacy = dict(KEY_MAP, SCHEMA="URBAN_ALSENAN_KEY_MAP_V1")
    (tmp_path / "b").mkdir()
    b = build(tmp_path / "b", km=legacy)
    assert a["sides"][0]["score"] == b["sides"][0]["score"]


# ---- the synthetic second project, scored by the CLI with no code change ----

def test_second_project_through_the_cli(tmp_path, capsys):
    mf = write_project(tmp_path)
    out, md = tmp_path / "o.json", tmp_path / "o.md"
    assert P.main(["--manifest", str(mf), "--out", str(out), "--markdown", str(md)]) == 0
    res = json.loads(out.read_text(encoding="utf-8"))
    s = res["sides"][0]
    g = by_key(s)
    assert g["CONC.FOOTING"]["engine_qty"] == pytest.approx(22.0, abs=TOL)
    assert g["CONC.FOOTING"]["original"]["variance_pct"] == pytest.approx(10.0, abs=1e-4)
    assert g["CONC.SLAB"]["original"]["variance_pct"] == pytest.approx(-4.0, abs=1e-4)
    assert g["BLOCK.200"]["original"]["variance_pct"] == pytest.approx(-1.0, abs=1e-4)
    assert g["BLOCK.200"]["original"]["within_tolerance"] is True
    c = bucket(s, "CONCRETE", "m3")
    assert (c["sum_reference"], c["sum_engine"], c["variance_original_pct"]) == (70.0, 70.0, 0.0)
    assert c["offsetting_errors"] is True and sorted(c["lines_outside_tolerance"]) == ["CONC.FOOTING", "CONC.SLAB"]
    assert c["complete"] is False                 # R8 REFERENCE_ONLY sits in the same trade and unit
    text = md.read_text(encoding="utf-8")
    assert "OFFSETTING_ERRORS" in text and "| CONCRETE | m3 |" in text
    assert res["project_id"] == PID and res["key_map"] == P.KEY_MAP_SCHEMA


def test_both_variances_and_reconciled_never_substituted(tmp_path):
    s = build(tmp_path)["sides"][0]
    g = by_key(s)
    assert g["CONC.SLAB"]["reconciled"]["status"] == P.REC_USED
    assert g["CONC.SLAB"]["reconciled"]["variance_pct"] == pytest.approx(100.0 * (48 - 49) / 49, abs=1e-4)
    assert g["CONC.FOOTING"]["reconciled"]["status"] == P.SCOPE_MISMATCH
    assert g["CONC.FOOTING"]["reconciled"]["variance_pct"] is None
    assert g["CONC.FOOTING"]["reconciled"]["exception"] == P.SCOPE_MISMATCH
    assert g["BLOCK.200"]["reconciled"]["status"] == P.REC_NOT_VERIFIED
    assert g["BLOCK.200"]["reconciled"]["qty"] is None and g["BLOCK.200"]["reconciled"]["variance_pct"] is None
    assert g["PLASTER"]["reconciled"]["status"] == P.REC_NONE
    c = bucket(s, "CONCRETE", "m3")
    assert c["rec_compared"] == 1 and c["variance_reconciled_pct"] == pytest.approx(-2.0408, abs=1e-4)
    assert [u["reason"] for u in s["goal_b"]["reconciled_unused"]] == [P.REC_FOREIGN]


# ---- exception classes: never a division by zero, never a silent drop ----

def test_exception_classes(tmp_path):
    s = build(tmp_path)["sides"][0]
    g = by_key(s)
    assert g["PLASTER"]["exception"] == P.ZERO_REFERENCE
    assert g["PLASTER"]["original"]["variance_pct"] is None and g["PLASTER"]["engine_qty"] == 30.0
    assert g["WP.ROOF"]["exception"] == P.REFERENCE_ONLY
    assert g["PAINT"]["exception"] == P.SCOPE_MISMATCH and "excludes" in g["PAINT"]["exception_reason"]
    assert g["REBAR"]["exception"] == P.SCOPE_MISMATCH and g["REBAR"]["outcome"] == "UNIT_MISMATCH"
    ex = s["goal_b"]["exceptions"]
    ro = [e for e in ex if e["exception"] == P.REFERENCE_ONLY]
    assert sorted(e.get("key") or e.get("ref_id") for e in ro) == ["R8", "WP.ROOF"]     # R10 (DETAIL) not keyed kind
    eo = [e for e in ex if e["exception"] == P.ENGINE_ONLY]
    assert sorted(e["item_code"] for e in eo) == ["MEP.PIPE", "WP.FOUNDATION.PROCUREMENT"]
    cnt = s["goal_b"]["exception_counts"]
    assert cnt == {P.ZERO_REFERENCE: 1, P.ENGINE_ONLY: 2, P.REFERENCE_ONLY: 2, P.SCOPE_MISMATCH: 3}
    # every reference row of the keyed kinds and every engine line is accounted for
    keyed_refs = {g["ref_id"] for g in s["goal_b"]["lines"]} | {e["ref_id"] for e in ro if "ref_id" in e}
    assert keyed_refs == {f"R{i}" for i in range(1, 10)}


def test_held_is_never_zero_or_a_partial_sum(tmp_path):
    s = build(tmp_path)["sides"][0]
    f = by_key(s)["FLOOR"]
    assert f["outcome"] == "HELD" and f["engine_qty"] is None and f["original"]["variance_pct"] is None
    b = bucket(s, "FLOOR", "m2")
    assert b["held"] == 1 and b["compared"] == 0 and b["variance_original_pct"] is None and b["complete"] is False
    assert b["sum_reference"] is None and b["sum_engine"] is None        # nothing compared: no sum, never 0


def test_zero_reference_trade_has_no_percentage(tmp_path):
    s = build(tmp_path)["sides"][0]
    b = bucket(s, "PLASTER", "m2")
    assert b["compared"] == 0 and b["variance_original_pct"] is None and b["exceptions"][P.ZERO_REFERENCE] == 1
    assert by_key(s)["PLASTER"]["cost"]["reference_cost"] == 0.0     # 0 x 2.00: a zero, never a division


# ---- cost: one approved basis, same rate both sides ----

def test_cost_variance(tmp_path):
    s = build(tmp_path)["sides"][0]
    cost = {c["trade"]: c for c in s["goal_b"]["trade_cost"]}
    assert cost["CONCRETE"]["status"] == P.PRICED
    assert (cost["CONCRETE"]["reference_cost"], cost["CONCRETE"]["engine_cost"]) == (2100.0, 2100.0)
    assert cost["CONCRETE"]["variance_original_pct"] == 0.0
    assert cost["CONCRETE"]["variance_reconciled_pct"] == pytest.approx(100.0 * (1440 - 1470) / 1470, abs=1e-4)
    assert cost["BLOCKWORK"]["variance_original_pct"] == pytest.approx(-1.0, abs=1e-4)
    assert cost["PLASTER"]["compared_keys"] == 0 and cost["PLASTER"]["variance_original_pct"] is None


def test_incomplete_and_missing_pricing(tmp_path):
    b2 = copy.deepcopy(BASIS)
    b2["rates"] = [r for r in b2["rates"] if r["key"] != "BLOCK.200"]
    (tmp_path / "a").mkdir()
    cost = {c["trade"]: c for c in build(tmp_path / "a", basis=b2)["sides"][0]["goal_b"]["trade_cost"]}
    assert cost["BLOCKWORK"]["status"] == P.INCOMPLETE_PRICING and cost["BLOCKWORK"]["engine_cost"] is None
    assert cost["BLOCKWORK"]["unpriced_keys"] == ["BLOCK.200"]
    assert cost["CONCRETE"]["variance_original_pct"] == 0.0
    (tmp_path / "b").mkdir()
    cost = build(tmp_path / "b", basis=None)["sides"][0]["goal_b"]["trade_cost"]
    assert {c["status"] for c in cost} == {P.NO_BASIS} and all(c["engine_cost"] is None for c in cost)
    assert all(c["unpriced_keys"] == [] for c in cost)      # no basis: the status says it, no key list implied


@pytest.mark.parametrize("mutate,msg", [
    (lambda b: b["approval"].pop("date"), "approval date"),
    (lambda b: b["rates"][0].update(unit="m2"), "never converted"),
    (lambda b: b["rates"].append({"key": "CONC.SLAB", "unit": "m3", "rate": 1.0}), "priced twice"),
    (lambda b: b["rates"][0].update(rate=-1.0), "non-negative"),
    (lambda b: b["rates"].append({"key": "NOPE", "unit": "m3", "rate": 1.0}), "not a key"),
])
def test_pricing_basis_refusals(tmp_path, mutate, msg):
    b = copy.deepcopy(BASIS)
    mutate(b)
    with pytest.raises(ValueError, match=msg):
        build(tmp_path, basis=b)


# ---- adverse inputs ----

def test_foreign_key_map_and_label_refused(tmp_path):
    km = dict(KEY_MAP, project_id="another-villa")
    with pytest.raises(ValueError, match="used for project"):
        build(tmp_path, km=km)
    (tmp_path / "c").mkdir()
    (tmp_path / "c" / "cand.json").write_text(json.dumps(LINES), encoding="utf-8")
    mf = write_project(tmp_path / "c", extra={"candidate_lines": "cand.json", "candidate_label": "run A"})
    with pytest.raises(ValueError, match="never combined"):
        P.load_manifest(mf)


def test_unknown_high_value_key_and_key_without_codes_refused(tmp_path):
    with pytest.raises(ValueError, match="high-value keys"):
        build(tmp_path, extra={"high_value_keys": ["NOPE"]})
    km = copy.deepcopy(KEY_MAP)
    km["keys"][0]["item_codes"] = []
    (tmp_path / "k").mkdir()
    with pytest.raises(ValueError, match="never be answered"):
        build(tmp_path / "k", km=km)


def test_line_order_does_not_change_the_result(tmp_path):
    """Order invariance (the scoring analogue of mirror / rotation: the same lines in any order, same score)."""
    a = build(tmp_path)["sides"][0]["goal_b"]
    lines = copy.deepcopy(LINES)
    random.Random(452).shuffle(lines)
    (tmp_path / "s").mkdir()
    b = build(tmp_path / "s", lines=lines)["sides"][0]["goal_b"]
    strip = lambda g: json.dumps({k: g[k] for k in ("trade_units", "trade_cost", "exception_counts")}, sort_keys=True)
    assert strip(a) == strip(b)


def test_candidate_side_kept_apart(tmp_path):
    cand = copy.deepcopy(LINES)
    cand[3]["measured_net"] = 25.0                # slab 49.000: reconciled 0.000 %
    (tmp_path / "cand.json").write_text(json.dumps(cand), encoding="utf-8")
    res = build(tmp_path, extra={"candidate_lines": "cand.json", "candidate_label": "candidate B"})
    assert [s["label"] for s in res["sides"]] == ["run A", "candidate B"]
    assert by_key(res["sides"][0])["CONC.SLAB"]["engine_qty"] == 48.0
    assert by_key(res["sides"][1])["CONC.SLAB"]["reconciled"]["variance_pct"] == 0.0


def test_candidate_lines_override_carries_its_own_label(tmp_path):
    """F-C-T452-1 (r2): lines given on the command line never inherit the manifest's candidate label."""
    cand = copy.deepcopy(LINES)
    cand[3]["measured_net"] = 25.0
    (tmp_path / "cand.json").write_text(json.dumps(cand), encoding="utf-8")
    (tmp_path / "other.json").write_text(json.dumps(LINES), encoding="utf-8")
    mf = write_project(tmp_path, extra={"candidate_lines": "cand.json", "candidate_label": "candidate B"})
    # normal: the override is scored under the label given with it
    res = P.build(P.load_manifest(mf, candidate_lines=str(tmp_path / "other.json"), candidate_label="candidate C"))
    assert [s["label"] for s in res["sides"]] == ["run A", "candidate C"]
    assert by_key(res["sides"][1])["CONC.SLAB"]["engine_qty"] == 48.0
    # manifest-only path unchanged
    assert [s["label"] for s in P.build(P.load_manifest(mf))["sides"]] == ["run A", "candidate B"]
    # adverse: an override with no label of its own is refused (it would be shown as 'candidate B')
    with pytest.raises(ValueError, match="needs --candidate-label"):
        P.load_manifest(mf, candidate_lines=str(tmp_path / "other.json"))
    with pytest.raises(ValueError, match="never combined"):
        P.load_manifest(mf, candidate_lines=str(tmp_path / "other.json"), candidate_label="run A")
    (tmp_path / "n").mkdir()
    with pytest.raises(ValueError, match="without candidate lines"):
        P.load_manifest(write_project(tmp_path / "n"), candidate_label="candidate C")
    out = tmp_path / "o.json"
    with pytest.raises(ValueError, match="needs --candidate-label"):
        P.main(["--manifest", str(mf), "--out", str(out), "--candidate-lines", str(tmp_path / "other.json")])


# ---- the training villa's committed manifest resolves and validates (its run is private, outside the repository) ----

def test_dev_villa_manifest_inputs(tmp_path):
    root = Path(__file__).resolve().parents[2]
    run = tmp_path / "empty_run"
    run.mkdir()
    (run / "BOQ_LINES.json").write_text("[]", encoding="utf-8")
    m = P.load_manifest(root / "research/agents_t452/DEV_VILLA_MANIFEST.json", run=str(run))
    res = P.build(m)
    assert res["key_map"] == "legacy URBAN_ALSENAN_KEY_MAP_V2" and res["pricing_basis"] is None
    g = by_key(res["sides"][0])
    assert len(g) == 13 and all(x["outcome"] == "SILENT_OMISSION" for x in g.values())
    assert all(x["exception"] == P.REFERENCE_ONLY for x in g.values())      # no line: never 0, never dropped
    assert g["CONC.SLAB"]["reconciled"]["status"] == P.REC_USED and g["CONC.SLAB"]["reconciled"]["qty"] == 60.2804
    assert g["CONC.FOOTING"]["reconciled"]["status"] == P.REC_NOT_VERIFIED    # PARTIALLY VERIFIED: not substituted
    assert {c["status"] for c in res["sides"][0]["goal_b"]["trade_cost"]} == {P.NO_BASIS}
