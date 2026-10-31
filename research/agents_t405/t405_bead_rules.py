"""T-405 rules: PLASTER CORNER BEADS / PROFILES (BOQ family B4-09, unit m.l), any villa.

Research module (unwired). Pure functions, no I/O. It decides, edge by edge, which arrises of plastered faces take a
steel plaster angle bead and how long each is, with the evidence and a section 5 status per edge.

The physical element (ERS s.2.1). A plaster corner bead is a galvanised steel angle fixed along a CONVEX arris of a
plastered surface before the plaster coats, so the arris is straight and protected. It exists only where two
plastered surfaces meet at an outside corner. Its length is the length of plaster on BOTH sides of that arris. A
concave (internal) corner, an edge against a frame flush with the face, an edge where one side is tiled, clad or not
plastered, and an edge hidden above a ceiling or under a coping are not plaster arrises and take no plaster bead.

Owner basis (searched before anything else; WORKFLOW_CONTROLS s.4):
  URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1 (OD-V3-4): plaster corner beads / profiles are a separate m.l item wherever
      source geometry supports them, never buried in plaster.
  OD-V3B-8 STEEL_PLASTER_ANGLE_BEADS (owner, 2026-10-04; registers_v3b OWNER_METHOD_REGISTER; URBAN_STANDARD_CANDIDATE,
      Alsenan first): beads at exposed plaster edges: door / opening jambs, window edges (incl. below / around WHERE THE
      SITE METHOD REQUIRES), external plastered corners and exposed corners receiving a bead; never on a hidden or
      non-plastered edge; never on a fully tiled edge unless the project specifies it; segment record HOST, EDGE TYPE,
      LENGTH, SOURCE, FINISH POPULATION, STATUS.
  Q-37 A: where tile owns a face there is no plaster bead (the tile edge is B4-10, T-368).
  Q-55 C: internal door height 2.20 m where none is printed (ASSUMED - OWNER-APPROVED); a door-height fallback, never a
      head for a doorless opening or an arch springing (T-368 r2 lesson).

Edge classes (R-T405-1):
  EXTERNAL_CORNER   convex vertical arris between two plastered faces: column / pier proud of a wall, wall corner
                    turning into the room, obtuse corner (interior angle > 180 deg on the room polygon).
  WALL_END          the two arrises of a free wall end (nib / stub) standing into the room.
  DOOR_JAMB / DOOR_HEAD  the arris between a plastered face and the plastered door reveal (UP-FIN-PLASTER-001):
                    2 jambs x door height + head width, ON EACH PLASTERED FACE of the opening.
  WINDOW_JAMB / WINDOW_HEAD  same on the face that has a reveal (outside here); an arched head is measured on its
                    developed arc, never on the chord or the bounding rectangle (T-377).
  WINDOW_SILL_EDGE  the edge at / below the sill: OD-V3B-8 makes it conditional on the site method -> HELD by name.
  OPENING_UNDER_HEAD (passage, lift entrance, arch): wall-end arrises up to a head that must be read from a drawing.
  STOP_END          a horizontal plaster termination along a room perimeter (top under the decor ceiling or bottom at
                    the skirting): not a convex arris; a stop profile only when a rule or note asks for it -> HELD by name.
  NOT A BEAD (listed, never counted): INTERNAL_CORNER, FLUSH_FRAME (window frame flush with the room face: no reveal,
                    no arris), TILED_FACE, an arc facet (a drawn curve tessellated into short chords is ONE smooth
                    surface, not a string of arrises), HIDDEN (above a ceiling / under a coping).

Rules (research, proposed; scope every villa; provenance T-405):
  R-T405-1  The edge classes above; a bead is counted only on a convex arris with plaster on both sides.
  R-T405-2  Vertical arris length = overlap of the plaster intervals of its two faces. The owner manual method (the
            owner plaster height, G1 / Q-43 / Q-48 A) and the drawing-derived method (plaster top to the slab soffit /
            datum) are shown SIDE BY SIDE; a HELD interval gives a HELD length with the count kept (never 0).
  R-T405-3  A door / opening edge on a face is 2h + w when the face is plastered and the head lies at or below the
            LOWEST plaster top of that face under every method shown (then the plaster top does not matter); a tiled
            face gives no plaster bead (Q-37 A); a face whose finish is not in the face ledger is HELD by name.
  R-T405-4  One physical arris is counted once: a corner vertex read from two room polygons, or one opening face
            listed twice (two labels of one shared polygon), is refused. The two faces of one opening are two arrises.
  R-T405-5  A room-polygon vertex is an arris only if its turn is at least ARRIS_MIN_DEG and it is not inside a run of
            at least ARC_RUN equal facets with equal turns (a tessellated drawn arc); every arris is named by the wall /
            column entity that makes it (a counter or zone-line vertex is not a wall corner: T-368 R-T368-6).
  R-T405-6  A window frame drawn flush with the room face leaves no room-side arris (DRAWING-CONFIRMED 0, not a
            missing quantity). Arched window heads / arches: developed arc length only (basis ARC_DEVELOPED).
  R-T405-7  An opening without a drawn head (passage, lift entrance, arch springing not printed) is HELD by name with
            its arris count; its length is never a default door height and never the full storey.
  R-T405-8  Every edge carries one section 5 status; totals are reported per status and HELD / UNKNOWN never count as
            zero or as measured.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

VERIFIED = "VERIFIED"
DC = "DRAWING-CONFIRMED"
OA = "ASSUMED — OWNER-APPROVED"
HELD = "HELD"
UNKNOWN = "UNKNOWN"
NOT_BEAD = "NOT A BEAD"
STATUSES = (VERIFIED, DC, OA, HELD, UNKNOWN, NOT_BEAD)

ARRIS_MIN_DEG = 10.0     # a turn below this on a wall line is a drafting kink, not an arris
ARC_RUN = 3              # >= 3 consecutive equal facets with equal turns = a tessellated arc
FACET_TOL_M = 0.005
TURN_TOL_DEG = 0.5

CLASSES = ("EXTERNAL_CORNER", "WALL_END", "DOOR_JAMB_HEAD", "WINDOW_JAMB_HEAD", "WINDOW_SILL_EDGE",
           "OPENING_UNDER_HEAD", "MOUTH_WALL_END", "PARAPET_TOP", "SLAB_EDGE", "STAIR_EDGE", "VOID_EDGE",
           "CEILING_EDGE", "FENCE_EDGE", "STOP_END", "INTERNAL_CORNER", "FLUSH_FRAME", "TILED_FACE", "ARC_FACET")
BEAD_CLASSES = CLASSES[:14]


class BeadError(ValueError):
    pass


def to_m(value, unit):
    if value is None:
        return None
    if unit == "m":
        return float(value)
    if unit == "mm":
        return float(value) / 1000.0
    raise BeadError(f"unit {unit!r}: only m or mm")


# ------------------------------------------------------------------------------------------------- geometry (R-5)

def _ccw(points):
    pts = [tuple(map(float, p[:2])) for p in points]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) < 3:
        raise BeadError("a room polygon needs at least 3 vertices")
    a2 = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    if abs(a2) < 1e-12:
        raise BeadError("degenerate room polygon (zero area)")
    return pts if a2 > 0 else pts[::-1]


def turns(points):
    """(ccw points, signed turn in degrees at each vertex; positive = convex seen from inside the room)."""
    pts = _ccw(points)
    out = []
    n = len(pts)
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        v1 = (p1[0] - p0[0], p1[1] - p0[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        out.append(math.degrees(math.atan2(v1[0] * v2[1] - v1[1] * v2[0], v1[0] * v2[0] + v1[1] * v2[1])))
    return pts, out


def arris_vertices(points, min_deg=ARRIS_MIN_DEG):
    """Indices (in the ccw order) of the room polygon's convex wall arrises (reflex vertices seen from the room),
    excluding the facets of a tessellated arc. Returns (arris indices, arc-facet indices)."""
    pts, tr = turns(points)
    n = len(pts)
    a = [math.dist(pts[i - 1], pts[i]) for i in range(n)]          # incoming facet of vertex i
    b = [math.dist(pts[i], pts[(i + 1) % n]) for i in range(n)]    # outgoing facet of vertex i
    even = [abs(a[i] - b[i]) <= FACET_TOL_M and abs(tr[i]) < 45.0 for i in range(n)]
    facet = [False] * n
    # ARC_RUN equal facets = ARC_RUN - 1 consecutive 'even' vertices with equal turns
    for i in range(n):
        run = [(i + k) % n for k in range(ARC_RUN - 1)]
        if all(even[k] for k in run) and all(abs(tr[k] - tr[i]) <= TURN_TOL_DEG for k in run):
            for k in run:
                facet[k] = True
    arr = [i for i in range(n) if tr[i] <= -min_deg and not facet[i]]
    arc = [i for i in range(n) if tr[i] < 0 and facet[i]]
    return arr, arc


# ------------------------------------------------------------------------------------------------- intervals (R-2)

@dataclass(frozen=True)
class Top:
    """Plaster top of a face under one method: value_m None = HELD (count kept, never 0)."""
    value_m: float | None
    status: str
    source: str
    why_held: str = ""

    def __post_init__(self):
        if self.status not in STATUSES:
            raise BeadError(f"status {self.status!r}")
        if self.value_m is None and self.status not in (HELD, UNKNOWN):
            raise BeadError("a plaster top without a value must be HELD / UNKNOWN")
        if self.value_m is not None and self.status in (HELD, UNKNOWN):
            raise BeadError("a HELD plaster top carries no single value (use lo / hi in the note)")
        if self.value_m is not None and not (0.5 <= self.value_m <= 20.0):
            raise BeadError(f"plaster top {self.value_m} m outside 0.5 .. 20 m: unit error?")


@dataclass(frozen=True)
class Face:
    face_id: str
    finish: str            # PLASTER / TILE / CLAD / UNKNOWN
    owner: Top | None      # owner manual method
    dwg: Top | None        # drawing-derived method
    lo_any_m: float | None = None   # the lowest plaster top this face can have under any method shown (bounds)
    line_id: str = ""


def corner_length(face_a: Face, face_b: Face, method: str):
    """R-T405-2: overlap of both faces' plaster on one method; (length or None, status)."""
    if face_a.finish != "PLASTER" or face_b.finish != "PLASTER":
        return 0.0, NOT_BEAD
    ta, tb = getattr(face_a, method), getattr(face_b, method)
    if ta is None or tb is None or ta.value_m is None or tb.value_m is None:
        return None, HELD
    st = OA if OA in (ta.status, tb.status) else (DC if DC in (ta.status, tb.status) else VERIFIED)
    return min(ta.value_m, tb.value_m), st


