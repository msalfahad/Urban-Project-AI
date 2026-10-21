# T-084: hand table of the Alsenan stairs from section A-A and the plans (NO REPO CODE)

Worker 3, 2026-10-19 21:00-22:10 UTC. Hand reading only. **EXECUTION NOT VERIFIED**: the session refused the clone of
the working branch ("[Untrusted Code Integration]"; the chained self-check before it: "[Code from External]"), so no
engine code, codemap, pytest or freeze check ran. The only script is `calc.py` (stdlib arithmetic of the readings below,
it reads no file). Development villa, not an accuracy claim. Rules: owner Q-19 (one step = 1/2 x riser x tread x width,
x number of steps), Q-20 = C after reading every stair detail, Q-14 (16 cm is not applied to stairs or landings by
default), UP-STAIR-002 (geometry from sections, levels, details and CAD), UP-STAIR-009 (riser = rise / counted risers;
0.155-0.165 m is a sanity range only), UP-QTY-STATUS-001, UP-KB-PREC-001. Row table: `STAIRS.csv`.

## Sources read (Drive "Alsenan chalet project", scratchpad copies, never committed)

| Sheet | What was read |
|---|---|
| p7757_arch_sheet10.pdf = SECTION A-A 1:100 (400 dpi scan) | every flight of the stair hall: tread finish lines located by pixel profile (scale 157.5 px per m, checked on 450 = 709 px and 420 = 661 px), levels +0.30, +1.00, +5.50, +9.70, +13.90, dimension "320" |
| p7757_arch_sheet03.pdf = GROUND FLOOR PLAN | main stair (widths "120" / "10" / "120", landing "125", "250", hall "500"), riser lines per column, entrance flight ("280"), round stair ("157", "120") |
| p7757_arch_sheet04.pdf = 1st FLOOR PLAN | main stair run "330", "120" / "10" / "120", "125"; round stair arrival "125", "240" |
| Pages_11-12 part, sheet 11 = SECTION B-B | entrance flight risers; no section through the round stair (the GF view there is the glazing) |
| ST7757.pdf p.4 / p.5 / p.6 slab plans, p.10 schedule, p.16 details | stair panels, "T 16", "8 d16/m", "B3 (With Stair)", the 2F roof slab over the hall; B3 row; TYPICAL STEEL LAYOUT-STAIR SECTION and TYPICAL DETAIL OF STAIR BEAM |
| research/alsenan_stairs_s8_7c (frozen study, by DXF handle) and research/agents_t063 | structural counts, winder levels, B20 / B23 clashes, round-stair counts (cited, not re-measured) |

## Result per stair

| Stair | Risers counted | Riser | Steps concrete (hand) | Status |
|---|---|---|---|---|
| E1 entrance flight, court +0.15 -> GF +1.00, width 2.80 printed | 5 on B-B = 5 riser lines on the GF plan | 0.85 / 5 = 0.170 m | 5 x 1/2 x 0.170 x 0.30 x 2.80 = **0.357 m3** | RELEASED (waist HELD, not printed) |
| D1 GF hall +1.00 -> +0.30 lobby under the landing, width 1.20 printed | 4 on A-A = 4 solid riser lines on the GF plan | 0.70 / 4 = 0.175 m | 4 x 1/2 x 0.175 x 0.30 x 1.20 = **0.126 m3** | RELEASED (waist HELD) |
| MS1 main stair GF +1.00 -> 1F +5.50 | A-A 10 + 5 winders + 12 = 27; arch GF plan 10 + 4 + 11 = 25; structural 12 + 4 + 12 = 28 | 0.1667 / 0.180 / 0.1607 | straight steps 0.660 (27) / 0.680 (25) / 0.694 (28) | HELD: drawings disagree (owner Q-46) |
| MS2 main stair 1F +5.50 -> 2F +9.70 | A-A 13 (12 + closing riser at a flat quarter) + 12 = 25; arch 1F plan 12 + 4 + 11 = 27; structural 12 + 1 + 11 = 24 | 0.168 / 0.1556 / 0.175 | straight steps 0.726 (25) / 0.644 (27) / 0.725 (24) | HELD: drawings disagree (owner Q-46) |
| MS3 2F +9.70 -> roof | none drawn | - | - | NOT_PRESENT: A-A has no flight above +9.70; the 2F roof slab over the hall is a closed T18 slab "WATER TANK PLACE" |
| RS round stair in the reception, GF +1.00 -> 1F +5.50 | no section cuts it; plan 12 curved + 11 straight + corner landing + 5 = 28 | 0.1607 if 28 | straight 0.318 + arrival 0.151 candidate; curved HELD (tapered) | HELD: RISERS_NOT_COUNTED_ON_A_SECTION |
| Waists and landings, every stair | - | - | candidates at 0.16 m: MS1 waists 1.400, MS2 waists 1.485, landings 0.240 + 0.500 | HELD: STAIR_WAIST_NOT_PRINTED / LANDING_NOT_PRINTED (owner Q-47) |

