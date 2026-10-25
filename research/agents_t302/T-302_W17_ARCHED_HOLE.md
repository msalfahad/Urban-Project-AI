# T-302: the developed hole W17 leaves in the curved 1F wall (Alsenan; every villa with an arched opening in a curved wall)

Research only (R-T302-1, `t302_arched_hole.py`): no engine module, rule or knowledge version file, candidate line,
window line or released line changed. Released default stays V2.9 + route G. T-244 (lane I) consumes this ledger.
Source: own read of P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55); every value below is RELATIVE (plan about
the curved bay's arc centre, elevation about its crown axis and the +5.50 mark). `t302_alsenan.py --extract <dxf>`
re-reads all 58 values by handle and fails on any difference (EXTRACT OK on this run).

## 1. Physical element first

A 0.20 m curved wall (two coaxial arcs) bulging WEST into 1F-11: room face BD2 r 2.135 (convex to the room, the glass
line the room touches, T-250), exterior face BCE / BCD / BD0 r 1.935 (concave to the exterior, east, where the NW
elevation looks from). The hole runs between two jamb lines that are radial in plan (BD9: 135.1898 deg at both radii;
BD7: 223.4682 at r 2.135 -> 223.3295 at r 1.935) from the +5.50 floor to an arched head. The developed hole on a face of
radius r is the integral of the head height along that face's developed arc between the jambs.

## 2. Registration of plan and elevation (on drawn and printed marks, no scaling)

- Elevation u axis = plan +y about the arc centre (the NW elevation is an orthographic view along plan x).
- The plan exterior-face jambs project to u = 1.935 sin 223.3295 = -1.3278 and 1.935 sin 135.1898 = +1.3637; the
  elevation draws jamb lines 2A44 / 2A46 at exactly those u (residual 0.0000 mm both), and PRINTS the chain
  2D61 201.9 | **2D53 2691.5** | 2D46 166.0 between them (2691.494 = 1.3637 + 1.3278).
- The jamb lines rise from the +5.50 mark (level insert 2888 at height 0; 2886 +1.00 at -4500: vertical 1 : 1) and END ON
  the arch chain 2738 .. 2741 (tops 2.2190 / 2.1676 = the chain's height at those u, 0.0000 mm).
- **Correction to the T-292 / F-T292-02 reading:** the chain's ends at u +-1.5297, height 1.350 (lines 2784 / 2565 below
  them) are NOT the window's jambs: they are the projected ENDS OF THE CURVED BAY on the exterior face (BCD start /
  BD0 end, r 1.935 at 127.7635 / 232.2365 deg: 1.935 sin 127.7635 = 1.5297, 0.00 mm), dimensioned separately as the
  piers 201.9 / 166.0. The 1.350 "springing" lies outside the hole; at the hole's own jambs the head is 2.168 / 2.219.
  This also explains T-292's open note "jamb x 1.5297 is not 2.135 sin(half angle) = 1.487": the two are different
  points of the wall.

## 3. Developed hole per face (W17_HOLE_LEDGER_T302.csv)

| Face | r m | jamb to jamb developed m | hole m2 | status |
|---|---|---|---|---|
| EXTERIOR (the face the elevation shows) | 1.935 | 2.9767 | **8.1434** (projected 7.4223) | DRAWING-CONFIRMED |
| CENTRELINE (blockwork) | 2.035 | 3.1331 | 8.4598 .. 8.5699 | HELD (BOUNDED) |
| ROOM SIDE (1F-11 plaster / paint) | 2.135 | 3.2895 | **8.7414 .. 8.9965** | HELD (BOUNDED) |

Rectangle caps (developed width x crown 3.000): 8.9300 / 9.3992 / 9.8685; every value below its cap.

Why the inner faces are a pair, not one number: the elevation draws the head on the exterior face only. Through the
0.20 thickness the soffit can run RADIALLY (each radial line at one height: the same h(angle) on both faces; consistent
with the drawn radial jambs) or PRISMATICALLY (along the view direction: the room face reads the drawn head at its own,
wider projection). RADIAL gives the room side 8.9965, PRISMATIC 8.7414. No section or interior elevation draws the W17
soffit (T-238 A5), so the face stays HELD (BOUNDED) between the two, with the named item "head soffit through the wall
thickness not drawn"; never a midpoint. Engineering reading (recommendation for the Checker / designer list): RADIAL,
because the jambs are drawn radial and a prismatic soffit would drop the room-side head at the jamb from 2.17 to 1.77 m
over 0.20 m (a warped soffit nothing on the drawings shows).

Reconciliation in m2 by cause (room side):
- projected over the drawn jambs 7.4223 -> developed on the exterior 8.1434 (+0.7211: ds / du = 1 / cos(angle), up to
  1.39 at the jambs; mean factor 1.0972);
