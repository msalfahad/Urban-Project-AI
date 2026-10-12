"""SCOPE QUANTITIES (M8) - the scope a completeness finding locates, measured from the drawn plan or bounded by a
stated range (generic; stdlib + engine.source helpers). Conventions V6 switch it on (SCOPE_FROM_FINDINGS).

    enabled(conv) -> bool
    measure(CR, D, items, conv, *, scan=None, src_file="") -> {items, register, bounds, risk, findings, totals}
    totals(items, bounds, findings) -> the bounded total (BOQ section F)

The completeness pass (concrete_completeness) says WHAT the drawing shows that no item holds. A QS would price each of
those things: from the drawn plan dimension, with a stated professional assumption for the dimension the drawing does
not print - or, when the element itself is uncertain, as an allowance with a range. This pass does that, finding by
finding, and nothing stays volume-less:

  MEASURED      the finding's family is SETTLED (one family; its layer, words and shape agree: confidence MEDIUM or
                HIGH, or a stated rule below) and its plan geometry is enough: PROVISIONAL items from the drawn geometry
                x printed values (a dimension note beside the element, PRINTED_DIMENSION_NOTES) or the V6 conventions
                (support CONVENTION_ONLY, confidence LOW, every assumed dimension named)
                  POOL        walls = drawn wall plan area (ring / strip x drawn width) x wall height; floor = the
                              pool's outer plan area x floor thickness
                  LIFT pit    walls x pit depth; base slab unless the pit lies inside a measured footing (its base)
                  WATER_TANK  walls x tank height; cover slab; base slab unless it stands on a slab plan
                  DOMES       spherical cap pi (r^2 + h^2) x shell thickness, h = rise ratio x r; a ring drawn as two
                              circles (and not measured as a beam) x ring depth. On the topmost slab plan a radial or
                              ring group is a dome when the set names domes (DOME_ON_TOP_PLAN): a stair needs a storey
                              above it to arrive at
                  STAIRS      a flight drawn outside any stair zone: its tread lines -> stair_measure (risers = lines +
                              1 or lines, convention riser, waist); a flight drawn at the same place on two vertically
                              adjacent plans is measured once (STAIR_FLIGHT_ON_TWO_PLANS), the other drawing's volume is
                              an exposure
                  BOUNDARY    a boundary-wall strip whose drawn width is the first size of the family's schedule row
                              (BOUNDARY_WALL_ROW_BY_WIDTH): strip length x row section
  BOUNDED       every other finding: an exposure range (low, high) by kind and shape, BOUND_RULES below - never added
                to the measured total, always to the bounded range
  HELD_BY_ITEMS the finding restates UNRESOLVED items (their exposure is counted once, with the items)
  EXPLAINED     the finding names a family that is now measured (a dome note when a dome is measured)
  QUALIFIER     a note / conflict on a measured member with no volume of its own (0 .. 0, stated)

The bounded total (totals) = measured (planning) + every UNRESOLVED item's exposure + every bound, low and high; each
finding contributes once. Reinforcement for the new families is MISSING_DATA (never a kg/m3 ratio). The pass reads
the route's detection record, the completeness report and the items, never a reference quantity.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from engine.source import concrete_completeness as CC
from engine.source import member_detection as MD
from engine.source import provisional_estimate as PE
from engine.source import slab_engine as SE
from engine.source import stair_measure as SM

POLICY_ID = "SCOPE_QUANTITIES_V1"
SETTLED = ("MEDIUM", "HIGH")
STOREY_ORDER = CC.STOREY_ORDER
CORE = ("FOOTINGS", "GROUND_BEAMS", "COLUMNS", "BEAMS", "SLABS")
PLAIN = "PLAIN"
RC = "RC"
STATES = ("MEASURED", "BOUNDED", "HELD_BY_ITEMS", "EXPLAINED", "QUALIFIER")
# printed dimension notes beside an element: keyword, number, optional unit
DIM_NOTE = re.compile(r"\b(DEPTH|DEEP|HEIGHT|HT|H|THICKNESS|THICK|THK|T|WAIST|RISER|RISE|WALL|FLOOR|BASE|COVER|SLAB|"
                      r"SHELL|RING)\s*[=:.]?\s*(\d+(?:\.\d+)?)\s*(MM|CM|M)?\b")
DIM_KIND = {"DEPTH": "height", "DEEP": "height", "HEIGHT": "height", "HT": "height", "H": "height",
            "THICKNESS": "thickness", "THICK": "thickness", "THK": "thickness", "T": "thickness", "WALL": "wall",
            "FLOOR": "floor", "BASE": "floor", "COVER": "cover", "SLAB": "cover", "SHELL": "shell", "WAIST": "waist",
            "RISER": "riser", "RISE": "rise", "RING": "ring"}
PLAUSIBLE = {"height": (0.5, 4.0), "thickness": (0.08, 0.6), "wall": (0.08, 0.6), "floor": (0.08, 0.6),
             "cover": (0.08, 0.6), "shell": (0.05, 0.4), "waist": (0.1, 0.3), "riser": (0.12, 0.22), "rise": (0.3, 6.0),
             "ring": (0.15, 1.0)}
NOTE_NEAR_M = 1.5
NON_STRUCTURAL_WORDS = {"FURN", "FURNITURE", "FIXTURE", "FIXTURES", "EQUIP", "EQUIPMENT", "SANITARY", "PLUMB",
                        "PLUMBING", "ELEC", "ELECTRICAL", "LIGHT", "LIGHTING", "HVAC", "MECH", "MECHANICAL",
                        "LANDSCAPE", "TREE", "TREES", "PLANTING", "IRRIGATION", "INTERIOR", "DECOR", "CARPET", "TILE",
                        "TILES", "FLOORING", "CEILING"}

BOUND_RULES = {
    "REGION_EXCLUDED": "0 .. region area x the higher of the sheet's slab thickness and SLAB_THICKNESS_EXPOSURE_M high "
                       "(the region may be a void or a slab of its detail)",
    "OPENING_NOT_DEDUCTED": "-opening area x panel thickness .. 0 (deduct when the opening is confirmed)",
    "COLUMN_PRESENCE_NOT_ITEMIZED": "0 .. the drawn column's own volume",
    "COLUMN_ITEM_WITHOUT_PRESENCE": "-the item's volume .. 0 (over-counted when the column stops)",
    "COLUMN_BAND_NOT_ON_PLAN": "0 .. occurrences x the largest measured column of that storey",
    "MEMBER_DETECTED_NOT_ITEMIZED": "0 .. plan area x the deepest section of its family (schedule / exposure range)",
    "SCHEDULED_NOT_PLACED": "0 .. one instance (a beam over the longest measured beam length)",
    "SCHEDULE_ROW_UNREAD": "0 .. one instance of the row's sizes (a beam over the longest measured beam length)",
    "LABEL_NOT_CONSUMED": "0 .. one member of the label's family at its scheduled (else exposure) section",
    "PLACED_NOT_SCHEDULED": "0 .. one member of the label's family at the exposure section",
    "LABEL_MEMBER_CONFLICT": "the band's volume under the label's section minus its measured volume (either sign)",
    "MEMBER_OVERLAP": "-overlap x the deeper member's depth .. 0 (counted twice)",
    "HATCH_ON_MEASURED_MEMBER": "-fill area x the host's thickness .. 0 (the fill marks a void at most)",
    "DEPENDENCY": "qualifier: the member is measured; the note asks for another document (0 .. 0)",
    "SLAB_COVERAGE_LOW": "qualifier: the plan's regions carry their own findings (0 .. 0, never counted twice)",
    "MEMBER_OUTLINE_SUSPECT": "qualifier: the column is measured at its section; the outline is another element's",
    "STOREY_PLAN_MISSING": "the neighbouring storeys' measured slab + beam volume (min .. max; one neighbour 0.5 .. 1)",
    "PLAN_SHEET_NOT_MEASURED": "the neighbouring storeys' measured slab + beam volume (min .. max)",
    "STOREY_COLUMN_BANDS_MISSING": "qualifier: the columns are drawn; their sections are asked for",
    "STOREY_HEIGHT_MISSING": "qualifier: the storey's columns are held by their own findings",
    "REFERENCED_NOT_DRAWN": "the family's allowance (parapets: free roof edge x section; tank / pit / pool / dome: one "
                            "element at its convention size; any other family: REFERENCED_ELEMENT_ALLOWANCE_M3), 0 low",
    "DRAWN_NOT_MEASURED": "by shape: strip 0 .. length x width x UNEXPLAINED_STRIP_DEPTH_M high; area / fill 0 .. area x "
                          "slab thickness high; ring 0 .. ring area x the highest wall height; curve / linework 0 .. "
                          "half the length x UNEXPLAINED_LINEWORK_SECTION_M2 high; radial 0 .. the dome or the winder "
                          "it could be; a fill round the whole plan: plain concrete 0 .. area x blinding high",
    "STAIR_NOT_MEASURED": "0 .. zone (or flight) plan x (waist high / cos 40 deg + riser high / 2)",
}


class ScopeError(ValueError):
    pass


def enabled(conv):
    return conv is not None and "SCOPE_FROM_FINDINGS" in conv.items and \
        conv.base("SCOPE_FROM_FINDINGS") == "SETTLED_MEASURED_ELSE_BOUNDED"


# ====================================================================== small helpers
def _t(conv, cid, default=None):
    if cid in conv.items:
        return conv.triple(cid)
    if default is None:
        raise ScopeError(f"convention {cid} is required")
    return default


def _shape(f):
    m = re.search(r"\bshape ([A-Z_]+)", f.get("EVIDENCE") or "")
    return m.group(1) if m else None


def _candidates(f):
    m = re.search(r"could be ([A-Z_]+(?: or [A-Z_]+)*)", f.get("EVIDENCE") or "")
    return m.group(1).split(" or ") if m else []


ELEMENT_FAMILIES = ("POOL", "LIFT", "WATER_TANK", "DOMES", "STAIRS", "BOUNDARY_WALL", "PARAPETS")


def _layer(f):
    m = re.match(r"layer (.+?): \d+ entities", f.get("EVIDENCE") or "")
    return m.group(1) if m else None


def _non_structural(f, conv):
    lay = _layer(f)
    return bool(lay) and "NON_STRUCTURAL_LAYERS" in conv.items and \
        bool(set(CC._tokens(lay)) & NON_STRUCTURAL_WORDS)


def _settled(f):
    """one family, confidence MEDIUM / HIGH, no candidates - and the layer name and the notes beside it do not name
    two different element families (a pool layer with a lift note beside it is not settled)."""
    if f["FAMILY"] in ("UNKNOWN", "", None) or f.get("CONFIDENCE") not in SETTLED or _candidates(f):
        return False
    ev = f.get("EVIDENCE") or ""
    named = set()
    m = re.search(r"layer suggests ([A-Z_]+)", ev)
    if m:
        named.add(m.group(1))
    m = re.search(r"notes: ([A-Z_, ]+?)(?:;|$)", ev)
    if m:
        named.update(x.strip() for x in m.group(1).split(","))
    return not ({x for x in named if x in ELEMENT_FAMILIES} - {f["FAMILY"]})


def _box_draw(box_m, org, u):
    return (box_m[0] / u + org[0], box_m[1] / u + org[1], box_m[2] / u + org[0], box_m[3] / u + org[1])


def _box_area(b):
    return max(b[2] - b[0], 0.0) * max(b[3] - b[1], 0.0)


def _iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    uni = _box_area(a) + _box_area(b) - inter
    return inter / uni if uni > 0 else 0.0


def _rng(lo, base, hi):
    v = sorted((lo, base, hi))
    return v[0], base, v[2]


def _combo(fn, *triples):
    """fn evaluated at every low / base / high of its parameters: (min, value at the bases, max)."""
    import itertools
    vals = [fn(*xs) for xs in itertools.product(*triples)]
    return min(vals), fn(*(t[1] for t in triples)), max(vals)


def _ring_poly_area(ring):
    return abs(CC._signed_area(ring))


def _perimeter(ring):
    return sum(math.dist(ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring)))


# ====================================================================== the run's context
class _Ctx:
    def __init__(self, CR, D, items, conv, scan, src_file):
        self.CR, self.D, self.items, self.conv = CR, D, items, conv
        self.u = D["unit_m"]
        P = CR.get("params") or {}
        self.ents = {sid: {e["eid"]: e for e in ents} for sid, ents in (P.get("_ents") or {}).items()}
        self.gids = P.get("_group_eids") or {}
        self.sheets = {sid: rec["sheet"] for sid, rec in D["sheets"].items()}
        self.src = src_file or "drawing"
        slab_st = [rec["sheet"]["storey"] for _, rec in D["sheets"].items() if rec["sheet"]["role"] == "SLAB_PLAN"
                   and rec["sheet"].get("storey") in STOREY_ORDER]
        self.top = max(slab_st, key=STOREY_ORDER.index) if slab_st else None
        fams = set()
        for f in CR["findings"]:
            if f["KIND"] == "REFERENCED_NOT_DRAWN":
                fams.add(f["FAMILY"])
        for fam, s in (scan or {}).items():
            if s and s.get("n_texts"):
                fams.add(fam)
        words, _ = CC._note_words()
        for t in D["model"]["texts"]:
            if len(t.get("norm") or "") <= 60:
                fams.update(CC.note_families(t["norm"], words))
        self.referenced = fams
        self.texts = defaultdict(list)
        for t in D["model"]["texts"]:
            self.texts[t.get("sheet")].append(t)
        self.members = CC._members(D)
        self.lib = D.get("lib") or {}
        self.beam_len_max = max([i["dimensions"].get("length_m") or 0.0 for i in items
                                 if i["trade"] == "CONCRETE" and i["family"] == "BEAMS"] or [0.0])
        sa = defaultdict(float)
        for i in items:
            if i["trade"] == "CONCRETE" and i["family"] in ("SLABS", "GROUND_SLAB") and i["category"] != "UNRESOLVED":
                sa[i["storey"]] += (i.get("dimensions") or {}).get("area_m2") or 0.0
        self.slab_area_max = max(sa.values()) if sa else 0.0
        self.storey_rcv = defaultdict(float)        # measured slab + beam volume per storey (planning base)
        for i in items:
            if i["trade"] == "CONCRETE" and i["family"] in ("SLABS", "BEAMS") and i["category"] != "UNRESOLVED":
                self.storey_rcv[i["storey"]] += i.get("base") or 0.0

    def plan_box(self, sid):
        """the sheet-local box of the plan's measured slab faces (None when it has none)."""
        if not hasattr(self, "_pb"):
            held = set(_consumed_members(self))
            self._pb = {}
            for s_, ms in self.members.items():
                b = None
                for m in ms:
                    if m["kind"] == "FACE" and (s_, m["mid"]) in held:
                        b = CC._union_box(b, CC._bbox(m["poly"]))
                self._pb[s_] = CC._local_box(b, self.org(s_), self.u) if b else None
        return self._pb.get(sid)

    def org(self, sid):
        return (self.sheets.get(sid) or {}).get("origin") or (0.0, 0.0)

    def group(self, f):
        """the finding's drawn entities (drawing units); a finding located by a slab face (a flight in a stair well,
        a stair zone) holds the lines drawn inside that face."""
        sid = f["SHEET"]
        pool = self.ents.get(sid) or {}
        ids = self.gids.get(f["FINDING_ID"])
        if ids is None:
            ids = [x for x in (f.get("REFS") or "").replace("...", "").split(",") if x]
        got = [pool[i] for i in ids if i in pool]
        if got or not ids:
            return got
        face = self.face(sid, ids[0])
        if not face:
            return []
        poly = face["polygon"]
        tol = 0.01 / self.u                     # a line on the face's own boundary (a flight's end) is inside it

        def inside(x, y):
            return MD.point_in_poly(x, y, poly) or min(
                CC._seg_dist(x, y, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))) <= tol
        return [e for e in pool.values() if e["type"] in ("LINE", "ARC", "CIRCLE") and
                inside(sum(x for x, _ in e["pts"]) / len(e["pts"]), sum(y for _, y in e["pts"]) / len(e["pts"])) and
                not CC.annotation_layer(e["layer"])]

    def face(self, sid, face_id):
        for fc in (((self.D["sheets"].get(sid) or {}).get("slab") or {}).get("faces") or []):
            if fc["face_id"] == face_id:
                return fc
        return None

    def notes_near(self, f, ents):
        """printed dimension notes within NOTE_NEAR_M of the element: {kind: [m, ...]}."""
        sid = f["SHEET"]
        if ents:
            box = None
            for e in ents:
                box = CC._union_box(box, e["box"])
        elif f.get("BOX_M"):
            box = _box_draw(f["BOX_M"], self.org(sid), self.u)
        else:
            return {}
        return notes_in_box(self.texts.get(sid, ()), box, self.u)


