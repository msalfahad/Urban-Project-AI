# T-711 concrete blank tail: 15 HELD blank STR.CONC lines on V3.0.70 (lane S, research only)

Worker 1, 2026-11-11, branch `agents/task-T-711`. Nothing wired, released or VERIFIED; no AT_MOST; no bound summed into a
total. ERS s.2-7; R-CONC-OWN-1; UP-QTY-STATUS-001; R-T696-1 (floors at 6 dp). Rules `t711_rules.py` (R-T711-1 .. 3),
ledger `t711_alsenan.py` -> `out/T711_LEDGER.json` + `out/T711_CENSUS.md`, tests `tests/t711_concrete_blank_tail` (31).

## Own reads this run (Drive 'Alsenan chalet project', read-only; private copies only)

- ST7757.pdf p.14 lift detail: pit wall '20' on the raft top up to the slab-on-grade TOP (F.F.L. drawn above it); under
  the raft 5 cm screed / membrane / 10 cm plain concrete; pit depth 'As Per Lift Manufactures recommendations'.
- ST7757.pdf p.8 note 19: beams tie the lift columns at 3.00 m where the storey exceeds 4.30 m; no section anywhere.
  Note 20: walls containing columns are as thick as the column (not a beam section).
- ST7757.pdf p.14 parapet details P1 / P2 / P3 (P1: RC upstand above the slab top 'MUST BE MORE THAN THE HEIGHT OF ROOF
  FINISHING', block above, RC cap 'as per arc.'): agrees with T-311 / T-319.
- p7757_arch_sheet03.pdf (GF plan): the lift 1.80 x 1.80 sits between the hall and the stair hall, both '+1.00'; the
  '+0.30' mark lies east of the stair, away from the lift. So the GF landing = F.F.L. +1.00, slab-on-grade top +0.95
  (T-214 build-up 0.05), equal to the lift column base +0.95 (T-394). NEW for the pit walls.

## Result per line (physical element -> bound)

| Line | Element | Before | After | Basis |
|---|---|---|---|---|
| 4 lift necks C1 / C2 / C2 / C9 | column below GF on raft FF | blank | AT_LEAST 0.173 / 0.173 / 0.173 / 0.4325 | R-T711-1 = T-657 (MERGED) low: min section (D-63) x h 1.73 = +0.95 - (-1.50 + 0.17 + 0.55); upper open (D-43 supplier depth) |
| L-684fcad3 pit walls | RC ring '20', raft top -> slab top | blank | AT_LEAST 1.903 | ring net 1.100 m2 (T-394) x 1.73; D-63 does not move the ring (column long sides run along it: overlap 0.500 either reading) |
| L-5ae06fda tie beam | GF tie beam at +3.00 | blank | BLANK, D-43 | no section printed; 5.500 m3 per m2 of section (5.50 m) |
| 4 parapets | RC above the roof slab top | blank | AT_LEAST 1.799103 / 1.677886 / 2.949453 / 1.624500 (annex / GF / 1F / 2F) | smallest drawn top x 0.30 upstand (T-319 floor, Checker p.14); upper open: b_edge D-39, material Q-65 C |
| L-061e18cf ST-03 E1 | steps + waist | blank | AT_LEAST 0.355017 | drawn steps (T-258, Checker AGREE); waist S-9 open |
| L-7863355d ST-01 GF remainder | MS1-L + winders + turn slab | blank | AT_LEAST 1.213429 | R-T711-2: min(reading A 27 risers 1.213429, reading B 28 risers 1.400927); turn >= 1.44 m2 x 0.16 + 1/2 r x 1.44 whatever the winder subdivision (D-67) or soffit (C-ST-3) |
| L-659243ed MS2 turn riser | junction of plates 0.168 apart | blank | BLANK, C-ST-3 | must exist (upper soffit 0.008 above lower top) but no section: 0.328 m3 per m thickness per m length |
| L-821032bc D1 waist | waist under 4 steps on grade | blank | BLANK, S-9 | may physically be 0 (steps on fill): no floor, no ceiling |
| L-b6b0354b ST-02 curved | 12 curved treads, helicoid, CA | blank | BLANK, D-08 / Q-50 / Q-51 | curved rise printed nowhere: wedges 2.05385 m3 per m of riser |

Family AT_LEAST (beside, never summed into the released totals): NECK 0.9515, LIFT 1.903, PARAPET 8.050942, STAIR
1.568446 m3. Census 15 / 15 by id: 11 AT_LEAST, 4 BLANK_NAMED; none 0, none a range.

## Owner manual method beside the drawing-derived method

Manual (freelancer workbook): lift walls 8.00 x 0.20 x 1.50 = 2.400 m3 including the column pieces 0.750 (also in his
necks) -> his net ring 1.650 < drawn floor 1.903: ENGINE_RIGHT proposal on the low end (his flat 1.50 m is not a
printed height; the drawn minimum is 1.73 m). Necks: his 8.805 m3 on 34 < drawn family low (T-657). Parapets: no
concrete row (blockwork only): RULE_DIFFERENCE / HELD on Q-65 C. Stairs: no waist split: NOT_COMPARABLE.

## For the Checker (own re-measure of 2 lines)

1. Pit walls: p.14 wall top = slab-on-grade top; GF plan '+1.00' on both sides of the lift; 1.100 x 1.73 = 1.903.
2. ST-01 remainder: reading B sum 1.054813 + 0.115714 + 0.2304; the 1.44 m2 smallest turn reading (T-258).
3. Parapet per-line floors: 1.6778868 floors to 1.677886 (T-642 printed 1.677887 half-way): R-T696-1.
Uncertain: the 0.02 membrane in the 0.17 stack is p.13's (T-657); p.14 prints the membrane without a thickness. A
thinner membrane lowers the raft top and only RAISES the floors (the bound stays valid).

## Lessons row (ERS s.7, proposed)

| 2026-11-11 | 11 lines sat blank although merged work held a valid floor (T-657 lift necks, T-319 parapets, T-258 steps) | the
wiring had no one-sided state, so 'lower only' floors stayed in text | a held line with a drawing-supported floor and an
open upper end carries AT_LEAST (never a range, never 0); a line that may physically be 0 or needs an unprinted dimension
stays blank with its item and a per-unit quantity (every villa; R-T711-1 .. 3) | tests/t711_concrete_blank_tail | PROPOSED |
