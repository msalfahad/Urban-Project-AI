"""T-600: column-beam pair residual split into physical causes (R-T600-1 .. 3). Hand villa "V600" (not the training
villa: three columns, two beams crossing in one column, a beam wider than a column, one column HELD on a schedule /
plan CONFLICT), adverse cases, then the development villa from the committed output (the private rebuild only when
the private inputs are present)."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t600"))
import t600_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t600" / "out" / "T600_PAIR_RESIDUAL.json"
PRIV = ROOT.parent / "private"
PRIVATE = (PRIV / "concrete_rebar.xlsx", PRIV / "t600" / "bands.json", PRIV / "st7757.dxf")
D = Decimal


def _zone(band, rect, u, D_, key):
    inside, beside, along = R.strip_zone(band, rect, u)
    ax = "X" if u == (1.0, 0.0) else "Y" if u == (0.0, 1.0) else "OBLIQUE"
    return {"poly": inside, "beside": beside, "D": D_, "axis": ax, "key": key}


# ---- villa "V600" (hand, metres) ---------------------------------------------------------------------------------
# K1 0.40 x 0.25 (x 0 .. 0.40, y 0 .. 0.25), D_ctrl 0.60: J = 0.10 x 0.60 = 0.060
#   BX 0.20 wide along X (y 0.025 .. 0.225), D 0.60, runs through K1: zone 0.40 x 0.20 x 0.60 = 0.048
#   BY 0.20 wide along Y (x 0.10 .. 0.30),   D 0.50, runs through K1: zone 0.20 x 0.25 x 0.50 = 0.025
#   union: [0, 0.50) (0.08 + 0.05 - 0.04) x 0.50 = 0.045 ; [0.50, 0.60) 0.08 x 0.10 = 0.008 -> 0.053
#   OVERLAP_CROSSING 0.073 - 0.053 = 0.020 (= 0.20 x 0.20 x 0.50) ; UNCOVERED 0.060 - 0.053 = 0.007
# K2 0.20 x 0.20 (x 5.0 .. 5.2), D_ctrl 0.60: J = 0.024 ; BX2 0.30 wide (y -0.05 .. 0.25) D 0.60 through it:
#   inside 0.20 x 0.20 x 0.60 = 0.024 (UNCOVERED 0), BESIDE (0.06 - 0.04) x 0.60 = 0.012
# K3 0.30 x 0.20 HELD (CONFLICT): BX3 0.20 wide D 0.60 through: zone 0.30 x 0.20 x 0.60 = 0.036 OUTSIDE_SET_HELD
# carrier crossing: M1 frames through a 0.20 wide carrier: 0.20 x 0.20 x 0.60 = 0.024
# his through volumes: M1 (BX + carrier) 0.050 -> SHORT 0.022 ; M2 (BY) 0.025 ; M3 (BX2) 0.036 ; M4 (BX3) 0.040 ->
#   BEYOND -0.004.  T = 0.151, J = 0.084, R = 0.067 = 0.020 - 0.007 + 0.012 + 0.036 + 0.024 - 0.022 + 0.004
K1, K2, K3 = (0.0, 0.0, 0.40, 0.25), (5.0, 0.0, 5.2, 0.2), (9.0, 0.0, 9.3, 0.2)
BX = [(-3.0, 0.025), (0.40, 0.025), (0.40, 0.225), (-3.0, 0.225)]
BY = [(0.10, 0.25), (0.30, 0.25), (0.30, 4.0), (0.10, 4.0)]
BX2 = [(2.0, -0.05), (8.0, -0.05), (8.0, 0.25), (2.0, 0.25)]
BX3 = [(8.5, 0.0), (12.0, 0.0), (12.0, 0.2), (8.5, 0.2)]


def _v600():
    k1 = R.column_zone_terms([_zone(BX, K1, (1.0, 0.0), "0.60", "BX"), _zone(BY, K1, (0.0, 1.0), "0.50", "BY")],
                             col_rect=K1, joint=D("0.060"))
    k2 = R.column_zone_terms([_zone(BX2, K2, (1.0, 0.0), "0.60", "BX2")], col_rect=K2, joint=D("0.024"))
    k3 = R.column_zone_terms([_zone(BX3, K3, (1.0, 0.0), "0.60", "BX3")], col_rect=K3)
    return k1, k2, k3


def test_hand_column_terms():
    k1, k2, k3 = _v600()
    assert (k1["ZONES"], k1["UNION"], k1["OVERLAP_CROSSING"], k1["OVERLAP_REPEAT"], k1["BESIDE"], k1["UNCOVERED"]) == (
        D("0.073000"), D("0.053000"), D("0.020000"), D("0.000000"), D("0.000000"), D("0.007000"))
    assert (k2["UNION"], k2["BESIDE"], k2["UNCOVERED"]) == (D("0.024000"), D("0.012000"), D("0.000000"))
    assert k3["UNION"] == D("0.036000") and "UNCOVERED" not in k3


def test_hand_pair_closure():
    k1, k2, k3 = _v600()
    m1 = R.mark_short(D("0.048") + D("0.024"), "0.050")
    m4 = R.mark_short(k3["ZONES"], "0.040")
    assert m1 == {"SHORT": D("0.022000")} and m4 == {"BEYOND": D("-0.004000")}
    T, J = D("0.151"), D("0.084")
    terms = [("OVERLAP_CROSSING", "K1", k1["OVERLAP_CROSSING"]), ("UNCOVERED", "K1", -k1["UNCOVERED"]),
             ("BESIDE", "K2", k2["BESIDE"]), ("UNCOVERED", "K2", -k2["UNCOVERED"]),
             ("OUTSIDE_SET_HELD", "K3", R.held_term(k3["UNION"])), ("CARRIER_NODE", "M1 carrier", D("0.024")),
             ("UNRESOLVED_SHORT", "M1", -m1["SHORT"]), ("UNRESOLVED_SHORT", "M2", D(0)),
             ("UNRESOLVED_SHORT", "M3", D(0)),
             ("BEYOND", "M4", -m4["BEYOND"])]
    by = R.pair_closure(T - J, terms)
    assert sum(D(v) for v in by.values()) == D("0.067000")


def test_hand_mirror_and_rotation_invariant():
    k1 = _v600()[0]
    mir = lambda pts: [(-x, y) for x, y in pts]                         # noqa: E731
    K1m = (-0.40, 0.0, 0.0, 0.25)
    m = R.column_zone_terms([_zone(mir(BX), K1m, (1.0, 0.0), "0.60", "BX"),
                             _zone(mir(BY), K1m, (0.0, 1.0), "0.50", "BY")], col_rect=K1m, joint=D("0.060"))
    rot = lambda pts: [(-y, x) for x, y in pts]                         # noqa: E731  (+90 deg)
    K1r = (-0.25, 0.0, 0.0, 0.40)
    r = R.column_zone_terms([_zone(rot(BX), K1r, (0.0, 1.0), "0.60", "BX"),
                             _zone(rot(BY), K1r, (1.0, 0.0), "0.50", "BY")], col_rect=K1r, joint=D("0.060"))
    assert m == k1 == r


def test_hand_oblique_strip_and_repeat():
    # beam rotated 12 deg through a 1.00 x 0.25 column: strip across the outline's projection on the axis
    import math
    a = math.radians(12)
    u = (math.cos(a), math.sin(a))
    v = (-u[1], u[0])
    c = (0.5, 0.125)
    band = [(c[0] + s * u[0] + t * v[0], c[1] + s * u[1] + t * v[1]) for s, t in ((-3, -0.1), (3, -0.1), (3, 0.1),
                                                                                    (-3, 0.1))]
    inside, beside, along = R.strip_zone(band, (0.0, 0.0, 1.0, 0.25), u)
    assert abs(along - (1.0 * math.cos(a) + 0.25 * math.sin(a))) < 1e-9
    assert inside.area + beside.area == pytest.approx(along * 0.2, abs=1e-9)
    # two collinear beams entering one column from opposite sides, each to the far face: REPEAT = the whole column
    col = (0.0, 0.0, 0.20, 0.50)
    w = [(-2.0, 0.15), (0.20, 0.15), (0.20, 0.35), (-2.0, 0.35)]
    e = [(0.0, 0.15), (2.0, 0.15), (2.0, 0.35), (0.0, 0.35)]
    t = R.column_zone_terms([_zone(w, col, (1.0, 0.0), "0.40", "W"), _zone(e, col, (1.0, 0.0), "0.40", "E")],
                            col_rect=col, joint=D("0.040"))
    assert t["OVERLAP_REPEAT"] == D("0.016000") and t["OVERLAP_CROSSING"] == D("0.000000")
    assert t["UNCOVERED"] == D("0.024000")                              # 0.10 - 0.04 m2 outside the strip x 0.40



# ---- r2: carrier nodes (hand villa "V600", metres) -------------------------------------------------------------------
# carrier CR 0.90 wide on an axis at 53.6 deg through the origin; framing W (from the west) and E (from the east) on the
# X axis, 0.20 wide (y -0.10 .. 0.10), both D 0.50, b 0.20; N (vertical, x 0.30 .. 0.50) D 0.50 b 0.20.
# crossing on the X axis: L = 0.90 / sin 53.6 = 0.90 / 0.804894 = 1.118160; W and E occupy the same parallelogram: node once.
import math  # noqa: E402
TH = math.radians(53.6)
CU = (math.cos(TH), math.sin(TH))
CV = (-CU[1], CU[0])
CR = [(s_ * CU[0] + t_ * CV[0], s_ * CU[1] + t_ * CV[1]) for s_, t_ in ((-5, -0.45), (5, -0.45), (5, 0.45), (-5, 0.45))]
W = [(-6.0, -0.1), (-0.8, -0.1), (-0.8, 0.1), (-6.0, 0.1)]
E = [(0.8, -0.1), (6.0, -0.1), (6.0, 0.1), (0.8, 0.1)]
N = [(0.30, 1.0), (0.50, 1.0), (0.50, 6.0), (0.30, 6.0)]


def _entry(key, mark, band, D_="0.50", b="0.20"):
    x = R.crossing(band, CR)
    return {"key": key, "mark": mark, "poly": x["poly"], "D": D(D_), "b": D(b), "w_drawn": x["w_framing"],
            "m3": R.entry_m3(x["L"], b, D_), "L": x["L"]}


def test_hand_oblique_crossing_on_the_framing_axis():
    x = R.crossing(W, CR)
    assert x["L"] == pytest.approx(0.90 / math.sin(TH), abs=1e-9)          # not the 0.90 perpendicular extent
    assert x["poly"].area == pytest.approx(0.20 * 0.90 / math.sin(TH), abs=1e-9)
    assert R.entry_m3(x["L"], "0.20", "0.50") == D("0.111816")             # 0.90 / 0.804894 = 1.118160 x 0.20 x 0.50
    with pytest.raises(R.Refused):
        R.crossing(W, E)                                                    # collinear: no crossing


def test_hand_node_entered_by_two_marks_counted_once():
    nodes = R.carrier_nodes([_entry("W", "MW", W), _entry("E", "ME", E)])
    assert len(nodes) == 1 and nodes[0]["shared"] and nodes[0]["marks"] == ["ME", "MW"]
    n = nodes[0]
    assert n["capacity_m3"] == D("0.111816") and n["entries_sum_m3"] == D("0.223632")
    # a third mark crossing the same carrier at another angle and overlapping part of the node joins it (union)
    nodes = R.carrier_nodes([_entry("W", "MW", W), _entry("E", "ME", E), _entry("N", "MN", N)])
    assert len(nodes) == 1 and nodes[0]["marks"] == ["ME", "MN", "MW"]
    xw, xn = R.crossing(W, CR)["poly"], R.crossing(N, CR)["poly"]
    exp = R.d6(D(repr(xw.union(xn).area)) * D("0.50"))
    assert nodes[0]["capacity_m3"] == exp < nodes[0]["entries_sum_m3"]
    groups = R.mark_groups({"MW": {nodes[0]["id"]}, "ME": {nodes[0]["id"]}, "MX": {"other"}})
    assert groups == [("ME", "MW"), ("MX",)]


def test_adverse_one_node_two_marks_refused():
    a, b = _entry("W", "MW", W), _entry("E", "ME", E)
    with pytest.raises(R.Refused):
        R.assert_nodes_once([(a["key"], a["poly"], a["m3"]), (b["key"], b["poly"], b["m3"])])
    R.assert_nodes_once([(a["key"], a["poly"], a["m3"]), ("far", box(50, 50, 51, 51), D("0.1"))])
    bad = dict(b, w_drawn=0.30)                                              # drawn 0.30 vs his b 0.20
    with pytest.raises(R.Refused):
        R.carrier_nodes([a, bad])
    with pytest.raises(R.Refused):
        R.carrier_nodes([a, dict(a)])                                        # one entry twice


def test_short_bounds_and_tolerance():
    lo, hi = R.short_bounds("0.30", "0.11", "0.25")
    assert (lo, hi) == (D("0.050000"), D("0.160000"))
    assert R.short_is_zero("0.000073", "0.20", "0.40") and not R.short_is_zero("0.0009", "0.20", "0.40")


# ---- adverse -------------------------------------------------------------------------------------------------------
def test_adverse_cause_counted_twice_refused():
    with pytest.raises(R.Refused):
        R.pair_closure("0.02", [("OVERLAP_CROSSING", "K1", "0.01"), ("OVERLAP_CROSSING", "K1", "0.01")])
    z = _zone(BX, K1, (1.0, 0.0), "0.60", "BX")
    with pytest.raises(R.Refused):
        R.column_zone_terms([z, dict(z)], col_rect=K1, joint=D("0.06"))


def test_adverse_held_conflict_never_zero_and_missing_refused():
    with pytest.raises(R.Refused):
        R.held_term("0")
    with pytest.raises(R.Refused):
        R.held_term(None)
    with pytest.raises(R.Refused):
        R.pair_closure("0.01", [("UNRESOLVED_SHORT", "M1", None)])
    with pytest.raises(R.Refused):
        R.pair_closure("0.01", [("SHORT", "M1", "0.01")])                   # r2: SHORT is not a cause class


def test_adverse_units_percent_and_open_sum():
    with pytest.raises(R.Refused):
        R.column_zone_terms([_zone(BX, K1, (1.0, 0.0), "600", "BX")], col_rect=K1, joint=D("0.06"))   # mm depth
    with pytest.raises(R.Refused):
        R.d6("12.5%")
    with pytest.raises(R.Refused):
        R.pair_closure("0.067", [("BESIDE", "K2", "0.012")])                # terms do not re-add
    with pytest.raises(R.Refused):
        R.pair_closure("0.01", [("MAJORITY", "K1", "0.01")])                # unknown class
    with pytest.raises(R.Refused):
        R.mark_short("0.1", "-0.05")


def test_adverse_reading_member_with_two_values_refused():
    with pytest.raises(R.Refused):
        R.reading_differences({"C3 a": "0.05"}, {"C3 a": "0.06"})
    assert R.reading_differences({"a": "0.05", "b": "0.02"}, {"a": "0.05", "c": "0.15"}) == {
        "b": D("-0.020000"), "c": D("0.150000")}


def test_adverse_empty_outline_refused():
    with pytest.raises(R.Refused):
        R.strip_zone(BX, (0.0, 0.0, 0.0, 0.25), (1.0, 0.0))


# ---- development villa (committed output) ---------------------------------------------------------------------------
def _doc():
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_villa_storey_terms_close_to_the_statement_residual():
    doc = _doc()
    exp = {"GF": (D("2.901714") + D("0.120452"), D("2.28125")), "1F": (D("1.593362"), D("0.385"))}
    for st, (T, J) in exp.items():
        s = doc["storeys"][st]
        assert D(s["through_support_T_m3"]) == T and D(s["joint_head_J_m3"]) == J
        assert D(s["residual_m3"]) == T - J
        assert sum(D(v) for v in s["by_class_m3"].values()) == T - J
        assert sum(D(t[2]) for t in s["terms"]) == T - J
        keys = [(t[0], t[1]) for t in s["terms"]]
        assert len(keys) == len(set(keys))                               # each cause once
    assert D(doc["storeys"]["GF"]["statement_pair_residual_m3"]) == D("0.620464")
    assert D(doc["storeys"]["1F"]["statement_pair_residual_m3"]) == D("1.208362")


def test_villa_columns_and_marks_reconcile():
    doc = _doc()
    for st, s in doc["storeys"].items():
        for lab, c in s["columns"].items():
            if c["beams"]:
                parts = D(c["UNION"]) + D(c["OVERLAP_CROSSING"]) + D(c["OVERLAP_REPEAT"]) + D(c["BESIDE"])
                assert parts == D(c["ZONES"]), lab
            if c["kind"] == "REC":
                assert D(c["JOINT"]) - D(c["UNION"]) == D(c["UNCOVERED"]), lab
            if c["kind"] == "HELD":
                assert D(c["UNION"]) > 0, lab                             # a held partner's zone is never 0
        J = sum(D(c["JOINT"]) for c in s["columns"].values() if c["kind"] == "REC")
        assert J == D(s["joint_head_J_m3"])
        for mk, b in s["beam_marks"].items():
            lo, hi = (D(x) for x in b["short_bounds_m3"])
            assert lo == D(b["capacity_exclusive_m3"]) - D(b["T_m3"]), mk
            assert hi - lo == D(b["capacity_shared_entries_m3"]), mk
        # group closure: zones + node capacities - T = group SHORT / BEYOND, each group once
        for g in s["groups"]:
            mk = g.split(" + ")
            cap = sum(D(s["beam_marks"][m]["zones_m3"]) for m in mk) + sum(
                D(n["capacity_m3"]) for n in s["carrier_nodes"] if set(n["marks"]) & set(mk))
            T = sum(D(s["beam_marks"][m]["T_m3"]) for m in mk)
            b = s["beam_marks"][mk[0]]
            assert cap - T == D(b.get("group_SHORT", b.get("group_BEYOND"))), g


def test_villa_carrier_capacity_once_per_node():
    """r2 (Verifier 23:58): B27 node entered by B5 and B4 (and CB4) counted once; orthogonal entries unchanged."""
    gf = _doc()["storeys"]["GF"]
    keys = [k for n in gf["carrier_nodes"] for k in n["id"].split(" + ")]
    assert len(keys) == len(set(keys))                                   # every entry in exactly one node
    b27 = next(n for n in gf["carrier_nodes"] if "B5 GF:BAND0017 -> GF:BAND0048.1" in n["id"])
    assert b27["marks"] == ["B4", "B5", "CB4"] and b27["shared"]
    assert D(b27["capacity_m3"]) < D(b27["entries_sum_m3"])
    b22 = next(n for n in gf["carrier_nodes"] if "CB3 GF:BAND0019.1 -> GF:BAND0045" in n["id"])
    assert b22["marks"] == ["B4", "CB3"] and D(b22["capacity_m3"]) == D("0.074690")   # deeper CB3 (0.75) covers B4
    car = {c["key"]: c for c in gf["beam_marks"]["B4"]["carriers"]}
    assert \
        abs(D(car["B4 GF:BAND0018 -> GF:BAND0048.2"]["L_m"]) - D("1.120")) < D("0.002")   # 0.90 / sin 53.6 deg
    assert car["B4 GF:BAND0011 -> GF:BAND0044.1"]["entry_m3"] == "0.045070"           # orthogonal: as T-229
    f1 = _doc()["storeys"]["1F"]
    n = next(n for n in f1["carrier_nodes"] if n["shared"])
    assert n["marks"] == ["B2", "CB13"] and n["capacity_m3"] == "0.067425"
    for st in ("GF", "1F"):
        terms = [t for t in _doc()["storeys"][st]["terms"] if t[0] == "CARRIER_NODE"]
        assert sum(D(t[2]) for t in terms) == sum(D(n["capacity_m3"]) for n in _doc()["storeys"][st]["carrier_nodes"])
        assert "SHORT" not in _doc()["storeys"][st]["by_class_m3"]                    # r2: never a cause


def test_villa_per_mark_proposals_only_where_short_zero():
    for st in ("GF", "1F"):
        for mk, b in _doc()["storeys"][st]["beam_marks"].items():
            if b["proposal"].startswith("PER-MARK"):
                assert b["group"] == mk and b["capacity_shared_entries_m3"] == "0"
                assert abs(D(b["short_bounds_m3"][0])) <= D("0.001"), mk
            if b.get("per_column"):
                assert b["proposal"].startswith(("PER-MARK", "CONDITIONAL")), mk
    gf = _doc()["storeys"]["GF"]["beam_marks"]
    assert {m for m, b in gf.items() if b["proposal"].startswith("PER-MARK")} == {"B2", "CB5", "CB7"}
    assert gf["CB6"]["proposal"].startswith("CONDITIONAL")


def test_villa_b7_row_traced():
    b7 = _doc()["storeys"]["GF"]["beam_marks"]["B7"]
    assert D(b7["T_m3"]) == D("0.354452")                                # 0.234000 through + 0.120452 untraced
    assert b7["group"] == "B7" and D(b7["group_SHORT"]) == D("0.177978")  # inside the drawn closing faces
    assert D(b7["capacity_exclusive_m3"]) == D("0.532430")               # 3.55 m x 0.20 x 0.75 (T-576)
    assert len(b7["carriers"]) == 8 and not any(c["node_shared"] for c in b7["carriers"])   # ring ends distinct


def test_villa_readings_reproduce_reported_totals():
    r = _doc()["readings"]
    assert r["GF"]["T-551 (record)"]["joint_m3"] == "2.281250" and r["GF"]["T-572"]["joint_m3"] == "1.883750"
    assert r["GF"]["T-576 (10E0 = C8)"]["joint_m3"] == "2.033750"
    assert r["GF"]["T-576 (10E0 = C7)"]["joint_m3"] == "2.075000"
    assert r["1F"]["T-576 (10E0 = C8)"]["minus_record_by_member_m3"] == {
        "P.C 20x50 69D (D_low 0.75, LOWER_BOUND)": "0.075000"}
    c = _doc()["storeys"]["1F"]["columns"]["P.C 20x50 69D"]
    assert c["kind"] == "OPEN" and c["joint_at_lower_bound_m3"] == "0.075000" == c["UNION"]


def test_villa_no_freelancer_row_tracked():
    txt = OUT.read_text(encoding="utf-8")
    for word in ("\"his_rows\"", "\"his_n\"", "\"his_L", "\"his_length"):
        assert word not in txt


@pytest.mark.skipif(not all(p.exists() for p in PRIVATE), reason="private inputs absent")
def test_private_rebuild_equals_committed():
    import t600_alsenan as A
    doc = A.build(*(str(p) for p in PRIVATE))
    assert json.loads(json.dumps(doc, sort_keys=True)) == _doc()
