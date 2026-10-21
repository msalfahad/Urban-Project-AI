# URBAN QTO — V3c FORENSIC ACCURACY + DONOR GAP AUDIT

**Status: RECOMMENDATION / INFORMATION ONLY. Nothing in this round changes any engine, register or quantity.**
No code was written or changed. The V3b freeze (`tests/alsenan/registers_v3b/FINAL_FREEZE_V3B.json`, code commit
17efc83, package commit 66dd3fb) is untouched. The freelancer workbook was read **after** that freeze, from the
already-frozen B1 registers (`tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json`, `BENCHMARK_NORMALISED.json`), for
evaluation only. No benchmark value is a target. kg/m³ is used only as a QA diagnostic and never to generate a quantity.
Pricing and cornice are ignored. Lift = ELEVATOR, but the 1.8 × 1.8 shaft is **not** assumed to be an elevator (OQ-1).
Qortuba RC1_REFERENCE was not touched.

**STOP. Do not implement until Mohammad / ChatGPT have reviewed these findings.**

---

## 0. Executive summary: what the forensic pass proved

Tests proved that V3b is **consistent**: registers are byte-identical when rebuilt twice, QA passes and the mutations are
caught. They did not prove it is **correct**. Checking every population against the drawing found **six proven Urban
engine defects** (D1–D6). None of them was caught by a test, because no test asks "does every drawn or scheduled
population carry rebar?".

| # | Proven defect | Evidence | Effect on rebar (net) |
|---|---|---|---|
| D1 | **Continuous beams CB1–CB13 carry no rebar.** The "SCHEDULE OF CONTINUES BEAMS (2 SPAN / THREE SPAN)" on ST7757 p.11–12 was transcribed for B / H / spans only (`alsenan_phase_a3.py: CB_TRANSCRIPTION`). The bars (top per span, support top bars at 0.22 Ln, bottom per span, stirrups per span, middle 2Ø12/30) were never read. `beam_rebar()` skips any type without a definition and writes **no BLOCKED row**. | p.11–12 images; DXF texts `SCHEDULE OF CONTINUES BEAMS` ×3, `CB1..CB13`; `alsenan_v3_structure.py:319-347` | **missing ≈ 2.2 t** straight (diagnostic hand pass over 11 placed types, see §A.4) |
| D2 | **Footing bars given per metre are used as absolute counts.** F8 / F12 / F13 / F14 are `6/10/7/6 Ø14/m`; `footing_rebar()` uses `count=b["count"]` and ignores `per_m`. | `alsenan_v3_structure.py:285`; definitions `per_m: true` | **missing ≈ 0.60 t** (245.6 kg measured vs 848.3 kg per-metre) |
| D3 | **FF footing (4.6 × 4.5 × 0.55, the largest footing) has concrete but zero rebar.** Its schedule cell is a merged two-row read (`"6 9 Ø Ø 14/m 14/m"`), so the definition has `bars: {}`. `footing_rebar()` then emits nothing and **no BLOCKED row**. | `a3.rebar.definitions` FF = BLOCKED; FF concrete 11.385 m³ is in C-FTG | **missing ≈ 0.29–0.72 t** (one or two layers, OQ-3) |
| D4 | **Strap beams SB1–SB3 have no rebar population.** The SB schedule rows (SB1 bottom 7Ø16, top 13Ø18, 8Ø8/m …) and the strap geometry (4.551 / 2.294 / 3.259 m, measured) both exist. No function builds the sets. | `a3.straps.library` / `a3.straps.rows`; no strap function in V3a / V3b | **missing ≈ 0.42 t** straight (≈ 0.65 t with anchorage) |
| D5 | **17 columns get rebar although B2A says they are not on that storey.** `column_rebar()` filters only on `B_cm is None` and ignores `state`. That emits bars for 4 (1F) + 13 (2F) columns in `NOT_DRAWN_ON_STOREY_SHEET`, which the concrete and reporting paths exclude. | `alsenan_v3_structure.py:298-302` vs `alsenan_phase_b2a.py:390/415` | **over-count ≈ 1.04 t** (216.7 + 824.7 kg) |
| D6 | **The ground slab is bound to the smallest closed cell around each label.** `ground()` uses `outer = min(hit, key=area)`, so the two typical labels "5Ø10/m E.W. T=10cm" cover 103.4 m² + 60.6 m² outer (115.4 m² net). The GF floor finishes cover ≈ 254 m² and there is **no suspended GF floor slab** (the "GF slab" is GF_ROOF_SLAB = 1F floor). Floor finish with no structural floor under it is a physical contradiction. | `alsenan_v3_structure.py:98-113`; `structural_sheets`; ST7757 p.3 | concrete **−10.9 to −18.0 m³**, rebar **−0.67 to −1.1 t** (scope to confirm, OQ-2) |

There are also seven **source-supported gaps that were wrongly or too conservatively blocked** (G1–G7), set out in
§A.3, and four **evaluation-map errors** that hid the true comparisons (E1–E4, §B).

**Rebar headline (diagnostic only, not a quantity):** correcting D1–D6 plus G1 / G2 / G3 / G6 moves Urban net rebar
from 26.24 t to roughly **30–32 t** (≈ 34 t if the stairs, elevator walls and pool are confirmed and measured). The remaining gap to the freelancer's 44.19 t is **proven** to come from the
freelancer's method. Their rebar column is not measured: every one of the seven category tonnages equals
**concrete × a round kg/m³ allowance** (75 / 130 / 200 / 150 / 90 / 180 / 120). Urban must not tune to it.

---

## A. Rebar population forensic audit

### A.1 Population matrix (V3b frozen register, every population)

Source: `REBAR_POPULATION_REGISTER.json` (998 sets) and V3a ctx. "Net" means straight length plus hooks; laps are
separate. Lengths are bar metres (count × bar length).

