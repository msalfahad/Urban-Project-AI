"""ALSENAN V3b - structure completion (lab adapter: ezdxf / shapely; the decisions are in the stdlib engines).

    slab_rebar(ctx, st)   B09  every S-TEXT-SLAB / S-TEXT-CORNER annotation bound by slab_rebar_binding (drawn bar ->
                               panel by ray casting against the slab sheet's element lines), deduplicated; PARTIAL
                               (far support face not drawn) gets a labelled commercial embedment; SEE DETAIL panels are
                               bound to the DETAIL OF DOME by containment in the plan dome circles
    domes(ctx, st, arch)  B05  3 domes: count + span from the plan circles (P7757.dxf) = Route A, span / rise printed on
                               the elevations = Route C; shell / ring beam / bars from the DETAIL OF DOME (N.I.S.; drawing
                               factor proved by its printed 442 dimension against the measured dimension line)
Every record carries technical class + commercial release fields (engine.source.release_model).
"""

from __future__ import annotations

import math
import statistics
from collections import Counter
from pathlib import Path

import ezdxf
from shapely.geometry import Point

from engine.source import bbs_optimiser as BB
from engine.source import slab_rebar_binding as SB

COVER_M = 0.025                                                   # p.8 note 22
LAP_D = 70                                                        # p.8 note 9 (tension lap 70 Ø)
SLAB_TEXT_LAYERS = ("S-TEXT-SLAB", "S-TEXT-CORNER")
SLAB_BAR_LAYERS = ("S-REIN-SLAB", "S-REIN-CORNER")
FLOORS = ("GF", "1F", "2F")
MIN_BAR_MM = 600.0


def kgm(d):
    return d * d / 162.0


def _r(v, n=3):
    return None if v is None else round(v, n)


def _doc(ctx, name):
    return ezdxf.readfile(str(Path(ctx["_work"]) / ctx["paths"][name]))


# ================================================================== B09 slab reinforcement
def slab_extract(st) -> dict:
    msp = st.modelspace()
    texts, bars = [], []
    for e in msp.query("TEXT MTEXT"):
        if e.dxf.layer not in SLAB_TEXT_LAYERS:
            continue
        t = e.dxf.text if e.dxftype() == "TEXT" else e.plain_text()
        texts.append({"id": e.dxf.handle, "text": t, "x": e.dxf.insert.x, "y": e.dxf.insert.y,
                      "rotation_deg": float(e.dxf.get("rotation", 0.0) or 0.0), "layer": e.dxf.layer})
    for e in msp.query("LINE LWPOLYLINE"):
        if e.dxf.layer not in SLAB_BAR_LAYERS:
            continue
        if e.dxftype() == "LINE":
            b = {"id": e.dxf.handle, "x0": e.dxf.start.x, "y0": e.dxf.start.y, "x1": e.dxf.end.x, "y1": e.dxf.end.y}
        else:
            pts = [(p[0], p[1]) for p in e.get_points()]
            if len(pts) < 2:
                continue
            b = {"id": e.dxf.handle, "path": pts, "x0": pts[0][0], "y0": pts[0][1], "x1": pts[-1][0], "y1": pts[-1][1]}
        b["layer"] = e.dxf.layer
        bars.append(b)
    return {"texts": sorted(texts, key=lambda t: t["id"]), "bars": sorted(bars, key=lambda b: b["id"])}


def _dome_circles_st(st) -> list:
    """Dome outlines on the structural slab sheets: circles / arcs of the detail diameter (442 cm +- 2 cm)."""
    out = []
    for e in st.modelspace().query("CIRCLE ARC"):
        if abs(2 * e.dxf.radius - 4420.0) <= 20.0:
            c = (round(e.dxf.center.x, 1), round(e.dxf.center.y, 1))
            if c not in [o["c"] for o in out]:
                out.append({"c": c, "r": e.dxf.radius, "handle": e.dxf.handle, "type": e.dxftype()})
    return out


def slab_rebar(ctx, st) -> dict:
    raw = slab_extract(st)
    domes = _dome_circles_st(st)
    floors, rows = {}, []
    for fl in FLOORS:
        g = ctx["b2a"]["sheets"][fl]
        zone = g["_gross"].buffer(800.0)
        sup = [tuple(float(v) for v in s[1:5]) for s in g["_segs"]]
        bars = [b for b in raw["bars"] if zone.contains(Point(b["x0"], b["y0"])) and SB._developed(b) > MIN_BAR_MM]
        ann = [t for t in raw["texts"] if zone.contains(Point(t["x"], t["y"]))]
        recs = SB.dedupe(SB.bind(ann, bars, sup, cover_mm=COVER_M * 1000))
        bound_w = [w for r in recs if r.get("anchorage") == "BOTH_SUPPORTS_MEASURED" for w in r["support_widths_mm"]]
        med_w = statistics.median(bound_w) if bound_w else None
        max_w = max(bound_w) if bound_w else None
        detail = []
        for t in ann:
            if t["text"].strip().upper() == "SEE DETAIL":
                hit = [d for d in domes if math.hypot(t["x"] - d["c"][0], t["y"] - d["c"][1]) <= d["r"] + 50]
                detail.append({"annotation": t["id"], "text": "SEE DETAIL", "state": "BOUND_TO_DETAIL" if hit else
                               "UNBOUND", "detail": "DETAIL OF DOME" if hit else None,
                               "dome_circle": hit[0]["handle"] if hit else None,
                               "why": "inside the plan dome circle (442 cm) - reinforcement per DETAIL OF DOME "
                                      "(counted with the domes)" if hit else "no detail outline contains the text"})
        for r in recs:
            rows.append(_slab_row(fl, r, med_w, max_w))
        rows += [dict(floor=fl, **d, technical="DERIVED" if d["state"] == "BOUND_TO_DETAIL" else "BLOCKED",
                      net_kg=None) for d in detail]
        floors[fl] = {"annotations": len(ann), "bars": len(bars), "states": dict(Counter(r["state"] for r in recs)),
                      "see_detail": dict(Counter(d["state"] for d in detail)),
                      "median_support_width_mm": med_w, "max_support_width_mm": max_w}
    return {"rows": rows, "floors": floors, "policy": SB.policy_record(), "dome_circles_on_slab_sheets": domes}


