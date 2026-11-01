"""LIFT_ENTRANCE_MARBLE_V1 (T-413, research only; stdlib): the elevator landing marble at every lift entrance, for any
villa. Nothing here is wired into a method; engine/elevator_marble.py (ELEVATOR_LANDING_MARBLE_V1) is read, not edited.

The physical element (ERS s.2.1), per LANDING DOOR (a station, UP-ELEV-001):
  * B6-06 ELEVATOR OUTER SURROUND: marble on LEFT, TOP and RIGHT of the outer landing door, on the landing wall face,
    measured as the UNION area of the three bands (UP-ELEV-003), its outer edge length kept beside it (never instead).
  * B6-07 ELEVATOR THRESHOLD: the marble step at the door, width x depth in m2 and its exposed front edge in m.l
    (UP-ELEV-005), its own object: never a door threshold (B3-04), never a transition profile (B3-07), never porcelain.

Rules (R-T413-1 .. 7):
  R-T413-1 one station per landing DOOR: a floor with two doors into the shaft is two stations; one-per-floor (or
           one-per-shaft) counting is refused when the plan shows more doors.
  R-T413-2 the clear width comes from the drawn jamb lines (or a printed dimension): DRAWING-CONFIRMED; never a default.
  R-T413-3 each surround band width: printed / drawn -> DRAWING-CONFIRMED; else the owner default UP-ELEV-002 (0.50 m)
           -> ASSUMED — OWNER-APPROVED with its source; a default with no source is refused; a default never replaces
           a drawn width; a default wider than the landing wall face available beside that jamb (to the next corner or
           opening, measured on the plan) is INFEASIBLE -> that band is HELD with the bound (0, available].
  R-T413-4 the surround AREA needs the door clear height h (the head level). h not printed -> the area is HELD with
           A(h) = h x (L + R) + T x (W + L + R) kept as the formula, AT_LEAST the top band T x (W + L + R), AT_MOST the
           value at h_max = storey height (F.F.L. to F.F.L.) - T. Never a default h, never the freelancer's.
  R-T413-5 threshold: width = the drawn clear width (a known dimension is never replaced); depth printed, else the owner
           fallback depth UP-ELEV-005 (0.50 m) -> ASSUMED — OWNER-APPROVED; area W x D, front edge W (m.l).
  R-T413-6 ownership: the threshold area that lies on a landing floor face is taken out of that floor-finish line
           (THRESHOLD n PORCELAIN = 0, UP-ELEV-005); where the depth's position across the wall band is not drawn, the
           overlap is the bound [D - wall band, D] and stays HELD; the opening band itself belongs to no floor face.
  R-T413-7 no double count: a lift opening is never a door (UP-DOOR-CLS-005), so it never carries a B3-04 door
           threshold or an ARCH.THRESHOLD strip; it is never a B3-07 transition profile (T-409); a jamb / head arris
           covered by the surround carries no plaster corner bead (B4-09) once the surround is established.
"""
from __future__ import annotations

MODEL = "LIFT_ENTRANCE_MARBLE_V1"

DRAWING = "DRAWING-CONFIRMED"
OWNER = "ASSUMED — OWNER-APPROVED"
HELD = "HELD"
UNKNOWN = "UNKNOWN"

SURROUND_DEFAULT_M = 0.50       # UP-ELEV-002 v1.0.0 value 0.5 (owner_confirmed, DEFAULT)
THRESHOLD_DEFAULT_DEPTH_M = 0.50  # UP-ELEV-005 v1.1.0 value depth_m 0.5 (owner_confirmed, DEFAULT)
SURROUND_SOURCE = "UP-ELEV-002 v1.0.0 (URBAN_PROJECTS_RULE_LIBRARY 1.4.0; owner addendum 2026-09-17 s.I)"
THRESHOLD_SOURCE = "UP-ELEV-005 v1.1.0 (URBAN_PROJECTS_RULE_LIBRARY 1.4.0; owner addendum 2026-09-17 s.L, 6E-A s.16)"

FORBIDDEN_LINE_CODES = ("FIN.MARBLE.THRESHOLD", "ARCH.THRESHOLD", "FIN.PROFILE", "FIN.BEAD")


class Refused(ValueError):
    """An input the method does not accept (never silently corrected)."""


MAX_M = 10.0  # every dimension is in metres; a value above this is a millimetre slip, refused (never rescaled)


def _metres(name, v):
    if v is not None and v > MAX_M:
        raise Refused(f"{name} = {v}: metres expected (a millimetre value is refused, never rescaled)")
    return v


def _r(v, n=4):
    return None if v is None else round(v + 0.0, n)


