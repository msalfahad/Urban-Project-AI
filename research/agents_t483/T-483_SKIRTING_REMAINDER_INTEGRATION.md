# T-483: skirting remainder integration, ARCH_TAKEOFF_V3.0.48 (development villa; method every villa)

Worker 1 (stream F, lane I), 2026-11-03. Gate B integration package on the candidate of record V3.0.47 (T-443, merge
c814c55d, candidate e86a53a8). ERS applied: s.2.1 element, s.2.2 evidence (owner manual method and drawing method side
by side), s.2.4 closure in units, s.4 rule + tests, s.7 lesson. No client data, drawing text or coordinate in this
file: handles, line ids, states and quantities only. Source: the merged T-481 census (a8609a7a; Verifier
2026-11-03T05:44Z own re-measure AGREE on W17, W11, W02 and the 1F dressing).

## 1. Physical elements and methods (ERS s.2.1 / s.2.2)

A room skirting is a strip at the foot of a finished dry wall / column face at the room's floor level. Under a window
it exists only where wall stands below the opening (masonry base above the FFL > 0.02 m); at floor glazing there is no
wall base; along a flight or landing the face belongs to the stair skirting (B7-07 / B7-08), one face one owner.

| Item | Owner manual method | Drawing-derived method (merged T-481) |
|---|---|---|
| GF-01 W11 / W12 | perimeter less doors; a window deducted only where no wall continues under it | section B-B: frame base +1.00 over the printed +0.30 floor -> sill 0.70 m (views 0.55 .. 0.70, all > 0.02: skirted); W12 bound to W11 (identical outline); hand 20.128 - 2 x 1.000 = 18.128 lm |
| GF open plan W02 | floor glazing deducted | section B-B: frame base on the +1.00 floor line: sill 0.00, no wall base |
| 1F-11 W17 | floor glazing deducted | NW elevation printed chain 1.00 + 4.30 + 0.20 = 5.50 = 1F FFL: sill 0.00 |
| 1F living W13 / W25 | (no room skirting along a stair) | R-T481-3 stations: W13 inside MS2-L.W2, W25 inside MS2-LD.N (T-410 side table): stair-owned; NOT applied here (B7 has no candidate line) |
| 1F dressing | perimeter 6.90 less door 0.80 and arch 1.00 | walk by handle: W 0.8908 + 0.1092, E 1.800, N 1.650, S 0.500 + 0.150 = 5.100 lm; joinery-backed 2.800 lm beside, not deducted |

## 2. What the package does (V3.0.48, engine/source/arch_v3048.py)

R-T483-1 (module docstring): RELEASE (window base under an established sill joins the room line; its range line
NOT_APPLICABLE, carried once), CLOSE_RANGE (a held range whose every window is FLOOR_GLAZING or STAIR_OWNED closes
NOT_APPLICABLE only when the windows take its whole high; partial refused), WALK (a BLOCKED dry-cell line valued from
the walk: cover once, handles on faces, ids on openings, no jamb skirting, closes on the declared gross). Every binding
is checked against the candidate (state, gross, net, range) and refused if stale; this version adds no line; totals
move only in FIN.SKIRTING (asserted); every other V3.0.47 line byte-identical (asserted).

## 3. Development-villa run (own, this session)

