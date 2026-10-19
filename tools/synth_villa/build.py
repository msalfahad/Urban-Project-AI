"""Write a synthetic villa (villas.py) as a DXF and its truth as JSON (T-019).

    write_villa(villa_id, path, *, units="mm", layers="AIA", rotate_deg=0.0, mirror=False, drop_labels=())
        -> {"path", "truth"}
    truth_of(villa_id, *, units, layers, rotate_deg, mirror, drop_labels) -> the truth record (no file written)

Truth is computed from the villa SPEC with plain formulas (shoelace + circular segments for bulged edges, arc length,
opening width = s1 - s0); the drawing is written from the same spec, and the engine is never called here. Variants
move only the drawing: `rotate_deg` turns the plan contents about the centre of its outer box, `mirror` mirrors them
x -> -x first, `units` "mm" or "m" scales every coordinate ($INSUNITS 4 or 6), `layers` picks the layer names
("AIA": A-WALL ...; "ARABIC": جدران ...), `drop_labels` removes room words. Areas, lengths, counts and widths do
not change; the truth's `point_m` / `centre_m` give where each room probe and opening centre lands in drawing
coordinates (m), so a reader can match its own output to it.
"""

from __future__ import annotations

import copy
import math

from tools.synth_villa import villas as V

UNITS = {"mm": (1000.0, 4), "m": (1.0, 6)}
LAYERS = {
    "AIA": {"wall": "A-WALL", "glaz": "A-GLAZ", "door": "A-DOOR", "text": "A-TEXT", "frame": "A-FRAME",
            "title": "A-TITLE"},
    "ARABIC": {"wall": "جدران", "glaz": "زجاج", "door": "ابواب", "text": "نصوص", "frame": "اطار", "title": "عنوان"},
}
# sheet frames (m, drawing coordinates before scaling): one per floor, side by side; the plan's outer-box centre
# sits at the frame's PLAN_AT point whatever the rotation
FRAME_W, FRAME_H, FRAME_GAP = 34.0, 30.0, 6.0
PLAN_AT = (17.0, 16.0)
FLOOR_ORDER = ("GF", "1F", "2F")
WALL_FAMILY_TOL = 1e-9


# ---- spec geometry (plain formulas; the truth)
def _pt(v):
    return (float(v[0]), float(v[1]))


def _bulge(v):
    return float(v[2]) if len(v) > 2 else 0.0


def _seg(r, theta):
    return 0.5 * r * r * (theta - math.sin(theta))


def _arc_of(p, q, b):
    """chord p -> q with bulge b: (centre, radius, sweep theta > 0); b > 0 runs counter-clockwise."""
    theta = 4.0 * math.atan(abs(b))
    c = math.dist(p, q)
    r = c / (2.0 * math.sin(theta / 2.0))
    mx, my = (p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0
    ux, uy = (q[0] - p[0]) / c, (q[1] - p[1]) / c
    h = r * math.cos(theta / 2.0)
    sgn = 1.0 if b > 0 else -1.0                       # centre on the left of p -> q for a counter-clockwise arc
    return (mx - sgn * uy * h, my + sgn * ux * h), r, theta


def area_m2(poly):
    """area of a face polygon with bulged edges: |signed shoelace over the chords + the signed circular segments|.
    A positive bulge (counter-clockwise arc) adds its segment to the signed area, a negative one subtracts it, for
    either drawing direction of the polygon (a counter-clockwise polygon's outward bulge is positive)."""
    pts = [_pt(v) for v in poly]
    n = len(pts)
    s = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)) / 2.0
    for i, v in enumerate(poly):
        b = _bulge(v)
        if b:
            _c, r, th = _arc_of(pts[i], pts[(i + 1) % n], b)
            s += _seg(r, th) * (1.0 if b > 0 else -1.0)
    return abs(s)


def perimeter_lm(poly):
    pts = [_pt(v) for v in poly]
    n, tot = len(pts), 0.0
    for i, v in enumerate(poly):
        b = _bulge(v)
        if b:
            _c, r, th = _arc_of(pts[i], pts[(i + 1) % n], b)
            tot += r * th
        else:
            tot += math.dist(pts[i], pts[(i + 1) % n])
    return tot


