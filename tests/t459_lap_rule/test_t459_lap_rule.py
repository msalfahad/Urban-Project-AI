"""T-459 REBAR_LAP_RULE_V2: lap length by element class (owner 40 d columns / 60 d beams-slabs-footings, drawing
first) + the lap-aware count, against the frozen route G form. Synthetic villa K459 (not the development villa): a
30.00 m ground beam, a 23.80 m and a 35.00 m beam run, column storeys of 4.50 m and 11.50 m, with hand values; adverse
cases (units, missing diameter, unknown class, minimum-only note, unprinted zone, lap >= stock, drawing note vs owner
convention); the committed census outputs. Nothing here writes outside tmp_path."""
import ast
import importlib.util
import json
from pathlib import Path

import pytest

from engine.source import continuous_beams as CBM
from engine.source import rebar_lap_rule_v2 as V
from engine.source import rebar_laps_v1 as RL

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/agents_t459"
KGM = lambda d: d * d / 162.0          # noqa: E731  route G unit mass (bar_shapes)


def _census():
    spec = importlib.util.spec_from_file_location("t459_census", HERE / "t459_census.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ hand fixture K459
def test_30m_ground_beam_hand_count():
    # 4 T16 bottom bars, 30.00 m continuous, stock 12 m, owner 60 d = 0.96 m:
    # laps = ceil((30 - 12) / (12 - 0.96)) = ceil(18 / 11.04) = ceil(1.630) = 2; bar = 30 + 2 x 0.96 = 31.92 m
    r = V.bar_with_laps("30.00", 16, "GROUND_BEAM")
    assert (r["laps"], r["lap_m"], r["length_m"], r["state"]) == (2, 0.96, 31.92, V.PROVISIONAL)
    assert 4 * r["length_m"] * KGM(16) == pytest.approx(201.765926, abs=1e-6)       # 4 x 31.92 x 256 / 162
    # route G before: same count here, but the 50 d base lap: 30 + 2 x 0.80 = 31.60 m (-0.32 m per bar)
    assert V.frozen_route_g(30.0, 16, 50) == pytest.approx(31.60)
    assert V.frozen_route_g(30.0, 16, 60) == pytest.approx(31.92)


def test_count_defect_windows_23_8_and_35():
    # 23.80 m T12 beam, 60 d = 0.72 m: owner ceil(11.8 / 11.28) = 2 -> 25.24 m; frozen ceil(23.8 / 12) - 1 = 1 -> 24.52
    r = V.bar_with_laps("23.80", 12, "BEAM")
    assert (r["laps"], r["length_m"]) == (2, pytest.approx(25.24))
    assert CBM._with_laps(23.8, 12, 60, 12.0) == pytest.approx(24.52)               # the frozen code, unedited
    # 35.00 m T16 beam, 0.96 m: owner ceil(23 / 11.04) = 3 -> 37.88 m; frozen 2 -> 36.92 m
    r = V.bar_with_laps("35.00", 16, "CONTINUOUS_BEAM")
    assert (r["laps"], r["length_m"]) == (3, pytest.approx(37.88))
    assert CBM._with_laps(35.0, 16, 60, 12.0) == pytest.approx(36.92)


@pytest.mark.parametrize("run,laps", [("12.00", 0), ("12.01", 1), ("22.80", 1), ("22.81", 2)])
def test_owner_boundaries_1_2m_lap(run, laps):
    # owner s.6.3: 12 m stock, 1.2 m lap (60 d x 20 mm); from decimal text and from mm integers
    assert V.bar_with_laps(run, 20, "BEAM")["laps"] == laps
    mm = int(round(float(run) * 1000))
    assert V.bar_with_laps(mm, 20, "BEAM", stock=12000, unit="mm")["laps"] == laps


def test_column_storey_lap_40d():
    # 4.50 m storey, T16: 4.50 + 40 x 0.016 = 5.14 m, one storey lap
    r = V.storey_bar("4.50", 16)
    assert (r["laps"], r["lap_m"], r["length_m"]) == (1, 0.64, pytest.approx(5.14))
    # adverse: 11.50 m storey, T20 (0.80 m): 12.30 m > 12 -> one more splice: 11.5 + 0.8 + 0.8 = 13.10 m, 2 laps
    r = V.storey_bar("11.50", 20)
    assert (r["laps"], r["length_m"]) == (2, pytest.approx(13.10))


# ------------------------------------------------------------------ adverse
def test_units_mm_equals_m_and_cm_refused():
    a = V.bar_with_laps("23.80", 12, "BEAM")
    b = V.bar_with_laps(23800, 12, "BEAM", stock=12000, unit="mm")
    assert (a["laps"], a["length_m"]) == (b["laps"], b["length_m"])
    with pytest.raises(RL.LapError):
        V.bar_with_laps(2380, 12, "BEAM", unit="cm")
    with pytest.raises(RL.LapError):
        V.bar_with_laps("-1", 12, "BEAM")


def test_missing_diameter_held_never_zero():
    r = V.bar_with_laps("30.00", None, "BEAM")
    assert r["state"] == V.HELD and r["length_m"] is None and r["laps"] is None
    # a run within the stock needs no lap at all: NOT_REQUIRED even when the diameter is missing
    r = V.bar_with_laps("8.48", None, "BEAM")
    assert (r["state"], r["laps"], r["length_m"]) == (V.NOT_REQUIRED, 0, 8.48)
    r = V.storey_bar("4.50", None)
    assert r["state"] == V.HELD and r["length_m"] is None


def test_unknown_class_held():
    r = V.bar_with_laps("23.80", 12, "LINTEL")
    assert r["state"] == V.HELD and r["length_m"] is None and r["element_class"] is None
    assert V.route_g_triple_v2("LINTEL") is None


def test_drawing_note_governs_over_owner_convention():
    note = {"tier": RL.NOTE, "lap_d": 40, "kind": RL.EXACT, "governs": True, "ref": "synthetic note 1: lap 40 x DIA",
            "category": RL.LAP_CAT}
    r = V.bar_with_laps("23.80", 10, "SLAB", authorities=[note])
    assert (r["state"], r["lap_m"]) == (V.DRAWING_CONFIRMED, 0.4)              # 40 d, not the owner 60 d
    assert r["ref"] == note["ref"] and any("owner convention 60 d not applied" in f for f in r["findings"])
    assert (r["laps"], r["length_m"]) == (2, pytest.approx(24.60))            # ceil(11.8 / 11.6) = 2


def test_minimum_only_and_zone_not_printed_held():
    mini = {"tier": RL.NOTE, "lap_d": 70, "kind": RL.MINIMUM, "governs": True, "ref": "not less than 70 d",
            "category": RL.LAP_CAT}
    r = V.bar_with_laps("23.80", 16, "BEAM", authorities=[mini])
    assert r["state"] == V.HELD and r["length_m"] is None and r["lap_min_m"] == pytest.approx(1.12)
    zone = {"tier": RL.NOTE, "tension_d": 70, "compression_d": 40, "governs": True, "ref": "zones",
            "category": RL.LAP_CAT}
    r = V.bar_with_laps("23.80", 16, "BEAM", authorities=[zone])
    assert r["state"] == V.HELD and r["length_m"] is None


def test_anchorage_source_never_a_lap():
    anch = {"tier": RL.NOTE, "lap_d": 70, "kind": RL.EXACT, "governs": True, "ref": "starter anchorage",
            "category": RL.ANCHORAGE_CAT}
    r = V.bar_with_laps("23.80", 16, "BEAM", authorities=[anch])
    assert r["lap_m"] == 0.96 and r["state"] == V.PROVISIONAL                 # owner class, the anchorage ignored


def test_lap_not_shorter_than_stock_blocked():
    r = V.bar_with_laps("30.00", 250, "BEAM")                                  # 60 x 0.25 = 15 m >= 12 m
    assert r["state"] == V.BLOCKED and r["length_m"] is None


def test_route_g_triples():
    assert V.route_g_triple_v2("COLUMNS") == (40.0, 40.0, 40.0)
    assert V.route_g_triple_v2("CONTINUOUS_BEAM") == (60.0, 60.0, 60.0)
    assert V.route_g_triple_v2("FOOTING") == (60.0, 60.0, 60.0)


def test_unwired_and_policy_digest_stable():
    for d in ("engine", "tools"):
        for p in (ROOT / d).rglob("*.py"):
            if p.name == "rebar_lap_rule_v2.py":
                continue
            tree = ast.parse(p.read_text(encoding="utf-8"))
            names = [a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names]
            assert "rebar_lap_rule_v2" not in names, p
    assert V.policy_record()["digest"] == V.policy_record()["digest"]


# ------------------------------------------------------------------ committed census
def test_route_g_census_committed():
    s = json.loads((HERE / "T459_ROUTE_G_RUN.json").read_text(encoding="utf-8"))
    bl = s["bar_length_census"]
    assert bl["bars_over_stock_12m"] == 0 and bl["cb_runs_over_stock"] == 0
    assert bl["cb_lengths_that_change_by_count_or_lap"] == 0 and bl["longest_bar_m"] < 12.0
    assert s["families_changed"] == ["COLUMNS"]
    fam = s["by_family_storey"]
    assert sum(v["delta_base_kg"] for v in fam.values()) == pytest.approx(s["totals_kg"]["delta_base"], abs=1e-5)
    assert all(v["delta_base_kg"] == 0 for k, v in fam.items() if not k.startswith("COLUMNS|"))
    # the low reading was already 40 d: unchanged
    assert s["totals_kg"]["before_low"] == s["totals_kg"]["after_low"]


def test_candidate_binding_rebuilds():
    mod = _census()
    committed = json.loads((HERE / "T459_CANDIDATE_BINDING.json").read_text(encoding="utf-8"))
    rebuilt = mod.candidate_binding()
    assert rebuilt == committed
    assert committed["lap_convention_lines_with_quantity"] == 0
    assert committed["later_steps_touching"] == []
