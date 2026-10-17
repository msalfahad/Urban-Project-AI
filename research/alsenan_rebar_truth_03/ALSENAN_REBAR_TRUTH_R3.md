# Alsenan Accuracy Program — Round 3: Structural Rebar Truth Engine

**Baseline:** `7c5b162`. **Scope:** structural reinforcement only. No architectural trades, pricing or UI were touched.

**What this round did not do:**
- Nothing was tuned to 44.19 t, to kg/m³ ratios or to any human total. The benchmark was read only after the registers were frozen.
- No geometry changed.
- The frozen V3, V3b, Round-2 and Qortuba registers were not overwritten.

**Project final rebar total: NOT YET ESTABLISHED.** Only 4 of 208 rebar populations are complete.

## 0. Summary for ChatGPT and Mohammad

### What worked
- **A generic typed rebar model** (`engine/source/rebar_model.py`):
  - explicit count modes;
  - D²/162 with no early rounding;
  - length *parts* with their own states;
  - component → population → trade release;
  - completeness, mass-conservation, provenance, duplicate, source-consistency and BBS-eligibility invariants.
- **Two-layer footings (D2, G11 → PASS).**
  - F8 / F12 / F13 / F14 and FF are now counted as bars per metre, both layers, both directions.
  - The old reading (rate taken as an absolute count, bottom layer dropped) is reconstructed exactly at 245.58 kg.
- **Straps (D4, G13 → PASS).**
  - SB1 and SB3 are consumed.
  - SB2 stays BLOCKED as a source conflict, with both rows (100×50 and 80×50) audited and neither selected.
- **Continuous beams (D1).**
  - The C-BEAM block definitions contain no bar graphics. The bars are drawn in model space inside each schedule frame (layer S-REIN.D), together with '/m' stirrup-zone dimensions and split "2 / Ø / 12" callouts.
  - Round 3 reads that geometry, binds labels one-to-one and normalises each bar to span coordinates.
  - Lengths are split into a VERIFIED core (whole spans from the schedule attributes) and a PROVISIONAL template part (N.T.S. proportions × real span).
  - Every CB occurrence has a full component matrix.
- **The continuous top bars that Round 2 called unreadable are now bound** (2Ø12, 3Ø12, 3Ø14 and loose 5Ø18 / 3Ø16 callouts).
- **D5 columns are reconciled exactly.** The 26 blocked occurrences weigh 1,739.65 kg verified-equivalent, the same as Round 2, and they stay out of every released total.
- **The (T&B) qualifiers are bound by position:**
  - all four sit ≤ 533 mm from one same-orientation slab annotation, with the next candidate ≥ 2.1 m away;
  - their top layers are added, +222.48 kg;
  - de-duplication is proven not to collapse layers.
- **Cover and lap authority were read from ST7757 page 8:**
  - note 22: cover ≥ 2.5 cm, or ≥ 7 cm against soil;
  - note 9: lap ≥ 70Ø (tension) / 40Ø (compression);
  - note 21: side bars.
  
  Every component cites a cover rule.
- **Mass conservation and the other invariants are all clean.** The build ran twice with identical output, 12 independent known-answer fixtures pass, and all 16 mutations are caught.

### What is not working / not yet established
- **Population completeness is only 1.9 %:** 4 of 208 non-out-of-scope populations are VERIFIED_COMPLETE (the FN footings). Nearly every population is a lower bound because required components are not detailed in the source:
  - anchorage and hooks;
  - side bars (note 21: mapping not printed);
  - BOXED cages (semantics unknown);
  - two-layer-footing top-mesh ends;
  - lift-pit walls;
  - the end-bar count convention.
- **CB cut-offs are template proportions.** The schedule diagram is not to scale and its spans are drawn equal, so support-bar and hanger lengths are PROVISIONAL (553.7 kg).
- **6 of 11 CB occurrences are not established:**
  - CB3 is a band-type conflict;
  - CB5, CB6, CB8 and CB12 have plan span counts that disagree with the schedule;
  - CB4's plan length does not confirm the schedule.
  
  CB2 and CB10 have no plan occurrence.
- **G15 (ground-slab scope) and G23 (stairs) remain XFAIL.** These are genuine engineering questions.
- **Carried populations are not yet re-audited** with the component model: ground beams, lintels, dome, pool, exterior ground beams, boundary wall, starters and residue.
- **Simple-beam verified weight fell** from the V3b 4,115.9 kg to 3,844.7 kg. The verified core is now the measured clear span; embedment to the centreline is PROVISIONAL.

