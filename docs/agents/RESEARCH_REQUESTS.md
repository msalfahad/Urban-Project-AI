# Research requests (Lead writes; the research scout answers in RESEARCH_LOG.md "Answer to R-nn")

At most 3 open. Each: the problem in one sentence, the measured gap, what to look for, which task it unblocks.

## Open

### R-01 Floor and ceiling heights from Kuwait villa section drawings (lead 2026-10-19)
Problem: plaster and paint cannot be released without per-floor wall heights, and the engine has no bound section
heights for real plans. Gap (Alsenan, T-001b): plaster 1151.14 m2 and paint 1191.13 m2 reference, 0 compared (29 and 13
lines HELD). Look for: methods to read level marks (+3.50, F.F.L., S.S.L., T.O.S.) and dimension chains from DXF section
and elevation sheets and bind them to plan storeys; level-symbol detection; open-source code (permissive licence) for
section parsing; how QS practice derives plaster height (slab soffit vs false ceiling). Unblocks T-035, T-013, T-031.

### R-02 Structural element populations from schedules and tables in DXF (lead 2026-10-19)
Problem: column and ground-beam concrete is held because element sizes and heights are not tied to every instance.
Gap (Alsenan, T-001b): columns 118 of 118 lines held (freelancer 39.75 m3), ground beams 61 of 84 held (freelancer
75.09 m3). Look for: reading column / beam schedules drawn as DXF text grids (cell detection, row / column binding),
linking a schedule mark to every plan instance, neck-column height from foundation sections; papers or tools with
permissive licences. Unblocks T-036 follow-ups, T-009.

### R-03 Storey / sheet detection in multi-sheet villa DXF (lead 2026-10-19)
Problem: a storey whose title the engine does not recognise is not measured. Gap: Alsenan run found GF / 1F / 2F only
while the reference includes a basement; T-029 still holds PENTHOUSE, LEVEL nn, 12th-floor Arabic titles. Look for:
title-block and frame detection in model-space sheets, bilingual (Arabic / English) storey naming conventions in Gulf
drawings, level-number conventions (LEVEL 00 = ground?), tools that split one DXF into sheets. Unblocks T-038, T-039.

## Answered

(none yet)
