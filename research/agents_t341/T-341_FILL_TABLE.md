# T-341: canonical-deduction FILL table on the V3.0.22 candidate (integration dependency of T-246; every villa)

Worker 1 (lane S), 2026-10-29. Research only: no engine, method, rule / knowledge version, registry, frozen file or
candidate line changed; nothing re-measured. Development villa, not an accuracy claim. Drawings by Drive title only.

## 1. Run identity (acceptance a)

Drive "Alsenan chalet project": P7757_DXF_COMPRESSED.zip (DXF `ab54dd55`) + "ST7757 dxf.dxf" `9f9d1179`; own run
`research/agents_t167/v304_run.py` then `research/agents_t331/v3022_run.py` (Python 3.11.18): V3_0_22_BOQ_LINES.json
**`7199c8b6`** (3,706 lines); V3.0.21 `be22a4e4` and V3.0.20 `097a80b6` reproduced byte for byte.
T-330 check (`tools/t330_deductions_check.py`, reused read-only) on V3.0.22: **41 FLAG, 0 REFUSED** (74 OK, 3,591
NOT_APPLICABLE): plaster 4 + paint 4 + wall tile 12 EMPTY_DEDUCTIONS, skirting 8 NOT_SUMMING + 2 EXPORT_TOTAL_BLANK,
porcelain 2 NOT_SUMMING, wall run 7 + ceiling 2 EXPORT_TOTAL_BLANK / MISSING_ID.

## 2. The fill (acceptance b): `t341_fill.py`, FILL_TABLE_T341.csv (129 rows), FILL_LINES_T341.csv (41 lines)

Per line: each deducted opening / element by id, face, amount in the line's unit, source; `gross - sum = net` within
0.0005. Sources: the line's own owner-method list (calculation.inputs.owner_manual_method.deductions), the merged
per-opening skirting ledger research/agents_t296/DEDUCTIONS_BY_OPENING_T296.csv (T-296 MERGED 57c31ae4), the line's
own base_ownership_v3021.on_tiled_faces and floor_scope_v3014 records. A signed ledger row (the band passage OP-003
longer than its stretch on the boundary) is an ADDITION (+1.400 lm on L-71e2e002), never a negative deduction.

| Family (unit) | Lines | Gross field | Net | Listed (ded - add) | Status |
|---|---|---|---|---|---|
| FIN.WALL.TILE (m2) | 12 | 374.274 | 340.304 | **33.970** (25 opening rows by id + face) | 12 RECONCILED |
| FIN.PLASTER (m2) | 4 | 259.510 | 217.208 | **42.302** (12 openings) | 4 RECONCILED |
| FIN.PAINT (m2) | 4 | 259.510 | 217.208 | **42.302** (same 12 openings) | 4 RECONCILED |
| FIN.SKIRTING (lm) | 10 | 254.959 | 180.117 | **74.842**, incl. the unlisted F-17 threshold halves **13.069** (8 lines) and the pantry base on the tiled faces 3.500 (6 faces) | 10 RECONCILED |
| FIN.FLOOR.PORCELAIN (m2) | 2 | 143.489 | 143.489 | GF 17.149 from face 126.928; 1F 36.381 from face 75.983 | 1 RECONCILED_GROSS_RESTATED, **1 UNEXPLAINED** |
| FIN.CEILING (m2) | 2 | 202.911 | 170.901 | 32.010 (the 16.005 void, by element) | 2 RECONCILED_BY_ELEMENT |
| ARCH.WALL_RUN (lm) | 7 | 337.849 | 216.931 | 120.918 (one aggregate per line) | 7 RECONCILED_BY_ELEMENT |

Applied in memory to copies (`apply_fill`, what T-246 does): T-330 re-check **41 FLAG -> 1 FLAG, 0 REFUSED** (the one
UNEXPLAINED line, left untouched). Residuals within tolerance are the owner list's 4-decimal rounding (wall tile up to
0.00015 m2, plaster 0.00005 m2). Skirting 13.069 lm (was 13.569 on V3.0.20): L-af6fb2d3's 0.500 lm left with the line
(NOT_APPLICABLE since V3.0.21).

## 3. Hand checks, one line per family (acceptance c)

- Plaster L-af9621f4 (1F-01): 59.295 - (D115 landing 2.200 + D315 bath 1.760 + W14 3.920) = **51.415** = net.
- Paint L-ade6f056: the same three openings, 59.295 - 7.880 = 51.415 = net.
- Wall tile L-ca4e74c5 (GF-16): W07 0.60 x (2.50 - 1.70) = 0.480; D-GF-14 0.80 x 2.20 = 1.760; 27.83125 - 2.240 =
  25.59125 vs net 25.5912 (owner list at 4 dp; +0.00005 m2, inside 0.0005).
