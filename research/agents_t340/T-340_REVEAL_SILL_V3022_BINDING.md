# T-340: reveals, sills and thresholds bound to the V3.0.22 line ids, with the wet-room cross-check (integration dependency of T-326 / T-327)

Worker 3 (lane A row, lane I had no claimable row), 2026-10-29. Development villa, not an accuracy claim. Research only:
no engine module, candidate line or released line changes; V2.9 + route G stays the default; lane I applies the two
FILL tables (T-326 reveals, T-327 sills / thresholds) unchanged. Drawings are named by Drive folder and title only
("Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip, sha256 ab54dd55..; "ST7757 dxf.dxf" 9f9d1179..).
ERS s.2 - s.4 and s.7 applied; no owner question (s.2.7: every open item is a designer / specification item or is
settled by an answered rule).

## 1. Run and identity

Own run on the two Drive copies (decoded into the private folder only): research/agents_t167/v304_run.py (27 min), then
research/agents_t331/v3022_run.py. **V3_0_20 json `097a80b6` / csv `ca90351b`, V3_0_21 json `be22a4e4` / csv
`3548e39c`, V3_0_22 json `7199c8b6` / csv `924a60b4` REPRODUCED** (= the candidates of record; V3.0.22 = T-331 Gate B).
Extract `t340_alsenan.py --extract` -> CANDIDATE_V3022_T340.json (191 lines of the seven families FIN.PLASTER,
ARCH.WINDOW_REVEAL, ARCH.THRESHOLD, FIN.MARBLE.THRESHOLD, FIN.FLOOR.PORCELAIN, FIN.WALL.TILE, FIN.WP.DOORWAY: ids, item
codes, element ids, units, states, quantities, a digest of each line in V3.0.20 / V3.0.21 / V3.0.22; no coordinates, no
names). **LINE_REBIND_T340.csv: all 92 carrier lines (every line a component is bound to, plus the 14 WP doorway lines)
are byte-identical in V3.0.20, V3.0.21 and V3.0.22**: the T-313 r2 / T-325 ledgers, verified on V3.0.20, bind to the
candidate of record unchanged; no family line is gone since V3.0.20.

## 2. Physical elements (ERS s.2.1) and the binding rule

One component = one physical surface of one opening, once: per window and side its jambs and its head (a held jamb never
hides a measured head), its sill (raised window) or floor-level strip; per door / gate / arch ONE reveal through the
wall (jambs, head; no sill) and one threshold strip (clear width x wall thickness, UP-THR-001). The window sill and the
floor-level strip are described by BOTH ledgers (T-313 as a reveal row, T-325 as its own item): they are one surface,
merged with an area-equality check (all 27 agree to the mm2; a disagreement stops the build). The finish-change edge is
geometry, never a line (R-T325-1). 59 census openings (T-249) -> **264 components, each with exactly one owner**
(OWNERS_T340.csv), on **120 carriers** (existing line or NEW row; one carrier, one opening).

R-T340-BIND-1 (project-independent research rule, not a rule-file version; provenance UP-REVEAL-001,
UP-FIN-PLASTER-001, UP-THR-001, UP-FIN-PAINT-001 substrate, Q-55 C, Q-37 A, URBAN-REVEAL-FINISH-METHOD v1, T-313 r2 /
T-325 / T-336 verdicts): one component, one owner (two refused); a door reveal carried by a FIN.PLASTER 'door jambs and
head' line stays only there (a second carrier refused), a door with none gets one NEW row in the same family; sills and
thresholds are their own item (a reveal in a sill line, or a threshold in a reveal line, refused); a backing / tile face
is the wall face less each opening's part in the band, a reveal is not a wall face (face closure recomputed; a reveal
owned by a backing / tile line refused); a superseded figure (closure polygon) is refused; HELD / UNKNOWN blank, never 0.

## 3. FILL table T-326 (reveals; FILL_T326_T340.csv, 61 carriers)

| Action | Carriers | m2 | Evidence status | Detail |
|---|---|---|---|---|
| KEEP (FIN.PLASTER 'door jambs and head') | 21 | 18.820 | 20 ASSUMED — OWNER-APPROVED (Q-55 C 2.20 jambs) + D-GF-01 within bound 1.08 .. 1.20 | EQUAL, residual 0.000000 each (T-313 r2 per-door reconciliation re-checked against V3.0.22) |
| NARROW L-2f94dca4 (D-GF-07) | 1 | 1.400 | DRAWING-CONFIRMED (printed 2.50, T-201 / T-237) | bound 1.28 .. 1.40 -> 1.400 |
| ADD_ROW FIN.PLASTER door jambs and head (D-GF-02, D-GF-10, D-GF-14, D-1F-03, D-1F-04) | 5 | 3.930 | ASSUMED — OWNER-APPROVED (jambs 3.300, Q-55 C) + DRAWING-CONFIRMED (heads 0.630) | missing scope (no line in any family; T-325 re-located only their THRESHOLDS) |
| ADD_ROW REVEAL.WINDOW_OUT (window outside jambs + head) | 27 | 9.667 | DRAWING-CONFIRMED | jambs 6.6976 + heads 2.9694; W02 head 0.5064 carried, its jambs HELD beside (height D-53) |
| ADD_HELD_ROW | 7 | blank | HELD / UNKNOWN | W03, W17 (curved, both sides), A-GF-01 (D-45), A-1F-01 (not drawn), gate D-GF-15 |
| no carrier (room side) | - | 0 by evidence | NOT_APPLICABLE_WITH_EVIDENCE | frame flush with the room face on all 27 straight windows (T-313) |

