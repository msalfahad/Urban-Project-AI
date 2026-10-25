"""T-285: one established blockwork register revision (rule R-T285-1, research/agents_t285/register_v3.py).

Fixture villa R (NOT Alsenan), storey 3.60 m, slab t 0.15 -> block under a slab 3.45 m; hand truth:
  R-W1 0.20 black, census 5.000 m between column faces; exact pieces slab 2.200 (3.45) + B1 30x60 0.300 (3.00) + slab
       2.500 (3.45) -> gross 4.700 x 3.45 + 0.300 x 3.00 = 16.215 + 0.900 = 17.115 m2; window W1 (schedule 0.90 x 1.20)
       drawn gap -0.04 .. 0.86 m from the column face (its jamb 0.04 m INSIDE the column cut from the length) -> part in
       the masonry 0.86 x 1.20 = 1.032 m2 (never 1.080) -> net 16.083 m2.
       register v2 (sampled with a 0.03 m halo each side of B1): slab 2.17 + B1 0.36 + slab 2.47 -> 17.088 - 1.080 =
       16.008; causes +0.027 (pieces) +0.048 (jamb) = +0.075.
  R-W2 0.15 white, census 3.000 m crossed square by B2 (schedule W 20 H 50, drawn 0.25): drawn reading slab 1.375 + B2
       0.250 (3.10) + slab 1.375 = 2.750 x 3.45 + 0.250 x 3.10 = 10.2625 m2; schedule reading (the face over the wall
       moves): 2.800 x 3.45 + 0.200 x 3.10 = 10.2800 m2 -> established 10.2625 (in every reading) + CONFLICT 0.0175
       (= 0.05 x 0.35) by name, never added, none chosen. register v2 (B2 sampled 0.31): 2.69 x 3.45 + 0.31 x 3.10 =
       10.2415; cause +0.0210.
  R-W3 0.20 white, census 4.000 m under the slab: Checker VERIFIED 13.800 m2 (4.000 x 3.45); a later layer proposes
       13.795 (lower class) -> 13.800 kept, -0.005 listed; an explicit replace is refused.
  register: v2 40.0495 -> v3 40.1455 m2 = +0.0960 = 0.027 + 0.048 + 0.021, residual 0.
Adverse: a piece list not summing to the census (B1 at a wrong 0.25) refused; pieces sampled long (5.05 m) refused;
  millimetres refused; a VERIFIED value replaced by a lower class refused; a CONFLICT collapsed to one reading refused;
  a held item written as 0 / unnamed refused; an established wall written as 0 refused; a register move with an unnamed
  cause refused; a wall carried twice refused; mirror gives the same figures.
Alsenan (development villa, research/agents_t285): outputs reproduce; register v2 449.260 -> basis A 449.5934 (T-274
  449.5651 + GF-W22 +0.0101 + GF-W34 +0.0182) -> basis B 625.8957 (+ T-261 r3 176.3023); VERIFIED 106.004 on 13 walls at
  the Checker's values; every CONFLICT wall carries >= 2 readings; HELD walls carry no number and no 0.
"""
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/agents_t285"
sys.path.insert(0, str(HERE))
import register_v3 as R3  # noqa: E402
import piece_close as PC  # noqa: E402  (research/agents_t274, put on the path by register_v3)

H_SLAB, H_B1, H_B2 = 3.45, 3.00, 3.10


def slab(L):
    return {"length_m": L, "height_m": H_SLAB, "kind": "SLAB"}


def beam(L, h):
    return {"length_m": L, "height_m": h, "kind": "BEAM"}


# ---------------------------------------------------------------- villa R, normal cases
def test_rw1_exact_pieces_and_jamb_inside_column():
    ded = PC.opening_in_masonry(-0.04, 0.86, (0.0, 5.0)) * 1.20
    assert ded == pytest.approx(1.032, abs=1e-9)
    w = R3.wall_from_pieces(5.000, [slab(2.200), beam(0.300, H_B1), slab(2.500)], ded)
    assert w["established_gross_m2"] == pytest.approx(17.115, abs=1e-9)
    assert w["established_net_m2"] == pytest.approx(16.083, abs=1e-9)
    assert w["held"] == []


def test_rw1_mirror_same_figures():
    ded = PC.opening_in_masonry(4.14, 5.04, (0.0, 5.0)) * 1.20      # mirrored: jamb inside the far column
    w = R3.wall_from_pieces(5.000, [slab(2.500), beam(0.300, H_B1), slab(2.200)], ded)
    assert w["established_net_m2"] == pytest.approx(16.083, abs=1e-9)


def test_rw2_conflict_both_readings_kept():
    drawn = R3.wall_from_pieces(3.000, [slab(1.375), beam(0.250, H_B2), slab(1.375)])["established_net_m2"]
    sched = R3.wall_from_pieces(3.000, [slab(1.400), beam(0.200, H_B2), slab(1.400)])["established_net_m2"]
    assert drawn == pytest.approx(10.2625, abs=1e-9) and sched == pytest.approx(10.2800, abs=1e-9)
    est, inc, rd = R3.conflict_part({"drawn 0.25": drawn, "schedule 0.20": sched})
    assert est == pytest.approx(10.2625, abs=1e-9)
    assert inc == pytest.approx(0.0175, abs=1e-9) == pytest.approx(0.05 * (H_SLAB - H_B2), abs=1e-9)
    assert set(rd) == {"drawn 0.25", "schedule 0.20"}                # both carried, none chosen


