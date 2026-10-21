"""T-071: EXTERIOR_SPACES_V1 on hand-calculated synthetic plans (not Alsenan; layer names unlike any project).

Hand truth, metres, before the variant transform (scale to mm, rotation 37 deg, mirror):
  building  A-WALL outer face of a 4.40 x 3.40 block, x 0 .. 4.40, y 0 .. 3.40 (one closed ring here: the room builder's
            boundary items are what the trace sees).
  roof      parapet inner face on A-ROOF round three sides of the block: x -3.00 .. 7.40, y -2.00 .. 3.40; both inner
            parapet lines stop 0.10 m short of the block (drafting gap, owner Q-25: closed and listed); outer parapet
            line 0.25 m outside (band measured, B for review only).
            A filled = 10.40 x 5.40 - 4.40 x 3.40 = 56.16 - 14.96 = 41.200 m2
            dome circle r 0.80 inside: pi 0.64 = 2.011 m2 -> A net = 39.189 m2
            A perimeter: parapet 2.90 + 5.40 + 10.40 + 5.40 + 2.90 = 27.00, building 3.40 + 4.40 + 3.40 = 11.20,
            closures 2 x 0.10 = 0.20 -> 38.40 m; dome ring 2 pi 0.80 = 5.027 m
            labelled dome (opening, owner Q-24 / Q-29): membrane 39.189 m2, upturn 38.40 + 5.027 = 43.427 m,
            43.427 x 0.20 = 8.685 m2; unlabelled circle: membrane 39.189, held part 2.011 m2, upturn 38.40 m
            B = 10.90 x 5.90 - 4.40 x 3.65 - 2.011 = 64.31 - 16.06 - 2.011 = 46.239 m2
  balcony   A-RAIL closed 3.00 x 1.50 m outside the block at x 10 .. 13, y 5 .. 6.5: membrane 4.500 m2 PROVISIONAL,
            perimeter 9.00 m, upturn HELD by specification
  pool      A-ROOF D shape: 1.00 x 2.00 rectangle + half circle r 1.00 -> 2.000 + pi / 2 = 3.571 m2: HELD (no rule)
  void      A-VOID 1.50 x 1.00 = 1.500 m2: UNSUPPORTED
  terrace   a TERRACE label with no line round it: HELD NO_CLOSING_LAYER, no area (never 0)
"""
from __future__ import annotations

import math

import pytest

from engine.source import exterior_spaces as XS

PI = math.pi
HAND = {"A_filled": 41.2, "dome": PI * 0.64, "A_net": 41.2 - PI * 0.64, "perim": 38.4, "own": 27.0, "bld": 11.2,
        "clos": 0.2, "ring": 2 * PI * 0.8, "B": 64.31 - 16.06 - PI * 0.64}
VARIANTS = {"m": dict(scale=1.0), "mm": dict(scale=1000.0), "rot37": dict(scale=1000.0, deg=37.0),
            "mirror": dict(scale=1000.0, mirror=True), "rot37_mirror_m": dict(scale=1.0, deg=37.0, mirror=True)}
C0 = (2.2, 1.7)


class P:
    def __init__(self, scale=1.0, deg=0.0, mirror=False):
        self.k, self.a, self.m = scale, math.radians(deg), mirror

    def __call__(self, x, y):
        if self.m:
            x = 2 * C0[0] - x
        dx, dy = x - C0[0], y - C0[1]
        x, y = C0[0] + dx * math.cos(self.a) - dy * math.sin(self.a), C0[1] + dx * math.sin(self.a) + dy * math.cos(self.a)
        return x * self.k, y * self.k

    def ang(self, t):                   # an angle of the source plan in the transformed plan
        if self.m:
            t = PI - t
        return t + self.a

    @property
    def unit_m(self):
        return 1.0 / self.k


def segs(p, pts, lid, role="OWN"):
    out = []
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        (x1, y1), (x2, y2) = p(*a), p(*b)
        out.append((f"{lid}:{i}", "SEGMENT", (x1, y1, x2, y2), role))
    return out


def arc(p, cx, cy, r, t0, t1, sid):
    a0, a1 = p.ang(t0), p.ang(t1)
    if p.m:
        a0, a1 = a1, a0
    while a1 <= a0:
        a1 += 2 * PI
    x, y = p(cx, cy)
    return (sid, "ARC", (x, y, r * p.k, a0, a1), "OWN")


