"""T-072 membrane purchase table: every expected value below is written by hand from the room sizes and the owner's
rules (roll 1.00 x 10.00 m UP-WP-001, lap 0.10 m UP-WP-002, upturn 0.20 m UP-WP-003); the table itself only reads
the engine's schedule, layout, cutting plan and continuous-fold alternative (none of these values comes from the code
under test). Synthetic rooms only; no client project."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t072_fixtures as X                                            # noqa: E402
from engine.source import membrane_purchase_table as MT              # noqa: E402

DOOR_K = {"id": "D1", "edge": 0, "t0": 1000, "t1": 1900, "depth": 200, "other_side": "DRY"}
A = pytest.approx


def one(a):
    t = MT.from_areas([a], X.plans([a]))
    assert len(t["rows"]) == 1 and not t["held"]
    return t, t["rows"][0]


# ------------------------------------------------------------------------------------------------ owner's kitchen
def test_owner_kitchen_q30_every_number_continuous_fold():
    """owner Q-30: kitchen 3.00 x 4.00 m, one 0.90 m door, roll 1 x 10, lap 0.10, upturn 0.20 folded from the same
    membrane. Hand (his numbers): strips across the 3 m width 0.80 + 0.90 + 0.90 + 0.40 = 3.00 m of floor, the 4th
    strip 0.70 m wide; each strip 4.00 + 0.20 + 0.20 = 4.40 m; cut 3 x 4.40 + 0.70 x 4.40 = 16.28 m2; floor 12.00,
    perimeter 14.00, floor + upturn 14.80; rolls 2 (4 cuts of 4.40 m, two per 10 m roll); offcuts 20 - 16.28 = 3.72."""
    t, r = one(X.area(X.rect(3000, 4000), room_id="K1", name_en="KITCHEN", codes=("KITCHEN",), doors=[DOOR_K]))
    f = r["fold"]
    assert f["state"] == "COMPUTED"
    assert f["direction"] == "ALONG_Y" and f["strips"] == 4                       # strips run the 4 m way
    assert f["last_strip_width_m"] == A(0.70) and f["strip_length_m"] == A(4.40)
    assert f["installed_m2"] == A(3 * 1.00 * 4.40 + 0.70 * 4.40) == A(16.28)       # his "membrane cut"
    assert f["required_m2"] == A(12.00 + 14.00 * 0.20) == A(14.80)                 # his "floor + upturn surface"
    assert f["rolls_if_alone"] == 2
    assert r["fold_gross_offcuts_if_alone_m2"] == A(2 * 10.0 - 16.28) == A(3.72)
    # what the owner's table does not show, the engine does: 3 side laps 3 x 0.10 x 4.40 and 4 corner squares
    assert f["laps_m2"] == A(3 * 0.10 * 4.40) and f["corner_excess_m2"] == A(4 * 0.20 * 0.20)
    assert f["consumed_m2"] == A(4 * 4.40 * 1.00)       # the 4th strip is ripped from a full-width 4.40 m cut
    # the other direction (strips the 3 m way) is reported, never dropped: 5 strips of 3.40 m, 3 rolls
    other = next(x for x in f["alternatives"] if x["direction"] == "ALONG_X")
    assert other["rolls"] == 3 and other["consumed_m2"] == A(5 * 3.40)
    assert f["direction_changes_rolls"] is True
    assert t["systems"][0][MT.FOLD]["rolls_to_buy"] == 2


def test_owner_kitchen_engine_separate_upstand_differs_and_says_where():
    """the engine's own plan (separate upstand band, the V2.5 layout; junction UNRESOLVED N-11). Hand: floor strips
    along the 3 m wall, n = ceil((4.00 - 1.00) / 0.90) + 1 = 5, last 4.00 - 4 x 0.90 = 0.40 m; upturn on the walls
    only (UP-WP-003): 14.00 - 0.90 door = 13.10 lm x 0.20 = 2.62 m2; doorway piece 0.90 x 0.20 = 0.18 m2;
    surface 12.00 + 2.62 + 0.18 = 14.80 m2 (the same 14.80 as the owner: his upturn across the door = the doorway
    piece). Laps: side 4 x 3.00 x 0.10 = 1.20, flange 13.10 x 0.10 = 1.31, band ends 4 x 0.10 x 0.30 = 0.12,
    doorway piece onto the floor 0.90 x 0.10 = 0.09 -> 2.72; installed 14.80 + 2.72 = 17.52 m2 (owner 16.28:
    +1.24 m2, +7.6 %); rolls 2 (same as the owner)."""
    t, r = one(X.area(X.rect(3000, 4000), room_id="K1", codes=("KITCHEN",), doors=[DOOR_K]))
    s = r["strips"]
    assert (s["direction"], s["floor_strips"], s["strip_length_m"], s["last_strip_width_m"]) == ("ALONG_X", 5, 3.0, 0.4)
    assert r["net_m2"] == A(12.0) and r["upturn_lm"] == A(13.10) and r["upturn_m2"] == A(2.62)
    assert r["doorway_continuation_m2"] == A(0.18) and r["surface_m2"] == A(14.80)
    assert s["band_pieces"] == 5 and s["band_pieces_m"] == A(13.10 + 4 * 0.10)     # open run, 4 joints
    assert r["laps_m2"] == A(1.20 + 1.31 + 0.12 + 0.09)
    assert r["installed_m2"] == A(17.52)
    assert r["rolls_if_alone"] == 2 and r["doorway_transitions_open"] == 1
    assert r["junction_state"] == "UNRESOLVED"
    assert r["installed_m2"] - r["fold"]["installed_m2"] == A(1.24)


def test_closed_kitchen_separate_upstand_consumed_by_hand():
    """3.00 x 4.00 m, no door. Floor 5 cuts of 3.00 m = 15.00 m2; the 0.40 m last strip leaves 0.60 m = 2 band lanes
    of 0.30 x 3.00 m (6.00 m of band); the closed band is 14.00 m + 5 joints x 0.10 = 14.50 m, 8.50 m still to cut
    as 3 lanes of one segment: 3 x 2.84 >= 8.50 (1 cm steps) -> consumed 15.00 + 2.84 = 17.84 m2, 2 rolls;
    installed 12.00 + 2.80 + laps (1.20 + 1.40 + 5 x 0.03 = 2.75) = 17.55; waste 17.84 - 17.55 = 0.29 m2."""
    t, r = one(X.area(X.rect(3000, 4000), room_id="K2", codes=("KITCHEN",)))
    assert r["upturn_lm"] == A(14.0) and r["laps_m2"] == A(2.75) and r["installed_m2"] == A(17.55)
    assert r["consumed_m2"] == A(17.84) and r["cutting_waste_m2"] == A(0.29) and r["rolls_if_alone"] == 2
    assert r["strips"]["band_pieces_m"] == A(14.50)
    assert t["systems"][0][MT.SEPARATE]["rolls_to_buy"] == 2


# ------------------------------------------------------------------------------------------------ owner's 3 x 3
def test_owner_bathroom_3x3_picture_does_not_match_his_own_q30_method():
    """his picture: 3 strips x 3.20 m = 9.60 m2, 1 roll. By his Q-30 method: developed 3.00 + 2 x 0.20 = 3.40 m each
    way; strips 1.00 + 0.90 + 0.90 = 2.80 -> a 4th strip of 0.60 + 0.10 lap = 0.70 m; 4 cuts of 3.40 m = 13.60 m
    of roll: a 10 m roll takes two (6.80, 3.20 left) -> 2 rolls; installed 3 x 3.40 + 0.70 x 3.40 = 12.58 m2;
    surface 9.00 + 12.00 x 0.20 = 11.40 m2. Even 3 strips (10.20 m) do not fit one roll."""
    t, r = one(X.area(X.rect(3000, 3000), room_id="B1", name_en="BATH"))
    f = r["fold"]
    assert f["strips"] == 4 and f["strip_length_m"] == A(3.40) and f["last_strip_width_m"] == A(0.70)
    assert f["installed_m2"] == A(12.58) and f["required_m2"] == A(11.40) and f["rolls_if_alone"] == 2
    assert r["net_m2"] == A(9.0) and r["upturn_m2"] == A(2.40)
    # separate upstand: n = ceil(2.00 / 0.90) + 1 = 4 strips of 3.00 m, last 3.00 - 3 x 0.90 = 0.30 m; laps
    # 3 x 0.30 + 12 x 0.10 + 5 x 0.03 = 2.25; installed 11.40 + 2.25 = 13.65; 2 rolls
    s = r["strips"]
    assert (s["floor_strips"], s["last_strip_width_m"]) == (4, 0.3)
    assert r["laps_m2"] == A(2.25) and r["installed_m2"] == A(13.65) and r["rolls_if_alone"] == 2
    assert f["direction_changes_rolls"] is False                 # square: both directions give 2 rolls


def test_toilet_with_doorway():
    """2.40 x 1.70 m, a 0.80 m door (wall 0.20) on the 2.40 m wall. Upturn (2.40 + 1.70) x 2 - 0.80 = 7.40 lm
    = 1.48 m2; doorway piece 0.80 x 0.20 = 0.16; surface 4.08 + 1.48 + 0.16 = 5.72 m2. Fold: developed 2.80 x 2.10,
    strips along 2.10: n = ceil(1.80 / 0.90) + 1 = 3, last 2.80 - 1.80 = 1.00 m; 3 x 2.10 = 6.30 m2 installed and
    consumed, 1 roll; laps 2 x 0.10 x 2.10 = 0.42, corners 0.16 -> 5.72 + 0.42 + 0.16 = 6.30."""
    t, r = one(X.area(X.rect(2400, 1700), room_id="T1", doors=[{"id": "D2", "edge": 0, "t0": 200, "t1": 1000,
                                                                  "depth": 200, "other_side": "DRY"}]))
    assert r["upturn_lm"] == A(7.40) and r["upturn_m2"] == A(1.48) and r["surface_m2"] == A(5.72)
    f = r["fold"]
    assert (f["direction"], f["strips"], f["strip_length_m"], f["last_strip_width_m"]) == ("ALONG_Y", 3, 2.1, 1.0)
    assert f["installed_m2"] == A(6.30) == A(f["required_m2"] + f["laps_m2"] + f["corner_excess_m2"])
    assert f["rolls_if_alone"] == 1 and r["rolls_if_alone"] == 1


# ------------------------------------------------------------------------------------------------ shapes
L_POLY = [(0, 0), (3000, 0), (3000, 1500), (1500, 1500), (1500, 2500), (0, 2500)]


def test_l_shaped_bathroom_fold_not_computed_reason_shown():
    """L: 3.00 x 1.50 + 1.50 x 1.00 = 6.00 m2; perimeter 3 + 1.5 + 1.5 + 1 + 1.5 + 2.5 = 11.00 lm -> 2.20 m2;
    surface 8.20. The engine's continuous fold is for rectangles only: the row says so, never 0."""
    t, r = one(X.area(L_POLY, room_id="L1"))
    assert r["net_m2"] == A(6.0) and r["upturn_lm"] == A(11.0) and r["surface_m2"] == A(8.20)
    assert r["fold"]["state"] == "BLOCKED" and "rectangle" in r["fold"]["reason"]
    assert r["fold_rolls_if_alone"] is None and r["rolls_if_alone"] == 2
    s = t["systems"][0][MT.FOLD]
    assert s["areas_computed"] == 0 and "rolls_to_buy" not in s
    assert "not computed" in MT.markdown(t)


