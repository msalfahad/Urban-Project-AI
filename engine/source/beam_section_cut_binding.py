"""BEAM SECTION CUT BINDING V1 (T-102): a printed beam section settles the ONE beam span its cut line crosses.

New policy, NOT wired into any released method (no method version calls it; no released run can change).
It reads, never edits, MEMBER_DETECTION_V1 (engine/source/member_detection.py, frozen) and BEAM_BINDING_V2
(engine/source/beam_binding_v2.py, T-085): `section_cuts` (cut line + view arrows + letter) and `section_profile`
(beam rectangle and upstand of a dimensioned rectilinear outline) are reused as they are.

What it adds (BEAM_BINDING_V2 reads sections only for the upstand line):
1. Section drawing per sheet. Each title 'SECTION X-X' on a sheet is paired with the dimensioned outline nearest to it
   on the SAME sheet, lying wholly on the far side of the title's baseline in the title's own frame (titles turned
   by 90 / 180 / 270 deg are read in their frame), and the pairing must be mutual. A letter titled twice on one sheet,
   an outline nearer to another title, or no outline -> HELD. A section drawn on another sheet is never borrowed.
2. Printed size, unit and scale from the drawing. The beam is the widest strip stack of the outline (V2 rule); the
   printed width and depth are the DIMENSION values shown on it (override text > the dimension's own block text >
   measurement x DIMLFAC). The printed unit is proven by the plan: printed width x unit = the drawn width of the span
   the cut crosses (cm, mm or m, within the binder's width tolerance). Every used value needs its own dimension at
   one drawing scale (V2 `section_profile`).
3. One span. Of the straight spans the cut line crosses, exactly one may have the printed width: that span is bound.
   None -> HELD (NO_SPAN_AT_PRINTED_WIDTH); two or more -> HELD (CUT_CROSSES_SEVERAL_SPANS). The other spans the cut
   crosses are listed with their width: the section neither shows nor excludes them (owner Q-61 C(5)).
4. Schedule check. The span's mark (a printed mark bound to it, or the mark it would take along its line, which the
   route only proposes) must have a schedule row equal to the printed width AND depth; a row that differs -> HELD
   CONFLICT with both volumes (owner Q-61 C(1): never pick one because it is printed); two marks on the span -> HELD.
   No mark at all -> the printed section alone settles the span (DRAWING-VERIFIED, basis SECTION_ONLY), because it
   is a printed size on exactly that span; a neighbour's size is never copied (owner Q-16 A).
5. Quantity. Released m3 = printed width x printed depth x the span's clear length (the route G basis "gross B x clear
   L x D"; a caller may pass the route's own net plan area instead, recorded as the basis). Held spans keep their
   candidate volumes; missing never becomes 0 (UP-QTY-STATUS-001). The printed upstand is listed through V2
   `upstand_lines`, never added to the span.

Rules: owner Q-16 A, Q-17 A (status DRAWING-VERIFIED), Q-61 C, UP-KB-PREC-001 (a printed value outranks a convention),
URBAN-BEAM-TYPE-FROM-SCHEDULE-LENGTH-FROM-PLAN@v1, UP-QTY-STATUS-001. Project-agnostic: no layer names, no
coordinates; tolerances are the caller's (drawing tolerance, binder width tolerance). Stdlib only (+ ezdxf in the two
optional readers).
"""

from __future__ import annotations

import math
import re

from engine.source import beam_binding_v2 as BV2
from engine.source import member_detection as MD

POLICY_ID = "BEAM_SECTION_CUT_BINDING_V1"
STATUS_RELEASED = "DRAWING-VERIFIED"
UNITS_M = (0.01, 0.001, 1.0)                           # cm, mm, m: the only printed units accepted
_CTRL = re.compile(r"%%[UuOoKk]|\\[A-Za-z][^;]*;|[{}]")
_NUM = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*$")


# ------------------------------------------------------------------------------------------------ text, frames
def norm_text(s):
    """the printed words of a TEXT / MTEXT value: underline / overline codes and MTEXT formatting removed"""
    return re.sub(r"\s+", " ", _CTRL.sub("", s or "")).strip().upper()


