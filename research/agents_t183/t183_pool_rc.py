"""T-183 POOL_RC_COMPONENTS (research, NEW and UNWIRED): a swimming pool measured as reinforced concrete, component by
component, for any villa.

Nothing imports this module; no released quantity changes (rollback: delete research/agents_t183 and tests/t183_*).
Stdlib only. All lengths in metres after `to_m`; inputs may be given in mm / cm / m.

Physical element (what is built), from the inside out:
    water  |  RC wall (two curtains)  |  protection screed  |  membrane  |  soil
           |  RC base slab (two mats) |  protection screed  |  membrane  |  plain-concrete blinding  |  soil
The base is one RC slab cast on the blinding build-up; the walls stand on the base. One junction, one owner:
    BASE  = structural footprint (to the outer wall face) x base thickness   (the wall foot below the base top included)
    WALLS = wall plan band (outer outline - water outline) x wall height ABOVE the base top
(the same split as the frozen generic engine/source/pool_qto.wall_base_split; re-implemented here, cross-checked in the
tests). Blinding, screed and membrane are separate lines and never part of the RC volume.

General rules carried by the code (scope: every villa; provenance: T-183, ENGINEERING_REASONING_STANDARD sections 2-4):
    R-POOL-1  A pool shown as a reinforced-concrete shell (a structural pool detail with bars) is RC by component:
              base, walls, steps / benches, rebar, formwork, joints, waterproofing, finishes. It is never blockwork.
    R-POOL-2  Walls are measured all the way round (straight and curved parts); a wall band that does not equal
              outer outline - water outline, or a takeoff with a base but no wall line, is refused (never a silent 0).
    R-POOL-3  Blinding / screed / membrane under the base are their own lines; the RC base thickness is the printed
              RC thickness only. Blinding never enters the RC total; changing the blinding never changes RC m3.
    R-POOL-4  Wall height = height above the base top from the documents (owner Q-26 A for Alsenan: flat floor, inner
              depth 1.15 m); a missing height gives None (HELD), never a convention.
    R-POOL-5  A pump room, balance tank or steps count only when drawn (owner Q-22 A / Q-19 for the pump room).
    R-POOL-6  Wall horizontal bars are distributed over the wall height above the base top; the base's own mats
              occupy the base thickness (no hoop counted inside the base).
    R-POOL-7  Casting method (cast-in-place / shotcrete) only from the documents, else UNKNOWN; formwork faces are
              stated for the documented method only.

CLI:  python3 -I research/agents_t183/t183_pool_rc.py --check            (synthetic non-Alsenan fixture)
      python3 -I research/agents_t183/t183_pool_rc.py ledger INPUT.json  (prints the component ledger as JSON)
"""

from __future__ import annotations

import json
import math
import sys

EPS = 1e-9
UNITS = {"mm": 0.001, "cm": 0.01, "m": 1.0}

HELD = "HELD"
DRAWING_CONFIRMED = "DRAWING-CONFIRMED"
UNKNOWN = "UNKNOWN"
NOT_DRAWN = "NOT_DRAWN"
CALCULATED = "CALCULATED"


class PoolError(ValueError):
    """refused input or a takeoff that breaks R-POOL-1 .. R-POOL-3"""


def to_m(value, unit):
    if value is None:
        return None
    if unit not in UNITS:
        raise PoolError(f"unknown unit {unit!r}")
    v = float(value) * UNITS[unit]
    if not v > 0:
        raise PoolError(f"a dimension must be positive, got {value} {unit}")
    return v


# ---------------------------------------------------------------- plan outlines (exact, analytic)