def test_roof_with_skylight_opening_exterior_system():
    """roof 6.00 x 5.00 m inside the parapet, a 1.00 x 1.00 m skylight opening (owner Q-29: membrane stops at the
    opening with a 0.20 m upturn round it). Net 30.00 - 1.00 = 29.00 m2; upturn (22.00 + 4.00) x 0.20 = 5.20 m2;
    surface 34.20 m2; its own membrane system (exterior), never added to the wet-area rolls."""
    roof = X.area(X.rect(6000, 5000), room_id="RF1", codes=("ROOF",), scope="EXTERIOR",
                  holes=[[(2500, 2000), (2500, 3000), (3500, 3000), (3500, 2000)]])
    bath = X.area(X.rect(3000, 3000), room_id="B1")
    t = MT.from_areas([roof, bath], X.plans([roof, bath]))
    r = next(x for x in t["rows"] if x["room_id"] == "RF1")
    assert r["net_m2"] == A(29.0) and r["upturn_lm"] == A(26.0) and r["surface_m2"] == A(34.20)
    assert r["kind"] == "EXTERIOR" and r["fold"]["state"] == "BLOCKED"
    assert sorted(s["system_id"] for s in t["systems"]) == ["URBAN_DEFAULT_EXTERIOR", "URBAN_DEFAULT_WET_AREA"]
    for s in t["systems"]:
        assert s["areas"] == 1


