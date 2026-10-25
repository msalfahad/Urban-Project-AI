"""T-281 STAIR_SOFFIT_V1: the underside of every flight and landing, measured on the stair's own geometry.

Research module, NOT wired into any engine route or released line. Pure rules, standard library only.

Physical element (ERS s.2.1): the soffit of a stair is the underside of its waist (an inclined plane parallel to the
pitch line, the waist thickness t below the line through the inner step corners) and of its landing plates (flat, the
plate thickness below the landing level). It is a finish surface of the STAIR, seen from the space below it; it is
never a decor ceiling of that space (R-STAIR-SOFFIT-1, proposed).

Two methods side by side (ERS s.2.2), both on ONE stair geometry (OWNER_RULE_STAIRS_2026-10-24 s.1 'BOQ'):

* OWNER-REGION (method "O"): no owner rule measures a stair soffit, so this is the owner's concrete region carried
  over (Q-47 A: the waist runs between the first and the last riser line; Q-62 A cond: an arrival wedge inside a plate
  or beam belongs to that member; R-STAIR-LAND-1). Flight soffit = lane between the first riser line (or the support
  beam's face) and the last riser line (or the head beam's face), sloped; landing soffit = landing polygon, flat.
  True area needs only the riser and the going (sec theta = hypot(g, r) / g); it does not need the waist.
* DRAWING-DERIVED (method "D"): the physical soffit planes. The waist soffit meets a landing plate's soffit where
  z0 + (r / g) s - t sec(theta) = plate soffit, i.e. at the foot  s = (g / r)(t sec - tL)  past the first riser line,
  at the head  s = g + (g / r)(t sec - tL)  past the last riser line; on a ground slab it rises out of the slab at
  s = (g / r) t sec (the strip before it bears on the slab: no soffit); at a beam it stops on the beam face (checked
  above the beam bottom, else HELD). Needs the riser, the going and the waist thickness.

The plan area of every row is a partition: method O and method D move strips between rows (flat <-> sloped, soffit
<-> slab-borne), never create or lose plan area; `partition_check` refuses a residual.

Missing never becomes 0 (MISSION.md): a riser that is not printed (or not owner-approved), an unprinted waist, a winder
or curved flight whose soffit is not drawn (S-9, C-ST-3) give HELD (value None), never a convention value. A
convention input is refused outright.
"""

from __future__ import annotations

import math

METHOD = "STAIR_SOFFIT_V1"
UNITS = {"m": 1.0, "cm": 0.01, "mm": 0.001}
RISER_OK = ("PRINTED", "ASSUMED — OWNER-APPROVED")
REFUSED_SOURCES = ("CONVENTION", "DEFAULT", "TYPICAL", "ASSUMED")
EPS = 1e-9


class SoffitError(ValueError):
    """The record cannot be measured as given (refused input, overlap, residual, unit)."""


# ----------------------------------------------------------------------------------------------------------- units
def to_m(v, unit):
    if v is None:
        return None
    if unit not in UNITS:
        raise SoffitError(f"unknown unit {unit!r}")
    return float(v) * UNITS[unit]


# ------------------------------------------------------------------------------- rectangles in a local (s, u) frame
# A rectangle is (s0, s1, u0, u1): s along the flight / landing, u across it, metres from the piece's own edge lines.
def _clip(r, b):
    s0, s1 = max(r[0], b[0]), min(r[1], b[1])
    u0, u1 = max(r[2], b[2]), min(r[3], b[3])
    return (s0, s1, u0, u1) if s1 - s0 > EPS and u1 - u0 > EPS else None


def union_area(rects):
    """Exact area of a union of axis-aligned rectangles (coordinate compression)."""
    rects = [r for r in rects if r is not None]
    if not rects:
        return 0.0
    xs = sorted({v for r in rects for v in (r[0], r[1])})
    a = 0.0
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        iv = sorted((r[2], r[3]) for r in rects if r[0] <= x0 + EPS and r[1] >= x1 - EPS)
        cov, cur0, cur1 = 0.0, None, None
        for u0, u1 in iv:
            if cur1 is None or u0 > cur1:
                if cur1 is not None:
                    cov += cur1 - cur0
                cur0, cur1 = u0, u1
            else:
                cur1 = max(cur1, u1)
        if cur1 is not None:
            cov += cur1 - cur0
        a += cov * (x1 - x0)
    return a


