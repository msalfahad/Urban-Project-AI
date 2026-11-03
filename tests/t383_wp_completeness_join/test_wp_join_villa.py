"""T-383: the per-line WP completeness join (research/agents_t236/wp_join.py, R-T383-WP-WHOLE-1) and the export's join
reader (tools/boq_export_v1.wp_overlay), on a synthetic villa VW-383 (not the development villa).

Hand calculation (VW-383, drawn faces from its own footing and lift-pit details):
  WP.FOUNDATION.FOOTING_MEMBRANE m2 (membrane under each footing):
    F1 2.00 x 1.50 = 3.000 m2, F2 1.80 x 1.80 = 3.240 m2 -> one released line L-FM (element FTG-ALL) 6.240 m2;
    F3 under the lift pit: NOT_APPLICABLE (the pit's own system owns it; VW-S-04 lift detail)  -> inventory 2 faces in
    line + 1 NA, residual 6.240 - 6.240 = 0.000 m2: whole-countable
  WP.FOUNDATION.LIFT_PIT_SCREED m2: pit base 3.00 x 2.40 = 7.200 m2, one line L-PS 7.200 m2           -> whole-countable
  FIN.WP.FLOOR m2: one wet-room floor 2.40 x 1.80 = 4.320 m2, line L-WF; NO wet-area inventory        -> blocked
  STR.CONC.FOOTING m3 (not WP): F1 2.00 x 1.50 x 0.60 = 1.800 m3                                    -> never touched
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t236", ROOT / "research" / "agents_t301"):
    sys.path.insert(0, str(p))

from engine.source import boq_line as BL  # noqa: E402
from engine.source import trade_completeness_v1 as TC  # noqa: E402
from tools import boq_export_v1 as X  # noqa: E402

import t301_wp_inventory as W  # noqa: E402
import wp_join as J  # noqa: E402

PID, REV, CVER = "SYNTH-VILLA-VW383", "e" * 64, "ARCH_TAKEOFF_V3.0.TEST"
DOC = [{"title": "VW-S-04 lift pit detail", "sheet": "S-04"}]
FM, PS = "WP.FOUNDATION.FOOTING_MEMBRANE", "WP.FOUNDATION.LIFT_PIT_SCREED"


def wl(code, eid, q, ev="MEASURED", unit="m2", **kw):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=q, element_id=eid, floor="FDN", formula="sum(L*B)", inputs={"faces": eid},
                        rule_id="R-SYN", rule_version="1", documents=DOC, trade="WATERPROOFING", item_en=code,
                        item_ar="عزل", **kw)


def villa(fm=6.24, extra=()):
    out = [wl(FM, "FTG-ALL", fm), wl(PS, "PIT-BASE", 7.2),
           BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="FIN.WP.FLOOR", unit="m2",
                        evidence_state="MEASURED", measured_net=4.32, element_id="GF-BATH-1", floor="GF",
                        formula="L*B", inputs={"L": 2.4, "B": 1.8}, rule_id="R-SYN", rule_version="1"),
           BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="STR.CONC.FOOTING", unit="m3",
                        evidence_state="MEASURED", measured_net=1.8, element_id="F1", floor="FDN", formula="L*B*H",
                        inputs={"L": 2.0, "B": 1.5, "H": 0.6}, rule_id="R-SYN", rule_version="1")]
    return out + list(extra)


def el(item, element, face, qty, app="APPLICABLE", ev=None):
    e = {"family": "WP.FOUNDATION", "item_code": item, "unit": "m2", "element": element, "face": face, "floor": "FDN",
         "applicability": app, "source": "VW-383 footing schedule", "qty": qty}
    if ev is not None:
        e["evidence"] = ev
    return e


def inventory():
    return [el(FM, "F1", "UNDERSIDE", 3.0), el(FM, "F2", "UNDERSIDE", 3.24),
            el(FM, "F3", "UNDERSIDE", None, app="NOT_APPLICABLE",
               ev={"sheet": "VW-S-04", "ref": "lift detail: pit membrane system under F3"}),
            el(PS, "PIT", "BASE", 7.2)]


def ids(lines):
    return {ln["location"]["element_id"]: ln["line_id"] for ln in lines}


def links(lines):
    i = ids(lines)
    return {i["FTG-ALL"]: [f"{FM}[m2]/F1/UNDERSIDE", f"{FM}[m2]/F2/UNDERSIDE"], i["PIT-BASE"]: [f"{PS}[m2]/PIT/BASE"]}


def whole(lines, eid, qty):
    return X.verdict_add(lines, candidate_version=CVER, boq_lines_sha256=X.lines_sha256(lines),
                         line_ids=[ids(lines)[eid]], scope="WHOLE", checker_qty=qty,
                         evidence=[{"sheet": "S-04", "printed_value": "membrane under footings"}],
                         run_token="20261102T233000-1-1", routine="Checker", verdict_commit="c0ffee12",
                         time="2026-11-02T23:30:00Z")


def summary(res):
    return {(s["trade"], s["item_code"], s["unit"]): s for s in res["summary"]}


def g(code, unit="m2", trade="WATERPROOFING"):
    return (trade, code, unit)


# ---- normal case --------------------------------------------------------------------------------------------------

def test_hand_villa_records_pass_exactly_where_the_inventory_closes():
    lines = villa()
    doc, recs = J.records(inventory(), lines, links(lines), (PID, REV))
    assert doc["refused"] is None and doc["inventory_counts"] == {"IN_LINE": 3, "NOT_APPLICABLE": 1, "MISSING": 0}
    assert [tuple(x) for x in doc["groups_passing"]] == [g(FM), g(PS)]
    fm = recs[g(FM)]
    assert (fm["inventory_count"], fm["element_scope_count"], fm["missing"], fm["held"], fm["duplicated"]) == \
        (1, 1, 0, 0, 0)
    assert fm["inventory_faces"] == {"in_line": 2, "not_applicable": 1, "missing": 0, "held": 0}
    assert (fm["inventory_qty_in_line"], fm["line_qty"], fm["residual"]) == (6.24, 6.24, 0.0)   # 3.000 + 3.240
    assert recs[g("FIN.WP.FLOOR")]["blockers"][0].startswith("NO WP INVENTORY")
    assert recs[g("FIN.WP.FLOOR")]["inventory_count"] is None                 # absent, never 0
    assert g("STR.CONC.FOOTING", "m3", "CONCRETE") not in recs                # a non-WP line is never read


def test_export_verifies_the_closed_wp_lines_only_and_leaves_every_other_row_byte_identical():
    lines = villa()
    doc, _r = J.records(inventory(), lines, links(lines), (PID, REV))
    v2 = [whole(lines, "FTG-ALL", 6.24), whole(lines, "PIT-BASE", 7.2), whole(lines, "GF-BATH-1", 4.32)]
    kw = dict(candidate_version=CVER, boq_lines_sha256=X.lines_sha256(lines), v2_records=v2)
    base = X.build(lines, **kw)
    res = X.build(lines, wp_completeness=doc, **kw)
    sb, sr = summary(base), summary(res)
    for k in (g(FM), g(PS), g("FIN.WP.FLOOR")):                               # without the join: no WP line verifies
        assert sb[k]["line_status"] == "NOT VERIFIED"
    assert sr[g(FM)]["line_status"] == "VERIFIED" and sr[g(FM)]["verified_subtotal"] == 6.24
    assert sr[g(PS)]["line_status"] == "VERIFIED" and sr[g(PS)]["completeness"].startswith("PASS")
    assert sr[g("FIN.WP.FLOOR")]["line_status"] == "NOT VERIFIED"           # a WHOLE record, but no inventory
    assert "NO WP INVENTORY" in sr[g("FIN.WP.FLOOR")]["completeness"]
    wp = {ln["line_id"] for ln in lines if TC.line_trade(ln) == "WATERPROOFING"}
    other_b = [r for r in base["rows"] if r["line_id"] not in wp]
    other_r = [r for r in res["rows"] if r["line_id"] not in wp]
    assert X.csv_bytes(other_b) == X.csv_bytes(other_r) and len(other_r) == 1
    key = g("STR.CONC.FOOTING", "m3", "CONCRETE")
    assert sb[key] == sr[key]
    assert res["completeness_input"] == "records given + T-383 WP join (URBAN_T383_WP_COMPLETENESS_V1)"
    assert base["completeness_input"] == "none given: no line can read VERIFIED"


def test_the_t236_trade_join_alone_can_never_close_a_wp_line_and_the_overlay_can():
    """the cause: one WATERPROOFING trade spans several BOQ lines, so its trade-level record never passes."""
    lines = villa()
    inv, exc, ll = W.to_t236(inventory(), links(lines), "VW-383 WP inventory")
    rep = TC.check(inventories=inv, lines=lines, line_links=ll, exclusions=exc)
    v2 = [whole(lines, "PIT-BASE", 7.2)]
    kw = dict(candidate_version=CVER, boq_lines_sha256=X.lines_sha256(lines), v2_records=v2,
              completeness_report=rep)
    s0 = summary(X.build(lines, **kw))
    assert s0[g(PS)]["line_status"] == "NOT VERIFIED" and "SPANS" in s0[g(PS)]["completeness"]
    doc, _r = J.records(inventory(), lines, links(lines), (PID, REV))
    res = X.build(lines, wp_completeness=doc, **kw)
    s1 = summary(res)
    assert s1[g(PS)]["line_status"] == "VERIFIED"
    assert res["completeness_input"].startswith("T-236 report") and res["completeness_input"].endswith(
        "(URBAN_T383_WP_COMPLETENESS_V1)")
    base = X.build(lines, **kw)                                               # every non-WP row unchanged, in order
    nb = [r for r in base["rows"] if r["trade"] != "WATERPROOFING"]
    nr = [r for r in res["rows"] if r["trade"] != "WATERPROOFING"]
    assert X.csv_bytes(nb) == X.csv_bytes(nr) and len(nr) > 1
    assert [s for s in base["summary"] if s["trade"] != "WATERPROOFING"] == \
        [s for s in res["summary"] if s["trade"] != "WATERPROOFING"]


# ---- adverse cases ------------------------------------------------------------------------------------------------

def _no_wp_line_passes(doc):
    return doc["groups_passing"] == []


def test_a_face_in_two_lines_refuses_the_join_and_no_wp_line_passes():
    second = wl(FM, "FTG-F1-AGAIN", 3.0)
    lines = villa(extra=[second])
    lk = links(lines)
    lk[second["line_id"]] = [f"{FM}[m2]/F1/UNDERSIDE"]
    doc, recs = J.records(inventory(), lines, lk, (PID, REV))
    assert "double count" in doc["refused"] and _no_wp_line_passes(doc)
    assert all(r["blockers"][-1].startswith("WP INVENTORY JOIN REFUSED") for r in recs.values())


def test_not_applicable_without_evidence_is_refused():
    inv = inventory()
    inv[2] = el(FM, "F3", "UNDERSIDE", None, app="NOT_APPLICABLE")
    lines = villa()
    doc, _r = J.records(inv, lines, links(lines), (PID, REV))
    assert "NOT_APPLICABLE without evidence" in doc["refused"] and _no_wp_line_passes(doc)


def test_missing_given_as_zero_is_refused():
    inv = inventory()
    inv[1]["qty"] = 0
    lines = villa()
    doc, _r = J.records(inv, lines, links(lines), (PID, REV))
    assert "never 0" in doc["refused"] and _no_wp_line_passes(doc)


def test_a_dropped_element_prints_missing_never_whole():
    lines = villa(fm=3.0)                                                     # the line carries F1 only
    lk = links(lines)
    lk[ids(lines)["FTG-ALL"]] = [f"{FM}[m2]/F1/UNDERSIDE"]
    doc, recs = J.records(inventory(), lines, lk, (PID, REV))
    fm = recs[g(FM)]
    assert fm["missing"] == 1 and "MISSING 1" in fm["blockers"] and not fm["t383_passes"]
    assert fm["inventory_count"] == 2 and fm["element_scope_count"] == 1    # 1 carrying element + 1 missing face
    res = X.build(lines, candidate_version=CVER, boq_lines_sha256=X.lines_sha256(lines),
                  v2_records=[whole(lines, "FTG-ALL", 3.0)], wp_completeness=doc)
    s = summary(res)[g(FM)]
    assert s["line_status"] == "NOT VERIFIED" and "MISSING 1" in s["completeness"]


def test_a_residual_in_the_unit_blocks_the_whole_line():
    lines = villa(fm=6.25)                                                    # 0.010 m2 more than 3.000 + 3.240
    doc, recs = J.records(inventory(), lines, links(lines), (PID, REV))
    assert "RESIDUAL -0.010000 m2 (inventory - line)" in recs[g(FM)]["blockers"] and not recs[g(FM)]["t383_passes"]
    assert recs[g(PS)]["t383_passes"]                                         # the other item is unaffected


def test_a_face_on_a_held_line_and_an_unlinked_line_block():
    held = wl(FM, "FTG-F2", None, ev="BOUNDED_EXPOSURE", bounded_range={"low": 3.0, "high": 3.5, "basis": "tag"},
              rfi={"question": "F2 tag conflict"})
    extra = wl(PS, "PIT-EXTRA", 1.0)
    lines = villa(fm=3.0, extra=[held, extra])
    i = ids(lines)
    lk = {i["FTG-ALL"]: [f"{FM}[m2]/F1/UNDERSIDE"], i["FTG-F2"]: [f"{FM}[m2]/F2/UNDERSIDE"],
          i["PIT-BASE"]: [f"{PS}[m2]/PIT/BASE"]}
    doc, recs = J.records(inventory(), lines, lk, (PID, REV))
    assert "HELD 1" in recs[g(FM)]["blockers"] and not recs[g(FM)]["t383_passes"]
    assert "UNLINKED LINES 1" in recs[g(PS)]["blockers"] and not recs[g(PS)]["t383_passes"]


def test_a_register_only_key_blocks():
    lines = villa()
    lk = links(lines)
    lk[ids(lines)["PIT-BASE"]].append(f"{PS}[m2]/PIT/NOT_DRAWN")
    doc, recs = J.records(inventory(), lines, lk, (PID, REV))
    assert "REGISTER_ONLY 1" in recs[g(PS)]["blockers"] and not recs[g(PS)]["t383_passes"]


@pytest.mark.parametrize("mutate, text", [
    (lambda d: d.update(schema="OTHER"), "schema must be"),
    (lambda d: d.update(project_id="ANOTHER-VILLA"), "another project"),
    (lambda d: d["records"].append(copy.deepcopy(d["records"][0])), "twice"),
    (lambda d: d["records"].pop(0), "not in the join"),
    (lambda d: d["records"].append(dict(d["records"][0], trade="CONCRETE", item_code="STR.CONC.FOOTING", unit="m3")),
     "not a WATERPROOFING line"),
])
def test_the_export_reader_refuses_a_join_of_other_lines(mutate, text):
    lines = villa()
    doc, _r = J.records(inventory(), lines, links(lines), (PID, REV))
    bad = copy.deepcopy(doc)
    mutate(bad)
    with pytest.raises(X.ExportError, match=text):
        X.build(lines, candidate_version=CVER, boq_lines_sha256=X.lines_sha256(lines), wp_completeness=bad)


def test_t471_component_verified_lines_without_inventory_stay_held():
    lines = villa()
    doc, recs = J.records(inventory(), lines, links(lines), (PID, REV))
    reg = {"components": [
        {"component_id": "C-WET", "family": "B8-01", "applicability": "APPLICABLE", "item_codes": ["FIN.WP.FLOOR"]},
        {"component_id": "C-FDN", "family": "B8-08", "applicability": "APPLICABLE", "item_codes": [FM, PS]},
        {"component_id": "C-NA", "family": "B8-09", "applicability": "NOT_APPLICABLE", "item_codes": [PS]},
        {"component_id": "C-CONC", "family": "B2-01", "applicability": "APPLICABLE", "item_codes": ["STR.CONC.FOOTING"]}]}
    cls = {ln["line_id"]: "VERIFIED" for ln in lines}
    rows = {r["component_id"]: r for r in J.components(reg, lines, cls, recs, inventory())}
    assert set(rows) == {"C-WET", "C-FDN", "C-NA"}                           # the concrete component is not read
    assert (rows["C-WET"]["state"], rows["C-WET"]["gate"], rows["C-WET"]["wp_inventory"]) == \
        ("APPLICABLE_HELD", "HELD", "ABSENT")
    assert (rows["C-FDN"]["state"], rows["C-FDN"]["gate"], rows["C-FDN"]["wp_inventory"]) == \
        ("APPLICABLE_VERIFIED", "VERIFIED", "COMPLETE")
    assert rows["C-FDN"]["whole_countable_items"] == [f"{FM}[m2]", f"{PS}[m2]"]
    assert rows["C-NA"]["conflict"] in ("NA_WITH_QUANTITY_LINES", "NA_WITH_INVENTORY_FACES")


def test_command_line_reads_the_join_and_states_it_in_the_manifest(tmp_path):
    import json
    lines = villa()
    doc, _r = J.records(inventory(), lines, links(lines), (PID, REV))
    lp, jp = tmp_path / "lines.json", tmp_path / "wp.json"
    lp.write_text(BL.dumps(lines), encoding="utf-8")
    jp.write_text(J.dump(doc), encoding="utf-8")
    assert X.main(["--lines", str(lp), "--candidate-version", CVER, "--out", str(tmp_path / "a"),
                   "--code-commit", "abc1234"]) == 0
    assert X.main(["--lines", str(lp), "--candidate-version", CVER, "--out", str(tmp_path / "b"),
                   "--code-commit", "abc1234", "--wp-completeness", str(jp)]) == 0
    ma = json.loads((tmp_path / "a" / "EXPORT_MANIFEST.json").read_text(encoding="utf-8"))
    mb = json.loads((tmp_path / "b" / "EXPORT_MANIFEST.json").read_text(encoding="utf-8"))
    assert "wp_completeness" not in ma["inputs_sha256"] and "wp_completeness" in mb["inputs_sha256"]
    assert mb["completeness_input"].endswith("T-383 WP join (URBAN_T383_WP_COMPLETENESS_V1)")
    # without verdicts nothing verifies either way: the CSV rows are the same bytes
    assert (tmp_path / "a" / "BOQ.csv").read_bytes() == (tmp_path / "b" / "BOQ.csv").read_bytes()
