# ALSENAN — Round 5: architectural BOQ truth engine

**Scope:** rooms, walls, wet areas, openings and finishes.

**Baseline:** `ae62b1b` (Round 4).

**Rebar is frozen.** No Round 3 or Round 4 rebar quantity, claim, BBS or register was touched; `test_rebar_untouched` checks this by hash. Structural contradictions found here are recorded as `CROSS_DISCIPLINE_FINDING`.

**Benchmark firewall.** The human / contractor figures were read only after three steps were complete:
- the registers were frozen (built twice, identical);
- the INDEX hashes were verified;
- the Round 5 tests had passed.

That reading is `post_freeze_arch_benchmark.py` → `POST_FREEZE_ARCH_BENCHMARK.json` (`use: FINDING_ONLY`). No engine code was changed after it.

**The question:**
> Can the engine account for every architectural quantity-bearing object in Alsenan without silently losing, merging or double-counting it?

**Answer:** yes for accounting, not yet for release.

Accounting:
- Every admitted source object ends in a terminal state.
- The floor plate is conserved on every floor (unaccounted 0).
- The wall ledger is conserved (2,788.23 m admitted = 2,788.23 m classified).
- Silent disappearances = 0.
- Conservation `pass = True`, with all 9 mutation-proof checks.

Release:
- About 36 % of floor area still has a blocked or provisional class.
- All masonry is PROVISIONAL, because material identity rests on convention.
- 27 of 60 openings have no height.

## 1. Model

Three layers are kept apart: **physical space ≠ semantic zone ≠ trade measurement region**.

- **Route A** is the production sites (vector topology on the canonical measurement input).
- **Route B** is a new independent planar half-edge shadow (`engine/source/planar_shadow_topology.py`). It is built from layers 1, W, S-COL.BON and 5, plus door-swing closures and mutually facing gap bridges (0.3–3.6 m).
- **Route C** is the architect's area sheet. It is used for the floor-plate cross-check only.

A connected polygon never becomes one treatment region by default:
- A mixed space is split only along Route B faces (positive evidence).
- Otherwise it stays `MIXED_UNRESOLVED`.

Wall pieces come from paired faces (60–450 mm). Each piece gets exactly one terminal class from `WALL_CLASSES`. Masonry needs four things:
- paired faces;
- the wall layer;
- a structural registration (not inside RC);
- the Urban convention.

The material therefore stays PROVISIONAL.

Opening heights use a ladder:

`EXACT_SOURCE > TYPE_SCHEDULE > CROSS_VERIFIED_REPEATED_TYPE > OWNER_PROJECT_FACT > SCALED_SOURCE_SINGLE > URBAN_FALLBACK > BUDGET > BLOCKED`

Windows and glazed-door candidates may not use URBAN_FALLBACK or BUDGET. There is no default window height.

## 2. Results (frozen registers)

| Item | GF | 1F | 2F | Notes |
|---|---|---|---|---|
| Physical spaces (SPACE) | 12 | 10 | 3 | + wall bands 102/80/33, slivers 69/68/22, shafts |
| Recovered rooms (Route B) | DRIVER 7.87, pool 8.57, unlabelled 5.0, 1.25 | BATH 5.02 | – | orphan labels recovered |
| Route A vs B | 8 MATCH, 2 A coarser, 2 partial | 6 MATCH, 2 B coarser, 2 partial | 2 MATCH, 1 partial | TOPOLOGY_DISAGREEMENT records |
| Floor plate (structural) | 322.41 | 217.20 | 55.48 | architect sheet 319.99 / 211.44 / 55.08 |
| Unaccounted plate | 0 | 0 | 0 | residuals UNRESOLVED_BLOCKED |
| Internal floor (VC / PROV) | 85.35 / 160.23 | 162.73 / 5.02 | 43.50 / – | GF includes stair 14.64 |
| Masonry centreline 150 / 200 m | 27.98 / 81.21 | 46.26 / 47.87 | 8.70 / 25.09 | ambiguous 10.35 / 9.95 / 3.25 |
| Blockwork net 150 / 200 m² | 119.90 / 310.57 | 150.25 / 173.82 | 33.06 / 88.17 | PROVISIONAL; around openings 46.86 extra |
| Ceiling (VC / PROV) | 70.71 / 144.23 | 162.73 / 5.02 | 43.50 / – | void, stair well and shaft excluded |

### Wall ledger
- Admitted 2,788.23 m; classified 2,788.23 m; unaccounted 0.
- Masonry 237.1 m; RC inside band 35.4 m.
- No RC_WALL was found.
- The material interpretation covers 92.1 % of the wall length.

