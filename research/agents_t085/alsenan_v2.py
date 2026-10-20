"""T-085 read-only diagnostic: BEAM_BINDING_V2 against MEMBER_DETECTION_V1 on a real structural DXF, through the
unchanged route G (tools/urban_boq_m2.compute, the way tools/urban_boq_m9.py arch --structural calls it).

Nothing is wired and nothing is written into the repository. route G runs once with the V1 functions; their inputs on
every slab plan are captured (monkeypatch that passes every call through unchanged) and then re-run twice from the
same inputs: V1 (must reproduce the route's own records, checked) and V2 (planted columns, arc-aware binding). The
printed beam sections are read from the DXF (DIMENSION shown values with their effective DIMLFAC: entity override >
style > header) for the upstand lines.

Usage (Python 3.11 venv, repo root):
  python -I research/agents_t085/alsenan_v2.py <structural.dxf> <conventions.json> <out.json> [--profile P.json]
Prints a summary; out.json holds band ids, marks, states, lengths and volumes (no drawing coordinates)."""
from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.source import beam_binding_v2 as BV2  # noqa: E402
from engine.source import generic_route as GR  # noqa: E402
from engine.source import member_detection as MD  # noqa: E402


def _capture():
    calls = []
    orig_split, orig_bind = MD.split_at_supports, MD.bind_marks

    def split(bands, cols, min_piece, touch=0.0):
        out = orig_split(bands, cols, min_piece, touch)
        calls.append({"kind": "split", "bands": bands, "cols": cols, "min_piece": min_piece, "touch": touch,
                      "out": out})
        return out

    def bind(bands, bm, widths_of, u, *a, **k):
        out = orig_bind(bands, bm, widths_of, u, *a, **k)
        calls.append({"kind": "bind", "bands": bands, "bm": bm, "widths_of": widths_of, "out": out})
        return out
    MD.split_at_supports, MD.bind_marks = split, bind
    return calls, (orig_split, orig_bind)


