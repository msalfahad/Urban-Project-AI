"""T-727 development-villa builder: the two T-719 findings on the V-01 light well closed (research, unwired; no
candidate line moved), on the candidate of record ARCH_TAKEOFF_V3.0.72 (T-703 line index).

Reads only repository files, each sha256-pinned (an edited input stops the build):
  research/agents_t727/T727_DRAWN.json              own DXF read by handle this run (t727_extract.py) + the released
                                                    engine's footprints of the same face (areas only)
  research/agents_t345/TRACE_ROWS_T345.csv          the piece record that set the 1F living floor net (T-345, merged):
                                                    STAIR_FLOOR_RESIDUE_V1 rows by id
  research/agents_t703/out/LINE_INDEX_V3_0_72.json  candidate of record V3.0.72
  research/agents_t283/CEILINGS_T283.csv            ceiling ledger R3 (T-283, merged; the decor group's face split)
  research/agents_t719/out/T719_VOIDS.json          void register (T-719, merged): V-07 record, the base-list check
Typed here (cited): the T-421 threshold deduction 0.300 m2 on L-b06400d4 (33.711036 -> 33.411036, T-421 table row
'Threshold's floor part on the landing floor'), the only change to the net after the T-345 trace.

    python3 -I research/agents_t727/t727_alsenan.py           # writes out/T727_VOIDS_CLOSED.json and .md
    python3 -I research/agents_t727/t727_alsenan.py --check   # rebuilds in memory, compares byte for byte
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t727_rules as R  # noqa: E402

D, q6 = R.D, R.q6
DRAWN = HERE / "T727_DRAWN.json"
TRACE = ROOT / "research/agents_t345/TRACE_ROWS_T345.csv"
INDEX = ROOT / "research/agents_t703/out/LINE_INDEX_V3_0_72.json"
CEIL = ROOT / "research/agents_t283/CEILINGS_T283.csv"
T719 = ROOT / "research/agents_t719/out/T719_VOIDS.json"
PINS = {DRAWN: "c405679a020a46acce954f0618a0059ea147b37a19fe0453f39509cb9fb623b0",
        TRACE: "476c7a6b9dc46ec6da34ec06328ea35c94130300a0fd85129076aca83d749c13",
        INDEX: "8e753204d90ebf75d8fa5fe3de120f235bdb16e06a7d677e6aeb615e84ef5d2b",
        CEIL: "10214b3dbffcf57a5327130edd65794646864c60cb11abb090e1f1906d30d522",
        T719: "8ffcd16db639aaec2a19e3cfb5917c1f4d8fba48f3632da207e96f7aa3ba1508"}
OUT_JSON = HERE / "out" / "T727_VOIDS_CLOSED.json"
OUT_MD = HERE / "out" / "T727_VOIDS_CLOSED.md"

FLOOR = "L-b06400d46d252f242018"
BED = "L-ebce765b"
DECOR = "L-43bf1f869e1588f1d3bd"
OVER_VOID = "L-35341ff2e6a848b9436b"
GF_CEIL = "L-eb3be58fc760b39f0e38"
TREAD_F1, TREAD_F4 = "L-6cf11c2d", "L-ea55ed31"
T421_THRESHOLD = D("0.300")
FACE_M2 = D("75.983002")                       # 1F-R78C367 face (T-345 conservation face; T727_DRAWN engine face)
BELOW_SEEN = ("F1", "F4", "F6")


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load():
    for p, h in PINS.items():
        if _sha(p) != h:
            raise SystemExit(f"input changed: {p.relative_to(ROOT)} sha256 {_sha(p)[:12]} != pinned {h[:12]}")
    dr = json.loads(DRAWN.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(TRACE.open(encoding="utf-8")))
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    ceil = list(csv.DictReader(CEIL.open(encoding="utf-8")))
    t719 = json.loads(T719.read_text(encoding="utf-8"))
    L = {}
    for ln in idx["lines"]:
        L[ln["line_id"]] = ln
        L[ln["line_id"][:10]] = ln
    return dr, rows, idx, ceil, t719, L


def _in_well(row):
    """a piece-record row lies in the light well when it is the void, a flight of the plan below, or a residue cell that
    touches only the void / flights of the plan below (its note 'touches F..'); cells touching an own flight (F2 / F3 /
    F5, the ST-01 dog-leg) are the dog-leg well, outside the light well."""
    if row["category"] in ("VOID", "TREADS_BELOW_SEEN"):
        return True
    if row["category"] in ("VOID_RESIDUE", "STAIR_FOOTPRINT"):
        note = row["note"]
        t = note.split("touches ", 1)[1].split(";")[0] if "touches " in note else ""
        fl = [x.strip() for x in t.split("/") if x.strip()]
        return bool(fl) and all(f in BELOW_SEEN for f in fl)
    return False


def build():
    dr, rows, idx, ceil, t719, L = _load()
    j, wp, roof = dr["junction_F1_F4"], dr["well_pieces_1F"], dr["roof_over_well_2F"]
    floor = [r for r in rows if r["line_id"] == FLOOR]
    out = {"task": "T-727", "candidate": idx["candidate_version"], "rule": "R-T727-1 .. -4 (t727_rules.py)",
           "tol_m2": str(R.TOL_M2), "moved": []}

    # ---- 1. the F1 / F4 overlap re-measured by handle ---------------------------------------------------------------
    strip = q6(D(str(j["lengths_m"]["B43"])).min(D(str(j["lengths_m"]["B4E"]))) * D(str(j["spacing_m"])))
    ex, twice = R.overlap_named([j["F1_footprint_m2"], j["F4_footprint_m2"]], j["F1_F4_union_m2"])
    out["overlap"] = {
        "handles": j["handles"], "layers": j["layers"], "lengths_m": j["lengths_m"], "spacing_m": j["spacing_m"],
        "parallel": j["parallel_same_direction"], "gf_plan_same_place": j["gf_plan_same_place"],
        "strip_by_handles_m2": str(strip), "engine_footprint_overlap_m2": j["engine_footprint_overlap_m2"],
        "overlap_w_h_m": j["engine_footprint_overlap_w_h_m"],
        "handle_vs_engine_m2": str(q6(D(str(j["engine_footprint_overlap_m2"])) - strip)),
        "handle_vs_engine_cause": "F1 is radial: its last riser is drawn 1.1498 wide (engine riser_widths), so its last "
                                  "quad is a hair short of the 1.150 rectangle between B43 and B4E",
        "sum_minus_union_m2": str(ex), "exceeds_tol": twice, "inside_void_window_m2": wp["overlap_inside_void_window_m2"],
        "inside_well_m2": wp["overlap_inside_well_m2"]}

    # ---- 2. the 1F living floor: which list set the net (R-T727-3), and the union check (R-T727-1) -------------------
    rec = [(f"{r['category']} {r['item_id'].split(':')[-1]}", r["amount"]) for r in floor]
    prov, pres = R.net_provenance(FACE_M2, rec, [("T-421 threshold certain part", T421_THRESHOLD)],
                                  L[FLOOR]["measured_net"])
    well_rows = [(f"{r['category']} {r['item_id'].split(':')[-1]}", r["amount"]) for r in floor if _in_well(r)]
    res_net, r_net = R.deduction_check(wp["face_in_well_m2"], well_rows)
    base = [("engine VOID", wp["void_window_m2"]), ("engine STAIR_BELOW_SEEN (base list: F1 + F4 + F6 summed)",
             wp["below_seen_sum_m2"]), ("T-116 residue as typed by T-719", "3.453")]
    res_base, r_base = R.deduction_check(wp["face_in_well_m2"], base)
    geo = [("void window", wp["void_window_m2"])] + [(f"{k} (union increment)", v) for k, v in
                                                       wp["below_seen_union_increments_m2"].items()] + \
          [("remainder (residue cells)", wp["remainder_after_void_and_union_m2"])]
    res_geo, r_geo = R.deduction_check(wp["face_in_well_m2"], geo)
    below_rec = {r["item_id"].split(":")[-1]: r["amount"] for r in floor if r["category"] == "TREADS_BELOW_SEEN"}
    t719_v01 = next(x for x in t719["register"] if x["void"] == "V-01")
    out["floor_1F"] = {
        "line": FLOOR, "class": L[FLOOR]["class"], "measured_net": L[FLOOR]["measured_net"],
        "bed_line_same_area": {"line": L[BED]["line_id"], "measured_net": L[BED]["measured_net"]},
        "net_record": {"source": "T-345 TRACE_ROWS (STAIR_FLOOR_RESIDUE_V1 piece rows + floor-scope rows)",
                       "rows": len(floor), "later": "T-421 threshold 0.300", "result": prov, "residual_m2": str(pres)},
        "face_in_well_m2": wp["face_in_well_m2"], "well_m2": wp["well_m2"],
        "net_record_in_well": {"rows": well_rows, "result": res_net, "residual_m2": str(r_net),
                               "below_seen_rows_m2": below_rec,
                               "below_seen_rows_sum_m2": str(q6(sum(D(v) for v in below_rec.values())))},
        "own_geometry_in_well": {"rows": geo, "result": res_geo, "residual_m2": str(r_geo),
                                 "below_seen_union_m2": wp["below_seen_union_m2"]},
        "t719_base_list_check": {"rows": base, "result": res_base, "residual_m2": str(r_base),
                                 "t719_result": t719_v01["floor_1F"]["result"],
                                 "t719_if_corrected_m2": next((f["if_corrected"] for f in t719["flags"]
                                                               if f["line"] == FLOOR), None)},
        "verdict": ("ENGINE_RIGHT on the net (the overlap is deducted once, on F1; F4 carries its union increment); "
                    "T-719 finding (1) withdrawn: it checked the superseded base list (ENGINE_LIST_STALE, T-345), not "
                    "the record that set the net")
        if prov == "RECORD_OF_NET" and res_net == "DEDUCTED_ONCE" and res_base == "DEDUCTED_TWICE" else "UNRESOLVED",
        "corrected_m2": L[FLOOR]["measured_net"],
        "not_applied": "33.468204 (T-719 if-corrected) would add the 0.0575 m2 stair strip inside the opening back as "
                       "porcelain floor"}

    # ---- 3. ceiling over V-01: one face, one line (R-T727-2) -------------------------------------------------------
    c = {r["SURFACE"]: D(r["QTY"]) for r in ceil if r["FACE"] == "1F-R78C367" and r["UNIT"] == "m2" and r["QTY"]}
    decor = c['horizontal decor ceiling (gypsum), incl. bulkhead undersides']
    stair_zone = c['stair zone (stair face of the slab plan)']
    dome = c['under an open dome position (Q-44 A; DCR-4)']
    beyond = c['stair zone beyond the stair face (R-CEIL-R3-1: flight under a beam band)']
    face_sum = q6(decor + stair_zone + dome + beyond)
    own = R.face_owner("V-01 top (1F roof soffit over the light well)", [
        {"line_id": DECOR, "face_contains": True, "value": L[DECOR]["measured_net"]},
        {"line_id": OVER_VOID, "face_contains": False, "value": L[OVER_VOID]["measured_net"]}])
    out["ceiling_top"] = {
        "roof_over_well_2F": {"entities": roof["entities_crossing_well_by_type_layer"],
                              "named": roof["named_entities"], "opening_outline_found": roof["opening_outline_found"]},
        "decor_face_split_m2": {"decor": str(decor), "ST-01 stair zone": str(stair_zone), "east dome HELD": str(dome),
                                "stair beyond face": str(beyond), "sum": str(face_sum),
                                "face": str(FACE_M2), "residual": str(q6(FACE_M2 - face_sum))},
        "decor_line": {"line": DECOR, "class": L[DECOR]["class"], "measured_net": L[DECOR]["measured_net"],
                       "equals_ledger": q6(L[DECOR]["measured_net"]) == q6(decor)},
        "well_top_in_decor_m2": roof["roofed_face_in_well_m2"],
        "st01_zone_in_well_m2": roof["own_flights_F2_F3_F5_in_well_m2"],
        "st01_zone_gap_to_well_m": roof["own_flights_F2_F3_F5_gap_to_well_m"],
        "well_top_under_east_dome_m2": roof["east_dome_overlap_with_face_in_well_m2"],
        "over_void_line": {"line": OVER_VOID, "class": L[OVER_VOID]["class"], "value": L[OVER_VOID]["measured_net"],
                           "names_m2": t719_v01["ceiling_top"]["note"].split("names ")[1].split(" ")[0]
                           if "names " in t719_v01["ceiling_top"]["note"] else None},
        "ownership": own,
        "gf_ceiling": {"line": GF_CEIL, "measured_net": L[GF_CEIL]["measured_net"],
                       "t719_result": t719_v01["ceiling_GF"]["result"]}}

    # ---- 4. V-07 stays HELD (R-T727-4) -----------------------------------------------------------------------------
    v7 = next(x for x in t719["register"] if x["void"] == "V-07")
    out["V-07"] = dict(R.held_void("V-07", v7["evidence"] +
                                   "; scenario S0 (approved design, no opening) vs S1 (open skylight) not decided "
                                   "(Q-29 / T-185)"),
                       disc_if_opened_m2=v7["disc_if_opened_m2"], over_2f_faces_m2=v7["over_2f_faces_m2"],
                       lines=v7["lines"])

    # ---- 5. downstream: the same strip in the held stair tread highs (named, not this task's line) -------------------
    hi = q6(D(str(L[TREAD_F1]["held_high"])) + D(str(L[TREAD_F4]["held_high"])))
    out["downstream"] = [{
        "lines": [L[TREAD_F1]["line_id"], L[TREAD_F4]["line_id"]], "what": "FIN.MARBLE.TREAD 1F-R78C367 flights 1 / 4 "
        "(HELD 0 .. high)", "highs_sum_m2": str(hi), "union_m2": j["F1_F4_union_m2"],
        "excess_m2": str(q6(hi - D(str(j["F1_F4_union_m2"])))), "result": "DOUBLE_COUNT_RISK in the held highs (R-T727-1)",
        "owner": "stair ledger (lane A stairs / T-725 family); never valued as the sum"}]
    return out


def render_md(o):
    f, c, ov = o["floor_1F"], o["ceiling_top"], o["overlap"]
    w = [f"# T-727 V-01 light-well deductions closed ({o['candidate']}; research, unwired; no line moved)", "",
         f"Rules {o['rule']}; tolerance {o['tol_m2']} m2.", "",
         "## 1. F1 / F4 overlap by handle", "",
         f"- B43 (layer {ov['layers']['B43']}, F4 first riser) {ov['lengths_m']['B43']} m and B4E (layer "
         f"{ov['layers']['B4E']}, F1 last line) {ov['lengths_m']['B4E']} m, parallel {ov['parallel']}, "
         f"{ov['spacing_m']} m apart: strip {ov['strip_by_handles_m2']} m2.",
         f"- Engine footprints F1 x F4: {ov['engine_footprint_overlap_m2']} m2 ({ov['overlap_w_h_m'][0]} x "
         f"{ov['overlap_w_h_m'][1]}); handle - engine {ov['handle_vs_engine_m2']} m2 ({ov['handle_vs_engine_cause']}).",
         f"- GF plan draws the same pair: {ov['gf_plan_same_place']}. Inside the void window "
         f"{ov['inside_void_window_m2']}, inside the well {ov['inside_well_m2']} m2.", "",
         "## 2. 1F living porcelain " + f["line"][:10], "",
         f"- Net {f['measured_net']} ({f['class']}); record of the net: {f['net_record']['result']} "
         f"(residual {f['net_record']['residual_m2']}).",
         f"- Face in well {f['face_in_well_m2']}: net record rows in the well -> {f['net_record_in_well']['result']} "
         f"(residual {f['net_record_in_well']['residual_m2']}); below-seen rows {f['net_record_in_well']['below_seen_rows_m2']}"
         f" = {f['net_record_in_well']['below_seen_rows_sum_m2']} (union {f['own_geometry_in_well']['below_seen_union_m2']}).",
         f"- Own geometry (void + union increments + remainder): {f['own_geometry_in_well']['result']} "
         f"(residual {f['own_geometry_in_well']['residual_m2']}).",
         f"- T-719 base-list check: {f['t719_base_list_check']['result']} ({f['t719_base_list_check']['residual_m2']}); "
         f"its if-corrected {f['t719_base_list_check']['t719_if_corrected_m2']} is NOT applied.",
         f"- Verdict: {f['verdict']}. Corrected figure: **{f['corrected_m2']} m2** (unchanged).", "",
         "## 3. Ceiling over V-01", "",
         f"- 2F plan over the well: {c['roof_over_well_2F']['entities']}; opening outline found: "
         f"{c['roof_over_well_2F']['opening_outline_found']} (roof slab closed; block ROOF).",
         f"- Decor face split {c['decor_face_split_m2']}; line {c['decor_line']['line'][:10]} = ledger: "
         f"{c['decor_line']['equals_ledger']}.",
         f"- Well top in the decor face {c['well_top_in_decor_m2']} m2; under the east dome (HELD) "
         f"{c['well_top_under_east_dome_m2']} m2; ST-01 stair zone (own flights F2 / F3 / F5) in the well "
         f"{c['st01_zone_in_well_m2']} m2, {c['st01_zone_gap_to_well_m']} m away (the 0.1725 band piece is the ST-01 "
         "first going, T-283).",
         f"- Owner {c['ownership']['owner'][:10]}; {c['ownership']['excluded']}; result {c['ownership']['result']}.", "",
         "## 4. V-07", "", f"- {o['V-07']['status']} {o['V-07']['result']}: {o['V-07']['cause']}.", "",
         "## 5. Downstream (named)", ""]
    for d in o["downstream"]:
        w.append(f"- {d['what']}: highs {d['highs_sum_m2']} vs union {d['union_m2']} -> {d['excess_m2']} m2, "
                 f"{d['result']}; {d['owner']}.")
    return "\n".join(w) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    o = build()
    js = json.dumps(o, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n"
    md = render_md(o)
    if "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == js and OUT_MD.read_text(encoding="utf-8") == md
        print("T-727 rebuild identical:", ok)
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(js, encoding="utf-8")
    OUT_MD.write_text(md, encoding="utf-8")
    print("written", OUT_JSON.name, OUT_MD.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
