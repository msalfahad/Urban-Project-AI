# T-544: B9-02 1F lintel END CEILINGS of W16 / W19 / W20 / W24, so the 1F AAC glue host L-2fdc0f97 is bounded

Worker 1, lane S, non-candidate, claim 2026-11-06 03:22 UTC (run session_01E6cPncUBvQ3SK3ebfeL38S), engine base 3f3b580c.
Files: `t544_extract.py` (drawing reader: the merged LINTEL_BEARING_V3 run with the 4 openings as cases, plus an extended
search for an end the 3.0 m search left open), `held_lintel_ceiling.py` (rule R-T544-1), `t544_apply.py` (application to
the host, committed inputs only), `out/` (numbers only: lengths from a jamb or along a wall, ids, no coordinate),
`tests/t544_held_lintel_ceiling/` (30 tests). Every merged module (T-516, T-519, T-527, T-537, T-523) imported read-only
and unchanged; no engine, rule, knowledge, registry, master or candidate file changed; V2.9 + route G and V3.0.58
untouched. Drawing cited by Drive folder and title only: 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf
(sha ab54dd55).

## 1. Physical element and engineering question (ERS s.2.1)

Each lintel END of the four 1F windows W16 (sea side, band WB-FL0041-FL0042) and W19 / W20 / W24 (neighbour side, band
WB-FL0002-FL0003), all in the 1F white AAC 0.20 host. Their lintel is HELD because the head is not established (no
printed sill / height: designer item D-45, T-175): whether masonry is built over the opening, so whether a lintel exists,
is not known. That stays HELD. What the drawing does fix is how long a lintel COULD be: an RC piece over the gap cannot
run past the first column face, the next opening or the end of the masonry on its own wall line (R-T516-1 / R-T527-1).
So the face it can take out of the host is in {0} U [D x L_min, D x L_ceil]; the material base needs 0 .. D x L_ceil.

| | owner manual method | drawing-derived method |
|---|---|---|
| bearing | owner precast 0.15 m min; project detail MIN 0.40 m (both MINIMA) | measured masonry a beside each jamb, full thickness, V3 stopper order |
| held face max | T-453: D x (w + 0.80) (a LOWER bound of a built lintel, F-T537-1) | D x (w_gap + c_START + c_END), c = a rounded UP to the mm |
| shared pier | (none) | one pier counted once on one host (joint record) |

## 2. The 8 ends (`out/JAMB_EVIDENCE_T544.csv`, `out/EXTENDED_SEARCH_T544.csv`)

| lintel | gap m | START a -> stopper -> ceiling | END a -> stopper -> ceiling | L_ceil m | face m2 | concrete if built m3 |
|---|---|---|---|---|---|---|
| W16 | 1.5523 | 0.4933 OPENING W15 (shared pier) -> 0.494 | 1.2322 COLUMN -> 1.233 | 3.280 | 0 .. 0.6560 | 0 .. 0.1312 |
| W19 | 0.6000 | 0.7250 COLUMN -> 0.725 | 0.8750 OPENING W20 (shared pier) -> 0.875 | 2.200 | 0 .. 0.4400 | 0 .. 0.0880 |
| W20 | 0.6000 | 0.8750 OPENING W19 -> 0.875 | 1.011731 COLUMN -> 1.012 | 2.487 | 0 .. 0.4974 | 0 .. 0.09948 |
| W24 | 1.5524 | 0.937069 COLUMN -> 0.938 | 3.000 SEARCH_LIMIT (V3) -> extended 4.2188 COLUMN -> 4.219 | 6.710 | 0 .. 1.3420 | 0 .. 0.2684 |

