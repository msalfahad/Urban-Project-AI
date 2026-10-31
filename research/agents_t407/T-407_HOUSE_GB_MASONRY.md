# T-407 Masonry below the exterior ground beams of the house, run by run (development villa; method every villa)

Worker 1 (lane S), 2026-10-31 / 11-01 UTC. Research row: no engine, rule, knowledge, method, registry or candidate line
changed; nothing released. ERS applied: s.2.1 (physical element first), s.2.2 (printed > drawn > inherited; owner
method beside), s.2.3 (first principles), s.2.4 (freelancer reconciled), s.3 (physical vs line; a range never a mid
value; a printed minimum is a bound), s.4 (rules + tests), s.7 (lesson). Owner rules: Q-60 A (block to the underside of
the beam above it), owner block rule 2026-10-20 10:45 (engineering-office notes decide black / white and override the
Urban fallback), Q-21 C (1.50 m is a minimum excavation, not the founding level), Q-28 A PROVISIONAL (crossings),
Q-65 C (a block product stays HELD until specified), Q-75 (black-block count is procurement, after net m2),
UP-QTY-STATUS-001. ELEMENT REGISTER ruling 2026-10-31 20:20: owner trade BLOCKWORK BELOW N.G., one line per run, never
inside the boundary-wall masonry (T-403) or the ground-beam concrete (T-391). Built on merged T-253 (exterior datum,
annex CONFLICT), T-289 (exterior run ids / line ids), T-391, T-403 (lower band split, fence masonry). Files cited by Drive
folder and title, entities by DXF handle; no coordinate, image, client name or note text committed.

## 0. Read this run (Drive "Alsenan chalet project", read-only; private copies in .work/private only)

| Source | sha256 prefix | Read for |
|---|---|---|
| ST7757.pdf | 74da1523 | p.1 notes (note 2, neighbour-side beams) + column plan; p.2 FOUNDATION PLAN; p.3 GROUND BEAMS PLAN; p.9 note 1 + Schedule of Footings (H); p.13 'Ground Beams for exterior walls' (300 dpi) + TYP. DETAIL OF ISOLATED FOOTING; p.14 TYPICAL BOUNDARY WALL A-A |
| ST7757 dxf.dxf | 9f9d1179 | S-BOUN 1658 / 1659 (lower band), 7FE / 7FC / 810 (fence), layer-1 house beam faces on the plot line (136, F8, FC, FD), S-COL.BON closed outlines, footing outlines of PITS_T347.csv |
| Alsenan_Architectural_P7757_Pages_11-12.pdf | (Drive) | p.11 SECTION B-B at both plot ends (200 dpi): ground line +-0.00 with earth hatch; nothing drawn below it |
| P7757.dxf (P7757_DXF_COMPRESSED.zip) | ab54dd55 | the V3.0.33 chain run for the line binding (s.6) |
| freelancer workbooks | (repo FREELANCER_RAW_ROWS.json) | blockwork 'الكميات' all rows; RC 'الشناجات' r15 (quantities only) |

## 1. The physical element (ERS s.2.1) and what the sheets print

Under each exterior ground beam of the house one of three things is built, and the class comes only from what is
printed for that run (R-T407-1):

- **p.13 'Ground Beams for exterior walls'**: top 'Ground Floor slab level', underside a dashed line 'Outer Normal
  ground level', depth 'FOLLOW ARCH.', 0.30 wide on 10 cm blinding 0.50 wide. Read alone: the beam soffit sits on
  blinding at the outer natural ground; nothing is built below it.
- **p.1 note 2** (column and axis plan, Arabic): the exterior ground beams on the NEIGHBOUR side are cast with black
  block above and below them, built from the foundation level. This overrides p.13 below those beams only.
- **p.2 FOUNDATION PLAN**: the 0.20 lower boundary band (S-BOUN 1658 / 1659) runs round the whole plot line, also under
  the house where the house stands on the plot line (T-403 HOUSE split 44.37 m).
