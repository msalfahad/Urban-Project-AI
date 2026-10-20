# T-014 Facade gaps: window recesses on the outline (D-N10-01) and wide glazed gaps for the independent reading (D-N10-02)

Worker 2, 2026-10-20. Gate 1 (geometry integrity). New check piece `engine/source/facade_gap_closure.py`
(FACADE_GAP_CLOSURE_V1), NOT wired: no released quantity moves. Rules: UP-FACADE-001, UP-WALL-GEOM-001,
UP-QTY-STATUS-001, owner Q-25 answer (no assumed gap limit; each closure listed with its width). Q-07 (facade height
slab to slab) is not touched: this piece works on the run in metres only; facade m2 stays HELD (height, T-031).

## What the engine gives (Alsenan, development villa; Mode A as T-016a: S2 facts, layer roles 1 / D / W / S-COL.BON)

| Floor | Released run (V2.9, same in V2.10 - V2.12) | FACADE_GAP_CLOSURE_V1 | Hand | Independent outline | Verdict proposal |
|---|---|---|---|---|---|
| GF | 98.886694 m | 98.886694 m (1 corner notch KEPT) | notch 0.05 + 0.08 + 0.05 m read by hand; rest not hand-read | 98.887038 m, 21 / 21 rooms, plate 284.146302 vs engine 284.146505 m2 (was: NOT established, 15 / 21 rooms) | ENGINE_RIGHT (+0.000344 m, 0.0003 %, curve flattening) |
| 1F | 63.168865 m | 63.008865 m (-0.160 m, -0.25 %) | 63.008865 m (T-016a) | 63.008863 m, 13 / 13 rooms; plate +0.0374 m2 = 0.4673 x 0.08 (the recess) | engine CONTRADICTED (D-N10-01), the new piece = hand |
| 2F | 29.800 m | 29.800 m (no recess) | 29.800 m (T-016a) | 29.800 m, 4 / 4 rooms | VERIFIED |

Freelancer: there is no facade-run row to compare. His exterior plaster is taken in m2 per elevation (width x height
per facade), so the run in metres is not comparable; the facade m2 waits on the slab-to-slab heights (Q-07, T-031).

## 1. D-N10-01 on the first floor: a window beside a column that the census missed

The 1F outline steps 0.080 m in, runs 0.4673 m along window frame lines and steps 0.080 m out (one side a wall cap,
the other the column side). The wall is 0.20 m thick (wall band thickness from the plan); the frame sits in its inner
0.12 m and the outer 0.08 m is open. Glazing covers the whole 0.4673 m mouth, the step (0.080 m) is less than its wall,
and no opening threshold of the engine lies in it, so FACADE_GAP_CLOSURE_V1 closes it on the face line:
0.6273 - 0.4673 = 0.160 m off the run, 63.168865 -> 63.008865 m, exactly the hand figure of T-016a and the
independent reader (63.008863 m). The same step is listed as a window opening the census did not detect, 0.4673 m wide
between the wall cap and the column, beside_column = true (the window's own width, its schedule and height are not
established here).

The second step found on 1F (3.53 m walked against a 3.06 m chord, 0.22 m deep) is the curved window band of the
master bedroom: the engine already measures that opening (its threshold arc lies in the step), so it is KEPT as drawn.

## 2. The GF 0.10 m "pocket" (T-016a, UNRESOLVED): not a window recess, the run is right

At the north end of the curved pool glazing, the outline walks 0.05 m down the column's side, 0.08 m along the wall's
face and 0.05 m along the first glass frame line, 0.18 m in all; a straight line across the mouth is 0.08 m (0.10 m
less). Read by hand from the drawing: the face line of that column continues past the notch only as the frame's head
line (0.12 m, behind the glass), not as a wall face; there is no glass across the notch mouth. Its three sides are
exterior faces (column, wall end, frame end). UP-FACADE-001 measures the exterior face and closes only openings in a
wall; this is not an opening in a wall. So the piece classifies it CORNER_NOTCH, KEPT, and the GF run stays 98.886694 m.
The independent outline (below) walks the same notch and gives 98.887038 m. If glass were drawn across such a mouth the
piece would HOLD the run as a range (closed .. walked), never pick one.

## 3. D-N10-02: the ground floor read independently

