# T-707 Concrete column tail: F-T689-1 settled from the drawing, the 2 tank columns bounded below, formwork named

Worker 1 (lane S), 2026-11-11, branch `agents/task-T-707`. Research only, unwired: no engine module, candidate line,
rule / knowledge version file, key map or released default changed; nothing released; development villa, not an
accuracy claim. Drawings cited by Drive folder / title and DXF handle; no coordinate committed. New rules R-T707-1 /
-2 1.0.0 (`t707_rules.py`), built on R-T689-1 / -2, R-T682-1, R-T678-2, R-T669-2 (none edited). Tables:
`out/T707_COLUMN_TAIL.md` / `.json` (`t707_alsenan.py --write / --check`); own read `out/T707_OWN_READ.json`
(`t707_extract.py`, Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf', sha256 9f9d1179 = manifest, decoded into
`.work/private` only). Tests `tests/t707_column_tail` (21 incl. the hand villa V707 and the Alsenan rebuild).

## 1. The conflict, the two rules and their scope (task (a))

| Rule | Says | Provenance | Scope it was written for |
|---|---|---|---|
| R-T669-2 1.0.0 | roof column low = highest printed opening top + **printed** slab thickness; (iii) one plane = section draws one continuous top, plan prints no step or level change | T-669 on the 6 UPPER_ONLY 2F roof columns | a plate that prints its thickness |
| R-T678-2 1.0.0 / R-T682-1 1.0.0 (b) | one plane = one outline, no step, no level **or thickness** text inside; any thickness text -> two planes | T-678 on the annex roof (prints no thickness at all), Checker F-V678-2 | a plate that prints nothing inside |

On the 2F roof the two cannot both stand: R-T669-2 needs the T 18 that R-T682-1 (b) reads as 'two planes' (F-T689-1).
Per the Lead ruling (12:25) the drawing decides first, then the rule whose scope fits the element.

**Physical element.** The top surface of one cast roof slab. A column (one joint node, UP-CONC-JOINT-001) runs to the
top of the highest member framing in. A level mark or a drawn step prints a change of the top; a thickness text
prints a depth. A depth difference between panels can move the top by at most that difference (flush soffit: thicker
panel higher) or not at all (flush top); it cannot move the top the other way.

**What the ST drawing prints (own read this run).**

- One outline 8.10 x 6.80 m; 21 beam-edge lines on layer 1 -> 7 clear panels P1 .. P7 between the 0.20 bands.
- 100 entities inside: every line CONTINUOUS (no hidden / dashed step line), no INSERT (no section mark), no LEVEL
  text, no '+' mark. The same drawing prints levels where they change: LEVEL texts +0.15 / +0.30 / +1.00 / +9.70, and
  the two +9.70 marks 3F4 / 3F6 print the lower roofs right beside this outline on this plan (the convention record).
- Thickness: 'T 18' twice, one per panel: P2 (7B3 / 7B4) and P1 (1A7D / 1A7E), each with '(T&B)' (7AF / 7B0,
  1A7F / 1A80), and 'WATER TANK PLACE' (1A85) at the NW corner: the two tank-place panels. Every other panel takes the
  printed general note 7D (S-NOTE, decoded T-044 r2): **all slabs 16 cm unless stated**. In the whole ST set only
  three panels print a thickness (these two and one 'T 16' on the 1F roof plan, 768 / 769): a thickness text here
  means 'stated otherwise', a zone, not a level.
- Section A-A (arch sheet 10, T-669 merged): one continuous hatched roof slab, +13.90 on its top line.

So the plate prints one top plane (no level, no step, convention evidenced) with two printed thickness zones,
0.18 (P1, P2) and 0.16 (P3 .. P7). Neither old rule fits: R-T682-1 (b) refuses a plane the drawing does not split;
R-T669-2 transfers 0.18 to panels that print 0.16. **R-T707-1** states it: top_P >= s_lo - max(0, t_src - t_P), with
every panel's thickness printed (panel text or general note; never borrowed), a level / step / section step / dashed
line still refusing as before.

