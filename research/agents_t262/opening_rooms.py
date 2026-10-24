"""T-262 opening-to-room join by geometry (research, stdlib only, any villa; rules R-T262-1 .. 3 proposed).

Physical element: an opening is a gap through ONE wall. Its jambs cut the wall's two faces; the room on each face at the
opening (or no room: outdoors, a court, a roof) is the opening's side A / side B. So the room of an opening is found by
walking square to the opening line from the opening, on both sides, until a room region is entered; never from a label,
a room name, an engine id or the order of a ledger.

  probe_track     walk from one station along +n or -n (START_M .. MAX_M, STEP_M): the runs of room / no room it is
                  in; probe_side = the first room entered (None = no room within MAX_M: outdoors / not a walked room).
  join_opening    one station every 5 cm along the opening line; a side is ESTABLISHED when every station finds the
                  same room (or none), MULTI_ROOM when every station finds a room but not the same one (the opening
                  serves several rooms on that side, e.g. a glazing band with a partition stopping on it), SPLIT when
                  some find a room and some none (not established: refused as a value). A region that covers the
                  opening's own reveal is named (REVEAL_IN_REGION) and the side is the room beyond it.
  label_verdict   what a census label CLAIMS (its room set, read once by the room's name) against the geometric pair:
                  AGREE / AGREE_OPEN_ZONE (label and geometry name two parts of one space that no wall divides: a clip
                  box) / LABEL_INCOMPLETE (the label names one of several rooms the opening serves) / LABEL_WRONG /
                  NOT_ESTABLISHED. A label never overrides geometry.
  door_pair_check a door (or a leafless opening) inside the building has a room on BOTH sides, unless one side is
                  established as no-room; a door given one room only, with the other side not established, is refused.
  strip_overlaps  a room region that covers a wall strip (the band between a wall's two drawn faces) by more than
                  OVERLAP_MIN_M2 is listed with the strip's two face handles: that region's contour runs on the FAR face
                  of the wall, so the far face is counted in two rooms and the near face in none.

Every input is plain data (lists of (x, y) in metres); nothing here reads a file, a project or a name.
"""
from __future__ import annotations

import math

START_M = 0.02      # off the opening line (a door closure / glazing line is the room boundary itself)
STEP_M = 0.01
MAX_M = 0.70        # > a 0.30 m wall with finishes and frame + a 0.40 m reveal; < a room's depth
OVERLAP_MIN_M2 = 0.02   # the region builder grows faces 0.015 m onto the drawn lines: contact is not overlap


# ------------------------------------------------------------------ geometry (stdlib)
def _in_ring(p, ring):
    x, y = p
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xc = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xc > x:
                inside = not inside
    return inside


def in_room(p, parts):
    """parts: [{"ext": [(x, y), ...], "holes": [[...], ...]}, ...] -> point inside any part (not in its holes)."""
    for pt in parts:
        if _in_ring(p, pt["ext"]) and not any(_in_ring(p, h) for h in pt.get("holes", [])):
            return True
    return False


def probe_track(station, sign, rooms, start=START_M, step=STEP_M, dmax=MAX_M):
    """walk from one station along sign * n; -> [(room_id | None, d_enter, d_exit)] runs of what the walk is in."""
    (px, py), (nx, ny) = station["p"], station["n"]
    runs, k = [], 0
    while True:
        d = round(start + k * step, 6)
        if d > dmax + 1e-9:
            return runs
        q = (px + sign * nx * d, py + sign * ny * d)
        hits = [rid for rid, parts in rooms.items() if in_room(q, parts)]
        if len(hits) > 1:
            raise ValueError(f"point inside two room regions {sorted(hits)}: overlapping regions refused")
        cur = hits[0] if hits else None
        if runs and runs[-1][0] == cur:
            runs[-1] = (cur, runs[-1][1], d)
        else:
            runs.append((cur, d, d))
        k += 1


def _first_room(track, skip=None):
    for rid, d0, _ in track:
        if rid is not None and rid != skip:
            return rid, round(d0, 3)
    return None, None


def probe_side(station, sign, rooms, start=START_M, step=STEP_M, dmax=MAX_M):
    """-> (first room entered | None, distance_m | None)"""
    return _first_room(probe_track(station, sign, rooms, start, step, dmax))


INNER_GAP_MAX_M = 0.30   # a no-room run inside the opening line, flanked by rooms, no longer than a wall thickness


