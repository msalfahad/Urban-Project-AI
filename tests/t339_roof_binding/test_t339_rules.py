"""T-339 rules R-T339-1 .. 5 on a hand-made villa (NOT Alsenan): two roofs at different levels, roof A with a parapet on
three sides (the fourth side is the upper storey's wall), roof B with a parapet all round.

Hand calculation (metres, parapet t = 0.20 everywhere):
  Roof A +3.50: inside the parapet inner faces / wall face 8.00 x 5.00 = 40.00 m2; parapet south 8.10 + east 5.20 +
    north 8.10 = 21.40 m centreline (corners on the centreline) x 0.20 = 4.28 m2 footprint; slab roof zone to the outer
    wall line 8.20 x 5.40 = 44.28 m2 = 40.00 + 4.28 (closure 0.000). The finish hatch stops on a 0.10 m band along the
    5.00 m wall: finish 7.90 x 5.00 = 39.50 m2, face layers 39.50 .. 40.00 (band 0.500 m2 named).
  Roof B +7.00: 4.00 x 3.00 = 12.00 m2; centreline 2 x 4.20 + 2 x 3.20 = 14.80 m x 0.20 = 2.96 m2; zone 4.40 x 3.40 =
    14.96 m2 = 12.00 + 2.96. Finish to the inner face: 12.00 m2.
  Upturn (membrane): A 8.00 + 5.00 + 8.00 + wall 5.00 = 26.00 m; B 14.00 m.
"""
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t339"))
sys.path.insert(0, str(ROOT / "research" / "agents_t321"))
import roof_buildup as RB  # noqa: E402
import t339_binding as B   # noqa: E402

A = B.Roof("A", "R-A", "1F", "GF", 44.28, (4.28, 4.28), (39.50, 40.00), (39.50, 39.50), (26.0, 26.0))
BB = B.Roof("B", "R-B", "2F", "1F", 14.96, (2.96, 2.96), (12.00, 12.00), (12.00, 12.00), (14.0, 14.0))
LINES = {"A-WP": {"line_id": "L-a1", "item_code": "FIN.WP.ROOF", "unit": "m2", "state": "SOURCE_DERIVED",
                  "quantity": 40.0},
         "A-UP": {"line_id": "L-a2", "item_code": "FIN.WP.ROOF_UPTURN", "unit": "lm", "state": "SOURCE_DERIVED",
                  "quantity": 26.0},
         "B-WP": {"line_id": "L-b1", "item_code": "FIN.WP.ROOF", "unit": "m2", "state": "SOURCE_DERIVED",
                  "quantity": 12.0},
         "B-UP": {"line_id": "L-b2", "item_code": "FIN.WP.ROOF_UPTURN", "unit": "lm", "state": "SOURCE_DERIVED",
                  "quantity": 14.0}}


def _rows(roof, key):
    face = roof.face_m2
    return [
        B.bind(roof, "FALLS_SCREED", scope="OWNER_RULE", scope_source="Q-41", area=face, quantity_status="HELD",
               new_row=f"B13-01 ROOF SCREED TO FALLS {key}", held_reason="t0 unprinted"),
        B.bind(roof, "MEMBRANE", scope="OWNER_RULE", scope_source="Q-24", area=face, quantity=face,
               line=LINES[f"{key}-WP"]),
        B.bind(roof, "UPTURN", scope="OWNER_RULE", scope_source="Q-24", quantity=roof.upturn_lm, line=LINES[f"{key}-UP"],
               upturn_height_m=0.2, upturn_source="Q-24"),
        B.bind(roof, "INSULATION", scope="UNKNOWN", scope_source="nothing printed", new_row=f"B13-01 ROOF INSULATION {key}"),
        B.bind(roof, "PROTECTION", scope="UNKNOWN", scope_source="nothing printed", new_row=f"B13-01 ROOF PROTECTION {key}"),
        B.bind(roof, "FINISH", scope="PRINTED", scope_source="hatch", area=roof.finish_m2, quantity=roof.finish_m2,
               new_row=f"B13-01 ROOF FINISH {key}"),
    ]


