# 08 ST7757 positions (post-freeze, differences only)

**Rules of this record.**
- **Read after the freeze.** The external figures were read at run time from the M5 record
  (`research/urban_engine_m5_concrete_reconciliation/02C_FAMILY_TOTALS.csv`), after the M8 engine freeze.
- **Never copied.** They appear here and in `st7757/POSITIONS.csv` only as differences and in-range flags.
  `test_m8_package.py` checks that no external figure is copied into the package.
- **Positions, not targets.** No convention was set or changed against them.
- **Not blind.** ST7757 is post-discovery: the developer has seen M5's bridge in earlier milestones.

**The four positions.**

| Tag | What it is | Independent of the engine? |
|---|---|---|
| STAGE_RECONCILIATION | the project-specific stage pipeline (S8.x / S9), measured from the same drawings | no: the same developer, and M5 bridged the core families against it |
| FREELANCE_QS | the professional freelance QS takeoff | yes |
| MCP_RUN_1, MCP_RUN_2 | two runs of the MCP tools | yes. They report 9 families: no lintels, domes, pool, lift, tank, boundary wall, parapets or blinding |

**How to read the columns.**
- `DIFF_PCT` = (V6 measured base − position) / position. Positive: V6 measures more.
- `IN_V6_RANGE` = the position lies inside V6's bounded range for that family. For a family whose bound is not
  settled (the pit that could be LIFT / WALLS / WATER_TANK), the candidate high is added to the high end.
- `POSITION_ZERO`: the source gives 0 for that family. `NOT_IN_SOURCE`: the source does not report the family.

## Total reinforced concrete

| Position | V6 measured base vs position | Inside the family-sum range (318.556 – 466.878 m³)? |
|---|---|---|
| Stage reconciliation | +1.2 % | no: just below the low end. It lies inside the BOQ section F bounded total (313.235 – 476.110 m³) |
| Freelance QS | −6.0 % | yes |
| MCP run 1 | −5.3 % | yes |
| MCP run 2 | −4.0 % | yes |

**Why there are two ranges.**
- The TOTAL_RC row of `POSITIONS.csv` sums the family rows.
- The BOQ bounded total also includes bounds whose family is not settled, and the negative lows of hatch-on-member
  findings. That is why its low end is lower.

**The MCP totals are not like for like.** The MCP runs do not report domes, pool, boundary wall, tank, parapets or
lift; for the total they count 0. Their total agreement with V6 therefore partly comes from offsetting family
differences.

## By family

| Family | V6 measured, m³ | V6 bounded, m³ | Stage | Freelance QS | MCP 1 | MCP 2 |
|---|---|---|---|---|---|---|
| Footings | 66.264 | 64.520 – 78.037 | 0.0 % ✓ | +1.0 % ✓ | −0.5 % ✓ | +0.9 % ✓ |
| Strap beams | 3.781 | 3.555 – 4.281 | 0.0 % ✓ | +11.5 % | −38.2 % | −37.5 % |
| Foundation necks | 10.855 | 11.260 – 16.210 | 0.0 % | +23.3 % | +76.5 % | +76.5 % |
| Ground beams | 30.702 | 26.846 – 31.583 | 0.0 % ✓ | −19.2 % | −14.7 % | −14.7 % |
| Ground slab | 17.241 | 21.170 – 21.170 | +2.9 % | −41.7 % | −46.4 % | −46.8 % |
| Columns GF–2F | 36.714 | 35.580 – 55.755 | 0.0 % ✓ | +28.6 % | −5.7 % ✓ | −4.6 % ✓ |
| Suspended beams | 64.820 | 72.625 – 100.555 | +0.4 % | −1.7 % | +27.5 % | +39.1 % |
| Suspended slabs | 60.919 | 60.919 – 65.777 | −0.1 % ✓ | +1.8 % | −36.3 % | −37.0 % |
| Lintels | 0.463 | 0.432 – 3.909 | 0.0 % ✓ | position zero | not in source | not in source |
| **Stairs** | 9.954 | 7.891 – 14.472 (+0.967 candidate) | +9.9 % ✓ | −33.9 % ✓ | +86.9 % | +97.2 % |
| **Domes and rings** | 7.372 | 3.839 – 9.215 | +9.4 % ✓ | +8.7 % ✓ | not in source | not in source |
| **Swimming pool** | 3.495 | 2.697 – 4.293 | −50.7 % | −60.6 % | not in source | not in source |
| **Lift pit walls** | 0 | 0 (+6.745 candidate) | −100 % ✓ | −100 % ✓ | not in source | not in source |
| **Water tank** | 0 | 0 – 10.000 | position zero ✓ | position zero ✓ | not in source | not in source |
| **Boundary wall** | 7.220 | 7.220 | position zero | −4.5 % | not in source | not in source |
| **Parapets** | 0 | 0 – 44.400 | position zero ✓ | position zero ✓ | not in source | not in source |
| Blinding (plain) | 22.155 | 22.155 – 67.371 | 0.0 % ✓ | −52.9 % ✓ | not in source | not in source |

