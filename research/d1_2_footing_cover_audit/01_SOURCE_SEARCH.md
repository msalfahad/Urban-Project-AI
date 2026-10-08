# 01 SOURCE SEARCH: footing cover

**Classification: `MINIMUM_PROJECT_COVER_70`** (exactly one of EXACT_PROJECT_COVER_70 / MINIMUM_PROJECT_COVER_70 / DERIVED_EXACT_COVER / BOUNDED_COVER / UNRESOLVED).

## A. General minimum-cover note

- P8-N22 (ST7757.pdf p.8, channels PDF_RASTER, OCR(R4)):
  - Arabic: 22. يجب أن لا يقل سمك الغطاء الخرساني عن 2.5 سم في الأعمدة والبلاطات والجسور وعن 7سم في الخرسانة الملاصقة للتربة.
  - English: 22. The concrete cover thickness shall not be less than 2.5 cm in columns, slabs and beams, and 7 cm in concrete in contact with the soil.
- Wording read as: {'s1_transcription': 'MINIMUM', 'p8_raster_reread': 'MINIMUM', 'r4_register_scope': 'MINIMUM'} (every reading: MINIMUM).
- R4 register: COVER_AGAINST_SOIL_70MM = 70 mm, scope 'minimum cover', applies to FOOTING, FOOTING_2_LAYER, FOOTING_LIFT, STRAP_BEAM, GROUND_BEAM, GROUND_SLAB, COLUMN_STARTERS, POOL.
- S4 used it as: COVER_AGAINST_SOIL_70MM taken as the cover value with authority SOURCE_EXPLICIT; net straight = span - 70 - 70; rate count = ceil(rate x (dimension - 2 x 70)).

## B. Exact bar centreline / face offset in the footing details

Both p.13 details 'TYP. DETAIL OF ISOLATED FOOTING' were checked in two ways:
- the vector strokes (S-DIM.D dimension ticks against the S-REIN.D bar lines);
- a visual reading of every printed label and dimension in the footing body.

- SHALLOW: 214 dimension segments, 132 ticks; 0 on the bottom-bar line, 0 on the bar legs.
  - 'D': footing depth (vertical dimension, value from the schedule)
  - '40 Ø': column starter development above the footing top
  - 'Min. 30cm': length of the column bar's bent foot
  - 'Max. 10cm': from the column bar's bent foot down to the footing bottom face: places the column starter; it does not dimension the footing bars
  - '5': screed thickness under the footing (5cm Screed)
  - '10': plain concrete thickness (10cm Plain con.)
  - 'LESS THAN 2.5m': level difference ground beam to footing
  - 'Long bars / Short bars / Boxed bars': leaders to the bars, no dimension
  - bar-to-concrete-face dimension: NONE; cover annotation: NONE
- DEEP: 598 dimension segments, 473 ticks; 0 on the bottom-bar line, 0 on the bar legs.
  - 'Min. 30cm': length of the column bar's bent foot
  - 'Max. 10cm': from the column bar's bent foot down to the footing bottom face
  - '5 / 10': screed and plain-concrete thicknesses
  - 'MORE THAN 2.5m': level difference
  - 'Long bars / Short bars / Boxed bars / Insulation membrane': leaders, no dimension
  - bar-to-concrete-face dimension: NONE; cover annotation: NONE

## C. DXF

- 2780 texts, attributes and dimension overrides scanned, legacy Arabic decoded.
- Cover wording found: 0 (English); 0 (Arabic 'غطاء').
- Note 22 is not in the DXF; it exists only on the p.8 raster.
- The only '7.5cm' values: 16 on ['S-DIM.SCH'] = continuous-beam typical figures (pp.11-12): the 7.5 cm dimension that binds the CB bottom bar; not a footing cover.

## D. OCR of pp.9-16

- the D1.1 OCR dumps of pp.9-16 (same method as research/d1_1_stirrup_authority_audit/source_search_inputs/PDF_TEXT_OCR_PP9_16.json), searched again for COVER / COV / 7cm / 7 cm / 7.5 / CLEAR.
- Hits: {'p11': '7.5 (continuous-beam typical: the 7.5 cm bottom-bar dimension)', 'p15': 'CLEAR SPAN (slab detail)'}; footing cover hits: 0.

## Method

p.8 is a raster page (two embedded 1-bit images): image Xop1 OCR'd with tesseract 5 'ara' and the note-22 crop re-read visually after rotation. p.13 has no text layer: the two isolated-footing detail boxes were rendered from the vector strokes (pure-python pypdf renderer, 3.0 and 6.0 px/pt, rotated 90) and every printed label and dimension in the footing body was read visually. Nothing was measured by plotted scale. Renders stay in the session scratchpad; only their hashes are kept here.
