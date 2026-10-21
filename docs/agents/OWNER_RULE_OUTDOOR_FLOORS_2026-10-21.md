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
