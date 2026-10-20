# T-106: skirting lines whose listed deductions do not add back to the net

Worker 1, 2026-10-20. Branch agents/task-T-106 from working head 79bd397. Metres and widths only; no client data.

## Result in one paragraph

The 17.035 m found by T-016a is reproduced exactly and traced to one mechanism. On the Alsenan reference plan
(Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, sha256 ab54dd55...31cc4), ARCH_TAKEOFF_V2.11 and V2.12
in Mode A (synthetic S2 facts, as T-016a) give 28 measured skirting lines; 20 do not re-add, by 17.035173 m in total,
and in all 20 the missing amount is exactly the F-17 equal-split credit that the room's own bounded range line states
(`v1_equal_split_credit_lm`). The NET is right in every one of the 20 lines (certain skirting = wall + column faces;
the window-frame edges whose skirting depends on the window type are held whole in the range line); only the listing
is wrong. With the Alsenan facts file (owner wet scope: wet rooms full-height porcelain, no skirting) 11 lines carry a
quantity and 9 of them miss 13.569 m the same way. The same defect is on every synthetic villa (SV-A 4 of 4 lines,
4.80 m; SV-B 6 of 7, 10.20 m; SV-C 4 of 4, 5.60 m), there through the V2.8 path (sill-unknown window thresholds moved
whole to the range line), so it is a general defect of the skirting trail, not an Alsenan one.

## Where the difference comes from (engine/source/arch_measure.py, frozen, not changed)

- `skirt = wall + column + window_threshold` (V1 run, coincident roles split equally), deduction list `_sk_ded(runs)`
  = door + passage, glazing edge, "other". So gross - listed = wall + column + window_threshold.
- F-17 (`release_safety.skirting`, ARCH_TAKEOFF_V2.2 on): every edge skirted under one reading only (roles
  WINDOW+WINDOW_THRESHOLD: a window frame drawn on the room face; COLUMN+WINDOW) leaves the certain line: its V1
  share (length x skirted roles / roles = half the edge) is subtracted, and the whole edge goes to the range line
  [0, edge]. The certain line lists the WINDOW half as "glazing edge" but never the credited half.
- V2.8 (`arch_v28.skirting_adjustment`): a sill-unknown window threshold moves whole to the range line and floor
  glazing is dropped; neither is listed either (SV villas).
- The note on the certain line says "sill windows skirted (3.92 m)" for exactly the metres that are not in it.

## Every Alsenan line by hand (Mode A, ARCH_TAKEOFF_V2.12 = V2.11 for skirting)

