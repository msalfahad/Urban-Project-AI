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
from engine.source import continuous_beams as CBM
from engine.source import detail_evidence as DE
from engine.source import family_coverage as FC
from engine.source import slab_engine as SE
from engine.source import stair_measure as SM
from engine.source import lintel_measure as LMS

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


def column_boxes(ents, lib, unit_m, tol_m=0.02, layer_evidence=False):
    """layer_evidence (M7): a schedule-sized rectangle is a column only on a layer that shows columns - a layer named
    for columns, or one where at least half its rectangles are column-like (at a scheduled section or holding a
    column mark); a furniture / fixture layer whose odd rectangle matches a section or covers a mark is not"""
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
    per_layer = defaultdict(lambda: [0, 0])               # rectangles, column-like ones
    for r in MD.candidate_rects(ents, unit_m):
        bx = r["box"]
        d = sorted(((bx[2] - bx[0]) * unit_m, (bx[3] - bx[1]) * unit_m))
        fit = any(abs(d[0] - a) <= tol_m and abs(d[1] - b) <= tol_m for a, b in sizes)
        marked = d[1] <= 1.5 and any(MD._contains(bx, m["x"], m["y"]) for m in cmarks)
        st = per_layer[r["layer"]]
        st[0] += 1
        st[1] += fit or marked
        if fit or marked:
            out.append((bx, r["layer"]))
    if layer_evidence:
        ok = {lay for lay, (n, nc) in per_layer.items() if MD._layer_role(lay) == "COLUMN" or nc >= 0.5 * n}
        out = [o for o in out if o[1] in ok]
    out = [o[0] for o in out]
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


def detect_options(conv):
    """M7: the detection behaviour a conventions set switches on (absent conventions -> the frozen M2-M6 behaviour)."""
    on = lambda cid: cid in conv.items                                       # noqa: E731
    return {"frames_from_lines": on("SHEET_FRAMES_FROM_LINES"), "dedupe_texts": on("DUPLICATE_ANNOTATION_READ_ONCE"),
            "junction_gaps": on("SLAB_JUNCTION_GAP_CLOSURE"), "opening_extent": on("SLAB_OPENING_EXTENT_GUARD"),
            "column_by_section": on("COLUMN_OUTLINE_BY_SECTION"),
            "column_layer_evidence": on("COLUMN_LAYER_EVIDENCE"), "treads_per_layer": on("STAIR_TREADS_ONE_LAYER"),
            "local_origin": on("GEOMETRY_LOCAL_ORIGIN")}


def detect(intake, *, typical_widths_m=None, options=None):
    """typical_widths_m: the widths of printed typical ground-beam sections (typical_gb_widths(conv)); when given, or
    when the schedule has ground-beam rows, a ground-beam plan is searched at those widths only and every other drawn
    width mode is recorded as rejected (M3: a slab strip between two faces is not a ground beam).
    options: detect_options(conv) - M7 behaviour switched on by the conventions (None: the frozen behaviour)."""
    opt = options or {}
    M = DM.build(intake, options=opt)
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
    out = {"model": M, "schedule": S, "lib": lib, "unit_m": u, "sheets": {}, "options": dict(sorted(opt.items()))}
    for sh in M["sheets"]:
        E = DM.sheet_entities(M, intake, sh["sheet_id"])
        rec = {"sheet": sh, "n_segments": len(E["segments"])}
        if sh["role"] == "FOUNDATION_PLAN":
            rec["footings"] = MD.footings(sh, E, lib, u)
            rec["columns"] = MD.column_occurrences(sh, E, lib, u, prefer_section=bool(opt.get("column_by_section")))
            rec["straps"] = _straps(E, S, lib, u, rec["footings"])
        elif sh["role"] == "COLUMN_PLAN":
            rec["columns"] = MD.column_occurrences(sh, E, lib, u, prefer_section=bool(opt.get("column_by_section")))
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
            # M3: a layer NAMED for beams joins on any mark it carries (one inclined transfer beam on its own layer is
            # still a beam: B27 on ST7757 GF)
            lays |= {l for l, v in sc.items() if v >= 1 and MD._layer_role(l) == "BEAM"}
            cols = column_boxes(E, lib, u, layer_evidence=bool(opt.get("column_layer_evidence")))
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
            inh = MD.inherit_sections(bands, bound, lib, 1.0 / u, supports=cols + [
                b for b in rec["column_presence"] if not any(max(abs(b[k] - c[k]) for k in range(4)) <= tol
                                                             for c in cols)])
            rec.update(edge_layers=sorted(lays), layer_scores=sc, widths_m=widths_m, width_basis=basis,
                       column_boxes=cols,
                       bands=bands, band_conflicts=conf, marks=bound, inherited=inh)
            # M3: every drawn column outline bounds the slab cells (a column at a size no schedule band prints still
            # closes a cell and owns its footprint); bands are still split at the schedule-sized boxes only
            extra = [b for b in rec["column_presence"] if not any(max(abs(b[k] - c[k]) for k in range(4)) <= tol
                                                                  for c in cols)]
            rec["slab_column_boxes"] = cols + extra
            # M7: band ends around an undrawn support close the cells there (a missing column must not merge bays)
            rec["junction_gaps"] = SE.junction_gaps(bands, cols + extra, u) if (lays and opt.get("junction_gaps")) \
                else []
            slab = SE.panels(E, lays, bands, cols + extra, u, region_id=sh["sheet_id"],
                             junction_boxes=rec["junction_gaps"], opening_extent=bool(opt.get("opening_extent")),
                             local_origin=bool(opt.get("local_origin"))) \
                if lays else None
            SE.classify_regions(slab, E, lays, bands, cols + extra, u, ground=sh["role"] == "GROUND_BEAM_PLAN",
                                treads_per_layer=bool(opt.get("treads_per_layer")))
            rec["slab"] = slab
            rec["band_sides"] = SE.band_sides(slab["faces"], bands, u, cols + extra) if slab else {}
            # M3: an edge beam with one drawn face (the outer face undrawn), from its mark and scheduled width
            sf_b, sf_m = MD.single_face_beams(E, lays, bound, widths_of, bands, slab["faces"] if slab else [], cols, u) \
                if lays else ([], {})
            if sf_b:
                for k, b in enumerate(sf_b, 1):
                    b["band_id"] = f"BANDSF{k:02d}"
                pieces = MD.split_at_supports(sf_b, cols, 0.05 / u)
                for mi, v in sf_m.items():
                    ids = {b["band_id"] for b in v["bands"]}
                    own = [p_["band_id"] for p_ in pieces if p_["parent"] in ids]
                    bound[mi] = dict(bound[mi], state="BOUND_SINGLE_FACE", band=own[0] if own else None, bands=own,
                                     single_face=v["face"])
                bands = bands + pieces
                rec["bands"] = bands
            rec["single_face_bands"] = [b["band_id"] for b in bands if b.get("rule") == "SINGLE_FACE_INFERRED"]
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


