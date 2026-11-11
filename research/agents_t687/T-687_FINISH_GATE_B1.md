# T-687: PLASTER / PAINT GATE B ROUND 1 integration package, ARCH_TAKEOFF_V3.0.69 (lane I)

Worker 3, 2026-11-11. INTEGRATION PACKAGE for Checker Gate B. Base: the candidate of record V3.0.68 (T-672, Gate B
PASS, merge 4d1b254c, run of record d1de50cb); released default V2.9 + route G untouched; nothing released. No drawing,
workbook, client name or coordinate here; Drive files named by folder and title only.

## 1. What is wired (every piece Checker-merged)

| source | merge | Checker | wired as |
|---|---|---|---|
| T-676 OP-009 reveal fix row (1.08 m2, Q-55 C) + A-1F-01 cause correction | cffefa0c | Verifier 2026-11-10T16:0xZ GATE A PASS (own DXF read of both) | FIN_RESTATE VALUE / CAUSE |
| T-680 R-T680-1 / -2 stair-shaft ST-01 storey bands (W25 / W27 heads, pier returns by band) | 707c624e | Verifier 2026-11-10T17:00Z GATE A PASS (own N face 1F / 2F 8.60 m2) | FIN_RESTATE BOUND x 6 |
| T-686 R-T686-1 / -3 annex wet backing, annex paint, stair-core wet backing | 8a0fc1e1 | Verifier 2026-11-11 00:05 GATE A PASS (own datums + arithmetic of all 8; faces inherited) | FIN_RESTATE BOUND x 8 |
| T-690 R-T690-1 wet-room band above the ceiling (F-T686-1) | adef31c5 | Verifier 2026-11-11 02:02 GATE A PASS (own 1F-07 10.8416, GF-06 8.545994 .. 8.555) | WET_BAND ADD x 18 |

T-684 (MERGED 8563a6fa) closed the Checker challenge F-V680-1 (MS2 NW corner) ENGINE_RIGHT with 0 change: the shaft
lines are wired exactly as T-680 verified them. T-690 parts (a) tile census, (b) OP-020 skirting and (d) MS2-TR nosing
are not plaster / paint and are not wired here (FIN.SKIRTING / B7-05 rows of their own).

## 2. Method (R-T687-1, every villa; module `engine/source/arch_v3069.py`)

- (a) FIN_RESTATE: a named HELD FIN.PLASTER / FIN.PAINT line is restated only when the merged ledger names it by id
  AND the candidate figure the ledger started from equals the line (asserted: blank, or the exact low .. high).
  BOUND: 0 < low < high, the open datums written in the line's question. VALUE: a bound closed from inside on an
  owner-approved fallback -> PROVISIONAL, status ASSUMED - OWNER-APPROVED with its source. CAUSE: the cause text is
  corrected and the line stays HELD blank (a corrected cause never makes a quantity).
- (b) WET_BAND: one new FIN.PLASTER line per wet room, element '<engine room>:plaster band above ceiling', bound by id
  to the room's tile-backing FIN.PLASTER line, never summed into it (a different coat by a different trade; plaster owns
  the band, register ruling 2026-11-11). The band is RECOMPUTED in the module from the merged terms and asserted equal
  to the ledger: main house L x ((1 - s)(S_floor - H) + s (S_roof - H)) - beam ends (the larger deduction at the low
  end); annex / stair core: gross high asserted = L x max(S - H), S - H fixed on one datum for the annex. A band is
  PROVISIONAL only where T-690 states ASSUMED - OWNER-APPROVED (H Q-48 A on a DRAWING-CONFIRMED soffit, 4 rooms);
  every other band is HELD BOUNDED with its datum named, including the two annex bands whose figure is datum-invariant
  (GF-03 4.425, GF-05 3.304: S - H = 0.59 at every datum, but the datum itself is Q-54 B HOLD: kept HELD, low = high).
  Where backing line and band hang on one datum, the joint room total (R-T690-1 (d)) is carried BESIDE in the band
  record, never the sum of the two separate extremes.