def _side(per, spacing):
    """per: [(room | None, d)] in station order along the opening line."""
    ids = [r if r is not None else "NO_ROOM" for r, _ in per]
    flags = []
    # an interior no-room run between rooms, no longer than INNER_GAP_MAX_M: a wall end stopping against the opening
    # or a return of the probe line along a jamb (the probe then runs inside the wall). It is not a side of the
    # opening; it is named with its position along the line
    k, keep = 0, [True] * len(ids)
    while k < len(ids):
        if ids[k] == "NO_ROOM":
            j = k
            while j < len(ids) and ids[j] == "NO_ROOM":
                j += 1
            interior = k > 0 and j < len(ids)
            if interior and (j - k) * spacing <= INNER_GAP_MAX_M + 1e-9:
                for q in range(k, j):
                    keep[q] = False
                flags.append(f"NO_ROOM_RUN_IN_LINE:{ids[k - 1]}|{ids[j]}:{round((j - k) * spacing, 3)}m"
                             f"@{round(k * spacing, 3)}m")
            k = j
        else:
            k += 1
    kept = [x for x, ok in zip(ids, keep) if ok]
    shares = {}
    for r in kept:
        shares[r] = shares.get(r, 0) + 1
    shares = {k2: round(v / len(kept), 4) for k2, v in shares.items()}
    if len(shares) == 1:
        st = {"state": "ESTABLISHED", "room": next(iter(shares)), "rooms": set(shares), "shares": shares}
    elif "NO_ROOM" not in shares:
        st = {"state": "MULTI_ROOM", "room": None, "rooms": set(shares), "shares": shares}
    else:
        st = {"state": "SPLIT", "room": None, "rooms": set(shares), "shares": shares}
    st["flags"] = flags
    return st


def join_opening(op, rooms):
    """op: {"stations": [{"p", "n"}, ...]} (side A = +n). -> {"A": side, "B": side, "flags": [...]}.
    side state: ESTABLISHED (one room, or NO_ROOM on every station), MULTI_ROOM (every station finds a room, more
    than one: the opening serves several rooms on that side; station shares, not lengths), SPLIT (some stations find a room and
    some none: not established, refused as a value).
    A region that covers the opening's own reveal (the opening line lies INSIDE one room region on both sides at the
    first step) is named REVEAL_IN_REGION and the side is the next room the walk enters beyond it. A no-room run
    inside the line, flanked by rooms, <= INNER_GAP_MAX_M (a wall end against the opening, a jamb return of the probe
    line) is named NO_ROOM_RUN_IN_LINE and is not a side."""
    st = op.get("stations", [])
    if len(st) < 2:
        raise ValueError("an opening needs at least two probe stations along its line")
    tracks = {s: [probe_track(x, sg, rooms) for x in st] for s, sg in (("A", 1.0), ("B", -1.0))}
    flags = []
    per = {"A": [], "B": []}
    for i in range(len(st)):
        ra, da = _first_room(tracks["A"][i])
        rb, db = _first_room(tracks["B"][i])
        if ra is not None and ra == rb and da is not None and db is not None and da <= START_M + 1e-9 \
                and db <= START_M + 1e-9:
            # the opening line itself is inside one region: look beyond that region on each side
            na, nda = _first_room(tracks["A"][i], skip=ra)
            nb, ndb = _first_room(tracks["B"][i], skip=rb)
            if na is not None or nb is not None:
                flags.append(f"REVEAL_IN_REGION:{ra}")
                ra, da = (na, nda) if na is not None else (ra, da)
                rb, db = (nb, ndb) if nb is not None else (rb, db)
        per["A"].append((ra, da))
        per["B"].append((rb, db))
    spacing = float(op.get("line_m", 0.05 * len(st))) / len(st)
    out = {"A": _side(per["A"], spacing), "B": _side(per["B"], spacing)}
    out["flags"] = sorted(set(flags)) + out["A"]["flags"] + out["B"]["flags"]
    out["A"]["per_station"], out["B"]["per_station"] = per["A"], per["B"]
    if out["A"]["state"] == "ESTABLISHED" and out["A"]["room"] != "NO_ROOM" and out["A"]["room"] == out["B"]["room"]:
        out["flags"].append("SAME_ROOM_BOTH_SIDES")     # a doorless mouth inside one room (a niche): named
    return out


# ------------------------------------------------------------------ labels against geometry
NOT_SETTLED = ("SPLIT",)


