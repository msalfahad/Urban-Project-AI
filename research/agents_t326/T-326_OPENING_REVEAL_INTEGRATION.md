# T-326: opening reveals in the candidate (ARCH_TAKEOFF_V3.0.28), integration package for Gate B

Worker 3 (lane I), 2026-10-30 UTC. Development villa, not an accuracy claim. Opt-in candidate only: the released
default stays ARCH_TAKEOFF_V2.9 + route G; nothing is released. No client name, coordinate or image is committed;
drawings are cited by Drive title only.

integrates: T-313 (r2, MERGED 5f2bf0d5, Verifier 2026-10-29 01:24 UTC Gate A PASS: the opening reveal ledger, every
census opening once per side and face, the all-family search, the 22 door reveals bound to FIN.PLASTER), T-325 (MERGED
98f50f0f, Verifier 2026-10-29 04:59 UTC Gate A PASS: the second read of every external sill / floor-level threshold,
and the correction of T-313's five 'no line' doors: each carries a BLOCKED threshold / closure strip = that door's FLOOR
face). Inputs: `research/agents_t326/t326_inputs.py` reads REVEAL_LEDGER_T313.csv, FAMILY_SEARCH_T313.csv,
DOOR_PLASTER_RECONCILIATION_T313.csv and SILL_THRESHOLD_LEDGER_T325.csv, each pinned by sha256; nothing is typed; the
T-325 sill figures must equal T-313 row by row or the build stops (26 / 26 equal).

## 1. The physical question and the answer (ERS s.2.1, s.3)

The element is ONE FACE of the wall thickness at an opening: a jamb, the head soffit, the outside sill (raised window)
or the floor-level threshold, on the room side, the outside, or once through the wall (door / arch / gate). The drawn
evidence (T-313, Checker re-measured): all 27 straight windows sit in 0.200 m walls with the frame band (0.120, or 0.100
m) drawn FLUSH with the room face, so the room side has no reveal (NONE, by evidence, not 0 by default) and the outside
reveal is 0.080 / 0.100 m deep; doors have one reveal through the wall (UP-FIN-PLASTER-001: 2 x t x h + t x w).

What the candidate carried before (V3.0.27): 27 ARCH.WINDOW_REVEAL lines, all BLOCKED_RFI blank, 'strip faces in the
wall thickness' (the w x 0.20 plan strip: frame bed + sill); 22 FIN.PLASTER 'door jambs and head' lines (20 equal to
the ledger, D-GF-01 / D-GF-07 a class bound); NO line for any window jamb or head, W18's sill, or five doors' reveals.

Rule **R-T326-1** (engine/source/arch_v3028.py, every villa): a reveal face is booked in ONE line; a blank reveal-strip
line is filled with the external sill / threshold surface only (the frame bed is not a finish surface); a door bound held
for a pending height class is narrowed to the printed height when the drawing prints it; a face no line carries is
added once per opening / side / item (valued faces summed in one line, held / unresolved faces in one BLANK line naming
each face, never 0); a face already carried (the 22 FIN.PLASTER doors, a door's floor face in its threshold / closure
line) is refused a second carrier; every other line byte-identical.

## 2. BOQ lines (V3.0.27 -> V3.0.28), m2

| Population | Before (V3.0.27) | After (V3.0.28) | Evidence (WORKFLOW_CONTROLS s.5) |
|---|---|---|---|
| ARCH.WINDOW_REVEAL, 26 lines FILLED | BLOCKED_RFI blank | **2.9294 m2** MEASURED: 22 raised outside sills 2.5214 + 4 floor-level outside thresholds W15 / W16 / W25 / W27 0.4080 | DRAWING-CONFIRMED (T-313 = T-325); material UNKNOWN (no spec printed), W15 / W16 = the terrace finish continued |
| ARCH.WINDOW_REVEAL W17 | BLOCKED_RFI | unchanged (curved, UNRESOLVED) | UNKNOWN |
| ARCH.WINDOW_REVEAL W18 sill (ADDED) | no line | **0.040 m2** MEASURED | DRAWING-CONFIRMED |
| ARCH.REVEAL window outside jambs + head (27 ADDED) | no line | **9.6670 m2** MEASURED (jambs 6.6976 + heads 2.9694) | DRAWING-CONFIRMED; finish candidate URBAN-REVEAL-FINISH-METHOD v1 (not DC) |
| FIN.PLASTER 'door jambs and head' D-GF-07 (NARROWED) | BOUNDED 1.28 .. 1.40 | **1.400 m2** PROVISIONAL (h 2.50 printed: 2 x 0.20 x 2.50 + 0.20 x 2.00) | DRAWING-CONFIRMED height; plastered extent PROVISIONAL (frame detail) |
| FIN.PLASTER 'door jambs and head' D-GF-02 / -10 / -14, D-1F-03 / -04 (5 ADDED) | no line | **3.930 m2** PROVISIONAL (D-1F-03 0.810 = 2 x 0.15 x 2.20 + 0.15 x 1.00; the others 0.780) | ASSUMED — OWNER-APPROVED (Q-55 C door height 2.20) + head DC |
| BLANK held lines (10 ADDED) | no line | blank by name: W02 outside jambs (height HELD, D-53); W03 room side jambs / head / floor strip and outside jambs / head / threshold (curved glazing); W17 room side and outside jambs / head (curved wall); gate D-GF-15 (width / height not established); A-GF-01 (D-45; candidate jambs 0.660 + head 0.1836 not booked); A-1F-01 (not drawn) | HELD / UNKNOWN |