**Family change (m2): in line 20.220 (of which 1.400 narrowed from the bound 1.28 .. 1.40), new rows 13.597 = 9.667 +
3.930, held 7 rows blank.** The 22 doors' 20.220 stay ONLY in FIN.PLASTER (pinned by test: no second carrier).

## 4. FILL table T-327 (sills and thresholds; FILL_T327_T340.csv, 59 carriers)

| Action | Carriers | m2 | Material (status) |
|---|---|---|---|
| KEEP: 10 FIN.MARBLE.THRESHOLD 1.340, 6 porcelain strips 0.950, A-1F-01 strip 0.150, 6 external-door ARCH.THRESHOLD within bound 1.310 | 23 | 3.750 | marble OWNER_APPROVED; porcelain continued; external HELD (by specification) |
| FILL: 22 ARCH.WINDOW_REVEAL external sills 2.5214 (29.530 m.l, 22 pcs), 4 floor-level strips 0.408, A-GF-01 strip 0.150 | 27 | 3.0794 | sills UNKNOWN (no specification, RFI A13); W15 / W16 terrace finish continued; W25 / W27 UNKNOWN |
| RETYPE_FILL: the 4 BLOCKED closure strips -> FIN.MARBLE.THRESHOLD 0.120 each (D-GF-02, D-GF-10, D-GF-14, D-1F-04) and D-1F-03 -> FIN.FLOOR.PORCELAIN 0.150 | 5 | 0.630 | marble (wet doorway rule) / porcelain (dry) |
| ADD_ROW ARCH.WINDOW_REVEAL W18 external sill | 1 | 0.040 (0.500 m.l, 1 pc) | UNKNOWN |
| HOLD L-c90d5d6c (W17), ADD_HELD_ROW W03, D-GF-15 | 3 | blank | UNKNOWN |

Every fill is the ledger's clear width x wall thickness, **never the closure polygon** (0.153542 / 0.1575 / 0.218846 /
0.185778 / 0.131977 are refused in code). Area, m.l and pcs stay three measures.

## 5. Wet-room cross-check (acceptance b; WET_CROSS_CHECK_T340.csv, FACE_CLOSURE_T340.csv)

- **Every backed and tiled face closes**: 146 faces (73 V3.0.22 backing faces + 73 T-312 tile faces), gross - each
  opening's part in the band = net, max |residual| 0.0001 m2 (4-dp rounding of the face figures). So no reveal, sill or
  threshold surface is inside a backing or tile face. The 12 filled V3.0.22 backing lines equal the sum of their faces
  (340.3038 m2); the 6 held lines are blank.
- 29 openings sit in a wet-room face (15 doors, 1 arch, 13 windows; 141 component rows, a door between two wet rooms listed per
  face): every component is owned by a reveal / sill / threshold carrier, **none by a backing or tile line: double count
  0.000 m2**. Door reveals in wet rooms: FIN.PLASTER (the owner method URBAN-REVEAL-FINISH-METHOD v1: plaster by
  default, porcelain only where shown, never because the room is wet; no drawing shows a tiled reveal), status
  ASSUMED — OWNER-APPROVED for the finish. Wet-room windows: room side NONE (flush frame), so no reveal can enter the tile.
- Held faces (6 rooms, G2 / Q-54 B / D-39; T-088): their openings' components keep their own owner; no figure enters a
  held face.

## 6. Threshold corrections and the layer check (acceptance c; THRESHOLD_LAYERS_T340.csv, CLOSURE_TRACE_T340.csv)

- T-336 corrections carried: D-GF-14 and D-1F-04 thresholds **0.120 m2** each in both layers (finish = waterproofing
  piece, EQUAL), never 0.218846 / 0.131977; the T-336 pantry piece 'D-GF-07-PANTRY' **is census D-GF-06** (INSERT 33E
  D120 into the pantry GF-07): 0.200 m2 in both layers (finish material HELD: external-entrance class).
- Finish strip vs membrane piece, door by door: 14 EQUAL, 1 DIFFERS (D-GF-10, below), 14 finish only (dry or external
  doorways: the membrane rule does not reach them).
