# progress.md: owner instructions, decisions and inputs (kept by the main chat)

The owner asked (2026-11-11): "anything important i said to you or gave you, save it in a file called progress.md".
Newest first within each section. Owner words in quotes are verbatim. Full records stay in OWNER_SESSION_CHANGES.md,
OWNER_QUESTIONS_ANSWERED.md, AGENT_BRIEF.md and BOARD.md; this file is the short index. No client data in this file.

## 0. For a fresh main-chat session (read this first)

- DELIVERY MODE (owner 2026-11-13): docs/agents/DELIVERY_MODE.md is the operating document; the board was rebuilt around rows T-760 .. T-775 (FILL -> GENERALISE -> SECOND VILLA); the workbook docs/agents/boq/ is the scoreboard.

- Role: the main chat is the owner's single point of contact and auditor for the agent team (Lead, Workers 1-3,
  Checker / Verifier; Scout paused). It records owner decisions on the board, writes the daily update (scheduled task
  trig_01QAPf5hzouxE6bZh9PAbEJ6, 07:31 Kuwait: run ledger + scorecard), keeps RUN_LOG.md to 24 h (older entries to
  archive/) and LEAD_REPORT.md to 3 entries, and reports material issues at once.
- Board edits: edit files under .work/board/docs/agents/, then commit and push agents/control from .work/board
  (commit message ends with the attribution lines; no model ids). Every owner change also gets one row in
  OWNER_SESSION_CHANGES.md.
- Engine facts: read-only from origin/claude/access-permissions-setup-ii24ws (candidate line index
  research/agents_t*/out/LINE_INDEX_V3_0_*.json; newest Lead report in LEAD_REPORT.md).
- main holds only the agent configuration (CLAUDE.md, .claude/settings.json, scripts/agent_env.sh + tests);
  changes go by PR and the owner merges.

## 1. Standing rules (always apply)

- Focus: "I always want you to focus on the boq and not urban project manager" (2026-11-07). App work only when the
  owner asks explicitly.
- UrbanProjectsManager: "do not touch the Urbanprojectmanager, i added it here so that in the future you can have
  access of projects and maybe you can fill in later or we can use our agents to make contracts, or marketing or
  anything else" (2026-11-08). No agent reads, changes, branches or pushes it unless the owner asks.
- Merging: "You can merge everything related to boq" (2026-11-08); "why do i merge, its your role" and "Push and
  merge for Urban project AI and not urbanprojectmanager" (2026-11-12). The main chat pushes and merges in
  Urban-Project-AI only, never in UrbanProjectsManager. Direct pushes to main stay denied; main changes through
  merged PRs. PR #7 (merged by the owner 2026-11-12) removed the merge block: the main chat now merges.
- No assumptions: only the owner's rules and what the drawings print; unresolved stays HELD as a range or blank,
  never 0. "do not assume" (2026-11-11).
- Never copy client drawings, client data, names or personal data into the repository (it is public). Google Drive
  is read-only. Never write to urban-boq-private-data.
- Never answer an owner question or write an answer to the board without the owner's own words in the chat.
- No automatic pricing (KD). No change to frozen methods or released versions; V2.9 + route G stays the default;
  V3.0 stays an opt-in candidate. No RFI sent outside without the owner's written approval.
- No schedule or prompt changes without the owner's words; no duplicate tasks; do not interrupt productive agents.
- Do not bypass safety controls or platform permissions; do not change the GitHub default branch.
- Reports: plain engineering words, quantities with units, before / after; one daily update (07:31 Kuwait) with the
  scorecard in at most 15 lines; immediate report of a material quantity change, safety contradiction or milestone
  risk; push notifications only for critical alerts. Be lean on tokens.
- "The priority now is actual BOQ delivery, not further investigations or prompt/rulebook expansion." Report
  integrated quantities and verified lines, not agent activity (2026-11-08).

## 2. Decisions by date