def test_normal_two_roofs_every_layer_once():
    rows = _rows(A, "A") + _rows(BB, "B")
    assert B.check_bindings(rows)
    assert len(rows) == 12 and len({(r["roof"], r["layer"]) for r in rows}) == 12
    scr = [r for r in rows if r["layer"] == "FALLS_SCREED"]
    assert all(r["unit"] == "m3" and r["quantity_lo"] is None and r["status"] == "HELD" for r in scr)
    assert scr[0]["area_lo"] == 39.50 and scr[0]["area_hi"] == 40.00
    unk = [r for r in rows if r["status"] == "UNKNOWN"]
    assert len(unk) == 4 and all(r["quantity_lo"] is None and r["area_lo"] is None for r in unk)
    fin = {r["roof"]: r["quantity_lo"] for r in rows if r["layer"] == "FINISH"}
    assert fin == {"A": 39.50, "B": 12.00}
    fill = B.fill_rows(rows)
    assert [f["action"] for f in fill if f["roof"] == "A"] == [
        "ADD (blank, held)", "UNCHANGED (cross-reference)", "UNCHANGED (cross-reference)", "ADD (blank, held)",
        "ADD (blank, held)", "ADD"]


def test_normal_closures_hand_values():
    c = B.closure(A, 40.00, [], end="hi")
    assert c["closes"] and abs(c["residual_m2"]) < 1e-9
    c = B.closure(A, 39.50, [["0.10 band along the 5.00 m wall", 0.50]], end="lo")
    assert c["closes"] and abs(c["residual_m2"] - 0.50) < 1e-9
    c = B.closure(BB, 12.00, [], end="hi")
    assert c["closes"]
    # the footprint by centreline x t equals outer - inner on every roof (the hand numbers above)
    assert abs((8.10 + 5.20 + 8.10) * 0.20 - (8.20 * 5.40 - 8.00 * 5.00)) < 1e-9
    assert abs((2 * 4.20 + 2 * 3.20) * 0.20 - (4.40 * 3.40 - 4.00 * 3.00)) < 1e-9


def test_normal_mirror_rotation_and_shared_area():
    from shapely.geometry import Polygon
    inner = [(0, 0), (8, 0), (8, 5), (0, 5)]
    outer = [(0, -0.2), (8.2, -0.2), (8.2, 5.2), (0, 5.2)]
    for deg in (0.0, 30.0, -121.0, 47.0):
        for mir in (1, -1):
            t = math.radians(deg)

            def f(p):
                x, y = p[0] * mir, p[1]
                return (x * math.cos(t) - y * math.sin(t), x * math.sin(t) + y * math.cos(t))
            pi, po = Polygon([f(p) for p in inner]), Polygon([f(p) for p in outer])
            assert abs(po.area - 44.28) < 1e-9 and abs(pi.area - 40.0) < 1e-9
            assert B.shared_area(pi, [po.difference(pi)]) < 1e-9
            # adverse: a layer drawn to the parapet outer face shares the whole footprint
            assert abs(B.shared_area(po, [po.difference(pi)]) - 4.28) < 1e-9
    assert abs(RB.shoelace(inner) - 40.0) < 1e-12


def test_adverse_layer_to_the_parapet_outer_face_refused():
    with pytest.raises(B.Refused, match="exceeds the area inside the parapet inner face"):
        B.bind(A, "FINISH", scope="PRINTED", scope_source="hatch", area=(44.28, 44.28), quantity=(44.28, 44.28),
               new_row="B13-01 ROOF FINISH A")
    # millimetres slipped in as m2: refused by the same check, never a 40 million m2 roof
    with pytest.raises(B.Refused):
        B.bind(A, "FALLS_SCREED", scope="OWNER_RULE", scope_source="Q-41", area=(39.5e6, 40.0e6),
               quantity_status="HELD", new_row="B13-01 ROOF SCREED TO FALLS A")


def test_adverse_falls_screed_as_an_area_or_twice_refused():
    with pytest.raises(B.Refused, match="booked in m2"):
        B.bind(A, "FALLS_SCREED", scope="OWNER_RULE", scope_source="Q-41", area=A.face_m2, quantity_status="HELD",
               new_row="B13-01 ROOF SCREED TO FALLS A", booked_unit="m2")
    rows = _rows(A, "A")
    second = dict(rows[0])
    second["layer"] = "FALLS_SCREED"
    with pytest.raises(B.Refused, match="bound twice"):
        B.check_bindings(rows + [second])


