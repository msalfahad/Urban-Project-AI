# T-178 lessons into rules and tests (ENGINEERING_REASONING_STANDARD section 4 B / C)

Worker 3 (lane I), 2026-10-22. Research record for the Lead, nothing wired, no engine module edited, no BOQ quantity
changes (V2.9 + route G and every V3.0.x candidate unchanged by construction: the only new files are this folder and
`tests/t178_lessons`). Every lesson below comes from a merged, Checker-verified piece; the corrected quantity (section 4
A) already lives in that piece. This task adds what section 4 B / C asks for: a general rule (scope and provenance) and
a regression test with a normal and an adverse case on a synthetic non-Alsenan fixture ("Villa Q"), plus a
deliberately broken variant the test rejects.

No new rule-version file is created. Lessons 1 and 2 are already governed by owner-approved method rules
(URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1, URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1, rules/methods/
URBAN_METHOD_REGISTER_V3.json): the test pins them. Lessons 3-7 are engineering conclusions verified by the Checker,
not owner rules: per the task row they stay research records here until the Lead accepts them (a rule CHANGE would be a
new rule / knowledge version).

## The seven lessons

| # | Physical element | Discrepancy resolved (merged piece) | General rule (scope; provenance) | Test (normal / adverse / broken) |
|---|---|---|---|---|
| 1 | Ring beam round a circular slab opening (dome) inside a bay framed by straight beams | full annulus counted as ring concrete double counted the parts lying in the straight beams (T-160, b5da75b) | Ring concrete = annulus INSIDE the bay (between the inner faces of its framing members) x depth; the parts in a framing member belong to that member, past its far face to the next panel; a ring with no printed depth is HELD (any villa; owner Q-44 A, URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1) | `test_l1_*`: hand 3.872977 m2 / 1.936488 m3 (rot 0 / 30 / -73 deg, mm); adverse tangent ring = full annulus 3.864159, corner inside the ring refused, no depth HELD; broken full annulus 2.026327 m3 rejected |
| 2 | Column concrete above the neck, per storey | one global deduction (interval - 0.75) or the deepest member whatever its side of the slab (T-119 r2, 0f32ff8) | Height = storey interval - hang of the deepest member framing into THAT column (downstand: its depth; upstand: slab t only); slab t when none; side of the slab not shown -> HELD range between both readings; joint = A x (D_ctrl - t) (any villa; URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1) | `test_l2_*`: 3.00 / 3.00 (upstand tank wall 1.00 ignored) / 3.42 (none); 0.270 m3, joint 0.0378; adverse side unknown HELD 2.70 .. 3.15, missing depth / interval HELD; broken global 0.75 (2.85) and any-side (2.60) rejected |
| 3 | Facade face of an upper storey standing on a lower roof | the face measured from its own floor level lost the band between the lower roof and that floor (T-159, 349251f; Alsenan +4.080 m2) | A face portion whose lower plate is a roof starts at THAT roof's printed level; flush portions start at their floor; an unprinted lower-roof level makes that face HELD, never its floor (any villa; T-159 composer `house_facade`) | `test_l3_*`: 1F east 34.40 m2, 1F total 108.40 (quarter turn, mirror, mirror + -37 deg); adverse level None -> HELD, other faces 74.00; broken from-floor 29.60 rejected |
| 4 | Blinding under a ground beam / strap ending on a footing with no outline | the HELD lower bound was the unmerged strip, above the hand value (T-142 D3, 5de8657: 5.724 vs hand 5.189 m3) | A HELD range must CONTAIN the physical value: high = strip to the unbound footing's centre; low = that footing at the largest extent the evidence allows (its label search window); no window -> low NOT_ESTABLISHED (None), never the high value, never 0 (any villa, any held range) | `test_l4_*`: both outlined 0.2025 m3; unbound HELD 0.1935 .. 0.2340 contains it (m and mm); adverse no window low None; broken low = high 0.2340 rejected |
| 5 | Any Gate B diff, census or scoreboard against "released V2.9 + route G" | two diffs compared against different "released" runs (one with the route G profile, one without) (T-140 -> T-165, 37124da) | Every comparison names its pinned baseline spec; a spec states every choice (null = "none", a missing key is refused); a comparison reports every configuration difference before any figure (every villa; tools/release_baseline.py) | `test_l5_*`: valid spec, profile null valid, profile key missing refused; compare of manifests differing only in the profile names `pinned_files`; broken figures-only comparison sees nothing |
| 6 | Partition wall at a free-end doorway with a drawn jamb nib | the nib went into the doorway, the physical blockwork lost it (T-169, c8a524f; GF-W29 0.500 vs 0.553 m) | A nib drawn with both faces on the wall layer from the face of the wall across, >= 0.05 m (L-P9-04), is WALL: doorway = gap - nib; shorter = drafting artefact, listed, never dropped (any villa; MASONRY_CENTRELINE_V2 `_jamb_stub`) | `test_l6_*`: boundary nib exactly 0.050 -> WALL, doorway 0.85, physical 2.55 (T-169's own tests use 0.06 / 0.03, not the boundary); adverse 0.045 listed, physical 2.50; broken gap-as-doorway 2.50 rejected |
| 7 | Covered porch: its floor and its soffit | one area used for both surfaces (T-157 / T-121: porch floor 19.220 vs soffit 19.181 m2 on the development villa, different boundaries) | Floor and soffit of a covered outdoor space are two surfaces measured from their own boundaries (floor: ground-plan walls, steps, landing, minus what stands on it; soffit: slab edge / beam faces, minus beam soffits and voids); the difference is named by component and re-adds exactly (any villa; T-157 report) | `test_l7_*`: floor 19.64, soffit 17.25, floor-only 2.85, soffit-only 0.46, re-add exact; adverse flush slab over the same outline equal by geometry (18.40); broken soffit := floor (+2.39 m2) rejected |

## Mutation record (each test shown failing on a broken variant, then passing on the merged code)

Run on agents/task-T-178 (Python 3.11.17, `bash scripts/agent_env.sh pytest --tree task-T-178 tests/t178_lessons`):
merged code 32 passed. Temporary mutations (reverted with `git checkout`, nothing committed): dome_ring `a_ring =
annulus` -> 4 L1 tests FAIL; column hang ignores the slab side -> 2 L2 FAIL; house_facade bottom = floor -> 5 L3 FAIL;
held low = high -> 3 L4 FAIL; JAMB `>` instead of `>=` -> L6 threshold FAIL; release_baseline without
`pinned_files` in CONFIG_FIELDS and without `profile` in REQUIRED_KEYS -> 2 L5 FAIL; soffit := floor -> L7 FAIL. After
the revert: 32 passed.

## Finding for the Lead (not changed here)

`research/agents_t159/t159_sides.py::house_facade` defaults a missing `lower_roof` KEY to the floor level
(`fl.get("lower_roof", fl.get("floor"))`); only an explicit `None` makes the face HELD. When this composer is wired
(lane I, V3.0.x), the T-186 default guard should apply: a face COVERED by a lower plate with no lower-roof level stated
must be HELD, not measured from its floor. Test L3 pins the explicit-None behaviour only.

## Proposed lessons-register rows (ENGINEERING_REASONING_STANDARD section 7; the Lead copies accepted rows)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-22 | Dome ring concrete double counted with the straight beams (T-160) | full annulus taken as the ring | ring = annulus inside the bay faces x depth; member parts to the member (any villa) | T-178 L1 | rule pinned (owner Q-44 A), test added |
| 2026-10-22 | Column heights off by one global depth (T-119 r2) | a single deduction for every column; upstands treated as hanging | height to the deepest member hanging into THAT column; unknown side HELD (any villa) | T-178 L2 | rule pinned (method rule v1), test added |
| 2026-10-22 | Upper face on a lower roof short by the roof-to-floor band (T-159) | per-floor band from the floor level only | a face starts at the plate it stands on; unknown level HELD (any villa) | T-178 L3 | research record, test added |
| 2026-10-22 | HELD lower bound above the hand value (T-142 D3) | unbound footing treated as no footing for the low end | a held range must contain the physical value; low from the largest allowed footing, else NOT_ESTABLISHED (any held range) | T-178 L4 | research record, test added |
| 2026-10-22 | Two "released" baselines compared as one (T-165) | the profile choice was implicit | every comparison names its pinned spec; missing key refused (every villa) | T-178 L5 | tool merged, test added |
| 2026-10-22 | Doorway jamb nib lost from blockwork (T-169) | the face-to-face gap booked as doorway | a two-face nib >= 0.05 m is wall; shorter listed (any villa) | T-178 L6 (threshold case) | research record, test added |
| 2026-10-22 | Porch floor and soffit taken as one area (T-157) | two surfaces of different boundary merged | measure each from its own boundary; name the difference by component (any villa) | T-178 L7 | research record, test added |
