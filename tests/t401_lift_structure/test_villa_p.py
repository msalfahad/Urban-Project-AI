"""T-401 LIFT_STRUCTURE_V1 on hand villa P (not the development villa). Every expected value is a hand calculation:

Raft 4.00 x 4.20 x 0.60 = 10.080 m3. Ring outer 2.00 x 2.20, shaft 1.50 x 1.70 (walls 0.25): gross 4.400 - 2.550 = 1.850 m2.
Columns in the band: SW 0.25 x 0.50 = 0.125, NE 0.25 x 0.50 = 0.125, SE 0.35 x 0.80 drawn 0.10 proud of the ring, in the
band 0.25 x 0.80 = 0.200 -> 0.450; net ring 1.400 m2. Clear runs: S 1.50, N 1.75, W 1.45, E 0.90 = 5.60 m
(check: 5.60 x 0.25 = 1.400 m2). Pit depth (supplier) 1.40 below the F.F.L., build-up F.F.L. -> slab top 0.12, wall top at
the slab top: wall height 1.28 m, wall concrete 1.400 x 1.28 = 1.792 m3. GF storey 0.00 -> 4.60 = 4.60 > 4.30: tie beam
at +3.00, 5.60 x 0.25 x 0.40 = 0.560 m3; 1F 4.60 -> 8.40 and 2F 8.40 -> 12.00 need none. Shaft 2.550 m2: opening at GF
and 1F, cap at the 2F roof.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t401"))
import lift_structure_v1 as X  # noqa: E402


def villa(**kw):
    s = {
        "unit": "cm",
        "raft": {"rect": [0, 0, 400, 420], "depth": 60},
        "ring_outer": [100, 100, 300, 320], "shaft": [125, 125, 275, 295],
        "columns": [[100, 100, 125, 150], [275, 270, 300, 320], [275, 100, 310, 180]],
        "wall_top_datum": X.WALL_TOP_SLAB,
        "pit_depth": {"value": 1.40, "basis": X.SUPPLIER, "datum": X.WALL_TOP_FFL},
        "build_up": 0.12,
        "tie_rule": {"limit": 4.30, "level": 3.00}, "tie_section": {"b": 0.25, "d": 0.40},
        "storeys": [
            {"name": "GF", "ffl": 0.00, "next_ffl": 4.60, "shaft": "OPENING",
             "ring_beams": [{"mark": "B3", "length": 1.50, "depth": 0.50}]},
            {"name": "1F", "ffl": 4.60, "next_ffl": 8.40, "shaft": "OPENING", "ring_beams": []},
            {"name": "2F", "ffl": 8.40, "next_ffl": 12.00, "shaft": "CAP", "ring_beams": []},
        ],
        "shaft_wall_trade": "BLOCKWORK",
        "bind": {"RAFT": "L-raft", "PIT_WALL": "L-wall", "TIE_BEAM:GF": "L-tie", "RING_BEAM:GF:B3:1": "L-b3",
                 "SHAFT_SLAB:2F": "L-roof", "COLUMN:1": "L-c1", "COLUMN:2": "L-c2", "COLUMN:3": "L-c3"},
    }
    s.update(kw)
    return s


def comp(led, cid):
    return {c["id"]: c for c in led["components"]}[cid]


def test_normal_hand_values():
    led = X.build(villa())
    g = led["ring"]
    assert g["gross_m2"] == pytest.approx(1.85) and g["columns_in_band_m2"] == pytest.approx(0.45)
    assert g["net_m2"] == pytest.approx(1.40)
    assert g["runs_m"] == pytest.approx({"S": 1.50, "N": 1.75, "W": 1.45, "E": 0.90})
    assert g["run_total_m"] == pytest.approx(5.60)
    assert led["wall_height_m"] == pytest.approx(1.28)
    assert comp(led, "RAFT")["value"] == pytest.approx(10.08)
    assert comp(led, "PIT_WALL")["value"] == pytest.approx(1.792) and comp(led, "PIT_WALL")["status"] == X.DC
    assert comp(led, "TIE_BEAM:GF")["value"] == pytest.approx(0.56)
    assert "TIE_BEAM:1F" not in {c["id"] for c in led["components"]}
    assert comp(led, "SHAFT_SLAB:GF")["owner_trade"] == "NONE" and comp(led, "SHAFT_SLAB:GF")["value"] == pytest.approx(2.55)
    assert comp(led, "SHAFT_SLAB:2F")["line_id"] == "L-roof"
    assert comp(led, "SHAFT_VOID:GROUND")["owner_trade"] == "NONE"
    assert comp(led, "PIT_FLOOR")["value"] is None                         # the raft top, no volume


def test_depth_to_slab_top_needs_no_build_up():
    led = X.build(villa(pit_depth={"value": 1.28, "basis": X.PRINTED, "datum": X.WALL_TOP_SLAB}, build_up=None))
    assert comp(led, "PIT_WALL")["value"] == pytest.approx(1.792)


def test_supplier_depth_without_build_up_stays_held():
    led = X.build(villa(build_up=None))
    w = comp(led, "PIT_WALL")
    assert w["status"] == X.HELD and w["value"] is None
    assert w["missing"] == ["floor build-up F.F.L. -> slab-on-grade top"]


def test_no_depth_held_never_zero():
    led = X.build(villa(pit_depth={"value": None}))
    w = comp(led, "PIT_WALL")
    assert w["value"] is None and w["status"] == X.HELD and "pit depth (lift supplier / designer)" in w["missing"]


@pytest.mark.parametrize("basis", ["NECK_HEIGHT", "DEFAULT", "FREELANCER", None])
def test_depth_defaulted_refused(basis):
    with pytest.raises(X.Refused) as e:
        X.build(villa(pit_depth={"value": 1.50, "basis": basis, "datum": X.WALL_TOP_SLAB}))
    assert e.value.code == "DEPTH_DEFAULTED"


def test_held_as_zero_refused():
    with pytest.raises(X.Refused) as e:
        X._comp("PIT_WALL", "pit wall", "STRUCTURE", "m3", 0.0, X.HELD, missing=["pit depth"])
    assert e.value.code == "HELD_WITH_VALUE"
    with pytest.raises(X.Refused) as e:
        X._comp("PIT_WALL", "pit wall", "STRUCTURE", "m3", None, X.HELD)
    assert e.value.code == "HELD_WITHOUT_MISSING_FACT"


def test_missing_line_named_not_valued():
    b = villa()["bind"]
    b.pop("PIT_WALL")
    led = X.build(villa(bind=b))
    w = comp(led, "PIT_WALL")
    assert w["status"] == X.MISSING and w["value"] is None and "1.792000 m3 ready" in w["missing"][0]


def test_tie_section_not_printed_held_with_length():
    led = X.build(villa(tie_section=None))
    t = comp(led, "TIE_BEAM:GF")
    assert t["status"] == X.HELD and t["value"] is None and "5.600 m" in t["note"]


def test_mirror_quarter_turn_and_mm_identical():
    base = X.build(villa())

    def mirror(r):
        return [-r[2], r[1], -r[0], r[3]]

    def turn(r):
        return [r[1], -r[2], r[3], -r[0]]

    for f in (mirror, turn):
        v = villa(raft={"rect": f([0, 0, 400, 420]), "depth": 60}, ring_outer=f([100, 100, 300, 320]),
                  shaft=f([125, 125, 275, 295]), columns=[f(c) for c in villa()["columns"]])
        led = X.build(v)
        assert led["ring"]["net_m2"] == pytest.approx(1.40) and led["ring"]["run_total_m"] == pytest.approx(5.60)
        assert comp(led, "PIT_WALL")["value"] == pytest.approx(comp(base, "PIT_WALL")["value"])
    mm = villa(unit="mm", raft={"rect": [0, 0, 4000, 4200], "depth": 600}, ring_outer=[1000, 1000, 3000, 3200],
               shaft=[1250, 1250, 2750, 2950], columns=[[c * 10 for c in r] for r in villa()["columns"]])
    led = X.build(mm)
    assert comp(led, "RAFT")["value"] == pytest.approx(10.08) and comp(led, "PIT_WALL")["value"] == pytest.approx(1.792)


def test_unit_and_geometry_guards():
    for kw, code in ((dict(unit=None), "UNIT_NOT_DECLARED"), (dict(raft={}), "NO_LIFT_BASE"),
                     (dict(raft={"rect": [150, 150, 250, 250], "depth": 60}), "RING_OUTSIDE_RAFT"),
                     (dict(columns=[[130, 130, 160, 180]]), "COLUMN_INTO_SHAFT"),
                     (dict(wall_top_datum=None), "WALL_TOP_DATUM_NOT_DRAWN")):
        with pytest.raises(X.Refused) as e:
            X.build(villa(**kw))
        assert e.value.code == code


def test_line_bound_to_two_components_refused():
    b = dict(villa()["bind"])
    b["TIE_BEAM:GF"] = "L-wall"
    with pytest.raises(X.Refused) as e:
        X.build(villa(bind=b))
    assert e.value.code == "LINE_BOUND_TWICE"


def test_shaft_opening_billed_as_slab_refused():
    b = dict(villa()["bind"])
    b["SHAFT_SLAB:1F"] = "L-1f-slab"
    with pytest.raises(X.Refused) as e:
        X.build(villa(bind=b))
    assert e.value.code == "SHAFT_OPENING_BILLED_AS_SLAB"


V = villa()


def test_claims_normal_zero_double_and_no_gap():
    claims = [
        {"line": "L-wall", "family": "PIT_WALL", "valued": False,      # held wall: S, N, W, E net bands
         "rects": [[125, 100, 275, 125], [100, 295, 275, 320], [100, 150, 125, 295], [275, 180, 300, 270]]},
        {"line": "L-c1", "family": "COLUMN", "rect": [100, 100, 125, 150]},
        {"line": "L-c2", "family": "COLUMN", "rect": [275, 270, 300, 320]},
        {"line": "L-c3", "family": "COLUMN", "rect": [275, 100, 310, 180]},
        {"line": "L-slab", "family": "SLAB", "level": "GROUND", "rects": [[0, 0, 100, 420], [300, 180, 400, 420]]},
    ]
    r = X.claims_check(V["ring_outer"], V["shaft"], V["columns"], claims, s=0.01)
    assert r["doubles"] == [] and r["pairs"] == [] and r["gap_ring_m2"] == pytest.approx(0.0)
    assert r["ring_net_m2"] == pytest.approx(1.40)


def test_pit_wall_in_slab_and_wall_refused():
    claims = [{"line": "L-wall", "family": "PIT_WALL", "valued": False, "rect": [125, 100, 275, 125]},
              {"line": "L-slab", "family": "SLAB", "level": "GROUND", "rect": [0, 0, 400, 125]}]
    with pytest.raises(X.Refused) as e:
        X.claims_check(V["ring_outer"], V["shaft"], V["columns"], claims, s=0.01)
    assert e.value.code == "PIT_WALL_IN_SLAB_AND_WALL"


def test_lift_columns_inside_the_ring_twice_refused():
    claims = [{"line": "L-wall", "family": "PIT_WALL", "valued": False, "rect": [100, 100, 300, 125]},   # gross run
              {"line": "L-c1", "family": "COLUMN", "rect": [100, 100, 125, 150]}]
    with pytest.raises(X.Refused) as e:
        X.claims_check(V["ring_outer"], V["shaft"], V["columns"], claims, s=0.01)
    assert e.value.code == "COLUMN_IN_RING_AND_COLUMN"


def test_shaft_void_as_ground_slab_refused():
    claims = [{"line": "L-slab", "family": "SLAB", "level": "GROUND", "rect": [125, 125, 275, 295]}]
    with pytest.raises(X.Refused) as e:
        X.claims_check(V["ring_outer"], V["shaft"], V["columns"], claims, s=0.01)
    assert e.value.code == "SHAFT_VOID_AS_SLAB"


def test_valued_double_named_and_gap_named():
    claims = [{"line": "L-c1", "family": "COLUMN", "rect": [100, 100, 125, 150]},
              {"line": "L-neck", "family": "COLUMN", "rect": [100, 100, 125, 150]},
              {"line": "L-wall", "family": "PIT_WALL", "valued": False, "rect": [125, 100, 275, 125]}]
    r = X.claims_check(V["ring_outer"], V["shaft"], V["columns"], claims, s=0.01)
    assert r["doubles"] == [{"a": "L-c1", "b": "L-neck", "m2": pytest.approx(0.125), "kind": "DOUBLE"}]
    assert r["gap_ring_m2"] == pytest.approx(1.40 - 0.375)
