"""GENERIC ROUTE (M2) - a structural drawing set -> concrete and reinforcement items, with NO project register
(generic, stdlib + engine.source).

    intake (tools/urban_intake)  ->  drawing_model (sheets, roles, storeys, units)
                                 ->  schedule_reader (attribute rows / text tables; units inferred)
                                 ->  member_detection (footings, columns, beam and ground-beam bands, bindings)
                                 ->  slab_engine (panels, openings, thickness, coverage-risk cells)
                                 ->  items (provisional_estimate)  +  reinforcement models (bar_shapes)
                                 ->  reinforcement completeness register  +  coverage-risk register

Categories: a new project is never VERIFIED. A quantity whose every dimension is printed and drawn is PROVISIONAL with
support SOURCE_COMPLETE_UNREVIEWED; one that uses a convention names it; one without a defensible value is UNRESOLVED
(with an exposure range only when a parameterised expression exists). A fourth register, COVERAGE RISK, lists what
the engine may have missed (unbound marks, unreferenced schedule rows, unknown sheets, weak-evidence cells): an empty
unresolved list never proves completeness.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from engine.source import bar_shapes as BS
from engine.source import drawing_model as DM
from engine.source import ground_beam_network as GN
from engine.source import member_detection as MD
from engine.source import provisional_estimate as PE
from engine.source import schedule_grammar as SG
from engine.source import schedule_reader as SR
from engine.source import cad_heal as CH
from engine.source import detail_evidence as DE
from engine.source import slab_engine as SE

POLICY_ID = "GENERIC_ROUTE_V1"
LINK_ROLES = ("STI", "STR", "LINK", "TIE", "ST")
REBAR_STATES = ("MEASURED", "PROVISIONAL_MODEL", "PARTIAL_MISSING", "MISSING_DATA", "EXPLICIT_NONE", "OUTSIDE_SCOPE")
GB_REQUIRED_ROLES = ("TOP", "BOTTOM", "LINKS")      # a ground-beam detail without one of them is incomplete
TIE_NOTE = re.compile(r"(?:ST\.?|TIES?|STIRRUPS?|LINKS?)\s*(?:OF\s*COLUMNS?)?\s*[-:]?\s*(\d+)\s*Ø\s*(\d+)\s*/\s*M",
                      re.I)


def merge_conventions(generic, profile=None, overrides=None):
    """The generic set with a project profile's conventions added or overriding by id (the profile wins); then the
    person's --set overrides (recorded as overridden_from)."""
    by = {c["id"]: c for c in generic["conventions"]}
    for c in (profile or {}).get("conventions", []):
        by[c["id"]] = c
    name = generic.get("set", "GENERIC") + ("+" + profile["profile"] if profile else "")
    return PE.Conventions({"set": name, "conventions": [by[k] for k in sorted(by)]}, overrides)


def storey_heights(conv):
    return {k[len("STOREY_HEIGHT_"):]: conv.base(k) for k in conv.items if k.startswith("STOREY_HEIGHT_")}


def _cv(conv, cid, default=None):
    return conv.base(cid) if cid in conv.items else default


def _trip(conv, cid):
    return conv.triple(cid)


def column_boxes(ents, lib, unit_m, tol_m=0.02):
    sizes = set()
    for (fam, _), row in lib.items():
        if fam != "COLUMN" or row is None:
            continue
        for b in list(row["by_storey"].values()) + [{"dims_m": row.get("dims_m", {})}]:
            W, H = b["dims_m"].get("W"), b["dims_m"].get("H")
            if W and H:
                sizes.add((min(W, H), max(W, H)))
    cmarks = [m for m in MD.marks(ents["texts"]) if m["family"] == "COLUMN"]
    out = []
    for r in MD.candidate_rects(ents, unit_m):
        bx = r["box"]
        d = sorted(((bx[2] - bx[0]) * unit_m, (bx[3] - bx[1]) * unit_m))
        if any(abs(d[0] - a) <= tol_m and abs(d[1] - b) <= tol_m for a, b in sizes) or \
                (d[1] <= 1.5 and any(MD._contains(bx, m["x"], m["y"]) for m in cmarks)):
            out.append(bx)
    uniq = []
    for b in sorted(set(out)):                 # twins within 1 mm are one column (M3)
        if not any(all(abs(p - q) <= 1e-3 / unit_m for p, q in zip(b, o)) for o in uniq):
            uniq.append(b)
    return uniq


def _schedule_marks(texts, lib):
    """plan marks with the family their schedule row has: a token whose pattern family has no row but which IS a row
    of another family takes that family (CA: a cantilever beam row, a column by pattern) - M3"""
    by_mark = defaultdict(set)
    for fam, mk in lib:
        by_mark[mk].add(fam)
    out = []
    for m in MD.marks(texts):
        if (m["family"], m["mark"]) not in lib and len(by_mark.get(m["mark"], ())) == 1:
            m = dict(m, family=next(iter(by_mark[m["mark"]])), family_from_schedule=True)
        out.append(m)
    return out


def width_modes(ents, layers_ok, unit_m, lo_m=0.15, hi_m=1.0, min_count=4):
    """Separations of parallel, overlapping face pairs (10 mm bins) that occur at least min_count times."""
    segs = [s for s in ents["segments"] if s["layer"] in layers_ok and math.dist(s["a"], s["b"]) * unit_m >= 1.0]
    c = Counter()
    for i, a in enumerate(segs):
        ux, uy = a["b"][0] - a["a"][0], a["b"][1] - a["a"][1]
        La = math.hypot(ux, uy)
        ux, uy = ux / La, uy / La
        for b in segs[i + 1:]:
            vx, vy = b["b"][0] - b["a"][0], b["b"][1] - b["a"][1]
            Lb = math.hypot(vx, vy)
            if abs(ux * vy / Lb - uy * vx / Lb) > 0.01:
                continue
            off = abs((b["a"][0] - a["a"][0]) * -uy + (b["a"][1] - a["a"][1]) * ux) * unit_m
            if not (lo_m <= off <= hi_m):
                continue
            ta = sorted((0.0, La))
            tb = sorted(((b["a"][0] - a["a"][0]) * ux + (b["a"][1] - a["a"][1]) * uy,
                         (b["b"][0] - a["a"][0]) * ux + (b["b"][1] - a["a"][1]) * uy))
            if min(ta[1], tb[1]) - max(ta[0], tb[0]) <= 0.5 / unit_m:
                continue
            c[round(off * 100) / 100.0] += 1
    return sorted(w for w, n in c.items() if n >= min_count)


def typical_gb_widths(conv):
    """the widths of the printed typical ground-beam sections a profile carries (GB_TYPICAL_SECTIONS classes and a
    GB_EXTERIOR_DETAIL), the source-supported widths for an unmarked ground-beam network - M3"""
    out = set()
    if conv is not None and "GB_TYPICAL_SECTIONS" in conv.items:
        out |= {round(c["W"], 3) for c in conv["GB_TYPICAL_SECTIONS"].get("classes") or [] if c.get("W")}
    if conv is not None and "GB_EXTERIOR_DETAIL" in conv.items and conv["GB_EXTERIOR_DETAIL"].get("W"):
        out.add(round(conv["GB_EXTERIOR_DETAIL"]["W"], 3))
    return sorted(out)


STRAP_WIDTH_TOL_M = 0.015              # the binding tolerance of bind_marks / _gb_class (a 1:100 drawing's precision)


def _straps(E, S, lib, u, footings):
    """Strap beams on a foundation plan (M3): parallel face pairs at a scheduled strap width, on the layers a strap
    mark points at, with the plan inside every footing outline left to the footing (clear length between footing
    faces). A pair lying inside footing outlines is two outline sides, not a strap. Only a band a strap mark binds is
    a strap; a strap-width pair no mark reaches is reported, never quantified (it may be any two parallel lines)."""
    rows = [r for r in S["rows"] if r["family"] == "STRAP_BEAM" and r["dims_m"].get("W")]
    marks = [m for m in _schedule_marks(E["texts"], lib) if m["family"] == "STRAP_BEAM"]
    out = {"bands": [], "marks": [], "layers": [], "inside_footing": 0, "unbound_candidates": []}
    if not rows or not marks:
        out["reason"] = "no strap schedule rows" if not rows else "no strap marks on the plan"
        out["marks"] = [dict(m, state="TAG_UNBOUND", band=None, bands=[]) for m in marks]
        return out
    widths_m = sorted({round(r["dims_m"]["W"], 3) for r in rows})
    widths = [w / u for w in widths_m]
    tol = STRAP_WIDTH_TOL_M / u
    sc = MD.strap_layers(E, widths, tol, marks, 0.3 / u)
    lays = {k for k, v in sc.items() if v >= max(1, 0.5 * max(sc.values()))} if sc else set()
    out.update(layers=sorted(lays), widths_m=widths_m)
    if not lays:
        out["marks"] = [dict(m, state="TAG_UNBOUND", band=None, bands=[]) for m in marks]
        return out
    bands, _ = MD.beam_bands(E, lays, widths, tol, 0.3 / u)
    bands = [b for b in bands if b["kind"] == "STRAIGHT"]
    polys = [f.get("polygon") or MD.box_poly(f["box"]) for f in footings if f.get("polygon") or f.get("box")]
    keep, inside = MD.deduct_support_plan(bands, polys, u)
    # a pair whose two faces are both sides of footing outlines is the gap between two footings, never a strap
    outl = {str(f.get("outline")) for f in footings if f.get("outline")}
    on_outline = [b for b in keep if sum(1 for h in b.get("handles", [])[:2] if h.rsplit(":", 1)[0] in outl) == 2]
    keep = [b for b in keep if b not in on_outline]
    out["between_footings"] = len(on_outline)
    wof = defaultdict(set)
    for r in rows:
        wof[(r["family"], r["mark"])].add(round(r["dims_m"]["W"], 3))
    bound = MD.bind_marks(keep, marks, {k: tuple(sorted(v)) for k, v in wof.items()}, u,
                          width_tol_m=STRAP_WIDTH_TOL_M)
    by_band = defaultdict(list)
    for m in bound:
        if m["state"].startswith("BOUND"):
            for bid in m.get("bands") or []:
                by_band[bid].append(m)
    for b in keep:
        W = b["width_native"] * u
        ms = by_band.get(b["band_id"], [])
        mk = sorted({m["mark"] for m in ms})
        rec = {"band_id": b["band_id"], "kind": "STRAIGHT", "width_m": W, "length_m": b["clear_length_m"],
               "band_length_m": b["length"] * u, "polygon": b["polygon"], "handles": b.get("handles", []),
               "net_plan_m2": b["net_plan_m2"], "support_overlap_m2": b["support_overlap_m2"],
               "n_footings_cut": len(b["supports"]), "family": "STRAP_BEAM"}
        if not mk:
            out["unbound_candidates"].append(rec)
            continue
        if len(mk) > 1:
            rec["state"] = "MULTIPLE_MARKS"
            rec["marks"] = mk
            out["bands"].append(rec)
            continue
        cands = [r for r in rows if r["mark"] == mk[0]]
        fit = [r for r in cands if abs(r["dims_m"]["W"] - W) <= STRAP_WIDTH_TOL_M]
        if len(cands) == 1:
            row, state = cands[0], "BOUND" if fit else "BOUND_WIDTH_CONFLICT"
        elif len(fit) == 1:
            row, state = fit[0], "BOUND_ROW_BY_DRAWN_WIDTH"     # duplicate rows: the drawn width selects one
        else:
            row, state = None, "SCHEDULE_CONFLICT"
        rec.update(state=state, mark=mk[0], binding=sorted({m["state"] for m in ms})[0],
                   alternatives=[{"source": r["source"], "W": r["dims_m"]["W"], "H": r["dims_m"].get("H"),
                                  "bars": r.get("bars", [])} for r in cands if r is not row])
        if row is not None:
            rec.update(depth_m=row["dims_m"].get("H"), schedule_width_m=row["dims_m"]["W"], bars=row.get("bars", []),
                       schedule_source=row["source"])
        out["bands"].append(rec)
    out["inside_footing"] = len(inside)
    out["marks"] = bound
    return out


