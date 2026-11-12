"""T-717: the package summary out/T717_SUMMARY.json from a finished v3074_run.py output folder (item codes, line ids,
element ids, units, states and quantities only; no coordinate, no name):

  - the integration ledger rows (before / after per line, piece, host, flag, verification);
  - the FIN.PLASTER / FIN.PAINT census before / after (released / bounded / blank per unit) and the code totals moved;
  - the like-for-like scoreboard line restated (T-701 dry + shaft, his gross with the T-726 13.50 NO_FACE row shown
    apart: never added, never removed from his total): each restated dry line's change applied to the T-701 engine
    range, Decimal, from the lines of record.

    python3 -I research/agents_t717/t717_summary.py --run <out of v3074_run.py> --write
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

F701 = ROOT / "research/agents_t701/out/T701_RECONCILE.json"
F726 = ROOT / "research/agents_t726/out/T726_SHAFT_RESIDUAL.json"
OUT = HERE / "out/T717_SUMMARY.json"
X = Decimal
Q = X("0.000001")
HIS_APART = X("13.50")          # T-726 R-T726-1..3: his 2.50 x 5.40 continuation row, NO_FACE (plaster 24 / paint 25)


def _q(ln):
    from engine.source import arch_v30 as A30
    q = A30._qty(ln)
    return {k: q.get(k) for k in ("value", "low", "high")}


def like_for_like(lines73, lines74):
    """T-701 like-for-like dry + shaft, restated: engine range += each dry line's change V3.0.73 -> V3.0.74 (the lines
    T-701 counted), his gross shown with the 13.50 row apart."""
    t701 = json.loads(F701.read_text(encoding="utf-8"))
    by73 = {ln["line_id"]: ln for ln in lines73}
    by74 = {ln["line_id"]: ln for ln in lines74}
    out = {}
    for layer, code in (("plaster", "FIN.PLASTER"), ("paint", "FIN.PAINT")):
        lf = t701["like_for_like_dry_plus_shaft"][layer]
        lo, hi = (X(v) for v in lf["engine_net"])
        moved = []
        for r in t701["dry_rooms"]:
            pref = r[f"{layer}_line"]
            hits = [lid for lid in by73 if lid.startswith(pref) and by73[lid]["item_code"] == code]
            if len(hits) != 1:
                raise SystemExit(f"{layer} {r['room']}: line {pref} is not one candidate line")
            a, b = _q(by73[hits[0]]), _q(by74[hits[0]])
            if a == b:
                continue
            al, ah = (X(str(a["value"])),) * 2 if a["value"] is not None else (X(str(a["low"])), X(str(a["high"])))
            bl, bh = (X(str(b["value"])),) * 2 if b["value"] is not None else (X(str(b["low"])), X(str(b["high"])))
            lo, hi = lo + (bl - al), hi + (bh - ah)
            moved.append({"room": r["room"], "line_id": hits[0], "v3_0_73": [float(al), float(ah)],
                          "v3_0_74": [float(bl), float(bh)], "delta": [float(bl - al), float(bh - ah)]})
        his = X(lf["his_gross"])
        apart = his - HIS_APART

        def pct(v, h):
            return float(((v / h - 1) * 100).quantize(X("0.01")))
        out[layer] = {"engine_net_t701": lf["engine_net"], "moved_lines": moved,
                      "engine_net_v3_0_74": [float(lo.quantize(Q)), float(hi.quantize(Q))],
                      "his_gross": float(his), "his_row_apart_no_face": float(HIS_APART),
                      "his_like_for_like": float(apart),
                      "pct_vs_his_gross": [pct(lo, his), pct(hi, his)],
                      "pct_vs_his_with_row_apart": [pct(lo, apart), pct(hi, apart)],
                      "not_in_this_line": "the stairwell band and the return-paint lines are new elements the T-701 "
                                          "like-for-like set (11 dry rooms + 3 shaft lines) does not hold: shown "
                                          "beside, never added to his comparison"}
    return out


def build(run):
    run = Path(run)
    from engine.source import boq_line as BL  # noqa: F401
    l73 = json.loads((run / "V3_0_73_BOQ_LINES.json").read_text(encoding="utf-8"))
    l74 = json.loads((run / "V3_0_74_BOQ_LINES.json").read_text(encoding="utf-8"))
    l73 = l73["lines"] if isinstance(l73, dict) else l73
    l74 = l74["lines"] if isinstance(l74, dict) else l74
    rj = json.loads((run / "V3_0_74_RUN.json").read_text(encoding="utf-8"))
    led = json.loads((run / "V3_0_74_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    rows = [{k: r.get(k) for k in ("piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit",
                                   "host_line_id", "before_base", "after_v3_0_74", "class", "flag", "correction",
                                   "map_row", "verification")} for r in led["rows"]]
    added = [r for r in rows if r["change"] == "ADD"]
    sums = {}
    for r in added:
        k = (r["piece"], r["item_code"])
        z = sums.setdefault(f"{k[0]}|{k[1]}", {"lines": 0, "low": X(0), "high": X(0), "blank": 0})
        z["lines"] += 1
        a = r["after_v3_0_74"]
        if a.get("low") is None:
            z["blank"] += 1
        else:
            z["low"] += X(str(a["low"]))
            z["high"] += X(str(a["high"]))
    sums = {k: dict(v, low=float(v["low"]), high=float(v["high"])) for k, v in sums.items()}
    return {"schema": "URBAN_T717_SUMMARY_V1", "task": "T-717", "method": rj["method"], "extends": rj["extends"],
            "lines_sha256": {"V3_0_73": hashlib.sha256((run / "V3_0_73_BOQ_LINES.json").read_bytes()).hexdigest(),
                             "V3_0_74": hashlib.sha256((run / "V3_0_74_BOQ_LINES.json").read_bytes()).hexdigest()},
            "identity": {k: rj["identity"][k] for k in ("base_lines", "v3_0_74_lines", "replaced", "added",
                                                         "outside_rows", "outside_rows_identical_to_base", "diff",
                                                         "finishes", "fin_census_before", "fin_census_after")},
            "totals_moved": {k: {f: round(v["v3_0_74"][f] - (v["base"] or {}).get(f, 0), 6)
                                 for f in ("released", "held_low", "held_high", "lines", "bounded_lines",
                                           "blocked_lines")} for k, v in rj["totals_moved_by_code"].items()},
            "added_sums": sums, "rows": rows, "like_for_like": like_for_like(l73, l74),
            "waiting": {k: v for k, v in rj["waiting_pieces"].items() if k.startswith("T717")}}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    doc = build(a.run)
    print(json.dumps({k: doc[k] for k in ("totals_moved", "added_sums", "like_for_like")}, indent=1))
    if a.write:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("written", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
