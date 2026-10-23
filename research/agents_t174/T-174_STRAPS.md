# T-174 Strap beams at their axis length (Q-74 answered; lane S, gate 2; Alsenan + every villa)

Worker 1, 2026-10-23. New unwired module `engine/source/strap_beam_takeoff_v1.py` (stdlib only, `DEFAULT_GUARD_CLASS =
"UNWIRED_PRODUCER"`; GROUND_SYSTEM_SPANS_V2 / T-141 is not edited, its `measure_straps` still holds every strap). Hand
fixture (not Alsenan) `tests/t174_strap_takeoff/test_strap_takeoff.py`; Alsenan check `run_t174_alsenan.py` ->
`T174_STRAPS.json` (ids, lengths, quantities; no coordinates); ledger test `test_t174_alsenan_ledger.py`. Candidate only:
no released or candidate method imports the module, the released default V2.9 + route G is unchanged.

Governing: owner Q-74 (2026-10-22, CONFIRMED final: "Use the actual angled beam-axis length between the appropriate
footing faces. Verify 2.29 m and 3.26 m against the drawings. Reinforcement, formwork and excavation retain their own
measurement geometries."), ERS s.2 / s.3 (one element, several geometries; notation before arithmetic), UP-QTY-STATUS-001,
Q-31 C (F10 + F outline HELD), Q-21 C (formation HELD), OQ-10 (formed / earth-cast below ground: alternatives), D-36 /
D-37 / D-38 (designer items).

## 1. The physical element

A strap beam is a reinforced-concrete beam cast between two isolated footings along its own axis, on the foundation
plan (ST7757 dxf, S-FOOTINGS layer; ST7757.pdf p.7). Three on Alsenan:

| Strap | Drawn edges (handles) | From footing (outline, schedule p.9, H) | To footing | Printed section p.10 | Bars p.10 |
|---|---|---|---|---|---|
| SB1 | 1689 / 1B1C, orthogonal (90.000 deg) | F8 (1B24, 4.00 x 3.60, 0.50) | F10 + F (1B1B OPEN, Q-31 HELD) | 70 x 50 | 7 T16 bottom, 13 T18 top, 8 T8/m |
| SB2 | 1B08 / 1B09, 101.08 deg | F11 (1B07 OPEN, 3.50 x 1.50, 0.50) | **F6** (1B19 OPEN, 2.20 x 2.60, 0.50; text "C6/F6") | 100 x 50 (D-38: off-sheet 80 x 50 row) | 10 T16 / 20 T18, 10 T8/m |
| SB3 | 1B26 / 1B27, 110.57 deg | F15 (1B2A, 1.80 x 1.00, 0.40) | F3 ("F" insert 166B, 1.60 x 1.40, **0.30**; text "C3/F3") | 50 x 40 | 5 T16 / 5 T18, 7 T8/m |

Finding: SB2's far footing is **F6** (outline 2.20 x 2.60 = schedule F6 260 x 220, label C6/F6), not F3 as the T-073
ledger wrote; no quantity moves (F6 H 0.50 = the strap depth). No strap section or elevation is printed on any sheet
(p.13 / p.14 show ground beams and footings only): the strap's level against the footings is not printed.

## 2. Reconstruction from the drawing (hand, then the module)

The open footing outlines are closed by their chord, which is exactly where the strap edges cross the face: F11's open
ends (134,829.2 / 135,835.3 at y 37,847.96) and F6's (134,388.5 / 135,395.2 at y 40,097.96) are the strap edge
crossings to 0.1 mm; the chord is collinear with the face, so the module merges it into one face.

| | SB2 | SB3 |
|---|---|---|
| faces crossed | F11 top y 37,847.96, F6 bottom y 40,097.96 (both horizontal) | F15 top y 37,347.96, F3 bottom y 40,397.96 |
| face-to-face rise | 2,250.0 mm | 3,050.0 mm |
| axis direction (cos to the y axis) | 0.98135 (edges 1B08 / 1B09 parallel to 0.01 deg) | 0.93625 / 0.93608 (edges 0.03 deg off parallel) |
| **axis face to face** | 2,250.0 / 0.98135 = **2,292.8 mm** (module 2.2927) | 3,050.0 / 0.9362 = **3,257.7 .. 3,258.3 mm** (module 3.2580) |
| both edges | 2.2927 / 2.2927 (faces parallel to each other) | 3.2580 / 3.2580 |
| owner's figure to verify | 2.29 m: **verified** (+0.3 mm) | 3.26 m: **verified** (-2.0 mm on 3.26, i.e. rounding) |

SB1 (control, orthogonal): F8 bottom y 42,297.96 - F10 + F top y 37,747.96 = **4,550.0 mm**; axis = projection.

**Second drawing (ST7757.pdf p.2 "FOUNDATION PLAN", 1:100, page rotated 270; vector paths read with pymupdf, scale
28.3465 pt/m checked on the strap edges: SB2 edges 144.76 / 150.27 pt = 5.1053 / 5.2999 m, SB3 133.06 / 135.65 pt =
4.6964 / 4.7850 m, all four 28.35 pt/m):** SB2 faces at x 272.92 (F11) / 336.64 (F6) pt: 63.72 pt = 2.2479 m rise, edge
cos 0.98149 / 0.98143 -> axis **2.2903 m** (DXF 2.2927: -2.4 mm, -0.10 %); SB3 faces at x 258.76 (F15, a 51.00 pt =
1.80 m line) / 345.16 (F3, 45.36 pt = 1.60 m) pt: 86.40 pt = 3.0480 m, cos 0.93612 / 0.93594 -> axis **3.2563 m** (DXF
3.2580: -1.7 mm, -0.05 %). The residual is the PDF coordinate quantisation (0.04 pt = 1.4 mm per point, two faces);
same geometry, same faces, same footings (labels C11/F11, C6/F6, C3/F3, F15 on the sheet). The DXF governs the value.

**Cause of the released / S5 short lengths (1.829 / 2.838 m)**: the frozen S5 register measures the gap between the two
footings' PROJECTIONS on the strap axis. On an oblique strap a footing corner beside the strap projects further along the
axis than the face the strap actually crosses:

| | axis | - over-reach start | - over-reach end | = projection gap (S5) |
|---|---|---|---|---|
| SB2 | 2.2927 | 0.2911 (F11 west corner x 133,817: 1,515 mm x 0.19224) | 0.1730 (F6 east corner x 135,792: 900 mm x 0.19224) | 1.8287 |
| SB3 | 3.2580 | 0.2176 (F15 west corner x 124,742) | 0.2026 (F3 east corner x 124,792) | 2.8377 |

The projection is not a length that is built (no concrete, bar or form follows it); it is kept only to name the cause.

## 3. Concrete: owner manual method and drawing-derived method side by side

| | Owner / Urban manual method | Drawing-derived (this module) |
|---|---|---|
| basis | Q-74: section x actual axis length between the footing faces | plan area of the PRINTED-width strip, centred on the drawn axis, outside both footing outlines, x printed D (equals B x axis when each edge crosses one straight face: true for all three) |
| overlap with the footing | "concrete inside a footing counted once" | inside the outline it is footing concrete up to the footing thickness; where D > H the excess depth is strap concrete in no footing: HELD range |
| width | printed | printed (drawn 0.987 / 0.502 flagged, never used) |

| Strap (m3) | Released V2.9 + route G | V3.0 candidate (T-073, PLOT_EDGE_MEMBERS_V1) | **This module** | Status |
|---|---|---|---|---|
| SB1 | 1.995 (5.70 m, runs 1.15 m into the open F10 + F outline) | 1.593 + HELD 0 .. 0.403 | **1.5925** (0.70 x 4.55 x 0.50) | DRAWING-CONFIRMED |
| SB1 inside F10 + F | - | (in the held range above) | A_in 0.770 m2 (column C10 0.035 removed): **HELD** (which footing, H 0.50 or 0.30, Q-31 C) | HELD, <= 0.385 |
| SB2 | 1.132 PROVISIONAL (2.294 x drawn 0.987 x 0.50) | 1.146 | **1.1464** (1.00 x 2.2927 x 0.50) | DRAWING-CONFIRMED on the issued p.10 row; D-38 open (0.9171 under the off-sheet 80 x 50 row) |
| SB3 | 0.654 | 0.652 | **0.6516** (0.50 x 3.2580 x 0.40) | DRAWING-CONFIRMED |
| **SB3 inside F3 (new)** | none | none | strap 0.40 deep on a 0.30 footing: A_in 0.2953 m2 (0.3416 gross - 0.0463 column C3) x [0.10 .. 0.40] = **0.0295 .. 0.1181** | HELD (strap level vs footing not printed) |
| inside F8 / F11 / F6 / F15 | - | - | D <= H: footing concrete, counted once in the footing line (0 here, owner FOOTING) | DRAWING-CONFIRMED |
| **Straps, measured** | **3.781** | **3.390** | **3.3905** + HELD (SB3 / F3 0.0295 .. 0.1181; SB1 / F10 + F <= 0.385) | |

Against the freelancer (strap total 3.3925 m3 as T-073 read his workbook; SB2 priced 100 x 50 x 2.3 = 1.150): measured
3.3905 vs 3.3925 = **-0.0020 m3 (-0.06 %)**; per strap SB2 1.1464 vs 1.150 = -0.0036 (-0.3 %, his 2.3 m is the axis
length rounded). Reconciliation in units: released 3.781 -> 3.3905 = SB1 -0.4025 (1.15 m into the open outline,
T-073), SB2 +0.0144 (printed width 1.00 vs drawn 0.987), SB3 -0.0024 (0.50 vs drawn 0.502 and the axis); residual 0.
The axis basis itself moves no candidate figure (T-073 already measured 2.294 / 3.251 .. 3.258 m along the axis); it
moves the S5 / route G steel and formwork bases, below. New scope: the SB3 excess depth inside F3 (never in any state).

## 4. Bars: their own geometry

Straight run lower bound = the bar's run between the two footing faces along the strap (= the axis length; both edge
runs equal on Alsenan). Anchorage beyond each face: 40 d .. 70 d per end (p.8 note 9, written for starter bars; zone
and end shape not printed, D-36) HELD. Unit mass = the project method D2_OVER_162 (rebar_unit_mass, R3 authority).

