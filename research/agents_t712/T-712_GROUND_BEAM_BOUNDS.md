# T-712 concrete ground beams: 20 HELD BLANK STR.CONC.GROUND_BEAM lines on V3.0.70 (lane S, research only)

Worker 1, 2026-11-11, branch `agents/task-T-712`. Nothing wired, released or VERIFIED; no AT_MOST; no floor summed into
a released total. ERS s.2-7; R-CONC-OWN-1 / R-T666-1; UP-QTY-STATUS-001; R-T658-1 (bounds contain the drawn member);
R-T696-1 (floors at 6 dp). Rules `t712_rules.py` (R-T712-1 .. 3), own DXF outlines `t712_measure.py` ->
`out/T712_AREAS.json`, ledger `t712_alsenan.py` -> `out/T712_LEDGER.json` + `out/T712_CENSUS.md`, tests
`tests/t712_ground_beam_bounds` (27).

## Own reads this run (Drive 'Alsenan chalet project', read-only; private copies only)

- 'ST7757 dxf.dxf' (sha 9f9d1179), ST p.3 ground-beam frame: every outline below drawn by handle to its owning faces;
  no two outlines overlap and none enters a GB-frame column (shapely check in the output).
- ST7757.pdf p.13 'Ground Beams for exterior walls': top 'Ground Floor slab level', depth 'FOLLOW ARCH.', underside
  'Outer Normal ground level' on 10 cm blinding; bars 3T16 top, 2T12/30cm each side (two rows drawn), 6T16 bottom (two
  rows), T8/15. Interior sections 30x30 (< 2.5 m), 30x40 (< 5 m), 30x60 (> 5 m), all 'without concentrated load'.
- ST p.3 levels: annex +0.30 inside, yard +0.15 outside, plot corners +-0.00; NO level mark on the west-entrance landing
  (between the yard stair and the main west wall) nor on the C4 -> plot-end stretch by the pool. Arch sheet03 GF plan:
  the entrance stair rises from the +0.15 yard to the door; the landing carries no level either.
- The annex is drawn in a second frame (annex roof beams B1 / CB5 / CB6) with SMALLER columns (0.20 / 0.25 instead of
  0.30): not a ground-beam frame; R-T712-3: the GB frame's larger columns give the shorter (floor) length.

## Result per line (physical element -> bound)

| class | lines | floor basis | AT_LEAST beside (m3) |
|---|---|---|---|
| D-35 annex exterior | 8 | drawn area x (+0.25 - N.G. 0.00), both levels DESIGNER-APPROVED; the printed bars cannot fit 0.25, so the beam is at least that deep (R-T658-3) | 2.250481 |
| D-35 junction remainder BAND0013.1 | 1 | 0.10 x 0.30 sliver between face 7D6 and col 211 (C3) x 0.25: least floor of the members that may own the square (R-T712-1 JUNCTION); 0.012 if the 30x40 of the released span 0017.1 runs through (beside) | 0.007500 |
| D-33 loaded runs | 8 | drawn area x least title holding over the span readings (R-T658-8) | 2.841864 |
| D-35 court (yard-side) | 3 | none: top (landing / deck level) and the ground under it unprinted -> BLANK, m3 per m of depth 0.18 / 1.14 / 0.39 (0.415 with the 0.05 strip of band 1812 under col 1E8) | blank |

Census 20 / 20 by id: 17 AT_LEAST (5.099845 m3), 3 BLANK_NAMED; none 0, none a range. The 9 bounded lines (1.178378 ..
5.096771) are not touched.

Against the T-658 floors the V3.0.64+ candidates carry as text beside 16 LOWER_ONLY lines (5.069839): +0.022500
BAND0012.1 (T-669 SE corner square, merged), +0.000008 BAND0042 (exact ring area 0.541925 m2 vs census centreline
1.8063 x 0.30), -0.000001 each on BAND0037.1 / BAND0008.2 (directed rounding: 0.2423086 and 0.1476567 FLOOR to
0.242308 / 0.147656, T-658 rounded them up); +0.007500 the new junction floor. Every annex run length re-measured: 5.45
+ 4.25 / 1.50 / 2.30 / 6.00 / 2.40 / 0.50 / 5.80 m = the census runs (the census 'line' lengths 10.13 / 6.4 / 3.1 run
through columns and are NOT the net length).

## AT_MOST

None: the exterior underside is printed only as 'Outer Normal ground level' (the conflicting reading itself), and no
footing-top or formation level is printed (ST p.9 note 1 gives a MINIMUM founding depth 1.50 m, which is no cap); the
loaded runs' unloaded titles are a reference, not a ceiling (D-33).

## Owner manual method beside the drawing-derived method

Freelancer workbook: one GB section 0.30 x 0.60 everywhere. On these 20 drawn plans his section gives 11.116685 m3
(his lump lengths cannot be split per line, T-391). Per class: annex 9.03 m2 x 0.60 = 5.42 vs our floor 2.26 (his depth is
not printed; the drawing prints 'FOLLOW ARCH.' = 0.25 literal: UNRESOLVED on D-35, not an agreement); D-33 7.79 x 0.60 =
4.67 vs floor 2.84 (a loaded run may well be 0.60 or more; UNRESOLVED on D-33); court 1.71 x 0.60 = 1.03 vs blank
(RULE_DIFFERENCE: he assumes a section where the drawing prints none). No verdict ENGINE_RIGHT is claimed on a floor.

## For the Checker (own re-measure of 2 beams)

1. Annex south band L-402dbe61: F8 / 7D4 (0.30 apart) from col 207 face x+0.40 to col 20B (5.45), col 20B to face 7D1
   (4.25); SE square owned by L-6bf14711 (T-669). 9.70 x 0.30 x 0.25 = 0.7275.
2. Junction L-be6708e0: 13D / 7D2 end on 7D6; col 211 (0.50 x 0.30) starts 0.10 east of 7D6; 13E / 7D6 run unbroken
   through the square; sliver 0.10 x 0.30 x 0.25 = 0.0075.
Uncertain: the court stretches are exterior by position (yard on one side) but the ST does not label them; if the
designer prints the landing level, R-GB-EXT-DEPTH-1 values them like the main exterior beams (0.95 deep at +0.95).

## Lessons row (ERS s.7, proposed)

| 2026-11-11 | 20 GB lines sat blank though 16 had Checker-passed floors and one more was measurable | floors were carried as
text and two were rounded up; the neck-cut sliver was held 'no section' though both members through it have a guaranteed
depth | a held member's floor = exact drawn area (owning faces, GB-frame columns) x the least depth the drawings
guarantee, FLOORED; a junction remainder takes the least floor of its possible owners; a beam with neither datum printed
stays blank with m3 per m of depth (R-T712-1 .. 3, every villa) | tests/t712_ground_beam_bounds | PROPOSED |
