"""T-079 read-only Alsenan run: ARCH_TAKEOFF_V2.10 and ARCH_TAKEOFF_V2.11 on the same architectural DXF, the
waterproofing figures of V2.11 and every line that differs between the two. Nothing is written into the repository;
the output holds areas, lengths, counts and engine room ids only.
    python3 -I research/agents_t079/alsenan_v211_run.py <P7757.dxf> --out <scratch>/t079_alsenan.json
The project inputs of V2.11 come from the merged research of the earlier tasks (both committed, no client data):
research/agents_t010/sanitary_reading.json (the sanitary drawing read by hand per engine room id, T-010) and
research/agents_t071/alsenan_facts.json (the two dome circles = skylight openings, owner Q-29, T-071)."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _key(ln):
    loc = ln["location"]
    return "|".join(str(x) for x in (ln["item_code"], loc.get("floor"), loc.get("room_id"), loc.get("element_id"),
                                     ln["unit"]))


def _tot(lines):
    t = Counter()
    for ln in lines:
        if ln["evidence_state"] in ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL") and ln["measured_net"] is not None:
            t[f"{ln['item_code']} [{ln['unit']}]"] += ln["measured_net"]
    return {k: round(v, 4) for k, v in sorted(t.items())}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from engine.source import arch_measure as AM
    from tools import urban_boq_m9 as M
    facts = {"schema": AM.FACTS_SCHEMA,
             "sanitary_by_room": json.loads((ROOT / "research/agents_t010/sanitary_reading.json").read_text(
                 encoding="utf-8"))["items"],
             "exterior_spaces": json.loads((ROOT / "research/agents_t071/alsenan_facts.json").read_text(
                 encoding="utf-8"))}
    b10, a10, _ = M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.10")
    b11, a11, _ = M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.11", facts=facts)
    q10 = {_key(x): (x["measured_net"], x["evidence_state"]) for x in b10["lines"]}
    q11 = {_key(x): (x["measured_net"], x["evidence_state"]) for x in b11["lines"]}
    t10, t11 = _tot(b10["lines"]), _tot(b11["lines"])
    v = a11["v211"]
    out = {"method": "ARCH_TAKEOFF_V2.11", "summary": v["summary"],
           "only_v2_10": {k: q10[k] for k in sorted(set(q10) - set(q11))},
           "only_v2_11": {k: q11[k] for k in sorted(set(q11) - set(q10))},
           "changed": {k: [q10[k], q11[k]] for k in sorted(set(q10) & set(q11)) if q10[k] != q11[k]},
           "totals_changed": {k: [t10.get(k), t11.get(k)] for k in sorted(set(t10) | set(t11))
                              if abs((t10.get(k) or 0) - (t11.get(k) or 0)) > 1e-6},
           "membrane_table": v["membrane_table"], "release_report": a11["run"]["v2_11"]["release_report"]}
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("totals_changed", "release_report")}, indent=1))
    print(len(out["only_v2_10"]), "lines only in V2.10;", len(out["only_v2_11"]), "only in V2.11;",
          len(out["changed"]), "changed")


if __name__ == "__main__":
    main()
