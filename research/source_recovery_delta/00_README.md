# Source recovery delta: S4 / S5 / S6 unresolved project-source exhaustion

**Round:** `SOURCE_RECOVERY_DELTA_S4_S5_S6` · **Policy:** `SOURCE_RECOVERY_DELTA_V1` · **Built by** `build_source_recovery_delta.py` (blind; byte-identical rebuild)

S4, S5 and S6 remain accepted and frozen.
- **No frozen file was changed.** Their freeze manifests are hash-checked at build time.
- **No kg was recalculated.**
- **S7 was not started.**

This round records the project engineer's statement and searches the issued plan set a second time, graphics first, for every unresolved or blocked S4 / S5 / S6 reinforcement item.

## 1. The engineer claim (`01_ENGINEER_PROJECT_CLAIM.json`)

`PROJECT_ENGINEER_CLAIM` v1, recorded 2026-10-08:

> "The project engineer has confirmed that the required construction / reinforcement information is contained within the issued construction plan set."

- **It authorises no assumption** (`authorises_assumptions: false`). It changes the workflow only:
  - OLD: not found → engineer required.
  - NEW: not found → `SOURCE_EXPECTED_NOT_LOCATED` → exhaust the issued plan set → only explicit source conflicts go back to the engineer.
- **F / F10 and the other known drawing conflicts** wait for the engineer's separate answer. They were not resolved by inference.

## 2. What was searched, and how

| Source (sha256) | Channel | New in this round |
|---|---|---|
| ST7757.dxf `9f9d1179…` (plans and schedules, pp.1-7 and 9-12) | All TEXT, MTEXT, ATTRIB, ATTDEF and DIMENSION entities in modelspace and the 420 block definitions; legacy-Arabic notes decoded with `engine.source.legacy_text`; block geometry; sheet frames | STR2 / str3 icon geometry and how each icon binds to a schedule row; SB2 rows against the sheet frame; CB typical dimensions measured against their printed factors |
| ST7757.pdf `74da1523…` (issued plot; details pp.13-16 exist only here) | **Vector strokes for each CAD layer**, read with pypdf content streams (`vector_pdf.py`): `S-REIN.D` reinforcement, leaders, bar dots. Bars are grouped into connected components by shared end points | Bar shapes, which leader touches which bar, link topology, and the leg ends at CB end supports |
| same, rendered from those strokes (kept outside the repo) | Visual reading of stroke text, with a tesseract cross-check (raw OCR strings are kept) | p.16 stair-beam callouts; p.15 planted-column callouts; p.14 "2 Ø16" |
| P7757.dxf `ab54dd55…` (architectural) | All TEXT entities | FOLLOW ARCH: only level marks exist, no floor build-up |

**The engine PDF stack was not touched.** PyMuPDF and `engine/pdf_vector_evidence` were not used. pypdf is a pure-Python, read-only reader. No reference quantity, external engine output or generic code value was read.

### Graphic rule (brief §6)

A graphic reading is `SOURCE_FOUND_DERIVED` only when all four conditions hold:
1. its target is unambiguous (a leader touches that bar);
2. its geometry binds (shared vertices, levels);
3. repeated examples agree;
4. no project source contradicts it.

The builder asserts every vector fact it uses and stops if one fails (`13_GRAPHIC_EVIDENCE.json`).

## 3. Results

| Stage | Items | FOUND_EXPLICIT | FOUND_DERIVED | CONFLICT | EXPECTED_NOT_LOCATED | PENDING_ENGINEER | Newly source-resolved |
|---|---|---|---|---|---|---|---|
| S4 | 14 | 1 | 3 | 0 | 9 | 1 | 3 (S4-03, S4-07, S4-12) |
| S5 | 18 | 0 | 3 | 3 | 12 | 0 | 3 (S5-01, S5-04, S5-18) |
| S6 | 25 | 2 | 6 | 3 | 14 | 0 | 5 (S6-02, S6-04, S6-05, S6-14, S6-15) |

`GENERIC_CODE_QA_ONLY` is used for nothing.

**What the item counts include:**
- **S4 (14):**
  - 10 items carried from the frozen unresolved register and questions;
  - S4-06, a brief §3 topic whose frozen state was NOT_APPLICABLE;
  - S4-12, S4-13 and S4-14, facets the frozen run had as VERIFIED or straight, re-examined because the new graphics bear on them.
- **S5 (18):** all from the frozen register and the questions Q1-Q10, with the strap links split out as S5-18.
- **S6 (25):**
  - 22 open items;
  - S6-12 and S6-24, already source-known;
  - the T/M guard (S6-25).

### New project evidence (all from the issued set)

1. **p.13 footing details, both variants (E-PDF-01).**
   - The bar labelled **"Long bars"** is one drawn **U**. Two up-legs share the bottom run's exact vertices and end in **45° hooks**.
   - **"Boxed bars."** is an **inverted U**: a top run with legs down to the bottom-bar level, and no hooks.
   - Short bars appear only as dots (seen in section).
