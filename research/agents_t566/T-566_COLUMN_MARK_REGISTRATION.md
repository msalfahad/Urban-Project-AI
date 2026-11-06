# T-566 GF column mark registration from the drawings alone, and the B10-07 beam UNTRACED -0.365 m3 named

Worker 1 (lane S, non-candidate, backlog-permitted), 2026-11-06, run session_01E6cPnd5ziDtQa7C7YRG2tV, branch
`agents/task-T-566`. Research only: no engine, candidate, released line, rule file or method version changed; nothing
released; no quantity moves (both CONFLICT positions are HELD lines). Development villa, not an accuracy claim. ERS
s.2.1 - 2.6, s.3, s.4, s.7 applied. Answers the Checker's T-551 note (2026-11-06 11:59): "the GF column frame is
label-free; the neck frames carry C3 x5 and x6 labels, so GF C3 +1 = 0.469 m3 rests on the merged T-217 / T-394
registration, not on a re-measure"; and T-545's UNRESOLVED -0.365289 m3.

## 0. Sources and run

- Drawing: Drive "Alsenan chalet project" / 'ST7757 dxf.dxf' (sha256 9f9d1179..., the route G input), downloaded this
  run, decoded into `.work/private` only. `t566_extract.py` is an OWN read: frame fields found by clustering the
  S-COL.BON outlines in x (6 fields, the frame titles name them), each frame's translation onto the FOUNDATION PLAN
  measured from equal-size outlines (CAP -38 724, GBP +38 724, GFRS +77 449, FFRS +116 173, SFRS +154 898 mm), labels bound
  to outlines inside each sheet by a minimum-total-distance assignment (scipy), never nearest-first. The T-205 / T-217 /
  T-394 marks are compared afterwards, never used. Committed `POSITION_INPUT_T566.json`: handles, marks, sizes; no
  coordinates.
- Engine: candidate ARCH_TAKEOFF_V3.0.58 (NOT RELEASED); column / beam lines = `agents_t507/out/LINE_INDEX_V3_0_57.json`
  (R-T507-1 (e)); line of each drawn member named through the T-394 per-line member handle (GFRS:350 -> line id).
- Freelancer (only for the T-551 re-split and the beam row checks): Drive "Alsenan chalet project", the concrete + rebar
  workbook, read with openpyxl into memory; tracked output carries m3 terms only.

```
python3 -I research/agents_t566/t566_extract.py .work/private/ST7757.dxf --write
python3 -I research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/st7757_route_g .work/private/t566/bands.json
python3 -I research/agents_t566/t566_alsenan.py --freelancer .work/private/concrete_rebar.xlsx --bands .work/private/t566/bands.json --write
```

## 1. The physical element (ERS s.2.1)

A column position is one neck outline on the foundation sheets (FP / CAP / GBP draw the same 36 / 35 / 36 outlines under
one translation). The member above it on each storey is the SOLID-hatched outline on that storey's roof-slab plan
within 400 mm (T-217 hatch convention). The slab plans print NO column label (searched: the only mark-like text on
GFRS is 'C' 173A on layer S-SEC-TEXT, a section-cut letter beside two 'D's; FFRS / SFRS none), so a storey member's mark
can only come by continuity from the labels printed at its neck position (R-T566-3); its section per storey is the
schedule band of that mark (GR / 1ST / 2ND), a section change is never a new mark.

## 2. Position table (R-T566-1; `out/T566_REGISTRATION.json` "positions")

36 positions: **34 REGISTERED** (33 with 3 / 3 sheets, 180A 2 / 2: CAP draws no outline there, T-042), **2 CONFLICT**,
0 HELD. The FP label equals the merged T-205 mark at 36 / 36; the registered mark equals it at 34 / 34.

| Position (FP outline) | FP | CAP | GBP | Neck drawn / CAP text | GF member (line, class) | 1F member | Class |
|---|---|---|---|---|---|---|---|
| 10AE | C3 1681 | C3 100A | **C 20D** | 0.30 x 0.50 / 30X50 | GFRS 350 0.20 x 0.40 (L-694a75c8, HELD annex) | none | **CONFLICT C3 / C** |
| 10E0 | C8 10E1 | C8 101A | **C7 24E** | 0.30 x 0.80 / 30X80 | GFRS 380 0.25 x 0.80 (L-4c449657, HELD) | FFRS 69A 0.25 x 0.80 (L-1dc713c8, HELD) | **CONFLICT C8 / C7** |
| 10A0, 10B1, 10C5, 10CC, 10E4 | C3 | C3 | C3 | 0.30 x 0.50 / 30X50 | 344 H, 353 H, 365 R, 36B R, 383 R | 68B (10C5), 691 (10CC) | REGISTERED C3 |
| 10A4, 10A8, 10AB, 10B4, 10B7 | C | C | C | 0.30 x 0.50 (10B7 0.30 x 0.40) / 30X50 | 347, 34A, 34D, 356, 359 (all HELD) | none | REGISTERED C |
| every other position (24) | = | = | = | | | | REGISTERED (3 / 3, or 2 / 2) |

