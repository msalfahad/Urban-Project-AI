"""Phase 2A P2-09a: the read-only dimension cross-check (round 2 AT-Q4-01 .. 05) - DIMLFAC per dimension, the census,
opening widths and wall thicknesses against authored dimensions, stale / overridden dimensions never used, no
quantity changed, dimension evidence on doors without promotion."""

from __future__ import annotations

import math

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import dimension_evidence as DEV            # noqa: E402
from tools import arch_dimensions as ADIM                      # noqa: E402


def _rec(**kw):
    base = {"handle": "D1", "type": "ALIGNED", "layer": "DIM", "p1": [0, 500], "p2": [0.0, 0.0], "p3": [1000.0, 0.0],
            "angle": 0.0, "dimstyle": "S", "style_dimlfac": None, "override_dimlfac": None, "measurement": None,
            "text": "", "shown_text": "1000"}
    base.update(kw)
    return base


def test_dimlfac_from_the_style_and_from_the_header_both_give_the_defpoint_distance():
    """AT-Q4-01: DIMLFAC 0.1 in the dimension style only (header 1.0), and 0.1 in the header with a style that sets
    none: the value in drawing units equals the defpoint distance in both; an entity override wins over both."""
    a = DEV.resolve(_rec(style_dimlfac=0.1, shown_text="100"), 1.0, 1e-3)
    b = DEV.resolve(_rec(style_dimlfac=None, shown_text="100"), 0.1, 1e-3)
    c = DEV.resolve(_rec(style_dimlfac=0.1, override_dimlfac=0.5, shown_text="500"), 0.1, 1e-3)
    for d, src in ((a, "DIMENSION_STYLE"), (b, "HEADER (style sets none)"), (c, "ENTITY_OVERRIDE")):
        assert d["usable"] and d["dimlfac_source"] == src and d["value_du"] == pytest.approx(d["geometry_du"])


def test_the_reader_resolves_dimlfac_per_dimension_from_a_real_dxf(tmp_path):
    doc = ezdxf.new("R2018", setup=True)
    doc.header["$INSUNITS"] = 4
    doc.header["$DIMLFAC"] = 1.0
    st = doc.dimstyles.duplicate_entry("EZDXF", "TENTH")
    st.dxf.dimlfac = 0.1
    one = doc.dimstyles.duplicate_entry("EZDXF", "ONE")
    one.dxf.dimlfac = 1.0
    msp = doc.modelspace()
    msp.add_aligned_dim(p1=(0, 0), p2=(1000, 0), distance=300, dimstyle="TENTH").render()
    msp.add_aligned_dim(p1=(0, 2000), p2=(1500, 2000), distance=300, dimstyle="ONE").render()
    msp.add_aligned_dim(p1=(0, 4000), p2=(800, 4000), distance=300, dimstyle="ONE", override={"dimlfac": 0.5}).render()
    p = tmp_path / "d.dxf"
    doc.saveas(p)
    R = ADIM.read(p)
    rs = [DEV.resolve(d, R["header_dimlfac"], 1e-3) for d in R["dimensions"]]
    assert sorted(d["dimlfac_source"] for d in rs) == ["DIMENSION_STYLE", "DIMENSION_STYLE", "ENTITY_OVERRIDE"]
    assert all(d["usable"] and d["value_du"] == pytest.approx(d["geometry_du"], abs=1e-6) for d in rs)


def test_a_stale_or_overridden_dimension_is_reported_and_never_used():
    d = DEV.resolve(_rec(text="1200"), 1.0, 1e-3)
    assert not d["usable"] and d["why_not"].startswith("SHOWN_VALUE_DIFFERS") and d["text_overridden"]
    x = DEV.crosscheck([d], [], 1e-3)
    assert [f["code"] for f in x["findings"]] == ["DIMENSION_STALE_OR_OVERRIDDEN"] and not x["checks"]


def test_group_42_scaling_is_reported_not_assumed():
    assert DEV.resolve(_rec(measurement=1000.0), 1.0, 1e-3)["measurement_matches"] == "UNSCALED"
    assert DEV.resolve(_rec(measurement=100.0, style_dimlfac=0.1, shown_text="100"), 1.0, 1e-3)[
        "measurement_matches"] == "SCALED_BY_DIMLFAC"