### Openings (60)

| Measure | Breakdown |
|---|---|
| Type | 23 internal doors · 4 external doors · 9 windows · 24 glazed-door candidates |
| Height authority | 1 EXACT · 11 CROSS_VERIFIED · 18 SCALED_SINGLE · 3 BUDGET · 27 BLOCKED |
| Area | 12 VC · 21 PROV · 27 BLOCKED |
| Host wall / adjacency | 59 / 54 VC |

### Finishes

| Item | Quantity |
|---|---|
| Floor internal | 456.83 m² (VC 291.58 / PROV 165.25) |
| — dry porcelain | 205.01 |
| — wet ceramic | 72.80 |
| — marble stair | 14.64 |
| — material unknown | 164.39 (mixed GF-Z04 121.5 + unlabelled + unassigned pieces) |
| Ceiling | 426.19 m² (VC 276.94 / PROV 149.25) |
| Skirting released | 176.99 m (VC 17.3 + LOWER_BOUND 159.69) |
| Skirting blocked | 102.36 m in non-dry / mixed regions; 35.16 m on glazing edges |
| Waterproofing floor | 72.80 m² (VC 38.46 + PROV 34.35) |
| Waterproofing upturn | 139.53 m path (0.15 m; doors counted, not deducted) |
| Wall tile | 366.57 m² net, PROV (openings deducted, reveals 0.25 m added on L/R/top) |
| Plaster | 778.47 m² (VC 175.14 + PROV 603.33) |
| Paint | 531.55 m² PROV |

Plaster and paint each have their own height. The METHOD_SENSITIVITY_REGISTER lists the alternatives for each.

### External facade, PROVISIONAL
- GF: gross 238.2 m², net 210.6 m² (11 openings not deducted).
- 1F: gross 113.9 m².
- Blocked: party walls, plinth and finish system.

### Stairs
- Tread lines: PROVISIONAL.
- Blocked: risers, landings, handrail and stair skirting.

## 3. Scorecard V3

There is deliberately no aggregate figure.

| Metric | % |
|---|---|
| Physical space accounting | 93.2 (100 incl. blocked residual) |
| Geometry confidence | 26.3 |
| Semantic / trade-region coverage | 64.0 |
| Wet room accounting / bound | 100 / 88.2 |
| Wall length accounting | 100 |
| Wall material interpretation | 92.1 |
| Opening count / area | 100 / 55 |
| Floor / ceiling completeness | 63.8 / 60.6 |
| Skirting path | 89.9 |
| Wall tile / WP | 100 / 100 |
| Plaster-paint | 66.6 |
| Provenance | 100 |

## 4. Post-freeze benchmark (finding only)

| Human line | Human | Engine | Δ % | Class |
|---|---|---|---|---|
| WP wet floor | 72.01 | 72.80 | +1.1 | AGREES |
| WP upturn (perimeter) | 144.61 | 139.53 | −3.5 | AGREES (human unit ambiguity) |
| Ceiling gypsum dry + wet | 409.58 | 426.19 | +4.1 | AGREES (numeric) |
| Floor all | 409.58 | 442.20 ex-stair | +8.0 | DIFFERENT_SCOPE |
| Skirting all | 282.85 | 176.99 released | −37.4 | UNRESOLVED (released + blocked = 279.35) |
| Wall tile wet rooms | 433.83 | 366.57 | −15.5 | DIFFERENT_METHOD |
| Blockwork all | 1,260.69 | 875.78 | −30.5 | ENGINE_LOW |
| — external + 20 cm | 643.44 | 572.56 | −11.0 | ENGINE_LOW |
| — 15 cm | 617.25 | 303.21 | −50.9 | ENGINE_LOW |
| Plaster internal | 1,151.14 | 778.47 | −32.4 | ENGINE_LOW |
| Paint internal | 1,191.13 | 531.55 | −55.4 | ENGINE_LOW |
| Plaster external | 1,469.97 | 400.01 | – | DIFFERENT_SCOPE |
| Railing / stair skirting | 18.95 / 29.87 | BLOCKED | – | UNRESOLVED |
| Pool, yard, roof WP, cornice | – | not measured | – | DIFFERENT_SCOPE |

On the wall tile row, the human figure equals the plaster sheet subtotal "bathrooms and kitchens", which is a spatter-coat backing area. The engine figure is full-height tile to the finished ceiling.

### Room by room

