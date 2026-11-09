# T-519: B9-02 lintel pieces by system and standard length, plus LINTEL_BEARING_V2 (R-T519-1, Gate A)

Worker 1, 2026-11-05. Lane S. Research only: `t519_lintel_pieces.py` (project-agnostic rule + training-villa builder
over the sha-pinned merged T-516 / T-453 outputs and the S8.6 schedule transcription), `lintel_bearing_v2.py`
(F-C-T516-1 successor of the T-516 reach / stopper step), `tests/t519_lintel_pieces/` (26 tests). No engine, rule,
knowledge, hub, master or candidate file changed; released default (V2.9 + route G) untouched; bars untouched.
Rebuild: the tests call `build()`; no private file is needed.

## 1. Engineering question first: which lintel system, per opening (ERS s.2.1 - 2.3)

Physical element: one lintel per opening over the masonry opening, resting on built masonry at both ends.
Evidence, highest first:
- ST7757 p.13 LINTEL SCHEDULE (S8.6 transcription, pinned): cast-in-situ RC, B = wall width, D by width band
  L1 0-100 / L2 101-200 / L3 201-300 / L4 301-500 / L5 501-750 cm; note 'B-WIDTH OF THE BLOCK WALL' (block walls, no
  block type excluded); LINTEL DETAIL 'MIN.40cm' (a minimum, not the bearing).
- Owner Q-60 standing directive: "engineering office rules override urban project rules"; atab (precast) only for
  white blocks.
- UPC-LINTEL-001 (owner 2026-11-02, level 3): precast stock 1.20 / 1.50 / 2.50 / 3.00 / 4.00 m, 0.15 m minimum,
  shortest stock >= opening + 2 b, > 4.00 m FLAGGED; its scope: "a printed structural lintel schedule ... governs
  instead (never both)".

Rule R-T519-1 (every villa): a printed schedule whose scope covers the wall's block type and whose band covers the width
-> PROJECT_RC (cast to length, no stock length); covered wall but width in a band gap / above the last band -> HELD
(SCHEDULE_SILENT, never the nearest band); no schedule: WHITE wall -> OWNER_PRECAST, BLACK wall -> HELD (the company rule
defers black walls to the drawings, which are silent). Decided by the hierarchy, never by the longer piece.

