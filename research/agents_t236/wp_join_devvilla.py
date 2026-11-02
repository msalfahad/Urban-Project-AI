"""T-383 on the development villa (no private input): the T-301 WP.FOUNDATION inventory + the committed waterproofing
line extract (research/agents_t301/CANDIDATE_V3017_WP.json; the B8-08 lines are unchanged V3.0.15 .. V3.0.43, T-353
Gate A) read by the per-line WP join (wp_join.py), with the Checker's V2 records on the WP lines as line id -> scope
(docs/agents/verdicts/V3.0.17 and V3.0.41 on agents/control: the same 7 line ids, re-bound by content).

    python3 -I research/agents_t236/wp_join_devvilla.py --out OUT_DIR
writes WP_JOIN_T383_DEVVILLA.json (the per-line records + the whole-line restatement); nothing else.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (ROOT, HERE, ROOT / "research" / "agents_t301", ROOT / "research" / "agents_t469",
           ROOT / "research" / "agents_t471"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import t301_alsenan as A  # noqa: E402
import t469_trade_scoreboard as T469  # noqa: E402
import t471_completeness as T471  # noqa: E402
import wp_join as J  # noqa: E402

PID = "development-villa-t131"     # the project id the V2 records carry (no client name)
REV = "5e3690754db90b5fa2d878d4fc29b2e84ce9d1d91e4c1e68a62019d1b34bbc22"
# the Checker's V2 records on the WP lines (V3.0.17 set; re-bound on V3.0.41 to the same line ids): line id -> scope
V2 = {"L-69e6e6d74707afe3ac5b": "COMPONENT", "L-e6280a91646613667b62": "COMPONENT",
      "L-4ec54f9922da7281573a": "COMPONENT", "L-d3ec19448415e0a0f083": "COMPONENT",
      "L-1f3aaafcc460173462d9": "COMPONENT", "L-e11f17bb076058bf172d": "WHOLE", "L-e4789d76efedbc351bd4": "WHOLE"}
OUT = "WP_JOIN_T383_DEVVILLA.json"
REGISTER = ROOT / "research" / "agents_t471" / "EIMP_REGISTER_DEV_VILLA.json"


def lines():
    """the extract as canonical-shaped lines (location, trade, evidence_state, measured_net; no other field)."""
    raw = json.loads(A.EXTRACT.read_text(encoding="utf-8"))["lines"]
    return [{"line_id": x["line_id"], "item_code": x["item_code"], "unit": x["unit"], "trade": x["trade"],
             "subtrade": x.get("subtrade"), "evidence_state": x["evidence_state"], "measured_net": x["measured_net"],
             "location": {"floor": x["floor"], "element_id": x["element_id"]}} for x in raw]


def run():
    els = A.inventory()
    ls = lines()
    fl = [{"line_id": x["line_id"], "item_code": x["item_code"], "unit": x["unit"], "components":
           y["components"], "record_element": y.get("record_element")}
          for x, y in zip(ls, json.loads(A.EXTRACT.read_text(encoding="utf-8"))["lines"])]
    lk, unread, mk = A.links([x for x in fl if x["item_code"].startswith("WP.FOUNDATION.")], els)
    doc, recs = J.records(els, ls, lk, (PID, REV))
    groups = J.wp_groups(ls)
    by_id = {x["line_id"]: x for x in ls}
    whole = {}
    for lid, sc in sorted(V2.items()):
        if sc == "WHOLE":
            x = by_id[lid]
            whole[(x["trade"], x["item_code"], x["unit"])] = lid
    ok, not_ok = J.whole_lines(recs, groups, whole, (PID, REV))
    doc["v2_whole_records"] = len(whole)
    doc["wp_whole_lines"] = [{"group": list(g), "line_id": lid} for g, lid in ok]
    doc["wp_whole_records_not_counted"] = [{"group": list(g), "line_id": lid} for g, lid in not_ok]
    doc["unread_lines_no_inventory"] = len(unread)
    # T-471 framework: line classes (T-469 line_class; the two WHOLE records confirm the engine figure exactly:
    # 20.700 m2 / 1.035 m3, Verifier V3.0.41 re-bind) and the register's components that carry a WP item code
    cls = {x["line_id"]: T469.line_class(x) for x in ls}
    for lid in whole.values():
        cls[lid] = T471.VERIFIED
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    doc["components"] = J.components(reg, ls, cls, recs, els)
    return doc, recs, els, ls


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    doc, *_r = run()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / OUT).write_text(J.dump(doc), encoding="utf-8")
    print(f"T-383: {doc['wp_groups']} WP lines (groups), passing {len(doc['groups_passing'])}, "
          f"WHOLE counted {len(doc['wp_whole_lines'])} of {doc['v2_whole_records']} WHOLE records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
