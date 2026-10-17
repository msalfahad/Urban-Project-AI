# S8.3 errata (dated correction layer)

S8.3 stays frozen (`16_S8_3_FREEZE_MANIFEST.json` 92bfe9c0b2b7…, verified before and after). These errata change no released quantity: concrete stays 5.081361321 m3 and reinforcement 602.111303562 kg.

- **S8.3-E01** (NOTE_CORRECTION, 07_REBAR_NOTATION_REGISTER.csv): both cuts draw all labelled bars: [3, 2, 2, 3] and [3, 2, 2, 3] (bottom, side, side, top) plus one unlabelled small bar each (E02). Quantity effect: none (graphic completeness only).
- **S8.3-E02** (OBJECT_ADDED, 07_REBAR_NOTATION_REGISTER.csv / 08_REBAR_QTO_REGISTER.csv): UNLABELLED_JUNCTION_BAR: one per cut (1A4D: 324.5 units from the outer face, 458.7 below the ring top, drawn 0.667 of a labelled bar, 1A4F: 324.5 units from the outer face, 458.7 below the ring top, drawn 0.667 of a labelled bar); it bears on the outer leg of the shell bar where that bar turns down into the ring; one family per dome (the two cuts are the one ring). Quantity effect: none: BLOCKED_UNQUANTIFIED for DOME-A and DOME-B (no label, no stated diameter, role or length; N.I.S drawing).
- **S8.3-E03** (EVIDENCE_ADDED, evidence (no frozen row changes)): structural sheets ['FFRS', 'SFRS', 'DET']: 799 primitives and inserts, 0 with a non +Z extrusion, 0 mirrored inserts; architectural DXF: 0 non +Z extrusions, 13 mirrored inserts (AR1, D115, D120, D215, D315, arch120, d220), 0 within 3 m of a dome centre. Quantity effect: none.

Found by re-auditing the frozen package against the brief's 'anchorage and junction bars' item. No earlier Urban, freelancer or donor figure informed it, and no post-freeze comparison row depends on it.