| Strap | Run (m) | Bottom kg (LB) | Top kg (LB) | Total LB | S5 released (projection) | Anchorage HELD (kg) | Links (n, HELD) |
|---|---|---|---|---|---|---|---|
| SB1 | 4.5500 | 7 x 1.5802 x 4.55 = 50.331 | 13 x 2.000 x 4.55 = 118.300 | **168.631** | 168.63 | 51.60 .. 90.30 | 36.4 .. 38 (8/m) |
| SB2 | 2.2927 | 36.230 | 91.708 | **127.938 HELD (D-38)** (91.71 under the off-sheet row) | BLOCKED | 77.83 .. 136.20 | 22.9 .. 24 (10/m) |
| SB3 | 3.2580 | 25.742 | 32.580 | **58.322** | 50.80 (2.838 m) | 24.51 .. 42.90 | 22.8 .. 24 (7/m) |

SB3 moves +7.52 kg (+14.8 %) against the frozen S5 register's projected run; it equals the T-138 r2 hand ledger (58.32),
so the hand basis is now drawing-derived. The link count reading of "n / m" for straps is not established (Q-71 is for
footings; ERS s.3): both readings shown, link developed length not computed (D-37: hooks, the 4 / 6 legs of STR2 / str3).

## 5. Formwork: the two side faces

