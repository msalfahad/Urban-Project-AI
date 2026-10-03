"""ALSENAN / P7757 + ST7757 - PHASE B2A (GENERIC ENGINE IMPROVEMENT + OWNER METHODS; SHADOW; source-driven, frozen
BEFORE the benchmark is read for evaluation).

    python3 research/external_engine_lab/alsenan_phase_b2a.py <work_dir> <register_dir> [code_commit]

PROJECT ADAPTER (facts only) on top of the A3 adapter (which reruns A2 + A3 from the ORIGINAL SOURCE). B2A adds, all
through generic engines (engine/source):
    beam_binding          tag -> band binding with positive constraints, occurrences, four length bases
    structural_vertical   per-column controlling member, interval, joint; neck fail-closed
    slab_region           slab plate / openings / thickness per roof sheet
    concrete_model        physical non-overlapping storey model + gross beam view + stair (fail-closed)
    opening_authority     door evidence from closures / swings, function UNKNOWN when ambiguous
    curved_opening        inner / centre / outer / chord + the inner-face method
    finish_height         blockwork / plaster / paint / wall-tile heights per room face
    waterproofing_policy  roof (0.20 upturn) / wet (0.15 upturn); laps separate
    urban_methods         versioned method register
Project facts here: the owner statements of this round (OF-B2A-A..F), the printed FFLs (A2 transcription), layer
names of the line work census (element / column / opening / stair layers). No benchmark value, no Qortuba fact.
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import ezdxf                                                                                         # noqa: E402
from shapely.geometry import LineString, Point, Polygon                                              # noqa: E402

from engine.source import benchmark_firewall as FW, canonical_input as CI, entity_role_inference as ERI  # noqa: E402
from engine.source import beam_binding as BB, concrete_model as CM, curved_opening as CO               # noqa: E402
from engine.source import finish_height as FH, opening_authority as OA, slab_region as SR              # noqa: E402
from engine.source import structural_schedule as SS, structural_vertical as SV, topology as T          # noqa: E402
from engine.source import urban_methods as UM, waterproofing_policy as WP                              # noqa: E402

import alsenan_phase_a as AP                                                                         # noqa: E402
import alsenan_phase_a2 as A2                                                                        # noqa: E402
import alsenan_phase_a3 as A3                                                                        # noqa: E402

PHASE = "ALSENAN_P7757_ST7757_PHASE_B2A"
FLOORS = ("GF", "1F", "2F")
ROOF_SHEET = {"GF": "GF_ROOF_SLAB", "1F": "1F_ROOF_SLAB", "2F": "2F_ROOF_SLAB"}
STOREY_BAND = {"GF": "GROUND FLOOR", "1F": "1ST FLOOR", "2F": "2ND FLOOR & TOP"}
ELEMENT_LAYERS = ("1", "S-BEAM")          # census: beam band / slab edge line work on the slab sheets
COLUMN_LAYER = "S-COL.BON"
OPENING_LAYER = "S-OPENING"
STAIR_LAYERS = ("2", "5", "ST")
DOOR_LAYER = "D"
TOL_MM = 10.0                              # authoring tolerance for breadths (as A3)
MAX_SUPPORT_MM = 1200.0                    # a girder / column support is at most this wide along a beam
BAND_SEARCH_MM = (100.0, 1000.0)           # unbound band candidates around a column: drawn breadth window
COLUMN_TAG_ADJ = 6.0                       # column tag -> outline: clear gap in text heights
COLUMN_TAG_MARGIN = 2.0                    # second outline of the same printed size must be this many text heights
                                           # farther (and 1.5x) - otherwise AMBIGUOUS
SIDE_PROBE_MM = 300.0                      # beyond the wall face when testing which space an opening joins


def _vt(vid):
    return next(v for v in A2.VERTICAL_TRANSCRIPTIONS if v["id"] == vid)


LEVELS = [{"name": "GF", "level_m": _vt("VE-AA-04")["value_m"], "kind": "FFL", "source": "VE-AA-04"},
          {"name": "1F", "level_m": _vt("VE-AA-05")["value_m"], "kind": "FFL", "source": "VE-AA-05"},
          {"name": "2F", "level_m": _vt("VE-AA-06")["value_m"], "kind": "FFL", "source": "VE-AA-06"},
          {"name": "ROOF", "level_m": _vt("VE-AA-07")["value_m"], "kind": "ROOF_LEVEL", "source": "VE-AA-07"}]

# ------------------------------------------------------------------ owner statements of THIS round (project facts)
OWNER_FACTS_B2A = [
    {"id": "OF-B2A-A", "class": "PROJECT_OWNER_FACT", "scope": {"floor": "GF", "labels": ["DINING", "RECEPTION", "SALOON"]},
     "fact": {"internal_doors": 0, "open_to_each_other": True},
     "statement": "GF Dining, Reception and Salon are open to each other; no internal doors",
     "use": "one physical site, several semantic zones; no wall is invented between them"},
    {"id": "OF-B2A-B", "class": "PROJECT_OWNER_FACT", "scope": {"floor": "GF", "label": "RECEPTION"},
     "fact": {"double_height": "ENTIRE_RECEPTION"}, "statement": "the entire Reception is double height",
     "use": "a DOUBLE_HEIGHT_FINISH_REGION inside the open site"},
    {"id": "OF-B2A-C", "class": "PROJECT_OWNER_FACT", "alias": "ALSENAN_MBR_WARDROBE_OWNER_FACT",
     "scope": {"floor": "GF", "label": "MASTER BED ROOM"}, "fact": {"box_mm": [500, 1460], "role": "WARDROBE / FIXED_JOINERY"},
     "statement": "the 0.50 x 1.46 m box in the GF master bedroom is a wardrobe (fixed joinery); it does not split the room",
     "method": "URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1"},
    {"id": "OF-B2A-D", "class": "PROJECT_OWNER_FACT", "scope": {"floor": "GF", "label": "SALOON", "element": "sea-view opening"},
     "fact": {"material": "ALUMINIUM_GLASS"}, "statement": "the Salon sea-view opening is aluminium + glass",
     "carries": "OF-A3-SALON-MATERIAL"},
    {"id": "OF-B2A-E", "class": "SOURCE_EVIDENCE", "scope": {"floor": "GF", "label": "SALOON", "element": "sea-view opening"},
     "fact": {"width_m": 6.33}, "statement": "Salon opening width 6.33 m is source-correlated (printed 633 + CAD gap)"},
    {"id": "OF-B2A-F", "class": "OWNER_DERIVED_PROJECT_DIMENSION", "scope": {"floor": "GF", "label": "SALOON",
     "element": "sea-view opening"}, "fact": {"height_m": 3.65, "status": "PROVISIONAL"},
     "statement": "Salon aluminium height 3.65 m is provisional, not final authority", "carries": "OF-A3-SALON-HEIGHT"},
]
NO_FACT = {"F_F10": "no owner fact: SOURCE_CONFLICT stays BLOCKED", "benchmark": "no benchmark statement is a fact"}


# ------------------------------------------------------------------ build
def build(work, commit=None) -> dict:
    work = Path(work)
    ctx = A3.build(work, commit)
    ctx["_work"] = str(work)
    with FW.OpenAudit() as audit:
        ctx["b2a"] = _b2a(ctx, work)
    ctx["b2a"]["firewall_audit"] = audit.opened
    return ctx


def _rotations(path) -> dict:
    """TEXT rotation (deg) by decimal handle (the K2 source_handle form)."""
    doc = ezdxf.readfile(str(path))
    out = {}
    for e in doc.modelspace().query("TEXT"):
        out[str(int(e.dxf.handle, 16))] = float(e.dxf.rotation) if e.dxf.hasattr("rotation") else 0.0
    return out


def _libs(ctx) -> dict:
    rows = {t: {"B_cm": v["B_cm"], "D_cm": v["D_cm"]} for t, v in A3._simple_beam_library(ctx).items()}
    rows.update({r["type"]: {"B_cm": r["B_cm"], "D_cm": r["H_cm"]} for r in A3.CB_TRANSCRIPTION})
    return BB.split_library(rows)


def _rect_poly(r):
    (cx, cy), w, h = r[3], r[1], r[2]
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]


def _col_rects(S, bounds):
    cs = [p for p in S["parts"] if p.kind == "SEGMENT" and CI.effective_layer(p)[0] == COLUMN_LAYER
          and AP.in_box(p.geometry[0], p.geometry[1], bounds)]
    rs = ERI._rectangles([tuple(p.geometry) for p in cs], [p.identity.key for p in cs], 1.0)
    return sorted(rs, key=lambda r: (round(r[3][0], 3), round(r[3][1], 3)))


def _b2a(ctx, work) -> dict:
    S = A3._blob(ctx, work, "ST7757.dxf")
    A = A3._blob(ctx, work, "P7757.dxf")
    rot = _rotations(work / ctx["paths"]["ST7757.dxf"])
    libs = _libs(ctx)
    out = {"namespace_audit": BB.namespace_audit(libs), "libraries": libs,
           "policies": {"beam_binding": BB.policy_record(), "structural_vertical": SV.policy_record(),
                        "slab_region": SR.policy_record(), "concrete_model": CM.policy_record(),
                        "opening_authority": OA.policy_record(), "finish_height": FH.policy_record()},
           "owner_facts": OWNER_FACTS_B2A, "no_fact": NO_FACT, "methods": UM.register()}
    out["intervals"] = SV.storey_intervals(LEVELS)
    out["sheets"] = {fl: _sheet(ctx, S, ROOF_SHEET[fl], rot, libs) for fl in FLOORS}
    out["registration"] = _registration(ctx, A, S)
    out["columns"] = _columns(ctx, S, out, libs)
    out["concrete"] = _concrete(ctx, out)
    out["structural_items"] = _items(ctx, out)
    out["stairs"] = _stairs(ctx)
    out["architecture"] = _architecture(ctx, A, out)
    return out


# ------------------------------------------------------------------ per roof sheet: binding, occurrences, slab
def _sheet(ctx, S, key, rot, libs) -> dict:
    sb = ctx["structural_sheets"][key]["bounds"]
    inb = lambda p: AP.in_box(p.geometry[0], p.geometry[1], sb)
    lay = lambda p: CI.effective_layer(p)[0]
    segs = [(p.identity.key,) + tuple(p.geometry) for p in S["parts"] if p.kind == "SEGMENT" and lay(p) in ELEMENT_LAYERS and inb(p)]
    arcs = [(p.identity.key,) + tuple(p.geometry[:5]) for p in S["parts"] if p.kind == "ARC" and lay(p) in ELEMENT_LAYERS and inb(p)]
    rects = _col_rects(S, sb)
    cols = [{"id": "COL:" + "+".join(sorted(r[0])[:2]), "polygon": _rect_poly(r), "w_mm": round(r[1], 1), "h_mm": round(r[2], 1),
             "centre": [round(r[3][0], 3), round(r[3][1], 3)]} for r in rects]
    tx = sorted([t for t in S["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, sb)], key=lambda t: t.identity.key)
    types = sorted({t for lib in libs.values() for t in lib})
    marks = []
    for t in tx:
        pm = SS.parse_mark(t.value.strip(), types, normalise=False)
        if len(pm["types"]) == 1:
            marks.append({"key": t.identity.key, "value": t.value.strip(), "type": pm["types"][0], "x": t.x, "y": t.y,
                          "height": t.height, "rotation_deg": rot.get(t.identity.source_handle, 0.0)})
    lines = BB.merge_lines(segs, eps=AP.EPS)
    bound = BB.bind(marks, libs, lines, segs, umm=1.0, tol_mm=TOL_MM, eps=AP.EPS)
    ok = [r for r in bound if r["state"] in BB.BOUND_STATES]
    spans = {r["type"]: r["spans_m"] for r in A3.CB_TRANSCRIPTION}
    occ = BB.occurrences(ok, segs, umm=1.0, eps=AP.EPS, max_support_mm=MAX_SUPPORT_MM, schedule_spans=spans, columns=cols)
    for o in occ["occurrences"]:
        o["band_polygon"] = [[round(x, 3), round(y, 3)] for x, y in BB.band_polygon(o["band_record"])]
        if o["namespace"] == "CONTINUOUS" and o["state"] == "MEASURED":
            n_sched = len(spans.get(o["type"], []))
            o["schedule_spans"] = n_sched
            o["tags_vs_spans"] = f"{len(o['tags'])} tag(s) / {n_sched} span(s)"
            if o["segments_between_supports"] != n_sched or len(o["tags"]) != n_sched:
                o["state"] = "SPAN_COUNT_MISMATCH"
    # slab region
    ops = [(p.identity.key,) + tuple(p.geometry) for p in S["parts"] if p.kind == "SEGMENT" and lay(p) == OPENING_LAYER and inb(p)]
    sts = [(p.identity.key,) + tuple(p.geometry) for p in S["parts"] if p.kind == "SEGMENT" and lay(p) in STAIR_LAYERS and inb(p)]
    voids = [(t.x, t.y) for t in tx if t.value.strip().upper() == "VOID"]
    tags = []
    for t in tx:                                                     # 'T' over the thickness inside one tag (as A3)
        if t.value.strip() == "T":
            below = [u for u in tx if u is not t and re.fullmatch(r"\d{2}", u.value.strip()) and abs(u.x - t.x) < 300
                     and 0 < t.y - u.y < 500]
            if len(below) == 1:
                tags.append({"t_cm": int(below[0].value.strip()), "x": t.x, "y": t.y})
    bp = []
    for r in ok:
        b = r["band"]
        mid = (b["lo"] + b["hi"]) / 2.0
        bp.append((r["mark_key"], b["u"][0] * b["tag_t"] + b["n"][0] * mid, b["u"][1] * b["tag_t"] + b["n"][1] * mid))
    slab = SR.regions(segments=segs, arcs=arcs, columns=cols, void_labels=voids, opening_segments=ops, stair_segments=sts,
                      thickness_tags=tags, band_points=bp, umm=1.0, eps=AP.EPS)
    rings = slab.pop("_rings")
    dang = slab.pop("_dangles", [])
    gross, plate = _polygons(rings)
    return {"sheet": key, "bounds": sb, "element_segments": len(segs), "element_arcs": len(arcs), "merged_lines": len(lines),
            "columns": cols, "marks": len(marks), "binding": bound, "binding_states": dict(Counter(r["state"] for r in bound)),
            "occurrences": occ["occurrences"], "occurrence_notes": occ["notes"],
            "occurrence_states": dict(Counter(o["state"] for o in occ["occurrences"])),
            "slab": slab, "dangles": dang, "_plate": plate, "_gross": gross, "_lines": lines, "_segs": segs}


def _polygons(rings):
    """Shapely views of the slab-region rings (research side only; engine/source stays stdlib)."""
    from shapely.ops import unary_union
    def poly(r):
        p = Polygon(r)
        return p if p.is_valid else p.buffer(0)
    outer = [poly(r) for r in rings["outer"] if len(r) >= 3]
    if not outer:
        return None, None
    gross = unary_union(outer)
    ops = [poly(r) for r in rings["openings"] if len(r) >= 3]
    plate = gross.difference(unary_union(ops)) if ops else gross
    return gross, plate


# ------------------------------------------------------------------ cross-document registration
def _vote(a, b):
    c = Counter()
    for x in a:
        for y in b:
            if round(x[1]) == round(y[1]) and round(x[2]) == round(y[2]):
                c[(round(y[3][0] - x[3][0], 1), round(y[3][1] - x[3][1], 1))] += 1
    return c.most_common(2)


def _registration(ctx, A, S) -> dict:
    """Architectural plan of storey X <-> structural 'X ROOF SLAB' sheet: a translation is REGISTERED only when every
    architectural column outline lands on an equal outline under ONE translation and no other translation explains
    more than one outline."""
    out = {}
    for fl in FLOORS:
        a = [r for r in _col_rects(A, ctx["sheets_by_floor"][fl]["bounds"])]
        b = _col_rects(S, ctx["structural_sheets"][ROOF_SHEET[fl]]["bounds"])
        v = _vote(a, b)
        best = v[0] if v else (None, 0)
        second = v[1][1] if len(v) > 1 else 0
        ok = best[0] is not None and best[1] == len(a) and len(a) >= 5 and second <= 1
        out[fl] = {"architectural_outlines": len(a), "structural_outlines": len(b), "translation": best[0],
                   "matched": best[1], "second_best": second, "state": "REGISTERED" if ok else "NOT_REGISTERED"}
    return out


def _to_sheet(reg, fl, x, y):
    dx, dy = reg[fl]["translation"]
    return x + dx, y + dy


# ------------------------------------------------------------------ columns
def _frame_offset(ctx, a, b):
    A_, B_ = ctx["structural_sheets"][a]["bounds"], ctx["structural_sheets"][b]["bounds"]
    same = abs((A_[2] - A_[0]) - (B_[2] - B_[0])) <= 2 and abs((A_[3] - A_[1]) - (B_[3] - B_[1])) <= 2
    return (B_[0] - A_[0], B_[1] - A_[1]), same


def _bind_column_tags(ctx, S, lib) -> list:
    sb = ctx["structural_sheets"]["COLUMN_AXIS"]["bounds"]
    rects = _col_rects(S, sb)
    tx = [t for t in S["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, sb) and t.layer == A3.STRUCT_LAYERS["text"]]
    tags = sorted([t for t in tx if t.value.strip() in lib], key=lambda t: t.identity.key)
    sizes = [t for t in tx if SS.SIZE_LABEL.match(t.value.strip())]
    out = []
    for t in tags:
        h = t.height
        L = len(t.value.strip()) * h * BB.CHAR_WIDTH
        lab = [s for s in sizes if min(t.x + L, s.x + len(s.value.strip()) * s.height * BB.CHAR_WIDTH) - max(t.x, s.x) > 0
               and 0 < t.y - s.y < 2.5 * h]                       # the size label printed under the tag
        rec = {"tag_key": t.identity.key, "type": t.value.strip(), "xy": [round(t.x, 3), round(t.y, 3)]}
        if len(lab) != 1:
            out.append(dict(rec, state="SIZE_LABEL_NOT_PAIRED", labels=len(lab)))
            continue
        m = SS.SIZE_LABEL.match(lab[0].value.strip())
        printed = tuple(sorted((int(m.group(1)) * 10, int(m.group(2)) * 10)))
        f = lib[rec["type"]]["FOUNDATION"]
        rec["printed_size_cm"] = lab[0].value.strip()
        rec["printed_vs_schedule_foundation"] = ("AGREES" if f["B_cm"] and tuple(sorted((f["B_cm"] * 10, f["D_cm"] * 10))) == printed
                                                 else "DIFFERS")
        cands = []
        for r in rects:
            if tuple(sorted((round(r[1]), round(r[2])))) != printed:
                continue
            (cx, cy), w, hh = r[3], r[1], r[2]
            gx = max(cx - w / 2 - (t.x + L), t.x - (cx + w / 2), 0.0)
            gy = max(cy - hh / 2 - (t.y + h), t.y - (cy + hh / 2), 0.0)
            cands.append((math.hypot(gx, gy) / h, r))
        cands.sort(key=lambda c: (c[0], c[1][3]))
        if not cands or cands[0][0] > COLUMN_TAG_ADJ:
            out.append(dict(rec, state="NO_OUTLINE_OF_PRINTED_SIZE_ADJACENT"))
            continue
        g0 = cands[0][0]
        if len(cands) > 1 and cands[1][0] <= max(g0 + COLUMN_TAG_MARGIN, 1.5 * g0):
            out.append(dict(rec, state="AMBIGUOUS_OUTLINE", gaps_in_text_heights=[round(c[0], 3) for c in cands[:3]]))
            continue
        r = cands[0][1]
        out.append(dict(rec, state="BOUND", gap_in_text_heights=round(g0, 3), outline=_rect_poly(r),
                        outline_keys=sorted(r[0]), outline_mm=[round(r[1], 1), round(r[2], 1)]))
    seen = Counter(json.dumps(o.get("outline_keys")) for o in out if o["state"] == "BOUND")
    for o in out:
        if o["state"] == "BOUND" and seen[json.dumps(o["outline_keys"])] > 1:
            o["state"] = "OUTLINE_CLAIMED_TWICE"
    return out


def _unbound_bands(sheet, rect_poly, bound_keys) -> list:
    """Parallel element-line pairs (drawn breadth within BAND_SEARCH_MM) whose footprint touches the column outline,
    with no element line between them and no line shared with a bound band - members the tags did not name."""
    lines = sheet["_lines"]
    out = []
    near = [l for l in lines if _line_near_poly(l, rect_poly, BAND_SEARCH_MM[1])]
    for i, a in enumerate(near):
        for b in near[i + 1:]:
            if abs(a["angle"] - b["angle"]) > 1e-3:
                continue
            sep = abs(b["offset"] - a["offset"])
            if not (BAND_SEARCH_MM[0] <= sep <= BAND_SEARCH_MM[1]):
                continue
            t0, t1 = max(a["t0"], b["t0"]), min(a["t1"], b["t1"])
            if t1 - t0 <= AP.EPS:
                continue
            ka, kb = set(a["keys"]), set(b["keys"])
            if ka & bound_keys or kb & bound_keys:
                continue
            lo, hi = sorted((a["offset"], b["offset"]))
            if any(abs(c["angle"] - a["angle"]) <= 1e-3 and lo + AP.EPS < c["offset"] < hi - AP.EPS
                   and min(c["t1"], t1) - max(c["t0"], t0) > AP.EPS for c in near):
                continue
            u, n = a["u"], a["n"]
            P = lambda t, o: (u[0] * t + n[0] * o, u[1] * t + n[1] * o)
            poly = [P(t0, lo), P(t1, lo), P(t1, hi), P(t0, hi)]
            if SV.convex_overlap(rect_poly, poly, AP.EPS):
                out.append({"id": "UNBOUND:" + "+".join(sorted(ka)[:1] + sorted(kb)[:1]), "polygon": poly, "bound": False,
                            "drawn_breadth_mm": round(sep, 1)})
    return out


def _line_near_poly(l, poly, d):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    u = l["u"]
    n = l["n"]
    p0 = (u[0] * l["t0"] + n[0] * l["offset"], u[1] * l["t0"] + n[1] * l["offset"])
    p1 = (u[0] * l["t1"] + n[0] * l["offset"], u[1] * l["t1"] + n[1] * l["offset"])
    return LineString([p0, p1]).distance(Polygon(poly)) <= d


def _columns(ctx, S, out, libs) -> dict:
    lib = A3.column_library(ctx["schedules"]["COLUMNS"])
    tags = _bind_column_tags(ctx, S, lib)
    iv = {i["from"]: i for i in out["intervals"]}
    rows = []
    for fl in FLOORS:
        sheet = out["sheets"][fl]
        (dx, dy), same = _frame_offset(ctx, "COLUMN_AXIS", ROOF_SHEET[fl])
        band = STOREY_BAND[fl]
        t_cm = (sheet["slab"]["sheet_thickness_tags_cm"] or [None])[0] if len(sheet["slab"]["sheet_thickness_tags_cm"]) == 1 else None
        bound_keys = set()
        members = []
        for o in sheet["occurrences"]:
            for ks in o["band_record"]["edge_keys"]:
                bound_keys |= set(ks)
            conflict = o["state"] == "BAND_TYPE_CONFLICT"
            members.append({"id": o["type"] + ":" + o["tags"][0], "polygon": [tuple(p) for p in o["band_polygon"]],
                            "bound": not conflict, "type": o["type"], "D_cm": o["D_cm"], "drawn_breadth_mm": o["drawn_breadth_mm"],
                            "candidate_types": ([o["type"]] + o.get("conflict_with", [])) if conflict else None})
        for tg in tags:
            sec = lib[tg["type"]].get(band) or {}
            rec = {"floor": fl, "storey_band": band, "type": tg["type"], "tag_key": tg["tag_key"], "tag_binding": tg["state"],
                   "B_cm": sec.get("B_cm"), "D_cm": sec.get("D_cm"), "frame_offset_same_size": same}
            if tg["state"] != "BOUND":
                rows.append(dict(rec, state="BLOCKED_TAG_NOT_BOUND", height_m=None, volume_m3=None))
                continue
            proj = [(x + dx, y + dy) for x, y in tg["outline"]]
            hits = [c for c in sheet["columns"] if SV.convex_overlap(proj, c["polygon"], AP.EPS)]
            if len(hits) == 0:
                rows.append(dict(rec, state="NOT_DRAWN_ON_STOREY_SHEET" if sec.get("B_cm") else "NOT_IN_STOREY",
                                 height_m=None, volume_m3=None))
                continue
            if len(hits) > 1:
                rows.append(dict(rec, state="BLOCKED_SEVERAL_OUTLINES_ON_STOREY_SHEET", height_m=None, volume_m3=None))
                continue
            c = hits[0]
            rec["storey_outline_mm"] = [c["w_mm"], c["h_mm"]]
            rec["storey_outline_centre"] = c["centre"]
            if sec.get("B_cm") is None:
                rows.append(dict(rec, state="BLOCKED_SECTION_NOT_SCHEDULED_FOR_STOREY", height_m=None, volume_m3=None))
                continue
            rec["drawn_vs_schedule"] = ("AGREES" if tuple(sorted((c["w_mm"], c["h_mm"]))) == tuple(sorted((sec["B_cm"] * 10, sec["D_cm"] * 10)))
                                        else "DIFFERS (schedule is the section authority)")
            fr = SV.framing_members(c["polygon"], members, eps=AP.EPS) + _unbound_bands(sheet, c["polygon"], bound_keys)
            ctrl = SV.controlling_member(fr, libs, tol_mm=TOL_MM, slab_thickness_cm=t_cm)
            ci = SV.column_interval(B_cm=sec["B_cm"], D_cm_col=sec["D_cm"], interval=iv.get(fl), control=ctrl,
                                    slab_thickness_cm=t_cm)
            rows.append(dict(rec, upper=ctrl, **ci))
    by = defaultdict(lambda: {"computed": 0, "blocked": 0, "volume_m3": 0.0, "joint_m3": 0.0})
    for r in rows:
        if r.get("volume_m3") is not None:
            by[r["floor"]]["computed"] += 1
            by[r["floor"]]["volume_m3"] = round(by[r["floor"]]["volume_m3"] + r["volume_m3"], 6)
            by[r["floor"]]["joint_m3"] = round(by[r["floor"]]["joint_m3"] + (r.get("joint_m3") or 0.0), 6)
        elif r["state"] not in ("NOT_IN_STOREY", "NOT_DRAWN_ON_STOREY_SHEET"):
            by[r["floor"]]["blocked"] += 1
    return {"tag_binding": tags, "tag_binding_states": dict(Counter(t["state"] for t in tags)), "rows": rows,
            "states": {f"{k[0]}|{k[1]}": v for k, v in sorted(Counter((r["floor"], r["state"]) for r in rows).items())},
            "by_storey": {k: dict(v) for k, v in sorted(by.items())},
            "neck": SV.neck(footing_top_m=None, upper_start_m=None),
            "neck_why": "no footing-top / founding level and no ground-beam or ground-slab level is printed in the "
                        "structural source (typical footing detail p.13 dimensions none); +1.00 FFL is corroboration only",
            "rule": "tag -> column-plan outline by printed size + adjacency + margin; storey outline by frame offset + "
                    "overlap; section from the schedule band; height from the member framing into THIS outline"}


# ------------------------------------------------------------------ concrete
def _beam_volume(o, t_cm):
    L = (o.get("lengths") or {}).get("CLEAR_FACE_TO_FACE_LENGTH")
    if o["state"] != "MEASURED" or L is None or t_cm is None:
        return None, o["state"] if o["state"] != "MEASURED" else ("SLAB_THICKNESS_UNKNOWN" if t_cm is None else "NO_CLEAR_LENGTH")
    return L, None


def _concrete(ctx, out) -> dict:
    res = {}
    for fl in FLOORS:
        sh = out["sheets"][fl]
        s = sh["slab"]
        t = s["sheet_thickness_tags_cm"][0] if len(s["sheet_thickness_tags_cm"]) == 1 else None
        slab = ({"net_area_m2": s["net_plate_area_m2"], "t_cm": t} if s["volume_state"] == "COMPUTED"
                else {"blocked": s["closure"] if s["closure"] != "CLOSED" else "SLAB_THICKNESS_NOT_PRINTED", "t_cm": t})
        beams = []
        for o in sh["occurrences"]:
            L, why = _beam_volume(o, t)
            beams.append({"id": f"{o['type']}:{o['tags'][0]}", "type": o["type"], "length_m": L, "B_cm": o["B_cm"], "D_cm": o["D_cm"],
                          "blocked": why})
        unbound_tags = [r for r in sh["binding"] if r["state"] not in BB.BOUND_STATES]
        for r in unbound_tags:
            beams.append({"id": f"{r['type']}:{r['mark_key']}", "type": r["type"], "length_m": None, "B_cm": r.get("B_cm"),
                          "D_cm": r.get("D_cm"), "blocked": "TAG_NOT_BOUND: " + r["state"]})
        cols = [r for r in out["columns"]["rows"] if r["floor"] == fl and r["state"] not in ("NOT_IN_STOREY", "NOT_DRAWN_ON_STOREY_SHEET")]
        joints = [{"id": r["tag_key"], "volume_m3": r.get("joint_m3"),
                   "blocked": None if r.get("joint_m3") is not None else r["state"]} for r in cols]
        columns = [{"id": r["tag_key"], "volume_m3": r.get("volume_m3"), "blocked": None if r.get("volume_m3") is not None else r["state"]}
                   for r in cols]
        model = CM.physical_model(slab=slab, beams=beams, joints=joints, columns=columns)
        gross = CM.gross_beam_view([b for b in beams if not b["blocked"]])
        res[fl] = {"sheet": ROOF_SHEET[fl], "slab_thickness_cm": t, "model": model, "gross_beam_view": gross,
                   "gross_beam_view_m3": round(sum(g["volume_m3"] for g in gross), 6),
                   "downstand_m3": model["by_component_m3"].get("DOWNSTAND_BEAM", 0.0),
                   "beam_rows": beams}
    return res


def _items(ctx, out) -> list:
    a3 = ctx["a3"]
    con = a3["concrete"]
    fts = [r for r in a3["footings"]["rows"] if r["status"] == A3.SQ.COMPLETE]
    blind = 0.0
    for r in fts:
        sr = r["schedule_row"]
        blind += (sr["L_cm"] / 100.0 + 0.20) * (sr["W_cm"] / 100.0 + 0.20) * 0.10
    rows = [
        {"item": "FOOTINGS", "state": "COMPUTED_PARTIAL", "volume_m3": con["footings_m3"],
         "computed": con["footings_computed"], "of": con["footings_total"], "blocked": con["blocked"]["footings"],
         "basis": "A3 schedule-driven occurrences (unchanged); F / F10 stays SOURCE_CONFLICT"},
        {"item": "STRAPS", "state": "COMPUTED", "volume_m3": con["straps_m3"], "computed": con["straps_measured"],
         "of": con["straps_total"], "basis": "A3 strap bands (unchanged)"},
        {"item": "BLINDING (under computed footings)", "state": "COMPUTED_FROM_TYPICAL_DETAIL",
         "volume_m3": round(blind, 6), "computed": len(fts),
         "basis": "ST7757.pdf p.13 TYP. DETAIL OF ISOLATED FOOTING: 10 cm plain concrete, 10 cm beyond L x W each side",
         "not_included": "blocked footings; straps / ground beams (their blinding is not dimensioned for straps)"},
        {"item": "COLUMN NECKS", "state": "BLOCKED_HEIGHT", "volume_m3": None, "why": out["columns"]["neck_why"]},
        {"item": "GROUND BEAMS", "state": "BLOCKED_WITH_REASON", "volume_m3": None,
         "why": "the GROUND BEAMS plan carries no beam tags; p.13 gives typical sections by length (30x60 > 5 m, 30x40 "
                "< 5 m, 30x30, exterior 30 x 'FOLLOW ARCH.') whose exterior depth needs the outer ground level to the "
                "ground-slab level - not proved"},
        {"item": "GROUND SLAB", "state": "BLOCKED_WITH_REASON", "volume_m3": None,
         "why": "no ground-slab thickness / outline is printed (the details show 'Ground Floor slab level' only)"},
    ]
    for fl in FLOORS:
        c = out["concrete"][fl]
        col = out["columns"]["by_storey"].get(fl, {})
        rows.append({"item": f"COLUMNS {fl}", "state": "COMPUTED_PARTIAL" if col.get("blocked") else "COMPUTED",
                     "volume_m3": col.get("volume_m3"), "joint_m3": col.get("joint_m3"), "computed": col.get("computed"),
                     "blocked": col.get("blocked")})
        rows.append({"item": f"BEAMS {fl} (downstand)", "state": "COMPUTED_PARTIAL", "volume_m3": c["downstand_m3"],
                     "computed": sum(1 for b in c["beam_rows"] if not b["blocked"]),
                     "blocked": sum(1 for b in c["beam_rows"] if b["blocked"])})
        s = out["sheets"][fl]["slab"]
        rows.append({"item": f"SLAB {fl} ROOF", "state": s["volume_state"], "volume_m3": s["volume_m3"],
                     "net_area_m2": s["net_plate_area_m2"], "why": None if s["volume_state"] == "COMPUTED" else s["closure"]})
    rows += [
        {"item": "STAIRS", "state": "BLOCKED_INPUT_MISSING", "volume_m3": None, "why": "waist thickness and riser height not printed"},
        {"item": "STRUCTURAL WALLS", "state": "BLOCKED_WITH_REASON", "volume_m3": None,
         "why": "no structural (shear / retaining) wall is tagged on any plan; the 'B.W' schedule row (20 x 60) is bound "
                "to no plan occurrence"},
        {"item": "POOL", "state": "BLOCKED_WITH_REASON", "volume_m3": None,
         "why": "DETAIL OF SWIMMING POOL is a section detail (N.T.S.) with no plan extent bound to it"},
    ]
    return rows


def _stairs(ctx) -> dict:
    s = CM.stair(flights=[{"risers": None, "riser_m": None, "going_m": 0.30, "width_m": None, "waist_m": None}])
    return {"evidence": {"tread_going_cm": 30, "source": "ST7757.pdf p.16 TYPICAL STEEL LAYOUT-STAIR SECTION (N.T.S.); "
                         "architectural tread runs (A3 STAIR_REGISTER: going 300 mm, flight widths 1150 / 2800 mm)",
                         "waist": "NOT_PRINTED ('THICK' without value)", "riser": "NOT_PRINTED",
                         "landing_thickness": "NOT_PRINTED", "stair_beam": "G.B 30 wide on 10 cm blinding 50 wide (typical)",
                         "riser_count": "not proved (tread lines are not risers; a count from the storey height would be "
                                        "an assumption)"},
            "result": s, "never": "steps x 0.30 x 0.15"}


# ------------------------------------------------------------------ architecture
def _site_polygon(arr, cyc, step=math.radians(5.0)):
    pts = []
    for k, fw in cyc:
        e = arr.edges[k]
        if e["kind"] == "S":
            pts.append(arr.nodes[e["n0"] if fw else e["n1"]])
        else:
            pr = e["prim"]
            n = max(int((e["t1"] - e["t0"]) / step), 2)
            ts = [e["t0"] + (e["t1"] - e["t0"]) * i / n for i in range(n)]
            if not fw:
                ts = [e["t1"] - (e["t1"] - e["t0"]) * i / n for i in range(n)]
            pts += [pr.point(t) for t in ts]
    return pts


def _window_box(w):
    (a0, a1), (b0, b1) = w["jambs"]
    ux, uy = w["axis"]
    nx, ny = -uy, ux
    corners = [(a * ux + b * nx, a * uy + b * ny) for a in (a0, a1) for b in (b0, b1)]
    xs = [p[0] for p in corners]
    ys = [p[1] for p in corners]
    bm = (b0 + b1) / 2.0
    j = [(a0 * ux + bm * nx, a0 * uy + bm * ny), (a1 * ux + bm * nx, a1 * uy + bm * ny)]
    return (min(xs), min(ys), max(xs), max(ys)), j, (nx, ny)


def _architecture(ctx, A, out) -> dict:
    res = {}
    res["openings"] = _openings(ctx, A)
    res["salon"] = _salon(ctx, out, res["openings"])
    res["curved"] = _curved(ctx)
    res["mbr"] = _mbr(ctx, A)
    res["gf_open_site"] = _open_site(ctx)
    res["reception"] = _reception(ctx, A, out)
    res["wall_heights"] = _wall_heights(ctx, out, res)
    res["waterproofing"] = _waterproofing(ctx, out, res)
    return res


def _openings(ctx, A) -> dict:
    rows = []
    for fl in FLOORS:
        raw = ctx["a2_raw"][fl]
        res = raw["res"]
        arr, sites = res.get("_arr"), res.get("sites") or []
        by = {s["site_id"]: s for s in sites}
        closures = [c for c in res.get("closures") or [] if str(getattr(c, "source_id", "")).startswith("CLOSURE|")
                    and str(c.source_id).split("|")[1] != "GLAZED"]           # door occurrences only, never glazing
        fb = ctx["sheets_by_floor"][fl]["bounds"]
        arcs = [p for p in A["parts"] if p.kind == "ARC" and CI.effective_layer(p)[0] == DOOR_LAYER
                and AP.in_box(p.geometry[0], p.geometry[1], fb)]
        a3w = {w["window"]: w for w in ctx["a2"]["floors"][fl]["windows"]}
        for i, w in enumerate(raw["eri"]["glazing"]["windows"]):
            wid = f"{fl}-W{i + 1:02d}"
            box, jambs, nrm = _window_box(w)
            pad = w["thickness_mm"] / 2.0 + AP.EPS
            door = []
            for c in closures:
                x1, y1, x2, y2 = c.geometry
                if all(box[0] - pad <= x <= box[2] + pad and box[1] - pad <= y <= box[3] + pad for x, y in ((x1, y1), (x2, y2))) \
                        and abs(math.hypot(x2 - x1, y2 - y1) - w["width_mm"]) <= w["thickness_mm"]:
                    door.append(f"closed door {c.source_id.split('|')[1]} closes this gap (closure {c.source_id})")
            for p in arcs:
                cx, cy, r, a0, a1 = p.geometry[:5]
                if OA.swing_closes_on_opening({"cx": cx, "cy": cy, "r": r, "a0": a0, "a1": a1}, jambs[0], jambs[1],
                                              end_tol=w["thickness_mm"]):
                    door.append(f"door-layer swing {p.identity.key} hinged at a jamb closes on the opening")
            door = sorted(set(door))
            mid = ((jambs[0][0] + jambs[1][0]) / 2.0, (jambs[0][1] + jambs[1][1]) / 2.0)
            d = w["thickness_mm"] / 2.0 + SIDE_PROBE_MM
            sides = []
            for sg in (1, -1):
                pt = (mid[0] + sg * nrm[0] * d, mid[1] + sg * nrm[1] * d)
                sid = T.locate(arr, sites, pt, 1.0)[0] if arr is not None else None
                s = by.get(sid)
                lab = sorted({" / ".join(A2._label_values(s)[0])}) if s and s["kind"] == "LABELLED_SITE" else []
                interior = bool(s) and (s["kind"] == "LABELLED_SITE" or s.get("status") == "CERTIFIED")
                sides.append({"site": sid, "labels": lab, "interior": interior})
            amb = ["the opening joins two interior spaces (both sides inside room sites) and has no door geometry"] \
                if all(x["interior"] for x in sides) and not door else []
            c = OA.classify({"id": wid, "existence": "GLAZING_IN_WALL_GAP (entity_role_inference)", "width_mm": w["width_mm"],
                             "glazing": True, "door_evidence": door, "ambiguity": amb, "previous_function": "WINDOW"})
            c.update({"floor": fl, "wall_thickness_mm": w["thickness_mm"], "sides": sides,
                      "box_native": [round(v, 3) for v in box], "jambs_native": [[round(v, 3) for v in j] for j in jambs],
                      "a3_record": {"window": wid, "width_mm": a3w.get(wid, {}).get("width_mm")},
                      "height": "BLOCKED_HEIGHT" if c["function"] != OA.WINDOW else "BLOCKED_HEIGHT (no source / section / "
                      "owner value; no versioned fallback adopted this round)"})
            rows.append(c)
    return {"rows": rows, "functions": {f"{k[0]}|{k[1]}": v for k, v in sorted(Counter((r["floor"], r["function"]) for r in rows).items())},
            "changes": [{"id": r["id"], "from": "WINDOW", "to": r["function"], "change": r["function_change"],
                         "basis": r["function_basis"]} for r in rows if r["function_change"]]}


def _salon(ctx, out, openings) -> dict:
    reg = out["registration"]["GF"]
    ws = ctx["a2_raw"]["GF"]["eri"]["glazing"]["windows"]
    w9 = [(i, w) for i, w in enumerate(ws) if abs(w["width_mm"] - 6330.0) <= A3.SALON_WIDTH_TOL_MM]
    rec = {"owner_facts": ["OF-B2A-D", "OF-B2A-E", "OF-B2A-F"], "registration": reg["state"]}
    if len(w9) != 1 or reg["state"] != "REGISTERED":
        return dict(rec, state="BLOCKED", why="opening or registration not unique")
    i, w = w9[0]
    box, _, _ = _window_box(w)
    dx, dy = reg["translation"]
    poly = [(box[0] + dx, box[1] + dy), (box[2] + dx, box[1] + dy), (box[2] + dx, box[3] + dy), (box[0] + dx, box[3] + dy)]
    over = [o for o in out["sheets"]["GF"]["occurrences"]
            if SV.convex_overlap(poly, [tuple(p) for p in o["band_polygon"]], AP.EPS)
            and Polygon([tuple(p) for p in o["band_polygon"]]).intersection(Polygon(poly)).area >= 0.9 * Polygon(poly).area]
    iv = next(x for x in out["intervals"] if x["from"] == "GF")
    if len(over) != 1:
        return dict(rec, opening=f"GF-W{i + 1:02d}", state="BLOCKED_BEAM_ABOVE_NOT_UNIQUE", beams=[o["type"] for o in over])
    o = over[0]
    soffit_above_ffl_max = round(iv["interval_m"] - o["D_cm"] / 100.0, 6)
    h = OWNER_FACTS_B2A[5]["fact"]["height_m"]
    return dict(rec, opening=f"GF-W{i + 1:02d}", width_m=6.33, width_authority="SOURCE (printed 633 + CAD gap)",
                beam_above={"type": o["type"], "namespace": o["namespace"], "B_cm": o["B_cm"], "D_cm": o["D_cm"],
                            "drawn_breadth_mm": o["drawn_breadth_mm"], "tags": o["tags"], "occurrence_state": o["state"],
                            "covers_opening": "the opening footprint lies inside the band footprint (>= 90 %)"},
                interval_m=iv["interval_m"], interval_authority=iv["authority"],
                structural_soffit_above_gf_ffl_m=f"{soffit_above_ffl_max} - (1F floor build-up)",
                structural_soffit_upper_bound_m=soffit_above_ffl_max,
                finished_ceiling="NOT_IN_SOURCE", aluminium_head="NOT_IN_SOURCE",
                height_m=h, height_authority="OWNER_DERIVED_PROJECT_DIMENSION (OF-B2A-F, provisional)",
                source_consistency="CONSISTENT (3.65 <= structural soffit bound)" if h <= soffit_above_ffl_max else "INCONSISTENT",
                state="OWNER_DERIVED_REVIEW_REQUIRED", area_m2=round(6.33 * h, 6),
                rule="the beam soffit is an upper bound for the aluminium head; the head itself is not printed")


def _curved(ctx) -> dict:
    rows = []
    for g in ctx["a3"]["architecture"]["curved_glazing"]["items"]:
        arcs = [{"cx": g["centre"][0], "cy": g["centre"][1], "r": r, "sweep_rad": s} for r, s in zip(g["radii_mm"], g["sweep_rad"])]
        b = CO.bases(arcs)
        c = CO.commercial(b)
        rows.append({"id": g["id"], "floor": g["floor"], "host_labels": g["host_labels"],
                     "bases_m": {k: round(b[k] / 1000.0, 6) for k in CO.BASES} if b["state"] == "COMPUTED" else None,
                     "commercial_m": round(c["length_mm"] / 1000.0, 6) if c["state"] == "COMPUTED" else None,
                     "commercial_basis": c.get("basis"), "authority": c.get("authority"),
                     "a3_developed_length_m": round(g["developed_length_mm"] / 1000.0, 6),
                     "height": g["height"], "area_m2": None})
    return {"rows": rows, "method": CO.METHOD_ID, "override": None}


def _mbr(ctx, A) -> dict:
    res = ctx["a2_raw"]["GF"]["res"]
    sites = res.get("sites") or []
    tgt = [s for s in sites if s["kind"] == "LABELLED_SITE" and "MASTER BED ROOM" in " ".join(A2._label_values(s)[0])]
    if len(tgt) != 1:
        return {"state": "BLOCKED", "why": "master-bedroom site not unique"}
    s = tgt[0]
    unknown = sorted(s.get("blocked_by") or [])
    parts = {p.identity.key: p for p in A["parts"] if p.identity.key in set(unknown)}
    box = OWNER_FACTS_B2A[2]["fact"]["box_mm"]
    poly = _site_polygon(res["_arr"], s["cycle"])
    room = Polygon(poly)
    released, residual = [], []
    segs = {k: p.geometry for k, p in parts.items() if p.kind == "SEGMENT"}
    # wardrobe: a straight line of the box length parallel to a room face at the box depth, plus its diagonal
    for k, g in sorted(segs.items()):
        L = math.hypot(g[2] - g[0], g[3] - g[1])
        face_d = _parallel_face_depth(poly, g)
        if abs(L - box[1]) <= 10.0 and abs(face_d - box[0]) <= 10.0:
            released.append({"part": k, "role": "WARDROBE_FRONT", "fact": "OF-B2A-C", "length_mm": round(L, 1),
                             "depth_from_room_face_mm": round(face_d, 1)})
    fronts = [r["part"] for r in released]
    for k, g in sorted(segs.items()):
        if k in fronts:
            continue
        L = math.hypot(g[2] - g[0], g[3] - g[1])
        if abs(L - math.hypot(*box)) <= 15.0 and fronts:
            fg = segs[fronts[0]]
            if any(math.hypot(g[i] - fg[j], g[i + 1] - fg[j + 1]) <= AP.EPS for i in (0, 2) for j in (0, 2)):
                released.append({"part": k, "role": "WARDROBE_DIAGONAL (symbol)", "fact": "OF-B2A-C", "length_mm": round(L, 1)})
                continue
        residual.append(k)
    # door-frame ticks: door layer, length <= wall thickness, on a closed door's closure line at its jamb ends
    closures = [c for c in res.get("closures") or [] if str(getattr(c, "source_id", "")).startswith("CLOSURE|")
                and str(c.source_id).split("|")[1] != "GLAZED"]
    still = []
    for k in residual:
        p = parts[k]
        g = p.geometry
        L = math.hypot(g[2] - g[0], g[3] - g[1])
        hit = None
        if CI.effective_layer(p)[0] == DOOR_LAYER and L <= 200.0:
            for c in closures:
                x1, y1, x2, y2 = c.geometry
                cl = LineString([(x1, y1), (x2, y2)])
                if cl.distance(LineString([(g[0], g[1]), (g[2], g[3])])) <= AP.EPS and \
                        min(math.hypot(g[i] - e[0], g[i + 1] - e[1]) for i in (0, 2) for e in ((x1, y1), (x2, y2))) <= AP.EPS:
                    hit = c.source_id
                    break
        if hit:
            released.append({"part": k, "role": "DOOR_FRAME_TICK", "rule": "door layer, <= 200 mm, at a jamb end of a closed "
                             "door's closure line", "closure": hit, "length_mm": round(L, 1)})
        else:
            still.append(k)
    cert = not still and s["holes"] == 0
    return {"site": s["site_id"], "a3_status": s["status"], "a3_issues": s["issues"], "unknown_parts": unknown,
            "released": released, "residual_unknown": still,
            "state": "CERTIFIED_WITH_OWNER_FACT" if cert else "BLOCKED", "floor_area_m2": round(s["area_m2"], 6) if cert else None,
            "candidate_area_m2": round(s["area_m2"], 6), "perimeter_m": round(s["perimeter"] / 1000.0, 6),
            "wardrobe_treatment": "FIXED_JOINERY: floor finish continues under it (URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1); "
                                  "no wall face, no partition, no area deduction; wall finish behind it not deducted (no rule)",
            "_polygon": poly}


def _parallel_face_depth(poly, g):
    """Perpendicular distance from the mid point of segment g to the nearest room face parallel to it."""
    ux, uy = g[2] - g[0], g[3] - g[1]
    L = math.hypot(ux, uy)
    mx, my = (g[0] + g[2]) / 2.0, (g[1] + g[3]) / 2.0
    best = math.inf
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        vx, vy = x2 - x1, y2 - y1
        M = math.hypot(vx, vy)
        if M <= AP.EPS or abs(ux * vy - uy * vx) / (L * M) > 1e-3:
            continue
        d = abs((mx - x1) * vy - (my - y1) * vx) / M
        if d > AP.EPS:
            best = min(best, d)
    return best


def _open_site(ctx) -> dict:
    res = ctx["a2_raw"]["GF"]["res"]
    sites = res.get("sites") or []
    want = ("SALOON", "RECEPTION", "DINING")
    hits = []
    for s in sites:
        labs = " / ".join(A2._label_values(s)[0]).upper()
        found = [w for w in want if w in labs]
        if found:
            hits.append({"site": s["site_id"], "labels": found, "status": s["status"], "kind": s["kind"],
                         "area_m2": round(s["area_m2"], 6)})
    state = ("ONE_PHYSICAL_SITE" if len(hits) == 1 and hits[0]["status"] == "CERTIFIED" else
             "NOT_CLOSED (no certified site holds the zone labels)")
    return {"owner_fact": "OF-B2A-A", "zone_labels": list(want), "sites_holding_labels": hits, "state": state,
            "rule": "no wall is invented between the zones and no exterior door is invented at the entry (OF-B2A-A, section 16); "
                    "the open zone closes only from source boundaries",
            "exterior_entry": "UNRESOLVED (no door / screen in the source at the entry; none invented)"}


def _reception(ctx, A, out) -> dict:
    reg = out["registration"]["GF"]
    gb = ctx["sheets_by_floor"]["GF"]["bounds"]
    rec = [t for t in A["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, gb) and t.value.strip().upper() == "RECEPTION"]
    sh = out["sheets"]["GF"]
    res = {"owner_fact": "OF-B2A-B", "registration": reg["state"], "labels": len(rec)}
    if len(rec) != 1 or reg["state"] != "REGISTERED":
        return dict(res, state="BLOCKED", region=FH.double_height_region(span_evidence=None))
    x, y = _to_sheet(out["registration"], "GF", rec[0].x, rec[0].y)
    # opening faces of the GF roof slab: recompute their polygons from the stored plate (gross - plate)
    gross, plate = sh["_gross"], sh["_plate"]
    holes = gross.difference(plate) if gross is not None and plate is not None else None
    parts = list(getattr(holes, "geoms", [holes])) if holes is not None and not holes.is_empty else []
    inside = [p for p in parts if p.buffer(AP.EPS).contains(Point(x, y))]
    if len(inside) != 1:
        return dict(res, state="BLOCKED_NO_SLAB_OPENING_OVER_THE_LABEL", label_on_slab_sheet=[round(x, 3), round(y, 3)],
                    region=FH.double_height_region(span_evidence=None))
    p = inside[0]
    area = round(p.area / 1e6, 6)
    return dict(res, state="REGION_FROM_SLAB_OPENING", label_on_slab_sheet=[round(x, 3), round(y, 3)], area_m2=area,
                perimeter_m=round(p.length / 1000.0, 6),
                region=FH.double_height_region(span_evidence="GF ROOF SLAB opening (VOID) holding the projected RECEPTION "
                                                             "label", area_m2=area),
                note="the opening includes whatever the slab void spans (stair / gallery edge); the zone's own floor area "
                     "inside the open site is not split from it without a source boundary")


def _wall_heights(ctx, out, arch) -> dict:
    """Per certified GF/1F/2F room: each boundary edge -> termination on the roof sheet above; heights per quantity."""
    rows = []
    for fl in FLOORS:
        reg = out["registration"][fl]
        if reg["state"] != "REGISTERED":
            continue
        sh = out["sheets"][fl]
        plate = sh["_plate"]
        t_cm = sh["slab"]["sheet_thickness_tags_cm"][0] if len(sh["slab"]["sheet_thickness_tags_cm"]) == 1 else None
        iv = next((x for x in out["intervals"] if x["from"] == fl), None)
        bands = [(o, Polygon([tuple(p) for p in o["band_polygon"]])) for o in sh["occurrences"]]
        res = ctx["a2_raw"][fl]["res"]
        sites = [s for s in res.get("sites") or [] if s["kind"] == "LABELLED_SITE" and s["status"] == "CERTIFIED"]
        extra = []
        if fl == "GF" and arch["mbr"].get("state") == "CERTIFIED_WITH_OWNER_FACT":
            extra = [s for s in res.get("sites") or [] if s["site_id"] == arch["mbr"]["site"]]
        for s in sorted(sites + extra, key=lambda z: z["site_id"]):
            labs = " / ".join(A2._label_values(s)[0])
            wet = any(w in labs.upper() for w in A2.WET_WORDS)
            poly = arch["mbr"]["_polygon"] if s in extra else _site_polygon(res["_arr"], s["cycle"])
            dx, dy = reg["translation"]
            P = [(x + dx, y + dy) for x, y in poly]
            room = Polygon(P)
            over = [o for o, bp in bands if bp.intersects(room.buffer(-AP.EPS)) or bp.buffer(AP.EPS).intersects(room.exterior)]
            ctrl = max((o["D_cm"] for o in over if o["state"] != "BAND_TYPE_CONFLICT"), default=None)
            any_conflict = any(o["state"] == "BAND_TYPE_CONFLICT" for o in over)
            room_ctrl = None if any_conflict else (ctrl if ctrl is not None else t_cm)
            faces = []
            for i in range(len(P)):
                a, b = P[i], P[(i + 1) % len(P)]
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                if L < 50.0:
                    continue
                edge = LineString([a, b])
                cov = []
                for o, bp in bands:
                    inter = bp.buffer(AP.EPS * 2).intersection(edge).length
                    if inter > AP.EPS:
                        cov.append({"type": o["type"], "D_cm": o["D_cm"], "bound": o["state"] != "BAND_TYPE_CONFLICT",
                                    "coverage": min(inter / L, 1.0)})
                inside = plate is not None and plate.buffer(AP.EPS).contains(edge)
                term = FH.termination(covering_bands=cov, inside_plate=inside, plate_t_cm=t_cm)
                hts = FH.wall_heights(interval=iv, term=term, room_ctrl_D_cm=room_ctrl, wet=wet, buildup_above_m=None)
                faces.append({"edge": i, "length_m": round(L / 1000.0, 6), "termination": term, "heights": hts,
                              "plaster_gross_m2": round(L / 1000.0 * hts["PLASTER"]["height_m"], 6)
                              if hts["PLASTER"]["height_m"] is not None else None})
            rows.append({"floor": fl, "site": s["site_id"], "room": labs, "wet": wet, "room_controlling_soffit_cm": room_ctrl,
                         "faces": faces, "faces_terminated": sum(1 for f in faces if f["termination"]["type"] != FH.UNKNOWN),
                         "faces_total": len(faces),
                         "plaster_gross_computed_faces_m2": round(sum(f["plaster_gross_m2"] or 0 for f in faces), 6),
                         "faces_blocked": [f["edge"] for f in faces if f["plaster_gross_m2"] is None],
                         "room_plaster_state": "COMPUTED" if all(f["plaster_gross_m2"] is not None for f in faces)
                         else "PARTIAL (blocked faces listed; never totalled as the room)",
                         "paint": "BLOCKED_FLOOR_BUILDUP", "wall_tile": "BLOCKED_FLOOR_BUILDUP" if wet else "NOT_APPLICABLE"})
    return {"rows": rows, "paint_blocker": "floor build-up above each storey is not in the source (owner action)",
            "net_of_openings": "BLOCKED (opening heights are blocked; gross face areas published)"}


def _waterproofing(ctx, out, arch) -> dict:
    from shapely.affinity import translate
    roofs = []
    plates = {fl: out["sheets"][fl]["_gross"] for fl in FLOORS}
    def onto(lo, hi):
        """The plate of the sheet above, carried onto the sheet below by the frame offset - accepted only when the
        column outlines of the sheet above land on column outlines of the sheet below (>= 80 %)."""
        (dx, dy), same = _frame_offset(ctx, ROOF_SHEET[hi], ROOF_SHEET[lo])
        cols_hi = [[(x + dx, y + dy) for x, y in c["polygon"]] for c in out["sheets"][hi]["columns"]]
        hit = sum(1 for c in cols_hi if any(SV.convex_overlap(c, d["polygon"], AP.EPS) for d in out["sheets"][lo]["columns"]))
        ok = same and cols_hi and hit / len(cols_hi) >= 0.8
        return (translate(plates[hi], xoff=dx, yoff=dy) if ok and plates[hi] is not None else None), \
            {"frame_same_size": same, "columns_above_on_columns_below": f"{hit}/{len(cols_hi)}", "aligned": bool(ok)}
    top_ok = out["sheets"]["2F"]["slab"]["closure"] == "CLOSED" and plates["2F"] is not None
    roofs.append(WP.roof(area_m2=plates["2F"].area / 1e6 if top_ok else None,
                         perimeter_m=plates["2F"].length / 1000.0 if top_ok else None, region="2F ROOF (top)"))
    for lo, hi in (("1F", "2F"), ("GF", "1F")):
        up, align = onto(lo, hi)
        if plates[lo] is None or up is None or out["sheets"][hi]["slab"]["closure"] != "CLOSED" \
                or out["sheets"][lo]["slab"]["closure"] != "CLOSED":
            roofs.append(dict(WP.roof(area_m2=None, perimeter_m=None, region=f"{lo} ROOF exposed (not under {hi})"),
                              alignment=align, why=f"{hi} or {lo} plate not closed / sheets not aligned"))
            continue
        ex = plates[lo].difference(up).buffer(-1.0).buffer(1.0)
        roofs.append(dict(WP.roof(area_m2=ex.area / 1e6, perimeter_m=ex.length / 1000.0,
                                  region=f"{lo} ROOF exposed (not under {hi})"), alignment=align,
                          note="candidate: plate minus the plate above; covered terraces under an overhang are not "
                               "separated (UNRESOLVED)"))
    wet = []
    for r in arch["wall_heights"]["rows"]:
        if r["wet"]:
            res = ctx["a2_raw"][r["floor"]]["res"]
            s = next(x for x in res["sites"] if x["site_id"] == r["site"])
            wet.append(WP.wet(floor_m2=s["area_m2"], perimeter_m=s["perimeter"] / 1000.0, room=f"{r['floor']} {r['room']}"))
    return {"roof": roofs, "wet": wet, "method": "URBAN-ROOF-WATERPROOF-UPTURN-200@v1",
            "laps": WP.procurement(0.0)["why"]}


REVIEW_OPENINGS = ("GF-W03", "GF-W04", "GF-W11", "GF-W13", "GF-W14")


def review_image(ctx, out_png) -> dict:
    """Annotated source crops of the GF 1.00 m openings: opening, glazing parts, door-layer swings, walls, room labels and
    the B2A verdict with its evidence (section 20). Drawn from the source blob only."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    work = Path(ctx["_work"])
    A = A3._blob(ctx, work, "P7757.dxf")
    rows = {r["id"]: r for r in ctx["b2a"]["architecture"]["openings"]["rows"]}
    ws = ctx["a2_raw"]["GF"]["eri"]["glazing"]["windows"]
    gb = ctx["sheets_by_floor"]["GF"]["bounds"]
    col = {"5": "#777777", "1": "k", DOOR_LAYER: "b", "W": "c", COLUMN_LAYER: "r", "2": "g", "TOI": "#aa7700"}
    parts = sorted([p for p in A["parts"] if AP.in_box(p.geometry[0], p.geometry[1], gb)], key=lambda p: p.identity.key)
    texts = [t for t in A["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, gb)]
    fig, axs = plt.subplots(1, len(REVIEW_OPENINGS), figsize=(6.2 * len(REVIEW_OPENINGS), 7.6))
    for ax, oid in zip(axs, REVIEW_OPENINGS):
        i = int(oid.split("W")[1]) - 1
        w, r = ws[i], rows[oid]
        x0, y0, x1, y1 = r["box_native"]
        pad = 1600.0
        X0, Y0, X1, Y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
        for p in parts:
            g = p.geometry
            c = col.get(CI.effective_layer(p)[0], "#cccccc")
            if p.kind == "SEGMENT":
                if max(g[0], g[2]) < X0 or min(g[0], g[2]) > X1 or max(g[1], g[3]) < Y0 or min(g[1], g[3]) > Y1:
                    continue
                own = p.identity.key in w["parts"]
                ax.plot([g[0], g[2]], [g[1], g[3]], color="orange" if own else c, lw=2.4 if own else 0.8)
            elif p.kind == "ARC":
                cx, cy, rr, a0, a1 = g[:5]
                if not (X0 - rr <= cx <= X1 + rr and Y0 - rr <= cy <= Y1 + rr):
                    continue
                if a1 < a0:
                    a1 += 2 * math.pi
                ts = [a0 + (a1 - a0) * k / 40 for k in range(41)]
                ax.plot([cx + rr * math.cos(t) for t in ts], [cy + rr * math.sin(t) for t in ts], color=c, lw=1.2 if c == "b" else 0.8)
        for t in texts:
            if X0 <= t.x <= X1 and Y0 <= t.y <= Y1 and t.value.strip().isascii():
                ax.text(t.x, t.y, t.value.strip(), fontsize=8, color="darkgreen")
        ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="red", lw=1.6, ls="--"))
        side = "; ".join((s["labels"][0] if s["labels"] and s["labels"][0] else ("room site" if s["interior"] else "no room site"))
                         for s in r["sides"])
        ax.set_title(f"{oid}  {w['width_mm']:.0f} mm  wall {w['thickness_mm']:.0f} mm\nB2A: {r['function']}", fontsize=11)
        ax.text(0.01, 0.01, "evidence: " + r["function_basis"][:95] + ("..." if len(r["function_basis"]) > 95 else "") +
                "\nsides: " + side, transform=ax.transAxes, fontsize=7.5, va="bottom",
                bbox={"facecolor": "white", "alpha": 0.85, "lw": 0})
        ax.set_xlim(X0, X1)
        ax.set_ylim(Y0, Y1)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle("ALSENAN GF 1.00 m openings - source crops (P7757.dxf). Orange: glazing parts bound to the opening; red "
                 "dashed: opening; blue: door layer (swings / frames); black / grey: walls; red: columns; green: labels",
                 fontsize=12)
    fig.savefig(str(out_png), dpi=90, bbox_inches="tight")
    plt.close(fig)
    return {"file": Path(out_png).name, "openings": list(REVIEW_OPENINGS),
            "verdicts": {o: rows[o]["function"] for o in REVIEW_OPENINGS}}


def strip(o):
    """Drop private (underscore) keys recursively for publication."""
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, list):
        return [strip(v) for v in o]
    return o


def main(work, regdir, commit=None):
    import alsenan_b2a_registers as REGS
    return REGS.main(work, regdir, commit)


if __name__ == "__main__":
    main(*sys.argv[1:4])
