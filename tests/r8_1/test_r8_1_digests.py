"""R8.1 — production URBAN-SRD-1 / URBAN-RGD-1 against the frozen R8.0 contract.

A digest is an identity / change detector, not reconciliation: the last
test shows two correct realisations that differ by sub-quantum float noise
straddling a rounding boundary and therefore hash differently.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from engine.source import digests as PD
from engine.source.cad import kernel, libredwg_map as L
from tests.r8_0 import digest_contract as D, libredwg_builder as B
from tests.r8_0.test_r8_0_digests import SCENES

VECTORS = json.loads((Path(__file__).resolve().parents[1] / "r8_0" / "registers" / "R8_0_DIGEST_VECTORS.json").read_text())


def realised(scene):
    return kernel.realise(L.to_document(B.build(scene)))


@pytest.mark.parametrize("name", sorted(VECTORS["vectors"]))
def test_production_srd_reproduces_golden_vector(name):
    assert L.source_representation_digest(B.build(SCENES[name])) == VECTORS["vectors"][name]["SOURCE_REPRESENTATION_DIGEST"]


@pytest.mark.parametrize("name", sorted(VECTORS["vectors"]))
@pytest.mark.parametrize("form", ["RealisedGeometry", "contract_dict"])
def test_production_rgd_reproduces_golden_vector_from_real_k1(name, form):
    rg = realised(SCENES[name])
    arg = rg if form == "RealisedGeometry" else rg.as_contract_dict()
    assert PD.realised_geometry_digest(arg, 1.0) == VECTORS["vectors"][name]["REALISED_GEOMETRY_DIGEST"]


def test_srd_field_list_and_quanta_are_the_frozen_contract():
    assert L.SRD_FIELDS == D.SOURCE_FIELDS
    assert PD.REALISED_QUANTUM == D.REALISED_QUANTUM and PD.SOURCE_QUANTUM == D.SOURCE_QUANTUM
    assert (PD.SRD_PREFIX, PD.RGD_PREFIX) == (D.SRD_PREFIX, D.RGD_PREFIX)


def test_case_A_on_real_k1_mirror_equals_direct_wcs():
    a, b = realised(SCENES["MIRRORED"]), realised(SCENES["DIRECT_WCS"])
    assert PD.realised_geometry_digest(a, 1.0) == PD.realised_geometry_digest(b, 1.0)
    assert L.source_representation_digest(B.build(SCENES["MIRRORED"])) != \
        L.source_representation_digest(B.build(SCENES["DIRECT_WCS"]))


def test_case_D_other_side_of_chord_differs_on_real_k1():
    assert PD.realised_geometry_digest(realised(SCENES["BULGE_FWD"]), 1.0) != \
        PD.realised_geometry_digest(realised(SCENES["BULGE_OTHER_SIDE"]), 1.0)


def test_realised_digest_requires_a_unit():
    rg = realised(SCENES["ARC_ENTITY"])
    for bad in (None, 0, -1.0):
        with pytest.raises(ValueError):
            PD.realised_geometry_digest(rg, bad)


def test_realised_digest_is_in_millimetres():
    rg = realised(SCENES["SQUARE_LINES"])
    assert PD.realised_geometry_digest(rg, 1.0) != PD.realised_geometry_digest(rg, 1000.0)


@pytest.mark.parametrize("theta", [0.0, 0.3, 1.1, 2.0])
def test_elliptical_record_uses_principal_axes_not_the_parameterisation(theta):
    """C + cos t u + sin t v and the same ellipse with rotated conjugates must agree."""
    u, v = (1000.0, 0.0), (0.0, 500.0)
    c, s = math.cos(theta), math.sin(theta)
    u2 = (c * u[0] + s * v[0], c * u[1] + s * v[1])
    v2 = (-s * u[0] + c * v[0], -s * u[1] + c * v[1])
    (m1, n1), (m2, n2) = PD.principal_axes(u, v), PD.principal_axes(u2, v2)
    assert all(abs(a - b) < 1e-9 for a, b in zip(m1, m2)) and abs(n1 - n2) < 1e-9
    assert abs(math.hypot(*m1) - 1000.0) < 1e-9 and abs(n1 - 500.0) < 1e-9


def test_new_kinds_do_not_change_r8_0_vectors_and_are_hashed():
    from tests.r8_0 import scenes as S
    rg = kernel.realise(L.to_document(B.build(S.F04_SCENE)))
    recs = PD.realised_records(rg, 1.0)
    assert sorted({r["k"] for r in recs}) == ["ELLIPTICAL_ARC", "SEGMENT"]


def test_digest_is_not_reconciliation():
    """Two geometrically-equal results (difference 2e-10 mm, far below any
    drafting tolerance) that straddle a 1e-6 mm rounding boundary hash
    differently. Equality of physical geometry is decided by R8.2
    tolerance-aware reconciliation, never by comparing these digests."""
    a = {"segments": [((0.0, 0.0), (1000.0000005 - 1e-10, 0.0))]}
    b = {"segments": [((0.0, 0.0), (1000.0000005 + 1e-10, 0.0))]}
    assert PD.realised_geometry_digest(a, 1.0) != PD.realised_geometry_digest(b, 1.0)
