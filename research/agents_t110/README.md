# T-110: Alsenan beam member register, member by member (owner Q-61 = C)

Worker 3, 2026-10-20. NO REPO CODE task. **EXECUTION NOT VERIFIED** for repo code: this run's freeze check
(`tools/freeze_verify.py check`) was refused by the session permission check ("[Code from External]"), so nothing in
the engine was changed or run. Everything below is hand reading of the drawing, helped by the small scripts in
`scripts/` (census of texts and lines, schedule rows, band widths, label binding, uncovered lines) run on a scratchpad
copy of Drive "Alsenan chalet project" / "ST7757 dxf.dxf" (sha256 9f9d1179...38079, the verifier's file). No drawing
file and no client data is in this folder. Coordinates are drawing metres (the DXF is in mm).

Engine band list used as the starting census: the committed route G run
`research/urban_engine_m4_correctness/st7757_route_g/` (PROVISIONAL_REGISTER.csv: 112 released beam spans 64.820 m3;
UNRESOLVED_CONCRETE_EXCEPTIONS.csv: 24 held spans). Its overlay polygons (overlays/SH0x_*.svg) were mapped to drawing
metres by a fit on the 24 held spans that carry metre centres (max error 0.0006 m), then every span was checked
against the drawing by this run's own measurement, not the engine's.

## Result (gross beam concrete B x clear length x D, the route G basis)

`BEAM_MEMBER_REGISTER.csv`: **137 span records in 118 members** (GF 61, 1F 39, 2F 18), one row per span, each with
member id, floor, location (x, y), type, b x h, length, governing section, schedule row, m3, status, evidence and
conflict record. Status words: owner directive 2.2.

| Status | Records | m3 | Freelancer beams 65.97 m3 |
|---|---|---|---|
| CALCULATED | 111 | **64.764** | -1.206 m3 (-1.8 %) |
| CONFLICT (two documents disagree, both volumes) | 7 | 5.123 / 6.086 | not compared |
| HELD (candidate range, never 0) | 19 | 4.123 .. 8.553 | not compared |
| HELD, depth not printed (projections the engine has no band for) | 3 | plan 1.78 m2, no m3 | not compared |

Released engine today (route G): 64.820 m3 (-1.150 m3, -1.7 %). The two totals are close by chance: 5.022 m3 the
engine releases is CONFLICT here, and 10.855 m3 settled by the drawing is not released by the engine yet
(GF B26 / B27 one span 3.905 + 3.787 instead of 5.606 released, B7 strip 0.255, B20 / B23 west spans 0.900 + 1.0125
by the printed sections, upstands 0.240, west dome ring 0.755 instead of 0.281).

## Checks made this run (all on the drawing)

1. **Schedules read from the drawing**: simple beams B1-B29, CA, B.W, SB1-SB3; continuous CB1-CB13 (2-span and
   3-span tables, with their printed spans). Every one of the **119 beam labels** on the three roof-slab plans sits on
   a record (0 labels lost). Schedule rows on no slab plan: B10, B12, B.W (and SB1-SB3, the strap beams).
2. **Width of every straight span re-measured** from its two edge lines (layer 1 / 5): 103 released spans have drawn
   width = schedule width and a parallel label of their own (99 straight spans measured; the 4 released void-ring arc
   pieces were not re-measured). **Five released spans do not** (new finding, below).
3. **Length re-measured by hand on 5 released spans** (GF B22 7.80, GF CB7 11.80, 1F B25 6.875, 1F B18 6.30,
   2F B7 6.60 m): all = engine. The other lengths are the engine's (not re-measured).
4. **Lines no engine band covers** (layer 1 / 2 / 5 on the slab frames): stair treads, the section drawings, single
   facade lines 0.075 m off a beam face (not a band), and **three projection pieces the engine never measures** (below).
5. **Dome rings re-measured as geometry**: west ring (centre 16.380, 41.651; R 2.211 / 2.411) inside the box CB10
   inner face 14.269 / CB13 face 18.369 / B6 faces 39.440 and 43.862 = 1.5105 m2; east ring (centre 30.828) inside
   B25 face 28.617 / CB12 face 32.989 / the same B6 faces = 1.7993 m2. Both equal T-097.

## Findings for the owner and the designer

- **Five released spans are the CB10 case** (schedule width differs from the drawn width; the engine releases them at
  the schedule width, exactly what owner Q-61 C(1) forbids): GF B29 (schedule 25, drawn 0.200 over 6.74 m: 1.264 /
  1.011 m3), GF CB2 both spans (schedule 20, drawn 0.250: 0.682 / 0.853), GF B21 (schedule 45, drawn 0.400 on the
  inclined band: 2.525 / 2.244), 1F B6 vertical span (schedule 25, drawn 0.200; the four other B6 spans are drawn 0.25:
  0.552 / 0.442). With CB10 (0.744 / 0.893) the CONFLICT set is 5.123 (drawn) .. 6.086 m3 (schedule; neither is "the
  conservative one"). Designer request D-27.
- **East dome ring has no B4 mark**: within 3.2 m of it only B6, B25 and "SEE DETAIL" are printed; the west ring has two
  B4 texts. Owner Q-61 C(3): B4 only where identified as B4, so the east ring is HELD (candidate 0.900 at B4), the west
  ring CALCULATED 0.755. T-097 had released both through the Q-44 A rule. Designer request D-28.
- **The 0.20 outer strips are the "projections" of the printed slab note**. Note 1 on each slab sheet, typed with an
  Arabic keyboard map ("ugD Hglrh,G l'hfrm jthwdG Hg]v,M , Hgfv,>HJ / Hglulhvdm rfG jktd`ih"), reads "the contractor
  shall match the details of the parapet and the projections to the architectural drawings before executing them",
  next to "CHECK ARCHITECTURAL DETAIL OF PARAPET, BEFORE CASTING". The outer strips round the roof edges (north of
  B20 / B23, the 1F west strip, the strip and box outside CB12, the SE box) all end in rounded corners, which a beam
  does not have: a projection whose section is in the architectural details, not a beam of the schedule. They stay
  HELD (never excluded: Sections A-A / B-B draw only the beam outline, with no slab on either side, so they do not show
  that nothing is north of the beam: owner Q-61 C(5) "exclude only if conclusive"). Designer request D-26.
- **Three projection pieces the engine has no band for** (silent today): GF outer west strip 0.20 x 4.10 m (plan
  0.820 m2, the GF twin of the 1F west strip), 1F 0.10 strip outside CB12 over 5.69 m (about 0.569 m2), 1F rounded
  box outside CB12 about 0.40 x 1.00 m (about 0.39 m2). Depth not printed: HELD, no m3.
- **CB10 (D-02) re-read**: the 0.30 inner strip carries 0.20-wide columns flush with its outer face; its mirror CB13 is
  printed 30 = drawn 0.30; no section, elevation or detail on the structural set cuts CB10; the 0.20 outer projection
  strip lies against it. Nothing on the structural drawings says whether 0.30 is the structure: CONFLICT, both volumes.
- **GF CB3 span 2 / "B3 (With Stair)" (D-03)**: CB3 is printed under each of the band's three spans and its row prints
  three spans (3.4 / 3.3 / 3.8 m), which supports CB3; B3 + "(With Stair)" is printed 0.15 m above span 2. HELD:
  B3 0.212 or CB3 0.3975 m3, never both (0.610).
- Observation for the column task (T-119): spans cut at a column are measured to the column face, but GF CB7 runs
  through its middle column (0.40 m inside the 11.80 m band, not a support box of the route); the column-beam joint is
  therefore inside the beam on CB7 and in no beam elsewhere. The joint rule URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1 /
  URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1 decides who owns it; not changed here.

## Verdict proposals (for the verifier)

- GF B26, B27, B7 strip, B20 / B23 west spans, upstands, west ring: ENGINE_RIGHT once wired (hand above, T-043 /
  T-097 / T-102); today's released engine is wrong on them (5.606 instead of 7.692 for B26 + B27, etc.).
- Five width conflicts and CB10: UNRESOLVED (designer D-27 / D-02), engine wrong to release at the schedule width.
- East ring: UNRESOLVED (D-28); T-097's 0.900 release is not allowed by Q-61 C(3).
- Freelancer 65.97 vs CALCULATED 64.764 m3: not a verdict: 7 CONFLICT and 22 HELD records are outside both totals.

## Not done / uncertain

- Lengths of 106 released spans are the engine's (5 re-measured). The verifier re-measures 3 more.
- Beam basis is gross (B x L x D, the route G and freelancer-comparison basis); the downstand basis (D - t) of
  URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1 needs the slab thickness per panel and is not computed here.
- The architectural parapet / projection details were not read (the architectural set is a separate download).
