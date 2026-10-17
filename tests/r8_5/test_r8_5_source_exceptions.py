"""R8.5 §10-§14 — source exceptions resolved only by positive evidence; V-CAD-5 unchanged.

Synthetic raw objects in the LibreDWG JSON shape; the entity-graphics stream is built byte by byte in the
documented record layout. Nothing is declared irrelevant because of how it looks."""

from __future__ import annotations

import struct

from engine.source import source_exceptions as SX
from engine.source import findings as F
from tests.r8_0 import libredwg_builder as B
from tests.r8_0.k1_harness import _imports, apply_test_schema_extensions
from tests.r8_0.scenes import SKIP_CASES

REGION = (0.0, 0.0, 100.0, 100.0)
REL = {"A-DIM": "dimension layer (test)", "A-WALL": "wall layer (test)"}


def graphics(*records):
    body = b""
    for typ, payload in records:
        body += struct.pack("<ii", 8 + len(payload), typ) + payload
    return (struct.pack("<ii", 8 + len(body), len(records)) + body).hex()


def poly(*pts):
    return 6, struct.pack("<i", len(pts)) + b"".join(struct.pack("<3d", x, y, 0.0) for x, y in pts)


def text(x, y):
    return 11, struct.pack("<3d", x, y, 0.0) + b"\0" * 64


def row(handle="99", layer="A-DIM", code=F.CUSTOM_CLASS, path=()):
    return {"obs_id": f"D1:{handle}", "handle": handle, "code": code, "source_type": "LIBREDWG:600:", "layer": layer,
            "instance_path": list(path), "impacts": [{"domain": "GEOMETRY_COMPLETENESS", "severity": "BLOCKING"}]}


def doc():
    _, _, lm = _imports()
    dec = B.build({"entities": [{"kind": "LINE", "a": (0, 0), "b": (1, 0)}]})
    return apply_test_schema_extensions(dec, lm.to_document(dec))


ARCDIM = {"dxfname": "ARC_DIMENSION", "cppname": "AcDbArcDimension", "appname": "ObjectDBX Classes"}
RTEXT = {"dxfname": "RTEXT", "cppname": "RText", "appname": "RText|AutoCAD Express Tool"}
WIPE = {"dxfname": "WIPEOUT", "cppname": "AcDbWipeout", "appname": "WipeOut"}


def diesel_bits(s):
    return (b"\x00" + s.encode("ascii") + b"\x00").hex()


def test_proxy_graphics_decode_and_quality():
    g = SX.proxy_graphics(graphics(poly((1, 2), (3, 4))))
    assert g["quality"] == SX.EXACT and g["points"] == [(1.0, 2.0), (3.0, 4.0)]
    assert SX.proxy_graphics(graphics(poly((1, 2), (3, 4)), text(5, 5)))["quality"] == SX.POINT_ONLY   # glyphs unbounded
    assert SX.proxy_graphics(graphics((33, b"\0" * 16)))["quality"] == SX.LOCATION_UNRESOLVED       # unparsed geometry
    assert SX.proxy_graphics(None)["quality"] == SX.LOCATION_UNRESOLVED


def test_image_extent_from_its_own_fields():
    raw = {"entity": "IMAGE", "pt0": [10.0, 20.0, 0.0], "uvec": [0.5, 0.0, 0.0], "vvec": [0.0, 0.5, 0.0], "size": [4.0, 2.0]}
    pts, q, _ = SX.raw_extent(raw)
    assert q == SX.EXACT and SX.placed_bounds(pts, SX.instance_matrix(doc(), ())) == (10.0, 20.0, 12.0, 21.0)


def test_located_outside_is_irrelevant_even_on_a_relevant_layer():
    raw = {"_subclass": "AcDbEntity", "preview": graphics(poly((200, 200), (210, 210)))}
    e = SX.classify(row(layer="A-WALL"), raw, None, doc(), "R", REGION, REL)
    assert e.state == SX.PROFILE_IRRELEVANT_PROVEN and e.region_overlap == "DISJOINT"


def test_unknown_class_inside_on_relevant_layer_blocks():
    raw = {"_subclass": "AcDbEntity", "preview": graphics(poly((10, 10), (20, 20)))}
    e = SX.classify(row(layer="A-WALL"), raw, {"dxfname": "AEC_WALL", "cppname": "AecDbWall"}, doc(), "R", REGION, REL)
    assert e.state == SX.PROFILE_RELEVANT_BLOCKING
    (f,) = SX.region_findings([(e, ((F.GEOMETRY_COMPLETENESS, F.BLOCKING),))])
    assert F.GEOMETRY_COMPLETENESS in f.blocking_domains


