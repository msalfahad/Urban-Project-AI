# T-428 Concrete reconciliation roll-up r4 (research only)

The merged T-406 r3 roll-up (T-385 r2 on ARCH_TAKEOFF_V3.0.29 + the V3.0.33 column moves; merge 35c9212e) restated
PART BY PART with the Checker-merged traces of T-415 (ST-02 curved flight), T-417 (ST-01 flight length and landing
area), T-416 (ground-beam length) and T-426 (ground-beam section class). No quantity, line, state or released cell is
changed. Every figure is read from a merged summary and asserted against the Checker's own figure in its board verdict
(`CHECKER` in `t428_alsenan.py`) before it is used; the class of every traced or held sub-part names that verdict.
Engine-side figures and residual splits in m3 only; no freelancer row text.

## Candidate of record

The table holds on **V3.0.37** (= V3.0.34 for valued concrete), asserted from the merged Gate B summaries:
V3.0.35 (T-400) changed one concrete line, the upper boundary G.B `L-fb7a6431` blank -> blank with a range 0 .. 3.5256
(already HELD in GB-BOUNDARY), and added one BLANK `STR.CONC.BOUNDARY_PAD` (pad count not printed, 0.312 m3 per pad
beside: new HELD scope on the engine side, no residual move; whether the other side bills pads is not readable from
public data); V3.0.36 (T-246) moved 0 quantities; V3.0.37 (T-420) added 80 floor-bed lines, no concrete code.

## Headline (m3, engine - freelancer; residual = traced + HELD + unexplained)

| | Traced | HELD | Unexplained | Residual |
|---|---|---|---|---|
| r3 current (V3.0.33 = V3.0.37) | +4.128223 | -115.460212 | -11.568269 | -122.900258 |
| **r4 current (V3.0.37)** | **-1.387154** | **-116.428339** | **-5.084765** | **-122.900258** |

Bookkeeping closes in 10 / 10 families, cause in 4 / 10 (blinding, footings, slabs, parapet RC). Unexplained by sign
(never closed by its sign): **-5.242949 negative, +0.158184 positive**, 16 parts. Traced fell because large NEGATIVE
engine-right terms (ST-01 rise -2.027, GB bounded -3.525) left the unexplained column; HELD grew by the ST-02 RS-C binding
(-1.244067) less the held-line length fields T-416 names (+0.275940).

| Family | r3 current: traced / HELD / unexplained | r4 current |
|---|---|---|
| CONC.GROUND (slab + ground beams) | -4.844 / -13.251 / -4.569 | **-8.253 / -12.975 / -1.436** |
| CONC.STAIR_DOME | +0.233 / -5.788 / -5.828 | **-1.874 / -7.032 / -2.476** |
| all other families | unchanged | unchanged |

## SD-STAIR -9.683920 (before: traced -0.328 / HELD -3.528 / unexplained -5.828)

| Part | m3 | Class | Verdict |
|---|---|---|---|
| ST-02 RS-LD flat landing T 16 vs his 'slab + steps' 0.28 | -0.162300 | ENGINE_RIGHT | T-415 (h) |
| ST-02 RS-S / RS-A drawn 0.26187 m3/m2 vs his 0.28 | -0.065268 / -0.026107 | ENGINE_RIGHT | T-415 (h) |
| ST-02 RS-C at his 0.28 on the drawn 4.443096 m2 (waist t not printed, RFI-S27) | -1.244067 | HELD | T-415 (h) |
| ST-02 his 8.844 m2 beyond the drawn 10.836 m2 (16.4 m untraced) | -2.476433 | UNRESOLVED | T-415; owner **T-432** |
| ST-01 RISE_IN_LENGTH: his 5.300 = run 3.300 + rise laid as plan length | -2.026752 | ENGINE_RIGHT | T-417 (h) |
| ST-01 ONE_LENGTH (MS2 own profile 5.316 vs his 5.300) | +0.010752 | ENGINE_RIGHT | T-417 (h) |
| ST-01 landings: his depth 1.400 includes the B3 band owned by the beam | -0.076800 | ENGINE_RIGHT | T-417 (h) |
| ST-01 MS2-LD-W drawn plate with no unit of his | +0.239200 | ENGINE_RIGHT | T-417 (h) |
| unchanged r3 parts (thickness basis / ownership / D1 / held MS1-L, turns, ST-03 E1) | -0.328145 traced, -3.528 HELD | | T-398 |

r4: **traced -2.435420 / HELD -4.772067 / unexplained -2.476433** (ST-02 only). The row text's "SD-STAIR unexplained
-3.974175 (ST-02 only)" is the figure after T-417 alone; with T-415 applied it is -2.476433.

## GB-MAIN -10.354614 (before: traced +2.343720 / HELD -9.690354 / unexplained -3.007980)

