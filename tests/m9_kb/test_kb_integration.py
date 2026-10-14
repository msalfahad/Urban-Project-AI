"""Phase 2B-1 WP-5: ARCH_TAKEOFF_V2.3 end to end on the synthetic villa - V2.3 changes only what a registry rule
names, never a measured dimension; it is deterministic and invariant under moving, mirroring and turning the plan;
an assumption is never released as confirmed; V2.2 and earlier never read the registry."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import kb_fixtures as KF                                      # noqa: E402
from engine.source import boq_line as BL                      # noqa: E402
from engine.source import knowledge as K                      # noqa: E402
from tools import arch_synth as AS                            # noqa: E402

V22, V23 = "ARCH_TAKEOFF_V2.2", "ARCH_TAKEOFF_V2.3"
NEW_CODES = {"FIN.MARBLE.THRESHOLD"}
STRIP = ("doorway strip", "marble threshold")


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("villa")
    return {"tmp": tmp, "v22": KF.villa_run(tmp, V22), "v23": KF.villa_run(tmp, V23),
            "v23_again": KF.villa_run(tmp, V23),
            "v22_h": KF.villa_run(tmp, V22, facts=KF.FX.HEIGHT_FACTS),
            "v23_h": KF.villa_run(tmp, V23, facts=KF.FX.HEIGHT_FACTS)}


def _wet_rooms(arch):
    return {r["room_id"] for r in arch["rooms"] if (r.get("finish_scope") or {}).get("scope") == "WET"}


def _key(ln):
    return (ln["location"].get("room_id"), ln["item_code"], ln.get("physical_element"))


@pytest.mark.parametrize("pair", [("v22", "v23"), ("v22_h", "v23_h")])
def test_v2_3_changes_only_the_lines_the_registry_names(runs, pair):
    """outside the owner wet-area rooms, the doorway strips and the door / passage jamb lines, every V2.2 line is
    in V2.3 unchanged (quantity, state, formula inputs); every V2.3-only line names a registry rule."""
    (r22, _a22), (r23, a23) = runs[pair[0]], runs[pair[1]]
    wet = _wet_rooms(a23)
    a = {_key(ln): ln for ln in r22["lines"]}
    b = {_key(ln): ln for ln in r23["lines"]}
    for k, ln in a.items():
        rid = k[0] or ""
        if rid in wet or "-STRIP-" in rid or ln["item_code"] in ("ARCH.THRESHOLD",):
            continue
        assert k in b, k
        assert (b[k]["measured_net"], b[k]["evidence_state"]) == (ln["measured_net"], ln["evidence_state"]), k
    new = [b[k] for k in b if k not in a]
    rules = {r["rule_id"] for r in K.registry()["rules"]} | {"UP-CER-004", "UP-WP-001", "UP-WP-002", "UP-WP-003",
                                                             "UP-CER-009", "UP-CER-001"}
    for ln in new:
        rid = ln["location"].get("room_id") or ""
        assert (ln.get("rule") or {}).get("rule_id") in rules or rid in wet, _key(ln)
    assert NEW_CODES <= {ln["item_code"] for ln in new}


def test_no_drawn_dimension_is_replaced(runs):
    """the rooms, openings and door elements V2.3 measures are the V2.2 ones (areas, widths, wall thicknesses)."""
    (_r, a22), (_r3, a23) = runs["v22"], runs["v23"]
    dims = lambda a: sorted((r["room_id"], r.get("area_m2"), r.get("perimeter_lm")) for r in a["rooms"])  # noqa: E731
    assert dims(a22) == dims(a23)
    ops = lambda a: sorted((o["floor"], o["opening_id"], o["kind"], o["width_m"], o.get("wall_t_m"))      # noqa: E731
                           for o in a["openings"])
    assert ops(a22) == ops(a23)
    doors = lambda a: sorted((e["element_id"], e.get("structural_opening_width_m")) for e in a["doors"]["elements"])  # noqa
    assert doors(a22) == doors(a23)


def test_v2_3_is_deterministic(runs):
    """two runs of the same drawing file: the same lines, scenarios and questions."""
    a, b = runs["v23"], runs["v23_again"]
    dump = lambda r: json.dumps([r[0]["lines"], r[1]["door_scenarios"], r[1]["owner_questions"],      # noqa: E731
                                 r[1]["space_model"], r[1]["elevator_schedule"], r[1]["ledger"]["summary"]],
                                sort_keys=True, default=str)
    assert dump(a) == dump(b)


def _profile(run):
    room, arch = run
    lines = Counter((ln["item_code"], ln.get("physical_element") if ln.get("physical_element") in STRIP + (
        "door jambs and head", "passage jambs", "paint above wall tile") else "-", ln["evidence_state"],
        None if ln["measured_net"] is None else round(ln["measured_net"], 4)) for ln in room["lines"]
        if not ln["item_code"].startswith(("ARCH.WINDOW", "ARCH.DOOR", "ARCH.PASSAGE", "DOOR.")))
    views = {k: v for k, v in arch["door_scenarios"]["views"].items() if k != "note"}
    return lines, views, arch["owner_questions"]["summary"], arch["space_model"]["summary"]


@pytest.mark.parametrize("variant", [{"dx": 731.0, "dy": -412.0}, {"mirror": True}, {"quarter_turns": 1}],
                         ids=["translate", "mirror", "turn"])
def test_v2_3_is_invariant_under_moving_mirroring_and_turning(runs, tmp_path, variant):
    """metamorphic: the V2.3 quantities, door views, question groups and space statuses of the villa do not change
    when its contents are moved, mirrored or turned inside the sheet frames."""
    p = tmp_path / "villa_x.dxf"
    AS.villa(p, **variant)
    other = KF.drawing_run(p, V23)
    base, moved = _profile(runs["v23"]), _profile(other)
    assert base[0] == moved[0]
    assert base[1] == moved[1] and base[2] == moved[2] and base[3] == moved[3]


def test_an_assumption_is_never_released_as_confirmed(runs):
    """a quantity on an owner fallback height is PROVISIONAL (or a count); assumed door areas live in the scenario
    views only; no released quantity is negative; the ledger finds no confirmed omission."""
    for key in ("v23", "v23_h"):
        room, arch = runs[key]
        for ln in room["lines"]:
            i = (ln.get("calculation") or {}).get("inputs") or {}
            assumed = i.get("height_state") == "ASSUMED" or "HEIGHT_ASSUMED" in (ln.get("notes") or "")
            if assumed and ln["measured_net"] is not None:
                assert ln["evidence_state"] == "PROVISIONAL" or ln["unit"] in ("no", "nr", "pcs"), _key(ln)
            if ln["evidence_state"] in BL.QUANTITY_STATES and ln["measured_net"] is not None:
                assert ln["measured_net"] >= 0, _key(ln)
        for r in arch["door_scenarios"]["rows"]:
            for side in ("as_drawn", "owner_required"):
                ar = r[side]["wall_opening_area"]
                if r["as_drawn"]["height"]["state"] == "ASSUMED" and ar["m2"] is not None:
                    assert ar["state"] != "CONFIRMED"
        assert arch["ledger"]["summary"]["confirmed_missing"] == 0
        assert arch["ledger"]["summary"]["conservation"]["ok"]


def test_the_owner_required_view_never_reaches_the_boq_lines(runs):
    """the enlarged wall openings are a proposed modification (scenario view); the BOQ lines keep the drawn doors."""
    room, arch = runs["v23"]
    rows = arch["door_scenarios"]["rows"]
    assert any(r["review_status"] == "MODIFICATION_PROPOSED_NOT_APPROVED" for r in rows)
    drawn = sorted(round(e["structural_opening_width_m"], 3) for e in arch["doors"]["elements"] if e["released"])
    assert drawn == sorted(round(r["as_drawn"]["cad_wall_opening_m"], 3) for r in rows if r["view"] == "AS_DRAWN")
    sc = arch["boq_scenarios"]
    assert sc["never"].startswith("the AS_DRAWN and OWNER_REQUIRED views added together")
    assert sc["OWNER_REQUIRED"]["doors_with_enlargement"] == sum(1 for r in rows if r["view"] == "AS_DRAWN" and
                                                                  r["review_status"] != "NO_MODIFICATION")


def test_v2_2_never_reads_the_registry(runs, monkeypatch):
    """a different registry (every door standard 2.00 m, no wet areas) leaves V2.2 unchanged and changes V2.3."""
    reg = json.loads(json.dumps(K.registry()))
    for r in reg["rules"]:
        if r["rule_id"] == "UP-DOOR-OPEN-002":
            for v in r["logic"]["table"].values():
                v.update(required_nominal_door_m=1.90, required_wall_opening_m=2.00)
    monkeypatch.setattr(K, "_load", lambda: reg)
    v22 = KF.villa_run(runs["tmp"], V22)                          # the same drawing file as runs["v22"]
    assert json.dumps(v22[0]["lines"], sort_keys=True) == json.dumps(runs["v22"][0]["lines"], sort_keys=True)
    v23 = KF.villa_run(runs["tmp"], V23)
    assert {r["owner_required"]["owner_required_wall_opening_m"] for r in v23[1]["door_scenarios"]["rows"]
            if r["category"] == "INTERNAL_PVC"} == {2.0}
