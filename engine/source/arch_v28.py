"""ARCHITECTURAL TAKEOFF V2.8 (M9 Phase 2B-9) - heights read from the drawing, the opening schedule, window reveals
and the wall geometry per face (generic; stdlib only). Read only by ARCH_TAKEOFF_V2.8 (tools/urban_boq_m9.py); no
earlier method reaches this module.

Height evidence (UP-HGT-001, registry 1.4.0). Every height a quantity uses is a candidate with its source, value,
unit, scope and rank; the best rank governs, a more specific scope breaks a tie, two candidates of the governing rank
and scope that disagree are a CONFLICT (no value), and a lower-ranked disagreeing candidate is kept as overridden:
    1 ELEMENT_ANNOTATION  a text on the element: next to an opening (SILL 1.00, H=2.20, 1.50x1.20) or inside a room
                          (C.H. 3.00, WALL TILES 2.40, PLASTER TO 3.20)
    2 SCHEDULE            a door / window schedule row, bound to an opening by the mark drawn next to it
    3 SECTION / ELEVATION a section's level texts on the floor's band (F.F.L., F.C.L., U/S SLAB): ceiling height =
                          F.C.L. - F.F.L., soffit height = U/S SLAB - F.F.L.; floor-to-floor is reported, never a wall
                          height
    3.5 DERIVED           the plan-level interval minus every sourced component (engine.source.wall_height.derive)
    4 FLOOR_NOTE          a general note on the floor's plan sheet (ALL WINDOW SILLS 1.00 M, CEILING HEIGHT 3.00 M)
    4.5 PROJECT_NOTE      a general note on another sheet (project scope)
    5 PROJECT_RULE        the project facts (URBAN_ARCH_FACTS_V1, an approved project rule or owner project fact)
    6 URBAN_DEFAULT       the owner reference door heights (UP-DOOR-HGT-001), always HEIGHT_ASSUMED
Scopes, most specific first: OPENING > ROOM > FLOOR > PROJECT. A floor-to-floor height is never a wall height; a
plaster height is the structural soffit, a paint / wall-tile height the finished ceiling (URBAN-PAINT-TO-FINISHED-
CEILING); a unit not stated is inferred only when exactly one reading is physically plausible (else UNIT_AMBIGUOUS).

Openings (UP-OPEN-SCHED-001). Each opening carries its plan width, the schedule width (checked), height, sill, head
(= sill + height), class (DOOR / WINDOW / FLOOR_GLAZING), and the effect on each trade: a wall finish deducts the
opening's own rectangle inside the finish band, w x (min(head, H) - max(sill, 0)); floor-level glazing (sill 0) is not
skirted; a window whose sill is not established is not skirted with certainty (a range); a window without a height
releases its width and holds its area.

Window reveals (UP-REVEAL-001). The reveal depth is the measured strip between the room's wall face and the glazing
(strip area / opening width), never a fixed value: jambs 2 x depth x the window's height inside the plaster band, the
head soffit depth x width only where wall remains above the head, both plaster (owner method: plaster by default),
PROVISIONAL (a frame detail can change it); the internal sill surface (depth x width) is its own geometry, finish by
the window detail; for floor-level glazing the strip is floor (the room's floor finish continues to the glazing).

Wall geometry (UP-WALL-GEOM-001). The wall bands keep centreline, faces, thickness and plan strip; a wall stretch
with both faces drawn over less than 0.30 m that the band rule drops (a short return at a door jamb, a curved stub
beside a curved window) is measured as wall (RETURN_STUB / CURVED_STUB), with the plan strip moved out of the
junction pieces so the plan area stays conserved.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

POLICY_ID = "ARCH_V28_HEIGHTS_OPENINGS_WALLS_V1"
RANK = {"ELEMENT_ANNOTATION": 1.0, "SCHEDULE": 2.0, "SECTION": 3.0, "ELEVATION": 3.0, "DERIVED": 3.5,
        "FLOOR_NOTE": 4.0, "PROJECT_NOTE": 4.5, "PROJECT_RULE": 5.0, "URBAN_DEFAULT": 6.0}
SCOPES = ("OPENING", "ROOM", "FLOOR", "PROJECT")
ESTABLISHED, BLOCKED, CONFLICT = "ESTABLISHED", "BLOCKED", "CONFLICT"
AGREE_M = 0.005                      # two heights agree within 5 mm
TAG_REACH_M = 1.20                   # a mark / annotation binds to the nearest opening within this
TAG_AMBIGUOUS_M = 0.10               # ... unless a second opening is this close to the same distance
WIDTH_TOL_M = 0.03                   # a schedule width agrees with the plan width within 3 cm
FLOOR_GLAZING_SILL_M = 0.02          # a sill at or below this is floor-level glazing
LEVEL_FIT_TOL_M = 0.30               # level texts are placed at their level lines within this (y calibration)
STUB_MIN_M = 0.05                    # a both-faces stretch shorter than this is a drawing artefact, never a stub
STUB_MAX_M = 0.30                    # the band rule's own minimum (arch_plan._bands, arch_v27.ARC_MIN_RUN_M)
PLAUSIBLE = {"WIDTH": (0.3, 8.0), "HEIGHT": (0.3, 6.0), "SILL": (0.0, 3.0), "ROOM_HEIGHT": (1.8, 9.0)}

_N = r"\d+(?:[.,]\d+)?"
_U = r"\s*(MM|CM|M)\b"
MARK_RE = re.compile(r"^\s*(?P<p>WD|DW|SD|AD|GD|FW|CW|D|W|V)\s*[-.]?\s*(?P<n>\d{1,3}[A-Z]?)\s*$")
MARK_KIND = {"D": "DOOR", "AD": "DOOR", "SD": "DOOR", "GD": "DOOR", "WD": "DOOR", "DW": "DOOR",
             "W": "WINDOW", "FW": "WINDOW", "CW": "WINDOW", "V": "WINDOW"}
SCHEDULE_TITLE_RE = re.compile(r"(DOOR|WINDOW|OPENING)S?(\s*(AND|&)\s*(DOOR|WINDOW)S?)?\s+SCHEDULE|"
                               r"SCHEDULE\s+OF\s+(DOORS?|WINDOWS?|OPENINGS?)")
VIEW_TITLE_RE = re.compile(r"\b(SECTION|ELEVATION)\b")
HEADER_WORDS = {"MARK": ("MARK", "REF", "TAG", "NO", "NO.", "CODE", "TYPE"), "WIDTH": ("WIDTH", "W"),
                "HEIGHT": ("HEIGHT", "H", "HT"), "SILL": ("SILL", "SILL HEIGHT", "S.H.", "SH", "SILL LEVEL"),
                "DESCRIPTION": ("DESCRIPTION", "DESC", "MATERIAL", "REMARKS")}
LEVEL_LABELS = (
    ("FFL", r"F\.?\s?F\.?\s?L\.?|FINISH(?:ED)?\s+FLOOR(?:\s+LEVEL)?"),
    ("FCL", r"F\.?\s?C\.?\s?L\.?|FINISH(?:ED)?\s+CEILING(?:\s+LEVEL)?|CEILING\s+LEVEL"),
    ("SOFFIT", r"U\s?/\s?S\.?\s*(?:OF\s*)?SLAB|SOFFIT|B\.?\s?O\.?\s?S\.?|UNDERSIDE\s+(?:OF\s+)?SLAB"),
    ("TOS", r"T\.?\s?O\.?\s?S\.?|S\.?\s?S\.?\s?L\.?|TOP\s+OF\s+SLAB"),
    ("PARAPET", r"T\.?\s?O\.?\s?P\.?|TOP\s+OF\s+PARAPET|PARAPET(?:\s+LEVEL)?"))
LEVEL_VALUE = r"([+\-±]\s?\d{1,3}[.,]\d{2,3})"
FLOOR_NAMES = (("BASEMENT", r"BASEMENT"), ("GF", r"GROUND\s+FLOOR|\bG\.?\s?F\.?\b"),
               ("MEZZANINE", r"MEZZANINE"), ("1F", r"FIRST\s+FLOOR|1\s?ST\.?\s+FLOOR"),
               ("2F", r"SECOND\s+FLOOR|2\s?ND\.?\s+FLOOR"), ("3F", r"THIRD\s+FLOOR|3\s?RD\.?\s+FLOOR"),
               ("ROOF", r"\bROOF\b"))
# texts naming a height of a room / an opening / a floor (the value and its optional unit are groups v / u)
ANNOT = (
    ("CEILING_HEIGHT", re.compile(r"(?:\bC\.?\s?H\b\.?|CLG\.?\s*H(?:EIGH)?T?\b|CEILING\s+HEIGHT|CLEAR\s+HEIGHT)\s*"
                                  r"[=:]?\s*(?P<v>" + _N + r")(?:" + _U + r")?")),
    ("TILE_HEIGHT", re.compile(r"(?:WALL\s+)?(?:TILES?|CERAMIC|PORCELAIN)\s*(?:UP\s+TO|TO|H\s*=|HEIGHT)\s*"
                               r"(?P<v>" + _N + r")(?:" + _U + r")?")),
    ("PLASTER_HEIGHT", re.compile(r"PLASTER\s*(?:UP\s+TO|TO|HEIGHT)\s*(?P<v>" + _N + r")(?:" + _U + r")?")),
    ("DOOR_HEIGHT", re.compile(r"DOORS?\s+(?:HEIGHT|H)\s*[=:]?\s*(?P<v>" + _N + r")(?:" + _U + r")?")),
    ("WINDOW_HEIGHT", re.compile(r"WINDOWS?\s+(?:HEIGHT|H)\s*[=:]?\s*(?P<v>" + _N + r")(?:" + _U + r")?")),
    ("SILL", re.compile(r"(?:WINDOW\s+)?SILLS?(?:\s+(?:HEIGHT|LEVEL))?\s*[=:]?\s*\+?(?P<v>" + _N + r")(?:" + _U +
                        r")?")),
    ("HEIGHT", re.compile(r"(?:^|\s)(?:H|HT)\s*[=:]\s*(?P<v>" + _N + r")(?:" + _U + r")?")),
    ("SIZE", re.compile(r"(?P<w>" + _N + r")\s*[xX×*]\s*(?P<v>" + _N + r")(?:" + _U + r")?")),
)
FULL_HEIGHT_TILE = re.compile(r"(?:TILES?|CERAMIC|PORCELAIN)\b.*\bFULL\s+HEIGHT")
QUANTITY_OF = {"CEILING_HEIGHT": "ROOM_HEIGHT", "TILE_HEIGHT": "ROOM_HEIGHT", "PLASTER_HEIGHT": "ROOM_HEIGHT",
               "DOOR_HEIGHT": "HEIGHT", "WINDOW_HEIGHT": "HEIGHT", "SILL": "SILL", "HEIGHT": "HEIGHT", "SIZE": "HEIGHT"}


# ======================================================================================== values and units
def _f(s):
    return float(s.replace(",", "."))


def to_m(raw, unit=None, quantity="HEIGHT"):
    """a printed number in metres -> (value_m or None, how). A stated unit converts; otherwise the readings m / cm / mm
    that fall inside the physical range of the quantity are kept, and exactly one distinct value is required."""
    v = _f(raw)
    if unit:
        f = {"MM": 1e-3, "CM": 1e-2, "M": 1.0}[unit.upper()]
        return round(v * f, 6), f"UNIT_STATED_{unit.upper()}"
    lo, hi = PLAUSIBLE[quantity]
    cands = {"M": v} if ("." in raw or "," in raw) and v < 30 else {"M": v, "CM": v / 100.0, "MM": v / 1000.0}
    ok = {}
    for k, x in cands.items():
        if lo - 1e-9 <= x <= hi + 1e-9:
            ok.setdefault(round(x, 6), k)
    if len(ok) == 1:
        x, k = next(iter(ok.items()))
        return x, f"UNIT_INFERRED_{k}"
    if not ok:
        return None, "OUT_OF_RANGE"
    return None, "UNIT_AMBIGUOUS:" + "/".join(sorted(ok.values()))


def norm(s):
    return re.sub(r"\s+", " ", (s or "").replace("±", "±").strip().upper())


def mark_of(s):
    m = MARK_RE.match(norm(s))
    if not m:
        return None, None
    d = re.match(r"(\d+)([A-Z]?)$", m.group("n"))
    return m.group("p") + str(int(d.group(1))) + d.group(2), MARK_KIND[m.group("p")]


def parse_level(s):
    """-> (kind, value_m) for a level text: FFL / FCL / SOFFIT / TOS / PARAPET with a signed value, or MARK for a bare
    level mark; None otherwise."""
    t = norm(s)
    vm = re.search(LEVEL_VALUE, t)
    if not vm:
        return None
    val = _f(vm.group(1).replace("±", "").replace(" ", ""))
    for kind, rx in LEVEL_LABELS:
        if re.search(r"(?:^|[^A-Z])(?:" + rx + r")(?:$|[^A-Z])", t):
            return kind, val
    if re.fullmatch(LEVEL_VALUE, t):
        return "MARK", val
    return None


def annotations(s):
    """-> [(kind, value_m, how, extra)] of the heights a text states (several per text: SILL 1.00, H=1.20)."""
    t = norm(s)
    out, used = [], []
    for kind, rx in ANNOT:
        for m in rx.finditer(t):
            if any(a < m.end() and m.start() < b for a, b in used):
                continue
            unit = m.group("u") if "u" in rx.groupindex else None
            v, how = to_m(m.group("v"), unit, QUANTITY_OF[kind])
            extra = {}
            if kind == "SIZE":
                w, howw = to_m(m.group("w"), unit, "WIDTH")
                extra = {"width_m": w, "width_how": howw}
            out.append((kind, v, how, extra))
            used.append((m.start(), m.end()))
    if FULL_HEIGHT_TILE.search(t):
        out.append(("TILE_FULL_HEIGHT", None, "TEXT", {}))
    return out


# ======================================================================================== geometry helpers
def _inside(p, poly):
    x, y = p
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def _in_box(p, b):
    return b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]


def _seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _poly_dist(p, poly):
    return min(_seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


# ======================================================================================== reading the drawing
def _src(t, **kw):
    return dict({"text_id": t["id"], "text": t["value"], "layer": t.get("layer")}, **kw)


def read_schedules(texts, frames, unit_m):
    """door / window schedules: a title, a header row (MARK / WIDTH / HEIGHT / SILL ...) and one row per mark. ->
    {"schedules": [...], "rows": {mark: row}, "findings": [...]}."""
    out, rows, findings = [], {}, []
    titles = [t for t in texts if SCHEDULE_TITLE_RE.search(norm(t["value"]))]
    for ti in titles:
        box = next((f["box"] for f in frames if _in_box((ti["x"], ti["y"]), f["box"])), None)
        if box is None:
            r = 25.0 / unit_m
            box = (ti["x"] - 2.0 / unit_m, ti["y"] - r, ti["x"] + r, ti["y"] + 1.0 / unit_m)
        cells = [t for t in texts if t is not ti and _in_box((t["x"], t["y"]), box) and t["y"] <= ti["y"] + 1e-9
                 and not SCHEDULE_TITLE_RE.search(norm(t["value"]))]
        if not cells:
            continue
        hs = sorted(t.get("height") or 0.0 for t in cells)
        tol = max(0.5 * (hs[len(hs) // 2] or 0.2 / unit_m), 0.02 / unit_m)
        grid = []
        for t in sorted(cells, key=lambda t: -t["y"]):
            if grid and abs(grid[-1][0] - t["y"]) <= tol:
                grid[-1][1].append(t)
            else:
                grid.append([t["y"], [t]])
        header, hrow = None, None
        for k, (_y, cs) in enumerate(grid):
            fields = {}
            for c in cs:
                w = norm(c["value"])
                base = re.sub(r"\s*\((MM|CM|M)\)\s*$", "", w)
                for fld, words in HEADER_WORDS.items():
                    if base in words and fld not in fields:
                        fields[fld] = c
            if len(fields) >= 2 and "MARK" in fields:
                header, hrow = fields, k
                break
        if header is None:
            findings.append({"code": "SCHEDULE_HEADER_NOT_READ", "title": _src(ti)})
            continue
        units = {}
        for fld, c in header.items():
            m = re.search(r"\((MM|CM|M)\)", norm(c["value"]))
            if m:
                units[fld] = m.group(1)
        xs = sorted((c["x"], fld) for fld, c in header.items())
        sched = {"title": _src(ti), "header": {f: _src(c) for f, c in header.items()}, "units": units, "rows": []}
        for _y, cs in grid[hrow + 1:]:
            row = {}
            for c in cs:
                fld = min(xs, key=lambda xf: abs(xf[0] - c["x"]))[1]
                row.setdefault(fld, c)
            if "MARK" not in row:
                continue
            mk, kind = mark_of(row["MARK"]["value"])
            if mk is None:
                continue
            rec = {"mark": mk, "kind": kind, "source": _src(row["MARK"], schedule=ti["id"])}
            for fld, q in (("WIDTH", "WIDTH"), ("HEIGHT", "HEIGHT"), ("SILL", "SILL")):
                c = row.get(fld)
                raw = norm(c["value"]) if c else ""
                if not c or raw in ("-", "--", "N/A", ""):
                    rec[fld.lower() + "_m"], rec[fld.lower() + "_how"] = None, "NOT_GIVEN"
                    continue
                m = re.search(_N, raw)
                if not m:
                    rec[fld.lower() + "_m"], rec[fld.lower() + "_how"] = None, "NOT_A_NUMBER"
                    continue
                rec[fld.lower() + "_m"], rec[fld.lower() + "_how"] = to_m(m.group(0), units.get(fld), q)
            if row.get("DESCRIPTION"):
                rec["description"] = row["DESCRIPTION"]["value"]
            if mk in rows:
                findings.append({"code": "SCHEDULE_MARK_REPEATED", "mark": mk, "rows": [rows[mk]["source"],
                                                                                       rec["source"]]})
                rows[mk]["conflict"] = True
                continue
            rows[mk] = rec
            sched["rows"].append(rec)
        out.append(sched)
    return {"schedules": out, "rows": rows, "findings": findings}


def read_views(texts, frames, unit_m, plan_floor_levels, plan_floors):
    """sections / elevations on non-plan sheets: their level texts, bound to floors. -> {"views": [...],
    "floors": {floor: [candidate, ...]}, "findings": [...]}."""
    views, by_floor, findings = [], defaultdict(list), []
    k = 1.0 / unit_m
    for fr in frames:
        tx = [t for t in texts if _in_box((t["x"], t["y"]), fr["box"])]
        titles = [t for t in tx if VIEW_TITLE_RE.search(norm(t["value"])) and not parse_level(t["value"])]
        if not titles:
            continue
        kind = "SECTION" if any("SECTION" in norm(t["value"]) for t in titles) else "ELEVATION"
        levels = []
        for t in tx:
            pl = parse_level(t["value"])
            if pl:
                levels.append({"kind": pl[0], "value_m": pl[1], "y": t["y"], "text": t})
        names = []
        for t in tx:
            if t in titles:
                continue
            for fl, rx in FLOOR_NAMES:
                if re.search(rx, norm(t["value"])) and not parse_level(t["value"]):
                    names.append((fl, t))
                    break
        view = {"view_id": f"{kind}:{titles[0]['id']}", "kind": kind, "title": _src(titles[0]),
                "sheet_box": fr["box"], "levels": [{"kind": x["kind"], "value_m": x["value_m"],
                                                    "text": _src(x["text"])} for x in levels],
                "floor_names": [{"floor": fl, "text": _src(t)} for fl, t in names]}
        # y calibration: the level texts sit at their level lines (y = a + b value)
        cal = None
        if len(levels) >= 2 and len({x["value_m"] for x in levels}) >= 2:
            n = len(levels)
            mv = sum(x["value_m"] for x in levels) / n
            my = sum(x["y"] for x in levels) / n
            sxx = sum((x["value_m"] - mv) ** 2 for x in levels)
            b = sum((x["value_m"] - mv) * (x["y"] - my) for x in levels) / sxx
            a = my - b * mv
            res = max(abs(x["y"] - (a + b * x["value_m"])) for x in levels)
            ok = b > 0 and abs(b - k) <= 0.01 * k and res <= LEVEL_FIT_TOL_M * k
            cal = {"a": a, "b": b, "max_residual_m": round(res / k, 4), "consistent": ok}
        view["calibration"] = cal and {kk: (round(vv, 6) if isinstance(vv, float) else vv) for kk, vv in cal.items()}
        ffl = sorted({x["value_m"] for x in levels if x["kind"] == "FFL"})
        bands = []
        for i, v in enumerate(ffl):
            top = ffl[i + 1] if i + 1 < len(ffl) else None
            fl, how = None, None
            if cal and cal["consistent"]:
                inside = sorted({f for f, t in names if v - 1e-6 <= (t["y"] - cal["a"]) / cal["b"] <
                                 (top if top is not None else v + 100.0)})
                if len(inside) == 1:
                    fl, how = inside[0], "FLOOR_NAME_ON_THE_BAND"
            if fl is None:
                by_level = [f for f, lv in plan_floor_levels.items() if lv is not None and abs(lv - v) <= AGREE_M]
                if len(by_level) == 1:
                    fl, how = by_level[0], "FFL_EQUALS_THE_PLAN_LEVEL"
            if fl is None and len(ffl) == 1 and len(plan_floors) == 1:
                fl, how = plan_floors[0], "ONE_FLOOR_ONE_FFL"
            bands.append({"ffl_m": v, "next_ffl_m": top, "floor": fl, "binding": how})
        view["bands"] = bands
        for band in bands:
            if band["floor"] is None:
                findings.append({"code": "SECTION_BAND_NOT_BOUND", "view": view["view_id"], "ffl_m": band["ffl_m"]})
                continue
            v, top = band["ffl_m"], band["next_ffl_m"]
            for x in levels:
                if x["kind"] not in ("FCL", "SOFFIT"):
                    continue
                if not (v < x["value_m"] and (top is None or x["value_m"] <= top + 1e-9)):
                    continue
                q = "CEILING_HEIGHT" if x["kind"] == "FCL" else "SOFFIT_HEIGHT"
                by_floor[band["floor"]].append(cand(q, round(x["value_m"] - v, 6), kind, "FLOOR", band["floor"],
                                                    _src(x["text"], view=view["view_id"],
                                                         formula=f"{x['kind']} {x['value_m']:+.2f} - FFL {v:+.2f}")))
            if top is not None:
                by_floor[band["floor"]].append(cand("FLOOR_TO_FLOOR", round(top - v, 6), kind, "FLOOR", band["floor"],
                                                    {"view": view["view_id"], "formula": f"FFL {top:+.2f} - FFL "
                                                     f"{v:+.2f}"}, never_wall_height=True))
        views.append(view)
    return {"views": views, "floors": dict(by_floor), "findings": findings}


def cand(quantity, value_m, kind, scope, scope_id, source, how=None, **extra):
    rec = {"quantity": quantity, "value_m": value_m, "kind": kind, "rank": RANK[kind], "scope": scope,
           "scope_id": scope_id, "source": source, "state": ESTABLISHED if value_m is not None else BLOCKED}
    if how:
        rec["unit"] = how
    rec.update(extra)
    if value_m is None:
        rec["why"] = how or "no value"
    return rec


def bind_floor(floor, texts, rooms, openings, unit_m, rows):
    """the texts of one plan region bound to its openings (marks, element annotations), rooms (annotations inside the
    room) and the floor (notes). -> {"openings": {oid: {"mark", "candidates", "findings"}}, "rooms": {rid: [...]},
    "floor": [...], "findings": [...]}"""
    reach = TAG_REACH_M / unit_m
    ops = [o for o in openings if o["kind"] in ("DOOR", "WINDOW") and o.get("centre")]
    out_o = {o["opening_id"]: {"mark": None, "candidates": [], "findings": []} for o in ops}
    out_r = defaultdict(list)
    out_f, findings = [], []
    marks_to = defaultdict(list)

    def nearest(t, kind=None):
        d = sorted((math.dist((t["x"], t["y"]), o["centre"]), o["opening_id"], o) for o in ops
                   if kind is None or o["kind"] == kind or (kind == "WINDOW" and o["kind"] == "WINDOW"))
        if not d or d[0][0] > reach:
            return None, "NO_OPENING_WITHIN_REACH"
        if len(d) > 1 and d[1][0] - d[0][0] <= TAG_AMBIGUOUS_M / unit_m:
            return None, f"AMBIGUOUS: {d[0][1]} / {d[1][1]}"
        return d[0][2], None

    for t in texts:
        mk, mkind = mark_of(t["value"])
        if mk is not None:
            o, why = nearest(t, mkind)
            if o is None:
                findings.append({"code": "MARK_NOT_BOUND", "mark": mk, "why": why, "text": _src(t)})
            else:
                marks_to[o["opening_id"]].append((mk, t))
            continue
        ann = annotations(t["value"])
        if not ann:
            continue
        room = next((r for r in rooms if r.get("polygon") and _inside((t["x"], t["y"]), r["polygon"])), None)
        room_kinds = {"CEILING_HEIGHT", "TILE_HEIGHT", "PLASTER_HEIGHT", "TILE_FULL_HEIGHT"}
        if room is not None and any(a[0] in room_kinds for a in ann) and not re.search(r"\bALL\b|UNLESS|NOTE",
                                                                                        norm(t["value"])):
            for kind, v, how, _x in ann:
                if kind in room_kinds:
                    out_r[room["room_id"]].append(cand(kind, v, "ELEMENT_ANNOTATION", "ROOM", room["room_id"],
                                                       _src(t), how))
            continue
        if re.search(r"\bALL\b|UNLESS|NOTE|GENERAL", norm(t["value"])) or room is not None:
            for kind, v, how, x in ann:
                if kind in ("SIZE", "HEIGHT"):
                    continue
                out_f.append(cand(kind, v, "FLOOR_NOTE", "FLOOR", floor, _src(t), how))
            continue
        o, why = nearest(t)
        if o is None:
            findings.append({"code": "ANNOTATION_NOT_BOUND", "why": why, "text": _src(t)})
            continue
        for kind, v, how, x in ann:
            if kind in ("SILL", "HEIGHT", "SIZE"):
                q = {"SILL": "SILL", "HEIGHT": "HEIGHT", "SIZE": "HEIGHT"}[kind]
                out_o[o["opening_id"]]["candidates"].append(
                    cand(q, v, "ELEMENT_ANNOTATION", "OPENING", o["opening_id"], _src(t), how,
                         **({"width_m": x.get("width_m")} if kind == "SIZE" else {})))
    for oid, ms in marks_to.items():
        if len({m for m, _t in ms}) > 1:
            out_o[oid]["findings"].append({"code": "TWO_MARKS_ON_ONE_OPENING", "marks": sorted({m for m, _t in ms})})
            continue
        mk, t = ms[0]
        out_o[oid]["mark"] = {"mark": mk, "text": _src(t)}
        row = rows.get(mk)
        if row is None:
            out_o[oid]["findings"].append({"code": "MARK_NOT_IN_A_SCHEDULE", "mark": mk})
            continue
        if row.get("conflict"):
            out_o[oid]["findings"].append({"code": "SCHEDULE_MARK_REPEATED", "mark": mk})
            continue
        for q in ("HEIGHT", "SILL"):
            v = row.get(q.lower() + "_m")
            how = row.get(q.lower() + "_how")
            if v is not None or how not in ("NOT_GIVEN",):
                out_o[oid]["candidates"].append(cand(q, v, "SCHEDULE", "OPENING", oid, dict(row["source"], mark=mk),
                                                     how))
        out_o[oid]["schedule_row"] = row
    return {"openings": out_o, "rooms": dict(out_r), "floor": out_f, "findings": findings}


def project_notes(texts, frames, plan_boxes, schedule_frames, view_frames):
    """general notes on sheets that are neither a floor plan, a schedule nor a section: project scope."""
    out = []
    for t in texts:
        p = (t["x"], t["y"])
        if any(_in_box(p, b) for b in list(plan_boxes) + list(schedule_frames) + list(view_frames)):
            continue
        if not re.search(r"\bALL\b|UNLESS|NOTE|GENERAL", norm(t["value"])):
            continue
        for kind, v, how, _x in annotations(t["value"]):
            if kind in ("SIZE", "HEIGHT"):
                continue
            out.append(cand(kind, v, "PROJECT_NOTE", "PROJECT", "*", _src(t), how))
    return out


# ======================================================================================== resolution
def resolve(quantity, candidates):
    """the governing value of one quantity from its candidates (best rank, then most specific scope); two governing
    candidates that disagree -> CONFLICT; lower-ranked disagreeing ones are kept as overridden."""
    cs = [c for c in candidates if c["quantity"] == quantity]
    ok = sorted((c for c in cs if c["state"] == ESTABLISHED and not c.get("never_wall_height")),
                key=lambda c: (c["rank"], SCOPES.index(c["scope"])))
    out = {"quantity": quantity, "candidates": cs, "policy": POLICY_ID}
    if not ok:
        why = sorted({c.get("why") or "never a wall height" for c in cs}) or ["NO_EVIDENCE"]
        return dict(out, state=BLOCKED, value_m=None, governing=None, authority=None, why=why)
    g = ok[0]
    tied = [c for c in ok if c["rank"] == g["rank"] and c["scope"] == g["scope"]]
    if any(abs(c["value_m"] - g["value_m"]) > AGREE_M for c in tied):
        return dict(out, state=CONFLICT, value_m=None, governing=g["kind"], authority=None,
                    why=[f"CONFLICT ({g['kind']}, {g['scope']}): " + ", ".join(
                        sorted({f"{c['value_m']:.3f} m ({c['source'].get('text') or c['source'].get('formula')})"
                                for c in tied}))])
    over = [c for c in ok[len(tied):] if abs(c["value_m"] - g["value_m"]) > AGREE_M]
    auth = f"{g['kind']} ({g['scope']} {g['scope_id']}): " + str(g["source"].get("text") or g["source"].get("formula")
                                                               or g["source"].get("authority") or "")
    return dict(out, state=ESTABLISHED, value_m=g["value_m"], governing=g["kind"], authority=auth, rank=g["rank"],
                scope=g["scope"], source=g["source"],
                overridden=[{"kind": c["kind"], "scope": c["scope"], "value_m": c["value_m"],
                             "difference_m": round(c["value_m"] - g["value_m"], 6)} for c in over])


class Evidence:
    """the height evidence of one drawing: schedules, views, project notes, and per floor the plan-bound texts."""

    def __init__(self, texts, frames, plan_regions, unit_m, plan_floor_levels, facts=None):
        self.unit_m = unit_m
        self.facts = facts or {}
        pboxes = [r["box"] for r in plan_regions]
        self.sched = read_schedules(texts, frames, unit_m)
        self.views = read_views(texts, frames, unit_m, plan_floor_levels, [r["floor"] for r in plan_regions])
        s_frames = [f["box"] for f in frames if any(_in_box((t["x"], t["y"]), f["box"]) for t in texts
                                                    if SCHEDULE_TITLE_RE.search(norm(t["value"])))]
        v_frames = [v["sheet_box"] for v in self.views["views"]]
        self.project = project_notes(texts, frames, pboxes, s_frames, v_frames)
        self.floors = {}

    def bind(self, floor, texts, rooms, openings):
        self.floors[floor] = bind_floor(floor, texts, rooms, openings, self.unit_m, self.sched["rows"])
        return self.floors[floor]

    # ------------------------------------------------------------------ rooms
    def room_candidates(self, floor, room_id):
        f = self.floors.get(floor) or {}
        return (list((f.get("rooms") or {}).get(room_id) or ()) + list(f.get("floor") or ()) +
                list(self.views["floors"].get(floor) or ()) + list(self.project))

    def room_heights(self, floor, room_id, legacy):
        """per trade (PLASTER / PAINT / WALL_TILE) the governing height, in the arch_measure / wall_height shape.
        legacy: arch_measure.heights() of the room (the facts and the derived candidates), ranked as PROJECT_RULE /
        DERIVED."""
        cs = self.room_candidates(floor, room_id)
        out = {"_interval": legacy.get("_interval"), "_v28": True}
        for tr, q_main, q_alt in (("PAINT", "CEILING_HEIGHT", None), ("PLASTER", "SOFFIT_HEIGHT", "PLASTER_HEIGHT"),
                                  ("WALL_TILE", "TILE_HEIGHT", None)):
            mine = [dict(c, quantity=tr) for c in cs if c["quantity"] in (q_main, q_alt)]
            for c in (legacy.get(tr) or {}).get("candidates") or ():
                if c.get("kind") in ("FLOOR_TO_FLOOR",):
                    continue
                kind = "DERIVED" if c.get("kind") == "DERIVED_CLEAR_HEIGHT" else "PROJECT_RULE"
                mine.append(cand(tr, c.get("value_m") if c.get("state") == "ESTABLISHED" else None, kind, "FLOOR",
                                 floor, {"authority": c.get("authority"), "legacy_kind": c.get("kind"),
                                         "missing": c.get("missing")},
                                 None if c.get("state") == "ESTABLISHED" else "BLOCKED: " + str(c.get("missing"))))
            r = resolve(tr, mine)
            # the wall_height shape (OFS.wall_tile_height reads explicit WALL_TILE candidates by kind)
            r["candidates"] = [dict(c, kind=("OWNER_PROJECT_FACT" if c["kind"] == "PROJECT_RULE" else
                                             "SOURCE_FINISH_HEIGHT" if c["kind"] in ("ELEMENT_ANNOTATION", "SCHEDULE",
                                                                                     "FLOOR_NOTE", "PROJECT_NOTE")
                                             else "SECTION_CLEAR_HEIGHT" if c["kind"] in ("SECTION", "ELEVATION")
                                             else "DERIVED_CLEAR_HEIGHT"), evidence_kind=c["kind"])
                              for c in sorted(r["candidates"], key=lambda c: (c["rank"], SCOPES.index(c["scope"])))]
            if r["state"] != ESTABLISHED:
                r["state"] = BLOCKED if r["state"] != CONFLICT else CONFLICT
            out[tr] = r
        out["_tile_full_height_note"] = any(c["quantity"] == "TILE_FULL_HEIGHT" for c in cs)
        return out

    # ------------------------------------------------------------------ openings
    def opening(self, floor, o, *, door_fallback=None):
        """the opening's height, sill and head with their sources. door_fallback(o) -> the UP-DOOR-HGT-001 height of
        the door's category (rank URBAN_DEFAULT unless it came from the facts)."""
        f = (self.floors.get(floor) or {}).get("openings", {}).get(o["opening_id"]) or {"candidates": [],
                                                                                       "findings": [], "mark": None}
        cs = list(f["candidates"])
        kind = o["kind"]
        fl_notes = (self.floors.get(floor) or {}).get("floor") or []
        for c in fl_notes + list(self.project):
            if c["quantity"] == "SILL" and kind == "WINDOW":
                cs.append(dict(c, quantity="SILL"))
            if c["quantity"] == ("DOOR_HEIGHT" if kind == "DOOR" else "WINDOW_HEIGHT"):
                cs.append(dict(c, quantity="HEIGHT"))
        oh = (self.facts.get("opening_heights") or {})
        fh = oh.get(kind)
        if fh and fh.get("value_m") is not None:
            cs.append(cand("HEIGHT", fh["value_m"], "PROJECT_RULE", "PROJECT", "*",
                           {"authority": fh.get("authority"), "facts": f"opening_heights.{kind}"}))
            if fh.get("sill_m") is not None and kind == "WINDOW":
                cs.append(cand("SILL", fh["sill_m"], "PROJECT_RULE", "PROJECT", "*",
                               {"authority": fh.get("authority"), "facts": f"opening_heights.{kind}.sill_m"}))
        if kind == "DOOR" and door_fallback is not None:
            d = door_fallback(o) or {}
            if d.get("value_m") is not None and d.get("state") == "ASSUMED":
                cs.append(cand("HEIGHT", d["value_m"], "URBAN_DEFAULT", "PROJECT", "*",
                               {"authority": d.get("source"), "flags": d.get("flags")}))
        h = resolve("HEIGHT", cs)
        if kind == "DOOR":
            s = {"quantity": "SILL", "state": ESTABLISHED, "value_m": 0.0, "governing": "DOOR",
                 "authority": "a door stands on the floor", "candidates": []}
        else:
            s = resolve("SILL", cs)
        rec = {"opening_id": o["opening_id"], "floor": floor, "kind": kind, "mark": f.get("mark"),
               "plan_width_m": round(o["width_m"], 4), "height": _brief(h), "sill": _brief(s),
               "findings": list(f.get("findings") or ())}
        row = f.get("schedule_row")
        if row is not None:
            rec["schedule"] = {"mark": row["mark"], "width_m": row.get("width_m"), "height_m": row.get("height_m"),
                               "sill_m": row.get("sill_m"), "description": row.get("description"),
                               "source": row["source"]}
            if row.get("width_m") is not None and abs(row["width_m"] - o["width_m"]) > WIDTH_TOL_M:
                rec["findings"].append({"code": "SCHEDULE_WIDTH_DIFFERS", "schedule_m": row["width_m"],
                                        "plan_m": round(o["width_m"], 4)})
                if kind == "WINDOW":
                    # the mark may be wrong: neither the height nor the sill of a window is taken from a row that is
                    # not its size; other evidence (an annotation on the window, a note) still governs
                    rest = [c for c in cs if c["kind"] != "SCHEDULE"]
                    for q, key in (("HEIGHT", "height"), ("SILL", "sill")):
                        if rec[key].get("governing") != "SCHEDULE":
                            continue
                        r2 = resolve(q, rest)
                        rec[key] = (_brief(r2) if r2["state"] == ESTABLISHED else
                                    dict(rec[key], state=CONFLICT, value_m=None,
                                         why=["SCHEDULE_WIDTH_DIFFERS: the mark's row is not this window's size"]))
        hv, sv = rec["height"]["value_m"], rec["sill"]["value_m"]
        rec["head_m"] = round(sv + hv, 6) if hv is not None and sv is not None else None
        if kind == "WINDOW":
            rec["class"] = ("FLOOR_GLAZING" if sv is not None and sv <= FLOOR_GLAZING_SILL_M else
                            "WINDOW" if sv is not None else "WINDOW_SILL_NOT_ESTABLISHED")
        else:
            rec["class"] = "DOOR"
        rec["area_m2"] = round(o["width_m"] * hv, 6) if hv is not None else None
        rec["area_state"] = "MEASURED" if hv is not None and rec["height"]["governing"] != "URBAN_DEFAULT" else (
            "ASSUMED_HEIGHT" if hv is not None else "HELD: height not established")
        return rec