def section_titles(texts):
    """[{letter, x, y, rotation, id}] for every 'SECTION X-X' text (V2 SECTION_TITLE)."""
    out = []
    for t in texts:
        m = BV2.SECTION_TITLE.search(norm_text(t.get("value") or t.get("norm") or ""))
        if m:
            out.append({"letter": m.group(1), "x": float(t["x"]), "y": float(t["y"]),
                        "rotation": float(t.get("rotation") or 0.0), "id": t.get("id")})
    return out


def _quarter(rot_deg):
    """0 / 90 / 180 / 270 for a title turned by a multiple of 90 deg (1 deg tolerance), else None"""
    r = rot_deg % 360.0
    for q in (0, 90, 180, 270, 360):
        if abs(r - q) <= 1.0:
            return q % 360
    return None


def _to_frame(p, origin, q):
    """a point in the frame of a title at origin turned by q deg (x along the title's text)"""
    x, y = p[0] - origin[0], p[1] - origin[1]
    if q == 0:
        return (x, y)
    if q == 90:
        return (y, -x)
    if q == 180:
        return (-x, -y)
    return (-y, x)


def _dims_to_frame(dims, origin, q):
    """dimension records turned into the title frame: {axis, lo, hi, shown, p1, p2, id}"""
    out = []
    for d in dims:
        p1, p2 = _to_frame(d["p1"], origin, q), _to_frame(d["p2"], origin, q)
        axis = d["axis"] if q in (0, 180) else {"x": "y", "y": "x"}[d["axis"]]
        k = 0 if axis == "x" else 1
        out.append(dict(d, axis=axis, p1=p1, p2=p2, lo=min(p1[k], p2[k]), hi=max(p1[k], p2[k])))
    return out


def _inside(p, box):
    return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]


# ------------------------------------------------------------------------------------------ section drawings
def dimensioned_outlines(outlines, dims, tol):
    """[(outline, its dimensions)]: a dimension belongs to an outline when both its extension origins are outline
    vertices (drawing tolerance); an outline with no such dimension is no dimensioned section (one with a single
    dimension is kept, so its missing value is reported, not hidden)."""
    out = []
    for o in outlines:
        on = [d for d in dims if all(any(math.dist(q, p) <= tol for p in o["pts"]) for q in (d["p1"], d["p2"]))]
        if on:
            out.append((o, on))
    return out


def _box_dist(p, pts):
    xs, ys = [a[0] for a in pts], [a[1] for a in pts]
    dx = max(min(xs) - p[0], 0.0, p[0] - max(xs))
    dy = max(min(ys) - p[1], 0.0, p[1] - max(ys))
    return math.hypot(dx, dy)


def pair_section_drawings(titles, dimmed, box=None):
    """letter -> {state PAIRED / HELD, title, outline (title frame), dims (title frame), outline_id, why} for the
    titles on one sheet (box: the sheet frame; None = the whole drawing)."""
    on_sheet = [t for t in titles if box is None or _inside((t["x"], t["y"]), box)]
    cand = [(o, on) for o, on in dimmed if box is None or all(_inside(p, box) for p in o["pts"])]
    out = {}
    count = {}
    for t in on_sheet:
        count[t["letter"]] = count.get(t["letter"], 0) + 1
    for t in on_sheet:
        L = t["letter"]
        rec = {"title": f"SECTION {L}-{L}", "title_id": t["id"]}
        if count[L] > 1:
            out[L] = dict(rec, state="HELD", why=f"SECTION {L}-{L} is titled {count[L]} times on this sheet")
            continue
        q = _quarter(t["rotation"])
        if q is None:
            out[L] = dict(rec, state="HELD", why="section title not turned by a multiple of 90 deg")
            continue
        org = (t["x"], t["y"])
        best = []
        for o, on in cand:
            pf = [_to_frame(p, org, q) for p in o["pts"]]
            if min(p[1] for p in pf) < 0.0:            # not wholly on the far side of the title's baseline
                continue
            best.append((_box_dist((0.0, 0.0), pf), o, on, pf))
        if not best:
            out[L] = dict(rec, state="HELD", why="no dimensioned outline beside the title on this sheet")
            continue
        best.sort(key=lambda x: x[0])
        dist, o, on, pf = best[0]
        others = [u for u in on_sheet if u is not t and _box_dist((u["x"], u["y"]), o["pts"]) <
                  _box_dist((t["x"], t["y"]), o["pts"])]
        if others:
            out[L] = dict(rec, state="HELD", why="the nearest outline is nearer to another section title")
            continue
        out[L] = dict(rec, state="PAIRED", outline_id=o.get("id"), outline=pf, dims=_dims_to_frame(on, org, q),
                      rotation=q)
    return out


