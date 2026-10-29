"""T-339 on the development villa: the roof build-up layers bound to the V3.0.22 candidate lines or NEW rows, closed
against each roof's slab zone less the parapet footprint, cross-checked against the parapet rows, and the FILL table
the roof build-up integration (T-328) consumes unchanged. Research only, read by no method.

    python3 -I research/agents_t339/t339_alsenan.py [--out <dir>]          (default: print the summary only)
    python3 -I research/agents_t339/t339_alsenan.py --slab-lines <V3_0_22_BOQ_LINES.json>   (rebuild SLAB_LINES_T339.json)

Inputs (all committed; local metres, line ids and quantities only, no drawing coordinate, no client data):
  research/agents_t321/ALSENAN_ROOF_LAYERS_INPUT.json, ZONE_LAYER_LEDGER_T321.csv   T-321 (MERGED 59c82a05)
  research/agents_t324/COMPONENT_LEDGER_T324.csv                                     T-324 (MERGED bc5df868)
  research/agents_t342/CANDIDATE_V3022_T342.json, LABEL_BINDING_T342.csv             T-342 (MERGED 4dd9cff8)
  research/agents_t339/MEASURED_T339.json    t339_measure.py on P7757.dxf (slab roof zones to the parapet wall line)
  research/agents_t339/SLAB_LINES_T339.json  own V3.0.22 run: the STR.CONC.SLAB lines under the roofs (ids, m3)
Outputs (--out): BINDING_T339.csv, CLOSURE_T339.csv, CROSSCHECK_T339.csv, FILL_T328_T339.csv, summary.json.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t321"))
import roof_buildup as RB  # noqa: E402
import t339_binding as B   # noqa: E402

T321_IN = ROOT / "research/agents_t321/ALSENAN_ROOF_LAYERS_INPUT.json"
T321_LEDGER = ROOT / "research/agents_t321/ZONE_LAYER_LEDGER_T321.csv"
T324 = ROOT / "research/agents_t324/COMPONENT_LEDGER_T324.csv"
T342_CAND = ROOT / "research/agents_t342/CANDIDATE_V3022_T342.json"
T342_BIND = ROOT / "research/agents_t342/LABEL_BINDING_T342.csv"
MEASURED = HERE / "MEASURED_T339.json"
SLAB = HERE / "SLAB_LINES_T339.json"

# roof -> (candidate roof element, WP-line storey label, structural slab storey, T-324 parapet chain, labels bound)
ROOFS = {"ROOF-430": ("1F-ROOF-AT220", "1F", "GF", "ANNEX", "AT220"),
         "TERRACE-550": ("1F-ROOF-AT216", "1F", "GF", "GF", "AT216"),
         "ROOF-970": ("2F-ROOF-AT379", "2F", "1F", "1F", "AT379 + AT385 (DUPLICATE_OF AT379, T-342)"),
         "ROOF-1390": ("2F-ROOF-TOP", "2F", "2F", "2F", "none (no roof plan, D-62)")}
# T-319 STR.CONC.PARAPET lines per chain (READY agents/task-T-319, V3.0.23; not in V3.0.22): named for the cross-check
T319_LINES = {"ANNEX": "L-1d419b64e8ca1af30fb4", "GF": "L-b5ffc172a354375ca107", "1F": "L-9a2c81164ec6499cc28c",
              "2F": "L-030538dda6a32c601c4c"}
# T-337 NEW FIN.EXT.FINISH PARAPET-OUTER rows per chain (READY agents/task-T-337)
T337_ROWS = {"ANNEX": "NEW FIN.EXT.FINISH PARAPET-OUTER ANNEX +4.30", "GF": "NEW FIN.EXT.FINISH PARAPET-OUTER GF +5.50",
             "1F": "NEW FIN.EXT.FINISH PARAPET-OUTER 1F +9.70", "2F": "NEW FIN.EXT.FINISH PARAPET-OUTER 2F +13.90"}
EDGE_HANDLES = {
    "ROOF-430": {"face": ("B34", "CEC", "ADF", "B3A", "B35", "B38", "B2B", "B41", "B37", "D band B3C / C40 / C47"),
                 "finish": ("hatch D1F", "hatch B2A")},
    "TERRACE-550": {"face": ("B25", "B33", "BDB", "C9E", "B5D", "AE3", "CED", "D band C8A .. CA3 / B5E / C9D"),
                    "finish": ("hatch AE0", "hatch D1A", "hatch 1252")},
    "ROOF-970": {"face": ("1285", "12A7", "1278", "1291", "1281", "1288", "12B9", "12C9", "D band 12E2 / 12E6",
                          "dome circles 12EB / 2F33"),
                 "finish": ("hatch 2F21", "dome circles 12EB / 2F33")},
    "ROOF-1390": {"face": ("12B7", "1292", "1279", "1283", "dome circle 1300"), "finish": ()},
}
SEARCHED = "T-321 search (both DXFs' every text, sanitary sheets, section A-A): no roof layer printed"
Q41 = "Q-41 (screed on roofs, own line) + Lead ruling ELEMENT_REGISTER 2026-10-29: ONE screed volume, Q-45 its mix only"


def _spec(s):
    return [tuple(v[:2]) if v[0] != "ARC" else ("ARC", tuple(v[1]), v[2], v[3], v[4]) for v in s]


def _csv(path):
    return list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))


def inputs():
    t321 = json.loads(T321_IN.read_text(encoding="utf-8"))["roofs"]
    meas = json.loads(MEASURED.read_text(encoding="utf-8"))["roofs"]
    comp = _csv(T324)
    cand = {l["line_id"]: l for l in json.loads(T342_CAND.read_text(encoding="utf-8"))["lines"]}
    return t321, meas, comp, cand


def footprints(comp):
    """parapet top surfaces per T-324 chain (lo, hi): the plan footprint of the parapet (centreline x drawn t)."""
    out = {}
    for r in comp:
        if r["component"] == "TOP_SURFACE":
            ch = r["component_id"].split("/")[0]
            lo, hi = out.get(ch, (0.0, 0.0))
            out[ch] = (lo + float(r["qty_lo"]), hi + float(r["qty_hi"]))
    return out


def roofs():
    t321, meas, comp, _ = inputs()
    fp = footprints(comp)
    out = {}
    for rid, (el, fl, sfl, ch, _) in ROOFS.items():
        z = t321[rid]
        wall = RB.exact_area(_spec(z["face_wall"]))
        dband = RB.exact_area(_spec(z["face_dband"])) if z.get("face_dband") else None
        domes = {n: math.pi * c["r"] ** 2 for n, c in z.get("footprint_circles", {}).items()}
        if rid == "ROOF-1390":
            outer = RB.shoelace([tuple(v) for v in z["outer_wall"]])
            out[rid] = B.Roof(rid, el, fl, sfl, outer, fp[ch], (wall, wall), None, None, domes,
                              held="owner Q-34: the +13.90 roof stays HELD (no number, never 0); no roof plan (D-62)")
            continue
        m = meas[rid]
        finish = m["finish_hatch_m2"]
        if rid == "TERRACE-550":
            # F-T339-1: the D band along the 1F wall foot (the one finish-gap piece, 1.078 m2) is the same physical
            # question as ROOF-430's 0.640 and ROOF-970's 0.1575: the face layers are a range to it, cause named.
            gap = m["finish_gap_pieces"][0]["area_m2"]
            dband = wall - gap
        dd = sum(domes.values())
        face = ((dband if dband is not None else wall) - dd, wall - dd)
        fin = (finish if rid != "ROOF-970" else face[0], finish if rid != "ROOF-970" else face[0])
        # vertical faces round the roof (T-321 s.1); ROOF-970's line also carries the two dome rings (circles 2 pi r)
        up = {"ROOF-430": 35.7279, "TERRACE-550": 52.94,
              "ROOF-970": 65.14 + sum(2 * math.pi * c["r"] for c in z.get("footprint_circles", {}).values())}[rid]
        out[rid] = B.Roof(rid, el, fl, sfl, m["outer_m2_exact"], fp[ch], face, fin, (up, up), domes)
    return out


def _line(cand, el, code):
    for l in cand.values():
        if l["element_id"].startswith(el + ":") and l["item_code"] == code:
            return l
    raise KeyError((el, code))


def bindings():
    _, _, _, cand = inputs()
    rr = roofs()
    rows = []
    for rid, roof in rr.items():
        el = roof.element_id
        hold = roof.held
        h = EDGE_HANDLES[rid]
        face = None if hold else tuple(round(v, 6) for v in roof.face_m2)
        fin = None if (hold or roof.finish_m2 is None) else tuple(round(v, 6) for v in roof.finish_m2)
        dome_txt = (f"; dome footprints {' + '.join(f'{v:.4f}' for v in roof.domes_m2.values())} m2 SCOPE_UNKNOWN "
                    f"beside (T-303 / Q-24 / Q-29 C)") if roof.domes_m2 else ""
        beside_1390 = ("drawing-derived beside, not released: inside the parapet faces 7.70 x 6.45 = 49.665 m2, third "
                       "dome 15.2748 m2 (Q-29: held)") if hold else ""
        # 1. screed to falls: ONE volume, blank (t0 unprinted)
        rows.append(B.bind(roof, "FALLS_SCREED", scope="OWNER_RULE", scope_source=Q41, area=face,
                           quantity=None, quantity_status="HELD", new_row=f"{B.NEW_ITEM['FALLS_SCREED']} {rid}",
                           edge_handles=h["face"],
                           bounds_beside=(beside_1390 or f"basis area {face[0]:.4f} .. {face[1]:.4f} m2 (plan, the 1 % "
                                          f"fall adds 0.005 %){dome_txt}; volume = area x t0 + the falls rise: the part "
                                          f"above the t0 plane on T-321's outline is beside in T-321 s.4, not a bound "
                                          f"of this row"),
                           held_reason="t0 (screed thickness at the outlet) unprinted: D-39 designer; volume HELD, "
                                       "blank, never 0" + (f"; {hold}" if hold else "")))
        # 2. membrane and 3. upturn: the existing waterproofing lines, cross-referenced, unchanged
        lm = _line(cand, el, "FIN.WP.ROOF")
        lu = _line(cand, el, "FIN.WP.ROOF_UPTURN")
        rows.append(B.bind(roof, "MEMBRANE", scope="OWNER_RULE", scope_source="UP-WP-ROOF-001 / Q-24 (membrane inside "
                           "the parapet)", area=face, quantity=None if hold else face,
                           quantity_status="ASSUMED - OWNER-APPROVED", line=lm, edge_handles=h["face"],
                           bounds_beside=beside_1390 or dome_txt.lstrip("; "),
                           held_reason=hold or ""))
        rows.append(B.bind(roof, "UPTURN", scope="OWNER_RULE", scope_source="UP-WP-UPTURN-015 / Q-24: 0.20 m upturn on "
                           "every vertical face round the roof (own lm item)", area=None,
                           quantity=None if hold else roof.upturn_lm, quantity_status="ASSUMED - OWNER-APPROVED",
                           line=lu, upturn_height_m=0.2, upturn_source="Q-24 / UP-WP-UPTURN-015",
                           edge_handles=("parapet inner faces (T-324 inner arris)", "wall faces", "divider faces"),
                           bounds_beside=("faces 65.140 m + the two dome rings 2 x 13.8927 m (circles; the line takes polygons)"
                                          if rid == "ROOF-970"
                                          else beside_1390), held_reason=hold or ""))
        # 4. insulation, 5. protection: no print, no owner rule -> UNKNOWN rows, no number
        for lay, why in (("INSULATION", "printed nowhere, no owner rule"),
                         ("PROTECTION", "printed nowhere; Q-41 gives ONE screed line ('falls / protection'), a "
                                        "separate protection layer is neither printed nor ruled")):
            rows.append(B.bind(roof, lay, scope="UNKNOWN", scope_source=f"{SEARCHED}; {why}", area=None,
                               new_row=f"{B.NEW_ITEM[lay]} {rid}", edge_handles=h["face"],
                               bounds_beside=(beside_1390 or f"if the layer exists, its basis is the face plan "
                                              f"{face[0]:.4f} .. {face[1]:.4f} m2 (text only, not a quantity)"),
                               held_reason="scope UNKNOWN (designer specification): row kept blank, never 0" +
                                           (f"; {hold}" if hold else "")))
        # 6. walking finish: extent printed (designer hatch), material held
        rows.append(B.bind(roof, "FINISH", scope="PRINTED" if not hold else "UNKNOWN",
                           scope_source=("designer finish hatch, layer 3 (extent); material unprinted, no owner rule "
                                         "for roofs (Q-42: roof tile joints 2 mm)") if not hold else "no roof plan (D-62)",
                           area=fin, quantity=fin, quantity_status="DRAWING-CONFIRMED",
                           new_row=f"{B.NEW_ITEM['FINISH']} {rid}", edge_handles=h["finish"],
                           bounds_beside=(beside_1390 or ("dome footprints EXCLUDED (the hatch stops at the dome "
                                                          "circles; no walking surface inside a dome)"
                                                          if roof.domes_m2 else "")),
                           held_reason=("area DRAWING-CONFIRMED, material HELD (no tile / paving type printed): "
                                        "material blank" if not hold else f"{hold}; scope UNKNOWN")))
    B.check_bindings(rows)
    return rows, rr


def closures(rr):
    """R-T339-4 per roof: outer - footprint - layer = named causes."""
    out = []
    r = rr["ROOF-430"]
    out.append(B.closure(r, r.face_m2[1], [["T-324 SW-2 arc top 0.37699 (5 dp) vs exact pi (1.3^2 - 1.1^2) / 4",
                                             0.37699 - math.pi * (1.3 ** 2 - 1.1 ** 2) / 4]], end="hi") |
               {"layer": "FALLS_SCREED / MEMBRANE / INSULATION / PROTECTION (to the wall face)"})
    out.append(B.closure(r, r.face_m2[0], [["D band between the 1F wall face B3A and the band B3C, 0.200 x 3.200",
                                             0.64], ["SW-3 parapet end over the D band, 0.200 x 0.200 (T-324 C1 lo)",
                                                     0.04],
                                            ["T-324 SW-2 arc top 5 dp", 0.37699 - math.pi * (1.3 ** 2 - 1.1 ** 2) / 4]],
                         end="lo") | {"layer": "face layers to the D band (lo)"})
    out.append(B.closure(r, r.finish_m2[0], [["D band 0.200 x 3.200 (the finish hatch stops on it)", 0.64],
                                              ["T-324 SW-2 arc top 5 dp",
                                               0.37699 - math.pi * (1.3 ** 2 - 1.1 ** 2) / 4],
                                              ["hatch arc flattening (T-321)", -0.000032]], end="hi") |
               {"layer": "FINISH (designer hatch)"})
    r = rr["TERRACE-550"]
    out.append(B.closure(r, r.face_m2[1], [["junction square x -0.20 .. 0 at the boundary line: T-324 GF NE-4 runs its "
                                             "outer arris from the divider's far face (19.370 m); it lies beyond the "
                                             "divider east face CED, outside this roof's zone", -0.04],
                                            ["T-324 SW-9 hi 0.279980 vs 1.400 x 0.200 (T-324 rounding)", 0.00002]],
                         end="hi") | {"layer": "face layers to the wall face (hi)"})
    out.append(B.closure(r, r.face_m2[0], [["D band along the 1F wall foot (layer D C8A .. CA3, B5E, C9D): the one "
                                             "finish-gap piece (F-T339-1)", 1.078],
                                            ["SW-9 parapet end at the D band C9E vs the wall face B5D, 0.405 x 0.200 "
                                             "(T-324 C6)", 0.081024], ["junction square in T-324 NE-4", -0.04]],
                         end="lo") | {"layer": "face layers to the D band (lo) = FINISH"})
    r = rr["ROOF-970"]
    dd = sum(r.domes_m2.values())
    stubs = [["T-311 / T-324 1F runs NE-1 and SW-1 (inner arris 0, outer arris 0.080, centreline 0.040 x 0.200 "
              "each): return ends outside the straight 0.20 wall-line outline used here", -0.016],
             ["T-324 sea-side runs NW-1 .. NW-5: centreline 11.8127 m (C3 chord pieces) vs the straight 11.800 here",
              -0.00254]]
    out.append(B.closure(r, r.face_m2[1], [["dome footprints 12EB / 2F33 (2 x pi 2.211092^2), SCOPE_UNKNOWN for the "
                                             "face layers, inside the face outline", dd]] + stubs, end="hi") |
               {"layer": "face layers to the wall face (hi), domes beside"})
    out.append(B.closure(r, r.face_m2[0], [["dome footprints", dd], ["D band 12E2 / 12E6 along the 2F west wall, "
                                                                      "0.075 x 2.100", 0.1575],
                                            ["SW-2 parapet end at the D band (4.125 vs 4.200) x 0.200 (T-324 C2)",
                                             0.01502]] + stubs, end="lo") |
               {"layer": "face layers to the D band (lo) = FINISH (domes excluded)"})
    r = rr["ROOF-1390"]
    out.append(B.closure(r, r.face_m2[1], [], end="hi") |
               {"layer": "drawing-derived beside (HELD Q-34): outer 8.10 x 6.80 vs inner 7.70 x 6.45"})
    for c in out:
        c["named"] = json.dumps(c["named"])
    return out


def crosscheck(rr, meas, comp):
    """R-T339-5 table: what each layer could share with each parapet row, and the measured overlap."""
    rows = []
    for rid, roof in rr.items():
        ch = ROOFS[rid][3]
        m = meas.get(rid, {})
        inner_faces = [r for r in comp if r["component_id"].startswith(ch + "/") and r["component"].startswith(
            "INNER_FACE")]
        zone_lo = sum(float(r["qty_lo"]) for r in inner_faces if r["component"] == "INNER_FACE_UPTURN_ZONE")
        zone_hi = sum(float(r["qty_hi"]) for r in inner_faces if r["component"] == "INNER_FACE_UPTURN_ZONE")
        base = {"roof": rid, "chain": ch}
        if roof.held:
            rows.append(base | {"parapet_row": "all", "layer": "all", "kind": "-", "shared_m2": "",
                                "check": "HELD with the roof (Q-34): no layer row carries a number, nothing to share",
                                "result": "HELD"})
            continue
        rows += [
            base | {"parapet_row": f"parapet footprint (T-324 tops {roof.footprint_m2[0]:.6f} .. "
                                   f"{roof.footprint_m2[1]:.6f} m2; T-319 STR.CONC.PARAPET {T319_LINES[ch]})",
                    "layer": "every plan layer", "kind": "plan",
                    "shared_m2": 0.0,
                    "check": f"every layer edge is the inner face (R-T339-1, area <= face {roof.face_m2[1]:.4f}); "
                             f"slab zone {roof.outer_m2:.4f} - footprint - face closes (CLOSURE_T339)",
                    "result": "0.000 m2"},
            base | {"parapet_row": "parapet footprint polygon (outer 0.20 wall line - inner face)",
                    "layer": "FINISH (designer hatch, independent entity)", "kind": "plan, measured",
                    "shared_m2": m.get("finish_hatch_in_parapet_strip_m2"),
                    "check": f"hatch in the strip {m.get('finish_hatch_in_parapet_strip_m2')} m2; hatch outside the "
                             f"inner face {m.get('finish_hatch_outside_inner_face_m2')} m2 (t339_measure.py)",
                    "result": "0.000 m2 (< 0.00001)"},
            base | {"parapet_row": f"parapet inner face in the upturn zone (T-324 INNER_FACE_UPTURN_ZONE {zone_lo:.3f} "
                                   f".. {zone_hi:.3f} m2, WP edge detail, NO LINE)",
                    "layer": "UPTURN (membrane, existing lm line)", "kind": "vertical",
                    "shared_m2": 0.0,
                    "check": "different items on one face: the membrane upturn (lm, its own line) vs the finish / "
                             "protection over it (m2, T-324 row); no layer here books an m2 on that face",
                    "result": "0.000 m2 (lm vs m2, named)"},
            base | {"parapet_row": "parapet inner face above the upturn (T-324 INNER_FACE_ABOVE_UPTURN) and top "
                                   "(T-324 TOP_SURFACE)", "layer": "INSULATION / PROTECTION / FINISH / FALLS_SCREED",
                    "kind": "vertical", "shared_m2": 0.0,
                    "check": "no upturn height printed for any layer but the membrane: no vertical layer row exists "
                             "(R-T339-5; a skirting / upstand row would need a print)", "result": "0.000 m2"},
            base | {"parapet_row": f"{T337_ROWS[ch]} (T-337, outer face) and the MAS.BLOCK parapet alternative "
                                   "(T-311 / T-333, exclusive with the RC above the upstand)",
                    "layer": "every layer", "kind": "vertical, outside", "shared_m2": 0.0,
                    "check": "the outer face and the parapet body lie outside the inner face; no layer is vertical "
                             "there", "result": "0.000 m2"},
        ]
        if rid in ("ROOF-430", "TERRACE-550"):
            rows.append(base | {"parapet_row": "divider CEC / CED between the annex roof +4.30 and the terrace +5.50, "
                                               "0.200 x 1.300 = 0.260 m2 footprint (T-324: faces / top UNKNOWN, in no "
                                               "T-311 run)", "layer": "every plan layer", "kind": "plan",
                                "shared_m2": 0.0,
                                "check": "both roofs stop on its faces (CEC / CED): in neither roof's layers; its "
                                         "upturn 1.300 m is in each roof's upturn line (two faces, two roofs)",
                                "result": "0.000 m2; footprint named for the parapet rows"})
    return rows


def fill(rows):
    notes = {"FALLS_SCREED": "one SCREED volume per roof (never a second 'falls' row; Q-45 governs the mix of this "
                             "row only); quantity blank HELD on t0; the area is its basis",
             "MEMBRANE": "existing line, not moved by T-328",
             "UPTURN": "existing line, not moved by T-328",
             "INSULATION": "row present, blank: scope UNKNOWN",
             "PROTECTION": "row present, blank: scope UNKNOWN",
             "FINISH": "area DRAWING-CONFIRMED; material blank (HELD)"}
    return B.fill_rows(rows, notes)


LINE_CAUSES = {
    "L-d57d2dc2fafac8bc72d8": "engine face (T-071 / T-062 trace) with the arc B2B as a polyline: arc flattening; T-321 "
                              "compared the hand 55.560 and wrote 0.000",
    "L-2f7502be6f501baf49b1": "line = the wall-face reading (Checker 21:05); the D-band reading 31.643 is the range's "
                              "low end (F-T339-1)",
    "L-636fd3ff1784a12e653b": "candidate deducts the domes as polygons (2 x 15.350), not circles (2 x 15.359) (T-321)",
    "L-d4c73babd2a275c28929": "arc B2B length rounding (T-321)",
    "L-994b88140f2ea50f1b31": "-",
    "L-5ce5ba49792e8f9d1f6f": "dome rings as polygons (27.784) vs circles 27.7854 (T-321)",
}


def line_vs_layer(rows):
    out = []
    for r in rows:
        if r["line_id"] and r["line_quantity"] is not None:
            ref = r["quantity_hi"]
            out.append({"line": r["line_id"], "roof": r["roof"], "layer": r["layer"], "line_qty": r["line_quantity"],
                        "layer_hi": round(ref, 6), "difference": round(r["line_quantity"] - ref, 6),
                        "cause": LINE_CAUSES[r["line_id"]], "action": "none (line unchanged; T-339 binds only)"})
    return out


def slab_lines():
    return json.loads(SLAB.read_text(encoding="utf-8"))


def build_slab(lines_json):
    data = json.loads(Path(lines_json).read_text(encoding="utf-8"))
    lines = data["lines"] if isinstance(data, dict) else data
    import hashlib
    sha = hashlib.sha256(Path(lines_json).read_bytes()).hexdigest()
    out = {"source": f"{Path(lines_json).name} sha256 {sha[:8]}", "lines_total": len(lines),
           "by_floor": {}}
    for l in lines:
        if l.get("item_code") == "STR.CONC.SLAB":
            fl = l.get("floor") or (l.get("location") or {}).get("floor")
            f = out["by_floor"].setdefault(fl, {"lines": [], "m3": 0.0, "blank": 0})
            f["lines"].append(l["line_id"])
            q = l.get("measured_net", l.get("quantity"))
            if q is None:
                f["blank"] += 1
            else:
                f["m3"] += q
    for f in out["by_floor"].values():
        f["lines"].sort()
        f["m3"] = round(f["m3"], 6)
        f["count"] = len(f["lines"])
    return out


def build():
    rows, rr = bindings()
    _, meas, comp, _ = inputs()
    clo = closures(rr)
    xc = crosscheck(rr, meas, comp)
    fl = fill(rows)
    slab = slab_lines()
    sl = []
    for rid, roof in rr.items():
        f = slab["by_floor"].get(roof.slab_floor, {})
        sl.append({"roof": rid, "slab_floor": roof.slab_floor, "slab_lines": f.get("count"),
                   "slab_m3": f.get("m3"), "relation": "UNDER every layer; untouched by the build-up rows; the "
                                                       "per-panel attribution of the slab lines to this roof is NOT "
                                                       "made here (panel ids are SITE ids of the structural sheet)"})
    summ = {
        "candidate": {"lines_sha256_8": json.loads(T342_CAND.read_text(encoding="utf-8"))["lines_json_sha256"][:8],
                      "slab_source": slab["source"]},
        "roofs": {rid: {"outer_m2": None if r.outer_m2 is None else round(r.outer_m2, 6),
                        "footprint_m2": [round(v, 6) for v in r.footprint_m2],
                        "face_m2": [round(v, 6) for v in r.face_m2], "finish_m2": None if r.finish_m2 is None else
                        [round(v, 6) for v in r.finish_m2], "domes_m2": {k: round(v, 6) for k, v in r.domes_m2.items()},
                        "held": r.held} for rid, r in rr.items()},
        "rows": len(rows), "new_rows": sum(1 for r in rows if r["binding"] == "NEW_ROW"),
        "existing_lines": sorted(r["line_id"] for r in rows if r["line_id"]),
        "status_count": {s: sum(1 for r in rows if r["status"] == s) for s in B.STATUSES},
        "closures_close": all(c["closes"] for c in clo),
        "closures": [{k: c[k] for k in ("roof", "layer", "residual_m2", "unexplained_m2", "closes")} for c in clo],
        "shared_with_parapet_m2": round(sum(x["shared_m2"] or 0.0 for x in xc), 6),
        "slab": sl,
        "line_vs_layer": line_vs_layer(rows),
        "finish_new_rows_m2": round(sum(r["quantity_lo"] for r in rows if r["layer"] == "FINISH" and
                                        r["quantity_lo"] is not None), 6),
    }
    return rows, clo, xc, fl, summ


def _write(path, rows):
    if not rows:
        return
    keys = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r[k] is None else (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]))
                        for k in keys})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--slab-lines")
    a = ap.parse_args(argv)
    if a.slab_lines:
        SLAB.write_text(json.dumps(build_slab(a.slab_lines), indent=1, sort_keys=True) + "\n", encoding="utf-8")
        return 0
    rows, clo, xc, fl, summ = build()
    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        _write(out / "BINDING_T339.csv", rows)
        _write(out / "CLOSURE_T339.csv", clo)
        _write(out / "CROSSCHECK_T339.csv", xc)
        _write(out / "FILL_T328_T339.csv", fl)
        (out / "summary.json").write_text(json.dumps(summ, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summ, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