| Population | Source drawing / table | Members | Bar roles present | Ø (bar metres) | Count / spacing rule | Net kg | Tech kg | Status | Completeness verdict |
|---|---|---|---|---|---|---|---|---|---|
| FOOTINGS | p.9 SCHEDULE OF FOOTINGS + p.13 typical isolated footing | 24 (27 tags; F/F10 separate; FF missing) | long + short bottom bars (both directions ✓); boxed bars BLOCKED ×4 | 12: 670.9 · 14: 443.5 | count from schedule; **per-metre ignored (D2)** | 1132.7 | 1132.7 | DERIVED + 4 BLOCKED | **INCOMPLETE**: D2, D3, boxed bars (G1). No top mesh is scheduled (OK by source) |
| FOOTING_F_F10 | F / F10 conflict | 1 | long 10Ø14 + short 20Ø14 | 14: 51.8 | schedule | 62.7 | 0 | PROVISIONAL_SOURCE_RANGE | as V3b (owner conflict) |
| **STRAP BEAMS SB1/SB2/SB3** | p.10 Schedule of Simple Beams (SB rows) + foundation plan bands | 3 measured | **none** | — | — | **0** | **0** | **MISSING POPULATION (D4)** | **DEFECT** |
| COLUMN NECKS / STARTERS | column schedule "FOUNDATION" row | 1 aggregate line | weight only | n/a | **median 8 bars × 25 footings** (not per occurrence) | 938.7 | 0 | PROVISIONAL_URBAN_FALLBACK | **aggregate, not occurrence-based**. C7–C11 carry 12–14 bars in FOUNDATION, so the median under-counts them |
| COLUMNS GF / 1F / 2F | column schedule + storey sheets | 30 / 22 / 22 instances | vertical + ties ✓ for every instance | 8: 3149 · 16: 2681.4 | ties `ceil(6 × storey interval)` from "6Ø8/m" ✓; 40Ø compression lap per floor ✓ | 5481.4 | 5329.9 | DERIVED (ties PARTIAL) | **OVER-COUNT (D5)**: 17 instances not on the storey; 9 instances whose concrete is BLOCKED still carry DERIVED bars (751 kg) |
| BEAMS (simple B1–B29, CA) | p.10 Schedule of Simple Beams | 68 occurrences (34 GF / 20 1F / 14 2F) | top + bottom + stirrups ✓ for every member | 8: 2056.5 · 10: 324.4 · 12: 376.2 · 14: 270.6 · 16: 466.4 · 18: 1074.0 | top/bottom on support-centre length; stirrups `ceil(rate/m × clear length)` ✓ | 4561.6 | 4115.9 | PROVISIONAL_CODE_METHOD (hooks) | **INCOMPLETE**: side bars mis-sourced (G2); multi-leg links (box symbol) missing (G3) |
| BEAM_SIDE_BARS | p.8 note 21 (2/3/4 Ø12 by width) | 24 beams (D > 60) | side | 12: 307.1 | "3 (mid), range 2..4" | 272.9 | 0 | PROVISIONAL_SOURCE_RANGE | **mis-sourced (G2)**: schedule REMARKS state the bars per type (2Ø12/30 cm, 2Ø16/20 cm for B16 / B26 / B27, 2Ø14/20 cm for B19). Note 21 applies only "unless otherwise stated" |
| BEAM_RESIDUE | weight per m of measured same type × residue length | 10 | weight only | n/a | budget | 319.1 | 0 | BUDGET_ESTIMATE (outside total) | no double count with BEAMS (handles disjoint ✓) |
| **CONTINUOUS BEAMS CB1–CB13** | p.11–12 SCHEDULE OF CONTINUES BEAMS | 11 placed types (GF 7, 1F 4) | **none** | — | — | **0** | **0** | **MISSING POPULATION (D1)** | **DEFECT**: largest single gap |
| GROUND (interior GB + ZONE-1 slab) | p.3 ground-beam plan + p.13 typical GB sections | 31 spans + zone 1 | top + bottom (2 layers per detail ✓) + stirrups ✓; slab mesh X + Y ✓ | 8: 658.6 · 10: 704.0 · 14: 681.0 · 16: 222.0 | stirrups `floor(L/0.15)+1` ✓; section by length band ✓ | 1870.5 | 1687.5 | DERIVED / PROVISIONAL_CODE_METHOD | complete for what is bound. The two bottom rows are the 3 + 3 layers of the detail, **not a double count** |
| GROUND_BEAM_EXT | p.13 "for exterior walls" | 28 spans | top 3Ø16 + bottom 6Ø16 + side 2Ø12/30 + Ø8/15 links ✓ | 8: 1672.7 · 12: 441.2 · 16: 1101.4 | ✓ | 2793.7 | 0 | PROVISIONAL_SOURCE_DERIVED (depth) | complete by detail; depth provisional |
| GROUND_SLAB (zone 2) | p.3 label | 1 | mesh X + Y ✓ | 10: 463.4 | 5/m both ways ✓ | 286.1 | 286.1 | DERIVED | **scope defect (D6)** |
| SLAB (GF / 1F / 2F roof slabs) | slab plans, 123 annotations | 27 panel families | bottom / top / support / extra per **annotation** | 10: 5086.1 · 12: 166 · 14: 232.7 · 16: 864.3 · 18: 29 | per-metre: `floor(width/spacing)+1` ✓; count bars ✓ | 4992.8 | 4876.9 | DERIVED (+12 PARTIAL open supports, 2 DRAWN_EXTENT) | 121 annotations bound, 2 de-duplicated (OQ-9). **No per-panel completeness check** (G4) |
| LINTELS | p.13 LINTEL SCHEDULE by opening width | 59 openings | top + bottom + stirrups ✓ | 8 / 10 / 12 / 14 / 16 / 18 | 5Ø8/m ✓ | 626.9 | 582.5 | DERIVED | complete for admitted openings |
| STAIRS | p.16 typical section | 0 | — | — | — | 0 | 0 | BLOCKED | **review (G5)**: blocked because no callout is bound. Freelancer measures 3 stairs + entrance steps (§B.2) |
| POOL | pool detail | 4 elements | wall vertical inner/outer + horizontal + base top/bottom both ways ✓ | 12: 247.9 · 14: 302 | per-metre ✓ | 585.7 | 585.7 | DERIVED | geometry disputed (§B.2); pump room absent (OQ-6) |
| DOME | pool / dome detail | 3 domes × 6 roles | meridional, hoops, links, top / bottom / side rings ✓ | 8 / 12 / 14 / 16 / 18 | ✓ | 2079.1 | 2054.2 | DERIVED / PROVISIONAL_CODE_METHOD | complete |
| BOUNDARY WALL | B.W schedule row 20 × 60 + S-BOUN outline | 1 run | bottom 4Ø16 + top 2Ø14 + links 7Ø8/m ✓ | 8 / 14 / 16 | 44.07 m, 3 laps per bar ✓ | 555.7 | 0 | PROVISIONAL_SOURCE_DERIVED | complete |
| OTHER: elevator walls | freelancer row "elevator walls 20 cm" 8.0 × 0.2 × 1.5 m; ST7757 p.8 note 19 mentions the elevator | — | — | — | — | 0 | 0 | not modelled (owner) | **owner-gated (OQ-1)** |

**Answers to the structural completeness questions (§1):**

* **Every column has longitudinals and ties?** Yes. All 74 instances carry both. But 17 of them should not exist (D5).
* **Every beam has top, bottom and stirrups?** Yes for all 68 simple-beam occurrences. **No** for the 11 continuous
  beams (D1) and for straps (D4).
* **Every footing has both directions?** Yes for the 24 bound footings (long + short), but the per-metre count is wrong
  for 4 of them (D2). FF has no bars (D3). Boxed bars are blocked for 4 footings (G1).
* **Every slab panel has bottom / top / support / corner bars?** **Not verified.** The engine binds each *annotation*
  once and never checks that each *panel* received a bottom bar in both directions plus its support top bars.
  Corner and extra bars appear only where a label exists. This is gap G4, an audit to build, not a proven loss.
* **Every GB has longitudinals and stirrups?** Yes, interior and exterior.
* **Starters: occurrence-based or aggregate?** **Aggregate.** `necks()` uses the median section × median FOUNDATION
  bar count (8) × 25 footings. That is a single PROVISIONAL_URBAN_FALLBACK line.

### A.2 Per-diameter sanity table (Urban net, V3b)

Theoretical kg/m = D²/162. Urban uses exactly this value (no rounded table).

| Ø mm | Bar length m | Urban kg/m | Theoretical D²/162 | Net kg | Share % |
|---|---|---|---|---|---|
| 8 | 9 044.7 | 0.3951 | 0.3951 | 3 573.2 | 13.45 |
| 10 | 6 723.5 | 0.6173 | 0.6173 | 4 150.3 | 15.63 |
| 12 | 3 781.0 | 0.8889 | 0.8889 | 3 360.9 | 12.65 |
| 14 | 2 314.9 | 1.2099 | 1.2099 | 2 800.8 | 10.55 |
| 16 | 5 641.1 | 1.5802 | 1.5802 | 8 914.3 | 33.56 |
| 18 | 1 251.1 | 2.0000 | 2.0000 | 2 502.1 | 9.42 |
| 20 | 0 | — | 2.4691 | 0 | 0.00 |
| weight-only lines | — | — | — | 1 257.8 (starters 938.7 + residue 319.1) | 4.74 |
| **Total** | | | | **26 559.5** | 100 |

The **Ø18 share of 9.4% is a red flag on its own.** The simple-beam schedule, the continuous beams (D1) and the straps
(D4) are Ø18-heavy. Ø20 = 0 is consistent with no B27 (22Ø20) occurrence in the BEAMS population (to confirm on the plans). The kg/m values are exact. No hard
5% waste is used anywhere: waste stays PENDING, and the only computed waste is the BBS cutting result.

### A.3 Diagnostic kg steel / m³ concrete by population (QA only, never used to generate)

| Population | Urban net kg | Concrete m³ (Urban) | kg/m³ | Typical band (QA heuristic) | Flag |
|---|---|---|---|---|---|
| Footings (+F/F10) | 1 195.4 | 66.31 | **18.0** | 40–90 | **RED** → D2, D3, G1 |
| Straps | 0 | 3.39 | **0** | 100–250 | **RED** → D4 |
| Columns (incl. joints) | 5 481.4 | 26.35 | 208 | 150–250 | over-count D5 hidden inside a "normal" ratio |
| Starters / necks | 938.7 | 6.25 | 150 | 100–200 | aggregate |
| Simple beams (downstand) + side bars | 4 834.5 | 37.59 | 129 | 100–180 | diluted: 6 CB occurrences have concrete but 0 rebar |
| Slabs | 4 992.8 | 81.43 | 61 | 50–100 | ok |
| Interior GB + zone 1 | 1 870.5 | 18.29 | 102 | 80–150 | ok |
| Exterior GB | 2 793.7 | 33.09 | 84 | 80–150 | ok |
| Ground slab zone 2 | 286.1 | 4.50 | 64 | 50–70 (single mesh) | ok |
| Lintels | 626.9 | 4.75 | 132 | 80–150 | ok |
| Pool | 585.7 | 5.05 | 116 | 80–150 | ok |
| Domes | 2 079.1 | 13.49 | 154 | 80–160 | ok |
| Boundary wall beam | 555.7 | 5.29 | 105 | 80–150 | ok |
| Stairs | 0 | 5.23 | **0** | 80–140 | **RED** → G5 |
| **Whole building** | 26 559 | 316.06 | **84** | — | freelancer allowance basis = 125.4 |

The diagnostic would have flagged D2 / D3 / D4 / G5 automatically. It could **not** have flagged D1 (diluted) or D5
(inside a normal band). That is why the population-completeness invariant (§D, L-16) is needed, not more ratios.

