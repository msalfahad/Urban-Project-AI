# T-189 Concrete-volume ownership at intersecting structural elements (stair / B20 / B23 first; every villa)

Worker 1 (lane S), 2026-10-22. From the Checker's finding D-CHK-T180-1 (T-180 slot 17:18) and owner 18:00. Research +
one NEW unwired module + tests; no engine, method, rule or knowledge file changed; no released quantity changed.
ENGINEERING_REASONING_STANDARD (ERS) s.2.1-2.4, s.3, s.4 A/B/C, s.7 applied. Drive "Alsenan chalet project" read this
run (read-only; private copies in `.work/private`, never committed): ST7757 dxf.dxf (sha 9f9d1179),
P7757_DXF_COMPRESSED.zip (P7757.dxf sha ab54dd55). Development villa: not an accuracy claim.

## 1. Result in engineering terms

| Item | Before (T-184 ledger rev1) | After (rev2, this task) | Change | Cause |
|---|---|---|---|---|
| ST-01 MS1-U (GF -> 1F upper flight) | 1.0548 m3 | **0.9976 m3** | -0.0573 | flight solid inside the full-depth B20 band (0.20 m plan strip between the band's stair-side face and the last riser line) was billed in the stair AND in the B20 line |
| ST-01 MS2-U (1F -> 2F upper flight) | 1.0588 m3 | **1.0014 m3** | -0.0575 | same, inside B23 |
| ST-01 dog-leg | 4.746 m3 | **4.631 m3** | -0.1147 | the two heads |
| Staircase system (ST-01 + ST-01b + ST-02 + ST-03) | 6.790 m3 | **6.675 m3**, of which MS1-L 0.863 HELD (C-ST-4, range 0.863 .. 1.055): not held 5.812 | -0.1147 | |
| B20 span 2 (released route G line) | 0.990 m3 | 0.990 m3 (unchanged) | 0 | already billed at 0.40 x 0.75 x 3.30 through the shaft |
| B23 span 2 (released route G line) | 1.11375 m3 | 1.11375 m3 (unchanged) | 0 | already billed at 0.45 x 0.75 x 3.30 |

rev2 = the Checker's own quantities 0.9976 / 1.0014 (17:18) to 0.0001 m3, now reproduced by an exact 3-D intersection
(not by subtraction of the Checker's figure). The T-184 held item HEAD-CLASH 0.1147 is RESOLVED as a quantity (it is
exactly this double count); the riser-count RFI behind it (Q-46: section 12 risers vs plan 11 lines) stays open for the
designer, and a different answer re-computes the flight. Staircase system status unchanged: PARTIALLY VERIFIED (owner
16:45). Freelancer comparison unchanged in kind (his 8.131 for ST-01 vs own 4.631: -3.500 m3; the head clash is not in
his figures; ERS s.2.4 table of T-184 s.5 stands, the own side lower by 0.1147).

## 2. The physical element (ERS s.2.1)

ST-01 dog-leg stair beside the lift (ELEMENT_REGISTER ST-01), upper flights MS1-U (+3.50 -> 1F +5.50) and MS2-U
(+7.684 -> 2F +9.70). Reinforced concrete flight = 11 step triangles over 11 goings + waist T 16 (Q-19, Q-47 A), width
1.20 (wall face to the S-OPENING line), 12 risers (section A-A, Q-46 A). At the head each flight arrives into a
full-depth edge beam of the floor above: B20 40 x 75 (GF roof slab, ST p.4; schedule ST7757.pdf p.10) and B23 45 x 75
(1F roof slab, ST p.5). The question is not a quantity choice but OWNERSHIP of one monolithic volume.

Drawing readings (ST7757 dxf.dxf, mm):
- GF roof slab: 12 riser lines 25B (y 48448) .. 459 (y 45148) at 300, x 58643 .. 59793; B20 band lines 458 (y 44948)
  / 2C6 (y 45348), x 52693 .. 59793: the last riser line 459 is **0.200 m inside** the band (stair-side face 45348).
- 1F roof slab: 11 lines 62F (48448) .. 644 (45448); B23 band 5E4 (44898) / 5E1 (45348). The 12th riser (section
  A-A) is 11 goings from 62F = 45148: **0.200 m inside** B23 (0.45 wide), hidden by the band on the plan.
- Released route G lines (pinned baseline A, re-run this session: REPRODUCED 1,455 lines, BOQ_LINES.csv b96185d4,
  engine 94e39ee6): `P-C:BEAMS:GF:BAND0043.2` mark B20 (BOUND), depth 0.75, length 3.30, net plan 1.32 m2 = 0.40 x 3.30
  (junction deductions 0), 0.990 m3; `P-C:BEAMS:1F:BAND0031.2` mark B23, depth 0.75, 3.30, 1.485 m2, 1.11375 m3; basis
  "net plan (B x L - column - junction) x H; slab panels stop at band faces". Beam register (T-110 / T-145, 65.060 m3):
  BM-GF-043 B20 span 3.30 0.9900, BM-1F-026 B23 span 3.30 1.1138, CALCULATED, full section. The flights lie at x 58.593
  .. 59.793 / 19.869 .. 21.069, inside span 2 of each beam (x 56.493 .. 59.793 / 17.769 .. 21.069).
- V3.0.x candidate: carries the route G beam CONCRETE lines unchanged (V3.0.4 re-run, section 8: B20 0.990 / B23 1.11375 m3) (V3.0.1 lists T-105 "CONCRETE_LEDGER_V3 beams ...
  not wired here", arch_v301.py:97; V3.0.3 replaces beam STEEL only, arch_v303.py:1-3; V3.0.2 / V3.0.4 touch footing
  steel, soffits, necks); every other line is byte-identical by each version's identity assertion. Confirmed on a V3.0.4
  run this session (section 8).

So B20 and B23 ARE billed at their full depth over the stair: the intersection is in the beam lines, and the stair must
be measured net of it to be in the complete structural BOQ exactly once (owner 18:00 (1)).

## 3. Reconstruction from first principles (ERS s.2.3; exact 3-D, module `concrete_overlap_ownership`)

Section along the flight, s from the first riser line, z' above the flight's lower level; r = 2.00 / 12 (MS1-U) and
4.20 / 25 = 0.168 (MS2-U), g = 0.30, w = 1.20, t = 0.16, cos = g / hypot(g, r).
Inside the band, s in [3.10, 3.30] (the last 0.20 m before the last riser line):
- step 11 triangle (height r (1 - (s - 3.00) / g) over its going): part over its last 0.20 of 0.30 =
  1/2 r g (0.20 / 0.30)^2 w = 4/9 x 0.0300 = **0.013333** (MS1-U), 4/9 x 0.03024 = 0.013440 (MS2-U);
- waist strip: 0.20 x t / cos x w = 0.20 x 0.16 x 1.14396 x 1.20 = **0.043928** (MS1-U), 0.044011 (MS2-U);
- in-band total **0.057261 / 0.057451 m3** (0.1147 together); plus the arrival wedge (step 12 beyond the last riser
  line, 0.030 / 0.03024) already deducted by Q-62 A in rev1: 2/3 of its run in the band, the rest in the slab (GF-077
  / 1F-062): physical stair-beam intersection 0.0839 / 0.0869 m3, stair-slab 0.0033 / 0.0008 m3.
- Containment (the beam owns it only if the solid lies inside the beam section): flight solid in the band spans z
  +5.039 .. +5.333 inside B20 +4.75 .. +5.50 (MS2-U +9.237 .. +9.532 inside +8.95 .. +9.70). Margins: 0.167 m up,
  0.289 m down: the result does not change for any offset between the stair's level reference and the beam top in that
  range (finish build-up included).

Owner manual method and drawing-derived method side by side (ERS s.2.2): the owner's manual stair formulas (Q-19 steps
n x 1/2 r g w, Q-47 A waist w t L_sloped, Q-62 A wedge deduction) are kept unchanged term by term; the drawing-derived
3-D intersection decides only WHICH part of that solid sits inside a member billed separately. Both give the same
gross (1.0848 / 1.0891); the difference is only the ownership of 0.1147 m3.

