"""T-714: formwork bounds that follow their concrete member's bound (R-T714-1) and the T-638 fix rows restated by line
id (R-T714-2). Villa V714 is hand-made (not the development villa): a beam 4.00 m long scheduled 0.30 wide and drawn
0.25 wide, 0.60 deep under a 0.15 slab; a column scheduled 0.40 x 0.50 and drawn 0.30 x 0.50, 3.00 m clear; a parapet
whose RC height is only floored by a 0.30 upstand on a 10.00 m centreline. The last tests rebuild the development-villa
census from committed files only (no drawing is opened)."""
from __future__ import annotations

import json
import random
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t714"))
import t714_rules as R  # noqa: E402
import t714_alsenan as A  # noqa: E402


# ------------------------------------------------------------------ V714 normal (hand)
def _beam_faces():
    # sides 2 x 4.00 x (0.60 - 0.15) = 3.60 (no width in it); soffit at the drawn width 4.00 x 0.25 = 1.00, at the
    # schedule width x 0.30 / 0.25 = 1.20
    return [R.face("V714-B1.SIDE", "INDEPENDENT", value="3.60"),
            R.face("V714-B1.SOFFIT", "SCALED", value="1.00", ratio=X("0.30") / X("0.25"))]


def test_width_conflict_beam_hand():
    mem = R.member("BOUNDED", low="0.600", high="0.720")          # 4.00 x 0.60 x 0.25 .. x 0.30
    assert R.check_ratio(X("0.30") / X("0.25"), "0.600", "0.720")
    out = R.combine("V714-B1", mem, _beam_faces())
    assert out["cls"] == "BOUNDED" and out["low"] == X("4.600000") and out["high"] == X("4.800000")


def test_section_conflict_column_hand():
    # perimeter 2 x (0.30 + 0.50) = 1.60 drawn, 2 x (0.40 + 0.50) = 1.80 schedule, x 3.00 = 4.80 .. 5.40
    mem = R.member("BOUNDED", low="0.450", high="0.600")          # 0.15 / 0.20 m2 x 3.00
    f = [R.face("V714-C1.SHAFT", "TWO_READINGS", lo=X("1.60") * 3, hi=X("1.80") * 3)]
    out = R.combine("V714-C1", mem, f)
    assert (out["cls"], out["low"], out["high"]) == ("BOUNDED", X("4.800000"), X("5.400000"))


def test_parapet_floor_only_drops_the_high():
    # 2 faces x 0.30 x 10.00 = 6.00 .. all RC 2 x 1.00 x 10.00 = 20.00; the member has a floor only
    mem = R.member("AT_LEAST", low="0.600")                       # 0.30 x 0.20 x 10.00
    f = [R.face("V714-P1", "TWO_READINGS", lo="6.00", hi="20.00")]
    out = R.combine("V714-P1", mem, f)
    assert out["cls"] == "AT_LEAST" and out["low"] == X("6.000000") and out["high"] is None


def test_cap_only_neighbour_face_keeps_floor_and_adds_cap():
    mem = R.member("BOUNDED", low="0.450", high="0.600")
    f = [R.face("V714-C1.SHAFT", "TWO_READINGS", lo="4.80", hi="5.40"),
         R.face("V714-C1.JOINT", "CAP_ONLY", hi="0.25")]
    out = R.combine("V714-C1", mem, f)
    assert (out["low"], out["high"]) == (X("4.800000"), X("5.650000"))


def test_dependent_face_opens_the_high():
    mem = R.member("BOUNDED", low="0.064", high="0.192")          # unlabelled piece, depth 0.40 .. 1.20
    f = [R.face("V714-U.SOFFIT", "INDEPENDENT", value="0.16"), R.face("V714-U.SIDE", "DEPENDENT")]
    out = R.combine("V714-U", mem, f)
    assert out["cls"] == "AT_LEAST" and out["low"] == X("0.160000")


def test_face_order_mirror_does_not_change_the_line():
    mem = R.member("BOUNDED", low="0.600", high="0.720")
    base = R.combine("V714-B1", mem, _beam_faces())
    for seed in range(5):
        fs = _beam_faces()
        random.Random(seed).shuffle(fs)
        out = R.combine("V714-B1", mem, fs)
        assert (out["low"], out["high"]) == (base["low"], base["high"])


