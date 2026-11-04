"""T-480: the development-villa inputs (research/agents_t480/t480_inputs.py, read from the sha-pinned merged T-476 census
and reader binding; no private file needed) reproduce the merged census by recomputation (B7-09 33.31882 lm drawing-
confirmed, the Checker's own MS2-L 3.782209 lm); the hub names ARCH_TAKEOFF_V3.0.54, runs it after the V3.0.53 step and
refuses it without its inputs (no data needed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t480"))

import t480_inputs as T  # noqa: E402
from engine.source import arch_v3053 as A53  # noqa: E402
from engine.source import arch_v3054 as A  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402


@pytest.fixture(scope="module")
def d():
    return A.load_inputs(T.build("p"), "p")


def runs(d):
    return {r["run"]: r for r in d["_runs"]}


def pieces(d):
    return {p["piece_id"]: p for r in d["_runs"] for p in r["_pieces"]}


def test_run_actions_and_figures(d):
    r = runs(d)
    assert {k: v["action"] for k, v in r.items()} == {"RL-05": "CONFIRM", "RL-06": "CONFIRM", "RL-07": "VALUE",
                                                      "RL-08": "CONFIRM", "RL-09": "KEEP", "RL-11": "KEEP"}
    assert r["RL-07"]["_L"] == 15.953174                    # 3.088690 + 3.775066 + 3.782209 x 2 + 0.200 + 1.325
    assert r["RL-05"]["_L"] == 16.323713 and r["RL-08"]["_L"] == 1.041933 and r["RL-06"]["_L"] == 2.4
    b709 = round(sum(r[k]["_L"] for k in ("RL-05", "RL-07", "RL-08")), 6)
    assert b709 == 33.31882                                 # T-476 summary family_totals_census B7-09 confirmed_lm


def test_checker_own_ms2_l_recomputed(d):
    """Verifier 2026-11-02 18:40: 11 goings x 0.300 = 3.300 plan, 11 x 0.168 = 1.848 rise, hypot = 3.782209 lm"""
    p = pieces(d)["ST-01:MS2-L"]
    assert (p["_plan"], p["_rise"], p["_L"], p["_recomputed"]) == (3.3, 1.848, 3.782209, True)
    assert A.pitch_length("INCLINED", 3.3, 1.848) == 3.782209


def test_held_turns_and_unknown_band_named(d):
    p = pieces(d)
    assert p["ST-01:T-MS1-N"]["status"] == "HELD" and p["ST-01:T-MS2-LD"]["status"] == "HELD"
    assert [x["piece_id"] for x in d["_unknowns"]] == ["ST-01b:GF east-lane band beyond D1"]
    assert d["_unknowns"][0]["floor"] == "GF"
    assert len(d["_no_rail"]) == 7                          # wall sides with no rail drawn: no line


def test_curved_flight_per_going_bounded_not_recomputed(d):
    p = pieces(d)["ST-02:RS-C:inner (void)"]          # RS-C has an UNKNOWN outer side too
    assert p["_recomputed"] is False and p["_L"] == 3.228281
    assert A.pitch_length("INCLINED", p["_plan"], p["_rise"]) <= p["_L"] <= p["_plan"] + p["_rise"]


def test_fourteen_reader_lines_retired_to_runs(d):
    assert len(d["_retire"]) == 14
    homes = {h for r in d["_retire"] for h in r["homes"]}
    assert homes == {"RL-05", "RL-06", "RL-07", "RL-08", "RL-09"}
    assert len({r["physical_flight"] for r in d["_retire"]}) == 9   # 9 physical flights read by the reader (T-476)


def test_edited_input_refused(monkeypatch):
    monkeypatch.setitem(T.PINS, T.CENSUS, "0" * 64)
    with pytest.raises(SystemExit, match="sha256"):
        T.build()


FLAGS = [x for n in list(range(302, 310)) + list(range(3010, 3049)) for x in (f"--v{n}-inputs", "x.json")]


def _exit(argv, tmp_path):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + FLAGS
               + ["--v3050-inputs", "y.json", "--v3051-inputs", "z.json", "--v3053-inputs", "w.json"])
    return str(e.value.code)


def test_v3054_needs_its_inputs(tmp_path):
    assert "--v3054-inputs and --method ARCH_TAKEOFF_V3.0.54 go together" in _exit(["--method", A.METHOD], tmp_path)


def test_v3054_inputs_refused_on_v3053(tmp_path):
    assert "go together" in _exit(["--method", A53.METHOD, "--v3054-inputs", "a.json"], tmp_path)


def test_hub_chains_v3054_after_v3053():
    src = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
    i53, i54 = src.index("A3053.write("), src.index("A3054.write(")
    assert i53 < i54 and "l3053 = A3053.integrate(l3051, ch_v53, fl24)[0]" in src
    assert '("ARCH_TAKEOFF_V3.0.54",)' in src
    assert src.index('a.method = "ARCH_TAKEOFF_V3.0.53" if a.v3054') < src.index(
        'a.method = "ARCH_TAKEOFF_V3.0.51" if a.v3053') < src.index("v3044 = a.method in (")
