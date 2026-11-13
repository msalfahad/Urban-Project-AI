# T-703: MASONRY GATE B ROUND 4 integration package, ARCH_TAKEOFF_V3.0.72 (lane I)

Worker 3, 2026-11-11. INTEGRATION PACKAGE for Checker Gate B. Base: the candidate of record V3.0.71 (T-704 r2, Gate B
PASS, merge b211b3a2, run of record fc0bd98f); released default V2.9 + route G untouched; nothing released. No drawing,
workbook, client name or coordinate here; Drive files named by folder and title only.

## 1. What is wired (Checker-merged only)

| source | merge | Checker | wired as |
|---|---|---|---|
| T-696 `out/T696_B9_CENSUS.json` (6810a8ea): one-ended figures beside blank B9 material lines | 5b51924e | Verifier 2026-11-11 05:55 GATE A PASS | ONE_SIDED x 11 (2F roof-datum part hosts: black units / mortar AT_MOST x 6, AAC glue AT_MOST x 3; MAIN_S units / mortar AT_LEAST x 2) |
| T-696 `out/T696_B9_BOUNDS.json` (e9835de4): R-T696-1 directed rounding of the 15 bounded B9 lines | 5b51924e | same | BOUND_ROUNDING x 10 (5 already contain their exact interval: byte-identical) |
| T-713 `out/T713_MASONRY_REST.json` (0be1ddcd): R-T713-1 parent one end | aa4d8979 | Verifier 2026-11-11T17:58Z GATE A PASS (own re-measure 2F 0.15 parent 1.965 AGREE) | ONE_SIDED x 7 (2F 0.15 parent AT_MOST 1.965 m2 + units / mortar / glue; GF 0.15 parent AT_LEAST 12.9311 m2 + black units / mortar) |

Every ledger is sha-pinned in `t703_inputs.py` (a rebuilt or tampered file is refused); every figure is RECOMPUTED by
the module from its terms (area x rate, parent components, exact ends) and asserted equal to the ledger.

## 2. Method (R-T703-1, every villa; module `engine/source/arch_v3072.py`)

- Physical element (ERS s.2.1): a B9 material line is the units / mortar / glue of ONE host block face; a parent
  MAS.BLOCK line is the sum of the held walls / pieces no colour part line carries. A host with one drawn end gives a
  one-ended figure: AT_MOST at the drawn physical maximum (roof build-up b_r >= 0, member depth >= 0), AT_LEAST from a
  positive drawn minimum (GF-W22 conflict low end; MAIN_S h >= 0.70 one leaf).
- (g) the figure sits BESIDE the HELD blank line (record `masonry_gate_b_v3072.beside` {kind AT_MOST_<unit> /
  AT_LEAST_<unit>, value, exact, basis}); the line keeps BLOCKED_RFI, no measured_net, no range; never summed.
- (h) parent AT_MOST only when every component has an upper end; AT_LEAST only from positive drawn minima; a material
  is never firmer than its host (AT_LEAST only for the colour of the minimum: GF 0.15 gives no glue / white minimum);
  white units (no AAC count rule, Q-60) and perimeter joints (no piece ends) get no figure.
- (i) R-T696-1: AT_MOST and range highs UP, AT_LEAST and range lows DOWN at 6 dp, from exact decimal inputs in a local
  decimal context (never from rounded components).
- (j) a line already carrying a one-sided figure, a line named twice, a stale binding, a second application: refused.
- Rates (from the inputs, each with its source): black units 12.5 / m2 (UPC-BLACK-BLOCK-001 1.1.0, Q-75 / Q-80);
  laying mortar 0.0110625 / 0.01475 m3 per m2 at 0.15 / 0.20 (T-670, Q-78 1:4, 10 mm joint PROVISIONAL); AAC glue
  3.5 / 4.5 kg per m2 (owner 2026-11-02). Register: mesh / sharmat never inside the block m2 (untouched here).

