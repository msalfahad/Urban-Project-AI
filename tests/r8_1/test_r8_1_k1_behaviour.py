"""R8.1 — K1 behaviour beyond the R8.0 acceptance contract.

Literal mirror values, visible findings (xref / missing block / nesting /
skipped / proxy / custom), one disposition per visit, exact elliptical
arcs under non-uniform scale, invisibility, carried kinds, unit
independence, and the frozen R8.0 truth left untouched.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import pytest

from engine.source import findings as F
from engine.source import observations as O
from engine.source.cad import kernel, libredwg_map
from tests.r8_0 import libredwg_builder as B, scenes as S

from .helpers import BP, CURVE, MI, k1

ROOT = Path(__file__).resolve().parents[2]
H = 500.0 * math.sqrt(0.5)
EPS = 1e-9


def close(p, q, eps=EPS):
    return abs(p[0] - q[0]) <= eps and abs(p[1] - q[1]) <= eps


def codes(got):
    return [f["code"] for f in got["findings"]]


# ---------------------------------------------------------------- mirror, literally

def test_x_mirror_arc_literal_values():
    """The brief's worked example, written as literals (not via the scene map)."""
    got = k1(CURVE["F02_MIRROR_X"][3])
    (arc,), (bulge,) = got["arcs"], got["bulges"]
    assert close(arc["CENTER"], (-1000.0, 0.0))
    assert close(arc["P0"], (-1500.0, 0.0))
    assert close(arc["PM"], (-1353.5533905932738, 353.5533905932738))
    assert close(arc["P1"], (-1000.0, 500.0))
    assert arc["DIR"] == "CW" and abs(arc["RADIUS"] - 500.0) < EPS


def test_x_mirror_bulge_literal_values():
    (bulge,) = k1(CURVE["F02_MIRROR_X"][3])["bulges"]
    assert close(bulge["VERTEX_A"], (-1500.0, 0.0)) and close(bulge["VERTEX_B"], (-1000.0, 500.0))
    assert close(bulge["ARC_MIDPOINT"], (-1000.0 - H, H))
    assert close(bulge["CENTER"], (-1000.0, 0.0))
    assert bulge["DIR_A_TO_B"] == "CW"


@pytest.mark.parametrize("sid", sorted(CURVE) + sorted(BP))
def test_unmutated_k1_raises_no_orientation_or_frame_finding(sid):
    got = k1((CURVE.get(sid) or BP[sid])[3])
    assert got["findings"] == []
    assert sum(got["dispositions"].values()) > 0 and set(got["dispositions"]) <= {"REALISED"}


# ---------------------------------------------------------------- xref

XREF = {c[1]: c for c in S.XREF_CASES}


@pytest.mark.parametrize("sid", sorted(XREF))
def test_xref_is_a_visible_finding_never_zero_geometry(sid):
    exp = XREF[sid][4]
    got = k1(XREF[sid][3])
    xf = [f for f in got["findings"] if f["code"].startswith("XREF_")]
    assert [f["code"] for f in xf] == [exp["finding"]]
    assert xf[0]["blocks_final"] is True
    assert f"attachment={exp['attachment']}" in xf[0]["detail"]
    assert "zero children is not evidence of no geometry" in xf[0]["detail"]
    assert len(xf[0]["instance_path"]) == (2 if exp.get("nested") else 1)
    assert got["dispositions"].get("FINDING", 0) >= 1


@pytest.mark.parametrize("sid", sorted(XREF))
def test_xref_through_production_mapper_alone_fails_closed_to_not_resolved(sid):
    """Without the test-schema extension, D1 does not know what the resolved /
    unloaded flags mean in real decodes — so every xref is XREF_NOT_RESOLVED."""
    doc = libredwg_map.to_document(B.build(XREF[sid][3]))
    got = kernel.realise(doc).as_contract_dict()
    assert [c for c in codes(got) if c.startswith("XREF_")] == [F.XREF_NOT_RESOLVED]
    xr = [b for b in doc.blocks.values() if b.xref is not None]
    assert len(xr) == 1 and xr[0].xref.mapping_status == F.SOURCE_MAPPING_UNVERIFIED
    assert xr[0].xref.resolved is None and xr[0].xref.unloaded is None


