"""ALSENAN V3 - structure completion, blockwork, openings / lintels, stairs and deterministic rebar.

Sources (ST7757.pdf, read as images; ST7757.dxf / P7757.dxf geometry):
  p.3  GROUND BEAMS PLAN   untagged ground-beam bands (double lines, 300 mm), two slab zones "T=10cm, 5Ø10/m E.W."
  p.8  general notes        cover 2.5 cm (7 cm against soil), development / lap 70Ø tension, 40Ø compression
  p.13 typical details      isolated footing (bottom bars drawn straight; 10 cm plain concrete 10 cm beyond; insulation
                            membrane; two layers liquid waterproofing on all surfaces in contact with earth), ground beam
                            sections by length, LINTEL SCHEDULE by opening width
  p.7  pool / dome details  dome span 4.42 m, rise 1.90 m, shell 10 cm
  schedules sheet           column ties "6Ø8/m"; simple-beam schedule header "STIRRUPS/m"
Rebar: NET_DESIGN_WEIGHT (straight lengths the source supports) and PROCUREMENT_WEIGHT_INCL_LAPS (+ laps only where a
continuous bar exceeds the 12 m stock length) per URBAN-REBAR-NET-AND-PROCUREMENT@v1; hooks / bends / stirrup closing
only from an explicit detail, else BLOCKED_DETAILING (the bar set is then PARTIAL: its straight weight is shown, never
its total). Never kg/m3.
"""

from __future__ import annotations

import math
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

import alsenan_phase_a as AP
import alsenan_phase_a3 as A3
import alsenan_phase_b2a as B2A
import alsenan_v3_geom as G
from engine.source import canonical_input as CI, finish_height as FH, topology as T
from engine.source import urban_methods_v3 as UM3

FLOORS = ("GF", "1F", "2F")
COVER = {"member": 0.025, "soil": 0.07}                     # p.8 note 22
LAP = {"tension": 70, "compression": 40}                     # p.8 note 9 (x bar diameter)
STOCK_M = UM3.resolve("URBAN-REBAR-NET-AND-PROCUREMENT@v1")["parameters"]["stock_length_m"]
GB_SECTIONS = [  # p.13 ground beams (interior), by length
    {"max_m": 2.5, "B": 0.30, "D": 0.30, "top": (3, 14), "bottom": [(3, 14), (3, 14)], "stirrup": (8, 0.15)},
    {"max_m": 5.0, "B": 0.30, "D": 0.40, "top": (3, 14), "bottom": [(3, 14), (3, 14)], "stirrup": (8, 0.15)},
    {"max_m": 1e9, "B": 0.30, "D": 0.60, "top": (3, 16), "bottom": [(3, 16), (3, 16)], "stirrup": (8, 0.15)}]
GB_EXTERIOR = {"B": 0.30, "D": None, "top": (3, 16), "side": (2, 12, 0.30), "bottom": [(6, 16)], "stirrup": (8, 0.15),
               "depth": "FOLLOW ARCH. (outer normal ground level to GF slab level) - not printed"}
LINTELS = [  # p.13 LINTEL SCHEDULE: max opening width cm -> depth cm, bottom, top, stirrups per m
    (100, 20, (2, 12), (2, 10), (5, 8)), (200, 20, (2, 14), (2, 12), (5, 8)), (300, 30, (3, 16), (3, 14), (5, 8)),
    (500, 40, (3, 18), (3, 14), (5, 8)), (750, 55, (4, 18), (3, 14), (5, 8))]
LINTEL_BEARING_M = 0.40                                      # p.13 MIN. 40 cm each side
PARAPET_H_M = 0.50                                           # sections A-A / B-B (A2 vertical transcription)
DOME = {"span_m": 4.42, "rise_m": 1.90, "shell_m": 0.10, "bars": "Ø12/15 cm"}


def kgm(d_mm):
    return d_mm * d_mm / 162.0


def _r(v, n=6):
    return None if v is None else round(v, n)


# ================================================================== bar sets
def barset(element, ref, floor, *, dia, count, length_m, shape="STRAIGHT", hook=None, run_m=None, lap_kind="tension",
           basis="", status_extra=None):
    """One bar set: count x length. hook: None = no hook by the detail (straight, source), "BLOCKED" = a hook / closing
    exists but its length is not in the source, or a number (m per bar from a detail)."""
    net_len = count * length_m
    hook_add = 0.0 if hook is None else (None if hook == "BLOCKED" else count * hook)
    run = run_m if run_m is not None else length_m
    laps = 0
    if run > STOCK_M:
        lap = LAP[lap_kind] * dia / 1000.0
        laps = math.ceil((run - STOCK_M) / (STOCK_M - lap))
    lap_add = count * laps * LAP[lap_kind] * dia / 1000.0
    k = kgm(dia)
    total = None if hook_add is None else net_len + hook_add
    st = "COMPUTED" if hook_add is not None else "PARTIAL"
    if status_extra:
        st = status_extra
    return {"element": element, "ref": ref, "floor": floor, "dia_mm": dia, "count": count, "shape": shape,
            "straight_length_m": _r(length_m), "straight_total_m": _r(net_len),
            "hook_bend_addition_m": _r(hook_add) if hook_add is not None else "BLOCKED_DETAILING",
            "lap_addition_m": _r(lap_add), "laps_per_bar": laps, "total_bar_length_m": _r(total),
            "kg_per_m": _r(k, 4), "net_design_weight_kg": _r(total * k, 3) if total is not None else None,
            "straight_weight_kg": _r(net_len * k, 3),
            "procurement_weight_kg": _r((total + lap_add) * k, 3) if total is not None else None,
            "status": st, "basis": basis,
            "formula": f"{count} x {length_m:.3f} m x {k:.3f} kg/m" + ("" if hook is None else " + hooks")}


