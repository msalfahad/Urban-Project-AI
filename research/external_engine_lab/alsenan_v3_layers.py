"""ALSENAN V3 layers - room register, voids, finishes, blockwork, structure completion, rebar, openings, stairs.

Every value is either measured from the source (SOURCE), set by a recorded owner decision (PROJECT_OWNER_FACT /
OD-V3-n), or supplied by a versioned Urban fallback (URBAN_FALLBACK, urban_methods_v3); everything else is BLOCKED
with its reason. No benchmark value is read here (benchmark firewall).
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from shapely.geometry import LineString, Point, Polygon

import alsenan_phase_a as AP
import alsenan_phase_b2a as B2A
import alsenan_v3_geom as G
from engine.source import finish_height as FH, finish_height_v3 as FH3, legacy_text as LT
from engine.source import topology as T, urban_methods_v3 as UM3

FLOORS = ("GF", "1F", "2F")
BUILDUP = UM3.resolve("URBAN-RESIDENTIAL-FLOOR-BUILDUP-FALLBACK@v1")
WET = ("BATH", "W.C", "WC", "WASH", "TOILET", "SHOWER")
SERVICE = ("KITCHEN", "LAUNDRY", "PANTRY")
VOID_WORDS = ("VOID",)
VOID_AR = ("منور", "فراغ")
ROOM_LIKE = {"min_area_m2": 1.0, "min_effective_width_m": 0.6}
COMPUTED, REVIEW, PARTIAL, BLOCKED = "COMPUTED", "COMPUTED_REVIEW", "PARTIAL", "BLOCKED"


def layers(ctx, work) -> dict:
    out = {"buildup": BUILDUP, "methods": UM3.register()}
    out["voids"] = voids(ctx)
    out["rooms"] = rooms(ctx, out["voids"])
    out["finishes"] = finishes(ctx, out["rooms"], out["voids"])
    import alsenan_v3_structure as ST
    gr = ST.ground(ctx, work)
    gi = ST.ground_items(gr)
    out["ground"] = {k: v for k, v in gr.items()}
    out["ground_items"] = gi
    out["openings"] = ST.openings(ctx, out["rooms"])
    out["blockwork"] = ST.blockwork(ctx, out["rooms"])
    out["substructure"] = ST.substructure(ctx, gi)
    out["rebar"] = {"footings": ST.footing_rebar(ctx), "columns": ST.column_rebar(ctx), "beams": ST.beam_rebar(ctx),
                    "ground": gi["rebar"], "lintels": ST.lintel_rebar(out["openings"]["lintels"]),
                    "slabs": {"status": "BLOCKED", "why": "slab panel annotations (e.g. 5Ø10/m, 8Ø16/m) are printed per "
                              "panel but their distribution extents are not bound to the bars (generic slab-bar binding "
                              "not implemented this round)"}}
    out["railings"] = railings(out["voids"], out["rooms"])
    return out


def railings(vd, rm) -> list:
    """Void edges that are not on the boundary of the site holding the void: a gallery edge needs a guard."""
    out = []
    for v in vd["items"]:
        if not v.get("_polygon"):
            continue
        r = next((x for x in rm["rows"] if x["site"] == v["site"]), None)
        vp = Polygon(v["_polygon"])
        if r is None:
            continue
        sp = Polygon(r["_polygon"]).buffer(0)
        free = vp.exterior.difference(sp.exterior.buffer(50.0))
        out.append({"void": v["id"], "floor": v["floor"], "length_m": _r(free.length / 1000.0), "status": COMPUTED,
                    "material": UM3.BY_SPEC, "rule": "void outline less the parts on the room boundary (50 mm)"})
    return out


# ================================================================== room register
def _r(v, n=6):
    return None if v is None else round(v, n)


def _poly(res, s):
    return B2A._site_polygon(res["_arr"], s["cycle"])


def _fonts(ctx):
    return ctx["v3_topology"]["fonts_legacy"]


def _names(ctx, s):
    """(english, arabic, decode states) from the site's established label texts."""
    fonts = _fonts(ctx)
    en, ar, st = [], [], []
    for lt in s.get("label_texts") or []:
        v = (lt.get("value") or "").strip()
        h = lt["text"].split("|")[1][1:]
        fam = LT.font_family(fonts.get(h, ""))
        if fam:
            d = LT.decode(v, fam)
            ar.append(d["text"])
            st.append(d["state"])
        elif v:
            en.append(v)
    en = sorted(set(en), key=en.index)
    ar = sorted(set(ar), key=ar.index)
    return " / ".join(en), " / ".join(ar), st


