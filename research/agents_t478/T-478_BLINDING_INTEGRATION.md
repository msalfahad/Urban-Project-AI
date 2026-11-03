# T-478 integration package: CONC.BLINDING (T-445 pieces) into ARCH_TAKEOFF_V3.0.45

Worker 3 (lane I, stream S), 2026-11-02, branch `agents/task-T-478`. **Integration package for Checker Gate B.**
Integrates T-445 (MERGED ab6bd617, Gate A PASS with own re-measure of all 24 pits), T-322 (MERGED d3bcd9d4, pits
VERIFIED 2026-10-29 01:55, FF HELD >= 2.070), T-233 (MERGED 2ecb5bf0, outlines). Base (rebased 2026-11-02 23:50):
the candidate of record ARCH_TAKEOFF_V3.0.44 (`8b2fe2b6`, T-422, merge b4e22291). **NOT RELEASED**; released default
V2.9 + route G unchanged; rollback = V3.0.44 / V2.9. Development villa, not an accuracy claim; the method R-T478-1 is
for every villa. Drawings cited by Drive folder and title only.

integrates: T-445, T-322, T-233

## 0. Run identity and version

Drive "Alsenan chalet project": P7757.dxf (P7757_DXF_COMPRESSED.zip, `ab54dd55`) and 'ST7757 dxf.dxf' (`9f9d1179`),
decoded by the wrapper into `.work/private`. **Rebase run (2026-11-02 23:30-23:49 UTC):** own fresh
`research/agents_t167/v304_run.py`, then `research/agents_t478/v3045_run.py` through the hub (`--method
ARCH_TAKEOFF_V3.0.45`): **V3_0_43 `6f534d5e` and V3_0_44 `8b2fe2b6` reproduced** (the Checker's T-422 hashes), then
**V3_0_45_BOQ_LINES.json `5972888b`** (4,861 lines = 4,858 + 3; 3 changed, 3 added, 4,855 byte-identical to V3.0.44).
`t478_rebase_check.py`: the 6 blinding lines are byte-identical on both bases (the V3.0.43-based READY result `e1f4310a`
reproduced by the same module); V3.0.45 vs V3.0.43 = 10 FIN.SKIRTING (V3.0.44, carried byte-identical) + 6
STR.CONC.BLINDING; check_skirting re-run on V3.0.45 (4 released lines 5.802094 lm, 4 absorbed, 1 narrowed, 1 missing).

```
.work/venv/bin/python -I research/agents_t167/v304_run.py <P7757.dxf> <ST7757.dxf> --out <private>/t167
.work/venv/bin/python -I research/agents_t478/v3045_run.py <P7757.dxf> <ST7757.dxf> --out <private>/t478 --t167 <private>/t167
.work/venv/bin/python -I research/agents_t478/t478_rebase_check.py <private>/t478/v3045
.work/venv/bin/python -I research/agents_t478/t478_summary.py <private>/t478/v3045 --write
```

Version: Lead rule 2026-11-02 20:17 (T-422 and T-478 built without each other; the one READY second rebases on the
first merged candidate). T-422 merged first (V3.0.44 / registry 1.39.0), so this package is **V3.0.45 / registry
1.40.0 on V3.0.44 / 1.39.0**: EXTENDS = V3.0.44, the hub branch `if v3045:` after `if v3044:` with `--v3045-inputs`
(tools/urban_boq_m9.py; guards tested in tests/t478_blinding_integration/test_hub_wiring.py), registry OLD = 1.39.0.
Only STR.CONC.BLINDING lines move, so every quantity below is unchanged by the rebase.

## 1. The physical element (ERS s.2.1)

Blinding = plain concrete, printed t 0.10, on the formation under a member where a detail draws it: the 24 pits (p.13
typical, projection 0.10 printed), the FF lift raft (p.14, no projection printed), the F10 + F outline (follows its
footing), the ground beams (p.13 sections 10 / 30 / 10), the boundary-wall pads (p.14 A-A). Not under the ground slab
('COMPACTED SOIL', p.13); no strap section (D-15). One layer where grown plans overlap (deeper pit owns it).

## 2. Owner manual method and drawing-derived method side by side

| | Owner manual method | Drawing-derived method |
|---|---|---|
| pits | (L + 2p)(W + 2p) x t per footing, one layer | DXF outlines by handle grown 0.10 (mitred), union, overlap to the deeper pit, clipped to the plot line: 127.344375 m2 x 0.10 (Checker AGREE exactly) |
| FF raft | same, p of its own detail | p not printed: readings 0.10 / 0.15 -> 2.256 / 2.352; no projection 2.070 (AT_LEAST) |
| F10 + F | follows the footing scenario (owner 2026-11-02) | per scenario with and without the plot-line clip (own read, `t478_f10_clip.py`) |
| ground beams | strip (b + 2p) x length x t, not again over a footing | route G REACH: merged low = strips minus the pit layer; own-layer high = strips minus column footprints (`t478_gb_overlap.py`: both ends recomputed exactly) |
| boundary-wall base | pad count x (pad + p) x t | pad count not printed: HELD BLANK, >= 0.117 m3 per pad beside |

## 3. Per line: V2.9 / V3.0.43 (= V3.0.44 for these lines) / V3.0.45 (V3_0_45_INTEGRATION_LEDGER.csv, 6 rows; every other line byte-identical)

| Line | Action | V2.9 (released) | V3.0.43 | V3.0.45 | Evidence status (WFC s.5) |
|---|---|---|---|---|---|
| L-98eb2d58 pits | SPLIT_VALUE | not in released (V2.9 footings 15.659437 PROVISIONAL, other key) | PROVISIONAL 15.179437 (held whole by DG-3521554d) | **SOURCE_DERIVED 12.734438** | VERIFIED (T-322 + T-445 Gate A) |
| L-16b95607 FF raft | SPLIT_ADD | - | (inside L-98eb2d58 at 2.256) | BOUNDED 2.256 .. 2.352, at least 2.070 | HELD (S08 / S23; ESTIMATED 2.352 label only) |
| L-10032bf9 beyond plot | SPLIT_ADD | - | (inside L-98eb2d58 at 0.189) | BOUNDED 0 .. 0.189 | HELD (S06 / D-14) |
| L-080c97f5 F10 + F | RANGE_FIX | - | BOUNDED 0.552 .. 0.590 | **BOUNDED 0.435 .. 0.590** | HELD (S02 scenarios, S06 clip) |
| L-7a5214a3 ground beams | NETTING (record) | (V2.9 GB 6.495645 PROVISIONAL, other key) | BOUNDED 4.949374 .. 9.422514 | unchanged | HELD (S09 / S11) |
| L-d0313e5d boundary-wall base | ADD_HELD | - | absent (MISSING) | BLOCKED_RFI blank | HELD (pad count, M2 / S04) |
| L-35382b18 straps | none | - | BOUNDED 0 .. 0.912684 (T-356) | unchanged | HELD (S07) |

Split re-add: 12.734438 + 2.256 + 0.189 = 15.179438 vs 15.179437 (6-dp rounding of 12.7344375; TOL 1.5e-6, asserted).
F10 scenarios (own read; clipped low / clipped high / unclipped m3): F10 alone 0.435 / 0.450 / 0.480 (outline on the
plot corner: the bottom projection always beyond, the side projection when F10 sits at the corner end); F10 + F rows
0.525 / 0.560 / 0.590; drawn outline 0.5025 / 0.5025 / 0.552. Range = min clipped .. max unclipped = 0.435 .. 0.590
(R-T478-1 e; F-C-T445-1 / F-C-S06-1 carried). The V3.0.11 two-reading record is superseded by name
(`superseded_v3045`, kept whole). Ground beams (F-C-T445-2): grown strips 90.827865 m2 (+ 4.046606 free) overlap the
pit layer by 45.380730 m2 (37.636791 over outlined footings + 7.743939 over the REACH windows of the outline-less F /
F10 tag); the low end nets all of it (merged), the high end is a second layer at beam level; in PLAN the own-layer
reading has 3.763679 m3 over the footing blinding, so the plan-distinct GB range is 4.949374 .. 5.658835 m3.

Totals STR.CONC.BLINDING (only code moved, asserted): V3.0.44 (= V3.0.43) valued 15.179437 (all held by the downgrade) + held
5.501374 .. 10.925198 (3 lines) -> V3.0.45 **valued 12.734438 (VERIFIED)** + held 7.640374 .. 13.466198 (5 lines) +
1 blocked. Released V2.9: 15.659437 + 6.495645 m3, unchanged.

## 4. The -47.055 m3 roll-up item restated term by term (V3_0_45_PLATE.json; closes at both ends)

His figure = plot rectangle 31.37 x 15.00 x 0.10 (T-445 numeric identity). Terms = pieces inside the rectangle:

| Term | m3 | Cause |
|---|---|---|
| 24 pits VERIFIED, **now valued** | 12.734438 | - |
| FF raft | 2.256 .. 2.352 | S08 |
| F10 + F inside the plot | 0.435 .. 0.560 | S02, S06 clip |
| ground beams, plan-distinct of the pit layer | 4.949374 .. 5.658835 | S09 + S11 (F-C-T445-2 netted) |
| straps | 0 .. 0.912684 | S07 / D-15 (not plan-netted against the pits: listed) |
| boundary-wall base | no figure (in the remainder by name) | pad count |
| **RULE_DIFFERENCE** (one layer over the whole plot, drawn on no sheet) | **24.837043 .. 26.680188** | scope |
| beside: beyond the plot line | 0 .. 0.189 pits, <= 0.0495 F10 / F | not in his rectangle |

Engine valued vs his item: 12.734438 vs 47.055 = **-34.320562 m3 (-72.94 %)** (was 0 valued: -100 %); of it
24.84 .. 26.68 m3 (52.8 .. 56.7 % of his figure) is RULE_DIFFERENCE, the rest held by S02 / S06 / S07 / S08 / S09 / S11
/ pad count. Verdict proposals: pits ENGINE_RIGHT; plate RULE_DIFFERENCE; FF, F10 + F, GB, straps, BW UNRESOLVED.

## 5. Verification evidence, held items, downstream

- Checker evidence: T-322 verdict 2026-10-29 01:55; T-445 Verifier 2026-11-02 15:33 (own re-measure: 24 pits union
  inside the plot 127.344375 m2 AGREE exactly; F12 1.564, F9 1.044, FN 0.111 m3 AGREE).
- Downgrade DG-3521554d (LINE_CONTENT_V1 on L-98eb2d58): its content no longer exists after the split (FF is its own
  line); the Checker records it resolved; the record file is not edited (T-479).
- Earthworks (V3.0.43): zones name L-98eb2d58; the two new held lines are bound in the next earthworks round (held
  blank lines, no quantity). check_earthworks passes unchanged on V3.0.45.
- Not done / uncertain: strap blinding not plan-netted against the pit layer (its range carried); GB strips beyond
  the plot line not split (route G strips not clipped); no Checker re-measure of the GB strips (the range stays
  held); boundary-wall pad count is a designer item.

## 6. Regression

L2/L3: tests/t478_blinding_integration (28: villa C by hand + adverse + registry + development-villa pins), t445,
t350, t322, t233, t433, t203, m9_foundation, m9_kb, t140, t448, t212, t379 and the 36 candidate-module folders
t146 .. t463 pass; freeze 0; codemap stale none. Rule R-T478-1 (module docstring, every villa) and tests (normal +
adverse) written; lessons row proposed (ERS s.7): 2026-11-02 | the verified pit layer stayed unvalued under a whole-line
downgrade and the GB / pit overlap was proved by id only | split mixed lines; net strips by plan overlap, state the
overlap | tests/t478_blinding_integration | PROPOSED.

## 7. r3 (regression rework of the r2 Gate B rejection; no quantity change)

- Cause (Verifier 2026-11-03 00:35): the new module arch_v3045.py imports shapely lazily (lines 149, 165) and had no
  K1 record / by_design declaration (r8_1, t210, t257: 5 failures), and the T-459 candidate binding lacked the new step
  (1 failure).
- Fix: ALLOWED_OUTSIDE_K1 record in research/agents_t210/K1_DECISIONS.json; by_design `"arch_v3045.py": {"shapely"}`
  in tests/r8_1/test_r8_1_boundaries.py citing it; t210 / t257 pins 19 -> 20 record for record (as T-465 r2);
  research/agents_t459/T459_CANDIDATE_BINDING.json rebuilt by `t459_census.py candidate --write` (arch_v3045: no route
  G lap token; later_steps_touching stays []).
- Branch merged with the working head 983b75f4 (T-383 / T-464 / T-465); maps regenerated by the tool.
- Byte check (own Drive run, P7757.dxf ab54dd55, ST7757 9f9d1179, through v304_run + v3045_run on the merged head):
  V3.0.43 6f534d5e, V3.0.44 8b2fe2b6, V3.0.45 **5972888b unchanged**; t478_rebase_check: 6 blinding lines identical on
  both bases, the 10 V3.0.44 lines carried identical.
- L4: tests/ to the end on 2b29d74a: 17,818 passed, 618 skipped (private inputs absent), 105 xfailed, 0 failed, EXIT 0.
- F-C-T478-1 (stated, no quantity moved in r3): the F10 + F line's high end 0.590 m3 is the UNCLIPPED reading and so
  includes blinding beyond the plot line (0.030 m3 in the F10 + F scenario, 0.0495 for the drawn outline), while the
  pits carry their beyond-plot part in L-10032bf9. The inside-plot range is 0.435 .. 0.560 (already used in the s.4
  plate table) with 0 .. 0.0495 beyond. One treatment for both is the next blinding round's correction (a new
  version), proposed to the Checker; r3 keeps 0.435 .. 0.590 byte-identical to the verified r2 lines.
- Lessons row (Verifier's, adopted): 2026-11-03 | a new engine/source module importing shapely passed L3 but broke
  the K1 / T-257 / T-459 guards | integration packages with a new module run r8_1 + t210 + t257 + t459 (or L4) before
  READY | tests/t257_k1_declarations | PROPOSED.
