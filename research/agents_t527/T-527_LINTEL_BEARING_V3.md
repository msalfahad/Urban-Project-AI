# T-527: LINTEL_BEARING_V3, lintel ends at a curved bay read the DRAWN masonry end (F-C-T519-1, R-T527-1, Gate A)

Worker 1, lane S, claim 2026-11-05 15:21 UTC, base engine 1c0ac911. Research only: `lintel_bearing_v3.py` (project-
agnostic rule), `t527_extract.py` (drawing reader, private inputs outside the repository), `t527_effect.py` (downstream
effect through the merged T-516 / T-519 / T-524 code), `out/` (numbers only: lengths from a jamb or along a wall, radii,
ids; no drawing coordinate), `tests/t527_lintel_bearing_v3/` (26 tests). V2 (`research/agents_t519/lintel_bearing_v2.py`)
and every merged module are imported read-only and unchanged. No engine, rule, knowledge, hub, master or candidate file
changed; released default (V2.9 + route G) and candidate V3.0.58 untouched. Drawing cited by Drive folder and title only:
'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha ab54dd55).

## 1. Physical element and engineering question (ERS s.2.1)

The lintel END over the masonry beside a jamb, where the wall band runs towards a curved (bay) wall. Question: where does
the full-thickness masonry stop: at the arc outline, at the chord V2 constructs, or at a column face?

Evidence, highest first:
- The architectural plan (DXF): the bay is drawn as two concentric WALL-layer face arcs r_in 1.935 / r_out 2.135 m (wall
  0.20 m) about one centre, with 4 WINDOW-layer arcs (glazing) of the same centre. The band's far face line is drawn on
  to the INNER face arc and stops exactly on it (0.0 mm, both crossings 7.570294 / 10.629706 m along the band); beyond it
  the bay's step / floor edge lines start at the same point. No column stands at the bay end (nearest column outline is
  W18's START column C8).
- MASONRY_CENTRELINE_V2 stretch 'CURVED_GLAZED_BAY, arc r 2.075 m, sweep 1.8059 rad (CENTRELINE_MEETING)': 7.4708 ..
  10.7292 m, the points where a constructed centreline circle meets the band centreline. Nothing is drawn there.

Answer: the physical masonry end is the drawn inner face arc where it first cuts the band across the full thickness (here
the far face, 0.0995 m beyond the chord point). The chord is a construction, not a drawn edge; the column face is not
involved at this end.

## 2. Rule R-T527-1 (new version LINTEL_BEARING_V3; every villa; provenance F-C-T519-1)

1. Each CURVED_GLAZED_BAY stretch is matched to exactly one drawn bay: a centre with >= 2 concentric WALL-role arcs
   (1 mm) whose inner circle cuts the band within the stretch +- 0.50 m.
