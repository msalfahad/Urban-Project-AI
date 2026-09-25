"""The unseal pass: identity before comparison, and the frozen takeoff left alone.

The owner unsealed a workbook that is not in the session, and what is in the session measures a different villa.
These tests hold the two things that matter: no comparison was manufactured, and the frozen blind result is
byte-for-byte what it was.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import historical_identification as HI

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"


def ident():
    return json.loads((OUT / "ALRASHED_HISTORICAL_EVIDENCE_IDENTIFICATION.json").read_text("utf-8"))


def frozen():
    return json.loads((OUT / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json").read_text("utf-8"))


def test_the_frozen_blind_takeoff_is_untouched():
    f = frozen()
    assert f["DIGEST"] == "ae259eaba3203798"
    assert f["GIT_HEAD"] == "3e847af"
    assert f["TOTALS"]["BLOCKWORK_200_NET_M2"] == 963.188
    assert f["TOTALS"]["ALUMINIUM_M2"] == 14.3301


def test_no_trade_comparison_was_manufactured():
    c = ident()["COMPARISON_STATUS"]
    assert c["TRADE_COMPARISON_PERFORMED"] is False
    assert c["ALL_TRADES_CLASSIFIED"] == "NOT_COMPARABLE - DIFFERENT_PROJECT"
    assert c["BLIND_TAKEOFF_UNCHANGED"] is True


def test_the_requested_workbook_is_not_in_the_session():
    n = ident()["NAME_SEARCH"]
    assert n["EXACT_MATCH"] is None
    assert 18 not in n["UPLOADED_UNDERSCORE_COUNTS"].values()
    assert "no hit" in n["CONTENT_SEARCH_FOR_الراشد"]


def test_the_different_building_finding_rests_on_more_than_one_decisive_reason():
    e = ident()["NOT_THE_SAME_BUILDING"]
    decisive = [x for x in e if x["WEIGHT"] == "DECISIVE"]
    assert len(decisive) >= 3
    kinds = {x["EVIDENCE"] for x in decisive}
    assert "SWIMMING_POOL" in kinds and "BLOCKWORK_THICKNESS_PROFILE_IS_INVERTED" in kinds
    for x in e:
        assert x["IN_THE_WORKBOOKS"] and x["IN_THE_AL_RASHED_DRAWINGS"]


def test_the_blockwork_inversion_is_stated_against_our_own_frozen_numbers():
    f = frozen()["TOTALS"]
    assert f["BLOCKWORK_200_NET_M2"] > f["BLOCKWORK_150_NET_M2"] * 4, "ours is overwhelmingly 200 mm"
    row = next(x for x in ident()["NOT_THE_SAME_BUILDING"]
               if x["EVIDENCE"] == "BLOCKWORK_THICKNESS_PROFILE_IS_INVERTED")
    assert "963.188" in row["IN_THE_AL_RASHED_DRAWINGS"] and "190.289" in row["IN_THE_AL_RASHED_DRAWINGS"]


def test_no_observed_convention_is_promoted_without_the_owner():
    for c in HI.COMMERCIAL_CONVENTIONS_OBSERVED:
        assert c["PROMOTE"] in ("ASK_THE_OWNER", "NO_CHANGE_NEEDED"), c["CONVENTION"]
        assert c["CLASS"] in ("COMMERCIAL_RULE_DIFFERENCE", "SCOPE_DIFFERENCE", "CLOSE_AGREEMENT")


def test_identity_comes_before_comparison_as_a_stated_rule():
    assert "identity before comparison" in ident()["RULE"].lower()
