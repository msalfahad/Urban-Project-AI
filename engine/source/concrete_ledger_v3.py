"""CONCRETE LEDGER V3 - CONCRETE_LEDGER_V2 (strip guard, curved strips) with the slab-plan beams re-bound by
BEAM_BINDING_V2 and the neck-only column types read from schedule TEXT rows (method CONCRETE_LEDGER_V3). A NEW method
version beside the frozen pieces: it imports generic_route, member_detection, concrete_ledger_v2, beam_binding_v2 and
column_schedule_text_rows and edits none of them; no released method calls it.

What changes against the route-G items (everything else is the route's own item, byte for byte):

1. Beams (BEAM_BINDING_V2, T-085). Per slab / ground-beam plan the route's own beam pipeline is replayed from the
   route's recorded inputs (edge layers, column boxes, widths, the same healing, `beam_bands`): first with the frozen
   V1 functions, which must reproduce the route's bands and marks exactly (else the sheet is NOT replayed and keeps its
   V1 items, recorded REPLAY_MISMATCH), then with the V2 functions:
     - a column outline linked by its leader to a planted-column label ('P.C 20x50') and lying inside the beam's width
       does not cut the beam (`split_at_supports_v2`);
     - a mark is direction-tested against an arc band (`bind_marks_v2`);
   section inheritance, single-face beams and `beam_quantities` run unchanged on the V2 bands, and the beam items are
   rebuilt by the route's own `generic_route.items_from` on that sheet record (same conventions, same depth reading,
   same held reasons: an unlabelled span across a support stays HELD, owner Q-16 = A). Only CONCRETE items of the beam
   families are taken from the rebuild; reinforcement items stay the route's (not in scope, listed as a follow-up).
2. Ring beams round circular openings (owner Q-44 = A): `ring_beams` on the drawn concentric faces; a ring whose
   section comes from its own printed mark or from an owner rule passed by the caller (`ring_rule`) becomes one line
   (net plan x H, the route's BEAM_DEPTH_READING) that replaces its arc-band items; any other ring stays as the route
   left it and is listed.
3. Upstands from printed sections: a section title 'SECTION X-X', its dimensioned outline (`section_profile`) and its
   cut line on a plan (`section_cuts`) give w x h x the clear span crossed (`upstand_lines`), one line per span; a
   section that cannot be read is listed HELD with its reason; nothing is measured without the printed values.
4. Column types typed as TEXT rows (T-075, SCHEDULE_TEXT_ROWS_V1): a column-plan occurrence of a NECK_ONLY type (every
   level above the foundation struck out on the schedule) is NOT_PRESENT: its held column item leaves the list with a
   NOT_PRESENT record (drawn evidence, never silent); a neck of such a type gets its printed section and stays HELD on
   the founding datum (owner Q-21 = C).

Rules: UP-QTY-STATUS-001 (measured / held / unsupported, missing never 0), UP-KB-PREC-001 (printed value wins), owner
Q-12 B (members by type), Q-16 A (no neighbour's section), Q-19 (no usual-villa size), Q-21 C (necks held), Q-44 A
(ring beam stays; the caller passes the rule). Nothing here names a project, sheet, layer, mark or handle.

    measure(R, *, member_types=None, ring_rule=None, dxf_path=None) -> {"method", "v2", "sheets", "beam_items",
        "supersedes", "rings", "sections", "upstands", "necks", "not_present", "side_effects", ...}
    apply(R, v3) -> the route's item list with the V2 ledger and the V3 beam / ring / upstand / neck changes applied
"""

from __future__ import annotations

import math
from collections import defaultdict

from engine.source import beam_binding_v2 as BV2
from engine.source import cad_heal as CH
from engine.source import column_schedule_text_rows as TR
from engine.source import concrete_ledger_v2 as V2
from engine.source import drawing_model as DM
from engine.source import generic_route as GR
from engine.source import member_detection as MD
from engine.source import provisional_estimate as PE

