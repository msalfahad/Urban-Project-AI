# T-516: B9-02 lintel jamb bearing census (research rule proposal R-T516-1, Gate A)

Worker 1, 2026-11-05. Lane S. Research only: `t516_extract.py` (drawing reader, scratch inputs outside the repository),
`t516_jamb_bearing.py` (project-agnostic census + training-villa builder), `out/JAMB_EVIDENCE_T516.csv` (numbers only:
lengths from the jamb, wall / opening ids, no coordinate), `out/JAMB_BEARING_T516.json`, `tests/t516_jamb_bearing/`.
No hub, master, candidate, engine, rule or knowledge file changed; released default (V2.9 + route G) untouched.

## 1. Physical element and evidence (ERS s.2.1 - 2.3)

The lintel END resting on the masonry beside an opening. Its built bearing b is not printed for any lintel of this villa.
What the drawings fix:

- ST7757 p.13 LINTEL DETAIL: 'MIN.40cm' each side (transcription pinned, MIN-BEARING row): a MINIMUM, b >= 0.40 where the
  detail is built. A minimum is not the value (same reading as T-515 / owner 2026-10-24 on '70 d at least').
- The architectural plan (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf, sha ab54dd55, decoded
  this run into .work/private): the masonry drawn beside each jamb. Read through the merged MASONRY_CENTRELINE_V2 census
  (research/agents_t125 capture, the same wall records, column outlines and opening gaps every merged wall task uses):
  a = built wall material along the opening's wall line, across the FULL wall thickness, from the jamb to the first
  column outline, next opening / glazed stretch, or end of masonry (free end, or far face of a wall met). b <= a.
- A pier between two lintels is shared: b1 + b2 <= a.
- Owner precast rule (UPC-LINTEL-001, owner 2026-11-02, 0.15 m min bearing, stock 1.20 .. 4.00 m): beside only; the
  register ruling F-T453-1 keeps the project RC LINTEL SCHEDULE governing (level 1).

Visual check (scratch plots, not committed): door swings and frames of the DXF coincide with the census gaps on D-1F-02,
D-1F-03, D-1F-04, D-1F-07, D-GF-06, D-GF-12 and W18; the columns beside D-GF-06 / D-1F-04 / W18 are drawn columns.

## 2. Owner manual method vs drawing-derived method

| | Owner / prior method | Drawing-derived (this record) |
|---|---|---|
| Bearing | T-453 / T-515: exactly 0.40 m each side (the detail minimum used as the value) | b in [0.40, a] where a >= 0.40 (BOUNDED); a < 0.40: FLAGGED_DEFICIT, b <= a, never 0.40, never 0 |
| Concrete length | L = w + 0.80 | BEARING_OK: L in [w + 0.80, w + a_s + a_e]; deficit: w + 0.80 not buildable as drawn, L <= w + a_s + a_e |
| Links (5/m) | ceil(5 x (w + 0.80)) | [ceil(5 (w + 0.80)), ceil(5 (w + a_s + a_e))] or HELD |
| Straight bar ceiling | n x (w + 0.80) x kg/m (T-515) | n x (w + a_s + a_e) x kg/m: the bar cannot leave the concrete |
| Precast (owner practice) | shortest stock >= w + 0.30 | piece and FITS / DOES_NOT_FIT on the measured piers, beside |

## 3. Census, 16 / 16 REQUIRED lintels (32 ends: 21 BOUNDED, 10 FLAGGED_DEFICIT, 1 HELD, 0 MEASURED)

a in m from the jamb (stopper: COL column face, OPE next opening, END end of masonry / far face).

| Lintel | Fl | w | START a -> state | END a -> state | Lintel | L m | links | straight ceiling kg | precast |
|---|---|---|---|---|---|---|---|---|---|
| D-1F-02 | 1F | 1.00 | 2.274 COL BOUNDED | 1.125 COL BOUNDED | OK | 1.80 .. 4.399 | 9 .. 22 | 13.251 | 1.50 FITS |
| D-1F-03 | 1F | 1.00 | 0.238 END DEFICIT | 2.711 END BOUNDED | DEFICIT | .. 3.949 | .. 20 | 11.896 | 1.50 FITS |
| D-1F-04 | 1F | 0.80 | 0.079 COL DEFICIT | 2.120 COL BOUNDED | DEFICIT | .. 2.999 | .. 15 | 9.034 | 1.20 NO |
| D-1F-07 | 1F | 0.80 | 0.259 END DEFICIT | 1.090 END BOUNDED | DEFICIT | .. 2.149 | .. 11 | 6.474 | 1.20 FITS |
| D-1F-08 | 1F | 0.90 | 2.992 END BOUNDED | 0.844 OPE D-1F-09 BOUNDED | OK | 1.70 .. 4.736 | 9 .. 24 | 14.266 | 1.20 FITS |
| D-1F-10 | 1F | 0.80 | 1.340 END BOUNDED | 0.259 END DEFICIT | DEFICIT | .. 2.399 | .. 12 | 7.227 | 1.20 FITS |
| D-2F-01 | 2F | 1.00 | 0.615 END BOUNDED | >= 3.0 BOUNDED (no ceiling) | OK | 1.80 .. HELD | 9 .. HELD | HELD | 1.50 FITS |
| D-2F-03 | 2F | 0.80 | 0.249 COL DEFICIT | 2.150 END BOUNDED | DEFICIT | .. 3.199 | .. 16 | 9.636 | 1.20 FITS |
| D-GF-06 | GF | 1.00 | 0.759 COL BOUNDED | 0.140 COL DEFICIT | DEFICIT | .. 1.899 | .. 10 | 5.720 | 1.50 NO |
| D-GF-10 | GF | 0.80 | 0.253 END DEFICIT | 0.650 END BOUNDED | DEFICIT | .. 1.703 | .. 9 | 5.130 | 1.20 FITS |
| D-GF-11 | GF | 0.80 | 0.831 END BOUNDED | 0.238 OPE D-GF-12 DEFICIT | DEFICIT | .. 1.869 | .. 10 | 5.630 | 1.20 FITS |
| D-GF-12 | GF | 0.80 | 0.238 OPE D-GF-11 DEFICIT | HELD (oblique 3-wall junction; own band 0.141) | DEFICIT | HELD | HELD | HELD | HELD |
| D-GF-13 | GF | 1.00 | 1.503 END BOUNDED | 1.261 COL BOUNDED | OK | 1.80 .. 3.764 | 9 .. 19 | 11.338 | 1.50 FITS |
| W14 | 1F | 2.45 | 0.618 COL BOUNDED | 1.032 END BOUNDED | OK | 3.25 .. 4.10 | 17 .. 21 | 34.319 | 3.00 FITS |
| W15 | 1F | 1.55 | 0.794 COL BOUNDED | 0.493 OPE W16 BOUNDED* | OK | 2.35 .. 2.837 | 12 .. 15 | 11.908 | 2.50 FITS |
| W18 | 1F | 0.50 | 0.000 COL DEFICIT | 0.478 glazed bay BOUNDED | DEFICIT | .. 0.978 | .. 5 | 2.946 | 1.20 NO |