Totals (code totals): ARCH.WINDOW_REVEAL valued 0 -> 2.9694 m2 (27 -> 3 blank lines); ARCH.REVEAL new 9.667 m2 on 27
valued + 8 blank lines; FIN.PLASTER valued 575.2519 -> 580.5819 m2 (+3.930 added + 1.400 narrowed), bound 489.481 ..
545.4606 -> 488.201 .. 544.0606 (the D-GF-07 bound leaves). Net new physical scope: 13.637 m2 (= the T-313 r2 restated
missing scope) + 2.9294 m2 now valued in the formerly blank strip lines; D-GF-07 +0.120 / 0.000 against its bound.

Identity: 3,913 -> 3,956 lines; 27 replaced (26 FILL + 1 NARROW, all CHANGED), 43 added (33 valued + 10 held), 3,886
byte-identical (outside_rows_sha256 3c168091...). Released V2.9: the 26 filled lines exist there BLOCKED (QUANTITY_DIFFERS
now), the D-GF-07 line QUANTITY_DIFFERS; the 43 added lines NOT_IN_RELEASED. Line-by-line diff: V3_0_28_DIFF.csv; per
line before / after / faces / evidence: V3_0_28_INTEGRATION_LEDGER.csv (both in the run output, not committed).

## 3. Owner manual method and drawing-derived method side by side

| | Owner manual method | Drawing-derived (carried) |
|---|---|---|
| Window reveal | UP-REVEAL-001: 2 x depth x height + depth x width where a reveal exists; the sill its own item | room side NONE (frame flush, drawn); outside 0.080 / 0.100 m x T-237 sizes; the two agree (no room-side reveal under either) |
| Door reveal | UP-FIN-PLASTER-001: 2 x t x h + t x w through the wall (frame detail decides the plastered extent: PROVISIONAL) | t T-150, w T-237, h printed (D-GF-07 2.50) or Q-55 C 2.20 (ASSUMED — OWNER-APPROVED) |
| Finish | URBAN-REVEAL-FINISH-METHOD v1 candidate (default plaster; WIN-REVEAL owner decision queued) | area only; finish not drawing-confirmed; ARCH.REVEAL 'finish to be confirmed' |

## 4. Against the freelancer (not proof)

Freelancer: no reveal line (reveals inside his plaster / paint lumps): RULE_DIFFERENCE (scope), no % (T-313). Verdict
proposals stand from the merged ledger: the 20 FIN.PLASTER doors ENGINE_RIGHT; D-GF-07 low end 1.28 ENGINE_WRONG (the
drawing prints 2.50; now 1.400); window outside jambs / heads, W18 sill and the five doors ENGINE_WRONG (missing scope,
now added); the strip lines' w x 0.20 basis ENGINE_WRONG (now the outside sill only).

## 5. Evidence status, missing and held

- DRAWING-CONFIRMED: 26 fills 2.9294 m2, W18 sill 0.040 m2, 27 window outside reveal lines 9.667 m2, D-GF-07 height
  (1.400 m2, extent PROVISIONAL); VERIFIED: none here
  (the ledgers are Checker-verified; the integrated lines await Gate B).
- ASSUMED — OWNER-APPROVED: the jambs of the five added doors (Q-55 C, h 2.20), as the 20 doors already in FIN.PLASTER.
- HELD / UNKNOWN (10 blank lines, never 0): see section 2. Not in this package: the finish of every reveal face (WIN-REVEAL
  queued), the external-sill material (UNKNOWN, by specification), D-GF-01 (main-entrance class still 2.20 / 2.50: its
  bound stays), the five T-325 closure strips (door floor faces: retyped by T-327, never here).
- T-351 integration note (pantry FIN.WALL.TILE +0.0328 m2): this package carries no FIN.WALL.TILE line; it stays for
  the next package that does.

