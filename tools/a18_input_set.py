"""Assemble the inputs for a blind visual pass, and record every one.

    python -m tools.a18_input_set --source <drawings.pdf> \
        --rules data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json \
        --spec data/registry/P7757_PROJECT_RULES.json \
        --subject "the ground-floor open zone" \
        --subject-term PANTRY --subject-term SALON \
        --out data/runs/7757/blind

Every page of the drawing is extracted at its native resolution and
offered to the run through engine.blind_input_contract. The rules and the
specification are offered as PROJECTIONS — the fields a pass is allowed,
hashed as what they are — and never as the documents they came from.

The prohibited files that actually exist in this repository are offered
too, deliberately, so that the manifest records the gates refusing them
by name rather than a promise that they would have. Nothing prohibited is
ever opened: the path gate answers before anything is read.

What this writes is A18_INPUT_MANIFEST.json: the whole input side of a
blind run, sealed and hashed BEFORE the pass runs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

from engine import blind_input_contract as bic

# Files in this repository that a blind pass must never be handed. They
# are offered to the run on purpose, to be refused on the record.
SELF_TEST = (
    ("data/golden/7757/sealed/P7757_area_takeoff_benchmark.pdf",
     bic.SOURCE_DRAWING_IMAGE, "the sealed area take-off, offered as if "
     "it were a drawing"),
    ("data/runs/7757/reconciliation/"
     "P7757_GROUND_OPEN_ZONE_RECONCILIATION.json",
     bic.SHEET_METADATA, "the open-zone reconciliation, offered as if it "
     "were sheet metadata"),
    ("data/registry/OWNER_RULE_REQUESTS.json", bic.PROJECT_SPECIFICATION,
     "the open owner questions, offered as if they were a specification"),
    ("data/runs/7757/round6e_a_export/ROUND6E_A_EXPORT_MANIFEST.json",
     bic.PROJECT_SPECIFICATION, "a previous round's export, offered as if "
     "it were a specification"),
)


def _pages(source: Path, images: Path) -> list:
    """Every page of the drawing, at the resolution it was scanned at."""
    images.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(source)
    out = []
    for n, page in enumerate(doc, start=1):
        embedded = page.get_images(full=True)
        if embedded:
            raw = doc.extract_image(embedded[0][0])
            data, ext = raw["image"], raw["ext"]
            size = (raw["width"], raw["height"])
        else:                                   # a vector sheet: render it
            pix = page.get_pixmap(dpi=200)
            data, ext, size = pix.tobytes("png"), "png", (pix.width,
                                                          pix.height)
        path = images / f"page-{n:02d}.{ext}"
        path.write_bytes(data)
        out.append((n, path, size))
    doc.close()
    return out


def _sheet_metadata(source: Path, pages) -> dict:
    """What the file itself says about which sheet is which.

    On a scanned set that is very little, and saying so is the point: the
    floor of each page is NOT ESTABLISHED, and identifying it is part of
    what the pass is being asked to do rather than something handed to it.
    """
    return {
        "source_file": source.name,
        "pages": [{"page": n, "image": p.name,
                   "pixels": [w, h]} for n, p, (w, h) in pages],
        "page_count": len(pages),
        "text_layer": "NONE",
        "floor_of_each_page": "NOT_ESTABLISHED_FROM_THE_DRAWING",
        "how_it_would_be_established": (
            "by reading the title block on the sheet. This set carries no "
            "text layer, so the title is a picture like everything else"),
    }


def build(*, source, rules_path="", spec_path="", subject="",
          subject_terms=(), run_id="", out_dir="", self_test=True):
    source = Path(source)
    out = Path(out_dir or ".")
    run_id = run_id or f"BLIND-{source.stem}"
    images = out / run_id / "images"
    pages = _pages(source, images)

    run = bic.BlindRun(run_id=run_id, pass_id="A18", subject=subject,
                       floor="NOT_ESTABLISHED_FROM_THE_DRAWING")

    for n, path, (w, h) in pages:
        run.offer(bic.Input(
            input_id=f"IMG-{n:02d}", kind=bic.SOURCE_DRAWING_IMAGE,
            what_it_is=f"page {n} of {source.name}, at the resolution it "
                       f"was scanned at ({w}x{h} px)",
            path=str(path), origin=str(source),
            supplied_by="THE_DRAWING_SET"))

    run.offer(bic.Input(
        input_id="META-01", kind=bic.SHEET_METADATA,
        what_it_is="what the drawing file itself says about its sheets",
        content=_sheet_metadata(source, pages),
        supplied_by="THE_DRAWING_FILE"))

    if rules_path:
        library = json.loads(Path(rules_path).read_text(encoding="utf-8"))
        projection = bic.general_rules(library)
        run.notes["general_rules_withheld"] = {
            "rule_ids": projection["withheld_rule_ids"],
            "why": ("the projected rule still carried benchmark-shaped "
                    "text, so it was dropped on its own rather than "
                    "costing the pass the whole rule book"),
        }
        run.offer(bic.Input(
            input_id="RULES-01", kind=bic.GENERAL_RULE,
            what_it_is=f"{len(projection['rules'])} approved Urban "
                       "Projects general rules, projected to what a rule "
                       "IS",
            content=projection, supplied_by=Path(rules_path).name))

    if spec_path:
        spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
        projection = bic.spec_for_a_blind_pass(
            spec, subject_terms=subject_terms)
        run.notes["specification_withheld"] = {
            "blocks": projection["withheld_block_ids"],
            "why": bic.A_SPEC_ABOUT_THE_SUBJECT_IS_THE_ANSWER,
        }
        run.offer(bic.Input(
            input_id="SPEC-01", kind=bic.PROJECT_SPECIFICATION,
            what_it_is="the project specification, minus the blocks that "
                       "describe the spaces under test",
            content=projection, supplied_by=Path(spec_path).name))

    if self_test:
        for i, (path, claimed_kind, what) in enumerate(SELF_TEST, start=1):
            if not Path(path).exists():
                continue
            run.offer(bic.Input(
                input_id=f"DENIED-{i:02d}", kind=claimed_kind,
                what_it_is=what, path=path,
                supplied_by="THE_CONTRACT_SELF_TEST"))

    run.notes["pass_state"] = "INPUTS_SEALED_PASS_NOT_YET_RUN"
    run.notes["crops"] = (
        "no crop is generated in advance. A crop is cut when the pass "
        "asks to look somewhere, carries the basis that decided its box, "
        "and is appended to this manifest on the run that used it")
    return run


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True)
    ap.add_argument("--rules", default="")
    ap.add_argument("--spec", default="")
    ap.add_argument("--subject", default="")
    ap.add_argument("--subject-term", action="append", default=[])
    ap.add_argument("--run-id", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--no-self-test", action="store_true")
    a = ap.parse_args(argv)

    run = build(source=a.source, rules_path=a.rules, spec_path=a.spec,
                subject=a.subject, subject_terms=tuple(a.subject_term),
                run_id=a.run_id, out_dir=a.out,
                self_test=not a.no_self_test)
    manifest = run.manifest()

    out = Path(a.out or ".")
    for target in (out / bic.MANIFEST_NAME,
                   out / run.run_id / bic.MANIFEST_NAME):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(manifest, indent=2, ensure_ascii=False,
                                     default=str) + "\n", encoding="utf-8")
        print(f"wrote {target}")

    print(json.dumps({
        "pass_id": manifest["pass_id"],
        "run_id": manifest["run_id"],
        "status": manifest["status"],
        "MANIFEST_HASH": manifest["MANIFEST_HASH"][:16],
        "counts": manifest["counts"],
        "admitted": [d["input_id"] for d in
                     manifest["inputs_made_available"]],
        "refused": [{d["input_id"]: d["refused_by"]} for d in
                    manifest["refused_at_the_door"]],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
