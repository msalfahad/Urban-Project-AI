"""R8.1 — the Urban OCS (clean Arbitrary Axis Algorithm), fail-closed and independent of ezdxf.

ezdxf.math.OCS is used HERE ONLY as a comparison oracle; production never imports it.
"""

from __future__ import annotations

import ast
import math
from pathlib import Path

import pytest
from ezdxf.math import OCS, Vec3

from engine.source.cad import kernel_ocs as K
from engine.source.findings import FRAME_UNREADABLE, UNSUPPORTED_FRAME

ROOT = Path(__file__).resolve().parents[2]
NORMALS = [(0, 0, 1), (0, 0, -1), (0, 0.6, 0.8), (1, 1, 1), (0.01, 0, 1), (0.02, 0, 1), (0, -0.015, -1),
           (-0.3, 0.2, 0.93), (1, 0, 0), (0, 1, 0), (0, 0, 5)]


@pytest.mark.parametrize("n", NORMALS, ids=str)
def test_arbitrary_axes_match_the_dxf_algorithm_via_independent_oracle(n):
    ax, ay, nz = K.arbitrary_axes(n)
    o = OCS(Vec3(n))
    for mine, ref in ((ax, o.ux), (ay, o.uy), (nz, o.uz)):
        assert all(abs(mine[i] - ref[i]) < 1e-12 for i in range(3)), (n, mine, ref)


@pytest.mark.parametrize("n", NORMALS, ids=str)
def test_axes_are_orthonormal_and_right_handed(n):
    ax, ay, nz = K.arbitrary_axes(n)
    dot = lambda u, v: sum(a * b for a, b in zip(u, v))
    for u in (ax, ay, nz):
        assert abs(dot(u, u) - 1) < 1e-12
    assert abs(dot(ax, ay)) < 1e-12 and abs(dot(ax, nz)) < 1e-12 and abs(dot(ay, nz)) < 1e-12
    assert abs(dot(K._cross(ax, ay), nz) - 1) < 1e-12


def test_plus_z_is_identity_and_minus_z_mirrors_x():
    assert K.plan_frame([0.0, 0.0, 1.0]).linear == (1.0, 0.0, 0.0, 1.0)
    assert K.plan_frame([0.0, 0.0, 5.0]).linear == (1.0, 0.0, 0.0, 1.0)
    pf = K.plan_frame([0.0, 0.0, -1.0])
    assert pf.linear == (-1.0, 0.0, 0.0, 1.0) and pf.normal_z_sign == -1


@pytest.mark.parametrize("n", [(0, 0.6, 0.8), (1, 1, 1), (0.01, 0, 1), (1e-9, 0, 1)], ids=str)
def test_tilted_frame_is_unsupported_not_projected(n):
    with pytest.raises(K.SourceFrameError) as err:
        K.plan_frame(n)
    assert err.value.code == UNSUPPORTED_FRAME


@pytest.mark.parametrize("bad", [None, "NULL", [0, 0, 0], [0.0, 1.0], [0, 0, 1, 0], ["z", 0, 1],
                                 [float("nan"), 0, 1], [0, 0, float("inf")], [True, 0, 1], (), 7,
                                 "FLAG_BIT_1_SET_BUT_EXTRUSION_ABSENT"], ids=repr)
def test_unreadable_frame_is_never_identity(bad):
    with pytest.raises(K.SourceFrameError) as err:
        K.plan_frame(bad)
    assert err.value.code == FRAME_UNREADABLE and FRAME_UNREADABLE in str(err.value)


def _imports(path):
    tree = ast.parse(path.read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


K2_ROUTE = "kernel_ezdxf.py"      # R8.2: the ezdxf route itself (K2) is the one module allowed to import ezdxf


def test_k1_is_independent_of_ezdxf():
    """R8.1 OCS decision (Option A): no K1 module imports ezdxf, so K1 and the
    ezdxf-based K2 (R8.2, engine/source/cad/kernel_ezdxf.py) cannot share an OCS failure."""
    for p in sorted((ROOT / "engine" / "source").rglob("*.py")):
        if p.name == K2_ROUTE:
            continue
        assert not any(n == "ezdxf" or n.startswith("ezdxf.") for n in _imports(p)), p


def test_no_blanket_exception_fallback_in_ocs_or_kernel():
    """The U-C4N fail-open pattern `except Exception: return <identity>` must not exist."""
    for name in ("kernel_ocs.py", "kernel.py"):
        tree = ast.parse((ROOT / "engine" / "source" / "cad" / name).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                t = node.type
                assert t is not None and not (isinstance(t, ast.Name) and t.id in ("Exception", "BaseException")), name
