# BOQ engines study (owner-supplied input for the research scout), 2026-10-17

Sent by the owner from a Claude chat session. Nine BOQ / takeoff engines were studied for ideas:

- OpenConstructionERP and OpenTakeoff from their source code. The REA static analyzer mapped their structure; nothing was run.
- Seven commercial tools from their official help pages only. Their licences forbid reverse engineering, so none was decompiled.

No code from any engine was copied here. Both open-source engines are AGPL-3.0, so ideas only.

Scout: please review, confirm or change the proposed verdicts in RESEARCH_LOG.md, and refine the ideas in BOARD.md.
The lead decides which become tasks. Never install or run code from these repos.

## The common pipeline (all nine follow it)

1. Drawing in: DXF/PDF, scale set once and confirmed, each sheet keeps its own calibration.
2. Tagged measurements: areas, wall faces, lengths, counts, deductions. Each records its source entity, author and review state.
3. Recipes (assemblies): one measurement expands into materials and labour via per-unit factors or formulas, with waste per material.
4. BOQ lines: formulas over the measurements, never typed numbers. Each line carries measured, waste-adjusted and order quantity.
5. Pricing: rates come from a cost library and are matched with a score. Composite rates update when a source price changes.
6. Markups and sign-off: markups are sanity-checked, and the approved quantities are frozen as the contract baseline.

Two checks run beside the pipeline:

- Review gate: machine results stay pending until a person commits, withholds or rejects them.
- Revision check: a new drawing version is diffed against the old one, and every linked BOQ line is flagged for review.

## Evidence from code (open source)

### OpenConstructionERP

Repository: https://github.com/datadrivenconstruction/OpenConstructionERP (AGPL-3.0, Python FastAPI + React).
All paths are under `backend/app/modules/`.

- **`boq/models.py` `Position`**
  - A tree of lines with three price tiers (net cost, target, sale), `source`, `confidence`.
  - `risk_dispersion`: how wrong the line could be.
  - `price_basis`: invoice, catalogue or judgement.
  - Money is stored as strings and computed as `Decimal`.
- **`assemblies/models.py`, `templates_seed.py`, `formula_engine.py`**
  - A recipe is a list of components (material, labour, plant). Each has a per-unit `factor`, plus an optional `quantity_formula` over the assembly parameters, e.g. `wall_area * rebar_ratio`.
  - Seeded example, 11.5 cm brick wall per m2: 24 bricks, 0.012 m3 mortar, 0.7 h mason labour.
  - The formula engine supports variables, `if()`, `min`/`max`, `round` and lookup tables, behind a safe evaluator.
- **`norm_expansion/`**: an unpriced production-norm library (labour-h, machine-h and materials per unit), kept separate from priced recipes.
- **`waste_factors/waste_math.py`, `seed.py`**
  - Rule: gross = net x factor, one factor per category.
  - Seeded factors: blockwork 1.05, plaster 1.15, tiling 1.10, concrete 1.03, rebar 1.10, screed 1.05.
- **`cost_match/matcher.py`**: explainable description-to-rate matching.
  - Score = 0.65 x query coverage + 0.35 x term overlap, multiplied by 0.55 when the unit dimension clashes.
  - Bands: at or above 0.75 is confident; 0.45 to 0.75 needs review; below 0.45 is no match, with a hint.
  - Accent folding and multilingual synonyms, including Arabic terms. Factors are returned with every score.
- **`boq/change_review.py`**: a new drawing revision or BIM version raises change flags on the linked lines. The flags are review items only; nothing is auto-changed.
- **`boq/quantity_baseline.py`**: the first lock or approval freezes a snapshot, and later site measurement never overwrites the tendered quantity.
- **`boq/validators.py`**: markup-stack warnings, e.g. contingency on top of profit, an implausible percentage, or a duplicate order.
- **`takeoff/scale_detect.py`**: reads the scale note from the title-block text.
- **`takeoff/recognize.py`**: offline candidates from PDF vectors (areas, lengths, repeated symbols), each with a confidence and a reason.
- **`ai_estimator/service.py`**: Understand -> Group -> Match -> Assemble. Each stage ends in a human confirm, and the LLM never invents a rate.
- **`middle_east_pack/config.py`**: settings only (KWD, Hijri calendar, Sun-Thu week, FIDIC, CESMM4/POMI). It has no Kuwait measurement or material rules.

### OpenTakeoff

Repository: https://github.com/Kentucky-ai/opentakeoff (AGPL-3.0, TypeScript).

- **Model**
  - A sheet carries its calibration.
  - A condition is a finish item with `waste_pct`, `height_ft`, a `multiplier` (xN units) and materials rows `{per, basis, unit, round}`.
  - A shape has exactly one role: floor_area, deduct, surface_area (length x height), linear or count.
- **`web/src/lib/totals.js`**: the order of operations.
  1. Apply xN first.
  2. Apply waste to area and length, never to counts.
  3. Material quantity = basis / coverage, rounded up per item before the buy list is summed.
- **`mcp/src/session.ts`**
  - Skirting = room perimeter minus openings that are stated, never guessed. Gross, openings and the source room are recorded.
  - Finish schedule cells that are ambiguous ("A/B") are refused and listed as unresolved, with their area.
