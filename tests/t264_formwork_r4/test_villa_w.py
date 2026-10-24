"""T-264 formwork r4 rules on villa W (not the development villa; hand values in formwork_r4.check()).

Normal: a curved ring beam round a void from its own arcs, a beam ending on a 30-degree carrier on both edges, an
exterior ground beam with one face above the outer natural ground and one against fill, a tee cover, a section-CONFLICT
column, a planted column from its slab top. Adverse: chord sides for an arc, a one-face end, an earth-cast face without a
printed detail, formwork on a NOT_PRESENT member, a planted column taken to the foundation, a held line written as 0;
mirror / rotation / units (a ring is the same whatever its orientation; mm inputs are refused by the m-only rules)."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / "research" / "agents_t264" / "formwork_r4.py"


def _load():
    spec = importlib.util.spec_from_file_location("formwork_r4", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = _load()


def test_check_passes():
    assert M.check() is True


def _ring(sweep_out=90.0, sweep_in=90.0):
    return [dict(id="o", source="ARC", R=2.0, sweep_deg=sweep_out, beyond="SLAB"),
            dict(id="i", source="ARC", R=1.8, sweep_deg=sweep_in, beyond="VOID"),
            dict(id="e1", source="LINE", length=0.2, beyond="BEAM", D2=0.60),
            dict(id="e2", source="LINE", length=0.2, beyond="BEAM", D2=0.60)]


def test_ring_on_its_arcs_normal():
    r = M.curved_member(_ring(), 0.60, 0.596903, t=0.15)
    # outer arc 2 x pi / 2 = 3.141593 to the slab x 0.45; inner arc 1.8 x pi / 2 = 2.827433 to the void x 0.45 + band
    assert r["side"] == pytest.approx(3.141593 * 0.45 + 2.827433 * 0.45, abs=1e-6)
    assert r["band"] == pytest.approx(2.827433 * 0.15, abs=1e-6)
    assert r["soffit"] == pytest.approx(0.596903, abs=1e-6)
    # the two straight ends against equal-depth beams are covered
    assert [p["side"] for p in r["by_piece"] if p["id"].startswith("e")] == [0.0, 0.0]


def test_ring_mirror_and_rotation_do_not_change_it():
    # a mirrored / rotated ring has the same radii and sweeps: the faces depend on R x sweep only
    a = M.curved_member(_ring(), 0.60, 0.596903, t=0.15)
    b = M.curved_member(list(reversed(_ring())), 0.60, 0.596903, t=0.15)
    assert a["side"] == pytest.approx(b["side"]) and a["band"] == pytest.approx(b["band"])


def test_adverse_chord_for_an_arc_refused():
    chord = 2 * 1.8 * math.sin(math.radians(45))
    with pytest.raises(M.Refused):
        M.curved_member([dict(id="i", source="ARC", length=chord, beyond="VOID")], 0.60, 0.5)
    with pytest.raises(M.Refused):                    # a sweep given in radians (units) is not a sweep in degrees > 0
        M.arc_length(1.8, 0.0)


def test_oblique_end_both_edges_and_one_face_refused():
    o = M.oblique_end(3.0, 3.11547, 0.20, 0.50, t=0.15)
    assert o["sides"] == pytest.approx(6.11547 * 0.35, abs=1e-6)
    assert o["soffit"] == pytest.approx(0.2 * 6.11547 / 2, abs=1e-6)
    with pytest.raises(M.Refused):
        M.check_oblique_billed(2 * 3.0 * 0.35, 3.0, 3.11547, 0.50, t=0.15)
    # mirrored carrier (edges swapped) gives the same faces
    assert M.oblique_end(3.11547, 3.0, 0.20, 0.50, t=0.15)["sides"] == pytest.approx(o["sides"])


def test_ground_beam_one_face_above_ground_one_against_fill():
    g = M.ground_beam_faces(4.0, 0.90, [("outer", "ABOVE_GROUND"), ("inner", "BURIED")])
    assert g[0] == ("outer", "CALC", pytest.approx(3.6))
    assert ("inner", "FORMED", pytest.approx(3.6)) in g and ("inner", "EARTH_CAST", 0.0) in g
    # a panel not established beside the face: FORMED stays, EARTH_CAST is held, never 0
    u = M.ground_beam_faces(4.0, 0.90, [("inner", "BURIED_EARTH_UNKNOWN")])
    assert u[1][1] == "EARTH_CAST_HELD" and u[1][2] == (0.0, pytest.approx(3.6))


def test_adverse_earth_cast_without_printed_detail_refused():
    with pytest.raises(M.Refused):
        M.ground_beam_faces(4.0, 0.90, [("inner", "EARTH_CAST")])
    with pytest.raises(M.Refused):
        M.ground_beam_faces(4.0, 0.90, [("inner", ("EARTH_CAST", ""))])


def test_tee_cover_exact_and_held():
    assert M.tee_cover(0.30, 0.40, 0.95) == (pytest.approx(0.12), pytest.approx(0.12))
    lo, hi = M.tee_cover(0.30, (0.30, 0.40, 0.95), 0.95)
    assert (lo, hi) == (pytest.approx(0.09), pytest.approx(0.285))
    assert M.tee_cover(0.30, 0.60, 0.40) == (pytest.approx(0.12), pytest.approx(0.12))   # never above the carrier


def test_columns_conflict_planted_not_present():
    st, v = M.column_shaft([1.4, 1.5], 3.0)
    assert st == M.HELD and v == (4.2, 4.5)
    st, v = M.column_shaft([1.8], 3.45, planted=True)
    assert st == M.CALC and v == pytest.approx(6.21)
    with pytest.raises(M.Refused):
        M.column_shaft([1.4], 3.0, existence="NOT_PRESENT")
    with pytest.raises(M.Refused):
        M.column_shaft([1.8], 4.5, planted=True, base="FOUNDATION")


def test_held_never_zero():
    for bad in ((0.0, 0.0), (None, None), (1.0, 0.5)):
        with pytest.raises(M.Refused):
            M.held_range(*bad)
    with pytest.raises(M.Refused):
        M.row("X", "GF", "held written as a value", "G", 1.0, M.HELD, "b")