def test_unplaceable_unknown_on_relevant_layer_fails_closed():
    e = SX.classify(row(layer="A-WALL"), {"_subclass": "AcDbEntity"}, None, doc(), "R", REGION, REL)
    assert e.location_quality == SX.LOCATION_UNRESOLVED and e.state == SX.PROFILE_RELEVANT_BLOCKING
    raster = {"entity": "IMAGE", "_subclass": "AcDbRasterImage"}                 # role known, extent unknown
    e = SX.classify(row(layer="A-WALL"), raster, {"dxfname": "IMAGE", "cppname": "AcDbRasterImage"}, doc(), "R", REGION, REL)
    assert e.state == SX.UNRESOLVED_REVIEW_REQUIRED
    (f,) = SX.region_findings([(e, ((F.DOCUMENT_CONTENT, F.BLOCKING),))])
    assert F.GEOMETRY_COMPLETENESS in f.blocking_domains                          # an image may be a scanned plan


def test_image_inside_region_is_not_irrelevant_because_it_is_an_image():
    raw = {"entity": "IMAGE", "_subclass": "AcDbRasterImage", "pt0": [5, 5, 0], "uvec": [1, 0, 0], "vvec": [0, 1, 0],
           "size": [10.0, 10.0]}
    e = SX.classify(row(layer="A-WALL"), raw, {"dxfname": "IMAGE", "cppname": "AcDbRasterImage"}, doc(), "R", REGION, REL)
    assert e.state == SX.UNRESOLVED_REVIEW_REQUIRED and e.region_overlap == "OVERLAPS"


def test_class_role_needs_two_agreeing_source_fields():
    raw = {"_subclass": "AcDbEntity", "preview": graphics(poly((10, 10), (20, 20)))}
    e = SX.classify(row(), raw, ARCDIM, doc(), "R", REGION, REL)                  # record only: not proven
    assert e.class_role is None and e.state == SX.PROFILE_RELEVANT_BLOCKING
    raw["_subclass"] = "AcDbArcDimension"
    e = SX.classify(row(), raw, ARCDIM, doc(), "R", REGION, REL)
    assert e.state == SX.ANNOTATION_ONLY_PROVEN and e.influence["wall"] is False and e.influence["dimension"] is True


def test_wipeout_is_presentation_only_when_proven():
    raw = {"entity": "WIPEOUT", "_subclass": "AcDbWipeout", "preview": graphics(poly((10, 10), (12, 11)))}
    e = SX.classify(row(layer="A-WALL"), raw, WIPE, doc(), "R", REGION, REL)
    assert e.state == SX.PRESENTATION_ONLY_PROVEN
    (f,) = SX.region_findings([(e, ())])
    assert not f.blocking_domains


def test_rtext_plot_stamp_versus_unknown_text():
    stamp = {"_subclass": "AcDbEntity", "preview": graphics(poly((10, 10), (60, 12))),
             "unknown_bits": diesel_bits('$(getvar, "dwgprefix")$(getvar, "dwgname")  $(edtime, 0, MON DD"," YYYY)')}
    e = SX.classify(row(layer="A-WALL"), stamp, RTEXT, doc(), "R", REGION, REL)
    assert e.state == SX.ANNOTATION_ONLY_PROVEN and e.influence["label"] is False
    label = dict(stamp, unknown_bits=diesel_bits('$(getvar, "users1") KITCHEN AND DINING AREA'))
    e = SX.classify(row(layer="A-WALL"), label, RTEXT, doc(), "R", REGION, REL)
    assert e.state != SX.ANNOTATION_ONLY_PROVEN                                   # not a plot stamp: role unproven


def test_block_owned_object_is_placed_through_its_instance():
    _, kernel, lm = _imports()
    dec = B.build({"blocks": {"TB": {"entities": [{"kind": "LINE", "a": (0, 0), "b": (1, 0)}]}},
                   "entities": [{"kind": "INSERT", "block": "TB", "at": (500.0, 0.0), "scale": (1.0, 1.0), "rot": 0.0,
                                 "extrusion": (0.0, 0.0, 1.0)}]})
    d = apply_test_schema_extensions(dec, lm.to_document(dec))
    ins = next(o for o in d.entities if o.kind == "INSERT")
    raw = {"_subclass": "AcDbEntity", "preview": graphics(poly((0, 0), (5, 5)))}
    e = SX.classify(row(layer="A-WALL", path=(ins.obs_id,)), raw, None, d, "R", REGION, REL)
    assert e.placed_bounds == (500.0, 0.0, 505.0, 5.0) and e.state == SX.PROFILE_IRRELEVANT_PROVEN


def test_v_cad_5_legacy_f19_contract_unchanged():
    from tests.r8_0 import targets
    scene = next(s for s in SKIP_CASES if s[0] == "F19")[3]
    got = targets.call("SOURCE_PROFILE", decode=B.build(scene), profile="CAD_PROFILE")
    assert got["V-CAD-5"] == "FAIL" and got["region_release"] == "BLOCKED"
