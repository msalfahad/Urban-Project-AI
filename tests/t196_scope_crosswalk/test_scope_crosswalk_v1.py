"""T-196: scope crosswalk v1 (engine.source.scope_crosswalk_v1) on a synthetic villa (not a client drawing).

Hand expectations (villa "synthetic-villa-t196"):
ELEMENTS (11): from the element register v0 run: GF rooms KITCHEN and BEDROOM (printed labels), footings F1 @ x 2000 and
  F1 @ x 12000 (-> F1.1 west, F1.2 east), F2, column C1 GF; from ledgers: POOL-01 (pool shell), SLAB-1F (1F slab),
  LANDING-1F (the 1F arrival landing, the register ruling gives it to the FLOOR SLAB), RL-01 (a drawn roof railing).
LINES (10): porcelain KITCHEN 12.0 m2, porcelain BEDROOM 9.0 m2, footings 0.9 / 0.9 / 1.2 m3, column C1 0.4 m3, pool
  concrete 7.2 m3 (ledger link), 1F slab 19.2 m3 (ledger link), one facade line (later kind: UNLINKED with the
  register's reason) and one ceiling line 30.0 m2 (UNLINKED: names no element).
  -> LINKED 8, UNLINKED 2.
REFERENCE ROWS (10 DETAIL + 1 SUBTOTAL, the subtotal is not crosswalked):
  R01 kitchen floor -> KITCHEN                                  DRAWN
  R02 footing type F1 -> both F1 footings                       AGGREGATE (2 elements, one row)
  R03 footing F2 and R04 footing F2 again (same component)      DRAWN + DRAWN -> one DUPLICATE_ROW finding
  R05 pool floor, R06 pool walls (two components of POOL-01)    DRAWN + DRAWN, NOT a duplicate; POOL-01 counted once
  R07 pump room 3.48 m3, searched on the plan and the details   NOT_DRAWN -> NOT_DRAWN_SCOPE m3 3.48
  R08 column C1 GF                                               DRAWN
  R09 a row with no map entry                                    NOT_MAPPED (listed, never guessed)
  R10 a row mapped to an element id that does not exist         SCOPE_UNKNOWN (MAP_MISS)
  ROWS: DRAWN 6, AGGREGATE 1, NOT_DRAWN 1, NOT_MAPPED 1, SCOPE_UNKNOWN 1 = 10 (all accounted).
ELEMENTS REVERSE: HAS_LINE 8 (KITCHEN, BEDROOM, F1.1, F1.2, F2, C1, POOL-01, SLAB-1F), CARRIED_BY_RULING 1 (LANDING-1F
  by SLAB-1F), MISSING_LINE 1 (RL-01: drawn, no line in any trade).
DOCUMENTS: reflected ceiling plan NOT_IN_SET -> NOT_ISSUED designer item listing the ceiling line and the ceiling row,
  quantity UNKNOWN (never 0); the floor plan PRESENT -> nothing.
ADVERSE: mirrored plan (x -> -x) gives the same statuses and findings (labels, not coordinates, carry the ids); a
  ruling whose carrier has no line leaves the element MISSING_LINE with a finding; NOT_DRAWN without the sheets
  searched is refused; a row map naming an unknown row is refused; a held line keeps measured_net None.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import boq_line as BL  # noqa: E402
from engine.source import element_register_v0 as E  # noqa: E402
from engine.source import scope_crosswalk_v1 as X  # noqa: E402

REV_A, REV_B = "c3" * 32, "d4" * 32
PID = "synthetic-villa-t196"


def line(code, unit, element_id, *, floor=None, room_id=None, ev="PROVISIONAL", net=1.0, rev=REV_A):
    kw = {}
    if ev == "BOUNDED_EXPOSURE":
        kw = {"bounded_range": {"low": 0.3, "high": 0.5, "basis": "test"}, "rfi": {"question": "height?"}}
        net = None
    return BL.make_line(project_id=PID, revision_set_sha256=rev, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=element_id, floor=floor, room_id=room_id, formula="test",
                        rule_id="T196", rule_version="test", item_en=code, item_ar=code,
                        trade=None if code in BL.ITEMS else "OTHER", **kw)


def villa(sx=1.0):
    """register sources + lines; sx = -1 mirrors the plan (x -> -x) in metres and drawing units."""
    def poly(x0, y0, x1, y1):
        return [[sx * x0, y0], [sx * x1, y0], [sx * x1, y1], [sx * x0, y1]]
    rooms = [{"room_id": "GF-K", "floor": "GF", "codes": ["KITCHEN"], "label_source": "TEXT", "kind": "WET",
              "polygon_m": poly(0, 0, 4, 3), "face_id": "f1", "region_id": "r", "area_m2": 12.0},
             {"room_id": "GF-B", "floor": "GF", "codes": ["BEDROOM"], "label_source": "TEXT", "kind": "DRY",
              "polygon_m": poly(4.2, 0, 7.2, 3), "face_id": "f2", "region_id": "r", "area_m2": 9.0}]
    src = {"rooms": rooms, "walls": [], "openings": [], "curved": [], "doors": [], "membrane": [], "unit_m": 0.001,
           "arch_rev": REV_A[:12]}
    xa, xb = int(sx * 2000), int(sx * 12000)
    S = dict(rev=REV_B)
    lines = [
        line("FIN.FLOOR.PORCELAIN", "m2", "GF-K:floor", floor="GF", room_id="GF-K", net=12.0),
        line("FIN.FLOOR.PORCELAIN", "m2", "GF-B:floor", floor="GF", room_id="GF-B", net=9.0),
        line("STR.CONC.FOOTING", "m3", f"P-C:FTG:SH1:F1@{xa},1000:aa", floor="FOUNDATION", net=0.9, **S),
        line("STR.CONC.FOOTING", "m3", f"P-C:FTG:SH1:F1@{xb},1000:bb", floor="FOUNDATION", net=0.9, **S),
        line("STR.CONC.FOOTING", "m3", f"P-C:FTG:SH1:F2@{int(sx * 9000)},1000:cc", floor="FOUNDATION", net=1.2, **S),
        line("STR.CONC.COLUMN", "m3", f"U-C:COL:SH2:C1@{int(sx * 1000)},1000|GF", floor="GF", net=0.4, **S),
        line("STR.CONC.POOL", "m3", "P-C:SCOPE:POOL:shell", floor="GF", net=7.2, **S),
        line("STR.CONC.SLAB", "m3", "LEDGER:SLAB-1F", floor="1F", net=19.2, **S),
        line("ARCH.FACADE", "m2", "GF-FACADE:facade", floor="GF", room_id="GF-FACADE", net=80.0),
        line("FIN.CEILING", "m2", "XX-NOWHERE:ceiling", floor="GF", net=30.0),
    ]
    return lines, src


EXTRA = [{"id": f"{PID}/POOL-01", "kind": "POOL", "floor": "GF", "source": "T-x pool ledger", "refs": ["ST p.7"]},
         {"id": f"{PID}/SLAB-1F", "kind": "SLAB-LEDGER", "floor": "1F", "source": "T-x slab ledger"},
         {"id": f"{PID}/LANDING-1F", "kind": "LANDING-STR", "floor": "1F", "source": "T-x stair ledger"},
         {"id": f"{PID}/RL-01", "kind": "RAILING", "floor": "ROOF", "source": "T-x railing census", "refs": ["2F plan"]}]
RULINGS = [{"element": f"{PID}/LANDING-1F", "carried_by": f"{PID}/SLAB-1F",
            "basis": "register ruling: arrival landing owned by the floor slab"}]
DOCS = [{"item": "reflected ceiling plan", "status": "NOT_IN_SET", "families": ["FIN.CEILING"], "trades": ["CEILING"]},
        {"item": "floor plan per storey", "status": "PRESENT", "families": ["FIN.FLOOR"], "trades": ["FLOOR"]}]


def rows():
    r = lambda i, t, u, q, k="DETAIL": {"row_id": f"WB:S1:{i}", "trade": t, "unit": u, "qty": q, "row_kind": k}
    return [r(1, "FLOOR", "m2", 12.4), r(2, "FOOTING", "m3", 1.8), r(3, "FOOTING", "m3", 1.2), r(4, "FOOTING", "m3", 1.2),
            r(5, "POOL", "m3", 4.32), r(6, "POOL", "m3", 4.32), r(7, "POOL", "m3", 3.48), r(8, "COLUMN", "m3", 0.4),
            r(9, "CEILING", "m2", 31.0), r(10, "FLOOR", "m2", 5.0), r(11, None, "m3", 99.0, "SUBTOTAL")]


ROW_MAP = {
    "WB:S1:1": {"select": {"kind": "ROOM", "label_base": "KITCHEN"}},
    "WB:S1:2": {"select": {"kind": "FTG", "label_base": "F1"}},
    "WB:S1:3": {"select": {"kind": "FTG", "label_base": "F2"}},
    "WB:S1:4": {"select": {"kind": "FTG", "label_base": "F2"}},
    "WB:S1:5": {"elements": [{"id": f"{PID}/POOL-01", "component": "base"}]},
    "WB:S1:6": {"elements": [{"id": f"{PID}/POOL-01", "component": "walls"}]},
    "WB:S1:7": {"status": "NOT_DRAWN", "searched": ["GF plan", "pool detail ST p.7", "sections"],
                "basis": "pump room on no sheet"},
    "WB:S1:8": {"select": {"kind": "COL", "label_base": "C1", "floor": "GF"}},
    "WB:S1:10": {"elements": [f"{PID}/NO-SUCH-ROOM"]},
}


def run(sx=1.0, rulings=RULINGS, row_map=ROW_MAP):
    lines, src = villa(sx)
    reg = E.build(lines, src, project=PID)
    links, reasons = X.register_links(reg)
    by_key = {ln["location"]["element_id"]: ln["line_id"] for ln in lines}
    links[by_key["P-C:SCOPE:POOL:shell"]] = [f"{PID}/POOL-01"]
    links[by_key["LEDGER:SLAB-1F"]] = [f"{PID}/SLAB-1F"]
    for k in ("P-C:SCOPE:POOL:shell", "LEDGER:SLAB-1F"):
        reasons.pop(by_key[k], None)
    els = X.build_elements(reg, EXTRA)
    return X.crosswalk(els, rows(), row_map, lines, links, rulings, DOCS, reasons), reg, lines


def st(rep, kind, key="id"):
    return {(r.get(key) or r.get("row_id")).split("/")[-1]: r["status"] for r in rep[kind]}


def test_rows_lines_elements_hand_counts():
    rep, reg, lines = run()
    s = rep["summary"]
    assert s["rows"] == {"DRAWN": 6, "AGGREGATE": 1, "NOT_DRAWN": 1, "NOT_MAPPED": 1, "SCOPE_UNKNOWN": 1}
    assert s["all_rows_accounted"] and len(rep["rows"]) == 10               # the subtotal is not a scope row
    assert s["lines"] == {"LINKED": 8, "UNLINKED": 2}
    assert s["elements"] == {"HAS_LINE": 8, "CARRIED_BY_RULING": 1, "MISSING_LINE": 1}
    rows_st = {r["row_id"]: r for r in rep["rows"]}
    agg = rows_st["WB:S1:2"]
    assert agg["status"] == "AGGREGATE" and [e.split("/")[-1] for e in agg["elements"]] == ["F1.1", "F1.2"]
    assert rows_st["WB:S1:10"]["status"] == "SCOPE_UNKNOWN" and rows_st["WB:S1:10"]["reason"].startswith("MAP_MISS")
    assert rows_st["WB:S1:9"]["status"] == "NOT_MAPPED"
    el = {e["id"].split("/")[-1]: e for e in rep["elements"]}
    assert el["RL-01"]["status"] == "MISSING_LINE" and el["RL-01"]["lines"] == []
    assert el["LANDING-1F"]["status"] == "CARRIED_BY_RULING" and el["LANDING-1F"]["carried_by"].endswith("SLAB-1F")
    assert el["POOL-01"]["reference_rows"] == ["WB:S1:5", "WB:S1:6"]        # two components, one element
    un = {ln["element_key"]: ln for ln in rep["lines"] if ln["status"] == "UNLINKED"}
    assert set(un) == {"GF-FACADE:facade", "XX-NOWHERE:ceiling"}
    assert "later kind" in un["GF-FACADE:facade"]["reason"]


def test_findings_duplicate_not_drawn_and_not_issued():
    rep, _reg, lines = run()
    f = rep["findings"]
    dup = [x for x in f if x["finding"] == "DUPLICATE_ROW"]
    assert len(dup) == 1 and dup[0]["rows"] == ["WB:S1:3", "WB:S1:4"] and len(dup[0]["elements"]) == 1
    assert dup[0]["elements"][0].endswith("/F2")
    assert not any(e.endswith("POOL-01") for x in dup for e in x["elements"])   # components differ: not a double count

    nd = [x for x in f if x["finding"] == "NOT_DRAWN_SCOPE"]
    assert nd == [{"finding": "NOT_DRAWN_SCOPE", "unit": "m3", "reference_qty": 3.48, "rows": ["WB:S1:7"]}]
    assert not [x for x in f if x["finding"] == "ROW_WITHOUT_LINE"]
    ni = rep["not_issued"]
    assert len(ni) == 1 and ni[0]["item"] == "reflected ceiling plan" and ni[0]["status"] == "NOT_ISSUED"
    ceil = [ln["line_id"] for ln in lines if ln["item_code"] == "FIN.CEILING"]
    assert ni[0]["candidate_lines"] == ceil and ni[0]["reference_rows"] == ["WB:S1:9"]
    assert "never 0" in ni[0]["quantity_status"]


def test_mirrored_plan_same_result():
    a, _r, _l = run()
    b, _r2, _l2 = run(sx=-1.0)
    assert a["summary"] == b["summary"]
    assert st(a, "elements") == st(b, "elements")
    assert {r["row_id"]: (r["status"], len(r["elements"])) for r in a["rows"]} == \
        {r["row_id"]: (r["status"], len(r["elements"])) for r in b["rows"]}
    strip = lambda f: [{k: v for k, v in x.items() if k != "rows" or x["finding"] != "ROW_WITHOUT_LINE"} for x in f]
    assert strip(a["findings"]) == strip(b["findings"])


def test_adverse_carrier_without_line_stays_missing():
    bad = [{"element": f"{PID}/LANDING-1F", "carried_by": f"{PID}/RL-01", "basis": "wrong carrier"}]
    rep, _r, _l = run(rulings=bad)
    el = {e["id"].split("/")[-1]: e for e in rep["elements"]}
    assert el["LANDING-1F"]["status"] == "MISSING_LINE"
    assert {"finding": "RULING_CARRIER_WITHOUT_LINE", "element": f"{PID}/LANDING-1F",
            "carried_by": f"{PID}/RL-01"} in rep["findings"]


def test_adverse_row_on_a_drawn_element_without_line():
    m = dict(ROW_MAP, **{"WB:S1:9": {"elements": [f"{PID}/RL-01"]}})
    rep, _r, _l = run(row_map=m)
    hit = [x for x in rep["findings"] if x["finding"] == "ROW_WITHOUT_LINE"]
    assert hit == [{"finding": "ROW_WITHOUT_LINE", "element": f"{PID}/RL-01", "rows": ["WB:S1:9"]}]


def test_adverse_refusals_and_held_never_zero():
    m = dict(ROW_MAP, **{"WB:S1:7": {"status": "NOT_DRAWN", "searched": []}})
    with pytest.raises(ValueError, match="searched"):
        run(row_map=m)
    with pytest.raises(ValueError, match="do not exist"):
        run(row_map=dict(ROW_MAP, **{"WB:S9:1": {"status": "SCOPE_UNKNOWN"}}))
    lines, src = villa()
    held = line("STR.CONC.COLUMN", "m3", "U-C:COL:SH2:C1@1000,1000|GF", floor="GF", ev="BOUNDED_EXPOSURE", rev=REV_B)
    lines = [ln for ln in lines if not ln["item_code"] == "STR.CONC.COLUMN"] + [held]
    reg = E.build(lines, src, project=PID)
    links, reasons = X.register_links(reg)
    rep = X.crosswalk(X.build_elements(reg, EXTRA), rows(), {}, lines, links, (), (), reasons)
    rec = [ln for ln in rep["lines"] if ln["item_code"] == "STR.CONC.COLUMN"][0]
    assert rec["status"] == "LINKED" and rec["measured_net"] is None       # held stays held, never 0
    assert rep["summary"]["rows"] == {"NOT_MAPPED": 10}
    with pytest.raises(ValueError, match="given twice"):
        X.build_elements(reg, EXTRA + EXTRA[:1])


def test_partly_drawn_row_keeps_the_undrawn_part_visible():
    """R05 re-mapped as 'pool + a balance tank the details do not draw (0.9 m3 of his 4.32)': the row stays DRAWN on
    POOL-01, the tank part is a NOT_DRAWN_PART finding with its quantity; a part without the search is refused."""
    part = {"part": "balance tank", "discipline": "ST", "searched": ["pool detail ST p.7"], "qty": 0.9}
    m = dict(ROW_MAP, **{"WB:S1:5": {"elements": [{"id": f"{PID}/POOL-01", "component": "base"}],
                                     "not_drawn_parts": [part]}})
    rep, _r, _l = run(row_map=m)
    r5 = [r for r in rep["rows"] if r["row_id"] == "WB:S1:5"][0]
    assert r5["status"] == "DRAWN" and r5["not_drawn_parts"][0]["reference_qty"] == 0.9
    assert [x for x in rep["findings"] if x["finding"] == "NOT_DRAWN_PART"] == [
        {"finding": "NOT_DRAWN_PART", "row_id": "WB:S1:5", "part": "balance tank", "discipline": "ST",
         "element": None, "unit": "m3", "reference_qty": 0.9}]
    with pytest.raises(ValueError, match="NOT_DRAWN part"):
        run(row_map=dict(m, **{"WB:S1:5": {"elements": [f"{PID}/POOL-01"],
                                           "not_drawn_parts": [dict(part, searched=[])]}}))


def test_duplicate_pair_over_many_elements_is_one_finding():
    """two type-F1 rows (same trade) on both F1 footings: ONE finding naming the 2 elements, not one per element; a
    row of another trade on the same element is not a duplicate."""
    m = dict(ROW_MAP, **{"WB:S1:4": {"select": {"kind": "FTG", "label_base": "F1"}},
                         "WB:S1:10": {"select": {"kind": "FTG", "label_base": "F1"}}})
    rep, _r, _l = run(row_map=m)
    dup = [x for x in rep["findings"] if x["finding"] == "DUPLICATE_ROW"]
    assert len(dup) == 1 and dup[0]["rows"] == ["WB:S1:2", "WB:S1:4"]
    assert [e.split("/")[-1] for e in dup[0]["elements"]] == ["F1.1", "F1.2"]


# ---- r2 (checker 02:08): one element per physical member per storey ------------------------------------------------
# Hand expectation: element_register_v0 keys each bar set of a column by its own key, so column C1 GF with one concrete
# line and two steel lines (MAIN, TIES) gives 3 register COL elements; the crosswalk counts ONE physical column C1 GF
# with components concrete / steel MAIN / steel TIES. The same mark on 1F is a second, disjoint member. A steel set
# whose concrete element is absent stays its own element (PIECE_WITHOUT_MEMBER). A printed mark whose concrete line is
# NOT_APPLICABLE_WITH_EVIDENCE is not a member of the reference row (listed on it).

def steel(key, net=12.0):
    return line("STR.REBAR", "kg", key, net=net, rev=REV_B)


def villa_r2(sx=1.0, storeys=("GF",), orphan=False, not_applicable=False):
    lines, src = villa(sx)
    x = int(sx * 1000)
    lines = [ln for ln in lines if ln["item_code"] != "STR.CONC.COLUMN"]
    for s in storeys:
        lines += [line("STR.CONC.COLUMN", "m3", f"U-C:COL:SH2:C1@{x},1000|{s}", floor=s, net=0.4, rev=REV_B),
                  steel(f"P-S:COL:SH2:C1@{x},1000|{s}:MAIN:D16"), steel(f"P-S:COL:SH2:C1@{x},1000|{s}:TIES:D8")]
    if orphan:                                   # steel of a column with no concrete line anywhere
        lines.append(steel(f"P-S:COL:SH2:C1@{int(sx * 5000)},1000|GF:MAIN:D16"))
    if not_applicable:                           # a second C1 GF printed, not built (its own line says so)
        lines.append(BL.make_line(project_id=PID, revision_set_sha256=REV_B, item_code="STR.CONC.COLUMN", unit="m3",
                                  evidence_state="NOT_APPLICABLE_WITH_EVIDENCE",
                                  element_id=f"U-C:COL:SH2:C1@{int(sx * 8000)},1000|GF", floor="GF", formula="test",
                                  rule_id="T196", rule_version="test", notes="no column on the slab plan above"))
    return lines, src


def run_r2(**kw):
    lines, src = villa_r2(**kw)
    reg = E.build(lines, src, project=PID)
    links, reasons = X.register_links(reg)
    rmap = {"WB:S1:8": {"select": {"kind": "COL", "label_base": "C1", "floor": "GF"}, "component": "column"}}
    return X.crosswalk(X.build_elements(reg, ()), rows(), rmap, lines, links, (), (), reasons), reg, lines


def test_r2_one_column_three_engine_lines_is_one_element():
    rep, reg, lines = run_r2()
    reg_cols = [e for e in reg["elements"] if e["kind"] == "COL"]
    assert len(reg_cols) == 3                                   # the register's three pieces (the defect r2 corrects)
    cols = [e for e in rep["elements"] if e["kind"] == "COL"]
    assert len(cols) == 1 and cols[0]["floor"] == "GF"
    assert sorted(c["component"] for c in cols[0]["components"]) == ["concrete", "steel MAIN", "steel TIES"]
    assert len(cols[0]["lines"]) == 3 and cols[0]["status"] == "HAS_LINE"     # concrete + both steel lines, once each
    r8 = [r for r in rep["rows"] if r["row_id"] == "WB:S1:8"][0]
    assert r8["status"] == "DRAWN" and r8["elements"] == [cols[0]["id"]]      # not AGGREGATE of 3
    assert rep["summary"]["pieces_collapsed"] == 2
    steel_ids = {ln["line_id"] for ln in lines if ln["item_code"] == "STR.REBAR"}
    assert all(ln["elements"] == [cols[0]["id"]] for ln in rep["lines"] if ln["line_id"] in steel_ids)


def test_r2_two_storeys_of_one_mark_are_two_disjoint_sets():
    rep, _reg, _l = run_r2(storeys=("GF", "1F"))
    cols = {e["floor"]: e for e in rep["elements"] if e["kind"] == "COL"}
    assert set(cols) == {"GF", "1F"}
    a = {c["id"] for c in cols["GF"]["components"]}
    b = {c["id"] for c in cols["1F"]["components"]}
    assert len(a) == 3 and len(b) == 3 and not (a & b)         # never merged across storeys
    r8 = [r for r in rep["rows"] if r["row_id"] == "WB:S1:8"][0]
    assert r8["elements"] == [cols["GF"]["id"]]


def test_r2_mirror_same_counts_and_orphan_steel_kept():
    a, _r, _l = run_r2(storeys=("GF", "1F"), orphan=True)
    b, _r2, _l2 = run_r2(sx=-1.0, storeys=("GF", "1F"), orphan=True)
    assert a["summary"] == b["summary"]
    orph = [f for f in a["findings"] if f["finding"] == "PIECE_WITHOUT_MEMBER"]
    assert len(orph) == 1                                       # steel never silently dropped
    cols = [e for e in a["elements"] if e["kind"] == "COL"]
    assert len(cols) == 3 and any(e["id"] == orph[0]["element"] for e in cols)


def test_r2_not_applicable_mark_is_listed_not_a_member():
    rep, _reg, _l = run_r2(not_applicable=True)
    r8 = [r for r in rep["rows"] if r["row_id"] == "WB:S1:8"][0]
    assert r8["status"] == "DRAWN" and len(r8["elements"]) == 1 and len(r8["not_applicable"]) == 1
    assert r8["not_applicable"][0] not in r8["elements"]
