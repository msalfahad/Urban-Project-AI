"""M9 S6 Phase 1 - the two unit-dependent geometry tolerances (opening_census.band_gaps merge, drawing_model
closed_rectangles eps) become unit-relative in ARCH_TAKEOFF_V2: 1 mm in every unit, which is exactly 1.0 drawing unit
at millimetres (so millimetre drawings are unchanged by construction; opening_census.py itself is untouched - it is
in the S8.6 freeze's code digest - and engine.source.opening_gaps calls it at 1.0), and the villa drawn in mm / cm /
m / inch measures the same quantities. ARCH_TAKEOFF_V1 keeps the 1.0-unit literals; behind --strict-admission it refuses a
unit too coarse for them."""

from __future__ import annotations

import inspect

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import arch_plan as AP              # noqa: E402
from engine.source import discovery as DS              # noqa: E402
from engine.source import lintel_measure as LM         # noqa: E402
from engine.source import opening_census as OC         # noqa: E402
from engine.source import opening_gaps as OG           # noqa: E402
from tools import urban_boq_m9 as M9                   # noqa: E402

V1, V2 = "ARCH_TAKEOFF_V1", "ARCH_TAKEOFF_V2"


def test_unit_relative_tolerance_is_exactly_the_legacy_one_at_millimetres():
    assert AP.unit_tol(0.001, "UNIT_RELATIVE") == 1.0 == AP.unit_tol(0.001, "LEGACY")
    assert AP.unit_tol(1.0, "UNIT_RELATIVE") == pytest.approx(0.001)
    assert AP.unit_tol(0.01, "UNIT_RELATIVE") == pytest.approx(0.1)
    assert AP.unit_tol(1.0, "LEGACY") == 1.0
    with pytest.raises(ValueError):
        AP.unit_tol(0.001, "OTHER")


def test_legacy_defaults_are_the_old_literals(monkeypatch):
    assert "merge_tol" not in inspect.signature(OC.band_gaps).parameters          # the frozen module is unchanged
    assert inspect.signature(OG.band_gaps).parameters["merge_tol"].default == 1.0
    monkeypatch.setattr(OC, "band_gaps", lambda *a, **k: "FROZEN")
    assert OG.band_gaps({}, merge_tol=1.0) == "FROZEN"                            # 1.0 IS the frozen function
    assert inspect.signature(LM.openings).parameters["tol"].default == "LEGACY"
    assert inspect.signature(AP.layer_roles).parameters["tol"].default == "LEGACY"
    assert inspect.signature(AP.plan_regions).parameters["split"].default == "TITLE_MIDPOINTS"


def test_the_unit_relative_copy_reproduces_the_frozen_band_gaps(build, monkeypatch):
    from tools import urban_intake as UI
    E = UI.read(str(build("base")))
    segs = [(s["id"], tuple(s["a"]), tuple(s["b"])) for s in E["segments"]]
    bands = OC.wall_bands(OC.face_lines(segs, ang_res_deg=0.5, off_tol=2.0, join_tol=5.0, min_len=100.0), 100.0, 450.0,
                          min_overlap=300.0)
    assert bands
    frozen = [OC.band_gaps(b, min_gap=500.0, closures=segs) for b in bands]
    monkeypatch.setattr(OG, "LEGACY_MERGE_TOL", -1.0)                              # force the copy's own path
    copy = [OG.band_gaps(b, min_gap=500.0, closures=segs, merge_tol=1.0) for b in bands]
    assert copy == frozen and any(frozen)


def test_millimetre_villa_v2_keeps_every_v1_quantity(build, h):
    p = build("base")
    r1, a1, _ = M9.arch_compute(str(p), method=V1)
    r2, a2, _ = M9.arch_compute(str(p), method=V2)
    f1, f2 = h.fingerprint(r1, a1), h.fingerprint(r2, a2)
    assert f1["rooms"] == f2["rooms"] and f1["openings"] == f2["openings"] and f1["regions"] == f2["regions"]
    measured = lambda f: [x for x in f["lines"] if x[-1] != "-"]          # noqa: E731
    assert measured(f1) == measured(f2)


@pytest.mark.parametrize("variant", ["units_cm", "units_m", "units_in"])
def test_v2_measures_the_same_villa_in_every_unit(build, h, variant):
    ref = h.fingerprint(*M9.arch_compute(str(build("base")), method=V2)[:2])
    got = h.fingerprint(*M9.arch_compute(str(build(variant)), method=V2)[:2])
    assert got == ref


def test_v1_strict_refuses_a_unit_too_coarse_for_its_tolerances(build, cli, tmp_path, h):
    out = tmp_path / "out"
    rc, _, _ = cli("--drawings", build("units_m"), "--out", out, "--method", V1, "--strict-admission", "--no-svg",
                   "--no-m9-xlsx")
    assert rc == 2
    assert [f["code"] for f in h.read(out, "ADMISSION_BLOCKED.json")["stopping_findings"]] == \
        ["LEGACY_TOLERANCE_TOO_COARSE"]
    ok = tmp_path / "cm"
    assert cli("--drawings", build("units_cm"), "--out", ok, "--method", V1, "--strict-admission", "--no-svg",
               "--no-m9-xlsx")[0] == 0
    assert DS.legacy_tolerance_findings(0.0254) == [] and DS.legacy_tolerance_findings(1.0)


@pytest.mark.xfail(strict=True, reason="S6 Phase 1 open finding (S6P1-NEW-05): a lower length threshold equal to a drafted "
                                       "dimension (the 100 mm minimum face piece) drops that piece once the coordinates "
                                       "are in metres (float rounding); a relative slack fixes it but changes the "
                                       "millimetre result of the reference plan, so it waits for review (Phase 2)")
def test_a_drafted_100_mm_face_piece_survives_in_a_metre_drawing():
    def kept(scale, unit_m):
        a, b = (-152589.86 * scale, 0.0), (-152489.86 * scale, 0.0)        # a 100 mm door-frame return
        k = 1.0 / unit_m / 1000.0
        return len(OC.face_lines([("S", a, b)], ang_res_deg=0.5, off_tol=2.0 * k, join_tol=5.0 * k, min_len=100.0 * k))
    assert kept(1.0, 0.001) == 1                                            # millimetres: kept
    assert kept(0.001, 1.0) == 1                                            # metres: lost to 1e-14
