# URBAN PROJECTS — GENERIC STRUCTURAL REBAR ENGINE — S3 COLUMNS

Alsenan / ST7757 is the validation project. Baseline: `c5455ac` (after S2).

This round covers **columns only**: no footings, beams or slabs. The workbook `review/ALSENAN_COLUMN_REBAR_REVIEW.xlsx` is the quantity authority. The PDF is a visual check. Both are gitignored, because the PDF embeds client drawings and `*.xlsx` is ignored repo-wide; `review/REVIEW_MANIFEST.json` records their sha256.

**Benchmark firewall.** No benchmark, freelancer or human total, and no kg/m³ allowance, was read. The outputs were built twice (byte-identical), hashed in `INDEX.json` and tested before any comparison. No comparison was made in this round.

---

## 1. Generic code (`engine/source/column_rebar.py`, policy `COLUMN_REBAR_V1`)

Every project value is an input. The firewall test bans project names and marks, and the literals 25 / 40 / 70 / 6 / 800 / 4.5.

| Function | What it does |
|---|---|
| `schedule_row` | One schedule row per (type, storey band). A missing row returns `NO_ROW`; it is never borrowed from a neighbouring storey. |
| `select_band` | Picks the tie topology band from L. A value on an uncovered limit is a `RULE_GAP`. Only an applying claim can resolve it: same project + revision + flag, the same L, and an adjacent band. |
| `bar_layout` | Corner bars are fixed by cover + tie + bar radius. Internal bars use equal spacing, which is a method, so it is marked as derived. |
| `map_link_ranges` / `link_geometry` | Each link gets its own path, `2 × (across + along)`, along the enclosed bar range. Ranges come from the detail; they are scaled (and flagged) when the schedule bar count ≠ the detail. |
| `tie_levels` | `RATE_COUNT` and `SPACING_WITH_ENDS` in exact rational arithmetic (1000/6 mm is never rounded). Supports multiple zones. |
| `links_from_levels` | `SETS_PER_M` vs `LINKS_PER_M`. Under SETS, 1L → 6, 2L → 12, 3L → 18 links/m. |
| `_main_parts` | Separate parts: CORE_VERTICAL_RUN (= storey interval, never cut at the soffit), LAP_SPLICE, ANCHORAGE (stopped bars / top / planted base), STARTER, OTHER_EXTRA. |
| `_tie_parts` | Separate parts: TIE_PERIMETER (lower bound of any closed-link set over the clear zone × RATE_COUNT), TIE_INTERNAL (Σ links − perimeter, provisional), HOOK_1, HOOK_2 (provisional method, never in a core). |
| `release_segment` | Combines S2 flags through the facts each part depends on. Under a type conflict: a part shared by every candidate → LOWER_BOUND; a differing part → PROVISIONAL at a single corroborated candidate (and a lower bound only if it is also the smallest value), else BLOCKED. |
| `component_states` / `occurrence_state` | One terminal state per component and per occurrence. A blocked part beside released ones makes the component (and the occurrence) a LOWER_BOUND. BLOCKED only when nothing is releasable. |
| `validate_segments` | One segment per occurrence, no duplicates, and continuity consistent with the chain (no lap without a segment above, none missing above). |
| `mass_conservation` | part → segment → floor → project, by release bucket. Also checks no duplicate part or segment and that main and tie parts are disjoint. |
| `tie_scenarios` / `alt_section_tie_kg` | Clear vs full zone × RATE vs SWE, and ties on the drawn section. |
| `method_flags` | Quantified `TIE_ZONE`, `END_LEVEL_COUNT`, `HOOK`, `LAP` and `TIE_TOPOLOGY_RULE_GAP` flags, built through `engineering_flags.make_flag`. An existing flag on the same fact with a different effect is SUPERSEDED, with its history kept. |

**Tests** in `tests/column_rebar_engine/test_column_rebar.py` (19).

Hand-derived known answers:
- 20×50 one link: path 1168 mm, 15 levels over a 2500 mm clear zone;
- 25×60 two overlapping links on bars 0–2 / 1–3: 1122.667 mm each, perimeter 1468;
- 30×80 three links by claim: 1680.8 / 1680.8 / 819.2 mm, 15 levels → 45 links;
- 25×100 three links: 1900.8 / 1900.8 / 799.2;
- rate → levels: 4.5 m → 27 / 28.

