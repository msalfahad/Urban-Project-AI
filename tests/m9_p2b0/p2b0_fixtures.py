"""Phase 2B-0 synthetic plans (DXF through ezdxf; synthetic geometry only, truth written by hand from the coordinates).

    open_plan(path, zone_x)       one GROUND FLOOR PLAN: a hall opening through ONE 10.4 m passage onto an open space
                                  split into a dining zone and a W.C. zone by a drawn zone line (the reference-plan
                                  F-24 shape: one passage on the boundary of several faces)
    corner_openings(path)         one room with a passage ending at a corner and a window starting at the same corner
    windows(path, frame)          one 4.0 x 3.0 m room with a 1.5 m window whose glazing is recessed (frame="RECESSED")
                                  or drawn on the room face (frame="ON_FACE"), or a curtain wall that replaces the
                                  whole north wall (frame="CURTAIN": floor-level glazing)
"""

from __future__ import annotations

from tools import arch_synth as AS

FRAME = ((-6000, -8000), (24000, 18000), (0, 0), "GROUND FLOOR PLAN")
HEIGHT_FACTS = {"schema": "URBAN_ARCH_FACTS_V1", "project_id": "SYNTHETIC P2B0",
                "wall_heights": {"*": {"PLASTER": {"value_m": 3.0, "authority": "OWNER_PROJECT_FACT: synthetic test"},
                                       "PAINT": {"value_m": 3.0, "authority": "OWNER_PROJECT_FACT: synthetic test"},
                                       "WALL_TILE": {"value_m": 2.4, "authority": "OWNER_PROJECT_FACT: synthetic test"}}},
                "opening_heights": {"DOOR": {"value_m": 2.1, "authority": "OWNER_PROJECT_FACT: synthetic test"},
                                    "WINDOW": {"value_m": 1.5, "authority": "OWNER_PROJECT_FACT: synthetic test"}}}


def _doc():
    import ezdxf
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    blk = doc.blocks.new("DOOR1000")
    blk.add_line((0, 0), (1000, 0), dxfattribs={"layer": "0"})
    blk.add_arc((0, 0), 1000, 0, 90, dxfattribs={"layer": "0"})
    msp = doc.modelspace()
    (x0, y0), (x1, y1), _org, title = FRAME
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": "A-FRAME"})
    msp.add_text(title, dxfattribs={"layer": "A-TITLE", "height": 500}).set_placement((x0 + 2000, y0 + 1500))
    return doc, msp


def _save(doc, msp, path, *, rooms, outer, labels, words, openings, extra=()):
    AS._plan(msp, rooms=rooms, outer=outer, labels=labels, words=words, openings=openings, columns=(), level="+0.00",
             treads=(), origin=FRAME[2], dx=0.0, dy=0.0, mirror=False, quarter_turns=0)
    for a, b, layer in extra:
        msp.add_line(a, b, dxfattribs={"layer": layer})
    doc.saveas(str(path))
    return str(path)


OUTER = [(0, 0), (12400, 0), (12400, 9400), (0, 9400)]
PASSAGE = ("PASSAGE", "y", 4200, 4400, 1000, 11400, None)          # 10.4 m: the hall | the open north space


