"""Campaign CLI plumbing — versioning, budget display, review round-trip.

The model is stubbed; these tests cover the file handling and the engine wiring,
which is where a campaign would silently lose a version or mis-split a budget.
"""

import json

import pytest

from tools import campaign as cli

CAMPAIGN_JSON = {
    "objective": "Generate qualified chalet enquiries in Khairan",
    "audience": [{"segment": "families buying land", "where": "instagram"}],
    "phases": [{"phase": "Foundations", "weeks": "1-4", "focus": "credibility"}],
    "schedule": [
        {"week": 1, "channel": "instagram", "type": "reel",
         "topic": "concrete pour timelapse", "asset": "needs filming"},
        {"week": 2, "channel": "whatsapp", "type": "broadcast",
         "topic": "progress note to warm leads"},
    ],
    "channel_weights": {"instagram": 5, "whatsapp": 3},
    "kpis": [{"metric": "qualified enquiries", "target": "8-12",
              "how_measured": "A3 lead records"}],
    "review": {"cadence": "weekly, Sunday", "next_review": "2026-10-05",
               "bring": ["post metrics", "enquiry count"]},
    "adjustments": [],
    "notes": "",
}


@pytest.fixture(autouse=True)
def sandbox(tmp_path, monkeypatch):
    """Point the CLI at a temp campaigns/ dir and stub the model call."""
    monkeypatch.setattr(cli, "CAMPAIGNS", tmp_path / "campaigns")
    monkeypatch.setattr(cli, "ROOT", tmp_path)

    def fake_a17(payload, model=None):
        from agents.a17_campaign.schema import Campaign
        data = dict(CAMPAIGN_JSON)
        if payload.progress:
            data["adjustments"] = [
                {"change": "cut whatsapp to weight 1", "evidence": "180 sent, 0 enquiries"}]
            data["schedule"] = [{"week": 3, "channel": "instagram",
                                 "type": "carousel", "topic": "footing detail"}]
            data["channel_weights"] = {"instagram": 5}
        return Campaign.from_dict(data)

    monkeypatch.setattr(cli, "a17", fake_a17)
    return tmp_path


def _new(*extra):
    cli.main(["new", "--project", "Alsenan Chalet", "--window", "Oct-Dec 2026",
              "--type", "chalet", "--location", "Khairan", "--stage", "foundations",
              "--channels", "instagram,whatsapp", *extra])


# ---- slug ---------------------------------------------------------------------
def test_slugify():
    assert cli.slugify("Alsenan Chalet") == "alsenan-chalet"
    assert cli.slugify("شاليه القديري 2") == "2"


def test_slugify_rejects_a_nameless_project():
    with pytest.raises(SystemExit):
        cli.slugify("!!!")


# ---- new ----------------------------------------------------------------------
def test_new_writes_v1(sandbox, capsys):
    _new("--budget", "800")
    path = sandbox / "campaigns" / "alsenan-chalet" / "v1.json"
    assert path.is_file()
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["project"]["name"] == "Alsenan Chalet"
    assert record["budget_kwd"] == 800.0
    assert "campaign id: alsenan-chalet" in capsys.readouterr().out


def test_new_shows_the_engine_budget_split(capsys):
    _new("--budget", "800")
    out = capsys.readouterr().out
    # 5:3 of 800 KWD — computed by the engine, never by the agent.
    assert "500.000 KWD" in out
    assert "300.000 KWD" in out


def test_no_budget_shows_weights_instead(capsys):
    _new()
    out = capsys.readouterr().out
    assert "no budget set" in out and "weight 5" in out
    assert "KWD" not in out


def test_usps_and_photos_are_repeatable(sandbox):
    _new("--usp", "black structure", "--usp", "on schedule", "--photo", "render.jpg")
    record = json.loads((sandbox / "campaigns" / "alsenan-chalet" / "v1.json").read_text())
    assert record["project"]["usps"] == ["black structure", "on schedule"]
    assert record["project"]["photo_refs"] == ["render.jpg"]


# ---- review -------------------------------------------------------------------
def test_review_writes_v2_and_keeps_v1(sandbox, tmp_path):
    _new("--budget", "800")
    progress = tmp_path / "week1.json"
    progress.write_text(json.dumps({"instagram": {"posts": 2, "enquiries": 5}}))

    cli.main(["review", "--campaign", "alsenan-chalet", "--progress", str(progress)])

    folder = sandbox / "campaigns" / "alsenan-chalet"
    assert (folder / "v1.json").is_file() and (folder / "v2.json").is_file()
    v2 = json.loads((folder / "v2.json").read_text(encoding="utf-8"))
    assert v2["campaign"]["adjustments"][0]["evidence"] == "180 sent, 0 enquiries"
    # the project and window carry forward without being retyped
    assert v2["project"]["name"] == "Alsenan Chalet"
    assert v2["window"] == "Oct-Dec 2026"


def test_review_can_revise_the_budget(sandbox, tmp_path):
    _new("--budget", "800")
    progress = tmp_path / "w.json"
    progress.write_text("{}")
    cli.main(["review", "--campaign", "alsenan-chalet", "--progress", str(progress),
              "--budget", "500"])
    v2 = json.loads((sandbox / "campaigns" / "alsenan-chalet" / "v2.json").read_text())
    assert v2["budget_kwd"] == 500.0


def test_review_of_unknown_campaign_exits(tmp_path):
    progress = tmp_path / "w.json"
    progress.write_text("{}")
    with pytest.raises(SystemExit, match="no campaign named"):
        cli.main(["review", "--campaign", "nope", "--progress", str(progress)])


# ---- show / list --------------------------------------------------------------
def test_show_reads_the_latest_version(capsys):
    _new("--budget", "800")
    cli.main(["show", "--campaign", "alsenan-chalet"])
    assert "Alsenan Chalet" in capsys.readouterr().out


def test_show_can_resplit_against_a_different_budget(capsys):
    _new("--budget", "800")
    capsys.readouterr()
    cli.main(["show", "--campaign", "alsenan-chalet", "--budget", "1600"])
    out = capsys.readouterr().out
    assert "1,000.000 KWD" in out and "600.000 KWD" in out


def test_list_shows_saved_campaigns(capsys):
    _new()
    capsys.readouterr()
    cli.main(["list"])
    assert "alsenan-chalet" in capsys.readouterr().out


def test_list_with_no_campaigns(capsys):
    cli.main(["list"])
    assert "no campaigns yet" in capsys.readouterr().out
