"""REVIEW SET BINDING V1 (T-208) - settles the wet / dry CONDITIONAL review sets of an engine run by ANSWERED owner
rules, so a floor-area reference line can be scored like for like. Pure, stdlib only, NOT wired into any method; it
reads a run (BOQ_RELEASE_REPORT.json, ARCH_ROOMS.json, BOQ_LINES.json) and writes nothing unless asked.

Why: the released architectural method keeps a space whose type the drawing does not state (UP-WET-002 1.3.0: "a
basin alone does not make a space wet") as a REVIEW_CLASSIFICATION scenario set, mutually exclusive WET_SCOPE /
DRY_SCOPE, with its floor in NO line. The scorer (tools/alsenan_keymap.py) then answers the floor key HELD for every
such set, so the whole floor-area line is NOT YET MEASURED. An owner answer that classifies the space type already
exists for some sets; this module binds a set to a scenario ONLY through such an answer, and keeps it HELD otherwise.

    space_profile(room)                           -> the evidence a rule may test (fixture kinds, label class, issues)
    bind_set(scenario_set, room, rules, confirm)  -> URBAN_REVIEW_SET_BINDING_V1 record (scenario or HELD + reason)
    bind_run(release_report, rooms, rules, confirm) -> {"schema", "bindings": [...], "ignored_sets": [...]}
    key_rows(bindings_doc, key, key_items)        -> scorer rows for the key: bound sets with their scenario quantity
                                                     and status ASSUMED_OWNER_APPROVED, every other set HELD (qty None)
    floor_line(lines, bindings_doc, key_items)    -> released lines + bound sets per item and in total; the total is
                                                     None while any set holding the key is HELD (never a partial sum)

Rules (data, not code: ANSWERED_RULES below is the default library, every entry cites its owner source):
- Q-06 A (owner 2026-10-18, OWNER_QUESTIONS_ANSWERED.md Q-06): a basin-only hand-wash space (one or more wash basins,
  no water closet, shower, bath or urinal, no kitchen / laundry appliance) is WET: WET_SCOPE. Implemented for the
  candidate methods by engine/source/wet_room_evidence.py classify (BASIN_ONLY_HAND_WASH); here it settles the sets of
  the released run, which predates it.
Every binding is ASSUMED — OWNER-APPROVED (WORKFLOW_CONTROLS s.4: an approved fallback recorded in an answered owner
decision), never VERIFIED and never DRAWING-CONFIRMED by itself; the geometry status of the quantity is separate.

HELD, never a scenario by default (and NEVER dry by default):
- no answered rule matches the space's evidence (unclassified set);
- the room record is missing, carries a fixture conflict, or any non-basin fixture;
- a doorless cell is attached to the space (D-C3: a merged cell would take the wet scope silently) unless a boundary
  confirmation names that space;
- the space is a zone cut from an open space by drawn lines that are not walls (ZONE_FROM_DRAWN_LINES: the plan does
  not say a line is a finish boundary) unless a boundary confirmation names that space with its drawing check;
- the chosen scenario is missing from the set, or the set is not mutually exclusive;
- a key item is absent from the chosen scenario (that key's row only).
One physical strip, one line: in a bound WET_SCOPE the porcelain of a space with a door closure is the closure strip of
its doorless opening, which the run already carries as that opening's own ARCH.THRESHOLD line (finish held, Q-S6-1);
it is moved to "closure_strip" and never added to the floor key (the candidate path ARCH_TAKEOFF_V2.11 with
wet_room_evidence gives the same floor: wet tile only).
Sets of any other kind (e.g. DOOR_OWNER_MINIMUM) are listed as ignored, never bound.

Project-agnostic: no layer, room, coordinate or project name in code. A boundary confirmation is a project fact with
its source, passed in as data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCHEMA = "URBAN_REVIEW_SET_BINDING_V1"
ASSUMED = "ASSUMED_OWNER_APPROVED"
HELD = "HELD"
REVIEW_KIND = "REVIEW_CLASSIFICATION"
QUANTITY_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")      # tools/alsenan_keymap.py, UP-QTY-STATUS-001

STRIP_ITEM = "FIN.FLOOR.PORCELAIN [m2]"
BASIN = "BASIN"
NON_BASIN_FIXTURES = ("WC", "SHOWER", "BATH", "URINAL", "BIDET", "KITCHEN_SINK", "WASHING_MACHINE",
                      "KITCHEN_APPLIANCE", "IRONING_BOARD")

ANSWERED_RULES = (
    {"rule_id": "Q-06 A", "predicate": "BASIN_ONLY_HAND_WASH", "scenario": "WET_SCOPE",
     "source": "OWNER_QUESTIONS_ANSWERED.md Q-06 (owner 2026-10-18): basin-only hand-wash spaces are wet areas: "
               "porcelain floor, full-height wall porcelain, waterproofing, marble threshold"},
)


def _issue_codes(issue):
    """The issue codes of a room record ('CODE (rule): text; CODE: text')."""
    codes = []
    for part in str(issue or "").split(";"):
        head = part.strip().split(" ", 1)[0].split(":", 1)[0].strip()
        if head and head.upper() == head and "_" in head:
            codes.append(head)
    return codes


def space_profile(room):
    """What a rule may test, read from one ARCH_ROOMS room record (None when the record is missing)."""
    if room is None:
        return None
    ev = room.get("evidence") or {}
    kinds = [str(f.get("fixture") or "").upper() for f in ev.get("fixtures") or []]
    return {"room_id": room.get("room_id"), "floor": room.get("floor"), "class": room.get("class"),
            "codes": list(room.get("codes") or []), "fixture_kinds": kinds,
            "fixture_conflict": room.get("fixture_conflict"), "attached_cells": list(room.get("attached_cells") or []),
            "issue_codes": _issue_codes(room.get("issue")), "area_m2": room.get("area_m2"),
            "door_closures": int(room.get("door_closures") or 0)}


def _matches(predicate, prof):
    if predicate == "BASIN_ONLY_HAND_WASH":
        kinds = prof["fixture_kinds"]
        return (bool(kinds) and all(k == BASIN for k in kinds) and not prof["fixture_conflict"]
                and not (set(prof["codes"]) - {"HAND_WASH"}) and "WET_CLASSIFICATION_REVIEW" in prof["issue_codes"])
    raise ValueError(f"unknown predicate {predicate!r}")


def _held(s, reason, prof=None):
    return {"schema": SCHEMA, "set_id": s.get("set_id"), "subject": s.get("subject"), "status": HELD,
            "scenario": None, "rule_id": None, "source": None, "reason": reason, "quantities": None,
            "profile": prof}


def bind_set(scenario_set, room, rules=ANSWERED_RULES, confirmations=None):
    """One binding record for one REVIEW_CLASSIFICATION set."""
    s, confirmations = scenario_set, confirmations or {}
    prof = space_profile(room)
    if prof is None:
        return _held(s, "the room record of the set's subject is missing")
    if not s.get("mutually_exclusive"):
        return _held(s, "the set is not mutually exclusive: no single scenario can be chosen", prof)
    if prof["fixture_conflict"]:
        return _held(s, "fixture conflict on the space: its type is not established", prof)
    if any(k in NON_BASIN_FIXTURES for k in prof["fixture_kinds"]):
        return _held(s, "the space holds a non-basin fixture: not a basin-only space; no answered rule binds it", prof)
    conf = confirmations.get(s.get("subject"))
    if prof["attached_cells"] and not conf:
        return _held(s, "a doorless cell is attached to the space (D-C3): its scope is not confirmed", prof)
    if "ZONE_FROM_DRAWN_LINES" in prof["issue_codes"] and not conf:
        return _held(s, "zone cut by drawn lines that are not walls: the finish boundary is not confirmed", prof)
    hits = [r for r in rules if _matches(r["predicate"], prof)]
    if not hits:
        return _held(s, "no answered owner rule classifies this space (UP-WET-002 review stands): HELD, never dry "
                        "by default", prof)
    scen = {r["scenario"] for r in hits}
    if len(scen) != 1:
        return _held(s, "answered rules disagree on the scenario: " + ", ".join(sorted(scen)), prof)
    r = hits[0]
    if r["scenario"] not in (s.get("scenarios") or ()) or r["scenario"] not in (s.get("by_scenario") or {}):
        return _held(s, f"the set has no {r['scenario']} scenario", prof)
    q = dict(s["by_scenario"][r["scenario"]])
    strip = None
    if r["scenario"] == "WET_SCOPE" and prof["door_closures"] and STRIP_ITEM in q:
        # in a WET scenario the only porcelain is the closure strip of the space's doorless opening; that strip is
        # the opening's own threshold line (ARCH.THRESHOLD, Q-S6-1 / UP-THR-001), so it is counted once there
        strip = {"item": STRIP_ITEM, "m2": q.pop(STRIP_ITEM),
                 "reason": "doorway closure strip: carried by the opening's own threshold line, not the floor key"}
    return {"schema": SCHEMA, "set_id": s["set_id"], "subject": s.get("subject"), "status": ASSUMED,
            "scenario": r["scenario"], "rule_id": r["rule_id"], "source": r["source"],
            "reason": f"{r['predicate']} -> {r['scenario']} by {r['rule_id']}",
            "boundary_confirmation": conf, "quantities": q, "closure_strip": strip, "profile": prof}


def bind_run(release_report, rooms, rules=ANSWERED_RULES, confirmations=None):
    """Every CONDITIONAL set of a run: REVIEW_CLASSIFICATION sets bound or HELD, the other kinds ignored."""
    by_id = {r.get("room_id"): r for r in rooms}
    sets = (release_report or {}).get("categories", {}).get("CONDITIONAL", {}).get("scenario_sets", []) or []
    out, ignored = [], []
    for s in sets:
        if s.get("kind") != REVIEW_KIND:
            ignored.append({"set_id": s.get("set_id"), "kind": s.get("kind")})
            continue
        out.append(bind_set(s, by_id.get(s.get("subject")), rules, confirmations))
    return {"schema": SCHEMA, "method": "REVIEW_SET_BINDING_V1", "rules": [dict(r) for r in rules],
            "bindings": out, "ignored_sets": ignored}


def key_rows(doc, key, key_items):
    """Scorer rows (alsenan_keymap row shape) for every bound or held review set that carries a key item."""
    items, rows = set(key_items), []
    for b in doc["bindings"]:
        # a set answers the key when ANY scenario carries a key item: the held record keeps no quantities, so the
        # caller passes the sets from the release report for that test; here the bound quantity decides
        q = b.get("quantities")
        if b["status"] == ASSUMED:
            present = [i for i in items if i in q]
            if not present:
                continue
            missing = [i for i in items if i not in q]
            qty = round(sum(float(q[i]) for i in present), 6)
            rows.append({"id": f"COND:{b['set_id']}:{key}", "key": key, "qty": qty, "status": ASSUMED,
                         "rule_id": b["rule_id"], "items_absent_in_scenario": sorted(missing),
                         "surface": f"COND:{b['set_id']}"})
        else:
            rows.append({"id": f"COND:{b['set_id']}:{key}", "key": key, "qty": None, "status": HELD,
                         "reason": b["reason"], "surface": f"COND:{b['set_id']}"})
    return rows


def floor_line(lines, doc, key_items):
    """Released key lines + bound sets, per item and in total (total None while any review set is HELD)."""
    items = list(key_items)
    codes = {i.rsplit(" [", 1)[0]: i for i in items}
    rel = {i: 0.0 for i in items}
    held_lines = 0
    for ln in lines:
        i = codes.get(ln.get("item_code"))
        if i is None:
            continue
        if ln.get("evidence_state") in QUANTITY_STATES and ln.get("measured_net") is not None:
            rel[i] += float(ln["measured_net"])
        elif ln.get("evidence_state") not in ("NOT_APPLICABLE_WITH_EVIDENCE", "EXCLUDED_WITH_REASON"):
            held_lines += 1
    bound = {i: 0.0 for i in items}
    held_sets = []
    for b in doc["bindings"]:
        if b["status"] == ASSUMED:
            for i in items:
                bound[i] += float((b["quantities"] or {}).get(i, 0.0))
        else:
            held_sets.append(b["set_id"])
    r6 = lambda d: {k: round(v, 6) for k, v in d.items()}  # noqa: E731
    released, assumed = round(sum(rel.values()), 6), round(sum(bound.values()), 6)
    total = None if (held_sets or held_lines) else round(released + assumed, 6)
    return {"released_by_item": r6(rel), "released_m2": released, "assumed_by_item": r6(bound),
            "assumed_owner_approved_m2": assumed, "held_sets": held_sets, "held_lines": held_lines,
            "total_m2": total}


def run_dir(path, confirmations=None, key_items=("FIN.FLOOR.PORCELAIN [m2]", "FIN.FLOOR.WET_TILE [m2]")):
    p = Path(path)
    rr = json.loads((p / "BOQ_RELEASE_REPORT.json").read_text(encoding="utf-8"))
    rooms = json.loads((p / "ARCH_ROOMS.json").read_text(encoding="utf-8"))["rooms"]
    lines = json.loads((p / "BOQ_LINES.json").read_text(encoding="utf-8"))
    doc = bind_run(rr, rooms, ANSWERED_RULES, confirmations)
    return doc, floor_line(lines, doc, key_items)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("run", help="engine run directory (BOQ_RELEASE_REPORT.json, ARCH_ROOMS.json, BOQ_LINES.json)")
    ap.add_argument("--confirmations", help="boundary confirmations JSON {subject: {...}}")
    ap.add_argument("--out", help="write the binding document here")
    a = ap.parse_args(argv)
    conf = json.loads(Path(a.confirmations).read_text(encoding="utf-8"))["confirmations"] if a.confirmations else None
    doc, line = run_dir(a.run, conf)
    doc["floor_line"] = line
    text = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(json.dumps(line, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
