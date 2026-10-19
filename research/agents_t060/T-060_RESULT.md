# T-060: concrete ledger V2 (strip guard + curved strips wired), measured on the development villa

Worker 1, 2026-10-19. Development reference, not an accuracy claim. New method version `CONCRETE_LEDGER_V2`
(`engine/source/concrete_ledger_v2.py`); no frozen file and no released method changed; nothing calls it except the
read-only runner `research/agents_t060/run_v2.py` and the tests `tests/t060_concrete_ledger_v2/`.

## What the version does

Runs on the frozen route-G result (completeness on, conventions V6). For every completeness finding whose frozen scope
items measure a band or a wall strip (BOUNDARY_WALL, POOL), it re-measures the finding's drawn faces:

- the group's own lines + the same-layer faces inside its box that the frozen ledger removed before grouping
  (EXPLAINED_BY_MEMBER, CONTEXT_OF_OTHER_SHEET) + rebuilt plot-outline edges (PLOT_EDGE refs);
- straight faces through `concrete_strip_guard.guard` (centre line, corners once, the part inside a drawn member
  footprint HELD STRIP_UNDER_MEMBER, faces with no partner HELD STRIP_FACE_UNPAIRED), arcs through
  `concrete_curved_strips.curved_strips`; members = the route's detected footings, columns, column boxes, bands and
  strap candidates, except schedule-sized footprints drawn round a mark (not drawn: listed, never used);
- closed loops of lines and arcs give the outer / inner plan areas exactly (chord polygon +- circular segments), a
  ring check (outer - inner = strips) and the pool floor area.

Release (owner rules, no assumptions):

| Element | Released when | Otherwise |
|---|---|---|
| Boundary-wall band | a member type (B.W footing, G.B ground beam, isolated footing) identified with sheet evidence is passed in (owner Q-12 = B, conditional; T-065 not merged); depth from that evidence or the family's schedule row | HELD MEMBER_TYPE_PENDING with length and area, no volume |
| Band part inside a member | never (may already be in the member) | HELD STRIP_UNDER_MEMBER with length, area, member ids |
| Pool walls | a printed height note beside the pool | HELD POOL_WALL_HEIGHT_NOT_PRINTED with the wall plan area (owner Q-19, Q-26) |
| Pool floor | a printed floor-thickness note beside the pool and a closed outer outline | HELD with the outer plan area (a detail on another sheet is not bound here: T-049) |

Every other finding keeps its frozen items. Every face length of a re-measured finding is in exactly one record
(conservation printed per finding); missing never becomes 0.

## Alsenan run, frozen vs V2 (same 1 455-line engine run; Drive "Alsenan chalet project", both DXFs, sha256 = SOURCE_MANIFEST)

Frozen run: `tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V2.9 --structural ... --conventions V6` (exit 0,
1 455 lines, reproduces the scoreboard: concrete WAPE 17.03 % on 3 compared lines). V2: `run_v2.py` on that run.
Line diff: 3 frozen lines replaced by 4 V2 lines, the other 1 452 lines byte-identical and in the same order; every
other trade's scorer bucket identical.

| Concrete line (m3) | Freelancer | Frozen engine | V2 engine | Change |
|---|---|---|---|---|
| Footings + straps + perimeter | 77.63 | 77.27 released (incl. band 7.22 = 60.17 m x 0.20 x 0.60) | HELD: footings + straps 70.04 released, band 91.94 m centre line held (73.64 m / 14.73 m2 MEMBER_TYPE_PENDING + 18.30 m / 3.66 m2 under 17 drawn members) | compared -> held (owner Q-12) |
| Pool | 12.35 | 3.50 released (walls 1.24 m2 x 1.6 convention + floor 6.045 m2 x 0.25 convention) | HELD: wall plan 2.357 m2, outer plan 10.936 m2 (no printed depth or floor note beside the plan) | compared -> held (owner Q-19, Q-26) |
| Stairs + domes | 21.83 | 12.01 | 12.01 (not touched; T-049 / T-056) | none |
| Concrete WAPE (compared lines) | | 17.03 % on 3 lines (111.81 m3) | 45.01 % on 1 line (21.83 m3) | coverage 100 % both, silent omissions 0 both |

The WAPE rises only because two lines that rested on an unidentified member type and on convention sizes are now held,
as the owner's answers require; no released number got worse. Diagnostic only (not evidence, T-065 open): if the band
were confirmed as the B.W 20 x 60 footing, the released footing line would be 70.04 + 73.64 x 0.20 x 0.60 = 78.88 m3
(freelancer 77.63, +1.25 m3, +1.6 %) with 3.66 m2 still held under members (2.20 m3 at 0.60).

