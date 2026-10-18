# Scoreboard: Alsenan (development villa), engine vs freelancer (Verifier writes)

Development reference only: tuning against it is allowed, so these numbers never prove product accuracy (MISSION.md).
Verifier 2026-10-18 (8th run, 21:40, nothing merged, working branch still b35c944): still NOT MEASURED. Google Drive 'Urban BOQ private data / Alsenan chalet project' is readable now, but the engine-to-freelancer key map (T-001b) does not exist: T-001b is BLOCKED-OWNER on Q-11 (DXF exports), so tools/alsenan_scoreboard.py has no mapped input to run on. Verifier 2026-10-18 (7th run, after T-002b merge 5be347d (docs) and T-022 merge b35c944 (opt-in ROOM_VOCAB_V2, no released method uses it)): still NOT MEASURED, same reason (`urban-boq-private-data` cannot be attached: no repository-attach tool, private clone refused). Verifier 2026-10-18 (6th run, after T-021 merge 7b385cb, environment only): still NOT MEASURED, same reason (no repository-attach tool in the run; HTTPS clone of `urban-boq-private-data` denied). Verifier 2026-10-18 (5th run, after T-020 merge 7b040f6, tests only): still NOT MEASURED, same reason. Verifier 2026-10-18 (4th run, nothing merged): still NOT MEASURED; `urban-boq-private-data` cannot be attached to the verifier (no repository-attach tool in the run, HTTPS clone denied). Verifier 2026-10-18 (3rd run, after T-018 merge 1583c85, docs only): still NOT MEASURED, same reason; private data not attached to this run. Verifier 2026-10-18 (later run, after T-002a merge dabb897, docs only): still NOT MEASURED, same reason. Verifier 2026-10-18: NOT MEASURED. `tools/alsenan_scoreboard.py` is merged (T-001a, 39c9dea) but has not been run on real
data: the private repository `msalfahad/urban-boq-private-data` is not attached to the verifier, and the engine-to-freelancer
key map does not exist until T-001b. Every row below is still a seeded estimate, not a measurement.

Verifier 2026-10-18 (9th run, 22:58): FIRST MEASURED ROWS, PENDING MERGE. tools/alsenan_scoreboard.py via tools/alsenan_keymap.py
(T-001b, task head 3f47ec2; the worker's script output, the concrete figures re-summed independently by the verifier from the
engine's own lines) on ARCH_TAKEOFF_V2.9 + route G, Drive DXFs (sha = SOURCE_MANIFEST). Every gate passed, but the merge push was
refused by the session check, so these rows are not yet on the working branch (b35c944). Who is right: 3 UNRESOLVED (Q-12).

| Trade | Unit | Ref lines | Coverage | Silent omissions | Unit refused | Compared | WAPE | Signed | False pos. | Dup. | Verdicts |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Concrete | m3 | 8 | 100.00 % | 0 | 0 | 3 | 17.03 % | -17.03 % | 0 | 0 | footing -0.37, stair+dome -9.83, pool -8.85: UNRESOLVED (Q-12); 5 lines HELD |
| Plaster | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | 0 | 0 | HELD (no facts file) |
| Paint | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | 0 | 0 | HELD |
| Floor area | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | 0 | 0 | HELD (3 wet / dry review sets) |
| Doors (aluminium) | m2 | 1 | 0.00 % | 0 | 1 | 0 | - | - | 0 | 0 | unit refused (engine nr) |
| Windows (aluminium) | m2 | 1 | 0.00 % | 0 | 1 | 0 | - | - | 0 | 0 | unit refused (engine nr) |

Columns per MISSION.md. One row per trade and unit; never mix units. Each difference also gets a "who is right"
verdict (ENGINE_RIGHT / FREELANCER_RIGHT / RULE_DIFFERENCE / UNRESOLVED, MISSION.md); only FREELANCER_RIGHT and
UNRESOLVED count against the engine.

| Trade | Unit | Coverage | Silent omissions | WAPE | Signed error | Target | Source | Status |
|---|---|---|---|---|---|---|---|---|
| Rebar (net) | t | - | - | - | 26.24 vs 44.19 t, -40.6 % | <= 2-3 % | handoff §14 | reported; freelancer uses kg/m3 allowances (V3c) |
| Blockwork | m | - | - | - | about 140 m short, -36.5 % | <= 3 % | handoff §16.3 | reported |
| Wet-area waterproofing | m2 | - | - | - | -19.1 % | <= 2-3 %, no wet room missed | handoff §16.3 | reported (wet rooms merged into dry zones, B9) |
| Wall tile | m2 | - | - | - | about -15 % | <= 3 % | handoff §21 B9 | reported |
| Concrete | m3 | - | - | - | - | <= 2 % | - | to be measured by T-001 |
| Plaster, paint | m2 | - | - | - | - | <= 3 % | - | to be measured by T-001 |
| Floor area | m2 | - | - | - | - | <= 1-2 %, no room lost | - | to be measured by T-001 |
| Doors, windows | nr | - | - | - | - | exact count | - | to be measured by T-001 |

Seeded from `URBAN_PROJECTS_CLAUDE_HANDOFF.md` (snapshot 2026-10-04); unverified until T-001 measures it.