### A.3b Source-supported gaps that were blocked or simplified (not defects in the strict sense)

| # | Gap | Source evidence | Current engine | Better rule |
|---|---|---|---|---|
| G1 | Boxed bars, 4 footings (F8 / F12 / F13 / F14) + FF | p.13 both typical isolated-footing details draw "Boxed bars" as closed cages; schedule carries a boxed flag | BLOCKED "not dimensioned" | shape is fixed by L × W × D and the 7 cm soil cover → PROVISIONAL_SOURCE_DERIVED with a shape code; count from the schedule cell |
| G2 | Beam side bars | p.10 REMARKS: per type "2Ø12/30cm", "2Ø16/20cm" (B16, B26, B27), "2Ø14/20cm" (B19) | note-21 range 2..4 Ø12, mid 3 | rows per face = floor((D − 2c − top/bottom zones) / spacing); diameter from REMARKS; note 21 only where REMARKS are blank |
| G3 | Multi-leg (inner) links | p.10 box-icon symbol beside B17, B19–B26, SB1–SB3 (wide beams with 10–19 bottom bars) | one closed perimeter link | read the symbol as "additional inner link set". OWNER / ENGINEER confirm (OQ-7) before it enters a total |
| G4 | Slab per-panel completeness | slab plans | per-annotation binding only | per panel: assert bottom X + bottom Y + support tops on every supported edge, else PANEL_REINFORCEMENT_INCOMPLETE |
| G5 | Stairs | p.16 typical section (going only); freelancer allowance 180 kg/m³ | BLOCKED | keep BLOCKED unless a callout exists; add an owner question (OQ-5). Never a ratio |
| G6 | Starters per occurrence | FOUNDATION row per column type (8–14 Ø16) | median × 25 | per footing: the column type above it × its FOUNDATION bars × (neck + embedment + lap) |
| G7 | FF two-layer read | merged cell "6 9 Ø Ø 14/m 14/m" | definition BLOCKED → **silent** zero | split two stacked rows by y-order → "6Ø14/m" + "9Ø14/m" (layer roles to confirm, OQ-3); emit BLOCKED until confirmed, **never silent** |

### A.4 Strap-beam and continuous-beam evidence (scale only, not quantities)

**Straps:** Urban's own measured strap lengths match the freelancer to ±0.2% (SB1 4.551 m vs STB1 4.55; SB2 2.294 vs
2.3; SB3 3.259 vs 3.25), and strap concrete matches exactly (3.392 vs 3.3925 m³). A straight-only hand pass from the SB
schedule rows (top + bottom + links at 7 cm cover) gives SB1 ≈ 195 kg, SB2 ≈ 150 kg and SB3 ≈ 70 kg: **≈ 0.42 t before
anchorage into the footings**. The strap rebar absence is therefore a **real missing-population defect**, not a scope
difference.

**Continuous beams:** a diagnostic hand transcription of p.11–12 was made using only these rules: span bars over each
span; support top bars at 0.22 Ln each side + 0.30 m; bottom bars span + 0.30 m; links `ceil(rate × span)` at 2.5 cm
cover; middle reinforcement 2Ø12 full length. It gives **≈ 2.20 t** straight over the 11 placed types:

| CB1 | CB3 | CB4 | CB5 | CB6 | CB7 | CB8 | CB9 | CB11 | CB12 | CB13 |
|---|---|---|---|---|---|---|---|---|---|---|
| 339 | 132 | 80 | 84 | 175 | 190 | 361 | 149 | 321 | 234 | 132 kg |

This is **not** a quantity. The production reader must transcribe every cell with a confidence and resolve support
widths from the plan. It must also put hooks and laps through `bbs_optimiser`.

---

## B. Freelancer-vs-Urban mismatch table (every item, every difference > 5% proved or disproved)

Legend: **PROVEN** = a decomposition reproduces the difference from both sides' rows. **PROBABLE** = mechanism
identified, magnitude not fully closed. **UNRESOLVED** = needs source or owner. "Urban" = V3b commercial unless stated.

### B.1 Dashboard

| Item | Freelancer | Urban | Diff | WHY (verdict) |
|---|---|---|---|---|
| Flooring | 409.58 m² | 447.224 m² | +9.2% | **PROVEN mechanism / PROBABLE magnitude.** Freelancer = 12 named dry rooms 337.57 + 17 wet rows 72.01; there are no corridors, landings or circulation in the list. Urban dry 389.0 / wet 58.2. Circulation: 1F-Z06 63.7 vs "living" 38.96 (+24.7); 2F-R01 18.6 vs corridor 7.7 (+10.9); GF-R12 14.6 vs driver 7.87 (+6.8). GF-Z04 is named "PANTRY / SALOON / RECEPTION / Wash / DINING / GARDEN": 155.7 vs 147.96 (+7.7). **GARDEN inside a floor zone is an over-closure red flag (L-17).** |
| Skirting | 282.85 lm | 312.30 lm | +10.4% | **PROVEN (consistent with floor scope).** Freelancer skirting = Σ gross room perimeters (sheet البيان col A45 = 282.85, no door deduction). Urban skirting / dry floor = 0.80 lm/m² vs freelancer 0.84. The delta follows the extra circulation area (+15.2% dry area, +10.4% skirting). Check whether 1F-Z06's 80.8 lm runs along the gallery void edge (no wall, L-18). |
| Wall tile | 433.83 m² | 369.123 m² | −14.9% | **PROBABLE: MISSING POPULATION (Urban engine).** Wet spaces merged into dry zones carry no tile in Urban: diwaniya washroom (freelancer 6.43 m² floor) inside GF-Z06; "Wash" inside GF-Z04; on 1F the freelancer has 5 bathrooms + laundry against Urban's 3 baths + laundry + one UNKNOWN 2.97 m² room. 3–4 missing wet rooms × ≈ 25 m² ≈ the 64.7 m² gap. Second-order: Urban nets openings + reveals. |
| Wet-room WP | 72.01 m² | 58.237 m² | −19.1% | **PROVEN (same rows).** Freelancer WP = exactly their 17 wet floor rows. Gap 13.8 m² = the diwaniya washroom 6.43 + Z04 wash + the missing 1F baths, all of which are Urban wet-identity failures. Not a convention. |
| Roof WP | 285.00 m² | 364.031 m² | +27.7% | **PROVEN like-for-like: +13.1%.** Urban 364.0 = flat 322.42 + upturn 41.61 (0.20 m × 208 lm). The freelancer books the upturn separately as 194 lm. Flat vs flat: 322.42 vs 285 = +13.1%; upturn length 208 vs 194 lm = +7.2%. The +13.1% residual is **PROBABLE**: 3 dome plan footprints ≈ 3 × 15.3 = 46 m², and 322.4 − 46 = 276.4 ≈ 285 (−3%). Loophole L-2 confirmed (wet-room WP split, roof WP not). |
| Railing | 18.95 lm | 14.29 lm | −24.6% | **PROVEN EVALUATION-MAP ERROR (E1).** The MAP compares the freelancer's "internal railing" with the Urban *gallery* railing. Urban's stair handrail S-RAIL = 19.124 lm vs 18.95 (+0.9%). The gallery railing 14.29 lm has no freelancer counterpart (freelancer omission or included elsewhere, UNRESOLVED). |
| Blockwork | 1 260.69 m² | 801.075 m² | −36.5% | **Mostly URBAN UNDER-MEASUREMENT (PROBABLE), plus conventions.** (a) Parapet: freelancer 66 m × 1.0 + 42.85 m × 1.8 = 143.1 m² vs Urban 151.5 m × 0.50 = 75.8 m². Lengths agree to within reason; **HEIGHT basis** differs (OQ-8). (b) Fence: freelancer 37.2 × 2.0 = 74.4 is inside their total; Urban B-BWALL 156.5 is **excluded by the MAP (E2)**. (c) Building walls: freelancer gross wall **length 359.6 m** (through columns and openings; openings deducted as area) vs Urban measured pieces **167.3 m** (+9.8 m blocked). Even adding back opening widths (≈ 52 m) Urban is ≈ 140 m short. **This is the largest unexplained architectural gap.** The probable cause is wall runs not classified as blockwork (UNR / unbound bands, partitions without a material claim). Height basis: freelancer GF 4.0 / 3.5, 1F 3.7, roof 3.45 vs Urban "interval − member depth". (d) Freelancer 200 mm rows on 1F and ROOF are identical (13.32 / 4.44 / 2.59 / 9.99), a possible **copied row (BENCHMARK ERROR candidate, 30.34 m²)**. |
| Paint | 1 191.13 m² | 1 199.23 m² | +0.7% | **AGREEMENT NOT PROOF.** Freelancer paint height 3.6 (GF) / 3.4–3.5 (1F/roof) over their room list; Urban paint height 3.5 over more rooms (circulation) with net openings. The components move in opposite directions (Urban more area, lower height, more deductions) and largely cancel. Treat as unverified. |
| Plaster | 1 151.14 m² | 1 367.565 m² | +18.8% | **PROVEN: HEIGHT basis.** Freelancer plaster height = paint height (GF 3.6, 1F 3.4–3.5, roof 3.4; stairwell 12.9 m) = plaster to the false-ceiling line. Urban = rough plaster to the structural soffit (GF 4.34). 4.34 / 3.6 = 1.206 matches the +18.8% almost exactly. An owner method question (OQ-10), not an error on either side. |
| Blinding | 47.055 m³ | 29.623 m³ | −37.0% | **PROVEN: SCOPE (owner decision OD-V3B-1).** Freelancer = full plot rectangle 15.0 × 31.37 × 0.10 (includes the courts). Urban = founded footprint 288.276 m² × 0.10 + pool 0.80. 470.6 − 288.3 = 182.3 m² × 0.1 = 18.2 m³ = the whole gap. |
| RC concrete | 352.436 m³ | 316.058 m³ | −10.3% | **PROVEN to 0.01 m³ (§B.2).** |
| Rebar (net) | 44.190 t | 26.240 t | −40.6% | **PROVEN: METHOD + Urban defects (§B.3).** |
| Rebar (purchased) | 44.190 t | 27.537 t | −37.7% | same; purchased is cutting-optimised (5.46%), not a ratio |

