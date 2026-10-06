# Alsenan - consultant questions (generated from open engineering flags)

Each block is generated from the flag's source context. Answers are stored as PROJECT claims (ALSENAN_PROJECT_CLAIMS.json), never as engine rules.

## STR-BEA-001

**Issue:** P13 ground-beam typical details (<2.5 / <5 / >5 m): 9 beam(s) change class depending on the length basis (centre-to-centre / clear span).

**Why it matters:** A rule or note exists but it is not clear where or how it applies. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 26.899 m beam (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf, GROUND BEAMS PLAN, p.3; ST7757.pdf, ground beam details, p.13

**Engine's current interpretation:** none - held back

**Question:** "P13 ground-beam typical details (<2.5 / <5 / >5 m): is the length measured centre-to-centre or clear span?"

**Impact:** BLOCKED - CONCRETE, FORMWORK, REINFORCEMENT; 9 element(s); 26.899 m beam

## STR-BEA-002

**Issue:** Schedule row B.W (beam) is defined but no plan occurrence carries this mark.

**Why it matters:** A rule or note exists but it is not clear where or how it applies. No quantity changes with the answer; it is recorded for completeness.

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (simple beam), p.10

**Current evidence:**
- schedule row: 20x60

**Engine's current interpretation:** zero occurrences (a schedule row never creates an occurrence) (authority: PLAN_MEMBER_TAG)

**Question:** "Schedule row B.W has no occurrence on the plans. Is it unused, or is a mark missing on a plan?"

**Impact:** NO_QUANTITY_IMPACT - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s)

## STR-BEA-003

**Issue:** Schedule row B10 (beam) is defined but no plan occurrence carries this mark.

**Why it matters:** A rule or note exists but it is not clear where or how it applies. No quantity changes with the answer; it is recorded for completeness.

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (simple beam), p.10

**Current evidence:**
- schedule row: 20x75

**Engine's current interpretation:** zero occurrences (a schedule row never creates an occurrence) (authority: PLAN_MEMBER_TAG)

**Question:** "Schedule row B10 has no occurrence on the plans. Is it unused, or is a mark missing on a plan?"

**Impact:** NO_QUANTITY_IMPACT - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s)

## STR-BEA-004

**Issue:** Schedule row B12 (beam) is defined but no plan occurrence carries this mark.

**Why it matters:** A rule or note exists but it is not clear where or how it applies. No quantity changes with the answer; it is recorded for completeness.

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (simple beam), p.10

**Current evidence:**
- schedule row: 25x75

**Engine's current interpretation:** zero occurrences (a schedule row never creates an occurrence) (authority: PLAN_MEMBER_TAG)

**Question:** "Schedule row B12 has no occurrence on the plans. Is it unused, or is a mark missing on a plan?"

**Impact:** NO_QUANTITY_IMPACT - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s)

## STR-BEA-005

**Issue:** 16 beam occurrence(s) depend on P8-N21 (Side bars 2Ø12 / 3Ø12 / 4Ø12 in beams deeper than 60 cm, according to the beam width, unless stated otherwise.), whose method is not established (BLOCKED_METHOD).

**Why it matters:** The drawings give the requirement but not the method to measure it; the engineer must state the method. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 86.389 m beam (REINFORCEMENT).

**Where to look:** ST7757.pdf, rule P8-N21, p.8

**Current evidence:**
- P8-N21: Side bars 2Ø12 / 3Ø12 / 4Ø12 in beams deeper than 60 cm, according to the beam width, unless stated otherwise.

**Engine's current interpretation:** occurrences counted; quantities depending on the rule held back

**Question:** "Beams deeper than 60 cm without side bars in their schedule row (CB1, CB11, CB12, CB3, CB6, CB7, CB8): how many 12 mm side bars per face?"

**Impact:** BLOCKED - REINFORCEMENT; 16 element(s); 86.389 m beam

## STR-BEA-006

**Issue:** 2 beams: curved ground-beam span - support length not measured.

