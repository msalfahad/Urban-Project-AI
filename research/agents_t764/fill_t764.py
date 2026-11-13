"""T-764 (DELIVERY MODE fix-row set): B1 earthworks blanks / ranges and the top-roof (+13.90) WP blanks of
ARCH_TAKEOFF_V3.0.78 get a figure with a label (fallback order: merged geometry -> company default -> ratio).

Reads committed, Checker-merged files only (no drawings, no client data):
  research/agents_t738/out/LINE_INDEX_V3_0_78.json   candidate of record (line ids, before-state)
  research/agents_t700/WIRING_T700.csv               T-700 (MERGED 8210b549): zone bounds incl. T-695 (MERGED)
  research/agents_t700/ZONES_T700.json               T-700 lift pit S01 reading, annex free strip
  research/agents_t350r2/FILL_T350R2.csv             T-350 r2 (MERGED 42a99508): F10F backfill scenarios
Owner rules used: S01 founding level (owner-accepted RFI re-review 2026-11-02: formation -1.67 for footings),
Q-28 A (owner 2026-10-19, provisional: boundary band B.W 0.20 x 0.60 over 70.49 m net of footings), company
default beam depth 0.60 (owner 2026-11-13), disposal = excavation - backfill (DELIVERY_MODE s.3 step 4).
Working space is NOT added (the released pits / pool lines are neat; adding it only to these lines would mix
two measurement bases in one item): the 0.30 m allowance is reported beside, one figure per zone.

    python3 -I research/agents_t764/fill_t764.py [--write]
"""
from __future__ import annotations
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
IDX = os.path.join(ROOT, "research/agents_t738/out/LINE_INDEX_V3_0_78.json")
W700 = os.path.join(ROOT, "research/agents_t700/WIRING_T700.csv")
Z700 = os.path.join(ROOT, "research/agents_t700/ZONES_T700.json")
F350 = os.path.join(ROOT, "research/agents_t350r2/FILL_T350R2.csv")

S01_DEPTH = 1.67          # EG +-0.00 -> footing formation (1.50 + 0.07 underlay + 0.10 blinding), owner-accepted S01
GB_DEPTH_DEFAULT = 0.60   # company default beam depth (owner 2026-11-13)
BLINDING = 0.10
WS = 0.30                 # working space, reported beside only


def r6(x):
    return round(x, 6)


