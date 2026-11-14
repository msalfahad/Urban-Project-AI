"""T-771: every family without a candidate line gets new lines or one disposition; the committed set reproduces."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("fill_t771", ROOT / "research/agents_t771/fill_t771.py")
F = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(F)
LABELS = {"MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY"}
KINDS = {"NOT_APPLICABLE_WITH_EVIDENCE", "COVERED_BY_LINE", "COVERED_BY_ROW", "REGISTER_NO_LINE", "PARKED", "HELD_MEP_STAGE"}


@pytest.fixture(scope="module")
def built():
    return F.build()


def validate(d, missing):
    """The acceptance as a check: returns a list of problems (empty = pass)."""
    p = []
    fams = {n["family"] for n in d["new_lines"]} | set(d["dispositions"])
    p += [f"family not covered: {f}" for f in sorted(set(missing) - fams)]
    for n in d["new_lines"]:
        if n.get("label") not in LABELS:
            p.append(f"bad label {n['item_code']}")
        if not n.get("basis"):
            p.append(f"no basis {n['item_code']}")
        has_net = n.get("net") is not None
        has_rng = n.get("low") is not None and n.get("high") is not None
        if has_net == has_rng:
            p.append(f"no figure (blank) or both {n['item_code']}")
        if has_net and n["net"] == 0:
            p.append(f"zero figure {n['item_code']}")
        if has_rng and n["high"] < n["low"]:
            p.append(f"range reversed {n['item_code']}")
    for f, v in d["dispositions"].items():
        if v["disposition"] not in KINDS or not v.get("evidence"):
            p.append(f"bad disposition {f}")
    if set(d["summary"]["missing_sheet_after_wiring"]) - {"B12-02", "B12-03", "B12-04", "B12-05"}:
        p.append("Missing sheet keeps a non-MEP family")
    return p


def test_committed_set_reproduces(built):
    assert json.loads((F.OUT / "FIX_ROWS.json").read_text()) == json.loads(json.dumps(built))


def test_every_missing_family_covered_and_labelled(built):
    missing = F.missing_families(F.load(F.MASTER), F.load(F.IDX)["lines"])
    assert len(missing) == 39
    assert validate(built, missing) == []
    assert built["summary"]["missing_sheet_after_wiring"] == ["B12-02", "B12-03", "B12-04", "B12-05"]


def test_every_b12_fixture_kind_counted(built):
    codes = {n["item_code"]: n["net"] for n in built["new_lines"] if n["family"] == "B12-01"}
    assert codes["MEP.SAN.WC"] == 12 and codes["MEP.SAN.BASIN"] == 17
    assert codes["MEP.SAN.FLOOR_DRAIN_4IN"] + codes["MEP.SAN.FLOOR_DRAIN_3IN"] == 19
    assert codes["MEP.SAN.SHOWER_TRAY"] + codes["MEP.SAN.SHOWER_WALKIN"] == 6


def test_spatter_equals_its_carrier_once(built):
    sd = {n["element_id"]: n["net"] for n in built["new_lines"] if n["item_code"] == "FIN.SPATTER_DASH"}
    assert set(sd) == {"SPATTER:INTERIOR", "SPATTER:EXTERIOR", "SPATTER:FENCE"}
    assert all(v > 0 for v in sd.values())


def test_carrier_total_hand_fixture():
    # non-Alsenan: 3 plaster lines (released 10.0, held 4 .. 6 -> 5.0, blank -> fix row 7.5) and one excluded line
    lines = [dict(line_id="a", item_code="FIN.PLASTER", unit="m2", **{"class": "RELEASED"}, measured_net=10.0, held_low=None, held_high=None),
             dict(line_id="b", item_code="FIN.PLASTER", unit="m2", **{"class": "HELD"}, measured_net=None, held_low=4.0, held_high=6.0),
             dict(line_id="c", item_code="FIN.PLASTER", unit="m2", **{"class": "HELD"}, measured_net=None, held_low=None, held_high=None),
             dict(line_id="d", item_code="FIN.PLASTER", unit="m2", **{"class": "EXCLUDED"}, measured_net=99.0, held_low=None, held_high=None)]
    assert F.carrier_total(lines, "FIN.PLASTER", "m2", {"c": {"net": 7.5}}) == (22.5, 0)
    # adverse: a blank carrier is reported, never summed as 0
    assert F.carrier_total(lines, "FIN.PLASTER", "m2", {}) == (15.0, 1)


def test_adverse_blank_zero_uncovered_refused(built):
    missing = F.missing_families(F.load(F.MASTER), F.load(F.IDX)["lines"])
    d = copy.deepcopy(built)
    d["new_lines"][0].pop("net")                      # blank line
    d["new_lines"][1]["net"] = 0                      # zero figure
    d["new_lines"][2]["label"] = "GUESS"              # unknown label
    d["dispositions"].pop("B3-03")                    # a family left uncovered
    d["dispositions"]["B4-11"]["disposition"] = "SKIPPED"
    d["summary"]["missing_sheet_after_wiring"].append("B9-03")
    probs = validate(d, missing)
    assert any("blank" in x for x in probs) and any("zero" in x for x in probs)
    assert any("bad label" in x for x in probs) and "family not covered: B3-03" in probs
    assert "bad disposition B4-11" in probs and "Missing sheet keeps a non-MEP family" in probs