| Part | m3 | Class | Verdict |
|---|---|---|---|
| held runs at his section (53.8353 m, D-34, D-35 annex, court) | -9.690354 | HELD | T-391 |
| section: exterior main printed D 0.95 vs his 0.60 (56.5168 m) | +5.796522 | ENGINE_RIGHT | T-391 + T-426 (p.13 own read) |
| section: interior printed 30 x 40 vs his 0.60 (57.3969 m) | -3.443815 | ENGINE_RIGHT | T-391 + T-426 |
| section: annex-arc sliver L-be6708e0 valued at 0.30, no printed section | -0.009000 | **UNRESOLVED** (re-class from ENGINE_RIGHT) | T-426 NO_PRINTED_SECTION, Checker 'blank named'; owner T-430 |
| section: interior 0.60 runs where both sides agree (26.44 m) | 0.000000 | AGREE (both wrong on 2 runs: register E-1 / E-2 / E-4) | T-426 |
| plan / end adjustments | +0.000013 | AGREE | T-391 |
| his lumps through necks / crossings, 19.584 m inside the drawn allowance 34.526 m | -3.525102 | TRACED **BOUNDED_THROUGH_SUPPORTS** | T-416 (h) |
| L-fe78ae28 / L-0e30aadb through the founded necks 7F5 / 7ED (2 x 0.300 m exact) | +0.108000 | TRACED **ENGINE_WRONG** | T-416 (h); correction **T-430** |
| HELD annex lines F8+7D4 / 137+138 / 136+7D5: length fields through their necks (1.533 m) | +0.275940 | HELD | T-416 (f) |
| valued FD+7E0 / 107+7CE / ring: length field beyond the net, value net or in range (0.760 m) | +0.136764 | UNRESOLVED | no Checker class; T-430 |
| sliver L-be6708e0 0.10 m beside neck 211 | +0.018000 | UNRESOLVED | T-416; T-430 |
| 13D+7D2 junction in the other band, 17E+17F oblique end | -0.025002 | UNRESOLVED | T-416; T-430 |
| support cuts 1 mm long (extractor buffer, F-C-T416-1) and rounding | +0.003420 | UNRESOLVED | T-416 Checker; T-430 (exact cuts) |

r4: **traced -1.064382 (of which ENGINE_WRONG +0.108000, BOUNDED -3.525102) / HELD -9.414414 / unexplained +0.124182
(+0.158184 / -0.034002)**. The -3.007980 'length basis' is no longer one lump: it is the bounded through-support
term -3.525102 plus +0.517122 engine beyond the drawn net, named band by band.

**Engine-side register (not residual parts; the comparison cannot show them; each owned by T-430):**
E-1 VERIFIED_WRONG +0.423 m3: unloaded 3.525 m halves of L-fe78ae28 / L-0e30aadb at 0.60 where p.13 prints 30 x 40
(the other side is at 0.60 too: 0.000 AGREE). E-2 HELD 0.846 .. 1.269 m3: their loaded halves (D-33). E-3 HELD
0.864171 .. 1.152231 m3: 4 short runs at the 0.40 end of the unanswered D-34 pair (F-T426-1; their comparison term sits
in the -3.443815 part and would grow by up to -0.288057). E-4 HELD 0.5964 .. 0.9036 m3: 177+7CD#1 (5.020 / 4.970 span).

**GB-MAIN both ways (R-T428-6; T-430 QUEUED, so a scenario, never the current figure):**

