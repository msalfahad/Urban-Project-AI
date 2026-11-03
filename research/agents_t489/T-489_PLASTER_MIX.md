# T-489: plaster / render / spatter MIX as a documented estimate (beside candidate V3.0.45, not in it)

Worker 2, 2026-11-03. New opt-in table `engine/source/plaster_materials_table_v2.py` (PLASTER_MATERIALS_TABLE_V2,
UNWIRED_PRODUCER, reads V1 rows; V1 untouched) + reader `t489_plaster_mix.py` + `out/` + `tests/t489_plaster_mix/`.
No candidate, released (V2.9 + route G), rule, knowledge or registry file changed; no line moves. Inputs: the T-454
reader on its sha256-pinned inputs (line index V3.0.45 16920d3c, T-349 binding). Rebuild:
`python3 -I research/agents_t489/t489_plaster_mix.py` (byte-identical; tested).

## Physical element (ERS s.2.1)
Per coat, a cement : sand mortar placed wet on the wall: (a) two-coat wall plaster (first coat + finishing coat), (b) the
tiler's levelling render on wet walls, (c) the plasterer's spatter (bond) coat. Installed quantity = mortar m3 (V1:
area x thickness); procurement = cement bags + sand m3 from the ratio by volume and a dry-volume conversion. Kept
apart: physical area (candidate line), installed mortar (V1), materials (V2), waste / purchase factor (none sourced,
not applied), water (HELD).

## Source search (rule hierarchy levels 1-4, every listed source attempted in full)
| level / source | result |
|---|---|
| 1 project drawings / spec | no mix printed (T-080, T-329, T-335, T-454) |
| 2 owner project decision | none (Q-79 withdrawn, not answered) |
| 3 company rulebook 1.0.0 | UPC-CEMENT-LAYERS-METHOD-001 mix null |
| 4 Kuwait General Specification 1990 (Drive: Engineering Sources / 01 Kuwait References, title 'المواصفات العامة للمباني والأشغال الهندسية - الكويت 1990') | NOT READABLE. download_file_content REFUSED: 'File too large for download, over limit of 10 MB' (file 11,809,903 bytes). The text index (search snippet, as read_file_content) stops at 97,008 characters, end of chapter 02230. Its contents list shows the plastering chapter as 09200 'أعمال المساح' (section 9 Finishes), past the cut. The Lead's note 'can be downloaded whole' does not hold for this file. |
| 4 KSE 'Bayt Al-Omr' 2023 | thicknesses only (items 57 / 60 / 62 / 75; T-454) |
| 4 QCS 2014 (86.9 MB), Saudi Building Code 2018 (11.3 MB), Al-Jund 'Finishes' (79.9 MB) | over the 10 MB limit, not readable |
| 4 other Drive references under the limit | Drive full-text search (plaster / render / spatter / mortar terms, Arabic and English): no reference with a plaster mix; a QS-course price sheet on Drive has rates only (no mix) |
| freelancer workbooks / another project's takeoff | not used for a mix (not an engineering reference; ERS s.3) |

Result: no readable source prints any coat's ratio. Every ratio HELD with the missing source named (MIX_REFERENCE,
MIX_SEARCH in the module), never 0. The 1:4 (Q-78 blocks) and 1:3 (Q-53 stair bed) ratios are refused by code.

## Method (owner-approved conversion, ratio as input)
Per 1 m3 of wet placed coat, ratio 1:n by volume, owner Q-53 C convention (dry factor 1.33, cement 1,440 kg/m3,
50 kg bag; conversion only, 'not universal constants'): cement m3 = 1.33/(1+n), bags = x 1440 / 50, sand m3 = 1.33 n/(1+n).
| ratio | cement m3 | cement kg | bags / m3 | sand m3 / m3 |
|---|---|---|---|---|
| 1:3 | 0.3325 | 478.80 | 9.5760 | 0.9975 |
| 1:4 | 0.2660 | 383.04 | 7.6608 | 1.0640 |
| 1:5 | 0.2217 | 319.20 | 6.3840 | 1.1083 |
Yield per m2 = thickness x per-m3 figure (e.g. 2.0 cm plaster at 1:4: 0.153 bags + 0.0213 m3 sand per m2).

## Status mapping (F-C-T454-1)
'ESTIMATED-NET' is a provenance label; each V2 figure carries `s5_status` = weakest input (area, thickness, ratio,
conversion): level-4 estimate or AT_LEAST bound -> s.5 HELD (WORKFLOW_CONTROLS s.4: no approved fallback, no drawing
evidence -> HELD, estimate beside); owner level 2 / 3 input -> ASSUMED — OWNER-APPROVED; all level 1 -> DRAWING-
CONFIRMED. VERIFIED is never set by the table.

## Result on V3.0.45 (unwired; no quantity released)
| coat | area m2 | mortar m3 | cement / sand | sensitivity bags 1:3 / 1:4 / 1:5 (NOT A QUANTITY) | sand m3 1:3 / 1:4 / 1:5 |
|---|---|---|---|---|---|
| dry wall plaster (25 lines) | 236.3481 | 4.726962 (thickness level 4) | HELD (no mix) | 45.27 / 36.21 / 30.18 | 4.72 / 5.03 / 5.24 |
| wet levelling render (12 lines) | 340.3038 | >= 5.104557 (bound) | HELD | >= 48.88 / 39.10 / 32.59 | >= 5.09 / 5.43 / 5.66 |
| spatter (bond) coat | 576.6519 | HELD (no thickness) | HELD | none (no mortar m3) | none |
s.5 status of every coat sum: HELD. Hand checks: 4.726962 x 7.6608 = 36.2123 bags; 5.104557 x 9.576 = 48.8812;
576.6519 = 236.3481 + 340.3038. Fixture K489 (100 m2 x 0.020 m, synthetic 1:4 spec): 2.000 m3 -> 15.3216 bags,
2.128 m3 sand; adverse no source -> HELD naming the 1990 spec 09200.

## Freelancer
Not compared (no mix to compare; the freelancer workbook is never a mix source). Verdict proposal: UNRESOLVED.

## Open
Mix per coat: needs the 1990 spec chapter 09200 as a file under 10 MB (or the owner's Urban mix). Spatter thickness.
Water. Purchase / waste factor. Exterior render.

Lessons row (proposed): a governing reference over the connector's download limit is recorded with the exact refusal
and its chapter location; the conversion (owner convention) and the ratio (missing) are separate inputs, so a missing
ratio holds only cement / sand, and the s.5 status of a figure is its weakest input (provenance T-489).
