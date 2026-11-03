"""T-479: the T-471 BOQ completeness matrix (research/agents_t471/t471_completeness.py, unchanged) re-run on the
registry 1.41.0 and the EIMP component register 1.1.0, line by line, from the T-479 line index of the candidate of
record. Read only: changes no quantity; writes only --out / --register-out.

Register 1.1.0 = register 1.0.0 (research/agents_t471/EIMP_REGISTER_DEV_VILLA.json, never edited) with the two
REGISTRY_GAP components resolved by registry 1.41.0, nothing else:
  - C-GAP-POOL-FINISH  -> C-B13-09, family B13-09 (the new pool water-face finish family); applicability, evidence,
                          level and item code unchanged;
  - C-GAP-EXTERIOR-AREA -> removed from the components: ARCH.EXTERIOR is declared NOT_A_BOQ_LINE by 1.41.0
                          (not_a_boq_line_codes, with evidence); its lines are reported in 'not_a_boq_lines' with that
                          evidence, never dropped and never summed into a component.
A line whose code is NOT_A_BOQ_LINE and that a component also selects is a DOUBLY_MAPPED_LINE (reported). A NOT_A_BOQ
code no family owns that the registry does not declare stays an UNMAPPED_LINE (T-471 rule, unchanged).

    python3 -I research/agents_t479/t479_completeness.py --index research/agents_t479/out/LINE_INDEX_V3_0_45.json
        --master rules/coverage/BOQ_FAMILY_MASTER_1.41.0.json --out OUT.json [--register-out REG.json]
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "research" / "agents_t469", ROOT / "research" / "agents_t471"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import t471_completeness as T471  # noqa: E402

REGISTER_1_0_0 = ROOT / "research/agents_t471/EIMP_REGISTER_DEV_VILLA.json"
GAP_TO_FAMILY = {"C-GAP-POOL-FINISH": ("C-B13-09", "B13-09")}
GAP_NOT_A_BOQ = {"C-GAP-EXTERIOR-AREA": "ARCH.EXTERIOR"}


def register_1_1_0(reg, master):
    new = copy.deepcopy(reg)
    new["version"] = "1.1.0"
    new["master_version"] = master.get("version")
    nab = master.get("not_a_boq_line_codes") or {}
    comps = []
    for c in new["components"]:
        cid = c["component_id"]
        if cid in GAP_TO_FAMILY:
            nid, fam = GAP_TO_FAMILY[cid]
            if fam not in {f["code"] for f in master["families"]}:
                raise ValueError(f"{cid}: family {fam} is not in registry {master.get('version')}")
            c = dict(c, component_id=nid, family=fam,
                     rules=f"registry {master.get('version')} family {fam} (T-479); no owner finish rule",
                     exceptions="finish not printed on any sheet: the line stays BLOCKED_RFI blank")
        elif cid in GAP_NOT_A_BOQ:
            if GAP_NOT_A_BOQ[cid] not in nab:
                raise ValueError(f"{cid}: {GAP_NOT_A_BOQ[cid]} is not declared NOT_A_BOQ_LINE in the registry")
            continue
        comps.append(c)
    new["components"] = comps
    # codes a family gained after register 1.0.0 was built (on registry 1.37.0; e.g. T-350 gave B1-02 .. B1-04 their
    # STR.EARTH.* codes in 1.38.0): a family with exactly ONE component hands them to it; a family with several
    # components is left as it is, so its new lines stay UNMAPPED_LINE (reported, never guessed onto a component)
    by_fam = {}
    for c in comps:
        by_fam.setdefault(c.get("family"), []).append(c)
    added = {}
    for f in master["families"]:
        cs = by_fam.get(f["code"]) or []
        have = {x for c in cs for x in c.get("item_codes") or ()}
        gain = [x for x in f.get("item_codes") or () if x not in have]
        if gain and len(cs) == 1:
            cs[0]["item_codes"] = list(cs[0].get("item_codes") or []) + gain
            added[cs[0]["component_id"]] = gain
    new["codes_added_from_registry"] = added
    for item, cids in new.get("owner_gate", {}).items():
        new["owner_gate"][item] = [GAP_TO_FAMILY.get(x, (x,))[0] for x in cids if x not in GAP_NOT_A_BOQ]
    return new


def index_to_lines(index):
    """the T-479 line index -> pseudo lines and classes for T-471 (VERIFIED = a binding WHOLE verdict only)."""
    lines, cls = [], {}
    for r in index["lines"]:
        ln = {"line_id": r["line_id"], "item_code": r["item_code"], "unit": r["unit"],
              "measured_net": r["measured_net"], "location": {"element_id": r.get("element_id")},
              "bounded_range": (None if r.get("held_low") is None or r.get("held_high") is None
                                else {"low": r["held_low"], "high": r["held_high"]})}
        k = r["class"]
        if k == T471.T469.RELEASED and (r.get("binding") or {}).get("binding") == "VERIFIED_WHOLE":
            k = T471.VERIFIED
        lines.append(ln)
        cls[r["line_id"]] = k
    return lines, cls


def run(reg, index, master):
    nab = master.get("not_a_boq_line_codes") or {}
    lines, cls = index_to_lines(index)
    keep = [ln for ln in lines if ln["item_code"] not in nab]
    apart = [ln for ln in lines if ln["item_code"] in nab]
    doc = T471.build(reg, keep, master, version=index.get("candidate_version"),
                     classes={ln["line_id"]: cls[ln["line_id"]] for ln in keep})
    for ln in apart:
        hit = [c["component_id"] for c in reg["components"] if T471._selects(c, ln)]
        if hit:
            doc["issues"].append({"kind": "DOUBLY_MAPPED_LINE", "line_id": ln["line_id"],
                                  "components": sorted(hit) + ["NOT_A_BOQ_LINE"]})
            doc["complete_map"] = False
    doc["not_a_boq_lines"] = {c: {"line_ids": sorted(ln["line_id"] for ln in apart if ln["item_code"] == c),
                                  "quantities": T471._quantities([ln for ln in apart if ln["item_code"] == c], cls),
                                  "evidence": nab[c].get("evidence")}
                              for c in sorted({ln["item_code"] for ln in apart})}
    doc["lines"] = len(lines)
    kinds = {}
    for i in doc["issues"]:
        kinds[i["kind"]] = kinds.get(i["kind"], 0) + 1
    doc["issue_counts"] = dict(sorted(kinds.items()))
    doc["granularity"] = "line (T-479 line index)"
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--index", required=True)
    ap.add_argument("--master", required=True)
    ap.add_argument("--register", default=str(REGISTER_1_0_0))
    ap.add_argument("--out", required=True)
    ap.add_argument("--register-out")
    a = ap.parse_args(argv)
    master = json.loads(Path(a.master).read_text(encoding="utf-8"))
    reg = register_1_1_0(json.loads(Path(a.register).read_text(encoding="utf-8")), master)
    if a.register_out:
        Path(a.register_out).write_text(json.dumps(reg, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    doc = run(reg, json.loads(Path(a.index).read_text(encoding="utf-8")), master)
    Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"T-479 completeness: {doc['components']} components, {doc['lines']} lines, states {doc['states']}, "
          f"issues {doc['issue_counts']}, complete_map={doc['complete_map']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
