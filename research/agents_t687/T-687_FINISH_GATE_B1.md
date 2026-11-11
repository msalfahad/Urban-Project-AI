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

RUN_PLACEHOLDER

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

VALIDATION_PLACEHOLDER