def _slab_row(fl, r, med_w, max_w) -> dict:
    d = r["dia_mm"]
    k = kgm(d)
    row = {"floor": fl, "annotation": r["annotation"], "text": r["text"], "state": r["state"], "dia_mm": d,
           "kind": r["kind"], "n": r["n"], "top": r["top"], "bar": r.get("bar"), "binding": r.get("binding"),
           "count": r.get("count"), "clear_span_mm": _r(r.get("clear_span_mm"), 1), "width_mm": _r(r.get("width_mm"), 1),
           "support_widths_mm": [_r(w, 1) for w in r.get("support_widths_mm") or []],
           "embed_mm": [_r(e, 1) for e in r.get("embed_mm") or []], "length_mm": _r(r.get("length_mm"), 1),
           "drawn_length_mm": _r(r.get("drawn_length_mm"), 1), "why": r.get("why"), "duplicate_of": r.get("duplicate_of"),
           "kg_per_m": round(k, 4)}
    st = r["state"]
    if st in ("BOUND", "BOUND_TEXT_ONLY"):
        L = r["length_mm"] / 1000.0
        row.update(technical="DERIVED", net_m=row["count"] * L, commercial=None)
    elif st == "PARTIAL":
        L = r["length_mm"] / 1000.0
        e_open = (med_w - COVER_M * 1000) / 1000.0 if med_w else 0.0
        e_hi = (max_w - COVER_M * 1000) / 1000.0 if max_w else 0.0
        n_open = sum(1 for e in r["embed_mm"] if e is None)
        Lc, Lhi = L + n_open * e_open, L + n_open * e_hi
        row.update(technical="PARTIAL", net_m=row["count"] * L,
                   commercial={"class": "PROVISIONAL_GEOMETRIC_INFERENCE", "net_m": row["count"] * Lc,
                               "low_m": row["count"] * L, "high_m": row["count"] * Lhi, "confidence": "M",
                               "method": "open support: embedment = the floor's median measured support width - cover",
                               "assumption": f"{n_open} open support(s), embed {e_open:.3f} m each (range 0 .. "
                                             f"{e_hi:.3f})"})
    elif st == "DRAWN_EXTENT":
        L = r["length_mm"] / 1000.0
        row.update(technical="PARTIAL", net_m=None,
                   commercial={"class": "PROVISIONAL_SOURCE_DERIVED", "net_m": row["count"] * L,
                               "low_m": row["count"] * L * 0.9, "high_m": row["count"] * L * 1.1, "confidence": "M",
                               "method": "count bar outside the panel grid: drawn developed length (not dimensioned)",
                               "assumption": "drawn extent = bar length (+-10 % drafting)"})
    else:
        row.update(technical="BLOCKED" if st != "DUPLICATE_LABEL" else "DUPLICATE", net_m=None, commercial=None)
    if row.get("net_m") is not None:
        row["net_kg"] = row["net_m"] * k
        Lb = (row["length_mm"] or 0) / 1000.0
        row["pieces"] = [[f"{fl}-{r['annotation']}", p, row["count"]] for p in BB.split_run(Lb, LAP_D * d / 1000.0)]
    else:
        row["net_kg"] = None
    if row.get("commercial"):
        c = row["commercial"]
        c.update(net_kg=c["net_m"] * k, low_kg=c["low_m"] * k, high_kg=c["high_m"] * k)
    return row


# ================================================================== B05 domes
def _dimension_factor(st, region):
    """The N.I.S. detail's drawing factor: its printed span dimension text against the measured dimension line."""
    x0, y0, x1, y1 = region
    for e in st.modelspace().query("DIMENSION"):
        try:
            p = e.dxf.defpoint
        except AttributeError:
            continue
        if x0 <= p.x <= x1 and y0 <= p.y <= y1:
            m = e.get_measurement()
            if 20000 < m < 25000:
                return {"measured_drawing_units": m, "printed_cm": 442, "factor": m / 4420.0, "handle": e.dxf.handle}
    return None


DOME_DETAIL_REGION = (-66000, 25000, -38000, 44000)              # ST7757.dxf: '%%uDETAIL OF DOME' (N.I.S)


