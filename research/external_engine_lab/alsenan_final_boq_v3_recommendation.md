# Alsenan Final BOQ + Reporting V3 — recommendation (before implementation)

Base: B2A.1 registers (02feef8) and Reporting V2 + QS addendum (b9fef82), both frozen and accepted.
No engine or reporting code has changed for this round. Benchmark firewall: the freelancer workbooks were used only through the
frozen B1 raw-row register, and only as **section and item labels** (no quantity was read or used) to check scope completeness.
The six excluded uploads were not opened.

## 1. The honest starting point

| Area | Today (frozen) | Main reason |
|---|---|---|
| Structural concrete | 213.108 m³ released; necks, ground beams, ground slab, stairs, pool, structural walls BLOCKED; 25 beam / 9 column occurrences blocked | some levels and details not read yet (see §3) |
| Rebar | definitions computed (bar counts and diameters per element); **weight BLOCKED** | cover, laps, hooks treated as missing |
| Rooms (drives flooring, ceilings, plaster, paint, tile, skirting) | **9 certified rooms** (GF 5, 1F 4, **2F 0**); physical floor area 66.2 m² | Arabic room labels are font-glyph encoded and **not decoded**; most plan sites fail closure |
| Blockwork | lengths by thickness computed (150: 75.8 m, 200: 79.2 m); areas BLOCKED | wall termination (beam / slab soffit) unknown on most faces |
| Finishes materials | floor, ceiling, skirting, paint, wall tile BLOCKED_MATERIAL | no finish schedule exists |
| Openings | 24 doors, 28 window candidates, curved glazing length; areas BLOCKED | no head / sill levels |

**Conclusion.** Reporting is not the limiting factor. The architectural trades the brief asks for (flooring room by room,
ceilings, plaster, paint, wall tile) cannot be filled until two generic engine defects are fixed: Arabic label decoding and
room closure on P7757. If we build the 11 workbooks on today's data, most floor sheets will show BLOCKED rows. I recommend
completing the blocker-mastery pass first, freezing, then building Reporting V3 on that freeze, all in this round.

## 2. Source evidence earlier rounds missed (found during this inspection)

Re-reading ST7757.pdf turned up information that changes several blockers.

| Where | What it says | Releases |
|---|---|---|
| p.8 RECOMMENDATIONS, note 22 | concrete cover ≥ **2.5 cm** in columns, slabs, beams; ≥ **7 cm** in concrete against soil | rebar cut lengths |
| p.8 note 9 | development / lap length ≥ **70 Ø** (tension), **40 Ø** (compression) | rebar laps / anchorage |
| p.8 note 18 | normal slab thickness **16 cm** unless stated | default slab t (already used); stair waist candidate |
| p.8 notes 6, 8, 16 | f'c 300 kg/cm², fy 4200 kg/cm², plain concrete 1:3:6 | concrete grades in the BOQ description |
| p.8 note 19 | lift: tie beams at 3.00 m where floor height > 4.30 m | lift-shaft beams |
| p.8 note 21 | side bars 2/3/4 Φ12 in beams deeper than 60 cm | beam rebar |
| p.3 GROUND BEAMS PLAN | **"5Ø10/m E.W., T=10cm"** in two zones (main house +1.00, annex +0.30); ground-beam outlines drawn (untagged); **pool outline** drawn | ground slab, ground beams, pool plan |
| p.13 typical details | ground beam sections by length (30×60 > 5 m, 30×40 < 5 m), exterior "follow arch." | interior ground beams |
| p.7 | swimming pool detail: walls 20 cm, base 40, 10 cm plain concrete, 5 cm membrane, depths "as per arch."; **DOME detail**: span 4.42 m, rise 1.90 m, shell 10 cm, Ø12/15 cm | pool (partly), dome (new scope) |
| p.14 | typical **lift** with isolated footing (no basement), **boundary wall**, parapet details | lift, boundary wall, parapets (new scope) |
| p.16 | typical stair: going 30 cm, landing beams 20×40, stair rebar per m; waist drawn as "THICK" with no value | stair rebar; waist still missing |
| Arch sections A-A / B-B | FFL GF +1.00, 1F +5.50, 2F +9.70, roof +13.90; **annex** at +0.30 with roof +4.30; parapets 50 cm | annex block, parapets |

