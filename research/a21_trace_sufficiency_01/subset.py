"""Apply the frozen subset rule. Declared in protocol.py, executed here.

No A21 answer is read. The inputs are the case's own declared subject,
which predates the baseline, and the frozen E1.4 boundary-chain
composition - the same channel the original pilot selection used.

    python3 -m research.a21_trace_sufficiency_01.subset
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from research.a21_trace_sufficiency_01 import protocol as P

E14 = Path("data/runs/7757/e1_4/E1_4_PHYSICAL_BOUNDARY_CHAIN_REGISTER.json")
PILOT = Path("data/experiments/A21_VISUAL_QS_PILOT_01/"
             "PILOT_CASE_SELECTION.json")
OUT = Path("data/experiments/A21_TRACE_SUFFICIENCY_01")

MATERIAL_ELEMENTS = ("MATERIAL_WALL_FACE", "MATERIAL_CONTINUITY_SPAN")

DECLARED_SUBJECT = {
    "CASE-4-STAIR": "the stair rising from the ground floor",
    "CASE-5-EXTERNAL-FACADE": "external plaster on one facade",
    "CASE-6-ROOF-PARAPET": "the roof parapet on the CASE-5 facade",
}


def chain_composition() -> dict:
    ch = json.loads(E14.read_text("utf-8"))
    sel = json.loads(PILOT.read_text("utf-8"))
    want = {c["CANDIDATE_ID"]: c["CASE_ID"]
            for c in sel["ROOM_CASES"] if c.get("CANDIDATE_ID")}
    out = {}
    for c in ch["CANDIDATES"]:
        cid = want.get(c["CANDIDATE_ID"])
        if not cid:
            continue
        els = (c.get("CHAIN") or {}).get("CHAIN") or []
        k = Counter(e["CHAIN_ELEMENT"] for e in els)
        total = sum(k.values())
        material = sum(k.get(m, 0) for m in MATERIAL_ELEMENTS)
        out[cid] = {
            "CANDIDATE_ID": c["CANDIDATE_ID"],
            "CHAIN_ELEMENTS": total,
            "COMPOSITION": dict(k),
            "MATERIAL_FRACTION": round(material / total, 4) if total else None,
            "NON_MATERIAL_FRACTION": (
                round(1 - material / total, 4) if total else None),
            "DOOR_PORTALS": k.get("DOOR_PORTAL", 0),
        }
    return out


def select() -> dict:
    comp = chain_composition()
    rooms = sorted(comp)

    assign = {}
    assign["ORDINARY_WALL_WITH_PRINTED_DIMENSION"] = max(
        rooms, key=lambda c: (comp[c]["MATERIAL_FRACTION"], c))
    with_doors = [c for c in rooms if comp[c]["DOOR_PORTALS"] > 0]
    assign["AN_OPENING"] = sorted(with_doors)[0] if with_doors else None
    assign["AN_AMBIGUOUS_OR_OPEN_BOUNDARY"] = max(
        rooms, key=lambda c: (comp[c]["NON_MATERIAL_FRACTION"], c))
    assign["A_STAIR_OR_VERTICAL_CONDITION"] = "CASE-4-STAIR"
    assign["A_PARAPET_BALUSTRADE_DISTINCTION"] = "CASE-6-ROOF-PARAPET"

    subset = sorted({v for v in assign.values() if v})
    excluded = sorted(set(list(comp) + list(DECLARED_SUBJECT)) - set(subset))

    body = {
        "PHASE_ID": P.PHASE_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "ARTIFACT": "PILOT_SUBSET_SELECTION",
        "SUBSET_RULE": P.SUBSET_RULE,
        "SUBSET_ASSIGNMENT_RULE": P.SUBSET_ASSIGNMENT_RULE,
        "FROZEN_BEFORE_ANY_TRACE_WAS_GENERATED": True,
        "NO_A21_ANSWER_WAS_READ": True,
        "E1_4_CHAIN_COMPOSITION_USED_FOR_SELECTION_ONLY": comp,
        "ASSIGNMENT": assign,
        "SUBSET": subset,
        "EXCLUDED": excluded,
        "WHY_CASE_5_FALLS_OUT": P.WHY_CASE_5_FALLS_OUT,
        "A_HONEST_NOTE_ON_THE_OPENNESS_RULE":
            P.A_HONEST_NOTE_ON_THE_OPENNESS_RULE,
        "COVERAGE_IS_SATISFIED_IN_FACT": (
            "whatever label the openness rule attaches, the subset "
            "contains every room case, so the genuinely open-plan "
            "boundaries are in it either way"),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "PILOT_SUBSET_SELECTION.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    import hashlib
    return {"SUBSET": subset, "EXCLUDED": excluded, "ASSIGNMENT": assign,
            "SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}


if __name__ == "__main__":
    print(json.dumps(select(), indent=2))