class Outline:
    """RECT a x b, or D: a rectangle of depth b on a straight back of length 2r, closed by a half circle of radius r
    (the arc is tangent to the two sides). Rotation and mirror do not change any quantity below except the chord
    direction, which is named 'along_back' / 'across_back'."""

    def __init__(self, kind, **dims):
        self.kind = kind
        if kind == "RECT":
            self.a, self.b = dims["a"], dims["b"]
            if not (self.a > 0 and self.b > 0):
                raise PoolError("RECT needs a, b > 0")
        elif kind == "D":
            self.r, self.b = dims["r"], dims["b"]
            if not (self.r > 0 and self.b >= 0):
                raise PoolError("D needs r > 0, b >= 0")
        else:
            raise PoolError(f"unknown outline {kind!r}")

    def area(self):
        if self.kind == "RECT":
            return self.a * self.b
        return 2 * self.r * self.b + math.pi * self.r ** 2 / 2

    def perimeter(self):
        if self.kind == "RECT":
            return 2 * (self.a + self.b)
        return 2 * self.r + 2 * self.b + math.pi * self.r

    def curved_length(self):
        return 0.0 if self.kind == "RECT" else math.pi * self.r

    def inset(self, d):
        """the outline moved inwards by d on every side (wall thickness, cover)"""
        if self.kind == "RECT":
            if not (self.a > 2 * d and self.b > 2 * d):
                raise PoolError("inset larger than the outline")
            return Outline("RECT", a=self.a - 2 * d, b=self.b - 2 * d)
        if not (self.r > d and self.b >= d):
            raise PoolError("inset larger than the outline")
        return Outline("D", r=self.r - d, b=self.b - d)

    def offset_area(self, d):
        """area of the convex outline grown outwards by d (round corners): A + P d + pi d^2"""
        return self.area() + self.perimeter() * d + math.pi * d * d

    def offset_perimeter(self, d):
        return self.perimeter() + 2 * math.pi * d

    # chords (bar lines of one direction across the outline): positions A = midpoints of n strips, B = n + 1 lines
    # edge to edge, C = exact density (rate x area); n = ceil(rate x extent)
    def _chord(self, direction, t):
        if self.kind == "RECT":
            return self.a if direction == "along_back" else self.b
        r, b = self.r, self.b
        if direction == "along_back":           # bar parallel to the straight back, at distance t from the back
            if t <= b + EPS:
                return 2 * r
            u = t - b
            return 2 * math.sqrt(max(r * r - u * u, 0.0))
        u = t - r                               # bar across the back, at offset u from the axis
        return b + math.sqrt(max(r * r - u * u, 0.0))

    def extent(self, direction):
        if self.kind == "RECT":
            return self.b if direction == "along_back" else self.a
        return (self.b + self.r) if direction == "along_back" else 2 * self.r

    def chords(self, direction, rate):
        if direction not in ("along_back", "across_back"):
            raise PoolError("direction is along_back or across_back")
        if not rate > 0:
            raise PoolError("rate must be positive")
        H = self.extent(direction)
        n = int(math.ceil(rate * H - EPS))
        a = [self._chord(direction, (k + 0.5) * H / n) for k in range(n)]
        b = [self._chord(direction, k * H / n) for k in range(n + 1)]
        return {"A": (n, sum(a)), "B": (n + 1, sum(b)), "C": (rate * H, rate * self.area())}


# ---------------------------------------------------------------- concrete components

def concrete_components(outer, wall_t, base_t, wall_h, *, blinding_t=None, screed_t=None, membrane_t=None,
                        blinding_projection=None, element_class="REINFORCED_CONCRETE"):
    """A base / B walls / blinding, screed (separate lines). Returns a dict of lines; a None quantity is HELD."""
    if element_class != "REINFORCED_CONCRETE":
        raise PoolError(f"R-POOL-1: a pool with a structural RC detail is never {element_class}")
    inner = outer.inset(wall_t)
    band = outer.area() - inner.area()
    lines = {
        "C_BASE": {"m3": outer.area() * base_t, "plan_m2": outer.area(), "thickness_m": base_t,
                   "basis": "structural footprint to the outer wall face x RC base thickness (wall foot included)"},
        "D_WALLS": {"m3": None if wall_h is None else band * wall_h, "plan_m2": band, "height_m": wall_h,
                    "status": HELD if wall_h is None else DRAWING_CONFIRMED,
                    "basis": "wall band (outer - water outline) x height above the base top"},
    }
    build_up = (screed_t or 0.0) + (membrane_t or 0.0)
    if blinding_t is not None:
        lb = outer.offset_area(build_up)
        lines["B_BLINDING"] = {
            "m3_lower_bound": lb * blinding_t, "plan_m2_lower_bound": lb, "thickness_m": blinding_t,
            "m3": None if blinding_projection is None else outer.offset_area(build_up + blinding_projection) * blinding_t,
            "status": HELD if blinding_projection is None else DRAWING_CONFIRMED,
            "basis": "plain concrete under the membrane; at least the base footprint grown by screed + membrane; "
                     "its projection beyond that is " + ("not printed (HELD)" if blinding_projection is None
                                                          else f"{blinding_projection} m printed")}
    if screed_t is not None:
        lines["I_SCREED"] = {
            "m3": outer.offset_area(screed_t) * screed_t
                  + outer.offset_perimeter(screed_t / 2) * (base_t + (wall_h or 0.0)) * screed_t
                  if wall_h is not None else None,
            "horizontal_m2": outer.offset_area(screed_t),
            "vertical_m2": None if wall_h is None else outer.perimeter() * (base_t + wall_h),
            "basis": "protection screed under the base and on the outer wall faces (as drawn)"}
    return lines


