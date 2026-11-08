"""T-640: finishes hold census (R-T640-1). Synthetic room "F640" (not the training villa) by hand with adverse cases
(mirror, opening order, missing size, paint on a tiled face, a HELD line set to 0); then the development villa: the 72
HELD-blank B4 / B5 m2 lines of the T-630 dry run classed, with fix rows (repository files only)."""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t640"))
import t640_rules as R  # noqa: E402
import t640_alsenan as A  # noqa: E402

D = Decimal

# ---- room "F640" (hand) ---------------------------------------------------------------------------------------------
# Room 4.00 x 3.00: faces N 4.00, E 3.00, S 4.00, W 3.00; structural soffit 3.20 above the finished floor (plaster to
# the slab underside, Q-72), finished ceiling 2.90 (paint height); wall 0.20 thick. Window W1 on N 1.20 x 1.20, sill
# 1.00, frame in the middle of the wall: reveal depth 0.10 each side. Door D1 on S 0.90 x 2.20. E is tiled to 1.50 (no
# opening on E).
#   plaster: 4 x 3.20 + 3 x (3.20 - 1.50) + 4 x 3.20 + 3 x 3.20 = 12.80 + 5.10 + 12.80 + 9.60 = 40.30
#            - W1 1.20 x 1.20 (1.44) - D1 0.90 x 2.20 (1.98) = 36.88 m2
#   paint:   4 x 2.90 + 3 x (2.90 - 1.50) + 4 x 2.90 + 3 x 2.90 = 11.60 + 4.20 + 11.60 + 8.70 = 36.10 - 3.42 = 32.68 m2
#   tile:    3.00 x 1.50 = 4.50 m2
#   W1 IN jambs + head 2 x 0.10 x 1.20 + 0.10 x 1.20 = 0.36, sill 0.10 x 1.20 = 0.12; OUT the same
#   D1 through the wall 2 x 0.20 x 2.20 + 0.20 x 0.90 = 1.06 m2
FACES = {"N": "4.00", "E": "3.00", "S": "4.00", "W": "3.00"}
OPEN = [{"id": "W1", "face": "N", "kind": "window", "w": "1.20", "h": "1.20", "sill": "1.00", "d_in": "0.10",
         "d_out": "0.10"},
        {"id": "D1", "face": "S", "kind": "door", "w": "0.90", "h": "2.20"}]
TILED = {"E": "1.50"}


def run(faces=FACES, opens=OPEN, tiled=TILED):
    return R.room_finishes(faces, "3.20", "2.90", opens, tiled=tiled, wall_t="0.20")


def test_f640_by_hand():
    r = run()
    assert r["plaster"] == D("36.88")
    assert r["paint"] == D("32.68")
    assert r["tile"] == D("4.50")
    assert r["reveals"]["W1"]["IN"] == {"jambs_head": D("0.36"), "sill": D("0.12")}
    assert r["reveals"]["W1"]["OUT"] == {"jambs_head": D("0.36"), "sill": D("0.12")}
    assert r["reveals"]["D1"]["THROUGH"] == D("1.06")


def test_f640_mirror_and_order_invariant():
    mirror = {"S": "4.00", "W": "3.00", "N": "4.00", "E": "3.00"}
    opens = [dict(OPEN[1], face="N"), dict(OPEN[0], face="S")]
    a, b = run(), run(mirror, opens)
    assert (a["plaster"], a["paint"], a["tile"]) == (b["plaster"], b["paint"], b["tile"])


def test_f640_opening_in_tiled_band_cut_once_per_finish():
    # a door 0.90 x 2.20 on the tiled E face: tile loses 0.90 x 1.50, plaster / paint lose 0.90 x (2.20 - 1.50)
    opens = OPEN + [{"id": "D2", "face": "E", "kind": "door", "w": "0.90", "h": "2.20"}]
    r, base = run(opens=opens), run()
    assert base["tile"] - r["tile"] == D("1.35")
    assert base["plaster"] - r["plaster"] == D("0.63")
    assert base["paint"] - r["paint"] == D("0.63")


def test_f640_missing_data_never_zero():
    with pytest.raises(R.RuleError, match="depth missing"):
        run(opens=[dict(OPEN[0], d_in=None)])
    with pytest.raises(R.RuleError, match="size missing"):
        run(opens=[dict(OPEN[0], h=None)])
    with pytest.raises(R.RuleError, match="above the structural soffit"):
        R.room_finishes(FACES, "2.80", "2.90", [])