# ================================================================== ground-beam sheet
def ground(ctx, work) -> dict:
    S = A3._blob(ctx, Path(work), "ST7757.dxf")
    sb = ctx["structural_sheets"]["GROUND_BEAMS"]["bounds"]
    lay = lambda p: CI.effective_layer(p)[0]
    segs = [p for p in S["parts"] if p.kind == "SEGMENT" and lay(p) == "1" and AP.in_box(p.geometry[0], p.geometry[1], sb)]
    cols = [Polygon(B2A._rect_poly(r)) for r in B2A._col_rects(S, sb)]
    bands = _pair_bands(segs, width=300.0, tol=12.0)
    arcs = [p for p in S["parts"] if p.kind == "ARC" and lay(p) == "1" and AP.in_box(p.geometry[0], p.geometry[1], sb)]
    bands += _arc_bands(arcs, width=300.0, tol=12.0)
    union = unary_union([b["poly"] for b in bands] + cols)
    zones_txt = [t for t in S["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, sb) and "T=" in t.value]
    mesh_txt = [t for t in S["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, sb) and "E.W" in t.value]
    comps = list(getattr(union, "geoms", [union]))
    zones = []
    for z, t in enumerate(sorted(zones_txt, key=lambda q: q.identity.key)):
        pt = Point(t.x, t.y)
        hit = [Polygon(c.exterior) for c in comps if Polygon(c.exterior).contains(pt)]
        if not hit:
            zones.append({"id": f"ZONE-{z + 1}", "label": t.identity.key, "state": "BLOCKED_ZONE_NOT_CLOSED"})
            continue
        outer = min(hit, key=lambda p: p.area)
        slab = outer.difference(union)
        m = min(mesh_txt, key=lambda q: math.hypot(q.x - t.x, q.y - t.y)) if mesh_txt else None
        zones.append({"id": f"ZONE-{z + 1}", "label": t.identity.key, "thickness_text": t.value.strip(),
                      "mesh_text": m.value.strip() if m else None, "outer_area_m2": _r(outer.area / 1e6),
                      "slab_area_m2": _r(slab.area / 1e6), "_outer": outer, "_slab": slab,
                      "level": None})
    # band spans between columns, exterior flag
    zone_outers = [z["_outer"] for z in zones if "_outer" in z]
    col_u = unary_union(cols) if cols else None
    spans = []
    for b in bands:
        pieces = b["poly"].difference(col_u) if col_u is not None else b["poly"]
        for g in getattr(pieces, "geoms", [pieces]):
            if g.is_empty or g.area < 300 * 300:
                continue
            L = _band_len(g, b)
            ext = any(z.exterior.distance(g) < 5.0 for z in zone_outers)
            spans.append({"band": b["id"], "length_m": _r(L / 1000.0), "exterior": ext, "_poly": g})
    for i, s in enumerate(sorted(spans, key=lambda z: (z["band"], -z["length_m"]))):
        s["id"] = f"GB-{i + 1:03d}"
    return {"bands": len(bands), "columns_on_sheet": len(cols), "zones": zones, "spans": spans,
            "source": "ST7757 GROUND BEAMS PLAN (layer 1 double lines, 300 mm), p.13 typical ground-beam sections"}


def _pair_bands(segs, width, tol):
    lines = []
    for p in segs:
        g = p.geometry
        L = math.hypot(g[2] - g[0], g[3] - g[1])
        if L < 300:
            continue
        lines.append((p.identity.key, g, L))
    out, used = [], set()
    for i, (ka, a, la) in enumerate(lines):
        ua = ((a[2] - a[0]) / la, (a[3] - a[1]) / la)
        na = (-ua[1], ua[0])
        best = None
        for kb, b, lb in lines[i + 1:]:
            ub = ((b[2] - b[0]) / lb, (b[3] - b[1]) / lb)
            if abs(ua[0] * ub[1] - ua[1] * ub[0]) > 0.01:
                continue
            off = abs((b[0] - a[0]) * na[0] + (b[1] - a[1]) * na[1])
            if abs(off - width) > tol:
                continue
            s = sorted([0.0, la])
            t = sorted([(b[0] - a[0]) * ua[0] + (b[1] - a[1]) * ua[1], (b[2] - a[0]) * ua[0] + (b[3] - a[1]) * ua[1]])
            ov = min(s[1], t[1]) - max(s[0], t[0])
            if ov < 300:
                continue
            if best is None or ov > best[0]:
                best = (ov, kb, b, max(s[0], t[0]), min(s[1], t[1]))
        if best is None:
            continue
        ov, kb, b, s0, s1 = best
        sign = 1 if (b[0] - a[0]) * na[0] + (b[1] - a[1]) * na[1] > 0 else -1
        p0 = (a[0] + ua[0] * s0, a[1] + ua[1] * s0)
        p1 = (a[0] + ua[0] * s1, a[1] + ua[1] * s1)
        poly = Polygon([p0, p1, (p1[0] + sign * na[0] * width, p1[1] + sign * na[1] * width),
                        (p0[0] + sign * na[0] * width, p0[1] + sign * na[1] * width)])
        key = tuple(sorted((ka, kb)))
        if key in used:
            continue
        used.add(key)
        out.append({"id": "+".join(k.split("|")[1] for k in key), "poly": poly, "u": ua})
    # remove duplicates (overlapping bands from fragmented lines)
    keep = []
    for b in sorted(out, key=lambda z: -z["poly"].area):
        if any(b["poly"].intersection(k["poly"]).area > 0.8 * b["poly"].area for k in keep):
            continue
        keep.append(b)
    return keep


def _arc_bands(arcs, width, tol):
    """Curved ground beams: two concentric arcs whose radii differ by the beam width -> annular sector."""
    out = []
    for i, a in enumerate(arcs):
        ga = a.geometry
        for b in arcs[i + 1:]:
            gb = b.geometry
            if math.hypot(ga[0] - gb[0], ga[1] - gb[1]) > 5.0 or abs(abs(ga[2] - gb[2]) - width) > tol:
                continue
            r0, r1 = sorted((ga[2], gb[2]))
            a0, a1 = ga[3], ga[4]
            sweep = (a1 - a0) % (2 * math.pi)
            n = max(int(math.degrees(sweep) / 3), 4)
            outer = [(ga[0] + r1 * math.cos(a0 + sweep * k / n), ga[1] + r1 * math.sin(a0 + sweep * k / n)) for k in range(n + 1)]
            inner = [(ga[0] + r0 * math.cos(a0 + sweep * k / n), ga[1] + r0 * math.sin(a0 + sweep * k / n)) for k in range(n, -1, -1)]
            poly = Polygon(outer + inner).buffer(0)
            out.append({"id": "ARC:" + "+".join(sorted(x.identity.key.split("|")[1] for x in (a, b))), "poly": poly,
                        "u": None, "arc_len": (r0 + r1) / 2 * sweep})
    return out


def _band_len(g, b):
    if b.get("u") is None:                                      # curved band: centreline arc length x share kept
        return b["arc_len"] * g.area / b["poly"].area
    u = b["u"]
    xs = [x * u[0] + y * u[1] for x, y in g.exterior.coords]
    return max(xs) - min(xs)


def ground_items(gr) -> dict:
    beams, rebar = [], []
    for s in gr["spans"]:
        L = s["length_m"]
        if s["exterior"]:
            beams.append({"id": s["id"], "kind": "EXTERIOR", "length_m": L, "B_m": 0.30, "D_m": None, "volume_m3": None,
                          "status": "BLOCKED", "why": GB_EXTERIOR["depth"],
                          "formula": f"{L:.3f} x 0.30 x D(follow arch.)"})
            continue
        sec = next(x for x in GB_SECTIONS if L <= x["max_m"])
        v = L * sec["B"] * sec["D"]
        beams.append({"id": s["id"], "kind": "INTERIOR", "length_m": L, "B_m": sec["B"], "D_m": sec["D"],
                      "volume_m3": _r(v), "status": "COMPUTED",
                      "section_rule": f"p.13 typical ground beam: length {L:.2f} m -> {int(sec['B']*100)}x{int(sec['D']*100)}",
                      "formula": f"{L:.3f} x {sec['B']:.2f} x {sec['D']:.2f} = {v:.3f} m3",
                      "blinding_m3": _r(L * (sec["B"] + 0.20) * 0.10),
                      "wp_sides_m2": _r(2 * L * sec["D"])})
        c = COVER["soil"]
        n, d = sec["top"]
        rebar.append(barset("GROUND_BEAM", s["id"] + " top", "FOUNDATION", dia=d, count=n, length_m=L - 2 * 0.0, hook="BLOCKED",
                            basis="p.13 section; bar run = clear span between columns; end anchorage into the columns not "
                                  "detailed (BLOCKED_DETAILING)"))
        for (n, d) in sec["bottom"]:
            rebar.append(barset("GROUND_BEAM", s["id"] + " bottom", "FOUNDATION", dia=d, count=n, length_m=L, hook="BLOCKED",
                                basis="p.13 section"))
        sd, sp = sec["stirrup"]
        nst = int(math.floor(L / sp)) + 1
        per = 2 * (sec["B"] - 2 * c) + 2 * (sec["D"] - 2 * c)
        rebar.append(barset("GROUND_BEAM", s["id"] + " stirrups", "FOUNDATION", dia=sd, count=nst, length_m=per,
                            shape="CLOSED_LINK", hook="BLOCKED",
                            basis=f"p.13 Ø{sd}/{int(sp*100)}cm; link perimeter at 7 cm soil cover; closing hooks not detailed"))
    slabs = []
    for z in gr["zones"]:
        if "_slab" not in z:
            slabs.append({"id": z["id"], "status": "BLOCKED", "why": z["state"]})
            continue
        A = z["slab_area_m2"]
        t = 0.10
        slabs.append({"id": z["id"], "area_m2": A, "thickness_m": t, "volume_m3": _r(A * t), "status": "COMPUTED",
                      "formula": f"{A:.3f} m2 (zone {z['outer_area_m2']:.3f} - beam bands / columns) x 0.10",
                      "source": f"'{z['thickness_text']}' + '{z['mesh_text']}' printed in the zone"})
        b = z["_slab"].bounds
        for axis, (span, width) in (("X", (b[2] - b[0], b[3] - b[1])), ("Y", (b[3] - b[1], b[2] - b[0]))):
            bars_m = 5.0 * A                                  # 5 bars / m each way: length per m2 per direction = 5 m
            n = int(round(5.0 * width / 1000.0))
            rebar.append(barset("GROUND_SLAB", f"{z['id']} mesh {axis}", "FOUNDATION", dia=10, count=1, length_m=bars_m,
                                run_m=span / 1000.0, basis="5Ø10/m each way: 5 m of bar per m2 per direction (area x 5)",
                                status_extra="COMPUTED"))
            rebar[-1]["lap_addition_m"] = _r(n * _laps(span / 1000.0, 10) * LAP["tension"] * 10 / 1000.0)
            rebar[-1]["laps_per_bar"] = _laps(span / 1000.0, 10)
            rebar[-1]["procurement_weight_kg"] = _r((bars_m + rebar[-1]["lap_addition_m"]) * kgm(10), 3)
    return {"beams": beams, "slabs": slabs, "rebar": rebar}


def _laps(run, dia):
    if run <= STOCK_M:
        return 0
    lap = LAP["tension"] * dia / 1000.0
    return math.ceil((run - STOCK_M) / (STOCK_M - lap))


# ================================================================== footings, columns, beams rebar
def terminal(element, ref, floor, terminal_state, why, **audit) -> dict:
    """Control-plane R2: an admitted quantity-bearing object that yields no bar set still ends in a record. The
    record is BLOCKED (never in a total); what is known is kept under 'audit' and is never released."""
    rec = {"element": element, "ref": ref, "floor": floor, "status": "BLOCKED", "terminal_state": terminal_state,
           "why": f"{terminal_state}: {why}"}
    if audit:
        rec["audit"] = audit
    return rec


def footing_rebar(ctx) -> list:
    defs = {d["type"]: d for d in ctx["a3"]["rebar"]["definitions"] if d["element"] == "FOOTING"}
    out = []
    for i, f in enumerate(ctx["a3"]["footings"]["rows"]):
        ref = f"{f['type']} #{i + 1}"
        if not str(f.get("status", "")).startswith("COMPUTED"):
            out.append(terminal("FOOTING", ref + " bars", "FOUNDATION", "REBAR_BLOCKED_CONCRETE_NOT_ESTABLISHED",
                                f"footing concrete {f.get('status')}"))
            continue
        if f["type"] not in defs:
            out.append(terminal("FOOTING", ref + " bars", "FOUNDATION", "REBAR_BLOCKED_NO_DEFINITION",
                                f"no reinforcement definition for type {f['type']}"))
            continue
        d = defs[f["type"]]
        if not d.get("bars"):
            out.append(terminal("FOOTING", ref + " bars", "FOUNDATION", "REBAR_BLOCKED_SCHEDULE_CELL_UNREAD",
                                f"schedule cell for {f['type']} not parsed into bars", raw_fields=d.get("fields")))
            continue
        L, W = f["dims"]["L"]["m"], f["dims"]["W"]["m"]
        c = COVER["soil"]
        for key, span in (("long_bars", L), ("short_bars", W)):
            for b in d["bars"].get(key, []):
                if b.get("per_m"):
                    # a per-metre count is not a bar count: it needs the span-based consumer (Round 3)
                    out.append(terminal("FOOTING", f"{ref} {key}", "FOUNDATION",
                                        "REBAR_BLOCKED_PER_METRE_PENDING_CONSUMER_V2",
                                        f"{b['count']} Ø{b['dia_mm']} per metre; count over the footing not derived",
                                        per_m_count=b["count"], dia_mm=b["dia_mm"], span_m=span))
                    continue
                out.append(barset("FOOTING", f"{ref} {key}", "FOUNDATION", dia=b["dia_mm"], count=b["count"],
                                  length_m=span - 2 * c, hook=None,
                                  basis="p.13 typical footing: bottom bars drawn straight; length = side - 2 x 7 cm cover"))
        if d.get("boxed") and any("/m" in str(x) for x in d["boxed"]):
            # A3 stores the BOTTOM layer of a two-layer (FTB) footing under 'boxed': it is a per-metre mesh, not boxes
            out.append(terminal("FOOTING", ref + " bottom layer", "FOUNDATION",
                                "REBAR_BLOCKED_PER_METRE_PENDING_CONSUMER_V2",
                                f"two-layer footing BOTTOM layer {d['boxed']} (per metre) - consumer pending",
                                raw=d["boxed"]))
        elif d.get("boxed"):
            out.append({"element": "FOOTING", "ref": ref + " boxed bars", "floor": "FOUNDATION", "status": "BLOCKED",
                        "why": "boxed bar shape not dimensioned"})
    return out


def column_rebar(ctx) -> list:
    defs = {d["type"]: d for d in ctx["a3"]["rebar"]["definitions"] if d["element"] == "COLUMN"}
    ivs = {iv["from"]: iv["interval_m"] for iv in ctx["b2a"]["intervals"]}
    out = []
    for r in ctx["b2a"]["columns"]["rows"]:
        d = defs.get(r["type"])
        ref = f"{r['floor']} {r['type']} {r['tag_key'].split('|')[1]}"
        if r.get("state") == "NOT_IN_STOREY":
            continue                                   # the column type has no section in this storey (not admitted)
        if d is None or r.get("B_cm") is None:
            out.append(terminal("COLUMN", ref + " bars", r["floor"], "REBAR_BLOCKED_NO_DEFINITION",
                                f"no definition / section for {r['type']} ({r.get('state')})"))
            continue
        bars = d["bars"].get(r["storey_band"]) or []
        h = ivs.get(r["floor"])
        if r.get("volume_m3") is None:
            # D5: the occurrence's concrete is not established - its bars may not enter any verified total
            aud = sum(b["count"] * h * kgm(b["dia_mm"]) for b in bars) if h else None
            ties = None
            if h and r.get("D_cm"):
                B_, D_ = r["B_cm"] / 100.0, r["D_cm"] / 100.0
                ties = math.ceil(6 * h) * (2 * (B_ - 2 * COVER["member"]) + 2 * (D_ - 2 * COVER["member"])) * kgm(8)
            out.append(terminal("COLUMN", ref + " bars", r["floor"], "REBAR_BLOCKED_OCCURRENCE_NOT_ESTABLISHED",
                                f"column occurrence state {r.get('state')}: concrete not established",
                                occurrence_state=r.get("state"), vertical_straight_kg=_r(aud, 3) if aud else None,
                                ties_straight_kg=_r(ties, 3) if ties else None))
            continue
        for b in bars:
            out.append(barset("COLUMN", ref + " vertical", r["floor"], dia=b["dia_mm"], count=b["count"], length_m=h,
                              lap_kind="compression",
                              basis="storey interval; one compression lap 40Ø at each floor splice (procurement)"))
            out[-1]["lap_addition_m"] = _r(b["count"] * LAP["compression"] * b["dia_mm"] / 1000.0)
            out[-1]["procurement_weight_kg"] = _r((out[-1]["straight_total_m"] + out[-1]["lap_addition_m"]) * kgm(b["dia_mm"]), 3)
        B, D = r["B_cm"] / 100.0, r["D_cm"] / 100.0
        n = int(math.ceil(6 * h))
        per = 2 * (B - 2 * COVER["member"]) + 2 * (D - 2 * COVER["member"])
        out.append(barset("COLUMN", ref + " ties", r["floor"], dia=8, count=n, length_m=per, shape="CLOSED_LINK",
                          hook="BLOCKED", basis="schedule sheet: ST. OF COLUMN 6Ø8/m; closing hooks not detailed"))
    return out


def beam_rebar(ctx) -> list:
    defs = {d["type"]: d for d in ctx["a3"]["rebar"]["definitions"] if d["element"] == "BEAM"}
    out = []
    for fl in FLOORS:
        for o in ctx["b2a"]["sheets"][fl]["occurrences"]:
            d = defs.get(o["type"])
            ref = f"{fl} {o['type']} {o['tags'][0].split('|')[1] if o['tags'] else ''}"
            if d is None:
                st = ("REBAR_BLOCKED_PENDING_REBAR_CONSUMER_V2" if o["type"].startswith("CB") else
                      "REBAR_BLOCKED_NO_DEFINITION")
                out.append(terminal("BEAM", ref + " bars", fl, st,
                                    "continuous-beam definition read from the DXF schedule (V2 source reader); no "
                                    "rebar consumer yet" if st.endswith("V2") else f"no definition for {o['type']}",
                                    occurrence_state=o["state"]))
                continue
            if o["state"] != "MEASURED":
                out.append(terminal("BEAM", ref + " bars", fl, "REBAR_BLOCKED_OCCURRENCE_NOT_MEASURED",
                                    f"occurrence state {o['state']}", occurrence_state=o["state"]))
                continue
            Ls = o["lengths"].get("SUPPORT_CENTRELINE_LENGTH")
            Lc = o["lengths"].get("CLEAR_FACE_TO_FACE_LENGTH")
            if not Ls or not Lc:
                out.append(terminal("BEAM", ref + " bars", fl, "REBAR_BLOCKED_LENGTH_MISSING",
                                    "support-centreline or clear length not measured"))
                continue
            for pos in ("top", "bottom"):
                for b in d["bars"].get(pos, []):
                    out.append(barset("BEAM", f"{ref} {pos}", fl, dia=b["dia_mm"], count=b["count"], length_m=Ls,
                                      hook="BLOCKED",
                                      basis="support centreline length; anchorage / hooks at the supports not detailed"))
            for b in d["bars"].get("stirrups", []):
                B, D = o["B_cm"] / 100.0, o["D_cm"] / 100.0
                n = int(math.ceil(b["count"] * Lc))
                per = 2 * (B - 2 * COVER["member"]) + 2 * (D - 2 * COVER["member"])
                out.append(barset("BEAM", f"{ref} stirrups", fl, dia=b["dia_mm"], count=n, length_m=per,
                                  shape="CLOSED_LINK", hook="BLOCKED",
                                  basis="schedule header STIRRUPS/m x clear length; closing hooks not detailed"))
            if o["D_cm"] and o["D_cm"] > 60:
                out.append({"element": "BEAM", "ref": f"{ref} side bars", "floor": fl, "status": "BLOCKED",
                            "why": "p.8 note 21: 2/3/4 Ø12 by beam width - the width-to-count mapping is not printed"})
    return out


def strap_rebar(ctx) -> list:
    """D4: strap beams have definitions (element STRAP) but no rebar consumer yet - one terminal record each."""
    return [terminal("STRAP", f"FOUNDATION {s['type']} {s['mark_key'].split('|')[1]} bars", "FOUNDATION",
                     "REBAR_BLOCKED_NO_CONSUMER", f"strap beam {s['type']}: definition parsed, no rebar consumer",
                     concrete_status=s.get("status"))
            for s in ctx["a3"]["straps"]["rows"]]


# ================================================================== openings, lintels
def _opening_states(width_known) -> dict:
    """Control-plane R2: each opening attribute carries its own state; the record status is PARTIAL (count and width
    established, height not) - never COMPUTED while the height is BLOCKED (no default height is inserted)."""
    return {"count_state": "COMPUTED", "width_state": "COMPUTED" if width_known else "BLOCKED",
            "height_state_v2": "BLOCKED", "area_state": "BLOCKED_OPENING_AREA_HEIGHT"}


def openings(ctx, rooms) -> dict:
    rows = []
    for fl in FLOORS:
        res = ctx["a2_raw"][fl]["res"]
        doors = (res.get("roles") or {}).get("doors") or {}
        st = res.get("openings") or {}
        geom = {c.source_id: c.geometry for c in res.get("closures") or []}
        for occ in sorted(st):
            s = st[occ]
            if occ.startswith("GLAZED") or s.get("state") != "CLOSED":
                if occ in doors and s.get("state") != "CLOSED":
                    rows.append({"floor": fl, "id": f"{fl}-D-{occ}", "kind": "DOOR", "width_m": None, "status": "BLOCKED",
                                 "why": s.get("why"), **_opening_states(False)})
                continue
            a = geom.get(s.get("closure_a"))
            b = geom.get(s.get("closure_b"))
            w = math.hypot(a[2] - a[0], a[3] - a[1]) / 1000.0 if a else None
            t = (Point(a[0], a[1]).distance(LineString([(b[0], b[1]), (b[2], b[3])])) / 1000.0) if a and b else None
            kind = "DOUBLE_LEAF_DOOR" if s.get("rule") == "DOOR_IN_WALL_GAP_V1" else "DOOR"
            rows.append({"floor": fl, "id": f"{fl}-D-{occ}", "kind": kind, "width_m": _r(w, 3), "wall_t_m": _r(t, 3),
                         "height_m": None, "height_state": "BLOCKED_OPENING_HEIGHT (no door schedule / elevation value)",
                         "status": "PARTIAL", "rule": s.get("rule", "FROZEN_DOOR_CLOSURE"),
                         **_opening_states(w is not None)})
        for i, w in enumerate(ctx["a2_raw"][fl]["eri"]["glazing"]["windows"]):
            rows.append({"floor": fl, "id": f"{fl}-W{i + 1:02d}", "kind": "WINDOW", "width_m": _r(w["width_mm"] / 1000.0, 3),
                         "wall_t_m": _r(w["thickness_mm"] / 1000.0, 3), "height_m": None,
                         "height_state": "BLOCKED_OPENING_HEIGHT (no head / sill printed)", "status": "PARTIAL",
                         **_opening_states(True)})
    lint = []
    for o in rows:
        if o.get("width_m") is None:
            lint.append({"opening": o["id"], "floor": o["floor"], "status": "BLOCKED",
                         "why": "LINTEL_BLOCKED_NO_OPENING_WIDTH: opening closure not established"})
            continue
        wcm = o["width_m"] * 100.0
        sch = next((x for x in LINTELS if wcm <= x[0] + 0.5), None)
        if sch is None:
            lint.append({"opening": o["id"], "floor": o["floor"], "status": "BLOCKED",
                         "why": "opening wider than the lintel schedule (750 cm)"})
            continue
        B = o.get("wall_t_m")
        L = o["width_m"] + 2 * LINTEL_BEARING_M
        D = sch[1] / 100.0
        rec = {"opening": o["id"], "floor": o["floor"], "kind": o["kind"], "opening_width_m": o["width_m"],
               "schedule_row": f"<= {sch[0]} cm: B x {sch[1]}", "length_m": _r(L), "B_m": B, "D_m": D,
               "volume_m3": _r(L * B * D) if B else None, "status": "COMPUTED" if B else "BLOCKED",
               "why": None if B else "host wall thickness not measured",
               "formula": f"({o['width_m']:.3f} + 2 x 0.40) x {B if B else 'B'} x {D:.2f}"}
        lint.append(rec)
    return {"rows": rows, "lintels": lint}


def lintel_rebar(lint) -> list:
    out = []
    for l in lint:
        if l.get("status") != "COMPUTED":
            out.append(terminal("LINTEL", f"{l['opening']} lintel bars", l.get("floor") or l["opening"].split("-")[0],
                                "REBAR_BLOCKED_LINTEL_NOT_ESTABLISHED", l.get("why") or "lintel not established"))
            continue
        sch = next(x for x in LINTELS if l["opening_width_m"] * 100 <= x[0] + 0.5)
        L = l["length_m"] - 2 * COVER["member"]
        for pos, (n, d) in (("bottom", sch[2]), ("top", sch[3])):
            out.append(barset("LINTEL", f"{l['opening']} {pos}", l["floor"], dia=d, count=n, length_m=L,
                              basis="p.13 LINTEL SCHEDULE; straight bars over the lintel length less cover"))
        n_st = int(math.ceil(sch[4][0] * l["length_m"]))
        per = 2 * (l["B_m"] - 2 * COVER["member"]) + 2 * (l["D_m"] - 2 * COVER["member"])
        out.append(barset("LINTEL", f"{l['opening']} stirrups", l["floor"], dia=sch[4][1], count=n_st, length_m=per,
                          shape="CLOSED_LINK", hook="BLOCKED", basis="p.13 LINTEL SCHEDULE 5Ø8/M; closing hooks not detailed"))
    return out


# ================================================================== blockwork (wall bands)
def blockwork(ctx, rm) -> dict:
    rows = []
    for fl in FLOORS:
        res = ctx["a2_raw"][fl]["res"]
        u = ctx["a2_raw"][fl]["inp"].unit_native_to_mm or 1.0
        reg = ctx["b2a"]["registration"][fl]
        sh = ctx["b2a"]["sheets"][fl]
        plate = sh["_plate"]
        t_cm = sh["slab"]["sheet_thickness_tags_cm"][0] if len(sh["slab"]["sheet_thickness_tags_cm"]) == 1 else None
        bands = [({"type": o["type"], "D_cm": o["D_cm"], "bound": o["state"] != "BAND_TYPE_CONFLICT"},
                  Polygon([tuple(p) for p in o["band_polygon"]])) for o in sh["occurrences"]]
        iv = next((x for x in ctx["b2a"]["intervals"] if x["from"] == fl), None)
        interior_sites = {r["site"] for r in rm["rows"] if r["floor"] == fl}
        geom = {p.identity.key: p.geometry for p in ctx["a2_raw"][fl]["inp"].parts if p.kind == "SEGMENT"}
        for b in (res.get("wall_bands") or {}).get("bands") or []:
            if b["state"] != "WALL_BAND_ESTABLISHED":
                Lm = (b["interval"][1] - b["interval"][0]) * u / 1000.0
                rows.append({"floor": fl, "band": b["band_id"], "thickness_mm": round(float(b["width"]) * u),
                             "position": "UNRESOLVED_SIDES", "length_m": _r(Lm), "pieces": [], "area_m2": None,
                             "blocked_length_m": _r(Lm), "status": "BLOCKED",
                             "terminal_state": "BLOCKWORK_BLOCKED_AMBIGUOUS_BAND",
                             "why": f"wall band {b['state']}: masonry identity not established"})
                continue
            ga = geom.get(b["faces"][0])
            gb = geom.get(b["faces"][1]) if len(b["faces"]) > 1 else None
            if ga is None or gb is None:
                Lm = (b["interval"][1] - b["interval"][0]) * u / 1000.0
                rows.append({"floor": fl, "band": b["band_id"], "thickness_mm": round(float(b["width"]) * u),
                             "position": "UNRESOLVED_SIDES", "length_m": _r(Lm), "pieces": [], "area_m2": None,
                             "blocked_length_m": _r(Lm), "status": "BLOCKED",
                             "terminal_state": "BLOCKWORK_BLOCKED_FACE_GEOMETRY_MISSING",
                             "why": "a face segment of the band is not in the input parts"})
                continue
            ux, uy = b["axis"]
            nx, ny = -uy, ux
            oa = (ga[0] + ga[2]) / 2 * nx + (ga[1] + ga[3]) / 2 * ny
            ob = (gb[0] + gb[2]) / 2 * nx + (gb[1] + gb[3]) / 2 * ny
            om = (oa + ob) / 2
            s0, s1 = b["interval"]
            A = (s0 * ux + om * nx, s0 * uy + om * ny)
            B = (s1 * ux + om * nx, s1 * uy + om * ny)
            Lm = (s1 - s0) * u / 1000.0
            w = float(b["width"]) * u
            if w > 400.0:
                rows.append({"floor": fl, "band": b["band_id"], "thickness_mm": round(w), "position": "NOT_MASONRY",
                             "length_m": _r(Lm), "pieces": [], "area_m2": None, "blocked_length_m": _r(Lm),
                             "status": "EXCLUDED", "why": "band wider than 400 mm (not a block wall: stair / planter / "
                                                          "double line)"})
                continue
            mid = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
            side = []
            for sg in (1, -1):
                pt = (mid[0] + sg * nx * (w / 2 + 300.0) / u, mid[1] + sg * ny * (w / 2 + 300.0) / u)
                sid, _ = T.locate(res["_arr"], res["sites"], pt, 1.0)
                side.append(sid in interior_sites)
            pos = "INTERNAL" if all(side) else "EXTERNAL" if any(side) else "UNRESOLVED_SIDES"
            pcs = []
            if reg["state"] == "REGISTERED":
                dx, dy = reg["translation"]
                for pc in G.face_pieces(((A[0] + dx, A[1] + dy), (B[0] + dx, B[1] + dy)), bands, plate, t_cm, eps=AP.EPS):
                    h = FH.wall_heights(interval=iv, term=pc["termination"])["BLOCKWORK"]["height_m"]
                    pcs.append({"length_m": _r(pc["length"] * u / 1000.0), "termination": pc["termination"]["type"],
                                "member": pc["termination"].get("member"), "D_cm": pc["termination"].get("D_cm"),
                                "height_m": h})
            area = sum(p["length_m"] * p["height_m"] for p in pcs if p["height_m"] is not None)
            blocked = sum(p["length_m"] for p in pcs if p["height_m"] is None)
            rows.append({"floor": fl, "band": b["band_id"], "thickness_mm": round(w), "position": pos,
                         "length_m": _r(Lm), "pieces": pcs, "area_m2": _r(area), "blocked_length_m": _r(blocked),
                         "status": "COMPUTED" if blocked < 1e-6 and pcs else ("PARTIAL" if area else "BLOCKED"),
                         "formula": " + ".join(f"{p['length_m']:.2f} x {p['height_m']:.2f}" for p in pcs if p["height_m"])})
    # parapets: exposed roof edges (waterproofing plates), height from the sections
    par = parapets(ctx)
    return {"rows": rows, "parapets": par,
            "rule": "established wall bands; height per piece = structural interval - terminating member depth "
                    "(finish_height_v3 split); door / window openings are already outside the bands (net of openings "
                    "at full height); masonry over openings BLOCKED_OPENING_HEIGHT"}


def parapets(ctx) -> list:
    """Parapet = exposed roof edge: the top roof plate perimeter, and for each lower roof the edge of (plate - plate
    above) that does not run along the storey above. Height 0.50 m from sections A-A / B-B."""
    from shapely.affinity import translate
    sh = ctx["b2a"]["sheets"]
    out = []
    top = sh["2F"]["_gross"]
    if top is not None:
        out.append({"region": "2F ROOF (top)", "length_m": _r(top.length / 1000.0)})
    for lo, hi in (("1F", "2F"), ("GF", "1F")):
        (dx, dy), same = B2A._frame_offset(ctx, B2A.ROOF_SHEET[hi], B2A.ROOF_SHEET[lo])
        a, b = sh[lo]["_gross"], sh[hi]["_gross"]
        if a is None or b is None or not same:
            out.append({"region": f"{lo} ROOF exposed", "length_m": None})
            continue
        up = translate(b, xoff=dx, yoff=dy)
        ex = a.difference(up).buffer(-1.0).buffer(1.0)
        bd = ex.boundary
        shared = bd.intersection(up.buffer(50.0)).length
        out.append({"region": f"{lo} ROOF exposed (not under {hi})", "length_m": _r((bd.length - shared) / 1000.0),
                    "excluded_along_storey_above_m": _r(shared / 1000.0)})
    for p in out:
        L = p["length_m"]
        p.update(height_m=PARAPET_H_M, area_m2=_r(L * PARAPET_H_M) if L else None, status="COMPUTED" if L else "BLOCKED",
                 thickness="BY DETAIL (p.14 parapet detail) - not bound", formula=f"{L:.3f} x 0.50" if L else None)
    return out


# ================================================================== earth-contact waterproofing, blinding, dome, pool
def substructure(ctx, gi) -> dict:
    fo = []
    for f in ctx["a3"]["footings"]["rows"]:
        if not str(f.get("status", "")).startswith("COMPUTED"):
            continue
        L, W, H = f["dims"]["L"]["m"], f["dims"]["W"]["m"], f["dims"]["H"]["m"]
        fo.append({"type": f["type"], "wp_m2": _r(2 * (L + W) * H + L * W),
                   "membrane_m2": _r((L + 0.20) * (W + 0.20)),
                   "formula": f"2 x ({L:.2f} + {W:.2f}) x {H:.2f} + {L:.2f} x {W:.2f}"})
    gb = [b for b in gi["beams"] if b["status"] == "COMPUTED"]
    a = DOME["span_m"] / 2.0
    R = (a * a + DOME["rise_m"] ** 2) / (2 * DOME["rise_m"])
    area = 2 * math.pi * R * DOME["rise_m"]
    return {"footing_wp": fo, "footing_wp_m2": _r(sum(x["wp_m2"] for x in fo)),
            "footing_membrane_m2": _r(sum(x["membrane_m2"] for x in fo)),
            "ground_beam_wp_m2": _r(sum(b["wp_sides_m2"] for b in gb)),
            "ground_beam_blinding_m3": _r(sum(b["blinding_m3"] for b in gb)),
            "wp_rule": "p.13: two layers liquid waterproofing on all surfaces in contact with earth (footing sides + top; "
                       "ground beam sides); the column-neck area on the footing top is not deducted (necks BLOCKED)",
            "dome": {"surface_m2": _r(area), "concrete_m3": _r(area * DOME["shell_m"]), "radius_m": _r(R),
                     "formula": f"2 pi R h, R = (a2 + h2) / 2h = {R:.3f}; x 0.10", "count": None,
                     "status": "REVIEW", "why": "p.7 detail is N.T.S. and its plan location / number is not bound"},
            "pool": {"status": "BLOCKED", "why": "p.7 section gives walls 20 / base 40 / 10 cm plain concrete; depths "
                                                 "'as per arch.' are not printed in the architectural set"}}
