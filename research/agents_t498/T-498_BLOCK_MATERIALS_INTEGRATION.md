# T-498 blockwork MATERIALS wiring: integration package ARCH_TAKEOFF_V3.0.57 (stream S; method every villa)

Worker 3, 2026-11-04 (claim 21:00 UTC). Gate B integration package on the candidate of record ARCH_TAKEOFF_V3.0.56
(T-508, merge 40ab9061; 4e25c54f). Opt-in candidate only; the released default V2.9 + route G is untouched; nothing
released. No drawing, workbook, client name or coordinate in this folder.

## 1. Physical element (ERS s.2.1)

What is BOUGHT and LAID to build the masonry the MAS.BLOCK lines measure, kept apart from the contract area:
black (cement) block units, the 1:4 bed + head joint mortar between them, the thin-bed glue between white AAC units,
and the AAC units. Theoretical (installed) quantities only; breakage / waste / procurement rounding are HELD (no sourced
value; owner: waste separate). The RC lintels the printed LINTEL SCHEDULE casts inside a panel are concrete (B9-02,
T-487 lines), never laid block: their faces leave the material base (R-T453-5, owner Q-73).

| | owner manual method | drawing-derived method (this package) |
|---|---|---|
| black units | net wall m2 x 12.5 (40 x 20, Q-75 / 2026-11-02) | candidate MAS.BLOCK net (drawn pieces x clear height - openings) - REQUIRED lintel faces (w + 0.80) x D, x 12.5; 0.20 m only (0.15 m module not stated: HELD) |
| black mortar | 1:4, 8 bags + 1.1 m3 sand per m3 (Q-78) | material base x 0.07375 t m3/m2 (T-367 0.39 x 0.19 unit, 10 mm joints, owner-provisional) -> PROVISIONAL; bags / sand beside |
| AAC glue | net m2 x 3.5 (0.15) / 4.5 (0.20) kg (owner 2026-11-02) | material base x the same; RANGE where a HELD lintel may occupy the panel; bags once per purchasing group (census), never per line |
| AAC units | (no company rule) | HELD: face not selected (62.5 x 25 / 60 x 20 beside) |

## 2. Rule R-T498-1 (engine/source/arch_v3057.py)

(1) material base = contract net - every REQUIRED lintel face named in the inputs, each bound to a VALUED
STR.CONC.LINTEL line of the same candidate; a HELD / FLAGGED face is a named range 0 .. face bound to a BLANK lintel
line (BOUNDED_EXPOSURE); an unbounded face holds the material; (2) one producer per (masonry line, material): this
version produces units / mortar / glue (T-453 r2 basis, T-506 verdict); T-367 is beside only; a base already carrying a
material code is refused; (3) a held masonry line gives blank material lines by name (colour split: its two
materials; colour not split: all four), never 0; (4) every figure recomputed in the engine from the line and the
rulebook records and asserted equal to the inputs' expected figure (the merged T-453 r2 machinery on V3.0.56);
(5) millimetre faces, typed rates, a face on a held line, one lintel on two lines, faces above the net refused.
Rates arrive as COMPANY_RULEBOOK_V1 records (method, version, digest, OWNER_CONFIRMED) in the inputs: the rulebook is
an UNWIRED_PRODUCER (T-212 P2) and is never imported by the candidate.

## 3. Inputs (research/agents_t498/t498_inputs.py, every file pinned)

