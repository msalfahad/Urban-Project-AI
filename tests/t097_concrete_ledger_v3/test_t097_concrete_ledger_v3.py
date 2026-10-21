"""T-097: CONCRETE_LEDGER_V3 (engine.source.concrete_ledger_v3) end to end on synthetic structural villas (NOT a client
drawing): tools/synthetic_villa + the hand cases of fixture.py, through the frozen route G (conventions V6,
completeness on) and the V3 ledger. Hand truth from the DESIGN numbers (fixture.plan), never from engine output:

  seed 3 (mm), planted P.C 20x60 in B1 (0.20 x 0.50) on line y 4.70: clear span 13.40 - 8.90 = 4.50 m
      V3 one span 4.50 x 0.20 x 0.50 = 0.450 m3 (V1: two pieces, the untagged one HELD across the 'support')
  seed 7 (m),  planted P.C 25x50 in B5 (0.25 x 0.50): clear 12.80 - 7.85 = 4.95 m -> 4.95 x 0.25 x 0.50 = 0.61875 m3
  rings (both seeds), B1 0.20 x 0.50, ri 1.00, ro 1.20: annulus pi (1.44 - 1.00) = 1.382301 m2 -> x 0.50 = 0.691150 m3
      R1 (arcs, B1 printed): replaces its four arc-band items; R2 (inner face a CIRCLE, no mark): HELD unless an
      owner rule is passed, then OWNER_RULE 0.691150 m3
  upstand 0.10 x 0.15 printed in SECTION A-A on the cut span: seed 3 B3 span 4.50 - 0.15 = 4.35 m -> 0.065250 m3;
      seed 7 B1 span 4.125 - 0.15 = 3.975 m -> 0.059625 m3
  The ring is polygonised (256 segments per quarter) by the binder: its net plan may fall short of the exact annulus by
  under 1e-4 m2 (seen 9e-6), the only tolerance used below.
Each villa also runs mirrored (x -> -x). Every other concrete item must stay the route's own item."""
from __future__ import annotations

import math
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import concrete_ledger_v3 as V3          # noqa: E402
from engine.source import provisional_estimate as PE        # noqa: E402
from tests.t097_concrete_ledger_v3 import fixture as FX     # noqa: E402
from tools import urban_boq_m2 as M2                        # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CONV = str(ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json")
RING_TOL_M2 = 1e-4
_CACHE = {}


def run(tmp_root, seed, *, mirror=False, ring_rule=True, **kw):
    key = (seed, mirror, ring_rule, tuple(sorted(kw.items())))
    if key in _CACHE:
        return _CACHE[key]
    d = tmp_root / f"s{seed}_{int(mirror)}_{int(ring_rule)}_{'_'.join(f'{k}{v}' for k, v in sorted(kw.items()))}"
    d.mkdir(parents=True, exist_ok=True)
    src = d / "villa.dxf"
    D, T = FX.write(seed, str(src), **kw)
    path = src
    if mirror:
        path = d / "villa_mirror.dxf"
        FX.mirror_dxf(str(src), str(path))
    R = M2.compute([str(path)], conventions=CONV, route="G", completeness=True)
    rule = {"family": "BEAM", "mark": T["rings"][1]["mark"], "storey": "GF", "basis": "test: owner rule"} \
        if ring_rule else None
    v3 = V3.measure(R, ring_rule=rule)
    items = V3.apply(R, v3)
    _CACHE[key] = (D, T, R, v3, items)
    return _CACHE[key]


@pytest.fixture(scope="module")
def tmp_root(tmp_path_factory):
    return tmp_path_factory.mktemp("t097")


VARIANTS = [(3, False), (7, False), (3, True)]


def _gf(v3):
    return next(s for s in v3["sheets"] if s["storey"] == "GF")


def _by_id(items):
    return {i["item_id"]: i for i in items}


