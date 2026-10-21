# Reinforcement completeness: M1's 89 bar-less components, one by one

**Background.** The M1 post-freeze finding PF-M1-03 identified 89 concrete components M1 carries with no bar row in S9 03: 53 beams, 30 ground beams and 6 lift.

`05_REINFORCEMENT_COMPLETENESS_89.csv` lists **each of them** with:
- the M1 category;
- how it was matched to the generic route;
- the generic component id;
- the generic rebar state and its reason;
- the generic bar model in kg, where one exists.

## How the match is made (no position guessing)

| M1 id form | match | rows |
|---|---|---|
| `BM-<floor>-<mark>-BLnnn-<hex>` | the hex is the beam TAG handle; the generic mark with the same text handle, then its bound band | 11 matched, 3 not |
| `CBO-<sheet>-<mark>-BLnnn#SPANk` | the continuous-beam tag bound to that line (pre-S6 occurrence register), then its generic band | 10 matched, 4 not |
| `SPAN:<sheet>:BLnnn:a-b` (untagged spans) | first, a generic band inherited from the tagged neighbour with the clear length (±0.05 m); else a generic band inside the stations (sheet-local mm, ±0.4 m) with the clear length (±0.10 m), unique | 8 matched, 17 not |
| `GSO-…` / `SOCC-…` (ground beams) | the face-line handles in the id (hex), against the generic band handles (the kernel's decimal ids) | 28 matched, 2 not |
| `LIFT-…` | none: no generic lift detector | 6 outside scope |

## Result

| family | generic bar model | generic MISSING_DATA | not matched / not bound | outside scope |
|---|---|---|---|---|
| beams (53) | 11 (741 kg) | 18 | 24 | — |
| ground beams (30) | 0 | 28 | 2 | — |
| lift (6) | — | — | — | 6 |
| **total (89)** | **11** | **46** | **26** | **6** |

**What MISSING_DATA means.** The generic route found the member and states why it has no bar quantity:
- ground beams: typical bars not read, the detail is only in the PDF (28);
- continuous-beam bars are per span, and the span order of this band is not established (10);
- no section for the band: unbound or multiple marks (8).

No component gets a kg/m³ ratio or a guessed bar.

**The 26 unmatched rows**
- Most are untagged spans that the generic route did not inherit, because the line's tag is too far or the span crosses a support differently. The rest are tags the generic route left unbound.
- Each row says which. They need either a better inheritance rule or a person to bind the tag.

**Generic-wide bar register for Alsenan** (`alsenan_route_g/REBAR_COMPLETENESS.csv`): 254 PROVISIONAL_MODEL and 161 MISSING_DATA over 415 concrete components. Every concrete component has a row, so a missing bar model is never hidden behind a total.

## Bar rules used (all named conventions, all reversible)

| rule | detail |
|---|---|
| hooks and bends | from the bar diameter: ACI 318-19 Tables 25.3.1 and 25.3.2 (PROVISIONAL_CODE_METHOD, not verified against a project document) |
| closed links | 2(a + b′) − 8 r_c + 2π r_c + 2 × 135° hook addition, with centreline legs |
| beam main bars | clear span + 2 × 40 d anchorage (BEAM_BAR_ANCHORAGE_D, range 0–50) |
| column main bars | storey height + 50 d lap (COLUMN_LAP_D, range 40–60) |
| footing mats | straight bars, cover 50 mm (FOOTING_BAR_END) |
| slab mesh | printed note, one direction (SLAB_MESH_DIRECTIONS, range 1–2) |
| mass | d² / 162 kg/m |

The closed-link and hook formulas are tested against an independent derivation in the synthetic generator: agreement to 1 µm, which is the engine's stated rounding.