The independent reader (tools/indep_reader.py, unchanged) closes only 0.30 - 2.60 m wall gaps, so the GF outline leaked
through two glazed openings: the 6.332 m window on the east wall and the curved pool glazing (4.90 m between the column
and the wall end). Its outline held 15 of 21 rooms (112.87 m2). Two new independent closures, both read from the drawing,
never from the engine and never from a width limit:
- glazed_gap_closures: a gap of any width between collinear wall pieces is closed on both faces when jamb lines cross
  the wall at both ends (giving its thickness) and window pieces inside the wall band cover it jamb to jamb. The 6.332 m
  east window: inner face CLOSED_GLAZED (wall 0.20 m, glazing over 100 %); outer face HELD (glazing pieces reach past
  the band). Every other gap over 2.60 m on GF / 1F / 2F stays HELD (no glazing, part glazed, or no jamb pair): 14 + 10 +
  1 gaps, nothing closed on width alone.
- glass_chain_closures: a chain of window pieces whose two ends lie on wall or column lines is a glass wall. The pool
  glazing gives two such chains, 6.994658 m (the outermost frame line, the one the engine walks: 0.1935 + 6.6577 arc
  + 0.1435) and 6.925124 m (the innermost); the outline takes the outermost.
With both, the GF independent outline holds 21 / 21 rooms, plate 284.146302 m2 (engine 284.146505), run 98.887038 m
against the engine's 98.886694 m: the GF facade run is now independently established (was EXPLAINED_UNVERIFIED).
1F and 2F are unchanged by the new closures (1F reader with curved closures 63.008863 m, 13 / 13; 2F 29.800 m).

## Synthetic hand fixtures (not Alsenan), tests/t014_facade_gaps (39 tests)

- 10.00 x 8.00 m with a 1.50 m window step 0.20 m deep in a 0.20 m wall: walked 36.40 m, closed 36.00 m, one missed
  window 1.50 m; started at another edge, reversed, mirrored, rotated 30 / -121 / 90 deg; through the engine's own
  topology and arch_v29 outline (the engine walks 36.40 m) in metres and in millimetres (unit 0.001), mirrored + 30 deg.
- no glazing -> HELD 36.00 .. 36.40 m; glazing 1.00 of 1.50 m -> HELD; glazing drawn apart inside the step -> closed;
  a 1.50 m deep porch -> KEPT 39.00 m; wall thickness unknown -> HELD; a measured threshold in the step -> KEPT; one
  jamb a column -> beside_column; two steps, one glazed -> HELD 36.00 .. 36.40 m of 36.80 walked; a pilaster standing
  out -> not a recess; a curved edge never serves as a face line; an empty outline -> NO_OUTLINE, no value (never 0).
- corner notch 0.08 x 0.05 m (15.66 m walked): KEPT; glass across its mouth -> HELD 15.56 .. 15.66 m.
- wall band with a 3.00 m glazed gap -> CLOSED on both faces (6.00 m of closure), turned 30 / -121 deg and mirrored;
  no glazing, part glazing, a missing jamb, glazing leaving the band -> HELD; a 5.20 m glazed gap (over the old
  2.60 m reader limit) -> CLOSED; a glass bay of radius 2.00 m (pi x 2 = 6.283185 m) joining two walls -> closed with
  that length; the same bay stopping 0.04 m short of a wall -> open, never extended.

## What is learned / what is missing

- A facade "pocket" is two different things: a step into a wall opening whose frame sits back (close it at the face
  line when glass fills its mouth), and a notch at a corner where glass meets a column (real exterior faces, keep it).
  The test is whether the face line resumes on the far side of the mouth.
- The reader's 2.60 m closure limit was the only thing leaving GF unverified; reading the glazing (any width, with jamb
  and band evidence) settles it without a width limit.
- Missing: wiring FACADE_GAP_CLOSURE_V1 into a method version (a tools/urban_boq_m9.py change, outside this task's
  files) so the released 1F run becomes 63.008865 m; adding the missed 1F window (0.4673 m) to the opening census
  needs its schedule / height (not read here). Facade m2 stays HELD (Q-07 heights, T-031).

Reproduce: `python3 -I research/agents_t014/alsenan_facade_check.py <P7757 plan DXF> <out dir> research/urban_m9_s2/SYNTHETIC_FACTS_S2.json`
(the DXF from Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, sha256 of the DXF ab54dd55...; kept outside
the repository). It prints lengths, room counts and closure widths only.