### B.2 RC concrete reconciliation (freelancer category → Urban)

| Population | Freelancer m³ | Freelancer method | Urban m³ | Urban method | Diff | Cause (verdict) |
|---|---|---|---|---|---|---|
| Footings (pure) | 65.634 | type L × W × D × count | 66.306 | 25 tags + F/F10 1.96 | +0.67 | **PROVEN**: identical per type, except F3 with 2 tags in Urban vs 1 in the freelancer (OQ-11) |
| Straps STB1–3 | 3.3925 | B × D × L | 3.392 | measured bands | 0.00 | **PROVEN match** |
| Perimeter strap 0.2 × 0.6 × 71.7 | 8.604 | inside "footings" total | 0 | — | −8.60 | **UNRESOLVED**: no drawn 20 × 60 edge beam found; candidate double count with the exterior GB on the same lines (Urban ext GB 110.3 m) **or** an Urban miss (OQ-12) |
| Ground slab | 29.55 | 295.5 m² × 0.10 | 11.54 | 2 zones (115.4 m²) | −18.01 | **Urban SCOPE DEFECT (D6)**, magnitude depends on OQ-2 (net of beams ≈ −10.9) |
| Ground beams (building) | 37.98 | 211 m × 0.3 × 0.6 | 44.33 | int 88.5 m by length band + ext 110.3 m × 0.3 × 1.0 | +6.35 | **PROVEN method**: Urban uses the p.13 section bands and the 1.0 m exterior depth (provisional); the freelancer uses a single 0.3 × 0.6 |
| Fence GB | 7.56 | 42 m × 0.3 × 0.6 | 5.29 | B.W 20 × 60, 44.07 m | −2.27 | **PROVEN section**: schedule B.W = 20 × 60, freelancer 30 × 60 |
| Elevator walls 20 cm | 2.40 | 8.0 × 0.2 × 1.5 | 0 | not assumed | −2.40 | **OWNER-GATED (OQ-1)** |
| Necks | 8.805 | 13 types × 1.5 m | 6.25 | median fallback | −2.56 | **PROBABLE**: neck height basis (1.5 vs Urban −1.50 founding → +0.90) and median vs per-type section |
| Columns GF / 1F / 2F | 28.547 | h 3.75 / 3.45 / 3.45 | 31.405 | storey interval incl. joints + residue | +2.86 | **PROVEN method**: Urban includes beam-depth joints (3.21) |
| Beams + slabs + lintels | 125.783 | beams full-depth B × D × L; slabs 207 / 120 / 31.84 / 13.35 m² | 123.768 | downstand B × (D − t) + net plate + lintels | −2.02 (−1.6%) | **PROVEN convention**: the split differs (freelancer beams 65.97 / slabs 59.82 vs Urban 37.59 / 81.43) but the **sum agrees to 1.6%**. Budget residue 7.95 sits outside the Urban total |
| Stairs | 15.053 | 4 rows, 55.2 m² × 0.28 / 0.2 | 5.231 | 2 flights provisional | −9.82 | **PROBABLE MISSING POPULATION**: freelancer has an entrance stair 1.8 × 2.8 and "stair 2" 1.2 × 16.4 m besides the main stair; Urban models one stair. Check the arch plans (OQ-5) |
| Domes | 6.78 | 3 × 22.6 m² × 0.10 shells | 13.49 | shells 7.52 + ring beams 5.97 (D 0.75 provisional) | +6.71 | **PROVEN**: rings are not in the freelancer stair+dome sheet; shell vs shell +11% (2πRh vs 22.6 m²) |
| Pool | 12.348 | floor 10.8 m² × 0.4, walls 12 × 1.8 × 0.2, pump room 3.48, steps 0.23 | 5.053 | inner 3.10 × 1.55, depth 1.15 | −7.30 | **UNRESOLVED**: geometry (perimeter 12 vs 10.1, wall height 1.8 vs 1.15) and pump room missing in Urban (OQ-6) |
| **Total** | **352.436** | | **316.058** | | **−36.38** | sum of the rows = −36.39 ✓ |

### B.3 Rebar total reconciliation (freelancer 44.19 t)

The freelancer rebar column H (RC file, sheet ورقة1 rows 17–25) holds **typed constants**. Each equals the category
concrete × a round allowance:

| Freelancer category | Concrete m³ | Freelancer t | kg/m³ (method) | Urban t (V3b net) | Urban method | Diff t | Cause |
|---|---|---|---|---|---|---|---|
| Footings (+ straps + perimeter strap) | 77.6305 | 5.80 | **74.7 ≈ 75** | 1.195 | bars from schedule | −4.61 | Urban defects D2 (+0.60), D3 (+0.29–0.72), D4 (+0.42–0.65), G1 (boxed); then the allowance itself (isolated footings with a bottom-only mesh do not reach 75 kg/m³) |
| Strap + GB + ground slab | 75.09 | 9.75 | **129.8 ≈ 130** | 5.506 | bar sets by detail | −4.24 | D6 (+0.67–1.1); **allowance applied to a 10 cm slab-on-grade** (29.55 m³ × 130 = 3.84 t vs a single 5Ø10/m E.W. mesh ≈ 295.5 × 6.17 = 1.82 t) |
| Walls + columns | 39.7515 | 7.95 | **200.0** | 6.420 | schedule bars + ties + starters | −1.53 | elevator walls (owner); D5 is an **over-count** in Urban (−1.04); per-occurrence starters G6 (+0.1–0.3) |
| Beams | 65.966 | 9.89 | **149.9 ≈ 150** | 5.154 | simple schedule + side + residue | −4.74 | **D1 continuous beams (+≈ 2.2)**, G2 / G3 side bars and inner links (+0.3–1.0); allowance on full-depth volume |
| Slabs | 59.817 | 5.40 | **90.3 ≈ 90** | 4.993 | 121 bound annotations | −0.41 | within method noise; G4 audit pending |
| Stair + dome | 21.833 | 3.90 | **178.6 ≈ 180** | 2.079 | dome detail; stairs BLOCKED | −1.82 | G5 stairs blocked; freelancer stair volume includes extra stairs |
| Pool | 12.348 | 1.50 | **121.5 ≈ 120** | 0.586 | pool detail | −0.91 | pool geometry + pump room (OQ-6) |
| Lintels | (in beams) | — | — | 0.627 | lintel schedule | +0.63 | Urban measures them separately |
| **Total** | 352.436 | **44.19** | 125.4 | **26.56** (26.24 excl. budget) | | **−17.63** | |

**Diagnostic correction scale (not a quantity):** D1 +2.2 · D2 +0.60 · D3 +0.29–0.72 · D4 +0.42–0.65 · D6 +0.67–1.1 ·
G1 +0.2–0.5 · G2 / G3 +0.3–1.0 · G6 +0.1–0.3 · D5 −1.04 → **net +3.7 to +6.0 t → Urban ≈ 30–32.3 t** (≈ 34 t if the
stairs, elevator walls and pool are confirmed and measured). The remaining **≈ 10–14 t is the freelancer's allowance
basis**. It is proven by the round ratios and by the 10 cm slab carrying 130 kg/m³. It is not a measurement Urban
should reproduce.

---

## C. Donor mechanism comparison (current versions, licences checked)

All nine repositories were shallow-cloned through the proxy on 2026-10-04 (network available). Licences were read from
each repository's LICENSE / package metadata. **No code was copied in this round.**