- **The five closure-strip residuals T-325 left untraced are now traced** (T-327 acceptance d), by own read on P7757.dxf
  at the jambs (wall-face line ends = clear width, face pair = depth) against each line's own polygon: the polygon runs
  past the jamb over the wall-end nib and, on three doors, across the cross wall to its far face. D-GF-02 +0.2236149 m
  (nib 0.0736 + cross wall 0.150): 0.033542 m2; D-GF-10 +0.2529608 (nib 0.0530 + cross wall 0.200): 0.037944; D-1F-03
  +0.2385198 (nib 0.0885 + cross wall 0.150): 0.035778; D-1F-04 +0.0798447 (nib): 0.011977; D-GF-14 past both jambs
  (east nib + cross wall 0.028377, west face run 0.041799, splayed-wall junction pocket 0.028663): 0.098846 (residual
  0.000006 = polygon vertex rounding). **Residual 0.000000 m2 on four, 0.000006 on one.** Cause: the closure polygon is
  bounded by the cross walls' faces, not by the jambs; the threshold is the jamb read.
- **D-GF-10 finding (correction proposed, not applied):** its drawn jamb gap is **0.7970392 m** (faces 2B1 / 2B2 and
  2AF / 2B0), not the T-237 width 0.800 (matched within 0.06); the polygon trace closes only with 0.797039 and the
  waterproofing piece already uses it (0.119556). Threshold 0.120 -> 0.119556 m2 and the new head soffit 0.120 ->
  0.119556 m2 (-0.000444 each, -0.37 %). The Checker-passed ledger value is carried in both FILL tables with the
  proposal on the row, for the Checker's Gate A.

## 7. Engine vs freelancer, verdict proposals

- The freelancer's workbooks carry no reveal, sill or threshold row (T-313 / T-325 searches of the committed raw rows,
  885 rows): the whole reveal family (in line 20.220 + new 13.597 m2) and the sill / threshold family (7.4994 m2 with
  the fills and new rows) are **RULE_DIFFERENCE (scope)**, freelancer omission, -100 % on his side; his 'door steps'
  7.70 is external steps by length in an area column (T-325: RULE_DIFFERENCE, element).
- ENGINE_RIGHT: the 20 FIN.PLASTER door lines (EQUAL), the 10 marble and 6 porcelain strips (EQUAL), the 6 external
  bounded lines (within bound). ENGINE_WRONG (missing scope): window outside reveals 9.667, five door reveals 3.930, W18
  sill 0.040 m2; ENGINE_WRONG (range width): D-GF-07 1.28 .. 1.40 -> 1.400; ENGINE_WRONG (rule application): the 27
  window strip lines as w x wall thickness (frame bed included), the 5 closure strips as polygons. UNRESOLVED: D-GF-10
  width (section 6), W03 / W17 / W02 jambs / arches / gate.

## 8. Missing, held, downstream

- HELD / UNKNOWN (blank, never 0): W02 outside jambs (D-53), W03 and W17 all components (curved, T-302), A-GF-01 (D-45),
  A-1F-01 (not drawn), gate D-GF-15; sill material UNKNOWN on 23 sills + W25 / W27 (RFI A13); external-door threshold
  material HELD (by specification).
- Downstream for lane I: T-326 consumes FILL_T326_T340.csv (adds 32 rows, narrows 1, keeps 21, adds 7 held rows; BOQ
  family B4-08 'Reveals and returns' then carries 9.667 m2 window outside reveals); T-327 consumes FILL_T327_T340.csv
  (fills 27, retypes 5, adds 1 and 2 held rows). Outer arrises stay with the corners line (T-162); the exterior face
  ledger (T-305 / T-337) deducts openings by hole and holds no reveal surface (not re-read here).

## 9. Tests and lessons

- tests/t340_reveal_sill_binding (36): villa R340 by hand (two windows, a wet and a dry door, a bath face: W1 0.336 +
  sill 0.096, W2 0.416 + strip 0.080, D1 0.780 in its plaster line + marble 0.120 retyped, D2 1.060 new row, face 5.760
  - 1.760 = 4.000), normal (room side NA, shared sill one surface, mirror order, held part beside a measured one, within
  bound / narrow, layer alias) and adverse (second carrier for a door reveal, reveal in a sill line, threshold in a
  reveal line, a threshold under two doors, held sill as 0, measured with no figure, missing scope without a row, the
  ledgers disagreeing, line differing, narrow outside bound, superseded polygon, the shared jamb counted in the wet face,
  reveal owned by a backing line, valued face with a held deduction, negative / unknown component, line not in the
  candidate); development villa pinned (byte rebuild, candidate shas, 92 SAME, 59 openings once, totals, 22 doors only in
  FIN.PLASTER, corrections and superseded values, traces, zero overlap, held never 0, a tampered ledger stops the build).
- Lessons-register row (proposed, ERS s.7): 2026-10-29 | five door thresholds sat as BLOCKED closure polygons 0.012 ..
  0.099 m2 above the jamb figure, and one door's ledger width (0.800) was a matched nominal 3 mm off the drawn jamb gap
  | the strip was bounded by the cross walls' faces and the door width was taken from a tolerance match, not from the
  jambs | a threshold / reveal width is the drawn jamb gap (wall-face line ends); a strip polygon is reconciled to it by
  nib and cross-wall terms with the residual named; one physical strip carries one area in every layer (finish,
  membrane) (every villa) | tests/t340_reveal_sill_binding (superseded polygon refused; layer DIFFERS named) | PROPOSED.