def _side_match(lab, geo_rooms, zone_of, loose):
    def ok(r):
        return r in lab or (loose and r in zone_of and bool(zone_of[r] & set(lab)))
    hit = [r for r in geo_rooms if ok(r)]
    if not hit:
        return 0
    return 2 if len(hit) == len(geo_rooms) else 1        # 2 every geometric room claimed, 1 only some


def label_verdict(label_sets, geo, open_zones=()):
    """label_sets: (set_a, set_b) of room ids the census label CLAIMS for its two sides ("NO_ROOM" for no walked
    room: outdoors or an interior space with no region); geo: join_opening result. Sides are compared as an unordered
    pair (the census order is not a geometric side). open_zones: sets of room ids that are one space split only by a
    clip box (no wall). -> AGREE / AGREE_OPEN_ZONE / LABEL_INCOMPLETE (the label names one of several rooms the
    opening serves) / LABEL_WRONG / NOT_ESTABLISHED. A label never changes the geometric result."""
    if any(geo[s]["state"] in NOT_SETTLED for s in ("A", "B")):
        return "NOT_ESTABLISHED"
    zone_of = {}
    for z in open_zones:
        for r in z:
            zone_of[r] = frozenset(z)
    ga, gb = geo["A"]["rooms"], geo["B"]["rooms"]
    best = 0
    for loose in (False, True):
        for la, lb in ((label_sets[0], label_sets[1]), (label_sets[1], label_sets[0])):
            m = (_side_match(la, ga, zone_of, loose), _side_match(lb, gb, zone_of, loose))
            if m == (2, 2):
                return "AGREE" if not loose else "AGREE_OPEN_ZONE"
            if 0 not in m:
                best = max(best, 1)
    return "LABEL_INCOMPLETE" if best else "LABEL_WRONG"


def door_pair_check(kind, geo):
    """a door / gate / leafless opening has two settled sides; one room with the other side not settled is refused
    (never 'the door belongs to the room the label names')."""
    if kind not in ("DOOR", "GATE", "OPENING"):
        return "N/A"
    if any(geo[s]["state"] in NOT_SETTLED for s in ("A", "B")):
        return "REFUSED_ONE_SIDE_NOT_ESTABLISHED"
    return "TWO_SIDES"


# ------------------------------------------------------------------ room regions over wall strips
def _poly_area(r):
    return abs(sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r)))) / 2.0


def _clip(subject, a, b):
    """Sutherland-Hodgman: keep the part of `subject` left of the directed edge a -> b."""
    def left(p):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-12

    def cut(p, q):
        x1, y1, x2, y2 = p[0], p[1], q[0], q[1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        den = dx * (y2 - y1) - dy * (x2 - x1)
        t = (dy * (x1 - a[0]) - dx * (y1 - a[1])) / den
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    out = []
    n = len(subject)
    for i in range(n):
        p, q = subject[i], subject[(i + 1) % n]
        if left(q):
            if not left(p):
                out.append(cut(p, q))
            out.append(q)
        elif left(p):
            out.append(cut(p, q))
    return out


def ring_in_convex(ring, quad):
    """area of a simple ring inside a convex quadrilateral (counter-clockwise or clockwise)."""
    q = list(quad)
    if sum(q[i][0] * q[(i + 1) % 4][1] - q[(i + 1) % 4][0] * q[i][1] for i in range(4)) < 0:
        q = q[::-1]
    # a non-convex ring clipped by a convex window: Sutherland-Hodgman keeps the area exactly (degenerate
    # connecting edges have no area)
    pts = [p for p in ring]
    if pts and pts[0] == pts[-1]:
        pts = pts[:-1]
    for i in range(4):
        if not pts:
            return 0.0
        pts = _clip(pts, q[i], q[(i + 1) % 4])
    return _poly_area(pts) if len(pts) >= 3 else 0.0


def strip_overlaps(rooms, strips, min_m2=OVERLAP_MIN_M2):
    """rooms: {room_id: parts}; strips: [{"handles": (h1, h2), "quad": [4 points], "t_m", "overlap_m"}].
    -> [{"room", "handles", "t_m", "overlap_m2"}] for every room region covering a strip by more than min_m2."""
    out = []
    for rid, parts in rooms.items():
        for s in strips:
            a = sum(ring_in_convex(pt["ext"], s["quad"]) - sum(ring_in_convex(h, s["quad"]) for h in pt.get("holes", []))
                    for pt in parts)
            if a > min_m2:
                out.append({"room": rid, "handles": tuple(s["handles"]), "t_m": s["t_m"], "overlap_m2": round(a, 4)})
    return out