def notes_in_box(texts, box, unit_m, near_m=NOTE_NEAR_M):
    """printed dimension notes beside a box (drawing units): {kind: [m]} - per kind the value of the note nearest the
    box within near_m (a neighbour's note further away is not this element's); two equally near notes that disagree
    give both values (not printed: ambiguous)."""
    r = near_m / unit_m
    found = defaultdict(list)                       # kind -> [(distance m, value)]
    for t in texts:
        dx = max(box[0] - t["x"], 0.0, t["x"] - box[2])
        dy = max(box[1] - t["y"], 0.0, t["y"] - box[3])
        d = math.hypot(dx, dy)
        if d > r:
            continue
        for m in DIM_NOTE.finditer((t.get("norm") or "").upper()):
            k = DIM_KIND[m.group(1)]
            v = _dim_value(float(m.group(2)), m.group(3), k)
            if v is not None:
                found[k].append((d * unit_m, v))
    out = {}
    for k, xs in found.items():
        xs.sort()
        near = [v for dd, v in xs if dd <= xs[0][0] + 0.1]
        out[k] = near
    return out


def _dim_value(x, unit, kind):
    """a printed number as metres: the written unit, else the one reading inside the plausible band of the kind."""
    lo, hi = PLAUSIBLE[kind]
    if unit:
        v = x / {"MM": 1000.0, "CM": 100.0, "M": 1.0}[unit]
        return v if lo <= v <= hi else None
    ok = [v for v in (x, x / 100.0, x / 1000.0) if lo <= v <= hi]
    return ok[0] if len(ok) == 1 else None


def _printed(notes, kinds, conv, cid):
    """(triple, printed?) - the first of the kinds (most specific first: 'RISE' before 'HEIGHT', 'SHELL' before 'T')
    with a printed note beside the element gives the value; two disagreeing notes of that kind: the convention."""
    for k in kinds:
        vals = sorted({round(v, 4) for v in notes.get(k, ())})
        if len(vals) == 1:
            return (vals[0], vals[0], vals[0]), True
        if vals:
            break
    return conv.triple(cid), False


