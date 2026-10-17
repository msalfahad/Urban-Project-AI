"""The SE elevation owner source check: the audit's declared rules hold
without touching the frozen artifacts (pure declarations and transform)."""

from research.qs_wall_treatment_01 import se_elevation_source_audit as SE


def test_every_audited_owner_is_in_the_physical_vocabulary():
    for tid, rec in SE.AUDIT.items():
        owner = rec["OWNER"] if isinstance(rec, dict) else rec[2]
        assert any(owner.startswith(v) for v in SE.PHYSICAL_OWNERS), (tid, owner)


def test_55_and_50_never_usable_as_plaster_height_from_the_elevation():
    for tid in ("DIM-16", "DIM-14"):
        rec = SE.AUDIT[tid]
        plaster = rec["PLASTER"] if isinstance(rec, dict) else rec[-1]
        assert plaster is False


def test_104_has_a_source_trace_and_is_a_balustrade_assembly_not_a_face():
    rec = SE.AUDIT["DIM-18"]
    owner = rec["OWNER"] if isinstance(rec, dict) else rec[2]
    plaster = rec["PLASTER"] if isinstance(rec, dict) else rec[-1]
    assert owner.startswith("BALUSTRADE_RAILING")
    assert plaster is False


def test_130_is_on_section_b_b_and_a_different_location():
    assert "DIM-07" in SE.AUDIT
    assert any("DIFFERENT_PHYSICAL_LOCATION" in v for k, v in SE.CROSS_SHEET.items() if "130" in k)


def test_processed_to_original_transform_is_the_90_degree_rotation():
    T = {"scale": 0.5, "trim_x0": 10, "trim_y0": 20, "W_orig": 4672}
    x, y = SE._to_orig(T, 100, 40)
    assert (x, y) == ((4672 - 1) - (40 / 0.5 + 20), 100 / 0.5 + 10)
