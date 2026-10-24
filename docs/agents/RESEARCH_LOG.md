# Research log (Research scout writes; newest first)

Daily target (PLAN.md, owner 2026-10-18): at most 5 entries, at least one aimed at the current biggest scoreboard gap; the engine must work on any villa, not one project.

Each entry: date, what it is (link), licence, what it could improve in the engine or the workflow, risk, verdict
(ADOPT idea / TRY in sandbox / WATCH / REJECT). Never install or run downloaded code from here; the lead decides.

## FEEDBACK TO LEAD 2026-10-24 (scout run 23:55 UTC)

No open research requests; all five items below come from RUN_LOG / LEAD_REPORT 22:15 / RUN_LEDGER. Nothing asks any agent
to reprioritise.
1. **Overlap IDLE runs (usage).** Problem: 11 IDLE lines on 24 Oct (Worker 1 x6, Worker 2 x5), each a whole cloud session
   (setup hook, context) that delivers nothing; cause is a run longer than its 60-min slot (Worker 1 22:21 -> 23:32 = 71 min,
   Worker 2 22:40 -> 23:48 = 68 min). Evidence: the scheduled-tasks docs document no skip-if-still-running behaviour and say
   runs "draw down subscription usage the same way interactive sessions do", so the run lock is the only guard and each IDLE
   run is paid. Change: every worker task row states a hand-in point at 50 min of run time (READY with what is done, the rest
   as rN), and the Lead splits any task that ran > 55 min twice. Expected effect: IDLE lines towards 0, one more delivering
   run per worker per overlap. Who: Lead (task rows); optionally owner (wrapper prints minutes since STARTED).
2. **Full suite does not fit one 10-minute shell (Worker 1 22:00; LEAD REPORT need (2)).** This needs no owner change today:
   the wrapper's `pytest` already accepts several `tests/<folder>` paths, and `.claude/settings.json` allows
   `Bash(bash scripts/agent_env.sh *)`, so a worker can (a) run the suite in 3-4 folder chunks, each under 10 min, or (b) run
   the same wrapper command with `run_in_background` and `timeout` up to 7,200,000 ms (documented 2-hour ceiling for cloud
   sessions), reading only the failure lines at the end. Change: put the chunk list (from `codemap`) into the Checker's and
   workers' L4 wording. Expected effect: L4 hand-ins without waiting for the Checker. Who: Lead. (Repeats idea 30 for workers;
   still not used.)
3. **Wrapper `run` allowlist (LEAD REPORT need (1)).** Docs: a Bash allow rule matches "everything before the first `*` as
   written", so an owner rule like `Bash(.work/venv/bin/python *)` would approve ANY python code; keep the wrapper as the only
   gate. Change: owner adds one `run` entry for a fixed folder, e.g. `tools/research/*.py` with the same path regex and
   `..` refusal the `pytest` entry uses. Expected effect: research scripts run through the audited path. Who: owner.
4. **Stair soffits, T-281 (new missing scope).** NRM2 formwork item 25 "Soffits of sloping work" (m2, "sloping one way" /
   "two ways") "includes work to soffits of slabs, ramps, steps, staircases"; steps in soffits are a separate m item; plaster
   to "stair undersides" is a separate category; ANZSMM classes soffits <= 15 deg / > 15 deg. No source read says plan or
   slope area. Change: T-281 output per flight: plan area, true sloping area (plan x sqrt(1 + (riser / going)^2)), slope
   class, landings as flat soffits in their own row, the plan / slope choice HELD for the owner. Who: Lead (acceptance);
   owner (basis).
5. **"run unknown" still appears** (Verifier 23:52, 22:51, 21:51): idea 29 (SessionStart hook writes the session id) is
   still unapplied. Who: owner.

## 2026-10-24 (scout run 23:55 UTC): 0 requests (none open), 6 findings

Read: RESEARCH_REQUESTS (Open: none), LEAD_REPORT 22:15 / 20:15, RUN_LOG top 40 + today's IDLE lines, FEEDBACK top,
RESEARCH_LOG top 2, RUN_LEDGER totals (55 / 55 SUCCESS, last audited block), OWNER_SESSION_CHANGES top 5. Drive not opened
(not needed). Nothing installed or run; every page cited was opened.

### Team finding: overlapping runs and their cost (scheduled-tasks documentation)

