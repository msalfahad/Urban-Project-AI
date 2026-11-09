"""T-637: BOQ_FAMILY_MASTER 1.56.0 (R-T637-1).

Synthetic villa K637 (not the training villa; hand values): one 0.20 m black wall W1, panel 10.0 m2 (5.0 lm run x 2.0 m):
  MAS.BLOCK 10.0 m2 (work) | ARCH.WALL_PANEL 10.0 m2 | ARCH.WALL_VOLUME 10.0 x 0.20 = 2.0 m3 | ARCH.WALL_RUN 5.0 lm
  MAS.UNITS.BLACK 10.0 x 12.5 = 125 pcs | MAS.MORTAR.BLACK 0.15 m3 | one lift landing door HELD blank.
By hand under the 1.56.0 mapping: B9 m2 = 10.0 (never 20.0), B9 pcs 125 apart, B9-04 m3 0.15, B6-08 pcs 1 HELD blank,
UNCODED (NO_FAMILY) none, the three register codes UNCODED (NOT_A_BOQ_LINE), no REGISTER_BESIDE_WORK pair.
Adverse: a material row in its work unit; a code in two families; a panel without its block twin; a panel quantity that
differs from its block; a volume that is not panel x thickness; a crosswalk key missing / in the wrong group.
Then the training-villa registry and reader outputs must equal their committed rebuilds."""

import copy
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t637"))
sys.path.insert(0, str(ROOT / "research/agents_t630"))
import build_master_1_56_0 as BM   # noqa: E402
import e2e_dry_run as E            # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

EL = "K637-WALLS:walls t=0.20#BLOCKWORK:K"
BASE = "K637-WALLS:walls t=0.20"


def _l(lid, code, unit, el=EL, cls="RELEASED", v=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": el, "class": cls, "measured_net": v,
            "held_low": None, "held_high": None, "binding": None, "unbound_records": []}


def _lines():
    return [_l("L1", "MAS.BLOCK", "m2", v=10.0), _l("L2", "ARCH.WALL_PANEL", "m2", v=10.0),
            _l("L3", "ARCH.WALL_VOLUME", "m3", v=2.0), _l("L4", "ARCH.WALL_RUN", "lm", el=BASE, v=5.0),
            _l("L5", "MAS.UNITS.BLACK", "pcs", v=125.0), _l("L6", "MAS.MORTAR.BLACK", "m3", v=0.15),
            _l("L7", "DOOR.LIFT_LANDING", "pcs", el="K637:LIFT:GF", cls="HELD")]


def _fam(code, grp, codes, **kw):
    return dict({"code": code, "group": grp, "item_en": code, "unit": None, "item_codes": codes,
                 "capability": "PARTIAL", "candidate": {"state": "IN_CANDIDATE_BASE_LINES"}}, **kw)


def _master_1_56():
    mats = {c: dict(m, rule=BM.MATERIAL_RULE) for c, m in BM.MATERIAL.items()}
    return {"families": [_fam("B9-01", "B9 Masonry", ["MAS.BLOCK", "MAS.UNITS.BLACK", "MAS.UNITS.WHITE"],
                              material_rows=mats),
                         _fam("B9-04", "B9 Masonry", sorted(BM.B9_04_CODES)),
                         _fam("B6-08", "B6 Openings", ["DOOR.LIFT_LANDING"])],
            "not_a_boq_line_codes": {c: {"evidence": r["evidence"]} for c, r in BM.REGISTER.items()},
            "item_codes_without_family": {c: "register" for c in BM.REGISTER}}


def _master_1_55():
    return {"families": [_fam("B9-01", "B9 Masonry", ["ARCH.WALL_PANEL", "ARCH.WALL_RUN", "ARCH.WALL_VOLUME",
                                                      "MAS.BLOCK"]),
                         _fam("B9-04", "B9 Masonry", [])],
            "not_a_boq_line_codes": {}, "item_codes_without_family": {}}


def _agg(master, lines=None):
    after = {l["line_id"]: l for l in (lines or _lines())}
    return E.aggregate(after, {}, [], master)