def detect(intake, *, typical_widths_m=None):
    """typical_widths_m: the widths of printed typical ground-beam sections (typical_gb_widths(conv)); when given, or
    when the schedule has ground-beam rows, a ground-beam plan is searched at those widths only and every other drawn
    width mode is recorded as rejected (M3: a slab strip between two faces is not a ground beam)."""
    M = DM.build(intake)
    u = M["units"]["unit_m"]
    S = SR.from_attribute_rows(intake["attributes"], sheet_of=M["sheet_of"])
    if len(S["rows"]) < 3:
        for sh in M["sheets"]:
            if sh["role"] == "SCHEDULE":
                ts = [t for t in M["texts"] if t["sheet"] == sh["sheet_id"]]
                h = sorted(t.get("height") or 0 for t in ts)
                hm = h[len(h) // 2] if h else 0.2 / u
                T = SR.from_text_table(ts, row_tol=hm * 0.6, col_pad=hm * 0.5)
                S["rows"] += T["rows"]
                S["warnings"] += T["warnings"]
        S = SR._finish(S["rows"], _fam_vals(S["rows"]), S["warnings"], "MIXED")
    lib = SR.library(S)
    tol = 0.012 / u
    out = {"model": M, "schedule": S, "lib": lib, "unit_m": u, "sheets": {}}
    for sh in M["sheets"]:
        E = DM.sheet_entities(M, intake, sh["sheet_id"])
        rec = {"sheet": sh, "n_segments": len(E["segments"])}
        if sh["role"] == "FOUNDATION_PLAN":
            rec["footings"] = MD.footings(sh, E, lib, u)
            rec["columns"] = MD.column_occurrences(sh, E, lib, u)
            rec["straps"] = _straps(E, S, lib, u, rec["footings"])
        elif sh["role"] == "COLUMN_PLAN":
            rec["columns"] = MD.column_occurrences(sh, E, lib, u)
        elif sh["role"] in ("SLAB_PLAN", "GROUND_BEAM_PLAN"):
            fams = MD.BEAM_FAMILIES if sh["role"] == "SLAB_PLAN" else MD.GROUND_FAMILIES
            widths_m = sorted({round(r["dims_m"]["W"], 3) for r in S["rows"] if r["family"] in fams and
                               r["dims_m"].get("W")})
            cand = {s["layer"] for s in E["segments"] if MD._layer_role(s["layer"]) not in
                    MD.ANNOTATION_ROLES + ("COLUMN", "FOOTING")}
            basis = {"SCHEDULE": list(widths_m)}
            if sh["role"] == "GROUND_BEAM_PLAN":
                gbw = {round(r["dims_m"]["W"], 3) for r in S["rows"] if r["family"] == "GROUND_BEAM" and
                       r["dims_m"].get("W")}
                tw = sorted(set(typical_widths_m or ()))
                modes = width_modes(E, cand, u)
                if gbw or tw:
                    ok = set(widths_m) | set(tw)
                    basis.update(TYPICAL_DETAIL=tw, REJECTED_DRAWN_MODES=[w for w in modes if all(
                        abs(w - x) > STRAP_WIDTH_TOL_M for x in ok)])
                    widths_m = sorted(ok)
                else:                                  # nothing printed: drawn width modes, recorded as such
                    basis["DRAWN_MODES"] = modes
                    widths_m = sorted(set(widths_m) | set(modes))
            widths = [w / u for w in widths_m]
            bm = [m for m in _schedule_marks(E["texts"], lib) if m["family"] in fams]
            sc = MD.score_edge_layers(E, widths, tol, bm, min_face_native=0.3 / u) if widths else {}
            if not sc and widths:                     # unmarked network (typical ground beams): densest pair layer
                cnt = {}
                for lay in sorted(cand):
                    if MD.outline_share(E, lay) > 0.5:
                        continue
                    faces = MD._faces(E, {lay})
                    if 2 <= len(faces) <= 6000:
                        cnt[lay] = sum(len(GN.pair_straight(faces, width=w, tol=tol, admitted_layers={lay},
                                                            min_face=0.3 / u, min_overlap=0.3 / u,
                                                            join_tol=0.001 / u)["bands"]) for w in widths)
                sc = {k: v for k, v in cnt.items() if v >= 5}
            lays = {l for l, v in sc.items() if v >= max(2, 0.2 * max(sc.values()))} if sc else set()
            cols = column_boxes(E, lib, u)
            # every column-sized outline on the layers that carry the column boxes, at any size: storey-presence
            # evidence only (a column drawn at a size no schedule band prints is still a column) - M3
            clay = {r["layer"] for r in MD.candidate_rects(E, u) if tuple(r["box"]) in {tuple(c) for c in cols}}
            rec["column_presence"] = [r["box"] for r in MD.candidate_rects(E, u) if r["layer"] in clay and
                                      0.15 <= min(r["box"][2] - r["box"][0], r["box"][3] - r["box"][1]) * u and
                                      max(r["box"][2] - r["box"][0], r["box"][3] - r["box"][1]) * u <= 1.5]
            heal = []
            if lays:                                   # drafting noise: duplicates, broken faces, ends short of a face
                segs, h1 = CH.merge_collinear(E["segments"], lays, gap=CH.GAP_M / u, off_tol=0.5e-3 / u)
                tgt = [(p[j], p[(j + 1) % 4]) for c in cols for p in [MD.box_poly(c)] for j in range(4)]
                wide = CH.WIDE_SNAP_FRACTION * min(widths_m) / u if widths_m else None
                segs, h2 = CH.extend_dangling(segs, lays, tgt, snap=CH.SNAP_M / u, eps=0.5e-3 / u, wide_snap=wide)
                E = dict(E, segments=segs)
                heal = h1 + h2
            rec["heal"] = {"merged": sum(1 for h in heal if h["code"] == "HEAL_MERGE"),
                           "extended": sum(1 for h in heal if h["code"] == "HEAL_EXTEND"),
                           "extended_wide": [h for h in heal if h["code"] == "HEAL_EXTEND_WIDE"], "log": heal[:200]}
            bands, conf = MD.beam_bands(E, lays, widths, tol, 0.3 / u) if lays else ([], [])
            bands = MD.split_at_supports(bands, cols, 0.05 / u)
            widths_of = defaultdict(set)              # every printed width of a mark (duplicate rows kept)
            for r in S["rows"]:
                if r["dims_m"].get("W"):
                    widths_of[(r["family"], r["mark"])].add(r["dims_m"]["W"])
            widths_of = {k: tuple(sorted(v)) for k, v in widths_of.items()}
            bound = MD.bind_marks(bands, bm, widths_of, u)
            inh = MD.inherit_sections(bands, bound, lib, 1.0 / u)
            rec.update(edge_layers=sorted(lays), layer_scores=sc, widths_m=widths_m, width_basis=basis,
                       column_boxes=cols,
                       bands=bands, band_conflicts=conf, marks=bound, inherited=inh)
            slab = SE.panels(E, lays, bands, cols, u, region_id=sh["sheet_id"]) if lays else None
            rec["slab"] = slab
            rec["band_sides"] = SE.band_sides(slab["faces"], bands, u, cols) if slab else {}
            t = slab["uniform_t_m"] if slab and slab.get("uniform_t_m") else None
            rec["beams"] = MD.beam_quantities(bands, bound + inh, lib, [], u, t)
            rec["texts"] = E["texts"]
        out["sheets"][sh["sheet_id"]] = rec
    return out


def _fam_vals(rows):
    fv = defaultdict(lambda: defaultdict(list))
    for r in rows:
        for k, v in r.get("dims_raw", {}).items():
            fv[r["family"]][k].append(v)
    return fv


# ====================================================================== items
def _common(**kw):
    return kw


# families the generic engine does not quantify yet: drawing evidence makes them NOT_DETECTED lines (coverage risk)
SCOPE_WORDS = {
    "STAIRS": ("STAIR", "FLIGHT", "LANDING", "درج", "سلم"),
    "LINTELS": ("LINTEL", "عتب"),
    "LIFT": ("LIFT", "ELEVATOR", "مصعد"),
    "POOL": ("POOL", "SWIMMING", "مسبح"),
    "WATER_TANK": ("WATER TANK", "TANK", "خزان"),
    "DOMES": ("DOME", "قبة"),
    "PARAPETS": ("PARAPET", "دروة"),
    "PLAIN_CONCRETE": ("BLINDING", "PLAIN CONCRETE", "P.C.", "خرسانة عادية", "نظافة"),
    "WALLS": ("BOUNDARY WALL", "RETAINING", "SHEAR WALL", "سور", "جدار"),
    "CANTILEVER_PORTIONS": ("CANTILEVER", "كابولي"),
    "COLUMN_NECKS": ("NECK", "رقبة"),
}
SCOPE_EN = {"درج": "STAIR", "سلم": "STAIR", "عتب": "LINTEL", "مصعد": "LIFT", "مسبح": "POOL", "خزان": "TANK",
            "قبة": "DOME", "دروة": "PARAPET", "خرسانة عادية": "PLAIN CONCRETE", "نظافة": "BLINDING",
            "سور": "BOUNDARY WALL", "جدار": "WALL", "كابولي": "CANTILEVER", "رقبة": "NECK"}


def scope_scan(D):
    """{family: {keywords (English), n_texts, sheets}} for families outside the generic scope that the drawing
    mentions. Evidence is the matched keyword only - never the text itself."""
    out = {}
    for t in D["model"]["texts"]:
        u = t["norm"].upper()
        for fam, words in SCOPE_WORDS.items():
            hit = [w for w in words if w.upper() in u]
            if hit:
                r = out.setdefault(fam, {"keywords": set(), "n_texts": 0, "sheets": set()})
                r["keywords"].update(SCOPE_EN.get(w, w) for w in hit)
                r["n_texts"] += 1
                if t.get("sheet"):
                    r["sheets"].add(t["sheet"])
    return {f: {"keywords": sorted(r["keywords"]), "n_texts": r["n_texts"], "sheets": sorted(r["sheets"])}
            for f, r in sorted(out.items())}


def items_from(D, conv, heights=None, evidence=None):
    """evidence: a detail-evidence document (engine.source.detail_evidence schema; tools/pdf_evidence.py or a manual
    transcription) - typical ground-beam bars come from it, OCR-derived ones as PROVISIONAL / LOW."""
    heights = heights or {}
    gb_details = DE.ground_beam_details(evidence) if evidence else []
    u = D["unit_m"]
    items, register, risk = [], [], []
    src_file = D["model"]["file"]
    hook_std = _cv(conv, "REBAR_HOOK_STANDARD", "ACI_318_19")
    covers = {k: _trip(conv, f"REBAR_COVER_{k}_M") for k in ("BEAM", "COLUMN", "FOOTING")}
    notes = " ".join(t["norm"] for t in D["model"]["texts"])
    tie = TIE_NOTE.search(notes)
    tie_rule = (int(tie.group(1)), float(tie.group(2))) if tie else None

    def reg(component_id, family, storey, state, reason, kg=None):
        register.append({"COMPONENT_ID": component_id, "FAMILY": family, "STOREY": storey, "REBAR_STATE": state,
                         "REASON": reason, "PROVISIONAL_KG_BASE": kg})

    # ---------------------------------------------------------------- footings
    for sid, rec in sorted(D["sheets"].items()):
        for f in rec.get("footings", []):
            cid = f["member_id"]
            common = dict(component_id=cid, trade="CONCRETE", family="FOOTINGS", storey="FOUNDATION",
                          source=f"{src_file} {sid} outline {f.get('outline')}; schedule {f.get('schedule_source')}",
                          dimensions={"drawn_m": f.get("drawn_m"), "schedule_m": f.get("schedule_m")},
                          double_count_risk="overlaps with other footings deducted once" if f.get("overlaps") else
                          "none found (outline overlap checked)")
            ded = sum(o["area_m2"] for o in f.get("overlaps", []) if o.get("deduct")) * \
                (f.get("schedule_m") or [0, 0, 0])[2] if f.get("schedule_m") else 0.0
            if f["state"] == "CONFIRMED" and f.get("volume_polygon"):
                v = f["volume_polygon"] - ded
                items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=v, base=v, high=v,
                                     formula="drawn polygon area x D (schedule); the outline is clipped where it "
                                             "meets a neighbour, and the clipped part belongs to the neighbour",
                                     assumptions=["FROZEN:SOURCE_COMPLETE"], support="SOURCE_COMPLETE_UNREVIEWED",
                                     confidence="HIGH", blocker="NOT_REVIEWED", **common))
            elif f["state"] == "CONFIRMED" and f.get("volume_schedule"):
                v = f["volume_schedule"] - ded
                outside = f.get("binding") == "LABEL_OUTSIDE_NEAREST_OUTLINE"
                items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=v, base=v, high=v,
                                     formula="L x W x D (schedule; drawn outline confirms L x W) - overlap" +
                                     ("; the label sits outside its outline (nearest unclaimed outline)"
                                      if outside else ""),
                                     assumptions=["FROZEN:SOURCE_COMPLETE"], support="SOURCE_COMPLETE_UNREVIEWED",
                                     confidence="MEDIUM" if outside else "HIGH", blocker="NOT_REVIEWED", **common))
            elif f["state"] in ("LABEL_ONLY", "LABEL_TYPE_CONFLICT") and not all(
                    k in conv.items for k in ("FOOTING_LABEL_ONLY", "FOOTING_LABEL_CONFLICT")):
                # a convention set without the M3 label rules (e.g. V1): the M2 behaviour, unresolved
                items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                                     confidence="LOW", blocker="NO_OUTLINE", expression="L x W x D", **common))
                reg(cid, "FOOTINGS", "FOUNDATION", "MISSING_DATA", "NO_OUTLINE")
                risk.append({"KIND": "FOOTING_NO_OUTLINE", "WHERE": f"{sid} {f.get('mark')}", "DETAIL": cid})
                continue
            elif f["state"] == "LABEL_TYPE_CONFLICT":
                vals = {k: c["volume"] for k, c in sorted(f["candidates"].items())}
                lo, b, hi = PE.by_choice(conv, "FOOTING_LABEL_CONFLICT", {"LARGER": max(vals.values()),
                                                                          "SMALLER": min(vals.values())})
                items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=lo, base=b, high=hi,
                                     formula="one footing labelled with two types and no outline found: the larger "
                                             "or the smaller schedule type (" + ", ".join(f"{k} {v:.3f} m3" for k, v
                                                                                      in vals.items()) + ")",
                                     assumptions=["FOOTING_LABEL_CONFLICT"], support="CONVENTION_ONLY",
                                     confidence="LOW", blocker="SOURCE_CONFLICT", **common))
                risk.append({"KIND": "FOOTING_LABEL_TYPE_CONFLICT", "WHERE": f"{sid} {'/'.join(vals)}",
                             "DETAIL": f"{cid} and {f['conflict_with']}: quantified once"})
                reg(cid, "FOOTINGS", "FOUNDATION", "MISSING_DATA", "footing type conflict: bars of which type")
                continue
            elif f["state"] == "LABEL_TYPE_CONFLICT_SECONDARY":
                reg(cid, "FOOTINGS", "FOUNDATION", "OUTSIDE_SCOPE",
                    f"second label of {f['conflict_with']} (quantified there once)")
                continue
            elif f["state"] == "LABEL_ONLY" and f.get("volume_schedule"):
                v = f["volume_schedule"]
                items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=v, base=v, high=v,
                                     formula="L x W x D of the labelled schedule type; the physical outline was "
                                             "NOT found, so its position and plan size are not confirmed",
                                     assumptions=["FOOTING_LABEL_ONLY"], support="ONE_ASSUMED_DIMENSION",
                                     confidence="LOW", blocker="OUTLINE_NOT_CONFIRMED", **common))
                risk.append({"KIND": "FOOTING_LABEL_ONLY", "WHERE": f"{sid} {f.get('mark')}",
                             "DETAIL": f"{cid}: schedule-size quantity, outline not found "
                                       f"({f['evidence']['segments_within_footing_size']} footing-size segments "
                                       f"near the label)"})
            elif f["state"] == "TYPE_BY_SIZE_MATCH" and f.get("volume_schedule"):
                v = f["volume_schedule"] - ded
                items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=v, base=v, high=v,
                                     formula="L x W x D of the one schedule type whose plan size equals the drawn "
                                             "outline (the outline holds a column mark only)",
                                     assumptions=["FOOTING_TYPE_FROM_SIZE"], support="CONVENTION_ONLY",
                                     confidence="LOW", blocker="FOOTING_TAG_MISSING", **common))
            elif f["state"] == "SIZE_MISMATCH" and f.get("volume_schedule") and f.get("volume_drawn"):
                lo, b, hi = PE.by_choice(conv, "FOOTING_SIZE_MISMATCH", {"SCHEDULE": f["volume_schedule"] - ded,
                                                                         "DRAWN": f["volume_drawn"] - ded})
                items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=lo, base=b, high=hi,
                                     formula="schedule or drawn plan size x schedule D", support="CONVENTION_ONLY",
                                     assumptions=["FOOTING_SIZE_MISMATCH"], confidence="LOW",
                                     blocker="SECTION_CONFLICT", **common))
            else:
                items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                                     confidence="LOW", blocker=f["state"], expression="L x W x D", **common))
                reg(cid, "FOOTINGS", "FOUNDATION", "MISSING_DATA", f["state"])
                risk.append({"KIND": "FOOTING_" + f["state"], "WHERE": f"{sid} {f.get('mark')}", "DETAIL": cid})
                continue
            # footing bars: SH runs the short side, LO the long side; count given or per metre
            bars = f.get("bars") or []
            kg = _footing_bars(f, bars, covers["FOOTING"], conv, hook_std)
            if kg is None:
                reg(cid, "FOOTINGS", "FOUNDATION", "MISSING_DATA", "no readable bar roles in the schedule row")
            else:
                lo, b, hi, dia_kg = kg
                for d, (dl, db, dh) in sorted(dia_kg.items()):
                    items.append(PE.item(item_id=f"P-S:{cid}:D{d:g}", component_id=cid, trade="REINFORCEMENT",
                                         family="FOOTINGS", storey="FOUNDATION", category="PROVISIONAL", low=dl,
                                         base=db, high=dh, dia_mm=d, source=common["source"],
                                         formula="count x (side - 2 cover [+ hooks]) x d^2/162 per direction",
                                         assumptions=["REBAR_COVER_FOOTING_M", "FOOTING_BAR_END",
                                                      "REBAR_HOOK_STANDARD"], support="CONVENTION_ONLY",
                                         confidence="MEDIUM", blocker="BAR_DETAIL_RULES"))
                reg(cid, "FOOTINGS", "FOUNDATION", "PROVISIONAL_MODEL", "schedule bars x drawn outline", b)

    # ---------------------------------------------------------------- columns
    occ = []
    for sid, rec in sorted(D["sheets"].items()):
        if rec["sheet"]["role"] == "COLUMN_PLAN":
            occ += rec.get("columns", [])
    if not occ:
        for sid, rec in sorted(D["sheets"].items()):
            if rec["sheet"]["role"] == "FOUNDATION_PLAN":
                occ += rec.get("columns", [])
    fsheets = [rec for _, rec in sorted(D["sheets"].items()) if rec["sheet"]["role"] == "FOUNDATION_PLAN"]
    necks_from_foundation = bool(fsheets) and any(r["sheet"]["role"] == "COLUMN_PLAN" for r in D["sheets"].values())
    if necks_from_foundation:
        _neck_items(items, reg, risk, fsheets, conv, covers, tie_rule, src_file)
    # storey presence: a column piece counts at a storey only if that storey's roof-slab plan shows a column outline
    # at the occurrence's position (sheets share local coordinates: world - sheet origin). A schedule band alone is
    # no evidence (M3: every type with a 2F band was counted on a partial 2F).
    slab_cols = {}
    for rec in D["sheets"].values():
        if rec["sheet"]["role"] == "SLAB_PLAN" and (rec.get("column_boxes") or rec.get("column_presence")):
            o_ = rec["sheet"].get("origin") or (0.0, 0.0)
            slab_cols.setdefault(rec["sheet"]["storey"], []).extend(
                ((c[0] + c[2]) / 2 - o_[0], (c[1] + c[3]) / 2 - o_[1]) for c in
                list(rec.get("column_boxes", [])) + list(rec.get("column_presence", [])))
    origin_of = {sid: (rec["sheet"].get("origin") or (0.0, 0.0)) for sid, rec in D["sheets"].items()}
    for p in MD.column_storeys(occ, heights):
        cid = p["piece_id"]
        st = p["storey"]
        if necks_from_foundation and st == "FOUNDATION":
            continue                         # necks are measured on the foundation plan, over their own footing
        if st in slab_cols and p.get("state") == "MEASURED":
            if p.get("box"):
                o_ = origin_of.get(p["sheet"], (0.0, 0.0))
                cx = (p["box"][0] + p["box"][2]) / 2 - o_[0]
                cy = (p["box"][1] + p["box"][3]) / 2 - o_[1]
                near = min(math.hypot(cx - a, cy - b) for a, b in slab_cols[st]) * u
                if near > 0.25:
                    reg(cid, "COLUMNS", st, "EXPLICIT_NONE", f"no column outline on the {st} roof-slab plan at this "
                                                           f"position (nearest {near:.2f} m)")
                    risk.append({"KIND": "COLUMN_ABSENT_ON_STOREY_PLAN", "WHERE": f"{st} {p['mark']}",
                                 "DETAIL": f"{cid}: schedule band {st} exists but the {st} roof-slab plan shows no "
                                           f"column here; not counted"})
                    continue
            else:
                risk.append({"KIND": "COLUMN_STOREY_PRESENCE_UNVERIFIED", "WHERE": f"{st} {p['mark']}",
                             "DETAIL": f"{cid}: no column outline bound on the column plan; counted on the schedule "
                                       f"band alone"})
        common = dict(component_id=cid, trade="CONCRETE", family="COLUMNS", storey=st,
                      source=f"{src_file} {p['sheet']} mark {p['mark']}; schedule storey band {st}",
                      dimensions={"section_m": p.get("section_m"), "drawn_m": p.get("drawn_m"),
                                  "height_m": p.get("height_m")},
                      double_count_risk="the column owns its footprint; beams split at its outline")
        if p["state"] != "MEASURED":
            exp = p.get("section_m")
            hts = sorted(h for h in heights.values() if h)
            dr = p.get("drawn_m")                # a type with no schedule row: the drawn section gives an exposure
            el = dr[0] * dr[1] * hts[0] if (dr and hts and not exp) else None
            eh = dr[0] * dr[1] * sum(hts) if (dr and hts and not exp) else None
            items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                                 blocker="STOREY_HEIGHT_NOT_PRINTED" if p["state"] == "NO_HEIGHT" else p["state"],
                                 exposure_low=el, exposure_high=eh,
                                 expression=(f"{exp[0]:g} x {exp[1]:g} x storey height" if exp else
                                             (f"drawn {dr[0]:g} x {dr[1]:g} x one to all storey heights (exposure "
                                              f"only)" if dr else "B x H x height")), **common))
            reg(cid, "COLUMNS", st, "MISSING_DATA", "storey height not in the profile" if p["state"] == "NO_HEIGHT"
                else p["state"])
            continue
        B, H = p["section_m"]
        v = B * H * p["height_m"]
        asm = [f"STOREY_HEIGHT_{st}"] if f"STOREY_HEIGHT_{st}" in conv.items else ["FROZEN:PROFILE_HEIGHT"]
        if p["drawn_match"] is False and p["drawn_m"]:
            vd = p["drawn_m"][0] * p["drawn_m"][1] * p["height_m"]
            lo, b, hi = PE.by_choice(conv, "COLUMN_SECTION_MISMATCH", {"SCHEDULE": v, "DRAWN": vd})
            items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=lo, base=b, high=hi,
                                 formula="section (schedule or drawn) x storey height", support="CONVENTION_ONLY",
                                 assumptions=asm + ["COLUMN_SECTION_MISMATCH"], confidence="LOW",
                                 blocker="SECTION_CONFLICT", **common))
        else:
            items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=v, base=v, high=v,
                                 formula="B x H (schedule) x storey height (profile)", assumptions=asm,
                                 support="ONE_ASSUMED_DIMENSION" if asm[0].startswith("FROZEN") else
                                 "CONVENTION_ONLY", confidence="MEDIUM", blocker="NOT_REVIEWED", **common))
        main = [b for b in p.get("bars", []) if b.get("count") and b.get("dia_mm")]
        if not main:
            reg(cid, "COLUMNS", st, "MISSING_DATA", "no main bars in the schedule band")
            continue
        lap = _trip(conv, "COLUMN_LAP_D")
        tot = 0.0
        for bb in main:
            d = bb["dia_mm"]
            vals = [bb["count"] * BS.mass_kg(p["height_m"] + x * d / 1000.0, d) for x in lap]
            items.append(PE.item(item_id=f"P-S:{cid}:MAIN:D{d:g}", component_id=cid, trade="REINFORCEMENT",
                                 family="COLUMNS", storey=st, category="PROVISIONAL", low=min(vals), base=vals[1],
                                 high=max(vals), dia_mm=d, source=common["source"],
                                 formula="count x (storey height + lap) x d^2/162", assumptions=asm + ["COLUMN_LAP_D"],
                                 support="CONVENTION_ONLY", confidence="MEDIUM", blocker="LAP_ANCHORAGE_RULE"))
            tot += vals[1]
        if tie_rule:
            n, d = tie_rule
            vals = []
            for cv in covers["COLUMN"]:
                try:
                    ln = BS.closed_link(B, H, cv, d)["developed_m"]
                except ValueError:
                    continue
                vals.append(n * p["height_m"] * BS.mass_kg(ln, d))
            if vals:
                vals.sort()
                items.append(PE.item(item_id=f"P-S:{cid}:TIES:D{d:g}", component_id=cid, trade="REINFORCEMENT",
                                     family="COLUMNS", storey=st, category="PROVISIONAL", low=vals[0],
                                     base=vals[len(vals) // 2], high=vals[-1], dia_mm=d, source="printed tie note",
                                     formula="n/m x height x closed link (code bends and 135 hooks) x d^2/162",
                                     assumptions=asm + ["REBAR_COVER_COLUMN_M", "REBAR_HOOK_STANDARD"],
                                     support="CONVENTION_ONLY", confidence="MEDIUM", blocker="TIE_LINK_HOOK_RULE"))
                tot += vals[len(vals) // 2]
        reg(cid, "COLUMNS", st, "PROVISIONAL_MODEL", "schedule main bars" + (" + printed tie note" if tie_rule else
                                                                           "; ties not printed"), tot)

    # ---------------------------------------------------------------- strap beams on the foundation plan (M3)
    for sid, rec in sorted(D["sheets"].items()):
        st_ = rec.get("straps") or {}
        for b in st_.get("bands", []):
            cid = f"GROUND_BEAMS:FOUNDATION:{b['band_id']}"
            common = dict(component_id=cid, trade="CONCRETE", family="GROUND_BEAMS", storey="FOUNDATION",
                          source=f"{src_file} {sid} strap faces {','.join(map(str, b['handles'][:2]))}"
                                 + (f"; mark {b.get('mark')} ({b.get('binding')})" if b.get("mark") else ""),
                          dimensions={"width_m": round(b["width_m"], 4), "clear_length_m": round(b["length_m"], 4),
                                      "band_length_m": round(b["band_length_m"], 4),
                                      "net_plan_m2": round(b["net_plan_m2"], 5), "depth_m": b.get("depth_m"),
                                      "footing_overlap_m2": round(b["support_overlap_m2"], 5),
                                      "binding": b["state"]},
                          double_count_risk="the plan inside each footing outline is the footing's (clear length "
                                            "between footing faces)")
            if b["state"] in ("BOUND", "BOUND_ROW_BY_DRAWN_WIDTH", "BOUND_WIDTH_CONFLICT") and b.get("depth_m"):
                v = b["net_plan_m2"] * b["depth_m"]
                alts = [b["net_plan_m2"] * (a["W"] / b["width_m"]) * a["H"] for a in b.get("alternatives", [])
                        if a.get("H")]
                if b["state"] == "BOUND":
                    items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=v, base=v, high=v,
                                         formula="net plan (drawn faces, footing plan deducted) x H (schedule)",
                                         assumptions=["FROZEN:SOURCE_COMPLETE"], support="SOURCE_COMPLETE_UNREVIEWED",
                                         confidence="HIGH", blocker="NOT_REVIEWED", **common))
                elif b["state"] == "BOUND_ROW_BY_DRAWN_WIDTH":
                    items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=min([v] + alts), base=v,
                                         high=max([v] + alts),
                                         formula="net plan x H of the schedule row whose width the drawing shows; the "
                                                 "other row of the same mark gives the range",
                                         assumptions=["SCHEDULE_DUPLICATE_ROW"], support="CONVENTION_ONLY",
                                         confidence="LOW", blocker="SCHEDULE_DUPLICATE_MARK",
                                         limitations=f"{len(alts) + 1} schedule rows for {b['mark']}", **common))
                else:
                    k = b["schedule_width_m"] / b["width_m"]
                    lo_, hi_ = sorted((v, v * k))
                    base_ = v * k if _cv(conv, "WIDTH_CONFLICT_SECTION") == "SCHEDULE" else v
                    items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=lo_, base=base_, high=hi_,
                                         formula="net plan x H; drawn and scheduled widths differ",
                                         assumptions=["WIDTH_CONFLICT_SECTION"], support="CONVENTION_ONLY",
                                         confidence="LOW", blocker="SECTION_CONFLICT", **common))
                _beam_bars(items, reg, dict(b, family="STRAP_BEAM"), cid, "GROUND_BEAMS", "FOUNDATION",
                           common["source"], covers["BEAM"], conv, hook_std)
                if b.get("alternatives"):
                    register[-1]["REASON"] += (f"; {len(b['alternatives'])} other schedule row(s) for {b['mark']} "
                                               "not used (the drawn width selects this row)")
            else:
                hs = [a["H"] for a in b.get("alternatives", []) if a.get("H")] + ([b["depth_m"]] if b.get("depth_m")
                                                                                 else [])
                items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                                     confidence="LOW", blocker=b["state"],
                                     exposure_low=b["net_plan_m2"] * min(hs) if hs else None,
                                     exposure_high=b["net_plan_m2"] * max(hs) if hs else None,
                                     expression=f"{b['net_plan_m2']:.3f} m2 x H (schedule rows conflict)", **common))
                reg(cid, "GROUND_BEAMS", "FOUNDATION", "MISSING_DATA", "strap section not established (" +
                    b["state"] + ")")
        for b in st_.get("unbound_candidates", []):
            risk.append({"KIND": "STRAP_CANDIDATE_UNBOUND", "WHERE": sid,
                         "DETAIL": f"{b['band_id']} {b['width_m']:.2f} x {b['length_m']:.2f} m clear, faces "
                                   f"{','.join(map(str, b['handles'][:2]))}: a strap-width pair no strap mark reaches"})
        for m in st_.get("marks", []):
            if m["state"] in ("TAG_UNBOUND", "AMBIGUOUS", "TYPE_NOT_IN_SCHEDULE"):
                risk.append({"KIND": "STRAP_MARK_" + m["state"], "WHERE": sid,
                             "DETAIL": f"{m['mark']} at {round(m['x'])},{round(m['y'])}"})

    # ---------------------------------------------------------------- beams, ground beams, slabs
    for sid, rec in sorted(D["sheets"].items()):
        sh = rec["sheet"]
        if "beams" not in rec:
            continue
        ground = sh["role"] == "GROUND_BEAM_PLAN"
        fam = "GROUND_BEAMS" if ground else "BEAMS"
        st = sh["storey"]
        lib = D["lib"]
        for b in rec["beams"]:
            cid = f"{fam}:{st}:{b['band_id']}"
            common = dict(component_id=cid, trade="CONCRETE", family=fam, storey=st,
                          source=f"{src_file} {sid} band faces {','.join(map(str, b['handles'][:2]))}"
                                 + (f"; mark {b.get('mark')} ({b.get('binding')})" if b.get("mark") else ""),
                          dimensions={"width_m": round(b["width_m"], 4), "length_m": round(b["length_m"], 4),
                                      "net_plan_m2": round(b["net_plan_m2"], 5), "depth_m": b.get("depth_m"),
                                      "junction_deductions": len(b.get("junction_deductions", []))},
                          double_count_risk="column footprint split out; junction squares owned by one band; slab "
                                            "panels stop at band faces")
            if b["state"] == "BOUND" and b.get("depth_m"):
                inh = "INHERITED" in (b.get("binding") or "")
                if inh and _cv(conv, "COLLINEAR_INHERITANCE") == "OFF":
                    items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                                         confidence="LOW", blocker="UNTAGGED_SPAN", expression="B x H x L (no tag)",
                                         **common))
                    reg(cid, fam, st, "MISSING_DATA", "untagged span")
                    continue
                A, Bv = b["v_total_depth"], b.get("v_below_slab")
                asm = ["BEAM_DEPTH_READING"] + (["COLLINEAR_INHERITANCE"] if inh else [])
                vals = {"TOTAL_DEPTH": A, "BELOW_SLAB": Bv if Bv is not None else A}
                if "WIDTH_CONFLICT" in (b.get("binding") or "") and b.get("schedule_width_m"):
                    k = b["schedule_width_m"] / b["width_m"]
                    v4 = {(w, r): vals[r] * (k if w == "SCHEDULE" else 1.0) for w in ("SCHEDULE", "DRAWN")
                          for r in vals}
                    base = v4[(_cv(conv, "WIDTH_CONFLICT_SECTION"), _cv(conv, "BEAM_DEPTH_READING"))]
                    lo, hi = min(v4.values()), max(v4.values())
                    asm.append("WIDTH_CONFLICT_SECTION")
                    conf, blk = "LOW", "SECTION_CONFLICT"
                else:
                    lo, base, hi = PE.by_choice(conv, "BEAM_DEPTH_READING", vals)
                    conf, blk = ("LOW" if inh else "MEDIUM"), "BEAM_DEPTH_CONVENTION"
                items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=lo, base=base, high=hi,
                                     formula="net plan (B x L - column - junction) x H  |  x (H + t)",
                                     assumptions=asm, support="CONVENTION_ONLY", confidence=conf, blocker=blk,
                                     **common))
                _beam_bars(items, reg, b, cid, fam, st, common["source"], covers["BEAM"], conv, hook_std)
            elif ground and b["state"] == "UNBOUND" and "GB_TYPICAL_SECTIONS" in conv.items:
                cls = _gb_class(conv, b)
                if cls is None:
                    items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                                         confidence="LOW", blocker="GB_CLASS_WIDTH_MISMATCH",
                                         expression="drawn width matches no printed typical class", **common))
                    reg(cid, fam, st, "MISSING_DATA", "drawn width matches no typical class")
                    continue
                sides = rec.get("band_sides", {}).get(b["band_id"], [])
                common["dimensions"].update(binding="BOUND_TYPICAL_CLASS", sides=sides)
                ext = _gb_exterior(conv, b) if "OUTSIDE" in sides else None
                if "OUTSIDE" in sides and ext is None:
                    risk.append({"KIND": "GB_EXTERIOR_DEPTH_NOT_ESTABLISHED", "WHERE": sid,
                                 "DETAIL": f"{cid}: perimeter band; no printed exterior detail / levels in the profile"
                                           " - the typical class section is used"})
                lo, base, hi, note = cls["volumes"]
                asm = ["GB_TYPICAL_SECTIONS", "GB_LENGTH_BASIS"]
                formula = ("net plan x class depth (typical section by support-to-support span; the class at the "
                           "other length basis gives the range)")
                blk, H_bars = "GB_TITLES_AND_LENGTH_BASIS", None
                if ext:
                    e_lo, e_b, e_hi = (b["net_plan_m2"] * d for d in ext["depth"])
                    exterior = _cv(conv, "GB_EXTERIOR_CANDIDATE", "EXTERIOR") == "EXTERIOR"
                    lo, hi = min(lo, e_lo), max(hi, e_hi)
                    base = e_b if exterior else base
                    asm += ext["assumptions"]
                    formula = ("perimeter band (one side on the outside of the ground-beam network): net plan x "
                               "(floor level - build-up - outer ground level), the printed exterior detail; the typical"
                               " class section gives the low end")
                    blk = "GB_EXTERIOR_DEPTH"
                    note += f"; exterior depth {ext['depth'][1]:.2f} m ({ext['depth'][0]:.2f} - {ext['depth'][2]:.2f})"
                    H_bars = ext["depth"][1] if exterior else None
                items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=lo, base=base, high=hi,
                                     formula=formula, assumptions=asm, support="CONVENTION_ONLY", confidence="LOW",
                                     blocker=blk, limitations=note, **common))
                _gb_bars(items, reg, b, cid, fam, st, common["source"], cls, ext if H_bars else None, gb_details,
                         covers["BEAM"], conv, hook_std)
            else:
                rows_w = [r["dims_m"]["H"] for r in D["schedule"]["rows"] if r["family"] in
                          (MD.GROUND_FAMILIES if ground else MD.BEAM_FAMILIES) and r["dims_m"].get("W") and
                          abs(r["dims_m"]["W"] - b["width_m"]) <= 0.015 and r["dims_m"].get("H")]
                if rows_w:
                    hl, hh = min(rows_w), max(rows_w)
                    asm = []
                else:
                    hl, _, hh = _trip(conv, "GB_DEPTH_EXPOSURE_M" if ground else "UNTAGGED_BEAM_DEPTH_RANGE_M")
                    asm = ["GB_DEPTH_EXPOSURE_M" if ground else "UNTAGGED_BEAM_DEPTH_RANGE_M"]
                items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                                     confidence="LOW", blocker=b["state"] if b["state"] != "BOUND" else
                                     "NO_SCHEDULE_DEPTH", assumptions=asm,
                                     exposure_low=b["net_plan_m2"] * hl, exposure_high=b["net_plan_m2"] * hh,
                                     expression=f"{b['net_plan_m2']:.3f} m2 x H (H not established; "
                                                f"{hl:g} - {hh:g} m at this width)", **common))
                reg(cid, fam, st, "MISSING_DATA", "no section for the band (" + b["state"] + ")")
                risk.append({"KIND": "BAND_" + b["state"], "WHERE": f"{sid}", "DETAIL": cid})
        for m in rec.get("marks", []):
            if m["state"] in ("TAG_UNBOUND", "AMBIGUOUS", "TYPE_NOT_IN_SCHEDULE"):
                risk.append({"KIND": "MARK_" + m["state"], "WHERE": sid, "DETAIL": f"{m['mark']} at "
                                                                                    f"{round(m['x'])},{round(m['y'])}"})
        for h in rec.get("heal", {}).get("extended_wide", []):
            risk.append({"KIND": "HEAL_EXTEND_WIDE", "WHERE": sid,
                         "DETAIL": f"face {h['id']} end extended {h['by'] * u * 1000:.1f} mm to {h['to']}"})
        slab = rec.get("slab")
        if slab:
            sfam = "GROUND_SLAB" if ground else "SLABS"
            for x in slab.get("unenclosed_sides", []):
                risk.append({"KIND": "SLAB_UNENCLOSED_BAND_SIDE", "WHERE": sid,
                             "DETAIL": f"{x['band_id']} side at {round(x['side_mid'][0])},{round(x['side_mid'][1])}: "
                                       f"no closed slab cell although a band lies {x['facing_band_at_m']:.2f} m away"})
            for f in slab["faces"]:
                if f["class"] == "OPEN_BOUNDARY":
                    risk.append({"KIND": "SLAB_OPEN_BOUNDARY_FACE", "WHERE": sid,
                                 "DETAIL": f"{f['face_id']} {f['area_m2']:.2f} m2 (panel leaked into a beam strip)"})
            for f in slab["faces"]:
                if f["class"] != "PANEL":
                    if f["class"] == "OPENING":
                        risk.append({"KIND": "OPENING_DEDUCTED", "WHERE": sid,
                                     "DETAIL": f"{f['face_id']} {f['area_m2']:.2f} m2 {f['opening_labels']}"})
                    continue
                cid = f"{sfam}:{st}:{f['face_id']}"
                common = dict(component_id=cid, trade="CONCRETE", family=sfam, storey=st,
                              source=f"{src_file} {sid} face {f['face_id']} (beam-face bounded)",
                              dimensions={"area_m2": round(f["area_m2"], 4), "t_m": f.get("t_m"),
                                          "t_basis": f.get("t_basis")},
                              double_count_risk="none: the face stops at band faces and column outlines")
                if f.get("t_m"):
                    printed = f["t_basis"] == "PRINTED_IN_PANEL"
                    v = f["volume_m3"]
                    items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=v, base=v, high=v,
                                         formula="face area x thickness",
                                         assumptions=["FROZEN:PRINTED_THICKNESS"] if printed else
                                         ["SLAB_SHEET_UNIFORM_THICKNESS"],
                                         support="SOURCE_COMPLETE_UNREVIEWED" if printed else "CONVENTION_ONLY",
                                         confidence="HIGH" if printed else "MEDIUM", blocker="NOT_REVIEWED",
                                         **common))
                    _slab_bars(items, reg, f, cid, sfam, st, rec["texts"], conv, common["source"])
                else:
                    tl, _, th = _trip(conv, "SLAB_THICKNESS_EXPOSURE_M")
                    items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                                         confidence="LOW", blocker="SLAB_THICKNESS_" + f["t_basis"],
                                         assumptions=["SLAB_THICKNESS_EXPOSURE_M"],
                                         exposure_low=f["area_m2"] * tl, exposure_high=f["area_m2"] * th,
                                         expression=f"{f['area_m2']:.3f} m2 x t (t not printed)", **common))
                    reg(cid, sfam, st, "MISSING_DATA", "slab thickness not established")
                    risk.append({"KIND": "CELL_" + f["t_basis"], "WHERE": sid, "DETAIL": f"{cid} {f['area_m2']:.2f} m2"})
    # ---------------------------------------------------------------- coverage risk: schedule rows never used
    used = set()
    for i in items:
        used.update(re.findall(r"mark (\S+)", i["source"]))
    for r in D["schedule"]["rows"]:
        if r["mark"] not in used and r["family"] in ("FOOTING", "COLUMN", "BEAM", "CONTINUOUS_BEAM", "STRAP_BEAM",
                                                     "GROUND_BEAM"):
            risk.append({"KIND": "SCHEDULE_ROW_NOT_FOUND_ON_PLAN", "WHERE": r["source"], "DETAIL": r["mark"]})
    for sh in D["model"]["sheets"]:
        if sh["role"] == "UNKNOWN":
            risk.append({"KIND": "SHEET_ROLE_UNKNOWN", "WHERE": sh["sheet_id"], "DETAIL": "no title matched"})
    for c in D["schedule"]["conflicts"]:
        risk.append({"KIND": "SCHEDULE_DUPLICATE_MARK", "WHERE": c["family"], "DETAIL": c["mark"]})
    for fam, ev in scope_scan(D).items():
        risk.append({"KIND": "FAMILY_NOT_QUANTIFIED", "WHERE": fam,
                     "DETAIL": f"{ev['n_texts']} labels ({', '.join(ev['keywords'])}) on {', '.join(ev['sheets'])}; "
                               f"the generic engine has no detector for this family - not in any total"})
    return items, register, risk