def assert_complete(lines):
    """R-POOL-2 / R-POOL-3 guards on a finished concrete takeoff (also usable on another method's output)."""
    if "C_BASE" not in lines or "D_WALLS" not in lines:
        raise PoolError("R-POOL-2: a pool takeoff needs both a base line and a wall line (walls omitted?)")
    w = lines["D_WALLS"]
    if w.get("m3") == 0:
        raise PoolError("R-POOL-2: pool walls measured as 0 m3; an unknown height is None (HELD), never 0")
    for k, v in lines.items():
        if k.startswith(("C_", "D_", "E_")) and "blind" in v.get("basis", "").lower():
            raise PoolError(f"R-POOL-3: {k} includes blinding")
    return True


def check_wall_band(outer, inner, band_m2, *, tol=1e-6):
    """R-POOL-2: the wall band must equal outer - water outline (catches a half-measured curved pool)."""
    want = outer.area() - inner.area()
    if abs(band_m2 - want) > tol:
        raise PoolError(f"R-POOL-2: wall band {band_m2:.6f} m2 is not outer - water {want:.6f} m2")
    return True


def rc_total(lines):
    """the RC concrete total: base + walls + steps; None when any RC component is HELD"""
    tot = 0.0
    for k in ("C_BASE", "D_WALLS", "E_STEPS"):
        if k in lines:
            if lines[k].get("m3") is None:
                return None
            tot += lines[k]["m3"]
    return tot


# ---------------------------------------------------------------- formwork (cast-in-place only)

def formwork(outer, wall_t, base_t, wall_h, casting_method):
    """G: formed faces of a cast-in-place pool. Base cast on the blinding build-up (no soffit form); outer face formed
    over base + wall height; water face over the wall height; wall tops are not formed."""
    if casting_method != "CAST_IN_PLACE":
        return {"status": UNKNOWN, "m2": None,
                "basis": f"casting method {casting_method!r}: formwork stated only for a documented cast-in-place pool"}
    if wall_h is None:
        return {"status": HELD, "m2": None, "basis": "wall height HELD"}
    inner = outer.inset(wall_t)
    out_h = base_t + wall_h
    res = {
        "outer_face_m2": outer.perimeter() * out_h,
        "outer_curved_m2": outer.curved_length() * out_h,
        "water_face_m2": inner.perimeter() * wall_h,
        "water_curved_m2": inner.curved_length() * wall_h,
    }
    res["m2"] = res["outer_face_m2"] + res["water_face_m2"]
    res["status"] = DRAWING_CONFIRMED
    return res


# ---------------------------------------------------------------- waterproofing and finishes (areas only)

def surfaces(outer, wall_t, base_t, wall_h):
    """I: membrane on the protected concrete faces (net, measured on the concrete); J: water-side surfaces."""
    if wall_h is None:
        return None
    inner = outer.inset(wall_t)
    return {"membrane_under_base_m2": outer.area(), "membrane_outer_walls_m2": outer.perimeter() * (base_t + wall_h),
            "finish_floor_m2": inner.area(), "finish_walls_m2": inner.perimeter() * wall_h}


