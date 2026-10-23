# Older Lead feedback entries (moved from FEEDBACK.md to keep the last 20; newest first)

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
