"""T-666: one owner per junction square of an unlabelled beam piece, and a boundary band on a stretch shared in plan
with a building ground beam (research/agents_t666, R-T666-1 / R-T666-2). Hand villa "V666" (not the training villa)
with normal and adverse cases, then the development-villa ledger rebuilt from committed repository files."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t666"))
import t666_rules as R  # noqa: E402
import t666_alsenan as A  # noqa: E402

D = Decimal
OUT = ROOT / "research" / "agents_t666" / "out" / "T666_LEDGER.json"


# ---- villa "V666" (hand) -----------------------------------------------------------------------------------------
# A 0.25 m wide unlabelled piece runs north from the plot-side edge band (0.30 wide, 0.50 deep). The edge band's two
# lines are measured up to the piece's faces (adjacent boxes), so the piece's drawn outline owns the 0.25 x 0.30 square.
# At its north end it meets a column 0.25 x 0.60 (from y 2.80) with a 0.20 crossing beam drawn THROUGH the column.
#   owned length = 3.00 (outer line .. far face of the crossing beam) - 0.20 (square inside the column) = 2.80 m
#   bound with schedule depths 0.50 .. 0.75: 0.25 x 2.80 x 0.50 = 0.350000 .. 0.25 x 2.80 x 0.75 = 0.525000 m3
EDGE_W, EDGE_E = ("-3.00", "0", "0", "0.30"), ("0.25", "0", "4.00", "0.30")
SOUTH_SQ, NORTH_SQ = ("0", "0", "0.25", "0.30"), ("0", "2.80", "0.25", "3.00")
COLUMN = ("C1", ("0", "2.80", "0.25", "3.40"))
CROSS = ("CB-through", ("-3.00", "2.80", "4.00", "3.00"))  # drawn through the column


def _owners(sq_list, columns, through, rot=lambda b: b):
    return [R.square_owner(rot(sq), columns=[(i, rot(b)) for i, b in columns],
                           through=[(i, rot(b)) for i, b in through], piece_id="P1") for sq in sq_list]


def test_hand_t_junction_normal():
    """Normal T-junction: the neighbour stops at the piece's faces -> the piece keeps the square, far-face length."""
    assert R.square_owner(SOUTH_SQ, through=[("E-W", EDGE_W), ("E-E", EDGE_E)], piece_id="P1") == ("PIECE", "P1")
    L = R.owned_length(("0", "3.00"), [("0", "0.30", ("PIECE", "P1"))])
    assert L == D("3.00")
    assert R.envelope("0.25", L, "0.50", "0.75") == (D("0.375000"), D("0.562500"))


def test_hand_column_at_junction_adverse():
    """A beam drawn through a column does not take the square: the column owns it to the slab top (UP-CONC-JOINT-001)."""
    owners = _owners([SOUTH_SQ, NORTH_SQ], [COLUMN], [("E-W", EDGE_W), ("E-E", EDGE_E), CROSS])
    assert owners == [("PIECE", "P1"), ("COLUMN", "C1")]
    L = R.owned_length(("0", "3.00"), [("0", "0.30", owners[0]), ("2.80", "3.00", owners[1])])
    assert L == D("2.80")
    assert R.envelope("0.25", L, "0.50", "0.75") == (D("0.350000"), D("0.525000"))
    # the column runs to the slab top: no exposure whatever the piece depth
    assert R.depth_exposure("COLUMN", "0.05", d_other="0.50", d_piece_low="0.50", d_piece_high="0.75") == (0, 0)


def test_hand_near_face_everywhere_leaves_a_square_in_no_line():
    """The all-near-face length 2.50 loses the south square (0.25 x 0.30 x 0.50 .. 0.75) that no other line bills."""
    near = D("3.00") - D("0.30") - D("0.20")
    owned = R.owned_length(("0", "3.00"), [("0", "0.30", ("PIECE", "P1")), ("2.80", "3.00", ("COLUMN", "C1"))])
    assert owned - near == D("0.30")
    lost = R.envelope("0.25", "0.30", "0.50", "0.75")
    assert lost == (D("0.037500"), D("0.056250"))


