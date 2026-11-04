"""T-508 ARCH_TAKEOFF_V3.0.55 on a synthetic villa-K508 candidate (hand fixture, not the development villa): stair
skirting home. Room stretches along a shaft with no floor at their level retired by closure; landing pieces valued in
FIN.SKIRTING; flight pieces a blank zigzag / sloped pair until the form is chosen; every other line byte-identical;
adverse inputs refused.

Villa K508 by hand (dog-leg stair GF +-0.00 -> half landing +1.65 -> 1F +3.30; three wall faces of the shaft; riser
0.165 m, going 0.300 m):
  F1.E  face E, s 0 .. 2.700 (9 goings), 10 risers, +0.00 -> +1.65:
        zigzag = 2.700 + 10 x 0.165 = 4.350 lm; sloped = hypot(2.700, 1.650) = sqrt(7.29 + 2.7225) = 3.164253 lm
  LD.E  face E, s 2.700 .. 3.900 at +1.65, wall: 1.200 lm
  LD.N  face N, s 0 .. 2.000 at +1.65, wall + column returns 0.100: 2.100 lm
  LD.N2 face N, s 2.000 .. 2.500 at +1.65: window, sill not printed -> HELD blank (own line), never 0
  F2.W  face W, s 0 .. 2.700, 10 risers, +3.30 (s 0) -> +1.65 (s 2.7): zigzag 4.350 / sloped 3.164253 lm
  landing line LD = 1.200 + 2.000 + 0.100 = 3.300 lm (FIN.SKIRTING, MEASURED)
  form pairs (form not chosen, ORR-007): F1.E, F2.W -> 4 blank lines; zigzag beside 8.700, sloped beside 6.328506
  1F room line, measured at the 1F floor +3.30 along the shaft: gross 20.000, door 2.000, net 18.000 lm, of which
        E 0 .. 3.900 (3.900) and N 0 .. 2.000 + returns 0.100 (2.100) have no +3.30 floor = 6.000 lm retired
        -> net 12.000 lm (closes 20.000 - 2.000 - 6.000); the held range 0 .. 0.500 over N 2.000 .. 2.500 (the window)
        is NOT_APPLICABLE (carried by LD.N2).
  FIN.SKIRTING released 18.000 -> 12.000 + 3.300 = 15.300 lm (-2.700); 1 held landing line added; range closed."""
import copy

import pytest

from engine.source import arch_v304 as A304
from engine.source import arch_v3055 as M
from engine.source import boq_line as BL

PID, REV = "villa-k508", "0" * 64
SLOPE = 3.164253


def mk(eid, code, unit, state, net=None, gross=None, floor="GF", ded=(), rng=None):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                        measured_net=net, gross=gross, element_id=eid, floor=floor, formula="synthetic", rule_id="R-X",
                        rule_version="1", item_en=code, item_ar=code, deductions=ded, bounded_range=rng,
                        rfi={"question": "held"} if state == "BLOCKED_RFI" else None)


def candidate():
    return [mk("GF-WALLS:t=0.20", "MAS.BLOCK", "m2", "SOURCE_DERIVED", 40.0, 40.0),
            mk("1F-R1:skirting", "FIN.SKIRTING", "lm", "MEASURED", 18.0, 20.0, floor="1F",
               ded=[{"opening_id": "D-1", "qty": 2.0}]),
            mk("1F-R1:skirting, boundary role unresolved", "FIN.SKIRTING", "lm", "BOUNDED_EXPOSURE", floor="1F",
               rng={"low": 0.0, "high": 0.5, "basis": "window base"}),
            mk("GF-R2:skirting", "FIN.SKIRTING", "lm", "MEASURED", 9.0, 9.0)]


ROOM = BL.line_id(PID, "FIN.SKIRTING", "1F-R1:skirting", "R-X", "1", "lm")
RANGE = BL.line_id(PID, "FIN.SKIRTING", "1F-R1:skirting, boundary role unresolved", "R-X", "1", "lm")
SRC = [{"task": "T-K", "file": "stair_side_table.csv", "sha256": "k" * 64, "merge_commit": "abcdef12",
        "checker_run": "run k"},
       {"task": "T-K binding", "file": "binding.csv", "sha256": "b" * 64, "merge_commit": "abcdef12",
        "checker_run": "run k"}]