def items_from(D, conv, heights=None, evidence=None, arch=None):
    """evidence: a detail-evidence document (engine.source.detail_evidence schema; tools/pdf_evidence.py or a manual
    transcription) - typical ground-beam bars come from it, OCR-derived ones as PROVISIONAL / LOW.
    arch (M4): arch_evidence.gb_exterior(D, architectural intake) - which perimeter ground beams carry an exterior wall
    and the floor level printed inside each."""
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
    pieces = MD.column_storeys(occ, heights)
    contra = "COLUMN_PRESENCE_CONTRADICTION" in conv.items
    order = {s_: k for k, s_ in enumerate(("FOUNDATION",) + STOREY_SEQUENCE)}

    def _present(p_):
        if not (p_["storey"] in slab_cols and p_.get("state") == "MEASURED" and p_.get("box")):
            return None
        o_ = origin_of.get(p_["sheet"], (0.0, 0.0))
        cx_ = (p_["box"][0] + p_["box"][2]) / 2 - o_[0]
        cy_ = (p_["box"][1] + p_["box"][3]) / 2 - o_[1]
        return min(math.hypot(cx_ - a, cy_ - b) for a, b in slab_cols[p_["storey"]]) * u <= 0.25
    seen_above = defaultdict(set)          # M7: occurrence -> the storeys whose plans show it
    if contra:
        for p_ in pieces:
            if _present(p_):
                seen_above[p_["member_id"]].add(p_["storey"])
    for p in pieces:
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
                above = sorted(s_ for s_ in seen_above.get(p["member_id"], ()) if order.get(s_, 0) > order.get(st, 0))
                if near > 0.25 and contra and (above or not seen_above.get(p["member_id"])):
                    # M7: absent on this plan but shown above (a column cannot stand on nothing), or absent on every
                    # plan (the mark was bound to another outline): a contradiction, held unresolved - never dropped
                    B_, H_ = p["section_m"]
                    v_ = B_ * H_ * (p["height_m"] or 0.0)
                    why = (f"shown on the {', '.join(above)} plan(s) above" if above else
                           "shown on no storey plan at the position of its bound outline")
                    items.append(PE.item(item_id=f"U-C:{cid}", component_id=cid, trade="CONCRETE", family="COLUMNS",
                                         storey=st, category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                                         blocker="COLUMN_PRESENCE_CONTRADICTION", exposure_low=0.0, exposure_high=v_,
                                         source=f"{src_file} {p['sheet']} mark {p['mark']}; schedule storey band {st}",
                                         dimensions={"section_m": p.get("section_m"), "height_m": p.get("height_m"),
                                                     "nearest_outline_m": round(near, 3)},
                                         expression=f"0 .. {B_:g} x {H_:g} x {p['height_m']:g}: no column outline on "
                                                    f"the {st} plan here although the column is {why}"))
                    reg(cid, "COLUMNS", st, "MISSING_DATA", f"column presence contradiction ({why})")
                    risk.append({"KIND": "COLUMN_PRESENCE_CONTRADICTION", "WHERE": f"{st} {p['mark']}",
                                 "DETAIL": f"{cid}: no outline on the {st} roof-slab plan (nearest {near:.2f} m) but "
                                           f"{why}; held unresolved"})
                    continue
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

    # ---------------------------------------------------------------- M5: planted columns labelled on slab plans
    if "PLANTED_COLUMN_LABELS" in conv.items:
        _planted_column_items(D, items, reg, risk, conv, heights, occ, src_file, u)

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
        cbm = _cb_model(D, rec, conv, covers["BEAM"], hook_std) if not ground and "CB_SPAN_MATCH_TOL_M" in \
            conv.items else None
        rec["cb_lines"] = cbm["lines"] if cbm else []
        slab_t = (rec.get("slab") or {}).get("uniform_t_m")
        for b in rec["beams"]:
            ev = (cbm or {}).get("band", {}).get(b["band_id"])
            if ev and ev["inherited"]:
                # M4: a span of a matched continuous-beam line (printed span sequence) takes the mark
                row = lib.get(("CONTINUOUS_BEAM", ev["mark"]))
                H = (row or {}).get("dims_m", {}).get("H")
                if b["state"] == "UNBOUND" and H:
                    b = dict(b, state="BOUND", mark=ev["mark"], family="CONTINUOUS_BEAM", depth_m=H,
                             schedule_width_m=row["dims_m"].get("W"), bars=row.get("bars", []),
                             schedule_source=row["source"], binding="INHERITED_BY_SPAN_SEQUENCE",
                             v_total_depth=b["net_plan_m2"] * H,
                             v_below_slab=b["net_plan_m2"] * (H + slab_t) if slab_t is not None else None)
                elif "INHERITED" in (b.get("binding") or ""):
                    b = dict(b, binding="INHERITED_BY_SPAN_SEQUENCE")
            cid = f"{fam}:{st}:{b['band_id']}"
            common = dict(component_id=cid, trade="CONCRETE", family=fam, storey=st,
                          source=f"{src_file} {sid} band faces {','.join(map(str, b['handles'][:2]))}"
                                 + (f"; mark {b.get('mark')} ({b.get('binding')})" if b.get("mark") else ""),
                          dimensions={"width_m": round(b["width_m"], 4), "length_m": round(b["length_m"], 4),
                                      "net_plan_m2": round(b["net_plan_m2"], 5), "depth_m": b.get("depth_m"),
                                      "junction_deductions": len(b.get("junction_deductions", []))},
                          double_count_risk="column footprint split out; junction squares owned by one band; slab "
                                            "panels stop at band faces")
            if b["state"] == "BOUND" and b.get("depth_m") and "SINGLE_FACE" in (b.get("binding") or ""):
                A, Bv = b["v_total_depth"], b.get("v_below_slab")
                lo, base, hi = PE.by_choice(conv, "BEAM_DEPTH_READING", {"TOTAL_DEPTH": A, "BELOW_SLAB": Bv if Bv
                                                                          is not None else A})
                items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=lo, base=base, high=hi,
                                     formula="drawn face length x scheduled width x H (the opposite face is not "
                                             "drawn: placed at the scheduled width toward the mark)",
                                     assumptions=["BEAM_DEPTH_READING"], support="ONE_ASSUMED_DIMENSION",
                                     confidence="LOW", blocker="SINGLE_FACE_BEAM", **common))
                _beam_bars(items, reg, b, cid, fam, st, common["source"], covers["BEAM"], conv, hook_std)
                risk.append({"KIND": "BEAM_SINGLE_FACE_INFERRED", "WHERE": sid,
                             "DETAIL": f"{cid} {b.get('mark')}: one face drawn; the second placed at the scheduled "
                                       f"width {b['width_m']:.2f} m"})
            elif b["state"] == "BOUND" and b.get("depth_m"):
                inh = "INHERITED" in (b.get("binding") or "")
                if inh and _cv(conv, "COLLINEAR_INHERITANCE") == "OFF":
                    items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                                         confidence="LOW", blocker="UNTAGGED_SPAN", expression="B x H x L (no tag)",
                                         **common))
                    reg(cid, fam, st, "MISSING_DATA", "untagged span")
                    continue
                if inh and _cv(conv, "COLLINEAR_INHERITANCE") == "SPAN_EVIDENCE_ONLY" and \
                        b.get("binding") != "INHERITED_BY_SPAN_SEQUENCE":
                    # M4: alignment alone never carries a section across a support; the neighbour's section is an
                    # alternative, the schedule depths at the drawn width the exposure
                    rows_w = [r["dims_m"]["H"] for r in D["schedule"]["rows"] if r["family"] in MD.BEAM_FAMILIES and
                              r["dims_m"].get("W") and abs(r["dims_m"]["W"] - b["width_m"]) <= 0.015 and
                              r["dims_m"].get("H")]
                    hl, hh = (min(rows_w), max(rows_w)) if rows_w else (b["depth_m"], b["depth_m"])
                    alt = b["v_total_depth"]
                    common["dimensions"].update(alternative_as_neighbour_m3=round(alt, 4),
                                                neighbour_mark=b.get("mark"))
                    items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                                         confidence="LOW", blocker="UNLABELLED_SPAN_ACROSS_SUPPORT",
                                         assumptions=["COLLINEAR_INHERITANCE"],
                                         exposure_low=b["net_plan_m2"] * min(hl, b["depth_m"]),
                                         exposure_high=b["net_plan_m2"] * max(hh, b["depth_m"]),
                                         expression=f"{b['net_plan_m2']:.3f} m2 x H: no label on this span; the "
                                                    f"collinear {b.get('mark')} across the support gives "
                                                    f"{alt:.3f} m3 (alternative), the schedule depths at "
                                                    f"{b['width_m']:.2f} m give {hl:g} - {hh:g} m", **common))
                    reg(cid, fam, st, "MISSING_DATA", f"unlabelled span across a support (the collinear "
                                                      f"{b.get('mark')} is not evidence of its section)")
                    risk.append({"KIND": "BEAM_UNLABELLED_SPAN_ACROSS_SUPPORT", "WHERE": sid,
                                 "DETAIL": f"{cid}: collinear with {b.get('mark')} across a support, no label, no "
                                           f"printed span sequence (alternative {alt:.3f} m3)"})
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
                if b.get("binding") == "INHERITED_BY_SPAN_SEQUENCE":
                    asm = [a for a in asm if a != "COLLINEAR_INHERITANCE"] + ["CB_SPAN_MATCH_TOL_M"]
                    conf = "MEDIUM" if conf == "LOW" and "WIDTH_CONFLICT" not in (b.get("binding") or "") else conf
                items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=lo, base=base, high=hi,
                                     formula="net plan (B x L - column - junction) x H  |  x (H + t)",
                                     assumptions=asm, support="CONVENTION_ONLY", confidence=conf, blocker=blk,
                                     **common))
                if cbm is not None and b.get("family") == "CONTINUOUS_BEAM":
                    _cb_bars(items, reg, b, cid, fam, st, common["source"], cbm)
                else:
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
                ext_mode = _cv(conv, "GB_EXTERIOR_EVIDENCE", "PERIMETER")
                av = ((arch or {}).get("bands") or {}).get(b["band_id"]) if ext_mode != "PERIMETER" else None
                acls = (av or {}).get("class", "NOT_REGISTERED")
                if ext_mode != "PERIMETER" and "OUTSIDE" in sides:
                    common["dimensions"].update(arch_class=acls, wall_cover=(av or {}).get("wall_cover"),
                                                arch_floor_level_m=(av or {}).get("floor_level_m"))
                ext = _gb_exterior(conv, b, (av or {}).get("floor_level_m"), m4=ext_mode != "PERIMETER") \
                    if "OUTSIDE" in sides else None
                ext_case = None                       # M4: EVIDENCED / CANDIDATE / NO_WALL / SHALLOWER / NONE
                if ext is not None and ext_mode != "PERIMETER":
                    cls_h = cls["classes"][cls["basis"]]["H"]
                    if acls == "PERIMETER_NO_WALL":
                        ext_case = "NO_WALL"
                    elif acls != "EXTERIOR_WALL":
                        ext_case = "CANDIDATE"
                    elif ext.get("none") or ext["depth"][1] <= cls_h:
                        ext_case = "SHALLOWER"
                    else:
                        ext_case = "EVIDENCED"
                    if ext_case in ("NO_WALL",) or ext.get("none"):
                        if ext_case == "SHALLOWER":
                            risk.append({"KIND": "GB_EXTERIOR_SHALLOWER_THAN_CLASS", "WHERE": sid,
                                         "DETAIL": f"{cid}: exterior wall on the band, but the printed floor level "
                                                   f"{ext.get('floor_m')} gives no depth below it - class section"})
                        ext = None
                    elif ext_case == "SHALLOWER":
                        risk.append({"KIND": "GB_EXTERIOR_SHALLOWER_THAN_CLASS", "WHERE": sid,
                                     "DETAIL": f"{cid}: exterior wall on the band; floor level {ext['floor_m']:.2f} "
                                               f"gives an exterior depth {ext['depth'][1]:.2f} m, not deeper than the "
                                               f"class section {cls_h:.2f} m - source conflict, class section as base"})
                if ext_case == "NO_WALL":
                    risk.append({"KIND": "GB_PERIMETER_NO_WALL", "WHERE": sid,
                                 "DETAIL": f"{cid}: perimeter band with no wall drawn on it in the architectural plan "
                                           "- the exterior detail ('for exterior walls') does not apply; class section"})
                if "OUTSIDE" in sides and ext is None and ext_case is None:
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
                    if ext_case is not None:
                        exterior = ext_case == "EVIDENCED"
                    if ext_case != "SHALLOWER":           # a conflicting exterior reading never sets the range
                        lo, hi = min(lo, e_lo), max(hi, e_hi)
                    base = e_b if exterior else base
                    asm += ext["assumptions"]
                    formula = ("perimeter band (one side on the outside of the ground-beam network): net plan x "
                               "(floor level - build-up - outer ground level), the printed exterior detail; the typical"
                               " class section gives the low end")
                    blk = "GB_EXTERIOR_DEPTH"
                    if ext_case == "CANDIDATE":
                        formula = ("perimeter band, no architectural wall evidence: the typical class section is the "
                                   "base; the printed exterior detail (floor level - build-up - outer ground) is the "
                                   "high alternative")
                        blk = "GB_EXTERIOR_NOT_EVIDENCED"
                    elif ext_case == "SHALLOWER":
                        formula = ("exterior wall on the band (architectural plan), but the exterior depth from the "
                                   "printed floor level is not deeper than the class section: the class section (source "
                                   "conflict, RFI)")
                        blk = "GB_EXTERIOR_LEVEL_CONFLICT"
                    elif ext_case == "EVIDENCED":
                        asm = asm + ["GB_EXTERIOR_EVIDENCE"]
                        formula = ("exterior wall on the band (architectural plan, wall cover "
                                   f"{(av or {}).get('wall_cover')}): net plan x (floor level "
                                   f"{ext['floor_m']:.2f} - build-up - outer ground level), the printed exterior "
                                   "detail; the class section gives the low end")
                    note += f"; exterior depth {ext['depth'][1]:.2f} m ({ext['depth'][0]:.2f} - {ext['depth'][2]:.2f})"
                    H_bars = ext["depth"][1] if exterior else None
                    if ext_case == "SHALLOWER":            # the exterior detail's bars govern ('for exterior walls'),
                        H_bars = cls["classes"][cls["basis"]]["H"]   # at the class depth the concrete takes
                        ext = dict(ext, depth=(H_bars, H_bars, H_bars))
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
                cbx = (cbm or {}).get("steel", {}).get(b["band_id"])
                if cbx:
                    # M4: a span the printed sequence of a continuous beam maps, but whose section is unresolved (two
                    # marks on it): the bars the line allocates to it are held as exposure, never dropped
                    kg = [0.0, 0.0]
                    for (role, d), (lo, mid, hi) in sorted(cbx["values"].items()):
                        if hi <= 0:
                            continue
                        kg = [kg[0] + lo, kg[1] + hi]
                        items.append(PE.item(item_id=f"U-S:{cid}:CB_{role}:D{d:g}", component_id=cid,
                                             trade="REINFORCEMENT", family=fam, storey=st, category="UNRESOLVED",
                                             support="NO_GEOMETRY", confidence="LOW",
                                             blocker="CB_SPAN_SECTION_UNRESOLVED", dia_mm=d,
                                             exposure_low=lo, exposure_high=hi,
                                             dimensions={"allocated_kg_base": round(mid, 6)},
                                             source=f"{common['source']}; continuous-beam line {cbx['line']}",
                                             expression=f"{role.lower()} bars the line {cbx['line']} allocates to this "
                                                        f"span; the band's section is unresolved ({b['state']})"))
                    risk.append({"KIND": "CB_SPAN_MARK_CONFLICT", "WHERE": sid,
                                 "DETAIL": f"{cid}: the printed span sequence of line {cbx['line']} maps this band, "
                                           f"which also carries {', '.join(b.get('marks') or [])} - section "
                                           f"unresolved; its line bars {kg[0]:.1f} - {kg[1]:.1f} kg held as exposure"})
                reg(cid, fam, st, "MISSING_DATA", "no section for the band (" + b["state"] + ")" +
                    ("; continuous-beam bars held as exposure" if cbx else ""))
                risk.append({"KIND": "BAND_" + b["state"], "WHERE": f"{sid}", "DETAIL": cid})
        for m in rec.get("marks", []):
            if m["state"] in ("TAG_UNBOUND", "AMBIGUOUS", "TYPE_NOT_IN_SCHEDULE"):
                risk.append({"KIND": "MARK_" + m["state"], "WHERE": sid, "DETAIL": f"{m['mark']} at "
                                                                                    f"{round(m['x'])},{round(m['y'])}"})
        for h in rec.get("heal", {}).get("extended_wide", []):
            risk.append({"KIND": "HEAL_EXTEND_WIDE", "WHERE": sid,
                         "DETAIL": f"face {h['id']} end extended {h['by'] * u * 1000:.1f} mm to {h['to']}"})
        slab = rec.get("slab")
        if slab and "SLAB_DEDUCT_MEMBER_OVERLAP" in conv.items:
            _slab_m4(slab, rec, u, conv, ground, risk, sid)
        if slab:
            sfam = "GROUND_SLAB" if ground else "SLABS"
            for x in slab.get("unenclosed_sides", []):
                risk.append({"KIND": "SLAB_UNENCLOSED_BAND_SIDE", "WHERE": sid,
                             "DETAIL": f"{x['band_id']} side at {round(x['side_mid'][0])},{round(x['side_mid'][1])}: "
                                       f"no closed slab cell although a band lies {x['facing_band_at_m']:.2f} m away"})
            for f in slab["faces"]:
                if f["class"] == "OPEN_BOUNDARY":
                    risk.append({"KIND": "SLAB_OPEN_BOUNDARY_FACE", "WHERE": sid,
                                 "DETAIL": f"{f['face_id']} {f['area_m2']:.2f} m2 (panel leaked into a beam strip; "
                                           f"{f.get('recovered_panel_m2', 0):.2f} m2 recovered as panel = face - "
                                           "beam bands - columns)"})
            for f in slab["faces"]:
                if f["class"] == "OPEN_BOUNDARY" and f.get("region") in ("STRUCTURAL_SLAB", "GROUND_SLAB"):
                    cid = f"{sfam}:{st}:{f['face_id']}"
                    A = f["recovered_panel_m2"]
                    common = dict(component_id=cid, trade="CONCRETE", family=sfam, storey=st,
                                  source=f"{src_file} {sid} face {f['face_id']} (open boundary, beam bands subtracted)",
                                  dimensions={"area_m2": round(A, 4), "face_area_m2": round(f["area_m2"], 4),
                                              "t_m": f.get("t_m"), "t_basis": f.get("t_basis"),
                                              "region": f["region"]},
                                  double_count_risk="the beam bands and column outlines inside the face are "
                                                    "subtracted (they are the beams' and columns')")
                    if f.get("t_m"):
                        v = A * f["t_m"]
                        items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=v, base=v, high=v,
                                             formula="(face area - beam bands - columns) x thickness",
                                             assumptions=["FROZEN:PRINTED_THICKNESS"] if f["t_basis"] ==
                                             "PRINTED_IN_PANEL" else ["SLAB_SHEET_UNIFORM_THICKNESS"],
                                             support="CONVENTION_ONLY", confidence="LOW",
                                             blocker="OPEN_BOUNDARY_RECOVERED", **common))
                        reg(cid, sfam, st, "MISSING_DATA", "panel recovered from an open-boundary face: the bar tags "
                                                           "of the leaked cells cannot be assigned to one panel")
                    else:
                        tl, _, th = _trip(conv, "SLAB_THICKNESS_EXPOSURE_M")
                        items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                                             confidence="LOW", blocker="SLAB_THICKNESS_" + f["t_basis"],
                                             assumptions=["SLAB_THICKNESS_EXPOSURE_M"], exposure_low=A * tl,
                                             exposure_high=A * th, expression=f"{A:.3f} m2 x t", **common))
                        reg(cid, sfam, st, "MISSING_DATA", "slab thickness not established")
                    continue
                if f["class"] == "OPENING_SUSPECT":
                    # M7: a void label in a face that holds a beam band - bays merged through a gap. Neither slab nor
                    # opening: its slab part (face - bands - columns) is held as exposure, never deleted
                    A = SE.open_boundary_panel(f, rec.get("bands", []), rec.get("slab_column_boxes", []), u)
                    cid = f"{sfam}:{st}:{f['face_id']}"
                    tl, _, th = _trip(conv, "SLAB_THICKNESS_EXPOSURE_M")
                    t_ = (slab.get("uniform_t_m") or _cv(conv, "SLAB_PROJECT_DEFAULT_THICKNESS_M")) if not ground \
                        else None
                    lo_t, hi_t = (t_, t_) if t_ else (tl, th)
                    items.append(PE.item(item_id=f"U-C:{cid}", component_id=cid, trade="CONCRETE", family=sfam,
                                         storey=st, category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                                         blocker="SLAB_OPENING_EXTENT_UNKNOWN",
                                         assumptions=[] if t_ else ["SLAB_THICKNESS_EXPOSURE_M"],
                                         exposure_low=0.0, exposure_high=A * hi_t,
                                         source=f"{src_file} {sid} face {f['face_id']} (void label in a face that "
                                                f"holds beam bands)",
                                         dimensions={"area_m2": round(A, 4), "face_area_m2": round(f["area_m2"], 4),
                                                     "t_m": t_, "region": f.get("region"),
                                                     "opening_labels": f.get("opening_labels")},
                                         expression=f"0 .. {A:.3f} m2 x t: the void's extent is not drawn (its label "
                                                    "lies in cells merged through a gap)",
                                         double_count_risk="not counted: neither slab nor opening until the void's "
                                                           "extent is confirmed"))
                    reg(cid, sfam, st, "MISSING_DATA", "slab region whose opening extent is unknown")
                    risk.append({"KIND": "SLAB_OPENING_EXTENT_UNKNOWN", "WHERE": sid,
                                 "DETAIL": f"{cid} {f['area_m2']:.2f} m2 face ({A:.2f} m2 net of members) holds a "
                                           f"void label {f.get('opening_labels')} and beam bands: cells merged through "
                                           "a gap - the void's extent is not established"})
                    continue
                if f["class"] == "JUNCTION_GAP":
                    risk.append({"KIND": "SLAB_JUNCTION_GAP", "WHERE": sid,
                                 "DETAIL": f"{f['face_id']} {f['area_m2']:.3f} m2: band ends around an undrawn support "
                                           "closed the cells; the junction itself is in no item (confirm the support)"})
                    continue
                if f["class"] != "PANEL":
                    if f["class"] == "OPENING":
                        risk.append({"KIND": "OPENING_DEDUCTED", "WHERE": sid,
                                     "DETAIL": f"{f['face_id']} {f['area_m2']:.2f} m2 {f['opening_labels']}"})
                    continue
                cid = f"{sfam}:{st}:{f['face_id']}"
                if f.get("free_columns") and f.get("region") != "UNRESOLVED":
                    risk.append({"KIND": "SLAB_PANEL_FREE_COLUMN", "WHERE": sid,
                                 "DETAIL": f"{cid} {f['area_m2']:.2f} m2 holds {len(f['free_columns'])} column(s) on "
                                           "no beam (a flat-slab zone; counted)"})
                if f.get("treads") and f.get("region") != "STAIR_ZONE":
                    hull = min(f["treads"].get("hull_m2") or 0.0, f["area_m2"])
                    held = "SLAB_STAIR_FOOTPRINT_UNRESOLVED" in conv.items and hull > 0.0 and f.get("t_m")
                    risk.append({"KIND": "SLAB_PANEL_STAIR_LINES", "WHERE": sid,
                                 "DETAIL": f"{cid} {f['area_m2']:.2f} m2: {f['treads']['kind']} of "
                                           f"{f['treads']['n']} tread lines over part of the cell " +
                                           (f"(the flight's {hull:.2f} m2 held unresolved, the rest counted)" if held
                                            else "(counted)")})
                    if held:
                        # M7: a flight drawn inside a slab panel is a possible void of at least its footprint: that
                        # part is neither counted nor dropped, it is held as exposure (0 .. footprint x t)
                        f["area_before_stair_m2"] = f["area_m2"]
                        f["area_m2"] = f["area_m2"] - hull
                        f["volume_m3"] = f["area_m2"] * f["t_m"]
                        items.append(PE.item(item_id=f"U-C:{cid}:STAIR_FOOTPRINT", component_id=cid + ":STAIR",
                                             trade="CONCRETE", family=sfam, storey=st, category="UNRESOLVED",
                                             support="NO_GEOMETRY", confidence="LOW",
                                             blocker="SLAB_STAIR_FOOTPRINT_UNRESOLVED", exposure_low=0.0,
                                             exposure_high=hull * f["t_m"],
                                             source=f"{src_file} {sid} face {f['face_id']} (tread lines)",
                                             dimensions={"area_m2": round(hull, 4), "t_m": f["t_m"],
                                                         "treads": f["treads"]["n"]},
                                             expression=f"0 .. {hull:.3f} m2 x {f['t_m']:g}: slab or stair void "
                                                        "under a drawn flight (not decided by the drawing)",
                                             double_count_risk="deducted from the panel item of the same face"))
                if f.get("region") == "STAIR_ZONE" and "STAIR_RISER_RULE" in conv.items and \
                        _stair_items(items, reg, risk, f, sid, st, ground, conv, u, src_file):
                    continue
                if f.get("region") in ("STAIR_ZONE", "UNRESOLVED"):
                    tl, _, th = _trip(conv, "SLAB_THICKNESS_EXPOSURE_M")
                    t_ = f.get("t_m")
                    lo_t, hi_t = (t_, t_) if t_ else (tl, th)
                    common = dict(component_id=cid, trade="CONCRETE", family=sfam, storey=st,
                                  source=f"{src_file} {sid} face {f['face_id']} (beam-face bounded)",
                                  dimensions={"area_m2": round(f["area_m2"], 4), "t_m": t_, "region": f["region"],
                                              "free_columns": len(f.get("free_columns") or [])},
                                  double_count_risk="not counted: the cell is a stair zone or holds free-standing "
                                                    "columns")
                    kind = "SLAB_STAIR_ZONE" if f["region"] == "STAIR_ZONE" else "SLAB_CELL_FREE_COLUMNS"
                    items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                                         confidence="LOW", blocker=kind,
                                         assumptions=[] if t_ else ["SLAB_THICKNESS_EXPOSURE_M"],
                                         exposure_low=f["area_m2"] * lo_t, exposure_high=f["area_m2"] * hi_t,
                                         expression=f"{f['area_m2']:.3f} m2 x t: {f['region_reason']}", **common))
                    reg(cid, sfam, st, "MISSING_DATA", f"{f['region'].lower()} cell not counted as slab "
                                                       f"({f['region_reason']})")
                    risk.append({"KIND": kind, "WHERE": sid, "DETAIL": f"{cid} {f['area_m2']:.2f} m2: "
                                                                      f"{f['region_reason']}"})
                    continue
                common = dict(component_id=cid, trade="CONCRETE", family=sfam, storey=st,
                              source=f"{src_file} {sid} face {f['face_id']} (beam-face bounded)",
                              dimensions={"area_m2": round(f["area_m2"], 4), "t_m": f.get("t_m"),
                                          "t_basis": f.get("t_basis")},
                              double_count_risk="none: the face stops at band faces and column outlines")
                if f.get("t_m"):
                    printed = f["t_basis"] == "PRINTED_IN_PANEL"
                    v = f["volume_m3"]
                    if f.get("member_overlap_m2"):
                        common["dimensions"].update(area_gross_m2=round(f["area_gross_m2"], 4),
                                                    member_overlap_deducted_m2=round(f["member_overlap_m2"], 4))
                    items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=v, base=v, high=v,
                                         formula="face area (members' overlap deducted) x thickness",
                                         assumptions=["FROZEN:PRINTED_THICKNESS"] if printed else
                                         (["SLAB_PROJECT_DEFAULT_THICKNESS_M"] if f["t_basis"] == "PROJECT_DEFAULT"
                                          else ["SLAB_SHEET_UNIFORM_THICKNESS"]),
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
    _blinding_items(D, items, reg, risk, conv, src_file)
    if arch and arch.get("lintels") and "LINTEL_SCHEDULE" in conv.items:
        _lintel_items(items, reg, risk, arch["lintels"], conv, covers["BEAM"], hook_std)
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
    scan = scope_scan(D)
    for c in FC.coverage(D, items, risk, scan, evidence):       # M3: precise coverage, never "absent"
        if c["STATE"] in ("DETECTED_NOT_QUANTIFIED", "PARTLY_QUANTIFIED"):
            risk.append({"KIND": "FAMILY_NOT_QUANTIFIED" if c["STATE"] == "DETECTED_NOT_QUANTIFIED" else
                         "FAMILY_PARTLY_QUANTIFIED", "WHERE": c["FAMILY"],
                         "DETAIL": f"{c['EVIDENCE']}; {c['REASON']}; needs {c['NEEDED']} - not in any total"})
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


