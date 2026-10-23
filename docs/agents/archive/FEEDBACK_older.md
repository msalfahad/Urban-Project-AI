# Older Lead feedback entries (moved from FEEDBACK.md to keep the last 20; newest first)

## 2026-10-20 22:15 (lead run)

- **T-122 / T-123 / T-124 / T-110: WORKED (MERGED 21:05, verifier run 45, each re-measured on the Drive DXFs).** 1F
  landing 4.875 printed / 4.865 m2 drawn to marble once, porcelain 33.594 .. 33.711 HELD (hand 33.713); GF facade 98.887 vs
  hand 105.887 m (-6.6 %), passage 1.20 x 4.70 with the mouth open (Q-67 A condition met); membrane V5: no released or proven
  roll count changes; beam register 64.764 vs freelancer 65.97 m3 (-1.8 %) with B29 and B21 drawn-vs-schedule CONFLICTs
  confirmed. T-110 is PARTIAL on the beam line itself (HELD 4.123 .. 8.553 m3, 3 projection pieces, D-26..D-28). Decision:
  T-102 promoted (the two printed section cuts settle two spans); the rest stays with the designer list; T-122 joins V3.0.1
  (T-133).
- **T-126 route G scope (blinding by member, undrawn columns): WORKED (MERGED cd34bd0, run 46).** Columns 36.714 -> 34.446
  m3 (5 undrawn occurrences NOT_PRESENT, -2.268, ENGINE_RIGHT); blinding 22.155 -> 15.179 m3 released, and the checker's own
  union of the raw footing outlines gave the same 151.794 m2; held F10 0.480 .. 0.590, ground beams 5.724 .. 9.423, straps
  0.772. Freelancer's 47.055 whole-plot plate = RULE_DIFFERENCE. Decision: wire into V3.0.1 (T-133); column heights stay
  with T-119 (freelancer 28.547 is still -17 % on the height basis).
