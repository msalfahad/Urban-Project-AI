# T-714 B10-13 formwork restated on V3.0.70: the 370 HELD BLANK lines given their members' bounds (research, unwired)

Worker 1, lane S, 2026-11-11, branch `agents/task-T-714`. Files: `t714_rules.py` (R-T714-1 / R-T714-2, every villa),
`t714_alsenan.py` (builder, committed inputs only, sha256-pinned in `PINS.json`), `out/T714_FORMWORK_BOUNDS.json`
(one row per line, every face with its class), `out/T714_CENSUS.md`, `out/T714_WIRING_FORM.csv` (54 fix rows by
V3.0.70 line id), `tests/t714_formwork_bounds`. No engine, candidate, rule / knowledge version, registry or frozen file
changed; nothing wired, released or VERIFIED. No drawing opened this run: every face figure is the merged formwork
ledger of the released method (r4 / r5, T-264 / T-308 / T-332, bound by T-474 and classed by T-638); every member bound
is V3.0.70 or a MERGED ledger (T-711 1e06f656, T-712 dfeb0240, T-721 9e1ed6c5). V3.0.71 (T-704) carries the same 614
formwork lines byte-for-byte (asserted per line).

## 1. Physical element and method (ERS s.2.1)

Formwork = the contact face of each cast face not cast against earth, blinding, masonry or an earlier pour (R-CONC-OWN-1;
same walk / shaft / soffit / edge-band method as the 244 released lines; contact m2 only). A member held on a bound is
held on ONE dimension with two readings (beam width, column section, beam depth, parapet RC height) or a floor only.
So the bound passes to the formwork face by face, by whether the face contains that dimension (R-T714-1):

| Face class | Meaning | Example |
|---|---|---|
| INDEPENDENT | the face does not contain the held dimension: figure stands | beam side L x (D - t) under a width conflict; soffit under a depth hold; slab edge band along a beam |
| TWO_READINGS | ledger already carries the face at both readings | column shaft drawn vs printed perimeter x clear height range; parapet 2 x (0.30 upstand .. all RC) x centreline |
| SCALED | proportional to the held dimension, recorded at the drawn reading | beam soffit x (schedule b / drawn b); ratio checked against the member's own concrete ratio (1 %) |
| CAP_ONLY | 0 .. x decided by a neighbour / unprinted framing depth | joint strips beside a stair / ring mix / held edge; D-26 / D-39 shafts |
| FLOOR_ONLY | bundled face with a depth-free part | east dome ring: soffit = plan band (T-721 least reading 1.7993 m2), inner / outer faces over the depth open |
| DEPENDENT | contains the held dimension, recorded at one unstated reading | joint face 'of a HELD column'; side of an unlabelled beam; edge band over a held column; RFI-extent column shaft |
| BLOCK | an open drawn item outside the member decides whether the face is formed | OQ-10 formed vs earth-cast; dome casting method; unprinted thickness / mark / count / drop / contact |

Line: low = sum of lows, high = sum of highs if all known; low > 0 -> BOUNDED / AT_LEAST; low 0 -> HELD BLANK with the
cap beside (never 0, never an AT_MOST printed as a quantity); a high that follows an AT_LEAST member's open reading is
dropped. Directed rounding R-T696-1.

## 2. Result: census 370 / 370 by id

| Class after | Lines | Formwork m2 (beside, never summed into the released total) |
|---|---|---|
| BOUNDED | 26 | **87.941284 .. 103.192739** (columns 10: 59.262 .. 68.003; width-conflict beams 15: 28.391 .. 34.902; unlabelled 1F piece 0.288) |
| AT_LEAST | 32 | **>= 98.543697** (parapets 24: 81.589; columns 2: 13.441; unlabelled beams 4: 1.715; east ring 1: 1.7993; two-marks beam 1: 0.000077) |
| FIX_ROW (T-638) | 54 | 33.127058 released CALCULATED, restated by V3.0.70 id, **stale 0** |
| BLANK_NAMED | 258 | OQ-10 126; no positive floor 91 (cap beside on 59 lines, 59.38 m2); member blank 22; other drawn items 19 |

By member: RELEASED 224 (54 fix rows, 170 blank: OQ-10 / neighbour faces, unchanged from T-638); BOUNDED 73 (26
BOUNDED, 7 AT_LEAST, 40 blank: OQ-10 ground beams / footing / boundary, DEPENDENT-only faces); AT_LEAST 51 (24 parapets
+ ring + 0 ground beams: all T-712 ground-beam faces are OQ-10 or a section CONFLICT with no figure -> blank); BLANK 22.