# ------------------------------------------------------------------------------------------------ adversarial
def _core(r):
    keep = ("net_m2", "upturn_lm", "upturn_m2", "surface_m2", "laps_m2", "installed_m2", "consumed_m2",
            "rolls_if_alone")
    return {k: r[k] for k in keep}


def test_units_mm_and_m_give_the_same_row():
    a_mm = X.area(X.rect(3000, 4000), room_id="K1", codes=("KITCHEN",), doors=[DOOR_K])
    door_m = dict(DOOR_K, t0=1.0, t1=1.9, depth=0.2)
    a_m = X.area(X.rect(3.0, 4.0), unit=1.0, room_id="K1", codes=("KITCHEN",), doors=[door_m])
    r1, r2 = one(a_mm)[1], one(a_m)[1]
    assert _core(r1) == A(_core(r2))
    assert r1["fold"]["installed_m2"] == A(r2["fold"]["installed_m2"]) == A(16.28)


def test_rotated_37_and_mirrored():
    """the separate-upstand plan follows the room's own frame: rotated 37 deg or mirrored, the same numbers. The
    continuous fold is axis-parallel only in the engine: rotated it is NOT computed (reason shown, a finding for
    the engine), mirrored (still axis-parallel) it gives the same 16.28 m2."""
    base = one(X.area(X.rect(3000, 4000), room_id="K1", codes=("KITCHEN",)))[1]
    rot = one(X.area(X.transform(X.rect(3000, 4000), deg=37, dx=5000, dy=-2000), room_id="K1",
                     codes=("KITCHEN",)))[1]
    mir = one(X.area(X.transform(X.rect(3000, 4000), mirror=True), room_id="K1", codes=("KITCHEN",)))[1]
    assert _core(rot) == A(_core(base)) and _core(mir) == A(_core(base))
    assert rot["fold"]["state"] == "BLOCKED" and "axis-parallel" in rot["fold"]["reason"]
    assert mir["fold"]["state"] == "COMPUTED" and mir["fold"]["installed_m2"] == A(16.28)