- **T-129 stair arrivals once: WORKED (MERGED 1513f1d, run 46).** 2F arrival 4.875 m2 marble (Q-70 A condition met: the
  195 is in the stair's own 1200 + 3300 + 1950 chain), 2F porcelain 2.500 not 3.900; front floor 7.375 vs freelancer 7.70
  (+4.4 %). Found a released defect: V2.9 counts the 1F -> 2F lower flight again on the 2F plan (+3.45 m2 tread marble,
  +11.5 lm steps). Decision: code task T-135 (lane A); the arrival joins V3.0.1 (T-133).
- **T-131 V3.0 skeleton: READY (33f1da2), awaits the checker.** 1519 of 1528 Alsenan lines byte-identical; straps 3.781 ->
  3.390 m3 (+11.5 % -> -0.07 %), GF facade 98.887 -> 105.887 lm under Q-67 A, 1F porcelain 44.869 -> 38.459 .. 38.979 range;
  L4 396 = 396. Decision: verifier checks it first; T-133 / T-134 build on it once merged.
- **T-105 beam ledger + stair rework: READY (7975663), awaits the checker.** Firewall declarations only; beams 68.84 vs
  65.97 m3 (+4.4 %, 18 spans held), main stair 5.011 vs 8.131 (RULE_DIFFERENCE). Decision: after it merges, T-136 (footing
  rebar) may take the same registry file.
- **Silent runs (recurring cause 4, new form): FAILED.** Worker 2 21:39 (1.5 min, no line, no commit) and worker 3 21:59
  (STARTED written, 9 min, no claim, no final line) although claimable TODO existed for both (T-127 / T-128 / T-125;
  T-130). Cause NOT KNOWN from the repository. Decision: no board change can fix it; P-01 (owner's Test B + repo-attached
  config) stays the fix; reported under NEEDS FIXING.

## 2026-10-20 18:20 (lead run)

- **T-116 stair openings and wells out of room floors: WORKED (MERGED 559269, verifier 16:49 run).** Candidate 1F living
  porcelain 38.459 .. 38.979 m2 (hand 38.588 .. 38.990, freelancer 38.96 inside) vs released 44.869. Not wired. Your Q-66
  B (16:23) makes the 4.875 m2 landing marble, once: porcelain 33.584 .. 34.104, stair marble 44.365. Decision: T-122 (room
  rows with polygons, landing counted exactly once across floor, marble and void lines; your 17:54 condition), NO REPO CODE.
- **T-109 passage walls in the GF facade run: WORKED, then CONTRADICTED IN PART (MERGED 4fddf74).** Piece 105.887 m = hand;
  but T-121 reads the slab plans: the 1.556 m2 T-109 called "open to the sky" lies under the GF roof slab, so the passage
  is roofed full length with one open mouth; by T-109's own rule 5 the run would be HELD 98.887 .. 105.887. Is the passage
  outside? Your UP-SPACE-002 makes such a space POSSIBLY_EXTERIOR until a project decision: owner Q-67. Decision: T-123
  (perimeter 105.887 / billable 105.787 / reveal returns 0.100 apart per your Q-64 B and 17:54 (3); passage roof re-read).
- **T-117 wall run vs hand, run by run: WORKED (MERGED bc21314).** Engine 149.42 / 118.20 / 39.60 vs hand 143.16 / 120.75 /
  39.78 m: GF +4.4 % hides +16.63 m of bands across open floor and passage mouths and -10.37 m of misses; the piece is not
  ready to wire. Glazed lines 12.05 m are the whole GF hand-vs-freelancer gap. Decision: T-125 (MASONRY_CENTRELINE_V2) +
  owner Q-69 (glass lines in the run?); D-12 walls with columns stay CONFLICT for the designer.
- **T-120 membrane release version V2.13: PARTIAL (READY 17:46).** 33 tests, L4 no new failure, but Alsenan NOT run (Drive
  zip decode refused "[Untrusted Code Integration]"). Found: MEMBRANE_FOLD_V3's Q-58 A count can use one leftover twice.
  Decision: verifier runs the Alsenan script; stays a candidate (owner 17:54 (5)); T-124 audits every Q-58 A count
  (wet 19 / 21, roofs 8 + 6, 2F 17) for a leftover booked twice and builds a fold that books each leftover once.
- **T-121 slabs over outside air: WORKED by hand, pending verification (READY 18:07).** 5 places 45.632 m2 CALCULATED, the
  concrete above them is in the slab lines (5.304 m3, no omission); 31.612 m2 in neither BOQ; freelancer pool ceiling
  19.154 vs 14.020 net (+36.6 %, UNRESOLVED). Decision: owner Q-68 (soffit finish), verifier re-measures passage + pool court.
- **Team: 4 INCOMPLETE runs in this window (worker 1 16:19 and 17:19, worker 2 16:39, worker 3 17:59: 5-6 minutes, no line,
  no commit) and one silent verifier run that merged 3 tasks (16:49) without its board / log write.** Cause NOT KNOWN (no
  transcript). Decision: board rows corrected from the merge commits; the STARTED-line proposal of RUN_LEDGER.md (it
  changes agent instructions) needs your approval; NEEDS FIXING.

## 2026-10-20 16:20 (lead run)

- **T-114 2F roof trim proof and pantry cutting plan: WORKED (MERGED 8c23eea, verifier re-measured the roof on the DXF).**
  Under your Q-58 A the 0.70 x 6.97 m side trim covers the 0.30 x 4.60 m step band: 17 rolls PROVEN on the second-floor
  roof (strict layout 18), but only with strips stopping at the opening edge and 16 flap pieces from the same roof's roll
  ends; pantry 2 rolls, so wet areas 19 -> 21. Engine V2.12 shows 17 / 18 = hand. Went well: every piece dimensioned
  (254 rows), separate re-measure by the verifier. Wrong: nothing; the 0.05 m start offset it recommends has no rule (not
  adopted). Decision: T-120 builds the release version, opt-in until you confirm the reconciliation.
- **T-116 stair openings and stair wells out of a room floor: WORKED, pending verification (READY 15:20; verifier 15:52
  refused execution).** 1F living porcelain released 44.869 m2 -> 38.459 .. 38.979 m2 HELD range (hand 38.588 .. 38.990,
  freelancer 38.96 inside); each deducted piece = hand to 0.01 m2; winder-step defect (0.296 m2) fixed; 24 other floor
  lines unchanged. New small closed element 0.1175 m2 beside the round-stair arrival (designer D-23). Decision: verifier
  checks it first at the next run with execution; the landing finish stays on Q-66.
- **T-109 open-air passage walls in the GF facade run: WORKED, pending verification (READY 15:56).** New piece 105.887 m
  vs released 98.887 m (+7.000 m) = the verifier's hand; the two passage "openings" are not building openings (2 -> 0).
  New finding: the first floor covers 4.08 of the passage's 5.64 m2 (a bathroom and a bedroom corner over outside air):
  soffit and slab over open air not measured anywhere. Decision: T-121 (census of every slab over outside air, NO REPO
  CODE), missing-scope M-07; verifier checks T-109 after T-116.
- **T-107 block type per wall: verifier REJECTED 15:10 (part 1 not done, no branch).** The hand typing (white 141.31 /
  black 136.00 m ASSUMED, black 57.54 m by the note, 125.35 m held) is kept as hand evidence. Decision: already reworked
  as T-117 (claimed 16:01 by worker 3); T-108 now waits on T-117 instead of T-107. No new cause.
- **Worker 2 (two runs): FAILED / no line.** 14:39 run left no RUN_LOG line and no commit; 15:39 run: venv refused
  ("[Untrusted Code Integration]") and the claim commit refused, so T-117 stayed free (worker 3 took it). Verifier 15:49:
  venv, codemap and freeze refused ("[Code from External]"). Recurring cause 4 / 8 unchanged: 3 of 7 runs in this window
  could not run code. Decision: enough NO REPO CODE rows on the board (T-110, T-111, T-119, T-121); the owner setting stays
  under NEEDS FIXING.

## 2026-10-20 14:20 (lead run)

- **T-112 wall heights by both methods: WORKED (READY 9e10d0d, not verified; came in during this run).** 32 rooms. Owner
  method on 4 dry rooms with verified datums 234.17 vs freelancer 258.40 m2 (-9.4 %; same-wall rooms -1.5 %, his flat 3.40
  vs 3.35); annex 102.78 vs 117.00 m2 not releasable (Q-54 B: +4.30 reads as a finished roof); every drawing-derived height
  HELD (no ceiling plane printed). Where the owner line meets a deeper beam (GF open room / pantry 0.10 m into B26 / B27;
  wash lobby, 1F bed room 380 x 430, dewaneya at the beam soffit) it is a method difference reported to the owner, not
  decided. Decision: designer rows D-17..D-22; the owner sees the four beam places in the report (his reconciliation is
  pending); closed wall runs of 7 dry rooms become a task when the board has room.
- **T-100 blinding and columns by hand: WORKED, MERGED 5fe31ca (14:05).** Blinding hand range 20.71-26.37 m3, engine
  22.155 inside it; freelancer 47.055 = one 15.00 x 31.37 x 0.10 plate under the whole plot, drawn nowhere: -24.90 m3
  (-52.9 %) is his basis (ENGINE_RIGHT on basis). Columns at the storey interval 34.446 vs engine 36.711 (-6.2 %: engine
  counts 5 columns the roof-slab plans do not draw, +2.268 m3) vs freelancer 28.547 (his 3.75 / 3.45 heights). What went
  wrong: the handoff says no Urban rule covers column height; URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1 does (interval
  minus the deepest member framing into that column). Decision: T-119 (columns by that rule, column by column; no owner
  question needed); T-101 acceptance adds F10 blinding HELD and the 5 undrawn columns NOT_PRESENT; the other two cases
  (blinding past the plot line 0.189 m3, strap blinding 0.913 m3) and C8 30X80 vs 30 x 90 are designer rows D-14..D-16.
- **T-113 1F living traced: WORKED, MERGED c1f0467 (14:05).** Engine 44.869 vs hand 38.588 m2 (+6.281, +16.3 %) explained
  to 0.0001 m2: stair-opening and stair-well residues 4.635, round-stair quarter landing 1.353, tread-clipping defect
  0.296; freelancer 38.96 = hand 38.990 (-0.1 %). Decision: T-116 (general fix, new piece); the 0.4025 m2 flight foot is
  designer D-13; the landing finish conflicts between owner Q-56 A (porcelain PROVISIONAL) and UP-STAIR-005 (landing
  marble) -> owner Q-66.
- **T-016b, T-014, T-027, T-104: WORKED, MERGED 13:25 (head 60f1d8d).** GF facade passage: verifier read the drawing,
  HAND_RIGHT (98.887 vs 105.887 m, -6.6 %); T-014's "GF established" withdrawn (both readers bridged the passage mouth by
  width alone). Decision: T-109 promoted to TODO; the 0.10 m notch is owner Q-64 (verifier), carried as a range.
