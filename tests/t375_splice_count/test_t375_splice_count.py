"""T-375 splice count of a run longer than stock: the frozen continuous_beams._with_laps form (n = ceil(L / S) - 1)
against the proposed pieces form N = ceil((L - lap) / (S - lap)) (= CONTINUOUS_BEAM_LAPS_V2, T-273). Synthetic villa
K375 (not the development villa) with hand values, boundary and adverse cases, the frozen code itself (imported, never
edited), the caller census and the committed outputs. Nothing here writes outside tmp_path."""
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


T = _load("t375", "research/agents_t375/t375_splice_count.py")
S = Fraction(12)


# ---------------------------------------------------------------- K375 hand fixture (three bar populations, S = 12 m)
# GB-K1 ground-beam bottom 6 ø12, run 23.80 m, lap 40 d = 0.48 m (a printed 40 d in this fixture)
#   correct: (23.80 - 0.48) / (12 - 0.48) = 23.32 / 11.52 = 2.0243 -> 3 pieces, 2 laps; 3 x 12 - 2 x 0.48 = 35.04 >= 23.80
#   frozen : ceil(23.80 / 12) - 1 = 1 lap, 2 pieces cover 2 x 12 - 0.48 = 23.52 < 23.80 (0.28 m of run uncovered)
#   per bar +0.48 m; ø12 = 144 / 162 = 0.888889 kg/m -> +0.426667 kg/bar, x 6 = +2.560000 kg
# SL-K2 slab bars 10 ø16, run 35.00 m, lap 40 d = 0.64 m
#   correct: (35 - 0.64) / 11.36 = 3.0246 -> 4 pieces, 3 laps; frozen ceil(35 / 12) - 1 = 2 laps (3 pieces cover 34.72)
#   per bar +0.64 m x 256 / 162 = +1.011358 kg/bar, x 10 = +10.113580 kg
# BM-K3 beam top 4 ø14, run 20.00 m, lap 60 d = 0.84 m: (20 - 0.84) / 11.16 = 1.717 -> 2 pieces, 1 lap; frozen 1: AGREE
K375 = [("GB-K1", 6, 12, "23.80", "0.48", 3, 2, 1, Fraction("2.56")),
        ("SL-K2", 10, 16, "35.00", "0.64", 4, 3, 2, Fraction(10) * Fraction("0.64") * 256 / 162),
        ("BM-K3", 4, 14, "20.00", "0.84", 2, 1, 1, Fraction(0))]


@pytest.mark.parametrize("pid,bars,d,L,lap,n_pieces,n_laps,n_frozen,dkg", K375)
def test_k375_hand_values(pid, bars, d, L, lap, n_pieces, n_laps, n_frozen, dkg):
    assert T.pieces(L, lap) == n_pieces
    assert T.laps(L, lap) == n_laps
    assert T.frozen_laps(L) == n_frozen
    assert T.covers(L, lap, S, n_pieces) and not T.covers(L, lap, S, n_pieces - 1)
    delta_kg = bars * Fraction(d * d, 162) * (T.procurement_length(L, lap) - T.frozen_length(L, lap))
    assert delta_kg == dkg


def test_k375_totals_by_hand():
    tot = sum(r[1] * Fraction(r[2] ** 2, 162) * (T.procurement_length(r[3], r[4]) - T.frozen_length(r[3], r[4]))
              for r in K375)
    assert float(tot) == pytest.approx(2.56 + 10.113580247, abs=1e-6)


# ---------------------------------------------------------------- normal cases (frozen and proposed agree)
@pytest.mark.parametrize("L,lap", [("11.9", "0.48"), ("12", "0.84"), ("12.000", "0.40"), ("20", "0.64"),
                                   ("23.52", "0.48"), ("35", "0.48")])
def test_normal_frozen_right(L, lap):
    assert T.laps(L, lap) == T.frozen_laps(L)
    assert T.procurement_length(L, lap) == T.frozen_length(L, lap)


def test_run_below_stock_no_splice_for_any_lap():
    for lap in ("0", "0.4", "5", "11.99"):
        assert T.laps("11.9", lap) == 0 and T.pieces("11.9", lap) == 1
    assert T.laps("11.9", None) == 0                           # within the stock the lap value is not needed


# ---------------------------------------------------------------- exact boundary (owner s.6.3 style), units of reading
def test_exact_window_edge_from_text_mm_and_float():
    # L = S + (S - lap) = 23.52 at lap 0.48 -> exactly 1 lap; 1 mm more -> 2
    for v in ("23.52", 23.52, T.q("23520") / 1000):
        assert T.laps(v, "0.48") == 1
    assert T.laps("23.521", "0.48") == 2
    assert T.frozen_laps("23.521") == 1                        # the frozen form misses it
    assert T.laps("24", "0.48") == 2 and T.frozen_laps("24") == 1   # top of window k = 1
    assert T.laps("24.001", "0.48") == 2 and T.frozen_laps("24.001") == 2


# ---------------------------------------------------------------- adverse cases
def test_adverse_35m_at_064_frozen_refused():
    assert T.pieces("35", "0.64") == 4 and T.laps("35", "0.64") == 3
    assert T.frozen_laps("35") == 2
    assert not T.covers("35", "0.64", S, T.frozen_laps("35") + 1)     # 3 pieces reach 34.72 m only: refused
    assert T.procurement_length("35", "0.64") == Fraction("36.92")
    assert T.frozen_length("35", "0.64") == Fraction("36.28")


