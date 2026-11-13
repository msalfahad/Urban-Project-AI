# T-764 fix rows on ARCH_TAKEOFF_V3.0.78: earthworks B1 + top-roof WP (DEFAULT / ESTIMATE / MEASURED)

Summary: {"rows": 21, "excavation_total_m3": 336.528464, "backfill_total_m3": 327.479909, "backfill_z1_m3": 177.289667, "z2_m3": 150.190242, "disposal_net_m3": 9.048556, "by_label": {"DEFAULT": 3, "ESTIMATE": 15, "MEASURED": 3}, "b1_lines": 20, "b1_without_figure_after": 0}

Working space beside (m3, not in any line): {"FF": 9.603, "ANNEX": 13.401828, "COURT": 2.052, "BOUNDARY": 70.63098, "note": "0.30 each side, NOT in any line: released pits / pool are neat; one decision for all B1 lines"}

| line | item | unit | before | after | label | basis |
|---|---|---|---|---|---|---|
| L-4445d5e20d1805f12402 | STR.EARTH.EXCAVATION | m3 | BLANK | 0.00 | ESTIMATE | p.13 two-beam detail exists only if GB top - footing underside > 2.50 m; under S01 2.45 m -> element absent, 0.00 by geometry (T-350 r2 / T-700); flips to REQUIRED at S01 +0.10 |
| L-b4ebff00041d90e03eca | STR.EARTH.EXCAVATION | m3 | BLANK | 34.16 | ESTIMATE | lift raft plan 4.60 x 4.50 = 20.70 m2 x 1.65 (S01: raft underside -1.50 + 5 cm screed + 10 cm plain concrete) = 34.155 m3 (T-700 S01 reading; AT_LEAST 31.05 at formation -1.50); pit floor per lift supplier |
| L-ce0132c7212e42e306a5 | STR.EARTH.EXCAVATION | m3 | HELD 7.2645 .. 8.39175 | 8.39 | ESTIMATE | F10 / F open outline (Q-31 C): the DRAWN outline 5.025 m2 x 1.67 = 8.39175 m3 (range 7.2645 .. 8.39175, S02 scenarios; the drawn outline is the one plan the drawing prints) |
| L-438a4abd3adc0475d0bd | STR.EARTH.EXCAVATION | m3 | HELD 1.069269 .. 1.176467 | 1.12 | ESTIMATE | blinding cut L 55.99 x 0.50 x 0.10 outside the pits, range 1.069269 .. 1.176467 is only the plot-line clip (S06 / D-14, 0.107 m3): midpoint |
| L-952a18b10db99c4eb1d3 | STR.EARTH.EXCAVATION | m3 | BLANK | 0.00 | MEASURED | T-695 (MERGED): 13 interior runs, blinding bottom >= +0.45 above EG +-0.00 -> no cut |
| L-b97f95d2784d456e0743 | STR.EARTH.EXCAVATION | m3 | BLANK | 0.00 | DEFAULT | 13 interior D-33 runs: cut is 0 while D <= 0.85 m (T-700 / T-242); company default beam depth 0.6 -> 0.00; a printed D > 0.85 replaces it |
| L-54baa058d6ccd9a38314 | STR.EARTH.EXCAVATION | m3 | BLANK | 5.77 | DEFAULT | annex free strip 12.819 m2 (T-700: high 21.407259 / S01 1.67) x cut 0.45 m (GB top +0.25, default depth 0.6, blinding 0.10, EG +-0.00); inside T-700 range 0.877899 .. 21.407259 |
| L-d9185fb243fd3b7130e9 | STR.EARTH.EXCAVATION | m3 | BLANK | 1.03 | DEFAULT | 3 court runs 5.70 m x b 0.30 x default D 0.6 (top on N.G., T-253 s.4: cut depth = D; T-253 range 0.627 .. 1.410 at D 0.30 / 0.40 .. 0.95) |
| L-a5844c9318406eccedde | STR.EARTH.EXCAVATION | m3 | BLANK | 13.04 | ESTIMATE | SB1 / SB2 / SB3 cut, T-695 (MERGED) range 9.950299 .. 16.121241 = D-15 strap blinding x S02 F10 / F end (two unprinted items): midpoint |
| L-313384fed48301ae02d2 | STR.EARTH.EXCAVATION | m3 | BLANK | 47.09 | ESTIMATE | boundary band (Q-28 A, owner provisional) 70.49 m net of the 21.45 m inside footings x width 0.40 (band 0.20 + 0.10 blinding projection each side, p.13 pattern) x 1.67 (same formation as the footings it runs through, S01) |
| L-2b8f1ae2ec46cd74552f | STR.EARTH.BACKFILL | m3 | BLANK | 15.07 | ESTIMATE | (raft plan 20.70 - pit ring 4.84) x raft-top depth 0.95 under S01 = 15.067 m3 (T-700; AT_LEAST 12.688) |
| L-afa1a6f9e01eb47c56e4 | STR.EARTH.BACKFILL | m3 | BLANK | 5.30 | ESTIMATE | drawn-outline scenario 5.29575 m3 (T-350 r2, same scenario as the excavation line), before the C10 / C necks (< 0.1 m3 each at 0.30 x 0.30 x 1.0) |
| L-a6af7c610a8adce59df3 | STR.EARTH.BACKFILL | m3 | HELD 119.963335 .. 128.643547 | 124.30 | ESTIMATE | 208.164757 - verified 71.925255 - re-measured 7.595955 .. 16.276167 (range 119.963335 .. 128.643547 = the D-33 / D-35 beam sections over the pits only): midpoint |
| L-91abe286a34e874e8ab2 | STR.EARTH.BACKFILL | m3 | BLANK | 0.00 | MEASURED | T-695 (MERGED): shell, p.7 layers and water space fill the neat envelope cut |
| L-6471367d85bdf361f9e7 | STR.EARTH.BACKFILL | m3 | BLANK | 0.00 | MEASURED | T-695 (MERGED): the neat cut is the blinding itself (2.79956 = 2.79956 m3) |
| L-eac006402d3035da007b | STR.EARTH.BACKFILL | m3 | BLANK | 150.19 | ESTIMATE | placed fill EG -> slab underside per plan column, T-700 (MERGED) 136.900995 .. 163.479489 (GS-08 lobby level, GS-12 / GS-16 floored or open, D-33 / D-34 / D-35 sections): midpoint; owner plan x depth 216.41 x 0.85 = 183.95 beside |
| L-89b8e6beaea55fc0e4c9 | STR.EARTH.BACKFILL | m3 | BLANK | 32.62 | ESTIMATE | annex 1.795 (cut 0.50 x 0.45 less blinding 0.50 x 0.10 and GB 0.30 x 0.35: the two 0.10 side strips) + court 0 (cut = beam) + straps 8.695 (T-695 6.437519 .. 10.952471, midpoint) + boundary 22.134 (70.49 m x two 0.10 strips x 1.57 above the blinding) + D-33 0 |
| L-78d7c8a989ab34527a1c | STR.EARTH.DISPOSAL | m3 | BLANK | 9.05 | ESTIMATE | excavation 336.53 (12 lines incl. released pits 208.16 / pool 17.78) - backfill 327.48 (Z1 177.29 + Z2 150.19, fill 'from excavation material', p.13) = 9.05 m3 in situ, no bulking (no measured factor; R-T505-1 dry-mass balance stays the method of record when densities exist) |
| L-636fd3ff1784a12e653b | FIN.WP.ROOF | m2 | HELD 115.656474 .. 115.813974 | 115.81 | ESTIMATE | +9.70 roof membrane 115.656474 (= ROOF-970 finish, released) + drawn band D-BAND 0.1575 m2 = 115.813974 |
| L-aac1f35e08f85b643692 | FIN.WP.ROOF_UPTURN | lm | BLANK | 29.80 | ESTIMATE | top roof +13.90 edge = 2F facade run 29.8 lm (MAIN_FILL_3, plan dimension governs a facade); upturn along it |
| L-90b40877c8c3da54ba1b | FIN.WP.MEMBRANE_ROLLS | pcs | BLANK | 7.00 | ESTIMATE | top roof 46.59 m2 (MAIN_FILL) x 8 rolls / 55.559 m2 of roof 1F-AT220 (released, same edge / area ratio 0.64 lm/m2 as the top roof 29.8 / 46.59) = 6.71 -> 7 rolls |
