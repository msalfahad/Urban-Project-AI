"""T-753 read-only development-villa run: B13-06 joinery census on the architectural DXF (t753_joinery.JOINERY_CENSUS_
T753_V1). Nothing in the repository is written; output goes to --out (outside the repository).

Usage (from the checkout root, through the wrapper):
  bash scripts/agent_env.sh run --tree task-T-753 research/agents_t753/t753_alsenan.py <arch.dxf> \
      --rooms <t743_arch_dump output json> --out <scratch>/t753_alsenan.json

READING (below): each unit is named by the CAD handles of its drawn lines (fixture layer '5' fronts / returns /
diagonals, wall layer '1' faces, structural column outline) and its outline is built from their end points and line
intersections, so every number is re-derivable by handle. Handles and engine room ids only; no coordinates, no client
data are kept in the repository.

Independent checks: (1) a machine scan of every fixture-layer LINE pair for the cupboard symbol (front + one diagonal)
must find exactly the CUPBOARD units of the reading; (2) every fixture-layer LINE inside a room that holds a unit is either
part of a unit or listed as not-joinery with its reason; nothing is silently dropped."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import t753_joinery as J  # noqa: E402

FIXTURE_LAYER = "5"
WALL_LAYERS = ("1",)

# --------------------------------------------------------------------------------------------- the person's reading
# ring: point refs, front chain first. 'H.s' / 'H.e' = start / end of LINE H; 'H.vN' = vertex N of polyline H;
# 'X(A,B)' = intersection of the infinite lines of A and B (a polyline edge as 'H.eN' = vertex N -> N+1).
READING = [
    {"unit_id": "J-GF-KIT-01", "kind": J.BASE_RUN, "floor": "GF", "room_id": "GF-RA3AD49",
     "ring": ["137.s", "137.e", "11C.s", "X(A4,11B)", "X(11B,136)", "136.s"],
     "front": ["137", "11C"], "returns": [],
     "evidence": ["L-shaped counter outline on the fixture layer, 0.50 m off the W and N wall faces, kitchen tag 276; "
                  "the same L is drawn on p7757_arch_sheet03 (second drawing)"],
     "note": "ends on the WC wall face 14F (S) and on the E wall face A4: no end return drawn; back = wall faces 136 / 11B"},
    {"unit_id": "J-GF-PAN-01", "kind": J.BASE_RUN, "floor": "GF", "room_id": "GF-RC99C2A",
     "ring": ["335.e", "335.s", "B1.s", "15C.e", "33F.s", "X(158,2FAE.e0)", "2FAE.v0", "X(AE,2FAE.e3)"],
     "front": ["B1", "15C"], "returns": ["335", "33F"],
     "evidence": ["L-shaped counter outline on the fixture layer along the W wall AE / AF and the N wall 158, the column "
                  "2FAE projecting 0.05 m under the N leg; pantry tag 178; same outline on p7757_arch_sheet03"],
     "note": "pantry is the open-plan engine space (Q-37 A, UP-PANTRY-*)"},
    {"unit_id": "J-GF-PAN-02", "kind": J.BASE_RUN, "floor": "GF", "room_id": "GF-RC99C2A",
     "ring": ["B2.e", "B2.s", "AA.e", "B4.s", "15D.e", "X(B3,A6)"],
     "front": ["AA", "B4"], "returns": ["B2", "15D"],
     "evidence": ["L-shaped counter: S leg along the wall A6, E leg (peninsula) whose back is the OPEN edge B3 of the "
                  "pantry toward the dining, two stools 174/175 and 176/177 drawn beyond it (loose, excluded); same on "
                  "p7757_arch_sheet03"],
     "note": "the peninsula back B3 is an open edge, not a wall: its back face is joinery too (designer item)"},
    {"unit_id": "J-GF-WSH-01", "kind": J.VANITY, "floor": "GF", "room_id": "GF-RDBD4F9",
     "ring": ["2BF.e", "2BF.s", "2BE.s", "X(324,318)", "X(318,BE)", "BE.e"],
     "front": ["2BF", "2BE"], "returns": [],
     "evidence": ["counter outline on the fixture layer holding the two basin blocks WASH2 2C0 and 2C1 (hand-wash lobby, "
                  "tag 2C5)"],
     "excluded": ["WASH2#2C0 (B12-01)", "WASH2#2C1 (B12-01)"],
     "note": "ends on the S wall face (y of BE.e) and on the angled wall 324; depth tapers along the angled leg"},
    {"unit_id": "J-GF-WSH-02", "kind": J.VANITY, "floor": "GF", "room_id": "GF-R8496F0",
     "ring": ["1CE.e", "1CE.s", "X(11F,12E)", "X(12E,117)"],
     "front": ["1CE"], "returns": [],
     "evidence": ["counter front on the fixture layer, wall 117 to wall 11F, holding the two basin blocks WASH2 1CF and "
                  "1EE against the wall 12E (hand-wash lobby of the majlis, tag 1F0)"],
     "excluded": ["WASH2#1CF (B12-01)", "WASH2#1EE (B12-01)"],
     "note": "found by the completeness scan (a fixture-layer line left over in GF-R8496F0)"},
    {"unit_id": "J-GF-WSH-03", "kind": J.VANITY, "floor": "GF", "room_id": "GF-RD36087",
     "ring": ["33A.s", "33A.e", "X(211,218)", "X(2B2,211)"],
     "front": ["33A"], "returns": [],
     "evidence": ["counter front on the fixture layer, wall 218 to wall 2B2, holding the basin block WASH2 33B against "
                  "the wall 211 (lobby off the stair hall)"],
     "excluded": ["WASH2#33B (B12-01)"],
     "note": "found by the completeness scan (a fixture-layer line left over in GF-RD36087)"},
    {"unit_id": "J-GF-CPB-01", "kind": J.CUPBOARD, "floor": "GF", "room_id": "GF-R75FBAE",
     "ring": ["2EF.e", "2EF.s", "319.e", "2E0.e"],
     "front": ["2EF"], "returns": [],
     "evidence": ["diagonal 2F1 corner to corner (cupboard symbol); back = wall faces 2E0 + 319; master bedroom GF"],
     "note": "trapezoid: the back corner is cut by the angled wall 319"},
    {"unit_id": "J-1F-CPB-01", "kind": J.CUPBOARD, "floor": "1F", "room_id": "1F-RFFE7AF",
     "ring": ["B0A.s", "B0A.e", "B00.e", "B00.s"],
     "front": ["B0A"], "returns": [],
     "evidence": ["diagonal BE3 corner to corner (cupboard symbol); back = wall face B00 (dressing cell, T-460 / T-481)"]},
    {"unit_id": "J-1F-CPB-02", "kind": J.CUPBOARD, "floor": "1F", "room_id": "1F-R3CFCFD",
     "ring": ["B0C.e", "B0C.s", "C17.e", "X(C17,B0C@back)"],
     "front": ["B0C"], "returns": [],
     "evidence": ["diagonal C17 corner to corner (cupboard symbol); back = the wall face at the diagonal's far end "
                  "(bedroom lobby, T-218: joinery, not a shaft)"]},
]

NOT_DRAWN = [
    {"room_id": "GF-RA3AD49", "item": "WALL_CABINETS",
     "reason": "no wall-cabinet outline (dashed or solid) on the plan, no interior elevation: designer item"},
    {"room_id": "GF-RC99C2A", "item": "WALL_CABINETS (pantry)",
     "reason": "no wall-cabinet outline on the plan, no interior elevation: designer item"},
    {"room_id": "1F-R26FA0D", "item": "LAUNDRY_JOINERY",
     "reason": "laundry draws no counter, cabinet or appliance outline (T-351): nothing to measure, designer item"},
]


# fixture-layer lines inside a room that holds no joinery: what they are (read on the plan by handle), so the
# completeness check leaves nothing unexplained. Room-level classes first, then single handles.
NOT_JOINERY_ROOMS = {
    "GF-R31F8AE": "STAIR room: flights, treads, handrail and break lines (B7)",
    "2F-R4D1B62": "STAIR room: flights, treads, handrail and break lines (B7)",
    "1F-R78C367": "living hall: the stair flights / treads / rails and the VOID cross (B74..B79) (B7, B2-05)",
    "GF-R89E756": "LIFT car symbol (closed box + diagonal, stacked on every floor): not joinery",
    "1F-RCCB686": "LIFT car symbol (closed box + diagonal, stacked on every floor): not joinery",
    "2F-R2BDCEE": "LIFT car symbol (closed box + diagonal, stacked on every floor): not joinery",
}
NOT_JOINERY_HANDLES = {
    "B3": "pantry OPEN edge toward the dining: the back of the peninsula J-GF-PAN-02 (on its outline)",
    "AD": "pantry OPEN edge toward the dining, north of the peninsula (floor-zone edge)",
    "19C": "threshold line in the door opening D120 (B3-07)",
    "22B": "threshold line at the lift door", "B9B": "threshold line at the lift door",
    "12B3": "threshold line at the lift door",
    "13C": "step / level edge between reception and garden", "22C": "step / level edge", "22D": "step / level edge",
    "22E": "step / level edge", "30F": "garden floor-zone edge", "310": "garden floor-zone edge",
}
TREAD_LM = 1.15                     # the GF reception curved flight treads (B7), by their drawn length


# ------------------------------------------------------------------------------------------------- reading the DXF
def load(dxf_path):
    import ezdxf
    doc = ezdxf.readfile(str(dxf_path))
    u = 1 / 1000.0                                                 # this plan is in mm ($INSUNITS 4)
    return doc, u


def _line(doc, u, h):
    e = doc.entitydb.get(h)
    if e is None:
        raise KeyError(f"handle {h} not in the drawing")
    if e.dxftype() != "LINE":
        raise ValueError(f"{h} is a {e.dxftype()}, not a LINE")
    return J.Seg(h, (e.dxf.start.x * u, e.dxf.start.y * u), (e.dxf.end.x * u, e.dxf.end.y * u), e.dxf.layer)


def _verts(doc, u, h):
    e = doc.entitydb.get(h)
    return [(p[0] * u, p[1] * u) for p in e.get_points()]


def _edge(doc, u, ref):
    """'H' (a LINE) or 'H.eN' (edge N of a polyline) -> (a, b)."""
    if ".e" in ref and ref.split(".e")[1].isdigit():
        h, k = ref.split(".e")
        v = _verts(doc, u, h)
        k = int(k)
        return v[k], v[(k + 1) % len(v)]
    s = _line(doc, u, ref)
    return s.a, s.b


def _x(p1, p2, p3, p4):
    d = (p1[0] - p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] - p4[0])
    if abs(d) < 1e-12:
        raise ValueError("parallel lines have no intersection")
    a = p1[0] * p2[1] - p1[1] * p2[0]
    b = p3[0] * p4[1] - p3[1] * p4[0]
    return ((a * (p3[0] - p4[0]) - (p1[0] - p2[0]) * b) / d, (a * (p3[1] - p4[1]) - (p1[1] - p2[1]) * b) / d)


def point(doc, u, ref):
    if ref.startswith("X(") and ref.endswith(")"):
        a, b = ref[2:-1].split(",")
        if b.endswith("@back"):
            # the back line parallel to the front through the diagonal's far end: the cupboard's wall face
            return _back_corner(_line(doc, u, b[:-5]), _line(doc, u, a))
        return _x(*_edge(doc, u, a), *_edge(doc, u, b))
    h, _, part = ref.partition(".")
    if part in ("s", "e"):
        s = _line(doc, u, h)
        return s.a if part == "s" else s.b
    if part.startswith("v"):
        return _verts(doc, u, h)[int(part[1:])]
    raise ValueError(f"bad point ref {ref!r}")


def _back_corner(front, diag):
    """the back corner of a cupboard box behind the front end the diagonal starts from (the diagonal itself ends at
    the other back corner): that end + the diagonal's offset from the front line."""
    for shared in (front.a, front.b):
        for p, q in ((diag.a, diag.b), (diag.b, diag.a)):
            if J._near(p, shared):
                foot = J._proj(q, front.a, front.b)[2]
                return (shared[0] + q[0] - foot[0], shared[1] + q[1] - foot[1])
    raise ValueError(f"{diag.ref} does not start at an end of {front.ref}")


