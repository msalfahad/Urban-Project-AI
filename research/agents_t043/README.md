# T-043: hand reading of the 24 held beam spans and bands on the Alsenan slab plans

Worker 2, 2026-10-19. NO REPO CODE task: hand reading only. Source: Drive "Alsenan chalet project" / "ST7757 dxf.dxf"
(read in the scratchpad, never copied here). Span list: `research/urban_engine_m4_correctness/07_UNRESOLVED_CONCRETE_EXCEPTIONS.csv`.
Coordinates in m (the DXF is in mm). Rule: UP-QTY-STATUS-001; owner answer Q-16 = A (hold unless the drawing gives enough
evidence, never copy a neighbour's depth). Full table, one row per span: `SPANS.csv`.

EXECUTION NOT VERIFIED: the session refused the project's own Python environment this run ("[Code from External]"), so no
engine code, codemap, pytest or freeze check was run. Everything here was read from the drawing with three small stdlib
scripts of this task (`dxfscan.py` census / window / marks, `rows.py` schedule rows, `render.py` window pictures), run with
the system Python on the scratchpad copy.

## Result: 24 of 24 classified with sheet evidence

| Class | Spans | Concrete |
|---|---|---|
| Section printed on the span (Section B-B, Section A-A) | 1F B23 west span, GF B20 west span | 1.0125 + 0.900 m3 released (DRAWING-VERIFIED) |
| Same span split by the engine at a planted column (P.C) | GF B26 south piece, GF B27 south piece | 0.683 + 0.841 m3 released |
| Mark printed, binder missed it | GF B7 strip (1.70 m) | 0.255 m3 released |
| Mark printed, schedule width differs from the drawing | 1F CB10 (2 spans) | HELD: 0.744 (printed 0.25 x 0.50) or 0.893 m3 (drawn 0.30) |
| Two marks on one span (binder right to hold) | GF CB3 / "B3 (With Stair)" | HELD: 0.212 - 0.610 m3 |
| Dome ring segments, two printed sections disagree | 1F ring x2 | HELD: 0.281 - 0.422 m3; scope open after Q-29 |
| Ring segment round the GF void, no mark of its own | GF x1 | HELD: 0.035 - 0.105 m3 |
| Unlabelled span past a column (Q-16 A) | 2F x4, 1F x1, GF B24 east | HELD: 1.00 - 2.44 m3 |
| No mark; the section through it shows no concrete | 1F and GF 0.20 m strip north of B23 / B20 (2 + 2) | HELD: 0.56 - 1.69 m3; proposal NOT A MEMBER (RFI) |
| No mark, outer facade strips and boxes | 1F west outer strip, 1F SE box, 1F strip outside CB12 | HELD: 1.41 - 3.02 m3 |

Released by drawing evidence: 5 spans, **3.691 m3** (was HELD, 0 in no total). Still held: 19 spans, 4.25 - 9.18 m3 (engine
exposure range). New items the engine does not have at all: two 0.20 x 0.20 m upstands on top of B23 (1F) and B20 (GF),
3.00 m each, printed in Sections B-B and A-A: **0.240 m3**.

## Engine vs freelancer

The beam line is HELD on the scoreboard (SCOREBOARD.md: concrete 5 lines held), so beams engine vs freelancer is
**not measured**. Effect once the 5 releases are accepted: +3.691 m3 of beam concrete measured from the drawing, +0.240 m3
upstands; no released quantity changes today (nothing in this task is wired).

## Verdict proposals (for the verifier)

- SH04-09 B23 west span, SH06-05 B20 west span: ENGINE_RIGHT to have held them without a label; the sections settle them.
  Section B-B (cut x 15.667 through the B23 west span) prints 45 / 75 / 25 / 20 / 20 cm with 11 T18 top and bottom = B23
  row (45 x 75, 11 T18 / 11 T18). Section A-A prints 40 / 75 / 20 / 20 with 11 T18 top and bottom = B20 row. Hand:
  3.00 x 0.45 x 0.75 = 1.0125 m3; 3.00 x 0.40 x 0.75 = 0.900 m3; upstands 3.00 x 0.20 x 0.20 = 0.120 m3 each (plan: a
  layer-2 line at y 45.148, 0.20 m inside the north face, over 3.00 m on both floors).
- SH06-07 B26, SH06-08 B27: ENGINE_WRONG split. Both beams' edges are single lines from end column to end column (B27
  on layer S-BEAM: 0.900 m apart = B27 width; B26: 0.650 m = B26 width). The column outline where the engine split them is
  the one the notes "P.C 20x50" / "P.C 20x70" point to (planted columns: carried by the beam, not supporting it), and the
  crossing band lines stop at the B26 / B27 faces. Net plan from the engine: 0.80382 x 0.85 = 0.683 m3; 0.98898 x 0.85 =
  0.841 m3.
