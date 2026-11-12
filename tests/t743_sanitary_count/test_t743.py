"""T-743: B12-01 sanitary fixtures and floor drains, research/agents_t743/t743_census.py (not wired).

Hand-made synthetic villa N743 (not the development villa), plan in metres, one floor 'GF':
  B1 bathroom  x 0.0 .. 2.4, y 0.0 .. 2.0   WC (0.40, 1.60), basin (1.90, 1.70), shower tray (0.50, 0.50),
                                             floor drain 4in (1.20, 0.60) drawn on the SANITARY sheet only
  B2 bathroom  x 2.6 .. 5.0, y 0.0 .. 2.0   B1 mirrored about x = 2.50: WC (4.60, 1.60), basin (3.10, 1.70),
                                             tray (4.50, 0.50); no drain on either sheet
  K1 kitchen   x 0.0 .. 3.0, y 2.2 .. 5.0   nothing drawn on either sheet
ARCH sheet: the B1 basin block (real linework) and a block named 'WC' at the B1 WC that holds only text (a room tag).
SANITARY sheet: every fixture above, in sheet pixels: u = (x + 2) / 0.025, v = (8 - y) / 0.025.
HAND TRUTH (pcs): WC 2, BASIN 2 (the B1 basin is on both sheets: ONE fixture), SHOWER_TRAY 2, FLOOR_DRAIN 1 (4in);
HELD: KITCHEN_SINK 1 (K1 needs one, neither sheet draws one: pcs None, never 0). The 'WC' tag is no fixture.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t743"))
import t743_census as C  # noqa: E402

ROOMS = [
    C.Room("B1", "GF", [(0.0, 0.0), (2.4, 0.0), (2.4, 2.0), (0.0, 2.0)], ("BATHROOM",)),
    C.Room("B2", "GF", [(2.6, 0.0), (5.0, 0.0), (5.0, 2.0), (2.6, 2.0)], ("BATHROOM",)),
    C.Room("K1", "GF", [(0.0, 2.2), (3.0, 2.2), (3.0, 5.0), (0.0, 5.0)], ("KITCHEN",)),
]
PLAN = [  # kind, plan point, drain size
    (C.WC, (0.40, 1.60), None), (C.BASIN, (1.90, 1.70), None), (C.SHOWER_TRAY, (0.50, 0.50), None),
    (C.FLOOR_DRAIN, (1.20, 0.60), 4),
    (C.WC, (4.60, 1.60), None), (C.BASIN, (3.10, 1.70), None), (C.SHOWER_TRAY, (4.50, 0.50), None),
]
ANCHORS = [(0.0, 0.0), (5.0, 2.0), (2.4, 2.0)]          # room corners shared by both sheets


def to_sheet(x, y, *, mirror=False, rotate=False):
    u, v = (x + 2.0) / 0.025, (8.0 - y) / 0.025
    if rotate:
        u, v = v, u
    return (-u if mirror else u), v


def arch_inserts(at_basin=(1.90, 1.70)):
    return [{"name": "WASH2", "kind": C.BASIN, "entity_types": ["ARC", "LINE", "CIRCLE"], "at_m": at_basin,
             "floor": "GF"},
            {"name": "WC", "kind": C.WC, "entity_types": ["TEXT", "TEXT"], "at_m": (0.40, 1.60), "floor": "GF"},
            {"name": "DOOR1", "kind": None, "entity_types": ["ARC", "LINE"], "at_m": (1.0, 2.0), "floor": "GF"}]


def sanitary(plan=PLAN, *, mirror=False, rotate=False):
    pairs = [(to_sheet(*p, mirror=mirror, rotate=rotate), p) for p in ANCHORS]
    fit, res = C.fit_sheet(pairs, mirror_x=mirror)
    C.check_fit(res)
    out = []
    for i, (k, p, size) in enumerate(plan, 1):
        out.append(C.Symbol(kind=k, at_m=fit.to_plan(*to_sheet(*p, mirror=mirror, rotate=rotate)),
                            source=C.SANITARY, floor="GF", ref=f"S{i}", size_in=size))
    return out


def run(arch=None, san=None, read=("GF",)):
    a, tags = C.fixture_symbols(arch_inserts() if arch is None else arch)
    return C.census(ROOMS, a, sanitary() if san is None else san, sanitary_floors_read=set(read)), tags


def recon(c, rid, kind):
    return sorted(x["status"] + ("" if x["status"] == C.AGREE else ":" + x["cause"])
                  for x in c.rooms[rid]["recon"] if x["kind"] == kind)


# ------------------------------------------------------------------------------------------------------- NORMAL
def test_normal_counts_once_per_physical_fixture():
    c, tags = run()
    assert c.totals == {C.WC: 2, C.BASIN: 2, C.SHOWER_TRAY: 2, C.FLOOR_DRAIN: 1}
    assert c.held_totals == {C.KITCHEN_SINK: 1}
    assert c.drains_by_size == {"4in": 1}
    assert tags == {"WC": 1}                                  # the room tag is no WC
    assert c.unassigned == []


def test_normal_reconciliation_names_the_cause():
    c, _ = run()
    assert recon(c, "B1", C.BASIN) == [C.AGREE]               # arch + sanitary twin = one basin
    assert recon(c, "B2", C.BASIN) == [C.SANITARY_ONLY + ":" + C.CAUSE_ARCH_MISSING_HERE]
    assert recon(c, "B1", C.WC) == [C.SANITARY_ONLY + ":" + C.CAUSE_ARCH_DRAWS_NO_KIND]
    assert recon(c, "B1", C.FLOOR_DRAIN) == [C.SANITARY_ONLY + ":" + C.CAUSE_ARCH_DRAWS_NO_KIND]
    assert recon(c, "B2", C.FLOOR_DRAIN) == []                # no drain drawn: nothing invented
    b1 = {f["kind"]: f for f in c.rooms["B1"]["fixtures"]}
    assert b1[C.BASIN]["sources"] == [C.ARCH, C.SANITARY]


def test_normal_kitchen_without_sink_is_held_never_zero():
    c, _ = run()
    (h,) = c.rooms["K1"]["held"]
    assert h["kind"] == C.KITCHEN_SINK and h["state"] == "HELD" and h["pcs"] is None
    assert C.KITCHEN_SINK not in c.totals


def test_normal_mirrored_bathrooms_count_alike():
    c, _ = run()
    k = lambda rid: sorted(f["kind"] for f in c.rooms[rid]["fixtures"] if f["kind"] != C.FLOOR_DRAIN)  # noqa: E731
    assert k("B1") == k("B2") == sorted([C.WC, C.BASIN, C.SHOWER_TRAY])


def test_normal_mirrored_sheet_with_mirror_fit_gives_the_same_census():
    c0, _ = run()
    c1, _ = run(san=sanitary(mirror=True))
    assert C.table(c0) == C.table(c1)


def test_normal_double_vanity_is_two_basins_not_three_or_one():
    plan = [(C.BASIN, (1.60, 1.70), None), (C.BASIN, (2.20, 1.70), None)]
    c, _ = run(arch=arch_inserts(at_basin=(1.62, 1.70)), san=sanitary(plan))
    assert c.totals[C.BASIN] == 2
    assert recon(c, "B1", C.BASIN) == [C.AGREE, C.SANITARY_ONLY + ":" + C.CAUSE_ARCH_MISSING_HERE]


def test_fit_recovers_the_hand_transform():
    pairs = [(to_sheet(*p), p) for p in ANCHORS]
    fit, res = C.fit_sheet(pairs)
    assert fit.s == pytest.approx(0.025) and fit.a == pytest.approx(-2.0) and fit.b == pytest.approx(8.0)
    assert max(res) < 1e-9


# ------------------------------------------------------------------------------------------------------ ADVERSE
def test_adverse_rotated_sheet_is_refused_not_placed():
    with pytest.raises(ValueError):
        sanitary(rotate=True)


def test_adverse_mirrored_sheet_without_mirror_is_refused():
    pairs = [(to_sheet(*p, mirror=True), p) for p in ANCHORS]
    with pytest.raises(ValueError):
        f, res = C.fit_sheet(pairs)
        C.check_fit(res)


def test_adverse_units_mm_symbol_is_unassigned_held_not_counted_twice():
    c, _ = run(arch=arch_inserts(at_basin=(1900.0, 1700.0)))   # a mm point passed as metres
    assert c.totals[C.BASIN] == 2                              # the sanitary basins still count once each
    assert c.unassigned and c.unassigned[0]["state"] == "HELD"
    assert c.held_totals.get("UNASSIGNED_" + C.BASIN) == 1
    assert recon(c, "B1", C.BASIN) == [C.SANITARY_ONLY + ":" + C.CAUSE_ARCH_MISSING_HERE]


def test_adverse_sanitary_floor_not_read():
    c, _ = run(san=[], read=())
    assert c.totals == {C.BASIN: 1}
    assert recon(c, "B1", C.BASIN) == [C.ARCH_ONLY + ":" + C.CAUSE_SAN_NOT_READ]


def test_adverse_untyped_symbol_is_held_never_a_default_type():
    plan = PLAN + [(C.UNTYPED, (3.80, 1.00), None)]
    c, _ = run(san=sanitary(plan))
    assert c.held_totals[C.UNTYPED] == 1
    assert sum(c.totals.values()) == 7
    (u,) = [f for f in c.rooms["B2"]["fixtures"] if f["kind"] == C.UNTYPED]
    assert u["state"] == "HELD"


def test_adverse_unknown_kind_refused():
    with pytest.raises(ValueError):
        C.census(ROOMS, [], [C.Symbol("JACUZZI_XL", (1, 1), C.SANITARY, "GF")], sanitary_floors_read={"GF"})


def test_adverse_drain_size_unprinted_stays_unprinted():
    plan = [(C.FLOOR_DRAIN, (1.20, 0.60), None)]
    c, _ = run(san=sanitary(plan))
    assert c.drains_by_size == {"UNPRINTED": 1}


@pytest.mark.parametrize("types,expected", [
    (["TEXT", "TEXT"], True), (["MTEXT"], True), (["ATTDEF", "TEXT"], True),
    (["ARC", "LINE"], False), (["TEXT", "LINE"], False), ([], False)])
def test_tag_block_by_content_not_name(types, expected):
    assert C.is_tag_block(types) is expected


def test_fit_needs_two_objects():
    with pytest.raises(ValueError):
        C.fit_sheet([((0, 0), (0, 0))])