def main(write=False):
    idx = json.load(open(IDX))
    byid = {l["line_id"]: l for l in idx["lines"]}
    w = {r["line_id"]: r for r in csv.DictReader(open(W700))}
    z = json.load(open(Z700))
    f350 = {r["row_id"]: r for r in csv.DictReader(open(F350))}

    def rng(lid):
        r = w[lid]; return float(r["low_m3"]), float(r["high_m3"])

    rows, beside = [], {}

    def row(lid, code, unit, after, label, method, basis):
        l = byid[lid]
        assert l["item_code"] == code and l["unit"] == unit and l["class"] == "HELD", (lid, l["item_code"], l["class"])
        rows.append({"line_id": lid, "item_code": code, "unit": unit, "element_id": l["element_id"],
                     "before": {"class": l["class"], "net": l["measured_net"], "low": l["held_low"], "high": l["held_high"]},
                     "after": {"class": "RELEASED", "net": r6(after)}, "label": label, "method": method, "basis": basis})
        return after

    EX, BF = "STR.EARTH.EXCAVATION", "STR.EARTH.BACKFILL"
    ex, bf = {}, {}
    # ---- excavation (B1-02) -------------------------------------------------------------------------------
    ex["LOWER"] = row("L-4445d5e20d1805f12402", EX, "m3", 0.0, "ESTIMATE", "GEOMETRY_UNDER_S01",
                      "p.13 two-beam detail exists only if GB top - footing underside > 2.50 m; under S01 2.45 m -> "
                      "element absent, 0.00 by geometry (T-350 r2 / T-700); flips to REQUIRED at S01 +0.10")
    lp = z["lift_pit"]["S01_beside"]
    assert abs(z["lift_pit"]["plan_own_m2"] - 20.70) < 1e-9 and abs(lp["formation_depth_min_m"] - 1.65) < 1e-9
    ex["FF"] = row("L-b4ebff00041d90e03eca", EX, "m3", 20.70 * 1.65, "ESTIMATE", "MERGED_S01_READING",
                   "lift raft plan 4.60 x 4.50 = 20.70 m2 x 1.65 (S01: raft underside -1.50 + 5 cm screed + 10 cm plain "
                   f"concrete) = {lp['excavation_m3']} m3 (T-700 S01 reading; AT_LEAST 31.05 at formation -1.50); pit "
                   "floor per lift supplier")
    lo, hi = byid["L-ce0132c7212e42e306a5"]["held_low"], byid["L-ce0132c7212e42e306a5"]["held_high"]
    ex["F10F"] = row("L-ce0132c7212e42e306a5", EX, "m3", hi, "ESTIMATE", "DRAWN_OUTLINE",
                     f"F10 / F open outline (Q-31 C): the DRAWN outline 5.025 m2 x 1.67 = {hi} m3 (range {lo} .. {hi}, "
                     "S02 scenarios; the drawn outline is the one plan the drawing prints)")
    l = byid["L-438a4abd3adc0475d0bd"]
    ex["EXT_GB"] = row(l["line_id"], EX, "m3", (l["held_low"] + l["held_high"]) / 2, "ESTIMATE", "RANGE_MIDPOINT",
                       f"blinding cut L 55.99 x 0.50 x 0.10 outside the pits, range {l['held_low']} .. {l['held_high']} is "
                       "only the plot-line clip (S06 / D-14, 0.107 m3): midpoint")
    assert w["L-952a18b10db99c4eb1d3"]["state"] == "PROPOSED_ZERO_BY_GEOMETRY"
    ex["ZERO"] = row("L-952a18b10db99c4eb1d3", EX, "m3", 0.0, "MEASURED", "ZERO_BY_GEOMETRY",
                     "T-695 (MERGED): 13 interior runs, blinding bottom >= +0.45 above EG +-0.00 -> no cut")
    ex["D33"] = row("L-b97f95d2784d456e0743", EX, "m3", 0.0, "DEFAULT", "ZERO_UNDER_DEFAULT_DEPTH",
                    "13 interior D-33 runs: cut is 0 while D <= 0.85 m (T-700 / T-242); company default beam depth "
                    f"{GB_DEPTH_DEFAULT} -> 0.00; a printed D > 0.85 replaces it")
    hi_annex = rng("L-54baa058d6ccd9a38314")[1]
    strip = hi_annex / S01_DEPTH
    annex_depth = (GB_DEPTH_DEFAULT - 0.25) + BLINDING  # top +0.25, default D 0.60, blinding 0.10 below EG
    ex["ANNEX"] = row("L-54baa058d6ccd9a38314", EX, "m3", strip * annex_depth, "DEFAULT", "STRIP_X_DEFAULT_DEPTH",
                      f"annex free strip {strip:.3f} m2 (T-700: high {hi_annex} / S01 1.67) x cut {annex_depth:.2f} m (GB top "
                      f"+0.25, default depth {GB_DEPTH_DEFAULT}, blinding 0.10, EG +-0.00); inside T-700 range "
                      f"{rng('L-54baa058d6ccd9a38314')[0]} .. {hi_annex}")
    ex["COURT"] = row("L-d9185fb243fd3b7130e9", EX, "m3", 5.70 * 0.30 * GB_DEPTH_DEFAULT, "DEFAULT", "LxBxD",
                      f"3 court runs 5.70 m x b 0.30 x default D {GB_DEPTH_DEFAULT} (top on N.G., T-253 s.4: cut depth = D; "
                      "T-253 range 0.627 .. 1.410 at D 0.30 / 0.40 .. 0.95)")
    lo_s, hi_s = rng("L-a5844c9318406eccedde")
    ex["STRAPS"] = row("L-a5844c9318406eccedde", EX, "m3", (lo_s + hi_s) / 2, "ESTIMATE", "RANGE_MIDPOINT",
                       f"SB1 / SB2 / SB3 cut, T-695 (MERGED) range {lo_s} .. {hi_s} = D-15 strap blinding x S02 F10 / F "
                       "end (two unprinted items): midpoint")
    L_bnd = 91.94 - 21.45
    ex["BOUNDARY"] = row("L-313384fed48301ae02d2", EX, "m3", L_bnd * 0.40 * S01_DEPTH, "ESTIMATE", "LxBxD",
                         f"boundary band (Q-28 A, owner provisional) {L_bnd:.2f} m net of the 21.45 m inside footings x "
                         f"width 0.40 (band 0.20 + 0.10 blinding projection each side, p.13 pattern) x {S01_DEPTH} (same "
                         "formation as the footings it runs through, S01)")
    # ---- backfill (B1-03) ---------------------------------------------------------------------------------
    bf["FF"] = row("L-2b8f1ae2ec46cd74552f", BF, "m3", (20.70 - 4.84) * 0.95, "ESTIMATE", "MERGED_S01_READING",
                   f"(raft plan 20.70 - pit ring 4.84) x raft-top depth 0.95 under S01 = {lp['backfill_m3']} m3 (T-700; "
                   "AT_LEAST 12.688)")
    sc = f350["B1-03 BACKFILL|GAP Z1-PIT-F10F [drawn outline]"]
    bf["F10F"] = row("L-afa1a6f9e01eb47c56e4", BF, "m3", float(sc["lo_m3"]), "ESTIMATE", "DRAWN_OUTLINE",
                     f"drawn-outline scenario {sc['lo_m3']} m3 (T-350 r2, same scenario as the excavation line), before "
                     "the C10 / C necks (< 0.1 m3 each at 0.30 x 0.30 x 1.0)")
    l = byid["L-a6af7c610a8adce59df3"]
    bf["PITS"] = row(l["line_id"], BF, "m3", (l["held_low"] + l["held_high"]) / 2, "ESTIMATE", "RANGE_MIDPOINT",
                     f"208.164757 - verified 71.925255 - re-measured 7.595955 .. 16.276167 (range {l['held_low']} .. "
                     f"{l['held_high']} = the D-33 / D-35 beam sections over the pits only): midpoint")
    assert w["L-91abe286a34e874e8ab2"]["state"] == w["L-6471367d85bdf361f9e7"]["state"] == "PROPOSED_ZERO_BY_GEOMETRY"
    bf["POOL"] = row("L-91abe286a34e874e8ab2", BF, "m3", 0.0, "MEASURED", "ZERO_BY_GEOMETRY",
                     "T-695 (MERGED): shell, p.7 layers and water space fill the neat envelope cut")
    bf["EXT_GB"] = row("L-6471367d85bdf361f9e7", BF, "m3", 0.0, "MEASURED", "ZERO_BY_GEOMETRY",
                       "T-695 (MERGED): the neat cut is the blinding itself (2.79956 = 2.79956 m3)")
    lo_z, hi_z = rng("L-eac006402d3035da007b")
    bf["Z2"] = row("L-eac006402d3035da007b", BF, "m3", (lo_z + hi_z) / 2, "ESTIMATE", "RANGE_MIDPOINT",
                   f"placed fill EG -> slab underside per plan column, T-700 (MERGED) {lo_z} .. {hi_z} (GS-08 lobby level, "
                   "GS-12 / GS-16 floored or open, D-33 / D-34 / D-35 sections): midpoint; owner plan x depth 216.41 x "
                   "0.85 = 183.95 beside")
    a_bf = ex["ANNEX"] * (2 * 0.10 * (GB_DEPTH_DEFAULT - 0.25)) / (0.50 * annex_depth)
    lo_sb, hi_sb = rng("NEW (split of L-89b8e6beaea55fc0e4c9)")
    s_bf = (lo_sb + hi_sb) / 2
    b_bf = L_bnd * 2 * 0.10 * (S01_DEPTH - BLINDING)
    other = a_bf + 0.0 + s_bf + b_bf + 0.0
    bf["OTHER"] = row("L-89b8e6beaea55fc0e4c9", BF, "m3", other, "ESTIMATE", "SUM_OF_ZONES",
                      f"annex {a_bf:.3f} (cut 0.50 x {annex_depth:.2f} less blinding 0.50 x 0.10 and GB 0.30 x 0.35: the two "
                      f"0.10 side strips) + court 0 (cut = beam) + straps {s_bf:.3f} (T-695 {lo_sb} .. {hi_sb}, midpoint) + "
                      f"boundary {b_bf:.3f} ({L_bnd:.2f} m x two 0.10 strips x 1.57 above the blinding) + D-33 0")
    # ---- disposal (B1-04) ---------------------------------------------------------------------------------
    exc_all = sum(ex.values()) + byid["L-cf8ffcdaacd0159b7e29"]["measured_net"] + byid["L-0a49a302b7926f86a37f"]["measured_net"]
    bf_all = sum(bf.values())
    net = exc_all - bf_all
    row("L-78d7c8a989ab34527a1c", "STR.EARTH.DISPOSAL", "m3", max(net, 0.0), "ESTIMATE", "EXCAVATION_MINUS_BACKFILL",
        f"excavation {exc_all:.2f} (12 lines incl. released pits 208.16 / pool 17.78) - backfill {bf_all:.2f} (Z1 "
        f"{bf_all - bf['Z2']:.2f} + Z2 {bf['Z2']:.2f}, fill 'from excavation material', p.13) = {net:.2f} m3 in situ, no "
        "bulking (no measured factor; R-T505-1 dry-mass balance stays the method of record when densities exist)"
        + ("" if net >= 0 else f"; negative = {-net:.2f} m3 to import, disposal 0"))
    # ---- top roof +13.90 WP (row names FIN.WP.ROOF; T-750 wires the rest of WP) ----------------------------
    l = byid["L-636fd3ff1784a12e653b"]
    row(l["line_id"], "FIN.WP.ROOF", "m2", l["held_high"], "ESTIMATE", "DRAWN_BAND_INCLUDED",
        f"+9.70 roof membrane {l['held_low']} (= ROOF-970 finish, released) + drawn band D-BAND 0.1575 m2 = {l['held_high']}")
    row("L-aac1f35e08f85b643692", "FIN.WP.ROOF_UPTURN", "lm", 29.8, "ESTIMATE", "FACADE_RUN",
        "top roof +13.90 edge = 2F facade run 29.8 lm (MAIN_FILL_3, plan dimension governs a facade); upturn along it")
    row("L-90b40877c8c3da54ba1b", "FIN.WP.MEMBRANE_ROLLS", "pcs", 7.0, "ESTIMATE", "RATIO_SAME_SHAPE_ROOF",
        "top roof 46.59 m2 (MAIN_FILL) x 8 rolls / 55.559 m2 of roof 1F-AT220 (released, same edge / area ratio 0.64 "
        "lm/m2 as the top roof 29.8 / 46.59) = 6.71 -> 7 rolls")

    ws = {"FF": (5.20 * 5.10 - 20.70) * 1.65, "ANNEX": 0.60 * 49.6364 * annex_depth,
          "COURT": 0.60 * 5.70 * GB_DEPTH_DEFAULT, "BOUNDARY": 0.60 * L_bnd * S01_DEPTH}
    out = {"schema": "DELIVERY_FIX_ROWS_V1", "task": "T-764", "candidate_version": idx["candidate_version"],
           "inputs": {"index": "LINE_INDEX_V3_0_78.json", "t700": "WIRING_T700.csv + ZONES_T700.json",
                      "t350r2": "FILL_T350R2.csv"},
           "supersedes_main_fill": {"L-78d7c8a989ab34527a1c": "MAIN_FILL_1 EARTH_DISPOSAL HELD 105.632 .. 115.546 (ignored Z2 "
                                    "and 14 blank zones)"},
           "working_space_beside_m3": {k: r6(v) for k, v in ws.items()} | {"note": "0.30 each side, NOT in any line: "
                                       "released pits / pool are neat; one decision for all B1 lines"},
           "summary": {"rows": len(rows), "excavation_total_m3": r6(exc_all), "backfill_total_m3": r6(bf_all),
                       "backfill_z1_m3": r6(bf_all - bf["Z2"]), "z2_m3": r6(bf["Z2"]), "disposal_net_m3": r6(net),
                       "by_label": {k: sum(1 for r in rows if r["label"] == k) for k in sorted({r["label"] for r in rows})}},
           "rows": rows}
    # self-check: every B1 line of the candidate has a figure after this set (or was released before)
    b1 = [l for l in idx["lines"] if l["item_code"].startswith("STR.EARTH") and l["class"] != "EXCLUDED"]
    done = {r["line_id"] for r in rows}
    left = [l["line_id"] for l in b1 if l["class"] != "RELEASED" and l["line_id"] not in done]
    assert not left, left
    out["summary"]["b1_lines"] = len(b1); out["summary"]["b1_without_figure_after"] = 0
    print(json.dumps(out["summary"], indent=1)); print(json.dumps(out["working_space_beside_m3"]))
    if write:
        d = os.path.join(HERE, "out"); os.makedirs(d, exist_ok=True)
        json.dump(out, open(os.path.join(d, "FIX_ROWS.json"), "w"), indent=1)
        md = [f"# T-764 fix rows on {out['candidate_version']}: earthworks B1 + top-roof WP (DEFAULT / ESTIMATE / MEASURED)", "",
              f"Summary: {json.dumps(out['summary'])}", "",
              f"Working space beside (m3, not in any line): {json.dumps(out['working_space_beside_m3'])}", "",
              "| line | item | unit | before | after | label | basis |", "|---|---|---|---|---|---|---|"]
        for r in rows:
            b = r["before"]
            bs = "BLANK" if b["low"] is None else f"HELD {b['low']} .. {b['high']}"
            md.append(f"| {r['line_id']} | {r['item_code']} | {r['unit']} | {bs} | {r['after']['net']:.2f} | {r['label']} | {r['basis']} |")
        open(os.path.join(d, "FIX_ROWS.md"), "w").write("\n".join(md) + "\n")


if __name__ == "__main__":
    main("--write" in sys.argv)
