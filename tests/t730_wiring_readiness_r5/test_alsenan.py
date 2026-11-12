"""T-730 on the development villa: the committed readiness output equals a rebuild from merged repository files (+ the
pinned T-717 extract), every mapped host is a V3.0.73 line (stale 0), every ledger row is accounted once per piece, the
T-723 map is restated row for row with the T-722 / T-703 rows wired, and the cross-piece facts hold by hand (census
deltas equal the ledgers' own totals, supersessions, the carried T-707 / T-714 conflict, blockers per hub). Repository
files only; nothing is written."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t730"))
import t730_alsenan as A  # noqa: E402
import t730_rules as R  # noqa: E402

R698, R705, R723 = R.R698, R.R705, R.R723


@pytest.fixture(scope="module")
def built():
    return A.build()


@pytest.fixture(scope="module")
def rows(built):
    return {r["row"]: r for r in built["rows"]}


def by_line(built, lid, piece=None):
    return [r for r in built["rows"] if r["host_line_id"] == lid and (piece is None or r["piece"] == piece)]


def test_committed_output_reproduces(built):
    assert A.OUT_JSON.read_text(encoding="utf-8") == A.dumps(built)
    assert A.OUT_CSV.read_text(encoding="utf-8") == A.to_csv(built)


def test_candidate_pins_and_extract(built):
    assert built["candidate"] == "ARCH_TAKEOFF_V3.0.73"
    assert built["inputs_sha256"][A.IDX73] == built["line_index_sha256"]
    assert built["rule"] == ["R-T730-1", "1.0.0"]
    t717 = json.loads((ROOT / A.T717).read_text(encoding="utf-8"))
    assert t717["commit"].startswith("9b998fc8") and t717["base"] == A.CANDIDATE
    assert (len(t717["changed"]), len(t717["added"])) == (4, 32)


def test_stale_zero_and_every_row_once(built):
    assert built["stale"] == 0 and built["restated_t723"]["rows"] == 633
    keys = [r["row"] for r in built["rows"]]
    assert len(keys) == len(set(keys))
    tgt = A.index(A.IDX73)
    for r in built["rows"]:
        assert r["class"] != R698.STALE
        if r["host_line_id"]:
            assert r["host_line_id"] in tgt


def test_piece_counts(built):
    p = built["pieces"]
    assert {k: v["rows"] for k, v in p.items()} == {"T-714": 370, "T-724": 10, "T-725": 20, "T-726": 15, "T-727": 6,
                                                   "T-728": 116, "T-731": 4}
    assert p["T-714"]["actions"] == {"BESIDE": 90, "CHANGE": 80, "TEXT": 200}
    assert p["T-714"]["live"] == {"CONFLICT": 13, "LIVE": 353, "SUPERSEDED": 4}


def test_t722_and_t703_rows_wired(built, rows):
    m = built["merged_hubs"]
    assert (m["T-722"]["rows"], m["T-722"]["wired"], m["T-722"]["still_moving"]) == (54, 36, [])
    assert m["T-703"]["still_moving"] == []
    t713 = [r for r in rows.values() if r["piece"] == "T-713"]
    assert len(t713) == 95 and all(r["action"] in (R.KEEP, R.NONE) for r in t713)
    assert all(R698.PENDING_CHANGE != r["class"] for r in t713)          # T-703 merged: nothing pends on it
    # a T-707 plate row narrowed by T-722 is WIRED (index 0.45738 .. 0.595)
    (r,) = by_line(built, "L-53f223b06db14ac41d47", "T-707")
    assert r["action"] == R.WIRED and r["class"] == R698.HOST_CHANGED


def test_hub_sizes_and_blockers(built):
    h = {x["hub"]: x for x in built["hub_order"]}
    assert [x["hub"] for x in built["hub_order"]] == A.HUB_ORDER
    assert (h["T-717"]["changed"], h["T-717"]["added"], h["T-717"]["buildable_after_earlier_hubs"]) == (4, 32, True)
    assert (h["C10"]["changed"], h["C10"]["added"], h["C10"]["buildable_after_earlier_hubs"]) == (2, 4, True)
    assert (h["T-729"]["changed"], h["T-729"]["text_only"], len(h["T-729"]["conflict_lines"])) == (186, 191, 13)
    assert not h["T-729"]["buildable_after_earlier_hubs"]
    assert any(b.startswith("WAITS T-732") for b in h["T-729"]["open_blockers"])
    assert h["H2a"]["added"] == 14 and h["H2a"]["buildable_after_earlier_hubs"]
    assert h["H2b"]["open_blockers"] == ["WAITS T-314 r3 (face rows replace the blank facade host)"]
    assert h["H4"]["open_blockers"] == [A.HUB_WAITS["H4"]] and h["H5"]["open_blockers"] == [A.HUB_WAITS["H5"]]
    assert h["H1R"]["changed_ids"] == ["L-35341ff2e6a848b9436b"]


def test_formwork_census_equals_ledger_totals(built):
    c = built["census_formwork_t729"]["STR.FORMWORK"]
    before, after = c["v3_0_73"]["sums_by_state"], c["after_t729_projection"]["sums_by_state"]
    t714 = json.loads((ROOT / A.T714).read_text(encoding="utf-8"))["summary"]
    assert round(after["released"] - before["released"], 6) == float(t714["fix_rows_m2"])      # 33.127058
    assert after["bounded_low"] == 87.942377                    # T-714 87.941284 + T-724 0.001093
    assert after["bounded_high"] == float(t714["bounded_high_m2"])
    assert after["at_least_beside"] == float(t714["at_least_m2"])
    s = built["census_formwork_t729"]["STR.FORMWORK.STAIR"]["after_t729_projection"]
    lows = round(s["sums_by_state"]["at_least_beside"] + s["sums_by_state"]["bounded_low"], 6)
    assert lows == float(json.loads((ROOT / A.T725).read_text(encoding="utf-8"))["sum_of_lows_m2_beside"])
    assert s["sums_by_state"]["bounded_high"] == round(0.843465 + 2.38, 6)       # T-731 high on L-9c3643da


def test_concrete_census_c10(built):
    gb = built["census_concrete_c10"]["STR.CONC.GROUND_BEAM"]
    assert gb["v3_0_73"]["counts"]["bounded"] == 9 and gb["after_c10_projection"]["counts"]["bounded"] == 8
    assert gb["after_c10_projection"]["sums_by_state"]["bounded_high"] == 1.571171
    assert gb["after_c10_projection"]["sums_by_state"]["at_most_beside"] == 3.5256
    st = built["census_concrete_c10"]["STR.CONC.STAIR"]
    assert round(st["v3_0_73"]["sums_by_state"]["at_least_beside"]
                 - st["after_c10_projection"]["sums_by_state"]["at_least_beside"], 6) == 0.000001
    for code, v in built["census_concrete_c10"].items():
        assert v["v3_0_73"]["sums_by_state"]["released"] == v["after_c10_projection"]["sums_by_state"]["released"]


def test_supersessions(built):
    (o,) = by_line(built, "L-7863355dfcb68a681d2d", "T-711")
    (n,) = by_line(built, "L-7863355dfcb68a681d2d", "T-731")
    assert (o["live"], n["live"], n["action"]) == (R.SUPERSEDED, R.LIVE, R.RESTATE_BESIDE)
    (o,) = by_line(built, "L-9c3643da524267bf47f6", "T-725")
    (n,) = by_line(built, "L-9c3643da524267bf47f6", "T-731")
    assert (o["live"], n["live"], n["after"]["high"]) == (R.SUPERSEDED, R.LIVE, 0.843465)
    (n,) = by_line(built, "L-3280c42cb578a211045e", "T-724")
    assert n["live"] == R.LIVE and n["after"]["low"] == 3.559782
    beads = [r for r in built["rows"] if r["piece"] == "T-697" and r["t723_action"] == R.ADD]
    assert len(beads) == 116 and all(r["live"] == R.SUPERSEDED for r in beads)
    assert not any(f.startswith("RULING_RESTATE:") for r in built["rows"] for f in r["flags"])


def test_conflict_t707_t714_carried(built):
    lines = set(built["conflict_register"])
    assert len(lines) == 13
    for lid in lines:
        rs = by_line(built, lid)
        assert {r["piece"] for r in rs} == {"T-707", "T-714"} and {r["live"] for r in rs} == {R.CONFLICT}


def test_form_restate_and_cap_zero(built):
    (r,) = by_line(built, "L-fb7a6431fede62e93fd5", "T-724")
    assert r["action"] == R.CHANGE and R.FORM_RESTATE in r["action_reason"] and r["after"]["value"] == 3.5256
    (z,) = by_line(built, "L-867e155d6f8f0a452eba", "T-714")
    assert z["after"]["kind"] == R705.BLANK and any(f.startswith("CAP_ZERO") for f in z["flags"])


def test_held_never_zero(built):
    for r in built["rows"]:
        a = r.get("after")
        if a and a["kind"] == R723.ONE_SIDED:
            assert a["value"] > 0
        if r["held"]:
            assert r["qty"] is None
    R698.check_no_zero_for_held(built["rows"])


def test_owner_and_blockers_well_formed(built):
    R705.check_owner_named(built["rows"])
    R.check_blockers(built["rows"])


def test_adverse_real_row_id_missing_never_maps(built):
    tgt = A.index(A.IDX73)
    with pytest.raises(R.ReadinessError):
        R.resolve("L-0eac839", tgt)                       # T-726 short id cut to 7 hex digits
    gone = dict(tgt)
    gone.pop("L-35341ff2e6a848b9436b")                     # its decor-group neighbour stays: never re-mapped
    with pytest.raises(R.ReadinessError):
        R.resolve("L-35341ff2", gone)


def test_adverse_conflict_without_register_fails(built):
    rs = copy.deepcopy([r for r in built["rows"] if r["piece"] in ("T-707", "T-714")
                        and r["host_line_id"] in built["conflict_register"]])
    for r in rs:
        r["live"], r["blockers"] = None, []
    with pytest.raises(R.ReadinessError):
        R.resolve_live(rs, A.ORDER, {}, {})