B10-13 for the trial BOQ: released 1,027.977403 + T-638 fix rows 33.127058 = 1,061.104461 m2 (wiring, T-638) unchanged
here; beside it, 58 held lines now carry a bound (87.94 .. 103.19 + >= 98.54 m2). No freelancer formwork row exists
(FREELANCER_NO_ROW): no %; verdicts NOT_COMPARABLE.

## 3. Hand checks (Checker picks)

1. BM-GF-055 span 1 (CB2, schedule b 0.20 vs drawn 0.2502, T-402 / D-27), line L-3280c42c: side 2.310933 (walk, no
   width in it) + soffit 0.867255 at the drawn width -> 0.867255 x 0.20 / 0.2502 = 0.693249 + edge band 0.555045 =
   **3.559227 .. 3.733233 m2**. Concrete 0.347 .. 0.4338 m3: ratio 1.2501 = 0.2502 / 0.20 within 0.1 % (consistency).
   Named residual: at the schedule width the slab panel beside the beam gains L x 0.05 = 0.173 m2 of soffit, a RELEASED
   slab line (not this line; the T-277 GAP 0 .. +0.0278 m3 records the same pairing).
2. COL-1F-41 C9 (T-256 FFRS:679), line L-093b1a87: shaft 2.20 x 3.45 = 7.590 .. 2.50 x 3.45 = 8.625, joint
   0.7763 .. 0.9238 (stated vs drawn outline) = **8.3663 .. 9.5488 m2**. Concrete 0.756 .. 1.05 = 0.18 / 0.25 m2 x 4.20:
   the same two sections (0.20 x 0.90 / 0.25 x 1.00) whose perimeters are 2.20 / 2.50 (consistency).
3. Parapets: face lows = 2 x 0.30 x centreline (T-332 'P1 upstand'), the same 0.30 floor T-711 uses: family 81.588690
   m2 = 2 x 0.30 x 135.98 m; T-711 floors 8.050942 m3 / (0.30 x 135.98) = 0.197 m mean RC width (consistent with the
   0.20 drawn parapet). High (all RC) dropped: the member's upper end is open (Q-65 C material, D-39).

## 4. Held, with the cause (nothing chosen)

- 126 OQ-10 lines (ground beams, footings, boundary, pit): one designer item, the working space / excavation method
  (also B1 OQ-13). The T-712 floors do not free them: below natural ground the face may be earth-cast (0).
- PC-2F planted column L-fcb1852c: concrete bound 0.1824 .. 0.35 rests on a designer RFI over its extent (height
  2.28 .. 3.50 implied), while the shaft range 4.14 .. 4.83 m2 carries only the section readings at 3.45: DEPENDENT,
  blank (R-T714-1 RFI clause).
- Joint strips recorded 'of a HELD column' at one reading, sides of unlabelled beams (depth 0.40 .. 1.20 not printed),
  edge bands over held columns: their highs stay open; the lines with another floor become AT_LEAST.
- 7 T-712 ground-beam lines: 'CONFLICT literal 0.25 vs printed section (no depth)' faces have no figure: blank.
- Lift pit outer face / tie beam, court stretches (T-712 D-35), projection strips (T-721 D-26): member blank.

## 5. Wiring form (R-T714-2)

`out/T714_WIRING_FORM.csv`: FR-T638-1 .. 54 by V3.0.70 line id, before HELD blank, after RELEASED CALCULATED (50 split
faces 6.125058 + 4 column shafts 27.002 = 33.127058 m2), 4 companions with their recorded lo / hi; each line checked
unchanged (element id, HELD, no figure, no bound): CURRENT 54, STALE 0. The bounds of section 2 are beside the wiring
form for the formwork Gate B; whether to print them in the candidate is lane I's decision (Gate B), not taken here.

## 6. Lesson (ERS s.7, proposed)

| date | discrepancy | cause | rule | regression | status |
|---|---|---|---|---|---|
| 2026-11-11 | 73 formwork lines stayed blank on BOUNDED concrete, 51 on AT_LEAST concrete | a member's bound was not passed to its faces; the faces were recorded at one reading | the formwork follows the member's held dimension face by face: faces without it stand, faces at both readings range, proportional faces scale by the member's own ratio, faces at one unstated reading stay open, OQ-10 faces block (R-T714-1, PROJECT-INDEPENDENT) | tests/t714_formwork_bounds (V714 normal: width beam 4.60 .. 4.80, column 4.80 .. 5.40, parapet >= 6.00, ring >= 2.40; adverse: member blank, OQ-10, zero floor, unit, ratio mismatch, stale fix row, RFI extent) | PROPOSED |
