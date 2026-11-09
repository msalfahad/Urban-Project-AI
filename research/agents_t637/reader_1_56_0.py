"""T-637 acceptance reader: the T-630 dry-run reader (research/agents_t630/e2e_dry_run.py, read only, R-T630-1
unchanged) on the V3.0.58 overlay after WIRING MANIFEST V16 (T-631, merged 01880ae3; rebuilt with its own calls and
checked against the committed V16), grouped once by BOQ_FAMILY_MASTER 1.55.0 and once by 1.56.0.

It prints, per master: the UNCODED (NO_FAMILY) lines, the family coverage, the same-quantity pairs, and the aggregation
proof; then the comparison: every family row other than B9-01 / B9-04 / B6-08 byte-equal between the two runs, every
line in exactly the same place except the codes R-T637-1 moves, and the B9 re-add by hand. Nothing is wired or written
except research/agents_t637/out (through the pytest writer).
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (HERE, ROOT / "research/agents_t630", ROOT / "research/agents_t631"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import e2e_dry_run as E                    # noqa: E402  (R-T630-1, read only)
import manifest_v16 as M16                 # noqa: E402  (R-T631-1, read only)
import build_master_1_56_0 as BM           # noqa: E402

OUT_JSON = HERE / "out/T637_READER_1_56_0.json"
OUT_MD = HERE / "out/T637_READER_1_56_0.md"
MASTER_OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.55.0.json"
MASTER_NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.56.0.json"
MOVED_CODES = set(BM.REGISTER) | set(BM.MATERIAL) | set(BM.B9_04_CODES) | {"DOOR.LIFT_LANDING"}
D, S = E.D, E.S


def overlay_v16():
    """the T-631 build up to after16 (same calls, same order); checked against the committed V16."""
    M16.pins()
    t624, t622, t625 = M16._json(M16.IN["T624"]), M16._json(M16.IN["T622"]), M16._json(M16.IN["T625"])
    v16 = M16._json(M16.OUT_JSON)
    idx, order15, rul15, after15, rep15, t584 = M16.v15_state()
    wedge, chained, rul_w, _ = M16.t624_rows(t624, after15, order15)
    gf14 = M16.gf14_row(t622, after15, order15)
    stair, rul_s, _, _ = M16.t625_rows(t625, after15, order15)
    order16 = M16.M15.chain_into(order15, M16.P_OVER, chained) + [(M16.P_WEDGE, wedge), (M16.P_GF14, [gf14]),
                                                                    (M16.P_STAIR, stair)]
    after16, rep = E.OV.apply(idx, order16, list(rul15) + rul_w + rul_s)
    if len(after16) != v16["overlay"]["lines"]["after_v16"]:
        raise E.DryRunError("STALE_INPUT: the V16 rebuild differs from the committed V16 line count")
    t16 = E.OV.totals(after16)
    for k, d in v16["overlay"]["v16_vs_v15_totals"].items():
        if t16.get(k) != d["after"]:
            raise E.DryRunError(f"STALE_INPUT: V16 rebuild total {k} differs from the committed V16")
    return idx, order16, after16, rep


def run(master, after, bound, order):
    owner, item, fam, grp, unit, per_line, unc = E.aggregate(after, bound, order, master)
    checks = E.proof(after, item, fam, grp, unit)
    cov = E.family_coverage(master, fam)
    rows = {}
    for (g, f, u), a in fam.items():
        rows[f"{f}|{u}"] = dict(E._out(a, u, g == "B11"), group=g, boq_lines={
            c: E._out(item[(g2, f2, c, u2)], u2, g == "B11") for (g2, f2, c, u2) in item if (g2, f2, u2) == (g, f, u)})
    return {"uncoded": [{"bucket": b, "item_code": c, "unit": u, "lines": n} for (b, c, u), n in sorted(unc.items())],
            "same_quantity_codes": E.same_quantity_codes(item), "aggregation_proof": checks,
            "family_coverage": {c["family"]: c for c in cov}, "family_rows": rows,
            "placement": {l["line_id"]: (l["group"], l["family"]) for l in per_line},
            "unit_grand": {u: E._out(a, u) for u, a in sorted(unit.items())}}


def compare(old, new, after):
    """every family row and line placement equal except where R-T637-1 moves a code; -> (diffs, moved lines)"""
    changed = set(BM.CHANGED_FAMILIES)
    diffs = []
    for k in sorted(set(old["family_rows"]) | set(new["family_rows"])):
        if k.split("|")[0] in changed or k.startswith("UNCODED"):
            continue
        if json.dumps(old["family_rows"].get(k), sort_keys=True) != json.dumps(new["family_rows"].get(k), sort_keys=True):
            diffs.append(f"family row {k}")
    for c in sorted(set(old["family_coverage"]) | set(new["family_coverage"])):
        if c in changed:
            continue
        if json.dumps(old["family_coverage"].get(c), sort_keys=True) != \
                json.dumps(new["family_coverage"].get(c), sort_keys=True):
            diffs.append(f"family coverage {c}")
    moved = {}
    for lid, place in old["placement"].items():
        if new["placement"][lid] != place:
            code = after[lid]["item_code"]
            if code not in MOVED_CODES:
                diffs.append(f"line {lid} ({code}) moved {place} -> {new['placement'][lid]}")
            moved.setdefault(code, {"from": place, "to": new["placement"][lid], "lines": 0})["lines"] += 1
    if old["aggregation_proof"] != new["aggregation_proof"]:
        diffs.append("aggregation proof per unit differs (a regrouping never moves a unit sum)")
    return diffs, moved


def b9_by_hand(after, master):
    """the B9 re-add by hand, from the lines: work m2 = MAS.BLOCK only; units pcs apart; mortar m3 / glue kg in B9-04;
    the register codes outside."""
    out = {}
    for lid, l in after.items():
        if l["item_code"] in ("MAS.BLOCK",) or l["item_code"] in BM.MATERIAL or l["item_code"] in BM.B9_04_CODES \
                or l["item_code"] in BM.REGISTER:
            k = f"{l['item_code']}|{l['unit']}"
            o = out.setdefault(k, {"released_n": 0, "released": Decimal(0), "held_n": 0, "excluded_n": 0})
            if l["class"] == "RELEASED":
                o["released_n"] += 1
                o["released"] += D(l["measured_net"])
            elif l["class"] == "HELD":
                o["held_n"] += 1
            else:
                o["excluded_n"] += 1
    BM.material_guard(list(after.values()), master)
    return {k: dict(v, released=S(v["released"])) for k, v in sorted(out.items())}


def build():
    old_m, new_m = E._json(MASTER_OLD), E._json(MASTER_NEW)
    if (old_m["version"], new_m["version"]) != ("1.55.0", "1.56.0"):
        raise E.DryRunError("masters are not 1.55.0 / 1.56.0")
    idx, order, after, rep = overlay_v16()
    bound = E.bindings()
    old, new = run(old_m, after, bound, order), run(new_m, after, bound, order)
    diffs, moved = compare(old, new, after)
    hand = b9_by_hand(after, new_m)
    b9_new = {k: v for k, v in new["family_rows"].items() if v["group"] == "B9"}
    b9_pairs = [d for d in new["same_quantity_codes"] if d["kind"].startswith("REGISTER")]
    return {
        "schema": "URBAN_T637_READER", "rule": "R-T637-1 (reader R-T630-1 unchanged)", "task": "T-637",
        "overlay": "V3.0.58 + WIRING MANIFEST V16 (T-631, merged 01880ae3)",
        "inputs": {str(p.relative_to(ROOT)): E.sha256(p) for p in (MASTER_OLD, MASTER_NEW, M16.OUT_JSON)},
        "lines": len(after),
        "acceptance": {
            "uncoded_no_family_lines_1_56_0": sum(u["lines"] for u in new["uncoded"] if u["bucket"] == E.UNCODED_NO_FAMILY),
            "uncoded_no_family_lines_1_55_0": sum(u["lines"] for u in old["uncoded"] if u["bucket"] == E.UNCODED_NO_FAMILY),
            "b9_04_state_1_56_0": new["family_coverage"]["B9-04"]["overlay_state"],
            "b9_04_state_1_55_0": old["family_coverage"]["B9-04"]["overlay_state"],
            "b6_08_state_1_56_0": new["family_coverage"]["B6-08"]["overlay_state"],
            "register_beside_work_pairs_1_56_0": b9_pairs,
            "register_beside_work_pairs_1_55_0": [d for d in old["same_quantity_codes"] if d["kind"].startswith("REGISTER")],
            "other_family_rows_byte_equal": not diffs, "differences": diffs,
            "aggregation_re_adds_exactly": all(c["re_adds_exactly"] for c in new["aggregation_proof"]),
        },
        "moved_codes": moved,
        "uncoded_1_56_0": new["uncoded"], "uncoded_1_55_0": old["uncoded"],
        "b9_rows_1_56_0": b9_new,
        "b9_04_rows_1_55_0": {k: v for k, v in old["family_rows"].items() if k.startswith("B9-04")},
        "b6_08_rows_1_56_0": {k: v for k, v in new["family_rows"].items() if k.startswith("B6-08")},
        "b9_by_hand": hand,
        "aggregation_proof_1_56_0": new["aggregation_proof"],
        "flagged_overlay_rows": [r for r in rep["rows"] if r["status"] != "APPLIED"],
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def render_md(b):
    a = b["acceptance"]
    L = ["# T-637 reader: T-630 dry run on V3.0.58 + V16, master 1.55.0 vs 1.56.0 (generated)", "",
         f"Lines {b['lines']}. UNCODED (NO_FAMILY) lines: 1.55.0 {a['uncoded_no_family_lines_1_55_0']} -> 1.56.0 "
         f"{a['uncoded_no_family_lines_1_56_0']}. B9-04: {a['b9_04_state_1_55_0']} -> {a['b9_04_state_1_56_0']}. "
         f"B6-08: {a['b6_08_state_1_56_0']}. REGISTER_BESIDE_WORK pairs: {len(a['register_beside_work_pairs_1_55_0'])} "
         f"-> {len(a['register_beside_work_pairs_1_56_0'])}. Other family rows byte-equal: "
         f"{a['other_family_rows_byte_equal']}. Aggregation re-adds exactly: {a['aggregation_re_adds_exactly']}.", "",
         "## Codes moved by R-T637-1", "", "| Code | From | To | Lines |", "|---|---|---|---|"]
    for c, m in sorted(b["moved_codes"].items()):
        L.append(f"| {c} | {' / '.join(m['from'])} | {' / '.join(m['to'])} | {m['lines']} |")
    L += ["", "## B9 and B6-08 family rows (1.56.0)", "",
          "| Family x unit | Live | Released n | Released | HELD blank | HELD bounded | Re-add state |",
          "|---|---|---|---|---|---|---|"]
    for k, v in sorted(list(b["b9_rows_1_56_0"].items()) + list(b["b6_08_rows_1_56_0"].items())):
        L.append(f"| {k} | {v['live_lines']} | {v['released_n']} | {v['released']} | {v['held_blank_n']} | "
                 f"{v['held_bounded_n']} | {v['total'] if v['total'] is not None else v['total_state']} |")
    L += ["", "## B9 by hand from the lines", "", "| Code x unit | Released n | Released | HELD | Excluded |",
          "|---|---|---|---|---|"]
    for k, v in b["b9_by_hand"].items():
        L.append(f"| {k} | {v['released_n']} | {v['released']} | {v['held_n']} | {v['excluded_n']} |")
    L += ["", "Register codes (ARCH.WALL_PANEL / WALL_VOLUME / WALL_RUN) are UNCODED (NOT_A_BOQ_LINE) in 1.56.0: "
          "reported, never summed into B9-01; the material rows MAS.UNITS.* stay in pcs, never in the m2 work.", ""]
    return "\n".join(L)


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n"


def write_outputs():
    b = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    OUT_MD.write_text(render_md(b), encoding="utf-8")
    return b
