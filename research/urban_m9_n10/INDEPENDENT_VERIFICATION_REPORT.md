# Independent verification report (Phase N10)

## 1. The tools

`tools/indep_reader.py` is a second reading of the raw DXF with ezdxf, shapely and arithmetic only. It imports no engine module and reads no engine output.

`tools/arch_change_verify.py` compares two runs. It attributes every changed total to the correction records that explain it, then checks it against the reader.

Each difference gets one of four results:

- VERIFIED;
- EXPLAINED_UNVERIFIED;
- CONTRADICTED;
- UNEXPLAINED.

## 2. Added in N10

| Addition | What it reads |
|---|---|
| curved gaps (`Drawing.curved_gaps`) | jambed curved wall gaps from the arcs' own parameters; the glazing share; with `curved_closures` (opt-in), both faces closed and a glazed gap on a face read as a window of that face's arc |
| joined rooms | a room the run joined through clear passages: the union of the reader's faces inside the room polygon |
| zone-bounded rooms | the zone lines the run used, read by their handle (decimal in the run, hexadecimal in the reader), closing the reader's own face |
| INDEPENDENT_OPENING_COUNT | windows on the reader's face (straight symbols and glazed curved gaps) |
| INDEPENDENT_OUTLINE | the facade run: the exterior ring of the union of the reader's faces inside the floor's plan region that holds the most rooms; **not established unless it holds every room of the floor** |
| CURVED_OPENING, CURVED_GLAZING_LAYER, MASONRY_PANEL, FACADE scopes | which locations and items each new correction record explains |

The plan region and the room polygons only select which reader faces are compared; the values come from the drawing.

## 3. Results on the reference plan (Mode A, snapshot `n10_a`)

| Comparison | VERIFIED | EXPLAINED_UNVERIFIED | CONTRADICTED | UNEXPLAINED | Differences |
|---|---|---|---|---|---|
| V2.6 → V2.7.1 | **45** (was 32) | 10 | 0 | 0 | 55 |
| V2.7.1 → V2.8 | 1 | 0 | 0 | 0 | 1 |
| V2.8 → V2.9 | 5 | 14 | **1** | 0 | 20 |

**V2.8 → V2.9 in detail:**

- **VERIFIED:**
  - the window count (+1, INDEPENDENT_OPENING_COUNT);
  - plaster and paint +57.9478 m² (reader 57.94776 vs engine 57.947764);
  - skirting (reader 17.161159 vs engine 17.161172);
  - the 2F facade run (29.80 m, exact).
- **EXPLAINED_UNVERIFIED:**
  - the curved window's reveal: blocked, no value to check;
  - masonry panel and volume lines: held, no value; there is also no independent masonry reading (D-N10-03);
  - facade area, exterior finish and plinth lines: held, no value;
  - the GF facade run: the reader's outline holds 15 of 21 rooms, because a glazed opening wider than its 2.60 m closure limit leaks (D-N10-02).
- **CONTRADICTED:** the 1F facade run, reader 63.008863 m vs engine 63.168865 m (+0.16 m, 0.25 %).
  - Cause: the engine walks the 0.08 m-deep recess of a window that the opening census did not detect (window frame lines beside a column). The reader closes the gap at the face line, which is what the facade convention asks for.
  - This is an engine defect (D-N10-01). The difference is reported, not tolerated away.

## 4. Synthetic verification (tests)

| Test | Result |
|---|---|
| example 4S, V2.8 → V2.9 | floor change 7.507006 → 7.068583 m² VERIFIED (INDEPENDENT_FACE); 0 unexplained, 0 contradicted |
| reader's curved-gap census (window, splayed, passage) | inner arc 4.312389 / 1.00 m, glazing share 1.0 / 0.0 |
| reader closes the curved window on the room face | face 7.068583 m², perimeter 10.712389 m; openings DOOR 1.00 + WINDOW 4.312389 m |
| facade box, V2.8 → V2.9 | facade run VERIFIED by INDEPENDENT_OUTLINE (15.60 m) |

## 5. What is still not independently checked

- masonry (no reader-side wall-mass census);
- facade area (no value on the real plans);
- formwork, excavation and rebar: checked against the synthetic design spec and by conservation with route G's own volumes, not against a second reading of the drawing;
- symbol-less gaps on a face: plaster, paint and tile (D-P8-05).