| Repo | Head commit (date) | vs DONORS.lock | Licence | Copy policy |
|---|---|---|---|---|
| U-C4N/Autocad-MCP | cdb1063 (2026-09-25) | **same** as lock | MIT | COPY_ADAPT allowed with notice; prefer clean reimplementation |
| beiming183-cloud/AutoCAD-MCP | 11f7c47 (2026-07-19) | **same** | MIT | as above |
| Kentucky-ai/OpenTakeoff | beaa4fe (2026-10-03) | **34 commits newer** than e6d2251 | Apache-2.0 | clean reimplementation (Python); NOTICE if any text is reused |
| v-Zak/bar-bending-scheduler | d949054 (2023-09-14) | not locked | **NONE** (all rights reserved) | **idea only, no copy** |
| thuanlm-eng/steel-bar-takeoff | d8f3cb6 (2026-06-22) | not locked | **NONE** | **idea only** |
| divyanshu964/Rebar-Pdf-Extractor | 4721802 (2026-05-18) | not locked | **NONE** | **idea only** |
| xu323/Rebar-Material-Schedule-OCR-Pipeline | a045fa5 (2026-04-16) | not locked | **NONE** | **idea only** |
| ContractorKeith/conmcp | 0a08f63 (2026-08-26) | not locked | MIT | COPY_ADAPT allowed with notice |
| hamzaabduljabbar/autoConst-drawing-takeoff-claude | 3f0c8be (2026-08-02) | not locked | **AutoConst Source-Available (no resale / no redistribution as a product)** | **idea only**: Urban is a product, so no code or schema text |

### C.A U-C4N/Autocad-MCP (unchanged since the lock)

* **arch_rooms_detect / rooms.py:** planar faces of LINE / LWPOLYLINE on wall layers; confidence 1.0 when every edge is on
  its own wall layer, 0.6 when foreign. The `skipped` list carries the handle of every arc, old POLYLINE and block-nested
  wall (never approximated). **Door gaps are closed only from its own opening records** (face lines continued in
  memory). On a foreign plan such as Alsenan, "the gaps stay open". It therefore cannot close Alsenan rooms.
* **faces.py:** a hand-rolled planar kernel (already REJECTED in DONORS.lock).
* **arch_dimension_chains / dimension.py:** **generates** ISO 129-1 exterior chains from its own wall model. It does
  not **read** a foreign plan's dimensions. Useful only as a pattern for a "printed vs geometric" cross-check row
  ordering.
