# T-672: MASONRY GATE B ROUND 1 integration package, ARCH_TAKEOFF_V3.0.68 (lane I)

Worker 3, 2026-11-11. INTEGRATION PACKAGE for Checker Gate B. Base: the candidate of record V3.0.67 (T-682, Gate B PASS,
merge 4bbe407b, run of record a29a11a9); released default V2.9 + route G untouched; nothing released. No drawing,
workbook, client name or coordinate here; Drive files named by folder and title only.

## 1. What is wired (every piece Checker-merged)

| source | merge | Checker | wired as |
|---|---|---|---|
| T-670 R-T670-1 (B9 material lines restated on rulebook 1.1.0, Q-80) | 91a74d45 | Verifier 2026-11-10T09:00Z GATE A PASS (own DXF GF-W19 / GF-W29) | MAT_RESTATE |
| T-675 R-T675-1 (MAIN_S / ANNEX_S black by ST p.1 note 2) | e0984b13 | Verifier 2026-11-10T14:08Z GATE A PASS (note 2 own read) | MAT_NOT_APPLICABLE |
| T-372 R-T372-1 perimeter + T-675 R-T675-3 bands / pieces | dc1ac41e / e0984b13 | Verifier 11:04Z (own 1F-W18 AGREE) / 14:08Z | PERIMETER_JOINT |
| T-372 R-T372-1 (5) bed + T-675 R-T675-2 (6 dp at a masonry-end stopper) | dc1ac41e / e0984b13 | as above (own D-1F-04 bed AGREE) | LINTEL_BED |

Bed / head panel mortar already wired by T-498 / T-506 (V3.0.59) is the line the restatement re-produces; its producer is
unchanged (read-only use of `arch_v3059.materials_for`).

## 2. Method (R-T672-1, every villa; module `engine/source/arch_v3068.py`)

- (a) MAT_RESTATE: the merged V3.0.59 producer is re-run on the V3.0.67 MAS.BLOCK hosts and STR.CONC.LINTEL lines,
  first on COMPANY_RULEBOOK 1.0.0: it must reproduce every one of the 74 current material lines BYTE-IDENTICALLY (else
  refused); then on 1.1.0 (UPC-BLACK-BLOCK-001 0.15 m = 40 x 20, owner Q-80 2026-11-07). A line whose figure changes is
  replaced in place (same producer, same line id); a line with the same figure stays byte-identical. Every figure is
  asserted equal to the merged T-670 row.
- (b) MAT_NOT_APPLICABLE: the 4 AAC glue / AAC unit lines on the colour-less hosts HOUSE_BELOW_NG:MAIN_S / ANNEX_S ->
  NOT_APPLICABLE_WITH_EVIDENCE with the note-2 evidence and the architectural check in the line; only a HELD blank line
  on a host whose id carries no colour can be retired; the black pair stays HELD (host height, leaf not printed).
- (c) PERIMETER_JOINT: one new MAS.MORTAR.BLACK.PERIMETER line per black laying-mortar line (20), bound by id, never
  summed into it (its own producer key, R-T520-1 increment over the panel). Valued panel: envelope [T-372 low, T-372
  high + held bands high + held piece soffits high] (asserted = the T-675 envelope; band sum per line asserted);
  PROVISIONAL when low = high, else HELD BOUNDED. HELD panel: HELD blank with the host's own cause and question.
- (d) LINTEL_BED: one new MAS.MORTAR.BLACK.LINTEL_BEARING line per lintel face the material base names on a BLACK host (9;
  white AAC hosts carry thin-bed glue, no bed joint line); m3 = bearing x kappa x t x 0.010, kappa = unit face / module
  face = 0.92625 (f = 0.001389375 m3/m at 0.15 m), recomputed in the module and asserted equal to the ledger;
  EXACT -> PROVISIONAL, deficit end -> BOUNDED (0.40 .. drawn available, 6 dp), lintel itself HELD (D-1F-09) -> BOUNDED
  0 .. 2 x 0.40 printed bearing.
- (e) Correlated lintel scenarios (F-C-T372-4) BESIDE in the run identity, never mixed into a line: A = printed 0.40 m
  bearing with the deficit-end bands present; B = bearing to the drawn available length, no end band.
