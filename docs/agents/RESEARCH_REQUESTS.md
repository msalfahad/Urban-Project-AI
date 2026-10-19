# Research requests (Lead writes; the research scout answers in RESEARCH_LOG.md "Answer to R-nn")

At most 3 open. Each: the problem in one sentence, the measured gap, what to look for, which task it unblocks.

## Open

### R-01 Floor and ceiling heights from Kuwait villa section drawings (lead 2026-10-19)
Problem: plaster and paint cannot be released without per-floor wall heights, and the engine has no bound section
heights for real plans. Gap (Alsenan, T-001b): plaster 1151.14 m2 and paint 1191.13 m2 reference, 0 compared (29 and 13
lines HELD). Look for: methods to read level marks (+3.50, F.F.L., S.S.L., T.O.S.) and dimension chains from DXF section
and elevation sheets and bind them to plan storeys; level-symbol detection; open-source code (permissive licence) for
section parsing; how QS practice derives plaster height (slab soffit vs false ceiling). Unblocks T-035, T-013, T-031.
Update (lead 2026-10-19 10:15, owner answer Q-14): the owner set the structural slab at 0.16 m unless a drawing or detail
says otherwise and asked that each floor report ground level, FFL, structural slab top, soffit, floor-to-floor, clear
height, false-ceiling height, plaster height and paint height separately, nothing subtracted by assumption. The
architectural sections are now readable as six PDF parts (vector, read visually). Sharpest question: how to tell these
level kinds apart on Gulf section and elevation sheets (symbols, prefixes such as F.F.L., S.S.L., T.O.S., Arabic
equivalents) and how to bind them to plan storeys. Unblocks T-063, T-013, T-046.

### R-02 Structural element populations from schedules and tables in DXF (lead 2026-10-19)
Problem: column and ground-beam concrete is held because element sizes and heights are not tied to every instance.
Gap (Alsenan, T-001b): columns 118 of 118 lines held (freelancer 39.75 m3), ground beams 61 of 84 held (freelancer
75.09 m3). Look for: reading column / beam schedules drawn as DXF text grids (cell detection, row / column binding),
linking a schedule mark to every plan instance, neck-column height from foundation sections; papers or tools with
permissive licences. Unblocks T-036 follow-ups, T-009.
Update (lead 2026-10-19 02:20, from T-036): 167 of the 205 held concrete lines release only when storey heights, neck
top level, founding depth, typical ground-beam sections by span band (printed as titles like `< 2.5 m (30x30)`) and the
blinding thickness come from a person-typed profile; so the sharpest question is how to read those printed values (level
marks, section titles, general notes) from structural DXF text reliably, in English and Arabic, cm and m. Unblocks
T-045, T-046, T-044.
Update (lead 2026-10-19 04:10, from T-044 / T-033): on two villas Arabic notes are drawn in SHX fonts and stored as Latin
keyboard codes (a printed founding depth was missed this way). Look for: how Arabic SHX fonts encode text in DXF, published
keyboard-to-Arabic maps and their variants per font, letter joining, open-source decoders (permissive licence), how to
detect an Arabic SHX style without a project's font names. Unblocks T-047, T-044, T-049.
Update (lead 2026-10-19 08:15, from T-004a): a second Arabic SHX family is unread: 47 room labels on the Alsenan
architectural plans (and 72 labels counted by T-044) use x-arab1b-style fonts whose codes match none of the Arabic (101)
keyboard maps T-047 uses. Look for: published code tables for the common Gulf / Middle East Arabic SHX fonts (ARABIC,
X-ARAB, XARAB1B, ARB, "Arial Arabic SHX" families), glyph-number to Unicode tables, and how to read an SHX font file's
glyph shapes to confirm a mapping (so a code is mapped only from a source, never inferred). Unblocks T-047 follow-ups,
T-053, T-062.

### R-04 Comparing an old building (PDF only) with its new design (CAD) for a renovation BOQ (lead 2026-10-19 12:20)
Problem: the owner's sealed test villa is a renovation: the old building exists only as a PDF, the new design as DWG / DXF
and PDF, and the engine must say for every wall and space whether it is retained, demolished or new before it can measure
flooring (wet / dry), plaster, paint and inner / outer blocks. Gap: the engine has no old-vs-new comparison and no plan
reader yet (0 of these classes produced today); synthetic old / new pairs are being built (T-068). Look for: registering a
scanned or vector PDF plan to a CAD plan (scale from printed dimensions, rotation, translation; ICP or feature matching on
wall lines), wall-level change detection between two plan versions, demolition / new-wall drawing conventions (hatch,
dashed lines, Arabic and English notes such as "هدم" / "يزال" / "جديد" / "TO BE DEMOLISHED"), QS practice for measuring
renovation items in the Gulf, open-source code with a permissive licence. Unblocks T-068 follow-ups, T-003, and the
measuring tasks that follow owner Q-23.

## Answered

(none yet)

## Withdrawn

### R-03 Storey / sheet detection in multi-sheet villa DXF (lead 2026-10-19)
Problem: a storey whose title the engine does not recognise is not measured. Gap: Alsenan run found GF / 1F / 2F only
while the reference includes a basement; T-029 still holds PENTHOUSE, LEVEL nn, 12th-floor Arabic titles. Look for:
title-block and frame detection in model-space sheets, bilingual (Arabic / English) storey naming conventions in Gulf
drawings, level-number conventions (LEVEL 00 = ground?), tools that split one DXF into sheets. Unblocks T-038, T-039.
Withdrawn (lead 2026-10-19 12:20): no longer the biggest gap: Alsenan has no basement (T-038, verified from the drawings) and storey titles beyond GF / 1F / 2F are merged (980e489); slot given to R-04.
