"""R8.0 source capability — XREF, skipped / proxy / custom objects, and the
entity classes the current engine does not realise.

RULE: a decoder that skips or cannot realise an object records it in the
SOURCE_CAPABILITY_REGISTER (per entity: handle, type, owner/instance path,
reason, blocks_final). Never: object skipped -> silently absent -> BOQ looks
complete.

Two levels are tested:
  * FLOOR (current engine): the object is at least COUNTED somewhere
    (unhandled / custom-class counters). Regression guard — passes today.
  * CONTRACT (R8): a per-entity register row with handle and blocks_final,
    and the affected region cannot release FINAL.
"""

from __future__ import annotations

import math

import pytest

from . import libredwg_builder as B, scenes as S, targets
from .geometry import close, current_realised

XREF = {c[1]: c for c in S.XREF_CASES}
SKIP = {c[1]: c for c in S.SKIP_CASES}


# ------------------------------------------------------------------- F08 XREF

@pytest.mark.parametrize("sid", list(XREF))
def test_xref_is_a_visible_finding_current_engine(sid):
    nd = current_realised(B.build(XREF[sid][3]))["normalized"]
    text = (repr(nd.notes) + repr(nd.unhandled)).upper()
    assert "XREF" in text, f"{sid}: xref placed as an empty instance with no finding"


@pytest.mark.parametrize("sid", list(XREF))
def test_xref_register_contract(sid):
    exp = XREF[sid][4]
    reg = targets.call("CAPABILITY_REGISTER", B.build(XREF[sid][3]))
    rows = [r for r in reg if r["code"] == exp["finding"]]
    assert len(rows) == 1
    r = rows[0]
    assert r["blocks_final"] is exp["blocks_final"]
    assert r["attachment"] == exp["attachment"]
    assert r["handle"] is not None and r["instance_path"]
    if exp.get("nested"):
        assert len(r["instance_path"]) == 2


# -------------------------------------------- F35 / F36 / F19 skipped objects

@pytest.mark.parametrize("sid", list(SKIP))
def test_skipped_object_is_counted_current_engine(sid):
    nd = current_realised(B.build(SKIP[sid][3]))["normalized"]
    code = SKIP[sid][4]
    counted = nd.unhandled.get(code, 0) + nd.notes["custom_class_entities_by_type_code"].get(code, 0)
    assert counted >= 1, f"{sid}: type {code} vanished without a count"


@pytest.mark.parametrize("sid", list(SKIP))
def test_skipped_object_register_contract(sid):
    reg = targets.call("CAPABILITY_REGISTER", B.build(SKIP[sid][3]))
    rows = [r for r in reg if r["type_code"] == int(SKIP[sid][4])]
    assert rows and all(r["handle"] is not None and r["reason"] for r in rows)
    assert all(r["blocks_final"] for r in rows)


def test_custom_entity_on_wall_layer_blocks_region_contract():
    """F19: an unrealised custom entity on a wall layer blocks the region's
    measured claims (it may be the wall)."""
    prof = targets.call("SOURCE_PROFILE", decode=B.build(SKIP["F19_CUSTOM_ON_WALL_LAYER"][3]), profile="CAD_PROFILE")
    assert prof["V-CAD-5"] == "FAIL" and prof["region_release"] == "BLOCKED"


def test_route_missing_a_declared_class_contract():
    """F20: a route that declares it realises LWPOLYLINE but returns fewer
    LWPOLYLINE observations than the census holds -> PRESENCE BLOCK."""
    decode = B.build({"entities": [{"kind": "LWPOLYLINE", "pts": [(0, 0), (1000, 0)], "bulges": [0, 0]},
                                   {"kind": "LWPOLYLINE", "pts": [(0, 500), (1000, 500)], "bulges": [0, 0]}]})
    r = targets.call("RECONCILE", route_a={"decode": decode, "declares": ["LWPOLYLINE"]},
                     route_b={"decode": decode, "declares": ["LWPOLYLINE"], "drop_first_of": "LWPOLYLINE"})
    assert r["verdict"] == "BLOCK" and r["field_class"] == "PRESENCE"


# ------------------------------------------------------- F07 ELLIPSE / SPLINE

ELLIPSE_SCENE = {"entities": [{"kind": "ELLIPSE", "c": (0.0, 0.0), "major": (1000.0, 0.0), "ratio": 0.5}]}


def test_ellipse_is_counted_current_engine():
    nd = current_realised(B.build(ELLIPSE_SCENE))["normalized"]
    assert nd.unhandled.get("35", 0) == 1


def test_ellipse_flattening_contract():
    """Flattened within a DECLARED chord tolerance; every flattened vertex on
    the analytic ellipse x^2/1000^2 + y^2/500^2 = 1."""
    got = targets.call("K1_REALISE", B.build(ELLIPSE_SCENE))
    fl = got["flattened"][0]
    assert fl["declared_chord_tolerance_mm"] > 0
    for x, y in fl["vertices"]:
        assert abs((x / 1000.0) ** 2 + (y / 500.0) ** 2 - 1.0) < 1e-9
    assert fl["max_chord_deviation_mm"] <= fl["declared_chord_tolerance_mm"]


