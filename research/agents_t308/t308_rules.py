"""T-308 formwork r5 rules (research scope, any villa; provenance T-308 on T-293 parts 1 / 2 / 3, T-163 r3, T-264 r4).

Nothing here is wired and no candidate line changes. A formwork revision r5 is the merged face-to-line ledgers
(T-293 parts 1 / 2 / 3) with each Checker-confirmed correction applied ONCE, by a named rule, to the rows it names,
never by hand edits of rows; r3 / r4 and the part ledgers stay untouched.

R-T308-0  UNION. The part ledgers are joined by source key (a row's split_of, else its face id). A later part replaces
          an earlier part's NAMED aggregate rows of the same key; a key carried by two parts that are not a
          NAMED, information or scenario listing -> pieces replacement is refused; the union reproduces the source totals per (status, alternative,
          method) to 0.0005 m2 (r4 value of every piece, by its status in r4).
R-T308-1  ONE SPAN ONCE. A span (member + span row) is one set of formed faces: a second piece of the same span in an
          element-method row is not a face (DUPLICATE_IN_SOURCE), removed; two r5 faces with one span key refused.
R-T308-2  DRAWN SOFFIT ONLY. A volume / thickness soffit row keeps only its drawn face; the part inside another member
          (no surface), under a member whose own rows hold it (one face once), a retired reading and print rounding
          are removed with their cause; held pieces stay HELD, blank, with their value kept.
R-T308-3  BIND BY BAND (see t308_walk_delta.py): an unmatched walk face bound to the one member whose band covers it;
          its pieces replace the unmatched pieces; nothing else re-cut.
R-T308-4  ONE MEMBER ONE VIEW. A row that is a second view of a member whose faces are already tied (the tank walls =
          beam B15) is removed; its open designer item travels on the member's faces.
R-T308-5  HOLD WITH THE LINE (R-FW-P3-1, Checker 2026-10-26 01:55 'one rule for held lines'). A CALCULATED or
          ALTERNATIVE face tied to a line whose concrete carries no quantity in the current candidate (BLOCKED_RFI,
          BOUNDED_EXPOSURE) becomes HELD, blank, its value kept as held_from; a face tied to a NOT_APPLICABLE line is
          refused.
R-T308-6  RE-TIE TO AN ADDED LINE. A face listed NO_CANDIDATE_LINE whose member a later candidate adds (HELD) is tied
          to that line (and R-T308-5 holds it).
Guards (every villa): a HELD face with a number refused; an r5 face with no drawn evidence (walk face, drawn plane or
named ledger piece) refused; a removed kind (no face, duplicate, retired, rounding, pointer, second view) left tied
refused; one plan region in two r5 soffit faces refused.
"""
from __future__ import annotations

from collections import defaultdict

TOL = 0.0005
CALC, HELD, ALT = "CALCULATED", "HELD", "ALTERNATIVE"
TIED, NAMED = "TIED", "NAMED_NOT_TIED"
REMOVED = "REMOVED_IN_R5"
LISTED = (NAMED, "INFO_NOT_A_QUANTITY", "SCENARIO_NOT_IN_CANDIDATE")   # rows an earlier part lists, never ties
UNMEASURED = ("BLOCKED_RFI", "BOUNDED_EXPOSURE")
NOT_APPLICABLE = "NOT_APPLICABLE_WITH_EVIDENCE"
REMOVE_KIND = {"DUPLICATE_IN_SOURCE": "R-T308-1", "NO_FACE_INSIDE_MEMBER": "R-T308-2", "RETIRED_IN_SOURCE": "R-T308-2",
               "PRINT_ROUNDING": "R-T308-2", "POINTER_ROW": "R-T308-2", "DUPLICATE_VIEW": "R-T308-4"}


class Refused(ValueError):
    pass


def num(v):
    return None if v in (None, "") else float(v)


def key_of(r):
    return r.get("split_of") or r["face_id"]


