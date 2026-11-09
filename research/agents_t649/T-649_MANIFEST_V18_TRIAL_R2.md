# T-649 WIRING MANIFEST V18 + overlay dry run + TRIAL BOQ r2 (R-T649-1 / R-T649-2; lane I, non-candidate)

Base: V17 (T-641) rebuilt in memory on the V3.0.58 copy (5,151 lines) and compared with the committed V17 rows and
totals. V18 adds 39 ops (35 quantity, 4 TEXT_ONLY): 29 in 5 new packages + 10 steps chained in T-498 (R1). Nothing is wired
to the candidate; V2.9 + route G and V3.0.58 are untouched. Outputs: `out/WIRING_MANIFEST_V18.json`,
`out/TRIAL_BOQ_R2_T649.{json,md}`, `out/TRIAL_BOQ_R2_T649_LINES.csv` (rebuilt by `tests/t649_manifest_v18` with
`URBAN_T649_WRITE=1`; the tests assert committed == rebuild).

## Fix rows (each cites its merged verdict)

| package | rows | before -> after | evidence |
|---|---|---|---|
| STRIP_COL353 (T-642) | FR-T642-2 L-efd3f780 | HELD 0.04 .. 0.12 -> RELEASED 0.050 (0.20 x 0.50 x B4 0.50) + new HELD 0 .. 0.025 (x (0.75 - 0.50)) | VERIFIED / HELD |
| | FR-T642-4 L-5bc1baae | 0.282743 m3 unchanged: depth B7 stamp (TEXT_ONLY) | DRAWING-CONFIRMED |
| CHECKER_DOWNGRADES (T-643) | DGP-T643-fdb3ed37 / 943b0c58 / ca59159e / 196fcf58 | COL-2F-50/51/53/54 main bars 4 x 39.822 kg RELEASED -> HELD blank (D-39) | HELD |
| STAIR_FINISH_HOLD_RELEASE (T-645) | 16 | 10 HELD blank -> RELEASED (risers 6.836036 m2, flights 13.36392 lm); 6 -> HELD bounded | DRAWING-CONFIRMED / ASSUMED — OWNER-APPROVED / HELD |
| ROOF_SCREED_AT_LEAST (T-646) | 3 | HELD blank -> AT_LEAST 2.512672 / 3.324832 / 4.791492 m3, high OPEN | HELD |
| T-498 (chained) + LINTEL_RC_BOUNDS (T-650) | 10 SET + 3 TEXT | 2 NEW bounds, 8 HELD BY NAME bounds (pair D-GF-11 + D-GF-12 0.06 .. 0.07914 on one line); D-1F-07 / L-GF-01 HELD blank 'Checker re-measure pending' | HELD |

Stair face pairs (riser beside tread m2, flight pitch line beside step lm on one flight) are 14 EXPLAINED conflicts by
ruling; one code twice on a flight is refused as a double count.

## Re-adds by hand

- STR.REBAR kg released: 9,787.750205 - 4 x 39.822 = 9,628.462205 = 9,216.017760 (T-643 base after the downgrades) +
  412.444445 (T-639 overlay); HELD blank 795 -> 799; -1.63 % on V17.
- FIN.MARBLE.RISER m2: 1.96 + 0.667 + 1.886 + 1.8975 + 1.633929 + 0.751607 = 8.796036; HELD bounded 3.310533 .. 3.7904.
- FIN.STAIR.FLIGHT lm: 1.041933 + 3.775064 + 3.782209 + 3.403367 + 1.361347 = 13.36392; HELD 6.527061 .. OPEN.
- STR.CONC.BEAM m3: released +0.050; HELD high 0.12 -> 0.025 on the strip.
- FIN.ROOF.SCREED m3: AT_LEAST 10.628996 .. OPEN (3 of 6 lines; 3 stay HELD blank with cause).
- STR.CONC.LINTEL m3 HELD: low 0.502 -> 0.955692 (= T-650 summary 0.991692 - D-1F-07 withheld 0.036), high known part
  0.74642 -> 1.379112 (+ D-2F-01 OPEN); 44 HELD blank with cause.
- Overlay 5,152 lines; 0 STALE; 0 two-package lines; 0 unexplained conflicts; stair census 89 edges, 0 doubles /
  0 orphans; every other line byte-equal to V17.

## Lead ruling F-T645-1 (MS1-L tread / step)

The tread 3.105 m2 (9 x 0.30 x 1.15) and step 10.35 lm (9 x 1.15) count 9 goings from the architectural GF plan edges
DC .. 486, the very edges C-ST-4 / RFI-A04 disputes against ST p.4 45A .. 25E (11 goings); T-645 holds the same flight's
pitch line on 9 .. 11 goings. The count is not independent of the held riser count, so each line takes a downgrade
PROPOSAL (DGP-T649-2543430910268708: 3.105 .. 3.795 m2; DGP-T649-a20e51752f360854: 10.35 .. 12.65 lm). Not applied: a
worker proposal; the Checker validates or refuses (owner 2026-10-24 23:57).

## Trial BOQ r2 (master 1.57.0)

HELD with cause 2,314 / 2,750 (T-636) -> 2,351 / 2,744; F-T636-1 436 -> 393; released lines 1,559 -> 1,566; no unit
grand is a total; three-column re-add exact at every level. Statement-only: T-633 D-GF-06 RULE_DIFFERENCE ->
ENGINE_RIGHT (statement V12). Reader correction F-T525-1: B8-06 'open' minus its stale first sentence.

## Listed, not wired

- FR-T642-1 (CB12) / FR-T642-3 (GF B11): ENGINE_RIGHT no-change restates.
- 40 T-646 lines and 42 T-650 lines: HELD blank with their census cause (trial BOQ cause sources).
- Refused by name: T-647 (TODO r2), T-648 (READY).

## Uncertain

- W18 lintel carries the T-650 HELD-BY-NAME range 0.034692 .. 0.034692 (equal ends) as stated; still HELD, a designer
  connection item.
- A-1F-01 bound is CHECKER-PARTIAL (width engine-read); named in its cause.
- T-498 package keeps its pre-existing NO_BEFORE row (unchanged since V17).

Lessons row proposed (s.7): a released count is never more certain than the drawn edges it counts; where a HELD
conflict disputes those edges, every line counting them is HELD or proposed for downgrade together (every villa).
