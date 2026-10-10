"""§14: the UNRESOLVED population is ranked by impact, never by length.

"Do not call a wall important merely because it is long." The ranking is
inherited from measured leak topology, and a place on the list is not
evidence that the stroke is a wall.
"""

from engine import unresolved_impact as ui


class _Stroke:
    def __init__(self, i, length, cls="UNRESOLVED"):
        self.stroke_id, self.stroke_class = i, cls
        self.axis, self.fixed_mm = "H", 0.0
        self.start_mm, self.end_mm = 0.0, length

    @property
    def length_mm(self):
        return abs(self.end_mm - self.start_mm)


class _Leak:
    def __init__(self, i, *, aperture=(), frontier=(), a=(), b=(),
                 aperture_len=0.0):
        self.leak_id = i
        self.strokes_at_aperture = aperture
        self.unpaired_strokes_at_frontier = frontier
        self.labels_a, self.labels_b = a, b
        self.aperture_length_mm = aperture_len


def test_a_long_stroke_nowhere_near_a_failure_outranks_nothing():
    strokes = [_Stroke("LONG", 40000.0), _Stroke("SHORT", 300.0)]
    leaks = [_Leak("LK-1", aperture=("SHORT",), a=("BED-09",),
                   b=("BTH-09",), aperture_len=800.0)]
    r = ui.assess(strokes, leaks).record()
    assert [w["stroke_id"] for w in r["work_list"]] == ["SHORT"]
    assert r["by_impact"][ui.IMPACT_IN_AN_APERTURE] == 1
    assert r["by_impact"][ui.IMPACT_NONE] == 1
    # The 40 m stroke is in the population and not in the work list.
    assert r["population_length_m"] == 40.3
    assert r["length_at_a_measured_separation_failure_m"] == 0.3


def test_a_frozen_control_aperture_outranks_an_ordinary_aperture():
    strokes = [_Stroke("ORD", 900.0), _Stroke("CTL", 100.0)]
    leaks = [_Leak("LK-1", aperture=("ORD",), a=("BED-09",), b=("BTH-09",),
                   aperture_len=900.0),
             _Leak("LK-2", aperture=("CTL",), a=("BED-01",), b=("COR-02",),
                   aperture_len=200.0)]
    r = ui.assess(strokes, leaks, controls=("BED-01",)).record()
    got = [w["stroke_id"] for w in r["work_list"]]
    assert got == ["CTL", "ORD"], "the shorter control stroke must rank first"


def test_a_control_frontier_outranks_an_ordinary_frontier():
    strokes = [_Stroke("ORD", 5000.0), _Stroke("CTL", 200.0)]
    leaks = [_Leak("LK-1", frontier=("ORD",), a=("BED-09",), b=("BTH-09",)),
             _Leak("LK-2", frontier=("CTL",), a=("BED-01",), b=("COR-02",))]
    r = ui.assess(strokes, leaks, controls=("BED-01",)).record()
    assert [w["stroke_id"] for w in r["work_list"]] == ["CTL", "ORD"]
    assert r["work_list"][0]["impact"] == ui.IMPACT_ON_A_CONTROL_FRONTIER


def test_an_aperture_hit_outranks_a_frontier_hit():
    strokes = [_Stroke("FRONT", 5000.0), _Stroke("HOLE", 150.0)]
    leaks = [_Leak("LK-1", frontier=("FRONT",), a=("A",), b=("B",)),
             _Leak("LK-2", aperture=("HOLE",), a=("A",), b=("B",),
                   aperture_len=400.0)]
    r = ui.assess(strokes, leaks).record()
    assert [w["stroke_id"] for w in r["work_list"]] == ["HOLE", "FRONT"]


def test_only_the_named_class_is_examined():
    strokes = [_Stroke("U", 1000.0), _Stroke("F", 9000.0, "FRAGMENTED_MATE")]
    r = ui.assess(strokes, []).record()
    assert r["strokes_in_population"] == 1
    assert r["population_length_m"] == 1.0


def test_empty_tiers_are_declared_rather_than_hidden():
    """A ranking whose top tier is empty must say so, not imply coverage."""
    r = ui.assess([_Stroke("A", 500.0)], []).record()
    assert ui.IMPACT_IN_AN_APERTURE in r["tiers_with_no_members_here"]
    assert ui.IMPACT_NONE not in r["tiers_with_no_members_here"]
    assert "nothing is drawn at all" in r[
        "what_an_empty_aperture_tier_means"]


def test_a_place_on_the_list_is_not_evidence_the_stroke_is_a_wall():
    r = ui.assess([_Stroke("A", 500.0)], []).record()
    assert "NOT evidence that the stroke is a wall" in r[
        "what_a_place_on_this_list_is_not"]
    assert "remains UNRESOLVED" in r["what_a_place_on_this_list_is_not"]
    assert "NOT by length" in r["ranked_by"]


def test_nothing_is_recovered_or_promoted_here():
    """§14 is a work list. The module may not touch geometry at all.

    Scanned as code, not prose: the docstring is free to say the module
    admits nothing, and the code must contain no way to.
    """
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(ui))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    for forbidden in ("buffer", "union", "unary_union", "difference",
                      "admit", "admissions", "polygons", "ESTABLISHED"):
        assert forbidden not in names, f"{forbidden} has no business here"
    imports = {a.name.split(".")[0]
               for n in ast.walk(tree) if isinstance(n, ast.Import)
               for a in n.names}
    imports |= {(n.module or "").split(".")[0]
                for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert "shapely" not in imports, "a work list needs no geometry kernel"
