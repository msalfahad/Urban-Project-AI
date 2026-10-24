# T-272 Ground-beam stirrups: shape, count and mass closure (boundary G.B and main-house exterior; every villa)

Worker 1 (lane S), 2026-10-24. Research piece, not wired: no engine, candidate or released line changed. Development
villa, not an accuracy claim. Drawings named by Drive folder and title only; members by run id.

## 0. Inputs

| Input | Read for |
|---|---|
| Drive "Alsenan chalet project" / "ST7757.pdf" p.13 (100 + 400 dpi, own read this run) | 'Ground Beams. for exterior walls' 1:20: 30 wide, 'FOLLOW ARCH.'; ONE closed link 'ø8/15cm' with 2 vertical legs (the X at mid-depth is the '2ø12/30cm' side-bar leader, not a cross-tie); corners drawn bent; ONE hook drawn at the top right corner turning into the core (135-degree shape), tail not dimensioned. No zone, no first-stirrup position, no ground-beam elevation |
| same, p.13 vector strokes (layer S-REIN.D, own read) | exterior link: 4 corners drawn as curves, TWO short hook strokes at one corner (a hook pair, 135-degree shape), no dimension on any of them |
| same, p.13 'TYP. DETAIL OF ISOLATED FOOTING' (right), ground beam drawn in ELEVATION through a column | links drawn at a regular pitch (34.0 pt), the first link on each side drawn 19.3 / 19.4 pt from the column face = about 0.57 of the drawn pitch; undimensioned, no link label in this detail, typical / not to scale, P8-N03 'do not scale': a drawn pattern only (QA), not an end rule |
| same, p.14 section A-A (400 dpi + vector strokes, own read) | upper G.B 20 x 40, 'ø8/20 STIRRUPS' (unit not on the label; every dimension on the sheet is cm), link drawn as a CLOSED RECTANGLE WITH SHARP CORNERS AND NO HOOK OR OVERLAP; the 20 x 30 boundary columns pass through the band ('SEE ARCH PLAN', none drawn on either plan: M4) |
| same, p.8 note 22 | cover >= 2.5 cm beams, >= 7 cm against soil: MINIMUMS |
| research/d1_1_stirrup_authority_audit (frozen) | channel-by-channel source search: 0 radius / diameter dimensions in the DXF, no bend / hook / closure / fabrication text on any sheet; re-confirmed visually here on pp.13-14 |
| research/ad1_authority_decisions AD-4 (owner, 2026-10-08) | hook angle = drawn shape only; hook extension BLOCKED unless the project dimensions it; code hook values QA only |
| research/agents_t265/LEDGER_T265.csv (MERGED dd08d6b2, Checker Gate A) | the 22 runs and face-to-face lengths (boundary 5 runs 44.07 m; exterior 16 runs + ring 55.9912 m at D 0.95) |
| research/agents_t242/ALSENAN_GROUND_INPUT.json (merged) | ring ARC:157+158 faces r_in 2.25 / r_out 2.55 m |

Files: `t272_stirrups.py` (STIRRUP_CLOSURE_V1, pure rules, stdlib + engine rebar_unit_mass), `t272_alsenan_check.py`
(-> `LEDGER_T272.csv`, `summary.json`); tests `tests/t272_stirrup_closure` (Villa F hand fixture + adverse, Alsenan pinned).

## 1. The physical element

A stirrup is one bent bar: 2 legs + 2 sides set by the section less the ACTUAL cover on each face, 4 corner bends of
a centreline radius R, a closure (two hooks of angle theta with straight tails e, or an overlap). One closed link with
135-degree hooks at one corner: **L = 2a + 2c' + (3 pi - 8) R + 2e** (a, c' = centreline side lengths). Its count
needs the spacing, the MEANING of the spacing (exact pitch or maximum c/c) and the END RULE (first / last stirrup from
the supporting face). Concrete axis, longitudinal bars and stirrups are three different geometries of one member.

## 2. Facet by facet (exterior / boundary)

