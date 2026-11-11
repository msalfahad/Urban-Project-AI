# T-704: CONCRETE GATE B ROUND 8 integration package, ARCH_TAKEOFF_V3.0.71 (lane I)

Worker 3, 2026-11-11. INTEGRATION PACKAGE for Checker Gate B. Base: the candidate of record V3.0.70 (T-693, Gate B
PASS, merge 2bfa2fbe, run of record e8e001de); released default V2.9 + route G untouched; nothing released. No drawing,
workbook, client name or coordinate here; Drive files named by folder and title only.

## 1. What is wired (Checker-merged only)

| source | merge | Checker | wired as |
|---|---|---|---|
| T-699 R-T699-1: one-sided bounds of the 21 blank STR.CONC.LINTEL lines (`out/T699_LEDGER.json`, sha c41adc99, rebuilt by its own merged builder and asserted equal) | 3b0e03d4 | Verifier 2026-11-11T10:03Z GATE A PASS (own P7757 re-measure W08 / D-2F-02 / L-GF-01 AGREE, family AT_MOST 1.321826 AGREE) | LINTEL_SIDE AT_MOST x 16, DATUM_NAMED x 3 |
| T-678 / T-682 AT_LEAST of D-GF-04 / D-1F-06 (0.048 / 0.036 m3) | f8515d4b / V3.0.67 | already in the candidate since V3.0.67 (LOWER_ONLY) | CONFIRMED unchanged (asserted on the live line, byte-identical) |

**Finding while wiring (F-T704-1):** the row text says "2 AT_LEAST 0.084 m3 ... wire blank -> HELD one-sided". Those two
lines already carry exactly that figure beside them since V3.0.67 (T-682 LOWER_ONLY, record `concrete_ledger_v3067`,
existence ASSUMED - OWNER-APPROVED on Q-55 C with its re-run trigger). Restating them would write the same physical
statement twice under two records; the package confirms them (value, kind, record asserted; line sha recorded in the
run log) and changes nothing on them. T-699 itself says "D-GF-04 / D-1F-06 unchanged from T-678".

## 2. Method (R-T704-1, every villa; module `engine/source/arch_v3071.py`)

- Physical element (ERS s.2.1): one cast lintel over one opening, B (host wall) x D (ST p.13 schedule depth) x (clear
  width + the bearing taken at each end). Its line quantity is 0 (no masonry over the head, or a member soffit serves
  the opening) or a value in [lo, hi]; so an AT_MOST holds even while existence is open.
- (aa) The figure is RECOMPUTED at wiring time from its terms carried in the inputs: section (metres, cm / mm refused),
  width used (largest of a width CONFLICT), two ends each with a RECORDED stopper (COLUMN / END_OF_MASONRY / END /
  OPENING / SEARCH_LIMIT), the drawn available length and the bearing taken (never more than the available length 1 mm
  up); AT_MOST ceiled, conditional least floored at 6 dp in a local decimal context (R-T696-1); equal to the ledger or
  refused. The end terms are re-derived by `t704_inputs.py` with the T-699 rule functions (unchanged) and their sum is
  asserted equal to the ledger's length.
- (bb) The line stays HELD blank (BLOCKED_RFI, no measured_net, no bounded_range): the figure sits in the record
  `concrete_ledger_v3071.beside` {kind AT_MOST_M3, value, convention, length, terms}; the rfi question names the cause
  class, the reference and the deciding datum (and the member of a conditional exclusion). No code total moves
  (asserted: `check_totals` refuses any moved total). The family AT_MOST is a run-record figure only: sum of the exact
  figures less the W11 / W12 pier both take whole (counted once) = 1.321826 m3, recomputed and asserted.
- (cc) AT_MOST only with existence OPEN or CONDITIONAL_EXCLUSION (member named); an AT_LEAST needs existence REQUIRED
  and is not formed here (refused); a line that already carries a one-sided figure is refused for restatement.
- (dd) The "if REQUIRED" least figure is beside as CONDITIONAL, never a bound, never above the AT_MOST.
- Earlier records are not moved: the V3.0.53 lintel record stays in place (the V3.0.67 lintel check reads it); the V3.0.64
  .. V3.0.67 / V3.0.70 concrete checks, the V3.0.67 lintel check, the V3.0.68 masonry check and the V3.0.69 finish check
  re-run on the result.

Owner manual method vs drawing-derived method, side by side: owner = one precast piece per opening, the shortest of
1.20 / 1.50 / 2.50 / 3.00 / 4.00 m >= opening + 2 x 0.15 (e.g. W08 1.50 -> 2.50 m piece; doors 0.8 / 0.9 -> 1.20 m),
existence from the head vs the soffit; drawing = RC cast (ST p.13 prints every lintel cast, 60 / 60), B x D x (w + drawn
bearings), 0.40 printed schedule bearing governing over the 0.15 owner minimum. The m3 follows the drawing; the owner
piece is carried beside per line (`owner_manual`).

