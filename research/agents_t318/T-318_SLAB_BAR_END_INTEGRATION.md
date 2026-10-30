# T-318: slab bar ends in the candidate (ARCH_TAKEOFF_V3.0.27), integration package for Gate B

Worker 3 (lane I), 2026-10-30 UTC. Development villa, not an accuracy claim. Opt-in candidate only: the released
default stays ARCH_TAKEOFF_V2.9 + route G; nothing is released. No client name, coordinate or image is committed;
drawings are cited by Drive title only.

integrates: T-307 (MERGED c48f7062, Verifier 2026-10-26 05:56 UTC Gate A PASS: every bottom-bar end of the 98
development lines classified by support from ST p.15), T-316 (MERGED ebe99ecf, Verifier 2026-10-28 22:18 UTC Gate A
PASS: top-bar extent by support, F-T316-01 across-beam part, F-T316-02 clear-span cap), T-306 (MERGED 01358449: the
bound decomposition both rest on). Owner: option B approved 2026-10-29 21:22 (only drawn / printed bar parts are
counted; an undrawn part HELD blank unless physically certain from the drawings); 22:05 (read ST p.8 notes and p.15
typical slab details before an end is unresolved; never invent an anchorage, bend or hook). Inputs:
`research/agents_t318/t318_inputs.py` reads LANE_I_CONSUMER_T307.csv, TOP_LINE_LEDGER_T316.csv and
TOP_GROUP_LEDGER_T316.csv, each pinned by sha256; nothing is typed.

## 1. The physical question and the answer (ERS s.2.1, s.3)

The element is ONE END of one suspended-slab bar where it meets the support at the panel edge. The candidate carried
since V3.0.5 one DEVELOPMENT / ANCHORAGE line and one TOP BARS OVER SUPPORTS line per panel and bar direction (98 + 98,
STR.REBAR kg, BOUNDED_EXPOSURE): development as note-9 '40 d .. 70 d per bar end' on EVERY end, top as T-152's reading
i .. max(ii, p.15) + crossing. ST p.8 note 9 is a starter-bar anchorage note (OWNER_RULE_REBAR_2026-10-24 s.4 / s.6);
the governing slab detail is ST p.15 TYP. SLAB ON BEAMS DETAIL (both re-read by T-307 at 600 dpi and by the Checker):

| Support class at the end | p.15 draws (bottom / development) | p.15 draws (top) | Carried in V3.0.27 |
|---|---|---|---|
| CONTINUOUS | no development, no lap (50 % stop short, the rest run on: bottom line) | 0.30 x max(L1, L2) from the face + band | development 0; top valued |
| EDGE_BEAM | straight to 40 mm of the outer face: w - 0.040; curtailed bar turns up (leg undimensioned) | 0.25 L1 + across the beam [w - 0.040, w]; hook-down leg undimensioned; dashed 50 % extension | straight part / top part valued; legs and extension BLANK by name |
| STEP_EDGE, IRREGULAR, OPENING | nothing | nothing | BLANK by name (never 0) |

Rule **R-T318-1** (engine/source/arch_v3027.py, every villa): a slab bar-end line is re-booked from a merged
support-class ledger only; an all-continuous development line is NOT_APPLICABLE_WITH_EVIDENCE; a line with valued and
held ends is split (parent BLANK with every held end class, leg and extension named; the valued ends their own
BOUNDED_EXPOSURE line); a line with no valued end is BLANK; legs / hooks / extensions / held ends carry no figure; a
development part on a note-9 / lap basis is refused; the top part is the envelope of the two printed documents on the
SAME valued ends (plan note 2 vs p.15 stays a designer item: never chosen here); every other line byte-identical.

Top envelope on the valued ends (no reading chosen): low = min(note 2 reading i at count A, p.15 at A), high =
max(note 2 reading ii + crossing at count B, p.15 at B). The note-2 readings on the valued ends are the sums of the
T-316 group ledger's own rows (note2_i_m x n at A; (note2_ii_m + over_band_m at continuous groups) x n at B); the sum
over ALL groups reproduces the line ledger's note2_i_A_kg / note2_ii_cross_B_kg on all 98 lines within 0.0015 kg
(asserted, else the build stops); a line with no held group takes the line ledger figures as stored. The p.15 reading
is T-316's p15_valued (F-T316-01 across-beam [w - 0.040, w] and F-T316-02 clear-span cap R316-10 included).