Released by drawing evidence: **0.483 m3** of steps (E1 + D1). Held, never 0: main-stair steps (two storeys), winders,
round stair, every waist and landing. Not one typical value was used: riser 0.15-0.17 and tread 0.30 appear only as
sanity checks; every tread of 0.30 m is the drawn riser-line pitch (47.2-47.6 px at 1:100 on the plans, the same going
on the sections) or the printed run "330" over 11 goings; widths are printed dimensions.

### How the section was counted (A-A, sheet 10)

- GF -> 1F upper flight (cut, hatched): finish lines every 26.25 px = 0.1667 m from the landing at +3.50 (2.50 m above
  +1.00, 394 px) to the 1F finish line +5.50: 12 risers. Lower flight (seen beyond the cut): tread lines at the same
  pitch from +1.00; in the turn four dashed winder treads at +2.667, +2.83, +2.99, +3.155 and a fifth on the landing
  soffit line at +3.33; landing finish +3.50 = "320" above +0.30. 10 + 5 + 12 = 27, equal risers 0.1667 m.
- 1F -> 2F: lower flight seen beyond, 11 visible tread lines at 26.4 px, the 12th tread (+7.52, a flat quarter) hidden
  behind the landing band, one closing riser to the landing finish at +7.675 (+7.684 with equal risers); upper flight
  cut, 12 risers to +9.70. 25 risers, 0.168 m. No winder lines in this turn (the architectural plan draws winders).
- GF hall -> +0.30: a cut flight of 4 risers (27.5 px = 0.175 m, going 47 px = 0.30 m) under the landing, next to the
  outer wall; the plan shows the same 4 riser lines solid under the dashed upper flight.

## Engine vs freelancer (concrete, m3)

| Group | Freelancer | Hand released | Hand candidate (section counts, waists / landings at the 'T 16' tag) | Proposal |
|---|---|---|---|---|
| Main stair (2 storeys, 4 flights) | 8.131 (4 x 1.2 x 5.3 x 0.28 + 3 x 1.2 x 1.4 x 0.20) | 0 (held) | steps 1.386 + winders 0.120 + waists 2.885 + landings 0.740 = 5.131 (-36.9 %) | UNRESOLVED: his 5.3 m flight length is 37-54 % longer than the drawn sloped flights (3.43-3.87 m) and his 0.28 m "slab + steps" depth is not printed |
| Entrance stair | 1.411 (1.8 x 2.8 x 0.28) | 0.357 steps | waist not printed | UNRESOLVED (drawn plan run 4 x 0.30 = 1.20 m, sloped 1.47 m, not 1.8) |
| Stair 2 (most likely the round stair, 16.4 m) | 5.510 (1.2 x 16.4 x 0.28) | 0 (held) | straight + arrival steps 0.469; curved, waists, landing held | UNRESOLVED |
| Hall -> +0.30 lobby flight | none | 0.126 | - | HAND_FOUND, no freelancer row (drawn on A-A and the GF plan) |
| Freelancer "basement" stairs (T-038) | 6.92 = entrance 1.411 + stair 2 5.510 | 0.357 | as above | there is no basement; the 6.92 is these two stairs |

