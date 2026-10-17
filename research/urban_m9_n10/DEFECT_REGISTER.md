# Defect register (Phase N10)

This register carries `research/urban_m9_p2b9/DEFECT_AND_EVIDENCE_REGISTER.md` forward.

- **"Fixed in V2.9"** means corrected in ARCH_TAKEOFF_V2.9 (opt-in), with a test against hand truth or the
  independent reader.
- V1 – V2.8 keep every defect as found. They are frozen and byte-identical: see `REGRESSION_AND_FROZEN_EVIDENCE.md`.
- A status is as stated here. `tools/codemap.py` reads this register as the newest one.

## 1. Closed, corrected or addressed in this phase

| id | Defect (as found) | Status | Evidence |
|---|---|---|---|
| D-P9-01 | curved glazing alone, with no wall gap, is not read as a window: the room it bounds is not closed and is in no quantity | **fixed in V2.9**. A glazing layer is inferred only when all three hold: it is an OTHER layer (a declared role is never changed); a concentric arc covers at least half of a jambed curved wall gap; and at least half of its linework lies in wall gaps | example 4S with roles inferred: floor 7.068583 m², the same as with roles declared (`tests/m9_n10/test_n10_curved_openings.py`) |
| D-P9-02 | with roles declared, a curved window is closed at its glazing line: the floor and ceiling take the 0.438423 m² strip between the face and the glazing | **fixed in V2.9** (UP-OPEN-CURVED-001). The opening is closed on both wall faces by arcs; the room ends at its own face; the strip is a reveal / sill strip, measured radially | floor 7.507006 → 7.068583 m², VERIFIED by INDEPENDENT_FACE (`test_n10_indep_curved.py`) |
| D-P9-04 | the zone-bounded ground-floor space cannot be verified (the reader's face is 0.899 m² smaller) | **resolved** (verification). Root cause: the reader's gap rule split two recesses (0.2617 + 0.6368 m²) off the space. The verifier now unions the reader's faces inside the room and reads zone lines by their handle; the union equals the engine's polygon (symmetric difference 0.0) | V2.6 → V2.7.1 re-run: 45 VERIFIED, 10 EXPLAINED_UNVERIFIED, 0 CONTRADICTED (was 32 / 55 verified) |
| L-P9-05 | masonry by thickness stays BLOCKED: the block height and the material are not read | **open, partly addressed in V2.9** (UP-MAS-HEIGHT-001). Panel area and volume by thickness from the section's T.O.S. to the soffit, or from stated facts. The panel is held at its upper bound without beam evidence. MAS.BLOCK still needs the material | hand truth: 43.26 m² / 8.652 m³; range 35.86 – 43.26 m² with a beam bottom (`test_n10_masonry.py`) |
| D-N10-00 | the session guard failed at the baseline 504b56a: `tools/codemap.py` named the freeze verifier | **fixed** (dec6766): the command lives in `tools/routing_topics.json` | the one new baseline failure (`FULL_SUITE_COMPARISON.md`) |

## 2. Found in Phase N10

| id | Defect | Class | Found by | Status / proposed fix | Effect on the reference plan |
|---|---|---|---|---|---|
| **D-N10-01** | the facade run walks the recess of a window that the opening census did not detect (glazing frame lines beside a column): the recess's two 0.08 m returns are in the run; the reader closes the gap at the face line | GEOMETRY | INDEPENDENT_OUTLINE | **open**: close a glazing-lined gap on the outline at the face line, or detect the window beside the column | 1F facade run +0.16 m (0.25 %): CONTRADICTED, reported |
| **D-N10-02** | the independent reader closes only 0.30 – 2.60 m wall gaps: a wider glazed opening leaks, so a floor with one cannot be read independently | VERIFICATION GAP | INDEPENDENT_OUTLINE | **open**: reader closures for wide glazed openings | GF facade run EXPLAINED_UNVERIFIED (the reader's outline holds 15 of 21 rooms) |
| **D-N10-03** | there is no independent masonry reading: masonry differences are explained by the MASONRY_PANEL record but not verified | VERIFICATION GAP | verifier | **open**: a reader-side wall-mass census (plan area / t) | all masonry lines held on the reference plan; no verified change |
| **D-N10-04** | formwork column sides are an upper bound: which beams frame into each column is not in the route G register | DATA | structural tests | **open**: carry beam-column adjacency in the register | column sides UPPER_BOUND on every run |
| **D-N10-05** | the new structural module `engine/source/struct_n10.py` names reinforcement (its rebar audit) but was not declared in the rebar product firewall registry. The targeted test runs did not include the static scan that enforces this | PROCESS | the full suite at 4b299ae (`test_every_rebar_module_in_engine_is_declared`, the one test that went from pass to fail) | **fixed** (24db651): declared as OTHER_REBAR_AWARE (stdlib only, writes no reinforcement quantity); reproduced first, folder 54 passed after | 0 (no quantity) |
| D-N10-draft-01 | **facade draft** counted networks made only of loose lines (zero plate) as exterior outlines | RECOGNITION | the reference plan | **fixed before commit**: counted apart as line networks | 0 |
| D-N10-draft-02 | **facade draft** drew curved edges of the outline ring from the arc's own parameter as an absolute angle | GEOMETRY | ring vs perimeter check | **fixed before commit** (the ring now equals the perimeter on all three floors) | 0 |
| D-N10-draft-03 | **verifier draft** compared the facade run against a reader face spanning all three floors | VERIFICATION | the reference plan | **fixed before commit**: faces inside the floor's plan region only; not established unless the outline holds every room | 0 |

## 3. Limitations recorded

| id | Limitation |
|---|---|
| L-N10-01 | a second exterior outline on a floor is reported as an RFI and never added (each reference-plan floor has a thin 10.84 m outline around 0.66 m², a drawing element on a wall layer) |
| L-N10-02 | facade: set-back floors' exposed slab edges and parapets are not separate items; the plinth below the lowest F.F.L. and the exterior finish are RFIs |
| L-N10-03 | excavation pits are not merged where neighbours overlap (pit positions are not in the register): a stated volume is an upper bound |
| L-N10-04 | `engine/source/struct_n10.py` writes its own files (FORMWORK.json, EXCAVATION.json, REBAR_AUDIT.json); its quantities are not yet lines of the BOQ workbook |
| L-N10-05 | a curved opening wider than half a turn, or one whose jamb lines are on a non-wall layer, is refused (listed with its reason, never guessed) |

## 4. Still open from earlier phases (restated, unchanged in N10)

| id | Status |
|---|---|
| L-P8-01 | open (strict xfail): a WC-sized chair touching a back on the wall face reads as a WC outline |
| D-P8-05 | open: a face with a symbol-less gap has no independent check for plaster / paint / tile |
| O-P8-01 | by design / input: door class by space type |
| O-P8-02 | by design / input: every ceiling line is PROVISIONAL (the ceiling type is not in a plan) |
| D-C2 / D-C2b | open: leaf-closed doorways (threshold withheld) |
| D-C3 | open: a doorless cell merged into a wet room takes the wet scope silently |
| D-P6-03 | open: a drain of column size still needs a second source |
| D-16, D-17 | owner decisions (kitchen membrane, junction details) |
| L-P9-01 | limitation: a schedule sheet turned on the drawing is not read |
| L-P9-02 | limitation: elevation views are read for their level texts only |
| L-P9-03 | limitation: a metres drawing whose only closed rectangles are sheet frames is refused at admission until confirmed |
| L-P9-04 | limitation: wall stubs under 0.05 m are treated as drafting artefacts |