@pytest.mark.parametrize("seed,mirror", VARIANTS)
def test_replay_reproduces_the_route_before_changing_anything(tmp_root, seed, mirror):
    _, _, R, v3, _ = run(tmp_root, seed, mirror=mirror)
    plans = [s for s in R["generic"]["D"]["sheets"].values() if s["sheet"]["role"] in V3.PLAN_ROLES]
    assert len(v3["sheets"]) == len(plans) >= 2
    assert all(s["state"] == "REPLAYED" for s in v3["sheets"])
    assert v3["side_effects"] == []                    # no non-beam concrete item moves


@pytest.mark.parametrize("seed,mirror", VARIANTS)
def test_planted_column_no_longer_splits_its_beam(tmp_root, seed, mirror):
    _, T, R, v3, items = run(tmp_root, seed, mirror=mirror)
    p = T["planted"]
    gf = _gf(v3)
    assert [x["state"] for x in gf["planted"]] == ["LINKED"]
    ch = [m for m in gf["marks_changed"] if m["mark"] == p["beam"]]
    assert len(ch) == 1 and len(ch[0]["v1"][1]) == 1 and len(ch[0]["v2"][1]) == 1
    v1_piece, v2_band = ch[0]["v1"][1][0], ch[0]["v2"][1][0]
    parent = v1_piece.split(".")[0]
    assert v2_band == parent                           # one whole span, no split
    route = [i for i in R["items"] if i["trade"] == "CONCRETE" and i["component_id"].startswith(f"BEAMS:GF:{parent}.")]
    assert sorted(i["category"] for i in route) == ["PROVISIONAL", "UNRESOLVED"]
    assert [i["blocker"] for i in route if i["category"] == "UNRESOLVED"] == ["UNLABELLED_SPAN_ACROSS_SUPPORT"]
    new = [i for i in items if i["trade"] == "CONCRETE" and i["component_id"] in (f"BEAMS:GF:{parent}",)]
    assert len(new) == 1 and new[0]["category"] == "PROVISIONAL"
    assert new[0]["base"] == pytest.approx(p["v3_m3"], abs=1e-6)          # clear span x B x H, by hand
    assert not [i for i in items if i["trade"] == "CONCRETE" and i["component_id"].startswith(f"BEAMS:GF:{parent}.")]


@pytest.mark.parametrize("seed,mirror", VARIANTS)
def test_rings_printed_mark_and_owner_rule(tmp_root, seed, mirror):
    _, T, R, v3, items = run(tmp_root, seed, mirror=mirror)
    hand = T["rings"][0]
    rings = {r["state"]: r for r in v3["rings"] if r["storey"] == "GF"}
    assert set(rings) == {"PRINTED_MARK", "OWNER_RULE"}
    for st, r in rings.items():
        assert r["mark"] == hand["mark"]
        assert r["annulus_m2"] == pytest.approx(hand["annulus_m2"], abs=1e-6)
        assert 0 <= hand["annulus_m2"] - r["net_plan_m2"] <= RING_TOL_M2
    pm = rings["PRINTED_MARK"]
    assert len(pm["arc_bands"]) == 4 and rings["OWNER_RULE"]["arc_bands"] == []
    ids = _by_id(items)
    ring_items = [i for i in items if ":RING" in i["component_id"]]
    assert len(ring_items) == 2
    for it in ring_items:
        assert it["category"] == "PROVISIONAL" and it["assumptions"] == ["BEAM_DEPTH_READING"]
        assert it["base"] == pytest.approx(hand["v_m3"], abs=RING_TOL_M2 * hand["H"])
    # the printed ring's arc-band items are gone (superseded), none of them left beside the ring line
    for b in pm["arc_bands"]:
        assert not [i for i in ids.values() if i["component_id"] == f"BEAMS:GF:{b}" and i["trade"] == "CONCRETE"]


def test_ring_without_mark_or_rule_is_held_and_listed(tmp_root):
    _, T, R, v3, items = run(tmp_root, 3, ring_rule=False)
    held = [r for r in v3["rings"] if r["state"] == "HELD"]
    assert len(held) == 1 and held[0]["why"] == "no mark printed on this ring"
    assert held[0]["annulus_m2"] == pytest.approx(T["rings"][1]["annulus_m2"], abs=1e-6)   # listed with its size
    assert len([i for i in items if ":RING" in i["component_id"]]) == 1                    # only the printed one


