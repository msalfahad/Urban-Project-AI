"""R8.2 — the source capability register (§5-§7) and the per-entity census."""

from __future__ import annotations

import pytest

from engine.source import capability as CAP
from engine.source import findings as F
from engine.source.cad import census, kernel, libredwg_map as L
from tests.r8_0 import libredwg_builder as B, scenes as S

REQUIRED_KINDS = ("LINE", "ARC", "CIRCLE", "LWPOLYLINE", "ELLIPSE", "INSERT", "MINSERT", "ATTRIB", "ATTDEF", "TEXT",
                  "MTEXT", "DIMENSION", "HATCH", "POINT", "SOLID", "WIPEOUT", "IMAGE", "OLE2FRAME",
                  "ACAD_PROXY_ENTITY", "CUSTOM_CLASS", "XREF", "ANONYMOUS_BLOCK", "DYNAMIC_BLOCK")
REQUIRED_FIELDS = ("source_kind", "routes", "physical_geometry_support", "source_geometry_exact",
                   "downstream_measurement_supported", "identity_support", "text_support", "completeness_effect",
                   "known_decoder_limitations", "default_finding", "impacts", "required_validation",
                   "downstream_allowed_uses")


@pytest.mark.parametrize("kind", REQUIRED_KINDS)
def test_every_required_kind_has_a_complete_row(kind):
    row = CAP.row(kind)
    for f in REQUIRED_FIELDS:
        assert f in row, (kind, f)
    assert set(row["routes"]) == {CAP.D1, CAP.D2}


def test_no_kind_is_deleted_or_called_noise():
    for row in CAP.REGISTER:
        text = (row["note"] + " ".join(row["downstream_allowed_uses"])).lower()
        assert "ignore" not in text and "delete" not in text.replace("never deleted", "")
        assert "noise" not in text.replace('"noise"', "")


def test_point_is_carried_not_region_forming_and_not_deleted():
    r = CAP.row("POINT")
    assert r["physical_geometry_support"] == "CARRIED_ANCHOR_ONLY"
    assert "NOT REGION-FORMING BY DEFAULT" in r["note"] and "never deleted" in r["note"]


def test_solid_is_not_a_wall_and_not_discarded():
    r = CAP.row("SOLID")
    assert r["default_finding"] == F.UNVERIFIED_FOR_QTO_USE and "not a wall" in r["note"]
    assert CAP.FINAL_GEOMETRY not in r["downstream_allowed_uses"]


def test_hatch_is_never_wall_geometry_by_type():
    r = CAP.row("HATCH")
    assert CAP.FINAL_GEOMETRY not in r["downstream_allowed_uses"] and "never wall geometry" in r["note"]


def test_exact_source_geometry_is_not_downstream_support():
    for kind in ("ELLIPSE", "ELLIPTICAL_ARC_FROM_NON_UNIFORM_SCALE"):
        r = CAP.row(kind)
        assert r["source_geometry_exact"] is True and r["downstream_measurement_supported"] is False
        assert r["downstream_allowed_uses"] == [CAP.PREVIEW]


def test_dynamic_block_geometry_usable_identity_blocked():
    r = CAP.row("DYNAMIC_BLOCK")
    assert CAP.FINAL_GEOMETRY in r["downstream_allowed_uses"]
    assert ["IDENTITY", "BLOCKING"] in r["impacts"] and ["GEOMETRY", "INFO"] in r["impacts"]
    assert any("native AutoCAD" in v for v in r["required_validation"])


def test_minsert_real_mapping_stays_unverified_and_cannot_be_final():
    r = CAP.row("MINSERT")
    assert r["routes"][CAP.D1] == "SOURCE_MAPPING_UNVERIFIED" and CAP.FINAL_GEOMETRY not in r["downstream_allowed_uses"]