| Facet | Exterior GB (p.13) | Boundary G.B (p.14) | Status |
|---|---|---|---|
| diameter | ø8 | ø8 | PRINTED |
| spacing | 15 cm | 20 (cm by the sheet's units) | PRINTED; meaning (exact / maximum) not established for ground-beam links |
| topology | 1 closed link, 2 legs | 1 closed link, 2 legs | DRAWN |
| section | 0.30 x 0.95 (D by T-253, Checker CONFIRMED) | 0.20 x 0.40 | PRINTED / DRAWING-CONFIRMED |
| cover | >= 2.5 / >= 7 cm | >= 2.5 / >= 7 cm | MINIMUM_ONLY: link size is an UPPER envelope |
| bend radius | drawn bent, not dimensioned | drawn sharp | NOT PRINTED (P8-N03: do not scale) |
| hook angle | 135-degree shape drawn | no hook drawn | SHAPE ONLY / NOT DRAWN |
| hook tail | not dimensioned | - | NOT PRINTED (AD-4 BLOCKED) |
| closure | hook pair drawn (2 strokes at one corner) | **none drawn** (vector: 4 straight strokes, the long sides shared with the column bars running through): designer item | - / FLAG |
| end rule | not printed | not printed | NOT PRINTED |

Cut length: **HELD** on both families (4 facets exterior, 5 boundary). Mass: **HELD**. Never 0.

## 3. Count: the end rule decides, and it is not printed

Over a clear span L at spacing s (gaps never above s):
- low = the support faces act as the end ties (first stirrup up to a full s from the face): ceil(L / s) - 1;
- high = a stirrup at each face: ceil(L / s) + 1;
- the frozen S5 'lower bound' and T-265's A, ceil(L / s), is the reading 'first stirrup within s / 2 of the face':
  an UNPRINTED end rule, so it is neither the lower bound nor the count. Correction to T-265: its count range
  380 .. 397 was labelled DRAWING-CONFIRMED (COUNT); the drawing confirms only the envelope below and the count stays
  HELD (ERS s.3: notation meaning before arithmetic; lessons 2026-10-23: a reading is established per element type).
- Curved ring: the spacing radius is not printed, so the envelope runs from the inner-face arc (2.25 m x 2.5364 rad =
  5.7068 m) to the outer-face arc (6.4678 m); T-265 counted on the centreline 6.0873 m.
- Second drawing checked: the typical isolated-footing detail on p.13 draws a ground beam in elevation with its
  first link about 0.57 of a pitch from each column face (vector strokes, undimensioned, not to scale). It neither
  prints an end rule nor matches the s / 2 reading exactly (0.57 s gives counts between low and the s / 2 reading);
  under P8-N03 it is QA only. It confirms the end rule is a designer item, not a reading.

| Runs | Length (m) | Count low | half-s reading (= T-265 A) | high | T-265 range | Status |
|---|---|---|---|---|---|---|
| Exterior, 16 straight runs | 49.9039 | 323 | 339 | 355 | 339 .. 355 | HELD (end rule) |
| Exterior ring ARC:157+158 | 6.0873 (centreline) | 38 | 41 | 45 | 41 .. 42 | HELD (end rule + spacing radius) |
| **Exterior, 17 runs** | **55.9912** | **361** | **380** | **400** | 380 .. 397 | **HELD** |
| Boundary, 5 runs | 44.07 | no envelope: columns (M4) split the runs | (217 .. 227 if no column) | | HELD | HELD (M4 + end rule) |

Hand check for the Checker (one run, own count from p.13): 7D0+FC#2, L 5.745 m face to face, s 0.15: 5.745 / 0.15 =
38.3 -> low 38, reading 39, high 40. Ring: 5.7068 / 0.15 = 38.05 -> ceil 39 - 1 = 38; 6.4678 / 0.15 = 43.12 -> 44 + 1 = 45.

## 4. Mass and materiality (QA only, not a quantity, not a bound)

Unit mass ø8 = 64 / 162 = 0.395062 kg/m (rebar_unit_mass D2_OVER_162). The sharp-corner centreline box at the 2.5 cm
minimum cover, no hooks: exterior 2 x (0.242 + 0.892) = 2.268 m, boundary 2 x (0.142 + 0.342) = 0.968 m. At the high
counts: **exterior 358.40 kg, boundary 86.81 kg (no-column runs)**, about 0.45 t of ground-beam link steel HELD. This
is not a bound: R shortens each corner by (2 - pi/2) R, the tails add, and the actual cover may be larger.

| Ground-beam steel (kg), T-265 + this task | Boundary G.B | Exterior (17 runs) | Status |
|---|---|---|---|
| top + bottom | 315.564 | 796.319 | DRAWING-CONFIRMED (lower bound, T-265 merged) |
| side bars | - | 199.082 | DRAWING-CONFIRMED (T-265 merged) |
| stirrups count | HELD (M4, end rule) | HELD in 361 .. 400 | HELD |
| stirrups mass | HELD | HELD | HELD (cover min, R, hook angle, tails; boundary closure) |
| laps / development | HELD | HELD | T-273 (owner 15:31 lap authority) / D-36 |

The line cannot close on the issued set: stirrup mass needs the designer facts below. Freelancer: steel is a kg/m3
lump (44.19 t total over all elements), no stirrup row: **RULE_DIFFERENCE, no %**.

## 5. Verdict proposals

| Item | Proposal |
|---|---|
| exterior stirrup count 361 .. 400 | DRAWING-CONFIRMED envelope; count HELD (end rule not printed); T-265 '380 .. 397 DRAWING-CONFIRMED (COUNT)' superseded: its low end rests on an unprinted end rule and the ring on the centreline |
| boundary stirrup count | HELD (M4 columns + end rule), no envelope |
| stirrup cut length / mass | HELD on both families; AD-4 holds the tails; QA reading 0.45 t only |
| boundary link closure | NOT DRAWN: designer item (added to D-37 below) |
| freelancer | RULE_DIFFERENCE (kg/m3 lump) |

## 6. Rule proposed (every villa; provenance T-272; adopted only as a new rule version)

**R-STIRRUP-1**: a link's mass is released only when its count and its cut length are both established. Cut length
L = 2a + 2c' - 8R + R (3 pi / 2 + 2 theta) + 2e from PRINTED facets (section, actual cover, centreline radius, hook
angle, tail) with a project or owner-approved provenance; a minimum cover gives an upper envelope only; a drawn shape
is not a dimension; a code value is QA only. Count over the clear span zone by zone with the printed end rule and an
established spacing meaning; otherwise HELD inside [faces as end ties, a stirrup at each face] (single zone
ceil(L/s) - 1 .. ceil(L/s) + 1); a curved run is counted on the leg the spacing is measured on, else inner to outer
face arc. A closed link drawn with no closure is a designer item. Never 0, never a range in the BOQ.