## 2. BOQ lines (V3.0.26 -> V3.0.27), kg (t at the export boundary only)

| Population (98 lines each) | Before: V3.0.26 bound | After: valued lines | After: BLANK / NA |
|---|---|---|---|
| DEVELOPMENT / ANCHORAGE | 939.794 .. 1,741.976 (note 9 on every end) | **136.573 .. 150.695** on 59 part lines (drawn straight part, count A .. B) | 8 NA (were 78.621 .. 146.623: every end continuous); 59 parents BLANK (were 633.522 .. 1,170.166); 31 BLANK (were 227.651 .. 425.187) |
| TOP BARS OVER SUPPORTS | 781.395 .. 2,002.348 | **612.079 .. 1,618.962** on 86 lines: 79 parts 565.385 .. 1,478.715 + 7 re-based in place 46.694 .. 140.247 | 79 parents BLANK (held ends, legs, extension); 12 BLANK: 8 every end at a step / irregular support, 4 (T&B) tank panels (note 3, F-T316-03) |
| **Both** | **1,721.189 .. 3,744.324** | **748.652 .. 1,769.657** (145 lines) | 138 parents + 43 restated BLANK, 8 NA |

Inside the top valued ends: plan note 2 612.076 .. 1,407.226 kg, p.15 1,404.705 .. 1,546.858 kg (T-316 s.3).
Candidate STR.REBAR kg (code totals): released 10,250.167987 unchanged; bounded range 15,250.786488 .. 21,621.544938 ->
14,278.249488 .. 19,646.877938 (-972.537 / -1,974.667 = exactly the 196 lines' before minus after valued); blocked
lines 579 -> 760; bounded lines 945 -> 894; lines counted 1,936 -> 2,066 (8 NA leave the count, 138 parts join).
**The lower range is partly a move to HELD blank, not a resolved total**: the held legs and undrawn ends have no
figure (never 0). In t: valued 0.748652 .. 1.769657 t.

Identity: 3,775 -> 3,913 lines; 196 replaced (190 CHANGED, 6 CHANGED_TEXT_ONLY = re-based top lines whose envelope
equals the candidate range), 138 added, 3,579 byte-identical (outside_rows_sha256 c7e5495b...). Released V2.9: no
suspended-slab bar-end line (all 196 + 138 NOT_IN_RELEASED). Line-by-line diff: V3_0_27_DIFF.csv; per line before /
after / held / ends: V3_0_27_INTEGRATION_LEDGER.csv.

## 3. Owner manual method and drawing-derived method side by side

| | Owner manual method | Drawing-derived (carried) |
|---|---|---|
| Slab development | none: the owner lap proposal (40 d / 60 d) is not approved and never applies against the drawings; note 9 is a starter-bar note | p.15 by support class: continuous 0, edge beam w - 0.040 straight, legs HELD |
| Slab top extent | none (Q-71 not extended to slabs) | p.15 0.30 max(L1, L2) / 0.25 L1 + across-beam, capped at the clear span, beside plan note 2 (both printed: bound) |

## 4. Against the freelancer (not proof)

Freelancer: one lump 5,400 kg for all slabs, no bar population: RULE_DIFFERENCE, no % (T-152, T-307). The candidate's
slab bar-end lines are bounds and blanks: no total verdict. Verdict proposals stand from the merged ledgers:
development at continuous ends ENGINE_WRONG (no bar drawn), at edge-beam ends ENGINE_WRONG in basis (note 9 vs the
drawn w - 0.040); F-T316-01 ENGINE_WRONG (omission), F-T316-02 ENGINE_WRONG (past the span); note 2 vs p.15, legs,
step / irregular / opening ends UNRESOLVED (designer).

## 5. Evidence status, missing and held

- DRAWING-CONFIRMED (BOUND): the 59 development parts (drawn straight length, count A .. B) and the 86 top lines
  (bound between two printed documents). VERIFIED: none (the count convention and the legs keep every line a bound).
- HELD (BLANK by name): up-turn legs at 1,004 .. 1,044 bottom ends (50 .. 100 %); hook-down legs at 882 .. 919 top
  ends; the dashed 50 % extension (UNRESOLVED); step / irregular / opening ends of both populations; the 4 (T&B) tank
  top lines (note 3). NOT_APPLICABLE_WITH_EVIDENCE: 8 development lines.
- Not in this package: the BOTTOM MESH lines (98, unchanged; 35 flagged F-T307-02 / 03 for the step and wide-support
  continuity, D-41), the T-307 F-03 skew correction of GF-126 y (moot here: its 16 .. 17 held ends now leave the
  line; the valued ends carry note 2 9.456 .. 20.739 / p.15 18.549 .. 18.953 kg, part 9.456 .. 20.739 kg), beam / ground-beam ends (same method, not measured).
- Downgrade-only records (T-245 (f)): none exist for these lines (none written by a worker).

## 6. Downstream consistency (cross-trade, double count)

- Each end once: a part line's ends are only the valued ends of its parent; the parent carries no figure (asserted:
  a part beside a parent with a figure is refused). Development and top are different bars (bottom vs top layer); the
  bottom line keeps the crossing half of continuous bottom bars, so a continuous end booked 0 here is not lost.
