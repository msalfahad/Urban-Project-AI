# T-237: cross-trade wall-face consistency (blockwork / plaster / paint), Alsenan development villa

Worker 2, 2026-10-23 23:43 UTC onward, run session_014MMA2JXJY7nDyNTy8gCLya. Lane A, gate 1, backlog-permitted
(integration dependency of the plaster / paint whole line, T-211). Research + tests only: no engine module, rule /
knowledge version, registry, merged ledger or released quantity changed. No drawing was opened in this run: every
input is a merged research CSV of this repository (list below). Development villa, not an accuracy claim. Self-check
of this run (codemap check, pytest t061, freeze): PASS.

## 1. Physical element (ERS s.2 step 1)

One wall **face** = one wall seen from one room. On it, with the structural floor top as the common datum:

| trade | physical surface | top |
|---|---|---|
| blockwork | the block panel | soffit of the member on the wall: beam (depth d) or slab (d = slab t) -> `storey - d` |
| plaster (drawing-derived) | block panel + the concrete band of a beam that projects below the slab (beam side face) | slab soffit `storey - slab t` |
| plaster in the stair void | block + beam side + slab edge (no ceiling slab at the face) | storey (floor to floor) |
| paint / tile | plastered face below the ceiling line | T-128 `storey - slab - build-up(0 .. 0.10) - decor 0.15` |
| owner manual method | the owner's room heights (Q-43 / Q-48 A) | 3.15 / 3.65 / 3.35, shown beside, never merged |

So `plaster top - block top = d - slab t` (the beam band; 0 under a slab; `d` in the void). Anything the members over
the wall do not explain is a datum residual and is named, never 'rounding'. The band is plastered concrete, not block:
the block m2 and the plaster m2 of one face differ by exactly that band.

## 2. Method

`face_consistency.py` (stdlib, any villa) holds the rule R-T237-1 (proposed): (a) one opening id at most once per face,
at most two faces per id, a split face (one side shared by two room regions) must sum to the opening width; (b) a
plaster / paint height above the block top only with a named member whose band explains it, else refused
(PLASTER_ABOVE_BLOCK_NO_MEMBER); (c) a HELD block height is never carried as a plaster number (HELD_BLOCK_CARRIED);
(d) one opening, one w x h in every ledger that deducts it (mismatch named in m2); heights outside 0 .. 20 m refused
(units). `alsenan_t237.py` builds the crosswalk read-only:

| input (merged) | used for |
|---|---|
| research/agents_t128 ROOMS_T128_R3 / OPENINGS_T128_R3 (T-128 r3, a6ac2c66) | 32 rooms, 94 face rows, plaster top, paint heights, owner heights, face deductions |
| research/agents_t175 T175_OPENING_HOSTS (T-175) | opening id -> host wall, the two sides (room names), sill above FFL |
| research/agents_t201 HEADS_T201, agents_t207 CLOSURE_T207, agents_t238 DELTA_T238 | merged heads / heights / arched outlines |
| research/agents_t225 BLOCKWORK_WALL_REGISTER_V1 + agents_t226 / agents_t227 register_delta | wall height, class, members over the wall |

Crosswalk room face -> wall: each T-128 opening face is matched to its census id (explicit id in the T-128 label; else
room alias + kind + width 0.06; door labels that name the room on the other side; door-block nominal widths for split
faces; a window family label takes the one member no other room deducts), and the census host gives the wall. A
reproduction guard recomputes T-128 r3's own drawing-derived net per room from its own rows before any change is
computed: **30 of 30 rooms with a level REPRODUCED** to 0.015 m2 (GF-10 / GF-11 have no drawn level: HELD both ways).

Limit (named, not hidden): walls that host no opening are not reached by an opening crosswalk; the face LENGTH of a room
on each wall is not in any merged ledger (T-128 walks the room contour, the register the wall runs), so the per-face
m2 of a height difference is given per metre of face (`band_m2_per_m_face`), not as a total. The geometric crosswalk
(room contour segments x register runs on P7757.dxf) is the next piece if the Lead wants the faces closed in m2.

## 3. Results (files in this folder)