def width_m(o):
    return round(o["s1"] - o["s0"], 9)


def _centre_local(o):
    m = (o["lo"] + o["hi"]) / 2.0
    s = (o["s0"] + o["s1"]) / 2.0
    return (m, s) if o["axis"] == "x" else (s, m)


def thickness_m(o):
    return round(o["hi"] - o["lo"], 9)


# ---- the transform: local metres -> drawing metres (then x scale for the units)
class _Xf:
    def __init__(self, outer, frame_origin, rotate_deg, mirror):
        xs, ys = [v[0] for v in outer], [v[1] for v in outer]
        self.c = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
        self.at = (frame_origin[0] + PLAN_AT[0], frame_origin[1] + PLAN_AT[1])
        self.deg = float(rotate_deg)
        self.th = math.radians(rotate_deg)
        self.mirror = bool(mirror)

    def __call__(self, p):
        x, y = p[0] - self.c[0], p[1] - self.c[1]
        if self.mirror:
            x = -x
        ct, st = math.cos(self.th), math.sin(self.th)
        return (self.at[0] + x * ct - y * st, self.at[1] + x * st + y * ct)

    def angle(self, a_deg):
        """a direction angle in the local frame -> drawing frame."""
        return ((180.0 - a_deg) if self.mirror else a_deg) + self.deg


def _frame_origin(i):
    return (i * (FRAME_W + FRAME_GAP), 0.0)


# ---- truth
def truth_of(villa_id, *, units="mm", layers="AIA", rotate_deg=0.0, mirror=False, drop_labels=()):
    spec = V.VILLAS[villa_id]
    if units not in UNITS or layers not in LAYERS:
        raise ValueError(f"units in {tuple(UNITS)}, layers in {tuple(LAYERS)}")
    floors = {}
    for i, (fl, f) in enumerate(_floors(spec)):
        X = _Xf(f["outer"], _frame_origin(i), rotate_deg, mirror)
        rooms = []
        for rid, r in f["rooms"].items():
            labelled = r["label"] is not None and rid not in drop_labels
            rooms.append({"room_id": rid, "label": r["label"] if labelled else None, "labelled": labelled,
                          "code": r["code"] if labelled else None, "design_code": r["code"], "wet": r["wet"],
                          "kind": r["kind"], "area_m2": area_m2(r["poly"]), "perimeter_lm": perimeter_lm(r["poly"]),
                          "point_m": X(r["probe"]),
                          "doors": [o["id"] for o in f["openings"] if o["kind"] == "DOOR" and rid in o["rooms"]],
                          "windows": [o["id"] for o in f["openings"] if o["kind"] == "WINDOW" and rid in o["rooms"]]})
        openings = [{"opening_id": o["id"], "kind": o["kind"], "width_m": width_m(o), "wall_t_m": thickness_m(o),
                     "rooms": list(o["rooms"]), "exterior": len(o["rooms"]) == 1, "centre_m": X(_centre_local(o)),
                     "mirrored_block": o["hand"] == "R"} for o in f["openings"]]
        hand = V.HAND[villa_id][fl]
        walls = {}
        for fam, w in hand["walls"].items():
            op = sum(width_m(o) for o in f["openings"] if abs(thickness_m(o) - float(fam)) < 1e-6)
            walls[fam] = {"gross_lm": w["gross_lm"], "openings_lm": op, "net_lm": w["gross_lm"] - op}
        outer = area_m2(f["outer"])
        floors[fl] = {
            "title": f["title"], "level": f["level"], "outer_m2": outer,
            "rooms": rooms, "openings": openings, "walls_by_thickness": walls,
            "wall_mass_m2": outer - sum(r["area_m2"] for r in rooms),
            "counts": {"rooms": len(rooms), "wet_rooms": sum(r["wet"] for r in rooms),
                       "unlabelled_rooms": sum(not r["labelled"] for r in rooms),
                       **{k: sum(o["kind"] == k for o in f["openings"]) for k in ("DOOR", "WINDOW", "PASSAGE")}},
        }
        if "curved_wall" in hand:
            floors[fl]["curved_wall"] = dict(hand["curved_wall"])
    return {"schema": "URBAN_SYNTH_VILLA_TRUTH_V1", "villa_id": villa_id,
            "variant": {"units": units, "layers": layers, "rotate_deg": float(rotate_deg), "mirror": bool(mirror),
                        "drop_labels": sorted(drop_labels)},
            "conventions": {
                "room_area": "area inside the wall faces (gross: no column, fixture or tread deducted); curved edges "
                             "exact (circular segment)",
                "walls": "per thickness: exterior ring on its centreline + each partition's clear length between the "
                         "faces it meets (junction piece counted once); gross = openings not deducted, net = gross - "
                         "opening widths in walls of that thickness",
                "coordinates": "point_m / centre_m are drawing coordinates in metres (after rotation and mirror)",
                "source": "spec formulas + hand values (tools/synth_villa/villas.py HAND); never the engine"},
            "floors": floors}


