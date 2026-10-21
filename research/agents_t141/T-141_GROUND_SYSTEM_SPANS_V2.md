# T-141 Ground-beam span splitter V2 and strap axis lengths (lane S, gate 3; repo code, opt-in, not wired)

Worker 1, 2026-10-21. New module `engine/source/ground_system_spans_v2.py` (stdlib only; the frozen S5 chain is not
edited or imported). Hand fixture (not Alsenan) `tests/t141_ground_system_spans_v2/`. Alsenan check
`research/agents_t141/run_t141_alsenan.py <structural DXF>` writes `T141_SPANS.csv` / `T141_STRAPS.csv` (ids and
lengths only). No released quantity changes; wiring is for lane I (V3.0.x).

## What the module does (owner manual method = the T-138 hand reading, now drawing-derived)

| | Owner / Urban manual method (T-138 hand ledger) | Frozen S5 register | V2 (this task) |
|---|---|---|---|
| Support on a band | every column drawn on the band | columns from a rectangle census that missed three founded columns (228, 1E0, 211) | every column outline that overlaps the band strip, full or partial width (partial flagged) |
| Span length | face to face along the band | centreline-based face finding; "centreline - 0.30" where column and band edges are collinear | support outline clipped to the band strip: exact face to face |
| Band end at another band | that band's face | that band's face | same; where the band's own faces run past the other band's face (L corner) the junction zone is cut off; a tee or crossing mid-span never splits the carrier |
| Free band end over a footing | the footing face | footing face | the footing face on the span side (FOOTING_FACE) |
| Band end drawn short of / beside a column | the column face (a reading) | centreline | GAP_TO_COLUMN: HELD with every candidate (band end, column face, footing face) |
| Section (p.13 title) | from the face-to-face span | from its own span | from the span after splitting; centreline class stored beside; exactly on a limit -> both titles, HELD |
| Strap length | between the footing faces along the strap axis | gap between the footings' projections on the axis | all bases stored apart, HELD: no Urban rule or owner answer sets the strap length basis (URBAN-BEAM-TYPE-FROM-SCHEDULE-LENGTH-FROM-PLAN@v1 never applies to STRAP) |

Rules: URBAN-BEAM-TYPE-FROM-SCHEDULE-LENGTH-FROM-PLAN@v1 (four bases stored apart: centreline, clear concrete, face to
face, bar straight run lower bound), URBAN-REBAR-NET-AND-PROCUREMENT@v1 (no kg here: lengths only), UP-QTY-STATUS-001
(released / held / unsupported; missing never 0).

## Alsenan result (structural DXF sha 9f9d1179; ground-beams plan, 41 straight bands + 3 curved band pieces)

- **Spans**: 59 straight spans: 56 released lengths, 3 held (1811 / 1812 free east end on the plot boundary;
  177 / 7CD span 1 GAP_TO_COLUMN; 184 / 7CF span 3 exactly 5.00 m). The 3 curved pieces are listed UNSUPPORTED (V2
  measures straight bands only; the hand ledger also carried them from S5).
- **Against the T-138 r2 hand ledger: 52 of the 53 hand-measured spans agree within 0.3 mm** (all within 5 mm). The one
  difference is 177 / 7CD span 1: hand 4.97 m (column 1EC face) vs V2 HELD. The band is drawn to x 100,718, column 1EC
  (x 100,518 .. 100,768) sits 50 mm beside the band face, so the support face is a reading: band end 5.02 m (> 5 m,
  section GT5M), column face 4.97 m (< 5 m, LT5M), footing FF face 3.52 m. The section changes with the reading, so V2
  holds it with the three values (verdict proposal UNRESOLVED; designer question S5 Q-G1 / D-34).
- **The three S5 defects are gone**: (1) bands 109 / 7CB 9.50 -> 4.40 + 4.40 m (GT5M -> LT5M), 170 / 7C3 6.22 ->
  2.40 + 3.37 m, 13E / 7D6 5.10 -> 4.30 + 0.50 m (GT5M -> LT5M + LT2_5M; column 211 covers 0.67 of the band width,
  flagged PARTIAL_WIDTH_SUPPORT) - all three columns are founded (over footings F6, F2, F3 on the foundation plan,
  frame offset 38,724.4 mm checked against the plot boundary); (2) 26 spans S5 measured differ from V2 by more than
  5 mm, e.g. 7D0 / FC 3.375 / 6.245 / 6.650 / 1.400 -> 2.975 / 5.745 / 6.350 / 1.200 m; (3) straps on the axis: SB2
  1.829 -> 2.293 m, SB3 2.838 -> 3.258 m, SB1 4.550 m both ways (all HELD on the length basis, see below).
