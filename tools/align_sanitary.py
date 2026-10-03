"""Register the sanitary set, align it to the plan, and ask the pantry.

    python -m tools.align_sanitary --decode-json <arch decode> \
        --sanitary <sanitary.pdf> --supervised <floors.json> \
        --out data/runs/7757/sanitary/P7757_SANITARY_ALIGNMENT.json

The architectural decode is never touched. The sanitary PDF becomes its
own DESIGN_SANITARY source, with its own hash and its own coordinates,
and the only thing that joins them is a TESTED alignment: the long walls
of the ground-floor plan against the long lines of the sheet, at a scale
that has to win rather than merely lead.

What comes out is evidence, not a quantity. Round 6E-A stays frozen.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import floor_register as freg
from engine import pantry_alignment as palign
from engine import sanitary_source as ss
from engine import semantic_seed as seeds_mod
from tools import run_round6d as r6d

LONG_WALL_MM = ss.LONG_WALL_MM


def _ground_walls(rep, region_id: str):
    """The CENTRELINES of the long walls of one plan, per axis."""
    walls = [w for wr in rep.walls if wr.region_id == region_id
             for w in wr.walls]

    def span(w):
        return max((hi - lo) for lo, hi in w.drawn_mm) if w.drawn_mm else 0.0

    long_v = sorted({round((w.face_a_mm + w.face_b_mm) / 2.0, 1)
                     for w in walls
                     if w.axis == "V" and span(w) > LONG_WALL_MM})
    long_h = sorted({round((w.face_a_mm + w.face_b_mm) / 2.0, 1)
                     for w in walls
                     if w.axis == "H" and span(w) > LONG_WALL_MM})
    face_v = sorted({round(f, 1) for w in walls if w.axis == "V"
                     for f in (w.face_a_mm, w.face_b_mm)})
    face_h = sorted({round(f, 1) for w in walls if w.axis == "H"
                     for f in (w.face_a_mm, w.face_b_mm)})
    return long_v, long_h, face_v, face_h


def run(decode_json: str, sanitary_pdf: str, *, supervised_json: str = "",
        region_id: str = "") -> dict:
    from shapely.wkt import loads

    decode = json.loads(Path(decode_json).read_text(encoding="utf-8"))
    nd = adapter.normalize(decode, source_file="P7757_ARCHITECTURAL.dwg",
                           source_hash="7f61f3acdd62d62d")
    rep = measure.measure(nd, cprofile.build(nd),
                          semantic=seeds_mod.classify(nd.texts))
    supervised = {}
    if supervised_json and Path(supervised_json).exists():
        supervised = json.loads(Path(supervised_json).read_text(
            encoding="utf-8")).get("assignments", {})
    built = freg.assemble(nd, rep, supervised=supervised)
    rows = r6d._faces(rep, built["rows"])

    # the GROUND floor plan is what a ground floor drainage plan draws
    floor_of = built["floor_of"]
    ground = region_id or next(
        (r for r, f in sorted(floor_of.items()) if f == "GROUND"), "")
    long_v, long_h, face_v, face_h = _ground_walls(rep, ground)

    src = ss.read(sanitary_pdf)
    pages = []
    best = None
    for page in src.pages:
        al = ss.align(page, wall_x=long_v, wall_y=long_h)
        pages.append({"page": page.record(), "alignment": al.record()})
        if al.status == ss.ESTABLISHED and (
                best is None or al.matched_x + al.matched_y >
                best[1].matched_x + best[1].matched_y):
            best = (page, al)

    polygons = []
    for r in rep.rows:
        if r.region_id != ground or r.clear is None:
            continue
        try:
            polygons.append((r.space_id, loads(r.clear.polygon_wkt)))
        except Exception:      # noqa: BLE001
            continue

    evidence = {"status": ss.NOT_ESTABLISHED, "rows": []}
    symbols = []
    if best is not None:
        page, al = best
        evidence = ss.drainage_evidence(page, al, polygons=polygons,
                                        arch_v=face_v, arch_h=face_h)
        symbols = ss.fixtures(page, al)

    # §14 the pantry label stands somewhere even when it names no
    # space, and "is there drainage here" is a question about a place.
    neighbourhood = []
    if best is not None:
        page, al = best
        for v in built["register"].labels:
            text = (getattr(v, "text", "") or "").upper()
            if "PANTRY" not in text and "KITCHEN" not in text:
                continue
            for radius in (1500.0, 3000.0):
                row = ss.evidence_near(page, al, getattr(v, "x", 0.0),
                                       getattr(v, "y", 0.0),
                                       radius_mm=radius,
                                       arch_v=face_v, arch_h=face_h)
                row["label"] = getattr(v, "text", "")
                row["drawing_region_id"] = getattr(v, "region_id", "")
                neighbourhood.append(row)

    # the pantry, asked of both representations at once
    alignment_rows = palign.align(
        rows, built["register"].labels, fittings=built["linings"],
        wall_bands=[w for wr in rep.walls for w in wr.walls],
        sources=[palign.Source(
            name=src.name, kind=ss.DESIGN_SANITARY,
            status=(palign.SANITARY_READ if best is not None
                    else palign.SANITARY_UNREADABLE),
            what_it_is=(f"{len(src.pages)} vector pages, sha256 "
                        f"{src.sha256[:16]}; page "
                        f"{best[0].index if best else '-'} aligns to the "
                        "ground floor"),
            why_it_could_not_be_read=(
                "" if best is not None else
                "no page aligned to the ground-floor plan well enough "
                "to place anything"))],
        sanitary_fixtures=symbols,
        floor_of=floor_of)

    out = {
        "model": ss.MODEL,
        "SANITARY_SOURCE_HASH": ss.model_hash(),
        "architectural_source": {
            "file": "P7757_ARCHITECTURAL.dwg",
            "decode": decode_json,
            "representation": ss.DESIGN_ARCHITECTURAL,
            "untouched": True,
        },
        "sanitary_source": src.record(),
        "ground_floor_region": ground,
        "long_walls_used": {"vertical": len(long_v),
                            "horizontal": len(long_h)},
        "pages": pages,
        "drainage_evidence": evidence,
        "around_the_pantry_and_the_kitchen": neighbourhood,
        "symbols_found": len(symbols),
        "pantry": alignment_rows,
        "frozen_parameters": ss.frozen_parameters(),
        "what_this_is_not": (
            "not a quantity, not a fixture schedule and not a tiled "
            "wall. Round 6E-A stays frozen: this is evidence for the "
            "pantry question and nothing is measured from it"),
    }
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--decode-json", required=True)
    ap.add_argument("--sanitary", required=True)
    ap.add_argument("--supervised", default="")
    ap.add_argument("--region", default="")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    rec = run(a.decode_json, a.sanitary, supervised_json=a.supervised,
              region_id=a.region)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(rec, indent=2,
                                          ensure_ascii=False,
                                          default=str) + "\n",
                               encoding="utf-8")
        print(f"wrote {a.out}")
    print(json.dumps({
        "sanitary_source": rec["sanitary_source"]["source"],
        "RAW_FILE_SHA256": rec["sanitary_source"]["RAW_FILE_SHA256"][:16],
        "pages": [{"page": p["page"]["page"],
                   "status": p["alignment"]["status"],
                   "scale_mm_per_pt": p["alignment"]["scale_mm_per_pt"],
                   "matched": [p["alignment"]["long_walls_matched_x"],
                               p["alignment"]["long_walls_matched_y"]]}
                  for p in rec["pages"]],
        "drainage_rows": len(rec["drainage_evidence"]["rows"]),
        "pantry_status": [r["status"] for r in rec["pantry"]["rows"]],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