def _blinding_items(D, items, reg, risk, conv, src_file):
    """M3 plain-concrete blinding (family PLAIN_CONCRETE): under every quantified footing, (L + 2p)(W + 2p) x t, and
    under ground and strap beams when BLINDING_UNDER says so, (net plan + 2p x clear length) x t. t is a printed
    value (profile BLINDING_THICKNESS_M); without it the blinding is UNRESOLVED with an exposure only. The projection
    p is a named convention. No reinforcement (EXPLICIT_NONE)."""
    p_ = _trip(conv, "BLINDING_PROJECTION_M") if "BLINDING_PROJECTION_M" in conv.items else None
    if p_ is None:
        return
    t_ = _trip(conv, "BLINDING_THICKNESS_M") if "BLINDING_THICKNESS_M" in conv.items else None
    under = _cv(conv, "BLINDING_UNDER", "FOOTINGS_ONLY")
    foot, foot_box, strips, strip_rec, n_f, n_s, skipped = [], [], [], [], 0, 0, 0
    for sid, rec in sorted(D["sheets"].items()):
        for f in rec.get("footings", []):
            dims = None
            if f["state"] == "LABEL_TYPE_CONFLICT" and f.get("candidates"):
                # one footing, two labelled types: the type the concrete item takes as base (FOOTING_LABEL_CONFLICT)
                sizes = sorted((c["schedule_m"] for c in f["candidates"].values() if c.get("schedule_m")),
                               key=lambda d: d[0] * d[1])
                if sizes:
                    dims = (sizes[0] if _cv(conv, "FOOTING_LABEL_CONFLICT", "LARGER") == "SMALLER" else sizes[-1])[:2]
            elif f["state"] in ("LABEL_ONLY", "LABEL_TYPE_CONFLICT") and f.get("schedule_m"):
                dims = f["schedule_m"][:2]
            elif f["state"] not in ("LABEL_TYPE_CONFLICT_SECONDARY", "NESTED_OR_DUPLICATE_OUTLINE", "NO_OUTLINE") and \
                    f.get("drawn_m"):
                dims = f["drawn_m"][:2]
            elif f["state"] not in ("LABEL_TYPE_CONFLICT_SECONDARY", "NESTED_OR_DUPLICATE_OUTLINE"):
                skipped += 1
            if dims:
                foot.append(dims)
                n_f += 1
                # M4: a drawn outline places the footing (its blinding can overlap a neighbour's or a beam strip's)
                foot_box.append(f["box"] if f.get("box") and f.get("drawn_m") and dims == f["drawn_m"][:2] and
                                rec["sheet"]["role"] == "FOUNDATION_PLAN" else None)
        if rec["sheet"]["role"] == "GROUND_BEAM_PLAN":
            bpoly = {x["band_id"]: x for x in rec.get("bands", [])}
            for b in rec.get("beams", []):
                strips.append((b["net_plan_m2"], b["length_m"], bpoly.get(b["band_id"]), sid))
                strip_rec.append(b)
                n_s += 1
        for b in (rec.get("straps") or {}).get("bands", []):
            strips.append((b["net_plan_m2"], b["length_m"], b if b.get("u") else None, sid))
            strip_rec.append(b)
            n_s += 1
    fA = [sum((L + 2 * p) * (W + 2 * p) for L, W in foot) for p in p_]
    sA = [sum(s[0] + 2 * p * s[1] for s in strips) for p in p_]
    overlap = None
    if "BLINDING_OVERLAP" in conv.items and under == "FOOTINGS_AND_GROUND_BEAMS":
        overlap = _blinding_union(D, foot, foot_box, strips, strip_rec, p_)   # M4: each square metre once
        D["blinding_overlap"] = overlap                  # kept for the visual QA (registration shift per sheet)
        if overlap and overlap["state"] == "REGISTERED":
            fA, sA = list(overlap["footings_m2"]), list(overlap["beams_m2"])
            risk.append({"KIND": "BLINDING_OVERLAP_DEDUCTED", "WHERE": "FOUNDATION",
                         "DETAIL": f"blinding plan = union of the footing and beam-strip outlines: "
                                   f"{overlap['area_m2'][1]:.2f} m2 of beam strip on footing blinding, "
                                   f"{overlap['strip_strip_m2'][1]:.2f} m2 where strips cross, "
                                   f"{overlap['footing_footing_m2'][1]:.2f} m2 where footing projections meet, each "
                                   f"counted once ({overlap['strips_over_footings']} strips; plans registered on "
                                   f"{overlap['matched']} footings; {overlap['free_strips']} strips and "
                                   f"{overlap['free_footings']} footings without a placed outline added whole)"})
        elif overlap:
            risk.append({"KIND": "BLINDING_OVERLAP_NOT_ESTABLISHED", "WHERE": "FOUNDATION",
                         "DETAIL": f"the ground-beam and foundation plans could not be registered ({overlap['state']}):"
                                   " the beam blinding over footings may be counted twice"})
    parts = [("FOOTINGS", fA, n_f, "(L + 2p)(W + 2p) x t under each footing")]
    if under == "FOOTINGS_AND_GROUND_BEAMS":
        parts.append(("GROUND_BEAMS", sA, n_s, "(net plan + 2p x clear length) x t under each ground / strap beam"))
    elif strips:
        risk.append({"KIND": "BLINDING_UNDER_BEAMS_NOT_ESTABLISHED", "WHERE": "FOUNDATION",
                     "DETAIL": f"{n_s} ground / strap beams: blinding under them only when the typical detail shows it "
                               "(BLINDING_UNDER)"})
    for name, A, n, formula in parts:
        if not n:
            continue
        cid = f"PLAIN_CONCRETE:FOUNDATION:BLINDING_{name}"
        common = dict(component_id=cid, trade="CONCRETE", family="PLAIN_CONCRETE", storey="FOUNDATION",
                      source=f"{src_file}: {n} {name.lower().replace('_', ' ')} quantified on the plans",
                      dimensions={"members": n, "plan_m2_base": round(A[1], 3)} | (
                          {"overlap_with_footing_blinding_m2": round(overlap["area_m2"][1], 3)}
                          if name == "GROUND_BEAMS" and overlap and overlap["state"] == "REGISTERED" else {}),
                      double_count_risk="beam blinding stops at the footing faces (the clear length); the projection "
                                        "zones of adjacent members may overlap slightly")
        if t_:
            items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=A[0] * t_[0], base=A[1] * t_[1],
                                 high=A[2] * t_[2], formula=formula,
                                 assumptions=["BLINDING_THICKNESS_M", "BLINDING_PROJECTION_M"] +
                                 (["BLINDING_UNDER"] if name != "FOOTINGS" else []),
                                 support="CONVENTION_ONLY", confidence="MEDIUM", blocker="BLINDING_PROJECTION",
                                 **common))
        else:
            tl, _, th = _trip(conv, "BLINDING_THICKNESS_EXPOSURE_M")
            items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                                 blocker="BLINDING_THICKNESS_NOT_PRINTED",
                                 assumptions=["BLINDING_THICKNESS_EXPOSURE_M", "BLINDING_PROJECTION_M"],
                                 exposure_low=A[0] * tl, exposure_high=A[2] * th,
                                 expression=f"{A[1]:.2f} m2 x t (blinding thickness not printed)", **common))
        reg(cid, "PLAIN_CONCRETE", "FOUNDATION", "EXPLICIT_NONE", "plain concrete: no reinforcement")
    if skipped:
        risk.append({"KIND": "BLINDING_FOOTING_WITHOUT_SIZE", "WHERE": "FOUNDATION",
                     "DETAIL": f"{skipped} footing records without a size: no blinding counted for them"})


