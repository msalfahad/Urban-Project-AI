# Scoreboard: Alsenan (development villa), engine vs freelancer (Verifier writes)

Development reference only: tuning against it is allowed, so these numbers never prove product accuracy (MISSION.md).
Verifier 2026-10-19 (16th run, 07:05): rows below still current. Merged T-048 (fd0d5dd): new engine/source/concrete_curved_strips.py, imported by no engine, tool or method file, so the Alsenan run is identical by construction; not re-run. Commit measured stays b5475db. Drive read this run (structural DXF, sha = manifest) to run T-050's edge trace: the 31.77 m (3.81 m3) footing edge-strip silent omission is confirmed (to be fixed by T-058); verdict on that line stays UNRESOLVED (Q-12 c). Verdict counts unchanged.
Verifier 2026-10-19 (14th run, 05:00): rows below still current. Merged T-038 (fa93ec2): docs only, no engine, tool or
method file changed, so the Alsenan run is identical by construction; not re-run. Commit measured stays b5475db. Drive
read this run (both DXFs, sha = SOURCE_MANIFEST) for who-is-right checks only. Verdicts from the drawing this run: storeys
ENGINE_RIGHT (no basement plan, T-038); pool floor term and pool wall plan FREELANCER_RIGHT (T-037); concrete lines pool,
stair+dome, footing edge strip and lift walls UNRESOLVED (Q-12, Q-18, Q-19). Line-level counts: 0 ENGINE_RIGHT,
0 FREELANCER_RIGHT, 0 RULE_DIFFERENCE, 3 UNRESOLVED on the scored concrete lines (unchanged).
Verifier 2026-10-19 (13th run, 04:30): rows below still current. Merged T-025a (2748ffe): new engine/source/cad_limit_census.py,
imported by no engine, tool or method file, so the Alsenan run (ARCH_TAKEOFF_V2.9 + route G) is identical by construction;
not re-run. Commit measured stays b5475db (engine code reached by the run identical at 2748ffe). Drive not read this run (not needed).
Verifier 2026-10-19 (11th run, 02:00): MEASURED ON THE WORKING BRANCH. T-001b merged (b5475db) and T-035 merged (56820cb, no
engine change: facts file only). tools/alsenan_scoreboard.py via tools/alsenan_keymap.py, run by the verifier on b5475db
(ARCH_TAKEOFF_V2.9 + route G, conventions URBAN_M8_GENERIC_CONVENTIONS_V6, no facts file, no route G profile; Drive
"Alsenan chalet project" DXFs, sha256 ab54dd55...31cc4 and 9f9d1179...38079 = SOURCE_MANIFEST; Python 3.11 venv from
requirements.txt; 1455 canonical lines, exit 0). Same rows as the 9th-run pending measurement. With T-035's facts file the
run is line-for-line identical (no printed wall height exists), so plaster / paint stay HELD. Commit measured: b5475db
(engine code identical at 56820cb). Who is right: 3 UNRESOLVED (Q-12), 0 ENGINE_RIGHT, 0 FREELANCER_RIGHT, 0 RULE_DIFFERENCE.

| Trade | Unit | Ref lines | Coverage | Silent omissions | Unit refused | Compared | WAPE | Signed | False pos. | Dup. | Verdicts |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Concrete | m3 | 8 | 100.00 % | 0 | 0 | 3 | 17.03 % | -17.03 % | 0 | 0 | footing -0.37, stair+dome -9.83, pool -8.85: UNRESOLVED (Q-12); 5 lines HELD (205 held lines, census T-036) |
| Plaster | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | 0 | 0 | HELD (no printed wall height, T-035; owner Q-14) |
| Paint | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | 0 | 0 | HELD (same) |
| Floor area | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | 0 | 0 | HELD (3 wet / dry review sets) |
| Doors (aluminium) | m2 | 1 | 0.00 % | 0 | 1 | 0 | - | - | 0 | 0 | unit refused (engine nr) |
| Windows (aluminium) | m2 | 1 | 0.00 % | 0 | 1 | 0 | - | - | 0 | 0 | unit refused (engine nr) |
Verifier 2026-10-19 (10th run, 01:20): not refreshed: nothing merged (merge pushes still refused by the session check; working branch still b35c944) and the last measurement is from 2026-10-18 22:58. T-029 and T-034 are opt-in (storey vocabulary, ARCH_TAKEOFF_V2.10) and change no released quantity. Drive was not needed this run.
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
