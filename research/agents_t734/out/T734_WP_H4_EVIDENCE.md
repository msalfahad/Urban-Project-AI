# T-734 waterproofing H4 evidence on ARCH_TAKEOFF_V3.0.73

## (a) Roof membrane L-636fd3ff1784a12e653b: downgrade-record evidence

R-T734-2: the face rebuilt from its 8 named carrier lines (vertex = carrier x carrier, shoelace); independent of the T-321 / T-691 buffered flood fill.

| carrier | handles | kind | edge m (D-band ring) |
|---|---|---|---|
| C1 | 12E6 + 1280 + door gap 1.000 (1280 east end .. 1281 west end) + 1281 | H | 8.175 |
| C2 | 1291 (2F block east wall outer face) | V | 6.600 |
| C3 | 1278 (north parapet inner face) | H | 6.570 |
| C4 | 12A7 (east parapet inner face) | V | -11.600 |
| C5 | 1285 (south parapet inner face) | H | -18.870 |
| C6 | 12C9 (west parapet inner face) | V | 7.100 |
| C7 | 12B9 (west-wing north parapet inner face) | H | 4.125 |
| C8 | 12E2 (layer D band line, D-band reading) / the 2F west wall outer face (wall-face reading) | V | -2.100 |

| component | m2 |
|---|---|
| face, D-band reading (C8 on 12E2) | 146.374500 |
| face, wall-face reading (C8 on the 2F west wall face) | 146.532000 |
| D-BAND strip 0.075 x 2.100 (12E6 x 12E2 below C7) | 0.157500 |
| dome 12EB true pi r^2 | 15.359013 |
| dome 2F33 true pi r^2 | 15.359013 |
| each dome as the engine's 105-chord polygon | 15.349849 |

Own band 115.656474 .. 115.813974 m2 (T-321 115.65646 .. 115.81396: low 0.000014, high 0.000014). Released 115.832 = the engine closed the face on the 2F wall face (wall-face reading) and deducted 105-chord polygons: 146.532000 - 2 x 15.349849 = 115.832303 (residual -0.000303, rounding). Above the high end 0.018026 m2 (0.015565 %): ABOVE_BAND.

Domes tangent to the parapet faces: {'12EB': '12C9 (west parapet, clearance 0.0000 m)', '2F33': '12A7 (east parapet, 0.0000 m)'}.

D-BAND 0.157500 m2 (0.135994 %): 12E2 continues a stepped layer-D profile on the 2F west wall (12E0 / 12DF / 12DD / 12DC / 12D3 / 12CB / 12D5 / 12D6 / 12D8 / 12D9 / 12DB: 25 / 50 / 75 mm steps off the wall face) drawn at the plan cut: a projecting facade feature 0.075 proud over 2.7684 m, not a base. Layer D also holds elevation titles; no text, hatch, schedule or detail names the feature. Alternatives: built before the membrane (a masonry pilaster / thickened wall): the membrane stops at its face and turns up there -> D-band reading (low) | applied after the membrane (cladding / moulding): the membrane runs to the wall face under it -> wall-face reading (high). Settled by: an elevation / wall section or finishes schedule naming the 2F west wall feature (designer item, proposed for DESIGNER_QUESTIONS; ERS s.2.7 not met: no owner rule).

Draft record (Checker types it with `downgrade-add`; the tool binds project, revision set and line content):

