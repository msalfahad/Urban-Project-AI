"""T-263 development-villa ledger (Alsenan; not an accuracy claim): liquid waterproofing of buried concrete.

Built ONLY from committed, merged, values-only inputs (no drawing is read here; the drawing reads are in
T-263_BURIED_WP.md section 1):
- research/agents_t242/ALSENAN_GROUND_INPUT.json + LEDGER_T242.csv (T-242 MERGED 9455a63d): ground-beam runs, face-to-face
  lengths (T-230 ring ends), the slab panels on each side of each run, titles, statuses;
- research/agents_t253/LEDGER_T253.csv (T-253 MERGED dff9cb79): main-house exterior depth 0.95 (natural ground +-0.00),
  boundary band 44.07 m x 0.20 x 0.40, annex CONFLICT, court HELD;
- research/agents_t233/ALSENAN_FOOTING_INPUT.json (T-233 MERGED 2ecb5bf0): the 26 footing outlines;
- research/agents_t205/ALSENAN_NECK_INPUT.json + LEDGER_T205.csv (T-205 MERGED 5f40dfdb): 36 necks, sections, footing.

Repeat: `python3 -I research/agents_t263/t263_alsenan_check.py [--write]`.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import buried_wp_v1 as W  # noqa: E402

R = ROOT / "research"
TOP = {"MAIN": 0.95, "ANNEX": 0.25}          # T-214 structural tops (DRAWING-CONFIRMED)
SLAB_T = 0.10                                # ground slab 'T=10cm' (T-206 / T-242)
NATURAL_GROUND = 0.00                        # T-253 R-GB-DATUM-1: natural ground +-0.00; the court +0.15 is paving
PANEL_HELD = {"GS-12": "HELD", "GS-16": "HELD"}      # T-242: open or floored not printed (architect items)
PANEL_SPLIT = {"GS-08": "SPLIT_LEVEL"}               # stair hall: slab under +0.30 and +1.00 (T-242 / T-184)
TITLE_D = {"GB-LT2_5M": 0.30, "GB-LT5M": 0.40, "GB-GT5M": 0.60}  # p.13 interior sections
EXCLUDED_NECK_FOOTINGS = {"1B2B"}           # lift footing FF: pit walls / columns under the p.14 sheet system (T-219)


def _csv(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def panel_state(panels):
    if any(p in PANEL_HELD for p in panels):
        return "HELD"
    if any(p in PANEL_SPLIT for p in panels):
        return "SPLIT_LEVEL"
    return "FILL"


def build_runs():
    gi = json.loads((R / "agents_t242" / "ALSENAN_GROUND_INPUT.json").read_text(encoding="utf-8"))
    sides = {s["span_id"]: s["panels_by_side_m2"] for s in gi["spans"]}
    t253 = {r["item"]: r for r in _csv(R / "agents_t253" / "LEDGER_T253.csv")}
    runs = []
    for r in _csv(R / "agents_t242" / "LEDGER_T242.csv"):
        comp = r["component"]
        if not comp.startswith("GB-") or comp.startswith("GB-EXTERIOR (curved)"):
            continue
        rid, L, part = r["run"], float(r["L_m"]), r["part"]
        sd = sides[rid]
        faces = []
        for k in ("A", "B"):
            if sd[k]:
                faces.append({"side": "PANEL", "panel_state": panel_state(sd[k]), "panels": sd[k]})
            else:
                faces.append({"side": "OUTSIDE", "panels": []})
        depth, rng = None, None
        cls = comp.replace("GB-", "")
        if comp == "GB-INTERIOR" and r["status"] == "CALCULATED":
            ds = [TITLE_D[t] for t in r["titles"].split("+") if t in TITLE_D]
            assert len(set(ds)) == 1, rid                    # T-242: one printed title on every basis
            depth = ds[0]
            assert abs(0.3 * L * depth - float(r["value_m3"])) < 1e-3, rid
        elif comp == "GB-INTERIOR":
            ds = [TITLE_D[t] for t in r["titles"].split("+") if t in TITLE_D]
            rng = (min(ds), max(ds)) if ds else None
        elif comp == "GB-EXTERIOR" and part == "MAIN":
            assert t253[rid]["d_m"] == "0.95", rid
            depth = 0.95
        runs.append({"id": rid, "class": f"{cls} {part}", "L": L, "b": 0.3, "top": TOP[part], "depth": depth,
                     "depth_range": rng, "slab_t": SLAB_T,
                     "natural_ground": NATURAL_GROUND, "faces": faces, "t242_status": r["status"]})
    return runs, gi


def arc_rows(gi):
    rows = []
    for a in gi["arc_bands"]:
        axis_L = a["net_plan_m2"] / a["width_m"]
        r_ax = (a["r_in_m"] + a["r_out_m"]) / 2.0
        L_in, L_out = axis_L * a["r_in_m"] / r_ax, axis_L * a["r_out_m"] / r_ax
        if a["part"] == "MAIN":
            h = 0.95 - SLAB_T
            rd = {"building_on_convex_face": L_out * h, "building_on_concave_face": L_in * h}
            why = ("ARC_SIDE_NOT_TRACED: S1 prints no level on either side of the ring; which face looks into the slab "
                   "panels (GS-10 / GS-23) is not traced on the plan; the outside face is above the natural ground (0)")
        else:
            rd = {}
            why = "ANNEX_DEPTH_CONFLICT (D-35 annex, T-253): no depth, no face height"
        rows.append(W.Row(a["arc_band"], "GROUND_BEAM", "building-side face (curved)", "m2", None, W.HELD,
                          f"net axis {axis_L:.4f} m, faces {L_in:.4f} (r {a['r_in_m']}) / {L_out:.4f} (r {a['r_out_m']})",
                          rd, why))
    return rows


def footing_rows():
    fi = json.loads((R / "agents_t233" / "ALSENAN_FOOTING_INPUT.json").read_text(encoding="utf-8"))
    ni = json.loads((R / "agents_t205" / "ALSENAN_NECK_INPUT.json").read_text(encoding="utf-8"))
    nl = {r["neck_id"]: r for r in _csv(R / "agents_t205" / "LEDGER_T205.csv")}
    by_outline, unlinked = {}, []
    for n in ni["necks"]:
        led = nl[n["id"]]
        rng = tuple(float(x) for x in led["section_range_m2"].strip("()").split(","))
        perims = sorted({2 * (sec["W"] + sec["D"]) / 100.0 for sec in n["sections"]})
        rec = {"id": f"{n['type']} {n['outline_handle']}", "type": n["type"],
               "section_m2": float(led["section_m2"]) if led["section_m2"] else rng[1],
               "range": rng, "W": n["sections"][0]["W"] / 100.0, "D": n["sections"][0]["D"] / 100.0,
               "perims": perims, "status": led["section_status"]}
        fo = (n.get("footing") or {}).get("outline_handle")
        if fo:
            by_outline.setdefault(fo, []).append(rec)
        else:
            unlinked.append(((n.get("footing") or {}).get("type") or n["type"], rec))
    # three CN necks on FN footings carry no outline handle in T-205: every FN outline carries exactly one CN 0.30 x 0.30
    fn_free = [o["id"] for o in fi["outlines"] if o["tags"] == ["FN"] and o["id"] not in by_outline]
    cn_free = [rec for t, rec in unlinked if rec["type"] == "CN"]
    assert len(fn_free) == len(cn_free) == 3 and all(abs(c["section_m2"] - 0.09) < 1e-9 for c in cn_free)
    for o, rec in zip(sorted(fn_free), cn_free):
        rec = dict(rec, id=rec["id"] + " (FN one-to-one)")
        by_outline[o] = [rec]
    rows, necks = [], []
    for o in fi["outlines"]:
        if o["id"] in EXCLUDED_NECK_FOOTINGS:
            rows.append(W.Row(f"FTG:{o['id']}", "FOOTING", "top outside the necks", "m2", None, W.EXCLUDED,
                              "lift footing FF: base top outside the pit is under the p.14 sheet membrane (T-219 "
                              "WP.LIFT_PIT 15.810 m2): owned there", {"outline_m2": o["area"]}))
            continue
        held = None
        if len(o["tags"]) > 1:
            held = f"one outline, two tags {'+'.join(o['tags'])} (T-233 / T-239 CONFLICT, Q-31 C)"
        rows.append(W.footing_top_row(f"FTG:{o['id']}", "+".join(o["tags"]), o["area"], by_outline.get(o["id"], []),
                                      detail_selected=None, held_outline=held))
    for o, recs in by_outline.items():
        for rec in recs:
            if o in EXCLUDED_NECK_FOOTINGS:
                necks.append(W.Row(f"NECK:{rec['id']}", "NECK", "4 sides", "m2", None, W.EXCLUDED,
                                   "lift column inside the pit walls / FF: the p.14 lift detail (sheet membrane + board, "
                                   "T-219) owns its earth faces"))
                continue
            row = W.neck_row(f"NECK:{rec['id']}", rec["type"], rec["W"], rec["D"])
            if rec["range"][0] != rec["range"][1]:
                row.readings = {"m2_per_m_height_low": rec["perims"][0], "m2_per_m_height_high": rec["perims"][-1]}
                row.held_why += " | SECTION_CONFLICT (T-217)"
            necks.append(row)
    return rows, necks


def other_rows():
    t253 = {r["item"]: r for r in _csv(R / "agents_t253" / "LEDGER_T253.csv")}
    band = sum(float(t253[k]["L_m"]) for k in ("7FE#1", "7FE#2", "7FE#3", "7FC#1", "810#1"))
    return [
        W.Row("BOUNDARY-GB (S-BOUN 7FE / 7FC / 810)", "BOUNDARY_GB", "2 sides x 0.40 below N.G.", "m2", None, W.HELD,
              f"band {band:.2f} m x 2 faces x 0.40 (top at N.G., p.14 A-A) = {band * 2 * 0.40:.4f} gross (20 x 30 "
              "columns through it not deducted: count not printed, M4)", {"gross_m2": band * 2 * 0.40},
              "NOTE_SCOPE: the p.14 boundary-wall detail prints no coating; the p.13 note is printed in the "
              "isolated-footing details (ERS s.3: not carried to another element without its own evidence)"),
        W.Row("BOUNDARY lower G.B + 80 x 30 base", "BOUNDARY_GB", "all earth faces", "m2", None, W.HELD,
              "p.14 A-A: lower G.B depth not written, wall 'as per excavation depth below N.G.'", {},
              "NOTE_SCOPE + DEPTH_NOT_PRINTED"),
        W.Row("STRAPS SB1 / SB2 / SB3", "STRAP", "2 sides + top", "m2", None, W.HELD,
              "strap sections and lengths T-174; ends on footing faces T-219", {},
              "LEVEL_NOT_PRINTED (T-230) + NOTE_SCOPE: straps are not drawn in the p.13 detail"),
        W.Row("LIFT-01 pit walls", "LIFT_PIT", "outer wall faces", "m2", None, W.EXCLUDED,
              "p.14 lift detail: sheet membrane + protection board on the outer faces (T-219 WP.LIFT_PIT, walls HELD on "
              "the pit depth); no liquid coat printed there: owned by that line, never twice"),
        W.Row("GROUND SLAB (29 panels)", "GROUND_SLAB", "soffit on fill", "m2", None, W.EXCLUDED,
              "slab on grade cast on the compacted fill: a soffit cast on earth cannot be liquid-coated; no damp-proof "
              "sheet is printed under it (p.14 'Slab on grade.' draws none): a named exclusion, designer item"),
        W.procurement_row("LIQUID WP (all faces)"),
    ]


def main(write=False):
    runs, gi = build_runs()
    rows = []
    for run in runs:
        rows.extend(W.gb_run_rows(run))
    rows.extend(arc_rows(gi))
    ftg, necks = footing_rows()
    rows.extend(ftg)
    rows.extend(necks)
    rows.extend(other_rows())
    gb_dc = [r for r in rows if r.member == "GROUND_BEAM" and r.status == W.DC]
    by_class = {}
    run_cls = {r["id"]: r["class"] for r in runs}
    for r in gb_dc:
        c = run_cls[r.element]
        by_class.setdefault(c, [0, 0.0])
        by_class[c][0] += 1
        by_class[c][1] = W.r6(by_class[c][1] + r.qty)
    ftg_single = sum(next(iter(r.readings.values())) for r in ftg if r.status == W.HELD and r.readings
                     and len(r.readings) == 1)
    ftg_conf = [r for r in ftg if r.status == W.HELD and len(r.readings) == 2]
    neck_lo = sum(r.readings.get("m2_per_m_height", r.readings.get("m2_per_m_height_low", 0.0))
                  for r in necks if r.status == W.HELD)
    neck_hi = sum(r.readings.get("m2_per_m_height", r.readings.get("m2_per_m_height_high", 0.0))
                  for r in necks if r.status == W.HELD)
    summary = {
        "method": W.METHOD,
        "sources": {"t242": "9455a63d", "t253": "dff9cb79", "t233": "2ecb5bf0", "t205": "5f40dfdb",
                    "structural_sha_prefix": gi["source"]["structural_sha256"][:8]},
        "runs": len(runs),
        "gb_faces_drawing_confirmed": {"faces": len(gb_dc), "m2": W.measured_total(gb_dc), "by_class": by_class},
        "gb_faces_held": sum(1 for r in rows if r.member == "GROUND_BEAM" and r.status == W.HELD
                             and r.face != "soffit"),
        "gb_faces_excluded_above_ground": sum(1 for r in rows if r.member == "GROUND_BEAM" and r.status == W.EXCLUDED
                                              and r.face != "soffit"),
        "gb_soffits_excluded_m2": W.r6(sum(r.readings["face_m2"] for r in rows if r.face == "soffit")),
        "footing_tops": {"outlines_held_detail": sum(1 for r in ftg if r.held_why.startswith("DETAIL")),
                         "single_reading_m2_exact": W.r6(ftg_single),
                         "single_reading_conflict": {r.element: {k: W.r6(v) for k, v in r.readings.items()}
                                                     for r in ftg_conf},
                         "two_tag_held": [r.element for r in ftg if r.held_why == "OUTLINE_HELD"]},
        "necks": {"held": sum(1 for r in necks if r.status == W.HELD),
                  "excluded_lift": sum(1 for r in necks if r.status == W.EXCLUDED),
                  "m2_per_m_height": [W.r6(neck_lo), W.r6(neck_hi)]},
        "measured_total_m2": W.measured_total(rows),
        "totals": W.totals(rows),
    }
    if write:
        with open(HERE / "LEDGER_T263.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["element", "member", "face", "unit", "qty", "status", "basis",
                                              "readings", "held_why"])
            w.writeheader()
            for r in rows:
                d = r.as_dict()
                d["readings"] = json.dumps(d["readings"], sort_keys=True)
                w.writerow(d)
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return rows, summary


if __name__ == "__main__":
    _, s = main(write="--write" in sys.argv)
    print(json.dumps(s, indent=1, sort_keys=True))