- **T-106 skirting audit: WORKED (READY 696b29d, not verified).** All 28 nets right; 20 lines leave 17.035 m unlisted (the
  F-17 window-frame credit); same on the synthetic villas, so general. Engine gross 262.56 vs freelancer 282.85 m (-7.2 %),
  certain net 185.52 m: RULE_DIFFERENCE (he deducts no door; UP-CER-003). Decision: T-118 queued (listing fix after merge).
- **T-107 block type per wall: PARTIAL (READY, board-only).** No architectural sheet names a block type; structural notes
  do (neighbour-side ground beams black, walls with columns at column thickness). 93 runs typed: white ASSUMED 141.31 m,
  black ASSUMED 136.00 m, black PROVISIONAL 57.54 m, HELD 125.35 m; new scope M-05 (substructure black block 2 x 31.17 m).
  What went wrong: part 1 (code vs hand table) not done, freeze check and branch write refused. No-assumption check:
  fallback values marked ASSUMED, parapets / fence held and asked (Q-65): passes. Decision: T-117 (part 1, D-12 thickness
  conflicts, and the evidence files).

(Older entries trimmed by the Lead 18:20; the last 20 are kept.)

## 2026-10-20 20:10 (lead run)

- **T-120 membrane purchase version V2.13: WORKED (MERGED 2264938, verifier 17:49 run).** Opt-in candidate; the checker
  re-placed all 39 pieces of the 2F roof itself (17 rolls under Q-58 A, 0 overlaps), pantry 13.50 m2 / 2 rolls, wet 21.
  Released numbers unchanged by design. Decision: V2.13 is the base of the ONE consolidated candidate V3.0 (T-131, lane I);
  no V2.14.
