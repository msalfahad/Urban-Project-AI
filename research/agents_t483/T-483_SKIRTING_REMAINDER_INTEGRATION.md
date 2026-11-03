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
| 1F living W13 / W25 | (no room skirting along a stair) | R-T481-3 stations: W13 inside MS2-L.W2, W25 inside MS2-LD.N (T-410 side table): stair-owned |
| 1F dressing | perimeter 6.90 less door 0.80 and arch 1.00 | walk by handle: W 0.8908 + 0.1092, E 1.800, N 1.650, S 0.500 + 0.150 = 5.100 lm; joinery-backed 2.800 lm beside, not deducted |

## 2. What the package does (V3.0.48, engine/source/arch_v3048.py)

R-T483-1 (module docstring): RELEASE (window base under an established sill joins the room line; its range line
NOT_APPLICABLE, carried once), CLOSE_RANGE (a held range whose every window is FLOOR_GLAZING or STAIR_OWNED closes
NOT_APPLICABLE only when the windows take its whole high; partial refused), WALK (a BLOCKED dry-cell line valued from
the walk: cover once, handles on faces, ids on openings, no jamb skirting, closes on the declared gross). Every binding
is checked against the candidate (state, gross, net, range) and refused if stale; this version adds no line; totals
move only in FIN.SKIRTING (asserted); every other V3.0.47 line byte-identical (asserted).

RESULTS_PLACEHOLDER

## 4. Engine vs freelancer (quantities only; T-106 / T-481 traces)

Freelancer FIN.SKIRTING 282.85 lm = 12 dry-room gross perimeters with no door deduction (T-106). RULE_DIFFERENCE
(UP-CER-003 doors / passages deducted; his perimeters also run along the stair shaft), never the target; the
percentage is not an accuracy figure.
- W11 / W12: ENGINE_RIGHT now (sill 0.70 above the +0.30 floor; hand 20.128 - 2.000 = 18.128 lm).
- W02 / W17: ENGINE_RIGHT now (floor glazing; hand W17 1.00 + 4.30 + 0.20 = 5.50 = FFL).
- 1F dressing: ENGINE_OMISSION closed (hand 6.90 - 0.80 - 1.00 = 5.10 lm; he has no dressing row).
- W13 / W25: RULE_DIFFERENCE vs his room perimeter (one face one owner: B7 along flights).

## 5. Held / not done (named)

- T483_1F_SHAFT: the 9.050 lm of 1F shaft faces (R-T481-3) are still inside the 1F living line's certain net
  41.435360 lm: the line carries no edge-level record by handle, so moving them to B7 needs that binding first (a
  separate package); until then the shaft faces may be counted both in B3-06 and in the B7 stair side lines (those are
  HELD, so no certain double count). W13 / W25's held range is closed here because R-T481-3 puts both windows inside
  stair stretches. CHECKER: R-T481-3 was not re-measured at T-481 Gate A; re-measure W13 / W25 stations.
- W02 pier D-53: no width drawn, nothing valued.
- Materials of the dressing skirting follow its floor finish (unchanged line material state).

## 6. Tests and regression

- tests/t483_skirting_remainder (K483 hand villa, not Alsenan): 31 module tests + 4 registry tests. Normal: release
  13.00 -> 16.00 (+3.00), range NA carried once, floor-glazing and stair-owned ranges closed whole (-4.20 / -2.10),
  walk 7.00 - 0.80 - 0.90 = 5.30 (mirror invariant), totals +8.30 certain / -9.30 held high, outside lines
  byte-identical, files. Adverse: sill at floor released, sill in mm, unread sill, partial listing, stale binding,
  floor glazing with a raised sill, stair-owned without owner, partial close, close of a valued line, walk gap, face
  without handle, opening without id, joinery as boundary, short cover, gross mismatch, jamb skirting, mm side, walk of
  a valued line, no skirted face, one line twice, applied twice, wrong project, figure on a closed range.

## 7. Lesson (ERS s.7 row proposed)

| 2026-11-03 | the T-422 narrowing refused a narrowing that takes a whole range ('re-read the line'), so a range held whole by
windows later decided NOT_SKIRTED had no closing path | a range-only operation was written for the partial case |
a decided window either joins its room line (skirted) or closes its range whole (not skirted); partial and whole are
two named actions, each refused in the other's case | tests/t483_skirting_remainder test_partial_close_refused |
T-483 |
