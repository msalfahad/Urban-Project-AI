"""T-093 read-only Alsenan run: ARCH_TAKEOFF_V2.10 and ARCH_TAKEOFF_V2.11 (rolls per area alone, owner Q-49 A; held
top roof, owner Q-34) on the same architectural DXF. Prints the purchase table (areas, lengths, counts and engine room
ids only), the lines that differ between the two methods and the release-report counts. Nothing is written into the
repository.
    python3 -I research/agents_t093/alsenan_rolls_run.py <P7757.dxf> --out <scratch>/t093_alsenan.json
Project inputs as T-079: research/agents_t010/sanitary_reading.json and research/agents_t071/alsenan_facts.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _key(ln):
    loc = ln["location"]
    return "|".join(str(x) for x in (ln["item_code"], loc.get("floor"), loc.get("room_id"), loc.get("element_id"),
                                     ln["unit"]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from engine.source import arch_measure as AM
    from engine.source import arch_v211 as AV
    from tools import urban_boq_m9 as M
    facts = {"schema": AM.FACTS_SCHEMA,
             "sanitary_by_room": json.loads((ROOT / "research/agents_t010/sanitary_reading.json").read_text(
                 encoding="utf-8"))["items"],
             "exterior_spaces": json.loads((ROOT / "research/agents_t071/alsenan_facts.json").read_text(
                 encoding="utf-8"))}
    b10, _a10, _ = M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.10")
    b11, a11, _ = M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.11", facts=facts)
    q10 = {_key(x): (x["measured_net"], x["evidence_state"]) for x in b10["lines"]}
    q11 = {_key(x): (x["measured_net"], x["evidence_state"]) for x in b11["lines"]}
    rows = AV.purchase_rows(a11["v211"]["membrane_table"])
    out = {"purchase": rows, "top_roofs_held": a11["v211"]["top_roofs_held"],
           "changed_from_v2_10": {k: [q10[k], q11[k]] for k in sorted(set(q10) & set(q11)) if q10[k] != q11[k]},
           "only_v2_10": sorted(set(q10) - set(q11)),
           "only_v2_11": {k: q11[k] for k in sorted(set(q11) - set(q10))},
           "release_report": a11["run"]["v2_11"]["release_report"]}
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    for r in rows:
        print({k: r.get(k) for k in ("system", "floor", "room_id", "name", "state", "floor_m2", "layout", "rolls",
                                     "strip_length_m", "leftover_m", "reason")})
    print(len(out["changed_from_v2_10"]), "V2.10 lines changed;", len(out["only_v2_10"]), "only in V2.10;",
          len(out["only_v2_11"]), "only in V2.11;", out["release_report"])


if __name__ == "__main__":
    main()
