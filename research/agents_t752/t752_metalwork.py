"""T-752: B13-07 SPECIAL METALWORK census (canopies, pergolas, louvre screens, gates, handrail frames and any other
drawn non-door / non-window / non-rebar item that no other family owns), per floor, each item in its own unit.
Research only: nothing wired, no BOQ line produced.

PHYSICAL ELEMENT. A special-metalwork item is a drawn, fixed, fabricated piece: a canopy or pergola (plan m2 of its
drawn outline, lm of its drawn members, pcs), a louvre screen (face m2 of its drawn panel), a gate (pcs + leaf size),
a handrail frame (lm), a projecting member such as a beam end (pcs, visible projection in m). One physical item is
counted ONCE, by the family that owns it: railings (B7-09 / B7-11 railing runs), shutters, fence gates, doors and
windows are listed here only as EXCLUDED by id with their owner family, never measured a second time.

NO DEFAULTS (MISSION no-assumptions rule).
  * Material: printed or HELD. A render never makes a material (R-RAIL-2).
  * kg: only when a printed SECTION, a measured LENGTH and a MASS PER METRE with a named source (printed on the
    drawing or a cited section table) are all present; anything missing -> kg HELD (value None, never 0) with every
    missing piece named. Never a default kg/m, never a kg from a plan m2.
  * A size read only from a raster sheet (no CAD geometry, no printed dimension) is never scaled: HELD.
  * Geometry in metres. A length above MAX_MEMBER_M or a plan area above MAX_PLAN_M2 is refused as a unit error
    (mm or cm given as m), never silently divided.

Statuses (ENGINEERING_REASONING_STANDARD s.2.6): DRAWING-CONFIRMED = from drawn CAD geometry or a printed figure;
DERIVED = arithmetic on DRAWING-CONFIRMED inputs and a cited table; HELD = needs a fact the drawings do not print;
NOT_DRAWN = the kind was searched on every listed sheet and is not drawn (no quantity, never 0); EXCLUDED = owned by
another family (listed by id). Nothing here is VERIFIED (the Checker re-measures).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

METHOD_ID = "METALWORK_CENSUS_T752_V1"

CANOPY = "CANOPY"
PERGOLA = "PERGOLA"
LOUVRE_SCREEN = "LOUVRE_SCREEN"
GATE = "GATE"
HANDRAIL_FRAME = "HANDRAIL_FRAME"
PROJECTING_MEMBER = "PROJECTING_MEMBER"     # beam ends / outriggers projecting from a facade
KINDS = (CANOPY, PERGOLA, LOUVRE_SCREEN, GATE, HANDRAIL_FRAME, PROJECTING_MEMBER)

DRAWING_CONFIRMED = "DRAWING-CONFIRMED"
DERIVED = "DERIVED"
HELD = "HELD"
NOT_DRAWN = "NOT_DRAWN"
EXCLUDED = "EXCLUDED"

GEOM_CAD = "CAD"            # coordinates of drawn CAD entities (re-derivable by handle)
GEOM_PRINTED = "PRINTED"    # a dimension figure printed on the sheet
GEOM_RASTER = "RASTER"      # seen on a raster sheet only: counted, never scaled
GEOM_SOURCES = (GEOM_CAD, GEOM_PRINTED, GEOM_RASTER)

MAX_MEMBER_M = 60.0         # a single member / run longer than this in a villa is a unit error (mm or cm as m)
MAX_PLAN_M2 = 400.0         # a canopy / pergola outline larger than a villa plot is a unit error
MAX_MASS_PER_M = 500.0      # kg/m above this is not a light-metalwork section (unit error: g/m, kg/mm)


def _area(ring):
    s = 0.0
    for i in range(len(ring)):
        (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % len(ring)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


@dataclass(frozen=True)
class Member:
    """one drawn straight member (metres), with its CAD handle or sheet reference."""
    ref: str
    a: tuple
    b: tuple

    @property
    def length(self):
        return math.hypot(self.b[0] - self.a[0], self.b[1] - self.a[1])


@dataclass
class Item:
    """one special-metalwork item (or a group of identical drawn pieces counted together).

    pcs: drawn count; outline: plan / face ring (m) for an m2 item; members: drawn members for lm; source: how the
    geometry is known (CAD / PRINTED / RASTER); section: the printed section designation or None; mass_per_m:
    (kg/m, source text) or None; material: printed material or None; owner_family: set when another family owns the
    item (then it is EXCLUDED and not measured)."""
    item_id: str
    kind: str
    floor: str
    where: str
    pcs: int | None
    source: str
    evidence: list = field(default_factory=list)
    outline: list | None = None
    members: list = field(default_factory=list)
    section: str | None = None
    mass_per_m: tuple | None = None
    material: str | None = None
    owner_family: str | None = None
    held_extra: list = field(default_factory=list)     # further designer-item causes (embedment, fixing ...)
    note: str = ""


def _check(it):
    if it.kind not in KINDS:
        raise ValueError(f"{it.item_id}: unknown kind {it.kind!r}")
    if it.source not in GEOM_SOURCES:
        raise ValueError(f"{it.item_id}: unknown geometry source {it.source!r}")
    if it.pcs is not None and (not isinstance(it.pcs, int) or it.pcs < 1):
        raise ValueError(f"{it.item_id}: a drawn count is a positive integer (held count is None, never 0)")
    for m in it.members:
        if m.length <= 0:
            raise ValueError(f"{it.item_id}: member {m.ref} has no length")
        if m.length > MAX_MEMBER_M:
            raise ValueError(f"{it.item_id}: member {m.ref} {m.length:.1f} m > {MAX_MEMBER_M} m: units (mm / cm as m?)")
    if it.outline is not None:
        if len(it.outline) < 3:
            raise ValueError(f"{it.item_id}: outline needs 3 points")
        a = _area(it.outline)
        if a <= 0:
            raise ValueError(f"{it.item_id}: outline has no area")
        if a > MAX_PLAN_M2:
            raise ValueError(f"{it.item_id}: outline {a:.1f} m2 > {MAX_PLAN_M2} m2: units (mm / cm as m?)")
    if it.mass_per_m is not None:
        v, src = it.mass_per_m
        if not src or not str(src).strip():
            raise ValueError(f"{it.item_id}: a mass per metre needs its source (printed note or cited table)")
        if not (0 < v <= MAX_MASS_PER_M):
            raise ValueError(f"{it.item_id}: mass per metre {v} kg/m outside 0 .. {MAX_MASS_PER_M}: units?")
    if it.source == GEOM_RASTER and (it.outline is not None or it.members):
        raise ValueError(f"{it.item_id}: a raster-only item carries no measured geometry (never scaled)")


def measure(it):
    """-> the item's quantities with statuses (see the module text)."""
    _check(it)
    if it.owner_family:
        return {"item_id": it.item_id, "kind": it.kind, "floor": it.floor, "where": it.where,
                "status": EXCLUDED, "owner_family": it.owner_family, "evidence": list(it.evidence)}
    geo = DRAWING_CONFIRMED if it.source in (GEOM_CAD, GEOM_PRINTED) else HELD
    q = {"item_id": it.item_id, "kind": it.kind, "floor": it.floor, "where": it.where, "source": it.source,
         "evidence": list(it.evidence), "note": it.note,
         "pcs": {"value": it.pcs, "status": DRAWING_CONFIRMED if it.pcs else HELD}}
    if it.outline is not None:
        q["plan_m2"] = {"value": round(_area(it.outline), 4), "status": geo}
    lm = sum(m.length for m in it.members) if it.members else None
    if lm is not None:
        q["member_lm"] = {"value": round(lm, 4), "status": geo, "refs": [m.ref for m in it.members]}
    elif it.source == GEOM_RASTER:
        q["member_lm"] = {"value": None, "status": HELD,
                          "reason": "seen on a raster sheet only: sizes never scaled"}
    q["material"] = ({"value": it.material, "status": DRAWING_CONFIRMED} if it.material else
                     {"value": None, "status": HELD, "reason": "material not printed (designer item)"})
    missing = []
    if not it.section:
        missing.append("section not printed")
    if lm is None:
        missing.append("member length not measured")
    if it.mass_per_m is None:
        missing.append("mass per metre not printed / no cited table")
    if missing:
        q["kg"] = {"value": None, "status": HELD, "reason": "; ".join(missing)}
    else:
        q["kg"] = {"value": round(lm * it.mass_per_m[0], 3), "status": DERIVED,
                   "basis": f"{lm:.4f} m x {it.mass_per_m[0]} kg/m ({it.section}; {it.mass_per_m[1]})"}
    q["held_causes"] = [c for c in ([q["material"].get("reason")] + [q["kg"].get("reason")] + list(it.held_extra))
                        if c]
    return q