The merged T-453 r2 machinery (`build_from`, unchanged) on the V3.0.55 line index (its MAS.BLOCK / STR.CONC.LINTEL
lines are V3.0.56's: T-508 moved skirting only, asserted line by line by v3057_apply.py), with the T-488 walls carried
HELD (2F-W01 .. W08 roof datum D-39, GF-W22 width CONFLICT D-27). T-453's reconciliation closes against every released
V3.0.56 line (residual 0.0000 m2 on all 13). The T-367 row of the GF 0.15 DC BLACK line (21.5261 -> 8.595 m2 by T-488)
is restated at its per-m2 rate for the BESIDE figure only (the line's mortar is HELD: 0.15 m module).

## 4. Before / after (development villa)

Base: earlier T-453 r2 figures were on V3.0.45; on V3.0.56 (out/T498_LEDGER_DIFF.json: 7 material rows change, 45
unchanged; every change is a 2F line T-488 held on D-39):

| material | T-453 r2 (V3.0.45) | V3.0.57 lines (on V3.0.56) | change, cause |
|---|---|---|---|
| black 0.20 units | 1,346.55 pcs VERIFIED (107.724 m2) + RANGE 43.25 .. 47.50 (2F-W05) | **1,075.80 pcs** (86.064 m2: GF 62.164 -> 777.05, 1F 23.9 -> 298.75), MEASURED | -270.75 pcs (-20.11 %) = 2F-W01 6.84 + W06 14.82 = 21.66 m2 x 12.5 now HELD (D-39); 2F-W05 range -> HELD |
| black 0.20 mortar | 1.588929 m3 PROVISIONAL + RANGE 0.051 .. 0.056 | **1.269444 m3** PROVISIONAL (GF 0.916919, 1F 0.352525); 10.155552 bags, 1.396388 m3 sand beside | -0.319485 m3 (-20.11 %) = 21.66 x 0.01475; range -> HELD |
| AAC glue VERIFIED | 116.703 kg | **20.061 kg** (GF 0.20 W 4.458 m2) | -96.642 kg = 2F-W04 21.476 x 4.5 HELD |
| AAC glue PROVISIONAL | 112.8725 kg | **23.535 kg** (GF 0.20 OA W 5.23 m2) | -89.3375 kg = 2F-W03 25.885 x 3.5 HELD |
| AAC glue RANGE | 907.2045 .. 932.9445 kg (4 lines) | **842.06025 .. 861.32025 kg** (3 lines: 1F VW, 1F DCW, GF DCW) | -65.14425 .. -71.62425 = 2F DC WHITE 15.9165 m2 (W02 / W07) HELD |
| 0.15 black units / mortar | HELD (module) | HELD blank by name, T-367 figure beside | unchanged |
| AAC units | HELD | HELD blank, 6.4 / 8.33 per m2 beside | unchanged |
| held masonry lines | HELD | blank material lines by name | never 0 |

Hand checks: GF black 62.164 x 12.5 = 777.05 pcs; 62.164 x 0.01475 = 0.916919 m3 x 8 = 7.335352 bags; 1F 23.9 x 12.5 =
298.75; GF white 4.458 x 4.5 = 20.061 kg; GF OA white 0.20 5.59 - 0.36 (D-GF-06 face) = 5.23 x 4.5 = 23.535 kg.

## 5. Lintel pieces

The 16 REQUIRED / 44 blank STR.CONC.LINTEL lines (T-487) ARE the lintel pieces (cast in situ per the printed schedule,
1 piece each): no lintel line is added here (no double count). Each REQUIRED face that leaves a material base is bound
to its lintel line id in the material record; lintels on hosts T-488 held deduct nothing (34 faces on held hosts listed
in the inputs). F-C-T487-1 lintel bars stay HELD on B9-02.

## 6. Missing / uncertain

0.15 m black module (owner data item 2026-11-02); AAC face; breakage / waste (no source); the 2F roof datum b_r (D-39)
holds 8 walls' materials; GF-W22 CONFLICT (D-27); 10 mm joint owner-provisional; cross-trade cement / sand total
(T-511). Freelancer: no material rows comparable by line (T-367 s.6): RULE_DIFFERENCE, no numeric verdict.

Lessons row (proposed, ERS s.7): "a material line set produced from a merged ledger is re-run on the CURRENT candidate's
lines before wiring, and every change is explained by a named upstream package (here: the T-488 roof-datum walls),
never carried from the ledger's own base (every villa; T-498)".