## 2. Corrected bound (task (a))

B8 (R-T689-1, merged, Gate A PASS): top >= 12.937 (W28 head 12.200 - 0.013 + 0.75). B8's south side borders P1
(0.18) and P4 (0.16): t_src = 0.18. Tank-zone tops >= 12.937; 0.16-zone tops >= 12.917.

| Line | Member (handle) | Panels touched | top >= | h_lo | V3.0.70 | After (HELD) | d low m3 |
|---|---|---|---|---|---|---|---|
| L-53f223b0 | C9 2F 20x70 (418) | P3 P4 P6 P7 (0.16) | 12.917 | 3.267 | 0.4242 .. 0.595 | **0.45738 .. 0.595** | +0.03318 |
| L-26f6b6f2 | C2 2F (41B) | P1 (0.18), P3 P4 | 12.937 | 3.287 | 0.303 .. 0.425 | **0.3287 .. 0.425** | +0.0257 |
| L-33a9b772 | C2 2F (41E) | P3 P5 P6 (0.16) | 12.917 | 3.267 | 0.303 .. 0.425 | **0.3267 .. 0.425** | +0.0237 |
| L-d79d17d1 | C1 2F (421) | P1 P2 (0.18), P3 P5 | 12.937 | 3.287 | 0.303 .. 0.425 | **0.3287 .. 0.425** | +0.0257 |
| L-541c7e56 | PC-2F (778), 0.08 .. 0.10 | P4 (0.16) | 12.917 | 2.517 (- 0.75 support) | 0.1824 .. 0.350 | **0.20136 .. 0.350** | +0.01896 |
| | **5 lines** | | | | | | **+0.12724** |

T-689 named +0.133640 on a flat-plate premise; the difference 0.0064 m3 = 0.02 m x (0.14 + 0.10 + 0.08) is the
thickness-zone allowance on the three 0.16-zone columns (418, 41E, PC-2F): the drawing does not exclude a flush
soffit, so those tops may sit 0.02 below the tank zone. High ends unchanged (D-39: +13.90 finished, 4.25 / 3.50 m).

R-T669-2 restated on the same rule: W26 (apex +12.50) sits under the T 18 stair-roof panel (D-T173-1, Checker), so its
soffit >= 12.50 and a 0.16 panel top >= 12.66, not the 12.68 now carried. The V3.0.70 lows of 418 / 41E / PC-2F are
therefore 0.0064 m3 above what R-T669-2 itself supports; superseded here by the higher B8 bound (no line goes down).
If the Checker refuses R-T707-1, those three lows must come DOWN by 0.0028 / 0.0020 / 0.0016 m3 (F-T707-1).

## 3. The two tank columns (task (b)): one-sided, D-44 kept

40F (C2 2F, L-0ede77cf; drawn 0.20 x 0.50 = schedule CGT 1D46 2ND 20x50, AGREE 0.10) touches P2 only; 424 (C3 2F,
L-c10e2945; drawn 0.25 x 0.50 vs schedule CGT 1D5A 2ND 20x50, CONFLICT 0.10 .. 0.125, D-66) touches P2 and P5. Both
are framed by B15 20 x 120 on the west band (borders P2 only), whose up / down-stand is D-44. Down-stand: column top =
slab top; up-stand: column top = B15 top > slab top. Either way top >= the P2 top >= 12.937 (R-T707-2):

| Line | Member | Low m3 | High | Beside (named, not applied) |
|---|---|---|---|---|
| L-0ede77cf | C2 2F tank 40F | **0.3287** (0.10 x 3.287) | OPEN, D-44 | down-stand h <= 4.25; up-stand (B15 bottom at P2 soffit) h <= 13.90 - 0.18 + 1.20 - 9.65 = 5.27 |
| L-c10e2945 | C3 2F tank 424 | **0.3287** (least 0.10 x 3.287) | OPEN, D-44 + D-66 | same |

COLUMN blank 2 -> **0**: STR.CONC.COLUMN held moves from 11.67283 .. 15.5015 (27 bounded) + 2 blank to
**11.80007 .. 15.5015 (27 bounded) + 2 LOWER_ONLY floor 0.6574 (high OPEN)**. Released 19.7765 unchanged.

