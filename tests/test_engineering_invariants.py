"""Repository-level invariants, enforced across the engine rather than per file.

Both rules here were learned by making the same mistake in more than one
module. Fixing them one module at a time is what let the second occurrence
happen, so they are checked globally.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ENGINE = Path("engine")
MODULES = sorted(ENGINE.glob("*.py"))

# Where an index-join is the legitimate, local idiom rather than an entity
# join: geometry point lists, character strings, matrix rows.
ALLOWED_INDEX_NAMES = {
    "points", "pts", "poly", "polygon", "coords", "xs", "ys", "items",
    "parts", "bounds", "ring", "walk", "segs", "lines", "args", "rows",
    "ranked", "scored", "hits", "group", "runs", "marks", "idxs",
}


def _entity_like(name: str) -> bool:
    """Does this name look like a collection of domain entities?"""
    n = name.lower()
    if n in ALLOWED_INDEX_NAMES:
        return False
    return any(k in n for k in (
        "component", "space", "face", "edge", "node", "band", "region",
        "quantity", "trace", "finding", "terminus", "termini", "cluster"))


def test_no_module_joins_domain_entities_by_array_position():
    """ORDER IS NEVER IDENTITY.

    `cycle_capacity` sorts components by cycle count and `components` sorts
    them by length; joining those two lists on index scored every component
    against another component's numbers. The same reasoning had already
    misidentified spaces across revisions. It is checked globally because
    fixing it per module is what allowed the second occurrence.
    """
    offenders = []
    for path in MODULES:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            # enumerate(entities) whose index is then used to subscript
            # ANOTHER entity collection
            if not isinstance(node, ast.Subscript):
                continue
            target = node.value
            if not isinstance(target, ast.Name) or not _entity_like(target.id):
                continue
            idx = node.slice
            if isinstance(idx, ast.Name) and idx.id in ("i", "j", "k", "n",
                                                        "idx", "index"):
                offenders.append(f"{path.name}:{node.lineno} "
                                 f"{target.id}[{idx.id}]")
    assert not offenders, (
        "domain entities joined by array position:\n  " + "\n  ".join(offenders)
        + "\nJoin by stable id, explicit key, or validated geometry identity.")


def test_the_invariants_are_written_down_where_someone_will_read_them():
    doc = Path("docs/ENGINEERING_INVARIANTS.md")
    assert doc.exists()
    text = doc.read_text()
    assert "ORDER IS NEVER IDENTITY" in text
    assert "DO NOT PROMOTE A PROXY INTO PHYSICAL TRUTH" in text.upper()
    assert "NEVER INVENT THE MISSING HALF" in text.upper()
    assert "A LENGTH WITHOUT A BASIS IS NOT A LENGTH" in text.upper()
    assert "BBOX IS NEVER PHYSICAL GEOMETRY" in text.upper()


def test_no_module_derives_room_geometry_from_a_bounding_box():
    """BBOX IS NEVER PHYSICAL GEOMETRY.

    STR-01's 2606 mm "missing wall" was the east edge of a bounding box
    crossing open space in an L-shaped room. A box may index and localise; the
    moment it supplies a side, a perimeter, a closure or an area, it is
    claiming a shape nobody proved.
    """
    from engine.bbox import PHYSICAL_USES, BoundingBox, BoundingBoxError
    box = BoundingBox("STR-01", 0.0, 0.0, 4000.0, 3000.0, fill_ratio=0.676)
    for use in PHYSICAL_USES:
        with pytest.raises(BoundingBoxError):
            box.physical(use)
    # and the permitted use is still permitted, without ceremony
    assert box.index_extent()


def test_a_raster_outline_may_not_replace_the_retired_bounding_box():
    """The obvious next move, and the one WSH-01 rules out."""
    from engine.bbox import RASTER_MAY, RASTER_MAY_NOT
    assert any("localise" in m for m in RASTER_MAY)
    assert any("construct" in m for m in RASTER_MAY_NOT)


def test_every_module_that_validates_requires_two_evidence_families():
    """Correlated observations of one construction are not independent
    proofs. Any module with a MIN_FAMILIES constant must require at least two.
    """
    import importlib
    for path in MODULES:
        mod = importlib.import_module(f"engine.{path.stem}")
        for name in dir(mod):
            if "MIN_FAMILIES" in name:
                assert getattr(mod, name) >= 2, f"{path.stem}.{name}"


def test_no_module_mirrors_a_lone_wall_face_by_an_assumed_thickness():
    """NEVER INVENT THE MISSING HALF. Mirroring a single face manufactures a
    wall the drawing does not contain, and every quantity downstream inherits
    it."""
    for path in MODULES:
        src = path.read_text().lower()
        for forbidden in ("assumed_thickness", "default_thickness",
                          "mirror_face", "assume_wall_thickness"):
            assert forbidden not in src, f"{path.name}: {forbidden}"


def test_unresolved_is_an_available_answer_in_every_classifier():
    """A classifier with no UNRESOLVED state is a classifier that guesses."""
    import importlib
    classifiers = ("envelope", "connectivity", "wall_bands", "space_model",
                   "face_qa")
    for name in classifiers:
        mod = importlib.import_module(f"engine.{name}")
        names = {n for n in dir(mod) if "UNRESOLVED" in n.upper()}
        assert names, f"engine.{name} has no UNRESOLVED state"
