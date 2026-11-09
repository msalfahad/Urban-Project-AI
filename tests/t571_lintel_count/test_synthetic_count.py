"""T-571 R-T571-1 on a synthetic villa Y (not the training villa): precast lintel count by standard length per storey
(owner lintel rule 2026-11-02 / UPC-LINTEL-001: stock 1.20 / 1.50 / 2.50 / 3.00 / 4.00 m, 0.15 m minimum bearing each
side, shortest stock >= w + 2 b, one per opening, > 4.00 m FLAGGED) and its reconciliation in nr with a second list.

NORMAL (hand, b = 0.15):
  Y1 GF w 0.90: 0.90 + 0.30 = 1.20 -> 1.20 m (exactly the stock length: fits)
  Y2 GF w 1.25: 1.55 > 1.50 -> 2.50 m
  Y3 GF w 0.60: 0.90 -> 1.20 m
  Y4 1F w 1.10: 1.40 -> 1.50 m
  Y5 1F w 2.60: 2.90 -> 3.00 m
  Y6 1F w 3.50: 3.80 -> 4.00 m
  Y7 1F w 3.80: 4.10 > 4.00 -> FLAGGED, no piece (never a 4.00 m piece, never 0)
  Y8 GF w 1.00, HELD (head not established): AT_MOST 1.50 m, not ESTABLISHED
  Y9 GF glazing line: NO_LINTEL (0 nr by cause, named)
  -> AT_MOST: 1.20 GF 2; 1.50 GF 1 1F 1; 2.50 GF 1; 3.00 1F 1; 4.00 1F 1 = 7 nr; ESTABLISHED 6 nr; lm beside 2.40 /
     3.00 / 2.50 / 3.00 / 4.00 = 14.90 lm (never added to nr).
  Project bearing 0.40 (named source): Y1 0.90 + 0.80 = 1.70 -> 2.50; Y3 1.40 -> 1.50; Y6 4.30 -> FLAGGED.
RECONCILIATION (other list Z, same villa; hand):
  Z GF 1.00 (census key of Y1: w 1.00 h 2.40)  -> WIDTH_READ: ours 1.20, theirs 1.50 (+1 @1.20, -1 @1.50)
  Z GF 1.25 -> same width as Y2 -> SAME_PIECE; Z GF 0.60 -> Y3 SAME_PIECE; Z 1F 1.10 -> Y4 SAME_PIECE
  Z 1F 2.60 -> Y5 SAME_PIECE; Z GF 1.00 -> Y8 (same width) SAME_PIECE
  Z 1F 2.00 glazing (key of Y9 w 2.00) -> NOT_IN_MASONRY: -1 @2.50
  Z UNSPLIT 0.80 (no storey): Y6 1F 3.50 is left after the same-storey steps -> d_width_read_unsplit: ours 4.00 vs
    theirs 1.20 -> WIDTH_READ (+1 @4.00, -1 @1.20) (an attribution, not a quantity: both counts are unchanged)
  Y7 FLAGGED left alone -> FLAGGED (no piece on our side, counted apart)
  table difference (ours - theirs, AT_MOST): 1.20 2 - 2 = 0; 1.50 2 - 3 = -1; 2.50 1 - 2 = -1; 3.00 1 - 1 = 0;
    4.00 1 - 0 = +1
  causes: WIDTH_READ Y1 (+1 @1.20, -1 @1.50) + Y6 (+1 @4.00, -1 @1.20) = (0, -1, 0, 0, +1); NOT_IN_MASONRY (0, 0, -1, 0,
    0); sum = (0, -1, -1, 0, +1) = the table difference, length by length (asserted in reconcile).
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t571"))

import t571_lintel_count as T  # noqa: E402

ST = ["GF", "1F", "2F", T.UNSPLIT]
PB = (0.40, "villa Y lintel detail 'MIN 40 cm'")


def villa_y():
    return [
        {"id": "Y1", "storey": "GF", "wall_class": "EXT", "width_m": 0.90, "state": T.REQUIRED,
         "key": {"w": 1.00, "h": 2.40, "certain": True}},
        {"id": "Y2", "storey": "GF", "wall_class": "EXT", "width_m": 1.25, "state": T.REQUIRED},
        {"id": "Y3", "storey": "GF", "wall_class": "EXT", "width_m": 0.60, "state": T.REQUIRED},
        {"id": "Y4", "storey": "1F", "wall_class": "EXT", "width_m": 1.10, "state": T.REQUIRED},
        {"id": "Y5", "storey": "1F", "wall_class": "EXT", "width_m": 2.60, "state": T.REQUIRED},
        {"id": "Y6", "storey": "1F", "wall_class": "EXT", "width_m": 3.50, "state": T.REQUIRED},
        {"id": "Y7", "storey": "1F", "wall_class": "EXT", "width_m": 3.80, "state": T.REQUIRED},
        {"id": "Y8", "storey": "GF", "wall_class": "EXT", "width_m": 1.00, "state": T.HELD},
        {"id": "Y9", "storey": "1F", "wall_class": "EXT", "width_m": 2.00, "state": T.NO_LINTEL,
         "key": {"w": 2.00, "h": 3.00, "certain": True}},
    ]


def list_z():
    return T.expand([("GF", "EXT", 1, 1.00, 2.40), ("GF", "EXT", 1, 1.25, 2.00), ("GF", "EXT", 1, 0.60, 0.80),
                     ("1F", "EXT", 1, 1.10, 2.00), ("1F", "EXT", 1, 2.60, 2.00), ("GF", "EXT", 1, 1.00, 2.00),
                     ("1F", "EXT", 1, 2.00, 3.00), (T.UNSPLIT, "EXT", 1, 0.80, 2.40)], "Z")


# ------------------------------------------------------------------ the owner rule, one opening
@pytest.mark.parametrize("w,piece", [(0.90, 1.20), (1.25, 2.50), (0.60, 1.20), (1.10, 1.50), (2.00, 2.50),
                                     (2.60, 3.00), (3.50, 4.00), (1.20, 1.50), (0.50, 1.20)])
def test_piece_shortest_stock(w, piece):
    p = T.piece(w)
    assert p["status"] == T.OK and p["piece_m"] == piece and p["count"] == 1
    assert p["required_m"] == pytest.approx(w + 0.30)


def test_over_4m_flagged_never_forced():
    p = T.piece(3.80)
    assert p["status"] == T.FLAGGED and p["piece_m"] is None and p["count"] is None
    assert p["required_m"] == pytest.approx(4.10)


def test_project_bearing_needs_source_and_changes_piece():
    with pytest.raises(T.CountError):
        T.piece(0.90, 0.40, "")
    assert T.piece(0.90, *PB)["piece_m"] == 2.50
    assert T.piece(0.60, *PB)["piece_m"] == 1.50
    assert T.piece(3.50, *PB)["status"] == T.FLAGGED
    # a project bearing below the company minimum is a CONFLICT, never silently used
    assert T.piece(0.90, 0.10, "a note")["status"] == T.FLAGGED


@pytest.mark.parametrize("w", [900, 90.0, 0, -1.0, None])
def test_units_and_missing(w):
    if w is None:
        assert T.piece(None)["status"] == T.HELD
    else:
        with pytest.raises(T.CountError):
            T.piece(w)


# ------------------------------------------------------------------ count table
def test_count_table_by_hand():
    t = T.count_table(villa_y(), ST)
    am, es = t["at_most"], t["established"]
    assert am[1.2] == {"GF": 2, "1F": 0, "2F": 0, T.UNSPLIT: 0}
    assert am[1.5] == {"GF": 1, "1F": 1, "2F": 0, T.UNSPLIT: 0}
    assert am[2.5]["GF"] == 1 and am[3.0]["1F"] == 1 and am[4.0]["1F"] == 1
    assert t["total_at_most_nr"] == 7 and t["total_established_nr"] == 6
    assert es[1.5] == {"GF": 0, "1F": 1, "2F": 0, T.UNSPLIT: 0}          # Y8 HELD: at most, not established
    assert [f["id"] for f in t["flagged"]] == ["Y7"] and t["no_lintel"] == ["Y9"]
    assert dict(t["lm_beside_at_most"]) == {1.2: 2.4, 1.5: 3.0, 2.5: 2.5, 3.0: 3.0, 4.0: 4.0}
    assert sum(t["lm_beside_at_most"].values()) == pytest.approx(14.90)
    # every storey column and every length row sum to the same total
    assert sum(sum(v.values()) for v in am.values()) == 7


def test_count_table_order_invariant():
    a = T.count_table(villa_y(), ST)
    recs = villa_y()
    random.Random(7).shuffle(recs)
    b = T.count_table(recs, ST)
    assert a["at_most"] == b["at_most"] and a["established"] == b["established"]


def test_lm_reported_as_nr_refused():
    recs = villa_y()
    recs[0] = dict(recs[0], unit="lm", qty=1)
    with pytest.raises(T.CountError, match="nr"):
        T.count_table(recs, ST)


def test_fractional_count_refused():
    recs = villa_y()
    recs[1] = dict(recs[1], qty=2.5)
    with pytest.raises(T.CountError, match="whole"):
        T.count_table(recs, ST)


def test_flagged_given_4m_piece_refused():
    recs = villa_y()
    recs[6] = dict(recs[6], piece_m=4.0)
    with pytest.raises(T.CountError, match="FLAGGED"):
        T.count_table(recs, ST)


def test_wrong_asserted_piece_refused():
    recs = villa_y()
    recs[1] = dict(recs[1], piece_m=1.5)                                  # 1.25 needs 2.50
    with pytest.raises(T.CountError, match="2.5"):
        T.count_table(recs, ST)


def test_opening_twice_refused():
    with pytest.raises(T.CountError, match="twice"):
        T.count_table(villa_y() + [dict(villa_y()[0])], ST)


def test_unknown_state_and_storey_refused():
    with pytest.raises(T.CountError):
        T.count_table([dict(villa_y()[0], state="MAYBE")], ST)
    with pytest.raises(T.CountError):
        T.count_table([dict(villa_y()[0], storey="3F")], ST)


def test_held_without_width_is_listed_never_zero():
    t = T.count_table([{"id": "H1", "storey": "GF", "width_m": None, "state": T.HELD}], ST)
    assert t["no_width"] == ["H1"] and t["total_at_most_nr"] == 0 and t["flagged"] == []


# ------------------------------------------------------------------ reconciliation
def test_reconcile_closes_with_named_causes():
    rc = T.reconcile(villa_y(), list_z())
    by = {(r["ours"], r["theirs"]): r for r in rc["pairs"]}
    assert by[("Y1", "Z-GF-EXT-01")]["cause"] == "WIDTH_READ" and by[("Y1", "Z-GF-EXT-01")]["step"] == "a_census_key"
    assert by[("Y9", "Z-1F-EXT-03")]["cause"] == "NOT_IN_MASONRY"
    assert by[("Y2", "Z-GF-EXT-02")]["cause"] == "SAME_PIECE"
    assert by[("Y8", "Z-GF-EXT-04")]["cause"] == "SAME_PIECE"
    unsplit = [r for r in rc["pairs"] if r.get("theirs") == "Z-UNSPLIT-EXT-01"][0]
    assert unsplit["ours"] == "Y6" and unsplit["step"] == "d_width_read_unsplit"
    flag = [r for r in rc["pairs"] if r["ours"] == "Y7"][0]
    assert flag["cause"] == "FLAGGED" and flag["theirs"] is None
    assert rc["flagged_no_piece_nr"] == {"ours": 1, "theirs": 0}
    d = rc["table_difference_nr_by_length"]
    assert dict(d) == {1.2: 0, 1.5: -1, 2.5: -1, 3.0: 0, 4.0: 1}
    c = rc["causes_nr_by_length"]
    assert dict(c["WIDTH_READ"]) == {1.2: 0, 1.5: -1, 2.5: 0, 3.0: 0, 4.0: 1}
    assert dict(c["NOT_IN_MASONRY"]) == {1.2: 0, 1.5: 0, 2.5: -1, 3.0: 0, 4.0: 0}
    assert {L: sum(c[k][L] for k in c) for L in T.STOCK} == dict(d)
    assert rc["held_or_flagged_in_pairs_nr"] == 1                         # Y8 matched but HELD on our side


def test_reconcile_one_list_only_both_ways():
    ours = villa_y()[:3]
    theirs = T.expand([("GF", "EXT", 1, 0.90, 2.40), ("2F", "EXT", 2, 1.95, 2.00)], "Z")
    rc = T.reconcile([dict(r, key=None) for r in ours], theirs)
    c = rc["causes_nr_by_length"]
    # Y1 0.90 = Z 0.90 same; Y2 1.25 / Y3 0.60 have no GF partner (Z's are 2F) -> ENGINE_ONLY; Z 2F x2 OTHER_ONLY
    assert c["ENGINE_ONLY"][2.5] == 1 and c["ENGINE_ONLY"][1.2] == 1
    assert c["OTHER_ONLY"][2.5] == -2
    assert dict(rc["table_difference_nr_by_length"]) == {1.2: 1, 1.5: 0, 2.5: -1, 3.0: 0, 4.0: 0}


def test_reconcile_thickness_preferred_over_id_order():
    ours = [{"id": "A", "storey": "GF", "wall_class": "INT", "width_m": 1.00, "state": T.REQUIRED, "wall_t_m": 0.15},
            {"id": "B", "storey": "1F", "wall_class": "INT", "width_m": 1.00, "state": T.REQUIRED, "wall_t_m": 0.20}]
    theirs = T.expand([(T.UNSPLIT, "INT", 1, 1.00, 2.40, 0.20)], "Z")
    rc = T.reconcile(ours, theirs)
    pair = [r for r in rc["pairs"] if r.get("theirs")][0]
    assert pair["ours"] == "B"                                            # the 20 cm wall takes the 20 cm row


def test_reconcile_mirror_storey_relabel_invariant():
    """mirroring / renaming storeys changes no count by length (the method holds no coordinate)."""
    ren = {"GF": "1F", "1F": "GF"}
    ours = [dict(r, storey=ren.get(r["storey"], r["storey"])) for r in villa_y()]
    theirs = [dict(t, storey=ren.get(t["storey"], t["storey"])) for t in list_z()]
    a, b = T.reconcile(villa_y(), list_z()), T.reconcile(ours, theirs)
    assert a["causes_nr_by_length"] == b["causes_nr_by_length"]
    assert a["table_difference_nr_by_length"] == b["table_difference_nr_by_length"]


def test_expand_refuses_fractional_row_count():
    with pytest.raises(T.CountError):
        T.expand([("GF", "EXT", 1.5, 1.0, 2.0)], "Z")
