"""T-473 DOWNGRADE_DRIFT_CHECK_V2: the public run reads no live board; a drifting record fails only when it binds a
schedule line; promotion stays refused; DG-2ddc451c17d2b589 binds no straight-bar row, by id and by section basis.
Writes only to tmp_path."""
import copy
import csv
import importlib.util
import json
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/agents_t374"


def _load():
    spec = importlib.util.spec_from_file_location("t473_v2", HERE / "t374_drift_check_v2.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V = _load()
B = V.B
DG = "DG-2ddc451c17d2b589"
DG_LINES = ["L-0bb78accf8c0a0fbdbaf", "L-0e852cca42fb8b765c58", "L-1487bdda099006e0c4ba", "L-c0b7102a36344a0349f5"]


def _rec(k, ids, state="HELD", resolved=False, sets=("V3.0.41",)):
    return {"downgrade_id": k, "state": state, "resolved": resolved, "basis_label": "UNSUPPORTED BASIS", "unit": "kg",
            "candidate_version": "ARCH_TAKEOFF_V3.0.41", "line_content_sha256": None, "engine_qty": 1.0,
            "verdict_sets": list(sets), "line_ids": sorted(ids)}


def _with(snap, *recs):
    s = copy.deepcopy(snap)
    s["records"] = sorted(s["records"] + list(recs), key=lambda r: r["downgrade_id"])
    s["record_count"] = len(s["records"])
    return s


# ---------------------------------------------------------------- the committed copy (R-T473-1)

def test_v2_copy_carries_source_shas_counts_board_commit_and_supersedes_v1():
    snap = V.load_snapshot_v2()
    assert snap["schema"] == "T374_BOUND_DOWNGRADES_V2" and snap["policy"] == V.POLICY
    assert snap["record_count"] == len(snap["records"]) == 22
    assert set(snap["source_record_count"]) == set(snap["source_sha256"])
    assert snap["source_record_count"]["V3.0.29"] == 11                    # 10 (T-411 copy) + DG-2ddc451c
    assert len(snap["board_commit"]) == 40
    assert snap["supersedes"] == {"file": "T374_BOUND_DOWNGRADES.json", "sha256": V.sha256(V.SNAPSHOT_V1)}
    v1 = B.load_snapshot()
    assert {r["downgrade_id"] for r in snap["records"]} - {r["downgrade_id"] for r in v1["records"]} == {DG}
    rec = next(r for r in snap["records"] if r["downgrade_id"] == DG)
    assert rec["line_ids"] == DG_LINES and rec["state"] == "HELD" and rec["resolved"] is False and rec["unit"] == "m3"


def test_the_public_run_names_no_live_board_by_default():
    assert V.board_verdicts_dir({}) is None
    assert V.board_verdicts_dir({V.ENV_BOARD: "  "}) is None
    assert V.board_verdicts_dir({V.ENV_BOARD: "/x/verdicts"}) == Path("/x/verdicts")
    # V1 vs V2 differs only by the new record, which binds no schedule line: reported, not failed
    rep = V.check_v2(V.load_snapshot_v2(), B.load_snapshot(), V.bbs_line_ids())
    assert rep[0] == f"record {DG} on the board, missing from the snapshot: binds no schedule line (reported, not failed)"
    assert rep[1].startswith("verdict set V3.0.29: DOWNGRADES.json sha256 ") and rep[1].endswith("reported)")
    assert len(rep) == 2


def test_live_board_against_the_v2_copy_only_when_named():
    d = V.board_verdicts_dir()
    if d is None or not d.is_dir():
        pytest.skip(f"no live verdicts folder named ({V.ENV_BOARD} unset): the public run reads no board state")
    V.check_v2(B.snapshot_downgrades(d), V.load_snapshot_v2(), V.bbs_line_ids())   # reports are allowed, binding fails


# ---------------------------------------------------------------- (1) DG-2ddc451c binds no schedule row

def test_dg_2ddc451c_binds_no_bbs_line_by_id_census():
    ids = V.bbs_line_ids()
    assert len(ids) == 442 and not set(DG_LINES) & set(ids)


def test_dg_2ddc451c_section_basis_leaves_the_straight_bars_invariant():
    rec = next(r for r in V.load_snapshot_v2()["records"] if r["downgrade_id"] == DG)
    cen = V.section_invariance(rec)
    assert [c["span"] for c in cen] == ["GSO-17E-17F-1", "GSO-15C-7CC-1", "GSO-142-7D8-1", "GSO-114-115-7DF-1"]
    assert all(c["candidates"] == ["LT2_5M", "LT5M"] and c["invariant"] for c in cen)
    assert all(c["bars"] == [["TOP", 3, 14], ["BOTTOM_ROW_1", 3, 14], ["BOTTOM_ROW_2", 3, 14]] for c in cen)
    assert V.must_hold(cen) == []
    st = {c["span"]: sorted(r["row_status"] for r in c["rows"]) for c in cen}
    assert st == {"GSO-17E-17F-1": ["HELD"], "GSO-15C-7CC-1": ["SCHEDULED"] * 3,
                  "GSO-142-7D8-1": ["SCHEDULED"] * 3, "GSO-114-115-7DF-1": ["BOUNDED_NO_ROW"]}
    # hand: 9 bars T14 x (2.45 + 2.40) m x 196/162 kg/m = 52.811111 kg; the 6 dp rows add to ..112 (storage rounding)
    hand = Decimal(9) * (Decimal("2.45") + Decimal("2.40")) * Decimal(196) / Decimal(162)
    assert hand.quantize(Decimal("0.000001")) == Decimal("52.811111")
    assert abs(V.scheduled_kg(cen) - hand) < Decimal("0.000003")


def test_schedule_built_on_the_v2_copy_equals_the_committed_schedule(tmp_path):
    lines, pop_of = B.load_candidate()
    rows, _ = B.build(lines, pop_of, B.shape_status(), B.lap_status(), B.t318_line_ids(),
                      downgrades=V.load_snapshot_v2())
    out = tmp_path / "s.csv"
    B.write_csv(rows, out)
    assert out.read_text(encoding="utf-8") == V.BBS_CSV.read_text(encoding="utf-8")


# ---------------------------------------------------------------- adverse: (a) binding FAILS, (b) non-binding PASSES

def test_a_new_record_binding_a_bbs_line_fails_naming_it():
    snap = V.load_snapshot_v2()
    live = _with(snap, _rec("DG-BINDS", ["L-3f26163f50298305091b", "L-not-in-bbs"]))
    with pytest.raises(V.ScheduleRefused, match=r"record DG-BINDS on the board, missing from the snapshot -> binds "
                                                r"L-3f26163f50298305091b"):
        V.check_v2(live, snap, V.bbs_line_ids())


def test_a_new_record_binding_no_bbs_line_passes_with_a_report_line():
    snap = V.load_snapshot_v2()
    live = _with(snap, _rec("DG-CONCRETE", ["L-concrete-1", "L-concrete-2"]))
    assert V.check_v2(live, snap, V.bbs_line_ids()) == [
        "record DG-CONCRETE on the board, missing from the snapshot: binds no schedule line (reported, not failed)"]


def test_a_changed_binding_record_and_its_set_fail_and_a_removed_unbinding_one_is_reported():
    snap = V.load_snapshot_v2()
    live = copy.deepcopy(snap)
    a97 = next(r for r in live["records"] if r["downgrade_id"] == "DG-a97ec2ea66e02194")
    a97["resolved"] = True
    live["source_sha256"] = dict(live["source_sha256"], **{a97["verdict_sets"][-1]: "0" * 64})
    with pytest.raises(V.ScheduleRefused, match=r"record DG-a97ec2ea66e02194 differs \(resolved\).*verdict set"):
        V.check_v2(live, snap, V.bbs_line_ids())
    gone = dict(snap, records=[r for r in snap["records"] if r["downgrade_id"] != DG], record_count=21)
    assert V.check_v2(gone, snap, V.bbs_line_ids()) == [
        f"record {DG} in the snapshot, not on the board: binds no schedule line (reported, not failed)"]


def test_a_copy_with_a_wrong_record_count_fails(tmp_path):
    snap = dict(V.load_snapshot_v2(), record_count=21)
    with pytest.raises(V.ScheduleRefused, match="record_count 21 != its 22 records"):
        V.check_v2(V.load_snapshot_v2(), snap, V.bbs_line_ids())
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(snap), encoding="utf-8")
    with pytest.raises(V.ScheduleRefused, match="record_count 21 != 22 records"):
        V.load_snapshot_v2(p)


