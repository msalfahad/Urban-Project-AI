# T-001b: first measured scoreboard rows, Alsenan (development villa), ARCH_TAKEOFF_V2.9 + route G

Worker run 2026-10-18. Rows for the VERIFIER to check and copy into SCOREBOARD.md (PLAN.md roles: the worker
measures, the verifier writes the scoreboard). Development reference only: this is not an accuracy claim.

## Inputs (read outside the clone, never committed)

| Input | Where | sha256 | = SOURCE_MANIFEST.json |
|---|---|---|---|
| P7757.dxf (17 227 946 bytes) | Drive "Alsenan chalet project" / "P7757_DXF_COMPRESSED.zip", unzipped | ab54dd55...31cc4 | yes (line 156) |
| ST7757.dxf (3 153 037 bytes) | Drive "Alsenan chalet project" / "ST7757 dxf.dxf" | 9f9d1179...38079 | yes (line 602) |
| freelancer rows | `tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json` (COVER_TOTAL rows) | committed | - |

## Run (working branch b35c944, Python 3.11.17, requirements.txt)

```bash
python3 -I tools/urban_boq_m9.py arch --drawings P7757.dxf --out RUN --method ARCH_TAKEOFF_V2.9 \
    --structural ST7757.dxf --conventions engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json --no-m9-xlsx --no-svg
python3 -I tools/alsenan_keymap.py --run RUN --reference tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json \
    --key-map tests/alsenan/T001B_KEY_MAP.json --out SCORE.json --markdown SCORE.md
```

Exit 0. 1 455 canonical lines: 506 architectural (floors found: GF, 1F, 2F) + 949 structural (route G).
No project facts file was passed (none is committed for this villa), so heights and finishes the method needs from
facts stay HELD: that is the method's answer, not a scorer choice.

Release class (tools/alsenan_keymap.py, the engine's own UP-QTY-STATUS-001 rule): MEASURED / SOURCE_DERIVED /
PROVISIONAL with a quantity -> RELEASED; BLOCKED_RFI / BOUNDED_EXPOSURE / no quantity -> HELD; NOT_APPLICABLE ->
not an answer; a CONDITIONAL wet / dry review set carrying a keyed item -> HELD. A reference line is compared only when
every answer is RELEASED (T-001a rule), so one held line holds the whole line.

## Measured rows (tools/alsenan_scoreboard.py output, unchanged)

| Trade | Unit | Ref lines | Coverage | Silent omissions | Unit refused | Compared | WAPE | WAPE (adjudicated) | Signed | False pos. | Duplicates |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CONCRETE | m3 | 8 | 100.00 % | 0 | 0 | 3 | 17.03 % | 17.03 % | -17.03 % | 0 | 0 |
| DOORS | m2 | 1 | 0.00 % | 0 | 1 | 0 | - | - | - | 0 | 0 |
| FLOOR_AREA | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | - | 0 | 0 |
| PAINT | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | - | 0 | 0 |
| PLASTER | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | - | 0 | 0 |
| WINDOWS | m2 | 1 | 0.00 % | 0 | 1 | 0 | - | - | - | 0 | 0 |

Concrete WAPE by hand: |77.265354 - 77.6305| + |12.006536 - 21.8328| + |3.49525 - 12.348| = 0.365146 + 9.826264 +
8.85275 = 19.04416; / (77.6305 + 21.8328 + 12.348 = 111.8113) = 0.17032 = 17.03 %.

## Per line (engine side: released lines / sum, held lines)

| Key | Freelancer row | Ref qty | Outcome | Released lines, sum | Held lines | Note |
|---|---|---|---|---|---|---|
| CONC.BLINDING | RC:ورقة1:15 | 47.055 m3 | HELD | 0 | 1 | |
| CONC.FOOTING | RC:ورقة1:17 | 77.6305 m3 | COMPARED | 30, 77.265 | 0 | incl. BOUNDARY_WALL 7.22 as "perimeter" (to confirm) |
| CONC.GROUND | RC:ورقة1:18 | 75.09 m3 | HELD | 23, 17.127 | 61 | ground beams all held |
| CONC.COLUMN | RC:ورقة1:19 | 39.7515 m3 | HELD | 0 | 118 | necks + columns all held |
| CONC.BEAM | RC:ورقة1:20 | 65.966 m3 | HELD | 112, 64.820 | 24 | |
| CONC.SLAB | RC:ورقة1:21 | 59.817 m3 | HELD | 75, 61.551 | 1 | |
| CONC.STAIR_DOME | RC:ورقة1:22 | 21.833 m3 | COMPARED | 5, 12.007 | 0 | |
| CONC.POOL | RC:ورقة1:23 | 12.348 m3 | COMPARED | 2, 3.495 | 0 | |
| PLASTER.INTERNAL | PLS:الفاتورة:16 | 1151.138 m2 | HELD | 20, 17.740 | 29 | unit from the row label (record has none) |
| PAINT.INTERNAL_WALL | PNT:الفاتورة:16 | 1191.128 m2 | HELD | 0 | 13 | + 14 not-applicable lines; unit from label |
| FLOOR.INTERNAL | FIN:الغلاف:15 | 409.58 m2 | HELD | 44, 376.286 | 3 | 3 = wet / dry review sets |
| DOORS.ALUMINIUM | ALU:الغلاف:16 | 12.0 m2 | UNIT_MISMATCH | 2 nr refused | - | m2 vs nr, never converted |
| WINDOWS.ALUMINIUM | ALU:الغلاف:17 | 116.9 m2 | UNIT_MISMATCH | 27 nr refused | - | m2 vs nr |

Released sums of HELD lines are diagnostics only; they are never compared (a held part would understate).

## Verdict proposals for the verifier (no hand calculation from the drawing was made in this run)

- CONC.FOOTING -0.37 m3 (-0.5 %): UNRESOLVED until the verifier confirms the boundary-wall strip is the freelancer's
  "perimeter" footing; without it the engine is 70.05 m3 (-9.8 %).
- CONC.STAIR_DOME -9.83 m3: UNRESOLVED; the freelancer's stair sheet holds a basement sub-stair (13.70 m3) and the main
  stair (8.13 m3), and the engine reads 3 stair lines (4.635) + 2 dome lines (7.372); likely FREELANCER_RIGHT
  (an engine stair omission) but needs the stair sections checked.
- CONC.POOL -8.85 m3: UNRESOLVED; engine 2 pool lines 3.495 vs freelancer 12.348.

## Uncertain / for the lead

- The architectural run found GF, 1F and 2F only; the freelancer's sheets include a basement. Floor area, plaster and
  paint will stay short or held until every storey is found (relates to T-029, unrecognised storey titles).
- Plaster, paint, columns, ground beams and blinding are HELD: a project facts file (heights, finishes) and the held
  structural RFIs are what would release them; no quantity was changed by this task.
- Doors and windows: the freelancer measures aluminium in m2, the engine counts nr. A comparable row needs either an
  engine opening-area line or the freelancer's counts; the scorer refuses, as it should.
- Out of these trades (UNMAPPED, listed in SCORE.json): rebar (kg vs t), blockwork, waterproofing, ceilings, marble,
  skirting, internal PVC doors (no freelancer line).
