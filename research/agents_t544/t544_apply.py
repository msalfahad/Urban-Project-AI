"""T-544: R-T544-1 applied to the 1F white AAC 0.20 glue host L-2fdc0f97 (development villa), from committed inputs only
(no drawing needed):

  research/agents_t544/out/JAMB_EVIDENCE_T544.csv     the 8 ends of W16 / W19 / W20 / W24 (LINTEL_BEARING_V3 run)
  research/agents_t544/out/EXTENDED_SEARCH_T544.csv   W24 END re-searched past the 3.0 m limit (R-T544-1 (1))
  research/agents_t527/out/JAMB_EVIDENCE_V3_T527.csv  W15's ends (its END is the pier it shares with W16)
  research/agents_t537/t537_apply.py                  the T-537 r2 host machinery: ledger, T-530 lintel lines, the
                                                      R-T523-1 glue group (imported, not copied, not edited)

Nothing is written: tests/t544_held_lintel_ceiling assert every figure against the hand calculation (T-544 report).
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t537"))
import held_lintel_ceiling as H  # noqa: E402
import r_t498_2 as R  # noqa: E402  (read only)
import t537_apply as A  # noqa: E402  (read only)

EVIDENCE = HERE / "out" / "JAMB_EVIDENCE_T544.csv"
EXTENDED = HERE / "out" / "EXTENDED_SEARCH_T544.csv"
EVIDENCE_P2 = HERE / "out" / "JAMB_EVIDENCE_T544_P2.csv"
T527_EVIDENCE = ROOT / "research" / "agents_t527" / "out" / "JAMB_EVIDENCE_V3_T527.csv"
HOST_1F = "L-2fdc0f971a94348ec855"
HELD_IDS = ("W16", "W19", "W20", "W24")
PAIRS = (("W15", "W16"), ("W19", "W20"))          # facing ends stop at each other (OPENING both ways), one host


def _csv(p):
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def ends_of():
    """{oid: {side: {"a_m", "stopper", "stopper_id", "w_gap_m", "basis"}}}: V3 evidence, SEARCH_LIMIT ends replaced by
    their extended search where it found a stopper."""
    out = {}
    for r in _csv(EVIDENCE) + _csv(EVIDENCE_P2) + [x for x in _csv(T527_EVIDENCE) if x["opening_id"] == "W15"]:
        a = r["v3_available_6dp_m"]
        out.setdefault(r["opening_id"], {})[r["side"]] = {
            "side": r["side"], "a_m": float(a) if a else None, "stopper": r["stopper"], "stopper_id": r["stopper_id"],
            "w_gap_m": float(r["clear_width_m"]), "basis": "MEASURED", "search": "3.0 m (V3)"}
    for r in _csv(EXTENDED):
        e = out[r["opening_id"]][r["side"]]
        if e["stopper"] != "SEARCH_LIMIT":
            raise H.RuleError(f"{r['opening_id']} {r['side']}: extended search on an end that had a stopper")
        e.update(a_m=float(r["available_6dp_m"]), stopper=r["stopper"], stopper_id=r["stopper_id"],
                 search=f"{r['search_m']} m (R-T544-1 (1))")
    for oid, es in out.items():
        if len({e["w_gap_m"] for e in es.values()}) != 1:
            raise H.RuleError(f"{oid}: the two ends disagree on the clear gap")
    return out


def _held_ledger(m):
    return {h["opening_id"]: h for h in m.get("lintel_held_faces") or []}


def faces_1f(m, lintels, ends):
    """the 1F host's face records under R-T544-1: W14 / W18 as T-537 r2 (lintel lines), W15 + W16 and W19 + W20 joint,
    W24 alone; every HELD member's D and B from the T-453 ledger face (B = host thickness: one-depth lintels)."""
    t = m["thickness_m"]
    held = _held_ledger(m)
    if set(held) != set(HELD_IDS):
        raise H.RuleError(f"1F host held faces {sorted(held)} != {HELD_IDS}")
    hosts_of = {d["opening_id"]: HOST_1F for d in m["lintel_deductions"]}
    hosts_of.update({k: HOST_1F for k in held})
    faces, singles = [], {}
    for d in m["lintel_deductions"]:
        f = R.lintel_face(lintels[d["opening_id"]], t)
        f["length_m"] = list(lintels[d["opening_id"]]["length_m"])
        singles[d["opening_id"]] = f
    for oid in HELD_IDS:
        h = held[oid]
        singles[oid] = H.held_face(oid, [t, h["depth_m"]], ends[oid]["START"]["w_gap_m"],
                                   [ends[oid]["START"], ends[oid]["END"]], t)
    used = set()
    for first, second in PAIRS:
        fe, se = ends[first]["END"], ends[second]["START"]
        if not (fe["stopper"] == "OPENING" and fe["stopper_id"] == second and se["stopper"] == "OPENING"
                and se["stopper_id"] == first and abs(fe["a_m"] - se["a_m"]) <= 1e-6):
            raise H.RuleError(f"{first}/{second}: not one shared pier")
        mem = []
        for oid, outer in ((first, "START"), (second, "END")):
            D = held[oid]["depth_m"] if oid in held else lintels[oid]["section_B_D_m"][1]
            mem.append({"opening_id": oid, "D_m": D, "w_gap_m": ends[oid]["START"]["w_gap_m"],
                        "face_lo_m2": singles[oid]["face_m2"][0], "outer": ends[oid][outer]})
        mem[0]["pier_m"] = fe["a_m"]
        faces += list(H.joint_face(mem, hosts_of).values())
        used |= {first, second}
    faces += [singles[k] for k in singles if k not in used]
    return faces, singles