Gross = room boundary; listed = what the line's deduction list shows; unlisted = gross - listed - net. The door and
passage run is checked against the door blocks drawn in the plan: block extents along the wall D315 0.80 m (11
inserts), D215 / d220 0.90 m (5), D115 / D120 1.00 m (10), D200 2.00 m (1), every insert scaled +-1 (mirror only).
Every door width in the runs is one of these values; the GF open plan's 5.00 m = D120 + D120 + D115 + D200 (1.00 +
1.00 + 1.00 + 2.00, swing arcs 0.89 / 0.89 / 0.89 / 2 x 0.934 m beside its boundary), the driver room's 1.70 m =
D215 0.90 + D315 0.80, the laundry's 1.70 m = 0.90 + 0.80, the GF master bedroom's 1.80 m = D115 1.00 + D315 0.80
(the en-suite door, which no room lists as its own door: the deduction is right, the door list incomplete). Passages
are open doorway faces (e.g. the GF open plan's 10.82 m along the entrance / stair zone lines).

| Floor | Room | Gross m | Listed deductions m | Net m | Unlisted m | Component | Range [0, high] m | Door + passage run m | Audit |
|---|---|---|---|---|---|---|---|---|---|
| GF | Dining + Living + Pantry + Reception | 56.006 | 23.919 | 28.172 | 3.916 | F-17 credit 3.916 | 7.832 | 15.820 | HELD |
| GF | Majlis / diwaniya | 20.128 | 3.955 | 14.218 | 1.955 | F-17 credit 1.955 | 3.910 | 2.000 | HELD |
| GF | Master bedroom | 21.534 | 6.902 | 14.633 | 0.000 | - | - | 1.800 | READDS |
| GF | Kitchen | 14.500 | 1.750 | 12.000 | 0.750 | F-17 credit 0.750 | 1.500 | 1.000 | HELD |
| GF | Driver room | 12.500 | 2.000 | 10.200 | 0.300 | F-17 credit 0.300 | 0.600 | 1.700 | HELD |
| GF | Bathroom / W.C. | 7.625 | 1.100 | 6.225 | 0.300 | F-17 credit 0.300 | 0.600 | 0.800 | HELD |
| GF | Bathroom / W.C. | 7.500 | 0.800 | 6.700 | 0.000 | - | - | 0.800 | READDS |
| GF | Dining + Living + Pantry + Reception (2nd face) | 7.600 | 5.200 | 1.900 | 0.500 | F-17 credit 0.500 | 1.000 | 2.500 | HELD |
| GF | Bathroom / W.C. | 7.414 | 0.800 | 6.614 | 0.000 | - | - | 0.800 | READDS |
| GF | Bathroom / W.C. | 6.810 | 1.100 | 5.410 | 0.300 | F-17 credit 0.300 | 0.600 | 0.800 | HELD |
| GF | Bathroom / W.C. | 6.200 | 1.097 | 4.803 | 0.300 | F-17 credit 0.300 | 0.600 | 0.797 | HELD |
| GF | Bathroom / W.C. | 5.600 | 0.800 | 4.800 | 0.000 | - | - | 0.800 | READDS |
| GF | Unnamed space | 9.499 | 2.856 | 6.643 | 0.000 | - | - | 1.600 | READDS |
| GF | Unnamed space | 7.200 | 1.800 | 5.400 | 0.000 | - | - | 1.800 | READDS |
| GF | Unnamed space | 4.900 | 1.697 | 3.203 | 0.000 | - | - | 1.697 | READDS |
| 1F | Living / saloon | 52.440 | 8.352 | 41.435 | 2.652 | F-17 credit 2.652 | 5.305 | 5.700 | HELD |
| 1F | Master bedroom | 17.700 | 3.025 | 13.450 | 1.225 | F-17 credit 1.225 | 2.450 | 1.800 | HELD |
| 1F | Master bedroom | 22.151 | 3.345 | 17.161 | 1.645 | F-17 credit 1.645 | 3.289 | 1.700 | HELD |
| 1F | Master bedroom | 17.400 | 2.576 | 14.048 | 0.776 | F-17 credit 0.776 | 1.552 | 1.800 | HELD |
| 1F | Master bedroom | 16.200 | 1.900 | 14.300 | 0.000 | - | - | 1.900 | READDS |
| 1F | Laundry | 16.940 | 2.000 | 14.640 | 0.300 | F-17 credit 0.300 | 0.600 | 1.700 | HELD |
| 1F | Bathroom / W.C. | 9.000 | 1.100 | 7.600 | 0.300 | F-17 credit 0.300 | 0.600 | 0.800 | HELD |
| 1F | Bathroom / W.C. | 9.000 | 1.100 | 7.600 | 0.300 | F-17 credit 0.300 | 0.600 | 0.800 | HELD |
| 1F | Bathroom / W.C. | 8.700 | 1.284 | 7.400 | 0.016 | F-17 credit 0.016 (COLUMN+WINDOW 0.033) | 0.033 | 0.800 | HELD |
| 1F | Bathroom / W.C. | 7.600 | 1.100 | 6.200 | 0.300 | F-17 credit 0.300 | 0.600 | 0.800 | HELD |
| 1F | Bathroom / W.C. | 6.540 | 1.100 | 5.140 | 0.300 | F-17 credit 0.300 | 0.600 | 0.800 | HELD |
| 2F | Maid room | 18.900 | 2.300 | 16.000 | 0.600 | F-17 credit 0.600 | 1.200 | 1.700 | HELD |
| 2F | Bathroom / W.C. | 9.700 | 1.100 | 8.300 | 0.300 | F-17 credit 0.300 | 0.600 | 0.800 | HELD |
| | **28 lines** | | | **304.194** | **17.035** | **20 of 20 matched** | **34.070** | | **20 HELD, 8 READDS** |

Worked example, Laundry: boundary 16.94 = wall 13.29 + column 1.35 + door 1.70 + glazing half 0.30 + threshold half
0.30 (the 0.60 m window OP-013 sits on the room face). Listed 1.70 + 0.30 = 2.00 -> 14.94, but net 14.64 = wall +
column. The second 0.30 is the F-17 credit; the range line holds the whole 0.60. Correct listing: 1.70 doors + 0.60
"edge held in the range line" = 2.30 -> 16.94 - 2.30 = 14.64.

Verdict per line: the 20 nets are ENGINE_RIGHT under F-17 (the certain line keeps only what both readings agree on;
whether the 34.07 m of window edges are skirted depends on the window sill, which the plan does not print: the range
lines' RFI). The listing is a defect (UP-QTY-STATUS-001: a line must be checkable from its own trail).

Not an Alsenan quantity in Mode A: kitchen, laundry and the W.C.s are skirted only because the synthetic S2 facts
set the wall tile to 2.40 m < 3.00 m clear (UP-CER-004). With the Alsenan facts file they are NOT_APPLICABLE (owner
wet scope, full-height porcelain), which matches the freelancer, who has no skirting in any wet room.

## Engine vs freelancer (Alsenan facts file; the released owner-scope reading)

The freelancer's skirting row (floors workbook, "ceramic" sheet) is 282.85 lm = the sum of 12 dry-room gross
perimeters, no door deduction (his labour line is 315 lm). The engine deducts doors and passages (UP-CER-003, owner
rule) and holds window-frame edges, so only gross is like for like.

| Room group | Freelancer gross m | Engine gross m | Engine certain net m | Engine net + range high m | Gross diff |
|---|---|---|---|---|---|
| GF open plan: reception + dining (+ entrance hall) | 72.92 | 63.606 | 30.072 | 38.903 | -12.8 % |
| GF master bedroom | 21.71 | 21.534 | 14.633 | 14.633 | -0.8 % |
| GF majlis / diwaniya | 20.00 | 20.128 | 14.218 | 18.128 | +0.6 % |
| GF driver room | 12.50 | 12.500 | 10.200 | 10.800 | 0.0 % |
| 1F living | 43.78 | 52.440 | 41.435 | 46.740 | +19.8 % |
| 1F four bedrooms | 79.04 | 73.451 | 58.959 | 66.251 | -7.1 % |
| 2F maid room | 19.30 | 18.900 | 16.000 | 17.200 | -2.1 % |
| 2F corridor (engine: stair hall, BLOCKED_RFI) | 13.60 | held | held | held | held |
| total | 282.85 | 262.559 | 185.517 | 212.654 | -7.2 % |

- Gross matches within 2.1 % on the four single rooms that map one to one (GF master, majlis, driver, 2F maid).
- RULE_DIFFERENCE: the freelancer deducts no door, passage or glazing; the engine net is 185.52 m certain, 212.65 m
  if every held window edge is skirted, against his 282.85 m. The gap is the owner's door rule plus open sides.
- UNRESOLVED: GF open plan -12.8 % (the engine's 10.82 m of passage / zone lines along the entrance and stair are
  not skirted; the freelancer runs a full perimeter round reception, dining and a separate entrance hall); 1F living
  +19.8 % (the same extra area T-113 traces, 44.87 vs 38.92 m2); the 2F corridor is a stair hall the engine blocks
  (Q-S6-4). The 1F bedrooms map only as a group (two of four perimeters differ by more than 1 m either way).

## The check piece (engine/source/skirting_deduction_audit.py, SKIRTING_DEDUCTION_AUDIT_V1, not wired)

For any villa: every FIN.SKIRTING line with a quantity gets one record, READDS or HELD (SKIRTING_UNEXPLAINED with the
signed unlisted length, SKIRTING_NOT_READDABLE when a length is missing, SKIRTING_UNIT_UNKNOWN, plus
SKIRTING_DECOMPOSITION_MISMATCH when the role split does not add up to the boundary). The candidate names each
component (F-17 credit from the range line, V2.8 thresholds moved to it, V2.8 floor glazing from the room record);
a match explains the cause but the record stays HELD. Alsenan Mode A: 28 lines, 8 READDS, 20 HELD, 17.035173 m, all
20 matched; owner facts: 11 / 2 / 9, 13.568824 m, all matched; SV-A / SV-B / SV-C: 4.80 / 10.20 / 5.60 m, all matched.

## Fix proposal for the Lead (not built here)

A new skirting output version (new method version; arch_measure.py and the released methods stay frozen): the
certain skirting line lists every length it takes off, one deduction per component, with the range line id:
"edges skirted under one reading only, equal-split share (F-17); the whole edge is held in range line L-...",
"window threshold, sill not established (V2.8), held in range line L-...", "floor-level glazing threshold (V2.8)";
and the note "sill windows skirted (x m)" states only the metres that are in the line. Acceptance:
SKIRTING_DEDUCTION_AUDIT_V1 gives 0 HELD on Alsenan (Mode A 28 lines, owner facts 11 lines) and SV-A / SV-B / SV-C,
with every quantity byte-identical to V2.12.

## What is missing

- The window sills that would release the 34.07 m (Mode A) of held edges are not printed on the plan (T-083 / T-092
  read heights from the scanned elevations); the range lines stay held.
- The freelancer entrance hall and 2F corridor have no engine skirting line (merged into the open plan / stair hall).
