"""Quantity-level diff of two ARCH_TAKEOFF output folders, independent of room / opening id renumbering and of the
drawing unit: rooms by (floor, class, codes, name), openings by (floor, kind, width, jambs, room names), lines by
(floor, room name, element kind, item, state, quantity).
usage: python3 -I qdiff.py A B [JSON_OUT]"""
import json, re, sys
from collections import Counter
A, B = sys.argv[1], sys.argv[2]
def J(d, f):
    return json.load(open(f"{d}/{f}"))
def room_names(d):
    out = {}
    for r in J(d, "ARCH_ROOMS.json")["rooms"]:
        nm = r.get("name_en") or "+".join(r.get("codes") or []) or r["class"]
        out[r["room_id"]] = f'{r["floor"]}:{r["class"]}:{nm}'
    return out
def rooms(d):
    return Counter((r["floor"], r["class"], "+".join(r.get("codes") or []), round(r["area_m2"], 4))
                   for r in J(d, "ARCH_ROOMS.json")["rooms"])
def ops(d):
    rn = room_names(d)
    O = J(d, "ARCH_OPENINGS.json"); O = O["openings"] if isinstance(O, dict) else O
    return Counter((o["floor"], o["kind"], round(o["width_m"], 4), "/".join(o["jambs"]),
                    " | ".join(sorted(rn.get(x, x) for x in o["rooms"]))) for o in O)
def lines(d):
    rn = room_names(d)
    L = J(d, "BOQ_LINES.json"); L = L["lines"] if isinstance(L, dict) else L
    out = Counter()
    for l in L:
        loc = l.get("location") or {}
        el = loc.get("element_id") or ""
        el = el.split(":", 1)[1] if ":" in el else el
        el = re.sub(r"OP-\d+(\+OP-\d+)*", "OP", el)
        q = l.get("measured_net")
        out[(loc.get("floor"), rn.get(loc.get("room_id"), loc.get("room_id")), el, l["item_code"], l["evidence_state"],
             None if q is None else round(q, 4))] += 1
    return out
res = {}
for name, f in (("rooms", rooms), ("openings", ops), ("lines", lines)):
    a, b = f(A), f(B)
    res[name] = {"equal": a == b, "n_A": sum(a.values()), "n_B": sum(b.values()),
                 "only_in_A": sorted(map(str, (a - b).elements())), "only_in_B": sorted(map(str, (b - a).elements()))}
print(json.dumps(res, indent=1, ensure_ascii=True))
if len(sys.argv) > 3:
    json.dump(res, open(sys.argv[3], "w"), indent=1)
