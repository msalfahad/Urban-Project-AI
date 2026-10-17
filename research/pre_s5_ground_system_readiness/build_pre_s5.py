"""PRE-S5 ground-system rebar readiness (strap beams + ground beams): geometry + source applicability, no kg.

    python3 -I research/pre_s5_ground_system_readiness/build_pre_s5.py [ST7757.dxf]

Inputs (Urban only):
  * ST7757.dxf, sha256-checked (default: data/inputs/by_sha256/<sha>.dxf), decoded by the Urban K2 route (ground-beam
    plan, the frozen V3 network convention) and by the S1 sheet reader (foundation plan: straps, footings, columns);
  * the frozen V3 GROUND_STRUCTURE_REGISTER (the OLD network, re-derived here and checked equal);
  * the frozen S1 registers (footing occurrences, strap definitions) and the R4 visual source-claim register (p.13 /
    p.8 claims, read as typical-detail sources) and R4 project rule register (cover, development, hooks).
No reference, donor or benchmark file is read.

The OLD network is V3 (single best partner per face, first-arc sweep). The NEW network is the generic
engine/source/ground_beam_network.py with two rules only: MULTI_PARTNER_PAIRING and ARC_OVERLAP. Every change is
attributed by re-running the network under four configurations (V3 / +multi-partner / +arc overlap / both); a change
that neither rule explains stops the build.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LAB = ROOT / "research" / "external_engine_lab"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(LAB))

from engine.source import canonical_input as CI  # noqa: E402
from engine.source import ground_beam_network as GN  # noqa: E402
from engine.source import ground_system_provenance as GP  # noqa: E402

BASELINE = "6b2b41b"
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
DEFAULT_DXF = ROOT / "data" / "inputs" / "by_sha256" / f"{DXF_SHA}.dxf"
GB_SHEET = (78930.0, 29036.0, 114124.0, 57066.0)     # frozen FLOOR_PLAN_REGISTER ground-beams frame (V3 convention)
WIDTH, TOL = 300.0, 12.0                              # V3 convention: layer-1 double lines at 300 +- 12 mm
FACE_LAYERS = {"1"}
MIN_PIECE_AREA = 300.0 * 300.0                         # V3 span rule: a piece < 300 x 300 mm is not a span
TOUCH = 5.0                                            # mm: geometric contact
LEN_EQ_TOL = 0.001                                     # m: a length within 1 mm of a threshold is ON the threshold
V3_REGISTER = ROOT / "tests/alsenan/registers_v3/GROUND_STRUCTURE_REGISTER.json"
S1 = ROOT / "research/alsenan_structural_census_s1"
R4 = ROOT / "research/alsenan_rebar_source_exhaustion_04/registers"
CLAIMS = R4 / "VISUAL_SOURCE_CLAIM_REGISTER.json"
RULES = R4 / "PROJECT_REBAR_RULE_REGISTER.json"
S4_F3 = ROOT / "research/alsenan_footing_rebar_s4/F3_AUTHORITY_DECISION.json"
CODE = ["engine/source/ground_beam_network.py", "engine/source/ground_system_provenance.py",
        "research/pre_s5_ground_system_readiness/build_pre_s5.py"]
INPUTS = [V3_REGISTER, S1 / "FOOTING_OCCURRENCE_REGISTER.json", S1 / "BEAM_DEFINITION_REGISTER.json",
          S1 / "BEAM_OCCURRENCE_REGISTER.json", CLAIMS, RULES, S4_F3, R4 / "GROUND_BEAM_REBAR_V4.json"]
CONTEXT = {"PROJECT_ID": "ALSENAN-ST7757", "REVISION": "ALSENAN_ST7757_DXF", "DRAWING_ID": "ST7757.dxf",
           "DRAWING_SHA": DXF_SHA, "REGISTER_VERSION": "GROUND_SYSTEM_READINESS_V1", "CALCULATION_ROUND": "PRE_S5"}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def r3(v):
    return None if v is None else round(float(v), 3)


def r1(v):
    return None if v is None else round(float(v), 1)


# ===================================================================================================== decode
def decode(dxf, work):
    import alsenan_phase_a as AP
    import alsenan_phase_a3 as A3
    if _sha(dxf) != DXF_SHA:
        raise SystemExit(f"ST7757.dxf sha mismatch (expected {DXF_SHA})")
    shutil.copyfile(dxf, work / "ST7757.dxf")
    ctx = {"paths": {"ST7757.dxf": "ST7757.dxf"}, "structural_sheets": {"GROUND_BEAMS": {"bounds": GB_SHEET}}}
    S = A3._blob(ctx, work, "ST7757.dxf")
    assert S["dxf_sha256"] == DXF_SHA and AP.REV_STR == CONTEXT["REVISION"]
    return S, ctx


def lay(p):
    return CI.effective_layer(p)[0]


def hx(key):
    """'ALSENAN_ST7757_DXF|H276|...' -> '114' (the DXF hex handle)."""
    return format(int(key.split("|")[1][1:]), "X")


def sheet_parts(S, kind, layers=None):
    import alsenan_phase_a as AP
    return [p for p in S["parts"] if p.kind == kind and AP.in_box(p.geometry[0], p.geometry[1], GB_SHEET)
            and (layers is None or lay(p) in layers)]


# ===================================================================================================== bands
def bands_v3(S, layers):
    """OLD bands: the frozen V3 functions, unchanged."""
    import alsenan_v3_structure as V3S
    st = V3S._pair_bands(sheet_parts(S, "SEGMENT", layers), width=WIDTH, tol=TOL)
    ar = V3S._arc_bands(sheet_parts(S, "ARC", layers), width=WIDTH, tol=TOL)
    out = []
    for b in st:
        hs = sorted(format(int(k[1:]), "X") for k in b["id"].split("+"))
        out.append({"id": "+".join(hs), "handles": hs, "kind": "STRAIGHT", "poly": b["poly"], "u": b["u"],
                    "rule": "V3_SINGLE_PARTNER"})
    for b in ar:
        hs = sorted(format(int(k[1:]), "X") for k in b["id"].replace("ARC:", "").split("+"))
        out.append({"id": "ARC:" + "+".join(hs), "handles": hs, "kind": "ARC", "poly": b["poly"], "u": None,
                    "arc_len": b["arc_len"], "rule": "V3_FIRST_ARC_SWEEP"})
    return out


def bands_new(S, layers, *, multi=True, arc=True):
    """NEW bands from the generic engine. multi / arc switch one rule back to V3 for the causal attribution."""
    from shapely.geometry import Polygon
    old = bands_v3(S, layers)
    out, diag = [], {}
    if multi:
        faces = [{"handle": hx(p.identity.key), "layer": lay(p), "p0": tuple(p.geometry[0:2]),
                  "p1": tuple(p.geometry[2:4])} for p in sheet_parts(S, "SEGMENT")]
        res = GN.pair_straight(faces, width=WIDTH, tol=TOL, admitted_layers=set(layers))
        diag["straight"] = res
        for b in res["bands"]:
            out.append({"id": "+".join(b["handles"]), "handles": b["handles"], "kind": "STRAIGHT",
                        "poly": Polygon(b["polygon"]), "u": b["u"], "rule": b["rule"], "gn": b})
    else:
        out += [b for b in old if b["kind"] == "STRAIGHT"]
    if arc:
        arcs = [{"handle": hx(p.identity.key), "layer": lay(p), "cx": p.geometry[0], "cy": p.geometry[1],
                 "r": p.geometry[2], "a0": p.geometry[3], "a1": p.geometry[4]} for p in sheet_parts(S, "ARC")]
        res = GN.pair_arcs(arcs, width=WIDTH, tol=TOL, admitted_layers=set(layers))
        diag["arcs"] = res
        for b in res["bands"]:
            out.append({"id": "ARC:" + "+".join(b["handles"]), "handles": b["handles"], "kind": "ARC",
                        "poly": Polygon(b["polygon"]).buffer(0), "u": None, "arc_len": b["CENTERLINE_ARC_LENGTH"],
                        "rule": "ARC_OVERLAP", "gn": b})
    else:
        out += [b for b in old if b["kind"] == "ARC"]
    return out, diag


# ===================================================================================================== V3 span rule
def columns(S):
    import alsenan_phase_b2a as B2A
    from shapely.geometry import Polygon
    return [{"id": "COL:" + "+".join(sorted(hx(k) for k in r[0])[:2]), "poly": Polygon(B2A._rect_poly(r)),
             "centre": tuple(r[3])} for r in B2A._col_rects(S, GB_SHEET)]


def band_len(g, b):
    if b["u"] is None:
        return b["arc_len"] * g.area / b["poly"].area
    xs = [x * b["u"][0] + y * b["u"][1] for x, y in g.exterior.coords]
    return max(xs) - min(xs)


def spans_v3_rule(S, bands, cols):
    """The V3 ground() span + zone logic with the band set as a parameter (zones from the 'T=' slab notes)."""
    import alsenan_phase_a as AP
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    cpolys = [c["poly"] for c in cols]
    union = unary_union([b["poly"] for b in bands] + cpolys)
    comps = list(getattr(union, "geoms", [union]))
    ztxt = sorted([t for t in S["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, GB_SHEET)
                   and "T=" in t.value], key=lambda q: q.identity.key)
    outers = []
    for t in ztxt:
        hit = [Polygon(c.exterior) for c in comps if Polygon(c.exterior).contains(Point(t.x, t.y))]
        if hit:
            outers.append(min(hit, key=lambda p: p.area))
    col_u = unary_union(cpolys)
    spans = []
    for b in bands:
        pieces = b["poly"].difference(col_u)
        for g in getattr(pieces, "geoms", [pieces]):
            if g.is_empty or g.area < MIN_PIECE_AREA:
                continue
            spans.append({"band": b["id"], "length_mm": band_len(g, b), "exterior": any(
                z.exterior.distance(g) < TOUCH for z in outers), "poly": g, "b": b})
    return spans, outers


def footprints(S, bands_12, cols):
    """R4 / V3b footprint rule: outer outline of each connected ground-beam system (layers 1+2 bands, columns and
    every layer 1/2 line as a 1 mm barrier); systems < 20 m2 ignored."""
    from shapely.geometry import LineString, Polygon
    from shapely.ops import unary_union
    thin = [LineString([tuple(p.geometry[0:2]), tuple(p.geometry[2:4])]).buffer(1.0)
            for p in sheet_parts(S, "SEGMENT", {"1", "2"})]
    union = unary_union([b["poly"] for b in bands_12] + [c["poly"] for c in cols] + thin)
    comps = sorted([Polygon(c.exterior) for c in getattr(union, "geoms", [union])], key=lambda p: -p.area)
    return [c for c in comps if c.area >= 20e6]


# ===================================================================================================== topology
def piece_frame(sp):
    """(s0, s1, centreline offset, half width) of a straight piece along its band axis."""
    b = sp["b"]
    u = b["u"]
    n = (-u[1], u[0])
    xs = [x * u[0] + y * u[1] for x, y in sp["poly"].exterior.coords]
    ys = [x * n[0] + y * n[1] for x, y in b["poly"].exterior.coords]
    return min(xs), max(xs), (min(ys) + max(ys)) / 2.0, (max(ys) - min(ys)) / 2.0, u, n


def classify_ends(sp, spans, bands, cols, fps):
    """Start / end node of a span (COLUMN | BEAM_JUNCTION | CONTINUATION | FREE_END), support centre stations, the
    support-centreline length, intermediate junctions and footing / column contacts."""
    from shapely.geometry import LineString, Point
    b = sp["b"]
    if b["kind"] == "ARC":
        return arc_ends(sp, bands, cols, fps)
    s0, s1, mid, hw, u, n = piece_frame(sp)
    pt = lambda s, o: (s * u[0] + o * n[0], s * u[1] + o * n[1])
    nodes = []
    for s in (s0, s1):
        edge = LineString([pt(s, mid - hw), pt(s, mid + hw)])
        refs = []
        for c in cols:
            if c["poly"].distance(edge) <= TOUCH:
                cs = c["centre"][0] * u[0] + c["centre"][1] * u[1]
                refs.append({"kind": "COLUMN", "ref": c["id"], "station": cs})
        if not refs:
            for o in bands:
                if o is b or o["poly"].distance(edge) > TOUCH:
                    continue
                if o["u"] is not None and abs(o["u"][0] * u[1] - o["u"][1] * u[0]) < 0.2:
                    refs.append({"kind": "CONTINUATION", "ref": o["id"], "station": s})
                    continue
                st = s
                if o["u"] is not None:          # centreline intersection station
                    ou = o["u"]
                    on = (-ou[1], ou[0])
                    oys = [x * on[0] + y * on[1] for x, y in o["poly"].exterior.coords]
                    omid = (min(oys) + max(oys)) / 2.0
                    p0 = pt(s, mid)
                    den = u[0] * on[0] + u[1] * on[1]
                    if abs(den) > 1e-9:
                        t = (omid - (p0[0] * on[0] + p0[1] * on[1])) / den
                        st = s + t
                refs.append({"kind": "BEAM_JUNCTION", "ref": o["id"], "station": st})
        kinds = {r["kind"] for r in refs}
        kind = ("COLUMN" if "COLUMN" in kinds else "BEAM_JUNCTION" if "BEAM_JUNCTION" in kinds else
                "CONTINUATION" if "CONTINUATION" in kinds else "FREE_END")
        sup = [r for r in refs if r["kind"] == kind]
        station = sum(r["station"] for r in sup) / len(sup) if sup and kind != "CONTINUATION" else s
        nodes.append({"kind": kind, "refs": sorted({r["ref"] for r in sup}), "station": station})
    cc = abs(nodes[1]["station"] - nodes[0]["station"])
    inter = []
    for o in bands:
        if o is b:
            continue
        g = o["poly"].intersection(sp["poly"].buffer(TOUCH))
        if g.is_empty:
            continue
        cx = g.centroid
        s = cx.x * u[0] + cx.y * u[1]
        if s0 + 2 * TOUCH < s < s1 - 2 * TOUCH:
            inter.append({"ref": o["id"], "station": round(s - s0, 1),
                          "relation": "CROSSING" if o["poly"].intersection(sp["poly"]).area > 1.0 else "CARRIES"})
    return finish_nodes(sp, nodes, cc, inter, cols, fps)


def arc_ends(sp, bands, cols, fps):
    from shapely.geometry import Point
    b = sp["b"]["gn"]
    cx, cy = b["centre"]
    angs = sorted(math.atan2(y - cy, x - cx) % (2 * math.pi) for x, y in sp["poly"].exterior.coords)
    # largest angular gap = outside the piece
    gaps = [(angs[(i + 1) % len(angs)] - angs[i]) % (2 * math.pi) for i in range(len(angs))]
    k = max(range(len(gaps)), key=lambda i: gaps[i])
    a_start, a_end = angs[(k + 1) % len(angs)], angs[k]
    nodes = []
    for a in (a_start, a_end):
        p = Point(cx + b["CENTERLINE_RADIUS"] * math.cos(a), cy + b["CENTERLINE_RADIUS"] * math.sin(a))
        e = p.buffer(b["width"] / 2.0 + TOUCH)
        refs = [{"kind": "COLUMN", "ref": c["id"]} for c in cols if c["poly"].distance(p) <= b["width"] / 2 + TOUCH]
        if not refs:
            refs = [{"kind": "BEAM_JUNCTION", "ref": o["id"]} for o in bands
                    if o is not sp["b"] and o["poly"].intersects(e)]
        kind = refs[0]["kind"] if refs else "FREE_END"
        nodes.append({"kind": kind, "refs": sorted({r["ref"] for r in refs}), "station": None})
    return finish_nodes(sp, nodes, None, [], cols, fps)


def finish_nodes(sp, nodes, cc, inter, cols, fps):
    touch_cols = sorted(c["id"] for c in cols if c["poly"].distance(sp["poly"]) <= TOUCH)
    feet = sorted(f["id"] for f in fps if f["poly"].intersection(sp["poly"]).area > 1.0)
    return {"start": nodes[0], "end": nodes[1], "cc_mm": cc, "intermediate": inter, "columns": touch_cols,
            "footings": feet}


# ===================================================================================================== FP sheet
def fp_sheet(dxf):
    import alsenan_structural_s1 as S1M
    src = S1M.Source(dxf)
    return src, S1M


def footing_index():
    out = {}
    for r in J(S1 / "FOOTING_OCCURRENCE_REGISTER.json")["rows"]:
        h = r["outline"]["handle"]
        occ = "FOCC-" + h.split(":")[0].split("+")[0]
        typ = r.get("type") or ("|".join(r["candidate_types"]) if r.get("candidate_types") else None)
        out[h] = {"occurrence_id": occ, "type": typ, "footing_id": r["footing_id"],
                  "terminal_state": r.get("terminal_state"), "issues": r.get("issues") or []}
    return out


def footings_on(src, S1M, sheet_frame_to):
    """S1 foundation-plan footing outlines as polygons in the target sheet's model frame."""
    from shapely.geometry import Polygon
    fo = S1M.footing_outlines(src)
    idx = footing_index()
    f0 = src.sheets["FP"]["frame"]
    out = []
    for f in fo:
        h = f["id"].split(":", 1)[1]
        meta = idx.get(h)
        if meta is None:
            continue
        ring = [(x + sheet_frame_to[0], y + sheet_frame_to[1]) for x, y in f["ring"]]
        out.append({"id": meta["occurrence_id"], "type": meta["type"], "poly": Polygon(ring), "local_ring": f["ring"],
                    "handle": h})
    return out


