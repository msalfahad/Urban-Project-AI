"""Phase N10 - masonry by thickness (ARCH_TAKEOFF_V2.9, UP-MAS-HEIGHT-001), against hand truth (n10_truth.py).

The wall panel runs from the floor's structural slab top (T.O.S.) to the soffit above (U/S SLAB), both read from the
floor's own section; a finish height or floor-to-floor is never a masonry height. The run is the wall-mass plan area
over the thickness (corners counted once), the wall above / below each opening added back. Beams over walls and the
wall material are separate evidence: without them the panel is held (upper bound) or a range, and MAS.BLOCK (the
material item) stays an RFI naming exactly what is missing."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import n10_fixtures as F                                      # noqa: E402
import n10_run as R                                           # noqa: E402
import n10_truth as T                                         # noqa: E402

A = 1e-6
NO_BEAMS = {"masonry": {"*": {"beams_over_walls": {"state": "NONE", "authority": "OWNER_PROJECT_FACT: synthetic"}}}}
BLOCK = {"materials": {"0.20": {"value": "BLOCK_200", "authority": "OWNER_PROJECT_FACT: synthetic"}}}


@pytest.fixture(scope="module")
def ex(tmp_path_factory):
    cache, root = {}, tmp_path_factory.mktemp("n10_mas")

    def get(section="TOS", partition=False, facts=None, method=R.V29):
        key = (section, partition, repr(facts), method)
        if key not in cache:
            name = f"{section}_{partition}_{len(cache)}"
            dxf = F.masonry_room(root / f"{name}.dxf", section=section, partition=partition)
            cache[key] = R.run_facts(dxf, root / f"o_{name}", facts, method=method) if facts else \
                R.run(dxf, root / f"o_{name}", method=method)
        return cache[key]
    return get


def _one(out, code, el="walls t=0.20"):
    return R.the(out, code, el)


def test_hand_truth_is_consistent():
    assert T.MAS_AREA == pytest.approx(T.MAS_AREA_CENTRELINE_CHECK, abs=1e-9)          # two derivations, one value
    assert T.MAS_AREA == pytest.approx(43.26, abs=1e-9) and T.MAS_AREA_LOW == pytest.approx(35.86, abs=1e-9)


def test_panel_measured_with_beams_stated_absent(ex):
    out = ex(facts=NO_BEAMS)
    assert _one(out, "ARCH.WALL_PANEL")["measured_net"] == pytest.approx(T.MAS_AREA, abs=A)
    assert _one(out, "ARCH.WALL_VOLUME")["measured_net"] == pytest.approx(T.MAS_VOLUME, abs=A)
    fam = R.masonry(out)[0]["families"]["0.20"]
    assert fam["run_equivalent_lm"] == pytest.approx(T.MAS_RUN_EQ, abs=A)
    assert fam["panel_m"] == pytest.approx(T.MAS_PANEL, abs=A)
    assert R.masonry(out)[0]["evidence"]["buildup_m"] == pytest.approx(T.MAS_BUILDUP, abs=A)
    # the material is not stated: MAS.BLOCK stays an RFI on the material only
    mb = _one(out, "MAS.BLOCK")
    assert mb["measured_net"] is None and "material" in mb["rfi"]["question"] and "panel" not in mb["rfi"]["question"]


def test_block_wall_with_its_material_stated(ex):
    out = ex(facts={"masonry": dict(NO_BEAMS["masonry"], **BLOCK)})
    mb = _one(out, "MAS.BLOCK")
    assert mb["measured_net"] == pytest.approx(T.MAS_AREA, abs=A) and mb["evidence_state"] == "PROVISIONAL"


def test_beams_not_established_hold_the_panel_at_its_upper_bound(ex):
    out = ex()
    ln = _one(out, "ARCH.WALL_PANEL")
    assert ln["measured_net"] is None and ln["evidence_state"] == "BLOCKED_RFI"
    assert ln["calculation"]["inputs"]["upper_bound"] == pytest.approx(T.MAS_AREA, abs=A)
    assert "BEAMS_OVER_WALLS_NOT_ESTABLISHED" in ln["rfi"]["question"]


def test_beam_bottom_on_the_section_gives_a_range(ex):
    out = ex(section="BOB")
    rg = _one(out, "ARCH.WALL_PANEL")["bounded_range"]
    assert (rg["low"], rg["high"]) == (pytest.approx(T.MAS_AREA_LOW, abs=A), pytest.approx(T.MAS_AREA, abs=A))


@pytest.mark.parametrize("section,why", [("NO_TOS", "T.O.S."), ("TWO", "SECTIONS_DISAGREE"), (None, "T.O.S.")])
def test_no_masonry_height_without_its_evidence(ex, section, why):
    out = ex(section=section, facts=NO_BEAMS)
    for code in ("ARCH.WALL_PANEL", "ARCH.WALL_VOLUME", "MAS.BLOCK"):
        ln = _one(out, code)
        assert ln["measured_net"] is None and ln["evidence_state"] == "BLOCKED_RFI"
        assert why in ln["rfi"]["question"]
    # the finish height (F.C.L. +3.00) or the plaster height is never taken as the masonry height
    assert not [ln for ln in R.lines(out) if ln["item_code"] == "ARCH.WALL_PANEL" and ln["measured_net"]]


def test_masonry_height_from_stated_project_facts(ex):
    facts = {"masonry": {"*": {"panel_height_m": {"value_m": 3.20, "authority": "OWNER_PROJECT_FACT: synthetic"},
                               "floor_buildup_m": {"value_m": 0.10, "authority": "OWNER_PROJECT_FACT: synthetic"},
                               "beams_over_walls": NO_BEAMS["masonry"]["*"]["beams_over_walls"]}}}
    out = ex(section="NO_TOS", facts=facts)
    assert _one(out, "ARCH.WALL_PANEL")["measured_net"] == pytest.approx(T.MAS_AREA, abs=A)
    assert R.masonry(out)[0]["evidence"]["kind"] == "PROJECT_RULE"


def test_two_thickness_families_and_their_junctions(ex):
    out = ex(partition=True, facts=NO_BEAMS)
    assert _one(out, "ARCH.WALL_PANEL", "walls t=0.15")["measured_net"] == pytest.approx(T.MAS_PART_AREA, abs=A)
    assert _one(out, "ARCH.WALL_VOLUME", "walls t=0.15")["measured_net"] == pytest.approx(T.MAS_PART_VOLUME, abs=A)
    assert _one(out, "ARCH.WALL_PANEL")["measured_net"] == pytest.approx(T.MAS_EXT_AREA_WITH_PART, abs=A)
    j = R.the(out, "ARCH.WALL_VOLUME", "walls junctions (mixed thickness)")
    assert j["measured_net"] == pytest.approx(T.MAS_JUNCTION_VOLUME, abs=A)


def test_earlier_methods_keep_their_block_wall_rfi(ex):
    out = ex(facts=NO_BEAMS, method=R.V28)
    assert not R.all_of(out, "ARCH.WALL_PANEL")
    assert _one(out, "MAS.BLOCK")["measured_net"] is None