✓ = the position lies inside V6's bounded range. Families in bold are new in M8.

**A quirk of the range for necks and beams.** The bounded low adds the unresolved items' low exposure to the
measured items. So a position equal to the measured base (stage: 0.0 % on necks, +0.4 % on beams) can lie below
the bounded low. The same happens to the freelance QS on beams (−1.7 %) and slabs (+1.8 %).

## Agreement count (from `st7757/POSITIONS.csv`)

Families with a numeric difference (position zero and not-in-source excluded):

| Position | Families compared | Within ±10 % | Within ±20 % | Inside V6's range |
|---|---|---|---|---|
| Stage reconciliation | 14 | 12 | 12 | 10 |
| Freelance QS | 14 | 5 (footings, beams, slabs, domes, boundary wall) | 7 | 5 |
| MCP run 1 | 9 | 2 (footings, columns) | 3 | 2 |
| MCP run 2 | 9 | 2 (footings, columns) | 3 | 2 |

The stage agreement is expected: it is not an independent check (see the table at the top).

## What this does and does not show

**What it shows.**
- **Total RC: within 6 % of all three external positions, and all three lie inside V6's ranges.** Under V5 (M7)
  the measured RC was 28.04 m³ lower and the scope families had no volume at all.
- **More families agree with the freelance QS than with the MCPs.** Within ±10 %: 5 against 2.
  - Beams and slabs: V6 sits with the freelance QS; both MCPs differ from it by 27–39 %.
  - Stairs: V6 lies between the freelance QS and the MCPs. The MCPs are about half of V6 and the freelance QS is
    about half again above it. The freelance QS is inside V6's range only through the candidate pit.
  - Domes: V6 is within 9 % of the freelance QS. The MCPs report no domes.
- **The new families have positions to compare against.** In M7 these families had no volume. In M8:
  - domes and the boundary wall are within 10 % of the freelance QS;
  - stairs are inside V6's range.

**What it does not show.**
- **That V6 is more accurate than the MCPs, or as accurate as the freelance QS.** No position is a released truth.
  On beams, slabs and stairs the freelance QS and the MCPs are further apart from each other than either is from
  V6 (this follows from the two differences). Agreement with one of them is not accuracy.
- **That the engine is right on ST7757's core families.** These gaps are unchanged by M8 (W8-10):
  - ground slab: 42–47 % below the external positions;
  - ground beams: 15–19 % below;
  - necks: 23–77 % above;
  - columns: 29 % above the freelance QS.

  The causes listed by the M5 bridge are still open: a perimeter tie beam, the slab under the stairs, and levels.
- **Pool.** V6 measures half of the stage figure and less than half of the freelance QS. Only the drawn wall strip
  is read (W8-01).

**The honest summary for the goal ("as strong as a freelancer, more accurate than the MCPs").** On ST7757:
- V6's total is in the same place as all three external positions.
- V6 now measures or bounds every family the freelance QS prices.
- V6 agrees with the freelance QS on more families (5 within ±10 %) than with either MCP run (2).

That is a position, not proof. Proof needs two things (`12_QUOTATION_STATUS.md`):
- a blind second villa;
- engineer-released quantities.