- Skirting L-c021ae79 (1F-01): 17.700 - (OP-004 0.800 + OP-020 1.000 + W14 glazing half 1.224887 + W14 threshold
  half 1.224887) = **13.450226** = net.
- Porcelain L-7625f35c (GF open plan): face 126.927696 (= ceiling line L-eb3be58f gross, same engine face, polygon 81
  vertices) - stair treads 8.194412 - pantry wet part GF-PANTRY-RC99C2A-PART 8.954867 = **109.778417** = net.
- Ceiling L-eb3be58f: 126.927696 - 16.005 = 110.922696 = net. Wall run L-b5b4b55f (GF t=0.15): 39.077881 - 8.743127
  = 30.334754 = net.

## 4. Findings for the Lead (never forced to fit)

1. **UNEXPLAINED, L-b06400d4 (1F living porcelain), 5.891 m2.** Face 75.983002 (ceiling L-fc116bb6) - listed 31.113649
   (treads 8.336981, void 16.005, flight below 6.771668) = 44.869353; the line's formula starts from a range low
   38.458536 (+0.175 settled FLOOR, - landing 4.9225 Q-66 B) = 33.711036. The step 44.869353 -> 38.458536 = 6.410817
   m2 is not itemised anywhere on the line; the held strips D-13 / D-23 explain 0.520 of it (0.345 NOT_FLOOR listed
   here), **5.890817 m2 remain unnamed**. The net is not judged; the line's gross field (= net) must not be exported
   with this list until the step is itemised (T-246: keep it HELD on the export, or a lane I trace of the range low).
2. **Porcelain gross written equal to net (both lines).** GF closes only from the face area: T-246 must restate the
   gross field 109.778417 -> 126.927696 (RECONCILED_GROSS_RESTATED), not just add the list.
3. **No opening ids for 9 aggregate lines.** Wall run (7 lines, 120.918 lm: "openings, wall ends and columns") and the
   ceiling voids (2 lines, 32.010 m2) carry one aggregate each; they close by element, not by opening. A wall-band
   opening ledger (T-261 wall-by-wall is the natural source) would split the wall run; the voids are elements, not
   openings.
4. **Owner-list labels that are not census ids** (plaster / paint / tile): "bath door (loose arc)", "W03 pool glazing
   band (bed-room part)", "D115 (landing)", "D315 to bath", "D315 to W.C.", "d220": named, not bound to the T-249
   census; T-246 should carry the census id beside the label where the merged inventory has one.

## 5. Adverse cases (acceptance d), tests/t341_fill (synthetic villa VG-341, hand-calculated)

Normal: owner list fills and closes (42.000 - 1.980 - 1.200 = 38.820 m2); ledger split with a signed passage row as an
addition and an unlisted threshold half (14.00 - 5.10 + 0.50 = 9.40 lm); floor gross restated from the face (30 - 2 - 5
= 23 m2), input lines never modified. Adverse: an opening listed twice -> REFUSED (even when the arithmetic closes); a
list item in lm on an m2 line -> REFUSED; a net 1.000 m2 below what the openings explain -> UNEXPLAINED, line left as
is, T-330 still FLAGs it; gross = net with no face -> UNEXPLAINED (residual None, never 0); a ledger that does not close
its aggregate -> falls back to the element row, never a partial split.

## 6. T-246 consumption (acceptance e)

T-246 reads FILL_TABLE_T341.csv unchanged: per RECONCILED* line, deductions = rows with role DEDUCTION as
{"id", "qty", "unit", "face", "source", "what"} (keys the export reads), additions = rows with role ADDITION, gross =
`gross_used` from FILL_LINES_T341.csv; UNEXPLAINED / REFUSED lines are not filled. `apply_fill` is the reference.

## 7. Lesson (proposed for ENGINEERING_REASONING_STANDARD s.7)

| 2026-10-29 | 41 V3.0.22 lines could not explain their net by opening id; one (1F porcelain) cannot at all: 5.891 m2 between face-minus-list and its range low is stated nowhere | lines carried the list in the owner-method inputs, an aggregate per 'what', or a gross overwritten by the net | every exported deduction is one opening / element id with its amount in the line's unit, from the line's own records or a merged per-opening ledger; a signed correction is an addition; a net no list explains stays a named residual and is not filled (every villa) | tests/t341_fill (normal 3; adverse 5) | table DONE; consumption = T-246 |