### What I recommend next (Round 4)
1. Send the 14 engineering questions in §21 as one batch. Each answer is designed to promote a named, counted set of components; the registers say which.
2. Record each answer as a versioned human claim (the R8 claim mechanism) that flips specific component states. That is how the population completeness percentage rises, never by relaxing a rule.
3. Re-audit the carried populations (ground beams first: V3a reads p.13 "3Ø16 + 3Ø16" as two bottom layers) with the Round-3 component model.
4. Only then return to the architectural trades (blockwork, wet rooms, finishes, openings), as planned.

## 1. Production files changed

| Kind | File |
|---|---|
| New generic | `engine/source/rebar_model.py` (`REBAR_MODEL_V1`) |
| New Alsenan consumer | `research/external_engine_lab/alsenan_rebar_v3.py` (CB schedule-graphic reader, consumers, project invariants) |
| New runner / comparison | `research/alsenan_rebar_truth_03/build_rebar_v3.py`, `post_freeze_rebar_compare.py` |
| Tests | `tests/alsenan_rebar_truth/test_rebar_truth_r3.py`; `tests/alsenan_control_plane/test_control_plane_r2_gates.py` (G11 / G13 promoted to the R3 consumers) |

The following are unchanged and **not overwritten**:
- `alsenan_v3_structure.py`, V3b and Round-2 code;
- the frozen registers under `tests/alsenan/*`;
- the Round-2 registers;
- RC1 / Qortuba.

## 2. Rebar engine and data model

**`rebar_model`:**
- **Count modes:** ABSOLUTE_COUNT / BARS_PER_METRE / SPACING_MM / ONE_PER_OCCURRENCE / UNKNOWN. A mode is never inferred from another.
- **Per-metre counts:** the verified count is `ceil(rate × d)`; the convention count is `ceil(d/s)+1` and is PROVISIONAL.
- **Length parts:** CORE / EXTENSION / HOOK / ANCHORAGE / LEG / BEND / LAP, each COMPLETE / PARTIAL / PROVISIONAL / BLOCKED / NOT_REQUIRED.
- **Component kg:** `verified_kg` = verified count × COMPLETE length; `provisional_kg` = provisional parts + convention bars; `audit_kg` = blocked weight.
- **Population release:** VERIFIED_COMPLETE only when every required component is COMPLETE or NOT_REQUIRED **and** the occurrence is established. One BLOCKED, PARTIAL or PROVISIONAL required component caps it at LOWER_BOUND. A BLOCKED occurrence sends all of its kg to audit.
- **Laps (`lap_parts`):** computed only when a run exceeds the 12 m stock and a lap authority exists; otherwise BLOCKED_LAP_METHOD. Laps go to BBS length, never to net.
- **BBS (`bbs`):** cuts only COMPLETE / PARTIAL components of VC / LB populations, using their verified length plus procurement additions that have an authority (column storey splice, 40Ø, note 9).
- **`ratio_qa`:** reports kg/m³ for QA only and is never on a quantity path (gate G28).

**Cover authority** (`REBAR_SOURCE_DEFINITION_REGISTER.cover_rules`):

| Rule | Value | Applies to |
|---|---|---|
| COVER-SOIL-70 | 70 mm | footings, straps, ground beams, ground slab |
| COVER-MEMBER-25 | 25 mm | columns, beams, CB, slabs, lintels |
| COVER-STAIR | NOT_SPECIFIED | stairs (note 22 does not name them) |

**Lap authority:** LAP-TENSION-70D and LAP-COMPRESSION-40D (note 9). The 12 m stock length is a procurement fact (OD-V3B-12), not an engineering rule.

## 3. Footings

Old = frozen V3b technical; new = Round 3. Full table: `FOOTING_REBAR_REGISTER_V3.json`. Method and worked examples: `FOOTING_BAR_COUNT_METHOD.md`.

