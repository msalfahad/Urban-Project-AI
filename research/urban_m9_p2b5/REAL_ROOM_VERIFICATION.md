# Stage C - real rooms verified independently (reference plan, aggregates only)

Five rooms of the private reference plan were measured independently of the engine. They were then taken through
the owner rules to every finish quantity and compared with the engine's BOQ lines (ARCH_TAKEOFF_V2.5, Mode A; V2.6 as
committed in Stage B gives the same lines; the Stage D door correction of V2.6 and its re-score are in §7). Per-room sheets, coordinates and room ids stay in the private work area. This page gives
anonymised rooms (R-A to R-E) and relative figures only.

## 1. Independence, and what still depends on the engine

| step | source | engine involvement |
|---|---|---|
| read the drawing | ezdxf, read-only, never saved | none (the engine has its own reader) |
| room faces | wall-face linework (wall and column layers) noded and polygonised with shapely; doorway and window gaps closed by an own rule: a gap of 0.30 - 2.60 m between collinear face segments, not closed where a parallel face runs on behind it (a column standing proud of the wall) | none |
| seed of each room | the raw insertion point of its room-name text | none |
| openings | gap closures typed DOOR by a raw door arc (radius ~ the gap, centre at a jamb; OCS arcs of mirrored blocks transformed to world), WINDOW by window-layer lines | none |
| second check | the designer's DIMENSION entities around each room | none |
| splayed room (R-E) | read by hand from the raw wall-face end points (exact coordinates) | none |
| which engine room to compare with | the engine room containing the seed | **yes - pairing only** |
| heights | the project facts file (synthetic test heights: finish 3.00, wall tile 2.40, door 2.10, window 1.50 m) | the same stated input for both sides; heights are **not verified** here |
| rules | the owner registry 1.1.0 and the owner library (UP-WET-001, UP-FIN-WALL-001, UP-FIN-PAINT-001, UP-CER-004, UP-SKIRT-001, UP-THR-001, UP-WP-003, UP-WP-DOOR-001) | none |

**Sealed benchmark.** The sealed benchmark was not opened, read or used. Nothing was tuned against it, and its
evaluation status is unchanged. The formal blind evaluation was not started.

## 2. The rooms

| room | kind | why chosen |
|---|---|---|
| R-A | kitchen with its entry recess (no wall between them) | wet, an attached area, an external door |
| R-B | bathroom | wet, simple rectangle, the reference case |
| R-C | laundry with a doorless lobby that also serves a bathroom | wet, attached area, two doors |
| R-D | master bedroom | dry, two doors, wide glazing, pilasters |
| R-E | W.C. with two splayed (45-degree) walls | wet, non-orthogonal geometry |

## 3. Results

Every quantity that applies to each room (61 checks: the wet-only quantities in the four wet rooms), plus the 5
wet-room doorway thresholds: 66 checks.