def test_xref_with_local_entities_still_realises_them_but_stays_flagged():
    line = O.SourceEntityObservation("t:1", "1", "T", O.LINE, O.LineGeom((0.0, 0.0), (10.0, 0.0)))
    ins = O.SourceEntityObservation("t:2", "2", "T", O.INSERT, O.InsertGeom("X", (100.0, 0.0), (1.0, 1.0), 0.0))
    xr = O.XrefInfo("a.dwg", "ATTACH", False, False, "TEST")
    doc = O.SourceDocument(O.SourceRevisionAnchor(None, "T", "T", None), (ins,),
                           {"X": O.BlockDefinition("X", "X", (0.0, 0.0), (line,), xr)})
    got = kernel.realise(doc).as_contract_dict()
    assert codes(got) == [F.XREF_NOT_RESOLVED]
    assert got["segments"] == [((100.0, 0.0), (110.0, 0.0))]


# ---------------------------------------------------------------- block structure

def _doc(entities, blocks=None):
    return O.SourceDocument(O.SourceRevisionAnchor(None, "T", "T", None), tuple(entities), blocks or {})


def _ins(obs_id, key, at=(0.0, 0.0)):
    return O.SourceEntityObservation(obs_id, obs_id, "T", O.INSERT, O.InsertGeom(key, at, (1.0, 1.0), 0.0))


def test_missing_block_definition_is_a_finding():
    got = kernel.realise(_doc([_ins("t:1", "NOPE")])).as_contract_dict()
    assert codes(got) == [F.MISSING_BLOCK_DEFINITION] and got["dispositions"] == {"FINDING": 1}


def test_self_referencing_block_stops_at_nesting_limit():
    blk = O.BlockDefinition("LOOP", "LOOP", (0.0, 0.0), (_ins("t:inner", "LOOP"),))
    got = kernel.realise(_doc([_ins("t:outer", "LOOP")], {"LOOP": blk})).as_contract_dict()
    assert codes(got) == [F.NESTING_LIMIT]
    (f,) = got["findings"]
    assert len(f["instance_path"]) == kernel.MAX_NESTING_DEPTH + 1


def test_nameless_block_is_flagged_but_still_placed_through_its_insert():
    line = O.SourceEntityObservation("t:1", "1", "T", O.LINE, O.LineGeom((0.0, 0.0), (10.0, 0.0)))
    blk = O.BlockDefinition("H9", "", (0.0, 0.0), (line,), name_readable=False)
    got = kernel.realise(_doc([_ins("t:2", "H9", (5.0, 5.0))], {"H9": blk})).as_contract_dict()
    assert codes(got) == [F.BLOCK_NAME_UNREADABLE]
    assert got["segments"] == [((5.0, 5.0), (15.0, 5.0))]


SKIP = {c[1]: c for c in S.SKIP_CASES}


@pytest.mark.parametrize("sid,code", [("F35_OLE2FRAME_IN_BLOCK", F.SKIPPED), ("F36_PROXY_ENTITY", F.PROXY),
                                      ("F19_CUSTOM_ON_WALL_LAYER", F.CUSTOM_CLASS)])
def test_unrealised_entities_are_visible_findings(sid, code):
    got = k1(SKIP[sid][3])
    assert code in codes(got)
    f = next(f for f in got["findings"] if f["code"] == code)
    assert f["blocks_final"] and f["obs_id"]
    assert got["dispositions"]["FINDING"] == 1


def test_ole2frame_in_block_does_not_hide_its_sibling_line():
    got = k1(SKIP["F35_OLE2FRAME_IN_BLOCK"][3])
    assert got["segments"] == [((0.0, 0.0), (100.0, 0.0))]
    (f,) = [f for f in got["findings"] if f["code"] == F.SKIPPED]
    assert len(f["instance_path"]) == 1                     # inside the placed instance


def test_custom_class_on_wall_layer_keeps_its_layer_in_the_record():
    got = k1(SKIP["F19_CUSTOM_ON_WALL_LAYER"][3])
    assert got["segments"] == [((0.0, 0.0), (3000.0, 0.0))]
    assert "AEC_WALL" in next(f for f in got["findings"] if f["code"] == F.CUSTOM_CLASS)["detail"]