Mutations (each must be caught):
1. one link where two are required;
2. two where three are required;
3. 6/m read as single pieces;
4. column omitted on an upper floor;
5. column wrongly continued upward;
6. wrong schedule row;
7. main bars cut at the soffit;
8. ties verified while the zone is open;
9. hook hidden in the core;
10. duplicate segment;
11. claim leaking to another project or revision, or to another flag.

## 2. Project claims applied (PROJECT_ONLY, `ALSENAN_COLUMN_PROJECT_CLAIMS.json`)

| Claim | Kind | Effect |
|---|---|---|
| ALS-S3-CLAIM-001 "6Ø8/m = six complete tie sets per metre" | ADJUDICATION of STR-COL-002 | STR-COL-002 → RESOLVED, history kept. It applies to every column governed by the tie rule, because the flag is scoped to the rule: 1L 6, 2L 12, 3L 18 links/m. |
| ALS-S3-CLAIM-002 "L = 800 mm → 3-link set" | ADJUDICATION of STR-COL-008 | STR-COL-008 → RESOLVED. Applies to X07 C7 ×3 and to the C7 candidate at X12-Y02, because the gap flag is scoped by value. Generic code still returns RULE_GAP for any other project, revision or flag (tested). |

Project evidence (not engine logic):
- EV-001: all type counts accepted.
- EV-002: CN — 5 on the axis plan, 6 on the foundation plan. The census agrees: 6 CN, all at FOUNDATION, none continuing up.

The S2 claim store is untouched.

## 3. Results

### Coverage

| Item | Value |
|---|---|
| Occurrences | 95 in → 95 terminal records (all `REBAR_LOWER_BOUND`) |
| Main-bar coverage | 95 / 95: VERIFIED 56, LOWER_BOUND 38, PROVISIONAL 1 (X12-Y02 1F, likely C7) |
| Tie-topology coverage | 95 / 95: EXACT_RULE 89, RESOLVED_BY_CLAIM 6 |
| Links per level | 1L 63, 2L 13, 3L 19 |

### kg by floor

| Floor | Main core | Tie core | Hooks (prov.) | Lap / starter / anch. | Extras | Total |
|---|---|---|---|---|---|---|
| FOUNDATION | 974.83 | 309.32 | 32.44 | 886.43 | 0 | 2203.01 |
| GF | 2031.32 | 604.56 | 66.23 | 288.90 | 25.25 | 3016.26 |
| 1F | 1140.19 | 309.21 | 39.18 | 191.93 | 0 | 1680.51 |
| 2F | 397.74 | 100.28 | 12.67 | 68.69 | 0 | 579.38 |
| **Total** | **4544.08** | **1323.36** | **150.51** | **1435.94** | **25.25** | **7479.15** |

### Release buckets

| Floor | Verified | Lower bound | Provisional | Blocked |
|---|---|---|---|---|
| FOUNDATION | 0 | 1286.50 | 824.24 | 92.27 |
| GF | 1889.27 | 690.89 | 278.80 | 157.31 |
| 1F | 1073.90 | 409.00 | 197.61 | 0 |
| 2F | 397.74 | 120.49 | 52.53 | 8.62 |
| **Total** | **3360.91** | **2506.87** | **1353.18** | **258.20** |

Seven blocked parts carry no value: 5 starters (3 CN on unresolved footing records, 2 on the F/F10 footing) and 2 turned-column spirals.

### Sensitivity

**Clear vs full-storey tie zone** (RATE_COUNT, 92 segments where both zones are known):

| Zone | Levels | Links | Core kg | Hooks kg |
|---|---|---|---|---|
| Clear | 1623 | 2481 | 1288.49 | 146.84 |
| Full | 1975 | 3030 | 1573.77 | 179.34 |

Difference: **+285.28 kg** core. Three foundation segments have no established clear zone, because the exterior ground-beam depth "follows arch".

**RATE_COUNT vs SPACING_WITH_ENDS** (base zone): 1661 vs 1756 levels; 1323.36 vs 1400.63 kg (**+77.27 kg**).

### Laps and starters

| Component | Provisional | Lower bound | Blocked |
|---|---|---|---|
| LAP | 54 | 2 (shared parts at X12-Y02) | — |
| ANCHORAGE | 49 | 10 | — |
| STARTER | 29 | 2 (X04-Y01 / X12-Y02 shared) | 5 (no value) |

The lap / anchorage alternative at 70D instead of 40D is +640.99 kg.

### Open column flags: 24