def build():
    led = {m["line_id"]: m for m in A._json(A.T453_LEDGER)["block_materials"] if m["item"] == "LAYING_MATERIAL"}
    t537 = A.build()
    man = A._json(A.T530_MANIFEST)
    v3 = A.v3_ends()
    lintels = {}
    for row in man["stream_S"]["lintel_lines"]:
        if "pair" in row["after"]:
            continue
        li = A._lintel_input(row)
        lintels[li["opening_id"]] = A._ceiling_input(li, v3) if li["state"] == "HELD_BY_NAME" else li
    ends = ends_of()
    m = led[HOST_1F]
    faces, singles = faces_1f(m, lintels, ends)
    base = R.material_base(m["net_m2"], faces)
    glue = R.material_line(base, m["kg_per_m2"], "kg")
    bags = R.material_line(base, m["kg_per_m2"] / A.PACK_KG, "bags_25kg_net")
    # beside: the individual-ceiling sum (each lintel taking the whole shared pier) -- not achievable, never the result
    indiv = R.material_base(m["net_m2"], list(singles.values()))
    before = next(h for h in t537["hosts"] if h["host_line_id"] == HOST_1F)["after_r_t498_2"]
    gf = next(h for h in t537["hosts"] if h["host_line_id"] != HOST_1F)
    group = A._glue_group({HOST_1F: bags, gf["host_line_id"]: gf["after_r_t498_2"]["bags_25kg_net"]})
    concrete = {oid: {"B_D_m": [m["thickness_m"], singles[oid]["D_m"]], "L_ceil_m": singles[oid]["L_ceil_m"],
                      "concrete_m3": [0.0, None if singles[oid]["L_ceil_m"] is None else
                                      R._r(m["thickness_m"] * singles[oid]["D_m"] * singles[oid]["L_ceil_m"])]}
                for oid in HELD_IDS}
    return {"schema": "T544_APPLICATION_V1", "rule": f"{H.RULE_ID} {H.RULE_VERSION} on {R.RULE_ID} {R.RULE_VERSION}",
            "host_line_id": HOST_1F, "contract_net_m2": m["net_m2"], "kg_per_m2": m["kg_per_m2"],
            "ends": {k: ends[k] for k in HELD_IDS + ("W15",)},
            "held_lintels": {k: singles[k] for k in HELD_IDS},
            "before_t537_r2": {"base": before["base"]["base_m2"], "glue_kg": before["glue_kg"]},
            "after": {"base": base, "glue_kg": glue, "bags_25kg_net": bags},
            "beside_individual_ceilings": {"base_m2": indiv["base_m2"], "face_sum_m2": indiv["face_sum_m2"],
                                           "note": "each lintel taking the whole shared pier: not buildable, not the bound"},
            "beside_concrete_if_built": concrete,
            "glue_group": {"before_t537_r2": t537["glue_group"]["after_r_t498_2"], "after": group},
            "released_quantities_changed": 0}


# ------------------------------------------------------------------------------------------------ part 2
HOSTS_P2 = ("L-541cf7210e52db0498bb", "L-b7b4d784fbe7fdbebe84", "L-bbb82de298fecbafa11d")