Owner manual method vs drawing-derived method, side by side: owner = wall length x height floor to soffit less
openings, x 12.5 blocks / m2, mortar 1:4, glue by bag rate, a height not printed held with a designer request; drawing
= the same rates on the host area read from the drawings, the unprinted datum bounded on one side only (b_r >= 0,
member depth >= 0, drawn conflict low end). The two agree on rates; the held quantity is the area, not the method.

## 3. Lines (beside = never summed; every line HELD blank before and after)

| line | host | code | kind | by hand | cause |
|---|---|---|---|---|---|
| L-c76dd0d1 / L-b765c24a | 2F 0.15 OA black (W08) | units / mortar | AT_MOST | 9.47 x 12.5 = 118.375 pcs; x 0.0110625 = 0.104761875 -> 0.104762 m3 | D-39 b_r |
| L-a9876502 / L-3cdc29f2 | 2F 0.20 DC black (W05) | units / mortar | AT_MOST | 3.85 x 12.5 = 48.125; x 0.01475 = 0.0567875 -> 0.056788 | D-39 |
| L-8075d1bd / L-539af3a6 | 2F 0.20 V black (W01+W06) | units / mortar | AT_MOST | 21.945 x 12.5 = 274.3125; x 0.01475 = 0.32368875 -> 0.323689 | D-39 |
| L-bd48d897 / L-4ccc5dc2 / L-320814d3 | 2F white 0.15 OA / 0.20 DC / 0.20 V | glue | AT_MOST | 25.895 x 3.5 = 90.6325; 16.225 x 4.5 = 73.0125; 21.7875 x 4.5 = 98.04375 kg | D-39 |
| L-bd21b0ea / L-cf220ce7 | MAIN_S | units / mortar | AT_LEAST | 11.389 x 12.5 = 142.3625; x 0.0110625 = 0.1259908125 -> 0.125990 (CONDITIONAL one leaf >= 0.15) | OPEN BOUND |
| L-246f3c09 | 2F 0.15 parent | MAS.BLOCK | AT_MOST | 0.10 x 4.25 + 2 x 0.20 x 3.85 = 1.965 m2 | D-04 / D-39 |
| L-318e6311 / L-cdb8d543 / L-d6373b9f | 2F 0.15 parent | units / mortar / glue | AT_MOST | 24.5625 pcs; 0.0217378125 -> 0.021738 m3; 6.8775 kg | D-04 / D-39 |
| L-0d9b9e89 | GF 0.15 parent | MAS.BLOCK | AT_LEAST | GF-W22 low end 12.9311 m2 (D-27) | annex datum, GF-W30, A-GF-01 |
| L-dc7b4e20 / L-39a62186 | GF 0.15 parent | black units / mortar | AT_LEAST | 161.63875 pcs; 0.14305029375 -> 0.143050 m3 | same |