- **`web/src/lib/scopeCollision.js`**: shared floor = sum of the areas minus the union area, and it must be 0. This catches double-counted floor.
- **`web/src/lib/transitions.ts`**: the median gap between room rings separates butt joints (committed) from wall-separated runs (withheld).
- **Review**: every machine shape is stamped `reviewed:false` with its batch. The original geometry is frozen on the first human edit, and only a human can approve.
- **Limits for Kuwait**: it works in feet and is built for US interior finishes. It has no blockwork, lintel or plaster rules.

## Evidence from public docs (commercial)

- **CostX**
  - Coded dimension groups feed the workbook through functions: `XGETAREA`; `XGETWALLAREA` (length x group height); `XGETSPACEDCOUNTRND` (items at centres).
  - Composite rates are built from other rates.
  - Auto-revisioning re-matches old measurements onto the new drawing and keeps a warning on every unreviewed item.
  - Strongest Gulf presence: Dubai office since 2018, with CostX QS jobs in Dubai and Riyadh.
  - Sources: https://www.rib-software.com/en/blogs/rib-costx-functions, https://www.rib-software.com/en/blogs/rib-costx-auto-drawing-revisioning
- **PlanSwift**
  - A property tree in which a child formula reads its parent (`[..\Takeoff]*1.1`).
  - Door and window cutouts are child objects of the wall run.
  - Source: https://constructconnect-help.atlassian.net/wiki/spaces/PSUPPORT/pages/48431425/Useful+Formulas+for+PlanSwift
- **Bluebeam Revu**
  - Quantity Link: an Excel cell is the sum of the markups that match a filter, refreshed live.
  - Compare Documents clouds the differences between revisions.
  - Source: https://support.bluebeam.com/revu/how-to/tips-and-tricks/improve-takeoffs-with-quantity-link.html
- **Togal.AI**
  - Detection outputs net area, gross area, footprint, wall centreline and door widths per room, all at once.
  - Assembly items carry their own waste %.
  - Source: https://help.togal.ai/en/articles/15602901-ai-powered-area-and-wall-detection
- **Cubit**: room picker, door and window library, and revisions that flow into the estimate. Details are uncertain because the guides are not public.
- **PriMus**: every line is backed by measurement rows (parts x L x W x H), with negative rows for openings.
- **Autodesk Takeoff**
  - Symbol detection results stay pending until accepted.
  - A revised sheet lists new instances separately from those already counted.
  - Source: https://help.autodesk.com/cloudhelp/ENU/Takeoff-Takeoff/files/Symbol_Detect.html

## Ideas, ranked for the Alsenan mission (match the freelancer trade by trade)

| # | Idea | Why it helps the scoreboard | Likely home (check with `codemap.py route`) |
|---|---|---|---|
| 1 | Visible deduction rows per wall (`D1 2 x 1.0 x 2.1 = -4.20 m2`, tied to the DXF block) | Blockwork and plaster differences vs the freelancer become explainable line by line | `opening_census.py` / `door_model.py` output feeding the wall line (new method version) |
| 2 | Measured / waste-adjusted / order quantity as three columns | Shows whether a difference is measurement, waste rule or rounding | BOQ output of a new method version |
| 3 | Several variants per room or wall (net, gross, centreline) | The freelancer may use centreline for blockwork and net for plaster; storing both makes the reconciliation exact | `arch_rooms.py`, `arch_walls.py`, `arch_measure.py` |
| 4 | Recipes per unit (block wall per m2 -> blocks, glue, lintels, plaster, labour) | One rule source for derived materials; easier to compare with the freelancer's material lines | recipe file beside `rules/materials/`, read by a new method |
| 5 | Provenance on every quantity (file, layer, entity handle, rule version, reviewed) | Every scoreboard difference can be traced to an entity | BOQ records |
| 6 | Overlap check: shared floor = sum - union = 0 | Catches double-counted floor and tile areas | `robust_geometry.py` (shapely) |
| 7 | Three-band confidence (commit / withhold with location / reject) | Withheld items stay out of totals but are listed as owner questions | `tools/urban_boq_m9.py` output |
| 8 | Skirting = perimeter minus stated door widths, recorded | Skirting is a common freelancer-vs-engine gap | `arch_measure.py` |
| 9 | Revision diff of DXF entities -> flag affected BOQ lines | Needed once a second villa or revision arrives | new tool next to `tools/urban_intake.py` |
| 10 | Explainable price matching and contract baseline | Web app side (UrbanProjectsManager), not the engine | `cost_items` screens, BOQ provider |

Urban already leads on Kuwait-specific rules (white and cement blocks, glue mortar, lintels, tile-size waste, pallets).
None of the nine engines has them.

## Limits

- The study is static only: neither open engine was run on a drawing.
- Commercial internals that were not confirmed: CostX and Bluebeam waste handling, Cubit's data model, PriMus field names, and Autodesk's formula outputs.
- The Urban code was not inspected when the "likely home" column was written. Confirm each with `python3 -I tools/codemap.py route`.