# ====================================================================== geometry readers
def _inner_faces_t(lines, outer, u):
    """the wall thickness drawn by inner face lines that do not close (broken at the corners): the median distance of
    lines inside the outline, parallel to one of its sides, 0.08 - 0.6 m from it. None when there are none."""
    edges = [(outer[i], outer[(i + 1) % len(outer)]) for i in range(len(outer))]
    ds = []
    for e in lines:
        a, b = e["a"], e["b"]
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        if not MD.point_in_poly(mx, my, outer):
            continue
        L = math.dist(a, b)
        if L <= 0:
            continue
        best = None
        for p0, p1 in edges:
            el = math.dist(p0, p1)
            if el <= 0:
                continue
            cross = abs((b[0] - a[0]) * (p1[1] - p0[1]) - (b[1] - a[1]) * (p1[0] - p0[0])) / (L * el)
            if cross > math.sin(math.radians(3.0)):
                continue
            d = abs((p1[0] - p0[0]) * (p0[1] - my) - (p1[1] - p0[1]) * (p0[0] - mx)) / el * u
            if d > 1e-6 and (best is None or d < best):
                best = d
        if best is not None and 0.08 <= best <= 0.6:
            ds.append(best)
    if len(ds) < 2:
        return None
    ds.sort()
    return ds[len(ds) // 2]


def _wall_geometry(ctx, f, ents, t_conv):
    """(wall plan area triple m2, outer area m2, inner area m2, basis) of a box structure's drawn walls:
    a double outline (ring) -> the ring; one outline with inner face lines broken at the corners -> P t - 4 t^2 at
    the drawn t; a wall strip (parallel pairs) -> strip length x width; one outline alone -> the convention t."""
    u = ctx.u
    mag = f.get("MAGNITUDE") or {}
    lines = [e for e in ents if e["type"] == "LINE"]
    loops = CC._loops(lines, 0.002 / u) if lines else []
    areas = sorted((_ring_poly_area(r) * u * u, r) for r in loops)
    if areas:
        outer_a, outer = areas[-1]
        inner = [(a, r) for a, r in areas[:-1] if all(MD.point_in_poly(x, y, outer) for x, y in r)]
        if inner:
            ia = max(a for a, _ in inner)
            w = outer_a - ia
            return (w, w, w), outer_a, ia, "drawn double outline (ring)"
        per = _perimeter(outer) * u
        on_outer = {e["eid"] for e in lines if any(math.dist(e["a"], outer[i]) * u < 0.003 or
                                                    math.dist(e["b"], outer[i]) * u < 0.003 for i in range(len(outer)))
                    and _on_ring(e, outer, u)}
        t = _inner_faces_t([e for e in lines if e["eid"] not in on_outer], outer, u)
        if t:
            w = max(per * t - 4 * t * t, 0.0)
            return (w, w, w), outer_a, max(outer_a - w, 0.0), f"outline with inner faces {t:.3f} m inside it"
        walls = tuple(max(per * t - 4 * t * t, 0.0) for t in t_conv)
        return walls, outer_a, max(outer_a - walls[1], 0.0), "single drawn outline, wall thickness by convention"
    if mag.get("ring_area_m2"):
        w = mag["ring_area_m2"]
        return (w, w, w), mag.get("outer_area_m2"), mag.get("inner_area_m2"), "drawn double outline (ring)"
    if mag.get("strip_width_m") and mag.get("strip_length_m"):
        w = mag["strip_width_m"] * mag["strip_length_m"]
        box = f.get("BOX_M")
        fill = mag.get("fill_m2")
        outer = (fill + w) if fill else (_box_area(box) if box else None)
        inner = fill if fill else (max(outer - w, 0.0) if outer else None)
        return (w, w, w), outer, inner, f"drawn wall strip {mag['strip_width_m']:g} m x {mag['strip_length_m']:g} m"
    a = mag.get("area_m2") or mag.get("outer_area_m2")
    if a:
        per = 4 * math.sqrt(a)
        walls = tuple(max(per * t - 4 * t * t, 0.0) for t in t_conv)
        return walls, a, max(a - walls[1], 0.0), "closed outline area (square perimeter), wall thickness by convention"
    return None


def _on_ring(e, ring, u):
    """the line runs along one side of the ring (both ends on that side's line)."""
    for i in range(len(ring)):
        p0, p1 = ring[i], ring[(i + 1) % len(ring)]
        el = math.dist(p0, p1)
        if el <= 0:
            continue
        ok = all(abs((p1[0] - p0[0]) * (p0[1] - q[1]) - (p1[1] - p0[1]) * (p0[0] - q[0])) / el * u < 0.003
                 for q in (e["a"], e["b"]))
        if ok:
            return True
    return False


def _inside_footing(ctx, f):
    """the finding's centre lies inside a measured footing of a substructure plan (sheet-local metres: the plans
    share local coordinates)."""
    box = f.get("BOX_M")
    if not box:
        return False
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    held = set(_consumed_members(ctx))
    u = ctx.u
    for sid2, ms in ctx.members.items():
        if (ctx.sheets.get(sid2) or {}).get("role") not in ("FOUNDATION_PLAN", "GROUND_BEAM_PLAN"):
            continue
        org = ctx.org(sid2)
        for m in ms:
            if m["kind"] == "FOOTING" and (sid2, m["mid"]) in held:
                poly = [((x - org[0]) * u, (y - org[1]) * u) for x, y in m["poly"]]
                if MD.point_in_poly(cx, cy, poly):
                    return True
    return False


def _consumed_members(ctx):
    if not hasattr(ctx, "_cons"):
        cons = CC._consumption(ctx.D, ctx.items, ctx.members)
        ctx._cons = [k for k in cons if k != "__items__" and cons[k]["items"]]
    return ctx._cons


PITCH_M = (0.18, 0.40)


def _straight_run(part, going):
    """a straight run from parallel tread lines [(s0, s1, offset, entity)] (metres): lines = the span over the going
    + 1 (a missing line inside the run is counted), width = the median line length."""
    offs = [x[2] for x in part]
    span = max(offs) - min(offs)
    n = int(round(span / going)) + 1
    if n < 3 or abs(span - (n - 1) * going) > 0.25 * going * max(1, n - 1) ** 0.5:
        return None
    widths = sorted(x[1] - x[0] for x in part)
    w = widths[len(widths) // 2]
    return {"kind": "FLIGHT", "n_lines": n, "going_m": going, "width_m": w, "run_m": (n - 1) * going,
            "plan_m2": (n - 1) * going * w, "drawn_lines": len(part), "eids": [x[3]["eid"] for x in part],
            "basis": "parallel tread lines at a regular pitch (a line missing inside the run counted)"}


def _flights(ctx, ents):
    """the stair runs of a group's lines: parallel tread lines split into flights by where they lie along their own
    direction (two flights of a dog-leg sit side by side) and by gaps across it; the lines left over that fan about
    one point are a winder run. -> [stair_measure.flight run]."""
    u = ctx.u
    segs = [e for e in ents if e["type"] == "LINE" and 0.4 <= math.dist(e["a"], e["b"]) * u <= 4.0]
    by_ang = defaultdict(list)
    for e in segs:
        ang = math.degrees(math.atan2(e["b"][1] - e["a"][1], e["b"][0] - e["a"][0])) % 180.0
        by_ang[round(ang / 3.0) % 60].append(e)
    runs, used = [], set()
    for _, g in sorted(by_ang.items(), key=lambda kv: -len(kv[1])):
        if len(g) < 3:
            continue
        dx, dy = g[0]["b"][0] - g[0]["a"][0], g[0]["b"][1] - g[0]["a"][1]
        n = math.hypot(dx, dy)
        ux, uy = dx / n, dy / n
        rec = []
        for e in g:
            s0, s1 = sorted(((e["a"][0] * ux + e["a"][1] * uy) * u, (e["b"][0] * ux + e["b"][1] * uy) * u))
            off = (e["a"][0] * -uy + e["a"][1] * ux) * u
            rec.append((s0, s1, off, e))
        cols = []                                   # lines sharing their along-line extent: one flight's column
        for r in sorted(rec, key=lambda r: (r[0], r[2])):
            for c in cols:
                ov = min(c["s1"], r[1]) - max(c["s0"], r[0])
                if ov >= 0.5 * min(c["s1"] - c["s0"], r[1] - r[0]):
                    c["lines"].append(r)
                    c["s0"], c["s1"] = min(c["s0"], r[0]), max(c["s1"], r[1])
                    break
            else:
                cols.append({"s0": r[0], "s1": r[1], "lines": [r]})
        for c in cols:
            ls = sorted(c["lines"], key=lambda r: r[2])
            gaps = sorted(b[2] - a[2] for a, b in zip(ls, ls[1:]) if PITCH_M[0] <= b[2] - a[2] <= PITCH_M[1])
            if not gaps:
                continue
            going = gaps[len(gaps) // 2]
            part = [ls[0]]
            for r in ls[1:] + [None]:
                # a gap of a whole number of goings is a tread line the drawing does not show (hidden under a member
                # edge); a wider gap starts another flight
                if r is not None and r[2] - part[-1][2] <= 2.5 * going + 1e-6:
                    part.append(r)
                    continue
                if len(part) >= 3:
                    run = _straight_run(part, going)
                    if run:
                        runs.append(run)
                        used.update(x[3]["eid"] for x in part)
                part = [r] if r is not None else []
    rest = [e for e in segs if e["eid"] not in used]
    if len(rest) >= 3:
        run = SM.flight([{"a": e["a"], "b": e["b"]} for e in rest], u, min_lines=3)
        if run and run["kind"] == "WINDER":
            runs.append(dict(run, eids=[e["eid"] for e in rest]))
    return runs


# ====================================================================== measured families
def _item(ctx, f, fam, part, lo, base, hi, formula, assumptions, dims, *, support="CONVENTION_ONLY",
          blocker="SCOPE_FROM_DRAWN_PLAN", double_count="", storey=None):
    st = storey or f.get("STOREY") or "UNKNOWN"
    cid = f"SCOPE:{fam}:{st}:{f['FINDING_ID']}:{part}"
    lo, base, hi = max(lo, 0.0), max(base, 0.0), max(hi, 0.0)
    lo, hi = min(lo, base), max(hi, base)
    return PE.item(item_id=f"P-C:{cid}", component_id=cid, trade="CONCRETE", family=fam, storey=st,
                   category="PROVISIONAL", low=lo, base=base, high=hi, formula=formula,
                   assumptions=sorted(set(assumptions)), support=support, confidence="LOW", blocker=blocker,
                   source=f"{ctx.src} {f['SHEET']} completeness finding {f['FINDING_ID']} ({f['KIND']})",
                   dimensions=dims, double_count_risk=double_count or "the finding's drawn entities are held by no "
                                                                     "other item (completeness pass)")


def _pool(ctx, f, ents):
    conv = ctx.conv
    notes = ctx.notes_near(f, ents)
    t_w, pw = _printed(notes, ("wall", "thickness"), conv, "POOL_WALL_THICKNESS_M")
    geo = _wall_geometry(ctx, f, ents, t_w)
    if not geo or not geo[1]:
        return None
    walls, outer, inner, basis = geo
    H, ph = _printed(notes, ("height",), conv, "POOL_WALL_HEIGHT_M")
    tf, pf = _printed(notes, ("floor",), conv, "POOL_FLOOR_THICKNESS_M")
    asm = ["SCOPE_FROM_FINDINGS"] + ([] if ph else ["POOL_WALL_HEIGHT_M"]) + ([] if pf else ["POOL_FLOOR_THICKNESS_M"])
    if "convention" in basis and not pw:
        asm.append("POOL_WALL_THICKNESS_M")
    if notes:
        asm.append("PRINTED_DIMENSION_NOTES")
    w = _combo(lambda a, h: a * h, walls, H)
    fl = _combo(lambda t: outer * t, tf)
    dims = {"wall_plan_m2": round(walls[1], 4), "outer_m2": round(outer, 4), "inner_m2": round(inner or 0.0, 4),
            "wall_height_m": list(H), "floor_t_m": list(tf), "printed": sorted(notes), "basis": basis}
    sup = "ONE_ASSUMED_DIMENSION" if (ph + pf) == 1 and "convention" not in basis else \
        "SOURCE_COMPLETE_UNREVIEWED" if ph and pf and "convention" not in basis else "CONVENTION_ONLY"
    return [_item(ctx, f, "POOL", "WALLS", *w, "wall plan area x wall height", asm, dims, support=sup),
            _item(ctx, f, "POOL", "FLOOR", *fl, "outer plan area x floor thickness", asm, dims, support=sup)]


def _pit(ctx, f, ents, fam):
    conv = ctx.conv
    notes = ctx.notes_near(f, ents)
    cid_t = "PIT_WALL_THICKNESS_M" if fam == "LIFT" else "TANK_WALL_THICKNESS_M"
    t_w, pw = _printed(notes, ("wall", "thickness"), conv, cid_t)
    geo = _wall_geometry(ctx, f, ents, t_w)
    if not geo or not geo[1]:
        return None
    walls, outer, inner, basis = geo
    out, asm = [], ["SCOPE_FROM_FINDINGS"] + (["PRINTED_DIMENSION_NOTES"] if notes else [])
    if "convention" in basis and not pw:
        asm.append(cid_t)
    if fam == "LIFT":
        H, ph = _printed(notes, ("height",), conv, "PIT_DEPTH_M")
        tb, pb = _printed(notes, ("floor",), conv, "PIT_BASE_THICKNESS_M")
        asm += ([] if ph else ["PIT_DEPTH_M"])
        on_ftg = _inside_footing(ctx, f)
        dims = {"wall_plan_m2": round(walls[1], 4), "outer_m2": round(outer, 4), "wall_height_m": list(H),
                "base_t_m": None if on_ftg else list(tb), "inside_measured_footing": on_ftg, "basis": basis,
                "printed": sorted(notes)}
        out.append(_item(ctx, f, "LIFT", "WALLS", *_combo(lambda a, h: a * h, walls, H), "wall plan area x pit depth",
                         asm, dims))
        if not on_ftg:
            out.append(_item(ctx, f, "LIFT", "BASE", *_combo(lambda t: outer * t, tb), "outer plan area x base "
                             "thickness", asm + ([] if pb else ["PIT_BASE_THICKNESS_M"]), dims))
        return out
    # WATER_TANK
    H, ph = _printed(notes, ("height",), conv, "TANK_HEIGHT_M")
    ts, ps = _printed(notes, ("cover", "floor"), conv, "TANK_SLAB_THICKNESS_M")
    asm += ([] if ph else ["TANK_HEIGHT_M"]) + ([] if ps else ["TANK_SLAB_THICKNESS_M"])
    on_slab = (ctx.sheets.get(f["SHEET"]) or {}).get("role") == "SLAB_PLAN"
    dims = {"wall_plan_m2": round(walls[1], 4), "outer_m2": round(outer, 4), "wall_height_m": list(H),
            "slab_t_m": list(ts), "stands_on_slab": on_slab, "basis": basis, "printed": sorted(notes)}
    out.append(_item(ctx, f, "WATER_TANK", "WALLS", *_combo(lambda a, h: a * h, walls, H), "wall plan area x tank "
                     "height", asm, dims))
    n_slabs = 1 if on_slab else 2
    out.append(_item(ctx, f, "WATER_TANK", "SLABS", *_combo(lambda t: n_slabs * outer * t, ts),
                     "outer plan area x slab thickness (cover" + (")" if on_slab else " and base)"), asm, dims))
    return out


def _dome_geometry(ctx, f, ents):
    """(r_shell m, ring area m2 or 0, centre (local m), basis)."""
    u = ctx.u
    mag = f.get("MAGNITUDE") or {}
    circles = sorted((e for e in ents if e["type"] in ("CIRCLE", "ARC")), key=lambda e: -e["r"])
    box = f.get("BOX_M")
    centre = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2) if box else None
    concentric = []
    if circles:
        c0 = circles[0]
        concentric = [e for e in circles if math.dist(e["c"], c0["c"]) * u <= 0.05 and
                      (e["type"] == "CIRCLE" or e.get("sweep", 0) >= math.pi)]
        org = ctx.org(f["SHEET"])
        centre = ((c0["c"][0] - org[0]) * u, (c0["c"][1] - org[1]) * u)
    rs = sorted({round(e["r"] * u, 4) for e in concentric}, reverse=True)
    if len(rs) >= 2 and 0.05 <= rs[0] - rs[1] <= 0.8:
        return rs[1], math.pi * (rs[0] ** 2 - rs[1] ** 2), centre, \
            f"two concentric circles r {rs[0]:g} / {rs[1]:g} m: ring beam and the shell inside it"
    if mag.get("radial_r_m"):
        return mag["radial_r_m"], 0.0, centre, f"{mag.get('radial_spokes')} ribs radiating to r {mag['radial_r_m']:g} m"
    if rs:
        return rs[0], 0.0, centre, f"circle r {rs[0]:g} m"
    return None


def _dome(ctx, f, ents, rule):
    conv = ctx.conv
    geo = _dome_geometry(ctx, f, ents)
    if not geo or geo[0] <= 0.2:
        return None, None
    r, ring, centre, basis = geo
    notes = ctx.notes_near(f, ents)
    ratio = conv.triple("DOME_RISE_RATIO")
    rise, pr = _printed(notes, ("rise", "height"), conv, "DOME_RISE_RATIO")
    t, pt = _printed(notes, ("shell", "thickness"), conv, "DOME_SHELL_THICKNESS_M")
    hs = rise if pr else tuple(x * r for x in ratio)
    asm = ["SCOPE_FROM_FINDINGS"] + ([rule] if rule else []) + ([] if pr else ["DOME_RISE_RATIO"]) + \
        ([] if pt else ["DOME_SHELL_THICKNESS_M"]) + (["PRINTED_DIMENSION_NOTES"] if notes else [])
    shell = _combo(lambda h, th: math.pi * (r * r + h * h) * th, hs, t)
    dims = {"r_m": round(r, 4), "rise_m": [round(x, 4) for x in hs], "shell_t_m": list(t), "basis": basis,
            "ring_area_m2": round(ring, 4), "printed": sorted(notes)}
    out = [_item(ctx, f, "DOMES", "SHELL", *shell, "spherical cap pi (r^2 + h^2) x shell thickness", asm, dims)]
    if ring > 0:
        d, pd = _printed(notes, ("ring",), conv, "DOME_RING_DEPTH_M")
        out.append(_item(ctx, f, "DOMES", "RING", *_combo(lambda x: ring * x, d), "ring area x ring depth",
                         asm + ([] if pd else ["DOME_RING_DEPTH_M"]), dict(dims, ring_depth_m=list(d))))
    return out, (f["SHEET"], centre, r)


def _stair_flight(ctx, f, ents):
    """-> ([item], (n tread lines, high m3)) or (None, None): every run of the drawing measured (stair_measure), the
    risers of each run by the base riser rule and the alternative one (both readings inside the range)."""
    conv = ctx.conv
    runs = _flights(ctx, ents)
    if not runs:
        return None, None
    notes = ctx.notes_near(f, ents)
    Rt, pr = _printed(notes, ("riser",), conv, "STAIR_RISER_M")
    Wt, pw = _printed(notes, ("waist",), conv, "STAIR_WAIST_CONVENTION_M")
    if not pw and "STAIR_WAIST_M" in conv.items:
        Wt, pw = conv.triple("STAIR_WAIST_M"), True
    base_rule = conv.base("STAIR_RISER_RULE") if "STAIR_RISER_RULE" in conv.items else "LINES_PLUS_ONE"
    rules = [base_rule] + [r_ for r_ in ("LINES_PLUS_ONE", "LINES") if r_ != base_rule]
    lo = base = hi = 0.0
    per = []
    for run in runs:
        vals = []
        for rule in rules:
            n_r = SM.risers(run["n_lines"], rule)
            if n_r < 2:
                continue
            for R in Rt:
                for w in Wt:
                    q = SM.quantities(0.0, run, R * n_r, w, riser_rule=rule)
                    if q["state"] == "MEASURED":
                        vals.append((rule, R, w, q))
        b = next((q for rule, R, w, q in vals if rule == base_rule and R == Rt[1] and w == Wt[1]), None)
        if b is None:
            continue
        tot = [q["total_m3"] for *_, q in vals]
        lo, base, hi = lo + min(tot), base + b["total_m3"], hi + max(tot)
        per.append({"kind": run["kind"], "tread_lines": run["n_lines"], "going_m": round(run["going_m"], 4),
                    "width_m": round(run["width_m"], 4), "risers": b["risers"],
                    "plan_m2": round(b["flight_plan_m2"], 4), "base_m3": round(b["total_m3"], 4)})
    if not per:
        return None, None
    asm = ["SCOPE_FROM_FINDINGS", "STAIR_LOOSE_FLIGHT", "STAIR_RISER_RULE"] + ([] if pr else ["STAIR_RISER_M"]) + \
        ([] if pw else ["STAIR_WAIST_CONVENTION_M"]) + (["PRINTED_DIMENSION_NOTES"] if notes else [])
    n_lines = sum(r["tread_lines"] for r in per)
    dims = {"runs": per, "tread_lines": n_lines, "riser_m": list(Rt), "waist_m": list(Wt), "riser_rules": rules,
            "landing": "landings not drawn as a zone: not measured", "printed": sorted(notes)}
    it = _item(ctx, f, "STAIRS", "FLIGHTS", lo, base, hi,
               "per run: stair_measure (straight: stair_geometry.straight_flight; winder: plan x (waist / cos + R / 2))"
               "; risers by the riser rule, both readings in the range", asm, dims, blocker="STAIR_GEOMETRY_FROM_PLAN")
    return [it], (n_lines, hi)


def _row_section_m(sizes):
    """a schedule row's first two sizes in metres: millimetres when both are >= 100 (200 x 600), else centimetres
    (20 x 60) - a 1.0 x 3.0 m or a 0.02 x 0.06 m member section is never the reading."""
    a, b = float(sizes[0]), float(sizes[1])
    k = 1000.0 if min(a, b) >= 100 else 100.0
    return a / k, b / k


def _boundary(ctx, f, rows):
    mag = f.get("MAGNITUDE") or {}
    w, L = mag.get("strip_width_m"), mag.get("strip_length_m")
    if not (w and L):
        return None, None
    for r in rows:
        sizes = (r.get("MAGNITUDE") or {}).get("sizes") or []
        if len(sizes) < 2:
            continue
        W, H = _row_section_m(sizes)
        if abs(W - w) <= 0.011:
            dims = {"strip_length_m": L, "strip_width_m": w, "row_section_m": [W, H],
                    "schedule_finding": r["FINDING_ID"]}
            v = L * W * H
            return [_item(ctx, f, "BOUNDARY_WALL", "BEAM", v, v, v, "strip length x the schedule row's section",
                          ["SCOPE_FROM_FINDINGS", "BOUNDARY_WALL_ROW_BY_WIDTH"], dims,
                          support="SOURCE_COMPLETE_UNREVIEWED")], r["FINDING_ID"]
    return None, None


# ====================================================================== bounds
def _bound(f, low, high, rule, basis, *, state="BOUNDED", cls=RC, items=()):
    lo, hi = (low, high) if low <= high else (high, low)
    return {"FINDING_ID": f["FINDING_ID"], "KIND": f["KIND"], "FAMILY": f["FAMILY"], "SHEET": f.get("SHEET") or "",
            "STOREY": f.get("STOREY") or "", "SCOPE_STATE": state, "CLASS": cls, "LOW_M3": round(lo, 4),
            "HIGH_M3": round(hi, 4), "RULE": rule, "BASIS": basis, "ITEMS": ",".join(items)[:300]}


def _stair_high(conv, plan_m2):
    w = conv.triple("STAIR_WAIST_CONVENTION_M")[2] if "STAIR_WAIST_CONVENTION_M" in conv.items else 0.2
    R = conv.triple("STAIR_RISER_M")[2] if "STAIR_RISER_M" in conv.items else 0.18
    return plan_m2 * (w / math.cos(math.radians(40.0)) + R / 2.0)


def _shape_bound(ctx, f, cands):
    """0 .. high by the group's shape (and the candidate families it could be)."""
    conv = ctx.conv
    mag = f.get("MAGNITUDE") or {}
    shape = _shape(f)
    sh = _t(conv, "SLAB_THICKNESS_EXPOSURE_M")[2]
    walls_h = max(_t(conv, "PIT_DEPTH_M")[2], _t(conv, "TANK_HEIGHT_M")[2], _t(conv, "POOL_WALL_HEIGHT_M")[2])
    highs = []
    if mag.get("radial_r_m"):
        r = mag["radial_r_m"]
        dh = math.pi * (r * r + (conv.triple("DOME_RISE_RATIO")[2] * r) ** 2) * conv.triple("DOME_SHELL_THICKNESS_M")[2]
        highs += [(dh, f"a dome of r {r:g} m at the high rise and shell"),
                  (_stair_high(conv, math.pi * r * r), f"a winder stair over the {r:g} m circle")]
    if mag.get("pit"):
        a = mag.get("inner_area_m2") or mag.get("area_m2") or 0.0
        per = 4 * math.sqrt(max(a, 0.0))
        t = max(conv.triple("PIT_WALL_THICKNESS_M")[2], conv.triple("TANK_WALL_THICKNESS_M")[2])
        outer = (math.sqrt(a) + 2 * t) ** 2
        highs.append(((per + 4 * t) * t * walls_h + 2 * outer * conv.triple("TANK_SLAB_THICKNESS_M")[2],
                      "a pit / tank of the drawn size at the highest wall height with base and cover"))
    if shape == "STRIP" and mag.get("strip_width_m"):
        highs.append((mag["strip_length_m"] * mag["strip_width_m"] * conv.triple("UNEXPLAINED_STRIP_DEPTH_M")[2],
                      "strip length x drawn width x UNEXPLAINED_STRIP_DEPTH_M high"))
    if shape == "RING" and mag.get("ring_area_m2"):
        slab_hi = max(conv.triple("TANK_SLAB_THICKNESS_M")[2], conv.triple("POOL_FLOOR_THICKNESS_M")[2],
                      conv.triple("PIT_BASE_THICKNESS_M")[2])
        highs.append((mag["ring_area_m2"] * walls_h + 2 * (mag.get("outer_area_m2") or 0.0) * slab_hi,
                      "ring area x the highest wall height + base and cover (pool / pit / tank)"))
    rs = sorted(mag.get("radii_m") or [], reverse=True)
    if rs and (mag.get("n_circles") or 0) >= 1:
        r_o = rs[0]
        r_i = rs[1] if len(rs) >= 2 and rs[0] - rs[1] <= 0.8 else r_o
        cap = math.pi * (r_i * r_i + (conv.triple("DOME_RISE_RATIO")[2] * r_i) ** 2) * \
            conv.triple("DOME_SHELL_THICKNESS_M")[2]
        ring = math.pi * (r_o * r_o - r_i * r_i) * conv.triple("DOME_RING_DEPTH_M")[2]
        highs.append((cap + ring, f"a round element of r {r_o:g} m: a dome (cap and ring) at the high values"))
    if shape in ("CLOSED_AREA", "HATCH_REGION") or mag.get("area_m2") or mag.get("hatch_area_m2"):
        a = mag.get("area_m2") or mag.get("hatch_area_m2") or mag.get("outer_area_m2") or 0.0
        pb = ctx.plan_box(f["SHEET"])
        box = f.get("BOX_M")
        if pb and box and box[0] - 0.5 <= pb[0] and box[1] - 0.5 <= pb[1] and pb[2] <= box[2] + 0.5 and \
                pb[3] <= box[3] + 0.5:
            return 0.0, (f"a closed outline of {a:.0f} m2 round every measured slab face of the plan: a plot / "
                         "boundary line, not a slab region")
        highs.append((a * sh, "plan area x SLAB_THICKNESS_EXPOSURE_M high"))
    if mag.get("n_treads") and mag.get("going_m"):
        w = mag.get("strip_length_m") or 1.2
        highs.append((_stair_high(conv, mag["n_treads"] * mag["going_m"] * min(w, 2.5)), "a flight of the drawn treads"))
    if mag.get("linework_m"):
        highs.append((mag["linework_m"] / 2.0 * conv.triple("UNEXPLAINED_LINEWORK_SECTION_M2")[2],
                      "half the linework x UNEXPLAINED_LINEWORK_SECTION_M2 high"))
    if not highs:
        return None
    hi, why = max(highs)
    return hi, why + (f" (could be {' or '.join(cands)})" if cands else "")


def _free_roof_edge_m(ctx, sid, step_m=0.25):
    """the free edge length of a slab plan: the outer outline of its members (raster of step_m cells; holes inside the
    plan - wells, openings - never count) where the plan above does not cover it."""
    D, u = ctx.D, ctx.u
    rec = D["sheets"].get(sid)
    if not rec:
        return 0.0
    st = rec["sheet"].get("storey")
    above = [s for s, r in D["sheets"].items() if r["sheet"]["role"] == "SLAB_PLAN" and
             r["sheet"].get("storey") in STOREY_ORDER and st in STOREY_ORDER and
             STOREY_ORDER.index(r["sheet"]["storey"]) == STOREY_ORDER.index(st) + 1]

    def cells(s):
        org = ctx.org(s)
        polys = [[((x - org[0]) * u, (y - org[1]) * u) for x, y in m["poly"]] for m in ctx.members.get(s, [])
                 if m["kind"] in ("FACE", "BAND", "COLUMN", "COLUMN_BOX") and
                 (m["kind"] != "FACE" or m.get("cls") in ("PANEL", "OPEN_BOUNDARY", None))]
        out = set()
        for p in polys:
            b = CC._bbox(p)
            for i in range(int(math.floor(b[0] / step_m)), int(math.ceil(b[2] / step_m))):
                for j in range(int(math.floor(b[1] / step_m)), int(math.ceil(b[3] / step_m))):
                    if MD.point_in_poly((i + 0.5) * step_m, (j + 0.5) * step_m, p):
                        out.add((i, j))
        return out
    here = cells(sid)
    if not here:
        return 0.0
    up = set()
    for s in above:
        up |= cells(s)
    i0, i1 = min(i for i, _ in here) - 1, max(i for i, _ in here) + 1
    j0, j1 = min(j for _, j in here) - 1, max(j for _, j in here) + 1
    ext, stack = set(), [(i0, j0)]
    while stack:                                   # the empty cells outside the plan (holes inside never count)
        q = stack.pop()
        if q in ext or q in here or not (i0 <= q[0] <= i1 and j0 <= q[1] <= j1):
            continue
        ext.add(q)
        stack.extend(((q[0] + 1, q[1]), (q[0] - 1, q[1]), (q[0], q[1] + 1), (q[0], q[1] - 1)))
    n = 0
    for i, j in here:
        if (i, j) in up:
            continue
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (i + di, j + dj)
            if q in ext and q not in up:
                n += 1
    return n * step_m


# ====================================================================== the pass
def measure(CR, D, items, conv, *, scan=None, src_file=""):
    if not enabled(conv):
        raise ScopeError("scope_quantities needs conventions with SCOPE_FROM_FINDINGS (V6)")
    ctx = _Ctx(CR, D, items, conv, scan, src_file)
    new, reg, bounds, risk = [], [], {}, []
    findings = CR["findings"]
    by_kind = defaultdict(list)
    for f in findings:
        by_kind[f["KIND"]].append(f)
    route_fams = Counter(i["family"] for i in items if i["trade"] == "CONCRETE")
    rows_bw = [f for f in by_kind.get("SCHEDULE_ROW_UNREAD", ()) if f["FAMILY"] == "BOUNDARY_WALL"]
    used_rows = set()
    domes = []                                     # (sheet, centre, r) measured
    flights = []                                   # (finding, box, n_treads, high) measured loose flights
    route_stairs = []
    for i in items:
        if i["trade"] == "CONCRETE" and i["family"] == "STAIRS" and i["category"] != "UNRESOLVED":
            face = i["component_id"].split(":")[-1]
            for sid, rec in D["sheets"].items():
                for fc in ((rec.get("slab") or {}).get("faces") or []):
                    if fc["face_id"] == face:
                        route_stairs.append((sid, CC._local_box(CC._bbox(fc["polygon"]), ctx.org(sid), ctx.u),
                                             i["item_id"], i["dimensions"].get("tread_lines") or 0))

    def add(f, its, state="MEASURED", rule="", basis=""):
        new.extend(its)
        for it in its:
            reg.append({"COMPONENT_ID": it["component_id"], "FAMILY": it["family"], "STOREY": it["storey"],
                        "REBAR_STATE": "MISSING_DATA", "PROVISIONAL_KG_BASE": None,
                        "REASON": f"{it['family'].lower()} bars need the element's bar details (never a kg/m3 "
                                  "ratio)"})
        lo = sum(it["low"] for it in its)
        hi = sum(it["high"] for it in its)
        bounds[f["FINDING_ID"]] = _bound(f, lo, hi, rule or "MEASURED", basis or "the items' own range",
                                         state=state, items=[it["item_id"] for it in its])

    # ---- pass 1: settled families measured from their drawn geometry
    order = sorted(findings, key=lambda f: (STOREY_ORDER.index(f["STOREY"]) if f.get("STOREY") in STOREY_ORDER
                                            else 99, f["FINDING_ID"]))
    for f in order:
        kind, fam = f["KIND"], f["FAMILY"]
        if kind not in ("DRAWN_NOT_MEASURED", "STAIR_NOT_MEASURED"):
            continue
        if _non_structural(f, conv):
            bounds[f["FINDING_ID"]] = _bound(f, 0.0, 0.0, "NON_STRUCTURAL_LAYERS",
                                             f"drawn on the non-structural layer {_layer(f)} (furniture / fixtures / "
                                             "services / landscape): not concrete", state="QUALIFIER")
            continue
        ents = ctx.group(f)
        mag = f.get("MAGNITUDE") or {}
        shape = _shape(f)
        cands = _candidates(f)
        try:
            if fam == "POOL" and _settled(f):
                its = _pool(ctx, f, ents)
                if its:
                    add(f, its, basis="pool walls and floor from the drawn plan")
                    continue
            if mag.get("pit") and fam in ("LIFT", "WATER_TANK") and _settled(f):
                its = _pit(ctx, f, ents, fam)
                if its:
                    add(f, its, basis=f"{fam.lower()} from the drawn walls")
                    continue
            if fam == "WATER_TANK" and _settled(f) and not mag.get("pit"):
                its = _pit(ctx, f, ents, "WATER_TANK")
                if its:
                    add(f, its, basis="tank walls and slabs from the drawn plan")
                    continue
            if fam == "LIFT" and _settled(f) and not mag.get("pit"):
                its = _pit(ctx, f, ents, "LIFT")
                if its:
                    add(f, its, basis="lift pit / shaft walls from the drawn plan")
                    continue
            dome_rule = None
            if fam == "DOMES" and _settled(f):
                dome_rule = ""
            elif (shape in ("RADIAL", "RING") or mag.get("radial_spokes")) and f.get("STOREY") == ctx.top and \
                    "DOMES" in ctx.referenced and (fam in ("UNKNOWN", "DOMES") and (not cands or "DOMES" in cands)):
                dome_rule = "DOME_ON_TOP_PLAN"
            if dome_rule is not None:
                its, key = _dome(ctx, f, ents, dome_rule)
                if its:
                    dup = next((d for d in domes if d[0] == key[0] and key[1] and d[1] and
                                math.dist(d[1], key[1]) <= 0.1 * max(key[2], 0.5) and abs(d[2] - key[2]) <= 0.1 *
                                key[2]), None)
                    if dup:
                        bounds[f["FINDING_ID"]] = _bound(f, 0.0, 0.0, "DOME_SAME_CENTRE", "the same dome as another "
                                                         "finding (same centre and radius): measured once",
                                                         state="EXPLAINED")
                        continue
                    domes.append(key)
                    add(f, its, rule=dome_rule or "MEASURED", basis="dome shell (and ring) from the drawn plan")
                    continue
            if fam == "BOUNDARY_WALL" and _settled(f) and "BOUNDARY_WALL_ROW_BY_WIDTH" in conv.items:
                its, row = _boundary(ctx, f, [r for r in rows_bw if r["FINDING_ID"] not in used_rows])
                if its:
                    used_rows.add(row)
                    add(f, its, rule="BOUNDARY_WALL_ROW_BY_WIDTH", basis="strip length x the family's schedule "
                                                                          "row section")
                    continue
        except (PE.EstimateError, ZeroDivisionError, ValueError) as e:
            risk.append({"KIND": "SCOPE_MEASURE_FAILED", "WHERE": f.get("SHEET") or "",
                         "DETAIL": f"{f['FINDING_ID']} {fam}: {type(e).__name__}: {str(e)[:120]} - bounded instead"})
    # ---- stairs: every settled flight drawing measured, the drawing with more tread lines first; a drawing at the
    # place of another (a route stair zone or a measured flight) on another plan is the same flight (exposure only)
    cand = []
    for f in order:
        if f["KIND"] in ("DRAWN_NOT_MEASURED", "STAIR_NOT_MEASURED") and f["FAMILY"] == "STAIRS" and _settled(f) and \
                f["FINDING_ID"] not in bounds:
            try:
                its, key = _stair_flight(ctx, f, ctx.group(f))
            except (PE.EstimateError, ZeroDivisionError, ValueError) as e:
                risk.append({"KIND": "SCOPE_MEASURE_FAILED", "WHERE": f.get("SHEET") or "",
                             "DETAIL": f"{f['FINDING_ID']} STAIRS: {type(e).__name__}: {str(e)[:120]} - bounded"})
                continue
            if its:
                cand.append((key[0], f, its, key[1]))
    for n, f, its, hi in sorted(cand, key=lambda x: (-x[0], x[1]["FINDING_ID"])):
        box = f.get("BOX_M")
        same = None
        if box:
            same = next((("a stair zone measured by the route", iid) for sid2, b2, iid, _ in route_stairs
                         if b2 and _iou(box, b2) >= 0.3), None) or \
                next((("a measured flight", g["FINDING_ID"]) for g, b2, _, _ in flights
                      if b2 and _iou(box, b2) >= 0.3 and g.get("STOREY") != f.get("STOREY")), None)
        if same and conv.base("STAIR_FLIGHT_ON_TWO_PLANS") == "SAME_FLIGHT_ONCE":
            bounds[f["FINDING_ID"]] = _bound(f, 0.0, hi, "STAIR_FLIGHT_ON_TWO_PLANS",
                                             f"drawn at the place of {same[0]} ({same[1]}) on another plan: the same "
                                             "flight, measured once; this drawing's own volume is the exposure "
                                             "(stacked flights)")
            continue
        flights.append((f, box, n, hi))
        add(f, its, basis=f"{len(its[0]['dimensions']['runs'])} drawn run(s), {n} tread lines")
    measured_fams = Counter(it["family"] for it in new) + route_fams

    # ---- pass 2: every remaining finding bounded by its kind and shape
    for f in findings:
        if f["FINDING_ID"] in bounds:
            continue
        b = _bound_of(ctx, f, measured_fams, used_rows)
        bounds[f["FINDING_ID"]] = b
    out_f = []
    for f in findings:
        b = bounds[f["FINDING_ID"]]
        out_f.append(dict(f, SCOPE_STATE=b["SCOPE_STATE"], SCOPE_LOW_M3=b["LOW_M3"], SCOPE_HIGH_M3=b["HIGH_M3"],
                          SCOPE_RULE=b["RULE"], SCOPE_ITEMS=b["ITEMS"]))
    blist = [bounds[f["FINDING_ID"]] for f in findings]
    # route items held UNRESOLVED with no exposure range: 0 .. the largest measured member of the family (storey)
    for i in items:
        if i["trade"] != "CONCRETE" or i["category"] != "UNRESOLVED" or i.get("exposure_high") is not None:
            continue
        same = [j.get("base") or 0.0 for j in items if j["trade"] == "CONCRETE" and j["family"] == i["family"] and
                j["category"] != "UNRESOLVED"]
        st = [j.get("base") or 0.0 for j in items if j["trade"] == "CONCRETE" and j["family"] == i["family"] and
              j["category"] != "UNRESOLVED" and j["storey"] == i["storey"]]
        hi = max(st or same or [0.0])
        pseudo = {"FINDING_ID": "ITEM:" + i["item_id"], "KIND": "UNRESOLVED_ITEM_WITHOUT_EXPOSURE",
                  "FAMILY": i["family"], "SHEET": "", "STOREY": i["storey"]}
        blist.append(_bound(pseudo, 0.0, hi, "UNRESOLVED_ITEM_WITHOUT_EXPOSURE",
                            f"{i['blocker']}: 0 .. the largest measured {i['family']} member "
                            + ("of its storey" if st else "of the set"), items=[i["item_id"]]))
    return {"policy": POLICY_ID, "items": new, "register": reg, "bounds": blist, "risk": risk, "findings": out_f,
            "top_storey": ctx.top, "referenced": sorted(ctx.referenced),
            "rule": "settled families measured from drawn geometry x printed values / named conventions; every other "
                    "finding bounded by its kind and shape; no ratio; nothing added twice"}


def _bound_of(ctx, f, measured_fams, used_rows):
    conv = ctx.conv
    kind, fam = f["KIND"], f["FAMILY"]
    mag = f.get("MAGNITUDE") or {}
    vlo, vhi = f.get("VOLUME_LOW_M3"), f.get("VOLUME_HIGH_M3")
    rule = BOUND_RULES.get(kind, "")
    sh = _t(conv, "SLAB_THICKNESS_EXPOSURE_M")
    if kind == "UNRESOLVED_ITEMS":
        return _bound(f, 0.0, 0.0, "HELD_BY_ITEMS", "the items' own exposure, counted once with the items",
                      state="HELD_BY_ITEMS", items=(f.get("ITEMS") or "").split(","))
    if kind in ("DEPENDENCY", "SLAB_COVERAGE_LOW", "MEMBER_OUTLINE_SUSPECT", "STOREY_COLUMN_BANDS_MISSING",
                "STOREY_HEIGHT_MISSING"):
        return _bound(f, 0.0, 0.0, "QUALIFIER", rule, state="QUALIFIER")
    if kind == "SCHEDULE_ROW_UNREAD" and f["FINDING_ID"] in used_rows:
        return _bound(f, 0.0, 0.0, "BOUNDARY_WALL_ROW_BY_WIDTH", "the row's section measures the boundary-wall strip",
                      state="EXPLAINED")
    if kind == "REGION_EXCLUDED":
        a = mag.get("area_m2") or 0.0
        t_hi = max(sh[2], (vhi / a) if (vhi and a) else 0.0)
        return _bound(f, 0.0, a * t_hi, kind, rule)
    if kind == "OPENING_NOT_DEDUCTED":
        return _bound(f, -(vhi or 0.0), 0.0, kind, rule)
    if kind == "COLUMN_PRESENCE_NOT_ITEMIZED":
        return _bound(f, 0.0, vhi or 0.0, kind, rule)
    if kind == "COLUMN_ITEM_WITHOUT_PRESENCE":
        return _bound(f, -(vhi or 0.0), 0.0, kind, rule)
    if kind == "COLUMN_BAND_NOT_ON_PLAN":
        st = f.get("STOREY")
        vmax = max([i.get("base") or 0.0 for i in ctx.items if i["trade"] == "CONCRETE" and i["family"] == "COLUMNS"
                    and i["storey"] == st and i["category"] != "UNRESOLVED"] or [0.0])
        return _bound(f, 0.0, (mag.get("occurrences") or 0) * vmax, kind, rule)
    if kind == "MEMBER_DETECTED_NOT_ITEMIZED":
        a = mag.get("plan_area_m2") or 0.0
        if fam == "FOOTINGS":
            ds = [_dims(r).get("D") for r in _lib_rows(ctx, "FOOTING") if _dims(r).get("D")]
            d = max(ds) if ds else 1.0
        elif fam == "GROUND_BEAMS":
            d = _t(conv, "GB_DEPTH_EXPOSURE_M")[2]
        else:
            d = _t(conv, "UNTAGGED_BEAM_DEPTH_RANGE_M")[2]
        return _bound(f, 0.0, a * d, kind, rule + f" (depth {d:g} m)")
    if kind in ("SCHEDULED_NOT_PLACED", "SCHEDULE_ROW_UNREAD"):
        W, H, Dp = mag.get("W"), mag.get("H"), mag.get("D")
        sizes = mag.get("sizes") or []
        if W is None and len(sizes) >= 2:
            W, H = _row_section_m(sizes)
        if W and H and Dp:
            return _bound(f, 0.0, W * H * Dp, kind, rule + " (one footing)")
        if W and H:
            L = ctx.beam_len_max or 6.0
            return _bound(f, 0.0, W * H * L, kind, rule + f" (W x H x {L:g} m)")
        return _bound(f, 0.0, conv.triple("REFERENCED_ELEMENT_ALLOWANCE_M3")[2], kind,
                      "0 .. REFERENCED_ELEMENT_ALLOWANCE_M3 high (no sizes read)")
    if kind in ("LABEL_NOT_CONSUMED", "PLACED_NOT_SCHEDULED"):
        hi = _one_member(ctx, f)
        return _bound(f, 0.0, hi, kind, rule)
    if kind == "LABEL_MEMBER_CONFLICT":
        lo, hi = _label_conflict(ctx, f)
        return _bound(f, lo, hi, kind, rule)
    if kind == "MEMBER_OVERLAP":
        a = mag.get("overlap_m2") or 0.0
        d = _t(conv, "GB_DEPTH_EXPOSURE_M")[2] if fam == "GROUND_BEAMS" else _t(conv, "UNTAGGED_BEAM_DEPTH_RANGE_M")[2]
        return _bound(f, -a * d, 0.0, kind, rule + f" (depth {d:g} m)")
    if kind == "HATCH_ON_MEASURED_MEMBER":
        a = mag.get("hatch_area_m2") or 0.0
        t = _host_thickness(ctx, f) or sh[2]
        return _bound(f, -a * t, 0.0, kind, rule + f" (thickness {t:g} m)")
    if kind in ("STOREY_PLAN_MISSING", "PLAN_SHEET_NOT_MEASURED"):
        st = f.get("STOREY")
        if st in STOREY_ORDER:
            k = STOREY_ORDER.index(st)
            nb = [ctx.storey_rcv[s] for s in STOREY_ORDER[max(0, k - 1):k + 2] if s != st and ctx.storey_rcv.get(s)]
            if len(nb) >= 2:
                return _bound(f, min(nb), max(nb), kind, rule)
            if nb:
                return _bound(f, 0.5 * nb[0], nb[0], kind, rule)
        return _bound(f, 0.0, max(ctx.storey_rcv.values() or [0.0]), kind, rule + " (no neighbour: 0 .. the largest "
                                                                                  "storey)")
    if kind == "REFERENCED_NOT_DRAWN":
        if measured_fams.get(fam):
            return _bound(f, 0.0, 0.0, "EXPLAINED", f"the {fam} family is measured", state="EXPLAINED")
        drawn = next((g for g in ctx.CR["findings"] if g["KIND"] in ("DRAWN_NOT_MEASURED", "STAIR_NOT_MEASURED") and
                      (g["FAMILY"] == fam or fam in _candidates(g) or
                       re.search(r"notes: [A-Z_, ]*\b" + fam + r"\b", g.get("EVIDENCE") or ""))), None)
        if drawn:
            return _bound(f, 0.0, 0.0, "EXPLAINED", f"the {fam} the notes name may be the drawn group "
                                                    f"{drawn['FINDING_ID']} (bounded there): never counted twice",
                          state="EXPLAINED")
        return _reference_allowance(ctx, f)
    if kind == "STAIR_NOT_MEASURED":
        a = mag.get("area_m2") or ((mag.get("n_treads") or 0) * (mag.get("going_m") or 0) *
                                   min(mag.get("strip_length_m") or 1.2, 2.5))
        return _bound(f, 0.0, _stair_high(conv, a), kind, rule)
    if kind == "DRAWN_NOT_MEASURED":
        if mag.get("hatch_area_m2") and not mag.get("linework_m") and "round the whole plan" in (f.get("EVIDENCE") or
                                                                                                 ""):
            t = _t(conv, "BLINDING_THICKNESS_EXPOSURE_M")[2]
            return _bound(f, 0.0, mag["hatch_area_m2"] * t, "SITE_FILL", "a fill round the whole plan: plain concrete "
                                                                          f"0 .. area x {t:g} m (blinding high)",
                          cls=PLAIN)
        if fam == "SLAB_STEP":
            a = mag.get("area_m2") or mag.get("outer_area_m2") or 0.0
            per = 4 * math.sqrt(a) if a else (mag.get("linework_m") or 0.0)
            hi = per * conv.triple("SLAB_STEP_DROP_M")[2] * sh[2]
            return _bound(f, 0.0, hi, "SLAB_STEP_DROP_M", "a sunken outline: perimeter x drop x slab thickness, 0 .. "
                                                          "high")
        if fam == "BOUNDARY_WALL" and mag.get("strip_length_m"):
            hi = mag["strip_length_m"] * conv.triple("BOUNDARY_WALL_RC_SECTION_M2")[2]
            return _bound(f, 0.0, hi, "BOUNDARY_WALL_RC_SECTION_M2", "strip length x the RC section high (no row of "
                                                                     "its width)")
        r = _shape_bound(ctx, f, _candidates(f))
        if r:
            return _bound(f, 0.0, r[0], kind, r[1])
    if vhi is not None:
        return _bound(f, 0.0, vhi, kind, "the finding's own volume (0 .. its high)")
    return _bound(f, 0.0, 0.0, "NO_RANGE", "no rule gives this finding a range", state="QUALIFIER")


def _lib_rows(ctx, fam):
    out = []
    for (f, _), row in (ctx.lib or {}).items():
        if f == fam and row:
            out.append(row)
    return out


def _dims(row, storey=None):
    """a schedule row's section in metres ({W, H, D, ...}); a per-storey row gives that storey's, else the largest."""
    if not row:
        return {}
    d = dict(row.get("dims_m") or {})
    bs = row.get("by_storey") or {}
    if storey and (bs.get(storey) or {}).get("dims_m"):
        d.update(bs[storey]["dims_m"])
    elif not d:
        for v in bs.values():
            for k, x in (v.get("dims_m") or {}).items():
                if isinstance(x, (int, float)):
                    d[k] = max(d.get(k, 0.0), x)
    return d


def _one_member(ctx, f):
    conv = ctx.conv
    fam = f["FAMILY"]
    mark = None
    m = re.search(r"label (\S+)", f.get("EVIDENCE") or "")
    if m:
        mark = m.group(1)
    rowfam = {"BEAMS": ("BEAM", "CONTINUOUS_BEAM", "LINTEL"), "COLUMNS": ("COLUMN",), "FOOTINGS": ("FOOTING",),
              "GROUND_BEAMS": ("GROUND_BEAM", "STRAP_BEAM")}.get(fam, ())
    rows = [row for (rf, mk), row in (ctx.lib or {}).items() if row and rf in rowfam and (mark is None or mk == mark)]
    hs = [h for h in (ctx.conv.base(k) for k in conv.items if k.startswith("STOREY_HEIGHT_")) if isinstance(h, float)]
    hmax = max(hs) if hs else 3.5
    L = ctx.beam_len_max or 6.0
    vals = []
    for row in rows:
        d = _dims(row)
        W, H, Dp = d.get("W") or d.get("B"), d.get("H"), d.get("D")
        if fam == "FOOTINGS" and W and H and Dp:
            vals.append(W * H * Dp)
        elif fam == "COLUMNS" and W and H:
            vals.append(W * H * hmax)
        elif W and H:
            vals.append(W * H * L)
    if vals:
        return max(vals)
    if fam == "COLUMNS":
        return 0.3 * 0.6 * hmax
    if fam in ("BEAMS", "GROUND_BEAMS"):
        return 0.3 * _t(conv, "UNTAGGED_BEAM_DEPTH_RANGE_M")[2] * L
    return conv.triple("REFERENCED_ELEMENT_ALLOWANCE_M3")[2]


def _label_conflict(ctx, f):
    m = re.search(r"label (\S+) .*on band (\S+) measured as (\S+)", f.get("EVIDENCE") or "")
    if not m:
        return 0.0, 0.0
    label, band, measured = m.group(1), m.group(2), m.group(3)
    it = next((i for i in ctx.items if i["trade"] == "CONCRETE" and i["category"] != "UNRESOLVED" and
               i["component_id"].endswith(":" + band)), None)
    if not it:
        return 0.0, 0.0
    v = it.get("base") or 0.0
    sec = {}
    for (rf, mk), row in (ctx.lib or {}).items():
        if row and mk in (label, measured) and rf in ("BEAM", "CONTINUOUS_BEAM", "GROUND_BEAM", "STRAP_BEAM"):
            d = _dims(row)
            W, H = d.get("W") or d.get("B"), d.get("H")
            if W and H:
                sec[mk] = W * H
    if label in sec and measured in sec and sec[measured] > 0:
        d = v * (sec[label] / sec[measured] - 1.0)
        return min(d, 0.0), max(d, 0.0)
    return -v, v


def _host_thickness(ctx, f):
    host = (f.get("MAGNITUDE") or {}).get("host")
    if not host:
        return None
    for i in ctx.items:
        if i["trade"] == "CONCRETE" and i["category"] != "UNRESOLVED" and i["component_id"].endswith(":" + host):
            d = i.get("dimensions") or {}
            return d.get("t_m") or d.get("depth_m")
    return None


def _reference_allowance(ctx, f):
    conv = ctx.conv
    fam = f["FAMILY"]
    if fam == "PARAPETS":
        sheets = [s for s in (f.get("SHEET") or "").split(",") if s in ctx.D["sheets"] and
                  ctx.D["sheets"][s]["sheet"]["role"] == "SLAB_PLAN"]
        L = sum(_free_roof_edge_m(ctx, s) for s in sheets)
        h, t = conv.triple("PARAPET_HEIGHT_M"), conv.triple("PARAPET_THICKNESS_M")
        return _bound(f, 0.0, L * h[2] * t[2], "PARAPET_HEIGHT_M",
                      f"free roof edge {L:.1f} m of the noted plans ({', '.join(sheets) or 'none'}) x parapet height "
                      f"{h[2]:g} m x thickness {t[2]:g} m (high); 0 low (a block parapet)")
    if fam == "WATER_TANK":
        s = conv.triple("TANK_REFERENCED_SIDE_M")[2]
        H, tw, ts = conv.triple("TANK_HEIGHT_M")[2], conv.triple("TANK_WALL_THICKNESS_M")[2], \
            conv.triple("TANK_SLAB_THICKNESS_M")[2]
        hi = 4 * (s + tw) * tw * H + 2 * (s + 2 * tw) ** 2 * ts
        return _bound(f, 0.0, hi, "TANK_REFERENCED_SIDE_M", f"an RC tank {s:g} m square, {H:g} m high, walls {tw:g} "
                                                            f"m, base and cover {ts:g} m (high); 0 low (a GRP tank)")
    if fam == "LIFT":
        s = conv.triple("PIT_REFERENCED_SIDE_M")[2]
        H, tw, tb = conv.triple("PIT_DEPTH_M")[2], conv.triple("PIT_WALL_THICKNESS_M")[2], \
            conv.triple("PIT_BASE_THICKNESS_M")[2]
        hi = 4 * (s + tw) * tw * H + (s + 2 * tw) ** 2 * tb
        return _bound(f, 0.0, hi, "PIT_REFERENCED_SIDE_M", f"a lift pit {s:g} m square, {H:g} m deep (high)")
    if fam == "POOL":
        a = conv.triple("POOL_REFERENCED_AREA_M2")[2]
        H, tw, tf = conv.triple("POOL_WALL_HEIGHT_M")[2], conv.triple("POOL_WALL_THICKNESS_M")[2], \
            conv.triple("POOL_FLOOR_THICKNESS_M")[2]
        hi = 4 * math.sqrt(a) * tw * H + a * tf
        return _bound(f, 0.0, hi, "POOL_REFERENCED_AREA_M2", f"a pool of {a:g} m2 (high)")
    if fam == "DOMES":
        r = conv.triple("DOME_REFERENCED_RADIUS_M")[2]
        hi = math.pi * (r * r + (conv.triple("DOME_RISE_RATIO")[2] * r) ** 2) * conv.triple("DOME_SHELL_THICKNESS_M")[2]
        return _bound(f, 0.0, hi, "DOME_REFERENCED_RADIUS_M", f"a dome of r {r:g} m (high)")
    return _bound(f, 0.0, conv.triple("REFERENCED_ELEMENT_ALLOWANCE_M3")[2], "REFERENCED_ELEMENT_ALLOWANCE_M3",
                  "one small RC element (high)")


# ====================================================================== totals (BOQ section F)
def totals(items, bounds, findings=None):
    rc = [i for i in items if i["trade"] == "CONCRETE" and i["family"] != "PLAIN_CONCRETE"]
    pc = [i for i in items if i["trade"] == "CONCRETE" and i["family"] == "PLAIN_CONCRETE"]

    def side(its, cls):
        m_lo = sum((i["low"] if i["category"] == "PROVISIONAL" else i["base"]) for i in its
                   if i["category"] in ("PROVISIONAL", "VERIFIED"))
        m_b = sum(i["base"] for i in its if i["category"] in ("PROVISIONAL", "VERIFIED"))
        m_hi = sum((i["high"] if i["category"] == "PROVISIONAL" else i["base"]) for i in its
                   if i["category"] in ("PROVISIONAL", "VERIFIED"))
        e_lo = sum(i.get("exposure_low") or 0.0 for i in its if i["category"] == "UNRESOLVED")
        e_hi = sum(i.get("exposure_high") or 0.0 for i in its if i["category"] == "UNRESOLVED")
        n_noexp = sum(1 for i in its if i["category"] == "UNRESOLVED" and i.get("exposure_high") is None)
        bs = [b for b in bounds if b["CLASS"] == cls and b["SCOPE_STATE"] == "BOUNDED"]
        b_lo, b_hi = sum(b["LOW_M3"] for b in bs), sum(b["HIGH_M3"] for b in bs)
        return {"measured_low": round(m_lo, 3), "measured_base": round(m_b, 3), "measured_high": round(m_hi, 3),
                "unresolved_exposure_low": round(e_lo, 3), "unresolved_exposure_high": round(e_hi, 3),
                "unresolved_items_without_exposure": n_noexp,
                "finding_bounds_low": round(b_lo, 3), "finding_bounds_high": round(b_hi, 3),
                "bounded_low": round(m_lo + e_lo + b_lo, 3), "bounded_high": round(m_hi + e_hi + b_hi, 3),
                "n_bounds": len(bs)}
    st = Counter(b["SCOPE_STATE"] for b in bounds)
    no_range = [b["FINDING_ID"] for b in bounds if b["RULE"] == "NO_RANGE"]
    return {"RC": side(rc, RC), "PLAIN": side(pc, PLAIN), "finding_states": dict(sorted(st.items())),
            "findings": len(bounds), "findings_without_range": len(no_range), "without_range_ids": no_range[:20],
            "rule": "bounded = measured (planning) + every UNRESOLVED item's exposure + every bounded finding, low and "
                    "high; HELD_BY_ITEMS / EXPLAINED / QUALIFIER findings add nothing; MEASURED findings are in the "
                    "measured total through their items"}


def boq_lines(T, bounds):
    """BOQ section F: the bounded total, then one line per bounded finding."""
    rc, pc = T["RC"], T["PLAIN"]
    out = [{"ITEM": "F.000", "SECTION": "F BOUNDED TOTAL (MEASURED + EVERY EXPOSURE)", "FAMILY": "RC", "UNIT": "m3",
            "DESCRIPTION": f"reinforced concrete: measured {rc['measured_low']:.2f} / {rc['measured_base']:.2f} / "
                           f"{rc['measured_high']:.2f}; unresolved items {rc['unresolved_exposure_low']:.2f} .. "
                           f"{rc['unresolved_exposure_high']:.2f}; findings {rc['finding_bounds_low']:.2f} .. "
                           f"{rc['finding_bounds_high']:.2f} -> bounded {rc['bounded_low']:.2f} .. "
                           f"{rc['bounded_high']:.2f} m3 ({T['findings_without_range']} findings without a range)",
            "EVIDENCE": "BOUNDED_TOTAL", "PLANNING_LOW": rc["bounded_low"], "PLANNING_BASE": rc["measured_base"],
            "PLANNING_HIGH": rc["bounded_high"]},
           {"ITEM": "F.001", "SECTION": "F BOUNDED TOTAL (MEASURED + EVERY EXPOSURE)", "FAMILY": "PLAIN_CONCRETE",
            "UNIT": "m3", "DESCRIPTION": f"plain concrete: measured {pc['measured_base']:.2f}; bounded "
                                         f"{pc['bounded_low']:.2f} .. {pc['bounded_high']:.2f} m3",
            "EVIDENCE": "BOUNDED_TOTAL", "PLANNING_LOW": pc["bounded_low"], "PLANNING_BASE": pc["measured_base"],
            "PLANNING_HIGH": pc["bounded_high"]}]
    k = 1
    for b in bounds:
        if b["SCOPE_STATE"] != "BOUNDED":
            continue
        k += 1
        out.append({"ITEM": f"F.{k:03d}", "SECTION": "F BOUNDED TOTAL (MEASURED + EVERY EXPOSURE)",
                    "FAMILY": b["FAMILY"], "UNIT": "m3",
                    "DESCRIPTION": f"{b['KIND']} {b['SHEET']} {b['STOREY']} ({b['FINDING_ID']}): {b['BASIS']}",
                    "EVIDENCE": b["RULE"], "UNRESOLVED_EXPOSURE_LOW": b["LOW_M3"],
                    "UNRESOLVED_EXPOSURE_HIGH": b["HIGH_M3"]})
    return out


def policy_record():
    return {"policy": POLICY_ID, "states": list(STATES), "bound_rules": BOUND_RULES,
            "rule": "a settled family is measured from the drawn plan with printed values or named conventions; every "
                    "other finding carries a stated range; no ratio; a finding never adds twice"}