def test_rw3_verified_kept_lower_class_listed():
    kept, diff = R3.apply_value({"value": 13.800, "class": R3.VERIFIED, "source": "Checker"},
                                {"value": 13.795, "class": R3.SS, "source": "later layer"})
    assert kept["value"] == 13.800 and kept["class"] == R3.VERIFIED
    assert diff["delta_m2"] == pytest.approx(-0.005, abs=1e-9)


def test_villa_r_register_reconciles_to_named_causes():
    v2 = 16.008 + 10.2415 + 13.800
    v3 = 16.083 + 10.2625 + 13.800
    causes = [{"wall_id": "R-W1", "cause": "exact pieces", "delta_m2": 0.027},
              {"wall_id": "R-W1", "cause": "jamb part in masonry", "delta_m2": 0.048},
              {"wall_id": "R-W2", "cause": "exact pieces", "delta_m2": 0.021}]
    assert v3 - v2 == pytest.approx(0.096, abs=1e-9)
    assert R3.reconcile(v2, v3, causes) == 0.0


def test_held_piece_named_never_zero():
    w = R3.wall_from_pieces(5.000, [slab(2.200), {"length_m": 0.300, "height_m": None, "held_item": "B1 depth not "
                                                  "printed"}, slab(2.500)])
    assert w["established_gross_m2"] == pytest.approx(4.700 * H_SLAB, abs=1e-9)
    assert w["held"][0]["held_item"].startswith("B1 depth") and w["held"][0]["figure_not_a_quantity"] == "0.3000 m"


# ---------------------------------------------------------------- villa R, adverse cases
def test_adverse_piece_list_not_closing_refused():
    with pytest.raises(PC.PieceError, match="NOT_CLOSED"):
        R3.wall_from_pieces(5.000, [slab(2.200), beam(0.250, H_B1), slab(2.500)])


def test_adverse_sampled_pieces_over_census_refused():
    with pytest.raises(PC.PieceError, match="OVER_CENSUS"):
        R3.wall_from_pieces(5.000, [slab(2.200), beam(0.360, H_B1), slab(2.490)])


def test_adverse_millimetres_refused():
    with pytest.raises(PC.PieceError, match="OVER_CENSUS"):
        R3.wall_from_pieces(5.000, [slab(2200), beam(300, H_B1), slab(2500)])


def test_adverse_verified_overwrite_refused():
    with pytest.raises(R3.RegisterError, match="VERIFIED_OVERWRITE"):
        R3.apply_value({"value": 13.800, "class": R3.VERIFIED}, {"value": 13.795, "class": R3.SS}, replace=True)


def test_adverse_conflict_collapsed_refused():
    with pytest.raises(R3.RegisterError, match="CONFLICT_COLLAPSED"):
        R3.conflict_part({"drawn 0.25": 10.2625})
    with pytest.raises(R3.RegisterError, match="CONFLICT_UNNAMED"):
        R3.conflict_part({"": 10.2625, "schedule 0.20": 10.28})


def test_adverse_held_as_zero_or_unnamed_refused():
    with pytest.raises(R3.RegisterError, match="HELD_AS_ZERO"):
        R3.held_item("B1 depth not printed", 0)
    with pytest.raises(R3.RegisterError, match="HELD_UNNAMED"):
        R3.held_item("  ")
    with pytest.raises(R3.RegisterError, match="HELD_AS_NUMBER"):
        R3.apply_value({"value": 1.0, "class": R3.SS}, {"value": 0.0, "class": R3.HELD})


def test_adverse_established_zero_refused():
    with pytest.raises(R3.RegisterError, match="MISSING_AS_ZERO"):
        R3.apply_value({"value": 1.0, "class": R3.SS}, {"value": 0.0, "class": R3.SS})


def test_adverse_unnamed_or_duplicate_cause_refused():
    with pytest.raises(R3.RegisterError, match="RESIDUAL"):
        R3.reconcile(40.0495, 40.1455, [{"wall_id": "R-W1", "cause": "exact pieces", "delta_m2": 0.027}])
    with pytest.raises(R3.RegisterError, match="UNNAMED_CAUSE"):
        R3.reconcile(1.0, 1.1, [{"wall_id": "R-W1", "cause": "", "delta_m2": 0.1}])
    with pytest.raises(R3.RegisterError, match="DUPLICATE_CAUSE"):
        R3.reconcile(1.0, 1.2, [{"wall_id": "R-W1", "cause": "x", "delta_m2": 0.1},
                                {"wall_id": "R-W1", "cause": "x", "delta_m2": 0.1}])


def test_adverse_wall_twice_refused():
    with pytest.raises(R3.RegisterError, match="DUPLICATE_WALL"):
        R3.one_wall_once([{"wall_id": "R-W1"}, {"wall_id": "R-W1"}])