| Type | Occurrences | Old kg | New verified kg (≥) | New provisional kg | State | Why it is not complete |
|---|---|---|---|---|---|---|
| FN | 4 | 12.2 each | 12.2 each | 0 | **VERIFIED_COMPLETE** | BOXED cell empty → NOT_REQUIRED; printed counts; straight bottom bars (p.13) |
| F, F2–F6, F9, F11, F15 (FT) | 16 | = new | 9.4 – 181.4 (same as old) | 0 | LOWER_BOUND | BOXED "3+4"…"3+8" is a BOXED_COMPONENT_UNKNOWN_SEMANTICS component (p.13 draws a boxed cage) |
| F (1 occurrence) and F10 | 2 | 0 | 0 | 0 | BLOCKED | concrete not established (F / F10 source conflict); audit 72.1 kg; F/F10 provisional 62.7 kg is carried |
| F8 | 1 | 53.14 | 494.50 | 17.71 | LOWER_BOUND | per-metre both layers; top-mesh end detail BLOCKED |
| F12 | 1 | (see method doc) | 696.1 | 20.4 | LOWER_BOUND | as F8 |
| F13 | 1 | ″ | 408.9 | 17.9 | LOWER_BOUND | as F8 |
| F14 | 1 | ″ | 422.8 | 16.5 | LOWER_BOUND | as F8 |
| FF (lift) | 1 | 0 (cell unread) | 720.24 (straight mesh) | 76.9 (perimeter legs + end bars) | LOWER_BOUND | pit walls (6Ø12/m + 6Ø16/m, height per lift manufacturer) and 2Ø16 base bars BLOCKED |

**Footings total:** verified 3,629.6 kg (48.9 complete + 3,580.7 lower bound) + 149.5 kg provisional. The old frozen V3b technical total was 1,132.7 kg, of which 245.58 kg was the per-metre misreading.

## 4. Straps

| Strap | Clear length | State | Verified kg | Provisional kg | Note |
|---|---|---|---|---|---|
| SB1 (70×50; 7Ø16 bottom, 13Ø18 top, 8Ø8/m) | 4.551 m | PROVISIONAL | 0 | 199.2 + hooks | its clear length is measured to the face of a footing whose size is the F / F10 SOURCE_CONFLICT |
| SB2 | 2.294 m | **BLOCKED** | 0 | 0 | SOURCE_CONFLICT_DUPLICATE_SCHEDULE_KEY. Audit candidates: 100×50 (10Ø16 / 20Ø18) = 128.0 kg longitudinal; 80×50 (10Ø18 / 10Ø18) = 91.8 kg. **Neither row is selected.** |
| SB3 (50×40; 5Ø16, 5Ø18, 7Ø8/m) | 3.259 m | LOWER_BOUND | 69.6 | 2.4 | anchorage into the footings not detailed |

## 5. Simple beams

There are 78 occurrences: 68 LOWER_BOUND and 10 BLOCKED (8 with missing length, 2 not measured).

- **Verified:** 3,844.7 kg. The verified core is the measured clear span.
- **Provisional:** 427.7 kg. This covers embedment to the support centrelines (the V3a basis), the end-bar convention and stirrup hooks.
- **Old V3b technical:** 4,115.9 kg (net 4,561.6 kg).

Every beam deeper than 60 cm (B7–B29) carries a BLOCKED SIDE_BARS component. Its REMARKS token is kept, for example `2Ø12/30cm`, `2Ø16/20cm` or `2Ø14/20cm`. **No simple beam is VERIFIED_COMPLETE**, because anchorage is BLOCKED for all of them and side bars are BLOCKED where required.

The provisional note-21 side-bar range that V3b carried (272.9 kg) is **withdrawn**: it is not calculated until the semantics are confirmed.

## 6. Continuous beams CB1–CB13

- **Machine-readable components:**
  - 13 definitions, read with B, H, spans, bottom bars per span, MID support bars and stirrups per span;
  - every drawn bar in all 13 frames (S-REIN.D), bound one-to-one to an attribute or a split callout;
  - '/m' stirrup-zone dimensions.
  
  T/M-n is a design load and is never read as reinforcement.
- **Template finding:** there are four graphic variants. CB1/2/4/5/6/7/10/12/13 share one, CB9 and CB11 share one, and CB3 and CB8 are edited frames:
  - CB3 has a 3Ø16 support bar running deep into span 2, no span-2 top bar, and empty MID cells.
  - CB8 has a 5Ø18 span-1 top bar on the support row and an empty MID1 cell.
- **Calculated:**
  - bottom bars per span (core = schedule span, VERIFIED);
  - stirrups per span (zone = span − all support widths, VERIFIED lower bound; +1 end bar and hooks PROVISIONAL);
  - support bars and continuous / hanger top bars (template lengths, PROVISIONAL).