## 4. Formwork consequence (task (c)): 13 STR.FORMWORK lines, HELD with their columns

Method of record UP-FW-001 draft (`struct_n10.py`, read only): sides = perimeter x (height - slab t), an UPPER_BOUND
by construction (FW-D3, framing beams' faces not deducted, D-N10-04). Per line: low = P_min x (h_lo - t_max),
high = P_max x (h_hi - t_min) over the panels touched; a CONFLICT section keeps both perimeters. Every FW line stays
HELD (not wired; the column is HELD), figures beside:

| Columns | FW m2 low .. high |
|---|---|
| T-693 six: C2 412 / annex 34A / 34D / 356 / annex C3 350 / C5 415 | 4.3498 .. 5.698 / 3.7608 .. 5.446 (x3) / 3.7608 .. 5.835 / 4.3778 .. 6.544 |
| this run: 418 / 41B / 41E / 421 / PC-2F | 5.5926 .. 7.362 / 4.3498 .. 5.726 (x3) / 2.8284 .. 4.676 |
| tank 40F / 424 | 4.3498 .. OPEN (each) |

Annex t = the general note 0.16 (the GFRS annex part prints no panel text, T-678 own read); a reader who holds the
annex thickness open (T-669 wording 'no annex roof slab thickness') keeps those four high ends open. Not summed.

## 5. Methods side by side (ERS s.2.2), verdicts, what stays held

- Owner manual method: member by member; a height without a printed datum is held (no storey value); a conflict keeps
  both readings (Q-61 C, X6). Drawing-derived: the same, plus the drawn bounds (R-T689-1 -> R-T707-1 / -2). Both hold
  the same high ends; the drawing method moves 5 lows (+0.12724) and gives 2 blank lines a floor (0.6574).
- Freelancer: columns per type x count (T-248 / T-683); not used for any bound, not comparable line by line.
- Verdicts: the 7 lows ENGINE (drawing) bound, DRAWING-CONFIRMED ends; every line stays HELD (D-39 high; D-44 for the
  tank pair; D-66 for 424 / PC-2F sections). No owner question: ERS 2.7 not met (designer items).
- F-T707-1 (rule consistency): R-T669-2's +0.18 is the tank-zone thickness; on the 0.16 zone its low is 12.66.
- F-T707-2 (register): D-44 names B15 only; its consequence on 40F / 424 high ends is now the only open end of those
  two lines (no new item needed).

## 6. Lessons rows (ERS s.7, PROPOSED)

| 2026-11-11 | a plane test refused a plate because it printed a thickness, while another rule needed that print | a
thickness text prints a depth, not a top; it moves the top by at most the printed difference | R-T707-1: zones carry
the bound less max(0, t_src - t_P); level / step still refuse | tests/t707_column_tail |
| 2026-11-11 | a column framed by a beam of open stand was left blank | both stands put its top at or above the slab
top: the low is drawn, only the high waits | R-T707-2 LOWER_ONLY, high OPEN by name | tests/t707_column_tail |

## 7. Checker re-measure list

1. Outline 397 / 39A / 392 / 38D; bands on layer 1 (x 0.2 / 2.7 / 2.9 / 4.7 / 4.9 / 7.9 m; y 0.2 / 1.4 / 1.6 /
   3.1 / 3.3 / 3.4 / 3.6 / 6.6) -> P1 .. P7; T 18 in P1 (1A7D / 1A7E) and P2 (7B3 / 7B4) only; general note 7D.
2. No LEVEL / '+' text, no INSERT, no non-continuous line inside; +9.70 marks 3F4 / 3F6 beside the outline.
3. Column outlines 418 / 41B / 41E / 421 / 778 / 40F / 424 and the panels each touches; B8 (38D / 38E, 412 -> 415)
   south side = P1 + P4; B15 band = P2 only. CGT rows 1D46 (C2) / 1D5A (C3) 2ND 20 x 50.
