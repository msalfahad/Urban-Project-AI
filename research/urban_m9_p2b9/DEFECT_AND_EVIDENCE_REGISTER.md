# Defect and unresolved-evidence register (Phase 2B-9)

This register carries `research/urban_m9_p2b8/REMAINING_DEFECT_REGISTER.md` forward.

- **"Fixed in V2.8"** means corrected in ARCH_TAKEOFF_V2.8 (opt-in), with a test against hand truth or the
  independent reader.
- V1 – V2.7.1 keep every defect as found; they are frozen and byte-identical.

## 1. Closed or corrected in this phase

| id | Defect (as found) | Status | Evidence |
|---|---|---|---|
| D-P8-03 | a wall stretch with both faces drawn over less than 0.30 m is not in the wall run | **corrected description + fixed in V2.8**. Collinear stubs **were already counted** (merged face lines); only non-collinear returns / nibs and short curved stubs were lost. V2.8 measures them (RETURN_STUB / CURVED_STUB, 0.05–0.30 m) | example 3R 12.95 → 13.15 m; 4S +0.413333 m; reference plan +0.16854 m VERIFIED by the arc census |
| D-P8-06 | skirting / wall tile at a window cannot be decided without the sill | **fixed in V2.8 where the drawing gives the sill** (schedule / annotation / note); without it the threshold is a range, never certain | examples 1 / 1F / no-schedule; villa 7 / 7 rooms VERIFIED |
| D-C5 / D-04 | wall areas rest on synthetic heights | **fixed in V2.8 where the drawing carries the evidence** (sections, notes, schedules); the reference plan carries none, so it is unchanged there | heights proof, 15 tests |
| sill clip (V2.2 – V2.7.1, by design) | a window is deducted at min(h, H) with no sill (`WINDOW_POSITION_ASSUMED`): it over-deducts where the head rises above the band | **fixed in V2.8** when the sill is established: w × (min(head, H) − max(sill, 0)) | `test_a_window_is_deducted_inside_each_band_only` |
| (V2.7.1) | window reveals BLOCKED_RFI | **fixed in V2.8**: measured depth, PROVISIONAL | 0.39 / 0.60 / 0.53 m² |
| (V2.7.1) | a room whose label lies in no closed space disappears silently | **V2.8 reports it** (ROOM_LABEL_NOT_IN_A_CLOSED_SPACE); open areas (garden, roof, pool, void) reported apart | example 4S; reference plan: 0 lost rooms, 11 open-area labels |

## 2. Found in Phase 2B-9

