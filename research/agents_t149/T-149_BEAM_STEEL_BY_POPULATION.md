# T-149 Alsenan beam steel by bar population, per beam and span (lane S, gate 3; NO REPO CODE; a checked piece for V3.0)

Worker 1, 2026-10-21. Development villa, not an accuracy claim. Hand ledger only: `t149_spans.py` measures the span
order, support widths and axis-to-axis spans on the structural DXF; `t149_beam_steel.py` does the arithmetic of a hand
table typed from the issued schedules (neither imports anything from `engine/`). `T149_SPANS_INPUT.csv` = the 137 spans
of the T-110 register + the T-145 CB5 span 2 row (GF CB7 split at its middle column: 139 rows); `T149_BEAMS.csv` =
752 rows, one per span and component; `T149_SUMMARY.json` the totals. Nothing released changes; nothing is wired.

Repeat: `.work/venv/bin/python -I research/agents_t149/t149_spans.py <ST7757 dxf> research/agents_t110/BEAM_MEMBER_REGISTER.csv research/agents_t149/T149_SPANS_INPUT.csv`
then `python3 -I research/agents_t149/t149_beam_steel.py --check`.

## Sources read this run (Drive "Alsenan chalet project"; structural DXF sha 9f9d1179, structural PDF sha 74da1523 = manifest)

| What | Where | Read |
|---|---|---|
| Simple-beam bars | PDF p.10 "Schedule of Simple Beams" (400 dpi), B1 .. B29, CA, B.W, SB1 .. SB3 | bottom / top "n ø d", STIRRUPS/m "n ø d", remarks: side bars 2ø12/30cm (B7 .. B15, B17, B18, B20 .. B25, B28, B29), 2ø14/20cm (B19), 2ø16/20cm (B16, B26, B27); link symbol with two nested links on B17, B19 .. B26 (B.W none; SB1 / SB3 two, SB2 three: ground straps, T-138) |
| Continuous-beam bars | PDF p.11 (2 span: CB1, CB2, CB4, CB5, CB6, CB7, CB10, CB12, CB13) and p.12 (3 span: CB3, CB8, CB9, CB11) | per span: top corner bars, bottom bars, STIR n ø d /m; bar over each interior support; MIDDLE REINT. 2ø12/30cm on CB1, CB3, CB6, CB7, CB8, CB11, CB12. Two irregular rows: **CB3** has no corner bar in span 2 and ONE 3 ø16 over both interior supports (it spans the whole middle span); **CB8** has no corner bar in span 1: its 5 ø18 starts hooked at the end support and runs over support 1 |
| Bar extents | p.11 / p.12 typical details | bar over an interior support: 0.22 Ln into each span, measured from the support FACE (ticks at the clear-span end L); Ln = support axis to support axis (dimension between the dashed axes); first link 7.5 cm from the face. "0.3 Ln2" at the end support and "0.15 L" are drawn but no bar of the schedules is tied to them: not used |
| Notes | p.8 note 9 (Arabic): anchorage length of **starter bars ("اشاير")**, "Development Length", not less than 70 d in tension zones, 40 d in compression zones; note 21: side bars 2 / 3 / 4 ø12 in beams deeper than 60 cm by width, unless stated otherwise; note 22: cover 2.5 cm in beams | note 9 is applied as the HELD 40 d .. 70 d range at bar ends, as T-138 r2 / T-148 did, but see finding 6 |
| Stair beams | p.16 "TYPICAL DETAIL OF STAIR BEAM": 2 ø12 top, 4 ø16 bottom, 6 ø8/m on a cranked profile, no dimensions | = the B3 row; "(With Stair)" printed beside B3 on the GF and 1F roof plans (DXF S-TEXT) |
| Planted columns | p.15 "BEAM CARRYING PLANTED COL. DETAIL": 4 ø16 in the carrying beam | length not dimensioned |
| Spans | T-110 register (merged), T-145 CB5 span 2 (merged d0b91a4), DXF layers 1 / 5 / S-COL.BON | clear length, span order, supports |
| Freelancer | workbook "حصر خرسانة+الحديد", sheet 1 row "الجسور" | 65.966 m3, steel 9.89 t (= 150 kg/m3) |

## Result: engine vs freelancer (Alsenan, beam steel above the ground beams, kg, net)