| What (link) | Documented behaviour (quoted) | Gap it helps | Verdict |
|---|---|---|---|
| [Automate work with scheduled tasks](https://code.claude.com/docs/en/routines) | "Expressions that run more often than once per hour are rejected"; scheduled tasks "draw down subscription usage the same way interactive sessions do"; scheduled runs limited to "100 per hour" per account; "A green status in the run list means the session started and exited without an infrastructure error. It does not mean the work your prompt describes succeeded." No sentence describes skipping or queueing a run while the previous run of the same task is still active | 11 IDLE runs on 24 Oct, each a paid session that only writes a lock line; the team's run lock is the only overlap guard (correct, keep it) | ADOPT-IDEA: a 50-min hand-in point per worker task (the slot is 60 min), and split tasks that overrun twice |
| same page, "Manage scheduled tasks from the CLI" | "ask about a scheduled task's run history, for example `/schedule why did my nightly review do nothing this morning?` ... It also reads a run's log to explain what happened, including tool errors, permission denials, and the final result. Requires Claude Code v2.1.227 or later"; inside a cloud session `/schedule` "isn't available in that environment" | RUN_LEDGER: "The auditor cannot read the transcripts of scheduled sessions"; the cause of an INCOMPLETE run is "NOT KNOWN" | TRY-IN-SANDBOX (owner, from a local CLI, on the next INCOMPLETE or IDLE run) |

### Team finding: L4 suite inside the 10-minute shell (tools reference)

| What (link) | Documented behaviour (quoted) | Gap it helps | Verdict |
|---|---|---|---|
| [Tools reference, Bash](https://code.claude.com/docs/en/tools-reference) | `BASH_MAX_TIMEOUT_MS` ceiling "ten minutes out of the box"; "In a session that runs unattended, such as ... a cloud session, background Bash and PowerShell commands have a time limit"; "A command that Claude starts in the background gets 30 minutes, or the `timeout` Claude passes with `run_in_background`, up to a maximum of 2 hours"; at the limit "Claude can start the command again with a longer `timeout`"; "The time limit requires Claude Code v2.1.285 or later" | Worker 1 T-277 full suite did not finish (22:00); Checker runs it before merge | ADOPT-IDEA: the existing wrapper command `bash scripts/agent_env.sh pytest --tree <T> tests/...` run with `run_in_background` (already allowed by `Bash(bash scripts/agent_env.sh *)`), or in folder chunks; no settings change needed |
| [pytest-xdist](https://pypi.org/project/pytest-xdist/2.5.0/) | Licence "MIT"; "`-n auto` to use as many processes as your computer has CPU cores"; `--dist loadfile` keeps a file's tests in one worker; "`-s`/`--capture=no` ... does not work"; a session-scoped fixture "runs once per worker process" | Wall time of the L4 suite | TRY-IN-SANDBOX (owner / Lead: new pinned dependency; risk: the root `conftest.py` session guard on `data/` / `tests/` would run per worker; compare NEW / KNOWN counts with a serial run before trusting it) |

### Team finding: the `run` allowlist and permission-rule prefixes (permissions documentation)

| What (link) | Documented behaviour (quoted) | Gap it helps | Verdict |
|---|---|---|---|
| [Configure permissions](https://code.claude.com/docs/en/permissions) | "Claude Code matches everything before the first `*` as written, so those words are what limit the rule: `Bash(git log *)` allows only `git log` commands, and `Bash(git *)` allows every git command"; "a rule like `Bash(safe-cmd *)` won't give it permission to run the command `safe-cmd && other-cmd` ... A rule must match each subcommand independently"; a Bash rule "isn't a security boundary around the program" | LEAD REPORT need (1): research scripts run with the venv python outside the wrapper | ADOPT-IDEA (owner): add a wrapper `run` entry for one fixed folder with the `pytest` entry's path check; do NOT add a `Bash(<venv python> *)` allow rule (it approves any code) |

### Practitioner method: stair soffits (T-281, missing scope found 22:15)

| What (link) | Evidence class | Content (as read) | Gap it helps | Verdict |
|---|---|---|---|---|
| [NRM2 formwork extract (GCU teaching copy)](https://edshare.gcu.ac.uk/3911/2/pdf_download/NRM_2%20Formwork.pdf) | STANDARD (NRM2 table as reproduced for teaching) | Item 25 "Soffits of sloping work", m2, "Sloping one way" / "Sloping two ways", note: "This includes work to soffits of slabs, ramps, steps, staircases and the like"; item 30 "Steps in soffits", m, "<= 500 high: width stated"; strings and risers are m items with width stated | Stair soffit is its own m2 line, classified by slope, never folded into flat ceilings | ADOPT-IDEA |
| [ASAQS Plastering FAQs](https://www.asaqs.co.za/page/PlasteringFAQs) | PRACTITIONER (QS association) | plaster to "soffits, beams, or stair undersides is treated as a separate category"; sloped surfaces "still measured by area" and described separately because stairwells "may require scaffolding" | Plaster / paint follow the same split | ADOPT-IDEA |
| [ANZSMM formwork rules (CAUL OER)](https://oercollective.caul.edu.au/building-measurement-approaches/chapter/4-2-measurement-rules-for-formwork/) | PRACTITIONER (teaching text on ANZSMM s.7) | slab soffits classed "horizontal", "slope not exceeding 15 degrees", "slope exceeding 15 degrees"; "each class of formwork be measured separately" | Slope class for every flight | Information |

None of the three says whether the area is taken on plan or on the slope. Next step for the Lead (T-281 acceptance): per
flight write plan area, sloping area = plan x sqrt(1 + (riser / going)^2) from the drawn risers and goings (stair rule S-9:
drawn goings, no generated winders), slope class, and landings as flat soffit rows; a stepped underside gives a linear
"steps in soffits" row instead; the plan / slope basis stays HELD for the owner. Tests: straight flight (both areas),
flight with landing, winder flight from drawn polygons, a stepped soffit.

### Market: takeoff MCP servers (new this month)

| What (link) | What it does / how | Licence | Maturity | Security | Gap it helps | Verdict |
|---|---|---|---|---|---|---|
| [OpenTakeoff](https://glama.ai/mcp/servers/Kentucky-ai/opentakeoff) | stdio MCP server (53 tools) + browser canvas for construction-plan PDFs / images: calibrate, measure, export CSV / JSON / xlsx / DXF; "Measuring an unscaled sheet refuses"; agent work lands as "dashed pencil proposals needing human review", only a human applies APPROVED; provenance per record | AGPL-3.0-only (Apache-2.0 up to commit 84c7f48e), CLA | "MCP 0.9.84", listed on the MCP registry; no star / release data read | installed by `npx -y opentakeoff-mcp` (runs a package); "Unconfigured builds make zero AI network calls"; trained adapters proprietary | PDF / scanned plans only (no DXF input); its scale gate and proposal / approval split match the engine's HELD / VERIFIED; copyleft rules out embedding | WATCH (design ideas only; do not install) |
| [ODA MCP Servers FAQ](https://www.opendesign.com/blog/2026/august/oda-mcp-servers-faq.md) | self-hosted MCP access layer to DWG, STEP, IFC: read models, "pull quantities", compare revisions; volume, surface area, bounding box | commercial, ODA membership (Sustaining tier and up) | launch "September 2026" inside ODA viewers | local mode has "no outbound network path" | a second DWG reader beside LibreDWG (idea 14); DXF not listed | WATCH (cost; not needed while the DXF route works) |

## FEEDBACK TO LEAD 2026-10-23 (scout one-off run 17:55 UTC, owner fire: R-12, R-09, R-10 only)

Nothing below asks any agent to reprioritise; it is evidence for rows already on the board.
1. **R-12 / Q-71 footings.** A third published count rule exists (SRIA, Oct 2025): edge bar at s/2 from the edge (never
   less than cover), count = ceil(full width / s). It is not one of Q-71's options A / B / C: it is C rounded up. On F8
   bottom short bars it gives 36 (A 35, B 36, C 36.0). Proposed: when Q-71 is next touched, add this rule as a fourth
   drawing-fact column per row (no recommendation, owner chooses). Expected effect: the owner sees every published rule.
2. **R-12 / D-57 pool.** D-57 is which bar population (R1 / R2) the flat floor takes, not a notation question: no
   reference can answer it; it stays a designer item.
3. **R-10.** Industry practice puts laps at stated positions and staggers them (at least 50 % of bottom bars lapped at the
   column centreline, SRIA s.3.1); the drawing does not show positions, so splice COUNT from the stock-length formula and
   lap LENGTH as a 40 d .. 70 d range stay the right output.

## 2026-10-23 (scout one-off run 17:55 UTC): supplements to R-12, R-09, R-10 (owner fire), evidence classes

Supplements the 17:50 entries below (not repeated). Evidence classes: CODE CLAUSE (a clause of a design code read here),
STANDARD (a named standard, clause not read), PRACTITIONER (industry body, supplier or tool page). No code clause was found
for any of the three; all evidence is level 4, below the project's own schedule, sections and notes.

### Answer to R-12 (supplement): footings and pool, the third count rule

| What (link) | Evidence class | Content (as read) | Gap it helps | Verdict |
|---|---|---|---|---|
| [SRIA Technical Note "Guidelines for Economical Assembly of Reinforcement" (Steel Reinforcement Institute of Australia, Oct 2025)](https://www.sria.com.au/wp-content/uploads/2025/10/Tech-Note-5-24-10-2025-Final-Document.pdf), s.2.4 Recommendation 4 | PRACTITIONER (industry body; AS 3600 context, not Gulf) | "The outermost reinforcement parallel to an exposed edge should be located one-half of the specified spacing" (not less than the cover) from the edge; scheduling hint: number = "width of slab or strip including edge cover" divided by "specified spacing", rounded up (example 52.5 -> 53-N16); "What is more important is that the total number of bars is specified, not just the spacing" | Q-71: a fourth rule beside A / B / C: N = ceil(n x full side). F8 bottom short bars "9 ø 14/m", side 4.00 m: 36 bars (s = 111.1 mm; s/2 = 55.6 mm is under the 70 mm cover, so the edge bars sit at cover and the inner spacing becomes 110.3 mm, closer than printed) | ADOPT-IDEA (as a named drawing-fact column, owner chooses) |
| [Eurocode Applied table](https://eurocodeapplied.com/design/en1992/reinforcement-quantity-table) (read 17:50) | PRACTITIONER | "bars per meter ... multiplied by the appropriate distribution length and rounded up" | Matches the route's project-only note 22B "rate per metre, rounded up" recorded in Q-71; does not say which length | Information |
| Arabic-language QS pages (searched "حصر حديد القواعد ... عدد الاسياخ في المتر"): the two candidate pages failed to load or did not cover counting | none | nothing read | no Gulf evidence this run | WATCH |
| Pool D-57 | n/a | which bar population (R1 / R2) a flat floor takes is a design choice, not a notation | none from references | REJECT as a research question (designer item) |

Summary of published count rules for a rate n per metre over a side W with cover c (s = 1/n): A = ceil(n (W - 2c));
B = ceil((W - 2c) / s) + 1 (Heaton / BS 8666-style); SRIA = ceil(W / s) with edge bars at max(s/2, c); C = n W kept
fractional. All agree "/m" is a rate (spacing 1000 / n mm), consistent with the team's DRAWING FACTS (1) in Q-71. Next step
for the Lead (optional, no reprioritisation): a one-line addition to the Q-71 drawing-facts table, computed by the same
recount that reproduced A / B / C: the SRIA column for the 20 rows and the five-footing total; evidence class PRACTITIONER.

### Answer to R-09 (supplement): evidence class and the count step

| What (link) | Evidence class | Content | Verdict |
|---|---|---|---|
| Table-grid method (17:50 entry) | own method (no source) | rebuild cells from drawn edges; merged cells by missing edges | ADOPT-IDEA |
| [ricklove/cad-extract](https://github.com/ricklove/cad-extract) | PRACTITIONER (MIT tool; feature list only) | merged-cell and touching-table cases; known silent-duplicate bug | ADOPT-IDEA (test list) |
| [SRIA Tech Note s.2.4](https://www.sria.com.au/wp-content/uploads/2025/10/Tech-Note-5-24-10-2025-Final-Document.pdf) | PRACTITIONER | the table cell gives the rate; the count rule is a separate, named step | ADOPT-IDEA |

Next step for the Lead: the reader returns (mark, layer, direction, notation kind COUNT / SPACING / RATE, d, n or s) per
cell and never a bar count; the count is applied afterwards by the rule the owner picks for Q-71, so the reader can merge
before Q-71 is answered. Tests as in the 17:50 entry plus one cell per notation kind ("8 ø 12", "ø 8/15 cm", "9 ø 14/m").

### Answer to R-10 (supplement): evidence class and lap positions

| What (link) | Evidence class | Content (as read) | Verdict |
|---|---|---|---|
| [CRSI Lap Splices](https://www.crsi.org/reinforcing-basics/reinforcing-steel/splicing-bars/lap-splices/) | PRACTITIONER (industry body, citing ACI 318) | ACI 318 requires "the locations and lengths of all lap splices on the structural drawings" | ADOPT-IDEA: no drawn location -> splice positions are not a measured fact |
| [SRIA Tech Note s.2.5, s.3.1](https://www.sria.com.au/wp-content/uploads/2025/10/Tech-Note-5-24-10-2025-Final-Document.pdf) | PRACTITIONER (AS 3600 context) | "Specify bottom slab bars to be staggered (ie 50% anchored in each support)"; "at least 50% of bottom bars must be lapped by Lsy.tb at the column centreline"; no stock-length guidance | Information: staggering sets positions, not the count, for runs each spliced once |
| Project note "development length >= 70 d (tension) / 40 d (compression)" | the project's own note (above every reference) | the only lap rule printed | ADOPT-IDEA: lap range 40 d .. 70 d |

Next step for the Lead: as in the 17:50 entry (pieces = ceil((L - lap) / (S - lap)), procurement length L + (pieces - 1)
lap, range at 40 d and 70 d, ends a separate line); evidence class of the output: PROJECT NOTE for the lap length, own
arithmetic for the count, NOT PRINTED for positions.

## FEEDBACK TO LEAD 2026-10-23 (scout run 17:50 UTC)

1. **"run unknown" in STARTED lines.** Problem: about half of today's STARTED lines carry `run unknown` (Worker 1 17:20,
   Worker 3 16:59, Verifier 16:51, 15:52), so an unclosed run cannot be traced to its session. Evidence: RUN_LOG 12:41-17:41.
   Change: the existing SessionStart hook reads `session_id` from its stdin JSON (documented common input field) and appends
   `export AGENT_SESSION_ID=<id>` to `$CLAUDE_ENV_FILE`; `agent_env.sh board log` fills the field from it. Effect: every run
   line names its session; the run lock can key on it. Who: owner (main / settings / hook are outside the team's write rights).
2. **L4 full suite left at 20 %** (Checker 15:52, T-203). Change: start the suite with `run_in_background` and an explicit
   `timeout` (documented: up to 2 h for an unattended session; foreground Bash caps at 10 min) and read its output file at the
   end of the run; give the result only the failure lines (documented PreToolUse output-filter pattern / a subagent). Effect:
   an L4 verdict that belongs to a finished run, less context per Checker run. Who: Lead (prompt wording in the Checker's
   task row); hook form: owner.
3. **Splice / lap weight on runs over 12 m (R-10).** Change: one pure function `pieces = ceil((L - lap) / (S - lap))`,
   `splices = pieces - 1`, procurement length `L + splices x lap`, computed twice (lap = 40 d and 70 d from the printed note)
   and reported as a RANGE; ends (development) a separate line. Effect: T-138 r2 / T-141 get a procurement weight without
   choosing a zone. Who: Lead (task).
4. **Slab / stair "/m" (R-12).** Published tables treat "n bars per metre" as spacing s = 1000 / n mm (same as T-171), but
   the published count rules differ: "n x distribution length, rounded up" (no +1) vs "(L - 2c) / s, round up, + 1". These are
   exactly counts A and B. Change: keep the A..B range; close it only with project evidence (a slab section or detail that
   draws the bars at an edge), never with a reference. Who: Lead.
5. **Footing schedule tables (R-09).** Change: build own table-grid code from DXF LINE / LWPOLYLINE edges (method below);
   use the MIT `cad-extract` feature list as the test list (merged cells, three-sided boxes, touching tables). Who: Lead (task
   for T-136).

## 2026-10-23 (scout run 17:50 UTC): 3 requests answered (R-09, R-10, R-12), 2 team findings

Read: RESEARCH_REQUESTS, LEAD_REPORT 16:20 / 14:20, RUN_LOG top 40, FEEDBACK top, RUN_LEDGER totals (55 / 55 SUCCESS since
22 Oct 14:30; 0 refusals today), OWNER_SESSION_CHANGES top 5. Drive not opened (not needed). Nothing installed or run.

### Answer to R-09: footing reinforcement from drawn CAD schedule tables

| What (link) | Licence | Maturity | Security | Gap it helps | Verdict |
|---|---|---|---|---|---|
| [ricklove/cad-extract](https://github.com/ricklove/cad-extract): DXF import, table and cell detection, text located in cells, "partition tables that touch", "three-sided boxes"; merged row cells identified, but merged rows/columns in pattern extraction unfinished and a known bug "duplicates values without indicating the merge" | MIT | 5 stars, 34 commits, .NET (inferred), no releases | Do not run; read the feature list only | Gives the case list a table reader must pass, and the exact failure mode B4 risks (a merged value copied or lost silently) | ADOPT-IDEA (test list), REJECT as a dependency |
| [IG-11-Kuiil/cad-data-extractor](https://github.com/IG-11-Kuiil/cad-data-extractor): ezdxf + LibreDWG extraction to JSON with entity handles; no table rebuilding; runs `dwg2dxf` as a subprocess | Own licence not stated (LibreDWG GPLv3 as external exe) | 3 commits, 0 stars | Subprocess execution | Nothing the engine lacks | REJECT |
| [Aspose.CAD reading tables](https://docs.aspose.com/cad/ja/net/developer-guide/how-to/work-with-file/reading-of-tables-from-dwg-dxf): reads TABLE entities only (load, get table entities, read values); a schedule drawn as lines + text is not a TABLE | Commercial | Mature | Closed .NET | Only for ACAD_TABLE entities | REJECT (cost; wrong case) |
| [Heaton rebar guide](https://heatonmanufacturing.co.uk/rebar-calculator-bar-quantity-and-cost/) (cites BS 8666 for scheduling): effective length = finished length - 2 x cover; "Number of bars = (Effective span / Spacing) + 1"; "Round up to the next whole bar" | Facts only | Supplier guide (level 4 evidence) | n/a | 'T d @ s' count, convention B | ADOPT-IDEA (as one named convention, with T-171's ceil(L_eff/s)+1) |

Method (own code, ezdxf already pinned): (1) collect horizontal / vertical segments from LINE and exploded LWPOLYLINE /
INSERT virtual entities inside the table's bounding frame, rotate into the frame axis if the frame is rotated; (2) snap x of
verticals and y of horizontals to a 1 mm grid -> grid lines X[], Y[]; (3) atomic cell (i, j) = rectangle between consecutive
grid lines; the edge between two neighbouring atomic cells EXISTS if drawn segments cover >= 95 % of its length; (4) union-find
over missing edges -> merged cells (each a set of atomic cells); (5) assign each TEXT / MTEXT by its insertion point (and
for MTEXT the text box) to exactly one merged cell; text whose box crosses a cell edge is OVERFLOW, reported, never split;
(6) row/column headers from row 0 / column 0; a value is read for (footing mark, column) only if exactly one cell covers it.
Every merged cell is reported with its span, so a footing whose rebar cell spans two marks is shown as shared, and an empty
cell is EMPTY, never 0 (fixes B4). Tests: own synthetic DXFs: plain 3 x 4 grid; one vertical merge; one horizontal merge;
empty cell; MTEXT wider than its cell; table rotated 90 deg; two tables touching; a three-sided last row. Next step for the
Lead: task "schedule-table grid reader, check-only" on the synthetic fixtures, then the footing schedule; compare with the
T-171 ledger cell by cell.

### Answer to R-10: laps and stock-length splicing when the drawing gives only a rule

| What (link) | Licence | Maturity | Security | Gap it helps | Verdict |
|---|---|---|---|---|---|
| [CRSI, Lap Splices](https://www.crsi.org/reinforcing-basics/reinforcing-steel/splicing-bars/lap-splices/): under ACI 318 the engineer must show "the locations and lengths of all lap splices on the structural drawings"; bars of different sizes: tension lap = larger of the smaller bar's lap and the larger bar's development length | Facts | Industry body | n/a | Where the drawing does not show splice locations, their position is not a measured fact: the estimate is a range | ADOPT-IDEA |
| [HardHatCalc lap splice calculator](https://hardhatcalc.com/calculators/structural/rebar-lap-splice-calculator): lap = ld x class factor (A 1.0, B 1.3); example 60 ft wall, 20 ft bars, "two splices" per run, "add the lap splice length to every joint"; states splices staggered so no more than half the bars lap at one point | Facts (calculator site, level 4; its staggering statement is not checked against the code text) | Web tool | n/a | Splice count per run; total length = run + laps | WATCH (example ignores that each lap eats stock length) |
| [Heaton rebar guide](https://heatonmanufacturing.co.uk/rebar-calculator-bar-quantity-and-cost/): stock "typically 6 m or 12 m"; laps commonly 40-50 d in tension; laps excluded from its bar count | Facts | Supplier guide | n/a | Confirms laps are a separate line on top of the net count | Information |

Method (derived here, own code): a run of length L with stock S and lap l needs `k = ceil((L - l) / (S - l))` pieces
(each joint consumes l of stock), `k - 1` splices, procurement length `L + (k - 1) l`. With the project note only
(70 d tension / 40 d compression) report both: for the 18.57 m run on 12 m stock, T16: 1 splice either way, 19.21 .. 19.69 m
per bar line (T12 19.05 .. 19.41, T20 19.37 .. 19.97). Staggering changes WHERE splices go, not their count, when every bar
in the run is spliced once; it changes the count only if staggering forces extra cut pieces, which the drawing does not
show: leave it out and say so. End development lengths are a separate line (never merged with splices). Tests: L <= S
(0 splices), L = S exactly, L = 2S - l (boundary, 1 splice), L = 2S - l + 0.001 (2 splices), l >= S (refuse). Next step: T-141
span splitter calls this function and writes net kg, lap kg low / high, and the zone status "NOT PRINTED".

### Answer to R-12: "n ø d / m" on slab and stair plans

| What (link) | Licence | Maturity | Security | Gap it helps | Verdict |
|---|---|---|---|---|---|
| [Eurocode Applied, distributed reinforcement table (EN 1992)](https://eurocodeapplied.com/design/en1992/reinforcement-quantity-table): columns "Bar Spacing (cm)" and "Bars per meter" (5.0 cm = 20.00 bars/m, so s = 100 / n cm); results written as "25.1cm => 3.98 bars/m"; Note 2: "The number of reinforcement bars per meter of length should be multiplied by the appropriate distribution length and rounded up" | Facts (level 4) | Maintained design site | n/a | Same meaning as T-171 (per-metre = spacing 1/n), but a DIFFERENT count rule: ceil(n x L), no +1 (count A) | ADOPT-IDEA (name both rules) |
| [Next Day Steel, rebar spacing](https://nextdaysteel.co.uk/pages/rebar-spacing-determination): UK notation "T16-200" = T16 at 200 mm centres; "per metre" used for steel area only, As = (1000 / s) x bar area | Facts | Supplier page | n/a | Shows "/m" in UK practice is an area/density, consistent with s = 1000/n | Information |
| Searched Arabic / Gulf sources (Arabic query "تسليح البلاطة ... / م"; one Syrian university exam key read: no "/m" notation in it) | n/a | n/a | n/a | No Kuwait / Gulf source found this run | WATCH (no evidence) |

Answer: no reference found that gives slab / stair "/m" a meaning other than a density with spacing 1000 / n mm. The two
published count rules, ceil(n x L) and ceil((L - 2c) / s) + 1, are the team's counts A and B, so the reference evidence does
not choose between them. Next step for the Lead: keep slabs 4,643.77 .. 6,832.33 kg and stairs 1,039.16 .. 1,378.63 kg as
ranges; close them only from project evidence: a slab or stair section that draws bars to an edge (first bar at cover or at
s/2), or a general note; if none exists, it is a designer question (DESIGNER_CLARIFICATIONS), not an owner one.

### Team findings (Claude Code documentation)

| What (link) | Documented behaviour (quoted) | Gap it helps | Verdict |
|---|---|---|---|
| [Hooks: common input fields, SessionStart, CLAUDE_ENV_FILE](https://code.claude.com/docs/en/hooks) | Every hook receives `session_id` "Current session identifier"; "SessionStart hooks have access to the `CLAUDE_ENV_FILE` environment variable, which provides a file path where you can persist environment variables for the shell commands Claude runs later in the session"; "Use append (`>>`)"; SessionStart plain-text stdout is added to Claude's context | `run unknown` in STARTED lines; run lock keyed on a real session id | ADOPT-IDEA (owner edits the hook / agent_env.sh on main) |
| [Tools reference: Bash timeouts, background commands](https://code.claude.com/docs/en/tools-reference) and [Manage costs](https://code.claude.com/docs/en/costs) | Foreground default 2 min, ceiling "ten minutes out of the box"; in unattended / cloud sessions a background command "gets 30 minutes, or the `timeout` Claude passes with `run_in_background`, up to a maximum of 2 hours"; on reaching it Claude Code stops it and "Claude can start the command again with a longer `timeout`". Costs page: a PreToolUse hook can rewrite a `pytest` command to keep only failure lines; delegate test runs to subagents; "Aim to keep CLAUDE.md under 200 lines" | Checker L4 suite stopped at 20 %; per-run context | TRY-IN-SANDBOX (one Checker run with the suite in the background, timeout 7200000 ms) |

## 2026-10-20 (scout run 23:55 UTC): 3 requests answered (R-06, R-07, R-08), 1 new finding

Private repo urban-boq-private-data could not be attached (no add_repo / list_repos tool in this session); Drive "Alsenan
chalet project" listed (names and formats only: xlsx / xls BOQ sheets), so this is not a failure. Nothing installed or run.

### Answer to R-06: Arabic + English notes and room tags on SCANNED villa plans

| What (link) | Licence / commercial safety | Maturity | Security | Gap it helps | Verdict |
|---|---|---|---|---|---|
| [Tesseract Arabic data `ara`](https://pkgs.alpinelinux.org/package/v3.21/community/x86_64/tesseract-ocr-data-ara) (distro package of tessdata, 5.5.0, 1.6 MiB) | Apache-2.0 (permissive, safe) | Mature, in every Linux distro | Data file only, no code; needs an image change (apt `tesseract-ocr-ara`), which agents may not do | Second language for the existing Tesseract; `eng+ara` on one note box | ADOPT-IDEA (Lead / owner adds the package to the image) |
| [KITAB-Bench](https://arxiv.org/html/2502.14949v2) (MBZUAI, ACL Findings 2025; 8,809 samples, 9 domains; [scores page](https://www.codesota.com/ocr/benchmark/kitab-bench)) | Paper CC BY 4.0; dataset licence not stated | Peer-reviewed benchmark | Read-only facts | Sets expectations: Arabic OCR CER / WER Tesseract **0.54 / 0.84**, EasyOCR 0.58 / 0.89, PaddleOCR 0.79 / 1.02, Surya 4.95; Gemini-2.0-Flash 0.13 / 0.32, GPT-4o 0.31 / 0.55 | ADOPT-IDEA: free reading of Arabic notes by any permissive engine is NOT reliable enough to release a quantity; only closed-vocabulary matching is |
| [PaddleOCR PP-OCRv5 multilingual](https://www.paddleocr.ai/v3.5.0/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html): `arabic_PP-OCRv5_mobile_rec` 81.27 % line accuracy on Paddle's own 2,676-image set (+22.83 pts over v3; [model list](https://www.paddleocr.ai/v3.5.0/version3.x/model_list.html) still shows v3 at 73.55 %); community fine-tune [arabic_PP-OCRv6_small_rec](https://huggingface.co/medyas/arabic_PP-OCRv6_small_rec) CER 10.2 % (patsocr) / 13.5 % (isippt) but 50.3 % on historical scans | Apache-2.0 (permissive); community model is one person's account | 3.x active; community model new | Paddle `.pdparams` training weights are pickle-based: use only the inference export (`inference.json` / `.pdiparams`); native code | Second, independent engine for the two-engine agreement check | TRY-IN-SANDBOX (official v5 model only, inference export) |
| [Moreno-García, Elyan, Jayne 2017, text / graphics segmentation heuristics for complex engineering drawings](https://rgu-repository.worktribe.com/OutputFile/845553) (EANN 2017, CCIS 744) | Paper; method only, no code | Cited method | none (own code) | Finding note boxes before OCR: remove frame (edges + connected components), strip long lines by directional dilation, then classic connected-component text grouping; text-detection precision rose 0.37 -> 0.91 at recall 0.98 (Fletcher-Kasturi) once lines were removed | ADOPT-IDEA |

Recommended next step (task for the Lead, "Scanned-note reader, check-only", unblocks T-091 as a check, T-092, T-003):
(1) on one Alsenan raster plan sheet, remove frame and long lines (OpenCV, already permissive), group small connected
components into text blocks, keep blocks inside closed rectangles (note boxes) and blocks inside room outlines (tags);
(2) read each block twice: Tesseract `eng` for digits / Latin (and `eng+ara` once the `ara` data is in the image), and a
second engine (PaddleOCR v5 inference export, sandbox) or a vision model as evidence only (idea 21); (3) release a value
only if both readings agree after normalising digits (Arabic-Indic to Latin, `x` / `×` / `*`) AND it matches a closed
list: tile formats (60x60, 120x60, 160x80 ... from the finishing schedule or the quantity-takeoff skill), room names from a
fixed Arabic / English lexicon by edit distance <= 1, door heights in a 2.00-2.40 m band; (4) anything else stays HELD
with the crop saved for a person. Score against the T-091 hand census: report per-field agreement, never fill a gap from OCR
alone. Expectation from KITAB-Bench: Arabic words will mostly fail the agreement test; digits and tile sizes should pass.

### Answer to R-07: proving that a strip layout covers every piece of a membrane outline

| What (link) | Licence / commercial safety | Maturity | Security | Gap it helps | Verdict |
|---|---|---|---|---|---|
| [shapely 2 `difference(..., grid_size=)`](https://shapely.readthedocs.io/en/2.0.1/reference/shapely.difference.html) + [`set_precision`](https://shapely.readthedocs.io/en/2.1.2/reference/shapely.set_precision.html); GEOS OverlayNG snap-rounding, [PostGIS note](https://www.postgis.net/development/docs/internals/precision-tolerance/): result vertices are guaranteed on the grid; repeatable only if inputs are already on the grid | BSD-3 (shapely) / LGPL-2.1 (GEOS, dynamically linked) — safe | Very mature; grid_size needs GEOS >= 3.9 | Native GEOS, no network | Exact coverage proof: `R = difference(set_precision(outline, 0.001), union_all(strips), grid_size=0.001)`; every polygon in R is either a named patch or a bug; 0.84 m2 step-upturn miss becomes a failing test | ADOPT-IDEA |
| [physdes `rpolygon_cut`](https://physdes-py.readthedocs.io/en/latest/_modules/physdes/rpolygon_cut.html) (Wai-Shing Luk): recursive cut of a rectilinear polygon into convex rectilinear pieces at concave vertices | Licence not shown on the page: unknown | Small academic library | Pure Python | Idea only: cut at every concave vertex so each step edge starts its own band | WATCH (write own band split; do not copy) |
| [ARDEX WeldTec installation sheet](https://www.ardex.co.nz/wp-content/uploads/2019/01/Ardex-WeldTec-Membranes-Installation-Sheet.pdf) (TPO sheet, not torch-on): upstand min 150 mm; external corner: 100 mm flashing first, main sheet cut at 45 deg, corner point covered with detail tape; internal corners filleted and taped; welded lap 150 mm, end laps butted with 100 mm cover strip | Vendor document (facts only) | Current product sheet | n/a | Practice: corners and steps are closed by separate flashing / detail pieces, so "patch" is a legitimate, countable line, never a silent residue | ADOPT-IDEA (patch lines priced and counted) |

Recommended next step (task for the Lead, T-096 / T-098): (1) band decomposition: take every coordinate of the unfolded
outline (body + 0.20 m upturns, after unfolding each step edge) on the axis PERPENDICULAR to the strips; between two
consecutive coordinates the outline cross-section is a fixed set of intervals; (2) lay strips across the full
perpendicular range at 0.90 m effective pitch, and give each strip the length of the PROJECTION of `outline ∩ strip
rectangle` onto the strip axis (union over its whole 1.00 m width, not the cross-section at its centre or edge: a step edge
parallel to the strips lies inside one strip's width and is missed when the length is read at one line, which matches the
4.20 x 0.20 m miss); (3) prove with the grid_size difference above (grid 1 mm) and fail the test on any residue that is not
a declared patch; curved outlines (dome opening): chord polygon with sagitta <= 1 mm, residue named as patch pieces with
area; (4) test generator (own code): random rectilinear outlines as unions of axis-aligned rectangles on a 0.05 m grid,
plus fixed cases: step parallel to strips, step across strips, notch, L / U / T, hole, 45 deg splay, outline narrower than
one strip; property: residue area == 0 (or all residue is declared patch) and strip count >= ceil(perpendicular extent /
0.90). Roll count then goes to the existing cutting plan (idea 20).

### Answer to R-08: blockwork centreline metres from double-line CAD walls

| What (link) | Licence / commercial safety | Maturity | Security | Gap it helps | Verdict |
|---|---|---|---|---|---|
| [Domínguez, García, Feito 2012, "Semiautomatic detection of floor topology from CAD architectural drawings"](https://investigacion.ujaen.es/documentos/5f1ce1ab29995265e44db696?lang=en) (Computer-Aided Design 44(5) 367-378, doi 10.1016/j.cad.2011.12.009) and the [thesis](https://rujapre.ujaen.es/bitstreams/f4d91eb2-e821-4e52-a084-cf0eec77a7e2/download) (Domínguez Martín, Jaén 2014): Wall Adjacency Graph: pairs of "wall-prone" parallel close lines become graph edges, segments split per overlap layout, generalised WAG for 3+ parallel lines and for arc pairs (curved walls), junctions closed by clustering wall end vertices and growing centre lines until they intersect; openings anchored from door / window INSERT bounding boxes; columns on their own layer leave holes that must be bridged | Paper / thesis: method only, no code | Cited reference method (2012) | none (own code) | The standard global method for line-pair walls; the thesis notes local rule methods overfit and break on drawing defects | ADOPT-IDEA |
| [ladybug-geometry-polyskel](https://pypi.org/project/ladybug-geometry-polyskel) 1.7.55 (2026-09-16): straight skeleton (Felkel-Obdržálek) for wall polygons | **AGPL-3.0**: not safe for a private commercial product | Active | Pure Python | Would give a skeleton centreline of wall polygons | REJECT (licence) |
| [CGAL Straight_skeleton_2](https://www.cgal.org/license.html): geometric packages are mostly GPL, commercial licence from GeometryFactory | GPL / paid | Very mature | Native C++ | Same | REJECT (licence, cost) |
| NRM2 / ANZSMM practice: "walling is measured on the centre line" ([GCU NRM2 notes](https://edshare.gcu.ac.uk/3991/2/index.html)), thickness stated in each description ([Deakin ANZSMM chapter](https://deakin.pressbooks.pub/buildingmeasurementapproaches/chapter/6-3-anzsmm-rules-related-to-measurement-of-masonry-works-and-sample-descriptions/), CC BY-NC: cite, do not copy); wall shorter than 4x thickness is a pier (linear m); openings measured gross then adjusted | Facts only | Standard practice | n/a | Report blockwork per thickness class on the centre line, piers separately | ADOPT-IDEA |

Recommended next step (task for the Lead, T-027 follow-up, check for T-103): (1) pair wall lines by thickness class
(parallel within 0.5 deg, offset equal to a known class 0.10 / 0.15 / 0.20 / 0.25 m +- 5 mm, overlap of projections > 0),
take the MIDLINE of each pair over the overlap (exact for parallel pairs, no skeleton needed); (2) bridge gaps at openings
when a door / window INSERT or a column outline lies in the gap and both sides have the same class (report each bridge);
(3) close junctions WAG-style: snap midline ends within one thickness, extend to the intersection of centre lines (L: both
legs to the crossing; T: stem to the main wall's centre line; X: both through), so corners and ends are counted; (4) an
exact independent check per thickness class: wall polygon area / t = Σ centreline length − (t/2 per T-stem) − (t per X)
(mitred L corners need no correction), equal within 1 mm per wall, which proves no corner or end was dropped (SV-A: 44.4 m
face run vs 46.2 m hand must close to the hand figure through this identity); pygeoops.centerline (BSD-3, logged
2026-10-17) stays the second, independent check on odd angles and arcs; (5) report metres per thickness, piers (< 4 t) as
linear items, bridges and unpaired lines as HELD with location.

### New findings

| Date | What (link) | Licence | Could improve | Risk | Verdict |
|---|---|---|---|---|---|
| 2026-10-20 | [IfcOpenShell `ifcmcp`](https://dev.glassvision.dedyn.io/Glassvision/IfcOpenShell/src/tag/bonsai-0.8.6-alpha2608231326/src/ifcmcp) (`pip install ifcopenshell-mcp`, stdio MCP inside the upstream IfcOpenShell tree): keeps an IFC model in memory; `ifc_quantify` runs ifc5d QTO (IFC4 / IFC4X3 base quantities: volume, area, length, count, weight), `ifc_cost`, `ifc_plot` 2D drawings, `ifc_validate` | LGPL-3.0+ (usable as a separate process; keep it out of the engine's own code) | If a client ever sends IFC, a ready QTO cross-check for concrete / blockwork volumes; also a way to build synthetic test villas as IFC and plot them to drawings | No version / release status shown; native ifcopenshell; `ifc_edit` mutates models | WATCH |

## 2026-10-20 (scout run 00:00 UTC): 3 requests answered (R-01, R-02, R-05), 2 new findings

Private repo urban-boq-private-data could not be attached (no add_repo / list_repos tool in this session); Drive "Alsenan
chalet project" listed (names and formats only: xlsx / xls BOQ sheets), so this is not a failure. Nothing installed or run.

### Answer to R-01: reading dimension numbers and level marks from SCANNED elevation / section sheets

| What (link) | Licence / commercial safety | Maturity | Security | Gap it helps | Verdict |
|---|---|---|---|---|---|
| [Dimension-set recognition with a chain-sum check](https://gsl.lab.asu.edu/wp-content/uploads/sites/117/2022/05/edimen.pdf) (Wang, Tang, Tang, Tsinghua, about 1996): find digit strings as connected components first, then search a rectangle beside each text for a dimension line ending on two perpendicular witness lines; the outer (overall) chain is extended end to end, then the inner chain; **the sum of the inner chain is compared with the outer total and a mismatch raises an alarm** | Paper only, method idea (own code; safe) | Old, about 90 % text recognition reported, no chain metrics | None (no code) | R-01: the check that lets an OCR'd scanned chain be trusted or HELD without a person: a vertical chain (sill + window + head-to-level) must add up to the printed floor-to-floor (owner rule 4.50 / 4.20 m on Alsenan) or to the difference of two level marks (+1.00, +5.50) | ADOPT-IDEA: every OCR'd chain is released only if its parts sum to its overall dimension or to the bracketing level difference within one rounding unit (0.01 m); otherwise HELD with the read values shown. Never fills a missing number |
| [eDOCr2](https://www.mdpi.com/2075-1702/13/3/254) (Villena Toro and Tarkian, Machines 2025, 13(3) 254; code github.com/javvi51/edocr2, licence not shown on the paper, repo page not reachable this run): CRAFT text detector on overlapping patches, oriented boxes limited to -90..90 deg, **regions whose long side is vertical are rotated 90 deg before recognition**, thin strokes dilated and boxes padded, Tesseract first pass, then a CRNN trained on about 40,000 synthetic dimension strings | Paper CC BY 3.0; code licence UNKNOWN (eDOCr v1 forks show a LICENSE file of unknown type) | Published 2025; v1 [eDOCr](https://www.frontiersin.org/articles/10.3389/fmtec.2023.1154132/pdf) 2023 | TensorFlow / Keras `.h5` weights (HDF5, not pickle, but loading Keras models can run Lambda-layer code: treat as untrusted) | R-01 published error rates on dimension text in raster drawings: eDOCr2 text recall 93.75 %, precision 96.15 %, character error rate 0.73 %; eDOCr v1 recall about 0.89, precision 0.92, CER about 8 %; v1 is weak on small text. Mechanical drawings, not Gulf architectural scans: expect worse on 300-dpi A1 scans | WATCH (code licence unknown); ADOPT-IDEA the pipeline order (rotate vertical boxes 90 deg, digit-alphabet check, re-read on mismatch), own code with Tesseract (Apache-2.0) |
| [PaddleOCR 3.7.0](https://pypi.org/project/paddleocr/) (2026-06-11): PP-OCRv5 / v6 detection + recognition, [text-line orientation classifier](https://www.paddleocr.ai/v3.0.0/en/version3.x/module_usage/text_line_orientation_classification.html) (0 / 180 deg only, top-1 95.54 % on PaddleX's own set: 90 deg vertical dimension text still needs an explicit 90 deg rotation), ONNX export, CPU via OpenVINO / ONNX Runtime | Apache-2.0 (permissive, safe) | Very mature; release 4 months old | Models are downloaded from model hubs at first use (network): pre-download and pin hashes in a sandbox; Paddle has native code | R-01 second OCR engine to cross-read the same crop as Tesseract: release a digit string only when two engines agree AND the chain-sum check passes | TRY-IN-SANDBOX |

Recommended next step (task for the Lead, after T-083 hand table exists as truth): "Scanned-elevation dimension reader, check-only": on one Alsenan raster elevation sheet (and one synthetic non-Alsenan scan rendered from a hand-made DXF at 200 and 300 dpi, rotated 90 deg text included): (1) OpenCV (Apache-2.0) Hough / LSD for long vertical and horizontal lines and short ticks; (2) Tesseract `--psm 7` with a whitelist `0123456789.+-` on each candidate box, the box also read rotated 90 deg; (3) chain-sum check against the bracketing level marks; (4) compare with the T-083 hand table per window: report read / agreed / HELD counts and every wrong digit. Acceptance: 0 released values that differ from the hand table; unread stays HELD. Binding to a plan opening: by order along the facade and width (width read from the same sheet's horizontal chain must equal the plan opening width within 0.01 m), never by position alone.

### Answer to R-02: Arabic SHX fonts (x-arab1b family and others) stored as Latin keyboard codes

| What (link) | Licence / commercial safety | Maturity | Security | Gap it helps | Verdict |
|---|---|---|---|---|---|
| No published code table found for XARAB / X-ARAB1B / ARB SHX families (searched Autodesk forum, CADTutor, CAD Forum, Unicode lists). [CADTutor thread 69752](https://www.cadtutor.net/forum/topic/69752-lisp-extracting-arabic-text-in-autocad-into-text-file) confirms the mechanism: XARAB.SHX stores Arabic as English keyboard characters that only draw as Arabic, and gives no table (only a pointer to a Wiktionary keyboard-to-Arabic gadget, i.e. the Arabic (101) map T-047 already uses) | n/a | Forum | n/a | R-02: explains why a second family does not match the 101 map: these fonts draw a **contextual form** (isolated / initial / medial / final) per code, so one letter has several codes | Information: the only reliable source of a mapping is the font file itself |
| [shxparser](https://github.com/tatarize/shxparser/) ([PyPI](https://pypi.org/project/shxparser/)): pure-Python SHX parser, all shape commands (pen, stack, subshapes, arcs), glyphs to path segments | MIT (permissive, safe) | 29 stars, 61 commits, no releases; author "believes complete and correct" | Pure Python, no network; still read before use | R-02: render every code (32-255) of the project's own SHX file to a numbered glyph sheet (SVG / PNG) so a person, or a check against Unicode Arabic presentation forms (U+FB50-FDFF, U+FE70-FEFF), maps each code from the font's actual drawing, never by inference from text | TRY-IN-SANDBOX |
| [@mlightcad/shx-parser 1.3.5](https://cdn.jsdelivr.net/npm/@mlightcad/shx-parser@1.3.5/README.md): TypeScript, supports shape, **bigfont, extended bigfont and unifont** SHX, `getCharShape(code)` returns polylines + bbox | MIT (permissive, safe) | Active npm package (port of a C# parser) | No network in the parser | Same as above, for bigfont-type Arabic fonts that shxparser may not cover. [ezdxf 1.1+ `ShapeFileFont`](https://ezdxf.readthedocs.io/en/stable/tools/fonts.html) (MIT) also renders .shx text to paths but documents no bigfont support | TRY-IN-SANDBOX (fallback) |

How to use (method, own code): (1) a font-fact file per SHX family keyed by the font file's SHA-256, each code mapped to a Unicode **presentation form** with the glyph-sheet image as its source; (2) decode a string code by code to presentation forms, then Unicode NFKC normalisation folds them to base Arabic letters (presentation forms are compatibility characters), which also solves letter joining for matching room names; (3) check reading order on one label whose meaning is known from the plan (some Arabic CAD add-ons store text in visual left-to-right order; reverse only if the source shows it); (4) detection without font names: a STYLE whose font file renders codes 65-122 as non-Latin glyphs (compare glyph bounding boxes / stroke count with txt.shx) is an Arabic SHX style. Fonts are not in the DXF: the engine needs the client's own font file (third-party fonts, do not redistribute or commit). Codes with no sheet entry stay UNREAD, never guessed. Next step for the Lead: one task "SHX glyph sheet": parse the x-arab1b-style file that the Alsenan DWG references (owner supplies it, owner question if absent), render the sheet, map the 47 labels' codes, decode them, and compare with the room names visible on the scanned PDF plan.

### Answer to R-05: (a) members drawn as block inserts or open outlines; (b) membrane rolls with offcuts reused

| What (link) | Licence / commercial safety | Maturity | Security | Gap it helps | Verdict |
|---|---|---|---|---|---|
| [ezdxf `Insert.virtual_entities()` / `multi_insert()`](https://ezdxf.readthedocs.io/en/stable/blocks/insert.html): yields the block content transformed to WCS; mirrored inserts (negative scale) count as uniform scaling and transform geometry correctly; non-uniform scale may be wrong for TEXT / MTEXT / ATTRIB only; unsupported entities reported through `skipped_entity_callback`; XCLIP ignored; MINSERT needs `multi_insert()` | MIT (already a dependency) | Mature | None new | R-05a: footing outlines inside INSERTs on any layer, mirrored or not, become WCS polylines to test as members | ADOPT-IDEA: classify a member by geometry (closed outline from virtual entities + a mark text within it), not by the insert's layer; log skipped entities and XCLIPped inserts as HELD |
| [ezdxf edgeminer + edgesmith](https://ezdxf.readthedocs.io/en/stable/tutorials/edges.html) (new in ezdxf 1.4): `edges_from_entities_2d()` turns LINE / ARC / ELLIPSE / SPLINE / open POLYLINE into edges; `find_loop_by_edge()` (fast, non-recursive) or `find_all_loops(timeout=)` find closed loops; `gap_tol` = max vertex distance counted as connected; `loop_area()`, `is_inside_polygon_2d()`; `filter_coincident_edges()` removes doubles that make false loops; [edgesmith API](https://ezdxf.readthedocs.io/en/stable/edgesmith.html) | MIT (permissive; requires ezdxf >= 1.4, check the pinned version) | Part of ezdxf 1.4.x | None | R-05a: close open footing outlines with a reported tolerance: run once at gap_tol = 1e-6 m and once at e.g. 0.005 m; any loop that only closes at the larger tolerance is released with a "gap bridged: n gaps, max x mm" evidence line, or HELD above a cap | ADOPT-IDEA (and TRY-IN-SANDBOX on the T-073 synthetic fixture: a footing as mirrored INSERT, one as 4 loose LINEs with a 3 mm gap, one on a wrong layer) |
| [OR-Tools bin packing](https://developers.google.com/optimization/bin/bin_packing) (SCIP MIP, reports only OPTIMAL) and [CP-SAT bin-packing example](https://nbviewer.org/github/google/or-tools/blob/v99bugfix/examples/notebook/sat/binpacking_problem_sat.ipynb) (Apache-2.0 header) | Apache-2.0 (permissive, safe) | Very mature | Native wheels; no network at solve time | R-05b: strips (each strip length incl. 0.10 m laps) are items, a 10.00 m roll is a bin; minimise rolls; solver proves optimality, and the printable cutting plan is the item-to-bin assignment | ADOPT-IDEA / TRY-IN-SANDBOX. Proof without a solver: lower bound L1 = ceil(sum of strip lengths / 10.00); if first-fit-decreasing reaches L1 the count is optimal and the proof is one line in the ledger |
| Gulf membrane laps: [Polybit Bitustick 1000 TDS (Henkel, GCC)](https://dm.henkel-dam.com/is/content/henkel/mea-polybit-tds-polybit-bitustick-1000-en-mea): roll 1 x 15 m, side laps >= 50 mm, end laps >= 100 mm, start at drains, upslope over downslope | Manufacturer sheet (information) | Current | n/a | R-05b: laps are product-specific (owner chose 0.10 m on a 1 x 10 m roll): keep the lap and the roll size as inputs from the product sheet or owner, never a constant; an end lap is needed wherever a strip is longer than the roll or is joined from offcuts | Information |

Recommended next step (task): T-072 follow-up "rolls by exact packing": strip list per room from the fold (whole-width strips, cut edges), items = strip length + end laps, FFD with the L1 bound proof; when FFD > L1, solve with OR-Tools CP-SAT (time limit, report OPTIMAL or best-with-gap) in the sandbox; output roll count, cutting plan (roll n: room / strip / length / offcut), and total offcut. Hand-checked synthetic fixture: 3 rooms whose strips pack into exactly L1 rolls only if offcuts cross rooms. Stays HELD on Q-49 until the owner rules.

### New findings

| Date | What (link) | Licence / commercial safety | Maturity | Security | Gap it helps | Verdict |
|---|---|---|---|---|---|---|
| 2026-10-20 | [AECV-Bench](https://arxiv.org/abs/2601.04819) (arXiv 2601.04819, Jan 2026): 120 floor plans, counting doors / windows / bedrooms / toilets, plus 192 drawing QA pairs; multimodal models reach up to 0.95 on OCR / text QA but **only about 0.40-0.55 accuracy on door and window counting** | Paper (dataset licence not stated) | Recent benchmark | n/a | Gate 4 plan reader and opening counts: evidence that a vision-language model may be used to read printed text on scanned sheets but must never count openings or symbols as measured | ADOPT-IDEA (policy): VLM output is evidence for text only; opening counts come from geometry / schedules, and any VLM count is a cross-check that HOLDS on disagreement |
| 2026-10-20 | [Arabic presentation forms + NFKC](https://en.wikipedia.org/wiki/Arabic_Presentation_Forms-B) (U+FE70-FEFF, legacy contextual letter forms; plus U+FB50-FDFF): each isolated / initial / medial / final glyph has its own code point; verified with Python's own unicodedata (no download): U+FE8D `<isolated> 0627`, U+FE91 / FE92 / FE90 `<initial>/<medial>/<final> 0628`, U+FB58 `<initial> 067E`, all fold to the base letter under NFKC | Unicode (free use) | Standard | n/a | R-02 / T-047: decoding SHX codes to presentation forms then NFKC gives matchable room-name strings regardless of which contextual form the font drew | ADOPT-IDEA (in the SHX decoder) |

## 2026-10-18 (scout run): 5 findings, 0 requests answered

No docs/agents/RESEARCH_REQUESTS.md or docs/agents/FEEDBACK.md on agents/control (5fe920c), so no Lead request to answer; this run targets the scoreboard gaps instead (Q-11 DWG conversion block, Q-12 concrete verdicts, T-028 unlabelled rooms).

| Date | What (link) | Licence / commercial safety | Maturity | Security | Gap it helps | Verdict |
|---|---|---|---|---|---|---|
| 2026-10-18 | [ACadSharp](https://github.com/DomCR/ACadSharp) ([NuGet](https://www-1.nuget.org/packages/ACadSharp)), plus its TypeScript port [acad-ts](https://cdn.jsdelivr.net/npm/@node-projects/acad-ts@2.3.0/README.md): reads DWG AC1014-AC1032 (R14 to 2018+) and writes DXF AC1012-AC1032, ASCII and binary, with blocks, layers, styles | MIT (both; permissive, safe) | About 890 stars; 3.8.0 on 2026-09-21, 1.7 M downloads; acad-ts 2.3.0 | Managed .NET (no native code); no network calls documented; acad-ts builds and tests offline. Not run | Q-11 / TD-11: agents cannot turn P7757.dwg (or villa 2's DWG) into DXF in the sandbox, and LibreDWG 0.13.3 (D1) has no independent cross-check (handoff: BLOCKED_EXTERNAL_INPUT, needs an AutoCAD export). A second, separately written decoder gives that check without the owner | TRY-IN-SANDBOX: next step for the Lead: one task, worker installs the .NET 8 SDK (or Node for acad-ts) in a throwaway sandbox, converts P7757.dwg and ST7757.dwg from Drive to DXF 2018, and diffs entity counts per layer, block inserts, text strings and polyline lengths against the LibreDWG dwgread JSON; adopt as a pinned external converter only if both agree, record version + sha like decoder_pins.py |
| 2026-10-18 | Q-12 hand-check formulas (stair + dome -9.83 m3, pool -8.85 m3): stair per flight = waist (width x slope length x waist thickness) + steps (N x R/2 x T x width) + landing (L x B x t) ([InfraLens handbook](https://infralens.in/handbook/concrete-volume-calculator), after SP 34 / IS 456); dome shell = outer spherical cap minus inner cap, cap V = pi h (3a^2 + h^2) / 6 with base radius a and rise h, sphere R = (a^2 + h^2) / 2h, inner cap R - t ([Wikipedia, Spherical cap](https://en.wikipedia.org/wiki/Spherical_cap)); pool = base slab + mean wall perimeter x wall height x thickness, plus coping / ring beam if drawn | Public formulas (ideas only) | Textbook geometry | None | Concrete WAPE 17.03 %, all of it from the three UNRESOLVED lines: shows per element which part (landings, steps, ring beam, inner-cap subtraction, pool walls vs slab only) the engine or the freelancer left out | ADOPT-IDEA: next step: verifier/worker builds one hand-calc sheet per UNRESOLVED line from printed drawing dimensions (each term a separate row: waist, steps, landing; outer cap, inner cap, ring beam; pool slab, each wall), then labels each term ENGINE_RIGHT / FREELANCER_RIGHT / RULE_DIFFERENCE for Q-12; the engine's stair rule should emit the same three terms so gaps are traceable |
| 2026-10-18 | [ResPlan](https://github.com/m-agour/ResPlan) ([paper, arXiv 2508.14006](https://arxiv.org/html/2508.14006v1)): 17,000 vector residential plans, room polygons (bedroom, bathroom, kitchen, living, balcony, storage, pool, stairs), walls / doors / windows as polygons, room-connectivity graphs with door / arch / shared-wall edges | Data CC BY 4.0 (commercial use allowed with attribution), code MIT | 14 stars; 2025 paper | Data ships as a Python pickle (ResPlan.pkl): loading it can run code. Do not load; the Kaggle copy is also pickle-based | T-028 (unlabelled room typed with no code) and T-010 (wet vs dry): the room-graph shows which context separates wet rooms (small area, single door, adjacent to a bedroom or corridor, shares a wall with another wet room) | ADOPT-IDEA: no data load; next step: in T-028 add a context score (area, door count, adjacency to bedroom / kitchen / other wet room, fixture symbols) that only proposes a wet / dry type on the HELD record, never commits scope; if the Lead later wants statistics, a sandbox task converts the pickle once in an isolated container to JSON and checks it |
| 2026-10-18 | [ODA MCP Servers](https://www.opendesign.com/blog/2026/august/oda-mcp-servers-faq.md) (Open Design Alliance, launch September 2026): self-hosted MCP access to DWG, IFC, STEP (DGN, Revit later); query quantities, compare revisions, volume / area in fixed tested code; DWG write-back | Commercial: ODA Core Package+ membership (Sustaining / Founding / Corporate); royalty-free per company | New (Sept 2026) | Local mode has no outbound network path (per ODA); write-back tools would need a read-only allowlist | DWG intake and revision diff (BOARD idea 9) without LibreDWG; would also cover villa 2 | WATCH: membership cost and closed SDK; reconsider only if ACadSharp fails the cross-check above |
| 2026-10-18 | [dwg-mcp-server](https://www.getdrio.com/mcp/io-github-dimitrovakulenko-dwg-mcp-server/md) (npm @dmytro-prototypes/dwg-mcp-server 0.1.4, 2026-05-10): read-only MCP server for inspecting DWG files, folder allowlist via DWG_MCP_HOST_FOLDERS | Unknown (repository page could not be opened this run) | 0.1.x prototype | Launched with `npx -y` (fetches and runs code at start); backend decoder unknown | DWG inspection for agents | WATCH: unknown licence and decoder; the engine already decodes DWG itself; recheck when it states its backend and licence |

Reference noted for doors / windows unit (scoreboard: engine nr vs freelancer m2): Drive "Urban Projects - Kuwait Engineering References" / "01 — Kuwait References" holds "المواصفات العامة للمباني والأشغال الهندسية - الكويت 1990" (MPW General Specifications, CSI divisions); its Division 8 is where a measurement unit for aluminium doors and windows would be stated (11.8 MB, above the 10 MB connector download limit).

## 2026-10-17 (scout run): 5 findings

| Date | What (link) | Licence / commercial safety | Maturity | Security | Gap it helps | Verdict |
|---|---|---|---|---|---|---|
| 2026-10-17 | [Li et al. 2026, knowledge-driven agent for quantity checking of concrete bridges](https://www.citedrive.com/en/discovery/a-knowledge-driven-intelligent-agent-for-automated-quantity-checking-of-concrete-bridge-structures/) (Applied Sciences, doi 10.3390/app16189366): two-stage detect (region, then parameter) + OCR + table parsing, each value linked to parameter type, location and component in one record; deterministic rules compute concrete and check reinforcement consistency; human check BEFORE calculation | Paper (idea only; no code published) | Peer-reviewed 2026; 1,362 annotated drawings | None (nothing to run) | Rebar / concrete from structural schedules (T-009, rebar -40.6 %): parameter accuracy 82.77 % -> 100 % after the human check, concrete volume error 23.94 % -> 2.98 %; prompt-only LLM baselines did worse | ADOPT-IDEA: link every schedule value to (element, location, parameter) and hold it for review before any tonnage is computed |
| 2026-10-17 | [dxfstructure](https://pypi.org/project/dxfstructure/): DXF detailing tool that reads bar marks drawn as text (`[1] - #12 L=2120`, quantity expressions such as `2*2#12-[4]`) and writes a bar schedule with shape column | GPL (copyleft): do not copy code into the private product | 0.4.8 beta, July 2022, alpha status; ezdxf + PyQt5 | Desktop GUI, no network noted; not run | Rebar populations from bar-mark text in structural DXF (T-009) | ADOPT-IDEA: use its notation as test cases for our own bar-mark / count-expression parser (write ours from scratch) |
| 2026-10-17 | [pygeoops.centerline](https://pygeoops.readthedocs.io/en/stable/api/pygeoops.centerline.html) ([PyPI](https://pypi.org/project/pygeoops)): medial-axis centreline of a polygon with width-relative densify, short-branch pruning and simplify | BSD-3-Clause (permissive, safe) | 0.6.0, Nov 2025; pure-Python wheel on Shapely / GeoPandas | Pure Python per wheel tag; no network noted | Blockwork wall length (-36.5 %, about 140 m short, T-007): centreline length of wall-hatch / wall-pair polygons as an independent cross-check of `arch_walls.py` runs, with `min_branch_length` set from wall thickness so T-junction stubs are kept or pruned explicitly | TRY-IN-SANDBOX: synthetic L / T / cross walls with known centreline length before any adoption |
| 2026-10-17 | [K.C. Tang, Taking-off techniques](https://kctang.com.hk/web/node/248): QS centre-line rules: external `(L+W)x2`, internal `(L+W)x2 - 8T`, centre line `(L+W)x2 - 4T` (1T per external corner; paired internal/external corners cancel, recesses add `2A+2B`); measure overall first then adjust; openings deduct then add head, sill and 2 reveals; columns/beams add or deduct finish faces per exposed side | Public web page (ideas only) | Practitioner reference | None | Blockwork length, plaster and paint, skirting: a closed-form per-building check that flags when engine wall length departs from the centre-line girth | ADOPT-IDEA: add a girth check (external girth - 4T vs engine external-wall centreline) as a scoreboard diagnostic |
| 2026-10-17 | [puran-water/autocad-mcp](https://github.com/puran-water/autocad-mcp): MCP server, 8 tools (drawing, entity, layer, block, annotation, view, system); headless ezdxf backend or AutoCAD LT via keystroke IPC | MIT (permissive) | About 570 stars, v3.1 | `system.execute_lisp` runs arbitrary AutoLISP with no allowlist; file IPC in `C:/temp`; drawing text could steer an agent into it | None for measurement: it writes drawings, it does not read quantities; engine already uses ezdxf directly | REJECT: no accuracy gain and an arbitrary-code path |

## 2026-10-17: BOQ engines study (owner-supplied; verdicts PROPOSED, scout to confirm)

Full study, with file evidence: [research/2026-10-17_BOQ_ENGINES_STUDY.md](research/2026-10-17_BOQ_ENGINES_STUDY.md)

| Date | What (link) | Licence | Could improve | Risk | Verdict (proposed) |
|---|---|---|---|---|---|
| 2026-10-17 | [OpenConstructionERP](https://github.com/datadrivenconstruction/OpenConstructionERP): recipes (assemblies) with per-unit factors and formulas, waste factors, explainable cost matching, revision change flags, contract quantity baseline | AGPL-3.0 | Recipe layer for blockwork, plaster and tiles; three-quantity lines; revision flags | AGPL: copying code would force publishing ours. Its Middle East pack has no Kuwait rules | ADOPT idea |
| 2026-10-17 | [OpenTakeoff](https://github.com/Kentucky-ai/opentakeoff): role-based shapes, order of xN then waste then rounding, skirting from perimeter minus stated openings, overlap check (sum - union = 0), review stamps | AGPL-3.0 | Deduction and skirting traceability, double-count check, withheld-item list | AGPL; it works in feet and covers US interior finishes only | ADOPT idea |
| 2026-10-17 | [CostX](https://www.rib-software.com/en/blogs/rib-costx-functions): dimension groups feeding workbook functions, composite rates, auto-revisioning | Commercial | Wall-area-by-group-height; revision re-match with review warnings | Closed; public docs only | WATCH |
| 2026-10-17 | [PlanSwift](https://constructconnect-help.atlassian.net/wiki/spaces/PSUPPORT/pages/48431425/Useful+Formulas+for+PlanSwift): parent/child formula tree, openings as children of the wall | Commercial | Openings modelled as children of their host wall | Closed; public docs only | ADOPT idea |
| 2026-10-17 | [Togal.AI](https://help.togal.ai/en/articles/15602901-ai-powered-area-and-wall-detection): net, gross, footprint, centreline and door widths per room at once | Commercial | Store several quantity variants per room or wall | Closed; public docs only | ADOPT idea |
| 2026-10-17 | [Bluebeam](https://support.bluebeam.com/revu/how-to/tips-and-tricks/improve-takeoffs-with-quantity-link.html), Cubit, PriMus, [Autodesk Takeoff](https://help.autodesk.com/cloudhelp/ENU/Takeoff-Takeoff/files/Symbol_Detect.html): filter-linked quantities, measurement rows with negative openings, pending-until-accepted detection | Commercial | Measurement-row audit format; pending state for detections | Closed; public docs only; some internals uncertain | WATCH |
