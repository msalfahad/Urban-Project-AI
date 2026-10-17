# S8.3 post-freeze comparison

Run after the freeze (`16_S8_3_FREEZE_MANIFEST.json` 92bfe9c0b2b7…, verified before and after; nothing frozen changes).

| row | item | S8.3 | reference | value | same scope | class |
|---|---|---|---|---|---|---|
| PF-01 | concrete: two terrace dome shells (m3) | 5.081 | old Urban C-DOME-SHELL-12EB + -2F33 | 4.68 | True | GEOMETRY_INPUT |
| PF-02 | concrete: two terrace dome shells (m3) | 5.081 | freelancer QS 'G13' two of 3 domes | 4.52 | True | SURFACE_BASIS |
| PF-03 | concrete: tower dome shell (m3) | - | old Urban C-DOME-SHELL-1300 | 2.843 | False | POPULATION |
| PF-04 | concrete: tower dome shell (m3) | - | freelancer QS (one of 3) | 2.26 | False | POPULATION |
| PF-05-DOME-A | concrete: ring beam DOME-A (m3) | - | old Urban C-DOME-RING-12EB | 1.989 | False | NTS_BASIS |
| PF-05-DOME-B | concrete: ring beam DOME-B (m3) | - | old Urban C-DOME-RING-2F33 | 1.989 | False | NTS_BASIS |
| PF-05-DOME-TOWER | concrete: ring beam DOME-TOWER (m3) | - | old Urban C-DOME-RING-1300 | 1.989 | False | POPULATION |
| PF-06 | concrete: all dome lines (m3) | 5.081 | old Urban domes, verified layer | 7.523 | False | POPULATION |
| PF-07 | concrete: all dome lines (m3) | 5.081 | freelancer QS domes | 6.78 | False | POPULATION |
| PF-08 | reinforcement: two terrace domes (kg) | 602.111 | old Urban R-DOME-1F | 1325.877 | False | SCOPE |
| PF-09 | reinforcement: tower dome (kg) | - | old Urban R-DOME-2F_ROOF | 728.35 | False | POPULATION |
| PF-10 | reinforcement: domes (kg) | 602.111 | freelancer QS | - | False | NOT_COMPARABLE |
| PF-11-DOME-A | interface: slab region under DOME-A (m2, matched by area) | 16.492 | old Urban radial-fan void | 16.357 | True | GEOMETRY_INPUT |
| PF-12-DOME-A | interface: slab region under DOME-A (m2, matched by area) | 18.131 | christiannp kept as slab | 18.131 | True | NO_DIFFERENCE |
| PF-11-DOME-B | interface: slab region under DOME-B (m2, matched by area) | 17.127 | old Urban radial-fan void | 17.127 | True | NO_DIFFERENCE |
| PF-12-DOME-B | interface: slab region under DOME-B (m2, matched by area) | 19.335 | christiannp kept as slab | 19.335 | True | NO_DIFFERENCE |
| PF-13 | ownership: S6 dome ring arcs (kg) | 0 | S6 / S6.1 (frozen) | 0 | True | NO_DIFFERENCE |
| PF-14 | S7 top-support steel at the dome bays (kg) | 43.113 | S7 / S7A (frozen) | 43.113 | True | NO_DIFFERENCE |

## Why they differ

- **PF-01**: the old formula with rise 1.72 m reproduces 2.341 per shell; with the p.7 rise 1.90 it gives 2.542, within 1.0 litres of S8.3's exact 2.540681: the difference is the rise reading, not the formula.
- **PF-02**: freelancer 1 x 22.6 m2 x 0.1 m per dome (surface basis not stated); S8.3 mid-surface 25.4016 m2 x 0.10 equivalent, exact concentric caps.
- **PF-03**: old Urban counts the architectural-only tower dome as RC (VERIFIED_COMPLETE); S8.3 does not (no structural occurrence, section A-A draws none). S8.3's sensitivity with the terrace thickness, 2.844907, matches the old 2.843 (old formula 2.844): same arithmetic, different population decision.
- **PF-04**: the freelancer counts three domes; S8.3 counts two structural.
- **PF-05-DOME-A**: old: pi x 4.2222 x 0.20 x 0.75 = 1.990: the drawn N.I.S depth, which the source dimensions 'AS PER ARCH'; S8.3 keeps the depth and the plan position open (sensitivity 0.755-3.408 m3 per terrace ring).
- **PF-05-DOME-B**: old: pi x 4.2222 x 0.20 x 0.75 = 1.990: the drawn N.I.S depth, which the source dimensions 'AS PER ARCH'; S8.3 keeps the depth and the plan position open (sensitivity 0.755-3.408 m3 per terrace ring).
- **PF-05-DOME-TOWER**: a ring under an architectural-only dome.
- **PF-06**: old 7.523 = two terrace shells + the tower shell; its best layer 13.49 adds three provisional rings.
- **PF-07**: three domes in the freelancer, two in S8.3.
- **PF-08**: old = shell mesh at rise 1.72 (554.946 kg for two) + ring bars on the detail centreline (413.325 kg for two) + links at the N.I.S depth and laps (the rest); S8.3 releases only the mesh at rise 1.90 (602.461 kg old formula vs 602.111).
- **PF-09**: architectural-only dome.
- **PF-10**: the freelancer gives one steel figure for stairs and dome together.
- **PF-11-DOME-A**: S8.3 opening + plan-reading ring inside the bay; old Urban deducted this as a void.
- **PF-12-DOME-A**: christiannp keeps the whole bay rectangle as slab (not deducted); S7 excludes the dome-zone faces.
- **PF-11-DOME-B**: S8.3 opening + plan-reading ring inside the bay; old Urban deducted this as a void.
- **PF-12-DOME-B**: christiannp keeps the whole bay rectangle as slab (not deducted); S7 excludes the dome-zone faces.
- **PF-13**: eight segments move to S8.3 with no quantity.
- **PF-14**: neither added nor subtracted.