METHOD = "CONCRETE_LEDGER_V3"
RULES = V2.RULES + ("OWNER-Q-16", "OWNER-Q-21", "OWNER-Q-44")
BEAM_ITEM_FAMILIES = ("BEAMS", "GROUND_BEAMS")
PLAN_ROLES = ("SLAB_PLAN", "GROUND_BEAM_PLAN")
ROUTE_TOL_M = 0.012           # generic_route.detect: tol = 0.012 / u (the route's drawing tolerance)
MIN_PIECE_M = 0.05            # generic_route.detect: split_at_supports(..., 0.05 / u, touch)
MIN_FACE_M = 0.3              # generic_route.detect: beam_bands(..., 0.3 / u)
TOUCH_M2 = 1e-4               # generic_route.detect: (1e-2 / u) ** 2 when touch_tolerance is on
WIDTH_TOL_M = 0.015           # the binder's width tolerance (bind_marks, ring_beams, upstand_lines)


class LedgerError(ValueError):
    pass


def _r(v, n=6):
    return None if v is None else round(v, n)


# ====================================================================== 1. replay of the route's beam pipeline
def _widths_of(S):
    w = defaultdict(set)
    for r in S["rows"]:
        if r["dims_m"].get("W"):
            w[(r["family"], r["mark"])].add(r["dims_m"]["W"])
    return {k: tuple(sorted(v)) for k, v in w.items()}


def sheet_inputs(D, intake, sid):
    """The inputs generic_route.detect gave the beam functions on one plan sheet, rebuilt from the route's records:
    healed entities, edge layers, column boxes, marks, the bands BEFORE the support split."""
    rec = D["sheets"][sid]
    sh = rec["sheet"]
    u, lib, S = D["unit_m"], D["lib"], D["schedule"]
    opt = D.get("options") or {}
    E = DM.sheet_entities(D["model"], intake, sid)
    raw = E
    fams = MD.BEAM_FAMILIES if sh["role"] == "SLAB_PLAN" else MD.GROUND_FAMILIES
    widths_m = list(rec.get("widths_m") or [])
    widths = [w / u for w in widths_m]
    lays = set(rec.get("edge_layers") or [])
    cols = [tuple(c) for c in rec.get("column_boxes") or []]
    bm = [m for m in GR._schedule_marks(E["texts"], lib) if m["family"] in fams]
    if lays:                                   # the same healing as detect (cad_heal, frozen)
        segs, _ = CH.merge_collinear(E["segments"], lays, gap=CH.GAP_M / u, off_tol=0.5e-3 / u)
        tgt = [(p[j], p[(j + 1) % 4]) for c in cols for p in [MD.box_poly(c)] for j in range(4)]
        wide = CH.WIDE_SNAP_FRACTION * min(widths_m) / u if widths_m else None
        segs, _ = CH.extend_dangling(segs, lays, tgt, snap=CH.SNAP_M / u, eps=0.5e-3 / u, wide_snap=wide)
        E = dict(E, segments=segs)
    tol = ROUTE_TOL_M / u
    pre, _ = MD.beam_bands(E, lays, widths, tol, MIN_FACE_M / u) if lays else ([], [])
    touch = (TOUCH_M2 ** 0.5 / u) ** 2 if opt.get("touch_tolerance") else 0.0
    sup = cols + [tuple(b) for b in rec.get("column_presence") or []
                  if not any(max(abs(b[k] - c[k]) for k in range(4)) <= tol for c in cols)]
    return {"E": E, "raw": raw, "lays": lays, "cols": cols, "bm": bm, "pre": pre, "touch": touch, "tol": tol,
            "widths_of": _widths_of(S), "supports": sup, "u": u}


def _band_sig(b):
    return (b["band_id"], round(b.get("t0", 0.0), 6), round(b.get("t1", 0.0), 6))


def _single_face(I, rec, bands, bound):
    """generic_route.detect's single-face step on the given bands / marks (bound is changed in place, as there)."""
    slab = rec.get("slab")
    sf_b, sf_m = MD.single_face_beams(I["E"], I["lays"], bound, I["widths_of"], bands, slab["faces"] if slab else [],
                                      I["cols"], I["u"]) if I["lays"] else ([], {})
    if not sf_b:
        return bands
    for k, b in enumerate(sf_b, 1):
        b["band_id"] = f"BANDSF{k:02d}"
    pieces = MD.split_at_supports(sf_b, I["cols"], MIN_PIECE_M / I["u"], I["touch"])
    for mi, v in sf_m.items():
        ids = {b["band_id"] for b in v["bands"]}
        own = [p_["band_id"] for p_ in pieces if p_["parent"] in ids]
        bound[mi] = dict(bound[mi], state="BOUND_SINGLE_FACE", band=own[0] if own else None, bands=own,
                         single_face=v["face"])
    return bands + pieces