def pairs_of(ids, ends):
    """facing ends that stop at each other with one measured pier -> [(first, second)] in band order."""
    out = []
    for a in ids:
        e = ends[a]["END"]
        if e["stopper"] == "OPENING" and e["stopper_id"] in ids:
            b = e["stopper_id"]
            s = ends[b]["START"]
            if s["stopper"] == "OPENING" and s["stopper_id"] == a and abs(s["a_m"] - e["a_m"]) <= 1e-6:
                out.append((a, b))
            else:
                raise H.RuleError(f"{a}/{b}: facing ends disagree (not one pier)")
    return out


def faces_held_only(m, ends):
    """a host whose lintel faces are all HELD / FLAGGED (existence not established): R-T544-1 per lintel, shared piers
    joint on the host."""
    if m.get("lintel_deductions"):
        raise H.RuleError(f"{m['line_id']}: has REQUIRED lintels (use faces_1f-style input)")
    t = m["thickness_m"]
    held = _held_ledger(m)
    singles = {oid: H.held_face(oid, [t, h["depth_m"]], ends[oid]["START"]["w_gap_m"],
                                [ends[oid]["START"], ends[oid]["END"]], t) for oid, h in held.items()}
    hosts_of = {k: m["line_id"] for k in held}
    faces, used = [], set()
    for a, b in pairs_of(list(held), ends):
        mem = [{"opening_id": a, "D_m": held[a]["depth_m"], "w_gap_m": ends[a]["START"]["w_gap_m"], "face_lo_m2": 0.0,
                "outer": ends[a]["START"], "pier_m": ends[a]["END"]["a_m"]},
               {"opening_id": b, "D_m": held[b]["depth_m"], "w_gap_m": ends[b]["START"]["w_gap_m"], "face_lo_m2": 0.0,
                "outer": ends[b]["END"]}]
        faces += list(H.joint_face(mem, hosts_of).values())
        used |= {a, b}
    faces += [singles[k] for k in singles if k not in used]
    return faces, singles


def build_part2():
    led = {m["line_id"]: m for m in A._json(A.T453_LEDGER)["block_materials"] if m["item"] == "LAYING_MATERIAL"}
    ends = ends_of()
    rows = []
    for lid in HOSTS_P2:
        m = led[lid]
        faces, singles = faces_held_only(m, ends)
        base = R.material_base(m["net_m2"], faces)
        rows.append({"host_line_id": lid, "host_element": m["element_id"], "contract_net_m2": m["net_m2"],
                     "kg_per_m2": m["kg_per_m2"],
                     "before_t453_r1": {"base_m2": m["material_base_range_m2"], "glue_kg": m["consumption_kg_range"],
                                        "bags_25kg_net": m["bags_25kg_net_range"],
                                        "basis": "R-T498-1 legacy held maxima D x (w + 0.80): a LOWER bound of a built "
                                                 "lintel (F-T537-1), so the low end is no proven bound"},
                     "held_lintels": singles, "after": {"base": base,
                                                        "glue_kg": R.material_line(base, m["kg_per_m2"], "kg"),
                                                        "bags_25kg_net": R.material_line(base, m["kg_per_m2"] / A.PACK_KG,
                                                                                         "bags_25kg_net")}})
    return rows


def host_freshness():
    """{line_id: T-523 'fresh' of its glue_bags binding}: a host whose contract class is HELD in the candidate
    (STALE_CLASS, e.g. the 2F roof-storey walls D-39) is never moved into a valued group member."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("t523_for_t544", ROOT / "research/agents_t523/t523_binding_map_v2.py")
    m523 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m523)
    return {b["line_id"]: b["fresh"] for b in m523.run()["bindings"]
            if b["table"] == "T-453" and b["kind"] == "glue_bags_25kg_net"}


def build_all():
    """part 1 (the task host) + part 2 (the other three white AAC hosts with held lintels) + the glue group with every
    moved host whose contract class is current (FRESH); a STALE / HELD host keeps its HELD binding (range beside)."""
    p1 = build()
    p2 = build_part2()
    fresh = host_freshness()
    for r in p2:
        r["t523_fresh"] = fresh.get(r["host_line_id"])
        r["group_member_moved"] = r["t523_fresh"] == "FRESH"
    t537 = A.build()
    gf = next(h for h in t537["hosts"] if h["host_line_id"] != HOST_1F)
    moves = {HOST_1F: p1["after"]["bags_25kg_net"], gf["host_line_id"]: gf["after_r_t498_2"]["bags_25kg_net"]}
    moves.update({r["host_line_id"]: r["after"]["bags_25kg_net"] for r in p2 if r["group_member_moved"]})
    return {"part1": p1, "part2": p2, "glue_group_all": A._glue_group(moves)}


def dumps(d):
    return json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n"


if __name__ == "__main__":
    sys.stdout.write(dumps(build_all()))
