# T-205 Neck columns: both ends from the drawings; released 10.855 vs freelancer 8.805 m3 reconciled

Worker 1 (lane S), 2026-10-23, run session_016N9PyUZg3dm4kLuRmRLWPq. Development villa, not an accuracy claim. ERS s.2-4
and s.7 applied. No engine module, method version, route G, rule / knowledge file or released quantity changed. New:
`neck_ends_v1.py` (NECK_ENDS_V1, unwired, stdlib), `ALSENAN_NECK_INPUT.json` (values and DXF handles only, read this
run), `t205_alsenan_check.py` -> `summary.json`, `LEDGER_T205.csv` (one row per neck), tests `tests/t205_neck_ends/`
(19 pass: non-Alsenan hand fixture Villa N + development-villa checks).

## 1. The physical element (ERS s.2.1)

A neck is the part of a column below the ground floor: reinforced concrete of the column's FOUNDATION section (column
schedule, "FOUNDATION" band) standing on its footing and carrying the ground beams. Element: STR.CONC.NECK, storey
FOUNDATION, one per column mark drawn on the foundation plan. Its height is the distance between two STRUCTURAL datums:

- **Bottom = FOOTING_TOP** = formation + 0.05 screed + 0.02 membrane + 0.10 blinding + H (ST7757.pdf p.13 both typical
  footing details, underlay 0.07 DRAWING-CONFIRMED by T-206; H from the footing schedule). The footing line is billed at
  its full L x W x H, so the footing owns the neck / footing junction and the neck starts on its top (R-CONC-OWN-1
  pair "neck on footing", T-189 tests).