def _convex_union_area(polys):
    """area of the union of convex polygons by inclusion-exclusion over every group of mutually overlapping
    polygons (the intersection of convex polygons is convex, so each term is one clip): exact. Bounding boxes prune
    the pairs. -> (area, sum of the pairwise overlaps, largest group of outlines meeting at one place)."""
    bb = [(min(x for x, _ in q), min(y for _, y in q), max(x for x, _ in q), max(y for _, y in q)) for q in polys]
    n = len(polys)
    nb = defaultdict(set)
    for i in range(n):
        for j in range(i + 1, n):
            if bb[i][0] < bb[j][2] and bb[j][0] < bb[i][2] and bb[i][1] < bb[j][3] and bb[j][1] < bb[i][3]:
                nb[i].add(j)
                nb[j].add(i)
    total, pair, deepest = 0.0, 0.0, 1

    def grow(c, members, cand):
        nonlocal total, pair, deepest
        for k in sorted(cand):
            t = MD.clip_convex(c, polys[k])
            if len(t) < 3:
                continue
            a = MD.poly_area(t)
            if a <= 1e-12:
                continue
            m = members + 1
            total += a if m % 2 else -a
            pair += a if m == 2 else 0.0
            deepest = max(deepest, m)
            grow(t, m, {x for x in cand & nb[k] if x > k})
    for i in range(n):
        total += MD.poly_area(polys[i])
        grow(polys[i], 1, {j for j in nb[i] if j > i})
    return total, pair, deepest


