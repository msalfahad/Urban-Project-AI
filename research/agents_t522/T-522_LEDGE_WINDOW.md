# T-522 B8-06 pool court: the window run and the ledge, measured from the drawings or narrowed (research, unwired)

Worker 2 (lane A), 2026-11-05, claim 10:40 UTC. Files: `t522_ledge_window.py` (R-T522-1 .. 4, any villa),
`t522_inputs.py` (training-villa handles and printed values, no coordinate), `t522_alsenan.py` (run on the private
drawing), `tests/t522_ledge_window/` (12 tests). No engine, method, rule / knowledge version, registry, master or
candidate file changed; no candidate (V3.0.58) or released (V2.9 + route G) line moves. Drawings by Drive title and
handle only ("Alsenan chalet project": P7757_DXF_COMPRESSED.zip -> P7757.dxf sha256 ab54dd55...; the architectural PDF
part Alsenan_Architectural_P7757_Pages_07-08 p.2 NORTH WEST ELEVATION; p7757_arch_sheet09 (NE elevation) and sheet10
(section A-A) read and found not to show the court).

## 1. Physical elements (ERS s.2.1)

- WINDOW RUN: the 1F bath window (plan C35, 0.500002 lm on the wall line, glazing C33 .. C3E set 0.20 m back in the
  wall) over the +5.50 open-sky court slab. The membrane turns up 0.20 m on the masonry under the sill only if the sill
  stands at least 0.20 m above the slab top (R-WP-APPL-UPTURN-1).
- LEDGE: the 0.20 m strip of the +5.50 slab between the 1F curved bay (r 1.935) and the void edge (BCF, r 1.735), west
  of the wall line. Above it: the +9.70 roof terrace slab, solid over the bay, the ledge and the void part west of the
  wall line (2F plan, frame -44.85 m in x: ROOF +9.70 hatch to its parapet on the 1F wall line, no opening); the open
  sky starts at the wall line. Below the void: the GF pool.
- LEDGE FACE: the bay face is three drawn pieces, not one wall: BCD (layer 1, wall end), BCE (layer 5, the arched
  glazing) and BD0 (layer 1, wall end). In the NW elevation the glazing BCE ('269' = its chord 2 x 1.935 x sin 44.07
  deg = 2.692 m, measured 2.691494, AGREE 0.2 mm) is drawn '305' from the +5.50 slab-top line to the arch spring: its
  frame stands on the slab (floor-level glazing into the master bedroom), with no masonry under it.

## 2. Results per held part (statuses WORKFLOW_CONTROLS s.5)

| V3.0.58 line | before | after (this piece) | evidence / status |
|---|---|---|---|
| L-1954878b window_face, FIN.WP.ROOF_UPTURN lm | HELD 0 .. 0.500002 | **0.500002 lm MEASURED** (= 0.100000 m2 at 0.20) | sill printed **'84'** cm above the +5.50 slab-top line: DXF NW elevation DIMENSION 2EEC (measured 839.27 mm, vertical, starts 0.000 mm from the slab-top line of the 5500 level dim 29D0, inside the window width '50' 2D8D; head '216' 2EFA on it) and the PDF NW elevation chain '84 / 216 / 230'. 0.84 >= 0.20: an UPTURN. DRAWING-CONFIRMED |
| L-2361d6ec ledge membrane, FIN.WP.ROOF m2 | HELD 0 .. 0.639573 | HELD 0 .. **0.639573** (bound unchanged, own re-measure 0.639573) | covered 4.20 m level-to-level above, open toward the void; cause narrowed to ONE binary decision (s.3) |
| L-d7d1bf8c ledge upturn, FIN.WP.ROOF_UPTURN lm | HELD 0 .. 3.528277 | UPTURN HELD 0 .. **0.551615 lm** (BCD 0.250804 + BD0 0.300810) + WINDOW_TRANSITION HELD **2.976663 lm** (BCE, by detail, UP-WP-DOOR-001) | pieces 3.528277 = run 3.528277, residual 0.000000; a floor-level frame is a transition, never an upturn (R-WP-APPL-UPTURN-1). Upturn bound -84.4 % |

Unchanged beside: ledge void edge 0 .. 2.817214 lm (termination by detail), slab / void edges of the open-sky zone,
drainage RFI.

Effect if wired (stream F, no wiring here): FIN.WP.ROOF_UPTURN valued **186.782544 -> 187.282546 lm (+0.500002 lm =
+0.100 m2, +0.27 %)**, HELD lines on the code 3 -> 3 (window line closed; ledge line split into upturn 0 .. 0.551615 +
transition 2.976663); FIN.WP.ROOF unchanged 209.018867 m2 + HELD 0 .. 0.639573. Freelancer roof waterproofing 285.00 m2
(cells not read, T-494): no change to the comparison. Verdict proposals: window run ENGINE_RIGHT once wired (sill
printed, hand 0.50 x 0.20 = 0.100 m2); ledge upturn ENGINE_WRONG as a single 3.528 lm run (84 % of it is a glazing
threshold), corrected here; ledge membrane UNRESOLVED (exposure decision).