| measure | value |
|---|---|
| rooms crosswalked to at least one wall | 32 / 32 |
| opening faces matched to a census id | 83 / 85 (2 doorless faces: width-only candidate P-GF-01, not taken) |
| room-wall faces formed | 75: AGREES 4, BAND_EXPLAINED 38 (residual within 0.02 m on every one), BLOCK_HELD 30, PLASTER_HELD 3 |
| same opening deducted twice on one face | 0 (rule a holds on Alsenan; ADVERSARIAL_PROBE #3 is now detected by the test) |
| plaster above block with no member | 0 |
| datum residual after the members and the void are accounted | 0 m on every established face |

Findings (`FINDINGS_T237.csv`, one row each, with wall and room):

| finding | count | engineering meaning | BOQ lines, units |
|---|---|---|---|
| HEIGHT_DATUM_SPLIT_ROOF | 18 faces | the same storey interval is formed by the block register (storey 4.20 / 4.50 - member) and HELD by the plaster ledger on the roof build-up (DCR-6). Under a roof the printed mark is a finished level: structural interval = mark difference - roof build-up + floor build-up. The register's figure on these faces is therefore not established either; the two ledgers must carry ONE datum | blockwork m2 and plaster / paint m2 on 1F-01 / 02 / 03 / 04 / 11 / 12, 2F-01 / 02 / 03, GF annex rooms: m2 = face length x (roof build-up - floor build-up) per face; T-221 (merged) gives 0.190 .. 0.203 m for the +5.50 terrace only |
| MASKED_DATUM_CAUSE | 5 faces (GF-W04, GF-W18, GF-W26) | annex walls whose register height = 4.00 (annex storey +4.30 - 0.30) - member, i.e. the same Q-54 B / D-39 annex datum that holds GF-W00, but the register's single cause column says 'held opening'; when the opening is resolved the height would look established while it is not | blockwork GF-W04 / W18 / W26 gross; T-228 should carry both causes |
| BLOCK_HEIGHT_HELD_PLASTER_ESTABLISHED | 12 faces | the plaster top (slab soffit) does not need the member, so the plaster gross stands, but the block / concrete-band split of the face (substrate) stays HELD with the block height | beam-band m2 on those faces HELD |
| HEIGHT_DATUM_SPLIT_LEVEL | 2 (GF-W29 from GF-10 / GF-11) | block height 4.34 formed while the two rooms' level is not drawn (T-088) | GF-W29 block vs those rooms' plaster |
| ROOM_ASSIGNMENT_DIFFERS | 1: W06 | T-128 deducts the 0.60 window in GF-13 (wedge B) and nothing in GF-12; T-175 puts W06 in wedge A. One window, two rooms in two ledgers | 0.480 m2 moves between GF-12 / GF-13 faces (tile, paint); the Checker re-looks at the plan |
| SPLIT_FACE_SUM_DIFFERS | 1: W03 | T-128 deducts the pool glazing band as 1.625 + 5.106 = 6.731 m (developed on the curve) vs the census width 6.57 | +0.161 m x 4.30 = 0.692 m2 more deducted in plaster / paint than the opening census; curved band: developed vs chord to be ruled (R4 curved geometry) |
| SPLIT_FACE_SUMS | 1: D-1F-02 | 1F-01 1.00 + 1F-13 0.42 + ST-1F 0.58: the landing side split over two regions sums exactly | none |
| SIZE_DIFFERS (door) | 2 | D-GF-05 (kitchen) 0.95 and D-1F-07 (bath by the laundry) 0.75 in T-128 vs 1.00 / 0.80 in the census: one-side faces kept the rebate width; T-128's own rule (frame = leaf + 0.11) gives the census width | -0.110 m2 deduction each (net +0.11 too high) |
| OUTLINE_DIFFERS (arched, T-238) | 2 | W15 1.55 x 3.10 = 4.805 vs arched outline 4.363; W26 2.040 vs 1.875 | +0.442 / +0.165 m2 net per face (T-128 over-deducted) |
| T-128 DEDUCTS A HEIGHT THE MERGED LEDGER HOLDS | 1: W17 | T-128 deducts 3.286 x 3.50 = 11.50 m2 in 1F-11; T-238: 3.50 is the archivolt, finish deduction HELD, upper bound 10.024 | 1F-11 net HELD (at least +1.48 m2 above T-128) |
| OPENING_NOT_CROSSWALKED | 2 | the 0.90 doorless opening between GF-11 and ST-GF: census row P-GF-01 has no sides | both faces HELD (head not printed) |

## 4. Per-room change if the plaster / paint ledger took the merged heads (NOT applied)

`ROOMS_T237.csv`: old (T-128 r3) and new net per room by both methods, held openings before / after, missing items.
New = T-128 r3 faces with the merged heads of T-201 (17 windows now DRAWING-CONFIRMED), T-207 (W11 / W12 h 2.20, sill
HELD: deduction capped at 4.290 each), T-238 (W15 / W16 4.363, W26 1.875, W17 HELD <= 10.024) and the two census door
widths. Doors keep the Q-55 C 2.20 head (ASSUMED — OWNER-APPROVED).

| method (30 rooms with a level; owner: 27 with an owner height) | old net m2 | new net m2 | change |
|---|---|---|---|
| drawing-derived paint / plaster net | 1403.88 .. 1570.84 | 1449.99 .. 1560.92 | +46.11 lo / -9.92 hi |
| owner manual method net | 1101.24 .. 1203.21 | 1133.94 .. 1195.64 | +32.70 lo / -7.57 hi |
| HELD openings in the ledger | 27 | 11 | -16 |

The range narrows by 56.0 m2 (drawing-derived) and 40.3 m2 (owner) because 16 held window bands are now known; the hi
bound falls where the known windows are now deducted, and rises only in 1F-11 (+11.50 hi: W17 is HELD after T-238, so
its old 11.50 deduction can no longer be taken as known). Status of every new figure: SOURCE-SUPPORTED PENDING
INDEPENDENT CHECK where the room's gross is DRAWING-CONFIRMED, HELD where the room carries the roof datum (DCR-6) or a
held opening; nothing VERIFIED, nothing released. Lane I applies it (T-211 V3.0.9b or the next slot), not this task.

## 5. Statuses and what stays HELD

Rooms whose plaster / paint stays HELD after this crosswalk, with the missing item (`ROOMS_T237.csv` missing_items):
roof datum DCR-6 (annex D-39) on 23 rooms in part or whole; level not drawn (T-088) GF-10, GF-11; owner shaft height
Q-72 for ST-GF / ST-1F / ST-2F; held opening heads L-GF-01 / L-1F-01 / L-2F-01 (lift supplier), W02 (designer D-53),
W11 / W12 sills, A-GF-01, A-1F-01, the GF-11 / ST-GF doorless opening, W17. Sheets searched for these by the merged
tasks cited (T-201, T-207, T-221, T-227, T-238); this run opened no sheet.

## 6. For the Checker (re-measure 3 flagged faces; sources)

1. GF-12 / GF-13 W06: which wedge W.C. carries the 0.60 window (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip,
   P7757.dxf GF plan, layer W at GF-W10; T-175 host row W06; T-128 walk_r3.json GF-13).
2. GF-08 / GF-15 W03 pool glazing band: developed 6.731 vs census 6.57 (same DXF, layer W curved band; T-128 walk
   GF-08 / GF-15; T-150 W03 width).
3. 1F-01 face on 1F-W05 (HEIGHT_DATUM_SPLIT_ROOF): register 3.691 m (ST7757 dxf.dxf roof-slab plan members on 1F-W05)
   vs plaster top 4.04 HELD on the roof mark (p7757_arch_sheet10.pdf section): is the 1F storey interval under the roof
   a structural interval?
Reproduce: `python3 -I research/agents_t237/alsenan_t237.py` (writes the five CSVs + summary.json here); tests
`tests/t237_face_consistency`.

## 7. Verdict proposals, rule, lessons

- W15 / W16 / W26 finish deductions: ENGINE (merged T-238) RIGHT over T-128 r3 (hand: arched outline, T-238 fixture).
- D-GF-05 / D-1F-07 widths: census RIGHT (T-128's own frame rule); T-128 face width is the rebate side.
- W06 room, W03 developed width, the roof-datum split, the masked annex cause: UNRESOLVED (named above, quantities HELD).
- Rule R-T237-1 (proposed, any villa, scope: one face measured by several trades): (a)-(d) of section 2. Provenance:
  this task, from ADVERSARIAL_PROBE 2026-10-23 #3 and ERS s.3 (one element several trades). Regression test with normal
  and adverse cases: tests/t237_face_consistency.
- Lessons-register row proposed (ERS s.7): "A wall height and a finish height on one face are two readings of ONE
  datum: compare them through the members (band = d - slab t, d in a void) before either is released; a single
  held-cause column can mask a second cause (annex datum under 'held opening')."
