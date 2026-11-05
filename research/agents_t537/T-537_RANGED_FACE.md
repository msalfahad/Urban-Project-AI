# T-537 R-T498-2 1.0.0: block materials on a BOUNDED / RANGED lintel host face (every villa)

Worker 3, lane I, non-candidate, backlog-permitted; 2026-11-05 (claim 19:02 UTC, run session_01E6cPnbx2DpRhVUNKRqatjh),
engine base c4a34358. Files: `r_t498_2.py` (rule), `t537_apply.py` (application to the 2 staged hosts, committed
inputs only), `tests/t537_ranged_face/` (27 tests). R-T498-1 (T-498 stage, `engine/source/arch_v3059.py`), every
candidate, released, frozen, rule-version and registry file: untouched. No drawing, client name or coordinate here.
Gap closed: RG-1 / F-T530-2 (T-530 WIRING MANIFEST, merged f05abdd6).

## 1. Physical element (ERS s.2.1)

The block face left in a host wall after the RC lintel band over each opening is taken out of it, and the AAC glue
(white) or the units and 1:4 laying mortar (black) on that face. The lintel is concrete (B9-02, one piece cast to
length, R-T519-1); its face is D x L where L is the BUILT length. The MAS.BLOCK contract area never moves (R-T453-5,
Q-73, register 'RC LINTEL over an opening vs the host masonry wall'). Installed quantities only; waste HELD (owner:
waste separate); bags only once per purchasing group (R-T523-1).

| | owner manual method | drawing-derived method |
|---|---|---|
| face | (no company rule for the lintel face) | D x [L_lo, L_hi] of the lintel's own line: T-516 [w + 0.80, w + a_s + a_e] (BEARING_OK), T-524 length at a deficit end |
| glue | net m2 x 3.5 / 4.5 kg (owner 2026-11-02) | [net - sum face_hi, net - sum face_lo] x the same rate |
| black units / mortar | 12.5 / m2 (Q-75); 1:4 (Q-78) | the same base interval x 12.5 / the T-367 joint m3 per m2 |

## 2. Rule R-T498-2 1.0.0 (scope: any host masonry line losing lintel faces; provenance R-T453-5, R-T516-1, R-T519-1, R-T524-1, R-T523-1, UP-QTY-STATUS-001; no new factor)

1. FACE = D x [L_lo, L_hi] of the lintel line (VALUED lo = hi; BOUNDED_MIN_BEARING; HELD_BY_NAME with a T-524 bound).
   L_hi unknown -> face OPEN. A legacy held face 0 .. max is kept only where the max is a PROVEN ceiling; a 'max' of
   D x (w + 2 x printed minimum bearing) is OPEN (F-T537-1, section 4).
2. BASE = [net - sum face_hi - sum proven legacy max, net - sum face_lo]: the material's LOW end takes every face's
   HIGH end (longest lintel) and vice versa. No midpoint; never the larger or smaller alone. lo = hi -> one value.
3. OPEN face -> material HELD blank by name, never 0; AT_MOST (net - sum face_lo) x rate beside only.
4. Every material of the host (units, mortar, glue) = base interval x its owner rate; a range gives a BOUNDED_EXPOSURE
   line with both ends.
5. PURCHASE: a ranged key enters R-T523-1 with both ends; ONE ceiling of EACH end of the group sum. Equal ceilings ->
   DETERMINATE (every value in the range needs that many packs: arithmetic, not a pick); unequal -> to-buy stays a
   range by name, the high ceiling is never booked as 'the' figure; HELD member or HELD loss -> HELD, AT_LEAST.
6. REFUSED: inverted interval, negative / millimetre D or L, faces above the host net, the same lintel twice; a
   partial-depth lintel (B != host t) and a pair split over two hosts make their faces OPEN (designer items).

## 3. Hand fixture K537 (not the training villa) and adverse cases