def _candidate_names(ctx, s):
    """Unresolved (TR-06 / TR-10) texts inside the site that corroborate each other bilingually: an English room word
    and its legacy-Arabic twin. Returned only when CORROBORATED (else nothing)."""
    fonts = _fonts(ctx)
    en, ar = [], []
    for lt in s.get("unresolved_texts") or []:
        v = (lt.get("value") or "").strip()
        h = lt["text"].split("|")[1][1:]
        fam = LT.font_family(fonts.get(h, ""))
        if fam:
            ar.append(LT.decode(v, fam)["text"])
        elif v:
            en.append(v)
    if en and ar and LT.corroborate(" ".join(en), " ".join(ar))["state"] == "CORROBORATED":
        return " / ".join(en), " / ".join(ar)
    return None


def _ar_words(ar):
    a = LT.normalise(ar)
    return {w for w, terms in LT.LEXICON.items() if any(LT.normalise(t) in a for t in terms)}


def _room_class(en, ar):
    u = (en + ar).upper().replace(".", "").replace(" ", "")
    words = set(re.findall(r"[A-Z]+", en.upper().replace("W.C", "WC"))) | _ar_words(ar)
    if len([n for n in en.split(" / ") if n.strip()]) >= 2:          # open-plan zone: classify each name
        cls = {_room_class(n, "") for n in en.split(" / ") if n.strip()}
        return "DRY" if "DRY" in cls else sorted(cls)[0]
    if words & {"BATH", "WC", "WASH", "TOILET", "SHOWER"}:
        return "WET"
    if words & set(SERVICE):
        return "SERVICE"
    if "VOID" in words or any(LT.normalise(w) in LT.normalise(ar) for w in VOID_AR):
        return "VOID"
    if words & {"ROOF"}:
        return "ROOF"
    if words & {"GARDEN", "COURT", "POOL", "SWIMMING"}:
        return "EXTERNAL"
    return "DRY" if u else "UNKNOWN"


def _plate_in_arch(ctx, fl):
    reg = ctx["b2a"]["registration"][fl]
    plate = ctx["b2a"]["sheets"][fl]["_gross"]
    if reg["state"] != "REGISTERED" or plate is None:
        return None
    from shapely.affinity import translate
    dx, dy = reg["translation"]
    return translate(plate, xoff=-dx, yoff=-dy)


