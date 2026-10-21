"""Cut the local crops a frozen pass asked for, and record how to get back.

    python -m tools.a18_local_crops --parent <page image> \
        --register <NEEDS_LOCAL_CROP register>.json --out <dir>

Every crop here is cut at a location the FROZEN pass named. The harness
chooses no location: it chooses only the padding and the zoom, and it
chooses them by one rule applied to every record, so that no zone is
framed more helpfully than another.

Each requested location is cut TWICE, because a coordinate pair written
by a pass that worked in a rotated frame can be a reading in either
frame, and deciding which on the pass's behalf would be the harness
interpreting:

    AS_STATED                the numbers read as parent coordinates
    VIA_RECORDED_TRANSFORM   the numbers read in the rotated frame and
                             mapped through the transform the pass
                             recorded

Which one lands on the described feature is for the reading pass to say.

Every crop carries the transform back to parent coordinates, so anything
seen in a crop can be pointed at on the sheet.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from engine import blind_input_contract as bic
from engine import export_provenance as prov

AS_STATED = "AS_STATED"
VIA_TRANSFORM = "VIA_RECORDED_TRANSFORM"

# One rule for every record, so that no zone is framed more kindly.
PAD_FRACTION = 0.15
PAD_MIN_PX = 150
TARGET_LONG_SIDE = 1600
MAX_SCALE = 6.0
ROTATION = "90_CCW"


def pad_box(box, size) -> tuple:
    left, top, right, bottom = box
    pad = max(PAD_MIN_PX, round(PAD_FRACTION * max(right - left,
                                                   bottom - top)))
    return (max(0, left - pad), max(0, top - pad),
            min(size[0], right + pad), min(size[1], bottom + pad))


def via_transform(box, size) -> tuple:
    """Read the numbers as rotated-frame and map them with the pass's rule.

    orig_x = 4671 - rot_y, orig_y = rot_x, i.e. the pair (a, b) becomes
    (width - 1 - b, a).
    """
    left, top, right, bottom = box
    w = size[0]
    xs = sorted((w - 1 - top, w - 1 - bottom))
    ys = sorted((left, right))
    return (max(0, xs[0]), max(0, ys[0]),
            min(w, xs[1]), min(size[1], ys[1]))


def scale_for(box) -> float:
    long_side = max(box[2] - box[0], box[3] - box[1]) or 1
    return round(min(MAX_SCALE, max(1.0, TARGET_LONG_SIDE / long_side)), 3)


def to_parent(box, scale) -> dict:
    """How to turn a pixel in this crop back into a sheet coordinate.

    The crop is cut from the parent at `box`, then rotated 90 degrees
    counter-clockwise, then scaled. PIL's 90 CCW maps a source pixel
    (x, y) of a W x H image to (y, W - 1 - x). Inverting that, and then
    the crop offset:

        src_x = W - 1 - round(cy / scale)
        src_y = round(cx / scale)
        sheet = (left + src_x, top + src_y)
    """
    left, top, right, bottom = box
    return {
        "parent_box_lrtb": [left, top, right, bottom],
        "rotation": ROTATION,
        "scale": scale,
        "crop_pixel_to_sheet": (
            "src_x = (right - left) - 1 - round(cy / scale); "
            "src_y = round(cx / scale); "
            "sheet_x = left + src_x; sheet_y = top + src_y"),
        "parent_width_used_for_W": right - left,
    }


def _check_inverse() -> None:
    """The transform is verified, not asserted."""
    img = Image.new("L", (7, 3), 0)
    img.putpixel((5, 1), 255)
    rot = img.rotate(90, expand=True)
    found = [(x, y) for y in range(rot.size[1]) for x in range(rot.size[0])
             if rot.getpixel((x, y)) == 255]
    cx, cy = found[0]
    assert (7 - 1 - cy, cx) == (5, 1), (found, "rotation inverse is wrong")


def build(parent, register, out_dir) -> dict:
    _check_inverse()
    img = Image.open(parent)
    reg = json.loads(Path(register).read_text(encoding="utf-8"))
    out = Path(out_dir)
    (out / "crops").mkdir(parents=True, exist_ok=True)

    run = bic.BlindRun(run_id=reg.get("run_id", ""), pass_id="A18")
    rows = []
    for rec in reg["needs_local_crop"]:
        stated = tuple(rec["coordinates_as_stated"]["box"])
        for framing, raw in ((AS_STATED, stated),
                             (VIA_TRANSFORM, via_transform(stated,
                                                           img.size))):
            box = pad_box(raw, img.size)
            if box[2] - box[0] < 8 or box[3] - box[1] < 8:
                continue
            scale = scale_for(box)
            cut = img.crop(box).rotate(90, expand=True)
            if scale != 1.0:
                cut = cut.resize((round(cut.size[0] * scale),
                                  round(cut.size[1] * scale)),
                                 Image.LANCZOS)
            name = f"{rec['nlc_id']}_{framing}.png"
            path = out / "crops" / name
            cut.convert("L").save(path)
            decision = run.offer(bic.Input(
                input_id=name.rsplit(".", 1)[0], kind=bic.LOCAL_CROP,
                what_it_is=f"{rec['nlc_id']} framed {framing}",
                path=str(path), derived_from="IMG-01",
                crop_basis=bic.CROP_REQUESTED_BY_THE_AGENT,
                crop_box_px=box, supplied_by="THE_FROZEN_PASS_B_REQUEST"))
            rows.append({
                "crop_id": name.rsplit(".", 1)[0],
                "file": name,
                "nlc_id": rec["nlc_id"],
                "framing": framing,
                "requested_because": rec["REASON_FOR_LOCAL_CROP"],
                "coordinates_as_stated_by_pass_b":
                    rec["coordinates_as_stated"],
                "box_before_padding": list(raw),
                "transform": to_parent(box, scale),
                "pixels": list(cut.size),
                "crop_basis": bic.CROP_REQUESTED_BY_THE_AGENT,
                "gate": decision.status,
                prov.RAW: prov.raw_sha256(path),
            })

    manifest = {
        "MODEL": "A_LOCAL_CROP_CARRIES_ITS_WAY_BACK_V1",
        "run_id": run.run_id,
        "parent_image": {"file": Path(parent).name,
                         "pixels": list(img.size),
                         prov.RAW: prov.raw_sha256(parent)},
        "framing_rule": {
            "padding": f"max({PAD_MIN_PX}px, {PAD_FRACTION} x the longer "
                       "side of the requested box)",
            "zoom": f"scale to a {TARGET_LONG_SIDE}px long side, capped at "
                    f"x{MAX_SCALE}",
            "rotation": ROTATION,
            "why_one_rule": ("the harness chooses padding and zoom, not "
                             "locations, and it applies the same rule to "
                             "every record so that no zone is framed more "
                             "helpfully than another")},
        "two_framings": {
            AS_STATED: "the numbers read as parent coordinates",
            VIA_TRANSFORM: ("the numbers read in the rotated frame and "
                            "mapped with orig_x = W - 1 - rot_y, "
                            "orig_y = rot_x"),
            "why": ("a coordinate written by a pass that worked in a "
                    "rotated frame can be a reading in either frame. "
                    "Deciding which, on its behalf, would be the harness "
                    "interpreting the drawing")},
        "crops": rows,
        "count": len(rows),
        "all_gates_passed": all(r["gate"] == bic.ADMITTED for r in rows),
    }
    manifest["CROP_MANIFEST_HASH"] = prov.canonical_sha256(manifest)
    (out / "A18_PASS_C_CROP_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parent", required=True)
    ap.add_argument("--register", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    man = build(a.parent, a.register, a.out)
    print(json.dumps({"crops": man["count"],
                      "all_gates_passed": man["all_gates_passed"],
                      "CROP_MANIFEST_HASH":
                          man["CROP_MANIFEST_HASH"][:16]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
