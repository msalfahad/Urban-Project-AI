"""T-293 formwork face-to-line ledger: rules (research scope, any villa; nothing wired, no BOQ line changed).

A formed face is the concrete surface cast against a form. It belongs to the concrete member it bounds, and the BOQ line
that owns that member's concrete is the line its formwork is reported beside (one element, several geometries: ERS s.3).
This module ties every face record of a merged formwork ledger to exactly one candidate concrete line id and proves the
tie closes (residual 0 m2 per status, per alternative, per method), without changing any face quantity.

Rules written here (proposed; provenance T-293, built on T-163 r3 / T-264 r4 / T-282 r3 / T-289):

R-FW-LINE-1   every face record appears once (face id unique); it is tied to the ONE candidate concrete line that owns
              its member. A record naming two members is refused (split it per member first). A member that two
              candidate lines share (the candidate split one drawn member over two lines with no length per line) is
              listed SPLIT_UNRESOLVED, HELD by name, its quantity kept, never divided by a guess.
R-FW-LINE-2   a member with no candidate concrete line is listed NO_CANDIDATE_LINE with the reason; its faces are kept
              with their own status (never dropped, never 0).
R-FW-LINE-3   a face cast against earth or blinding is not FORMED unless the record names the printed detail that forms
              it: contact EARTH booked as FORMED (outside an OQ-10 alternative) is refused. OQ-10 alternatives (FORMED /
              EARTH_CAST) stay two alternatives, never summed, never chosen.
R-FW-LINE-4   a face whose depth / height is not printed for its member (basis UNPRINTED) carries no quantity: HELD,
              blank, its range kept. A basis taken from a task the Checker has not merged is PENDING, blank.
R-FW-LINE-5   the face takes its own status from the formwork ledger revision it names (R-FW-STATUS-1) and carries the
              concrete line's own state beside it (a BLOCKED / HELD concrete line is shown as such, never as measured).
R-FW-LINE-6   closure: for every (status, alternative, method) the sum of the tied faces + the faces named in no line =
              the sum of the source rows; m2, low and high separately; residual 0.000 m2 (tolerance 0.0005).
"""

from __future__ import annotations

import collections
import math

SCHEMA = "T293_FORMWORK_FACE_TO_LINE_V1"
CONSUMER_SCHEMA = "T293_FORMWORK_BY_CONCRETE_LINE_V1"
TOL = 0.0005

TIED = "TIED"
NO_LINE = "NO_CANDIDATE_LINE"
SPLIT = "SPLIT_UNRESOLVED"
NAMED = "NAMED_NOT_TIED"          # aggregate rows of a later part (listed with their quantity, not tied in this part)
INFO = "INFO_NOT_A_QUANTITY"
SCENARIO = "SCENARIO_NOT_IN_CANDIDATE"

CONTACTS = ("FORM", "EARTH", "OQ10", "NONE")
UNPRINTED = "UNPRINTED"


class Refused(ValueError):
    pass


def _num(v):
    if v is None or v == "":
        return None
    x = float(v)
    if math.isnan(x):
        raise Refused("NaN quantity")
    return x


def check_face(f: dict) -> dict:
    """validate one face record and return it with its quantity fields normalised (R-FW-LINE-3 / -4)"""
    for k in ("face_id", "revision", "status", "members"):
        if f.get(k) in (None, "", []):
            raise Refused(f"face {f.get('face_id')!r}: missing {k}")
    if f.get("unit", "m2") != "m2":
        raise Refused(f"face {f['face_id']}: unit {f.get('unit')!r} is not m2")
    if len(f["members"]) != 1:
        raise Refused(f"face {f['face_id']}: booked to {len(f['members'])} members {f['members']} (split it per member)")
    c = f.get("contact", "FORM")
    if c not in CONTACTS:
        raise Refused(f"face {f['face_id']}: unknown contact {c!r}")
    alt = f.get("alternative") or ""
    if c == "EARTH" and "FORMED" in (f.get("item") or "").upper().split() and not alt.startswith("OQ10") \
            and not f.get("forming_detail"):
        raise Refused(f"face {f['face_id']}: cast against earth booked as FORMED without a printed forming detail")
    if c == "EARTH" and alt == "OQ10_FORMED":
        pass                                  # the OQ-10 FORMED alternative is a named alternative, never a fact
    g = dict(f)
    g["status_in"] = f["status"]
    g["m2"], g["lo"], g["hi"] = _num(f.get("m2")), _num(f.get("lo")), _num(f.get("hi"))
    if g["lo"] is not None and g["hi"] is not None and g["lo"] > g["hi"] + TOL:
        raise Refused(f"face {f['face_id']}: range low {g['lo']} above high {g['hi']}")
    if f.get("basis") == UNPRINTED and g["m2"] is not None:
        g["held_from"], g["m2"], g["status"] = g["m2"], None, "HELD"
        g["held_reason"] = "depth / height not printed for this member (R-FW-LINE-4)"
    if f.get("basis_task_merged") is False:
        g["pending_from"], g["m2"], g["status"] = g["m2"], None, "PENDING-VERIFICATION"
        g["held_reason"] = f"basis from {f.get('basis_task')} not merged (R-FW-LINE-4)"
    if g["status"] == "HELD" and g["m2"] is not None:
        raise Refused(f"face {f['face_id']}: HELD with a quantity {g['m2']} (a held face is blank, range only)")
    return g