- exterior 8.1434 -> room RADIAL 8.9965: x 2.135 / 1.935 = 8.9851 (+0.8417, longer arc) + the room face's wider south
  jamb angle (BD7 is 0.139 deg off radial: 223.4682 vs 223.3295) +0.0114;
- room PRISMATIC 8.7414 = RADIAL - 0.2551 (the room face reads the head at |u| up to 1.5047 instead of 1.3637, lower).
- Against the Checker's F-T292-02 bounds: 8.1338 / 8.1239 ("elevation projection", "on the outer face") was the whole chain
  INCLUDING the bay-end piers (u +-1.5297): it coincides with the exterior developed hole only by chance (8.1338 vs
  8.1434); the true elevation hole is 7.4223. Upper bound 9.858 (w x crown) holds: 8.9965 < 9.858.
- Not the hole: the window line's 3.29 x 3.00 = 9.870 m2 (Q-76 A, a WINDOW measure, unchanged; check refuses it as a
  deduction, `WINDOW_AREA_AS_HOLE`), and the projected 7.4223 (`PROJECTED_AS_DEVELOPED`).

## 4. Per trade

- **Plaster / paint, 1F-11 room side** (LINE_1F11_T302.csv): T-292's face ledger, 8 VERIFIED faces 59.4510 + the W17
  piece gross 3.286 x 3.35 = 11.0081 minus the room-side hole: piece **2.0116 .. 2.2667**; line
  **61.4626 .. 61.7177 m2** per code (T-292 60.6011 .. 66.0230 reproduced first, residual 0.0000; Checker bound
  60.6011 .. 62.3352: inside). Released candidate 59.4511 is LOW by 2.0115 .. 2.2666 m2 (3.4 .. 3.8 %): ENGINE_WRONG
  to release (T-244 replaces it). Whole-trade per-code HELD totals in T-292 s.8 move by lo +0.8615 / hi -4.3053.
  Named residual (not this task's): the face piece uses T-128's room-side length 3.286; the hole spans the BD2 arc
  3.2895 (T-250: -0.0035 m, about 0.008 m2 at the jamb heads).
- **Exterior face** 8.1434 DRAWING-CONFIRMED: for an exterior plaster / Sigma line on the bay's concave face if one is
  formed (not established here which line carries it).
- **Blockwork, centreline** 8.4598 .. 8.5699: the merged registers (T-291 s.4) carry W17 as NOT_APPLICABLE (glazed
  host, nothing built). The elevation shows wall around the hole (piers 0.202 / 0.166 projected, the head spandrels up
  to the face top): whether that curved wall is a masonry quantity is a register question for T-279 / the Lead; this
  task changes no blockwork figure.
- Jamb reveals (radial, 0.20 deep) are a finish surface of their own; not measured here (no line asks for it).

## 5. Statuses, verdicts, lessons

- EXTERIOR hole DRAWING-CONFIRMED (plan and elevation register on printed / drawn marks to 0.0000 mm); CENTRELINE and
  ROOM SIDE HELD (BOUNDED) on the soffit; window line unchanged (Q-76 A).
- Verdict proposals: 1F-11 plaster / paint candidate 59.4511 ENGINE_WRONG (deducts 3.286 x 3.35 = 11.008, more than the
  rectangle to the crown); T-292 / F-T292-02 lower bound (springing 1.350 across the full width) superseded by the drawn
  jambs (FINDING: the arch ends are the bay's ends). Freelancer: one height per storey, no room line (T-292 s.5): not
  comparable per room.
- Lesson (ERS s.7, proposed): "on a curved wall, an elevation's outermost vertical lines may be the bay's ends, not the
  opening's jambs: register every elevation jamb on the plan face it projects from before reading a springing" | scope:
  every elevation of a curved wall | rule R-T302-1 | tests/t302_arched_hole | OPEN until T-244 consumes it.

## 6. For the Checker (re-measure on one face)

Exterior face: BCE r 1935 between BD9 135.1898 and BD7 223.3295; head chain 2738 .. 2741 (13 points, crown 3000 at u 0);
jambs 2A44 / 2A46; printed 2D53 2691.494. Hand route: split at the 12 chord vertices, h(phi) = chain height at
u = 1935 sin(phi), integrate h * 1.935 dphi: 8.1434 m2. Tests: tests/t302_arched_hole (rules on hand villa V-302:
semicircle on a 3.00 m chord in a 4.00 m wall, 6.6751 m2 by binomial series; adverse: projected, window area, over the
rectangle, missing radius, unregistered, prismatic outside the head, mirror / rotation / mm).