def test_ring_soffit_floor_only_hand():
    # skylight ring 0.25 wide, radii 1.50 / 1.75, in-bay plan 2.40 (least of two readings 2.40 / 2.55): soffit >= 2.40,
    # inner / outer faces over an unprinted depth open
    mem = R.member("AT_LEAST", low="0.163")
    out = R.combine("V714-RING", mem, [R.face("V714-RING.F", "FLOOR_ONLY", value=min(X("2.40"), X("2.55")))])
    assert out["cls"] == "AT_LEAST" and out["low"] == X("2.400000") and out["high"] is None
    with pytest.raises(R.Refused):
        R.face("V714-RING.F", "FLOOR_ONLY", value="0")            # a floor is never 0


def test_directed_rounding():
    mem = R.member("BOUNDED", low="0.1", high="0.2")
    out = R.combine("V714-R", mem, [R.face("x", "TWO_READINGS", lo="1.0000004", hi="1.0000006")])
    assert out["low"] == X("1.000000") and out["high"] == X("1.000001")


# ------------------------------------------------------------------ V714 adverse
def test_member_held_blank_gives_blank_never_zero():
    out = R.combine("V714-B2", R.member("BLANK", cause="section not printed"), _beam_faces())
    assert out["cls"] == "BLANK_NAMED" and out["low"] is None and out["high"] is None
    assert "section not printed" in out["why"]


def test_oq10_face_blocks_the_line():
    mem = R.member("RELEASED")
    f = [R.face("V714-GB.SIDE", "BLOCK", cause="OQ-10 formed vs earth-cast")] + _beam_faces()
    out = R.combine("V714-GB", mem, f)
    assert out["cls"] == "BLANK_NAMED" and out["low"] is None and "OQ-10" in out["why"]


def test_zero_floor_is_blank_with_cap_beside_not_a_quantity():
    mem = R.member("RELEASED")
    out = R.combine("V714-J", mem, [R.face("V714-J1", "CAP_ONLY", hi="0.30"), R.face("V714-J2", "CAP_ONLY", hi="0.10")])
    assert out["cls"] == "BLANK_NAMED" and out["low"] is None and out["cap_beside"] == X("0.400000")


def test_no_faces_is_blank():
    out = R.combine("V714-E", R.member("RELEASED"), [])
    assert out["cls"] == "BLANK_NAMED" and out["low"] is None


@pytest.mark.parametrize("kw", [dict(value="-0.12"), dict(value=None), dict(value="4000")])
def test_bad_independent_figure_refused(kw):
    with pytest.raises(R.Refused):
        R.face("bad", "INDEPENDENT", **kw)


def test_scaled_ratio_must_match_member():
    with pytest.raises(R.Refused):
        R.check_ratio(X("1.20"), "0.600", "0.800")                # concrete says 1.333
    with pytest.raises(R.Refused):
        R.face("bad", "SCALED", value="1.00")                      # no ratio


def test_member_guards():
    with pytest.raises(R.Refused):
        R.member("BOUNDED", low="0", high="1")                     # a 0 .. x bound has no floor
    with pytest.raises(R.Refused):
        R.member("AT_LEAST", low="0.5", high="0.6")
    with pytest.raises(R.Refused):
        R.member("AT_LEAST", low="0")
    with pytest.raises(R.Refused):
        R.face("bad", "TWO_READINGS", lo="5.40", hi="4.80")


def test_restate_fix_current_and_stale():
    line = {"element_id": "FW:X", "class": "HELD", "measured_net": None, "held_low": None, "held_high": None}
    assert R.restate_fix("FR-1", "L-1", "FW:X", line)["state"] == "CURRENT"
    assert R.restate_fix("FR-1", "L-1", "FW:Y", line)["state"] == "STALE"
    assert R.restate_fix("FR-1", "L-1", "FW:X", dict(line, held_low=1.0, held_high=2.0))["state"] == "STALE"
    assert R.restate_fix("FR-1", "L-1", "FW:X", None)["state"] == "STALE"


# ------------------------------------------------------------------ development villa (committed inputs only)
@pytest.fixture(scope="module")
def built():
    data = A.load()
    rows, wiring = A.build(data)
    return data, rows, wiring