Each side face is its own run between the footing faces x D; ends cast against the footings, top open, soffit HELD
(blinding or formed: no strap section printed). Below ground the line follows OQ-10 (FORMED / EARTH_CAST alternatives).

| Strap | Sides (m2) FORMED | EARTH_CAST | T-163 ledger (length basis open) |
|---|---|---|---|
| SB1 | 2 x 4.55 x 0.50 = 4.550 | 0 | |
| SB2 | 2 x 2.2927 x 0.50 = 2.2927 | 0 | |
| SB3 | 2 x 3.2580 x 0.40 = 2.6064 | 0 | |
| **total** | **9.449** | **0** | 8.648 .. 9.449 -> the axis end **9.449** (Q-74) |

Footing side faces covered by the straps (for the footing formwork owner, T-163 "strap-end contacts -2.050 .. 0"; not
applied here): chord on the face x min(D, H): F8 0.70 x 0.50 = 0.350; F11 and F6 1.019 (= 1.00 / cos 11.08 deg) x 0.50 =
0.5095 each; F15 0.534 x 0.40 = 0.2136; F3 0.534 x 0.30 = 0.1602; F10 + F 0.70 x HELD. Known 1.743 m2 + F10 + F <= 0.350.

## 6. Excavation: its own geometry, HELD