### 2026-11-13 (delivery reset)
- MAIN FILLS: fill 1 (185 rows: floor bed, formwork ratio, roof layers, disposal) and fill 2 (22 rows: 11 dry-room plaster lines 866.1 m2 at 4.34 / 3.84 / 4.04 with default heads, paint 675.8 m2) in docs/agents/boq/fixrows/MAIN_FILL_ALL.json for Worker 3 to wire. Freelancer method studied from the 6 parsed workbooks: plaster / paint perimeter x 3.6 m no deductions; blockwork length x 4.0 gross; slabs area x 0.16; blinding = plot 15 x 31.37 x 0.10; his compare rows show the gap is mostly our HELD lines (blockwork 561 / 793, plaster 857 / 969, external 1,160 / 1,503).
- Drive: connected on the owner side but this session could not attach any connector (platform fault); owner asked to upload the جلال sample BOQ here.
- OWNER: "work strong to finish the project in 4 days": answered = Alsenan BOQ complete + compare + end-to-end run by 17 Nov possible (conditions: Drive reconnected, answers within the day, no new scope, agents at half frequency); generic engine proven on a second villa NOT in 4 days. Main chat built the Compare sheet (candidate vs freelancer per trade) into docs/agents/boq/build_boq.py; workbook V3.0.78 committed. FINDING: all 76 candidate modules (arch_v30 .. arch_v3078) restate Alsenan lines by id from maps; the generic engine is V2.13 + route G + the base V3.0 consolidation; GENERALISE stream (T-772) is where the product is made.
- OWNER: "we have been working on the project for more than 2 weeks and we havent reach a good progress ... reaching the level where i can send a project in pdf, dxf, dwg and i get the boq closer or more accurate to the freelancer excels. Fix the issues and re arrange". Main chat wrote DELIVERY_MODE.md, rebuilt AGENT_BRIEF.md, archived the board header notes and 301 MERGED rows, replaced the backlog with T-760 .. T-775, lightened the Checker gates, and asked the owner to halve the agent frequency (owner-only).
- PLASTER HEIGHT: "4.5 and 4.2 is from slab to slab as we measured correct? which means depends on slab thickness for example 16cm. minus 4.2 so we get 4.04 plastering correct, check it." Checked: levels are finished-floor levels; engine used storey - 0.05 build-up - 0.16 slab = 4.29 / 3.99; owner rule = storey - slab = 4.34 (GF) / 4.04 (1F, 2F). Adopted; about +1 % plaster.
- CLARIFIED: "5, not maxed 1m^2 for ignored i mean if there was an ignored (calculate by calculator the area manually) and for small peices if you know its under 0.05m^3 ignore them and add a safety of 1m^3 if they do not even reach 1m^3." -> ignore only pieces known < 0.05 m3; anything larger hand-calculated; safety 1 m3 if the ignored sum < 1 m3, else the sum.
- HEIGHTS: "3. company default is correct however alsenan is 4m and 4.5m which will increase concrete, walls blocks, plastering, paint, ceramic on bathroom and walls etc." -> printed levels govern (GF 4.50, 1F / 2F 4.20 storeys on the drawings); false ceiling default = clear height - 0.90 m (GF ~3.40, 1F ~3.10), wet rooms 2.70 m.
- NEVER STOP: "I told you everything i can explain to you. so now you need to see whatever you dont understand or cant work on, find a way to do either add extra based on area or find a way to calculate it manually through pdf plan or calculations no need to only do geometric for example? what if geometric didnt this area? do we stop progressing? or find a better or sufficient way?" -> fallback order geometry -> manual PDF / hand calc -> company defaults -> ratio / area allowance -> safety; every line gets a figure with its method label; the main chat's proposed defaults are adopted (full list on BOARD.md 2026-11-13 13:30).
- Owner on progress: "I dont think there is a progress in here its been 2 weeks nearly with agents". Main chat found 3 -> 13 Nov: concrete +1.6 m3, formwork +33 m2, masonry materials added, plaster height corrected, verified lines unchanged.
- MATERIALITY: "If we ignore the 0.1m3 once its fine twice is also fine, 5-6 times is also fine as long as we add at the end a safety of 1m^3. the 0.01 is useless so less than 0.1 we can if we can add later the sum of the missing or ignored." Rule: concrete pieces / differences < 0.1 m3 ignored (logged), one safety allowance line at the end = max(1 m3, sum ignored); other units: nothing below 1 %.
- "And lets work with your suggestions." = (1) materiality, (2) company default values for unprinted dimensions (values from the owner), (3) the owner sends the designer list, (6) the main chat builds the full BOQ workbook now; agents only fix the gaps it lists.

### 2026-11-12
- PAINT RULE: "Paint, technically would be close enough to plastering (inside the building) outside will also should be the same, the difference is with the corners outside maybe only and lm for windows doors and corners, so the Area is the same." Confirmed: paint stops at the false ceiling (Q-72 kept); no paint on tiled faces. Paint m2 = plaster m2 of the same faces minus those two; corners / openings are lm items.
- "why do i merge, its your role" / "Push and merge for Urban project AI and not urbanprojectmanager": merging is
  the main chat's job in this repository. PR #7 opened (settings allow the main chat to merge PRs; agents never merge,
  written in CLAUDE.md). PR #6 (decode fix) merged by the owner.

### 2026-11-11
- REBAR PARKED: "We will do the ratio rebar in tons, and since rebar is taking a while here we can leave at at the
  very far end of the project. We can test later everything and ignore accurate rebar and give approx rebar in tons."
  No kg/m3 assumed; all rebar work stops; the detailed 9.6 t already measured stays; at the end one approximate ratio
  figure in tons, labelled ESTIMATE. Q-81 closed as DEFERRED.
