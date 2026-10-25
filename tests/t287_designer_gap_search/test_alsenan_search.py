"""T-287 development villa (Drive 'Alsenan chalet project'): the committed sheet search ALSENAN_SEARCH_T287.json, pinned;
re-running the search on the private copies (.work/private beside the checkout, never in the repository) reproduces it
byte for byte. Values and handles only.

Pinned findings (worker 1, 2026-10-25):
  G1  no structural level / neck end / section at the CB5 columns on ST p.1 - p.6 or the arch GF plan (MISSING); the
      floors printed beside them: annex +0.30 (ST 1B4 / arch 405) and the side passage / court +0.15; no +1.00 -> base
      +0.25 for both 35F (C5) and 365 (C3), the main-house +0.95 reading has no drawn support.
  G2  the winder turn MS1-T and the 1F turn riser MS2-TR print no level, no wholly-contained dimension, no outline word
      (MISSING); thickness 'T 16' is printed on ST-01 (580 on p.4, 74A on p.5) and on ST-02's straight part (5B6);
      D1, E1 and the curved RS-C print no thickness (MISSING).
  G3  no opening, ring, drum or dome at the tower dome position on ST p.5 / p.6 (MISSING); no drum material or
      thickness at the terrace domes (MISSING); the one dome detail is ST p.7 'DETAIL OF DOME'.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t287"
COMMITTED = json.loads((HERE / "ALSENAN_SEARCH_T287.json").read_text(encoding="utf-8"))
PRIVATE_ST = ROOT.parent / "private" / "ST7757.dxf"
PRIVATE_ARCH = ROOT.parent / "private" / "P7757_DXF" / "P7757.dxf"


def q(qid):
    return COMMITTED["questions"][qid]


def test_every_question_has_a_verdict_and_missing_carries_no_value():
    assert len(COMMITTED["questions"]) == 5 + 14
    for qid, v in COMMITTED["questions"].items():
        assert v["verdict"] in ("FOUND", "MISSING"), qid
        assert (v["verdict"] == "FOUND") == bool(v["hits"]), qid
        assert v["sheets_searched"], qid


def test_g1_no_structural_print_and_base_settled_at_the_annex_slab():
    assert q("G1-a")["verdict"] == "MISSING"
    assert {s for s, _ in q("G1-a")["sheets_searched"]} == {"ST p.1", "ST p.2", "ST p.3", "ST p.4", "ST p.5",
                                                            "ST p.6", "ARCH GF plan"}
    g = COMMITTED["g1_adjoining"]
    for col in ("35F", "365"):
        s = g[col]["space_reading_ARCH_GF"]["settled"]
        assert s["status"] == "SETTLED" and s["base"] == 0.25 and s["indoor_ffl"] == 0.3 and s["exterior"] == [0.15]
        levels = {lv for _, lv, _ in g[col]["space_reading_ARCH_GF"]["by_probe"]}
        assert 1.0 not in levels                            # the main-house floor touches neither column
    assert g["365"]["bay_reading_ST_p3"]["settled"]["base"] == 0.25
    assert g["35F"]["bay_reading_ST_p3"]["settled"]["status"] == "MISSING"     # its kitchen bay prints no mark itself


def test_g2_turns_missing_thickness_found_where_printed():
    assert q("G2-a")["verdict"] == "MISSING" and q("G2-c")["verdict"] == "MISSING"
    found = {k.split(":")[1] for k, v in COMMITTED["questions"].items() if k.startswith("G2-w") and v["hits"]}
    missing = {k.split(":")[1] for k, v in COMMITTED["questions"].items() if k.startswith("G2-w") and not v["hits"]}
    assert missing == {"D1", "E1", "RS-C"}
    assert found == {"MS1-L", "MS1-T", "MS1-LD", "MS1-U", "MS2-L", "MS2-TR", "MS2-LD", "MS2-U", "RS-S", "RS-LD", "RS-A"}
    tags = {h[1] for k, v in COMMITTED["questions"].items() if k.startswith("G2-w") for h in v["hits"]}
    assert tags == {"580", "74A", "5B6"}
    assert COMMITTED["global"]["winder_turn_landing_words"] == []


def test_g3_nothing_structural_at_the_tower_dome():
    assert q("G3-a")["verdict"] == "MISSING" and q("G3-b")["verdict"] == "MISSING"
    assert [h[3] for h in COMMITTED["global"]["dome_ring_drum_words"]] == ["%%uDETAIL OF DOME"]


def test_no_coordinates_and_no_long_drawing_text_committed():
    js = json.dumps(COMMITTED, ensure_ascii=False)
    assert "box" not in js and "pts" not in js
    for v in COMMITTED["global"].values():
        assert all(len(h[3]) <= 40 for h in v)


@pytest.mark.skipif(not (PRIVATE_ST.exists() and PRIVATE_ARCH.exists()), reason="private drawings absent (Drive)")
def test_rerun_on_the_private_drawings_reproduces_the_committed_file():
    spec = importlib.util.spec_from_file_location("t287_alsenan", HERE / "t287_alsenan.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("t287_alsenan", mod)
    spec.loader.exec_module(mod)
    fresh = json.dumps(mod.build(PRIVATE_ST, PRIVATE_ARCH), indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    assert fresh == (HERE / "ALSENAN_SEARCH_T287.json").read_text(encoding="utf-8")
