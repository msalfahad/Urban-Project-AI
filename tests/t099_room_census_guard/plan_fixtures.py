"""T-099 synthetic plan (NOT a client drawing): nine closed rooms drawn in mm with ezdxf, read back through the
architectural route's own reader composition (urban_intake.read + arch_intake.read_arch + ellipse chords), then turned
into faces by arch_rooms.spaces with the ARCH_TAKEOFF_V2.11 flags. Layer names deliberately unlike any project's:
PARTITIONS-200 (wall), FF-FURN (furniture), SAN-PLUMB (sanitary), TXT-ROOMS (labels).

Every room is its own closed inside-face rectangle on the wall layer (200 mm walls, no doors), inside an L-shaped
outer outline (0,0) (9150,0) (9150,1350) (8000,1350) (8000,6600) (0,6600): 8.00 x 6.60 + 1.15 x 1.35 = 54.3525 m2.
Every gap between two rooms, and between a room and the outline, is one 200 mm wall, so no face but the nine rooms is
wider than a wall. Hand areas (local mm, before any transform):
    BED     200..4200 x 200..4200   'BEDROOM'          4.00 x 4.00          = 16.0000 m2  labelled room
    WC08    4400..5400 x 200..1000  'W.C.'             1.00 x 0.80          =  0.8000 m2  2A/P = 1.6/3.6 = 0.444 < 0.45:
                                                                                         a WALL face for the room
                                                                                         builder -> HELD
                                                                                         SUB_THRESHOLD_LABELLED (wet)
    SHAFT09 4400..5350 x 1200..2150  (no label)        0.95 x 0.95          =  0.9025 m2  2A/P = 0.475: a SLIVER ->
                                                                                         stays SLIVER
    DUCT    4400..4800 x 2350..6200 'DUCT'             0.40 x 3.85          =  1.5400 m2  2A/P = 3.08/8.5 = 0.362: thin
                                                                                         -> HELD THIN_FACE_LABELLED
    UBLOCK  5600..7800 x 200..2200   (no label)        2.20 x 2.00          =  4.4000 m2  a WC block on its north wall
                                                                                         -> TYPED_BY_EVIDENCE WET
    ULOOSE  5000..7800 x 2400..4400  (no label)        2.80 x 2.00          =  5.6000 m2  a WC drawn as loose lines:
                                                                                         on FF-FURN -> HELD (Q-13 B);
                                                                                         on SAN-PLUMB -> WET
    UNONE   200..4200 x 4400..6400   (no label)        4.00 x 2.00          =  8.0000 m2  nothing inside -> HELD
                                                                                         UNLABELLED_ROOM
    BATH    5000..7800 x 4600..6400 'حمام'              2.80 x 1.80          =  5.0400 m2  labelled room (wet)
    STORE09 8000..8950 x 200..1150  'STORE'            0.95 x 0.95          =  0.9025 m2  a labelled SLIVER -> HELD
                                                                                         SUB_THRESHOLD_LABELLED (dry)
    rooms 16.0 + 0.8 + 0.9025 + 1.54 + 4.4 + 5.6 + 8.0 + 5.04 + 0.9025 = 43.185 m2; the wall faces carry the rest,
    54.3525 - 43.185 = 11.1675 m2 (HAND_WALL_MASS)
"""

from __future__ import annotations

import math

import ezdxf
from ezdxf.math import Matrix44

WALL, FURN, SAN, NAMES = "PARTITIONS-200", "FF-FURN", "SAN-PLUMB", "TXT-ROOMS"
ROLES = {WALL: "WALL", FURN: "OTHER", SAN: "OTHER", NAMES: "OTHER", "0": "OTHER"}
OUTER = [(0, 0), (9150, 0), (9150, 1350), (8000, 1350), (8000, 6600), (0, 6600)]
ROOMS = {   # id: (x0, y0, x1, y1, label or None, label point)
    "BED": (200, 200, 4200, 4200, "BEDROOM", (2200, 2200)),
    "WC08": (4400, 200, 5400, 1000, "W.C.", (4900, 600)),
    "SHAFT09": (4400, 1200, 5350, 2150, None, None),
    "DUCT": (4400, 2350, 4800, 6200, "DUCT", (4600, 4275)),
    "UBLOCK": (5600, 200, 7800, 2200, None, None),
    "ULOOSE": (5000, 2400, 7800, 4400, None, None),
    "UNONE": (200, 4400, 4200, 6400, None, None),
    "BATH": (5000, 4600, 7800, 6400, "حمام", (6400, 5500)),
    "STORE09": (8000, 200, 8950, 1150, "STORE", (8475, 675)),
}
HAND_M2 = {k: (x1 - x0) * (y1 - y0) / 1e6 for k, (x0, y0, x1, y1, _l, _p) in ROOMS.items()}
HAND_LITERALS = {"BED": 16.0, "WC08": 0.8, "SHAFT09": 0.9025, "DUCT": 1.54, "UBLOCK": 4.4, "ULOOSE": 5.6,
                 "UNONE": 8.0, "BATH": 5.04, "STORE09": 0.9025}