Of the 28 human floor rows:
- **21 AGREE** within 5 % (most within 1 %).
- 1 ENGINE_LOW: 1F bedroom 17.29 vs 16.34.
- 2 DIFFERENT_SCOPE:
  - GF reception + dining 137.5 vs the mixed region 121.5;
  - 1F living 38.96 vs 63.66, which includes the landing around the void.
- 5 UNRESOLVED: the human labels have no engine label:
  - entrance hall 10.46;
  - 2F corridor 7.7;
  - diwaniya washroom 4.73 + 1.7;
  - 1F bathroom 2.59.

### Human lines
- **HUMAN_FORMULA_ERROR candidate:** marble + yard total `H44 = SUM(H13:H41)` includes the yard 151.8, which is also reported separately on the cover.
- **Reused numbers (DIFFERENT_METHOD):**
  - skirting = dry cornice = 282.85;
  - wet gypsum = WP floor = 72.01;
  - wet cornice = WP upturn = 144.61;
  - wall tile = plaster spatter subtotal.

## 5. What worked
- The Route B half-edge shadow topology recovered 5 rooms that Route A lost (DRIVER, pool, 1F BATH and two unlabelled regions). The orphan-label register gives every label a terminal outcome.
- Bilingual-twin placement moved the "Wash" label into the actual washroom instead of the DEWANEYA.
- Wet rooms and named dry rooms agree with the human sheet to within 1 % (21 of 28 rows).
- Waterproofing agrees within 1.1 % (floor) and 3.5 % (path).
- Conservation holds everywhere:
  - floor plate unaccounted 0;
  - wall ledger unaccounted 0;
  - source coverage: 0 unterminated objects;
  - silent disappearances 0;
  - the mutation checks catch duplicate / unknown / negative components.
- Masonry around openings uses one engine rule (above head + below sill), which removed the window-sill double count.

## 6. What is not working
- **Blockwork 15 cm is about half the human figure.** Engine centreline is 82.9 m; the human area implies about 150–160 m. Candidate causes, not yet tested:
  - partitions drawn on layers other than wall layer 1;
  - single-line partitions not paired;
  - the 23.55 m of ambiguous width.
- **Plaster and paint are 32 % and 55 % low.** Paint has no VC rows. The likely gap is mixed / unassigned regions and the paint-height method.
- GF-Z04 is still one 121.5 m² MIXED_UNRESOLVED region: SALOON / RECEPTION / DINING plus the Wash lobby. The entrance hall (10.46) is not separated.
- Glazed-door candidates (24) block 35 m of skirting continuity and the opening areas. 27 openings have no height.
- 1F W.C and the circular void remain BLOCKED_TOPOLOGY. Two strict XFAILs track them:
  - `test_GF_Z04_wash_zone_resolved`;
  - `test_1F_wc_closed`.
- The structural plate is larger than the architect sheet: GF +2.42 m², 1F +5.76 m² (CROSS_DISCIPLINE_FINDING).

## 7. Recommendation for Round 6
1. **Wall source exhaustion for 15 cm partitions.** Trace each human-implied partition against every DXF layer, with blocks exploded. Admit single-line partitions only with paired-face or dimension evidence. Re-run the ledger with a new freeze.
2. **One owner batch of 4 decisions:**
   - masonry identity (releases 875.8 m²);
   - finished ceiling level and build-up (898 m² of paint / tile height);
   - the 24 glazed-door candidates (window or door);
   - the GF-Z04 Wash / entrance boundary.
3. **Plaster/paint audit.** List, per region, which face metres feed plaster but not paint, and why. Then add a paint VC path where the heights are source-supported.
4. Close GF unclosed plate areas 23.3 m² and 8.6 m² from the Route B faces, with a door-arc check.
5. Get the door/window schedule or elevation dimensions for the 27 openings that have no height.

## 8. Files
- **Registers** (22) and `INDEX.json` (hashes, gates A01–A12, built twice identical): `registers/`.
- **Runner:** `build_arch_r5.py`.
- **Post-freeze:** `post_freeze_arch_benchmark.py` → `POST_FREEZE_ARCH_BENCHMARK.json`.
- **Engine (new):**
  - `engine/source/planar_shadow_topology.py`
  - `engine/source/arch_quantity_truth.py`
- **Adapter:** `research/external_engine_lab/alsenan_arch_r5.py`.
- **Tests:** `tests/alsenan_arch_truth/test_arch_r5.py`:
  - 15 known-answer fixtures;
  - 16 mutations;
  - gates A01–A12;
  - firewall;
  - rebar-untouched check.
