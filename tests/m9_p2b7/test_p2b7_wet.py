"""Phase 2B-7 acceptance: the wet-room evidence rule UP-WET-002 (knowledge registry 1.2.0) under ARCH_TAKEOFF_V2.7.
A wash basin alone never makes a space wet; a water closet may be a block, loose linework, linework inside an
anonymously named block, or an Arabic / English room word; two independent pieces of evidence type an unlabelled
space; one geometric shape alone, or an adversary (an oval table, a vanity counter), leaves it REVIEW - never DRY.
The plan (tests/m9_p2b7/p2b7_fixtures.wc_plan): a W.C. 2.00 x 3.00 m (room word) and an unlabelled lobby
3.40 x 3.00 m = 10.20 m2 behind a 0.80 m door."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

ezdxf = pytest.importorskip("ezdxf")

import p2b7_fixtures as F                                     # noqa: E402
import p2b7_run as R                                          # noqa: E402


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b7_wet")


def _lobby(out):
    lob = [r for r in R.rooms(out) if abs(r["area_m2"] - F.WC_TRUTH["lobby_m2"]) < 1e-6]
    assert len(lob) == 1
    return lob[0]


def _run(work, kind, method=R.V27):
    return R.run(F.wc_plan(work / f"WC_{kind}.dxf", kind), work / f"o_{kind}_{method[-3:]}", roles=F.ROLES,
                 facts=True, method=method)


def test_basin_alone_is_review(work):
    """the lobby holds only a WASH block: no room type, no wet and no dry finish lines - its area as ARCH.SPACE and
    a WET_CLASSIFICATION_REVIEW item; the W.C. keeps its own scope and its own doorway waterproofing 0.80 x 0.20 =
    0.16 m2 (V2.6 typed the lobby a bathroom from the basin)."""
    out = _run(work, "BASIN")
    lob = _lobby(out)
    assert lob["class"] == "UNLABELLED" and not lob["codes"]
    assert lob["issue"].startswith("WET_CLASSIFICATION_REVIEW")
    rid = lob["room_id"]
    mine = [ln for ln in R.lines(out) if (ln.get("location") or {}).get("room_id") == rid and
            (ln["item_code"].startswith("FIN.") or ln["item_code"] == "ARCH.SPACE")]
    assert [ln["item_code"] for ln in mine] == ["ARCH.SPACE"] and abs(mine[0]["measured_net"] - 10.2) < 1e-6
    assert any(str(u.get("reason", "")).startswith("WET_CLASSIFICATION_REVIEW") for u in R.unresolved(out))
    assert R.net(out, "FIN.WP.DOORWAY", "Bathroom") == 0.16
    v26 = _run(work, "BASIN", R.V26)
    assert _lobby(v26)["label_source"] == "FIXTURES" and _lobby(v26)["kind"] == "WET"


@pytest.mark.parametrize("kind,source", [("EXPLODED", "FIXTURES+WC_SHAPE+SANITARY_LAYER"),
                                         ("EXPLODED_FURN", "FIXTURES+WC_SHAPE"),
                                         ("ANON_BLOCK", "FIXTURES+WC_SHAPE")])
def test_basin_and_drawn_wc(work, kind, source):
    """the basin and a water closet drawn as linework - loose on a sanitary layer, loose on a furniture layer (the
    shape is the only second evidence), or inside an anonymously named block: two independent pieces of evidence ->
    the lobby is a bathroom (wet floor 10.20 m2, membrane 10.20 m2), flagged for review."""
    out = _run(work, kind)
    lob = _lobby(out)
    assert lob["codes"] == ["BATHROOM"] and lob["label_source"] == source and lob["kind"] == "WET"
    rid = lob["room_id"]
    net = lambda c: sum(ln["measured_net"] or 0 for ln in R.lines(out)                      # noqa: E731
                        if ln["item_code"] == c and (ln.get("location") or {}).get("room_id") == rid)
    assert abs(net("FIN.FLOOR.WET_TILE") - 10.2) < 1e-6 and abs(net("FIN.WP.FLOOR") - 10.2) < 1e-6
    wc = [c for c in R.corrections(out) if c["correction"] == "WET_EVIDENCE"]
    assert wc and wc[0]["decision"] == "WET_BASIN_CORROBORATED"
    w = wc[0]["detail"]["wc_shapes"][0]
    assert w["bowl_m"] == [0.4, 0.6] or w["bowl_m"] == [0.4, 0.599]
    assert w["cistern_m"] == [0.2, 0.5]


def test_one_shape_alone_is_review(work):
    """a water closet drawn as linework, no basin, no word: one geometric shape - WC_CANDIDATE_REVIEW, no type."""
    out = _run(work, "ALONE")
    lob = _lobby(out)
    assert not lob["codes"] and lob["issue"].startswith("WC_CANDIDATE_REVIEW")


@pytest.mark.parametrize("kind", ["OVAL_TABLE", "BASIN_COUNTER"])
def test_adversaries_do_not_make_a_wc(work, kind):
    """an oval table (1.20 x 0.80) with a bench, a vanity counter holding its basin bowl: not a water closet - the
    basin stays alone, the lobby REVIEW."""
    out = _run(work, kind)
    lob = _lobby(out)
    assert not lob["codes"] and lob["issue"].startswith("WET_CLASSIFICATION_REVIEW")


def test_arabic_room_word(work):
    """the Arabic room word for a W.C. inside the lobby types it from the text (the strongest evidence)."""
    out = _run(work, "ARABIC")
    lob = _lobby(out)
    assert lob["codes"] == ["BATHROOM"] and lob["label_source"] == "TEXT"


@pytest.mark.parametrize("kind", ["rot30", "mirror", "metres", "nest"])
def test_wc_evidence_invariant(work, kind):
    base = F.wc_plan(work / f"WCE_{kind}.dxf", "EXPLODED_FURN")
    a = R.run(base, work / f"o_wce_{kind}_a", roles=F.ROLES, facts=True)
    b = R.run(F.variant(base, work / f"WCE_{kind}_v.dxf", kind), work / f"o_wce_{kind}_b", roles=F.ROLES, facts=True)
    assert _lobby(b)["codes"] == ["BATHROOM"]
    assert R.invariant(a, b, tol=1e-5), R.diff(a, b, 1e-5)


def test_doorway_of_a_review_space_takes_no_dry_finish(work):
    """the lobby's external doorway (1.00 x 0.20 m): V2.6 gave it the wet marble threshold (the lobby typed wet from
    its basin); V2.7 must not give it the dry floor porcelain either - the lobby's type is under review. The strip is
    kept measured, with the review question (THRESHOLD_OF_SPACE_UNDER_WET_REVIEW); the W.C.'s own doorway into the
    lobby keeps its marble threshold (a wet side)."""
    out = _run(work, "BASIN")
    strips = {ln["location"]["room_id"]: ln for ln in R.lines(out) if "-STRIP-" in ln["location"]["room_id"]}
    fin = [ln for ln in R.lines(out) if "-STRIP-" in ln["location"]["room_id"] and
           ln["item_code"] in ("FIN.FLOOR.PORCELAIN", "FIN.MARBLE.THRESHOLD")]
    assert [ln["item_code"] for ln in fin] == ["FIN.MARBLE.THRESHOLD"]            # the W.C. doorway only
    assert abs(fin[0]["measured_net"] - 0.8 * 0.2) < 1e-6
    held = [u for u in R.unresolved(out) if str(u.get("reason", "")).startswith("THRESHOLD_OF_SPACE_UNDER_WET_REVIEW")]
    assert len(held) == 1 and "[0.200 m2]" in held[0]["reason"]
    assert any(ln["item_code"] == "ARCH.THRESHOLD" and ln["measured_net"] is None for ln in strips.values())
