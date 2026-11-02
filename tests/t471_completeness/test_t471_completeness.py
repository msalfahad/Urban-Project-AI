"""T-471: research/agents_t471/t471_completeness.py, the completeness matrix, component register and component -> BOQ
line map. Synthetic hand fixture 'villa K471' (not the development villa): six registry families, lines made with
engine/source/boq_line.make_line, verdicts and downgrades with tools/boq_export_v1 (the Checker's own record builders).
Every expected figure is a hand calculation. Adverse cases: a dropped component, a duplicated component, an unmapped
line, missing evidence, a not-applicable component carrying a quantity, a downgrade, a code of another family, a
reversed (mirrored) line order. The last two tests pin the committed development-villa register (structure only)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t471"))

from engine.source import boq_line as BL  # noqa: E402
from tools import boq_export_v1 as EX  # noqa: E402
import t471_completeness as T  # noqa: E402

PID, REV = "synthetic-k471", "b" * 64
MASTER = {"version": "test", "families": [
    {"code": "B10-08", "group": "B10 Concrete", "item_en": "Suspended slabs", "unit": "m3", "item_codes": ["STR.CONC.SLAB"]},
    {"code": "B10-06", "group": "B10 Concrete", "item_en": "Columns", "unit": "m3", "item_codes": ["STR.CONC.COLUMN"]},
    {"code": "B10-10", "group": "B10 Concrete", "item_en": "Pool / lift pit", "unit": "m3",
     "item_codes": ["STR.CONC.POOL", "STR.CONC.LIFT"]},
    {"code": "B9-02", "group": "B9 Masonry", "item_en": "Lintels", "unit": "m3", "item_codes": ["STR.CONC.LINTEL"]},
    {"code": "B1-05", "group": "B1 Site", "item_en": "Anti-termite", "unit": "m2", "item_codes": []},
    {"code": "B8-07", "group": "B8 Waterproofing", "item_en": "Balconies", "unit": "m2", "item_codes": ["FIN.WP.BALCONY"]},
]}


def mk(code, el, ev, net=None, unit="m3", br=None):
    kw = {}
    if ev == "BLOCKED_RFI":
        kw["rfi"] = {"question": "which section?"}
    if ev == "EXCLUDED_WITH_REASON":
        kw["notes"] = "not drawn"
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=el, bounded_range=br, formula="L x W x D", rule_id="R-T471",
                        rule_version="1.0.0", trade="CONCRETE", item_en=code, item_ar=code, **kw)


def lines():
    return [
        mk("STR.CONC.SLAB", "S1", "MEASURED", 12.0),                                   # slab 12.0 + 3.5 = 15.5
        mk("STR.CONC.SLAB", "S2", "MEASURED", 3.5),
        mk("STR.CONC.COLUMN", "C1", "MEASURED", 1.8),                                  # released 1.8
        mk("STR.CONC.COLUMN", "C2", "BOUNDED_EXPOSURE", None, br={"low": 0.4, "high": 0.9, "basis": "range"}),
        mk("STR.CONC.COLUMN", "C3", "BLOCKED_RFI"),                                    # UNKNOWN, never 0
        mk("STR.CONC.POOL", "POOL-W", "MEASURED", 2.75),                               # pool walls
        mk("STR.CONC.LIFT", "PIT-R", "MEASURED", 1.2),                                 # lift-pit raft
    ]


def comp(cid, fam, app, codes, ev=("ST p.9 schedule",), level=1, **kw):
    c = {"component_id": cid, "family": fam, "name": cid, "applicability": app, "item_codes": list(codes),
         "evidence": list(ev), "level": level, "method": "m", "formula": "f", "materials": "none"}
    c.update(kw)
    return c


def register():
    return {"schema": T.REGISTER_SCHEMA, "project": "K471", "version": "1", "components": [
        comp("K-SLAB", "B10-08", "APPLICABLE", ["STR.CONC.SLAB"]),
        comp("K-COL", "B10-06", "APPLICABLE", ["STR.CONC.COLUMN"]),
        comp("K-POOL", "B10-10", "APPLICABLE", ["STR.CONC.POOL"]),
        comp("K-PIT", "B10-10", "APPLICABLE", ["STR.CONC.LIFT"]),
        comp("K-LINTEL", "B9-02", "APPLICABLE", ["STR.CONC.LINTEL"], ev=("ST p.13 lintel schedule",)),
        comp("K-TERMITE", "B1-05", "NOT_APPLICABLE", [], ev=("ST p.8 notes 1-24: none requires it",)),
        comp("K-BALC", "B8-07", "POSSIBLY_APPLICABLE", ["FIN.WP.BALCONY"], ev=(), level=5,
             exceptions="no balcony label; terrace edge open"),
    ]}


def whole_slab(ls, checker=15.5):
    ids = [x["line_id"] for x in ls if x["item_code"] == "STR.CONC.SLAB"]
    return EX.verdict_add(ls, candidate_version="V-K", boq_lines_sha256=EX.lines_sha256(ls), line_ids=ids,
                          scope="WHOLE", checker_qty=checker, evidence=[{"sheet": "S-1", "printed_value": "t 200"}],
                          run_token="t", routine="Checker", verdict_commit="abcdef1", time="2026-11-02T00:00:00Z")


def row(doc, cid):
    return next(r for r in doc["rows"] if r["component_id"] == cid)


def kinds(doc):
    return [i["kind"] for i in doc["issues"]]


def test_five_states_normal_case():
    ls = lines()
    doc = T.build(register(), ls, MASTER, [whole_slab(ls)], [], "V-K")
    assert row(doc, "K-SLAB")["state"] == "APPLICABLE_VERIFIED" and row(doc, "K-SLAB")["gate"] == "VERIFIED"
    assert row(doc, "K-SLAB")["quantities"]["m3"]["verified"] == 15.5
    assert row(doc, "K-COL")["state"] == "APPLICABLE_HELD" and row(doc, "K-COL")["gate"] == "HELD"
    assert row(doc, "K-COL")["reason"] == "2 of 3 lines held"
    assert row(doc, "K-POOL")["gate"] == "MEASURED"                      # released, never VERIFIED without a verdict
    assert row(doc, "K-POOL")["state"] == "APPLICABLE_HELD"
    assert row(doc, "K-LINTEL")["state"] == "APPLICABLE_UNMEASURED" and row(doc, "K-LINTEL")["gate"] == "MISSING"
    assert row(doc, "K-TERMITE")["state"] == "NOT_APPLICABLE"
    assert row(doc, "K-BALC")["state"] == "POSSIBLY_APPLICABLE"
    assert doc["states"] == {"NOT_APPLICABLE": 1, "APPLICABLE_VERIFIED": 1, "APPLICABLE_HELD": 3,
                             "APPLICABLE_UNMEASURED": 1, "POSSIBLY_APPLICABLE": 1}
    assert doc["issues"] == [] and doc["complete_map"] is True


def test_held_is_never_zero_and_unknown_stays_open():
    doc = T.build(register(), lines(), MASTER, [], [], "V-K")
    q = row(doc, "K-COL")["quantities"]["m3"]
    assert q["released"] == 1.8                                          # the held 0.4 .. 0.9 never enters it
    assert (q["held_low"], q["held_high"], q["held_unknown_lines"]) == (0.4, 0.9, 1)
    md = T.markdown(doc, register())
    assert "1.800 m3 released + held 0.400 .. 0.900 + 1 held UNKNOWN" in md


def test_dropped_component_is_reported_not_assumed_out_of_scope():
    reg = register()
    reg["components"] = [c for c in reg["components"] if c["component_id"] != "K-COL"]   # columns dropped
    doc = T.build(reg, lines(), MASTER, [], [], "V-K")
    assert {"kind": "FAMILY_NOT_IN_REGISTER", "family": "B10-06", "item_en": "Columns"} in doc["issues"]
    unm = sorted(i["line_id"] for i in doc["issues"] if i["kind"] == "UNMAPPED_LINE")
    assert len(unm) == 3                                                 # its three lines surface, never dropped
    assert doc["complete_map"] is False


def test_duplicated_component_is_reported_on_every_line():
    reg = register()
    dup = copy.deepcopy(reg["components"][0])
    dup["component_id"] = "K-SLAB-COPY"
    reg["components"].append(dup)
    doc = T.build(reg, lines(), MASTER, [], [], "V-K")
    d = [i for i in doc["issues"] if i["kind"] == "DOUBLY_MAPPED_LINE"]
    assert len(d) == 2 and all(i["components"] == ["K-SLAB", "K-SLAB-COPY"] for i in d)
    assert doc["complete_map"] is False
    reg["components"].append(copy.deepcopy(reg["components"][1]))      # same id twice
    assert "DUPLICATE_COMPONENT_ID" in kinds(T.build(reg, lines(), MASTER, [], [], "V-K"))


def test_element_prefix_splits_one_family_without_double_mapping():
    reg = register()
    for c in reg["components"]:
        if c["component_id"] in ("K-POOL", "K-PIT"):
            c["item_codes"] = ["STR.CONC.POOL", "STR.CONC.LIFT"]
    reg["components"][2]["element_prefix"] = "POOL-"
    reg["components"][3]["element_prefix"] = ["PIT-"]
    doc = T.build(reg, lines(), MASTER, [], [], "V-K")
    assert len(row(doc, "K-POOL")["line_ids"]) == 1 and len(row(doc, "K-PIT")["line_ids"]) == 1
    assert row(doc, "K-PIT")["quantities"]["m3"]["released"] == 1.2
    assert doc["complete_map"] is True


def test_unmapped_line_of_no_family_is_listed():
    ls = lines() + [mk("STR.CONC.OTHER", "X1", "MEASURED", 0.7)]
    doc = T.build(register(), ls, MASTER, [], [], "V-K")
    assert [i["item_code"] for i in doc["issues"] if i["kind"] == "UNMAPPED_LINE"] == ["STR.CONC.OTHER"]


def test_evidence_level_and_code_ownership_are_required():
    reg = register()
    reg["components"][5]["evidence"] = []                                # NOT_APPLICABLE without evidence
    reg["components"][0]["level"] = 7
    reg["components"][1]["item_codes"].append("STR.CONC.SLAB")          # another family's code
    reg["components"][4]["applicability"] = "MAYBE"
    doc = T.build(reg, lines(), MASTER, [], [], "V-K")
    k = kinds(doc)
    for want in ("NO_EVIDENCE", "INVALID_RULE_LEVEL", "CODE_NOT_OWNED_BY_FAMILY", "INVALID_APPLICABILITY",
                 "DOUBLY_MAPPED_LINE"):
        assert want in k, want
    assert doc["complete_map"] is False


def test_not_applicable_with_a_quantity_line_is_a_conflict():
    ls = lines() + [mk("FIN.WP.BALCONY", "B1", "MEASURED", 4.0, unit="m2")]
    reg = register()
    reg["components"][6].update(applicability="NOT_APPLICABLE", evidence=["no balcony drawn"])
    doc = T.build(reg, ls, MASTER, [], [], "V-K")
    assert {"kind": "NA_WITH_QUANTITY_LINES", "component_id": "K-BALC", "lines": 1} in doc["issues"]
    ls2 = lines() + [mk("FIN.WP.BALCONY", "B1", "EXCLUDED_WITH_REASON", None, unit="m2")]
    assert "NA_WITH_QUANTITY_LINES" not in kinds(T.build(reg, ls2, MASTER, [], [], "V-K"))   # an excluded line is the NA record


def test_applicable_with_only_excluded_lines_is_flagged():
    ls = lines() + [mk("STR.CONC.LINTEL", "L1", "EXCLUDED_WITH_REASON", None)]
    doc = T.build(register(), ls, MASTER, [], [], "V-K")
    assert row(doc, "K-LINTEL")["state"] == "APPLICABLE_HELD"
    assert "APPLICABLE_BUT_ONLY_EXCLUDED" in kinds(doc)


def test_downgrade_and_partial_verdicts_never_verify():
    ls = lines()
    ids = [x["line_id"] for x in ls if x["location"]["element_id"] == "S2"]
    dg = EX.downgrade_add(ls, candidate_version="V-K", line_ids=ids, state="HELD", basis_label="UNSUPPORTED BASIS",
                          reason="t not printed", evidence=[{"sheet": "S-1", "printed_value": "none"}], run_token="t",
                          routine="Checker", verdict_commit="abcdef1", time="2026-11-02T00:00:00Z")
    doc = T.build(register(), ls, MASTER, [whole_slab(ls)], [dg], "V-K")
    r = row(doc, "K-SLAB")
    assert r["state"] == "APPLICABLE_HELD" and r["quantities"]["m3"]["released"] == 12.0
    s1 = [x["line_id"] for x in ls if x["location"]["element_id"] == "S1"]
    part = EX.verdict_add(ls, candidate_version="V-K", boq_lines_sha256=EX.lines_sha256(ls), line_ids=s1,
                          scope="COMPONENT", checker_qty=12.0, evidence=[{"sheet": "S-1", "printed_value": "t"}],
                          run_token="t", routine="Checker", verdict_commit="abcdef1", time="2026-11-02T00:00:00Z")
    assert row(T.build(register(), ls, MASTER, [part], [], "V-K"), "K-SLAB")["gate"] == "MEASURED"


def test_registry_gap_component_is_kept_and_reported():
    reg = register()
    reg["components"].append(comp("K-GAP", None, "POSSIBLY_APPLICABLE", [], ev=(), level=5))
    doc = T.build(reg, lines(), MASTER, [], [], "V-K")
    assert {"kind": "REGISTRY_GAP", "component_id": "K-GAP", "name": "K-GAP"} in doc["issues"]
    assert row(doc, "K-GAP")["state"] == "POSSIBLY_APPLICABLE" and row(doc, "K-GAP")["line_ids"] == []
    assert doc["complete_map"] is True                                   # the line map itself stays complete
    ls = lines() + [mk("EXT.POOL.FACE", "PF", "BLOCKED_RFI", unit="m2")]  # a code no family owns
    reg["components"][-1]["item_codes"] = ["EXT.POOL.FACE"]
    doc = T.build(reg, ls, MASTER, [], [], "V-K")
    assert "UNMAPPED_LINE" not in kinds(doc) and len(row(doc, "K-GAP")["line_ids"]) == 1
    reg["components"][-1]["item_codes"] = ["STR.CONC.SLAB"]             # a gap may not claim a family's code
    assert "CODE_NOT_OWNED_BY_FAMILY" in kinds(T.build(reg, ls, MASTER, [], [], "V-K"))


def test_item_code_mode_counts_and_never_overstates_verified():
    rows = [{"item_code": "STR.CONC.SLAB", "unit": "m3", "released_lines": 2, "verified_whole_lines": 2,
             "released_qty": 15.5, "held_lines": 0, "held_unknown_lines": 0, "held_low": 0.0, "held_high": 0.0,
             "excluded_lines": 0},
            {"item_code": "STR.CONC.COLUMN", "unit": "m3", "released_lines": 1, "verified_whole_lines": 0,
             "released_qty": 1.8, "held_lines": 2, "held_unknown_lines": 1, "held_low": 0.4, "held_high": 0.9,
             "excluded_lines": 0},
            {"item_code": "STR.CONC.POOL", "unit": "m3", "released_lines": 2, "verified_whole_lines": 1,
             "released_qty": 4.0, "held_lines": 0, "held_unknown_lines": 0, "held_low": 0.0, "held_high": 0.0,
             "excluded_lines": 0},
            {"item_code": "STR.CONC.XYZ", "unit": "m3", "released_lines": 1, "verified_whole_lines": 0,
             "released_qty": 0.5, "held_lines": 0, "held_unknown_lines": 0, "held_low": 0.0, "held_high": 0.0,
             "excluded_lines": 0}]
    ls, cls = T.code_lines(rows)
    doc = T.collapse_code_issues(T.build(register(), ls, MASTER, classes=cls))
    assert row(doc, "K-SLAB")["state"] == "APPLICABLE_VERIFIED"
    q = row(doc, "K-COL")["quantities"]["m3"]
    assert (q["released"], q["held_low"], q["held_high"], q["held_unknown_lines"]) == (1.8, 0.4, 0.9, 1)
    p = row(doc, "K-POOL")
    assert p["gate"] == "MEASURED" and p["quantities"]["m3"]["verified"] == 0.0   # mixed code: never overstated
    assert {"kind": "UNMAPPED_CODE", "item_code": "STR.CONC.XYZ", "lines": 1} in doc["issues"]
    assert row(doc, "K-SLAB")["item_codes"] == ["STR.CONC.SLAB"]


def test_mirrored_line_order_gives_the_same_matrix():
    ls = lines()
    a = T.build(register(), ls, MASTER, [whole_slab(ls)], [], "V-K")
    b = T.build(register(), list(reversed(ls)), MASTER, [whole_slab(ls)], [], "V-K")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


DEV = ROOT / "research" / "agents_t471" / "EIMP_REGISTER_DEV_VILLA.json"
MASTER_137 = ROOT / "rules" / "coverage" / "BOQ_FAMILY_MASTER_1.37.0.json"


def test_dev_villa_register_is_structurally_complete():
    reg = json.loads(DEV.read_text(encoding="utf-8"))
    master = json.loads(MASTER_137.read_text(encoding="utf-8"))
    issues = T.validate_register(reg, master)                          # every family, evidence, levels, codes
    assert [i["kind"] for i in issues] == ["REGISTRY_GAP", "REGISTRY_GAP"]   # only the two stated gaps
    for c in reg["components"]:
        for k in ("method", "formula", "materials", "sources", "rules"):
            assert c.get(k), (c["component_id"], k)


def test_dev_villa_register_claims_every_registry_code_once():
    reg = json.loads(DEV.read_text(encoding="utf-8"))
    master = json.loads(MASTER_137.read_text(encoding="utf-8"))
    owned = sorted(c for f in master["families"] for c in f.get("item_codes") or ())
    claimed = sorted(c for comp_ in reg["components"] if comp_["family"] for c in comp_.get("item_codes") or ())
    assert claimed == owned                                              # no code unclaimed, none claimed twice


def test_committed_dev_villa_matrix_reproduces(tmp_path):
    out = tmp_path / "m.json"
    rc = T.main(["--register", str(DEV), "--scoreboard",
                 str(ROOT / "research" / "agents_t469" / "out" / "T469_SCOREBOARD_V3_0_41.json"),
                 "--override", str(ROOT / "research" / "agents_t471" / "V3_0_42_CODE_OVERRIDE.json"),
                 "--master", str(MASTER_137), "--out", str(out)])
    assert rc == 0
    got = json.loads(out.read_text(encoding="utf-8"))
    want = json.loads((ROOT / "research" / "agents_t471" / "out" / "T471_MATRIX_V3_0_42.json").read_text(encoding="utf-8"))
    for k in ("inputs",):                                                # paths differ only by checkout
        got.pop(k), want.pop(k)
    assert got == want
    assert got["complete_map"] is True and got["issue_counts"] == {"REGISTRY_GAP": 2}
    assert sum(got["states"].values()) == got["components"] == 106
