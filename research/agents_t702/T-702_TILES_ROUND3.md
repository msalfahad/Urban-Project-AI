# T-702 tiles round 3: roof / terrace build-up, stair-core floor, beam crossings (lane A, research, unwired)

Worker 2, 2026-11-11. Candidate ARCH_TAKEOFF_V3.0.69 (T-687 line index). Nothing wired or released; V2.9 + route G
unchanged; no engine module, rule / knowledge version, registry or frozen file touched. Rules R-T702-1 .. -5 in
`t702_rules.py`; builder `t702_alsenan.py` (`--check`, every input sha256-pinned); own drawing probe `t702_probe.py`
(relative stations and handles only); outputs `out/T702_TILES_ROUND3.{json,md}`; tests `tests/t702_tiles_round3`
(villa K702 by hand + adverse + development pin). Drawings by Drive title only: "Alsenan chalet project" /
P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55) and "ST7757 dxf.dxf" (9f9d1179), own decode this run.

## Census (d)

The 264 tile-scope lines are byte-identical V3.0.66 -> V3.0.69, so the T-681 / T-690 census stands: 104 HELD
(OWNER_OPEN 46, OPEN_BOUND 44, DESIGNER_ITEM 7, MEASURABLE_NOW 6, WIRING_GAP 1). This task moves **2** of them from
blank to a bound: the stair-core wet-room wall tile GF-10 L-1341e041 **11.40 .. 25.21 m2** and GF-11 L-de4088e7
**7.04 .. 19.555 m2** (R-T702-5: a fully tiled wet room's wall tile is its backing render's face to the same top less
the same openings; the backing lines L-3f7fb1b3 / L-a636dabc carry exactly these bounds, merged T-686 R-T686-3 and
wired in V3.0.69). FIN.WALL.TILE blank 6 -> 4; DESIGNER_ITEM blank 7 -> 5. Never summed with the released 340.30 m2.
Parts (a) and (c) move no tile-scope line (roof layers, landings and the wet-room plaster bands are other codes).

## (a) Roof and terrace build-up, layer by layer (R-T702-3)

Own census this run: ST7757 2,237 text / attribute / dimension entities, P7757 497: **no roof or terrace layer and no
thickness is printed**. The only 'INSULATION' is the pool detail ('5cm INSULATION MEMBRANE.' / '10cm PLAIN
CONCRETE.'), not extended to a roof (ERS s.3). Structural level texts are +0.15 / +0.30 / +1.00 / +9.70 only: no slab
level under a roof or terrace. So for the 16 FIN.ROOF.* lines:

| Zone | Finish m2 (own edge) | Screed m3 (Q-41, own line) | Insulation | Protection | Membrane face basis m2 |
|---|---|---|---|---|---|
| ROOF-430 +4.30 | 54.9203 released (hatch) | AT_LEAST 3.324832 .. OPEN | UNKNOWN (D-39) | carried by the screed (Q-41) | 55.560 (D-band 54.920 .. 55.560) |
| TERRACE-550 +5.50 | 31.643 released | AT_LEAST 2.512672 .. OPEN | UNKNOWN | carried | 32.721 |
| ROOF-970 +9.70 | 115.65646 released | AT_LEAST 4.791492 .. OPEN | UNKNOWN | carried | 115.65646 .. 115.81396 (T-691) |
| ROOF-1390 +13.90 | HELD blank | HELD blank | HELD | HELD | HELD (Q-34 PARKED) |

The screed lows are the merged T-646 falls wedges (unwired); no printed thickness exists, so the volume high stays
OPEN. Adhesive and bed under a roof finish: material and tile size not printed, adhesive HELD; Q-45 'roof depending on
slope' and Q-41 'roof -> screed' are ONE falls volume, carried once by FIN.ROOF.SCREED (no FIN.FLOOR.BED line sits on a
roof zone: 0 found, no double count).