V1 (T-516) and V2 (T-519) give the same values and stoppers on all 8 ends (V1 W19 START 0.725 vs V2/V3 0.724 floored;
6 dp 0.725000). No curved bay on WB-FL0002-FL0003; on WB-FL0041-FL0042 the bay lies beyond W18, not at a W16 end.
Independent check (second method, scratch only): the column outlines projected onto each band axis without the masonry
union: columns at 0.000 / 3.8117 / 4.5117 / 11.22 m on WB-FL0002-FL0003 and 0.000 / 5.625 m on WB-FL0041-FL0042 give
W19 START 0.725, W20 END 1.0117, W24 START 0.9371, W24 END 4.2188, W16 END 1.2322, pier W19/W20 0.875, pier W15/W16 0.4933:
AGREE to 0.1 mm. A scratch plot of WB-FL0002-FL0003 shows no other gap on 7.00 .. 11.22 m (W24 END run).
Status per end if a lintel exists: W19 / W20 / W24 ends >= 0.40 and the W19/W20 pier 0.875 >= 2 x 0.40: BEARING_OK
(L_min = w + 0.80); W16: the 0.4933 pier shared with REQUIRED W15 cannot carry two 0.40 minimums: pair deficit, a designer
item if W16 gets a lintel (T-516 conditional flag, now measured on both sides).

## 3. Rule R-T544-1 1.0.0 (`held_lintel_ceiling.py`; scope: any HELD lintel face on any host; provenance R-T516-1,
R-T527-1, R-T498-2 (1)-(3), (6), F-T537-1, F-T537-2; no new factor)

1. End ceiling = measured a ROUNDED UP to the mm (upper bound direction, F-T537-2). A SEARCH_LIMIT end is re-searched on
   the same line to 20 m; still none -> no ceiling. A printed-minimum bearing figure is refused as a ceiling.
2. L_ceil = drawn gap + both ceilings, rounded up. Any end without a ceiling -> face OPEN (material HELD, never 0).
3. HELD face = [0, D x L_ceil] (0: existence not established). B != host t -> OPEN.
4. Two lintels sharing one pier on ONE host = one joint record, lo = sum of member lows, hi = max D x (outer + gap + pier
   + gap + outer), pier once; on two hosts -> both OPEN. Cross-check: joint span vs column face to column face.
5. Records enter R-T498-2 material_base unchanged.

## 4. Host L-2fdc0f97 (1F 0.20 white AAC, contract net 101.976 m2, 4.5 kg/m2)

| face record | lo m2 | hi m2 | basis |
|---|---|---|---|
| W14 (T-537 r2) | 0.975 | 1.23 | BOUNDED_MIN_BEARING [3.25, 4.10] |
| W15 + W16 joint | 0.47 | 1.1254 | 0.20 x 5.627 (column 0 to column 5.625 + roundings) |
| W18 (T-537 r2) | 0.17346 | 0.20886 | HELD_BY_NAME, V3 ceiling |
| W19 + W20 joint | 0 | 0.7624 | 0.20 x 3.812 (column 0 to column 3.8117 + roundings) |
| W24 | 0 | 1.342 | 0.20 x 6.710 |
| sum | 1.61846 | 4.66866 | |

| | before (T-537 r2) | after (R-T544-1) | change |
|---|---|---|---|
| material base m2 | HELD, AT_MOST 100.35754 | **97.30734 .. 100.35754** (RANGE) | low end established |
| AAC glue kg | HELD blank, AT_MOST 451.60893 | **437.88303 .. 451.60893** (BOUNDED_EXPOSURE) | -13.7259 .. 0 kg (-3.04 .. 0 %) from the AT_MOST |
| bags 25 kg net | HELD | 17.515321 .. 18.064357 | |

