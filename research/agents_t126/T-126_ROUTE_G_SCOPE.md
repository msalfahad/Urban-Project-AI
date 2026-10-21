# T-126: route G scope - blinding by member family and the column pieces no upper slab plan draws

Worker 1 (lane S, structural), 2026-10-20. New piece `engine/source/route_g_scope_v1.py` (method ROUTE_G_SCOPE_V1),
not wired into any released method: route G (`generic_route.py`, frozen) and CONCRETE_LEDGER_V2 are read, never
edited. Lane I wires it into the one opt-in candidate (ARCH_TAKEOFF_V3.0 + route G). Development reference, not an
accuracy claim.

## Inputs (read in the session scratchpad, never committed)

| Input (Drive "Alsenan chalet project") | sha256 | Used for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179...38079 (= manifest, = T-044 / T-064 / T-100) | route G run B and the scope pass |
| T-100 hand takeoff (research/agents_t100, merged) | - | the hand truth per footing, per beam and per column storey |

Run (verifier can repeat it): `.venv/bin/python -I research/agents_t126/run_t126_scope.py <repo> <ST7757.dxf> <out.json>`:
route G with the V6 conventions and the typed profile (run B, T-036 / T-044), completeness on, then the scope pass.

## What the piece does

| Family | Before (route G) | Rule now (ROUTE_G_SCOPE_V1) |
|---|---|---|
| Column piece on a storey | counted when the column-plan mark is bound to an outline and the storey's roof-slab plan draws one there; a mark bound to NO outline counted on the schedule band alone (risk COLUMN_STOREY_PRESENCE_UNVERIFIED) | released only where the roof-slab plan of its storey draws an outline at the position. Position = column-plan outline; else the SAME mark's foundation-plan outline nearest the mark (<= 2.5 m, next one >= 0.5 m farther, not the outline of a bound occurrence); else one outline within reach at a section the schedule prints. Undrawn -> NOT_PRESENT with the sheet and the nearest outline; no position or no plan -> HELD (UNRESOLVED item, exposure 0 .. v), never released, never a silent 0 |
| Footing blinding | one released layer, every footing incl. one whose own concrete is in conflict | per footing: released only where the footing is; a footing in conflict / held (owner Q-31 C) keeps its blinding HELD, range larger candidate .. every candidate as its own pad |
| Ground-beam blinding | released, merged with the footing layer | HELD range while the footing-detail choice is open (owner Q-21 C): low = merged with the footing layer, high = its own layer at beam level (crossings once); released as one reading only when a caller passes the detail choice |
| Strap blinding | released inside the beam layer | HELD while no strap section prints a blinding (designer request); the quantity if blinded is the merged strip |

## Alsenan before / after (route G run B on this head, m3)

| Line | Before | After | Change | Status after | Hand (T-100) | Freelancer |
|---|---|---|---|---|---|---|
| columns GF | 20.250 | 20.250 | 0 | released 30 pieces | 20.250 | 17.438 (32 at 3.75 m) |
| columns 1F | 10.668 | 10.248 | -0.420 | released; NOT_PRESENT 1F C3 (one) | 10.248 | 7.728 (19 at 3.45 m) |
| columns 2F | 5.796 | 3.948 | -1.848 | released; NOT_PRESENT 2F C3 x2, C5, C8 | 3.948 | 3.381 (9 at 3.45 m) |
| columns total (above the necks) | 36.714 | **34.446** | **-2.268** | | **34.446** | 28.547 |
| necks (FOUNDATION) | 10.855 | 10.855 | 0 | as route (heights held downstream, Q-21 C) | - | - |
| blinding released | 22.155 | **15.179** | -6.976 (moved to HELD) | 25 footings | 15.179 | 47.055 (one plate) |
| blinding footing in conflict | (in 22.155: 0.480) | HELD 0.480 .. 0.590 | | Q-31 C | HELD 0.480 .. 0.590 | in his plate |
| blinding ground beams | (in 22.155) | HELD 5.724 .. 9.423 | | Q-21 C | HELD 5.534 .. 9.691 | in his plate |
| blinding straps | (in 22.155) | HELD 0.772 | | designer request | HELD 0.913 | in his plate |
| blinding total range | 22.155 | 22.155 .. 25.964 | | | 20.713 .. 26.373 | 47.055 |

