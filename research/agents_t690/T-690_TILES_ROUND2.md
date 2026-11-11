# T-690 tiles round 2 + wet-room band above the ceiling + MS2-TR nosing (lane A, research, unwired)

Worker 2, 2026-11-11. Candidate ARCH_TAKEOFF_V3.0.66 (T-677 line index). Nothing wired or released; V2.9 + route G
unchanged; no engine, rule, knowledge, registry or method file touched. Rules R-T690-1 .. -3 in `t690_rules.py`;
builder `t690_alsenan.py` (`--check`, every input sha256-pinned); outputs `out/T690_TILES_ROUND2.{json,md}`; own drawing
probe `t690_probe.py` (relative stations only); tests `tests/t690_tiles_round2` (villa K690 by hand + development pin).
Drive "Alsenan chalet project" read this run: P7757_DXF_COMPRESSED.zip (714,410 bytes = Drive size, re-encoded to
base64 before `decode`), P7757.dxf sha ab54dd55, private copy only.

## (a) Census restated on V3.0.66 (R-T690-2)

The 264 tile-scope lines (11 codes) are byte-identical V3.0.65 -> V3.0.66, so the merged T-681 census stands: 104 HELD
= OWNER_OPEN 46, OPEN_BOUND 44, DESIGNER_ITEM 7, MEASURABLE_NOW 6, WIRING_GAP 1 (count = filter by line id). The 6
MEASURABLE_NOW lines are skirting stretches beside stair-hall openings (not wall / floor tile): T-681 measured them from
the DXF and the Checker re-measured them independently (MERGED ebd8a77d): MS2-LD.W25 1.000 lm FULL; MS2-LD.W13 and the
four MS1-L / MS2-L flight stretches NOT_APPLICABLE (walking level inside the opening). They are still blank in V3.0.66
only because no Gate B has wired them: no re-measure is owed, the wiring is. Areas, beds and the adhesive bound are
unchanged (adhesive 149 .. 248 bags HELD: no tile size printed).

## (b) WIRING_GAP L-6ff876ae (OP-020 jamb skirting) (R-T690-3)