- **Blocked:**
  - drawn hook lengths and the end anchorage of bottom bars (not dimensioned);
  - side bars where H > 60 (note 21);
  - support cells left empty (CB3 MID1/MID2, CB8 MID1).
- **Laps:** NOT_REQUIRED. Every bar run is ≤ 12 m.

| Occurrence | Occurrence state | Release | Lower-bound kg | Provisional kg | Audit kg | Component states |
|---|---|---|---|---|---|---|
| CB:GF:CB1:H1249 | ESTABLISHED | VERIFIED_PARTIAL_LOWER_BOUND | 196.2 | 143.7 | 0.0 | BLOCKED 1, PARTIAL 4, PROVISIONAL 3 |
| CB:GF:CB3:H1171 | BLOCKED | BLOCKED | 0.0 | 0.0 | 138.7 | BLOCKED 2, PARTIAL 6, PROVISIONAL 3 |
| CB:GF:CB4:H1116 | PROVISIONAL | PROVISIONAL | 0.0 | 85.2 | 0.0 | NOT_REQUIRED 1, PARTIAL 4, PROVISIONAL 3 |
| CB:GF:CB5:H1140 | BLOCKED | BLOCKED | 0.0 | 0.0 | 89.3 | NOT_REQUIRED 1, PARTIAL 4, PROVISIONAL 3 |
| CB:GF:CB6:H1148 | BLOCKED | BLOCKED | 0.0 | 0.0 | 165.7 | BLOCKED 1, PARTIAL 4, PROVISIONAL 3 |
| CB:GF:CB7:H1145 | ESTABLISHED | VERIFIED_PARTIAL_LOWER_BOUND | 111.1 | 72.0 | 0.0 | BLOCKED 1, PARTIAL 4, PROVISIONAL 3 |
| CB:GF:CB8:H1695 | BLOCKED | BLOCKED | 0.0 | 0.0 | 376.1 | BLOCKED 2, PARTIAL 6, PROVISIONAL 4 |
| CB:1F:CB9:H1734 | ESTABLISHED | VERIFIED_PARTIAL_LOWER_BOUND | 89.4 | 72.6 | 0.0 | NOT_REQUIRED 1, PARTIAL 6, PROVISIONAL 5 |
| CB:1F:CB11:H1754 | ESTABLISHED | VERIFIED_PARTIAL_LOWER_BOUND | 199.4 | 119.6 | 0.0 | BLOCKED 1, PARTIAL 6, PROVISIONAL 5 |
| CB:1F:CB12:H1758 | BLOCKED | BLOCKED | 0.0 | 0.0 | 229.5 | BLOCKED 1, PARTIAL 4, PROVISIONAL 3 |
| CB:1F:CB13:H1898 | ESTABLISHED | VERIFIED_PARTIAL_LOWER_BOUND | 79.1 | 60.7 | 0.0 | NOT_REQUIRED 1, PARTIAL 4, PROVISIONAL 3 |

**CB total:** lower bound 675.2 kg, provisional 553.7 kg, blocked audit 999.3 kg. CB2 and CB10 are NO_PLAN_OCCURRENCE.

## 7. Columns

- **Valid occurrences:** 48 at LOWER_BOUND, 3,481.6 kg verified + 115.1 kg provisional.
  - Verticals: count × storey interval, COMPLETE.
  - Ties: 6Ø8/m over the clear column height; the end-bar convention and 135° hooks are PROVISIONAL.
  - The storey-splice lap of 40Ø (note 9) is in the BBS only.
- **D5:** 26 occurrences are BLOCKED_OCCURRENCE_NOT_ESTABLISHED, audit 1,808.7 kg (1,739.65 kg verified-equivalent, exactly Round 2). They are **not** re-added.
- **NOT_IN_STOREY:** 31 occurrences, recorded as NOT_IN_SCOPE.
- **Change from Round 2:** Round 2 had 3,590.2 kg; Round 3 has 3,481.6 kg. The −108.6 kg is because ties now run over the clear column height (interval − controlling beam depth) instead of the full interval.

## 8. Slab

- **(T&B):** all 4 qualifiers bind to one 2F annotation each: 7Ø14/m, 6Ø14/m, 6Ø12/m, 6Ø12/m.
  - Each has the same rotation, d1 = 416–533 mm and d2 ≥ 2,116 mm.
  - Each annotation had been bound bottom-only, and no top record existed, so the top layer was missing.
  - The top layers are added at +222.48 kg (in the 2F slab lower bound).