def test_adverse_held_thickness_as_zero_or_default_refused():
    with pytest.raises(B.Refused, match="never 0"):
        B.bind(A, "FALLS_SCREED", scope="OWNER_RULE", scope_source="Q-41", area=A.face_m2, quantity_status="HELD",
               new_row="B13-01 ROOF SCREED TO FALLS A", thickness_m=0.0, thickness_source="drawing")
    with pytest.raises(B.Refused, match="without a printed source"):
        B.bind(A, "FALLS_SCREED", scope="OWNER_RULE", scope_source="Q-41", area=A.face_m2, quantity_status="HELD",
               new_row="B13-01 ROOF SCREED TO FALLS A", thickness_m=0.05)
    with pytest.raises(B.Refused, match="carried as 0"):
        B.bind(A, "FALLS_SCREED", scope="OWNER_RULE", scope_source="Q-41", area=A.face_m2, quantity=(0, 0),
               quantity_status="HELD", new_row="B13-01 ROOF SCREED TO FALLS A")
    with pytest.raises(B.Refused, match="carried as 0"):
        B.bind(A, "INSULATION", scope="UNKNOWN", scope_source="none", quantity=(0, 0),
               new_row="B13-01 ROOF INSULATION A")


def test_adverse_membrane_double_or_wrong_line_refused():
    with pytest.raises(B.Refused, match="double count with the waterproofing line"):
        B.bind(A, "MEMBRANE", scope="OWNER_RULE", scope_source="Q-24", area=A.face_m2, quantity=A.face_m2,
               new_row="B13-01 ROOF MEMBRANE A")
    wrong = {"line_id": "L-x", "item_code": "FIN.EXT.FINISH", "unit": "m2", "state": "SOURCE_DERIVED"}
    with pytest.raises(B.Refused, match="the layer's family is FIN.WP.ROOF"):
        B.bind(A, "MEMBRANE", scope="OWNER_RULE", scope_source="Q-24", area=A.face_m2, quantity=A.face_m2, line=wrong)
    rows = _rows(A, "A") + _rows(BB, "B")
    rows[7] = dict(rows[7], line_id="L-a1")      # B's membrane pointed at A's line
    with pytest.raises(B.Refused, match="bound under"):
        B.check_bindings(rows)


def test_adverse_parapet_component_or_unprinted_upstand_refused():
    with pytest.raises(B.Refused, match="names a parapet component"):
        B.bind(A, "FINISH", scope="PRINTED", scope_source="hatch", area=A.finish_m2, quantity=A.finish_m2,
               new_row="B13-01 ROOF FINISH A incl. PARAPET TOP")
    with pytest.raises(B.Refused, match="without a printed height"):
        B.bind(A, "PROTECTION", scope="UNKNOWN", scope_source="none", new_row="B13-01 ROOF PROTECTION A",
               upturn_height_m=0.3)


def test_adverse_unexplained_residual_reported_not_forced():
    c = B.closure(A, 39.50, [], end="lo")
    assert not c["closes"] and abs(c["unexplained_m2"] - 0.50) < 1e-9
    c = B.closure(A, 39.50, [["band", 0.40]], end="lo")
    assert not c["closes"] and abs(c["unexplained_m2"] - 0.10) < 1e-9


def test_adverse_unknown_with_a_number_or_area_refused():
    with pytest.raises(B.Refused, match="carries a number"):
        B.bind(A, "INSULATION", scope="UNKNOWN", scope_source="none", quantity=(40.0, 40.0),
               new_row="B13-01 ROOF INSULATION A")
    with pytest.raises(B.Refused, match="carries no area"):
        B.bind(A, "INSULATION", scope="UNKNOWN", scope_source="none", area=(40.0, 40.0),
               new_row="B13-01 ROOF INSULATION A")


def test_adverse_held_roof_blank():
    held = B.Roof("H", "R-H", "2F", "2F", 55.0, (5.0, 5.0), (50.0, 50.0), None, None, held="no roof plan")
    r = B.bind(held, "FINISH", scope="UNKNOWN", scope_source="none", new_row="B13-01 ROOF FINISH H")
    assert r["status"] == "HELD" and r["area_lo"] is None and r["quantity_lo"] is None
    with pytest.raises(B.Refused, match="carries a number"):
        B.bind(held, "FINISH", scope="PRINTED", scope_source="x", quantity=(50.0, 50.0), new_row="B13-01 ROOF FINISH H")
