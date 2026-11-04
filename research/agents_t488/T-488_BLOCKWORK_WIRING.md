# T-488: blockwork wiring, ARCH_TAKEOFF_V3.0.55 (integration package, Gate B)

Worker 3, 2026-11-04, run session_01E6cPnc48aDb9BNiT3i9dRL. Stream S. Opt-in candidate only; the released default
V2.9 + route G is untouched. Built on the merged V3.0.54 (T-480, merge 1b66b719, which merged during this run: the
package was rebased on it before the run of record).

## 1. Physical element (ERS s.2.1)

A block wall is the masonry between its two faces from the STRUCTURAL top of the plate under it to the soffit of the
member over it (Q-60 A, Q-72), less every actual opening (Q-73). The soffit hangs from the structural top of the plate
ABOVE. A roof-only plate whose structural level is not printed has no structural top: the storey under it is not
established, and taking the architectural finished chain (+9.70 -> +13.90 = 4.20) silently uses the floor build-up
0.05 m for the roof build-up b_r (FINISHED_AS_STRUCTURAL, refused by the T-482 verdict).

| | Owner manual method | Drawing-derived method |
|---|---|---|
| Wall m2 | length x clear height (structural floor to the underside of the member over it) - openings | T-449 r3 register (BLOCKWORK_BASIS_RULES_V1): drawn pieces x printed soffit depths x declared storeys, 234 entries reproduced, 26 specified |
| Storey | floor to floor, structural | plate tops from the structural set: GF 0.95 -> 5.45 (4.50), 1F 5.45 -> 9.65 (4.20) DRAWING-CONFIRMED; 2F 9.65 -> 13.90 - b_r: HELD (D-39) |
| Conflict member | one reading | D-27: CB2 drawn 0.25 vs schedule 0.20: both readings carried as a range |

## 2. What the package does (engine/source/arch_v3055.py, rule R-T488-1)

- ROOF_DATUM: the 8 roof-storey walls (2F-W01 .. W08) leave their 6 released part lines in each of MAS.BLOCK,
  ARCH.WALL_PANEL, ARCH.WALL_VOLUME (18 lines): each part line becomes BLOCKED_RFI blank, its walls named with
  U - L x b_r; the two 2F parents list them. Carried = U - L x 0.05 asserted per wall (within 0.0005 m2, 3 dp prints).
- WIDTH_CONFLICT: GF-W22 leaves the GF t 0.15 DRAWING-CONFIRMED BLACK part (21.5261 -> 8.595 m2, GF-W19 stays) and is
  named on its parent as CONFLICT [12.9311, 12.9439] m2 (D-27); volume [1.939665, 1.941585] m3.
