"""E1.2 — record a cold visual pass's answers into its frozen register.

    python -m tools.e1_3_record_visual --stage v1 --out <dir> \
        --answers a.json [--answers b.json ...]

The challenger answers in prose and vocabulary, never in geometry, so
every answer is screened on the way in: a coordinate pair or a measured
quantity in a returned observation is refused and recorded as refused,
because the one thing this pass may not do is move the drawing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine import export_provenance as prov
from engine import visual_challenger_v2 as vc

REGISTER = {"v1": "E1_3_VISUAL_V1_REGISTER.json",
            "v2": "E1_3_VISUAL_V2_REGISTER.json"}


def _flat(row) -> str:
    return json.dumps(row, ensure_ascii=False)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", required=True, choices=("v1", "v2"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--answers", action="append", required=True)
    a = ap.parse_args(argv)

    path = Path(a.out) / REGISTER[a.stage]
    body = json.loads(path.read_text(encoding="utf-8"))
    rows, refused = [], []
    for src in a.answers:
        for row in json.loads(Path(src).read_text(encoding="utf-8")):
            problems = vc.screen_return(_flat(row))
            if a.stage == "v2":
                bad = [s for s in row.get("statuses", ())
                       if s not in vc.V2_STATUSES]
                if bad:
                    problems.append(f"NOT_A_V2_STATUS:{sorted(bad)}")
            else:
                from engine import edge_relation as edge
                bad = [e.get("EDGE_RELATION")
                       for e in (row.get("EDGES") or ())
                       if isinstance(e, dict)
                       and not edge.relation_is_valid(e.get("EDGE_RELATION"))]
                if bad:
                    problems.append(f"NOT_AN_EDGE_RELATION:{sorted(bad)}")
            if problems:
                refused.append({"candidate_id": row.get("candidate_id"),
                                "refused_because": problems,
                                "why": vc.THE_CHALLENGER_MAY_NOT_MOVE_A_COORDINATE})
                continue
            row["ANSWER_SHA256"] = prov.canonical_sha256(row)
            row["source_file"] = src
            rows.append(row)

    body["answers"] = rows
    body["answers_refused_on_the_way_in"] = refused
    body["status"] = "FROZEN"
    body["counts"] = {"answered": len(rows), "refused": len(refused)}
    body.pop(f"{REGISTER[a.stage].split('.')[0]}_HASH", None)
    key = f"{REGISTER[a.stage].split('.')[0]}_HASH"
    body[key] = prov.canonical_sha256(body)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False,
                               default=str) + "\n", encoding="utf-8")
    print(json.dumps({"stage": a.stage, "answered": len(rows),
                      "refused": len(refused),
                      "register": str(path),
                      "REGISTER_SHA256": prov.raw_sha256(path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