def P(pid, element, face, kind, cls, s0, s1, l0, l1, risers=0, ret=0.0, status=None, value=None, zz=None, sl=None,
      cause="", floor="GF"):
    return {"pid": pid, "element": element, "face": face, "kind": kind, "cls": cls,
            "status": status or ({"LANDING": "DRAWING-CONFIRMED"}.get(kind, "HELD-FORM") if cls == "WALL" else cls),
            "floor": floor, "s0": s0, "s1": s1, "plan_lm": round(s1 - s0, 6), "risers": risers, "returns_lm": ret,
            "level0": l0, "level1": l1, "value_lm": value, "zigzag_lm": zz, "sloped_lm": sl, "cause": cause,
            "evidence": "villa K508 plans", "source_tasks": ["T-K"]}


def pieces():
    return [P("F1.E", "F1", "E", "FLIGHT", "WALL", 0.0, 2.7, 0.0, 1.65, risers=10, zz=4.35, sl=SLOPE),
            P("LD.E", "LD", "E", "LANDING", "WALL", 2.7, 3.9, 1.65, 1.65, value=1.2),
            P("LD.N", "LD", "N", "LANDING", "WALL", 0.0, 2.0, 1.65, 1.65, ret=0.1, value=2.1),
            P("LD.N2", "LD", "N", "LANDING", "HELD", 2.0, 2.5, 1.65, 1.65, cause="window: sill not printed"),
            P("F2.W", "F2", "W", "FLIGHT", "WALL", 0.0, 2.7, 3.3, 1.65, risers=10, zz=4.35, sl=SLOPE, floor="1F")]


def doc(**over):
    d = {"schema": M.INPUTS_SCHEMA, "project_id": PID, "sources": SRC, "form": None, "pieces": pieces(),
         "retire": {"room_line_id": ROOM, "floor_level": 3.3,
                    "expect": {"evidence_state": "MEASURED", "gross": 20.0, "measured_net": 18.0},
                    "stretches": [{"segment": "E 0 .. 3.900", "face": "E", "s0": 0.0, "s1": 3.9,
                                   "status_before": "certain", "owners": ["F1.E", "LD.E"]},
                                  {"segment": "N 0 .. 2.000", "face": "N", "s0": 0.0, "s1": 2.0, "returns_lm": 0.1,
                                   "status_before": "certain", "owners": ["LD.N"]},
                                  {"segment": "N window", "face": "N", "s0": 2.0, "s1": 2.5,
                                   "status_before": "held range", "owners": ["LD.N2"]}],
                    "range_line_id": RANGE, "range_expect": {"low": 0.0, "high": 0.5},
                    "source_tasks": ["T-K binding"]}}
    d.update(over)
    return d


def run(d=None, prev=None):
    prev = prev or candidate()
    v = M.load_inputs(d or doc(), PID)
    ch, log = M.changes_for(v, prev)
    new, ident = M.integrate(prev, ch)
    return prev, new, ident, log


def by_eid(lines):
    return {ln["location"]["element_id"]: ln for ln in lines}