Training villa: all 16 REQUIRED widths (0.50 .. 2.45 m) fall inside L1 / L2 / L3 and the schedule covers every block
wall -> **PROJECT_RC governs 16 / 16**; owner precast: governing on 0, BESIDE on the 5 white-wall lintels only, at the
project bearing 0.40 m (the detail's scope is every block-wall lintel: level 1 > company 0.15 m); black walls: no
precast alternative (Q-60). The 44 HELD / FLAGGED openings keep their band (same as T-453 for 60 / 60) and stay HELD.

## 2. Owner manual method vs drawing-derived method

| | Owner manual (precast practice) | Drawing-derived (governs here) |
|---|---|---|
| System | atab in white walls, stock pieces | project RC schedule, every block wall |
| Length | shortest stock >= w + 2 x 0.15 (company) | cast to w + b_s + b_e, b in [0.40, pier] (T-516) |
| Bearing | 0.15 m minimum | MIN.40cm printed; pier measured from the DXF |
| Count | 1 piece per opening | 1 per opening; HELD where an end cannot take the minimum |

## 3. Pieces (nr)

RC, governing: **6 nr PRODUCED** (BEARING_OK: D-1F-02, D-1F-08, D-2F-01, D-GF-13, W14, W15; lengths T-516: e.g. W14
3.25 .. 4.10 m, D-2F-01 1.80 .. HELD); **10 HELD by name** (bearing deficit: D-1F-03, D-1F-04, D-1F-07, D-1F-10,
D-2F-03, D-GF-06, D-GF-10, D-GF-11, D-GF-12, W18; at most 1 each; D-GF-11 + D-GF-12 may become one: designer RFI of
T-516). Ceilings equal T-516 on 16 / 16 (tested).

Precast BESIDE (white walls, b = 0.40, fit on the measured piers: each end >= b and a_s + a_e >= piece - w):

| Lintel | w | w + 0.80 | stock | piers (m) | fit |
|---|---|---|---|---|---|
| D-2F-01 | 1.00 | 1.80 | 2.50 | 0.615 / >= 3.0 | FITS |
| D-GF-06 | 1.00 | 1.80 | 2.50 | 0.759 / 0.140 | DOES_NOT_FIT (0.140 < 0.40) |
| W14 | 2.45 | 3.25 | 4.00 | 0.618 / 1.032 (1.650 >= 1.55) | FITS |
| W15 | 1.55 | 2.35 | 2.50 | 0.794 / 0.493 shared W16 | CONDITIONAL, HELD (W16 HELD; 0.493 < 2 x 0.40) |
| W18 | 0.50 | 1.30 | 1.50 | 0.000 / 0.478 | DOES_NOT_FIT (jamb on the column face) |

By stock length (beside): 1.20 -; 1.50 W18 flagged; 2.50 1 produced (D-2F-01) + W15 held + D-GF-06 flagged; 3.00 -;
4.00 1 produced (W14). Governing precast on this villa: none (NOT_APPLICABLE, not 0).

## 4. Reconciliation in nr to the cause

- T-453 (merged): 16 RC lintels, 1 nr each, all labelled REQUIRED with L = w + 0.80. R-T519-1: 6 PRODUCED + 10 HELD.
  Cause: T-453 did not measure the jamb masonry (its own open check); T-516 found 10 ends below the printed minimum.
- T-453 precast beside (5 white, b 0.40): 2.50 / 2.50 / 4.00 / 2.50 / 1.50 = this record 5 / 5 in nr and length; T-453
  had no fit test: 2 DOES_NOT_FIT and 1 CONDITIONAL are new.
- T-516 precast beside (company 0.15 on all 16): 11 pieces on BLACK walls not applicable (Q-60); on the 5 white,
  4 lengths differ by the bearing basis only: D-2F-01 1.50 -> 2.50, D-GF-06 1.50 -> 2.50, W14 3.00 -> 4.00,
  W18 1.20 -> 1.50; W15 2.50 the same.
- Freelancer: no lintel row (RC workbook one rebar total; no lintel concrete / piece row): **UNRESOLVED**, no
  comparable cell.

## 5. LINTEL_BEARING_V2 (F-C-T516-1)

`lintel_bearing_v2.py`: linear tolerance (every non-masonry piece of the strip must be <= 0.5 mm in one direction:
hairlines close, intrusions stop) and the reach ends where a non-hairline piece touching the leading edge begins, so
the tolerance never lengthens the reach (V1 overran by up to its area tolerance / thickness, about 0.13 mm, at every
end and up to sqrt(2e-5) = 4.5 mm into a pointed column corner). The stopper probe is the full band slice, columns
first: a column corner off the axis is COLUMN. Tested on synthetic geometry against V1 (corner 4.47 mm overrun vs 0;
long 0.2 mm seam: V1 stops < 0.2 m, V2 runs on; real 1 mm gap stops both; rotation 30 degrees and mirror identical).

Training-villa re-run: **NOT EXECUTED**. The DXF chain (Drive -> decode -> t125 dump / V2 run -> extract) needs
research scripts that the run wrapper refuses (`run allows only tools/alsenan_scoreboard.py or
tools/alsenan_keymap.py`; Lead blocker 'wrapper allow-list'). Expected moves, from the Checker's own re-measure, recorded
not applied: D-GF-11 START 0.831 -> 0.827 m, END_OF_MASONRY -> COLUMN, state BOUNDED unchanged, hard length ceiling
1.869 -> 1.865 m; no other end within 5 mm of 0.40 m, so 0 states can move. No quantity in this record depends on it
(D-GF-11 is HELD on its END deficit).

## 6. Open / not done

- V2 on the DXF (above). D-GF-12 END (oblique junction) HELD. W16 head HELD (holds W15's precast fit).
- No supplier load / span table: precast fit is geometric only (UPC-LINTEL-001 'capacity NOT_PERFORMED').

Lessons row (proposed, ERS s.7): | 2026-11-05 | a precast stock piece was chosen for every lintel at the company
bearing, on black walls too, without asking which system the drawings specify or whether the piece fits the piers |
wrong product, 11 non-applicable pieces and 4 wrong lengths | decide the system per opening by the hierarchy (printed
schedule in scope -> RC cast to length; else white -> precast, black -> HELD); a precast piece counts only when it fits
the measured piers | tests/t519_lintel_pieces | T-519 |
