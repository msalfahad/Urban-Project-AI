# Scoreboard: Alsenan (development villa), engine vs freelancer (Verifier writes)

Development reference only: tuning against it is allowed, so these numbers never prove product accuracy (MISSION.md).
Verifier 2026-10-19 (23rd run, 16:10): rows below still current. Merged and pushed T-060 (9671133), T-065 (b09c06a), T-042 (b842ec2), T-010 (8fcabe0), T-071 (4054509), T-040 (2c86de1); head 2c86de1. New modules engine/source/concrete_ledger_v2.py, wet_room_evidence.py, exterior_spaces.py are imported by no engine, tool or method file (grep checked), the rest is research / docs, so the Alsenan run is identical by construction; not re-run. Commit measured stays 8774071. Drive read this run (P7757.dxf, sha ab54dd55...31cc4 = SOURCE_MANIFEST) for who-is-right checks: method-piece diagnostics (not scored rows) roof membrane 204.112 vs 285.00 m2 (-28.4 %), upturn 181.589 vs 194.00 lm (-6.4 %), three plan roofs ENGINE_RIGHT, total UNRESOLVED (Q-34); three printed-height windows 9.08 vs freelancer 9.70 m2 (-6.4 %, drawing prints 1.60 / 2.30 where he used 2.00).
Verifier 2026-10-19 (22nd run, 15:12): rows below still current. T-060, T-065, T-042, T-010 verified and merged locally but the push was refused ("[Merge Without Review]"), so the working branch stays 97c4bfc; none of the four is wired into a released method, so the Alsenan run is identical by construction; not re-run. Commit measured stays 8774071. Drive read this run (both DXFs, sha = SOURCE_MANIFEST) for who-is-right checks. Development diagnostics, not released lines: concrete ledger V2 holds the footing line (70.04 m3 released + band 91.94 m held, owner Q-28 A provisional) and the pool line (wall plan 2.357 m2, floor plan 10.936 m2, both ENGINE_RIGHT by hand); wet-room evidence gives wet floor 72.12 vs 72.01 m2 (+0.2 %) and upturn 144.73 vs 144.61 lm (+0.1 %), V2.9 released -12.8 % / -14.9 %. New verdicts this run: F3 count ENGINE_RIGHT (+0.672 m3), CN neck section ENGINE_MISSED_PRINTED_VALUE, blinding RULE_DIFFERENCE, F10 UNRESOLVED (Q-31).
Verifier 2026-10-19 (20th run, 12:57): rows below still current. Merged T-066 (1c23c4d), T-062 (37a801c), T-063 (97c4bfc): research and docs only (research/agents_t066, agents_t062, agents_t063 + rebuilt maps), imported by no engine, tool or method file, so the Alsenan run is identical by construction; not re-run. Commit measured stays 8774071. Drive read this run (P7757.dxf, sha = SOURCE_MANIFEST) for who-is-right checks only: pool depth 1150 and third-dome 4410 / 2149.4 dimensions confirmed. New verdicts (diagnostic lines, not scored rows): storeys ENGINE_RIGHT; roof waterproofing, pool wall height, dome count, lift walls UNRESOLVED (open Q-24..Q-27); pool slab plan RULE_DIFFERENCE.
Verifier 2026-10-19 (19th run, 12:10): RE-MEASURED, rows below still current. tools/alsenan_scoreboard.py via tools/alsenan_keymap.py run by the verifier on 6def656 (after the owner-session merges of 11:0x: T-044, T-036, T-034, T-029, T-033, T-011, T-037, T-041, T-047) and again on 8774071 (after this run's merges T-019, T-057, T-061, T-058): ARCH_TAKEOFF_V2.9 + route G, conventions V6, no facts file, no profile; Drive DXFs sha ab54dd55...31cc4 / 9f9d1179...38079 = SOURCE_MANIFEST; Py 3.11.17; exit 0, 1455 lines, BOQ_LINES.csv byte-identical between the two heads and every bucket identical to the b5475db rows. Commit measured: 8774071. Concrete compared lines: engine 92.77 vs freelancer 111.81 m3, -19.04 m3 (-17.03 %), unchanged (footing 77.27 vs 77.63, stair+dome 12.01 vs 21.83, pool 3.50 vs 12.35). New method pieces (strip guard: footing band 91.94 m = 9.425 m3 measured + 1.608 m3 held; room label guard: 11 labels HELD; pool check list) are not wired, so no released quantity moved. Who is right this run: footing band length ENGINE_RIGHT for the guard vs the frozen 60.17 m (hand calc from the band vertices); vs the freelancer 71.7 m UNRESOLVED (owner Q-12 answered, member split in T-065). Line-level counts on the scored concrete lines unchanged: 3 UNRESOLVED.
Verifier 2026-10-19 (18th run, 09:55): rows below still current. Merged T-004a (2622ddd): new tools/label_census.py, a read-only diagnostic imported by no engine, tool or method file, so the Alsenan run is identical by construction; not re-run. Commit measured stays b5475db. Drive read this run (architectural DXF, sha = manifest) to reproduce the T-004a census: 11 room labels lie in no room (4 GF yard / courtyard, 2 GF pool, 4 roof, 1 void), engine gaps not measured against the freelancer (follow-ups T-061, T-062). Verdict counts unchanged.
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
