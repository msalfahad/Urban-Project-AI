# T-154 Pool-court soffit: 12.834 vs 14.704 m2 reconciled term by term; the 0.088 m2 traced; SX pieces classified

Worker 2, 2026-10-21. Lane A, gate 2, NO REPO CODE (research files only; nothing reads them; no quantity changes).
Rules: owner Q-38 A (the printed 6.57 m line bounds the curved glazing), Q-39 C, Q-67 A conditional (met), Q-68 C (finish
HELD, option A provisional only), UP-QTY-STATUS-001, WORKFLOW_CONTROLS sections 4-5. No controlling figure is selected
here (owner instruction): the two figures are explained; the Checker decides after Gate A.

Data (Drive "Alsenan chalet project", read in the session's private folder, never copied here): P7757_DXF_COMPRESSED.zip
(plan DXF, sha256 ab54dd55...), "ST7757 dxf.dxf" (sha256 9f9d1179...). Engine head 0dec24c. Reproduce:
`t154_alsenan_run.py <plan.dxf> <structural.dxf> <V2.9 run dir>` (restates T-121's census steps; local frame of T-127;
prints areas and term names only) and `t154_reconcile.py --check` (generic decomposition, synthetic fixture).

Local frame (T-127): X = 0 at the court face of the west pier line, Y = 0 at the court face of the south wall (metres).

## 1. The two figures, side by side

| | T-127 (MERGED 5315d48, Checker re-measured 12.8343) | T-121 verdict basis (verifier 2026-10-20 18:40) |
|---|---|---|
| Scope | the ceiling the court sees: face to face of the walls that bound the court, less the drawn opening | slab plate over outside air: route G slab faces of the GF roof-slab sheet outside the V2.9 GF facade outline |
| Method / version | hand, printed GF-plan dimensions (2000, 20/200, 750 + 3500 + 1150, 3500, 500, 657) | T-121 census (agents/task-T-121, not merged) on route G conventions V6 + ARCH_TAKEOFF_V2.9 FACADE.json; strips < 0.10 m removed by erosion / dilation 0.05 m |
| Gross | 16.5245 | 18.3927 (re-run here on the Drive DXFs: 13 columns agree on the sheet placement; = T-121 18.393) |
| Void | 3.6901 inside the B7 ring inner faces (ST arcs) | 3.689 (verifier, same ring; route G VOID face 4.3728 gave T-121's 14.020) |
| Net | **12.8343** | **14.7037** (quoted 14.704) |

## 2. Term-by-term re-add (all m2; signed so that hand + terms = CAD)

`t154_alsenan_run.py`, residual +0.00000 (tolerance 0.005):

| # | Term | m2 | Where (local frame) and drawing evidence | Evidence status |
|---|---|---|---|---|
| | hand gross (T-127 1.1) | 16.5245 | printed dimensions | VERIFIED (Checker 04:10) |
| E | + east court wall top, Y 0..5.40 | 1.0800 | X 1.80..2.00: wall 20 / 200 printed; the CAD set counts it because the V2.9 outline runs on the wall's OUTER face (X 2.000) | DRAWING-CONFIRMED |
| NE | + NE wall corner | 0.0400 | X 1.80..2.00, Y 5.40..5.60 (0.200 x 0.200 printed walls) | DRAWING-CONFIRMED |
| N | + north court wall top, X 0.50..1.80 | 0.2603 | Y 5.40..5.60 (200 printed); X 0..0.50 is the GF column (plan S-COL.BON 0.500 x 0.250), removed by the census; +0.0003 = the slab-sheet face at Y 5.6002 | DRAWING-CONFIRMED |
| W | + frame recess (SX-02) | 0.5609 | between the printed 657 line (r 2.250) and the V2.9 outline on the frame line (CAD 0.080 outside it, r 2.330), Y 0.45..5.40 incl. the frame ends | DRAWING-CONFIRMED (0.080 is CAD) |
| C | - **turned column face drawn on the slab sheet** | 0.0650 | **the first part of the 0.088.** X 0.30..0.50, Y 0..0.325 inside the court: the GF roof-slab sheet draws a hatched S-COL.BON column 0.200 x 0.900 (Y -0.575..0.325) next to the GF column 0.900 x 0.250, both inside one circled "T.C" mark; the 1F plan draws the same 0.200 x 0.900 outline (within 1 mm); the GF plan draws NO column there (only the 0.900 x 0.250 inside the south wall, Y -0.25..0). So it is the 1F column, turned against the GF one, standing ON the slab / beam B28: the court still sees the B28 soffit under it. The census keeps only PANEL / BEAM / JUNCTION_GAP / OPEN_BOUNDARY faces, so it dropped this COLUMN face. Hand right: 0.200 x 0.325 = 0.0650 is soffit. | DRAWING-CONFIRMED |
| R | - census clean-up rounding | 0.0078 | **the second part.** the 0.05 m erosion / dilation rounds every convex corner of the CAD set by (1 - pi/4) x 0.05^2 = 0.000537 m2 (0.0078 / 0.000537 = about 14-15 corners incl. the arc-to-line joints; the synthetic fixture proves the formula); a method artefact, no drawing meaning | METHOD ARTEFACT |
| - | - sliver at X 1.797..1.800, Y 0 | 0.0001 | face-line offset | METHOD ARTEFACT |
| | **= CAD gross** | **18.3927** | re-adds exactly | |
| V | void basis: 3.689 (verifier) vs 3.6901 | +0.0011 | rounding of the same ring area | VERIFIED |
| | **CAD net 18.3927 - 3.689 = 14.7037**; hand net 12.8343 + 1.0800 + 0.0400 + 0.2603 + 0.5609 - 0.0650 - 0.0078 - 0.0001 + 0.0011 = **14.7037** | | difference 1.8694 m2 fully named | |

### Where T-127's "0.088 untraced" went

T-127 rebuilt the CAD figure as 16.5245 + pocket 0.5607 + east 1.080 + north 0.316 = 18.4812, which is 0.0884 above the CAD
set 18.3927. Traced:

| Part of the 0.0884 | m2 | Reason |
|---|---|---|
| turned 1F column face over the court (term C) | 0.0650 | dropped by the census class filter; it IS soffit (hand right) |
| T-127's north strip west of the court face, X -0.08..0, Y 5.40..5.60 | 0.0160 | the V2.9 outline walks (0, 5.40) -> (-0.08, 5.40): that wall end lies INSIDE the house outline, so the CAD set never had it; T-127's table over-reached (wall end, never soffit in either method) |
| census clean-up rounding (term R) | 0.0078 | method artefact |
| CAD faces vs T-127 boxes (north face at 5.6002 -0.0003, recess polygonisation -0.0002, sliver +0.0001) | -0.0004 | drafting / arc polygonisation |
| **total** | **0.0884** | residual 0.0000 |

So no unknown area remains: the figures re-add within 0.0001 m2 (tolerance 0.005).

## 3. Which BOQ line each piece belongs to, and whether V2.9 / V3.0 already measure it

Re-run here on the Drive plan DXF: released ARCH_TAKEOFF_V2.9 (506 lines) and the opt-in V3.0 candidate with
`--v30-released` (579 lines). In BOTH: no room polygon overlaps the court (0.0000 m2), no FIN.CEILING / soffit line, no
GF opening in either court wall (ARCH_OPENINGS: 0 of the 60 openings lies in the court; the 27 ARCH.WINDOW_REVEAL lines
are elsewhere), the GF curved frame is not a curved opening (CURVED_OPENINGS: only the 1F window COP-001), GF FIN.EXT.FINISH
and ARCH.FACADE m2 are BLOCKED_RFI (no facade height); the V3.0 GF facade outline is byte-identical to V2.9. The V2.9
outline walks the frame line (arc 6.658 lm + frame ends 0.224 lm) and the court's south face (2.450 lm) inside the GF
facade run 98.887 lm (V3.0 range 98.887 .. 105.887). Therefore **nothing below is measured twice, and nothing below is
measured at all today**: every piece is missing scope, HELD (never 0).

| Piece | m2 | Belongs to (proposal for the Lead's element register) | Drawing evidence | V2.9 / V3.0 | Status |
|---|---|---|---|---|---|
| PL-03 court soffit | 12.8343 | ceilings: soffit over outside air (exterior); finish HELD under Q-68 C, option A provisional 12.834 plaster + 12.834 paint | T-127 (printed) | not measured | geometry VERIFIED; finish HELD; NOT RELEASED |
| SX-01 head of the 4.521 m opening in the east court wall | 0.9043 | openings: head soffit of a wall opening (exterior reveal family, with its two jambs 0.200 x height; height not printed -> HELD); not the court ceiling; under beam CB1 (ST: X 1.65..2.00) | GF plan dimension 4521.4 (Y 0.632..5.153), wall 20 / 200, opening ends drawn on layer D | no opening, no reveal line | DRAWING-CONFIRMED; HELD |
| SX-03 head of the 1.00 m opening in the north court wall | 0.2000 | openings: as SX-01; under beam B24 | width 1.000 CAD (between the GF column at X 0.50 and the 0.300 pier X 1.50..1.80; no printed 1000), wall 200 printed, head lines drawn (layer 2) | no opening, no reveal line | DRAWING-CONFIRMED (width CAD); HELD |
| SX-02 recess in front of the curved frame | 0.5609 | openings / glazing: outer head and reveal strip of the GF curved glazed frame (the 0.080 between the band face Q-38 A fixes and the frame line), with T-123's external-strip line; not ceiling | printed 657 line (Q-38 A), frame line CAD 0.080 outside it | not an opening; the facade run walks the frame line | DRAWING-CONFIRMED (0.080 CAD); HELD |
| wall tops under the slab: east piers 0.1757 (Y 0..0.632 and 5.153..5.400), north pier 0.0600 (X 1.50..1.80), NE corner 0.0400, face offset 0.0003 | 0.2760 | masonry / concrete interface: concealed, no finish line (masonry height runs to the slab underside) | printed walls 200, opening ends | none | DRAWING-CONFIRMED; no BOQ finish line |
| turned 1F column over B28 (term C) | 0.0650 | stays in PL-03 (the court sees B28's soffit); the column's concrete and bars belong to the 1F column line (T.C turned column) | ST S-COL.BON + T.C mark, 1F plan, GF plan (no column) | in PL-03 hand only | DRAWING-CONFIRMED |
| north wall end X -0.08..0 | 0.0160 | none (inside the house outline) | V2.9 outline vertices | none | n/a |

Cross-trade notes for the element register (owner proposals, not decided here):

1. **One surface, one line**: SX-01, SX-02, SX-03 belong to the opening rows (T-150 doors / windows by hand, T-123 strip),
   not to the ceiling row; PL-03 stays 12.834 m2 net. The CAD basis 14.704 carries all three plus 0.276 m2 of wall
   tops, so it must not be used for a ceiling line while any opening head is measured (double count 1.665 m2 + wall tops).
2. **T-150 scope**: the two court-wall openings (4.521 m east, 1.000 m north) are not V2.9 openings at all (their walls lie
   outside the GF facade outline); a door / window count from V2.9 misses them.
3. **Facade run**: the V2.9 / V3.0 GF run includes the curved frame arc 6.658 lm. GF by_role reports WINDOW 6.995 lm, so the
   arc is probably classed glazing; that is not attributed segment by segment here (UNKNOWN): if a facade m2 is ever
   released on the run, the Checker should confirm the arc is not plastered as wall.
4. **Census lesson** (any villa): a slab-sheet COLUMN face is not always a column under the slab; a column that starts on
   the slab (turned / planted, T.C / P.C marks) is drawn the same way. A soffit census must test each column face against
   the plan of the storey BELOW before removing it.

## 4. Second-drawing cross-checks done in this run

- Structural vs 1F plan: the 0.200 x 0.900 column outline agrees within 1 mm on both; GF plan: absent (one column
  0.900 x 0.250 inside the south wall only).
- Structural beams over the wall tops: CB1 inner face X 1.65 (east wall under it), B24 Y 5.10..5.60 (north wall under it),
  B28 X 0.25..0.50 (over the turned column face): consistent with T-127's beam strips.
- V2.9 and V3.0 outlines: identical rings around the court.

## 5. Freelancer

No change: his "ceiling above the swimming pool" 19.154 m2 vs PL-03 12.834 (+49.2 % his side), vs the CAD basis 14.704
(+30.3 %); ENGINE_RIGHT stays the Checker's verdict on T-127. Even CAD gross + every SX piece (18.393) is below 19.154.

## 6. Missing / for the Checker (Gate A)

- Re-measure: term C (0.200 x 0.325 at X 0.30..0.50, Y 0..0.325 on the ST GF roof-slab sheet and the 1F plan; GF plan
  has no column there) and SX-01 (4521.4 x 200).
- Open: heights of the two court-wall openings (jambs) not printed; SX-03 and SX-02 widths are CAD; finish of every piece
  HELD (D-24); beam side faces under PL-03 (T-110 depths) still not measured.