- (c) Only FIN.PLASTER|m2 / FIN.PAINT|m2 totals move, each exactly by the changes and equal to the inputs' expected
  totals (computed by `t687_inputs.py` from the committed V3.0.68 line index and cross-checked against the T-686
  'after_round3' totals); every other line byte-identical (asserted); the V3.0.67 concrete / lintel checks and the
  V3.0.68 masonry check re-run on the result. No line is VERIFIED; installed quantities only.
- (d) Coat materials (Q-79 internal 1:4, render 1:4, spatter 1:2) wire only on material lines; the candidate holds no
  plaster / render / spatter material line (T-676 F-T676-3, T-364 MISSING), so none is opened here (WAITING record).

Owner manual method vs drawing-derived method, side by side: owner = face length x height (plaster to the slab
underside, paint to the finished ceiling) - openings in full (Q-73); drawing = the same with the heights and faces
taken from the drawings and the merged records (shaft: T-173 model + T-201 vector heads; annex: slab top bounded 3.544
.. 4.30 by R-T678-2 and the roof mark, S = s - 0.46, H = s - 1.05; band: S from storey interval - 0.05 - 0.16). The
owner G1 manual method (plaster at the paint height) gives no band; the later owner rule (plaster to the slab underside,
2026-11-02 / Q-72) governs, so the band lines are a RULE_DIFFERENCE against G1 and an ENGINE_OMISSION closed against
the current rule.

## 3. Run of record and line-by-line diff

Drive 'Alsenan chalet project' copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) and 'ST7757 dxf.dxf'
(9f9d1179), decoded into the private folder only: own fresh t167 `v304_run.py` -> `research/agents_t687/v3069_run.py`
(exit 0): every earlier version re-run and asserted, **V3_0_68 d1de50cb (asserted = T-672 run of record)** ->
**V3_0_69 7ea65f9b**, 5,123 lines; replaced 16 (14 BOUND + 1 VALUE + 1 CAUSE), added 18 (bands), outside 5,089
byte-identical (asserted). Diff vs V3.0.68: CHANGED 16, ADDED 18, SAME 5,089. vs released V2.9 + route G:
QUANTITY_DIFFERS 1,049 -> 1,054 and SAME_QUANTITY 543 -> 538 (five lines that were equal to V2.9 as blank / the same
bound are now restated: GF-RA3AD49 / GF-RB62B55 / GF-RDF7D28 / GF-RFAD3C4 plaster, OP-009), NOT_IN_RELEASED 3,513 ->
3,531 (+18 bands): no released V2.9 line moved. Totals moved: FIN.PLASTER|m2 and FIN.PAINT|m2 only, equal to the
inputs' `expect_totals` (asserted in the run). Census `t479_registry_census.py` (unchanged; verdict set V3.0.44
b3b08dd7, downgrade snapshot 81732639) on V3_0_68 reproduces `research/agents_t672/out/LINE_INDEX_V3_0_68.json` byte
for byte; on V3_0_69 -> `out/LINE_INDEX_V3_0_69.json` (e908a5f1), issues {}, complete map, 0 stale blocks.
`t687_package_families.py` (T-483 attribute unchanged, chain 68 -> 69): B4-03 FIN.PLASTER 10 changed + 1 record-only
+ 18 added; B4-06 FIN.PAINT 5 changed. Summary `summary_t687.json`.

Code census, V3.0.68 -> V3.0.69 (m2; blank lines counted, never summed as 0):

| code | V3.0.68 | V3.0.69 |
|---|---|---|
| FIN.PLASTER | 62 lines: 363.3738 valued + 932.72581 .. 1,006.77641 (14 bounded) + 10 blank | 80 lines: 388.58436 valued (+1.08 OP-009, +24.13056 four bands) + 1,131.965876 .. 1,300.69428 (34 bounded) + 3 blank |
| FIN.PAINT | 14 lines: 217.2081 valued + 487.121 .. 542.8606 (7) + 3 blank | 14 lines: 217.2081 valued + 601.645338 .. 682.3313 (10) + 0 blank |