def circle(p, cx, cy, r, sid):
    x, y = p(cx, cy)
    return (sid, "CIRCLE", (x, y, r * p.k), "OWN")


def plan(p, dome_label=True, door_on_gap=False):
    building = segs(p, [(0, 0), (4.4, 0), (4.4, 3.4), (0, 3.4), (0, 0)], "W", "WALL")
    roof = segs(p, [(-0.1, 3.4), (-3.0, 3.4), (-3.0, -2.0), (7.4, -2.0), (7.4, 3.4), (4.5, 3.4)], "R")
    roof += segs(p, [(-0.1, 3.65), (-3.25, 3.65), (-3.25, -2.25), (7.65, -2.25), (7.65, 3.65), (4.5, 3.65)], "RO")
    roof += [circle(p, -1.5, 0.0, 0.8, "DOME1")]
    roof += segs(p, [(10.0, -1.0), (11.0, -1.0), (11.0, 1.0), (10.0, 1.0)], "PL")
    roof += [arc(p, 10.0, 0.0, 1.0, PI / 2, 3 * PI / 2, "PLA")]
    layers = {"A-ROOF": roof,
              "A-VOID": segs(p, [(-9.0, 0.0), (-7.5, 0.0), (-7.5, 1.0), (-9.0, 1.0), (-9.0, 0.0)], "V"),
              "A-RAIL": segs(p, [(10.0, 5.0), (13.0, 5.0), (13.0, 6.5), (10.0, 6.5), (10.0, 5.0)], "BL")}
    texts = [("T1", "ROOF", 2.2, -1.0), ("T2", "ROOF", 6.0, 1.5), ("T3", "SWIMMING POOL", 10.3, 0.0),
             ("T4", "VOID", -8.25, 0.5), ("T5", "TERRACE", 12.5, 9.0), ("T6", "BALCONY", 11.5, 5.75)]
    if dome_label:
        texts.append(("T7", "DOME", -1.5, 0.0))
    texts = [{"id": i, "value": v, "x": p(x, y)[0], "y": p(x, y)[1]} for i, v, x, y in texts]
    openings = []
    if door_on_gap:                     # a gate drawn across the west gap: the gap must not be closed
        (x1, y1), (x2, y2) = p(-0.1, 3.3), p(0.0, 3.5)
        openings.append({"id": "GATE1", "kind": "GATE", "segment": (x1, y1, x2, y2)})
    return building, layers, texts, openings


def run(p, **kw):
    b, layers, texts, ops = plan(p, **{k: v for k, v in kw.items() if k in ("dome_label", "door_on_gap")})
    labels = [t for t in texts if t["value"] != "DOME"]
    return XS.trace(labels, b, layers, kw.get("unit_m", p.unit_m), openings=ops, texts=texts)


def by_code(out):
    d = {}
    for r in out["records"]:
        d.setdefault(r["code"], []).append(r)
    return d


@pytest.mark.parametrize("name", list(VARIANTS))
def test_roof_hand_values_every_variant(name):
    p = P(**VARIANTS[name])
    d = by_code(run(p))
    r1, r2 = d["ROOF"]
    assert r1["status"] == "RELEASED_METHOD_PIECE" and r1["geometry_status"] == "CLOSED"
    c = r1["candidates"]["A-ROOF"]
    assert abs(c["A_filled_m2"] - HAND["A_filled"]) < 0.005
    assert abs(c["A_net_m2"] - HAND["A_net"]) < 0.005
    assert abs(c["A_perimeter_lm"]["own_layer_edge"] - HAND["own"]) < 0.005
    assert abs(c["A_perimeter_lm"]["building"] - HAND["bld"]) < 0.005
    assert abs(c["A_perimeter_lm"]["closure"] - HAND["clos"]) < 0.005
    assert sorted(x["length_m"] for x in c["closures"]) == [0.1, 0.1]
    assert all(set(x["meets"]) == {"WALL"} for x in c["closures"])
    assert abs(r1["membrane_m2"] - HAND["A_net"]) < 0.005
    assert abs(r1["upturn_lm"] - (HAND["perim"] + HAND["ring"])) < 0.005
    assert abs(r1["upturn_m2"] - 0.2 * (HAND["perim"] + HAND["ring"])) < 0.002
    assert r1["held_part_m2"] is None
    assert [s["treatment"] for s in c["inner_shapes"]] == ["OPENING"]
    assert c["B_review_only"]["band_width_m"] == 0.25 and abs(c["B_review_only"]["area_m2"] - HAND["B"]) < 0.01
    assert len(r1["gap_cover"]) == 2 and all(g["lap_m"] == 0.10 and g["upturn_m"] == 0.20 for g in r1["gap_cover"])
    # the second ROOF label is in the same face: reported, never counted twice
    assert r2["counted_with"] == r1["text_id"] and r2["membrane_m2"] is None and r2["status"] == r1["status"]
    s = by_code(run(p))  # deterministic
    assert s["ROOF"][0]["membrane_m2"] == r1["membrane_m2"]


