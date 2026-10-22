# T-173 Stair shaft wall geometry (Q-72 investigation; development villa; every villa)

Worker 2 (lane A), 2026-10-22. Research module + tests; no engine, rule, knowledge or method file changed, nothing
wired, nothing released. ERS (ENGINEERING_REASONING_STANDARD.md) s.2 steps 1-6, s.3 (build before deduct, geometric
scope before numbers) and s.4 applied. Drive "Alsenan chalet project" read this run (read-only; private copies in
`.work/private`, never committed): P7757_DXF_COMPRESSED.zip (architectural DXF: GF, 1F, 2F plans), p7757_arch_sheet10.pdf
(section A-A, re-read at 400 dpi), ST7757 dxf.dxf (GF and 1F roof slab plans), and the freelancer's plaster workbook (his
two shaft rows, numbers only). Element: ST-01 dog-leg stair beside the lift (T-184 id, merged 9fbedc4); walls only, never
stair concrete.

Files: `t173_shaft.py` (generic face measure: union of contacts and openings in the wall plane; any villa),
`t173_alsenan.py` (development-villa run; `--write` makes `SHAFT_T173.json`), `ALSENAN_SHAFT_INPUT.json` (shaft-local
dimensions, levels, sources; no coordinates or client data), tests `tests/t173_shaft` (13 pass).

## 1. Result in engineering terms (m2, whole shaft ST-01)

| Method | Gross | Net (paint) | Status |
|---|---|---|---|
| OWNER MANUAL (G1 room heights 3.65 / 3.35 / 3.35 applied storey by storey, as written; no shaft case in the owner rule) | **142.22** (55.12 + 43.55 + 43.55) | not defined (window positions are not storey-relative in a shaft) | shown beside; owner method, not a measurement; NOT RELEASED |
| Storey-interval shortcut (Q-72 option B; T-128 r2 READY 8710bb1) | 171.90 .. 173.20 (paint) | 147.21 .. 160.55 | superseded by the row below for this element |
| **DRAWING-DERIVED, actual exposed geometry (this task)** | plaster **173.82 .. 177.07**, paint **171.88 .. 175.14** | plaster **156.82 .. 160.98**, paint **154.87 .. 159.03** with every held item undeducted; lower bound with every held item deducted: plaster 137.06, paint **135.26** | geometry DRAWING-CONFIRMED; build-up b and roof datum PROVISIONAL (0 .. 0.10, DCR-6 / DCR-7); door heads ASSUMED - OWNER-APPROVED (Q-55 C); paint top ASSUMED - OWNER-APPROVED (Q-48 A, 0.15 decor); 7 items HELD (s.4); NOT RELEASED |
| Freelancer (his two "stair-house walls" rows, gross) | 204.42 (14.80 x 12.90 + 2.50 x 5.40) | his openings in a separate half-deduction list | - |

Range of the drawing-derived net, explained (paint, 159.03 -> 135.26 = 23.77 m2): build-up b 0 -> 0.10 and the NW floor
under the winders +0.30 -> +1.00: 4.16; held contacts 6.07 (winder turn 2.90, B20 / B23 ends at the stair head 1.44 on
the side walls, B20 over the GF south wall 1.88; 6.22 as pieces, 6.07 once overlaps with other deductions are removed); held openings 13.54 (1F north window 3.92, W27 5.96, GF
doorless passage to the basin space 3.81). The held openings dominate: printing two window heights and
one passage head would close 57 % of the range.

Drawing-derived vs freelancer (gross plaster, like for like): 177.07 vs 204.42 = **-27.35 m2 (-13.4 %)**. Drawing-derived
vs owner manual (gross): +34.85 m2 (+24.5 %), fully explained in s.3.

## 2. The physical element (ERS s.2.1) and the segment table

ST-01 shaft, 2.50 m wide inside (printed 250 on GF / 1F / 2F; DXF inner faces 2.500 apart; the three plans stack the
shaft at the same place, inner faces agree to 1 mm). From the north inner face southward: intermediate landings 1.20
(MS1 winders + 1.20 x 1.20 landing at +3.50; MS2 landing 2.50 x 1.20 at +7.516 / +7.684), flights 3.30, then the floor
slab edge at **4.50 m** (1F / 2F printed chain 120 + 330 + 195 = 645). Below the 1F slab the GF enclosure is 5.00 m long
(printed 500) with a south wall and door; above it the arrival landings (1.95 x 2.50) are floor-slab zones open to the
void (no wall on that side: 1F / 2F plans, section A-A).