def corner_edge(edge_id, room, cls, count, face, handles, source, note=""):
    if cls not in ("EXTERNAL_CORNER", "WALL_END"):
        raise BeadError(f"{cls} is not a vertical corner class")
    if count < 1:
        raise BeadError("a corner edge has a count of at least 1")
    lo, so = corner_length(face, face, "owner")
    ld, sd = corner_length(face, face, "dwg")
    return {"edge_id": edge_id, "scope": "INTERIOR", "room": room, "class": cls, "count": count,
            "owner_m": None if lo is None else round(lo * count, 4), "owner_status": so,
            "dwg_m": None if ld is None else round(ld * count, 4), "dwg_status": sd,
            "held_range": "" if lo is not None else (face.owner.why_held if face.owner else "owner top not given"),
            "line_id": face.line_id, "handles": handles, "basis": "VERTICAL", "source": source, "note": note}


# ------------------------------------------------------------------------------------------------- openings (R-3, R-6)

@dataclass(frozen=True)
class Opening:
    opening_id: str
    kind: str                 # DOOR / WINDOW / ARCH / PASSAGE / GATE
    width_m: float | None
    height_m: float | None
    height_status: str        # status of the height (Q-55 C -> OA; printed -> DC)
    head_basis: str = "STRAIGHT"   # STRAIGHT / ARC_DEVELOPED / CHORD / RECTANGLE
    head_m: float | None = None    # developed head length when the head is an arc


