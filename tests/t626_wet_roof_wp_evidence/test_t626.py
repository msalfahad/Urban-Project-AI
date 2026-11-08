"""T-626: B8 waterproofing rows to drawing evidence (R-T626-1). Hand-calculated non-development fixtures (a bathroom
with a shower recess and a shaft; a roof field inside a parapet with a shaft and a skylight), adverse cases, and the
development-villa build (committed drawing read + statement rows; the drawing re-read is skipped when the private DXF
is absent)."""
from __future__ import annotations

import json
import math
import sys
from decimal import Decimal as D
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t626"
sys.path.insert(0, str(HERE))
import t626_rules as R  # noqa: E402

DXF = ROOT.parents[1] / ".work" / "private" / "P7757_DXF_COMPRESSED" / "P7757.dxf"


def rect(x0, y0, w, h):
    return [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)]


def rot(pts, deg):
    a = math.radians(deg)
    return [(x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)) for x, y in pts]


def mirror(pts):
    return [(-x, y) for x, y in reversed(pts)]


# ---- fixture 1: bathroom 2.40 x 2.00, shower recess 0.90 x 0.90 on its east side, shaft 0.30 x 0.40 in a corner ----
BATH = rect(0, 0, 2.40, 2.00)
RECESS = rect(2.40, 0.50, 0.90, 0.90)
SHAFT = {"kind": "SHAFT", "poly": rect(0.05, 1.55, 0.30, 0.40)}
# hand: 2.40 x 2.00 = 4.80; + 0.90 x 0.90 = 0.81; - 0.30 x 0.40 = 0.12 -> 5.49 m2


def test_bathroom_with_recess_and_shaft_by_hand():
    r = R.membrane_area(BATH, bays=[RECESS], openings=[SHAFT])
    assert D(r["gross"]) == D("5.610000") and D(r["deducted"]) == D("0.120000") and D(r["net"]) == D("5.490000")


@pytest.mark.parametrize("deg", [0, 90, 33.5, 180])
def test_bathroom_rotation_and_mirror_invariant(deg):
    f = (lambda p: rot(p, deg))
    for g in (f, lambda p: mirror(f(p))):
        r = R.membrane_area(g(BATH), bays=[g(RECESS)], openings=[{"kind": "SHAFT", "poly": g(SHAFT["poly"])}])
        assert abs(D(r["net"]) - D("5.49")) <= D("0.000001")


# ---- fixture 2: roof field 10.00 x 8.00 to the inner parapet faces, a shaft 0.60 x 0.60, a skylight r 1.00 --------
ROOFF = rect(0, 0, 10.0, 8.0)


def test_roof_field_with_shaft_and_skylight_by_hand():
    r = R.membrane_area(ROOFF, openings=[{"kind": "SHAFT", "poly": rect(1, 1, 0.6, 0.6)},
                                         {"kind": "SKYLIGHT", "circle": ((6.0, 4.0), 1.0)}])
    # hand: 80 - 0.36 - pi x 1.00^2 = 76.498407 (the circle exactly, never the chord polygon)
    assert D(r["net"]) == D("76.498407")
    assert [o["area"] for o in r["openings"]] == ["0.360000", "3.141593"]


def test_adverse_opening_outside_or_crossing_the_outline_refused():
    with pytest.raises(R.RuleError, match="not inside"):
        R.membrane_area(ROOFF, openings=[{"kind": "SKYLIGHT", "circle": ((9.5, 4.0), 1.0)}])   # crosses the parapet
    with pytest.raises(R.RuleError, match="not inside"):
        R.membrane_area(BATH, openings=[{"kind": "SHAFT", "poly": rect(3, 3, 0.3, 0.3)}])


def test_adverse_bay_overlapping_or_detached_refused():
    with pytest.raises(R.RuleError, match="twice"):
        R.membrane_area(BATH, bays=[rect(2.0, 0.5, 0.9, 0.9)])
    with pytest.raises(R.RuleError, match="does not touch"):
        R.membrane_area(BATH, bays=[rect(2.6, 0.5, 0.9, 0.9)])


def test_adverse_unknown_opening_kind_and_zero_radius_refused():
    with pytest.raises(R.RuleError):
        R.membrane_area(ROOFF, openings=[{"kind": "LABEL", "poly": rect(1, 1, 1, 1)}])
    with pytest.raises(R.RuleError):
        R.membrane_area(ROOFF, openings=[{"kind": "SKYLIGHT", "circle": ((5, 4), 0.0)}])


def test_wet_basis_fixtures_or_owner_rule_only():
    assert R.wet_basis("bath", {"fixtures": ["WC + basin + FD"]}).startswith("FIXTURES")
    assert R.wet_basis("pantry", {"owner_rule": "Q-37 A"}) == "OWNER: Q-37 A"
    with pytest.raises(R.RuleError, match="label alone"):
        R.wet_basis("store by the bath", {"label": "SERVICE", "fixtures": []})   # dry room taken wet by a label
    with pytest.raises(R.RuleError, match="stays dry"):
        R.wet_basis("bedroom", {})


