# T-756 exterior render / paint face ledger re-based onto ARCH_TAKEOFF_V3.0.77 (worker 2, lane A, 2026-11-13; research)

Nothing is wired: no candidate line, hub, registry, rule / knowledge version file or default moves (wiring: T-314 r3).
Rules R-T756-1 .. -4 1.0.0 (`t756_rules.py`, every villa); application `t756_alsenan.py` (`--check` rebuilds from the
committed, sha-pinned merged inputs; `--recheck <index>` is step E); outputs `out/T756_*.csv`, `out/T756_SUMMARY.json`;
tests `tests/t756_face_ledger_rebase`. No drawing, workbook, client name or coordinate here; no DXF was opened this run:
every quantity below is a merged, Checker-passed ledger figure (T-305, T-311, T-314 r2 stage via the T-737 / T-747
pins, T-747, T-751, T-754, T-749 V3.0.77 index). ERS read: s.2.1, 2.4, 3, 7.

## 1. Physical element

Each external rendered face (storey band F.F.L. -> next level, parapet outer / inner / top, plinth, slab-edge band),
its gross m2, its holes by opening id (Q-73 A, once, on the face that holds them), and the arrises it owns in lm, each
bound to ONE line id of the candidate of record. Paint is the render of the same face (OWNER RULE PAINT 2026-11-12,
UP-FIN-PAINT-002; OWNER_NOTES_SIGMA 2026-10-21); edges / corners are lm, never m2.

## 2. (A) Re-base by id (R-T756-1): stale 0, collisions 0, nothing dropped

| source | rows in | rows out | V3.0.77 state |
|---|---|---|---|
| T-305 face bands | 98 | 108 (+20 stage-added faces = 128) | LIVE 52 (3 storey lines), NEW_FREE 74 (15 stage lines, ids and element ids free), NOT_A_FACE 2 |
| T-305 own bindings | 98 | 98 | finish line LIVE on the 45 IN_LINE rows, geometry line LIVE (ARCH.FACADE x 4) on 74; NO_LINE rows named |
| T-311 components | 46 | 66 | LIVE 36 (STR.CONC.PARAPET 4, STR.FORMWORK T332 parapet 24, FIN.WP.ROOF_UPTURN 5, MAS.BLOCK plinth course 2, annex-roof band on L-b05f70c9 1), NEW_FREE 15, MISSING 9, PARKED 4, OTHER_TRADE 2 |
| T-305 openings | 39 | 39 | 38 on their face's line + edge line (windows FIN.EXT.PAINT.EDGE, doors FIN.PAINT.EDGE, T-749 F-T749-1); OP-001 0.20 gap NOT_A_FACE |

- Two T-305 bands carry another figure in the stage, both by merged record (asserted; any other difference stops the
  build): 1F/NW-2 parapet 4.5853 -> 3.977236 m2 (T-348 r2: straight on the chord above +9.70, -0.608064) and 1F/NW-2
  slab edge no area -> 0.535 .. 2.00625 (T-348 r2 depth bound). 1F/NW-1 and NW-3 slab edges are NOT_A_FACE (T-348 /
  T-754). The 20 faces without a T-305 row are each cited to their merged record (T-348 r2 screen, arc, returns, ring
  and court front; T-567 pier returns; T-324 C5 NE-6x; T-311 / T-324 parapet inner / top).
- MISSING by id (no V3.0.77 line, never 0): parapet blockwork x 4 (no MAS.* parapet element; 0 .. solid HELD Q-65 C /
  D-39), parapet top arrises x 4 (T-337 FIN.EXT.CORNERS horizontals 710.17 .. 821.86 m.l, not restated), passage
  substrate split. PARKED: parapet rebar x 4 (owner 2026-11-11). OTHER_TRADE: plinth substrate = STR.CONC.GROUND_BEAM
  (61 lines now vs 59 counted by T-311; a substrate face, not re-bound).
- T-311 bound the annex and 2F parapet outer faces inside the GF / 2F storey lines; the stage splits them to their own
  PARAPET-OUTER lines (L-7c48b6a4 / L-d503696a): the old binding is LIVE but superseded, no area counted twice.

## 3. (B) T-754 deltas on the FIN.EXT.PAINT.EDGE lines (R-T756-3; residual 0)

| line | element | V3.0.77 | after | host now -> after r3 |
|---|---|---|---|---|
| L-d8a40db5 | CORNER_EDGE:PARAPET-OUTER_1F_9.70 | 9.185812 | **6.585812** (NW-1/NW-2, NW-2/NW-3 NOT_A_CORNER, -2.60) | L-8bb83e16 -> L-5a04a3ec |
| L-b15852d9 | CORNER_EDGE:PASSAGE_MOUTH_NO_HOST | 1.40 | 1.40 (HOSTED on GF/P-1 + P-2, both on L-b05f70c9: a re-binding, no delta) | L-b05f70c9 (asserted = T-754 host) |
| 36 others | windows 26 + 3 blank, corner groups 7 | unchanged | KEEP; parapet / plinth corner groups re-bind to their stage lines by face key | per row |

Corners 179.535812 .. 180.735812 -> **176.935812 .. 178.135812 lm** = T-754 after_physical exactly; windows 103.682251
(= T-751); FIN.EXT.PAINT.EDGE total 283.218063 .. 284.418063 -> **280.618063 .. 281.818063 lm**. Doors 0 .. 12.20 stay
under FIN.PAINT.EDGE (7 lines by engine opening ref, mapped per door). The element id label NO_HOST is left as is (a
rename is a next version); its host is now a face.

