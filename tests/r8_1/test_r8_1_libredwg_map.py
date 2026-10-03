"""R8.1 — D1 (LibreDWG JSON) -> neutral observations: verified fields only, nothing silent.

Real-decode field verification lives in the research lab
(research/external_engine_lab/r8_1_real_drawing_characterisation.py); these
tests pin the mapper's behaviour on builder decodes.
"""

from __future__ import annotations

import pytest

from engine.source import findings as F
from engine.source import observations as O
from engine.source.cad import kernel, libredwg_map as L
from tests.r8_0 import libredwg_builder as B, scenes as S

from .helpers import BP, CURVE, curve_failures


def realise(dec):
    return kernel.realise(L.to_document(dec)).as_contract_dict()


def codes(got):
    return [f["code"] for f in got["findings"]]


# ---------------------------------------------------------------- field register

def test_field_register_statuses_are_from_the_closed_vocabulary():
    allowed = ("VERIFIED", "VERIFIED_BY_FLAG_PATTERN", "VERIFIED_PATH_VALUE_UNOBSERVED", "SOURCE_MAPPING_UNVERIFIED")
    for kind, fields in L.FIELD_REGISTER.items():
        for name, (_, status) in fields.items():
            assert any(status.startswith(a) for a in allowed), (kind, name, status)


def test_unverified_kinds_are_not_in_the_geometry_type_map():
    assert L.T_MINSERT not in L.KIND_BY_TYPE and L.T_PROXY not in L.KIND_BY_TYPE
    assert L.FIELD_REGISTER["MINSERT"]["grid"][1].startswith("SOURCE_MAPPING_UNVERIFIED")


def test_xref_flag_semantics_are_marked_unverified():
    bh = L.FIELD_REGISTER["BLOCK_HEADER"]
    assert bh["xref_resolved"][1].startswith("SOURCE_MAPPING_UNVERIFIED")
    assert bh["xref_unloaded"][1].startswith("SOURCE_MAPPING_UNVERIFIED")


# ---------------------------------------------------------------- D1 -> K1 on the truth scenes

@pytest.mark.parametrize("sid", sorted(CURVE))
def test_production_mapper_alone_reproduces_curve_truth(sid):
    """No test-schema extension needed: every field these scenes use is VERIFIED."""
    assert curve_failures(S.curve_case_truth(CURVE[sid]), realise(B.build(CURVE[sid][3]))) == []


@pytest.mark.parametrize("sid", sorted(BP))
def test_production_mapper_alone_reproduces_base_point_truth(sid):
    assert curve_failures(S.base_point_truth(BP[sid]), realise(B.build(BP[sid][3]))) == []


# ---------------------------------------------------------------- LWPOLYLINE extrusion flag

def _pline_decode(flag, extrusion="OMIT"):
    dec = B.build({"entities": [{"kind": "LWPOLYLINE", "pts": [(0, 0), (100, 0)], "bulges": [0.0, 0.0]}]})
    for o in dec["OBJECTS"]:
        if o.get("entity") == "LWPOLYLINE":
            o["flag"] = flag
            if extrusion == "OMIT":
                o.pop("extrusion", None)
            else:
                o["extrusion"] = extrusion
    return dec


def test_absent_lwpolyline_extrusion_with_bit_clear_is_the_default_and_recorded():
    doc = L.to_document(_pline_decode(0))
    (obs,) = doc.entities
    assert tuple(obs.extrusion) == O.DEFAULT_EXTRUSION
    assert ("extrusion", "DEFAULT_BY_FLAG_PATTERN") in obs.provenance
    assert realise(_pline_decode(0))["segments"] == [((0.0, 0.0), (100.0, 0.0))]


def test_absent_lwpolyline_extrusion_with_bit_set_is_unreadable_never_default():
    got = realise(_pline_decode(1))
    assert codes(got) == [F.FRAME_UNREADABLE] and got["segments"] == []


def test_present_lwpolyline_extrusion_is_used():
    got = realise(_pline_decode(1, [0.0, 0.0, -1.0]))
    assert got["segments"] == [((0.0, 0.0), (-100.0, 0.0))]


# ---------------------------------------------------------------- skipped / proxy / custom / conflicts

def _single(kind, type_code, **fields):
    dec = B.build({"entities": [{"kind": "LINE", "a": (0, 0), "b": (1, 0)}]})
    for o in dec["OBJECTS"]:
        if o.get("entity") == "LINE":
            o["entity"], o["type"] = kind, type_code
            o.update(fields)
    return dec


