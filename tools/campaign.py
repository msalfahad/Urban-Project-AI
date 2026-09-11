"""Run and review a project marketing campaign (A17 + E21).

The campaign is a file you work against, not a one-off answer. Each review
writes a new version beside the last, so the record of what you changed and why
survives.

    campaigns/<slug>/v1.json   the opening campaign
    campaigns/<slug>/v2.json   after the first review
    ...

Usage:
    python -m tools.campaign new --project "Alsenan Chalet" --type chalet \\
        --location Khairan --stage foundations --window "Oct-Dec 2026" \\
        --objective "more chalet enquiries" --channels instagram,whatsapp \\
        --budget 1200 --usp "black structure specialist" --photo alsenan_render.jpg

    python -m tools.campaign show --campaign alsenan-chalet
    python -m tools.campaign review --campaign alsenan-chalet --progress week1.json

Live runs need ANTHROPIC_API_KEY (or an `ant auth login` profile).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path

from agents.a17_campaign.agent import run as a17
from agents.a17_campaign.schema import CampaignInput, Project
from engine.campaign import split_budget

ROOT = Path(__file__).resolve().parent.parent
CAMPAIGNS = ROOT / "campaigns"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        raise SystemExit("project name must contain at least one letter or digit")
    return slug


def versions(slug: str) -> list[Path]:
    folder = CAMPAIGNS / slug
    if not folder.is_dir():
        return []
    return sorted(folder.glob("v*.json"), key=lambda p: int(p.stem[1:]))


def load_latest(slug: str) -> dict:
    found = versions(slug)
    if not found:
        raise SystemExit(f"no campaign named {slug!r} — run `new` first")
    return json.loads(found[-1].read_text(encoding="utf-8"))


def save(slug: str, record: dict) -> Path:
    folder = CAMPAIGNS / slug
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"v{len(versions(slug)) + 1}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def show(record: dict) -> None:
    campaign = record["campaign"]
    budget = record.get("budget_kwd", 0.0)

    print(f"\n{record['project']['name']} — {record['window']}")
    print(f"Objective: {campaign['objective']}\n")

    if campaign.get("phases"):
        print("Phases")
        for phase in campaign["phases"]:
            weeks = phase.get("weeks", "?")
            print(f"  wk {weeks:<8} {phase.get('phase', '')} — {phase.get('focus', '')}")
        print()

    weights = campaign["channel_weights"]
    if budget:
        print(f"Budget — {budget:g} KWD")
        for channel, amount in sorted(
            split_budget(budget, weights).items(), key=lambda kv: -kv[1]
        ):
            print(f"  {channel:<12} {amount:>10,.3f} KWD   (weight {weights[channel]:g})")
    else:
        print("Channel weights (no budget set — pass --budget to see the split)")
        for channel, weight in sorted(weights.items(), key=lambda kv: -kv[1]):
            print(f"  {channel:<12} weight {weight:g}")
    print()

    print("Schedule")
    for item in campaign["schedule"]:
        asset = item.get("asset", "")
        print(f"  wk {str(item['week']):<4} {item['channel']:<10} {item.get('type', ''):<9} "
              f"{item['topic']}")
        if asset:
            print(f"{'':<27}asset: {asset}")
    print()

    if campaign.get("kpis"):
        print("KPIs")
        for kpi in campaign["kpis"]:
            print(f"  {kpi.get('metric', '')}: {kpi.get('target', '')}"
                  f"  ({kpi.get('how_measured', '')})")
        print()

    if campaign.get("adjustments"):
        print("Adjustments this review")
        for change in campaign["adjustments"]:
            print(f"  - {change['change']}")
            print(f"      why: {change['evidence']}")
        print()

    review = campaign.get("review", {})
    if review:
        print(f"Next review: {review.get('next_review', '?')} ({review.get('cadence', '')})")
        for item in review.get("bring", []):
            print(f"  bring: {item}")
    if campaign.get("notes"):
        print(f"\nNotes: {campaign['notes']}")
    print()


def cmd_new(args: argparse.Namespace) -> None:
    project = Project(
        name=args.project,
        type=args.type or "",
        location=args.location or "",
        stage=args.stage or "",
        usps=args.usp or [],
        photo_refs=args.photo or [],
    )
    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8")) if args.evidence else {}
    channels = [c.strip() for c in args.channels.split(",") if c.strip()]

    campaign = a17(CampaignInput(
        project=project,
        window=args.window,
        objective=args.objective or "",
        channels=channels,
        evidence=evidence,
    ))

    slug = slugify(args.project)
    record = {
        "project": asdict(project),
        "window": args.window,
        "objective": args.objective or "",
        "channels": channels,
        "budget_kwd": args.budget,
        "campaign": asdict(campaign),
    }
    path = save(slug, record)
    show(record)
    print(f"saved {path.relative_to(ROOT)}  (campaign id: {slug})")


def cmd_review(args: argparse.Namespace) -> None:
    slug = args.campaign
    previous = load_latest(slug)
    progress = json.loads(Path(args.progress).read_text(encoding="utf-8"))

    # The model sees the campaign it is correcting alongside what happened.
    progress = {"campaign_so_far": previous["campaign"], "results": progress}
    project = Project(**previous["project"])

    campaign = a17(CampaignInput(
        project=project,
        window=previous["window"],
        objective=previous.get("objective", ""),
        channels=previous.get("channels", []),
        progress=progress,
    ))

    record = dict(previous)
    record["campaign"] = asdict(campaign)
    if args.budget is not None:
        record["budget_kwd"] = args.budget
    path = save(slug, record)
    show(record)
    print(f"saved {path.relative_to(ROOT)}  (was {len(versions(slug)) - 1} version(s))")


def cmd_show(args: argparse.Namespace) -> None:
    record = load_latest(args.campaign)
    if args.budget is not None:
        record["budget_kwd"] = args.budget
    show(record)


def cmd_list(_: argparse.Namespace) -> None:
    if not CAMPAIGNS.is_dir():
        print("no campaigns yet")
        return
    for folder in sorted(CAMPAIGNS.iterdir()):
        if folder.is_dir() and (found := versions(folder.name)):
            record = json.loads(found[-1].read_text(encoding="utf-8"))
            print(f"{folder.name:<28} v{len(found)}  {record['window']:<14} "
                  f"{record['campaign']['objective'][:50]}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="campaign", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="plan a new campaign for a project")
    new.add_argument("--project", required=True, help="project name")
    new.add_argument("--window", required=True, help='e.g. "Oct-Dec 2026"')
    new.add_argument("--type", help="villa | chalet | apartment | fitout")
    new.add_argument("--location")
    new.add_argument("--stage", help="design | foundations | structure | finishes | handover")
    new.add_argument("--objective")
    new.add_argument("--channels", default="instagram,whatsapp")
    new.add_argument("--budget", type=float, default=0.0, help="total KWD for the window")
    new.add_argument("--usp", action="append", help="repeatable")
    new.add_argument("--photo", action="append", help="existing asset, repeatable")
    new.add_argument("--evidence", help="JSON file of A14's Instagram analysis")
    new.set_defaults(func=cmd_new)

    review = sub.add_parser("review", help="correct a campaign from what actually happened")
    review.add_argument("--campaign", required=True, help="campaign id (the slug)")
    review.add_argument("--progress", required=True, help="JSON file of what was published + results")
    review.add_argument("--budget", type=float, help="revise the budget")
    review.set_defaults(func=cmd_review)

    shown = sub.add_parser("show", help="print the latest version of a campaign")
    shown.add_argument("--campaign", required=True)
    shown.add_argument("--budget", type=float, help="re-split against a different budget")
    shown.set_defaults(func=cmd_show)

    sub.add_parser("list", help="list saved campaigns").set_defaults(func=cmd_list)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