def replay_sheet(D, intake, sid, conv=None):
    """{sheet, storey, state REPLAYED / REPLAY_MISMATCH / NO_BANDS, v1 / v2 records, planted, changes}."""
    rec = D["sheets"][sid]
    I = sheet_inputs(D, intake, sid)
    u, lib = I["u"], D["lib"]
    out = {"sheet": sid, "storey": rec["sheet"].get("storey"), "role": rec["sheet"]["role"]}
    if not I["lays"]:
        return dict(out, state="NO_BANDS")
    min_piece = MIN_PIECE_M / u
    # V1 replay: must give the route's own bands and marks
    b1 = MD.split_at_supports(I["pre"], I["cols"], min_piece, I["touch"])
    m1 = MD.bind_marks(b1, I["bm"], I["widths_of"], u)
    i1 = MD.inherit_sections(b1, m1, lib, 1.0 / u, supports=I["supports"])
    b1 = _single_face(I, rec, b1, m1)
    same_b = [_band_sig(b) for b in b1] == [_band_sig(b) for b in rec.get("bands") or []]
    same_m = [(m["mark"], m["state"], tuple(m.get("bands") or [])) for m in m1] == \
        [(m["mark"], m["state"], tuple(m.get("bands") or [])) for m in rec.get("marks") or []]
    same_i = [(m["mark"], m["state"], tuple(m.get("bands") or [])) for m in i1] == \
        [(m["mark"], m["state"], tuple(m.get("bands") or [])) for m in rec.get("inherited") or []]
    if not (same_b and same_m and same_i):
        return dict(out, state="REPLAY_MISMATCH", bands_same=same_b, marks_same=same_m, inherited_same=same_i)
    # V2
    pcl = {}
    if conv is not None and "PLANTED_COLUMN_LABELS" in conv.items:
        pcl = conv["PLANTED_COLUMN_LABELS"] or {}      # as generic_route._planted_column_items
    pattern = pcl.get("label_pattern") or BV2.PLANTED_LABEL
    unit = float(pcl.get("label_unit_m") or BV2.PLANTED_LABEL_UNIT_M)
    segs = [s for s in I["raw"]["segments"] if s["layer"] not in I["lays"]]
    box = rec["sheet"]["box"]
    circles = [c for c in intake.get("circles", []) if box[0] <= c["c"][0] <= box[2] and box[1] <= c["c"][1] <= box[3]]
    planted = BV2.planted_columns(rec.get("texts") or I["E"]["texts"], segs, circles, I["cols"], u, I["tol"],
                                  label_pattern=pattern, label_unit_m=unit)
    b2 = BV2.split_at_supports_v2(I["pre"], I["cols"], min_piece, I["touch"], planted=planted, tol_native=I["tol"])
    m2 = BV2.bind_marks_v2(b2, I["bm"], I["widths_of"], u)
    i2 = MD.inherit_sections(b2, m2, lib, 1.0 / u, supports=I["supports"])
    b2 = _single_face(I, rec, b2, m2)
    t = (rec.get("slab") or {}).get("uniform_t_m")
    beams2 = MD.beam_quantities(b2, m2 + i2, lib, [], u, t)
    marks_changed = [{"mark": a["mark"], "v1": [a["state"], a.get("bands") or a.get("candidates")],
                      "v2": [b["state"], b.get("bands") or b.get("candidates")]}
                     for a, b in zip(m1, m2) if (a["state"], a.get("bands")) != (b["state"], b.get("bands"))]
    return dict(out, state="REPLAYED", planted=[{k: p.get(k) for k in ("label", "state", "link", "drawn_m",
                                                                       "section_m")} for p in planted],
                bands_v1=len(b1), bands_v2=len(b2), marks_changed=marks_changed,
                rec_v2=dict(rec, bands=b2, marks=m2, inherited=i2, beams=beams2,
                            single_face_bands=[b["band_id"] for b in b2 if b.get("rule") == "SINGLE_FACE_INFERRED"]),
                inputs=I)