Section evidence beside the conflicts (R-T566-2; information for the designer, never a resolution):

- **10AE**: FOU 30 x 50 for both C and C3 (no discrimination); the GF outline 0.20 x 0.40 differs from both GR bands
  (C 20 x 50, C3 25 x 50) and equals the drawn section of the five C positions; no 1F member. Labels FP + CAP vs GBP.
  The GBP label 20D 'C' sits 0.26 m from its outline (next outline 4.6 m): the binding is not ambiguous. (GBP draws the
  neck there 0.30 x 0.40, outline 20B, as at three C positions: T-217 DRAFTING_NOTE.)
- 10E0 binding margin: GBP 24E 'C7' 0.86 m from its outline, next outline 1.99 m (that one, 10E4, carries its own C3 252).
- **10E0**: every printed / drawn size fits **C7** (schedule FOU 30 x 80 = CAP text 30X80 = CAP dims 0.80 x 0.30 = drawn
  neck; GR 25 x 80 = GFRS 380; 1F 69A 0.25 x 0.80 vs C7 1ST 20 x 80 differs in width only), none fits C8 (FOU 30 x 90,
  GR 25 x 90, 1ST 20 x 90). This is why T-217 found printed-vs-printed CONFLICTs at C8/F14: under the GBP reading they
  vanish on FOU / GF. Still CONFLICT by R-T566-1 (two printed labels differ; never resolved by a section match).

**GF count by mark** (30 GF members over necks): REGISTERED C 5, C1 1, C2 4, **C3 5**, C4 2, C5 3, C6 1, C7 1, **C8 1**,
C9 2, C10 1, C11 2 = 28, + 2 CONFLICT (10AE C3 | C, 10E0 C8 | C7). The Checker's 'C3 x5 and x6': CAP and FP print six C3
(including 10AE), GBP five (10AE printed 'C'). The registered C3 count is **5**, the sixth is CONFLICT.