## 3. Lines (STR.CONC.LINTEL, m3; every one HELD blank before and after; beside = never summed)

| opening | line | existence | AT_MOST by hand (B x D x (w + ends)) | if REQUIRED | cause |
|---|---|---|---|---|---|
| W04 | L-1313767d | COND. EXCL. (CB6) | 0.04 x (0.60 + 0.40 + 0) = 0.040 MIN_BEARING | 0.040 | D-39 / Q-54 B |
| W08 | L-7f9eb7cc | COND. EXCL. (CB6) | 0.04 x (1.50 + 0.45 + 0.55) = 0.100 | 0.092 | D-39 / Q-54 B |
| W11 | L-c1e57b06 | COND. EXCL. (B9) | 0.04 x (1.95 + 0.633 + 1.146) = 0.149160 | 0.110 | T-207 |
| W12 | L-e3917519 | COND. EXCL. (B9) | 0.04 x (1.95 + 1.146 + 0.413) = 0.140360 | 0.110 | T-207 |
| W25 | L-bf88bf6f | OPEN | 0.04 x (1.00 + 0.40 + 0.10) = 0.060 MIN_BEARING | 0.056 | R-T228-3 F3 |
| W26 | L-b699ce0d | COND. EXCL. (stair-roof piece) | 0.04 x (1.20 + 0.75 + 0.75) = 0.108 | 0.080 | D-39 |
| W27 | L-f892163c | OPEN | 0.04 x 1.50 = 0.060 MIN_BEARING | 0.056 | R-T228-3 F4 |
| D-GF-08 | L-0d5e2e3a | COND. EXCL. (lift tie beam) | 0.04 x (1.00 + 0.40 + 0.10) = 0.060 | 0.056 | D-43 |
| D-GF-09 | L-072bc37c | OPEN | 0.04 x (1.00 + 0.40 + 0.1469) = 0.061876 (width 0.90 / 1.00 CONFLICT: 1.00) | 0.052 | T-581 |
| D-1F-01 | L-2c1c49db | OPEN | 0.03 x (0.80 + 1.373 + 2.428) = 0.138030 | 0.048 | T-227 |
| D-1F-09 | L-96160886 | OPEN | 0.03 x (0.90 + 0.445 + 2.863) = 0.126240 | 0.051 | T-227 |
| D-2F-02 | L-1c0e7646 | COND. EXCL. (BM-2F-017) | 0.04 x (0.90 + 0.2516 + 0.2484) = 0.056 MIN_BEARING | 0.036 | D-04 / Q-61 C(4) |
| L-GF-01 / L-1F-01 / L-2F-01 | L-8f69c407 / L-a500f10e / L-fd8aaedc | OPEN | 0.04 x (1.00 + 0.40 + 0.40) = 0.072 each | 0.072 | D-45 |
| P-GF-01 | L-d887eecf | OPEN | 0.04 x (0.90 + 0 + 0.40) = 0.052 MIN_BEARING | 0.052 | D-45 |
| A-GF-01 | L-b729bd63 | OPEN | none: curved head (T-238) | - | DATUM_NAMED |
| D-GF-05 | L-df32d6f4 | OPEN | none: START stopper unrecorded | 0.040 | DATUM_NAMED (Q-67) |
| D-GF-14 | L-17953d78 | OPEN | none: no jamb evidence (GF-W30) | 0.024 | DATUM_NAMED (MEASURABLE NOW) |
| D-GF-04 / D-1F-06 | L-274b1125 / L-9ec762c0 | REQUIRED (Q-55 C) | AT_LEAST 0.048 / 0.036 (V3.0.67, confirmed) | - | METHOD GAP (junction END) |

Family AT_MOST (16 lines): 1.367666 - 0.04 x 1.146 (W11 / W12 pier once) = **1.321826 m3**; AT_LEAST 0.084 m3 (2
lines); 3 lines no figure. STR.CONC.LINTEL census before and after: 61 lines = 16 released + 24 bounded 1.361 ..
2.050636 + 21 blank; released / bounded / every code total unchanged (a beside figure is never summed).

## 4. Run of record, line-by-line diff

