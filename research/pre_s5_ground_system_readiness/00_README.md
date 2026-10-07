# PRE-S5: ground-system rebar readiness (strap beams and ground beams)

| Item | Value |
|---|---|
| Baseline | `6b2b41b` (S4 accepted and frozen; S4 is not reopened) |
| Builder | `build_pre_s5.py <ST7757.dxf>` (sha256-checked; byte-identical on rebuild) |
| Engines | `engine/source/ground_beam_network.py`, `engine/source/ground_system_provenance.py` (generic, accurate-side, no kg) |

**No steel mass is calculated.** This round establishes S5's inputs: which members exist, which source detail applies to each, which dimensions are source-supported, and which components stay unresolved.

## 1. F3 provenance (`F3_PROVENANCE_CHECK.json`)

The S4 decision is drawing-based: F3 = 2 occurrences, SOURCE_VERIFIED. The drawing evidence is:
- outline 166B with tag 168F, drawn 160 × 140 = schedule;
- outline 166C with tag 168E, drawn 160 × 140 = schedule.

**What was wrong:** the S4 record's `project_source` sentence also cited the R9.1 donor crosswalk (08 FO10 / FO11) as if it were source. The per-part S4 provenance already cites drawing handles only.

**Correction:** the corrected record names **PROJECT_DRAWING** as the authority and lists the donor crosswalk as corroboration only. The OQ-11 reference disagreement stays a comparison flag. No quantity changed, and the frozen S4 files are untouched: the S4 freeze manifest still matches.

## 2. Ground-beam network: two generic fixes only (01, 02)

| | Old (V3, frozen) | New |
|---|---|---|
| Bands | 43 (41 straight + 2 arcs) | 43 (41 + 2) |
| Band length | 207.847 m | **208.129 m** (+0.282) |
| Spans | 59 | 59 |
| Span length | 198.796 m | **199.494 m** (+0.698) |
| Exterior spans (V3 zone test) | 28 | 29 |

The old network is re-derived and checked equal to the frozen V3 `GROUND_STRUCTURE_REGISTER`: lengths, exterior flags and band count. The R4 footprint-exterior flag is reproduced 59 / 59.

**MULTI_PARTNER_PAIRING** (one band):
- Face 114 (4.225 m) has two contiguous collinear partners on the other side: 115 (1.000 m) and 7DF (3.225 m).
- V3 kept one best partner, so the band was 3.225 m. It is now 4.225 m (+1.000 m), and its span grows from 0.300 to 1.300 m.
- The recovered strip joins two band systems. As a result:
  - the V3 slab-zone outline containing the "T=" note grows from 103.44 to 171.55 m²;
  - 11 spans' zone-proxy exterior flags flip (6 to exterior, including the recovered span; 5 to interior);
  - 1 footprint-proxy flag flips.
- The geometry of those spans is unchanged. Each flip is attributed by re-running the network with the multi-partner rule alone.

**ARC_OVERLAP** (one band):
- Arcs 157 (96.38°–263.62°) and 158 (109.75°–259.84°) now pair over their common range only: 109.75°–259.84° at r_c 2,400 mm.
- Band length goes from 7.005 m to 6.287 m (−0.718 m). The span after the CN column goes from 6.180 to 5.878 m (−0.302 m).
- Arcs 139 / 13A have identical sweeps and are unchanged (1.806 m).

**Attribution:** every change was attributed by four runs: V3, multi-partner only, arc overlap only, and both. **No other geometry changed.** The build stops on any change neither rule explains.

**Conservation (all pass):**
- every sheet line is accounted for: 83 admitted layer-1 faces, 341 other-layer lines rejected by layer, 2 short;
- for every face, covered + unpaired = face length;
- all 4 arcs are accounted for;
- 20 unpaired physical candidates are logged with reasons (18 face intervals, NO_PARTNER; 2 arc ends, UNPAIRED_SWEEP);
- band length = span length + length inside columns or dropped.

**Nodes (118 span ends):**

| Node kind | Count |
|---|---|
| COLUMN | 65 |
| BEAM_JUNCTION | 46 |
| FREE_END | 7 |

- 34 of 36 columns touch a span.
- 51 spans touch a footing (23 footing occurrences). Footings are placed on the GBP sheet by the shared FP / GBP sheet frame: 29 of 36 columns agree within 5 mm, the rest within 100 mm.

## 3. Strap beams (03, 05)

All three straps are on the foundation plan (FP). **Concrete keeps the clear length between footing faces.** That length is never reused as a bar length.

| Mark | Clear concrete | Column c/c | Footing c/c | Drawn faces | Schedule (SBT, p.10) | Authority |
|---|---|---|---|---|---|---|
| SB1 | 4.550 m | 7.600 m | 7.050 m | 7.350 m | 70×50; TOP 13Ø18; BOT 7Ø16; 8Ø8/m | SOURCE_VERIFIED (start support = the F / F10 outline: clear length is a lower bound) |
| SB2 | 1.829 m | 4.977 m | 4.388 m | 5.110 m | **two rows:** 80×50 (10Ø18 / 10Ø18 / 10Ø8/m) and 100×50 (20Ø18 / 10Ø16 / 10Ø8/m) | SOURCE_CONFLICT |
| SB3 | 2.838 m | 4.886 m | 4.559 m | 4.701 m | 50×40; TOP 5Ø18; BOT 5Ø16; 7Ø8/m | SOURCE_VERIFIED |

**Strap reinforcement sources, after exhausting the project sources:**
- the four SBT schedule rows (ATTRIB);
- the plan tags, which identify the members only;
- the 70 mm soil cover.

**What exists nowhere:**
- a strap section or detail;
- link topology;
- development into the footing.

The p.8 starter-development note (70Ø / 40Ø) applies to starters only. Note 21 (side bars) applies to depth > 60 cm only.

