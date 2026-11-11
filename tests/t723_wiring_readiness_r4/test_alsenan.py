"""T-723 on the development villa: the committed readiness output equals a rebuild from merged repository files (+ the
pinned T-703 extract), every mapped host is a V3.0.71 line (stale 0), every ledger row is accounted once per piece, the
T-705 map is restated row for row, the beside register is rebuilt from the merged concrete Gate B builders, and the
known cross-piece facts hold (supersession, duplicates, beside restatements, pending lines, blocked hubs). Repository
files only; nothing is written."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t723"))
import t723_alsenan as A  # noqa: E402
import t723_rules as R  # noqa: E402

R698 = R.R698


@pytest.fixture(scope="module")
def built():
    return A.build()


@pytest.fixture(scope="module")
def rows(built):
    return {r["row"]: r for r in built["rows"]}


def test_committed_output_reproduces(built):
    assert A.OUT_JSON.read_text(encoding="utf-8") == A.dumps(built)
    assert A.OUT_CSV.read_text(encoding="utf-8") == A.to_csv(built)


def test_candidate_and_pins(built):
    assert built["candidate"] == "ARCH_TAKEOFF_V3.0.71"
    assert built["inputs_sha256"][A.IDX71] == built["line_index_sha256"]
    assert built["rule"] == ["R-T723-1", "1.0.0"]
    t703 = json.loads((ROOT / A.T703).read_text(encoding="utf-8"))
    assert t703["commit"].startswith("af54dee2") and t703["doc_blob"].startswith("4de5fedd")
    assert (len(t703["one_sided"]), len(t703["bound_rounding"])) == (18, 10)


def test_stale_zero_hosts_present_owner_named(built):
    tgt = A.index(A.IDX71)
    assert built["stale"] == 0
    for r in built["rows"]:
        assert r["class"] != R698.STALE
        if r["class"] in (R698.MAPPED, R698.HOST_CHANGED, R698.PENDING_CHANGE, R698.WRONG):
            assert r["host_line_id"] in tgt, r["row"]
        assert r["owner_family"] and r["owner"], r["row"]


def test_every_ledger_row_once(built):
    expect = {"T-707": 20, "T-711": 15, "T-712": 20, "T-721": 12, "T-709": 34, "T-710": 58, "T-713": 95,
              "T-715": 86, "T-718": 6}
    assert {p: v["rows"] for p, v in built["pieces"].items()} == expect
    keys = [r["row"] for r in built["rows"]]
    assert len(keys) == len(set(keys)) == sum(expect.values()) + 287


def test_t705_restated_row_for_row(built):
    s = built["restated_t705"]
    assert s["rows"] == s["t705_rows"] == 287
    assert s["classes_after"] == s["classes_before"]           # V3.0.71 moved no T-705 host (index lines equal)
    assert s["host_changed"] == []
    assert s["ruling_restate_rows"] == 116                     # every B4-09 bead ADD (Lead ruling 16:25)
    # BLANK-on-blank rows are TEXT now (rule 2), never KEEP: 17, and no other action moved
    assert s["actions_before"]["KEEP"] - s["actions_after"]["KEEP"] == s["actions_after"]["TEXT"] == 17


def test_beside_register(built):
    b = built["beside_register"]
    assert (b["v3_0_70"], b["v3_0_71"]) == (24, 40)
    assert len(b["changed_70_71"]) == 16                       # the T-704 AT_MOST lintel lines
    assert [x["one_sided_set"] for x in b["rounds"]] == [4, 22, 2, 0, 1, 2, 0, 16]


def test_concrete_round(rows, built):
    assert rows["T-711:L-061e18cf35a4b6b33d68"]["action"] == R.KEEP      # ST-03 AT_LEAST 0.355017 since V3.0.66
    for lid, old in (("L-e16c98075f69532a3dc7", 0.135473), ("L-0bb78accf8c0a0fbdbaf", 0.242309),
                     ("L-d53e5eb08e2c6c668254", 0.147657)):
        r = rows[f"T-712:{lid}"]
        assert r["action"] == R.RESTATE_BESIDE and f"AT_LEAST {old} ->" in r["action_reason"]
    tank = rows["T-707:L-c10e2945d582b5a03126"]
    assert tank["action"] == R.BESIDE and tank["after"] == {"kind": "ONE_SIDED", "side": "AT_LEAST", "value": 0.3287,
                                                             "low": None, "high": None, "note": tank["after"]["note"]}
    h = {x["hub"]: x for x in built["hub_order"]}["T-722"]
    assert (h["changed"], h["text_only"], h["added"], h["form_conflicts"]) == (18, 18, 0, [])
    for r in built["rows"]:                                     # a one-sided figure is never a range or 0
        a = r.get("after")
        if a and a["kind"] == R.ONE_SIDED:
            assert a["low"] is None and a["high"] is None and a["value"] > 0


def test_formwork_follows_t714(rows, built):
    fw = [r for r in built["rows"] if r["hub"] == "T-714"]
    assert len(fw) == 13 and all(r["action"] == R.CHANGE for r in fw)
    assert all(A.index(A.IDX71)[r["host_line_id"]]["item_code"] == "STR.FORMWORK" for r in fw)


def test_stairs_supersession_and_duplicates(rows, built):
    t718 = [r for r in built["rows"] if r["piece"] == "T-718"]
    sup = [r for r in built["rows"] if r["piece"] == "T-715" and r["live"] == R.SUPERSEDED]
    assert len(sup) == 4 and {r["live_of"] for r in sup} <= {r["row"] for r in t718}
    assert sorted(r["live"] for r in t718) == [R.DUPLICATE, R.DUPLICATE, R.LIVE, R.LIVE, R.LIVE, R.LIVE]
    assert rows["T-718:L-95b9555dd144951b071e"]["after"]["low"] == 13.8      # RS-C step 13.80 .. 16.52144 lm


def test_wp_round(rows, built):
    t710 = [r for r in built["rows"] if r["piece"] == "T-710"]
    assert sum(r["live"] == R.DUPLICATE for r in t710) == 22             # restates T-691 exactly
    new = {r["row"] for r in t710 if r["live"] == R.LIVE}
    assert new == {"T-710:L-2361d6ec13c952bd2ae3", "T-710:L-d7d1bf8c5991ccf69ea2", "T-710:L-1954878bb02c91139e1b",
                   "T-710:MISSING:FIN.WP.DOORWAY_TRANSITION[m2]/DOOR:D-GF-07-PANTRY/TRANSITION"}
    held = rows["T-710:MISSING:FIN.WP.DOORWAY_TRANSITION[m2]/DOOR:D-GF-07-PANTRY/TRANSITION"]
    assert held["action"] == R.ADD and held["after"]["kind"] == "BLANK" and held["held"] and held["qty"] is None


def test_masonry_waits_on_t703(built):
    t713 = [r for r in built["rows"] if r["piece"] == "T-713"]
    t703 = json.loads((ROOT / A.T703).read_text(encoding="utf-8"))
    pend = {r["host_line_id"] for r in t713 if r["class"] == R698.PENDING_CHANGE}
    assert pend == set(t703["one_sided"]) | set(t703["bound_rounding"])
    assert all(r["action"] in (R.NONE, R.KEEP) for r in t713)


def test_plaster_hub_blocked_items(built, rows):
    h = {x["hub"]: x for x in built["hub_order"]}
    assert (h["T-717"]["changed"], h["T-717"]["added"], h["T-717"]["blocked_rows"]) == (4, 32, 2)
    assert h["H2a"]["blocked_rows"] + h["H2b"]["blocked_rows"] == 116
    gf01 = rows["T-701:GF-01"]
    assert gf01["class"] == R698.MAPPED and any("F-T709-1" in f for f in gf01["flags"])
    band = rows["T-709:band:plaster"]
    assert band["host_line_id"] == "L-8cecb1d010d5aafbf25d" and (band["lo"], band["hi"]) == (0.839412, 0.870912)


def test_held_never_zero(built):
    for r in built["rows"]:
        if r["held"]:
            assert r["qty"] in (None,) or r.get("piece_round") == "T-705", r["row"]
        a = r.get("after")
        if a and a["kind"] in ("BLANK", "EXCLUDED"):
            assert a["value"] is None


def test_adverse_row_mapped_twice_is_refused(built):
    rs = copy.deepcopy([r for r in built["rows"] if r["piece"] == "T-711"][:2])
    rs[1]["row"] = rs[0]["row"]
    with pytest.raises(R.ReadinessError, match="mapped to two lines"):
        R.check_one_line_per_row(rs)


def test_adverse_conflict_on_real_rows_is_refused(built):
    a = copy.deepcopy(next(r for r in built["rows"] if r["row"] == "T-707:L-53f223b06db14ac41d47"))
    b = copy.deepcopy(a)
    b["piece"], b["row"] = "T-711", "T-711:fake"
    b["after"] = R.after(R.R705.BOUND, lo=0.46, hi=0.595)
    with pytest.raises(R.ReadinessError, match="CONFLICT"):
        R.resolve_live([a, b], A.ORDER, {})


def test_concrete_census_reconciles_with_t704_and_the_ledgers(built):
    """index census vs the T-704 run's code totals: equal for BEAM / COLUMN; GROUND_BEAM differs by exactly one line,
    the boundary G.B at N.G. L-fb7a6431 (index range 0 .. 3.5256, counted 'blocked' by the code totals: F-T723-3)."""
    c = built["conc_census_t722"]
    s704 = json.loads((ROOT / "research/agents_t704/summary_t704.json").read_text(encoding="utf-8"))["conc_code_totals"]
    for code in ("STR.CONC.BEAM", "STR.CONC.COLUMN"):
        a, b = c[code]["v3_0_71"], s704[f"{code}|m3"]["v3_0_71"]
        assert (a["released_m3"], a["bounded"], a["bounded_low_m3"], a["bounded_high_m3"]) == \
            (b["released"], b["bounded_lines"], b["held_low"], b["held_high"])
        assert (a["blank"], a["lines"] - a["excluded"]) == (b["blocked_lines"], b["lines"])
    a, b = c["STR.CONC.GROUND_BEAM"]["v3_0_71"], s704["STR.CONC.GROUND_BEAM|m3"]["v3_0_71"]
    assert (a["bounded"] - b["bounded_lines"], b["blocked_lines"] - a["blank"]) == (1, 1)
    assert a["bounded_high_m3"] - b["held_high"] == pytest.approx(3.5256) and a["bounded_low_m3"] == b["held_low"]
    col = c["STR.CONC.COLUMN"]["after_t722"]
    assert col["bounded_low_m3"] == 11.80007 and col["beside_sum_m3_run_record_only"] == {"AT_LEAST": 0.6574}  # T-707
    gb = c["STR.CONC.GROUND_BEAM"]
    assert gb["after_t722"]["beside_sum_m3_run_record_only"] == {"AT_LEAST": 5.099845}                       # T-712
    assert gb["v3_0_71"]["bounded_high_m3"] == 5.096771                                    # = T-712's 9 bounded lines
    for code, v in c.items():                                   # released never moves in a one-sided round
        assert v["after_t722"]["released_m3"] == v["v3_0_71"]["released_m3"], code