@pytest.mark.parametrize("seed,mirror", VARIANTS)
def test_upstand_from_the_printed_section(tmp_root, seed, mirror):
    _, T, R, v3, items = run(tmp_root, seed, mirror=mirror)
    s = T["section"]
    assert v3["sections"]["A"]["state"] == "READ"
    up = v3["upstands"]
    assert len(up) == 1 and up[0]["state"] == "MEASURED"
    assert (up[0]["w_m"], up[0]["h_m"]) == (pytest.approx(s["w"]), pytest.approx(s["h"]))
    assert up[0]["length_m"] == pytest.approx(s["clear"], abs=1e-6)
    assert up[0]["side"] == ("FLUSH_LEFT" if mirror else "FLUSH_RIGHT")
    it = _by_id(items)[up[0]["item_id"]]
    assert it["category"] == "PROVISIONAL" and it["base"] == pytest.approx(s["v_m3"], abs=1e-9)
    assert up[0]["rows_fitting_section"] == [s["beam"]]


def test_upstand_height_not_printed_is_held_never_zero(tmp_root):
    _, T, R, v3, items = run(tmp_root, 3, print_h=False)
    up = v3["upstands"]
    assert len(up) == 1 and up[0]["state"] == "HELD" and "volume_m3" not in up[0]
    it = _by_id(items)[up[0]["item_id"]]
    assert it["category"] == "UNRESOLVED" and it["base"] is None and it["blocker"].startswith("UPSTAND_HELD")


def test_planted_label_without_leader_changes_nothing(tmp_root):
    _, T, R, v3, items = run(tmp_root, 3, leader=False, cases=("P",))
    gf = _gf(v3)
    assert [x["state"] for x in gf["planted"]] == ["NO_LEADER"]
    assert gf["bands_v1"] == gf["bands_v2"] and gf["marks_changed"] == []
    conc = lambda L: sorted((i["item_id"], i["category"], i["base"]) for i in L if i["trade"] == "CONCRETE"  # noqa
                            and i["family"] in V3.BEAM_ITEM_FAMILIES)
    assert conc(items) == conc(R["items"])             # the beam stays split, its untagged piece held


@pytest.mark.parametrize("seed,mirror", VARIANTS)
def test_every_other_item_is_the_routes_own(tmp_root, seed, mirror):
    _, T, R, v3, items = run(tmp_root, seed, mirror=mirror)
    gone = set(v3["supersedes"])
    v2_gone = set((v3.get("v2") or {}).get("supersedes") or [])
    new_ids = {i["item_id"] for i in v3["beam_items"]} | {i["item_id"] for i in (v3.get("v2") or {}).get("items", [])}
    ids = _by_id(items)
    for it in R["items"]:
        if it["item_id"] in gone or it["item_id"] in v2_gone:
            continue
        assert ids.get(it["item_id"]) == it                       # untouched, byte for byte
    for k, it in ids.items():
        assert k in new_ids or k in {i["item_id"] for i in R["items"]}
    # held lines carry no number; released lines carry one (missing never 0)
    for it in items:
        if it["category"] == "UNRESOLVED":
            assert it["base"] is None and it["blocker"]
        else:
            assert it["base"] is not None
    PE.check(items, R["conv"])


