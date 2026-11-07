# T-610 beam band overlap census (research, unwired; lane S)

Task: Checker F-C-P03-2 (T-180 P03 GF, 16:57): "B27 face 325 from column 35C crosses B1; overlap 0.014761 m2 billed in
B27 AND B1 (ENGINE_WRONG -0.005295 m3 at GF B1)"; census every beam-beam band intersection on the GF / 1F / 2F roof-slab
plans. Candidate ARCH_TAKEOFF_V3.0.57 (= V3.0.58 for STR.CONC.BEAM). Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'
(sha256 9f9d1179..), read only in .work/private. Nothing released, no candidate line moved.

## Physical element

The concrete common to two beams hanging from one slab where their DRAWN bands cross or touch (net of every column
outline: the column owns its footprint, UP-CONC-JOINT-001 1.0.0). Over that plan zone the concrete exists to the DEEPER
beam's soffit (both beams run from the slab top); the 3-D intersection (zone x shallower depth) is the part at risk of
double billing. R-T610-1 (PROPOSED, t610_rules.py) records this.

## Method (drawing-derived; t610_alsenan.py)

- Drawn band per route G band: the strip between its two drawn face lines; past the station where both faces are drawn
  a face that runs on by at most one band width is the oblique drawn end (one face stops at a column / member face, the
  other at its corner); a longer run is a line shared with another member. Split between the band's pieces at the
  mid point of each column cut. Columns: route G column boxes + slab-plan boxes + the slab arrangement's COLUMN faces;
  an outline carrying the S-COL.HAT ANSI35 hatch is a member that STARTS on the slab (T-229; ST p.15) and is not
  deducted from the beam under it.
- Billed plan per candidate line: a route G line = its rectangle minus the junction squares route G deducts from it
  (member_detection.beam_quantities: the square goes to the longer band); a ledger run (T-229 / T-252) = its pieces'
  billed plans plus the drawn band beyond them up to every other member's plan (the T-229 `_beyond` construction).
  16 of 30 ledger lines reproduce to <= 0.01 m3 (B27 included); the others carry other T-229 / T-395 terms (joint
  deductions, gaps) and are listed with their residual.
- Per zone: engine = sum of each line's billed plan in the zone x its depth; physical = zone x deeper depth;
  engine - physical = DOUBLE (both lines, x shallower depth) + DEPTH (billed only at the shallower depth) + OMISSION
  (in neither), asserted to re-add.

## Results (out/T610_BEAM_OVERLAP_CENSUS.json / .md)

| storey | zones | verdicts | engine - physical m3 |
|---|---|---|---|
| GF | 5 | RIGHT 2, UNDER 2, DOUBLE 1 | -0.005634 (DOUBLE +0.000692, DEPTH -0.006326) |
| 1F | 3 | RIGHT 1, UNDER 1, HELD 1 (CB10 schedule / drawn width CONFLICT) | -0.003125 |
| 2F | 1 | RIGHT 1 | 0.000000 |

No plan is billed by two lines outside a drawn common block on any storey (route G squares are deducted once; ledger
runs stop at other members' plans).

### F-C-P03-2 (who is right)

Reproduced: zone 0.014761 m2 (triangle in B1's strip east of column 35C and west of B27 face 325), B1 (line
L-39779d6e) bills 0.013237 m2 of it x 0.40 = 0.005295 m3. But the B27 ledger run (L-3dddf990, 4.1918 m3) does NOT bill
it: T-229 measures B27 to B1's band (its `_beyond` region stops at other members' plans); the plan model reproduces
4.1918, and including the triangle would give 4.1918 + 0.013237 x 0.85 = 4.2031 m3. B27 bills only the 0.001524 m2 tip
of its route G rectangle (which B1 deducts). So the block is billed ONCE, not twice; it is billed at B1's 0.40 depth
where B27 (0.85) is drawn through to the column corner: engine 0.006590 vs physical 0.012547 m3 = UNDER -0.005957 m3.
Verdict: the Checker's B1 figure is RIGHT (B1 should stop at B27's face, 0.151391 -> 0.146096); "billed in B27 AND B1"
is NOT supported on the candidate; the net effect is an omission. With the deeper owner: B1 -0.005295, B27 +0.011252
(4.1918 -> 4.203052) m3.

### Fix rows (for the next wiring manifest; deeper member owns)

- FR-T610-1 GF B1 x B27: UNDER -0.005957 (B1 -0.005295, B27 +0.011252).
- FR-T610-2 GF B27 x CB8 (L-7c1a1da8): 0.00369 m2 billed by CB8 at 0.75, B27 0.85: UNDER -0.000369 (B27 +0.003137,
  CB8 -0.002768). CB8 ledger plan residual -0.059 m3 (model above ledger): the CB8 side is MODEL-based.
- FR-T610-3 GF B27 x CB8 (L-bd16e692): 0.000923 m2 inside both ledger runs' beyond regions: DOUBLE +0.000692 (CB8
  -0.000692). Cause: T-229 `_beyond` stops at other members' pieces, not at another run's beyond region.
- FR-T610-4 1F CB12 x B6: 0.0125 m2 (CB12 0.25 wide runs 0.05 past the 0.20 column; B6 frames to the column face
  across it) billed by B6 at 0.50, CB12 0.75: UNDER -0.003125 (CB12 +0.009375, B6 -0.00625).

### Sensitivity (oblique-end cap)

With no oblique end (cap 0) FR-T610-1, -2 and -4 stand unchanged (each block lies where both faces of both beams are
drawn); FR-T610-3 (0.000692 m3) exists only once a face may run on past its partner (cap 1 or 2 x width, same value):
it is the one result that rests on the end-edge reading.

### Named open items

- F-T610-1 (register vs rule scope): ELEMENT_REGISTER 'BEAM BAND OVERLAP' names the owner "by UP-CONC-JOINT-001
  1.0.0", but that record lists beam-beam junctions as NOT in scope. The beam-beam owner is R-T610-1 (c) (PROPOSED,
  for the Lead to adopt or amend; total independent of the owner).
- 1F B4 x CB10 zone 0.003333 m2 HELD (CB10 width CONFLICT, no valued line).
- 14 ledger lines whose billed plan is not reproduced within 0.01 m3 (listed in out/); of the zones above only
  FR-T610-2 (CB8 L-7c1a1da8) reads one of them.

## Lessons-register row (ERS s.7, PROPOSED)

| 2026-11-07 | a beam-beam block at a column corner was reported billed twice (F-C-P03-2) when the deeper run stopped at the
shallow beam's face: billed once, at the shallower depth | the overlap was read from one line's plan without the other
line's construction | a common block: drawn bands net of columns; physical = zone x deeper depth; read BOTH lines'
billed plans before naming a double count (every villa) | tests/t610_beam_overlap normal + adverse | PROPOSED |