def band_binding(face_area, cover, cover_min=0.95):
    """R-T308-3: face_area m2; cover {band id: area of the band inside the face}. -> the one band that covers at
    least cover_min of the face while no other band covers any of it, else None (the face stays UNMATCHED)."""
    if face_area <= 0:
        raise Refused("face area must be positive")
    hit = {b: a for b, a in cover.items() if a > 1e-9}
    if len(hit) != 1:
        return None
    (b, a), = hit.items()
    return b if a / face_area >= cover_min else None


def union(parts):
    """parts: [(name, rows)] oldest first. -> rows kept, each with 'part'. A later part's key replaces an earlier
    part's NAMED row of the same key; any other repeat of a key across parts is refused."""
    owner = {}
    for name, rows in parts:
        for k in {key_of(r) for r in rows}:
            owner.setdefault(k, []).append(name)
    out = []
    for i, (name, rows) in enumerate(parts):
        later = {n for n, _ in parts[i + 1:]}
        for r in rows:
            k = key_of(r)
            if set(owner[k]) & later:
                if r["tie"] not in LISTED and not r.get("_replaceable"):
                    raise Refused(f"{r['face_id']}: key {k} is in {owner[k]} and this row is not a NAMED aggregate")
                continue
            out.append(dict(r, part=name))
    return out


def r4_value(r):
    """the piece's value in r4: (status, m2, lo, hi) by its status in r4 (status_in)."""
    s = r.get("status_in") or r["status"]
    if s == "NOT_IN_R4":
        return s, 0.0, 0.0, 0.0
    if s in (CALC, ALT):
        v = num(r.get("m2"))
        if v is None:
            v = num(r.get("held_from"))
        return s, v or 0.0, 0.0, 0.0
    if s == HELD:
        return s, 0.0, num(r.get("lo")) or 0.0, num(r.get("hi")) or 0.0
    return s, num(r.get("m2")) or 0.0, 0.0, 0.0


def totals(rows, value):
    t = defaultdict(lambda: [0.0, 0.0, 0.0, 0])
    for r in rows:
        s, m, lo, hi = value(r)
        k = (s, r.get("alternative") or "", r["method"])
        t[k][0] += m
        t[k][1] += lo
        t[k][2] += hi
        t[k][3] += 1
    return t


def r5_value(r):
    s = r["r5_status"]
    if s == REMOVED:
        return s, 0.0, 0.0, 0.0
    if s == HELD:
        return s, 0.0, r["r5_lo"] or 0.0, r["r5_hi"] or 0.0
    return s, r["r5_m2"] or 0.0, 0.0, 0.0


def apply(rows, state, corrections=None, retie=None):
    """rows: union rows (ledger fields). state: {line_id: evidence_state of the current candidate}. corrections:
    {face_id: (rule, cause)} rows removed by name; retie: {member prefix: line_id} (R-T308-6).
    -> rows with r5_status / r5_m2 / r5_lo / r5_hi / r5_held_from / r5_tie / r5_line / rule / cause."""
    corrections = corrections or {}
    retie = retie or {}
    out = []
    for r in rows:
        x = dict(r)
        st, tie, line = r["status"], r["tie"], r.get("line_id") or ""
        m2, lo, hi, hf = num(r.get("m2")), num(r.get("lo")), num(r.get("hi")), num(r.get("held_from"))
        rule, cause = "", ""
        if st == HELD and m2 is not None:
            raise Refused(f"{r['face_id']}: a HELD face carries a number ({m2})")
        if r["face_id"] in corrections:
            rule, cause = corrections[r["face_id"]]
            st, tie, line, m2, lo, hi = REMOVED, REMOVED, "", None, None, None
        elif tie in REMOVE_KIND:
            rule = REMOVE_KIND[tie]
            if tie == "DUPLICATE_IN_SOURCE" and r.get("piece_kind") == tie:
                rule = "R-T308-2"          # a soffit piece under a member whose own rows hold it (stair rows)
            cause = r.get("tie_reason") or tie
            st, tie, line, m2, lo, hi = REMOVED, REMOVED, "", None, None, None
        elif tie == "NO_CANDIDATE_LINE" and any(m.startswith(p) for p in retie for m in r["members"].split(";")):
            p = next(p for p in retie if any(m.startswith(p) for m in r["members"].split(";")))
            tie, line, rule = TIED, retie[p], "R-T308-6"
            cause = f"the member's concrete line was added by a later candidate ({retie[p]})"
        if tie == TIED and line:
            ls = state.get(line)
            if ls is None:
                raise Refused(f"{r['face_id']}: line {line} is not in the current candidate")
            if ls == NOT_APPLICABLE:
                raise Refused(f"{r['face_id']}: tied to {line}, NOT_APPLICABLE in the current candidate")
            if st in (CALC, ALT) and ls in UNMEASURED:
                hf = m2 if m2 is not None else hf
                rule = (rule + " + " if rule else "") + "R-T308-5"
                cause = (cause + "; " if cause else "") + f"line {ls}: the face is held with it (R-FW-P3-1)"
                st, m2, lo, hi = HELD, None, None, None
            x["r5_line_state"] = ls
        else:
            x["r5_line_state"] = ""
        x.update(r5_status=st, r5_tie=tie, r5_line=line, r5_m2=m2, r5_lo=lo, r5_hi=hi, r5_held_from=hf, rule=rule,
                 cause=cause)
        out.append(x)
    guards(out)
    return out


