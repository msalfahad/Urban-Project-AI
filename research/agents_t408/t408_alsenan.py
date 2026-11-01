"""T-408 on the development villa (read-only; outputs to --out or the research folder: ids, codes, states, m / m2 / m3
only, no coordinates, no names, no drawing text).

    python3 -I research/agents_t408/t408_alsenan.py --structural <private>/ST7757.dxf \
        --v3034 <run>/V3_0_34_BOQ_LINES.json --v3032 <run>/V3_0_32_BOQ_LINES.json --out research/agents_t408

1. Tie-beam clear runs measured on the column outlines of EACH plan that draws the GF lift columns (GF roof slab plan =
   the columns under the GF roof; p.1 columns plan; ground-beams plan pit ring = T-401's), plus 1F roof and 2F roof
   (their columns) for the storey table; R-T408-1 / -5.
2. Binding of the T-401 components to the candidate of record V3.0.34 and the V3.0.32 -> V3.0.34 drift of every lift
   line (R-T408-6).
3. The pit-wall line's held text against the two facts it depends on.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lift_tie_v1 as X  # noqa: E402

# DXF handles (structural set): the four lift column outlines and the shaft per plan (S-OPENING cross or S-BW ring).
PLANS = {
    "GF_ROOF_SLAB_PLAN (columns under the GF roof)": {"cols": ["33E", "341", "33B", "338"], "shaft": ["54F"]},
    "P1_COLUMNS_PLAN": {"cols": ["834", "837", "831", "82E"], "shaft": None},
    "GROUND_BEAMS_PLAN (pit ring, T-401)": {"cols": ["1096", "1099", "1093", "1090"], "shaft": ["10EA"],
                                             "outer": "10EB"},
    "1F_ROOF_SLAB_PLAN (columns under the 1F roof)": {"cols": ["67F", "682", "67C", "679"], "shaft": ["73F"]},
    "2F_ROOF_SLAB_PLAN (columns under the 2F roof)": {"cols": ["41E", "421", "41B", "418"], "shaft": None},
}
STOREYS = [("GF", 1.00, 5.50, "GF_ROOF_SLAB_PLAN (columns under the GF roof)"),
           ("1F", 5.50, 9.70, "1F_ROOF_SLAB_PLAN (columns under the 1F roof)"),
           ("2F", 9.70, 13.90, "2F_ROOF_SLAB_PLAN (columns under the 2F roof)")]
RULE = {"limit": 4.30, "level": 3.00, "ref": "ST p.8 note 19"}


def _bb(doc, h):
    from ezdxf import bbox
    b = bbox.extents([doc.entitydb[h]])
    return [b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y]


def plan_geometry(doc):
    out = {}
    for name, p in PLANS.items():
        cols = [_bb(doc, h) for h in p["cols"]]
        sw, nw, ne, se = cols
        if p["shaft"]:
            shaft = _bb(doc, p["shaft"][0])
        else:  # shaft = between the inner faces of the flush columns (W inner x, E inner x, S/N inner faces of the band)
            shaft = [sw[2], sw[1] + 200.0, ne[0], nw[3] - 200.0]
        band = {"W": shaft[0] - sw[0], "E": ne[2] - shaft[2], "S": shaft[1] - sw[1], "N": nw[3] - shaft[3]}
        outer = _bb(doc, p["outer"]) if p.get("outer") else [shaft[0] - band["W"], shaft[1] - band["S"],
                                                             shaft[2] + band["E"], shaft[3] + band["N"]]
        g = X.storey_runs(outer, shaft, cols, "mm")
        sec = [((c[2] - c[0]) / 1000.0, (c[3] - c[1]) / 1000.0) for c in cols]
        out[name] = {"runs_m": g["runs_m"], "run_total_m": g["run_total_m"], "band_m": {k: round(v / 1000, 3)
                     for k, v in band.items()}, "shaft_m": [round((shaft[2] - shaft[0]) / 1000, 3),
                     round((shaft[3] - shaft[1]) / 1000, 3)], "column_sections_m": sec,
                     "handles": p["cols"] + (p["shaft"] or [])}
    return out


def lines_by_id(path):
    data = json.loads(Path(path).read_text())
    rows = data["lines"] if isinstance(data, dict) else data
    out = {}
    for ln in rows:
        lid = ln["line_id"]
        br = ln.get("bounded_range") or {}
        calc = ln.get("calculation") or {}
        rfi = ln.get("rfi") or {}
        out[lid] = {"item_code": ln.get("item_code"), "state": ln.get("evidence_state"),
                    "value": ln.get("measured_net"), "range": [br.get("low"), br.get("high")] if br else None,
                    "text": " ".join(str(x or "") for x in (calc.get("formula"), ln.get("notes"),
                                                            rfi.get("question") if isinstance(rfi, dict) else rfi,
                                                            ln.get("physical_element"),
                                                            (ln.get("location") or {}).get("element_id"))),
                    "element_id": (ln.get("location") or {}).get("element_id"), "raw": ln}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--structural", required=True)
    ap.add_argument("--v3034", required=True)
    ap.add_argument("--v3032", required=True)
    ap.add_argument("--out", default=str(HERE))
    a = ap.parse_args()
    import ezdxf
    doc = ezdxf.readfile(a.structural)
    geo = plan_geometry(doc)
    out = Path(a.out)

    # 1. storey table
    st_rows = []
    for name, ffl, nxt, plan in STOREYS:
        g = geo[plan]
        r = X.tie_beam({"name": name, "ffl": ffl, "next_ffl": nxt}, RULE, g, None, line_id=None,
                       ring_above={"top": None, "depth": 0.75 if name == "GF" else None})
        st_rows.append({"storey": name, "ffl": ffl, "next_ffl": nxt, "height_m": r["storey_height_m"],
                        "tie_required": r["required"], "plan": plan, "clear_runs_m": g["run_total_m"],
                        "runs": g["runs_m"], "clash": r.get("clash"),
                        "components": r["components"]})

    # 2. binding V3.0.32 (T-401 verified table) -> V3.0.34
    l34, l32 = lines_by_id(a.v3034), lines_by_id(a.v3032)
    comp_csv = HERE.parent / "agents_t401" / "COMPONENTS_T401.csv"
    col_csv = HERE.parent / "agents_t401" / "COLUMNS_T401.csv"
    exp = []
    for row in csv.DictReader(comp_csv.open()):
        if row["candidate_line"].startswith("L-"):
            exp.append({"component": row["component_id"], "line_id": row["candidate_line"],
                        "item_code": row["line_code"], "state": row["line_state"],
                        "value": float(row["line_value"]) if row["line_value"] else None})
    for row in csv.DictReader(col_csv.open()):
        if row["item_code"].startswith("STR.CONC"):
            exp.append({"component": f"{row['member']}:{row['line_id'][:10]}", "line_id": row["line_id"],
                        "item_code": row["item_code"], "state": row["state"],
                        "value": float(row["value_m3"]) if row["value_m3"] else None})
    bind = X.bind_check(exp, l34)
    drift32 = []
    for e in exp:
        a32, a34 = l32.get(e["line_id"]), l34.get(e["line_id"])
        if a32 and a34 and (a32["raw"] != a34["raw"]):
            drift32.append({"line_id": e["line_id"], "item_code": e["item_code"],
                            "v32": [a32["value"], a32["state"], a32["range"]],
                            "v34": [a34["value"], a34["state"], a34["range"]]})

    # 3. lift lines in V3.0.34 by code / text
    # held lines whose value depends on the pit-wall height (the valued pit-floor WP lines do not)
    lift = {lid: v for lid, v in l34.items() if v["value"] is None and (
            (v["item_code"] or "").startswith("STR.CONC.LIFT") or "LIFT_PIT" in (v["item_code"] or "")
            or "LIFT-PIT" in (v["element_id"] or ""))}
    facts = {"pit depth (lift supplier)": ["pit depth", "lift supplier", "manufactur"],
             "GF build-up F.F.L. -> slab-on-grade top": ["build-up", "build up", "slab-on-grade top",
                                                          "slab top"]}
    lift_rows = [{"line_id": lid, "item_code": v["item_code"], "state": v["state"], "value": v["value"],
                  "range": v["range"], "facts_not_named": X.held_facts_check(v["text"], facts)}
                 for lid, v in sorted(lift.items())]
    tie_lines = [lid for lid, v in l34.items() if any(k in (v["text"] or "").lower() for k in
                 ("tie beam", "tie-beam", "lift_tie")) and (v["item_code"] or "").startswith("STR.")]
    # the GF lift block walls held on the tie-beam size (displacement paired with the tie: R-T408 masonry item)
    blk = {}
    for lid, v in l34.items():
        if v["item_code"] in ("MAS.BLOCK", "ARCH.WALL_PANEL", "ARCH.WALL_VOLUME"):
            raw = json.dumps(v["raw"])
            walls = sorted(set(w for w in ("GF-W08", "GF-W09", "GF-W13", "GF-W14")
                               if f'"lift tie beam size (ST p.8 n.19)", "kind": "HELD_WALL", "wall": "{w}"' in raw))
            if walls:
                blk[lid] = {"item_code": v["item_code"], "state": v["state"], "value": v["value"], "walls": walls}
    # whole-candidate delta V3.0.33 -> V3.0.34 is read from the run's own DIFF by the caller; here: lift lines only
    gf = geo["GF_ROOF_SLAB_PLAN (columns under the GF roof)"]
    closure = {"runs_x_band_m2": round(gf["run_total_m"] * 0.20, 6),
               "columns_in_band_m2": round(0.20 * 0.50 * 3 + 0.20 * 1.00, 6),
               "gross_band_m2": round(2.20 ** 2 - 1.80 ** 2, 6)}
    closure["closes"] = abs(closure["runs_x_band_m2"] + closure["columns_in_band_m2"] - closure["gross_band_m2"]) < 1e-6
    clash_bound = {"tie_level_m": 1.00 + RULE["level"], "gf_roof_ffl_above_m": 5.50,
                   "ring_beams_under": {"S": ("B14", 0.75), "W": ("B7", 0.75), "E": ("B1", 0.40), "N": ("B1", 0.40)},
                   "d_max_S_W": "0.75 - (1F floor build-up F.F.L. +5.50 -> GF roof slab top), unprinted: d < 0.75 m",
                   "d_max_N_E": "1.10 - (same build-up): d < 1.10 m",
                   "status": "OPEN (no structural slab level printed; the d bound is a physical constraint, not a "
                             "section)"}

    ring = [b for b in bind if b["component"].startswith("RING_BEAM")]
    cap = [b for b in bind if b["component"].startswith("SHAFT_SLAB")]
    summary = {
        "method": X.METHOD_ID, "plans": geo, "storeys": st_rows,
        "binding": bind, "drift_v3032_v3034": drift32,
        "ring_beams_m3": round(sum(b["line_value"] or 0 for b in ring), 6), "ring_beam_lines": len(ring),
        "ring_all_bound": all(b["result"] == "BOUND" for b in ring),
        "cap_m3": cap[0]["line_value"] if cap else None, "cap_bound": bool(cap) and cap[0]["result"] == "BOUND",
        "lift_lines_v3034": lift_rows, "tie_lines_v3034": tie_lines, "gf_lift_block_lines": blk,
        "gf_band_closure": closure, "gf_tie_clash": clash_bound,
        "lines_v3034": len(l34), "lines_v3032": len(l32),
    }
    (out / "summary_t408.json").write_text(json.dumps(summary, indent=1, sort_keys=True, default=str))
    with (out / "BINDING_T408.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["component", "line_id", "item_code", "state_v3032", "value_v3032", "state_v3034", "value_v3034",
                    "result"])
        for b in bind:
            w.writerow([b["component"], b["line_id"], b["item_code"], b["state"], b["value"], b.get("line_state"),
                        b.get("line_value"), b["result"]])
    print(json.dumps({k: summary[k] for k in ("ring_beams_m3", "ring_beam_lines", "ring_all_bound", "cap_m3",
                                               "cap_bound", "lift_lines_v3034", "tie_lines_v3034",
                                               "gf_lift_block_lines", "gf_band_closure", "lines_v3034",
                                               "lines_v3032")}, indent=1, default=str))
    print(json.dumps({k: {"runs": v["runs_m"], "total": v["run_total_m"], "band": v["band_m"], "shaft": v["shaft_m"],
                          "cols": v["column_sections_m"]} for k, v in geo.items()}, indent=1))
    print("drift:", json.dumps(drift32, indent=1, default=str))
    print("binding not BOUND:", [b for b in bind if b["result"] != "BOUND"])


if __name__ == "__main__":
    main()
