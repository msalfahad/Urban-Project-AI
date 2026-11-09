# T-569 WIRING MANIFEST V8 on ARCH_TAKEOFF_V3.0.58

Worker 3 (lane I, non-candidate, backlog-permitted), 2026-11-06, engine base 540bc99c. Not an integration package:
nothing is wired; no candidate, released (V2.9 + route G), rule, knowledge or registry file is touched. Files:
`manifest_v8.py` (builder; V7 pinned by sha256 72d2714c), `WIRING_MANIFEST_V8.json`, `tests/t569_wiring_manifest_v8/`
(18 tests). Rebuild: `python3 -I research/agents_t569/manifest_v8.py` (`--check`). No drawing read: inputs are the
committed line index (LINE_INDEX_V3_0_57 + the 5 T-507 lines) and merged outputs (T-561, T-567, T-564 V7).

## 1. Coverage (R-T549-1)

Range (V7 base 33a5833f, V8 base 540bc99c], first-parent: 6 merges, all covered. Wiring sources: T-564 (F-C-T564-1),
T-567 (R-T567-6), T-568 (F-C-T568-1), T-560 (rebar ENGINE_OMISSION). NO_WIRING: T-565 (earthworks to cause, NO_ROW),
T-570 (statement adapters; its F-C-T570-1 restatement rides RETURN_PAINT_FACES).

## 2. Rows (expected after; every other line byte-identical)

| Row | Physical element | Before | Expected after | Evidence status |
|---|---|---|---|---|
| RETURN_PAINT_FACES (T-561, register PLASTERED RETURN FACE, R-T569-1) | painted part of each plastered return face | no FIN.PAINT return line | 26 FIN.PAINT rows on the 26 valued face ids, HELD blank, bound beside 0 .. the face's plaster m2 (sum 23.070 = T-561 count and sum) + 4 rows HELD by name on the 4 HELD plaster returns (1 with the plaster's own bound 0 .. 1.20, 3 none); FIN.PAINT released 217.2081 unchanged | HELD (frame-covered depth not printed) |
| FLOOR_CLASS_A08 (F-C-T564-1) | finished floor of the unlabelled 1F space (our 'dressing') | V7: FINISH_HELD 2.970, class 'unlabelled' | same line and 2.970 m2; class FIN.FLOOR.PORCELAIN (A08 ESTIMATED) from neighbour 1F-R0E919A's floor line L-c044aecc; ADH / TILE bindings stay HELD blank | area DRAWING-CONFIRMED; class ESTIMATED, NOT VERIFIED |
| PIER_RETURNS_EXT (T-567 R-T567-6) | SW pier return faces, 1F NW-5 | no row | ledger of FIN.EXT.FINISH 1F L-8bb83e16 (stays HELD blank, T-314): storey 0.536522 x 4.20 = 2.2533924 m2 + parapet 0.0536522 .. 0.6974786 HELD; no internal line takes them | storey DRAWING-CONFIRMED, parapet HELD |
| W17_Q76A (F-C-T568-1) | curved 1F window over the pool | HELD L-0392d374 9.870 .. 11.515 (W17 alone) | HELD line retires; 1F settled L-ba28ba2d 23.285 -> 33.155 m2 (+3.29 x 3.00); W17 reveals stay HELD | ASSUMED - OWNER-APPROVED (Q-76 A, Q-39 C) |
| REBAR_OMISSION (T-560) | bars of the dome shells, dome rings, lift-pit walls | no STR.REBAR line | 6 STR.REBAR rows HELD blank, one per live concrete line (DOME-A / DOME-B / DOME-3 shells, two rings, lift-pit walls); the 2 EXCLUDED scope domes get none | HELD (no bar detail read) |

Cross-trade: no FIN.PLASTER, FIN.SKIRTING, MAS.* or valued STR.REBAR line moves; pairing check after the paint rows
(each plastered return has exactly one paint row, HELD).

## 3. Findings

- F-T569-1: the 30 plastered return lines are 26 valued faces (23.070 m2) + 4 HELD by name; V7 listed them as one.
- F-T569-2: RFI-A08 text names the bed room beside the space as 4.20 x 4.00; the arch A-1F-01 (T-292, room 1F-10) and
  T-553 give the 3.80 x 4.30 room 1F-R0E919A. Both 1F bed rooms are PORCELAIN on a DRY bed: the A08 class is the same
  either way (Lead: correct the RFI text; no quantity effect).
- F-T569-3: W17 Q-76 A (+9.870 m2) and the dome / lift-pit rebar lines had no wiring row before V8.

Effect for the statements: floor tile 387.094 m2 valued + 2.970 ESTIMATED beside vs 409.58 (-5.49 % valued); return
paint HELD <= 23.07 m2 (no longer ENGINE_WRONG once the rows exist, T-570); 1F windows +9.870 m2 settled.

## 4. Lesson proposal (ERS s.7)

"One face, two layers: a plastered dry face (return, nib, pier side) carries its paint row on the same face id; until
the covered depth is printed the paint is HELD, bounded by the plaster of that face, and the pairing is checked by rule"
(scope: any villa on the engine's id scheme; provenance T-561 / T-570 / T-569; test tests/t569_wiring_manifest_v8).