Changed / added lines (hand check of each: the merged ledger figure, and for the bands the module's recompute):

| line | code | element | before | after | by hand |
|---|---|---|---|---|---|
| L-95f2c45c / L-145bd239 | PLASTER / PAINT | shaft ST_GF | 48.52 .. 62.01 | 50.945 .. 62.434 | +2.000 W25 band below +5.50 + 0.423 returns (low); + 0.424 (high) |
| L-0eac839f / L-2ab93d50 | PLASTER / PAINT | shaft ST_1F | 42.48 .. 47.67 | 45.317 .. 46.564 | N face HI 2.50 x 4.20 - 1.50 - 0.40 = 8.60 (Checker AGREE) |
| L-418121a4 | PLASTER | shaft ST_2F | blank | 47.342 .. 48.772 | N face HI 2.50 x 4.04 - 1.50 = 8.60 (Checker AGREE) |
| L-5a7a5c6f | PAINT | shaft ST_2F | blank | 45.392 .. 46.822 | plaster band - 0.15 below the soffit (Q-48 A) |
| L-2211463b | PLASTER | GF-02 wash | blank | 13.7028 .. 21.64 | 7.2 x 2.494 - 1.76 - 1.0 x 2.494; 7.2 x 3.25 - 1.76 |
| L-f43782d5 | PLASTER | GF-03 W.C. | blank | 16.945 .. 22.615 | 7.5 x 2.494 - 1.76; 7.5 x 3.25 - 1.76 |
| L-f179fc08 | PLASTER | GF-05 W.C. | blank | 12.2064 .. 16.44 | 5.6 x 2.494 - 1.76; 5.6 x 3.25 - 1.76 |
| L-595181aa | PLASTER | GF-06 kitchen | blank | 31.720506 .. 42.6735 | 14.5 x 2.494 - 1.501 x 1.494 - 2.20; 14.5 x 3.25 - 1.501 x 1.50 - 2.20 |
| L-3f7fb1b3 | PLASTER | GF-10 core | blank | 11.40 .. 25.21 | 6.2 x 2.20 - 1.76 - 0.48; 6.2 x 4.35 - 1.76 |
| L-a636dabc | PLASTER | GF-11 core | blank | 7.04 .. 19.555 | 4.9 x 2.20 - 1.76 - 0.9 x 2.2; 4.9 x 4.35 - 1.76 |
| L-cdf7f5cd | PAINT | GF-01 dewaneya | blank | 36.911738 .. 56.9257 | 20.127 x H - W11 / W12 - D-GF-01 - arch (T-686) |
| L-d7d6d2f7 | PAINT | GF-04 driver | blank | 26.9586 .. 36.405 | 12.5 x 2.494 - 0.6 x 0.794 - 1.98 - 1.76; 12.5 x 3.25 - 0.48 - 1.98 - 1.76 |
| L-f4175f99 | PLASTER | OP-009 reveal | 1.08 .. 1.20 | 1.08 PROVISIONAL | 2 x 0.20 x 2.20 + 0.20 x 1.00 (Q-55 C) |
| L-64cb94b4 | PLASTER | A-1F-01 reveal | blank | blank, cause corrected | drawn 1.000 x 0.150 on the 1F plan; rise D-45 |
| 4 bands VALUE | PLASTER | 1F-07 / 1F-08 / GF-12 / GF-13 | new | 10.8416 / 4.1856 / 4.74496 / 4.3584 | 16.94 / 6.54 / 7.414 / 6.81 x 0.64 |
| 5 bands roof | PLASTER | 1F-02 / 1F-03 / 1F-12 / 2F-02 / 1F-09 | new | 3.51 .. 6.21 x 2 / 3.393 .. 6.003 / 3.783 .. 6.693 / 4.275 .. 4.9818 | L x (S_roof 3.74 .. 4.04 - 3.35); 1F-09 share 0.31 |
| 2 bands terrace / beam | PLASTER | GF-07 / GF-16 / GF-14 | new | 2.853686 .. 6.918815 / 2.2448 .. 5.085875 / 5.05488 .. 5.29088 | share 0.39 / 0.54, S_roof 3.65 .. 4.34; B27 1.242, B11 0.236 at the low end |
| 4 bands annex | PLASTER | GF-02 / -03 / -05 / -06 | new | 3.658 .. 4.248 / 4.425 / 3.304 / 8.545994 .. 8.555 (HELD) | L x 0.59 on one datum (A-GF-01 0.59 at low; W08 0.009006 at low) |
| 2 bands core | PLASTER | GF-10 / GF-11 | new | 3.584 .. 17.298 / 2.56 .. 13.671 | L x (S 4.29 .. 4.99 - H 2.20 .. 4.35); joint 24.358 .. 29.178 / 15.40 .. 22.691 beside |

Band totals 78.83192 .. 123.02493 m2 (= T-690); annex 19.932994 .. 20.532 (= F-T686-1 gross 20.532).

## 4. Held / missing, named

- FIN.PLASTER 3 lines HELD blank: A-GF-01 / A-1F-01 arch reveals (spring / rise printed nowhere, D-45; information
  only <= 1.302 / 1.347 m2), D-GF-15 gate reveal (D-53, T-313). A-1F-01 now carries the corrected cause.
- 14 band lines HELD bounded: roof build-up D-39 / DCR-6 (1F-02, 1F-03, 1F-09, 1F-12, 2F-02), terrace build-up with no
  merged upper bound (GF-07, GF-16), beam-end count (GF-07 B27, GF-14 B11), annex datum Q-54 B (GF-02 / -03 / -05 /
  -06), stair-core floor +0.30 / +1.00 (GF-10 / GF-11, C-SH-2 designer).
- Spatter dash (T-364), coat materials and water: MISSING / HELD (no line, no ratio).
- F-T690-1 (B27 soffit 0.05 below the GF-07 ceiling) and F-T680-1 (W25 raster vs vector, 0.26 m2 per finish on the 1F
  shaft lines) stay named findings; neither moves a line.

## 5. Freelancer, verdicts, lesson

Freelancer: stair-house walls gross 204.42 m2 with half-deducted openings (T-173 s.3: like for like -27.35 m2,
-13.4 %), annex paint GF-01 72.0 vs engine gross 50.197 .. 65.413 (-30.28 .. -9.15 %), GF-04 45.0 vs 31.175 .. 40.625
(-30.72 .. -9.72 %) at his flat 3.60 m: RULE_DIFFERENCE (owner G1 to the finished ceiling); his plaster stops at his
paint height, so no band in his BOQ: RULE_DIFFERENCE; wet rooms not itemised per room: UNRESOLVED. Verdict proposals:
shaft lines ENGINE_RIGHT on scope (open south side, R-SHAFT-1) and on heads (T-201 drawn 1.50 vs his 2.00); OP-009
UNRESOLVED (no itemised row); bands ENGINE_OMISSION closed (scope, not measurement).
Lesson row (ERS s.7, proposed): "a component that sits between two finished layers (the band between the tile top and
the plaster top) is its own line bound by id to the layer it continues, recomputed from its merged terms at wiring time
and never summed into that layer; a figure that does not depend on a held datum stays HELD while the datum is held
(every villa; T-687)".

