"""T-391 Alsenan run: GS-SLAB and GB-MAIN of the T-385 reconciliation split into named causes in m3.

    .work/venv/bin/python -I research/agents_t391/t391_alsenan.py \
        --freelancer "<.work/private>/<concrete + rebar workbook>.xlsx" --out <checkout>/.work/private/t391/out [--write]

Inputs: the candidate's buried concrete lines as committed by T-347 (CANDIDATE_V3024_BURIED_LINES.json; the 25 ground-slab
and 58 ground-beam lines are those of V3.0.29 / V3.0.30: same ids and figures, T-385 component totals 17.240684 and
27.625386 m3 reproduced below), the V3.0.29 downgrade records (agents/control verdicts/V3.0.29/DOWNGRADES.json), the
own drawing read OWN_GROUND_T391.json (t391_extract.py) and the freelancer workbook (private; quantities only, never a
rate). --out must be outside the repository: the freelancer's row values stay there. --write writes the ENGINE-side
summary (no freelancer value) to summary_t391.json beside this file.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t391_rules as R  # noqa: E402

LINES = ROOT / "research" / "agents_t347" / "CANDIDATE_V3024_BURIED_LINES.json"
DOWNGRADES = ROOT.parent / "board" / "docs" / "agents" / "verdicts" / "V3.0.29" / "DOWNGRADES.json"
OWN = HERE / "OWN_GROUND_T391.json"
T_SLAB = 0.10                    # ST GROUND BEAMS PLAN 'T=10cm' (T-206 DRAWING-CONFIRMED), the engine's t on every face
HELD_CELL = "SITE-c1089bdb4cfcdc4a"
SLIVER_AS_PANEL = {"OWN-090"}    # 0.1556 m2 triangle bounded by three beams (T-242 GS-29, engine cell 997c65af): a panel
#                                  whose equivalent width falls under the strip test; its own reading is a slab panel


def load_engine(lines_path=LINES, dg_path=DOWNGRADES):
    d = json.loads(Path(lines_path).read_text(encoding="utf-8"))
    held = set()
    for x in json.loads(Path(dg_path).read_text(encoding="utf-8"))["downgrades"]:
        held |= set(x["line_ids"])
    gs = [ln for ln in d["lines"] if ln["item_code"] == "STR.CONC.GROUND_SLAB"]
    gb = [ln for ln in d["lines"] if ln["item_code"] == "STR.CONC.GROUND_BEAM"
          and "BOUNDARY_GB" not in ln["element_id"]]
    return gs, gb, held


def freelancer(path):
    import openpyxl  # private step only
    ws = openpyxl.load_workbook(path, data_only=True).worksheets[2]
    def row(r):
        return [ws.cell(r, c).value for c in (2, 3, 4, 9)]
    s, gl, gt = row(11), row(13), row(14)
    if not (gl[0] == gt[0] and gl[2] == gt[2]):
        raise SystemExit("his two ground-beam rows carry different sections: split not by one section")
    return {"slab_area_m2": float(s[0]), "slab_t_m": float(s[2]), "slab_m3": float(s[3]),
            "gb_b_m": float(gl[0]), "gb_d_m": float(gl[2]), "gb_length_m": float(gl[1]) + float(gt[1]),
            "gb_m3": float(gl[3]) + float(gt[3])}


def own_partition(own):
    faces = {f["face"]: dict(f) for f in own["faces"]}
    for k in SLIVER_AS_PANEL:
        faces[k]["kind"] = "PANEL"
    return faces


def slab_split(gs, own, fl):
    faces = own_partition(own)
    tot = R.check_partition([{"id": k, "kind": f["kind"], "area_m2": f["area_m2"]} for k, f in faces.items()])
    bind = {b["engine_cell"]: b for b in own["engine_binding"]}
    by_cell = {ln["element_id"].split(":")[-1]: ln for ln in gs}
    valued = [ln for ln in gs if ln["evidence_state"] != "BOUNDED_EXPOSURE"]
    eng_v_m3 = sum(ln["measured_net"] for ln in valued)
    eng_v_m2 = sum(ln["dimensions"]["area_m2"] for ln in valued)
    held_cell = bind[HELD_CELL]
    held_pieces = [faces[k] for k in held_cell["own_faces"]]
    hb = R.bound_of_held_cell(held_pieces, T_SLAB)
    other_family = [b for c, b in bind.items() if c not in by_cell]          # engine cells with no GS line
    own_other = sum(faces[k]["area_m2"] for b in other_family for k in b["own_faces"] if faces[k]["kind"] == "PANEL")
    panels = tot["PANEL"]
    strips = tot["BEAM"] + tot["COLUMN"] + tot["LIFT"]
    network = sum(tot.values())
    own_valued = panels - hb["slab_m2"] - own_other
    per_face = []
    for c, b in sorted(bind.items()):
        if c not in by_cell or c == HELD_CELL:
            continue
        own_m2 = sum(faces[k]["area_m2"] for k in b["own_faces"])
        per_face.append({"engine_cell": c, "line_id": by_cell[c]["line_id"], "engine_m2": b["net_m2"],
                         "gross_m2": b["gross_m2"], "member_overlap_m2": b["member_overlap_m2"],
                         "own_faces": b["own_faces"], "own_m2": round(own_m2, 4)})
    # the one own panel the engine splits into two cells (OWN-006 = d74f + 0caa + the arc-side remainder)
    split = [p for p in per_face if not p["own_faces"]]
    for p in split:
        host = [q for q in per_face if q["own_faces"] and q["own_m2"] > q["engine_m2"] + p["engine_m2"] - 1.0
                and q["own_m2"] - q["engine_m2"] > 1.0]
        if len(host) != 1:
            raise SystemExit(f"{p['engine_cell']}: no single own panel hosts it")
        p["shares_own_face_with"] = host[0]["engine_cell"]
    out = {"engine_valued_m3": round(eng_v_m3, 6), "engine_valued_m2": round(eng_v_m2, 4),
           "engine_held_line": by_cell[HELD_CELL]["line_id"], "engine_held_bound_m3":
           round(by_cell[HELD_CELL]["bounded_high"], 6), "held_cell_own": hb, "own_totals_m2": tot,
           "own_panels_m2": round(panels, 4), "own_strips_m2": round(strips, 4), "own_network_m2": round(network, 4),
           "own_valued_panels_m2": round(own_valued, 4), "own_other_family_m2": round(own_other, 4),
           "other_family_cells": [b["engine_cell"] for b in other_family], "per_face": per_face}
    if fl is not None:
        if abs(fl["slab_t_m"] - T_SLAB) > 1e-9:
            raise SystemExit("his slab thickness differs from the printed T=10cm: the split is not by area alone")
        out["split"] = R.slab_cause_split(t_m=T_SLAB, engine_valued_m3=eng_v_m3, other_m3=fl["slab_m3"],
                                          own_valued_m2=own_valued, engine_valued_m2=eng_v_m2,
                                          own_held_panels_m2=hb["slab_m2"], own_other_family_m2=own_other,
                                          own_strips_m2=strips, own_network_m2=network,
                                          other_area_m2=fl["slab_area_m2"])
    return out


def beam_runs(gb, held):
    runs = []
    for ln in gb:
        dim = ln["dimensions"]
        is_held = ln["evidence_state"] == "BLOCKED_RFI" or ln["line_id"] in held
        if is_held:
            why = ("D-34 downgrade DG-a31a0d7e9dd564ad" if ln["line_id"] in held else
                   "court section not printed" if "court" in ln["formula"] else "D-35 annex CONFLICT")
            runs.append({"id": ln["line_id"], "state": "HELD", "L_m": dim["length_m"], "b_m": dim["width_m"],
                         "value_m3": None, "group": "HELD: " + why})
            continue
        A, V = dim["net_plan_m2"], ln["measured_net"]
        D = round(V / A, 4)
        grp = ("exterior main house, D printed by two levels (top +0.95 to N.G. +-0.00)" if D > 0.85 else
               f"interior p.13 class D {D:.2f}")
        runs.append({"id": ln["line_id"], "state": "VALUED", "L_m": dim["length_m"], "b_m": dim["width_m"],
                     "A_m2": A, "D_m": V / A, "value_m3": V, "group": grp})
    return runs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--freelancer")
    ap.add_argument("--out")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    gs, gb, held = load_engine()
    own = json.loads(OWN.read_text(encoding="utf-8"))
    fl = freelancer(a.freelancer) if a.freelancer else None
    slab = slab_split(gs, own, fl)
    runs = beam_runs(gb, held)
    # drawn length envelope of the lump (own read, OWN_GROUND_T391.json): strips alone / strips + every adjacent support
    beams = {"valued_m3": round(sum(r["value_m3"] for r in runs if r["state"] == "VALUED"), 6),
             "lines": len(runs), "held_lines": sum(r["state"] == "HELD" for r in runs)}
    if fl is not None:
        beams["split"] = R.beam_cause_split(runs=runs, other_b=fl["gb_b_m"], other_d=fl["gb_d_m"],
                                            other_length_m=fl["gb_length_m"], drawn_bounds_m=own.get("gb_bounds_m"))
    if a.out:
        out = Path(a.out).resolve()
        if ROOT.resolve() in out.parents or out == ROOT.resolve():
            raise SystemExit("--out inside the repository: the freelancer's values stay in .work/private")
        out.mkdir(parents=True, exist_ok=True)
        (out / "T391_PRIVATE.json").write_text(json.dumps({"slab": slab, "beams": beams, "freelancer": fl},
                                                          indent=1, sort_keys=True) + "\n", encoding="utf-8")
    pub = {"schema": "T391_SUMMARY_V1", "slab": {k: v for k, v in slab.items() if k != "split"},
           "beams": {k: v for k, v in beams.items() if k != "split"}}
    if fl is not None:   # cause TERMS in m3 (engine - freelancer); his raw row values are not written here
        pub["slab"]["cause_terms_m3"] = slab["split"]["terms_m3"]
        pub["slab"]["residual_m3"] = slab["split"]["residual_m3"]
        pub["slab"]["remainder_m3"] = slab["split"]["remainder_m3"]
        sp = beams["split"]
        pub["beams"].update(cause_terms_m3=sp["terms_m3"], residual_m3=sp["residual_m3"],
                            remainder_m3=sp["remainder_m3"], engine_length_m=sp["engine_length_m"],
                            held_length_m=sp["held_length_m"], groups=sp["groups"],
                            length_inside_drawn_bounds=sp.get("length_inside_drawn_bounds"),
                            drawn_bounds_m=sp.get("drawn_bounds_m"))
    if a.write:
        (HERE / "summary_t391.json").write_text(json.dumps(pub, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"slab": pub["slab"].get("cause_terms_m3"), "slab_residual": pub["slab"].get("residual_m3"),
                      "slab_rem": pub["slab"].get("remainder_m3"), "beams": pub["beams"].get("cause_terms_m3"),
                      "beams_residual": pub["beams"].get("residual_m3"), "beams_rem": pub["beams"].get("remainder_m3")},
                     indent=1))


if __name__ == "__main__":
    main()