@pytest.mark.parametrize("type_code", [74, 2])
def test_ole2frame_is_skipped_whatever_type_code_the_decoder_gives(type_code):
    """The Al Rashed decode labels OLE2FRAME with type 2 (the ATTRIB code);
    the R8.0 census and cad_adapter both missed it for that reason."""
    got = realise(_single("OLE2FRAME", type_code))
    assert codes(got) == [F.SKIPPED]
    if type_code != 74:
        assert "type-code conflict" in got["findings"][0]["detail"]


def test_type_2_ole2frame_is_not_taken_for_an_attribute():
    dec = B.build({"blocks": {"CURVES": S.CURVES_BLOCK}, "entities": [S._insert("CURVES")]})
    ins = next(o for o in dec["OBJECTS"] if o.get("entity") == "INSERT")
    dec["OBJECTS"].append({"entity": "OLE2FRAME", "type": 2, "handle": [0, 1, 999],
                           "ownerhandle": [4, 1, ins["handle"][-1], ins["handle"][-1]], "layer": ins["layer"]})
    got = realise(dec)
    assert got["attributes"] == [] and F.SKIPPED in codes(got)


def test_proxy_is_its_own_category():
    assert codes(realise(_single("ACAD_PROXY_ENTITY", 498))) == [F.PROXY]


@pytest.mark.parametrize("type_code", [500, 512, 777])
def test_class_based_entities_are_custom_class(type_code):
    assert codes(realise(_single("AEC_WALL", type_code))) == [F.CUSTOM_CLASS]


def test_unknown_type_is_unhandled_not_dropped():
    assert codes(realise(_single("SPLINE", 36))) == [F.UNHANDLED]


def test_name_type_conflict_is_not_resolved_by_guessing():
    got = realise(_single("CIRCLE", 19))                   # named CIRCLE, typed LINE
    assert codes(got) == [F.SOURCE_TYPE_CONFLICT] and got["segments"] == [] and got["circles"] == []


def test_missing_required_field_is_unsupported_not_zero():
    dec = B.build({"entities": [{"kind": "ARC", "c": (0, 0), "r": 5, "a0": 0, "a1": 90}]})
    for o in dec["OBJECTS"]:
        if o.get("entity") == "ARC":
            del o["radius"]
    assert codes(realise(dec)) == [F.UNSUPPORTED]


def test_delimiters_are_counted_not_realised():
    dec = B.build({"entities": [{"kind": "LINE", "a": (0, 0), "b": (1, 0)}]})
    dec["OBJECTS"] += [{"entity": n, "type": t, "handle": [0, 1, 900 + t], "ownerhandle": [4, 1, 2, 2]}
                       for n, t in (("BLOCK", 4), ("ENDBLK", 5), ("SEQEND", 6))]
    doc = L.to_document(dec)
    delims = {k: v for k, v in doc.notes.items() if k.startswith("delimiter_")}
    assert len(doc.entities) == 1 and delims == {"delimiter_BLOCK": 1, "delimiter_ENDBLK": 1, "delimiter_SEQEND": 1}
    assert doc.notes["raw_entity_rows"] == 4                       # R8.2 conservation: every row counted


# ---------------------------------------------------------------- block headers

def test_nameless_block_header_is_detected_by_type_and_its_content_is_not_top_level():
    """P7757: 409/442 BLOCK_HEADER rows have an empty name AND an empty object
    name. cad_adapter emits their 2,308 entities as top-level geometry; D1 must not."""
    dec = B.build({"blocks": {"CURVES": S.CURVES_BLOCK}, "entities": [S._insert("CURVES", at=(10.0, 0.0))]})
    for o in dec["OBJECTS"]:
        if o.get("type") == 49 and o.get("name") == "CURVES":
            o["name"], o["object"] = "", ""
    doc = L.to_document(dec)
    assert len(doc.entities) == 1 and doc.entities[0].kind == O.INSERT
    (blk,) = [b for b in doc.blocks.values() if not b.name_readable]
    assert len(blk.entities) == 3
    got = kernel.realise(doc).as_contract_dict()
    assert codes(got) == [F.BLOCK_NAME_UNREADABLE]
    assert len(got["arcs"]) == 1 and got["arcs"][0]["CENTER"] == (1010.0, 0.0)