def rooms(ctx, vd) -> dict:
    """Every site of every floor, classified (OD-V3-7). A room / zone publishes its physical area even when its name is
    unknown; area is never invented across an open edge."""
    out = {"rule": dict(ROOM_LIKE), "floors": {}, "rows": []}
    for fl in FLOORS:
        res = ctx["a2_raw"][fl]["res"]
        u = ctx["a2_raw"][fl]["inp"].unit_native_to_mm or 1.0
        plate = _plate_in_arch(ctx, fl)
        counts = Counter()
        for s in sorted(res["sites"], key=lambda z: z["site_id"]):
            P = _poly(res, s)
            poly = Polygon(P) if len(P) >= 3 else None
            area = s["area_m2"]
            per = s["perimeter"] * u / 1000.0
            w = 2 * area / per if per else 0.0
            c = poly.representative_point() if poly is not None and poly.is_valid else Point(P[0]) if P else None
            inside = plate is not None and c is not None and plate.buffer(1500.0).contains(c)
            en, ar, dst = _names(ctx, s)
            occs = sorted(set(s.get("labels") or []))
            names = sorted({e.strip() for e in en.split(" / ") if e.strip()})
            if not inside:
                cls = "OUTSIDE_BUILDING (sheet note / legend / title box)"
            elif s.get("kind") == "OBSTACLE_INTERIOR":
                cls = "OBSTACLE_INTERIOR (column / shaft interior)"
            elif s.get("kind") == T.OPENING_SITE:
                cls = "OPENING_STRIP (door / glazed opening between two closures)"
            elif area < ROOM_LIKE["min_area_m2"] or w < ROOM_LIKE["min_effective_width_m"]:
                cls = "NOT_ROOM_LIKE (wall cavity / reveal / sliver)"
            elif len(names) >= 2 and len(occs) >= 2:
                cls = "OPEN_PLAN_ZONE"
            elif occs:
                cls = "ROOM"
            else:
                cls = "UNNAMED_ROOM (physical area published, name UNKNOWN)"
            counts[cls.split(" ")[0]] += 1
            if cls.split(" ")[0] not in ("ROOM", "OPEN_PLAN_ZONE", "UNNAMED_ROOM", "OPENING_STRIP"):
                continue
            name_basis = "ESTABLISHED_ROOM_LABEL" if occs else None
            if not occs:
                cand = _candidate_names(ctx, s)
                if cand:
                    en, ar = cand
                    name_basis = "BILINGUAL_CANDIDATE_TEXTS_IN_SITE (TR-V3-B on loose texts; REVIEW)"
            rc = _room_class(en, ar) if (occs or name_basis) else "UNKNOWN"
            phys = s.get("physical_status") == T.CERTIFIED
            status = COMPUTED if s["status"] == T.CERTIFIED else (REVIEW if phys else REVIEW)
            rid = f"{fl}-{'Z' if cls == 'OPEN_PLAN_ZONE' else 'T' if cls.startswith('OPENING') else 'R'}" \
                  f"{len([r for r in out['rows'] if r['floor'] == fl]) + 1:02d}"
            vs = [v for v in vd["items"] if v["floor"] == fl and v.get("site") == s["site_id"]]
            out["rows"].append({
                "id": rid, "floor": fl, "site": s["site_id"], "class": cls.split(" ")[0], "room_class": rc,
                "name_en": en or ("UNKNOWN" if not occs else ""), "name_ar": ar, "decode_states": dst,
                "name_basis": name_basis, "contains_stair": (s.get("contents") or {}).get("STAIR_GEOMETRY", 0) > 0,
                "label_occurrences": occs, "area_m2": _r(area), "perimeter_m": _r(per), "effective_width_m": _r(w, 3),
                "status": status, "site_status": s["status"], "physical_status": s.get("physical_status"),
                "issues": s["issues"], "voids": [v["id"] for v in vs],
                "void_area_m2": _r(sum(v["area_in_site_m2"] for v in vs)),
                "boundary_role_lengths_m": {k: _r(v * u / 1000.0) for k, v in sorted(s["boundary_role_lengths"].items())},
                "_polygon": P})
        out["floors"][fl] = dict(sorted(counts.items()))
    _shafts(ctx, out)
    return out


def _shafts(ctx, out):
    """An unnamed room repeated at the same sheet position with the same size on EVERY storey is a vertical shaft
    candidate (lift / duct): no floor or ceiling finish is measured in it; the owner confirms (question)."""
    def key(r):
        b = ctx["sheets_by_floor"][r["floor"]]["bounds"]
        xs = [p[0] for p in r["_polygon"]]
        ys = [p[1] for p in r["_polygon"]]
        return (round((min(xs) - b[0]) / 50.0), round((min(ys) - b[1]) / 50.0), round((max(xs) - min(xs)) / 50.0),
                round((max(ys) - min(ys)) / 50.0))
    groups = defaultdict(list)
    for r in out["rows"]:
        if r["class"] == "UNNAMED_ROOM" and not r["name_basis"]:
            groups[key(r)].append(r)
    for g in groups.values():
        if len({r["floor"] for r in g}) == len(FLOORS):
            for r in g:
                r["room_class"] = "SHAFT"
                r["shaft_evidence"] = f"same position and size on {', '.join(sorted(x['floor'] for x in g))}"


