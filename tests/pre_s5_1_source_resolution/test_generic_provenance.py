"""PRE-S5.1 §1: generic element identity (rebar_provenance) with S4 backward compatibility.

* a ground beam carries ELEMENT_OCCURRENCE_ID / ELEMENT_MARK / ELEMENT_FAMILY; a FOOTING_* key on it is rejected;
* FOOTING_* are aliases for the FOOTING family only and must equal ELEMENT_*;
* the generic validator gives exactly validate_s4_part's verdict on the frozen S4 provenance log and its mutations;
* ground_system_provenance runs the generic validator (no footing view of a beam) and writes no FOOTING_* key.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from engine.source import accurate_boq_rebar as AR
from engine.source import ground_system_provenance as GP
from engine.source import rebar_provenance as RP

ROOT = Path(__file__).resolve().parents[2]
S4_LOG = ROOT / "research/alsenan_footing_rebar_s4/FOOTING_REBAR_PROVENANCE.jsonl"
SHA = "a" * 64


def base(**over):
    p = {"PROJECT_ID": "PRJ", "DRAWING_ID": "DRW.dxf", "DRAWING_SHA": SHA, "REVISION": "REV-A", "SHEET_REGION": "GBP",
         "SOURCE_HANDLES": ["A", "B"], "SOURCE_TEXT": "3Ø14", "COMPONENT": "BEAM_TOP_BAR", "RULE_ID": "R",
         "CONVENTION_ID": "C", "MEASUREMENT_STATE": "MEASURED", "AUTHORITY_STATE": "SOURCE_EXPLICIT",
         "RELEASE_STATE": "LOWER_BOUND", "FORMULA": "f", "INPUTS": {}, "ENGINE_COMMIT": "1234567+code:" + "b" * 16,
         "REGISTER_VERSION": "V1", "CALCULATION_ROUND": "S5", "LOW": 1.0, "BEST": 1.0, "HIGH": None,
         "UNQUANTIFIED_COMPONENTS": ["ANCHORAGE"]}
    p.update(over)
    return p


def part(prov, comp="BEAM_TOP_BAR", cat="GROUND_BEAMS"):
    return {"part_id": "p1", "category": cat, "component": comp, "state": prov["RELEASE_STATE"], "kg": 1.0,
            "basis": ["STRUCTURAL_DETAIL"], "provenance": prov}


def gb_identity():
    return RP.identity_fields(family="GROUND_BEAM", occurrence_id="GSO-X-1", mark="GB")


def test_generic_identity_on_a_ground_beam_is_accepted():
    RP.validate_part(part(base(**gb_identity())))
    assert RP.element_identity(base(**gb_identity()))["ELEMENT_FAMILY"] == "GROUND_BEAM"


def test_fake_footing_identity_on_a_ground_beam_is_rejected():
    # the beam id placed in the footing slots as its authoritative identity (the pre-S5 shortcut)
    fake = base(ELEMENT_FAMILY="GROUND_BEAM", FOOTING_OCCURRENCE_ID="GSO-X-1", FOOTING_MARK="GB")
    with pytest.raises(AR.AccurateRebarError, match="FOOTING"):
        RP.validate_part(part(fake))
    # even alongside a correct generic identity
    both = base(**gb_identity(), FOOTING_OCCURRENCE_ID="GSO-X-1")
    with pytest.raises(RP.ProvenanceError, match="alias for the FOOTING family only"):
        RP.validate_part(part(both))


def test_missing_generic_identity_is_named():
    with pytest.raises(RP.ProvenanceError, match="ELEMENT_FAMILY"):
        RP.validate_part(part(base(ELEMENT_OCCURRENCE_ID="X", ELEMENT_MARK="M")))
    with pytest.raises(RP.ProvenanceError, match="ELEMENT_MARK"):
        RP.validate_part(part(base(ELEMENT_OCCURRENCE_ID="X", ELEMENT_FAMILY="STRAP_BEAM")))


def test_footing_aliases_must_equal_the_element_identity():
    f = RP.identity_fields(family="FOOTING", occurrence_id="FOCC-1", mark="F1")
    assert f["FOOTING_OCCURRENCE_ID"] == "FOCC-1" and f["FOOTING_MARK"] == "F1"
    prov = base(**f, COMPONENT="FOOTING_BOTTOM_LONG")
    RP.validate_part(part(prov, comp="FOOTING_BOTTOM_LONG", cat="FOUNDATIONS"))
    prov["FOOTING_MARK"] = "F2"
    with pytest.raises(RP.ProvenanceError, match="must equal"):
        RP.validate_part(part(prov, comp="FOOTING_BOTTOM_LONG", cat="FOUNDATIONS"))


def test_a_frozen_s4_record_reads_as_the_footing_family():
    r = json.loads(S4_LOG.read_text(encoding="utf-8").splitlines()[0])
    ident = RP.element_identity(r["provenance"])
    assert ident == {"ELEMENT_FAMILY": "FOOTING", "ELEMENT_OCCURRENCE_ID": r["provenance"]["FOOTING_OCCURRENCE_ID"],
                     "ELEMENT_MARK": r["provenance"]["FOOTING_MARK"]}


MUTATIONS = [
    lambda p: None,
    lambda p: p["provenance"].pop("FOOTING_MARK"),
    lambda p: p["provenance"].update(FOOTING_OCCURRENCE_ID=""),
    lambda p: p["provenance"].update(DRAWING_SHA="nope"),
    lambda p: p["provenance"].update(AUTHORITY_STATE="UNRESOLVED"),
    lambda p: p["provenance"].update(RELEASE_STATE="PROVISIONAL"),
    lambda p: p["provenance"].update(INPUTS=[]),
    lambda p: p["provenance"].update(LOW=1.0, BEST=0.0, HIGH=2.0, UNQUANTIFIED_COMPONENTS=[]),
    lambda p: p["provenance"].update(SOURCE_HANDLES=[]),
    lambda p: p["provenance"].update(MEASUREMENT_STATE="GUESSED"),
]


def _ok(f, p):
    try:
        f(p)
        return True
    except AR.AccurateRebarError:
        return False


def test_generic_validator_equals_the_frozen_s4_validator_on_every_s4_record():
    recs = [json.loads(x) for x in S4_LOG.read_text(encoding="utf-8").splitlines()]
    assert len(recs) >= 80
    n = 0
    for r in recs:
        for m in MUTATIONS:
            p = {"part_id": r["part_id"], "category": "FOUNDATIONS", "component": r["provenance"]["COMPONENT"],
                 "state": r["state"], "kg": r["kg"], "basis": ["SCHEDULE"], "provenance": copy.deepcopy(r["provenance"])}
            m(p)
            assert _ok(AR.validate_s4_part, copy.deepcopy(p)) == _ok(RP.validate_part, copy.deepcopy(p)), r["part_id"]
            n += 1
    assert n == len(recs) * len(MUTATIONS)


def test_s5_part_runs_the_generic_validator_and_never_a_footing_view():
    t = GP.template(family="GROUND_BEAM", occurrence_id="GSO-X-1", mark="GB",
                    start_node={"kind": "COLUMN", "refs": ["C1"]}, end_node={"kind": "FOOTING", "refs": ["F1"]},
                    handles=["A"], detail_id=["P13-GB-LT5M"], applicability="EXPLICIT_LENGTH_CONDITION",
                    context={"PROJECT_ID": "P", "REVISION": "R", "DRAWING_ID": "D", "DRAWING_SHA": SHA,
                             "ENGINE_COMMIT": "e", "REGISTER_VERSION": "V", "CALCULATION_ROUND": "S5"})
    assert not any(k.startswith("FOOTING_") for k in t) and GP.provenance_ready(t)
    prov = base(**{k: v for k, v in t.items() if v is not None})
    GP.validate_s5_part(part(prov))
    with pytest.raises(ValueError):
        GP.validate_s5_part(part(dict(prov, FOOTING_OCCURRENCE_ID="GSO-X-1")))
    with pytest.raises(ValueError):                                           # a footing is not an S5 member
        GP.validate_s5_part(part(dict(prov, ELEMENT_FAMILY="FOOTING", FOOTING_OCCURRENCE_ID="GSO-X-1",
                                      FOOTING_MARK="GB")))
    assert not GP.provenance_ready(dict(t, FOOTING_MARK="GB"))
    with pytest.raises(ValueError):
        GP.template(family="FOOTING", occurrence_id="x", mark="m", start_node={}, end_node={}, handles=[],
                    detail_id=[], applicability="X", context={})


def test_contract_fields_are_the_s4_fields_with_the_generic_identity():
    assert set(RP.BASE_FIELDS) == (set(AR.S4_PROVENANCE_FIELDS) - set(RP.FOOTING_ALIASES)) | set(RP.IDENTITY_FIELDS)
    assert set(GP.S5_PROVENANCE_FIELDS) == set(RP.BASE_FIELDS) | set(GP.S5_EXTRA_FIELDS)
    assert not set(GP.S5_PROVENANCE_FIELDS) & set(RP.FOOTING_ALIASES)
