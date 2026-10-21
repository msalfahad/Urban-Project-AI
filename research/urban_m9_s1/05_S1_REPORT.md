# 05 S1 report — what worked, what failed, what is incomplete, recommendations

**Scope basis.** No separate S1 prompt was uploaded. S1 therefore means two things together:
- the S1 slice of the M9A roadmap: canonical line and adapters, opt-in outputs, coverage census, rule store, conflict pins, rooms diagnostic;
- the owner's **M9 S1 addendum**: material dimensions, waterproofing rolls, minimum-waste porcelain layouts, room-by-room workbook.

**Status.** S1 stops here. S2 waits for approval.

- Implementation commits: `7a18b39` (S1) and `6c1deb4` (workbook boundary fix). Full-suite record: `TEST_GATE_M9_S1.json`.
- Full suite on `6c1deb4`: **0 code failures**, 7,610 executed and passed (M8: 7,512; +98 S1 tests), 376 blocked by missing data and 136 skipped for an unavailable prerequisite (both unchanged from M8). Gate **INCOMPLETE**.
- Nothing here is quotation-ready. Every line is `MACHINE_ONLY` and the gate stays **INCOMPLETE**.

## 1. Acceptance checks (addendum) — result

| Check | Result | Evidence |
|---|---|---|
| M2–M8 outputs unchanged | **Yes** | `urban_boq_m9 run` and `urban_boq_m2 run` on synthetic villa seed 21 write the same 46 route G files. Only the `run_log.json` timings differ. The frozen route files are byte-equal to `8177ccf` (`test_m9_s1_package`, `test_m9_wrapper_and_census`). |
| No old rule silently overrides a new decision | **Yes** | 1.5.0 replaces UP-STAIR-012, UP-WP-002, UP-WP-003 and UP-GEN-003 by rule_id. Every superseded rule carries its new version in the effective set. Proposals (UP-WP-004 v1.1.0, UP-STAIR-014) stay out unless asked for. Each result names the rule set and its digest. |
| Defaults stored correctly | **Yes** | MEM-URBAN-DEFAULT-1x10 is 1.00 × 10.00 m (10 m²), with 0.10 m side and end laps and the upturn from UP-WP-002@2.0.0 (0.20 m). The tile registry holds 120×60, 60×60 and 160×80 with no invented box data. |
| Room totals reconcile to floor totals | **Yes** | The workbook was recalculated by LibreOffice: 0 formula errors. Room subtotal = its lines; floor = Σ rooms; project = Σ floors. Wherever a room is unresolved the subtotal reads `PARTIAL: x (n UNRESOLVED)` instead of a number. |
| Waste, surplus and BOQ quantities separate | **Yes** | The BOQ net lives on the canonical line. Waste, offcuts, overlap, packs, surplus and spare live on a material result that names the line and never changes its net. A balance check per row reads 0.000. |
| Missing data never invents results | **Yes** | No dimensions → `BLOCKED_RFI` with the question. Polygon → net area exact, layout `BLOCKED (S2)`. No joint width → `JOINT_WIDTH_NOT_ESTABLISHED`. No box data → boxes `UNRESOLVED`. Corners and penetrations are counted but `NOT_QUANTIFIED`. |
| 3 × 2 m bathroom comparison, explicit assumptions | **Done** | `01_TILE_COMPARISON_3x2_BATHROOM.md / .csv` |
| Synthetic roll-layout example | **Done** | `02_MEMBRANE_ROLL_LAYOUT_EXAMPLE.md / .csv` (+ the M9A fixture WP-1) |
| Implemented vs future interfaces | **Done** | `04_IMPLEMENTED_VS_FUTURE.md` |

## 2. What worked

- **Rule store** (`rules/`). The 1.4.0 owner library is a byte copy. The 1.5.0 overlay holds 8 OWNER_APPROVED records and 2 PROPOSED. Digests are recorded and the manifest drift check is clean.
- **Canonical line.**
  - Adapters exist for 7 legacy state vocabularies. They never raise a state, and an unknown state is refused.
  - No price, rate or amount key is accepted. An agent role cannot approve. A measure pair must price one basis.