- **De-duplication (OQ-9):** both DUPLICATE_LABEL rows (8Ø16/m on GF and on 1F) repeat the same bar family, direction, panel and layer flag. The de-dup key includes the top/bottom flag, so **no genuine layer is collapsed**.
- **Slab populations:** LOWER_BOUND 5,019.0 kg + 196.3 kg provisional. The net is unchanged from the binder. The per-metre counts are split into a verified `ceil(rate × w)` part and a provisional binder end bar. A slab is never VERIFIED_COMPLETE, because it is not proven that every panel is annotated.

## 9. Ground slab

Ground slab is **PROVISIONAL**, 712.3 kg.

- **ZONE-1** (70.41 m²): the note lies in nested closed cells, the smallest 103.4 m² inside the 227.7 m² footprint. Scope is AMBIGUOUS, a BLOCKED_SCOPE remainder is recorded, and Q-S4 stays open. The min → max swap was **not** used.
- **ZONE-2** (44.98 m²): the note's smallest cell is a whole footprint (60.56 m²), so the scope is ESTABLISHED_SOLE_CANDIDATE.

Both zones stay provisional because the mesh run is area × rate, with the cover and edge bars not resolved. **G15 remains XFAIL.**

## 10. Stairs

Stairs are **BLOCKED_DETAIL_APPLICABILITY**, and **G23 remains XFAIL**. The p.16 detail does not match Alsenan's stairs:

| | p.16 detail | Alsenan |
|---|---|---|
| Scale | typical, N.T.S. | — |
| Levels | 0.00 / +2.00 / +4.00, one landing | GF→1F rises 4.50 m with two turns (plan tread runs 4 / 7 / 6), plus a 2.80 m-wide flight; 1F→2F rises 4.20 m |
| Waist | printed only as "THICK" | — |
| Binding | no plan callout binds it to a flight | — |

No generic stair ratio is used.

## 11. Rebar totals

**Project final rebar total: NOT YET ESTABLISHED.**

| | kg | t |
|---|---|---|
| Verified complete | 48.9 | 0.049 |
| Verified lower bound (≥) | 21,146.2 | 21.146 |
| Provisional | 6,959.1 | 6.959 |
| Budget (beam residue) | 319.1 | 0.319 |
| Blocked audit (never released) | 2,880.0 | 2.880 |

Populations: 4 VERIFIED_COMPLETE, 150 LOWER_BOUND, 8 PROVISIONAL, 1 BUDGET, 45 BLOCKED, 31 NOT_IN_SCOPE.

**By element type:**

