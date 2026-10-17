# 09 Ablation on ST7757 (each M8 convention alone)

- Source: `st7757/ABLATION.csv`, made by `st7757_run.py`.
- Each row changes **one** of the 37 M8 conventions and keeps the other 102 at V6.
- Every case ran: 62 cases, 0 NOT_SEPARABLE.
- Deltas are against the V6 run: RC measured base 319.800 m³, bounded total 313.235 – 476.110 m³.

**What each kind of case does.**

| Kind of convention | Case | What it tests |
|---|---|---|
| A choice with alternatives | each other option | the effect of the professional choice |
| A rule switch (single option) | the convention removed | what the rule adds |
| A number (low / base / high) | the base set to the low, then to the high | how sensitive the measured base is. The bounded range keeps the convention's own low / high, so it does not move |

## Rules: what each one adds

Ordered by the size of the effect on the measured base.

| Convention removed or changed | Measured base, m³ | Bounded low | Bounded high | Findings without range | What it means |
|---|---|---|---|---|---|
| without `SCOPE_FROM_FINDINGS` | −21.822 | – | – | – | the whole scope pass: domes 7.372 + boundary wall 7.220 + pool 3.495 + the two loose stair flights 3.734. With it off there is no section F, as in V5 |
| without `DOME_ON_TOP_PLAN` | −7.372 | −3.840 | +1.569 | 0 | the two 2F radial groups stay unsettled findings: bounded, not measured |
| without `BOUNDARY_WALL_ROW_BY_WIDTH` | −7.220 | −7.221 | +15.857 | 0 | the boundary strip is no longer measured by the B.W row; it falls back to a bound from 0 |
| `STAIR_UNPRINTED_WAIST` = UNRESOLVED_EXPOSURE | −6.220 | 0 | 0 | 0 | the two route stairs (1F 4.451 + GROUND 1.770) move from measured to unresolved. The bounded total does not move: the exposure is the same range |
| `STAIR_DRAWN_RUN` = SLAB_ZONE_EXPOSURE | −5.319 | −1.095 | +3.922 | 0 | the M7 behaviour: a stair zone held as an unresolved slab zone |
| without `STAIR_LOOSE_FLIGHT` | −3.734 | −2.703 | +1.572 | 0 | the GF flights and the GROUND loose flight are bounded, not measured |
| `STAIR_FLIGHT_ON_TWO_PLANS` = EACH_PLAN | +1.071 | +0.753 | 0 | 0 | a flight drawn on two plans would be counted twice |
| without `FINDING_BOUNDS` | 0 | +7.851 | −100.681 | **66** | without it, 66 findings have no range — the M7 state |
| without `STAIR_TREAD_ANGLE_WRAP` | 0 | 0 | 0 | 0 | no effect on ST7757; it matters under rotation (`10_PROPERTIES_AND_REGRESSION.md`) |
| without `NON_STRUCTURAL_LAYERS` | 0 | 0 | 0 | 0 | no effect on ST7757: no scope finding there is changed by it |
| without `PRINTED_DIMENSION_NOTES` | 0 | 0 | 0 | 0 | no printed note was read for a scope element on ST7757; every scope dimension there is a convention or a schedule row |
| without `STOREY_PLAN_MISSING_BRACKET` | 0 | 0 | 0 | 0 | no storey plan is missing on ST7757 |

## Numbers: how much the measured base depends on each

Only the conventions that moved the measured base on ST7757 are listed. In every case the bounded total did not
move: each range already spans its convention's low – high.

| Convention | Base set to low | Base set to high |
|---|---|---|
| `DOME_RISE_RATIO` (0.5 / 1; base 1) | −2.764 | 0 (the base is the high: a hemisphere) |
| `DOME_SHELL_THICKNESS_M` (0.10 / 0.15 m; base 0.12) | −1.228 | +1.843 |
| `STAIR_WAIST_CONVENTION_M` (0.15 / 0.20 m; base 0.175) | −1.060 | +1.060 |
| `POOL_WALL_HEIGHT_M` (1.2 / 2.0 m; base 1.6) | −0.496 | +0.496 |
| `STAIR_RISER_M` (0.15 / 0.18 m; base 0.165) | −0.335 | +0.343 |
| `POOL_FLOOR_THICKNESS_M` (0.20 / 0.30 m; base 0.25) | −0.302 | +0.302 |

**No effect on the measured base.** These conventions feed bounds or items that ST7757 does not measure:
- pool wall thickness (the drawn strip gives 0.2 m);
- every pit and tank number (the pit is not settled; the tank is referenced, not drawn);
- the dome ring depth (no ring drawn);
- the referenced sizes (allowances use the high end);
- parapet height and thickness (bounds only);
- the boundary-wall section (the schedule row measures it);
- slab step drop;
- unexplained strip depth and linework section.

## Reading the ablation

1. **The scope pass is what moves ST7757.** Of the +28.04 m³ over V5:
   - 21.82 m³ come from `SCOPE_FROM_FINDINGS` (domes, boundary wall, pool, loose flights);
   - 6.22 m³ come from the route stairs, which are measured under `STAIR_DRAWN_RUN` / `STAIR_UNPRINTED_WAIST`.
2. **Three single rules carry most of the measured scope.**
   - `DOME_ON_TOP_PLAN`: 7.37 m³.
   - `BOUNDARY_WALL_ROW_BY_WIDTH`: 7.22 m³.
   - The stair rules: 6.22 + 3.73 m³.

   These are the rules a reviewer should confirm first. W8-06 explains how the dome rule can misread a radial
   stair.
3. **Without `FINDING_BOUNDS` the engine is back to M7 on ranges.** 66 findings are volume-less and the bounded
   high falls by 100.7 m³. That 100.7 m³ is the exposure M7 did not show.
4. **Conventions matter less than rules.** The largest number sensitivity is the dome rise ratio (2.76 m³). The
   largest single choice is the unprinted stair waist (6.22 m³ between measured and unresolved). Each of these is
   inside the item ranges that the BOQ already prints.