def region_area(base, minus=(), band=None):
    """Area of base (optionally clipped to band) less the union of `minus`."""
    b = base if band is None else _clip(base, band)
    if b is None:
        return 0.0
    full = (b[1] - b[0]) * (b[3] - b[2])
    return full - union_area([_clip(m, b) for m in minus])


def partition(base, subs):
    """Split base into the ordered sub-rectangles (first claim wins) and the remainder; refuses a sub outside base."""
    out, taken = [], []
    for name, cls, r in subs:
        if _clip(r, base) is None or abs(region_area(r) - region_area(_clip(r, base))) > 1e-7:
            raise SoffitError(f"sub-rectangle {name} lies outside its piece")
        a = region_area(r, taken)
        out.append((name, cls, r, a))
        taken.append(r)
    return out, region_area(base, taken), taken


# ------------------------------------------------------------------------------------------------------- the pitch
def pitch(r, g, r_source):
    """sec(theta) of a straight flight; HELD (None) when the riser is not printed / owner-approved."""
    if r_source is not None and any(r_source.upper().startswith(x) for x in REFUSED_SOURCES) and \
            r_source not in RISER_OK:
        raise SoffitError(f"riser source {r_source!r} refused: a convention riser is never measured")
    if r is None or g is None or r_source not in RISER_OK:
        return None
    if r <= 0 or g <= 0:
        raise SoffitError("riser and going must be positive")
    return math.hypot(g, r) / g


def _waist_src_ok(t, t_source):
    if t_source is not None and any(t_source.upper().startswith(x) for x in REFUSED_SOURCES):
        raise SoffitError(f"waist source {t_source!r} refused: a convention waist is never measured")
    return t is not None and t_source is not None


# ---------------------------------------------------------------------------------------------- straight flights
def flight_limits(f):
    """Method O and method D limits (s) of the waist soffit along the flight, with the kinks into the neighbours.

    f: n (riser lines, at g from s = 0), r, g, w (lane), t, r_source, t_source,
       foot: {"type": plate|ground|beam_face|continues, "t": plate thickness, "offset": face past the first riser line,
              "depth": beam depth below the lower level}
       head: {"type": plate|beam_face|held_junction, "t", "offset_before_last", "depth", "room": landing depth along s}
    """
    n, g = f["n"], f["g"]
    last = (n - 1) * g
    foot, head = f["foot"], f["head"]
    sec = pitch(f.get("r"), g, f.get("r_source"))
    t_ok = _waist_src_ok(f.get("t"), f.get("t_source"))
    # method O: riser line to riser line, or to the beam face
    o0 = foot.get("offset", 0.0) if foot["type"] == "beam_face" else 0.0
    o1 = last - head["offset_before_last"] if head["type"] == "beam_face" else last
    res = {"sec": sec, "O": (o0, o1), "D": None, "D_held": None, "kink_foot": 0.0, "kink_head": 0.0,
           "slab_borne": 0.0}
    if sec is None:
        res["D_held"] = "riser not printed / not owner-approved: no slope, no kink (HELD, never a convention riser)"
        return res
    if not t_ok:
        res["D_held"] = "waist thickness not printed: the soffit planes cannot be placed (HELD)"
        return res
    r, t = f["r"], f["t"]
    ts = t * sec
    d0, d1, held = o0, o1, None
    if foot["type"] == "plate":
        d0 = (g / r) * (ts - foot["t"])
        if d0 < -EPS:
            held = "foot plate thicker than the waist: the kink lies inside the landing (not modelled, HELD)"
        res["kink_foot"] = max(d0, 0.0)
    elif foot["type"] == "ground":
        d0 = (g / r) * ts
        res["slab_borne"] = d0
    elif foot["type"] == "beam_face":
        z = (r / g) * o0 - ts
        if z < -foot["depth"] - EPS:
            held = "the waist soffit passes below the foot beam's bottom: junction not drawn (HELD)"
    elif foot["type"] == "continues":
        d0 = 0.0
    else:
        raise SoffitError(f"unknown foot type {foot['type']!r}")
    if head["type"] == "plate":
        d1 = last + g + (g / r) * (ts - head["t"])
        res["kink_head"] = d1 - last
        if head.get("room") is not None and res["kink_head"] > head["room"] + EPS:
            held = "the head kink runs past the far edge of the plate: geometry not drawn (HELD)"
    elif head["type"] == "beam_face":
        x = o1                                           # face position; root line there: z0 + (r / g) x
        z_soffit_below_top = (n * r) - (r / g) * x + ts  # depth of the soffit under the arrival level at the face
        if z_soffit_below_top > head["depth"] + EPS:
            held = "the waist soffit passes below the head beam's bottom: junction not drawn (HELD)"
    elif head["type"] == "held_junction":
        d1 = o1
    else:
        raise SoffitError(f"unknown head type {head['type']!r}")
    if held:
        res["D_held"] = held
    else:
        res["D"] = (d0, d1)
    return res


