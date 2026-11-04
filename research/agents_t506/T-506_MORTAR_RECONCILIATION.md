# T-506: black-block laying mortar, T-367 vs T-453 r2, and the materials producer-role map

Worker 3, 2026-11-04 (claim 09:02 UTC), base engine 8b94facc. Research only (`t506_mortar_reconcile.py`, `out/`,
`tests/t506_mortar_reconcile/`): no candidate, engine, rule, knowledge or registry file changed; no candidate
(V3.0.50 d40c4ec5) or released (V2.9 + route G) line moves. Inputs sha256-pinned; drawings not re-read (both
ledgers are merged and Checker-verified; this task reconciles them). Rebuild: `python3 -I
research/agents_t506/t506_mortar_reconcile.py` (byte-identical, tested).

## 1. Physical element (ERS s.2.1)
The wet bed + head joint mortar between the units of black (cement) block masonry that is actually built, wall by
wall, before waste. Kept apart: contract area (MAS.BLOCK m2), installed mortar (m3), materials (cement bags, loose
sand: Q-78 1:4 = 8 bags + 1.1 m3 per m3), procurement (waste: none sourced, HELD).

## 2. Reconciliation in units (R-T506-1): residual 0
Joint geometry re-derived (T-367 module, 0.39 x 0.19 + 10 / 10 mm): 0.07375 t -> 0.0110625 (0.15) / 0.01475 (0.20)
m3/m2. All 11 part lines are in V3.0.50 with the same released net (checked against the line index).

| Bucket (24 black walls / pieces, 312.6661 m2) | walls | m2 | m3 |
|---|---|---|---|
| T-453 PROVISIONAL-NET (0.20 m: GF-W01, 1F-W02 / W03 / W09, 2F-W01 / W06) | 6 | 107.7240 | 1.588929 |
| T-453 RANGE-NET 2F-W05 piece (HELD lintel D-2F-02 face 0 .. 0.34 m2) | 1 | 3.8000 | 0.051035 .. 0.056050 |
| 0.15 m on the material base: HELD (module not stated, owner Q-75 answer 2026-11-02), figure beside | 17 | 198.1221 | 2.191725 (low 2.187963: HELD D-1F-09 on 1F-W13) |
| REQUIRED RC lintel faces inside 0.15 m walls (concrete, not laid block; R-T453-5) | 8 | 3.0200 | 0.033408 |
| **= T-367 (contract area, V3.0.26)** | 24 | 312.6661 | **3.870113** |

The Lead's first reading is confirmed with one correction: the 0.20 m residual 0.056050 is NOT a base difference
(2F-W05 is 3.80 m2 in both ledgers, no REQUIRED lintel on any 0.20 m black wall); it is the whole 2F-W05 piece,
which T-453 carries as a RANGE (0.051035 .. 0.056050) outside its point total because the HELD lintel D-2F-02 may
occupy 0 .. 0.34 m2 of it. The 0.15 m set 2.225134 = 2.191725 on the material base + 0.033408 on 3.02 m2 of REQUIRED
lintel faces (1F-W23 D-1F-02 / 04 0.68; 1F-W12 D-1F-03 0.36; 1F-W13 D-1F-08 0.34; 1F-W17 D-1F-10 0.32; 1F-W19 D-1F-07
0.32; 2F-W08 D-2F-03 0.32; GF-W28 D-GF-13 0.36; GF-W29 D-GF-10 0.32). Every opening behind a deducted face is
DEDUCTED in the fill of the same established piece (T-453 lintel rule requires it), so no face is taken from a held
piece. Wall by wall: `out/MORTAR_RECONCILIATION_T506.csv`. 22 black walls / pieces are HELD in both ledgers, blank
by name (never 0).

## 3. Which ledger governs the MATERIAL line (R-T506-2)
T-453 r2 PRODUCES the installed m3, cement bags and sand. Reasons: (a) Q-73 / R-T453-5: a lintel face is concrete;
T-367's contract basis puts 0.033408 m3 of joint where no joint exists; (b) the owner's Q-75 answer (2026-11-02,
UPC-BLACK-BLOCK-001) post-dates T-367 (2026-10-30) and confirms the 40 x 20 module for 0.20 m only, so the 0.15 m
joint is a data item: HELD, T-367's figure beside; (c) Q-78 gives the 1:4 mix T-367 held. T-367 stays the READ
input (per-m2 joint geometry) and a BESIDE figure. T-372 is narrowed (Lead to update the row): a B9-04 line per part
line carrying T-453 r2's figure (3 COMPUTED, 1 RANGE, 7 HELD with T-367 beside), F-T367-1 perimeter joints a separate
HELD component (in NEITHER ledger: T-453 reads T-367's rate), cement / sand produced once. Wired as first written
(T-367 3.870113 m3 as a figure beside T-453) it would double the mortar on the 4 released 0.20 m lines (tested).

## 4. Producer roles (F-C-T496-1, R-T506-3)
Role on all 1,202 T-496 rows (+ 11 T-367 BESIDE rows): T-453 PRODUCER 128; T-455 PRODUCER 128; T-495 PRODUCER 10
(finish options, never summed); T-454 PRODUCER 156 (installed plaster mortar m3), BESIDE 312 (cement / sand, no mix);
T-489 READER 156 (mortar m3, must equal T-454: 0 divergences), PRODUCER 312 (cement / sand from the V2 mix); T-367
BESIDE 11. Census: 675 keys, 472 bound by two tables, keys with two producers 0, reader divergences 0. A wiring sums
PRODUCER rows only: the 4.726962 m3 plaster estimate is counted once (T-454), not 9.453924.

## 5. Engineering result and verdicts
Black mortar wireable now: 1.588929 m3 = 12.711 bags + 1.748 m3 sand (PROVISIONAL-NET, 0.20 m) + RANGE 0.051 .. 0.056
m3; 0.15 m 2.191725 m3 (17.53 bags, 2.41 m3 sand) HELD beside until the 0.15 m block module is stated. Freelancer:
no mortar row (T-367 s.6): RULE_DIFFERENCE, no numeric verdict. T-367 vs T-453: no defect in either; RULE_DIFFERENCE
of basis (contract area vs material base) and date (pre / post Q-75 answer): T-453 r2 governs.

## 6. Lessons row (proposed, ERS s.7)
| 2026-11-04 | Two merged ledgers gave black-block mortar 3.870113 vs 1.588929 m3 | a later table read an earlier
table's rate on a new basis (material base, post-answer module) without closing the earlier figure | one producer per
(line, material, kind); a reader keeps the producer's rate, a superseded ledger becomes BESIDE; reconcile in m3 per
wall to a named residual before wiring (every villa; T-506) | tests/t506_mortar_reconcile (0.15 released refused;
two producers refused; reader divergence refused) | PROPOSED |
