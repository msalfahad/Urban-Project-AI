# T-272 Ground-beam stirrups: shape, count and mass closure (boundary G.B and main-house exterior; every villa)

Worker 1 (lane S), 2026-10-24. Research piece, not wired: no engine, candidate or released line changed. Development
villa, not an accuracy claim. Drawings named by Drive folder and title only; members by run id.

## r2 (Checker 2026-10-24 17:04, narrow): counted per drawn clear span; the ring split at its column

Fault fixed: r1 counted each run from support face to support face as ONE span, i.e. it let the links run through
the ground beams that frame into the run (run #2 7D0+FC#2: 38 .. 40 instead of 36 .. 40), and spaced the ring as one
run on scaled face arcs. r2 rule (Checker): no link continues through a crossing / tee ground beam unless a print shows
it, so a run is counted per drawn clear span between supporting faces (column faces AND the faces of every beam that
frames into it or crosses it); the curved ring is split at column 17BA. Count stays HELD (end rule not printed), the
envelope is never called DRAWING-CONFIRMED, mass HELD, never 0.

New input `CLEAR_SPANS_T272R2.json` (values only, no coordinates) from `t272_r2_extract.py` on Drive "Alsenan chalet
project" / "ST7757 dxf.dxf" (sha 9f9d1179, same file as T-141 / T-230 / T-242): bands, columns and spans exactly as
T-242 (GROUND_SYSTEM_SPANS_V2); the footprint of each beam the splitter lists as 'CROSSING_OR_TEE (no split)' by the
same engine function (`_junction_interval`), widened to the drawn face-line ends of an oblique beam (the paired band
of an oblique beam is cut square at its shorter face line). All 9 framing beams STOP AT THE FACE of the run (T-junctions,
none crosses through); every one is 0.30 wide.

Oblique beam 182+183 at 170+7C3#2 (vector read): face line 183 ends ON the run face 1.8115 m from its start face; face
line 182 ends 0.1627 m off the run face, on the side face of 15D+7C8 at 1.55 m. The oblique beam therefore occupies the
run face from 1.55 to 1.8115 m, adjoining 15D+7C8 (1.25 .. 1.55): one support zone 1.25 .. 1.8115, clear spans 1.25 +
1.5585 m (the V2 interval alone saw a 7 mm corner contact and would have left a false 0.2545 m span).

Ring ARC:157+158 (vector read): inner arc r 2.25 drawn over 167.236 deg (6.5674 m), outer arc r 2.55 over 150.086 deg
(6.6797 m), concentric within 0.1 mm. The drawn ranges differ: at the 17C0 / 170+7C3#4 end the inner face runs 13.4 deg
(0.525 m) past the end of the outer face (the outer face meets 170+7C3 there). Column 17BA's outline crosses the inner
arc over 0.1274 m (3.24 deg) and the outer arc over 0.3019 m (6.78 deg); 17BD's outline covers the last 0.1029 m of the
outer arc. A link is a radial section from the inner to the outer face; it exists only where that section crosses no
support: two sweeps, 66.43 deg (inner 2.6087 / outer 2.9566 m) and 72.36 deg (inner 2.8416 / outer 3.2205 m).
Envelope (spacing leg not printed): low on the inner arcs (18 - 1) + (19 - 1) = 35, high on the outer arcs (20 + 1) +
(22 + 1) = 44. Reading on the drawn face pieces net of the column outlines (inner 3.2108 + 3.2108, outer 2.9751 +
3.2988 m): inner 42 .. 46, outer 40 .. 44; it is reported beside, not as the envelope, because its inner pieces include
the 0.525 m wedge at 17C0 / 170+7C3 and the 17BA sweep where only the inner face is clear: a radial link there would cross
beam 170+7C3 or column 17BA, which the Checker's own rule excludes.
Reconciliation with the Checker's 40 .. 45 (faces inner 6.2675 / outer 6.380 m): those are the drawn arcs less 0.300 m
each (6.5674 - 0.300 = 6.2674; 6.6797 - 0.300 = 6.3797); the drawn column outline crosses the inner arc over 0.1274 m
(not 0.300) and the outer over 0.3019 + 0.1029 (17BD) m, and the inner-only wedge is not a link zone. Cause named:
column width deducted uniformly vs the drawn outline crossing, and face length vs radial-section admissibility.

| Run | f-f (m) | framing beams | clear spans (m) | low | half-s reading | high | r1 through (refused) | T-265 |
|---|---|---|---|---|---|---|---|---|
| 107+7CE#1 | 0.3639 | - | 0.3639 | 2 | 3 | 4 | 2 .. 4 | 3..4 |
| 109+7CB#2 | 4.4 | 15C+7CC, 185+7C7 (opposite sides) | 2.700 + 0.300 + 0.800 | 23 | 26 | 29 | 29 .. 31 | 30..31 |
| 109+7CB#3 | 2.7 | - | 2.700 | 17 | 18 | 19 | 17 .. 19 | 18..19 |
| 10A+7C9#1 | 4.3 | - | 4.300 | 28 | 29 | 30 | 28 .. 30 | 29..30 |
| 114+115+7DF#2 | 1.0 | - | 1.000 | 6 | 7 | 8 | 6 .. 8 | 7..8 |
| 145+7CA#1 | 1.9 | 178+7DB | 0.500 + 1.100 | 10 | 12 | 14 | 12 .. 14 | 13..14 |
| 170+7C3#1 | 2.4 | - | 2.400 | 15 | 16 | 17 | 15 .. 17 | 16..17 |
| 170+7C3#2 | 3.37 | 15D+7C8 + oblique 182+183 | 1.250 + 1.5585 | 18 | 20 | 22 | 22 .. 24 | 23..24 |
| 170+7C3#3 | 3.35 | 175+7DE | 2.230 + 0.820 | 19 | 21 | 23 | 22 .. 24 | 23..24 |
| 170+7C3#4 | 3.25 | - | 3.250 | 21 | 22 | 23 | 21 .. 23 | 22..23 |
| 7D0+FC#1 | 2.975 | 109+7CB | 2.500 + 0.175 | 17 | 19 | 21 | 19 .. 21 | 20..21 |
| 7D0+FC#2 | 5.745 | 17D+7E4 | 2.125 + 3.320 | 36 | 38 | 40 | 38 .. 40 | 39..40 |
| 7D0+FC#3 | 6.35 | 17B+7E5 | 2.950 + 3.100 | 39 | 41 | 43 | 42 .. 44 | 43..44 |
| 7D0+FC#4 | 1.2 | - | 1.200 | 7 | 8 | 9 | 7 .. 9 | 8..9 |
| 7E0+FD#1 | 3.35 | 184+7CF | 1.000 + 2.050 | 19 | 21 | 23 | 22 .. 24 | 23..24 |
| 7E0+FD#2 | 3.25 | - | 3.250 | 21 | 22 | 23 | 21 .. 23 | 22..23 |
| 16 straight runs | 49.9039 | 8 runs split | | **298** | 323 | **348** | 323 .. 355 | 339 .. 355 |
| ARC:157+158 | 6.0873 (T-265 centreline) | 17BA (split), 17BD (end) | sweeps inner 2.6087 + 2.8416 / outer 2.9566 + 3.2205 | **35** | (41) | **44** | 38 .. 45 | 41..42 |
| **Exterior, 17 runs** | **55.9912** | | | **333** | 364 | **392** | 361 .. 400 | 380 .. 397 |

Effect: exterior link count HELD inside **333 .. 392** (r1 361 .. 400; T-265 380 .. 397 'DRAWING-CONFIRMED (COUNT)'
superseded). The high end falls too: a link at each face of each clear span is fewer than links through the 0.30 m
junction zones. QA reading (sharp box at 2.5 cm cover, high count, no hooks): exterior 351.23 kg (r1 358.40); boundary
86.81 kg unchanged; not a quantity, not a bound. Boundary G.B: unchanged, HELD without an envelope (M4 columns).
Hand check (for the Checker, two runs): 7D0+FC#2: 2.125 / 0.15 = 14.17 -> ceil 15 -> 14 .. 16; 3.320 / 0.15 = 22.13
-> ceil 23 -> 22 .. 24; run 36 .. 40 (= the Checker's alternative). 7E0+FD#1: 1.000 / 0.15 = 6.67 -> ceil 7 -> 6 .. 8;
2.050 / 0.15 = 13.67 -> ceil 14 -> 13 .. 15; run 19 .. 23.

## 0. Inputs (r1)

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

## 3. Count: the end rule decides, and it is not printed (r1 table below SUPERSEDED by the r2 table above)

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
| exterior stirrup count (r2) | HELD inside 333 .. 392 (per drawn clear span; ring on radial sweeps split at 17BA); the envelope is NOT DRAWING-CONFIRMED while the end rule is unprinted; r1 361 .. 400 and T-265 '380 .. 397 DRAWING-CONFIRMED (COUNT)' superseded (links through framing beams; unprinted end rule; ring as one run) |
| ring count | HELD 35 .. 44 on radial sweeps; face reading 40 .. 46 beside; Checker 40 .. 45 reconciled (0.300 m deducted per arc vs drawn outline crossings 0.1274 / 0.3019 + 0.1029 m; inner-only wedge 0.525 m) |
| boundary stirrup count | HELD (M4 columns + end rule), no envelope |
| stirrup cut length / mass | HELD on both families; AD-4 holds the tails; QA reading 0.45 t only |
| boundary link closure | NOT DRAWN: designer item (added to D-37 below) |
| freelancer | RULE_DIFFERENCE (kg/m3 lump) |

## 6. Rule proposed (every villa; provenance T-272; adopted only as a new rule version)

**R-STIRRUP-1**: a link's mass is released only when its count and its cut length are both established. Cut length
L = 2a + 2c' - 8R + R (3 pi / 2 + 2 theta) + 2e from PRINTED facets (section, actual cover, centreline radius, hook
angle, tail) with a project or owner-approved provenance; a minimum cover gives an upper envelope only; a drawn shape
is not a dimension; a code value is QA only. Count over each drawn clear span between supporting faces (column faces and the faces of every beam that frames into
or crosses the run: no link through a crossing beam unless printed), zone by zone, with the printed end rule and an
established spacing meaning; otherwise HELD inside [faces as end ties, a stirrup at each face] (single zone
ceil(L/s) - 1 .. ceil(L/s) + 1); a curved run is split at its supports and counted on the sweeps where a radial link
section crosses no support, on the leg the spacing is measured on, else inner (low) to outer (high) face arc. A closed link drawn with no closure is a designer item. Never 0, never a range in the BOQ.

## 7. Lessons-register row (proposed)

2026-10-24 | Ground-beam stirrup counts 380 .. 397 were carried as DRAWING-CONFIRMED although the drawings print no
end rule; the honest envelope is 361 .. 400 | ceil(L / s), the frozen S5 'lower bound', silently assumes the first
stirrup within s / 2 of the face (a rate reading of a spacing notation); the curved ring was spaced on its centreline
| A spacing count is exact only with a printed end rule and an established spacing meaning; otherwise it is HELD
inside [faces as end ties, a stirrup at each face]; a curved member is spaced on the printed leg, else inner to
outer face arc (any villa) | tests/t272_stirrup_closure (test_no_end_rule_gives_envelope_and_held,
test_mirrored_beam_same_count, test_curved_run_envelope_inner_to_outer_arc, test_ring_counted_on_face_arcs) | PROPOSED.

r2 row (proposed): 2026-10-24 | r1 counted each run face to face as one span (links through 9 framing beams) and the ring
as one run on scaled arcs; envelope 361 .. 400 called DRAWING-CONFIRMED | the V2 span splitter lists framing beams as
'CROSSING_OR_TEE (no split)' for concrete; a link count needs the drawn clear spans, and an oblique beam's paired band
under-reads its footprint (7 mm corner vs 0.2615 m drawn) | Links are counted per drawn clear span between supporting
faces (columns and every framing / crossing beam, footprint to the drawn face-line ends); a curved member is split at
its supports and counted on radial sweeps; a uniform column-width deduction is not a drawn face (any villa) |
tests/t272_stirrup_closure/test_r2_clear_spans.py, test_alsenan_ledger.py (test_one_run_by_hand,
test_ring_split_at_column_on_radial_sweeps) | PROPOSED.

## 8. Designer items (no owner question: ERS 2.7 not met; AD-4 already rules on hooks)

D-37 extended (Lead to record): for the ground-beam links of p.13 / p.14: (1) hook angle and tail length, or a
standard-link note; (2) bend (mandrel) diameter; (3) the cover as built (or the link outer size); (4) the first link
position from the support face (end rule) and whether 15 / 20 cm is a maximum c/c; (5) the boundary G.B link
closure (drawn with no hook or overlap); (6) for the curved ring, the face or leg the 15 cm is measured on; (7) M4
boundary column positions (already listed). With (1)-(4) the module releases the exterior mass at once.

## 9. Not done / uncertain

- r2: the clear spans come from the DXF vectors only (second drawing for the tees: the ST PDF ground-beam plan not
  re-read this run); CLEAR_SPANS_T272R2.json is reproducible only with the private DXF (command and sha in r2 section).
- r2: a print showing links continuing through a junction would restore the through-run reading for that junction.

- Interior ground-beam families (> 5 m, < 5 m, < 2.5 m sections) are outside this task's runs (T-265 scope).
- The lower G.B of section A-A (Q-28 band) is not in scope.
- Spacing '20' on p.14 is read in cm from the sheet's units (every printed dimension on p.14 is cm); stated, not chosen.