HAND_OUTER_M2 = 8.0 * 6.6 + 1.15 * 1.35                           # 52.80 + 1.5525 = 54.3525 m2
HAND_WALL_MASS = HAND_OUTER_M2 - sum(HAND_LITERALS.values())     # 54.3525 - 43.185 = 11.1675 m2
EXPECT = {   # room -> (census status, reason or None, wet_dry)
    "BED": ("LABELLED", None, None),
    "WC08": ("HELD", "SUB_THRESHOLD_LABELLED", "WET"),
    "SHAFT09": ("SLIVER", None, None),
    "DUCT": ("HELD", "THIN_FACE_LABELLED", "NONE"),
    "UBLOCK": ("TYPED_BY_EVIDENCE", "FIXTURES_TOILET", "WET"),
    "ULOOSE": ("HELD", "UNLABELLED_ROOM", "REVIEW"),
    "UNONE": ("HELD", "UNLABELLED_ROOM", "REVIEW"),
    "BATH": ("LABELLED", None, None),
    "STORE09": ("HELD", "SUB_THRESHOLD_LABELLED", "DRY"),
}


def _rect(msp, x0, y0, x1, y1, layer):
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": layer})


def _blocks(doc):
    b = doc.blocks.new("WC-WALLHUNG")                     # a WC block: cistern on the wall, elliptical pan
    _rect(b, -250, 0, 250, 200, "0")
    b.add_ellipse((0, -300), major_axis=(0, 300), ratio=200 / 300, dxfattribs={"layer": "0"})
    b = doc.blocks.new("COOKER-4")                        # a kitchen appliance (no sanitary meaning)
    _rect(b, 0, 0, 600, 600, "0")


def _loose_wc(msp, layer):
    """a water closet drawn as loose lines in ULOOSE: cistern 0.50 x 0.20 on the north wall face (y 4400), bowl
    0.40 x 0.60 touching it."""
    _rect(msp, 6450, 4200, 6950, 4400, layer)
    msp.add_ellipse((6700, 3900), major_axis=(0, 300), ratio=200 / 300, dxfattribs={"layer": layer})


def transform_matrix(transform):
    """'none' | 'rot30' | 'mirror' | 'metres' | 'rot30_mirror_metres' -> (Matrix44, unit scale)."""
    m = Matrix44()
    if "mirror" in transform:
        m = m @ Matrix44.scale(-1, 1, 1)
    if "rot30" in transform:
        m = m @ Matrix44.z_rotate(math.radians(30))
    m = m @ Matrix44.translate(41_000, -27_000, 0)       # far from the origin, as real sheets are
    scale = 0.001 if "metres" in transform else 1.0
    if scale != 1.0:
        m = m @ Matrix44.scale(scale, scale, scale)
    return m, scale


def plan_dxf(path, *, transform="none", wc_layer=FURN, drop=(), cooker_in_unone=False):
    """write the plan (drop: room ids whose LABEL is left out; cooker_in_unone: a COOKER-4 block in UNONE at
    (400, 4600)); -> {room id: its centre in drawing units}."""
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 6 if "metres" in transform else 4
    for name in (WALL, FURN, SAN, NAMES):
        doc.layers.add(name)
    _blocks(doc)
    msp = doc.modelspace()
    msp.add_lwpolyline(OUTER, close=True, dxfattribs={"layer": WALL})
    for k, (x0, y0, x1, y1, label, pt) in ROOMS.items():
        _rect(msp, x0, y0, x1, y1, WALL)
        if label and k not in drop:
            msp.add_text(label, dxfattribs={"layer": NAMES, "height": 100}).set_placement(pt)
    msp.add_blockref("WC-WALLHUNG", (6700, 2000), dxfattribs={"layer": FURN})
    _loose_wc(msp, wc_layer)
    if cooker_in_unone:
        msp.add_blockref("COOKER-4", (400, 4600), dxfattribs={"layer": FURN})
    m, _ = transform_matrix(transform)
    for e in list(msp):
        e.transform(m)
    doc.saveas(str(path))
    return {k: tuple(m.transform(((x0 + x1) / 2, (y0 + y1) / 2, 0)))[:2]
            for k, (x0, y0, x1, y1, _l, _p) in ROOMS.items()}


def read_plan(path):
    """the architectural route's entities, composed as tools/urban_boq_m9._arch_compute does."""
    from tools import arch_intake as AI
    from tools import urban_intake as UI
    E = UI.read(str(path))
    A = AI.read_arch(path, unit_m=E.get("unit_m"))
    chords = AI.ellipse_chords(E.get("ellipses") or [], E["unit_m"])
    return dict(E, texts=A["texts"], inserts=A["inserts"], segments=E["segments"] + A["extra_segments"] + chords,
                arcs=E["arcs"] + A["extra_arcs"])


def spaces_v211(ents):
    """arch_rooms.spaces with the flags ARCH_TAKEOFF_V2.11 passes (tools/urban_boq_m9._arch_compute)."""
    from engine.source import arch_rooms as AR
    from engine.source import robust_geometry as RG
    from engine.source import room_vocab as RV
    u = ents["unit_m"]
    return AR.spaces(ents, ROLES, u, region_id="T099", geom=RG.Geometry(u), release_safety=True, door_review=True,
                     v27=True, v271={"scenario": None}, v29=True, vocab=RV.VOCAB_ID)