@pytest.mark.parametrize("rot", [
    lambda b: (str(-D(b[2])), b[1], str(-D(b[0])), b[3]),                         # mirror about x = 0
    lambda b: (b[1], b[0], b[3], b[2]),                                            # rotation by 90 deg (swap axes)
    lambda b: tuple(str(D(v) + D("12.5")) for v in b),                            # translation
])
def test_hand_mirror_rotation_translation(rot):
    owners = _owners([SOUTH_SQ, NORTH_SQ], [COLUMN], [("E-W", EDGE_W), ("E-E", EDGE_E), CROSS], rot)
    assert owners == [("PIECE", "P1"), ("COLUMN", "C1")]


def test_hand_through_member_and_exposures():
    """A through beam whose span covers the square owns it; the piece deeper than it is named beside, never added."""
    sq = ("0", "-0.40", "0.25", "0")
    assert R.square_owner(sq, through=[("B-through", ("-2.0", "-0.40", "3.0", "0"))], piece_id="P2") == ("THROUGH", "B-through")
    assert R.depth_exposure("THROUGH", "0.10", d_other="0.60", d_piece_low="0.50", d_piece_high="0.75") == (D(0), D("0.015000"))
    assert R.depth_exposure("THROUGH", "0.10", d_other="0.80", d_piece_low="0.50", d_piece_high="0.75") == (D(0), D(0))
    # corner kept by the piece next to a deeper member that stops at it: GAP exposure below the piece's low soffit
    assert R.depth_exposure("PIECE", "0.04", d_other="0.75", d_piece_low="0.40", d_piece_high="1.20") == (D(0), D("0.014000"))


@pytest.mark.parametrize("kw,msg", [
    (dict(through=[("A", ("-1", "0", "1", "0.30")), ("B", ("-1", "0", "1", "0.30"))]), "DOUBLE"),
    (dict(through=[("A", ("0.10", "0", "2", "0.30"))]), "PARTIAL"),
    (dict(columns=[("C", ("0", "0.10", "0.25", "0.80"))]), "PARTIAL"),
    (dict(columns=[("C", ("0", "0", "0.25", "0.60")), ("C2", ("0", "0", "0.25", "0.60"))]), "DOUBLE"),
])
def test_hand_two_or_partial_owners_refused(kw, msg):
    with pytest.raises(R.Refused, match=msg):
        R.square_owner(SOUTH_SQ, piece_id="P1", **kw)


@pytest.mark.parametrize("call", [
    lambda: R.square_owner(None, piece_id="P1"),                                   # square not drawn
    lambda: R.square_owner(("0", "0", "0", "0.3"), piece_id="P1"),                 # empty square
    lambda: R.owned_length(("0", "3000"), []),                                     # mm
    lambda: R.owned_length(("0", "3.00"), [("1.0", "1.2", ("COLUMN", "C"))]),      # mid-span square
    lambda: R.owned_length(("0", "3.00"), [("2.9", "3.2", ("COLUMN", "C"))]),      # outside the extent
    lambda: R.owned_length(("0", "0.20"), [("0", "0.20", ("COLUMN", "C"))]),       # nothing left: never 0
    lambda: R.envelope("0.25", "2.80", "0.75", "0.50"),                            # low > high
    lambda: R.envelope("0.25", None, "0.50", "0.75"),                              # missing length: HELD, never 0
    lambda: R.depth_exposure("PIECE", "0.04", d_other=None, d_piece_low="0.4", d_piece_high="1.2"),
])
def test_hand_adverse_inputs_refused(call):
    with pytest.raises(R.Refused):
        call()


# ---- R-T666-2: boundary band on a plot-line stretch shared with a building ground beam --------------------------
def test_hand_band_on_plot_line_disjoint_keeps_both():
    r = R.stretch_ownership(shared_length="12.00", band_width="0.20", band_depth_low="0.40", band_depth_high="0.60",
                            relation="DISJOINT")
    assert r["status"] == "OWNED_ONCE_EACH" and r["deduction_m3"] == 0