# ---------------------------------------------------------------- dispositions

def _expected_visits(doc, obs, depth=0):
    """Independent recount: one visit per observation per instance reached."""
    if obs.kind != O.INSERT or not obs.visible:
        return 1
    blk = doc.blocks.get(obs.geometry.block_key)
    if blk is None or depth >= kernel.MAX_NESTING_DEPTH:
        return 1
    cells = 1 if obs.geometry.grid is None else obs.geometry.grid.columns * obs.geometry.grid.rows
    return 1 + cells * sum(_expected_visits(doc, c, depth + 1) for c in blk.entities)


ALL_SCENES = ({**CURVE, **BP, **MI, **XREF, **SKIP}).items()


@pytest.mark.parametrize("sid,case", sorted(ALL_SCENES), ids=[s for s, _ in sorted(ALL_SCENES)])
def test_every_visit_gets_exactly_one_disposition(sid, case):
    from tests.r8_0.k1_harness import apply_test_schema_extensions
    dec = B.build(case[3])
    doc = apply_test_schema_extensions(dec, libredwg_map.to_document(dec))
    rg = kernel.realise(doc)
    assert sum(rg.dispositions.values()) == rg.visits
    assert rg.visits == sum(_expected_visits(doc, o) for o in doc.entities)


# ---------------------------------------------------------------- MINSERT via D1 only

@pytest.mark.parametrize("sid", sorted(MI))
def test_minsert_through_production_mapper_alone_is_unverified_never_one_instance(sid):
    got = kernel.realise(libredwg_map.to_document(B.build(MI[sid][3]))).as_contract_dict()
    assert F.SOURCE_MAPPING_UNVERIFIED in codes(got)
    assert got["segments"] == []                             # not a single instance for a grid


# ---------------------------------------------------------------- non-uniform scale

def test_non_uniform_arc_is_an_exact_elliptical_arc_with_a_notice():
    got = k1(S.F04_SCENE)
    assert got["arcs"] == [] and got["bulges"] == [] and got["circles"] == []
    assert len(got["elliptical_arcs"]) == 2
    for e in got["elliptical_arcs"]:
        C, u, v = e["CENTER"], e["AXIS_U"], e["AXIS_V"]
        assert close(C, (2000.0, 0.0))
        for k, want in S.F04_TRUTH_POINTS.items():
            assert close(e[k], want), (e["source"], k)
            # the point lies EXACTLY on the ellipse ((x-2000)/1000)^2 + (y/500)^2 = 1
            assert abs(((e[k][0] - 2000.0) / 1000.0) ** 2 + (e[k][1] / 500.0) ** 2 - 1.0) < 1e-12
        # conjugate semi-diameters of that ellipse
        assert abs(abs(u[0] * v[1] - u[1] * v[0]) - 1000.0 * 500.0) < 1e-6
        assert e["SWEEP_DIRECTION"] == "CCW"
    notes = [f for f in got["findings"] if f["code"] == F.NON_UNIFORM_SCALE_CURVE]
    assert len(notes) == 2 and not any(f["blocks_final"] for f in notes)
    assert codes(got) == [F.NON_UNIFORM_SCALE_CURVE] * 2


def test_non_uniform_mirror_reverses_elliptical_sweep():
    scene = {"blocks": {"CURVES": S.CURVES_BLOCK}, "entities": [S._insert("CURVES", scale=(-2.0, 1.0))]}
    got = k1(scene)
    assert {e["SWEEP_DIRECTION"] for e in got["elliptical_arcs"]} == {"CW"}
    for e in got["elliptical_arcs"]:
        assert close(e["START_POINT"], (-3000.0, 0.0)) and close(e["END_POINT"], (-2000.0, 500.0))
        assert close(e["MID_SWEEP_POINT"], (-2000.0 - 2 * H, H))


def test_non_uniform_circle_is_a_full_ellipse_not_a_circle():
    scene = {"blocks": {"C": {"base": (0.0, 0.0), "entities": [{"kind": "CIRCLE", "c": (0.0, 0.0), "r": 100.0}]}},
             "entities": [S._insert("C", scale=(3.0, 1.0))]}
    got = k1(scene)
    assert got["circles"] == [] and len(got["elliptical_arcs"]) == 1 and got["elliptical_arcs"][0]["FULL"]