## 6. Validation

- L1 / L2: `tests/t687_finish_gate_b1` (hand villa K687, not the development villa: shaft band bound, blank paint
  bound, a point band PROVISIONAL, a roof-share band recomputed 3.92 .. 5.32, a datum-invariant annex band HELD with its
  joint total beside, a reveal VALUE, a cause-only restatement; mirror order; adverse: a ledger that started from
  another figure, a value outside its bound, a value without the owner status, a cause with a figure, VERIFIED, a
  structural code, low 0, a point as a bound, a line named twice, a band figure not the recompute, millimetres as
  metres, a zero band, an owner-approved range, a held band with no datum, a wrong gross, two bands per room, a roof
  share without a roof bound, a backing line of another room / a paint line / an excluded line, a released line,
  applied twice, totals not the inputs', a stray structural change; a tiled face keeps no paint), the inputs builder
  on the committed ledgers (counts, hand figures, totals, tampered pin refused), master 1.70.0 (pending) builder /
  checks / adverse. 43 pass.
- L4 full suite on the task tree (c2b7f2ad, with the two later code edits landing during the run): 22,922 passed,
  678 skipped (377 private-input phases), 105 xfail, 0 failed; the determinism guard flagged only this task's own test
  file, edited while the suite ran. After the final commit: t687 + t672 + t682 + t677 + t479 + t459 + t457 + t483 +
  m9_foundation + t131 + codemap + t061 re-run (L3 importer folders of the hub), see the handoff.
- Freeze check 0 differing; codemap check stale none; the chain run re-asserts every earlier version's sha.