# ====================================================================== 2. rings and 3. upstands
def rings_of(D, intake, rp, ring_rule=None):
    """ring records of one replayed sheet (BEAM_BINDING_V2.ring_beams on its edge-layer arcs and circles)."""
    rec, I = D["sheets"][rp["sheet"]], rp["inputs"]
    box = rec["sheet"]["box"]
    inside = lambda p: box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]      # noqa: E731
    arcs = [a for a in intake.get("arcs", []) if a["layer"] in I["lays"] and inside(a["c"])]
    circ = [c for c in intake.get("circles", []) if c["layer"] in I["lays"] and inside(c["c"])]
    if not arcs and not circ:
        return []
    fb = None
    if ring_rule and rp["role"] == "SLAB_PLAN" and ring_rule.get("storey", rp["storey"]) == rp["storey"]:
        fb = {"family": ring_rule["family"], "mark": ring_rule["mark"], "basis": ring_rule.get("basis", "owner rule")}
    v2 = rp["rec_v2"]
    return BV2.ring_beams(arcs, circ, v2["bands"], I["cols"], v2["marks"], I["widths_of"], D["lib"], I["u"], I["tol"],
                          fallback=fb, parent_bands=I["pre"])


def read_section_drawing(dxf_path):
    """every linear DIMENSION {axis, lo, hi, shown, p1, p2} (shown = the printed text, or the measurement x DIMLFAC:
    entity override > style > header) and every LWPOLYLINE outline of >= 4 vertices, in drawing units."""
    import ezdxf
    doc = ezdxf.readfile(dxf_path)
    hdr = doc.header.get("$DIMLFAC", 1.0) or 1.0
    dims, outl = [], []
    for e in doc.modelspace():
        t = e.dxftype()
        if t == "DIMENSION" and (e.dimtype & 7) in (0, 1):
            ov = e.override().get("dimlfac")
            st = e.get_dim_style().dxf.get("dimlfac")
            lfac = ov if ov not in (None, 0) else st if st not in (None, 0) else hdr
            ang = float(e.dxf.get("angle", 0.0) or 0.0) % 180.0
            p1, p2 = e.dxf.defpoint2, e.dxf.defpoint3
            if (e.dimtype & 7) == 1:
                ang = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0])) % 180.0
            axis = "x" if min(ang, 180 - ang) < 1e-6 else "y" if abs(ang - 90.0) < 1e-6 else None
            if axis is None:
                continue
            k = 0 if axis == "x" else 1
            txt = (e.dxf.get("text", "") or "").strip()
            shown = float(txt) if txt.replace(".", "", 1).isdigit() else e.get_measurement() * lfac
            dims.append({"axis": axis, "lo": min(p1[k], p2[k]), "hi": max(p1[k], p2[k]), "shown": round(shown, 6),
                         "p1": (p1[0], p1[1]), "p2": (p2[0], p2[1])})
        elif t == "LWPOLYLINE":
            pts = [(p[0], p[1]) for p in e.vertices_in_wcs()]       # OCS -> WCS: a mirrored outline (extrusion -Z)
            if len(pts) >= 4:
                outl.append({"handle": e.dxf.handle, "layer": e.dxf.layer, "pts": pts})
    return dims, outl


def _shift(dims, outlines, intake):
    lo = intake.get("local_origin")
    if not lo:
        return dims, outlines
    ox, oy = lo["x"], lo["y"]
    k = {"x": ox, "y": oy}
    dims = [dict(d, lo=d["lo"] - k[d["axis"]], hi=d["hi"] - k[d["axis"]], p1=(d["p1"][0] - ox, d["p1"][1] - oy),
                 p2=(d["p2"][0] - ox, d["p2"][1] - oy)) for d in dims]
    outlines = [dict(o, pts=[(x - ox, y - oy) for x, y in o["pts"]]) for o in outlines]
    return dims, outlines