def domes(ctx, st, arch, raster) -> dict:
    fac = _dimension_factor(st, DOME_DETAIL_REGION)
    f = fac["factor"] if fac else None
    msp = st.modelspace()
    arcs = sorted([e for e in msp.query("ARC") if e.dxf.layer == "S-EXTL.D"
                   and DOME_DETAIL_REGION[0] <= e.dxf.center.x <= DOME_DETAIL_REGION[2]
                   and DOME_DETAIL_REGION[1] <= e.dxf.center.y <= DOME_DETAIL_REGION[3]], key=lambda e: -e.dxf.radius)
    shell_t = (arcs[0].dxf.radius - arcs[1].dxf.radius) / f / 1000.0 if f and len(arcs) >= 2 else None
    ring = [e for e in msp.query("LWPOLYLINE") if e.dxf.layer == "S-EXTL.D"]
    ring = [e for e in ring if DOME_DETAIL_REGION[0] <= e.get_points()[0][0] <= DOME_DETAIL_REGION[2]
            and DOME_DETAIL_REGION[1] <= e.get_points()[0][1] <= DOME_DETAIL_REGION[3]]
    rb = None
    if f and len(ring) >= 2:
        bx = [(min(p[0] for p in e.get_points()), max(p[0] for p in e.get_points()),
               min(p[1] for p in e.get_points()), max(p[1] for p in e.get_points())) for e in ring]
        bx.sort()
        w = (bx[0][1] - bx[0][0]) / f / 1000.0
        h = (bx[0][3] - bx[0][2]) / f / 1000.0
        cl = ((bx[-1][0] + bx[-1][1]) / 2 - (bx[0][0] + bx[0][1]) / 2) / f / 1000.0
        rb = {"B_m": round(w, 3), "D_drawn_m": round(h, 3), "centreline_diameter_m": round(cl, 3),
              "depth_text": "AS PER ARCH"}
    # Route A: plan circles in P7757.dxf (dome outlines on the 2F plan): 4.41 / 4.42 m
    circ = []
    for e in arch.modelspace().query("CIRCLE"):
        if 2150 <= e.dxf.radius <= 2260:
            circ.append({"handle": e.dxf.handle, "c": (round(e.dxf.center.x, 1), round(e.dxf.center.y, 1)),
                         "span_m": round(2 * e.dxf.radius / 1000.0, 3), "layer": e.dxf.layer})
    circ.sort(key=lambda c: c["c"])
    printed = {(c["quantity"], c["binds"]): c for c in raster["printed_claims"]}
    tower_rise = printed.get(("DOME_RISE", "TOWER ROOF DOME"))
    terrace_rise = printed.get(("DOME_RISE", "TERRACE DOME (2F)"))
    tower_span = printed.get(("DOME_SPAN", "TOWER ROOF DOME"))
    rows = []
    for c in circ:
        tower = abs(c["span_m"] - 4.41) < 0.005
        rise = (tower_rise if tower else terrace_rise)
        h = rise["value_cm"] / 100.0 if rise else None
        a = c["span_m"] / 2.0
        rec = {"id": f"DOME-{'TOWER' if tower else 'TERRACE'}-{c['handle']}", "plan_circle": c["handle"],
               "location": "tower roof (+13.90)" if tower else "2F terrace (+9.70)", "span_m": c["span_m"],
               "span_route_c_m": (tower_span["value_cm"] / 100.0 if tower and tower_span else 4.42 if not tower else None),
               "rise_m": h, "rise_source": rise["sheet_ref"] if rise else None, "shell_t_m": _r(shell_t),
               "detail_factor": _r(f, 5)}
        if h and shell_t:
            R = (a * a + h * h) / (2 * h)
            Rm, hm = R - shell_t / 2.0, h - shell_t / 2.0
            area_out = 2 * math.pi * R * h
            area_mid = 2 * math.pi * Rm * hm
            rec.update(R_m=round(R, 4), outer_area_m2=round(area_out, 3), mid_area_m2=round(area_mid, 3),
                       shell_m3=round(area_mid * shell_t, 3), inner_area_m2=round(2 * math.pi * (R - shell_t) *
                                                                                   (h - shell_t), 3))
            # shell mesh Ø12 / 15 cm each way (S-TEXT-SLAB '%%C12MM/15cm' x 2 in the detail)
            mesh_kg = area_mid * 2 * (1.0 / 0.15) * kgm(12)
            rec["shell_mesh_kg"] = round(mesh_kg, 3)
        if rb:
            per = math.pi * rb["centreline_diameter_m"]
            rec["ring_beam"] = dict(rb, perimeter_m=round(per, 3),
                                    volume_m3=round(per * rb["B_m"] * rb["D_drawn_m"], 3))
            per_bar = math.pi * (rb["centreline_diameter_m"])
            bars = [(3, 16, "top ring 3Ø16"), (3, 18, "bottom ring 3Ø18"), (4, 14, "side rings 2Ø14 each face")]
            ring_kg = sum(n * per_bar * kgm(d) for n, d, _ in bars)
            links = math.ceil(8 * per)
            link_len = 2 * (rb["B_m"] - 2 * COVER_M) + 2 * (rb["D_drawn_m"] - 2 * COVER_M)
            hook = BB.hook_addition(8, "135_TIE")
            rec["ring_rebar"] = {"rings": [{"n": n, "dia": d, "length_m": round(per_bar, 3), "what": w} for n, d, w in bars],
                                 "ring_kg": round(ring_kg, 3), "links": links, "link_length_m": round(link_len, 3),
                                 "link_hooks_m": round(2 * hook["addition_m"], 4), "hook_class": hook["class"],
                                 "links_kg": round(links * (link_len + 2 * hook["addition_m"]) * kgm(8), 3),
                                 "laps_m": round(sum(n * LAP_D * d / 1000.0 for n, d, _ in bars), 3)}
        rows.append(rec)
    return {"count": len(rows), "count_route_a": "P7757.dxf plan circles (r 2205 / 2211)",
            "count_route_c": raster["dome_count"], "detail_factor": fac, "shell_t_m": shell_t, "ring_beam": rb,
            "rows": rows}


# ================================================================== B07 beam / column residue
def _prov(cls, qty, lo, hi, conf, method, assumption, source=None):
    return {"class": cls, "qty": qty, "low": lo, "high": hi, "confidence": conf, "method": method,
            "assumption": assumption, "source": source}