## 3. Blocker classification

Classes: **A** SOURCE_RESOLVABLE_NOW · **B** GENERIC_ENGINE_DEFECT · **C** OWNER_METHOD_ALREADY_AVAILABLE ·
**D** PROJECT_OWNER_FACT_REQUIRED · **E** SOURCE_IMPOSSIBLE · **F** COMMERCIAL_METHOD_REQUIRED · **G** REPORTING_ONLY_DEFECT.

For every row:
- Q7 (would using the freelancer number be calibration?) is **YES** — none of them is used.
- Q9 (what stays blocked if unresolved) is the "Blocks" column.

| # | Blocker | Blocks | Class | Missing evidence | Resolution proposed |
|---|---|---|---|---|---|
| 1 | Ground slab | CON-GSLAB m³ (+ its blinding, rebar) | **A + B** | none: "T=10cm, 5Ø10/m E.W." printed on the ground-beams plan; earlier register missed the annotation | generic fix: bind slab annotations (T=, mesh) printed on any structural plan to the enclosing slab zone; area = slab zone net of ground-beam bands; two zones (main +1.00, annex +0.30) |
| 2 | Ground beams (interior) | CON-GBEAM m³ | **A + B** | none for interior beams: outlines on plan + p.13 length rule | generic fix: measure untagged beam bands and assign the section from a printed length rule (rule stored as source evidence); status COMPUTED_FROM_TYPICAL_DETAIL |
| 3 | Ground beams (exterior, "follow arch.") | part of CON-GBEAM | **D** (after A attempt) | depth from outer ground (±0.00 / +0.15) to slab level not proved | try section levels first; otherwise one owner / engineer question |
| 4 | Column necks | CON-NECK m³ | **D** | founding / footing-top level not printed; note 12 leaves founding level to site and soil | count and sections (CN, P.C 20×50 / 20×70) computed; height BLOCKED; owner: founding level (or confirm depth from the p.9 depth / bearing table) |
| 5 | Stairs concrete | CON-STAIR m³ | **B + D** | riser count per flight not proved (B); waist not printed (D) | generic: prove riser count from plan tread lines + floor-to-floor; waist: note 18's 16 cm is an interpretation, not a printed value → compute as REVIEW and ask one confirmation |
| 6 | Structural walls | CON-SWALL m³ | **A** (to verify) | the "B.W 20×60" schedule row is very likely the **boundary-wall beam**, not a shear wall; lift walls appear in the p.14 typical detail | re-bind B.W to the boundary wall; locate the lift shaft on the plans; lift walls per note 20; if no lift on the plans, the item is EXPECTED = 0 with evidence |
| 7 | Pool | CON-POOL m³ | **A + D** | plan outline exists (p.3); thicknesses printed (p.7); depths "as per arch." | search architectural sections / plan for pool depths; if absent, one owner question (depths) |
| 8 | Dome (new scope) | concrete, rebar, plaster | **A** | location to confirm on the roof plans | shell area of revolution from span 4.42 / rise 1.90 / t 0.10; status REVIEW (detail N.T.S.) |
| 9 | Beam tag / occurrence issues (GF 18, 1F 7) | part of CON-SUPER | **B**, then **D** per residue | binding tolerance, span count, band-type conflict | generic binding pass with synthetic tests; the residue goes to one image-based owner sheet (not 25 questions) |
| 10 | Column occurrences (9) | part of CON-SUPER | **B**, then **D** | tag binding / several outlines / upper member | same as 9 |
| 11 | F / F10 footing conflict | CON-FOOT (one outline) | **D** | genuine drawing conflict | keep separate and visible; owner / consultant decides (OQ3-S1, already asked) |
| 12 | Rebar weight | REBAR kg | **A + F** | cover and laps now in source (§2); hook / bend lengths, bar shapes and stirrup closing are not printed | weight = Σ count × cut length × kg/m; cut length = member dimension − 2 × cover + hooks + laps (70 Ø / 40 Ø from source); hooks need an Urban detailing method (commercial standard, owner approval); never kg/m³ |
| 13 | Room closure (only 9 rooms, 2F none) | flooring, ceilings, skirting, plaster, paint, wall tile by room | **B** (largest) | 149 / 130 / 48 thin sites per floor fail room-likeness; door / portal closure incomplete | generic: closure at door / portal openings and wall-gap closure for P7757; synthetic tests; Qortuba rerun |
| 14 | Arabic labels not decoded | room names (bilingual), wet-room semantics | **B** | font-glyph encoding (style X-ARAB1B over ANSI_1252) | generic decoder for that font family (glyph map, tested on both projects); labels stay semantic only |
| 15 | GF open site (salon / reception / dining) entrance | GF zone areas | **D** | entrance door / screen / open not drawn | already asked (OQ3-A1); the room engine still certifies the closed parts |
| 16 | Wall termination unknown | blockwork area, plaster | **B** | band covers only part of the wall line | generic: termination per wall segment from the slab / beam bands above (split the face at band ends) |
| 17 | Blockwork area | BLK-150 / 200 area | **C + B** | height = structural interval − termination depth; the interval is already accepted for columns (STRUCTURAL_INTERVAL_FROM_FFL_EQUAL_BUILDUP); **does not need the build-up value** | reuse the existing method once #16 is fixed |
| 18 | Floor build-up per storey | paint height, wall-tile height, finished ceiling | **D or F** | not printed (the p.16 typical stair hint of 5 cm is N.T.S. and typical, so it is not authority) | owner gives the value per storey, **or** approves a firm-wide Urban method (e.g. one build-up for all residential storeys) that travels to future projects |
| 19 | Finish materials (floor, ceiling, skirting, paint, wall tile) | material lines | **F** (+ **G**) | no finish schedule ("the supplied files are all the files") | separate **quantity** from **specification**: release the finish area on the physical measure with "material per specification"; material by room class (dry / wet / service) as an Urban commercial method the owner approves once |
| 20 | Opening heights (windows, doors, curved glazing) | aluminium area, opening deductions, external plaster | **A + B**, then **D / E** | NW and SE elevations are vector in P7757.dxf; SW / NE are raster only | generic: read head / sill from vector elevations (scale-checked against the section levels); raster elevations measured as a second signal (REVIEW); the rest → owner question or SOURCE_IMPOSSIBLE |
| 21 | Door type / material / height | door schedule lines | **D / E** | no door schedule | count by width class from the plan (computed); type and material → owner |
| 22 | Stair finishes and railing | stair finish, railing lm | **B + F** | riser count (as #5); railing geometry is on the plan | railing length from stair / void edges (generic); material → F |
| 23 | External plaster / paint | facades | **A + B**, then **E** | facades from vector elevations; openings from #20; raster facades lower confidence | compute per facade; raster facades REVIEW or BLOCKED |
| 24 | Master-bedroom curved glazing height | curved aluminium area | **A**, then **D** | salon's 3.65 m is not transferable | elevation first, then owner |
| 25 | Annex block (+0.30 / +4.30) | all trades of that block | **A** (scope check) | has a ground slab zone and columns; I have not verified whether today's registers cover it | inventory it explicitly; if missing, add it as its own "OTHER / EXTERNAL" floor block |
| 26 | Boundary wall, courtyard paving, external steps, parapets | external works | **A** (plans, sections, p.14) + **F** (finishes) | not in scope today ("external works not measured") | add as EXPECTED scope with geometry from source; materials per F |
| 27 | Foundation waterproofing / membranes | WP under footings / pool | **A** | membranes drawn on p.7 / p.13 details | add as expected items (area from the elements they wrap) |
| 28 | Gypsum decor, cornices, cove light; plaster corners / beads; spatter dash in wet rooms | finishes extras | **F** | commercial scope, not drawing facts | owner decides whether Urban measures them and by which rule; until then they are listed as EXPECTED / NOT IN URBAN SCOPE (never silently omitted) |
| 29 | Reporting: physical measures shown apart from finish lines; BLOCKED rows dominate | readability | **G** | — | Reporting V3 design (§5) |

**Q4 (generic engine fix?)**:
- yes: 1, 2, 5, 9, 10, 13, 14, 16, 20, 22, 23;
- not needed: 4, 11, 18, 19, 21, 28.

**Q5 (existing Urban method?)**:
- available today: #17 (column / wall interval), the wet-room tile and paint methods (once #18 is decided), and the floor-under-cabinetry method;
- not available: #12 hooks and #19 materials.

**Q6 (owner fact genuinely required?)** — only these:
- #3 exterior ground-beam depth (if sections fail);
- #4 founding level;
- #5 waist confirmation;
- #7 pool depths (if architecture lacks them);
- #9 / #10 residue;
- #11 F / F10;
- #15 GF entrance;
- #18 build-up;
- #20 / #24 heights not on elevations;
- #21 door types.

## 4. Scope check against the human QS workflow (labels only)

From the freelancer section structure (organisation only) the BOQ must also carry the following items, which our prompt or
engine does not list:
- dome concrete + plaster;
- lift walls / pit;
- boundary wall (concrete beam, blockwork, plaster);
- parapets (blockwork, plaster, WP upturn);
- courtyard paving and skirting;
- entrance and stair marble, stair nosing strips;
- pool finishes (floor / wall tiles);
- gypsum decor and cornices;
- plaster corners / beads and spatter dash;
- door / window reveals ("sharshoub");
- elevator door frame;
- internal railing;
- pool annex (pump room walls and floor).

They enter the completeness matrix as EXPECTED items with their own status.

One heading in the human workflow ("basement walls") is not in our source: the sections show natural ground ±0.00 and
GF +1.00, and the lift detail says "without basement". The matrix will record **BASEMENT: NOT IN SOURCE (evidence)**,
not a zero.

## 5. Reporting V3 design (built on the new freeze)

- **One model, many files.** All 11 workbooks, the master summary, both PDFs and the completeness matrix are rendered from one
  frozen reporting model (the V2 engine, extended). That keeps the totals identical across files by construction. Readback
  validates every file against the model and the frozen registers.
- **Every trade workbook** follows the same order:
  - Sheet 1: trade total;
  - then GF / 1F / 2F + ROOF / OTHER + EXTERNAL, each on its own page with a navy floor band, thick divider and floor subtotal;
  - then detailed calculation, and traceability last.
- **Visual style** follows the mock-up: white page, navy headers, green trade headers, light-blue subtotals, green / amber /
  red status, bilingual. Formula text is shown where it helps (e.g. "F: 4 × 0.90 × 0.80 × 0.30 = 0.864 m³"); the value
  itself stays the frozen engine value.
- **Formulas** follow the accepted addendum policy:
  - only totals, subtotals and reconciliation arithmetic;
  - never an engine quantity.
- **Master summary:** a trade × floor matrix (GF / 1F / 2F + ROOF / FOUNDATION / EXTERNAL / TOTAL / UNIT / STATUS).
  - It only adds ADDITIVE lines of one unit per trade line.
  - Different units (m³ vs kg, m² vs nr) get separate rows, never one total.
- **Completeness matrix** (JSON + xlsx + a PDF page), per trade:
  - expected / computed / partial / blocked / not-in-source items;
  - coverage % by item count;
  - blocker reasons and what releases each.
- **Final PDF** (~25–35 pages):
  - master summary;
  - one summary page per trade;
  - floor-by-floor tables at room level;
  - blockers / owner questions;
  - completeness matrix.

  The technical audit PDF carries handles, registers, digests, QA and the benchmark evaluation (after the freeze).
- **10_QS_RECONCILIATION.xlsx** reuses the accepted 08 sheet design (locked Urban values, yellow inputs, difference / status
  formulas), split into one sheet per trade.

## 6. Proposed order of work (one round, two freezes)

1. **Source re-mining** (no engine change), items #1, 2, 6, 7, 8, 12, 25–27:
   - read the evidence in §2 into a SOURCE_EVIDENCE register;
   - commit.
2. **Generic engine fixes**:
   - priority order: #14 labels → #13 room closure → #16 termination → #1 / #2 structural annotations → #12 rebar cut
     lengths → #5 riser proof → #20 elevation heights → #9 / #10 binding;
   - each fix gets synthetic tests first and a Qortuba rerun (no Qortuba-specific code);
   - Qortuba stays RC1_REFERENCE; any Qortuba quantity change is reported as a regression finding, never patched.
3. **Alsenan rebuild → registers built twice (byte-identical) → freeze V3a.** Benchmark evaluation only after this freeze.
4. **Reporting V3** on the V3a freeze:
   - build twice (byte-identical), readback, LibreOffice recalc;
   - package;
   - ONE full suite from the final commit;
   - final report in your format.
5. **Owner questions** are sent once, batched by trade, after step 3 has exhausted the source. The exception is the four
   method / commercial decisions below, which no drawing can answer and which save a round if decided now.

Risk: steps 2b (room closure) and 2a (glyph decoding) are the largest. If either does not reach a defensible result, I will
freeze what is proven and ship Reporting V3 with those rows honestly BLOCKED, not stretch the round with unproven geometry.

## 7. Decisions I need from you (only method / commercial; no drawing can answer them)

1. **Floor build-up**: give it per storey, or approve one Urban build-up method for residential storeys (it would apply to
   future projects too).
2. **Finish quantity vs specification**: may Urban release finish areas (floor, ceiling, skirting, paint, wall tile) on the
   physical measure with "material per specification", plus a default material by room class (dry: porcelain; wet: ceramic;
   ceilings: gypsum board) as an Urban commercial method? Without this they stay BLOCKED_MATERIAL.
3. **Rebar detailing method**: hooks / bends (e.g. standard 90° / 135° hook lengths by diameter), stirrup closing length and
   whether laps are counted at stock-length breaks (12 m bars). Cover and lap lengths come from the drawings.
4. **Extras scope**: should Urban measure gypsum decor / cornices / cove light, plaster corners and beads, spatter dash and
   reveals ("sharshoub") as separate BOQ items? (Yes / no per item.)

Questions that wait for the source pass (asked only if the source still fails):
- F / F10 (open);
- GF entrance (open);
- founding level;
- stair waist confirmation;
- pool depths;
- exterior ground-beam depth;
- opening heights not on vector elevations;
- door types;
- the beam / column residue (one image sheet).

## 8. Answer to Q10 — where I disagree with the proposed completion strategy

1. **Order.** The brief leads with workbook layout. The binding constraint is room coverage (9 rooms, none on 2F) and label
   decoding. Polishing 11 workbooks first would present a mostly blocked BOQ beautifully. Engine first, reporting on the new
   freeze.
2. **"Blocked material" is partly a reporting / policy issue, not a source issue.** A QS normally measures the finish area and
   leaves the specification to the BOQ description. With your approval (decision 2) a large part of the architectural BOQ
   becomes quantity-complete without inventing a material.
3. **Rebar is closer than "blocked" suggests.** Cover and laps are printed (p.8). Only hooks and shapes need an Urban method.
   A deterministic weight is achievable this round for footings, columns, beams, slabs and the stair detail. Pool and dome
   follow their geometry.
4. **Blockwork area does not need the build-up value.** It needs the wall termination (an engine defect). Linking it to
   build-up, as today's register does, over-blocks it.
5. **Separate workbooks are fine for reading, risky for consistency.** They must come from one frozen model with cross-file
   readback, or totals will drift between files.
6. **"Full foundation blinding vs isolated".** The source is a typical detail of isolated footings (10 cm plain concrete
   under footings), now also under the ground slab / beams once released. "Full site blinding" has no source and stays
   out unless you decide otherwise.
7. **Coverage %.** It should be by item count per trade (as in V2), because quantities in different units cannot be added.
   A quantity-weighted % would be misleading for trades with blocked items of unknown size.
8. **A 20–35 page PDF is achievable** if floor detail is shown at room level and occurrence-level tables (beam / column
   occurrences, handles) move to the technical audit PDF.
9. **External works and extras.** The brief's trade list omits the dome, lift, boundary wall, parapets, courtyard and annex,
   all of which the source shows. Leaving them out would make the BOQ look complete when it is not. I add them as expected
   scope.

## 9. Gates for this recommendation

- ENGINE_CHANGED = NO
- QUANTITIES_CHANGED = NO
- IMPLEMENTATION_STARTED = NO
- BENCHMARK_QUANTITIES_USED = NO (labels only, for scope)
- NEXT: your answers to §7 (or "proceed with defaults: keep blocked"), then implementation.