# ---------------------------------------------------------------- hidden / carried

def test_invisible_entity_is_hidden_not_realised_not_dropped():
    dec = B.build({"entities": [{"kind": "LINE", "a": (0, 0), "b": (10, 0)}, {"kind": "LINE", "a": (0, 5), "b": (10, 5)}]})
    for o in dec["OBJECTS"]:
        if o.get("entity") == "LINE" and o["start"][1] == 5.0:
            o["invisible"] = 1
    got = k1_from_decode(dec)
    assert got["segments"] == [((0.0, 0.0), (10.0, 0.0))]
    assert len(got["hidden"]) == 1 and got["dispositions"] == {"REALISED": 1, "HIDDEN": 1}


def test_children_of_an_invisible_insert_are_not_realised():
    dec = B.build({"blocks": {"CURVES": S.CURVES_BLOCK}, "entities": [S._insert("CURVES")]})
    for o in dec["OBJECTS"]:
        if o.get("entity") == "INSERT":
            o["invisible"] = 1
    got = k1_from_decode(dec)
    assert got["segments"] == [] and got["arcs"] == [] and got["dispositions"] == {"HIDDEN": 1}


def k1_from_decode(dec):
    from tests.r8_0.k1_harness import realise_decode
    return realise_decode(dec)


def test_text_and_dimension_are_carried_not_realised():
    scene = {"entities": [{"kind": "TEXT", "at": (0, 0), "text": "D01"},
                          {"kind": "MTEXT", "at": (0, 0), "text": "R-01"},
                          {"kind": "DIMENSION_LINEAR", "x1": (0, 0), "x2": (3000, 400), "act": 3000.0}]}
    got = k1(scene)
    assert sorted(c["kind"] for c in got["carried"]) == ["DIMENSION", "MTEXT", "TEXT"]
    assert got["segments"] == [] and got["findings"] == []


def test_attribute_is_placed_through_its_insert_parent_not_the_block():
    scene = {"blocks": {"CURVES": S.CURVES_BLOCK},
             "entities": [{"kind": "INSERT_WITH_ATTRIB", "block": "CURVES", "at": (1000.0, 0.0), "scale": (-1.0, 1.0),
                           "attrib_at": (1200.0, 50.0), "tag": "NO", "value": "D01"}]}
    got = k1(scene)
    (att,) = got["attributes"]
    assert att["tag"] == "NO" and att["value"] == "D01" and close(att["insertion"], (1200.0, 50.0))


# ---------------------------------------------------------------- units

@pytest.mark.parametrize("sid", ["F02_MIRROR_X", "F05_NESTED_BLOCK_MIRROR"])
def test_k1_output_is_independent_of_the_header_unit_code(sid):
    """K1 never infers or applies units: INSUNITS is carried, not used."""
    a = k1(dict(CURVE[sid][3], insunits=4))
    b = k1(dict(CURVE[sid][3], insunits=1))
    assert a == b


# ---------------------------------------------------------------- frozen files

FROZEN = {
    "engine/cad_adapter.py": "4d060a1d0f9c5a6ed19c6f8b7b508fa7a5762aa4dc74684bc3b1ec9cd0a573a3",
    "tests/r8_0/scenes.py": "d1277a1f35e8ace3058f72b0decda8512967d83337656a851b009511e7e84bcd",
    "tests/r8_0/geometry.py": "2d758d9eedd71d29da652b85ea1cf5566703edbb62345d09f30ede3976d8a458",
    "tests/r8_0/digest_contract.py": "058ec853f2568a526cce860996b250290b81ce030a6ce2d8ff8af695d9f79cf7",
    "tests/r8_0/registers/R8_0_DIGEST_VECTORS.json": "09dd0471624e15d6e00f84c53691f9a9c7d2761be7ed575ea5210f65660a59ba",
}


@pytest.mark.parametrize("rel", sorted(FROZEN))
def test_frozen_truth_and_cad_adapter_unchanged_by_r8_1(rel):
    assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == FROZEN[rel]