def guards(rows):
    span, region = {}, {}
    for r in rows:
        if r["r5_status"] == REMOVED:
            continue
        if r["r5_tie"] in REMOVE_KIND:
            raise Refused(f"{r['face_id']}: kind {r['r5_tie']} cannot stay in r5")
        if r["r5_status"] == HELD and r["r5_m2"] is not None:
            raise Refused(f"{r['face_id']}: HELD with a number")
        if r["r5_tie"] != TIED or r["r5_status"] not in (CALC, ALT):
            continue
        if not r.get("evidence"):
            raise Refused(f"{r['face_id']}: no drawn evidence for a measured face")
        sk = r.get("span_key")
        if sk:
            if sk in span:
                raise Refused(f"span {sk} booked twice ({span[sk]}, {r['face_id']})")
            span[sk] = r["face_id"]
        rk = r.get("plan_region")
        if rk:
            if rk in region:
                raise Refused(f"plan region {rk} in two soffit faces ({region[rk]}, {r['face_id']})")
            region[rk] = r["face_id"]


def by_line(rows):
    """{line_id: {(status, alternative, method): [r4 m2, lo, hi, r5 m2, lo, hi, r5 held_from, rules]}}. r4 goes to
    the line the piece is tied to, else the line of the tied piece of the same row and member, else (a stair piece
    of part 3) the one line its row's tied pieces carry; r5 to the piece's r5 line."""
    row_line = defaultdict(set)
    mem_line = {}
    for r in rows:
        if r.get("line_id"):
            row_line[key_of(r)].add(r["line_id"])
            mem_line[(key_of(r), r["members"])] = r["line_id"]
    out = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, set()]))
    for r in rows:
        l4 = r.get("line_id") or mem_line.get((key_of(r), r["members"])) or ""
        if not l4 and r.get("part") == "P3" and len(row_line[key_of(r)]) == 1:
            l4 = next(iter(row_line[key_of(r)]))
        s, m, lo, hi = r4_value(r)
        if l4 and s != "NOT_IN_R4":
            c = out[l4][(s, r.get("alternative") or "", r["method"])]
            c[0] += m; c[1] += lo; c[2] += hi
            if r["rule"]:
                c[7].add(r["rule"])
        if r["r5_line"]:
            s5, m5, lo5, hi5 = r5_value(r)
            c = out[r["r5_line"]][(s5, r.get("alternative") or "", r["method"])]
            c[3] += m5; c[4] += lo5; c[5] += hi5
            if s5 == HELD and r.get("r5_held_from") is not None:
                c[6] += r["r5_held_from"]
            if r["rule"]:
                c[7].add(r["rule"])
    return out
