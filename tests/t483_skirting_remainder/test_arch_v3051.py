"""T-483: ARCH_TAKEOFF_V3.0.51 (skirting remainder: sill release, range close, cell walk) on a hand-calculated
NON-Alsenan villa (K483).

Villa K483, by hand (own figures; nothing from the development villa):
  R1 majlis (GF): walls 5.00 x 4.00 -> gross 18.00 lm. Doors D1 0.90 + D2 1.10 = 2.00 deducted (UP-CER-003). Windows
     WA 1.50 and WB 1.50 listed in halves (0.75 + 0.75 each, UNRESOLVED). Section: frame base +1.05 over the +0.30
     floor -> sill 0.75 m above the FFL: wall under it, skirted.
        before: 18.00 - 2.00 - 3.00 = 13.00 lm; range line R1 [0, 3.00] (WA + WB).
        after:  18.00 - 2.00 = 16.00 lm (+3.00); the range line NOT_APPLICABLE, carried by R1 (no figure, never 0).
  R2 saloon (GF): range line [0, 4.20] = WC 4.20, frame base on the floor (sill 0.00): floor glazing, no wall base.
        after: range NOT_APPLICABLE (closed whole, -4.20 held high); no certain value moves.
  R3 living (1F): range line [0, 2.10] = WD 1.30 + WE 0.80, both inside stair-flight stretches (owners FL-1.W2, FL-2.N)
        after: range NOT_APPLICABLE (STAIR_OWNED, -2.10 held high).
  R4 dressing (1F): skirting line BLOCKED_RFI blank. Walk by handle (cell 2.00 x 1.50):
     W 2.00: wall a1 0.00..0.40 | door D3 0.40..1.20 (0.80) | wall a2 1.20..2.00    faces 1.20
     E 2.00: wall a3                                                                 faces 2.00 (wardrobe in front:
             joinery, not a boundary; 2.00 beside)
     N 1.50: wall a4                                                                 faces 1.50
     S 1.50: wall a5 0.00..0.30 | arch A1 0.30..1.20 (0.90) | wall a6 1.20..1.50     faces 0.60
     gross 7.00 - D3 0.80 - A1 0.90 = 5.30 lm.
  Certain FIN.SKIRTING: +3.00 (R1) + 5.30 (R4) = +8.30 lm; held high: -3.00 - 4.20 - 2.10 = -9.30 lm.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3051 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-k483", "d" * 64
DOCS = [{"file": "k483_arch.dxf", "sha256": "c" * 64}]


def _src(t):
    return {"task": t, "file": f"research/k483/{t}.csv", "sha256": t[-1] * 64, "merge_commit": "b" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _ded(i, q, cid=None, chk=None):
    d = {"id": i, "qty": q, "unit": "lm"}
    if cid:
        d["census_id"] = cid
    if chk:
        d["physical_check"] = chk
    return d


def _skirt(room, floor, ev, net=None, gross=None, ded=(), br=None, eid=None, rfi=None):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="FIN.SKIRTING", unit="lm", evidence_state=ev,
                        measured_net=net, gross=gross, deductions=list(ded), bounded_range=br,
                        element_id=eid or f"{room}:skirting", floor=floor, room_id=room,
                        formula=f"skirting {room}", documents=DOCS, rule_id="G", rule_version="1", rfi=rfi, notes="k")


def base_lines():
    q = {"question": "sill", "unlocks": "x"}
    r1 = _skirt("R1", "GF", "SOURCE_DERIVED", net=13.0, gross=18.0,
                ded=[_ded("D1", 0.9), _ded("D2", 1.1), _ded("WA#g", 0.75, "WA", "UNRESOLVED"),
                     _ded("WA#t", 0.75, "WA", "UNRESOLVED"), _ded("WB#g", 0.75, "WB", "UNRESOLVED"),
                     _ded("WB#t", 0.75, "WB", "UNRESOLVED")])
    r1r = _skirt("R1", "GF", "BOUNDED_EXPOSURE", br={"low": 0.0, "high": 3.0, "basis": "WA + WB"},
                 eid="R1:skirting:range", rfi=q)
    r2r = _skirt("R2", "GF", "BOUNDED_EXPOSURE", br={"low": 0.0, "high": 4.2, "basis": "WC"},
                 eid="R2:skirting:range", rfi=q)
    r3 = _skirt("R3", "1F", "SOURCE_DERIVED", net=25.0, gross=26.0, ded=[_ded("D5", 1.0)])
    r3r = _skirt("R3", "1F", "BOUNDED_EXPOSURE", br={"low": 0.0, "high": 2.1, "basis": "WD + WE"},
                 eid="R3:skirting:range", rfi=q)
    r4 = _skirt("R4", "1F", "BLOCKED_RFI", eid="SKIRT-T422:R4", rfi={"question": "walk", "unlocks": "R4"})
    floor = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="FIN.FLOOR.PORCELAIN", unit="m2",
                         evidence_state="PROVISIONAL", measured_net=20.0, gross=20.0, element_id="R1:floor",
                         floor="GF", room_id="R1", formula="5 x 4", documents=DOCS, rule_id="G", rule_version="1",
                         notes="k")
    return [r1, r1r, r2r, r3, r3r, r4, floor]


def _id(lines, eid):
    return next(x["line_id"] for x in lines if x["location"]["element_id"] == eid)


def _w(cid, edge, sill, status="DRAWING-CONFIRMED", **kw):
    return dict({"census_id": cid, "edge_lm": edge, "sill_m": sill, "status": status, "why": f"{cid} merged sill"},
                **kw)


def walk_sides():
    return [
        {"id": "W", "length": 2.0, "stretches": [{"s0": 0.0, "s1": 0.4, "kind": "WALL", "handles": "a1"},
                                                 {"s0": 0.4, "s1": 1.2, "kind": "DOOR", "opening_id": "D3"},
                                                 {"s0": 1.2, "s1": 2.0, "kind": "WALL", "handles": "a2"}]},
        {"id": "E", "length": 2.0, "stretches": [{"s0": 0.0, "s1": 2.0, "kind": "WALL", "handles": "a3"}]},
        {"id": "N", "length": 1.5, "stretches": [{"s0": 0.0, "s1": 1.5, "kind": "WALL", "handles": "a4"}]},
        {"id": "S", "length": 1.5, "stretches": [{"s0": 0.0, "s1": 0.3, "kind": "WALL", "handles": "a5"},
                                                 {"s0": 0.3, "s1": 1.2, "kind": "ARCH", "opening_id": "A1"},
                                                 {"s0": 1.2, "s1": 1.5, "kind": "WALL", "handles": "a6"}]},
    ]


def inputs(lines):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-481")],
            "releases": [{"line_id": _id(lines, "R1:skirting"), "expect": {"gross": 18.0, "measured_net": 13.0},
                          "windows": [_w("WA", 1.5, 0.75), _w("WB", 1.5, 0.75)],
                          "range_line": {"line_id": _id(lines, "R1:skirting:range"),
                                         "expect": {"low": 0.0, "high": 3.0}}, "source_tasks": ["T-481"]}],
            "closes": [{"line_id": _id(lines, "R2:skirting:range"), "expect": {"low": 0.0, "high": 4.2},
                        "windows": [_w("WC", 4.2, 0.0, reason="FLOOR_GLAZING")], "source_tasks": ["T-481"]},
                       {"line_id": _id(lines, "R3:skirting:range"), "expect": {"low": 0.0, "high": 2.1},
                        "windows": [_w("WD", 1.3, None, reason="STAIR_OWNED", owner="FL-1.W2"),
                                    _w("WE", 0.8, None, reason="STAIR_OWNED", owner="FL-2.N")],
                        "source_tasks": ["T-481"]}],
            "walks": [{"line_id": _id(lines, "SKIRT-T422:R4"), "room": "R4", "floor": "1F",
                       "expect": {"evidence_state": "BLOCKED_RFI"}, "gross_lm": 7.0,
                       "evidence_status": "DRAWING-CONFIRMED", "evidence_state": "SOURCE_DERIVED",
                       "joinery_backed_lm": 2.0, "sides": walk_sides(), "source_tasks": ["T-481"]}]}


def run(lines=None, doc=None):
    lines = lines or base_lines()
    d = A.load_inputs(doc or inputs(lines), PID)
    ch, log = A.changes_for(d, lines)
    new, ident = A.integrate(lines, ch)
    return lines, new, ident, log


def by_eid(lines, eid):
    return next(x for x in lines if x["location"]["element_id"] == eid)


# ------------------------------------------------------------------------------------------------ normal
def test_release_rises_by_the_window_edges_and_closes():
    _, new, ident, log = run()
    r1 = by_eid(new, "R1:skirting")
    assert r1["measured_net"] == pytest.approx(16.0)
    assert r1["gross"] == pytest.approx(18.0)
    assert [d["id"] for d in r1["deductions"]] == ["D1", "D2"]
    assert log["released_lm"] == pytest.approx(3.0)
    assert ident["remainder"]["released_lm"] == pytest.approx(3.0)


def test_released_range_is_not_applicable_and_names_its_carrier():
    _, new, ident, _ = run()
    rg = by_eid(new, "R1:skirting:range")
    assert rg["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE"
    assert rg["bounded_range"] is None and rg["measured_net"] is None
    rec = rg["calculation"]["inputs"][A.REC_KEY]
    assert rec["action"] == "ABSORB_RANGE" and rec["carried_by"] == by_eid(new, "R1:skirting")["line_id"]


def test_floor_glazing_and_stair_owned_ranges_closed_whole():
    _, new, ident, log = run()
    for eid in ("R2:skirting:range", "R3:skirting:range"):
        ln = by_eid(new, eid)
        assert ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and ln["bounded_range"] is None
    assert log["range_closed_lm"] == pytest.approx(6.3)
    assert by_eid(new, "R3:skirting")["measured_net"] == pytest.approx(25.0)   # a close moves no value


def test_cell_walk_values_the_blocked_line():
    _, new, ident, log = run()
    r4 = by_eid(new, "SKIRT-T422:R4")
    assert r4["evidence_state"] == "SOURCE_DERIVED" and r4["rfi"] is None
    assert r4["gross"] == pytest.approx(7.0) and r4["measured_net"] == pytest.approx(5.3)
    assert sorted(d["opening_id"] for d in r4["deductions"]) == ["A1", "D3"]
    assert all(d["jamb_skirting"] is False for d in r4["deductions"])
    assert r4["calculation"]["inputs"][A.REC_KEY]["joinery_backed_lm"] == pytest.approx(2.0)


def test_totals_move_only_in_skirting_by_hand():
    old, new, ident, _ = run()
    t0, t1 = A304.code_totals(old), A304.code_totals(new)
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    assert moved and all(k.startswith("FIN.SKIRTING") for k in moved)
    cert = lambda ls: sum(x["measured_net"] or 0 for x in ls if x["item_code"] == "FIN.SKIRTING")  # noqa: E731
    hi = lambda ls: sum((x.get("bounded_range") or {}).get("high") or 0 for x in ls  # noqa: E731
                        if x["item_code"] == "FIN.SKIRTING")
    assert cert(new) - cert(old) == pytest.approx(8.3)
    assert hi(old) - hi(new) == pytest.approx(9.3)


def test_outside_lines_byte_identical_and_no_line_added():
    old, new, ident, _ = run()
    assert len(new) == len(old) and ident["added"] == 0
    named = {ln["line_id"] for ln in old if ln["location"]["element_id"] not in ("R3:skirting", "R1:floor")}
    for a, b in zip(old, new):
        if a["line_id"] not in named:
            assert A30.line_sha(a) == A30.line_sha(b)


def test_mirror_invariance_of_the_walk():
    lines = base_lines()
    doc = inputs(lines)
    sides = walk_sides()
    for sd in sides:           # mirrored cell: each side walked from the other end
        L = sd["length"]
        sd["stretches"] = [dict(st, s0=round(L - st["s1"], 6), s1=round(L - st["s0"], 6))
                           for st in reversed(sd["stretches"])]
    doc["walks"][0]["sides"] = sides
    _, new, _, _ = run(lines, doc)
    assert by_eid(new, "SKIRT-T422:R4")["measured_net"] == pytest.approx(5.3)


def test_files_written(tmp_path):
    old = base_lines()
    d = A.load_inputs(inputs(old), PID)
    ch, log = A.changes_for(d, old)
    names, ident, led = A.write(tmp_path, old, ch, log)
    assert "V3_0_51_BOQ_LINES.json" in names
    run_doc = json.loads((tmp_path / "V3_0_51_RUN.json").read_text(encoding="utf-8"))
    assert run_doc["released_default"] is False and "T483_1F_SHAFT" in run_doc["waiting_pieces"]
    assert "T443_1F_SHAFT" not in run_doc["waiting_pieces"]


# ------------------------------------------------------------------------------------------------ adverse
def _bad(mut, msg):
    lines = base_lines()
    doc = inputs(lines)
    mut(doc, lines)
    with pytest.raises(A.InputsError, match=msg):
        d = A.load_inputs(doc, PID)
        A.changes_for(d, lines)


def test_sill_at_floor_is_not_released():
    _bad(lambda d, ls: d["releases"][0]["windows"].__setitem__(0, _w("WA", 1.5, 0.01)), "not above the floor")


def test_sill_in_millimetres_refused():
    _bad(lambda d, ls: d["releases"][0]["windows"].__setitem__(0, _w("WA", 1.5, 750)), "not a sill height")


def test_unread_sill_stays_held():
    _bad(lambda d, ls: d["releases"][0]["windows"].__setitem__(0, _w("WA", 1.5, 0.75, status="UNRESOLVED")),
         "unread sill stays held")


def test_partial_listing_refused():
    _bad(lambda d, ls: d["releases"][0]["windows"].__setitem__(0, _w("WA", 1.2, 0.75)), "partial or doubled")


def test_stale_release_binding_refused():
    _bad(lambda d, ls: d["releases"][0]["expect"].__setitem__("measured_net", 13.5), "stale binding")


def test_floor_glazing_with_a_raised_sill_refused():
    _bad(lambda d, ls: d["closes"][0]["windows"].__setitem__(0, _w("WC", 4.2, 0.6, reason="FLOOR_GLAZING")),
         "floor glazing needs")


def test_stair_owned_without_owner_refused():
    _bad(lambda d, ls: d["closes"][1]["windows"][0].pop("owner"), "names its stair side stretch owner")


def test_partial_close_refused():
    _bad(lambda d, ls: d["closes"][1].__setitem__("windows", [d["closes"][1]["windows"][0]]), "closed only whole")


def test_close_of_a_valued_line_refused():
    def m(d, ls):
        d["closes"][0]["line_id"] = _id(ls, "R3:skirting")
    _bad(m, "stale binding")


def test_walk_gap_refused():
    _bad(lambda d, ls: d["walks"][0]["sides"][0]["stretches"][2].__setitem__("s0", 1.25), "gap")


def test_walk_face_without_handle_refused():
    _bad(lambda d, ls: d["walks"][0]["sides"][1]["stretches"][0].pop("handles"), "without a drawn handle")


def test_walk_opening_without_id_refused():
    _bad(lambda d, ls: d["walks"][0]["sides"][0]["stretches"][1].pop("opening_id"), "without an opening id")


def test_walk_joinery_as_boundary_refused():
    _bad(lambda d, ls: d["walks"][0]["sides"][1]["stretches"][0].__setitem__("kind", "JOINERY"), "joinery")


def test_walk_side_short_cover_refused():
    _bad(lambda d, ls: d["walks"][0]["sides"][2].__setitem__("length", 1.6), "short cover")


def test_walk_declared_gross_mismatch_refused():
    _bad(lambda d, ls: d["walks"][0].__setitem__("gross_lm", 7.4), "declared gross")


def test_walk_jamb_skirting_refused():
    _bad(lambda d, ls: d["walks"][0].__setitem__("jambs", [{"opening_id": "D3", "depth": 0.2}]), "jamb")


def test_walk_in_millimetres_refused():
    _bad(lambda d, ls: d["walks"][0]["sides"][1].__setitem__("length", 2000), "mm / cm")


def test_walk_of_a_valued_line_refused():
    _bad(lambda d, ls: d["walks"][0].__setitem__("line_id", _id(ls, "R3:skirting")), "stale binding")


def test_walk_held_line_never_zero():
    def m(d, ls):
        for st in d["walks"][0]["sides"]:
            for x in st["stretches"]:
                if x["kind"] == "WALL":
                    x["kind"], x["opening_id"] = "DOOR", f"X{x['handles']}"
                    x.pop("handles")
    _bad(m, "no skirted face")


def test_one_line_named_twice_refused():
    def m(d, ls):
        d["closes"][0]["line_id"] = d["releases"][0]["range_line"]["line_id"]
    _bad(m, "named twice")


def test_applied_twice_refused():
    old, new, _, _ = run()
    d = A.load_inputs(inputs(old), PID)
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(d, new)


def test_wrong_project_refused():
    lines = base_lines()
    doc = inputs(lines)
    doc["project_id"] = "other"
    with pytest.raises(A.InputsError, match="are for"):
        A.load_inputs(doc, PID)


def test_post_integration_check_catches_a_figure_on_a_closed_range():
    old, new, _, _ = run()
    bad = copy.deepcopy(new)
    rg = by_eid(bad, "R2:skirting:range")
    rg["bounded_range"] = {"low": 0.0, "high": 0.0}
    with pytest.raises(ValueError, match="carries a figure"):
        A.check_remainder(bad, old)


def test_range_with_an_earlier_narrow_record_closes():
    """regression (Alsenan chain): a range line narrowed by V3.0.44 (its NARROW_RANGE record kept) closed here: the
    V3.0.44 check must not read the superseded record; the closed line is checked by check_remainder."""
    from engine.source import arch_v3044 as A44
    lines = base_lines()
    i = next(k for k, x in enumerate(lines) if x["location"]["element_id"] == "R3:skirting:range")
    ln = copy.deepcopy(lines[i])
    ln["calculation"]["inputs"][A44.REC_KEY] = {"action": "NARROW_RANGE"}
    lines[i] = BL.validate(ln)
    with pytest.raises(ValueError, match="not a held range"):
        A44.check_skirting([dict(ln, evidence_state="NOT_APPLICABLE_WITH_EVIDENCE", bounded_range=None)])
    _, new, ident, _ = run(lines)
    assert by_eid(new, "R3:skirting:range")["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE"
    assert ident["superseded_records"] == [A44.REC_KEY]