def _brief(r):
    out = {k: r.get(k) for k in ("state", "value_m", "governing", "authority")}
    out.update({k: r[k] for k in ("scope", "why", "overridden") if r.get(k) is not None})
    return out


# ======================================================================================== quantities
def band_height(op, H):
    """the opening's own height inside a finish band [0, H]: min(head, H) - max(sill, 0); None when not established."""
    if op is None:
        return None
    hv, sv = op["height"].get("value_m"), op["sill"].get("value_m")
    if hv is None or sv is None:
        return None
    return max(0.0, min(sv + hv, H) - max(sv, 0.0))


def height_of(schedule, legacy_heights):
    """-> the release_safety.wall_finish height_of(o, H): the V2.8 band height when the opening's height AND sill are
    established, else the V2.2 reading (the facts' kind height, full height inside the band)."""
    def f(o, H):
        op = schedule.get(o["opening_id"])
        b = band_height(op, H)
        if b is not None:
            return b, f"{op['height']['authority']}; sill {op['sill']['value_m']:.2f} m ({op['sill']['governing']})"
        if op is not None and op["height"].get("value_m") is not None and o["kind"] == "WINDOW":
            return min(op["height"]["value_m"], H), (op["height"]["authority"] +
                                                     "; WINDOW_POSITION_ASSUMED: no sill - full height in the band")
        hh = (legacy_heights or {}).get(o["kind"])
        if hh:
            return min(hh["value_m"], H), hh["authority"]
        return None
    return f


