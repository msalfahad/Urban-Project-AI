"""Design and render an Instagram grid (A16 grid mode + social/render).

    python -m tools.grid plan   --account @upc.kw --out out/launch \\
        --service "villas" --service "black structure" --fact "15-year structure warranty" \\
        [--photos photos.json] [--theme light] [--lang ar --lang en] [--notes "..."]

    python -m tools.grid render --out out/launch [--photos-dir photos/] [--no-png]

`plan` calls A16, saves `brief.json` + `grid.json`, and prints the designer's
questions for you. Answer them by editing `grid.json` (or re-running `plan`
with more facts/photos), then `render` draws every tile, a 3-wide preview
sheet, and `captions.md` in posting order — without another model call.

`photos.json` is a list of {"ref": "file.jpg", "description": "..."}; put the
files themselves in `--photos-dir` when rendering. Live `plan` needs
ANTHROPIC_API_KEY; PNGs need Chromium (see documents/render.py).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from agents.a16_post_designer.agent import run_grid
from agents.a16_post_designer.schema import GridBrief, GridDesign, Photo
from social.render import render_grid


def load_brief(path: Path) -> GridBrief:
    j = json.loads(path.read_text(encoding="utf-8"))
    j["photos"] = [Photo(**p) for p in j.get("photos", [])]
    brief = GridBrief(**j)
    brief.validate()
    return brief


def load_design(path: Path, brief: GridBrief) -> GridDesign:
    return GridDesign.from_dict(
        json.loads(path.read_text(encoding="utf-8")),
        expected_tiles=brief.tiles,
        inventory={p.ref for p in brief.photos} if brief.photos else None,
        languages=brief.languages,
    )


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(asdict(obj), ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_plan(args: argparse.Namespace) -> None:
    photos = []
    if args.photos:
        photos = [Photo(**p) for p in json.loads(Path(args.photos).read_text(encoding="utf-8"))]
    brief = GridBrief(
        account=args.account, purpose=args.purpose, tiles=args.tiles, theme=args.theme,
        languages=args.lang or ["ar", "en"], services=args.service or [], facts=args.fact or [],
        photos=photos, owner_notes=args.notes or "",
    )
    brief.validate()
    design = run_grid(brief)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    _dump(out / "brief.json", brief)
    _dump(out / "grid.json", design)
    print(f"saved {out / 'brief.json'}\nsaved {out / 'grid.json'}\n")

    print("Tiles")
    for t in sorted(design.tiles, key=lambda t: t.position):
        photo = t.photo_ref or (f"needs: {t.photo_needs}" if t.photo_needs else "—")
        print(f"  {t.position:02d} {t.role:<4} {t.layout:<14} {t.headline_ar}  /  {t.headline_en}")
        if photo != "—":
            print(f"{'':<25}photo: {photo}")
    if design.questions:
        print("\nThe designer asks:")
        for i, q in enumerate(design.questions, 1):
            print(f"  {i}. {q}")


def cmd_render(args: argparse.Namespace) -> None:
    out = Path(args.out)
    brief = load_brief(out / "brief.json")
    design = load_design(out / "grid.json", brief)
    photos_dir = Path(args.photos_dir) if args.photos_dir else None
    result = render_grid(design, brief, out, photos_dir=photos_dir, png=not args.no_png)
    for p in result["png"] or result["html"]:
        print(f"tile  {p}")
    if result["sheet"]:
        print(f"sheet {result['sheet']}")
    print(f"copy  {result['captions']}")
    missing = [t for t in design.tiles if t.layout in ("photo_full", "split") and not (
        photos_dir and t.photo_ref and (photos_dir / t.photo_ref).is_file())]
    if missing:
        print("\nphotos still needed:")
        for t in sorted(missing, key=lambda t: t.position):
            print(f"  tile {t.position:02d}: {t.photo_ref or t.photo_needs}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="grid", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan", help="design the grid with A16")
    p.add_argument("--account", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--purpose", default="launch")
    p.add_argument("--tiles", type=int, default=9)
    p.add_argument("--theme", choices=["light", "dark"], default="light")
    p.add_argument("--lang", action="append", help="repeatable; default ar, en")
    p.add_argument("--service", action="append")
    p.add_argument("--fact", action="append", help="a verifiable claim, repeatable")
    p.add_argument("--photos", help="JSON inventory of photos you will supply")
    p.add_argument("--notes")
    p.set_defaults(func=cmd_plan)

    r = sub.add_parser("render", help="draw the tiles from grid.json")
    r.add_argument("--out", required=True, help="folder holding brief.json + grid.json")
    r.add_argument("--photos-dir")
    r.add_argument("--no-png", action="store_true")
    r.set_defaults(func=cmd_render)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