def printed_numbers(outline, dims, tol):
    """the printed beam width and depth numbers of a section outline in its own frame, unit still unknown:
    {state, shown_w, drawn_w, shown_d, drawn_d, why}. Beam = the widest strip stack (V2 rule)."""
    pts = [tuple(p[:2]) for p in outline]
    if len(pts) > 2 and math.dist(pts[0], pts[-1]) <= tol:
        pts = pts[:-1]
    st = BV2._strips(pts, tol)                         # noqa: SLF001 - the V2 profile rule, reused unchanged
    if not st:
        return {"state": "UNSUPPORTED", "why": "outline is not one rectilinear profile"}
    wmax = max(s[3] - s[2] for s in st)
    beam = [s for s in st if abs((s[3] - s[2]) - wmax) <= tol]
    by0, by1 = min(s[0] for s in beam), max(s[1] for s in beam)
    pw = BV2._printed(dims, "x", beam[0][2], beam[0][3], tol)  # noqa: SLF001
    pd = BV2._printed(dims, "y", by0, by1, tol)        # noqa: SLF001
    if not pw:
        return {"state": "HELD", "why": "beam width not printed on the section"}
    rec = {"shown_w": pw[0][0], "drawn_w": pw[0][1]}
    if not pd:
        return dict(rec, state="HELD", why="beam depth not printed on the section")
    return dict(rec, state="PRINTED", shown_d=pd[0][0], drawn_d=pd[0][1])


def _unit_of(shown, drawn_m, tol_m):
    """the printed unit (0.01 / 0.001 / 1) that makes `shown` the plan's drawn size within tol_m, or None"""
    hits = [u for u in UNITS_M if abs(shown * u - drawn_m) <= tol_m]
    return hits[0] if len(hits) == 1 else None


# ------------------------------------------------------------------------------------------------ binding
def straight_bands_crossed(a, b, bands, angle_tol=12.0):
    """the straight bands the segment a-b crosses face to face at a right angle inside their length (the same test
    as BEAM_BINDING_V2.section_cuts; used to list what each of several same-letter cut lines would cross)"""
    hit = []
    for band in bands:
        if band.get("kind") != "STRAIGHT":
            continue
        if BV2._adiff(BV2._dir(a, b), MD.band_axis_deg(band) + 90.0) > angle_tol:  # noqa: SLF001
            continue
        u, n = band["u"], band["n"]
        na, nb = a[0] * n[0] + a[1] * n[1], b[0] * n[0] + b[1] * n[1]
        lo, hi = sorted((band["lo_off"], band["hi_off"]))
        if not (min(na, nb) <= lo and max(na, nb) >= hi) or nb == na:
            continue
        k = ((lo + hi) / 2 - na) / (nb - na)
        p = (a[0] + k * (b[0] - a[0]), a[1] + k * (b[1] - a[1]))
        if band["t0"] <= p[0] * u[0] + p[1] * u[1] <= band["t1"]:
            hit.append(band)
    return hit


def arc_bands_crossed(a, b, bands):
    """the curved bands whose outline the segment a-b crosses (BEAM_BINDING_V2.section_cuts tests straight bands
    only; a ring of the printed width must still count as a second span)"""
    out = []
    for band in bands:
        if band.get("kind") != "ARC" or not band.get("polygon"):
            continue
        poly = band["polygon"]
        n = len(poly)
        if any(BV2._seg_cross(a, b, poly[i], poly[(i + 1) % n]) is not None for i in range(n)):  # noqa: SLF001
            out.append(band)
    return out