Main bars: kg = count x length x d^2/162; length = clear span face to face (simple beams, continuous bottom bars),
clear span less the zones of the support bars (continuous top corner bars), 0.22 Ln + support + 0.22 Ln (support bars).

| Floor (roof slab of) | Hand NET RELEASED | Hand HELD, defined | Hand HELD, candidates | Frozen engine S6 (lower bound) | Freelancer |
|---|---|---|---|---|---|
| GF | **2,954.89** (simple 2,174.52 + continuous 780.37) | 398.94 (B21, B29, CB2 width conflicts; GF stair beam B3) | 64.86 .. 82.63 | 1,781.42 | lump, see below |
| 1F | **1,917.81** (simple 1,415.77 + continuous 502.04) | 137.36 (B6, CB10 width conflicts; 1F stair beam B3) | 78.09 | 1,572.18 | |
| 2F | **298.33** (simple) | - | 33.91 .. 77.69 | 276.55 | |
| **Total** | **5,171.03 kg** | **536.30 kg** | **176.86 .. 238.41 kg** | **3,630.15 kg** | 9.89 t "beams" lump |

HELD on top of net (ranges, never 0; released members first, members already held in brackets):

| Item | kg | Why held |
|---|---|---|
| Links (count = owner Q-71, rate per metre) | A 1,963.12 / B 2,035.52 / C 1,949.80 at the lower path; B upper path 2,199.22 [held members A 253.50 / B 259.71 / C 253.39] | A = ceil(rate x zone), B = A + 1, C = rate x clear span; zone = clear span less 2 x 7.5 cm for continuous beams (printed), clear span for simple beams (no offset printed); nested links (symbol) not dimensioned: lower path = outer link + two legs per extra link, upper = n outer links; hooks not printed |
| Bar ends, note 9 | 1,610.85 .. 2,818.98 [133.10 .. 232.93] | 40 d .. 70 d per end, 2 ends per bar run (one for CB8's 5 ø18), zone not printed; note 9 is written for starter bars (finding 6) |
| Side bars | at least 361.94 [25.28] (2 bars x span) | "2ø12/30cm": 2 bars in all or 2 per face per 30 cm of depth is not printed; count from a spacing = Q-71 |
| Bars over end columns inside the register span | 13.83 | register runs to an end column's outer face (finding 2); anchorage, kept apart from net |
| Ln upper reading (3 end supports not closed on the DXF) | 0 .. 0.58 | GF CB3 east end, GF CB4 south end |
| Unquantified | B26 / B27 planted-column extra 4 ø16; upstands on B20 / B23; 10 projection pieces and strips with no schedule row (D-05 / D-26); hooks and bends; cantilever free end of GF B20 west span; stair-beam crank | not printed |
| Procurement laps | 0 | no single bar run over the 12 m stock (longest: CB1 / CB8 support bars 5.6 m, B22 7.80 m) |

**Freelancer**: one line "الجسور" 65.966 m3 with steel 9.89 t, i.e. 150 kg/m3: a kg/m3 allowance, not a bar population.
**RULE_DIFFERENCE, no %** (URBAN-REBAR-NET-AND-PROCUREMENT@v1: never kg/m3). For orientation only: defined main bars
5,171.03 + 536.30 = 5.71 t, links 1.95 .. 2.20 t (+ 0.25 .. 0.30 t on held members), bar ends 1.74 .. 3.05 t (all held), against his 9.89 t.

## What the hand reading found (verdict proposals for the checker)

1. **Simple beams: the frozen engine S6 equals the hand on 51 of 56 spans both release** (1,726.13 hand vs 1,728.18 S6
   kg on the 56; the five differ only by the register clear length, 0.01 .. 0.06 m): **ENGINE_RIGHT** on bar counts and
   the face-to-face basis.
2. **Register length runs over an end column on 5 spans** (new, for lane I / the T-110 register): GF CB1 span 1 (7.400 ->
   6.998, column 0.40 inside the 0.35 band at the south end), GF CB8 span 1 (3.450 -> 3.050), GF CB7 span 1 (the band
   start lies inside the corner column: 5.651 -> 5.450 once split), GF B2 (2.900 -> 2.502), GF B16 (3.850 -> 3.475, the
   turned-column zone); GF B9 (0.201) and GF B13 (0.029) are candidates only (fewer than two drawn end faces: not
   applied, register length kept). Hand check B2: column x 44.793 .. 45.193 over
   the whole band y 42.848 .. 43.048; register end x 45.191 -> clear 2.900 - 0.398 = 2.502 m. The concrete m3 of T-110 is
   unaffected where the column is narrower than the band (CB1, CB8: concrete beside the column), but no bar is "clear
   span" over a column: the 0.40 m parts are held as anchorage (13.83 kg).
3. **GF CB7 is two spans**: the 11.80 m register band runs through its middle column (x 47.943 .. 48.343 inside the band):
   5.450 + 0.400 + 5.749 m; Ln 5.85 / 6.15 m against printed 6.0 / 6.1. The beams framing in (B4 at 4.10 m in span 1; B4
   at 1.25 m and B1 at 4.45 m in span 2) match the schedule's concentrated loads (4.1 | 1.3, 4.5): span order confirmed.
4. **Span order of every continuous beam checked against the drawing**: Ln (axis to axis) against the printed design
   spans and the beams framing into each span against the printed concentrated loads. All forward (plan west -> east /
   south -> north = schedule left -> right). CB9 and CB13: Ln alone would fit the reverse order slightly better, the
   framing beams do not (CB9: B2 at 1.90 m in the west span = load 2.0 in span 1, nothing frames into the east span;
   CB13: one beam in the south span, two in the north = one load in span 1, two in span 2): forward kept, reverse delta
   not released. CB3: spans 1 / 3 carry the same bars, order does not change kg.
5. **S6 does not release continuous top corner bars, CB4 / CB5 / CB8 / CB3 at all, and runs continuous bottom bars
   through the supports + 7.5 cm** (CB11 bottom S6 141.72 vs hand 118.11 kg face to face; CB1 117.35 vs 106.98): the
   through-support part is anchorage, which this ledger holds. **Support bars agree** (S6 MID_TOP vs hand: CB1 53.94 /
   53.97, CB11 64.65 / 64.64, CB12 41.89 / 41.89, CB7 30.40 / 30.40, CB13 22.79 / 22.79, CB6 22.61 / 22.62; CB9 28.94 /
   29.14 from the support widths): ENGINE_RIGHT on the 0.22 Ln reading (axis-to-axis Ln, from the face).
6. **p.8 note 9 is a starter-bar note** (Arabic "طول رباط اشاير حديد التسليح": anchorage length of the starter bars).
   S6 reads it that way and gives beam bar ends no length. T-138 r2 and T-148 (and this ledger, as the task asks) apply
   40 d .. 70 d to every bar end as a HELD range. Nothing is released on it, but the Lead should put to the owner whether
   note 9 governs beam laps / anchorage at all (it also touches the T-138 r2 and T-148 held ranges).
7. **Two B3 spans are stair beams** ("(With Stair)" beside the label on the GF and 1F roof plans; p.16 detail = B3's
   bars on a cranked profile without dimensions): HELD_DEFINED 20.25 kg each (plan length only a lower bound). T-110
   lists them CALCULATED; S6 blocks them.
8. **S6 takes shorter spans than the T-110 register on 9 simple beams** (GF B22 6.40 vs 7.80, 1F B18 4.85 vs 6.30, 2F B7
   4.418 vs 6.60, GF B27 3.444 vs 4.95, GF B11 2.625 vs 4.554, GF B13 3.398 vs 4.998, 1F B19 2.876 vs 5.3375, GF B20 2.5
   vs 3.0 / 3.3, GF B5 / B4): B22, B18 and 2F B7 were re-measured by hand in T-110 (= register): **ENGINE (S6) WRONG on
   those three** (it cuts the band at a crossing beam), the other six not re-measured here (UNRESOLVED for the checker).
9. **Width conflicts (D-27, D-02)**: B21, B29, 1F B6 span, CB2, CB10 bar counts and lengths do not depend on the width,
   but the register holds them (Q-61 C(1)): HELD_DEFINED 495.81 kg; only their link paths depend on the width.
10. **B15 (D-44)**: released (10 bars x 2.70 m): up- or downstand changes the concrete overlap with the slab, not the bar
    count or length. **CB1 / B24 (D-30)**: released; section D-D concerns the shape, the schedule rows govern the bars.

## Owner manual method and drawing-derived method side by side

| | Owner / Urban manual method (this ledger) | Drawing-derived engine (frozen S6) | Route G |
|---|---|---|---|
| Count | as printed (p.10 / p.11 / p.12) | as printed | not re-run this time |
| Main bar length | clear span face to face from the plan (register, corrected at end columns) | support face to support face (its own spans; shorter on 9 beams) | |
| Continuous top | corner bars: clear span less 0.22 Ln per support bar; support bars 0.22 Ln + support + 0.22 Ln | corner bars not released; support bars same reading | |
| Continuous bottom | clear span; through-support and lap HELD | clear span + support + 7.5 cm | |
| Ends, laps | 40 d .. 70 d per end HELD (note 9, zone not printed; note written for starter bars) | none (no beam-source rule) | |
| Links | rate per metre, readings A / B / C HELD (Q-71); path at 2.5 cm cover, nested links lower / upper | counts released as lower bound (no + 1), no mass | |
| Side bars | HELD (2-bar minimum shown) | text kept, blocked | |
| Mass | d^2 / 162 | d^2 / 162 | |

## Three spans for the checker (re-count on p.10 / p.11 / p.12)

| Span | Schedule | Hand |
|---|---|---|
| GF B22 (R052, T-110 re-measured 7.80 m) | 50 x 75, 14 ø18 bottom, 5 ø14 top, 5 ø8/m, 2ø12/30cm, two nested links | 14 x 7.80 x 2.0000 = 218.400 + 5 x 7.80 x 1.2099 = 47.185 -> **265.585 kg RELEASED**; links A 39 / B 40 / C 39.0 on a 3.700 .. 4.600 m path (HELD, Q-71) |
| 1F CB11 (3 spans, R097 .. R099) | 30 x 75; span 1 6 ø18 bottom, 2 ø12 top; support 1 8 ø18; support 2 4 ø16 | span 1 bottom 6 x 6.7083 x 2.0000 = 80.500; Ln1 = 6.7083 + 0.70 / 2 + 0.7988 / 2 = 7.4577, Ln2 = 3.3499; support 1: 8 x (0.22 x 7.4577 + 0.7988 + 0.22 x 3.3499) x 2.0000 = 8 x 3.1765 x 2.0 = **50.824 kg**; span 1 corner 2 x (6.7083 - 0.22 x 7.4577) x 0.8889 = 9.009 kg |
| GF B20 west span, cantilever (R049, 3.00 m, T-145 hatch "Cantilever portion") | 40 x 75, 11 ø18 bottom, 11 ø18 top | 22 x 3.00 x 2.0000 = **132.000 kg RELEASED**; the free end treatment is not detailed (unquantified) |

## Non-Alsenan hand fixture (asserted by `--check`)

Beam "K7": 2 spans 25 x 60, clear 4.00 / 5.00 m, supports 0.30 / 0.40 / 0.30 -> Ln 4.35 / 5.35. Bottom 3 ø16 x 4.00 =
18.963 kg, 4 ø16 x 5.00 = 31.605 kg; corner 2 ø12 x (4.00 - 0.22 x 4.35 = 3.043) and x (5.00 - 0.22 x 5.35 = 3.823);
support 5 ø16 x (0.957 + 0.40 + 1.177 = 2.534 m); links 6 ø8/m over 4.00 - 0.15 = 3.85 m: A 24 / B 25 / C 24.0, path
2 x (0.20 + 0.55) = 1.50 m; ends 3 ø16 x 2 x 0.64 .. 1.12 m. Simple "K1" 25 x 50 whose register runs 0.30 m over an
end column: released on 3.00 m, 0.30 m held apart; a width conflict -> HELD_DEFINED with the same kg; a strip with no
schedule row -> UNQUANTIFIED (never 0); 6 / m x 3.00 m = exactly 18 links. The span tool's orientation and end-column
tests are geometric (rotation / mirror give the same faces). Plus a re-add of the project ledger (rows -> floors ->
total).

## Not done / uncertain

- Clear lengths of most simple spans are T-110's route G lengths (5 re-measured there, 5 corrected here at end columns, 2 more flagged).
- GF CB3 east end and GF CB4 south end are not closed by a face line on the DXF (Ln range kept; +0.58 kg at most).
- Ground straps SB1 .. SB3 and B.W are in T-138 / foundation scope, not here; CB lift-shaft beams of note 19 are not on
  the slab plans (none in the register).
- Designer requests for the Lead: stair-beam crank (B3 With Stair), planted-column extra length, link hooks and nested
  link sizes, the side-bar notation, note 9 scope; D-02, D-27, D-28, D-44 unchanged.