- (f) Only the six masonry material codes move (asserted); every other line byte-identical (asserted); the V3.0.67
  concrete / lintel checks re-run on the result. Statuses: ASSUMED - OWNER-APPROVED (Q-75 / Q-80 module, Q-78 mix, owner
  2026-10-29 10 mm joint) on every valued / bounded line, DRAWING-CONFIRMED on the 4 not-applicable lines, never VERIFIED;
  installed only, waste / procurement HELD.

Owner manual method vs drawing-derived method, side by side: units = net wall m2 x 12.5; mortar = net m2 x t x (1 -
0.39 x 0.19 / 0.40 x 0.20) (both methods agree on the rate; the drawing method deducts the REQUIRED lintel faces bound
to their concrete lines). Perimeter and bed are not in the owner's manual method (m2-based mortar only): RULE_DIFFERENCE,
carried as their own lines so a reviewer can price or drop them by line.

## 3. Checker acceptance items

- F-C-T372-1 (bed high from a 3 dp field): the bed uses the T-675 6 dp bearings (D-1F-03 0.638520, D-1F-04 0.479800,
  D-1F-07 / -10 0.659300, D-GF-10 0.653000), recomputed in the module; full-precision 8-lintel high 0.007628 m3, sum of
  the 6 dp line figures 0.007626 m3 (rounding per line, stated).
- F-C-T372-2 (dome-panel 'SEE DETAIL' high only): the 6 dome-opening piece soffits are 0 .. high inside the envelope
  (no low invented).
- F-C-T372-3 (COMPUTED is not a s.5 status): every perimeter / bed line carries ASSUMED - OWNER-APPROVED (the 0.20 m
  lines with the T-675 part (c) basis, F-T372-1).
- F-C-T372-4 (correlated scenarios): (e) above.
- F-T670-1 / F-T675-2 (producer opens 4 codes on a colour-less host): R-T675-1 applied before the perimeter step; the
  frozen V3.0.59 producer is not edited (a producer rule change would be a new version).
- T-682 downstream note (lintel existence status): every V3.0.67 lintel restated by T-682 sits on a HELD host (faces
  listed on held hosts in the merged T-498 inputs) except W13, whose face is a HELD range 0 .. 0.40 m2 on the white
  1F 0.20 DRAWING_CONFIRMED host (glue 203.562 .. 210.762 kg): a valid bound of the now-existing lintel, unchanged here;
  it narrows to the deducted end once the W13 lintel line is valued.

## 4. Run of record and line-by-line diff

Drive 'Alsenan chalet project' copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) and 'ST7757 dxf.dxf'
(9f9d1179), decoded into the private folder only: own fresh t167 `v304_run.py` (27 min) -> `research/agents_t672/v3068_run.py`
(exit 0): every earlier version re-run and asserted, **V3_0_67 a29a11a9 (asserted = T-682 run of record)** ->
**V3_0_68 d1de50cb**, 5,105 lines; replaced 16 (12 restated + 4 not applicable), added 29 (20 perimeter + 9 bed),
outside 5,060 byte-identical (asserted). Diff vs V3.0.67: CHANGED 16, ADDED 29, SAME 5,060. vs released V2.9 + route G:
QUANTITY_DIFFERS 1,049 and SAME_QUANTITY 543 unchanged, NOT_IN_RELEASED 3,484 -> 3,513 (+29 new lines): no released
line moved. The 1.0.0 reproduction: 74 / 74 material lines byte-identical. Census `t479_registry_census.py` (unchanged;
verdicts V3.0.44 b3b08dd7, downgrades 81732639) on V3_0_67 reproduces `research/agents_t682/out/LINE_INDEX_V3_0_67.json`
byte for byte; on V3_0_68 -> `out/LINE_INDEX_V3_0_68.json` (fc485958), issues {}, complete map, 0 stale blocks (registry
1.69.0 pending). `t672_package_families.py` (T-483 attribute unchanged, chain 67 -> 68): B9-01 UNITS.BLACK 6 changed /
UNITS.WHITE 2; B9-04 MORTAR.BLACK 6 / GLUE.AAC 2 changed, PERIMETER +20, LINTEL_BED +9. Summary `summary_t672.json`.

Code census, V3.0.67 -> V3.0.68 (units never summed across codes):

