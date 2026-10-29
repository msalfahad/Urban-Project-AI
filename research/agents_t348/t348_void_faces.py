"""T-348 research rules (not a method, not wired): faces round a void / recess open to outside air.

R-T348-1  A face is classified by what it faces, not by the storey it stands in: a face towards outside air (a void
          open to the sky or to an open court, a roofed recess open on one side, owner Q-67 A: open to outside air
          without enclosing doors or glazing) is EXTERIOR; a face towards a room is INTERIOR; a face above the roof it
          stands on is a PARAPET face (outer or inner), never a storey facade face.
R-T348-2  Faces stacked in depth (a screen standing in front of a recessed wall) are separate faces, each measured once
          in its own plane: screen front, screen back, the screen opening's intrados (a reveal), the recessed wall, the
          soffit over the recess. An elevation shows them as one plane; a projected width is never a face length. The
          screen opening is deducted from both screen faces (full hole, owner Q-73 A); the recessed wall keeps its own
          window.
R-T348-3  A face already carried by a ledger key is bound to that key, never emitted again (cross-check 0.000 m2); a
          ledger row that describes no physical face (a 'slab edge below' where the lower roof runs on in front) is
          reported NOT_A_FACE with its evidence, never measured.
R-T348-4  A face whose height or hole is not settled by a printed source is HELD with its bound beside it, blank in
          the quantity column, never 0; a freelancer row is evidence to trace, never a quantity.

Pure functions; metres, m2. No drawing, coordinate or client data in this module."""
import math

STATUSES = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN")


class T348Error(ValueError):
    pass


# ----------------------------------------------------------------------------------------------- R-T348-1
def classify(faces, top, roof_level=None):
    """faces: 'OPEN_AIR' | 'ROOM' | 'ROOF' (what the face looks onto); top: the face's top level; roof_level: the
    level of the roof the face stands on, when it stands on one. Returns the owner family of the face."""
    if faces not in ("OPEN_AIR", "ROOM", "ROOF"):
        raise T348Error("unknown side: %r" % (faces,))
    if faces == "ROOF":
        return "PARAPET-INNER"
    if faces == "ROOM":
        return "INTERIOR"
    if roof_level is not None and top is not None and top > roof_level + 1e-9:
        raise T348Error("face rises above the roof it stands on: split it at the roof level first")
    return "EXTERIOR"


def split_at_roof(bottom, top, roof_level):
    """Split a face band at the roof level: below = storey face, above = parapet face."""
    if top <= roof_level:
        return [("STOREY", bottom, top)]
    if bottom >= roof_level:
        return [("PARAPET", bottom, top)]
    return [("STOREY", bottom, roof_level), ("PARAPET", roof_level, top)]


