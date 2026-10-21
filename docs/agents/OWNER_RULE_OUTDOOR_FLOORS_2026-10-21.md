# Owner rule: outdoor floor finishes (owner, main chat, 2026-10-21)

Owner's words, unchanged: "Outdoor court area انترلوك for chalet, but houses outdoor areas sides and infront flooring
area for ceramic, stairs outside is marble"

It answers OQ-04 (option A: outside finishes are in the BOQ) and becomes a NEW rule version in the rule library (never an
edit of an existing file).

| Project type | Outdoor area | Finish | Status |
|---|---|---|---|
| Chalet | outdoor court (open court areas) | interlock paving (انترلوك) | owner rule |
| House / villa | outdoor side areas and the front area | ceramic flooring | owner rule |
| Any | outside stairs (steps outside the house) | marble (as UP-STAIR-001; geometry by UP-STAIR-002 and the owner stair rule) | owner rule |

How agents apply it:

- The project type comes from the project facts (Alsenan is a chalet: Drive folder "Alsenan chalet project"); a project
  whose type is not recorded is HELD on this rule, never guessed.
- Areas are the measured outdoor areas (T-153 / T-157 classification: open to outside air under Q-67 A); the finish line
  carries the area, the rule id and the evidence status of WORKFLOW_CONTROLS section 5.
- A deduction for elements standing on the area (a planter, a column footprint, the pool water) follows the existing
  measured geometry; the pool water is never a floor.
- Still open (OD-1, asked by the main chat; agents do not ask again): in a chalet, are the covered porch, the pool deck
  and the side passage interlock like the court, or ceramic like house side / front areas? Until the owner answers,
  those three are HELD; the open court areas are interlock.

Alsenan effect (areas measured by T-153, waiting for the Checker where not yet verified): west court 138.761 m2 including
the porch 19.181 m2 and a 3.360 m2 element footprint, north court strip 21.348 m2 (Checker re-measured 21.021, split
HELD), pool deck 7.605 m2, side passage 5.640 m2; the freelancer prices "yard" 151.80 m2.

## Owner additions (2026-10-21, main chat; his words: "side walk court will be on the right side next to the pool
(Porcelain because sides will always be porcelain or ceramic no interlock) its considered part of the house. so 150 times
the length 1597 for side. (look for it to learn) pool deck not sure yet. What covered porch not sure. show me, if its the
seating area next to door it could be wood or ceramic or marble with the stairs")

- SIDES ARE NEVER INTERLOCK, in any project type: a side walk / side strip along the house is porcelain or ceramic and
  counts as PART OF THE HOUSE. Interlock is for the open court only.
- Alsenan side walk (the strip between the north neighbour wall and the house block with the stair, the W.Cs, the master
  bedroom and the pool; GF plan): owner manual method = printed width 1500 x printed block length 15970 (the DXF dimension
  15970 runs x -145040 .. -129070 at y -797705; 1500 dimensions on the same strip) = 1.50 x 15.97 = 23.955 m2, porcelain.
  T-153 measured that strip as 21.348 m2 (Checker 21.021): the 2.6 m2 difference must be explained term by term
  (what the drawn strip excludes: the pool frame, a door swing, a step, the strip ends) with both figures kept, the
  owner's manual method beside the drawing-derived one.
- POOL DECK: HELD (owner not sure yet).
- COVERED PORCH (GF, in front of the main entrance door with the entrance steps, under the 1F; about 4.60 x 4.10 =
  19.181 m2): shown to the owner on a marked plan; finish OPEN (wood, ceramic, or marble together with the stairs):
  HELD until he decides. The entrance steps themselves are marble (outside stairs).
- Side passage 5.640 m2 (between annex and house): a side area, so porcelain / ceramic by the sides rule, part of the
  house (consistent with Q-67 A exterior classification for walls; its floor finish is porcelain / ceramic, not interlock).

## Owner decisions after the renders (2026-10-21 23:20, main chat; his words: "you are correct, but interlock is cheaper
and it is available, this stone is not available at this time" / "in plan its the level and not up the stairs. lets
measure the area and can decide later for the kind and price")

- COURT = INTERLOCK, confirmed for Alsenan even though the designer's renders show natural-stone crazy paving: the owner
  chooses interlock because it is cheaper and available and the rendered stone is not available now. General rule: a
  render shows design intent; when the owner sets a different, available material for the BOQ, the owner's choice governs
  and the line records "owner choice, differs from render".
- COVERED PORCH: on the plan it is AT COURT LEVEL, not up the entrance steps (the render's raised terrace does not govern).
  MEASURE its area as its own line (about 4.60 x 4.10 = 19.181 m2, to be re-measured from the plan and kept separate from
  the court interlock area so it is never counted twice); the finish KIND and PRICE stay open (owner decides later):
  quantity measured, material HELD.
- The entrance steps stay marble (outside stairs); the pool deck stays HELD.