def test_adverse_held_lap_never_zero():
    with pytest.raises(T.SpliceError, match="HELD"):
        T.laps("23.8", None)


@pytest.mark.parametrize("lap", ["12", "12.5"])
def test_adverse_lap_not_shorter_than_stock_blocked(lap):
    with pytest.raises(T.SpliceError, match="BLOCKED"):
        T.laps("30", lap)


@pytest.mark.parametrize("bad", ["-1", "abc", float("nan"), True])
def test_adverse_bad_length_refused(bad):
    with pytest.raises(T.SpliceError):
        T.q(bad)


# ---------------------------------------------------------------- the proofs on a grid (P1 - P4)
GRID = [Fraction(n, 100) for n in range(1190, 4801, 7)] + [Fraction(24), Fraction(36), Fraction(48)]
GRID_LAPS = [Fraction(x) for x in ("0.40", "0.48", "0.64", "0.84", "1.2", "3")]


def test_p1_one_formula_with_engine():
    from engine.source import bbs_optimiser as BB
    from engine.source import rebar_laps_v1 as RL
    for L in GRID:
        for lap in GRID_LAPS:
            n = T.laps(L, lap)
            assert n == RL.lap_count_exact(str(float(L)), str(float(lap)), "12")
            assert n == len(BB.split_run(float(L), float(lap), 12.0)) - 1
            if L > S:                                          # identity: ceil((L - lap) / (S - lap)) - 1
                assert n == T._ceil((L - S) / (S - lap)) == T._ceil((L - lap) / (S - lap)) - 1


def test_p2_p3_frozen_is_lower_bound_and_wrong_exactly_on_windows():
    for lap in GRID_LAPS:
        win = T.windows(lap, L_max=Fraction(48))
        for L in GRID:
            nf, nv = T.frozen_laps(L), T.laps(L, lap)
            assert nf <= nv
            inside = any(lo < L <= hi for _, lo, hi in win)
            assert (nf != nv) == inside
            sl = T.safe_lap_max(L)
            assert (nf == nv) == (sl is None or lap <= sl)
            assert nv - nf < T.deficit_bound(L, lap)


def test_frozen_code_itself_matches_the_reproduction():
    from engine.source.continuous_beams import _with_laps          # FROZEN module: imported, never edited
    for L in GRID:
        for d, lap_d in ((12, 40), (16, 40), (14, 60)):
            lap = Fraction(d * lap_d, 1000)
            assert _with_laps(float(L), d, lap_d, 12.0) == pytest.approx(float(T.frozen_length(L, lap)), abs=1e-9)


# ---------------------------------------------------------------- caller census
def test_callers_single_route_path():
    c = T.caller_census()
    wl = [r for r in c["references"] if r["symbol"] == "_with_laps"]
    pb = [r for r in c["references"] if r["symbol"] == "physical_bars"]
    assert [(r["file"], r["in_function"]) for r in wl] == [("engine/source/continuous_beams.py", "physical_bars")]
    assert {(r["file"], r["in_function"]) for r in pb} == {("engine/source/generic_route.py", "_cb_model")}
    for x in c["frozen_form_copies"]:
        assert (x["file"], x["in_function"]) in T.COPY_VERDICTS, x


def test_census_detects_a_new_copy(tmp_path):
    (tmp_path / "engine").mkdir()
    (tmp_path / "engine" / "m.py").write_text(
        "import math\ndef f(L, stock_m):\n    return math.ceil(L / stock_m) - 1\n"
        "def g(L, S):\n    return math.ceil(L / S - 1e-12) - 1\n"
        "def ok(L, lap, S):\n    return math.ceil((L - S) / (S - lap))\n", encoding="utf-8")
    got = T.caller_census(root=tmp_path, dirs=("engine",))["frozen_form_copies"]
    assert [(x["in_function"]) for x in got] == ["f", "g"]


# ---------------------------------------------------------------- committed outputs
def test_committed_outputs_reproduce():
    out = T.build()
    assert (ROOT / "research/agents_t375/T375_BOUNDARY_TABLE.csv").read_text(encoding="utf-8") == out["csv"]
    assert (ROOT / "research/agents_t375/T375_CALLERS.json").read_text(encoding="utf-8") == out["callers"]
    assert (ROOT / "research/agents_t375/T375_CANDIDATE_BINDING.json").read_text(encoding="utf-8") == out["candidate"]
    assert (ROOT / "research/agents_t375/T375_SUMMARY.json").read_text(encoding="utf-8") == out["summary"]


def test_summary_facts():
    s = json.loads((ROOT / "research/agents_t375/T375_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["frozen_ever_above_proposed"] is False
    assert s["max_deficit_laps"] == 1
    assert s["frozen_pieces_short_of_run_when_disagree"] is True
    assert "23.800" in s["disagreements_by_lap"]["0.48"] and "35.000" not in s["disagreements_by_lap"]["0.48"]
    assert "35.000" in s["disagreements_by_lap"]["0.64"]
    c = s["candidate"]
    assert c["cb_lines"] == 105 and c["cb_lines_with_quantity"] == 0 and c["later_steps_touching_cb"] == []
    assert c["route_g_longest_run_m"] <= 12.0 and c["route_g_delta_kg"] == [0.0, 0.0, 0.0]