WT = "WINDOW_THRESHOLD"


def skirting_adjustment(room_windows, detail, schedule):
    """dry-room skirting under V2.8, edge by edge against the F-17 reading (release_safety.skirting): floor-level glazing
    is never skirted; a window whose sill is not established is skirted under one reading only. Each threshold edge of
    the room's windows (boundary_detail threshold_sets) moves at most once:
      certain -> not skirted   floor-level glazing alone on the edge (floor_glazing_lm, out of the skirting line)
      certain -> range         an unknown sill, or floor glazing on a line shared with a wall / column (to_range_lm)
      range -> not skirted     floor glazing on an edge F-17 already held as a range with no other skirted role
                               (floor_glazing_range_lm, out of the range line)
    an edge F-17 already holds in its range stays there once; an edge of a sill window (class WINDOW) is unchanged.
    -> {"floor_glazing_lm", "to_range_lm", "to_range_by": {why: lm}, "floor_glazing_range_lm",
        "range_out_by_roles": {role set: lm}, "range_out_credit_lm", "by_window": {...}}"""
    from engine.source.release_safety import SKIRTED_OUTER
    cls_of = {w["opening_id"]: ((schedule.get(w["opening_id"]) or {}).get("class") or "WINDOW_SILL_NOT_ESTABLISHED")
              for w in room_windows}
    fg = fg_range = credit_out = 0.0
    to_range, range_out = defaultdict(float), defaultdict(float)
    for g in detail.get("threshold_sets") or ():
        ws = [o for o in g["openings"] if o in cls_of]
        roles = set(g["roles"].split("+"))
        if not ws or WT not in roles:
            continue
        cs = {cls_of[o] for o in ws}
        if cs == {"WINDOW"}:
            continue
        ln, others, unskirted = g["lm"], (roles & SKIRTED_OUTER) - {WT}, roles - SKIRTED_OUTER
        if cs == {"FLOOR_GLAZING"}:
            if not others and not unskirted:
                fg += ln
            elif not others:
                fg_range += ln
                range_out[g["roles"]] += ln
                credit_out += ln / len(roles)
            elif not unskirted:
                to_range["FLOOR_GLAZING_ON_" + "+".join(sorted(others))] += ln
        elif not unskirted:
            to_range["WINDOW_SILL_NOT_ESTABLISHED"] += ln
    by = {w["opening_id"]: {"lm": round((detail.get("opening_lm") or {}).get(w["opening_id"], 0.0), 6),
                            "class": cls_of[w["opening_id"]]} for w in room_windows}
    return {"floor_glazing_lm": round(fg, 6), "to_range_lm": round(sum(to_range.values()), 6),
            "to_range_by": {k: round(v, 6) for k, v in sorted(to_range.items())},
            "floor_glazing_range_lm": round(fg_range, 6),
            "range_out_by_roles": {k: round(v, 6) for k, v in sorted(range_out.items())},
            "range_out_credit_lm": round(credit_out, 6), "by_window": by}