# ---------------------------------------------------------------- synthetic: normal
def test_hand_values_under_1_56_0():
    m = _master_1_56()
    assert BM.check_t637(m) == []
    _o, item, fam, grp, _u, per_line, unc = _agg(m)
    b9m2 = E._out(grp[("B9", "m2")], "m2")
    assert b9m2["released"] == "10" and b9m2["total"] == "10"            # the wall once, never 20
    assert E._out(fam[("B9", "B9-01", "pcs")], "pcs")["released"] == "125"
    assert E._out(fam[("B9", "B9-04", "m3")], "m3")["released"] == "0.15"
    assert ("B9", "B9-01", "m3") not in fam and ("B9", "B9-01", "lm") not in fam
    door = E._out(fam[("B6", "B6-08", "pcs")], "pcs")
    assert door["held_blank_n"] == 1 and door["total"] is None              # HELD blank, never 0
    assert {b for (b, c, u) in unc} == {E.UNCODED_NOT_A_LINE}
    assert sorted(c for (b, c, u) in unc) == sorted(BM.REGISTER)
    assert [d for d in E.same_quantity_codes(item) if d["kind"].startswith("REGISTER")] == []
    assert BM.material_guard(_lines(), m) == 1


def test_the_same_villa_under_1_55_0_shows_the_three_findings():
    _o, item, fam, grp, _u, per_line, unc = _agg(_master_1_55())
    assert E._out(grp[("B9", "m2")], "m2")["released"] == "20"           # panel + block: the wall twice
    assert [d["codes"] for d in E.same_quantity_codes(item)] == [["ARCH.WALL_PANEL", "MAS.BLOCK"]]
    assert sorted(c for (b, c, u) in unc if b == E.UNCODED_NO_FAMILY) == ["DOOR.LIFT_LANDING", "MAS.MORTAR.BLACK",
                                                                          "MAS.UNITS.BLACK"]


def test_register_pairing_on_the_synthetic_index():
    p = BM.register_pairing({"lines": _lines()})
    assert p["panel_block_pairs"] == 1 and p["panel_released_m2"] == 10.0 and p["volume_lines"] == 1
    assert p["run_lines"] == 1 and p["block_without_panel"] == []


# ---------------------------------------------------------------- synthetic: adverse
def test_adverse_material_row_in_its_work_unit_refused():
    m = _master_1_56()
    m["families"][0]["material_rows"]["MAS.UNITS.BLACK"]["unit"] = "m2"
    assert any("work unit" in b for b in BM.check_t637(m))
    lines = _lines()
    lines[4]["unit"] = "m2"                                               # 125 'm2' would be re-added into the work
    with pytest.raises(BM.MasterError, match="work unit"):
        BM.material_guard(lines, _master_1_56())
    m2 = _master_1_56()
    m2["families"][0]["material_rows"]["MAS.UNITS.BLACK"]["material_of"] = "MAS.OTHER"
    assert any("outside the family" in b for b in BM.check_t637(m2))


def test_adverse_code_in_two_families_refused():
    m = _master_1_56()
    m["families"][1]["item_codes"].append("MAS.UNITS.BLACK")
    assert any("owned by B9-01 and B9-04" in b for b in BM.check_t637(m))
    with pytest.raises(E.DryRunError, match="owned by"):
        _agg(m)
    m2 = _master_1_56()
    m2["families"][0]["item_codes"].append("ARCH.WALL_PANEL")             # owned AND NOT_A_BOQ_LINE
    assert any("NOT_A_BOQ_LINE and owned" in b for b in BM.check_t637(m2))


def test_adverse_register_pairing_breaches_refuse_the_ruling():
    lines = [l for l in _lines() if l["line_id"] != "L1"]                 # a panel with no block twin
    with pytest.raises(BM.MasterError, match="twin"):
        BM.register_pairing({"lines": lines})
    lines = _lines()
    lines[1]["measured_net"] = 10.5                                       # panel != block
    with pytest.raises(BM.MasterError, match="twin"):
        BM.register_pairing({"lines": lines})
    lines = _lines()
    lines[2]["measured_net"] = 1.5                                        # volume != panel x 0.20
    with pytest.raises(BM.MasterError, match="panel x"):
        BM.register_pairing({"lines": lines})
    lines = _lines()
    lines[1]["element_id"] = "K637:OTHER"                                 # rotated / mirrored id: still no twin
    with pytest.raises(BM.MasterError):
        BM.register_pairing({"lines": lines})


