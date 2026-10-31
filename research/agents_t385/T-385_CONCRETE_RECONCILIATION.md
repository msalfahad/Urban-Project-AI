# T-385 Concrete reconciliation: candidate V3.0.29 vs the freelancer, family by family (research only)

Candidate of record ARCH_TAKEOFF_V3.0.29 (own run from the Drive copies P7757_DXF_COMPRESSED.zip ab54dd55 and
'ST7757 dxf.dxf' 9f9d1179: V3_0_29_BOQ_LINES.json 6b5dc44f / csv 09b3493b = the Checker's reproduction of 2026-10-30 23:40).
Contractual view: the 11 concrete lines under the three V3.0.29 downgrade records (DG-3521554d2fd011b9 footing blinding,
DG-6dd9f1caba1ca77d boundary lower band, DG-a31a0d7e9dd564ad 9 ground-beam D-34 lines) are HELD, their figures audit only.
No quantity, line, state or released cell is changed by this package.

## Where the freelancer's numbers are

The freelancer workbook (Drive: Urban BOQ private data / Alsenan chalet project / the concrete + rebar workbook) is the
owner's private data and this repository is public (CLAUDE.md "Private client drawings"). Its row values therefore stay
in `.work/private/t385/` (input `ALSENAN_T385_INPUT.json`, outputs `RECON_T385.csv`, `FAMILIES_T385.csv`,
`summary_t385.json`); a run that tried to copy that input into this folder was refused by the session check, and the
builder now refuses an `--out` inside the repository. This file and the board carry ENGINE-side figures, line counts,
cause classes and verdict proposals only. The acceptance's freelancer-m3 column (a) is met in the private table; the
Checker rebuilds it from Drive with:

    python3 -I research/agents_t385/t385_extract.py --lines <run>/V3_0_29_BOQ_LINES.json \
        --downgrades <board>/docs/agents/verdicts/V3.0.29/DOWNGRADES.json --freelancer <private>/<workbook>.xlsx \
        --out <checkout>/.work/private/t385/ALSENAN_T385_INPUT.json
    python3 -I research/agents_t385/t385_alsenan.py --out <checkout>/.work/private/t385/out

## Method (t385_rules.py, R-T385-1 .. 5; every villa)

Family = one freelancer summary row keyed by tests/alsenan/T001C_KEY_MAP.json (sheet 1 rows 15, 17 .. 23). Each family is
split into components (one physical element or one population of identical elements) bound to the candidate line ids
that carry it and to the freelancer sheet rows that carry it; every one of the 525 STR.CONC lines is bound exactly once
and every freelancer element row exactly once. Contribution = engine valued part - freelancer part. A HELD engine part
adds 0 to the engine side, is reported with its bound and is never AGREE; a wholly held component is HELD whatever the
freelancer figure. The contributions sum to the family residual within 0.001 m3 or the remainder is printed as
UNEXPLAINED. A freelancer sub-total that differs from his own rows is its own cause (FREELANCER_ARITHMETIC). A cause
stated as a ratio, percentage or scaling is refused.

## Result (engine side)

All 9 families close (unexplained 0.000 m3 in each). 47 components: AGREE 15, ENGINE_RIGHT 10, HELD 11, UNRESOLVED 11,
FREELANCER_RIGHT 0, RULE_DIFFERENCE 0. Engine valued (contractual) per family, m3: blinding 0.000 (4 held), footings
67.6945 (4 held), ground 44.8661 (22 held), columns + necks 28.2155 (55 held), beams 66.3179 (27 held), slabs 60.2802
(0 held), stairs + domes 10.4502 (6 held), pool 7.2023 (1 held); parapet RC 4 held lines, no key, no freelancer row.

UNRESOLVED means: the element is named and bound, its contribution is stated in the private table, but it is NOT yet
traced to a single physical cause (the freelancer's row is a lump over many runs, or the engine part mixes valued and
held runs). Those 11 components are the next work, not agreements.

| Component | Family | Engine lines | Engine valued m3 | Held lines (of them unbounded) | Held: low of the bounded lines .. high (open when a held line has no bound) | Cause class | Verdict proposal |
|---|---|---|---|---|---|---|---|
| BL-1 | BLINDING | 4 | 0.000000 | 4 (1) | 5.879177 .. open | HELD_ITEM | HELD |
| FT-F | FOOTING | 4 | 0.864000 | 0 (0) |  | AGREE | AGREE |
| FT-F2 | FOOTING | 2 | 2.261000 | 0 (0) |  | AGREE | AGREE |
| FT-F3 | FOOTING | 2 | 1.344000 | 0 (0) |  | COUNT | ENGINE_RIGHT |
| FT-F4 | FOOTING | 2 | 3.520000 | 0 (0) |  | AGREE | AGREE |
| FT-F5 | FOOTING | 2 | 4.032000 | 0 (0) |  | AGREE | AGREE |
| FT-F6 | FOOTING | 1 | 2.860000 | 0 (0) |  | AGREE | AGREE |
| FT-F8 | FOOTING | 1 | 7.200000 | 0 (0) |  | AGREE | AGREE |
| FT-F9 | FOOTING | 1 | 5.049000 | 0 (0) |  | AGREE | AGREE |
| FT-F10 | FOOTING | 1 | 0.000000 | 1 (0) | 2.176 .. 2.275 | HELD_ITEM | HELD |
| FT-F11 | FOOTING | 1 | 2.625000 | 0 (0) |  | AGREE | AGREE |
| FT-F12 | FOOTING | 1 | 9.856000 | 0 (0) |  | AGREE | AGREE |
| FT-F13 | FOOTING | 1 | 5.160000 | 0 (0) |  | AGREE | AGREE |
| FT-F14 | FOOTING | 1 | 6.270000 | 0 (0) |  | AGREE | AGREE |
| FT-F15 | FOOTING | 1 | 0.720000 | 0 (0) |  | AGREE | AGREE |
| FT-FF | FOOTING | 1 | 11.385000 | 0 (0) |  | AGREE | AGREE |
| FT-FN | FOOTING | 4 | 1.158000 | 0 (0) |  | DIMENSION | ENGINE_RIGHT |
| ST-SB1 | FOOTING | 1 | 1.592500 | 0 (0) |  | AGREE | AGREE |
| ST-SB1-IN | FOOTING | 1 | 0.000000 | 1 (0) | 0.0 .. 0.385 | HELD_ITEM | HELD |
| ST-SB2 | FOOTING | 1 | 1.146400 | 0 (0) |  | DIMENSION | ENGINE_RIGHT |
| ST-SB3 | FOOTING | 1 | 0.651600 | 0 (0) |  | DIMENSION | ENGINE_RIGHT |
| ST-SB3-IN | FOOTING | 1 | 0.000000 | 1 (0) | 0.0295 .. 0.1181 | HELD_ITEM | HELD |
| ST-NA | FOOTING | 5 | 0.000000 | 0 (0) |  | SCOPE | AGREE |
| BW-BAND | FOOTING | 1 | 0.000000 | 1 (1) | - .. open | WRONG_BASIS | HELD |
| GS-SLAB | GROUND | 25 | 17.240684 | 1 (0) | 3.929788 .. 3.929788 | SCOPE | UNRESOLVED |
| GB-BOUNDARY | GROUND | 1 | 0.000000 | 1 (1) | - .. open | HELD_ITEM | HELD |
| GB-MAIN | GROUND | 58 | 27.625386 | 20 (20) | - .. open | HELD_ITEM | UNRESOLVED |
| CL-LIFT | COLUMN | 0 | 0.000000 | 0 (0) |  | SCOPE | UNRESOLVED |
| CL-NECK | COLUMN | 36 | 0.000000 | 36 (1) | 3.075 .. open | HELD_ITEM | HELD |
| CL-GF | COLUMN | 30 | 17.967500 | 5 (5) | - .. open | DIMENSION | UNRESOLVED |
| CL-1F | COLUMN | 23 | 10.248000 | 0 (0) |  | DIMENSION | UNRESOLVED |
| CL-2F | COLUMN | 14 | 0.000000 | 9 (9) | - .. open | HELD_ITEM | HELD |
| CL-UNDRAWN | COLUMN | 5 | 0.000000 | 5 (2) | 1.134 .. open | HELD_ITEM | HELD |
| BM-GF | BEAM | 104 | 39.329077 | 10 (1) | 4.867479 .. open | HELD_ITEM | UNRESOLVED |
| BM-1F | BEAM | 66 | 22.690302 | 12 (3) | 2.94335 .. open | HELD_ITEM | UNRESOLVED |
| BM-2F | BEAM | 21 | 4.298500 | 5 (1) | 0.562 .. open | HELD_ITEM | UNRESOLVED |
| BM-ARITH | BEAM | 0 | 0.000000 | 0 (0) |  | FREELANCER_ARITHMETIC | ENGINE_RIGHT |
| SL-GF | SLAB | 40 | 33.069524 | 0 (0) |  | DIMENSION | ENGINE_RIGHT |
| SL-1F | SLAB | 26 | 19.756334 | 0 (0) |  | DIMENSION | ENGINE_RIGHT |
| SL-2F | SLAB | 9 | 7.454300 | 0 (0) |  | DIMENSION | ENGINE_RIGHT |
| SD-DOME | STAIR_DOME | 5 | 5.081362 | 1 (1) | - .. open | HELD_ITEM | UNRESOLVED |
| SD-STAIR | STAIR_DOME | 12 | 5.368881 | 5 (5) | - .. open | HELD_ITEM | UNRESOLVED |
| PL-BASE | POOL | 1 | 4.374226 | 0 (0) |  | DIMENSION | ENGINE_RIGHT |
| PL-WALLS | POOL | 1 | 2.828071 | 0 (0) |  | DEPTH | ENGINE_RIGHT |
| PL-STEPS | POOL | 1 | 0.000000 | 1 (1) | - .. open | HELD_ITEM | HELD |
| PL-PUMP | POOL | 2 | 0.000000 | 0 (0) |  | SCOPE | UNRESOLVED |
| PA-RC | UNKEYED.PARAPET | 4 | 0.000000 | 4 (4) | - .. open | HELD_ITEM | HELD |

## Findings with a physical cause (engine figures; the freelancer side as a method class)

- F3: the structural DXF prints the label C3/F3 twice (own count this run); the candidate carries two F3 footings
  2 x 1.40 x 1.60 x 0.30 = 1.344 m3; the freelancer counts one. ENGINE_RIGHT (COUNT).
- FN: one of the four FN outlines is clipped where it meets a neighbouring footing (0.258 instead of 0.300 m3): the
  overlap is owned once; the freelancer counts four full FN. ENGINE_RIGHT (no double count).
- Straps SB2 / SB3: drawn face-to-face axes 2.2927 / 3.258 m against rounded axes. ENGINE_RIGHT (DIMENSION, < 0.004 m3).
- Slabs GF / 1F / 2F: the candidate's 62-panel net (Checker WHOLE-LINE VERIFIED, V2-c5004423d32f2106) against areas
  rounded to the m2. ENGINE_RIGHT (DIMENSION).
- Pool base: drawn D outline 3.50 x 1.75 + pi 1.75^2 / 2 = 10.935564 m2 x 0.40 = 4.374226 m3. ENGINE_RIGHT.
- Pool walls: wall band 2.356726 m2 x 1.20 (rim to base top, the wall foot measured once in the base) = 2.828071 m3;
  the freelancer's wall height runs from the base bottom, so the base thickness is counted again in the walls.
  ENGINE_RIGHT (DEPTH).
- Beams: the freelancer's printed 1F beam sub-total leaves one of his own 1F rows out, so his family total is below the
  sum of his own rows by that row. FREELANCER_ARITHMETIC (the m3 in the private table).
- Blinding: the engine measures plain concrete under members (ST p.13 / p.14; all four lines HELD in the contractual
  view); the freelancer measures one plain layer over a whole rectangle, a scope no drawing prints. Proposed
  RULE_DIFFERENCE once the engine side is released; HELD now.
- HELD by name (never 0, never agreement): F10 + F (Q-31 C), SB1 / SB3 parts inside footings, boundary lower band
  (DG-6dd9f1caba1ca77d; T-356 range 5.6392 .. 11.0328), boundary-wall ground beam (M4), 36 necks (Q-21 C formation),
  2F columns (D-39), 5 undrawn columns (D-65), DOME-3 (Q-27 A, no detail), pool steps (not drawn), parapet RC (T-319).

## Proposed lessons-register row (ERS section 7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-31 | No per-family concrete statement existed after the V3.0.x candidate moved concrete; a family comparison of two totals hid held parts as apparent shortfalls and his own sub-total slip as an engine gap (T-385) | families were compared total vs total; held lines and the freelancer's row arithmetic were never separated from the physical differences | a family residual is split component by component, each bound to line ids and freelancer rows exactly once; a held part is a named item, never agreement; a freelancer sub-total that differs from his rows is its own cause; a ratio never closes a residual; the freelancer's values stay in the private table (scope: every villa, every trade comparison; provenance T-385) | tests/t385_concrete_recon (held as AGREE refused, ratio refused, line twice refused, downgraded line held, unexplained remainder printed) | PROPOSED |