- Note on the ratios: the 2026-11-09 decision text had "[my figures: …]" with no numbers; no figures were received.
- "merge it": PR #5 (setup / venv fix) merged to main fc03a1fb.
- "fix decode": PR #6 opened (decode accepts raw Drive downloads, fails loudly on short writes). Owner merges.
- "Approve" (improvement points): join approved work into the candidate first (Worker 3, two rounds); reserve the
  next version number on the board before a Gate B package starts; one designer question list (owner sends it);
  idle worker slots plan the 38 missing categories, MEP last; main chat may edit scheduled tasks (not possible:
  repository settings deny it for every session, agents included; left in place).
- "save it in a file called progress.md": this file.

### 2026-11-09 (change of focus)
- Order of work: concrete first (every member from the drawings, no shortcuts) -> rebar (now parked, see 11 Nov) ->
  masonry (blocks, mortar, glue, lintels) -> plaster (internal, external) and paint -> tiles and adhesive ->
  waterproofing -> earthworks (backfill, disposal) -> the 38 missing categories with a plan, MEP last.
- Q-79 answered: "internal plaster 1:4, external render 1:4, spatter dash 1:2".
- 10 Nov = trial BOQ with held items as ranges. Asked for a realistic date for a BOQ with no held lines in concrete,
  rebar, masonry, plaster and tiles (given: about 17 Nov, rebar now excluded) and the top 3 blockers.
- "fix setup: PR with a test, I merge" -> PR #5. Include 7-day run numbers in the update.

### 2026-11-08
- Delivery directive: integrate the waiting packages one at a time with Checker validation after each; complete
  trial BOQ for 10 Nov with every trade represented, HELD only where unavoidable; never call it complete while a
  major trade is missing; keep the freelancer reference comparison separate from engineering verification; no new
  investigation tasks, no pricing, no frozen changes, no owner questions unless essential.
- "rename it": local session branch renamed to main-checkout (nothing changed on GitHub).
- "You can merge everything related to boq": PR #4 (run allow-list for research scripts) merged to main fd71bc30.
  PR #1 left open (main holds only the agent configuration).
- Asked about external repos (OpenConstructionERP, bbs-automation, dwg-takeoff, DWG / PDF readers): none adopted
  now; possible later trials after 10 Nov: ezdwg (local) and a non-client sample on a commercial reader.

