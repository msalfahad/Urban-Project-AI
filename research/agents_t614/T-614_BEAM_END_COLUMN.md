# T-614 beam band beside a partial column (research, unwired; lane S)

Task: Checker F-C-P02-3 (T-180 P02 1F, 2026-11-07 22:57): 1F CB11's east run stops at the face of corner column 69D
across the whole 0.30 band while the column is only 0.20 deep: a 0.25 x 0.10 piece owned by nobody, ENGINE_WRONG
OMISSION +0.018750 m3. Census of every beam band x column on the GF / 1F / 2F roof-slab plans, with fix rows.
Also answers Checker F-C-P02-5 (GF CB8, 2026-11-08 00:58), which asked T-614 to take GF CB8 columns 2 / 3 / 4.
Candidate ARCH_TAKEOFF_V3.0.57 (= V3.0.58 for STR.CONC.BEAM). Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'
(sha256 9f9d1179..) read only in .work/private. Nothing released, no candidate line moved.

## Physical element

The part of a drawn beam band beside a column that does not fill the band width (column shallower across the band,
or off the band axis): plan = drawn band n column span - column outlines, depth = the beam's (full schedule depth to
the slab top, as the candidate bills). The column owns only its own footprint (UP-CONC-JOINT-001 1.0.0); the piece is
the beam's, up to the next drawn member face. R-T614-1 (PROPOSED, t614_rules.py) records it, clauses (a)-(f).

## Method (drawing-derived; t614_alsenan.py, reusing the T-610 member / line plan model unchanged)

- Every straight route G parent band x every support column within 50 mm (carried S-COL.HAT ANSI35 columns excluded:
  the beam runs under them, T-229). Position END / THROUGH / BESIDE_BAND; cover across the band; piece E.
- Billed plans per candidate line as T-610, plus the T-229 SUPPORT_CUT_BESIDE credit: at a cut between two pieces of
  one band the ledger run bills the WHOLE strip beside the column (research/agents_t229/beam_support.py classify_gap:
  beside = gap - support). All 9 credits of the ledger match the drawn strip x depth within -0.00035 .. +0.00125 m3;
  the neighbouring run's plan half past the cut is model only (GF CB1 L-9270e8b8: model residual -0.028125 =
  0.0375 m2 x 0.75 exactly) and is removed.
- (f) the strip beside the column (and an end gap) is MEASURED only inside the drawn band; outside it and billed by
  no line it is HELD. Where the band resumes collinear on the column's far side (same axis, same face offsets) the
  strip beside the whole column span is examined (the face is broken there).
- Ends: every drawn end of every parent band classified COLUMN / BEAM / OPEN (ARC rings listed): 0 unexamined.

## Results (out/T614_BEAM_END_CENSUS.json / .md)

| storey | parent bands | pairs | partial-cover columns | omission | HELD |
|---|---|---|---|---|---|
| GF | 53 | 64 | 9 | 0.00285 m2 / 0.002137 m3 (CB8 col 4) | 0.00454 m2, bound 0.003405 m3 (CB8 col 2) |
| 1F | 36 | 48 | 9 | 0.025 m2 / 0.018750 m3 (CB11 at 69D) | 0 (CB10 strips sit in its HELD line: 0.09 m2) |
| 2F | 12 | 14 | 0 | 0 | 0 |

Ends: GF 101 (COLUMN 44, BEAM 51, OPEN 1, ARC 5), 1F 68 (30 / 30 / 4 / 4), 2F 24 (9 / 9 / 6): unexamined 0.

### F-C-P02-3 (1F CB11): ENGINE_WRONG OMISSION reproduced exactly

Column C18 (= 69D) END_HI of CB11 (band 0.30, column 0.20 deep): piece 0.025 m2 in CB11's drawn band, billed by no
line (route G line L-780b8142, 3.30 x 0.30 x 0.75 = 0.7425, stops at the column face) -> +0.018750 m3. The oblique
end triangle of the hull (0.004167 m2) and the rest of the strip (0.020833 m2) lie in CB12's band and CB12 bills them.
The two mid columns (694, 69A) strips are billed by the T-229 credits (+0.0230 / +0.0303 vs 0.0225 / 0.0300).