def section_upstands(D, replays, dims, outlines):
    """{letter: {state READ / HELD, why, lines: [{band, rows_fitting_section, profile, upstand}]}} - each printed
    section title -> the dimensioned outline nearest above it (mutual nearest), its cut line found once on the plans,
    the crossed band at the printed width -> upstand_lines."""
    u, lib = D["unit_m"], D["lib"]
    tol = ROUTE_TOL_M / u
    tit = [(BV2.SECTION_TITLE.search((t.get("norm") or t.get("value") or "").replace("%%U", "")), t)
           for t in D["model"]["texts"]]
    tit = [(m.group(1), t) for m, t in tit if m]
    titles = {L for L, _ in tit}
    cuts = {}
    for rp in replays:
        if rp["state"] != "REPLAYED":
            continue
        rec = D["sheets"][rp["sheet"]]
        segs = [s for s in rp["inputs"]["raw"]["segments"]]
        cuts[rp["sheet"]] = BV2.section_cuts(rec.get("texts") or rp["inputs"]["E"]["texts"], segs,
                                             rp["rec_v2"]["bands"], u, edge_layers=rp["inputs"]["lays"], titles=titles)

    def bdist(t, o):
        xs, ys = [p[0] for p in o["pts"]], [p[1] for p in o["pts"]]
        return math.hypot(max(min(xs) - t["x"], 0.0, t["x"] - max(xs)), max(min(ys) - t["y"], 0.0, t["y"] - max(ys)))
    dimmed = []
    for o in outlines:
        on = [d for d in dims if all(any(math.dist(q, p) <= tol for p in o["pts"]) for q in (d["p1"], d["p2"]))]
        if len(on) >= 2:
            dimmed.append((o, on))
    out = {}
    for L, t in tit:
        cand = sorted(((bdist(t, o), k) for k, (o, on) in enumerate(dimmed) if min(p[1] for p in o["pts"]) >= t["y"]))
        if not cand:
            out[L] = {"state": "HELD", "why": "no dimensioned outline above the title"}
            continue
        o, on = dimmed[cand[0][1]]
        if min(tit, key=lambda x: bdist(x[1], o))[1] is not t:
            out[L] = {"state": "HELD", "why": "the nearest outline is nearer to another title"}
            continue
        hit = [(sid, c[L]) for sid, c in cuts.items() if L in c]
        if len(hit) != 1 or hit[0][1]["state"] != "CUT":
            out[L] = {"state": "HELD", "why": f"cut line found on {len(hit)} plans (needs exactly one)" if len(hit) != 1
                      else f"cut line {hit[0][1]['state']} on {hit[0][0]} (two segments carry the letter)"}
            continue
        sid, cut = hit[0]
        rp = next(r for r in replays if r["sheet"] == sid)
        bands = rp["rec_v2"]["bands"]
        by = {b["band_id"]: b for b in bands}
        rows = [(fam, mk, r) for (fam, mk), r in lib.items() if fam in MD.BEAM_FAMILIES + MD.GROUND_FAMILIES and r]
        res = {}
        for bid in cut["bands"]:
            w = by[bid]["width_native"] * u
            for fam, mk, r in rows:
                if abs((r["dims_m"].get("W") or 0) - w) > WIDTH_TOL_M:
                    continue
                p = BV2.section_profile(o["pts"], on, r["dims_m"]["W"], r["dims_m"].get("H"), tol)
                # a profile read in full, or one whose beam is printed at this width but whose upstand is drawn with
                # an unprinted size: the latter becomes a HELD upstand line (listed, never 0)
                drawn_up = p["state"] == "HELD" and p.get("upstand") is not None
                if (p["state"] == "PRINTED" or drawn_up) and p.get("beam_w_m") is not None and \
                        abs(p["beam_w_m"] - w) <= WIDTH_TOL_M:
                    x = res.setdefault(bid, {"band": bid, "rows_fitting_section": [], "profile": p,
                                             "upstand": BV2.upstand_lines(p, cut, bands, u, section=f"{L}-{L}")})
                    x["rows_fitting_section"].append(mk)
        if not res:
            out[L] = {"state": "HELD", "sheet": sid, "why": "no crossed band matches a printed profile"}
            continue
        out[L] = {"state": "READ", "sheet": sid, "storey": rp["storey"], "lines": list(res.values())}
    return out


# ====================================================================== 4. neck-only column types
def neck_census(D, intake):
    """SCHEDULE_TEXT_ROWS_V1 on the route's intake -> classify() lines (one per changed column / neck occurrence)."""
    ext = TR.read(intake)
    return TR.classify(D, ext), ext


# ====================================================================== items
def _beam_item(common, cid, *, base, lo, hi, formula, assumptions, support, conf, blocker=""):
    return PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=lo, base=base, high=hi, formula=formula,
                   assumptions=assumptions, support=support, confidence=conf, blocker=blocker, **common)