Wall 4.00 x 3.00 m, door 1.20 x 2.10 -> net 9.48 m2; lintel 0.20 x 0.20, bearing 0.15 .. 0.40 each end -> L [1.50,
2.00], face [0.30, 0.40] m2 -> base [9.08, 9.18] m2. White 0.20: glue [40.86, 41.31] kg = [1.6344, 1.6524] bags ->
to buy [2, 2] DETERMINATE; white 0.15: [31.78, 32.13] kg; black 0.20: [113.5, 114.75] pcs, mortar x 0.01475 =
[0.13393, 0.135405] m3. Wall 4.70 x 3.00 with a 1.20 x 2.20 window: glue [49.77, 50.22] kg -> to buy [2, 3] (range
by name). Both walls one group: [3.6252, 3.6612] bags -> one ceiling [4, 4] (per-wall ceilings 4 .. 5 never bought).
Adverse (tests): unbounded face -> HELD, value None, AT_MOST 41.31 beside; inverted -> refused; mm / negative ->
refused; faces above net -> refused; min-bearing 'max' -> HELD; no basis -> refused; partial depth -> OPEN; pair on
two hosts -> both OPEN, on one host -> once; twice / pre-rounded -> refused; no midpoint on a range.

## 4. The 2 staged glue hosts (development villa; T-498 stage lines, not merged, nothing released)

| host (stage line) | before (R-T498-1) | after R-T498-2 | change, cause |
|---|---|---|---|
| L-a3f88ecd GF 0.20 OA white (L-d14c6c9b), net 5.59 | 5.23 m2 -> 23.535 kg (0.9414 bags) | D-GF-06 face 0.20 x [1.40, 1.54] = [0.28, 0.308]: base [5.282, 5.31] m2 -> **[23.769, 23.895] kg**, [0.95076, 0.9558] bags | +0.234 .. +0.360 kg (+0.99 .. +1.53 %): T-453 deducted 0.36 (w + 0.80 = 1.80 m), the deficit lintel stops at its host (T-524) |
| L-2fdc0f97 1F 0.20 VERIFIED white (L-4b9a29d4), net 101.976 | RANGE 98.771 .. 100.271 m2 -> 444.4695 .. 451.2195 kg | W14 [0.975, 1.23], W15 [0.47, 0.5674], W18 0.17346 (= 0.20 x 0.8673); W16 / W19 / W20 / W24 OPEN -> **HELD blank**, AT_MOST 451.60893 kg (100.35754 m2) beside | the low end loses its basis: F-T537-1 |

F-T537-1 (ENGINE_WRONG proposal on the staged low end, every villa): the four held faces W16 / W19 / W20 / W24
(head not established) carry 'max' 0.47 / 0.28 / 0.28 / 0.47 m2 = D x (w + 0.80), the T-453 length; R-T516-1 (Gate A
PASS 06:05) shows that length is the LOWER bound of a built lintel (piers 0.618 / 1.032 m measured on W14), so if
those lintels exist their faces lie in [D (w + 0.80), D (w + a_s + a_e)], piers not measured. The staged and the T-530
low end (444.4695 / 443.27313 kg) is therefore no proven lower bound. CONDITIONAL beside (if those maxima were
ceilings): [98.50514, 100.35754] m2 -> [443.27313, 451.60893] kg = T-530's after, reproduced to 6 decimals (independent
check: faces recomputed from the lintel lines, not read from T-530). Closure: a T-516-method pier census of those 4
openings (measurable, no owner question). Also beside: W15 / W16 share a 0.493 m pier (T-516 note): if W16 gets a
lintel, W15's high end is a pair case (rule (6)).

AAC glue group (R-T523-1 through T-523's own function and bindings): before 35.42625 .. 36.19665 bags AT_LEAST (to buy
>= 36 .. 37); conditional = T-530 35.387755 .. 36.226627 (>= 36 .. 37); R-T498-2 **17.65683 .. 18.16227 AT_LEAST
(>= 18 .. 19), HELD**: the known part shrinks because host 1 becomes open, not because less glue is needed.

## 5. Verdicts, lessons

Engine vs freelancer: no freelancer glue / lintel row (UNRESOLVED, unchanged). Lessons row (proposed, ERS s.7):
| 2026-11-05 | a held lintel face carried 0 .. D (w + 0.80) as its maximum after T-516 proved w + 0.80 is the minimum built
length | a bound's direction was not re-checked when the measure behind it changed meaning | every bound records its
basis (UPPER_PROVEN / MIN_BEARING_LENGTH); a minimum-length 'max' opens the face; ranged faces enter the material
base low-with-high (every villa) | tests/t537_ranged_face | proposed |
