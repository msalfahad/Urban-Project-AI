"""T-140: coverage census V2 (engine.source.coverage_census_v2, BOQ_FAMILY_MASTER 1.1.0) on a synthetic villa (not a
client drawing). Hand expectations (every figure from the printed sizes below, by hand):

ARCHITECTURAL
  B3-01 bedroom porcelain 4.00 x 3.00 = 12.000 m2 (SOURCE_DERIVED)                          -> FOUND m2 12.000
  B3-02 bath wet tile 2.40 x 1.80 = 4.320 m2 (MEASURED)                                       -> FOUND m2 4.320
  B3-04 ONE family under TWO keys: FIN.MARBLE.THRESHOLD 0.90 x 0.20 = 0.180 and 0.80 x 0.20 = 0.160 m2, plus one
        ARCH.THRESHOLD BLOCKED_RFI (no size)                                                 -> FOUND m2 0.340, held 1
  B8-03 FIN.WP.WALL_UPTURN 2 x (2.40 + 1.80) = 8.40 lm less door 0.80 = 7.60 lm x 0.20 = 1.520 m2; FIN.WP.TERMINATION
        bounded 0 .. 0.80 lm                                                                 -> FOUND m2 1.520 | lm held
  B7-03 two riser lines BLOCKED_RFI                                                          -> HELD, quantity UNKNOWN
  B9-01 ARCH.WALL_RUN 2 x (4.00 + 3.00) = 14.000 lm; ARCH.WALL_PANEL 14.00 x 2.90 .. 14.00 x 3.20 = 40.600 .. 44.800 m2
        bounded                                                                              -> HELD (lm is not block m2)
  B6-02 DOOR.INTERNAL.PVC 2 pcs                                                              -> FOUND pcs 2
  B8-07 nothing emitted (FIN.WP.BALCONY absent, the architectural route ran)                 -> NOT_FOUND_IN_SOURCE
STRUCTURAL
  B10-02 footing 1.50 x 1.50 x 0.50 = 1.125 m3, and a second line for the same footing that the first names
         never-additive                                                                     -> FOUND m3 1.125, 1 not summed
  B10-06 column 0.30 x 0.30 x 3.00 .. 3.60 = 0.270 .. 0.324 m3 bounded                       -> HELD
  B10-10 pool 2.000 m3 with no steel line                                                    -> FOUND; B11-03 HELD MISSING_DATA
OTHER
  ARCH.EXTERIOR (listed without family in 1.1.0) and X.UNOWNED (nobody's code)               -> listed, never silent
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import boq_line as BL  # noqa: E402
from engine.source import coverage_census as CS1  # noqa: E402
from engine.source import coverage_census_v2 as C  # noqa: E402
from engine.source import rule_store as RS  # noqa: E402

PID = "synthetic-villa-t140"
REV = "c3" * 32


def line(code, unit, eid, *, ev="SOURCE_DERIVED", net=None, rng=None, pe=None, nadd=(), trade=None):
    kw = {}
    if ev == "BOUNDED_EXPOSURE":
        kw = {"bounded_range": {"low": rng[0], "high": rng[1], "basis": "test"}, "rfi": {"question": "height?"}}
    if ev == "BLOCKED_RFI":
        kw = {"rfi": {"question": "size not printed"}}
    if ev in ("EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE"):
        kw = {"notes": "not applicable (test)"}
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=eid, physical_element=pe, formula="hand (test)", rule_id="T140",
                        rule_version="test", item_en=code, item_ar=code, never_additive_with=nadd,
                        trade=trade or (None if code in BL.ITEMS else "OTHER"), **kw)


def villa():
    f1 = line("STR.CONC.FOOTING", "m3", "F1", net=1.50 * 1.50 * 0.50)
    f1b = line("STR.CONC.FOOTING", "m3", "F1-dup", net=1.50 * 1.50 * 0.50)
    f1 = dict(f1, never_additive_with=[f1b["line_id"]])
    return [
        line("FIN.FLOOR.PORCELAIN", "m2", "GF-BED", net=4.00 * 3.00),
        line("FIN.FLOOR.WET_TILE", "m2", "GF-BATH", ev="MEASURED", net=2.40 * 1.80),
        line("FIN.MARBLE.THRESHOLD", "m2", "D1", net=0.90 * 0.20),
        line("FIN.MARBLE.THRESHOLD", "m2", "D2", net=0.80 * 0.20),
        line("ARCH.THRESHOLD", "m2", "D3", ev="BLOCKED_RFI"),
        line("FIN.WP.WALL_UPTURN", "m2", "GF-BATH", net=(2 * (2.40 + 1.80) - 0.80) * 0.20),
        line("FIN.WP.TERMINATION", "lm", "GF-BATH", ev="BOUNDED_EXPOSURE", rng=(0.0, 0.80)),
        line("FIN.MARBLE.RISER", "m2", "ST1", ev="BLOCKED_RFI"),
        line("FIN.MARBLE.RISER", "m2", "ST2", ev="BLOCKED_RFI"),
        line("ARCH.WALL_RUN", "lm", "GF-W20", ev="PROVISIONAL", net=2 * (4.00 + 3.00)),
        line("ARCH.WALL_PANEL", "m2", "GF-W20", ev="BOUNDED_EXPOSURE", rng=(14.00 * 2.90, 14.00 * 3.20),
             trade="MASONRY"),
        line("DOOR.INTERNAL.PVC", "pcs", "GF-DOORS", net=2.0),
        line("ARCH.EXTERIOR", "m2", "GARDEN", net=30.0),
        line("X.UNOWNED", "m2", "ODD", net=1.0),
        f1, f1b,
        line("STR.CONC.COLUMN", "m3", "C1", ev="BOUNDED_EXPOSURE", rng=(0.30 * 0.30 * 3.00, 0.30 * 0.30 * 3.60)),
        line("STR.CONC.POOL", "m3", "POOL", ev="PROVISIONAL", net=2.0, pe="POOL"),
    ]


@pytest.fixture(scope="module")
def master():
    return C.load_master()


@pytest.fixture(scope="module")
def run(master):
    return C.census(villa(), master=master)


def row(rows, code):
    return next(r for r in rows[0] if r["code"] == code)


def test_master_is_1_1_0_and_checked_against_the_manifest(master):
    assert master["version"] == "1.1.0" and len(master["families"]) == 99
    man = json.loads((ROOT / "rules/RULES_MANIFEST.json").read_text(encoding="utf-8"))
    assert C.MASTER_REL in man["files"]


def test_old_census_and_rule_store_untouched():
    # the released run keeps census V1 on 1.0.0 (the census gap V2 closes is still there in V1)
    assert RS.family_master()["version"] == "1.0.0"
    v1 = {r["code"]: r for r in CS1.census(villa(), structural_run=True, arch_run=True)}
    assert v1["B8-03"]["run_state"] == "NOT_FOUND_IN_SOURCE" and v1["B6-02"]["run_state"] == "NOT_IMPLEMENTED"


def test_one_family_under_two_keys_found_with_held_apart(run):
    r = row(run, "B3-04")
    assert r["run_state"] == "FOUND" and r["lines"] == 3
    c = r["by_unit"]["m2"]
    assert c["found_lines"] == 2 and c["found_qty"] == pytest.approx(0.340, abs=1e-9)
    assert c["held_lines"] == 1 and c["held_qty"] == "UNKNOWN" and c["held_range"] is None


def test_hand_quantities_found(run):
    assert row(run, "B3-01")["by_unit"]["m2"]["found_qty"] == pytest.approx(12.000, abs=1e-9)
    assert row(run, "B3-02")["by_unit"]["m2"]["found_qty"] == pytest.approx(4.320, abs=1e-9)
    assert row(run, "B6-02")["run_state"] == "FOUND" and row(run, "B6-02")["by_unit"]["pcs"]["found_qty"] == 2.0
    b = row(run, "B8-03")
    assert b["run_state"] == "FOUND" and b["by_unit"]["m2"]["found_qty"] == pytest.approx(1.520, abs=1e-9)
    # units never mixed: the bounded termination stays in lm, held, apart from the m2 found
    assert b["by_unit"]["lm"]["found_qty"] is None and b["by_unit"]["lm"]["held_range"] == \
        {"low": 0.0, "high": 0.8, "complete": True}


def test_held_family_is_unknown_never_zero(run):
    r = row(run, "B7-03")
    assert r["run_state"] == "HELD"
    c = r["by_unit"]["m2"]
    assert c["found_qty"] is None and c["held_qty"] == "UNKNOWN" and c["held_unbounded_lines"] == 2
    col = row(run, "B10-06")["by_unit"]["m3"]
    assert row(run, "B10-06")["run_state"] == "HELD"
    assert col["held_range"]["low"] == pytest.approx(0.270) and col["held_range"]["high"] == pytest.approx(0.324)


def test_quantity_only_outside_the_family_unit_is_not_found(run):
    r = row(run, "B9-01")
    assert r["run_state"] == "HELD" and "QUANTITY_ONLY_OUTSIDE_FAMILY_UNIT" in r["flags"]
    assert r["by_unit"]["lm"]["found_qty"] == pytest.approx(14.000)
    assert r["by_unit"]["m2"]["held_range"] == {"low": pytest.approx(40.6), "high": pytest.approx(44.8),
                                                "complete": True}


def test_absent_family_not_found_in_source(run):
    r = row(run, "B8-07")
    assert r["run_state"] == "NOT_FOUND_IN_SOURCE" and r["lines"] == 0 and r["by_unit"] == {}


def test_never_additive_line_not_summed_twice(run):
    r = row(run, "B10-02")
    c = r["by_unit"]["m3"]
    assert c["found_lines"] == 1 and c["found_qty"] == pytest.approx(1.125) and c["not_summed_lines"] == 1
    assert "NEVER_ADDITIVE_LINES_NOT_SUMMED" in r["flags"]


def test_scope_steel_missing_is_held(run):
    assert row(run, "B10-10")["run_state"] == "FOUND"
    r = row(run, "B11-03")
    assert r["run_state"] == "HELD" and r["reason"].startswith("MISSING_DATA")
    assert row(run, "B11-01")["run_state"] == "NOT_FOUND_IN_SOURCE"     # structural route ran, no steel line


def test_capability_states_and_no_line_key(run):
    assert row(run, "B1-01")["run_state"] == "NOT_IMPLEMENTED"
    assert row(run, "B12-02")["run_state"] == "BLOCKED_BY_SOURCE"
    r = row(run, "B2-03")
    assert r["run_state"] == "NO_LINE_KEY" and "ARCH_FLOOR_AREAS.json" in r["reason"]


def test_unowned_and_without_family_codes_listed(run):
    meta = run[1]
    assert meta["unowned_codes"] == {"X.UNOWNED": 1}
    assert list(meta["codes_without_family"]) == ["ARCH.EXTERIOR"]
    s = C.summary(run[0], meta)
    assert s["silent_omissions"] == 1 and s["families"] == 99 and sum(s["by_run_state"].values()) == 99


def test_every_family_has_a_state_and_a_reason(run):
    assert all(r["run_state"] in C.STATES and r["reason"] for r in run[0])


def test_line_order_does_not_change_the_census(master):
    a = C.census(villa(), master=master)[0]
    b = C.census(list(reversed(villa())), master=master)[0]
    strip = [(r["code"], r["run_state"], r["lines"],
              {u: {k: v for k, v in c.items() if k != "not_summed_lines"} for u, c in r["by_unit"].items()})
             for r in a]
    strip_b = [(r["code"], r["run_state"], r["lines"],
                {u: {k: v for k, v in c.items() if k != "not_summed_lines"} for u, c in r["by_unit"].items()})
               for r in b]
    assert strip == strip_b


def test_line_in_a_unit_outside_the_family_is_flagged(master):
    ls = villa() + [line("FIN.FLOOR.PORCELAIN", "m", "GF-EDGE", net=3.0)]
    r = next(x for x in C.census(ls, master=master)[0] if x["code"] == "B3-01")
    assert r["run_state"] == "FOUND" and "LINE_UNIT_OUTSIDE_FAMILY_UNIT: m" in r["flags"]
    assert r["by_unit"]["m2"]["found_qty"] == pytest.approx(12.0) and r["by_unit"]["m"]["found_qty"] == 3.0


def test_invalid_line_refused_never_counted_as_zero(master):
    bad = copy.deepcopy(villa()[0])
    bad["measured_net"] = None                            # a quantity state without its quantity
    with pytest.raises(BL.LineError):
        C.census([bad], master=master)


def test_run_kind(master):
    rel = {r["code"]: r for r in C.census(villa(), master=master, run_kind="released")[0]}
    assert rel["B8-06"]["run_state"] == "NOT_RUN" and "released_method_reads" in rel["B8-06"]["reason"]
    cand = {r["code"]: r for r in C.census(villa(), master=master, run_kind="candidate")[0]}
    assert cand["B8-06"]["run_state"] == "NOT_FOUND_IN_SOURCE"          # in the candidate (V2.11+ roof lines)
    with pytest.raises(ValueError):
        C.census(villa(), master=master, run_kind="other")


def test_routes_not_run():
    m = C.load_master()
    arch_only = [ln for ln in villa() if not ln["item_code"].startswith("STR.")]
    rows = {r["code"]: r for r in C.census(arch_only, master=m)[0]}
    assert rows["B10-02"]["run_state"] == "NOT_RUN" and rows["B11-03"]["run_state"] != "HELD"
    st_only = [ln for ln in villa() if ln["item_code"].startswith("STR.")]
    rows = {r["code"]: r for r in C.census(st_only, master=m)[0]}
    assert rows["B3-01"]["run_state"] == "NOT_RUN"


def test_route_census_never_makes_a_family_found(master):
    cov = [{"FAMILY": "COLUMN_NECKS", "STATE": "PARTLY_QUANTIFIED", "REASON": "r"},
           {"FAMILY": "LINTELS", "STATE": "NO_EVIDENCE_FOUND", "REASON": "r"}]
    rows = {r["code"]: r for r in C.census(villa(), master=master, family_coverage=cov)[0]}
    assert rows["B10-03"]["run_state"] == "HELD" and rows["B10-03"]["lines"] == 0
    assert rows["B9-02"]["run_state"] == "NOT_FOUND_IN_SOURCE"


def test_membrane_roll_plans_from_material_results(master):
    mats = [{"material_spec": {"kind": "MEMBRANE_SHEET"}, "state": "PROVISIONAL"}]
    r = next(x for x in C.census(villa(), master=master, material_results=mats)[0] if x["code"] == "B8-05")
    assert r["run_state"] == "FOUND" and "FOUND_IN_MATERIAL_RESULTS_ONLY" in r["flags"] and r["by_unit"] == {}


def test_master_validation(master):
    m = copy.deepcopy(master)
    m["families"][1]["item_codes"] = list(m["families"][1]["item_codes"]) + ["FIN.FLOOR.PORCELAIN"]
    with pytest.raises(C.MasterError):
        C.validate_master(m)
    m = copy.deepcopy(master)
    m["families"][0]["capability"] = "DONE"
    with pytest.raises(C.MasterError):
        C.validate_master(m)
    m = copy.deepcopy(master)
    m["item_codes_without_family"]["FIN.SKIRTING"] = "x"
    with pytest.raises(C.MasterError):
        C.validate_master(m)


def test_every_item_master_code_is_owned_or_listed(master):
    owner = C.validate_master(master)
    without = master["item_codes_without_family"]
    assert [c for c in BL.ITEMS if c not in owner and c not in without] == []


def test_the_t130_census_gaps_are_mapped(master):
    fam = {f["code"]: set(f["item_codes"]) for f in master["families"]}
    assert "FIN.WP.WALL_UPTURN" in fam["B8-03"]
    assert fam["B6-02"] == {"DOOR.INTERNAL.PVC"} and fam["B6-04"] == {"ARCH.WINDOW"}
    assert {"DOOR.EXTERNAL.ALUMINIUM", "DOOR.MAIN_ENTRANCE"} <= fam["B6-03"]
    assert {"MAS.BLOCK", "ARCH.WALL_RUN", "ARCH.WALL_PANEL", "ARCH.WALL_VOLUME"} == fam["B9-01"]
    assert "FIN.MARBLE.THRESHOLD" in fam["B3-04"] and fam["B2-02"] == {"ARCH.SPACE"} and fam["B2-03"] == set()


def test_family_units_parser():
    assert C.family_units("m2 + lm") == {"m2", "lm"}
    assert C.family_units("m2 (m3 / pcs procurement)") == {"m2", "m3", "pcs"}
    assert C.family_units("-") == set() and C.family_units("bags / m3") == {"pcs", "m3"}
    assert C.family_units("m2 / rolls") == {"m2", "pcs"} and C.family_units("zone") == set()


def test_membrane_roll_lines_in_pcs_are_the_family_quantity(master):
    ls = villa() + [line("FIN.WP.MEMBRANE_ROLLS", "pcs", "GF-BATH", net=2.0)]
    r = next(x for x in C.census(ls, master=master)[0] if x["code"] == "B8-05")
    assert r["run_state"] == "FOUND" and r["by_unit"]["pcs"]["found_qty"] == 2.0 and r["flags"] == []