def _overlap_with_union(poly, convex):
    """area of poly ∩ union(convex polygons): inclusion-exclusion over the groups of mutually overlapping convex
    polygons that touch poly (each term clips poly by one convex intersection)."""
    cand = [q for q in convex if MD.overlap_area(poly, q) > 1e-12]
    total = 0.0

    def grow(c, m, rest):
        nonlocal total
        for k in rest:
            t = MD.clip_convex(c, cand[k])
            if len(t) < 3 or MD.poly_area(t) <= 1e-12:
                continue
            a = MD.overlap_area(poly, t)
            total += a if (m + 1) % 2 else -a
            grow(t, m + 1, [x for x in rest if x > k])
    for i, q in enumerate(cand):
        total += MD.overlap_area(poly, q)
        grow(q, 1, list(range(i + 1, len(cand))))
    return total


def _register_on_foundation(D):
    """the translation of the ground-beam plan onto the foundation plan (column centres landing in the footings,
    a centre-difference vote on a 0.05 m grid) -> (state, shift {sheet: (dx, dy)}, matched footings)."""
    fp = next((r for r in D["sheets"].values() if r["sheet"]["role"] == "FOUNDATION_PLAN"), None)
    gb = next((r for r in D["sheets"].values() if r["sheet"]["role"] == "GROUND_BEAM_PLAN"), None)
    if fp is None:
        return "NO_FOUNDATION_PLAN", {}, 0
    u = D["unit_m"]
    boxes = [f["box"] for f in fp.get("footings", []) if f.get("box")]
    shift = {fp["sheet"]["sheet_id"]: (0.0, 0.0)}
    if gb is None:
        return "REGISTERED", shift, len(boxes)
    cols = gb.get("column_boxes", [])
    votes = Counter()
    g = 0.05 / u
    for fb in boxes:
        fc = ((fb[0] + fb[2]) / 2, (fb[1] + fb[3]) / 2)
        for c in cols:
            cc = ((c[0] + c[2]) / 2, (c[1] + c[3]) / 2)
            votes[(round((fc[0] - cc[0]) / g) * g, round((fc[1] - cc[1]) / g) * g)] += 1
    if not votes:
        return "NO_COMMON_MEMBERS", {}, 0
    (dx, dy), n1 = votes.most_common(1)[0]
    n2 = votes.most_common(2)[1][1] if len(votes) > 1 else 0
    hit = sum(1 for fb in boxes if any(fb[0] <= (c[0] + c[2]) / 2 + dx <= fb[2] and
                                       fb[1] <= (c[1] + c[3]) / 2 + dy <= fb[3] for c in cols))
    if hit < 0.6 * max(1, len(boxes)) or n1 < 2 * max(1, n2):
        return "NOT_REGISTERED", {}, hit
    shift[gb["sheet"]["sheet_id"]] = (dx, dy)
    return "REGISTERED", shift, hit


def _strip_outline(b, band, pn, dx, dy):
    """the blinding strip of a beam (its band +- p sideways) in the foundation frame, CCW; None when the band has no
    straight frame or four-cornered outline."""
    if band is not None and band.get("kind", "STRAIGHT") == "STRAIGHT" and band.get("u"):
        uu, nn = band["u"], (-band["u"][1], band["u"][0])
        lo, hi = band["lo_off"] - pn, band["hi_off"] + pn
        return [(uu[0] * t_ + nn[0] * o + dx, uu[1] * t_ + nn[1] * o + dy)
                for t_, o in ((band["t0"], lo), (band["t1"], lo), (band["t1"], hi), (band["t0"], hi))]
    poly = b.get("polygon")
    if not poly or len(poly) != 4 or b.get("kind", "STRAIGHT") != "STRAIGHT":
        return None
    e = max(range(4), key=lambda i: math.dist(poly[i], poly[(i + 1) % 4]))
    (ax, ay), (bx, by) = poly[e], poly[(e + 1) % 4]
    L = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / L, (by - ay) / L
    nx, ny = -uy, ux
    ts = [x * ux + y * uy for x, y in poly]
    os_ = [x * nx + y * ny for x, y in poly]
    t0, t1, o0, o1 = min(ts), max(ts), min(os_) - pn, max(os_) + pn
    return [(ux * t_ + nx * o + dx, uy * t_ + ny * o + dy) for t_, o in ((t0, o0), (t1, o0), (t1, o1), (t0, o1))]


def _blinding_union(D, foot, foot_box, strips, strip_rec, p_):
    """M4: the blinding plan as the union of the footing outlines (+ p) and the beam strips (band +- p), each
    registered on the foundation plan: an area under two outlines (a strip on a footing, two strips at a junction,
    two footings' projections) is counted once. Outlines without a place (a footing by its label only, a curved
    band) are added whole. -> {state, footings_m2, beams_m2 (per p), area_m2 (strip on footing), strip_strip_m2,
    footing_footing_m2, ...}"""
    state, shift, matched = _register_on_foundation(D)
    if state != "REGISTERED":
        return {"state": state, "area_m2": (0.0, 0.0, 0.0), "matched": matched}
    u = D["unit_m"]
    fpos = [(b, dims) for b, dims in zip(foot_box, foot) if b]
    ffree = [dims for b, dims in zip(foot_box, foot) if not b]
    res = {k: [] for k in ("footings_m2", "beams_m2", "area_m2", "strip_strip_m2", "footing_footing_m2",
                           "placed_footing_union_m2", "placed_union_m2")}
    over, free_s, quad = set(), 0, 0
    for p in p_:
        pn = p / u
        F = [[(b[0] - pn, b[1] - pn), (b[2] + pn, b[1] - pn), (b[2] + pn, b[3] + pn), (b[0] - pn, b[3] + pn)]
             for b, _ in fpos]
        S, add_s = [], 0.0
        free_s = 0
        for k, ((net, length, band, sid), b) in enumerate(zip(strips, strip_rec)):
            q = _strip_outline(b, band, pn, *shift[sid]) if sid in shift else None
            if q is None:
                add_s += net + 2 * p * length
                free_s += 1
                continue
            if sum(q[i][0] * q[(i + 1) % 4][1] - q[(i + 1) % 4][0] * q[i][1] for i in range(4)) < 0:
                q = q[::-1]
            S.append(q)
            if any(MD.overlap_area(q, f) > 1e-12 for f in F):
                over.add(k)
        uf, _, _ = _convex_union_area(F)
        ua, _, deep = _convex_union_area(F + S)
        us, _, _ = _convex_union_area(S)
        quad = max(quad, deep)
        fA = uf * u * u + sum((L + 2 * p) * (W + 2 * p) for L, W in ffree)
        tot = ua * u * u + sum((L + 2 * p) * (W + 2 * p) for L, W in ffree) + add_s
        res["footings_m2"].append(fA)
        res["beams_m2"].append(tot - fA)
        res["area_m2"].append((us + uf - ua) * u * u)        # strip area lying on footing blinding
        res["strip_strip_m2"].append((sum(MD.poly_area(q) for q in S) - us) * u * u)
        res["footing_footing_m2"].append((sum(MD.poly_area(f) for f in F) - uf) * u * u)
        res["placed_footing_union_m2"].append(uf * u * u)
        res["placed_union_m2"].append(ua * u * u)
    return dict({k: tuple(v) for k, v in res.items()}, state="REGISTERED", shift=shift, matched=matched,
                strips_over_footings=len(over), free_strips=free_s, free_footings=len(ffree),
                most_outlines_at_one_place=quad)


def _blinding_overlap(D, strips, p_):
    """M4: the area of ground / strap beam blinding strips (band +- p) lying on footing blinding (footing + p), at
    each projection p. The ground-beam plan is registered on the foundation plan by its column outlines landing in
    the footings (centre-difference vote): -> {state, area_m2 (per p), strips_over_footings, matched}."""
    fp = next((r for r in D["sheets"].values() if r["sheet"]["role"] == "FOUNDATION_PLAN"), None)
    gb = next((r for r in D["sheets"].values() if r["sheet"]["role"] == "GROUND_BEAM_PLAN"), None)
    if fp is None:
        return None
    u = D["unit_m"]
    boxes = [f["box"] for f in fp.get("footings", []) if f.get("box")]
    shift = {fp["sheet"]["sheet_id"]: (0.0, 0.0)}
    matched = len(boxes)
    if gb is not None:
        cols = gb.get("column_boxes", [])
        votes = Counter()
        g = 0.05 / u
        for fb in boxes:
            fc = ((fb[0] + fb[2]) / 2, (fb[1] + fb[3]) / 2)
            for c in cols:
                cc = ((c[0] + c[2]) / 2, (c[1] + c[3]) / 2)
                votes[(round((fc[0] - cc[0]) / g) * g, round((fc[1] - cc[1]) / g) * g)] += 1
        if not votes:
            return {"state": "NO_COMMON_MEMBERS", "area_m2": (0.0, 0.0, 0.0)}
        (dx, dy), n1 = votes.most_common(1)[0]
        n2 = votes.most_common(2)[1][1] if len(votes) > 1 else 0
        hit = sum(1 for fb in boxes if any(fb[0] <= (c[0] + c[2]) / 2 + dx <= fb[2] and
                                           fb[1] <= (c[1] + c[3]) / 2 + dy <= fb[3] for c in cols))
        matched = hit
        if hit < 0.6 * max(1, len(boxes)) or n1 < 2 * max(1, n2):
            return {"state": "NOT_REGISTERED", "area_m2": (0.0, 0.0, 0.0), "matched": hit}
        shift[gb["sheet"]["sheet_id"]] = (dx, dy)
    out, over = [], set()
    for p in p_:
        pn = p / u
        foot = [[(b[0] - pn, b[1] - pn), (b[2] + pn, b[1] - pn), (b[2] + pn, b[3] + pn), (b[0] - pn, b[3] + pn)]
                for b in boxes]
        tot = 0.0
        for k, (_, _, band, sid) in enumerate(strips):
            if band is None or band.get("kind", "STRAIGHT") != "STRAIGHT" or sid not in shift:
                continue
            dx, dy = shift[sid]
            uu, nn = band["u"], (-band["u"][1], band["u"][0])
            lo, hi = band["lo_off"] - pn, band["hi_off"] + pn
            q = [(uu[0] * t_ + nn[0] * o + dx, uu[1] * t_ + nn[1] * o + dy)
                 for t_, o in ((band["t0"], lo), (band["t1"], lo), (band["t1"], hi), (band["t0"], hi))]
            a = sum(MD.overlap_area(q, f) for f in foot) * u * u
            if a > 1e-6:
                over.add(k)
            tot += a
        out.append(tot)
    return {"state": "REGISTERED", "area_m2": tuple(out), "strips_over_footings": len(over), "matched": matched,
            "shift": shift}


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


