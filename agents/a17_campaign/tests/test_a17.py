"""A17 — Campaign Manager tests (offline, stub models)."""

import json

import pytest

from agents.a17_campaign.agent import run
from agents.a17_campaign.schema import CampaignInput, Project

ALSENAN = Project(
    name="Alsenan Chalet",
    type="chalet",
    location="Khairan",
    stage="foundations",
    usps=["black structure specialist", "17 footings poured on schedule"],
    photo_refs=["alsenan_render.jpg", "alsenan_pour_01.jpg"],
)


def _campaign(**over):
    base = {
        "objective": "Generate qualified chalet enquiries in Khairan",
        "audience": [{"segment": "families buying land in Khairan", "where": "instagram"}],
        "phases": [{"phase": "Foundations", "milestone": "17 footings", "weeks": "1-4"}],
        "schedule": [
            {"week": 1, "channel": "instagram", "type": "reel",
             "topic": "concrete pour timelapse", "asset": "needs filming",
             "cta": "راسلنا للقياس المجاني"},
        ],
        "channel_weights": {"instagram": 5, "whatsapp": 3},
        "kpis": [{"metric": "qualified enquiries", "target": "8-12"}],
        "review": {"cadence": "weekly, Sunday", "next_review": "2026-10-05"},
    }
    base.update(over)
    return lambda s, u: json.dumps(base, ensure_ascii=False)


def _input(**over):
    kwargs = {"project": ALSENAN, "window": "Oct-Dec 2026", "channels": ["instagram", "whatsapp"]}
    kwargs.update(over)
    return CampaignInput(**kwargs)


# ---- happy path ---------------------------------------------------------------
def test_builds_a_campaign():
    out = run(_input(objective="more chalet enquiries"), model=_campaign())
    assert out.objective and out.schedule and out.channel_weights
    assert out.review["next_review"] == "2026-10-05"


def test_project_and_assets_reach_the_prompt():
    seen = {}

    def model(system, user):
        seen["user"] = user
        return _campaign()(system, user)

    run(_input(), model=model)
    assert "Alsenan Chalet" in seen["user"]
    assert "foundations" in seen["user"]
    assert "alsenan_render.jpg" in seen["user"]


def test_evidence_and_progress_only_included_when_given():
    seen = {}

    def model(system, user):
        seen["user"] = user
        return _campaign()(system, user)

    run(_input(), model=model)
    assert "Progress since the last review" not in seen["user"]

    run(_input(progress={"published": 3, "enquiries": 4}), model=model)
    assert "Progress since the last review" in seen["user"]


def test_review_mode_returns_adjustments():
    out = run(
        _input(progress={"tiktok": {"posts": 3, "enquiries": 0}}),
        model=_campaign(adjustments=[
            {"change": "cut tiktok to weight 1", "evidence": "3 posts, 0 enquiries"}]),
    )
    assert out.adjustments[0]["evidence"] == "3 posts, 0 enquiries"


def test_adjustment_without_evidence_rejected():
    # A change the owner cannot check against a number is an opinion.
    with pytest.raises(ValueError, match="adjustments\\[0\\] is missing evidence"):
        run(_input(progress={"x": 1}),
            model=_campaign(adjustments=[{"change": "cut tiktok"}]))


# ---- validation ---------------------------------------------------------------
def test_empty_schedule_rejected():
    with pytest.raises(ValueError, match="at least one scheduled action"):
        run(_input(), model=_campaign(schedule=[]))


def test_missing_objective_rejected():
    with pytest.raises(ValueError, match="objective"):
        run(_input(), model=_campaign(objective="  "))


def test_missing_channel_weights_rejected():
    with pytest.raises(ValueError, match="channel weights"):
        run(_input(), model=_campaign(channel_weights={}))


def test_negative_channel_weight_rejected():
    with pytest.raises(ValueError, match="must be positive"):
        run(_input(), model=_campaign(channel_weights={"instagram": -2}))


def test_non_numeric_channel_weight_rejected():
    with pytest.raises(ValueError, match="must be a number"):
        run(_input(), model=_campaign(channel_weights={"instagram": "heavy"}))


def test_schedule_item_missing_topic_rejected():
    with pytest.raises(ValueError, match="missing topic"):
        run(_input(), model=_campaign(
            schedule=[{"week": 1, "channel": "instagram", "type": "reel"}]))


def test_schedule_to_unbudgeted_channel_rejected():
    # Scheduling work on a channel with no weight means the budget split funds
    # none of it — a silent hole in the campaign.
    with pytest.raises(ValueError, match="no channel weight"):
        run(_input(), model=_campaign(
            schedule=[{"week": 1, "channel": "tiktok", "type": "reel", "topic": "pour"}]))


def test_a_price_in_the_plan_is_not_the_agents_job():
    # A17 emits weights, never dinars. The engine owns the money — this test
    # pins the contract: weights are numbers without currency attached.
    out = run(_input(), model=_campaign(channel_weights={"instagram": 5, "whatsapp": 3}))
    assert set(out.channel_weights) == {"instagram", "whatsapp"}
    assert all(isinstance(v, (int, float)) for v in out.channel_weights.values())