- **T-121 ceilings over outside air: PARTIAL (REJECTED, gate d).** Census reproduced and the passage roofing confirmed,
  but the pool-court void was the route G face (4.373 m2), not the drawn opening (3.689 m2): PL-03 14.020 -> 14.704 m2,
  total 45.632 -> 46.316 m2; the gross 18.393 was never measured by hand. Cause: a CAD face used as the "hand check" (the
  same source twice). Decision: rework T-127 (lane A) with the hand gross from printed dimensions and the Q-68 C finish
  search.
- **T-122 1F living floor and landing under Q-66 B: WORKED pending the checker (READY f85fe97).** Porcelain 33.594 ..
  33.711 m2 (hand 33.713; corrected its own earlier 33.584 / 34.104), landing marble once 4.875, stair marble 44.365; the
  0.4025 m2 strip is marble in every reading. Every value cites Q-56 / Q-66. Decision: verifier order 1; Q-70 (answered A
  conditional) and the strip / D-23 -> T-129.
- **T-123 GF facade under Q-64 B / Q-67: WORKED pending the checker (READY 54425be).** Q-67 condition met on the drawings
  (nothing across the 1.20 m mouth, far end closed); billable stays 105.887 m until a reveal line holds the 0.100 m (then
  105.787); passage roofed 5.640 m2 (4.080 under 1F + 1.560 GF roof): confirms T-121, contradicts T-109's "open to sky".
  New finding: engine passage spaces leave out 0.480 m2 (two 0.20 strips at B5 / B1), cause not traced -> T-131 lists it
  as a held item. Decision: verifier order 2; then V3.0 carries perimeter / billable apart.
- **T-124 offcut booked once: WORKED pending the checker (READY a582f32).** New opt-in fold V5 books each leftover once;
  every released / proven Alsenan count VALID (wet 21, roofs 6 + 8, 2F 17); synthetic V3 claims corrected 1 -> 2 and
  8 -> 9; one unchosen V4 2F layout (19) held. Decision: verifier order 3; the audit joins V3.0 (no method V2.14).
- **Team: verifier silent twice (18:49, 19:49: 2-3 minute runs, no STARTED line, no commit) and worker 3 18:59 silent.**
  Cause NOT KNOWN (no transcript). Decision: READY order written on the board; the fix is the owner's repo-attached
  migration (P-01); reported under NEEDS FIXING.

Recurring cause 9 (new 20:10): **a CAD face checked against itself.** T-121's "hand" pool void was the engine's own face.
Every hand check must come from printed dimensions or a separate reading (checker rule 1 of the 20:10 decision).