- **Route G as canonical lines.** On synthetic villa seed 21, 221 lines reproduce the route's planning totals exactly: concrete 76.992 m³ and steel 3,387.367 kg. Line ids are reproducible.
- **Tile layouts, owner 3.00 × 2.00 m bathroom.** Joint 2 mm, minimum cut 0.10 m, minimum reusable offcut 0.10 m, kerf 0, no rotation. All three plans were checked by hand:

  | Size | Role | Layout | Tiles opened | Material | Owner cutting waste |
  |---|---|---|---|---|---|
  | 120×60 | selected | 0° corner/corner | 9 (6 full + 6 cut; 3 opened for cuts) | 6.480 m² | 0.016 m² (0.26 %) |
  | 60×60 | alternative | 0° corner/corner | 17 | 6.120 m² | 0.027 m² |
  | 160×80 | alternative | 90° centred tile/corner | 5 | 6.400 m² | 0.005 m² |

  - The two alternatives are reported as **recommendations only**; the BOQ stays on the selected 120×60.
  - The takeoff skill's 4.2 × 3.6 m grid example is reproduced: 42 / 24 / 15 tiles.
- **Membrane roll plans.**
  - WP-1 fixture: 3 strips covering 2.80 m; 9.600 m² of strip material against 7.360 m² net; 9.740 m² installed. The M9A figures are reproduced exactly.
  - 3 × 2 m bathroom with a 0.80 m door: net 8.160 m² and 2 rolls. Naive shortcuts would say 1 roll, both "net / 10" and "net + 10 %".
  - The roll balance holds on every plan tested: 6 rooms × 3 doorway details × 3 strip directions × 2 offcut settings.
- **Room BOQ and workbook.**
  - Synthetic schedule: 6 rooms on 2 floors, 12 lines, 7 material results.
  - Workbook: 18 sheets with the requested columns and Arial throughout; deterministic bytes.
  - Formula subtotals by room, floor and project.
  - The PROCUREMENT sheet shows per-room packs and pooled boxes.
  - The TILE COMPARISON sheet carries the recommendation-only rows.
  - The UNRESOLVED sheet lists every blocking question.
- **Coverage census.** All 99 families get a terminal state and a reason in every run.
  - On the villa + rooms run: 14 QUANTIFIED, 1 BOUNDED_ONLY, 1 BLOCKED, 7 NOT_FOUND_IN_SOURCE, 32 NOT_RUN, 28 NOT_IMPLEMENTED, 16 BLOCKED_BY_SOURCE.
- **Tests.** `tests/m9_foundation` has 98 tests. They cover rule precedence, schema, adapters, hand-checked formulas, balance properties, workbook reconciliation after recalculation, conflict pins, wrapper no-regression and package hygiene.

## 3. What failed (found and fixed during S1)

1. **Name clash: I overwrote an existing module.**
   - My first material-result module was written to `engine/source/waste_procurement.py`. That file already existed: the V3b rule-driven waste layer used by research builders and an existing V3b synthetic test module.
   - It was caught by `git status` before any commit and restored from git. The S1 schema now lives in `engine/source/material_result.py`.
   - The V3b tests pass (26/26), and the S1 package test pins the V3b file to the base commit.
2. **The price guard rejected the schema's own `price_one_basis` flag.** Fixed with an explicit allow-list.
3. **The route G adapter dropped the item's low/high range for SOURCE_DERIVED items.** Fixed: every quantity state keeps the item's range.
4. **Workbook: the doorway overlap was counted twice** on the membrane material row (balance −0.08 m²). Doorway rows are now counted by item code.
5. **Workbook: subtotals read blank cells of unresolved rooms as 0.** Fixed with the PARTIAL text.
6. **Optimisation objective.**
   - Ranking layouts by the owner-defined cutting waste alone chose layouts that open more tiles (120×60: 12 tiles instead of 9). This happens because retained offcuts count as saved even though S1 never reuses them.
   - The default objective is now "fewest tiles opened, then least owner-defined waste". The owner-waste objective stays available.
   - Both readings are shown in example 01. **Owner decision Q-TILE-1.**