def test_census_370_by_id_and_matches_committed(built):
    data, rows, wiring = built
    assert len(rows) == 370 and len({r["line_id"] for r in rows}) == 370
    held = {k for k, x in data["index"].items() if x["item_code"] == "STR.FORMWORK" and x["class"] == "HELD"}
    assert {r["line_id"] for r in rows} == held
    doc = json.loads(A.OUT_JSON.read_text(encoding="utf-8"))
    assert doc["lines"] == json.loads(json.dumps(rows, sort_keys=True))
    assert doc["summary"] == A.summarise(rows, wiring)


def test_every_bound_consistent_with_its_member(built):
    _, rows, _ = built
    for r in rows:
        m, c = r["member"]["class"], r["class_after"]
        if c == "BOUNDED":
            assert m in ("RELEASED", "BOUNDED") and X(r["low"]) > 0 and X(r["high"]) >= X(r["low"])
        elif c == "AT_LEAST":
            assert m in ("RELEASED", "BOUNDED", "AT_LEAST") and X(r["low"]) > 0 and r["high"] is None
        elif c == "BLANK_NAMED":
            assert r["low"] is None and r["high"] is None and r["why"]
        if m == "BLANK":
            assert c == "BLANK_NAMED"


def test_counts_and_totals(built):
    _, rows, wiring = built
    s = A.summarise(rows, wiring)
    assert s["by_class"] == {"AT_LEAST": 32, "BLANK_NAMED": 258, "BOUNDED": 26, "FIX_ROW": 54}
    assert (s["bounded_low_m2"], s["bounded_high_m2"], s["at_least_m2"]) == ("87.941284", "103.192739", "98.543697")
    assert s["fix_rows_stale"] == 0 and s["fix_rows_m2"] == "33.127058"


def test_checker_picks_by_hand(built):
    _, rows, _ = built
    by = {r["line_id"]: r for r in rows}
    # BM-GF-055 span 1 (CB2: schedule 0.20, drawn 0.2502): side 2.310933 + soffit 0.867255 x 0.20 / 0.2502 =
    # 0.693249 .. 0.867255 + edge band 0.555045
    b = by["L-3280c42cb578a211045e"]
    lo = X("2.310933") + X("0.867255") * X("0.20") / X("0.2502") + X("0.555045")
    assert X(b["low"]) == R.BR.round_low(lo) and b["high"] == "3.733233"
    # COL-1F-41 C9: shaft 2.20 x 3.45 = 7.59 .. 2.50 x 3.45 = 8.625; joint 0.7763 .. 0.9238
    c = by["L-093b1a8701615f5fed8c"]
    assert (c["low"], c["high"]) == ("8.366300", "9.548800")


def test_adverse_villa_cases(built):
    _, rows, _ = built
    by = {r["line_id"]: r for r in rows}
    # planted column PC-2F: concrete bound rests on a designer RFI over its extent -> the shaft range is not its bound
    pc = [r for r in rows if r["line_id"].startswith("L-fcb1852c")][0]
    assert pc["class_after"] == "BLANK_NAMED" and any(f["dep"] == "DEPENDENT" for f in pc["faces"])
    # every OQ-10 face blocks its line, whatever its member
    for r in rows:
        if any("OQ-10" in f["cause"] for f in r["faces"]):
            assert r["class_after"] == "BLANK_NAMED"
    # a member blank in a merged ledger (T-712 court stretch) keeps its formwork blank
    gb = [r for r in rows if any(x["source"] == "T-712" and x["class"] == "BLANK" for x in r["member"]["lines"])]
    assert gb and all(r["class_after"] == "BLANK_NAMED" for r in gb)


def test_east_ring_follows_t721_floor(built):
    _, rows, _ = built
    r = [x for x in rows if x["line_id"].startswith("L-e86ee698")][0]
    assert r["class_after"] == "AT_LEAST" and r["low"] == "1.799300"          # T-721 least plan reading 1.7993 m2


def test_wiring_form_rows_current(built):
    _, _, wiring = built
    assert len(wiring) == 54 and {w["fix"] for w in wiring} == {f"FR-T638-{i}" for i in range(1, 55)}
    assert all(w["state"] == "CURRENT" for w in wiring)
