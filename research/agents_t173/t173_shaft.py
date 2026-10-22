"""T-173: stair-shaft wall faces from the actual exposed geometry (any villa; research module, not wired).

Each wall face of a shaft is measured in its own plane: u = horizontal position along the face (m), z = level (m).
The face region G is the union of rectangles the drawings establish (floor to soffit, piece by piece); everything
physically built against the face is subtracted ONCE, as the geometric union of its contact profile:

- landing / floor-slab bands: [finished level - build-up - slab thickness, finished level] over the contact length;
- flights: the side profile of the steps plus the waist, bounded by the soffit line (ERS s.2.1: build before deduct);
- held contacts (an element whose geometry the drawings do not fix): a bounded zone, subtracted only in the low case;
- openings: PRINTED / ASSUMED (owner fallback) bands, subtracted where they do not overlap a contact; HELD openings as
  a bounded band (low case only).

Nothing here assumes a wall continues through a floor: continuity comes only from the face region the caller builds
(from the sections / plans), and any slab that crosses the shaft is a contact band. Missing data never becomes 0:
a held item is a range, and `require` refuses a spec with an unknown value.

Statuses (WORKFLOW_CONTROLS s.5) are attached by the caller; this module returns areas and the pieces they come from.
"""

from __future__ import annotations

import math
from typing import Iterable

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

UNITS = {"m": 1.0, "cm": 0.01, "mm": 0.001}
EPS = 1e-9


class ShaftInputError(ValueError):
    """A required dimension is missing or a unit is unknown (never silently 0)."""


def to_m(value, units: str = "m") -> float:
    if units not in UNITS:
        raise ShaftInputError(f"unknown unit {units!r}")
    if value is None:
        raise ShaftInputError("missing value (held, never 0)")
    return float(value) * UNITS[units]


def require(d: dict, *keys):
    for k in keys:
        if k not in d or d[k] is None:
            raise ShaftInputError(f"missing {k!r} in {d.get('id', '?')} (held, never 0)")


# ---------------------------------------------------------------- element profiles in the wall plane

def rect(u0, u1, z0, z1) -> Polygon:
    return box(min(u0, u1), min(z0, z1), max(u0, u1), max(z0, z1))


def band(u0, u1, level, thickness, buildup=0.0) -> Polygon:
    """Landing or slab edge against the face: finished level on top, structural soffit below (level - b - t)."""
    return rect(u0, u1, level - buildup - thickness, level)


def flight_profile(u_first: float, direction: int, z0: float, risers: int, riser: float, going: float,
                   waist: float, t_start: float, t_end: float, extend_end: bool = True) -> Polygon:
    """Side profile of a straight flight against a wall.

    s = 0 at the first riser line, the flight rises in +s; u = u_first + direction * s.
    risers N, N - 1 goings; the N-th riser arrives at the upper landing / floor (z_top = z0 + N r) at s = (N-1) g.
    Waist t perpendicular to the pitch, measured from the line through the step roots (Q-47 A convention, as T-184).
    The start is bounded below by the lower support's soffit (z0 - t_start; 0 for a flight on grade: the face starts
    at the floor) and the soffit line runs on until it meets the upper support's soffit (z_top - t_end).
    extend_end=False stops the profile at the last riser line: used when the upper support's soffit is not drawn
    (the junction then belongs to a HELD zone of the caller, never to an invented soffit).
    """
    if direction not in (1, -1):
        raise ShaftInputError("direction must be +1 or -1")
    for name, v in (("risers", risers), ("riser", riser), ("going", going), ("waist", waist)):
        if v is None or v <= 0:
            raise ShaftInputError(f"flight {name} missing or not positive (held, never 0)")
    n, r, g = int(risers), float(riser), float(going)
    tv = waist * math.hypot(g, r) / g          # vertical depth of the waist
    s_last = (n - 1) * g
    z_top = z0 + n * r

    def soffit(s):
        return z0 + s * r / g - tv

    s_end = max(s_last, (z_top - t_end - z0 + tv) * g / r) if extend_end else s_last
    pts = [(0.0, z0)]
    for k in range(n):
        pts.append((k * g, z0 + (k + 1) * r))
        if k < n - 1:
            pts.append(((k + 1) * g, z0 + (k + 1) * r))
    pts.append((s_end, z_top))
    pts.append((s_end, min(z_top, soffit(s_end))))
    pts.append((-1.0, soffit(-1.0)))
    pts.append((-1.0, z0))
    poly = Polygon(pts).buffer(0)
    poly = poly.intersection(box(0.0, z0 - t_start, s_end, z_top))
    # map s -> u
    from shapely import affinity
    if direction == 1:
        return affinity.translate(poly, xoff=u_first)
    return affinity.translate(affinity.scale(poly, xfact=-1.0, yfact=1.0, origin=(0, 0)), xoff=u_first)


def flight_soffit_at_last_riser(z0, risers, riser, going, waist):
    """Lowest level a following element's soffit can start from (the flight soffit line at its last riser)."""
    return z0 + (risers - 1) * riser - waist * math.hypot(going, riser) / going


def flight_unit_profile_area(risers, riser, going, waist):
    """Hand check: steps triangles + waist parallelogram per unit width (= T-184 steps m3 + waist m3 over width)."""
    n, r, g = risers, riser, going
    return n * 0.5 * r * g + waist * math.hypot((n - 1) * g, (n - 1) * r)


# ---------------------------------------------------------------- one face