def opening_face_edge(edge_id, room, op: Opening, face: Face, source, note=""):
    """R-T405-3: the arris ring (2 jambs + head) of one opening on one face."""
    base = {"edge_id": edge_id, "scope": "INTERIOR", "room": room, "line_id": face.line_id, "handles": op.opening_id,
            "source": source, "note": note, "basis": op.head_basis}
    cls = "WINDOW_JAMB_HEAD" if op.kind == "WINDOW" else "DOOR_JAMB_HEAD"
    if op.kind in ("ARCH", "PASSAGE"):
        cls = "OPENING_UNDER_HEAD"
    if face.finish == "TILE":
        return {**base, "class": "TILED_FACE", "count": 1, "owner_m": 0.0, "owner_status": NOT_BEAD, "dwg_m": 0.0,
                "dwg_status": NOT_BEAD, "held_range": "", "note": (note + "; " if note else "")
                + "tiled face: tile edge (B4-10, T-368), never a plaster bead (Q-37 A, OD-V3B-8)"}
    if face.finish != "PLASTER":
        return {**base, "class": cls, "count": 1, "owner_m": None, "owner_status": HELD, "dwg_m": None,
                "dwg_status": HELD, "held_range": f"face finish {face.finish}: FACE_NOT_IN_FACE_LEDGER"}
    if op.head_basis in ("CHORD", "RECTANGLE"):
        raise BeadError(f"{op.opening_id}: an arched head measured as {op.head_basis} (R-T405-6: developed arc only)")
    if op.kind in ("ARCH", "PASSAGE") and op.height_status == OA:
        raise BeadError(f"{op.opening_id}: a door-height fallback is not a head for a doorless opening (R-T405-7)")
    if op.height_m is None or op.width_m is None:
        return {**base, "class": cls, "count": 1, "owner_m": None, "owner_status": HELD, "dwg_m": None,
                "dwg_status": HELD, "held_range": "opening height / head not established (count 2 jambs + head)"}
    head = op.head_m if op.head_basis == "ARC_DEVELOPED" else op.width_m
    if head is None:
        raise BeadError(f"{op.opening_id}: arc head without its developed length")
    ring = 2 * op.height_m + head
    if face.lo_any_m is None or face.lo_any_m < op.height_m:
        return {**base, "class": cls, "count": 1, "owner_m": None, "owner_status": HELD, "dwg_m": None,
                "dwg_status": HELD, "held_range": f"0 .. {ring:.4f}: the face's plaster top may lie below the head"}
    st = op.height_status
    return {**base, "class": cls, "count": 1, "owner_m": round(ring, 4), "owner_status": st,
            "dwg_m": round(ring, 4), "dwg_status": st, "held_range": ""}


