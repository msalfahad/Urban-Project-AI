"""Package a frozen blind run for external review. Packaging only.

    python -m tools.a18_review_package --run-dir <frozen run> --out <dir>

Nothing here reads a benchmark, opens a workbook, computes an area or
decides which reading is right. It copies frozen artifacts, checks each
copy against the run's own artifact index so that a reviewer can see
nothing was altered on the way in, and renders contact sheets that put
three pictures side by side:

    LEFT     the source crop the pass was given
    MIDDLE   the frozen pass's stated extent, drawn on that same crop
    RIGHT    the challenging pass's own overlay

Every generated sheet is labelled PRESENTATION_ONLY_NOT_A_FROZEN_AGENT_
ARTIFACT, because a picture the harness drew to help somebody look is not
evidence and must never be mistaken for it.

The caption text is run through the benchmark scanner before it is drawn.
A contact sheet is a thing a human reads while judging, which is exactly
the moment an expected figure must not be on the page.
"""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from engine import benchmark_protection as bp
from engine import export_provenance as prov

PRESENTATION = "PRESENTATION_ONLY_NOT_A_FROZEN_AGENT_ARTIFACT"
ORIGINAL = "ORIGINAL_FROZEN_AGENT_ARTIFACT"

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# The crop tool targets a 1600px long side, so a 1600px row shows every
# panel at its own pixels: nothing is enlarged and nothing is resampled
# down. Printed dimensions and wall strokes survive only at native scale.
# The tallest panel in this set is 4048px. A cap above it means NOTHING
# is resampled in either direction: every panel is shown at the exact
# pixels the pass saw, which is the only way printed dimensions and wall
# strokes stay as readable as they were.
PANEL_H = 4100
GAP = 24
PAD = 28
HEADER_H = 300
FOOTER_H = 96

GROUP = {"PHYSICAL_SPACE": "A_PHYSICAL_SPACES",
         "FUNCTIONAL_ZONE": "B_FUNCTIONAL_ZONES",
         "FLOOR_FINISH_TRADE_ZONE": "C_FLOORING_TRADE_ZONES"}

PASS_B_BOX = (20, 90, 220)


def _font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def _fit(img, height):
    """Downscale to the row height, but NEVER upscale.

    Enlarging a crop adds bytes and no detail. The point of these sheets
    is that walls, labels and printed dimensions stay readable, so a
    panel is shown at its own pixels unless it is too tall for the row.
    """
    img = img.convert("RGB")
    if img.height <= height:
        return img
    w = max(1, round(img.width * height / img.height))
    return img.resize((w, height), Image.LANCZOS)


def _to_crop(px, py, transform):
    """Parent sheet pixel -> crop pixel, inverting the recorded transform."""
    left, top, right, _ = transform["parent_box_lrtb"]
    scale = transform["scale"]
    w = right - left
    return ((py - top) * scale, (w - 1 - (px - left)) * scale)