def _strip_side(strip, rooms):
    """the room on the strip's side: a room listing the window whose boundary the strip touches (its centroid within
    half the strip's depth + 2 cm of the room polygon); None = the strip lies beyond the glazing, outside every room."""
    ids = strip["geometry"].get("room_face_ids")
    if ids is not None:
        # a curved opening's strip (ARCH_TAKEOFF_V2.9 records the faces meeting its wall face): its centroid can lie
        # off the strip, so the side is the room meeting the strip's own wall face
        return next((r for r in rooms if r.get("face_id") in ids and strip["opening_ids"][0] in
                     (r.get("windows") or ())), None)
    pm = strip["polygon_m"]
    c = (sum(x for x, _ in pm) / len(pm), sum(y for _, y in pm) / len(pm))
    reach = 0.5 * (strip["geometry"].get("depth_m") or 0.0) + 0.02
    best = None
    for r in rooms:
        if not r.get("polygon_m") or strip["opening_ids"][0] not in (r.get("windows") or ()):
            continue
        d = _poly_dist(c, r["polygon_m"])
        if d <= reach and (best is None or d < best[0]):
            best = (d, r)
    return best[1] if best else None


def window_strip_lines(ctx, strips, rooms, floor, schedule, heights_of_room, *, line, wet_rooms=()):
    """the WINDOW_REVEAL strips of windows whose sill is established, and the window reveals. -> (lines, unresolved,
    remaining strips, reveal records). A sill window: the strip is its internal sill surface (geometry released, finish
    by the window detail) and the reveals are jambs 2 x depth x band height + head depth x width where wall remains
    above; floor-level glazing: the strip is floor (the room's floor finish), jambs only up to the plaster height.
    heights_of_room(room) -> the room's established PLASTER height or None."""
    lines, unresolved, rest, recs = [], [], [], []
    groups = defaultdict(list)
    for s in strips:
        if s["class"] == "WINDOW_REVEAL" and len(s["opening_ids"]) == 1:
            groups[s["opening_ids"][0]].append(s)
        else:
            rest.append(s)
    for oid, ss in sorted(groups.items()):
        op = schedule.get(oid)
        if op is None or op["class"] not in ("WINDOW", "FLOOR_GLAZING") or op["height"].get("value_m") is None or \
                not all(s["geometry_verified"] for s in ss):
            rest.extend(ss)
            continue
        sill, hv = op["sill"]["value_m"], op["height"]["value_m"]
        head = sill + hv
        for s in ss:
            room = _strip_side(s, rooms)
            g = s["geometry"]
            w, d = g.get("opening_width_m"), g.get("depth_m")
            pseudo = {"room_id": f"{floor}-STRIP-{oid}-{s['strip_id']}", "floor": floor,
                      "name_en": f"window {oid}" + (f" | {room['name_en']}" if room else ""),
                      "name_ar": room["name_ar"] if room else "-"}
            src = f"sill {sill:.2f} m ({op['sill']['governing']}), height {hv:.2f} m ({op['height']['governing']})"
            if room is None:
                # the strip beyond the glazing: an external surface (external sill / reveal) - geometry only, the
                # external finishes are not in the internal finishing scope
                lines.append(line(ctx, item_code="ARCH.WINDOW_REVEAL", room=pseudo,
                                  element=f"window external strip {oid}", unit="m2", net=round(s["area_m2"], 6),
                                  formula="the strip between the glazing and the outer wall face (measured face)",
                                  inputs={"opening_id": oid, "strips": [s["strip_id"]],
                                          "depth_m": s["geometry"].get("depth_m"),
                                          "width_m": s["geometry"].get("opening_width_m"),
                                          "dims": "external strip", "sill": op["sill"], "class": op["class"]},
                                  rule_id=None, notes="EXTERNAL_STRIP: outside the glazing - an external sill / "
                                                      "threshold surface; external finishes are not in the internal "
                                                      "scope (" + src + ")"))
                recs.append({"opening_id": oid, "floor": floor, "strip": s["strip_id"], "room_id": None,
                             "depth_m": s["geometry"].get("depth_m"), "state": "EXTERNAL_NOT_IN_INTERNAL_SCOPE"})
                continue
            dims = f"{w:.2f} x {d:.2f} m (width x depth to the glazing)" if w is not None and d is not None else ""
            if op["class"] == "FLOOR_GLAZING":
                wet = room is not None and room["room_id"] in wet_rooms
                lines.append(line(ctx, item_code="FIN.FLOOR.WET_TILE" if wet else "FIN.FLOOR.PORCELAIN", room=pseudo,
                                  element=f"window floor strip {oid}", unit="m2", net=round(s["area_m2"], 6),
                                  ev="PROVISIONAL", formula="the strip between the room face and the glazing of a "
                                                            "floor-level window (measured face)",
                                  inputs={"opening_id": oid, "strips": [s["strip_id"]], "depth_m": d, "width_m": w, "dims": dims,
                                          "sill": op["sill"], "class": op["class"]},
                                  rule_id=None, notes="FLOOR_LEVEL_GLAZING: the strip is floor - the room's floor "
                                                      "finish continues to the glazing (" + src + ")"))
            else:
                lines.append(line(ctx, item_code="ARCH.WINDOW_REVEAL", room=pseudo, element=f"window sill surface {oid}",
                                  unit="m2", net=round(s["area_m2"], 6), formula="the strip between the room face and "
                                  "the glazing of a sill window = its internal sill surface (measured face)",
                                  inputs={"opening_id": oid, "strips": [s["strip_id"]], "depth_m": d, "width_m": w, "dims": dims,
                                          "sill": op["sill"], "class": op["class"]},
                                  rule_id=None, notes="SILL_SURFACE: the wall below the sill, not floor; its finish "
                                                      "(marble / plaster) is the window detail's (" + src + ")"))
            Hp = heights_of_room(room) if room else None
            rec = {"opening_id": oid, "floor": floor, "strip": s["strip_id"], "room_id": room and room["room_id"],
                   "depth_m": d, "width_m": w, "sill_m": sill, "head_m": round(head, 6), "plaster_height_m": Hp,
                   "class": op["class"]}
            if Hp is None or d is None or w is None:
                rec["state"] = "HELD: " + ("no plaster height" if Hp is None else "strip depth not measured")
                recs.append(rec)
                unresolved.append({"room_id": pseudo["room_id"], "floor": floor, "item": "FIN.PLASTER (reveal)",
                                   "reason": f"WINDOW_REVEAL_HELD ({oid}): {rec['state']}"})
                continue
            band = max(0.0, min(head, Hp) - max(sill, 0.0))
            jambs = 2 * d * band
            # a curved opening's head soffit is its strip's own plan area (ARCH_TAKEOFF_V2.9 records it), not d x w
            headsoffit = (g["curved_soffit_m2"] if g.get("curved_soffit_m2") is not None else d * w) \
                if head < Hp - 1e-9 else 0.0
            rec.update(jambs_m2=round(jambs, 6), head_m2=round(headsoffit, 6), band_m=round(band, 6),
                       plaster_m2=round(jambs + headsoffit, 6), state="MEASURED")
            recs.append(rec)
            lines.append(line(ctx, item_code="FIN.PLASTER", room=pseudo, element=f"window reveals {oid}", unit="m2",
                              net=round(jambs + headsoffit, 6), ev="PROVISIONAL",
                              formula="2 jambs x reveal depth x the window's height inside the plaster band + head "
                                      "soffit reveal depth x width (only where wall remains above the head)",
                              inputs=dict({k: rec[k] for k in ("depth_m", "width_m", "sill_m", "head_m",
                                                               "plaster_height_m", "band_m", "jambs_m2", "head_m2")},
                                          dims=f"jambs 2 x {d:.2f} x {band:.2f} m + head {d:.2f} x {w:.2f} m" +
                                          ("" if headsoffit else " (no wall above the head)")),
                              rule_id=None, notes="REVEAL_PLASTER (UP-REVEAL-001): depth = the measured strip face / "
                                                  "the opening width; plaster by the owner method (a frame detail can "
                                                  "change it); never inside the room's main wall face (" + src + ")"))
    return lines, unresolved, rest, recs