def _poly(item) -> Polygon:
    if "rect" in item:
        return rect(*item["rect"])
    if "band" in item:
        b = item["band"]
        return band(b["u"][0], b["u"][1], b["level"], b["t"], b.get("buildup", 0.0))
    if "flight" in item:
        return flight_profile(**item["flight"])
    if "poly" in item:
        return Polygon(item["poly"])
    raise ShaftInputError(f"element {item.get('id')} has no geometry")


def _union(items: Iterable[dict]):
    polys = [_poly(i) for i in items]
    return unary_union(polys) if polys else Polygon()


def measure_face(face: dict, storeys: list[float] | None = None) -> dict:
    """Areas of one wall face. face = {id, region: [[u0,u1,z0,z1], ...], contacts: [...], openings: [...],
    returns: [{u, depth}]}; contacts / openings carry 'status' KNOWN / HELD (contacts) or PRINTED / ASSUMED / HELD
    (openings). Returns the area of each piece, net_hi (held items not deducted) and net_lo (held items deducted)."""
    require(face, "id", "region")
    G = unary_union([rect(*r) for r in face["region"]])
    known_c = [c for c in face.get("contacts", []) if c.get("status", "KNOWN") == "KNOWN"]
    held_c = [c for c in face.get("contacts", []) if c.get("status") == "HELD"]
    known_o = [o for o in face.get("openings", []) if o.get("status") in ("PRINTED", "ASSUMED")]
    held_o = [o for o in face.get("openings", []) if o.get("status") == "HELD"]
    for o in face.get("openings", []):
        if o.get("status") not in ("PRINTED", "ASSUMED", "HELD"):
            raise ShaftInputError(f"opening {o.get('id')} has no status")

    K = _union(known_c).intersection(G)
    O = _union(known_o).intersection(G.difference(K))
    rest = G.difference(K).difference(O)
    HC = _union(held_c).intersection(rest)
    HO = _union(held_o).intersection(rest.difference(HC))
    net_hi_geom = rest
    net_lo_geom = rest.difference(HC).difference(HO)

    # pier returns: depth x the exposed vertical length of the face at that u
    ret_hi = ret_lo = 0.0
    zmin, zmax = G.bounds[1] - 1, G.bounds[3] + 1
    for rt in face.get("returns", []):
        line = LineString([(rt["u"], zmin), (rt["u"], zmax)])
        ret_hi += rt["depth"] * net_hi_geom.intersection(line).length
        ret_lo += rt["depth"] * net_lo_geom.intersection(line).length

    out = {
        "id": face["id"],
        "gross": G.area,
        "contacts_known": K.area,
        "openings_known": O.area,
        "contacts_held_max": HC.area,
        "openings_held_max": HO.area,
        "returns_hi": ret_hi,
        "returns_lo": ret_lo,
        "net_hi": net_hi_geom.area + ret_hi,
        "net_lo": net_lo_geom.area + ret_lo,
        "pieces": {
            "contacts": {c["id"]: _poly(c).intersection(G).area for c in face.get("contacts", [])},
            "openings": {o["id"]: _poly(o).intersection(G).area for o in face.get("openings", [])},
        },
    }
    if storeys:
        marks = [-1e9] + list(storeys) + [1e9]
        split = []
        for lo, hi in zip(marks, marks[1:]):
            clip = box(-1e9, lo, 1e9, hi)
            split.append({
                "z_from": lo if lo > -1e8 else None, "z_to": hi if hi < 1e8 else None,
                "gross": G.intersection(clip).area,
                "net_hi": net_hi_geom.intersection(clip).area,
                "net_lo": net_lo_geom.intersection(clip).area,
            })
        out["storeys"] = split
    return out


def measure_shaft(faces: list[dict], storeys: list[float] | None = None) -> dict:
    rows = [measure_face(f, storeys) for f in faces]
    keys = ("gross", "contacts_known", "openings_known", "contacts_held_max", "openings_held_max",
            "returns_hi", "returns_lo", "net_hi", "net_lo")
    total = {k: sum(r[k] for r in rows) for k in keys}
    if storeys:
        total["storeys"] = [
            {k: sum(r["storeys"][i][k] for r in rows) for k in ("gross", "net_hi", "net_lo")}
            | {"z_from": rows[0]["storeys"][i]["z_from"], "z_to": rows[0]["storeys"][i]["z_to"]}
            for i in range(len(storeys) + 1)
        ]
    return {"faces": rows, "total": total}


# ---------------------------------------------------------------- the two methods side by side

def owner_manual_gross(lengths_by_storey: dict, owner_height_by_storey: dict) -> dict:
    """OWNER MANUAL METHOD as written (Q-43 G1): face length per storey x the owner's room height of that storey.
    Shown beside the drawing-derived value; it is the owner's room formula, not a measurement of a shaft."""
    per = {}
    for st, length in lengths_by_storey.items():
        if st not in owner_height_by_storey or owner_height_by_storey[st] is None:
            raise ShaftInputError(f"owner height for {st} missing (held, never 0)")
        per[st] = length * owner_height_by_storey[st]
    return {"per_storey": per, "total": sum(per.values())}


def storey_interval_gross(lengths_by_storey: dict, interval_by_storey: dict) -> dict:
    """The 'storey interval' shortcut (T-128 option B): length x floor-to-floor, no element deducted."""
    per = {st: lengths_by_storey[st] * interval_by_storey[st] for st in lengths_by_storey}
    return {"per_storey": per, "total": sum(per.values())}


def continuity_check(slabs_across: list[dict], z_from: float, z_to: float) -> list[dict]:
    """A wall face is continuous between z_from and z_to only if no slab spans the whole shaft section between
    them. Returns the crossing slabs (each makes the face two faces plus a band); [] means continuous."""
    return [s for s in slabs_across if z_from < s["level"] < z_to and s.get("spans_full_section")]
