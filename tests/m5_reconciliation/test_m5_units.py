"""M5 reconciliation rules on hand-made records: difference classes, how an item enters the reference (measured /
conditional / unmeasurable / excluded), the crosswalk keys, the strip centreline, the mark normalisation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research/urban_engine_m5_concrete_reconciliation"
sys.path.insert(0, str(PKG))
sys.path.insert(0, str(ROOT))
import m5_reconcile as M      # noqa: E402
import m5_sources as S        # noqa: E402
import m5_tables as T         # noqa: E402


def _u(**kw):
    base = {"UID": "X", "ORIGIN": "M4", "FAMILY": "BEAMS", "FLOOR": "GF", "MARK": "B1", "CATEGORY": "PROVISIONAL",
            "LOW": 1.0, "BASE": 1.2, "HIGH": 1.5, "EXP_LOW": None, "EXP_HIGH": None, "BLOCKER": "", "SOURCE": "",
            "DIMS": {}, "COMPONENT": "X", "FORMULA": "", "M5": "KEEP", "M5_NOTE": ""}
    base.update(kw)
    return base


def test_classes():
    assert M.classify(1.0, 1.01) == "MATCHED_WITHIN_TOLERANCE"
    assert M.classify(1.0, 0.0).startswith("MISSING_IN_URBAN")
    assert "held as unresolved" in M.classify(1.0, 0.0, has_exposure=True)
    assert M.classify(0.0, 1.0) == "MISSING_IN_FREELANCER"
    assert M.classify(0.0, 0.0).startswith("UNRESOLVED_REQUIRES_ENGINEER")      # never 'matched' at zero
    assert M.classify(1.0, 1.3) is None
    assert M.classify(1.0, 0.0, scope="SCOPE_DIFFERENCE") == "SCOPE_DIFFERENCE"


def test_lanes():
    assert T.contrib(_u())["STATE"] == "MEASURED" and T.contrib(_u())["MB"] == 1.2
    c = T.contrib(_u(CATEGORY="UNRESOLVED", LOW=None, BASE=None, HIGH=None, EXP_LOW=0.2, EXP_HIGH=0.9))
    assert c["STATE"] == "CONDITIONAL" and c["MB"] == 0 and (c["CL"], c["CH"]) == (0.2, 0.9)
    assert T.contrib(_u(CATEGORY="UNRESOLVED", BASE=None))["STATE"] == "UNMEASURABLE"
    for st in ("EXCLUDED_SAME_AS_M4", "REALLOCATED_TO_DOMES", "NOT_SLAB_DOME_OPENING", "SUPERSEDED_BY_CANTILEVER"):
        c = T.contrib(_u(M5=st, EXP_HIGH=3.0))
        assert c["STATE"].startswith("EXCLUDED") and c["MB"] == c["CH"] == 0         # counted once, elsewhere
    c = T.contrib(_u(CATEGORY="UNRESOLVED", M5="CONDITIONAL_DECOMPOSED", DIMS={"t_m": 0.1}, M5_SLAB_M2=20.0,
                     M5_SLAB_HIGH_M2=30.0, EXP_HIGH=4.5))
    assert (round(c["CL"], 9), round(c["CH"], 9)) == (2.0, 3.0)                   # not the overstated exposure


def test_family_totals_never_add_an_excluded_item():
    U = [_u(UID="a"), _u(UID="b", M5="EXCLUDED_SAME_AS_M4"), _u(UID="c", FAMILY="BLINDING", BASE=9.0)]
    fam = M.urban_families(U)
    assert fam["BEAMS"]["MEAS_BASE"] == 1.2 and fam["BEAMS"]["EXCLUDED_M3"] == 1.2
    assert fam["BLINDING"]["MEAS_BASE"] == 9.0


def test_crosswalk_keys():
    r = {"FAMILY": "BEAMS", "FLOOR": "GF", "MARK": "CB1", "CATEGORY": "BEAMS", "ROW": 43, "D": 13}
    assert T.fl_key(r) == ("BEAMS", "GF", "CB1")
    assert T.fl_key(dict(r, FAMILY="COLUMNS", FLOOR="1F", MARK="PC2")) == ("COLUMNS", "1F", "P.C")
    assert T.fl_key(dict(r, FAMILY="FOOTINGS", MARK="F10")) == T.fl_key(dict(r, FAMILY="FOOTINGS", MARK="F"))
    assert T.ur_key(_u(FAMILY="FOOTINGS", MARK="F/F10")) == ("FOOTINGS", "FOUNDATION", "F+F10")
    assert T.ur_key(_u(MARK="")) == ("BEAMS", "GF", "UNLABELLED")
    assert S._mark("BCB8") == "CB8" and S._mark("GCB10") == "CB10" and S._mark("STB2") == "SB2"
    assert S._mark("F.F") == "FF" and S._mark("some words") == ""


def test_strip_centreline():
    # an L-shaped 200 mm strip: 10 m + 5 m outer legs -> centreline 14.8 m (area / thickness)
    pts = [(0, 0), (10000, 0), (10000, 200), (200, 200), (200, 5000), (0, 5000)]
    s = S.strip_centreline(pts)
    assert s["thickness_mm"] == 200 and abs(s["centreline_m"] - 14.8) < 1e-9