| quantity | checks | pass | fail | what fails |
|---|---|---|---|---|
| floor area | 5 | 5 | 0 | - (engine and raw faces agree to 0.02 cm2; every principal span is confirmed by the designer's dimensions) |
| ceiling area | 5 | 5 | 0 | - |
| perimeter | 5 | 5 | 0 | - |
| windows (count) | 5 | 5 | 0 | - |
| doors released | 5 | 4 | 1 | R-C: a drawn bathroom door is held PROVISIONAL (not released) |
| skirting released / range | 10 | 8 | 2 | R-C (the same door) |
| internal plaster | 5 | 4 | 1 | R-C (the same door) |
| wall porcelain | 4 | 3 | 1 | R-C (the same door) |
| paint | 5 | 5 | 0 | wet rooms: BLOCKED by rule (the band above an explicit 2.40 m tile is a question), as expected |
| waterproofing floor | 4 | 4 | 0 | - |
| waterproofing upturn | 4 | 3 | 1 | R-C (the same door) |
| waterproofing doorway continuation | 4 | 2 | 2 | R-C (opening width), R-E (no doorway line at the splayed wall) |
| marble thresholds | 5 | 2 | 3 | withheld: two STRIP_NOT_ATTRIBUTED, one with no strip line |
| **all** | **66** | **55** | **11** | **two causes (D-C1, D-C2)** |

*Corrected in Stage D: the total line first read 70 / 58 / 12, an addition slip; the rows above (and the stored
aggregate of the comparison script) were always 66 / 55 / 11.*

Floor, ceiling and perimeter are exact in all five rooms, including the splayed W.C. and the two attached areas: the
recess and the lobby add up to the engine's areas to the millimetre.

## 4. Discrepancy register (ranked by BOQ impact)

| id | discrepancy | cause | BOQ impact (sample) | class |
|---|---|---|---|---|
| D-C1 | A drawn door (leaf + 90-degree swing, the standard door block, mirrored) between R-C's lobby and a bathroom is read by the room / opening model as a **1.02 m PASSAGE of unknown height**. The door schedule holds the same opening as a 0.80 m door, PROVISIONAL and not released. *Refined in Stage D (§7): of the three bathroom door blocks near passages on the plan, only this one is a door drawn two ways at one opening; the other two close their own doorways next to a passage and are correctly separate doors* | the leaf-ray closure (0.80 m) lies inside the band opening (1.023 m): the two views of one opening are not reconciled | R-C: plaster -2.0 %, wall porcelain -1.1 %, skirting -0.5 %, upturn -0.5 %, doorway waterproofing +11 %; one door not released; that doorway's marble threshold missing. Over the sample: plaster -0.5 %, wall porcelain -0.4 % | ENGINE DEFECT (recognition), conservative on doors (held, not lost) |
| D-C2 | 3 of 5 wet-room doorway thresholds are withheld: two strips are STRIP_NOT_ATTRIBUTED (in R-E two doors on the splayed wall share one merged strip); one has no strip line (the D-C1 door). R-E also has no doorway waterproofing line. *Refined in Stage G (§8): the merged strips are doorway faces running on past a jamb drawn only with the door symbol into a wall junction (split in V2.6, D-V26-07); R-E's doorway piece is in the BOQ, carried by the basin lobby beyond the door (C-07)* | strip attribution fails at a splayed wall and where an opening is read as a passage | marble thresholds: -49 % of the sample's threshold area (withheld with an RFI, not silently lost); doorway waterproofing -12 % | ENGINE DEFECT (attribution), conservative |
| D-C3 | R-C's doorless lobby (44 % of the room's area) is part of the laundry's face with **no attachment note**. R-A's recess, attached the same way, is flagged ATTACHED_THROUGH_OPEN_PASSAGE | the lobby and the laundry form one cell (no jambs at the joint), so the attachment path is not taken | none on geometry. The lobby takes the laundry's wet scope (waterproofing, full porcelain) without a visible note; if the owner treats it as a dry lobby, the wet items fall by that share | VISIBILITY / SCOPE (owner review) |
| D-C4 | Wet rooms with a 2.40 m tile below a 3.00 m finish height keep a released skirting (UP-CER-004's exception), while the program states "no skirting in wet rooms" | rule conflict between the owner library's exception and the program statement | about 41 lm of skirting in the four wet rooms of the sample | RULE CONFLICT (owner decision) |
| D-C5 | Mode A heights are synthetic test parameters. The door height 2.10 m differs from the owner reference 2.20 m (UP-DOOR-HGT-001), so door-area deductions use 2.10 | input, not engine | every wall-area line depends on heights that are not project values | INPUT (project values needed before release) |

## 5. Error propagation to BOQ lines

| BOQ line family | effect of D-C1 / D-C2 | direction |
|---|---|---|
| FIN.FLOOR.*, FIN.CEILING, FIN.WP.FLOOR | none | - |
| FIN.PLASTER, FIN.WALL.TILE | the passage piece is deducted to the full height (its height is not established) instead of the door height | under-measured by the excess deduction |
| FIN.SKIRTING | the opening (1.02 m) is wider than the door (0.80 m) | under-measured |
| FIN.WP.WALL_UPTURN | same | under-measured |
| FIN.WP.DOORWAY | the width is 1.02 m instead of 0.80 m (R-C); the line is missing at the splayed wall (R-E) | over (R-C) / under (R-E) |
| FIN.MARBLE.THRESHOLD | withheld for 3 of 5 doorways | under, with RFI |
| DOOR.INTERNAL.PVC | the door is held provisional | under in the released count, visible in the schedule |
| door feasibility (UP-DOOR-OPEN-002) | none: the three bathroom doors are in the feasibility view from the door schedule (0.80 m CAD openings, 0.70 m available nominal, ENLARGEMENT_REQUIRED 0.20 m for the owner's 0.90 m bathroom door), stated UNRESOLVED (insufficient drawing evidence) | reported, not released |

## 6. What this does and does not show

- Plan geometry is right in every room tested, including the non-orthogonal one and the attached areas.
- The quantity errors found all come from **opening recognition and doorway-strip attribution**, not from areas or
  rules. They are conservative: held, withheld or flagged, never silently invented. One case (D-C3) is not flagged.
- Wall quantities are verified only for the formula and the openings, not for the heights (synthetic).
- Five rooms are a sample, not a census. A door-block census found 3 of 27 door blocks next to openings the engine
  reads as passages; Stage D's geometry check (§7) shows only one of them is the D-C1 pattern.

Next steps: attribute doorway strips at splayed walls; flag a doorless cell merged into a wet room; settle the width
of the reconciled R-C door (1.023 m jamb to jamb against the 0.80 m leaf closure: a drawing question); owner
decisions on D-C3 and D-C4. The opening / door-schedule reconciliation is done in ARCH_TAKEOFF_V2.6 (§7).

## 7. Stage D follow-up: D-C1 diagnosed and reconciled in ARCH_TAKEOFF_V2.6

An instrumented private run measured, for each of the three door blocks, why the strict door fit rejects it and
where its leaf-ray closure lies (aggregates only):

| door block | strict fit fails on | leaf closure | the passage it stands near | reading |
|---|---|---|---|---|
| 1 | the leaf (0.69 m) is 67 % of the 1.023 m opening | 0.80 m, parallel to the passage's wall, inside its gap, 0.13 m from its centre | the same opening | **one opening drawn two ways** (D-C1) |
| 2 | the hinge is 0.35 m from the passage's jamb | 0.80 m, perpendicular to the passage's wall, about 1.0 m away | a different, doorless opening | a separate door into an inner room - confirmed by the independent reader, which closes a 0.80 m DOOR gap there and a 0.90 m OPENING at the passage |
| 3 | the hinge is 0.70 m from the passage's jamb, and the leaf fit | 0.80 m, perpendicular, about 1.3 m away | a different opening | a separate door |

The opt-in correction D-V26-06 (`engine/source/arch_rooms.py` `closure_in_passage`, `match_swings_review`):

- **Passage whose gap holds a door's leaf closure.** The passage becomes a DOOR, held from every released total
  (DOOR_SYMBOL_FIT_REVIEW). Its record carries both widths, and the door's separate closure is dropped.
- **Swing that closes no gap.** It may still fit a passage within review limits: a hinge up to 0.45 m from a
  jamb, or a leaf down to 60 % of the width. That passage then becomes a held DOOR. Beyond those limits it only
  gets a note.
- **Swing that closes its own doorway** is never moved. A first version without this guard merged two cells of a
  bathroom; the independent reader showed that was wrong, so the guard was added before any commit.

On the reference plan, V2.6 now changes exactly one opening: door 1. Room areas are unchanged. The Stage C checks
re-scored against V2.6:

| | checks | fail | changes |
|---|---|---|---|
| V2.5 | 66 | 11 | - |
| V2.6 | 66 | 10 | R-C doors 1 → 2 (pass); plaster error −0.94 → −0.15 m2; wall porcelain error −0.42 → −0.15 m2 |

The remaining R-C differences come from the width: the engine's 1.023 m against the 0.80 m leaf closure, a
drawing question now recorded on the held door. In the whole plan's BOQ, one doorway strip moves from porcelain to
a marble threshold (0.15 m2; floor area conserved) and door jamb plaster adds 0.81 m2 (PROVISIONAL). V1 - V2.5
outputs are byte-identical (968 files).

## 8. Stage G follow-up: D-C2 diagnosed and split in ARCH_TAKEOFF_V2.6 (D-V26-07)

An instrumented private run read every door / passage doorway face the strip register withholds, and every doorway
piece of a door closed by its leaf (aggregates only).

**The pattern.** A door's jamb is drawn only with the door symbol (the door layer), not on the wall layer. The
wall-face piece beside it is shorter than the band census's 100 mm minimum (a 70 - 77 mm return), and beyond it is a
junction with a perpendicular wall. No wall cap seals the wall body there, so the doorway face runs on past the jamb
into 0.20 - 0.27 m of wall. Where two doors share a wall with a partition meeting it between them, one face holds both
doors and the 0.24 m of wall between them (the sample's W.C. and its neighbour). The strip then fails the opening-box
check, and its threshold is withheld. A door that is not a band opening (closed by its leaf and the wall's other face)
takes the whole face as its doorway waterproofing piece.

**The rule** (D-V26-07, `engine/source/arch_completeness.py` `split_strips`, `closure_box`). A face is split at its
openings' boxes, or at the box between a leaf-closed door's two closures, only when its own boundary proves the
reading:

- its threshold / closure edges are both faces of its openings (2 x the sum of the widths);
- every other edge is a WALL line;
- it is no wider across than the wall;
- its openings lie on one wall line;
- it covers each box whole (to 1 mm).

The box takes the doorway's treatment (UP-THR-001, UP-WP-003) as any other doorway. The rest becomes a
WALL_BAND_REMAINDER strip (BLOCKED_RFI, no quantity). Floor areas, room areas and coverage do not change.

**On the reference plan:**

| | faces | outcome |
|---|---|---|
| band-opening faces split | 4 (5 doorways) | 4 marble thresholds of 0.12 m2 each, 1 doorway-strip porcelain of 0.135 m2; 0.14 m2 of wall left as 4 remainder strips |
| band-opening faces refused | 6 | wider across than the wall (the held two-way door's perpendicular wall cells, a garden passage), threshold edges not both faces of the opening |
| leaf-closed doorway pieces boxed | 2 of 4 in wet rooms | doorway waterproofing −0.0715 m2 (each face held 0.034 / 0.038 m2 of wall) |
| leaf-closed pieces refused | 2 | an irregular face wider than the wall; a face bounded by a column |

**Independent check.** A raw-line reading (ezdxf, unrounded coordinates, every layer, never the engine's reader;
`indep_jambs`, private) finds the lines crossing the wall at full thickness. In all six boxed doorways these are the
door symbol's own jamb and frame lines (layer D): spans of 0.800 m (five) and 0.900 m (one), frames 50 mm. The
engine's boxes agree to 0.1 mm, except one leaf-closed box that is 0.4 % small: its width comes from the leaf
closure, 0.797 m. The remainders agree with the raw wall stubs to 0.1 mm. No wall-layer jamb line exists at any of
them.

The Stage C automated reader mis-reads the 45-degree W.C. pair: its 1 mm snap separates the 27 / 61 mm wall pieces
from their face line (E-05). Read by hand from the raw coordinates, the pair is two 0.80 m doors and 0.238 m of wall.

**Stage C re-scored:**

| | checks | fail | thresholds pass | sample threshold area |
|---|---|---|---|---|
| V2.5 | 66 | 11 | 2 of 5 | −49 % (withheld) |
| V2.6 with D-V26-06 | 66 | 10 | 2 of 5 | −28 % |
| V2.6 with D-V26-06 and D-V26-07 | 66 | **8** | **4 of 5** | **+4.5 %** (the two-way door's width) |

The comparison script had a scoring fault, now fixed. When one pseudo room carried a threshold line and a left-over
strip line, it scored whichever came last. It now scores the threshold line. No count changes in V2.5 or in V2.6
before the split (C-06).

**What is left in the sample** (8 checks, two causes):

1. **The held two-way door's width (R-C: seven checks).** The raw reading settles it. The door symbol's jamb lines
   are 0.80 m apart. Of the rest of the 1.023 m wall gap, 73 mm is a wall return with both faces drawn and 150 mm is
   the crossing of a perpendicular wall. The drawing answers the width question; it is not an owner decision
   (`OWNER_DECISIONS.md` 6 is withdrawn). Applying it means narrowing the opening to the symbol's jambs and closing the
   rest as wall inside the face partition. That changes the room's boundary, so it was not done in this program
   (`ROADMAP.md` 1).
2. **R-E's doorway waterproofing (one check).** The piece is in the BOQ once, at the right size (0.12 m2). It is
   carried by the space beyond the door, a lobby with three wash basins that the engine types wet from its fixtures
   (ROOM_TYPE_FROM_FIXTURES, review). UP-WP-003 counts a doorway piece once, so the room that carries it depends on
   whether a basin lobby is a wet area. The check stays FAIL per room; at the opening it is right. The statement in
   §3 that R-E has no doorway waterproofing line is corrected (C-07). Whether a basin lobby is a wet area is an
   owner decision (`OWNER_DECISIONS.md` 11).