def flight_rows(f, subs=()):
    """Rows of one straight flight: the waist soffit and the named sub-pieces of its lane (O and D)."""
    lim = flight_limits(f)
    w = f["w"]
    base = (lim["O"][0], lim["O"][1], 0.0, w)
    parts, waist_plan, taken = partition(base, subs)
    sec = lim["sec"]
    rows = []
    o_true = None if sec is None else waist_plan * sec
    row = {"id": f["id"], "piece": "waist soffit", "cls": "STAIR_SOFFIT", "plan_O": waist_plan, "true_O": o_true,
           "status": f["status"] if sec is not None else "HELD", "below": f["below"], "src": f["src"]}
    if lim["D"] is None:
        row.update(plan_D=None, true_D=None, held_D=lim["D_held"])
    else:
        d0, d1 = lim["D"]
        o0, o1 = lim["O"]
        sloped_band = (max(d0, o0), min(d1, o1), -1e9, 1e9)
        flat_band = (o0, max(d0, o0), -1e9, 1e9) if f["foot"]["type"] == "plate" else None
        sloped_in = region_area(base, taken, sloped_band)
        flat_in = region_area(base, taken, flat_band) if flat_band else 0.0
        borne = region_area(base, taken, (o0, max(d0, o0), -1e9, 1e9)) if f["foot"]["type"] == "ground" else 0.0
        row.update(plan_D=sloped_in + flat_in, true_D=sloped_in * sec + flat_in, held_D=None,
                   slab_borne_plan_D=borne, head_kink_m=lim["kink_head"], foot_kink_m=lim["kink_foot"],
                   ground_kink_m=lim["slab_borne"])
    rows.append(row)
    for name, cls, r, a in parts:
        rows.append({"id": f"{f['id']}/{name}", "piece": name, "cls": cls, "plan_O": a, "true_O": None,
                     "plan_D": a, "true_D": None, "status": "HELD" if cls != "NO_SOFFIT" else "DRAWING-CONFIRMED",
                     "below": f["below"], "src": f["src"]})
    if lim["D"] is not None and f["foot"]["type"] == "ground":
        rows.append({"id": f"{f['id']}/slab-borne foot", "piece": "slab-borne foot strip (waist on the slab: no soffit)",
                     "cls": "NO_SOFFIT", "plan_O": 0.0, "true_O": None, "plan_D": row["slab_borne_plan_D"],
                     "true_D": 0.0, "status": f["status"], "below": "ground slab", "src": f["src"]})
    return rows, lim


def landing_rows(L, kinks=()):
    """Rows of one landing plate: flat soffit (O); in method D the arriving flights' head-kink strips leave it.

    L: id, length (s), width (u), subs [(name, cls, rect)], status, below, src. kinks: [{"rect": (s0, s1, u0, u1) in
    L's frame, "held": None or why}] from `kink_rows`."""
    base = (0.0, L["length"], 0.0, L["width"])
    parts, flat_plan, taken = partition(base, L.get("subs", ()))
    row = {"id": L["id"], "piece": "landing soffit", "cls": "STAIR_SOFFIT", "plan_O": flat_plan, "true_O": flat_plan,
           "status": L["status"], "below": L["below"], "src": L["src"]}
    held = [k["held"] for k in kinks if k.get("held")]
    if held:
        row.update(plan_D=None, true_D=None, held_D="; ".join(held))
    else:
        rects = [_clip(k["rect"], base) for k in kinks]
        if union_area(rects) < sum(region_area(r) for r in rects if r) - 1e-7:
            raise SoffitError(f"two flights claim the same strip of landing {L['id']}")
        kink_plan = sum(region_area(r, taken) for r in rects if r)
        row.update(plan_D=flat_plan - kink_plan, true_D=flat_plan - kink_plan, held_D=None)
    rows = [row]
    for name, cls, r, a in parts:
        rows.append({"id": f"{L['id']}/{name}", "piece": name, "cls": cls, "plan_O": a, "true_O": None,
                     "plan_D": a, "true_D": None, "status": "HELD" if cls != "NO_SOFFIT" else "DRAWING-CONFIRMED",
                     "below": L["below"], "src": L["src"]})
    return rows