def _gb_exterior(conv, b, floor_m=None, m4=False):
    """the exterior ground-beam depth from printed levels: floor level - build-up - outer ground level (low = lowest
    floor, highest build-up and ground; high the opposite). None unless the profile prints the exterior detail and
    both levels, and the band's width is the detail's. floor_m (M4): the floor level printed on the architectural plan
    inside this band, replacing the profile's single ground-floor level."""
    need = ("GB_EXTERIOR_DETAIL", "GF_FLOOR_LEVEL_M", "OUTER_GROUND_LEVEL_M", "GB_EXTERIOR_BUILDUP_M")
    if not all(k in conv.items for k in need):
        return None
    det = conv["GB_EXTERIOR_DETAIL"]
    if det.get("W") and abs(det["W"] - b["width_m"]) > STRAP_WIDTH_TOL_M:
        return None
    f, g, bu = _trip(conv, "GF_FLOOR_LEVEL_M"), _trip(conv, "OUTER_GROUND_LEVEL_M"), _trip(conv, "GB_EXTERIOR_BUILDUP_M")
    if floor_m is not None:
        f = (floor_m, floor_m, floor_m)
    d = (f[0] - bu[2] - g[2], f[1] - bu[1] - g[1], f[2] - bu[0] - g[0])
    if not m4:
        if d[0] <= 0:
            return None
    elif d[2] <= 0:
        return {"depth": d, "detail": det, "none": True, "floor_m": f[1], "assumptions": []}
    elif d[0] <= 0:
        d = (0.0, max(d[1], 0.0), d[2])
    return {"depth": d, "detail": det, "floor_m": f[1],
            "assumptions": ["GB_EXTERIOR_CANDIDATE", "GB_EXTERIOR_DETAIL",
                            "OUTER_GROUND_LEVEL_M", "GB_EXTERIOR_BUILDUP_M"] +
                           ([] if floor_m is not None else ["GF_FLOOR_LEVEL_M"])}


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


def _slab_m4(slab, rec, u, conv, ground, risk, sid):
    """M4, in place on the sheet's slab faces: (1) a face's overlap with beam bands and column outlines is deducted
    (the members own it - never counted twice); (2) an untagged panel takes the project's printed default thickness
    before the sheet-uniform extension of one panel's tag. The original area and basis are kept on the face."""
    if slab.get("_m4"):
        return
    slab["_m4"] = True
    bands = [b["polygon"] for b in rec.get("bands", []) if b["kind"] == "STRAIGHT"]
    cols = [MD.box_poly(c) for c in rec.get("slab_column_boxes", rec.get("column_boxes", []))]
    dflt = _cv(conv, "SLAB_PROJECT_DEFAULT_THICKNESS_M") if not ground else None
    first = _cv(conv, "SLAB_UNTAGGED_THICKNESS_SOURCE", "PROJECT_DEFAULT_FIRST")
    for f in slab["faces"]:
        if f["class"] not in ("PANEL",):
            continue
        poly = f["polygon"]
        # a band crossing a column inside the face counts once; a member inside a hole of the face is not in it
        ov = (_overlap_with_union(poly, bands + cols) -
              sum(_overlap_with_union(h, bands + cols) for h in (f.get("hole_polygons") or []) if len(h) >= 3)) * u * u
        if ov > 1e-4:
            f["area_gross_m2"] = f["area_m2"]
            f["member_overlap_m2"] = ov
            f["area_m2"] = max(f["area_m2"] - ov, 0.0)
            risk.append({"KIND": "SLAB_FACE_MEMBER_OVERLAP_DEDUCTED", "WHERE": sid,
                         "DETAIL": f"{f['face_id']}: {ov:.3f} m2 of the face lies in beam bands / column outlines "
                                   "(deducted: the members own it)"})
        if dflt and f.get("t_basis") == "SHEET_UNIFORM" and first == "PROJECT_DEFAULT_FIRST":
            if f.get("t_m") is not None and abs(f["t_m"] - dflt) > 1e-6:
                risk.append({"KIND": "SLAB_THICKNESS_SHEET_TAG_VS_PROJECT_DEFAULT", "WHERE": sid,
                             "DETAIL": f"{f['face_id']} {f['area_m2']:.2f} m2: untagged; the sheet's one printed tag "
                                       f"gives {f['t_m']:.3f} m, the project default {dflt:.3f} m (default used)"})
            f["t_sheet_uniform_m"] = f.get("t_m")
            f["t_m"], f["t_basis"] = dflt, "PROJECT_DEFAULT"
        if f.get("t_m"):
            f["volume_m3"] = f["area_m2"] * f["t_m"]


def _stair_items(items, reg, risk, f, sid, st, ground, conv, u, src_file):
    """M4: a stair zone measured as a stair (stair_measure) from its drawn treads, the rise of its storey and the
    waist: PROVISIONAL with a printed waist (profile STAIR_WAIST_M), else UNRESOLVED with the waist range as the
    exposure. A zone whose riser height falls outside the diagnostic band holds part of a stair: False (the caller
    keeps the slab-zone exposure)."""
    tr = f.get("treads") or {}
    if not tr.get("lines"):
        return False
    run = SM.flight([{"a": a, "b": b} for a, b in tr["lines"]], u)
    if run is None:
        return False
    if ground:
        if not all(k in conv.items for k in ("GF_FLOOR_LEVEL_M", "OUTER_GROUND_LEVEL_M")):
            return False
        rise = conv.base("GF_FLOOR_LEVEL_M") - conv.base("OUTER_GROUND_LEVEL_M")
    else:
        if f"STOREY_HEIGHT_{st}" not in conv.items:
            return False
        rise = conv.base(f"STOREY_HEIGHT_{st}")
    rule = _cv(conv, "STAIR_RISER_RULE", "LINES_PLUS_ONE")
    printed = "STAIR_WAIST_M" in conv.items
    waists = _trip(conv, "STAIR_WAIST_M") if printed else _trip(conv, "STAIR_WAIST_EXPOSURE_M")
    qs = [SM.quantities(f["area_m2"], run, rise, w, riser_rule=rule) for w in waists]
    if any(q["state"] != "MEASURED" for q in qs):
        risk.append({"KIND": "STAIR_ZONE_PARTIAL", "WHERE": sid,
                     "DETAIL": f"{f['face_id']}: {qs[0].get('why')} - the zone holds part of a stair; slab-zone "
                               "exposure kept"})
        return False
    cid = f"STAIRS:{st}:{f['face_id']}"
    q = qs[1]
    if q["overflow_m2"] > 0.01:
        risk.append({"KIND": "STAIR_FLIGHT_EXCEEDS_ZONE", "WHERE": sid,
                     "DETAIL": f"{f['face_id']}: the flight's plan ({q['flight_plan_m2']:.2f} m2) exceeds the zone "
                               f"({f['area_m2']:.2f} m2) - part of the flight lies outside the zone (landing 0)"})
    common = dict(component_id=cid, trade="CONCRETE", family="STAIRS", storey=st,
                  source=f"{src_file} {sid} stair zone {f['face_id']}: {run['n_lines']} drawn tread lines ({run['kind']})",
                  dimensions={"kind": run["kind"], "tread_lines": run["n_lines"], "risers": q["risers"],
                              "riser_m": round(q["riser_m"], 4), "going_m": round(run["going_m"], 4),
                              "width_m": round(run["width_m"], 4), "flight_plan_m2": round(q["flight_plan_m2"], 4),
                              "landing_m2": round(q["landing_m2"], 4), "zone_m2": round(f["area_m2"], 4),
                              "rise_m": rise, "tread_finish_m2": round(q["tread_m2"], 4),
                              "riser_finish_m2": round(q["riser_face_m2"], 4)},
                  double_count_risk="the zone is not counted as slab; landing beams on the plan are the beams'")
    asm = ["STAIR_RISER_RULE"] + (["STAIR_WAIST_M"] if printed else ["STAIR_WAIST_EXPOSURE_M"]) + \
        (["GF_FLOOR_LEVEL_M", "OUTER_GROUND_LEVEL_M"] if ground else [f"STOREY_HEIGHT_{st}"])
    if printed:
        items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=qs[0]["total_m3"],
                             base=q["total_m3"], high=qs[2]["total_m3"], formula=q["basis"] + "; landings x waist",
                             assumptions=asm, support="CONVENTION_ONLY", confidence="LOW",
                             blocker="STAIR_GEOMETRY_FROM_PLAN", **common))
    else:
        items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                             blocker="STAIR_WAIST_NOT_PRINTED", assumptions=asm,
                             exposure_low=qs[0]["total_m3"], exposure_high=qs[2]["total_m3"],
                             expression=f"{q['basis']}; landings x waist; waist {waists[0]:g} - {waists[2]:g} m "
                                        "(not printed)", **common))
    reg(cid, "STAIRS", st, "MISSING_DATA", "stair bars need the stair section's bar details")
    return True