def sheet_alignment(src, S1M):
    """Columns on FP and GBP in sheet-local coordinates: the residual says whether the two plans share a frame."""
    cf, cg = S1M.column_outlines(src, "FP"), S1M.column_outlines(src, "GBP")
    cen = lambda c: ((c["bbox"][0] + c["bbox"][2]) / 2, (c["bbox"][1] + c["bbox"][3]) / 2)
    res = sorted(min(math.dist(cen(a), cen(b)) for b in cg) for a in cf)
    return {"fp_columns": len(cf), "gbp_columns": len(cg), "within_5mm": sum(r <= 5 for r in res),
            "max_residual_mm": r1(max(res)), "median_residual_mm": r1(res[len(res) // 2]),
            "rule": "FP and GBP sheet frames share their local origin; footing outlines are placed on the GBP sheet "
                    "by that shared frame (columns agree within 5 mm except where a column is drawn at another size)"}


# ===================================================================================================== straps
def sbt_rows(dxf):
    import ezdxf
    doc = ezdxf.readfile(str(dxf))
    rows = []
    for e in doc.modelspace().query('INSERT[name=="SBT"]'):
        a = {x.dxf.tag: x.dxf.text for x in e.attribs}
        if a.get("BEAM", "").upper().startswith("SB"):
            rows.append({"insert": e.dxf.handle, "mark": a["BEAM"].upper(), "W_cm": float(a["W"]), "H_cm": float(a["H"]),
                         "top": (int(a["TOP-B"]), int(a["TOP-D"])), "bottom": (int(a["BOT-B"]), int(a["BOT-D"])),
                         "stirrups_per_m": (int(a["STI-B"]), int(a["D"])), "attribs": a})
    return sorted(rows, key=lambda r: (r["mark"], r["insert"]))


def strap_census(src, S1M, dxf):
    from shapely.geometry import LineString, Polygon
    straps, unbound = S1M.strap_beams(src)
    feet = footings_on(src, S1M, (0.0, 0.0))                       # FP-local frame
    cols = S1M.column_outlines(src, "FP")
    sbt = sbt_rows(dxf)
    occ_s1 = {r["source_id"]: r for r in J(S1 / "BEAM_OCCURRENCE_REGISTER.json")["rows"] if r["family"] == "STRAP"}
    out = []
    for s in sorted(straps, key=lambda z: z["tag"] or ""):
        b = s["band"]
        u, n = b["dir"], b["normal"]
        hw = b["width_mm"] / 2.0
        along = lambda p: p[0] * u[0] + p[1] * u[1]
        across = lambda p: p[0] * n[0] + p[1] * n[1] - b["offset"]
        sup = []
        for f in feet:
            pts = list(f["poly"].exterior.coords)
            ac = [across(p) for p in pts]
            al = [along(p) for p in pts]
            if min(ac) <= hw and max(ac) >= -hw and max(al) >= b["t0"] - 60 and min(al) <= b["t1"] + 60:
                sup.append({"footing": f, "lo": min(al), "hi": max(al)})
        sup.sort(key=lambda z: z["lo"])
        start, end = (sup[0], sup[-1]) if len(sup) >= 2 else (None, None)

        def col_in(f):
            hits = []
            for c in cols:
                x0, y0, x1, y1 = c["bbox"]
                cpoly = Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
                if f["footing"]["poly"].intersection(cpoly).area > 1.0:
                    ac = across(c["centre"])
                    hits.append((abs(ac), c))
            return min(hits, key=lambda z: z[0])[1] if hits else None
        cs, ce = (col_in(start), col_in(end)) if start else (None, None)
        clear = (end["lo"] - start["hi"]) if start else None
        cc_col = abs(along(ce["centre"]) - along(cs["centre"])) if cs and ce else None
        fcent = lambda f: f["footing"]["poly"].centroid
        cc_ft = abs(along((fcent(end).x, fcent(end).y)) - along((fcent(start).x, fcent(start).y))) if start else None
        rows_def = [r for r in sbt if r["mark"] == s["tag"]]
        s1row = occ_s1.get(f"STRAP:FP:{b['band_id']}", {})
        flags = []
        sizes = ", ".join("%.0fx%.0f" % (r["W_cm"], r["H_cm"]) for r in rows_def)
        if len(rows_def) > 1:
            flags.append(f"SCHEDULE_KEY_CONFLICT: {len(rows_def)} SBT rows for {s['tag']} "
                         f"({sizes})")
        for end_, tag in ((start, "START"), (end, "END")):
            if end_ and "|" in (end_["footing"]["type"] or ""):
                flags.append(f"{tag}_SUPPORT_OUTLINE_SOURCE_CONFLICT ({end_['footing']['type']}): the clear length is "
                             "measured to the drawn face; every candidate footing is smaller than the drawn outline, so "
                             "the measured clear length is a lower bound")
        width_match = [r for r in rows_def if abs(s["drawn_width_mm"] - 10 * r["W_cm"]) <= 25]
        auth = ("SOURCE_VERIFIED" if len(rows_def) == 1 and width_match and start else
                "SOURCE_CONFLICT" if len(rows_def) > 1 else "UNRESOLVED")
        out.append({
            "STRAP_OCCURRENCE_ID": "SOCC-" + "-".join(sorted(b["edges"])), "MARK": s["tag"], "TYPE": "STRAP_BEAM",
            "PLAN": "FOUNDATION PLAN (ST7757.dxf FP sheet, PDF p.2)",
            "SOURCE_HANDLES": sorted(b["edges"]) + ([s["tag_handle"]] if s["tag_handle"] else []),
            "START_SUPPORT": None if not start else {"kind": "FOOTING", "footing": start["footing"]["id"],
                                                     "footing_type": start["footing"]["type"],
                                                     "column": cs["id"] if cs else None},
            "END_SUPPORT": None if not end else {"kind": "FOOTING", "footing": end["footing"]["id"],
                                                 "footing_type": end["footing"]["type"],
                                                 "column": ce["id"] if ce else None},
            "CLEAR_CONCRETE_LENGTH_M": r3(clear / 1000 if clear is not None else None),
            "CENTERLINE_SUPPORT_TO_SUPPORT_M": r3(cc_col / 1000 if cc_col is not None else None),
            "CENTERLINE_BASIS": "column centre to column centre, projected on the strap axis",
            "FOOTING_CENTRE_TO_CENTRE_M": r3(cc_ft / 1000 if cc_ft is not None else None),
            "DRAWN_FACE_LENGTH_M": r3((b["t1"] - b["t0"]) / 1000),
            "WIDTH_DRAWN_MM": r1(s["drawn_width_mm"]),
            "WIDTH_SCHEDULE_CM": [r["W_cm"] for r in rows_def], "DEPTH_SCHEDULE_CM": [r["H_cm"] for r in rows_def],
            "SCHEDULE_DETAIL_REFERENCE": [f"SBT insert {r['insert']} (Schedule of beams, PDF p.10)" for r in rows_def],
            "REINFORCEMENT_REFERENCE": [{"TOP": f"{r['top'][0]}Ø{r['top'][1]}", "BOTTOM": f"{r['bottom'][0]}Ø{r['bottom'][1]}",
                                         "STIRRUPS_PER_M": f"{r['stirrups_per_m'][0]}Ø{r['stirrups_per_m'][1]}/m"}
                                        for r in rows_def],
            "AUTHORITY_STATE": auth, "S1_STATE": s1row.get("terminal_state"), "FLAGS": flags,
            "_rows": rows_def, "_clear_m": clear / 1000 if clear is not None else None})
    return out, [t["handle"] for t in unbound]


# ===================================================================================================== details
def detail_library():
    cl = {c["claim_id"]: c for c in J(CLAIMS)["claims"]}
    gt5, lt5, lt25b, lt25s, ext = (cl[k] for k in ("P13-GB-GT5M", "P13-GB-LT5M", "P13-GB-LT2_5M-BARS",
                                                     "P13-GB-LT2_5M-SECTION", "P13-GB-EXTERIOR"))
    vv = lambda c: c["value"]
    lib = {
        "P13-GB-GT5M": {"scope": "INTERIOR", "cond": ("GT", 5.0), "literal": gt5["raw_visual_transcription"],
                        "B": vv(gt5)["B_mm"], "D": vv(gt5)["D_mm"], "top": tuple(vv(gt5)["top"]),
                        "rows": [tuple(x) for x in vv(gt5)["lower_rows"]], "side": None,
                        "stirrup": tuple(vv(gt5)["stirrup"]), "state": gt5["source_state"], "page": 13,
                        "claims": ["P13-GB-GT5M"], "section_state": gt5["source_state"]},
        "P13-GB-LT5M": {"scope": "INTERIOR", "cond": ("LT", 5.0), "literal": lt5["raw_visual_transcription"],
                        "B": vv(lt5)["B_mm"], "D": vv(lt5)["D_mm"], "top": tuple(vv(lt5)["top"]),
                        "rows": [tuple(x) for x in vv(lt5)["lower_rows"]], "side": None,
                        "stirrup": tuple(vv(lt5)["stirrup"]), "state": lt5["source_state"], "page": 13,
                        "claims": ["P13-GB-LT5M"], "section_state": lt5["source_state"]},
        "P13-GB-LT2_5M": {"scope": "INTERIOR", "cond": ("LT", 2.5), "literal": lt25b["raw_visual_transcription"],
                          "B": vv(lt25s)["B_mm"], "D": vv(lt25s)["D_mm"], "top": tuple(vv(lt25b)["top"]),
                          "rows": [tuple(x) for x in vv(lt25b)["lower_rows"]], "side": None, "stirrup": None,
                          "state": lt25b["source_state"], "page": 13,
                          "claims": ["P13-GB-LT2_5M-BARS", "P13-GB-LT2_5M-SECTION"],
                          "section_state": lt25s["source_state"]},
        "P13-GB-EXTERIOR": {"scope": "EXTERIOR", "cond": None, "literal": ext["raw_visual_transcription"],
                            "B": vv(ext)["B_mm"], "D": vv(ext)["D_mm"], "top": tuple(vv(ext)["top"]),
                            "rows": [tuple(x) for x in vv(ext)["bottom_rows"]], "side": vv(ext)["side"],
                            "stirrup": tuple(vv(ext)["stirrup"]), "state": ext["source_state"], "page": 13,
                            "claims": ["P13-GB-EXTERIOR"], "section_state": ext["source_state"]},
    }
    return lib, cl


def length_details(L, lib):
    """Literal length conditions met by L (m); [] when L sits ON a threshold that no condition covers."""
    out = []
    for k, d in lib.items():
        if d["cond"] is None:
            continue
        op, th = d["cond"]
        if abs(L - th) <= LEN_EQ_TOL:
            continue
        if (op == "GT" and L > th) or (op == "LT" and L < th):
            out.append(k)
    return sorted(out)


def applicability(occ, lib):
    """Candidate detail set + DETAIL_APPLICABILITY_STATE for one ground-beam occurrence."""
    bases = {"CLEAR": occ["clear_m"]}
    if occ.get("cc_m") is not None:
        bases["SUPPORT_CENTRELINE"] = occ["cc_m"]
    by_basis = {k: length_details(v, lib) for k, v in bases.items()}
    boundary = sorted({f"{k}={v:.3f} m on the {th} m threshold" for k, v in bases.items()
                       for th in (2.5, 5.0) if abs(v - th) <= LEN_EQ_TOL})
    length_c = set()
    for v in by_basis.values():
        length_c |= set(v)
    if boundary:
        length_c |= {"P13-GB-GT5M", "P13-GB-LT5M"}
    basis_agree = len({tuple(v) for v in by_basis.values()}) == 1
    ext_a, ext_b = occ["exterior_zone_test"], occ["exterior_footprint_test"]
    flags, why_no = [], []
    if boundary:
        flags.append("LENGTH_ON_THRESHOLD_UNRESOLVED: " + "; ".join(boundary))
    if not basis_agree:
        flags.append("LENGTH_BASIS_CHANGES_DETAIL: " + "; ".join(f"{k} {bases[k]:.3f} m -> {by_basis[k]}"
                                                                 for k in sorted(bases)))
    if len(length_c) > 1 and {"P13-GB-LT2_5M", "P13-GB-LT5M"} <= length_c and basis_agree and not boundary:
        flags.append("NESTED_LITERAL_CONDITIONS: 'Less than 2.5m' and 'Less than 5m' both hold literally")
    if ext_a and ext_b:
        cand = ["P13-GB-EXTERIOR"]
        state = "PROJECT_GENERAL_DETAIL"
        why = ("typical detail 'for exterior walls'; the span lies on the outer outline of the ground-beam system by "
               "two independent geometric tests (V3 slab-zone outline + R4 footprint outline)")
        flags.append("ARCHITECTURAL_EXTERIOR_WALL_OVERLAY_PENDING (Q-R4-6)")
        why_no.append("interior length sections: span is on the outer outline (both tests)")
    elif ext_a or ext_b:
        cand = sorted({"P13-GB-EXTERIOR"} | length_c)
        state = "CANDIDATE_DETAIL"
        why = ("the two exterior tests disagree (zone outline: " + ("EXTERIOR" if ext_a else "INTERIOR") +
               ", footprint outline: " + ("EXTERIOR" if ext_b else "INTERIOR") + "); exterior and interior "
               "sections are both candidates until the architectural exterior walls are overlaid (Q-R4-6)")
    else:
        cand = sorted(length_c)
        if not cand:
            state, why = "NO_APPLICABLE_DETAIL", "no literal length condition covers this span"
        elif boundary or not basis_agree:
            state = "CANDIDATE_DETAIL"
            why = "interior span; the governing length section depends on the length basis / threshold"
        else:
            state = "EXPLICIT_LENGTH_CONDITION"
            why = (f"interior span; literal length condition(s) met on every basis: {cand} (conditions read as "
                   "printed; 'without concentrated load' is part of the title and is not assessed)")
        why_no.append("exterior-wall section: span is inside the outer outline (both tests)")
    for k in lib:
        if k not in cand:
            if lib[k]["cond"]:
                why_no.append(f"{k}: literal condition '{lib[k]['cond'][0]} {lib[k]['cond'][1]} m' not met")
    return {"bases": bases, "by_basis": by_basis, "candidates": cand, "state": state, "why": why,
            "why_not": "; ".join(sorted(set(why_no))), "flags": flags}


def bars(t):
    return None if t is None else f"{t[0]}Ø{t[1]}"


def readiness_gb(occ, app, lib, rules):
    """Component readiness for one ground-beam occurrence (never a kg)."""
    C = [lib[k] for k in app["candidates"]]
    comp = {}

    def same(vals):
        return len({repr(v) for v in vals}) == 1

    if not C:
        for k in ("TOP_MAIN", "BOTTOM_ROW_1", "BOTTOM_ROW_2", "SIDE_BARS", "STIRRUP_DIAMETER", "STIRRUP_RATE",
                  "STIRRUP_CORE_PATH", "STIRRUP_COUNT", "HOOK_1", "HOOK_2", "END_ZONE_EXTRA", "END_TREATMENT",
                  "DEVELOPMENT_INTO_SUPPORT_1", "DEVELOPMENT_INTO_SUPPORT_2", "LAP"):
            comp[k] = ("NO_APPLICABLE_DETAIL", None, "no applicable detail")
        return comp
    straight = ("straight run: support face-to-face, derived per span in PRE-S5.1 (research/pre_s5_1_source_resolution, "
                "no numerical-minimum shortcut); development / end anchorage not source-established")
    for k, f in (("TOP_MAIN", lambda d: d["top"]), ("BOTTOM_ROW_1", lambda d: d["rows"][0]),
                 ("BOTTOM_ROW_2", lambda d: d["rows"][1])):
        vals = [f(d) for d in C]
        comp[k] = (("READY_LOWER_BOUND", bars(vals[0]), straight) if same(vals) else
                   ("BLOCKED_COMPONENT", " | ".join(sorted({bars(v) for v in vals})),
                    "candidate details disagree: " + "; ".join(f"{k2} {bars(f(lib[k2]))}" for k2 in app["candidates"])))
    sides = [d["side"] for d in C]
    if all(s is None for s in sides):
        comp["SIDE_BARS"] = ("NOT_APPLICABLE", None, "the candidate section(s) carry no side bars")
    else:
        comp["SIDE_BARS"] = ("BLOCKED_COMPONENT", " | ".join(sorted(str(s) for s in sides)),
                             "side bars 2Ø12 per 30 cm of depth; depth FOLLOW ARCH. not printed" +
                             ("" if all(s is not None for s in sides) else "; other candidates have none"))
    st = [d["stirrup"] for d in C]
    if any(s is None for s in st):
        dia = ("BLOCKED_COMPONENT", " | ".join(sorted(str(s) for s in st)),
               "a candidate section draws a stirrup with no size / spacing callout")
        rate = dia
    elif same(st):
        dia = ("READY", f"Ø{st[0][0]}", "typical section callout")
        rate = ("READY", f"{st[0][1]} mm", "typical section callout")
    else:
        dia = rate = ("BLOCKED_COMPONENT", " | ".join(sorted(str(s) for s in st)), "candidate callouts differ")
    comp["STIRRUP_DIAMETER"], comp["STIRRUP_RATE"] = dia, rate
    Ds = [d["D"] for d in C]
    if any(D is None for D in Ds):
        core = ("BLOCKED_COMPONENT", "D = FOLLOW ARCH.", "section depth not printed (FOLLOW ARCH.)")
    elif not same(Ds):
        core = ("BLOCKED_COMPONENT", " | ".join(f"300x{D:.0f}" for D in sorted(set(Ds))),
                "candidate sections differ in depth")
    elif any(d["section_state"] != "CROSS_VERIFIED_SOURCE" for d in C):
        core = ("PROVISIONAL_ONLY", f"300x{Ds[0]:.0f}", "section size is an AI transcription only; closed rectangular "
                                                          "link drawn in the typical section, legs not a verified facet")
    else:
        core = ("PROVISIONAL_ONLY", f"300x{Ds[0]:.0f}, cover 70 (soil)",
                "B, D and the 70 mm soil cover are source-established; the closed single link is drawn in the typical "
                "section but its topology is not a verified facet")
    comp["STIRRUP_CORE_PATH"] = core
    comp["STIRRUP_COUNT"] = (("READY_LOWER_BOUND", rate[1], "count >= ceil(clear span / spacing); first / last "
                                                            "stirrup position not stated")
                             if rate[0] == "READY" else ("BLOCKED_COMPONENT", None, "spacing not established"))
    hook = rules["HOOKS_AND_BENDS"]
    comp["HOOK_1"] = comp["HOOK_2"] = ("BLOCKED_COMPONENT", None,
                                       f"hook angle / extension: {hook['source_state']} ({hook['note']})")
    comp["END_ZONE_EXTRA"] = ("NOT_APPLICABLE", None, "the section prints one uniform spacing; no end-zone callout")
    dev = rules["DEVELOPMENT_STARTER_70D_40D"]
    comp["END_TREATMENT"] = ("BLOCKED_COMPONENT", None, "bar ends at the supports are not detailed")
    comp["DEVELOPMENT_INTO_SUPPORT_1"] = comp["DEVELOPMENT_INTO_SUPPORT_2"] = (
        "BLOCKED_COMPONENT", None, f"no beam-end anchorage rule in the project source ({dev['rule_id']} is "
                                   f"'{dev['scope']}' only)")
    comp["LAP"] = ("NOT_APPLICABLE", None, "net measurement: laps are a procurement matter (BBS firewall)")
    return comp


def readiness_strap(st, rules):
    rows = st["_rows"]
    comp = {}
    straight = ("straight run >= the clear concrete length between footing faces; development into the footings "
                "not source-established")
    if not rows:
        return {k: ("NO_APPLICABLE_DETAIL", None, "no SBT row") for k in ("TOP_MAIN", "BOTTOM_ROW_1")}
    same = lambda vals: len(set(vals)) == 1
    for k, f in (("TOP_MAIN", lambda r: r["top"]), ("BOTTOM_ROW_1", lambda r: r["bottom"])):
        vals = [f(r) for r in rows]
        comp[k] = (("READY_LOWER_BOUND", bars(vals[0]), straight + ("; BOTTOM is one schedule total (row split not "
                                                                    "stated)" if k == "BOTTOM_ROW_1" else ""))
                   if same(vals) else ("BLOCKED_COMPONENT", " | ".join(bars(v) for v in vals),
                                       "duplicated schedule key: rows disagree"))
    comp["BOTTOM_ROW_2"] = ("NOT_APPLICABLE", None, "the schedule gives one BOTTOM total; no second row is stated")
    side = rules["SIDE_BARS_NOTE_21"]
    hs = ", ".join("%.0f" % r["H_cm"] for r in rows)
    comp["SIDE_BARS"] = ("NOT_APPLICABLE", None, f"p.8 note 21 applies to depth > 60 cm; schedule H = "
                                                 f"{hs} cm")
    stv = [r["stirrups_per_m"] for r in rows]
    comp["STIRRUP_DIAMETER"] = (("READY", f"Ø{stv[0][1]}", "SBT D column") if same(stv) else
                                ("BLOCKED_COMPONENT", " | ".join(str(v) for v in stv), "rows disagree"))
    comp["STIRRUP_RATE"] = (("READY", f"{stv[0][0]}/m", "SBT STI-B under the 'STIRRUPS/m' header") if same(stv) else
                            comp["STIRRUP_DIAMETER"])
    Bs = {r["W_cm"] for r in rows}
    comp["STIRRUP_CORE_PATH"] = ("BLOCKED_COMPONENT", " | ".join("%.0fx%.0f" % (r["W_cm"], r["H_cm"]) for r in rows),
                                 ("section width conflict; " if len(Bs) > 1 else "") +
                                 "leg count / link topology not stated (SBT is a schedule row with no section sketch)")
    comp["STIRRUP_COUNT"] = (("READY_LOWER_BOUND", comp["STIRRUP_RATE"][1], "count >= ceil(rate x clear length)")
                             if comp["STIRRUP_RATE"][0] == "READY" else ("BLOCKED_COMPONENT", None, "rate not established"))
    hook = rules["HOOKS_AND_BENDS"]
    comp["HOOK_1"] = comp["HOOK_2"] = ("BLOCKED_COMPONENT", None, f"{hook['source_state']} ({hook['note']})")
    comp["END_ZONE_EXTRA"] = ("NOT_APPLICABLE", None, "the schedule gives one rate per metre")
    comp["END_TREATMENT"] = ("BLOCKED_COMPONENT", None, "bar ends inside the footings are not detailed")
    dev = rules["DEVELOPMENT_STARTER_70D_40D"]
    comp["DEVELOPMENT_INTO_SUPPORT_1"] = comp["DEVELOPMENT_INTO_SUPPORT_2"] = (
        "BLOCKED_COMPONENT", None, f"development into the footing not source-established ({dev['rule_id']} is "
                                   f"'{dev['scope']}' only)")
    comp["LAP"] = ("NOT_APPLICABLE", None, "net measurement: laps are a procurement matter (BBS firewall)")
    return comp


def occ_status(comp):
    lon = [comp[k][0] for k in ("TOP_MAIN", "BOTTOM_ROW_1") if k in comp]
    if all(s == "NO_APPLICABLE_DETAIL" for s in lon):
        return "NO_APPLICABLE_DETAIL"
    if all(s in ("READY", "READY_LOWER_BOUND") for s in lon) and comp.get("BOTTOM_ROW_2", ("NOT_APPLICABLE",))[0] in (
            "READY", "READY_LOWER_BOUND", "NOT_APPLICABLE"):
        return "READY" if all(s == "READY" for s in lon) and comp["DEVELOPMENT_INTO_SUPPORT_1"][0] == "READY" else \
            "READY_LOWER_BOUND"
    if any(s == "PROVISIONAL_ONLY" for s in lon):
        return "PROVISIONAL_ONLY"
    return "BLOCKED_COMPONENT"


# ===================================================================================================== writers
def wcsv(path, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: (json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, (list, dict, tuple)) else
                        (round(v, 3) if isinstance(v, float) else v)) for k, v in r.items()})
    path.write_text(buf.getvalue(), encoding="utf-8")