@pytest.mark.parametrize("relation,prec", [("UNKNOWN", None), ("INTERSECT", None)])
def test_hand_band_on_plot_line_adverse_held_not_deducted(relation, prec):
    """Plan coincidence alone deducts nothing; unknown levels or no precedence -> HELD exposure beside, not 0."""
    r = R.stretch_ownership(shared_length="12.00", band_width="0.20", band_depth_low="0.40", band_depth_high="0.60",
                            relation=relation, precedence=prec)
    assert r["status"] == "HELD_EXPOSURE" and r["deduction_m3"] is None
    assert r["exposure_m3"] == (D(0), D("1.440000"))


def test_hand_band_intersect_with_precedence_owned_once():
    r = R.stretch_ownership(shared_length="12.00", band_width="0.20", band_depth_low="0.40", band_depth_high="0.60",
                            relation="INTERSECT", precedence="GROUND_BEAM")
    assert r["status"] == "OWNED_ONCE_BY_GROUND_BEAM"


@pytest.mark.parametrize("kw", [dict(relation="PLAN_OVERLAP"), dict(relation="UNKNOWN", shared_length="12000"),
                                dict(relation="UNKNOWN", band_depth_low="0.70")])
def test_hand_band_adverse_refused(kw):
    base = dict(shared_length="12.00", band_width="0.20", band_depth_low="0.40", band_depth_high="0.60")
    base.update(kw)
    with pytest.raises(R.Refused):
        R.stretch_ownership(**base)


# ---- development villa (committed files only) --------------------------------------------------------------------
@pytest.fixture(scope="module")
def doc():
    return A.build()


def test_dev_rebuild_equals_committed(doc):
    assert json.loads(OUT.read_text(encoding="utf-8")) == json.loads(json.dumps(doc, sort_keys=True))


def test_dev_each_line_once_each_square_one_owner(doc):
    ids = [r["line_id"] for r in doc["pieces"]]
    assert len(ids) == len(set(ids)) == 5
    for r in doc["pieces"]:
        assert all(s["owner_kind"] in ("PIECE", "COLUMN", "THROUGH") for s in r["squares"])
        # a square kept by the piece is inside its length; a square owned by another is outside it
        kept = sum(D(s["area_m2"]) / D("0.20") for s in r["squares"] if s["owner_kind"] == "PIECE")
        assert D(r["owned_length_m"]) == D(r["all_near_face_length_m"]) + kept


def test_dev_key_figures(doc):
    by = {r["element"]: r for r in doc["pieces"]}
    assert by["2F BAND0008.1"]["after"] == ["0.112000", "0.336000"]
    assert by["2F BAND0011.1"]["after"] == ["0.112000", "0.336000"]
    assert by["2F BAND0006.1"]["after"] == ["0.248000", "0.744000"]
    assert by["2F BAND0001.3"]["after"] == ["0.090400", "0.271200"]
    assert by["1F BAND0005.1"]["after"] == ["0.064000", "0.192000"]
    assert doc["pieces_totals"] == {"before": ["0.626256", "1.878768"], "after": ["0.626400", "1.879200"],
                                    "delta": ["0.000144", "0.000432"]}
    assert by["2F BAND0001.3"]["exposures_beside"][0]["m3"] == ["0", "0.014000"]
    assert by["1F BAND0005.1"]["exposures_beside"][0]["m3"] == ["0", "0.040500"]
    for r in doc["pieces"]:
        assert r["status"] == "HELD_BOUNDED_AS_DRAWN"   # nothing released


def test_dev_band_unchanged_and_owned_once(doc):
    b = doc["band"]
    assert b["after"] == b["T659_bound"] == ["5.639200", "11.032800"]
    assert b["continues_under_building_stretches"] is True
    assert b["shared_centre_line_m"] == "43.60" and b["shared_free_m"] == "25.02"
    assert all(s["deduction_m3"] == "0" for s in b["stretches"])


def test_dev_no_absolute_coordinates_or_workbook_text():
    """Only relative member geometry (m) is committed: no drawing coordinate (thousands of mm), no workbook text."""
    import re
    s = OUT.read_text(encoding="utf-8")
    assert not re.search(r"(?<![A-Z0-9])\d{4,}\.\d", s)
    assert "freelancer" not in s.lower() and "xlsx" not in s.lower()