# ---------------------------------------------------------------- reinforcement by bar population

def kg_per_m(d_mm):
    """unit mass method D2_OVER_162 (engine/source/rebar_unit_mass.py), the method of the merged slab / stair ledgers"""
    return d_mm * d_mm / 162.0


def _counts(rate_or_spacing, extent, *, closed=False, spacing=False):
    """A = ceil, B = A + 1 (an edge bar at both ends; on a closed loop B = A), C = unrounded"""
    if spacing:
        c = extent / rate_or_spacing
    else:
        c = rate_or_spacing * extent
    a = int(math.ceil(c - EPS))
    return {"A": a, "B": a if closed else a + 1, "C": c}


def rebar(population, outer, wall_t, base_t, wall_h, *, soil_cover=None):
    """F: bar families of one printed population on the pool. population keys (None = not printed):
        wall_v_out, wall_v_in: (n per m, d)     wall_h_out, wall_h_in: (spacing m, d)
        floor_main, floor_dist: (n per m, d)    rim, corner: (count, d)
    Lengths: soil_cover None = face to face (the merged ledgers' basis); a number = net of that printed cover on the
    soil faces (outer wall face, base underside, base edge); the water-face and wall-top cover is not printed and is not
    deducted (upper bound). Returns rows with A / B / C bar counts, metres and kg; laps / development are not here."""
    if wall_h is None:
        raise PoolError("wall height HELD: no bar population without it")
    c = soil_cover or 0.0
    inner = outer.inset(wall_t)
    rows = []

    def add(fam, d, cnt, length=None, metres=None):
        m = {k: (cnt[k] * length if metres is None else metres[k]) for k in "ABC"}
        rows.append({"family": fam, "d": d, "count": cnt, "length_m": length,
                     "m": m, "kg": {k: m[k] * kg_per_m(d) for k in "ABC"}})

    v_len = base_t + wall_h - c
    if population.get("wall_v_out"):
        n, d = population["wall_v_out"]
        add("wall vertical, outer face", d, _counts(n, outer.inset(c).perimeter() if c else outer.perimeter(),
                                                     closed=True), v_len)
    if population.get("wall_v_in"):
        n, d = population["wall_v_in"]
        add("wall vertical, water face", d, _counts(n, inner.perimeter(), closed=True), v_len)
    for key, face, line in (("wall_h_out", "outer", outer.inset(c) if c else outer), ("wall_h_in", "water", inner)):
        if population.get(key):
            s, d = population[key]
            add(f"wall horizontal hoops, {face} face (over the wall height above the base top)", d,
                _counts(s, wall_h, spacing=True), line.perimeter())
    mesh = outer.inset(c) if c else outer
    for key, layer_dir in (("floor_main", "across_back"), ("floor_dist", "along_back")):
        if population.get(key):
            n, d = population[key]
            ch = mesh.chords(layer_dir, n)
            for layer in ("bottom", "top"):
                add(f"floor {layer}, {key} ({layer_dir})", d, {k: ch[k][0] for k in "ABC"},
                    metres={k: ch[k][1] for k in "ABC"})
    centre = outer.inset(wall_t / 2)
    for key, fam in (("rim", "rim bars at the wall top"), ("corner", "corner bars floor / wall")):
        if population.get(key):
            n, d = population[key]
            add(fam, d, {"A": n, "B": n, "C": n}, centre.perimeter())
    tot = {k: sum(r["kg"][k] for r in rows) for k in "ABC"}
    return rows, tot


# ---------------------------------------------------------------- ledger from a JSON input