Continuity (ERS: never a wall assumed through all floors without the section showing it): section A-A (cut through
the east lane) draws no slab, beam band or ceiling crossing the void between +1.00 and the roof; the slab bands at +5.50
and +9.70 stop at the stair head; the structural GF and 1F roof slab plans put B2 along both long walls at wall width
(flush, no projection into the void) and 'B3 (With Stair)' along the north wall; the 2F roof slab closes the shaft at
+13.90. So the north, west and east faces are each ONE continuous face from the lowest floor to the roof soffit; the
open south side is not a face.

| Face (plane u, z) | Region (levels cited) | Built against it (subtracted once, as a union) | Openings |
|---|---|---|---|
| W, outer wall, u = 0 .. 5.20 from the north face | u 0 .. 1.15 from the NW floor (+0.30 / +1.00 HELD) and u 1.15 .. 5.00 from +1.00 to the roof soffit +13.90 - b - 0.16; u 5.00 .. 5.20 from +5.50 (above the GF south wall) | MS1-L side profile (+1.00 -> +2.667, Y 3.85 -> 1.15, on grade, stopped at its last riser); MS1-T winders HELD (zone Y 0 .. 1.15, +2.317 .. +3.50: the soffit cannot start below the MS1-L soffit at its last riser and the turn ends at the +3.50 landing); MS2-L profile (+5.50 -> +7.516); MS2-LD band +7.516 - b - 0.16 .. +7.516 over 1.20; 1F and 2F slab bands over u 4.50 .. 5.20; B20 (40 x 75) and B23 (45 x 75) ends HELD | W01 +2.00 .. +4.00, W13 +6.50 .. +8.80, W26 +10.80 .. +12.50 (all printed, T-144), u 1.05 .. 2.25; D115 shaft-box part 0.575 x 2.20 ASSUMED; pier returns 2 x 0.05 m x exposed height |
| E, lift-shaft wall, u = 0 .. 5.20 | +0.30 lobby (u < 1.15), D1 treads +0.475 / +0.65 / +0.825 (u 1.15 .. 2.05, solid on grade), +1.00 beyond; to the roof soffit; u 5.00 .. 5.20 from +5.50 | MS1-LD band at +3.50 (1.20); MS1-U profile (+3.50 -> +5.50); MS2-LD band at +7.684; MS2-U profile (+7.684 -> +9.70); slab bands; B20 / B23 ends HELD | GF doorless passage to the basin space 0.90 (u 2.10 .. 3.00): HELD (no head printed; Q-55 C is for doors), band bounded by +1.00 and the MS1-U soffit |
| N, outer wall, u = 0 .. 2.50 | west part from the NW floor (HELD), east part from the +0.30 lobby; to the roof soffit | winders HELD (u 0 .. 1.30); MS1-LD band (u 1.30 .. 2.50); MS2-LD bands west / east halves | court door 1.00 (frame in the DXF), +0.30 .. +2.50 ASSUMED (section A-A draws its lintel at about +2.5); 1F north window 1.00 HELD within +3.50 .. +7.524 (it crosses the 1F plan cut, so it lies between landing 1 top and landing 2 soffit); W27 1.00 HELD within +7.684 .. roof soffit |
| S, GF only, u = 0 .. 2.50 | +1.00 to the 1F slab soffit +5.34 - b | B20 over the wall HELD (section A-A draws it there; the slab plan draws it at the stair head: Q-46 clash; depth basis OQ-11) | south door 1.00, +1.00 .. +3.20 ASSUMED |