# ======================================================================================== wall stubs
def straight_stubs(segments_by_layer, wall_layers, bands, unit_m, t_range=(0.10, 0.45), families=()):
    # bands: the floor's wall records (arch_walls.walls()["walls"]): a stretch inside one of them is already wall
    """straight wall stretches whose two faces overlap less than the band rule's 0.30 m (and at least STUB_MIN_M), with
    no line between them, at least one end closed by a wall-layer line across them (a return / nib) and the thickness
    of a wall family the floor's bands already have (families, m; a 0.40 m 'stretch' between a wall face and the cap
    of a return standing on it is the junction, not a wall): -> [stub]. Bands already found are never repeated (the
    stretch must lie outside every band's strip)."""
    out = []
    lo_t, hi_t = t_range[0] / unit_m, t_range[1] / unit_m
    for lay in wall_layers:
        segs = [s for s in segments_by_layer.get(lay, ()) if math.dist(s["a"], s["b"]) > 1e-9]
        for i, A in enumerate(segs):
            ax, ay = A["a"]
            ux, uy = A["b"][0] - ax, A["b"][1] - ay
            La = math.hypot(ux, uy)
            ux, uy = ux / La, uy / La
            nx, ny = -uy, ux
            for B in segs[i + 1:]:
                bx, by = B["b"][0] - B["a"][0], B["b"][1] - B["a"][1]
                Lb = math.hypot(bx, by)
                if abs(ux * by - uy * bx) / Lb > 1e-6:
                    continue
                off = (B["a"][0] - ax) * nx + (B["a"][1] - ay) * ny
                if not lo_t - 1e-9 <= abs(off) <= hi_t + 1e-9:
                    continue
                if families and not any(abs(abs(off) * unit_m - f) <= 0.005 for f in families):
                    continue
                a0, a1 = 0.0, La
                b0 = (B["a"][0] - ax) * ux + (B["a"][1] - ay) * uy
                b1 = (B["b"][0] - ax) * ux + (B["b"][1] - ay) * uy
                lo, hi = max(a0, min(b0, b1)), min(a1, max(b0, b1))
                ov = (hi - lo) * unit_m
                if not STUB_MIN_M - 1e-9 <= ov < STUB_MAX_M - 1e-9:
                    continue
                mid = ((lo + hi) / 2, off / 2)
                pm = (ax + ux * mid[0] + nx * mid[1], ay + uy * mid[0] + ny * mid[1])
                if any(_in_wall(pm, w, unit_m) for w in bands):
                    continue
                # nothing parallel between the faces; both ends closed by a line across the stretch
                between = any(abs((C["a"][0] - ax) * nx + (C["a"][1] - ay) * ny) < abs(off) - 1e-6 and
                              (C["a"][0] - ax) * nx * math.copysign(1, off) + (C["a"][1] - ay) * ny *
                              math.copysign(1, off) > 1e-6 and _parallel(C, ux, uy) and
                              _overlap_along(C, ax, ay, ux, uy, lo, hi) > 1e-6 for C in segs if C is not A and C is not B)
                if between:
                    continue
                ends = sum(1 for s_ in (lo, hi) if _closed_at(segs, ax, ay, ux, uy, nx, ny, s_, off, unit_m))
                if ends < 1:
                    continue
                c0 = (ax + ux * lo + nx * off / 2, ay + uy * lo + ny * off / 2)
                c1 = (ax + ux * hi + nx * off / 2, ay + uy * hi + ny * off / 2)
                out.append({"kind": "RETURN_STUB", "layer": lay, "length_m": round(ov, 6), "t_m": round(abs(off) * unit_m, 4),
                            "plan_m2": round(ov * abs(off) * unit_m, 6), "ends_closed": ends,
                            "faces": [A["id"], B["id"]], "mid": pm, "centreline": [c0, c1]})
    return out


