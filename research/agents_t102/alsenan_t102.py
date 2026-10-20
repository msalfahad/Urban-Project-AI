"""T-102 read-only diagnostic: BEAM_SECTION_CUT_BINDING_V1 on a real structural DXF, through the unchanged route G.

Nothing is wired and nothing is written into the repository. Route G (tools/urban_boq_m2.compute, route "G") runs once;
the inputs of MEMBER_DETECTION_V1 split_at_supports / bind_marks on every slab plan are captured by a pass-through
wrapper (the T-085 harness), so the bands, marks, marks proposed along a line and net plan areas are the route's own.
Every section letter on every slab sheet is then bound by the new piece.

Usage (Python 3.11 venv, repo root):
  python -I research/agents_t102/alsenan_t102.py <structural.dxf> <conventions.json> <out.json>
out.json: per sheet, per letter: state, reason, span id, printed size, unit, volume, crossed span ids / widths /
marks. No drawing coordinates, no texts other than marks."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.source import beam_section_cut_binding as SC  # noqa: E402
from engine.source import generic_route as GR  # noqa: E402
from engine.source import member_detection as MD  # noqa: E402


def _capture():
    calls = []
    orig_split, orig_bind = MD.split_at_supports, MD.bind_marks

    def split(bands, cols, min_piece, touch=0.0):
        out = orig_split(bands, cols, min_piece, touch)
        calls.append({"kind": "split", "cols": cols, "out": out})
        return out

    def bind(bands, bm, widths_of, u, *a, **k):
        out = orig_bind(bands, bm, widths_of, u, *a, **k)
        calls.append({"kind": "bind", "out": out})
        return out
    MD.split_at_supports, MD.bind_marks = split, bind
    return calls, (orig_split, orig_bind)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    dxf, conv, out_path = argv[:3]
    import ezdxf
    from tools import urban_boq_m2 as M2
    from tools import urban_intake as UI
    calls, orig = _capture()
    try:
        R = M2.compute([dxf], conventions=conv, profile=None, route="G", completeness=True)
    finally:
        MD.split_at_supports, MD.bind_marks = orig
    D = R["generic"]["D"]
    u, lib = D["unit_m"], D["lib"]
    tol = 0.012 / u                                     # the route's own drawing tolerance (generic_route.detect)
    intake = UI.read_dxf(dxf)
    doc = ezdxf.readfile(dxf)
    dims, outlines = SC.dimension_records(doc), SC.outline_records(doc)
    if (D.get("options") or {}).get("local_origin"):   # the route computed near the origin: same shift here
        intake = GR.to_local_origin(intake)
        ox, oy = intake["local_origin"]["x"], intake["local_origin"]["y"]
        k_ = {"x": ox, "y": oy}
        dims = [dict(d, lo=d["lo"] - k_[d["axis"]], hi=d["hi"] - k_[d["axis"]], p1=(d["p1"][0] - ox, d["p1"][1] - oy),
                     p2=(d["p2"][0] - ox, d["p2"][1] - oy)) for d in dims]
        outlines = [dict(o, pts=[(x - ox, y - oy) for x, y in o["pts"]]) for o in outlines]
    titles = SC.section_titles([dict(t, value=t.get("value") or t.get("norm")) for t in D["model"]["texts"]])
    dimmed = SC.dimensioned_outlines(outlines, dims, tol)
    schedule = {mk: (r["dims_m"].get("W"), r["dims_m"].get("H")) for (fam, mk), r in lib.items()
                if fam in MD.BEAM_FAMILIES}
    slab = [sid for sid, rec in D["sheets"].items() if rec["sheet"]["role"] in ("SLAB_PLAN", "GROUND_BEAM_PLAN")]
    seq = iter(calls)
    report = {"policy": SC.policy_record(), "titles": sorted(t["letter"] for t in titles),
              "dimensioned_outlines": len(dimmed), "sheets": {}}
    for sid in slab:
        sp = next(c for c in seq if c["kind"] == "split")
        bd = next(c for c in seq if c["kind"] == "bind")
        rec = D["sheets"][sid]
        box = rec["sheet"]["box"]
        inside = lambda p: box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]  # noqa: E731
        segs = [s for s in intake["segments"] if inside(s["a"]) and inside(s["b"])]
        lays = set(rec.get("edge_layers") or [])
        bands = sp["out"]
        sup = sp["cols"] + [b for b in rec["column_presence"] if not any(max(abs(b[k] - c[k]) for k in range(4)) <=
                                                                          tol for c in sp["cols"])]
        inh = MD.inherit_sections(bands, bd["out"], lib, 1.0 / u, supports=sup)
        t = (rec.get("slab") or {}).get("uniform_t_m")
        # route state from the printed marks only (a mark proposed along a line is not a release: route G holds
        # those spans as UNLABELLED_SPAN_ACROSS_SUPPORT); the net plan area is the route's own for every band
        q = {r["band_id"]: r for r in MD.beam_quantities(bands, bd["out"], lib, [], u, t)}
        qi = {r["band_id"]: r for r in MD.beam_quantities(bands, bd["out"] + inh, lib, [], u, t)}
        net = {k: r["net_plan_m2"] for k, r in qi.items() if r.get("net_plan_m2") is not None}
        res = SC.bind_sections(sheet_id=sid, sheet_box=box, texts=[dict(x, value=x.get("value") or x.get("norm"))
                                                                   for x in rec["texts"]],
                               segments=segs, bands=bands, unit_m=u, titles_all=titles, dimmed=dimmed,
                               bindings=bd["out"] + inh, schedule=schedule, edge_layers=lays, net_plan_m2=net,
                               tol_native=tol)
        for r in res:
            r.pop("section_outline_id", None)
            if r.get("upstand"):
                r["upstand"] = {k: r["upstand"].get(k) for k in ("state", "band", "w_m", "h_m", "length_m",
                                                                 "volume_m3", "why")}
            for c in r.get("crossed", []) + r.get("not_bound", []):
                c["route_state"] = q.get(c["band"], {}).get("state")
                c["route_m3"] = q.get(c["band"], {}).get("v_total_depth")
        report["sheets"][sid] = {"storey": rec["sheet"].get("storey"), "letters": res}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, sort_keys=True, default=str)
    for sid, s in report["sheets"].items():
        for r in s["letters"]:
            print(sid, s["storey"], r["section"], r["state"], r.get("reason", ""), r.get("band", ""),
                  r.get("printed", ""), r.get("volume_m3", ""), r.get("check", r.get("why", "")))


if __name__ == "__main__":
    main()