### F-C-P02-5 (GF CB8): who is right, by column

His claim 0.12244 m2 x 0.75 - 0.0184 = 0.073430 m3 (col 2 0.055, col 3 0.025, col 4 0.035, gap 0.00744).
- Col 3 (C21): billed: the +0.0184 credit is AT col 3 (the cut BAND0040.1 -> .2 is there; col 2 lies between two
  parent bands with no T-229 cut) vs drawn 0.025 x 0.75 = 0.01875 (-0.00035). 'Col 3 +0.018750 VERIFIED' is not
  supported; his total is unchanged (he netted the same credit).
- Col 2 + gap (C13): 0.062435 m2 = 0.054816 inside B27's drawn band, billed by B27 (0.85, the deeper member; 0.000923
  of it also billed by CB8 = FR-T610-3, not counted again) + 0.004001 billed by CB8 + 0.00454 not in any drawn band
  and unbilled: HELD (FR-T614-H1, bound 0.003405 m3), CB8's inner face is not drawn there (a 1.045 m break beside the column).
- Col 4 (C25): 0.035036 m2 = 0.032154 inside B26's drawn band, billed by B26 (0.85) + 0.002882 in CB8's drawn band
  (0.00285 unbilled -> FR-T614-1 +0.002137 m3; 3.3e-05 in B26).
Proposal: ENGINE_WRONG_OMISSION +0.002137 m3; HELD 0.003405 m3 (bound); RULE_DIFFERENCE (by-mark attribution, no
BOQ total effect) for 0.086970 m2 billed in B27 / B26: his CB8 includes concrete the engine bills, at the deeper
depth, in the beams whose drawn bands hold it.

### Fix rows (owner: the beam, R-T614-1 (b))

- FR-T614-1 GF CB8 L-b6b4eb28 (P-C:BEAMS:GF:BAND0040.2) at col 4 END_HI: 0.00285 m2 x 0.75 = +0.002137 m3.
- FR-T614-2 1F CB11 L-780b8142 (P-C:BEAMS:1F:BAND0027.3) at 69D END_HI: 0.025 m2 x 0.75 = +0.018750 m3.
- FR-T614-H1 GF CB8 col 2: 0.00454 m2 HELD (bound 0.003405 m3), never 0.

### General rule found (every villa)

T-229 credits the strip beside a partial support only at a CUT between two pieces of one band; a band END at a partial
column has no cut, so the strip is lost whenever the route G rectangle stops at the column face (both findings are
END cases; all 9 THROUGH cases are credited). R-T614-1 closes it for ends and makes the broken-face case HELD.

## Named open items

- The ground-beam plan (SH08) is outside this census (task scope GF / 1F / 2F roof slabs).
- Column labels C<n> are census indices (sorted by centroid), mapped to the Checker's names in this note only.
- 1F CB10 strips (0.09 m2) stay in CB10's HELD line (width CONFLICT D-02).

## Lessons-register row (ERS s.7, PROPOSED)

| 2026-11-08 | strips beside partial columns: lost at band ENDS (1F CB11 +0.018750, GF CB8 +0.002137 m3), credited at
cuts; a strip in a deeper neighbour's drawn band reported as the shallow beam's omission (GF CB8 0.087 m2) | T-229
classified only gaps between pieces; the Checker read the strip from one band | at every beam-column contact the strip
beside the column belongs to the beam whose DRAWN band holds it (deeper band first); outside every drawn band it is
HELD; read the billing of every neighbouring line before naming an omission (every villa) | tests/t614_beam_end_column
normal + adverse | PROPOSED |

## r2 (Checker 2026-11-08T03:55Z, Gate A (e)): billing read from the line's own extent, never from a plan model

