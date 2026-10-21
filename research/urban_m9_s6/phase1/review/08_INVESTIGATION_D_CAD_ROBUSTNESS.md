# Investigation D: CAD robustness, case by case

What decides the action column:
- **Fix the parser** when the information is in the file and is read wrongly.
- **Fix interpretation** when it is read correctly but turned into the wrong element.
- **Improve semantic classification** when the element is right but its role or kind is wrong.
- **Require reviewer confirmation** when the drawing is legitimately ambiguous.
- **Block** when measuring would be guessing.

Evidence: the Phase 1 sweep (31 synthetic variants through the production CLI) and the reference plan's discovery report. File and line pointers are into commit c757d8a.

**Root cause shared by four rows:** fills (HATCH) reach the plan reader through `tools/urban_intake.py:150-157`:
- `doc.modelspace().query("HATCH")`, top level only;
- the first boundary path only (`paths[0]`);
- edge **start points** only, so arc-edged fills become chords;
- no layer-0 inheritance.

Lines and arcs reach the plan reader through the K2 kernel, which handles nesting, MINSERT, OCS and reflection correctly. **One parser fix, fills from the K2 / `arch_discovery.shapes()` path, addresses rows 1, 2, 3 and 4.** `urban_intake.py` is pinned by the M7 / M8 freezes, so the fix belongs in the V2 path (`shapes()` feeding V2's `ents["hatches"]`), with V1 unchanged.

| # | Case | Phase 1 state | Root cause (where) | Action | Why this action, not another |
|---|---|---|---|---|---|
| 1 | Nested INSERT (2–3 levels) | FLAGGED: rooms change; `FILLS_NOT_READ_IN_PLAN` (reference plan nested 2 deep: a bedroom alcove split off as UNLABELLED) | fills read one block level only (intake HATCH) | **Fix the parser** (fills from K2 at every depth) | the geometry is unambiguous; nesting is a transport detail |
| 2 | MINSERT (column arrays) | FLAGGED | K2 expands the cells' lines (`multi_insert`), but their fills are not read | **Fix the parser** (the same fix) | as above |
| 3 | Layer-0 inheritance (block content on layer 0, INSERT on COLUMN) | FLAGGED for columns | inheritance is done for segments / arcs (`urban_intake.py:65-71`), not for fills | **Fix the parser** (the same fix) | standard CAD semantics; no judgement involved |
| 4 | SOLID / TRACE / HATCH fills; arc-edged hatches | FLAGGED (SOLID-only columns lost) | SOLID is a CARRIED kind (K2 `CARRIED_DXF`), not geometry; hatch arc edges dropped | **Fix the parser**: SOLID / TRACE as polygons, hatch edge paths flattened with a chord tolerance; then **interpretation**: a fill is column evidence only with an outline or a column-role layer | fills are evidence of material, not outlines by themselves |
| 5 | Exploded columns (four LINEs + HATCH) | FLAGGED | the column role needs filled / crossed rectangles; outlines from lines exist (`DM.closed_rectangles`), but the fill association fails (row 4) | **Fix interpretation** after the parser fix | — |
| 6 | Rotated columns / plans at 30° | FLAGGED (plans 30° inside upright frames) | axis-aligned rectangle tests; **and** the float-threshold defect bites hardest on rotated geometry (Investigation A: a 100 mm piece kept about 50 % of the time at a random angle) | **Fix interpretation** (oriented rectangles) **+ robust predicates (S6R-A1)** | rotation is metamorphic; the result must not depend on it |
| 7 | Fewer than three columns | SEE_DETAIL (hand truth) | the COLUMN role needs at least 3 filled rectangles on a layer (`arch_plan.layer_roles`) | **Improve semantic classification** (per-element evidence: outline + fill + coincidence with the structural plan), **require reviewer confirmation** below the role threshold | a layer role inferred from 2 samples is a guess; ask instead |
| 8 | Scaled door blocks (non-uniform / mirrored) | FLAGGED `DOOR_SYMBOLS_DISTORTED` | under non-uniform scale an ARC becomes an elliptical arc (K2 records it); the swing test assumes a circle radius | **Fix interpretation** (the swing from the ellipse axes along the leaf) + **reviewer confirmation** when the axes differ by more than 5 % | a stretched door symbol may be a deliberate wide door or a drafting error |
| 9 | Arabic diacritics (shadda, tanween), tatweel, letter variants | not silent: the room goes UNLABELLED with an `ARCH.SPACE` RFI | the lexicon matches exact words | **Improve semantic classification**: normalise before matching (strip U+064B–U+0652 and U+0640; unify alef / ya / ta-marbuta variants) | deterministic and small; no reviewer needed |
| 10 | Pre-2007 `\U+XXXX` text escapes | FIXED in the architectural route; route G's intake still raw (S6-TXT-01) | route G reads text through the frozen intake | route G: **owner decision** (frozen); architectural route: done | do not modify the frozen route without a versioned correction |
| 11 | XREF | missing XREF: FIXED (exit 2 `XREF_NOT_SUPPLIED`, or `--accept-missing-xref`) | external files are not resolved | **Block** unless supplied or accepted; then **parser**: bind supplied XREFs through K2 | a missing XREF is missing geometry; never measure around it silently |
| 12 | Paper-space viewports | FIXED: exit 2 `PAPER_SPACE_SHEETS` (or `--region`) | viewport transforms, clipping and scale are not read | **Block** now; **parser** later (Phase 3: viewport → model transform + clip) | a plan visible only through a viewport needs its scale and clip; guessing them corrupts every area |
| 13 | Multiple plans per sheet | two plans in one frame: FIXED (EMPTY_BANDS split, never through geometry); a cut through geometry: exit 2 | — | remaining risk: a detail / enlargement at another scale inside the same frame. **Semantic classification** (scale from dimension values vs geometry, text height) + **reviewer confirmation** | an enlargement measured as a floor is a silent doubling |
| 14 | LINE / LWPOLYLINE / bulge / ARC / CIRCLE / ELLIPSE | parsed correctly by K2 (bulges to arcs, OCS, reflections) | **curved walls**: `opening_census.arc_bands / arc_gaps` exist but are not wired into the architectural band path (`arch_plan._bands` is straight-only) | **Fix interpretation**: wire arc bands; until then a **REVIEW** flag on arcs paired at a wall thickness | the reference plan has a round stair; curved walls without openings or wall run are a silent omission |
| 15 | SPLINE, MLINE, 2D POLYLINE; RTEXT, ARC_DIMENSION, unknown kinds | SPLINE / MLINE / POLYLINE are read by the architectural intake (`tools/arch_intake.py`: SPLINE flattened to 1 mm chords, at any nesting depth); ELLIPSE as chords. Stage 1 warns `ENTITY_KIND_NOT_MEASURED` for the rest (reference plan: 3 RTEXT, 1 ARC_DIMENSION) | these kinds reach the plan reader through a second path beside K2 | RTEXT / unknown: **REVIEW** with counts. Longer term: one reader path (K2) for every kind (R1) | NSD-1: every entity consumed, classified or flagged; two reader paths are two places to get it wrong |
| 16 | Dashed / hidden lines (linetype) | not handled: a dashed line is geometry like any other | linetype is not read | **Improve semantic classification**: hidden / dashed / centre linetypes are never room boundaries or wall faces; they are overhead / below evidence (beams, soffits, voids) | a dashed overhead beam closing a room is a silent area error |
| 17 | Dimension entities and text | not read: **388 DIMENSION entities on the reference plan**, with a warning | — | **Parser** (DIMENSION as annotation, never geometry), then **semantic**: use the measured values as **independent evidence** (opening widths, wall thicknesses, room sizes) for NSD-8 | the cheapest independent check available: the drafter's own numbers |
| 18 | Hidden / frozen / OFF layers | REVIEW `HIDDEN_LAYER_CONTENT`; an old room word on a frozen layer: FLAGGED | the reader ignores layer state | **Parser** (honour the layer state by default) + **REVIEW** listing what was ignored | a frozen layer is the drafter saying "not this" |
| 19 | SHX-encoded Arabic text in an unmapped font | **51 texts undecoded on the reference plan** (font `x-arab1b`). Recorded only in `RUN_RULES.arch_reader.undecoded_fonts`; **no discovery finding** | the SHX keyboard map covers other fonts only | **Parser** (a mapping table for the font, verified on known words) + a stage-1 **REVIEW** finding with the count and positions until then | undecoded text can be room names; a room left unlabelled because its name was unreadable is a classification error the reviewer cannot see |

## Ranking for Phase 2 (reliability gained per unit of risk)

1. **Robust predicates** (row 6 + Investigation A). Every rotated or site-offset drawing is at risk.
2. **Fills from K2 at every depth, layer-0 inheritance, SOLID** (rows 1–4). One change behind the V2 flag clears four flagged rows.
3. **Element conservation for doors** (Investigation B / C, NSD-2). This is not a CAD-reader item, but it is the largest silent omission found.
4. **Dimension values as independent evidence** (row 17).
5. **Diacritic normalisation** (row 9) and **linetype semantics** (row 16).
6. **Curved walls** (row 14) and **non-uniform door blocks** (row 8).
7. Defer: paper-space viewports and XREF binding (until a drawing needs them; blocked meanwhile).
