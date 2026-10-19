"""T-079: ARCH_TAKEOFF_V2.11 = ARCH_TAKEOFF_V2.10 + the verified waterproofing pieces wired into the released route
(engine/source/arch_v211.py, tools/urban_boq_m9.py, knowledge registry 1.7.0). Synthetic drawings only (no client
drawing, not Alsenan); every expected value is a hand calculation from the drawn coordinates below.

WET (tools/arch_synth villa, the GF BATH face 9.40..12.20 x 0.20..2.60 m relabelled, a WASH BASIN block inside):
  space 2.80 x 2.40 = 6.72 m2; boundary 2 x (2.80 + 2.40) = 10.40 m; its door 0.80 m (LIVING | space) is not a wall;
  its 0.60 m window is a sill wall (UP-WP-003 eligible) -> walls-only upturn 10.40 - 0.80 = 9.60 lm = 1.92 m2 (x 0.20).
  Under V2.10 the space is a review space (a basin alone never types a space, UP-WET-002): no wet line, a conditional
  set. Under V2.11 the label "HAND WASH" (owner Q-06 a: wet) decides it: the wet scope is released.
  The villa's other wet areas: GF KITCHEN 2.80 x 6.40 (one 0.90 door; upturn 18.40 - 0.90 = 17.50 lm), 1F BATH 2.80 x
  2.40 (one 0.80 door). Doors of wet areas: 3, none shared -> 3 transition lines (owner Q-35 C).
  Strips (owner Q-30 method, roll 1.00 x 10.00, lap 0.10, upturn 0.20; n = ceil((span + 0.40 - 1.00) / 0.90) + 1):
    2.80 x 2.40 along the 2.80 wall: span 2.40 -> 3 strips of 3.20 m; across: span 2.80 -> 4 strips of 2.80 m
    2.80 x 6.40 along the 6.40 wall: span 2.80 -> 4 strips of 6.80 m; across: span 6.40 -> 8 strips of 3.20 m
  rolls packed by length (10 m):
    all along   : 6 x 3.20 + 4 x 6.80 (46.40 m) -> 4 rolls of 6.80 + 3.20, 1 roll of 2 x 3.20 = 5
    all across  : 8 x 2.80 + 8 x 3.20 (48.00 m) -> at most 3 pieces fit a roll (4 x 2.80 = 11.20 > 10) -> 16 / 3 = 6
    each room on its shorter roll length: 3.20 x 3 + 3.20 x 8 (kitchen across 25.60 < 27.20) + 3.20 x 3 -> 14 pieces
      of 3.20 m, 3 per roll -> 5
  -> the rolls line is HELD (owner Q-49 open): low 5, high 6, every count shown, none selected.
ROOF (a plan of its own; T-062 geometry, here drawn closed): block 0..4.40 x 0..3.40 m (0.20 m walls) with a BEDROOM;
  parapet inner face x -3.00 .. 7.40, y -2.00 .. 3.40 m meeting the block's wall at its north corners; a skylight circle
  r = 0.80 m labelled SKYLIGHT (owner Q-29: an opening with a 0.20 m upturn round it).
  membrane = 10.40 x 5.40 - 4.40 x 3.40 - pi x 0.80^2 = 56.16 - 14.96 - 2.0106 = 39.1894 m2 (owner Q-24 inside the parapet)
  upturn   = parapet 3.00 + 5.40 + 10.40 + 5.40 + 3.00 = 27.20 + block walls 3.40 + 4.40 + 3.40 = 11.20
             + skylight 2 x pi x 0.80 = 5.0265 -> 43.4265 lm
  With a 1.00 m gap in the parapet (more than a wall thickness: no closure found) the roof is HELD, never 0.
Variants: mirrored, a quarter turn, rotated 30 degrees, drawing units metres."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v211 as AV                     # noqa: E402
from engine.source import knowledge as K                      # noqa: E402
from engine.source import membrane_fold_v2 as F               # noqa: E402
from tools import arch_synth as AS                            # noqa: E402
from tools import urban_boq_m9 as M9                          # noqa: E402

V210, V211 = "ARCH_TAKEOFF_V2.10", "ARCH_TAKEOFF_V2.11"
QUANT = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
SPACE_M2 = 2.80 * 2.40                                       # 6.72
SPACE_UPTURN_LM = 2 * (2.80 + 2.40) - 0.80                   # 9.60
ROOF_M2 = 10.40 * 5.40 - 4.40 * 3.40 - math.pi * 0.80 ** 2  # 39.1894
ROOF_UP_LM = 27.20 + 11.20 + 2 * math.pi * 0.80            # 43.4265
CTX = {"project_id": "synthetic", "revision_set_sha256": "0" * 64, "documents": [{"file": "x.dxf", "sha256": "0"}]}


# ------------------------------------------------------------------------------------------------ drawings
def _metres(src, dst):
    import ezdxf
    from ezdxf.math import Matrix44
    doc = ezdxf.readfile(str(src))
    doc.header["$INSUNITS"] = 6
    for e in doc.modelspace():
        e.transform(Matrix44.scale(0.001, 0.001, 0.001))
    doc.saveas(str(dst))
    return dst


def _villa(path, *, word, blocks=("WASH BASIN",), mirror=False, quarter_turns=0, metres=False):
    """the synthetic villa, its GF BATH face relabelled `word`, a fixture block per name in `blocks` inside it."""
    import ezdxf
    mm = path.with_suffix(".mm.dxf")
    with mock.patch.dict(AS.GF_WORDS, {"BATH": word}):
        AS.villa(mm, mirror=mirror, quarter_turns=quarter_turns)
    doc = ezdxf.readfile(str(mm))
    xs, ys = [p[0] for p in AS.GF_OUTER], [p[1] for p in AS.GF_OUTER]
    centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    for i, name in enumerate(blocks):
        b = doc.blocks.new(name)
        b.add_lwpolyline([(0, 0), (400, 0), (400, 300), (0, 300)], close=True)
        p = AS._xf((10000 + 900 * i, 1900), AS.FRAMES["GF"][2], 0, 0, mirror, quarter_turns, centre)
        doc.modelspace().add_blockref(name, p, dxfattribs={"layer": "A-SANI", "rotation": 90 * quarter_turns})
    doc.saveas(str(mm))
    return _metres(mm, path) if metres else mm


def _roof_plan(path, *, deg=0.0, mirror=False, scale=1.0, gap=False):
    import ezdxf
    c = (2200.0, 1700.0)

    def xf(p):
        x, y = p
        if mirror:
            x = 2 * c[0] - x
        a = math.radians(deg)
        dx, dy = x - c[0], y - c[1]
        return ((c[0] + dx * math.cos(a) - dy * math.sin(a)) * scale, (c[1] + dx * math.sin(a) + dy * math.cos(a)) * scale)
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4 if scale == 1.0 else 6
    msp = doc.modelspace()

    def poly(pts, layer):
        for a, b in zip(pts, pts[1:]):
            msp.add_line(xf(a), xf(b), dxfattribs={"layer": layer})
    box = [(-12000, -12000), (18000, -12000), (18000, 14000), (-12000, 14000)]
    msp.add_lwpolyline([(x * scale, y * scale) for x, y in box], close=True, dxfattribs={"layer": "A-FRAME"})
    msp.add_text("GROUND FLOOR PLAN", dxfattribs={"layer": "A-TITLE", "height": 500 * scale}).set_placement(
        (-10000 * scale, -11000 * scale))
    poly([(0, 0), (4400, 0), (4400, 3400), (0, 3400), (0, 0)], "A-WALL")
    poly([(200, 200), (4200, 200), (4200, 3200), (200, 3200), (200, 200)], "A-WALL")
    if gap:          # the west parapet stops 1.00 m short: (-3000, 400) .. (-3000, 1400) open
        poly([(0, 3400), (-3000, 3400), (-3000, 1400)], "A-ROOF")
        poly([(-3000, 400), (-3000, -2000), (7400, -2000), (7400, 3400), (4400, 3400)], "A-ROOF")
    else:
        poly([(0, 3400), (-3000, 3400), (-3000, -2000), (7400, -2000), (7400, 3400), (4400, 3400)], "A-ROOF")
    poly([(-100, 3650), (-3250, 3650), (-3250, -2250), (7650, -2250), (7650, 3650), (4500, 3650)], "A-ROOF")
    msp.add_circle(xf((-1500, 0)), 800 * scale, dxfattribs={"layer": "A-ROOF"})
    for txt, p in (("BEDROOM", (2200, 1700)), ("ROOF", (2200, -1000)), ("SKYLIGHT", (-1500, 0))):
        msp.add_text(txt, dxfattribs={"layer": "A-TEXT", "height": 150 * scale}).set_placement(xf(p))
    doc.saveas(str(path))
    return path


ROLES = {"A-WALL": "WALL", "A-ROOF": "OTHER", "A-TEXT": "OTHER", "A-FRAME": "OTHER", "A-TITLE": "OTHER"}


def _run(dxf, method, **kw):
    try:
        room, arch = M9.arch_compute(str(dxf), method=method, **kw)[:2]
    except M9.CompletenessFailed as ex:
        room, arch = ex.room_boq, ex.arch
    return room, arch


def _space(arch):
    rs = [r for r in arch["rooms"] if r["floor"] == "GF" and abs(r["area_m2"] - SPACE_M2) < 1e-6]
    assert len(rs) == 1, [(r["floor"], r["area_m2"]) for r in arch["rooms"]]
    return rs[0]


def _lines_at(room, rid):
    return {(ln["item_code"], ln["physical_element"]): ln for ln in room["lines"]
            if (ln.get("location") or {}).get("room_id") == rid}


def _qty(lines, item):
    xs = [ln for (code, _e), ln in lines.items() if code == item]
    assert len(xs) == 1, (item, list(lines))
    return xs[0]["measured_net"] if xs[0]["evidence_state"] in QUANT else None


def _sets(arch):
    return [s["set_id"] for s in arch["release_report"]["categories"]["CONDITIONAL"]["scenario_sets"]]


def _key(ln):
    loc = ln["location"]
    return (ln["item_code"], loc.get("floor"), loc.get("room_id"), loc.get("element_id"), ln["unit"])


# ------------------------------------------------------------------------------------------------ wet areas
@pytest.mark.parametrize("variant", [{}, {"mirror": True}, {"quarter_turns": 1}, {"metres": True}])
def test_review_space_decided_wet_by_label_releases_the_wet_scope(tmp_path, variant):
    dxf = _villa(tmp_path / "hw.dxf", word="HAND WASH", **variant)
    room, arch = _run(dxf, V211)
    sp = _space(arch)
    rid = sp["room_id"]
    assert arch["v211"]["decided"] == {rid: "WET_SCOPE"}
    assert arch["v211"]["classes"][rid]["class"] == "WET" and arch["v211"]["classes"][rid]["reason"] == "LABEL_WET"
    L = _lines_at(room, rid)
    assert abs(_qty(L, "FIN.WP.FLOOR") - SPACE_M2) < 1e-6
    assert abs(_qty(L, "FIN.WP.WALL_UPTURN") - SPACE_UPTURN_LM * 0.20) < 1e-6
    assert abs(_qty(L, "FIN.FLOOR.WET_TILE") - SPACE_M2) < 1e-6
    assert all("DECIDED_BY_EVIDENCE" in (ln.get("notes") or "") for (c, _e), ln in L.items()
               if c in ("FIN.WP.FLOOR", "FIN.FLOOR.WET_TILE"))
    assert not any(s.startswith("REVIEW_CLASSIFICATION") for s in _sets(arch))
    assert arch["release_report"]["conservation"]["every_line_once"]
    # the membrane table row of the space (owner strip method)
    row = [x for x in arch["v211"]["membrane_table"]["systems"]["WET_AREAS"]["rows"] if x["room_id"] == rid][0]
    assert abs(row["floor_m2"] - SPACE_M2) < 1e-6 and abs(row["upturn_walls_lm"] - SPACE_UPTURN_LM) < 1e-6
    assert sorted((d["strips"], round(d["roll_length_used_m"], 4)) for d in row["directions"]) == [(3, 9.6), (4, 11.2)]
    # 3 doors of wet areas, one line each; the rolls line held with every layout's count
    tr = [ln for ln in room["lines"] if ln["item_code"] == "FIN.WP.DOORWAY_TRANSITION_NR"]
    assert len(tr) == 3 and all(ln["measured_net"] == 1 and ln["unit"] == "pcs" for ln in tr)
    rolls = [ln for ln in room["lines"] if ln["item_code"] == "FIN.WP.MEMBRANE_ROLLS"]
    assert len(rolls) == 1 and rolls[0]["measured_net"] is None and rolls[0]["evidence_state"] == "BOUNDED_EXPOSURE"
    assert (rolls[0]["bounded_range"]["low"], rolls[0]["bounded_range"]["high"]) == (5, 6)
    by = rolls[0]["calculation"]["inputs"]["by_layout"]
    assert {k: v["rolls_to_buy"] for k, v in by.items()} == {"ALL_ALONG_LONGEST_WALL": 5,
                                                              "ALL_ACROSS_LONGEST_WALL": 6,
                                                              "EACH_ROOM_LESS_ROLL_LENGTH": 5}
    assert rolls[0]["calculation"]["inputs"]["selected"] is None
    assert "Q-49" in rolls[0]["rfi"]["question"]
    if not variant:
        # V2.10 on the same drawing: the space stays under review, and every V2.10 line other than the space's own
        # and the added items is in V2.11 with the same quantity and state (nothing else moves)
        r10, a10 = _run(dxf, V210)
        rid10 = _space(a10)["room_id"]
        assert rid10 == rid and "FIN.WP.FLOOR" not in {c for c, _e in _lines_at(r10, rid10)}
        assert f"REVIEW_CLASSIFICATION:GF:{rid}" in _sets(a10)
        new = {_key(ln): (ln["measured_net"], ln["evidence_state"]) for ln in room["lines"]}
        for ln in r10["lines"]:
            if ln["location"].get("room_id") == rid:
                continue
            assert new.get(_key(ln)) == (ln["measured_net"], ln["evidence_state"]), _key(ln)
        assert a10["run"]["method"] == V210 and "v2_11" not in a10["run"] and "v211" not in a10


def test_unlabelled_space_without_evidence_stays_in_review(tmp_path):
    """no label, a basin and a washing machine: which wet room it is is not established (WET_DRY_NOT_ESTABLISHED,
    Q-13 B) -> the review stays, no wet line is released, nothing is 0."""
    dxf = _villa(tmp_path / "wm.dxf", word="X1", blocks=("WASH BASIN", "WASHING MACHINE"))
    room, arch = _run(dxf, V211)
    sp = _space(arch)
    rid = sp["room_id"]
    c = arch["v211"]["classes"][rid]
    assert c["class"] == "HELD", c
    assert rid not in arch["v211"]["decided"]
    L = _lines_at(room, rid)
    assert not {code for code, _e in L} & {"FIN.WP.FLOOR", "FIN.FLOOR.WET_TILE", "FIN.WALL.TILE"}
    tr = [ln for ln in room["lines"] if ln["item_code"] == "FIN.WP.DOORWAY_TRANSITION_NR"]
    assert len(tr) == 2                                   # the kitchen and the 1F bath only
    sets = _sets(arch)
    if sp.get("issue", "").startswith("WET_CLASSIFICATION_REVIEW"):
        assert f"REVIEW_CLASSIFICATION:GF:{rid}" in sets


def test_decide_review_closes_only_wet_or_dry():
    tg = [{"room_id": r, "plausible": [{"scenario": "WET_SCOPE"}, {"scenario": "DRY_SCOPE"}]} for r in "ABCD"]
    tg.append({"room_id": "E", "plausible": []})
    cl = {"A": {"class": "WET"}, "B": {"class": "DRY"}, "C": {"class": "HELD"}, "D": {"class": "NONE"},
          "E": {"class": "WET"}}
    assert AV.decide_review(tg, cl) == {"A": "WET_SCOPE", "B": "DRY_SCOPE"}


# ------------------------------------------------------------------------------------------------ door transitions
def _row(fid, rid, poly, doors, roles):
    r = F.area(floor=fid, room_id=rid, polygon=poly, roles_lm=roles, doors=doors)
    r.update(system="WET_AREAS", name_en=rid, name_ar=None)
    return r


def test_door_transitions_one_per_door_shared_door_once():
    """a W.C. (1.20 x 1.50) opening into a wash lobby (2.00 x 1.50) by OP-1 (0.80), the lobby to the hall by OP-2
    (0.90), plus a 0.70 door edge on the W.C. ring that no opening lists: 2 doors released (OP-1 once, naming both
    areas), the unlisted edge held."""
    wc = _row("GF", "WC", [(0, 0), (1.2, 0), (1.2, 1.5), (0, 1.5)], [{"opening_id": "OP-1", "width_m": 0.8}],
              {"wall": 5.4 - 0.8 - 0.7, "door": 0.8 + 0.7})
    lobby = _row("GF", "LOBBY", [(1.4, 0), (3.4, 0), (3.4, 1.5), (1.4, 1.5)],
                 [{"opening_id": "OP-1", "width_m": 0.8}, {"opening_id": "OP-2", "width_m": 0.9}],
                 {"wall": 7.0 - 1.7, "door": 1.7})
    out = AV.door_transition_lines(CTX, [wc, lobby], lambda x: {"name_en": x["name_en"], "name_ar": None})
    rel = [ln for ln in out if ln["evidence_state"] == "SOURCE_DERIVED"]
    held = [ln for ln in out if ln["evidence_state"] == "BLOCKED_RFI"]
    assert sorted(ln["calculation"]["inputs"]["opening_id"] for ln in rel) == ["OP-1", "OP-2"]
    op1 = [ln for ln in rel if ln["calculation"]["inputs"]["opening_id"] == "OP-1"][0]
    assert op1["calculation"]["inputs"]["wet_areas"] == ["LOBBY", "WC"] and op1["measured_net"] == 1
    assert len(held) == 1 and held[0]["measured_net"] is None and abs(held[0]["calculation"]["inputs"]["width_m"] -
                                                                      0.7) < 1e-9
    assert len({ln["line_id"] for ln in out}) == len(out)


# ------------------------------------------------------------------------------------------------ membrane table
def test_membrane_table_owner_kitchen_example():
    """owner Q-30: kitchen 3 x 4 m, one 0.90 m door: along the 4 m wall 4 strips (0.80 + 0.90 + 0.90 + 0.40 m of
    floor), each 4.00 + 0.20 + 0.20 = 4.40 m long; cut 3 x 1.00 x 4.40 + 0.70 x 4.40 = 16.28 m2; 2 rolls (2 x 4.40 per
    roll). Across the 4 m span: n = ceil((4.00 + 0.40 - 1.00) / 0.90) + 1 = 5 strips (0.80 + 3 x 0.90 + 0.50 of floor),
    each 3.00 + 0.40 = 3.40 m; cut 4 x 3.40 + 0.80 x 3.40 = 16.32 m2; 17.00 m of roll, 2 x 3.40 per roll -> 3 rolls.
    Floor 12.00 m2, walls-only upturn 14.00 - 0.90 = 13.10 lm (Q-35 C)."""
    k = _row("GF", "KITCHEN", [(0, 0), (4, 0), (4, 3), (0, 3)], [{"opening_id": "OP-9", "width_m": 0.9}],
             {"wall": 13.1, "door": 0.9})
    t = AV.membrane_table([k], [])
    row = t["systems"]["WET_AREAS"]["rows"][0]
    assert abs(row["floor_m2"] - 12.0) < 1e-9 and abs(row["upturn_walls_lm"] - 13.1) < 1e-9
    d = {x["direction"]: x for x in row["directions"]}
    assert d[F.ALONG_LONG]["strips"] == 4 and abs(d[F.ALONG_LONG]["cut_m2"] - 16.28) < 1e-6
    assert d[F.ALONG_LONG]["rolls_if_alone"] == 2
    assert d[F.ACROSS]["strips"] == 5 and abs(d[F.ACROSS]["cut_m2"] - 16.32) < 1e-6
    assert d[F.ACROSS]["rolls_if_alone"] == 3
    assert t["systems"]["ROOFS"]["project"] is None
    assert "a total across membrane systems (UP-WP-MAT-001)" in t["never"]


def test_rolls_line_held_with_every_layout_count():
    """the kitchen above and the owner's 3 x 3 m bathroom (either way 4 strips of 3.40 m): every layout's count is
    shown in the line, none selected, the line held with the range."""
    k = _row("GF", "KITCHEN", [(0, 0), (4, 0), (4, 3), (0, 3)], [], {"wall": 14.0})
    b = _row("GF", "BATH", [(5, 0), (8, 0), (8, 3), (5, 3)], [], {"wall": 12.0})
    t = AV.membrane_table([k, b], [])
    sets = t["systems"]["WET_AREAS"]["project"]["direction_sets"]
    # hand packing by length, 10 m rolls:
    #   all along : 4 x 4.40 + 4 x 3.40 -> (4.40, 4.40), (4.40, 4.40), (3.40, 3.40), (3.40, 3.40) = 4 (no roll takes 3)
    #   all across: 5 x 3.40 + 4 x 3.40 = 9 x 3.40 -> 2 per roll (3 x 3.40 = 10.20 > 10) = 5
    #   each room on its shorter roll length: kitchen across (17.00 < 17.60), bath 13.60 either way -> 9 x 3.40 = 5
    assert {n: s["rolls_to_buy"] for n, s in sets.items()} == {"ALL_ALONG_LONGEST_WALL": 4,
                                                               "ALL_ACROSS_LONGEST_WALL": 5,
                                                               "EACH_ROOM_LESS_ROLL_LENGTH": 5}
    lines = AV.rolls_lines(CTX, t)
    assert len(lines) == 1
    ln = lines[0]
    assert ln["evidence_state"] == "BOUNDED_EXPOSURE" and ln["measured_net"] is None
    assert (ln["bounded_range"]["low"], ln["bounded_range"]["high"]) == (4, 5)
    assert ln["calculation"]["inputs"]["selected"] is None and ln["unit"] == "pcs"


# ------------------------------------------------------------------------------------------------ roofs
@pytest.mark.parametrize("variant", [{}, {"scale": 0.001}, {"deg": 30.0}, {"mirror": True},
                                     {"deg": 30.0, "mirror": True, "scale": 0.001}])
def test_roof_with_skylight_released_like_a_bathroom(tmp_path, variant):
    dxf = _roof_plan(tmp_path / "roof.dxf", **variant)
    room, arch = _run(dxf, V211, layer_roles=ROLES)
    roofs = [r for r in arch["v211"]["roofs"] if r["code"] == "ROOF"]
    assert len(roofs) == 1 and roofs[0]["status"] == "RELEASED_METHOD_PIECE", roofs
    m = [ln for ln in room["lines"] if ln["item_code"] == "FIN.WP.ROOF"]
    u = [ln for ln in room["lines"] if ln["item_code"] == "FIN.WP.ROOF_UPTURN"]
    assert len(m) == 1 and m[0]["evidence_state"] == "SOURCE_DERIVED" and abs(m[0]["measured_net"] - ROOF_M2) < 0.01
    assert len(u) == 1 and u[0]["unit"] == "lm" and abs(u[0]["measured_net"] - ROOF_UP_LM) < 0.01
    assert abs(u[0]["calculation"]["inputs"]["upturn_round_openings_lm"] - 2 * math.pi * 0.80) < 0.01
    tbl = arch["v211"]["membrane_table"]["systems"]["ROOFS"]
    assert len(tbl["rows"]) == 1 and abs(tbl["rows"][0]["floor_m2"] - ROOF_M2) < 0.01
    rolls = [ln for ln in room["lines"] if ln["item_code"] == "FIN.WP.MEMBRANE_ROLLS"
             and ln["calculation"]["inputs"]["system"] == "ROOFS"]
    assert len(rolls) == 1 and rolls[0]["measured_net"] is None


def test_roof_without_closing_layer_is_held_never_zero(tmp_path):
    dxf = _roof_plan(tmp_path / "gap.dxf", gap=True)
    room, arch = _run(dxf, V211, layer_roles=ROLES)
    m = [ln for ln in room["lines"] if ln["item_code"] == "FIN.WP.ROOF"]
    assert len(m) == 1 and m[0]["evidence_state"] == "BLOCKED_RFI" and m[0]["measured_net"] is None
    assert m[0]["rfi"]["question"]
    assert not [ln for ln in room["lines"] if ln["item_code"] == "FIN.WP.ROOF_UPTURN"]
    assert arch["v211"]["membrane_table"]["systems"]["ROOFS"]["project"] is None


# ------------------------------------------------------------------------------------------------ registry 1.7.0
def test_registry_1_7_is_the_builder_output_and_validates():
    p = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "kb_build_1_7.py"), "--check"],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    with K.using("1.7.0"):
        reg = K.registry()
    assert K.validate(reg, links=True) == []


def test_registry_1_7_is_1_5_plus_the_answers_only():
    with K.using("1.5.0"):
        r15 = K.registry()
    with K.using("1.7.0"):
        r17 = K.registry()
        std = K.wp_standard()
    old = {r["rule_id"]: r for r in r15["rules"]}
    new = {r["rule_id"]: r for r in r17["rules"]}
    assert set(old) == set(new)
    assert {k for k in old if old[k] != new[k]} == {"UP-WET-001", "UP-WP-003", "UP-WP-ROOF-001", "UP-WP-LAY-001"}
    for k in ("UP-WET-001", "UP-WP-003", "UP-WP-ROOF-001", "UP-WP-LAY-001"):
        lg = {x: y for x, y in new[k]["logic"].items() if x not in ("owner_answers_1_7_0", "state_1_7_0")}
        assert lg == old[k]["logic"] and new[k]["status"] == old[k]["status"]
    assert std == {"roll_width_m": 1.0, "roll_length_m": 10.0, "gross_roll_area_m2": 10.0, "lap_m": 0.1,
                   "upturn_h_m": 0.2}
    assert r17["owner_questions"] == r15["owner_questions"]
    assert M9.V211_KNOWLEDGE == "1.7.0" and M9.V210_KNOWLEDGE == "1.5.0" and K.version() == "1.0.0"
    assert json.loads((ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.7.0.json").read_text(encoding="utf-8"))[
        "base"]["version"] == "1.5.0"