## 4. Ground-beam detail applicability (04)

**p.13 typical sections, with literal titles preserved:**

| Detail | Literal title (abridged) | Section | Bars |
|---|---|---|---|
| P13-GB-GT5M | "More than 5m length … without concentrated load" | 30×60 | 3Ø16 top; two lower rows 3Ø16 + 3Ø16; Ø8/15 |
| P13-GB-LT5M | "Less than 5m length … without concentrated load" | 30×40 | 3Ø14; 3Ø14 + 3Ø14; Ø8/15 |
| P13-GB-LT2_5M | "Less than 2.5m length" | 30×30 (AI transcription only) | 3Ø14; 3Ø14 + 3Ø14; stirrup drawn, no callout |
| P13-GB-EXTERIOR | "for exterior walls" | width 30, depth FOLLOW ARCH. | 3Ø16 top; 6Ø16 drawn as two rows of 3; 2Ø12/30cm sides; Ø8/15 |

**How the conditions are read:**
- **Length:** tested on two bases, clear span and support centreline. A length on 2.5 or 5.0 m (±1 mm) satisfies no literal condition and stays unresolved; no span is on a threshold.
- **Below 2.5 m:** both "Less than 2.5m" and "Less than 5m" hold literally. Both are kept as candidates, never collapsed (15 spans).
- **Exterior:** tested twice, by the V3 slab-zone outline and the R4 footprint outline. 19 spans get different answers from the two tests.

| DETAIL_APPLICABILITY_STATE | Spans | Meaning |
|---|---|---|
| PROJECT_GENERAL_DETAIL | 20 | both exterior tests agree: the "for exterior walls" section; architectural overlay (Q-R4-6) still pending |
| EXPLICIT_LENGTH_CONDITION | 16 | interior; the literal length condition is met on both bases |
| CANDIDATE_DETAIL | 23 | the exterior tests disagree (19) or the length basis changes the section (7, overlapping) |
| NO_APPLICABLE_DETAIL / SOURCE_CONFLICT | 0 | — |

## 5. Readiness (06) — no kg

### Ground beams (59 occurrences)

| Component | READY | READY_LOWER_BOUND | PROVISIONAL_ONLY | BLOCKED | NOT_APPLICABLE |
|---|---|---|---|---|---|
| TOP_MAIN / BOTTOM_ROW_1 / BOTTOM_ROW_2 | — | **46** | — | 13 | — |
| SIDE_BARS | — | — | — | 39 (depth FOLLOW ARCH. or candidates differ) | 20 |
| STIRRUP diameter / rate | 43 | — | — | 16 | — |
| STIRRUP_COUNT | — | 43 | — | 16 | — |
| STIRRUP_CORE_PATH | — | — | 12 | 47 | — |
| HOOK_1 / HOOK_2, END_TREATMENT, DEVELOPMENT_1 / 2 | — | — | — | 59 | — |
| END_ZONE_EXTRA, LAP (net) | — | — | — | — | 59 |

- **Occurrence status:** 46 READY_LOWER_BOUND, 13 BLOCKED_COMPONENT. No occurrence is READY or NO_DETAIL.
- **Why 13 are blocked:** the candidate details disagree on the bars, 3Ø14 versus 3Ø16, so exterior-versus-interior must be resolved first.
- **Bar-run lower bound:** the shorter of clear span and support centreline. Two spans whose column does not cut the full band are flagged.

### Straps (3 occurrences)

- **SB1 and SB3:** longitudinal bars READY_LOWER_BOUND (run ≥ clear concrete length).
- **SB2:** BLOCKED (SOURCE_CONFLICT).
- **All three:**
  - stirrup diameter / rate READY;
  - stirrup count READY_LOWER_BOUND;
  - stirrup core path BLOCKED (no topology);
  - hooks and development BLOCKED;
  - BOTTOM_ROW_2 NOT_APPLICABLE (one schedule total; no row is invented).
- SB2's identical stirrup values still never release, because the member is in conflict.

### Provenance

Every occurrence has a complete S5 provenance template (`S5_PROVENANCE_TEMPLATES.json`): the S4 contract fields plus:
- `GROUND_SYSTEM_OCCURRENCE_ID`
- `MEMBER_MARK`
- `START_NODE` / `END_NODE`
- `GEOMETRY_HANDLES`
- `DETAIL_ID`
- `DETAIL_APPLICABILITY_STATE`

**Release gating:**
- A CANDIDATE_DETAIL component releases only when it is identical in every candidate (`CANDIDATE_INVARIANT`).
- A SOURCE_CONFLICT never releases.
- `MAY_RELEASE` in 06 is the gate.

## Files

| File | Content |
|---|---|
| 01_GROUND_BEAM_GEOMETRY_CHANGELOG.csv | every old → new change with its cause |
| 02_GROUND_BEAM_NETWORK_SUMMARY.json | old / new counts, conservation, nodes, unpaired ledger, readiness tallies |
| 03_STRAP_OCCURRENCE_REGISTER.csv | strap occurrences, supports, clear / c/c / drawn lengths, schedule refs |
| 04_GROUND_BEAM_DETAIL_APPLICABILITY.csv | per span: bases, supports, exterior tests, candidates, state, why / why not |
| 05_STRAP_REBAR_SOURCE_REGISTER.csv | strap reinforcement source exhaustion |
| 06_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv | occurrence × component readiness (S5_STATUS, MAY_RELEASE) |
| 07_PRE_S5_ENGINEERING_QUESTIONS.md / 08_S5_SCOPE_RECOMMENDATION.md | questions / safe S5 scope |
| F3_PROVENANCE_CHECK.json, S5_PROVENANCE_TEMPLATES.json, INDEX.json | F3 check, templates, hashes |