def test_offcuts_shared_between_two_rooms_give_fewer_rolls():
    """R1 0.60 x 7.60 m and R2 0.60 x 1.60 m (closed showers). Fold: developed 1.00 x 8.00 and 1.00 x 2.00 = one
    strip each, 8.00 m and 2.00 m of roll: alone 1 + 1 = 2 rolls, together 8.00 + 2.00 = 10.00 m = 1 roll.
    Separate upstand (the engine's plan): alone 2 + 1 = 3, shared cutting plan 2."""
    r1, r2 = X.area(X.rect(600, 7600), room_id="R1"), X.area(X.rect(600, 1600), room_id="R2")
    t = MT.from_areas([r1, r2], X.plans([r1, r2]))
    s = t["systems"][0]
    assert s[MT.FOLD]["rolls_if_each_area_alone"] == 2 and s[MT.FOLD]["rolls_to_buy"] == 1
    assert s[MT.FOLD]["installed_m2"] == A(8.0 + 2.0) and s[MT.FOLD]["gross_offcuts_m2"] == A(0.0)
    assert s[MT.SEPARATE]["rolls_if_each_area_alone"] == 3 and s[MT.SEPARATE]["rolls_to_buy"] == 2
    assert s[MT.SEPARATE]["rolls_saved_by_reusing_offcuts"] == 1


