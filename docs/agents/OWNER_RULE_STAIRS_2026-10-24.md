# Owner stair preferences and construction method (owner, main chat, 2026-10-24)

Recorded by the main chat from the owner's words in his chat (2026-10-24, with a site photograph and two reference
sheets). It becomes a NEW rule version (URBAN_RULES 1.7.0 record UP-STAIR-016); UP-STAIR-015 (1.6.0) and every
earlier stair record stay unchanged. Agents never answer section 4 themselves.

## 1. Owner words (essentials, quoted)

- Terminology: القائم Riser (vertical step height); النايم Going / tread (horizontal step depth); البسطة Landing;
  بيت الدرج Stairwell; منسوب الخرسانة structural concrete level; منسوب التشطيب finished floor level (FFL); سماكة التشطيب
  finishing build-up; درج رخام marble stair finishing; بروز الدرج stair projection beyond the intended alignment.
- "Owner-preferred finished riser: 15–17 cm." "Owner-preferred going: 28–30 cm, replacing the previous fixed 30 cm
  preference." "These are design preferences, not universal defaults and not permission to overwrite approved
  drawings or mandatory requirements." "Project-specific drawings take precedence over generic preferences, subject to
  conflict reporting and applicable requirements."
- Construction method: "The structural first and last risers may differ from intermediate structural risers because
  the ground-floor and upper-floor finishing build-ups affect the finished step heights." With R = intended finished
  riser, F0 / F1 = ground / upper floor finishing build-up above its structural slab, Si = finish above structural
  tread i: first structural riser = R + F0 − S1; intermediate i = R + S(i−1) − Si; last = R + S(last) − F1.
  Examples (F0 = F1 = 10 cm, stair finish omitted): R 15 -> 25 / 15 / 5 cm; R 16 -> 26 / 16 / 6 cm. "Do not hardcode
  25/15/5 or 26/16/6." "Do not assume every project has 10 cm floor finishing or identical floor and stair finishing
  thicknesses. Read the plans and approved details; otherwise mark the input as requiring confirmation."
- Fit: count actual goings, not risers; "changing 25 actual goings from 30 cm to 28 cm reduces horizontal run by 50
  cm. But if a flight has 25 risers and only 24 goings, the reduction is 48 cm." "Never silently change an approved
  stair design. Report alternatives for designer approval." The site photograph is an example of a stair / wall
  coordination problem, "not as dimensional proof of a particular defect".
- BOQ: concrete, reinforcement, formwork, marble treads and risers (m2 and pieces), landing marble, nosing, handrail
  along the slope by side, from ONE verified stair geometry; never structural and finished dimensions mixed; a landing
  never both a tread and a landing.

## 2. Sign convention, checked by the main chat (2026-10-24)

Concrete level under each finished surface = finished level − its finish. Riser i (from surface i−1 to surface i)
concrete height = (FFL_i − S_i) − (FFL_{i−1} − S_{i−1}) = R + S_{i−1} − S_i; surface 0 is the lower floor (S_0 = F0),
the last surface is the upper floor (S_n = F1). So first = R + F0 − S1, last = R + S_{n−1} − F1 ("S(last)" is the
finish on the last TREAD, below the upper floor). Reproduced by the existing frozen engine function
stair_riser_schedule.first_last: R 150, F0 = F1 = 100, S 0 -> 250 / 50; R 160 -> 260 / 60; with S 30 -> 220 / 150 / 80;
a landing finished 50 between treads finished 30 gives 140 then 180 (stair_riser_schedule.schedule).

## 3. Relation to existing rules (what changes)

| Existing | Says | Effect of this owner rule |
|---|---|---|
| UP-STAIR-002 (S-1 DRAWING GOVERNS) | drawn counts govern, rule is a check | unchanged; the new ranges are checks on drawn stairs |
| UP-STAIR-015 (1.6.0) | max riser 0.16 m, tread default 0.30 (0.28 - 0.30 allowed) | check limits become finished riser 0.15 - 0.17, going 0.28 - 0.30 (new record UP-STAIR-016) |
| UP-STAIR-009 | 0.155 - 0.165 diagnostic sanity range | stays a diagnostic range (not a limit); question in 4 |
| UP-STAIR-003 / -006 | visible riser = riser less tread build-up; tread marble 0.030 m unless drawing / spec / owner | unchanged; 0.030 is the tread finish S unless the drawing says otherwise |
| S-3 | floor_height = FFL to FFL | unchanged; the structural slab-to-slab height is derived, never used as the riser basis |

## 4. Open for the owner (asked 2026-10-24 by the main chat; agents do not ask again)

- S-4 Undrawn stair design values: when the drawings do not draw the stair (owner method, S-1), which design values
  replace the single defaults 0.16 m / 0.30 m: (A) keep 0.16 max riser and 0.30 going as the design values, the new
  ranges only as checks; (B) max riser 0.17 and the going chosen inside 0.28 - 0.30 to fit the available length, all
  alternatives reported; (C) report every count / going combination inside the ranges and leave the choice to the
  designer, quantities HELD until chosen. Main chat recommendation: (C) for design, (A)'s values only as a
  PROVISIONAL planning figure, because a range is not a value.
