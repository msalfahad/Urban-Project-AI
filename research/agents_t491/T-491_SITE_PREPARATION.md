# T-491 Site clearance (B1-01) and preliminaries (B1-07) as quantities (Alsenan; method every villa)

Worker 1 (lane S), 2026-11-03, run session_01E6cPneFZD7cGaf9npp8GfK. Research piece, NOT wired: no engine module,
method version, route G, rule / knowledge / registry file or candidate line changed; no released quantity. No prices.
Drawings named by Drive folder "Alsenan chalet project" and title; entities by DXF handle; lengths and areas only.

Files: `site_preparation_v1.py` (SITE_PREPARATION_V1, stdlib), `ALSENAN_SITE_PREP_INPUT.json` (values / handles),
`t491_alsenan_check.py` -> `SITE_PREP_T491.csv`, `summary.json`, `T471_PROPOSAL_T491.json`; tests
`tests/t491_site_preparation/` (33 pass: 26 villa Q hand fixtures incl. adverse, 7 Alsenan pins).

## 1. Physical elements (ERS s.2.1) and rules

Owner 2026-11-02 17:20 notes (2) and (6), Q-21 C (EG kept apart from formation), T-357 R-PLOT-1. Site clearance is a
surface operation on existing ground over the worked area; formation and fill compaction (T-350) are separate m2 and
never summed with it. Preliminaries are temporary facilities and project items; counts come from a logistics plan,
pour sequence or contract, durations only from a programme. Proposed rules R-T491-FENCE-1, -CLR-1, -DUR-1, -PWR-1,
-ITEM-1: text in the module docstring (adoption = a new rule version, Lead / lane I).

## 2. Results, one row per component (`SITE_PREP_T491.csv`)

| Component | Family | Qty | Unit | Status | Source / missing input |
|---|---|---|---|---|---|
| Site clearance | B1-01 | 470.550 | m2 | DRAWING-CONFIRMED geometry; extent rule PROPOSED | plot 15.00 x 31.37 printed (ARCH p.1 / p.2, sanitary p.1 - p.3); scope owner 17:20 (6) |
| Formation / fill compaction | B1-02 / 03 | - | m2 | HELD here | owned by T-350 r3; reported apart |
| Hoarding gross boundary | B1-07 | 92.740 | lm | DRAWING-CONFIRMED | 2 x (15.00 + 31.37); DXF pieces by handle sum 15.000 / 31.370 / 15.000 / 31.370 |
| Hoarding fence net | B1-07 | HELD (at most 92.740) | lm | HELD | temporary gate count and widths (no site / logistics plan in the set) |
| Hoarding gates | B1-07 | HELD | nos | HELD | same |
| Guard cabin or tent | B1-07 | HELD | nos x months | HELD | count (logistics plan) x construction months (programme) |
| Water tanks | B1-07 | HELD | nos | HELD | logistics plan / contract |
| Water-tanker trips | B1-07 | HELD | trips | HELD | trips per week x weeks (programme) |
| Concrete pump, pours | B1-07 | HELD | pours | HELD | pour sequence: none printed (ST p.1, p.8 notes 1-24, p.9 notes 1-4, T-357 search) |
| Pour generator, days | B1-07 | HELD | days | HELD | same |
| Generator fuel / government connection | B1-07 | HELD (one of two) | item | HELD | project choice (contract / authority); both refused |
| Site and workers insurance | B1-07 | HELD | item | HELD | contract clause |
| Site handover (Municipality + office) | B1-07 | 1 | item | ASSUMED - OWNER-APPROVED | owner 17:20 (6), item without a contract condition |

## 3. Boundary re-measure (P7757.dxf ab54dd55, GF plan, this run)

- Second drawing, own read this run: ARCH p.1 GF area plan (Alsenan_Architectural_P7757_Pages_01-02, 110 dpi) prints
  STREET 15.00, SEA VIEW 15.00, NEIGHBOUR 31.37 on both long sides; its own chains close: 16.37 + 10.60 + 4.40 =
  31.37 along the neighbour side and 13.50 + 1.50 = 15.00 across.
