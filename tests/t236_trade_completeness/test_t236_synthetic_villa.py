"""T-236 acceptance: trade completeness on a hand-made synthetic villa ("synthetic-villa-t236", not a client drawing),
with an independent inventory per trade and one injection per required fault.

Hand expectations
  CONCRETE.FOOTING  inventories: printed schedule occurrences + plan tags, both FDN: F1.1, F1.2, F2, F3 (AGREED)
                    lines: F1.1 0.900, F1.2 0.900, F2 1.200 m3; F2 has a Checker COUNTED verdict
                    INJECTION F3 removed from the register AND the BOQ -> MISSING (found by both inventories)
                    d = 4: measured 3 (incl. verified 1), held 0 -> completeness 3 / 4 = 75.0 %, verified 1 / 4 = 25.0 %
  CONCRETE.COLUMN   plan tags GF C1, C2 and 1F C1, C2 (one source covering GF and 1F); lines on all four
                    INJECTION GF:C2 on two lines (rules R-C, R-C2) -> DUPLICATED (one element, two lines, same unit)
                    GF:C1 and 1F:C1: the same label on two storeys -> two keys, NOT a duplicate
                    a line on 1F:C9 (no tag on 1F) -> REGISTER_ONLY (in no inventory; not in d)
                    d = 4, measured 4 -> 4 / 4; status GAPS (the duplicate)
  MASONRY.200       wall census GF W1, W2; W1 gross 10.000 - D1 1.600 = 8.400 net (RECONCILED)
                    INJECTION W2 gross 12.000 - D2 2.000 = 10.000, line says 10.500 -> REFUSED NET_MISMATCH
  PLASTER           GF:W1 face A in two height bands (components A-low, A-high); INJECTION both bands deduct door D1 on
                    face A -> both lines REFUSED DEDUCTION_REPEATED_ACROSS_LINES:D1@A; NOT a duplicate (two components)
  DOORS             door schedule GF D1, D2; plan tags GF D1 only (both cover GF); line on D1 only
                    -> D1 MEASURED (AGREED), D2 CONFLICT (inventories disagree, no line: never picked, never MISSING)
  WINDOWS           block inserts GF WN-A (tagged) and G-7 (untagged geometry); a line on WN-A
                    -> G-7 INVENTORY_GEOMETRY_ONLY with the residual risk named
  CEILING           room census GF LIVING, STORE; line on LIVING; STORE excluded by owner rule OR-1 -> EXCLUDED (d = 1)
  RAILINGS          census 1F RL-01; line BLOCKED_RFI naming its question -> HELD (no quantity, never 0)
  PAINT             no inventory, no line -> NOT_MEASURED row (present, never absent)
  LEVELS            GF FFL +1.00 on two sheets AGREED; 1F FFL +5.50 vs +5.55 CONFLICT; GF SSL +0.95 is another datum
                    (never compared with the FFL)
  ACCURACY          footing reference rows 0.90 / 0.90 / 1.30 / 1.00 m3 against engine 0.90 / 0.90 / 1.20 / None:
                    compared 3 / 4, WAPE = 0.10 / 3.10 = 3.23 %, in its own table only
  METAMORPHIC       every input list reversed / shuffled, and every x coordinate mirrored -> identical report bytes
"""

from __future__ import annotations

import copy
import random

import pytest

from engine.source import boq_line as BL
from engine.source import trade_completeness_v1 as TC

REV = "c" * 64


def L(eid, q, code, unit, rule="R-1", ev="MEASURED", floor="GF", **kw):
    # element ids carry the storey (as the register's ids do): line_id hashes the element id, not the floor
    return BL.make_line(project_id="synthetic-villa-t236", revision_set_sha256=REV, item_code=code, unit=unit,
                        evidence_state=ev, measured_net=q, element_id=f"{floor}/{eid}", formula="hand", rule_id=rule,
                        rule_version="1", floor=floor, geometry_source="SYNTHETIC_FIXTURE", **kw)