def _pass_b_panel(crop_path, box, transform):
    """The same crop, with the frozen pass's stated extent drawn on it."""
    img = Image.open(crop_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    corners = [(box[0], box[1]), (box[2], box[1]),
               (box[2], box[3]), (box[0], box[3])]
    pts = [_to_crop(x, y, transform) for x, y in corners]
    draw.line(pts + [pts[0]], fill=PASS_B_BOX, width=9)
    return img


def _safe(lines):
    """Nothing benchmark-shaped goes on a sheet a human judges from."""
    leaks = bp.scan(lines)
    if leaks:
        raise ValueError(
            "a caption carried benchmark-shaped text: "
            + ", ".join(sorted({x.get("matched") or x["key"][:40]
                                for x in leaks})[:4]))
    return lines


def contact_sheet(row, cand, transform, crop, overlay, out_path) -> dict:
    raw = [("LEFT — source crop as A18 received it",
            Image.open(crop), Path(crop).name),
           ("MIDDLE — Pass B stated extent (blue) on the same crop",
            _pass_b_panel(crop, cand["box"], transform),
            f"generated from {Path(crop).name}"),
           ("RIGHT — Pass D challenge overlay",
            Image.open(overlay), Path(overlay).name)]
    panels = [(c, _fit(i, PANEL_H), s) for c, i, s in raw]
    shown = [{"position": c.split(" —")[0],
              "native_pixels": list(i.size),
              "shown_pixels": list(f.size),
              "shown_at_scale": round(f.height / i.height, 3)}
             for (c, i, _s), (_c2, f, _s2) in zip(raw, panels)]
    row_h = max(p[1].height for p in panels)
    width = PAD * 2 + sum(p[1].width for p in panels) + GAP * 2
    height = HEADER_H + row_h + 74 + FOOTER_H
    sheet = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)

    label = cand.get("label_as_drawn", "") or "(no label on the drawing)"
    head = _safe([
        f"{row['candidate_id']}   ·   {row['hypothesis_kind']}",
        f"label as drawn: {label}",
        f"Pass B confidence: {row['pass_b_confidence']}"
        f"   (marker: {row['pass_b_marker']})",
        f"Pass D  A physical space: {row['pass_d_A_PHYSICAL_SPACE']}"
        f"   ·   B functional zone: {row['pass_d_B_FUNCTIONAL_ZONE']}",
        f"Pass D  C floor-finish trade zone: "
        f"{row['pass_d_C_FLOOR_FINISH_TRADE_ZONE']}",
    ])
    draw.text((PAD, 20), head[0], font=_font(58, True), fill=(20, 20, 20))
    y = 96
    for line in head[1:]:
        draw.text((PAD, y), line, font=_font(34), fill=(45, 45, 45))
        y += 44

    x = PAD
    for caption, img, _src in panels:
        sheet.paste(img, (x, HEADER_H))
        draw.text((x, HEADER_H + row_h + 14), caption, font=_font(30),
                  fill=(70, 70, 70))
        draw.rectangle([x - 2, HEADER_H - 2, x + img.width + 1,
                        HEADER_H + img.height + 1],
                       outline=(180, 180, 180), width=2)
        x += img.width + GAP

    foot = (f"{PRESENTATION}   ·   the three panels answer three separate "
            "questions and are not forced to agree   ·   no area, total or "
            "quantity is shown or implied anywhere on this sheet")
    draw.text((PAD, height - FOOTER_H + 16), foot, font=_font(28),
              fill=(120, 40, 40))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return {"file": out_path.name, "pixels": list(sheet.size),
            "panel_resolution": shown,
            "panels_were_upscaled": False,
            "any_panel_downscaled": any(p["shown_at_scale"] < 1.0
                                        for p in shown),
            "panels": [{"position": c.split(" —")[0], "source": s}
                       for c, _i, s in panels],
            "stable_id": row["candidate_id"],
            "provenance": PRESENTATION,
            prov.RAW: prov.raw_sha256(out_path)}