@pytest.mark.parametrize("name", ["m", "rot37_mirror_m"])
def test_other_codes(name):
    p = P(**VARIANTS[name])
    out = run(p)
    d = by_code(out)
    b = d["BALCONY"]
    terr = [r for r in b if r["text"] == "TERRACE"][0]
    bal = [r for r in b if r["text"] == "BALCONY"][0]
    assert bal["status"] == "PROVISIONAL" and abs(bal["membrane_m2"] - 4.5) < 0.005 and abs(bal["upturn_lm"] - 9.0) < 0.005
    assert bal["upturn_m2"] is None and bal["upturn_reason"] == "EXTERIOR_WP_UPTURN_BY_SPECIFICATION"
    # missing data: no line round the label -> HELD, no area, never 0
    assert terr["status"] == "HELD" and terr["reason"] == "NO_CLOSING_LAYER" and terr["membrane_m2"] is None
    pool = d["POOL"][0]
    assert pool["status"] == "HELD" and pool["reason"] == "POOL_NO_MEMBRANE_RULE" and pool["membrane_m2"] is None
    assert abs(pool["candidates"]["A-ROOF"]["A_net_m2"] - (2 + PI / 2)) < 0.005
    void = d["VOID"][0]
    assert void["status"] == "UNSUPPORTED" and void["reason"] == "VOID_OPEN_TO_BELOW"
    assert abs(void["candidates"]["A-VOID"]["A_net_m2"] - 1.5) < 0.005
    sm = out["summary"]
    assert sm["traced"] == 6 and sum(sm["by_status"].values()) == 6
    assert abs(sm["membrane_m2_by_code"]["ROOF"] - HAND["A_net"]) < 0.005    # one roof face, counted once
    assert sm["labels_counted_with_another"] == 1


def test_unlabelled_inner_shape_is_held_not_dropped():
    p = P(scale=1000.0, deg=37.0)
    r = by_code(run(p, dome_label=False))["ROOF"][0]
    assert r["status"] == "RELEASED_METHOD_PIECE"
    assert abs(r["membrane_m2"] - HAND["A_net"]) < 0.005                 # the shape's area is not membraned ...
    assert abs(r["held_part_m2"] - HAND["dome"]) < 0.005                 # ... it is shown, held
    assert r["held_part_reason"] == "INNER_SHAPE_UNIDENTIFIED"
    assert abs(r["upturn_lm"] - HAND["perim"]) < 0.005                   # no upturn round an unidentified shape


def test_project_fact_identifies_inner_shape():
    p = P()
    b, layers, texts, ops = plan(p, dome_label=False)
    facts = {"inner_shapes": {"DOME1": {"treatment": "OPENING", "source": "test fact"}}}
    out = XS.trace([t for t in texts], b, layers, 1.0, facts=facts)
    r = by_code(out)["ROOF"][0]
    assert r["held_part_m2"] is None and abs(r["upturn_lm"] - (HAND["perim"] + HAND["ring"])) < 0.005
    facts["inner_shapes"]["DOME1"]["treatment"] = "MEMBRANE_UNDER"
    r = by_code(XS.trace(texts, b, layers, 1.0, facts=facts))["ROOF"][0]
    assert abs(r["membrane_m2"] - HAND["A_filled"]) < 0.005 and abs(r["upturn_lm"] - HAND["perim"]) < 0.005