### 2026-11-07
- "go A, with conditions: merge PR #3 first" -> PR #3 merged; run allow-list change limited to
  research/agents_t*/*.py, refuses '..' and symlinks, python -I inside .work only, with a test.
- Q-80: "40×20 face, 12.5 blocks/m² (tell me if the drawings show otherwise)".
- PyMuPDF: keep for now, review after 10 Nov.
- The freelancer workbooks (floors, railings) and the 1990 specification: not blockers; owner will upload.
- Until the merge, the Lead gives workers only unblocked work and avoids empty runs.
- App: client-statement and dashboard changes were made, then "undo what you did for those 3 things" -> reverted
  (main 5b36716). Focus back on the BOQ.

### 2026-11-02 (and earlier, carried in AGENT_BRIEF / OWNER_QUESTIONS_ANSWERED)
- Black blocks 12.5 / m2 (Q-75), block mortar 1:4 (Q-78), AAC glue 3.5 / 4.5 kg/m2, tile adhesive bags per tile
  size (Q-45), plaster to the slab underside / paint to the finished ceiling (Q-72), full opening deduction (Q-73),
  lintel stock lengths and bearing, wet-area wall build-up, backfill lift 150 mm provisional; T-350 earthworks rules
  (sources KOC-C-005, ASTM D1557 / D6938, QCS 2024; geometry always calculated).
- Stage 1 token plan approved; handoff <= 600 characters (Checker flags, never invalidates); scorecard in the daily
  update; report material issues at once.

## 3. Things the owner gave

- Google Drive (read-only): folder "Urban BOQ private data" with one subfolder per project (Alsenan chalet: the
  structural and architectural drawings, sanitary PDF, freelancer workbooks; development project 2 paused) and two
  engineering-reference folders. Referred to by folder and title only.
- 2026-11-05: a private package of contracts, samples, studies and analyses was built for the owner (not in the repo);
  his questions on invoices: the system makes quotations and contracts only; an invoice type would be new work;
  suggested numbering UPC-Q / UPC-C / UPC-INV per year (a proposal, his decision).
- The UrbanProjectsManager repository (attached for future use only, see section 1).

## 4. Open owner actions (not yet confirmed)

- Make the repository private.
- Upload the freelancer floors / railings workbooks and the 1990 specification (not blockers).
- Send the designer question list once the Lead has compiled it.
- Stair skirting form (ORR-007) still with the owner.
- PyMuPDF review after 10 Nov.

## 5. Where the BOQ stands (2026-11-11)

- Candidate ARCH_TAKEOFF_V3.0.68 (not released); released V2.9 + route G unchanged.
- Joined since 8 Nov: blockwork materials (black blocks 1,075.8 -> 2,571.3 + held 698.7 .. 702.9; mortar 1.27 ->
  2.59 m3), face deductions / ceilings, plaster height (internal plaster 363.4 m2 + 932.7 .. 1,006.8 held), six
  concrete rounds (beams, necks, columns, ground beams, lintels, pool blinding, boundary band).
- Waiting: plaster / paint with the wet band, external plaster, stairs, roof, formwork +33 m2, waterproofing.
- Verified whole lines: slab 60.28 m3 and lift-pit blinding only. Target for no held lines in concrete, masonry,
  plaster and tiles: about 17 Nov; main risk: dimensions the drawings do not print (designer list).

### 2026-11-13 evening: QS-office samples (owner upload, three PDFs; no client names kept)
- Owner: "here are they جلال samples" (not Alsenan; "maybe would help you for our own system"). Recorded in
  docs/agents/OUTPUT_FORMAT_REFERENCE.md: the document shape (inputs sheet with slab-to-slab storey heights and wastage
  %, key-quantities page, one sheet per trade, corners in lm by type, steel by diameter = length x d^2/162), the rules
  seen (block count by volume = 12.5/m2; wastage apart: concrete 5 %, steel 10 %, blocks 5 %, tiles 10 %; paint =
  plaster faces - tiled; ceilings = floor area) and plausibility bands per m2 of internal floor (3 Kuwait villas agree
  on 120-140 kg steel per m3 of concrete = the owner's end-of-project approximate-tons basis).
- Workbook now has a "Key quantities" sheet (calculated / held / blank per trade + per-m2 ratio vs the band).
  V3.0.78 with fill: concrete 291.5 + 44.6..66.3 held (0.68 m3/m2, in band); blockwork 467.8 net with 15 blank lines
  (1.10/m2 vs band 2.5..3.2 = the biggest hole); external plaster 0 (15 blank); corners 0 calc; backfill 0 calc;
  sanitary count 0. These four are the next fills.

### 2026-11-13 evening: owner's parallel run ("blind BOQ" PDF, 11 pages, 13 Nov) and the facade fill
- Owner ran the same engine (V2.9 + route G) through ChatGPT on the Alsenan drawings and did a fill pass on top; not blind
  (it admitted having seen benchmark totals). Its figures are now the "Parallel run" column of the Cross-check sheet.
  Where it is close to the freelancer it used the same fill-by-default approach we are running (blockwork 1,092 by wall
  band x height - openings = T-765). Where it is low (plaster 733, paint 554) it used clear heights below the owner rule.
- MAIN FILL 3 (fill3_facade.py): facade render from the released facade runs (GF 105.89 / 1F 63.17 / 2F 29.8 lm) x
  storey heights - openings = 762.3 m2 + plinth 105.9 (GF run x printed F.F.L. +1.00) = 868.1 m2 ESTIMATE. The parallel
  run got 769.2 by the same method with 98.9 lm on GF. MAIN_FILL_ALL now 214 rows.

### 2026-11-13 evening: owner decisions on the cross-check
- Owner: "Why wet tiles calculated as 2.7m height? freelancer on 3m right? lets do 3m too." -> wall tiles 3.00 m from
  F.F.L. in every wet room (MAIN FILL 4). Fact: the engine's released tile lines were NOT at 2.70; they ran to the decor
  ceiling (clear height - 0.90 = 3.44 GF / 3.14 upper); 2.70 was the parallel run's default. 3.00 lowers ours.
- Owner: "rebar use the normal okay, but also add our calculation method to get a similar calculation" -> BOQ rebar = ratio
  120-140 kg/m3 (Key quantities row); the detailed takeoff stays as the parallel check (must converge).
- Windows: owner "i gave you all the results, what is missing?" -> Q-76 A (W17 = 9.87) was answered on 24 Oct but never
  wired; wired now (MAIN FILL 4). Still missing: W02 one-or-two windows (D-53, owner said drawing / designer evidence),
  shutter leaves W11 / W12 / W14 (fence), and the freelancer's 116.9 m2 is aluminium incl. external doors.
- Roof +9.70 membrane: held 115.66..115.81 for a 0.16 m2 band question -> released at the low end (materiality).
  The annex roof (+4.30, finish 54.92 m2) has NO membrane line in the index: new line needed (T-770 wiring).
