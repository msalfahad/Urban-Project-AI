# T-735 formwork conflict decider: 7 STR.FORMWORK lines, one live form each (research, unwired)

Worker 1, lane S, 2026-11-12, branch `agents/task-T-735`. Files: `t735_rules.py` (R-T735-1 / R-T735-2 1.0.0, every
villa), `t735_alsenan.py` (builder; committed inputs sha256-pinned in `PINS.json`, T-732's builder reused read-only;
`--check` rebuilds byte for byte), `out/T735_DECIDER.json`, `out/T735_DECIDER.md`, `out/T735_OWN_READ.json`, tests
`tests/t735_formwork_conflict` (20). No engine, candidate, rule / knowledge version, registry or frozen file changed;
R-T732-1 / R-T714-1 / R-T707-1 / R-T730-1 not edited; nothing wired, released or VERIFIED. Own read this run: Drive
'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179 = manifest), decoded by the wrapper into the private folder
only; sizes, handles and edge directions recorded, no coordinate.

## 1. Physical element and the two methods (ERS s.2.1 / 2.2)

Column formwork = the cast faces from the top of what the column stands on up to the slab soffit, less the faces the
framing members cover (R-CONC-OWN-1): SHAFT P x (soffit of the deepest framing member - base) + JOINT strips + EDGE
bands (R-T732-1). A beam side below the slab = contact length beside a slab x (D - t), D the TOTAL schedule depth.

| | Owner manual method | Drawing-derived method (this run) |
|---|---|---|
| column | perimeter x storey height to the beam soffit; unprinted datum held | P_min x (least panel top - base - D_max) .. P_max x (h_hi - D_min) + walk joints / edges (R-T732-1) |
| beam side | 2 x L x (D - t) per beam | walk length beside slab x (D - t); the walk booked 0 because it held D (R-T735-2) |

## 2. The conflict and the decision (R-T735-1)

T-707 (merged first) bounded the 6 column lines by P x (h - t) .. P_max x (h_hi - t); T-714 (merged later, V3.0.70)
stated them BLANK 'no positive floor' and declared no restatement. Neither stands: T-707's low is the UP-FW-001
upper-bound method (it contains the faces under framing beams, F-T732-1), its high is exactly the perimeter envelope
(asserted for all 6) and leaves out the slab-edge band outside the column; T-714 read the shaft as dependent on the
column reading, but the shaft floor P_min x (least top - base - D_max) is positive for every reading.

| Line | Column (own read) | Concrete m3 | Sections | Shaft h lo / D_ctrl | T-707 m2 | T-714 | **T-735 live m2** |
|---|---|---|---|---|---|---|---|
| L-6f83fc39 | 412 C2 2F COL-2F-51, 200 x 500 | 0.3287 .. 0.425 | 20x50 only | 2.537 / 0.75 settled | 4.3498 .. 5.698 | BLANK | **BOUNDED 4.183916 .. 5.532116** |
| L-b35c1688 | 415 C5 2F COL-2F-49, drawn 600 x 200 | 0.3287 .. 0.51 | 20x50 sched / 20x60 drawn | 2.067 / 0.75 .. 1.20 (BM-2F-015, D-04) | 4.3778 .. 6.544 | BLANK | **AT_LEAST 2.893800** |
| L-6cba8c04 | 34A C GF annex, drawn 200 x 400 | 0.26352 .. 0.405 | 20x40 / 20x50 | 2.544 / 0.75 settled | 3.7608 .. 5.446 | BLANK | **AT_LEAST 3.052800** |
| L-ddec0b3f | 34D C GF annex, drawn 400 x 200 | 0.26352 .. 0.405 | 20x40 / 20x50 | 2.544 / 0.75 settled | 3.7608 .. 5.446 | BLANK | **AT_LEAST 3.052800** |
| L-f9836bd6 | 356 C GF annex, drawn 400 x 200 | 0.26352 .. 0.405 | 20x40 / 20x50 | 2.544 / 0.75 settled | 3.7608 .. 5.446 | BLANK | **AT_LEAST 3.052800** |
| L-7fe93376 | 350 C3 GF annex, drawn 400 x 200 | 0.26352 .. 0.50625 | 20x40 / 25x50 | 2.544 / 0.75 settled | 3.7608 .. 5.835 | BLANK | **AT_LEAST 3.052800** |
| L-867e155d | 1F-072 REST beam side, BM-1F-031 CB10 | 0.7438 .. 0.8925 (width) | D 0.50 both candidates | L 0.300056 beside slab, t 0.16 | - | BLANK, cap 0 | **BOUNDED 0.102019** |

