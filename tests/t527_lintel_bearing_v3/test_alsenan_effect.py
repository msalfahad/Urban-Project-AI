"""T-527 on the development villa, from the committed numbers-only DXF re-run (no private file needed): every end that
moves V1 -> V2 -> V3 with its cause, and what that does to the merged T-516 / T-519 / T-524 results (computed by their
own code on substituted ends).

Hand checks (W18, w 0.50; span bars from T-515, kg/m = d^2 / 162; links 5 / m):
  W18 END: the band's far face is drawn on to the bay's inner face arc (r_in 1.935 m about the bay centre): crossing at
  s = 7.570294 m from the band start, the drawn face line ends there (0.0 mm); jamb 6.9923 -> a = 0.577994 m, 0.577 on
  the T-516 floor-to-mm convention (Checker 0.578; V2 chord point 7.4708 -> 0.4785, floor 0.478). START stays 0.000
  (column C8 face) -> W18 stays FLAGGED_DEFICIT; hard length ceiling 0.50 + 0 + 0.577 = 1.077 m (V2 0.978); links
  ceiling ceil(5 x 1.077) = ceil(5.385) = 6 (V2 ceil(4.89) = 5); straight bar ceiling x 1.077 / 0.978.
  D-GF-11 START: V2 0.827 m COLUMN (V1 0.831 END_OF_MASONRY: EPS_AREA ran 3.7 mm into the 45-degree column corner),
  state BOUNDED unchanged, ceiling 0.80 + 0.827 + 0.238 = 1.865 m (V1 1.869).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t527"))
import t527_effect as E  # noqa: E402

PRIVATE = ROOT.parent / "private"


@pytest.fixture(scope="module")
def doc():
    return E.build()


def test_committed_effect_reproduces(doc):
    fresh = E.render(doc)
    if PRIVATE.is_dir():
        (PRIVATE / "t527").mkdir(exist_ok=True)
        (PRIVATE / "t527" / "EFFECT_T527.json").write_text(fresh, encoding="utf-8")
    assert E.OUT.is_file() and E.OUT.read_text(encoding="utf-8") == fresh


def _ev():
    import csv
    return {(r["opening_id"], r["side"]): r for r in csv.DictReader(
        (ROOT / "research/agents_t527/out/JAMB_EVIDENCE_V3_T527.csv").open(encoding="utf-8"))}


def test_v1_control_reproduces_the_merged_t516_census_32_of_32():
    import csv
    t516 = {(r["opening_id"], r["side"]): r for r in csv.DictReader(
        (ROOT / "research/agents_t516/out/JAMB_EVIDENCE_T516.csv").open(encoding="utf-8"))}
    ev = _ev()
    assert len(ev) == 32 and set(ev) == set(t516)
    for k, r in ev.items():
        assert (r["v1_available_m"], r["v1_stopper"], r["v1_stopper_id"]) == \
               (t516[k]["available_m"], t516[k]["stopper"], t516[k]["stopper_id"]), k


def test_v1_census_equals_the_committed_t516_record():
    committed = json.loads((ROOT / "research/agents_t516/out/JAMB_BEARING_T516.json").read_text(encoding="utf-8"))
    mine = E.census("V1")
    assert [(r["opening_id"], r["state"], r.get("length_hi_m")) for r in mine["rows"]] == \
           [(r["opening_id"], r["state"], r.get("length_hi_m")) for r in committed["rows"]]


def test_exactly_three_ends_move_and_why(doc):
    moved = {(e["opening_id"], e["side"]): e for e in doc["changed_ends"]}
    assert set(moved) == {("D-GF-11", "START"), ("D-GF-13", "END"), ("W18", "END")}
    g11, g13, w18 = moved[("D-GF-11", "START")], moved[("D-GF-13", "END")], moved[("W18", "END")]
    assert g11["v1"] == [0.831, "END_OF_MASONRY"] and g11["v2"] == [0.827, "COLUMN"] and g11["v2_to_v3_m"] == 0.0
    assert g13["v1"] == [1.261, "COLUMN"] and g13["v2"] == [1.26, "COLUMN"] and g13["v2_to_v3_m"] == 0.0
    assert w18["v2"] == [0.478, "OPENING"] and w18["v3"][:2] == [0.577, "END_OF_MASONRY"]
    assert w18["v3"][2].startswith("CURVED_BAY:")


def test_w18_end_is_the_drawn_inner_face_crossing():
    import csv
    bays = list(csv.DictReader((ROOT / "research/agents_t527/out/CURVED_BAYS_T527.csv").open(encoding="utf-8")))
    assert len(bays) == 1 and bays[0]["status"] == "DRAWN" and bays[0]["band"] == "WB-FL0041-FL0042"
    b = bays[0]
    assert (b["r_in_m"], b["r_out_m"]) == ("1.9350", "2.1350")
    assert b["face_minus_line_end_mm"] == "0.0;0.0"          # the drawn far-face line stops exactly on the arc
    cross = float(b["face_minus_cross_m"].split(";")[0])
    jamb = 6.9923                                           # W18 END jamb (V2 stretch 6.4923 + 0.5000)
    r = _ev()[("W18", "END")]
    assert abs(float(r["v3_available_6dp_m"]) - (cross - jamb)) < 2e-6
    assert abs((cross - jamb) - 0.578) < 1e-5               # Checker F-C-T519-1: 0.578 m
    assert abs(float(b["chord_from_m"]) - jamb - 0.4785) < 1e-6   # V2 chord point 0.4785 m
    assert r["available_m"] == "0.577"                      # T-516 convention: floor to the mm (0.577994)


def test_downstream_effects(doc):
    v1v2, v2v3 = doc["steps"]["V1_to_V2"], doc["steps"]["V2_to_V3"]
    assert set(v1v2["t516"]) == {"D-GF-11", "D-GF-13"} and set(v2v3["t516"]) == {"W18"}
    w = dict((p, (a, b)) for p, a, b in v2v3["t516"]["W18"])
    assert w["length_hi_m"] == (0.978, 1.077) and w["links_hi"] == (5, 6)
    assert math.isclose(w["straight_ceiling_kg"][1] / w["straight_ceiling_kg"][0], 1.077 / 0.978, rel_tol=1e-5)
    assert "state" not in w and "precast_beside_fit" not in w      # still FLAGGED (START 0.000 at C8), DOES_NOT_FIT
    g = dict((p, (a, b)) for p, a, b in v1v2["t516"]["D-GF-11"])
    assert g["length_hi_m"] == (1.869, 1.865) and "state" not in g
    # T-519: no system / state / piece change; only the RC length ceilings follow
    for step in (v1v2, v2v3):
        for oid, ch in step["t519"].items():
            assert [p for p, _a, _b in ch] == ["rc_length_hi_m"], oid
    assert doc["t519_rc_produced"]["V1"] == doc["t519_rc_produced"]["V3"] and len(doc["t519_rc_produced"]["V3"]) == 6
    # T-524 deficit-end set unchanged: every moved end is BOUNDED (W18 END keeps b_min in hi) or a non-deficit end
    assert v1v2["t524"] == [] and v2v3["t524"] == []
    s = doc["t524_summary"]["V3"]
    assert (s["corrected_lo_m3"], s["corrected_hi_m3"], s["removed_m3"]) == (0.372692, 0.437542, 0.076458)


def test_no_end_held_and_none_zero_by_default():
    for k, r in _ev().items():
        assert r["available_m"] != "" and r["stopper"] != "", k
        if r["available_m"] == "0.000":
            assert k == ("W18", "START") and r["stopper"] == "COLUMN"