def census(items, *, other_family_ids=(), not_drawn=()):
    """-> {"items", "excluded", "by_floor", "totals", "not_drawn"}.

    other_family_ids: ids that another family already counts (railing runs, shutters, fence gates, doors, windows);
    an item with such an id must carry owner_family (EXCLUDED), or the census refuses it (a double count).
    not_drawn: [{"kind", "searched"}] -> NOT_DRAWN rows, value None (never 0)."""
    ids, rows, excluded = set(), [], []
    owned = set(other_family_ids)
    for it in items:
        if it.item_id in ids:
            raise ValueError(f"{it.item_id}: listed twice")
        ids.add(it.item_id)
        if it.item_id in owned and not it.owner_family:
            raise ValueError(f"{it.item_id}: already counted by another family: list it EXCLUDED with its owner")
        q = measure(it)
        (excluded if q.get("status") == EXCLUDED else rows).append(q)
    by_floor, totals = {}, {}
    for r in rows:
        for bucket in (by_floor.setdefault(r["floor"], {}), totals):
            k = bucket.setdefault(r["kind"], {"items": 0, "pcs": 0, "pcs_held": 0, "plan_m2": 0.0,
                                              "member_lm": 0.0, "member_lm_held": 0, "kg": 0.0, "kg_held": 0})
            k["items"] += 1
            if r["pcs"]["value"]:
                k["pcs"] += r["pcs"]["value"]
            else:
                k["pcs_held"] += 1
            if "plan_m2" in r and r["plan_m2"]["status"] == DRAWING_CONFIRMED:
                k["plan_m2"] = round(k["plan_m2"] + r["plan_m2"]["value"], 4)
            ml = r.get("member_lm")
            if ml and ml["value"] is not None:
                k["member_lm"] = round(k["member_lm"] + ml["value"], 4)
            elif ml:
                k["member_lm_held"] += 1
            if r["kg"]["value"] is not None:
                k["kg"] = round(k["kg"] + r["kg"]["value"], 3)
            else:
                k["kg_held"] += 1
    nd = []
    for x in not_drawn:
        if x.get("kind") not in KINDS:
            raise ValueError(f"not-drawn row with unknown kind {x.get('kind')!r}")
        if not x.get("searched"):
            raise ValueError(f"NOT_DRAWN {x['kind']}: list the sheets searched (absence needs every sheet read)")
        nd.append({**x, "value": None, "status": NOT_DRAWN})
    return {"method": METHOD_ID, "items": rows, "excluded": excluded, "by_floor": by_floor, "totals": totals,
            "not_drawn": nd}


# ---------------------------------------------------------------------------------- projecting members, plan vs elev
def plan_elevation_agree(plan_offsets, elev_offsets, plan_width, elev_width, tol=0.005):
    """projecting members drawn in plan (stubs along the facade) and on the elevation (end squares): the count, the
    spacing along the facade and the member width must agree within tol (m). Offsets are positions along the facade
    measured from any common or arbitrary origin: only the differences are compared (mirror / origin free).
    -> {"agree": bool, "count": (n_plan, n_elev), "spacing": ([..], [..]), "width": (p, e)}"""
    p, e = sorted(plan_offsets), sorted(elev_offsets)
    sp = [round(b - a, 4) for a, b in zip(p, p[1:])]
    se = [round(b - a, 4) for a, b in zip(e, e[1:])]
    ok = (len(p) == len(e) and all(abs(a - b) <= tol for a, b in zip(sp, se))
          and abs(plan_width - elev_width) <= tol)
    return {"agree": ok, "count": (len(p), len(e)), "spacing": (sp, se),
            "width": (round(plan_width, 4), round(elev_width, 4))}