# ----------------------------------------------------------------------------------------------- geometry
def poly_area(pts):
    s = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def path_length(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def segment_area(r, chord):
    """Circular segment between an arc of radius r and its chord."""
    if chord <= 0 or chord > 2 * r:
        raise T348Error("chord outside the circle")
    h = chord / 2.0
    d = math.sqrt(r * r - h * h)
    return r * r * math.acos(d / r) - d * h


def arc_length(r, chord):
    return 2 * r * math.asin(chord / (2 * r))


# ----------------------------------------------------------------------------------------------- R-T348-2
def screen_faces(width, bottom, roof_level, top, hole_lo, hole_hi, depth, hole_perim_lo, hole_perim_hi):
    """A screen of `width` between piers, standing from `bottom` to `top`, roofed behind at `roof_level`, with one
    opening whose area lies wholly below `roof_level` and is bounded [hole_lo, hole_hi] (two drawn edges), and whose
    intrados runs `depth` deep along a developed perimeter [hole_perim_lo, hole_perim_hi] (legs + head, no sill).
    Returns the faces of R-T348-2 (front storey, front parapet, back storey, intrados)."""
    if not (bottom < roof_level < top):
        raise T348Error("levels out of order")
    if hole_lo > hole_hi or hole_perim_lo > hole_perim_hi:
        raise T348Error("bound reversed")
    gross = width * (roof_level - bottom)
    if hole_hi > gross:
        raise T348Error("hole larger than its face")
    par = width * (top - roof_level)
    out = []
    for name in ("SCREEN-FRONT", "SCREEN-BACK"):
        out.append(dict(face=name, band="storey", bottom=bottom, top=roof_level, length=width, gross=gross,
                        hole_lo=hole_lo, hole_hi=hole_hi, net_lo=gross - hole_hi, net_hi=gross - hole_lo))
    out.append(dict(face="SCREEN-FRONT", band="parapet", bottom=roof_level, top=top, length=width, gross=par,
                    hole_lo=0.0, hole_hi=0.0, net_lo=par, net_hi=par))
    out.append(dict(face="SCREEN-INTRADOS", band="reveal", bottom=bottom, top=None, length=None,
                    gross=None, hole_lo=0.0, hole_hi=0.0, net_lo=depth * hole_perim_lo, net_hi=depth * hole_perim_hi))
    return out


# ----------------------------------------------------------------------------------------------- R-T348-3 / 4
def bind(faces, ledger_keys):
    """faces: dicts with 'key' (the physical face id) and 'bound_to' (an existing ledger key or None). Refuses a
    face bound to a key the ledger does not hold, a key claimed twice, and a NEW face whose key the ledger holds."""
    seen = set()
    for f in faces:
        k = f["key"]
        if k in seen:
            raise T348Error("face %s emitted twice" % k)
        seen.add(k)
        b = f.get("bound_to")
        if b is not None and b not in ledger_keys:
            raise T348Error("face %s bound to a key the ledger does not hold: %s" % (k, b))
        if b is None and k in ledger_keys:
            raise T348Error("face %s is already in the ledger: bind it, do not emit it as NEW" % k)
    claimed = [f["bound_to"] for f in faces if f.get("bound_to")]
    if len(claimed) != len(set(claimed)):
        raise T348Error("one ledger key bound by two faces")
    return True


def overlap_m2(faces_inside, faces_outside):
    """Sum of m2 of physical faces present in both an interior and an exterior set (must be 0.000)."""
    ins = {f["key"]: f for f in faces_inside}
    tot = 0.0
    for f in faces_outside:
        if f["key"] in ins:
            raise T348Error("face %s counted inside and outside" % f["key"])
    return tot


def fill_row(face_id, status, m2=None, lo=None, hi=None, source="drawing"):
    """One FILL row for the lane I package. HELD -> m2 blank with its bound; a figure needs a drawing source."""
    if status not in STATUSES:
        raise T348Error("unknown status %r" % (status,))
    if source != "drawing":
        raise T348Error("a FILL quantity comes from the drawing, never from %s" % source)
    if status in ("HELD", "UNKNOWN"):
        if m2 is not None:
            raise T348Error("HELD / UNKNOWN row with a point value")
        if lo is not None and hi is not None and lo > hi:
            raise T348Error("bound reversed")
        return dict(face=face_id, status=status, m2="", lo="" if lo is None else "%.6f" % lo,
                    hi="" if hi is None else "%.6f" % hi)
    if m2 is None:
        raise T348Error("%s row without a figure" % status)
    if m2 <= 0:
        raise T348Error("a measured face has a positive area")
    return dict(face=face_id, status=status, m2="%.6f" % m2, lo="", hi="")


def reconcile(his_total, parts, tol=1e-6):
    """parts: [(name, m2)] named terms (drawn faces matched, double counts, band terms, no-face parts); they must
    add up to his total, residual reported and refused above tol."""
    for n, v in parts:
        if v is None:
            raise T348Error("part %s has no value: an unresolved part is named with its m2, never None" % n)
    s = sum(v for _, v in parts)
    res = his_total - s
    if abs(res) > tol:
        raise T348Error("parts do not add up: residual %.6f" % res)
    return round(res, 6)


def his_row_as_quantity(row):
    """Guard used by the tests: a freelancer row is never a face quantity."""
    raise T348Error("freelancer row %s is evidence to trace, never a quantity" % (row,))