def test_is_xref_ref_is_not_an_xref_flag():
    dec = B.build({"blocks": {"CURVES": S.CURVES_BLOCK}, "entities": [S._insert("CURVES")]})
    for o in dec["OBJECTS"]:
        if o.get("type") == 49:
            o["is_xref_ref"] = 1                            # set on every P7757 block
    doc = L.to_document(dec)
    assert all(b.xref is None for b in doc.blocks.values())
    assert realise(dec)["findings"] == []


def test_missing_base_point_is_read_as_origin_with_a_visible_finding():
    dec = B.build({"blocks": {"CURVES": S.CURVES_BLOCK}, "entities": [S._insert("CURVES")]})
    for o in dec["OBJECTS"]:
        if o.get("name") == "CURVES":
            del o["base_pt"]
    doc = L.to_document(dec)
    assert [f.code for f in doc.findings] == [F.SOURCE_MAPPING_UNVERIFIED]


def test_paper_space_entities_are_retained_not_mixed_into_model_space():
    """R8.2: paper-space content is kept as observations (OTHER_LAYOUT), not merely counted."""
    dec = B.build({"entities": [{"kind": "LINE", "a": (0, 0), "b": (1, 0)}]})
    dec["OBJECTS"].append({"object": "BLOCK_HEADER", "type": 49, "handle": [0, 1, 800], "name": "*Paper_Space"})
    dec["OBJECTS"].append({"entity": "LINE", "type": 19, "handle": [0, 1, 801], "ownerhandle": [4, 1, 800, 800],
                           "start": [0, 0, 0], "end": [5, 0, 0]})
    doc = L.to_document(dec)
    assert len(doc.entities) == 1
    assert [(lay, o.source_handle) for lay, o in doc.other_layouts] == [("*Paper_Space", "801")]
    got = kernel.realise(doc).as_contract_dict()
    assert got["segments"] == [((0.0, 0.0), (1.0, 0.0))] and got["dispositions"]["OTHER_LAYOUT"] == 1


def test_unresolved_owner_is_quarantined_never_model_space():
    """R8.2 Phase 0 (replaces R8.1's non-blocking model-space fallback): an owner
    the source does not establish -> UNPLACED + blocking OWNER_UNRESOLVED."""
    dec = B.build({"entities": [{"kind": "LINE", "a": (0, 0), "b": (1, 0)}]})
    for o in dec["OBJECTS"]:
        if o.get("entity") == "LINE":
            o["ownerhandle"] = [4, 1, 12345, 12345]
    got = realise(dec)
    assert codes(got) == [F.OWNER_UNRESOLVED] and got["findings"][0]["blocks_final"] is True
    assert got["segments"] == [] and got["dispositions"] == {"UNPLACED": 1}
    assert got["unplaced"][0]["reason"] == "OWNER_HANDLE_UNKNOWN" and got["unplaced"][0]["raw_owner"] == [4, 1, 12345, 12345]


# ---------------------------------------------------------------- attributes

def test_attrib_rows_attach_to_their_insert():
    scene = {"blocks": {"CURVES": S.CURVES_BLOCK},
             "entities": [{"kind": "INSERT_WITH_ATTRIB", "block": "CURVES", "at": (0.0, 0.0),
                           "attrib_at": (5.0, 5.0), "tag": "NO", "value": "D01"}]}
    doc = L.to_document(B.build(scene))
    (ins,) = doc.entities
    assert [(a.tag, a.value) for a in ins.geometry.attributes] == [("NO", "D01")]


# ---------------------------------------------------------------- accounting

ALL = {c[1]: c for c in S.CURVE_CASES + S.BASE_POINT_CASES + S.MINSERT_CASES + S.XREF_CASES + S.SKIP_CASES}


@pytest.mark.parametrize("sid", sorted(ALL))
def test_every_entity_row_is_accounted_for(sid):
    dec = B.build(ALL[sid][3])
    doc = L.to_document(dec)
    rows = [o for o in dec["OBJECTS"] if "entity" in o]
    attached = sum(len(e.geometry.attributes) for e in doc.entities + tuple(x for b in doc.blocks.values()
                                                                           for x in b.entities)
                   if e.kind == O.INSERT)
    mapped = len(doc.entities) + sum(len(b.entities) for b in doc.blocks.values())
    retained = len(doc.unplaced) + len(doc.other_layouts)
    noted = sum(v for k, v in doc.notes.items() if k.startswith("delimiter_"))
    assert mapped + attached + retained + noted == len(rows)