```
{
 "candidate_version": "ARCH_TAKEOFF_V3.0.73",
 "line_ids": [
  "L-636fd3ff1784a12e653b"
 ],
 "unit": "m2",
 "engine_qty_binding": 115.832,
 "state": "HELD",
 "basis_label": "UNSUPPORTED BASIS",
 "reason": "UNSUPPORTED BASIS: the released +9.70 roof membrane 115.832 m2 lies 0.018026 m2 ABOVE its own same-basis band 115.656474 .. 115.813974 m2: the trace deducts the two dome CIRCLEs 12EB / 2F33 (r 2.211092 m) as inscribed 105-chord polygons (1 mm sagitta), 15.349849 instead of 15.359013 m2 each (under-deduction 0.018329 m2, R-T691-1); the face is closed on named lines (wall-face reading 146.532000 m2, D-band reading 146.374500 m2: the 0.075 layer-D feature at the 2F west wall foot is unprinted, D-BAND 0.1575 m2). Downgrade only: the line goes HELD; the candidate figure stays in the audit rows; the H4 package then carries the drawing band (R-T734-1 c), never a chosen end",
 "evidence": [
  "Alsenan chalet project / P7757.dxf (2F plan, +9.70 roof) CIRCLE 12EB and CIRCLE 2F33 = radius 2211.0915 mm each (pi r^2 = 15.359013 m2; 105-chord polygon 15.349849 m2)",
  "Alsenan chalet project / P7757.dxf (2F plan) LINE 1281 / 1291 / 1278 / 12A7 / 1285 / 12C9 / 12B9 / 12E2 / 12E6 / 1280 + door gap 1.000 = closed face 146.374500 m2 (12E2) .. 146.532000 m2 (2F wall face), perimeter 65.140 m",
  "ARCH_TAKEOFF_V3.0.73 L-636fd3ff1784a12e653b = 115.832 m2 = 146.532000 - 2 x 15.349849 = 115.832303 (3-decimal rounding 0.000303)"
 ]
}
```

Which figure: the record keeps NO figure of its own (owner 2026-10-24 23:57: never a Checker measurement). It binds the released 115.832 (engine_qty), which stays only in the audit rows ('Audit (unsupported basis)'). The line becomes HELD; the H4 package then writes the drawing band 115.656474 .. 115.813974 m2 (both ends measured; neither chosen). 115.813974 is NOT released: its high end rests on the unprinted D-BAND reading.

Upturn L-5ce5ba49792e8f9d1f6f: 92.922 -> 92.925396 lm. NOT A DOWNGRADE (R-T734-1 d): 92.922 -> 92.925 raises a released value; a Gate B change with its own re-measure, needing no record; the T-730 H4 blocker 'WAITS T-734' on this row can be lifted. Open: a +0.000750 lm residual between the released 92.922 and the 105-chord reconstruction 92.921250 is not named in this run (above the 0.0005 rounding half-step): the Gate B re-measure of the upturn change names it before wiring.

Rolls L-2ecffd1f396ede3b5eb4 17 pcs: not named by the record (another line, unit pcs): the procurement count is KEEP in T-730; the strip count's sensitivity to the 0.075 D-BAND and to 0.018 m2 was not re-run here (the roof layout inputs live in the engine trace).

## (b) Census on V3.0.73 (R-T734-3)

WP lines 160 (V3.0.70) = 160 (V3.0.73), ids equal True, entries differing 0; 53 HELD + 5 MISSING; stale 0, gone 0.

By cause T-710 {'DESIGNER': 46, 'MEASURABLE_NOW': 8, 'NEEDS_OWNER_RULE': 3, 'NO_PHYSICAL_ELEMENT': 1} -> restated {'DESIGNER': 41, 'MEASURABLE_NOW': 13, 'NEEDS_OWNER_RULE': 3, 'NO_PHYSICAL_ELEMENT': 1} (moved: 5).

