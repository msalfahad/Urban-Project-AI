"""T-761 (lane S, DELIVERY MODE F-02): the 80 blank STR.CONC.* lines of ARCH_TAKEOFF_V3.0.78 to figures.

    python3 -I research/agents_t761/fill_t761.py            # writes research/agents_t761/out/FIX_ROWS.{json,md}

Fallback order (DELIVERY_MODE s.3): drawing geometry -> drawn / printed reading -> COMPANY DEFAULT (AGENT_BRIEF table,
owner 2026-11-13) -> ratio of this villa -> SAFETY. Every row carries line id, item, unit, before, after, label, basis.
Materiality (owner 2026-11-13 14:00): a piece KNOWN to be < 0.05 m3 is IGNORED_SMALL (logged by id with its size, not
added to the total) and the SAFETY line covers the ignored sum (1 m3 if the sum < 1 m3, else the sum). The rule file
itself belongs to T-757; this row only applies it. Ranged (bounded) lines are NOT touched here: each is listed with the
designer item that holds it (T-755 sweep), as the row's acceptance allows.

Inputs are merged, Checker-read research files only (no private data): the line index, T-699 lintel ledger, T-712 GB
ledger, T-721 projection ledger, T-724 strip pieces, T-711 stair ledger, T-319 parapet runs, T-401 lift structure,
T-667 pool blinding, T-254 boundary GB, route G registers, T-755 sweep. Each figure's dimension chain is in its basis.
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
R = lambda p: os.path.join(ROOT, p)

INDEX = "research/agents_t738/out/LINE_INDEX_V3_0_78.json"
SMALL = 0.05            # m3, owner materiality threshold
LINTEL_BEARING = 0.15   # company default, each side
BEAM_DEFAULT_D = 0.60   # company default when no same mark / adjacent span depth is printed
PLATE_T = 0.16          # ST-01 printed stair plate thickness (T-711: plates 'T 0.16')
ROOF_BUILDUP = 0.075 + 0.05 + 0.05  # company default roof build-up at the edge: screed avg + insulation + protection (membrane ~0)
PARAPET_DEFAULT_H = 1.20            # company default parapet height above the finished roof (used only where none printed)


def gb_class_depth(clear_span):
    """ST p.13 typical interior GB sections 30x30 (< 2.5 m), 30x40 (< 5 m), 30x60 (>= 5 m) by clear span
    (route G convention; exterior / loaded runs take the same mark = company default)."""
    if clear_span < 2.5:
        return 0.30
    if clear_span < 5.0:
        return 0.40
    return 0.60


def main():
    idx = json.load(open(R(INDEX)))
    lines = {l["line_id"]: l for l in idx["lines"]}
    blank = [l for l in idx["lines"] if l["item_code"].startswith("STR.CONC") and l["class"] == "HELD" and l["held_low"] is None]
    ranged = [l for l in idx["lines"] if l["item_code"].startswith("STR.CONC") and l["class"] == "HELD" and l["held_low"] is not None]
    sweep = {r["line_id"]: r for r in json.load(open(R("research/agents_t755/out/T755_CONCRETE_SWEEP.json")))["rows"]}
    rows = {}

    def put(lid, value, label, basis, piece=None):
        assert lid in lines and lid not in rows, lid
        assert value is not None and value > 0 and label in ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY"), (lid, value, label)
        l = lines[lid]
        small = value < SMALL
        rows[lid] = {"line_id": lid, "item_code": l["item_code"], "unit": l["unit"], "element_id": l["element_id"],
                     "before": {"class": l["class"], "net": l["measured_net"], "low": l["held_low"], "high": l["held_high"]},
                     "after": ({"class": "IGNORED_SMALL", "size_m3": round(value, 4), "covered_by": "NEW:STR.CONC.SAFETY"}
                               if small else {"class": "RELEASED", "net": round(value, 4)}),
                     "label": label, "basis": basis, "designer_item": sweep.get(lid, {}).get("bucket")}

    # ---- 1. LINTELS (21): B x D from the T-699 ledger (ST p.13 schedule B = wall width, D 0.20) x (width + 2 x 0.15)
    for r in json.load(open(R("research/agents_t699/out/T699_LEDGER.json")))["lines"]:
        w = r["width_m"]
        note = ""
        if isinstance(w, list):  # D-GF-09: drawn gap 0.90 vs printed frame D120 1.00 (T-581)
            w, note = 1.00, "; width = printed door type D120 1.00 (drawn gap 0.90 gives 0.048: same materiality class boundary, named)"
        L = w + 2 * LINTEL_BEARING
        v = r["B_m"] * r["D_m"] * L
        extra = {"CONDITIONAL_EXCLUSION": "; existence default = one lintel per opening (owner lintel rule) although a beam may serve the head (" + str(r.get("conditional_exclusion_member")) + ")",
                 "OPEN": "; existence default = one lintel per opening (owner lintel rule)"}.get(r["existence"], "")
        if r["opening"] == "A-GF-01":
            extra += "; arched head: straight-lintel equivalent (curved crown not printed, T-238)"
        put(r["line_id"], v, "DEFAULT",
            f"{r['opening']}: {r['B_m']:.2f} x {r['D_m']:.2f} (ST p.13 schedule) x ({w:.2f} + 2 x 0.15 bearing default) = {v:.4f} m3"
            f"{note}{extra}; printed note 'MIN 40 cm' bearing would give {r['B_m'] * r['D_m'] * (w + 0.80):.4f}")

    # ---- 2. GROUND BEAMS (21): drawn area (T-712 / T-724 / route G) x class depth by clear span (exterior GB = same mark)
    led = {r["line_id"]: r for r in json.load(open(R("research/agents_t712/out/T712_LEDGER.json")))["lines"]}
    reg = {r["ITEM_ID"]: r for r in csv.DictReader(open(R("research/urban_engine_m2_generalization/alsenan_route_g/PROVISIONAL_REGISTER.csv")))}
    ring_0042 = math.pi / 2 * 1.15  # annex NE quarter ring r 1.00 .. 1.30: centre-line length
    for lid, r in led.items():
        if lid not in lines or lines[lid]["held_low"] is not None or lid in rows:
            continue
        e = r["element_id"]
        if "area_m2" in r:
            area = float(r["area_m2"])
        else:  # D-35 court stretches: m3 per m of depth = drawn net plan area
            area = float(r["m3_per_m_depth"][0])
        if r.get("spans_m"):
            span = min(float(s) for s in r["spans_m"])
            sp_src = f"clear span {span:.2f} (T-712)"
        elif e.endswith("BAND0042"):
            span = ring_0042
            sp_src = f"quarter ring centre-line {span:.2f}"
        else:
            span = float(json.loads(reg[e]["DIMENSIONS"])["length_m"])
            sp_src = f"clear span {span:.2f} (route G register)"
        if e.endswith("BAND0010.3"):
            d = 0.60  # 5.00 m ON_LIMIT: route G class at the c/c reading 5.30 (both readings 30x60)
            sp_src += " ON_LIMIT, c/c 5.30 -> 30x60 (route G both readings)"
        else:
            d = gb_class_depth(span)
        v = area * d
        put(lid, v, "DEFAULT",
            f"drawn plan {area:.4f} m2 x {d:.2f} (ST p.13 typical 30x{int(d * 100)} by {sp_src}; company default exterior / loaded GB = same mark) = {v:.4f} m3; holds {r['d_id']}")
    # boundary GB at natural ground (T-253 / T-254 / T-724 F-T723-3)
    put("L-fb7a6431fede62e93fd5", 3.5256, "DRAWING-READ",
        "boundary band 5 runs 44.07 m: 8.8140 m2 (Checker own) x 0.40 (ST p.14 'GROUND BEAM (20x40)') = 3.5256 m3; minus 0.024 m3 per boundary column (count not printed, each below materiality: not deducted)")

    # ---- 3. BEAMS (16): projection strips / boxes (T-721) and T-729 children (T-724) at the beam default 0.60;
    #         east dome ring at the twin west ring depth (same DETAIL OF DOME, B4 0.50: adjacent / same-type)
    for r in json.load(open(R("research/agents_t721/out/T721_LEDGER.json")))["rows"]:
        lid = r["line_id"]
        if lid == "L-ab37afa17f2ac5b0efd1":
            v = 1.7993 * 0.50
            put(lid, v, "DEFAULT", "east dome-opening ring in bay: plan 1.7993 m2 (T-721) x 0.50 = depth of the twin west ring B4 (L-48b7d139 released 0.7552, same ST p.7 DETAIL OF DOME; adjacent-span default) "
                f"= {v:.4f} m3; 0.60 default would give {1.7993 * 0.60:.4f}; D-28 replaces it")
            continue
        a = float(r["m3_per_m_depth"])
        v = a * BEAM_DEFAULT_D
        put(lid, v, "DEFAULT", f"{r['member']}: plan {a:.4f} m2 (T-721 DXF) x 0.60 (company default: no mark, no section, adjacent span unprinted) = {v:.4f} m3; "
            f"slab-cast at 0.16 would give {a * 0.16:.4f}; D-05 / D-26 replace it")
    for lid, piece, a in (("L-f113ed57f7875fed9a67", "GF-STRIP-AT-COL", 0.16), ("L-e296002577c012f0afd4", "GF-NW-CORNER", 0.029309),
                          ("L-56c49c3c2596a0869533", "1F-STRIP-AT-COL", 0.16), ("L-89d266a3e5280a10a3b9", "1F-NW-CORNER", 0.029309)):
        put(lid, a * BEAM_DEFAULT_D, "DEFAULT", f"{piece}: plan {a} m2 (T-724 census) x 0.60 company default = {a * 0.6:.4f} m3")

    # ---- 4. COLUMNS (2): schedule governs: tank columns 2F at the same mark's 1F / 2F value (0.10 m2 x 4.20)
    for lid, mark in (("L-0ede77cfd0badc4c7d62", "C2@247685,64087"), ("L-c10e2945d582b5a03126", "C3@247476,61310")):
        put(lid, 0.42, "DEFAULT", f"{mark} 2F: schedule section 0.10 m2 x storey 4.20 = 0.4200 m3 (= released 1F lines of the same mark, route G register 0.42); B15 up / down-stand on the tank (D-44) not added")

    # ---- 5. NECKS (4, lift columns): route G register base (founding at the printed minimum, neck top at the GB)
    rel = {r["ITEM_ID"]: r for r in csv.DictReader(open(R("research/urban_engine_m7_reliability/st7757/RELEASE_REGISTER.csv")))}
    for lid in ("L-12f3d8b9375cac407bca", "L-8eb74a02fcf5ae4465f8", "L-953e87a3e9d0425d404e", "L-dd6d11415961b554e906"):
        e = lines[lid]["element_id"]
        b = float(rel[e]["BASE"])
        put(lid, b, "DEFAULT", f"{e.split(':')[-1]}: route G base {b:.4f} m3 (schedule section x neck from the printed minimum founding to the GB; register high {float(rel[e]['HIGH']):.4f}); lift raft level (D-43) replaces it")

    # ---- 6. LIFT (2) (T-401)
    put("L-5ae06fda7d729d54c033", 0.650, "DEFAULT", "GF tie beam (ST p.8 n.19), runs 1.80 / 1.80 / 1.20 / 0.70 = 5.50 m: nearest printed section = the GF-roof shaft ring beams on the same runs "
        "(B14 0.20x0.75x1.80 0.270 + B1 0.20x0.40x0.70 0.056 + B7 0.20x0.75x1.20 0.180 + B1 0.20x0.40x1.80 0.144) = 0.650 m3; D-43 replaces it")
    put("L-684fcad323adc0c8a267", 1.100 * 1.50, "SAFETY", "pit walls 0.20 ring: plan 1.100 m2 (T-401, Checker T-394) x 1.50 m pit height = 1.650 m3; pit depth is a lift-supplier item (D-43 / RFI L-1) "
        "and no company default exists: 1.50 is the SAFETY height (upper end of usual home-lift pits), replaced by the supplier depth")

    # ---- 7. PARAPETS (4): T-319 runs: top (centreline x t) x (printed height above finish + roof build-up default)
    runs = list(csv.DictReader(open(R("research/agents_t319/V3_0_23_RUNS_T319.csv"))))
    by = {}
    for r in runs:
        top = float(r["top_m2"].split("..")[0])
        if r["h_status"] == "PRINTED":
            h, hs = float(r["h_above_finish_m"].split("..")[0]), "printed"
        else:
            h, hs = PARAPET_DEFAULT_H, "default 1.20"
        by.setdefault(r["line_id"], []).append((r["run"], top, h, hs))
    for lid, rr in by.items():
        v = sum(t * (h + ROOF_BUILDUP) for _, t, h, _ in rr)
        chain = lines[lid]["element_id"].split("#")[0]
        txt = "; ".join(f"{n} {t:.4f} x ({h:.3f} {hs} + 0.175)" for n, t, h, hs in rr)
        put(lid, v, "DEFAULT", f"{chain}: sum of runs top m2 (T-319 / T-324 drawn) x (height above finish + roof build-up default 0.175) = {v:.4f} m3 [{txt}]; "
            "all-RC above the slab top (P7757 sections A-A / B-B cut every parapet in RC = this villa's drawing; ST p.14 P1 'typical' alternative = RC 0.30 upstand "
            f"{sum(t for _, t, _, _ in rr) * 0.30:.4f} m3 + block above; Q-65 C designer answer replaces it)")

    # ---- 8. STAIRS (5) (T-711 ledger; risers / treads default; waist = printed plate 0.16)
    e1_slope = math.hypot(5 * 0.30, 5 * 0.17)
    v = 0.355017 + e1_slope * 2.80 * PLATE_T
    put("L-061e18cf35a4b6b33d68", v, "ESTIMATE", f"ST-03 E1: steps 0.3550 (T-258 / T-711) + waist {e1_slope:.3f} slope x 2.80 x 0.16 (ST-01 printed plate) = {v:.4f} m3; S-9 / D-56 replaces the waist")
    put("L-7863355dfcb68a681d2d", 1.213429, "DEFAULT", "ST-01 GF->1F remainder: reading A (27 equal risers 0.1667, within the 0.15-0.175 default) 0.8630 + winder wedges 1/2 x 0.1667 x 1.44 + flat turn 1.44 x 0.16 = 1.2134 m3 (T-711); reading B 1.4009")
    put("L-659243ed9fc2831c3ae8", 0.328 * PLATE_T * 1.20, "DEFAULT", "ST-01 MS2 turn riser: height 0.168 + 0.16 = 0.328 x thickness 0.16 (plate) x width 1.20 (turn 1.44 m2) = 0.0630 m3 (T-711 per-unit)")
    put("L-821032bc04a0b0d02133", 1.035 * PLATE_T, "ESTIMATE", "ST-01b lobby D1 waist under 4 steps: plan 1.035 m2 (T-711) x 0.16 plate = 0.1656 m3 (if on compacted fill: 0)")
    slope = math.hypot(1.0, 0.1607 / 0.28)
    v = 2.05385 * (4.50 / 28) + 4.1077 * PLATE_T * slope
    put("L-b6b0354b7842f0ed6e41", v, "ESTIMATE", f"ST-02 round stair 12 curved treads: wedges 2.05385 m3/m x riser 4.50/28 = 0.3301 (T-711) + helicoid waist 4.1077 m2 x 0.16 x slope {slope:.3f} = {4.1077 * PLATE_T * slope:.4f}; CA (0 .. 0.09) in SAFETY; D-08 replaces it")

    # ---- 9. DOME-3, POOL steps, BLINDING (2), BOUNDARY PAD (1)
    put("L-d5401fa8986900c66c37", 2.540681, "DEFAULT", "DOME-3 tower dome: arch circle r 2.205 (dia 4.41) and SE elevation 441 / 215 = the shells A / B; the only ST p.7 DETAIL OF DOME (442 / 190 / 10) -> same shell 2.5407 m3 (L-8ea34765 / L-fffa895e released); D-21 replaces it")
    put("L-b62a7065645589011141", 0.30 * 2.00 * 0.38, "SAFETY", "pool steps not drawn (T-667 R-T667-5; consultant P-2): SAFETY block 0.30 x 2.00 x 0.38 = 0.228 m3 (one bench step across the 3.50 back wall, the size the reference workbook carries; never VERIFIED)")
    put("L-893c3db13b14dc38625e", 0.915529, "DRAWING-READ", "pool blinding: outline 7C6 grown by the printed wrap 0.10, clipped at the plot line, 11.8511 - 2.6958 (pit blinding already in L-98eb2d58) = 9.1553 m2 x 0.10 = 0.9155 m3 (T-667)")
    n_pads = 10
    put("L-cda8f41522dc6f42b3d6", n_pads * 1.30 * 0.80 * 0.30, "SAFETY", f"boundary pads 1.30 x 0.80 x 0.30 (ST p.14) = 0.312 m3 each x {n_pads} (one column at each end of the 5 drawn band runs: count 'SEE ARCH PLAN', none drawn) = {n_pads * 0.312:.3f} m3; designer item replaces the count")
    put("L-d0313e5d204e2758996a", n_pads * 1.30 * 0.80 * 0.10, "SAFETY", f"blinding under the {n_pads} boundary pads: 1.30 x 0.80 x 0.10 (projection not printed) = {n_pads * 0.104:.3f} m3; follows the pad count")

    # ---- checks
    missing = [l["line_id"] for l in blank if l["line_id"] not in rows]
    extra = [lid for lid in rows if lines[lid]["held_low"] is not None or lines[lid]["class"] != "HELD"]
    assert not missing, ("blank lines without a row", missing)
    assert not extra, ("rows on non-blank lines", extra)

    ignored = sorted((r for r in rows.values() if r["after"]["class"] == "IGNORED_SMALL"), key=lambda r: r["line_id"])
    isum = sum(r["after"]["size_m3"] for r in ignored)
    safety = 1.0 if isum < 1.0 else isum
    released = [r for r in rows.values() if r["after"]["class"] == "RELEASED"]
    by_item, by_label = {}, {}
    for r in released:
        by_item.setdefault(r["item_code"], [0, 0.0]); by_item[r["item_code"]][0] += 1; by_item[r["item_code"]][1] += r["after"]["net"]
        by_label[r["label"]] = by_label.get(r["label"], 0.0) + r["after"]["net"]
    kept = []
    for l in ranged:
        s = sweep.get(l["line_id"], {})
        kept.append({"line_id": l["line_id"], "item_code": l["item_code"], "element_id": l["element_id"], "low": l["held_low"], "high": l["held_high"],
                     "designer_item": s.get("bucket"), "fact": s.get("fact"), "list_item": s.get("list_item")})
    out = {"schema": "T761_FIX_ROWS_V1", "task": "T-761", "candidate_version": idx.get("candidate_version"), "index": INDEX,
           "defaults": {"lintel_bearing_m": LINTEL_BEARING, "beam_default_depth_m": BEAM_DEFAULT_D, "stair_plate_m": PLATE_T,
                        "roof_buildup_m": ROOF_BUILDUP, "parapet_default_h_m": PARAPET_DEFAULT_H, "materiality_m3": SMALL},
           "counts": {"blank_before": len(blank), "blank_after": 0, "released_rows": len(released), "ignored_small": len(ignored), "ranged_kept_named": len(kept)},
           "released_m3_by_item": {k: {"lines": v[0], "m3": round(v[1], 3)} for k, v in sorted(by_item.items())},
           "released_m3_by_label": {k: round(v, 3) for k, v in sorted(by_label.items())},
           "ignored_small": {"lines": len(ignored), "sum_m3": round(isum, 4), "rule": "owner 2026-11-13 14:00 (rule file: T-757)"},
           "safety_line": {"line_id": "NEW:STR.CONC.SAFETY", "item_code": "STR.CONC.SAFETY", "unit": "m3", "after": {"class": "RELEASED", "net": round(safety, 3)}, "label": "SAFETY",
                           "basis": f"ignored known pieces {isum:.4f} m3 on {len(ignored)} lines < 1 m3 -> 1 m3 (owner materiality rule); covers also unread scraps named in bases (ST-02 CA 0 .. 0.09). T-757 may merge its own IGNORED_SMALL set into this ONE line (never two safety lines)"},
           "rows": sorted(rows.values(), key=lambda r: (r["item_code"], r["line_id"])), "ranged_kept_named": kept}
    od = os.path.join(HERE, "out"); os.makedirs(od, exist_ok=True)
    json.dump(out, open(os.path.join(od, "FIX_ROWS.json"), "w"), indent=1, ensure_ascii=False)

    md = [f"# T-761 FIX ROWS on {out['candidate_version']}: blank STR.CONC lines to figures (lane S, DELIVERY MODE F-02)", "",
          f"Blank STR.CONC lines: {len(blank)} before -> 0 after ({len(released)} with a figure, {len(ignored)} IGNORED_SMALL < 0.05 m3 covered by the SAFETY line). "
          f"Added m3: {sum(by_item[k][1] for k in by_item):.2f} + SAFETY {safety:.2f}. Ranged lines kept with their designer item: {len(kept)}.", "",
          "| item | lines | m3 |", "|---|---|---|"]
    md += [f"| {k} | {v['lines']} | {v['m3']:.2f} |" for k, v in out["released_m3_by_item"].items()]
    md += ["", "By label: " + ", ".join(f"{k} {v:.2f} m3" for k, v in out["released_m3_by_label"].items()), "",
           "| line | item | before | after | label | basis |", "|---|---|---|---|---|---|"]
    for r in out["rows"]:
        a = r["after"]
        aft = f"{a['net']:.4f}" if a["class"] == "RELEASED" else f"IGNORED_SMALL {a['size_m3']:.4f}"
        md.append(f"| {r['line_id']} | {r['item_code'][9:]} | HELD blank | {aft} | {r['label']} | {r['basis']} |")
    md += ["", f"SAFETY line NEW:STR.CONC.SAFETY = {safety:.2f} m3 ({out['safety_line']['basis']})", "",
           "## Ranged lines kept (not changed by this row; designer item named, T-755 sweep)", "", "| line | item | low .. high | designer item |", "|---|---|---|---|"]
    md += [f"| {k['line_id']} | {k['item_code'][9:]} | {k['low']} .. {k['high']} | {k['designer_item']}: {k['fact']} |" for k in kept]
    open(os.path.join(od, "FIX_ROWS.md"), "w").write("\n".join(md) + "\n")
    print(json.dumps(out["counts"]), json.dumps(out["released_m3_by_item"]), json.dumps(out["ignored_small"]), "safety", safety)


if __name__ == "__main__":
    sys.exit(main())