def test_adverse_crosswalk():
    m = json.loads(BM.NEW.read_text(encoding="utf-8"))
    sc, st = BM._json(BM.SCORECARD), BM._json(BM.STATEMENT)
    keys = dict(BM.KEYS)
    try:
        del BM.KEYS["T-543/blockwork"]
        with pytest.raises(BM.MasterError, match="missing"):
            BM.crosswalk(m, sc, st)
        BM.KEYS.update(keys)
        BM.KEYS["T-543/blockwork"] = ("B9", ["B9"], ["B10-07"], "wrong")
        with pytest.raises(BM.MasterError, match="not in"):
            BM.crosswalk(m, sc, st)
        BM.KEYS["T-543/blockwork"] = ("B9", ["B9", "B10"], ["B9-01"], "two groups, one target")
        with pytest.raises(BM.MasterError, match="one target"):
            BM.crosswalk(m, sc, st)
        BM.KEYS["T-543/blockwork"] = ("B14", ["B14"], [], "outside")
        with pytest.raises(BM.MasterError, match="not B1"):
            BM.crosswalk(m, sc, st)
    finally:
        BM.KEYS.clear()
        BM.KEYS.update(keys)


# ---------------------------------------------------------------- the committed registry
@pytest.fixture(scope="module")
def docs():
    return (json.loads(BM.OLD.read_text(encoding="utf-8")), json.loads(BM.NEW.read_text(encoding="utf-8")))


def test_builder_reproduces_the_committed_file():
    assert BM.text(BM.build()) == BM.NEW.read_text(encoding="utf-8")


def test_candidate_check_and_r_t637_1_clean(docs):
    _old, new = docs
    assert FMC.check(new, root=ROOT, is_ancestor=FMC.git_is_ancestor) == []
    assert BM.check_t637(new) == []


def test_only_the_three_families_and_the_listed_fields_change(docs):
    old, new = docs
    of, nf = {f["code"]: f for f in old["families"]}, {f["code"]: f for f in new["families"]}
    assert set(nf) - set(of) == {"B6-08"} and len(nf) == 104 and set(of) <= set(nf)
    for code in of:
        if code not in BM.CHANGED_FAMILIES:
            assert of[code] == nf[code], code
        assert of[code]["capability"] == nf[code]["capability"]                 # no capability change
    for k in ("released_configuration", "candidate", "candidate_packages", "pending_packages", "capability_states",
              "candidate_states", "candidate_state_definitions", "run_evidence", "census_gaps"):
        assert old[k] == new[k], k
    assert new["pending_packages"][0]["task"] == "T-507"                        # promotion is a separate row
    assert nf["B9-01"]["item_codes"] == ["MAS.BLOCK", "MAS.UNITS.BLACK", "MAS.UNITS.WHITE"]
    assert nf["B9-04"]["item_codes"] == ["MAS.GLUE.AAC", "MAS.MORTAR.BLACK"]
    assert nf["B6-08"]["item_codes"] == ["DOOR.LIFT_LANDING"] and nf["B6-08"]["candidate"]["state"] == "NOT_IN_CANDIDATE"
    assert set(new["not_a_boq_line_codes"]) == {"ARCH.EXTERIOR"} | set(BM.REGISTER)
    assert new["capability_counts"]["NOT_IMPLEMENTED"] == old["capability_counts"]["NOT_IMPLEMENTED"] + 1
    assert new["candidate_state_counts"]["NOT_IN_CANDIDATE"] == old["candidate_state_counts"]["NOT_IN_CANDIDATE"] + 1


def test_census_v3_0_57_rerun(docs):
    old, new = docs
    oc, nc = old["candidate_census"], new["candidate_census"]
    for code, row in nc["families"].items():
        if code not in BM.CHANGED_FAMILIES:
            assert row == oc["families"][code], code
    b = nc["families"]["B9-01"]
    assert b["lines"] == 28 and list(b["units"]) == ["m2"]
    assert b["units"]["m2"]["released_lines"] == 13 and b["units"]["m2"]["released"] == 467.7925
    assert oc["families"]["B9-01"]["units"]["m2"]["released"] == 935.585            # = 2 x 467.7925 before
    assert nc["families"]["B9-04"]["in_candidate"] == "no" and nc["families"]["B6-08"]["in_candidate"] == "no"
    nab = nc["not_a_boq_lines"]
    assert {c: len(v["line_ids"]) for c, v in nab.items()} == {"ARCH.EXTERIOR": 1, "ARCH.WALL_PANEL": 26,
                                                               "ARCH.WALL_RUN": 7, "ARCH.WALL_VOLUME": 26}
    assert nc["issue_counts"] == {} and nc["no_family"] == {} and nc["stale_in_candidate_vs_registry"] == []
    p = nc["register_pairing_v3_0_57"]
    assert (p["panel_block_pairs"], p["panel_released_m2"], p["volume_lines"], p["run_lines"]) == (26, 467.7925, 26, 7)
    assert p["block_without_panel"] == ["HOUSE_BELOW_NG:ANNEX_S", "HOUSE_BELOW_NG:MAIN_S"]


