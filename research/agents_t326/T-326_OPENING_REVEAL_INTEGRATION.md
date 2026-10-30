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

## 0. r2 (2026-10-30 17:45 UTC): D-T326-1 fixed, the three ARCHED windows on their outline

Checker Gate B r1 (Verifier 2026-10-30 15:35 UTC) rejected r1 narrowly: W15 / W16 / W26 are ARCHED (T-238, MERGED
242e50b2, outline DRAWING-CONFIRMED; Checker re-walk on P7757.dxf layer 1 under T-326), but the merged T-313 r2 ledger
booked their OUTSIDE jambs and head on the band-crown rectangle (2 x d x 3.10 + d x 1.55; 2 x d x 1.70 + d x 1.20).
Everything else in r1 was accepted as checked and is NOT redone here.

| Line | Opening | r1 (rectangle) m2 | r2 (outline) m2 | Basis r2 | vs Checker hand |
|---|---|---|---|---|---|
| L-bafe179181f1 | W15 out jambs + head | 0.620 | 0.547688 | 2 x 0.080 x 2.1609 + 0.080 x 2.5243 | 0.5477 (arch 2.5240): +0.004 % |
| L-f9f1a4cddf86 | W16 out jambs + head | 0.620 | 0.547688 | as W15 | 0.5477: +0.004 % |
| L-d9ffbb4edfee | W26 out jambs + head | 0.460 | 0.40709 | 2 x 0.100 x 1.0500 + 0.100 x 1.9709 | 0.4071 (arch 1.9706): +0.007 % |

ARCH.WINDOW_REVEAL valued 12.6364 -> 12.438866 m2 (-0.197534, -1.56 %); FIN.PLASTER 580.5819 unchanged; nothing else
moves. Physical reason: the jamb faces stop at the springing (2.1609 / 1.05 above the sill / floor), the head soffit
follows the developed arch (2.5243 / 1.9709 m), not the 0.10 / 0.05 surround band crown and not the chord.

- Correction ledger (separate, pinned; the merged T-313 file is never edited, sha256 still 2cfa4211):
  `ARCHED_REVEAL_CORRECTION_T326.csv` (sha256 7cbe36f9), built deterministically by `build_arched_correction.py`
  from the pinned T-313 r2 ledger (depth d, the rectangle rows replaced, carried as ledger_*) and the pinned T-238
  `summary.json` (sha256 84b5b1f8: width, springing, crown, developed arch, status). `t326_inputs.py` applies each
  correction only if the T-313 row is still exactly the one it replaces and the correction re-derives from the outline
  (2 x d x springing / d x arch); else the build stops. Only DRAWING-CONFIRMED outlines with MEASURED outside faces
  are corrected (W15, W16, W26); W17 (curved on plan), A-GF-01 (pending check) and A-1F-01 (not drawn) stay BLANK.
- Rule R-T326-2 (every villa) in `engine/source/arch_v3028.py` (`load_inputs` outlines + `arched_face`): a valued
  jambs / head face of an opening with an ARCHED outline record must equal 2 x d x springing / d x developed arch,
  else refused (the message names the rectangle value); missing depth is refused (HELD, never a rectangle); a bad
  outline (no springing, springing not below the crown, unknown shape) is refused. The added line records the outline
  and `outline_rule: R-T326-2`. Line ids unchanged (rule id of the line stays R-T326-1).