def build(run_dir, out_dir) -> dict:
    run = Path(run_dir)
    pkg = Path(out_dir)
    if pkg.exists():
        shutil.rmtree(pkg)
    frozen = {r["file"]: r[prov.RAW] for group in json.loads(
        (run / "A18_GF_001_ARTIFACT_INDEX.json").read_text())
        ["groups"].values() for r in group}

    entries = []

    def take(src_rel, dest_rel, ids=()):
        src, dest = run / src_rel, pkg / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        digest = prov.raw_sha256(dest)
        expected = frozen.get(src_rel)
        entries.append({
            "package_path": dest_rel,
            "original_frozen_path": f"{run}/{src_rel}",
            "sha256": digest,
            "provenance": ORIGINAL,
            "matches_the_frozen_artifact_index": (
                expected == digest if expected else "NOT_IN_THE_INDEX"),
            "stable_ids": list(ids),
        })

    take("images/page-01.jpeg",
         "01_ORIGINAL_GROUND_FLOOR/page-01.jpeg", ids=("IMG-01",))
    for name in ("A18_GROUND_FLOOR_INTERPRETATION_OVERLAY.png",
                 "A18_VISUAL_ZONE_REGISTER.json",
                 "A18_GF_001_PASS_B_REPORT.md"):
        take(name, f"02_PASS_B/{name}")
    for name in ("A18_PASS_D_WHOLE_FLOOR_OVERLAY.png",
                 "A18_PASS_D_WHOLE_FLOOR_OVERLAY.json",
                 "A18_PASS_D_FALSE_CONFIDENCE_REGISTER.json",
                 "A18_GF_001_PASS_D_REPORT.md"):
        take(name, f"03_PASS_D/{name}")
    for overlay in sorted((run / "overlays_pass_d").iterdir()):
        cid = overlay.stem.replace("overlay_", "")
        take(f"overlays_pass_d/{overlay.name}",
             f"04_LOCAL_CHALLENGES/{overlay.name}", ids=(cid,))

    reg = json.loads(
        (run / "A18_PASS_D_FALSE_CONFIDENCE_REGISTER.json").read_text())
    cands = {c["candidate_id"]: c for c in json.loads(
        (run / "A18_PASS_D_CANDIDATES.json").read_text())["candidates"]}
    transforms = {}
    for row in json.loads(
            (run / "A18_PASS_D_CROP_MANIFEST.json").read_text())["crops"]:
        if row["framing"] == "AS_STATED":
            transforms[row["nlc_id"]] = (row["transform"], row["file"])

    sheets, missing = [], []
    for row in reg["rows"]:
        if row["outcome"] != "CHALLENGED":
            continue
        cid = row["candidate_id"]
        transform, crop_name = transforms[cid]
        crop = run / "crops" / crop_name
        overlay = run / row["overlay"]
        if not crop.exists() or not overlay.exists():
            missing.append({"candidate_id": cid,
                            "crop_present": crop.exists(),
                            "overlay_present": overlay.exists()})
            continue
        dest = (pkg / "05_REVIEW_CONTACT_SHEETS"
                / GROUP[row["hypothesis_kind"]] / f"CS_{cid}.png")
        rec = contact_sheet(row, cands[cid], transform, crop, overlay, dest)
        rec["package_path"] = str(dest.relative_to(pkg))
        rec["group"] = GROUP[row["hypothesis_kind"]]
        sheets.append(rec)
        entries.append({
            "package_path": rec["package_path"],
            "original_frozen_path": None,
            "generated_from": [f"{run}/crops/{crop_name}",
                               f"{run}/{row['overlay']}",
                               f"{run}/A18_PASS_D_CANDIDATES.json"],
            "sha256": rec[prov.RAW],
            "provenance": PRESENTATION,
            "stable_ids": [cid],
        })

    index = {
        "MODEL": "AN_EXTERNAL_REVIEW_PACKAGE_IS_A_COPY_AND_A_CAPTION_V1",
        "run_id": "A18-GF-001",
        "package": pkg.name,
        "what_this_package_is": (
            "frozen artifacts, copied and hash-checked, plus contact sheets "
            "drawn to help a human look at them"),
        "what_this_package_is_not": (
            "not a comparison, not a reconciliation, not a grading. No "
            "benchmark was opened, no workbook was read, no area was "
            "computed, and no reading was declared correct"),
        "two_kinds_of_file": {
            ORIGINAL: "copied byte for byte from the frozen run",
            PRESENTATION: ("drawn by the harness for this package. NOT "
                           "evidence, and never to be read as an agent's "
                           "output"),
        },
        "contact_sheet_panels": {
            "LEFT": "the source crop the pass was given",
            "MIDDLE": ("the frozen Pass B stated extent drawn in blue on "
                       "that same crop, by inverting the crop's recorded "
                       "transform"),
            "RIGHT": "the Pass D challenge overlay, as Pass D drew it"},
        "what_is_printed_on_a_sheet": [
            "the stable candidate id", "the label as drawn, if the pass gave one",
            "the Pass B confidence and its raw marker",
            "the Pass D classification for each of the three questions"],
        "what_is_deliberately_not_printed": [
            "any expected area", "any benchmark area", "any human quantity",
            "any corrected geometry", "any grading verdict"],
        "panel_resolution": {
            "rule": (f"a panel is shown at its own pixels up to a "
                     f"{PANEL_H}px row. Nothing is ever enlarged. A crop "
                     f"taller than that - the large union-box candidates - "
                     f"is reduced to fit, and every sheet records its own "
                     f"per-panel scale in this index"),
            "how_to_get_one_to_one": (
                "re-cut the exact crop from "
                "01_ORIGINAL_GROUND_FLOOR/page-01.jpeg using the frozen "
                "crop manifest's parent_box_lrtb, rotation and scale. The "
                "manifest is A18_PASS_D_CROP_MANIFEST.json in the frozen "
                "run, and its hash is recorded below so a reviewer can tell "
                "they have the right one"),
        },
        "caption_text_was_scanned": (
            "every caption ran through the benchmark scanner before it was "
            "drawn. A contact sheet is read while judging, which is exactly "
            "when an expected figure must not be on the page"),
        "counts": {
            "files": len(entries),
            "original_frozen": sum(1 for e in entries
                                   if e["provenance"] == ORIGINAL),
            "generated_presentation": sum(1 for e in entries
                                          if e["provenance"] == PRESENTATION),
            "contact_sheets_by_group": {
                g: sum(1 for s in sheets if s["group"] == g)
                for g in GROUP.values()},
            "challenged_candidates_in_the_register": sum(
                1 for r in reg["rows"] if r["outcome"] == "CHALLENGED"),
        },
        "integrity": {
            "every_original_matches_the_frozen_index": all(
                e["matches_the_frozen_artifact_index"] is True
                for e in entries if e["provenance"] == ORIGINAL),
            "source_artifacts_were_not_altered": (
                "this tool only reads and copies. The check above compares "
                "each copy against the hash the run recorded before this "
                "package existed"),
        },
        "stable_ids_represented": sorted(
            {i for e in entries for i in e.get("stable_ids", [])}),
        "missing": missing,
        "files": entries,
    }
    index["panel_resolution"]["frozen_crop_manifest"] = {
        "path": f"{run}/A18_PASS_D_CROP_MANIFEST.json",
        "sha256": prov.raw_sha256(run / "A18_PASS_D_CROP_MANIFEST.json"),
    }
    index["contact_sheets"] = sheets
    index["EXTERNAL_REVIEW_INDEX_HASH"] = prov.canonical_sha256(index)
    (pkg / "A18_GF_001_EXTERNAL_REVIEW_INDEX.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return index


def zip_package(pkg_dir, zip_path) -> dict:
    pkg = Path(pkg_dir)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(pkg.rglob("*")):
            if path.is_file():
                zf.write(path, str(Path(pkg.name) / path.relative_to(pkg)))
    return {"zip": str(zip_path),
            "bytes": Path(zip_path).stat().st_size,
            prov.RAW: prov.raw_sha256(zip_path)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--zip", default="")
    a = ap.parse_args(argv)
    index = build(a.run_dir, a.out)
    result = {"counts": index["counts"],
              "integrity": index["integrity"][
                  "every_original_matches_the_frozen_index"],
              "missing": index["missing"],
              "EXTERNAL_REVIEW_INDEX_HASH":
                  index["EXTERNAL_REVIEW_INDEX_HASH"]}
    if a.zip:
        result["package"] = zip_package(a.out, a.zip)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