Per face (paint, HI = b 0 and NW floor +0.30 / LO = b 0.10 and NW +1.00; net_hi: held not deducted, net_lo: held
deducted): W 56.66 / 54.70 .. 55.11 / 53.15; E 63.29 / 58.83 .. 62.46 / 57.95; N 30.43 / 18.97 .. 28.90 / 17.64;
S 8.65 / 6.77 .. 8.40 / 6.52 (pier returns 1.21 inside W). Per storey band (paint, HI, gross / net_hi / net_lo; returns
not included): below +5.50 70.77 / 62.01 / 50.83; +5.50 .. +9.70 54.18 / 47.67 / 42.99; above +9.70 50.18 / 48.14 /
44.25. `SHAFT_T173.json` has every face, piece and storey band in both cases.

Flight profiles are the steps + waist (T 0.16 perpendicular, Q-47 A) between the support soffits, with the junction
wedge into the landing / slab band; they reproduce T-184's per-metre profiles (MS1-U 0.904 m2 steps + waist) plus the
junction wedges (0.97 m2 as a piece; the union removes what the bands already cover).

## 3. Reconciliation in units (ERS s.2.4)

**Owner manual 142.22 -> drawing-derived gross 177.07 (plaster, HI): +34.85, closes to 0.00 (test).**
Per storey band: GF +15.66 = 15.10 m x (4.50 - 3.65) 12.835 [no 0.60 beam / 0.15 decor / 0.10 floor at the 1F level
inside a void: the B2 beams are flush, no slab crosses] + 3.675 [the +0.30 lobby and the D1 treads: the faces start
0.70 m lower at the north end: E 0.805 + D1 0.315 + N 0.84 + NW (HI) 1.715] - 0.40 [GF south wall stops at the 1F slab
soffit 4.34, not 4.50] - 0.45 [pier returns moved from the face length to the net]; 1F +10.63 = 13.00 x 0.85 - 0.42;
2F +8.57 = 13.00 x (4.04 - 3.35) - 0.40 [under the roof the slab 0.16 is real; the owner's 0.60 beam is not (flush B2)].
The physical cause in one line: the owner formula is a ROOM formula (beam, decor ceiling and floor build-up at every
ceiling); a shaft has one ceiling (the roof) and one floor, so 2 x 0.85 m per metre of face does not physically exist.

**Q-72's three options -> this result.** (A) 136.14 and (C) 157.66 and (B) 163.93 .. 165.35 used T-128 r1 face lengths
11.94 / 13.38 / 14.25 m (r1 traced the GF shaft without its south wall and passage side and the 1F / 2F shaft with part
of the arrival-landing walls); with the r2 lengths 15.10 / 13.013 / 13.008 (T-147 region) they become 142.29, -, and
171.90 .. 173.20. r2 storey interval (paint) 173.20 -> 175.14 gross: GF +2.82 (lobby / steps +3.675, south wall -0.40,
returns -0.45), 1F -0.47 (returns 0.42 + 0.013 m of face), 2F -0.42 (returns). Gross -> net (HI): known contacts -4.98
(landing and slab bands, flight profiles: the "landing-edge bands not deducted" of r2, now measured), openings -12.33
against r2's -12.65 (+0.32; the union also keeps 0.53 m2 where W01 / W13 sit behind a flight or landing from being
deducted twice, s.5), returns +1.21: 160.55 + 1.94 - 4.98 + 0.32 + 1.21 = 159.04 -> 159.03 (rounding).

**Freelancer 204.42 -> 177.07 gross (-27.35), closes to 0.00 (test):** south side +20.11 (his box counts a 2.40 m south
wall over 12.90 m; the drawings have a south wall only at GF under the 1F slab, 10.85 m2; above +5.50 the void is open
to the arrival landings); his second row 2.50 x 5.40 = 13.50 matches no face of the drawing (UNEXPLAINED RESIDUAL,
named: a 2.50 m face exists only as the GF south wall, already in his box); north -2.64 (his width 2.40 vs printed 2.50
and his +1.00 start vs the +0.30 lobby, against his 12.90 vs our 13.44 .. 12.74 height); west / east -3.62 (his 5.00 x
12.90 x 2 vs the faces to 5.20 under the slabs, the lobby / steps and the roof soffit 0.16 below the +13.90 mark). He
deducts no landing, flight or slab band.

## 4. Held (never 0) and what closes each