def kink_rows(f, lim, plate_length, plate_width, subs=(), u_offset=0.0, into="landing"):
    """The head-kink strip of flight f inside the plate it arrives into (method D: sloped, part of the flight's soffit).

    The strip is (0, kink) x (u_offset, u_offset + w) in the plate's own frame; the plate's sub-pieces stay theirs."""
    if lim["D"] is None:
        return [], {"rect": None, "held": lim["D_held"]}
    k = lim["kink_head"]
    rect = (0.0, k, u_offset, u_offset + f["w"])
    if k > plate_length + EPS or u_offset + f["w"] > plate_width + EPS:
        return [], {"rect": None, "held": "head kink outside the plate it arrives into (HELD)"}
    a = region_area(rect, [s[2] for s in subs])
    row = {"id": f"{f['id']}/head kink", "piece": f"waist soffit under the {into} edge (head kink {k:.6f} m)",
           "cls": "STAIR_SOFFIT", "plan_O": 0.0, "true_O": 0.0, "plan_D": a, "true_D": a * lim["sec"],
           "status": f["status"], "below": f["below"], "src": f["src"]}
    return [row], {"rect": rect, "held": None}


# ------------------------------------------------------------------------------------------ curved flights, winders
def held_surface(id_, piece, plan, below, src, why, status="DRAWING-CONFIRMED"):
    """A curved flight or a winder turn: plan area from the drawn outline, true area HELD (S-9, C-ST-3)."""
    if not why:
        raise SoffitError("a held true area needs its reason")
    return {"id": id_, "piece": piece, "cls": "STAIR_SOFFIT", "plan_O": plan, "true_O": None, "plan_D": plan,
            "true_D": None, "held_D": why, "status": status, "true_status": "HELD", "below": below, "src": src}


def winder_true_area(*, drawn_polygons=None, soffit_drawn=False, **_):
    """S-9: never a generated winder or a walking-line offset; without a drawn soffit the true area is HELD."""
    if not soffit_drawn or not drawn_polygons:
        return None
    raise SoffitError("a drawn warped winder soffit is not implemented in STAIR_SOFFIT_V1")


# --------------------------------------------------------------------------------------------- checks and totals
def partition_check(face_m2, parts, tol=5e-5, residual_named=None):
    """A zone face (the slab-plan stair zone) = the sum of its named parts; a residual must be named, never absorbed."""
    s = sum(parts.values())
    res = face_m2 - s
    if abs(res) > tol and not residual_named:
        raise SoffitError(f"zone {face_m2:.6f} vs parts {s:.6f}: residual {res:+.6f} m2 not named")
    return res


def totals(rows):
    """Sums by evidence; HELD true areas are counted, never as 0."""
    t = {"plan_O": 0.0, "plan_D": 0.0, "true_O_measured": 0.0, "true_D_measured": 0.0, "true_O_held_rows": 0,
         "true_D_held_rows": 0, "held_plan_m2": 0.0}
    for r in rows:
        if r["cls"] != "STAIR_SOFFIT":
            continue
        t["plan_O"] += r["plan_O"] or 0.0
        if r.get("plan_D") is not None:
            t["plan_D"] += r["plan_D"]
        if r["true_O"] is None:
            t["true_O_held_rows"] += 1
            t["held_plan_m2"] += r["plan_O"] or 0.0
        else:
            t["true_O_measured"] += r["true_O"]
        if r.get("true_D") is None:
            t["true_D_held_rows"] += 1
        else:
            t["true_D_measured"] += r["true_D"]
    return t


def exclude_from_ceiling(ceiling_m2, stair_plan_under):
    """R-STAIR-SOFFIT-1: a decor ceiling piece loses the plan area under the stair's own soffit pieces, once."""
    if stair_plan_under < -EPS or stair_plan_under > ceiling_m2 + EPS:
        raise SoffitError("stair plan under the ceiling piece is negative or larger than the piece")
    return ceiling_m2 - stair_plan_under