2. **p.13 ground-beam sections (E-PDF-02).**
   - Each section draws **exactly one closed link** (2 legs) with a corner hook.
   - The >5 m, <5 m and exterior links each carry one label leader (Ø8/15cm).
   - **The <2.5 m (30x30) link has no label leader**, so its diameter and spacing are not printed.
   - The p.13 footing details show the **GB bars running unbroken through the column**.
3. **p.14 lift footing (E-PDF-03).**
   - Each **"2 Ø16"** leader ends on two bars, one pair at the top mesh level and one at the bottom mesh level, **inside the cut pit wall**. These are wall-base bars, not footing-side bars.
   - The second cut wall repeats the same 2 + 2 bars.
   - On plan, the pit is a closed square of four 20 cm walls, 1.80 m inside and 2.20 m outside (E-DXF-05).
4. **CB typical figures, pp.11-12 (E-PDF-04).**
   - In all three figures, the end-support top bar turns down in a 90° leg whose foot ends **at the bottom-bar level**.
   - The figures are N.T.S. (E-DXF-06): drawn 0.2593 Ln for "0.22 Ln", 0.0918 L for "0.15L", and 697 mm for "7.5cm". So no label question can be settled by scale.
5. **Stirrup icons (E-DXF-03).**
   - In the REMARKS column, **STR2** is an outer link plus one inner closed link of full height, each with a hook-tick pair, giving **4 legs**. It appears on B17, B19-B26, SB1 and SB3.
   - **str3** is an outer link plus two inner links, giving 6 legs, on SB2.
   - The same symbol is the project's labelled link symbol on p.13. The p.15 typical beam section draws a single closed link with no inner link (E-PDF-05).
   - The strap rows carry the same icons, so SB1 and SB3 get 4 legs (S5-18). SB2 stays blocked by its row conflict.
6. **WITH STAIR (E-DXF-07, E-PDF-06).**
   - Every "(With Stair)" tag sits on a B3 tag.
   - The p.16 "TYPICAL DETAIL OF STAIR BEAM" callouts (2Ø12, 4Ø16, 6Ø8/m, depth AS PER SCH.) **equal the B3 schedule row**. The detail adds no bars; it draws the beam cranked.
7. **Planted column, p.15 (E-PDF-06).**
   - The detail adds extras only: 4Ø16 hooked rows extending DEPTH past each column face, and stirrups at 10 cm under the column.
   - One "4Ø16" leader touches both rows, so the split between rows is not stated.
8. **SB2 (E-DXF-04).**
   - Only row 2ABA (100x50, 20Ø18 / 10Ø16) is on the issued schedule sheet (PDF p.10).
   - Row 1FBB (80x50) lies below sheet frame 1B2D in model space.
   - The conflict is kept, because the issued sheet does not void 1FBB explicitly. A one-line confirmation is asked (PEC-02).

### An interpretation withdrawn

S4 had read the single-layer footing bottom bars as straight, from the p.13 detail ("SOURCE_DERIVED_HIGH_CONFIDENCE"), and released 20 BOTTOM_LONG and 20 BOTTOM_SHORT components as VERIFIED.
- The vector reading shows the long bars drawn with legs and hooks (S4-12).
- The short bars' end shape is not drawn at all (S4-13).
- The straight core stays a valid lower bound. S4.1 candidates C01-C03 propose LOWER_BOUND, with the end facets named as missing. No kg was changed here.

## 4. Files

| File | Content |
|---|---|
| `01_ENGINEER_PROJECT_CLAIM.json` | versioned claim, `authorises_assumptions: false` |
| `02_UNRESOLVED_MASTER_REGISTER.csv` | 57 items, one terminal state each, linked to their frozen rows |
| `03_UNRESOLVED_SOURCE_CONNECTION_GRAPH.csv` | OCCURRENCE / COMPONENT → SCHEDULE_CELL → DETAIL_REFERENCE → TYPICAL_DETAIL → GENERAL_NOTE → ARCHITECTURAL_REFERENCE, FOUND / NOT_FOUND per hop |
| `04/05/06_S*_SOURCE_RECOVERY.csv` | per stage: sources searched, evidence ids, finding, terminal state, what is still missing |
| `07/08/09_S*_1_CANDIDATES.csv` | state changes for S4.1 / S5.1 / S6.1. Columns: FROZEN_BASELINE, OLD_STATE, NEW_SOURCE, NEW_SOURCE_HANDLES, NEW_AUTHORITY, PROPOSED_NEW_STATE, EXPECTED_COMPONENTS_UNLOCKED. No kg; never VERIFIED |
| `10_PENDING_ENGINEER_CONFLICTS.csv` | 13 rows: F / F10 (pending clarification) and 12 genuine two-source conflicts |
| `11_SOURCE_EXPECTED_NOT_LOCATED.csv` | 35 items, with where they were searched and the precise ask |
| `12_RECOMMENDATION.md` | next step |
| `13_GRAPHIC_EVIDENCE.json` | every DXF and PDF-vector fact, with handles and coordinates |
| `SRD_SUMMARY.json` | counts, frozen baselines (manifest sha + engine stamp), flags `kg_recalculated: false`, `s7_started: false` |
| `vector_pdf.py` | pypdf-only vector reader (no rendering, no OCR, writes nothing) |

Rebuild: `python3 -I research/source_recovery_delta/build_source_recovery_delta.py`.