def tie(faces: list, binding: dict, lines: dict, named: dict | None = None, source: list | None = None) -> dict:
    """faces: face records; binding: member -> list of candidate line ids (empty / missing = no line, reason in
    binding['_reason'][member]); lines: line id -> candidate line (item_code, element_id, state); named: face id ->
    (tie kind, reason) for rows deliberately not tied in this part (INFO, scenario, later-part aggregates)"""
    named = named or {}
    reasons = binding.get("_reason", {})
    seen, rows = set(), []
    for f in faces:
        g = check_face(f)
        if g["face_id"] in seen:
            raise Refused(f"face {g['face_id']} appears twice (R-FW-LINE-1)")
        seen.add(g["face_id"])
        m = g["members"][0]
        if g["face_id"] in named:
            g["tie"], g["tie_reason"] = named[g["face_id"]]
            g["line_id"] = None
        else:
            ids = binding.get(m)
            if ids is None or len(ids) == 0:
                g["tie"], g["line_id"] = NO_LINE, None
                g["tie_reason"] = reasons.get(m, "no candidate concrete line holds this member")
            elif len(ids) > 1:
                g["tie"], g["line_id"] = SPLIT, None
                g["tie_reason"] = f"member {m} lies in {len(ids)} candidate lines {sorted(ids)}; no length per line"
                g["split_lines"] = sorted(ids)
                if g["status"] not in ("HELD", "INFO"):
                    g["status_before_split"], g["status"] = g["status"], "HELD"
                    g["held_from"], g["m2"] = g["m2"], None
            else:
                lid = ids[0]
                if lid not in lines:
                    raise Refused(f"face {g['face_id']}: line {lid} is not in the candidate")
                g["tie"], g["line_id"], g["tie_reason"] = TIED, lid, ""
        if g.get("line_id"):
            ln = lines[g["line_id"]]
            g["line_item_code"], g["line_element_id"] = ln["item_code"], ln["element_id"]
            g["line_state"] = ln.get("evidence_state")
        rows.append(g)
    return {"rows": rows, "closure": closure(source if source is not None else faces, rows)}


def closure(source: list, rows: list) -> list:
    """R-FW-LINE-6: per (source status, alternative, method): source sums vs ledger sums (tied + not tied, with the
    blanked quantities counted from their kept source value)"""
    def q(r, k):
        v = r.get(k)
        if k == "m2" and v is None:
            v = r.get("held_from", r.get("pending_from"))
        return _num(v) or 0.0
    a = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0])
    b = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0, collections.Counter()])
    for s in source:
        if s.get("split_of"):
            raise Refused(f"source row {s['face_id']} is itself a split piece")
        k = (s["status"], s.get("alternative") or "", s.get("method") or "")
        for i, f in enumerate(("m2", "lo", "hi")):
            a[k][i] += q(s, f)
        a[k][3] += 1
    counted = set()
    for r in rows:
        k = (r["status_in"], r.get("alternative") or "", r.get("method") or "")
        for i, f in enumerate(("m2", "lo", "hi")):
            b[k][i] += q(r, f)
        src = r.get("split_of") or r["face_id"]          # a source row split per member counts once
        if (k, src) not in counted:
            counted.add((k, src))
            b[k][3] += 1
        b[k][4][r["tie"]] += 1
    out = []
    for k in sorted(set(a) | set(b)):
        sa, sb = a[k], b[k]
        res = [round(sa[i] - sb[i], 6) for i in range(3)]
        if any(abs(x) > TOL for x in res) or sa[3] != sb[3]:
            raise Refused(f"closure fails for {k}: source {sa[:4]} vs ledger {sb[:4]}")
        out.append({"status": k[0], "alternative": k[1], "method": k[2], "rows": sa[3],
                    "m2": round(sa[0], 6), "lo": round(sa[1], 6), "hi": round(sa[2], 6),
                    "residual_m2": res[0], "residual_lo": res[1], "residual_hi": res[2],
                    "by_tie": dict(sorted(sb[4].items()))})
    return out


def consumer(rows: list, lines: dict, candidate: str, project: dict) -> dict:
    """the T-199 input shape: per candidate concrete line, its formwork faces and per-status totals (never summed
    across statuses or alternatives; scenario rows excluded; untied rows listed by reason)"""
    by = collections.defaultdict(list)
    for r in rows:
        if r["tie"] == TIED:
            by[r["line_id"]].append(r)
    out = []
    for lid in sorted(by):
        ln = lines[lid]
        tot = collections.defaultdict(lambda: {"m2": 0.0, "lo": 0.0, "hi": 0.0, "faces": 0})
        for r in by[lid]:
            t = tot[f"{r['status']}|{r.get('alternative') or ''}|{r.get('method') or ''}"]
            t["m2"] += r["m2"] or 0.0
            t["lo"] += r["lo"] or 0.0
            t["hi"] += r["hi"] or 0.0
            t["faces"] += 1
        out.append({"concrete_line_id": lid, "item_code": ln["item_code"], "element_id": ln["element_id"],
                    "floor": ln.get("floor"), "concrete_state": ln.get("evidence_state"),
                    "faces": [_slim(r) for r in by[lid]],
                    "totals": {k: {kk: (round(vv, 6) if isinstance(vv, float) else vv) for kk, vv in v.items()}
                               for k, v in sorted(tot.items())}})
    untied = [_slim(r) for r in rows if r["tie"] != TIED]
    return {"schema": CONSUMER_SCHEMA, "candidate": candidate, "project": project,
            "rule": "faces never summed across status / alternative / method; HELD and PENDING blank, range kept; "
                    "scenario S1 rows are never candidate faces",
            "lines": out, "not_tied": untied}


def _slim(r):
    keep = ("face_id", "revision", "element", "floor", "item", "face_kind", "contact", "alternative", "method", "m2",
            "lo", "hi", "status", "status_in", "members", "line_id", "tie", "tie_reason", "basis", "basis_note", "held_reason",
            "held_from", "pending_from", "split_lines", "split_of", "refs")
    return {k: r.get(k) for k in keep if r.get(k) not in (None, "", [])}