| code | V3.0.67 | V3.0.68 |
|---|---|---|
| MAS.UNITS.BLACK pcs | 1,075.80 (2) + 18 blank | 2,571.27625 (7) + 698.66125 .. 702.91125 (1) + 12 blank |
| MAS.MORTAR.BLACK m3 | 1.269444 (2) + 18 blank | 2.59294 (7) + 0.618315 .. 0.622076 (1) + 12 blank |
| MAS.GLUE.AAC kg | 43.596 (2) + 842.06025 .. 861.32025 (3) + 12 blank, 17 lines | same figures, 10 blank + 2 N/A (15 in totals) |
| MAS.UNITS.WHITE pcs | 17 blank | 15 blank + 2 N/A |
| MAS.MORTAR.BLACK.PERIMETER m3 | none | 0.104549 (4) + 0.072178 .. 0.108325 (4) + 12 blank = 0.176727 .. 0.212874 |
| MAS.MORTAR.BLACK.LINTEL_BEARING m3 | none | 0.003333 (3) + 0.00278 .. 0.005404 (6) = 0.006113 .. 0.008737 (D-1F-09 0 .. 0.001111 inside) |

Changed / added lines (hand check of each figure: net x 12.5; net x 0.0110625; perimeter envelope; bearing x f):

| line | code | host / opening | before | after | by hand |
|---|---|---|---|---|---|
| L-26c299b8 / L-794c7232 | UNITS / MORTAR | GF 0.15 VERIFIED 9.895 m2 | blank | 123.6875 pcs / 0.109463 m3 | 9.895 x 12.5; x 0.0110625 |
| L-fa0fae23 / L-33fcd56e | UNITS / MORTAR | GF 0.15 DRAWING_CONFIRMED 8.595 | blank | 107.4375 / 0.095082 | 8.595 x 12.5 (Checker GF-W19 AGREE) |
| L-1aa13ac0 / L-8f163174 | UNITS / MORTAR | GF 0.15 OWNER_APPROVED 24.2374 - 0.68 lintel faces | blank | 294.4675 / 0.260604 | 23.5574 x 12.5 (Checker GF-W29 AGREE) |
| L-06e9c608 / L-2051ab0a | UNITS / MORTAR | 1F 0.15 VERIFIED 52.318 | blank | 653.975 / 0.578768 | 52.318 x 12.5 |
| L-616b748b / L-a8f0d0e9 | UNITS / MORTAR | 1F 0.15 DRAWING_CONFIRMED 25.2727 | blank | 315.90875 / 0.279579 | 25.2727 x 12.5 |
| L-1e61a4aa / L-866a6602 | UNITS / MORTAR | 1F 0.15 OWNER_APPROVED 58.2529 - 2.02 (- 0 .. 0.34 D-1F-09) | blank | 698.66125 .. 702.91125 / 0.618315 .. 0.622076 | 55.8929 .. 56.2329 x 12.5 |
| L-a951fbf0 / L-09c52c7b | GLUE / WHITE | MAIN_S | blank | N/A with evidence | ST p.1 note 2 |
| L-6b0bb35b / L-2ae0aac4 | GLUE / WHITE | ANNEX_S | blank | N/A with evidence | ST p.1 note 2 |
| 4 PERIMETER VALUE | | GF 0.20 V / 1F 0.20 V / GF 0.15 DC / GF 0.15 V | new | 0.058854 / 0.039291 / 0.003237 / 0.003167 | T-372 low = high |
| 4 PERIMETER BOUND | | 1F 0.15 OA / 1F 0.15 DC / 1F 0.15 V / GF 0.15 OA | new | 0.028344 .. 0.049793 / 0.014744 .. 0.027441 / 0.018729 .. 0.019896 / 0.010361 .. 0.011195 | T-372 high + bands + pieces (0.032121 + 0.012199 + 0.005473; 0.02083 + 0.005141 + 0.00147; -; 0.010639 + 0.000556) |
| 12 PERIMETER HELD | | the 12 HELD hosts | new | blank, host cause | never 0 |
| 3 BED EXACT | | D-1F-02 / D-1F-08 / D-GF-13 | new | 0.001111 each | 0.80 x 0.001389375 |
| 5 BED RANGE | | D-1F-03 / -04 / -07 / -10, D-GF-10 | new | 0.000556 .. 0.000887 / .. 0.000667 / .. 0.000916 / .. 0.000916 / .. 0.000907 | 0.40 .. 0.638520 / 0.479800 / 0.659300 / 0.659300 / 0.653000 m x f |
| 1 BED HELD | | D-1F-09 (lintel HELD) | new | 0 .. 0.001111 | 2 x 0.40 printed bearing |

