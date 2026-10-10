"""Read AR-00's vector-outline text once, and cache every answer.

Separate from the pipeline on purpose. The pipeline must be re-runnable for
free and offline; a vision pass is neither, so it runs here, writes its
answers to a cache keyed on each crop's own bytes, and the pipeline then
reads the cache. A re-run costs nothing and returns the same strings.

The cache lives under data/ and is gitignored: these are the client's room
names and printed dimensions.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from engine import document_reader as dr        # noqa: E402
from engine import glyph_text as gt             # noqa: E402

PDF = "data/golden/23010/inputs/AR-00_MAR2023.pdf"
CACHE = "data/golden/23010/doc_read_cache"
KEY = ".secrets/anthropic.key"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", default=PDF)
    ap.add_argument("--cache", default=CACHE)
    ap.add_argument("--limit", type=int, default=0,
                    help="read at most this many runs (0 = all located)")
    ap.add_argument("--model", default="")
    ap.add_argument("--dry-run", action="store_true",
                    help="locate and report only; make no model call")
    a = ap.parse_args()

    located = gt.locate(a.pdf)
    runs = located.runs[:a.limit] if a.limit else located.runs
    print(f"located {len(located.runs)} text runs; offering {len(runs)}")

    if a.dry_run:
        print(json.dumps(located.record(limit=0), indent=1)[:1200])
        return

    if not os.environ.get("ANTHROPIC_API_KEY") and pathlib.Path(KEY).exists():
        os.environ["ANTHROPIC_API_KEY"] = pathlib.Path(
            KEY).read_text().strip()

    from agents.base import BEST, vision
    model = a.model or BEST
    print(f"reader: {model}")

    t = time.time()
    rep = dr.read_runs(
        a.pdf, runs, reader=vision(model=model), cache_dir=a.cache,
        drawing_id="AR-00", revision="MAR2023")
    rec = rep.record()
    print(f"took {time.time() - t:.0f}s  calls={rec['model_calls_made']} "
          f"cached={rec['model_calls_served_from_cache']} "
          f"empty={rec['runs_with_no_readable_text']}")
    print(f"dimensions={rec['printed_dimensions']} "
          f"(parsed {rec['printed_dimensions_parsed']})  "
          f"labels={rec['room_labels']}  other={rec['other_text']}")
    if rec["read_failures"]:
        print("failures:", json.dumps(rec["read_failures"][:5], indent=1))
    print("labels seen:", json.dumps(rec["by_label_text"],
                                     ensure_ascii=False)[:800])


if __name__ == "__main__":
    main()
