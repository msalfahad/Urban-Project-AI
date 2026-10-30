# T-358 Dewatering / excavation support / temporary works (B1-06): what the printed notes put in scope (development villa; every villa)

Worker 1 (lane S), 2026-10-30, run session_01E6cPnc7Cs1jc67Zzv26LBN. Research piece, not wired: no engine module, method
version, route G, rule / knowledge file, candidate line or released quantity changed. Development villa, not an accuracy
claim. Drawings named by Drive folder "Alsenan chalet project" and title; entities by DXF handle or PDF page; note and
sheet numbers only (no note text copied, no client data); excavation rectangles in plot-local metres. ERS s.2 - s.4, s.7.

Files: `tempworks_scope_v1.py` (TEMPWORKS_SCOPE_V1, pure rules, stdlib), `ALSENAN_TEMPWORKS_INPUT.json` (read this run),
`t358_alsenan_check.py` -> `SHEET_SEARCH_T358.csv`, `EXPOSURE_T358.csv` (31 excavations x 4 sides), `SIDES_T358.csv`,
`ITEMS_T358.csv`, `summary.json`; tests `tests/t358_tempworks/` (21 pass: 14 hand-fixture villa K358 incl. 7 adverse
+ 7 development-villa pins incl. output reproduction).

## 1. The physical elements and the question (ERS s.2.1)

- DEWATERING: lowering the groundwater below the formation (bottom of the excavation, under the blinding) for the
  duration of the works. Needed only where a formation reaches the water level.
- EXCAVATION SUPPORT / PROTECTION (shoring): support of an excavation face so the soil beyond it (neighbour plot,
  street, existing structure) does not move, plus edge protection. Exposure test (acceptance c): a face whose
  horizontal distance to a plot side is not more than its own depth below EG; a face on or beyond the line is exposed
  at any depth.
- OTHER TEMPORARY WORKS: hoarding, site office, access, scaffold. Formwork props are the formwork item, never B1-06.

B1-06 is an ITEM (BOQ_FAMILY_MASTER 1.20.0, BLOCKED_BY_SOURCE, source_needed 'site investigation'). Question: do the
printed notes create a scope, under what condition, and is any extent drawn.

## 2. Evidence search (acceptance a) — `SHEET_SEARCH_T358.csv`, 31 sheets