## 4. (C) Per face: render = paint (R-T756-2), 126 faces, residual 0.000000

Render = paint = **1,009.110254 .. 1,087.619176 m2** (T-747 faces + the 3 T-751 face changes, asserted equal to T-751 /
T-754). No face carries a printed other finish (T-747 drawing check: 0 finish words, no hatch), so no paint deduction;
the SE surround is OFF_FACE (T-751). Six 1F slab-edge faces stay HELD blank, cause per face from T-754: NE-1, SW-1,
SW-2 raster only (never scaled); NW-4, NW-5 hidden behind the GF roof strip / court front in the NW frame; **SE-1:
2.30 m over the porch mouth is ONE_PLANE (0 arris); its band 2.30 x 0.80 = 1.840 m2 is held by no stage face and must
be bound against GF/SE-2 and T-360 C-1 before valuing; the other 1.80 m lies behind the annex: blank**. Their line
L-22e75c39 is blank, with the valued NW-2 part 0.535 .. 2.00625 shown beside it.

## 5. (D) Ready-to-wire table for T-314 r3 (`out/T756_WIRE_TABLE.csv`, 56 rows)

| line | action | render m2 after (= paint) | status |
|---|---|---|---|
| L-b05f70c9 GF storey | CHANGE (blank -> ) | 376.694149 .. 410.179149 | HELD (W02, D-GF-07 holes) |
| L-8bb83e16 1F storey | CHANGE | 248.178057 .. 249.954348 | HELD |
| L-d52c4f76 2F storey | CHANGE | 117.305 | ASSUMED — OWNER-APPROVED (Q-55 C) |
| parapet outer annex / GF / 1F / 2F | ADD x 4 | 14.671022 .. 15.271022 / 14.385 / **54.651307** .. 60.029307 / 14.900 | HELD / DC / HELD / DC |
| parapet inner x 4, top x 4 | ADD x 8 | 67.411 .. 99.557 / 26.836 .. 26.972 | HELD (D-39 split, T-324 D bands); 2F top DC |
| plinth GF | ADD | 71.688590 .. 72.749795 | HELD (pool-court bottom, finish T-317) |
| slab edge GF / 1F | ADD x 2 | 1.854260 .. 4.309240 / blank | HELD |
| FIN.EXT.PAINT.EDGE x 38 | KEEP 37, CHANGE 1 | see section 3 (lm) | HELD |

Valued render lines 1,008.575254 .. 1,085.612926 m2 + blank 1F slab edge (valued part 0.535 .. 2.00625). The paint
column equals the render column line by line; its item code (an m2 exterior paint line per render key, T-747 proposal)
and the stage item codes FIN.EXT.PARAPET-INNER / -TOP are the Lead's naming decision at r3 (no quantity rides on them).

## 6. (E) Re-check

Every mapped live id (81) has the same item, element, unit, class and figures in V3.0.73, .74, .75, .76 and .77 (the
45 edge / door-edge ids exist only from V3.0.77, as T-749 added them); the 15 NEW ids and element ids are free in all
five. T-738 had not merged at this run: after it merges, run `t756_alsenan.py --recheck <LINE_INDEX_V3_0_78.json>`
(exit 0 = no mapped id changed); PENDING.

## 7. Engine vs freelancer, verdicts, open items

- Exterior paint / Sigma: his 1,469.9675 m2 vs 1,009.110 .. 1,087.619 (-31.35 % .. -26.01 %): RULE_DIFFERENCE stays
  (domes excluded, half holes, boundary wall Q-65, drip; T-567 / T-747 causes, unchanged); no face explains more.
- Corners: his 1,297.35 m.l vs 176.94 .. 178.14 vertical + 103.68 windows + 0 .. 12.20 doors (+ T-337 horizontals):
  RULE_DIFFERENCE (unchanged).
- Open, named, not decided here: F-T754-1 (1F storey corners NW-1/NW-2, NW-2/NW-3, 8.40 lm inside L-1f1149d7 37.80:
  screen-opening edges or arrises behind the screen, Checker re-walk); F-T751-2 (NE-2 parapet top +10.80 .. +11.30,
  the NE-2 outer face 25.051 m2 inside L-5a04a3ec); SE-1 slab-edge 1.840 m2 ownership (section 4).
- Checker re-measure suggestions (2 faces by handle, per T-747 / T-751): GF/SE-2/COVERED/storey 3.70 x 4.50 = 16.65
  gross, D-GF-07 hole 0 .. 5.00 (door 1C00 +1.00 .. +3.50), paint = render 11.65 .. 16.65; 2F/SE-1 storey 8.10 x 4.20
  - W26 1.875 = 26.685 (layer-1 lines 1291 / 1274..1277 per T-737).

## 8. Lessons register row (proposed, ERS s.7)

2026-11-13 | T-756 | face ledger keyed to an early candidate | a ledger bound to line ids of V3.0.18 was about to be
wired into V3.0.77 after eleven versions moved masonry, plaster and edges | re-base every source row by id against the
target index (LIVE / STALE / NEW_FREE / COLLISION / reason / MISSING, count in = count out), apply each merged edge
verdict as a per-line delta that must close the verdict exactly, and re-check the mapped ids against every later index
before wiring | tests/t756_face_ledger_rebase.