# ================================================================== voids
def voids(ctx) -> dict:
    """Floor voids from a VOID label (English VOID or decoded منور / فراغ) and positive outline evidence:
    X-RECT  a full diagonal of a rectangle plus a second segment from another corner along the other diagonal
    ARCS    concentric arcs around the label (>= 90 deg in total at the smallest radius enclosing it)
    The void polygon is clipped to the site that holds the label. No evidence -> VOID_EXTENT_UNRESOLVED."""
    fonts = _fonts(ctx)
    items = []
    for fl in FLOORS:
        inp = ctx["a2_raw"][fl]["inp"]
        res = ctx["a2_raw"][fl]["res"]
        texts = []
        for t in inp.texts:
            if t.x is None or not t.value:
                continue
            fam = LT.font_family(fonts.get(t.identity.source_handle, ""))
            val = LT.decode(t.value, fam)["text"] if fam else t.value
            if (t.value.strip().upper() in VOID_WORDS) or (fam and any(LT.normalise(w) in LT.normalise(val) for w in VOID_AR)):
                texts.append((t, val))
        seen = set()
        for t, val in sorted(texts, key=lambda z: z[0].identity.key):
            sid, _ = T.locate(res["_arr"], res["sites"], (t.x, t.y), 1.0)
            key = (sid, round(t.x, -2), round(t.y, -2))
            occ = (t.identity.instance_handles or ("",))[0]
            if (sid, occ) in seen:
                continue
            seen.add((sid, occ))
            site = next((s for s in res["sites"] if s["site_id"] == sid), None)
            shape, how = _x_rect(inp, t.x, t.y)
            if shape is None:
                shape, how = _arc_disc(inp, t.x, t.y)
            sp = Polygon(_poly(res, site)).buffer(0) if site else None
            if shape is not None and sp is not None and not sp.is_empty:
                clip = shape.intersection(sp)
                if clip.geom_type == "MultiPolygon":
                    clip = max(clip.geoms, key=lambda g: g.area)
            else:
                clip = None
            a = clip.area / 1e6 if clip is not None and not clip.is_empty else None
            items.append({"id": f"{fl}-V{len([i for i in items if i['floor'] == fl]) + 1:02d}", "floor": fl,
                          "label": t.identity.key, "label_value": val, "site": sid, "evidence": how,
                          "area_m2": _r(shape.area / 1e6) if shape is not None else None,
                          "area_in_site_m2": _r(a) if a else 0.0,
                          "state": COMPUTED if a else "VOID_EXTENT_UNRESOLVED",
                          "_polygon": list(clip.exterior.coords) if a and clip.geom_type == "Polygon" else None,
                          "_key": key})
    return {"items": items, "rule": "VOID label + positive outline (X-marked rectangle or concentric arcs), clipped to "
                                    "the site holding the label; floor finish excludes it, the ceiling of the storey "
                                    "below excludes its projection (double height), the ceiling of its own storey keeps it"}


def _segs_near(inp, x, y, r):
    for p in inp.parts:
        if p.kind != "SEGMENT":
            continue
        g = p.geometry
        if min(g[0], g[2]) - r <= x <= max(g[0], g[2]) + r and min(g[1], g[3]) - r <= y <= max(g[1], g[3]) + r:
            yield p


def _x_rect(inp, x, y):
    cands = [p for p in _segs_near(inp, x, y, 500.0)
             if abs(p.geometry[2] - p.geometry[0]) > 1000 and abs(p.geometry[3] - p.geometry[1]) > 1000]
    best = None
    for a in cands:
        g = a.geometry
        x0, x1 = sorted((g[0], g[2]))
        y0, y1 = sorted((g[1], g[3]))
        if not (x0 < x < x1 and y0 < y < y1):
            continue
        d1 = ((g[2] - g[0]), (g[3] - g[1]))
        other = [(x0, y1), (x1, y0)] if d1[0] * d1[1] > 0 else [(x0, y0), (x1, y1)]
        for b in cands:
            if b is a:
                continue
            h = b.geometry
            for (px, py), (qx, qy) in (((h[0], h[1]), (h[2], h[3])), ((h[2], h[3]), (h[0], h[1]))):
                for cx, cy in other:
                    if math.hypot(px - cx, py - cy) > 5.0:
                        continue
                    ox, oy = (x0 + x1) - cx, (y0 + y1) - cy                  # the opposite corner
                    v, w = (qx - px, qy - py), (ox - cx, oy - cy)
                    lv, lw = math.hypot(*v), math.hypot(*w)
                    if lv > 0.3 * lw and LineString([(px, py), (qx, qy)]).crosses(LineString([(g[0], g[1]), (g[2], g[3])])) \
                            and v[0] * w[0] + v[1] * w[1] > 0.9 * lv * lw:
                        r = Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
                        if best is None or r.area < best[0].area:
                            best = (r, {"rule": "X-RECT", "diagonal": a.identity.key, "second": b.identity.key,
                                        "rect_mm": [round(x1 - x0, 1), round(y1 - y0, 1)]})
    return best if best else (None, None)