| Sheet | Note | Class | What it puts in scope |
|---|---|---|---|
| ST p.8 (160 dpi, notes 1-24 in full) | 14 | DEWATERING | if groundwater is found: approved dewatering company, method approved by the supervising engineer (conditional by its own wording) |
| ST p.8 | 15 | SUPPORT | contractor submits a technical study by an accredited specialist body and carries out the protection and shoring needed during the work; liable for damage around the excavation sides (unconditional obligation; extent = the study's) |
| ST p.8 | 17, 23 | FORMWORK_PROPS | prop striking / re-propping: formwork item (T-163 / T-199), not B1-06 |
| ST p.8 | 10, 12, 13 | site investigation (boring at the contractor's cost), founding-level check, sulphate-resisting cement | other items, not B1-06 |
| ST p.9 (300 dpi; DXF 1E11, 1E0E) | 1 | EXCAVATION_LEVEL | excavation level not less than 1.5 m below the existing plot ground level |
| ST p.9 | 2 + bearing table | DESIGN_FOUNDING_DEPTH | design stress 2.20 kg/cm2 = the table's DEPTH 1.5 row: the design founding depth is the 1.5 m row |
| ST p.9 | 4 | GROUNDWATER | groundwater at a depth of 4.5 m |
| ST p.1 (DXF B8) | bullet 2 | EXCAVATION_AT_LINE | neighbour-side external ground beams over and under black brick built from the founding level |
| ST p.14 (220 dpi) | TYPICAL BOUNDARY WALL | EXCAVATION_AT_LINE | foundation 'AS PER EXCAVATION DEPTH BELOW N.G. LEVEL', wall outer face on the plot line |
| ST p.14 | lift detail | PARAMETRIC_DEPTH | pit depth 'As Per Lift Manufactures recommendations' (not printed) |
| ST p.2 - p.7, p.10 - p.13, p.15, p.16 | - | absent | (p.2 / p.3 geometry used in section 4) |
| ARCH p.1 - p.12 | - | absent | no note block on any sheet; SECTION A-A ground zone at 90 dpi: ground line +-0.00, no below-ground construction, no water line |
| SAN p.1 - p.3 | - | absent | drainage plans, legend, one note (stated dimensions) |

DXF census (`shx_arabic`, English + Arabic keywords): ST 2 253 records -> 1E0E (note 4), 1E11 (note 1), B8 (p.1), 2 false
positives (1A85 water-tank label, 1C4B 'SHORT BARS'); P7757 276 records -> 0. No soil report, no specification issued;
no owner rule on B1-06 (OWNER_QUESTIONS(_ANSWERED), OWNER_RULE_*, DECISION_REGISTER searched). Freelancer: 0 rows
(885 rows, Arabic / English). Engine: 0 lines.

## 3. Dewatering (acceptance b) — water -4.50 on the EG datum

Water level: depth 4.5 m (p.9 note 4). Its datum is not printed; read on EG +-0.00 (DERIVED, T-357) because the same box
measures note 1 from the existing plot ground and the bearing table's DEPTH is below ground: **INTERPRETED**.

| Element | Formation (EG datum) | Kind | Status | Trigger (m) |
|---|---|---|---|---|
| 24 footing pits + F10 / F | <= -1.50 | AT_MOST (p.9 note 1) | CONDITIONAL | clearance 3.00: only if the formation is lowered 3.00 m or more (to -4.50) by the note 12 founding check |
| boundary-wall trenches | <= -1.50 | AT_MOST (p.14 -> note 1) | CONDITIONAL | same, 3.00 |
| pool envelope | -1.50 | PRINTED (p.7; T-183 r2 / T-200) | NOT_TRIGGERED | clearance 3.00 |
| lift FF | 0.30 - d - t (pit floor = raft top; 0.55 + 0.05 + t + 0.10 below it; d below GF FFL +1.00) | PARAMETRIC | CONDITIONAL | only if pit depth d + membrane t >= 4.80 m |

**B1-06a DEWATERING: CONDITIONAL.** On every drawn formation the excavation stays 3.00 m above the printed water level,
and the design founding depth (2.20 kg/cm2 = the 1.5 m row) agrees with the 1.50 limit; dewatering enters only if
(i) the site founding check lowers a formation by >= 3.00 m, (ii) the lift pit is >= 4.80 m deep, or (iii) water is
found higher than printed (note 14's own condition). Sensitivity (datum not printed): measured from the GF FFL +1.00
instead (refused as EG by R-TW-2, reported only), water -3.50, clearance 2.00 m, lift threshold 3.80 m: the status does
not change. Quantity: None (no extent, no duration, no pump count printed).

## 4. Excavation support per plot side (acceptance b, c) — `SIDES_T358.csv`, `EXPOSURE_T358.csv`

Plot 31.37 x 15.00 (ST S-BOUN 1658 / 7FE; T-357 sides PRINTED): S0 lower neighbour, S1 upper neighbour, S2 street,
S3 sea view (ST p.2 / p.3 print STREET left, SEA VIEW right; T-357 corners). Excavations: 26 T-347 / T-170 pits by
handle (neat face = outline + 0.10 p.13 blinding projection; FF at its raft outline, projection not printed), pool 7C6
(+0.10 printed screed + membrane beyond the outer wall face), four boundary-wall trench runs (7FE x 3, 7FC; wall outer
face on the line, pad 0.80 + blinding 0.10 inward). Depth: AT_LEAST 1.50 (pits, trenches), PRINTED 1.50 (pool), HELD
(FF).

| Side | Status | Plot line with a face ON / BEYOND it (m) | Faces | Also within their depth (m) |
|---|---|---|---|---|
| S0 lower neighbour 31.37 | TRIGGERED | 15.15 (pits only) | F 1669, F15 1B2A, F 166A, F11 1B07, F14 1B1A, F10 / F 1B1B | 4.20: F3 166C (0.85), F5 166D (0.50) |
| S1 upper neighbour 31.37 | TRIGGERED | 31.37 (boundary-wall trench, whole side) | BW 7FE | 11.20: F2 x 2, F4 x 2, F5 1664 (0.50 .. 0.70) |
| S2 street 15.00 | TRIGGERED | 10.00 | F 1669, F 1668, BW 7FE street run 8.30 | - |
| S3 sea view 15.00 | TRIGGERED | 11.85 | pool 7C6, F8 1B24, FN 1100, F10 / F, BW 7FE 2.45 + 7FC 1.15 | 2.20: F4 1666 (0.55) |

Ten excavations stand BEYOND a plot line (negative distance = the 0.10 blinding projection, and the pool layers):
3 F, F11, F14, F15, F8, FN 1100, F10 / F, pool. This is the D-14 / F-T320-05 condition seen from the earthworks side:
the excavation itself, not only the blinding, crosses into the neighbour plot / street. S0 length counts the pits only:
p.1 bullet 2 (external ground beams on brick from the founding level) also takes the neighbour-side runs down to the
founding level at the line; that lower row is the conditional / Q-28 item of T-347 and is not added here.

**B1-06b EXCAVATION SUPPORT / PROTECTION: TRIGGERED** on all four sides by p.8 note 15 + the geometry (faces at the
plot line at >= 1.50 m). Extent: NOT PRINTED (the specialist study decides the system, length and duration). Quantity
None; the side lengths above are geometric facts in m, not a shoring quantity.

**B1-06c OTHER TEMPORARY WORKS: NOT_IN_DRAWN_SCOPE** (no sheet prints any; props belong to formwork).

## 5. Methods side by side and reconciliation (ERS s.2.4)

| | B1-06a dewatering | B1-06b support | B1-06c other |
|---|---|---|---|
| Owner manual method | no rule recorded (Q-21 C: EG / formation / blinding distinguished; 1.50 a minimum) | no rule | no rule |
| Released V2.9 / route G / candidate V3.0.25 | no line (BLOCKED_BY_SOURCE) | no line | no line |
| Freelancer | no row | no row | no row |
| Drawing-derived (this task) | CONDITIONAL, 3.00 m clearance, lift 4.80 m | TRIGGERED, 4 sides, extent by study | NOT_IN_DRAWN_SCOPE |

Both BOQs omit B1-06. Verdict proposal: **SCOPE_ITEMS_NOT_QUANTITIES** — neither is wrong on quantity (none can be
measured: no extent is drawn); both are incomplete on scope: a correct BOQ carries B1-06b as an item line (support +
protection per note 15, all four sides, extent by the contractor's specialist study) and B1-06a as a conditional item
(note 14, trigger in section 3). Residual: none in units; the water datum is INTERPRETED (no status change under the
alternative).

## 6. General rules (TEMPWORKS_SCOPE_V1, every villa, provenance T-358; research rule, not a rule-library version)

R-TW-1 status only from a printed source (sheet + note); no printed water level = UNKNOWN, never NOT_TRIGGERED.
R-TW-2 levels on the EG datum; a finished level offered as EG is refused. R-TW-3 formation kinds PRINTED / AT_MOST /
PARAMETRIC with their trigger in metres; project status = the worst element; a conditional note never lifts a measured
TRIGGERED. R-TW-4 face exposure by distance vs depth (ON_OR_BEYOND_LINE / WITHIN / CONDITIONAL / OUTSIDE). R-TW-5 an
item quantity only with a drawn / specified extent; none written without it; held never 0.

Tests: villa K358 normal (dewatering CONDITIONAL with clearances 1.80 / 0.60 and lift 3.10; water below every printed
formation -> NOT_TRIGGERED; support per side by hand; mirror and 90-degree rotation invariance; an extent with a
source) and adverse (no water -> UNKNOWN; finished level as EG / as formation / as depth basis refused; a quantity
without extent, a held 0, an extent without source, a quantity under NOT_TRIGGERED refused; five non-sources; mm
units; duplicates; a held depth never OUTSIDE).

## 7. Lessons-register proposal (ERS s.7)

| Date | Problem | Root cause | General rule | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-30 | B1-06 sat BLOCKED_BY_SOURCE 'needs a site investigation' although ST p.8 notes 14 / 15 and p.9 note 4 print the groundwater depth and a shoring obligation, and ten excavations of the drawn foundation cross the plot line | a family was blocked on a missing document instead of reading what the set prints; scope (an item) and quantity (an extent) were treated as one question | a temporary-works item is in scope from its printed note (TRIGGERED / CONDITIONAL with the trigger in metres: formation vs water level on the EG datum; face distance vs depth per plot side); its quantity exists only with a drawn or specified extent; a finished level is never the datum (every villa) | tests/t358_tempworks (water below every formation -> NOT_TRIGGERED; quantity without extent refused; finished level as EG refused) | PROPOSED |

## 8. For the Checker (re-read)

1. ST7757.pdf p.8 notes 14, 15 (and 10, 12, 13, 17, 23 classed as other items); p.9 boxed notes 1, 2, 4 + the bearing
   table (2.20 = the 1.5 m row).
2. ST p.14 TYPICAL BOUNDARY WALL section A-A ('AS PER EXCAVATION DEPTH BELOW N.G. LEVEL'); lift detail pit depth.
3. Foundation plan (ST DXF): S-BOUN 1658 = 31.37 x 15.00; outlines 1B07, 1B1A, 1B2A, 1B24, 1B1B, INSERT 1669 / 166A /
   1668, 4 LINEs 1100 on a plot line; pool 7C6 outer face on the sea line (GROUND BEAMS frame, 7FE).
4. SIDES_T358.csv lengths: S0 15.15 = 1.00 + 2.00 + 1.10 + 3.70 + 4.00 + 3.35.

## 9. Not done / uncertain

- No quantity (no extent printed). The specialist study of note 15 and any site water observation decide the extents.
- Water datum INTERPRETED (EG); sensitivity reported. Interior ground undulation unknown (T-357).
- Exposure uses rectangles: the pool D's curved face is inside its rectangle (its straight back and sides set the
  distances to S0 / S1 / S3 exactly; S2 is the curve apex). The FF face is at its raft outline (projection not printed:
  distances AT_MOST). The neighbour-side lower ground-beam row (p.1 bullet 2, Q-28) is not added to S0.
- Possible RFI B item (the Lead decides; ERS 2.7 not met, no owner question): the groundwater datum of p.9 note 4 and
  the lift pit depth, only if the Lead wants the conditional triggers closed before tender.