def test_held_rows_never_zero_and_outside_the_roll_totals():
    a = X.area(X.rect(3000, 3000), room_id="B1")
    h = MT.held_row(floor="1F", room_id="R9", name_en="ROOF", kind="EXTERIOR",
                    reason="roof outline not closed (parapet gap), owner Q-25")
    line = {"item_code": "FIN.WP.FLOOR", "measured_net": None, "evidence_state": "HELD", "line_id": "L7",
            "location": {"floor": "GF", "room_id": "W3", "room_name_en": "WC"},
            "rfi": {"question": "wet / dry not established"}}
    held = [h] + MT.held_from_lines([line, {"item_code": "FIN.WP.FLOOR", "measured_net": 4.0,
                                            "location": {"floor": "GF", "room_id": "B1"}}], {("GF", "B1")})
    t = MT.from_areas([a], X.plans([a]), held=held)
    assert t["held_count"] == 2 and [x["room_id"] for x in t["held"]] == ["R9", "W3"]          # sorted by floor, then room
    for x in t["held"]:
        assert x["state"] == "HELD" and x["net_m2"] is None and x["rolls_if_alone"] is None and x["reason"]
    assert t["systems"][0][MT.SEPARATE]["rolls_to_buy"] == 2                       # only B1
    assert {f["floor"]: f["held"] for f in t["floors"]} == {"1F": 1, "GF": 1}
    rows = MT.csv_rows(t)
    assert [r["state"] for r in rows].count("HELD") == 2
    assert all(r["net_m2"] is None for r in rows if r["state"] == "HELD")
    with pytest.raises(MT.TableError):
        MT.held_row(floor="GF", room_id="X", reason="")


def test_duplicate_area_refused():
    a = X.area(X.rect(3000, 3000), room_id="B1")
    with pytest.raises(MT.TableError):
        MT.from_areas([a], X.plans([a]), held=[MT.held_row(floor="GF", room_id="B1", reason="duplicate")])


def test_fold_cuts_refuses_a_record_that_does_not_balance():
    f = {"strips": 4, "pieces_per_strip": 1, "strip_length_m": 4.4, "consumed_m2": 17.6, "rolls_if_alone": 2}
    assert MT.fold_cuts(f, 10.0, 0.10, 1.0) == [4.4] * 4
    with pytest.raises(MT.TableError):
        MT.fold_cuts(dict(f, consumed_m2=16.28), 10.0, 0.10, 1.0)
    with pytest.raises(MT.TableError):
        MT.fold_cuts(dict(f, rolls_if_alone=1), 10.0, 0.10, 1.0)
    # a strip longer than a roll: 12.40 m = 10.00 + (12.40 - 9.90) = 10.00 + 2.50 with one 0.10 end lap
    g = {"strips": 1, "pieces_per_strip": 2, "strip_length_m": 12.4, "consumed_m2": 12.5, "rolls_if_alone": 2}
    assert MT.fold_cuts(g, 10.0, 0.10, 1.0) == A([10.0, 2.5])


def test_table_reads_the_engine_without_changing_it():
    """the table's numbers are the schedule's and the cutting plan's own (no second calculation)."""
    a = X.area(X.rect(3000, 4000), room_id="K1", codes=("KITCHEN",), doors=[DOOR_K])
    p = X.plans([a])
    before = json.dumps(a["row"], sort_keys=True, default=str)
    t = MT.from_areas([a], p)
    assert json.dumps(a["row"], sort_keys=True, default=str) == before
    r, s = t["rows"][0], t["systems"][0][MT.SEPARATE]
    assert r["installed_m2"] == A(a["row"]["B_installed_m2"]) and r["consumed_m2"] == A(a["row"]["consumed_m2"])
    assert s["rolls_to_buy"] == p[0]["rolls"] and t["junction"]["selected"] is None


