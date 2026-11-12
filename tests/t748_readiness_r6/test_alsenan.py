"""T-748 on the development villa (repository files only, sha-pinned; no drawing, no Drive): the committed readiness
map and scorecard equal a rebuild; stale 0 and double count 0 across hubs on V3.0.75; the merged packages' rows are
wired; the issued roof-membrane record is shown beside and never applied silently; the scorecard moves exactly the
T-729 trade x unit cells against the merged T-739 statement; HELD never summed or 0."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t748"))
import t748_alsenan as A  # noqa: E402
import t748_rules as R  # noqa: E402
import t748_scorecard as S  # noqa: E402


@pytest.fixture(scope="module")
def ready():
    return A.build()


@pytest.fixture(scope="module")
def card():
    return S.build()


def test_committed_outputs_equal_rebuild(ready, card):
    assert A.JSON_OUT.read_text(encoding="utf-8") == A.dumps(ready)
    assert A.CSV_OUT.read_text(encoding="utf-8") == A.to_csv(ready["row_list"])
    assert S.JSON_OUT.read_text(encoding="utf-8") == S.dumps(card)
    assert S.MD_OUT.read_text(encoding="utf-8") == S.render_md(card)


def test_stale_zero_and_every_t730_row_restated(ready):
    assert ready["stale"] == 0 and ready["rows_t730_restated"] == 1174
    assert ready["one_hub_per_target"]["double_count_across_hubs"] == 0
    assert ready["findings"]["unwired_after_merge"] == []


def test_merged_packages_wired(ready):
    p = ready["packages"]
    assert p["T-717 (MERGED V3.0.74)"]["moving_live_rows"] == 0
    assert p["T-729 (MERGED V3.0.75)"]["moving_live_rows"] == 0
    assert p["T-717 (MERGED V3.0.74)"]["by_action"]["WIRED_ADDED"] == 32
    assert p["T-729 (MERGED V3.0.75)"]["by_action"]["WIRED_ADDED"] == 4


def test_blockers_cleared_by_merges(ready):
    p = ready["packages"]
    assert p["T-509"]["open_blockers"] == {}                       # T-708 merged
    assert p["T-738"]["open_blockers"] == {"RULING ORR-007": 27}    # T-733 / T-493 merged, the ruling stays


def test_host_changed_rows_are_t717_plaster_hosts(ready):
    hc = ready["findings"]["host_changed"]
    assert len(hc) == 11 and all(x.endswith("by T-717") for x in hc)
    assert {x.split()[1] for x in hc} == {"L-b152995525ed123ddac9", "L-1ddc23d5657b4c4e4d0d"}


def test_downgrade_record_beside_not_applied(ready, card):
    assert "DG-98cbadebaecc5ede:L-636fd3ff1784a12e653b" in ready["findings"]["F-T748-1"]
    assert ready["findings"]["F-T748-2"][0].startswith("DG-a429c160: cited on the board, no record")
    b = card["board_downgrades_beside"][0]
    assert b["status"] == "VALID_NOT_APPLIED_IN_INDEX" and b["lines"][0]["index_state"] == "RELEASED"
    wp = next(t for t in card["trades"] if (t["trade"], t["unit"]) == ("B8 Waterproofing", "m2"))
    assert Decimal(wp["released"]) - Decimal("115.832") == Decimal("595.518096")


def test_paint_rows_released_unchanged_and_returns_pending(ready):
    rows = [r for r in ready["row_list"] if r["source"] == "T-740"]
    assert len(rows) == 105
    assert sum(r["action"] == "PENDING" for r in rows) == 30
    assert [r["target"] for r in rows if r["action"] == "KEEP_RELEASED"] == ["L-7f083d3e2c2702d14356"]
    assert ready["findings"]["released_changes"] == []


def test_scorecard_moves_only_t729_cells(card):
    d = card["delta_vs_t739_v3_0_74"]
    assert {(r["trade"], r["unit"]) for r in d["changed"]} == {("B10 Concrete", "m2"), ("B10 Concrete", "m3"),
                                                                ("B7 Stairs", "m2")}
    fw = next(r for r in d["changed"] if r["unit"] == "m2" and r["trade"] == "B10 Concrete")
    assert fw["released"] == ["1027.977403", "1061.104461", "33.127058"]
    ch = card["chain_readd_v3_0_74_to_v3_0_75"]
    assert (ch["package_rows"], ch["replaced"], ch["added"], ch["other_lines_byte_equal"]) == (396, 392, 4, 4763)


def test_held_never_summed_and_census_agrees(card):
    assert all(x["agree"] for x in card["census_crosscheck_t729"])
    for t in card["trades"]:
        held = sum(t["counts"][s] for s in ("BOUNDED", "AT_LEAST", "AT_MOST", "BLANK"))
        assert (held == 0) == (not t["statement"].startswith("NO SINGLE TOTAL"))


def test_adverse_tampered_pin_refused(monkeypatch):
    monkeypatch.setitem(A.PIN, "t740", (A.PIN["t740"][0], "0" * 64))
    with pytest.raises(R.ReadinessError, match="pinned"):
        A.build()