def _parallel(C, ux, uy):
    cx, cy = C["b"][0] - C["a"][0], C["b"][1] - C["a"][1]
    L = math.hypot(cx, cy)
    return L > 0 and abs(ux * cy - uy * cx) / L <= 1e-6


def _overlap_along(C, ax, ay, ux, uy, lo, hi):
    c0 = (C["a"][0] - ax) * ux + (C["a"][1] - ay) * uy
    c1 = (C["b"][0] - ax) * ux + (C["b"][1] - ay) * uy
    return min(hi, max(c0, c1)) - max(lo, min(c0, c1))


def _closed_at(segs, ax, ay, ux, uy, nx, ny, s, off, unit_m):
    """a wall-layer line crossing the stretch at s, from one face to the other (within 1 mm)."""
    tol = 1e-3 / unit_m
    for C in segs:
        p = ((C["a"][0] - ax) * ux + (C["a"][1] - ay) * uy, (C["a"][0] - ax) * nx + (C["a"][1] - ay) * ny)
        q = ((C["b"][0] - ax) * ux + (C["b"][1] - ay) * uy, (C["b"][0] - ax) * nx + (C["b"][1] - ay) * ny)
        if abs(p[0] - s) <= tol and abs(q[0] - s) <= tol and min(p[1], q[1]) <= min(0, off) + tol and \
                max(p[1], q[1]) >= max(0, off) - tol:
            return True
    return False