def test_paint_on_tiled_face_refused():
    with pytest.raises(R.RuleError, match="paint on the tiled face"):
        R.paint_on_face("E", TILED, "1.0")
    assert R.paint_on_face("N", TILED, "1.0") == D("1.0")


BLANK = {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None}


def entry(**kw):
    e = {"line_id": "L-x", "item_code": "FIN.PAINT", "class": "A_BOUND", "cause": "c", "sources": ["s"],
         "fix": {"kind": "SET", "before": dict(BLANK), "basis": "b",
                 "after": {"class": "HELD", "measured_net": None, "held_low": "0", "held_high": "1.2"}}}
    e.update(kw)
    return e


def test_census_adverse():
    R.check_entry(entry())
    with pytest.raises(R.RuleError, match="0 .. 0"):
        R.check_entry(entry(fix={"kind": "SET", "before": dict(BLANK), "basis": "b",
                                 "after": {"class": "HELD", "measured_net": None, "held_low": "0", "held_high": "0"}}))
    with pytest.raises(R.RuleError, match="released as 0"):
        R.check_entry(entry(fix={"kind": "SET", "before": dict(BLANK), "basis": "b", "companion": "x",
                                 "after": {"class": "RELEASED", "measured_net": "0"}}))
    with pytest.raises(R.RuleError, match="companion"):
        R.check_entry(entry(fix={"kind": "SET", "before": dict(BLANK), "basis": "b",
                                 "after": {"class": "RELEASED", "measured_net": "2.0"}}))
    with pytest.raises(R.RuleError, match="HELD with a value"):
        R.check_entry(entry(fix={"kind": "SET", "before": dict(BLANK), "basis": "b",
                                 "after": {"class": "HELD", "measured_net": "1", "held_low": "0", "held_high": "1"}}))
    with pytest.raises(R.RuleError, match="named cause"):
        R.check_entry(entry(cause=" "))
    with pytest.raises(R.RuleError, match="carrier"):
        R.check_entry(entry(**{"class": "A_CARRIED", "fix": None}))
    with pytest.raises(R.RuleError, match="needs a fix row"):
        R.check_entry(entry(fix=None))
    with pytest.raises(R.RuleError, match="carries no quantity"):
        R.check_entry(entry(**{"class": "B_HELD"}))


# ---- development villa ----------------------------------------------------------------------------------------------

@pytest.mark.skipif(os.environ.get("URBAN_T640_WRITE") != "1", reason="writer only on request")
def test_write_outputs():
    A.write_outputs()


def test_build_reproduces_committed_output():
    assert A.dumps(A.build()) == A.OUT_JSON.read_text(encoding="utf-8")
    assert A.render_md(A.build()) == A.OUT_MD.read_text(encoding="utf-8")


def test_alsenan_census():
    b = A.build()
    c = b["counts"]
    assert c["lines"] == 72
    assert c["by_class"] == {"A_BOUND": 33, "A_CARRIED": 8, "B_HELD": 24, "C_DRAWING": 0, "C_PENDING": 7}
    assert c["fix_rows"] == 35
    ids = [e["line_id"] for e in b["lines"]]
    assert len(set(ids)) == 72
    for e in b["lines"]:
        fx = e.get("fix")
        if fx and fx["kind"] == "SET":
            assert fx["after"]["class"] == "HELD" and D(fx["after"]["held_high"]) > 0
    fr = {e["element_id"]: e["fix"]["after"] for e in b["lines"] if e.get("fix") and e["fix"]["kind"] == "SET"}
    assert fr["HL:WALL_FINISH:ST_2F:PLASTER"] == {"class": "HELD", "measured_net": None, "held_low": "44.512",
                                                  "held_high": "49.872"}
    assert fr["HL:WALL_FINISH:ST_2F:PAINT"]["held_low"] == "42.722"
    assert fr["HL:WALL_FINISH:ST_2F:PAINT"]["held_high"] == "47.932"
    paint = [e for e in b["lines"] if e["item_code"] == "FIN.PAINT" and e.get("fix")]
    assert len(paint) == 28   # 27 return faces (26 valued + OP-009) + ST_2F
    assert sum(D(e["fix"]["after"]["held_high"]) for e in paint if "ST_2F" not in e["element_id"]) == D("24.27")
    assert b["fix_bound_total_m2"] == ["87.234", "138.53962"]