def villa():
    ftg = [L("F1.1", 0.9, "STR.CONC.FOOTING", "m3", floor="FDN"), L("F1.2", 0.9, "STR.CONC.FOOTING", "m3", floor="FDN"),
           L("F2", 1.2, "STR.CONC.FOOTING", "m3", floor="FDN")]
    col = [L("C1", 0.4, "STR.CONC.COLUMN", "m3"), L("C2", 0.4, "STR.CONC.COLUMN", "m3"),
           L("C2", 0.4, "STR.CONC.COLUMN", "m3", rule="R-C2"),
           L("C1", 0.4, "STR.CONC.COLUMN", "m3", floor="1F"), L("C2", 0.4, "STR.CONC.COLUMN", "m3", floor="1F"),
           L("C9", 0.4, "STR.CONC.COLUMN", "m3", floor="1F")]
    mas = [L("W1", 8.4, "MAS.BLOCK", "m2", subtrade="200", gross=10.0, deductions=[{"opening": "D1", "area": 1.6}]),
           L("W2", 10.5, "MAS.BLOCK", "m2", subtrade="200", gross=12.0, deductions=[{"opening": "D2", "area": 2.0}])]
    pla = [L("W1-A-low", 4.4, "FIN.PLASTER", "m2", gross=5.0, deductions=[{"opening": "D1", "area": 0.6, "face": "A"}]),
           L("W1-A-high", 4.0, "FIN.PLASTER", "m2", gross=5.0, deductions=[{"opening": "D1", "area": 1.0, "face": "A"}])]
    door = [L("D1", 1, "ARCH.DOOR", "pcs")]
    win = [L("WN-A", 1, "ARCH.WINDOW", "pcs")]
    ceil = [L("LIVING", 20.0, "FIN.CEILING", "m2")]
    rail = [BL.make_line(project_id="synthetic-villa-t236", revision_set_sha256=REV, item_code="FIN.RAILING", unit="lm",
                         evidence_state="BLOCKED_RFI", element_id="1F/RL-01", formula="sloping length", rule_id="R-1",
                         rule_version="1", floor="1F", rfi={"question": "D-99 railing height not printed"})]
    lines = ftg + col + mas + pla + door + win + ceil + rail
    links = {}
    for ln in lines:
        loc = ln["location"]
        eid = loc["element_id"].split("/", 1)[1]
        if eid.startswith("W1-A-"):
            links[ln["line_id"]] = [{"key": "GF:W1", "component": eid[3:]}]
        else:
            links[ln["line_id"]] = [f"{loc['floor']}:{eid}"]
    inv = [
        {"source": "FOOTING SCHEDULE occurrences", "basis": "PRINTED_SCHEDULE", "trade": "CONCRETE.FOOTING",
         "elements": [{"floor": "FDN", "label": x, "ref": f"sched {x}", "xy": [i * 3.0, 0.0]}
                      for i, x in enumerate(("F1.1", "F1.2", "F2", "F3"))]},
        {"source": "FOUNDATION PLAN tags", "basis": "TEXT_TAG", "trade": "CONCRETE.FOOTING",
         "elements": [{"floor": "FDN", "label": x, "ref": f"tag {x}", "xy": [i * 3.0, 1.0]}
                      for i, x in enumerate(("F1.1", "F1.2", "F2", "F3"))]},
        {"source": "COLUMN tags", "basis": "TEXT_TAG", "trade": "CONCRETE.COLUMN", "floors": ["GF", "1F"],
         "elements": [{"floor": f, "label": c, "ref": f"{f} {c}", "xy": [2.0 + i, 5.0]}
                      for f in ("GF", "1F") for i, c in enumerate(("C1", "C2"))]},
        {"source": "MASONRY census", "basis": "CENSUS", "trade": "MASONRY.200",
         "elements": [{"floor": "GF", "label": "W1"}, {"floor": "GF", "label": "W2"}]},
        {"source": "PLASTER faces census", "basis": "CENSUS", "trade": "PLASTER", "elements": [{"floor": "GF", "label": "W1"}]},
        {"source": "DOOR SCHEDULE", "basis": "PRINTED_SCHEDULE", "trade": "DOORS", "floors": ["GF"],
         "elements": [{"floor": "GF", "label": "D1"}, {"floor": "GF", "label": "D2"}]},
        {"source": "DOOR tags", "basis": "TEXT_TAG", "trade": "DOORS", "floors": ["GF"],
         "elements": [{"floor": "GF", "label": "D1"}]},
        {"source": "WINDOW blocks", "basis": "BLOCK_INSERT", "trade": "WINDOWS",
         "elements": [{"floor": "GF", "label": "WN-A"}, {"floor": "GF", "label": "G-7", "tagged": False}]},
        {"source": "ROOM census", "basis": "CENSUS", "trade": "CEILING",
         "elements": [{"floor": "GF", "label": "LIVING"}, {"floor": "GF", "label": "STORE"}]},
        {"source": "RAILING census", "basis": "HAND_COUNT", "trade": "RAILINGS", "elements": [{"floor": "1F", "label": "RL-01"}]},
    ]
    reg = [{"trade": "CONCRETE.FOOTING", "floor": "FDN", "label": x} for x in ("F1.1", "F1.2", "F2")]
    return dict(inventories=inv, register=reg, lines=lines, line_links=links,
                verdicts=[{"trade": "CONCRETE.FOOTING", "key": "FDN:F2", "verdict": "COUNTED", "ref": "checker run X"}],
                exclusions=[{"trade": "CEILING", "key": "GF:STORE", "rule_id": "OR-1", "basis": "owner: no ceiling"}],
                opening_census=["D1", "D2"],
                levels=[{"sheet": "A-03", "storey": "GF", "datum": "FFL", "level_m": 1.00},
                        {"sheet": "S-04", "storey": "GF", "datum": "FFL", "level_m": 1.00},
                        {"sheet": "S-04", "storey": "GF", "datum": "SSL", "level_m": 0.95},
                        {"sheet": "A-04", "storey": "1F", "datum": "FFL", "level_m": 5.50},
                        {"sheet": "A-10", "storey": "1F", "datum": "FFL", "level_m": 5.55}],
                accuracy=[{"trade": "CONCRETE.FOOTING", "unit": "m3", "row": r, "engine": e, "reference": f}
                          for r, e, f in (("R1", 0.9, 0.9), ("R2", 0.9, 0.9), ("R3", 1.2, 1.3), ("R4", None, 1.0))])