def wjson(path, obj):
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


# ===================================================================================================== main
def main(dxf):
    import alsenan_v3_structure as V3S
    work = Path(tempfile.mkdtemp(prefix="pre_s5_"))
    try:
        return _main(Path(dxf), work, V3S)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _main(dxf, work, V3S):
    S, ctx = decode(dxf, work)
    cols = columns(S)
    stamp = f"{BASELINE}+code:{code_digest()[:16]}"
    context = dict(CONTEXT, ENGINE_COMMIT=stamp)

    # ---------------- OLD network, checked against the frozen V3 register
    old_bands = bands_v3(S, FACE_LAYERS)
    old_spans, old_outers = spans_v3_rule(S, old_bands, cols)
    gr = V3S.ground(ctx, work)
    frozen = J(V3_REGISTER)["ground"]
    ref = sorted((round(s["length_m"], 3), bool(s["exterior"])) for s in frozen["spans"])
    mine = sorted((round(s["length_mm"] / 1000, 3), bool(s["exterior"])) for s in old_spans)
    live = sorted((round(s["length_m"], 3), bool(s["exterior"])) for s in gr["spans"])
    if not (ref == mine == live and frozen["bands"] == len(old_bands) == gr["bands"]):
        raise SystemExit("OLD network does not reproduce the frozen V3 register - refusing to compare")

    # ---------------- four configurations for the causal attribution
    conf = {}
    for name, m, a in (("V3", False, False), ("MULTI_PARTNER_ONLY", True, False), ("ARC_OVERLAP_ONLY", False, True),
                       ("NEW", True, True)):
        bands, diag = bands_new(S, FACE_LAYERS, multi=m, arc=a) if (m or a) else (old_bands, {})
        spans, outers = spans_v3_rule(S, bands, cols)
        conf[name] = {"bands": bands, "spans": spans, "outers": outers, "diag": diag}
    new = conf["NEW"]

    # ---------------- footprints (R4 rule) for every configuration, layers 1 + 2
    fp_old = footprints(S, bands_v3(S, {"1", "2"}), cols)
    b12_new, _ = bands_new(S, {"1", "2"})
    fp_new = footprints(S, b12_new, cols)

    # ---------------- FP sheet: footings, straps, alignment
    src, S1M = fp_sheet(dxf)
    align = sheet_alignment(src, S1M)
    gbp0 = src.sheets["GBP"]["frame"]
    feet_gbp = footings_on(src, S1M, (gbp0[0], gbp0[1]))

    # ---------------- changelog
    def key(b):
        return frozenset(b["handles"])

    def blen(b):
        return b["arc_len"] if b["u"] is None else band_len(b["poly"], b)

    change_rows = []
    nb = {key(b): b for b in new["bands"]}
    ob = {key(b): b for b in old_bands}
    matched_new = set()
    for k, b in sorted(ob.items(), key=lambda kv: sorted(kv[0])):
        sup = [n for n in nb if k <= n]
        if not sup:
            change_rows.append({"OBJECT": "BAND", "OLD_ID": b["id"], "NEW_ID": "", "CHANGE": "REMOVED",
                                "OLD_LENGTH_M": r3(blen(b) / 1000), "NEW_LENGTH_M": None, "CAUSE": "UNEXPLAINED"})
            continue
        n = nb[sup[0]]
        matched_new.add(sup[0])
        dl = blen(n) - blen(b)
        if sup[0] == k and abs(dl) < 0.5:
            continue
        cause = ("MULTI_PARTNER_PAIRING" if n["rule"] == "MULTI_PARTNER_PAIRING" else
                 "ARC_OVERLAP" if n["kind"] == "ARC" else "UNEXPLAINED")
        detail = ""
        if cause == "MULTI_PARTNER_PAIRING":
            g = n["gn"]
            detail = (f"face(s) {g['faces_a']} pair with contiguous collinear partners {g['faces_b']} "
                      f"(old: single best partner)") if len(g["faces_b"]) > 1 else \
                (f"face(s) {g['faces_b']} pair with contiguous collinear partners {g['faces_a']} (old: single best "
                 "partner)")
        elif cause == "ARC_OVERLAP":
            g = n["gn"]
            detail = (f"arcs {g['SOURCE_HANDLES']}: ranges {g['ARC_A_RANGE']} / {g['ARC_B_RANGE']} -> common "
                      f"{g['OVERLAP_RANGE']}; r_c {g['CENTERLINE_RADIUS']:.1f} mm (old: first arc's sweep)")
        change_rows.append({"OBJECT": "BAND", "OLD_ID": b["id"], "NEW_ID": n["id"], "CHANGE": "CHANGED",
                            "OLD_LENGTH_M": r3(blen(b) / 1000), "NEW_LENGTH_M": r3(blen(n) / 1000),
                            "DELTA_M": r3(dl / 1000), "CAUSE": cause, "DETAIL": detail})
    for k, n in nb.items():
        if k not in matched_new:
            change_rows.append({"OBJECT": "BAND", "OLD_ID": "", "NEW_ID": n["id"], "CHANGE": "ADDED",
                                "OLD_LENGTH_M": None, "NEW_LENGTH_M": r3(blen(n) / 1000),
                                "CAUSE": "MULTI_PARTNER_PAIRING" if n["rule"] == "MULTI_PARTNER_PAIRING" else
                                "UNEXPLAINED"})

    def span_sig(sp):
        return (sp["band"], round(sp["length_mm"], 1), bool(sp["exterior"]))

    def match_spans(A, B):
        """A -> best B by overlap area."""
        out = {}
        for i, a in enumerate(A):
            best = max(((a["poly"].intersection(b["poly"]).area, j) for j, b in enumerate(B)), default=(0, None))
            out[i] = best[1] if best[0] > 1.0 else None
        return out

    def diffs(A, B):
        """spans of B that differ from A (by geometry match): set of (B index, kind)."""
        mAB = match_spans(A, B)
        mBA = match_spans(B, A)
        res = {}
        for j, b in enumerate(B):
            i = mBA[j]
            if i is None:
                res[j] = "ADDED"
                continue
            a = A[i]
            if abs(a["length_mm"] - b["length_mm"]) >= 0.5:
                res[j] = "LENGTH"
            elif a["exterior"] != b["exterior"]:
                res[j] = "EXTERIOR_FLAG"
        removed = [i for i, j in mAB.items() if j is None]
        return res, removed

    d_new, rem_new = diffs(conf["V3"]["spans"], new["spans"])
    d_mp, _ = diffs(conf["V3"]["spans"], conf["MULTI_PARTNER_ONLY"]["spans"])
    d_arc, _ = diffs(conf["V3"]["spans"], conf["ARC_OVERLAP_ONLY"]["spans"])

    def sig_set(spans, d):
        return {(round(spans[j]["poly"].centroid.x), round(spans[j]["poly"].centroid.y)): k for j, k in d.items()}
    mp_sig = sig_set(conf["MULTI_PARTNER_ONLY"]["spans"], d_mp)
    arc_sig = sig_set(conf["ARC_OVERLAP_ONLY"]["spans"], d_arc)
    mBA = match_spans(new["spans"], conf["V3"]["spans"])
    unexplained = []
    zone_area = {k: [round(o.area / 1e6, 2) for o in v["outers"]] for k, v in conf.items()}
    for j, kind in sorted(d_new.items()):
        sp = new["spans"][j]
        c = (round(sp["poly"].centroid.x), round(sp["poly"].centroid.y))
        causes = []
        near = lambda sigs: any(math.dist(c, s) < 50 for s in sigs)
        if near(mp_sig) or sp["b"]["rule"] == "MULTI_PARTNER_PAIRING":
            causes.append("MULTI_PARTNER_PAIRING")
        if near(arc_sig) or sp["b"]["kind"] == "ARC":
            causes.append("ARC_OVERLAP")
        cause = "+".join(causes) if causes else "UNEXPLAINED"
        if cause == "UNEXPLAINED":
            unexplained.append(j)
        oi = mBA.get(j)
        o = conf["V3"]["spans"][oi] if oi is not None else None
        change_rows.append({"OBJECT": "SPAN", "OLD_ID": f"{o['band']}@{r1(o['length_mm'])}" if o else "",
                            "NEW_ID": f"{sp['band']}@{r1(sp['length_mm'])}",
                            "CHANGE": {"ADDED": "ADDED", "LENGTH": "CHANGED", "EXTERIOR_FLAG": "CHANGED"}[kind],
                            "OLD_LENGTH_M": r3(o["length_mm"] / 1000) if o else None,
                            "NEW_LENGTH_M": r3(sp["length_mm"] / 1000),
                            "DELTA_M": r3((sp["length_mm"] - (o["length_mm"] if o else 0.0)) / 1000),
                            "OLD_EXTERIOR": o["exterior"] if o else "", "NEW_EXTERIOR": sp["exterior"],
                            "CAUSE": cause, "DETAIL": kind if kind != "EXTERIOR_FLAG" else (
                                "EXTERIOR_FLAG (V3 zone-outline proxy): the slab-zone outline containing the 'T=' note "
                                f"changes {zone_area['V3']} -> {zone_area['MULTI_PARTNER_ONLY']} m2 when the recovered "
                                "strip joins two band systems; the span geometry is unchanged")})
    for i in rem_new:
        o = conf["V3"]["spans"][i]
        change_rows.append({"OBJECT": "SPAN", "OLD_ID": f"{o['band']}@{r1(o['length_mm'])}", "NEW_ID": "",
                            "CHANGE": "REMOVED", "OLD_LENGTH_M": r3(o["length_mm"] / 1000), "CAUSE": "UNEXPLAINED"})
        unexplained.append(-1)
    # footprint (R4) exterior test: old spans with old footprints, new spans with new footprints
    fp_mp = footprints(S, bands_new(S, {"1", "2"}, multi=True, arc=False)[0], cols)
    fp_arc = footprints(S, bands_new(S, {"1", "2"}, multi=False, arc=True)[0], cols)
    on_fp = lambda g, fps: min(f.exterior.distance(g) for f in fps) < TOUCH
    for j, sp in enumerate(new["spans"]):
        oi = mBA.get(j)
        if oi is None:
            continue
        o = conf["V3"]["spans"][oi]
        a, b2 = on_fp(o["poly"], fp_old), on_fp(sp["poly"], fp_new)
        if a == b2:
            continue
        causes = []
        if on_fp(sp["poly"], fp_mp) != a:
            causes.append("MULTI_PARTNER_PAIRING")
        if on_fp(sp["poly"], fp_arc) != a:
            causes.append("ARC_OVERLAP")
        cause = "+".join(causes) or "UNEXPLAINED"
        change_rows.append({"OBJECT": "SPAN", "OLD_ID": f"{o['band']}@{r1(o['length_mm'])}",
                            "NEW_ID": f"{sp['band']}@{r1(sp['length_mm'])}", "CHANGE": "CHANGED",
                            "OLD_LENGTH_M": r3(o["length_mm"] / 1000), "NEW_LENGTH_M": r3(sp["length_mm"] / 1000),
                            "DELTA_M": r3((sp["length_mm"] - o["length_mm"]) / 1000), "OLD_EXTERIOR": a,
                            "NEW_EXTERIOR": b2, "CAUSE": cause,
                            "DETAIL": "EXTERIOR_FOOTPRINT_FLAG (R4 footprint-outline proxy) changes with the footprint "
                                      "outline; the span geometry is unchanged" if abs(sp["length_mm"] - o["length_mm"])
                            < 0.5 else "EXTERIOR_FOOTPRINT_FLAG + LENGTH"})
    r4rows = {r["span"]: r["footprint_edge"] for r in J(R4 / "GROUND_BEAM_REBAR_V4.json")["occurrences"]}
    r4_repro = sum(1 for s_ in gr["spans"] if r4rows.get(s_["id"]) == on_fp(s_["_poly"], fp_old))
    if unexplained or any(r["CAUSE"] == "UNEXPLAINED" for r in change_rows):
        raise SystemExit(f"STOP: geometry change not explained by MULTI_PARTNER_PAIRING / ARC_OVERLAP: "
                         f"{[r for r in change_rows if r['CAUSE'] == 'UNEXPLAINED']}")

    # ---------------- occurrences (NEW spans) + topology
    lib, claims = detail_library()
    rules = {r["rule_id"]: r for r in J(RULES)["rules"]}
    occs = []
    per_band = defaultdict(list)
    for sp in new["spans"]:
        per_band[sp["band"]].append(sp)
    for bid, sps in per_band.items():
        b = sps[0]["b"]
        if b["u"] is not None:
            sps.sort(key=lambda s: min(x * b["u"][0] + y * b["u"][1] for x, y in s["poly"].exterior.coords))
        else:
            sps.sort(key=lambda s: (round(s["poly"].centroid.x), round(s["poly"].centroid.y)))
        for k, sp in enumerate(sps):
            sp["occ_id"] = f"GSO-{bid.replace('ARC:', 'A-').replace('+', '-')}-{k + 1}"
    for sp in sorted(new["spans"], key=lambda s: s["occ_id"]):
        topo = classify_ends(sp, new["spans"], new["bands"], cols, feet_gbp)
        ext_b = min(f.exterior.distance(sp["poly"]) for f in fp_new) < TOUCH
        occ = {"occ_id": sp["occ_id"], "band": sp["band"], "handles": sp["b"]["handles"], "kind": sp["b"]["kind"],
               "rule": sp["b"]["rule"], "clear_m": sp["length_mm"] / 1000,
               "cc_m": topo["cc_mm"] / 1000 if topo["cc_mm"] is not None else None,
               "exterior_zone_test": bool(sp["exterior"]), "exterior_footprint_test": bool(ext_b), "topo": topo,
               "width_mm": (sp["b"]["gn"]["width"] if "gn" in sp["b"] else WIDTH)}
        occ["length_flags"] = (["CLEAR_EXCEEDS_SUPPORT_CENTRELINE: a support column does not cut the full band width "
                                "(narrower / offset column, V3 piece-extent convention); not resolved by a numerical "
                                "minimum - see PRE-S5.1 LENGTH_GEOMETRY_CONFLICT"] if occ["cc_m"] is not None and occ["cc_m"] < occ["clear_m"] - 1e-6
                               else [])
        occ["app"] = applicability(occ, lib)
        occ["app"]["flags"] += occ["length_flags"]
        occ["comp"] = readiness_gb(occ, occ["app"], lib, rules)
        occ["status"] = occ_status(occ["comp"])
        occs.append(occ)

    # ---------------- straps
    straps, strap_unbound = strap_census(src, S1M, dxf)
    for st in straps:
        st["comp"] = readiness_strap(st, rules)
        st["status"] = occ_status(st["comp"])
        st["app_state"] = ("EXPLICIT_MARK_MATCH" if st["AUTHORITY_STATE"] == "SOURCE_VERIFIED" else
                           "SOURCE_CONFLICT" if st["AUTHORITY_STATE"] == "SOURCE_CONFLICT" else "NO_APPLICABLE_DETAIL")

    # ---------------- conservation
    sd = new["diag"]["straight"]
    ad = new["diag"]["arcs"]
    faces_l1 = [r for r in sd["ledger"]]
    led_ok = all(abs(r["covered"] + r["unpaired"] - r["length"]) < 1e-6 for r in faces_l1)
    all_face_handles = {hx(p.identity.key) for p in sheet_parts(S, "SEGMENT")}
    accounted = {r["handle"] for r in sd["ledger"]} | {r["handle"] for r in sd["rejected_faces"]}
    arc_handles = {hx(p.identity.key) for p in sheet_parts(S, "ARC", FACE_LAYERS)}
    arc_acc = {h for b in ad["bands"] for h in b["handles"]} | {u["handle"] for u in ad["unpaired"]}
    band_total = sum(blen(b) for b in new["bands"])
    span_total = sum(s["length_mm"] for s in new["spans"])
    cons = {
        "every_sheet_line_accounted": accounted == all_face_handles,
        "every_layer1_face_covered_plus_unpaired_equals_length": led_ok,
        "every_layer1_arc_accounted": arc_handles <= arc_acc,
        "no_unexplained_change": not unexplained,
        "every_span_has_two_nodes": all(o["topo"]["start"]["kind"] and o["topo"]["end"]["kind"] for o in occs),
        "old_reproduces_frozen_v3": True,
        "old_footprint_test_reproduces_r4": r4_repro == len(gr["spans"]),
    }
    unpaired_rows = ([{"handle": u["handle"], "kind": "LINE", "length_mm": r1(u["length"]), "reason": u["reason"]}
                      for u in sd["unpaired"]] +
                     [{"handle": u["handle"], "kind": "ARC", "length_mm": r1(u["length"]), "reason": u["reason"],
                       "range_deg": u["range_deg"]} for u in ad["unpaired"]])
    node_counter = Counter()
    for o in occs:
        for e in ("start", "end"):
            node_counter[o["topo"][e]["kind"]] += 1
    summary = {
        "baseline": BASELINE, "engine_stamp": stamp, "drawing_sha256": DXF_SHA, "policy": GN.policy_record(),
        "old": {"bands": len(old_bands), "straight_bands": sum(1 for b in old_bands if b["kind"] == "STRAIGHT"),
                "arc_bands": sum(1 for b in old_bands if b["kind"] == "ARC"),
                "band_length_m": r3(sum(blen(b) for b in old_bands) / 1000), "spans": len(old_spans),
                "span_length_m": r3(sum(s["length_mm"] for s in old_spans) / 1000),
                "exterior_spans": sum(1 for s in old_spans if s["exterior"]),
                "reproduces_frozen_v3_register": True},
        "new": {"bands": len(new["bands"]), "straight_bands": sum(1 for b in new["bands"] if b["kind"] == "STRAIGHT"),
                "arc_bands": sum(1 for b in new["bands"] if b["kind"] == "ARC"),
                "band_length_m": r3(band_total / 1000), "spans": len(new["spans"]), "span_length_m": r3(span_total / 1000),
                "exterior_spans_zone_test": sum(1 for o in occs if o["exterior_zone_test"]),
                "exterior_spans_footprint_test": sum(1 for o in occs if o["exterior_footprint_test"]),
                "exterior_tests_agree": sum(1 for o in occs if o["exterior_zone_test"] == o["exterior_footprint_test"]),
                "multi_partner_bands": sum(1 for b in new["bands"] if b["rule"] == "MULTI_PARTNER_PAIRING"),
                "curved_spans": sum(1 for o in occs if o["kind"] == "ARC")},
        "changes": {"by_cause": dict(Counter(r["CAUSE"] for r in change_rows)),
                    "by_object": dict(Counter(f"{r['OBJECT']}:{r['CHANGE']}" for r in change_rows))},
        "network": {
            "physical_faces": {"sheet_lines": len(all_face_handles), "layer1_faces_admitted": len(sd["ledger"]),
                               "rejected_by_reason": dict(Counter(r["reason"] for r in sd["rejected_faces"])),
                               "layer1_arcs": len(arc_handles)},
            "accepted_bands": len(new["bands"]), "support_to_support_spans": len(new["spans"]),
            "nodes_by_kind": dict(node_counter),
            "column_intersections": len({c for o in occs for c in o["topo"]["columns"]}),
            "columns_on_sheet": len(cols),
            "footing_intersections": sorted({f for o in occs for f in o["topo"]["footings"]}),
            "spans_touching_footings": sum(1 for o in occs if o["topo"]["footings"]),
            "curved_spans": sum(1 for o in occs if o["kind"] == "ARC"),
            "free_end_nodes": [{"occurrence": o["occ_id"], "end": e} for o in occs for e in ("start", "end")
                               if o["topo"][e]["kind"] == "FREE_END"],
            "unpaired_physical_candidates": {"count": len(unpaired_rows),
                                             "by_reason": dict(Counter(u["reason"] for u in unpaired_rows)),
                                             "length_m": r3(sum(u["length_mm"] for u in unpaired_rows) / 1000),
                                             "rows": unpaired_rows},
            "conflicts": sd["conflicts"] + ad["conflicts"],
            "band_length_split_m": {"bands": r3(band_total / 1000), "spans": r3(span_total / 1000),
                                    "inside_columns_or_dropped": r3((band_total - span_total) / 1000)},
            "sheet_alignment_fp_gbp": align},
        "conservation": dict(cons, all_pass=all(cons.values())),
        "rule": "segmentation counts may differ; physical conservation (every face accounted, length = covered + "
                "unpaired) is the invariant",
    }

    # ---------------- readiness tallies
    tally = {"ground_beams": dict(Counter(o["status"] for o in occs)),
             "straps": dict(Counter(s["status"] for s in straps)),
             "gb_applicability": dict(Counter(o["app"]["state"] for o in occs)),
             "gb_component_status": {k: dict(Counter(o["comp"][k][0] for o in occs)) for k in occs[0]["comp"]},
             "strap_component_status": {k: dict(Counter(s["comp"][k][0] for s in straps)) for k in straps[0]["comp"]}}
    summary["readiness"] = tally

    # ---------------- outputs
    out = HERE
    wcsv(out / "01_GROUND_BEAM_GEOMETRY_CHANGELOG.csv", change_rows,
         ["OBJECT", "OLD_ID", "NEW_ID", "CHANGE", "OLD_LENGTH_M", "NEW_LENGTH_M", "DELTA_M", "OLD_EXTERIOR",
          "NEW_EXTERIOR", "CAUSE", "DETAIL"])
    wjson(out / "02_GROUND_BEAM_NETWORK_SUMMARY.json", summary)
    wcsv(out / "03_STRAP_OCCURRENCE_REGISTER.csv", straps,
         ["STRAP_OCCURRENCE_ID", "MARK", "TYPE", "PLAN", "SOURCE_HANDLES", "START_SUPPORT", "END_SUPPORT",
          "CLEAR_CONCRETE_LENGTH_M", "CENTERLINE_SUPPORT_TO_SUPPORT_M", "CENTERLINE_BASIS", "FOOTING_CENTRE_TO_CENTRE_M",
          "DRAWN_FACE_LENGTH_M", "WIDTH_DRAWN_MM", "WIDTH_SCHEDULE_CM", "DEPTH_SCHEDULE_CM",
          "SCHEDULE_DETAIL_REFERENCE", "REINFORCEMENT_REFERENCE", "AUTHORITY_STATE", "S1_STATE", "FLAGS"])
    det_rows = []
    for o in occs:
        a = o["app"]
        det_rows.append({
            "OCCURRENCE_ID": o["occ_id"], "BAND_HANDLES": o["handles"], "KIND": o["kind"], "PAIRING_RULE": o["rule"],
            "CLEAR_LENGTH_M": r3(o["clear_m"]), "SUPPORT_CENTRELINE_LENGTH_M": r3(o["cc_m"]),
            "START_SUPPORT": {k: o["topo"]["start"][k] for k in ("kind", "refs")},
            "END_SUPPORT": {k: o["topo"]["end"][k] for k in ("kind", "refs")},
            "INTERMEDIATE_JUNCTIONS": o["topo"]["intermediate"], "FOOTINGS_TOUCHED": o["topo"]["footings"],
            "EXTERIOR_ZONE_TEST": o["exterior_zone_test"], "EXTERIOR_FOOTPRINT_TEST": o["exterior_footprint_test"],
            "CONDITIONS_MET_BY_BASIS": a["by_basis"], "DETAIL_CANDIDATES": a["candidates"],
            "DETAIL_APPLICABILITY_STATE": a["state"], "DETAIL_ID": a["candidates"],
            "SOURCE_PAGE": sorted({lib[k]["page"] for k in a["candidates"]}),
            "SOURCE_HANDLES_TEXT": [f"{k}: {lib[k]['literal']}" for k in a["candidates"]],
            "SOURCE_CLAIM_STATE": {k: lib[k]["state"] for k in a["candidates"]},
            "WHY_APPLICABLE": a["why"], "WHY_NOT_APPLICABLE": a["why_not"], "FLAGS": a["flags"]})
    wcsv(out / "04_GROUND_BEAM_DETAIL_APPLICABILITY.csv", det_rows, list(det_rows[0]))

    # strap rebar source register
    src_rows = []
    for r in sbt_rows(dxf):
        src_rows.append({"SOURCE_ID": f"SBT:{r['insert']}", "MARK": r["mark"], "SOURCE_KIND": "SCHEDULE_ROW (SBT ATTRIB)",
                         "LOCATION": "Schedule of beams (ST7757.dxf model space, PDF p.10)", "HANDLES": [r["insert"]],
                         "CONTENT": r["attribs"], "APPLIES_TO": r["mark"],
                         "STATE": "SOURCE_CONFLICT (duplicate key)" if sum(1 for x in sbt_rows(dxf)
                                                                          if x["mark"] == r["mark"]) > 1 else
                         "EXPLICIT_MARK_MATCH",
                         "PROVIDES": "B, H, TOP count/dia, BOTTOM count/dia, stirrups per metre + dia",
                         "DOES_NOT_PROVIDE": "bottom row split, link legs / topology, hooks, development into footing"})
    for st in straps:
        src_rows.append({"SOURCE_ID": f"PLAN_TAG:{','.join(h for h in st['SOURCE_HANDLES'][-1:])}", "MARK": st["MARK"],
                         "SOURCE_KIND": "PLAN TAG (TEXT / block text)", "LOCATION": "Foundation plan (FP, p.2)",
                         "HANDLES": st["SOURCE_HANDLES"], "CONTENT": st["MARK"], "APPLIES_TO": st["STRAP_OCCURRENCE_ID"],
                         "STATE": "IDENTIFIES_THE_MEMBER_ONLY", "PROVIDES": "occurrence identity",
                         "DOES_NOT_PROVIDE": "reinforcement"})
    for rid, why in (("COVER_AGAINST_SOIL_70MM", "cover for stirrup path / bar positions"),
                     ("DEVELOPMENT_STARTER_70D_40D", "starter bars only - not a strap-end anchorage rule"),
                     ("SIDE_BARS_NOTE_21", "depth > 60 cm only - straps are 40-50 cm"),
                     ("HOOKS_AND_BENDS", "no project source")):
        rr = rules[rid]
        applies = bool({"STRAP_BEAM", "ALL"} & set(rr.get("applies_to") or []))
        src_rows.append({"SOURCE_ID": f"RULE:{rid}", "MARK": "ALL STRAPS", "SOURCE_KIND": "GENERAL NOTE (p.8) / rule",
                         "LOCATION": f"claim {rr.get('claim_id')}", "HANDLES": [], "CONTENT": rr["value"],
                         "APPLIES_TO": "STRAP_BEAM" if applies else "NOT_STRAP_BEAM",
                         "STATE": rr["source_state"] if applies else "NOT_APPLICABLE", "PROVIDES": why,
                         "DOES_NOT_PROVIDE": "" if applies else "anything for straps"})
    strap_claims = [c for c in claims.values() if "STRAP" in json.dumps(c).upper() or "S.B" in c["raw_visual_transcription"]]
    src_rows.append({"SOURCE_ID": "SEARCH:VISUAL_CLAIMS_P8_P13_P14", "MARK": "ALL STRAPS",
                     "SOURCE_KIND": "DETAIL / SECTION search", "LOCATION": "ST7757.pdf pp.8, 13-16 claim register",
                     "HANDLES": [c["claim_id"] for c in strap_claims], "CONTENT": len(strap_claims),
                     "APPLIES_TO": "STRAP_BEAM",
                     "STATE": "NO_APPLICABLE_DETAIL" if not strap_claims else "SEE_CLAIMS",
                     "PROVIDES": "no strap section / detail exists in the claimed pages" if not strap_claims else "",
                     "DOES_NOT_PROVIDE": "link topology, development"})
    src_rows.append({"SOURCE_ID": "SEARCH:DXF_TEXT_MTEXT", "MARK": "ALL STRAPS", "SOURCE_KIND": "TEXT / MTEXT search",
                     "LOCATION": "ST7757.dxf model space + blocks (pattern S.B<n> / SB<n> / STRAP)",
                     "HANDLES": sorted({h for st in straps for h in st["SOURCE_HANDLES"][-1:]}),
                     "CONTENT": "plan tags only", "APPLIES_TO": "STRAP_BEAM", "STATE": "IDENTIFIES_THE_MEMBER_ONLY",
                     "PROVIDES": "no reinforcement text other than the SBT rows", "DOES_NOT_PROVIDE": "reinforcement"})
    wcsv(out / "05_STRAP_REBAR_SOURCE_REGISTER.csv", src_rows,
         ["SOURCE_ID", "MARK", "SOURCE_KIND", "LOCATION", "HANDLES", "CONTENT", "APPLIES_TO", "STATE", "PROVIDES",
          "DOES_NOT_PROVIDE"])

    # readiness matrix: one row per occurrence x component family
    mat = []
    fam_order = ("TOP_MAIN", "BOTTOM_ROW_1", "BOTTOM_ROW_2", "SIDE_BARS", "STIRRUP_DIAMETER", "STIRRUP_RATE",
                 "STIRRUP_CORE_PATH", "STIRRUP_COUNT", "HOOK_1", "HOOK_2", "END_ZONE_EXTRA", "END_TREATMENT",
                 "DEVELOPMENT_INTO_SUPPORT_1", "DEVELOPMENT_INTO_SUPPORT_2", "LAP")
    templates = []

    def node(n):
        if n is None:
            return {"kind": "FREE_END", "refs": []}
        return {"kind": n["kind"], "refs": n.get("refs") or [n.get("footing")]}

    for o in occs:
        a = o["app"]
        t = GP.template(family="GROUND_BEAM", occurrence_id=o["occ_id"], mark="GB (typical p.13)", start_node=node(o["topo"]["start"]),
                        end_node=node(o["topo"]["end"]), handles=o["handles"], detail_id=a["candidates"],
                        applicability=a["state"], context=context)
        ready = GP.provenance_ready(t)
        templates.append(t)
        exterior = "P13-GB-EXTERIOR" in a["candidates"]
        depth = (" | ".join(sorted({str(lib[k]["D"]) for k in a["candidates"]})) if a["candidates"] else "")
        base = {"OCCURRENCE_ID": o["occ_id"], "MEMBER_FAMILY": "GROUND_BEAM" + ("_CURVED" if o["kind"] == "ARC" else ""),
                "MARK": "untagged (p.13 typical sections)",
                "LENGTH_SOURCE": f"DXF GBP layer-1 face pair, clear between supports {o['clear_m']:.3f} m"
                                 + (f"; support centreline {o['cc_m']:.3f} m" if o["cc_m"] is not None else "")
                                 + "; bar run: PRE-S5.1 support face-to-face",
                "WIDTH_SOURCE": f"DXF face separation {o['width_mm']:.0f} mm = section B 300",
                "DEPTH_SOURCE": ("FOLLOW ARCH. (not printed)" if exterior and len(a["candidates"]) == 1 else
                                 f"p.13 section D candidates: {depth}" if a["candidates"] else "none"),
                "REBAR_DETAIL_ID": a["candidates"], "DETAIL_APPLICABILITY": a["state"],
                "TOP_MAIN": o["comp"]["TOP_MAIN"][1], "BOTTOM_ROW_1": o["comp"]["BOTTOM_ROW_1"][1],
                "BOTTOM_ROW_2": o["comp"]["BOTTOM_ROW_2"][1], "SIDE_REBAR": o["comp"]["SIDE_BARS"][1],
                "STIRRUP_DIAMETER": o["comp"]["STIRRUP_DIAMETER"][1], "STIRRUP_RATE": o["comp"]["STIRRUP_RATE"][1],
                "STIRRUP_GEOMETRY": o["comp"]["STIRRUP_CORE_PATH"][0], "END_TREATMENT": o["comp"]["END_TREATMENT"][0],
                "DEVELOPMENT": o["comp"]["DEVELOPMENT_INTO_SUPPORT_1"][0], "PROVENANCE_READY": ready,
                "OCCURRENCE_S5_STATUS": o["status"]}
        for f in fam_order:
            st_, val, why = o["comp"][f]
            inv = a["state"] == "CANDIDATE_DETAIL" and st_ in ("READY", "READY_LOWER_BOUND")
            mat.append(dict(base, COMPONENT=f, COMPONENT_VALUE=val, S5_STATUS=st_, WHY=why,
                            CANDIDATE_INVARIANT=inv,
                            MAY_RELEASE=st_ in ("READY", "READY_LOWER_BOUND") and
                            GP.may_release(a["state"], candidate_invariant=inv)))
    for st in straps:
        rows_def = st["_rows"]
        t = GP.template(family="STRAP_BEAM", occurrence_id=st["STRAP_OCCURRENCE_ID"], mark=st["MARK"], start_node=node(st["START_SUPPORT"]),
                        end_node=node(st["END_SUPPORT"]),
                        handles=st["SOURCE_HANDLES"], detail_id=[f"SBT:{r['insert']}" for r in rows_def],
                        applicability=st["app_state"], context=context)
        ready = GP.provenance_ready(t)
        templates.append(t)
        base = {"OCCURRENCE_ID": st["STRAP_OCCURRENCE_ID"], "MEMBER_FAMILY": "STRAP_BEAM", "MARK": st["MARK"],
                "LENGTH_SOURCE": f"DXF FP strap faces; clear between footing faces {st['CLEAR_CONCRETE_LENGTH_M']} m; "
                                 f"column c/c {st['CENTERLINE_SUPPORT_TO_SUPPORT_M']} m",
                "WIDTH_SOURCE": f"SBT W {st['WIDTH_SCHEDULE_CM']} cm; drawn {st['WIDTH_DRAWN_MM']} mm",
                "DEPTH_SOURCE": f"SBT H {st['DEPTH_SCHEDULE_CM']} cm",
                "REBAR_DETAIL_ID": [f"SBT:{r['insert']}" for r in rows_def], "DETAIL_APPLICABILITY": st["app_state"],
                "TOP_MAIN": st["comp"]["TOP_MAIN"][1], "BOTTOM_ROW_1": st["comp"]["BOTTOM_ROW_1"][1],
                "BOTTOM_ROW_2": st["comp"]["BOTTOM_ROW_2"][1], "SIDE_REBAR": st["comp"]["SIDE_BARS"][1],
                "STIRRUP_DIAMETER": st["comp"]["STIRRUP_DIAMETER"][1], "STIRRUP_RATE": st["comp"]["STIRRUP_RATE"][1],
                "STIRRUP_GEOMETRY": st["comp"]["STIRRUP_CORE_PATH"][0], "END_TREATMENT": st["comp"]["END_TREATMENT"][0],
                "DEVELOPMENT": st["comp"]["DEVELOPMENT_INTO_SUPPORT_1"][0], "PROVENANCE_READY": ready,
                "OCCURRENCE_S5_STATUS": st["status"]}
        for f in fam_order:
            st_, val, why = st["comp"][f]
            mat.append(dict(base, COMPONENT=f, COMPONENT_VALUE=val, S5_STATUS=st_, WHY=why, CANDIDATE_INVARIANT=False,
                            MAY_RELEASE=st_ in ("READY", "READY_LOWER_BOUND") and GP.may_release(st["app_state"])))
    wcsv(out / "06_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv", mat,
         ["OCCURRENCE_ID", "MEMBER_FAMILY", "MARK", "COMPONENT", "COMPONENT_VALUE", "S5_STATUS", "WHY",
          "CANDIDATE_INVARIANT", "MAY_RELEASE",
          "LENGTH_SOURCE", "WIDTH_SOURCE", "DEPTH_SOURCE", "REBAR_DETAIL_ID", "DETAIL_APPLICABILITY", "TOP_MAIN",
          "BOTTOM_ROW_1", "BOTTOM_ROW_2", "SIDE_REBAR", "STIRRUP_DIAMETER", "STIRRUP_RATE", "STIRRUP_GEOMETRY",
          "END_TREATMENT", "DEVELOPMENT", "PROVENANCE_READY", "OCCURRENCE_S5_STATUS"])
    wjson(out / "S5_PROVENANCE_TEMPLATES.json", {"fields": list(GP.S5_PROVENANCE_FIELDS),
                                                 "extra_fields": list(GP.S5_EXTRA_FIELDS),
                                                 "context": context, "templates": templates})

    # F3 provenance check (S4 frozen record is not edited)
    f3 = J(S4_F3)
    f3_occ = [r for r in J(S1 / "FOOTING_OCCURRENCE_REGISTER.json")["rows"] if r.get("type") == "F3"]
    wjson(out / "F3_PROVENANCE_CHECK.json", {
        "s4_record": "research/alsenan_footing_rebar_s4/F3_AUTHORITY_DECISION.json (frozen; not edited)",
        "s4_record_sha256": _sha(S4_F3),
        "finding": "the S4 decision is drawing-based, but its 'project_source' sentence also cites the R9.1 donor "
                   "crosswalk (08 FO10 / FO11) next to the drawing handles; a donor crosswalk is corroboration, never "
                   "the authority. The per-part S4 provenance cites drawing handles only.",
        "corrected_authority": {
            "decision": "F3 = 2 occurrences, SOURCE_VERIFIED",
            "authority": "PROJECT_DRAWING",
            "evidence": [{"outline": r["outline"]["handle"], "tag": (r.get("tag") or {}).get("handle"),
                          "tag_text": (r.get("tag") or {}).get("text"), "drawn_cm": [r["sizes"]["drawn_L_cm"],
                                                                                    r["sizes"]["drawn_W_cm"]],
                          "schedule_cm": [r["sizes"]["schedule_L_cm"], r["sizes"]["schedule_W_cm"]],
                          "sizes_match": r["sizes"]["match"]} for r in f3_occ],
            "drawing": {"file": "ST7757.dxf", "sha256": DXF_SHA, "sheet": "FOUNDATION PLAN (PDF p.2)"},
            "corroboration_only": ["R9.1 08_FOOTING_OCCURRENCE_CROSSWALK FO10 / FO11 (donor crosswalk)"],
            "comparison_flags": [f3["question"]]},
        "quantity_changed": False, "s4_freeze_changed": False})

    index = {"baseline": BASELINE, "engine_stamp": stamp, "drawing_sha256": DXF_SHA,
             "inputs": {str(Path(p).relative_to(ROOT)): _sha(p) for p in INPUTS},
             "code": {c: _sha(ROOT / c) for c in CODE},
             "outputs": {n: _sha(out / n) for n in sorted(os.listdir(out))
                         if n[:2].isdigit() and n.endswith((".csv", ".json"))
                         or n in ("S5_PROVENANCE_TEMPLATES.json", "F3_PROVENANCE_CHECK.json")}}
    wjson(out / "INDEX.json", index)
    print(json.dumps({"old": summary["old"], "new": summary["new"], "changes": summary["changes"],
                      "conservation": summary["conservation"], "readiness": {k: v for k, v in tally.items()
                                                                             if not k.endswith("component_status")}},
                     indent=1))
    return summary


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DXF)