def stations(floors):
    """R-T413-1. `floors`: [{floor, doors: [door dict]}] as drawn. Returns the station ids, one per door."""
    out = []
    for f in floors:
        doors = f.get("doors") or []
        if not doors:
            raise Refused(f"{f.get('floor')}: a served floor with no landing door drawn is not a station")
        for i, d in enumerate(doors, 1):
            sid = f"ELV-01-{f['floor']}" + (f"-{i}" if len(doors) > 1 else "")
            if d.get("station_id") and d["station_id"] != sid:
                raise Refused(f"station id {d['station_id']} != {sid}")
            out.append(sid)
    return out


def check_count(claimed_count, floors):
    """R-T413-1 adverse: a count lower than the drawn doors (one per floor where a floor has two) is refused."""
    n = len(stations(floors))
    if claimed_count != n:
        raise Refused(f"claimed {claimed_count} stations, the plans draw {n} landing doors")
    return n


def band_width(side, *, drawn_m=None, available_m=None, default_source=None, default_m=None):
    """R-T413-3: one surround band width with its status. `available_m` is the landing wall face beside that jamb
    (top band: None = not limited on the plan)."""
    for n, v in (("drawn_m", drawn_m), ("available_m", available_m), ("default_m", default_m)):
        _metres(f"{side} {n}", v)
    if drawn_m is not None:
        if drawn_m <= 0:
            raise Refused(f"{side}: a drawn surround width must be positive")
        if available_m is not None and drawn_m > available_m + 1e-9:
            raise Refused(f"{side}: drawn width {drawn_m} exceeds the face available {available_m}")
        if default_m is not None and abs(default_m - drawn_m) > 1e-9:
            raise Refused(f"{side}: a default never replaces the drawn width")
        return {"side": side, "width_m": drawn_m, "status": DRAWING, "source": "drawn / printed", "bound": None}
    if default_m is None:
        return {"side": side, "width_m": None, "status": HELD, "source": "nothing printed, no default applied",
                "bound": [0.0, available_m]}
    if not default_source or "UP-ELEV-002" not in default_source:
        raise Refused(f"{side}: a surround width defaulted without its owner source is refused")
    if abs(default_m - SURROUND_DEFAULT_M) > 1e-9:
        raise Refused(f"{side}: the owner default is {SURROUND_DEFAULT_M} m, not {default_m}")
    if available_m is not None and default_m > available_m + 1e-9:
        return {"side": side, "width_m": None, "status": HELD,
                "source": f"INFEASIBLE_DEFAULT: {default_m} m > {available_m} m of landing face beside the jamb",
                "bound": [0.0, available_m]}
    return {"side": side, "width_m": default_m, "status": OWNER, "source": default_source, "bound": None}


def surround_area(w, h, left, top, right):
    """UP-ELEV-003 union of the three bands (corners once): h (L + R) + T (W + L + R)."""
    if None in (w, h, left, top, right):
        return None
    if min(w, h, left, top, right) <= 0:
        raise Refused("surround dimensions must be positive")
    return h * (left + right) + top * (w + left + right)


def surround(station_id, *, clear_width_m, clear_height_m=None, storey_height_m=None, left=None, top=None,
             right=None):
    """R-T413-2 / -4. left / top / right are band_width() records."""
    if clear_width_m is None or clear_width_m <= 0:
        raise Refused(f"{station_id}: the clear width must be drawn (R-T413-2)")
    for n, v in (("clear_width_m", clear_width_m), ("clear_height_m", clear_height_m),
                 ("storey_height_m", storey_height_m)):
        _metres(f"{station_id} {n}", v)
    L, T, R = (b["width_m"] for b in (left, top, right))
    rec = {"station_id": station_id, "object": "B6-06 ELEVATOR_DOOR_SURROUND", "clear_width_m": clear_width_m,
           "clear_height_m": clear_height_m, "bands": [left, top, right]}
    statuses = {b["status"] for b in (left, top, right)}
    if clear_height_m is not None and None not in (L, T, R):
        a = surround_area(clear_width_m, clear_height_m, L, T, R)
        rec.update(area_m2=_r(a), edge_lm=_r(2 * clear_height_m + 2 * T + clear_width_m + L + R, 3),
                   status=(OWNER if OWNER in statuses else DRAWING), bound_m2=None, missing=[])
        return rec
    missing = []
    if clear_height_m is None:
        missing.append("door clear height (head level): not printed")
    for b in (left, top, right):
        if b["width_m"] is None:
            missing.append(f"{b['side']} band width: {b['source']}")
    lo_L = L if L is not None else 0.0
    lo_R = R if R is not None else 0.0
    lo_T = T if T is not None else 0.0
    lo = (lo_T * (clear_width_m + lo_L + lo_R)) if T is not None else 0.0
    hi = None
    if storey_height_m is not None:
        hi_L = L if L is not None else (left["bound"][1] if left["bound"] and left["bound"][1] is not None else None)
        hi_R = R if R is not None else (right["bound"][1] if right["bound"] and right["bound"][1] is not None
                                        else None)
        hi_T = T if T is not None else None
        h_max = clear_height_m if clear_height_m is not None else (
            storey_height_m - hi_T if hi_T is not None else None)
        if None not in (hi_L, hi_R, hi_T, h_max):
            if h_max <= 0:
                raise Refused(f"{station_id}: storey height leaves no door height")
            hi = h_max * (hi_L + hi_R) + hi_T * (clear_width_m + hi_L + hi_R)
    rec.update(area_m2=None, edge_lm=None, status=HELD, bound_m2=[_r(lo), _r(hi)], missing=missing,
               formula=f"A(h) = h x ({'L' if L is None else L} + {'R' if R is None else R}) + "
                       f"{'T' if T is None else T} x ({clear_width_m} + {'L' if L is None else L} + "
                       f"{'R' if R is None else R})")
    return rec