def build_units(doc, u, reading):
    units = []
    for r in reading:
        ring = [point(doc, u, p) for p in r["ring"]]
        units.append(J.Unit(unit_id=r["unit_id"], kind=r["kind"], floor=r["floor"], room_id=r["room_id"], ring=ring,
                            front=[_line(doc, u, h) for h in r["front"]],
                            returns=[_line(doc, u, h) for h in r.get("returns", ())],
                            evidence=r.get("evidence", []), excluded=r.get("excluded", []), note=r.get("note", "")))
    return units


def _pip(x, y, poly):
    ins, n = False, len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            ins = not ins
    return ins


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("arch_dxf")
    ap.add_argument("--rooms", required=True, help="t743_arch_dump output for the same drawing (engine room ids)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    doc, u = load(a.arch_dxf)
    rooms = json.loads(Path(a.rooms).read_text(encoding="utf-8"))["rooms"]
    poly = {r["room_id"]: [tuple(p) for p in r["polygon_m"]] for r in rooms}
    units = build_units(doc, u, READING)
    # the room the reading names must hold (or touch within 0.10 m) a front edge of the unit: the front faces the room
    # the unit serves (its body may stand outside every engine room polygon: reported in floor_outside_rooms)
    outside = {}
    for un in units:
        pg = poly[un.room_id]

        def dist(pt):
            return 0.0 if _pip(pt[0], pt[1], pg) else min(J._seg_dist(pt, pg[i], pg[(i + 1) % len(pg)])
                                                          for i in range(len(pg)))
        mids = [((s.a[0] + s.b[0]) / 2, (s.a[1] + s.b[1]) / 2) for s in un.front]
        if min(dist(m) for m in mids) > 0.10:
            raise SystemExit(f"{un.unit_id}: no front edge in or at {un.room_id}")
        # plan area of the unit outside every engine room of its floor (a 0.01 m grid count)
        xs, ys = [p[0] for p in un.ring], [p[1] for p in un.ring]
        n_out = n_in = 0
        step = 0.01
        x = min(xs) + step / 2
        while x < max(xs):
            y = min(ys) + step / 2
            while y < max(ys):
                if J._inside((x, y), un.ring):
                    if any(_pip(x, y, poly[r["room_id"]]) for r in rooms if r["floor"] == un.floor):
                        n_in += 1
                    else:
                        n_out += 1
                y += step
            x += step
        if n_out:
            outside[un.unit_id] = round(n_out * step * step, 3)
    c = J.census(units, not_drawn=NOT_DRAWN)

    # (1) machine scan for cupboard symbols on the fixture layer
    msp = doc.modelspace()
    fx = [J.Seg(e.dxf.handle, (e.dxf.start.x * u, e.dxf.start.y * u), (e.dxf.end.x * u, e.dxf.end.y * u), e.dxf.layer)
          for e in msp.query("LINE") if e.dxf.layer == FIXTURE_LAYER]
    walls = [J.Seg(e.dxf.handle, (e.dxf.start.x * u, e.dxf.start.y * u), (e.dxf.end.x * u, e.dxf.end.y * u),
                   e.dxf.layer) for e in msp.query("LINE") if e.dxf.layer in WALL_LAYERS]
    scan = J.find_cupboard_symbols(fx, walls)
    read_cpb = sorted(r["front"][0] for r in READING if r["kind"] == J.CUPBOARD)
    scan_cpb = sorted(s[0] for s in scan)
    # text-only blocks named like joinery are labels, never units
    tags = {}
    for e in msp.query("INSERT"):
        blk = doc.blocks.get(e.dxf.name)
        if J.is_tag_block([x.dxftype() for x in blk]):
            tags[e.dxf.name] = tags.get(e.dxf.name, 0) + 1

    # (2) completeness: fixture-layer LINEs inside each room that holds a unit, not used by any unit
    used = set()
    for r in READING:
        used.update(r["front"])
        used.update(r.get("returns", ()))
        used.update(x for x in (r.get("diag") or ()))
    used.update({"2F1", "BE3", "C17"})                         # the cupboard diagonals (type evidence)
    leftovers = {}
    for s in fx:
        if s.ref in used:
            continue
        mx, my = (s.a[0] + s.b[0]) / 2, (s.a[1] + s.b[1]) / 2
        for rid, pg in poly.items():
            if _pip(mx, my, pg):
                leftovers.setdefault(rid, []).append((s.ref, round(s.length, 3)))
    unexplained = {}
    for rid, ls in leftovers.items():
        if rid in NOT_JOINERY_ROOMS:
            continue
        for h, ln in ls:
            if h in NOT_JOINERY_HANDLES or (rid == "GF-RC99C2A" and abs(ln - TREAD_LM) < 0.06):
                continue
            unexplained.setdefault(rid, []).append((h, ln))
    out = {**c, "floor_outside_rooms_m2": outside, "fixture_lines_unexplained": unexplained, "cupboard_scan": scan, "cupboard_scan_agrees": read_cpb == scan_cpb,
           "text_only_blocks_not_units": tags, "fixture_lines_left_by_room": leftovers}
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in c["units"]:
        print(r["unit_id"], r["kind"], r["room_id"], "front", r["front_lm"]["value"], "depth", r["depth_m"]["min"],
              "..", r["depth_m"]["max"], "plan", r["plan_m2"]["value"], "corners", r["inside_corners"])
    print("totals", json.dumps(c["totals"]))
    print("cupboard scan", scan, "agrees with reading:", read_cpb == scan_cpb)
    print("unit plan area outside every engine room (V2.9 rooms, 0.01 m grid):", outside)
    print("text-only blocks (labels, not units):", tags)
    print("fixture-layer lines left and unexplained:", unexplained)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