- **Section (p.13 title) changes against S5**: 109 / 7CB and 13E / 7D6 (above); 177 / 7CD span 1 GT5M -> HELD;
  184 / 7CF span 3 5.15 GT5M -> 5.00 ON_LIMIT (HELD); 114 / 115 / 7DF span 1 (2.625 -> 2.325 m) and 17E / 17F
  (2.687 -> 2.427 m) cross 2.5 m, so both "less than" titles become candidates (the LT2_5M section prints no link: D-34).
- **Not hand-measured before, now measured by V2 (for the checker)**: 145 / 7CA 1.900 m one span (S5 0.40 + 2.30; the
  hand note read 1.900 through junction 178 / 7DB, which is a tee, not a support); 177 / 7CD span 2 1.537 m (S5 1.989,
  ends at the curved band 157 / 158); oblique bands 17E / 17F 2.427 (column 1EF covers 0.27 of the band width, flagged),
  180 / 181 0.789 (S5 1.089), 182 / 183 2.073 (S5 2.223).
- **Finding on the T-138 notes**: the footing under the free ends of 15D / 7C8 and 17C / 7E3 is FF (outline 1B2B), not
  F12 as the hand notes say; the lengths (1.900 / 1.928 m) are unchanged.

## Steel effect (engine vs hand vs freelancer, kg, net longitudinal, ground beams)

| | kg |
|---|---|
| Frozen S5 released (31 spans) | 1,238.56 |
| T-138 hand, same scope (31 spans) | 1,194.60 = 1,169.98 on the 30 straight spans + 24.62 on the curved span |
| Same bars on V2 lengths, the 30 straight spans | **1,169.97** (-0.01 vs hand); curved span 24.62 kg not measured by V2 (UNSUPPORTED) |
| Bars through interior columns (hand, T-138) | 58.31 (V2 lists every interior support with its length along the band; no kg) |
| Freelancer | lumps of a different scope (9.75 t "ground beams + ground floor", 5.8 t footings incl. straps): no % (RULE_DIFFERENCE) |

So V2 moves the engine's released ground-beam steel from S5's 1,238.56 kg to the hand figure: -43.96 kg (-3.5 %) on
the released scope, and supplies the split spans (109 / 7CB, 170 / 7C3, 13E / 7D6) whose bars the hand ledger already
released or held. Strap steel stays as T-138 / T-136 have it until the strap length basis is set.

## Held items and the gap for the Lead

- **Strap length basis (gap, no owner question filed)**: no Urban rule or answer sets it. Candidates stored per strap:
  axis face to face (SB1 4.550, SB2 2.293, SB3 3.258 m), each edge face to face (same values here), S5 projection gap
  (4.550 / 1.828 / 2.838), footing centre to centre (7.050 / 4.388 / 4.559), S5 column centre to centre (7.600 / 4.977 /
  4.886). The T-138 hand ledger used the axis face to face; the Lead decides whether this needs an owner question.
- 177 / 7CD span 1 (GAP_TO_COLUMN), 184 / 7CF span 3 (ON_LIMIT 5.00), 1811 / 1812 (FREE_END), curved bands
  (UNSUPPORTED). Interior footings without a column under a span: none on Alsenan (flag FOOTING_WITHOUT_COLUMN_UNDER_SPAN).
- Through-column bar continuity, development / laps / hooks and links stay as in T-138 (Q-71, D-33 .. D-38).

## Validation

`pytest tests/t141_ground_system_spans_v2` 15 passed (hand fixture: column on a band without footing, collinear column
edges, partial-width column, L corner, tee, free end over a footing, column beside the end, exactly 5.00 m, 30 deg strap;
mirror x 5 rotations, mm and m, missing data never 0, input errors). Firewall test + tests/ground_system_rebar_s5,
s5_1, pre_s5_ground_system: pass (the new module is declared in the firewall registry, geometry only). L2 concrete /
rebar folders: the same 6 failures as the clean working head (private inputs absent), no new one. Freeze check 0.