The trench between the footing pits is at most the run between the outlines along the axis (4.55 / 2.2927 / 3.258 m),
shorter by the pits' working space (not printed); width B + working space (not printed); depth below the formation
(HELD, Q-21 C; strap underside against the footing underside not printed). Volume HELD for all three, never 0 (T-170
owns the excavation ledger; this gives it the strap plan geometry).

## 7. Verdict proposals (for the checker)

- SB2 2.293 m / SB3 3.258 m (owner Q-74 "verify 2.29 / 3.26"): **VERIFIED by this run from the DXF** (re-measure:
  faces y 37,847.96 / 40,097.96 and 37,347.96 / 40,397.96; edges 1B08 / 1B09 / 1B26 / 1B27); the 1.829 / 2.838 m
  projections are **ENGINE (S5) WRONG** as built lengths (cause: corner over-reach, table in section 2).
- Strap concrete 3.3905 vs freelancer 3.3925 m3 (-0.06 %): ENGINE_RIGHT on the drawing (SB2 axis 2.2927 vs his 2.3 is
  his rounding); SB3 excess inside F3 UNRESOLVED (strap level, designer).
- Strap formwork 9.449 m2 FORMED (axis basis) vs T-163's lower 8.648 (projection basis): ENGINE (projection) WRONG.

## 8. Lessons-register row (proposed, ERS s.7)

| 2026-10-23 | Oblique straps SB2 / SB3 measured 1.829 / 2.838 m (S5) vs 2.293 / 3.258 m along the axis; SB3 (0.40 deep) enters a 0.30 F3 and the 0.10 excess was in no line | The gap between the footings' projections on the axis was used as a length: a footing corner beside an oblique strap projects past the face the strap crosses (over-reach 0.29 / 0.17 / 0.22 / 0.20 m); 'counted once in the footing' was applied in plan only, without comparing the strap depth with the footing thickness | A member framing into another is measured along its own axis to the face it crosses (never a projection of the supporting outline); an overlap is owned by the receiving element only up to that element's own depth: compare D with H, the excess is the framing member's (HELD while its level is unprinted) (every villa; straps, ground beams into footings, beams into shallower beams) | tests/t174_strap_takeoff (rotated / mirrored / mm; adverse: projection offered as the length, drawn width as the section, D > H with a column, strip past a footing corner, missing section / footing -> HELD) | proposed (T-174 READY) |

## 9. What remains (not done here)

- Wiring into the V3.0 candidate (lane I): the strap lines take these records; the SB3 / F3 excess becomes its own HELD
  line; the S5 / route G strap steel and the T-163 strap formwork move to the axis basis.
- Designer: D-38 (SB2 row), D-36 (bar ends; SB3 is drawn 0.68 m into F3 and 0.80 m into F15 after the face, less than
  40 d of T18 = 0.72 m on the F3 side), D-37 (link hooks / legs), strap level against the footings (new: affects only the
  SB3 / F3 excess 0.0295 .. 0.1181 m3). Owner: Q-31 C (F10 + F), Q-21 C (formation), OQ-10 (formed / earth-cast).