2. Open region = disk(r_in) + each annular sector [r_in, r_out] spanned by a WINDOW-role arc of that centre. V3 masonry
   = V2 masonry with the chord rectangle given back to the band (minus columns and the band's other gaps) and the band's
   part of the open region removed (own band only, as T-516).
3. Reach and stopper are V2's (0.5 mm linear tolerance, columns first), plus: the reach is capped where the open region
   first meets the FULL-thickness strip (V2's 0.5 mm lateral inset would otherwise run inset x cot(angle) past an oblique
   boundary: 0.33 mm on the fixture). Stopper END_OF_MASONRY, id CURVED_BAY:<stretch>, so R-T516-1 states apply as they
   are.
4. No drawn bay (no / one WALL arc, two candidate centres, unit mismatch, a circle that only touches the band): the ends
   that stop at that stretch are HELD by name (CURVED_BAY_NO_DRAWN_END): never the chord value, never 0.40, never 0.

## 3. Owner manual method vs drawing-derived method

| | Owner manual / prior method | Drawing-derived (V3) |
|---|---|---|
| Bearing basis | precast 0.15 m min (company) / project detail MIN 0.40 m | b in [0.40, a], a measured |
| End at a curved bay | V2: the centreline chord point (a construction) | the drawn inner face arc, full thickness |
| Missing drawn end | (V2: always a chord) | HELD by name |

The owner rule (stock lengths, 0.15 m minimum) is unaffected in its own scope; the project RC schedule governs these
lintels (R-T519-1, merged).

## 4. Full DXF re-run, 16 lintels / 32 ends (V1 control, V2 first DXF run, V3)

`out/JAMB_EVIDENCE_V3_T527.csv`. V1 (T-516 code) reproduces the merged T-516 evidence 32 / 32 (control). Only one curved
bay exists on the three storeys (`out/CURVED_BAYS_T527.csv`: 1F band WB-FL0041-FL0042); GF / 2F have none.

| End | V1 (T-516) | V2 (T-519) | V3 | Cause |
|---|---|---|---|---|
| D-GF-11 START | 0.831 END_OF_MASONRY | 0.827 COLUMN | 0.827 COLUMN | V2: EPS_AREA ran 3.7 mm into the 45 deg column corner (F-C-T516-1, Checker 0.827 AGREE) |
| D-GF-13 END | 1.261 COLUMN | 1.260 COLUMN | 1.260 COLUMN | V2: the area tolerance no longer lengthens the reach (0.13 mm overrun crossed a mm) |
| W18 END | 0.478 OPENING (bay chord) | 0.478 OPENING | 0.577 END_OF_MASONRY CURVED_BAY | V3: drawn inner face arc, 0.577994 m (Checker 0.578 AGREE; floor-to-mm convention 0.577) |

The other 29 ends: identical in value and stopper under V1, V2 and V3. No state moves: D-GF-11 START and D-GF-13 END stay
BOUNDED, W18 END stays BOUNDED (>= 0.40), W18 stays FLAGGED_DEFICIT on its START (0.000 at column C8).

## 5. Effect on merged results (computed by their own code, `out/EFFECT_T527.json`)

- T-516 (R-T516-1): W18 hard length ceiling 0.978 -> 1.077 m, links ceiling 5 -> 6 nr, straight bar ceiling 2.946074 ->
  3.244297 kg (x 1.077 / 0.978); D-GF-11 ceiling 1.869 -> 1.865 m (5.630075 -> 5.618025 kg); D-GF-13 3.764 -> 3.763 m
  (11.338470 -> 11.335458 kg). These are ceilings of FLAGGED / BOUNDED lintels; no released or candidate quantity uses them.
- T-519 (R-T519-1): 6 nr PRODUCED / 10 HELD unchanged; system 16 / 16 PROJECT_RC unchanged; precast beside pieces and fits
  unchanged (W18 1.50 DOES_NOT_FIT on its START). Only the RC length ceilings above follow.
- T-524 (R-T524-1): deficit-set concrete 0.372692 .. 0.437542 m3, removed 0.076458 m3: unchanged (the moved ends are
  BOUNDED; a BOUNDED end keeps b_min in hi).
- T-531 (lintel bars): the W18 group can proceed on V3 (W18 stays AT_LEAST by its START deficit; its END is now drawn).

## 6. Verdicts (proposals for the Checker)

- W18 END: V2 ENGINE_WRONG (constructed chord) -> V3 0.577994 m, hand calculation: jamb 6.9923, inner-arc crossing of
  the far face 9.1 - sqrt(1.935^2 - 1.185^2) in band coordinates = 7.570294 m, the drawn face line ends there.
- Freelancer: no lintel row (RC workbook one rebar total): UNRESOLVED, no comparable cell.

## 7. Tests

`tests/t527_lintel_bearing_v3`: synthetic bay (non-Alsenan; r_in 2.00 / r_out 2.20 about (7.00, -1.20), window
3.00-4.20): V3 1.129671 m vs V2 chord 1.076631 m (+0.053040, hand), rotations 30 / 117 / -45 deg, mirror, the side
without a bay unchanged, the arc meeting the far face at the jamb -> 0 (never 0.40), 5 no-drawn-end cases HELD, bad
radius refused; development villa: committed evidence reproduces, V1 control 32 / 32, the three moved ends, the W18
drawn crossing, downstream effects; DXF re-run (private drawing, skipped when absent) equals the committed CSVs byte for
byte. Merged t516 / t519 / t524 suites pass unchanged.

## 8. Lessons row (ERS s.7, proposed)

| 2026-11-05 | a lintel end at a curved bay read the masonry end from a constructed centreline chord | W18 END 0.0995 m short (and any bay-end bearing / ceiling with it) | read the end from the drawn face arcs across the full thickness; no drawn end -> HELD by name; a tolerance never lengthens the reach at an oblique boundary | tests/t527_lintel_bearing_v3 | T-527 |

## 9. For the Checker (re-measure from the DXF)

W18 END on 1F band WB-FL0041-FL0042: jamb at 6.9923 m from the band start; bay face arcs r 1.935 / 2.135 m (WALL layer);
far-face line (layer 1) from the jamb to its end on the inner arc; a = 0.578 m. Reproduce: decode P7757.dxf into
.work/private/P7757/, then `bash scripts/agent_env.sh pytest --tree <tree> tests/t527_lintel_bearing_v3` (builds the
t125 capture into .work/private/t527 on first run, about 1 min).

## 10. Open

- D-GF-12 END (oblique junction) and W16 head stay HELD (unchanged). GF / 2F carry no curved bay: no further end tested
  on a real bay with a glazed sector cutting the band (fixture only).
- Unresolved route defect B1 (mirrored ARC sweep / bulge side, engine/cad_adapter.py): V3's open disk does not depend on
  an arc's sweep (centre and radius only); the sweep is used only for glazed sectors, none of which cuts a band on this
  villa. A villa whose glazed sector cuts the band must be re-checked against B1 before its ends are trusted.
- Not wired: the T-516 / T-519 ledgers' committed outputs are V1; a wiring package adopts V2 + V3 (manifest T-530).