def _ring_items(rp, rings, conv, src):
    st = rp["storey"]
    t = (rp["rec_v2"].get("slab") or {}).get("uniform_t_m")
    items, sup = [], []
    for k, r in enumerate(rings, 1):
        if r["state"] not in ("PRINTED_MARK", "OWNER_RULE"):
            continue
        W, H = r["section_m"]
        net = r["net_plan_m2"]
        cid = f"BEAMS:{st}:RING{k:02d}"
        vals = {"TOTAL_DEPTH": net * H, "BELOW_SLAB": net * (H + t) if t is not None else net * H}
        lo, base, hi = PE.by_choice(conv, "BEAM_DEPTH_READING", vals)
        common = dict(component_id=cid, trade="CONCRETE", family="BEAMS", storey=st,
                      source=f"{src} {rp['sheet']} ring faces r {r['r_inner_m']:.4f} / {r['r_outer_m']:.4f} m; mark "
                             f"{r['mark']} ({'printed on the ring' if r['state'] == 'PRINTED_MARK' else 'owner rule: ' + str(r.get('basis_note'))}), "
                             f"{METHOD}",
                      dimensions={"method": METHOD, "basis": r["state"], "mark": r["mark"], "width_m": W, "depth_m": H,
                                  "r_inner_m": r["r_inner_m"], "r_outer_m": r["r_outer_m"],
                                  "annulus_m2": r["annulus_m2"], "owned_by_others_m2": r["owned_by_others_m2"],
                                  "net_plan_m2": net, "pieces": r.get("pieces"), "arc_bands": r["arc_bands"]},
                      double_count_risk="the part of the annulus inside straight beams and columns is theirs (deducted)"
                                        "; replaces the ring's arc-band items")
        items.append(_beam_item(common, cid, base=base, lo=lo, hi=hi, formula=r["formula"] + " | x (H + t)",
                                assumptions=["BEAM_DEPTH_READING"], support="CONVENTION_ONLY",
                                conf="MEDIUM" if r["state"] == "PRINTED_MARK" else "LOW",
                                blocker="BEAM_DEPTH_CONVENTION"))
        sup.extend(f"BEAMS:{st}:{b}" for b in r["arc_bands"])
    return items, sup


def _upstand_item(L, sec, ln, conv, src):
    up = ln["upstand"]
    st = sec["storey"]
    cid = f"BEAMS:{st}:UPSTAND:{L}:{ln['band']}"
    common = dict(component_id=cid, trade="CONCRETE", family="BEAMS", storey=st, part="UPSTAND",
                  source=f"{src} SECTION {L}-{L} printed profile; cut line on {sec['sheet']} across {ln['band']}, "
                         f"{METHOD}",
                  dimensions={"method": METHOD, "section": f"{L}-{L}", "band": ln["band"], "w_m": up.get("w_m"),
                              "h_m": up.get("h_m"), "length_m": up.get("length_m"), "side": up.get("side"),
                              "rows_fitting_section": ln["rows_fitting_section"]},
                  double_count_risk="above the beam's scheduled depth (the section prints the beam and the upstand "
                                    "separately); not in the slab")
    if up["state"] == "MEASURED" and "PRINTED_DIMENSION_NOTES" in conv.items:
        v = up["volume_m3"]
        return PE.item(item_id=f"P-C:{cid}", category="PROVISIONAL", low=v, base=v, high=v, formula=up["formula"],
                       assumptions=["PRINTED_DIMENSION_NOTES"], support="SOURCE_COMPLETE_UNREVIEWED",
                       confidence="MEDIUM", **common)
    why = up.get("why") or ("the conventions do not admit printed dimensions" if up["state"] == "MEASURED"
                            else up["state"])
    return PE.item(item_id=f"U-C:{cid}", category="UNRESOLVED", support="NO_GEOMETRY", confidence="LOW",
                   blocker=f"UPSTAND_HELD: {why}", expression="printed upstand w x h x clear span", **common)