def test_crosswalk_is_one_key_one_target(docs):
    x = docs[1]["trade_key_crosswalk"]
    assert x["counts"] == {"keys": 50, "single_group": 45, "multi_group": 5}
    assert all(v["master_group"] in BM.GROUPS + (BM.MULTI,) for v in x["keys"].values())
    c = x["v11_trade_code_to_master_groups"]
    assert c["B5"] == ["B4"] and c["B12"] == ["B6"] and c["B7"] == ["B5", "B7", "B13"]   # why the code is never the key


# ---------------------------------------------------------------- the reader on V3.0.58 + V16
@pytest.fixture(scope="module")
def reader():
    import reader_1_56_0 as R
    return R, R.build()


def test_reader_outputs_are_the_committed_rebuild(reader):
    R, b = reader
    assert R.OUT_JSON.read_text(encoding="utf-8") == R.dumps(b)
    assert R.OUT_MD.read_text(encoding="utf-8") == R.render_md(b)


def test_reader_acceptance(reader):
    R, b = reader
    a = b["acceptance"]
    assert b["lines"] == 5143
    assert a["uncoded_no_family_lines_1_55_0"] == 91 and a["uncoded_no_family_lines_1_56_0"] == 0
    assert a["b9_04_state_1_55_0"].startswith("MISSING") and a["b9_04_state_1_56_0"].startswith("PRESENT")
    assert a["b6_08_state_1_56_0"] == "HELD (every live line HELD)"
    assert len(a["register_beside_work_pairs_1_55_0"]) == 1 and a["register_beside_work_pairs_1_56_0"] == []
    assert a["other_family_rows_byte_equal"] and a["differences"] == []
    assert a["aggregation_re_adds_exactly"]
    assert set(b["moved_codes"]) == R.MOVED_CODES                  # every moved code carries overlay lines
    h = b["b9_by_hand"]
    m2 = b["b9_rows_1_56_0"]["B9-01|m2"]
    assert m2["released"] == h["MAS.BLOCK|m2"]["released"] and m2["released_n"] == h["MAS.BLOCK|m2"]["released_n"]
    assert Decimal(b["b9_rows_1_56_0"]["B9-01|pcs"]["released"]) == \
        Decimal(h["MAS.UNITS.BLACK|pcs"]["released"]) + Decimal(h.get("MAS.UNITS.WHITE|pcs", {}).get("released", "0"))
    assert Decimal(b["b9_rows_1_56_0"]["B9-04|m3"]["released"]) == Decimal(h["MAS.MORTAR.BLACK|m3"]["released"])
    assert b["released_quantities_changed"] == 0 and b["candidate_files_touched"] == 0


# ---------------------------------------------------------------- writers (env flag only)
@pytest.mark.skipif(os.environ.get("URBAN_T637_WRITE") != "1", reason="writer: URBAN_T637_WRITE=1 only")
def test_write_master():
    doc = BM.write()
    assert doc["version"] == "1.56.0"


@pytest.mark.skipif(os.environ.get("URBAN_T637_MANIFEST_WRITE") != "1", reason="writer: URBAN_T637_MANIFEST_WRITE=1 only")
def test_write_rules_manifest():
    """r2 (Verifier 18:32): register 1.56.0 in rules/RULES_MANIFEST.json by the manifest tool (T-507 precedent), no hand digest."""
    from tools import m9_rules_manifest as M
    assert M.check() == []                       # copies / exports / referenced profiles unchanged before the rebuild
    M.build()
    assert M.check() == []


def test_the_new_master_is_registered_in_the_rule_store():
    """1.56.0 lives under rules/ (read by V1 .. V2.2 through the manifest): it must carry its AUTHORED entry and digest."""
    import hashlib
    from tools import m9_rules_manifest as M
    rel = "coverage/BOQ_FAMILY_MASTER_1.56.0.json"
    assert rel in M.AUTHORED
    m = json.loads((ROOT / "rules/RULES_MANIFEST.json").read_text(encoding="utf-8"))
    assert m["files"][rel] == {"kind": "AUTHORED",
                               "sha256": hashlib.sha256((ROOT / "rules" / rel).read_bytes()).hexdigest()}
    assert M.check() == []


@pytest.mark.skipif(os.environ.get("URBAN_T637_READER_WRITE") != "1", reason="writer: URBAN_T637_READER_WRITE=1 only")
def test_write_reader():
    import reader_1_56_0 as R
    b = R.write_outputs()
    assert b["acceptance"]["uncoded_no_family_lines_1_56_0"] == 0
