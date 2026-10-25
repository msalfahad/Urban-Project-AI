"""T-297 r2: the member DATUM JOIN between the concrete trade of candidate ARCH_TAKEOFF_V3.0.17 and the reinforcement
lines (rule LB-10, every villa; Checker 2026-10-25 15:34 F-T297-04: one member, one datum status across trades).

A column's main bars run over the storey interval and its links over the concrete height: both lengths rest on the same
top-of-member datum as the member's concrete. Where V3.0.17 HOLDS that concrete on a datum (D-39 roof datum, Q-54 B annex
roof datum), the bar length on it cannot be DRAWING_CONFIRMED: it is HELD, or a BOUND whose datum names the held datum.
Where V3.0.17 RE-BASES the concrete on a newly printed height (T-287 CB5: base +0.25, h 5.20), a bar figure on the old
height is superseded and HELD until re-derived. A NOT_PRESENT member carries no bar line other than NOT_APPLICABLE.

Inputs, merged files only, nothing re-measured:
  research/agents_t254/t254_inputs.py build()             the V3.0.17 per-line concrete actions (T-254 MERGED 7c49e890)
  research/agents_t293/FORMWORK_FACE_TO_LINE_T293.csv      the member -> candidate column line tie (T-293 part 1 MERGED)
  research/agents_t148/T148_T119_INPUT.csv                 the reinforcement members (mark, storey) of the hand ledger

The join is checked, not trusted: the member's printed mark and storey must equal the candidate element id's, every
tie is one member <-> one line, and the tied members of one stack keep one schedule-sheet offset per storey (s.2 of the
report); a NOT_PRESENT line has no tied member.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T293 = ROOT / "research/agents_t293/FORMWORK_FACE_TO_LINE_T293.csv"
T148 = ROOT / "research/agents_t148/T148_T119_INPUT.csv"

# bar groups whose length is the member's height / interval (the datum the concrete uses); laps (note 9 at the storey
# bottom), joint links and bar ends do not take their length from the member top
LENGTH_ON_HEIGHT = ("MAIN BARS", "LINKS 6 ")
HELD_DATUM_WORDS = ("D-39", "Q-54B")
# the planted 2F column is held in the candidate (BLOCKED_RFI) and its formwork r4 row names T-248's D-39 roof datum;
# T-254 does not list it (no concrete change in V3.0.17), so its datum is taken from the merged formwork r4 row
PLANTED_2F = {"line_id": "L-541c7e565bb93ecdb78b", "held_item": "D-39_ROOF_DATUM (T-248 via FORMWORK_R4 row 248; "
              "candidate line BLOCKED_RFI, planted column)"}


class JoinError(ValueError):
    """the join cannot be shown member by member; the ledger is refused"""


def _v3017_column_records():
    sys.path.insert(0, str(ROOT / "research/agents_t254"))
    import t254_inputs as T  # noqa: E402
    return [r for r in T.build()["records"] if r["item_code"] == "STR.CONC.COLUMN"]


def _mark_storey(eid):
    m = re.search(r":(C[\w.]*)@(\d+),(\d+)\|(\w+)$", eid or "")
    return (m.group(1), m.group(4), int(m.group(2)), int(m.group(3))) if m else (None, None, None, None)


def ties():
    """member id -> candidate column line id (T-293 TIED rows, COLUMN element); one line per member"""
    out = {}
    for r in csv.DictReader(T293.open(encoding="utf-8")):
        if r["element"] != "COLUMN" or r["tie"] != "TIED" or not r["members"].startswith("COLUMN:"):
            continue
        mem = r["members"].split(":", 1)[1]
        prev = out.get(mem)
        if prev and prev[0] != r["line_id"]:
            raise JoinError(f"{mem} tied to two lines {prev[0]} / {r['line_id']}")
        out[mem] = (r["line_id"], r["line_element_id"], r["line_state"])
    return out


def build_join(records=None):
    """-> list of join rows for every V3.0.17 column line that is HELD on a datum, RE-BASED or NOT_PRESENT, plus the
    planted 2F column; each with its reinforcement member (or none) and the datum effect"""
    records = records if records is not None else _v3017_column_records()
    members = {r["id"]: r for r in csv.DictReader(T148.open(encoding="utf-8"))}
    tie = ties()
    by_line = {}
    for mem, (lid, eid, st) in tie.items():
        if lid in by_line:
            raise JoinError(f"line {lid} tied to two members {by_line[lid][0]} / {mem}")
        by_line[lid] = (mem, eid, st)
    rows = []
    recs = list(records) + [{"line_id": PLANTED_2F["line_id"], "element_id": "HL:PLANTED_COLUMN:PC-2F:CONCRETE",
                             "group": "COL_PLANTED_2F", "action": "HOLD", "held_item": PLANTED_2F["held_item"]}]
    for r in recs:
        act, held = r["action"], r.get("held_item") or ""
        if act == "HOLD" and not any(w in held for w in HELD_DATUM_WORDS):
            continue                                       # held for a reason that is not the member's datum
        if act == "REBASE" and r["group"] == "COL_PLANTED_1F":
            continue                                       # VERIFIED solid on two printed levels: no datum change here
        if act not in ("HOLD", "REBASE", "NOT_PRESENT"):
            continue
        mem = by_line.get(r["line_id"])
        if act == "NOT_PRESENT":
            if mem:
                raise JoinError(f"NOT_PRESENT line {r['line_id']} has a reinforcement member {mem[0]}")
            rows.append({"line_id": r["line_id"], "element_id": r["element_id"], "group": r["group"], "action": act,
                         "member": None, "length_datum": "NOT_PRESENT (T-256: no sheet draws the member)",
                         "length_datum_status": "NOT_PRESENT"})
            continue
        if not mem:
            raise JoinError(f"{r['group']} line {r['line_id']} ({r['element_id']}) has no tied reinforcement member")
        m = members.get(mem[0])
        if m is None:
            raise JoinError(f"{mem[0]} is not a T-148 member")
        if r["group"] != "COL_PLANTED_2F":
            mk, sto, _, _ = _mark_storey(r["element_id"])
            if (mk, sto) != (m["mark"], m["storey"]):
                raise JoinError(f"{mem[0]} {m['mark']} {m['storey']} != {r['element_id']}")
        elif not m["mark"].startswith("P.C") or m["storey"] != "2F":
            raise JoinError(f"{mem[0]} is not the planted 2F column")
        if act == "HOLD":
            datum, dst = f"{held} (V3.0.17 concrete line {r['line_id']} HELD)", "HELD"
        else:
            datum = (f"concrete re-based in V3.0.17 ({r.get('status')}, T-287: base +0.25, h 5.20) on line "
                     f"{r['line_id']}; the bar figure's height {m['height']} / interval {m['interval']} is superseded")
            dst = "SUPERSEDED"
        rows.append({"line_id": r["line_id"], "element_id": r["element_id"], "group": r["group"], "action": act,
                     "member": mem[0], "mark": m["mark"], "storey": m["storey"], "interval_m": m["interval"],
                     "height_m": m["height"], "length_datum": datum, "length_datum_status": dst})
    rows.sort(key=lambda x: (x["group"], x["member"] or "", x["line_id"]))
    stack_check(rows, tie, members)
    return rows


STOREY_INDEX = {"GF": 0, "1F": 1, "2F": 2}
# a stack's centroid may move where its section changes (COL-2F-55 C9: 1F 20x90 -> 2F 20x70 moves it 0.15 m); the tie is
# still unambiguous while the closest two columns of one storey stand more than 3 x this apart (asserted)
STACK_TOL_M = 0.30


def storey_shift(tie, members):
    """the hand ledger draws each storey plan in its own panel, shifted along x by one constant; the candidate's column
    element id carries ONE position per stack (the same xy on every storey). The shift is the modal plan-x step between
    members tied to one candidate position on adjacent storeys (votes reported)."""
    by_xy = {}
    for mem, (lid, eid, st) in tie.items():
        m = members.get(mem)
        mk, sto, x, y = _mark_storey(eid)
        if m is None or x is None or sto not in STOREY_INDEX:
            continue
        by_xy.setdefault((x, y), []).append((STOREY_INDEX[sto], float(m["x"]), float(m["y"]), mem))
    votes = {}
    for grp in by_xy.values():
        grp.sort()
        for a, b in zip(grp, grp[1:]):
            if b[0] - a[0] == 1:
                k = round(a[1] - b[1], 3)
                votes[k] = votes.get(k, 0) + 1
    if not votes:
        raise JoinError("no stack spans two storeys: the storey shift cannot be shown")
    shift = max(votes, key=votes.get)
    return shift, votes[shift], sum(votes.values()), by_xy


def stack_check(rows, tie, members):
    """second, independent check of every tie used here: the members tied to ONE candidate position (one stack) must sit
    at one plan position once the constant storey shift is removed (same plan y, plan x + storey index x shift equal,
    within STACK_TOL_M). A crossed tie between two columns of one mark on one storey fails it."""
    shift, n, total, by_xy = storey_shift(tie, members)
    for sto in STOREY_INDEX:
        pts = [(float(m["x"]), float(m["y"])) for m in members.values() if m["storey"] == sto]
        if len(pts) < 2:
            continue
        gap = min(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 for i, a in enumerate(pts) for b in pts[i + 1:])
        if gap <= 3 * STACK_TOL_M:
            raise JoinError(f"{sto}: two columns {gap:.3f} m apart: the stack tolerance cannot separate them")
    pos_of = {mem: xy for xy, grp in by_xy.items() for (_, _, _, mem) in grp}
    for r in rows:
        mem = r.get("member")
        if not mem or mem not in pos_of:
            continue
        grp = by_xy[pos_of[mem]]
        base = [(px + i * shift, py) for (i, px, py, _) in grp]
        for bx, by in base:
            if abs(bx - base[0][0]) > STACK_TOL_M or abs(by - base[0][1]) > STACK_TOL_M:
                raise JoinError(f"{mem}: stack at sheet {pos_of[mem]} is not one plan position: {grp}")
        r["stack_members"] = sorted(g[3] for g in grp)
    for r in rows:
        r["storey_shift_m"] = shift
        r["storey_shift_votes"] = f"{n} / {total}"
    return rows


def effect_of(join_rows):
    """member id -> (length_datum, length_datum_status) for the bar groups LENGTH_ON_HEIGHT"""
    return {r["member"]: (r["length_datum"], r["length_datum_status"]) for r in join_rows if r.get("member")}


def length_on_height(bar_group):
    return bar_group.startswith(LENGTH_ON_HEIGHT)
