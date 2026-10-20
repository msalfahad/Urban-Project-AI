# T-135 Stair flight drawn on two plans counted once (STAIR_FLIGHT_ONCE_V1, not wired)

Source: Drive "Alsenan chalet project": the architectural DXF (P7757_DXF_COMPRESSED.zip, sha ab54dd55...), one
ARCH_TAKEOFF_V2.9 run of the working branch (the same run T-113 / T-116 / T-122 / T-129 used), and the structural DXF
(ST7757 dxf.dxf, sha 9f9d1179...) for the slab above each storey. Script:
`alsenan_stair_flight_once.py --v29 <pickle> --st <structural DXF> --out <dir>`; outputs FLIGHTS_ONCE.csv and
flights_once_summary.json (areas, lengths, levels, counts only).

## The defect (from T-129)

`arch_rooms.cross_plan_flights` reads a flight that lies over a flight of the plan below as STACKED ("a stair core",
counted again) whenever no void mark is near it. The 2F plan draws the two flights of the 1F -> 2F dog-leg for
orientation, so V2.9 measures them on 1F and again on 2F.

## The rule of the new piece (engine/source/stair_flight_once_v1.py)

A flight belongs to the storey whose floor it leaves (owner Q-62 A cond: each element once). For a flight lying over
a flight of the plan below: (a) a printed level at one of its ends below / above the plan's floor decides; (b) else the
slab above the plan: the slab plan draws no stair and no opening -> nothing rises from this floor; a stair panel at
the flight -> it rises; a stair drawn but not located -> it rises only where the flight differs from the one under it;
(c) else HELD. A flight of the storey below is SEEN_ABOVE (0 here, the line names the lower flight) only on an exact
match: same tread count, corners within 0.01 m after the column-grid alignment, lower copy itself counted, not already
matched; otherwise HELD 0 .. its own value with every reason. Never counted twice, never dropped, never 0 by default.

## Alsenan, owner manual method and drawing-derived method side by side

| Plan | Flight (V2.9) | Treads | Tread marble m2 | Steps lm | V2.9 (released) | Once-only (drawing evidence) |
|---|---|---|---|---|---|---|
| 1F | west lane F2 (1F -> half landing) | 11 | 3.795 | 12.65 | counted | COUNTED 1F: the 1F roof slab draws the stair panel ('(With Stair)', T 16, stair-panel lines, the well opening); 11 treads over the GF flight's 7: another flight |
| 1F | east lane F3 (half landing -> 2F) | 10 | 3.450 | 11.50 | counted | COUNTED 1F (same evidence; 10 over 3) |
| 2F | east lane F2 | 10 | 3.450 | 11.50 | counted again | SEEN_ABOVE = 1F F3: 10 = 10 treads, outline shift 0.0000 m; the 2F roof slab plan draws no stair panel and no slab opening at all (T 18 slab at the stair) |
| 2F | west lane F1 | 10 | 3.450 | 11.50 | counted again | HELD 0 .. 3.450 m2 / 0 .. 11.50 lm, storey 1F: 10 treads here vs 11 on 1F F2, north end 0.300 m short (the 2F plan draws one tread fewer of the same flight) |

Totals of the engine's tread / step lines (all plans, exposure lines unchanged at 8.924 m2 / 29.896 lm):

| | Tread marble m2 | Steps lm |
|---|---|---|
| Released V2.9 (counted lines) | 27.324 | 91.028 |
| Once-only counted | 20.424 | 68.028 |
| Removed as a repeat (SEEN_ABOVE) | 3.450 | 11.500 |
| HELD (repeat by the slab evidence, drawn with one tread fewer) | 0 .. 3.450 | 0 .. 11.500 |
| Once-only range | 20.424 .. 23.874 (-25.3 % .. -12.6 %) | 68.028 .. 79.528 (-25.3 % .. -12.6 %) |

Conservation: 27.324 = 20.424 + 3.450 + 3.450 (0.000 left), 91.028 = 68.028 + 11.500 + 11.500. This is T-129's range
exactly: +3.45 m2 / +11.5 lm certain, up to +6.90 / +23.0. Hand check: 10 x 0.30 x 1.15 = 3.450 m2, 10 x 1.15 =
11.50 lm per 2F lane.

Owner manual method (finish table, T-129): stair marble once-only 48.515 .. 49.235 m2 (flights + landings, owner Q-46 A
counts and Q-66 B / Q-70 A landings). The engine's tread lines are a different basis (drawn tread polygons, landings
apart), so the two are not added; the piece removes from the engine only the 2F copies the finish table never had.

Section check (owner Q-46 A, listed only, no quantity changed): 1F -> 2F section A-A 13 + 12 = 25 risers vs 12 + 11 =
23 riser lines on the 1F plan's own flights (difference 2); GF -> 1F 27 vs 12 riser lines the engine reads on the GF
main-stair flights (difference 15: the winders and the upper flight are not read as flights on GF; T-111).

## Verdict proposals for the verifier

- 2F east lane (3.450 m2 / 11.50 lm): ENGINE_V2.9 counts it twice; once-only ENGINE_RIGHT (hand: the 2F roof slab
  sheet has 0 stair-panel lines, 0 openings, 0 '(With Stair)' tags; same 10 treads, same outline).
- 2F west lane (3.450 m2 / 11.50 lm): UNRESOLVED by rule (HELD): by the same slab evidence it is not a 2F flight,
  but the 2F plan draws it with 10 treads where 1F draws 11, so it is not an exact copy; the low end 20.424 m2 is the
  physically consistent reading (counted once on 1F).
- vs freelancer: no flight-level comparison possible (his stair marble 295.44 m2 includes the court twice, T-091).

## Held / missing

- The west-lane copy (above). - The slab-above evidence is read per slab plan (DRAWN / NONE_DRAWN), not located on the
architectural plan; locating it (DRAWN_AT polygons) needs the structural-to-architectural alignment (route G).
- Not wired: lane I wires it into ARCH_TAKEOFF_V3.0.x; no released quantity changes.