def test_named_classes_get_their_register_impacts_in_d1():
    dec = B.build({"entities": [{"kind": "LINE", "a": (0, 0), "b": (1, 0)}]})
    line = next(o for o in dec["OBJECTS"] if o.get("entity") == "LINE")
    for i, name in enumerate(("WIPEOUT", "IMAGE", "AEC_WALL")):
        dec["OBJECTS"].append({"entity": name, "type": 530 + i, "handle": [0, 1, 700 + i],
                               "ownerhandle": line["ownerhandle"], "layer": line["layer"]})
    rg = kernel.realise(L.to_document(dec))
    imp = {f.detail.split()[1] if f.detail.startswith("class-based entity") else f.detail.split()[1]: f.impacts
           for f in rg.findings if f.code == F.CUSTOM_CLASS}
    got = sorted(f.impacts for f in rg.findings if f.code == F.CUSTOM_CLASS)
    assert ((F.PRESENTATION, F.REVIEW),) in got                          # WIPEOUT
    assert ((F.DOCUMENT_CONTENT, F.BLOCKING),) in got                    # IMAGE
    assert ((F.GEOMETRY_COMPLETENESS, F.BLOCKING),) in got               # unknown class: may be the wall
    assert imp


def test_point_solid_attdef_are_carried_with_their_anchor():
    dec = B.build({"entities": [{"kind": "LINE", "a": (0, 0), "b": (1, 0)}]})
    line = next(o for o in dec["OBJECTS"] if o.get("entity") == "LINE")
    base = {"ownerhandle": line["ownerhandle"], "layer": line["layer"]}
    dec["OBJECTS"] += [
        {"entity": "POINT", "type": 27, "handle": [0, 1, 801], "x": 5.0, "y": 6.0, **base},
        {"entity": "SOLID", "type": 31, "handle": [0, 1, 802], "corner1": [0, 0], "corner2": [1, 0], "corner3": [0, 1],
         "corner4": [1, 1], **base},
        {"entity": "ATTDEF", "type": 3, "handle": [0, 1, 803], "ins_pt": [2.0, 2.0], "tag": "NO", **base},
    ]
    doc = L.to_document(dec)
    rg = kernel.realise(doc)
    kinds = sorted(c["kind"] for c in rg.carried)
    assert kinds == ["ATTDEF", "POINT", "SOLID"]
    assert [f.code for f in rg.findings] == [F.UNVERIFIED_FOR_QTO_USE]
    pt = next(o for o in doc.entities if o.kind == "POINT")
    assert pt.geometry.anchor == (5.0, 6.0)


def test_census_rows_carry_location_and_impacts():
    scene = {"blocks": {"OLEBLK": {"entities": [{"kind": "OLE2FRAME"}, {"kind": "LINE", "a": (0, 0), "b": (1, 0)}]}},
             "entities": [S._insert("OLEBLK")]}
    doc = L.to_document(B.build(scene))
    rows = census.capability_register(doc)
    (r,) = [r for r in rows if r["code"] == F.SKIPPED]
    assert r["handle"] and r["type_code"] == 74 and len(r["instance_path"]) == 1
    assert {"domain": "DOCUMENT_CONTENT", "severity": "BLOCKING"} in r["impacts"]


def test_census_text_undecodable_is_never_an_identity_source():
    doc = L.to_document(B.build({"entities": [{"kind": "TEXT", "at": (0, 0), "text": "D\udcc701"}]}))
    (r,) = [r for r in census.capability_register(doc) if r["code"] == F.TEXT_UNDECODABLE]
    assert r["identity_source_allowed"] is False


def test_census_dynamic_block_rows_scope_the_uncertainty():
    scene = {"blocks": {"*U9": {"entities": [{"kind": "LINE", "a": (0, 0), "b": (900, 0)}]}},
             "entities": [{"kind": "INSERT", "block": "*U9", "at": (0.0, 0.0)}]}
    doc = L.to_document(B.build(scene))
    (r,) = [r for r in census.capability_register(doc) if r["code"] == F.DYNAMIC_BLOCK_UNRESOLVED]
    assert r["identity_claim_allowed"] is False and r["geometry_evaluated"] is True
    assert {"domain": "IDENTITY", "severity": "BLOCKING"} in r["impacts"]
    assert kernel.realise(doc).segments                                   # geometry not blocked
