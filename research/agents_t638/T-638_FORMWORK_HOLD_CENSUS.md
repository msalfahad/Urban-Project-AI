# T-638 B10-13 formwork: the 370 HELD-blank lines to a quantity or a named cause (research, unwired)

Worker 1, lane S, 2026-11-08. Files: `t638_rules.py` (R-T638-1, every villa: classes, guards, generic contact
calculator), `t638_alsenan.py` (builder, repository files only, sha256-pinned), `out/FORMWORK_HOLD_CENSUS_T638.json` /
`.md` (one row per line, every face with its own cause), `tests/t638/` (13 tests). No engine, rule / knowledge
version, registry, frozen or candidate file changed; nothing wired or released. No drawing read this run: every figure
is a merged, Checker-passed ledger value of the same formwork method (formwork r4 / r5, T-264 / T-308 / T-332, bound to
the line ids by T-474) checked by hand against the printed section (T-119 r2).

## 1. Physical element and method (ERS s.2.1)

A formwork piece is the temporary mould face of a cast face NOT cast against earth, blinding, masonry or an earlier
pour; it sits beside the line carrying that member's concrete. Method of the 244 released lines (read only): beam
soffit b x L + sides L x (D - t) by the drawing-face walk; column shaft perimeter x (interval - D_ctrl) + joint strip;
slab soffit net panel; slab edge band. Contact m2 only (no panels, reuse or rate).

## 2. Result (scope = T-630 per_line, B10-13 STR.FORMWORK m2 HELD with no figure and no bound: 370 = the row)

| Class | Lines | What happens |
|---|---|---|
| A_FIX | 54 | fix rows FR-T638-1 .. 54, **+33.127058 m2 released (CALCULATED)**; 4 HELD companions |
| B_HELD | 203 | blank; the HELD concrete element is named: own / member line BLOCKED_RFI 37, BOUNDED_EXPOSURE 41 (+10 CALCULATED faces DEPENDENT_HELD), ranged 21, boundary wall 1, parapet RC 24, lift pit / tie 4, neck aggregate 1, split member 1; or, on RELEASED concrete, the adjacent element deciding contact (1F RING_MIX, STAIR, HELD_EDGE, UNMATCHED, held member; faces 0 .. x) 63 |
| C_HELD | 113 | blank; the missing drawn item is named: OQ-10 contact below N.G. 100, unmarked band pieces 4, dome method / drum 4, pool back on the boundary line (Q-28) 2, boundary pads count, sunken drop D-41, one section CONFLICT |

Fix rows by element: column shafts 4 rows 27.002 m2 (COL-GF-01 5.626, -02 6.375, -03 5.626, -09 9.375); split-member
faces 50 rows 6.125058 m2 (beam sides 18 / 4.952626, soffits 20 / 0.631766, slab-edge bands 12 / 0.540666).

- Column shafts: T-119 r2 FRAMING_MEMBER_HELD_D_SETTLED = the held framing member does not change D_ctrl; column
  concrete is RELEASED (full interval, T-394 / T-576). By hand: C4 0.25 x 0.50: 1.50 x (4.50 - 0.75) = 5.625 (method
  5.626, +0.001 drawn-outline perimeter, named); C5 0.25 x 0.60: 1.70 x 3.75 = 6.375; C9 0.25 x 1.00: 2.50 x 3.75 =
  9.375. Joint faces stay HELD as the companion (the held member's width / presence decides the strip).
  NOT freed: COL-GF-05 and COL-GF-22 (a stair element frames at the column; the method's 'no framing face below the
  controlling soffit' covers beams only), and every D_OPEN shaft (unlabelled member depth not printed, D-26: AT_MOST).
- Split-member faces: CALCULATED walk faces (R-FW-P2-5 REST pieces, CB1 void face) held only because the member lies in
  2-3 candidate concrete lines with no length per line; every one of those lines is RELEASED, so the per-line split
  changes no B10-13 total. Released on their own member-level lines; per-line attribution by T-149 spans stays a
  binding task, not a quantity. Faces 0 .. x beside a held neighbour are not freed (low end 0).

B10-13 effect for the trial BOQ: released 1,027.977403 -> **1,061.104461 m2** (+3.22 %), lines 244 -> 298 of 614.
No freelancer formwork row exists (FREELANCER_NO_ROW): no %.

## 3. (D) T-632 slab-edge strip: HELD, missing item named

0.20 x 4.325 = 0.865 m2 per storey (GF BAND0031, 1F BAND0013), Checker-verified as a slab-edge outline, not an upstand.
No section prints it (A-A / B-B draw the beam band only) and no thickness tag sits on it, so whether it is the slab
plate continued (T 16) or a drip / finish line is not printed. Concrete, soffit and edge forms stay HELD, never 0.
Beside, reading 'slab T 16 continues' only (not chosen): 0.1384 m3, soffit 0.865 m2, straight edge 0.692 m2 per storey
(corner arc and stair-side run not measured). Missing: a section through the strip or a thickness tag on it (designer
item, ERS s.2.7 not met: no owner question).

## 4. For the Lead / Checker

- Checker re-measure picks: column COL-GF-09 L-7f76e6db296d84785185 shaft 9.375 (C9 0.25 x 1.00, interval +0.95 ->
  +5.45, D_ctrl 0.75 from B13 / B16 / B17 schedule depths); beam BM-1F-023 REST side L-3123abfcbd78a3bf4c28 1.763786
  (1F roof slab sheet walk face 1F-103); slab edge: the strip (D) section A-A content (does the section draw slabs at
  all?) decides whether its thickness can be read.
- OQ-10 (100 C lines + 32 on held concrete) and the B1 excavation working space (OQ-13) hang on ONE missing drawn item:
  the working space / excavation method. One designer answer settles both trades.
- Fix rows go to the lane I manifest (V17 or next); the companion lines carry the T-332 ledger lo / hi as recorded.

## 5. Lesson (ERS s.7, proposed)

| date | discrepancy | cause | rule | regression | status |
|---|---|---|---|---|---|
| 2026-11-08 | 50 measured formwork faces (6.125 m2) and 4 settled column shafts (27.002 m2) stayed HELD blank on RELEASED concrete | a binding hold (member in several lines) and a framing-member hold that does not change D_ctrl were carried as quantity holds | a face measured by the released method is freed when every line it could bind to is RELEASED and its own hold does not change its geometry; an adjacent stair / held neighbour blocks it (R-T638-1, PROJECT-INDEPENDENT) | tests/t638 (V638 normal; HELD volume, blinding face, mm, missing depth refused; COL-GF-05 / -22 stay held) | PROPOSED |