## 4. Reconciliation (ERS s.2.4)

| Step | MS1-U | MS2-U | Cause |
|---|---|---|---|
| Ledger rev1 (T-184) | 1.0548 | 1.0588 | gross - Q-62 arrival wedge |
| Checker own (17:18) | 0.9976 | 1.0014 | flight measured to the beam face |
| difference | 0.0573 | 0.0575 | step-11 part 0.0133 / 0.0134 + waist strip 0.0439 / 0.0440 inside the band |
| this task (geometry) | 0.99755 | 1.00137 | = Checker to 0.0001; residual 0.0000 |

Released engine (baseline A), for lane I, no quantity changed: the route G stair line `P-C:SCOPE:STAIRS:GF:CC-7390ea1139`
measures its flight runs over plan 1.15 x 3.30 = 3.795 m2, i.e. also to the last riser line inside B20: by its own
convention (0.175 waist, 0.165 riser) 1.15 x 0.20 x 0.2822 = about **0.065 m3** of it is billed with B20 too (and the
1F -> 2F storey is missing altogether, D-T184-1). Any wiring of a stair ledger into V3.0.x must take rev2 with this rule.

## 5. The rule (ERS s.4 B) and the reusable check (s.4 C)

**R-CONC-OWN-1 (proposed, `research/agents_t189/R-CONC-OWN-1.json`; any villa; provenance Q-20, Q-62 A cond, the route
G measurement bases, D-CHK-T180-1)**: concrete where structural elements intersect is measured exactly once; the 3-D
intersection (never a plan overlap) is owned by the element whose BOQ line, by its stated basis, is billed THROUGH the
junction at full section; the other is measured net of it and keeps the deduction in its ledger; if no basis contains
it, the element that would lose it keeps it; where two bases contain it the project's one precedence decides (route G:
column > beam > slab / landing > stair; pool base > pool wall); a pair with no established precedence, or a junction
whose levels are not printed, stays HELD (OWNER_UNDEFINED / UNDETERMINED with a bound). Stair-head corollary: a flight
arriving into a beam billed at full depth is deducted by the flight solid from the beam's stair-side face, not only by
the last step triangle; a downstand-basis beam owns only the part below the slab soffit. Adoption = a new rule version
(lane I / Lead); no existing rule file edited.

