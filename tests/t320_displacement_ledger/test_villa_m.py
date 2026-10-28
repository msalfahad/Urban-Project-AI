"""T-320 hand-calculated fixture, villa T320-M (NOT Alsenan): two overlapping footing pits, a neck through the existing
ground, a ground beam partly above grade, a buried tank whose wall a footing runs into (a drawn CONFLICT).

Hand calculation (m; EG 0.00 printed; blinding 0.10 projecting 0.10; underlay 0.05):
  Pit A: footing 2.00 x 2.00 x 0.50 at (0, 0)          chain above F: 0.10 / 0.15 / 0.65
         blinding 2.20 x 2.20 x 0.10 = 0.484, underlay 4.00 x 0.05 = 0.200, footing 2.000
  Pit B: footing 1.00 x 1.00 x 0.30 at (1.90, 0.50)    chain above F: 0.10 / 0.15 / 0.45
         blinding 1.20 x 1.20 x 0.10 = 0.144, underlay 0.050, footing 0.300
  A / B shared (same formation): blinding plan 0.30 x 1.20 = 0.36 x 0.10 = 0.036; underlay 0.10 x 1.00 x 0.05 = 0.005;
         footings 0.10 x 1.00 x min(0.50, 0.30) = 0.030 -> netted 0.071
  Neck on A 0.30 x 0.30 from the footing top to +0.60: below EG only; F = -1.40 -> 0.09 x 0.75 = 0.0675
         (above EG 0.09 x 0.60 = 0.054 is NOT displacement)
  Ground beam 0.25 x 4.00, top +0.30, depth 0.60 -> bottom -0.30: below EG 0.25 x 4 x 0.30 = 0.300 (0.300 above EG
         excluded); its blinding (0.25 + 0.10) x 4 x 0.10 = 0.140 at -0.40 .. -0.30
  Tank (formation printed -1.00): base 2.00 x 1.50 x 0.20 = 0.600; wall band 0.96 m2 from -0.80 to +0.20: 0.768 below EG
         (0.192 above excluded); VOID 2.04 m2 from -0.80 to EG: 1.632. Shell + void = 3.000 = 3.00 m2 x 1.00
  Sum 6.6855 - netted 0.071 = 6.6145 m3 established; CONFLICT A footing / tank wall, 0.20 m2 drawn in both:
         F -1.40: footing -1.25 .. -0.75 vs wall -0.80 .. 0 -> 0.05 x 0.20 = 0.010 (kept open, never netted silently)
  Formation only a limit 'not less than 1.20 m' (F = -1.20 - d): every pit volume unchanged (whole chain below EG),
         neck 0.09 x (1.20 - 0.65) = 0.0495 AT_LEAST, + 0.09 m3 per m of d; conflict range 0 .. 0.20 x 0.25 = 0.050
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t320"))
import displacement_ledger_v1 as X  # noqa: E402


def villa(form_a=None, form_b=None):
    fa = form_a or {"value": -1.40}
    fb = form_b if form_b is not None else dict(fa)
    return {
        "unit": "m",
        "eg": {"value": 0.0, "status": "DRAWING-CONFIRMED"},
        "groups": {"PA": {"formation": fa, "kind": "PIT"}, "PB": {"formation": fb, "kind": "PIT"},
                   "TG": {"formation": None, "kind": "TRENCH"}, "TK": {"formation": {"value": -1.00},
                                                                       "kind": "PIT"}},
        "components": [
            {"id": "A:BLIND", "group": "PA", "kind": "BLINDING", "rect": [-0.1, -0.1, 2.1, 2.1],
             "z": [{"form": 0.0}, {"form": 0.10}]},
            {"id": "A:UNDER", "group": "PA", "kind": "UNDERLAY", "rect": [0, 0, 2, 2],
             "z": [{"form": 0.10}, {"form": 0.15}]},
            {"id": "A:FTG", "group": "PA", "kind": "FOOTING", "rect": [0, 0, 2, 2], "z": [{"form": 0.15}, {"form": 0.65}]},
            {"id": "A:NECK", "group": "PA", "kind": "NECK", "rect": [0.85, 0.85, 1.15, 1.15],
             "z": [{"form": 0.65}, {"abs": 0.60}]},
            {"id": "B:BLIND", "group": "PB", "kind": "BLINDING", "rect": [1.8, 0.4, 3.0, 1.6],
             "z": [{"form": 0.0}, {"form": 0.10}]},
            {"id": "B:UNDER", "group": "PB", "kind": "UNDERLAY", "rect": [1.9, 0.5, 2.9, 1.5],
             "z": [{"form": 0.10}, {"form": 0.15}]},
            {"id": "B:FTG", "group": "PB", "kind": "FOOTING", "rect": [1.9, 0.5, 2.9, 1.5],
             "z": [{"form": 0.15}, {"form": 0.45}]},
            {"id": "G1", "group": "TG", "kind": "GROUND_BEAM", "rect": [3.5, 0.0, 3.75, 4.0],
             "z": [{"abs": -0.30}, {"abs": 0.30}]},
            {"id": "G1:BLIND", "group": "TG", "kind": "BLINDING", "rect": [3.45, 0.0, 3.80, 4.0],
             "z": [{"abs": -0.40}, {"abs": -0.30}]},
            {"id": "TK:BASE", "group": "TK", "kind": "TANK_BASE", "rect": [4.5, 0, 6.5, 1.5],
             "z": [{"form": 0.0}, {"form": 0.20}]},
            {"id": "TK:WALL", "group": "TK", "kind": "TANK_WALL", "plan": 0.96, "z": [{"form": 0.20}, {"abs": 0.20}]},
            {"id": "TK:VOID", "group": "TK", "kind": "TANK_VOID", "plan": 2.04, "void": True,
             "z": [{"form": 0.20}, {"abs": 0.20}]},
        ],
        "shared": [{"a": "A:FTG", "b": "TK:WALL", "plan": 0.20, "status": "CONFLICT",
                    "why": "footing and tank wall drawn in the same plan strip; levels collide"}],
    }


def comp(led, cid):
    return next(c for c in led["components"] if c["id"] == cid)


def test_hand_values_printed_formation():
    led = X.build(villa())
    exp = {"A:BLIND": 0.484, "A:UNDER": 0.2, "A:FTG": 2.0, "B:BLIND": 0.144, "B:UNDER": 0.05, "B:FTG": 0.3,
           "A:NECK": 0.0675, "G1": 0.3, "G1:BLIND": 0.14, "TK:BASE": 0.6, "TK:WALL": 0.768, "TK:VOID": 1.632}
    for k, v in exp.items():
        assert comp(led, k)["value_m3"] == pytest.approx(v), k
    netted = {(x["a"], x["b"]): x["value_m3"] for x in led["shared"] if x["status"] == "NETTED"}
    assert netted == {("A:BLIND", "B:BLIND"): pytest.approx(0.036), ("A:UNDER", "B:UNDER"): pytest.approx(0.005),
                      ("A:FTG", "B:FTG"): pytest.approx(0.03)}
    t = X.totals(led)
    assert t["established_m3"] == pytest.approx(6.6145) and t["netted_m3"] == pytest.approx(0.071)
    assert not t["at_least"] and t["held_components"] == []
    conf = next(x for x in led["shared"] if x["status"] == "CONFLICT")
    assert conf["value_m3"] is None and conf["range_m3"] == [pytest.approx(0.01), pytest.approx(0.01)]
    assert t["open_shared_range_m3"] == [pytest.approx(0.01), pytest.approx(0.01)]


def test_above_ground_parts_excluded_and_refused():
    led = X.build(villa())
    assert comp(led, "G1")["above_ground_m3_excluded"] == pytest.approx(0.30)
    assert comp(led, "A:NECK")["above_ground_m3_excluded"] == pytest.approx(0.054)
    assert comp(led, "TK:WALL")["above_ground_m3_excluded"] == pytest.approx(0.192)
    v = villa()
    v["components"][7]["include_above_ground"] = True
    with pytest.raises(X.Refused) as e:
        X.build(v)
    assert e.value.code == "ABOVE_GROUND_NOT_DISPLACEMENT"


def test_shell_plus_void_is_the_envelope_column():
    led = X.build(villa())
    tank = sum(comp(led, k)["value_m3"] for k in ("TK:BASE", "TK:WALL", "TK:VOID"))
    assert tank == pytest.approx(3.00 * 1.00)
    assert comp(led, "TK:VOID")["void"] is True


def test_formation_only_a_limit_gives_bound_never_a_depth():
    led = X.build(villa(form_a={"limit": -1.20}))
    for k, v in {"A:BLIND": 0.484, "A:UNDER": 0.2, "A:FTG": 2.0, "B:FTG": 0.3}.items():
        c = comp(led, k)
        assert c["value_m3"] == pytest.approx(v) and c["coef_m3_per_m"] == pytest.approx(0.0)
    n = comp(led, "A:NECK")
    assert n["value_m3"] == pytest.approx(0.0495) and n["coef_m3_per_m"] == pytest.approx(0.09)
    assert n["status"] == X.BOUND_AT_LEAST and "FORMATION_ONLY_A_LIMIT" in n["held"]
    t = X.totals(led)
    assert t["at_least"] and t["coef_m3_per_m"] == pytest.approx(0.09)
    assert t["netted_m3"] == pytest.approx(0.071)                       # one cast: the overlap shares the formation
    conf = next(x for x in led["shared"] if x["status"] == "CONFLICT")
    assert conf["range_m3"] == [pytest.approx(0.0), pytest.approx(0.05)]


def test_absent_formation_is_held_never_zero():
    led = X.build(villa(form_b={}))
    for k in ("B:BLIND", "B:UNDER", "B:FTG"):
        c = comp(led, k)
        assert c["value_m3"] is None and c["status"] == X.HELD and "LEVEL_NOT_ESTABLISHED" in c["held"]
    t = X.totals(led)
    assert set(t["held_components"]) == {"B:BLIND", "B:UNDER", "B:FTG"}
    held_pairs = [x for x in led["shared"] if x["status"] == X.HELD and x["why"].startswith("OVERLAP_WITH_HELD")]
    assert held_pairs and all(x["value_m3"] is None for x in held_pairs)


def test_held_level_as_zero_refused():
    with pytest.raises(X.Refused) as e:
        X.build(villa(form_a={"value": 0.0, "status": "HELD"}))
    assert e.value.code == "HELD_LEVEL_AS_VALUE"
    v = villa()
    v["eg"] = {"value": 0.0, "status": "HELD"}
    with pytest.raises(X.Refused):
        X.build(v)
    v["eg"] = None
    with pytest.raises(X.Refused) as e:
        X.build(v)
    assert e.value.code == "EXISTING_GROUND_NOT_ESTABLISHED"


def test_gross_overlap_refused():
    with pytest.raises(X.Refused) as e:
        X.totals(X.build(villa()), net=False)
    assert e.value.code == "GROSS_OVERLAP_REFUSED"


def test_backfill_and_disposal_rules():
    assert X.backfill(None, 6.6) == (None, X.HELD)
    assert X.backfill(20.0, None) == (None, X.HELD)
    assert X.backfill(20.0, 6.6145) == (pytest.approx(13.3855), "CALCULATED")
    with pytest.raises(X.Refused):
        X.backfill(5.0, 6.6)
    with pytest.raises(X.Refused) as e:
        X.disposal(20.0, 13.0, bulking=1.25)
    assert e.value.code == "DEFAULT_BULKING_REFUSED"
    assert X.disposal(20.0, 13.0) == (None, X.HELD)
    assert X.disposal(20.0, 13.0, bulking=1.25, bulking_source="answered rule X") == (pytest.approx(12.0), "CALCULATED")


def _scaled(v, k):
    v = copy.deepcopy(v)
    v["unit"] = "mm"
    for g in v["groups"].values():
        f = g.get("formation")
        if f:
            for key in ("value", "limit"):
                if f.get(key) is not None:
                    f[key] *= k
    for c in v["components"]:
        if "rect" in c:
            c["rect"] = [x * k for x in c["rect"]]
        if "plan" in c:
            c["plan"] *= k * k
        for z in c["z"]:
            for key in z:
                z[key] *= k
    for s in v["shared"]:
        s["plan"] *= k * k
    return v


def test_mm_units_and_mirror_give_the_same_ledger():
    base = X.totals(X.build(villa()))
    mm = X.totals(X.build(_scaled(villa(), 1000.0)))
    assert mm["established_m3"] == pytest.approx(base["established_m3"])
    assert mm["netted_m3"] == pytest.approx(base["netted_m3"])
    mir = villa()
    for c in mir["components"]:
        if "rect" in c:
            x0, y0, x1, y1 = c["rect"]
            c["rect"] = [-x1, y0, -x0, y1]
    m = X.totals(X.build(mir))
    assert m["established_m3"] == pytest.approx(base["established_m3"]) and m["netted_m3"] == pytest.approx(0.071)
    with pytest.raises(X.Refused):
        X.build(dict(villa(), unit="ft"))


def test_volume_without_levels_needs_its_below_ground_basis():
    v = villa()
    v["components"].append({"id": "S1", "group": "TG", "kind": "STRAP", "value": 0.50})
    with pytest.raises(X.Refused) as e:
        X.build(v)
    assert e.value.code == "BELOW_EG_NOT_ESTABLISHED"
    v["components"][-1].update(below_eg_basis="ends cast against footing faces whose tops are below EG",
                               status="HELD")
    with pytest.raises(X.Refused) as e:
        X.build(v)
    assert e.value.code == "HELD_VOLUME_AS_VALUE"
    v["components"][-1]["status"] = "DRAWING-CONFIRMED"
    assert X.totals(X.build(v))["established_m3"] == pytest.approx(6.6145 + 0.50)
