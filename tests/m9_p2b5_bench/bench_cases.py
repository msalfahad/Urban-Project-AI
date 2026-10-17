"""BENCHMARK CASES - Phase 2B-5 Stages D / F: synthetic plans whose geometry is known by construction, for comparing
room readers (the native engine, the independent ezdxf + shapely reader, CAD MCPs when one is connected, and the
raster / vector-PDF vision prototype).

Every plan is drawn in millimetres with 200 mm walls: the room faces and the outer face of the exterior wall, cut at
every opening and closed by jambs (the tools/arch_synth conventions). `truth` is derived by hand from the coordinates
(rectangle, L, splay and column areas; outer perimeters - boundary_m adds the faces of a column; opening widths) and
written as typed literals. This file imports nothing.

Opening tuples follow tools/arch_synth: (kind, axis, wall band low, wall band high, s0, s1, door insert or None); a door
insert is (hinge x, hinge y, rotation deg, xscale sign, yscale sign) of a block whose leaf runs along +x and whose
swing closes at +y.
"""

CASES = [
    {"id": "B01", "title": "rectangular bathroom 4.00 x 3.00 m, one 0.80 m door, one 0.60 m window",
     "rooms": {"BATH": [(200, 200), (4200, 200), (4200, 3200), (200, 3200)]},
     "outer": [(0, 0), (4400, 0), (4400, 3400), (0, 3400)],
     "labels": {"BATH": (2200, 1700)}, "words": {"BATH": "BATH"},
     "openings": [("DOOR", "y", 0, 200, 1000, 1800, (1800, 200, 90, 1, 1)),
                  ("WINDOW", "x", 4200, 4400, 1000, 1600, None)],
     "columns": [], "rotate_deg": 0.0,
     "truth": {"rooms": {"BATH": {"area_m2": 12.0, "perimeter_m": 14.0, "holes_m2": 0.0}},
               "doors_m": [0.8], "windows_m": [0.6], "passages_m": []}},
    {"id": "B02", "title": "the same bathroom, the door drawn as a MIRRORED block (xscale -1)",
     "rooms": {"BATH": [(200, 200), (4200, 200), (4200, 3200), (200, 3200)]},
     "outer": [(0, 0), (4400, 0), (4400, 3400), (0, 3400)],
     "labels": {"BATH": (2200, 1700)}, "words": {"BATH": "BATH"},
     "openings": [("DOOR", "y", 0, 200, 1000, 1800, (1000, 200, 270, -1, 1)),
                  ("WINDOW", "x", 4200, 4400, 1000, 1600, None)],
     "columns": [], "rotate_deg": 0.0,
     "truth": {"rooms": {"BATH": {"area_m2": 12.0, "perimeter_m": 14.0, "holes_m2": 0.0}},
               "doors_m": [0.8], "windows_m": [0.6], "passages_m": []}},
    {"id": "B03", "title": "L-shaped bathroom 3.00 x 3.00 m less 1.00 x 1.00 m, one 0.90 m door",
     "rooms": {"BATH": [(200, 200), (3200, 200), (3200, 2200), (2200, 2200), (2200, 3200), (200, 3200)]},
     "outer": [(0, 0), (3400, 0), (3400, 2400), (2400, 2400), (2400, 3400), (0, 3400)],
     "labels": {"BATH": (1200, 1200)}, "words": {"BATH": "BATH"},
     "openings": [("DOOR", "y", 0, 200, 800, 1700, (1700, 200, 90, 1, 1))],
     "columns": [], "rotate_deg": 0.0,
     "truth": {"rooms": {"BATH": {"area_m2": 8.0, "perimeter_m": 12.0, "holes_m2": 0.0}},
               "doors_m": [0.9], "windows_m": [], "passages_m": []}},
    {"id": "B04", "title": "bedroom 3.00 x 2.50 m with a free-standing 0.40 x 0.40 m column, one 0.90 m door",
     "rooms": {"BEDROOM": [(200, 200), (3200, 200), (3200, 2700), (200, 2700)]},
     "outer": [(0, 0), (3400, 0), (3400, 2900), (0, 2900)],
     "labels": {"BEDROOM": (900, 2000)}, "words": {"BEDROOM": "BEDROOM"},
     "openings": [("DOOR", "x", 0, 200, 1000, 1900, (200, 1900, 0, 1, -1))],
     "columns": [(1500, 1000)], "rotate_deg": 0.0,
     "truth": {"rooms": {"BEDROOM": {"area_m2": 7.34, "perimeter_m": 11.0, "holes_m2": 0.16, "boundary_m": 12.6}},
               "doors_m": [0.9], "windows_m": [], "passages_m": []}},
    {"id": "B05", "title": "two adjacent rooms (bedroom 3.00 x 3.00, bathroom 2.00 x 3.00) sharing a 0.80 m door",
     "rooms": {"BEDROOM": [(200, 200), (3200, 200), (3200, 3200), (200, 3200)],
               "BATH": [(3400, 200), (5400, 200), (5400, 3200), (3400, 3200)]},
     "outer": [(0, 0), (5600, 0), (5600, 3400), (0, 3400)],
     "labels": {"BEDROOM": (1700, 2200), "BATH": (4400, 2200)}, "words": {"BEDROOM": "BEDROOM", "BATH": "BATH"},
     "openings": [("DOOR", "x", 3200, 3400, 1000, 1800, (3400, 1800, 0, 1, -1)),
                  ("DOOR", "y", 0, 200, 1200, 2100, (2100, 200, 90, 1, 1))],
     "columns": [], "rotate_deg": 0.0,
     "truth": {"rooms": {"BEDROOM": {"area_m2": 9.0, "perimeter_m": 12.0, "holes_m2": 0.0},
                         "BATH": {"area_m2": 6.0, "perimeter_m": 10.0, "holes_m2": 0.0}},
               "doors_m": [0.8, 0.9], "windows_m": [], "passages_m": []}},
    {"id": "B06", "title": "B01 turned by 27 degrees about the plan centre",
     "rooms": {"BATH": [(200, 200), (4200, 200), (4200, 3200), (200, 3200)]},
     "outer": [(0, 0), (4400, 0), (4400, 3400), (0, 3400)],
     "labels": {"BATH": (2200, 1700)}, "words": {"BATH": "BATH"},
     "openings": [("DOOR", "y", 0, 200, 1000, 1800, (1800, 200, 90, 1, 1)),
                  ("WINDOW", "x", 4200, 4400, 1000, 1600, None)],
     "columns": [], "rotate_deg": 27.0,
     "truth": {"rooms": {"BATH": {"area_m2": 12.0, "perimeter_m": 14.0, "holes_m2": 0.0}},
               "doors_m": [0.8], "windows_m": [0.6], "passages_m": []}},
    {"id": "B07", "title": "bathroom 3.00 x 4.00 m with a 45-degree splayed corner (0.50 m legs), one 0.80 m door",
     "rooms": {"BATH": [(200, 200), (3200, 200), (3200, 3700), (2700, 4200), (200, 4200)]},
     "outer": [(0, 0), (3400, 0), (3400, 3782.843), (2782.843, 4400), (0, 4400)],
     "labels": {"BATH": (1700, 2200)}, "words": {"BATH": "BATH"},
     "openings": [("DOOR", "y", 0, 200, 1000, 1800, (1800, 200, 90, 1, 1))],
     "columns": [], "rotate_deg": 0.0,
     "truth": {"rooms": {"BATH": {"area_m2": 11.875, "perimeter_m": 13.707107, "holes_m2": 0.0}},
               "doors_m": [0.8], "windows_m": [], "passages_m": []}},
    {"id": "B08", "title": "laundry 2.00 x 3.00 m and an unlabelled lobby 1.50 x 3.00 m joined by a 1.00 m passage",
     "rooms": {"LAUNDRY": [(200, 200), (2200, 200), (2200, 3200), (200, 3200)],
               "LOBBY": [(2400, 200), (3900, 200), (3900, 3200), (2400, 3200)]},
     "outer": [(0, 0), (4100, 0), (4100, 3400), (0, 3400)],
     "labels": {"LAUNDRY": (1200, 2200)}, "words": {"LAUNDRY": "LAUNDRY"},
     "openings": [("PASSAGE", "x", 2200, 2400, 1000, 2000, None),
                  ("DOOR", "y", 0, 200, 2800, 3600, (3600, 200, 90, 1, 1))],
     "columns": [], "rotate_deg": 0.0,
     "truth": {"rooms": {"LAUNDRY": {"area_m2": 6.0, "perimeter_m": 10.0, "holes_m2": 0.0}},
               "unlabelled": {"LOBBY": {"area_m2": 4.5, "perimeter_m": 9.0}},
               "doors_m": [0.8], "windows_m": [], "passages_m": [1.0]}},
    {"id": "B09", "title": "B05 mirrored as a whole plan (x -> -x about the plan centre): walls, doors, labels",
     "rooms": {"BEDROOM": [(200, 200), (3200, 200), (3200, 3200), (200, 3200)],
               "BATH": [(3400, 200), (5400, 200), (5400, 3200), (3400, 3200)]},
     "outer": [(0, 0), (5600, 0), (5600, 3400), (0, 3400)],
     "labels": {"BEDROOM": (1700, 2200), "BATH": (4400, 2200)}, "words": {"BEDROOM": "BEDROOM", "BATH": "BATH"},
     "openings": [("DOOR", "x", 3200, 3400, 1000, 1800, (3400, 1800, 0, 1, -1)),
                  ("DOOR", "y", 0, 200, 1200, 2100, (2100, 200, 90, 1, 1))],
     "columns": [], "rotate_deg": 0.0, "mirror": True,
     "truth": {"rooms": {"BEDROOM": {"area_m2": 9.0, "perimeter_m": 12.0, "holes_m2": 0.0},
                         "BATH": {"area_m2": 6.0, "perimeter_m": 10.0, "holes_m2": 0.0}},
               "doors_m": [0.8, 0.9], "windows_m": [], "passages_m": []}},
    {"id": "B10", "title": "bathroom 4.00 x 3.00 m whose east wall is a circular arc (chord 3.00 m, rise 0.50 m, "
                           "radius 2.50 m); the inner face an ARC, the outer face a bulged LWPOLYLINE; one 0.80 m door",
     # drawn primitives (not tools/arch_synth): (LINE, layer, a, b) | (ARC, layer, centre, r, start deg, end deg) |
     # (PLINE, layer, [(x, y, bulge)], closed) | (INSERT, layer, block, p, rotation, xscale, yscale) |
     # (TEXT, layer, word, p, height). The inner arc: centre (2200, 1700), r 2500, +-36.86989765 deg (sin = 0.6);
     # the outer arc: the same centre, r 2700, meeting y = 0 and y = 3400 at x = 2200 + sqrt(2700^2 - 1700^2) =
     # 4297.617696; its bulge tan(78.04560513 / 4) = 0.3543425316.
     "draw": [("LINE", "A-WALL", (200, 200), (1000, 200)), ("LINE", "A-WALL", (1800, 200), (4200, 200)),
              ("ARC", "A-WALL", (2200, 1700), 2500.0, -36.86989764584402, 36.86989764584402),
              ("LINE", "A-WALL", (4200, 3200), (200, 3200)), ("LINE", "A-WALL", (200, 3200), (200, 200)),
              ("LINE", "A-WALL", (0, 0), (1000, 0)), ("LINE", "A-WALL", (1800, 0), (4297.617696340303, 0)),
              ("PLINE", "A-WALL", [(4297.617696340303, 0, 0.3543425315645276), (4297.617696340303, 3400, 0.0)],
               False),
              ("LINE", "A-WALL", (4297.617696340303, 3400), (0, 3400)), ("LINE", "A-WALL", (0, 3400), (0, 0)),
              ("LINE", "A-WALL", (1000, 0), (1000, 200)), ("LINE", "A-WALL", (1800, 0), (1800, 200)),
              ("INSERT", "A-DOOR", "DOOR1000", (1800, 200), 90.0, 0.8, 0.8),
              ("TEXT", "A-TEXT", "BATH", (2200, 1700), 200.0), ("TEXT", "A-TEXT", "+0.00", (2200, 1200), 150.0)],
     "arc_room": {"BATH": {"straight": [(4200, 3200), (200, 3200), (200, 200), (4200, 200)],
                           "centre": (2200, 1700), "r": 2500.0, "a0_deg": -36.86989764584402,
                           "a1_deg": 36.86989764584402}},
     "rooms": {}, "outer": [(0, 0), (4900, 0), (4900, 3400), (0, 3400)],
     "labels": {"BATH": (2200, 1700)}, "words": {"BATH": "BATH"},
     "openings": [("DOOR", "y", 0, 200, 1000, 1800, None)], "columns": [], "rotate_deg": 0.0,
     # area: the 4.00 x 3.00 rectangle + the circular segment r^2 (2t - sin 2t) / 2, t = asin(1.5 / 2.5):
     # 12 + 6.25 x (1.287002218 - 0.96) / 2 = 13.02188193 m2; perimeter: 4 + 3 + 4 + the arc 2.5 x 1.287002218
     "truth": {"rooms": {"BATH": {"area_m2": 13.021881929958028, "perimeter_m": 14.217505543966421,
                                  "holes_m2": 0.0}},
               "doors_m": [0.8], "windows_m": [], "passages_m": []}},
]