**F-T702-1 (Lead / Checker): the cap 'b_roof < 0.30 (parapet note, ST p.14)'** used by merged T-250 and T-690 (roof
soffit S 3.74 .. 4.04 for 1F-02 / -03 / -12 / 2F-02 / 1F-09) is not located in the structural DXF: the parapet text is
'CHECK ARCHITECTURAL DETAIL OF PARAPET, BEFORE CASTING' (x3, title-area note, no dimension) and 'T min = 20 / 25 /
30 cm' is the column-thickness-by-storey-height note. R-T702-3 refuses a cited, unlocated cap as a bound (test), so
no screed high is taken from it. Someone should check ST7757.pdf p.14 visually (vector, no text layer); until it is
located, the T-690 roof-part band highs rest on it.

**Terrace soffit (GF-07 / GF-16 roof parts).** The structural set draws one 0.16 plate (no step, T-128 / T-220). On
that plate the terrace slab top is 5.451 and the build-up under the printed +5.50 would be 0.049 m, below the printed
1 % falls rise 0.190 .. 0.203 (T-321 Checker): the plate reading and the printed finished level cannot both hold
(DCR-6, designer). The T-690 bound S 3.65 .. 4.34 stands; no printed fact narrows it.

## (b) Stair-core floor (R-T702-4, R-T702-5)

The merged T-493 surface census (11 surfaces) is restated on V3.0.69 line ids: one owner per surface, 0 claimed twice
(test refuses a landing claimed by floor and B7-04). GF hall 4.805 (+1.00) and back lobby 1.3225 (+0.30) are floor-level
surfaces at flight ends: owner trade FLOOR (A6), material HELD (no finish source); centre strip L-a788de46 0 .. 0.23
HELD; under-stair porcelain 2.07 released. Intermediate landings and arrivals are B7-04: 1F arrival 4.9225 and E1 5.1794
released; MS1-LD 1.4375, MS2-LD 2.9325, 2F arrival 4.865, RS-LD 1.3525 m2 are still unwired (T-493 proposals);
L-1983e89d (0 .. 2.9225) holds no landing and L-5d2be30d (0 .. 9.225) holds 7.7975 of landings + 1.4275 named.

GF-10 / GF-11 floor level (own GF plan read): the marks +0.30 (back lobby, north) and +1.00 (hall, south) lie outside
both rooms; neither room has a mark, and the basin space's leafless 0.90 doorway opens toward the stair lanes. Both
options stay carried (C-SH-2, designer). The wall tile takes R-T686-3's top 2.20 (highest head, Q-55 C) .. G1 +4.65 -
floor +0.30, hence the two bounds above.

## (c) Beam crossings T-690 left as 0 .. 2 ends (R-T702-1, R-T702-2)

Overlay: ST column 35C -> arch 2FAE (1.10 x 0.25 both), checked on 22 column outlines within 12 m of it, worst
corner residual 0.0 mm.

**GF-07 pantry, B27 (90 x 85, soffit 3.60 < H 3.65: fills the band).** B27 runs diagonally (53.571 deg) from column
2FAE at the north-west corner to a column south-east of the open east edge. On the pantry's face walk (10.500 m) its
footprint covers the column face 0.900 + return 0.050 + north wall 0.1476 + west face 0.0462 = **1.143764 m (one
crossing)**; the south end leaves through the open edge B3 (1.516 m of footprint on an open edge: 0). T-690's 'ends x b'
(0 .. 2 x 0.90) is replaced by the measured stretch (oblique and corner pieces: R-T702-1 b).

**GF-14 wash lobby, B11 (20 x 75, depth 0.59 below the slab: a 0.05 strip stays in the 0.64 band).** Two crossings:
square on the south face D2 **0.200 m**, and at 45 deg over door 320 (D315, head 2.20 < H, so the wall above it is in
the band) **0.282868 m** (= 0.20 x sqrt 2). Total 0.482868 m, not 2 x 0.20.

