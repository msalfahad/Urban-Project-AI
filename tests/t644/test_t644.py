"""T-644 R-T644-1 precast lintel pieces per opening: a non-Alsenan fixture worked by hand (normal, mirrored, reordered),
the rule's adverse cases, the training-villa rebuild (byte-identical, merged inputs only) and, when the private drawing is
present, the jamb re-measure (fresh run == committed numbers-only evidence; written only under .work/private)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t644"
sys.path.insert(0, str(HERE))
import t644_lintel_pieces as R  # noqa: E402


def E(a, b, sa=None, sb=None):
    return {"START": {"a_m": a, "shared_with": sa}, "END": {"a_m": b, "shared_with": sb}}


# ------------------------------------------------------------------ fixture villa Y (not Alsenan), worked by hand
# By hand (owner rule, 0.15 m each side): 0.90 + 0.30 = 1.20 -> 1.20 ; 1.20 + 0.30 = 1.50 -> 1.50 ; 2.70 + 0.30 = 3.00
# -> 3.00 ; 3.80 + 0.30 = 4.10 > 4.00 -> FLAGGED_OVER_4M ; 4.20 + 0.30 = 4.50 -> FLAGGED_OVER_4M ; 3.60 + 0.30 = 3.90 ->
# 4.00 (the 4.00 stock length is reachable). The task row expected '3.80 -> 4.00': that needs a 0.10 m bearing, below the
# owner minimum, so the rule FLAGS it (F-T644-3) and a 4.00 piece asserted for it is refused (adverse below).
def villa_y():
    return [
        {"id": "D1", "storey": "GF", "width_m": 0.90, "existence": "REQUIRED", "ends": E(0.50, 0.40)},
        {"id": "D2", "storey": "GF", "width_m": 1.20, "existence": "REQUIRED", "ends": E(0.20, 0.30)},
        {"id": "W1", "storey": "1F", "width_m": 2.70, "existence": "REQUIRED", "ends": E(0.15, 0.60)},
        {"id": "W2", "storey": "1F", "width_m": 3.80, "existence": "REQUIRED", "ends": E(1.00, 1.00)},
        {"id": "W3", "storey": "1F", "width_m": 4.20, "existence": "REQUIRED", "ends": E(1.00, 1.00)},
        {"id": "W4", "storey": "2F", "width_m": 3.60, "existence": "HELD", "cause": "head not printed",
         "ends": E(0.20, 0.20)},
    ]


def test_villa_y_by_hand():
    per = R.classify(villa_y())
    assert {k: (p["cls"], p.get("piece_m")) for k, p in per.items()} == {
        "D1": ("PIECE", 1.2), "D2": ("PIECE", 1.5), "W1": ("PIECE", 3.0), "W2": ("FLAGGED_OVER_4M", None),
        "W3": ("FLAGGED_OVER_4M", None), "W4": ("PIECE_IF_BUILT", 4.0)}
    t = R.tables(per, ["GF", "1F", "2F"])
    assert t["established_total_nr"] == 3 and t["at_most_total_nr"] == 4
    assert t["established_nr"][1.2]["GF"] == 1 and t["established_nr"][1.5]["GF"] == 1
    assert t["established_nr"][3.0]["1F"] == 1 and t["at_most_nr"][4.0]["2F"] == 1
    assert t["lm_beside_established"][3.0] == 3.0 and sum(t["lm_beside_at_most"].values()) == pytest.approx(9.7)
    assert t["class_counts"]["FLAGGED_OVER_4M"] == 2


def test_overhang_exactly_used_fits_and_one_mm_less_is_short():
    # 1.00 + 0.30 = 1.30 -> 1.50: overhang 0.50 = 0.30 + 0.20 exactly (fits); 0.299 + 0.200 = 0.499 -> SHORT
    ok = R.classify([{"id": "A", "storey": "GF", "width_m": 1.0, "existence": "REQUIRED", "ends": E(0.30, 0.20)}])
    no = R.classify([{"id": "A", "storey": "GF", "width_m": 1.0, "existence": "REQUIRED", "ends": E(0.299, 0.20)}])
    assert ok["A"]["cls"] == "PIECE" and no["A"]["cls"] == "FLAGGED_SHORT_PIERS"


def test_shared_pier_by_hand():
    # two 0.80 doors (piece 1.20, overhang 0.40 each), outer ends 0.80: each needs max(0.15, 0.40 - 0.80) = 0.15 on the
    # pier: pier 0.30 fits both, 0.29 fits neither
    def pair(p):
        return R.classify([
            {"id": "D1", "storey": "GF", "width_m": 0.8, "existence": "REQUIRED", "ends": E(0.80, p, None, "D2")},
            {"id": "D2", "storey": "GF", "width_m": 0.8, "existence": "REQUIRED", "ends": E(p, 0.80, "D1", None)}])
    assert {k: v["cls"] for k, v in pair(0.30).items()} == {"D1": "PIECE", "D2": "PIECE"}
    assert {k: v["cls"] for k, v in pair(0.29).items()} == {"D1": "FLAGGED_SHARED_PIER", "D2": "FLAGGED_SHARED_PIER"}


def test_shared_pier_short_outer_end_raises_the_pier_share():
    # D1 outer end 0.20: it must put 0.40 - 0.20 = 0.20 on the pier; D2 0.15: pier 0.34 < 0.35 -> both FLAGGED
    ops = [{"id": "D1", "storey": "GF", "width_m": 0.8, "existence": "REQUIRED", "ends": E(0.20, 0.34, None, "D2")},
           {"id": "D2", "storey": "GF", "width_m": 0.8, "existence": "REQUIRED", "ends": E(0.34, 0.80, "D1", None)}]
    assert {p["cls"] for p in R.classify(ops).values()} == {"FLAGGED_SHARED_PIER"}
    ops[0]["ends"]["END"]["a_m"] = ops[1]["ends"]["START"]["a_m"] = 0.35
    assert {p["cls"] for p in R.classify(ops).values()} == {"PIECE"}


def test_neighbour_without_a_stock_piece_leaves_the_pier_whole():
    ops = [{"id": "W1", "storey": "GF", "width_m": 0.6, "existence": "HELD", "cause": "c", "ends": E(0.40, 0.20, None, "W2")},
           {"id": "W2", "storey": "GF", "width_m": 0.6, "existence": "HELD", "cause": "c", "ends": E(0.20, 0.0, "W1", None)}]
    per = R.classify(ops)
    assert per["W2"]["cls"] == "FLAGGED_NO_BEARING" and per["W1"]["cls"] == "PIECE_IF_BUILT"


def test_mirror_and_order_invariance():
    base = {k: (p["cls"], p.get("piece_m")) for k, p in R.classify(villa_y()).items()}
    mir = villa_y()
    for o in mir:
        o["ends"] = {"START": o["ends"]["END"], "END": o["ends"]["START"]}
    assert {k: (p["cls"], p.get("piece_m")) for k, p in R.classify(mir).items()} == base
    assert {k: (p["cls"], p.get("piece_m")) for k, p in R.classify(list(reversed(villa_y()))).items()} == base


def test_unresolved_width_flagged_at_both_ends_is_flagged_else_held():
    both = R.classify([{"id": "X", "storey": "GF", "width_bound_m": [0.9, 1.0], "existence": "HELD", "cause": "c",
                        "ends": E(1.45, 0.147)}])
    assert both["X"]["cls"] == "FLAGGED_NO_BEARING" and both["X"]["piece_beside_m"] == [1.2, 1.5]
    one = R.classify([{"id": "X", "storey": "GF", "width_bound_m": [0.9, 1.0], "existence": "HELD", "cause": "c",
                       "ends": E(0.35, 0.10 + 0.15)}])   # 0.9: 0.30 <= 0.60 fits; 1.0: 0.50 <= 0.60 fits -> HELD_WIDTH
    assert one["X"]["cls"] == "HELD_WIDTH" and one["X"].get("piece_m") is None


def test_head_room_and_register_holds_carry_no_piece():
    per = R.classify([
        {"id": "H", "storey": "GF", "width_m": 1.2, "existence": "FLAGGED_HEAD_ROOM", "cause": "soffit", "ends": E(1, 1)},
        {"id": "L", "storey": "GF", "width_m": 1.0, "existence": "HELD_REGISTER", "cause": "lift", "ends": E(1, 1)}])
    assert per["H"]["cls"] == "FLAGGED_HEAD_ROOM" and per["L"]["cls"] == "HELD_REGISTER"
    assert per["H"].get("piece_m") is None and per["L"].get("piece_m") is None and per["L"]["piece_beside_m"] == [1.5]


# ------------------------------------------------------------------ adverse
def test_bearing_omitted_is_held_and_a_piece_for_it_refused():
    per = R.classify([{"id": "D", "storey": "GF", "width_m": 0.9, "existence": "REQUIRED", "ends": None},
                      {"id": "E", "storey": "GF", "width_m": 0.9, "existence": "REQUIRED",
                       "ends": {"START": {"a_m": 0.5}, "END": {"a_m": None}}}])
    assert per["D"]["cls"] == "HELD_ENDS" and per["E"]["cls"] == "HELD_ENDS"
    with pytest.raises(R.PieceError, match="no stock piece"):
        R.check_asserted_piece({"id": "D", "piece_m": 1.2}, per)


def test_over_4m_given_a_piece_refused():
    per = R.classify(villa_y())
    with pytest.raises(R.PieceError, match="FLAGGED_OVER_4M"):
        R.check_asserted_piece({"id": "W2", "piece_m": 4.0}, per)
    assert R.check_asserted_piece({"id": "W1", "piece_m": 3.0}, per)
    with pytest.raises(R.PieceError, match="not the rule's"):
        R.check_asserted_piece({"id": "W1", "piece_m": 4.0}, per)
    with pytest.raises(R.PieceError, match="nr"):
        R.check_asserted_piece({"id": "W1", "piece_m": 3.0, "unit": "lm"}, per)
    with pytest.raises(R.PieceError, match="one piece per opening"):
        R.check_asserted_piece({"id": "W1", "piece_m": 3.0, "qty": 2}, per)


@pytest.mark.parametrize("w", [900, 90.0, 0, -1.0, None, True, float("nan")])
def test_bad_widths_refused_or_held(w):
    o = {"id": "D", "storey": "GF", "width_m": w, "existence": "REQUIRED", "ends": E(0.5, 0.5)}
    if w is None:
        assert R.classify([o])["D"]["cls"] == "HELD_WIDTH"
    else:
        with pytest.raises(R.PieceError):
            R.classify([o])


def test_duplicate_unknown_existence_and_one_sided_pier_refused():
    with pytest.raises(R.PieceError, match="twice"):
        R.classify(villa_y() + [villa_y()[0]])
    with pytest.raises(R.PieceError, match="existence"):
        R.classify([{"id": "D", "storey": "GF", "width_m": 0.9, "existence": "MAYBE", "ends": E(1, 1)}])
    with pytest.raises(R.PieceError, match="not recorded on its side"):
        R.classify([{"id": "D1", "storey": "GF", "width_m": 0.8, "existence": "REQUIRED", "ends": E(1, 0.3, None, "D2")},
                    {"id": "D2", "storey": "GF", "width_m": 0.8, "existence": "REQUIRED", "ends": E(0.3, 1)}])
    with pytest.raises(R.PieceError, match="measured twice"):
        R.classify([{"id": "D1", "storey": "GF", "width_m": 0.8, "existence": "REQUIRED", "ends": E(1, 0.3, None, "D2")},
                    {"id": "D2", "storey": "GF", "width_m": 0.8, "existence": "REQUIRED", "ends": E(0.5, 1, "D1")}])
    with pytest.raises(R.PieceError, match="metres"):
        R.classify([{"id": "D", "storey": "GF", "width_m": 0.9, "existence": "REQUIRED", "ends": E(150, 1)}])


def test_tables_refuse_a_piece_on_a_flagged_record():
    per = R.classify(villa_y())
    per["W2"] = dict(per["W2"], piece_m=4.0)
    with pytest.raises(R.PieceError, match="never a piece"):
        R.tables(per, ["GF", "1F", "2F"])


# ------------------------------------------------------------------ training villa (merged inputs, no private file)
def test_training_villa_rebuild_is_byte_identical_and_re_adds():
    res = R._keyfix(R.build())
    committed = json.loads((HERE / "out" / "T644_LINTEL_PIECES.json").read_text())
    assert json.loads(json.dumps(res)) == committed
    t = res["tables"]
    assert res["openings"] == 60 and res["candidate_lines"] == 60
    assert sum(t["class_counts"].values()) == 60
    assert t["class_counts"] == {"PIECE": 13, "PIECE_IF_BUILT": 24, "FLAGGED_OVER_4M": 0, "FLAGGED_NO_BEARING": 13,
                                 "FLAGGED_SHORT_PIERS": 0, "FLAGGED_SHARED_PIER": 4, "FLAGGED_HEAD_ROOM": 2,
                                 "HELD_WIDTH": 0, "HELD_ENDS": 1, "HELD_REGISTER": 3}
    est = {L: sum(v.values()) for L, v in t["established_nr"].items()}
    most = {L: sum(v.values()) for L, v in t["at_most_nr"].items()}
    assert est == {"1.2": 5, "1.5": 5, "2.5": 2, "3.0": 1, "4.0": 0}
    assert most == {"1.2": 18, "1.5": 9, "2.5": 9, "3.0": 1, "4.0": 0}
    assert sum(t["lm_beside_established"].values()) == pytest.approx(21.5)
    assert sum(t["lm_beside_at_most"].values()) == pytest.approx(21.6 + 13.5 + 22.5 + 3.0)
    assert all(g["same_piece"] for g in res["gap_check"])
    per = res["per_opening"]
    for oid in ("D-1F-04", "D-GF-06", "W18", "D-GF-09", "P-GF-01"):
        assert per[oid]["cls"] == "FLAGGED_NO_BEARING" and per[oid].get("piece_m") is None
    assert {o for o in per if per[o]["cls"] == "FLAGGED_SHARED_PIER"} == {"D-GF-03", "W04", "D-GF-11", "D-GF-12"}
    assert all(m["class_now"] == "HELD" for m in res["m3_lines"].values())


def test_stale_ledger_refused(monkeypatch):
    monkeypatch.setitem(R.PINS, "ledger", "0" * 16)
    with pytest.raises(R.PieceError, match="stale"):
        R.alsenan_openings()


# ------------------------------------------------------------------ jamb re-measure (private drawing only)
PRIVATE = ROOT.parent / "private"
DXF = PRIVATE / "P7757" / "P7757.dxf"


@pytest.mark.skipif(not DXF.is_file(), reason="private drawing P7757.dxf absent (Drive-only input)")
def test_jamb_rerun_equals_committed_evidence():
    assert hashlib.sha256(DXF.read_bytes()).hexdigest()[:8] == "ab54dd55"
    scratch = PRIVATE / "t644"
    scratch.mkdir(parents=True, exist_ok=True)
    pkl, js = scratch / "t125_inputs.pkl", scratch / "t125_v2.json"
    if not pkl.is_file() or not js.is_file():
        sys.path.insert(0, str(ROOT / "research" / "agents_t125"))
        import alsenan_v2_dump
        import alsenan_v2_run
        alsenan_v2_dump.main([str(DXF), "--out", str(pkl)])
        alsenan_v2_run.main([str(pkl), "--out", str(js)])
    import t644_extract as X
    fresh = scratch / "fresh" / "JAMB_EVIDENCE_T644.csv"
    fresh.parent.mkdir(exist_ok=True)
    X.main(str(scratch), out=fresh)          # also asserts the 16 T-527 control openings reproduce
    assert fresh.read_bytes() == (HERE / "out" / "JAMB_EVIDENCE_T644.csv").read_bytes()