def _marks_by_band(bindings):
    out = {}
    for m in bindings or ():
        for bid in m.get("bands") or ([m["band"]] if m.get("band") else []):
            out.setdefault(bid, set()).add((m["mark"], m.get("state") or ""))
    return out


def bind_sections(*, sheet_id, sheet_box, texts, segments, bands, unit_m, titles_all, dimmed, bindings=(),
                  schedule=None, edge_layers=(), net_plan_m2=None, tol_native, width_tol_m=0.015, angle_tol=12.0):
    """Every section letter on one plan sheet -> one record.

    texts / segments: the sheet's intake records ({value, x, y, rotation, id} / {id, layer, a, b}); bands: the route's
    clear spans (member_detection band dicts, after the support split); titles_all: section_titles() of the whole
    drawing; dimmed: dimensioned_outlines() of the whole drawing; bindings: the route's mark records ({mark, state,
    bands}) incl. the marks proposed along a line (INHERITED_ALONG_LINE); schedule: {mark: (width_m, depth_m)};
    net_plan_m2: optional {band_id: net plan area m2} from the route (else printed width x clear length).
    Returns [{letter, state RELEASED / HELD / LISTED, ...}] - never a silent letter."""
    schedule = schedule or {}
    by = {b["band_id"]: b for b in bands}
    letters_all = {t["letter"] for t in titles_all}
    drawings = pair_section_drawings(titles_all, dimmed, sheet_box)
    cuts = BV2.section_cuts(texts, segments, bands, unit_m, edge_layers=edge_layers, angle_tol=angle_tol,
                            titles=letters_all)
    marks = _marks_by_band(bindings)
    out = []
    for L in sorted(set(cuts) | set(drawings)):
        rec = {"policy": POLICY_ID, "sheet": sheet_id, "letter": L, "section": f"{L}-{L}"}
        cut, drw = cuts.get(L), drawings.get(L)
        if cut is None:
            out.append(dict(rec, state="HELD", reason="CUT_NOT_FOUND",
                            why="section drawing on this sheet but no cut line of this letter crosses a straight "
                                "span here", drawing=drw and drw["state"]))
            continue
        if cut["state"] != "CUT":
            seg_by = {x.get("id"): x for x in segments}
            lines = []
            for sid_ in cut.get("segments") or []:
                sg = seg_by.get(sid_)
                if sg is None:
                    continue
                lines.append({"segment": sid_, "crossed": [
                    {"band": b["band_id"], "kind": b["kind"], "width_m": round(b["width_native"] * unit_m, 6),
                     "marks": sorted(m for m, _ in marks.get(b["band_id"], ()))}
                    for b in straight_bands_crossed(sg["a"], sg["b"], bands, angle_tol)
                    + arc_bands_crossed(sg["a"], sg["b"], bands)]})
            out.append(dict(rec, state="HELD", reason="CUT_AMBIGUOUS",
                            why=f"{len(cut.get('segments') or [])} lines here read as cut lines of this letter"
                                + ("" if drw else "; no SECTION title of this letter on this sheet either"),
                            drawing=drw and drw["state"], cut_lines=lines))
            continue
        crossed = [{"band": bid, "kind": "STRAIGHT", "width_m": round(by[bid]["width_native"] * unit_m, 6),
                    "length_m": round(MD.band_length_native(by[bid]) * unit_m, 6),
                    "marks": sorted(m for m, _ in marks.get(bid, ()))} for bid in cut["bands"] if bid in by]
        crossed += [{"band": b["band_id"], "kind": "ARC", "width_m": round(b["width_native"] * unit_m, 6),
                     "length_m": round(MD.band_length_native(b) * unit_m, 6),
                     "marks": sorted(m for m, _ in marks.get(b["band_id"], ()))}
                    for b in arc_bands_crossed(cut["segment"][1], cut["segment"][2], bands)]
        rec["crossed"] = crossed
        if drw is None:
            out.append(dict(rec, state="HELD", reason="SECTION_NOT_ON_SHEET",
                            why="no SECTION title of this letter on this sheet (a section on another sheet is never "
                                "borrowed)"))
            continue
        if drw["state"] != "PAIRED":
            out.append(dict(rec, state="HELD", reason="SECTION_DRAWING_HELD", why=drw["why"]))
            continue
        rec["section_outline_id"] = drw["outline_id"]
        nums = printed_numbers(drw["outline"], drw["dims"], tol_native)
        if nums["state"] != "PRINTED":
            out.append(dict(rec, state="HELD", reason="SECTION_" + nums["state"], why=nums["why"]))
            continue
        rec["printed"] = {"width": nums["shown_w"], "depth": nums["shown_d"]}
        fit = []
        for c in crossed:
            u = _unit_of(nums["shown_w"], c["width_m"], width_tol_m)
            if u is not None:
                fit.append((c, u))
        if not fit:
            out.append(dict(rec, state="HELD", reason="NO_SPAN_AT_PRINTED_WIDTH",
                            why=f"no crossed span is {nums['shown_w']:g} wide in cm, mm or m"))
            continue
        if len(fit) > 1:
            out.append(dict(rec, state="HELD", reason="CUT_CROSSES_SEVERAL_SPANS",
                            why=f"{len(fit)} crossed spans have the printed width: "
                                + ", ".join(c["band"] for c, _ in fit),
                            candidates=[c["band"] for c, _ in fit]))
            continue
        c, unit = fit[0]
        if c["kind"] == "ARC":
            out.append(dict(rec, state="HELD", reason="ARC_SPAN_NOT_IN_SCOPE", band=c["band"],
                            why="the one span at the printed width is a curved (ring) piece: rings follow owner Q-61 "
                                "C(3), not this binding"))
            continue
        prof = BV2.section_profile(drw["outline"], drw["dims"], nums["shown_w"] * unit, None, tol_native)
        if prof.get("state") != "PRINTED":
            out.append(dict(rec, state="HELD", reason="SECTION_PROFILE_" + prof.get("state", "?"), band=c["band"],
                            why=prof.get("why")))
            continue
        w, d, L_m = prof["beam_w_m"], prof["beam_d_m"], c["length_m"]
        rec.update(band=c["band"], unit_m=unit, scale=prof["scale"], width_m=w, depth_m=d, length_m=L_m)
        others = [x for x in crossed if x is not c]
        rec["not_bound"] = [dict(x, why="width differs from the printed section; this section neither shows nor "
                                        "excludes it") for x in others]
        area = (net_plan_m2 or {}).get(c["band"])
        basis = "route net plan area x printed depth" if area is not None else \
            "printed width x clear length x printed depth (gross B x clear L x D)"
        plan = area if area is not None else w * L_m
        v_sec = round(plan * d, 6)
        rec["upstand"] = BV2.upstand_lines(prof, cut, bands, unit_m, section=f"{L}-{L}", width_tol_m=width_tol_m)
        mk = sorted(marks.get(c["band"], ()))
        names = sorted({m for m, _ in mk})
        rec["marks"] = [{"mark": m, "state": s} for m, s in mk]
        if len(names) > 1:
            out.append(dict(rec, state="HELD", reason="TWO_MARKS_ON_SPAN", candidates_m3={"section": v_sec},
                            why="the span carries " + " / ".join(names) + "; the section prints no mark"))
            continue
        if names:
            row = schedule.get(names[0])
            if row is None:
                out.append(dict(rec, state="HELD", reason="MARK_NOT_IN_SCHEDULE", candidates_m3={"section": v_sec},
                                why=f"mark {names[0]} has no schedule row to check the section against"))
                continue
            sw, sd = row
            if abs(sw - w) > 1e-6 or sd is None or abs(sd - d) > 1e-6:
                v_row = round((area if area is not None and abs(sw - w) <= 1e-6 else sw * L_m) * (sd or 0.0), 6) \
                    if sd is not None else None
                out.append(dict(rec, state="HELD", reason="CONFLICT_SECTION_VS_SCHEDULE",
                                candidates_m3={"section": v_sec, "schedule_row": v_row},
                                why=f"section {L}-{L} prints {w:g} x {d:g} m, schedule row {names[0]} "
                                    f"{sw:g} x {sd if sd is not None else '?'} m (designer RFI; neither is picked)"))
                continue
            check = f"= schedule row {names[0]} {sw:g} x {sd:g} m"
        else:
            check = "SECTION_ONLY: no mark on the span, the printed section alone settles it"
        out.append(dict(rec, state="RELEASED", status=STATUS_RELEASED, volume_m3=v_sec, basis=basis, check=check,
                        formula=f"{plan:.4f} m2 ({basis.split(' x printed depth')[0]}) x {d:g} (printed depth, "
                                f"section {L}-{L}) = {v_sec:.4f} m3"))
    return out