| Basis | Traced | HELD | Unexplained | GB-MAIN residual |
|---|---|---|---|---|
| as is (V3.0.37) | -1.064382 | -9.414414 | +0.124182 | **-10.354614** |
| after T-430, T-426 s.6 (1) scope (necks out -0.108, unloaded halves -0.423 ENGINE_RIGHT, loaded halves 1.269 into HELD) | -1.595382 | -10.683414 | +0.124182 | **-12.154614** |
| after the whole T-430 row (+ 177+7CD#1 0.9036, sliver 0.009, 4 D-34 lines 1.152231 withdrawn into HELD) | -1.595382 | -12.748245 | +0.124182 | **-14.219445** |

FINDING F-T428-1 (for the Lead): the row's "-10.959354" is T-426's HELD TERM after T-430 on the T-391 basis
(-9.690354 - 1.269), not the GB-MAIN headline; the headline after T-430 is -12.154614 (s.6 (1) scope) or -14.219445
(whole row). On the r4 basis that held term is -10.683414 (the 0.275940 m3 of held-line length fields T-416 names). The
whole-row scenario does not re-bind the classes of the terms already on the withdrawn lines (his per-run section is not
separable from his two lumps), the same convention as the r3 column moves.

**Observation O-T428-1 (proposal for the Checker; the table does not move by it).** Of GB-LEN-FIELD +0.136764,
**+0.086989** is one half of a bookkeeping pair: T-391's section term is the valued m3 less his 0.18 on the LENGTH
FIELDS (asserted: exterior valued 15.969555 - 0.18 x 56.5168 = 5.796531 = section + plan), its length term 0.18 x (all
length fields - his length); on FD+7E0 (field 6.900, value length 6.600), 107+7CE (0.390 / 0.363902) and the ring
L-7076482d (6.2868 / 6.129625) those 0.483273 m appear +0.086989 in the length term and -0.086989 inside the exterior
section term: no physical difference (AGREE, net 0). The other **+0.049775** is the value length beyond the GB-plan net
(FD+7E0 0.002, 107+7CE 0.000502, ring 0.274025 m inside its frame range 5.8556 .. 6.259: a range, never a chosen
frame). If ruled: GB-MAIN unexplained +0.124182 -> +0.037193, traced -1.064382 -> -0.977393 (exterior section
+5.796522 -> +5.883511).

## What remains unexplained (-5.084765 m3) and who owns it

| Part | m3 | Owner |
|---|---|---|
| ST-02 his area beyond the drawn plan (16.4 m) | -2.476433 | T-432 (TODO) |
| GS stair-zone panel (does a slab run under the curved flight foot?) | -0.837230 | none on the board: designer item F2, RFI draft |
| GS his area beyond the drawn network | -0.638640 | none: a bare number with no drawn element |
| PL-WALLS 0.20 m of his height above rim + base | -0.471346 | none |
| beams length beyond the drawn support allowance GF / 1F / 2F | -0.126242 / -0.153516 / -0.087240 | none |
| boundary: lower band 1.21 m / upper G.B 0.28 m | -0.145200 / -0.050400 | none |
| C9 section schedule vs drawn | -0.138000 | designer item |
| GS valued faces (three small reads) | -0.084700 | none |
| GB-MAIN small parts (sliver section -0.009, sliver length +0.018, field +0.136764, junction / oblique -0.025002, buffer +0.003420) | +0.124182 | T-430 |

Every part is bound once (part ids unique; the list re-adds to the table's unexplained to 5e-6, asserted). 9 parts
(-2.594514 m3) have no owner task: they are named for the Lead, not closed.

## Method (t428_rules.py, R-T428-1 .. 7; every villa)

A sub-trace restates exactly one merged part into sub-parts that re-add to it within 0.000002 m3; it never moves
residual between parts, components or families. TRACED or HELD needs the Checker verdict that gives the class (else
UNRESOLVED / UNTRACED only). ENGINE_WRONG (owner of the correction named) and BOUNDED_THROUGH_SUPPORTS (allowance and use
in m, use <= allowance) are TRACED with their own sub-totals. Engine-side items never enter the residual and never
share an id with a residual part. A queued correction is a scenario printed beside the as-is figure, never alone; a
merged one is a candidate move (R-T406-6).

Tests `tests/t428_rollup_r4` (35): Villa R428 hand fixture (not Alsenan) normal, order invariance, scenario beside
as-is, engine-side register leaves the table unchanged; adverse: unmerged source, part not found / found twice /
sub-traced twice, sub-parts not re-adding, TRACED / HELD without a Checker verdict, ENGINE_WRONG without an owner,
bounded beyond its allowance or without one, HELD 0, ratio cause, verdict counted as another class, unknown verdict,
residual counted in two parts, engine-side item moving the residual / 0 .. 0 range / no line ids / no owner, scenario
from a merged task, scenario removal not cancelling; Alsenan pins (summary reproduces, headline, stairs, GB-MAIN as is
and after T-430, verdict names, register, merged shas are ancestors).

## Not done / uncertain

- The V3.0.37 run was not reproduced here; the chain V3.0.34 -> V3.0.37 is read from the merged Gate B summaries.
- The F-C-T416-1 buffer shifts the split between the engine-beyond-net and the bounded term by order 0.01 m3 (sum
  exact); only the two neck cuts are carried exact (0.108000); lane I carries exact cuts (T-430).
- F-T426-1 (extend DG-a31a0d7e to the 4 D-34 lines) is a downgrade-only record for the Checker; this research task
  does not write a record (E-3 lists it).

## Proposed lessons-register row (ERS section 7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | A roll-up showed GB-MAIN interior 0.60 runs as 0.000 AGREE while the drawing prints 0.40 on two of them (both sides wrong, +0.423 m3 VERIFIED), and the 'after T-430' figure on the row was a held term, not a residual (T-428) | a residual table can only show engine-vs-other differences; an error both sides share, and a figure quoted without its column, pass unseen | a roll-up keeps an ENGINE-SIDE REGISTER of Checker-found engine errors and range-end values beside the residual (never a residual part, never moving a total) and prints a queued correction as a scenario beside the as-is figure with every column, never one figure alone; a later verdict that removes a part's printed basis re-classes it to UNRESOLVED (every villa, every reconciliation; provenance T-428) | tests/t428_rollup_r4 (register moving the residual refused; register id also a residual part refused; scenario from a merged task refused; TRACED without a Checker verdict refused) | PROPOSED |