def test_residual_split_re_adds_exactly_and_guards():
    parts = R.split_residual("0.523", [{"name": "chord", "qty": "0.001332", "class": "TOLERANCE", "evidence": "READING"}])
    assert [p["qty"] for p in parts] == ["0.001332", "0.521668"] and parts[-1]["class"] == "UNRESOLVED"
    assert sum(D(p["qty"]) for p in parts) == D("0.523")
    with pytest.raises(R.RuleError, match="name the cause"):
        R.split_residual("0.523", [{"name": "x", "qty": "0.02", "class": "TOLERANCE", "evidence": "e"}])
    with pytest.raises(R.RuleError, match="evidence"):
        R.split_residual("0.523", [{"name": "x", "qty": "0.001", "class": "TOLERANCE"}])
    with pytest.raises(R.RuleError, match="UNRESOLVED"):
        R.split_residual("0.523", [{"name": "x", "qty": "0.1", "class": "UNRESOLVED", "evidence": "e"}])


# ---- development villa ------------------------------------------------------------------------------------------
def _build():
    import t626_alsenan as B
    return B, B.build()


def test_dev_build_matches_committed_outputs():
    B, d = _build()
    assert (HERE / "out" / "T626_ROW_EVIDENCE.json").read_text(encoding="utf-8") == B.dumps(d)
    assert (HERE / "out" / "T626_ROW_EVIDENCE.md").read_text(encoding="utf-8") == B.render_md(d)


def test_dev_24_rows_evidence_and_exact_splits():
    _, d = _build()
    assert d["count"] == {"rows": 24, "by_evidence": {"DIFFERS": 1, "DRAWING_CONFIRMED": 23}}
    f, r = d["split"]["T-546/floor"], d["split"]["T-541/membrane"]
    assert D(f["total"]) == D("-13.565710") and f["count_by_evidence"] == {"DRAWING_CONFIRMED": 18}
    assert f["by_class"] == {"ENGINE_RIGHT": "-0.307294", "RULE_DIFFERENCE": "-13.235", "TOLERANCE": "-0.023416"}
    assert D(r["total"]) == D("75.341560") and r["by_evidence"] == {"DIFFERS": "0.523", "DRAWING_CONFIRMED": "74.818560"}


def test_dev_rooms_own_equals_engine_and_printed_second_read():
    _, d = _build()
    t = {x["room"]: x for x in d["room_table"]}
    assert len(t) == 18 and D(d["floor_own_total_m2"]) == D("85.575708")     # engine 85.575710: 2 x 0.000001 CAD noise
    assert all(abs(D(x["own_minus_engine"])) <= D("0.000001") for x in t.values())
    two = [k for k, x in t.items() if x["printed_second_read"] is not None]
    assert len(two) == 11 and all(D(t[k]["printed_minus_own"]) == 0 for k in two)
    assert t["GF driver W.C."]["handles"] == ["112", "134", "14E", "132"] and t["GF driver W.C."]["own"] == "1.95"
    assert t["GF pantry (wet zone, Q-37 A)"]["wet_basis"] == "OWNER: Q-37 A (pantry is a wet zone)"
    assert all(x["wet_basis"].startswith(("FIXTURES", "OWNER")) for x in t.values())


def test_dev_held_row_untouched_and_named():
    _, d = _build()
    held = [x for x in d["rows"] if x["class"] == "HELD"]
    assert len(held) == 1 and held[0]["delta"] == "34.390242" and held[0]["evidence_status"] == "DRAWING_CONFIRMED"
    assert d["held"][0]["waits_on"].startswith("Q-34")


def test_dev_roof_residual_differs_and_its_split_closes():
    _, d = _build()
    res = [x for x in d["rows"] if x["name"] == "RESIDUAL"][0]
    assert res["evidence_status"] == "DIFFERS" and res["expected"] == "0.521668"
    p = d["roof_residual_proposal"]
    assert [(x["class"], x["qty"]) for x in p["parts"]] == [("TOLERANCE", "0.001332"), ("UNRESOLVED", "0.521668")]
    assert p["remainder_evidence"] == "DRAWING_CONFIRMED"
    assert d["roof_fields_own_m2"]["ROOF-430"] == "55.560332" and d["roof_fields_own_m2"]["ROOF-970"] == "146.532000"


def test_dev_no_coordinates_or_client_text_in_committed_files():
    for p in (HERE / "T626_DRAWN.json", HERE / "out" / "T626_ROW_EVIDENCE.json"):
        txt = p.read_text(encoding="utf-8")
        assert all(ord(ch) < 128 for ch in txt)                               # no drawing text (Arabic) copied
        nums = []

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if "handle" not in k:                                     # handles are entity ids, not numbers
                        walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
            elif isinstance(o, (int, float)) or (isinstance(o, str) and o.replace(".", "", 1).lstrip("-").isdigit()):
                nums.append(abs(float(o)))
        walk(json.loads(txt))
        assert nums and max(nums) < 1000                                      # areas / lengths in m, no mm coordinate
    drawn = json.loads((HERE / "T626_DRAWN.json").read_text(encoding="utf-8"))
    assert set(drawn) == {"schema", "source", "units", "rooms", "roof", "poolcourt"}


@pytest.mark.skipif(not DXF.exists(), reason="private drawing absent")
def test_dev_drawing_re_read_identical():
    import t626_extract as X
    assert (HERE / "T626_DRAWN.json").read_text(encoding="utf-8") == X.dumps(X.read(str(DXF)))


def test_dev_upturn_basis_settled_by_the_same_faces():
    _, d = _build()
    b = d["upturn_boundary_check_lm"]
    # T-546 upturn table rests on the T-074 hand boundaries 144.7285 lm; own chain perimeters on the same faces
    assert b["hand_boundaries_lm"] == "144.7285" and b["own_perimeters_lm"] == "144.727365"
    assert D(b["difference_lm"]) == D("-0.001135") and abs(D(b["largest_room_difference"][1])) < D("0.002")