def _neck_items(R_items, necks, src):
    """(new items, superseded ids, not_present records): CN-like column occurrences NOT_PRESENT; necks re-held with
    their printed section."""
    by_member = defaultdict(list)
    for ln in necks:
        by_member[ln["member_id"]].append(ln)
    new, sup, gone = [], [], []
    for it in R_items:
        if it["trade"] != "CONCRETE":
            continue
        cid = it["component_id"]
        # classify() names the column occurrence (member_id = the column component id); a neck item's component
        # is NECK:<that id>
        mid = cid[len("NECK:"):] if cid.startswith("NECK:") else cid if cid.startswith("COL:") else None
        lns = by_member.get(mid) or []
        for ln in lns:
            if cid.startswith("COL:") and ln["role"] == "COLUMN_PLAN" and ln["status"] == "NOT_PRESENT" and \
                    it["category"] == "UNRESOLVED":
                sup.append(it["item_id"])
                gone.append({"item_id": it["item_id"], "component_id": cid, "status": "NOT_PRESENT", "code": ln["code"],
                             "why": ln["why"], "struck": ln.get("struck")})
            elif cid.startswith("NECK:") and ln["role"] == "FOUNDATION_PLAN" and ln["code"] == \
                    "FOUNDATION_DATUM_NOT_VERIFIED" and it["category"] == "UNRESOLVED":
                sup.append(it["item_id"])
                d = dict(it["dimensions"] or {}, method=METHOD, section_m=ln["section_m"], section_m2=ln["section_m2"],
                         section_source="schedule row typed as text (SCHEDULE_TEXT_ROWS_V1)")
                new.append(dict(it, dimensions=d, blocker="FOUNDATION_DATUM_NOT_VERIFIED: neck section printed "
                                                          f"{ln['section_m'][0]:g} x {ln['section_m'][1]:g} m; the "
                                                          "height waits on the founding level (owner Q-21 = C)",
                                source=it["source"] + f"; section from {METHOD}"))
    return new, sup, gone


# ====================================================================== the pass
def _sig(i):
    return (i["item_id"], i["category"], _r(i.get("base")), _r(i.get("low")), _r(i.get("high")), i.get("blocker"))


def measure(R, *, member_types=None, ring_rule=None, dxf_path=None):
    g = R.get("generic") or {}
    D, intake = g.get("D"), g.get("intake")
    if not D or intake is None:
        raise LedgerError("measure needs a route-G result (tools/urban_boq_m2.compute route G)")
    conv = R["conv"]
    if ring_rule is not None and not (ring_rule.get("family") and ring_rule.get("mark") and ring_rule.get("basis")):
        raise LedgerError("a ring rule names its family, mark and basis (the owner answer it comes from)")
    src = next((i.get("file") for i in R.get("inputs") or () if i.get("kind") == "DXF"), None) or "drawing"
    if dxf_path is None:
        dxf_path = next((i.get("path") for i in R.get("inputs") or () if i.get("kind") == "DXF" and i.get("path")),
                        None)
    v2 = V2.measure(R, member_types=member_types) if g.get("completeness") else None
    out = {"method": METHOD, "rules": list(RULES), "v2": v2, "sheets": [], "beam_items": [], "supersedes": [],
           "rings": [], "sections": {}, "upstands": [], "necks": [], "not_present": [], "side_effects": [],
           "ring_rule": ring_rule}
    replays = [replay_sheet(D, intake, sid, conv) for sid, rec in sorted(D["sheets"].items())
               if rec["sheet"]["role"] in PLAN_ROLES and "beams" in rec]
    heights = GR.storey_heights(conv)
    ev, arch = g.get("evidence"), g.get("arch")
    base_items, _, _ = GR.items_from(D, conv, heights, evidence=ev, arch=arch)
    route_ids = {i["item_id"]: i for i in R["items"]}
    if any(i["item_id"] not in route_ids or _sig(route_ids[i["item_id"]]) != _sig(i) for i in base_items):
        raise LedgerError("items_from on the route's records does not reproduce the route's items")
    D2 = dict(D, sheets={sid: (next((rp["rec_v2"] for rp in replays if rp["sheet"] == sid and
                                     rp["state"] == "REPLAYED"), None) or dict(rec))
                         for sid, rec in D["sheets"].items()})
    new_items, _, _ = GR.items_from(D2, conv, heights, evidence=ev, arch=arch)
    is_beam = lambda i: i["trade"] == "CONCRETE" and i["family"] in BEAM_ITEM_FAMILIES   # noqa: E731
    old_beam = [i for i in base_items if is_beam(i)]
    new_beam = [i for i in new_items if is_beam(i)]
    old_other = {i["item_id"]: _sig(i) for i in base_items if i["trade"] == "CONCRETE" and not is_beam(i)}
    new_other = {i["item_id"]: _sig(i) for i in new_items if i["trade"] == "CONCRETE" and not is_beam(i)}
    for k in sorted(set(old_other) | set(new_other)):
        if old_other.get(k) != new_other.get(k):
            out["side_effects"].append({"item_id": k, "v1": old_other.get(k), "v2_binding": new_other.get(k),
                                        "kept": "v1 (only beam items are replaced)"})
    old_sig = {i["item_id"]: _sig(i) for i in old_beam}
    new_sig = {i["item_id"]: _sig(i) for i in new_beam}
    changed_ids = sorted(k for k in set(old_sig) | set(new_sig) if old_sig.get(k) != new_sig.get(k))
    out["supersedes"].extend(k for k in changed_ids if k in old_sig)
    out["beam_items"].extend(i for i in new_beam if i["item_id"] in changed_ids)
    for rp in replays:
        out["sheets"].append({k: v for k, v in rp.items() if k not in ("rec_v2", "inputs")})
    # rings
    for rp in replays:
        if rp["state"] != "REPLAYED":
            continue
        rings = rings_of(D, intake, rp, ring_rule)
        items, sup_c = _ring_items(rp, rings, conv, src)
        for r in rings:
            out["rings"].append(dict({k: v for k, v in r.items() if k != "centre"}, sheet=rp["sheet"],
                                     storey=rp["storey"]))
        if items:
            cur = {i["component_id"]: i for i in new_beam}
            gone = [cur[c]["item_id"] for c in sup_c if c in cur]
            out["beam_items"] = [i for i in out["beam_items"] if i["item_id"] not in gone]
            out["supersedes"].extend(x for x in gone if x in old_sig)
            out["beam_items"].extend(items)
    # upstands
    if dxf_path:
        dims, outl = _shift(*read_section_drawing(dxf_path), intake)
        secs = section_upstands(D, replays, dims, outl)
        for L, sec in sorted(secs.items()):
            out["sections"][L] = {k: v for k, v in sec.items() if k != "lines"}
            for ln in sec.get("lines") or ():
                it = _upstand_item(L, sec, ln, conv, src)
                out["upstands"].append(dict(ln["upstand"], band=ln["band"], section=f"{L}-{L}", sheet=sec["sheet"],
                                            item_id=it["item_id"], rows_fitting_section=ln["rows_fitting_section"]))
                out["beam_items"].append(it)
    else:
        out["sections"] = {"*": {"state": "NOT_READ", "why": "no structural DXF path to read the section views"}}
    # necks
    necks, _ = neck_census(D, intake)
    out["necks"] = necks
    n_new, n_sup, gone = _neck_items(R["items"], necks, src)
    out["neck_items"] = n_new
    out["supersedes"].extend(n_sup)
    out["not_present"] = gone
    out["supersedes"] = list(dict.fromkeys(out["supersedes"]))
    return out


