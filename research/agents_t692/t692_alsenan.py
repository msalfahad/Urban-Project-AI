"""T-692 runner on the development villa: master 1.68.0 + the V3.0.67 line index + the DXF keyword census.

  --write : rebuild out/T692_CENSUS.json, out/T692_CENSUS.csv and out/DXF_KEYWORD_COUNTS.json (needs the private DXF copies
            under <checkout>/.work/private; counts only are written)
  --check : rebuild the census from the committed DXF counts and compare it with out/T692_CENSUS.json (no drawing needed)
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t692_census as C  # noqa: E402

MASTER = ROOT / "rules" / "coverage" / "BOQ_FAMILY_MASTER_1.68.0.json"
INDEX = ROOT / "research" / "agents_t682" / "out" / "LINE_INDEX_V3_0_67.json"
OUT = HERE / "out"
DXF_COUNTS = OUT / "DXF_KEYWORD_COUNTS.json"


def private_dir() -> Path:
    # the worktree is <checkout>/.work/task-T-692; the private folder is <checkout>/.work/private
    return ROOT.parent / "private"


def run(dxf_counts: dict) -> dict:
    master = C.load(MASTER)
    index = C.load(INDEX)["lines"]
    res = C.build(master, index, dxf_hits=dxf_counts["hits"])
    res["dxf_census"] = {"texts": dxf_counts["texts"], "files": {k: v["texts"] for k, v in dxf_counts["files"].items()},
                         "limitation": "SHX-drawn Arabic does not decode: a 0 is no decodable note, never proof of absence"}
    res["inputs"] = {"master": str(MASTER.relative_to(ROOT)), "index": str(INDEX.relative_to(ROOT))}
    return res


def write_csv(res: dict, path: Path) -> None:
    cols = ["order", "code", "item", "unit", "set", "capability", "candidate_state", "class", "band", "trade_step",
            "scale_bucket", "drawing_source", "rule_or_gap", "host_module", "dxf_keyword_group", "dxf_text_hits"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in res["rows"]:
            w.writerow(r)


def main(argv: list[str]) -> int:
    if "--write" in argv:
        import t692_dxf_census as D

        p = private_dir()
        dxf = D.census([p / "ST7757.dxf", p / "p7757" / "P7757.dxf"])
        OUT.mkdir(exist_ok=True)
        dxf["files"] = {("ST" if k.startswith("ST") else "ARCH") + "_dxf": v for k, v in dxf["files"].items()}
        DXF_COUNTS.write_text(json.dumps(dxf, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        res = run(dxf)
        (OUT / "T692_CENSUS.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        write_csv(res, OUT / "T692_CENSUS.csv")
        print(json.dumps({k: res[k] for k in ("selected", "primary", "base_lines_band", "class_counts", "band_counts")}))
        return 0
    res = run(C.load(DXF_COUNTS))
    old = C.load(OUT / "T692_CENSUS.json")
    ok = json.dumps(res, sort_keys=True) == json.dumps(old, sort_keys=True)
    print("CHECK", "SAME" if ok else "DIFFERS")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