def _lintel_items(items, reg, risk, lintels, conv, cover_trip, hook_std):
    """M4: lintels over the jambed openings of the architectural plans, bound to the printed lintel schedule by
    opening width. An opening with no structural beam over it carries masonry up to the slab: PROVISIONAL. Under a
    beam the need depends on the head height against the beam soffit (LINTEL_UNDER_BEAM, UNRESOLVED by default);
    an opening outside the schedule's bands is reported, never measured."""
    rows = conv["LINTEL_SCHEDULE"].get("rows") or []
    if not rows:
        return
    bearing = _trip(conv, "LINTEL_BEARING_M")
    under = _cv(conv, "LINTEL_UNDER_BEAM", "UNRESOLVED")
    cnt = Counter()
    for st, rec in sorted(lintels.items()):
        if rec.get("registration", {}).get("state") != "REGISTERED":
            risk.append({"KIND": "LINTEL_PLAN_NOT_REGISTERED", "WHERE": st,
                         "DETAIL": f"architectural {st} plan: {len(rec.get('openings', []))} openings, the plan is not "
                                   "registered on the slab above - lintel need not decided"})
            continue
        for op in rec["openings"]:
            res = LMS.lintel(op, rows, bearing_m=bearing, cover_m=tuple(sorted(cover_trip, reverse=True)))
            cid = f"LINTELS:{st}:{op['opening_id']}"
            over = op.get("beam_over", "NONE")
            if res["state"] != "MEASURED":
                cnt[res["state"]] += 1
                risk.append({"KIND": "LINTEL_OPENING_" + res["state"], "WHERE": st,
                             "DETAIL": f"{cid}: opening {op['width_m']:.2f} m in a {op['wall_t_m']:.2f} m wall - "
                                       "outside the lintel schedule's bands (not measured)"})
                continue
            common = dict(component_id=cid, trade="CONCRETE", family="LINTELS", storey=st,
                          source=f"architectural plan {rec['arch_sheet']} wall band {op['band_id']} (layer "
                                 f"{op['layer']}); lintel schedule row {res['row']}",
                          dimensions={"opening_m": round(op["width_m"], 3), "wall_t_m": round(op["wall_t_m"], 3),
                                      "D_m": res["D_m"], "length_m": round(res["length_m"][1], 3),
                                      "jambs": f"{op['start_jamb']}/{op['end_jamb']}", "beam_over": over},
                          double_count_risk="an opening under a beam is not given a lintel unless LINTEL_UNDER_BEAM "
                                            "says so")
            needed = over == "NONE" or (over == "FULL" and under == "REQUIRED")
            if over == "FULL" and under == "NOT_REQUIRED":
                cnt["UNDER_BEAM_NOT_REQUIRED"] += 1
                continue
            lo, b_, hi = res["concrete_m3"]
            if needed:
                cnt["MEASURED"] += 1
                items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=lo, base=b_, high=hi,
                                     formula="B (wall) x D (schedule row) x (opening + bearing on each masonry jamb)",
                                     assumptions=["LINTEL_SCHEDULE", "LINTEL_BEARING_M"] +
                                                 (["LINTEL_UNDER_BEAM"] if over == "FULL" else []),
                                     support="CONVENTION_ONLY", confidence="LOW", blocker="LINTEL_OPENING_FROM_ARCH",
                                     **common))
                tot = 0.0
                for role, n, d, L3 in res["bars"]:
                    m3 = sorted(n * BS.mass_kg(x, d) for x in L3)
                    items.append(PE.item(item_id=f"P-S:{cid}:{role}:D{d:g}", component_id=cid,
                                         trade="REINFORCEMENT", family="LINTELS", storey=st, category="PROVISIONAL",
                                         low=m3[0], base=n * BS.mass_kg(L3[1], d), high=m3[2], dia_mm=d,
                                         source=common["source"], formula="count x (lintel length - 2 cover)",
                                         assumptions=["LINTEL_SCHEDULE", "LINTEL_BEARING_M", "REBAR_COVER_BEAM_M"],
                                         support="CONVENTION_ONLY", confidence="LOW", blocker="LAP_ANCHORAGE_RULE"))
                    tot += n * BS.mass_kg(L3[1], d)
                s_ = res.get("stirrups")
                if s_:
                    vals = []
                    for k, cv in enumerate(sorted(cover_trip, reverse=True)):
                        try:
                            ln = BS.closed_link(res["B_m"], res["D_m"], cv, s_["dia_mm"], table=hook_std)["developed_m"]
                        except ValueError:
                            continue
                        vals.append(s_["count"][k] * BS.mass_kg(ln, s_["dia_mm"]))
                    if len(vals) == 3:
                        v3 = sorted(vals)
                        items.append(PE.item(item_id=f"P-S:{cid}:STIRRUPS:D{s_['dia_mm']:g}", component_id=cid,
                                             trade="REINFORCEMENT", family="LINTELS", storey=st,
                                             category="PROVISIONAL", low=v3[0], base=vals[1], high=v3[2],
                                             dia_mm=s_["dia_mm"], source=common["source"],
                                             formula="ceil(rate x length) closed links",
                                             assumptions=["LINTEL_SCHEDULE", "REBAR_COVER_BEAM_M",
                                                          "REBAR_HOOK_STANDARD"],
                                             support="CONVENTION_ONLY", confidence="LOW", blocker="TIE_LINK_HOOK_RULE"))
                        tot += vals[1]
                reg(cid, "LINTELS", st, "PROVISIONAL_MODEL", "lintel schedule bars", tot)
            else:
                cnt["UNDER_BEAM_UNRESOLVED" if over == "FULL" else "PARTIAL_BEAM_UNRESOLVED"] += 1
                items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                                     confidence="LOW", blocker="LINTEL_NEED_UNDER_BEAM" if over == "FULL" else
                                     "LINTEL_PARTIAL_BEAM", assumptions=["LINTEL_SCHEDULE", "LINTEL_UNDER_BEAM"],
                                     exposure_low=0.0, exposure_high=hi,
                                     expression=f"a beam runs over the opening ({over}): a separate lintel only if the "
                                                f"head is below the beam soffit; {b_:.3f} m3 if it is", **common))
                reg(cid, "LINTELS", st, "MISSING_DATA", "lintel need not established (beam over the opening)")
    risk.append({"KIND": "LINTEL_SUMMARY", "WHERE": "ARCH",
                 "DETAIL": ", ".join(f"{k} {v}" for k, v in sorted(cnt.items()))})


def _cb_model(D, rec, conv, cover_trip, hook_std):
    """M4: the continuous-beam lines of one plan (continuous_beams): spans matched to the printed span sequence, the
    physical bar groups of each matched line and their mass shared out to the pieces once. -> {lines, band, steel}."""
    u = D["unit_m"]
    rows = {r["mark"]: r for r in D["schedule"]["rows"] if r["family"] == "CONTINUOUS_BEAM"}
    kw = dict(tol_m=_cv(conv, "CB_SPAN_MATCH_TOL_M"), tol_rel=_cv(conv, "CB_SPAN_MATCH_TOL_REL", 0.10),
              margin_m=_cv(conv, "CB_DIRECTION_MARGIN_M", 0.25), basis=_cv(conv, "CB_PRINTED_SPAN_BASIS", "AXIS"))
    bkw = dict(anchorage_d=_trip(conv, "BEAM_BAR_ANCHORAGE_D"), support_frac=_trip(conv, "CB_SUPPORT_BAR_EXTENT_FRAC"),
               support_basis=_cv(conv, "CB_SUPPORT_BAR_SPAN_BASIS", "CLEAR"),
               bottom_ext_m=_trip(conv, "CB_BOTTOM_EXTENSION_M"), lap_d=_trip(conv, "BEAM_LAP_D"),
               stock_m=_cv(conv, "BAR_STOCK_LENGTH_M", 12.0))
    out = {"lines": [], "band": {}, "steel": {}}
    marks = sorted({m["mark"] for m in rec.get("marks", []) if m.get("family") == "CONTINUOUS_BEAM" and
                    str(m.get("state", "")).startswith("BOUND")})
    for mk in marks:
        row = rows.get(mk)
        if row is None:
            continue
        P = CBM.printed_spans(row)
        W, H = row["dims_m"].get("W"), row["dims_m"].get("H")

        def link_kg(g, W=W, H=H):
            vals = []
            for cv in cover_trip:
                try:
                    vals.append(BS.closed_link(W, H, cv, g["dia_mm"], table=hook_std)["developed_m"] *
                                BS.kg_per_m(g["dia_mm"]))
                except (ValueError, TypeError):
                    pass
            return tuple(sorted(vals)) if len(vals) == 3 else (0.0, 0.0, 0.0)
        for k, ln in enumerate(CBM.lines(rec, mk, u), 1):
            m = CBM.match(ln, P, **kw)
            lid = f"{rec['sheet']['sheet_id']}:{mk}:{k}"
            entry = {"line_id": lid, "mark": mk, "state": m["state"], "direction": m.get("direction"),
                     "decided_by": m.get("decided_by"), "printed_m": P, "residuals": m.get("residuals"),
                     "pieces": [p_["band_id"] for p_ in ln["pieces"]], "inherited": m.get("inherited", []),
                     "spans": [{k_: v for k_, v in s.items() if k_ not in ("piece_extents",)} for s in m["spans"]],
                     "best_attempt": m.get("best_attempt"), "groups": [], "missing": []}
            out["lines"].append(entry)
            for s in m["spans"]:
                for pid in s["pieces"]:
                    out["band"][pid] = {"mark": mk, "line": lid, "state": m["state"],
                                        "inherited": pid in m.get("inherited", [])}
            for p_ in ln["pieces"]:                          # a line not mapped to the spans still names its state
                out["band"].setdefault(p_["band_id"], {"mark": mk, "line": lid, "state": m["state"],
                                                       "inherited": False})
            if m["state"] not in CBM.MAPPED or not (W and H):
                continue
            readings = [m["spans"]] + ([m["alternative_spans"]] if m.get("alternative_spans") else [])
            allocs = []
            for spans in readings:
                pb = CBM.physical_bars(dict(m, spans=spans), row, **bkw)
                al, totals = CBM.allocate(pb["groups"], spans, link_kg)
                allocs.append((al, totals, pb, spans))
            if len(allocs) == 2:
                tb = [sum(v[1] for _, v in a[1]) for a in allocs]
                larger = _cv(conv, "CB_AMBIGUOUS_DIRECTION_BASE", "LARGER") == "LARGER"
                base_i = (0 if tb[0] >= tb[1] else 1) if larger else (0 if tb[0] <= tb[1] else 1)
            else:
                base_i = 0
            al0, totals0, pb0, spans0 = allocs[base_i]
            entry["groups"] = [{k_: v for k_, v in g.items()} | {"mass_kg": dict(totals0).get(g["bar_id"])}
                               for g in pb0["groups"]]
            entry["missing"] = pb0["missing"]
            by_ix = {s["index"]: s for s in spans0}
            for pid in {p_ for s in spans0 for p_ in s["pieces"]}:
                keys = set().union(*[set(a[0].get(pid, {})) for a in allocs])
                vals = {}
                for key in keys:
                    v = [a[0].get(pid, {}).get(key, [0.0, 0.0, 0.0]) for a in allocs]
                    vals[key] = (min(x[0] for x in v), v[base_i][1], max(x[2] for x in v))
                miss = []
                for role, j, why in pb0["missing"]:
                    ix = [j] if role in ("BOTTOM", "STIRRUP") else ([j, j + 1] if role == "SUPPORT_TOP" else
                                                                    list(by_ix))
                    if any(pid in by_ix[i]["pieces"] for i in ix if i in by_ix):
                        miss.append((role, j, why))
                out["steel"][pid] = {"line": lid, "state": m["state"], "values": vals, "missing": miss,
                                     "ambiguous": len(allocs) == 2, "decided_by": m.get("decided_by")}
    return out