def flush_window_face(edge_id, room, op: Opening, face: Face, source):
    """R-T405-6: frame flush with the room face: no reveal, no arris (listed with the evidence)."""
    return {"edge_id": edge_id, "scope": "INTERIOR", "room": room, "class": "FLUSH_FRAME", "count": 1,
            "owner_m": 0.0, "owner_status": NOT_BEAD, "dwg_m": 0.0, "dwg_status": NOT_BEAD, "held_range": "",
            "line_id": face.line_id, "handles": op.opening_id, "basis": "FLUSH", "source": source,
            "note": "window frame drawn flush with the room face (room-side reveal 0.000): no room-side arris"}


def held_edge(edge_id, scope, room, cls, count, why, line_id="", handles="", source="", physical_m=None, note=""):
    """R-T405-7: a known edge class whose bead length is not established: count kept, length None (never 0)."""
    if not why:
        raise BeadError("a HELD edge needs its cause by name")
    return {"edge_id": edge_id, "scope": scope, "room": room, "class": cls, "count": count, "owner_m": None,
            "owner_status": HELD, "dwg_m": None, "dwg_status": HELD,
            "held_range": why + ("" if physical_m is None else f"; physical edge {physical_m:.4f} m.l"),
            "line_id": line_id, "handles": handles, "basis": "", "source": source, "note": note}


