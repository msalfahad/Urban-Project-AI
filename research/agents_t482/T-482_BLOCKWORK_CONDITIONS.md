# T-482: blockwork wiring conditions (F-T449-R3-1 .. 4), training villa; method every villa

Worker 3, 2026-11-03, run session_01E6cPndqtv59XppUY4VBCWC. Lane A research (backlog-permitted). Files:
`research/agents_t482/*`, `tests/t482_blockwork_conditions/*` only. No candidate, engine, rule / knowledge version or
registry file changed; no candidate or released line moves (unwired). Drawings cited by Drive title and handle only.

## Sources read this run (own reads, private folder only)
- Drive 'Alsenan chalet project' / `ST7757 dxf.dxf` (sha 9f9d1179): every TEXT / MTEXT / ATTRIB / block text searched
  for a level, 'roof', S.S.L / T.O.S, screed, insulation, fall. Levels printed: +0.15 / +0.30 / +1.00 (ground
  sheets), two '+9.70' (LEVEL 3F4, 3F6) and block 'ROOF' (insert 3AE) on the SECOND FLOOR ROOF SLAB sheet (block
  SFRS, insert A8). Rendered: both '+9.70' and 'ROOF' sit on the 1F-roof terrace OUTSIDE the penthouse plate; the
  penthouse plate (beams B1 B2 B3 B7 B8 B15, tank slab 'T 18') prints NO level. Same on `ST7757.pdf` p.6 (raster read).
- `ST7757.pdf` p.14 'TYPICAL DETAIL OF PARAPET SECTION' (P1): RC upstand '30' above the slab, note 'MUST BE MORE THAN THE
  HEIGHT OF ROOF FINISHING'.
- `P7757_DXF_COMPRESSED.zip` -> `P7757.dxf` (sha ab54dd55): 1F roof parapet inner face 12A7 LINE 11.600 m, direction
  90.00 deg (straight); 0.20 wall line 12A5 5.6871 + 131C 1.0052 + 131B 4.8077 m, all straight.
- Merged: T-214 (drawn 0.05 floor build-up), T-248 / T-220 (one plate per structural slab plan), T-200, T-215
  (T215_ENDS.csv), T-277 (D-27), T-311, T-324 (C3, C5), T-449 r3 register (built here, byte-identical).

## (1) F-T449-R3-1: one roof datum basis (R-MAS-ROOF-DATUM-1)
Physical element: a block wall rises from the structural top of the plate under it to the soffit of the member over it
(Q-60 A); the soffit hangs from the structural top of the plate ABOVE. Basis for every trade (walls, columns, parapet
solids): the top of a plate.

| Plate (structural sheet) | Zones | Top | Status |
|---|---|---|---|
| ground slab | GF FFL +1.00, drawn 0.05 | +0.95 | DRAWING-CONFIRMED (T-214) |
| GFRS (p.4), one plate | 1F FFL +5.50 drawn 0.05 + GF terraces +5.50 | +5.45 | DRAWING-CONFIRMED |
| FFRS (p.5), one plate | 2F FFL +9.70 drawn 0.05 + 1F-roof terrace +9.70 | +9.65 | DRAWING-CONFIRMED |
| SFRS (p.6), roof only | main roof +13.90 (finished, A-A) | +13.90 - b_r | **HELD (D-39)** |
| annex roof, roof only | +4.30 (finished, B-B) | +4.30 - b_r | **HELD (Q-54 B / D-39)** |

Storeys: GF 4.50 = 5.45 - 0.95 and 1F 4.20 = 9.65 - 5.45 are STRUCTURAL (the terraces share their floor's plate, so
the roof zones on GFRS / FFRS need no roof build-up). 2F: 4.20 is the architectural finished chain +9.70 -> +13.90 and
equals 13.90 - 0.05 - 9.65, i.e. it silently takes the floor build-up 0.05 for the roof (FINISHED_AS_STRUCTURAL,
refused). The 2F structural storey is 4.25 - b_r with b_r unprinted.

Effect on the 9 2F MAS.BLOCK walls (V3.0.26 fill, L-lines as T-449): each closable wall becomes ROOF_DATUM:
U - L x b_r (U = net at b_r = 0, an upper bound, never a quantity; L = closable length). For all 8 the carried figure
= U - 0.05 x L exactly (residual 0.0000 m2): the carried 4.20 IS the b_r = 0.05 what-if.