| Element | Populations | Verified complete kg | Lower bound kg | Provisional kg | Budget kg | Audit kg | Population states |
|---|---|---|---|---|---|---|---|
| FOOTING | 22 | 48.9 | 838.2 | 0.0 | 0.0 | 72.1 | BLOCKED 2, VERIFIED_COMPLETE 4, VERIFIED_PARTIAL_LOWER_BOUND 16 |
| FOOTING_LIFT | 1 | 0.0 | 720.2 | 76.9 | 0.0 | 0.0 | VERIFIED_PARTIAL_LOWER_BOUND 1 |
| FOOTING_2_LAYER | 4 | 0.0 | 2,022.3 | 72.6 | 0.0 | 0.0 | VERIFIED_PARTIAL_LOWER_BOUND 4 |
| STRAP_BEAM | 3 | 0.0 | 69.6 | 201.6 | 0.0 | 0.0 | BLOCKED 1, PROVISIONAL 1, VERIFIED_PARTIAL_LOWER_BOUND 1 |
| BEAM | 78 | 0.0 | 3,844.7 | 427.7 | 0.0 | 0.0 | VERIFIED_PARTIAL_LOWER_BOUND 68, BLOCKED 10 |
| CONTINUOUS_BEAM | 11 | 0.0 | 675.2 | 553.7 | 0.0 | 999.3 | VERIFIED_PARTIAL_LOWER_BOUND 5, BLOCKED 5, PROVISIONAL 1 |
| COLUMN | 105 | 0.0 | 3,481.6 | 115.1 | 0.0 | 1,808.7 | VERIFIED_PARTIAL_LOWER_BOUND 48, BLOCKED 26, NOT_IN_SCOPE 31 |
| SLAB | 3 | 0.0 | 5,019.0 | 196.3 | 0.0 | 0.0 | VERIFIED_PARTIAL_LOWER_BOUND 3 |
| GROUND_SLAB | 2 | 0.0 | 0.0 | 712.3 | 0.0 | 0.0 | PROVISIONAL 2 |
| STAIR | 1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | BLOCKED 1 |
| GROUND | 1 | 0.0 | 1,252.9 | 183.0 | 0.0 | 0.0 | VERIFIED_PARTIAL_LOWER_BOUND 1 |
| LINTELS | 1 | 0.0 | 582.5 | 44.4 | 0.0 | 0.0 | VERIFIED_PARTIAL_LOWER_BOUND 1 |
| GROUND_BEAM_EXT | 1 | 0.0 | 0.0 | 2,793.7 | 0.0 | 0.0 | PROVISIONAL 1 |
| DOME | 1 | 0.0 | 2,054.2 | 24.9 | 0.0 | 0.0 | VERIFIED_PARTIAL_LOWER_BOUND 1 |
| POOL | 1 | 0.0 | 585.7 | 0.0 | 0.0 | 0.0 | VERIFIED_PARTIAL_LOWER_BOUND 1 |
| BEAM_RESIDUE | 1 | 0.0 | 0.0 | 0.0 | 319.1 | 0.0 | BUDGET 1 |
| BOUNDARY_WALL | 1 | 0.0 | 0.0 | 555.7 | 0.0 | 0.0 | PROVISIONAL 1 |
| FOOTING_F_F10 | 1 | 0.0 | 0.0 | 62.7 | 0.0 | 0.0 | PROVISIONAL 1 |
| COLUMN_STARTERS | 1 | 0.0 | 0.0 | 938.7 | 0.0 | 0.0 | PROVISIONAL 1 |

The populations from GROUND (ground beams) onwards are **carried from V3b and not re-audited** in Round 3. A carried population is never VERIFIED_COMPLETE.

## 12. BBS (`BBS_REGISTER_V3.json`, 12 m stock, laps 70Ø where a run > 12 m)

| | kg |
|---|---|
| Net (eligible verified) | 21,195.1 |
| Used (including column storey splices) | 21,668.7 |
| Purchased | 22,635.0 |
| Waste | 966.3 (4.27 %) |

- **Included:** 826 components.
- **Excluded:** every BLOCKED or PROVISIONAL component, and every component of a BLOCKED, PROVISIONAL or BUDGET population. These are:
  - carried provisional populations (128 components);
  - CB template / blocked parts (66);
  - D5 columns (52);
  - FF / FTB blocked parts (5);
  - ground slab (4);
  - straps SB1 / SB2 (3);
  - slab drawn-extent rows (2).

## 13–16. Coverage, completeness, mass conservation

- **Source coverage:** 84.4 % of the 77 schedule definitions feed a quantity. The others have no occurrence (CB2, CB10), are in conflict (SB2 ×2), or belong to unestablished occurrences. Round 2's accounting stays at 100 %. The CB split callouts and the (T&B) qualifiers that Round 2 left as BLOCKED_INTERPRETATION are now bound.
- **Population completeness:** 1.92 %, 4 of 208 non-out-of-scope populations.
- **Component completeness:** 28.95 % of required components are COMPLETE.

  | Component state | Count |
  |---|---|
  | COMPLETE | 335 |
  | PARTIAL | 578 |
  | PROVISIONAL | 173 |
  | BLOCKED | 71 |
  | NOT_REQUIRED | 95 |

- **Mass conservation:** all 13 checks pass: completeness, duplicates, provenance, mass, BBS eligibility, CB accounting, CB span cores, FTB layers, layer tags, D5, T&B, strap conflicts and source consistency.
  - Component sum = population sum = trade sum, per bucket.
  - BBS used ≥ net; purchased ≥ used; waste = purchased − used.

## 17. Gate transitions (`REBAR_GATE_TRANSITIONS.json`)