# An ELLIPSE's centre and major axis are WCS, but its parameter sweep runs
# CCW about its normal. With normal (0,0,-1) the minor axis is
# ratio * (N x major) = 0.5 * ((0,0,-1) x (1000,0,0)) = (0,-500), so the
# quarter t = 0 -> pi/2 runs (1000,0) -> (707.107,-353.553) -> (0,-500): CW in plan.
# Al Rashed carries 6 ELLIPSEs with this normal (R8.0 exposure census).
ELLIPSE_NEG_Z = {"entities": [{"kind": "ELLIPSE", "c": (0.0, 0.0), "major": (1000.0, 0.0), "ratio": 0.5,
                               "t0": 0.0, "t1": math.pi / 2, "extrusion": (0.0, 0.0, -1.0)}]}
ELLIPSE_NEG_Z_TRUTH = {"START_POINT": (1000.0, 0.0),
                       "MID_SWEEP_POINT": (1000.0 * math.sqrt(0.5), -500.0 * math.sqrt(0.5)),
                       "END_POINT": (0.0, -500.0), "SWEEP_DIRECTION": "CW"}


def test_ellipse_negative_normal_is_counted_current_engine():
    nd = current_realised(B.build(ELLIPSE_NEG_Z))["normalized"]
    assert nd.unhandled.get("35", 0) == 1


def test_ellipse_negative_normal_sweep_contract():
    got = targets.call("K1_REALISE", B.build(ELLIPSE_NEG_Z))
    e = got["elliptical_arcs"][0]
    for k in ("START_POINT", "MID_SWEEP_POINT", "END_POINT"):
        assert close(ELLIPSE_NEG_Z_TRUTH[k], e[k]), k
    assert e["SWEEP_DIRECTION"] == "CW"


# ----------------------------------------------------- F09 dynamic blocks

def test_dynamic_block_visibility_contract():
    """A dynamic block (anonymous *U instance of a parent with visibility
    states) whose state is not resolved yields no identity claim from its name."""
    scene = {"blocks": {"*U3": {"entities": [{"kind": "LINE", "a": (0, 0), "b": (900, 0)}]}},
             "entities": [{"kind": "INSERT", "block": "*U3", "at": (0.0, 0.0), "scale": (1.0, 1.0), "rot": 0.0}]}
    reg = targets.call("CAPABILITY_REGISTER", B.build(scene))
    row = next(r for r in reg if r["code"] == "DYNAMIC_BLOCK_UNRESOLVED")
    assert row["visibility_resolved"] is False and row["identity_claim_allowed"] is False


# ------------------------------------------------- F10 rotated linear dimension

F10_SCENE = {"entities": [{"kind": "DIMENSION_LINEAR", "x1": S.F10_ORIGINS[0], "x2": S.F10_ORIGINS[1],
                           "def": (3000.0, 1000.0), "rot": 0.0, "act": S.F10_PROJECTED_MM}]}


def test_rotated_linear_dimension_geometry_current_engine():
    """A linear dimension measures the PROJECTION of its origins on the
    dimension direction (3000 here), not their distance (3026.5)."""
    nd = current_realised(B.build(F10_SCENE))["normalized"]
    d = nd.dimensions[0]
    assert abs(d.geometry_mm - S.F10_PROJECTED_MM) <= 0.5, (
        f"geometry {d.geometry_mm:.3f} is the origin distance, not the projection")


def test_rotated_linear_dimension_contract():
    m = targets.call("DIMENSION_MEASURE", B.build(F10_SCENE))[0]
    assert abs(m["projected_measured_mm"] - S.F10_PROJECTED_MM) <= 0.5
    assert m["agrees_with_act_measurement"] is True


# ------------------------------------------------------------ F11 MTEXT codes

F11_SCENE = {"entities": [{"kind": "MTEXT", "at": (0.0, 0.0), "text": S.F11_RAW}]}


def test_mtext_literal_current_engine():
    nd = current_realised(B.build(F11_SCENE))["normalized"]
    assert nd.texts[0].value == S.F11_LITERAL, f"raw MTEXT codes kept: {nd.texts[0].value!r}"


def test_mtext_literal_cad_text_contract():
    assert targets.call("CAD_TEXT_PLAIN", S.F11_RAW) == S.F11_LITERAL


# ---------------------------------------------------------- F12 ATTRIB binding

F12_SCENE = {"blocks": {"DOOR": {"entities": [{"kind": "LINE", "a": (0, 0), "b": (0, 900)}]}},
             "entities": [{"kind": "INSERT_WITH_ATTRIB", "block": "DOOR", "at": (5000.0, 0.0),
                           "tag": "DOOR_TYPE", "value": "D03", "attrib_at": (5100.0, 450.0)}]}


def test_attrib_value_not_lost_current_engine():
    nd = current_realised(B.build(F12_SCENE))["normalized"]
    assert any(t.value == "D03" for t in nd.texts)


def test_attrib_bound_to_its_insert_contract():
    reg = targets.call("K1_REALISE", B.build(F12_SCENE))
    at = next(a for a in reg["attributes"] if a["tag"] == "DOOR_TYPE")
    assert at["value"] == "D03" and at["owner_insert_handle"] is not None


# --------------------------------------------------------- F14 legacy codepage

def test_legacy_codepage_text_contract():
    """Undecodable bytes -> TEXT_UNDECODABLE, never an identity source."""
    decode = B.build({"entities": [{"kind": "TEXT", "at": (0, 0), "text": "\udcc7\udce4"}]})
    reg = targets.call("CAPABILITY_REGISTER", decode)
    row = next(r for r in reg if r["code"] in ("TEXT_NORMALISED", "TEXT_UNDECODABLE"))
    assert row["code"] == "TEXT_UNDECODABLE" and row["identity_source_allowed"] is False