Chain: research/agents_t167/v304_run.py, then research/agents_t483/v3048_run.py on the Drive copies (P7757.dxf
ab54dd55, "ST7757 dxf.dxf" 9f9d1179): V3_0_47_BOQ_LINES.json = **e86a53a8** (the candidate of record reproduced,
asserted); the hub reached V3.0.48 and every binding loaded (first run stopped in the V3.0.44 check on a superseded
NARROW record of the living range, fixed: a version's check skips lines a later version changes, regression test).
Second hub run after the fix and the W13 / W25 decision (22:07-22:20 UTC, own): V3_0_47 e86a53a8 -> V3_0_48
**f1fbc045** through the hub (DONE 0), identical to research/agents_t483/v3048_apply.py on that e86a53a8 file ->
V3_0_48_BOQ_LINES.json **f1fbc045**
(summary_t483.json; pinned by tests/t483_skirting_remainder/test_alsenan_pins.py). 4874 lines, 5 changed, 0 added,
4869 byte-identical; totals move only in FIN.SKIRTING lm.

| Line | Before (V3.0.47) | After (V3.0.48) | Status |
|---|---|---|---|
| L-d3241491 GF-01 (W11 + W12) | 14.218037 lm | **18.127877** lm (gross 20.127876 - doors 2.000) | DRAWING-CONFIRMED (Checker AGREE W11) |
| L-83672015 GF-01 range | 0 .. 3.909839 | NOT_APPLICABLE_WITH_EVIDENCE, carried by L-d3241491 | carried once |
| L-e7dcdc69 GF open plan range (W02) | 0 .. 6.331578 | NOT_APPLICABLE_WITH_EVIDENCE (floor glazing) | Checker AGREE |
| L-fbba0e0d 1F-11 range (W17) | 0 .. 3.289498 | NOT_APPLICABLE_WITH_EVIDENCE (floor glazing) | Checker AGREE |
| L-4a85470b 1F dressing | BLOCKED_RFI blank | **5.100** lm SOURCE_DERIVED (6.900 - D315 0.800 - arch 1.000) | VERIFIED (Checker by handle) |
| L-079bc766 1F living range (W13 / W25) | 0 .. 2.200 | unchanged, HELD | see s.5 |

FIN.SKIRTING: certain **203.368752 -> 212.378592 lm (+9.009840, +4.43 %)**; held high 15.730915 -> **2.200**; blocked
lines 5 -> 4, range lines 4 -> 1. The row's 189.78 figure assumed the 9.050 lm shaft transfer, not done (s.5).

### Finding for the Lead (row vs candidate)

The row asks to bind R-T481-3 at integration (9.050 lm of shaft faces and W13 / W25 out of B3-06 into B7). In the
candidate B7-07 / B7-08 have NO line (BOQ_FAMILY_MASTER 1.44.0: NOT_IN_CANDIDATE). Moving the faces now would drop
11.250 lm (9.050 certain + 2.200 held) from the BOQ: a silent omission. Kept where they are, named WAITING
T483_1F_SHAFT; the module supports STAIR_OWNED closes (tested) for when the stair skirting lines exist.

## 4. Engine vs freelancer (quantities only; T-106 / T-481 traces)

Freelancer FIN.SKIRTING 282.85 lm = 12 dry-room gross perimeters with no door deduction (T-106). RULE_DIFFERENCE
(UP-CER-003 doors / passages deducted; his perimeters also run along the stair shaft), never the target; the
percentage is not an accuracy figure.
- W11 / W12: ENGINE_RIGHT now (sill 0.70 above the +0.30 floor; hand 20.128 - 2.000 = 18.128 lm).
- W02 / W17: ENGINE_RIGHT now (floor glazing; hand W17 1.00 + 4.30 + 0.20 = 5.50 = FFL).
- 1F dressing: ENGINE_OMISSION closed (hand 6.90 - 0.80 - 1.00 = 5.10 lm; he has no dressing row).
- W13 / W25 and the 9.050 lm shaft faces: unchanged here (HELD / in the living net); RULE_DIFFERENCE vs his room
  perimeter once B7 carries them (one face one owner).

## 5. Held / not done (named)

- T483_1F_SHAFT: the 9.050 lm of 1F shaft faces (R-T481-3) stay inside the 1F living line's certain net 41.435360
  lm and its W13 / W25 range 0 .. 2.200 stays HELD: the owner lines B7-07 / B7-08 are not in the candidate, so no
  double count today (the faces are counted once, in B3-06) and no transfer is possible without dropping them.
  R-T481-3 was not re-measured at T-481 Gate A.
- W02 pier D-53: no width drawn, nothing valued.
- Materials of the dressing skirting follow its floor finish (unchanged line material state).

## 6. Tests and regression

- tests/t483_skirting_remainder (K483 hand villa, not Alsenan): 32 module tests + 3 Alsenan pins + 4 registry tests. Normal: release
  13.00 -> 16.00 (+3.00), range NA carried once, floor-glazing and stair-owned ranges closed whole (-4.20 / -2.10),
  walk 7.00 - 0.80 - 0.90 = 5.30 (mirror invariant), totals +8.30 certain / -9.30 held high, outside lines
  byte-identical, files, a range carrying an earlier NARROW record closes (Alsenan regression). Adverse: sill at floor released, sill in mm, unread sill, partial listing, stale binding,
  floor glazing with a raised sill, stair-owned without owner, partial close, close of a valued line, walk gap, face
  without handle, opening without id, joinery as boundary, short cover, gross mismatch, jamb skirting, mm side, walk of
  a valued line, no skirted face, one line twice, applied twice, wrong project, figure on a closed range.

## 7. Lesson (ERS s.7 row proposed)

| 2026-11-03 | the T-422 narrowing refused a narrowing that takes a whole range ('re-read the line'), so a range held whole by
windows later decided NOT_SKIRTED had no closing path | a range-only operation was written for the partial case |
a decided window either joins its room line (skirted) or closes its range whole (not skirted); partial and whole are
two named actions, each refused in the other's case | tests/t483_skirting_remainder test_partial_close_refused |
T-483 |

## 8. Validation (this run)

- L1 / L2: tests/t483_skirting_remainder 39 pass (32 module, 3 pins, 4 registry).
- L3 (impact of tools/urban_boq_m9.py, HIGH): every test folder importing the hub directly + t443 / t419 / t478 / t479 /
  t485 / t459 / t422 / t481 / t471 / t469 on 5676d3d9 + inputs-only changes: 1 failure,
  `tests/t485_registry_promotion::test_a_merged_package_never_stays_pending_in_the_newest_registry` reports 'T-443':
  the same test fails on the working head e8ee22f0 (T-443 merged c814c55d, not promoted out of pending_packages in
  1.44.0; 1.45.0 copies the list as the builder rule requires). Pre-existing, not this package: a registry promotion
  (lane I) clears it.
- Freeze 0 differing; codemap check stale none; BOQ_FAMILY_MASTER 1.45.0 equals its builder, FMC.check problems [];
  RULES_MANIFEST drift []. t459 candidate binding rebuilt (adds arch_v3048.py: [], no lap token).
- L4: see the board handoff (started on 39255dea; result there).