| Gate | Round 2 | Round 3 | Evidence |
|---|---|---|---|
| G11 | XFAIL | **PASS** | FTB / FF: 4 per-metre sets each, distribution = other side − 2c, verified count = ceil(rate × d) > rate |
| G13 | XFAIL | **PASS** | SB1 / SB3 bottom, top and stirrups; SB2 BLOCKED with 2 candidates, none selected |
| G15 | XFAIL | XFAIL | ZONE-1 scope AMBIGUOUS (Q-S4) |
| G23 | XFAIL | XFAIL | BLOCKED_DETAIL_APPLICABILITY |
| G24 | — | PASS | CB component accounting: every drawn bar accounted for exactly once, stirrups for every span, side bars listed |
| G25 | — | PASS | rebar mass conservation |
| G26 | — | PASS | source provenance (drawing sha, locator, raw value, formula, cover rule, D²/162) on every quantity |
| G27 | — | PASS | no benchmark leakage in the rebar builders |
| G28 | — | PASS | no kg/m³ quantity; every released formula uses D²/162 |
| G29 | — | PASS | no duplicate component or occurrence |
| G30 | — | PASS | no incomplete population marked complete |
| G31 | — | PASS | every RC occurrence has a rebar population (239 occurrences) |

## Post-freeze benchmark (FINDING_ONLY; `POST_FREEZE_REBAR_BENCHMARK.json`)

The benchmark was read after `INDEX.json` was frozen and every hash had been verified. "REBAR / ALL" is **44.19 t**, a WEAK_HUMAN_REFERENCE.

| Round 3 measure | t | vs benchmark |
|---|---|---|
| Verified complete + lower bound | 21.195 | −52.0 % |
| + provisional + budget | 28.473 | −35.6 % |
| Blocked audit, never released | 2.880 | |

V3b technical was 20.651 t.

The gap is explained by populations that are **blocked with no quantity at all**:
- side bars on 24 established simple beams and every CB deeper than 60 cm;
- BOXED cages on 16 footings;
- anchorage and hooks;
- stairs;
- lift-pit walls;
- the ground-slab remainder;
- six CB occurrences;
- the 26 D5 columns.

It is **not** closed by tuning.

## 18. Tests

See `TEST_RUN.md` for the full command lines and per-suite counts.

Full suite, one invocation at the Round-3 head: `python3 -m pytest -p no:cacheprovider -rfE` → **5,917 passed, 96 xfailed, 3 skipped, 0 failed** (310 s, exit 0).

| Suite | Passed | XFAIL | Skipped | Failed |
|---|---|---|---|---|
| `tests/alsenan_rebar_truth` (new) | 46 | 2 (G15, G23) | 0 | 0 |
| `tests/alsenan_control_plane` | 91 | 2 | 0 | 0 |
| `tests/alsenan` (frozen V3 / V3b / R1) | 304 | 0 | 0 | 0 |
| R8 (`tests/r8_*`) | 1,852 | 92 | 1 | 0 |
| Qortuba RC1 (`tests/rc1`) | 28 | 0 | 0 | 0 |
| Qortuba PA08 (`tests/test_pa08_qortuba*`) | 289 | 0 | 0 | 0 |
| Everything else | 3,307 | 0 | 2 | 0 |
| **Total** | **5,917** | **96** | **3** | **0** |

**Against the Round-2 baseline** (5,869 passed, 96 xfailed, 3 skipped): +48 passed. That is 46 new rebar tests, plus G11 and G13 moving from XFAIL to PASS in the control plane. The two new strict XFAILs (G15 and G23 in the R3 suite) replace them, so the xfail total is unchanged.

**What the new tests cover:**
- 12 independent known-answer fixtures, each hand-computed from D²/162 and the count rule;
- mutations 01–16, every one caught;
- gates G11, G13 and G24–G31 PASS;
- G15 and G23 are strict XFAIL;
- determinism (`build_rebar_v3.py --twice`);
- INDEX hash integrity, the post-freeze firewall and the no-gaming scans.

## 19. Qortuba / R8 regression

- Qortuba `RC1_REFERENCE` was not patched, and no RC1 file is in the diff.
- The Qortuba RC1 and R8 suites run in the same full-suite invocation. Results: Qortuba RC1 28 passed, Qortuba PA08 289 passed, R8 1,852 passed / 92 xfailed / 1 skipped. Nothing failed, and the counts are unchanged from Round 2.
- The frozen Alsenan registers (V3, V3b, Round 1, Round 2) are byte-unchanged; their own integrity tests pass.

## 20. Commit

The commit SHA is given in the final response, on branch `claude/access-permissions-setup-ii24ws`.

## 21. Exact engineering questions (one batch)

Each answer promotes a named set of components. The register field that each answer flips is given in brackets.

