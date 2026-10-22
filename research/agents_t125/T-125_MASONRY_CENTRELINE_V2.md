# T-125: MASONRY_CENTRELINE_V2 - open floor split, doorways at free ends, curved glazed bays, glazed lines, Q-69 B lengths

Gate 2 (blockwork), lane A. Worker 2, 2026-10-21. New piece `engine/source/masonry_centreline_v2.py` (NOT wired: no
released quantity moves; V1 `masonry_centreline.py` untouched and reused for every junction rule). Drawing: Drive "Alsenan
chalet project" / P7757_DXF_COMPRESSED.zip -> P7757.dxf, sha256 ab54dd55...31cc4 (= manifest), decoded in the session
scratchpad only. Wall stage: ARCH_TAKEOFF_V2.12 (V2.9, the released method, gives the same walls, openings and V2 figures,
checked). Rules: UP-WALL-GEOM-001 (centreline run), UP-COL-ORIENT-001, UP-QTY-STATUS-001, owner Q-60 A (heights: T-108),
Q-65 C (parapets / fence HELD, not in this piece), Q-69 B CONDITIONAL (five lengths). Local metres only (origin = lower-left
corner of each floor's wall centrelines).

Files: `alsenan_v2_dump.py` (captures one arch run's wall-stage inputs into the scratchpad), `alsenan_v2_run.py` (V1 and
V2 on them), `t125_compare.py` (these tables), `V2_VS_V1_VS_HAND_BY_RUN.csv` (every T-117 pair: V1, V2 run / openings /
physical, T-103 hand run / openings / solid, cause and verdict proposal), `V2_TOTALS_BY_FLOOR_THICKNESS.csv`,
`V2_STRETCHES_AND_EVIDENCE.csv` (every undrawn stretch V2 judged and what bridged it, every doorway, bay, glazed line and
held piece).

## 1. What V2 does (general rules, no project constant)

1. Undrawn split: along every band, stretches where neither face is drawn on a wall-role layer stay in the run only with
   evidence: a column (cut later), a crossing band, a door / window record, a passage with a head line or a symbol block
   (at most 3.0 m wide), or glazing in the band. Anything else splits the band (listed). V1's OPENING_GAP rejoins only
   with evidenced openings.
2. Doorway at a free end: carried to the near face of the wall across when a door record or a swing (leaf 0.5..1.3 m,
   leaf <= gap <= leaf + 0.25 m) sits in the gap and nothing else (column, parallel band) does.
3. Curved glazed bay: concentric glazing arcs whose chord covers an undrawn stretch replace it; the glass mid circle is
   carried to the wall centreline (as an L corner meets at the centrelines); a curved masonry stub on that circle is
   absorbed once into the bay (masonry, not glass).
4. Glazed lines standing alone (straight or curved glazing sets, >= 1.0 m, outside every band): listed, family not drawn,
   never added to a block family, never dropped.
5. A crossing drawn through by both walls: split both there and V1's cross rule decides (one family: once; two: HELD).
6. Five Q-69 B lengths per run: (1) architectural run, (2) physical blockwork at the plan cut = (1) less every opening /
   doorway / glazed stretch in the run, (3) glass / aluminium, (4) masonry above / below openings HELD (heights: T-108),
   (5) net area inputs (physical metres + the openings with widths, height HELD). (2) + openings = (1) on every run.
7. Checks: plan identity sum(run x t) = union of the run strips (junction ends carried to the other wall's far face,
   columns cut): GF PASS_WITH_LISTED_PIECES (+0.116 m2 = one 0.40 band beside a column narrower than the wall: V1 cuts
   the full width over 0.30 m, listed), 1F PASS (-0.00001 m2), 2F PASS (0); piers < 4 t listed; every bridged stretch listed.

## 2. Alsenan totals (metres, centreline; hand = T-103 79bd397 as reconciled in T-117)

| Floor | t | V1 | V2 arch run (1) | V2 physical (2) | V2 openings in run | V2 glass (3) | split out | Hand T-103 | V2 - hand |
|---|---|---|---|---|---|---|---|---|---|
| GF | 0.15 | 38.023 | 37.788 | 31.665 | 6.124 | 0.000 | 1.958 | 41.185 | -3.397 |
| GF | 0.20 | 111.395 | 96.775 | 69.234 | 27.541 | 17.841 | 15.870 | 101.975 | -5.200 |
| GF | 0.40 | 0.600 | 0.600 | 0.600 | 0 | 0 | 0 | HELD (GF-H01) | status differs |
| GF | glazed line (no family) | - | 6.726 listed | 0 | - | 6.726 | - | (in 0.20 as GF-W37 5.050) | - |
| **GF** | 0.15+0.20 | **149.418** | **134.563** | 100.899 | | | 17.828 | **143.160** | **-8.597 (-6.0 %)**; with the glazed line -1.871 (-1.3 %) |
| 1F | 0.15 | 54.917 | 56.736 | 46.467 | 10.268 | 0 | 0 | 57.045 | -0.309 |
| 1F | 0.20 | 63.279 | 63.599 | 45.313 | 18.285 | 16.386 | 0 | 63.708 | -0.109 |
| **1F** | | **118.196** | **120.335** | 91.780 | | | | **120.753** | **-0.418 (-0.35 %)** |
| 2F | 0.15 | 10.900 | 10.900 | 9.100 | 1.800 | 0 | 0 | 11.000 | -0.100 |
| 2F | 0.20 | 28.700 | 28.700 | 22.800 | 5.900 | 4.000 | 0 | 28.775 | -0.075 |
| **2F** | | **39.600** | **39.600** | 31.900 | | | | **39.775** | **-0.175 (-0.44 %)** |

Freelancer blockwork metres (development reference, never a target): GF 134.28 / 1F 120.31 / 2F 39.10 m. V2 arch run vs
freelancer: GF +0.283 (+0.2 %), 1F +0.025 (+0.02 %), 2F +0.500 (+1.3 %). V1 was GF +15.138 (+11.3 %), 1F -2.114 (-1.8 %).
The GF match is not proof (the freelancer also lacks both glass lines and GF-W30; see 4.).

## 3. Every V1 -> hand difference of T-117, now (sum V2 - hand per floor, paired runs)

| T-117 cause | V1 | V2 | Evidence |
|---|---|---|---|
| A. band across open floor (GF y 1.50: 16.52 m, 4.30 wall; x 21.925 stubs) | +14.13 | 0 (GF-W02+W03 4.300 = hand; W20+W21 2.042 vs 2.092, the -0.050 is a 45 deg end held) | split 13.27 + 1.958 m, no evidence (passage OP-002 / OP-003 clear or 11.22 m wide) |
| B. band across both passage mouths | +2.50 | 0 (GF-W00+W01 26.370, W04+W05 7.750 = hand) | split 1.40 + 1.20 m: passage records with no head line and no symbol block |
| C. doorway at a free end | -3.49 | GF-W27 / 1F-W12 / 1F-W23 doorways 0.874 / 1.089 / 0.880 = hand; GF-W29 0.850 vs hand 0.649 | door swings 0.69 / 0.89 / 0.69 m in the gaps; W29: DXF face of the wall across at x 17.80, wall end 18.65 -> 0.850 m, ENGINE_RIGHT |
| D. GF-W30 not in the run (0.30 stub + 0.797 door, no band) | -1.53 | -1.525 (still) | no band from the wall stage: out of this piece's reach (T-108 / wall stage) |
| E. GF-W37 pool-side glass | -5.05 | listed as a GLAZED line 6.726 m, no family | four window-layer arcs r 2.33..2.45 m (the DXF draws a curve; T-103's "straight band 4.95" was the chord; the PDF prints 657) |
| F. 1F concave bay as chord | -0.35 | 1F-W00+W01+W25 11.139 vs 11.173 (-0.034) | arc 3.747 m on the glass mid circle r 2.075 carried to the centreline + stub 0.169 absorbed; hand 3.673 (UNRESOLVED, 0.074 m) |
| G. T stems (hand to centreline, T piece twice) | -3.03 (incl. C rows) | -2.831 (same rule; ENGINE_RIGHT) | see CSV |
| H / J. 45 deg and corner holds | -0.79 | -0.842 HELD / cut square (UNRESOLVED, as V1) | held list |
| I. 1F doorless 1.30 m opening with head lines | +1.14 | +1.141 (ENGINE_RIGHT, kept) | OP-009 head_lines 2 |
| X (new). 1F crossing drawn through by both walls (x 10.745 / y 9.825) | V1 counted 0.15 twice | counted once (1F 0.15 -0.150 m); the hand has it twice too | ENGINE_RIGHT: identity 1F -0.0225 m2 -> 0 |

Split-out metres are listed run by run in V2_STRETCHES_AND_EVIDENCE.csv (GF 17.828 m in 5 stretches; none on 1F / 2F).

## 4. Q-69 B wall-by-wall reconciliation of 143.16 and 131.88 (GF, owner request), arithmetic corrected

Q-69's text said "12.05 - 3.77 = +8.88". Corrected: hand vs freelancer GF = external +8.28 (= +12.05 two glass lines
- 3.77 unpaired external pieces) + internal +0.61 = +8.89 m (T-103 rounds +8.88; T-117 section 3).

| Step | Metres | Source |
|---|---|---|
| T-103 hand architectural run, GF (owner-manual comparison, kept) | 143.160 | T-103 |
| less GF-W11 saloon glazing (opening 6.332 printed 633) | -6.332 | T-103 row GF-W11 / V2 opening OP-019 6.3316 |
| less GF-W37 pool glazing (hand chord 4.95) | -4.950 | T-103 row GF-W37 |
| = owner's physical candidate (glass lines out, other openings in) | 131.878 (= 131.88) | |
| V2 equivalent: V2 arch run 0.15+0.20 + glazed line | 134.563 + 6.726 = 141.289 | V2 |
| less W11 glazing and the glazed line | -6.332 - 6.726 = 128.231 | V2 |
| difference V2 - owner candidate | -3.647 = -1.871 (V2 - hand arch, section 3) - 1.776 (glass arc 6.726 vs chord 4.95) | |
| V2 physical (2), every opening out (doors, windows, passages, doorways, glass) | 100.899 (+0.600 at 0.40) | V2 |

The two physical figures answer different questions: 131.88 removes only the two glass lines; V2 (2) is the solid
masonry at the plan cut, so T-108 adds (4) masonry above / below every opening from heights (none of it counted twice,
none dropped). Both are in the CSV per run.

## 5. Who is right (proposals for the verifier)

ENGINE_RIGHT: T stems on the face (G, 2.831 m over 3 floors); GF-W29 doorway 0.850 m (hand 0.649); 1F doorless 1.30 m (I);
1F crossing counted once (0.150 m). HAND_RIGHT and now matched by V2: A, B, C (3 of 4 doorways exactly), F (to 0.034 m).
UNRESOLVED: 45 deg / corner holds 0.842 m (V1 rule kept); 1F bay arc 3.747 vs 3.673 (0.074 m: which radius the hand used
is not written); GF-W37 glass curve 6.726 (DXF arcs) vs 4.95 (hand chord) vs 657 printed (PDF): a drawing conflict for the
designer, the glazed line has no block family either way. NOT FIXED: GF-W30 (-1.525 m, the wall stage forms no band).

## 6. Adversarial fixtures (tests/t125_masonry_centreline_v2, none is Alsenan)

Garden-edge band (6.80 vs V1 18.00), 11.20 m passage with a symbol block (split), 1.20 m passage clear (split) / with a
head line (kept, physical 6.80), doorway by swing (3.90) and by door record (counted once), no swing (3.10), 0.50 leaf in a
1.20 gap (no doorway), concave bay (10.240148, glass 4.240148), free glazed lines (5.00 and 3.220132, no family), window
glazing inside a band (not a glazed line), crossing drawn through (9.80; two families 5.90 / 3.80 + HELD), pier, column in
the gap, a stretch longer than its door (listed HELD 2.00), missing inputs (HELD / NO_WALL_BANDS, never 0); each turned
37 / -121 deg, mirrored, in metres and mm; identity PASS on every fixture.