**Why it matters:** A size or length needed to measure this is not given. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 8.093 m beam (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf, GROUND BEAMS PLAN, p.3

**Engine's current interpretation:** occurrence counted; measurement held back

**Question:** "Confirm the curved ground beam's supports and length (pool edge)."

**Impact:** BLOCKED - CONCRETE, FORMWORK, REINFORCEMENT; 2 element(s); 8.093 m beam

## STR-BEA-007

**Issue:** 113 beam occurrence(s) depend on P8-N11 (Beams crossed by service pipes are widened by 5 cm.), whose extent is not established (BLOCKED_METHOD).

**Why it matters:** A size or length needed to measure this is not given. Only the part that is certain is counted; the total is a minimum until this is answered. Affected: 389.327 m beam (CONCRETE, FORMWORK).

**Where to look:** ST7757.pdf, rule P8-N11, p.8

**Current evidence:**
- P8-N11: Beams crossed by service pipes are widened by 5 cm.

**Engine's current interpretation:** occurrences counted; quantities depending on the rule held back

**Question:** "Which beams are crossed by service pipes (drainage, water, electrical, AC) and must be widened by 5 cm?"

**Impact:** LOWER_BOUND - CONCRETE, FORMWORK; 113 element(s); 389.327 m beam

## STR-BEA-008

**Issue:** 6 beam member(s) at 1F_ROOF are drawn without a type mark (dome ring (curved)).

**Why it matters:** This member has no schedule row, so its size and bars are not defined. The affected quantity is shown for checking but not counted in totals. Affected: 9.521 m beam (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf, FIRST FLOOR ROOF SLAB, p.5

**Engine's current interpretation:** geometry counted; size and bars unknown

**Question:** "These beam members at 1F_ROOF carry no mark. Which type is each (or are they not structural members)?"

**Impact:** AUDIT_ONLY - CONCRETE, FORMWORK, REINFORCEMENT; 6 element(s); 9.521 m beam

## STR-BEA-009

**Issue:** 13 beam member(s) at 1F_ROOF are drawn without a type mark (no mark).

**Why it matters:** This member has no schedule row, so its size and bars are not defined. The affected quantity is shown for checking but not counted in totals. Affected: 46.021 m beam (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf, FIRST FLOOR ROOF SLAB, p.5

**Engine's current interpretation:** geometry counted; size and bars unknown

**Question:** "These beam members at 1F_ROOF carry no mark. Which type is each (or are they not structural members)?"

**Impact:** AUDIT_ONLY - CONCRETE, FORMWORK, REINFORCEMENT; 13 element(s); 46.021 m beam

## STR-BEA-010

**Issue:** 1 beam member(s) at 2F_ROOF are drawn without a type mark (no mark).

**Why it matters:** This member has no schedule row, so its size and bars are not defined. The affected quantity is shown for checking but not counted in totals. Affected: 3.25 m beam (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf, SECOND FLOOR ROOF SLAB, p.6

**Engine's current interpretation:** geometry counted; size and bars unknown

**Question:** "These beam members at 2F_ROOF carry no mark. Which type is each (or are they not structural members)?"

**Impact:** AUDIT_ONLY - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s); 3.25 m beam

## STR-BEA-011

**Issue:** 5 beam member(s) at GF_ROOF are drawn without a type mark (no mark).

**Why it matters:** This member has no schedule row, so its size and bars are not defined. The affected quantity is shown for checking but not counted in totals. Affected: 11.489 m beam (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf, GROUND FLOOR ROOF SLAB, p.4

**Engine's current interpretation:** geometry counted; size and bars unknown

**Question:** "These beam members at GF_ROOF carry no mark. Which type is each (or are they not structural members)?"

**Impact:** AUDIT_ONLY - CONCRETE, FORMWORK, REINFORCEMENT; 5 element(s); 11.489 m beam

## STR-BEA-012

**Issue:** 1 beam occurrence(s) of type B21: schedule width (cm) differs from drawn width (cm) (45.0 vs 40.0).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 7.768 m beam (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (simple beam), p.10; ST7757.dxf, GROUND FLOOR ROOF SLAB, p.4

**Current evidence:**
- schedule width (cm): 45.0 (ST7757.dxf / ST7757.pdf, p.10, schedule (simple beam), 'B21')
- drawn width (cm): 40.0 (ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 468, 'B21')

**Engine's current interpretation:** 45.0 (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For beam type B21: does the schedule width (cm) govern, or the drawn width (cm) (45.0 vs 40.0)?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s); 7.768 m beam

## STR-BEA-013

**Issue:** 1 beam occurrence(s) of type B29: schedule width (cm) differs from drawn width (cm) (25.0 vs 20.0).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 7.21 m beam (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (simple beam), p.10; ST7757.dxf, GROUND FLOOR ROOF SLAB, p.4

**Current evidence:**
- schedule width (cm): 25.0 (ST7757.dxf / ST7757.pdf, p.10, schedule (simple beam), 'B29')
- drawn width (cm): 20.0 (ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 465, 'B29')

**Engine's current interpretation:** 25.0 (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For beam type B29: does the schedule width (cm) govern, or the drawn width (cm) (25.0 vs 20.0)?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s); 7.21 m beam

## STR-BEA-014

**Issue:** 1 beam occurrence(s) of type B6: schedule width (cm) differs from drawn width (cm) (25.0 vs 20.0).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 4.729 m beam (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (simple beam), p.10; ST7757.dxf, FIRST FLOOR ROOF SLAB, p.5

**Current evidence:**
- schedule width (cm): 25.0 (ST7757.dxf / ST7757.pdf, p.10, schedule (simple beam), 'B6')
- drawn width (cm): 20.0 (ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, handle 6C5, 'B6')

**Engine's current interpretation:** 25.0 (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For beam type B6: does the schedule width (cm) govern, or the drawn width (cm) (25.0 vs 20.0)?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s); 4.729 m beam

## STR-BEA-015

**Issue:** 2 beam occurrence(s) of type CB10: schedule width (cm) differs from drawn width (cm) (25.0 vs 20.0).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 7.025 m beam (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (simple beam), p.10; ST7757.dxf, FIRST FLOOR ROOF SLAB, p.5

**Current evidence:**
- schedule width (cm): 25.0 (ST7757.dxf / ST7757.pdf, p.10, schedule (simple beam), 'CB10')
- drawn width (cm): 20.0 (ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, handle 717, 'CB10')

**Engine's current interpretation:** 25.0 (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For beam type CB10: does the schedule width (cm) govern, or the drawn width (cm) (25.0 vs 20.0)?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 2 element(s); 7.025 m beam

## STR-BEA-016

**Issue:** 2 beam occurrence(s) of type CB2: schedule width (cm) differs from drawn width (cm) (20.0 vs 25.0).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 7.77 m beam (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (simple beam), p.10; ST7757.dxf, GROUND FLOOR ROOF SLAB, p.4

**Current evidence:**
- schedule width (cm): 20.0 (ST7757.dxf / ST7757.pdf, p.10, schedule (simple beam), 'CB2')
- drawn width (cm): 25.0 (ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, handle 42A, 'CB2')

**Engine's current interpretation:** 20.0 (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For beam type CB2: does the schedule width (cm) govern, or the drawn width (cm) (20.0 vs 25.0)?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 2 element(s); 7.77 m beam

## STR-BEA-017

**Issue:** One drawn beam carries 2 different type marks (CB3, B3); both marks sit on the same drawn span.

**Why it matters:** Two places on the drawings say different things about the same thing. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 3.35 m beam (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf, GROUND FLOOR ROOF SLAB, p.4

**Current evidence:**
- mark 1: CB3
- mark 2: B3

**Engine's current interpretation:** none - held back

**Question:** "This beam is marked CB3 and B3. Which type is it - or is it two members drawn as one?"

**Impact:** BLOCKED - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s); 3.35 m beam

## STR-BEA-018

**Issue:** beam CB4: schedule spans [3.3, 3.7] but plan spans [2.724, 3.75] (SPAN_LENGTH_CONFLICT).

**Why it matters:** Two places on the drawings say different things about the same thing. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 6.474 m beam (REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (continuous beam), p.11; ST7757.dxf, GROUND FLOOR ROOF SLAB, p.4

**Current evidence:**
- schedule spans: [3.3, 3.7]
- plan spans: [2.724, 3.75]

**Engine's current interpretation:** none - held back

**Question:** "Which plan members form CB4 (schedule spans [3.3, 3.7])?"

**Impact:** BLOCKED - REINFORCEMENT; 1 element(s); 6.474 m beam

## STR-BEA-019

**Issue:** beam CB5: schedule spans [2.5, 4.5] but plan spans [2.85] (SPAN_COUNT_CONFLICT).

**Why it matters:** Two places on the drawings say different things about the same thing. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 2.85 m beam (REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (continuous beam), p.11; ST7757.dxf, GROUND FLOOR ROOF SLAB, p.4

**Current evidence:**
- schedule spans: [2.5, 4.5]
- plan spans: [2.85]

**Engine's current interpretation:** none - held back

**Question:** "Which plan members form CB5 (schedule spans [2.5, 4.5])?"

**Impact:** BLOCKED - REINFORCEMENT; 1 element(s); 2.85 m beam

## STR-BEA-020

**Issue:** beam CB5: schedule spans [2.5, 4.5] but plan spans [4.2] (SPAN_COUNT_CONFLICT).

**Why it matters:** Two places on the drawings say different things about the same thing. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 4.2 m beam (REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (continuous beam), p.11; ST7757.dxf, GROUND FLOOR ROOF SLAB, p.4

**Current evidence:**
- schedule spans: [2.5, 4.5]
- plan spans: [4.2]

**Engine's current interpretation:** none - held back

**Question:** "Which plan members form CB5 (schedule spans [2.5, 4.5])?"

**Impact:** BLOCKED - REINFORCEMENT; 1 element(s); 4.2 m beam

## STR-BEA-021

**Issue:** beam CB8: schedule spans [3.7, 6.4, 6.8] but plan spans [6.545, 6.95] (SPAN_COUNT_CONFLICT).

**Why it matters:** Two places on the drawings say different things about the same thing. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 13.495 m beam (REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (continuous beam), p.11; ST7757.dxf, GROUND FLOOR ROOF SLAB, p.4

**Current evidence:**
- schedule spans: [3.7, 6.4, 6.8]
- plan spans: [6.545, 6.95]

**Engine's current interpretation:** would match if extended: [3.825, 6.545, 6.95]

**Question:** "Which plan members form CB8 (schedule spans [3.7, 6.4, 6.8])?"

**Impact:** BLOCKED - REINFORCEMENT; 1 element(s); 13.495 m beam

## STR-BEA-022

**Issue:** Schedule key SB2 is defined 2 times with different values.

**Why it matters:** Two places on the drawings say different things about the same thing. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 5.11 m beam (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (strap beam), p.10

**Current evidence:**
- row 2ABA: {'BOT-B': '10', 'BOT-D': '16', 'D': '8', 'H': '50', 'STI-B': '10', 'TOP-B': '20', 'TOP-D': '18', 'W': '100'}
- row 1FBB: {'BOT-B': '10', 'BOT-D': '18', 'D': '8', 'H': '50', 'STI-B': '10', 'TOP-B': '10', 'TOP-D': '18', 'W': '80'}

**Engine's current interpretation:** drawn width 987 mm fits B = 100 cm (geometry hint only, not applied)

**Question:** "Schedule key SB2 appears twice. Which row is valid?"

**Impact:** BLOCKED - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s); 5.11 m beam

## STR-BEA-023

**Issue:** Mark B6 sits between 3 members at similar distance; the member it names is not certain.

**Why it matters:** A member drawn on the plan cannot be tied to one type mark with certainty. The affected quantity is shown for checking but not counted in totals.

**Where to look:** ST7757.dxf, FIRST FLOOR ROOF SLAB, p.5

**Current evidence:**
- mark: B6
- candidate members: ['BL013', 'BA002', 'BL009']

**Engine's current interpretation:** counted as a mark occurrence; member not assigned

**Question:** "Which member does mark B6 refer to?"

**Impact:** AUDIT_ONLY - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s)

## STR-BEA-024

**Issue:** Mark B6 sits between 3 members at similar distance; the member it names is not certain.

**Why it matters:** A member drawn on the plan cannot be tied to one type mark with certainty. The affected quantity is shown for checking but not counted in totals.

**Where to look:** ST7757.dxf, FIRST FLOOR ROOF SLAB, p.5

**Current evidence:**
- mark: B6
- candidate members: ['BL031', 'BA005', 'BA006']

**Engine's current interpretation:** counted as a mark occurrence; member not assigned

**Question:** "Which member does mark B6 refer to?"

**Impact:** AUDIT_ONLY - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s)

## STR-BEA-025

**Issue:** Mark B6 sits between 3 members at similar distance; the member it names is not certain.

**Why it matters:** A member drawn on the plan cannot be tied to one type mark with certainty. The affected quantity is shown for checking but not counted in totals.

**Where to look:** ST7757.dxf, FIRST FLOOR ROOF SLAB, p.5

**Current evidence:**
- mark: B6
- candidate members: ['BA007', 'BA008', 'BL030']

**Engine's current interpretation:** counted as a mark occurrence; member not assigned

**Question:** "Which member does mark B6 refer to?"

**Impact:** AUDIT_ONLY - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s)

## STR-BEA-026

**Issue:** Mark B6 sits between 3 members at similar distance; the member it names is not certain.

**Why it matters:** A member drawn on the plan cannot be tied to one type mark with certainty. The affected quantity is shown for checking but not counted in totals.

**Where to look:** ST7757.dxf, FIRST FLOOR ROOF SLAB, p.5

**Current evidence:**
- mark: B6
- candidate members: ['BL012', 'BA003', 'BA004']

**Engine's current interpretation:** counted as a mark occurrence; member not assigned

**Question:** "Which member does mark B6 refer to?"

**Impact:** AUDIT_ONLY - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s)

## STR-BEA-027

**Issue:** Mark B1 sits between 2 members at similar distance; the member it names is not certain.

**Why it matters:** A member drawn on the plan cannot be tied to one type mark with certainty. The affected quantity is shown for checking but not counted in totals.

**Where to look:** ST7757.dxf, GROUND FLOOR ROOF SLAB, p.4

**Current evidence:**
- mark: B1
- candidate members: ['BL029', 'BL016']

**Engine's current interpretation:** counted as a mark occurrence; member not assigned

**Question:** "Which member does mark B1 refer to?"

**Impact:** AUDIT_ONLY - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s)

## STR-BEA-028

**Issue:** Mark B8 sits between 2 members at similar distance; the member it names is not certain.

**Why it matters:** A member drawn on the plan cannot be tied to one type mark with certainty. The affected quantity is shown for checking but not counted in totals.

**Where to look:** ST7757.dxf, GROUND FLOOR ROOF SLAB, p.4

**Current evidence:**
- mark: B8
- candidate members: ['BL031', 'BA004']

**Engine's current interpretation:** counted as a mark occurrence; member not assigned

**Question:** "Which member does mark B8 refer to?"

**Impact:** AUDIT_ONLY - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s)

## STR-COL-001

**Issue:** Type CN occurs only at FOUNDATION (6 occurrence(s)) while other columns continue upward.

**Why it matters:** A rule or note exists but it is not clear where or how it applies. The quantity uses the engine's current interpretation; an answer may change it. Affected: 6 nr occurrences (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (column), p.9; ST7757.dxf, FOUNDATION PLAN, p.2

**Engine's current interpretation:** counted as column occurrences at FOUNDATION only (authority: PLAN_MEMBER_TAG)

**Question:** "Is CN a column that stops at FOUNDATION, or a short stub / pedestal that belongs to the foundation item?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 6 element(s); 6 nr occurrences

## STR-COL-002

**Issue:** ST. OF COLUMN- 6Ø8/m (column ties) gives a count per metre, but 2 band(s) use more than one closed tie per level; whether the count is of tie SETS or of single ties is not stated.

**Why it matters:** A rule or note exists but it is not clear where or how it applies. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 29 nr occurrences (REINFORCEMENT).

**Where to look:** ST7757.pdf, DETAILS OF COLUMN REINFORCEMENT (schedule sheet), p.9

**Current evidence:**
- rule: ST. OF COLUMN- 6Ø8/m (column ties)
- ties per level in the multi-tie bands: {'TIE_50_LT_L_LT_80': 2, 'TIE_80_LT_L_LT_120': 3}

**Engine's current interpretation:** none - held back

**Question:** "ST. OF COLUMN- 6Ø8/m (column ties): is the per-metre count the number of tie sets (all closed ties at one level) or the number of single ties?"

**Impact:** BLOCKED - REINFORCEMENT; 29 element(s); 29 nr occurrences

## STR-COL-003

**Issue:** Type C10 (FOUNDATION), C10 (GF), C5 (FOUNDATION), C5 (GF), C6 (FOUNDATION), C6 (GF), C9 (2F) has 10 main bars but the detail sketch for its band shows 8; which bars each tie encloses is not shown.

**Why it matters:** A rule or note exists but it is not clear where or how it applies. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 11 nr occurrences (REINFORCEMENT).

**Where to look:** ST7757.pdf, DETAILS OF COLUMN REINFORCEMENT (schedule sheet), p.9

**Current evidence:**
- schedule bars: 10
- bars in band sketch: 8

**Engine's current interpretation:** none - held back

**Question:** "For C10 (FOUNDATION), C10 (GF), C5 (FOUNDATION), C5 (GF), C6 (FOUNDATION), C6 (GF), C9 (2F) (10 bars): which bars does each overlapping tie enclose?"

**Impact:** BLOCKED - REINFORCEMENT; 11 element(s); 11 nr occurrences

## STR-COL-004

**Issue:** Type C11 (FOUNDATION), C11 (GF), C9 (FOUNDATION), C9 (GF) has 14 main bars but the detail sketch for its band shows 12; which bars each tie encloses is not shown.

**Why it matters:** A rule or note exists but it is not clear where or how it applies. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 8 nr occurrences (REINFORCEMENT).

**Where to look:** ST7757.pdf, DETAILS OF COLUMN REINFORCEMENT (schedule sheet), p.9

**Current evidence:**
- schedule bars: 14
- bars in band sketch: 12

**Engine's current interpretation:** none - held back

**Question:** "For C11 (FOUNDATION), C11 (GF), C9 (FOUNDATION), C9 (GF) (14 bars): which bars does each overlapping tie enclose?"

**Impact:** BLOCKED - REINFORCEMENT; 8 element(s); 8 nr occurrences

## STR-COL-005

**Issue:** Type C1 (1F), C1 (2F), C2 (2F), C3 (1F), C3 (2F), C5 (2F) has 6 main bars but the detail sketch for its band shows 4; which bars each tie encloses is not shown.

**Why it matters:** A rule or note exists but it is not clear where or how it applies. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 10 nr occurrences (REINFORCEMENT).

**Where to look:** ST7757.pdf, DETAILS OF COLUMN REINFORCEMENT (schedule sheet), p.9

**Current evidence:**
- schedule bars: 6
- bars in band sketch: 4

**Engine's current interpretation:** none - held back

**Question:** "For C1 (1F), C1 (2F), C2 (2F), C3 (1F), C3 (2F), C5 (2F) (6 bars): which bars does each overlapping tie enclose?"

**Impact:** BLOCKED - REINFORCEMENT; 10 element(s); 10 nr occurrences

## STR-COL-006

**Issue:** Type C (FOUNDATION), C (GF), C1 (FOUNDATION), C1 (GF), C2 (1F), C2 (FOUNDATION), C2 (GF), C3 (FOUNDATION), C3 (GF), C4 (1F), C4 (FOUNDATION), C4 (GF), C5 (1F) has 8 main bars but the detail sketch for its band shows 4; which bars each tie encloses is not shown.

**Why it matters:** A rule or note exists but it is not clear where or how it applies. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 45 nr occurrences (REINFORCEMENT).

**Where to look:** ST7757.pdf, DETAILS OF COLUMN REINFORCEMENT (schedule sheet), p.9

**Current evidence:**
- schedule bars: 8
- bars in band sketch: 4

**Engine's current interpretation:** none - held back

**Question:** "For C (FOUNDATION), C (GF), C1 (FOUNDATION), C1 (GF), C2 (1F), C2 (FOUNDATION), C2 (GF), C3 (FOUNDATION), C3 (GF), C4 (1F), C4 (FOUNDATION), C4 (GF), C5 (1F) (8 bars): which bars does each overlapping tie enclose?"

**Impact:** BLOCKED - REINFORCEMENT; 45 element(s); 45 nr occurrences

## STR-COL-007

**Issue:** ST. OF COLUMN- 6Ø8/m (column ties) gives ties per metre but not over which height: full storey height, clear height below the beams, or including the joint.

**Why it matters:** The drawings give the requirement but not the method to measure it; the engineer must state the method. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 95 nr occurrences (REINFORCEMENT).

**Where to look:** ST7757.pdf, DETAILS OF COLUMN REINFORCEMENT (schedule sheet), p.9

**Current evidence:**
- rule: ST. OF COLUMN- 6Ø8/m (column ties)

**Engine's current interpretation:** none - held back

**Question:** "Over which vertical length are the column ties counted: floor-to-floor, clear height between slab and beam soffit, or clear height plus the beam-column joint?"

**Impact:** BLOCKED - REINFORCEMENT; 95 element(s); 95 nr occurrences

## STR-COL-008

**Issue:** column tie rule (arrangement by long side L): value 80.0 cm (C7) is on a limit no band includes.

**Why it matters:** A drawing rule does not cover this exact case (for example a value sits exactly on a limit). Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 3 nr occurrences (REINFORCEMENT).

**Where to look:** ST7757.pdf, DETAILS OF COLUMN REINFORCEMENT (schedule sheet), p.9

**Current evidence:**
- rule bands: ['L ≤ 50cm', '50cm < L < 80cm', '80cm < L < 120cm']
- member value: 80.0 cm

**Engine's current interpretation:** none - held back

**Question:** "column tie rule (arrangement by long side L): which band applies where the value is exactly 80.0 cm?"

**Impact:** BLOCKED - REINFORCEMENT; 3 element(s); 3 nr occurrences

## STR-COL-009

**Issue:** column at grid X04/Y01: equal-authority sources give different types (C3 vs C).

**Why it matters:** Two places on the drawings say different things about the same thing. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 2 nr occurrences (REINFORCEMENT).

**Where to look:** ST7757.dxf, COLUMN & AXIS PLAN, p.1; ST7757.dxf, FOUNDATION PLAN, p.2; ST7757.dxf, GROUND BEAMS PLAN, p.3

**Current evidence:**
- COLUMN & AXIS PLAN tag: C3 (ST7757.dxf, p.1, COLUMN & AXIS PLAN, layer S-TEXT, handle 100A, 'C3')
- GROUND BEAMS PLAN tag: C (ST7757.dxf, p.3, GROUND BEAMS PLAN, layer S-TEXT, handle 20D, 'C')

**Engine's current interpretation:** type C3 used provisionally (authority: TAG_CONFLICT)

**Question:** "Which type is correct for this column (at grid X04/Y01): C3 or C?"

**Impact:** BLOCKED - REINFORCEMENT; 2 element(s); 2 nr occurrences

## STR-COL-010

**Issue:** column at grid X12/Y02: equal-authority sources give different types (C8 vs C7).

**Why it matters:** Two places on the drawings say different things about the same thing. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 3 nr occurrences (REINFORCEMENT, CONCRETE, FORMWORK).

**Where to look:** ST7757.dxf, COLUMN & AXIS PLAN, p.1; ST7757.dxf, FOUNDATION PLAN, p.2; ST7757.dxf, GROUND BEAMS PLAN, p.3

**Current evidence:**
- COLUMN & AXIS PLAN tag: C8 (ST7757.dxf, p.1, COLUMN & AXIS PLAN, layer S-TEXT, handle 101A, 'C8')
- GROUND BEAMS PLAN tag: C7 (ST7757.dxf, p.3, GROUND BEAMS PLAN, layer S-TEXT, handle 24E, 'C7')

**Engine's current interpretation:** type C8 used provisionally (authority: TAG_CONFLICT)

**Question:** "Which type is correct for this column (at grid X12/Y02): C8 or C7?"

**Impact:** BLOCKED - REINFORCEMENT, CONCRETE, FORMWORK; 3 element(s); 3 nr occurrences

## STR-COL-011

**Issue:** column CN is drawn on FOUNDATION PLAN, GROUND BEAMS PLAN but not on COLUMN & AXIS PLAN.

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 1 nr occurrences (CONCRETE).

**Where to look:** ST7757.dxf, FOUNDATION PLAN, p.2; ST7757.dxf, GROUND BEAMS PLAN, p.3

**Current evidence:**
- drawn on: ['FOUNDATION PLAN', 'GROUND BEAMS PLAN']
- missing on: ['COLUMN & AXIS PLAN']

**Engine's current interpretation:** counted (present on the other plans) (authority: DRAWN_GEOMETRY)

**Question:** "Does this column exist (it is missing on COLUMN & AXIS PLAN)?"

**Impact:** PROVISIONAL - CONCRETE; 1 element(s); 1 nr occurrences

## STR-COL-012

**Issue:** 1 column occurrence(s) of type C1: schedule section (storey band) differs from drawn outline ([30.0, 50.0] vs [20.0, 50.0]).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 1 nr occurrences (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (column), p.9; ST7757.dxf, FOUNDATION PLAN, p.2

**Current evidence:**
- schedule section (storey band): [30.0, 50.0] (ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C1')
- drawn outline: [20.0, 50.0] (ST7757.dxf, p.2, FOUNDATION PLAN, layer S-COL.BON, handle 1099)

**Engine's current interpretation:** [30.0, 50.0] (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For column type C1: does the schedule section (storey band) govern, or the drawn outline ([30.0, 50.0] vs [20.0, 50.0])?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s); 1 nr occurrences

## STR-COL-013

**Issue:** 2 column occurrence(s) of type C2: schedule section (storey band) differs from drawn outline ([30.0, 50.0] vs [20.0, 50.0]).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 2 nr occurrences (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (column), p.9; ST7757.dxf, FOUNDATION PLAN, p.2

**Current evidence:**
- schedule section (storey band): [30.0, 50.0] (ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C2')
- drawn outline: [20.0, 50.0] (ST7757.dxf, p.2, FOUNDATION PLAN, layer S-COL.BON, handle 1096)

**Engine's current interpretation:** [30.0, 50.0] (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For column type C2: does the schedule section (storey band) govern, or the drawn outline ([30.0, 50.0] vs [20.0, 50.0])?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 2 element(s); 2 nr occurrences

## STR-COL-014

**Issue:** 4 column occurrence(s) of type C3: schedule section (storey band) differs from drawn outline ([20.0, 50.0] vs [25.0, 50.0]; [25.0, 50.0] vs [20.0, 40.0]; [25.0, 50.0] vs [20.0, 50.0]).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 4 nr occurrences (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (column), p.9; ST7757.dxf, GROUND FLOOR ROOF SLAB, p.4

**Current evidence:**
- schedule section (storey band): [25.0, 50.0] (ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C3')
- drawn outline: [20.0, 40.0] (ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, layer S-COL.BON, handle 350)

**Engine's current interpretation:** [25.0, 50.0] (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For column type C3: does the schedule section (storey band) govern, or the drawn outline ([20.0, 50.0] vs [25.0, 50.0]; [25.0, 50.0] vs [20.0, 40.0]; [25.0, 50.0] vs [20.0, 50.0])?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 4 element(s); 4 nr occurrences

## STR-COL-015

**Issue:** 3 column occurrence(s) of type C4: schedule section (storey band) differs from drawn outline ([20.0, 50.0] vs [25.0, 50.0]; [30.0, 50.0] vs [25.0, 50.0]).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 3 nr occurrences (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (column), p.9; ST7757.dxf, FIRST FLOOR ROOF SLAB, p.5

**Current evidence:**
- schedule section (storey band): [20.0, 50.0] (ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C4')
- drawn outline: [25.0, 50.0] (ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer S-COL.BON, handle 697)

**Engine's current interpretation:** [20.0, 50.0] (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For column type C4: does the schedule section (storey band) govern, or the drawn outline ([20.0, 50.0] vs [25.0, 50.0]; [30.0, 50.0] vs [25.0, 50.0])?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 3 element(s); 3 nr occurrences

## STR-COL-016

**Issue:** 4 column occurrence(s) of type C5: schedule section (storey band) differs from drawn outline ([20.0, 50.0] vs [20.0, 60.0]; [20.0, 50.0] vs [25.0, 60.0]).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 4 nr occurrences (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (column), p.9; ST7757.dxf, FIRST FLOOR ROOF SLAB, p.5

**Current evidence:**
- schedule section (storey band): [20.0, 50.0] (ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C5')
- drawn outline: [25.0, 60.0] (ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer S-COL.BON, handle 694)

**Engine's current interpretation:** [20.0, 50.0] (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For column type C5: does the schedule section (storey band) govern, or the drawn outline ([20.0, 50.0] vs [20.0, 60.0]; [20.0, 50.0] vs [25.0, 60.0])?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 4 element(s); 4 nr occurrences

## STR-COL-017

**Issue:** 1 column occurrence(s) of type C6: schedule section (storey band) differs from drawn outline ([20.0, 60.0] vs [25.0, 70.0]).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 1 nr occurrences (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (column), p.9; ST7757.dxf, FIRST FLOOR ROOF SLAB, p.5

**Current evidence:**
- schedule section (storey band): [20.0, 60.0] (ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C6')
- drawn outline: [25.0, 70.0] (ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer S-COL.BON, handle 688)

**Engine's current interpretation:** [20.0, 60.0] (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For column type C6: does the schedule section (storey band) govern, or the drawn outline ([20.0, 60.0] vs [25.0, 70.0])?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s); 1 nr occurrences

## STR-COL-018

**Issue:** 1 column occurrence(s) of type C7: schedule section (storey band) differs from drawn outline ([20.0, 80.0] vs [25.0, 80.0]).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 1 nr occurrences (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (column), p.9; ST7757.dxf, FIRST FLOOR ROOF SLAB, p.5

**Current evidence:**
- schedule section (storey band): [20.0, 80.0] (ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C7')
- drawn outline: [25.0, 80.0] (ST7757.dxf, p.5, FIRST FLOOR ROOF SLAB, layer S-COL.BON, handle 68E)

**Engine's current interpretation:** [20.0, 80.0] (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For column type C7: does the schedule section (storey band) govern, or the drawn outline ([20.0, 80.0] vs [25.0, 80.0])?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s); 1 nr occurrences

## STR-COL-019

**Issue:** 3 column occurrence(s) of type C8: schedule section (storey band) differs from drawn outline ([20.0, 90.0] vs [25.0, 80.0]; [25.0, 90.0] vs [25.0, 80.0]; [30.0, 90.0] vs [30.0, 80.0]).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 3 nr occurrences (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (column), p.9; ST7757.dxf, FOUNDATION PLAN, p.2

**Current evidence:**
- schedule section (storey band): [30.0, 90.0] (ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C8')
- drawn outline: [30.0, 80.0] (ST7757.dxf, p.2, FOUNDATION PLAN, layer S-COL.BON, handle 10E0)

**Engine's current interpretation:** [30.0, 90.0] (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For column type C8: does the schedule section (storey band) govern, or the drawn outline ([20.0, 90.0] vs [25.0, 80.0]; [25.0, 90.0] vs [25.0, 80.0]; [30.0, 90.0] vs [30.0, 80.0])?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 3 element(s); 3 nr occurrences

## STR-COL-020

**Issue:** 3 column occurrence(s) of type C9: schedule section (storey band) differs from drawn outline ([20.0, 90.0] vs [20.0, 100.0]; [20.0, 90.0] vs [25.0, 100.0]; [30.0, 100.0] vs [25.0, 100.0]).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 3 nr occurrences (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (column), p.9; ST7757.dxf, FOUNDATION PLAN, p.2

**Current evidence:**
- schedule section (storey band): [30.0, 100.0] (ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C9')
- drawn outline: [25.0, 100.0] (ST7757.dxf, p.2, FOUNDATION PLAN, layer S-COL.BON, handle 1090)

**Engine's current interpretation:** [30.0, 100.0] (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For column type C9: does the schedule section (storey band) govern, or the drawn outline ([20.0, 90.0] vs [20.0, 100.0]; [20.0, 90.0] vs [25.0, 100.0]; [30.0, 100.0] vs [25.0, 100.0])?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 3 element(s); 3 nr occurrences

## STR-COL-021

**Issue:** 5 column occurrence(s) of type C: schedule section (storey band) differs from drawn outline ([20.0, 50.0] vs [20.0, 40.0]).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 5 nr occurrences (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (column), p.9; ST7757.dxf, GROUND FLOOR ROOF SLAB, p.4

**Current evidence:**
- schedule section (storey band): [20.0, 50.0] (ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'C')
- drawn outline: [20.0, 40.0] (ST7757.dxf, p.4, GROUND FLOOR ROOF SLAB, layer S-COL.BON, handle 34D)

**Engine's current interpretation:** [20.0, 50.0] (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For column type C: does the schedule section (storey band) govern, or the drawn outline ([20.0, 50.0] vs [20.0, 40.0])?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 5 element(s); 5 nr occurrences

## STR-COL-022

**Issue:** 1 column occurrence(s) of type P.C: schedule section (storey band) differs from drawn outline ([20, 50] vs [20.0, 40.0]).

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 1 nr occurrences (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (column), p.9; ST7757.dxf, SECOND FLOOR ROOF SLAB, p.6

**Current evidence:**
- schedule section (storey band): [20, 50] (ST7757.dxf / ST7757.pdf, p.9, schedule (column), 'P.C')
- drawn outline: [20.0, 40.0] (ST7757.dxf, p.6, SECOND FLOOR ROOF SLAB, layer S-COL.BON, handle 778)

**Engine's current interpretation:** [20, 50] (MEMBER_SCHEDULE) used (authority: MEMBER_SCHEDULE)

**Question:** "For column type P.C: does the schedule section (storey band) govern, or the drawn outline ([20, 50] vs [20.0, 40.0])?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s); 1 nr occurrences

## STR-COL-023

**Issue:** 10 column occurrence(s) (C, C1, C2) at GF: schedule gives 20.0 cm but minimum column thickness for the storey height (p.9) requires at least 25.

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 10 nr occurrences (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.pdf, rule P9-COL-TMIN, p.9

**Current evidence:**
- minimum column thickness for the storey height (p.9): 25
- schedule value: 20.0

**Engine's current interpretation:** schedule value kept (member-specific design) (authority: MEMBER_SCHEDULE)

**Question:** "The schedule gives 20.0 where the general rule asks for at least 25. Is the schedule correct, or must the section increase?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 10 element(s); 10 nr occurrences

## STR-DOM-001

**Issue:** 8 dome occurrence(s) depend on P7-DOME (Dome reinforcement.), whose applicability is not established (CANDIDATE).

**Why it matters:** A rule or note exists but it is not clear where or how it applies. The quantity uses the engine's current interpretation; an answer may change it. Affected: 30.278 m2 plan (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf, DETAILS (pool / dome), p.7; ST7757.dxf, FIRST FLOOR ROOF SLAB, p.5

**Current evidence:**
- P7-DOME: Dome reinforcement.

**Engine's current interpretation:** occurrences counted; quantities depending on the rule held back

**Question:** "Does the dome detail (100 mm shell, ring beam) apply to both domes on the first-floor roof?"

**Impact:** PROVISIONAL - CONCRETE, FORMWORK, REINFORCEMENT; 8 element(s); 30.278 m2 plan

## STR-FOO-001

**Issue:** The schedule field 'BOXED' is printed for 11 type(s) (e.g. F=3+4, F10=3+5, F11=3+8, F15=3+4) but its meaning is not stated.

**Why it matters:** A rule or note exists but it is not clear where or how it applies. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 17 nr (REINFORCEMENT).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (footing), p.9

**Current evidence:**
- field BOXED: {'F': '3+4', 'F10': '3+5', 'F11': '3+8', 'F15': '3+4', 'F2': '3+4', 'F3': '3+4', 'F4': '3+4', 'F5': '3+4', 'F6': '3+5', 'F7': '3+6', 'F9': '3+8'}

**Engine's current interpretation:** component held back; other bars of the same members stay releasable

**Question:** "What does the schedule field 'BOXED' mean (bar count, bar size, shape and position)?"

**Impact:** BLOCKED - REINFORCEMENT; 17 element(s); 17 nr

## STR-FOO-002

**Issue:** Schedule row F7 (footing) is defined but no plan occurrence carries this mark.

**Why it matters:** A rule or note exists but it is not clear where or how it applies. No quantity changes with the answer; it is recorded for completeness.

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (footing), p.9

**Current evidence:**
- schedule row: 300x250x50

**Engine's current interpretation:** zero occurrences (a schedule row never creates an occurrence) (authority: PLAN_MEMBER_TAG)

**Question:** "Schedule row F7 has no occurrence on the plans. Is it unused, or is a mark missing on a plan?"

**Impact:** NO_QUANTITY_IMPACT - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s)

## STR-FOO-003

**Issue:** 26 footing occurrence(s) depend on P13-FOOTING-DEEP (Where the upper ground beam is more than 2.5 m above the footing, an additional LOWER ground beam is provided.), whose dimension is not established (BLOCKED_METHOD).

**Why it matters:** A size or length needed to measure this is not given. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 26 nr (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.pdf, rule P13-FOOTING-DEEP, p.13; ST7757.pdf, rule P9-SOIL, p.9

**Current evidence:**
- P13-FOOTING-DEEP: Where the upper ground beam is more than 2.5 m above the footing, an additional LOWER ground beam is provided.

**Engine's current interpretation:** occurrences counted; quantities depending on the rule held back

**Question:** "What is the founding level? (A lower ground beam is required where the ground beam is more than 2.5 m above the footing.)"

**Impact:** BLOCKED - CONCRETE, FORMWORK, REINFORCEMENT; 26 element(s); 26 nr

## STR-FOO-004

**Issue:** Two footing outlines overlap by 0.14 m2 plan.

**Why it matters:** Two places on the drawings say different things about the same thing. The quantity uses the engine's current interpretation; an answer may change it. Affected: 0.14 m2 plan (CONCRETE).

**Where to look:** ST7757.dxf, FOUNDATION PLAN, p.2

**Engine's current interpretation:** both counted; overlap volume must not be counted twice

**Question:** "Are these two separate members or one combined member?"

**Impact:** PROVISIONAL - CONCRETE; 2 element(s); 0.14 m2 plan

## STR-FOO-005

**Issue:** One drawn footing carries 2 different type marks (F, F10); one outline holding columns C, C10.

**Why it matters:** Two places on the drawings say different things about the same thing. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 1 nr (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf, FOUNDATION PLAN, p.2

**Current evidence:**
- mark 1: F
- mark 2: F10

**Engine's current interpretation:** none - held back

**Question:** "This footing is marked F and F10. Which type is it - or is it two members drawn as one?"

**Impact:** BLOCKED - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s); 1 nr

## STR-GRO-001

**Issue:** 21 ground slab occurrence(s) depend on P3-GROUND-SLAB (Ground slab note: 10 cm, 5Ø10/m each way.), whose extent is not established (CANDIDATE).

**Why it matters:** A size or length needed to measure this is not given. Only the part that is certain is counted; the total is a minimum until this is answered. Affected: 167.636 m2 plan (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.pdf, rule P3-GROUND-SLAB, p.3

**Current evidence:**
- P3-GROUND-SLAB: Ground slab note: 10 cm, 5Ø10/m each way.

**Engine's current interpretation:** occurrences counted; quantities depending on the rule held back

**Question:** "Which areas receive the 10 cm ground slab (5Ø10/m each way): every cell inside the ground beams, or only the cells marked with the note?"

**Impact:** LOWER_BOUND - CONCRETE, FORMWORK, REINFORCEMENT; 21 element(s); 167.636 m2 plan

## STR-LIF-001

**Issue:** 1 lift pit occurrence(s) depend on P14-LIFT (Lift pit on the FF raft: 20 cm walls with 6Ø12/m and 6Ø16/m, pit depth by the lift manufacturer.), whose dimension is not established (BLOCKED_METHOD).

**Why it matters:** A size or length needed to measure this is not given. Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where to look:** ST7757.pdf, rule P14-LIFT, p.14

**Current evidence:**
- P14-LIFT: Lift pit on the FF raft: 20 cm walls with 6Ø12/m and 6Ø16/m, pit depth by the lift manufacturer.

**Engine's current interpretation:** occurrences counted; quantities depending on the rule held back

**Question:** "What is the lift-pit depth below the lift footing (manufacturer / engineer)?"

**Impact:** BLOCKED - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s)

## STR-LIF-002

**Issue:** Lift tie beams at 3.00 m height around the lift shaft when the storey is higher than 4.30 m. requires lift tie beam (storey height > 4.30 m) but none is drawn.

**Why it matters:** Something is required by a note or rule but is not drawn or detailed. Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where to look:** ST7757.pdf, rule P8-N19, p.8

**Current evidence:**
- P8-N19: Lift tie beams at 3.00 m height around the lift shaft when the storey is higher than 4.30 m.

**Engine's current interpretation:** required population recorded; no geometry

**Question:** "Lift tie beams at 3.00 m height around the lift shaft when the storey is higher than 4.30 m.: where are these lift tie beams, and what size and bars?"

**Impact:** BLOCKED - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s)

## STR-LIN-001

**Issue:** Lintels by opening width; width = wall width; 40 cm minimum bearing each side. requires lintel (one lintel per architectural opening, type by opening width) but none is drawn.

**Why it matters:** Something is required by a note or rule but is not drawn or detailed. Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where to look:** ST7757.pdf, rule P13-LINTEL, p.13

**Current evidence:**
- P13-LINTEL: Lintels by opening width; width = wall width; 40 cm minimum bearing each side.

**Engine's current interpretation:** required population recorded; no geometry

**Question:** "Lintels by opening width; width = wall width; 40 cm minimum bearing each side.: where are these lintels, and what size and bars?"

**Impact:** BLOCKED - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s)

## STR-PAR-001

**Issue:** 3 parapets: parapet height / length follow the architectural drawings (not on the structural set).

**Why it matters:** A size or length needed to measure this is not given. Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where to look:** ST7757.dxf, FIRST FLOOR ROOF SLAB, p.5; ST7757.dxf, GROUND FLOOR ROOF SLAB, p.4; ST7757.dxf, SECOND FLOOR ROOF SLAB, p.6

**Engine's current interpretation:** occurrence counted; measurement held back

**Question:** "Give the parapet height and the roof edges that carry a parapet."

**Impact:** BLOCKED - CONCRETE, FORMWORK, REINFORCEMENT; 3 element(s)

## STR-PLA-001

**Issue:** 3 planted column occurrence(s) depend on P15-PLANTED (Beam carrying a planted column: 4Ø16 extra, column bars anchored 100 into the beam.), whose applicability is not established (CANDIDATE).

**Why it matters:** A rule or note exists but it is not clear where or how it applies. Only the part that is certain is counted; the total is a minimum until this is answered.

**Where to look:** ST7757.pdf, rule P15-PLANTED, p.15

**Current evidence:**
- P15-PLANTED: Beam carrying a planted column: 4Ø16 extra, column bars anchored 100 into the beam.

**Engine's current interpretation:** occurrences counted; quantities depending on the rule held back

**Question:** "Does the p.15 detail (Beam carrying a planted column: 4Ø16 extra, column bars anchored 100 into the beam.) apply to each of these columns, and do they use the normal tie bands?"

**Impact:** LOWER_BOUND - CONCRETE, FORMWORK, REINFORCEMENT; 3 element(s)

## STR-POO-001

**Issue:** pool SPC-POOL: pool lengths and depths are 'AS PER ARCH' on the detail.

**Why it matters:** A size or length needed to measure this is not given. Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where to look:** ST7757.dxf, DETAILS (pool / dome), p.7; ST7757.dxf, GROUND BEAMS PLAN, p.3

**Engine's current interpretation:** occurrence counted; measurement held back

**Question:** "Provide the pool plan and section (lengths, depths, slope) from the architect."

**Impact:** BLOCKED - CONCRETE, FORMWORK, REINFORCEMENT; 1 element(s)

## STR-PRO-001

**Issue:** boundary wall definition: P14-BOUNDARY says TYPICAL BOUNDARY WALL: (20x30) R.C columns 4Ø14; GROUND BEAM (20x40); 2Ø14 (T&B); Ø8/20 STIRRUPS; 3Ø16 (T&B); 7Ø12; 4Ø12, schedule row B.W says 20x60 ['4', '16'].

**Why it matters:** Two places on the drawings say different things about the same thing. Until this is answered the affected part of the quantity is held back (not counted in totals).

**Where to look:** ST7757.dxf / ST7757.pdf, schedule (simple beam), p.10; ST7757.pdf, rule P14-BOUNDARY, p.14

**Current evidence:**
- None: TYPICAL BOUNDARY WALL: (20x30) R.C columns 4Ø14; GROUND BEAM (20x40); 2Ø14 (T&B); Ø8/20 STIRRUPS; 3Ø16 (T&B); 7Ø12; 4Ø12 (ST7757.pdf, p.14, rule P14-BOUNDARY)
- None: 20x60 ['4', '16'] (ST7757.dxf / ST7757.pdf, p.10, schedule (simple beam), 'B.W')

**Engine's current interpretation:** none - held back

**Question:** "boundary wall definition: which value governs, TYPICAL BOUNDARY WALL: (20x30) R.C columns 4Ø14; GROUND BEAM (20x40); 2Ø14 (T&B); Ø8/20 STIRRUPS; 3Ø16 (T&B); 7Ø12; 4Ø12 or 20x60 ['4', '16']?"

**Impact:** BLOCKED - CONCRETE, REINFORCEMENT; 1 element(s)

## STR-PRO-002

**Issue:** formwork rule: P8-N17 says formwork >= 14 days, P1-NOTE-C says formwork >= 21 days.

**Why it matters:** Two places on the drawings say different things about the same thing. No quantity changes with the answer; it is recorded for completeness.

**Where to look:** ST7757.pdf, rule P1-NOTE-C, p.1; ST7757.pdf, rule P8-N17, p.8

**Current evidence:**
- None: formwork >= 14 days (ST7757.pdf, p.8, rule P8-N17)
- None: formwork >= 21 days (ST7757.pdf, p.1, rule P1-NOTE-C, handle 7E)

**Engine's current interpretation:** none - held back

**Question:** "formwork rule: which value governs, formwork >= 14 days or formwork >= 21 days?"

**Impact:** NO_QUANTITY_IMPACT - OTHER; 1 element(s)

## STR-SLA-001

**Issue:** 49 slab occurrence(s) depend on P4-6-NOTE-2 (Top steel 5Ø10/m over beams for the slabs, length one third of the span, in both directions.), whose applicability is not established (CANDIDATE).

**Why it matters:** A rule or note exists but it is not clear where or how it applies. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 370.501 m2 plan (REINFORCEMENT).

**Where to look:** ST7757.pdf, rule P15-SLAB-ON-BEAMS, p.15; ST7757.pdf, rule P4-6-NOTE-2, p.4

**Current evidence:**
- P4-6-NOTE-2: Top steel 5Ø10/m over beams for the slabs, length one third of the span, in both directions.

**Engine's current interpretation:** occurrences counted; quantities depending on the rule held back

**Question:** "The plan note asks for 5Ø10/m top bars over beams for one third of the span, and p.15 gives top-bar extensions of 0.25L / 0.30L. Is the plan note a minimum where no top bar is drawn, or does it replace p.15?"

**Impact:** BLOCKED - REINFORCEMENT; 49 element(s); 370.501 m2 plan

## STR-SLA-002

**Issue:** temperature reinforcement table (p.15) has no row for 160 mm (47 element(s)); rows are [100, 125, 150, 175, 200, 250, 300].

**Why it matters:** A drawing rule does not cover this exact case (for example a value sits exactly on a limit). Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 356.866 m2 plan (REINFORCEMENT).

**Where to look:** ST7757.pdf, rule P15-TEMP-TABLE, p.15

**Current evidence:**
- table rows: [100, 125, 150, 175, 200, 250, 300]
- required key: 160

**Engine's current interpretation:** none - held back

**Question:** "temperature reinforcement table (p.15): which value applies for 160 mm?"

**Impact:** BLOCKED - REINFORCEMENT; 47 element(s); 356.866 m2 plan

## STR-SLA-003

**Issue:** temperature reinforcement table (p.15) has no row for 180 mm (2 element(s)); rows are [100, 125, 150, 175, 200, 250, 300].

**Why it matters:** A drawing rule does not cover this exact case (for example a value sits exactly on a limit). Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 13.635 m2 plan (REINFORCEMENT).

**Where to look:** ST7757.pdf, rule P15-TEMP-TABLE, p.15

**Current evidence:**
- table rows: [100, 125, 150, 175, 200, 250, 300]
- required key: 180

**Engine's current interpretation:** none - held back

**Question:** "temperature reinforcement table (p.15): which value applies for 180 mm?"

**Impact:** BLOCKED - REINFORCEMENT; 2 element(s); 13.635 m2 plan

## STR-STA-001

**Issue:** 5 stair occurrence(s) depend on P16-STAIR (Typical stair and stair-beam reinforcement (N.T.S.).), whose applicability is not established (BLOCKED_METHOD).

**Why it matters:** A rule or note exists but it is not clear where or how it applies. Until this is answered the affected part of the quantity is held back (not counted in totals). Affected: 56.327 m2 plan (CONCRETE, FORMWORK, REINFORCEMENT).

**Where to look:** ST7757.dxf, GROUND FLOOR ROOF SLAB, p.4; ST7757.pdf, rule P16-STAIR, p.16

**Current evidence:**
- P16-STAIR: Typical stair and stair-beam reinforcement (N.T.S.).

**Engine's current interpretation:** occurrences counted; quantities depending on the rule held back

**Question:** "Does the typical stair detail (p.16) apply to each stair on the plans, including the stair inside the void? Please give flight / landing levels and waist thickness."

**Impact:** BLOCKED - CONCRETE, FORMWORK, REINFORCEMENT; 5 element(s); 56.327 m2 plan

## STR-TUR-001

**Issue:** 2 turn column occurrence(s) depend on P15-TWISTED (Twisted (turned) column: spiral ties 6Ø8/m over 1 m each side of the floor, 4Ø16 extra.), whose applicability is not established (CANDIDATE).

**Why it matters:** A rule or note exists but it is not clear where or how it applies. Only the part that is certain is counted; the total is a minimum until this is answered.

**Where to look:** ST7757.pdf, rule P15-TWISTED, p.15

**Current evidence:**
- P15-TWISTED: Twisted (turned) column: spiral ties 6Ø8/m over 1 m each side of the floor, 4Ø16 extra.

**Engine's current interpretation:** occurrences counted; quantities depending on the rule held back

**Question:** "Does the p.15 detail (Twisted (turned) column: spiral ties 6Ø8/m over 1 m each side of the floor, 4Ø16 extra.) apply to each of these columns, and do they use the normal tie bands?"

**Impact:** LOWER_BOUND - CONCRETE, FORMWORK, REINFORCEMENT; 2 element(s)