**Module `engine/source/concrete_overlap_ownership.py` (CONCRETE_OVERLAP_OWNERSHIP_V1, unwired, rollback: delete)**:
elements as unions of convex polyhedra (half-spaces); exact volumes (vertex enumeration, facet pyramids), exact
differences and inclusion-exclusion unions; builders for boxes, convex plan prisms, beams on any axis, straight flights
(any direction, mirror, m / cm / mm, unknown unit refused). `check_ownership`: union of physical vs billed lines ->
DOUBLE / GAP / OUTSIDE / LEDGER_MISMATCH, per pair the owner by precedence (OWNER_UNDEFINED never guessed), levels not
printed -> UNDETERMINED with exposure 0 .. bound, never deducted; status PASS / PASS_HELD / FAIL.

**Tests `tests/t189_overlap` (35 pass)**, synthetic Villa R (hand values in the module docstring of the test):
stair head: riser line at the beam face -> only the wedge overlaps (normal) vs 0.20 inside a 0.40 beam with only the
wedge deducted -> DOUBLE 0.052665 (adverse) at 0 / 30 / 60 deg, mirrored, in mm; corrected -> PASS; no deduction at
all -> DOUBLE wedge + band; both lines net -> GAP reported (never 0). Beam through slab: route G basis PASS (union
3.68), full plate + full-depth beam DOUBLE 0.240, slab-plate / downstand basis PASS only with its own profile. Column
through beam: net plan PASS, gross DOUBLE 0.045. Neck on footing PASS; neck billed from the underside DOUBLE 0.080 +
OUTSIDE 0.080; neck drawn through the footing with no established owner -> OWNER_UNDEFINED (never split). Pool walls on
the base PASS (union 12.96); walls from the base underside DOUBLE 1.152 (the freelancer's pool error pattern). Plan
overlap with unprinted levels -> PASS_HELD, exposure (0, 0.150) / (0, 0.390), nothing deducted. A line billing nothing
-> GAP. Two beams crossing -> DOUBLE + OWNER_UNDEFINED. Ledger figure vs geometry cross-check. Alsenan: the two heads
(rev1 FAIL, rev2 PASS = Checker 0.9976 / 1.0014, total -0.1147, margins), the committed rev2 ledger re-generated
byte-identical, the pool (below).

## 6. Alsenan check on the other ledgers

- **Pool (T-183 r2)**: base = outer footprint x 0.40 (-1.30 .. -0.90), walls = band x 1.20 above the base top: PASS,
  no double, no gap; 36-chord model base 4.3718 / walls 2.8265 (T-183 exact arc 4.374 / 2.828; chord deficit 0.002 /
  0.0015, not a quantity). Walls from the base underside: DOUBLE 0.942 = band 2.357 x 0.40 (the freelancer's "+0.960
  base thickness counted again" on his 12 m). HELD, not deducted: combined footing F8 (S-FOOTINGS 1B24, 4.00 x 3.60 x
  0.50, founding level not printed) overlaps the pool in plan 1.2964 m2 (T-183 interface 1: 1.297): exposure 0 .. 0.518
  m3 with the base, 0 .. 0.772 with the walls; the boundary-wall band (T-183 interface 2, 0.20 x 0.60, level not
  printed) under the back wall: 0 .. 0.280 / 0 .. 0.840. Status of these junctions: UNDETERMINED until the designer
  prints the F8 / B.W levels (already open in T-183 / T-170); never a deduction.
- **Beams (T-110 register / route G)**: B20 / B23 spans 2 bill the full section through the shaft (section 2); the
  slab panels GF-077 / 1F-062 stop at the band faces (T-139: "1F arrival = B20 band 0.40 + 1.55 m of GF-077", "2F
  arrival = B23 band 0.45 + 1.50 m of 1F-062"): beam-slab PASS; the arrival wedges are owned by beam + slab (Q-62 A).
- **Landings MS1-LD / MS2-LD**: they meet the flights at the first riser line only (touch, no shared volume): PASS.

## 7. Not done / open (no quantity guessed)

- MS1-L stays HELD (owner 18:00 (4), C-ST-4: structural plan 12 straight riser lines vs architecture 10 + section 15).
- Foot of a flight on the floor it starts from (MS1-L at GF +1.00, ST-01b, ST-03): the waist below the floor level over
  the first t / sin of the run (about 0.33 m, of the order of 0.03 m3 per foot) may lie inside a ground slab / beam line;
  the ground-slab geometry under the shaft was not established here: a Checker / lane S follow-up, not a deduction.
- 'B3 (With Stair)' cranked beams (Q-61 (2)) stay HELD: if they are ever measured, this check must run on them first.
- Footing / neck, footing / strap (T-174), pool / F8 have no established precedence: OWNER_UNDEFINED if they ever
  intersect in a ledger; the drawing-based rule comes with their tasks.

## 8. V3.0.4 confirmation run

`research/agents_t167/v304_run.py` re-run this session on engine 94e39ee6 (M4 profile, as T-167): exit 0,
V3_0_4_BOQ_LINES.csv sha256 **d86de34a** (= the merged T-167 V3.0.4 output, reproduced). Its beam concrete lines over
the stair are the route G lines unchanged: `L-d06033aa8d5f29aef490` STR.CONC.BEAM 0.990 m3 (B20: depth 0.75, length 3.3,
net plan 1.32, junction deductions 0, deductions []) and `L-5ca0573b64ee1cb22e0e` STR.CONC.BEAM 1.11375 m3 (B23: 0.45 x
0.75 x 3.3). Its GF stair line `L-7863355dfcb68a681d2d` STR.CONC.STAIR 2.786 m3 is the released route G line (section 4:
it also reaches the last riser line inside B20). So in released A AND in candidate V3.0.4, B20 / B23 carry the full
depth over the stair; no V3.0.x stair ledger is wired yet, and rev2 is what a wiring task must take.

## 9. Lessons-register row proposed (ERS s.7)

| 2026-10-22 | Stair upper flights MS1-U / MS2-U 1.055 / 1.059 vs 0.998 / 1.001 m3 (Checker D-CHK-T180-1); 0.1147 m3 counted in the stair ledger AND in the full-depth B20 / B23 lines | the junction deduction was taken at the riser line (last step triangle only, Q-62 A applied to a slab), not at the face of the member billed through the junction; ownership was never checked against the beam line's measurement basis | R-CONC-OWN-1: the 3-D intersection is owned by the element whose line is billed through the junction at full section, the other is measured net of it from that member's face; sum of owned = union, no pair with zero or two owners; unknown levels / undefined precedence held (any villa) | tests/t189_overlap (normal: riser at the beam face; adverse: riser 0.20 inside a 0.40 beam, wedge-only deduction -> DOUBLE 0.0527; plus beam / slab, column / beam, neck / footing, pool wall / base, unknown levels) | rule proposed; ledger rev2; Checker to verify |