def _floors(spec):
    return [(fl, spec["floors"][fl]) for fl in FLOOR_ORDER if fl in spec["floors"]]


# ---- the drawing
def _cut(a, b, openings):
    """the straight face line a-b with the gap of every opening on it removed (faces are axis-aligned locally)."""
    (x1, y1), (x2, y2) = a, b
    vert, horiz = abs(x1 - x2) < 1e-12, abs(y1 - y2) < 1e-12
    gaps = []
    for o in openings:
        if o["axis"] == "x" and vert and any(abs(x1 - w) < 1e-9 for w in (o["lo"], o["hi"])) and \
                min(y1, y2) - 1e-9 <= o["s0"] and o["s1"] <= max(y1, y2) + 1e-9:
            gaps.append((o["s0"], o["s1"]))
        if o["axis"] == "y" and horiz and any(abs(y1 - w) < 1e-9 for w in (o["lo"], o["hi"])) and \
                min(x1, x2) - 1e-9 <= o["s0"] and o["s1"] <= max(x1, x2) + 1e-9:
            gaps.append((o["s0"], o["s1"]))
    if not gaps:
        return [(a, b)]
    t0, t1 = (min(y1, y2), max(y1, y2)) if vert else (min(x1, x2), max(x1, x2))
    pieces, pos = [], t0
    for s0, s1 in sorted(gaps):
        if s0 > pos + 1e-12:
            pieces.append((pos, s0))
        pos = max(pos, s1)
    if t1 > pos + 1e-12:
        pieces.append((pos, t1))
    return [(((x1, p), (x1, q)) if vert else ((p, y1), (q, y1))) for p, q in pieces]


def _door_insert(o):
    """(hinge, rotation deg, yscale sign) of the unit door block (leaf along +x, swing 0..90 deg closing at +y) whose
    closed leaf fills the gap and whose open leaf stands in the room on side `opens`."""
    lo, hi, s0, s1 = o["lo"], o["hi"], o["s0"], o["s1"]
    plain = {("x", "+"): ((hi, s0), 0.0), ("x", "-"): ((lo, s1), 180.0),
             ("y", "+"): ((s1, hi), 90.0), ("y", "-"): ((s0, lo), 270.0)}
    mirrored = {("x", "+"): ((hi, s1), 0.0), ("x", "-"): ((lo, s0), 180.0),
                ("y", "+"): ((s0, hi), 90.0), ("y", "-"): ((s1, lo), 270.0)}
    if o["hand"] == "R":
        h, r = mirrored[(o["axis"], o["opens"])]
        return h, r, -1.0
    h, r = plain[(o["axis"], o["opens"])]
    return h, r, 1.0