Hand checks. 412: base +9.65, panels P1 / P2 (t 0.18, top >= 12.937): shaft 1.40 x (12.937 - 9.65 - 0.75) = 1.40 x 2.537
= 3.5518 .. 1.40 x (4.25 - 0.75) = 4.90; joint R4-309 0.5961 and edge R4-312 0.036016 INDEPENDENT (one section, D
settled; walk made at D 0.75 = 4.20 - 3.45) -> 4.183916 .. 5.532116; envelope 1.40 x (4.25 - 0.18) = 5.698 >= 5.4961.
Annex (R-T678-2 one plane, slab top >= 3.544 from W08 head +2.80 under CB6 20x75, base +0.25, t 0.16): 1.20 x (3.544 -
0.25 - 0.75) = 1.20 x 2.544 = 3.0528; joints / edges recorded at one section of a conflict pair -> DEPENDENT -> AT_LEAST.
The trio's line-to-outline pairing is not asserted (T-689) and changes nothing: identical readings and floors.
L-867e155d: walk records face 1F-072 run REST: BEAM_SIDE 0.0 with BEAM_SIDE_HELD_LEN 0.300056 m (D None in the walk);
own read of the face: every slab-adjacent edge is on the east long side, along the band (1F-041 / 060 / 090 / 094 =
4.019 m vs walk 4.013 m for the three runs), so the face does not scale with the 0.25 / 0.30 width; CB10 25x50 TOTAL
depth (both concrete candidates decompose to D 0.50) under 0.16 panels: 0.300056 x 0.34 = 0.102019 m2. Not
ZERO_BY_GEOMETRY: there is a downstand along a slab. RING_MIX 0.5989 m (west dome ring side), HELD_EDGE 0.00003 m and
junction 0.10 m stay held lengths outside this line (named).

## 3. Family B10-13 (beside, never summed into a released total)

| class | after T-732 | after T-735 |
|---|---|---|
| BOUNDED | 30: 102.914777 .. 127.151372 | **32: 107.200712 .. 132.785507** (+4.285935 .. +5.634135) |
| AT_LEAST | 35: >= 107.379697 | **40: >= 122.484697** (+15.105) |
| BLANK_NAMED | 251 | **244** |
| FIX_ROW | 54 (33.127058) | 54 unchanged |

Released 1,027.977403 m2 untouched. T-729 can carry these 7 lines in the forms above (each with its supersession).

## 4. Reconciliation, held, verdicts

- 412 vs T-707: low 4.3498 -> 4.183916 = -0.165884 = 1.40 x (0.75 - 0.18) = 0.798 (the strip between the B8 soffit
  and the slab soffit, which T-707 counts whole) - 0.5961 (the part of it the walk finds formed; 0.2019 is covered by
  the framing beams B3 / B8, D-N10-04) - 0.036016 (edge band outside the perimeter). The high moves by the same
  -0.165884 (5.698 -> 5.532116). Residual 0.
- 415: D_max 1.20 by the register convention for the unmarked BM-2F-015 (T-110 m3 high 0.271 = 0.20 x 1.20 x 1.13,
  the same convention T-732 applied to 418 / 41E); T-119 names only B8 0.75 / B3 0.40 as candidates. If D-04 settles
  BM-2F-015 at <= 0.75 the floor rises 1.40 x 0.45 = 0.63 m2 (to 3.5238). The section conflict (D-66, drawn 20x60 vs
  schedule 20x50) keeps the joints / edge DEPENDENT: no line high.
- Annex: the floor rests on R-T678-2 (3.544); Q-54 B (annex slab top) and D-66 (section) are what open the high.
- T-638 shaft cap R4-240 4.83 (412) is below the live shaft high 4.90: the caps rest on the 4.20 interval, the member's
  own high is 4.25 (D-39) (same as F-T732-3).
- Verdicts: NOT_COMPARABLE (no freelancer formwork row); ENGINE (T-707 beside) WRONG as a floor, ENGINE (T-714) WRONG
  as BLANK where a floor exists, ENGINE (T-714 L-867e155d) WRONG cap 0 -> 0.102019.

| date | discrepancy | cause | rule | regression | status |
|---|---|---|---|---|---|
| 2026-11-12 | two merged pieces stated 6 column formwork lines differently (P x (h - t) bound vs BLANK) and a walk 0 entered a ledger as a cap of 0 | merge order was taken as a decision; the walk books 0 m2 when it holds a depth | R-T735-1 (one live form, every earlier form superseded by name) / R-T735-2 (held-depth 0 restated when D is settled and the edges run along the member) | tests/t735_formwork_conflict (V735 normal: settled column 4.55 .. 4.85, conflict column >= 3.36, held-depth side 0.5625; adverse: later blank without cause, no earlier form, cap 0, same-form mismatch, depth differs, edge across, t missing, D <= t, mm, non-decomposing candidate) | PROPOSED |

Checker re-measure: outlines 412 (200 x 500) and 350 (400 x 200) by handle on S-COL.BON; face 1F-072 slab edges (east
long side only); T-119 rows COL-2F-51 / COL-GF-29; BM-1F-031 register rows (D 0.50 in both candidates).
