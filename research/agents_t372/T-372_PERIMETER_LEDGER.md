# T-372 (research part): B9-04 perimeter joint mortar bound line by line to the V3.0.63 black-block mortar lines

Worker 2, 2026-11-10, base engine 8cb64551 (candidate of record ARCH_TAKEOFF_V3.0.63, NOT RELEASED; released V2.9 +
route G). Research only, nothing wired: `research/agents_t372/*`, `tests/t372_perimeter_ledger/*`. No engine, rule,
knowledge, registry or candidate file changed. No drawing, workbook, client name or coordinate here. The wiring part of
T-372 stays with the hub (after T-668, owner order concrete -> rebar -> masonry).

## 1. Physical element (ERS s.2.1)

The mortar between the last block and concrete: vertical at a column face / beam-drop side / lintel end, horizontal
over the last course under a soffit, and (new here) the bed between the bearing course and a precast lintel. It is the
INCREMENT over the panel module figure (R-T520-1): part of every perimeter joint is already inside the panel
`A b (1 - w h / W H)`. Installed, wet, before waste; 10 mm joint ASSUMED - OWNER-APPROVED (owner 2026-10-29).

## 2. Evidence used (all merged; no new drawing read this run)

T-520 (per wall + 71 junction bands, own DXF read, Checker Gate A 2/4 walls re-measured), T-615 (0.15 m perimeter
re-run on the Q-80 module, rulebook 1.1.0), T-670 (V3.0.63 mortar lines restated on 1.1.0), T-527 LINTEL_BEARING_V3
(available masonry per lintel end), the V3.0.63 line index (second path), rulebook 1.1.0 UPC-BLACK-MORTAR-001.

## 3. Result per mortar line (T372_PERIMETER_LEDGER.csv / .json)

| mortar line (host) | panel m3 (T-670) | perimeter m3 low .. high | % of panel | walls |
|---|---|---|---|---|
| GF 0.20 VERIFIED | 0.916919 | 0.058854 | 6.42 | GF-W01 |
| 1F 0.20 VERIFIED | 0.352525 | 0.039291 | 11.15 | 1F-W02 / W03 / W09 |
| GF 0.15 VERIFIED | 0.109463 | 0.003167 | 2.89 | GF-W21 / W33 |
| GF 0.15 DRAWING_CONFIRMED | 0.095082 | 0.003237 (+ GF-W22 beside, D-27) | 3.40 | GF-W19 |
| GF 0.15 OWNER_APPROVED | 0.260604 | 0.010361 .. 0.010639 | 3.98 .. 4.08 | GF-W28 / W29 |
| 1F 0.15 VERIFIED | 0.578768 | 0.018729 .. 0.019896 | 3.24 .. 3.44 | 1F-W20 / W21 / W22 |
| 1F 0.15 DRAWING_CONFIRMED | 0.279579 | 0.014744 .. 0.020830 | 5.27 .. 7.45 | 1F-W18 / W24 |
| 1F 0.15 OWNER_APPROVED | 0.618315 .. 0.622076 | 0.028344 .. 0.032121 | 4.56 .. 5.19 | 1F-W12 / 13 / 17 / 19 / 23 |
| **8 valued lines** | **3.211255 .. 3.215016** | **0.176727 .. 0.188035** (figure 0.177283) | **5.50 .. 5.86** | 19 walls |
| 12 HELD lines | blank | blank, host cause named (2F D-39 x3 with T-520 expressions beside; 7 BLOCK_WALL_NOT_ESTABLISHED; MAIN_S; ANNEX_S) | | |

Ranges are physical: a block-to-block end may be butt-jointed or bonded (no junction detail printed, R-T520-1), and
two 0.20 m lintel bands (GF-W28 D-GF-13, 1F-W23) depend on whether the lintel reaches the column. Never a picked point.