def residue(ctx) -> dict:
    """Beam occurrences / tags and columns V3a could not measure: a labelled commercial quantity from the drawn band
    or the same type's measured population (never the technical column)."""
    import alsenan_phase_b2a as B2A
    sheets = ctx["b2a"]["sheets"]
    t_cm = {fl: (sheets[fl]["slab"]["sheet_thickness_tags_cm"] or [None])[0] for fl in FLOORS}
    measured = {}
    for fl in FLOORS:
        for o in sheets[fl]["occurrences"]:
            L = (o.get("lengths") or {}).get("CLEAR_FACE_TO_FACE_LENGTH")
            if o["state"] == "MEASURED" and L:
                measured.setdefault(o["type"], []).append(L)
    beams = []
    for fl in FLOORS:
        t = (t_cm[fl] or 0) / 100.0
        for o in sheets[fl]["occurrences"]:
            if o["state"] == "MEASURED":
                continue
            B, D = o["B_cm"] / 100.0, o["D_cm"] / 100.0
            Lc = (o.get("lengths") or {}).get("CLEAR_FACE_TO_FACE_LENGTH")
            br = o["band_record"]
            Lb = (br["t1"] - br["t0"]) / 1000.0
            L = Lc or Lb
            v = L * B * (D - t)
            rec = {"floor": fl, "id": f"{o['type']}:{o['tags'][0]}", "type": o["type"], "why_v3a": o["state"],
                   "B_m": B, "D_m": D, "length_m": round(L, 3),
                   "length_basis": "CLEAR_FACE_TO_FACE (band measured; span count differs from the schedule)" if Lc
                   else "drawn band extent"}
            if o["state"] == "BAND_TYPE_CONFLICT":
                rec["commercial"] = _prov("PROVISIONAL_SOURCE_RANGE", round(v, 4), round(v, 4), round(v, 4), "M",
                                          "band x scheduled section of this tag (two tags claim one band)",
                                          "both tags' sections are listed; see the paired record")
            else:
                rec["commercial"] = _prov("PROVISIONAL_GEOMETRIC_INFERENCE", round(v, 4), round(0.85 * v, 4),
                                          round(v, 4), "M", "drawn band length x scheduled section (B x (D - t))",
                                          "band extent may include support zones (low = 85 %)")
            beams.append(rec)
        for r in sheets[fl]["binding"]:
            if r["state"] in B2A.BB.BOUND_STATES:
                continue
            B, D = (r.get("B_cm") or 0) / 100.0, (r.get("D_cm") or 0) / 100.0
            Ls = measured.get(r["type"]) or []
            Lm = statistics.median(Ls) if Ls else None
            rec = {"floor": fl, "id": f"{r['type']}:{r['mark_key']}", "type": r["type"], "why_v3a": r["state"],
                   "B_m": B, "D_m": D, "length_m": _r(Lm), "length_basis":
                   f"median clear length of the {len(Ls)} measured {r['type']} occurrence(s)" if Ls else "none"}
            if Lm:
                v = Lm * B * (D - t)
                rec["commercial"] = _prov("BUDGET_ESTIMATE", round(v, 4), 0.0, round(max(Ls) * B * (D - t), 4), "L",
                                          "unbound tag: same-type median clear length x section",
                                          "the tag may repeat a beam already measured (low = 0)")
            else:
                rec["commercial"] = None
            beams.append(rec)
    # paired conflict: keep only the larger section as the commercial value, the smaller as LOW
    conf = [b for b in beams if b["why_v3a"] == "BAND_TYPE_CONFLICT"]
    if len(conf) == 2:
        lo, hi = sorted(conf, key=lambda b: b["commercial"]["qty"])
        hi["commercial"].update(low=lo["commercial"]["qty"], high=hi["commercial"]["qty"],
                                assumption=f"selected commercial basis = the larger section ({hi['type']}); "
                                           f"alternative {lo['type']}")
        lo["commercial"] = None
        lo["superseded_by"] = hi["id"]
    cols = []
    ivs = {iv["from"]: iv["interval_m"] for iv in ctx["b2a"]["intervals"]}
    done = [r for r in ctx["b2a"]["columns"]["rows"] if r.get("volume_m3") is not None]
    for r in ctx["b2a"]["columns"]["rows"]:
        if r.get("volume_m3") is not None or r["state"] in ("NOT_IN_STOREY", "NOT_DRAWN_ON_STOREY_SHEET"):
            continue
        same = [d for d in done if d["floor"] == r["floor"]]
        hs = [d["height_m"] for d in same if d.get("height_m")]
        h = statistics.median(hs) if hs else ivs.get(r["floor"])
        B, D = r["B_cm"] / 100.0, r["D_cm"] / 100.0
        v = B * D * h
        cols.append({"floor": r["floor"], "id": r["tag_key"], "type": r["type"], "why_v3a": r["state"], "B_m": B, "D_m": D,
                     "height_m": round(h, 3), "commercial": _prov(
                         "PROVISIONAL_GEOMETRIC_INFERENCE", round(v, 4), round(B * D * min(hs or [h]), 4),
                         round(B * D * (ivs.get(r["floor"]) or h), 4), "M",
                         "scheduled section x the floor's median computed column height",
                         "upper member unbound: height between the floor's lowest computed height and the storey interval")})
    return {"beams": beams, "columns": cols}


# ================================================================== B01 exterior ground beams, B02 necks, B06 F / F10
EXT_GB_D = {"qty": 1.00, "low": 0.90, "high": 1.30}            # m; see ext_ground_beams


def ext_ground_beams(ctx) -> dict:
    """'Follow arch.' = from the outer ground to the GF slab: the elevations / sections print ±0.00 ground and the
    +1.00 GF level on every sheet (top AND bottom are therefore NOT both proven: the GB bottom below ground is not
    printed) -> PROVISIONAL_SOURCE_DERIVED (OC-V3B-A)."""
    import alsenan_v3_structure as V3S
    gbe = [x for x in ctx["v3"]["ground_items"]["beams"] if x["kind"] == "EXTERIOR"]
    L = sum(x["length_m"] for x in gbe)
    B = V3S.GB_EXTERIOR["B"]
    v = {k: L * B * d for k, d in EXT_GB_D.items()}
    g = V3S.GB_EXTERIOR
    per_m_kg = (g["top"][0] * kgm(g["top"][1]) + sum(n * kgm(d) for n, d in g["bottom"]))
    side_n = lambda D: 2 * max(0, math.floor((D - 0.30) / g["side"][2]))
    link = lambda D: 2 * (B - 2 * 0.07) + 2 * (D - 2 * 0.07)
    hook = BB.hook_addition(8, "135_TIE")
    def kg(D):
        n_side = side_n(D) if D > 0.60 else 0
        bars = per_m_kg * L + n_side * kgm(g["side"][1]) * L
        links = math.ceil(L / g["stirrup"][1]) * (link(D) + 2 * hook["addition_m"]) * kgm(g["stirrup"][0])
        return bars + links
    return {"spans": len(gbe), "length_m": round(L, 3), "B_m": B, "D": EXT_GB_D,
            "concrete": _prov("PROVISIONAL_SOURCE_DERIVED", round(v["qty"], 4), round(v["low"], 4), round(v["high"], 4),
                              "M", "length x 0.30 x D; D = ground (±0.00) to GF level (+1.00), printed on all elevations",
                              "the below-ground embedment is not printed (low 0.90 = 10 cm build-up off, high 1.30 = "
                              "30 cm below ground)"),
            "blinding_local_m3": round(L * (B + 0.20) * 0.10, 4),
            "rebar_kg": {"qty": round(kg(1.00), 3), "low": round(kg(0.90), 3), "high": round(kg(1.30), 3)},
            "rebar_basis": "p.13 exterior GB: top 3Ø16, bottom 6Ø16, side 2Ø12 @ 30, Ø8 @ 15 links (cover 7); "
                           "135° link hooks " + hook["class"]}