S2 flags still open:
- STR-COL-001, STR-COL-003…006;
- STR-COL-009 (X04-Y01 C3 vs C);
- STR-COL-010 (X12-Y02 C8 vs C7, likely C7);
- STR-COL-011, STR-COL-012…023.

New S3 flags:
- STR-COL-024 END_LEVEL (+77.27 kg);
- STR-COL-025 HOOK (150.51 kg provisional);
- STR-COL-026 LAP (+640.99 kg at 70D);
- STR-COL-027 TIE_ZONE (+285.28 kg). It supersedes STR-COL-007.

Front summary, de-duplicated: **2742.31 kg** sit in parts touched by an open flag, each part counted once.

### Mass conservation

All checks are true: parts = segments = floors = project, buckets = total, no duplicate part or segment, main and tie parts disjoint. The workbook re-derives every bucket with SUMIFS: 1248 formulas, 0 errors, all checks OK.

## 4. Key interpretation choices (for review)

1. **Core run uses the FFL-to-FFL storey interval.** The foundation storey is a lower bound: GF FFL (+1.00) minus founding level (≤ −1.50) minus the footing depth. Where the footing is not bound, the deepest scheduled footing is used.
2. **Clear zone = interval − deepest framing beam at the closing plan.**
   - Unknown-depth members are bounded by the deepest scheduled beam (1200 mm), as BOUNDED.
   - A column with no framing beam takes the thickest slab on that sheet.
   - An exterior ground beam ("follow arch") blocks the clear zone.
3. **Ties released = perimeter × RATE_COUNT over the clear zone**, as a lower bound. Internal links are provisional, because bar positions use equal spacing. Where the schedule bar count ≠ the detail sketch (STR-COL-003/004), they are blocked.
4. **Laps: 40D compression value of p.8 note 9**, provisional, with 70D as the alternative. Top anchorage and planted-column anchorage use the same note, provisionally.
5. **Starters: p.13 typical detail.** Length = (footing depth − 70 soil cover) + 300 foot + 40Ø; provisional, CANDIDATE detail.
6. **Hooks: Urban provisional method, 135° hooks, max(6Ø, 75 mm) × 2 per link.** Not printed on ST7757, so they are never in a verified weight.
7. **Turned columns (p.15): 4Ø16 × 2 m, provisional.** The spiral is blocked because its geometry is not dimensioned. The planted-column 4Ø16 belongs to the supporting beam, so it is not counted here.

---

## What worked / what is not working / recommendation (for ChatGPT)

### Worked

- The generic engine has no project constants (firewall test). Every Alsenan value enters as data from the frozen registers.
- Hand-derived known answers and all 11 mutation classes pass. The adapter test caught a real scoping bug before freeze: rule-scoped claims did not reach the X07 C7 columns. It is fixed by treating rule-scoped and value-scoped flags as covering every governed element.
- Release is per part. Conflicts release shared parts as lower bounds; X12-Y02 shows likely C7 while STR-COL-010 stays open.
- 95 → 95, mass conservation holds, and the build is byte-identical twice.

### Not working / limits

- **Clear zone on an FFL basis.** The floor build-up is not printed; the beam depth is assumed to be measured from FFL.
- **Unbound framing members are bounded by a 1200 mm beam**, which is conservative. This makes some clear zones short.
- **Internal link edges depend on equal bar spacing**, which is not dimensioned on ST7757.
- **Laps and starters are provisional.** P8-N09 states starter development, not the column splice rule.
- **Three CN footings are not resolved in S1** ("RB-" refs), so their starters are blocked.
- **No crank / offset bar allowance** where the section steps 25 → 20 between storeys.
- **Type summary sheet.** It shows the released type (C7 at X12-Y02) for readability, not the census tag.

### Recommend next

1. Mohammad reviews 01_Occurrences, 03_Tie_Sets and 04_Link_Cutting_Lengths against p.9, plus the X04-Y01 and X12-Y02 rows.
2. Ask the consultant, highest kg impact first:
   - lap rule (STR-COL-026, 641 kg);
   - tie zone (STR-COL-027, 285 kg);
   - X12-Y02 type (STR-COL-010);
   - end level count (77 kg);
   - hooks;
   - which bars the overlapping links enclose when the schedule count ≠ the sketch (STR-COL-003/004).
3. Record the answers as ADJUDICATION claims and re-run. The engine re-releases automatically, with flag history kept.
4. Before the next trade, bind the three "RB-" CN footings and the exterior GB depth in S1+, if a source exists.
