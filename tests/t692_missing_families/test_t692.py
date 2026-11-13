"""T-692 missing BOQ families census (research/agents_t692). Synthetic registry (not the training villa) with the
adverse cases (a registry family with no class, a doubled id, an illegal class, a class for a family that is not
missing, a NOT_IN_CANDIDATE family whose item code is in the candidate), then the real master 1.68.0 reconciled by id."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t692"))
import t692_census as C  # noqa: E402
import t692_alsenan as A  # noqa: E402
import t692_dxf_census as D  # noqa: E402


def fam(code, cap, state, codes=()):
    return {"code": code, "group": code[:2], "item_en": code, "unit": "m2", "capability": cap,
            "item_codes": list(codes), "candidate": {"state": state}}


def cls(c="MEASURABLE FROM DRAWINGS", band="BUILDING", step="masonry", scale=1):
    return dict(cls=c, band=band, step=step, scale=scale, source="sheet X", evidence="piece Y", rule="rule Z",
                host="module W", dxf=None)


SYN = {"version": "9.0.0", "candidate_census": {"method_version": "SYN"}, "families": [
    fam("X1-01", "NOT_IMPLEMENTED", "NOT_IN_CANDIDATE"),
    fam("X1-02", "PARTIAL", "IN_CANDIDATE_BASE_LINES", ["X.BASE"]),
    fam("X1-03", "PARTIAL", "INTEGRATED_IN_CANDIDATE_AND_TESTED", ["X.DONE"]),
    fam("X1-04", "BLOCKED_BY_SOURCE", "NOT_IN_CANDIDATE"),
    fam("X1-05", "PARTIAL", "HELD_IN_CANDIDATE", ["X.HELD"]),
    fam("X1-06", "IMPLEMENTED_NOT_INTEGRATED", "NOT_IN_CANDIDATE", ["X.NEW"]),
]}
SYN_LINES = [{"item_code": "X.BASE"}, {"item_code": "X.DONE"}, {"item_code": "X.HELD"}]
SYN_CLASSES = {
    "X1-01": cls("OUT OF SCOPE", step="earthworks", band="EARTHWORKS_SITE", scale=0),
    "X1-02": cls("MEASURABLE FROM DRAWINGS", step="register", scale=0),
    "X1-04": cls("DESIGNER ITEM", band="MEP", step="mep", scale=2),
    "X1-06": cls("MEASURABLE FROM DRAWINGS", step="plaster_paint", scale=3),
}


def test_synthetic_selection_and_order():
    r = C.build(SYN, SYN_LINES, classes=SYN_CLASSES)
    # selected = 6 families - 1 integrated - 1 held = 4: primary 3 (X1-01, X1-04, X1-06), band 1 (X1-02)
    assert (r["primary"], r["base_lines_band"], r["selected"]) == (3, 1, 4)
    assert [x["code"] for x in r["rows"]] == ["X1-06", "X1-02", "X1-01", "X1-04"]  # building, earthworks, MEP last
    assert r["rows"][-1]["band"] == "MEP"
    assert r["class_counts"] == {"MEASURABLE FROM DRAWINGS": 2, "NEEDS OWNER RULE": 0, "DESIGNER ITEM": 1,
                                 "OUT OF SCOPE": 1}
    assert r["rows"][0]["candidate_lines_by_code"] == {"X.NEW": 0}


def test_registry_family_without_class_fails():
    c = dict(SYN_CLASSES)
    del c["X1-04"]
    with pytest.raises(ValueError, match="NO CLASS X1-04"):
        C.build(SYN, SYN_LINES, classes=c)


def test_class_for_a_family_that_is_not_missing_fails():
    c = dict(SYN_CLASSES, **{"X1-03": cls()})
    with pytest.raises(ValueError, match="CLASS FOR UNSELECTED X1-03"):
        C.build(SYN, SYN_LINES, classes=c)


def test_illegal_class_band_and_empty_evidence_fail():
    c = copy.deepcopy(SYN_CLASSES)
    c["X1-01"]["cls"] = "PROBABLY FINE"
    c["X1-02"]["band"] = "SOMEWHERE"
    c["X1-06"]["evidence"] = " "
    with pytest.raises(ValueError) as e:
        C.build(SYN, SYN_LINES, classes=c)
    msg = str(e.value)
    assert "BAD CLASS X1-01" in msg and "BAD BAND X1-02" in msg and "NO EVIDENCE X1-06" in msg


def test_doubled_family_id_fails():
    m = copy.deepcopy(SYN)
    m["families"].append(fam("X1-01", "NOT_IMPLEMENTED", "NOT_IN_CANDIDATE"))
    with pytest.raises(ValueError, match="DOUBLED X1-01"):
        C.build(m, SYN_LINES, classes=SYN_CLASSES)


def test_not_in_candidate_family_with_a_candidate_line_fails():
    # adverse: the registry says no line, the index carries one: the census must not hide the contradiction
    with pytest.raises(ValueError, match="LINE PRESENT FOR NOT_IN_CANDIDATE X1-06"):
        C.build(SYN, SYN_LINES + [{"item_code": "X.NEW"}], classes=SYN_CLASSES)


def test_keyword_count_on_synthetic_texts():
    s = ["SPATTER DASH 1:2", "Floor drain 3\"", "", None, "kitchen", "CANOPY steel"]
    c = D.count(s, {k: D.KEYWORDS[k] for k in ("spatter", "sanitary", "kitchen", "metalwork", "mesh")})
    assert c == {"spatter": 1, "sanitary": 1, "kitchen": 1, "metalwork": 1, "mesh": 0}


# ---- the real registry (master 1.68.0, candidate V3.0.67) -------------------------------------------------------------
@pytest.fixture(scope="module")
def real():
    return A.run(C.load(A.DXF_COUNTS))


def test_real_reconciles_by_id_to_the_owner_38(real):
    m = C.load(A.MASTER)
    st = [f["candidate"]["state"] for f in m["families"]]
    assert real["families_in_master"] == 104
    assert real["primary"] == st.count("NOT_IN_CANDIDATE") == 32
    assert real["base_lines_band"] == st.count("IN_CANDIDATE_BASE_LINES") == 6
    assert real["selected"] == 104 - st.count("INTEGRATED_IN_CANDIDATE_AND_TESTED") - st.count("HELD_IN_CANDIDATE") == 38
    ids = [r["code"] for r in real["rows"]]
    assert len(ids) == len(set(ids)) == 38
    ni = {f["code"] for f in m["families"] if f["capability"] == "NOT_IMPLEMENTED"}
    assert len(ni) == 9 and ni <= set(ids)
    assert sum(real["class_counts"].values()) == 38


def test_real_every_registry_missing_family_has_a_class():
    m = C.load(A.MASTER)
    prim, band = C.select(m)
    assert not C.validate([f["code"] for f in prim + band], C.FAMILY_CLASS)
    assert set(C.FAMILY_CLASS) == {f["code"] for f in prim + band}


def test_real_mep_last_and_earthworks_apart(real):
    bands = [r["band"] for r in real["rows"]]
    assert bands[-5:] == ["MEP"] * 5
    ew = [i for i, b in enumerate(bands) if b == "EARTHWORKS_SITE"]
    assert ew == list(range(ew[0], ew[0] + 4)) and ew[-1] < bands.index("MEP")
    assert {r["code"] for r in real["rows"] if r["band"] == "EARTHWORKS_SITE"} == {"B1-01", "B1-05", "B1-06", "B1-07"}


def test_real_first_five_have_drafts_and_the_census_reproduces(real):
    assert len(real["first_five"]) == 5 and all(x["draft"] for x in real["first_five"])
    old = json.loads((A.OUT / "T692_CENSUS.json").read_text(encoding="utf-8"))
    assert json.dumps(real, sort_keys=True) == json.dumps(old, sort_keys=True)


def test_real_no_quantity_is_produced(real):
    for r in real["rows"]:
        assert not any(k in r for k in ("quantity", "qty", "measured_net", "rate", "amount"))