FOUNDING = {"qty": -1.50, "low": -1.00, "high": -2.00}         # m below ±0.00 - URBAN fallback (note 12: by site)


def necks(ctx) -> dict:
    """Column necks: footing top to the GF slab underside. The founding level is a site decision (note 12) -> the
    labelled Urban fallback founding level, range ±0.5 m; never procurement eligible (confidence L)."""
    rows = [f for f in ctx["a3"]["footings"]["rows"] if str(f.get("status", "")).startswith("COMPUTED")]
    defs = {d["type"]: d for d in ctx["a3"]["rebar"]["definitions"] if d["element"] == "COLUMN"}
    cols = [r for r in ctx["b2a"]["columns"]["rows"] if r["floor"] == "GF" and r.get("B_cm")]
    sec = statistics.median([r["B_cm"] * r["D_cm"] for r in cols]) / 1e4 if cols else None
    out = {}
    for k, z in FOUNDING.items():
        vol = 0.0
        for f in rows:
            H = f["dims"]["H"]["m"]
            h = max(0.0, (1.00 - 0.10) - (z + H))
            vol += sec * h
        out[k] = vol
    nbar = statistics.median([sum(b["count"] for b in (defs.get(r["type"], {}).get("bars", {}).get("FOUNDATION") or []))
                              for r in cols]) if cols else 0
    def kg(z):
        return sum(nbar * ((1.00 - 0.10) - (z + f["dims"]["H"]["m"]) + f["dims"]["H"]["m"] - 0.07 + 40 * 0.016) *
                   kgm(16) for f in rows)
    return {"footings": len(rows), "median_section_m2": sec, "founding_m": FOUNDING,
            "concrete": _prov("PROVISIONAL_URBAN_FALLBACK", round(out["qty"], 4), round(out["low"], 4),
                              round(out["high"], 4), "L",
                              "neck = median GF column section x (GF slab underside +0.90 - footing top)",
                              "founding level -1.50 (Urban fallback; note 12 leaves it to site) range -1.00 .. -2.00"),
            "starter_rebar_kg": {"qty": round(kg(FOUNDING["qty"]), 3), "low": round(kg(FOUNDING["low"]), 3),
                                 "high": round(kg(FOUNDING["high"]), 3), "bars_per_column": nbar,
                                 "basis": "FOUNDATION bars of the column schedule: neck + footing embedment (H - 7 cm) "
                                          "+ one 40Ø lap"}}


def f_f10(ctx) -> dict:
    lib = ctx["a3"]["footings"]["library"]
    defs = {d["type"]: d for d in ctx["a3"]["rebar"]["definitions"] if d["element"] == "FOOTING"}
    def vol(t, n):
        x = lib[t]
        return n * x["L_cm"] * x["W_cm"] * x["H_cm"] / 1e6
    def kg(t, n):
        x, d = lib[t], defs[t]["bars"]
        c = 0.07
        s = sum(b["count"] * (x["L_cm"] / 100 - 2 * c) * kgm(b["dia_mm"]) for b in d["long_bars"])
        s += sum(b["count"] * (x["W_cm"] / 100 - 2 * c) * kgm(b["dia_mm"]) for b in d["short_bars"])
        return n * s
    def bl(t, n):
        x = lib[t]
        return n * (x["L_cm"] / 100 + 0.2) * (x["W_cm"] / 100 + 0.2) * 0.10
    F, F10 = vol("F", 2), vol("F10", 1)
    return {"outline_mm": [3250.0, 1400.0], "marks": ["F", "F10"],
            "F_SCENARIO": {"what": "two F footings", "concrete_m3": F, "rebar_kg": kg("F", 2), "blinding_m3": bl("F", 2)},
            "F10_SCENARIO": {"what": "one F10 combined footing", "concrete_m3": F10, "rebar_kg": kg("F10", 1),
                             "blinding_m3": bl("F10", 1)},
            "LOW": min(F, F10), "HIGH": max(F, F10), "DIFFERENCE": abs(F10 - F), "technical": "BLOCKED_SOURCE_CONFLICT",
            "commercial": _prov("PROVISIONAL_SOURCE_RANGE", round(max(F, F10), 4), round(min(F, F10), 4),
                                round(max(F, F10), 4), "M", "the two schedule definitions of the one drawn outline",
                                "SELECTED COMMERCIAL BASIS = the larger (F10) definition, labelled")}


