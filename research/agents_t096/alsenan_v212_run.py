"""T-096 read-only Alsenan run: ARCH_TAKEOFF_V2.11 and ARCH_TAKEOFF_V2.12 (complete membrane coverage, MEMBRANE_FOLD_V3)
on the same architectural DXF. Prints the V2.12 purchase table (areas, lengths, counts and engine room ids only), the BOQ
lines that differ between the two methods and the release-report counts. Nothing is written into the repository.
    python3 -I research/agents_t096/alsenan_v212_run.py <P7757.dxf> --out <scratch>/t096_alsenan.json
Project inputs as T-079 / T-093: research/agents_t010/sanitary_reading.json and research/agents_t071/alsenan_facts.json."""

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
    from engine.source import arch_v212 as AV
    from tools import urban_boq_m9 as M
    facts = {"schema": AM.FACTS_SCHEMA,
             "sanitary_by_room": json.loads((ROOT / "research/agents_t010/sanitary_reading.json").read_text(
                 encoding="utf-8"))["items"],
             "exterior_spaces": json.loads((ROOT / "research/agents_t071/alsenan_facts.json").read_text(
                 encoding="utf-8"))}
    b11, _a11, _ = M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.11", facts=facts)
    b12, a12, _ = M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.12", facts=facts)
    q11 = {_key(x): (x["measured_net"], x["evidence_state"], (x.get("bounded_range") or {}).get("low"),
                     (x.get("bounded_range") or {}).get("high")) for x in b11["lines"]}
    q12 = {_key(x): (x["measured_net"], x["evidence_state"], (x.get("bounded_range") or {}).get("low"),
                     (x.get("bounded_range") or {}).get("high")) for x in b12["lines"]}
    rows = AV.purchase_rows(a12["v211"]["membrane_table"])
    pur = {f"{s}|{r['floor']}|{r['room_id']}": r.get("purchase") for s, st in
           a12["v211"]["membrane_table"]["systems"].items() for r in st["rows"]}
    out = {"purchase": rows, "purchase_detail": pur,
           "changed_from_v2_11": {k: [q11[k], q12[k]] for k in sorted(set(q11) & set(q12)) if q11[k] != q12[k]},
           "only_v2_11": sorted(set(q11) - set(q12)), "only_v2_12": {k: q12[k] for k in sorted(set(q12) - set(q11))},
           "release_report": a12["run"]["v2_12"]["release_report"]}
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    for r in rows:
        print({k: r.get(k) for k in ("system", "floor", "room_id", "name", "state", "floor_m2", "layout", "rolls",
                                     "rolls_q58_a", "rolls_q58_b", "rolls_q58_c", "upturn_only_strips",
                                     "strip_length_m", "leftover_m", "patch_m2")})
    print(len(out["changed_from_v2_11"]), "V2.11 lines changed:", out["changed_from_v2_11"])
    print(len(out["only_v2_11"]), "only in V2.11;", len(out["only_v2_12"]), "only in V2.12;", out["release_report"])


if __name__ == "__main__":
    main()