def threshold(station_id, *, clear_width_m, depth_m=None, depth_source=None, default_depth_m=None,
              default_width_m=None, wall_band_m=None, landing_face_overlap_m2=None):
    """R-T413-5 / -6."""
    if clear_width_m is None:
        raise Refused(f"{station_id}: the threshold width is the drawn clear width; none drawn")
    for n, v in (("clear_width_m", clear_width_m), ("depth_m", depth_m), ("wall_band_m", wall_band_m)):
        _metres(f"{station_id} {n}", v)
    if default_width_m is not None and abs(default_width_m - clear_width_m) > 1e-9:
        raise Refused(f"{station_id}: the 1.10 m fallback width never replaces a drawn clear width")
    if depth_m is not None:
        status, src = DRAWING, depth_source or "printed"
    elif default_depth_m is not None:
        if not depth_source or "UP-ELEV-005" not in depth_source:
            raise Refused(f"{station_id}: a threshold depth defaulted without its owner source is refused")
        if abs(default_depth_m - THRESHOLD_DEFAULT_DEPTH_M) > 1e-9:
            raise Refused(f"{station_id}: the owner fallback depth is {THRESHOLD_DEFAULT_DEPTH_M} m")
        depth_m, status, src = default_depth_m, OWNER, depth_source
    else:
        return {"station_id": station_id, "object": "B6-07 ELEVATOR_THRESHOLD_MARBLE", "width_m": clear_width_m,
                "depth_m": None, "area_m2": None, "front_edge_lm": _r(clear_width_m, 3), "status": HELD,
                "missing": ["threshold depth"], "floor_overlap_bound_m2": None}
    area = clear_width_m * depth_m
    if landing_face_overlap_m2 is not None:
        ov = [landing_face_overlap_m2, landing_face_overlap_m2]
    elif wall_band_m is not None:
        ov = [clear_width_m * max(depth_m - wall_band_m, 0.0), area]
    else:
        ov = [0.0, area]
    return {"station_id": station_id, "object": "B6-07 ELEVATOR_THRESHOLD_MARBLE", "width_m": clear_width_m,
            "depth_m": depth_m, "area_m2": _r(area), "front_edge_lm": _r(clear_width_m, 3), "status": status,
            "source": src, "missing": [],
            "floor_overlap_bound_m2": [_r(ov[0]), _r(ov[1])],
            "floor_overlap_status": DRAWING if ov[0] == ov[1] else HELD}


def bind(station_id, line_codes):
    """R-T413-7: the item codes a station's marble may be bound to; a door-threshold / profile / bead code is refused."""
    for c in line_codes:
        if any(c.startswith(f) for f in FORBIDDEN_LINE_CODES):
            raise Refused(f"{station_id}: lift marble bound to {c} is a double count (R-T413-7)")
    return list(line_codes)


def totals(records, key):
    """Sum of a family: a value only when every station is valued; otherwise the bound, never 0 for a held one."""
    vals = [r.get(key) for r in records]
    if all(v is not None for v in vals):
        return {"value": _r(sum(vals)), "bound": None}
    b = [r.get("bound_m2") or r.get("floor_overlap_bound_m2") or [None, None] for r in records]
    lo = [v if v is not None else bb[0] for v, bb in zip(vals, b)]
    hi = [v if v is not None else bb[1] for v, bb in zip(vals, b)]
    return {"value": None,
            "bound": [_r(sum(lo)) if None not in lo else None, _r(sum(hi)) if None not in hi else None]}