def _cb_bars(items, reg, b, cid, fam, st, source, cbm):
    """M4: the bars of one piece of a continuous-beam line from its line's physical bar groups (shared out once)."""
    s = cbm["steel"].get(b["band_id"])
    ev = cbm["band"].get(b["band_id"])
    if s is None:
        why = f"continuous-beam span sequence {ev['state']}" if ev else "the piece is on no continuous-beam line"
        reg(cid, fam, st, "MISSING_DATA", f"continuous-beam bars are per span; {why} (line not mapped to the "
                                          "schedule spans)")
        return
    tot = 0.0
    blk = "CB_SPAN_DIRECTION_AMBIGUOUS" if s["ambiguous"] else "LAP_ANCHORAGE_RULE"
    for (role, d), (lo, base, hi) in sorted(s["values"].items()):
        if base <= 0 and hi <= 0:
            continue
        items.append(PE.item(item_id=f"P-S:{cid}:CB_{role}:D{d:g}", component_id=cid, trade="REINFORCEMENT",
                             family=fam, storey=st, category="PROVISIONAL", low=lo, base=base, high=hi, dia_mm=d,
                             source=f"{source}; continuous-beam line {s['line']} ({s['state']})",
                             formula={"BOTTOM": "count x (clear span + extension at each support)",
                                      "SUPPORT_TOP": "count x (support + fraction x span each side), shared by span",
                                      "STIRRUP": "(rate x clear span + 1) closed links",
                                      "TOP_THROUGH": "count x (whole line + anchorage + laps), shared by span",
                                      "TOP_SPAN": "count x (clear span + anchorage)"}.get(role, role),
                             assumptions=["BEAM_BAR_ANCHORAGE_D", "CB_SUPPORT_BAR_EXTENT_FRAC", "CB_BOTTOM_EXTENSION_M",
                                          "REBAR_COVER_BEAM_M", "CB_SPAN_MATCH_TOL_M"] +
                                         (["CB_AMBIGUOUS_DIRECTION_BASE"] if s["ambiguous"] else []),
                             support="CONVENTION_ONLY", confidence="LOW" if s["ambiguous"] else "MEDIUM",
                             blocker=blk))
        tot += base
    for role, j, why in s["missing"]:
        items.append(PE.item(item_id=f"U-S:{cid}:CB_{role}{j or ''}", component_id=cid, trade="REINFORCEMENT",
                             family=fam, storey=st, category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                             blocker="CB_ROLE_" + why, source=f"{source}; continuous-beam line {s['line']}",
                             expression=f"{role.lower().replace('_', ' ')}{' ' + str(j) if j else ''}: "
                                        f"{'the schedule cell is empty' if why == 'EMPTY_CELL' else 'not printed in the schedule'}"))
    miss = sorted({f"{r}{j or ''}" for r, j, _ in s["missing"]})
    reg(cid, fam, st, "PARTIAL_MISSING" if miss else "PROVISIONAL_MODEL",
        f"continuous-beam model ({s['state'].lower()}"
        + (", direction by lower residual" if s.get("decided_by") == "LOWER_RESIDUAL" else "")
        + (", reading with the larger mass as base" if s["ambiguous"] else "") + ")"
        + (f"; missing: {', '.join(miss)}" if miss else ""), tot)


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


MISSING_STATES = ("MISSING_DATA", "PARTIAL_MISSING")


def rebar_completeness(items, register):
    """M3: one reinforcement state for every concrete component, and the missing steel counted by family and storey.
    A concrete component without a register row gets MISSING_DATA ('no bar model'): the BOQ can never read an
    absent row as zero steel. -> {rows, by_family_storey, totals}."""
    reg = {r["COMPONENT_ID"]: r for r in register}
    conc = {}
    for i in items:
        if i["trade"] == "CONCRETE":
            conc.setdefault(i["component_id"], i)
    u_steel = Counter(i["component_id"] for i in items if i["trade"] == "REINFORCEMENT" and
                      i["category"] == "UNRESOLVED")
    rows = []
    for cid, i in sorted(conc.items()):
        r = reg.get(cid) or {"REBAR_STATE": "MISSING_DATA", "REASON": "no bar model for this component",
                             "PROVISIONAL_KG_BASE": None}
        rows.append({"COMPONENT_ID": cid, "FAMILY": i["family"], "STOREY": i["storey"],
                     "CONCRETE_CATEGORY": i["category"], "REBAR_STATE": r["REBAR_STATE"], "REASON": r["REASON"],
                     "PROVISIONAL_KG_BASE": r.get("PROVISIONAL_KG_BASE"),
                     "UNRESOLVED_STEEL_ITEMS": u_steel.get(cid, 0)})
    for cid, r in sorted(reg.items()):
        if cid not in conc:                       # explicit none / outside scope rows with no concrete item
            rows.append({"COMPONENT_ID": cid, "FAMILY": r["FAMILY"], "STOREY": r["STOREY"], "CONCRETE_CATEGORY": "",
                         "REBAR_STATE": r["REBAR_STATE"], "REASON": r["REASON"],
                         "PROVISIONAL_KG_BASE": r.get("PROVISIONAL_KG_BASE"), "UNRESOLVED_STEEL_ITEMS": 0})
    agg = defaultdict(lambda: Counter())
    for r in rows:
        agg[(r["FAMILY"], r["STOREY"])][r["REBAR_STATE"]] += 1
        agg[(r["FAMILY"], r["STOREY"])]["UNRESOLVED_STEEL_ITEMS"] += r["UNRESOLVED_STEEL_ITEMS"]
    by = [{"FAMILY": f, "STOREY": st, "COMPONENTS": sum(c[k] for k in REBAR_STATES),
           **{k: c[k] for k in REBAR_STATES}, "UNRESOLVED_STEEL_ITEMS": c["UNRESOLVED_STEEL_ITEMS"],
           "MISSING_STEEL_COMPONENTS": sum(c[k] for k in MISSING_STATES)} for (f, st), c in sorted(agg.items())]
    tot = Counter()
    for r in rows:
        tot[r["REBAR_STATE"]] += 1
    return {"rows": rows, "by_family_storey": by, "totals": dict(tot),
            "missing_steel_components": sum(tot[k] for k in MISSING_STATES),
            "rule": "MISSING_DATA: no bar quantity exists; PARTIAL_MISSING: bars for part of the component, the rest "
                    "UNRESOLVED; neither is ever counted as zero kg"}


def policy_record():
    return {"policy": POLICY_ID, "rebar_states": REBAR_STATES,
            "rule": "no project register is loaded; every item names its source entities; a new project is never "
                    "VERIFIED; coverage risk is reported beside unresolved"}


STOREY_SEQUENCE = ("GF", "1F", "2F", "3F", "4F", "5F", "6F")


def _planted_column_items(D, items, reg, risk, conv, heights, occ, src_file, u):
    """M5: a column labelled on a slab plan with its own printed section (a planted column, e.g. 'P.C 20x70') stands
    on that slab and rises one storey. The generic route reads columns from the column plan; a planted column often
    appears only as such a label. Concrete only: section from the label (cm) x the height of the storey above; its
    bars stay MISSING_DATA (no ratio). A label within 1 m of a column already counted on that storey is skipped."""
    c = conv["PLANTED_COLUMN_LABELS"]
    pat = re.compile(c.get("label_pattern") or r"^\s*P\.?\s*C\.?\s*(\d{2,3})\s*[xX*]\s*(\d{2,3})\s*$")
    scale = float(c.get("label_unit_m", 0.01))
    order = [s_ for s_ in STOREY_SEQUENCE if s_ in heights]
    counted = {}
    for p in MD.column_storeys(occ, heights) if occ else []:
        if p.get("box") and p.get("state") == "MEASURED":
            o_ = D["sheets"][p["sheet"]]["sheet"].get("origin") or (0.0, 0.0)
            counted.setdefault(p["storey"], []).append(((p["box"][0] + p["box"][2]) / 2 - o_[0],
                                                        (p["box"][1] + p["box"][3]) / 2 - o_[1]))
    for sid, rec in sorted(D["sheets"].items()):
        if rec["sheet"]["role"] != "SLAB_PLAN":
            continue
        below = rec["sheet"].get("storey")
        st = order[order.index(below) + 1] if below in order and order.index(below) + 1 < len(order) else None
        o_ = rec["sheet"].get("origin") or (0.0, 0.0)
        for t in rec.get("texts", []) or []:
            m = pat.match(t.get("value") or "")
            if not m:
                continue
            W, Dp = int(m.group(1)) * scale, int(m.group(2)) * scale
            lx, ly = t["x"] - o_[0], t["y"] - o_[1]
            cid = f"COL:{sid}:PC@{round(t['x'])},{round(t['y'])}|{st or 'ROOF'}"
            if st and any(math.hypot(lx - a, ly - b) * u <= 1.0 for a, b in counted.get(st, [])):
                risk.append({"KIND": "PLANTED_COLUMN_ALREADY_COUNTED", "WHERE": sid,
                             "DETAIL": f"{cid}: label '{t['value']}' sits on a column already counted on {st}"})
                continue
            common = dict(component_id=cid, trade="CONCRETE", family="COLUMNS", storey=st or "UNKNOWN",
                          source=f"{src_file} {sid} label '{t['value']}' ({t.get('layer')}); planted on the {below} "
                                 f"slab", dimensions={"section_m": (W, Dp), "height_m": heights.get(st) if st else None,
                                                      "planted_on": below},
                          double_count_risk="stands on a beam / slab of the storey below; the column owns its footprint")
            if not st or not heights.get(st):
                items.append(PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY",
                                     confidence="LOW", blocker="PLANTED_COLUMN_STOREY", exposure_low=None,
                                     exposure_high=None, expression=f"{W:g} x {Dp:g} x storey height (no storey above)",
                                     **common))
                reg(cid, "COLUMNS", st or "UNKNOWN", "MISSING_DATA", "planted column: no storey above the slab plan")
                continue
            v = W * Dp * heights[st]
            items.append(PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=v, base=v, high=v,
                                 formula="planted column: label section x storey height",
                                 assumptions=[f"STOREY_HEIGHT_{st}", "PLANTED_COLUMN_LABELS"],
                                 support="CONVENTION_ONLY", confidence="MEDIUM", blocker="NOT_REVIEWED", **common))
            reg(cid, "COLUMNS", st, "MISSING_DATA", "planted column: bars of the label are not bound (no ratio)")
            risk.append({"KIND": "PLANTED_COLUMN_FROM_LABEL", "WHERE": sid,
                         "DETAIL": f"{cid}: '{t['value']}' -> {W:g} x {Dp:g} x {heights[st]:g} m on {st}"})
