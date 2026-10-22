"""T-194 OPENING_CONSISTENCY_V1: hand fixtures, NOT the development villa.

Villa "T194-A" (metres unless stated), one facade F seen from outside, left -> right; plan positions are the opening
centres from the facade's left corner:
  plan        WA 1.20 window @1.00   WB 1.80 window @4.00   DA 0.90 door @7.00   WC 0.60 window @9.50
              DI 0.80 interior door (no facade)
  elevation   drawn with its left edge 2.00 m beyond the plan corner: features @3.00 (1.20 printed, sill +1.35,
              head +2.55, FFL +0.45), @6.00 (1.75 printed), @9.00 (door), @11.50 (window, nothing printed),
              @13.00 (window 1.00 printed): the last one is on NO plan -> ELEVATION_ONLY
  section     WA sill as the chain part "90" from the +0.45 floor line -> 0.90 above FFL
  schedule    WA 1.20 x (0.90 .. 2.10), DA door 0.90 head 2.10, WB 1.80, WC 0.60; DI is NOT in the schedule

Hand truth:
  WA  width 1.20 plan = elevation = schedule: AGREES. Sill 1.35 - 0.45 = 0.90 (elevation, LEVEL) = 0.45 + 0.90 - 0.45
      = 0.90 (section, CHAIN_PART) = 0.90 (schedule): AGREES, but stated on three bases -> SILL_BASIS_MIXED (info).
      Head 2.55 - 0.45 = 2.10 = schedule 2.10: AGREES, also on two bases -> HEAD_BASIS_MIXED (info).
  WB  plan 1.80, schedule 1.80, elevation 1.75: WIDTH_DIFFERS (spread 0.05 m > 0.01): opening m2, block deduction,
      finish deductions, reveals, sill, lintel HELD.
  DA  kinds DOOR on plan, elevation and schedule: AGREES; head 2.10 printed on the schedule only: NOT_COMPARABLE
      (SINGLE_SOURCE), nothing held for it.
  WC  head printed nowhere: HEAD_NOT_PRINTED -> opening m2 / deductions / reveals / lintel HELD (never 0, no twin).
  DI  on the plan, in no schedule although the project issues one: MISSING_FROM_LIST.
Adverse: the same elevation drawn mirrored (binds only mirrored, MIRRORED_VIEW, same identities); the elevation given
in millimetres (same result) and the same millimetre numbers given as metres (refused); a symmetric pair of twins
(AMBIGUOUS, nothing bound); a curved bay (elevation chord vs plan chord AGREES, outer arc kept apart; a wrong chord
DIFFERS); an opening list (derived census) whose sill is a raw chain part (SILL_LIST_DIFFERS); a cut / occluded view
(NOT_SHOWN, never DIFFERS) vs a view that simply omits it (NOT_DRAWN_ON_SOURCE); an INFERRED value, a LEVEL without
its floor level, a missing basis, missing units and a duplicate observation (refused)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import opening_consistency_v1 as OC          # noqa: E402

PLAN = [
    {"opening_id": "WA", "kind": "WINDOW", "width": 1.20, "pos_m": 1.00},
    {"opening_id": "WB", "kind": "WINDOW", "width": 1.80, "pos_m": 4.00},
    {"opening_id": "DA", "kind": "DOOR", "width": 0.90, "pos_m": 7.00},
    {"opening_id": "WC", "kind": "WINDOW", "width": 0.60, "pos_m": 9.50},
]
ELEV = [  # (pos from the elevation's left edge, kind, width printed, sill level, head level)
    (3.00, "WINDOW", 1.20, 1.35, 2.55),
    (6.00, "WINDOW", 1.75, None, None),
    (9.00, "DOOR", None, None, None),
    (11.50, "WINDOW", None, None, None),
    (13.00, "WINDOW", 1.00, None, None),
]
L_ELEV = 15.0


def _plan(rows=PLAN, facade="F"):
    return [dict(r, source="PLAN", ref="A-101", units="m", width_basis="JAMB_TO_JAMB", storey="GF", facade=facade)
            for r in rows]


def _elev(mirror=False, mm=False, units=None):
    out = []
    for pos, kind, w, sill, head in ELEV:
        p = L_ELEV - pos if mirror else pos
        f = 1000.0 if mm else 1.0
        o = {"opening_id": None, "source": "ELEVATION", "ref": "A-201", "units": units or ("mm" if mm else "m"),
             "kind": kind, "storey": "GF", "facade": "F", "pos_m": p * f}
        if w is not None:
            o.update(width=w * f, width_basis="PRINTED")
        if sill is not None:
            o.update(sill=sill * f, head=head * f, level_basis="LEVEL", ffl=0.45 * f)
        out.append(o)
    return out


SECTION = {"opening_id": "WA", "source": "SECTION", "ref": "A-301", "units": "m", "sill": 0.90,
           "level_basis": "CHAIN_PART", "chain_base": 0.45, "ffl": 0.45}
SCHEDULE = [
    {"opening_id": "WA", "source": "SCHEDULE", "ref": "A-601", "units": "m", "kind": "WINDOW", "width": 1.20,
     "width_basis": "PRINTED", "sill": 0.90, "head": 2.10, "level_basis": "ABOVE_FFL"},
    {"opening_id": "WB", "source": "SCHEDULE", "ref": "A-601", "units": "m", "kind": "WINDOW", "width": 1.80,
     "width_basis": "PRINTED"},
    {"opening_id": "DA", "source": "SCHEDULE", "ref": "A-601", "units": "m", "kind": "DOOR", "width": 0.90,
     "width_basis": "PRINTED", "head": 2.10, "level_basis": "ABOVE_FFL"},
    {"opening_id": "WC", "source": "SCHEDULE", "ref": "A-601", "units": "m", "kind": "WINDOW", "width": 0.60,
     "width_basis": "PRINTED"},
]
DI = {"opening_id": "DI", "source": "PLAN", "ref": "A-101", "units": "m", "kind": "DOOR", "width": 0.80,
      "width_basis": "JAMB_TO_JAMB", "storey": "GF"}


def _bind(elev):
    plan_n = [OC.normalise(o) for o in _plan()]
    feats = [OC.normalise(o) for o in elev]
    res = OC.bind(plan_n, feats)
    bound = []
    for f, pid in res["bound"]:
        raw = elev[feats.index(f)]
        bound.append(dict(raw, opening_id=pid))
    return res, bound


def _run(mirror=False, mm=False):
    elev = _elev(mirror=mirror, mm=mm)
    res, bound = _bind(elev)
    out = OC.check(_plan() + [DI] + bound + [SECTION] + SCHEDULE)
    return res, out, {r["opening_id"]: r for r in out["openings"]}


def _codes(out, oid=None):
    return sorted(x["code"] for x in out["issues"] if oid is None or x["opening_id"] == oid)


def test_binding_and_elevation_only():
    res, _, _ = _run()
    assert res["mirrored"] is False
    assert sorted(pid for _, pid in res["bound"]) == ["DA", "WA", "WB", "WC"]
    assert abs(res["offset_m"] - (-2.00)) < 1e-9
    assert len(res["unbound_features"]) == 1 and abs(res["unbound_features"][0]["pos_m"] - 13.0) < 1e-9
    only = OC.elevation_only_issues(res["unbound_features"])
    assert [x["code"] for x in only] == ["ELEVATION_ONLY"] and "OPENING_SUPPLY" in only[0]["boq_lines"]


def test_wa_agrees_with_basis_mixed_sill():
    _, out, rows = _run()
    a = rows["WA"]["attrs"]
    assert a["WIDTH"]["verdict"] == "AGREES" and a["SILL"]["verdict"] == "AGREES" and a["HEAD"]["verdict"] == "AGREES"
    sills = sorted(round(x, 6) for _, x in a["SILL"]["values"])
    assert sills == [0.9, 0.9, 0.9]
    assert _codes(out, "WA") == ["HEAD_BASIS_MIXED", "SILL_BASIS_MIXED"]
    assert rows["WA"]["held"] == {}


def test_wb_width_differs_holds_its_lines():
    _, out, rows = _run()
    assert rows["WB"]["attrs"]["WIDTH"]["verdict"] == "DIFFERS"
    assert "WIDTH_DIFFERS" in _codes(out, "WB")
    held = rows["WB"]["held"]
    for line in ("OPENING_M2", "BLOCK_DEDUCTION", "FINISH_DEDUCTION", "REVEAL_ML", "SILL_OR_THRESHOLD_ML", "LINTEL"):
        assert line in held
    det = next(x["detail"] for x in out["issues"] if x["code"] == "WIDTH_DIFFERS")
    assert "spread 0.050" in det


def test_door_kind_agrees_head_single_source():
    _, out, rows = _run()
    a = rows["DA"]["attrs"]
    assert a["KIND"]["verdict"] == "AGREES"
    assert a["HEAD"]["verdict"] == "NOT_COMPARABLE" and "SINGLE_SOURCE" in a["HEAD"]["note"]
    assert "HEAD" not in [x["attr"] for x in out["issues"] if x["opening_id"] == "DA"]


def test_head_not_printed_is_held_never_zero():
    _, out, rows = _run()
    assert "HEAD_NOT_PRINTED" in _codes(out, "WC")
    assert rows["WC"]["attrs"]["HEAD"]["verdict"] == "NOT_SHOWN"
    assert "OPENING_M2" in rows["WC"]["held"] and "LINTEL" in rows["WC"]["held"]
    assert all("area" not in k for k in rows["WC"]["attrs"])          # the check never produces a quantity


def test_missing_from_schedule():
    _, out, rows = _run()
    assert _codes(out, "DI") == ["HEAD_NOT_PRINTED", "MISSING_FROM_LIST"]
    assert rows["DI"]["attrs"]["EXISTENCE"]["verdict"] == "DIFFERS"
    # with no schedule / list in the project at all, nothing is "missing from" it
    out2 = OC.check(_plan() + [DI])
    assert "MISSING_FROM_LIST" not in _codes(out2)


def test_mirrored_elevation_binds_the_same_identities():
    res_n, out_n, _ = _run()
    res_m, out_m, _ = _run(mirror=True)
    assert res_m["mirrored"] is True
    assert ("MIRRORED_VIEW" in [c for c, _ in res_m["issues"]])
    assert sorted(pid for _, pid in res_m["bound"]) == sorted(pid for _, pid in res_n["bound"])
    assert _codes(out_m) == _codes(out_n)
    # declared as not mirrored although it only binds mirrored: flagged
    plan_n = [OC.normalise(o) for o in _plan()]
    feats = [OC.normalise(o) for o in _elev(mirror=True)]
    res = OC.bind(plan_n, feats, declared_mirrored=False)
    assert "ORIENTATION_CONFLICT" in [c for c, _ in res["issues"]]


def test_millimetres_same_result_and_mm_as_metres_refused():
    _, out_m, _ = _run()
    _, out_mm, _ = _run(mm=True)
    assert _codes(out_mm) == _codes(out_m)
    with pytest.raises(ValueError, match="millimetres"):
        OC.normalise(_elev(mm=True, units="m")[0])


def test_symmetric_twins_are_ambiguous():
    plan = _plan([{"opening_id": "T1", "kind": "WINDOW", "width": 1.55, "pos_m": 2.00},
                  {"opening_id": "T2", "kind": "WINDOW", "width": 1.55, "pos_m": 6.00}])
    feats = [{"opening_id": None, "source": "ELEVATION", "ref": "E", "units": "m", "storey": "GF", "facade": "F",
              "pos_m": p, "width": 1.55, "width_basis": "PRINTED"} for p in (3.0, 7.0)]
    res = OC.bind([OC.normalise(o) for o in plan], [OC.normalise(o) for o in feats])
    assert res["bound"] == [] and res["mirrored"] is None
    assert res["issues"][0][0] == "BINDING_AMBIGUOUS"


def test_small_decoy_does_not_steal_a_window():
    """A 0.10 m square drawn 8 mm from a window's centre (kind not stated) must not take the window's identity."""
    plan = _plan([{"opening_id": "WW", "kind": "WINDOW", "width": 2.45, "pos_m": 5.00},
                  {"opening_id": "WS", "kind": "WINDOW", "width": 1.20, "pos_m": 0.00}])
    feats = [{"opening_id": None, "source": "ELEVATION", "ref": "E", "units": "m", "storey": "GF", "facade": "F",
              "pos_m": p, "kind": k, "width": w, "width_basis": "PRINTED" if w else None}
             for p, k, w in ((1.000, "WINDOW", 1.20), (6.000, "WINDOW", 2.45), (6.008, None, None),
                             (5.208, None, None), (6.808, None, None))]
    res = OC.bind([OC.normalise(o) for o in plan], [OC.normalise(o) for o in feats])
    got = {round(f["pos_m"], 3): pid for f, pid in res["bound"]}
    assert got == {1.0: "WS", 6.0: "WW"}
    assert len(res["unbound_features"]) == 3
    # without the printed widths, two windows read mirrored fit as well: AMBIGUOUS, nothing bound (never a guess)
    bare = [dict(f, width=None, width_basis=None) for f in feats]
    res = OC.bind([OC.normalise(o) for o in plan], [OC.normalise(o) for o in bare])
    assert res["bound"] == [] and res["issues"][0][0] == "BINDING_AMBIGUOUS"


def test_curved_bay_chord_vs_arc():
    plan = {"opening_id": "CB", "source": "PLAN", "ref": "A-102", "units": "m", "kind": "WINDOW", "width": 3.29,
            "width_basis": "ARC_OUTER", "chord_m": 2.692}
    elev_ok = {"opening_id": "CB", "source": "ELEVATION", "ref": "A-202", "units": "mm", "kind": "WINDOW",
               "width": 2691.5, "width_basis": "PROJECTED_CHORD"}
    out = OC.check([plan, elev_ok])
    a = out["openings"][0]["attrs"]["WIDTH"]
    assert a["verdict"] == "AGREES" and set(a["values"]) == {"ARC_OUTER", "PROJECTED_CHORD"}
    assert "never compared" in a["note"]                                   # 3.29 is not compared with 2.69
    bad = dict(elev_ok, width=2800)
    out = OC.check([plan, bad])
    assert out["openings"][0]["attrs"]["WIDTH"]["verdict"] == "DIFFERS"


def test_list_with_raw_chain_part_differs_from_the_sheet():
    elev = {"opening_id": "W9", "source": "ELEVATION", "ref": "E-1", "units": "m", "kind": "WINDOW", "sill": 2.00,
            "head": 4.00, "level_basis": "LEVEL", "ffl": 1.00}
    census = {"opening_id": "W9", "source": "CENSUS", "ref": "hand list", "units": "m", "kind": "WINDOW",
              "sill": 1.85, "head": 3.85, "level_basis": "ABOVE_FFL"}
    out = OC.check([dict(DI, opening_id="W9", kind="WINDOW"), elev, census])
    codes = _codes(out, "W9")
    assert "SILL_LIST_DIFFERS" in codes and "HEAD_LIST_DIFFERS" in codes
    row = out["openings"][0]
    assert row["attrs"]["SILL"]["verdict"] == "NOT_COMPARABLE"          # the list confirms nothing
    # the same census row stated on its true basis (a chain part from +0.15) agrees
    census_ok = dict(census, sill=1.85, head=3.85, level_basis="CHAIN_PART", chain_base=0.15, ffl=1.00)
    out = OC.check([dict(DI, opening_id="W9", kind="WINDOW"), elev, census_ok])
    assert "SILL_LIST_DIFFERS" not in _codes(out, "W9")


def test_cut_view_is_not_shown_but_omission_differs():
    base = [dict(DI, opening_id="W7", kind="WINDOW")]
    cut = {"opening_id": "W7", "source": "ELEVATION", "ref": "E-2", "units": "m", "drawn": False,
           "hidden": "drawn as a section: wall cut away"}
    out = OC.check(base + [cut])
    assert "NOT_DRAWN_ON_SOURCE" not in _codes(out, "W7")
    assert out["openings"][0]["attrs"]["EXISTENCE"]["verdict"] == "AGREES"
    omitted = dict(cut, hidden=None)
    out = OC.check(base + [omitted])
    assert "NOT_DRAWN_ON_SOURCE" in _codes(out, "W7")


def test_not_in_plan():
    el = {"opening_id": "X1", "source": "ELEVATION", "ref": "E-3", "units": "m", "kind": "WINDOW", "width": 1.0,
          "width_basis": "PRINTED"}
    out = OC.check([el])
    assert "NOT_IN_PLAN" in _codes(out, "X1")


@pytest.mark.parametrize("bad, msg", [
    (dict(SECTION, inferred=True), "INFERRED"),
    ({"opening_id": "Q", "source": "ELEVATION", "ref": "E", "units": "m", "sill": 2.0, "level_basis": "LEVEL"}, "ffl"),
    ({"opening_id": "Q", "source": "ELEVATION", "ref": "E", "units": "m", "sill": 2.0}, "level basis"),
    ({"opening_id": "Q", "source": "ELEVATION", "ref": "E", "units": "m", "width": 1.0}, "basis"),
    ({"opening_id": "Q", "source": "ELEVATION", "ref": "E", "width": 1.0, "width_basis": "PRINTED"}, "units"),
    ({"opening_id": "Q", "source": "PHOTO", "ref": "E", "units": "m"}, "source"),
    ({"opening_id": "Q", "source": "ELEVATION", "units": "m"}, "ref"),
    ({"opening_id": "Q", "source": "ELEVATION", "ref": "E", "units": "m", "sill": 0.9,
      "level_basis": "CHAIN_PART", "ffl": 0.45}, "chain_base"),
])
def test_guards(bad, msg):
    with pytest.raises(ValueError, match=msg):
        OC.normalise(bad)


def test_duplicate_observation_and_unbound_refused():
    with pytest.raises(ValueError, match="two observations"):
        OC.check([SECTION, dict(SECTION)])
    with pytest.raises(ValueError, match="bind"):
        OC.check(_elev())