# ---------------------------------------------------------------- adverse: (c) promotion refused

def test_a_downgrade_that_would_promote_is_refused_on_either_side(tmp_path):
    snap = V.load_snapshot_v2()
    up = _rec("DG-PROMOTE", ["L-concrete-9"], state="VERIFIED")
    with pytest.raises(V.ScheduleRefused, match=r"board records \['DG-PROMOTE'\].*never promote"):
        V.check_v2(_with(snap, up), snap, V.bbs_line_ids())
    with pytest.raises(V.ScheduleRefused, match=r"snapshot records \['DG-PROMOTE'\].*never promote"):
        V.check_v2(snap, _with(snap, up), V.bbs_line_ids())
    d = tmp_path / "verdicts" / "V3.0.41"
    d.mkdir(parents=True)
    (d / "DOWNGRADES.json").write_text(json.dumps({"downgrades": [up]}), encoding="utf-8")
    with pytest.raises(V.ScheduleRefused, match="state VERIFIED is not a downgrade"):
        V.make_snapshot_v2(tmp_path / "verdicts", "0" * 40)


def test_make_snapshot_v2_from_hand_built_verdicts(tmp_path):
    d = tmp_path / "verdicts" / "V3.0.41"
    d.mkdir(parents=True)
    (d / "DOWNGRADES.json").write_text(json.dumps({"downgrades": [_rec("DG-Z", ["L-1"]), _rec("DG-Y", ["L-2"])]}),
                                       encoding="utf-8")
    s = V.make_snapshot_v2(tmp_path / "verdicts", "a" * 40)
    assert s["record_count"] == 2 and s["source_record_count"] == {"V3.0.41": 2} and s["board_commit"] == "a" * 40
    assert [r["downgrade_id"] for r in s["records"]] == ["DG-Y", "DG-Z"]
    assert s["supersedes"]["sha256"] == V.sha256(V.SNAPSHOT_V1)