def open_plan(path, zone_x=6000):
    """a 12.0 x 4.0 m hall (LIVING) opening through ONE 10.4 m passage onto a 12.0 x 4.8 m north space that holds a
    DINING zone and a W.C. zone, split by one drawn zone line at x = zone_x (from the passage threshold to the north
    wall). zone_x=11000 makes the W.C. zone 1.2 m wide: its own wall run (7.2 m) is shorter than the passage."""
    rooms = {"HALL": [(200, 200), (12200, 200), (12200, 4200), (200, 4200)],
             "NORTH": [(200, 4400), (12200, 4400), (12200, 9200), (200, 9200)]}
    labels = {"HALL": (6000, 2000), "DINING": (zone_x / 2.0, 7000), "WC": ((zone_x + 12200) / 2.0, 7000)}
    words = {"HALL": "LIVING", "DINING": "DINING", "WC": "W.C."}
    doc, msp = _doc()
    for name in ("DINING", "WC"):
        msp.add_text(words[name], dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement(labels[name])
        msp.add_text("+0.00", dxfattribs={"layer": "A-TEXT", "height": 150}).set_placement(
            (labels[name][0], labels[name][1] - 500))
    return _save(doc, msp, path, rooms=rooms, outer=OUTER, labels={"HALL": labels["HALL"]}, words={"HALL": "LIVING"},
                 openings=[PASSAGE], extra=[((zone_x, 4400), (zone_x, 9200), "A-THIN")])


def open_plan_truth(zone_x=6000):
    """hand truth: each face's wall run (perimeter minus the zone line) and its own length of the passage."""
    w_d, w_c = (zone_x - 200) / 1000.0, (12200 - zone_x) / 1000.0
    return {"LIVING": {"run": 32.0, "passage_own": 10.4},
            "DINING": {"run": 2 * (w_d + 4.8) - 4.8, "passage_own": (zone_x - 1000) / 1000.0},
            "W.C.": {"run": 2 * (w_c + 4.8) - 4.8, "passage_own": (11400 - zone_x) / 1000.0}}


def corner_openings(path):
    outer = [(0, 0), (6400, 0), (6400, 5400), (0, 5400)]
    rooms = {"ROOM": [(200, 200), (6200, 200), (6200, 5200), (200, 5200)]}
    ops = [("PASSAGE", "y", 0, 200, 3200, 6200, None),            # south wall, ends at the room's south-east corner
           ("WINDOW", "x", 6200, 6400, 200, 2200, None)]          # east wall, starts at the same corner
    doc, msp = _doc()
    return _save(doc, msp, path, rooms=rooms, outer=outer, labels={"ROOM": (2500, 3000)}, words={"ROOM": "BEDROOM"},
                 openings=ops)


def windows(path, frame):
    """one 4.0 x 3.0 m BEDROOM. frame="RECESSED": a 1.5 m window in the north wall, glazing at 1/3 and 2/3 of the wall
    (V1 convention: a sill window, skirted); "ON_FACE": the same window with its outer frame line drawn on the room
    face (the boundary is threshold and glazing at once: sill status unknown); "CURTAIN": the whole north side is a
    glazing line with no wall band (floor-level glazing: the V1 glazing edge, not skirted)."""
    outer = [(0, 0), (4400, 0), (4400, 3400), (0, 3400)]
    rooms = {"ROOM": [(200, 200), (4200, 200), (4200, 3200), (200, 3200)]}
    doc, msp = _doc()
    if frame in ("RECESSED", "ON_FACE"):
        extra = [((1200, 3200), (2700, 3200), "A-GLAZ")] if frame == "ON_FACE" else []
        return _save(doc, msp, path, rooms=rooms, outer=outer, labels={"ROOM": (2000, 1500)},
                     words={"ROOM": "BEDROOM"}, openings=[("WINDOW", "y", 3200, 3400, 1200, 2700, None)], extra=extra)
    if frame != "CURTAIN":
        raise ValueError(frame)
    wall = [((200, 200), (4200, 200)), ((4200, 200), (4200, 3200)), ((200, 3200), (200, 200)),       # room faces
            ((0, 0), (4400, 0)), ((4400, 0), (4400, 3200)), ((0, 3200), (0, 0)),                     # outer faces
            ((0, 3200), (200, 3200)), ((4200, 3200), (4400, 3200))]                                   # wall ends
    for a, b in wall:
        msp.add_line(a, b, dxfattribs={"layer": "A-WALL"})
    msp.add_line((200, 3200), (4200, 3200), dxfattribs={"layer": "A-GLAZ"})                      # the curtain wall
    msp.add_text("BEDROOM", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((2000, 1500))
    msp.add_text("+0.00", dxfattribs={"layer": "A-TEXT", "height": 150}).set_placement((2000, 1000))
    doc.saveas(str(path))
    return str(path)


# ---- door guards (F-18 / F-19 / F-20 / F-22): plan entities built directly (mm), roles given, truth by hand
DOOR_ROLES = {"A-WALL": "WALL", "A-DOOR": "DOOR", "A-GLAZ": "WINDOW", "A-COL": "COLUMN"}
DOOR_OUTER = [(0, 0), (12000, 0), (12000, 8000), (0, 8000)]
DOOR_ROOMS = {"HALL": [(200, 200), (4000, 200), (4000, 3000), (200, 3000)],
              "LOBBY": [(4200, 200), (6000, 200), (6000, 3000), (4200, 3000)],          # unlabelled
              "LIVING": [(6200, 200), (11800, 200), (11800, 3000), (6200, 3000)],
              "BEDROOM": [(200, 3200), (4000, 3200), (4000, 7800), (200, 7800)],
              "KITCHEN": [(4200, 3200), (8000, 3200), (8000, 7800), (4200, 7800)],
              "SHAFT": [(8200, 3200), (9800, 3200), (9800, 4800), (8200, 4800)],         # unlabelled, 1.6 x 1.6
              "STORE": [(10000, 3200), (11800, 3200), (11800, 4800), (10000, 4800)],
              "CORRIDOR": [(8200, 5000), (11800, 5000), (11800, 7800), (8200, 7800)]}
DOOR_OPENINGS = [
    ("DOOR", "y", 0, 200, 1500, 2500, None),          # D1 HALL | outside 1.00, the main entrance (ENTRANCE word)
    ("PASSAGE", "y", 0, 200, 4400, 5800, None),       # P1 LOBBY | outside 1.40, no door: the lobby may be external
    ("DOOR", "y", 3000, 3200, 4600, 5500, None),      # D2 KITCHEN | LOBBY 0.90: PVC in V2.1, a class REVIEW in V2.2
    ("DOOR", "x", 11800, 12000, 1000, 1900, None),    # D3 LIVING | outside 0.90 with a 1.00 m frame (F-18)
    ("DOOR", "y", 3000, 3200, 1500, 2400, None),      # D4 HALL | BEDROOM 0.90: an ordinary PVC door
    ("PASSAGE", "x", 8000, 8200, 3600, 4400, None),   # P2 KITCHEN | SHAFT 0.80 access opening (F-22)
    ("DOOR", "y", 4800, 5000, 10400, 11300, None)]    # D5 STORE | CORRIDOR 0.90: an ordinary PVC door
DOOR_SWINGS = (((1500, 200), 1000, 0, 90), ((4600, 3200), 900, 0, 90), ((11800, 1000), 900, 90, 180),
               ((1500, 3200), 900, 0, 90), ((10400, 5000), 900, 0, 90))
DOOR_WORDS = (("ENTRANCE HALL", (2000, 1600)), ("LIVING", (9000, 1600)), ("BEDROOM", (2000, 5500)),
              ("KITCHEN", (6000, 5500)), ("BEDROOM", (10900, 4000)), ("CORRIDOR", (10000, 6500)))
# D3's door block also draws its frame along the wall strip: 1.00 m against the 0.90 m opening
DOOR_FRAME = (((11900, 950), (11900, 1950), "A-DOOR", "DOOR:3"),)
# P2 carries four head lines along the opening (as the lift landings of the reference plan): not a clear passage, so
# the shaft is not attached to the kitchen (engine.source.arch_rooms.open_passages)
SHAFT_HEADS = tuple((((x, 3600), (x, 4400)), "A-THIN", None) for x in (8040, 8080, 8120, 8160))


def door_guards():
    """-> (ents, roles): the D1 .. D5 / P1 / P2 floor above (the shaft is marked as the stacked-footprint pass would)."""
    ents = AS._s4_ents(DOOR_ROOMS, DOOR_OUTER, DOOR_OPENINGS, texts=DOOR_WORDS, swings=DOOR_SWINGS,
                       extra_segments=DOOR_FRAME + tuple((a, b, layer, path) for (a, b), layer, path in SHAFT_HEADS))
    return ents, dict(DOOR_ROLES, **{"A-THIN": "OTHER"})


def mark_stacked_shaft(S, box_mm):
    """what engine.source.arch_rooms.stacked_shafts does to a footprint repeated on the other plans."""
    x0, y0, x1, y1 = box_mm
    for f in S["faces"]:
        xs, ys = [p[0] for p in f["polygon"]], [p[1] for p in f["polygon"]]
        if abs(min(xs) - x0) < 1 and abs(min(ys) - y0) < 1 and abs(max(xs) - x1) < 1 and abs(max(ys) - y1) < 1:
            f.update(codes=["SHAFT"], label_source="STACKED_FOOTPRINT", **{"class": "ROOM"})
            f["issue"] = "ROOM_TYPE_FROM_STACKED_FOOTPRINT: the same footprint is on 3 plans (GF, 1F, 2F)"
            return f
    raise AssertionError("shaft face not found")
