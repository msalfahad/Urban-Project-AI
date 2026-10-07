# 17 Test fixture backlog (tiny synthetic fixtures)

Rules for every fixture:
- generic, a few entities, no Alsenan coordinates, no donor value;
- the expected answer is derived from the fixture geometry itself;
- each fixture names the crosswalk row that motivated it.

Nothing here is implemented in this round. Priorities:
- **P0:** before S4 (tests only).
- **P1:** with the next GB / slab / wall change.
- **P2:** later.

| ID | Fixture | Entities | Expected result | Motivating evidence | Target module | Priority |
|---|---|---|---|---|---|---|
| GB-01 | Two true parallel beam faces | 2 lines, 300 apart, 4000 long, layer `1` | one band, length 4.000, width 300 | 03 SAME_OBJECT_SAME_RESULT rows | GB band builder | P1 |
| GB-02 | False parallel pair | 2 lines 300 apart on a stair-tread layer, plus a third face between them | no band; reject reason recorded (layer / intervening face) | christiannp 134 LAYER_NOT_ALLOWED, INTERVENING_FACE | GB band builder | P1 |
| GB-03 | Fragmented mate | face A 4225; faces B1 1000 + B2 3225 collinear on the other side | two bands (1.000 + 3.225); total = 4.225; no double area | 03 S008 (URBAN_MISSED_PHYSICAL_OBJECT) | GB band builder (multi-partner) | P1 |
| GB-04 | Beam crossing | two 300 bands crossing at 90°, one face of each broken at the crossing | 4 bands or 2 bands, but the invariant length is the same either way; the crossing node has degree 4 | 04 B segmentation | GB comparison / topology QA | P1 |
| GB-05 | Curve with unequal sweeps | concentric arcs r = 2250 (96–264°) and r = 2550 (110–260°) | length = angular overlap × mean radius (150.1° × 2.40 m = 6.287 m), not the longer sweep | 03 S044 (+0.718 m) | `_arc_bands` | P1 |
| GB-06 | Partial-width column | 300 band; 200-wide column offset to one side over the band | both split conventions are reported, with a declared CONVENTION_ID | 03 F rows (9.051 against 16.256 m) | GB span split | P2 |
| GB-07 | Free-end stub | band ending 1 m from any support | span measured + FREE_END QA flag | 04 D (4 free ends) | GB topology QA | P2 |
| SL-01 | Void bounded by an opening-layer edge | slab outline + an S-OPENING rectangle edge + X cross + a `T` / `16` tag outside the void | void face and slab face separated; no OPENING_CONFLICT | 10 GF void (27.08 = 20.15 + 6.98) | `slab_region.regions` | P1 |
| SL-02 | Pit box in a ground slab | GB cell + closed S-BW box inside it | the box is a void, not slab | 05 FP1-C99368_44772 (URBAN_FALSE_POSITIVE) | `ground_slab_recovery` barriers | P1 |
| SL-03 | Radial fan | ≥ 6 opening-layer lines from one centre in a face | AMBIGUOUS_VOID (scenario pair), not OPENING_VOID | 10 1F fans | `slab_region` roles | P2 |
| SL-04 | Stacked thickness tag | TEXT `T` above TEXT `16` (separate entities) | t = 16 cm; the `T=` grammar is not required | 10 THICKNESS rows (christiannp miss) | slab thickness ladder (regression guard) | P1 |
| WL-01 | Door gap | wall faces broken by a 900 door block (leaf + arc) | wall metres exclude 0.900; the door-swing box does not deduct wall beyond the leaf | 07 opening split (Urban 53.96 against christiannp 9.94 m) | `wall_band_reconciliation.classify` | P1 |
| WL-02 | Column overlap | 200 wall pair running through a 300 × 300 column box | 0.300 COLUMN_OVERLAP; the rest PHYSICAL | 07 COLUMN rows | `classify` | P2 |
| WL-03 | Duplicate wall face | the same face drawn twice (< 5 mm) plus the partner | one pair; duplicate recorded once | 07 DUPLICATE rows (32.45 m) | Method B | P2 |
| WL-04 | Non-nominal width | two faces 400 apart, 1400 long | a pair is found (width-agnostic census), width 400 recorded | 07 GF_WP0638 | Method B | P2 |
| FT-01 | Two footing tags in one outline | 1 outline 3250 × 1400 + tags `F` and `F10` inside; schedule F 900 × 800, F10 2800 × 1400 | SOURCE_CONFLICT with hypotheses {2 × F, F10, drawn outline}; never nearest-wins | 08 FO20 / FTG-CONFLICT_F_F10 | S4 footing occurrence intake | **P0** |
| FT-02 | Tag without geometry | tag `F5` with no outline within 2500 | TAG_WITHOUT_OUTLINE terminal; the count is not created from the tag | christiannp `NO_OUTLINE_WITHIN_2500` route | S4 footing occurrence intake | **P0** |
| FT-03 | Geometry without tag | closed S-FOOTINGS rectangle with no tag | OUTLINE_WITHOUT_TAG terminal; measured, type unresolved | 08 | S4 footing occurrence intake | **P0** |
| FT-04 | Header-position ATTRIB binding | FT-like block whose tag names W / H / DEPHT sit under the L / W / H header texts | the binding is derived from the header geometry; a mismatch with the fixed table raises a conflict | MD02 | S4 schedule reader (test only) | **P0** |
| RB-01 | Ambiguous bar token | `2%%c14/20cm`, `%%c12/20cm`, `* ST. OF COLUMN- 6%%C8/m` | one normalised form per token across every applicable parser (count / diameter / spacing / per-m kept) | 11 SPLIT rows | bar-parser parity test | **P0** (S4 subset) / P1 (all) |
| RB-02 | Split count / diameter cells | ATTRIB cells `13` and `12`; `9` and `14/m` | 13 × Ø12; 9 × Ø14 per m | 11 cell-pair rows | `bar_from_cells` (regression) | **P0** |
| RB-03 | BOXED pair | `3+4` | NOT a bar token; BLOCKED_SEMANTICS; no parser accepts it | 11 BOXED rows | S4 census | **P0** |
| BM-01 | Same mark on two distinct members | two parallel 200 bands 1.2 m apart, one tag `B6` between them, schedule B6 250 | AMBIGUOUS, unless exactly one band is parallel + within extent + width = schedule (± 30) → bound; tie-break recorded | 06 URBAN_BINDING_FAILURE (6) | `beam_binding` tie-break | P2 |
| BM-02 | Horizontal tag on an oblique member | 45° band + 0° tag text on it | bound via member geometry, not text rotation | 06 CHRIS_BINDING_FAILURE (B7, B4) | `beam_binding` (regression) | P2 |
| BM-03 | Drawn width differs from the schedule | 250 band + tag of a 200 schedule mark | bound + DRAWN_WIDTH_DIFFERS_FROM_SCHEDULE flag; the quantity carries both widths | 06 SOURCE_CONFLICT (7) | `beam_binding` | P2 |
| CO-01 | Planted column | outline on roof plan N (hatch ANSI35) only, none below | the storey interval starts at N; no interval below | 09 DONOR_FALSE_POSITIVE (3) | column chain (regression) | P2 |
| ST-01 | Strap beam inside footings | strap faces running 1 m into each of two footings | clear length = face overlap − 2 × 1 m | 03 STRAP rows | strap length (regression) | P2 |
