# T-016b: the 14 EXPLAINED_UNVERIFIED changes V2.8 -> V2.9, checked by hand on the drawing

Worker 1, 2026-10-20 11:25-12:10 UTC. Docs only; no engine, tool, rule or test file changed. Rules: UP-QA-001,
UP-WALL-GEOM-001, UP-QTY-STATUS-001, owner Q-07 (b), Q-54 (open), Q-60 (A, 10:45 UTC today). The table is
`V28_V29_CHANGES.csv` (one row per change). No drawing coordinates, client names or images are committed: positions are
given as entity handles and as distances inside the drawing.

## Result

| Change (V2.8 -> V2.9) | Count | Hand result |
|---|---|---|
| GF ARCH.FACADE_RUN 98.886694 m | 1 | **CONTRADICTED**: hand 105.786694 m (engine -6.900 m, -6.5 %) |
| ARCH.FACADE (facade + plinth), GF / 1F / 2F, held | 3 | VERIFIED (hold right); 1F and 2F heights now printed-and-bound by hand (4.20 m each) |
| FIN.EXT.FINISH, GF / 1F / 2F, held | 3 | VERIFIED (hold right: no exterior finish printed) |
| ARCH.WALL_PANEL + ARCH.WALL_VOLUME, GF / 1F / 2F, held | 6 | VERIFIED for V2.9 (no masonry height in the plan); reason superseded by owner Q-60 A today |
| ARCH.WINDOW_REVEAL 1F curved window COP-001, held | 1 | **CONTRADICTED (hold reason)**: the NW elevation prints the sill at the floor |

12 VERIFIED, 2 CONTRADICTED. With T-016a's head start (2F run VERIFIED by hand, 1F run CONTRADICTED +0.160 m) every one
of the 20 V2.8 -> V2.9 differences is now classified by hand. Everything below is unchanged in the released
ARCH_TAKEOFF_V2.11 (same Mode A run: GF run 98.886694, COP-001 lines identical).

## Reproduction

Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, DXF sha256 ab54dd554c31...ed31cc4 (= manifest); working head
42123d8; `tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V2.8` and `V2.9` with `--facts
research/urban_m9_s2/SYNTHETIC_FACTS_S2.json --layer-roles 1=WALL D=DOOR W=WINDOW S-COL.BON=COLUMN`;
`tools/arch_change_verify.py` -> 20 differences: 5 VERIFIED, 14 EXPLAINED_UNVERIFIED, 1 CONTRADICTED (= the N10 report).
Hand reading: my own short ezdxf scripts on the raw DXF (no engine import) and the scanned sheets p7757_arch_sheet03.pdf
(GF plan) and Alsenan_Architectural_P7757_Pages_07-08.pdf p.8 (NORTH WEST ELEVATION).

## 1. GF facade run: 98.886694 m (engine) vs 105.786694 m (hand)

### 1a. Edge by edge, the ring arithmetic is right

The engine ring has 295 edges. For each straight edge I looked for raw DXF lines lying on it (collinear within 1.5 mm).
Every edge is on a drawn line except three closures; the two arcs are drawn arcs:

- west corner: ARC 10D, layer 1, R 1.300 m, 90 deg: 2.042035 m (the ring's 41 chords give 2.0418);
- curved pool glazing: frame polyline 280, layer W, R 2.330 m, 163.716 deg: 6.657684 m (centre = the pool's centre,
  the glass runs 0.08 m outside the pool coping R 2.250);
- straight edges: 90.186975 m, every opening closed on the face line between its jambs (16 openings, 23.741418 m).

Re-added: 90.186975 + 2.042035 + 6.657684 = **98.886694 m = engine**. The three closures without any line under them:

| Ring edges | Length | What the drawing shows |
|---|---|---|
| OP-007 (north, court side) | 1.200 | nothing: the open end of a 1.20 m passage between two columns (2FB1, 2FAE) |
| OP-001 part 1 (south) | 1.200 | two layer-5 lines 105 / 106, 0.20 m apart: the boundary wall closing the passage |
| OP-001 part 2 (south) | 0.200 | nothing: the outer face line 85 stops 0.20 m short of the jamb line A3 (drafting gap in a wall end) |

### 1b. The 1.20 m passage between the annex and the house is outside (main cause, +7.000 m)

Two of the three closures bridge the same space: a 1.20 m wide strip between the annex east wall (lines A2 / A3, layer 1)
and the house west wall (9F, 3BE, A0, 3CB, A1), 4.90 m long. The drawings say it is an open-air side passage:

- the GF plan (sheet 03, read at 200 dpi) prints **+0.15** inside it, the same level as the court (owner, 21:40: "the
  whole court is +0.15"); the annex beside it is +0.30 and the pantry +1.00 (also printed);
- the court end has no line at all (no door, no window, no threshold); the other end is the 0.20 m boundary wall that
  runs along the neighbour side;
- the annex W.C. door (block D120, 0.90 leaf) opens onto it, and the house wall has two windows facing it (layer-5 face
  lines 3BE 1.50 m and 3CB 1.00 m, frames on layer W in the inner 0.12 m);
- the engine itself has two unlabelled spaces there, GF 3.60 m2 and 1.56 m2 (T-099's held "unlabelled rooms").

So the passage walls are exterior walls. Hand run = engine - 1.200 (court-end closure) - 1.200 (boundary wall walked as
if it were the building) + 4.700 (house face, from the boundary wall's inner face to the court) + 4.700 (annex face) =
**105.886694 m**. The 0.20 m wall end on the boundary stays in the run (the engine counts the whole boundary face).

### 1c. The 80 x 50 mm pocket at the curved glazing (-0.100 m, D-N10-01 pattern)

The curved pool glazing sits in a 0.20 m wall gap whose outer face line is drawn on layer 5 at both ends (lines 96 and 95,
0.264 / 0.214 m long). The frame (layer W, four lines 27D, 27E, 27F, 280) fills only the inner 0.12 m; the outer 0.08 m is
open, the same detail as the 1F window of D-N10-01. At the south end the ring steps 0.08 m once (no extra). At the north
end column 2F87 stands 0.05 m proud of the wall face, so the ring walks up 0.05, across 0.08 (line 274) and down 0.05
before it reaches the frame: 0.18 m where the face-line closure gives 0.08 m. **-0.100 m.** The walk itself follows drawn
lines; it is the D-N10-01 convention (close the open reveal at the face line) that removes it, as in the 1F verdict.

**Hand GF run = 105.786694 m.** Split by block (for the facade heights below): annex (west of the passage) 34.242035 m =
6.70 + 3.10 + 2.042 + 0.50 + 6.40 + 4.70 + 0.20 + 10.60; main house 71.544659 m.

Facade openings change with it: OP-007 (1.20) and OP-001 (1.40) are not building openings; the passage faces add the two
house windows 1.50 + 1.00 and the annex W.C. door 1.00 (frame 0.05 + 0.90 + 0.05): facade openings 23.741418 -> 24.641418
m, solid face 75.145276 -> 81.145276 m (+6.000).

Side findings (released V2.11, Mode A):

- **ARCH.PASSAGE 2 nr released** (GF OP-007 and OP-001, SOURCE_DERIVED): neither is an opening of the building (one is the
  open end of an outdoor passage, the other a boundary wall). Hand: 0 nr.
- **OP-001 width 1.40 m** includes the 0.20 m drafting gap in the annex wall end; the opening in the boundary wall is
  1.20 m (jamb lines A3 / A1).
- The two spaces GF 3.60 + 1.56 = 5.16 m2 (T-099 UNRESOLVED) are this outdoor passage at court level: exterior paving, not
  an interior floor (the passage is 1.20 x 4.70 = 5.64 m2 between the boundary wall and the court).
- Freelancer: he measures exterior plaster + sigma per elevation, not per floor run (gross 1502.84, deducted 32.87, net
  1469.97 m2, "المساح الخارجي مع السجما"); no row names the passage, so the run cannot be compared line by line.

Verdict proposal: **CONTRADICTED, HAND_RIGHT** on the run (-6.900 m, -6.5 %): an opening into a space whose printed
level is the outside level must not be closed; the open reveal is closed at the face line. Both are facade-gap cases
for **T-014** (D-N10-01 / D-N10-02 scope), with this passage as a second hand fixture.

## 2. The 13 held lines: is the hold right on the drawing?

### ARCH.FACADE GF / 1F / 2F (facade area and plinth): hold right, inputs now readable by hand

V2.9's reason "no section band of this floor gives the next floor's F.F.L." is true of the method (it binds no section to
a floor, T-013), but the inputs are printed. Owner Q-07 (b): slab top to slab top. Printed levels (sections A-A sheet 10
and B-B page 11, plan marks; T-088 hand table, re-checked on the DXF level texts +1.00 / +5.50 in the section band and
+5.50 / +9.70 on the 1F and 2F plans):

| Floor / block | Slab to slab | Hand run | Gross facade candidate | Status |
|---|---|---|---|---|
| GF main house | +1.00 -> +5.50 = 4.50 | 71.544659 | 321.95 m2 | held: the stair hall is partly +0.30 (its face is 4.50 or 5.20) |
| GF annex | +0.30 -> +4.30 = 4.00 if +4.30 is the slab | 34.242035 | 136.97 m2 under Q-54 A | held: owner Q-54 open |
| 1F | +5.50 -> +9.70 = 4.20 | 63.008865 (engine 63.168865) | 264.64 m2 (engine run 265.31) | readable; waits on T-031 |
| 2F | +9.70 -> +13.90 = 4.20 | 29.800 | 125.16 m2 | readable; parapet above +13.90 separate |
| Plinth (below the lowest F.F.L.) | +1.00 / +0.30 down to outside: court +0.15 printed, street and neighbour ground not printed | 105.79 | - | held: right |

Classification: **VERIFIED (hold right)**, reason text to be replaced by T-031. Openings are not deducted here (their
heights are mostly unprinted, T-083 / Q-55).

### FIN.EXT.FINISH GF / 1F / 2F: hold right

No sheet prints an exterior finish (T-091 census of every note; my search of the 268 decodable DXF texts for plaster /
paint / stone / cladding / marble words, English and Arabic, finds none; the 51 texts in the unmapped Arabic SHX font are
not decoded). VERIFIED.

### ARCH.WALL_PANEL / ARCH.WALL_VOLUME, 3 floors (6 changes, 10 lines: GF 0.15 / 0.20 / 0.40, 1F and 2F 0.15 / 0.20)

The architectural DXF prints no T.O.S. or beam soffit, so the hold is right for V2.9. Since 10:45 UTC today the owner's
Q-60 answer is A (each wall to the underside of the beam above it from the ST7757 schedule, or of the 0.16 slab where no
beam runs), and the slab-to-slab heights are printed (4.50 / 4.00 / 4.20 / 4.20): the reason is superseded. Example on
the owner's terms: a GF main 0.20 wall under a 0.75 beam is 4.50 - 0.75 = 3.75 m high, under slab only 4.34 m. VERIFIED
(hold), with a proposed task: block m2 / m3 = MASONRY_CENTRELINE_V1 metres (T-027) x the Q-60 A height per wall.

### ARCH.WINDOW_REVEAL, 1F curved window COP-001 (0.502392 m2 measured, held): the hold reason is answered

The plan prints no sill, which is what V2.9 says. The NORTH WEST ELEVATION (Pages_07-08 p.8, 200 dpi) prints the chain
**430 / 20 / 305 / 45** on the pool axis from +1.00: the GF glazing 4.30, the 0.20 slab band (hatched, continuous with
the 1F floor line), then the 1F window 3.05 to the arch and 0.45 to its crown. The window bottom sits on the slab band
at +5.50 = 1F F.F.L.: **the window reaches the floor**, so the strip's floor status is set by the drawing (the same chain
T-083 used for W17). Geometry by hand: wall band R 1.935-2.135 (arcs BCD / BCE / BD0 and BD1 / BD2 / BD6), frame arcs
R 2.015, 2.055, 2.095 (layer W); the open strip outside the frame is 0.5 x 1.538320 x (2.015^2 - 1.935^2) = 0.24305 m2
(engine piece 0.243138); the other three engine pieces (0.126728, 0.126525, 0.006001) lie between the frame lines.
Classification: **CONTRADICTED (hold reason)**; no quantity was released, so no BOQ number is wrong today.

Side finding (traceability): both COP-001 lines (ARCH.WINDOW 1 nr and this reveal) cite as their source the entities of
1F **OP-001**, a straight 0.60 m window in another room (handles CFB ... D05), not the curved arcs. Unchanged in V2.11.

## Proposed follow-ups for the Lead

1. **T-014 (facade gap closure)**: add two hand fixtures from this note: an outdoor side passage at the court level
   (Alsenan GF: +7.000 m) and the 80 x 50 mm reveal pocket beside a proud column (-0.100 m).
2. **Openings / passages**: ARCH.PASSAGE counts 2 nr that are not building openings (GF OP-007, OP-001); OP-001's 1.40 m
   includes a 0.20 m drafting gap (hand 1.20 m). Fix with T-014's passage rule.
3. **Curved openings source trail**: COP-001 lines cite OP-001's entities (new output version; no quantity change).
4. **Masonry m2 / m3** on Q-60 A: T-027 metres x per-wall heights from the beam schedule (new task).
5. **T-031** (facade height, Q-07 b): 1F 264.64 and 2F 125.16 m2 gross are ready by hand; GF waits on Q-54 and the
   stair hall level.

## Not covered

- The 1F run (CONTRADICTED +0.160 m) and the 2F run (VERIFIED) are T-016a's, not re-read here.
- The side of the glass of the three COP-001 frame pieces was not re-traced.
- The 1F ring was not checked for an outdoor passage; the 1F floor spans over the GF passage (a 1F bathroom sits above it).
