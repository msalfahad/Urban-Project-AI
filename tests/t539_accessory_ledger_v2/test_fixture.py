"""T-539 (R-T539-1, COLUMN_END_ACCESSORY_LEDGER_V2) on a hand-calculated villa that is not the development villa (P539).

Villa P539, one storey 3.60 m (structural floor 0.00, finished floor 0.10). Owner band: interior plaster 0.10 .. 3.00,
exterior Sigma 0.00 .. 3.60. Project block schedule (fixture): black 0.20 m block 39 x 19 + 10 mm joint ONLY (no 0.15 m
entry). Two walls, three column ENDS (V3 end census) and one interior column:
  W1 internal, t 0.20, run R1: P0 COLUMN C1 0.30 (crossed), P1 BEAM BM1 h 0.50 4.00 m -> block top 3.60 - 0.50 = 3.10;
     end 1 stops on column K2 (END_COLUMN, gap 0).
  W2 external, t 0.15, run R2: P0 BEAM BM2 h 0.45 3.00 m -> block top 3.15; both ends stop on columns K3 / K4.
Hand count:
  ties (levels z = 3 k x module while z + 0.010 < top):
    module 0.200: top 3.10 -> 0.6 1.2 1.8 2.4 3.0 = 5; top 3.15 -> 5.  module 0.210: top 3.15 -> 0.63 .. 2.52 = 4
    (3.15 + 0.01 >= 3.15).  module 0.250: top 3.15 -> 0.75 1.5 2.25 3.0 = 4.
    W1: C1 interior 5 + K2 end 5 = 10 MEASURED.  W2 (0.15, no sourced module): K3 / K4 HELD, figures S-A 5 + 5,
    S-B 4 + 4, S-C 4 + 4 (never summed into the measured 10).
  bed-joint strip added by the three ends: 0 m.l (end face = column face; clear length unchanged).
  V-joint mesh at the ends: K2 (2 interior sides): owner 2 x (min(3.10, 3.00) - 0.10) = 5.80, drawing 2 x (3.10 - 0.10)
    = 6.00. K3 and K4 each: INT owner 2.90 / drawing 3.05; EXT owner = drawing (one band) min(3.15, 3.60) - 0 = 3.15
    (T-317's raw drawing band would read 3.05). Ends total owner 5.80 + 2 x 6.05 = 17.90; drawing 6.00 + 2 x 6.20 = 18.40.
Adverse: sliver end under another member HELD (F-C-T532-1), sliver of the same member keeps the member's head; unknown
kind HELD; partial column HELD; mirrored run identical; duplicate junction refused; gap beyond a joint and a moved run
length refused; 0.15 never takes the 0.20 module; white HELD; millimetres refused; HELD never carries a number.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in ("agents_t539", "agents_t532", "agents_t526", "agents_t533", "agents_t317"):
    sys.path.insert(0, str(ROOT / "research" / p))
import accessory_ledger_v2 as V  # noqa: E402
import block_module_v1 as BM  # noqa: E402
import end_census_v3 as V3  # noqa: E402
import t317_spatter_mesh as M  # noqa: E402

REG = [BM.ModuleEntry("BLACK", 0.20, 0.39, 0.19, 0.010, 0.010, "P539 block schedule (fixture)", "PROJECT_DOCUMENT")]
SCEN = [("S-A", V.course(0.19, 0.010, "what-if", "WHAT-IF")), ("S-B", V.course(0.20, 0.010, "what-if", "WHAT-IF")),
        ("S-C", V.course(0.24, 0.010, "what-if", "WHAT-IF"))]
FFL = 0.10
INT = [V.FinishedSide("INT-A", "PLASTER", 0.10, 3.00), V.FinishedSide("INT-B", "PLASTER", 0.10, 3.00)]
EXT = [V.FinishedSide("INT", "PLASTER", 0.10, 3.00), V.FinishedSide("EXT", "SIGMA", 0.00, 3.60)]
COL = V3.EndResult("COLUMN", 0.0, 1.0, 0.20, 0, True)
IN_RUN = V3.EndResult("COLUMN_PIECE_IN_RUN", 0.0, 1.0, 0.20, 0, True)


def course(t, btype="BLACK"):
    return V.course_for(BM.resolve, REG, btype, t)


def ties_for(junctions, t, tops, btype="BLACK"):
    c, held = course(t, btype)
    out = []
    for j, top in zip(junctions, tops):
        out.append(V.tie_record(j["state"], j.get("held", ""), c, held, top, SCEN if c is None else ()))
    return out


# ---------------------------------------------------------------------------------------------- normal case

def test_v3_population_of_the_fixture():
    r1 = V3.end_junctions_v3("R1", ["COLUMN", "BEAM"], [IN_RUN, COL])
    r2 = V3.end_junctions_v3("R2", ["BEAM"], [COL, COL])
    assert [(j["source"], j["state"], j["class"]) for j in r1] == [("V3_INTERIOR", "LISTED", "COLUMN-BEAM"),
                                                                    ("V3_END", "LISTED", "BEAM-END_COLUMN")]
    assert [(j["source"], j["at"]) for j in r2] == [("V3_END", "end 0"), ("V3_END", "end 1")]


def test_ties_hand_count_measured_and_held_015():
    r1 = V3.end_junctions_v3("R1", ["COLUMN", "BEAM"], [IN_RUN, COL])
    r2 = V3.end_junctions_v3("R2", ["BEAM"], [COL, COL])
    w1 = ties_for(r1, 0.20, [3.10, 3.10])
    w2 = ties_for(r2, 0.15, [3.15, 3.15])
    assert [t["ties"] for t in w1] == [5, 5] and all(t["state"] == "MEASURED" for t in w1)
    assert all(t["state"] == "HELD" and t["ties"] is None for t in w2)
    assert all("0.15 m black" in t["held"] for t in w2)
    assert [t["figures"] for t in w2] == [{"S-A": 5, "S-B": 4, "S-C": 4}] * 2
    rows = [dict(t, wall_id=w, column_at=c, face=f, t_m=tm) for t, w, c, f, tm in
            zip(w1 + w2, ["W1", "W1", "W2", "W2"], ["C1", "K2", "K3", "K4"],
                ["column_end", "column_start", "column_end", "column_start"], ["0.20", "0.20", "0.15", "0.15"])]
    pop = V.merge_population(rows[:1], rows[1:])
    assert V.tie_totals(pop) == {"junctions": 4, "measured_junctions": 2, "ties_measured": 10, "held_junctions": 2}
    V.no_zero_held(pop, ("ties",))


def test_strip_added_by_each_end_is_zero():
    assert [V.end_strip_delta(0.0, 0.0, 0.010) for _ in range(3)] == [0.0, 0.0, 0.0]


def test_vjoint_hand_values_and_t317_agrees():
    k2 = V.end_vjoint(INT, 3.10, FFL)
    k3 = V.end_vjoint(EXT, 3.15, FFL)
    assert [(x["owner_m"], x["drawing_m"]) for x in k2] == [(2.90, 3.00), (2.90, 3.00)]
    assert [(x["side"], x["owner_m"], x["drawing_m"]) for x in k3] == [("INT", 2.90, 3.05), ("EXT", 3.15, 3.15)]
    own = sum(x["owner_m"] for x in k2) + 2 * sum(x["owner_m"] for x in k3)
    drw = sum(x["drawing_m"] for x in k2) + 2 * sum(x["drawing_m"] for x in k3)
    assert round(own, 6) == 17.90 and round(drw, 6) == 18.40
    # independent path: the merged T-317 joint code on the same wall with the end column as a piece
    sides = [M.Side(s.side, s.finish, s.band_bottom, s.band_top) for s in EXT]
    w = M.make_wall("W2", 3.60, [M.Piece("COLUMN", 0.20, None, "K3"), M.Piece("BLOCK", 3.00, 3.15, "BM2", (), "BEAM"),
                                 M.Piece("COLUMN", 0.20, None, "K4")], sides)
    o = [j for j in M.joints(w) if j["dir"] == "V"]
    d = [j for j in M.joints_to_soffit(w, FFL) if j["dir"] == "V"]
    assert sorted((j["side"], j["length_m"]) for j in o) == [("EXT", 3.15), ("EXT", 3.15), ("INT", 2.90), ("INT", 2.90)]
    assert sorted((j["side"], j["length_m"]) for j in d) == [("EXT", 3.05), ("EXT", 3.05), ("INT", 3.05), ("INT", 3.05)]


# ---------------------------------------------------------------------------------------------- adverse cases

def test_sliver_end_under_another_member_is_held():
    top, held, why = V.end_head((0.002, 3.40, "F9"), (4.00, 3.10, "BM1"))
    assert top is None and held == V.SLIVER_HELD and why.startswith("OTHER_MEMBER")
    t = V.tie_record("HELD", held, *course(0.20), None)
    assert t["state"] == "HELD" and t["ties"] is None and "sliver" in t["held"]


def test_sliver_of_the_same_member_keeps_the_member_head():
    top, held, why = V.end_head((0.002, 3.10, "BM1"), (4.00, 3.10, "BM1"))
    assert (top, held) == (3.10, "") and why.startswith("SAME_MEMBER")
    assert V.tie_record("LISTED", "", *course(0.20), top)["ties"] == 5
    # same member id but a different top is not the same soffit: HELD
    assert V.end_head((0.002, 3.40, "BM1"), (4.00, 3.10, "BM1"))[1] == V.SLIVER_HELD
    # a one-piece sliver run has no neighbour: HELD
    assert V.end_head((0.002, 3.10, "BM1"), None)[1] == V.SLIVER_HELD


def test_unknown_kind_end_is_held_never_zero():
    js = V3.end_junctions_v3("R9", ["WEIRD"], [COL, V3.EndResult("NO_COLUMN", None, 0.0, None, None, False)])
    assert [j["state"] for j in js] == ["HELD"]
    t = V.tie_record(js[0]["state"], js[0]["held"], *course(0.20), 3.10, ())
    assert t["state"] == "HELD" and t["ties"] is None and "not mapped" in t["held"]


def test_partial_column_end_is_held():
    pr = V3.EndResult("PARTIAL_COLUMN", 0.0, 0.13, 0.0195, 0, None, "column meets 0.0195 m of the 0.150 m thickness")
    js = V3.end_junctions_v3("R8", ["BEAM"], [pr, V3.EndResult("NO_COLUMN", None, 0.0, None, None, False)])
    t = V.tie_record(js[0]["state"], js[0]["held"], *course(0.20), 3.10)
    assert t["state"] == "HELD" and "0.0195" in t["held"]


def test_mirrored_run_gives_the_same_junctions_and_quantities():
    a = V3.end_junctions_v3("R1", ["COLUMN", "BEAM"], [IN_RUN, COL])
    b = V3.end_junctions_v3("R1r", ["BEAM", "COLUMN"], [COL, IN_RUN])
    assert sorted(j["class"] for j in a) == ["BEAM-END_COLUMN", "COLUMN-BEAM"]
    assert sorted(j["class"] for j in b) == ["BEAM-COLUMN", "BEAM-END_COLUMN"]
    ta = sum(t["ties"] for t in ties_for(a, 0.20, [3.10, 3.10]))
    tb = sum(t["ties"] for t in ties_for(b, 0.20, [3.10, 3.10]))
    assert ta == tb == 10
    va = V.end_vjoint(INT, 3.10, FFL)
    vb = V.end_vjoint(list(reversed(INT)), 3.10, FFL)
    assert sorted((x["owner_m"], x["drawing_m"]) for x in va) == sorted((x["owner_m"], x["drawing_m"]) for x in vb)


def test_duplicate_junction_refused():
    r = {"wall_id": "W1", "column_at": "K2", "face": "column_start"}
    with pytest.raises(V.LedgerV2Error):
        V.merge_population([r], [dict(r)])


def test_gap_beyond_a_joint_or_moved_length_refused():
    with pytest.raises(V.LedgerV2Error):
        V.end_strip_delta(0.0, 0.015, 0.010)
    with pytest.raises(V.LedgerV2Error):
        V.end_strip_delta(0.02, 0.0, 0.010)
    with pytest.raises(V.LedgerV2Error):
        V.end_strip_delta(None, 0.0, 0.010)


def test_015_never_takes_the_020_module_and_white_is_held():
    c, held = course(0.15)
    assert c is None and "0.15 m black" in held
    c, held = course(0.20, "WHITE")
    assert c is None and held == V.WHITE_HELD
    c, held = course(0.20)
    assert abs(c.module - 0.200) < 1e-12


def test_millimetres_refused():
    with pytest.raises(BM.ModuleError):
        course(150)
    c, _ = course(0.20)
    with pytest.raises(V.LedgerV2Error):
        V.levels(c, 3100)
    with pytest.raises(V.LedgerV2Error):
        V.course(190, 10, "x", "y")


def test_held_record_carrying_a_number_refused():
    with pytest.raises(V.LedgerV2Error):
        V.no_zero_held([{"wall_id": "W2", "state": "HELD", "ties": 0}], ("ties",))


def test_vjoint_unknown_band_or_top_held():
    v = V.end_vjoint([V.FinishedSide("INT", "PLASTER", None, None), V.FinishedSide("EXT", "NONE", None, None)], 3.10, FFL)
    assert [(x["side"], x["state"], x["owner_m"]) for x in v] == [("INT", "HELD", None)]
    v = V.end_vjoint(INT, None, FFL)
    assert all(x["state"] == "HELD" and x["drawing_m"] is None for x in v)


def test_three_line_families_separate_units():
    fam = V.line_families()
    assert [(f["proposed_code"], f["unit"]) for f in fam] == [("MAS.TIE.SHARMAT", "pcs"), ("MAS.MESH.BED_JOINT", "m.l"),
                                                              ("MAS.MESH.JOINT", "m.l")]
    assert len({f["family"] for f in fam}) == 3 and all(f["owner_trade"] and f["status"] for f in fam)
