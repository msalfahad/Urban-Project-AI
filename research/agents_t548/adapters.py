"""T-548 adapters: normalise the MERGED reconciliation reports into statement sections (no new quantity).

Each adapter reads only committed research outputs and the V3.0.57 line index; every class assignment is an explicit
table entry with its source (a row the table does not know is refused, so a changed report is never silently
re-classed). No drawing, workbook or client data is read or stored here.

T-541 (MERGED 322c1409, R-T541-1): its own causes are already the statement classes (ENGINE_RIGHT / RULE_DIFFERENCE /
HELD / TOLERANCE / UNRESOLVED); the adapter adds the engine status of each row and the held line ids.

T-534 (MERGED, R-T534-3): its reference is the Q-53 text figure 39.485 m2 (the T-086 hand table), NOT a freelancer
row (T-534 s.5: the freelancer has no stair cement / sand rows, T-511 s.5); its causes COUNT / WIDTH / DEPTH_OR_HEIGHT
/ POLYGON / SCOPE are mapped per key below with T-534's own verdicts (s.3, s.5). Its sign is engine - reference; the
statement's is reference - engine, so every part is negated.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T541_JSON = ROOT / "research/agents_t541/out/T541_ROOF_WP_RECONCILE.json"
T541_INPUTS = ROOT / "research/agents_t541/t541_inputs.py"
T534_JSON = ROOT / "research/agents_t534/out/T534_STAIR_BED_RECONCILE.json"
INDEX = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"


class AdapterError(ValueError):
    pass


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def load_index(path: Path = INDEX) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    return {ln["line_id"]: ln for ln in d["lines"]}


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)  # type: ignore[union-attr]
    return m


def bind_to_index(sec: dict, index: dict) -> list[str]:
    """Every valued line found in the index must be RELEASED with the same measured net; every held line HELD.
    Returns the valued line ids that are not in the V3.0.57 index (named in the statement, never dropped)."""
    absent = []
    for ln in sec["engine"]["valued_lines"]:
        ix = index.get(ln["line_id"])
        if ix is None:
            absent.append(ln["line_id"])
            continue
        if ix["class"] != "RELEASED" or Decimal(str(ix["measured_net"])) != Decimal(str(ln["qty"])):
            raise AdapterError(f"{sec['section_id']}: valued line {ln['line_id']} is {ix['class']} "
                               f"{ix['measured_net']} in the index, report says {ln['qty']}")
        if ix["unit"] != sec["unit"]:
            raise AdapterError(f"{sec['section_id']}: line {ln['line_id']} unit {ix['unit']} in the index")
    for ln in sec["engine"]["held_lines"]:
        ix = index.get(ln["line_id"])
        if ix is None or ix["class"] != "HELD":
            raise AdapterError(f"{sec['section_id']}: held line {ln['line_id']} is not HELD in the index")
    for ln in sec["engine"].get("excluded_lines", []):
        ix = index.get(ln["line_id"])
        if ix is None or ix["class"] != "EXCLUDED":
            raise AdapterError(f"{sec['section_id']}: excluded line {ln['line_id']} is not EXCLUDED in the index")
    return absent


# ------------------------------------------------------------------------------------------------ T-541 -------------
T541_HELD = {"membrane": "L-3e8fe55da71851816dd4", "upturn": "L-aac1f35e08f85b643692"}  # 2F-ROOF-TOP (Q-34)
# row name prefix -> engine status (VALUED: the component lies in the engine's valued lines; NONE: not in the engine
# by the owner rule or scope; HELD: in a held line). Source: T-541 report s.2 / s.3 and t541_inputs.py.
T541_STATUS = {
    "membrane": {
        "2F block top roof +13.90": "HELD",
        "third dome footprint": "NONE",           # Q-29: membrane stops at the skylight whatever the Q-34 hold
        "two +9.70 dome footprints": "NONE",      # Q-24 / Q-29 deduction in the engine
        "engine arc discretisation": "VALUED",    # chords of the valued AT379 line
        "pool-court slab": "VALUED",              # L-eff54f96 / L-2361d6ec
        "RESIDUAL": "NONE",
    },
    "upturn": {
        "2F block top roof parapet": "HELD",
        "two +9.70 dome rings": "VALUED",         # in the valued AT379 upturn line
        "engine arc discretisation": "VALUED",
        "pool-court upturns": "VALUED",
        "RESIDUAL": "NONE",
    },
}
T541_TRADE = "B8 roof waterproofing"
T541_CODES = {"membrane": ["FIN.WP.ROOF"], "upturn": ["FIN.WP.ROOF_UPTURN"]}


def t541_sections(json_path: Path = T541_JSON, inputs_path: Path = T541_INPUTS) -> list[dict]:
    d = json.loads(json_path.read_text(encoding="utf-8"))
    inp = _load_module(inputs_path, "t548_t541_inputs")
    lines = {"membrane": inp.ENGINE_M2, "upturn": inp.ENGINE_LM}
    out = []
    for part in ("membrane", "upturn"):
        p = d[part]
        rows = []
        for r in p["rows"]:
            st = [v for k, v in T541_STATUS[part].items() if r["name"].startswith(k)]
            if len(st) != 1:
                raise AdapterError(f"T-541 {part}: row {r['name']!r} not in the adapter table")
            rows.append({"name": r["name"], "delta": r["delta"], "unit": r["unit"], "class": r["cause"],
                         "source_cause": r["cause"], "engine_status": st[0],
                         "held_line_ids": [T541_HELD[part]] if st[0] == "HELD" else [],
                         "source": r["source"], "note": r["note"]})
        out.append({
            "section_id": f"T-541/{part}", "report": "T-541", "trade": T541_TRADE, "item_codes": T541_CODES[part],
            "unit": p["unit"],
            "reference": {"kind": "FREELANCER", "total": p["freelancer_total"], "unit": p["unit"],
                          "basis": "freelancer waterproofing sheet, one typed row 'roofs and annexes' (T-541 s.1, "
                                   "F-T541-1; Drive 'Alsenan chalet project'); no sub-rows"},
            "engine": {"valued_total": p["engine_total"],
                       "valued_lines": [{"line_id": x["line_id"], "qty": x["qty"], "unit": x["unit"]}
                                        for x in lines[part]],
                       "held_lines": [{"line_id": T541_HELD[part], "low": None, "high": None,
                                       "reason": "2F-ROOF-TOP HELD (Q-34 parked); no engine bound"}],
                       "excluded_lines": []},
            "rows": rows,
        })
    return out


# ------------------------------------------------------------------------------------------------ T-534 -------------
T534_TRADE = "B7 stair marble bed"
# (key, surface) of a SCOPE part -> (class, engine status, held line ids, fix row, why). Source: T-534 s.3 / s.5 / s.7
# and the RECONCILE_A_TO_B notes; the held ids are the candidate's own HELD lines of that key and surface.
T534_SCOPE = {
    ("D1", "RISER"): ("HELD", "HELD", ["L-8938aa3b25bf605e4b9d"], None, "candidate riser line HELD"),
    ("MS1-L", "RISER"): ("HELD", "HELD", ["L-ecc450d6cc865617f8f6"], None, "candidate riser line HELD"),
    ("MS1-U", "RISER"): ("HELD", "HELD", ["L-07e0855f961a839c1277"], None, "candidate riser line HELD"),
    ("MS2-L", "RISER"): ("HELD", "HELD", ["L-0f060e9951c28c4cf074"], None, "candidate riser line HELD"),
    ("MS2-U", "RISER"): ("HELD", "HELD", ["L-12f56cbfe750f8b30c41"], None, "candidate riser line HELD"),
    ("MS2-TR", "RISER"): ("HELD", "HELD", ["L-0f060e9951c28c4cf074"], None,
                          "closing riser inside the HELD MS2-L riser line; position HELD"),
    ("MS2-LD", "LANDING"): ("HELD", "HELD", ["L-5d2be30dd8d2ffeacc42"], None, "only inside the HELD 2F bound"),
    ("MS1-LD", "LANDING"): ("ENGINE_WRONG", "NONE", [], "T-502",
                            "no candidate line for a drawn landing (T-493 F-3 silent omission); T-502 adds it"),
    ("1F-ARR", "LANDING"): ("RULE_DIFFERENCE", "VALUED", [], None, "Q-66 B answered after the T-086 reference"),
    ("E1-LD", "LANDING"): ("RULE_DIFFERENCE", "VALUED", [], None,
                           "reference counted the top E1 step as a tread, no entrance landing (T-534 s.5 scope)"),
    ("RS-S", "TREAD"): ("RULE_DIFFERENCE", "VALUED", [], None, "Q-50 A cond answered after the T-086 reference"),
    ("RS-A", "TREAD"): ("RULE_DIFFERENCE", "VALUED", [], None, "Q-50 A cond answered after the T-086 reference"),
}
# measurement causes: the candidate's released lines agree with the drawing (T-534 s.3 F-T534-1, s.5 ENGINE_RIGHT on
# the measurement; B_to_C within the polygon residuals); POLYGON = the candidate polygon vs printed arithmetic.
T534_MEASURE = {"COUNT": "ENGINE_RIGHT", "WIDTH": "ENGINE_RIGHT", "DEPTH_OR_HEIGHT": "ENGINE_RIGHT",
                "POLYGON": "TOLERANCE"}


def t534_sections(json_path: Path = T534_JSON) -> list[dict]:
    d = json.loads(json_path.read_text(encoding="utf-8"))
    a2b = d["reconcile"]["A_to_B"]
    if Decimal(str(a2b["unexplained_m2"])) != 0:
        raise AdapterError("T-534 A_to_B carries an unexplained rest; refused")
    b = d["B_candidate"]
    valued = [{"line_id": x["line_id"], "qty": str(x["net"]), "unit": "m2"} for x in b["lines"]
              if x["class"] == "RELEASED"]
    held = [{"line_id": x["line_id"], "low": None if x["bound"][0] is None else str(x["bound"][0]),
             "high": None if x["bound"][1] is None else str(x["bound"][1]), "reason": x["note"]}
            for x in b["held_lines"] if x["class"] == "HELD"]
    excluded = [{"line_id": x["line_id"]} for x in b["held_lines"] if x["class"] == "EXCLUDED"]
    rows = []
    for r in a2b["rows"]:
        for c in r["causes"]:
            part = -Decimal(str(c["m2"]))  # statement sign: reference - engine
            name = f"{r['key']} {r['surface']} {c['cause']}"
            if c["cause"] == "SCOPE":
                k = (r["key"], r["surface"])
                if k not in T534_SCOPE:
                    raise AdapterError(f"T-534: scope part {k} not in the adapter table")
                cls, est, ids, fix, why = T534_SCOPE[k]
            elif c["cause"] in T534_MEASURE:
                cls, est, ids, fix, why = T534_MEASURE[c["cause"]], "VALUED", [], None, c.get("note") or ""
            else:
                raise AdapterError(f"T-534: cause {c['cause']!r} not in the adapter table")
            rows.append({"name": name, "delta": str(part), "unit": "m2", "class": cls, "source_cause": c["cause"],
                         "engine_status": est, "held_line_ids": ids, "fix_row": fix,
                         "source": "research/agents_t534/out RECONCILE_A_TO_B (T-534 s.3)", "note": why})
    return [{
        "section_id": "T-534/stair-bed", "report": "T-534", "trade": T534_TRADE,
        "item_codes": ["FIN.MARBLE.TREAD", "FIN.MARBLE.RISER", "FIN.MARBLE.LANDING"], "unit": "m2",
        "reference": {"kind": "OWNER_QUESTION_FIGURE", "total": str(a2b["a_m2"]), "unit": "m2",
                      "basis": "Q-53 text 39.49 m2 = the T-086 hand table (39.485); freelancer: no stair bed / "
                               "cement / sand row (T-534 s.5, T-511 s.5)"},
        "engine": {"valued_total": str(a2b["b_m2"]), "valued_lines": valued, "held_lines": held,
                   "excluded_lines": excluded},
        "rows": rows,
    }]


def all_sections() -> tuple[list[dict], dict]:
    index = load_index()
    secs = t541_sections() + t534_sections()
    absent = {x["section_id"]: bind_to_index(x, index) for x in secs}
    prov = {"inputs": {rel(p): sha(p) for p in (T541_JSON, T541_INPUTS, T534_JSON, INDEX)},
            "valued_lines_not_in_V3_0_57_index": absent,
            "candidate_note": "T-534 lines from the V3.0.57 line index; T-541 adds the five V3.0.58 pool-court lines "
                              "(T-507) at their T-529 / T-536 values (t541_inputs.py)"}
    return secs, prov