def write_villa(villa_id, path, *, units="mm", layers="AIA", rotate_deg=0.0, mirror=False, drop_labels=()):
    import ezdxf
    truth = truth_of(villa_id, units=units, layers=layers, rotate_deg=rotate_deg, mirror=mirror,
                     drop_labels=drop_labels)
    k, insunits = UNITS[units]
    L = LAYERS[layers]
    S = lambda p: (p[0] * k, p[1] * k)                                       # noqa: E731
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = insunits
    for name in L.values():
        if name not in doc.layers:
            doc.layers.add(name)
    blk = doc.blocks.new("SV_DOOR")
    blk.add_line((0, 0), (k, 0), dxfattribs={"layer": "0"})                  # the open leaf, 1 m long
    blk.add_arc((0, 0), k, 0, 90, dxfattribs={"layer": "0"})                 # the swing, closing at +y
    msp = doc.modelspace()
    spec = V.VILLAS[villa_id]
    for i, (fl, f) in enumerate(_floors(spec)):
        ox, oy = _frame_origin(i)
        msp.add_lwpolyline([S((ox, oy)), S((ox + FRAME_W, oy)), S((ox + FRAME_W, oy + FRAME_H)),
                            S((ox, oy + FRAME_H))], close=True, dxfattribs={"layer": L["frame"]})
        msp.add_text(f["title"], dxfattribs={"layer": L["title"], "height": 0.5 * k}).set_placement(
            S((ox + 2.0, oy + 1.5)))
        X = _Xf(f["outer"], (ox, oy), rotate_deg, mirror)

        def line(a, b, layer):
            msp.add_line(S(X(a)), S(X(b)), dxfattribs={"layer": layer})

        def face(poly):
            n = len(poly)
            for j, v in enumerate(poly):
                p, q, b = _pt(v), _pt(poly[(j + 1) % n]), _bulge(v)
                if b:
                    (cx, cy), r, th = _arc_of(p, q, b)
                    a0 = math.degrees(math.atan2(p[1] - cy, p[0] - cx))
                    a1 = math.degrees(math.atan2(q[1] - cy, q[0] - cx))
                    if b < 0:
                        a0, a1 = a1, a0                                       # ezdxf arcs run counter-clockwise
                    d0, d1 = X.angle(a0), X.angle(a1)
                    if mirror:
                        d0, d1 = d1, d0                                       # a mirror reverses the sweep
                    msp.add_arc(S(X((cx, cy))), r * k, d0 % 360.0, d1 % 360.0, dxfattribs={"layer": L["wall"]})
                else:
                    for a, c in _cut(p, q, f["openings"]):
                        line(a, c, L["wall"])

        for r in f["rooms"].values():
            face(r["poly"])
        face(f["outer"])
        for o in f["openings"]:
            lo, hi, s0, s1 = o["lo"], o["hi"], o["s0"], o["s1"]
            for s in (s0, s1):                                                # jambs
                line((lo, s), (hi, s), L["wall"]) if o["axis"] == "x" else line((s, lo), (s, hi), L["wall"])
            if o["kind"] == "WINDOW":
                for frac in (1 / 3, 2 / 3):
                    g = lo + (hi - lo) * frac
                    line((g, s0), (g, s1), L["glaz"]) if o["axis"] == "x" else line((s0, g), (s1, g), L["glaz"])
            if o["kind"] == "DOOR":
                hinge, rot, ys = _door_insert(o)
                w = width_m(o)
                xs = 1.0
                if mirror:                                                   # Mx R(r) S = R(-r) S(-1, 1)
                    xs, rot = -xs, -rot
                msp.add_blockref("SV_DOOR", S(X(hinge)), dxfattribs={
                    "layer": L["door"], "xscale": xs * w, "yscale": ys * w, "rotation": (rot + rotate_deg) % 360.0})
        for rid, r in f["rooms"].items():
            if r["label"] is None or rid in drop_labels:
                continue
            msp.add_text(r["label"], dxfattribs={"layer": L["text"], "height": 0.2 * k}).set_placement(
                S(X(r["probe"])))
            msp.add_text(f["level"], dxfattribs={"layer": L["text"], "height": 0.15 * k}).set_placement(
                S(X((r["probe"][0], r["probe"][1] - 0.5))))
    doc.saveas(str(path))
    return {"path": str(path), "truth": copy.deepcopy(truth)}