| ID | Question | Promotes |
|---|---|---|
| Q-R3-1 | CB schedule (ST7757 CB sheet): are support-bar cut-offs and hanger lengths as drawn (N.T.S. template proportions), or is there a rule (e.g. L/3, L/4, 0.25 L from support face)? | CB support / top PROVISIONAL → COMPLETE (553.7 kg) [`CONTINUOUS_BEAM_BAR_GEOMETRY_REGISTER.extension_state`] |
| Q-R3-2 | CB3 MID1/MID2 and CB8 MID1 cells are empty. Is there no support top bar there, or is one omitted from the schedule? | CB3 / CB8 BLOCKED support components |
| Q-R3-3 | CB occurrences: CB3 band type conflicts; CB5, CB6, CB8 and CB12 plan span counts differ from the schedule; CB4 plan length does not confirm. Which plan beams are CB2 and CB10 (no plan occurrence)? | 6 CB occurrences (999.3 kg audit) → ESTABLISHED |
| Q-R3-4 | Anchorage and hook lengths: what is the standard hook (90° / 135°) length and the end anchorage of bottom / top bars into supports (beams, CB, straps)? | ANCHORAGE / HOOK parts on all beams, CB, straps |
| Q-R3-5 | Note 21 side bars: which beams receive them (H > 60 cm?), and does the REMARKS token `2Ø12/30cm` mean 2 bars per face at 30 cm vertical spacing, or per side, or total? | SIDE_BARS on 24 simple beams + every CB > 60 cm |
| Q-R3-6 | Footing BOXED column "3+4" … "3+8": is this a cage of 3 + n bars, a starter set, or spacing? What diameter and length? | BOXED components on 16 footings |
| Q-R3-7 | Two-layer footings F8 / F12 / F13 / F14: top-mesh end shape (straight / bent down / U) and whether per-metre count is `ceil(rate × width)` or `ceil(width/s)+1`. | FTB top-mesh ends + end-bar convention |
| Q-R3-8 | Lift pit FF: pit wall height and plan size (manufacturer), and is the p.14 mesh a closed loop? Location and length of the 2Ø16 base bars? | FF pit walls + base bars |
| Q-R3-9 | SB2 duplicate schedule key: which row is correct, 100×50 (10Ø16 / 20Ø18) or 80×50 (10Ø18 / 10Ø18)? SB1 clear length depends on F / F10 footing size: which is correct? | SB2 BLOCKED → computed; SB1 PROVISIONAL → LB |
| Q-R3-10 | Stairs: does the p.16 typical detail apply to Alsenan's 4.50 m two-turn GF→1F stair and 4.20 m 1F→2F stair? What is the waist thickness and the bar set? | Stair population (G23) |
| Q-R3-11 | D5 columns: do the 26 D5 occurrences exist on the column layout (they are not established by the schedule binding)? | D5 1,739.65 kg verified-equivalent |
| Q-R3-12 | Column ties: is the 6Ø8/m tie zone over the clear height only, or over the full storey (through the beam)? 135° hook length? | Column tie PROVISIONAL parts |
| Q-R3-13 | Is the provisional 2 × 135° tie-hook allowance (ACI 318-19 Table 25.3.2 extension, edition unverified) and nominal cover (25 mm members / 70 mm soil) acceptable for cutting length? | All PROVISIONAL_HOOK_ALLOWANCE parts |
| Q-R3-14 | Ground beams (p.13): is "3Ø16 + 3Ø16" two bottom layers, or bottom + top? | Carried GROUND population re-audit |
| Q-S4 | Ground slab ZONE-1: the note sits in nested closed cells (103.4 m² inside 227.7 m²). Which area does the ground-slab mesh cover? | Ground slab scope (G15) |

## 22. Recommendation for Round 4

1. **Send §21 as one batch** to the structural engineer. Do not send them piecemeal.
2. **Record each answer as a versioned human claim** (the R8 claim mechanism), with the answer text, who answered and the date. Each claim flips named component states in the registers. Completeness rises only through claims, never by relaxing a rule.
3. **Re-audit the carried populations** with the Round-3 component model, in this order: ground beams (Q-R3-14), exterior ground beams, column starters, lintels, dome, pool, boundary wall, beam residue.
4. **Re-run the post-freeze benchmark** only after the claims are frozen, and keep it FINDING_ONLY.
5. **Then return to the architectural trades:** blockwork, wet rooms, finishes and openings.

Round 3 stops here. No architectural quantity was corrected.