Merged FR-T601-2 settles it EXCLUDED (NOT_APPLICABLE, Q-06 A: the passage's wash side is a basin-only wet space).
Neighbours checked: GF-ST-HALL skirting L-af8221bd 4.650 lm = face 6.550 - OP-010 1.000 - OP-020 0.900 (T-443: width
deducted, no jamb return added); GF-11 skirting L-1cf6c336 EXCLUDED (full-height tile); no stair-skirting line names
OP-020. One count: HELD -> EXCLUDED, the 0.400 lm beside is removed, nothing moves into a neighbour. FIN.SKIRTING HELD
blank 7 -> 6 (5 with the T-681 W25 fix).

## (c) Wet-room wall band above the finished ceiling (F-T686-1, R-T690-1)

Element: the wall face of a wet room from the tile top H (= finished ceiling, Q-48 A) to the plaster top S (structural
soffit, owner 2026-11-02 / Q-72, R-T556-1). Owner manual method (G1, Q-43: plaster at the paint height) gives 0; the
owner's later rule (plaster to the slab underside) and the drawing give the band; the later owner rule governs.
Proof it is in no line now: in all 12 main-house wet rooms the FIN.PLASTER line equals the FIN.WALL.TILE line to the
m2 (tile backing to H) and 'paint above wall tile' is EXCLUDED; the 4 annex T-686 lines re-compute exactly as
L x H - openings below H at both datum ends; the 2 stair-core lines stop at the tile top by construction.

| room (lines) | length m | S / H m | band m2 | status |
|---|---|---|---|---|
| GF-02 / -03 / -05 / -06 annex | 7.2 / 7.5 / 5.6 / 14.5 | S 3.084 .. 3.84, H 2.494 .. 3.25 on one datum (S - H = 0.59) | 3.658 .. 4.248 / 4.425 / 3.304 / 8.545994 .. 8.555 | HELD (Q-54 B, D-39) |
| 1F-07 laundry, 1F-08, GF-12, GF-13 | 16.94 / 6.54 / 7.414 / 6.81 | floor S 3.99 / 4.29, H 3.35 / 3.65 | 10.8416 / 4.1856 / 4.74496 / 4.3584 | ASSUMED - OWNER-APPROVED (H) on a DRAWING-CONFIRMED soffit |
| GF-14 (B11 crossing, open side) | 8.267 | 4.29 / 3.65 | 5.05488 .. 5.29088 | HELD: beam-end count 0 .. 2 |
| 1F-02, 1F-03, 1F-12, 2F-02 (all under a roof) | 9 / 9 / 8.7 / 9.7 | roof S 3.74 .. 4.04 (b_roof 0 .. 0.30, parapet note) | 3.51 .. 6.21 / same / 3.393 .. 6.003 / 3.783 .. 6.693 | HELD: roof build-up (D-39 / DCR-6) |
| 1F-09 (roof share 0.31) | 7.6 | 3.99; roof 3.74 .. 4.04 | 4.275 .. 4.9818 | HELD (roof part) |
| GF-07 pantry (terrace 0.39, B27, open) | 10.491 | 4.29; terrace S >= H only | 2.853686 .. 6.918815 | HELD: terrace build-up has no merged upper bound; B27 ends 0 .. 2 |
| GF-16 (terrace 0.54) | 7.625 | 4.29; terrace S >= H only | 2.2448 .. 5.085875 | HELD (terrace part) |
| GF-10 / GF-11 stair core | 6.2 / 4.9 | floor +0.30 or +1.00: S 4.29 .. 4.99, H 2.20 .. G1 | 3.584 .. 17.298 / 2.56 .. 13.671 | HELD (C-SH-2, designer) |

Totals: annex 19.932994 .. 20.532 m2 (gross 20.532 = F-T686-1, AGREE); all 18 wet rooms 78.83192 .. 123.02493 m2;
the four main-house rooms with a fixed band 24.13056 m2 (point value). Carrier: FIN.PLASTER, one NEW component line per
room '<engine room>:plaster band above ceiling' (the register's 'plaster owns the band'); not added into the
tile-backing line (a different coat by a different trade, already verified to H) - the wiring lane decides with the
Checker. Joint bounds (R-T690-1 d): where the backing line and the band hang on one datum the room total is one bound
(GF-10 24.358 .. 29.178 m2 for line + band, against 14.984 .. 42.508 if the two separate bounds were summed).
Freelancer: his plaster stops at his flat paint height (T-556 / T-634), so no band in his BOQ: RULE_DIFFERENCE (owner
rule 2026-11-02); his wet rooms are not itemised per room: UNRESOLVED. Verdict proposal: ENGINE_OMISSION closed by the
new lines (scope, not measurement).

Finding F-T690-1 (Lead, not changed): B27 (0.90 x 0.85) leaves 0.69 below the GF slab soffit, so its soffit is +3.60
above the pantry FFL, 0.05 below the tile top / ceiling 3.65: the pantry ceiling must drop under it (the candidate has a
GF-07 bulkhead line 0.3281 m2); the tile line's height on the faces under B27's ends is not affected by this task.

## (d) MS2-TR nosing (own read this run, `t690_probe.py`)

1F plan: in the west lane's north square, a layer-5 line at 1.250 from the lane's west edge (0.100 from both lane
edges of the 0.200 well) from the well end to the north wall face, 1.150 long, with its layer-2 twin 0.050 east (the
riser face): the closing step's front overhangs toward the lower west part (+7.516). 2F plan: the same pair, 1.150. GF
plan: the pair only on layer 2 (above the GF cut): not a GF object. **1.150 lm AGREE** with T-598 (MERGED: arch 2F +
ST p.5) and T-684; T-412's "position not drawn" is wrong on two plans. DRAWING-CONFIRMED; one count: edge ST01-MS2TR
joins B7-05 through T-424 (QUEUED) as a landing / floor edge outside the step basis (T-598 s.6); the MS2-L step-lm line
L-23651ecf is 11 x 1.150 = 12.65 (treads only), so no double count. V3.0.66 carries no nosing line yet.

## Lessons-register row (proposed, ERS s.7)

2026-11-11 | a 0.59 .. 0.64 m wall band above the false ceiling of every wet room (18 rooms, 78.8 .. 123.0 m2) sat in no
line | the wet-room 'plaster' line was built as the tile backing to the tile top, and the later owner rule (plaster to
the slab underside) was applied only to dry rooms | each wall layer has its own top: tile and backing to the ceiling,
plaster to the soffit; a datum shared by two lines is bounded jointly, never by summing separate extremes | R-T690-1
(every villa) | tests/t690_tiles_round2 | PROPOSED.

## For the Checker (re-measure two rooms)

1. 1F-07 laundry: 16.940 x (3.99 - 3.35) = 10.8416 (no opening head above 3.35: W21 2.50, doors 2.20).
2. GF-06 kitchen: 14.500 x 0.59 = 8.555; at s 3.544 W08 head 2.50 lies 0.006 above H 2.494: 8.555 - 1.501 x 0.006 =
   8.545994.