- Concrete, formwork and every non-rebar line: byte-identical (totals moved only on STR.REBAR kg, asserted).
- Released-route rebar (route G) and the beam / column / footing rebar lines: untouched.

## 7. Validation

- Own Drive copies this run ('Alsenan chalet project': P7757_DXF_COMPRESSED.zip -> P7757.dxf `ab54dd55`, 'ST7757
  dxf.dxf' `9f9d1179`), decoded into the private folder only; fresh T-167 base run, then the full CLI run
  `research/agents_t318/v3027_run.py` (`tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V3.0.27 --v3027-inputs`):
  **V3_0_25 json 3064078a and V3_0_26 json 8959989c / csv 5e8cff67 reproduced (= the candidate of record, T-279
  Gate B)**; V3_0_27 by `v3027_direct.py` on the same V3.0.26 (hashes in the board handoff).
- tests/t318_slab_bar_end_split: villa V318 by hand (not Alsenan): normal (development split 1.944 .. 2.074 kg, NA,
  held blank, top envelope 12.346 .. 28.148 kg of note 2 12.346 .. 27.325 and p.15 26.019 .. 28.148, re-base in place,
  outside lines byte-identical, order invariance, files / totals) and adverse (NA with a value, held given a value,
  held as 0, leg value, note-9 basis, lap basis, part without held item, re-base with held, low > high, stale before,
  line not in the candidate, wrong direction, twice, unknown status, tonnes, source without checker run, applied
  twice, part beside a parent with a figure, outside line changed); Alsenan pins (counts, kg, closure, envelope,
  edited ledger stops the build); master 1.22.0 (builder, checks clean, dropping the entry is stale).
- L4 full suite and freeze: in the board handoff (run on the final commit).

## 8. For the Checker (Gate B always-checked lines)

Every changed line is structural reinforcement, so by rule every line >= 2 % of the trade or moved >= 5 % is checked.
Suggested re-derivations (acceptance: one continuous-end and one edge-beam line): development 1F-065 y
L-522b811eabc1a0d15f8b NA (CONTINUOUS 16 / 18 ends; was 3.951 .. 7.778); development GF-135 x part
L-b32114a46c2e4b285f1c 3.160 .. 3.259 kg (= the Checker's own T-307 figure 3.160494 / 3.259259; legs at 32..33 ends on
parent L-9a60fdc369047a4754f0); top 2F-047 y part L-0d6d0edfeb33e0cf1672 3.704 .. 17.259 kg (p.15 13.519 .. 17.259 =
the T-316 s.5 hand example; was 3.704 .. 18.062: the past-span 0.803 kg removed); the one re-base that moved: GF-137 x
14.198 .. 34.157 (was 34.158).

## 9. Lessons-register row (proposed)

| 2026-10-30 | the candidate's 196 slab bar-end lines carried note-9 lengths on continuous ends (no bar drawn) and top extents past the span for five versions after two merged ledgers classified every end (T-307, T-316) | the ledgers were research keyed by line id and no integration consumed them; a line mixing drawn and undrawn ends has no single honest bound | re-book bar-end lines end class by end class: all-continuous development NOT_APPLICABLE, valued ends their own bound line, every undrawn end / leg BLANK on the parent; where two printed documents disagree, the line carries their envelope on the same ends, never a choice (every villa; slabs, then beams) | tests/t318_slab_bar_end_split (normal: villa V318 1.944 .. 2.074 / 12.346 .. 28.148 kg; adverse: held as 0, leg value, note-9 / lap basis, stale, part beside a valued parent) | PROPOSED |