@pytest.fixture(scope="module")
def dimensioned_villa(tmp_path_factory):
    """the synthetic villa with aligned dimensions across 5 openings and 5 wall thicknesses at their jambs, and one
    extra dimension 10 mm longer than its opening (an authored dimension that disagrees with the plan)."""
    from tools import arch_synth as AS
    from tools import urban_boq_m9 as M9
    d = tmp_path_factory.mktemp("dv")
    p = d / "villa.dxf"
    AS.villa(str(p))
    room0, arch0, _E = M9.arch_compute(str(p), method="ARCH_TAKEOFF_V2.1")
    from tools import urban_intake as UI
    from tools import arch_intake as AI
    from engine.source import arch_plan as AP
    E = UI.read(str(p))
    A = AI.read_arch(p, unit_m=E["unit_m"])
    E = dict(E, hatches=[dict(h, ring=h["rings"][0]) for h in A["hatches"] if h["rings"]], texts=A["texts"],
             inserts=A["inserts"], segments=E["segments"] + A["extra_segments"], arcs=E["arcs"] + A["extra_arcs"])
    P = AP.plan_regions(E, split="EMPTY_BANDS", frames_from_lines_fallback=True)
    reg = next(r for r in P["regions"] if r["floor"] == "GF")
    from engine.source import arch_rooms as AR
    from engine.source import robust_geometry as RG
    ents = AP.region_entities(E, reg["box"])
    L = AP.layer_roles(ents, E["unit_m"], tol="UNIT_RELATIVE", geom=RG.Geometry(E["unit_m"]))
    S = AR.spaces(ents, L["roles"], E["unit_m"], region_id=reg["region_id"], tol="UNIT_RELATIVE",
                  geom=RG.Geometry(E["unit_m"]))
    ops = S["openings"][:5]
    doc = ezdxf.readfile(str(p))
    msp = doc.modelspace()
    st = doc.dimstyles.new("PLAN")
    st.dxf.dimlfac = 1.0
    for i, o in enumerate(ops):
        u, n = o["u"], o["n"]
        face = o["o0"]
        a = (u[0] * o["s0"] + n[0] * face, u[1] * o["s0"] + n[1] * face)
        b = (u[0] * o["s1"] + n[0] * face, u[1] * o["s1"] + n[1] * face)
        msp.add_aligned_dim(p1=a, p2=b, distance=-300, dimstyle="PLAN").render()
        f0 = (u[0] * (o["s0"] - 50) + n[0] * o["o0"], u[1] * (o["s0"] - 50) + n[1] * o["o0"])
        f1 = (u[0] * (o["s0"] - 50) + n[0] * o["o1"], u[1] * (o["s0"] - 50) + n[1] * o["o1"])
        msp.add_aligned_dim(p1=f0, p2=f1, distance=400, dimstyle="PLAN").render()
    o = S["openings"][5]
    u, n = o["u"], o["n"]
    a = (u[0] * o["s0"] + n[0] * o["o0"], u[1] * o["s0"] + n[1] * o["o0"])
    b = (u[0] * (o["s1"] + 10.0) + n[0] * o["o0"], u[1] * (o["s1"] + 10.0) + n[1] * o["o0"])
    msp.add_aligned_dim(p1=a, p2=b, distance=-300, dimstyle="PLAN").render()
    q = d / "villa_dims.dxf"
    doc.saveas(q)
    room2, arch2, _E2 = M9.arch_compute(str(q), method="ARCH_TAKEOFF_V2.1")
    return (room0, arch0), (room2, arch2)


def test_five_openings_and_five_walls_agree_and_one_10_mm_difference_is_exactly_one_review(dimensioned_villa):
    """AT-Q4-03 (the 10 mm case as an authored dimension that disagrees with the plan)."""
    _base, (_room, arch) = dimensioned_villa
    D = arch["dimensions"]
    assert D["checks_by_state"].get("OPENING_WIDTH:AGREES") == 5
    assert D["checks_by_state"].get("WALL_THICKNESS:AGREES", 0) >= 5
    assert D["checks_by_state"].get("OPENING_WIDTH:REVIEW") == 1
    agree = [c for r in D["regions"] for c in r["checks"] if c["state"] == "AGREES"]
    assert agree and all(abs(c["diff_mm"]) < 1e-6 for c in agree)
    rev = [f for f in D["findings"] if f["code"].endswith("_DIFFERS")]
    assert len(rev) == 1 and "+10.0 mm" in rev[0]["message"]


def test_the_cross_check_changes_no_quantity(dimensioned_villa):
    """AT-Q4-04: the BOQ lines, openings and rooms are identical with and without the dimensions in the drawing; the
    only difference is the cross-check output itself."""
    (room0, arch0), (room1, arch1) = dimensioned_villa

    def q(room):
        return sorted((ln["line_id"], ln["evidence_state"], repr(ln.get("measured_net"))) for ln in room["lines"])
    assert q(room0) and q(room0) == q(room1)
    assert [(o["floor"], o["kind"], o["width_m"]) for o in arch0["openings"]] == \
        [(o["floor"], o["kind"], o["width_m"]) for o in arch1["openings"]]
    assert {r["room_id"]: r["area_m2"] for r in arch0["rooms"]} == {r["room_id"]: r["area_m2"] for r in arch1["rooms"]}
    assert arch0["dimensions"]["counts"]["total"] == 0 and arch1["dimensions"]["counts"]["total"] == 11      # 5 widths + 5 thicknesses + 1


def test_dimension_evidence_on_a_provisional_door_never_promotes_it():
    """AT-Q4-05 is implemented behind a policy switch that the V2.1 run keeps off (owner decision pending)."""
    from engine.source import door_model as DM
    el = {"element_id": "E1", "state": DM.PROVISIONAL, "opening_id": None, "u": [1.0, 0.0], "n": [0.0, 1.0],
          "centre": [400.0, 0.0], "structural_opening_width_m": 0.8, "evidence": [], "history": []}
    d = DEV.resolve(_rec(p2=[0.0, 100.0], p3=[800.0, 100.0], shown_text="800"), 1.0, 1e-3)
    x = DEV.crosscheck([d], [], 1e-3, doors=[el])
    assert x["door_evidence"] and x["door_evidence"][0]["agrees"]
    DM.attach_dimensions([el], x["door_evidence"], promote=False)
    assert el["state"] == DM.PROVISIONAL and el["evidence"][-1]["kind"] == "DIMENSION"
    DM.attach_dimensions([el], x["door_evidence"], promote=True)
    assert el["state"] == DM.CONFIRMED and el["history"][-1]["to"] == DM.CONFIRMED


def test_dimension_evidence_is_stdlib_only():
    import ast
    from pathlib import Path
    src = Path(DEV.__file__).read_text(encoding="utf-8")
    mods = {n.module for n in ast.walk(ast.parse(src)) if isinstance(n, ast.ImportFrom)} | \
           {a.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Import) for a in n.names}
    assert mods <= {"__future__", "math", "re", "collections"}
    assert math.isfinite(DEV.AGREE_MM)