def _in_wall(p, w, unit_m):
    """the point lies in the plan strip of a straight wall record (its centreline +- half its thickness)."""
    cl = w.get("centreline")
    if not cl or len(cl) != 2 or str(w.get("wall_id", "")).startswith("ARCBAND"):
        return False
    (ax, ay), (bx, by) = cl
    L = math.hypot(bx - ax, by - ay)
    if L <= 0:
        return False
    ux, uy = (bx - ax) / L, (by - ay) / L
    s = (p[0] - ax) * ux + (p[1] - ay) * uy
    t = abs(-(p[0] - ax) * uy + (p[1] - ay) * ux)
    return -1e-6 <= s <= L + 1e-6 and t <= w["t_m"] / unit_m / 2 + 1e-3 / unit_m


def curved_stubs(arcs_by_layer, wall_layers, unit_m, t_range=(0.10, 0.45), banded_ids=()):
    """pairs of concentric wall-layer arcs (radii t apart) whose common sweep is shorter than the band rule's 0.30 m on
    the inner arc and at least STUB_MIN_M: -> [stub] with inner / centreline / outer lengths."""
    out = []
    for lay in wall_layers:
        arcs = list(arcs_by_layer.get(lay, ()))
        for i, a in enumerate(arcs):
            if a["id"] in banded_ids:
                continue
            for b in arcs[i + 1:]:
                if b["id"] in banded_ids or math.dist(a["c"], b["c"]) * unit_m > 1e-3:
                    continue
                t = abs(a["r"] - b["r"]) * unit_m
                if not t_range[0] - 1e-9 <= t <= t_range[1] + 1e-9:
                    continue
                ov = _sweep_overlap(a, b)
                if ov is None:
                    continue
                r_in = min(a["r"], b["r"]) * unit_m
                inner = ov * r_in
                if not STUB_MIN_M - 1e-9 <= inner < STUB_MAX_M - 1e-9:
                    continue
                s0, s1 = _ccw_common(a, b)
                rm = (r_in + t / 2) / unit_m
                cl = [(a["c"][0] + rm * math.cos(s0), a["c"][1] + rm * math.sin(s0)),
                      (a["c"][0] + rm * math.cos(s1), a["c"][1] + rm * math.sin(s1))]
                out.append({"kind": "CURVED_STUB", "layer": lay, "inner_m": round(inner, 6), "centreline": cl,
                            "centreline_m": round(ov * (r_in + t / 2), 6), "outer_m": round(ov * (r_in + t), 6),
                            "t_m": round(t, 4), "plan_m2": round(ov * ((r_in + t) ** 2 - r_in ** 2) / 2, 6),
                            "sweep_rad": round(ov, 9), "faces": [a["id"], b["id"]]})
    return out


