"""R8.2 — K2: an ezdxf-based route that reproduces the frozen hand truth on its own (§8-§13)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from engine.source import findings as F
from engine.source.cad import kernel_ezdxf as K2
from tests.r8_0 import scenes as S
from tests.r8_0.geometry import compare_arc, compare_bulge, compare_segment, failed_fields

from .pairing import build_dxf

ROOT = Path(__file__).resolve().parents[2]
CURVE = {c[1]: c for c in S.CURVE_CASES}
BP = {c[1]: c for c in S.BASE_POINT_CASES}
MI = {c[1]: c for c in S.MINSERT_CASES}
XREF = {c[1]: c for c in S.XREF_CASES}


def k2(scene):
    return K2.realise(build_dxf(scene)).as_contract_dict()


def _curve_failures(truth, got):
    if len(got["arcs"]) != 1 or len(got["bulges"]) != 1:
        return ["COUNT"]
    return (failed_fields(compare_arc(truth["arc"], got["arcs"][0]))
            + ["bulge." + f for f in failed_fields(compare_bulge(truth["bulge"], got["bulges"][0]))]
            + ["line." + f for f in failed_fields(compare_segment(truth["line"], got["segments"][0]))])


@pytest.mark.parametrize("sid", sorted(CURVE))
def test_k2_reproduces_curve_truth(sid):
    got = k2(CURVE[sid][3])
    assert _curve_failures(S.curve_case_truth(CURVE[sid]), got) == [] and got["findings"] == []


@pytest.mark.parametrize("sid", sorted(BP))
def test_k2_reproduces_base_point_truth(sid):
    assert _curve_failures(S.base_point_truth(BP[sid]), k2(BP[sid][3])) == []


@pytest.mark.parametrize("sid", sorted(set(MI) - {"F06_MINSERT_MIRRORED_PARENT"}))
def test_k2_reproduces_minsert_truth_every_cell(sid):
    got = k2(MI[sid][3])
    from tests.r8_0.geometry import match_segment_sets
    matched, missing, extra = match_segment_sets(MI[sid][4], got["segments"])
    assert not missing and not extra


def test_k2_flags_the_preregistered_nested_reflected_minsert_limitation():
    got = k2(MI["F06_MINSERT_MIRRORED_PARENT"][3])
    lim = [f for f in got["findings"] if f["code"] == F.KNOWN_LIBRARY_LIMITATION]
    assert len(lim) == 6 and all("EZDXF-L02" in f["detail"] and f["blocks_final"] for f in lim)


def test_k2_non_uniform_scale_is_exact_elliptical_arcs():
    got = k2(S.F04_SCENE)
    assert got["arcs"] == [] and len(got["elliptical_arcs"]) == 2
    for e in got["elliptical_arcs"]:
        for k, want in S.F04_TRUTH_POINTS.items():
            assert abs(e[k][0] - want[0]) < 1e-9 and abs(e[k][1] - want[1]) < 1e-9
    assert [f["code"] for f in got["findings"]] == [F.NON_UNIFORM_SCALE_CURVE] * 2


@pytest.mark.parametrize("sid", sorted(XREF))
def test_k2_xref_is_a_finding_never_zero_geometry(sid):
    got = k2(XREF[sid][3])
    codes = [f["code"] for f in got["findings"]]
    assert any(c.startswith("XREF_") for c in codes) and "EZDXF-L03" in got["findings"][0]["detail"]


def test_k2_tilted_frame_is_unsupported():
    got = k2(S.frame_scene([0.0, 0.6, 0.8]))
    assert [f["code"] for f in got["findings"]] == [F.UNSUPPORTED_FRAME] and got["arcs"] == []


def test_k2_route_decode_failure_is_a_finding(tmp_path):
    p = tmp_path / "broken.dxf"
    p.write_text("  0\nSECTION\n  2\nHEADER\n")
    doc, findings = K2.load(p)
    assert doc is None and [f.code for f in findings] == [F.ROUTE_DECODE_FAILED]


def test_k2_attributes_are_placed_by_ezdxf():
    import ezdxf
    doc = ezdxf.new()
    b = doc.blocks.new("D")
    b.add_line((0, 0), (0, 900))
    b.add_attdef("NO", (100, 450))
    ins = doc.modelspace().add_blockref("D", (5000, 0))
    ins.add_auto_attribs({"NO": "D03"})
    got = K2.realise(doc).as_contract_dict()
    assert got["attributes"][0]["value"] == "D03" and abs(got["attributes"][0]["insertion"][0] - 5100.0) < 1e-9


# ---------------------------------------------------------------- independence

def _imports(path):
    tree = ast.parse(path.read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level:
                mod = "." * node.level + mod
            names.add(mod)
            names |= {f"{mod}.{a.name}" for a in node.names}
        elif isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
    return names


def test_k2_shares_no_transformation_mathematics_with_k1():
    names = _imports(ROOT / "engine/source/cad/kernel_ezdxf.py")
    for forbidden in ("kernel", "kernel_ocs", "affine", ".kernel", ".kernel_ocs", ".affine"):
        assert not any(n == forbidden or n.endswith("." + forbidden.lstrip(".")) and "kernel_ezdxf" not in n
                       for n in names), (forbidden, sorted(names))
    src = (ROOT / "engine/source/cad/kernel_ezdxf.py").read_text()
    for sym in ("insert_matrix", "curve_orientation", "Affine2", "plan_frame", "arbitrary_axes"):
        assert sym not in src, sym


def test_k1_does_not_import_ezdxf():
    for p in (ROOT / "engine/source").rglob("*.py"):
        if p.name == "kernel_ezdxf.py":
            continue
        assert not any(n == "ezdxf" or n.startswith("ezdxf.") for n in _imports(p)), p


def test_limitations_are_preregistered_with_required_fields():
    for lid, lim in K2.EZDXF_LIMITATIONS.items():
        for f in ("version", "operation", "behaviour", "fixture", "classification", "k2_handling", "k2_final_in_domain"):
            assert f in lim, (lid, f)
        assert lim["version"] == __import__("ezdxf").__version__