| id | Defect | Class | Found by | Status / proposed fix | Effect on the reference plan |
|---|---|---|---|---|---|
| **D-P9-01** | curved glazing alone, with no wall gap, is not read as a window: the room it bounds is not closed and is in no quantity | RECOGNITION | example 4S | **open**: infer a WINDOW role for a glazing arc concentric with a wall arc pair (needs an adversarial test set) | the reference plan's rooms close; no loss seen |
| **D-P9-02** | with roles declared, a curved window is closed at its glazing line: the floor and ceiling take the 0.438423 m² strip between the face and the glazing (7.507006 instead of 7.068583 m²), and the wall finish becomes a range | GEOMETRY | example 4S | **open**: close a curved opening on the room face, as straight ones are | not seen |
| **D-P9-03** | the room lexicon reads the Arabic phrase for "swimming pool" as BATHROOM (it contains the word for bath) | LEXICON | the lost-label finding on the reference plan | **fixed for the V2.8 finding** (open-area phrases first); the lexicon itself is unchanged because frozen methods read it | the label lies outside every room: no quantity effect |
| **D-P9-04** | the zone-bounded ground-floor space (a drawn zone line, 1.256 m, on a non-wall layer) cannot be verified: closed by that line, read by its own handle, the reader's face is 3.832 m² against the engine's 4.731 m² (0.899 m² unexplained, probably a recess whose mouth the reader's gap rule closes) | VERIFICATION GAP | independent verification | **open**: a cell-by-cell comparison; until then its 13 differences (V2.6 → V2.7.1) stay EXPLAINED_UNVERIFIED | 13 of the 23 unverified differences |
| D-V28-draft-01 | **V2.8 draft** subtracted every window threshold from the certain skirting, though F-17 had already moved those edges to its range: 30.75 m removed twice on the reference plan | DOUBLE COUNT | the before / after check | **fixed before release**: edge by edge against the F-17 reading | 0 (was −30.75 m) |
| D-V28-draft-02 | **V2.8 draft** asked for a wall-tile height in dry rooms and in wet rooms whose owner full height was already resolved | REPORT NOISE | the missing-evidence report | **fixed** | — |
| D-V28-draft-03 | **V2.8 draft** took the sill from a schedule row whose width is not the window's | EVIDENCE | adversarial example | **fixed**: neither height nor sill from such a row | — |

## 3. Limitations recorded

| id | Limitation |
|---|---|
| L-P9-01 | a schedule sheet turned on the drawing is not read (SCHEDULE_HEADER_NOT_READ): openings held, nothing invented |
| L-P9-02 | elevation views are read only for their level texts; window heights / sills are not read from elevation geometry (the reference plan's arched elevations would be ambiguous) |
| L-P9-03 | a metres drawing whose only closed rectangles are sheet frames is refused at admission (UNITS_CONTRADICTED) until a reviewer confirms `--units m`: correct, recorded |
| L-P9-04 | wall stubs under 0.05 m are treated as drafting artefacts (stated convention; the reference plan has one, 0.0414 m) |
| L-P9-05 | masonry by thickness stays BLOCKED: the block height (T.O.S. to soffit / beam) and the material are not read |

## 4. Tooling (audit side) found and fixed during the phase

| id | Defect | Fix |
|---|---|---|
| T-P9-01 | the new straight-return census read wall lines on section and elevation sheets (6 false candidates) | read only inside the plan regions |
| T-P9-02 | a column with a wall nib above it looked like a 0.30 m return | stretches whose middle lies in a column outline are excluded (listed) |
| T-P9-03 | a verifier run without `--layer-roles` on a plan with project layer names reads no wall lines (an empty census contradicts a real stub) | operational: pass the run's declared roles; recorded in the verification results |
| T-P9-04 | the engine's source ids carry decimal entity handles; the reader's are hexadecimal | converted where the verifier matches entities |

## 5. Still open from earlier phases

| id | Status |
|---|---|
| L-P8-01 | a WC-sized chair touching a back on the wall face reads as a WC outline: open (strict xfail) |
| D-P8-05 | a face with a symbol-less gap has no independent check for plaster / paint / tile (skirting under unknown sills is now checked: P − every gap) |
| O-P8-01, O-P8-02 | by design / input (door class by space type; ceiling type PROVISIONAL) |
| D-C2 / D-C2b, D-C3, D-P6-03 | open |
| D-16, D-17, kitchen membrane, junction details | owner decisions |
| G-* | catalogue gaps (see `BOQ_CAPABILITY_GAP_AUDIT.md`) |

## 6. The reference plan's missing height evidence (aggregates)

This is from `MISSING_HEIGHT_EVIDENCE.json` of the V2.8 runs. Each item names what is needed.

| Item | Mode A (project facts used) | Mode U (no facts) | What the owner must supply |
|---|---|---|---|
| room plaster height | 25 rooms (facts, not drawing) | 25 BLOCKED | a section per floor with the structural soffit (U/S SLAB) on each floor's band |
| room paint height | 25 rooms (facts) | 25 BLOCKED | the finished ceiling level (F.C.L.) per floor, or a reflected ceiling plan |
| wet-room wall tile height | 14 wet rooms (facts) | 14 BLOCKED | F.C.L. (full height), or a printed tile height where lower |
| window height | 26 windows (facts) | 26 BLOCKED | a window schedule (mark, width, height, sill) with marks on the plan |
| window sill | 26 windows (none) | 26 BLOCKED | same |
| door height | 22 doors (facts) | 22 at the Urban default 2.20 m, labelled assumed | a door schedule, or heights printed by the doors |

No height for the reference plan was invented. Mode A shows these as PROJECT_RULE (the stated facts file) and lists
them, because a project fact is not drawing evidence. Both modes list 138 items (Mode A: 112 from facts, 26 blocked;
Mode U: 22 from the Urban default, 116 blocked).
