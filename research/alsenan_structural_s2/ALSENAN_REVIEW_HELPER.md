# Alsenan - review helper (plain language, for Mohammad)

## STR-BEA-001

**What does this mean?** A rule or note exists but it is not clear where or how it applies. P13 ground-beam typical details (<2.5 / <5 / >5 m): 9 beam(s) change class depending on the length basis (centre-to-centre / clear span).

**Words used here:**
- *span*: The length of a beam between two supports.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.dxf, p.3, GROUND BEAMS PLAN, layer 1
- ST7757.pdf, p.13, ground beam details

**What should I search in AutoCAD?**
- Open the sheet titled "GROUND BEAMS PLAN" (PDF page 3)
- LAYISO the layer "1" to see only that information (LAYUNISO to restore)
- Open the sheet titled "ground beam details" (PDF page 13)

**What would each answer change?**
- if *centre-to-centre*: classes: BM-GROUND_BEAMS-GB-BL002-2038=GB_LT_5M, BM-GROUND_BEAMS-GB-BL005-14438=GB_LT_5M, BM-GROUND_BEAMS-GB-BL008-9062=GB_LT_5M, BM-GROUND_BEAMS-GB-BL011-12362=GB_GT_5M, BM-GROUND_BEAMS-GB-BL020-9788=GB_LT_5M, BM-GROUND_BEAMS-GB-BL027-17038=GB_LT_5M, BM-GROUND_BEAMS-GB-BL028-17038=GB_LT_5M, BM-GROUND_BEAMS-GB-BL036-27612=GB_LT_5M, BM-GROUND_BEAMS-GB-BL037-28583=GB_LT_5M
- if *clear span*: classes: BM-GROUND_BEAMS-GB-BL002-2038=GB_LT_2_5M, BM-GROUND_BEAMS-GB-BL005-14438=GB_LT_2_5M, BM-GROUND_BEAMS-GB-BL008-9062=GB_LT_2_5M, BM-GROUND_BEAMS-GB-BL011-12362=GB_LT_5M, BM-GROUND_BEAMS-GB-BL020-9788=GB_LT_2_5M, BM-GROUND_BEAMS-GB-BL027-17038=GB_LT_2_5M, BM-GROUND_BEAMS-GB-BL028-17038=GB_LT_2_5M, BM-GROUND_BEAMS-GB-BL036-27612=GB_LT_2_5M, BM-GROUND_BEAMS-GB-BL037-28583=GB_LT_2_5M

**What should I ask the engineering office?** "P13 ground-beam typical details (<2.5 / <5 / >5 m): is the length measured centre-to-centre or clear span?"

## STR-BEA-002

**What does this mean?** A rule or note exists but it is not clear where or how it applies. Schedule row B.W (beam) is defined but no plan occurrence carries this mark.

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.

