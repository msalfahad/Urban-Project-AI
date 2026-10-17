# S7 post-freeze comparison (restricted slab rebar QTO)

S7 was frozen at `16741ec`. The manifest sha256 is `b23f97b6db334e64...`.
This script refused to open any reference until three checks passed:
- every frozen hash still matches;
- the manifest is the one committed at the freeze;
- that commit holds no post-freeze file.

Nothing here changes S7. RESTRICTED_S7_PROJECT_BASIS_KG stays **3,802.015 kg**. That is the restricted lower bound of 476 items, over 57.099 m3 of S7-scope slab, or 66.6 kg/m3.

## Reference totals (matching scope)

| reference | matching | reference kg | S7 kg | reference - S7 | classes (kg) |
|---|---|---|---|---|---|
| OLD_URBAN_R4 | TOKEN_BY_TOKEN | 5,203.7 | 3,802.0 | 1,401.7 | ANCHORAGE_EXCLUDED +240.0, COUNT_CONVENTION +16.1, CURTAILMENT +502.6, GEOMETRY +29.3, REFERENCE_ASSUMPTION +356.2, SPECIAL_STRUCTURE_EXCLUDED +1,721.3, TOP_SUPPORT_RULE -1,463.7 |
| OLD_URBAN_R3 | FLOOR (through R4) | 5,215.3 | 3,802.0 | 1,413.3 | ANCHORAGE_EXCLUDED +240.0, COUNT_CONVENTION +16.1, CURTAILMENT +502.6, GEOMETRY +29.3, REFERENCE_ASSUMPTION +367.7, SPECIAL_STRUCTURE_EXCLUDED +1,721.3, TOP_SUPPORT_RULE -1,463.7 |
| OLD_URBAN_V3B | TOTAL (through R4) | 4,992.8 | 3,802.0 | 1,190.8 | ANCHORAGE_EXCLUDED +240.0, COUNT_CONVENTION +16.1, CURTAILMENT +502.6, GEOMETRY +29.3, REFERENCE_ASSUMPTION +145.2, SPECIAL_STRUCTURE_EXCLUDED +1,721.3, TOP_SUPPORT_RULE -1,463.7 |
| FREELANCER | CATEGORY | 5,400.0 | 3,802.0 | 1,598.0 | GEOMETRY +28.5, REFERENCE_ASSUMPTION +1,352.6, SPECIAL_STRUCTURE_EXCLUDED +216.9 |
| UC4N | NOT_COMPARABLE | n/a | 3,802.0 | n/a | - |
| CHRISTIANNP | CATEGORY | 0.0 | 3,802.0 | -3,802.0 | SCOPE -3,802.0 |
| ROUGH_90_KG_PER_M3 | SANITY_ONLY | 5,138.9 | 3,802.0 | 1,336.9 | REFERENCE_ASSUMPTION +1,336.9 |

## Old Urban R4, by floor

| floor | S7 kg (bottom / top) | R4 kg (lower bound + provisional) | R3 kg |
|---|---|---|---|
| GF_ROOF_SLAB | 2,162.8 (1,322.3 / 840.5) | 2,965.8 (2,417.3 + 548.5) | 2,977.4 |
| 1F_ROOF_SLAB | 1,321.2 (805.8 / 515.4) | 1,440.8 (1,166.1 + 274.7) | 1,440.8 |
| 2F_ROOF_SLAB | 318.0 (210.3 / 107.8) | 797.1 (606.5 + 190.7) | 797.1 |

R4 callout tokens: {'S7_LOCAL_TOP_COUNT_ONLY': 1, 'NOT_IN_S7_TOKEN_REGISTER': 8, 'S7_EXCLUDED': 12, 'MATCHED': 90, 'S7_SOURCE_CONFLICT': 4, 'S7_SOURCE_CONFLICT_FAMILY': 3, 'S7_EXPLICIT_COUNT_LENGTH_BLOCKED': 4, 'S7_REFERENCE_ONLY_LABEL': 1}.

## Root causes

**OLD_URBAN_R4**

- SPECIAL_STRUCTURE_EXCLUDED: +1,721.3 kg. R4 quantifies callouts S7 transfers to S8 or excludes (water-tank T&B, the GF-21 light-well 8Ø16/m face, dome / stair zones).
- TOP_SUPPORT_RULE: -1,463.7 kg. S7 quantifies plan note 2 (5Ø10/m, 1/3 span each side, from the face); R4 has no note-2 top steel.
- CURTAILMENT: +502.6 kg. R4 STOP50 stops 0.125 L at both ends (worst case) and adds a provisional extension where continuity is unclassified; S7 applies 0.125 L per end class and blocks the unresolved stop zones.
- REFERENCE_ASSUMPTION: +356.2 kg. R4 quantifies callouts S7 holds as source conflicts or count-only (the GF-22 two callouts 526 / 533, the 552 / 5B9 / 750 count notation, 79F, 7A2, the 3Ø16/Top graphic length, the corner bars) and a reference-only label (77D); for R3 / V3b it also holds the reference's own revision to R4.
- ANCHORAGE_EXCLUDED: +240.0 kg. R4 bar = clear span + measured embedment at both supports; S7 stops at the faces and blocks the anchorage / end cover.
- GEOMETRY: +29.3 kg. distribution width / run per callout: R4 one drawn bar per callout, S7 the whole panel in local strips.
- COUNT_CONVENTION: +16.1 kg. R4 bars = ceil(rate x w) / binder floor(w/s)+1; S7 = rate x 0.5 x W, unrounded.

**FREELANCER**

- REFERENCE_ASSUMPTION: +1,352.6 kg. a lump at ~90 kg/m3 against a restricted bar QTO; it also carries what S7 excludes and does not quantify (temperature steel, anchorage / end cover, transitions / laps, sunken extras, edges, oblique ends, conflicts) - not separable.
- SPECIAL_STRUCTURE_EXCLUDED: +216.9 kg. the 2F T18 slab row (water tank, S8 in S7) at the lump's implied ratio.
- GEOMETRY: +28.5 kg. freelancer net slab volume (excl. the tank) vs the S7 panel volume, at the lump's implied ratio.

**CHRISTIANNP**

- SCOPE: -3,802.0 kg. christiannp prices no slab steel (every slab callout left unbound).

**ROUGH_90**

- REFERENCE_ASSUMPTION: +1,336.9 kg. SANITY_CHECK_ONLY heuristic (calibrated on the freelancer convention) against a restricted lower-bound QTO; never promoted.

U-C4N gives one project net rebar total (22.619 t, incomplete). It has no slab figure, so there is no matching scope and no difference is classified.

The rough 90 kg/m3 profile is `SANITY_CHECK_ONLY`. It is shown, not used: no S7 quantity is tuned, scaled or promoted towards any reference. Each difference above is a scope, rule or convention that S7 states explicitly. A correction needs a new issue, new source evidence, a new regression and a new version.

There are no UNKNOWN rows.