BY_ID = {c["id"]: c for c in CASES}


def _encoded(base, cid, title, encoding, **extra):
    """the same plan as `base` (so the same hand truth), written to the DXF in another CAD encoding."""
    return dict(BY_ID[base], id=cid, title=title, base=base, encoding=encoding, **extra)


# CAD-encoding cases: a vision reader sees the same picture as the base case, so only the DXF readers run on them
ENCODED = [
    _encoded("B01", "C01", "B01 with its walls inside two nested blocks: the outer INSERT mirrored (xscale -1), turned "
             "90 degrees and moved; the inner INSERT scaled non-uniformly (x 2.0, y 0.5)",
             {"nested_walls": {"outer_insert": (5000.0, -3000.0), "outer_rotation": 90.0, "outer_xscale": -1.0,
                               "inner_scale": (2.0, 0.5)}}),
    _encoded("B01", "C02", "B01 drawn in metres ($INSUNITS 6): every coordinate and text height / 1000",
             {"metres": True}),
    _encoded("B04", "C03", "B04 with its wall faces chained into LWPOLYLINEs - closed wall bands and open runs - and "
             "the column a closed LWPOLYLINE", {"polylines": True}),
    _encoded("B05", "C04", "B05 with Arabic room words (bedroom, bathroom) and linear DIMENSION entities across both "
             "rooms (one with a text override)", {"dimensions": True},
             words={"BEDROOM": "\u063a\u0631\u0641\u0629 \u0646\u0648\u0645", "BATH": "\u062d\u0645\u0627\u0645"}),
    _encoded("B01", "C05", "B01 with its window as an INSERT of a unit glazing block (xscale = the window width)",
             {"window_block": True}),
    _encoded("B01", "C06", "B01 whose walls are an external reference (XREF) to a file that is not supplied",
             {"xref_walls": "walls_not_supplied.dxf"},
             truth={"expect_state": "XREF_UNRESOLVED", "rooms": {}, "doors_m": [], "windows_m": [],
                    "passages_m": []}),
]
ENCODED_BY_ID = {c["id"]: c for c in ENCODED}
