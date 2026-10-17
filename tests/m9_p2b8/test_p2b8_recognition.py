"""Phase 2B-8 acceptance: the V2.7 recognition weaknesses closed (or bounded) by ARCH_TAKEOFF_V2.7.1.

1. Water-closet shapes (UP-WET-002): a WC drawn as linework is a bowl touching a cistern that stands against a wall.
   V2.7.1 requires the cistern on a wall face (within 0.10 m), a bowl no wider than a WC pan (0.32 - 0.42 m), and
   accepts a round bowl (a circle of that diameter) centred on the cistern (within 0.05 m). A weak resemblance - a
   seat wider than a pan, a free-standing chair, a round table, an off-centre circle - stays REVIEW.
2. A basin block's own linework is the basin, never a second piece of evidence: the fixture's insert is matched to
   the insert path of every entity drawn inside it (V2.7 compared ids of two different forms, L-P7-03).
3. A column turned off the drawing axes is a jamb and a wall interruption like an axis-aligned one: a plan turned 30
   degrees measures as the unturned plan (V2.7: the turned column was a room-boundary polygon only).
4. Every measured line names its drawn entities, or the reason it has none.

Plans: p2b8_fixtures.wc_plan (the W.C. + lobby of tests/m9_p2b7), door_plan COLUMN_JAMB (tests/m9_p2b7: a hatched
full-thickness column is the far jamb of the gap, door 0.877 m between the masonry jamb and the column face) and
column_in_wall (a 0.30 m column across the north wall of the 4.00 x 3.00 m bathroom: wall run 14.00 - 0.80 door -
0.60 window - 0.30 column = 12.30 m)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

ezdxf = pytest.importorskip("ezdxf")

import p2b8_fixtures as F                                     # noqa: E402
import p2b8_run as R                                          # noqa: E402


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b8_recognition")


_cache = {}


def _wc(work, kind, method=R.V271, transform=None):
    key = ("wc", kind, method, transform)
    if key not in _cache:
        src = F.wc_plan(work / f"WC_{kind}.dxf", kind)
        if transform:
            src = F.variant(src, work / f"WC_{kind}_{transform}.dxf", transform)
        _cache[key] = R.run(src, work / f"o_{kind}_{method[-5:].replace('.', '')}_{transform or 'b'}",
                            roles=F.ROLES, facts=True, method=method)
    return _cache[key]


def _lobby_type(out):
    lob = R.lobby(out)
    if lob["codes"] == ["BATHROOM"] and lob["kind"] == "WET":
        return "WET"
    assert lob["class"] == "UNLABELLED" and not lob["codes"], lob
    return "REVIEW"


# what each drawing is (hand truth from the coordinates; p2b8_fixtures / tests/m9_p2b7 docstrings)
WC_TRUTH = {
    "EXPLODED": "WET", "EXPLODED_FURN": "WET", "ANON_BLOCK": "WET", "ARABIC": "WET", "ROUND_BOWL": "WET",
    "BASIN": "REVIEW", "ALONE": "REVIEW", "OVAL_TABLE": "REVIEW", "BASIN_COUNTER": "REVIEW", "BASIN_FITTINGS": "REVIEW",
    "BIDET": "REVIEW", "CHAIR": "REVIEW", "DETACHED": "REVIEW", "SEAT_LOOKALIKE": "REVIEW",
    "ARMCHAIR_AT_WALL": "REVIEW", "ROUND_TABLE_SHELF": "REVIEW", "OFFSET_ROUND": "REVIEW",
    "BASIN_OWN_WC_LIKE": "REVIEW"}
# what ARCH_TAKEOFF_V2.7 did (as found, Phase 2B-8): the errors V2.7.1 corrects
V27_AS_FOUND = {"ROUND_BOWL": "REVIEW", "SEAT_LOOKALIKE": "WET", "ARMCHAIR_AT_WALL": "WET",
                "BASIN_OWN_WC_LIKE": "WET"}


@pytest.mark.parametrize("kind", sorted(WC_TRUTH))
def test_wc_evidence_to_truth(work, kind):
    assert _lobby_type(_wc(work, kind)) == WC_TRUTH[kind]


@pytest.mark.parametrize("kind", sorted(V27_AS_FOUND))
def test_v2_7_as_found(work, kind):
    """V2.7 is unchanged (frozen behaviour): its four recognition errors on these drawings stay as found."""
    assert _lobby_type(_wc(work, kind, R.V27)) == V27_AS_FOUND[kind]


def test_round_bowl_is_corroboration_like_an_elliptical_one(work):
    """the round bowl (circle d 0.40) centred on the 0.50 x 0.20 cistern standing on the wall face: the lobby is a
    bathroom from two independent pieces of evidence (the basin block and the WC linework), flagged for review."""
    out = _wc(work, "ROUND_BOWL")
    lob = R.lobby(out)
    assert lob["label_source"] == "FIXTURES+WC_SHAPE"
    wc = [c for c in R.corrections(out) if c["correction"] == "WET_EVIDENCE"][0]["detail"]["wc_shapes"][0]
    assert wc["bowl_shape"] == "ROUND" and wc["bowl_m"] == [0.4, 0.4] and wc["against_wall"] is True


def test_weak_resemblances_name_their_failing_test(work):
    """each rejected candidate says why: the seat is wider than a WC pan; the back of a free-standing chair is on no
    wall; the round table is too large; the circle is off the cistern's centre line."""
    why = {}
    for kind in ("SEAT_LOOKALIKE", "ARMCHAIR_AT_WALL", "ROUND_TABLE_SHELF", "OFFSET_ROUND"):
        rec = [c for c in R.corrections(_wc(work, kind)) if c["correction"] == "WET_EVIDENCE"][0]["detail"]
        why[kind] = {r["reason"] for r in rec.get("wc_rejected") or ()}
    assert "BOWL_WIDER_THAN_A_WC_PAN" in why["SEAT_LOOKALIKE"] | why["ARMCHAIR_AT_WALL"]
    assert "BOWL_WIDER_THAN_A_WC_PAN" in why["ARMCHAIR_AT_WALL"]
    assert "ROUND_BOWL_TOO_LARGE" in why["ROUND_TABLE_SHELF"]
    assert "ROUND_BOWL_OFF_CISTERN_CENTRE" in why["OFFSET_ROUND"]