**Why does it matter?** No quantity changes with the answer; it is recorded for completeness.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.10, schedule (simple beam), handle 1FA5, 'B.W'

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (simple beam)" (PDF page 10)
- FIND (Ctrl+F) the text "B.W" - match whole word
- Select by handle: type (command "_.SELECT" (handent "1FA5") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *unused*: no change
- if *used at a location*: occurrence(s) added there

**What should I ask the engineering office?** "Schedule row B.W has no occurrence on the plans. Is it unused, or is a mark missing on a plan?"

## STR-BEA-003

**What does this mean?** A rule or note exists but it is not clear where or how it applies. Schedule row B10 (beam) is defined but no plan occurrence carries this mark.

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.

**Why does it matter?** No quantity changes with the answer; it is recorded for completeness.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.10, schedule (simple beam), handle 1ED0, 'B10'

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (simple beam)" (PDF page 10)
- FIND (Ctrl+F) the text "B10" - match whole word
- Select by handle: type (command "_.SELECT" (handent "1ED0") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *unused*: no change
- if *used at a location*: occurrence(s) added there

**What should I ask the engineering office?** "Schedule row B10 has no occurrence on the plans. Is it unused, or is a mark missing on a plan?"

## STR-BEA-004

**What does this mean?** A rule or note exists but it is not clear where or how it applies. Schedule row B12 (beam) is defined but no plan occurrence carries this mark.

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.

**Why does it matter?** No quantity changes with the answer; it is recorded for completeness.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.10, schedule (simple beam), handle 1EE6, 'B12'

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (simple beam)" (PDF page 10)
- FIND (Ctrl+F) the text "B12" - match whole word
- Select by handle: type (command "_.SELECT" (handent "1EE6") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *unused*: no change
- if *used at a location*: occurrence(s) added there

**What should I ask the engineering office?** "Schedule row B12 has no occurrence on the plans. Is it unused, or is a mark missing on a plan?"

## STR-BEA-005

**What does this mean?** The drawings give the requirement but not the method to measure it; the engineer must state the method. 16 beam occurrence(s) depend on P8-N21 (Side bars 2Ø12 / 3Ø12 / 4Ø12 in beams deeper than 60 cm, according to the beam width, unless stated otherwise.), whose method is not established (BLOCKED_METHOD).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.8, rule P8-N21

**What should I search in AutoCAD?**
- Open the sheet titled "rule P8-N21" (PDF page 8)

**What would each answer change?**
- if *2Ø12 / 3Ø12 / 4Ø12 per face*: side bars added

**What should I ask the engineering office?** "Beams deeper than 60 cm without side bars in their schedule row (CB1, CB11, CB12, CB3, CB6, CB7, CB8): how many 12 mm side bars per face?"

## STR-BEA-006

**What does this mean?** A size or length needed to measure this is not given. 2 beams: curved ground-beam span - support length not measured.

**Words used here:**
- *ground beam*: A beam at ground level, usually under walls, between footings or columns.
- *span*: The length of a beam between two supports.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.dxf, p.3, GROUND BEAMS PLAN, layer 1

**What should I search in AutoCAD?**
- Open the sheet titled "GROUND BEAMS PLAN" (PDF page 3)
- LAYISO the layer "1" to see only that information (LAYUNISO to restore)

**What would each answer change?**

**What should I ask the engineering office?** "Confirm the curved ground beam's supports and length (pool edge)."

## STR-BEA-007

**What does this mean?** A size or length needed to measure this is not given. 113 beam occurrence(s) depend on P8-N11 (Beams crossed by service pipes are widened by 5 cm.), whose extent is not established (BLOCKED_METHOD).

**Why does it matter?** Only the part that is certain is counted; the total is a minimum until this is answered.

**Where should I look?**
- ST7757.pdf, p.8, rule P8-N11

**What should I search in AutoCAD?**
- Open the sheet titled "rule P8-N11" (PDF page 8)

**What would each answer change?**
- if *none*: no change
- if *listed beams*: +5 cm width on those beams

**What should I ask the engineering office?** "Which beams are crossed by service pipes (drainage, water, electrical, AC) and must be widened by 5 cm?"

## STR-BEA-008

**What does this mean?** This member has no schedule row, so its size and bars are not defined. 6 beam member(s) at 1F_ROOF are drawn without a type mark (dome ring (curved)).

**Why does it matter?** The affected quantity is shown for checking but not counted in totals.

**Where should I look?**
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer 1

**What should I search in AutoCAD?**
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- LAYISO the layer "1" to see only that information (LAYUNISO to restore)

**What would each answer change?**
- if *a schedule type*: size and bars from that row
- if *not a structural member*: removed from the count

**What should I ask the engineering office?** "These beam members at 1F_ROOF carry no mark. Which type is each (or are they not structural members)?"

## STR-BEA-009

**What does this mean?** This member has no schedule row, so its size and bars are not defined. 13 beam member(s) at 1F_ROOF are drawn without a type mark (no mark).

**Why does it matter?** The affected quantity is shown for checking but not counted in totals.

**Where should I look?**
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer 1

**What should I search in AutoCAD?**
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- LAYISO the layer "1" to see only that information (LAYUNISO to restore)

**What would each answer change?**
- if *a schedule type*: size and bars from that row
- if *not a structural member*: removed from the count

**What should I ask the engineering office?** "These beam members at 1F_ROOF carry no mark. Which type is each (or are they not structural members)?"

## STR-BEA-010

**What does this mean?** This member has no schedule row, so its size and bars are not defined. 1 beam member(s) at 2F_ROOF are drawn without a type mark (no mark).

**Why does it matter?** The affected quantity is shown for checking but not counted in totals.

**Where should I look?**
- ST7757.dxf, p.6, SECOND FLOOR ROOF SLAB, layer 1

**What should I search in AutoCAD?**
- Open the sheet titled "SECOND FLOOR ROOF SLAB" (PDF page 6)
- LAYISO the layer "1" to see only that information (LAYUNISO to restore)

**What would each answer change?**
- if *a schedule type*: size and bars from that row
- if *not a structural member*: removed from the count

**What should I ask the engineering office?** "These beam members at 2F_ROOF carry no mark. Which type is each (or are they not structural members)?"

## STR-BEA-011

**What does this mean?** This member has no schedule row, so its size and bars are not defined. 5 beam member(s) at GF_ROOF are drawn without a type mark (no mark).

**Why does it matter?** The affected quantity is shown for checking but not counted in totals.

**Where should I look?**
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, layer 1

**What should I search in AutoCAD?**
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)
- LAYISO the layer "1" to see only that information (LAYUNISO to restore)

**What would each answer change?**
- if *a schedule type*: size and bars from that row
- if *not a structural member*: removed from the count

**What should I ask the engineering office?** "These beam members at GF_ROOF carry no mark. Which type is each (or are they not structural members)?"

## STR-BEA-012

**What does this mean?** Two places on the drawings say different things about the same thing. 1 beam occurrence(s) of type B21: schedule width (cm) differs from drawn width (cm) (45.0 vs 40.0).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.10, schedule (simple beam), 'B21'
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 468, 'B21'

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (simple beam)" (PDF page 10)
- FIND (Ctrl+F) the text "B21" - match whole word
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)
- Select by handle: type (command "_.SELECT" (handent "468") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=28103, Y=12422 (sheet-local mm)

**What would each answer change?**
- if *schedule width (cm)*: current quantity stands
- if *drawn width (cm)*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For beam type B21: does the schedule width (cm) govern, or the drawn width (cm) (45.0 vs 40.0)?"

## STR-BEA-013

**What does this mean?** Two places on the drawings say different things about the same thing. 1 beam occurrence(s) of type B29: schedule width (cm) differs from drawn width (cm) (25.0 vs 20.0).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.10, schedule (simple beam), 'B29'
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 465, 'B29'

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (simple beam)" (PDF page 10)
- FIND (Ctrl+F) the text "B29" - match whole word
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)
- Select by handle: type (command "_.SELECT" (handent "465") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=23682, Y=12602 (sheet-local mm)

**What would each answer change?**
- if *schedule width (cm)*: current quantity stands
- if *drawn width (cm)*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For beam type B29: does the schedule width (cm) govern, or the drawn width (cm) (25.0 vs 20.0)?"

## STR-BEA-014

**What does this mean?** Two places on the drawings say different things about the same thing. 1 beam occurrence(s) of type B6: schedule width (cm) differs from drawn width (cm) (25.0 vs 20.0).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.10, schedule (simple beam), 'B6'
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, handle 6C5, 'B6'

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (simple beam)" (PDF page 10)
- FIND (Ctrl+F) the text "B6" - match whole word
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- Select by handle: type (command "_.SELECT" (handent "6C5") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=24665, Y=18398 (sheet-local mm)

**What would each answer change?**
- if *schedule width (cm)*: current quantity stands
- if *drawn width (cm)*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For beam type B6: does the schedule width (cm) govern, or the drawn width (cm) (25.0 vs 20.0)?"

## STR-BEA-015

**What does this mean?** Two places on the drawings say different things about the same thing. 2 beam occurrence(s) of type CB10: schedule width (cm) differs from drawn width (cm) (25.0 vs 20.0).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.10, schedule (simple beam), 'CB10'
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, handle 717, 'CB10'
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, handle 718, 'CB10'

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (simple beam)" (PDF page 10)
- FIND (Ctrl+F) the text "CB10" - match whole word
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- Select by handle: type (command "_.SELECT" (handent "717") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=12138, Y=9903 (sheet-local mm)
- Select by handle: type (command "_.SELECT" (handent "718") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=12138, Y=13663 (sheet-local mm)

**What would each answer change?**
- if *schedule width (cm)*: current quantity stands
- if *drawn width (cm)*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For beam type CB10: does the schedule width (cm) govern, or the drawn width (cm) (25.0 vs 20.0)?"

## STR-BEA-016

**What does this mean?** Two places on the drawings say different things about the same thing. 2 beam occurrence(s) of type CB2: schedule width (cm) differs from drawn width (cm) (20.0 vs 25.0).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.10, schedule (simple beam), 'CB2'
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 42A, 'CB2'
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 42B, 'CB2'

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (simple beam)" (PDF page 10)
- FIND (Ctrl+F) the text "CB2" - match whole word
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)
- Select by handle: type (command "_.SELECT" (handent "42A") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=20953, Y=20890 (sheet-local mm)
- Select by handle: type (command "_.SELECT" (handent "42B") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=25130, Y=20890 (sheet-local mm)

**What would each answer change?**
- if *schedule width (cm)*: current quantity stands
- if *drawn width (cm)*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For beam type CB2: does the schedule width (cm) govern, or the drawn width (cm) (20.0 vs 25.0)?"

## STR-BEA-017

**What does this mean?** Two places on the drawings say different things about the same thing. One drawn beam carries 2 different type marks (CB3, B3); both marks sit on the same drawn span.

**Words used here:**
- *span*: The length of a beam between two supports.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 494, 'CB3'
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 1827, 'B3'

**What should I search in AutoCAD?**
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)
- FIND (Ctrl+F) the text "CB3" - match whole word
- Select by handle: type (command "_.SELECT" (handent "494") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=25635, Y=8415 (sheet-local mm)
- FIND (Ctrl+F) the text "B3" - match whole word
- Select by handle: type (command "_.SELECT" (handent "1827") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=25171, Y=9058 (sheet-local mm)

**What would each answer change?**
- if *CB3*: size and bars from CB3
- if *B3*: size and bars from B3
- if *two separate members*: split the outline; both rows apply

**What should I ask the engineering office?** "This beam is marked CB3 and B3. Which type is it - or is it two members drawn as one?"

## STR-BEA-018

**What does this mean?** Two places on the drawings say different things about the same thing. beam CB4: schedule spans [3.3, 3.7] but plan spans [2.724, 3.75] (SPAN_LENGTH_CONFLICT).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *span*: The length of a beam between two supports.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 45C, 'CB4'
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 45B, 'CB4'
- ST7757.dxf / ST7757.pdf, p.11, schedule (continuous beam), handle 2933, 'CB4'

**What should I search in AutoCAD?**
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)
- FIND (Ctrl+F) the text "CB4" - match whole word
- Select by handle: type (command "_.SELECT" (handent "45C") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- Select by handle: type (command "_.SELECT" (handent "45B") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- Open the sheet titled "schedule (continuous beam)" (PDF page 11)
- Select by handle: type (command "_.SELECT" (handent "2933") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *the tagged plan spans*: schedule bars assigned to the drawn spans; schedule spans need correction
- if *include the adjacent span(s)*: the member is longer than tagged

**What should I ask the engineering office?** "Which plan members form CB4 (schedule spans [3.3, 3.7])?"

## STR-BEA-019

**What does this mean?** Two places on the drawings say different things about the same thing. beam CB5: schedule spans [2.5, 4.5] but plan spans [2.85] (SPAN_COUNT_CONFLICT).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *span*: The length of a beam between two supports.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 475, 'CB5'
- ST7757.dxf / ST7757.pdf, p.11, schedule (continuous beam), handle 299F, 'CB5'

**What should I search in AutoCAD?**
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)
- FIND (Ctrl+F) the text "CB5" - match whole word
- Select by handle: type (command "_.SELECT" (handent "475") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- Open the sheet titled "schedule (continuous beam)" (PDF page 11)
- Select by handle: type (command "_.SELECT" (handent "299F") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *the tagged plan spans*: schedule bars assigned to the drawn spans; schedule spans need correction
- if *include the adjacent span(s)*: the member is longer than tagged

**What should I ask the engineering office?** "Which plan members form CB5 (schedule spans [2.5, 4.5])?"

## STR-BEA-020

**What does this mean?** Two places on the drawings say different things about the same thing. beam CB5: schedule spans [2.5, 4.5] but plan spans [4.2] (SPAN_COUNT_CONFLICT).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *span*: The length of a beam between two supports.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 474, 'CB5'
- ST7757.dxf / ST7757.pdf, p.11, schedule (continuous beam), handle 299F, 'CB5'

**What should I search in AutoCAD?**
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)
- FIND (Ctrl+F) the text "CB5" - match whole word
- Select by handle: type (command "_.SELECT" (handent "474") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- Open the sheet titled "schedule (continuous beam)" (PDF page 11)
- Select by handle: type (command "_.SELECT" (handent "299F") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *the tagged plan spans*: schedule bars assigned to the drawn spans; schedule spans need correction
- if *include the adjacent span(s)*: the member is longer than tagged

**What should I ask the engineering office?** "Which plan members form CB5 (schedule spans [2.5, 4.5])?"

## STR-BEA-021

**What does this mean?** Two places on the drawings say different things about the same thing. beam CB8: schedule spans [3.7, 6.4, 6.8] but plan spans [6.545, 6.95] (SPAN_COUNT_CONFLICT).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *span*: The length of a beam between two supports.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 69F, 'CB8'
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 6A0, 'CB8'
- ST7757.dxf / ST7757.pdf, p.11, schedule (continuous beam), handle 2574, 'CB8'

**What should I search in AutoCAD?**
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)
- FIND (Ctrl+F) the text "CB8" - match whole word
- Select by handle: type (command "_.SELECT" (handent "69F") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- Select by handle: type (command "_.SELECT" (handent "6A0") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- Open the sheet titled "schedule (continuous beam)" (PDF page 11)
- Select by handle: type (command "_.SELECT" (handent "2574") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *the tagged plan spans*: schedule bars assigned to the drawn spans; schedule spans need correction
- if *include the adjacent span(s)*: the member is longer than tagged
- if *extension as computed*: [3.825, 6.545, 6.95]

**What should I ask the engineering office?** "Which plan members form CB8 (schedule spans [3.7, 6.4, 6.8])?"

## STR-BEA-022

**What does this mean?** Two places on the drawings say different things about the same thing. Schedule key SB2 is defined 2 times with different values.

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.10, schedule (strap beam), handle 2ABA, 'SB2'
- ST7757.dxf / ST7757.pdf, p.10, schedule (strap beam), handle 1FBB, 'SB2'

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (strap beam)" (PDF page 10)
- FIND (Ctrl+F) the text "SB2" - match whole word
- Select by handle: type (command "_.SELECT" (handent "2ABA") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- Select by handle: type (command "_.SELECT" (handent "1FBB") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *row 2ABA*: use {'BOT-B': '10', 'BOT-D': '16', 'D': '8', 'H': '50', 'STI-B': '10', 'TOP-B': '20', 'TOP-D': '18', 'W': '100'}
- if *row 1FBB*: use {'BOT-B': '10', 'BOT-D': '18', 'D': '8', 'H': '50', 'STI-B': '10', 'TOP-B': '10', 'TOP-D': '18', 'W': '80'}

**What should I ask the engineering office?** "Schedule key SB2 appears twice. Which row is valid?"

## STR-BEA-023

**What does this mean?** A member drawn on the plan cannot be tied to one type mark with certainty. Mark B6 sits between 3 members at similar distance; the member it names is not certain.

**Why does it matter?** The affected quantity is shown for checking but not counted in totals.

**Where should I look?**
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, handle 6BD, 'B6'

**What should I search in AutoCAD?**
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- FIND (Ctrl+F) the text "B6" - match whole word
- Select by handle: type (command "_.SELECT" (handent "6BD") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=14483, Y=15161 (sheet-local mm)

**What would each answer change?**
- if *BL013*: B6 assigned to BL013
- if *BA002*: B6 assigned to BA002
- if *BL009*: B6 assigned to BL009

**What should I ask the engineering office?** "Which member does mark B6 refer to?"

## STR-BEA-024

**What does this mean?** A member drawn on the plan cannot be tied to one type mark with certainty. Mark B6 sits between 3 members at similar distance; the member it names is not certain.

**Why does it matter?** The affected quantity is shown for checking but not counted in totals.

**Where should I look?**
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, handle 6D4, 'B6'

**What should I search in AutoCAD?**
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- FIND (Ctrl+F) the text "B6" - match whole word
- Select by handle: type (command "_.SELECT" (handent "6D4") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=29103, Y=15184 (sheet-local mm)

**What would each answer change?**
- if *BL031*: B6 assigned to BL031
- if *BA005*: B6 assigned to BA005
- if *BA006*: B6 assigned to BA006

**What should I ask the engineering office?** "Which member does mark B6 refer to?"

## STR-BEA-025

**What does this mean?** A member drawn on the plan cannot be tied to one type mark with certainty. Mark B6 sits between 3 members at similar distance; the member it names is not certain.

**Why does it matter?** The affected quantity is shown for checking but not counted in totals.

**Where should I look?**
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, handle 6D7, 'B6'

**What should I search in AutoCAD?**
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- FIND (Ctrl+F) the text "B6" - match whole word
- Select by handle: type (command "_.SELECT" (handent "6D7") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=29103, Y=10512 (sheet-local mm)

**What would each answer change?**
- if *BA007*: B6 assigned to BA007
- if *BA008*: B6 assigned to BA008
- if *BL030*: B6 assigned to BL030

**What should I ask the engineering office?** "Which member does mark B6 refer to?"

## STR-BEA-026

**What does this mean?** A member drawn on the plan cannot be tied to one type mark with certainty. Mark B6 sits between 3 members at similar distance; the member it names is not certain.

**Why does it matter?** The affected quantity is shown for checking but not counted in totals.

**Where should I look?**
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, handle 76C, 'B6'

**What should I search in AutoCAD?**
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- FIND (Ctrl+F) the text "B6" - match whole word
- Select by handle: type (command "_.SELECT" (handent "76C") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=14622, Y=9800 (sheet-local mm)

**What would each answer change?**
- if *BL012*: B6 assigned to BL012
- if *BA003*: B6 assigned to BA003
- if *BA004*: B6 assigned to BA004

**What should I ask the engineering office?** "Which member does mark B6 refer to?"

## STR-BEA-027

**What does this mean?** A member drawn on the plan cannot be tied to one type mark with certainty. Mark B1 sits between 2 members at similar distance; the member it names is not certain.

**Why does it matter?** The affected quantity is shown for checking but not counted in totals.

**Where should I look?**
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 45D, 'B1'

**What should I search in AutoCAD?**
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)
- FIND (Ctrl+F) the text "B1" - match whole word
- Select by handle: type (command "_.SELECT" (handent "45D") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=16626, Y=16532 (sheet-local mm)

**What would each answer change?**
- if *BL029*: B1 assigned to BL029
- if *BL016*: B1 assigned to BL016

**What should I ask the engineering office?** "Which member does mark B1 refer to?"

## STR-BEA-028

**What does this mean?** A member drawn on the plan cannot be tied to one type mark with certainty. Mark B8 sits between 2 members at similar distance; the member it names is not certain.

**Why does it matter?** The affected quantity is shown for checking but not counted in totals.

**Where should I look?**
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 472, 'B8'

**What should I search in AutoCAD?**
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)
- FIND (Ctrl+F) the text "B8" - match whole word
- Select by handle: type (command "_.SELECT" (handent "472") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=30868, Y=18194 (sheet-local mm)

**What would each answer change?**
- if *BL031*: B8 assigned to BL031
- if *BA004*: B8 assigned to BA004

**What should I ask the engineering office?** "Which member does mark B8 refer to?"

## STR-COL-001

**What does this mean?** A rule or note exists but it is not clear where or how it applies. Type CN occurs only at FOUNDATION (6 occurrence(s)) while other columns continue upward.

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf, p.2, FOUNDATION PLAN, 'CN'
- ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'CN'

**What should I search in AutoCAD?**
- Open the sheet titled "FOUNDATION PLAN" (PDF page 2)
- FIND (Ctrl+F) the text "CN" - match whole word
- Open the sheet titled "schedule (column)" (PDF page 9)

**What would each answer change?**
- if *column stopping at FOUNDATION*: stays in the column count
- if *foundation stub / pedestal*: moves to the foundation item

**What should I ask the engineering office?** "Is CN a column that stops at FOUNDATION, or a short stub / pedestal that belongs to the foundation item?"

## STR-COL-002

**What does this mean?** A rule or note exists but it is not clear where or how it applies. ST. OF COLUMN- 6Ø8/m (column ties) gives a count per metre, but 2 band(s) use more than one closed tie per level; whether the count is of tie SETS or of single ties is not stated.

**Words used here:**
- *tie*: A closed loop of thin steel bar that wraps the main vertical bars of a column (also called a link or stirrup). Ties stop the main bars buckling; their number decides how much small-diameter steel is needed.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').
- *per metre*: A bar count given for each metre of length (e.g. 6 ties per metre of column).

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.9, DETAILS OF COLUMN REINFORCEMENT (schedule sheet), handle 1BAA, 'ST. OF COLUMN- 6Ø8/m'

**What should I search in AutoCAD?**
- Open the sheet titled "DETAILS OF COLUMN REINFORCEMENT (schedule sheet)" (PDF page 9)
- FIND (Ctrl+F) the text "ST. OF COLUMN- 6Ø8/m" - match whole word
- Select by handle: type (command "_.SELECT" (handent "1BAA") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *tie sets per metre*: each level has all ties of the band
- if *single ties per metre*: the count is shared between the ties of a level

**What should I ask the engineering office?** "ST. OF COLUMN- 6Ø8/m (column ties): is the per-metre count the number of tie sets (all closed ties at one level) or the number of single ties?"

## STR-COL-003

**What does this mean?** A rule or note exists but it is not clear where or how it applies. Type C10 (FOUNDATION), C10 (GF), C5 (FOUNDATION), C5 (GF), C6 (FOUNDATION), C6 (GF), C9 (2F) has 10 main bars but the detail sketch for its band shows 8; which bars each tie encloses is not shown.

**Words used here:**
- *tie*: A closed loop of thin steel bar that wraps the main vertical bars of a column (also called a link or stirrup). Ties stop the main bars buckling; their number decides how much small-diameter steel is needed.
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.9, DETAILS OF COLUMN REINFORCEMENT (schedule sheet), handle 1BAA, 'ST. OF COLUMN- 6Ø8/m'

**What should I search in AutoCAD?**
- Open the sheet titled "DETAILS OF COLUMN REINFORCEMENT (schedule sheet)" (PDF page 9)
- FIND (Ctrl+F) the text "ST. OF COLUMN- 6Ø8/m" - match whole word
- Select by handle: type (command "_.SELECT" (handent "1BAA") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *scale the sketch*: tie sizes from the sketch fractions
- if *specific bar grouping*: tie sizes from the stated grouping

**What should I ask the engineering office?** "For C10 (FOUNDATION), C10 (GF), C5 (FOUNDATION), C5 (GF), C6 (FOUNDATION), C6 (GF), C9 (2F) (10 bars): which bars does each overlapping tie enclose?"

## STR-COL-004

**What does this mean?** A rule or note exists but it is not clear where or how it applies. Type C11 (FOUNDATION), C11 (GF), C9 (FOUNDATION), C9 (GF) has 14 main bars but the detail sketch for its band shows 12; which bars each tie encloses is not shown.

**Words used here:**
- *tie*: A closed loop of thin steel bar that wraps the main vertical bars of a column (also called a link or stirrup). Ties stop the main bars buckling; their number decides how much small-diameter steel is needed.
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.9, DETAILS OF COLUMN REINFORCEMENT (schedule sheet), handle 1BAA, 'ST. OF COLUMN- 6Ø8/m'

**What should I search in AutoCAD?**
- Open the sheet titled "DETAILS OF COLUMN REINFORCEMENT (schedule sheet)" (PDF page 9)
- FIND (Ctrl+F) the text "ST. OF COLUMN- 6Ø8/m" - match whole word
- Select by handle: type (command "_.SELECT" (handent "1BAA") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *scale the sketch*: tie sizes from the sketch fractions
- if *specific bar grouping*: tie sizes from the stated grouping

**What should I ask the engineering office?** "For C11 (FOUNDATION), C11 (GF), C9 (FOUNDATION), C9 (GF) (14 bars): which bars does each overlapping tie enclose?"

## STR-COL-005

**What does this mean?** A rule or note exists but it is not clear where or how it applies. Type C1 (1F), C1 (2F), C2 (2F), C3 (1F), C3 (2F), C5 (2F) has 6 main bars but the detail sketch for its band shows 4; which bars each tie encloses is not shown.

**Words used here:**
- *tie*: A closed loop of thin steel bar that wraps the main vertical bars of a column (also called a link or stirrup). Ties stop the main bars buckling; their number decides how much small-diameter steel is needed.
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.9, DETAILS OF COLUMN REINFORCEMENT (schedule sheet), handle 1BAA, 'ST. OF COLUMN- 6Ø8/m'

**What should I search in AutoCAD?**
- Open the sheet titled "DETAILS OF COLUMN REINFORCEMENT (schedule sheet)" (PDF page 9)
- FIND (Ctrl+F) the text "ST. OF COLUMN- 6Ø8/m" - match whole word
- Select by handle: type (command "_.SELECT" (handent "1BAA") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *scale the sketch*: tie sizes from the sketch fractions
- if *specific bar grouping*: tie sizes from the stated grouping

**What should I ask the engineering office?** "For C1 (1F), C1 (2F), C2 (2F), C3 (1F), C3 (2F), C5 (2F) (6 bars): which bars does each overlapping tie enclose?"

## STR-COL-006

**What does this mean?** A rule or note exists but it is not clear where or how it applies. Type C (FOUNDATION), C (GF), C1 (FOUNDATION), C1 (GF), C2 (1F), C2 (FOUNDATION), C2 (GF), C3 (FOUNDATION), C3 (GF), C4 (1F), C4 (FOUNDATION), C4 (GF), C5 (1F) has 8 main bars but the detail sketch for its band shows 4; which bars each tie encloses is not shown.

**Words used here:**
- *tie*: A closed loop of thin steel bar that wraps the main vertical bars of a column (also called a link or stirrup). Ties stop the main bars buckling; their number decides how much small-diameter steel is needed.
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.9, DETAILS OF COLUMN REINFORCEMENT (schedule sheet), handle 1BAA, 'ST. OF COLUMN- 6Ø8/m'

**What should I search in AutoCAD?**
- Open the sheet titled "DETAILS OF COLUMN REINFORCEMENT (schedule sheet)" (PDF page 9)
- FIND (Ctrl+F) the text "ST. OF COLUMN- 6Ø8/m" - match whole word
- Select by handle: type (command "_.SELECT" (handent "1BAA") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *scale the sketch*: tie sizes from the sketch fractions
- if *specific bar grouping*: tie sizes from the stated grouping

**What should I ask the engineering office?** "For C (FOUNDATION), C (GF), C1 (FOUNDATION), C1 (GF), C2 (1F), C2 (FOUNDATION), C2 (GF), C3 (FOUNDATION), C3 (GF), C4 (1F), C4 (FOUNDATION), C4 (GF), C5 (1F) (8 bars): which bars does each overlapping tie enclose?"

## STR-COL-007

**What does this mean?** The drawings give the requirement but not the method to measure it; the engineer must state the method. ST. OF COLUMN- 6Ø8/m (column ties) gives ties per metre but not over which height: full storey height, clear height below the beams, or including the joint.

**Words used here:**
- *slab*: A flat concrete floor or roof plate.
- *per metre*: A bar count given for each metre of length (e.g. 6 ties per metre of column).

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.9, DETAILS OF COLUMN REINFORCEMENT (schedule sheet), handle 1BAA, 'ST. OF COLUMN- 6Ø8/m'

**What should I search in AutoCAD?**
- Open the sheet titled "DETAILS OF COLUMN REINFORCEMENT (schedule sheet)" (PDF page 9)
- FIND (Ctrl+F) the text "ST. OF COLUMN- 6Ø8/m" - match whole word
- Select by handle: type (command "_.SELECT" (handent "1BAA") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *floor-to-floor*: largest tie count
- if *clear height*: fewer ties; needs beam depths per face
- if *clear height + joint*: between the two

**What should I ask the engineering office?** "Over which vertical length are the column ties counted: floor-to-floor, clear height between slab and beam soffit, or clear height plus the beam-column joint?"

## STR-COL-008

**What does this mean?** A drawing rule does not cover this exact case (for example a value sits exactly on a limit). column tie rule (arrangement by long side L): value 80.0 cm (C7) is on a limit no band includes.

**Words used here:**
- *tie*: A closed loop of thin steel bar that wraps the main vertical bars of a column (also called a link or stirrup). Ties stop the main bars buckling; their number decides how much small-diameter steel is needed.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.9, DETAILS OF COLUMN REINFORCEMENT (schedule sheet), handle 1BAA, 'ST. OF COLUMN- 6Ø8/m'

**What should I search in AutoCAD?**
- Open the sheet titled "DETAILS OF COLUMN REINFORCEMENT (schedule sheet)" (PDF page 9)
- FIND (Ctrl+F) the text "ST. OF COLUMN- 6Ø8/m" - match whole word
- Select by handle: type (command "_.SELECT" (handent "1BAA") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *50cm < L < 80cm*: use band TIE_50_LT_L_LT_80
- if *80cm < L < 120cm*: use band TIE_80_LT_L_LT_120

**What should I ask the engineering office?** "column tie rule (arrangement by long side L): which band applies where the value is exactly 80.0 cm?"

## STR-COL-009

**What does this mean?** Two places on the drawings say different things about the same thing. column at grid X04/Y01: equal-authority sources give different types (C3 vs C).

**Words used here:**
- *tag*: The short type mark printed next to a member on a plan (for example a column or beam mark).

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.dxf, p.1, COLUMN & AXIS PLAN, layer S-TEXT, handle 100A, 'C3'
- ST7757.dxf, p.2, FOUNDATION PLAN, layer S-TEXT, handle 1681, 'C3'
- ST7757.dxf, p.3, GROUND BEAMS PLAN, layer S-TEXT, handle 20D, 'C'

**What should I search in AutoCAD?**
- Open the sheet titled "COLUMN & AXIS PLAN" (PDF page 1)
- FIND (Ctrl+F) the text "C3" - match whole word
- Select by handle: type (command "_.SELECT" (handent "100A") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- LAYISO the layer "S-TEXT" to see only that information (LAYUNISO to restore)
- Open the sheet titled "FOUNDATION PLAN" (PDF page 2)
- Select by handle: type (command "_.SELECT" (handent "1681") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- Open the sheet titled "GROUND BEAMS PLAN" (PDF page 3)
- FIND (Ctrl+F) the text "C" - match whole word
- Select by handle: type (command "_.SELECT" (handent "20D") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *type C3*: section and bars from the C3 schedule row
- if *type C*: section and bars from the C schedule row

**What should I ask the engineering office?** "Which type is correct for this column (at grid X04/Y01): C3 or C?"

## STR-COL-010

**What does this mean?** Two places on the drawings say different things about the same thing. column at grid X12/Y02: equal-authority sources give different types (C8 vs C7).

**Words used here:**
- *tag*: The short type mark printed next to a member on a plan (for example a column or beam mark).

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.dxf, p.1, COLUMN & AXIS PLAN, layer S-TEXT, handle 101A, 'C8'
- ST7757.dxf, p.2, FOUNDATION PLAN, layer S-TEXT, handle 10E1, 'C8'
- ST7757.dxf, p.3, GROUND BEAMS PLAN, layer S-TEXT, handle 24E, 'C7'
- ST7757.dxf, p.1, COLUMN & AXIS PLAN, layer S-TEXT, '30X80'

**What should I search in AutoCAD?**
- Open the sheet titled "COLUMN & AXIS PLAN" (PDF page 1)
- FIND (Ctrl+F) the text "C8" - match whole word
- Select by handle: type (command "_.SELECT" (handent "101A") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- LAYISO the layer "S-TEXT" to see only that information (LAYUNISO to restore)
- Open the sheet titled "FOUNDATION PLAN" (PDF page 2)
- Select by handle: type (command "_.SELECT" (handent "10E1") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- Open the sheet titled "GROUND BEAMS PLAN" (PDF page 3)
- FIND (Ctrl+F) the text "C7" - match whole word
- Select by handle: type (command "_.SELECT" (handent "24E") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- FIND (Ctrl+F) the text "30X80" - match whole word

**What would each answer change?**
- if *type C8*: section and bars from the C8 schedule row
- if *type C7*: section and bars from the C7 schedule row; the corroborating evidence agrees

**What should I ask the engineering office?** "Which type is correct for this column (at grid X12/Y02): C8 or C7?"

## STR-COL-011

**What does this mean?** Two places on the drawings say different things about the same thing. column CN is drawn on FOUNDATION PLAN, GROUND BEAMS PLAN but not on COLUMN & AXIS PLAN.

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf, p.2, FOUNDATION PLAN, handle 180A
- ST7757.dxf, p.3, GROUND BEAMS PLAN, handle 17BA

**What should I search in AutoCAD?**
- Open the sheet titled "FOUNDATION PLAN" (PDF page 2)
- Select by handle: type (command "_.SELECT" (handent "180A") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- Open the sheet titled "GROUND BEAMS PLAN" (PDF page 3)
- Select by handle: type (command "_.SELECT" (handent "17BA") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *exists*: keep
- if *does not exist*: remove from the count

**What should I ask the engineering office?** "Does this column exist (it is missing on COLUMN & AXIS PLAN)?"

## STR-COL-012

**What does this mean?** Two places on the drawings say different things about the same thing. 1 column occurrence(s) of type C1: schedule section (storey band) differs from drawn outline ([30.0, 50.0] vs [20.0, 50.0]).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').
- *section*: The cross-section size of a member (width x depth).

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C1'
- ST7757.dxf, p.2, FOUNDATION PLAN, layer S-COL.BON, handle 1099

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (column)" (PDF page 9)
- FIND (Ctrl+F) the text "C1" - match whole word
- Open the sheet titled "FOUNDATION PLAN" (PDF page 2)
- Select by handle: type (command "_.SELECT" (handent "1099") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- LAYISO the layer "S-COL.BON" to see only that information (LAYUNISO to restore)
- ZOOM to about X=19688, Y=17362 (sheet-local mm)

**What would each answer change?**
- if *schedule section (storey band)*: current quantity stands
- if *drawn outline*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For column type C1: does the schedule section (storey band) govern, or the drawn outline ([30.0, 50.0] vs [20.0, 50.0])?"

## STR-COL-013

**What does this mean?** Two places on the drawings say different things about the same thing. 2 column occurrence(s) of type C2: schedule section (storey band) differs from drawn outline ([30.0, 50.0] vs [20.0, 50.0]).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').
- *section*: The cross-section size of a member (width x depth).

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C2'
- ST7757.dxf, p.2, FOUNDATION PLAN, layer S-COL.BON, handle 1096
- ST7757.dxf, p.2, FOUNDATION PLAN, layer S-COL.BON, handle 1093

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (column)" (PDF page 9)
- FIND (Ctrl+F) the text "C2" - match whole word
- Open the sheet titled "FOUNDATION PLAN" (PDF page 2)
- Select by handle: type (command "_.SELECT" (handent "1096") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- LAYISO the layer "S-COL.BON" to see only that information (LAYUNISO to restore)
- ZOOM to about X=19688, Y=15662 (sheet-local mm)
- Select by handle: type (command "_.SELECT" (handent "1093") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=21688, Y=17362 (sheet-local mm)

**What would each answer change?**
- if *schedule section (storey band)*: current quantity stands
- if *drawn outline*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For column type C2: does the schedule section (storey band) govern, or the drawn outline ([30.0, 50.0] vs [20.0, 50.0])?"

## STR-COL-014

**What does this mean?** Two places on the drawings say different things about the same thing. 4 column occurrence(s) of type C3: schedule section (storey band) differs from drawn outline ([20.0, 50.0] vs [25.0, 50.0]; [25.0, 50.0] vs [20.0, 40.0]; [25.0, 50.0] vs [20.0, 50.0]).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').
- *section*: The cross-section size of a member (width x depth).

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C3'
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, layer S-COL.BON, handle 350
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, layer S-COL.BON, handle 344
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer S-COL.BON, handle 691
- ST7757.dxf, p.6, SECOND FLOOR ROOF SLAB, layer S-COL.BON, handle 424

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (column)" (PDF page 9)
- FIND (Ctrl+F) the text "C3" - match whole word
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)
- Select by handle: type (command "_.SELECT" (handent "350") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- LAYISO the layer "S-COL.BON" to see only that information (LAYUNISO to restore)
- ZOOM to about X=7938, Y=7412 (sheet-local mm)
- Select by handle: type (command "_.SELECT" (handent "344") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=33158, Y=14962 (sheet-local mm)
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- Select by handle: type (command "_.SELECT" (handent "691") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=17013, Y=17362 (sheet-local mm)
- Open the sheet titled "SECOND FLOOR ROOF SLAB" (PDF page 6)
- Select by handle: type (command "_.SELECT" (handent "424") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *schedule section (storey band)*: current quantity stands
- if *drawn outline*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For column type C3: does the schedule section (storey band) govern, or the drawn outline ([20.0, 50.0] vs [25.0, 50.0]; [25.0, 50.0] vs [20.0, 40.0]; [25.0, 50.0] vs [20.0, 50.0])?"

## STR-COL-015

**What does this mean?** Two places on the drawings say different things about the same thing. 3 column occurrence(s) of type C4: schedule section (storey band) differs from drawn outline ([20.0, 50.0] vs [25.0, 50.0]; [30.0, 50.0] vs [25.0, 50.0]).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').
- *section*: The cross-section size of a member (width x depth).

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C4'
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer S-COL.BON, handle 697
- ST7757.dxf, p.2, FOUNDATION PLAN, layer S-COL.BON, handle 108D
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer S-COL.BON, handle 676

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (column)" (PDF page 9)
- FIND (Ctrl+F) the text "C4" - match whole word
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- Select by handle: type (command "_.SELECT" (handent "697") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- LAYISO the layer "S-COL.BON" to see only that information (LAYUNISO to restore)
- ZOOM to about X=27458, Y=20687 (sheet-local mm)
- Open the sheet titled "FOUNDATION PLAN" (PDF page 2)
- Select by handle: type (command "_.SELECT" (handent "108D") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=31508, Y=20687 (sheet-local mm)
- Select by handle: type (command "_.SELECT" (handent "676") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *schedule section (storey band)*: current quantity stands
- if *drawn outline*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For column type C4: does the schedule section (storey band) govern, or the drawn outline ([20.0, 50.0] vs [25.0, 50.0]; [30.0, 50.0] vs [25.0, 50.0])?"

## STR-COL-016

**What does this mean?** Two places on the drawings say different things about the same thing. 4 column occurrence(s) of type C5: schedule section (storey band) differs from drawn outline ([20.0, 50.0] vs [20.0, 60.0]; [20.0, 50.0] vs [25.0, 60.0]).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').
- *section*: The cross-section size of a member (width x depth).

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C5'
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer S-COL.BON, handle 694
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer S-COL.BON, handle 685
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer S-COL.BON, handle 673
- ST7757.dxf, p.6, SECOND FLOOR ROOF SLAB, layer S-COL.BON, handle 415

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (column)" (PDF page 9)
- FIND (Ctrl+F) the text "C5" - match whole word
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- Select by handle: type (command "_.SELECT" (handent "694") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- LAYISO the layer "S-COL.BON" to see only that information (LAYUNISO to restore)
- ZOOM to about X=27658, Y=8937 (sheet-local mm)
- Select by handle: type (command "_.SELECT" (handent "685") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=12588, Y=11912 (sheet-local mm)
- Select by handle: type (command "_.SELECT" (handent "673") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=23558, Y=20687 (sheet-local mm)
- Open the sheet titled "SECOND FLOOR ROOF SLAB" (PDF page 6)
- Select by handle: type (command "_.SELECT" (handent "415") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=23558, Y=20712 (sheet-local mm)

**What would each answer change?**
- if *schedule section (storey band)*: current quantity stands
- if *drawn outline*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For column type C5: does the schedule section (storey band) govern, or the drawn outline ([20.0, 50.0] vs [20.0, 60.0]; [20.0, 50.0] vs [25.0, 60.0])?"

## STR-COL-017

**What does this mean?** Two places on the drawings say different things about the same thing. 1 column occurrence(s) of type C6: schedule section (storey band) differs from drawn outline ([20.0, 60.0] vs [25.0, 70.0]).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').
- *section*: The cross-section size of a member (width x depth).

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C6'
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer S-COL.BON, handle 688

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (column)" (PDF page 9)
- FIND (Ctrl+F) the text "C6" - match whole word
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- Select by handle: type (command "_.SELECT" (handent "688") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- LAYISO the layer "S-COL.BON" to see only that information (LAYUNISO to restore)
- ZOOM to about X=17013, Y=12362 (sheet-local mm)

**What would each answer change?**
- if *schedule section (storey band)*: current quantity stands
- if *drawn outline*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For column type C6: does the schedule section (storey band) govern, or the drawn outline ([20.0, 60.0] vs [25.0, 70.0])?"

## STR-COL-018

**What does this mean?** Two places on the drawings say different things about the same thing. 1 column occurrence(s) of type C7: schedule section (storey band) differs from drawn outline ([20.0, 80.0] vs [25.0, 80.0]).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').
- *section*: The cross-section size of a member (width x depth).

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C7'
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer S-COL.BON, handle 68E

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (column)" (PDF page 9)
- FIND (Ctrl+F) the text "C7" - match whole word
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- Select by handle: type (command "_.SELECT" (handent "68E") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- LAYISO the layer "S-COL.BON" to see only that information (LAYUNISO to restore)
- ZOOM to about X=15888, Y=16187 (sheet-local mm)

**What would each answer change?**
- if *schedule section (storey band)*: current quantity stands
- if *drawn outline*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For column type C7: does the schedule section (storey band) govern, or the drawn outline ([20.0, 80.0] vs [25.0, 80.0])?"

## STR-COL-019

**What does this mean?** Two places on the drawings say different things about the same thing. 3 column occurrence(s) of type C8: schedule section (storey band) differs from drawn outline ([20.0, 90.0] vs [25.0, 80.0]; [25.0, 90.0] vs [25.0, 80.0]; [30.0, 90.0] vs [30.0, 80.0]).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').
- *section*: The cross-section size of a member (width x depth).

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C8'
- ST7757.dxf, p.2, FOUNDATION PLAN, layer S-COL.BON, handle 10E0
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, layer S-COL.BON, handle 380
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer S-COL.BON, handle 69A

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (column)" (PDF page 9)
- FIND (Ctrl+F) the text "C8" - match whole word
- Open the sheet titled "FOUNDATION PLAN" (PDF page 2)
- Select by handle: type (command "_.SELECT" (handent "10E0") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- LAYISO the layer "S-COL.BON" to see only that information (LAYUNISO to restore)
- ZOOM to about X=24308, Y=8912 (sheet-local mm)
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)
- Select by handle: type (command "_.SELECT" (handent "380") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=24308, Y=8937 (sheet-local mm)
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- Select by handle: type (command "_.SELECT" (handent "69A") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *schedule section (storey band)*: current quantity stands
- if *drawn outline*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For column type C8: does the schedule section (storey band) govern, or the drawn outline ([20.0, 90.0] vs [25.0, 80.0]; [25.0, 90.0] vs [25.0, 80.0]; [30.0, 90.0] vs [30.0, 80.0])?"

## STR-COL-020

**What does this mean?** Two places on the drawings say different things about the same thing. 3 column occurrence(s) of type C9: schedule section (storey band) differs from drawn outline ([20.0, 90.0] vs [20.0, 100.0]; [20.0, 90.0] vs [25.0, 100.0]; [30.0, 100.0] vs [25.0, 100.0]).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').
- *section*: The cross-section size of a member (width x depth).

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C9'
- ST7757.dxf, p.2, FOUNDATION PLAN, layer S-COL.BON, handle 1090
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer S-COL.BON, handle 679
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer S-COL.BON, handle 667

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (column)" (PDF page 9)
- FIND (Ctrl+F) the text "C9" - match whole word
- Open the sheet titled "FOUNDATION PLAN" (PDF page 2)
- Select by handle: type (command "_.SELECT" (handent "1090") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- LAYISO the layer "S-COL.BON" to see only that information (LAYUNISO to restore)
- ZOOM to about X=21713, Y=15912 (sheet-local mm)
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- Select by handle: type (command "_.SELECT" (handent "679") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- Select by handle: type (command "_.SELECT" (handent "667") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=27308, Y=16587 (sheet-local mm)

**What would each answer change?**
- if *schedule section (storey band)*: current quantity stands
- if *drawn outline*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For column type C9: does the schedule section (storey band) govern, or the drawn outline ([20.0, 90.0] vs [20.0, 100.0]; [20.0, 90.0] vs [25.0, 100.0]; [30.0, 100.0] vs [25.0, 100.0])?"

## STR-COL-021

**What does this mean?** Two places on the drawings say different things about the same thing. 5 column occurrence(s) of type C: schedule section (storey band) differs from drawn outline ([20.0, 50.0] vs [20.0, 40.0]).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').
- *section*: The cross-section size of a member (width x depth).

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C'
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, layer S-COL.BON, handle 34D
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, layer S-COL.BON, handle 359
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, layer S-COL.BON, handle 347
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, layer S-COL.BON, handle 34A
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, layer S-COL.BON, handle 356

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (column)" (PDF page 9)
- FIND (Ctrl+F) the text "C" - match whole word
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)
- Select by handle: type (command "_.SELECT" (handent "34D") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- LAYISO the layer "S-COL.BON" to see only that information (LAYUNISO to restore)
- ZOOM to about X=2088, Y=7412 (sheet-local mm)
- Select by handle: type (command "_.SELECT" (handent "359") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=14088, Y=7412 (sheet-local mm)
- Select by handle: type (command "_.SELECT" (handent "347") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=33158, Y=7512 (sheet-local mm)
- Select by handle: type (command "_.SELECT" (handent "34A") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=1988, Y=13812 (sheet-local mm)
- Select by handle: type (command "_.SELECT" (handent "356") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- ZOOM to about X=4788, Y=13912 (sheet-local mm)

**What would each answer change?**
- if *schedule section (storey band)*: current quantity stands
- if *drawn outline*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For column type C: does the schedule section (storey band) govern, or the drawn outline ([20.0, 50.0] vs [20.0, 40.0])?"

## STR-COL-022

**What does this mean?** Two places on the drawings say different things about the same thing. 1 column occurrence(s) of type P.C: schedule section (storey band) differs from drawn outline ([20, 50] vs [20.0, 40.0]).

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *band*: A range in a detailing rule (for example 'column long side between 50 and 80 cm').
- *section*: The cross-section size of a member (width x depth).

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'P.C'
- ST7757.dxf, p.6, SECOND FLOOR ROOF SLAB, layer S-COL.BON, handle 778

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (column)" (PDF page 9)
- FIND (Ctrl+F) the text "P.C" - match whole word
- Open the sheet titled "SECOND FLOOR ROOF SLAB" (PDF page 6)
- Select by handle: type (command "_.SELECT" (handent "778") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- LAYISO the layer "S-COL.BON" to see only that information (LAYUNISO to restore)
- ZOOM to about X=24888, Y=15994 (sheet-local mm)

**What would each answer change?**
- if *schedule section (storey band)*: current quantity stands
- if *drawn outline*: concrete / formwork / bars follow it; the other source needs revision

**What should I ask the engineering office?** "For column type P.C: does the schedule section (storey band) govern, or the drawn outline ([20, 50] vs [20.0, 40.0])?"

## STR-COL-023

**What does this mean?** Two places on the drawings say different things about the same thing. 10 column occurrence(s) (C, C1, C2) at GF: schedule gives 20.0 cm but minimum column thickness for the storey height (p.9) requires at least 25.

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *section*: The cross-section size of a member (width x depth).

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.pdf, p.9, rule P9-COL-TMIN, handle 1BEF

**What should I search in AutoCAD?**
- Open the sheet titled "rule P9-COL-TMIN" (PDF page 9)
- Select by handle: type (command "_.SELECT" (handent "1BEF") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *schedule is correct*: no quantity change
- if *increase to 25*: concrete, formwork and ties increase

**What should I ask the engineering office?** "The schedule gives 20.0 where the general rule asks for at least 25. Is the schedule correct, or must the section increase?"

## STR-DOM-001

**What does this mean?** A rule or note exists but it is not clear where or how it applies. 8 dome occurrence(s) depend on P7-DOME (Dome reinforcement.), whose applicability is not established (CANDIDATE).

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf, p.7, DETAILS (pool / dome), 'DETAIL OF DOME'
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, 'SEE DETAIL'

**What should I search in AutoCAD?**
- Open the sheet titled "DETAILS (pool / dome)" (PDF page 7)
- FIND (Ctrl+F) the text "DETAIL OF DOME" - match whole word
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- FIND (Ctrl+F) the text "SEE DETAIL" - match whole word

**What would each answer change?**
- if *yes*: dome zones use 100 mm
- if *no*: per answer

**What should I ask the engineering office?** "Does the dome detail (100 mm shell, ring beam) apply to both domes on the first-floor roof?"

## STR-FOO-001

**What does this mean?** A rule or note exists but it is not clear where or how it applies. The schedule field 'BOXED' is printed for 11 type(s) (e.g. F=3+4, F10=3+5, F11=3+8, F15=3+4) but its meaning is not stated.

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *footing*: The concrete pad under a column that spreads its load into the ground.
- *boxed*: A footing note describing an extra cage or box of bars; its meaning must come from the engineer.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.9, schedule (footing), 'BOXED'

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (footing)" (PDF page 9)
- FIND (Ctrl+F) the text "BOXED" - match whole word

**What would each answer change?**
- if *box / cage bars: a + b bars in the two directions*: extra bar set per footing
- if *top mesh counts*: a top layer is added
- if *column starter / dowel count*: starter bars only

**What should I ask the engineering office?** "What does the schedule field 'BOXED' mean (bar count, bar size, shape and position)?"

## STR-FOO-002

**What does this mean?** A rule or note exists but it is not clear where or how it applies. Schedule row F7 (footing) is defined but no plan occurrence carries this mark.

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *footing*: The concrete pad under a column that spreads its load into the ground.

**Why does it matter?** No quantity changes with the answer; it is recorded for completeness.

**Where should I look?**
- ST7757.dxf / ST7757.pdf, p.9, schedule (footing), handle 1CCC, 'F7'

**What should I search in AutoCAD?**
- Open the sheet titled "schedule (footing)" (PDF page 9)
- FIND (Ctrl+F) the text "F7" - match whole word
- Select by handle: type (command "_.SELECT" (handent "1CCC") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *unused*: no change
- if *used at a location*: occurrence(s) added there

**What should I ask the engineering office?** "Schedule row F7 has no occurrence on the plans. Is it unused, or is a mark missing on a plan?"

## STR-FOO-003

**What does this mean?** A size or length needed to measure this is not given. 26 footing occurrence(s) depend on P13-FOOTING-DEEP (Where the upper ground beam is more than 2.5 m above the footing, an additional LOWER ground beam is provided.), whose dimension is not established (BLOCKED_METHOD).

**Words used here:**
- *footing*: The concrete pad under a column that spreads its load into the ground.
- *ground beam*: A beam at ground level, usually under walls, between footings or columns.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.13, rule P13-FOOTING-DEEP
- ST7757.pdf, p.9, rule P9-SOIL, handle 1E11

**What should I search in AutoCAD?**
- Open the sheet titled "rule P13-FOOTING-DEEP" (PDF page 13)
- Open the sheet titled "rule P9-SOIL" (PDF page 9)
- Select by handle: type (command "_.SELECT" (handent "1E11") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *difference <= 2.5 m*: no lower ground beam
- if *difference > 2.5 m*: lower ground beams added

**What should I ask the engineering office?** "What is the founding level? (A lower ground beam is required where the ground beam is more than 2.5 m above the footing.)"

## STR-FOO-004

**What does this mean?** Two places on the drawings say different things about the same thing. Two footing outlines overlap by 0.14 m2 plan.

**Words used here:**
- *footing*: The concrete pad under a column that spreads its load into the ground.

**Why does it matter?** The quantity uses the engine's current interpretation; an answer may change it.

**Where should I look?**
- ST7757.dxf, p.2, FOUNDATION PLAN, handle 180F
- ST7757.dxf, p.2, FOUNDATION PLAN, handle 180C

**What should I search in AutoCAD?**
- Open the sheet titled "FOUNDATION PLAN" (PDF page 2)
- Select by handle: type (command "_.SELECT" (handent "180F") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- Select by handle: type (command "_.SELECT" (handent "180C") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *separate*: deduct the overlap once
- if *combined*: one member; redefine its size

**What should I ask the engineering office?** "Are these two separate members or one combined member?"

## STR-FOO-005

**What does this mean?** Two places on the drawings say different things about the same thing. One drawn footing carries 2 different type marks (F, F10); one outline holding columns C, C10.

**Words used here:**
- *footing*: The concrete pad under a column that spreads its load into the ground.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.dxf, p.2, FOUNDATION PLAN, layer S-FOOTINGS, handle 1B1B
- ST7757.dxf, p.2, FOUNDATION PLAN, handle 10A5, 'F'
- ST7757.dxf, p.2, FOUNDATION PLAN, handle 168B, 'F10'

**What should I search in AutoCAD?**
- Open the sheet titled "FOUNDATION PLAN" (PDF page 2)
- Select by handle: type (command "_.SELECT" (handent "1B1B") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- LAYISO the layer "S-FOOTINGS" to see only that information (LAYUNISO to restore)
- FIND (Ctrl+F) the text "F" - match whole word
- Select by handle: type (command "_.SELECT" (handent "10A5") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- FIND (Ctrl+F) the text "F10" - match whole word
- Select by handle: type (command "_.SELECT" (handent "168B") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *F*: size and bars from F
- if *F10*: size and bars from F10
- if *two separate members*: split the outline; both rows apply

**What should I ask the engineering office?** "This footing is marked F and F10. Which type is it - or is it two members drawn as one?"

## STR-GRO-001

**What does this mean?** A size or length needed to measure this is not given. 21 ground slab occurrence(s) depend on P3-GROUND-SLAB (Ground slab note: 10 cm, 5Ø10/m each way.), whose extent is not established (CANDIDATE).

**Words used here:**
- *slab*: A flat concrete floor or roof plate.

**Why does it matter?** Only the part that is certain is counted; the total is a minimum until this is answered.

**Where should I look?**
- ST7757.pdf, p.3, rule P3-GROUND-SLAB

**What should I search in AutoCAD?**
- Open the sheet titled "rule P3-GROUND-SLAB" (PDF page 3)

**What would each answer change?**
- if *all cells inside the building*: 167.636 m2 plan
- if *only marked cells*: smaller area

**What should I ask the engineering office?** "Which areas receive the 10 cm ground slab (5Ø10/m each way): every cell inside the ground beams, or only the cells marked with the note?"

## STR-LIF-001

**What does this mean?** A size or length needed to measure this is not given. 1 lift pit occurrence(s) depend on P14-LIFT (Lift pit on the FF raft: 20 cm walls with 6Ø12/m and 6Ø16/m, pit depth by the lift manufacturer.), whose dimension is not established (BLOCKED_METHOD).

**Words used here:**
- *footing*: The concrete pad under a column that spreads its load into the ground.
- *lift*: Elevator.
- *pit*: The pit below the lowest stop of an elevator.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.14, rule P14-LIFT

**What should I search in AutoCAD?**
- Open the sheet titled "rule P14-LIFT" (PDF page 14)

**What would each answer change?**
- if *depth given*: pit walls measured

**What should I ask the engineering office?** "What is the lift-pit depth below the lift footing (manufacturer / engineer)?"

## STR-LIF-002

**What does this mean?** Something is required by a note or rule but is not drawn or detailed. Lift tie beams at 3.00 m height around the lift shaft when the storey is higher than 4.30 m. requires lift tie beam (storey height > 4.30 m) but none is drawn.

**Words used here:**
- *tie*: A closed loop of thin steel bar that wraps the main vertical bars of a column (also called a link or stirrup). Ties stop the main bars buckling; their number decides how much small-diameter steel is needed.
- *lift*: Elevator.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.8, rule P8-N19

**What should I search in AutoCAD?**
- Open the sheet titled "rule P8-N19" (PDF page 8)

**What would each answer change?**
- if *positions + size given*: occurrences created
- if *not required here*: population closed as not applicable

**What should I ask the engineering office?** "Lift tie beams at 3.00 m height around the lift shaft when the storey is higher than 4.30 m.: where are these lift tie beams, and what size and bars?"

## STR-LIN-001

**What does this mean?** Something is required by a note or rule but is not drawn or detailed. Lintels by opening width; width = wall width; 40 cm minimum bearing each side. requires lintel (one lintel per architectural opening, type by opening width) but none is drawn.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.13, rule P13-LINTEL

**What should I search in AutoCAD?**
- Open the sheet titled "rule P13-LINTEL" (PDF page 13)

**What would each answer change?**
- if *positions + size given*: occurrences created
- if *not required here*: population closed as not applicable

**What should I ask the engineering office?** "Lintels by opening width; width = wall width; 40 cm minimum bearing each side.: where are these lintels, and what size and bars?"

## STR-PAR-001

**What does this mean?** A size or length needed to measure this is not given. 3 parapets: parapet height / length follow the architectural drawings (not on the structural set).

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, 'PARAPET, BEFORE CASTING'
- ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, 'PARAPET, BEFORE CASTING'
- ST7757.dxf, p.6, SECOND FLOOR ROOF SLAB, 'PARAPET, BEFORE CASTING'

**What should I search in AutoCAD?**
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)
- FIND (Ctrl+F) the text "PARAPET, BEFORE CASTING" - match whole word
- Open the sheet titled "FIRST FLOOR ROOF SLAB" (PDF page 5)
- Open the sheet titled "SECOND FLOOR ROOF SLAB" (PDF page 6)

**What would each answer change?**

**What should I ask the engineering office?** "Give the parapet height and the roof edges that carry a parapet."

## STR-PLA-001

**What does this mean?** A rule or note exists but it is not clear where or how it applies. 3 planted column occurrence(s) depend on P15-PLANTED (Beam carrying a planted column: 4Ø16 extra, column bars anchored 100 into the beam.), whose applicability is not established (CANDIDATE).

**Words used here:**
- *tie*: A closed loop of thin steel bar that wraps the main vertical bars of a column (also called a link or stirrup). Ties stop the main bars buckling; their number decides how much small-diameter steel is needed.
- *planted column*: A column that starts on a beam or slab instead of continuing from a column below.

**Why does it matter?** Only the part that is certain is counted; the total is a minimum until this is answered.

**Where should I look?**
- ST7757.pdf, p.15, rule P15-PLANTED

**What should I search in AutoCAD?**
- Open the sheet titled "rule P15-PLANTED" (PDF page 15)

**What would each answer change?**
- if *yes*: detail extras added
- if *no*: plain column only

**What should I ask the engineering office?** "Does the p.15 detail (Beam carrying a planted column: 4Ø16 extra, column bars anchored 100 into the beam.) apply to each of these columns, and do they use the normal tie bands?"

## STR-POO-001

**What does this mean?** A size or length needed to measure this is not given. pool SPC-POOL: pool lengths and depths are 'AS PER ARCH' on the detail.

**Words used here:**
- *section*: The cross-section size of a member (width x depth).

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.dxf, p.7, DETAILS (pool / dome), 'DETAIL OF SWIMMING POOL'
- ST7757.dxf, p.3, GROUND BEAMS PLAN, 'swimming pool'

**What should I search in AutoCAD?**
- Open the sheet titled "DETAILS (pool / dome)" (PDF page 7)
- FIND (Ctrl+F) the text "DETAIL OF SWIMMING POOL" - match whole word
- Open the sheet titled "GROUND BEAMS PLAN" (PDF page 3)
- FIND (Ctrl+F) the text "swimming pool" - match whole word

**What would each answer change?**

**What should I ask the engineering office?** "Provide the pool plan and section (lengths, depths, slope) from the architect."

## STR-PRO-001

**What does this mean?** Two places on the drawings say different things about the same thing. boundary wall definition: P14-BOUNDARY says TYPICAL BOUNDARY WALL: (20x30) R.C columns 4Ø14; GROUND BEAM (20x40); 2Ø14 (T&B); Ø8/20 STIRRUPS; 3Ø16 (T&B); 7Ø12; 4Ø12, schedule row B.W says 20x60 ['4', '16'].

**Words used here:**
- *schedule*: A table on the drawings that defines each member type once (size and bars). The plan then shows where each type occurs. The schedule alone never tells you how many there are.
- *ground beam*: A beam at ground level, usually under walls, between footings or columns.
- *t&b*: Top and bottom - the same bars are placed in both the upper and the lower layer.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.14, rule P14-BOUNDARY
- ST7757.dxf / ST7757.pdf, p.10, schedule (simple beam), 'B.W'

**What should I search in AutoCAD?**
- Open the sheet titled "rule P14-BOUNDARY" (PDF page 14)
- Open the sheet titled "schedule (simple beam)" (PDF page 10)
- FIND (Ctrl+F) the text "B.W" - match whole word

**What would each answer change?**
- if *TYPICAL BOUNDARY WALL: (20x30) R.C columns 4Ø14; GROUND BEAM (20x40); 2Ø14 (T&B); Ø8/20 STIRRUPS; 3Ø16 (T&B); 7Ø12; 4Ø12*: P14-BOUNDARY
- if *20x60 ['4', '16']*: schedule row B.W

**What should I ask the engineering office?** "boundary wall definition: which value governs, TYPICAL BOUNDARY WALL: (20x30) R.C columns 4Ø14; GROUND BEAM (20x40); 2Ø14 (T&B); Ø8/20 STIRRUPS; 3Ø16 (T&B); 7Ø12; 4Ø12 or 20x60 ['4', '16']?"

## STR-PRO-002

**What does this mean?** Two places on the drawings say different things about the same thing. formwork rule: P8-N17 says formwork >= 14 days, P1-NOTE-C says formwork >= 21 days.

**Why does it matter?** No quantity changes with the answer; it is recorded for completeness.

**Where should I look?**
- ST7757.pdf, p.8, rule P8-N17
- ST7757.pdf, p.1, rule P1-NOTE-C, handle 7E

**What should I search in AutoCAD?**
- Open the sheet titled "rule P8-N17" (PDF page 8)
- Open the sheet titled "rule P1-NOTE-C" (PDF page 1)
- Select by handle: type (command "_.SELECT" (handent "7E") "") then ZOOM Object, or use the 'Handle' field in Quick Properties

**What would each answer change?**
- if *formwork >= 14 days*: P8-N17
- if *formwork >= 21 days*: P1-NOTE-C

**What should I ask the engineering office?** "formwork rule: which value governs, formwork >= 14 days or formwork >= 21 days?"

## STR-SLA-001

**What does this mean?** A rule or note exists but it is not clear where or how it applies. 49 slab occurrence(s) depend on P4-6-NOTE-2 (Top steel 5Ø10/m over beams for the slabs, length one third of the span, in both directions.), whose applicability is not established (CANDIDATE).

**Words used here:**
- *span*: The length of a beam between two supports.
- *slab*: A flat concrete floor or roof plate.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.4, rule P4-6-NOTE-2, handle D8
- ST7757.pdf, p.15, rule P15-SLAB-ON-BEAMS

**What should I search in AutoCAD?**
- Open the sheet titled "rule P4-6-NOTE-2" (PDF page 4)
- Select by handle: type (command "_.SELECT" (handent "D8") "") then ZOOM Object, or use the 'Handle' field in Quick Properties
- Open the sheet titled "rule P15-SLAB-ON-BEAMS" (PDF page 15)

**What would each answer change?**
- if *minimum where no top bar drawn*: added only where missing
- if *replaces p.15*: one rule for all supports
- if *both apply*: both bar sets

**What should I ask the engineering office?** "The plan note asks for 5Ø10/m top bars over beams for one third of the span, and p.15 gives top-bar extensions of 0.25L / 0.30L. Is the plan note a minimum where no top bar is drawn, or does it replace p.15?"

## STR-SLA-002

**What does this mean?** A drawing rule does not cover this exact case (for example a value sits exactly on a limit). temperature reinforcement table (p.15) has no row for 160 mm (47 element(s)); rows are [100, 125, 150, 175, 200, 250, 300].

**Words used here:**
- *slab*: A flat concrete floor or roof plate.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.15, rule P15-TEMP-TABLE

**What should I search in AutoCAD?**
- Open the sheet titled "rule P15-TEMP-TABLE" (PDF page 15)

**What would each answer change?**
- if *row 150*: use the lower row
- if *row 175*: use the next higher row
- if *a stated value*: use the consultant's value

**What should I ask the engineering office?** "temperature reinforcement table (p.15): which value applies for 160 mm?"

## STR-SLA-003

**What does this mean?** A drawing rule does not cover this exact case (for example a value sits exactly on a limit). temperature reinforcement table (p.15) has no row for 180 mm (2 element(s)); rows are [100, 125, 150, 175, 200, 250, 300].

**Words used here:**
- *slab*: A flat concrete floor or roof plate.

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.15, rule P15-TEMP-TABLE

**What should I search in AutoCAD?**
- Open the sheet titled "rule P15-TEMP-TABLE" (PDF page 15)

**What would each answer change?**
- if *row 175*: use the lower row
- if *row 200*: use the next higher row
- if *a stated value*: use the consultant's value

**What should I ask the engineering office?** "temperature reinforcement table (p.15): which value applies for 180 mm?"

## STR-STA-001

**What does this mean?** A rule or note exists but it is not clear where or how it applies. 5 stair occurrence(s) depend on P16-STAIR (Typical stair and stair-beam reinforcement (N.T.S.).), whose applicability is not established (BLOCKED_METHOD).

**Why does it matter?** Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where should I look?**
- ST7757.pdf, p.16, rule P16-STAIR
- ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB

**What should I search in AutoCAD?**
- Open the sheet titled "rule P16-STAIR" (PDF page 16)
- Open the sheet titled "GROUND FLOOR ROOF SLAB" (PDF page 4)

**What would each answer change?**
- if *typical detail applies*: stair bars from p.16 per flight
- if *stair-specific detail*: needs the stair drawing

**What should I ask the engineering office?** "Does the typical stair detail (p.16) apply to each stair on the plans, including the stair inside the void? Please give flight / landing levels and waist thickness."

## STR-TUR-001

**What does this mean?** A rule or note exists but it is not clear where or how it applies. 2 turn column occurrence(s) depend on P15-TWISTED (Twisted (turned) column: spiral ties 6Ø8/m over 1 m each side of the floor, 4Ø16 extra.), whose applicability is not established (CANDIDATE).

**Words used here:**
- *tie*: A closed loop of thin steel bar that wraps the main vertical bars of a column (also called a link or stirrup). Ties stop the main bars buckling; their number decides how much small-diameter steel is needed.

**Why does it matter?** Only the part that is certain is counted; the total is a minimum until this is answered.

**Where should I look?**
- ST7757.pdf, p.15, rule P15-TWISTED

**What should I search in AutoCAD?**
- Open the sheet titled "rule P15-TWISTED" (PDF page 15)

**What would each answer change?**
- if *yes*: detail extras added
- if *no*: plain column only

**What should I ask the engineering office?** "Does the p.15 detail (Twisted (turned) column: spiral ties 6Ø8/m over 1 m each side of the floor, 4Ø16 extra.) apply to each of these columns, and do they use the normal tie bands?"