- SH06-01: ENGINE_WRONG (missed mark). "B7" is printed 0.064 m above the 1.70 m strip, parallel, inside its length; B7 row
  20 x 75: 1.70 x 0.20 x 0.75 = 0.255 m3. The cause in the binder was not traced (no code run).
- SH04-07/08 CB10: UNRESOLVED. CB10 is printed only outside an outer 0.20 m strip; the inner 0.30 m strip holds both
  columns and its spans fit the CB10 row (3.0 / 4.1 m printed; 2.85 / 4.175 m axis). On GF the same layout prints CB5
  outside an outer strip and the CB5 row width (0.20) is the inner strip's, so the label names the inner beam line. But CB10
  is printed 0.25 wide and the inner strip is drawn 0.30 (its mirror CB13 is printed 0.30 = drawn 0.30). Designer RFI.
- Everything else: UNRESOLVED as listed in SPANS.csv, with candidates and rejected alternatives.

## What we learned

1. **Unbroken edge lines over a column do not prove the same section on this drawing set.** On 2F one top band drawn with
   single lines over 7.9 / 8.1 m carries B3 on its west span and B8 on its middle span (20 x 40 vs 20 x 75). So a span is
   released only by a section, a mark or a proven non-support (B24 east, B2 south and the 2F pieces stay HELD).
2. **Planted columns split beams that are not split.** `engine/source/member_detection.py:841 split_at_supports` cuts a
   band at every column outline, including planted columns ("P.C axb") that sit on the beam; the P.C label parser already
   exists in `engine/source/concrete_completeness.py:141` and `:1592`. Proposed task: a new detection version (never an
   in-place edit) that does not split a band at a column outline a P.C note points to when the band's edge lines run
   through it and the crossing bands stop at its faces. Alsenan effect: 2 spans, 1.524 m3 released; adversarial cases:
   a real column under a continuous line (must still split), P.C with no leader, mirrored / rotated beam.
3. **The beam sections (A-A, B-B) sit on the slab plan sheets at a 4x scale**, with their own dimension text; reading
   them gave two DRAWING-VERIFIED sections and a member type (upstand) the engine never measures.
4. **The 1F dome ring has two printed sections**: B4 on the plan (20 x 50; 4 T16 / 2 T12 / 6 T8 per m) and the dome
   detail's ring (20 wide, depth text "AS PER ARCH", drawn 75; 3 T16, T8 at 8 per m). The detail's 442 cm outer diameter
   equals the plan's inner circle (4.422 m), not its outer one (4.822 m). The 6 curved bands the engine already bound to
   B4 (not in any total) have the same conflict.

## Missing / for the Lead

- Owner question needed (not added: 5 questions already open): after Q-29 (domes become open skylights) does the ring
  beam round each dome opening stay, and with which section (B4 20 x 50 on the plan, or the dome detail's ring)?
- Designer RFIs: CB10 width (0.25 printed / 0.30 drawn); the 0.20 m strip north of B23 / B20 (concrete or not);
  the outer west strip and the two facade pieces on 1F; GF CB3 span 2 vs "B3 (With Stair)" (stair section, T-056).
- Engine task: planted-column split (item 2 above); binder miss on the GF B7 strip (trace with code).
- docs/CODEMAP.md lists research folders: this new folder makes the map stale; it could not be regenerated this run
  (execution refused). The verifier regenerates it with `python3 -I tools/codemap.py build`.
