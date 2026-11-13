"""T-685 waterproofing HELD / MISSING census (R-T685-1 .. -3): synthetic villa W685 by hand (normal + adverse) and
the development villa pinned to the committed outputs.

Villa W685 (synthetic, not the development villa), by hand; utility room box 2.40 (E-W) x 3.10 (N-S), upturn 0.20:
  walls: north 2.40 with one door 0.90, west 3.10 with one window 1.20, south 2.40; east side 3.10 OPEN (no wall)
  wall run 2.40 + 3.10 + 2.40 = 7.90; less the door 0.90 = 7.00 lm
  window sill not printed  -> low 7.00 - 1.20 = 5.80 lm = 1.16 m2, high 7.00 lm = 1.40 m2 (OPEN_BOUND)
  window sill 0.90 (>= 0.20) -> 7.00 lm = 1.40 m2 MEASURED;  sill 0.10 (< 0.20) -> 5.80 lm = 1.16 m2 MEASURED
  open side with an owner box rule -> membrane edge 3.10 lm; without one -> HELD (never 0)
  two drains printed -> AT LEAST 2 penetrations; none printed / plan not read -> HELD
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t685"))
import t685_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t685" / "out" / "T685_WP_CENSUS.json"
WALLS = [("north", "2.40"), ("west", "3.10"), ("south", "2.40")]
DOORS = [("D1", "0.90")]


def test_upturn_sill_unknown_is_a_bound():
    u = R.upturn_bound(WALLS, DOORS, [("W1", "1.20", None)])
    assert (u["low_lm"], u["high_lm"], u["low_m2"], u["high_m2"]) == ("5.800000", "7.000000", "1.160000", "1.400000")
    assert u["status"] == "OPEN_BOUND" and len(u["held_terms"]) == 1


def test_upturn_sill_known():
    assert R.upturn_bound(WALLS, DOORS, [("W1", "1.20", "0.90")])["high_m2"] == "1.400000"
    hi = R.upturn_bound(WALLS, DOORS, [("W1", "1.20", "0.90")])
    assert hi["status"] == "MEASURED" and hi["low_m2"] == "1.400000"
    lo = R.upturn_bound(WALLS, DOORS, [("W1", "1.20", "0.10")])
    assert lo["status"] == "MEASURED" and lo["low_m2"] == lo["high_m2"] == "1.160000"


def test_upturn_mirror_and_rotation_invariant():
    a = R.upturn_bound(WALLS, DOORS, [("W1", "1.20", None)])
    b = R.upturn_bound(list(reversed(WALLS)), DOORS, [("W1", "1.20", None)])
    c = R.upturn_bound([("east", "3.10"), ("north", "2.40"), ("south", "2.40")], DOORS, [("W1", "1.20", None)])
    assert a["low_m2"] == b["low_m2"] == c["low_m2"] and a["high_m2"] == b["high_m2"] == c["high_m2"]


def test_open_side_carries_no_upturn():
    # an open side added as a wall run would raise the upturn: the rule takes walls only (adverse by construction)
    with_open = R.upturn_bound(WALLS + [("east open", "3.10")], DOORS, [])
    assert with_open["high_m2"] == "2.020000"            # the wrong reading, 10.10 lm
    assert R.upturn_bound(WALLS, DOORS, [])["high_m2"] == "1.400000"


@pytest.mark.parametrize("walls,doors,wins", [
    (WALLS, [("D1", "900")], []),                                        # mm read as m
    ([("north", "-2.40")], [], []),                                       # negative
    (WALLS, [("D1", "4.00"), ("D2", "4.00")], []),                        # openings longer than the walls
    ([], [], []),                                                          # all open: no upturn at all
])
def test_upturn_adverse(walls, doors, wins):
    with pytest.raises(R.RuleError):
        R.upturn_bound(walls, doors, wins)


def test_termination():
    assert R.termination([("east", "3.10")], "owner box rule")["value_lm"] == "3.100000"
    h = R.termination([("east", "3.10")], None)
    assert h["status"] == "HELD" and h["value_lm"] is None
    with pytest.raises(R.RuleError):
        R.termination([], "owner box rule")


def test_penetrations():
    assert R.penetrations_at_least(2) == {"status": "OPEN_BOUND", "at_least": 2, "high": None}
    assert R.penetrations_at_least(None)["status"] == "HELD"
    assert R.penetrations_at_least(0)["at_least"] is None          # none printed: open, never 0
    with pytest.raises(R.RuleError):
        R.penetrations_at_least(1.5)


def test_unprinted_membrane_system_stays_held():
    s = R.system_status(None)
    assert s["status"] == "HELD" and s["system"] is None
    assert R.system_status("2 layers liquid membrane (detail 3)")["status"] == "PRINTED"


def _l(**kw):
    l = {"line_id": "L-w685-1", "item_code": "FIN.WP.ROOF", "unit": "m2", "class": "RELEASED", "measured_net": 50.0,
         "held_low": None, "held_high": None}
    l.update(kw)
    return l


def test_element_totals_keep_flat_and_upturn_apart():
    t = R.element_totals([_l(), _l(line_id="L-2", item_code="FIN.WP.ROOF_UPTURN", unit="lm", measured_net=30.0),
                          _l(line_id="L-3", item_code="FIN.WP.MEMBRANE_ROLLS", unit="pcs", measured_net=6.0),
                          _l(line_id="L-4", **{"class": "HELD"}, measured_net=None, held_low=0.0, held_high=2.0)])
    assert t["ROOF_FLAT"]["m2"]["released"] == "50.000000"
    assert t["ROOF_FLAT"]["m2"]["held_high"] == "2.000000"
    assert t["ROOF_UPTURN"]["lm"]["released"] == "30.000000"
    assert t["PROCUREMENT_ROLLS"]["pcs"]["kind"] == "PROCUREMENT"


@pytest.mark.parametrize("bad", [
    _l(unit="lm"),                                            # an upturn lm booked into the flat roof m2
    _l(item_code="FIN.WP.WALL_UPTURN", unit="lm"),            # wall upturn must be m2
    _l(**{"class": "HELD"}, measured_net=3.0),                # HELD with a value
    _l(measured_net=None),                                    # released with no value
    _l(item_code="FIN.FLOOR.PORCELAIN"),                      # not a WP code
])
def test_element_totals_adverse(bad):
    with pytest.raises(R.RuleError):
        R.element_totals([bad])


def _e(key, cls="DESIGNER_ITEM", **kw):
    e = {"key": key, "class": cls, "cause": "detail printed on no sheet"}
    e.update(kw)
    return e


def test_census_normal_and_adverse():
    assert R.census([_e("L-1"), _e("MISSING:x", "MEASURABLE_NOW", fix={"value": "0.2"})], ["L-1"], ["MISSING:x"]) == \
        {"DESIGNER_ITEM": 1, "MEASURABLE_NOW": 1}
    with pytest.raises(R.RuleError):
        R.census([_e("L-1")], ["L-1", "L-2"], [])                          # a HELD line missing
    with pytest.raises(R.RuleError):
        R.census([_e("L-1"), _e("L-1")], ["L-1"], [])                       # twice
    with pytest.raises(R.RuleError):
        R.census([_e("L-1", cause="the freelancer has 285")], ["L-1"], [])  # freelancer as cause
    with pytest.raises(R.RuleError):
        R.census([_e("L-1", fix={"value": "0"})], ["L-1"], [])               # HELD resolved to 0
    with pytest.raises(R.RuleError):
        R.census([_e("L-1", cls="GUESS")], ["L-1"], [])


# ---- development villa: committed outputs -----------------------------------------------------------------------

def test_builder_outputs_match():
    p = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t685/t685_alsenan.py"), "--check"],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr


def test_alsenan_census_counts():
    r = json.loads(OUT.read_text())
    assert r["candidate"] == "ARCH_TAKEOFF_V3.0.66"
    assert r["held"] == 53 and r["missing"] == 5 and r["count"] == 58 and r["lines_in_scope"] == 160
    assert sum(r["by_class"].values()) == r["count"]
    for e in r["entries"]:
        f = e.get("fix") or {}
        assert f.get("value") is None or float(f["value"]) > 0
        if e["class"] in ("DESIGNER_ITEM", "OWNER_OPEN", "NO_PHYSICAL_ELEMENT"):
            assert not f


def test_alsenan_measured_pieces():
    r = json.loads(OUT.read_text())
    e = {x["key"]: x for x in r["entries"]}
    up = e["L-8090ff20f2b547d1bc96"]["fix"]
    assert (up["low"], up["high"]) == ("1.400000", "1.900000")         # 7.00 .. 9.50 lm x 0.20
    assert e["MISSING:FIN.WP.TERMINATION[lm]/GF-07:OPEN_SIDE_DINING/MEMBRANE_EDGE"]["fix"]["value"] == "4.500000"
    assert e["MISSING:FIN.WP.DOORWAY[m2]/DOOR:D-GF-07-PANTRY/THRESHOLD_FLOOR"]["fix"]["value"] == "0.200000"
    pen = [x for x in r["entries"] if x["item_code"] == "FIN.WP.PENETRATION"]
    assert len(pen) == 18 and all(x["fix"]["at_least"] >= 1 and x["fix"]["value"] is None for x in pen)
    # flat roof m2 and upturn lm never summed together
    assert set(r["element_totals"]["ROOF_FLAT"]) == {"m2"} and set(r["element_totals"]["ROOF_UPTURN"]) == {"lm"}
    assert r["systems"]["WET_FLOOR / WET_WALL_UPTURN"]["status"] == "HELD"


@pytest.mark.skipif(not (ROOT.parent / "private/P7757_DXF_COMPRESSED/P7757.dxf").exists(),
                    reason="private drawing not present (it never enters the repository)")
def test_alsenan_dxf_reread():
    sys.path.insert(0, str(ROOT / "research" / "agents_t685"))
    import t685_alsenan as A
    assert A.verify_dxf(str(ROOT.parent / "private/P7757_DXF_COMPRESSED/P7757.dxf"))
