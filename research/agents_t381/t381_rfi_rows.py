"""T-381 DESIGNER_RFI_ROWS_LANE_A_V1: proposed designer RFI rows for the lane A holds no drawing settles (Alsenan).

Research only. Nothing is sent, no rfi file is edited (the Lead applies the rows), no candidate line, rule, method or
released quantity changes. Drawings are named by Drive folder and title only; no client name, no drawing content beyond
sheet / layer / handle references.

Every row is checked by the rules of R-RFI-BIND-1 (T-376) as they apply to lane A:
  (i)   at least one citation that RESOLVES against a merged evidence file under research/ (the quoted token must be in
        that file); own readings of this run are listed apart and never replace a ledger citation;
  (ii)  the candidate line ids / held items it unlocks and the quantity it governs in its own unit: a range (low < high or
        a HELD bound), or HELD unquantified with a reason; a missing value is None (HELD), never 0;
  (iii) one fact once: two rows with the same fact key are refused; a row that adds to an existing RFI must name an id
        that exists in the RFI snapshot; a NEW id must not exist yet;
  (iv)  the owner rules searched are named, and a row whose fact an answered owner rule settles is refused (not an RFI);
  (v)   no Arabic script and no client name in any text (public repository).

Run: python3 -I research/agents_t381/t381_rfi_rows.py [--check]  (writes / compares T381_RFI_ROWS.csv and
T381_SUMMARY.json next to this file).
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

METHOD = "DESIGNER_RFI_ROWS_LANE_A_V1"
UNITS = {"m2", "m.l", "pcs"}
VERDICTS = {"NEW", "ADD_TO"}

# Snapshot of the open RFI ids (board agents/control @ f81a1770, rfi/A_PRIORITY_RFI.md and rfi/B_REMAINING_RFI.md
# headings, read 2026-10-31). The Lead re-checks against the live files when applying the rows.
RFI_IDS = frozenset(
    ["RFI-B-S09", "RFI-B-S10", "RFI-B-S11", "RFI-B-S12", "RFI-B-S13", "RFI-B-S14", "RFI-B-S16", "RFI-B-S17",
     "RFI-B-S18", "RFI-B-S19", "RFI-B-S20", "RFI-B-S21", "RFI-B-S22", "RFI-B-S29", "RFI-B-S30", "RFI-B-S31",
     "RFI-B-S32", "RFI-B-S33", "RFI-B-S34", "RFI-B-SH",
     "RFI-B-A01", "RFI-B-A02", "RFI-B-A03", "RFI-B-A04", "RFI-B-A05", "RFI-B-A07", "RFI-B-A08", "RFI-B-A09",
     "RFI-B-A10", "RFI-B-A11", "RFI-B-A12", "RFI-B-A13"]
    + [f"RFI-S{n:02d}" for n in range(1, 29)] + [f"RFI-A{n:02d}" for n in range(1, 10)])

# Owner rules searched (OWNER_QUESTIONS_ANSWERED.md) and the facts they settle. A row whose fact key is listed here is
# refused: an answered owner rule is not an RFI.
OWNER_SETTLED = {
    "shower.tanking_height": "Q-40 A (no tanking above the 0.20 m upturn; wet walls tiled full height, Q-48 A)",
    "window.W17.area": "Q-32 A / Q-39 / Q-76 A (W17 window unit 9.870 m2 on the opening line)",
    "door.height_unprinted": "Q-55 C (internal door 2.20 m, doors only)",
    "kitchen.waterproofing": "Q-30 A (kitchen classed wet)",
}

ARABIC = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")


def row(**kw):
    return kw


# ------------------------------------------------------------------------------------------------ the proposed rows
ROWS = [
    row(
        row_id="R01", fact="sanitary.kitchen_pantry_laundry_fixture", verdict="NEW", target="RFI-B-A14",
        part="(a)", discipline="architect / sanitary designer",
        question=("The sanitary sheet drains the GF KITCHEN (FD 4 in), the GF PANTRY (FD 3 in) and the 1F LAUNDRY "
                  "(FD 4 in) but draws no sink, washer or other fixture in them, and the architectural plan draws none "
                  "either. Which fixtures are provided in each of these three rooms (kitchen sink, pantry sink, washing "
                  "machine point) and where do they waste?"),
        citations=[("research/agents_t370/T-370_SANITARY_FIXTURE_REGISTER.md", "no sink drawn on either sheet"),
                   ("research/agents_t370/T-370_SANITARY_FIXTURE_REGISTER.md", "no washer / sink drawn")],
        own_reading=["sanitary-7757.pdf p.1 rendered 300 dpi around the GF kitchen: FD 4 in and a CO 4 in, no fixture "
                     "symbol", "P7757.dxf: no TEXT / MTEXT naming a sink in English; insert census has no sink block; "
                     "the 'kit' label 276 and 'PAN' 178 / 'laun' BDD carry no fixture insert within 1.8 m"],
        owner_rules_checked=["Q-30 A (kitchen wet: classification only, no fixture)", "Q-48 A"],
        why_no_rule="no owner rule gives a fixture count; a sink is a fixture the BOQ needs (B12-01), not a convention",
        unlocks=["B12-01 sink / appliance points in KITCHEN 276, PANTRY 178, LAUNDRY BDD (no candidate line: B12-01 "
                 "EXPERIMENTAL, T-370 s.6)"],
        unit="pcs", low=None, high=None,
        held_reason="count per room UNKNOWN: printed on no sheet (never inferred, never 0)",
        stays_held="sink / washer points UNKNOWN; their waste branches; kitchen tile zone stays with RFI-B-A12",
    ),
    row(
        row_id="R02", fact="sanitary.GF_WC_1C8_valve_symbol", verdict="NEW", target="RFI-B-A14",
        part="(b)", discipline="architect / sanitary designer",
        question=("In the GF W.C beside the kitchen (by the driver's room) the sanitary sheet draws, next to the "
                  "FD 4 in, the valve symbol that the 1F and 2F sheets draw inside a screened shower zone, with no "
                  "screen, no tray and no legend entry. What is it: a shower, a hand-shower / shattaf point, or "
                  "something else?"),
        citations=[("research/agents_t370/T-370_SANITARY_FIXTURE_REGISTER.md", "UNKNOWN valve symbol"),
                   ("research/agents_t369/T-369_SHOWER_FLOOR_TANKING.md", "UNK-GF-01")],
        own_reading=["sanitary-7757.pdf p.1 rendered 300 dpi: the yellow valve symbol at the FD 4 in of that W.C, no "
                     "screen line, no tray; same symbol as p.2 walk-in zones"],
        owner_rules_checked=["Q-40 A (tanking: none, so 0 m2 either way)"],
        why_no_rule="a symbol's identity is a drawing fact; the legend does not define it",
        unlocks=["B12-01 shower count 6 (DRAWING-CONFIRMED) or 7; hand-shower point 0 or 1 (no candidate line)"],
        unit="pcs", low=0, high=1,
        held_reason="",
        stays_held="UNK-GF-01 UNKNOWN, not counted; waterproofing impact 0 m2 either way (T-369: inside GF-05 B8-01 / "
                   "B8-03)",
    ),
    row(
        row_id="R03", fact="shower.zone_and_tray_extent", verdict="ADD_TO", target="RFI-B-A12",
        part="(add: wet-room details)", discipline="architect",
        question=("Within the wet-room details asked in A12: the size of the three shower trays (GF bath by the master "
                  "bedroom, 1F bath by the laundry, 1F east bath) and the extent of the three screened walk-in zones "
                  "(the two 1F west twin baths, the 2F W.C). The sanitary sheet draws them and is marked not to scale; "
                  "no sheet dimensions them."),
        citations=[("research/agents_t369/T-369_SHOWER_FLOOR_TANKING.md", "not dimensioned on any sheet"),
                   ("research/agents_t369/T-369_SHOWER_FLOOR_TANKING.md", "SH-1F-01")],
        own_reading=["P7757.dxf: the dimensions within 1.8 m of the bath labels C2C / C2F and the WC label 12B6 are "
                     "room and wall dimensions only (FF1 3650, 1008 / 101F 2050, 10AB 2450; 138E 2500, 139A 1800, "
                     "13D8 3000, ...); no screen line or tray is drawn on the architectural plan",
                     "sanitary-7757.pdf p.2 rendered 300 dpi: screen lines across both 1F west twin baths, undimensioned"],
        owner_rules_checked=["Q-40 A", "Q-48 A", "UP-WP-004 1.0.0"],
        why_no_rule="the rules settle the membrane (0.000 m2 extra, ASSUMED - OWNER-APPROVED); the extent is a drawing fact",
        unlocks=["6 HELD shower extents (T-369 register); tray size of 3 tray pcs (B12-01 specification)"],
        unit="m2", low=None, high=None,
        held_reason="governs NO current BOQ quantity (B8-01 / B8-03 / B8-04 unchanged by any answer); information for "
                    "a separate falls / tray item only: asked inside A12, never as its own question",
        stays_held="6 extents HELD; B8-04 stays 0.000 ASSUMED - OWNER-APPROVED (Q-40 A)",
    ),
    row(
        row_id="R04", fact="arch.W17.head_soffit_through_wall", verdict="ADD_TO", target="RFI-B-A04",
        part="(b)", discipline="architect",
        question=("W17 (1F, curved on plan, over the pool): the NW elevation draws the arched head on the exterior face "
                  "only. How does the head soffit run through the 0.20 m curved wall: radially (the same head height on "
                  "both faces along each radius, like the drawn radial jambs) or straight through in the view direction? "
                  "A section or interior elevation of W17 settles it."),
        citations=[("research/agents_t302/T-302_W17_ARCHED_HOLE.md", "RADIAL gives the room side 8.9965, PRISMATIC 8.7414"),
                   ("research/agents_t377/CANDIDATE_T377.csv", "L-31db3c83552682d92ca3"),
                   ("research/agents_t377/CANDIDATE_T377.csv", "L-349db74a70e1eecda2d2"),
                   ("research/agents_t377/CANDIDATE_T377.csv", "L-c90d5d6c06a671fc3b99")],
        own_reading=[],
        owner_rules_checked=["Q-32 A", "Q-39", "Q-76 A (window unit only)"],
        why_no_rule="the owner rules give the WINDOW m2 on the opening line; the finish hole and reveals follow the built "
                    "soffit, a drawing fact (T-238 A5)",
        unlocks=["L-31db3c83552682d92ca3 FIN.PLASTER 1F 61.4626 .. 61.7177 m2",
                 "L-349db74a70e1eecda2d2 FIN.PAINT 1F 61.4626 .. 61.7177 m2",
                 "L-c90d5d6c06a671fc3b99 ARCH.WINDOW_REVEAL W17 BLANK",
                 "W17 opening arris (T-162 -> T-314) HELD, blank"],
        unit="m2", low=8.7414, high=8.9965,
        held_reason="room-side developed hole per finish line (range 0.2551 m2 on plaster and on paint); reveals and "
                    "arris HELD unquantified",
        stays_held="plaster / paint W17 HELD BOUND; W17 reveals and arris HELD; W17 window unit unchanged (Q-76 A)",
    ),
    row(
        row_id="R05", fact="arch.A-GF-01.springing_crown", verdict="ADD_TO", target="RFI-B-A02",
        part="(name the arch)", discipline="architect",
        question=("Among the 3 arches in A02: the 1.00 m arched opening between the GF dewaneya and its wash space. The "
                  "plan draws it as an opening with overhead lines; one section draws a segmental arch in the wall "
                  "beyond the cut with no dimension. What are its springing and crown levels (or its rise) and its arch "
                  "form?"),
        citations=[("research/agents_t238/T-238_ARCHED_OPENINGS_CENSUS.md", "ARC 2422"),
                   ("research/agents_t377/HELD_CHECK_T377.csv", "A-GF-01,T-292 deduction room GF-01,HELD,3.1500"),
                   ("research/agents_t377/HELD_CHECK_T377.csv", "A-GF-01,T-292 deduction room GF-02,HELD,3.1500")],
        own_reading=["P7757.dxf: plan symbol = block 'arch120' insert 1F8 (layer 4, scale 1): a 1.00 x 0.15 m opening "
                     "whose two long sides are on layer 2 (HIDDEN, overhead); no DIMENSION within 1.8 m gives a height"],
        owner_rules_checked=["Q-32 A (windows and doors; this opening has no leaf or frame)", "Q-55 C (doors only)"],
        why_no_rule="Q-55 C is a door-height fallback and does not apply to a leafless arch (T-238); no rule gives an "
                    "arch head",
        unlocks=["plaster / paint deduction GF-01 and GF-02 faces (T-292 HELD BOUND 3.1500 m2 each; drawn candidate "
                 "2.4131 m2 per face, T-238 A6)", "GF-W26 masonry deduction (T-291) HELD",
                 "GF-W26 bed-joint mesh k 1 .. 6 (T-355) HELD", "reveals T-313 / T-340 HELD", "tile edge (T-368) HELD"],
        unit="m2", low=None, high=3.15,
        held_reason="deduction per face HELD with upper bound 3.15; masonry, mesh and reveals HELD unquantified",
        stays_held="every A-GF-01 edge and deduction item HELD (R-T377-2); the candidate outline stays a candidate",
    ),
    row(
        row_id="R06", fact="arch.A-1F-01.springing_crown", verdict="ADD_TO", target="RFI-B-A02",
        part="(name the arch)", discipline="architect",
        question=("Among the 3 arches in A02: the 1.00 m arched opening on 1F between the master bed room and the "
                  "unlabelled space asked in A08. It is drawn on the plan only (overhead lines); no elevation or section "
                  "draws it. What are its springing and crown levels and its arch form? (Send with A08.)"),
        citations=[("research/agents_t238/CENSUS_T238.csv", "A-1F-01,OPENING,1F,arch (no leaf),NOT_DRAWN"),
                   ("research/agents_t377/HELD_CHECK_T377.csv", "A-1F-01,T-292 deduction room 1F-10,HELD,3.3500")],
        own_reading=["P7757.dxf: plan symbol = block 'arch120' insert BEC (layer 4, rotation 90, mirrored): the same "
                     "1.00 x 0.15 m symbol with overhead long sides; no DIMENSION within 1.8 m gives a height"],
        owner_rules_checked=["Q-32 A", "Q-55 C (doors only)"],
        why_no_rule="as R05; the head is drawn on no view",
        unlocks=["plaster / paint deduction 1F-10 face (T-292 HELD BOUND 3.3500 m2); the other face (A08 space) UNKNOWN",
                 "1F-W16 masonry deduction (T-291) HELD", "1F-W16 bed-joint mesh k 1 .. 6 (T-355) HELD",
                 "reveals T-313 / T-340 UNKNOWN"],
        unit="m2", low=None, high=3.35,
        held_reason="deduction on the 1F-10 face HELD with upper bound 3.35; the rest HELD unquantified",
        stays_held="every A-1F-01 edge and deduction item HELD (R-T377-2); floor strip 0.15 m2 unaffected (width only)",
    ),
    row(
        row_id="R07", fact="opening.GF-14_open_side_overhead_element", verdict="ADD_TO", target="RFI-B-A10",
        part="(c)", discipline="architect (structural to confirm no beam)",
        question=("GF plan, the 1.256 m open side between the wash lobby by the core W.Cs and the lift lobby: a pair of "
                  "hidden (overhead) lines 0.15 m apart is drawn across it in the plane of the wall; the GF roof slab "
                  "plan draws no beam there and no section cuts it. What is the element (a block header over the "
                  "opening, a bulkhead, other) and at what level is its underside?"),
        citations=[("research/agents_t368/T-368_EXPOSED_TILE_EDGES.md", "OVERHEAD_ELEMENT_HEAD_NOT_ESTABLISHED"),
                   ("research/agents_t368/T-368_EXPOSED_TILE_EDGES.md", "2DB / 2DC"),
                   ("research/agents_t368/EDGE_LEDGER_T368.csv", "GF-14#OS1#HEAD")],
        own_reading=["P7757.dxf: LINEs 2DB and 2DC on layer 2 (linetype HIDDEN), 0.150 apart, between wall face 222 "
                     "and wall end BC; within 1.8 m no DIMENSION or level text gives a head"],
        owner_rules_checked=["Q-55 C (door height: not a door)", "Q-48 A (tile top 3.65 m)"],
        why_no_rule="Q-55 C is a door fallback; no owner rule gives the head of a passage (T-368 r2 s.0 point 4)",
        unlocks=["GF-14#WEND and GF-14#FSTOP tile edges, head .. 3.65 m.l each (upper 7.30 m.l)",
                 "GF-14#OS1#HEAD head arris 0 .. 1.256 m.l",
                 "header face tile 1.256 x (3.65 - head) m2 on wall-tile line L-fa408571a8adcfaf1a1f (BLOCKED_RFI)"],
        unit="m.l", low=0.0, high=8.556,
        held_reason="edges and arris together 0 .. 8.556 m.l (7.30 + 1.256); header tile m2 HELD unquantified",
        stays_held="GF-14 open-side edges, arris and header face HELD by name; whether a blockwork ledger carries the "
                   "header is a Lead check, not part of the question",
    ),
]

# items the task named that are NOT filed as their own row, with the reason
NOT_FILED = [
    ("UNK-GF-01 waterproofing", "0 m2 either way (T-369 s.3): only the fixture identity is asked (R02)"),
    ("W17 head above the beam soffit", "already RFI-B-A04 (conflict): R04 adds the soffit fact as A04 (b), one reply"),
    ("W17 window m2", "owner rule Q-76 A (9.870 m2 on the opening line): not an RFI"),
    ("shower tanking height", "owner rule Q-40 A with Q-48 A: not an RFI"),
    ("A-GF-01 / A-1F-01 as new questions", "same fact as RFI-B-A02 'arch rise of ... 3 arches' (D-45): named inside "
     "A02, never asked twice"),
    ("P-GF-01 / P-1F-01 heads", "different openings (0.90 m in GF-W14 / 1F): P-1F-01 already in RFI-B-A10; not this task"),
]


# ------------------------------------------------------------------------------------------------ validation
class RowError(ValueError):
    pass


def _text_fields(r):
    for k in ("question", "why_no_rule", "held_reason", "stays_held"):
        yield r.get(k, "")
    yield from r.get("own_reading", [])
    yield from r.get("unlocks", [])


def validate(rows, rfi_ids=RFI_IDS, root=ROOT, client_terms=()):
    seen = {}
    new_ids = {}
    for r in rows:
        rid = r.get("row_id", "?")
        if r.get("verdict") not in VERDICTS:
            raise RowError(f"{rid}: verdict {r.get('verdict')!r}")
        if r["fact"] in OWNER_SETTLED:
            raise RowError(f"{rid}: fact settled by owner rule {OWNER_SETTLED[r['fact']]}")
        if r["fact"] in seen:
            raise RowError(f"{rid}: same fact as {seen[r['fact']]} ({r['fact']})")
        seen[r["fact"]] = rid
        tgt = r.get("target", "")
        if r["verdict"] == "ADD_TO" and tgt not in rfi_ids:
            raise RowError(f"{rid}: ADD_TO an RFI that is in no RFI file: {tgt}")
        if r["verdict"] == "NEW":
            if tgt in rfi_ids:
                raise RowError(f"{rid}: NEW id already exists: {tgt}")
            parts = new_ids.setdefault(tgt, set())
            if r.get("part") in parts:
                raise RowError(f"{rid}: part {r.get('part')} of {tgt} twice")
            parts.add(r.get("part"))
        cites = r.get("citations") or []
        if not cites:
            raise RowError(f"{rid}: no citation")
        for path, token in cites:
            f = Path(root) / path
            if not f.is_file():
                raise RowError(f"{rid}: cited file missing {path}")
            if token not in f.read_text(encoding="utf-8"):
                raise RowError(f"{rid}: citation {token!r} not in {path}")
        if not r.get("owner_rules_checked"):
            raise RowError(f"{rid}: no owner rule search recorded")
        if r.get("unit") not in UNITS:
            raise RowError(f"{rid}: unit {r.get('unit')!r}")
        lo, hi = r.get("low"), r.get("high")
        if lo is None and hi is None:
            if not r.get("held_reason"):
                raise RowError(f"{rid}: HELD unquantified without a reason")
        else:
            if hi is None or hi == 0:
                raise RowError(f"{rid}: governed range has no positive upper value (HELD is never 0)")
            if lo is not None and lo > hi:
                raise RowError(f"{rid}: low > high")
        if not r.get("unlocks"):
            raise RowError(f"{rid}: unlocks nothing")
        for t in _text_fields(r):
            if ARABIC.search(t):
                raise RowError(f"{rid}: Arabic script in a public text")
            for c in client_terms:
                if c and c.lower() in t.lower():
                    raise RowError(f"{rid}: client term in a public text")
    return True


def governed(r):
    lo, hi = r.get("low"), r.get("high")
    if lo is None and hi is None:
        return f"HELD unquantified ({r['held_reason']})"
    return f"{'' if lo is None else f'{lo:g}'} .. {hi:g} {r['unit']}"


def to_csv(rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["row", "verdict", "target", "part", "fact", "discipline", "unit", "low", "high", "governs",
                "unlocks", "citations", "owner_rules_checked", "stays_held"])
    for r in rows:
        w.writerow([r["row_id"], r["verdict"], r["target"], r["part"], r["fact"], r["discipline"], r["unit"],
                    "" if r["low"] is None else r["low"], "" if r["high"] is None else r["high"], governed(r),
                    " | ".join(r["unlocks"]), " | ".join(f"{p} :: {t}" for p, t in r["citations"]),
                    " | ".join(r["owner_rules_checked"]), r["stays_held"]])
    return buf.getvalue()


def summary(rows):
    return {
        "method": METHOD,
        "rows": len(rows),
        "new": sorted({r["target"] for r in rows if r["verdict"] == "NEW"}),
        "added_to": sorted({r["target"] for r in rows if r["verdict"] == "ADD_TO"}),
        "not_filed": [n for n, _ in NOT_FILED],
        "candidate_lines_changed": 0,
        "quantities_computed": 0,
        "sent": False,
    }


def main(argv):
    validate(ROWS)
    out = {"T381_RFI_ROWS.csv": to_csv(ROWS),
           "T381_SUMMARY.json": json.dumps(summary(ROWS), indent=2, sort_keys=True) + "\n"}
    if "--check" in argv:
        bad = [n for n, s in out.items() if (HERE / n).read_text(encoding="utf-8") != s]
        print("check:", "OK" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    for n, s in out.items():
        (HERE / n).write_text(s, encoding="utf-8")
    print(f"{METHOD}: {len(ROWS)} rows written")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