def cited_edge(edge_id, scope, room, cls, count, length_m, status, source, line_id="", handles="", basis="",
               note=""):
    """An edge whose length comes from a merged ledger (cited, not re-derived), with that ledger's status."""
    if status not in STATUSES or status in (HELD, UNKNOWN, NOT_BEAD):
        raise BeadError(f"a cited measured edge needs a measured status, not {status!r}")
    if length_m is None or length_m <= 0:
        raise BeadError("a cited measured edge needs a positive length")
    return {"edge_id": edge_id, "scope": scope, "room": room, "class": cls, "count": count,
            "owner_m": round(length_m, 4), "owner_status": status, "dwg_m": round(length_m, 4), "dwg_status": status,
            "held_range": "", "line_id": line_id, "handles": handles, "basis": basis, "source": source, "note": note}


# ------------------------------------------------------------------------------------------------- checks (R-4, R-8)

def check_ledger(edges):
    """Refuse a ledger that double counts, beads a tiled face, holds as 0, measures an arc as a chord or mixes
    statuses with values. Returns the edges unchanged."""
    seen = set()
    for e in edges:
        if e["edge_id"] in seen:
            raise BeadError(f"{e['edge_id']}: one physical arris counted twice (R-T405-4)")
        seen.add(e["edge_id"])
        if e["class"] not in CLASSES:
            raise BeadError(f"{e['edge_id']}: class {e['class']!r}")
        for m, s in (("owner_m", "owner_status"), ("dwg_m", "dwg_status")):
            if e[s] not in STATUSES:
                raise BeadError(f"{e['edge_id']}: status {e[s]!r}")
            if e[s] in (HELD, UNKNOWN) and e[m] is not None:
                raise BeadError(f"{e['edge_id']}: a HELD edge carries no figure (held is never a number, never 0)")
            if e[s] not in (HELD, UNKNOWN) and e[m] is None:
                raise BeadError(f"{e['edge_id']}: a {e[s]} edge needs its length")
            if e[s] == NOT_BEAD and e[m] != 0.0:
                raise BeadError(f"{e['edge_id']}: a NOT A BEAD row carries 0.0 only")
            if e[s] not in (HELD, UNKNOWN, NOT_BEAD) and e["class"] not in BEAD_CLASSES:
                raise BeadError(f"{e['edge_id']}: {e['class']} is never a plaster bead")
        if e["class"] == "TILED_FACE" and e["owner_status"] != NOT_BEAD:
            raise BeadError(f"{e['edge_id']}: a bead counted on a tiled face (Q-37 A)")
        if e.get("basis") in ("CHORD", "RECTANGLE"):
            raise BeadError(f"{e['edge_id']}: arc measured as {e['basis']} (R-T405-6)")
        if e["owner_status"] in (HELD, UNKNOWN) and not e["held_range"]:
            raise BeadError(f"{e['edge_id']}: HELD without its cause")
    return edges


def check_corner_keys(keys):
    """R-T405-4 for corners read from several room polygons: keys = [(edge_id, vertex key)]; a vertex key shared by two
    edge ids is one arris counted twice."""
    owner = {}
    for eid, key in keys:
        if key in owner and owner[key] != eid:
            raise BeadError(f"vertex {key} counted by {owner[key]} and {eid}: one arris, one bead")
        owner[key] = eid
    return True


def totals(edges, method="owner"):
    """R-T405-8: m.l per status (and per class), HELD / UNKNOWN as counts only."""
    m, s = f"{method}_m", f"{method}_status"
    by_status, by_class, held = {}, {}, {}
    for e in edges:
        st = e[s]
        if st in (HELD, UNKNOWN):
            held[e["class"]] = held.get(e["class"], 0) + e["count"]
            continue
        if st == NOT_BEAD:
            continue
        by_status[st] = round(by_status.get(st, 0.0) + e[m], 4)
        by_class[e["class"]] = round(by_class.get(e["class"], 0.0) + e[m], 4)
    return {"measured_by_status_m": dict(sorted(by_status.items())),
            "measured_m": round(sum(by_status.values()), 4),
            "by_class_m": dict(sorted(by_class.items())),
            "held_edges_by_class": dict(sorted(held.items()))}