**F-T702-2 (material): sunken panels under the 1F wet rooms sit over these GF wet rooms.** The five GF-roof-slab
'Sunken slab.' hatches (T-213; drop d printed nowhere, designer item D-41) overlap the faces: GF-07 west face 2.7236 m
(panel 280) + north wall 1.7524 m (287) = 4.476 m; GF-14 W_B 1.000 + 317 0.142 + over door 320 0.517 + 31A 0.059 =
1.718 m (275 / 276). B11 is the beam between 275 and 276 (its top unprinted, T-213 s.4); B27 separates 280 / 287. T-690
took S = 4.29 (flat 1F slab) as DRAWING-CONFIRMED on those faces; under a panel S = 4.29 - d, bounded by 0 .. 0.64 of band
(the ceiling cannot lie above the soffit; R-T702-2).

| Line | Before (V3.0.69) m2 | After m2 | Terms |
|---|---|---|---|
| GF-07 band L-ea586fea | 2.853686 .. 6.918815 | **0.499037 .. 6.186806** | floor 6.39951 (T-690 split) = free 0.779746 + panels 4.476 + B27 1.143764; terrace 4.09149 x (0 .. 0.69) |
| GF-14 band L-ef7a1666 | 5.05488 .. 5.29088 | **3.892324 .. 5.005988** | free 6.066132 x 0.64 + B11 strips 0.010 .. 0.024143 + panels 1.718 x (0 .. 0.64) |

High ends drop by the established beam stretches (-0.732009 / -0.284892 m2); low ends drop -2.354649 / -1.162556 m2
(D-41 panels -2.86464 / -1.09952, beam terms +0.509991 / -0.063036). Both stay HELD. The panels also lie over the plan zone behind doors 320 / 321 (the W.C. wedges GF-12 /
GF-13, whose T-690 bands 4.74496 / 4.3584 are 'fixed'): not traced face by face this run, for the Lead.

Named residuals: face walks 10.500 vs T-690 10.491 (GF-07) and 8.243 vs 8.267 (GF-14) (T-128 walks, 0.009 / 0.024 m);
GF-07's floor / terrace split is T-690's share 0.39 (my 1F overlay puts the 1F south wall about 1.29 m north of the
pantry's south face; the boundary basis, inner vs outer 1F face, is not re-decided here).

## Engine vs freelancer

No tile quantity moved in a released line. The two new wall-tile bounds (18.44 .. 44.765 m2) and the band lines have no
freelancer counterpart (his wet rooms are not itemised by room; his plaster stops at his flat paint height: T-556 /
T-690): NOT_COMPARABLE / RULE_DIFFERENCE. Verdict proposals: beam crossings ENGINE_WRONG at T-690 (ends x b, oblique and
corner pieces missed; a sunken soffit taken as flat), corrected here as bounds; roof layers ENGINE_RIGHT as HELD
(nothing printed); stair-core floor ENGINE_RIGHT (one owner per surface).

## Lessons-register row (proposed, ERS s.7)

2026-11-11 | two GF wet-room bands were bounded with 'ends x beam width' on a flat soffit, while the beams cross the
faces obliquely or at a column corner and four faces sit under sunken 1F wet-room panels | the band was taken from the
room list and the beam schedule, not from the structural plan laid over the architectural plan | measure a beam's
crossing on the room's face walk from its drawn edges after a checked overlay (count, residual); a face under a sunken
panel takes S - d with d held (0 .. band) (every villa) | tests/t702_tiles_round3 (normal: square / 45 deg / corner;
adverse: parallel beam, unprinted beam top, missing roof soffit, tile top above soffit, cited-but-unlocated cap,
landing claimed twice, blank backing) | PROPOSED.

## For the Checker (re-measure one zone)

1. Overlay ST 35C on arch 2FAE; check 3 more column outlines. GF-07 frame: origin = A6 start. B27 edges 325 / 326 ->
   (0.900, 4.700) .. (4.369, 0.000) and (-0.034, 4.450) .. (3.398, -0.200); the face pieces inside: 0.900 / 0.050 /
   0.1476 / 0.0462 = 1.143764 m.
2. GF-14 frame: origin = D2 start. B11 edges at x -0.580 / -0.380; D2 0.200, over door 320 (317 end -> 31A start)
   0.282868.
3. Hatches 280 / 287 on GF-07 faces (2.7236 / 1.7524 m) and 275 / 276 on GF-14 faces (1.556 / 0.162 m).