- DROP_UPPER: GF-W34 U 10.3982 -> 10.4121 (max over the D-27 readings; L 1.7231 unchanged, T-288 re-clip open).
- The V3.0.26 increments named outside (GF-W22 0.0128, GF-W34 0.0139 m2) are now inside the range / U: retired once
  (asserted equal to the condition's width), never named twice.
- PARAPET_RUN: STR.CONC.PARAPET records only (quantity and state unchanged): 1F roof NW-2 block alternative
  [0, 3.6107] -> [0, 3.1672] m2 (run read straight at roof level, T-324 C3; 3.1672 x (1.30 - 0.30)); annex NE-6x
  none -> [0, 0.25999] m2 (1.29995 x (0.50 - 0.30)); summaries 43.335453 -> 42.891953 and 5.77702 -> 6.03701 m2.
- Lintels (R-T487-1 (3)): unchanged. D-2F-01 / D-2F-03 hosts (2F-W03 / W08) are now held lines; their margins (1.25 /
  1.60 m vs D + 0.06 = 0.26 m) keep REQUIRED for any b_r below 0.99 m (P1 note: b_r < 0.30): no lintel decision moves.

## 3. Per wall group, before / after (m2; volume = m2 x t)

| Line (element) | Walls | Evidence | V3.0.54 | V3.0.55 |
|---|---|---|---|---|
| 2F t0.20 VERIFIED BLACK | W01 6.84 + W06 14.82 | VERIFIED | 21.66 | HELD: 6.93 - 1.80 b_r; 15.015 - 3.90 b_r |
| 2F t0.20 VERIFIED WHITE | W04 21.476 | VERIFIED | 21.476 | HELD: 21.7875 - 6.225 b_r |
| 2F t0.20 DC BLACK | W05 part 3.80 | DRAWING-CONFIRMED | 3.80 | HELD: 3.85 - 1.00 b_r |
| 2F t0.20 DC WHITE | W02 part 9.6915 + W07 part 6.225 | DRAWING-CONFIRMED | 15.9165 | HELD: 9.865 - 3.47 b_r; 6.36 - 2.70 b_r |
| 2F t0.15 OA BLACK | W08 9.64 | ASSUMED - OWNER-APPROVED | 9.64 | HELD: 9.79 - 3.00 b_r |
| 2F t0.15 OA WHITE | W03 part 25.885 | ASSUMED - OWNER-APPROVED | 25.885 | HELD: 26.255 - 7.40 b_r |
| GF t0.15 DC BLACK | W19 8.595 + W22 12.9311 | DRAWING-CONFIRMED | 21.5261 | 8.595 (W22 CONFLICT [12.9311, 12.9439] on parent) |
| **MAS.BLOCK released** | | | **579.1011** | **467.7925 (-111.3086, -19.22 %)** |

2F sets (T-482): VALUED 53.5225 - 14.925 b_r, PART 46.330 - 14.570 b_r; at the what-if b_r = 0.05: 52.776 + 45.6015
= 98.3775 m2 = the carried figure (residual 0.0000). Hand check (any wall): 2F-W01 = 1.80 x (4.25 - 0.40 - b_r) =
6.93 - 1.80 b_r; at 0.05: 6.84 = carried. ARCH.WALL_PANEL moves identically; ARCH.WALL_VOLUME 2F t0.20 12.5705 m3 and
t0.15 5.32875 m3 held, GF -1.939665 m3.

## 4. Diffs, downstream, regression

- vs V3.0.54: 32 lines CHANGED (21 part lines: 18 held, 3 reduced; 9 parents restated; 2 parapet records), 0 added,
  every other line byte-identical (asserted); totals move only in MAS.BLOCK, ARCH.WALL_PANEL, ARCH.WALL_VOLUME.
- vs released V2.9 + route G: the released run carries no per-wall MAS.BLOCK fill on this villa (its blockwork lines
  are the V3.0.15 held family); the V2.9 column of the ledger names each line's released state.
- Downstream: T-498 blockwork materials: the 2F walls' blocks, mortar and glue leave the purchase base until b_r
  (material side follows the contract side); lintel host faces of D-2F-01 / D-2F-03 sit on held lines. Plaster / paint
  on the 2F walls are measured by their own families (not moved here).
- Freelancer: no like-for-like (his roof-storey walls use 3.45 / 3.70 heights from his own datums); verdict UNRESOLVED
  on D-39 for 2F; GF-W22 RULE_DIFFERENCE (one end vs the D-27 range, 0.10 %).
- Registry: BOQ_FAMILY_MASTER_1.52.0 = 1.51.0 + T-480 PROMOTED (R-T485-1) + pending V3.0.55 + B9-01 / B10-12 text.

## 5. Open / findings

- F-T488-1: GF-W19 (DRAWING-CONFIRMED 8.595 m2 on the same part line) also carries a conflict increment 0.017 m2
  named outside, the same CONFLICT_ONE_END form as W22; no Checker-verified range exists, so it is NOT moved here
  (Lead / Checker: a T-482-type reading of its member).
- The Checker's T-482 verdict re-measured 3 of 4 conditions; W34 U 10.4121 and the W22 schedule end are named for its
  Gate B re-measure (owner 2026-10-23: every wall whose status class changes).
- b_r (D-39) holds 98.3775 m2 of 2F blockwork (U 99.8525 at b_r = 0).

Lessons row (proposed, ERS s.7): | 2026-11-04 | a storey under a roof-only plate carried the finished chain | the
architectural FFL chain is a storey | a storey is plate top to plate top; a roof-only plate with no printed structural
level holds every wall under it as U - L x b_r, and a released part line whose walls are all held is blank by name |
tests/t488_blockwork_wiring | T-488 |