| Set | Carried m2 | U at b_r = 0 | L m | U - L x b_r |
|---|---|---|---|---|
| VALUED 4 (W01 6.84, W04 21.476, W06 14.82, W08 9.64) | 52.776 | 53.5225 | 14.925 | 53.5225 - 14.925 b_r |
| PART 4 (W02, W03, W05, W07: established parts) | 45.6015 | 46.330 | 14.570 | 46.330 - 14.570 b_r |
| HELD 1 (W00) | held | held | - | held (never 0) |

Proposed: 2F MAS.BLOCK / ARCH.WALL_PANEL / ARCH.WALL_VOLUME of those 8 walls from VALUED / PART to HELD ON ROOF DATUM
(D-39), same form as R-MAS-DROP-1; 52.776 m2 leaves the determinate total of the 2F line until b_r is printed. Concrete:
the round-1 columns held at an undeclared roof datum (13, T-449 r1; 2F and annex, T-248) are HELD on the same two
roof-only plates: one basis, both trades.
Beside, NOT applied: P1 note gives b_r < 0.30 at a P1 edge (-> 2F wall U - 0.30 L as a floor), but P1 is not keyed to
the main roof and where +13.90 is read (falls) is not printed. Annex walls could carry U - L x b_r over +0.25 -> +4.30
(upper storey 4.05) the same way: not done (they stay HELD as today).

## (2) F-T449-R3-2: GF-W22 low end (R-MAS-WIDTH-CONFLICT-1)
Physical cause: CB2 (BM-GF-055) width CONFLICT D-27, schedule 0.20 vs drawn 0.25 (handles 278 / 274); the drawn band's
inner face lies 0.049 m over the G-T108-1 junction piece (T-215). Readings: drawn 0.25 -> 12.9311 m2 (band over the
strip, h 4.00); schedule 0.20 on the drawn outer face -> 12.9439 m2 (slab, h 4.34). Width 0.0128 m2 (0.10 %). V1 rule
with no CB2 piece 12.94405 = the schedule end + 0.00015 (4 dp length rounding). Carried 12.9311 DRAWING-CONFIRMED is one
end (refused: CONFLICT_ONE_END, Q-61 C(1)). Proposed: GF-W22 = CONFLICT [12.9311, 12.9439] m2 (volume [1.939665,
1.941585] m3), held by name D-27. GF-W34 (DROP): U = max over readings 10.4121 (carried 10.3982, +0.0139); its d
coefficient (1.7231 carried vs 1.7827 rule) stays open for the T-288 re-clip.

## (3) F-T449-R3-3: parapet NW-2 (R-MAS-PARAPET-RUN-1) and (4) NE-6x
The roof plan draws the 1F sea-side parapet straight (12A7 11.600 m, own read AGREE T-324 C3); 3.6107 m was the 1F
floor outline's bay arc ((3.6931 + 3.5283) / 2). Block alternative on the roof-level run: [0, 3.1672 x (1.30 - 0.30)]
= [0, 3.1672] m2; reconciliation -0.4435 m2 = (3.1672 - 3.6107) m x 1.00 m, all from the run length. NE-6x (T-324 C5):
[0, 0.25999] m2 owed (1.29995 x 0.20), beside.

## Engine vs freelancer
No like-for-like: the freelancer's roof-storey walls use 3.45 / 3.70 heights from his own datums (workbook rows, not
an input). 2F walls: engine U 53.5225 - 14.925 b_r (VALUED set) remains HELD; verdict UNRESOLVED on D-39.

## Rules, tests, lessons
Rules: `blockwork_conditions_v1.py` (BLOCKWORK_CONDITIONS_V1, research version; V1 imported read only). Tests:
`tests/t482_blockwork_conditions` (VILLA-SYNTH-482 hand fixture: U 11.595, L 4.50, b_r 0.10 -> 11.145; adverse: FFL
chain under a roof, constant roof build-up, one plate two tops, mm-as-m, one-end conflict, floor-outline run; Alsenan
regression from merged files). Lessons row (proposed, ERS s.7): 'A storey under a roof whose plate carries no floor
zone has no structural storey until the roof build-up is printed; a roof zone on a floor plate takes that plate's top.
Carry U - L x b_r, never the finished chain (T-482).'