- **Top = GB_TOP.** The released ground-beam lines are billed NET of the column footprint ("column footprint split out;
  junction squares owned by one band", engine/source/generic_route.py:862, formula :929 "B x L - column - junction").
  By R-CONC-OWN-1 (precedence column > beam) the column / neck therefore owns the column footprint through the whole
  ground-beam depth: stopping the neck at the ground-beam SOFFIT would leave section x beam depth in no line (a GAP).
  If a later ground-beam basis bills through the column, the neck top moves to the soffit (the module does this,
  `gb_basis = THROUGH_COLUMN`). The GB top is printed only as a name: p.13 "Ground Beams for exterior walls", top =
  "Ground Floor slab level"; the interior typical sections draw no slab relation. The ground-floor STRUCTURAL slab top
  is printed nowhere (T-200, T-206: both sets, all sheets): it is FFL +1.00 minus an unprinted build-up b.
- **Never the FFL.** The FFL +1.00 is a finished level; using it as the neck top is FINISHED_AS_STRUCTURAL (refused by
  the module).
- The neck top must be the SAME datum as the bottom of the ground-floor column line. The released GF columns run from
  FFL +1.00 (profile rationale: "GF column height GF +1.00 to 1F +5.50 = 4.50"), so moving the neck top to the GB top
  without moving the GF column bottom would open a GAP of (GF column section x b); `stack_check` reports it. Physically
  the concrete between the slab top and the FFL is the GF column (its GF section, e.g. C 0.20 x 0.50), not the neck
  (0.30 x 0.50): the released convention bills that band at the neck section.

## 2. What was read (sheets searched)

Drive "Alsenan chalet project" / ST7757 dxf.dxf (sha256 9f9d1179..., = the route G input): FOUNDATION PLAN frame (title
at 144491, 29629): every column label (TEXT / MTEXT / block TEXT: 36) and every S-COL.BON outline (36), matched one to
one; every S-FOOTINGS outline and footing-block outline in the frame and each neck's containing footing; COLUMN & AXIS
PLAN (title 183110, 29576): the outlines (35; the one CN beside C9 / F9 not drawn, T-042) and the size texts, mapped by
the one translation that puts 34 / 36 outlines on each other (+38 724.4, 0); the column schedule (12 INSERT CGT rows
C .. C11, FOUNDATION band FOU.W / FOU.H) and the CN text row (T-075); the footing schedule (INSERT FT / FTB, 16 types,
DEPHT). Reused with citation (merged, Checker-verified source references): T-206 (underlay 0.07, formation limit, p.13
details), T-200 (no structural level printed in either set), T-204 (lift pit detail p.14: pit depth "as per lift
manufacturer"), T-042 / T-075 (CN neck-only, F10 / F open outline), T-189 (R-CONC-OWN-1). Freelancer: committed rows
RC / "walls + columns" rows 16-28. Released lines: M4 route G PROVISIONAL_REGISTER (28 neck lines, 10.8555 m3).

## 3. Inventory and the three methods side by side (m, m3)

| Mark | Drawn | Released lines | Printed section (schedule FOUNDATION) | Footings under them (H) | Released V2.9 m3 | Freelancer (his row) m3 |
|---|---|---|---|---|---|---|
| C | 5 | 4 (+1 HELD: F10 / F outline) | 0.30 x 0.50 | F x4 (0.30) | 1.320 | 5 x 0.30 x 0.50 x 1.50 = 1.125 |
| C1 | 1 (lift) | 1 | 0.30 x 0.50 vs plan text 20X50: CONFLICT | FF (0.55, pit raft) | 0.2925 | 0.225 |
| C2 | 4 (2 lift) | 4 | 0.30 x 0.50 (lift two: plan text 20X50, CONFLICT) | F2 x2 (0.35), FF x2 | 1.230 | 0.900 |
| C3 | 6 | 6 | 0.30 x 0.50 | F3 x2 (0.30), F15 (0.40), F12 (0.70), F14, F8 (0.50) | 1.845 | 5 x ... = 1.125 |
| C4 | 2 | 2 | 0.30 x 0.50 | F4 x2 (0.40) | 0.630 | 0.450 |
| C5 | 3 | 3 | 0.30 x 0.60 | F13 (0.50), F5 x2 (0.40) | 1.116 | 0.810 |
| C6 | 1 | 1 | 0.30 x 0.70 | F6 (0.50) | 0.420 | 0.315 |
| C7 | 1 | 1 | 0.30 x 0.80 | F12 (0.70) | 0.432 | 0.360 |
| C8 | 2 | 2 | 0.30 x 0.90 (one: plan text 30X80 + drawn 0.80: CONFLICT) | F14, F8 (0.50) | 1.080 | 0.810 |
| C9 | 2 (1 lift) | 2 | 0.30 x 1.00 (lift: plan text 25X100, CONFLICT) | FF (0.55), F9 (0.55) | 1.170 | 0.900 |
| C10 | 1 | 0 (HELD: F10 / F outline) | 0.30 x 0.70 | F10 / F conflict | HELD | 0.315 |
| C11 | 2 | 2 | 0.30 x 1.10 (plan text 30X110 x2, drawn 1.10) | F13, F11 (0.50) | 1.320 | 1 x **0.40** x 1.10 x 1.50 = 0.660 |
| CN | 6 | 0 (HELD: height) | 0.30 x 0.30 (text row) | FN x4 (0.30), F8 (0.50), F4 (0.40) | HELD | 6 x 0.135 = 0.810 |
| **Total** | **36** | **28** | released sum of sections 5.340 m2 | | **10.8555** | **34 necks, 8.805** |

| Method | Neck height h | Status |
|---|---|---|
| Released V2.9 + route G (convention) | h = 1.00 - (-1.50) - H = 2.50 - H: top at the FFL +1.00, footing underside at -1.50 | PROVISIONAL; top FINISHED_AS_STRUCTURAL; footing end implies a formation at -1.67 (= -1.50 - 0.17) |
| Freelancer | 1.50 flat for every mark | 1.50 is the number of p.9 note 1 ("excavation not less than 1.5 m below the plot level"): a formation LIMIT, not a neck length (notation before arithmetic) |
| Drawing-derived (this task) | **h = 2.33 - H - b + d**, b = FFL -> GF structural slab top build-up, d = depth of the formation below the printed -1.50 limit | **HELD on every neck**: b and d are printed nowhere (Q-21 C; T-200 / T-206). Per neck: section and H DRAWING-CONFIRMED |
| Owner manual method | none for neck heights (OWNER_QUESTIONS_ANSWERED searched: Q-21 = C, hold); Q-43's 0.10 floor finishing is a finish-height rule for plaster / paint, shown here only as a what-if (b = 0.10 -> -0.534 m3 on the 28), never a structural datum (T-206) | - |

WHAT_IF (information for the designer item, not a quantity): at b = d = 0 the 23 released necks with one printed section
give 8.1186 m3 (released 8.853: the released convention = d - b = 0.17 m on every neck, 0.17 x 4.32 m2 = 0.734 m3);
the conflicting C8 0.4392 .. 0.4941; the 6 CN 1.0692; the 4 lift necks have no form (their bottom is the lift-pit floor,
pit depth not printed); C10 / C none (footing conflict). Each 0.10 m of build-up b removes 0.534 m3 from the 28, each
0.10 m of formation below the limit adds 0.534 m3. The single / two-ground-beam detail switch (p.13, 2.5 m between GB top
and footing bottom) sits at 2.33 - b + d = 2.5, i.e. exactly at the released convention (d - b = 0.17): the released
datum also decides whether a lower ground-beam row exists (T-042 B3), another reason it cannot be a value.

## 4. Reconciliation of the 2.050 m3 (freelancer -> released, in units)

| Step | Cause | m3 |
|---|---|---|
| Freelancer | 34 necks x his section x 1.50 | 8.805 |
| Scope (engine HELD, he prices) | 6 CN 0.810 (height), C10 0.315 and the 5th C 0.225 (F10 / F open outline, T-042 A2) | -1.350 |
| Section | his C11 0.40 x 1.10; schedule FOU 30 x 110, plan text 30X110 twice, drawn 1100 x 300 | -0.165 |
| Count | he omits one C3 (6 drawn: labels 168F, 1681, 168E, 10CD, 10E5, 10A1) and one C11 (2 drawn: 10BF, block 1684), at his 1.50 | +0.720 |
| Height basis | released 2.50 - H vs his 1.50 on the 28 (sum A(1.00 - H)) | +2.8455 |
| Released | | **10.8555** (residual 0.000) |

The height step splits by physical cause against the drawing-derived reference (b = d = 0): released +0.17 m per neck
(its implied formation -1.67) = +0.908 m3 on 5.34 m2; freelancer 1.50 vs 2.33 - H = -1.938 m3. Neither end of either
figure is printed: both totals rest on unprinted heights.

## 5. Findings beyond the totals

1. **Lift-core necks (C1, C2, C2, C9 on FF):** the column plan prints 20X50 / 20X50 / 20X50 / 25X100 and the foundation
   plan draws them so, the schedule FOUNDATION band says 30 x 50 / 30 x 100: CONFLICT (0.10 vs 0.15, 0.25 vs 0.30 m2);
   they stand on the lift-pit raft whose depth is "as per lift manufacturer" (p.14, T-204). Released 1.4625 m3 takes
   the schedule section and the common -1.50 datum: wrong datum family. HELD (PIT_DEPTH_NOT_PRINTED + SECTION_CONFLICT).
2. **C8 at F14 (label 10E1, outline 10E0):** column plan prints 30X80 and draws 0.80; schedule 30 x 90: CONFLICT (as
   T-100 found on the slab plans), range 0.24 .. 0.27 m2; released took 0.27.
3. **Drafting notes, no quantity:** the C at F (outline 10B7) is drawn 0.30 x 0.40 and C4 at F4 (108D) 0.25 x 0.50 on
   the foundation plan, while the schedule and the column-plan text agree on 0.30 x 0.50: the printed size governs.
4. **Ground floor column / neck boundary:** released neck top and GF column bottom are both the FFL (no gap, no double
   in the released set) but on a finished datum; the drawing-derived boundary is the GB top. Moving one line without the
   other is a GAP / DOUBLE of section x b (lane I wiring note).

## 6. Verdict proposals (for the Checker)

- Neck total: **UNRESOLVED** (both ends unprinted; designer item T-042 B4: founding level, ground-beam top / slab
  build-up). Released 10.855 PROVISIONAL and freelancer 8.805 both rest on unprinted heights.
- C11 section: **ENGINE_RIGHT** (schedule + plan text x2 + drawn): freelancer 0.40 x 1.10 is a misread (-0.165 m3 at his
  height). Counts C3 6 / C11 2: **ENGINE_RIGHT** (36 labels = 36 outlines); freelancer omits 0.720 m3 at his height.
- CN / C10 / 5th C: engine HELD correctly; freelancer prices them on an unprinted height: **UNRESOLVED**.
- Lift necks and the C8 at F14: **UNRESOLVED** (printed conflicts + pit depth); the released lines should be HELD.
- No owner question: ERS 2.7 not met (unprinted design values and two conflicting printed sizes are designer items, not
  an owner decision). Designer list (Lead): founding level and GF structural slab top / floor build-up (T-042 B4);
  lift pit depth (T-204); C8 at F14 30X80 vs 30 x 90; lift columns 20X50 / 25X100 vs schedule FOUNDATION 30 x 50 / 30 x 100.

## 7. Rule and lessons row (proposed)

R-NECK-ENDS-1 (proposed; any villa; provenance T-205, R-CONC-OWN-1, UP-LEVEL-DATUM-001 proposed, Q-21 C): a neck runs
from the top of its footing (formation + printed underlay + blinding + H) to the datum where the column line above
starts; that datum is the ground-beam TOP when ground-beam lines are billed net of the column footprint and the soffit
when they are billed through it; both ends are structural datums with printed sources, the neck top and the column
bottom are one datum, and a finished level, a printed limit or another element's number is never a neck end; a printed
size that conflicts with another printed size is HELD as a range; a neck on a lift-pit raft takes the pit depth. Unprinted
-> HELD with the linear what-if, never a default and never 0. Adoption = a new rule version (lane I / Lead).

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-23 | Necks released 10.855 m3 to the FFL on a -1.50 underside; freelancer 8.805 m3 at a flat 1.50 m (the excavation-limit number); his C11 0.40 wide and one C3 / one C11 missing | Neither method defined the element's two structural ends or which line owns the neck / ground-beam junction; a finished level and a limit note were used as ends | R-NECK-ENDS-1: footing top -> column-line start (GB top for net-of-column ground beams); one datum with the column above; unprinted = HELD with the linear what-if (any villa) | tests/t205_neck_ends (normal: 3 necks, mixed H, m / mm / turned; adverse: FFL as top refused, missing formation HELD, formation above the limit, slab top unprinted, through-column basis, section conflict, pit raft, footing conflict, GAP / DOUBLE, reconciliation with not-drawn scope) | proposed |

## 8. For the Checker (re-measure from the drawings; 3 necks of different footing types + the conflicts)

1. C11 label 10BF -> outline 10BA 1100 x 300 inside F13 outline 1ADB (H 50, INSERT FTB 2A98): schedule CGT row C11
   FOU.W 30 / FOU.H 110; column plan text "30X110".
2. C3 label 10CD -> outline 10CC 300 x 500 inside F12 outline 1ABF (H 70, FTB 2A5E), with C7 (10C8) on the same footing.
3. C label (block 1682) -> outline 10B7 drawn 400 x 300 inside F block outline 166A (H 30, FT 1C79): schedule 30 x 50,
   column-plan outline 85B 300 x 500.
4. C8 label 10E1 -> outline 10E0 800 x 300 in F14 (1B1A): column-plan text "30X80" vs schedule FOU.H 90.
5. Lift: outlines 1099 / 1096 / 1093 (200 x 500), 1090 (250 x 1000) inside FF 1B2B; column-plan texts 20X50 x3, 25X100.
6. Freelancer rows RC "walls + columns" 16-28 (C11 row 26: 0.4 x 1.1 x 1.5 x 1).

## 9. Not done / uncertain

- Neck bars and neck formwork are not re-derived here (they follow the same two ends; the formwork faces at the
  ground-beam junction follow R-CONC-OWN-1 / T-163).
- Which ground beam frames each neck and its depth class is not needed while the ground-beam lines are net of the column
  (it is needed only for a through-column basis); not entered.
- The C11 / F11 label (block 1684) sits 2.0 m from its outline 10DD; the one-to-one match is by the global assignment and
  the F11 outline 1B07 containing 10DD (Checker to confirm).
- Wiring (HELD reason LEVEL_NOT_PRINTED on the 28 released neck lines, the stack check against the GF column line) is
  lane I work.
