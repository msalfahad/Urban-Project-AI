"""T-469: research/agents_t469/t469_trade_scoreboard.py, the eight owner categories per trade (owner decisions
2026-11-02 SCOREBOARD). Synthetic hand fixture (not the development villa): two registry groups, four families, lines
made with engine/source/boq_line.make_line, verdicts and downgrades made with tools/boq_export_v1 (the Checker's own
record builders). Every expected figure below is a hand calculation. No test reads the live board."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t469"))

from engine.source import boq_line as BL  # noqa: E402
from tools import boq_export_v1 as EX  # noqa: E402
import t469_trade_scoreboard as T  # noqa: E402

PID, REV = "synthetic-t469", "a" * 64
MASTER = {"version": "test", "families": [
    {"code": "B10-08", "group": "B10 Concrete", "item_en": "Suspended slabs", "unit": "m3",
     "item_codes": ["STR.CONC.SLAB"]},
    {"code": "B10-06", "group": "B10 Concrete", "item_en": "Columns", "unit": "m3", "item_codes": ["STR.CONC.COLUMN"]},
    {"code": "B10-12", "group": "B10 Concrete", "item_en": "RC parapets", "unit": "m3",
     "item_codes": ["STR.CONC.PARAPET"]},
    {"code": "B8-05", "group": "B8 Waterproofing", "item_en": "Membrane rolls", "unit": "m2 / rolls",
     "item_codes": ["FIN.WP.MEMBRANE_ROLLS"]},
]}


def mk(code, el, ev, net=None, unit="m3", br=None, trade="CONCRETE"):
    kw = {}
    if ev == "BLOCKED_RFI":
        kw["rfi"] = {"question": "which section?"}
    if ev in T.EXCLUDED_STATES:
        kw["notes"] = "not applicable: shown on the drawing"
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=el, bounded_range=br, formula="L x W x D", rule_id="R-T469",
                        rule_version="1.0.0", trade=trade, item_en=code, item_ar=code, **kw)


def lines():
    return [
        # slab: two released panels 10.0 + 5.5 = 15.5 m3 (WHOLE verdict below)
        mk("STR.CONC.SLAB", "S1", "MEASURED", 10.0),
        mk("STR.CONC.SLAB", "S2", "MEASURED", 5.5),
        # columns: released 2.0 + bounded 1.0 .. 3.0 + one UNKNOWN (no bound)
        mk("STR.CONC.COLUMN", "C1", "MEASURED", 2.0),
        mk("STR.CONC.COLUMN", "C2", "BOUNDED_EXPOSURE", None, br={"low": 1.0, "high": 3.0, "basis": "range"}),
        mk("STR.CONC.COLUMN", "C3", "BLOCKED_RFI"),
        # parapet: none (no line) -> UNMEASURED
        # membrane rolls: released 40 m2 (procurement layer)
        mk("FIN.WP.MEMBRANE_ROLLS", "R1", "PROVISIONAL", 40.0, unit="m2", trade="WATERPROOFING"),
        # a line no family owns
        mk("STR.CONC.OTHER", "X1", "MEASURED", 0.7),
    ]


def whole_slab(ls, version="V-TEST", checker=15.5):
    ids = [x["line_id"] for x in ls if x["item_code"] == "STR.CONC.SLAB"]
    return EX.verdict_add(ls, candidate_version=version, boq_lines_sha256=EX.lines_sha256(ls), line_ids=ids,
                          scope="WHOLE", checker_qty=checker,
                          evidence=[{"sheet": "S-1", "printed_value": "slab 200"}], run_token="t", routine="Checker",
                          verdict_commit="abcdef1", time="2026-11-02T00:00:00Z")


def grp(doc, name):
    return next(g for g in doc["sides"][0]["groups"] if g["group"] == name)


def fam(doc, code):
    return next(f for f in doc["sides"][0]["families"] if f["family"] == code)


def test_eight_categories_normal_case():
    ls = lines()
    doc = T.build(ls, "cand", "V-TEST", MASTER, [whole_slab(ls)], [])
    c = grp(doc, "B10 Concrete")
    assert c["expected"] == 3                      # (1) three families, one has no line
    assert c["measured"] == 1                      # (2) slab only (columns hold a held line)
    assert c["per_unit"]["m3"]["released_qty"] == 17.5   # 10 + 5.5 + 2.0, never the held lines
    assert c["verified_whole"] == 1                # (3) slab, WHOLE verdict on every released slab line
    assert c["per_unit"]["m3"]["verified_whole_qty"] == 15.5
    assert c["held"] == 1                          # (4) columns
    assert (c["per_unit"]["m3"]["held_low"], c["per_unit"]["m3"]["held_high"]) == (1.0, 3.0)
    assert c["per_unit"]["m3"]["held_unknown_lines"] == 1
    assert c["unmeasured"] == 1                    # (5) parapets: no line
    assert (c["verified_item_lines"], c["item_lines"]) == (1, 2)   # STR.CONC.SLAB (m3) of slab + column codes
    assert c["priced_lines"] == 0 and c["unpriced_lines"] == 5   # (8) every line UNPRICED
    w = grp(doc, "B8 Waterproofing")
    assert w["material_provisional"] == {"m2": 40.0}   # (6)
    assert w["material_verified"] == {"m2": 0.0}       # (7) no verdict on the procurement line
    assert doc["sides"][0]["no_family"] == [{"item_code": "STR.CONC.OTHER", "unit": "m3", "lines": 1,
                                             "released_qty": 0.7, "held_lines": 0}]   # listed, never dropped


def test_held_is_never_zero_and_unknown_stays_open():
    ls = lines()
    doc = T.build(ls, "cand", "V-TEST", MASTER, [], [])
    f = fam(doc, "B10-06")
    assert f["state"] == T.FAM_HELD
    assert f["per_unit"]["m3"]["released_qty"] == 2.0     # the held 1.0 .. 3.0 and the UNKNOWN never enter it
    md = T.markdown(doc)
    assert "1 UNKNOWN" in md and "1.000 .. 3.000" in md


def test_stale_verdict_is_not_counted():
    ls = lines()
    v = whole_slab(ls)
    moved = copy.deepcopy(ls)
    moved[1] = mk("STR.CONC.SLAB", "S2", "MEASURED", 5.6)           # one own line changed after the verdict
    doc = T.build(moved, "cand", "V-TEST", MASTER, [v], [])
    assert grp(doc, "B10 Concrete")["verified_whole"] == 0
    assert doc["sides"][0]["verdicts"][0]["status"].startswith("STALE")


def test_discrepancy_over_one_percent_is_not_verified():
    ls = lines()
    doc = T.build(ls, "cand", "V-TEST", MASTER, [whole_slab(ls, checker=15.5 * 1.02)], [])
    assert grp(doc, "B10 Concrete")["verified_whole"] == 0
    assert "DISCREPANCY" in doc["sides"][0]["verdicts"][0]["status"]


def test_whole_verdict_on_part_of_a_family_does_not_verify_the_line():
    ls = lines()
    s1 = [x["line_id"] for x in ls if x["location"]["element_id"] == "S1"]
    v = EX.verdict_add(ls, candidate_version="V-TEST", boq_lines_sha256=EX.lines_sha256(ls), line_ids=s1,
                       scope="WHOLE", checker_qty=10.0, evidence=[{"sheet": "S-1", "printed_value": "200"}],
                       run_token="t", routine="Checker", verdict_commit="abcdef1", time="2026-11-02T00:00:00Z")
    doc = T.build(ls, "cand", "V-TEST", MASTER, [v], [])
    assert fam(doc, "B10-08")["verified_whole"] is False
    assert fam(doc, "B10-08")["per_unit"]["m3"]["verified_whole_qty"] == 10.0   # shown, never promoted


def test_record_of_older_version_carries_by_content_only():
    ls = lines()
    doc = T.build(ls, "cand", "V-NEW", MASTER, [whole_slab(ls, version="V-OLD")], [])
    assert doc["sides"][0]["verdicts"][0]["status"] == "CARRIED_BY_CONTENT"
    assert grp(doc, "B10 Concrete")["verified_whole"] == 1


def test_downgrade_moves_released_to_held_and_blocks_verification():
    ls = lines()
    ids = [x["line_id"] for x in ls if x["location"]["element_id"] == "S2"]
    dg = EX.downgrade_add(ls, candidate_version="V-TEST", line_ids=ids, state="HELD", basis_label="UNSUPPORTED BASIS",
                          reason="section not printed", evidence=[{"sheet": "S-1", "printed_value": "none"}],
                          run_token="t", routine="Checker", verdict_commit="abcdef1", time="2026-11-02T00:00:00Z")
    doc = T.build(ls, "cand", "V-TEST", MASTER, [whole_slab(ls)], [dg])
    f = fam(doc, "B10-08")
    assert f["state"] == T.FAM_HELD and f["verified_whole"] is False
    assert f["per_unit"]["m3"]["released_qty"] == 10.0 and f["per_unit"]["m3"]["held_unknown_lines"] == 1
    assert doc["sides"][0]["downgrades"][0]["status"] == "APPLIED"


def test_downgrade_never_promotes_and_stale_downgrade_binds_nothing():
    ls = lines()
    ids = [x["line_id"] for x in ls if x["location"]["element_id"] == "S2"]
    dg = EX.downgrade_add(ls, candidate_version="V-TEST", line_ids=ids, state="HELD", basis_label="X", reason="r",
                          evidence=[{"sheet": "S-1", "printed_value": "none"}], run_token="t", routine="Checker",
                          verdict_commit="abcdef1", time="2026-11-02T00:00:00Z")
    moved = copy.deepcopy(ls)
    moved[1] = mk("STR.CONC.SLAB", "S2", "MEASURED", 5.6)
    doc = T.build(moved, "cand", "V-TEST", MASTER, [], [dg])
    assert doc["sides"][0]["downgrades"][0]["status"].startswith("STALE")
    assert fam(doc, "B10-08")["state"] == T.MEASURED     # nothing else moved
    assert fam(doc, "B10-06")["state"] == T.FAM_HELD     # held stays held (never promoted)


def test_family_item_code_owned_twice_is_refused():
    bad = copy.deepcopy(MASTER)
    bad["families"][2]["item_codes"] = ["STR.CONC.SLAB"]
    with pytest.raises(ValueError):
        T.build(lines(), "cand", "V", bad, [], [])


REF = {"records": [{"id": "R1", "qty": 20.0, "unit": "م3"}, {"id": "R2", "qty": 16.0, "unit": "m3"},
                   {"id": "R3", "qty": 4.0, "unit": "طن"}]}


def pairs(*rows):
    return {"pairs": [dict(zip(("pair", "family", "item_codes", "unit", "reference_ids"), r), boundary="b")
                      for r in rows]}


def test_pairs_all_released_unknown_range_and_unit_refused():
    ls = lines()
    p = pairs(("slab", "B10-08", ["STR.CONC.SLAB"], "m3", ["R2"]),
              ("cols", "B10-06", ["STR.CONC.COLUMN"], "m3", ["R1"]),
              ("cols t", "B10-06", ["STR.CONC.COLUMN"], "m3", ["R3"]))
    doc = T.build(ls, "cand", "V", MASTER, [], [], reference=REF, pairs=p)
    rows = doc["pairs"][0]["rows"]
    assert rows[0]["outcome"] == "ALL_RELEASED" and rows[0]["variance_pct"] == -3.12   # (15.5 - 16) / 16
    assert rows[1]["outcome"].startswith("RANGE_OPEN") and "variance_pct" not in rows[1]   # UNKNOWN: no %
    assert rows[2]["outcome"].startswith("UNIT_MISMATCH")                                 # t vs m3, never converted


def test_pairs_bounded_range_gives_a_range_not_one_percent():
    ls = [x for x in lines() if x["location"]["element_id"] != "C3"]       # columns: 2.0 + bounded 1.0 .. 3.0
    p = pairs(("cols", "B10-06", ["STR.CONC.COLUMN"], "m3", ["R1"]))
    r = T.build(ls, "cand", "V", MASTER, [], [], reference=REF, pairs=p)["pairs"][0]["rows"][0]
    assert r["outcome"] == "RANGE" and (r["engine_low"], r["engine_high"]) == (3.0, 5.0)
    assert (r["variance_low_pct"], r["variance_high_pct"]) == (-85.0, -75.0)


def test_pair_naming_an_item_code_of_another_family_is_refused():
    p = pairs(("x", "B10-06", ["STR.CONC.SLAB"], "m3", ["R2"]))
    with pytest.raises(ValueError):
        T.build(lines(), "cand", "V", MASTER, [], [], reference=REF, pairs=p)


def test_committed_snapshots_are_well_formed_and_offline():
    here = ROOT / "research" / "agents_t469"
    vs = json.loads((here / "VERDICT_V2_SET_V3_0_40_SNAPSHOT.json").read_text(encoding="utf-8"))
    assert EX.validate_v2_set(vs) == []
    dg = json.loads((here / "DOWNGRADES_SNAPSHOT.json").read_text(encoding="utf-8"))
    assert dg["schema"] == EX.DOWNGRADE_SET_SCHEMA and all(EX.validate_downgrade(d) == [] for d in dg["downgrades"])
    src = (here / "t469_trade_scoreboard.py").read_text(encoding="utf-8")
    assert "../board" not in src and "docs/agents" not in src     # never the live board


def test_held_material_line_has_no_quantity():
    ls = lines() + [mk("FIN.WP.MEMBRANE_ROLLS", "R2", "BLOCKED_RFI", unit="m2", trade="WATERPROOFING")]
    doc = T.build(ls, "cand", "V", MASTER, [], [])
    w = grp(doc, "B8 Waterproofing")
    assert w["material_provisional"] == {"m2": 40.0} and w["material_held_lines"] == 1   # held never adds 0 or a qty
    assert "+1 held material lines, no qty" in T.markdown(doc)


def test_committed_v3041_table_is_the_markdown_of_the_committed_json():
    out = ROOT / "research" / "agents_t469" / "out"
    doc = json.loads((out / "T469_SCOREBOARD_V3_0_41.json").read_text(encoding="utf-8"))
    assert T.markdown(doc) == (out / "T469_SCOREBOARD_V3_0_41.md").read_text(encoding="utf-8")
    cand = doc["sides"][1]
    assert cand["boq_lines_sha256"][:8] == "5176c7c4" and doc["inputs"]["candidate"] == "5176c7c4ac273282"
    assert sum(g["expected"] for g in cand["groups"]) == 102
    assert sum(g["measured"] + g["held"] + g["unmeasured"] + g["excluded_only"] for g in cand["groups"]) == 102
