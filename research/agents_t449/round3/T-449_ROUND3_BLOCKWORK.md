# T-449 round 3 (BLOCKWORK): A1 correction register

Candidate of record: ARCH_TAKEOFF_V3.0.44 (inputs as `research/agents_t422/v3044_run.py`). Nothing is wired: no
candidate line and no released (V2.9 + route G) line moves.

## Files
- `engine/source/blockwork_basis_rules_v1.py` (BLOCKWORK_BASIS_RULES_V1, UNWIRED_PRODUCER, stdlib, no engine import):
  R-MAS-PIECE-HEIGHT-1 (owner Q-60 A), R-MAS-OPENING-DEDUCT-1 (Q-73, Q-55 C), R-MAS-WALL-NET-1, R-MAS-DROP-1
  (R-T288-1), R-MAS-PANEL-SAME-1, R-MAS-VOLUME-1, R-MAS-PARAPET-BLOCK-ALT-1.
- `research/agents_t449/round3/t449_blockwork_register.py` + `out/CORRECTION_REGISTER_BLOCKWORK_T449.{json,csv}`.
- `research/agents_t449/round3/DEVELOPMENT-VILLA-T131.blockwork_facts.json` (URBAN_PROJECT_CONFIG_V1): storey heights
  GF 4.50 / 1F 4.20 / 2F 4.20 m (DRAWING, section chain), door fallback 2.20 m (OWNER_DECISION Q-55 C); affected lines =
  exactly the lines the register uses each fact for. NOT declared: the GF annex storey (Q-54 B: HOLD).
- `tests/t449_round3_blockwork/` (synthetic VILLA-SYNTH-05 hand fixture + register checks).

## Census (42 builders: V3.0.2, V3.0.3, V3.0.5 .. V3.0.44)
REACHES: V3.0.26 (per-wall fill, 228 entries), V3.0.23 (parapet block alternatives, 25 runs), V3.0.35 (fence block
lines, 5), V3.0.19 (opening-trace masonry states, 2). 16 builders name masonry in text only; the rest none.

## Result: 260 entries = 234 A-REPRODUCED + 26 A-SPECIFIED + 0 B + 0 C
- V3.0.26 MAS.BLOCK: 76 walls. 37 walls with a figure reproduced (carried 499.3040 m2 vs rule 499.3007 m2; max residual
  0.0039 m2 = 1F-W00, the Checker's own value 12.935 vs the drawn pieces 12.9311, named); 28 HELD walls reproduced HELD
  (annex storey undeclared, depth not printed, nothing drawn over, size-less note member, undeductible opening, no
  drawn piece); 3 of 6 drop walls reproduced as U - L x d. WALL_PANEL and WALL_VOLUME follow their wall (m2 / m2 x t).
  Complete lines (4 of 7) reproduce their declared determinate / part figures within 0.001 %.
- 8 walls A-SPECIFIED (x 3 items = 24): bay caps 0.572 and 1F-W25 1.490 (cap reader pending), above-lintel panel
  P-GF-05 2.640 (head-level reader pending), GF-W01 (v4 sliver 0.0026 m under B26), GF-W22 / GF-W34 (junction-close
  range), GF-W16 / GF-W20 (drop length L after the v4 re-cut / junction close).
- V3.0.23: 23 / 25 runs reproduced [0, centreline x (h - 0.30)]; NW-2 and NE-6x A-SPECIFIED (findings 3, 4).
- V3.0.35 fence (5) and V3.0.19 trace (2) reproduced.

## Independent check (Drive 'Alsenan chalet project' / ST7757.pdf p.10 'Schedule of Simple Beams', read on the sheet)
Every simple-beam depth the reader uses (19 marks B1 .. B25 incl. B15 D 120) equals the printed D column: 0 mismatches.
B26 prints D 85, so the GF-W01 v4 sliver height 3.65 = 4.50 - 0.85 is the rule's (rule 62.1636 vs carried 62.164,
+0.0004 m2 = the Checker's print). Continuous-beam depths (CB marks) come from the plan labels the merged ledgers read;
not re-read here. Hand: 1F-W03 = 2.70 x (4.20 - 0.40) + 1.20 x (4.20 - 0.75) = 14.400 m2 = carried (lengths from the
merged register, not re-measured).

## Findings (no quantity changed here)
1. F-T449-R3-1: the blockwork uses the 2F storey 4.20 m (section chain) while round 1 holds 13 2F columns at an
   undeclared roof datum (D-39 / Q-54 B): one datum basis for both trades is owed (Checker / Lead).
2. F-T449-R3-2: GF-W22 (DRAWING-CONFIRMED) carries 12.9311 m2, the LOW end of a junction-close range 12.9311 .. 12.9439
   (+0.0128 m2, 0.10 %) with no increment named; GF-W34 drop carries U = 10.3982, the low end of 10.3982 .. 10.4121, but
   U is an upper bound (its high end is the bound).
3. F-T449-R3-3: parapet 1F NW-2 block alternative carries [0, 3.6107] m2 from the superseded arc centreline (T-311);
   at the current straight centreline 3.1672 m (T-324 C3) the rule gives [0, 3.1672] (-0.4435 m2, beside only).
4. F-T449-R3-4: parapet annex NE-6x has no block alternative booked; the rule gives [0, 0.25999] m2 (beside only).

## Lessons row (proposed, ERS s.7)
A wall's masonry is reproduced from its drawn pieces, the printed soffit depth of each and the declared storey height,
never from its stored m2; an opening that cannot be deducted outside the held pieces holds the whole wall, never a part
(provenance T-449 r3).