| key | code | unit | V3.0.73 | restate | cause | after |
|---|---|---|---|---|---|---|
| L-9971bd68a5150abebe0a | FIN.WP.PENETRATION | pcs | HELD | LIVE | MEASURABLE_NOW | 1 .. 1 pcs (FD 1 firm + W.C. 0 open) |
| L-6375385673176b8b2c9c | FIN.WP.PENETRATION | pcs | HELD | LIVE | MEASURABLE_NOW | 1 .. 1 pcs (FD 1 firm + W.C. 0 open) |
| L-229e7bf9e837e1d838bd | FIN.WP.PENETRATION | pcs | HELD | LIVE | MEASURABLE_NOW | 1 .. 1 pcs (FD 1 firm + W.C. 0 open) |
| L-a4bbc2efdb8425554344 | FIN.WP.PENETRATION | pcs | HELD | LIVE | MEASURABLE_NOW | 1 .. 1 pcs (FD 1 firm + W.C. 0 open) |
| L-0db07ac89503dd3f5980 | FIN.WP.PENETRATION | pcs | HELD | LIVE | MEASURABLE_NOW | 1 .. 1 pcs (FD 1 firm + W.C. 0 open) |
| L-2361d6ec13c952bd2ae3 | FIN.WP.ROOF | m2 | HELD | LIVE | MEASURABLE_NOW | {"origin": "overlay op", "source": "T-529 R-WP-APPL-EXPOSED-2b (MERGED 5f775ba6): ledge 0. |
| L-d7d1bf8c5991ccf69ea2 | FIN.WP.ROOF_UPTURN | lm | HELD | LIVE | MEASURABLE_NOW | {"origin": "overlay op", "source": "T-522 / T-529 (MERGED 4777890b / 5f775ba6): ledge wall |
| L-1954878bb02c91139e1b | FIN.WP.ROOF_UPTURN | lm | HELD | LIVE | MEASURABLE_NOW | {"origin": "overlay op", "source": "T-522 (MERGED 4777890b): window run upturn 0.500002 lm |
| L-8090ff20f2b547d1bc96 | FIN.WP.WALL_UPTURN | m2 | HELD | LIVE | MEASURABLE_NOW | {"detail": {"doors_lm": "1.000000", "held_terms": ["W10 sill not printed: 1.000000 m exclu |
| MISSING:FIN.WP.DOORWAY[m2]/DOOR:D-GF-07-PANTRY/THRESHOLD_FLOOR | FIN.WP.DOORWAY | m2 | NO LINE | MISSING | MEASURABLE_NOW | 0.200 |
| MISSING:FIN.WP.DOORWAY_TRANSITION_NR[pcs]/DOOR:D-GF-07-PANTRY/TRANSITION | FIN.WP.DOORWAY_TRANSITION_NR | pcs | NO LINE | MISSING | MEASURABLE_NOW | 1 |
| MISSING:FIN.WP.TERMINATION[lm]/GF-07:OPEN_SIDE_DINING/MEMBRANE_EDGE | FIN.WP.TERMINATION | lm | NO LINE | MISSING | MEASURABLE_NOW | 4.500 |
| MISSING:FIN.WP.PENETRATION[pcs]/GF-07/FLOOR_PENETRATIONS | FIN.WP.PENETRATION | pcs | NO LINE | MISSING | MEASURABLE_NOW | 1 .. 1 (T-691: 1 FD, no W.C.) |
| MISSING:FIN.WP.DOORWAY_TRANSITION[m2]/DOOR:D-GF-07-PANTRY/TRANSITION | FIN.WP.DOORWAY_TRANSITION | m2 | NO LINE | MISSING | DESIGNER | None |

## (c) D-41 sunken panels

HELD 0 .. 13.335040 m2 (loop 51.8980 m); hosts 1F-RED23B8 L-a93486d24647a9e14445 1.36 LIVE, 1F-R52AC05 L-ace6533512ada47d1352 1.148 LIVE, 1F-R48AA46 L-ba15212ec9887e6d4f73 1.64 LIVE, 1F-R8BDA49 L-6e6daedebef2db6a83bd 1.64 LIVE, 1F-R48CDA5 L-60f100105399a9bdfb08 1.58 LIVE, 2F-RE83BED L-b842beb71b67af783cd7 1.78 LIVE (sum 9.148000 m2). Designer: DESIGNER_QUESTIONS.md item 9 'Sunken wet-room slab panels: membrane position' (D-41): membrane on the structural slab (tray: + loop x d) or on the fill under the tile (+0); d unprinted, bounded by the boundary beams (d_max 0.24 / 0.34 m). no candidate line: a HELD component beside the six released wall-upturn hosts (all LIVE on V3.0.73); low 0 is a physical alternative (membrane on the fill), never a default; nothing moves in this task.

Released quantities moved: none (research, unwired; V2.9 + route G unchanged).