## 6. Downstream consistency (cross-trade, double count)

- Each face once: 109 faces booked by a V3.0.28 reveal record, none twice (asserted on the finished lines); the 22
  FIN.PLASTER door lines' jambs / heads and the 27 door floor faces (T-325 threshold / closure lines) are inputs as
  CARRIED and refused a second carrier (two adverse tests). Independent re-derivation of all 59 valued lines (+ the
  narrowing) from REVEAL_LEDGER_T313.csv: 0 mismatches, 16.5664 m2.
- Room wall faces: plaster / paint lines deduct the opening areas only (Q-73) and carry no return face; the candidate has
  no FIN.PLASTER 'window reveals' line (room side NONE agrees). Facade: Q-64 B straight run excludes the return faces
  'measured under the window reveal finish': the 0.080 / 0.100 m outside jambs ARE those faces; the exterior plaster
  package (T-314) must not add them again (named for its integration).
- Pool court: the OD-07 deck line names an 'SX-02 reveal strip 0.561577 m2' excluded from the deck: the curved glazed
  band's outside floor strip (W03 outside threshold here, BLANK): when W03 is resolved, that strip is its candidate figure,
  once.
- Totals moved only on ARCH.WINDOW_REVEAL, ARCH.REVEAL and FIN.PLASTER m2 (asserted); every other item byte-identical.

## 7. Validation

- Own Drive copies this run ('Alsenan chalet project': P7757_DXF_COMPRESSED.zip -> P7757.dxf `ab54dd55`, 'ST7757
  dxf.dxf' `9f9d1179`), decoded into the private folder only; fresh T-167 base run, then the full CLI run
  `research/agents_t326/v3028_run.py` (`tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V3.0.28 --v3028-inputs`):
  **V3_0_26 json 8959989c and V3_0_27 json f7972540 reproduced (= the candidate of record, T-318 Gate B)**; V3_0_28 json
  dd0ad4b2 / csv 08cef00c, ledger csv bd280cf5, diff csv 37310a71.
- tests/t326_reveal_fill: villa V326 by hand (not Alsenan): fill 0.096 (never the 0.240 plan strip), W1 reveal 0.336,
  W2 sill 0.048 + reveal 0.144, D1 0.795, D3 narrowed 1.400, W3 blank; outside lines byte-identical, D2 not added, order
  invariance, held text states no result, files / totals; adverse: shared jamb counted twice, a door's floor face in a
  reveal line, held as 0, valued at 0, fill of a non-blank line, fill with jambs, two windows on one line, narrow outside
  the bound, faces not summing, stale line, stale bound, units, missing source, source without checker run, unknown face,
  plaster reveal on a window, applied twice, outside line changed, double booking on finished lines; Alsenan pins
  (counts, 13.637 m2, 2.9294 m2, each face once, edited ledger stops the build); master 1.23.0 (builder, checks clean,
  dropping the entry is stale).
- L4 full suite and freeze: in the board handoff (run on the final commit).

## 8. For the Checker (Gate B always-checked lines)

ARCH.REVEAL is a new item and a new scope: every line is always-checked by rule. Suggested re-derivations: W01 fill
L-0de10f4db591a2467b82 0.120 (0.100 x 1.200) and reveal L-18697e07350593a76139 0.520 (2 x 0.100 x 2.000 + 0.100 x
1.200); W15 floor-level threshold L-0e2e7299371efb8338cc 0.124 and reveal L-5e0394fc1ed614745eb7 0.620; W18 sill
L-c38a451ea827e373ac0d 0.040 and reveal L-dc22c7e4e0de36e98c08 0.3856 (2 x 0.080 x 2.160 + 0.080 x 0.500); W02 head
L-7d3fc14b52969c328c2e 0.5064 beside its blank jambs L-85014bdb76140dad2ae3; D-1F-03 L-28bdec18307660786387 0.810; D-GF-07
L-2f94dca4dd5f2ec05822 1.400.

## 9. Lessons-register row (proposed)

| 2026-10-30 | 27 reveal-strip lines stayed blank and 13.637 m2 of reveal faces had no line for two days after a merged ledger bound every face | the ledger was research keyed by opening and line id and no package consumed it; the strip line's w x wall basis mixed a finish face with the frame bed | book reveal faces face by face from the merged ledger: fill a strip line with the external face only, add unlined faces once per opening / side / item, refuse a second carrier (door reveals in plaster, door floor faces in threshold lines), held faces BLANK by name (every villa) | tests/t326_reveal_fill (normal: villa V326 0.096 / 0.336 / 0.795 / 1.400 m2; adverse: shared jamb twice, door floor face in a reveal line, held as 0, plan strip as fill) | PROPOSED |