def apply(R, v3):
    """the route's items (after the V2 ledger, when it ran) with every superseded item replaced: beam items in the
    place of the first superseded beam item of their sheet family, neck items in place, new rings / upstands after
    the beams, NOT_PRESENT items removed (listed in v3['not_present'])."""
    items = V2.apply(R, v3["v2"]) if v3.get("v2") else list(R["items"])
    gone = set(v3["supersedes"])
    neck_by_id = {i["item_id"]: i for i in v3.get("neck_items") or ()}
    out, placed = [], False
    for it in items:
        if it["item_id"] not in gone:
            out.append(it)
            continue
        if it["item_id"] in neck_by_id:
            out.append(neck_by_id[it["item_id"]])
            continue
        if not placed and it["trade"] == "CONCRETE" and it["family"] in BEAM_ITEM_FAMILIES:
            out.extend(v3["beam_items"])
            placed = True
    if not placed:
        out.extend(v3["beam_items"])
    PE.check(out, R.get("conv"))
    return out


def policy_record():
    return {"policy": METHOD, "rules": list(RULES), "builds_on": [V2.METHOD, BV2.POLICY_ID, TR.POLICY_ID],
            "frozen_untouched": ["engine/source/generic_route.py", "engine/source/member_detection.py",
                                 "engine/source/concrete_ledger_v2.py", "engine/source/beam_binding_v2.py"],
            "rule": "the route's beam pipeline replayed (V1 must reproduce the route) and re-run with BEAM_BINDING_V2; "
                    "beam items rebuilt by the route's own items_from; rings only from a printed mark or a passed "
                    "owner rule; upstands only from a printed section bound to its cut line; neck-only column types "
                    "NOT_PRESENT on the column plan, their necks held on the founding datum; missing never 0"}