Ranges restated (R-T696-1; exact ends from the line's inputs; m3):

| line | code | V3.0.71 | V3.0.72 | exact |
|---|---|---|---|---|
| L-686a15f1 D-1F-09 | LINTEL_BEARING | 0 .. 0.001111 | 0 .. 0.001112 | 0 .. 0.0011115 |
| L-5b828080 D-1F-03 | LINTEL_BEARING | 0.000556 .. 0.000887 | 0.000555 .. 0.000888 | 0.00055575 .. 0.000887143725 |
| L-e5cefb37 D-1F-04 | LINTEL_BEARING | 0.000556 .. 0.000667 | 0.000555 .. 0.000667 | 0.00055575 .. 0.000666622125 |
| L-ae1d4bef / L-ba28032b D-1F-07 / -10 | LINTEL_BEARING | 0.000556 .. 0.000916 | 0.000555 .. 0.000917 | 0.00055575 .. 0.0009160149375 |
| L-dc668eb5 D-GF-10 | LINTEL_BEARING | 0.000556 .. 0.000907 | 0.000555 .. 0.000908 | 0.00055575 .. 0.000907261875 |
| L-866a6602 1F 0.15 OA | MORTAR.BLACK | 0.618315 .. 0.622076 | 0.618315 .. 0.622077 | 0.61831520625 .. 0.62207645625 |
| L-c5969291 1F 0.15 OA | PERIMETER | 0.028344 .. 0.049793 | 0.028342 .. 0.049797 | 0.02834290266 .. 0.04979651991 |
| L-3b5eff6c 1F 0.15 V | PERIMETER | 0.018729 .. 0.019896 | 0.018728 .. 0.019897 | 0.0187284971 .. 0.0198962668 |
| L-dfe9524c GF 0.15 OA | PERIMETER | 0.010361 .. 0.011195 | 0.010360 .. 0.011195 | 0.0103604304 .. 0.0111946807 |

Unchanged (exact already inside, byte-identical): L-4b9a29d4 / L-6989349a / L-aa5532bb glue, L-43e616ee perimeter,
L-1e61a4aa units.

## 4. Run of record, line-by-line diff

Drive 'Alsenan chalet project' copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) and 'ST7757 dxf.dxf'
(9f9d1179), decoded by the wrapper into the private folder only: own fresh t167 `v304_run.py` (about 30 min) ->
`research/agents_t703/v3072_run.py` (exit 0): every earlier version re-run and asserted, V3_0_70 e8e001de (asserted),
**V3_0_71 fc0bd98f (asserted = T-704 r2 run of record)** -> **V3_0_72 f9578744**, 5,123 lines; replaced 28 (18
ONE_SIDED + 10 BOUND_ROUNDING), added 0, outside 5,095 byte-identical (asserted). Diff vs V3.0.71: CHANGED 28, SAME
5,095. vs released V2.9 + route G: NOT_IN_RELEASED 3,531, QUANTITY_DIFFERS 1,054, SAME_QUANTITY 538, unchanged.
Totals moved (held ranges only, asserted equal to the changes): LINTEL_BEARING held 0.002780 .. 0.005404 -> 0.002775 ..
0.005409 m3 (-5e-6 / +5e-6); PERIMETER held low -4e-6, high +5e-6 (0.072178 .. 0.108325 -> 0.072174 .. 0.108330);
MORTAR.BLACK held high +1e-6. Released quantities moved: none; a beside figure is never summed.
Census `t479_registry_census.py` (unchanged; verdicts board verdicts/V3.0.44 b3b08dd7, downgrades 81732639) on
V3_0_71 reproduces `research/agents_t704/out/LINE_INDEX_V3_0_71.json` byte for byte; on V3_0_72 ->
`out/LINE_INDEX_V3_0_72.json` (8e753204), issues {}, complete map, 0 stale blocks; vs V3.0.71 exactly the 10 restated
ranges differ. `t703_package_families.py` (chain 71 -> 72): B9-04 changed (MORTAR 1, LINTEL_BEARING 6, PERIMETER 3),
record B9-01 / B9-04.

B9 census (lines; never summed across lines):

| code | V3.0.71 released / bounded / AT_MOST / AT_LEAST / blank / excluded | V3.0.72 |
|---|---|---|
| MAS.BLOCK m2 | 13 / 0 / 0 / 1 / 14 / 0 | 13 / 0 / 1 / 2 / 12 / 0 |
| MAS.UNITS.BLACK pcs | 7 / 1 / 0 / 0 / 12 / 0 | 7 / 1 / 4 / 2 / 6 / 0 |
| MAS.UNITS.WHITE pcs | 0 / 0 / 0 / 0 / 15 / 2 | same |
| MAS.MORTAR.BLACK m3 | 7 / 1 / 0 / 0 / 12 / 0 | 7 / 1 / 4 / 2 / 6 / 0 |
| MAS.GLUE.AAC kg | 2 / 3 / 0 / 0 / 10 / 2 | 2 / 3 / 4 / 0 / 6 / 2 |
| MAS.MORTAR.BLACK.PERIMETER m3 | 4 / 4 / 0 / 0 / 12 / 0 | same (3 ranges restated) |
| MAS.MORTAR.BLACK.LINTEL_BEARING m3 | 3 / 6 / 0 / 0 / 0 / 0 | same (6 ranges restated) |