**Bounds** (R-T566-4, section area over the candidates' bands and the drawn outline): 10AE GF 0.080 .. 0.125 m2; 10E0
GF 0.200 .. 0.225 m2, 1F 0.160 .. 0.200 m2. All three lines are already HELD (annex roof unprinted Q-54 B / D-39;
section CONFLICT D-16 / D-63): no released quantity changes.

## 3. Effect on the merged T-551 column split (engine - his, m3; `t551_resplit`)

The storey residuals never move (GF -1.945, 1F -3.444): a conflict only moves m3 between COUNT and HELD (count binding
of held lines, R-T551-1). The merged T-551 split = the reading (10AE C3, 10E0 C8), reproduced exactly (test).

| Reading 10AE / 10E0 | GF COUNT | GF HELD | 1F COUNT | 1F HELD | GF C3 COUNT | GF C COUNT |
|---|---|---|---|---|---|---|
| C3 / C8 (merged T-551) | -0.562500 | -4.125000 | +0.414000 | -4.623000 | +0.468750 | 0 |
| C / C8 | -0.656250 | -4.031250 | +0.414000 | -4.623000 | 0 | +0.375000 |
| C3 / C7 | -0.656250 | -4.031250 | +0.345000 | -4.554000 | +0.468750 | 0 |
| C / C7 | -0.750000 | -3.937500 | +0.345000 | -4.554000 | 0 | +0.375000 |

So **GF C3 COUNT +0.469 m3 is CONFLICT-BOUNDED (0 .. +0.469), not ENGINE_RIGHT**: his five C3 equal the five
registered C3; the sixth depends on 10AE. Under C7 at 10E0 his C7 / C8 split (one C7, two C8, matching FP / CAP) would be
-1 C8 +1 C7 on GF and 1F. Verdict proposals: GF C3 count and GF / 1F C7 / C8 counts **UNRESOLVED-CONFLICT (designer
item)**; every other T-551 COUNT term stands (C1, C2, C9, C11, 1F C3 / C9 positions are REGISTERED 3 / 3).

## 4. Beam UNTRACED -0.365289 m3 named per mark (R-T566-5; `beam_untraced`)

| Mark | m3 | Cause | Verdict proposal | Evidence (drawn; his rows in memory only) |
|---|---|---|---|---|
| GF B11, GF B8, 1F B11, 1F B6 | +0.004050, +0.003021, +0.007173, +0.000273 = **+0.014517** | DRAWING_PRECISION | ENGINE_RIGHT | one row of his per drawn run, differing from the drawn line by < 0.05 m (his lengths printed to 0.05 m) |
| 2F B2 | **-0.087240** | COUNT | ENGINE_RIGHT (Checker re-counts the 2F B2 labels) | his rows equal the four drawn face-to-face B2 runs run by run (2.499, 3.000, 1.800, 3.000) plus one more 2.5 m row; no fifth drawn B2 run; every 2F B2 end frames into a perpendicular beam. The mark residual -0.200 is that one row: this UNTRACED -0.087240 **plus T-545's THROUGH_SUPPORT -0.112760 on this mark**, which is a count, not a through-support length (his lengths are face to face here) |
| GF B2 | **-0.011152** | MARK_BOUNDARY | ENGINE_RIGHT (drawn labels) | BAND0020.2 (B2) runs on through column 36B (gap 0.498 m) into BAND0020.1, 0.200 x 0.803 m, labelled B1 and billed once under B1; his excess beyond the B2 support allowance (0.139 m) fits inside that piece |
| 1F CB12 | **-0.160962** | BEYOND_EXTENT | ENGINE_RIGHT (proposal) | drawn outer-face extent 5.626 + 0.899 (over 664) + 5.025 + end supports 69D 0.20 / 676 0.25 = 12.00 m; his one row is longer; no collinear beam continues CB12 (B6 BAND0021, B4 BAND0015 perpendicular; BM-1F-036 BAND0025 lies beside BAND0018.2 sharing its long face) |
| GF B7 | **-0.120452** | UNRESOLVED (named) | UNRESOLVED | his longer B7 row has no location (T-252 / T-392 s.3); drawn B7 = three straight runs + void ring RING-B7 0.499805 m3 (T-392); his total exceeds the drawn outer-face extent incl. the ring by 0.80 m at 0.20 x 0.75 |
| **Total** | **-0.365289** | re-adds exactly (test) | | |

Net: of -0.365 m3, +0.015 is drawing precision and -0.259 is ENGINE_RIGHT by a named drawing cause (count, mark boundary,
extent); **-0.120 (GF B7) stays UNRESOLVED by name**. If the Checker accepts the 2F B2 re-class, T-545's 2F THROUGH_SUPPORT
becomes -0.420000 (from -0.532760) and 2F COUNT -0.200000: a split change, no total change (no line changed).

## 5. Who is right, what is open

- ENGINE_RIGHT (proposals): beam DRAWING_PRECISION +0.015, 2F B2 COUNT -0.200 (incl. the re-classed -0.113), GF B2
  MARK_BOUNDARY -0.011, 1F CB12 BEYOND_EXTENT -0.161; 34 positions REGISTERED with the merged marks (T-205 / T-217 now
  re-measured independently).
- CONFLICT (designer, not owner): 10AE C3 vs C, 10E0 C8 vs C7: both GF lines and the 1F 69A line already HELD. Proposed
  addition to the designer RFI list (D-16 / D-63 column sections): "10AE: FP / CAP print C3, GBP prints C; 10E0: FP / CAP
  print C8, GBP prints C7 (and every size printed or drawn at 10E0 is the C7 band): confirm the marks". ERS s.2.7 not
  met (no released quantity depends on it, the designer owns it): **no owner question**.
- UNRESOLVED: GF B7 -0.120452 m3 (his row without a location).
- Uncertain: 1F B6 precision term rests on T-395's run binding of his row (by length); the 2F B2 COUNT reading binds his
  rows to runs by equal length (0.005 m) - the Checker re-counts the B2 labels on the 2F roof sheet.

## 6. Rules, tests, lessons row (proposed)

R-T566-1 .. 5 (`t566_rules.py`). `tests/t566_column_mark_registration` (20): hand villa V566 (3 x 2 grid, two label
sheets, one disagreeing position, one sheet without a label, a 1F section change registered by continuity, rotation /
mirror / units), adverse (mark from a label count refused, freelancer count / row refused, no label = HELD, non-label
text refused, mm refused, UNRESOLVED as 0 refused, open sum refused, nearest-first label binding shown wrong), the
development villa from committed files (34 / 2, counts, bounds, slab frames label-free, beam closure, the merged T-551
split reproduced, residual invariant over readings) and the private rebuilds (extract = committed input; re-split and row
checks = committed).

Lessons row (ERS s.7): | 2026-11-06 | GF C3 +0.469 m3 carried as ENGINE_RIGHT on one sheet's labels; the label-free GF
frame took its marks from one binding | two label sheets of the same plan disagree at two positions (GBP vs FP / CAP) |
a column mark is registered per position from EVERY sheet that prints labels, each bound by a minimum-total assignment;
a disagreement is a CONFLICT with its bound, never a majority (every villa; provenance T-566, R-T566-1 .. 4) |
tests/t566_column_mark_registration | PROPOSED |

## 7. Checker re-measure list

- `test_private_extract_equals_committed_input` with `.work/private/ST7757.dxf`; GBP labels 20D at 10AE and 24E at 10E0
  (text and position), FP 1681 / 10E1 and CAP 100A / 101A.
- 2F roof sheet: number of B2 labels / runs (four drawn); GF BAND0020.1 label B1.
