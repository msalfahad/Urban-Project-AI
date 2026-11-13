"""T-684 turn-square element (R-T684-1 .. -3): synthetic villa V684 by hand (normal + adverse) and the development
villa pinned to the committed output.

Villa V684 (synthetic, not the development villa), by hand. Dog-leg in one shaft, storeys 3.60 m (printed), riser
0.180 m measured on the section -> 20 risers per storey.
  Lower storey: flights 8 + 8 risers -> budget (3.60 - 16 x 0.18) / 0.18 = 4.000 -> 4 turn risers; the section draws 4
    risers in the turn zone; 3 radiating lines from the inner corner (far ends (-0.40, 1.10), (-1.10, 1.10),
    (-1.10, 0.40)) on the hidden layer (above the cut) -> WINDERS, DRAWN.
  Upper storey: flights 10 + 9 -> budget (3.60 - 19 x 0.18) / 0.18 = 1.000 -> 1 (a closing riser); the section draws
    1; the plan draws the SAME three lines at the same corner on the visible layer, the zone open down to the lower
    turn -> LANDING_SPLIT, DRAWN, lines SEEN_BELOW (the winders are counted once, on the lower storey).
Adverse: the same lines on an annotation layer (ignored, never winders); hidden-layer lines with no readable section
(UNDETERMINED, held: hidden alone proves nothing); coinciding lines with a floor drawn between (not seen below ->
CONFLICT on a landing); genuine upper winders (budget 4, section 4, own lines) -> WINDERS; coinciding lines while the
upper budget asks for 4 risers -> UNDETERMINED; missing storey height / non-whole budget / section disagreeing ->
UNDETERMINED with no riser count (never 0, never a default landing); mirror and rotation -> the same decision; mm read
as m and an unknown unit refused; an unknown layer role refused.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t684"
sys.path.insert(0, str(HERE))
import t684_rules as R  # noqa: E402

_spec = importlib.util.spec_from_file_location("t684_alsenan", HERE / "t684_alsenan.py")
A = importlib.util.module_from_spec(_spec)
sys.modules["t684_alsenan"] = A
_spec.loader.exec_module(A)

OUT = HERE / "out" / "T684_MS2_TURN.json"
ENDS = [(-0.40, 1.10), (-1.10, 1.10), (-1.10, 0.40)]


def lines(role, ends=ENDS, f=lambda x, y: (x, y)):
    return [R.Seg(*f(0.0, 0.0), *f(x, y), role) for x, y in ends]


def lower(**kw):
    d = dict(storey="L", height_m=3.60, flight_risers=[8, 8], riser_m=0.18, segs=lines("HIDDEN"),
             section_turn_risers=4)
    d.update(kw)
    return R.StoreyTurn(**d)


def upper(**kw):
    d = dict(storey="U", height_m=3.60, flight_risers=[10, 9], riser_m=0.18, segs=lines("VISIBLE"),
             section_turn_risers=1, lower_turn_segs=lines("HIDDEN"), open_below=True)
    d.update(kw)
    return R.StoreyTurn(**d)


# ---------------------------------------------------------------- normal
def test_lower_storey_winders_drawn():
    r = R.classify(lower())
    assert (r["element"], r["status"], r["turn_risers"], r["lines_are"]) == ("WINDERS", "DRAWN", 4, "WINDERS")


def test_budget_hand_values():
    assert R.budget(lower())[0] == 4
    assert R.budget(upper())[0] == 1
    assert R.budget(upper(flight_risers=[10, 10]))[0] == 0


def test_upper_storey_lines_are_the_lower_turn_seen_below():
    r = R.classify(upper())
    assert (r["element"], r["status"], r["turn_risers"], r["lines_are"]) == ("LANDING_SPLIT", "DRAWN", 1, "SEEN_BELOW")


def test_flat_landing_with_no_riser_and_no_lines():
    r = R.classify(upper(flight_risers=[10, 10], section_turn_risers=0, segs=[], lower_turn_segs=None,
                         open_below=None))
    assert (r["element"], r["status"], r["turn_risers"], r["lines_are"]) == ("LANDING", "DRAWN", 0, None)


def test_genuine_upper_winders():
    own = [(-0.30, 1.10), (-1.10, 1.10), (-1.10, 0.30)]
    r = R.classify(upper(flight_risers=[8, 8], section_turn_risers=4, segs=lines("VISIBLE", own)))
    assert (r["element"], r["status"], r["turn_risers"]) == ("WINDERS", "DRAWN", 4)


# ---------------------------------------------------------------- adverse
def test_annotation_layer_lines_are_never_winders():
    r = R.classify(upper(segs=lines("ANNOTATION"), lower_turn_segs=None, open_below=None))
    assert (r["element"], r["status"], r["lines_are"]) == ("LANDING_SPLIT", "DRAWN", None)
    r = R.classify(lower(segs=lines("DIMENSION")))
    assert r["element"] == "UNDETERMINED" and r["status"] == "HELD"     # budget asks 4 but nothing drawn: held


def test_hidden_lines_without_a_readable_section_stay_held():
    r = R.classify(lower(section_turn_risers=None))
    assert (r["element"], r["status"], r["turn_risers"]) == ("UNDETERMINED", "HELD", 4)


def test_coinciding_lines_with_a_floor_between_are_a_conflict():
    r = R.classify(upper(open_below=False))
    assert (r["element"], r["status"], r["lines_are"]) == ("LANDING_SPLIT", "CONFLICT", "UNRESOLVED")


def test_coinciding_lines_while_the_budget_asks_winders_stay_held():
    r = R.classify(upper(flight_risers=[8, 8], section_turn_risers=4))
    assert (r["element"], r["status"], r["lines_are"]) == ("UNDETERMINED", "HELD", "SEEN_BELOW")


def test_one_line_off_by_more_than_10_mm_is_not_seen_below():
    off = [(-0.40, 1.10), (-1.10, 1.10), (-1.10, 0.415)]
    r = R.classify(upper(segs=lines("VISIBLE", off)))
    assert r["status"] == "CONFLICT" and r["lines_are"] == "UNRESOLVED"


@pytest.mark.parametrize("kw", [dict(height_m=None), dict(riser_m=None), dict(flight_risers=[10, None]),
                                dict(flight_risers=[])])
def test_missing_datum_is_held_never_zero(kw):
    r = R.classify(upper(**kw))
    assert r["element"] == "UNDETERMINED" and r["status"] == "HELD" and r["turn_risers"] is None


def test_non_whole_budget_and_section_disagreement_held():
    r = R.classify(upper(riser_m=0.175))                    # (3.60 - 19 x 0.175) / 0.175 = 1.571: not whole
    assert r["element"] == "UNDETERMINED" and r["turn_risers"] is None
    r = R.classify(upper(section_turn_risers=3))
    assert (r["element"], r["status"], r["turn_risers"]) == ("UNDETERMINED", "HELD", 1)


@pytest.mark.parametrize("f", [lambda x, y: (-x, y), lambda x, y: (-y, x), lambda x, y: (y, -x),
                               lambda x, y: (-x, -y)])
def test_mirror_and_rotation_keep_the_decision(f):
    u = upper(segs=lines("VISIBLE", f=f), lower_turn_segs=lines("HIDDEN", f=f))
    lo = lower(segs=lines("HIDDEN", f=f))
    assert R.classify(u)["lines_are"] == "SEEN_BELOW" and R.classify(u)["element"] == "LANDING_SPLIT"
    assert R.classify(lo)["element"] == "WINDERS"


def test_units_and_roles():
    assert R.to_m(1150, "mm") == pytest.approx(1.15)
    assert R.to_m(115, "cm") == pytest.approx(1.15)
    assert R.to_m(None, "mm") is None
    with pytest.raises(ValueError):
        R.to_m(1.15, "ft")
    with pytest.raises(ValueError):
        R.classify(upper(segs=[R.Seg(0, 0, -1.1, 1.1, "LAYER5")]))
    with pytest.raises(ValueError):
        R.budget(upper(height_m=-3.6))
    # millimetres taken as metres break the budget instead of passing silently
    r = R.classify(upper(height_m=3600))
    assert r["element"] == "UNDETERMINED" or r["turn_risers"] != 1


# ---------------------------------------------------------------- development villa (pinned)
def test_development_villa_pinned_and_unchanged_lines():
    res = A.build()
    assert json.loads(OUT.read_text()) == json.loads(json.dumps(res, sort_keys=True))
    gf, f1 = res["element"]["gf_turn"], res["element"]["f1_turn"]
    assert (gf["element"], gf["turn_risers"]) == ("WINDERS", 5)
    assert (f1["element"], f1["status"], f1["turn_risers"], f1["lines_are"]) == ("LANDING_SPLIT", "DRAWN", 1,
                                                                                  "SEEN_BELOW")
    assert all(r["change"] == "NONE" for r in res["lines"]) and res["released_change_m3"] == 0
    conc = {r["line_id"]: r["before"]["net"] for r in res["lines"] if r["item_code"] == "STR.CONC.STAIR"}
    assert conc["L-67e4b0485135f84acc46"] == 1.033445 and conc["L-2416e65f053a14199cfc"] == 0.4696
    assert conc["L-bb0e57b1948175a3d5b8"] == 1.001373 and conc["L-659243ed9fc2831c3ae8"] is None   # MS2-TR held
    nos = [p for p in res["proposals"] if p["item"] == "B7-05 nosing MS2-TR"][0]
    assert nos["delta"] == 1.150 and nos["unit"] == "lm"


def test_output_carries_no_absolute_coordinate():
    import re
    txt = OUT.read_text()
    # relative readings only: every number in the output is a level, a count, a length or a quantity well under 100
    nums = [float(x) for x in re.findall(r"(?<![\w.-])-?\d+\.\d+", txt)]
    assert nums and max(abs(n) for n in nums) < 100.0
    for seg_list in (A.GF_TURN, A.F1_LINES):
        assert all(max(abs(s.x1), abs(s.y1), abs(s.x2), abs(s.y2)) < 2.0 for s in seg_list)