def ledger(inp):
    u = inp.get("unit", "m")
    o = inp["outline"]
    if o["kind"] == "D":
        outer = Outline("D", r=to_m(o["r"], u), b=to_m(o["b"], u))
    else:
        outer = Outline("RECT", a=to_m(o["a"], u), b=to_m(o["b"], u))
    wt, bt = to_m(inp["wall_t"], u), to_m(inp["base_t"], u)
    wh = to_m(inp.get("wall_h"), u)
    conc = concrete_components(outer, wt, bt, wh, blinding_t=to_m(inp.get("blinding_t"), u),
                               screed_t=to_m(inp.get("screed_t"), u), membrane_t=to_m(inp.get("membrane_t"), u),
                               blinding_projection=to_m(inp.get("blinding_projection"), u),
                               element_class=inp.get("element_class", "REINFORCED_CONCRETE"))
    for comp in ("steps", "pump_room"):
        if not inp.get(comp + "_drawn", False):
            conc["E_STEPS" if comp == "steps" else "K_PUMP_ROOM"] = {"m3": None,
                                                                    "status": NOT_DRAWN,
                                                                    "basis": f"{comp} not drawn: no line (R-POOL-5)"}
    # a NOT_DRAWN component is reported but never enters the RC total
    rc_lines = {k: v for k, v in conc.items() if v.get("status") != NOT_DRAWN}
    assert_complete(rc_lines)
    out = {"concrete": conc, "rc_total_m3": rc_total(rc_lines),
           "formwork": formwork(outer, wt, bt, wh, inp.get("casting_method")),
           "surfaces": surfaces(outer, wt, bt, wh), "rebar": {}}
    for name, pop in (inp.get("populations") or {}).items():
        pop = {k: tuple(v) if v else None for k, v in pop.items()}
        for basis, cov in (("face_to_face", None), ("net_soil_cover", to_m(inp.get("soil_cover"), u))):
            if basis == "net_soil_cover" and cov is None:
                continue
            rows, tot = rebar(pop, outer, wt, bt, wh, soil_cover=cov)
            out["rebar"][f"{name}/{basis}"] = {"rows": rows, "kg": tot}
    return out


# ---------------------------------------------------------------- synthetic fixture (NOT Alsenan)

def check():
    """A rectangular pool 4.00 x 6.00 m outside (mm input), walls 250 mm, base 300 mm, water depth 1.40 m; and a
    D pool r 2.00, b 1.00 (cm input). Hand values worked on paper."""
    ok = True

    def eq(name, got, want, tol=1e-6):
        nonlocal ok
        good = got is not None and abs(got - want) <= tol
        ok &= good
        print(("PASS " if good else "FAIL ") + f"{name}: {got} vs {want}")

    led = ledger({"unit": "mm", "outline": {"kind": "RECT", "a": 4000, "b": 6000}, "wall_t": 250, "base_t": 300,
                  "wall_h": 1400, "blinding_t": 100, "screed_t": 50, "membrane_t": 10, "casting_method": "CAST_IN_PLACE"})
    c = led["concrete"]
    eq("rect base 24 x 0.30", c["C_BASE"]["m3"], 7.2)
    eq("rect band 24 - 3.5 x 5.5", c["D_WALLS"]["plan_m2"], 4.75)
    eq("rect walls 4.75 x 1.40", c["D_WALLS"]["m3"], 6.65)
    eq("rc total", led["rc_total_m3"], 13.85)
    eq("blinding lower bound (24 + 20 x 0.06 + pi 0.0036) x 0.10", c["B_BLINDING"]["m3_lower_bound"],
       (24 + 20 * 0.06 + math.pi * 0.0036) * 0.1)
    f = led["formwork"]
    eq("formwork outer 20 x 1.70", f["outer_face_m2"], 34.0)
    eq("formwork water 18 x 1.40", f["water_face_m2"], 25.2)
    d = Outline("D", r=to_m(200, "cm"), b=to_m(100, "cm"))
    eq("D area 2 x 2 x 1 + pi 4 / 2", d.area(), 4 + 2 * math.pi)
    eq("D perimeter 4 + 2 + 2 pi", d.perimeter(), 6 + 2 * math.pi)
    ch = d.chords("across_back", 2.0)
    eq("D chords C = rate x area", ch["C"][1], 2 * (4 + 2 * math.pi))
    print("ALL PASS" if ok else "SOME FAILED")
    return ok


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--check":
        sys.exit(0 if check() else 1)
    if len(sys.argv) == 3 and sys.argv[1] == "ledger":
        print(json.dumps(ledger(json.load(open(sys.argv[2]))), indent=1, default=str))
        sys.exit(0)
    print(__doc__)
    sys.exit(2)