def _arc_disc(inp, x, y):
    fam = defaultdict(float)
    for p in inp.parts:
        if p.kind != "ARC":
            continue
        g = p.geometry
        d = math.hypot(x - g[0], y - g[1])
        if g[2] > d and g[2] < 3000.0:
            fam[(round(g[0], 1), round(g[1], 1), round(g[2], 1))] += (g[4] - g[3]) % (2 * math.pi)
    ok = sorted(k for k, sw in fam.items() if sw >= math.pi / 2)
    if not ok:
        return None, None
    cx, cy, r = min(ok, key=lambda k: k[2])
    return Point(cx, cy).buffer(r, 64), {"rule": "ARCS", "centre": [cx, cy], "radius_mm": r,
                                         "sweep_deg": round(math.degrees(fam[(cx, cy, r)]), 1)}


# ================================================================== finishes
def _bands(ctx, fl):
    sh = ctx["b2a"]["sheets"][fl]
    return [({"type": o["type"], "D_cm": o["D_cm"], "bound": o["state"] != "BAND_TYPE_CONFLICT"},
             Polygon([tuple(p) for p in o["band_polygon"]])) for o in sh["occurrences"]]


def _cycle_edges(res, s, u):
    """[(points, roles, sources, length_m)] per cycle edge, arcs as polylines."""
    arr = res["_arr"]
    out = []
    for k, fw in s["cycle"]:
        e = arr.edges[k]
        if e["kind"] == "S":
            pts = [arr.nodes[e["n0"]], arr.nodes[e["n1"]]]
            if not fw:
                pts = pts[::-1]
        else:
            pr = e["prim"]
            n = max(int(abs(e["t1"] - e["t0"]) / math.radians(5)), 2)
            ts = [e["t0"] + (e["t1"] - e["t0"]) * i / n for i in range(n + 1)]
            pts = [pr.point(t) for t in (ts if fw else ts[::-1])]
        L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])) * u / 1000.0
        out.append((pts, sorted(e.get("roles") or ()), sorted(e.get("sources") or ()), L))
    return out


def _edge_kind(roles, sources):
    if any(x.startswith("CLOSURE|DRAFTING_GAP") for x in sources):
        return "DRAFTING_JOIN"
    if any(x.startswith("CLOSURE|GLAZED") for x in sources) or "GLAZING_BOUNDARY" in roles:
        return "GLAZING"
    if any(x.startswith("CLOSURE|") for x in sources) or "OPENING_BOUNDARY" in roles:
        return "OPENING"
    if any(x.startswith("TC|") or x.startswith("TCL") for x in sources):
        return "WALL_END_CLOSURE"
    return "WALL"