def test_gap_with_opening_element_is_not_closed():
    p = P(scale=1000.0, mirror=True)
    r = by_code(run(p, door_on_gap=True))["ROOF"][0]
    assert r["status"] == "HELD" and r["reason"] == "GAP_HAS_OPENING" and r["membrane_m2"] is None
    gaps = [g for c in r["candidates"].values() for g in c.get("gaps_with_opening", ())]
    assert gaps and gaps[0]["openings_on_gap"][0][0] == "GATE" and gaps[0]["length_m"] == 0.1


def test_gap_beyond_reach_stays_held():
    p = P()
    out = by_code(run(p, unit_m=1.0) if False else XS.trace(
        [t for t in plan(p)[2] if t["value"] != "DOME"], *plan(p)[:2], 1.0, reach_m=0.05))
    r = out["ROOF"][0]
    assert r["status"] == "HELD" and r["reason"] == "NO_CLOSING_LAYER" and r["membrane_m2"] is None


def test_units_missing_holds_everything():
    p = P()
    b, layers, texts, _ = plan(p)
    out = XS.trace(texts, b, layers, None)
    assert all(r["status"] == "HELD" and r["reason"] == "UNITS_MISSING" and r["membrane_m2"] is None
               for r in out["records"])


def test_two_layers_closing_different_faces_is_ambiguous():
    p = P()
    b, layers, texts, _ = plan(p)
    # a second OTHER layer draws a smaller closed outline round the first ROOF label (e.g. a hatch border)
    layers["A-HATCH"] = segs(p, [(1.0, -1.5), (3.4, -1.5), (3.4, -0.5), (1.0, -0.5), (1.0, -1.5)], "H")
    r = by_code(XS.trace([t for t in texts if t["value"] != "DOME"], b, layers, 1.0, texts=texts))["ROOF"][0]
    assert r["status"] == "HELD" and r["reason"] == "AMBIGUOUS_BOUNDARY_LAYER" and r["membrane_m2"] is None


def test_non_exterior_texts_pass_by_and_no_position():
    out = XS.trace([{"id": "a", "value": "BEDROOM", "x": 0, "y": 0}, {"id": "b", "value": "ROOF"},
                    {"id": "c", "value": "1500", "x": 1, "y": 1}], [], {}, 1.0)
    assert out["summary"]["texts_passed_by"] == 2
    assert out["records"][0]["status"] == "HELD" and out["records"][0]["reason"] == "LABEL_NO_POSITION"


def test_layer_role_check_flags_parapet_typed_as_wall():
    p = P()
    b, layers, texts, _ = plan(p)
    room = segs(p, [(0.2, 0.2), (4.2, 0.2), (4.2, 3.2), (0.2, 3.2), (0.2, 0.2)], "IW", "WALL")
    texts = texts + [{"id": "T9", "value": "BEDROOM", "x": 2.2, "y": 1.7}]
    closed_roof = segs(p, [(-3.0, 3.4), (-3.0, -2.0), (7.4, -2.0), (7.4, 3.4), (-3.0, 3.4)], "CR")
    good = XS.layer_role_check({"A-WALL": "WALL", "A-ROOF": "OTHER"}, {"A-WALL": b + room, "A-ROOF": closed_roof}, texts, 1.0)
    bad = XS.layer_role_check({"A-ROOF": "WALL", "A-WALL": "OTHER"}, {"A-WALL": b + room, "A-ROOF": closed_roof}, texts, 1.0)
    assert good[0]["status"] == "OK"
    assert bad[0]["status"] == "RISK" and bad[0]["reason"] == "LAYER_ROLE_PARAPET_AS_WALL"
    assert bad[0]["other_layers_separating_more_rooms"] == ["A-WALL"]


def test_report_rows_have_no_geometry():
    out = run(P())
    rows = XS.report_rows(out)
    import json
    txt = json.dumps(rows, default=str)
    assert "face_du" not in txt and "polygon_du" not in txt


def test_role_risk_holds_released_records():
    out = run(P())
    XS.apply_role_check(out, [{"wall_layer": "A-ROOF", "status": "RISK"}])
    roof = by_code(out)["ROOF"][0]
    assert roof["status"] == "HELD" and roof["reason"] == "LAYER_ROLE_RISK" and roof["membrane_m2"] is None
    assert abs(roof["held_figures"]["membrane_m2"] - HAND["A_net"]) < 0.005
    assert out["summary"]["by_status"]["RELEASED_METHOD_PIECE"] == 0 and out["summary"]["membrane_m2_by_code"] == {}