\* W15 / W16 share a 0.493 m pier: W16's lintel is HELD (head not established); IF it gets one, both 0.40 minimums
cannot be built (conditional flag). D-1F-08 / D-1F-09 share 0.844 m >= 0.80: both minimums fit.

Deficit causes (physical): next to an RC column (D-1F-04 0.079 m stub, D-2F-03 0.249, D-GF-06 0.140, W18 jamb on the
column face); door beside a cross wall, bearing at most through that wall to its far face (D-1F-03 0.238, D-1F-07 0.259,
D-1F-10 0.259, D-GF-10 0.253); two doors 0.238 m apart (D-GF-11 / D-GF-12).

Hand checks: W14 L = 2.45 + 0.618 + 1.032 = 4.10, links ceil(20.5) = 21, ceiling (3 x 256 + 3 x 196)/162 x 4.10 =
34.3185 kg; D-1F-07 a = 0.109 (own wall) + 0.150 (cross wall) = 0.259 < 0.40; D-GF-11 / 12 pier 1.9056 - 1.6672 = 0.2384.

## 4. Effect on merged figures (nothing applied; proposals for the Checker / integration)

- T-515 span AT_LEAST **63.161728 kg unchanged** (the span part does not depend on the bearing).
- T-515 'straight ceiling' 106.954321 kg assumed b = 0.40 exactly: on the 6 BEARING_OK lintels it is NOT a ceiling
  (58.456 kg at 0.40 vs the true pier-bounded 85.083 kg on 5 of them, D-2F-01 HELD: pier >= 3.0 m); on the 10 deficit
  lintels (48.499 kg at 0.40) b = 0.40 is not buildable; their hard ceiling is 63.693 kg (D-GF-12 HELD). Proposal:
  publish the T-515 ceiling as HELD, with these bounds beside.
- T-453 / V3.0.53 STR.CONC.LINTEL concrete (B x D x (w + 0.80)): BEARING_OK lintels 0.502 m3 = a LOWER bound (label
  MIN_BEARING; upper HELD by D-2F-01, 0.746 m3 without it); deficit lintels 0.514 m3 / formwork 7.730 m2 are lengths the
  masonry cannot carry as drawn: verdict proposal ENGINE_WRONG on the label (exact -> HELD by name on 10 lines, lower
  bound on 6), quantity change left to the integration package.
- Freelancer: no lintel row (RC workbook one rebar total 44.19 t; no lintel concrete row): UNRESOLVED, no comparison.

## 5. Designer RFI (not an owner question: ERS 2.7 not met, a drawing / structural fact)

"10 of 16 lintels have less masonry beside one jamb than the LINTEL DETAIL's MIN 40 cm (4 against RC columns, 4 beside
cross walls, 2 sharing a 0.24 m pier). For each: is the lintel dowelled / cast into the column, extended through the
cross wall, made one lintel over D-GF-11 + D-GF-12, or replaced by the owner's precast piece (on its 0.15 m minimum it fits 6 of the 10 taken
alone; D-GF-11 + D-GF-12 together need 0.30 m of a 0.238 m pier, so not both)?" Until answered those lines stay HELD by name; the 6 BEARING_OK lintels carry [lower, upper] bounds.

## 6. Open

- No built bearing is printed: MEASURED is supported (fixture) but never reached on this villa.
- D-GF-12 END: oblique three-wall junction (V2 leaves it unresolved): HELD.
- Width basis: census width vs DXF gap differ by <= 0.2 mm (W14 2.45 vs 2.4498); the gap fixes the jamb.

Lessons row (proposed, ERS s.7): | 2026-11-05 | a printed MINIMUM bearing was used as the bearing of every lintel |
hides 10 lintels whose jamb cannot take the minimum and makes the bar 'ceiling' a lower figure | measure the masonry
beside each jamb (to column face / next opening / end of masonry, full thickness, shared piers shared); min bounds from
below, pier from above, deficit FLAGGED, never the minimum | tests/t516_jamb_bearing | T-516 |