def finishes(ctx, rm, vd) -> dict:
    rows, faces = [], []
    ivs = {iv["from"]: iv for iv in ctx["b2a"]["intervals"]}
    for r in rm["rows"]:
        if r["class"] not in ("ROOM", "OPEN_PLAN_ZONE", "UNNAMED_ROOM") or r["room_class"] in ("SHAFT", "ROOF", "EXTERNAL"):
            continue
        fl = r["floor"]
        res = ctx["a2_raw"][fl]["res"]
        u = ctx["a2_raw"][fl]["inp"].unit_native_to_mm or 1.0
        s = next(x for x in res["sites"] if x["site_id"] == r["site"])
        reg = ctx["b2a"]["registration"][fl]
        sh = ctx["b2a"]["sheets"][fl]
        plate = sh["_plate"]
        t_cm = sh["slab"]["sheet_thickness_tags_cm"][0] if len(sh["slab"]["sheet_thickness_tags_cm"]) == 1 else None
        bands = _bands(ctx, fl)
        dx, dy = reg["translation"] if reg["state"] == "REGISTERED" else (None, None)
        rc = r["room_class"]
        wet = rc in ("WET", "SERVICE")
        # ---------------- floor and ceiling
        void_own = r["void_area_m2"] or 0.0
        below = _void_above(ctx, vd, fl, r)                     # voids of the storey above over this room
        floor_area = r["area_m2"] - void_own
        ceil_area = r["area_m2"] - below
        floor_mat = ("TILE (type BY_SPEC)", "URBAN_FALLBACK URBAN-WET-FLOOR-TILED@v1") if wet else \
            ("PORCELAIN", "URBAN_FALLBACK URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1") if rc == "DRY" else \
            (UM3.BY_SPEC, "no default for this room class")
        # ---------------- wall faces
        room_poly = Polygon(r["_polygon"]) if len(r["_polygon"]) >= 3 else None
        if dx is not None and room_poly is not None and room_poly.is_valid:
            from shapely.affinity import translate
            rp = translate(room_poly, xoff=dx, yoff=dy)
            over = [o for o, bp in bands if bp.intersects(rp.buffer(-AP.EPS)) or bp.buffer(AP.EPS).intersects(rp.exterior)]
            ctrl = max((o["D_cm"] for o in over if o["bound"]), default=None)
            room_ctrl = None if any(not o["bound"] for o in over) else (ctrl if ctrl is not None else t_cm)
        else:
            room_ctrl = None
        iv = ivs.get(fl)
        edges = _cycle_edges(res, s, u)
        gross = defaultdict(float)
        blocked_len = 0.0
        openings_w = 0.0
        open_edges = 0.0
        sk_len = 0.0
        corners = 0
        for i, (pts, roles, srcs, Lm) in enumerate(edges):
            kind = _edge_kind(roles, srcs)
            if kind == "DRAFTING_JOIN":
                continue
            if kind in ("OPENING", "GLAZING"):
                openings_w += Lm
            if kind == "WALL_END_CLOSURE":
                open_edges += Lm
                continue
            if kind == "WALL":
                sk_len += Lm
            for a, b in zip(pts, pts[1:]):
                if dx is None:
                    blocked_len += math.hypot(b[0] - a[0], b[1] - a[1]) * u / 1000.0
                    continue
                A, B = (a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy)
                for pc in G.face_pieces((A, B), bands, plate, t_cm, eps=AP.EPS):
                    hts = FH.wall_heights(interval=iv, term=pc["termination"], room_ctrl_D_cm=room_ctrl, wet=wet,
                                          buildup_above_m=BUILDUP["parameters"]["buildup_m"])
                    Lp = pc["length"] * u / 1000.0
                    rec = {"room": r["id"], "floor": fl, "edge": i, "edge_kind": kind, "length_m": _r(Lp),
                           "termination": pc["termination"]["type"], "member": pc["termination"].get("member"),
                           "D_cm": pc["termination"].get("D_cm")}
                    for q in ("BLOCKWORK", "PLASTER", "PAINT", "WALL_TILE"):
                        h = hts[q].get("height_m")
                        rec[q.lower() + "_h_m"] = h
                        if q == "PAINT" and wet:
                            continue
                        if q == "WALL_TILE" and not wet:
                            continue
                        if h is None:
                            gross[q + "_BLOCKED_LEN"] += Lp
                        else:
                            gross[q] += Lp * h
                    faces.append(rec)
        # convex (external) corners of the room polygon -> corner beads
        if room_poly is not None and room_poly.is_valid:
            P = list(room_poly.exterior.coords)[:-1]
            ccw = room_poly.exterior.is_ccw
            for k in range(len(P)):
                a, b, c = P[k - 1], P[k], P[(k + 1) % len(P)]
                la, lc = math.hypot(b[0] - a[0], b[1] - a[1]), math.hypot(c[0] - b[0], c[1] - b[1])
                if la * u < 200.0 or lc * u < 200.0:
                    continue                                           # polyline of a curve, not a wall corner
                cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
                if (cr < 0) == ccw and abs(cr) / (la * lc) > math.sin(math.radians(30)):
                    corners += 1                                       # reflex vertex of the room = projecting corner
        plaster_h = _modal(faces, r["id"], "plaster_h_m")
        row = {
            "room": r["id"], "floor": fl, "name_en": r["name_en"], "name_ar": r["name_ar"], "room_class": rc,
            "class": r["class"], "status": r["status"],
            "floor_area_m2": _r(floor_area), "floor_formula": f"site {r['area_m2']:.3f} - void {void_own:.3f}",
            "floor_material": floor_mat[0], "floor_material_authority": floor_mat[1],
            "floor_under_joinery": "included (OD-V3-2: floor finish continues beneath fixed joinery)",
            "ceiling_area_m2": _r(ceil_area), "ceiling_formula": f"site {r['area_m2']:.3f} - double-height below void {below:.3f}",
            "ceiling_material": UM3.BY_SPEC, "ceiling_material_authority": "URBAN-CEILING-QUANTITY-WITHOUT-MATERIAL@v1",
            "skirting_m": None if rc == "WET" or rc == "SERVICE" else _r(sk_len),
            "skirting_rule": ("none: wet / service room with full-height wall tile (URBAN-NO-SKIRTING-FULL-TILE-WET@v1)"
                              if wet else "wall edges of the room boundary; openings and open edges excluded"),
            "opening_widths_m": _r(openings_w), "open_edges_m": _r(open_edges),
            "blockwork_gross_m2": _r(gross["BLOCKWORK"]), "plaster_gross_m2": _r(gross["PLASTER"]),
            "paint_gross_m2": None if wet or (gross["PAINT_BLOCKED_LEN"] and not gross["PAINT"]) else _r(gross["PAINT"]),
            "wall_tile_gross_m2": (None if gross["WALL_TILE_BLOCKED_LEN"] and not gross["WALL_TILE"] else _r(gross["WALL_TILE"]))
            if wet else None,
            "faces_blocked_length_m": _r(gross["PLASTER_BLOCKED_LEN"] + blocked_len),
            "paint_blocked_length_m": _r(gross["PAINT_BLOCKED_LEN"] + gross["WALL_TILE_BLOCKED_LEN"]),
            "room_controlling_soffit_cm": room_ctrl,
            "paint_height_authority": f"URBAN_FALLBACK build-up {BUILDUP['parameters']['buildup_m']} m (OD-V3-1) + "
                                      f"URBAN-PAINT-TO-FINISHED-CEILING@v1",
            "opening_deduction": "BLOCKED_OPENING_HEIGHT (gross published; opening widths listed)" if openings_w else "NONE",
            "corner_beads_nr": corners, "corner_bead_m": _r(corners * plaster_h) if plaster_h else None,
            "cornice_m": _r(sk_len + openings_w), "cornice_status": "GEOMETRY_ONLY (cornice existence by specification)",
            "spatter_dash_m2": _r(gross["PLASTER"]), "spatter_dash_status": "GEOMETRY_ONLY (coverage method by owner)"}
        row["wall_state"] = (COMPUTED if row["faces_blocked_length_m"] == 0 else PARTIAL)
        rows.append(row)
    return {"rows": rows, "faces": faces, "policy": FH3.policy_record(),
            "rules": {"floor": "site area - own void", "ceiling": "site area - projection of the void of the storey above",
                      "walls": "room boundary edges split by beam coverage (finish_height_v3); heights per piece",
                      "paint / wall tile": "structural interval - build-up (URBAN_FALLBACK 0.10 m) - controlling soffit - 0.150"}}


def _modal(faces, rid, key):
    c = Counter(f[key] for f in faces if f["room"] == rid and f.get(key) is not None)
    return c.most_common(1)[0][0] if c else None


def _void_above(ctx, vd, fl, r):
    """Area of this room lying under a void of the storey above (double height: no ceiling at this level)."""
    up = {"GF": "1F", "1F": "2F"}.get(fl)
    if not up:
        return 0.0
    gb, ub = ctx["sheets_by_floor"][fl]["bounds"], ctx["sheets_by_floor"][up]["bounds"]
    dx, dy = gb[0] - ub[0], gb[1] - ub[1]
    rp = Polygon(r["_polygon"]).buffer(0) if len(r["_polygon"]) >= 3 else None
    if rp is None or rp.is_empty:
        return 0.0
    tot = 0.0
    for v in vd["items"]:
        if v["floor"] != up or not v.get("_polygon"):
            continue
        vp = Polygon([(x + dx, y + dy) for x, y in v["_polygon"]])
        tot += rp.intersection(vp).area / 1e6
    return tot