def _neck_items(items, reg, risk, fsheets, conv, covers, tie_rule, src_file):
    """Foundation necks: every column occurrence on the foundation plan, over the footing it stands on (the footing
    whose outline holds it, else the footing type named in a combined C/F label). Height = neck top level + founding
    depth - that footing's depth, both printed project values (profile: NECK_TOP_LEVEL_M, FOUNDING_DEPTH_M; the
    founding range gives low / high). Section and main bars: the schedule's FOUNDATION band. Without the two printed
    values, or without a footing, a neck is UNRESOLVED with an exposure (NECK_HEIGHT_EXPOSURE_M), never a quantity."""
    have = "FOUNDING_DEPTH_M" in conv.items and "NECK_TOP_LEVEL_M" in conv.items
    for rec in fsheets:
        sid = rec["sheet"]["sheet_id"]
        fts = rec.get("footings", [])
        lib_texts = {}
        for f in fts:
            lib_texts.setdefault(f.get("mark"), []).append(f)
        for o in rec.get("columns", []):
            cid = f"NECK:{o['member_id']}"
            x, y = o["mark_at"]
            p = ((o["box"][0] + o["box"][2]) / 2, (o["box"][1] + o["box"][3]) / 2) if o.get("box") else (x, y)
            host = [f for f in fts if f.get("box") and MD._contains(f["box"], p[0], p[1]) and
                    f["state"] in ("CONFIRMED", "SIZE_MISMATCH", "TYPE_BY_SIZE_MATCH")]
            how = "OUTLINE_HOLDS_THE_COLUMN"
            if not host:                     # a combined C/F label names the footing (same text)
                host = [f for f in fts if f.get("schedule_m") and math.dist(f.get("mark_at", (1e18, 1e18)), (x, y))
                        <= 1e-6 and f["state"] not in ("LABEL_TYPE_CONFLICT_SECONDARY",)]
                how = "COMBINED_LABEL"
            row = o.get("row") or {}
            band = (row.get("by_storey") or {}).get("FOUNDATION")
            sec = (band or {}).get("dims_m", {})
            common = dict(component_id=cid, trade="CONCRETE", family="COLUMNS", storey="FOUNDATION",
                          source=f"{src_file} {sid} mark {o['mark']}; schedule FOUNDATION band; footing "
                                 f"{host[0]['mark'] if host else 'not found'}",
                          dimensions={"section_m": [sec.get("W"), sec.get("H")], "footing": host[0]["member_id"]
                                      if host else None, "footing_binding": how if host else None},
                          double_count_risk="a neck runs from its footing top to the neck top; the column above "
                                            "starts there; beams split at its outline")
            fd = (host[0].get("schedule_m") or [None, None, None])[2] if host else None
            if not (sec.get("W") and sec.get("H")) or fd is None or not have:
                why = ("no FOUNDATION band in the schedule for " + o["mark"]) if not (sec.get("W") and sec.get("H")) \
                    else ("no footing found under the column" if fd is None else
                          "founding depth / neck top level not printed (profile)")
                area = (sec.get("W") or 0) * (sec.get("H") or 0) or (
                    (o["drawn_m"][0] * o["drawn_m"][1]) if o.get("drawn_m") else 0)
                el, _, eh = _trip(conv, "NECK_HEIGHT_EXPOSURE_M") if "NECK_HEIGHT_EXPOSURE_M" in conv.items else \
                    (None, None, None)
                items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                                     confidence="LOW", blocker="NECK_HEIGHT" if (sec.get("W") and fd is not None)
                                     else "NECK_SECTION_OR_FOOTING",
                                     exposure_low=area * el if (area and el) else None,
                                     exposure_high=area * eh if (area and eh) else None,
                                     assumptions=["NECK_HEIGHT_EXPOSURE_M"] if (area and el) else [],
                                     expression=f"section x (neck top + founding depth - footing depth): {why}",
                                     **common))
                reg(cid, "COLUMNS", "FOUNDATION", "MISSING_DATA", why)
                risk.append({"KIND": "NECK_UNRESOLVED", "WHERE": f"{sid} {o['mark']}", "DETAIL": f"{cid}: {why}"})
                continue
            top = conv.base("NECK_TOP_LEVEL_M")
            dl, db, dh = _trip(conv, "FOUNDING_DEPTH_M")
            hs = sorted(top + d - fd for d in (dl, db, dh))
            B, H = sec["W"], sec["H"]
            hb = top + db - fd
            if hb <= 0:
                reg(cid, "COLUMNS", "FOUNDATION", "EXPLICIT_NONE", "footing reaches the neck top")
                continue
            asm = ["NECK_TOP_LEVEL_M", "FOUNDING_DEPTH_M"]
            items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=B * H * hs[0], base=B * H * hb,
                                 high=B * H * hs[-1], formula="section x (neck top + founding depth - footing depth)",
                                 assumptions=asm, support="ONE_ASSUMED_DIMENSION", confidence="MEDIUM",
                                 blocker="FOUNDING_LEVEL", **common))
            main = [b for b in band.get("bars", []) if b.get("count") and b.get("dia_mm")]
            if not main:
                reg(cid, "COLUMNS", "FOUNDATION", "MISSING_DATA", "no main bars in the FOUNDATION band")
                continue
            lap = _trip(conv, "COLUMN_LAP_D")
            tot = 0.0
            for bb in main:
                d = bb["dia_mm"]
                vals = sorted(bb["count"] * BS.mass_kg(h + x * d / 1000.0, d) for h in hs for x in lap)
                base = bb["count"] * BS.mass_kg(hb + lap[1] * d / 1000.0, d)
                items.append(PE.item(item_id=f"P-S:{cid}:MAIN:D{d:g}", component_id=cid, trade="REINFORCEMENT",
                                     family="COLUMNS", storey="FOUNDATION", category="PROVISIONAL", low=vals[0],
                                     base=base, high=vals[-1], dia_mm=d, source=common["source"],
                                     formula="count x (neck height + lap) x d^2/162", assumptions=asm + ["COLUMN_LAP_D"],
                                     support="CONVENTION_ONLY", confidence="MEDIUM", blocker="LAP_ANCHORAGE_RULE"))
                tot += base
            if tie_rule:
                n, d = tie_rule
                lens = []
                for cv in covers["COLUMN"]:
                    try:
                        lens.append(BS.closed_link(B, H, cv, d)["developed_m"])
                    except ValueError:
                        continue
                if lens:
                    lens.sort()
                    v = [n * h * BS.mass_kg(ln, d) for h in hs for ln in lens]
                    base = n * hb * BS.mass_kg(lens[len(lens) // 2], d)
                    items.append(PE.item(item_id=f"P-S:{cid}:TIES:D{d:g}", component_id=cid, trade="REINFORCEMENT",
                                         family="COLUMNS", storey="FOUNDATION", category="PROVISIONAL",
                                         low=min(v), base=base, high=max(v), dia_mm=d, source="printed tie note",
                                         formula="n/m x neck height x closed link x d^2/162",
                                         assumptions=asm + ["REBAR_COVER_COLUMN_M", "REBAR_HOOK_STANDARD"],
                                         support="CONVENTION_ONLY", confidence="MEDIUM", blocker="TIE_LINK_HOOK_RULE"))
                    tot += base
            reg(cid, "COLUMNS", "FOUNDATION", "PROVISIONAL_MODEL", "neck: FOUNDATION band bars" +
                (" + printed tie note" if tie_rule else ""), tot)


def _gb_class(conv, b):
    """Typical ground-beam section by span class (profile table [{max_span_m, W, H}] in ascending order). The band's
    clear length and its length plus one support width give the two length bases. -> {volumes (low, base, high,
    note), classes {basis: class}, basis, lengths} or None."""
    classes = conv["GB_TYPICAL_SECTIONS"].get("classes") or []
    W = b["width_m"]
    sel = [c for c in classes if abs(c["W"] - W) <= 0.015]
    if not sel:
        return None

    def pick(L):
        for c in sorted(sel, key=lambda c: (c.get("max_span_m") is None, c.get("max_span_m") or 0)):
            if c.get("max_span_m") is None or L < c["max_span_m"]:
                return c
        return None
    clear = b["length_m"]
    cc = clear + W                                     # one support width added (centre to centre approximation)
    basis = conv.base("GB_LENGTH_BASIS") if "GB_LENGTH_BASIS" in conv.items else "CLEAR"
    kc, kcc = pick(clear), pick(cc)
    if kc is None or kcc is None:
        return None
    v = {"CLEAR": b["net_plan_m2"] * kc["H"], "CENTRE_TO_CENTRE": b["net_plan_m2"] * kcc["H"]}
    base = v.get(basis, v["CLEAR"])
    return {"volumes": (min(v.values()), base, max(v.values()),
                        f"clear {clear:.2f} m -> H {kc['H']:g}; c/c ~{cc:.2f} m -> H {kcc['H']:g}"),
            "classes": {"CLEAR": kc, "CENTRE_TO_CENTRE": kcc}, "basis": basis if basis in v else "CLEAR",
            "table": classes}


def _gb_exterior(conv, b):
    """the exterior ground-beam depth from printed levels: floor level - build-up - outer ground level (low = lowest
    floor, highest build-up and ground; high the opposite). None unless the profile prints the exterior detail and
    both levels, and the band's width is the detail's."""
    need = ("GB_EXTERIOR_DETAIL", "GF_FLOOR_LEVEL_M", "OUTER_GROUND_LEVEL_M", "GB_EXTERIOR_BUILDUP_M")
    if not all(k in conv.items for k in need):
        return None
    det = conv["GB_EXTERIOR_DETAIL"]
    if det.get("W") and abs(det["W"] - b["width_m"]) > STRAP_WIDTH_TOL_M:
        return None
    f, g, bu = _trip(conv, "GF_FLOOR_LEVEL_M"), _trip(conv, "OUTER_GROUND_LEVEL_M"), _trip(conv, "GB_EXTERIOR_BUILDUP_M")
    d = (f[0] - bu[2] - g[2], f[1] - bu[1] - g[1], f[2] - bu[0] - g[0])
    if d[0] <= 0:
        return None
    return {"depth": d, "detail": det, "assumptions": ["GB_EXTERIOR_CANDIDATE", "GB_EXTERIOR_DETAIL", "GF_FLOOR_LEVEL_M",
                                                       "OUTER_GROUND_LEVEL_M", "GB_EXTERIOR_BUILDUP_M"]}


def _detail_bar_mass(det_bars, L, W, H, cover_trip, conv, hook_std):
    """{(role, dia): (low, base, high)} for one ground-beam detail over a clear length L (section W x H)."""
    anch = _trip(conv, "BEAM_BAR_ANCHORAGE_D")
    side = _cv(conv, "SIDE_BAR_READING", "PRINTED_COUNT")
    out = {}
    for role, rows in det_bars.items():
        for n, d, sp in rows:
            if role == "LINKS":
                vals = []
                for cv in cover_trip:
                    try:
                        ln = BS.closed_link(W, H, cv, d, table=hook_std)["developed_m"]
                    except ValueError:
                        continue
                    vals.append((L / sp + 1) * BS.mass_kg(ln, d))
                if vals:
                    vals.sort()
                    out[(role, d)] = (vals[0], vals[len(vals) // 2], vals[-1])
                continue
            counts = [n]
            if role == "SIDE" and sp:
                each_face = 2 * max(int((H - 2 * cover_trip[1]) / sp - 1e-9), 1)
                counts = sorted({n, each_face})
            base_n = n if role != "SIDE" or side == "PRINTED_COUNT" else counts[-1]
            m = [c * BS.mass_kg(L + 2 * a * d / 1000.0, d) for c in counts for a in anch]
            out[(role, d)] = (min(m), base_n * BS.mass_kg(L + 2 * anch[1] * d / 1000.0, d), max(m))
    return out


def _gb_bars(items, reg, b, cid, fam, st, source, cls, ext, details, cover_trip, conv, hook_std):
    """Typical ground-beam bars from the detail evidence: the detail of the band's class (by span, at each length
    basis; the base basis gives the base, the other the range) or the printed exterior detail. OCR-derived bars are
    PROVISIONAL / LOW / OCR_DERIVED_UNREVIEWED; a role the detail does not show (or whose read was rejected) is an
    UNRESOLVED reinforcement item - never zero."""
    L = b["length_m"]
    if ext is not None:
        det = [d for d in details if d["condition"] == "EXTERIOR"]
        dets = {"BASE": det[0] if len(det) == 1 else None}
        H = {"BASE": ext["depth"][1]}
    else:
        dets = {k: DE.match_class(details, c, cls["table"]) for k, c in cls["classes"].items()}
        H = {k: c["H"] for k, c in cls["classes"].items()}
        base_k = cls["basis"]
        dets, H = {"BASE": dets[base_k], "ALT": dets["CENTRE_TO_CENTRE" if base_k == "CLEAR" else "CLEAR"]}, \
            {"BASE": H[base_k], "ALT": H["CENTRE_TO_CENTRE" if base_k == "CLEAR" else "CLEAR"]}
    d0 = dets["BASE"]
    if d0 is None:
        reg(cid, fam, st, "MISSING_DATA", "typical ground-beam bars not read (no usable detail evidence for the "
                                          + ("exterior detail" if ext is not None else "class") + ")")
        return
    W = b["width_m"]
    m0 = _detail_bar_mass(d0["bars"], L, W, H["BASE"], cover_trip, conv, hook_std)
    m1 = _detail_bar_mass(dets["ALT"]["bars"], L, W, H["ALT"], cover_trip, conv, hook_std) \
        if dets.get("ALT") else {}
    ocr = d0["ocr"] or bool(dets.get("ALT") and dets["ALT"]["ocr"])
    asm = ["BEAM_BAR_ANCHORAGE_D", "REBAR_COVER_BEAM_M", "REBAR_HOOK_STANDARD"] + \
        (["SIDE_BAR_READING"] if "SIDE" in d0["bars"] else []) + \
        (["GB_LENGTH_BASIS"] if dets.get("ALT") and dets["ALT"] is not d0 else [])
    tot = 0.0
    for (role, d), (lo, base, hi) in sorted(m0.items()):
        alt = [v for k, v in m1.items() if k[0] == role]
        lo2 = min([lo] + [a[0] for a in alt])
        hi2 = max([hi] + [a[2] for a in alt])
        items.append(PE.item(item_id=f"P-S:{cid}:{role}:D{d:g}", component_id=cid, trade="REINFORCEMENT", family=fam,
                             storey=st, category="PROVISIONAL", low=lo2, base=base, high=hi2, dia_mm=d,
                             source=f"{source}; typical detail {d0['detail_id']} p.{d0['page']} records "
                                    f"{','.join(d0['records'][:6])}",
                             formula=("(L/s + 1) closed links" if role == "LINKS" else
                                      "count x (clear length + 2 anchorage) x d^2/162"),
                             assumptions=asm, support="CONVENTION_ONLY", confidence="LOW",
                             blocker="OCR_DERIVED_UNREVIEWED" if ocr else "LAP_ANCHORAGE_RULE",
                             limitations=("typical detail read by OCR (vector-glyph checked), not reviewed; "
                                          if ocr else "") + ", ".join(d0["qualifiers"])))
        tot += base
    missing = [r for r in GB_REQUIRED_ROLES if r not in d0["bars"]]
    for r in missing:
        why = "OCR_READ_REJECTED" if d0["rejected_records"] else "ROLE_NOT_PRINTED_IN_DETAIL"
        items.append(PE.item(item_id=f"U-S:{cid}:{r}", component_id=cid, trade="REINFORCEMENT", family=fam, storey=st,
                             category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW", blocker=why,
                             source=f"{source}; typical detail {d0['detail_id']} p.{d0['page']}",
                             expression=f"{r.lower()} of the typical detail: not read" +
                                        (f" (rejected records {','.join(d0['rejected_records'])})"
                                         if d0["rejected_records"] else " (no notation printed in the detail)")))
    reg(cid, fam, st, "PARTIAL_MISSING" if missing else "PROVISIONAL_MODEL",
        ("typical-detail bars (OCR, unreviewed)" if ocr else "typical-detail bars") +
        (f"; missing: {', '.join(missing)}" if missing else ""), tot)


def _footing_bars(f, bars, cover_trip, conv, hook_std):
    if f["state"] == "LABEL_ONLY" and f.get("schedule_m"):
        L, W = sorted(f["schedule_m"][:2], reverse=True)
    else:
        L, W = sorted((f["drawn_m"] if f["state"] != "CONFIRMED" else
                       sorted(f["schedule_m"][:2])), reverse=True)[:2] if f.get("drawn_m") else (None, None)
    if not (L and W):
        return None
    out = defaultdict(lambda: [0.0, 0.0, 0.0])
    any_ok = False
    for b in bars:
        role = (b.get("role") or "").upper()
        d = b.get("dia_mm")
        if not d:
            continue
        if "SH" in role or "SHORT" in role:
            run, dist = W, L
        elif "LO" in role or "LONG" in role:
            run, dist = L, W
        else:
            continue
        n = b.get("count")
        if b.get("per_m"):
            n = (b.get("count") or 0) * dist
        if not n:
            continue
        any_ok = True
        vals = []
        for cv in cover_trip:
            for end in ("STRAIGHT", "HOOKED_90"):
                straight = run - 2 * cv
                ln = straight if end == "STRAIGHT" else BS.hooked(straight, d, ["90", "90"], hook_std)["developed_m"]
                vals.append((cv, end, n * BS.mass_kg(ln, d)))
        base_end = _cv(conv, "FOOTING_BAR_END", "STRAIGHT")
        base = next(v for cv, e, v in vals if e == base_end and abs(cv - cover_trip[1]) < 1e-12)
        out[d][0] += min(v for _, _, v in vals)
        out[d][1] += base
        out[d][2] += max(v for _, _, v in vals)
    if not any_ok:
        return None
    return (sum(v[0] for v in out.values()), sum(v[1] for v in out.values()), sum(v[2] for v in out.values()),
            {d: tuple(v) for d, v in out.items()})


def _beam_bars(items, reg, b, cid, fam, st, source, cover_trip, conv, hook_std):
    bars = b.get("bars") or []
    if b.get("family") == "CONTINUOUS_BEAM" and any(re.search(r"\d", x.get("role") or "") for x in bars):
        reg(cid, fam, st, "MISSING_DATA", "continuous-beam bars are per span; span order of this band not mapped")
        return
    if not bars:
        reg(cid, fam, st, "MISSING_DATA", "no bars in the schedule row")
        return
    L, W, H = b["length_m"], b.get("schedule_width_m") or b["width_m"], b["depth_m"]
    anch = _trip(conv, "BEAM_BAR_ANCHORAGE_D")
    tot = 0.0
    for x in bars:
        d, n = x.get("dia_mm"), x.get("count")
        if not (d and n):
            continue
        role = (x.get("role") or "").upper()
        if role.startswith(LINK_ROLES) and d <= 12:
            vals = []
            for cv in cover_trip:
                try:
                    ln = BS.closed_link(W, H, cv, d, table=hook_std)["developed_m"]
                except ValueError:
                    continue
                vals.append((n * L + 1) * BS.mass_kg(ln, d))
            if not vals:
                continue
            vals.sort()
            items.append(PE.item(item_id=f"P-S:{cid}:{role}:D{d:g}", component_id=cid, trade="REINFORCEMENT",
                                 family=fam, storey=st, category="PROVISIONAL", low=vals[0], base=vals[len(vals) // 2],
                                 high=vals[-1], dia_mm=d, source=source,
                                 formula="(n/m x L + 1) links x closed link (code bends, 135 hooks) x d^2/162",
                                 assumptions=["REBAR_COVER_BEAM_M", "REBAR_HOOK_STANDARD"], support="CONVENTION_ONLY",
                                 confidence="MEDIUM", blocker="TIE_LINK_HOOK_RULE"))
            tot += vals[len(vals) // 2]
        else:
            vals = sorted(n * BS.mass_kg(L + 2 * a * d / 1000.0, d) for a in anch)
            mid = n * BS.mass_kg(L + 2 * anch[1] * d / 1000.0, d)
            items.append(PE.item(item_id=f"P-S:{cid}:{role}:D{d:g}", component_id=cid, trade="REINFORCEMENT",
                                 family=fam, storey=st, category="PROVISIONAL", low=vals[0], base=mid, high=vals[-1],
                                 dia_mm=d, source=source, formula="count x (clear span + 2 anchorage) x d^2/162",
                                 assumptions=["BEAM_BAR_ANCHORAGE_D"], support="CONVENTION_ONLY", confidence="MEDIUM",
                                 blocker="LAP_ANCHORAGE_RULE"))
            tot += mid
    reg(cid, fam, st, "PROVISIONAL_MODEL", "schedule bars over the bound band", tot)


def _slab_bars(items, reg, f, cid, fam, st, texts, conv, source):
    tags = []
    for t in texts:
        if not MD.point_in_poly(t["x"], t["y"], f["polygon"]):
            continue
        b = SG.parse_bar(t["norm"])
        if b.get("grammar") in ("COUNT_DIA_PER_M", "DIA_AT_SPACING", "COUNT_DIA_AT_SPACING") and b.get("dia_mm"):
            n = b.get("count") if b.get("per_m") else (100.0 / b["spacing_cm"] if b.get("spacing_cm") else None)
            if n:
                tags.append((n, b["dia_mm"], "E.W" in t["norm"].upper().replace(" ", "")))
    note_scope = False
    if not tags:
        notes = set()
        for t in texts:
            if "E.W" not in t["norm"].upper().replace(" ", ""):
                continue
            b = SG.parse_bar(t["norm"].upper().replace("E.W.", "").replace("E.W", "").strip())
            if b.get("grammar") == "COUNT_DIA_PER_M" and b.get("dia_mm"):
                notes.add((b["count"], b["dia_mm"], True))
        if len(notes) == 1 and "SLAB_NOTE_MESH_SCOPE" in conv.items:
            tags, note_scope = list(notes), True
    if not tags:
        reg(cid, fam, st, "MISSING_DATA", "no bar tag inside the panel")
        return
    dl, db, dh = _trip(conv, "SLAB_MESH_DIRECTIONS")
    tot = 0.0
    for k, (n, d, ew) in enumerate(sorted(set(tags))):
        one = f["area_m2"] * n * BS.kg_per_m(d)
        lo, b, hi = (2 * one, 2 * one, 2 * one) if ew else (one * dl, one * db, one * (dh if len(set(tags)) == 1 else db))
        items.append(PE.item(item_id=f"P-S:{cid}:MESH{k}:D{d:g}", component_id=cid, trade="REINFORCEMENT", family=fam,
                             storey=st, category="PROVISIONAL", low=lo, base=b, high=hi, dia_mm=d, source=source,
                             formula="panel area x bars per m x directions x d^2/162 (no laps)",
                             assumptions=["SLAB_MESH_DIRECTIONS"] + (["SLAB_NOTE_MESH_SCOPE"] if note_scope else []),
                             support="CONVENTION_ONLY", confidence="LOW", blocker="SLAB_BAR_EXTENTS"))
        tot += b
    reg(cid, fam, st, "PROVISIONAL_MODEL", ("sheet mesh note (E.W.) applied to an untagged panel" if note_scope else
                                            f"{len(set(tags))} bar tag(s) in the panel"), tot)


def policy_record():
    return {"policy": POLICY_ID, "rebar_states": REBAR_STATES,
            "rule": "no project register is loaded; every item names its source entities; a new project is never "
                    "VERIFIED; coverage risk is reported beside unresolved"}
