# Capability coverage matrix (Phase 2B-9)

**Method:** ARCH_TAKEOFF_V2.8 (opt-in). V1 – V2.7.1 are unchanged.

**No category has an accuracy figure.** There is one real plan and no blind evaluation. The "Evidence" column says
what a quantity was checked against:

- **hand** — hand truth on a synthetic plan;
- **reader** — the independent reader / verifier on a real or synthetic plan;
- **none**.

The "Benchmark" column is the status under the sealed URBAN_BLIND_V2 protocol, which is unchanged. An UNSUPPORTED
metric is reported, never scored as zero.

## Reference plan, Mode A: line states

V2.8 has the same 487 lines and the same states as V2.7.1. The only changed quantity is the wall run, +0.16854 m.

| Release category | Lines | Of which |
|---|---|---|
| CONFIRMED | 296 | 196 SOURCE_DERIVED, 100 PROVISIONAL |
| HELD | 191 | 162 need drawing evidence, 20 an owner decision, 9 engineering review |
| CONDITIONAL scenario sets | 4 | never in a total |

## Matrix

| Capability | V2.7.1 | V2.8 (new) | Evidence | Benchmark | Remaining gap |
|---|---|---|---|---|---|
| **Wall-finish heights** | facts file only (project rule) | **drawing evidence hierarchy**: annotation > schedule > section / elevation > derived > floor note > project note > facts > Urban default; per trade (soffit vs ceiling); CONFLICT and overridden kept; floor-to-floor never used; missing-evidence report | hand: 9 evidence variants, units, invariance (25 tests) | was UNSUPPORTED for real heights; now PARTIAL (needs the drawings to carry the evidence) | the reference plan has no binding section; elevation reader (L-P9-02) |
| **Door heights** | owner reference fallback | schedule / annotation / note first; facts overridden by schedule; Urban default only as ASSUMED; door BOQ line carries the source | hand | PARTIAL | — |
| **Window height / sill / head / class** | width only | **opening schedule**: height, sill, head, class (WINDOW / FLOOR_GLAZING / SILL_NOT_ESTABLISHED), area or held; width check against the schedule | hand (6 opening tests) | was UNSUPPORTED; now PARTIAL | turned schedule sheet (L-P9-01); elevations |
| **Wall-face deductions** | each window at full height inside the band (assumed) | each opening's **own band** w × (min(head, H) − max(sill, 0)) per trade | hand (38.00 / 35.30 / 36.95 + 34.30 / ranges) | SUPPORTED where heights are evidenced | — |
| **Window reveals** | BLOCKED_RFI | jambs + head soffit from the **measured depth**, plaster PROVISIONAL; sill surface its own geometry; floor-glazing strip as floor; external strip separate | hand (0.39 / 0.60 / 0.53) | PARTIAL (PROVISIONAL) | frame / reveal detail |
| **Skirting at windows** | sill windows skirted by assumption | floor glazing not skirted; unknown sill → a range; edge by edge against F-17 (no double count) | hand; reader 7 / 7 villa rooms VERIFIED | SUPPORTED | — |
| Room floor areas | measured | as V2.7.1 | hand; reader faces | SUPPORTED | spaces closed by non-wall lines (D-P8-04); curved glazing loses the room (D-P9-01) |
| Wet-room floor, wall tile, plaster | measured with facts heights | heights from the section; owner full-height tile from F.C.L. | hand (worked example 2: 12.00 / 39.80 / 39.80) | SUPPORTED (with evidence) | review spaces (D-17) |
| Waterproofing | floor, upturn, doorway, layout, rolls | unchanged | hand: V2.5 proof reproduced (17.52 / 17.80 / 2 rolls) | SUPPORTED | junction / corner / penetration details |
| **Wall run (centreline)** | bands ≥ 0.30 m; curved bands | + **short returns and curved stubs** (0.05–0.30 m) as wall; plan strip conserved | hand (13.15, 0.413333); reader: return and arc censuses; reference plan +0.16854 m VERIFIED | run PARTIAL (PROVISIONAL) | masonry (BLOCKED: material and block height) |
| **Curved wall faces** | run on the mid arc; faces implicit | inner / centreline / outer arcs and radii recorded per curved wall | hand (4.712389 / 4.869469 / 5.026548) | SUPPORTED | external finishes not in the internal scope |
| **Lost rooms** | silent | room label in no closed space reported (open-area labels apart) | hand; reference plan: 0 lost rooms, 11 open-area labels | — | D-P9-01 root cause |
| Ceilings | measured, PROVISIONAL | as V2.7.1 | hand | PARTIAL | ceiling type |
| Doors (count, class, width, jamb plaster) | measured | jamb plaster height from the door's own evidence | hand | SUPPORTED | D-16 |
| Stairs | treads, landings | unchanged | earlier stages | PARTIAL | risers / flights from sections |
| Masonry by thickness (m², m³) | BLOCKED_RFI | BLOCKED_RFI (the material and the block height to the beam / soffit are not in a plan) | — | UNSUPPORTED | T.O.S. + beam depths + block spec |
| Change attribution | independent verification | + stub census, unknown-sill skirting takeoff | reference plan V2.7.1 → V2.8: 1 / 1 VERIFIED; villa 7 / 7 VERIFIED | — | zone-bounded space (D-P9-04) |
| Structural BOQ | route G (separate) | unchanged | earlier stages | not in URBAN_BLIND_V2 | combined export |
| Roofs, external works, formwork, excavation | absent | absent | — | not in URBAN_BLIND_V2 | `BOQ_CAPABILITY_GAP_AUDIT.md` |
