"""T-512 (b): an all-blank item code prints HELD (n blank lines), never 0.0 (F-C-T508-1, class F-C-T458-2; AGENT_BRIEF
'HELD is never 0'; R-T499-1). Synthetic hand fixture (not the development villa): four item codes of a made-up wall
finish, lines built as the candidate methods build them (evidence_state / measured_net / bounded_range), totalled by
the candidate method's own arch_v304.code_totals and read through research/agents_t512 held_view.

    X.MIXED   3.0 + 4.5 valued, 1 blank      -> code_totals 7.5;  view PARTIAL 'AT_LEAST 7.5 + HELD (1 lines ...)'
    X.BLANK   3 blank lines                  -> code_totals 0.0 (the defect); view HELD 'HELD (3 blank lines)'
    X.ZERO    one valued line of 0.0         -> 0.0 is a measured quantity: ALL_VALUED, no defect
    X.BOUND   2 bounded 1.0..2.0 + 0.5..0.75 -> code_totals 0.0 released (the defect); view HELD range 1.5..2.75
    X.BOUNDBL 1 bounded + 1 blank            -> HELD (1 blank line, 1 bounded), no range (one held line unbounded)
    X.EXCL    one excluded line              -> no code_totals key (unchanged)
Mirror / unit adverse: the same lines in another order and in mm-scaled values give the same statuses.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t512"))
sys.path.insert(0, str(ROOT / "research" / "agents_t469"))

from engine.source import arch_v304 as A304  # noqa: E402
import t512_held_totals as H  # noqa: E402
import t469_trade_scoreboard as T469  # noqa: E402


def ln(code, ev="MEASURED", net=None, br=None, unit="m2"):
    return {"item_code": code, "unit": unit, "evidence_state": ev, "measured_net": net,
            "bounded_range": None if br is None else {"low": br[0], "high": br[1]}}


def blank(code):
    return ln(code, "BLOCKED_RFI")


LINES = [ln("X.MIXED", net=3.0), ln("X.MIXED", net=4.5), blank("X.MIXED"),
         blank("X.BLANK"), blank("X.BLANK"), blank("X.BLANK"),
         ln("X.ZERO", net=0.0),
         ln("X.BOUND", "BOUNDED_EXPOSURE", br=(1.0, 2.0)), ln("X.BOUND", "BOUNDED_EXPOSURE", br=(0.5, 0.75)),
         ln("X.BOUNDBL", "BOUNDED_EXPOSURE", br=(1.0, 2.0)), blank("X.BOUNDBL"),
         ln("X.EXCL", "EXCLUDED_WITH_REASON")]


@pytest.fixture(scope="module")
def tot():
    return A304.code_totals(LINES)


def test_candidate_totals_unchanged_and_defect_reproduced(tot):
    assert "X.EXCL|m2" not in tot
    assert tot["X.MIXED|m2"]["released"] == 7.5
    assert tot["X.BLANK|m2"] == {"lines": 3, "released": 0.0, "held_low": 0.0, "held_high": 0.0,
                                 "bounded_lines": 0, "blocked_lines": 3}          # the printed 0.0 (F-C-T508-1)
    assert H.check(tot) == ["X.BLANK|m2", "X.BOUNDBL|m2", "X.BOUND|m2"]   # sorted keys


def test_normal_mixed_prints_number_with_held_beside(tot):
    v = H.view(tot["X.MIXED|m2"])
    assert v["status"] == H.PARTIAL and v["released"] == 7.5 and v["blank_lines"] == 1
    assert v["text"] == "AT_LEAST 7.5 + HELD (1 lines: 0 bounded, 1 blank)"
    assert not H.zero_printed(tot["X.MIXED|m2"])


def test_adverse_all_blank_prints_held_never_zero(tot):
    v = H.view(tot["X.BLANK|m2"])
    assert v["status"] == H.HELD and v["released"] is None and v["held_range"] is None
    assert v["text"] == "HELD (3 blank lines)"
    assert "0.0" not in v["text"]


def test_measured_zero_is_a_quantity(tot):
    v = H.view(tot["X.ZERO|m2"])
    assert v["status"] == H.ALL_VALUED and v["released"] == 0.0 and not H.zero_printed(tot["X.ZERO|m2"])


def test_bounded_only_and_bounded_plus_blank(tot):
    b = H.view(tot["X.BOUND|m2"])
    assert b["status"] == H.HELD_BOUNDED and b["released"] is None and b["held_range"] == [1.5, 2.75]
    bb = H.view(tot["X.BOUNDBL|m2"])
    assert bb["status"] == H.HELD and bb["released"] is None and bb["held_range"] is None
    assert bb["text"] == "HELD (1 blank lines, 1 bounded)"


def test_order_and_scale_do_not_change_the_status():
    rev = A304.code_totals(list(reversed(LINES)))
    assert {k: H.view(v)["status"] for k, v in rev.items()} == \
        {k: H.view(v)["status"] for k, v in A304.code_totals(LINES).items()}
    mm = [dict(x, measured_net=None if x["measured_net"] is None else x["measured_net"] * 1e6, unit="mm2")
          for x in LINES]
    t = A304.code_totals(mm)
    assert H.view(t["X.MIXED|mm2"])["released"] == 7.5e6 and H.view(t["X.BLANK|mm2"])["status"] == H.HELD


def test_scoreboard_schema_reads_alike():
    held = {"item_code": "X.BLANK", "unit": "m2", "released_qty": 0.0, "released_lines": 0, "held_lines": 3,
            "held_low": 0.0, "held_high": 0.0, "held_unknown_lines": 3, "excluded_lines": 0,
            "verified_whole_lines": 0}
    assert H.zero_printed(held) and H.view(held)["text"] == "HELD (3 blank lines)"
    mixed = dict(held, released_qty=7.5, released_lines=2, held_lines=1, held_unknown_lines=1)
    assert not H.zero_printed(mixed) and H.view(mixed)["status"] == H.PARTIAL


def test_inconsistent_counts_refused():
    with pytest.raises(ValueError):
        H.view({"lines": 2, "released": 0.0, "held_low": 0.0, "held_high": 0.0, "bounded_lines": 2,
                "blocked_lines": 1})


def test_t469_keyed_cell_prints_none_not_zero():
    row = {"key": "K1", "reference_qty": "10", "reference_unit": "m2", "released_qty": 0.0, "released_lines": 0,
           "held_lines": 2, "held_unknown_lines": 2, "held_low": 0.0, "held_high": 0.0,
           "outcome": "RANGE_OPEN", "variance_low_pct": -100.0}
    md = T469.markdown({"sides": [], "keyed": [{"label": "S", "rows": [row]}]})
    assert "released none (0 lines) + 2 UNKNOWN" in md and "released 0.000" not in md
    ok = dict(row, released_qty=4.0, released_lines=1, held_lines=0, held_unknown_lines=0, outcome="ALL_RELEASED",
              variance_pct=-60.0)
    assert "released 4.000 on 1 = -60.00 %" in T469.markdown({"sides": [], "keyed": [{"label": "S", "rows": [ok]}]})


def test_committed_census_names_the_candidate_path():
    """the committed candidate line index (V3.0.55) + the V3.0.56 moved codes: the stair skirting codes are all blank
    and the candidate method prints 0.0 for them; the view prints HELD (22 blank lines). Quantities unchanged."""
    rows = {r["code"]: r for r in H.census_index(H.INDEX, H.MOVED_V3056)}
    for c in ("FIN.STAIR.SKIRTING.ZIGZAG|lm", "FIN.STAIR.SKIRTING.SLOPED|lm"):
        assert rows[c]["defect"] and rows[c]["status"] == H.HELD and rows[c]["blank_lines"] == 22
        assert rows[c]["printed_total"] == 0.0
    assert rows["FIN.SKIRTING|lm"]["printed_total"] == pytest.approx(209.428592)
    assert not rows["FIN.SKIRTING|lm"]["defect"]


def test_committed_t469_markdown_has_no_zero_release():
    md = (ROOT / "research/agents_t469/out/T469_SCOREBOARD_V3_0_41.md").read_text(encoding="utf-8")
    assert "released 0.000 on 0" not in md
    doc = json.loads((ROOT / "research/agents_t469/out/T469_SCOREBOARD_V3_0_41.json").read_text(encoding="utf-8"))
    assert T469.markdown(doc) == md