# ------------------------------------------------------------------------------------------------ normal case
def test_hand_figures():
    prev, new, ident, log = run()
    e = by_eid(new)
    room = e["1F-R1:skirting"]
    assert room["measured_net"] == 12.0 and room["gross"] == 20.0
    assert sum(x["qty"] for x in room["deductions"]) == pytest.approx(8.0)       # door 2.000 + shaft 6.000
    assert e["1F-R1:skirting, boundary role unresolved"]["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE"
    assert e["1F-R1:skirting, boundary role unresolved"]["bounded_range"] is None
    ld = e["STAIR-SKIRT:LD:landing"]
    assert ld["item_code"] == "FIN.SKIRTING" and ld["measured_net"] == 3.3 and ld["evidence_state"] == "MEASURED"
    held = e["STAIR-SKIRT:LD.N2"]
    assert held["evidence_state"] == "BLOCKED_RFI" and held["measured_net"] is None and held["gross"] is None
    assert log["landing_lm"] == 3.3 and log["retired_lm"] == 6.0 and log["closed_range_lm"] == 0.5
    assert log["form_beside"] == {"zigzag_lm": 8.7, "sloped_lm": 6.328506, "wall_pieces": 2, "risers": 20}
    assert log["risers_by_flight"] == {"F1": 0.165, "F2": 0.165}
    assert ident["stair_skirting"] == {"landings": 1, "landing_lm": 3.3, "landing_held": 1, "pairs": 4,
                                       "valued_pairs": 0, "retired_lm": 6.0, "closed": 1}


def test_form_pairs_blank_never_additive():
    _, new, _, _ = run()
    pairs = [ln for ln in new if ln["item_code"] in (M.ZIG, M.SLO)]
    assert len(pairs) == 4
    for ln in pairs:
        assert ln["evidence_state"] == "BLOCKED_RFI" and ln["measured_net"] is None and ln["gross"] is None
        rec = ln["calculation"]["inputs"][M.REC_KEY]
        assert rec["pair_line"] in ln["never_additive_with"]
        assert rec["figure_beside_lm"] == (4.35 if ln["item_code"] == M.ZIG else SLOPE)
        assert rec["family"] == ("B7-07" if ln["item_code"] == M.ZIG else "B7-08")
    t = BL.totals(new, by=("floor",))
    assert all(v["lm"]["net"] >= 0 for v in t.values())


def test_totals_move_only_in_skirting_codes_and_rest_identical():
    prev, new, ident, _ = run()
    moved = M.check_totals(A304.code_totals(prev), A304.code_totals(new))
    assert set(moved) == {"FIN.SKIRTING|lm", M.ZIG + "|lm", M.SLO + "|lm"}
    assert moved["FIN.SKIRTING|lm"]["base"]["released"] == 27.0
    assert moved["FIN.SKIRTING|lm"]["v3_0_55"]["released"] == 24.3         # 12.0 + 9.0 + 3.3
    assert moved["FIN.SKIRTING|lm"]["v3_0_55"]["bounded_lines"] == 0
    assert moved[M.ZIG + "|lm"]["v3_0_55"]["blocked_lines"] == 2
    assert ident["outside_rows"] == ident["outside_rows_identical_to_base"] == 2
    assert (ident["replaced"], ident["added"]) == (2, 6)


def test_form_chosen_values_one_form_only():
    _, new, ident, _ = run(doc(form="sloped"))
    slo = [ln for ln in new if ln["item_code"] == M.SLO]
    zig = [ln for ln in new if ln["item_code"] == M.ZIG]
    assert all(ln["measured_net"] == SLOPE and ln["evidence_state"] == "MEASURED" for ln in slo)
    assert all(ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and ln["measured_net"] is None for ln in zig)
    assert ident["stair_skirting"]["valued_pairs"] == 2


def test_mirror_invariance():
    d = doc()
    for p in d["pieces"]:                                   # mirror every face: s -> L - s (L = 4.0)
        p["s0"], p["s1"] = round(4.0 - p["s1"], 6), round(4.0 - p["s0"], 6)
        p["level0"], p["level1"] = p["level1"], p["level0"]
    for s in d["retire"]["stretches"]:
        s["s0"], s["s1"] = round(4.0 - s["s1"], 6), round(4.0 - s["s0"], 6)
    a, b = run()[3], run(d)[3]
    for k in ("landing_lm", "retired_lm", "closed_range_lm", "form_beside", "risers_by_flight"):
        assert a[k] == b[k]


# ------------------------------------------------------------------------------------------------ adverse cases
def refused(d=None, prev=None, match=None):
    with pytest.raises((M.InputsError, ValueError), match=match):
        run(d, prev)


@pytest.mark.parametrize("form", ["wall", "open side", "average", "both"])
def test_side_or_average_is_not_a_form(form):
    refused(doc(form=form), match="not a form")


def test_open_side_is_no_piece():
    d = doc()
    d["pieces"][0]["kind"] = "OPEN"
    refused(d, match="open side is no piece")


def test_uncovered_stretch_keeps_the_room_figure():
    d = doc()
    d["pieces"] = [p for p in d["pieces"] if p["pid"] != "LD.E"]
    d["retire"]["stretches"][0]["owners"] = ["F1.E"]
    refused(d, match="cover")


def test_floor_at_the_level_is_never_retired():
    d = doc()
    d["retire"]["floor_level"] = 1.65                       # the landing stands at the room floor's level
    refused(d, match="stands at the room floor")


def test_two_owners_of_one_strip():
    d = doc()
    d["pieces"].append(P("LD.E2", "LD", "E", "LANDING", "WALL", 3.0, 3.5, 1.65, 1.65, value=0.5))
    refused(d, match="two owners")


def test_held_with_value_and_confirmed_mismatch():
    d = doc()
    d["pieces"][3]["value_lm"] = 0.0
    refused(d, match="carries a value")
    d = doc()
    d["pieces"][1]["value_lm"] = 1.25
    refused(d, match="plan \\+ returns")


def test_millimetres_refused():
    d = doc()
    d["pieces"][1].update(s0=2700.0, s1=3900.0, plan_lm=1200.0)
    refused(d, match="millimetres")


def test_one_riser_per_flight():
    d = doc()
    d["pieces"][0]["zigzag_lm"] = 4.45                      # 0.175 implied vs ... same flight F1 alone: still a riser
    d["pieces"].append(P("F1.Eb", "F1", "S", "FLIGHT", "WALL", 0.0, 0.3, 0.0, 0.165, risers=1, zz=0.465,
                         sl=0.342381))
    refused(d, match="one flight, one riser")


def test_sloped_recomputed_from_levels():
    d = doc()
    d["pieces"][0]["sloped_lm"] = 3.2                       # not hypot(2.7, 1.65)
    refused(d, match="hypot")


def test_held_without_cause_and_step_shape():
    d = doc()
    d["pieces"][3]["cause"] = ""
    refused(d, match="without a cause")


def test_stale_room_line_and_partial_range():
    d = doc()
    d["retire"]["expect"]["measured_net"] = 17.0
    refused(d, match="stale binding")
    d = doc()
    d["retire"]["range_expect"] = {"low": 0.0, "high": 0.7}
    prev = candidate()
    prev[2] = mk("1F-R1:skirting, boundary role unresolved", "FIN.SKIRTING", "lm", "BOUNDED_EXPOSURE", floor="1F",
                 rng={"low": 0.0, "high": 0.7, "basis": "window base"})
    refused(d, prev, match="closed only whole")


def test_applied_once():
    _, new, _, _ = run()
    refused(prev=new, match="already carries")


def test_check_refuses_both_forms_valued_and_a_zero_landing():
    _, new, _, _ = run()
    bad = copy.deepcopy(new)
    for ln in bad:
        if ln["item_code"] in (M.ZIG, M.SLO):
            ln["evidence_state"], ln["measured_net"], ln["gross"], ln["rfi"] = "MEASURED", 1.0, 1.0, None
    with pytest.raises(ValueError):
        M.check_stair_skirting(bad)
    bad = copy.deepcopy(new)
    for ln in bad:
        if ln["location"]["element_id"] == "STAIR-SKIRT:LD:landing":
            ln["measured_net"] = ln["gross"] = 0.0
    with pytest.raises(ValueError, match="sum of its pieces"):
        M.check_stair_skirting(bad)


def test_check_refuses_a_lone_pair_line():
    _, new, _, _ = run()
    drop = next(ln["line_id"] for ln in new if ln["item_code"] == M.SLO)
    with pytest.raises(ValueError, match="incomplete"):
        M.check_stair_skirting([ln for ln in new if ln["line_id"] != drop])


def test_integrate_refuses_a_foreign_code():
    prev = candidate()
    v = M.load_inputs(doc(), PID)
    ch, _ = M.changes_for(v, prev)
    ch[0] = dict(ch[0], after=dict(ch[0]["after"], item_code="MAS.BLOCK"))
    with pytest.raises(ValueError, match="not a code"):
        M.integrate(prev, ch)