Beside, never summed (separate HELD / bounded components for the wiring row):
- 23 HELD junction bands by name (dome-opening pieces of 1F-W13 / W17 / W24, the lintel ends 'bearing not
  established' of D-GF-10, D-1F-03 / 04 / 07 / 10, D-1F-08 next to the dome ring): bound 0 .. 0.017896 m3.
- R-T372-1 (5) LINTEL BEARING BED (new): the joint between the top of the bearing course and the lintel underside is
  not credited by the panel (the lintel face is deducted from its base). Per REQUIRED lintel on the candidate's face
  basis (w + 0.80) x D, 0.40 m per end, from T-527 V3 available masonry: available >= 0.40 EXACT; DEFICIT at a column
  [0, available]; DEFICIT at a masonry end [0, 0.40]. 8 lintels: D-1F-02 / 08, D-GF-13 EXACT 0.80 m; D-1F-03 / 07 / 10,
  D-GF-10 0.40 .. 0.80 m; D-1F-04 0.40 .. 0.479 m (0.079 m pier to the column) -> **0.006113 .. 0.008443 m3**;
  D-1F-09 HELD (lintel HELD_RANGE in the candidate). It moves with the lintel basis: if the payable lintel changes
  length (T-644 / T-650 standard pieces), re-run.
- Cement / sand of the perimeter as its OWN producer key 'B9-04 PERIMETER JOINT MORTAR' (UPC-BLACK-MORTAR-001, read
  from rulebook 1.1.0): 1.4138 .. 1.5043 bags, 0.1944 .. 0.2068 m3 loose sand; bags rounded only at the purchasing
  group; waste HELD.

## 4. Independent checks and reconciliation (m3, to the named cause)

- Second path: all 20 MAS.MORTAR.BLACK lines and their MAS.BLOCK hosts read straight from the V3.0.63 index (class,
  net, element id) = T-670: 0 mismatches. Host walls sum to the host net on every valued line (e.g. 1F 0.15
  OWNER_APPROVED 11.5815 + 16.8073 + 4.6943 + 5.512 + 19.6578 = 58.2529 m2).
- T-615 = T-520 on all 15 carried 0.15 m walls (max difference 0.000000 m3).
- Own arithmetic per wall, f (soffit + vertical c=2 - corners x j) + f x block-end range, f = kappa b j
  (0.0018525 / 0.001389375 m3/m): agrees to 2e-6 m3 on 21 of 24 walls; the 3 residuals are named: GF-W22 high
  -0.000004 (D-27 soffit 2.9795 .. 2.9825 m), GF-W28 and 1F-W23 low +0.000278 = 0.20 m lintel band x f (lintel
  reaching the column scenario). Example 1F-W18: (5.20 + 4.04 - 0.02) x 0.001389375 = 0.012810; + 4.04 x f = 0.018423.
- T-520 s.5 (GF + 1F, 20 walls 0.180867 .. 0.192179): = this ledger 0.176727 .. 0.188035 + GF-W22 0.004140 .. 0.004144
  (carried beside: its area is not in its host's 8.595 m2, D-27 conflict on the parent). Residual 0.
- T-367 3.870113 m3 (contract basis V3.0.26) and the Checker's 'about 0.2 .. 0.5 m3' bound: reconciled by T-520 (kappa,
  module credit, c = 1 walls); unchanged here. Panel + perimeter on the 8 valued lines: 3.387982 .. 3.403051 m3
  installed (+5.50 .. +5.86 % over the panel), plus the two beside components.

- Trial BOQ r4 (T-654, wiring manifest V20 overlay) already stages one perimeter line per host
  (`NEW:MAS.MORTAR.BLACK:PERIMETER:<host>`, R-T629-1 (d): line at the low end + HELD companion 0 .. high - low, OPEN
  where named pieces stay HELD). Line by line: all 8 lows residual 0.000000 m3; bounded companions agree (1F 0.15
  VERIFIED 0.001167, GF 0.15 OWNER_APPROVED 0.000278); OPEN companions = exactly the hosts with named HELD dome pieces
  (1F-W13 / W17 on 1F OWNER_APPROVED, 1F-W24 on 1F DRAWING_CONFIRMED); this ledger states their drawn part beside
  (0.003777 / 0.006086 m3 + the pieces OPEN). The trial's 3.387982 m3 = panel low 3.211255 + perimeter low 0.176727.

**F-T372-1 (label):** the two 0.20 m perimeter lines (hosts L-1c53fadb, L-10dd62f6; 0.058854 + 0.039291 m3) carry
evidence UNKNOWN in trial r4; T-520 states COMPUTED, 10 mm joint ASSUMED - OWNER-APPROVED. The wiring row labels them.
**F-T372-2 (missing components):** not in the V20 overlay: the lintel bearing bed 0.006113 .. 0.008443 m3 (8 lintels,
1 HELD), GF-W22 0.004140 .. 0.004144 m3 (beside its host, D-27), 23 drawn held junction bands 0 .. 0.017896 m3. The
wiring row adds them as HELD bounded companions by name (never 0, never summed into the panel).

## 5. Status, verdicts, lesson

Status: 0.20 m rows COMPUTED (T-520, Checker re-measured 2 / 4 walls); 0.15 m rows ASSUMED - OWNER-APPROVED (Q-80
module + 10 mm joint, T-615); every perimeter line PROVISIONAL (joint not printed); none VERIFIED. Freelancer: no mortar
row -> RULE_DIFFERENCE, no %. Verdict proposals: per-line binding ENGINE_RIGHT on the method (hand checks above);
lintel bearing bed ENGINE_RIGHT as a bounded component (block-count argument, fixture), UNRESOLVED as a point until the
deficit lintels are settled. Proposed lessons row (ERS s.7): "a component measured wall by wall (perimeter joints) is
bound to the candidate's material lines through the host id and an area-sum check, walls outside their host's figure go
beside by name, and a deducted face (lintel) leaves an uncredited bed joint at its bearings (every villa; T-372)".

## 6. For the wiring row and the Checker

Wire one perimeter component per valued mortar line (bound by `mortar_line_id`, beside the panel, never summed), the 12
HELD lines blank with their causes, lintel bed + held bands as named bounded components. Checker re-measure proposal:
1F-W18 (column-to-column segment 2.725 .. 6.20, 3.45 m + 0.25 m + soffit) and the D-1F-04 START pier (0.079 m to the
column, T-527 V3).
