# Plan reader: reads PDF and image plans the way a person does

Purpose: for every sheet, a census of what a QS sees (rooms and their types, wet vs dry, doors, windows, printed
dimensions and areas, schedules, scale) in Arabic and English. It is the checklist that catches **silent omissions**
(Gate 1) and the intake for sheets that have no CAD (Gate 4). **It never produces a BOQ quantity**: quantities come
from CAD; a reading is a cross-check, and a disagreement goes to a person (existing hybrid rules,
`.claude/skills/urban-floorplan-vision-review`). Never average CAD and plan-reader values.

## Two layers

1. **Local text layer (always allowed).** Vector PDF text with positions (pdfplumber, MIT; pages rendered with
   pypdfium2, Apache-2.0 / BSD; not PyMuPDF, AGPL). Scans and photos: Tesseract `eng+ara` (Apache-2.0; `ara.traineddata`
   from `tesseract-ocr/tessdata_fast`, fetched by sparse git clone and pinned by SHA-256, not committed). Tested on a
   synthetic bilingual sheet: every Arabic label, English label, dimension, D/W tag and the scale read exactly.
2. **Visual layer (needs owner consent, Q-01).** Claude looks at the rendered page and assigns labels to rooms, counts
   rooms, bathrooms, kitchens, door swings, windows and wet zones. Off until Q-01 is answered yes.

## Output per sheet: `plan_reading.json`

`sheet, file_sha256, page, scale {printed, calibrated_from: [>= 2 printed dimensions] | NOT_SCALABLE}, rooms [{label_ar,
label_en, type, wet: bool, printed_dims, printed_area, position}], doors [{tag, position}], windows [{tag}], schedules
[...], counts {rooms, bathrooms, kitchens, doors, windows}, each value graded PRINTED | OCR | VISUAL, reader version`.
Readings of private drawings stay in the private data repository; the public repo holds code and synthetic tests only.

## Room-type vocabulary (seed; extend from real sheets)

غرفة نوم bedroom · ماستر / غرفة نوم رئيسية master bedroom · حمام / دورة مياه / WC bath (wet) · مطبخ kitchen (wet,
membrane scope = owner decision WP-KITCHEN) · غسيل / laundry (wet) · صالة / hall · مجلس / ديوانية majlis / diwaniya ·
طعام dining · خادمة maid · سائق driver · مخزن store · درج stairs · ممر corridor · بلكونة / شرفة balcony · سطح roof.