- Tests `tests/t326_reveal_fill/test_arched_r2.py` (15): villa V326 window W4 (w 1.00, semicircle r 0.50, springing
  1.40, d 0.08) by hand 0.224 + 0.125664 = 0.349664 m2; adverse: the enclosing rectangle 0.384 refused, jambs to the
  crown refused, chord head refused, no depth refused, 4 bad outlines refused; rectangular W1 / W2 byte-identical to r1;
  Alsenan: the correction file is its build and matches T-238 (and the Checker's own walk within 0.0001 m2), the
  T-313 file untouched, W15 / W16 / W26 lines and 12.438866 total, the rectangle put back refused, an edited
  correction refused even when re-pinned. `test_t326_inputs_pins.py` expected JAMBS_HEAD 9.667 -> 9.469466 (by design).
- Validation on the r2 head (after merging working head 8f2b0354; CODEMAP / ROUTING by the tool, stale none; freeze
  0): own Drive copies P7757.dxf ab54dd55 + ST7757 9f9d1179, fresh T-167 base, full CLI `v3028_run.py`: V3_0_26
  8959989c and V3_0_27 f7972540 REPRODUCED; V3_0_28 json 6f19b32b (csv 6bd10592, ledger csv efcdfa58, diff csv
  dba4c588); `v3028_direct.py` byte-identical 6f19b32b; the r1 code (ff04ac6c) re-run on the same V3.0.27 gives
  a410b6fc (= the Checker's r1 hash): r1 -> r2 3,956 / 3,956 same ids, 3,953 byte-identical, 3 changed (above).
  Full suite tests/ + agents/ to the end on the code of the r2 head: 396 FAILED / ERROR, test by test against
  research/agents_t202/known_failures.json: 395 listed + tests/t212_guard_property (tools/label_census_v2.py, T-344,
  unclassified on the working head 8f2b0354, the Verifier's known 'label_census_v2'); christiannp WORKTREE_GITDIR
  passes here. NEW from this package: 0.
- Lessons row (ERS s.7, as proposed by the Checker): every reveal / arris / perimeter quantity of an opening reads the
  opening's OUTLINE record (T-238 class) first; R-T326-2 + its regression test; status 'fixed in T-326 r2'.

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
added once per opening / side / face group (valued faces summed in one line, held / unresolved faces in one BLANK line
naming each face, never 0) under a code the family registry already names (windows: ARCH.WINDOW_REVEAL = B4-08 'Reveals
and returns', sill and jambs / head in separate lines; through the wall: FIN.PLASTER '<kind> jambs and head' = B4-03,
as the 22 door lines; no new item code); a face already carried (the 22 FIN.PLASTER doors, a door's floor face in its threshold / closure
line) is refused a second carrier; every other line byte-identical.

## 2. BOQ lines (V3.0.27 -> V3.0.28), m2

| Population | Before (V3.0.27) | After (V3.0.28) | Evidence (WORKFLOW_CONTROLS s.5) |
|---|---|---|---|
| ARCH.WINDOW_REVEAL, 26 lines FILLED | BLOCKED_RFI blank | **2.9294 m2** MEASURED: 22 raised outside sills 2.5214 + 4 floor-level outside thresholds W15 / W16 / W25 / W27 0.4080 | DRAWING-CONFIRMED (T-313 = T-325); material UNKNOWN (no spec printed), W15 / W16 = the terrace finish continued |
| ARCH.WINDOW_REVEAL W17 | BLOCKED_RFI | unchanged (curved, UNRESOLVED) | UNKNOWN |
| ARCH.WINDOW_REVEAL W18 sill (ADDED) | no line | **0.040 m2** MEASURED | DRAWING-CONFIRMED |
| ARCH.WINDOW_REVEAL 'window reveal jambs and head (outside)' (27 ADDED) | no line | **9.6670 m2** MEASURED (jambs 6.6976 + heads 2.9694) | DRAWING-CONFIRMED; finish candidate URBAN-REVEAL-FINISH-METHOD v1 (not DC) |
| FIN.PLASTER 'door jambs and head' D-GF-07 (NARROWED) | BOUNDED 1.28 .. 1.40 | **1.400 m2** PROVISIONAL (h 2.50 printed: 2 x 0.20 x 2.50 + 0.20 x 2.00) | DRAWING-CONFIRMED height; plastered extent PROVISIONAL (frame detail) |
| FIN.PLASTER 'door jambs and head' D-GF-02 / -10 / -14, D-1F-03 / -04 (5 ADDED) | no line | **3.930 m2** PROVISIONAL (D-1F-03 0.810 = 2 x 0.15 x 2.20 + 0.15 x 1.00; the others 0.780) | ASSUMED — OWNER-APPROVED (Q-55 C door height 2.20) + head DC |
| BLANK held lines (10 ADDED) | no line | blank by name: ARCH.WINDOW_REVEAL W02 outside jambs (height HELD, D-53), W03 room side jambs / head and floor strip, outside jambs / head and threshold (curved glazing), W17 room side and outside jambs / head (curved wall); FIN.PLASTER 'gate jambs and head' D-GF-15 (width / height not established; finish of a boundary gate reveal not established), 'arch jambs and head' A-GF-01 (D-45; candidate jambs 0.660 + head 0.1836 not booked) and A-1F-01 (not drawn) | HELD / UNKNOWN |

Totals (code totals): ARCH.WINDOW_REVEAL (B4-08) valued 0 -> 12.6364 m2 = sills / thresholds 2.9694 + jambs / heads
9.6670 (27 blank lines -> 55 valued + 8 blank; the physical element tells sill from jambs / head); FIN.PLASTER valued 575.2519 -> 580.5819 m2 (+3.930 added + 1.400 narrowed), bound 489.481 ..
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
| Finish | URBAN-REVEAL-FINISH-METHOD v1 candidate (default plaster; WIN-REVEAL owner decision queued) | area only; finish not drawing-confirmed; the jambs / head lines' item text says 'finish to be confirmed' |

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
- Totals moved only on ARCH.WINDOW_REVEAL and FIN.PLASTER m2 (asserted); every other item byte-identical. No new item
  code: the first design booked the jambs / heads under a new code ARCH.REVEAL, which the L4 suite refused
  (tests/t130_family_master: every written code belongs to one family; BOQ_FAMILY_MASTER 1.1.0 is frozen), so they sit in
  B4-08's own code as the registry intends; a consumer separating sills from jambs uses the physical element.

## 7. Validation

- Own Drive copies this run ('Alsenan chalet project': P7757_DXF_COMPRESSED.zip -> P7757.dxf `ab54dd55`, 'ST7757
  dxf.dxf' `9f9d1179`), decoded into the private folder only; fresh T-167 base run, then the full CLI run
  `research/agents_t326/v3028_run.py` (`tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V3.0.28 --v3028-inputs`):
  **V3_0_26 json 8959989c and V3_0_27 json f7972540 reproduced (= the candidate of record, T-318 Gate B)**; V3_0_28 json
  a410b6fc / csv ded019b0, ledger csv b43c605c, diff csv 3b41c1a9, run json 4586eaee; `v3028_direct.py` on the same
  V3_0_27 gives the same json byte for byte. Independent re-derivation of the 59 valued lines + the narrowing straight
  from REVEAL_LEDGER_T313.csv (not through t326_inputs): 0 mismatches, 16.5664 m2.
- tests/t326_reveal_fill: villa V326 by hand (not Alsenan): fill 0.096 (never the 0.240 plan strip), W1 jambs + head 0.336,
  W2 sill 0.048 + jambs / head 0.144, D1 0.795, D3 narrowed 1.400, W3 blank; outside lines byte-identical, D2 not added,
  order invariance, held text states no result, no new item code, files / totals; adverse: sill and jambs mixed in one
  line, a face carried by a closure line filled again, shared jamb counted twice, a door's floor face in a
  reveal line, held as 0, valued at 0, fill of a non-blank line, fill with jambs, two windows on one line, narrow outside
  the bound, faces not summing, stale line, stale bound, units, missing source, source without checker run, unknown face,
  plaster reveal on a window, applied twice, outside line changed, double booking on finished lines; Alsenan pins
  (counts, 13.637 m2, 2.9294 m2, each face once, edited ledger stops the build); master 1.23.0 (builder, checks clean,
  dropping the entry is stale).
- L4 full suite and freeze: in the board handoff (run on the final commit).

## 8. For the Checker (Gate B always-checked lines)

The jambs / heads are a newly introduced scope: every such line is always-checked by rule. Suggested re-derivations: W01 fill
L-0de10f4db591a2467b82 0.120 (0.100 x 1.200) and jambs / head L-2d36229b4db5c798dc3b 0.520 (2 x 0.100 x 2.000 + 0.100 x
1.200); W15 floor-level threshold L-0e2e7299371efb8338cc 0.124 and jambs / head L-bafe179181f10f0a85af 0.620; W18 sill
L-cd88cb0d77ee82dc7259 0.040 and jambs / head L-0b1e539750a921554749 0.3856 (2 x 0.080 x 2.160 + 0.080 x 0.500); W02
head L-429605a88ef09abda085 0.5064 beside its blank jambs L-bcc55693d203e384d46e; D-1F-03 L-f0668097e8d872925fdf 0.810;
D-GF-07 L-2f94dca4dd5f2ec05822 1.400.

## 9. Lessons-register row (proposed)

| 2026-10-30 | 27 reveal-strip lines stayed blank and 13.637 m2 of reveal faces had no line for two days after a merged ledger bound every face | the ledger was research keyed by opening and line id and no package consumed it; the strip line's w x wall basis mixed a finish face with the frame bed | book reveal faces face by face from the merged ledger: fill a strip line with the external face only, add unlined faces once per opening / side / item, refuse a second carrier (door reveals in plaster, door floor faces in threshold lines), held faces BLANK by name (every villa) | tests/t326_reveal_fill (normal: villa V326 0.096 / 0.336 / 0.795 / 1.400 m2; adverse: shared jamb twice, door floor face in a reveal line, held as 0, plan strip as fill) | PROPOSED |