# ---------------------------------------------------------------- R-T473-4 adverse: candidate sections that differ

def test_span_whose_candidate_sections_differ_names_the_scheduled_rows_to_hold(tmp_path):
    t138 = tmp_path / "t138_fake.py"
    t138.write_text('DETAILS = {"LT5M": {"bars": [("TOP", 3, 14), ("BOTTOM", 3, 14)]},\n'
                    '           "LT2_5M": {"bars": [("TOP", 2, 12), ("BOTTOM", 2, 12)]}}\n', encoding="utf-8")
    cen = tmp_path / "census.csv"
    with open(cen, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["line_id", "run", "titles"])
        w.writeheader()
        w.writerow({"line_id": "L-C1", "run": "1A+2B#1", "titles": "LT2_5M+LT5M"})
    bbs = tmp_path / "bbs.csv"
    with open(bbs, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["line_id", "element_id", "component", "row_status", "net_kg_low"])
        w.writeheader()
        w.writerow({"line_id": "L-S1", "element_id": "HL:GROUND_SYSTEM_STEEL:GSO-1A-2B-1:TOP", "component": "TOP",
                    "row_status": "SCHEDULED", "net_kg_low": "5.000000"})
        w.writerow({"line_id": "L-S2", "element_id": "HL:GROUND_SYSTEM_STEEL:GSO-1A-2B-1:STIRRUP",
                    "component": "STIRRUP", "row_status": "HELD", "net_kg_low": ""})
        w.writerow({"line_id": "L-S3", "element_id": "HL:GROUND_SYSTEM_STEEL:GSO-1A-2B-10:TOP", "component": "TOP",
                    "row_status": "SCHEDULED", "net_kg_low": "7.000000"})          # another span: not matched
    out = V.section_invariance(_rec("DG-T", ["L-C1", "L-NOT-IN-CENSUS"]), census=cen, bbs=bbs, t138=t138)
    assert out[0]["invariant"] is False and out[0]["bars"] is None
    assert V.must_hold(out) == [("GSO-1A-2B-1", "L-S1")]
    assert out[1] == {"line_id": "L-NOT-IN-CENSUS", "span": None, "invariant": None, "rows": []}   # not assumed
    with pytest.raises(V.ScheduleRefused, match="run id"):
        V._run_to_band("1A-2B")