# ---------------------------------------------------------------- Alsenan (development villa)
def _reg():
    return list(csv.DictReader(open(HERE / "BLOCKWORK_WALL_REGISTER_V3.csv", encoding="utf-8")))


def _summ():
    return json.loads((HERE / "summary.json").read_text(encoding="utf-8"))


def test_alsenan_outputs_reproduce():
    r = subprocess.run([sys.executable, "-I", str(HERE / "build_t285.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_alsenan_register_totals_and_residual():
    s = _summ()
    t274 = json.loads((ROOT / "research/agents_t274/summary.json").read_text())
    t261 = json.loads((ROOT / "research/agents_t261/summary.json").read_text())
    assert s["register_v2_net_m2"] == pytest.approx(449.260, abs=1e-9)
    assert s["basis_A"]["net_m2"] == pytest.approx(t274["established_net_after_m2"] + 0.0101 + 0.0182, abs=1e-4)
    assert s["basis_B"]["net_m2"] == pytest.approx(s["basis_A"]["net_m2"] + t261["split_established_added_m2"], abs=1e-4)
    assert s["residual_A_m2"] == 0.0 and s["residual_B_m2"] == 0.0
    for b in ("basis_A", "basis_B"):
        assert sum(s[b]["by_class_m2"].values()) == pytest.approx(s[b]["net_m2"], abs=1e-4)


def test_alsenan_verified_walls_at_checker_values():
    ver = {r["wall_id"]: float(r["net_m2"]) for r in csv.DictReader(open(HERE / "CHECKER_VERIFIED.csv"))}
    reg = {r["wall_id"]: r for r in _reg()}
    assert len(ver) == 13
    for w, v in ver.items():
        assert reg[w]["net_class_v3"] == R3.VERIFIED and float(reg[w]["net_m2_v3"]) == pytest.approx(v, abs=1e-9)
        assert reg[w]["verified_by"]
    assert {w for w, r in reg.items() if r["net_class_v3"] == R3.VERIFIED} == set(ver)
    assert _summ()["verified_net_m2"] == pytest.approx(106.004, abs=1e-9) == pytest.approx(sum(ver.values()), abs=1e-9)


def test_alsenan_named_walls():
    reg = {r["wall_id"]: r for r in _reg()}
    for w, v in {"1F-W00": 12.9336, "1F-W20": 24.5068, "1F-W22": 20.4010, "GF-W28": 20.1384, "GF-W22": 12.9311,
                 "GF-W34": 10.3982, "1F-W18": 19.7326}.items():
        assert float(reg[w]["net_m2_v3"]) == pytest.approx(v, abs=1e-9), w
    assert float(reg["1F-W00"]["deductions_m2_v3"]) == pytest.approx(9.806 - 0.0706, abs=1e-9)


def test_alsenan_conflicts_carry_both_readings():
    reg = _reg()
    conf = [r for r in reg if r["conflict"]]
    assert {r["wall_id"] for r in conf} == {"GF-W19", "GF-W20", "GF-W22", "GF-W34", "1F-W16", "1F-W11"}
    for r in conf:
        assert r["conflict"].count("drawn width") == 1 and "schedule width" in r["conflict"]
        assert float(r["conflict_increment_m2"]) > 0
        if r["net_m2_v3"]:
            vals = [float(x) for x in re.findall(r"width [0-9.|]+(?: \(face \w+\))? ([0-9]+\.[0-9]{4})", r["conflict"])]
            assert float(r["net_m2_v3"]) == pytest.approx(min(vals) - float(r["deductions_m2_v3"]), abs=1e-9)


def test_alsenan_held_never_zero_and_each_wall_once():
    reg = _reg()
    R3.one_wall_once(reg)
    assert len(reg) == 76
    for r in reg:
        if r["net_class_v3"] == R3.HELD:
            assert r["net_m2_v3"] == "" and r["held_items"]
            assert r["gross_figure_not_a_quantity"] not in ("0", "0.0", "0.0000")
        else:
            assert float(r["net_m2_v3"]) > 0
        if r["completeness"] == "ESTABLISHED_PART_PLUS_HELD":
            assert r["held_items"]


def test_alsenan_export_matches_register():
    ex = json.loads((HERE / "REGISTER_V3_EXPORT.json").read_text(encoding="utf-8"))
    s = _summ()
    assert ex["register_sha256"] == s["register_sha256"] and len(ex["records"]) == 76
    tot = sum(r["net_m2"] for r in ex["records"] if r["net_m2"] is not None)
    assert tot == pytest.approx(s["basis_B"]["net_m2"], abs=1e-4)
    assert all(r["net_m2"] is None for r in ex["records"] if r["state"] == "HELD")


def test_alsenan_no_coordinates_in_outputs():
    for p in HERE.glob("*.csv"):
        assert not re.search(r"\b\d{4,}\.\d+", p.read_text(encoding="utf-8")), p.name
    assert not re.search(r"\b\d{4,}\.\d+", (HERE / "REGISTER_V3_EXPORT.json").read_text(encoding="utf-8"))