@pytest.mark.xfail(strict=True, reason="a seat at a WC pan's size touching a back on the wall face IS a close-coupled "
                                       "WC outline: geometry alone cannot tell them apart (documented limitation "
                                       "L-P8-01; the space is typed with a review flag, never released silently)")
def test_wc_sized_chair_at_a_wall_is_not_a_wc(work):
    assert _lobby_type(_wc(work, "WC_SIZED_CHAIR")) == "REVIEW"


def test_basin_block_linework_is_the_basin(work):
    """the basin block WASH3 draws a bowl-like ellipse and a deck on the wall face: its own linework - matched to the
    fixture through the insert path of every entity drawn inside the block - is excluded; the lobby stays REVIEW."""
    out = _wc(work, "BASIN_OWN_WC_LIKE")
    rec = [c for c in R.corrections(out) if c["correction"] == "WET_EVIDENCE"][0]["detail"]
    assert rec["wc_shapes"] == []
    assert rec["basin_linework_excluded"] >= 2


@pytest.mark.parametrize("transform", ["rot30", "mirror", "metres"])
def test_round_bowl_invariant(work, transform):
    assert _lobby_type(_wc(work, "ROUND_BOWL", transform=transform)) == "WET"


# --------------------------------------------------------------------------- turned columns

def _plan(work, name, method=R.V271, transform=None):
    key = ("plan", name, method, transform)
    if key not in _cache:
        if name == "COLUMN_JAMB":
            src = F.door_plan(work / "CJ.dxf", "COLUMN_JAMB")
        else:
            src = F.column_in_wall(work / f"{name}.dxf", through=(name == "COLUMN_OVER_WALL"))
        if transform:
            src = F.variant(src, work / f"{name}_{transform}.dxf", transform)
        _cache[key] = R.run(src, work / f"o_{name}_{method[-5:].replace('.', '')}_{transform or 'b'}",
                            roles=F.ROLES, facts=True, method=method)
    return _cache[key]


@pytest.mark.parametrize("transform", ["rot30", "rot90", "mirror", "rot37_metres"])
def test_turned_column_is_a_jamb(work, transform):
    """COLUMN_JAMB turned with its plan: the door's opening is still 0.877 m between the masonry jamb and the column
    face (a COLUMN_JAMB), and every BOQ total equals the unturned plan's."""
    base, moved = _plan(work, "COLUMN_JAMB"), _plan(work, "COLUMN_JAMB", transform=transform)
    d = [o for o in R.openings(moved) if o["kind"] == "DOOR"]
    assert len(d) == 1 and abs(d[0]["width_m"] - 0.877) < 1e-3 and "COLUMN_JAMB" in d[0]["jambs"]
    assert not R.diff(base, moved, 1e-5)


def test_v2_7_turned_column_as_found(work):
    """V2.7 as found: turned 30 degrees, the column is no jamb - the opening reads the whole 1.027 m gap."""
    d = [o for o in R.openings(_plan(work, "COLUMN_JAMB", R.V27, "rot30")) if o["kind"] == "DOOR"]
    assert abs(d[0]["width_m"] - 1.027) < 1e-3 and "COLUMN_JAMB" not in d[0]["jambs"]


@pytest.mark.parametrize("name", ["COLUMN_IN_WALL", "COLUMN_OVER_WALL"])
def test_turned_column_interrupts_the_wall(work, name):
    """a 0.30 m column across the north wall - the wall faces stopping at it, or drawn on through it: the wall run is
    12.30 m, turned 30 degrees or not."""
    for t in (None, "rot30"):
        tot = R.totals(_plan(work, name, transform=t))
        run = [v for k, v in tot.items() if k[0] == "ARCH.WALL_RUN"]
        assert len(run) == 1 and abs(run[0][0] - 12.30) < 1e-4, (name, t, run)


# --------------------------------------------------------------------------- provenance

def test_every_measured_line_names_its_entities_or_why_not(work):
    """on the W.C. plan, the bathroom / corridor plan and the column plans every line either carries its drawn
    entities or names why it has none (a quantity with no drawn entity of its own: an owner-question item, an
    engine count); no line is left NOT_TRACED without a reason."""
    outs = [_wc(work, "BASIN"), _plan(work, "COLUMN_JAMB"), _plan(work, "COLUMN_IN_WALL")]
    for out in outs:
        for ln in R.lines(out):
            ent = (ln.get("source") or {}).get("entities") or {}
            if ent.get("basis") == "NOT_TRACED":
                assert ent.get("reason"), (ln["item_code"], ln.get("location"))
