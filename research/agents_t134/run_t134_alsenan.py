"""T-134 read-only check of the element register v0 on a development-villa run (no client data is printed: counts,
states, item codes and engine keys only; no coordinates, no room names).

    python3 -I research/agents_t134/run_t134_alsenan.py <v30 run dir> [--v29 <v29 run dir>]

<v30 run dir> is the --out/v30 folder of research/agents_t131/alsenan_v30_run.py on the Drive DXFs. The register is
written beside that run's files (outside the repository). With --v29 the released ARCH_TAKEOFF_V2.9 run of the same
drawings is registered too and mapped to the V3.0 register (same revision: every element should keep its local id).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import element_register_v0 as E  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("v30")
    ap.add_argument("--v29")
    a = ap.parse_args(argv)
    reg = E.build_dir(a.v30)
    again = E.build_dir(a.v30)
    E.write(a.v30, reg)
    print("lines", reg["lines"], "links", reg["links"], "elements", len(reg["elements"]), "rerun identical",
          reg == again, "revisions", reg["revisions"]["all"])
    for k, v in reg["summary"]["per_kind"].items():
        print(f"{k:13s}", json.dumps(v, sort_keys=True))
    c = reg["checks"]
    print("checks:", {k: (v if isinstance(v, (int, bool)) else len(v)) for k, v in c.items()})
    for f in c["double_finish"] + c["double_concrete"] + c["held_released"] + c["duplicate_lines"] + \
            c["conflict_released"]:
        print("  FINDING", {k: v for k, v in f.items() if k != "lines"})
    for u in reg["summary"]["unlinked_by_reason"]:
        print("  UNLINKED", u["lines"], u["item_code"], "-", u["reason"])
    idle = Counter((x["kind"], x["status"], (x.get("evidence") or {}).get("file")) for x in c["elements_without_lines"])
    for (k, st, f), n in sorted(idle.items()):
        print("  NO LINE", n, k, st, f)
    # aggregate wall-run lines: the member walls' own net runs against the line's value
    lines = {ln["line_id"]: ln for ln in json.loads((Path(a.v30) / reg["lines_file"]).read_text(encoding="utf-8"))}
    agg = defaultdict(float)
    for e in reg["elements"]:
        for b in e["boq_lines"]:
            if b["item_code"] == "ARCH.WALL_RUN" and e["kind"] == "WALL":
                agg[b["line_id"]] += e.get("share_lm") or 0.0
    for lid, s in sorted(agg.items(), key=lambda t: lines[t[0]]["location"]["element_id"]):
        ln = lines[lid]
        print(f"  WALL_RUN {ln['location']['element_id']:24s} line {ln['measured_net']:.3f} lm, member walls "
              f"{s:.3f} lm, diff {s - ln['measured_net']:+.3f}")
    # floor-finish surfaces per element kind (one finish per surface): what the cross-trade check looked at
    fin = Counter()
    for e in reg["elements"]:
        codes = sorted({b["item_code"] for b in e["boq_lines"] if b["role"] == "PRIMARY" and b["item_code"]
                        in E.FLOOR_FINISH})
        if codes:
            fin[(e["kind"], "+".join(codes))] += 1
    for (k, codes), n in sorted(fin.items()):
        print("  FLOOR SURFACE", n, k, codes)
    # a drawing revision simulated on the real outputs: one wall moved 5 mm, then 60 mm, along its normal (the
    # longest axis-parallel wall of the first floor listed); every other element must keep its local id
    import copy
    lines0, src0, _ = E.load_run(a.v30)
    ws = [w for w in src0["walls"][0]["walls"] if len(w["centreline"]) == 2 and
          abs(w["centreline"][0][1] - w["centreline"][1][1]) < 1e-6]
    w = max(ws, key=lambda w: abs(w["centreline"][0][0] - w["centreline"][1][0]))
    for d_mm in (5, 60):
        src = copy.deepcopy(src0)
        for x in src["walls"][0]["walls"]:
            if x["wall_id"] == w["wall_id"]:
                x["centreline"] = [[p[0], p[1] + d_mm / 1000.0 / src["unit_m"]] for p in x["centreline"]]
        m = E.map_revisions(reg, E.build(lines0, src))
        print(f"wall {w['wall_id']} (t {w['t_m']}) moved {d_mm} mm:", dict(Counter(x["how"] for x in m["mapping"])),
              "new", len(m["new"]), "removed", len(m["removed"]),
              [x.get("overlap") for x in m["mapping"] if x["how"] == "OVERLAP"])
    if a.v29:
        r29 = E.build_dir(a.v29)
        m = E.map_revisions(r29, reg)
        print("V2.9 -> V3.0 mapping:", Counter(x["how"] for x in m["mapping"]), "new", len(m["new"]), "removed",
              len(m["removed"]))
        for x in m["new"]:
            print("  NEW in V3.0", x.split("/", 2)[2])
        for x in m["removed"]:
            print("  ONLY in V2.9", x.split("/", 2)[2])
        print("V2.9 lines", r29["lines"], "unlinked", r29["checks"]["unlinked"], "findings",
              {k: len(v) for k, v in r29["checks"].items() if isinstance(v, list)})
    return 0


if __name__ == "__main__":
    main()
