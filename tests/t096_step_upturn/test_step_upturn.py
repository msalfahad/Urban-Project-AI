"""T-096: complete membrane coverage (MEMBRANE_FOLD_V3), the cutting plan read under owner Q-58 (MEMBRANE_CUTTING_PLAN_V2)
and ARCH_TAKEOFF_V2.12. Synthetic, hand-calculated outlines only (none is the development villa). Roll 1.00 x 10.00 m,
lap 0.10 m, upturn 0.20 m (UP-WP-001 / 002 / 003).

The bands of a layout (MEMBRANE_FOLD_V2._bands, start wall at y = 0): strip k's sheet covers y = -0.20 + 0.90 k ..
+0.80 + 0.90 k; the slab it adds (where the previous sheet does not reach) is from 0.90 k - 0.10 (first: -0.20).

Fixture N, "notch" (m): a 12.00 x 4.60 roof with a 4.00 x 2.10 notch at one corner: (0,0) (12,0) (12,4.6) (4,4.6)
(4,2.5) (0,2.5). Strips along x from y = 0: 6 bands (n = ceil((4.60 + 0.40 - 1.00) / 0.90) + 1); bands 0-2 hold floor
over x 0..12 -> 12.40 m (10.00 + 2.50 spliced), bands 3-5 over x 4..12 -> 8.40 m (band 5 0.50 m wide). The notch edge
y = 2.50, x 0..4 runs parallel to the strips; its upturn y 2.50..2.70 is covered by band 2's sheet up to 2.60 only;
2.60..2.70 lies in band 3's slab (2.60..3.50), where x 0..4 has no floor and band 3's strip starts at x = 3.80.
Uncovered before the fix: x -0.20 (the mitred corner) .. 3.80 x 0.10 = 0.40 m2 (V2 counts 3.80 x 0.10 = 0.38 without
the corner square). V3: one upturn-only strip in band 3, 4.00 m + 0.10 end lap where it meets band 3's strip = 4.10 m,
need width 0.10 + 0.10 lap = 0.20 m. Rolls: 3 x 10.00, 3 x 8.40, 3 x 2.50 (+ 4.10): any two of the six long pieces
exceed 10 m -> 6 rolls with 0 / 1.60 m left; 3 x 2.50 = 7.50 in one roll (2.50 left) -> 7 rolls without the 4.10 m
piece; with it 2.50 + 2.50 + 4.10 = 9.10 and 2.50 alone -> 8 (no 1.60 / 2.50 leftover holds 4.10). Q-58 B = C = 8;
Q-58 A = 7 (the 0.20 x 4.10 piece is cut from the 0.50 m strip's side trim 0.50 x 8.40). The opposite start wall and
both across layouts meet no step: 7 / 7 / 7, so the area is RELEASED at 7 rolls (the fewest under every reading)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v211 as AV11                   # noqa: E402
from engine.source import arch_v212 as AV                     # noqa: E402
from engine.source import membrane_cutting_plan_v2 as CP      # noqa: E402
from engine.source import membrane_fold_v2 as F2              # noqa: E402
from engine.source import membrane_fold_v3 as F3              # noqa: E402

NOTCH = [(0, 0), (12, 0), (12, 4.6), (4, 4.6), (4, 2.5), (0, 2.5)]
HELD9 = [(0, 0), (9, 0), (9, 4.6), (2, 4.6), (2, 2.6), (0, 2.6)]
CTX = {"project_id": "synthetic", "revision_set_sha256": "0" * 64, "documents": [{"file": "x.dxf", "sha256": "0"}]}


def _xf(pts, *, scale=1.0, mirror=False, deg=0.0, shift=(0.0, 0.0)):
    a = math.radians(deg)
    out = []
    for x, y in pts:
        if mirror:
            x = -x
        x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        out.append(((x + shift[0]) * scale, (y + shift[1]) * scale))
    return out


def _lay(f, direction, start):
    return [x for x in f["layouts_v3"] if x["direction"] == direction and x["start"] == start][0]


def _step_layouts(f):
    return [x for x in f["layouts_v3"] if x["upturn_strips"]]


# ------------------------------------------------------------------------------------------------ unchanged cases
@pytest.mark.parametrize("poly,rolls", [([(0, 0), (12, 0), (12, 5), (0, 5)], {8, 14}),
                                        ([(0, 0), (4, 0), (4, 3), (0, 3)], {2, 3})])
def test_plain_rectangles_give_the_v2_strips_and_rolls(poly, rolls):
    """a 12.00 x 5.00 roof and the owner's 3 x 4 kitchen (Q-30): every V3 layout has the V2 strips exactly, no
    upturn-only strip, no patch, nothing uncovered, and the three Q-58 readings agree with the V2 count."""
    f = F3.fold(poly)
    v2 = {(o["direction"], F3.LOWER): o for o in f["directions"]}
    v2.update({(o["direction"], F3.OPPOSITE): dict(o["other_start"], strip_list=[
        {"width_m": w, "length_m": ln} for w, ln in o["other_start"]["strip_list"]]) for o in f["directions"]})
    for x in f["layouts_v3"]:
        o = v2[(x["direction"], x["start"])]
        assert [(s["width_m"], s["length_m"]) for s in x["strips"]] == [(s["width_m"], s["length_m"])
                                                                         for s in o["strip_list"]]
        assert x["upturn_strips"] == 0 and x["patches"] == [] and x["residual_before_m2"] == 0.0
        assert set(x["rolls_by_basis"].values()) == {o["rolls_if_alone"]}
    assert {x["rolls_by_basis"]["Q58_B"] for x in f["layouts_v3"]} == rolls


def test_owner_kitchen_cutting_plan_unchanged():
    """kitchen 3 x 4: along the 4 m wall from the lower wall, 4 strips of 4.40 m (3 x 1.00 + 0.70 wide), 2 per roll ->
    2 rolls, 2.40 m left: released, the same plan as V2.11."""
    a = CP.plan([(0, 0), (4, 0), (4, 3), (0, 3)], floor="GF", room_id="K", name="KITCHEN")
    p = a["purchase"]
    assert (a["state"], p["state"], p["rolls"], p["direction"], p["start"]) == ("COMPUTED", "RELEASED", 2,
                                                                              F3.ALONG_LONG, F3.LOWER)
    assert abs(p["leftover_m"] - 2.40) < 1e-9 and abs(p["strip_length_m"] - 17.60) < 1e-9
    assert [[q["length_m"] for q in r["pieces"]] for r in p["cutting_plan"]] == [[4.4, 4.4], [4.4, 4.4]]
    k = F2.area(floor="GF", room_id="K", polygon=[(0, 0), (4, 0), (4, 3), (0, 3)])
    p11 = AV11.purchase(k["fold"])
    assert (p11["rolls"], p11["leftover_m"], p11["strip_length_m"]) == (p["rolls"], p["leftover_m"],
                                                                        p["strip_length_m"])
    assert "rolls 2 (the same under owner Q-58 A / B / C)" in CP.text_table(a)


# ------------------------------------------------------------------------------------------------ the step
def test_notch_step_upturn_closed_by_an_upturn_only_strip():
    f = F3.fold(NOTCH)
    x = _lay(f, F3.ALONG_LONG, F3.LOWER)
    # V2 leaves the step's upturn uncovered (its own check, without the mitred corner square)
    v2 = [o for o in f["directions"] if o["direction"] == F3.ALONG_LONG][0]
    assert abs(v2["upturn_shortfall_m2"] - 0.38) < 1e-9 and v2["rolls_if_alone"] == 7
    assert abs(x["residual_before_m2"] - 0.40) < 1e-9
    up = [s for s in x["strips"] if s["kind"] == F3.UPTURN_STRIP]
    assert len(up) == 1 and up[0]["band"] == 3 and abs(up[0]["length_m"] - 4.10) < 1e-9
    assert abs(up[0]["need_width_m"] - 0.20) < 1e-9 and abs(up[0]["residual_m2"] - 0.40) < 1e-9
    assert x["residual_after_m2"] == 0.0 and x["patches"] == [] and x["numerical_residual_m2"] < 1e-6
    assert [s["length_m"] for s in x["strips"] if s["kind"] == "MAIN"] == [12.4, 12.4, 12.4, 8.4, 8.4, 8.4]
    assert abs(x["strip_metres"] - (3 * 12.5 + 3 * 8.4 + 4.1)) < 1e-9          # 12.40 = 10.00 + 2.50 spliced
    assert x["rolls_by_basis"] == {"Q58_A": 7, "Q58_B": 8, "Q58_C": 8}
    own = x["counts"]["Q58_A"]["pieces_from_own_offcuts"]
    assert len(own) == 1 and own[0]["offcut"] == "SIDE_TRIM" and abs(own[0]["offcut_w"] - 0.5) < 1e-9
    # the other three layouts meet no step: 7 rolls under every reading -> released at 7
    assert sorted(tuple(sorted(y["rolls_by_basis"].values())) for y in f["layouts_v3"] if y is not x) == [(7, 7, 7)] * 3
    p = CP.purchase(f)
    assert p["state"] == "RELEASED" and p["rolls"] == 7 and p["upturn_only_strips"] == 0
    assert "UPTURN_ONLY_STRIPS_ADDED" in f["flags_v3"] and "ROLLS_DEPEND_ON_Q58" in f["flags_v3"]


@pytest.mark.parametrize("variant", [{"scale": 1000.0}, {"mirror": True}, {"deg": 90.0}, {"deg": 30.0},
                                     {"deg": 90.0, "mirror": True, "scale": 1000.0, "shift": (55.0, -7.0)}])
def test_notch_mirror_rotation_and_units(variant):
    """the notch in millimetres, mirrored, turned 90 or 30 degrees and moved: one layout meets the step, with the
    same 0.40 m2, the same 4.10 m upturn-only strip and 7 / 8 / 8 rolls; the area is released at 7."""
    scale = variant.get("scale", 1.0)
    f = F3.fold(_xf(NOTCH, **variant), unit_m=1.0 / scale)
    st = _step_layouts(f)
    assert len(st) == 1
    x = st[0]
    assert abs(x["residual_before_m2"] - 0.40) < 1e-6 and abs(x["upturn_strip_m"] - 4.10) < 1e-6
    assert x["rolls_by_basis"] == {"Q58_A": 7, "Q58_B": 8, "Q58_C": 8}
    assert all(y["residual_after_m2"] == 0.0 for y in f["layouts_v3"])
    p = CP.purchase(f)
    assert (p["state"], p["rolls"]) == ("RELEASED", 7)


def test_count_that_depends_on_q58_is_held_bounded_never_zero():
    """Fixture H: 9.00 x 4.60 with a 2.00 x 2.00 notch (0,0) (9,0) (9,4.6) (2,4.6) (2,2.6) (0,2.6). Strips across
    the 9.00 m wall, from the opposite wall (x = 9 down): strip k's sheet x 8.20 - 0.90 k .. 9.20 - 0.90 k. Band 7
    (x 1.90 .. 2.90) holds floor up to y 4.60 -> 5.00 m; band 8 (x 1.00 .. 2.00, slab 1.00 .. 1.90) holds only the
    low part -> 3.00 m (y -0.20 .. 2.80). The step edge x = 2.00, y 2.60 .. 4.60 runs parallel to the strips; its
    upturn x 1.80 .. 2.00 is covered by band 7 down to x 1.90 only: x 1.80 .. 1.90, y 2.80 .. 4.80 (with the mitred
    corner) = 0.10 x 2.00 = 0.20 m2 uncovered. Upturn-only strip in band 8: 2.00 + 0.10 end lap (band 8's own strip
    ends at y 2.80) = 2.10 m, need width 0.10 + 0.10 lap = 0.20 m. Main strips 8 x 5.00 + 3 x 3.00 (last 0.40 wide)
    = 49.00 m -> 4 rolls of 2 x 5.00 + 1 roll of 3 x 3.00 = 5 rolls (A: the 0.20 x 2.10 piece from the 0.40 strip's
    0.60 x 3.00 side trim); with the 2.10 m piece from a roll 51.10 m > 50 -> 6 (B, C). Across from the lower wall:
    2 x 3.00 + 9 x 5.00 = 51.00 m -> 6, no step. Fewest: A 5, B 6, C 6 -> HELD, bounded 5 .. 6."""
    f = F3.fold(HELD9)
    x = _lay(f, F3.ACROSS, F3.OPPOSITE)
    assert abs(x["residual_before_m2"] - 0.20) < 1e-9
    up = [s for s in x["strips"] if s["kind"] == F3.UPTURN_STRIP]
    assert len(up) == 1 and abs(up[0]["length_m"] - 2.10) < 1e-9 and abs(up[0]["need_width_m"] - 0.20) < 1e-9
    assert sorted(s["length_m"] for s in x["strips"] if s["kind"] == "MAIN") == [3.0] * 3 + [5.0] * 8
    assert x["rolls_by_basis"] == {"Q58_A": 5, "Q58_B": 6, "Q58_C": 6}
    assert _lay(f, F3.ACROSS, F3.LOWER)["rolls_by_basis"] == {"Q58_A": 6, "Q58_B": 6, "Q58_C": 6}
    p = CP.purchase(f)
    assert p["state"] == "HELD_Q58" and p["rolls"] is None and p["rolls_bounded"] == {"low": 5, "high": 6}
    assert {k: v["rolls"] for k, v in p["rolls_by_reading"].items()} == {"Q58_A": 5, "Q58_B": 6, "Q58_C": 6}
    assert p["cutting_plan_q58_a"]["rolls"] == 5 and len(p["cutting_plan_q58_a"]["pieces_from_own_offcuts"]) == 1
    assert sum(len(r["pieces"]) for r in p["cutting_plan"]) == 11 and len(p["cutting_plan"]) == 6
    # through the arch layer: a bounded rolls line, never 0, the readings named; the total says it is incomplete
    row = F3.area(floor="RF", room_id="R1", polygon=HELD9, name="ROOF")
    row.update(system="ROOFS", line_room_id="RF-ROOF-R1")
    kit = F3.area(floor="GF", room_id="K", polygon=[(0, 0), (4, 0), (4, 3), (0, 3)], roles_lm={"wall": 14.0})
    kit.update(system="WET_AREAS", name_en="Kitchen", name_ar=None)
    t = AV.membrane_table([kit], [{"fold": row, "code": "ROOF", "floor": "RF", "membrane_m2": 1.0}])
    roofs = t["systems"]["ROOFS"]
    assert roofs["purchase_total"]["rolls_to_buy"] is None and roofs["purchase_total"]["complete"] is False
    assert (roofs["purchase_total"]["rolls_with_q58_held_low"], roofs["purchase_total"]["rolls_with_q58_held_high"]) == (5, 6)
    assert roofs["held_q58"] == [{"floor": "RF", "room_id": "R1", "name": "ROOF", "rolls_bounded": {"low": 5, "high": 6}}]
    lines = AV.rolls_lines(CTX, t)
    r = [ln for ln in lines if ln["location"]["room_id"] == "RF-ROOF-R1"]
    assert len(r) == 1 and r[0]["evidence_state"] == "BOUNDED_EXPOSURE" and r[0]["measured_net"] is None
    assert (r[0]["bounded_range"]["low"], r[0]["bounded_range"]["high"]) == (5, 6) and "Q-58" in r[0]["rfi"]["question"]
    k = [ln for ln in lines if ln["location"]["room_id"] == "K"]
    assert len(k) == 1 and k[0]["measured_net"] == 2 and k[0]["evidence_state"] == "SOURCE_DERIVED"
    rows = AV.purchase_rows(t)
    held = [x for x in rows if x["room_id"] == "R1"][0]
    assert held["state"] == "HELD" and held["rolls"] is None and (held["rolls_q58_a"], held["rolls_q58_b"]) == (5, 6)


# ------------------------------------------------------------------------------------------------ patches
def test_opening_crossing_a_band_and_slanted_corner_become_listed_patches():
    """an 8.00 x 5.00 roof with a round opening r 1.50 at (4.00, 2.00) (Q-29: 0.20 m upturn round it) and, separately,
    a room with a 45 degree wall: the residual the straight strips do not reach is a listed patch (m2, size, position),
    never an upturn-only strip; residual after strips and patches 0; the opening patches lie in the opening's 0.20 m
    ring and are less than the whole ring (pi (1.50^2 - 1.30^2) = 1.759 m2 laid flat): the strips that end in the
    opening fold h into it (the rest is the patch)."""
    circ = [(4 + 1.5 * math.cos(2 * math.pi * i / 64), 2 + 1.5 * math.sin(2 * math.pi * i / 64)) for i in range(64)]
    f = F3.fold([(0, 0), (8, 0), (8, 5), (0, 5)], holes=[circ])
    for x in f["layouts_v3"]:
        assert x["upturn_strips"] == 0 and x["residual_after_m2"] == 0.0
        op = [q for q in x["patches"] if q["kind"] == F3.PATCH_OPENING]
        assert op and all(q["m2"] > 0 and q["along_m"] > 0 and q["centre_drawing_units"] for q in op)
        assert 0 < sum(q["m2"] for q in op) < 0.1 * math.pi * (1.5 ** 2 - 1.3 ** 2)
        assert all(1.25 < math.dist(q["centre_drawing_units"], (4, 2)) < 1.5 for q in op)
    g = F3.fold([(0, 0), (5, 0), (5, 2), (3, 4), (0, 4)])           # the 45 degree wall from (5, 2) to (3, 4)
    for x in g["layouts_v3"]:
        assert x["residual_after_m2"] == 0.0
        assert all(q["kind"] == F3.PATCH_OUTLINE for q in x["patches"])
    assert any(x["patches"] for x in g["layouts_v3"])


def test_missing_and_unusable_inputs_are_held_never_zero():
    assert CP.plan(None, room_id="X")["state"] == "HELD"
    assert CP.plan([(0, 0), (1, 0)], room_id="X")["reason"].startswith("OUTLINE_NOT_USABLE")
    h = CP.plan([(0, 0), (4, 0), (4, 3), (0, 3)], spec={"lap_m": None}, room_id="X")
    assert h["state"] == "HELD" and h["purchase"] is None and "never 0" in CP.text_table(h)
    bad = F3.area(floor="GF", room_id="X", polygon=[(0, 0), (1, 1), (0, 1), (1, 0)])
    assert bad["state"] == "HELD" and bad["fold"] is None


def test_cutting_plans_repack_to_the_fold_counts_on_every_fixture():
    """every reading's cutting plan packs to the fold's own count (a code fault otherwise) and Q-58 A never needs more
    rolls than Q-58 B on the same layout."""
    for poly in (NOTCH, HELD9, [(0, 0), (12, 0), (12, 5), (4, 5), (4, 7), (0, 7)]):
        f = F3.fold(poly)
        for x in f["layouts_v3"]:
            assert x["rolls_by_basis"]["Q58_A"] <= x["rolls_by_basis"]["Q58_B"]
            assert x["rolls_by_basis"]["Q58_C"] <= x["rolls_by_basis"]["Q58_B"]
            for b in F3.BASES:
                CP._cutting_plan(x, b, f["spec"])       # raises when the plan does not give the count


def test_v2_12_policy_and_released_v2_11_untouched():
    pr = AV.policy_record()
    assert pr["method"] == "ARCH_TAKEOFF_V2.12" and pr["knowledge"] == "1.7.0" and pr["builds_on"] == "ARCH_TAKEOFF_V2.11"
    assert AV11.METHOD == "ARCH_TAKEOFF_V2.11" and AV11.purchase is not AV.purchase
    from tools import urban_boq_m9 as M9
    assert "ARCH_TAKEOFF_V2.12" in M9.ARCH_METHODS and M9.V212_KNOWLEDGE == "1.7.0"


# ------------------------------------------------------------------------------------------------ end to end
def _t079():
    import importlib.util
    spec = importlib.util.spec_from_file_location("t079_helpers", ROOT / "tests" / "t079_arch_v211" / "test_arch_v211.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.mark.parametrize("variant", [{}, {"deg": 30.0, "mirror": True, "scale": 0.001}])
def test_v2_12_on_a_drawn_roof_changes_only_what_the_fix_reaches(tmp_path, variant):
    """the T-079 synthetic roof (10.40 x 5.40 inside the parapet less the 4.40 x 3.40 block, a skylight r 0.80) run as
    ARCH_TAKEOFF_V2.11 and V2.12 on the same drawing: every BOQ line identical (ids, quantities, states) - its chosen
    layout has no step - and V2.12's rolls line carries the V3 record (7 rolls, the same under all three Q-58
    readings, the skylight's uncovered ring listed as patches)."""
    T = _t079()
    dxf = T._roof_plan(tmp_path / "roof.dxf", **variant)
    r11, a11 = T._run(dxf, "ARCH_TAKEOFF_V2.11", layer_roles=T.ROLES)
    r12, a12 = T._run(dxf, "ARCH_TAKEOFF_V2.12", layer_roles=T.ROLES)
    q11 = {T._key(x): (x["measured_net"], x["evidence_state"]) for x in r11["lines"]}
    q12 = {T._key(x): (x["measured_net"], x["evidence_state"]) for x in r12["lines"]}
    assert q11 == q12
    assert a12["run"]["policy"] == "URBAN_BOQ_T096_ARCH_V2_12" and "v2_12" in a12["run"]
    assert a11["run"]["policy"] == "URBAN_BOQ_T079_ARCH_V2_11" and "v2_12" not in a11["run"]
    rl = [x for x in r12["lines"] if x["item_code"] == "FIN.WP.MEMBRANE_ROLLS" and x["evidence_state"] == "SOURCE_DERIVED"]
    assert len(rl) == 1 and rl[0]["measured_net"] == 7
    inp = rl[0]["calculation"]["inputs"]
    assert inp["method"] == "MEMBRANE_FOLD_V3" and {v["rolls"] for v in inp["rolls_by_reading"].values()} == {7}
    p = a12["v211"]["membrane_table"]["systems"]["ROOFS"]["rows"][0]["purchase"]
    assert p["residual_after_m2"] == 0.0 and all(q["kind"] in (F3.PATCH_OPENING, F3.PATCH_OUTLINE)
                                                 for q in p["patches"])


def test_v2_12_writes_its_own_membrane_files(tmp_path):
    T = _t079()
    from tools import urban_boq_m9 as M9
    dxf = T._roof_plan(tmp_path / "roof.dxf")
    _r12, a12 = T._run(dxf, "ARCH_TAKEOFF_V2.12", layer_roles=T.ROLES)
    files = M9.v21_files(a12)
    assert "MEMBRANE_TABLE_V2_12.json" in files and "MEMBRANE_PURCHASE_V2_12.csv" in files
    assert "MEMBRANE_TABLE_V2_11.json" not in files
    head = files["MEMBRANE_PURCHASE_V2_12.csv"].splitlines()[0]
    assert "rolls_q58_a" in head and "patch_m2" in head
