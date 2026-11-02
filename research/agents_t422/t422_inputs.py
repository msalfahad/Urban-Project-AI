"""T-422: the URBAN_V3044_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.44 (engine.source.arch_v3044), built ONLY from the
Checker-merged T-296 ledger files, each pinned by sha256 (an edited file stops the build). Every line id, window, edge,
sill, reading, range and room is READ from those files; typed here are only the reading -> action map below, the
template line of the missing room and the floor word.

  research/agents_t296/WINDOW_CAUSES_T296.csv  T-296 (MERGED 57c31ae4, Verifier 2026-10-25 16:08 UTC Gate A PASS a-h;
      own re-measure 1F-01 L-c021ae79 15.900 lm and W14 sill AGREE): per (line, window) the edge, the merged sill and
      the reading SKIRTED / NOT_SKIRTED / HELD with its status;
  research/agents_t296/LINE_LEDGER_T296.csv    the same merge: per line the candidate gross / net, its range line and
      the range high it held (the binding the module checks against the candidate: a stale line stops);
  research/agents_t296/ROOMS_T296.csv          the same merge: the dry room with no skirting line (MISSING, HELD).

Reading -> action (R-T422-1): SKIRTED (sill above the floor, DRAWING-CONFIRMED / PRINTED) -> RELEASE the listed halves
into the room's determinate line and count the room's range line in it; NOT_SKIRTED (floor glazing, or the window of an
owner wet room) -> NARROW its room's held range by the edge; HELD -> nothing (stays whole in the range).

    python3 -I research/agents_t422/t422_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WC = ROOT / "research/agents_t296/WINDOW_CAUSES_T296.csv"
LL = ROOT / "research/agents_t296/LINE_LEDGER_T296.csv"
RM = ROOT / "research/agents_t296/ROOMS_T296.csv"
PINS = {WC: "4ed39b9617faf5176ad619e34afcf345e38271ce8188d7c10a018ea9c98b6716",
        LL: "cd76f184d8bd1129e8ad63d8520a0c5e53b93baab1ddcfac729024e957dd9a80",
        RM: "2fc2ca2c1447e89a04f95bd040a7f9255db6940f29c0c837487cd3061bf9e7d5"}
MERGE = "57c31ae4b590dc9b710eeb445d37ffb7c1789c16"
CHECKER = ("Verifier 2026-10-25 16:08 UTC (Gate A PASS a-h; own re-measure 1F-01 L-c021ae79 15.900 lm and W14 sill "
           "1.40 AGREE; T-250 walk joins the 9 whole-room lines within 0.032 lm)")
SOURCES = {"T-296": {"task": "T-296", "file": "research/agents_t296/WINDOW_CAUSES_T296.csv; "
                                              "research/agents_t296/LINE_LEDGER_T296.csv; "
                                              "research/agents_t296/ROOMS_T296.csv",
                     "sha256": "; ".join(PINS[p] for p in (WC, LL, RM)), "merge_commit": MERGE,
                     "checker_run": CHECKER}}
# the T-296 NOT_SKIRTED 'why' -> the module's reason word (typed map; an unknown why stops)
REASON = (("floor-level glazing", "FLOOR_GLAZING"), ("window of a wet room", "WET_BASE"))
# the missing room: a 1F skirting line whose project / documents the new line carries (bound by the module)
MISSING_TEMPLATE = {"1F": "L-c021ae79a3740089c3fe"}
FLOORS = ("GF", "1F", "2F")
# range lines whose NOT_SKIRTED window a later merged package already took out (the ledger read V3.0.17): named, never
# applied twice. V3.0.21 (T-315, base ownership SPLIT on the T-296 reading, ASSUMED - OWNER-APPROVED Q-37 A / Q-48 A)
# took W09 1.500 (GF-07 wet-pantry frame, entities on face GF-07|GF-W16) out of the GF open-plan range: 7.831578 ->
# 6.331578 (= W02 alone, sill not established, stays held).
ALREADY_OUT = {("L-e7dcdc69e1a2b24f8616", "W09"): "out since ARCH_TAKEOFF_V3.0.21 (T-315 base-ownership SPLIT 1.500 lm "
                                                  "on the wet-pantry wall tile GF-07; range 7.831578 -> 6.331578)"}


def _rel(p):
    return str(p.relative_to(ROOT))


def _read(p):
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    if h != PINS[p]:
        raise SystemExit(f"{_rel(p)}: sha256 {h[:12]} is not the merged {PINS[p][:12]} (an edited ledger stops)")
    return list(csv.DictReader(b.decode("utf-8").splitlines()))


def _f(x):
    return None if x in (None, "") else float(x)


def _reason(why):
    for key, word in REASON:
        if key in why:
            return word
    raise SystemExit(f"NOT_SKIRTED reading with no known reason: {why[:80]!r}")


def build(project_id=None):
    wc, ll = _read(WC), {r["line_id"]: r for r in _read(LL)}
    releases, narrows, set_aside = {}, {}, []
    for r in wc:
        L = ll.get(r["line_id"])
        if L is None:
            raise SystemExit(f"{r['line_id']}: window row of a line the ledger does not carry")
        win = {"census_id": r["census_id"], "opening_id": r["opening_id"], "edge_lm": float(r["edge_lm"]),
               "sill_m": _f(r["sill"]), "status": r["status"], "why": r["why"]}
        if r["reading"] == "SKIRTED":
            if L["ledger_status"] == "NOT_APPLICABLE":
                raise SystemExit(f"{r['line_id']}: a SKIRTED window on a NOT_APPLICABLE line")
            row = releases.setdefault(r["line_id"], {
                "line_id": r["line_id"], "floor": L["floor"], "engine_room": L["engine_room"],
                "expect": {"gross": float(L["cand_gross"]), "measured_net": float(L["cand_net"])},
                "windows": [], "range_line": ({"line_id": L["range_line"],
                                               "expect": {"low": 0.0, "high": float(L["cand_range_hi"])}}
                                              if L["range_line"] else None),
                "ledger_after": float(L["ledger_hi"]), "source_tasks": ["T-296"]})
            row["windows"].append(win)
        elif r["reading"] == "NOT_SKIRTED":
            if L["ledger_status"] == "NOT_APPLICABLE":
                continue            # the pantry-part line: NOT_APPLICABLE since V3.0.21 (with its range line); no range left
            if not L["range_line"]:
                raise SystemExit(f"{r['line_id']}: a NOT_SKIRTED window with no range line to narrow")
            if (L["range_line"], r["census_id"]) in ALREADY_OUT:
                set_aside.append({"line_id": L["range_line"], "census_id": r["census_id"],
                                  "why": ALREADY_OUT[(L["range_line"], r["census_id"])]})
                continue
            row = narrows.setdefault(L["range_line"], {
                "line_id": L["range_line"], "of_line": r["line_id"], "floor": L["floor"],
                "engine_room": L["engine_room"], "expect": {"low": 0.0, "high": float(L["cand_range_hi"])},
                "windows": [], "source_tasks": ["T-296"]})
            row["windows"].append(dict(win, reason=_reason(r["why"])))
        elif r["reading"] != "HELD":
            raise SystemExit(f"{r['line_id']} {r['census_id']}: unknown reading {r['reading']}")
    # every released line's range line held exactly the released edges plus, at most, other windows of the room
    for r in releases.values():
        rel = round(sum(w["edge_lm"] for w in r["windows"]), 6)
        if abs(r["expect"]["measured_net"] + rel - r["ledger_after"]) > 0.0005:
            raise SystemExit(f"{r['line_id']}: net {r['expect']['measured_net']} + released {rel} is not the ledger's "
                             f"{r['ledger_after']}")
    missing = []
    for r in _read(RM):
        reason = r.get("reason") or ""
        if "MISSING" in reason and "NO skirting line" in reason:
            room = r["engine_rooms"]
            floor = room.split("-")[0]
            if floor not in FLOORS:
                raise SystemExit(f"{room}: floor word {floor!r}")
            missing.append({"engine_room": room, "floor": floor, "template_line": MISSING_TEMPLATE[floor],
                            "room_kind": "DRY", "engine_boundary_lm": _f(r["contour_m"]),
                            "why": reason, "source_tasks": ["T-296"]})
    return {"schema": "URBAN_V3044_INPUTS_V1", "project_id": project_id, "sources": list(SOURCES.values()),
            "releases": sorted(releases.values(), key=lambda x: x["line_id"]),
            "narrows": sorted(narrows.values(), key=lambda x: x["line_id"]), "missing": missing, "set_aside": set_aside}


if __name__ == "__main__":
    d = build(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps({"releases": [(r["line_id"], [w["census_id"] for w in r["windows"]],
                                    round(sum(w["edge_lm"] for w in r["windows"]), 6)) for r in d["releases"]],
                      "narrows": [(r["line_id"], [w["census_id"] for w in r["windows"]],
                                   round(sum(w["edge_lm"] for w in r["windows"]), 6)) for r in d["narrows"]],
                      "missing": [m["engine_room"] for m in d["missing"]], "set_aside": d["set_aside"]}, indent=1))