Hand checks (from the drawing, not engine output):
- Band: closed ring, centre line 2 x 31.17 + 2 x 14.80 = 91.94 m (T-037 / T-050 hand value) = V2 rings[0]; plan
  91.94 x 0.20 = 18.388 m2 = V2 73.64 x 0.20 + 18.30 x 0.20. Frozen view reproduced: kept paired overlap 60.17 m;
  the two lost long faces 31.37 m (EXPLAINED_BY_MEMBER) and 30.97 m (CONTEXT_OF_OTHER_SHEET) recovered.
- Pool (D shape): outer 3.50 x 1.75 + pi / 2 x 1.75^2 = 10.936 m2, inner 3.10 x 1.55 + pi / 2 x 1.55^2 = 8.579 m2,
  ring 2.357 m2 (T-037: 2.358) = V2 straight strips 1.32 m2 (centre line 3.30 + 1.65 + 1.65 m) + curved
  pi / 2 x (1.75^2 - 1.55^2) = 1.037 m2. Frozen kept 1.24 m2 (the straight half).

Held-under-member length differs from the T-058 probe (13.40 m, re-run this task: closed polylines only, 8 on the
footing layer + 36 on the column layer): V2 uses the route's detected members (8 drawn footings + 9 columns along the
band, 17 in all), which include footings the drawing draws as loose lines on the footing layer (39 LINEs there):
F11 3.50 x 1.50 (3.50 m of band inside it), FN 1.00 x 1.00 (1.00 m; the probe saw only its column, 0.30 m) and
three small F pads about 0.90 x 0.80 at the west corners and mid-south. Total +4.90 m. Two
schedule-sized footprints drawn round marks (not drawn outlines) are listed and not used.

## Verdict proposals (for the verifier)

- Band length (part of CONC.FOOTING): ENGINE_RIGHT for V2 against the frozen 60.17 m (hand ring 91.94 m above).
  Against the freelancer's perimeter footing (71.7 m, 8.60 m3): UNRESOLVED until the member type is identified
  (owner Q-12; T-065). The CONC.FOOTING line is HELD under V2.
- Pool wall plan: ENGINE_RIGHT for V2 (2.357 m2 = hand ring) against the frozen 1.24 m2; the freelancer's
  12 m x 0.20 = 2.40 m2 agrees within 0.043 m2 (1.8 %). Pool floor plan: V2 10.936 m2 = hand; freelancer 10.8 m2
  (-1.3 %). Pool volumes: UNRESOLVED (pool depth Q-26; the 0.40 floor printed on the pool detail is bound by T-049).
- Stairs + domes: unchanged, UNRESOLVED (Q-18 domes held and visible, Q-19 / Q-20 stairs).

## Strip census on the same run (diagnostic only, frozen items kept)

| Family | Sheet | Frozen strip length m | V2 centre line m | V2 plan m2 | Removed faces recovered | Face conservation m | Use |
|---|---|---|---|---|---|---|---|
| STAIRS | GF slab plan | 7.995 | 11.699 | 1.170 | 0 | 0 | diagnostic |
| STAIRS | GF slab plan | 9.20 | 13.80 | 4.140 | 3 | 0 | diagnostic |
| UNKNOWN | ground-beam plan | 2.02 | 2.020 | 0.202 | 0 | 0 | diagnostic |
| POOL | ground-beam plan | 6.20 | 11.784 | 2.357 | 0 | 0 | replaced |
| BOUNDARY_WALL | foundation plan | 60.17 | 91.94 | 18.388 | 2 | 0 | replaced |
| STAIRS | ground-beam plan | 5.60 | 5.60 | 1.680 | 1 | 0 | diagnostic |
| STAIRS | ground-beam plan | 4.60 | 5.75 | 1.725 | 0 | 0 | diagnostic |

The stair groups are flights, not strips; their strip lengths only show that the frozen pairing also drops faces
there (3 recovered on one flight). Stair concrete is T-056's (riser / tread rule, owner Q-19).

## Other villas (synthetic, not Alsenan)

60 synthetic route-G villas (tools/synthetic_villa_m8.py seeds 1-60): face and arc conservation 0 on every strip
finding. Rectangular pools with printed depth and floor notes: V2 = frozen to 1e-4 m3 and = the generator truth to its
rounding (seeds 1, 9, 35 in the tests); pools without a printed note: frozen used convention sizes, V2 holds them with
the drawn ring area. Plot-line boundary strips on 2 or 3 sides: V2 centre line = frozen - one width per corner (the
frozen overlap counts each corner square twice); these findings are bounded, not measured, so no item changes.

## What is missing

- Member type per band part (T-065): until then no band volume on any villa.
- Pool depth (Q-26) and binding the pool detail's printed floor 0.40 (T-049).
- Wiring V2 into a released method (a new ARCH / route version) is a later, owner-approved step; this task only
  measures it.