* **arch_schedule:** renders door / window / room schedules *from its own records* ("a value the model does not carry is
  an empty cell, never a default"). Not a reader.
* **drawing_understand / drawing_topology_check / drawing_diff:** topology classifies each end as joined / attached /
  near-miss / dangling, plus interior crossings. The diff runs exact signature → handle (**only while handles look
  stable: at least half the exact matches kept their handle**) → … . Urban already clean-reimplemented topology and diff
  (R8.8 / R8.20). **Not yet taken: the handle-stability gate** for diffing the DWG against its DXF export.
* **Backends:** COM (live AutoCAD) and ezdxf. Tools carry **per-tool `readOnlyHint`** (e.g. Drawing Info = true). This is
  the better MCP for a read-only qualification.
* **What U-C4N does that Urban does not:** an explicit `skipped` with handle for entity kinds it cannot read **at the
  tool surface**, and per-tool read-only annotations. **What Urban does better:** foreign-plan door closure (portal
  model), curves, OCS, MINSERT / XREF, units authority (U-C4N's `unit_of` mm default stays rejected), two-layer release.
  **Take:** clean-reimplement the handle-stability gate. Nothing else.

### C.B beiming183-cloud/AutoCAD-MCP (unchanged)

| Mechanism | Classification |
|---|---|
| `drawing.audit` / `audit_geometry`: ZERO_LENGTH, SHORT, duplicate vertex, self-intersection, **DUPLICATE_ENTITY**, DANGLING, NEAR_MISS, INTERIOR_CROSSING, **UNASSIGNED_ENTITY**, **MISSING_SEMANTIC_FIELD** | **Urban-owned code** (clean reimplementation). UNASSIGNED_ENTITY is the rule that would have caught the CB schedule (texts on a structural sheet claimed by no reader) |
| `geometry_digest` (order- and handle-independent) | already adopted as a pattern; **OCS-blind**, so never proof of physical geometry (lock) |
| entity counts by type / layer, handle readback | **native AutoCAD oracle** (Route B, read-only) |
| endpoint topology graph, near-gap, dangling, crossings | Urban-owned (already in `engine/source/topology`) |
| cross-view **PROJECTION_ALIGNMENT** | **research-only**: needs caller-supplied handle lists; not automatic view matching. Useful for plan ↔ elevation ↔ section height checks once views are paired |
| native render (`drawing_render_preview`, plot to PNG) | **native oracle** for the Route C raster comparison |
| tools grouped (`AutoCAD Drawing Operations` etc.) with `readOnlyHint: False` | read-only cannot be guaranteed at tool level; it needs an allowlist proxy |

### C.C Kentucky-ai/OpenTakeoff (34 commits since the lock)

* **One-Click / room extraction (`web/src/lib/oneclick.ts`, 3 848 lines):** PDF op list → segments; downscaled 1-bit
  mask; 4-connected flood against 8-connected barriers; **tiered hatch mask** (walls bit 1, periodic hatch bit 2) with an
  escalating re-flood accepted only within an area-growth cap; **seal ladder** (dilate, flood, grow back;
  `GAP_BRIDGE_MAX = 2 px`, "never doorways"); **door seal** by the swing chord hinge → strike (`doorseal.ts`);
  minimum-passage rule; **raster fallback** for scanned sheets, marked `raster_traced: true`; **layer roles** from PDF
  OCGs, then pen weight, then **stroke luminance** (#260); subpath / figure facts (closed, fill luminance = poché).
* **Scale gate:** without `set_scale` it returns px only and commits nothing.
* **Cutouts:** `role: "deduct"` shapes; `cut_out` verb.
* **confidence_factors:** each sub-1.0 confidence names what deducted it (e.g. `sealed-opening(10% synthetic
  boundary)`), described as "a review PRIORITIZER, never a verification".
* **Overlay review / provenance:** `view_sheet {overlay:true}`; provenance schema records method, actor, seed,
  gap_sealed_px, door_wedges, hatch_filtered, raster_traced, edits …
* **Why One-Click is gated (`docs/design/ONE_CLICK_GATE.md`):** "an answer that may be wrong in ways that read as right,
  and a quantity that reads as right is the worst failure an estimating tool has." The verbs are **not registered**
  while it is re-validated against a wider corpus. **Corpus / tests:** owner hand takeoffs (`all-goldens.json`, real
  client plans kept *outside* the repo); the PROOF renderer (owner ring GREEN, engine BLUE within 5% / RED outside); and
  the **click-stability test** (`frag.mjs`: a grid of clicks in one room, count distinct answers).
* **New since the lock:** on-device OCR of **raster schedules** with misread-code repair and flags, OCR-confidence
  measurement against misreads, and table-ruling cleanup. This is directly relevant to D1 / G7: the Alsenan schedules
  are vector glyphs without a text layer.
* **Take (clean reimplementation, Python, Urban-owned):** named confidence factors per line; the PROOF overlay
  discipline per quantity; the click / seed stability metric applied to Urban's space builder; and the schedule-read
  "never silent row drop + flagged misread" rule. **Do not take** the flood as a measurement route. It stays a Route C
  candidate generator.

### C.D Rebar donors (all four have no licence: ideas only)

| Donor | Callout grammar | BBS / schedule extraction | Bar marks | Shape recognition | Weight reconciliation | Verdict |
|---|---|---|---|---|---|---|
| v-Zak/bar-bending-scheduler (2023) | regex `\d+H\d+-\d+` (UK "qty H size – mark"), MTEXT only | none | yes (mark) | no | sum by size → CSV | idea: mark-keyed totals; too narrow |
| thuanlm-eng/steel-bar-takeoff | prompt-defined `(15) 18Ø14a200 L=4320` = mark / count / Ø / spacing / length; parsing is done by an LLM | LLM | yes | no | kg/m = πD²/4 × 7850; per-Ø summary with % | idea: **per-Ø summary + % share** (adopted in §A.2); reject LLM-as-parser for quantities |
| divyanshu964/Rebar-Pdf-Extractor | loose regexes (DIA / LEN / QTY / SPC) | pdfplumber tables, Tesseract fallback | yes | no | D²/162 | idea only; the regexes are too permissive (any 1–3 digit number is a quantity) |
| xu323/Rebar-Material-Schedule-OCR-Pipeline | table cells | **layout analysis, merged cells (rowspan / colspan), per-cell OCR confidence, summary-row detection, browser review UI with anchor-stable cells** | yes | **template matching + CNN for bar shapes** | per row | **best idea donor for G7 (merged cell "6 9 Ø Ø") and G1 (shape codes)**: clean reimplementation of merged-cell geometry and per-cell confidence; no ML in the engine |

**What all four do that Urban does not:** they treat the **schedule / BBS table as the primary object** and the plan as
secondary. Urban reads plans first and schedules by known title. That inversion is exactly why the CB bars were missed.

### C.E conmcp and autoConst

* **conmcp (MIT):** the server never calls an LLM. It does deterministic sheet classification, table extraction,
  quantity-callout patterns and **report validation** (confidence per item, flagged mismatches, assumptions, **RFI
  candidates**: "plan vs schedule mismatch is an RFI"). Vision-first means it renders sheets for the client's model. It
  ships a field playbook of scope gotchas. **Take:** the plan-vs-schedule mismatch → RFI register (Urban owner questions
  are close, but they are not generated from mismatches).
* **autoConst (source-available, idea only):** index once into SQLite tables `sheets / words (with bbox) / objects
  (type, tag, source_method, confidence high/medium/low, attributes JSON) / measurements (value_m, method annotation |
  scaled, sanity_status)`. Confidence hierarchy: **schedule rows = HIGH, tag callouts = MEDIUM, printed dims = HIGH,
  scaled = LOW and must pass sanity**. The **envelope sanity check** takes the 98th percentile of annotation lengths as
  the building envelope and flags anything above 1.5× of it. **Take as ideas:** the confidence hierarchy (it matches
  Urban's DERIVED / RASTER / PROVISIONAL split) and an envelope check per sheet.

---

## D. Code loopholes (requested 1–15 plus new)

| # | Loophole | Verdict | Evidence |
|---|---|---|---|
| L-1 | PARTIAL rows enter technical totals | **CONFIRMED**. `release_model.TECH_IN_TOTAL` includes `PARTIAL`; C-FTG, C-COL-*, C-BEAM-GF/1F and B-150-EXT-1F / B-150-INT-1F / B-200-INT-GF are PARTIAL and summed. The technical total is a **verified lower bound** but is not labelled so | `engine/source/release_model.py:29-30` |
| L-2 | Roof WP includes the upturn m² while wet-room WP was split | **CONFIRMED** (`T-RWP-*` = flat + 0.20 × upturn) | BOQ lines T-RWP-GF/1F/2F |
| L-3 / L-13 | Strap rebar absent | **CONFIRMED = D4** | §A.4 |
| L-4 | 26 / 33 window heights are budget estimates | **CONFIRMED**: 19 PARTIAL + 7 BLOCKED technical, all BUDGET_ESTIMATE commercial | OPENING_REGISTER_V3B.heights |
| L-5 | 14 rooms have no Route B | **CONFIRMED** (12 reconciled, 1 mismatch GF-Z06 −1.03%, 14 route A only) | DUAL_MEASUREMENT_REGISTER |
| L-6 | Facades single route | **CONFIRMED** | FINISH_V3B_REGISTER.facades |
| L-7 | Rebar purchased −37.7% | **EXPLAINED** §B.3 (method + D1–D6) | |
| L-8 | Blockwork −36.5% | **PARTLY EXPLAINED**: parapet height, fence MAP exclusion; **≈ 140 m wall-length deficit unexplained** → top architectural audit | §B.1 |
| L-9 | Blinding −37% | **PROVEN scope** (owner method) | §B.1 |
| L-10 | RC −10.3% | **PROVEN** row by row | §B.2 |
| L-11 | Every slab annotation assigned exactly once | **YES for annotations** (123: 92 bound, 12 partial, 8 detail, 7 text-only, 2 drawn-extent, 2 de-duplicated "same family / direction / panel"). **The de-dup rule needs a check**: two identical labels can be two layers (OQ-9). **No per-panel check** (G4) | slab_binding.rows |
| L-12 | Stirrup / tie counts from schedule / spacing | **YES**: beams `ceil(rate/m × clear)`, columns `ceil(6 × interval)`, GB `floor(L / 0.15) + 1`, lintels 5/m. **But** inner links (box symbol) are not modelled (G3) and column ties run over the full storey interval (includes the beam joint; acceptable, documented) | V3a code |
| L-14 | Double count beam / side bar / residue | **NONE FOUND**: side bars are a separate role on the same 24 beams (no overlap with top / bottom / stirrups); residue handles are disjoint from BEAMS; GB "bottom" ×2 = the 3 + 3 layers of the detail | §A.1 |
| L-15 | Bars > 12 m split with the project lap | **YES**: laps_per_bar computed (boundary wall 44.07 m → 3 laps); tension 70Ø / compression 40Ø per p.8; column splice 40Ø per floor | REBAR register |
| **L-16 (new)** | **Silent population skip**: a definition missing or empty → no set **and no BLOCKED row** (FF, CB types) | **CONFIRMED** (D1, D3) | `footing_rebar`, `beam_rebar` |
| **L-17 (new)** | A merged zone name containing GARDEN / Wash (outdoor / wet) is accepted as one dry floor | **CONFIRMED** (GF-Z04, GF-Z06) | FINISH register names |
| **L-18 (new)** | Skirting may run along void / railing edges | **SUSPECTED** (1F-Z06 80.8 lm) | to audit |
| **L-19 (new)** | Concrete and rebar use different occurrence filters (column state) | **CONFIRMED = D5** | |
| **L-20 (new)** | Typical-label scope = smallest enclosing cell | **CONFIRMED = D6** | |
| **L-21 (new)** | Evaluation MAP errors: railing (E1), fence excluded from blockwork (E2), roof WP flat vs flat + upturn (E3), RC "residue / provisional" pre-declared cause hid D1 / D4 (E4) | **CONFIRMED** | `alsenan_v3b_evaluation.py: MAP` |
| **L-22 (new)** | Schedule tables are consumed by **known title only**: no inventory says which schedules / tables on a sheet were read | **CONFIRMED**: root cause of D1 | `alsenan_phase_a3.py` |

---

## E. Live AutoCAD MCP qualification plan (Claude Desktop + AutoCAD on Windows): lab, not production

**Set-up:** a Windows machine with AutoCAD; Claude Desktop with **U-C4N/Autocad-MCP (COM backend)** and
**beiming183/AutoCAD-MCP (native .NET plugin over a named pipe)**, one at a time. Work on a **copy** of `P7757.dwg` /
`ST7757.dwg`; record the SHA-256 before and after every session. **Read-only enforcement:** an allowlist of tools
(U-C4N: only `readOnlyHint: true`; beiming183: only query sub-operations through a proxy that rejects mutating
commands); `UNDO` mark checks; file hash unchanged; no save. Any write attempt = **FAIL of the read-only criterion**.

**Routes per case:** (1) MANUAL AUTOCAD: a human uses LIST / AREA / DIST / DIMLINEAR / QSELECT, with screenshots;
(2) NATIVE MCP: tool output with handles; (3) URBAN: K1 / K2 DXF canonical input; (4) PDF ROUTE B: Urban raster lane
or OpenTakeoff-style trace on the printed sheet.
**Thresholds:** lengths / areas **PASS < 0.25%**, **CLOSE < 1%**, **REVIEW ≥ 1%**; counts and texts must be exact.
**Scored per MCP:** accuracy (cases PASS), transparency (provenance + handle per value), handle availability, read-only
compliance, failure honesty (explicit "skipped / cannot read" vs silent).

| # | Case (Alsenan) | Quantity | Why |
|---|---|---|---|
| 1 | INSUNITS + drawing units on P7757 and ST7757 | unit | unit authority |
| 2 | Entity count by type, model space | count | census |
| 3 | Entity count by layer (wall, S-BOUN, layer "1") | count | layer roles |
| 4 | Handle readback for 20 sampled handles (type, layer, geometry) | exact | handle oracle |
| 5 | Room GF-R14 MASTER BED polyline area | m² | area |
| 6 | Room GF-Z04 boundary area (merged zone) | m² | over-closure check |
| 7 | Curved master-bed glazing arc length | m | arcs / bulges |
| 8 | Door swing arcs on GF: count and radii | count / m | door evidence |
| 9 | Window block INSERT count + scale / rotation | count | blocks |
| 10 | A MINSERT / array instance count (if present) | count | MINSERT |
| 11 | Nested block with negative scale (mirrored) placement | point | OCS / mirroring |
| 12 | Entity with non-default extrusion (OCS) | point | OCS |
| 13 | XREF presence / resolution | state | XREF |
| 14 | Legacy Arabic TEXT decode for 10 room labels | text | encoding |
| 15 | DIMENSION measurement vs override text (10 dims) | m / text | printed vs geometric |
| 16 | Hatch area in a wet room | m² | hatch |
| 17 | Column outline C9 on the GF storey sheet | m² | structural outline |
| 18 | Footing FF outline 4.6 × 4.5 | m | footing |
| 19 | Strap SB1 band length (clear) | m | D4 geometry |
| 20 | CB8 band total length on the GF roof slab sheet | m | D1 geometry |
| 21 | Interior ground-beam band GB-030 | m | GB |
| 22 | Exterior GB total length (28 spans) | m | GB ext |
| 23 | Ground-slab zone outlines (cells around the two labels) | m² | D6 |
| 24 | Slab annotation 53D position and bound bar extent | m | slab binding |
| 25 | Boundary wall S-BOUN polyline length | m | 44.07 m |
| 26 | Pool outline (blocks 7C5 / 7C6) | m | pool |
| 27 | Dome plan circles 12EB / 1300 / 2F33 radii | m | domes |
| 28 | Parapet run length per roof | m | parapet |
| 29 | Stair tread lines count per flight | count | stairs |
| 30 | Text inventory on the schedule sheets (every table title, CB1–CB13) | text / count | L-22 |
| 31 | Paper-space vs model-space separation (frames, viewports) | count | region identity |
| 32 | DWG vs DXF export diff (signature + handle-stability gate) | count | export identity |
| 33 | Frozen / off layers visibility for the wall layers | state | visibility authority |

**Decision rule:** an MCP qualifies as a **Route B oracle** only if it reaches ≥ 30 / 33 PASS-or-CLOSE, has 0 read-only
violations, returns handles for 100% of geometric answers and states every skipped entity. **Expectation (to be
measured, not assumed):** U-C4N wins on read-only and transparency (per-tool hints, `skipped` lists); beiming183 wins on
audit breadth (duplicate / unassigned / missing-field rules) and native rendering. Neither enters production.

---

## F. Three-oracle architecture assessment

* **A = Urban DXF (K1 / K2)**, **B = native AutoCAD via MCP**, **C = PDF / raster (Urban raster lane or OpenTakeoff
  style)**.
* **Majority vote is a defect locator, not truth.** 2-of-3 agreement points at the dissenting route to investigate. It
  never selects the quantity.
* **Independence caveat:** A and B read the **same DWG** (B is the authoring kernel, A a decoder), so they share every
  *source* error (a mis-drawn wall, a stale schedule). C is an independent rendering of the same design, so a design
  error is invisible to all three. Only a human route (a manual QS, or the freelancer *after freeze*) or a physical
  contradiction (finish without structure, D6) catches it.
* **What each catches:** A ≠ B → decoder defect (OCS, MINSERT, units, encoding). A = B ≠ C → print / plot or
  scale-calibration difference, or a raster misread. All agree but the human differs → **scope / convention**
  (§B: plaster height, blinding) or **a population all three ignore** (CB bars: all three "see" the schedule, none
  *reads* it).
* **Lesson from D1:** oracles compare *values*. They cannot find *missing populations*. An **inventory oracle** is needed
  in addition: every table title, schedule row and tag text must be claimed by a reader or explicitly UNREAD (L-22).

---

## G. Drawing knowledge database (index once / query many): recommendation

**Recommend: YES, as a derived, rebuildable SQLite index (`sqlite3` is stdlib, so `engine/source` stays
stdlib-only).** It is **never** an authority over the frozen registers.

* **Tables (Urban's own design, not autoConst's text):** `sources` (hash, revision), `sheets` (role, region, scale
  authority), `texts` (handle, value, decoded value, bbox, layer, reader_claim), `tables` (title, sheet, bbox, row / col
  grid, **reader**, **consumed rows / total rows**), `objects` (tag, type, occurrence, state), `bar_sets` (population,
  role, Ø, count rule, length, class), `quantities` (line code, class, method), `evidence_links` (quantity ↔ handles),
  `sanity` (envelope, kg/m³ diagnostic, per-Ø share, panel completeness).
* **Queries that would have caught this round's defects:** "tables with consumed_rows < total_rows" → D1 / G7; "concrete
  occurrences with no bar_set and no BLOCKED row" → D1 / D3 / D4; "bar_sets whose occurrence state ∉ concrete states" →
  D5; "floor-finish area over cells with no structural floor" → D6; "texts on structural sheets with no reader_claim" →
  L-22.
* **Rules:** built from the canonical input after a freeze; digest-pinned; deterministic rebuild; read-only query
  surface; no LLM writes to it.

---

## H. WHAT IS STILL STOPPING URBAN FROM MATCHING OR BEATING A GOOD HUMAN QS?

A good human QS **reads every schedule first, then counts occurrences, then asks about anything that is not drawn**.
Urban reads geometry very well, but it still loses whole populations silently.

| Weakness | Root cause | Current engine | Better algorithm | Public donor / paper / MCP | Difficulty | Expected accuracy improvement | Regression risk |
|---|---|---|---|---|---|---|---|
| W1 Whole populations missing (CB, straps, FF) | readers keyed to known titles; empty definition = silent skip | `alsenan_phase_a3` title list; `footing_rebar` / `beam_rebar` | **schedule inventory + population-completeness invariant**: every concrete occurrence ↔ bar sets or an explicit BLOCKED row; every table ↔ reader | beiming183 UNASSIGNED_ENTITY; xu323 table / summary-row detection; autoConst schema idea | M | rebar +3 t (≈ +11% of net) | low (adds rows, changes no existing one) |
| W2 Schedule semantics (per-metre, merged cells, REMARKS, symbols) | free-text parse without a typed grammar | `bars: {count, dia, per_m}` loosely applied | typed callout grammar (count / per-m / @spacing / layer / role) with a unit test per form; merged-cell split by row geometry; REMARKS column parsed | thuanlm grammar idea; xu323 merged cells; OpenTakeoff misread repair | L–M | +0.6–1.5 t | low |
| W3 Typical-label scope | binds a label to the smallest enclosing cell | `ground()` min-area hit | scope inference: same-label propagation over contiguous cells of the same role, with a **physical-contradiction check** (finish without structure) → OWNER question, never silent | — (Urban-owned) | M | ground slab +10.9–18 m³ | medium (owner-gated) |
| W4 Wall-length deficit in blockwork (≈ 140 m) | wall runs without a material claim / unbound bands drop out | blockwork pieces only from claimed bands | per-floor **wall-length conservation**: arch wall centreline = blockwork + RC wall + openings + columns + UNCLAIMED, where UNCLAIMED must be 0 or listed | U-C4N wall model (pattern) | H | blockwork up to +30% | medium |
| W5 Wet identity in merged zones | closure merges a wash / W.C into a dry zone | room roles by label set | forbid mixed wet + dry + outdoor labels in one zone; split by sub-label seed or raise LEAK | OpenTakeoff door seal / min-passage ideas | H | tile / WP +15–20% | medium |
| W6 Detail-shape bars (boxed, stairs, inner links) | blocked without a shape library | BLOCKED | shape-code library (BS 8666 / ACI-style codes) instantiated from member dims + cover; PROVISIONAL_SOURCE_DERIVED until confirmed | xu323 shape templates (idea) | M | +0.5–1.3 t | low |
| W7 Height / method conventions | owner methods not asked per trade | plaster to soffit, parapet 0.5 | OWNER_METHOD_REGISTER entries per trade with both bases published | conmcp playbook idea | L | removes ±18% plaster / ±47% parapet disputes | low |
| W8 Single-route quantities | no Route B for 14 rooms / facades | dual register | Route C raster trace with PROOF overlay; click / seed stability metric | OpenTakeoff PROOF / frag | M | confidence, not totals | low |
| W9 Tests prove consistency, not correctness | fixtures assert invariants of what was built | 95+ tests, mutations | **known-answer goldens per population** (hand-measured on Alsenan + Qortuba, frozen before runs); a missing-population mutation (delete a schedule → must raise) | OpenTakeoff goldens + PROOF | M | catches the next D1 | low |
| W10 Evaluation map can hide defects | pre-declared causes accepted without decomposition | MAP + TOL 10% | element-typed map, every row decomposed (§B style) before a cause is accepted | — | L | honesty | none |

### WHAT DID WE MISS FROM THE DONORS IN EARLIER ROUNDS?

1. **beiming183 UNASSIGNED_ENTITY / MISSING_SEMANTIC_FIELD.** We took its digest and diff patterns, but not the
   "everything must be claimed" rule. That rule would have exposed the unread CB bar texts.
2. **OpenTakeoff goldens + PROOF overlay + click stability.** We adopted its *gating* stance, but not its *proof*
   discipline: no quantity is accepted until a person has seen the ring against the hand takeoff.
3. **OpenTakeoff named confidence_factors.** Urban has classes and ranges but does not name, per line, *which edge or
   assumption* cost the confidence.
4. **autoConst schedule = HIGH / tag = MEDIUM hierarchy, and the envelope sanity check.** These are cheap gross-error
   detectors we never added.
5. **conmcp plan-vs-schedule mismatch → RFI.** Our owner questions are written by hand, not generated from mismatches
   (F3 two tags vs schedule; FF garbled cell; 2F columns not drawn).
6. **Rebar donors' schedule-first orientation and per-Ø summary.** Urban went plan-first. The per-Ø share would have
   shown the Ø18 deficit.
7. **xu323 merged-cell handling.** It would have split "6 9 Ø Ø 14/m 14/m" correctly.

---

## I. Ranked next 10 engine improvements (after review only)

| Rank | Improvement | Fixes | Class of the output | Est. effect | Risk |
|---|---|---|---|---|---|
| 1 | **Population-completeness invariant + schedule/table inventory** (no silent skip; every table consumed or UNREAD) | L-16, L-22, D1 / D3 detection | gate (no quantity) | prevents the next D1 | low |
| 2 | **Continuous-beam bar transcription + CB rebar population** (per span / support / stirrups / middle bars, with confidence; support widths from the plan; hooks and laps through BBS) | D1 | DERIVED / PROVISIONAL_SOURCE_DERIVED | +≈ 2.2 t | low |
| 3 | **Column rebar uses the concrete occurrence filter** (exclude NOT_DRAWN / NOT_IN_STOREY; BLOCKED concrete → bars not DERIVED) | D5, L-19 | correction | −1.04 t | low |
| 4 | **Typed bar grammar**: per-metre footing bars; merged-cell split (FF); REMARKS side bars | D2, D3 / G7, G2 | DERIVED (+ BLOCKED until FF confirmed) | +0.9–1.6 t | low |
| 5 | **Strap-beam rebar population** from the SB rows + measured straps (anchorage into the footings PROVISIONAL_CODE_METHOD) | D4 | DERIVED + provisional hooks | +0.42–0.65 t | low |
| 6 | **Ground-slab scope inference + contradiction check** → owner question | D6, L-20 | PROVISIONAL until OQ-2 | +10.9–18 m³, +0.67–1.1 t | medium |
| 7 | **Blockwork wall-length conservation audit** per floor (UNCLAIMED must be 0 or listed) | L-8 | audit, then corrections | blockwork up to +30% | medium |
| 8 | **Wet / dry / outdoor zone purity** (no GARDEN or Wash inside a dry floor zone) + 1F missing baths | L-17, W5 | correction | tile / WP +15–20% | medium |
| 9 | **Shape-code library** for boxed footing bars, stair bars (if a callout appears) and inner links (after OQ-7) | G1, G3, G5 | PROVISIONAL_SOURCE_DERIVED | +0.5–1.3 t | low |
| 10 | **Evaluation + reporting honesty**: fix MAP E1–E4; split roof WP (flat m² + upturn lm); label the technical total "VERIFIED lower bound (contains PARTIAL)"; user-facing terminology (§K) | L-1, L-2, L-21 | reporting | clarity | none |

---

## J. What is needed from ChatGPT / Mohammad

**Owner questions (Mohammad):**

* **OQ-1:** Is the 1.8 × 1.8 shaft an **elevator**? Evidence: ST7757 p.8 note 19 ("beams tying the elevator columns at
  3.00 m … around the elevator shaft"), freelancer "elevator walls 20 cm" and "for lift doors 17.4 m". **Not assumed**
  until answered.
* **OQ-2:** Is there a 10 cm slab-on-grade (5Ø10/m E.W.) under **all** GF rooms, or only in the two labelled cells?
* **OQ-3:** The FF schedule cell reads "6 / 9 Ø14/m". Which is top and which is bottom (or long / short)?
* **OQ-4:** Do F8 / F12 / F13 / F14 / FF have boxed bars in addition to the scheduled mesh? Is the shape as in p.13?
* **OQ-5:** Stairs: is there a reinforcement detail? Are there an entrance stair and a second stair ("stair 2",
  1.2 × 16.4 m in the freelancer)?
* **OQ-6:** Pool: confirm the inner size and depth, and whether the **pump room** is in scope.
* **OQ-7:** Is the box symbol beside B17, B19–B26 and SB1–SB3 "additional inner links"?
* **OQ-8:** Parapet height basis (0.50 Urban vs 1.0 / 1.8 freelancer).
* **OQ-9:** Slab labels 491 / 749 are identical to 490 / 748 on the same panel. Is that one layer (counted once) or two?
* **OQ-10:** Plaster height basis: to the structural soffit (Urban) or to the false-ceiling / paint line (freelancer
  3.6)?
* **OQ-11:** F3 is tagged twice on the foundation plan; the freelancer has one. Which is right?
* **OQ-12:** Is there a 20 × 60 perimeter strap / edge beam (freelancer 71.7 m) separate from the exterior ground beams?
* **OQ-13:** Do 2F columns continue where they are not drawn on the 2F sheet (13 columns)?
* **Approve** the implementation order in §I.

**ChatGPT review:**

* Challenge each PROVEN / PROBABLE verdict in §B.
* Re-derive the CB diagnostic from the p.11–12 images independently.
* Review the population-completeness invariant design (§I-1) and the DB schema (§G).
* Review the MCP qualification protocol (§E) before anyone runs it.

---

## K. User-facing terminology (to apply in reporting only after approval)

| Internal (unchanged in code) | User-facing label |
|---|---|
| TECHNICAL view (MEASURED, DERIVED, RASTER_DERIVED, SOURCE_RULE, CODE_METHOD, URBAN_STANDARD, OWNER_PROJECT_FACT) | **VERIFIED / DRAWING-BASED QTY** |
| PARTIAL inside the technical view | **VERIFIED / DRAWING-BASED QTY: INCOMPLETE (verified part only)**. Must be visible on the line and the total |
| COMMERCIAL view (PROVISIONAL_*, OWNER_APPROVED_PROVISIONAL) | **ESTIMATED / ASSUMPTION-BASED QTY** |
| BUDGET_ESTIMATE (beside, never inside the total) | **ESTIMATED: BUDGET ONLY (not in total)** |
| BLOCKED / REVIEW / PENDING | **NOT QUANTIFIED: needs source / owner** |

---

## L. Specific files / functions for ChatGPT to inspect

| File | Function / lines | Why |
|---|---|---|
| `research/external_engine_lab/alsenan_v3_structure.py` | `footing_rebar` (273–291) | D2 per-metre; D3 silent skip; boxed BLOCKED |
| same | `column_rebar` (294–317) | D5: no `state` filter |
| same | `beam_rebar` (319–347) | D1: types without a definition are skipped silently; side bars from note 21 |
| same | `ground` (85–130), `ground_items` (211–263) | D6: `outer = min(hit, key=area)` |
| `research/external_engine_lab/alsenan_phase_a3.py` | `CB_TRANSCRIPTION` (48–73), continuous rows (~350–380), simple-beam library (~248) | B / H / spans only; bars never transcribed; REMARKS read but unused for bars |
| `research/external_engine_lab/alsenan_phase_b2a.py` | 385–416, 452 | the column state vocabulary that rebar ignores |
| `research/external_engine_lab/alsenan_v3b_struct.py` | `necks` (382–411), `stairs` (635), `pool` (538), `ground_zones` (440) | starters by median; stairs blocked; pool geometry; zone 2 |
| `research/external_engine_lab/alsenan_v3b_rebar.py` | `inventory` (42), `extra_sets` (79), `population_register` (294) | no STRAP / CB population; no completeness assertion |
| `research/external_engine_lab/alsenan_v3b_evaluation.py` | `MAP` | E1–E4 |
| `engine/source/release_model.py` | `TECH_IN_TOTAL` (29–30) | L-1 PARTIAL in the verified total |
| `engine/source/slab_rebar_binding.py` | duplicate-label rule | OQ-9 |
| `research/external_engine_lab/alsenan_v3b_finish.py` | `net_finishes`, zone names | L-17, L-18, plaster height |
| `tests/alsenan/test_v3b_registers.py` | whole file | consistency tests only: no population-completeness or known-answer test |

---

## Appendix: reproduction (read-only)

All numbers above were computed from the committed frozen registers (`tests/alsenan/registers_v3b/*.json`,
`tests/alsenan/registers_b1/*.json`) and the V3a / V3b scratch context (`ctx.pkl`, rebuilt from commit 17efc83). The
images came from `ST7757.pdf` p.3, p.8, p.10, p.11, p.12 and p.13. Donor facts came from shallow clones at the commits
listed in §C. No register, engine file or benchmark file was modified. Benchmark binaries, XLSX and PDF deliverables were
not committed. The excluded files (Alsenan_Quotation_AR.md, alsenan_pricing.txt, alsenan_demo.xlsx,
ALRASHED_DETAILED_QUANTITY_TAKEOFF.xlsx, PDF 737b63b5, xlsx 6aafd947 / 7b6f737c) were not opened.