Columns: the scope pass finds exactly the five pieces T-100 found by hand (sheet = the roof-slab plan of that storey;
nearest drawn outline 1.48 / 9.43 / 8.54 / 7.05 / 7.11 m): 1F C3 0.20 x 0.50 x 4.20 = 0.420; 2F C3, C3, C5 0.420 each,
C8 0.20 x 0.70 x 4.20 = 0.588; together 2.268. Every other unbound mark (C3 / C5 / C8 / C10 / C / C1 / C2 on the
storeys their plans draw) is anchored on the foundation plan to within 0.07 m of an outline on each plan, and the one
mark with no foundation outline (C11, GF only) is released by its printed section 0.25 x 1.10 drawn on the GF plan.
Second drawing: ST7757.pdf p.6 (second-floor roof slab, rendered at 60 / 250 dpi) covers only the water-tank /
stair core between the neighbour-side beams B15 and B7; the four 2F NOT_PRESENT pieces stand at about 12.6 m and
24.3 - 24.5 m from the street line, outside that core, and the C3 the piece keeps on 2F (about 17.0 m) is inside it.
Engine vs freelancer columns: 36.714 vs 28.547 (+28.6 %) before, 34.446 vs 28.547 (+5.899, +20.7 %) after; the rest
is the height basis (full storey interval vs his interval - 0.75; rule URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1,
task T-119) and his count slips (T-100 section 4).

Blinding: released 15.179 = hand 15.179 to the m2 (151.794 m2, FN / F9 overlap 0.336 m2 once). The ground-beam
range differs from the hand range by +0.190 (low, +3.4 %) and -0.268 (high, -2.8 %): route G's beam bands stop at the
column faces, so the neck footprints the hand reading deducts (-5.37 m2 from the gross strips) are already outside
the engine strips except their 0.10 m projections (0.649 m2, taken out of the own-layer reading); the rest is the
length basis (GB_LENGTH_BASIS, a second hold on this line) and the curved beams; straps 0.772 vs hand 0.913 (engine strap lengths 3.27 /
5.70 / 2.26 m against the hand clear lengths 3.259 / 4.55 / 2.294 m: the SB1 length differs; not traced here).

## Two methods side by side (owner management decision section 5)

| Item | Owner / Urban manual method (hand, T-100) | Drawing-derived (engine, this piece) | Difference explained |
|---|---|---|---|
| column presence | a column stands on a storey when its outline is drawn on that storey's roof-slab plan (read by eye) | the same test on the DXF frames, position from the column plan or the foundation-plan anchor | none: same 5 pieces |
| footing blinding | (L + 0.20)(W + 0.20) x 0.10 per footing, overlaps once | union of the same outlines | none |
| ground-beam blinding | 0.50 x drawn length per beam, crossings and neck footprints once; reading L / R | union of route G strips (band +- p); readings merged / own layer | length basis and neck footprints (above) |
| straps | (B + 0.20) x clear length | merged strip on the route's strap bands | SB1 length |

## Verdict proposals (for the checker)

- Columns 1F / 2F, the five NOT_PRESENT pieces: ENGINE_RIGHT after this piece (hand from the roof-slab plans p.5 / p.6,
  T-100); against the freelancer the remaining +5.899 m3 is RULE_DIFFERENCE (height basis), not this piece.
- Blinding released 15.179 vs freelancer 47.055 (-31.876, -67.7 %): RULE_DIFFERENCE. His 15.00 x 31.37 x 0.10 plate is
  drawn on no sheet; the slab-on-ground notes print compacted fill under the ground slab (T-100 P7). Never copied.
- Ground-beam and strap blinding: UNRESOLVED (held on owner Q-21 C and the designer request), shown as ranges.
- F10 blinding: HELD with its footing (owner Q-31 C), flagged for the final BOQ like the footing.

## Tests

`tests/t126_route_g_scope/` (synthetic villa SV-SCOPE, not a client project; 33 tests): every expected value is a hand
calculation in the module docstring; the same villa in mm, mirrored, rotated 90 degrees, in metres and mirrored +
rotated + metres; an ambiguous anchor, an anchor that a bound column already owns, a mark with no anchor and no
printed section (HELD), a storey with no slab plan (HELD), a route-held piece (unchanged), a route-absent piece
(listed), a planted column (untouched), two footings with overlapping projections, a two-label footing (HELD with its
range), crossing beams, a neck outline inside a beam strip (own layer only, 5 frames), a strap, unregistered plans, missing blinding thickness (no number), the detail choice given
(each reading released), no column plan (foundation occurrences checked), inputs not mutated, no project constants.

## What is missing

- C8 (column plan prints 30X80, schedule 30 x 90, T-100): a section conflict on every storey; this piece keeps the
  route's section (heights and sections are T-119), so it is not held here.
- The 8 footings drawn on the plot line (projection 1.89 m2 outside the plot) stay a case for the Lead (T-100).
- Ground-beam length basis and the neck-footprint deduction inside the beam layer: not decided here (held line).
- Not wired: lane I adds `measure` / `apply` to the V3.0 candidate after the checker merges this.
