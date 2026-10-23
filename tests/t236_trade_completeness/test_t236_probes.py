"""T-236 regression baseline (owner 2026-10-23 19:45 (3)): the ADVERSARIAL_PROBE_2026-10-23.md probes 1b, 2, 3, 6 and 9
ported as tests. Synthetic data only (villa "synthetic-villa-t236-probe", no client drawing).

History contract: in the FIRST commit of T-236 (5ebe0410) every test below carried a strict xfail marker and fails on the merged
working head (the existing modules do not detect the fault: probe 1b / 2 / 9 through scope_crosswalk_v1, probe 3 through
boq_line, probe 6 has no sheet-to-sheet level check at all); the fix commit (engine/source/trade_completeness_v1.py)
removes each marker so the test passes. Each test first restates the probe's "actual today" on the existing module
(that part passes before and after: the existing modules are not changed), then asks the new check for the detection.

Hand expectations:
  1b  inventory (printed footing schedule occurrences) F1 .. F5 at FDN; register and BOQ carry F1 .. F4 only:
      crosswalk reports no MISSING_LINE (it never saw F5); T-236 reports FDN:F5 MISSING.
  2   footing F1 on two STR.CONC.FOOTING lines (rule ids R-T and R-T2, 1.1 m3 each): T-236 reports FDN:F1 DUPLICATED.
  3   wall W1 MAS.BLOCK gross 10.0 m2, opening W05 deducted twice (1.6 + 1.6), net 6.8: boq_line accepts it; T-236
      refuses the line (DEDUCTION_REPEATED; gross - deductions = 6.8 = net, so the refusal is the repeat alone).
  6   the GF finished floor level printed +1.00 on one sheet and +1.05 on another (same datum FFL): CONFLICT row.
  9   no PAINT line at all: T-236 still writes a PAINT trade row, status NOT_MEASURED.
"""

from __future__ import annotations

from engine.source import boq_line as BL
from engine.source import scope_crosswalk_v1 as XW

REV = "a" * 64


def _tc():
    from engine.source import trade_completeness_v1 as TC   # T-236 (absent before the fix commit)
    return TC


def _line(eid, q, code="STR.CONC.FOOTING", unit="m3", rule="R-T", **kw):
    return BL.make_line(project_id="PX", revision_set_sha256=REV, item_code=code, unit=unit, evidence_state="MEASURED",
                        measured_net=q, element_id=eid, formula="L*B*H", rule_id=rule, rule_version="1", floor="FDN",
                        **kw)


def _footing_inventory(n=5):
    return {"source": "SCHEDULE:FOOTINGS+PLAN_TAGS", "basis": "PRINTED_SCHEDULE", "trade": "CONCRETE.FOOTING",
            "elements": [{"floor": "FDN", "label": f"F{i}", "ref": f"plan tag F{i}"} for i in range(1, n + 1)]}


def _links(lines):
    return {ln["line_id"]: [f"FDN:{ln['location']['element_id']}"] for ln in lines}


def test_probe_1b_element_absent_from_register_and_boq_is_missing():
    els = [{"id": f"F{i}", "kind": "FOOTING", "floor": "FDN", "label": f"F{i}", "source": "ELEMENT_REGISTER_V0"}
           for i in range(1, 5)]
    lines = [_line(f"F{i}", 1.0 + i / 10) for i in range(1, 5)]
    r = XW.crosswalk(els, [], {}, lines, {ln["line_id"]: [ln["location"]["element_id"]] for ln in lines})
    assert [e["id"] for e in r["elements"] if e["status"] == "MISSING_LINE"] == []      # actual today: not seen
    TC = _tc()
    rep = TC.check(inventories=[_footing_inventory()],
                   register=[{"trade": "CONCRETE.FOOTING", "floor": "FDN", "label": f"F{i}"} for i in range(1, 5)],
                   lines=lines, line_links=_links(lines))
    st = {e["key"]: e["status"] for e in rep["elements"] if e["trade"] == "CONCRETE.FOOTING"}
    assert st["FDN:F5"] == "MISSING"
    assert [k for k, s in st.items() if s == "MISSING"] == ["FDN:F5"]


def test_probe_2_one_element_on_two_lines_is_duplicated():
    lines = [_line(f"F{i}", 1.0 + i / 10) for i in range(1, 6)] + [_line("F1", 1.1, rule="R-T2")]
    tot = BL.totals(lines, by=("trade",))
    assert abs(sum(v["m3"]["net"] for v in tot.values()) - 7.6) < 1e-9                  # actual today: both summed
    TC = _tc()
    rep = TC.check(inventories=[_footing_inventory()], lines=lines, line_links=_links(lines))
    dup = [e["key"] for e in rep["elements"] if e["trade"] == "CONCRETE.FOOTING" and e["duplicated"]]
    assert dup == ["FDN:F1"]


def test_probe_3_one_opening_deducted_twice_is_refused():
    ln = BL.make_line(project_id="PX", revision_set_sha256=REV, item_code="MAS.BLOCK", unit="m2",
                      evidence_state="MEASURED", measured_net=6.8, element_id="W1", gross=10.0,
                      deductions=[{"opening": "W05", "area": 1.6}, {"opening": "W05", "area": 1.6}], formula="g-d",
                      rule_id="R", rule_version="1", subtrade="200")                # actual today: accepted
    TC = _tc()
    rep = TC.check(lines=[ln], line_links={ln["line_id"]: ["GF:W1"]}, opening_census=["W05"])
    row = [d for d in rep["deductions"] if d["line_id"] == ln["line_id"]][0]
    assert row["status"] == "REFUSED"
    assert row["problems"] == ["DEDUCTION_REPEATED:W05"]


def test_probe_6_storey_level_printed_differently_on_two_sheets_is_conflict():
    TC = _tc()
    rep = TC.check(levels=[{"sheet": "ARCH sheet 03", "storey": "GF", "datum": "FFL", "level_m": 1.00},
                           {"sheet": "ST p.4", "storey": "GF", "datum": "FFL", "level_m": 1.05}])
    conf = [x for x in rep["levels"] if x["status"] == "CONFLICT"]
    assert len(conf) == 1 and conf[0]["storey"] == "GF" and conf[0]["datum"] == "FFL"


def test_probe_9_whole_trade_absent_still_gets_a_row():
    lines = [_line(f"F{i}", 1.0) for i in range(1, 6)]
    r = XW.crosswalk([], [{"row_id": "P1", "trade": "PAINT", "unit": "m2", "qty": 900, "row_kind": "DETAIL"}], {},
                     lines, {})
    assert r["rows"][0]["status"] == "NOT_MAPPED"                                       # actual today: join pending
    TC = _tc()
    rep = TC.check(inventories=[_footing_inventory()], lines=lines, line_links=_links(lines))
    paint = [t for t in rep["trades"] if t["trade"] == "PAINT"]
    assert len(paint) == 1 and paint[0]["status"] == "NOT_MEASURED"
