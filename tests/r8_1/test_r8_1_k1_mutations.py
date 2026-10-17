"""R8.1 — MT-01 / MT-02 / MT-03 / MT-49 re-applied to the REAL production K1.

Each mutation monkeypatches one module-level function of
engine.source.cad.kernel. The frozen R8.0 hand truth must then FAIL on the
scenes the defect affects and still PASS on the scenes it does not.
"""

from __future__ import annotations

import pytest

from engine.source.cad import kernel
from engine.source.cad.affine import Affine2

from .helpers import BP, CURVE, NON_REFLECTING, REFLECTING, base_point_failures, curve_scene_failures

OCS_SCENES = ["F03_OCS_NEG_Z_INSERT", "F03_OCS_NEG_Z_ENTITIES"]
NEG_SCALE_REFLECTING = [s for s in REFLECTING if s not in OCS_SCENES]


# baseline --------------------------------------------------------------------
@pytest.mark.parametrize("sid", sorted(CURVE))
def test_unmutated_k1_passes_every_curve_scene(sid):
    assert curve_scene_failures(sid) == []


@pytest.mark.parametrize("sid", sorted(BP))
def test_unmutated_k1_passes_every_base_point_scene(sid):
    assert base_point_failures(sid) == []


# MT-01 skip base point -----------------------------------------------------------
@pytest.fixture
def mt01(monkeypatch):
    real = kernel.insert_matrix
    monkeypatch.setattr(kernel, "insert_matrix", lambda ins, base_point, offset=(0.0, 0.0): real(ins, (0.0, 0.0), offset))


@pytest.mark.parametrize("sid", sorted(BP))
def test_MT01_real_k1_skip_base_point_detected(mt01, sid):
    assert base_point_failures(sid)


@pytest.mark.parametrize("sid", sorted(CURVE))
def test_MT01_real_k1_scenes_without_base_point_unaffected(mt01, sid):
    assert curve_scene_failures(sid) == []


# MT-02 mirror applied as a 180 deg rotation ------------------------------------
@pytest.fixture
def mt02(monkeypatch):
    def mirror_as_rotation(sx, sy):
        m = Affine2.scale(abs(sx), abs(sy))
        return Affine2.rotation(3.141592653589793) @ m if sx * sy < 0 else m
    monkeypatch.setattr(kernel, "scale_matrix", mirror_as_rotation)


@pytest.mark.parametrize("sid", NEG_SCALE_REFLECTING + ["F05_DOUBLE_REFLECTION_CANCELS"])
def test_MT02_real_k1_mirror_as_rotation_detected(mt02, sid):
    assert curve_scene_failures(sid)


@pytest.mark.parametrize("sid", [s for s in NON_REFLECTING if s != "F05_DOUBLE_REFLECTION_CANCELS"] + OCS_SCENES)
def test_MT02_real_k1_scenes_without_negative_scale_unaffected(mt02, sid):
    assert curve_scene_failures(sid) == []


# MT-03 drop OCS --------------------------------------------------------------------
@pytest.fixture
def mt03(monkeypatch):
    real = kernel.frame_matrix

    def drop_ocs(extrusion):
        real(extrusion)                 # keep the fail-closed validation, drop the frame
        return Affine2.identity()
    monkeypatch.setattr(kernel, "frame_matrix", drop_ocs)


@pytest.mark.parametrize("sid", OCS_SCENES)
def test_MT03_real_k1_drop_ocs_detected(mt03, sid):
    assert curve_scene_failures(sid)


@pytest.mark.parametrize("sid", [s for s in sorted(CURVE) if s not in OCS_SCENES])
def test_MT03_real_k1_plus_z_scenes_unaffected(mt03, sid):
    assert curve_scene_failures(sid) == []


# MT-49 orientation keyed on the entity frame only -------------------------------
@pytest.fixture
def mt49(monkeypatch):
    monkeypatch.setattr(kernel, "curve_orientation", lambda full, frame: 1 if frame.det() > 0 else -1)


@pytest.mark.parametrize("sid", NEG_SCALE_REFLECTING)
def test_MT49_real_k1_extrusion_only_orientation_detected(mt49, sid):
    bad = curve_scene_failures(sid)
    assert "SWEEP_DIRECTION" in bad and "bulge.SWEEP_DIRECTION" in bad


@pytest.mark.parametrize("sid", NEG_SCALE_REFLECTING)
def test_MT49_real_k1_raises_its_own_orientation_finding(mt49, sid):
    from .helpers import k1
    got = k1(CURVE[sid][3])
    assert any(f["code"] == "KERNEL_ORIENTATION_INCONSISTENT" and f["blocks_final"] for f in got["findings"])


def test_MT49_real_k1_entity_level_ocs_still_right(mt49):
    """Keyed on the entity frame the decision IS right for an entity whose own
    extrusion is -Z — which is why an extrusion-only fix looks finished."""
    assert curve_scene_failures("F03_OCS_NEG_Z_ENTITIES") == []