# --------------------------------------------------------------------------------------- optional DXF readers
def _shown(e, lfac):
    txt = (e.dxf.get("text", "") or "").strip()
    if _NUM.match(txt):
        return float(txt), txt
    try:
        blk = e.get_geometry_block()
    except Exception:                                       # noqa: BLE001 - no block: fall back to the measurement
        blk = None
    if blk is not None:
        vals = []
        for b in blk:
            if b.dxftype() in ("TEXT", "MTEXT"):
                s = norm_text(b.plain_text() if b.dxftype() == "MTEXT" else b.dxf.text)
                if _NUM.match(s):
                    vals.append(s)
        if len(vals) == 1:
            return float(vals[0]), vals[0]
    return round(e.get_measurement() * lfac, 6), None


def dimension_records(doc):
    """every linear (rotated / aligned) DIMENSION of the modelspace, axis-parallel only:
    [{id, axis, p1, p2, lo, hi, shown, printed_text}] in drawing units; DIMLFAC = entity override > style > header."""
    hdr = doc.header.get("$DIMLFAC", 1.0) or 1.0
    out = []
    for e in doc.modelspace().query("DIMENSION"):
        if (e.dimtype & 7) not in (0, 1):
            continue
        ov = e.override().get("dimlfac")
        st = e.get_dim_style().dxf.get("dimlfac")
        lfac = ov if ov not in (None, 0) else st if st not in (None, 0) else hdr
        p1, p2 = e.dxf.defpoint2, e.dxf.defpoint3
        ang = float(e.dxf.get("angle", 0.0) or 0.0) % 180.0
        if (e.dimtype & 7) == 1:
            ang = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0])) % 180.0
        axis = "x" if min(ang, 180.0 - ang) < 1e-6 else "y" if abs(ang - 90.0) < 1e-6 else None
        if axis is None:
            continue
        k = 0 if axis == "x" else 1
        shown, txt = _shown(e, lfac)
        out.append({"id": e.dxf.handle, "axis": axis, "p1": (p1[0], p1[1]), "p2": (p2[0], p2[1]),
                    "lo": min(p1[k], p2[k]), "hi": max(p1[k], p2[k]), "shown": shown, "printed_text": txt})
    return out


def outline_records(doc, min_vertices=4):
    """every LWPOLYLINE of the modelspace with at least min_vertices vertices: [{id, layer, pts}]"""
    return [{"id": e.dxf.handle, "layer": e.dxf.layer, "pts": [(p[0], p[1]) for p in e.get_points("xy")]}
            for e in doc.modelspace().query("LWPOLYLINE") if len(e) >= min_vertices]


def policy_record():
    return {"policy": POLICY_ID, "wired": False, "status_released": STATUS_RELEASED,
            "rules": ["Q-16 A", "Q-17 A", "Q-61 C", "UP-KB-PREC-001",
                      "URBAN-BEAM-TYPE-FROM-SCHEDULE-LENGTH-FROM-PLAN@v1", "UP-QTY-STATUS-001"],
            "reuses": ["BEAM_BINDING_V2.section_cuts", "BEAM_BINDING_V2.section_profile",
                       "BEAM_BINDING_V2.upstand_lines", "MEMBER_DETECTION_V1.band_length_native"]}
