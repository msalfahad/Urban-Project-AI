# T-734 waterproofing H4 evidence: roof membrane downgrade record, census on V3.0.73, D-41

Worker 2, 2026-11-12 (lane A, research, unwired). Candidate ARCH_TAKEOFF_V3.0.73 (LINE_INDEX_V3_0_73, T-722). Nothing
wired or released; V2.9 + route G unchanged; no engine module, rule / knowledge version, registry or frozen file
touched; no downgrade record written (a worker never grades: the Checker issues it). Rules R-T734-1 .. -3 in
`t734_rules.py`; builder `t734_alsenan.py` (`--check`; `--dxf <private P7757.dxf>` rebuilds the face from named
handles); outputs `out/T734_WP_H4_EVIDENCE.{json,md}`; tests `tests/t734_wp_h4_evidence` (synthetic villa W734 by hand +
development villa pinned). Drawing by Drive title only: "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip ->
P7757.dxf (sha256 ab54dd55..., re-checked; own decode this run).

## (a) The released +9.70 roof membrane L-636fd3ff1784a12e653b (115.832 m2)

**Physical element.** The flat membrane of the terraces round the 2F block, inside the parapet / wall faces where it
turns up 0.20 (UP-WP-ROOF-001, Q-24), the two dome discs open (Q-24 / Q-29).

**Own re-measure, independent method (R-T734-2).** T-321 / T-691 found the face by a buffered flood fill. This run
rebuilds it from its 8 named carrier lines only (vertex = carrier x carrier, shoelace; every carrier asserted straight
and axis-parallel): C1 12E6 + 1280 + door gap 1.000 + 1281 (one y) / C2 1291 / C3 1278 / C4 12A7 / C5 1285 / C6 12C9 /
C7 12B9 / C8 12E2 (D-band reading) or the 2F west wall face (wall-face reading). Faces 146.374500 / 146.532000 m2,
perimeter 65.140 m on both. Domes CIRCLE 12EB / 2F33 r 2.211092 m: pi r^2 15.359013 m2 each; each dome is TANGENT to a
parapet face (12EB to 12C9, 2F33 to 12A7, clearance 0.0000 m), so the disc lies wholly inside the face.

| | m2 |
|---|---|
| band (own) | 115.656474 .. 115.813974 (T-321 115.65646 .. 115.81396: both ends +0.000014, buffer artefact) |
| released | 115.832 = 146.532000 - 2 x 15.349849 (105-chord domes, 1 mm sagitta) = 115.832303, rounding 0.000303 |
| above the high end | 0.018026 (0.0156 %): cause the chord under-deduction 0.018329, nothing else |
| D-BAND | 0.157500 (0.136 %): the open term |

**D-BAND investigated (ERS s.2).** 12E2 is not a base: it continues a stepped layer-D profile on the 2F west wall
(25 / 50 / 75 mm steps, 11 named lines) drawn at the plan cut, a feature 0.075 proud over 2.7684 m. Built before the
membrane (pilaster / thick wall) -> the membrane stops at it (low); applied after (cladding / moulding) -> it runs to
the wall face (high). No text, schedule or detail names it: a designer item (proposed for DESIGNER_QUESTIONS), not an
owner question (s.2.7 not met).

**Record.** Draft fields in out/T734 (a): line L-636fd3ff1784a12e653b, state HELD, basis UNSUPPORTED BASIS, reason and
3 evidence items, engine quantity 115.832 bound; the Checker types it with `boq_export_v1.py downgrade-add` on the
V3.0.73 lines (the tool binds project, revision set and line content). **Which figure:** the record keeps none; 115.832
goes to the audit rows; the H4 package then writes HELD 115.656474 .. 115.813974 (both ends measured). 115.813974 is
not released (its high end rests on the D-BAND reading).

**Upturn L-5ce5ba49 92.922 -> 92.925396 lm: not a downgrade** (it raises a released value: a Gate B change, no record
needed; the T-730 'WAITS T-734' blocker on it can go). Open: +0.000750 lm between 92.922 and the 105-chord
reconstruction 92.921250, unnamed here. **Rolls 17 pcs** not named; sensitivity to the D-BAND not re-run.

## (b) Census on V3.0.73

160 WP lines on V3.0.70 and V3.0.73, ids equal, 0 entries differ: 53 HELD + 5 MISSING all LIVE / MISSING, stale 0,
gone 0. **Cause correction (F-T734-1):** 5 penetration lines (1F-R26FA0D, GF-R8496F0, GF-RA3AD49, GF-RD36087,
GF-RDBD4F9) read 1 .. 1 pcs (a printed FD, no W.C. in the room): MEASURABLE_NOW, not DESIGNER. By cause DESIGNER 46 ->
41, MEASURABLE_NOW 8 -> 13, NEEDS_OWNER_RULE 3 (Q-34 parked), NO_PHYSICAL_ELEMENT 1. The 5 MISSING (pantry GF-RC99C2A):
doorway 0.200 m2, transition 1 pcs, termination 4.500 lm, penetration 1 pcs (MEASURABLE_NOW); transition m2 HELD
(DESIGNER, Q-35 C). T-730 already maps the 5 penetration rows as CHANGE to 1.0: no hub change, census wording only.

## (c) D-41

HELD 0 .. 13.335040 m2 (loop 51.898 m) beside the six released wall-upturn hosts (9.148 m2, all LIVE on V3.0.73);
designer item 9 (D-41). Low 0 is a physical alternative (membrane on the fill), never a default.

## Engine vs freelancer; who is right

Roof membrane: engine released 115.832 vs own 115.656474 .. 115.813974: ENGINE_WRONG (+0.018 m2, chord deduction,
cause exact). Freelancer one roof line 285.00 m2 (T-071): scope gap unchanged (Q-34 top roof, dome footprints; T-321
decomposition), UNRESOLVED vs freelancer. No released quantity moved.

## Lessons-register row (proposed, ERS s.7)

2026-11-12 | a released roof membrane sat 0.018 m2 above its own band and the only path to correct it is a downgrade
record that may not carry a number | the band was measured by a buffered flood fill whose ends could not be tied to
named lines, and the class of the after-state was never stated | rebuild the face from its named carrier lines for the
record's evidence; a record only moves the line to HELD; the package writes the measured band, never a chosen end; a
raise is never a downgrade (every villa) | tests/t734_wp_h4_evidence (normal: L face, band reading, disc, eligibility,
draft, after-state; adverse: parallel / odd / self-crossing carriers, mm as m, NaN, inverted band, promotion state,
quantity in a record, stale record, raise as downgrade, HELD as 0, missing room prefix) | PROPOSED.