| Item | m2 (paint) | Closes with |
|---|---|---|
| 1F north window head / sill | up to 3.92 | designer: sill / head (section A-A draws glazing at about +5.6 .. +7.36, scaled, not used) |
| W27 head / sill | up to 5.96 | designer (section A-A about +9.75 .. +11.25, scaled, not used) |
| GF doorless passage to the basin space, head | up to 3.81 | designer (a lintel line only) |
| Winder turn MS1-T against W and N | up to 2.90 | consultant C-ST-3 (winder soffit, T-184) |
| B20 / B23 ends at the stair head; B20 over the GF south wall | up to 1.44 + 1.88 | Q-46 RFI (beam position), OQ-11 (depth basis) |
| NW floor under the winders (+0.30 or +1.00) | 1.71 (gross, in the HI / LO spread) | designer: level under the winders (no edge drawn) |
| Roof datum, build-up b (0 .. 0.10) | in the HI / LO spread | DCR-6 / DCR-7 |

## 5. Findings for the designer list (no quantity changed beyond the union)

- C-SH-1: W01 (sill +2.00) lies 0.33 .. 0.67 m below the MS1-L flight that runs along the west wall across it (flight
  top +2.33 .. +2.67 over the window width), and W13 (sill +6.50) below MS2-L and the MS2-LD landing (+7.36 .. +7.52):
  the stair side crosses the lower part of both windows (0.21 + 0.32 m2 of overlap, deducted once). Confirm the window
  sills or the stair-side detail at the glazing.
- C-SH-2: the GF floor under the winders (+0.30 lobby or +1.00) is not drawn.
- The 1F north window and W27 are drawn in section A-A but their sill / head are printed nowhere (scaled candidates
  only, listed in the input file, never a quantity).

## 6. Who is right (proposals for the Checker)

- Freelancer vs drawing: ENGINE (this ledger) RIGHT on scope: the south side of the void above GF is open (1F / 2F
  plans, section A-A); his 2.50 x 5.40 row is UNRESOLVED (on no drawing). RULE_DIFFERENCE on deductions (half vs full,
  Q-73 confirmed full, subject to the physical construction scope).
- Owner manual vs drawing-derived: not a who-is-right case; both columns kept (ERS s.2.2). Recommendation for the BOQ
  line: the drawing-derived net (the physically built face), the owner column displayed beside it; no owner question
  is needed (s.2.7: the drawings establish the geometry; the open items are designer items).

## 7. General rule (proposed, any villa; research provenance; a rule change is a new rule version)

R-SHAFT-1: a wall face of a stair shaft or any multi-storey void is ONE face from its lowest finished floor to the
first soffit above it, only where the sections show no slab, ceiling or projecting beam crossing it (beams flush with
the wall are part of the face); every element built against it (landing and slab edge bands, flight side profiles,
beam ends) and every opening is subtracted once, as a geometric union in the face plane; an open side of a void is not
a face; a room-height formula is applied only to faces with a ceiling at that storey, and where an owner room method
exists it is shown beside, never replaced.

Regression test `tests/t173_shaft` (synthetic Villa R, hand values in the docstring): normal (band, window, flight
profile 0.492843 m2, storey split, mirror / reversed frame, pier return); adverse: a shaft closed by a slab at one
level (34.80 vs the continuous 35.40, continuity_check names the slab); an open side counted as a box wall (+17.70);
a window crossing a flight deducted once; held items as ranges, missing riser / unit / status refused; the
development-villa run reconciles to the owner column and to the freelancer to 0.005 m2.

## 8. Lessons-register row proposed (ERS s.7)

| 2026-10-22 | Stair shaft walls 136.14 / 157.66 / 163.93 m2 offered as options; freelancer 204.42 | Storey-interval and room-height shortcuts measured a void like rooms (beam, decor, floor allowance at floors that have no slab) and a box perimeter counted the open side of the void; landing / flight contacts never subtracted | R-SHAFT-1 (s.7): one face per wall from the lowest floor to the first soffit where no slab crosses; contacts and openings subtracted once as a union; an open side is not a face; the owner room formula shown beside (any villa) | tests/t173_shaft (adverse: a slab crossing the shaft; the open side as a box wall; a window behind a flight) | proposed (T-173 READY) |