R-T614-1 (g) (PROPOSED): a LEDGER line bills its own route G rectangle (= printed length between the faces it names
x drawn width), a printed excess (mean-length oblique end, run over an unlabelled span) only through drawn parts whose
area matches it, named adds (T-229 END_SHORT_*, T-229 run) only through drawn parts whose volume matches the add
(best subset, 1 dm3 or 1 %), SUPPORT_CUT_BESIDE only at its cut. Every other drawn part beyond the rectangle is
MODEL_ONLY: not billed, whatever the T-610 whole-line model's MODEL_MATCHES says. Check of the basis: 28 of the 30
RELEASED ledger line values are rebuilt from (rectangle + placed excess) x depth + printed adds - printed deducts within
0.001 m3 (26 within 0.0001; GF CB8 BAND0039 +0.000638, GF B26 +0.000103); the two exceptions are named: GF CB4 BAND0021.1.r2 +0.01355 m3 (its mean-length excess 0.0271 m2 has no
drawn part outside other members' rectangles: it lies inside a neighbour's rectangle, a possible double billing for
the T-610 / T-229 owners) and GF B27 +0.00296 m3 (T-229 corner slivers).

Census on that basis (out/T614_BEAM_END_CENSUS.json, schema V2; 8 pairs whose r1 'billed' rested on the model):

| pair | r1 | r2 | m3 |
|---|---|---|---|
| GF CB8 col 2 east (C13) | ENGINE_RIGHT (model) | ENGINE_WRONG_OMISSION FR-T614-3, 0.003078 m2 (= Checker) | +0.002309 |
| GF B24 west end column (C23), cover 0.25 of 0.50 | ENGINE_RIGHT (model) | ENGINE_WRONG_OMISSION FR-T614-4, 0.20 x 0.25 = 0.050 m2 between the column face and B16's east face, inside B24's drawn band, outside its 3.55 m run | +0.037500 |
| 1F CB11 west end column (C3) | ENGINE_RIGHT (model) | ENGINE_WRONG_OMISSION FR-T614-5, 0.01174 x 0.10 = 0.001173 m2 (drawn 11.7 mm step: column face vs CB13 face) | +0.000880 |
| GF B26 at C25 / C27, GF B28 at C27 | ENGINE_RIGHT (model) | UNRESOLVED_ADD_UNPLACED: the named add (B26 run +0.1798, B28 END_SHORT_AT_CARRIED +0.0612) is placed by no drawn part set; bound = piece x depth 0.005245 / 0.125226 / 0.011971 | none |
| GF B27 at C8, 1F B19 at C15 | ENGINE_RIGHT (model) | UNRESOLVED_ADD_AMBIGUOUS (two part sets match the add): 0.00144 / 0.001064 | none |

Kept (cited, not redone): FR-T614-1 GF CB8 col 4 +0.002137 (Checker 0.002140), FR-T614-2 1F CB11 at 69D +0.018750.
Fix rows total +0.061576 m3 (5 rows). F-C-P02-5 by column: col 3 ENGINE_RIGHT (credit 0.0184 vs 0.01875, -0.00035);
col 2 east + col 4 ENGINE_WRONG; col 2 west HELD 0.00454 m2 (bound 0.003405); B27 part RULE_DIFFERENCE 0.054816 m2;
B26 part RULE_DIFFERENCE except 0.006171 m2 UNRESOLVED (B26's add unplaced). FR-T610-3 (0.000923 m2, -0.000692 m3 on
CB8) WITHDRAWN on this basis: CB8 BAND0040.1 does not bill the zone; B27 (deeper, owner) bills it once; FR-T610-1 / 2 / 4
unchanged.

Who is right: FR-T614-3 / -4 / -5 ENGINE_WRONG OMISSION (hand: drawn band faces, column outline, run printed length);
the rest UNRESOLVED for the T-229 add placement. Lessons row (PROPOSED, every villa): 'billing of a piece is read from
the line's own measured extent and named adds, never from a plan model inside a tolerance larger than the piece'
(tests/t614 adverse: test_adverse_model_match_never_proves_billing_of_a_smaller_piece).
