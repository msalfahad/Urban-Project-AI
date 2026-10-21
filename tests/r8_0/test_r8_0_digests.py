"""R8.0 digest contracts — CASE A..D (R8.0 brief §14, §15).

The reference definition lives in digest_contract.py (test side). The golden
vectors in registers/R8_0_DIGEST_VECTORS.json freeze it; the production
engine/source/digests module must reproduce them bit for bit
(TARGET_NOT_IMPLEMENTED today).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from . import digest_contract as D, libredwg_builder as B, reference_realiser as RR, scenes as S, targets
from .geometry import current_realised

VECTORS = Path(__file__).parent / "registers" / "R8_0_DIGEST_VECTORS.json"
Q = S.BULGE_Q
MIRRORED = next(c for c in S.CURVE_CASES if c[1] == "F02_MIRROR_X")[3]
# the SAME physical geometry as MIRRORED, drawn directly in WCS
DIRECT_WCS = {"entities": [
    {"kind": "ARC", "c": (-1000.0, 0.0), "r": 500.0, "a0": 90.0, "a1": 180.0},
    {"kind": "LWPOLYLINE", "pts": [(-1500.0, 0.0), (-1000.0, 500.0)], "bulges": [-Q, 0.0]},
    {"kind": "LINE", "a": (0.0, 0.0), "b": (-2000.0, 0.0)},
]}
SQUARE_POLY = {"entities": [{"kind": "LWPOLYLINE", "pts": [(0, 0), (3000, 0), (3000, 3000), (0, 3000)],
                             "bulges": [0, 0, 0, 0], "closed": True}]}
SQUARE_LINES = {"entities": [{"kind": "LINE", "a": a, "b": b} for a, b in
                             (((0, 0), (3000, 0)), ((3000, 0), (3000, 3000)), ((3000, 3000), (0, 3000)), ((0, 3000), (0, 0)))]}
ARC_ENTITY = {"entities": [{"kind": "ARC", "c": (1000.0, 0.0), "r": 500.0, "a0": 0.0, "a1": 90.0}]}
BULGE_FWD = {"entities": [{"kind": "LWPOLYLINE", "pts": [(1500.0, 0.0), (1000.0, 500.0)], "bulges": [Q, 0.0]}]}
BULGE_REV = {"entities": [{"kind": "LWPOLYLINE", "pts": [(1000.0, 500.0), (1500.0, 0.0)], "bulges": [-Q, 0.0]}]}
BULGE_OTHER_SIDE = {"entities": [{"kind": "LWPOLYLINE", "pts": [(1500.0, 0.0), (1000.0, 500.0)], "bulges": [-Q, 0.0]}]}

SCENES = {"MIRRORED": MIRRORED, "DIRECT_WCS": DIRECT_WCS, "SQUARE_POLY": SQUARE_POLY,
          "SQUARE_LINES": SQUARE_LINES, "ARC_ENTITY": ARC_ENTITY, "BULGE_FWD": BULGE_FWD,
          "BULGE_REV": BULGE_REV, "BULGE_OTHER_SIDE": BULGE_OTHER_SIDE}


def srd(scene):
    return D.source_representation_digest(B.build(scene), "D1_LIBREDWG_JSON")


def rgd(scene, mutations=()):
    return D.realised_geometry_digest(D.as_realised(RR.realise(scene, mutations)), unit_to_mm=1.0)


# ---------------------------------------------------------------- CASE A

@pytest.mark.parametrize("pair", [("MIRRORED", "DIRECT_WCS"), ("SQUARE_POLY", "SQUARE_LINES")], ids=lambda p: "_vs_".join(p))
def test_case_A_different_representation_same_geometry(pair):
    a, b = (SCENES[k] for k in pair)
    assert srd(a) != srd(b), "representations differ, so SOURCE_REPRESENTATION_DIGEST must differ"
    assert rgd(a) == rgd(b), "physical geometry is identical, so REALISED_GEOMETRY_DIGEST must match"


def test_case_A_current_engine_realised_digest():
    """Through TODAY's cad_adapter, the mirrored block and the same geometry
    drawn directly do NOT realise to the same physical geometry (the
    mirrored-curve defect, seen through the digest)."""
    def cur(scene):
        r = current_realised(B.build(scene))
        return D.realised_geometry_digest({k: r[k] for k in ("arcs", "bulges", "segments")}, unit_to_mm=1.0)
    assert cur(MIRRORED) == cur(DIRECT_WCS)


# ---------------------------------------------------------------- CASE B

def test_case_B_same_source_broken_kernel():
    """Same decode; a deliberately broken kernel (mirror applied as a
    rotation — MT-02 / MT-50). The source digest cannot see it; the realised
    digest must."""
    assert srd(MIRRORED) == srd(MIRRORED)
    assert rgd(MIRRORED) != rgd(MIRRORED, {"MIRROR_AS_ROTATION"})
    assert rgd(MIRRORED) != rgd(MIRRORED, {"BULGE_FLIP_ONLY_ON_EXTRUSION"})


# ---------------------------------------------------------------- CASE C

@pytest.mark.parametrize("pair", [("ARC_ENTITY", "BULGE_FWD"), ("BULGE_FWD", "BULGE_REV"), ("ARC_ENTITY", "BULGE_REV")],
                         ids=lambda p: "_vs_".join(p))
def test_case_C_equivalent_curve_representations(pair):
    a, b = (SCENES[k] for k in pair)
    assert rgd(a) == rgd(b)


# ---------------------------------------------------------------- CASE D

def test_case_D_different_physical_orientation():
    """Same end points, the arc on the OTHER side of its chord: a different
    physical curve -> a different realised digest."""
    assert rgd(BULGE_FWD) != rgd(BULGE_OTHER_SIDE)


# ------------------------------------------------------- contract rules

def test_realised_digest_requires_a_unit():
    with pytest.raises(ValueError):
        D.realised_geometry_digest(D.as_realised(RR.realise(ARC_ENTITY)), unit_to_mm=None)


def test_realised_digest_accounts_for_units():
    r = D.as_realised(RR.realise(ARC_ENTITY))
    assert D.realised_geometry_digest(r, unit_to_mm=1.0) != D.realised_geometry_digest(r, unit_to_mm=25.4)


def test_negative_zero_is_canonical():
    assert D.q(-0.0, D.REALISED_QUANTUM) == D.q(0.0, D.REALISED_QUANTUM) == "0.000000"


def test_float_noise_below_quantum_is_absorbed():
    x = 1353.5533905932737
    assert D.q(x, D.REALISED_QUANTUM) == D.q(x + 3e-11, D.REALISED_QUANTUM)


def test_non_finite_source_values_are_marked_not_rounded():
    assert D._canon_source(float("nan")).startswith("NONFINITE")


def test_quanta_are_frozen():
    assert D.REALISED_QUANTUM == D.Decimal("0.000001") and D.SOURCE_QUANTUM == D.Decimal("0.000000001")


# ------------------------------------------------------- golden vectors

def _vectors():
    return json.loads(VECTORS.read_text())


def test_golden_vectors_reproduce_reference_contract():
    v = _vectors()
    for name, row in v["vectors"].items():
        assert srd(SCENES[name]) == row["SOURCE_REPRESENTATION_DIGEST"], name
        assert rgd(SCENES[name]) == row["REALISED_GEOMETRY_DIGEST"], name


def test_golden_vectors_production_conformance():
    """engine/source/digests must reproduce the frozen vectors exactly."""
    srd_fn = targets.resolve("SOURCE_REPRESENTATION_DIGEST")
    rgd_fn = targets.resolve("REALISED_GEOMETRY_DIGEST")
    for name, row in _vectors()["vectors"].items():
        dec = B.build(SCENES[name])
        assert srd_fn(dec, "D1_LIBREDWG_JSON") == row["SOURCE_REPRESENTATION_DIGEST"]
        assert rgd_fn(targets.call("K1_REALISE", dec), unit_to_mm=1.0) == row["REALISED_GEOMETRY_DIGEST"]