def _el(rep, tr):
    return {e["key"]: e for e in rep["elements"] if e["trade"] == tr}


def _tr(rep, tr):
    return [t for t in rep["trades"] if t["trade"] == tr][0]


@pytest.fixture(scope="module")
def rep():
    return TC.check(**villa())


def test_footings_missing_verified_and_n_over_d(rep):
    e = _el(rep, "CONCRETE.FOOTING")
    assert {k: v["status"] for k, v in e.items()} == {"FDN:F1.1": "MEASURED", "FDN:F1.2": "MEASURED",
                                                       "FDN:F2": "VERIFIED", "FDN:F3": "MISSING"}
    assert all(v["inventory_agreement"] == "AGREED" for v in e.values())
    t = _tr(rep, "CONCRETE.FOOTING")
    assert (t["found"], t["measured"], t["verified"], t["missing"], t["status"]) == (4, 3, 1, 1, "GAPS")
    c = [x for x in rep["completeness_table"] if x["trade"] == "CONCRETE.FOOTING"][0]
    v = [x for x in rep["verified_table"] if x["trade"] == "CONCRETE.FOOTING"][0]
    assert (c["n"], c["d"], c["pct"]) == (3, 4, 75.0) and (v["n"], v["d"], v["pct"]) == (1, 4, 25.0)


def test_columns_duplicate_same_label_two_storeys_and_register_only(rep):
    e = _el(rep, "CONCRETE.COLUMN")
    assert [k for k, v in e.items() if v["duplicated"]] == ["GF:C2"]
    assert len(e["GF:C2"]["duplicate_lines"]) == 2
    assert not e["GF:C1"]["duplicated"] and not e["1F:C1"]["duplicated"]
    assert e["1F:C9"]["status"] == "REGISTER_ONLY"
    t = _tr(rep, "CONCRETE.COLUMN")
    assert (t["found"], t["measured"], t["duplicated"], t["register_only"], t["status"]) == (4, 4, 1, 1, "GAPS")


def test_wall_net_mismatch_refused_and_reconciled_line_kept(rep):
    rows = {tuple(r["keys"]): r for r in rep["deductions"] if r["trade"] == "MASONRY.200"}
    assert rows[("GF:W1",)]["status"] == "RECONCILED"
    assert rows[("GF:W2",)]["status"] == "REFUSED"
    assert rows[("GF:W2",)]["problems"][0].startswith("NET_MISMATCH")
    with pytest.raises(TC.CompletenessError):
        TC.reconcile_line([ln for ln in villa()["lines"] if ln["location"]["element_id"] == "GF/W2"][0])


