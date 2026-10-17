"""STRUCTURAL N10 (Phase N10) - formwork faces, excavation footprints and the reinforcement audit for a route G run.

    python3 -I tools/struct_n10.py --run OUT_OF_URBAN_BOQ_M2 --out DIR [--facts FACTS.json]

reads OUT/PROVISIONAL_REGISTER.csv and OUT/UNRESOLVED_REGISTER.csv (tools/urban_boq_m2.py), writes DIR/FORMWORK.json,
DIR/FORMWORK_FACES.csv, DIR/EXCAVATION.json and DIR/REBAR_AUDIT.json (engine.source.struct_n10). The route G run is
read only: none of its files changes. facts: {"excavation": {"working_space_m" | "depth_m" | "ngl_m" |
"founding_level_m": {"value_m", "authority"}}} - stated project inputs, labelled.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import struct_n10 as SN                # noqa: E402

REGISTERS = ("PROVISIONAL_REGISTER.csv", "UNRESOLVED_REGISTER.csv", "VERIFIED_REGISTER.csv")
FACE_COLUMNS = ("component_id", "family", "storey", "category", "face", "state", "area_m2", "alternatives_m2",
                "decision", "formula", "why")


def read_rows(run):
    rows = []
    for name in REGISTERS:
        p = Path(run) / name
        if p.exists():
            with p.open(encoding="utf-8", newline="") as fh:
                rows += list(csv.DictReader(fh))
    return rows


def build(run, out, facts=None):
    rows = read_rows(run)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    fw, ex, rb = SN.formwork(rows), SN.excavation(rows, facts), SN.rebar_audit(rows)
    head = {"policy": SN.policy_record(), "run": str(Path(run).name), "rows_read": len(rows)}
    (out / "FORMWORK.json").write_text(json.dumps(dict(head, **fw), indent=1, sort_keys=True), encoding="utf-8")
    (out / "EXCAVATION.json").write_text(json.dumps(dict(head, **ex), indent=1, sort_keys=True), encoding="utf-8")
    (out / "REBAR_AUDIT.json").write_text(json.dumps(dict(head, **rb), indent=1, sort_keys=True), encoding="utf-8")
    with (out / "FORMWORK_FACES.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(FACE_COLUMNS)
        for f in fw["faces"]:
            w.writerow([json.dumps(f.get(k), sort_keys=True) if isinstance(f.get(k), dict) else f.get(k)
                        for k in FACE_COLUMNS])
    return {"formwork": fw["totals"], "held": fw["held"], "excavation": {k: ex[k] for k in ("state", "footprint_m2",
                                                                                          "volume_m3")},
            "rebar_rows": rb["rows"], "violations": len(rb["violations"])}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="struct_n10", description=__doc__.split("\n\n")[0])
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--facts")
    a = ap.parse_args(argv)
    facts = json.loads(Path(a.facts).read_text(encoding="utf-8")) if a.facts else None
    print(json.dumps(build(a.run, a.out, facts), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