7. **A membrane heuristic made worse plans.** "Use an open roll's tail before opening a new roll" produced more band joints (8 vs 5) and more material. Removed.
8. **Boundary rule (first full-suite run, `7a18b39`): 2 code failures.** `engine/boq_room_workbook.py` sits outside `engine/source` and imported `engine.source.boq_line`; the R8 boundary tests forbid that. Fixed in `6c1deb4`: the workbook takes item labels from the lines it is given. The re-run has 0 code failures.
9. **Firewall.** A test input coincided at three decimals with an external benchmark figure. It was located by line number only, without printing the value, and the input was changed. The S1 outputs had none.

## 4. What remains incomplete

- **Layouts.** Rectangles only. Not supported:
  - polygon, L-shaped or holed rooms;
  - patterns other than straight;
  - perimeter gaps;
  - falls to drains;
  - wall-tile faces with openings.
- **Plan quality.** Both cutting plans are deterministic **feasible heuristics**, not proven minima. The addendum's "minimum feasible waste" means minimum over the 18 (or 9) layouts searched.
- **Room geometry.** Rooms come from a schedule. Reading them from drawings is S2; the existing room_slice still uses the v1.0.0 waterproofing rules (conflict C01).
- **Cross-room optimisation.** No offcut reuse across rooms and no roll-tail pooling.
- **Packaging.** No product data, so boxes stay UNRESOLVED for the owner sizes until a supplier gives pieces per box.
- **Membrane details.** Corner and penetration pieces are counted, not quantified. Only the separate-band upturn method is offered.
- **Trades not measured in S1.** Wall tile, plaster / paint, ceilings, skirting, marble, stair finishes and railing 3D path, doors / windows, aluminium. Their workbook sheets list the families with state and reason only.
- **Conflict pins.** 15 of the 24 rows are pinned in code. The other 9 are scheduled to the slice that touches them (listed in `test_conflict_pins.py`).
- **Opt-in route outputs.** The roadmap's opt-in `--boq-lines` / `--rooms` outputs became the `urban_boq_m9` wrapper, because the M8 freeze forbids editing `urban_boq_m2.py`.
- **Conventions (C17).** `urban_boq_m9 run` records the conventions set and digest, but still accepts a run without `--conventions`. In that case the frozen V3 default applies.
- **Validation.** Synthetic geometry only. No real-drawing or blind validation was done.

## 5. Recommendations (independent)

1. **Owner decisions needed before S2:**
   - Q-TILE-1: the layout objective.
   - Q-WP-1: the doorway detail.
   - Q-WP-2: the membrane system and its data sheet (laps, corners, penetrations).
   - Pieces per box for the three sizes.
   - The Urban standard joint width, minimum cut and minimum reusable offcut. S1 used 2 mm / 0.10 m / 0.10 m as test parameters only.
   - Whether a spare allowance exists, and its basis.
2. **S2 first: rooms from drawings.** Integrate TS01 under the v2 rules, then add polygon layouts by exact rectangle decomposition or 2D nesting. Room geometry gates every finish trade.
3. **Fail loud on conventions** in `urban_boq_m9 run` (C17): refuse a run without `--conventions`.
4. **Keep procurement optimisation separate.** Cross-room offcut and roll-tail pooling belong in a procurement view, never in the BOQ net.
5. **Blind validation needs two or three new villas** from different consultants (Q-DATA-1).
6. **Privacy.** The repository is still public, with client names in many paths (M9A finding 13). That is the owner's decision; nothing was changed here.