@pytest.mark.parametrize("seed,mirror", [(3, False), (7, False)])
def test_untagged_span_and_missing_type_stay_held(tmp_root, seed, mirror):
    """the generator's own hard cases: the untagged second span of line 0 (collinear with a tagged span across a
    column: owner Q-16 A, no neighbour's section) and, on seed 7, a beam type printed on the plan but missing from
    the schedule (no section printed): both stay HELD with the route's reasons."""
    _, T, R, v3, items = run(tmp_root, seed, mirror=mirror)
    held = lambda L: sorted((i["item_id"], i["blocker"]) for i in L if i["trade"] == "CONCRETE" and   # noqa
                            i["family"] == "BEAMS" and i["category"] == "UNRESOLVED")
    before, after = held(R["items"]), held(items)
    planted_parent = next(m for m in _gf(v3)["marks_changed"] if m["mark"] == T["planted"]["beam"])["v2"][1][0]
    expect = [h for h in before if f":{planted_parent}." not in h[0] and ":BAND" in h[0]
              and not any(h[0].endswith(f":{b}") for r in v3["rings"] for b in r.get("arc_bands") or ())]
    assert [h for h in after if ":RING" not in h[0] and ":UPSTAND" not in h[0]] == expect
    assert any(b == "UNLABELLED_SPAN_ACROSS_SUPPORT" for _, b in after)


def test_replay_mismatch_keeps_the_sheet(tmp_root):
    _, _, R, _, _ = run(tmp_root, 3)
    D = R["generic"]["D"]
    sid = next(k for k, s in D["sheets"].items() if s["sheet"]["role"] == "SLAB_PLAN")
    bad = dict(D, sheets=dict(D["sheets"], **{sid: dict(D["sheets"][sid], bands=D["sheets"][sid]["bands"][1:])}))
    rp = V3.replay_sheet(bad, R["generic"]["intake"], sid, R["conv"])
    assert rp["state"] == "REPLAY_MISMATCH" and rp["bands_same"] is False and "rec_v2" not in rp


def test_ring_rule_must_name_its_basis(tmp_root):
    _, _, R, _, _ = run(tmp_root, 3)
    with pytest.raises(V3.LedgerError):
        V3.measure(R, ring_rule={"family": "BEAM", "mark": "B1"})


def _it(cid, cat="UNRESOLVED", blocker="X"):
    return PE.item(item_id=f"U-C:{cid}", component_id=cid, trade="CONCRETE", family="COLUMNS", storey="GF",
                   category=cat, support="NO_GEOMETRY", confidence="LOW", blocker=blocker, source="t")


def test_neck_only_type_column_not_present_neck_held_with_section():
    """unit case of the neck rule on hand records (classify() output shape): a column-plan occurrence of a NECK_ONLY
    type leaves as NOT_PRESENT; its foundation neck stays HELD and gains the printed 0.30 x 0.30 = 0.09 m2 section;
    an occurrence of another type and a released item are untouched."""
    items = [_it("COL:SH9:CX@1,2", blocker="TYPE_NOT_IN_SCHEDULE"), _it("NECK:COL:SH8:CX@5,6"),
             _it("COL:SH9:C1@3,4", blocker="Y")]
    lines = [{"member_id": "COL:SH9:CX@1,2", "role": "COLUMN_PLAN", "status": "NOT_PRESENT", "code": "NECK_ONLY_TYPE",
              "why": "levels struck", "struck": ["GF", "1F"]},
             {"member_id": "COL:SH8:CX@5,6", "role": "FOUNDATION_PLAN", "status": "HELD",
              "code": "FOUNDATION_DATUM_NOT_VERIFIED", "why": "h", "section_m": [0.30, 0.30], "section_m2": 0.09}]
    new, sup, gone = V3._neck_items(items, lines, "t")
    assert sup == ["U-C:COL:SH9:CX@1,2", "U-C:NECK:COL:SH8:CX@5,6"]
    assert [g["status"] for g in gone] == ["NOT_PRESENT"] and gone[0]["struck"] == ["GF", "1F"]
    assert len(new) == 1 and new[0]["category"] == "UNRESOLVED" and new[0]["base"] is None
    assert new[0]["dimensions"]["section_m2"] == pytest.approx(0.09)
    assert new[0]["blocker"].startswith("FOUNDATION_DATUM_NOT_VERIFIED")


def test_policy_record():
    r = V3.policy_record()
    assert r["policy"] == "CONCRETE_LEDGER_V3" and "engine/source/generic_route.py" in r["frozen_untouched"]
    assert math.isfinite(len(r["rule"]))