The engine itself was not run (execution refused). Its last recorded stair lines (T-037) are 4.635 m3 by conventions
(waist 0.175, riser 0.165, CONVENTION_ONLY): none of them is a drawing value.

Marble cross-check (freelancer floors / marble workbook): entrance 5 x 2.80 = drawing; inner (round) stair 28 x 1.20 =
the plan's 28; main stair 63 steps against 27 + 25 = 52 risers on the section (27 + 27 = 54 on the architectural plans):
**+11 steps (+21 %) not on any drawing read**, no 2F -> roof flight exists.

## 'B3 (With Stair)' (from T-043, GF CB3 span 2) checked against the stair drawings

- The mark is printed three times: along the round stair's straight flight on the GF roof slab (p.4, over CB3 span 2,
  T-043 SH06-02), and along the outer (neighbour) edge of the main-stair panel on the GF and 1F roof slabs (p.4, p.5).
- ST7757 p.16 "TYPICAL DETAIL OF STAIR BEAM" draws a beam cranked along the flight, depth "AS PER SCH.", bars 2 d12 top,
  4 d16 bottom, 6 d8/m: exactly the B3 schedule row (20 x 40, 4 d16 / 2 d12 / 6 d8, p.10). So "B3 (With Stair)" is the
  cranked stair beam of the typical detail, a member of its own that follows the stair slope, not the floor-level CB3.
- Section A-A (architectural) cuts the main flights lengthways and draws no beam along them (an edge beam parallel to
  the cut is not cut), so it neither confirms nor contradicts the B3 depth.
- Proposal for T-043 SH06-02 / T-085: "both" members (CB3 20 x 75 at floor level + B3 20 x 40 cranked), but the B3 piece is
  measured along the slope (length = sloped flight length, not the 2.65 m plan span) and its end levels are not printed:
  HELD as STAIR_BEAM_LEVELS_NOT_PRINTED, candidate 0.20 x 0.40 x sloped length. Not settled here.

## Double counting checked

- Steps are the wedges above the waist root line; waists are the slabs below it; landings are plan areas at their own
  level: no volume is in two lines. One wedge per flight end (the last riser into a landing or floor) lies inside the
  landing / floor slab zone: when landings are released, measure them from the last riser line and drop that wedge
  from the steps (0.03 m3 per main-stair flight end), or count steps as treads. Today landings are held, so nothing is
  counted twice.
- The 1F and 2F floor slabs end at the stair openings (stair panels on p.4 / p.5 are separate panels): the floor
  landings at +5.50 / +9.70 belong to the floor slab line, not to the stair.

## What we learned (for the engine, every villa)

1. On this drawing set the plans and the section disagree on riser counts on both storeys (25 / 27 / 28 and 27 / 25 / 24):
   the plan riser lines are set-out symbols, the section is the only view that draws each riser against printed levels.
   An engine rule "counts from the section, plans only as a check, conflicts held and shown" is what Q-46 asks.
2. A flight that goes DOWN from a main floor to a lower lobby (here +1.00 -> +0.30) is drawn as solid riser lines under
   the dashed flight above: a plan reader that drops solid lines under a dashed flight loses a stair (the freelancer
   has no row for it).
3. The only thickness printed in the stair zones is the slab tag "T 16" with the stair mesh "8 d16/m", which matches the
   typical stair section's main bars; the typical section itself prints "THICK" with no value.
4. The typical stair section on p.16 prints levels +2.00, +4.00, -0.05: they are not Alsenan levels and must never bind.

## Missing / uncertain

- Owner Q-46 (which drawing gives the riser count) and Q-47 (is "T 16" the waist and landing thickness) hold 1.386 m3 of
  main steps and 3.625 m3 of waists and landings.
- Round stair: no section; its count (28) is a plan count only; its curved treads need a winder / tapered-tread rule.
- Winder wedges: no Urban rule; the 0.120 m3 is indicative (1/2 x riser x the 1.44 m2 quarter).
- The landing levels +7.52 / +7.68 on 1F -> 2F are scaled from the section, not printed.
- docs/CODEMAP.md lists research folders: this new folder makes the map stale; it could not be regenerated (execution
  refused). The verifier regenerates it with `python3 -I tools/codemap.py build`.
