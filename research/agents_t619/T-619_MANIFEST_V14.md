# T-619 WIRING MANIFEST V14 + OVERLAY DRY RUN on ARCH_TAKEOFF_V3.0.58

Worker 3 (lane I, non-candidate), 2026-11-08. Not an integration package: nothing is wired; no candidate, released
(V2.9 + route G), rule, knowledge or registry file is touched; no drawing read. Every figure comes from the committed,
Checker-merged outputs of T-608 (3c3aa2f8), T-610 (14cf2579), T-614 r2 (a7f1f3af), T-616 (17559e1b) and the V13
manifest (T-611), all sha256-pinned, plus the Checkers' verdict lines. Files: `manifest_v14.py` (R-T619-1),
`out/WIRING_MANIFEST_V14.json`, `tests/t619_manifest_v14/`. Rebuild: `python3 -I research/agents_t619/manifest_v14.py`
(`--check`).

## 1. Physical elements

- Lift landing door (GF OP-011, 1F OP-007, 2F OP-002): a framed opening in the shaft wall, not a passage (T-608, Checker
  own read of the 4 panel lines and the shaft cross on all 3 storeys). The landing-door assembly (frame, leaves, sill) is
  omitted from the candidate; who supplies it is printed nowhere.
- Beam crossing zone: the concrete common to two drawn beam bands, billed once by the deeper band (R-T610-1).
- Beam end piece: the drawn band beyond a narrower column at a run end, owned by the beam (R-T614-1).

## 2. Rows (before = V13 overlay state)

| Fix row | Line | Before | After | Evidence |
|---|---|---|---|---|
| FR-T608-1 | ARCH.PASSAGE GF OP-011 / 1F OP-007 / 2F OP-002 | RELEASED 1 pcs each | EXCLUDED | DRAWING-CONFIRMED |
| FR-T608-2 | NEW DOOR.LIFT_LANDING x 3 (same elements) | no line | HELD blank, count 1 beside, trade HELD | HELD |
| FR-T610-1 | B1 L-39779d6e (GF) | 0.151391 | 0.146096 (-0.005295, VERIFIED component) | PARTIALLY VERIFIED |
| FR-T610-1 | B27 L-3dddf990 (GF) | 4.1918 | 4.203052 (+0.011252, range low end) | PARTIALLY VERIFIED |
| FR-T610-1 | NEW companion on B27 element `#FR-T610-1:RANGE` | no line | HELD 0 .. 0.001295 | PARTIALLY VERIFIED |
| FR-T610-2 | B27 L-3dddf990 (chained) / CB8 L-7c1a1da8 | 4.203052 / 0.716937 | 4.206189 / 0.714169 | PARTIALLY VERIFIED (worker-measured) |
| FR-T610-4 | 1F CB12 L-076a6d9e / B6 L-651a3d19 | 1.079463 / 0.552773 | 1.088838 / 0.546523 | PARTIALLY VERIFIED (worker-measured) |
| FR-T614-1 | GF CB8 L-b6b4eb28 (col C25) | 1.42875 | 1.430887 | PARTIALLY VERIFIED (piece Checker AGREE) |
| FR-T614-2 | 1F CB11 L-780b8142 (col C18) | 0.7425 | 0.76125 | PARTIALLY VERIFIED (piece Checker AGREE) |
| FR-T614-3 | GF CB8 L-bd16e692 (col C13 east) | 1.310964 | 1.313273 | PARTIALLY VERIFIED (piece re-measured) |
| FR-T614-4 | GF B24 L-007ee149 (col C23) | 1.426197 | 1.463697 | PARTIALLY VERIFIED (piece re-measured) |
| FR-T614-5 | 1F CB11 L-9696bbb4 (col C3) | 1.539652 | 1.540532 | PARTIALLY VERIFIED (piece re-measured) |
| FR-T616-1 | LINTEL:P-GF-01 L-d887eecf | HELD blank | TEXT_ONLY cause 'HEAD_UNDER_BEAM' | HELD |

Withdrawn, 0 rows: FR-T610-3 (T-614 r2: CB8 BAND0040.1 bills no part of the B27 x CB8 zone; Checker AGREE).
Listed, 0 rows: T-612 (FR-T612-1 statement restate), T-617 (FR-T617-1 for the plaster wiring, 0.000 m2 here).
Listed HELD, not wired: FR-T614-H1 GF CB8 col 2 west 0.00454 m2, bound 0 .. 0.003405 m3 (the source names no owning
line; never placed on a guessed line, never 0). Open, not a fix row: GF CB4 BAND0021.1.r2 +0.01355 m3 possible double
billing (T-614, for the T-610 / T-229 owners); 1F CB10 crossing zone HELD with its line (T-610).

## 3. The range rule (R-T619-1 (c))

The Checker bounds the B27 component +0.011252 .. +0.012547 m3 (zone 0.014761 m2 x 0.85 m = 0.012547; B27 may already
bill its 0.001524 m2 tip, 0.001295 m3). The index has no released range, so the line is SET at the low end and a
companion HELD line on the same element carries 0 .. 0.001295: the B10 total reads as a range. The code refuses a range
with high <= low, a ranged SET at any other point, and a ranged row without its companion. B27's second step (FR-T610-2)
chains on the first inside the same package (one Gate B unit per line, R1).

## 4. Overlay

V2 .. V13 rebuilt (5,125 lines; every V13 row and the V13 FIN.SKIRTING totals = the committed V13), then the four V14
packages (19 ops): **5,129 lines (+3 landing doors, +1 range companion), 0 STALE, 0 two-package lines, 0 unexplained
conflicts; every line V14 does not write is identical to the V13 overlay.** One host conflict (1F BM-1F-023: CB11 runs
.1 and .2) is EXPLAINED by a ruling built from T-614's ledger extents (run .2 bills only its own 0.795 m2 rectangle).
The one flagged row is T-580's own NO_BEFORE (T-498). Totals move on exactly three keys. Stair edge census: 89 edges,
0 doubles / 0 orphans.

## 5. Acceptance figures (hand)

- ARCH.PASSAGE: 9 - 3 = **6 pcs** released (excluded 2 -> 5). DOOR.LIFT_LANDING: 3 HELD blank.
- B10 STR.CONC.BEAM released: 66.321054 + 0.009451 (T-610: 0.005957 + 0.000369 + 0.003125) + 0.061576 (T-614:
  0.002137 + 0.018750 + 0.002309 + 0.037500 + 0.000880) = **66.392081 .. 66.393376 m3** (+0.071027 .. +0.072322,
  +0.107 %); HELD 27 -> 28 lines, bounds 8.372829 .. 13.77951 -> 8.372829 .. 13.780805 (the companion only).
- FIN.SKIRTING: **198.558592 lm** unchanged from V13.
- Freelancer beams 66.093875 m3 (scorecard V10): the gap widens from +0.227179 to +0.298206 .. +0.299501 m3 on physical
  causes (crossing zones billed once at the deeper depth; band pieces beyond narrow columns); agreement is not the test.

## 6. Findings

- F-T619-1: the B10 total stays a range (width 0.001295 m3) until the B27 tip attribution is re-measured.
- F-T619-2: FR-T614-H1 needs its owning line named (lane S) before it can enter.

## 7. Lesson proposal (ERS s.7)

"A component the Checker carries as a range enters the line index as the low end plus a companion HELD 0 .. width line
on the same element, never as a point; a later merged verdict that withdraws a fix row is honoured by id with 0 rows"
(any villa on the line-index scheme; T-619; tests/t619_manifest_v14).