(the MAIN_S MAS.BLOCK AT_LEAST 11.389 m2 was already beside before this package: not restated.)

## 5. Held / missing, downstream, verdicts, finding

- Held: every ONE_SIDED line stays HELD blank: D-39 b_r (2F part hosts), D-04 member depths (2F 0.15 parent), annex
  datum D-06 / D-17 + GF-W30 + A-GF-01 width (GF 0.15 parent upper end), MAIN_S leaf and soffit. No figure: white units
  (Q-60 count rule), perimeter joints of the 2F / parent hosts, the five blank parents, ANNEX_S (D-35), the six 2F part
  host MAS.BLOCK lines (T-696 states the material base only). Waste / procurement HELD.
- Downstream: plaster / paint / mesh lines untouched (byte-identical); no concrete line moves.
- Freelancer: blockwork m2 only, no units / mortar / glue rows: RULE_DIFFERENCE, no %.
- Verdict proposals: the 18 figures ENGINE_RIGHT as one-ended bounds (Checker AGREE on the 2F 0.15 parent by
  re-measure, the rest by the hand rows above), UNRESOLVED as quantities; the 10 ranges ENGINE_RIGHT (exact inside),
  the V3.0.71 prints ENGINE_WRONG by <= 4e-6 m3 (rounding direction).
- **F-T703-1:** the T-704 merge left BOQ_FAMILY_MASTER_1.72.0 PENDING (no promotion, no GIT_FACTS refresh), so the
  1.73.0 builder refused its base (merge-order rule). Done on this branch with T-704's own tools, unchanged:
  `t704_promotions_source.py` (merge b211b3a2, verdict read at board 361a6be6) -> `build_master_1_72_0.py --promote
  --write` (--check True, 0 problems) -> manifest by the tool -> `build_t463_facts.py` (ancestry names b211b3a2).
  Checker: please confirm these four files equal what the T-704 merge should have committed.
- Lesson row (ERS s.7, proposed): | 2026-11-11 | a Gate B merge left its registry pending and its git facts stale |
  the promotion step was not in the merge checklist | the merge of a package runs its own promotion + manifest +
  build_t463_facts before publishing; the next package refuses a pending base | tests/t463_git_history,
  build_master --check | PROPOSED |
- Lesson row (ERS s.7, proposed): | 2026-11-11 | one-ended masonry figures sat in research ledgers, not beside their
  lines | wiring waited for a two-ended range | a one-ended figure is wired beside its blank line with its kind,
  recomputed from area x rate and rounded by direction (R-T703-1) | tests/t703_masonry_one_sided | PROPOSED |

## 6. Validation

- L1 / L2: `tests/t703_masonry_one_sided` (35 + 11 master): hand villa M703 (normal: 12 one-sided figures, 2 ranges
  restated, 1 exact range untouched, totals, census, mirror order, decimal context, written files; adverse: half-up
  print, AT_LEAST rounded up, exact not area x rate, area in mm / 0 / missing, parent open component, AT_LEAST without
  minimum, glue minimum from black, white units / perimeter figure, kind RANGE, material firmer than its parent, no
  printed thickness without condition, conditional with printed thickness, missing rate, named twice, line not blank,
  figure already beside, host not a held block, stale / wrong range, inverted ends, bad form, applied twice, another
  project, moved total, unknown source) + the merged-ledger regression (18 / 15 / 10, hand figures, bindings on the
  V3.0.71 index, tampered pin refused).
- L3 on the task branch: every test folder that imports `tools/urban_boq_m9.py`, an `arch_v305x .. v307x` module, the
  family master or the manifest (123 folders incl. t212 / t379 / t459 / t463 / t485 / t696 / t699 / t713 / t061): 0
  failed after the GIT_FACTS refresh (t463 failed once before it, F-T703-1). Freeze 0; codemap stale none;
  `build_master_1_72_0.py --check` / `build_master_1_73_0.py --check` True, 0 problems. L4 full suite: for the
  Checker's Gate B.