## 7. Lessons-register row (proposed)

2026-10-24 | Ground-beam stirrup counts 380 .. 397 were carried as DRAWING-CONFIRMED although the drawings print no
end rule; the honest envelope is 361 .. 400 | ceil(L / s), the frozen S5 'lower bound', silently assumes the first
stirrup within s / 2 of the face (a rate reading of a spacing notation); the curved ring was spaced on its centreline
| A spacing count is exact only with a printed end rule and an established spacing meaning; otherwise it is HELD
inside [faces as end ties, a stirrup at each face]; a curved member is spaced on the printed leg, else inner to
outer face arc (any villa) | tests/t272_stirrup_closure (test_no_end_rule_gives_envelope_and_held,
test_mirrored_beam_same_count, test_curved_run_envelope_inner_to_outer_arc, test_ring_counted_on_face_arcs) | PROPOSED.

## 8. Designer items (no owner question: ERS 2.7 not met; AD-4 already rules on hooks)

D-37 extended (Lead to record): for the ground-beam links of p.13 / p.14: (1) hook angle and tail length, or a
standard-link note; (2) bend (mandrel) diameter; (3) the cover as built (or the link outer size); (4) the first link
position from the support face (end rule) and whether 15 / 20 cm is a maximum c/c; (5) the boundary G.B link
closure (drawn with no hook or overlap); (6) for the curved ring, the face or leg the 15 cm is measured on; (7) M4
boundary column positions (already listed). With (1)-(4) the module releases the exterior mass at once.

## 9. Not done / uncertain

- Interior ground-beam families (> 5 m, < 5 m, < 2.5 m sections) are outside this task's runs (T-265 scope).
- The lower G.B of section A-A (Q-28 band) is not in scope.
- Spacing '20' on p.14 is read in cm from the sheet's units (every printed dimension on p.14 is cm); stated, not chosen.
