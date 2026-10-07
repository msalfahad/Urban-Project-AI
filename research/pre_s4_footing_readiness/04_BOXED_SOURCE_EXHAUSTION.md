# 04 BOXED: source exhaustion

**Terminal classification: `UNRESOLVED`.**
- The component itself (a boxed bar on single-layer isolated footings) is `SOURCE_EXPLICIT`.
- Its quantity semantics (what `3+4` counts, diameter, shape dimensions, length) are stated nowhere in the project set.
- One project pattern exists, the second number rises with footing length L. It is `PROJECT_PATTERN_ONLY` and diagnostic; it is not promoted.
- **S4 consequence:** the BOXED component is `BLOCKED_UNQUANTIFIED` on 12 footing types (11 printed values + FN's empty cell). Those footings release as `REBAR_LOWER_BOUND`; S4 still computes every other component.

No meaning has been assigned to `+`. No generic engineering convention is used as a project fact.

## 1. Sources searched

| Source | How | What was found |
|---|---|---|
| ST7757.dxf (sha `9f9d1179…`), every TEXT / MTEXT / ATTRIB in every layout and every block definition | regex `^\d+\+\d*$`, `box`, `cage` | header TEXT `1C53` "BOXED"; 11 FT `BOXED` ATTRIBs; the FT block ATTDEF `BOXED` default `3+-`. Nothing else in the drawing |
| Schedule of Footings grid (S-LINE.SCH lines + ATTRIB positions) | `engine.source.schedule_table.read` (COMPLETE, 26 bands, 0 unplaced) | the layout in §2 |
| FT / FTB block definitions | ATTDEF / TEXT list | FT: `%%C` glyph before SH-D and LO-D, **none before BOXED**; ATTDEF `BOXED` default `3+-`. FTB: `BOXED-T` default `TOP`, `BOXED-B` default `BOT` |
| Foundation plan (DXF texts inside every footing outline, frame-local) | search for bar / boxed / starter / dowel text | only footing tags and column marks; **no reinforcement text on any footing** |
| ST7757.pdf (sha `74da1523…`) p.8 general notes | rendered page + R4 OCR crops (notes 9, 18-22) | notes 1-24: cover (22), development length (9), other topics. **No note names boxed bars** |
| p.9 Schedules | rendered page | same table as the DXF; same values; REMARKS: section symbols on F12 / F13 / F14 / FF, and "lift footing" on FF |
| p.13 Details (1) | R4 crops `P13_FOOTING_TYPICAL` (`8b189ee3…`), `P13_FOOTING_DEEP` (`76d184df…`) + rendered page | both isolated-footing details label **"Boxed bars."**; see §3 |
| p.14 Details (2) | R4 crop `P14_LIFT_FOOTING` + rendered page | lift footing (FF): closed perimeter bar, "AS PER SCH.", two "2 Ø16" labels; no boxed value |
| pp.1-7, 10-12 (plans, DXF-derived) | DXF text search above | nothing |
| pp.15-16 Details (3) / (4) | rendered pages | columns, slabs, stairs, beams; nothing on footings |

The PDF pages were rendered read-only for reading in this round. Nothing was written to the PDF stack (see 00 §PyMuPDF).

## 2. The schedule layout as evidence (§8)

The table was read by drawn position, not by attribute tag. Header leaves, left to right:

```
TYPE OF FOOT. | FOOTING SIZE (cm): L | W | H | REINFORCEMENT: SHORT BARS | LONG BARS | BOXED | REMARKS
```

- **BOXED is its own top-level column.**
  - It is not a sub-column of REINFORCEMENT. The REINFORCEMENT group rule (`1C37`, y = 6727) stops at the BOXED double line (x = 148375).
  - BOXED is separated from LONG BARS and REMARKS by double rules, like the other group boundaries.
- **No diameter glyph.**
  - The block prints `%%C` (Ø) before every SHORT / LONG diameter cell.
  - The BOXED cell has no glyph and no second cell, so its value is not written as a count + diameter pair.
- **The `3` is part of the template.**
  - The FT ATTDEF default is `3+-`: the drafter's template pre-prints `3+`, and only the second number is filled per row.
  - All 11 values keep `3`.
- **FTB rows reuse the column.**
  - In the five two-layer footings (F8, F12, F13, F14, FF), the BOXED column holds the sub-row labels `TOP` / `BOT` (FTB ATTDEF defaults).
  - So the column carries no boxed value for two-layer footings.
  - FF has no sub-row rule in the DXF; its labels align with their bar cells on the same text line (header-binding check, `PRE_S4_SUMMARY.json`).
- **FN's cell is empty.** The `3+-` default was cleared for FN only.
- **Neighbour cells.**
  - Left: LONG BARS (`n | dia`).
  - Right: REMARKS, which is empty for every FT row. The only remarks are the FTB section symbols and FF's "lift footing".
- **No grouping rule ties BOXED values together.** There is no merged BOXED cell across rows and no boxed border grouping rows; each row has its own value.

Header binding (FT-04, run on the real table): 22 / 22 schedule (sub-)rows bind by drawn header. The tag → header map is `W → L`, `H → W`, `DEPHT → H`, `BOXED → BOXED`.

## 3. The detail drawings

**p.13 "TYP. DETAIL OF ISOLATED FOOTING."**, plus the deep-footing variant for a level difference > 2.5 m:
- **Shape:** one bar runs under the footing top face and down both side faces to the bottom-bar level. Separate vertical legs carry 45° hooks at the top corners. The leader "Boxed bars." points to the top run.
- **Bottom bars:** "Long bars" and "Short bars", drawn straight between the side legs.
- **Column starters:** foot ≥ 30 cm, max 10 cm above the mesh, projection 40 Ø.
- **Not printed:** count, diameter, spacing, leg length and hook length of the boxed bar.
- **Scope:** the title names no footing type, and the detail is a single elevation (one bar profile).

**p.14 lift footing (FF, two-layer):** a closed perimeter bar with top and bottom bars "AS PER SCH." and two "2 Ø16" labels. There is no BOXED value; this is the two-layer case.

## 4. Occurrences (03_BOXED_OCCURRENCES.csv)

| Mark | Value | L × W × D (cm) | Plan occ. | Bottom short / long | Status |
|---|---|---|---|---|---|
| F | 3+4 | 90 × 80 × 30 | 4 | 8Ø12 / 7Ø12 | UNRESOLVED |
| F2 | 3+4 | 190 × 170 × 35 | 2 | 13Ø12 / 13Ø12 | UNRESOLVED |
| F3 | 3+4 | 160 × 140 × 30 | 2 | 8Ø12 / 8Ø12 | UNRESOLVED |
| F4 | 3+4 | 220 × 200 × 40 | 2 | 18Ø12 / 17Ø12 | UNRESOLVED |
| F5 | 3+4 | 240 × 210 × 40 | 2 | 22Ø12 / 20Ø12 | UNRESOLVED |
| F15 | 3+4 | 180 × 100 × 40 | 1 | 15Ø12 / 8Ø12 | UNRESOLVED |
| F6 | 3+5 | 260 × 220 × 50 | 1 | 24Ø12 / 22Ø12 | UNRESOLVED |
| F10 | 3+5 | 280 × 140 × 50 | 0 (+ F / F10 conflict candidate) | 20Ø14 / 10Ø14 | UNRESOLVED |
| F7 | 3+6 | 300 × 250 × 50 | 0 | 24Ø14 / 21Ø14 | UNRESOLVED |
| F9 | 3+8 | 340 × 270 × 55 | 1 | 28Ø14 / 24Ø14 | UNRESOLVED |
| F11 | 3+8 | 350 × 150 × 50 | 1 | 32Ø14 / 14Ø14 | UNRESOLVED |
| FN | (empty) | 100 × 100 × 30 | 4 | 8Ø12 / 8Ø12 | UNRESOLVED (empty cell) |
| F8, F12, F13, F14, FF | TOP / BOT | (two-layer) | 1 each | per metre | not a boxed value (layer label) |

A value repeats only inside the schedule: `3+4` × 6, `3+5` × 2, `3+8` × 2, `3+6` × 1. It does not appear on any other sheet.

## 5. Cross-occurrence consistency (§9, diagnostic only)

Spearman ρ of the second number `n` against:

| L | D | bar Ø | short count | area | long count | W |
|---|---|---|---|---|---|---|
| 0.91 | 0.89 | 0.89 | 0.87 | 0.79 | 0.59 | 0.52 |

- **Monotone non-decreasing in L only.** `n = 4` for L 90-240, `5` for 260-280, `6` for 300, `8` for 340-350.
- **Not monotone in W or D.** F11 (W 150) has 8, while F7 (W 250) has 6.
- **The leading `3` never changes**, for W from 80 to 270 cm.
- **No relation to column count, position or diameter.**
  - F4 supports two columns and has `3+4`.
  - Edge, corner and internal footings all carry `3+4`.
  - D, Ø and bar counts correlate with `n` only through L.
- **Straps:** S1 records three strap beams but no footing link, so this was not tested.
- Correlation is not authority, and none of this becomes a rule.

A related check that **is** source-derived concerns the SHORT / LONG direction, which S4 needs.
- Spacing = (distribution − 2 × 7 cm cover) / (count − 1).
- Reading 1: SHORT bars are distributed along L and LONG bars along W. This gives near-equal spacing both ways on every FT type, for example F11 10.8 / 10.5 cm and F10 14.0 / 14.0 cm.
- Reading 2 (reversed) gives F11 4.4 / 25.8 cm and F10 6.6 / 29.6 cm.
- So "SHORT bars span W, are counted along L" is `SOURCE_DERIVED_HIGH_CONFIDENCE`. It rests on the printed counts plus header position, not on a convention.

## 6. Possible semantics (`GENERIC_HYPOTHESIS` only; never a project fact)

| Id | Hypothesis | For | Against |
|---|---|---|---|
| H1 | 3 bars one way + n bars the other way | two numbers; n rises with L | the 3 does not change with W from 80 to 270 cm; the detail shows one profile, not two directions |
| H2 | 3 boxed bars + n other bars on the same cage (e.g. side / face bars) | fixed `3+` in the template | no second bar type is drawn or labelled |
| H3 | 3 bars of Ø n mm | — | no Ø glyph; Ø4 / Ø5 / Ø6 bars are not used anywhere in the set (minimum Ø8) |
| H4 | n is a spacing or per-metre rate | — | no `/m` or `cm`; a per-metre `n` rising with L contradicts a rate |
| H5 | 3 top bars + n side bars per face | the detail shows top and side runs | not stated; side-bar count rising with L but not with D contradicts face bars |

None of these is supported by a project statement. Picking one would be inventing the quantity.

## 7. FN, the empty cell

- **For "no boxed bars":** the drafter actively cleared the `3+-` default.
- **Against:**
  - the p.13 detail applies to isolated footings with no type restriction;
  - F (90 × 80 × 30), which is smaller than FN (100 × 100 × 30), carries `3+4`;
  - FN supports the CN columns, which stop at the foundation (column schedule), but nothing states that this removes boxed bars.
- **Classification:** `UNRESOLVED (EMPTY CELL)`.
- **Change from R3:** R3 treated the empty cell as NOT_REQUIRED and marked FN `VERIFIED_COMPLETE`. Under the S4 rule, an empty cell is not source-explicit. FN therefore becomes `REBAR_LOWER_BOUND` with BOXED `BLOCKED_UNQUANTIFIED`, until the same owner answer covers it.

## 8. Decision and what would change it

| Class | Applies to | S4 |
|---|---|---|
| `SOURCE_EXPLICIT` | existence of a boxed bar on single-layer isolated footings (p.13, header) | the component is listed on every FT occurrence |
| `UNRESOLVED` | the meaning of `3+n`, diameter, shape dimensions, length; FN's empty cell | `BLOCKED_UNQUANTIFIED`; footing `REBAR_LOWER_BOUND` |
| `PROJECT_PATTERN_ONLY` | n rising with L | diagnostic; never a rule |
| `GENERIC_HYPOTHESIS` | H1-H5 | recorded only |
| `SOURCE_DERIVED_HIGH_CONFIDENCE` | SHORT / LONG bar direction | S4 may use it |

What would move BOXED to `SOURCE_EXPLICIT`: a written answer from the designer or owner to Q-R3-6 (S2 consultant question "What does the schedule field BOXED mean: bar count, bar size, shape and position?"), or a revised schedule or detail.

The answer must state:
- what each number counts;
- the diameter;
- the bar shape and leg / hook lengths, or a rule for them;
- whether FN has boxed bars.

Only then may S4 compute the component (`footing_rebar_guard.boxed_part` refuses to placeholder quantifiable semantics).
