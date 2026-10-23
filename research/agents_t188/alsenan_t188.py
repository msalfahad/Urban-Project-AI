"""T-188: element inventory across disciplines + storey continuity (R2 + R3) on the development villa, three BOQ states.

    python3 -I research/agents_t188/alsenan_t188.py [--write]      (prints the summary; --write rewrites the committed
                                                                     FINDINGS_T188.csv and summary.json beside this file)

The inventory is built from merged, checker-verdict-cited ledgers (WORKFLOW_CONTROLS s.10 rule 5: source references
reused with their citation, never another agent's quantity as proof) plus this run's own reads of "ST7757 dxf.dxf"
(Drive "Alsenan chalet project", sha 9f9d1179; private copy in .work/private, never committed). Nothing here is a
quantity: line ids are cited so a reviewer can find each line; their figures stay in the ledgers.

BOQ states (the lines that exist for these elements in each):
  A     released ARCH_TAKEOFF_V2.9 + route G (baseline A of T-184 s.5 / T-186)
  V305  opt-in candidate V3.0.5 (76d75bde, T-179 r2; lines as listed by T-187 s.3)
  V306  opt-in candidate V3.0.6 (3e622799, T-187 MERGED 8a6d604a; Gate B verdict 06:24)
Line ids with a route G / ledger prefix (P-C:, HL:, DG5:) are the engine keys the ledgers print; the others (POOL:,
DOME:, STAIR:, A:) are descriptors of a line the ledgers cite by item, floor and figure only (key not printed there).
Freelancer rows: row ids of research/agents_t196/ROWS_T196.csv (T-196 MERGED f933ef8a), never a cell text.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine.source import element_continuity_v1 as M  # noqa: E402

STOREYS = ["FDN", "GF", "1F", "2F", "ROOF"]
SEARCH_ST = "ST7757 all 16 pages (T-184 / T-185 / T-166 searches; own text search of ST7757 dxf.dxf this run)"
SEARCH_AR = "P7757 GF / 1F / 2F plans, elevations, sections A-A / B-B (T-184 / T-185)"
P16 = "ST p.16 TYPICAL STEEL LAYOUT - STAIR SECTION (N.T.S.): no printed level or dimension fits any stair (T-184 s.3)"


def pr(storey, disc, ref, what="DRAWN"):
    return {"storey": storey, "discipline": disc, "ref": ref, "what": what}


ELEMENTS = [
    {"id": "ST-01", "kind": "STAIR", "place": "dog-leg in the 2.50 m shaft beside the lift",
     "occupies": ["GF", "1F"], "occupies_ref": "section A-A (sheet10): +1.00 -> landing +3.50 -> +5.50 -> landing -> "
                                                "+9.70 (T-184 s.2, MERGED 924c2bd)",
     "presence": [pr("GF", "ARCH", "ARCH GF plan sheet03"), pr("GF", "STRUCT", "ST p.4 GF roof slab (stair zone)"),
                  pr("1F", "ARCH", "ARCH 1F plan sheet04"),
                  pr("1F", "STRUCT", "ST p.5 1F roof slab: riser lines x 18.57 .. 21.07 (checker 06:24 own read)"),
                  pr("2F", "ARCH", "ARCH 2F plan (pages 05-06): 1F -> 2F flights seen through the opening (T-111)",
                     "SEEN_BELOW")],
     "searched": {"ARCH": SEARCH_AR, "STRUCT": SEARCH_ST},
     "detail": {"state": "TYPICAL", "ref": P16},
     "ends": {"ref": "2F plan draws no flight leaving +9.70; ST p.6 slab panels cover the shaft (T-184 s.2)"}},
    {"id": "ST-01b", "kind": "STAIR", "place": "lobby flight D1 under the ST-01 half landing",
     "occupies": ["GF"], "occupies_ref": "section A-A +0.30 -> +1.00 (T-184 s.2)",
     "presence": [pr("GF", "ARCH", "ARCH GF plan sheet03: 4 solid riser lines"),
                  pr("GF", "STRUCT", "ST p.3 '+0.30' in the shaft")],
     "searched": {"ARCH": SEARCH_AR, "STRUCT": SEARCH_ST}, "detail": {"state": "TYPICAL", "ref": P16},
     "ends": {"ref": "one flight +0.30 -> +1.00 (section A-A)"}},
    {"id": "ST-02", "kind": "STAIR", "place": "round reception stair wrapped round the void",
     "occupies": ["GF"], "occupies_ref": "GF +1.00 -> +2.929 -> +4.696 -> 1F +5.50 (T-184 s.2)",
     "presence": [pr("GF", "ARCH", "ARCH GF plan sheet03"),
                  pr("GF", "STRUCT", "ST p.4 arcs and lines at the stair (finding CC-13011ac02f)"),
                  pr("1F", "ARCH", "ARCH 1F plan sheet04: the short flight arrives at +5.50", "ARRIVAL")],
     "searched": {"ARCH": SEARCH_AR, "STRUCT": SEARCH_ST}, "detail": {"state": "TYPICAL", "ref": P16},
     "ends": {"ref": "1F plan: nothing leaves +5.50; ST p.5 slab panels and the 2F plan draw no stair there "
                     "(T-184 s.2)"}},
    {"id": "ST-03", "kind": "STAIR", "place": "outside entrance stair E1, court to GF",
     "occupies": ["GF"], "occupies_ref": "+0.15 -> +1.00 (T-184 s.2)",
     "presence": [pr("GF", "ARCH", "ARCH GF plan (P7757 DXF): 5 riser lines 2.800 m"),
                  pr("GF", "STRUCT", "ST p.3: 4 riser lines, no slab panel")],
     "searched": {"ARCH": SEARCH_AR, "STRUCT": SEARCH_ST}, "detail": {"state": "TYPICAL", "ref": P16},
     "ends": {"ref": "one run +0.15 -> +1.00"}},
    {"id": "LIFT-01", "kind": "LIFT", "place": "lift box 1.80 x 1.80 inside, east of the ST-01 shaft",
     "occupies": ["FDN", "GF", "1F", "2F"],
     "occupies_ref": "FF lift base under the box + a shaft opening on GF / 1F / 2F (S8.6 opening census)",
     "presence": [pr("FDN", "STRUCT", "ST foundation plan: FF combined footing under C1 / C2 / C2 / C9 (text 1676, "
                                     "own read this run); schedule remark 'lift base' (pre-S8 PS8-LIFT-WALLS)"),
                  pr("GF", "ARCH", "ARCH GF plan: shaft opening OP-GF-023 (S8.6 census)"),
                  pr("GF", "STRUCT", "ST p.4 lift box B14 / B7 / B1 (T-184 s.2)"),
                  pr("1F", "ARCH", "ARCH 1F plan: shaft opening OP-1F-012 (S8.6 census)"),
                  pr("1F", "STRUCT", "ST p.5 lift box (T-184 s.2)"),
                  pr("2F", "ARCH", "ARCH 2F plan: shaft opening OP-2F-005 (S8.6 census)")],
     "searched": {"ARCH": SEARCH_AR, "STRUCT": SEARCH_ST},
     "components": [{"name": "PIT", "state": "HELD",
                     "ref": "ground slab lift-pit opening 3.24 m2 (S8.1A-RG-04) over the FF lift base",
                     "note": "pit depth, pit walls and pit base level not printed (pre-S8 LIFT_PIT_AND_WALLS "
                             "BLOCKED_NEEDS_AUTHORITY; FF legs drawn, not dimensioned: ELEMENT_REGISTER)"}]},
    {"id": "POOL-01", "kind": "POOL", "place": "GF pool court",
     "presence": [pr("GF", "ARCH", "ARCH GF plan sheet03"), pr("GF", "STRUCT", "ST p.7 DETAIL OF SWIMMING POOL")],
     "searched": {"ARCH": SEARCH_AR, "STRUCT": SEARCH_ST},
     "detail": {"state": "PROJECT", "ref": "ST p.7 DETAIL OF SWIMMING POOL (T-183 r2, MERGED 6380294)"},
     "components": [{"name": "BASE", "state": "DRAWN", "ref": "ST p.7 0.40 m base (checker VERIFIED 4.374 m3)"},
                    {"name": "WALLS", "state": "DRAWN", "ref": "ST p.7 + NW cut, 1.20 m to the structure line "
                                                           "(checker VERIFIED 2.828 m3)"},
                    {"name": "STEPS", "state": "NOT_DRAWN", "ref": "GF plan, ST p.7, sections (owner 2026-10-22 16:45)",
                     "note": "consultant item: access ladder or steps"}]},
    {"id": "DOME-A", "kind": "DOME", "place": "west terrace dome on the +9.70 roof",
     "presence": [pr("2F", "STRUCT", "ST p.5 centre 16.380 / 41.651, in-bay ring arcs 5FE / 5FF (checker 06:24)"),
                  pr("2F", "ARCH", "ARCH 2F plan circle r 2211.1 (T-185)")],
     "searched": {"ARCH": SEARCH_AR, "STRUCT": SEARCH_ST},
     "detail": {"state": "PROJECT", "ref": "ST p.7 DETAIL OF DOME 442 / 190 / 10 (T-185, MERGED 94e39ee6)"}},
    {"id": "DOME-B", "kind": "DOME", "place": "east terrace dome on the +9.70 roof",
     "presence": [pr("2F", "STRUCT", "ST p.5 centre 30.828 / 41.651, closed circle 649 (checker 06:24)"),
                  pr("2F", "ARCH", "ARCH 2F plan circle r 2211.1 (T-185)")],
     "searched": {"ARCH": SEARCH_AR, "STRUCT": SEARCH_ST},
     "detail": {"state": "PROJECT", "ref": "ST p.7 DETAIL OF DOME (T-185)"}},
    {"id": "DOME-TOWER", "kind": "DOME", "place": "tower cap over the 2F maid room",
     "presence": [pr("ROOF", "ARCH", "ARCH SE elevation 441 / 215 / 193 (T-185)")],
     "searched": {"ARCH": SEARCH_AR,
                  "STRUCT": "ST p.6 +13.90 slab flat, no opening, no ring; p.7 / p.14-16 no tower dome (T-185 s.2)"},
     "detail": {"state": "NONE", "ref": "ST7757 p.7 draws only the terrace dome detail (T-185)"}},
    {"id": "TANK-01", "kind": "TANK", "place": "on the 2F roof slab +13.90",
     "presence": [pr("ROOF", "STRUCT", "ST p.6 'WATER TANK PLACE' (text 1A85, own read) over two T&B panels "
                                      "2F-011 / 2F-013 (T-152)")],
     "searched": {"STRUCT": SEARCH_ST},
     "detail": {"state": "NONE", "ref": "p.7, p.14, p.15, p.16 searched: no tank wall, base, opening or member "
                                        "(T-166 s.4)"}},
] + [
    # the two voids in the 1F floor (own read this run). The architectural set prints exactly two 'VOID' labels, both on
    # the 1st FLOOR PLAN; the structural set prints exactly two, both in the GROUND FLOOR ROOF SLAB frame (= the 1F
    # floor). The pair is 7.745 / 6.369 m apart in the architecture and 7.744 / 6.369 m in the structure: one
    # translation maps both, i.e. both disciplines draw the same two openings. Neither set prints 'VOID' on the 2F plan
    # or the 1F roof slab: the voids end at 1F (label search of both sets; the slab panels above are T-139's).
    {"id": f"VOID-1F-{k}", "kind": "VOID", "place": f"1F floor opening {k} (near the master bedroom labels)",
     "occupies": ["1F"], "occupies_ref": "1F plan level +5.50 beside the label; GF roof slab sheet",
     "presence": [pr("1F", "ARCH", f"ARCH 1st.FLOOR PLAN 'VOID' label {k} (P7757.dxf ab54dd55, layer 5)"),
                  pr("1F", "STRUCT", f"ST GROUND FLOOR ROOF SLAB 'VOID' label {k} (ST7757 dxf.dxf, layer 5)")],
     "searched": {"ARCH": "P7757.dxf text search: 2 'VOID' labels, both on the 1F plan",
                  "STRUCT": "ST7757 dxf.dxf text search: 2 'VOID' labels, both on the GF roof slab"},
     "ends": {"ref": "no 'VOID' on the 2F plan or the 1F roof slab sheet (text search of both sets)"}}
    for k in ("a", "b")]

# lines per BOQ state. 'storey' is the storey of this inventory (route G prints GROUND for GF on some lines; the
# engine label is kept in ref).
_A = [
    {"line_id": "P-C:SCOPE:STAIRS:GF:CC-7390ea1139:FLIGHTS", "kind": "STAIR", "storey": "GF", "trade": "STRUCTURE",
     "state": "PROVISIONAL", "element": "ST-01", "ref": "ST-01 GF -> 1F flights (T-184 s.5; T-187 s.3)"},
    {"line_id": "A:STAIRS:GROUND:ST-02-winder-region", "kind": "STAIR", "storey": "GF", "trade": "STRUCTURE",
     "state": "PROVISIONAL", "element": "ST-02",
     "ref": "baseline A: an 8.37 m2 winder region on the ground-beam plan (T-184 s.5; engine label GROUND)"},
    {"line_id": "STAIR:ST-03:E1", "kind": "STAIR", "storey": "GF", "trade": "STRUCTURE", "state": "PROVISIONAL",
     "element": "ST-03", "ref": "entrance stair line (T-184 s.5; unchanged to V3.0.6, T-187 verdict)"},
    {"line_id": "POOL:GROUND:FLOOR", "kind": "POOL", "storey": "GF", "trade": "STRUCTURE", "state": "PROVISIONAL",
     "element": "POOL-01", "ref": "pool floor convention 0.25 m (T-186 / T-187 s.3)"},
    {"line_id": "POOL:GROUND:WALLS", "kind": "POOL", "storey": "GF", "trade": "STRUCTURE", "state": "PROVISIONAL",
     "element": "POOL-01", "ref": "pool walls convention 1.60 m (T-186 / T-187 s.3)"},
    {"line_id": "DOME:2F:CC-6e7b8c8d1f", "kind": "DOME", "storey": "2F", "trade": "STRUCTURE", "state": "PROVISIONAL",
     "element_any": ["DOME-A", "DOME-B"], "ref": "convention shell (T-185 / T-187 s.3)"},
    {"line_id": "DOME:2F:CC-a0729cfebc", "kind": "DOME", "storey": "2F", "trade": "STRUCTURE", "state": "PROVISIONAL",
     "element_any": ["DOME-A", "DOME-B"], "ref": "convention shell (T-185 / T-187 s.3)"},
]


def _blocked(lines, ids):
    return [dict(ln, state="BLOCKED_RFI") if ln["line_id"] in ids else dict(ln) for ln in lines]


_MISREAD = {"line_id": "P-C:STAIRS:1F:SITE-b845e1e78b1f74a8", "kind": "STAIR", "storey": "1F", "trade": "STRUCTURE",
            "element": "DOME-A",
            "ref": "route face on SH04: 18 lines from one point to r 2.211 m over 360 deg = DOME-A (checker 06:24)"}
_V305 = [dict(ln) for ln in _A if ln["line_id"] != "A:STAIRS:GROUND:ST-02-winder-region"] + [
    {"line_id": "P-C:STAIRS:GROUND:SITE-4df8", "kind": "STAIR", "storey": "GF", "trade": "STRUCTURE",
     "state": "PROVISIONAL", "element": "ST-02", "ref": "ST-02 on the candidate's own zone (T-187 s.3, key truncated "
                                                         "there; engine label GROUND)"},
    dict(_MISREAD, state="PROVISIONAL")]
_V306 = _blocked(_V305, {"P-C:SCOPE:STAIRS:GF:CC-7390ea1139:FLIGHTS", "P-C:STAIRS:GROUND:SITE-4df8",
                         "POOL:GROUND:FLOOR", "POOL:GROUND:WALLS", "DOME:2F:CC-6e7b8c8d1f", "DOME:2F:CC-a0729cfebc",
                         "P-C:STAIRS:1F:SITE-b845e1e78b1f74a8"}) + [
    {"line_id": f"HL:STAIR_CONCRETE:ST-01:{k}", "kind": "STAIR", "storey": "1F", "trade": "STRUCTURE", "state": s,
     "element": "ST-01", "ref": f"ST-01 1F -> 2F {k} (T-187 s.3; D-T184-1 fixed)"}
    for k, s in (("MS2_L", "VERIFIED"), ("MS2_U", "DRAWING-CONFIRMED"), ("MS2_LD", "HELD"), ("MS2_TR", "UNKNOWN"))] + [
    {"line_id": "DG5:ST-01:LOBBY", "kind": "STAIR", "storey": "GF", "trade": "STRUCTURE", "state": "UNKNOWN",
     "element": "ST-01b", "ref": "placeholder: lobby flight D1 drawn, carried by no line (T-187 s.3)"},
    {"line_id": "DG5:DOME-3:SHELL", "kind": "DOME", "storey": "ROOF", "trade": "STRUCTURE", "state": "UNKNOWN",
     "element": "DOME-TOWER", "ref": "placeholder: third dome (Q-27 A) carried by no line (T-187 s.3)"}]
STATES = {"A": _A, "V305": _V305, "V306": _V306}

REFERENCE_ROWS = [
    {"row_id": "RC:S16:11", "kind": "STAIR", "element": "ST-03"},
    {"row_id": "RC:S16:12", "kind": "STAIR", "element": "ST-02"},
    {"row_id": "RC:S16:13", "kind": "DOME", "element": "DOME-TOWER", "component": "3 domes aggregate (A, B, tower)"},
    {"row_id": "RC:S16:20", "kind": "STAIR", "element": "ST-01", "component": "flights, both storeys"},
    {"row_id": "RC:S16:21", "kind": "STAIR", "element": "ST-01", "component": "landings"},
    {"row_id": "RC:S17:11", "kind": "POOL", "element": "POOL-01", "component": "base"},
    {"row_id": "RC:S17:12", "kind": "POOL", "element": "POOL-01", "component": "walls"},
    {"row_id": "RC:S17:13", "kind": "POOL", "element": None, "component": "pump room walls",
     "ref": "T-183 item K: pump room / balance tank in no document read"},
    {"row_id": "RC:S17:14", "kind": "POOL", "element": "POOL-01", "component": "steps (NOT DRAWN, consultant item)"},
    {"row_id": "RC:S17:15", "kind": "POOL", "element": None, "component": "pump room floor",
     "ref": "T-183 item K: pump room / balance tank in no document read"},
    {"row_id": "RC:S13:11", "kind": "LIFT", "element": "LIFT-01", "component": "lift walls"},
]


def project(state):
    return {"storeys": list(STOREYS), "elements": json.loads(json.dumps(ELEMENTS)),
            "lines": json.loads(json.dumps(STATES[state])), "reference_rows": json.loads(json.dumps(REFERENCE_ROWS))}


def run():
    return {s: M.check(project(s)) for s in STATES}


def findings_csv(res):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["state", "review", "code", "status", "element", "kind", "storey", "lines", "why"])
    for s, r in res.items():
        for f in r["findings"]:
            w.writerow([s, f["review"], f["code"], f["status"], f["element"] or "", f["kind"] or "", f["storey"] or "",
                        " ".join(f["lines"]), f["why"]])
    return buf.getvalue()


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    res = run()
    summ = {s: r["summary"] for s, r in res.items()}
    if "--write" in argv:
        (HERE / "FINDINGS_T188.csv").write_text(findings_csv(res), encoding="utf-8")
        (HERE / "summary.json").write_text(json.dumps(summ, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summ, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