- **p.9 note 1**: excavation not less than 1.5 m below the existing plot level (a minimum, Q-21 C). Footing H: F 0.30,
  F8 / F10 / F11 / F14 0.50, F15 0.40, FN 0.30. **p.13 footing detail**: 10 cm plain concrete + membrane + 5 cm screed.
- **Architectural section B-B** (Pages_11-12 p.11): at both plot ends the walls rise from the +-0.00 ground line; no
  construction is drawn below it (silent, not evidence either way).

Levels (T-253 s.2, Checker-verified): main-house exterior beams top +0.95, soffit +-0.00 (D 0.95 DRAWING-CONFIRMED);
annex exterior beams top +0.25, soffit CONFLICT (D-35, RFI-S09): reading L (levels) 0.25 -> soffit +-0.00, reading S
(the printed section's three bar zones cannot sit in 0.25 m) prints no depth.

## 2. Run table (acceptance a, b)

Band axis lengths from `t407_extract.py` (T-403 frame and split, reproduced: HOUSE 44.37 m = annex S + main S 29.972 m +
street 6.599 + sea 7.799); the south side split at the 810 passage band (annex west of it, main house east of it).
Height lower bound (R-T407-2): h >= soffit - layer under the beam (0.10 max) - highest foundation top. Highest foundation
top: band -1.50 + 0.10 + 0.60 = **-0.80** (both printed band depths, blinding taken at its maximum); footings
-1.50 + 0.15 + 0.50 = -0.85 (thickest footing crossed). So **h >= 0.00 - 0.10 + 0.80 = 0.70 m**; no upper bound printed.

| Run | Owner / side | Ground-beam runs over it (T-289 ids, V3.0.33 lines) | Band axis m | Columns on the axis m (S-COL.BON) | Net axis m | Footing crossings m | Class (evidence) | h | Masonry plane (m2) |
|---|---|---|---|---|---|---|---|---|---|
| MAIN_S | main house, S (neighbour) | 7D0+FC #1..#4 = 2.975 + 5.745 + 6.35 + 1.20 = 16.27 ff (L-cc6aaa99, L-e8536bc4, L-e9a88532, L-c9bb2eca) | 19.271 | 218 0.50, 249 1.10, 251 0.50, 255 0.70, corner 200 0.201 = 3.001 | **16.270** (= the beam ff 16.27, 0.000) | F10/F 3.151, F11 3.50, F14 3.80, F 0.65 | PRINTED (p.1 n.2) | >= 0.70 | **MISSING, HELD: gross AT_LEAST 13.4897, net AT_LEAST 11.389** |
| ANNEX_S | annex, S (neighbour) | 7D4+F8 #1, #2 = 5.45 + 4.25 = 9.70 ff (L-402dbe61, CONFLICT) | 10.701 | corner 207 0.301, 20B 0.40 = 0.701 | **10.000** (= 9.70 ff + 0.30 corner square of the annex east beam 10B+7D1, no column there) | F15 1.80, F 0.801 | PRINTED (p.1 n.2) | none (D-35): reading L >= 0.70, reading S unprinted | **MISSING, HELD, no bound** (reading L would give net >= 7.000 m2, shown, not adopted) |
| MAIN_E_SEA | main house, E (sea) | 7E0+FD #1, #2 = 3.35 + 3.25 = 6.60 ff (L-9e28c701) | 7.799 | 1FC 0.50, corner 200 0.399, 809 0.30 = 1.199 | **6.600** (= ff, 0.000) | F10/F 1.299, F8 1.95, FN 1.00 | UNKNOWN_EXISTENCE: band drawn, nothing printed between; p.1 n.2 names the neighbour side only | (IF built) >= 0.70 | **HELD by name, no quantity** (IF built: net >= 4.620 m2) |
| ANNEX_W_STREET | annex, W (street) | 136+7D5 #1 = 6.00 ff (L-4783c6e1, CONFLICT) | 6.599 | 204 0.40, corner 207 0.199 = 0.599 | **6.000** (= ff, 0.000) | F 0.70 + 0.699 | UNKNOWN_EXISTENCE (as above) | none (D-35) | **HELD by name, no quantity** (IF built and reading L: net >= 4.200 m2) |
| 17 exterior runs inside the plot | main 11, annex 6 (summary key exterior_runs_inside_plot, with line ids) | 107+7CE, 109+7CB #2 #3, 10A+7C9, 114+115+7DF #2, 145+7CA, 170+7C3 #1..#4, ARC 157+158; annex 10B+7D1 #1 #2, 137+138, 13D+7D2, 13E+7D6 #2, ARC 139+13A | - | - | - | - | NOT_APPLICABLE (p.13 section on ground, no band below: S-BOUN in the two plan frames = 5 entities, all on the plot line) | - | none |
| 3 court runs | court | 178+7DB, 185+7C7, 1811+1812 | - | - | - | - | UNKNOWN: no section printed (T-253 s.4), no band below; HELD with their section | - | none |

Columns: every corner column is split along the axis and counted once (207: 0.301 S + 0.199 W; 200: 0.201 S + 0.399 E).
Block type on the two PRINTED runs: black block (p.1 n.2; owner rule 2026-10-20 10:45: the engineering-office note
decides); the product / density stays HELD in the sense of Q-65 C. Thickness: not printed -> HELD; readings beside, not
adopted: 0.20 (the band width it stands on, INHERITED) vs 0.30 (the beam width it carries).

Status words (WORKFLOW_CONTROLS s.5): MAIN_S plane AT_LEAST DRAWING-CONFIRMED in its lower bound, value HELD;
ANNEX_S HELD (CONFLICT); MAIN_E_SEA / ANNEX_W_STREET HELD (existence UNKNOWN); inside runs NOT APPLICABLE.

## 3. One layer, one owner (acceptance c; all 0.000)

- Fence (T-403 masonry AT_LEAST 17.628 m2 on 44.07 m): house axis inside the fence band **0.000 mm**; house 44.37 +
  fence 44.07 + pool 3.50 = band 91.94 m, residual **0.000 m**. No run is both fence and house.
- Ground-beam concrete (T-391 / T-289 lines above): the masonry ends at the beam soffit (+-0.00, less the 0..0.10
  blinding), the beam is measured from its soffit up (D 0.95 main; annex CONFLICT) -> 0.000 m3 shared. Plot-line house
  faces inside the fence band: 0.000 mm.
- Lower band concrete (L-6290a9f3, T-403 split): the masonry starts at the band / footing top -> 0.000 m3 shared.
- Columns: deducted from the net plane (they pass from the footing to the beam); not in the masonry.

## 4. Owner manual method and drawing-derived method side by side

| Component | Owner manual method | Drawing-derived (this task) | Candidate V3.0.33 | Freelancer |
|---|---|---|---|---|
| Block under the neighbour-side main-house beam | Q-60 A: run x height to the underside of the beam; type from the engineering note (black); thickness 'usually 15 / 20, 20 next to columns' is not a printed thickness | net AT_LEAST 11.389 m2 (16.27 x 0.70), gross AT_LEAST 13.4897; value HELD (formation) | no line (MISSING) | no row |
| Block under the neighbour-side annex beam | as above | HELD, no bound (D-35); reading L 7.000 m2 shown | no line (MISSING) | no row |
| Street / sea house sides | Q-60 A applies only if block is built | existence UNKNOWN (designer) | no line | no row |
| Count of blocks | Q-75: 12.5 / m2 for 40 x 20 faces, procurement after net m2 | not computed (net m2 HELD) | - | - |

The two methods agree on the measure (run x height to the beam underside); they differ in no rule, only in the facts
the sheets leave open (formation, the annex beam depth, existence on two sides).

## 5. Freelancer (quantities only; acceptance d)

Blockwork workbook: the GF exterior rows (r14 .. r36) carry heights 4.0 / 3.5 m above the slab, 'السور' (r150) 37.2 x
2.0 = 74.40 m2 above N.G. (T-396); **no row names masonry below N.G. or under the ground beams**. RC workbook: the lower
band in his 71.7 m perimeter row (T-403). Comparison: ours MAIN_S AT_LEAST 11.389 m2 net vs his none; ANNEX_S HELD vs
none; E / W HELD (existence) vs none.
- Existence on the neighbour side: **ENGINE_RIGHT** (p.1 note 2 prints it; T-403 F-finding confirmed run by run).
- Quantity: **UNRESOLVED** (HELD; the residual is the whole held quantity, traced to the unprinted formation and D-35).
- Street / sea sides: **UNRESOLVED** (neither he nor the drawings show block there).
- Whether any of his bare GF heights reach below the beam is not traceable (no level in his rows): not counted as a match.

## 6. Binding to the candidate V3.0.33 (acceptance a)

See `summary_t407.json` key `v3033_binding` (own chain run: v304_run.py -> v3033_run.py on the two private DXFs).

## 7. Designer facts for the RFI register (consultant items; no owner question: ERS s.2.7 not met)

1. Foundation (formation) level under the neighbour-side house beams: fixes the block height (AT_LEAST 0.70 m today;
   +0.20 m if the band is 0.40, +0.10 m without band blinding, +0.10 m without blinding under the beam).
2. Whether the p.13 10 cm blinding is cast under the house beam where the beam sits on block (0 .. 0.10 m of height).
3. Street (annex) and sea (main house) sides on the plot line: what stands between the lower band and the house beam
   (block, mass concrete, nothing) - T-403 item 6, now with the run lengths 6.000 / 6.600 m net.
4. Block thickness under the 0.30 beam on a 0.20 band.
5. Annex exterior beam depth (RFI-S09 / D-35): decides the annex south height (10.000 m net run).

## 8. Rules, tests, lessons, lane I proposal

Rules R-T407-1 .. -5 in `t407_rules.py` (research, every villa). Tests `tests/t407_house_gb_masonry` (18): Villa R hand
fixture (south neighbour run with a footing crossing: h >= 0.80, gross 12.000 / net 11.040 m2; street run existence
unknown, conditional 5.040 m2; interior face NOT_APPLICABLE), deeper formation only raises the bound, order / mirror
invariance, corner column once; adverse: masonry under the fence AND the house beam on one segment, defaulted height /
formation / band depth, held as 0 and a held line with a value, mm as m, the neighbour note extended to the street run,
a CONFLICT soffit given a bound, a beam deeper than the formation, no foundation member, columns longer than the run;
the development villa summary reproduces and pins (incl. a bare-number annex soffit refused).

Lessons-register row proposed: | 2026-11-01 | Block under the house's neighbour-side ground beams (26.27 m net of
columns, AT_LEAST 11.389 m2 on the main house alone) sat in no line, while two other house sides carry the same
foundation band with nothing printed on it | below-ground masonry was looked for in the boundary-wall section only;
the general note on the column plan that governs the house beams, and the beam's own exterior section, were never set
run by run against the foundation band | below every exterior ground beam the built element is classified run by run
from what is printed for THAT run: a note printing masonry -> it exists, height from the highest foundation top to the
beam soffit, bounded below from printed minima (AT_LEAST, never a point value); a band drawn with nothing printed
between -> existence UNKNOWN, never inferred from the band, never extended from another side; the beam's own section
on ground with no band -> NOT_APPLICABLE; a soffit in CONFLICT gives no bound (every villa; provenance T-407) |
tests/t407_house_gb_masonry | PROPOSED |

Lane I proposal (no candidate line here): two NEW HELD BLANK lines, owner trade BLOCKWORK BELOW N.G. (black block, p.1
n.2): MAIN_S (net axis 16.270 m, AT_LEAST 11.389 m2 beside, gross AT_LEAST 13.4897) and ANNEX_S (net axis 10.000 m,
no bound, D-35 named); MAIN_E_SEA and ANNEX_W_STREET as named register items (existence UNKNOWN, designer item 3), no
line until printed. Never inside L-6290a9f3 (band) or the ground-beam lines; never in the T-403 fence masonry line.

Reproduce: `python3 -I research/agents_t407/t407_extract.py "<private>/ST7757.dxf"` (checks the committed input),
`python3 -I research/agents_t407/t407_alsenan.py` (checks the summary),
`python3 -I research/agents_t407/t407_alsenan.py --v3033 <private>/<run>/V3_0_33_BOQ_LINES.json` (re-binds).