Beside (not the result): every lintel taking the whole shared pier -> faces hi 4.94166, base low 97.03434 m2 (not
buildable: the pier is counted twice). The conditional T-530 low end 443.27313 kg (legacy D x (w + 0.80) maxima taken as
ceilings) is 5.3901 kg ABOVE the measured low end: F-T537-1 confirmed by measurement (the 4 held faces may take up to
2.6626 m2, not 1.50).
AAC glue group (R-T523-1 via the T-523 function): before 17.643906 .. 18.16227 AT_LEAST (>= 18 .. 19), HELD; after
**35.159227 .. 36.226627 AT_LEAST (>= 36 .. 37), still HELD** (other members' losses / lines stay open): the known part
grows because the 1F host is now bounded, not because more glue is needed.

## 5. Part 2 (same topic, same run): the other three white AAC hosts with held lintels

The T-453 ledger still carries R-T498-1 legacy ranges on three more hosts whose 13 held / flagged lintels (head not
established; W13 / W26 FLAGGED: the head leaves room under some pieces only) use 'maximum' D x (w + 0.80), the lower
bound of a built lintel (F-T537-1). The same V3 run (`out/JAMB_EVIDENCE_T544_P2.csv`, 26 ends, no SEARCH_LIMIT end;
independent column projection AGREE 0.1 mm on every end) and R-T544-1 give:

| host | lintels: L_ceil m (face hi m2) | before (legacy) glue kg | after glue kg | moved into group |
|---|---|---|---|---|
| GF L-541cf721 0.20 DC, net 44.2975 | D-GF-09 2.501 (0.5002); W05+W06 joint 3.470 (0.694); W07 3.350 (0.670) | 194.02875 .. 199.33875 | **190.94985 .. 199.33875** | yes (FRESH) |
| 1F L-b7b4d784 0.20 DC, net 46.836 | W13 2.700 (0.540); W21+W22 3.470 (0.694); W23 3.350 (0.670); W25 2.500 (0.500) | 203.562 .. 210.762 | **199.944 .. 210.762** | yes (FRESH) |
| 2F L-bbb82de2 0.20 DC, net 15.9165 | W26 2.700 (0.540); W27 2.500 (0.500); W28+W29 joint 3.470 (0.694) | 65.14425 .. 71.62425 | 63.82125 .. 71.62425 conditional | NO: contract HELD in the candidate (T-523 STALE_CLASS, 2F D-39): stays HELD by name |

Ends worth naming: W06 / W22 / W29 END and W18-like jambs on a column face (a = 0.000: no masonry beside that jamb;
a lintel there bears into the column or is a designer detail); deficits below 0.40 at D-GF-09 END 0.1469, W05 / W21 /
W28 START 0.375, W25 / W27 END 0.100 (if those lintels exist: T-516-type FLAGGED_DEFICIT, designer). Joint spans equal
column face to column face (2.70 -> 6.17 = 3.47 m on all three pier pairs). The legacy low ends fall by 3.079 kg (GF,
-1.59 %), 3.618 kg (1F, -1.78 %), 1.323 kg (2F, conditional); high ends unchanged.

AAC glue group with every FRESH host moved (`t544_apply.build_all`): **34.891351 .. 36.226627 AT_LEAST (>= 35 .. 37),
HELD** (part 1 alone 35.159227 .. 36.226627): the low end drops 0.267876 bags because the two legacy low ends were no
bounds; 2F L-bbb82de2, the losses and the other open members keep the group HELD.

## 6. Verdicts, residuals

- Engine vs freelancer: no freelancer lintel or glue row (his RC workbook gives one rebar total): UNRESOLVED, no
  comparable cell. Engine verdict: the T-537 low end was correctly HELD; T-530's conditional low end ENGINE_WRONG as a
  bound (proposal already F-T537-1; now quantified -5.3901 kg).
- HELD (unchanged): the existence of the 4 lintels (head, designer D-45); if they exist, W16's pair with W15 (designer).
- Residual named: W14 / W15 / W18 faces are the merged T-537 r2 values (floor-to-mm ceilings, F-T537-2: < 1 mm per end,
  their hi understates by <= 0.0002 m2 each); not re-derived here. W24's ceiling is loose (4.219 m to a column): it is
  what the drawing proves; the head decides the rest.
- Not wired: research only; a wiring package carries the range into the T-498 stage line (manifest after T-549).

## 7. Lessons row (ERS s.7, proposed)

| 2026-11-06 | a HELD lintel's face stayed OPEN because its ends had no ceiling, and two lintels on one pier would each take the whole pier | the host material stayed HELD although the drawing bounds it; summing individual ceilings double-counts the pier | measure both jamb ends of every HELD lintel (and re-bound every legacy D x (w + 0.80) host range) (V3 order, re-search past the limit), round ceilings UP, one joint record per shared pier on one host | tests/t544_held_lintel_ceiling | T-544 |