def test_opening_deducted_in_two_bands_of_one_face_refused_not_duplicate(rep):
    rows = [r for r in rep["deductions"] if r["trade"] == "PLASTER"]
    assert len(rows) == 2 and all(r["status"] == "REFUSED" for r in rows)
    assert all(r["problems"] == ["DEDUCTION_REPEATED_ACROSS_LINES:D1@A"] for r in rows)
    assert not _el(rep, "PLASTER")["GF:W1"]["duplicated"]


def test_inventories_disagree_conflict_never_picked(rep):
    e = _el(rep, "DOORS")
    assert e["GF:D1"]["status"] == "MEASURED" and e["GF:D1"]["inventory_agreement"] == "AGREED"
    assert e["GF:D2"]["status"] == "CONFLICT" and e["GF:D2"]["inventory_agreement"] == "CONFLICT"
    assert e["GF:D2"]["sources"] == ["DOOR SCHEDULE"]
    t = _tr(rep, "DOORS")
    assert (t["missing"], t["conflict"], t["found"]) == (0, 1, 2)


def test_untagged_geometry_reported_with_risk(rep):
    e = _el(rep, "WINDOWS")["GF:G-7"]
    assert e["status"] == "INVENTORY_GEOMETRY_ONLY" and "omitted" in e["reason"]


def test_owner_exclusion_is_excluded_with_rule_not_missing(rep):
    e = _el(rep, "CEILING")["GF:STORE"]
    assert e["status"] == "EXCLUDED" and e["reason"].startswith("OR-1")
    t = _tr(rep, "CEILING")
    assert (t["found"], t["excluded"], t["missing"]) == (1, 1, 0)


def test_held_with_question_never_zero(rep):
    e = _el(rep, "RAILINGS")["1F:RL-01"]
    assert e["status"] == "HELD" and "D-99" in e["reason"]
    c = [x for x in rep["completeness_table"] if x["trade"] == "RAILINGS"][0]
    assert (c["n"], c["d"]) == (1, 1)
    v = [x for x in rep["verified_table"] if x["trade"] == "RAILINGS"][0]
    assert (v["n"], v["d"]) == (0, 1)


def test_every_principal_trade_has_a_row(rep):
    trades = [t["trade"] for t in rep["trades"]]
    assert trades[:len(TC.PRINCIPAL_TRADES)] == list(TC.PRINCIPAL_TRADES)
    assert _tr(rep, "PAINT")["status"] == "NOT_MEASURED"
    assert _tr(rep, "FORMWORK")["status"] == "NOT_MEASURED"
    # a trade with lines but no inventory: never 100 %
    c = {x["trade"]: x for x in rep["completeness_table"]}
    assert c["PAINT"]["pct"] == "n/a"


def test_levels_conflict_only_within_one_datum(rep):
    lv = {(x["storey"], x["datum"]): x["status"] for x in rep["levels"]}
    assert lv == {("1F", "FFL"): "CONFLICT", ("GF", "FFL"): "AGREED", ("GF", "SSL"): "SINGLE_SHEET"}


def test_accuracy_apart_with_compared_n_over_d(rep):
    a = rep["accuracy_table"]
    assert a == [{"trade": "CONCRETE.FOOTING", "unit": "m3", "compared": "3 / 4", "wape_pct": 3.23}]
    assert "wape_pct" not in rep["completeness_table"][0] and "pct" not in a[0]


def test_reference_line_rows_for_t235(rep):
    rows = {r["element_scope"]: r for r in TC.reference_line_rows(rep)}
    f = rows["CONCRETE.FOOTING"]
    assert (f["inventory_count"], f["missing"], f["completeness"], f["verified"]) == (4, ["FDN:F3"], "3 / 4", "1 / 4")
    assert rows["CONCRETE.COLUMN"]["duplicated"] == ["GF:C2"]
    assert rows["RAILINGS"]["held"] == ["1F:RL-01"]
    assert f["inventory_sources"] == ["FOOTING SCHEDULE occurrences (PRINTED_SCHEDULE)",
                                      "FOUNDATION PLAN tags (TEXT_TAG)"]


def test_metamorphic_reorder_and_mirror_same_report(rep):
    v = villa()
    rnd = random.Random(236)
    w = copy.deepcopy(v)
    for k in ("inventories", "register", "lines", "verdicts", "exclusions", "levels", "accuracy"):
        rnd.shuffle(w[k])
    for src in w["inventories"]:
        rnd.shuffle(src["elements"])
        for e in src["elements"]:
            if "xy" in e:
                e["xy"] = [-e["xy"][0], e["xy"][1]]
    w["line_links"] = dict(reversed(list(w["line_links"].items())))
    assert TC.dumps(TC.check(**w)) == TC.dumps(rep)


