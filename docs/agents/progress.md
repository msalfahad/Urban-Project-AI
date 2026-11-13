# progress.md: owner instructions, decisions and inputs (kept by the main chat)

The owner asked (2026-11-11): "anything important i said to you or gave you, save it in a file called progress.md".
Newest first within each section. Owner words in quotes are verbatim. Full records stay in OWNER_SESSION_CHANGES.md,
OWNER_QUESTIONS_ANSWERED.md, AGENT_BRIEF.md and BOARD.md; this file is the short index. No client data in this file.

## 0. For a fresh main-chat session (read this first)

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