- Street 15.000: 107 0.833 (L1) + 341 1.955 (L5, W 342-344) + 108 1.145 + 347 1.955 (W 348-34A) + 109 0.812 + 10F
  8.300 (L5). Lower neighbour 31.370: corner column 2F9D 0.370 + 85 10.230 + 0.200 + 86 / 105 1.200 + 9A 3.000 +
  0.200 + 8A 16.170. Sea 15.000: 8B 0.900 + 261 6.332 (W) + 8C 0.668 + 0.232 + 8D 5.168 + 8E 1.700. Upper neighbour
  31.370: 98 16.370 + 99 15.000 (house wall 13A on the boundary). Total 92.740 lm = printed sides.
- Permanent openings on the boundary (evidence only, NOT temporary gates): street access 2.500 (10A .. 10B, hidden
  110 overhead), two street glazed openings 1.955 each, sea door D120 1.000, sea glazed band 6.332.

## 4. Methods side by side

| Method | Clearance | Fence | Duration / count items |
|---|---|---|---|
| Owner manual (17:20 (6)) | site clearing m2, separate from formation compaction | lm from the plot boundary, gates by count | HELD with the formula until a programme exists |
| Drawing-derived (this task) | 470.550 m2 = plot inside the printed boundary | gross 92.740; net = gross - gates, HELD on gates | HELD, inputs named |
| Released V2.9 + route G / candidate V3.0.46 | no B1-01 / B1-07 line | none | none |
| Freelancer | no row (885 rows searched) | no row (his boundary-wall rows are permanent masonry) | no row |

Who is right: no freelancer row on any component: missing from both BOQs, no verdict (MISSING_BOTH). The engine
gains the components, quantified or HELD.

## 5. Findings

1. F-T491-1 SCOPE CHANGE: T-357 / the Lead ruling 2026-10-30 04:25 set C-B1-01 NOT_APPLICABLE (R-CLR-1, no printed
   scope). Owner 17:20 (6) now puts site clearance in scope for every villa: the next T-471 matrix version should set
   C-B1-01 APPLICABLE with R-T491-CLR-1 (extent = the plot unless a limit is printed); R-CLR-1 keeps refusing a
   convention extent (plot minus footprint, margins). Proposed in `T471_PROPOSAL_T491.json`, not written.
2. F-T491-2 the net fence cannot be released from the issued set: no site plan, logistics plan or hoarding detail
   (T-195 MISSING row 2). Upper bound 92.740 lm. A residual not settled by drawing: existing neighbour walls could
   replace hoarding on the two 31.37 sides; no survey shows them (UNKNOWN), so the owner method (boundary) stands.
3. F-T491-3 pump / generator pours: the candidate's concrete volumes by element exist, but a pour count is a
   construction-method decision; no pour sequence is printed. HELD, never derived from the number of levels.
4. No owner question: ERS 2.7 not met (every HELD input is a project document the contractor produces: programme,
   logistics plan, pour plan, contract; none is a drawing contradiction or missing safety-critical design).

## 6. Lessons register row (proposed)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-03 | B1-01 / B1-07 had no component rows: preliminaries were "item by contract" and clearance NOT_APPLICABLE, so the 10 Nov BOQ could not list them present or HELD | site items were judged only by printed drawing scope; owner company rules and project documents (programme, logistics, contract) were not separate inputs | one row per site component: quantity from drawings where they fix it (boundary lm, plot m2), HELD with formula and the named project document otherwise; durations never defaulted; temporary power exactly one source; gross fence never reported as net (any villa) | tests/t491_site_preparation (normal 20 x 30 plot 96 lm, L plot, mm, mirror / rotation; adverse no programme, value without source, both power sources, gates > boundary, open polygon, HELD with a quantity) | proposed |

## 7. For the Checker

1. ARCH p.1 / p.2 area plans: sides 15.00 / 31.37 / 15.00 / 31.37 -> 92.740 lm, 470.550 m2.
2. P7757.dxf: the handle sums of section 3 per side.
3. ST7757.pdf p.1, p.8, p.9: no pour sequence; the issued set: no site / logistics plan.

## 8. Not done / uncertain

- Net fence, gates and every duration / count item HELD on project documents; no default used.
- The clearance extent rule is PROPOSED; the quantity is not released until a rule version adopts it.
- Registry / T-471 matrix not edited (T-350 r3 holds the registry file).