def test_adverse_engine_inventory_and_unruled_exclusion_refused():
    v = villa()
    v["inventories"][0]["basis"] = "ENGINE_REGISTER"
    with pytest.raises(TC.CompletenessError, match="not an independent"):
        TC.check(**v)
    v = villa()
    v["exclusions"] = [{"trade": "CEILING", "key": "GF:STORE"}]
    with pytest.raises(TC.CompletenessError, match="owner rule"):
        TC.check(**v)


def test_adverse_held_line_cannot_carry_zero():
    with pytest.raises(BL.LineError):
        BL.make_line(project_id="P", revision_set_sha256=REV, item_code="FIN.RAILING", unit="lm",
                     evidence_state="BLOCKED_RFI", measured_net=0.0, element_id="RL-01", formula="x", rule_id="R",
                     rule_version="1", rfi={"question": "q"})


def test_adverse_two_lines_one_line_id_refused():
    v = villa()
    a = v["lines"][0]
    b = copy.deepcopy(a)
    b["measured_net"] = 5.0
    v["lines"].append(b)
    with pytest.raises(TC.CompletenessError, match="line id"):
        TC.check(**v)
    v = villa()
    v["lines"].append(copy.deepcopy(v["lines"][0]))       # the same line given twice: one line, accepted
    assert TC.dumps(TC.check(**v)) == TC.dumps(TC.check(**villa()))


def test_held_without_reason_is_unresolved():
    rep = TC.check(inventories=[{"source": "S", "basis": "CENSUS", "trade": "RAILINGS",
                                 "elements": [{"floor": "1F", "label": "RL-02"}]}],
                   register=[{"trade": "RAILINGS", "floor": "1F", "label": "RL-02", "status": "HELD"}])
    assert _el(rep, "RAILINGS")["1F:RL-02"]["status"] == "UNRESOLVED"


def test_line_trade_mapping():
    assert TC.line_trade({"item_code": "MAS.BLOCK", "subtrade": None, "calculation": {"inputs": {"thickness_mm": 150}},
                          "trade": "MASONRY"}) == "MASONRY.150"
    assert TC.line_trade({"item_code": "MAS.BLOCK", "subtrade": None, "calculation": {"inputs": {}},
                          "trade": "MASONRY"}) == "MASONRY.UNSTATED"
    assert TC.line_trade({"item_code": "STR.CONC.STRAP", "trade": "CONCRETE"}) == "CONCRETE.STRAP"
    assert TC.line_trade({"item_code": "DOOR.INTERNAL.PVC", "trade": "OPENINGS"}) == "DOORS"
    assert TC.line_trade({"item_code": "ARCH.PASSAGE", "trade": "OPENINGS"}) == "OTHER:OPENINGS"


def test_policy_record_and_guard_class():
    p = TC.policy_record()
    assert p["default_guard_class"] == "CHECK_ONLY" and len(p["principal_trades"]) == len(TC.PRINCIPAL_TRADES)


def test_canonical_deduction_form_unit_key_and_what():
    ok = BL.make_line(project_id="P", revision_set_sha256=REV, item_code="FIN.FLOOR.PORCELAIN", unit="m2",
                      evidence_state="SOURCE_DERIVED", measured_net=11.8, element_id="GF/HALL", formula="g-d",
                      rule_id="R", rule_version="1", gross=12.0, deductions=[{"m2": 0.2, "what": "column"}])
    bad = BL.make_line(project_id="P", revision_set_sha256=REV, item_code="FIN.SKIRTING", unit="lm",
                       evidence_state="SOURCE_DERIVED", measured_net=9.0, element_id="GF/HALL", formula="g-d",
                       rule_id="R", rule_version="1", gross=10.0, deductions=[{"lm": 0.9}])
    assert TC.reconcile_line(ok) is ok
    rep = TC.check(lines=[ok, bad])
    st = {r["line_id"]: (r["status"], r["problems"]) for r in rep["deductions"]}
    assert st[ok["line_id"]] == ("RECONCILED", [])
    assert st[bad["line_id"]][0] == "REFUSED"
    assert st[bad["line_id"]][1] == ["DEDUCTION_UNNAMED", "NET_MISMATCH:gross 10 - deductions 0.9 + additions 0 != net 9"]