# ================================================================== B10 ground slab zone 2 (annex) and the founded footprints
def ground_zones(ctx) -> dict:
    """Close the annex zone across layers: single structural lines (any layer drawn on the ground-beam sheet that the
    zone needs) act as barriers when the paired 300 mm bands leave the zone open. Footprints: the outer outline of each
    connected ground-beam system (bands + columns + barriers)."""
    import alsenan_phase_a as AP
    import alsenan_phase_a3 as A3
    import alsenan_phase_b2a as B2A
    import alsenan_v3_structure as V3S
    from shapely.geometry import LineString, Polygon
    from shapely.ops import unary_union
    from engine.source import canonical_input as CI
    Sb = A3._blob(ctx, Path(ctx["_work"]), "ST7757.dxf")
    sb = ctx["structural_sheets"]["GROUND_BEAMS"]["bounds"]
    lay = lambda p: CI.effective_layer(p)[0]
    LAYERS = ("1", "2")
    segs = [p for p in Sb["parts"] if p.kind == "SEGMENT" and lay(p) in LAYERS and AP.in_box(p.geometry[0], p.geometry[1], sb)]
    arcs = [p for p in Sb["parts"] if p.kind == "ARC" and lay(p) in LAYERS and AP.in_box(p.geometry[0], p.geometry[1], sb)]
    cols = [Polygon(B2A._rect_poly(r)) for r in B2A._col_rects(Sb, sb)]
    bands = V3S._pair_bands(segs, width=300.0, tol=12.0) + V3S._arc_bands(arcs, width=300.0, tol=12.0)
    thin = [LineString([(p.geometry[0], p.geometry[1]), (p.geometry[2], p.geometry[3])]).buffer(1.0) for p in segs]
    union = unary_union([b["poly"] for b in bands] + cols + thin)
    comps = sorted([Polygon(c.exterior) for c in getattr(union, "geoms", [union])], key=lambda p: -p.area)
    fps = [c for c in comps if c.area >= 20e6]
    zones = []
    for z in ctx["v3"]["ground"]["zones"]:
        if "_outer" in z:
            zones.append({"id": z["id"], "state": "CLOSED_V3A", "slab_m2": z["slab_area_m2"]})
            continue
    zt = [t for t in Sb["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, sb) and "T=" in t.value]
    zt = sorted(zt, key=lambda q: q.identity.key)
    z2 = None
    for i, t in enumerate(zt):
        zid = f"ZONE-{i + 1}"
        if any(z["id"] == zid for z in zones):
            continue
        P = Point(t.x, t.y)
        hit = [c for c in comps if c.contains(P)]
        if not hit:
            zones.append({"id": zid, "state": "STILL_OPEN"})
            continue
        outer = min(hit, key=lambda p: p.area)
        slab = outer.difference(union)
        pcs = [q for q in getattr(slab, "geoms", [slab]) if 2 * q.area / q.length >= 450.0]
        a = sum(q.area for q in pcs) / 1e6
        z2 = {"id": zid, "state": "CLOSED_CROSS_LAYER", "outer_m2": round(outer.area / 1e6, 3), "slab_m2": round(a, 3),
              "pieces": len(pcs), "t_m": 0.10, "volume_m3": round(a * 0.10, 4),
              "mesh_kg": round(a * 2 * 5 * kgm(10), 3),
              "rule": "paired 300 mm bands (layers 1 + 2) + single lines as barriers; slab = outer - beams / columns / "
                      "barriers, strips narrower than 450 mm effective width excluded"}
        zones.append(z2)
    return {"zones": zones, "footprints": [{"id": f"FP-{i + 1}", "area_m2": round(c.area / 1e6, 3),
                                            "bounds": [round(v) for v in c.bounds]} for i, c in enumerate(fps)],
            "_fp": fps}


def blinding(ctx, gz, ext, ff) -> dict:
    """OD-V3B-1: SOURCE_DETAIL_LOCAL_BLINDING (p.13 typical detail: 10 cm, 10 cm beyond each footing / beam) and
    OWNER_FULL_FOOTPRINT_BLINDING (one plain layer over each independently founded footprint at formation level, t from
    SOURCE = 0.10 m p.13). The local blinding is the same physical layer (double-count guard): only the owner method
    enters the total; the local one is the published alternative."""
    items = {i["item"]: i for i in ctx["b2a"]["structural_items"]}
    loc_f = items["BLINDING (under computed footings)"]["volume_m3"]
    loc_gb = ctx["v3"]["substructure"]["ground_beam_blinding_m3"]
    local = loc_f + loc_gb + ext["blinding_local_m3"] + ff["F10_SCENARIO"]["blinding_m3"]
    t = 0.10
    fp = gz["footprints"]
    area = sum(f["area_m2"] for f in fp)
    plate = L_plate_area(ctx)
    return {"thickness": {"value_m": t, "authority": "SOURCE (ST7757 p.13 typical footing: 10 cm plain concrete)",
                          "hierarchy": "SOURCE > OWNER FACT > URBAN METHOD 0.10 > PENDING"},
            "concrete": {"strength": "f'c >= 150 kg/cm2 (p.8 note 6)", "cement": "sulfate- and salt-resisting (note 13)",
                         "soil_contact": True, "sulfate_requirement": "YES (note 13)", "source": "ST7757.pdf p.8"},
            "SOURCE_DETAIL_LOCAL_BLINDING": {
                "volume_m3": round(local, 4), "level": "under each footing / ground beam (formation of each element)",
                "parts": {"footings (computed)": loc_f, "interior ground beams": loc_gb,
                          "exterior ground beams (provisional length x 0.50)": ext["blinding_local_m3"],
                          "F / F10 (F10 definition)": ff["F10_SCENARIO"]["blinding_m3"]},
                "source": "p.13 typical detail", "role": "ALTERNATIVE (same physical layer) - not in the total"},
            "OWNER_FULL_FOOTPRINT_BLINDING": {
                "footprints": fp, "area_m2": round(area, 3), "thickness_m": t, "volume_m3": round(area * t, 4),
                "level": "formation level (one layer; footings set out above it)",
                "source": "OD-V3B-1 (owner method) x ground-beam system outline (ST7757 GROUND BEAMS PLAN)",
                "route_b": {"what": "GF architectural plate (structural GF roof plate registered on the plan)",
                            "area_m2": plate, "note": "the roof plate includes overhangs / terraces; the founded "
                                                      "footprint is expected below it"}},
            "double_count_guard": "local detail blinding = the same layer; only OWNER_FULL_FOOTPRINT enters the total"}


def L_plate_area(ctx):
    import alsenan_v3_layers as L
    p = L._plate_in_arch(ctx, "GF")
    return round(p.area / 1e6, 3) if p is not None else None


# ================================================================== B04 pool
POOL_DEPTH_CLAIM = ("SUNKEN_ELEMENT_DEPTH", "POOL CANDIDATE (to be matched to the p.3 pool outline)")


def pool(ctx, st, raster) -> dict:
    """Plan: the S-BW double rectangle around the SWIM block on the ground-beam sheet (inner x outer = wall 20);
    depth: the pit printed on the NW elevation (115) beside the curved glazing; thicknesses: DETAIL OF SWIMMING POOL
    (walls 20, base 40, 10 cm plain concrete, 5 cm membrane + 5 cm screed)."""
    msp = st.modelspace()
    sb = ctx["structural_sheets"]["GROUND_BEAMS"]["bounds"]
    swim = [e for e in msp.query("INSERT") if e.dxf.name.upper() == "SWIM"
            and sb[0] <= e.dxf.insert.x <= sb[2] and sb[1] <= e.dxf.insert.y <= sb[3]]
    rects = []
    for e in msp.query("LWPOLYLINE"):
        if e.dxf.layer != "S-BW":
            continue
        pts = e.get_points()
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        rects.append((min(xs), min(ys), max(xs), max(ys), e.dxf.handle))
    if not swim:
        return {"state": "NO_POOL_BLOCK"}
    sx, sy = swim[0].dxf.insert.x, swim[0].dxf.insert.y
    around = sorted([r for r in rects if r[0] <= sx <= r[2] and r[1] <= sy <= r[3]], key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
    if len(around) < 2:
        return {"state": "OUTLINE_NOT_FOUND"}
    inn, out = around[0], around[1]
    Li, Wi = (inn[2] - inn[0]) / 1000.0, (inn[3] - inn[1]) / 1000.0
    wall = 0.20                                            # DETAIL OF SWIMMING POOL: walls 20 (the S-BW outer outline
    drawn_offsets = [round((inn[0] - out[0]) / 1000.0, 3), round((out[2] - inn[2]) / 1000.0, 3),   # shares one side)
                     round((inn[1] - out[1]) / 1000.0, 3), round((out[3] - inn[3]) / 1000.0, 3)]
    dep = {(c["quantity"], c["binds"]): c for c in raster["printed_claims"]}.get(POOL_DEPTH_CLAIM)
    D = dep["value_cm"] / 100.0 if dep else None
    L, W = max(Li, Wi), min(Li, Wi)
    base_t = 0.40
    res = {"state": "DERIVED" if D else "BLOCKED_DEPTH", "swim_block": swim[0].dxf.handle, "inner_m": [L, W],
           "wall_t_m": wall, "wall_source": "detail (20)", "drawn_outer_offsets_m": drawn_offsets, "base_t_m": base_t, "depth_m": D, "depth_source": dep and dep["sheet_ref"],
           "outline_handles": [inn[4], out[4]]}
    if D:
        per_c = 2 * ((L + wall) + (W + wall))
        walls = per_c * wall * D
        base = (L + 2 * wall) * (W + 2 * wall) * base_t
        blind = (L + 2 * wall + 0.2) * (W + 2 * wall + 0.2) * 0.10
        wp = (L + 2 * wall) * (W + 2 * wall) + 2 * ((L + 2 * wall) + (W + 2 * wall)) * (D + base_t)
        inner_finish = L * W + 2 * (L + W) * D
        per_in = 2 * (L + W)
        # detail: deep wall vertical 7Ø14/m (outer face) + 7Ø12/m (inner), horizontal Ø12/20 both faces;
        # base 7Ø14/m bottom and top, both ways (deep end values used for the whole pool - labelled)
        wall_v = per_c * (7 * kgm(14) + 7 * kgm(12)) * (D + base_t - 0.05)
        wall_h = 2 * math.ceil(D / 0.20 + 1) * per_c * kgm(12)
        base_b = 2 * 2 * ((L + 2 * wall) * (W + 2 * wall)) * 7 * kgm(14)
        res.update(walls_m3=round(walls, 4), base_m3=round(base, 4), concrete_m3=round(walls + base, 4),
                   blinding_m3=round(blind, 4), external_wp_m2=round(wp, 3), internal_finish_m2=round(inner_finish, 3),
                   coping_lm=round(per_in, 3), rebar_kg=round(wall_v + wall_h + base_b, 3),
                   rebar_basis="DETAIL OF SWIMMING POOL deep-end callouts applied to the whole pool (the detail's sloped "
                               "shallow end is not shown on the 1.55 x 3.10 plan): walls 7Ø14/m + 7Ø12/m vertical, "
                               "Ø12/20 horizontal both faces; base 7Ø14/m top and bottom both ways",
                   formula=f"walls {per_c:.2f} x {wall:.2f} x {D:.2f}; base {L + 2 * wall:.2f} x {W + 2 * wall:.2f} x "
                           f"{base_t:.2f}")
    return res


# ================================================================== B14 boundary wall
FENCE = {"height_m": 2.65, "parts": "2.15 + 0.50 (fence sheet section)"}


def boundary_wall(ctx, st, raster) -> dict:
    """Run: the S-BOUN polylines on the ground-beam sheet (200 mm double line = the boundary wall footprint);
    height: the fence sheet (2.65 = 2.15 + 0.50, printed); beam: schedule row B.W 20 x 60 (p.14 typical)."""
    from shapely.geometry import Polygon
    msp = st.modelspace()
    sb = ctx["structural_sheets"]["GROUND_BEAMS"]["bounds"]
    runs = []
    for e in msp.query("LWPOLYLINE"):
        if e.dxf.layer != "S-BOUN" or not e.closed:
            continue
        pts = [(p[0], p[1]) for p in e.get_points()]
        if not all(sb[0] <= x <= sb[2] and sb[1] <= y <= sb[3] for x, y in pts):
            continue
        poly = Polygon(pts)
        w = 2 * poly.area / poly.length
        cl = poly.area / 200.0
        runs.append({"handle": e.dxf.handle, "area_m2": round(poly.area / 1e6, 4), "centreline_m": round(cl / 1000.0, 3),
                     "width_mm_effective": round(w, 1)})
    Lc = sum(r["centreline_m"] for r in runs)
    fr = {(c["quantity"], c["binds"]): c for c in raster["printed_claims"]}.get(("FENCE_FRONT_RUN", "FRONT FENCE RUN (plan 1:100)"))
    H = FENCE["height_m"]
    return {"runs": runs, "length_m": round(Lc, 3), "height_m": H, "height_source": "ARCH-P12-FENCE (printed 2.15 + 0.50)",
            "front_run_printed_m": fr["value_cm"] / 100.0 if fr else None,
            "blockwork_m2": round(Lc * H, 3), "blockwork_basis": "run x 2.65 printed face height",
            "beam_m3": round(Lc * 0.20 * 0.60, 4), "beam": "B.W 20 x 60 (schedule)",
            "plaster_both_faces_m2": round(2 * Lc * H, 3),
            "note": "S-BOUN runs on the ground-beam sheet are 200 mm wide (wall on its beam); footings of the p.14 "
                    "typical detail are not spaced on any plan -> not quantified (PENDING)",
            "class": "PROVISIONAL_SOURCE_DERIVED"}


# ================================================================== B03 stairs
RISE = {"GF->1F": 4.50, "1F->2F": 4.20}
R_MAX, R_MIN = 0.175, 0.15                                       # 2R + G comfort band with G = 0.30 (code method)


def stairs(ctx) -> dict:
    """Riser count: the section A-A treads were not countable by machine this round -> PROVISIONAL_CODE_METHOD from the
    2R + G band (G = 0.30 printed p.16): n = ceil(H / 0.175) (low), floor(H / 0.15) (high). Waist 16 cm from note 18
    is NOT proof of the waist (OC-V3B-B): PROVISIONAL_SOURCE_DERIVED. Width 1.15 m (plan tread lines)."""
    k = ctx["b2a"]["stairs"]["known_inputs"]
    G = k["tread_going_m"]["value"]
    W = 1.15
    t = 0.16
    out = []
    for f, H in RISE.items():
        n = math.ceil(H / R_MAX - 1e-9)
        n_hi = math.floor(H / R_MIN)
        R = H / n
        treads = n - 1
        run = treads * G
        slope = math.hypot(run, H)
        landing = W * W * (2 if f == "GF->1F" else 1)
        waist = slope * W * t
        steps = n * R * G / 2 * W
        land_v = landing * t
        conc = waist + steps + land_v
        out.append({"flight": f, "H_m": H, "risers": n, "risers_range": [n, n_hi], "R_m": round(R, 4), "G_m": G,
                    "treads": treads, "width_m": W, "slope_len_m": round(slope, 3), "landings_m2": landing,
                    "concrete_m3": round(conc, 4),
                    "concrete_hi_m3": round(math.hypot((n_hi - 1) * G, H) * W * t + n_hi * (H / n_hi) * G / 2 * W + land_v, 4),
                    "tread_m2": round(treads * G * W + landing, 3), "riser_m2": round(n * R * W, 3),
                    "nosing_lm": round(treads * W, 3), "handrail_lm": round(slope + (W if landing else 0), 3),
                    "plan_tread_lines_check": [r["tread_lines"] for r in k["observed_tread_line_runs"]
                                               if r["floor"] == f[:2] and r["width_m"] == W and r["linetype"] == "CONTINUOUS"]})
    return {"flights": out, "waist": {"t_m": t, "class": "PROVISIONAL_SOURCE_DERIVED",
                                      "why": "note 18 (slabs 16 cm unless stated) is not a stair waist proof"},
            "risers_class": "PROVISIONAL_CODE_METHOD (2R + G band, G = 0.30 printed)",
            "landings": "W x W per turn (GF->1F two turns, 1F->2F one; plan tread runs 3 / 2) - labelled"}


# ================================================================== B14 courtyard / external paving
def courtyard(ctx, st, gz) -> dict:
    """External paved area inside the boundary-wall enclosure (S-BOUN runs, ground-beam sheet) less the founded
    footprints and the pool: the south limit (front) is not drawn on the structural sheet -> low confidence."""
    from shapely.geometry import box, Polygon
    from shapely.ops import unary_union
    msp = st.modelspace()
    sb = ctx["structural_sheets"]["GROUND_BEAMS"]["bounds"]
    bou = [e for e in msp.query("LWPOLYLINE") if e.dxf.layer == "S-BOUN" and e.closed
           and all(sb[0] <= p[0] <= sb[2] and sb[1] <= p[1] <= sb[3] for p in e.get_points())]
    if not bou:
        return {"state": "NO_ENCLOSURE"}
    big = max(bou, key=lambda e: Polygon([(p[0], p[1]) for p in e.get_points()]).area)
    pts = [(p[0], p[1]) for p in big.get_points()]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    inner = box(min(xs) + 200, min(ys), max(xs) - 200, max(ys) - 200)
    pool = [e for e in msp.query("LWPOLYLINE") if e.dxf.layer == "S-BW"]
    pools = [Polygon([(p[0], p[1]) for p in e.get_points()]) for e in pool if len(e.get_points()) >= 4]
    rest = inner.difference(unary_union([f.buffer(0) for f in gz["_fp"]] + [p.buffer(0) for p in pools]))
    a = rest.area / 1e6
    return {"class": "PROVISIONAL_GEOMETRIC_INFERENCE", "qty": round(a, 3), "low": round(0.7 * a, 3), "high": round(a, 3),
            "confidence": "L", "method": "boundary-wall enclosure (S-BOUN) - founded footprints - pool / shaft outlines",
            "assumption": "the enclosure's open south side is closed at the end of the side runs; paving material BY_SPEC",
            "formula": f"enclosure {inner.area / 1e6:.2f} m2 - buildings / pool = {a:.2f} m2"}