def _dims_and_outlines(dxf):
    """every linear DIMENSION as {axis, lo, hi, shown} and every open/closed LWPOLYLINE outline, in drawing units"""
    import ezdxf
    doc = ezdxf.readfile(dxf)
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
            if (e.dimtype & 7) == 1:                       # aligned: its own direction
                ang = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0])) % 180.0
            axis = "x" if min(ang, 180 - ang) < 1e-6 else "y" if abs(ang - 90.0) < 1e-6 else None
            if axis is None:
                continue
            k = 0 if axis == "x" else 1
            txt = (e.dxf.get("text", "") or "").strip()
            shown = float(txt) if txt.replace(".", "", 1).isdigit() else e.get_measurement() * lfac
            dims.append({"axis": axis, "lo": min(p1[k], p2[k]), "hi": max(p1[k], p2[k]), "shown": round(shown, 6),
                         "handle": e.dxf.handle, "p1": (p1[0], p1[1]), "p2": (p2[0], p2[1])})
        elif t == "LWPOLYLINE":
            pts = [(p[0], p[1]) for p in e.get_points("xy")]
            if len(pts) >= 4:
                outl.append({"handle": e.dxf.handle, "layer": e.dxf.layer, "pts": pts})
    return dims, outl


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    prof, ring_fb = None, None
    if "--ring-fallback" in argv:                       # FAMILY:MARK:basis (an owner answer for rings with no mark)
        i = argv.index("--ring-fallback")
        fam, mk, st_, basis = argv[i + 1].split(":", 3)    # FAMILY:MARK:STOREY:basis
        ring_fb = {"family": fam, "mark": mk, "storey": st_, "basis": basis}
        del argv[i:i + 2]
    if "--profile" in argv:
        i = argv.index("--profile")
        prof = argv[i + 1]
        del argv[i:i + 2]
    dxf, conv, out_path = argv[:3]
    from tools import urban_boq_m2 as M2
    from tools import urban_intake as UI
    calls, orig = _capture()
    try:
        R = M2.compute([dxf], conventions=conv, profile=prof, route="G", completeness=True)
    finally:
        MD.split_at_supports, MD.bind_marks = orig
    D = R["generic"]["D"]
    u, lib = D["unit_m"], D["lib"]
    tol = 0.012 / u                                      # the route's own drawing tolerance (generic_route.detect)
    conv_d = {c["id"]: c for c in json.loads(open(conv, encoding="utf-8").read())["conventions"]}
    pcl = conv_d.get("PLANTED_COLUMN_LABELS") or {}
    intake = UI.read_dxf(dxf)
    dims, outlines = _dims_and_outlines(dxf)
    if (D.get("options") or {}).get("local_origin"):    # the route computed near the origin: same shift here
        intake = GR.to_local_origin(intake)
        ox, oy = intake["local_origin"]["x"], intake["local_origin"]["y"]
        k_ = {"x": ox, "y": oy}
        dims = [dict(d, lo=d["lo"] - k_[d["axis"]], hi=d["hi"] - k_[d["axis"]], p1=(d["p1"][0] - ox, d["p1"][1] - oy),
                     p2=(d["p2"][0] - ox, d["p2"][1] - oy)) for d in dims]
        outlines = [dict(o, pts=[(x - ox, y - oy) for x, y in o["pts"]]) for o in outlines]
    titles = {m.group(1) for t in D["model"]["texts"] for m in [BV2.SECTION_TITLE.search(t["norm"].replace("%%U", ""))]
              if m}
    report = {"items": len(R["items"]), "sheets": {}, "replay_v1_identical": True, "sections": {}}
    # pair the captured calls with the slab sheets in route order (split then bind per sheet; single-face splits
    # after bind are skipped)
    slab = [sid for sid, rec in D["sheets"].items() if rec["sheet"]["role"] in ("SLAB_PLAN", "GROUND_BEAM_PLAN")]
    seq = iter(calls)
    pairs = {}
    for sid in slab:
        sp = next(c for c in seq if c["kind"] == "split")
        bd = next(c for c in seq if c["kind"] == "bind")
        pairs[sid] = (sp, bd)
    for sid, (sp, bd) in pairs.items():
        rec = D["sheets"][sid]
        box = rec["sheet"]["box"]
        inside = lambda p: box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]  # noqa: E731
        segs = [s for s in intake["segments"] if inside(s["a"]) and inside(s["b"])]
        circ = [c for c in intake.get("circles", []) if inside(c["c"])]
        lays = set(rec.get("edge_layers") or [])
        cols = sp["cols"]
        planted = BV2.planted_columns(rec["texts"], [s for s in segs if s["layer"] not in lays], circ, cols, u, tol,
                                      label_pattern=pcl.get("label_pattern") or BV2.PLANTED_LABEL,
                                      label_unit_m=float(pcl.get("label_unit_m") or BV2.PLANTED_LABEL_UNIT_M))
        b1 = MD.split_at_supports(sp["bands"], cols, sp["min_piece"], sp["touch"])
        same = [x["band_id"] for x in b1] == [x["band_id"] for x in sp["out"]]
        m1 = MD.bind_marks(b1, bd["bm"], bd["widths_of"], u)
        same &= [(m["mark"], m["state"], tuple(m.get("bands", []))) for m in m1] == \
                [(m["mark"], m["state"], tuple(m.get("bands", []))) for m in bd["out"]]
        report["replay_v1_identical"] &= same
        b2 = BV2.split_at_supports_v2(sp["bands"], cols, sp["min_piece"], sp["touch"], planted=planted,
                                      tol_native=tol)
        m2 = BV2.bind_marks_v2(b2, bd["bm"], bd["widths_of"], u)
        sup = cols + [b for b in rec["column_presence"] if not any(max(abs(b[k] - c[k]) for k in range(4)) <= tol
                                                                   for c in cols)]
        i1 = MD.inherit_sections(b1, m1, lib, 1.0 / u, supports=sup)
        i2 = MD.inherit_sections(b2, m2, lib, 1.0 / u, supports=sup)
        t = (rec.get("slab") or {}).get("uniform_t_m")
        q1 = {r["band_id"]: r for r in MD.beam_quantities(b1, m1 + i1, lib, [], u, t)}
        q2 = {r["band_id"]: r for r in MD.beam_quantities(b2, m2 + i2, lib, [], u, t)}

        def line(r):
            return {"state": r["state"], "mark": r.get("mark"), "binding": r.get("binding"),
                    "len_m": round(r["length_m"], 4), "w_m": round(r["width_m"], 3),
                    "net_plan_m2": round(r["net_plan_m2"], 5), "v_m3": round(r["v_total_depth"], 4)
                    if r.get("v_total_depth") is not None else None}
        changed = []
        for k in sorted(set(q1) | set(q2)):
            a, b = q1.get(k), q2.get(k)
            if a is None or b is None or line(a) != line(b):
                changed.append({"band": k, "v1": line(a) if a else None, "v2": line(b) if b else None})
        mk = []
        for a, b in zip(m1, m2):
            if (a["state"], a.get("bands")) != (b["state"], b.get("bands")):
                mk.append({"mark": a["mark"], "v1": [a["state"], a.get("bands") or a.get("candidates")],
                           "v2": [b["state"], b.get("bands") or b.get("candidates")]})
        bound = lambda q: sum(r.get("v_total_depth") or 0 for r in q.values() if r["state"] == "BOUND")  # noqa
        unb = lambda q: [k for k, r in q.items() if r["state"] != "BOUND"]  # noqa
        cuts = BV2.section_cuts(rec["texts"], segs, b2, u, edge_layers=lays, titles=titles)
        arcs_s = [a for a in intake.get("arcs", []) if a["layer"] in lays and inside(a["c"])]
        circ_s = [c for c in circ if c["layer"] in lays]
        fb = ring_fb if ring_fb and rec["sheet"]["role"] == "SLAB_PLAN" and \
            rec["sheet"].get("storey") == ring_fb.get("storey", rec["sheet"].get("storey")) else None
        rings = BV2.ring_beams(arcs_s, circ_s, b2, cols, m2, bd["widths_of"], lib, u, tol, fallback=fb,
                               parent_bands=sp["bands"])
        for r_ in rings:
            r_["arc_bands_bound_v2_m3"] = round(sum(q2[b]["v_total_depth"] or 0 for b in r_["arc_bands"]
                                                    if b in q2 and q2[b]["state"] == "BOUND"), 4)
            r_.pop("centre", None)
        report["sheets"][sid] = {
            "storey": rec["sheet"].get("storey"), "replay_v1_identical": same,
            "planted": [{k: v for k, v in p.items() if k in ("label", "state", "link", "drawn_m", "section_m")}
                        for p in planted],
            "bands_v1": len(b1), "bands_v2": len(b2), "marks_changed": mk, "lines_changed": changed,
            "bound_v1_m3": round(bound(q1), 4), "bound_v2_m3": round(bound(q2), 4),
            "not_bound_v1": len(unb(q1)), "not_bound_v2": len(unb(q2)),
            "cuts": {k: {"state": v["state"], "bands": v.get("bands")} for k, v in cuts.items()},
            "rings": rings,
        }
        report["sheets"][sid]["_cuts"] = cuts
        report["sheets"][sid]["_bands"] = b2
    # printed sections: each title -> the dimensioned outline nearest to it, lying wholly above its baseline; the
    # pairing must be mutual (that outline is not nearer to another section title), else HELD
    tit = [(BV2.SECTION_TITLE.search(t["norm"].replace("%%U", "")), t) for t in D["model"]["texts"]]
    tit = [(m.group(1), t) for m, t in tit if m]

    def bdist(t, o):
        xs, ys = [p[0] for p in o["pts"]], [p[1] for p in o["pts"]]
        dx = max(min(xs) - t["x"], 0.0, t["x"] - max(xs))
        dy = max(min(ys) - t["y"], 0.0, t["y"] - max(ys))
        return math.hypot(dx, dy)
    dimmed_all = []
    for o in outlines:
        # a dimension belongs to the outline when both its extension origins are outline vertices
        on = [d for d in dims if all(any(math.dist(q, p) <= tol for p in o["pts"]) for q in (d["p1"], d["p2"]))]
        if len(on) >= 2:
            dimmed_all.append((o, on))
    for L, t in tit:
        dimmed = sorted(((bdist(t, o), o, on) for o, on in dimmed_all if min(p[1] for p in o["pts"]) >= t["y"]),
                        key=lambda x: x[0])
        if not dimmed:
            report["sections"][L] = {"state": "HELD", "why": "no dimensioned outline above the title"}
            continue
        _, o, on = dimmed[0]
        if min(tit, key=lambda x: bdist(x[1], o))[1] is not t:
            report["sections"][L] = {"state": "HELD", "why": "the nearest outline is nearer to another title"}
            continue
        # which sheet's cut line names this letter -> the band and its schedule row
        hit = [(sid, s["_cuts"][L]) for sid, s in report["sheets"].items() if L in s["_cuts"]]
        rec_s = {"title": f"SECTION {L}-{L}", "outline_handle": o["handle"], "n_dims": len(on), "cuts": len(hit)}
        if len(hit) != 1 or hit[0][1]["state"] != "CUT":
            report["sections"][L] = dict(rec_s, state="HELD", why="cut line not found once on the plans")
            continue
        sid, cut = hit[0]
        bands = report["sheets"][sid]["_bands"]
        by = {b["band_id"]: b for b in bands}
        rows = [(fam, mk, r) for (fam, mk), r in lib.items() if fam in MD.BEAM_FAMILIES]
        cand = []
        for bid in cut["bands"]:
            w = by[bid]["width_native"] * u
            for fam, mk, r in rows:
                if abs((r["dims_m"].get("W") or 0) - w) <= 0.015:
                    p = BV2.section_profile(o["pts"], on, r["dims_m"]["W"], r["dims_m"].get("H"), tol)
                    if p["state"] == "PRINTED" and abs(p["beam_w_m"] - w) <= 0.015:
                        cand.append((bid, mk, p))
        if not cand:
            report["sections"][L] = dict(rec_s, state="HELD", why="no crossed band matches a printed profile")
            continue
        # one upstand per crossed band: the schedule rows whose W x H the section prints are listed (the section
        # prints no mark, so the row itself stays open; the upstand needs only the printed section and the span)
        res = {}
        for bid, mk, p in cand:
            r_ = res.setdefault(bid, {"band": bid, "rows_fitting_section": [], "profile": p,
                                      "upstand": BV2.upstand_lines(p, cut, bands, u, section=f"{L}-{L}")})
            r_["rows_fitting_section"].append(mk)
        report["sections"][L] = dict(rec_s, sheet=sid, state="READ", lines=list(res.values()))
    for s in report["sheets"].values():
        s.pop("_cuts", None)
        s.pop("_bands", None)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, sort_keys=True, default=str)
    print(json.dumps({"items": report["items"], "replay_v1_identical": report["replay_v1_identical"],
                      "sheets": {k: {kk: v[kk] for kk in ("storey", "bands_v1", "bands_v2", "bound_v1_m3",
                                                          "bound_v2_m3", "not_bound_v1", "not_bound_v2")}
                                 for k, v in report["sheets"].items()}}, indent=1))


if __name__ == "__main__":
    main()