## 3. Ledge exposure: narrowed, not decided (R-T522-4)

Strip 0.639573 m2; its farthest point is d_max = 0.750 m behind the open-sky line (the cover edge on the wall line);
clear height h = 4.20 m level to level (4.00 m if the +9.70 slab is 0.20 m thick: its thickness is not printed here).
Rain more than theta_c = atan(0.75 / h) = **10.12 deg (h 4.20) .. 10.62 deg (h 4.00)** off vertical reaches the whole
strip; at 5 deg 0.215 .. 0.228 m2, at 10 deg 0.615 .. 0.637 m2, at 15 deg and above all 0.639573 m2. So no partial quantity has a
physical meaning: the strip is wetted whole by any driven rain beyond ~10 deg, or not at all in still rain. The open
side is also where the bay's floor-level glazing meets the slab (water at a bedroom threshold). Engineering view
(proposed, NOT applied): the ledge behaves as EXPOSED. Applying it needs a NEW rule version (V2 of the applicability
rule) with a sourced driven-rain criterion; no design angle is printed or held in a source, and inventing one is
refused (no-assumptions rule). The decision is the Lead's / Checker's (agent-derived rule scope, provenance T-486); an
owner question is not raised (ERS s.2.7: 0.64 m2 + 0.11 m2 upturn, no owner method changes).

## 4. Fixture and tests (villa Q522, by hand)

Ledge 3.00 x 0.40 printed +0.15, open sky, wall 2.00 lm + window 1.00 lm (sill 0.90 printed), detail upturn 0.15:
membrane 1.200 m2, upturn 3.00 x 0.15 = 0.450 m2 (default 0.600 without the detail). Adverse: nothing printed -> HELD
0.20 m2 bound, never 0; sill or upturn without a cited source refused; mm as metres refused; sill 0.10 -> transition;
face 0.50 solid + 2.00 glazing on slab + 0.50 solid -> upturn 0.200 m2 + transition 2.00 lm; covered -> all HELD with
bounds; glazing on a 0.25 kerb with the section cited -> kerb-face upturn + transition NOT_APPLICABLE, kerb without
section refused; pieces not reconciling refused; covered strip 3.00 x 0.40 under h 3.00: theta_c 7.5946 deg, 5 deg
0.787398 m2, 10 deg 1.200; mirror / rotation invariant. Development villa (private drawing): the values of s.2 / s.3.

## 5. Findings

- F-T522-1: the window sill was printed all along, in a DIMENSION entity (2EEC '84'); T-494 / T-517 searched TEXT /
  MTEXT / ATTRIB only. Dimension blocks carry printed values: every printed-value search reads them too.
- F-T522-2: the T-486 BAY_FACE treated three drawn pieces on two layers (wall ends layer 1, glazing layer 5) as one
  'wall' run; the elevation shows floor-level glazing. Any face run built from a chain of handles is split by layer /
  standing element before an upturn is valued.
- F-T522-3 (cross-trade): the bay glazing BCE is a floor-level window over an exterior ledge; its threshold detail
  (transition 2.976663 lm) belongs to the window / WP interface (designer item, UP-WP-DOOR-001), never to the room's
  skirting (R-T481 skirting lessons: a floor-level opening is deducted there).
- One element one owner: the ledge area is outside the pool membrane (T-503 / T-507) and TERRACE-550 (T-494 s.4,
  re-confirmed: the ledge polygon is the T-486 overhang, 0.639573 m2).

## 6. Lessons row (proposed, ERS s.7)

| 2026-11-05 | a window run and a 3.53 m bay face stayed HELD / were valued as one upturn though the drawing printed the sill ('84') and showed 84 % of the face as floor-level glazing | printed values were searched in text entities only (dimension blocks skipped), and a face built from a handle chain was not split by what stands on it | R-T522-1..4 (every villa): a sill is read from the printed elevation / section dimension and cited; a face is split by its standing elements (solid -> upturn, frame on slab -> transition, kerb with section -> upturn + N/A); a printed upturn height overrides 0.20 only with its detail; a covered strip open at a side is narrowed by d_max / h (theta_c), never valued by an assumed angle | tests/t522_ledge_window (Q522 by hand; adverse: no print, no source, mm, low sill, kerb without section, unreconciled pieces, covered, mirror / rotation) | proposed |

Missing: the ledge exposure decision (s.3), the threshold and void-edge details (designer), the +9.70 slab thickness
(only moves theta_c 10.12 -> 10.62 deg), drainage (RFI). Wiring: a later V3.0.x under Gate B (stream F).