def _ccw(x):
    """the arc's angular interval counter-clockwise [start, end) from its start / mid / end points."""
    c = x["c"]
    ang = [math.atan2(p[1] - c[1], p[0] - c[0]) % (2 * math.pi) for p in (x["s"], x["m"], x["e"])]
    s, m, e = ang
    span = (e - s) % (2 * math.pi)
    if (m - s) % (2 * math.pi) <= span + 1e-12:
        return s, s + span
    return e, e + (s - e) % (2 * math.pi)


def _ccw_common(a, b):
    """the start / end angles of the two arcs' common sweep (radians)."""
    s1, e1 = _ccw(a)
    s2, e2 = _ccw(b)
    best = None
    for k in (-1, 0, 1):
        lo, hi = max(s1, s2 + 2 * math.pi * k), min(e1, e2 + 2 * math.pi * k)
        if hi - lo > 1e-12 and (best is None or hi - lo > best[1] - best[0]):
            best = (lo, hi)
    return best


def _sweep_overlap(a, b):
    s1, e1 = _ccw(a)
    s2, e2 = _ccw(b)
    best = None
    for k in (-1, 0, 1):
        lo, hi = max(s1, s2 + 2 * math.pi * k), min(e1, e2 + 2 * math.pi * k)
        if hi - lo > 1e-12 and (best is None or hi - lo > best):
            best = hi - lo
    return best


# open-area phrases a room lexicon reads as a room (D-P9-03: the Arabic phrase for "swimming pool" contains the word
# for "bath"); checked first, for the lost-label finding only - the room lexicon itself is unchanged
OPEN_AREA_PHRASES = ((re.compile(r"SWIMMING\s*POOL|\u062d\u0645\u0627\u0645\s*\u0633\u0628\u0627\u062d\u0629"), "POOL"),)


def lost_labels(texts, faces, room_word, floor, title_of=lambda s: (None, None), open_codes=()):
    """room-name texts that lie in no closed face of the plan: the room they name was not closed (a gap the plan
    reader could not bound - e.g. a window drawn only as curved glazing) and is in no quantity. A finding, never a
    silent omission. A label of an open area (open_codes: garden, roof, pool, void - outside the enclosed rooms by
    nature) is recorded as OPEN_AREA_LABEL_OUTSIDE_ROOMS, not as a lost room. -> [{floor, text, code, finding}]"""
    out = []
    polys = [f["polygon"] for f in faces if f.get("polygon") and len(f["polygon"]) >= 3]
    for t in texts:
        if title_of(t.get("value") or "")[0]:
            continue                                   # a floor-plan title, not a room tag
        code, _m = room_word(t.get("value") or "")
        if not code:
            continue
        code = next((c for rx, c in OPEN_AREA_PHRASES if rx.search(norm(t.get("value")))), code)
        if any(_inside((t["x"], t["y"]), p) for p in polys):
            continue
        out.append({"floor": floor, "code": code, "text": _src(t),
                    "finding": "OPEN_AREA_LABEL_OUTSIDE_ROOMS" if code in open_codes else
                    "ROOM_LABEL_NOT_IN_A_CLOSED_SPACE"})
    return out


def policy_record():
    return {"policy_id": POLICY_ID, "ranks": RANK, "scopes": list(SCOPES), "agree_m": AGREE_M,
            "tag_reach_m": TAG_REACH_M, "width_tol_m": WIDTH_TOL_M, "floor_glazing_sill_m": FLOOR_GLAZING_SILL_M,
            "stub_m": [STUB_MIN_M, STUB_MAX_M], "plausible": PLAUSIBLE,
            "never": ["a floor-to-floor height as a wall height", "a unit guessed when two readings are plausible",
                      "a fixed reveal depth", "a reveal inside the main wall face", "a window area from a height "
                      "not established", "a window area from a schedule row whose width is not the window's",
                      "an Urban default presented as a drawing value"]}