Drive 'Alsenan chalet project' copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) and 'ST7757 dxf.dxf'
(9f9d1179), decoded by the wrapper into the private folder only: own fresh t167 `v304_run.py` (28 min) ->
`research/agents_t704/v3071_run.py` (exit 0): every earlier version re-run and asserted, **V3_0_69 7ea65f9b, V3_0_70
e8e001de (asserted = T-693 run of record)** -> **V3_0_71 ddb559b9**, 5,123 lines; replaced 19 (16 AT_MOST + 3
DATUM_NAMED), added 0, outside 5,104 byte-identical (asserted); totals moved: none (asserted). Diff vs V3.0.70: CHANGED
19 (fields calculation / rfi / notes only: evidence_state, measured_net, bounded_range unchanged on every one), SAME
5,104. vs released V2.9 + route G: NOT_IN_RELEASED 3,531, QUANTITY_DIFFERS 1,054, SAME_QUANTITY 538, unchanged from
V3.0.70. The 2 confirmed lines (D-GF-04 / D-1F-06) byte-identical, their V3.0.67 AT_LEAST asserted on the live line.
Census `t479_registry_census.py` (unchanged; verdict set board verdicts/V3.0.44 b3b08dd7, downgrade snapshot
81732639) on V3_0_70 reproduces `research/agents_t693/out/LINE_INDEX_V3_0_70.json` byte for byte; on V3_0_71 ->
`out/LINE_INDEX_V3_0_71.json` (e230f6b5), issues {}, complete map, 0 stale blocks; its `lines` equal V3.0.70's (no
class / quantity / range change). `t704_package_families.py` (chain 70 -> 71): no quantity family changed, B9-02
record only. Summary `summary_t704.json` (lintel census by what sits beside each blank line).

| STR.CONC.LINTEL | V3.0.70 | V3.0.71 |
|---|---|---|
| released | 16 lines, 1.016 m3 | same |
| bounded | 24 lines, 1.361 .. 2.050636 m3 | same |
| blank, AT_MOST beside | 0 | 16 (family 1.321826 m3, never summed) |
| blank, AT_LEAST beside | 2 (0.084 m3, V3.0.67) | 2 (same lines, unchanged) |
| blank, datum only | 19 | 3 (datum named) |

## 5. Held / missing, downstream, verdicts

Held: every one of the 21 lines stays HELD blank; existence UNRESOLVED on
designer items (D-39 / Q-54 B, T-207, R-T228-3, D-43, T-581, T-227, D-04, D-45, T-238, Q-67); the D-GF-04 / D-1F-06 high
end is a METHOD GAP (a Lead / Checker ruling on a junction end, ERS s.2.7 not met: no owner question); D-GF-14 is
MEASURABLE NOW (a lane S read of the GF-W30 run). Downstream: lintel formwork, rebar and bed mortar of these openings
are not re-derived from a one-sided figure (V3.0.70 lines byte-identical). Freelancer: no lintel concrete row (T-571):
NOT_COMPARABLE. Verdict proposals: 16 AT_MOST ENGINE_RIGHT as bounds (Checker AGREE on 3 by re-measure, the rest by
the hand rows above), existence UNRESOLVED; 3 datum-named lines UNRESOLVED with the datum named.

Lesson row (ERS s.7, proposed): | 2026-11-11 | a task row asked to wire two AT_LEAST bounds the candidate had carried
since V3.0.67 | the row was written from the research census, not from the candidate's records | before wiring a bound,
read the candidate line's records: a figure already beside it is confirmed, never restated under a second record |
tests/t704_lintel_side (test_adverse_line_with_a_figure_beside_already) | PROPOSED |

## 6. Validation

- L1 / L2: `tests/t704_lintel_side` (44 = 29 module + 4 inputs + 11 master; hand villa K704, not the development villa: W1 CEILING 0.04 x 2.35 = 0.094,
  D1 MIN_BEARING 0.03 x 1.55 = 0.0465 with a conditional exclusion, W2 / W3 sharing a pier taken whole (family
  0.350582 with the pier once), W4 directed ceiling 0.06004125 -> 0.060042, A1 curved head DATUM_NAMED, D9 V3.0.67
  AT_LEAST confirmed; lines stay HELD blank, no total moves, outside lines byte-identical, mirror order; adverse: a
  half-up rounded ledger, a bearing beyond the drawn length, an open (crossing-wall) end, one end only, a section in
  cm, a missing depth (never 0), a length that is not the terms, a conditional least above the AT_MOST, existence
  REQUIRED, an exclusion with no member, a figure on a datum-named line, the pier counted twice / not taken whole, a
  bounded line, a line already carrying a figure, a stale confirm, applied twice, a line named twice, another project,
  a beam code, a valued restated line, a moved total), the inputs builder on the committed ledger (counts, hand rows,
  family, tampered pin), master 1.72.0 (pending) builder / checks / adverse.
- L3 on the task branch: every test folder that imports `tools/urban_boq_m9.py` or an `arch_v305x .. v307x` module (68
  folders) + t212 / t379 / t459 / t463 / t485 / t699 / t061: 2,773 passed, 0 failed, 39 skipped (private inputs),
  2 xfail (d2530eea: m9_* + gates 1,260 / 27 s / 2 x; 6149774f: the other 45 folders 1,513 / 12 s). Freeze 0, codemap
  stale none, `build_master_1_72_0.py --check` True / 0 problems. L4 full suite: for the Checker's Gate B (as T-693).