Correlated scenarios beside (F-C-T372-4): A (printed 0.40 m bearing at the 5 deficit lintels, their 10 end bands present)
0.00556 m3; B (bearing to the drawn available length, no end band) 0.004293 m3 (deficit-lintel bed + bands only).
Panel + perimeter + bed on the 8 valued mortar lines: 3.211255 .. 3.215016 + 0.176727 .. 0.212874 + 0.006113 .. 0.007626
= 3.394095 .. 3.435516 m3 installed (PROVISIONAL), against T-367's contract-basis 3.870113 m3 (V3.0.26, reconciled by
T-520: kappa, module credit, c = 1 walls).

## 5. Held / missing, named

- 12 MAS.UNITS.BLACK / 12 MAS.MORTAR.BLACK / 12 PERIMETER lines HELD blank on 12 HELD hosts (2F roof datum D-39,
  BLOCK_WALL_NOT_ESTABLISHED, MAIN_S / ANNEX_S below N.G.); MAS.GLUE.AAC 10 blank on held hosts; MAS.UNITS.WHITE 15
  blank (no AAC face selected, Q-60 faces beside only).
- GF-W22 perimeter 0.004140 .. 0.004144 m3 beside its host (parent area CONFLICT D-27), recorded on the GF 0.15
  DRAWING_CONFIRMED perimeter line, not in it.
- MAIN_S beside CONDITIONAL AT_LEAST 142.3625 pcs / 0.125991 m3 (one 0.15 leaf) stays in the T-675 ledger, not on the
  line (host height has no upper bound, leaf not printed).
- Waste / procurement, bag rounding: HELD (no owner rule; bags only at the purchasing group).

## 6. Freelancer, verdicts, lesson

Freelancer: blockwork in m2 only, no unit / mortar / glue / perimeter / bed rows (T-176 / T-367): RULE_DIFFERENCE, no %.
Verdict proposals: restated units / mortar ENGINE_RIGHT on the method (T-670 hand checks, Checker hosts GF-W19 / GF-W29);
perimeter and bed ENGINE_RIGHT as bounded components, UNRESOLVED as points (junction detail, deficit bearings: designer).
Lesson row (ERS s.7, proposed): "a rule-version change reaches the candidate only by re-running the merged producer on
the candidate's current lines after the old version reproduces every current line byte-identically; a component
measured wall by wall gets its own code bound by id to the line it adds to (every villa; T-672)".

## 7. Validation

- L1 / L2: `tests/t672_masonry_gate_b1` (hand villa K672, not the development villa: a 0.20 m black host with two
  REQUIRED lintels (EXACT and deficit bed), a 0.15 m black host with a HELD lintel face (restated 96 .. 100 pcs /
  0.08496 .. 0.0885 m3, bed HELD 0 .. 0.80 f), a white host left alone, a colour-less below-ground host retired to
  NOT_APPLICABLE; mirror order; adverse: a candidate line the old rulebook does not reproduce, a T-670 figure that
  differs, a typed rate, N/A on a coloured host, a valued perimeter on a blank panel (never 0), a missing perimeter
  entry, an envelope that is not the ledger's, a measured bed under a HELD lintel, a bed figure not recomputed, applied
  twice, a millimetre face), the inputs builder on the committed ledgers (counts, hand figures, totals 0.176727 ..
  0.188035 and + 0.017896 + 0.006943, bearings 4.40 .. 5.48992 m, tampered pin refused), master 1.69.0 (pending).
- L4 full suite on a8f7cfcd (34 min): 22,779 passed, 685 skipped (377 private-input phases), 105 xfail, 3 FAILED, all
  three this package's own: maps not rebuilt yet; `t457` reads every '*BED*' item code in the candidate closure as a
  wall fixing bed (the bed code is renamed MAS.MORTAR.BLACK.LINTEL_BEARING: a lintel bearing bed joint, not a tile bed);
  `t459` candidate binding not rebuilt for the new module (rebuilt by its tool, one new module with no binding, exactly
  as T-682). All three re-run GREEN on the final commit together with the importer folders listed below.
- Freeze check 0 differing; codemap check stale none; the chain run re-asserts every earlier version's sha.