def test_cli_writes_the_table(tmp_path):
    """tools/membrane_table.py on a run's output files (written here by the test from synthetic areas)."""
    from engine.source import waterproofing_system as WS
    k = X.area(X.rect(3000, 4000), room_id="K1", codes=("KITCHEN",), doors=[DOOR_K])
    b = X.area(X.rect(3000, 3000), room_id="B1")
    p = X.plans([k, b])
    sched = WS.schedule([k, b], p)
    run = tmp_path / "run"
    run.mkdir()
    (run / "WATERPROOFING_SCHEDULE.json").write_text(json.dumps({"waterproofing": {x: v for x, v in sched.items()
                                                                                  if x != "systems"}}, default=str))
    (run / "MEMBRANE_CUTTING_PLAN.json").write_text(json.dumps({"systems": p}, default=str))
    inst = WS.installation_outputs([k, b])
    (run / "WP_INSTALLATION.json").write_text(json.dumps({"installation": inst["installation"]}, default=str))
    (run / "MATERIAL_RESULTS.json").write_text(json.dumps({"results": [k["layout"], b["layout"]]}, default=str))
    (run / "REVIEW_SPACES.json").write_text(json.dumps({"spaces": [
        {"floor": "GF", "room_id": "H1", "name_en": "Unnamed space", "issue_code": "WET_CLASSIFICATION_REVIEW",
         "conditional": {"WET_SCOPE": [{"item_code": "FIN.WP.FLOOR", "quantity": 1.92}], "DRY_SCOPE": []}},
        {"floor": "GF", "room_id": "H2", "conditional": {"WET_SCOPE": [], "DRY_SCOPE": []}}]}))
    (run / "ARCH_ROOMS.json").write_text(json.dumps({"rooms": [
        {"floor": "GF", "room_id": "OP1", "class": "MIXED", "codes": ["LIVING", "PANTRY"],
         "finish_scope": {"scope": "REVIEW", "flags": ["OPEN_PLAN_WET_SCOPE_EXTENT: not drawn"]}},
        {"floor": "GF", "room_id": "K1", "class": "ROOM", "codes": ["KITCHEN"], "finish_scope": {"scope": "WET"}}]}))
    held = tmp_path / "held.json"
    held.write_text(json.dumps([{"floor": "1F", "room_id": "R9", "reason": "roof outline held (T-071)"}]))
    out = tmp_path / "out"
    cp = subprocess.run([sys.executable, "-I", str(X.ROOT / "tools" / "membrane_table.py"), str(run), "--out",
                         str(out), "--held", str(held)], capture_output=True, text=True, cwd=str(X.ROOT))
    assert cp.returncode == 0, cp.stderr
    t = json.loads((out / "MEMBRANE_TABLE.json").read_text())
    ks = {r["room_id"]: r for r in t["rows"]}
    assert ks["K1"]["fold"]["installed_m2"] == A(16.28) and ks["K1"]["strips"]["floor_strips"] == 5
    # the roof of --held, the wet-review space H1 (H2 has no wet membrane), the open plan OP1; never K1 again
    assert sorted(h["room_id"] for h in t["held"]) == ["H1", "OP1", "R9"]
    assert all(h["net_m2"] is None for h in t["held"]) and "1.92" in next(h for h in t["held"]
                                                                          if h["room_id"] == "H1")["reason"]
    assert t["held_count"] == 3 and (out / "MEMBRANE_TABLE.csv").exists() and (out / "MEMBRANE_TABLE.md").exists()
    wet = t["systems"][0]
    assert wet[MT.SEPARATE]["rolls_to_buy"] == p[0]["rolls"]
    assert wet[MT.FOLD]["rolls_if_each_area_alone"] == 2 + 2
