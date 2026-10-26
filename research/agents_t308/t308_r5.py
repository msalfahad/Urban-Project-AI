"""T-308: formwork r5 research rows, one consolidated set by candidate concrete line id, for the T-199 package.

    python3 -I research/agents_t308/t308_r5.py            # build + assert, print the summary
    python3 -I research/agents_t308/t308_r5.py --write    # also write the committed outputs in this folder

Inputs (all committed, all Checker-merged): the three face-to-line ledgers of T-293 (part 1 MERGED 294da634, part 2
a1e0c43a, part 3 02f3e47e), the part-1 source summary (closure per status / alternative / method of the 384 r4 / T-282 /
T-290 source rows), the BAND0049 walk delta of this task (t308_walk_delta.py, run on the Drive copy 'ST7757 dxf.dxf'
9f9d1179), the candidate line states: V3.0.16 (CANDIDATE_V3016_CONCRETE_LINES.json) + the 49 V3.0.17 lines of the T-254
per-line table (Gate B PASS 2026-10-25 13:35) + the V3.0.18 stair / dome lines (T-266, as recomputed by T-293 part 3).
Rules: t308_rules.py (R-T308-0 .. 6). Nothing is wired, no candidate or released line changes, r3 / r4 and the part
ledgers are untouched.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
ROOT = RES.parent
P293 = RES / "agents_t293"
sys.path.insert(0, str(HERE))
import t308_rules as R  # noqa: E402

PARTS = (("P1", P293 / "FORMWORK_FACE_TO_LINE_T293.csv"), ("P2", P293 / "FORMWORK_FACE_TO_LINE_T293_P2.csv"),
         ("P3", P293 / "FORMWORK_FACE_TO_LINE_T293_P3.csv"))
WALK = HERE / "T308_WALK_DELTA_BAND0049.json"
CAND16 = P293 / "CANDIDATE_V3016_CONCRETE_LINES.json"
CAND18 = P293 / "CANDIDATE_V3018_STAIR_DOME_LINES_T293P3.json"
T254 = RES / "agents_t254" / "T-254_BASIS_CORRECTION.md"
CANDIDATE = "ARCH_TAKEOFF_V3.0.18 (V3.0.16 lines + T-254 V3.0.17 table + T-266 V3.0.18 stair / dome lines)"
ROUNDING = {}                                 # per (status|alt|method): unrounded pieces minus printed rows
REPLACED_BY_P3 = {"R4-313", "R4-316"}         # part 3's own union statement: part-2 rows it replaces
BAND0049_LINE = "L-5bc1baae70fcc325abea"      # P-C:BEAMS:GF:BAND0049 (B7 20 x 75, PROVISIONAL 0.282743 m3)
BOUNDARY_LINE = "L-fb7a6431fede62e93fd5"      # T-254 ADD: T254:GROUND_BEAMS:GROUND:BOUNDARY_GB_NG (BLOCKED_RFI, M4)
CB5_DUP = ("R4-253.R138.DUP", "R4-255.R138.DUP")
CORRECTIONS = {
    "R4-275.GF-095.UNMATCHED_PLAN": ("R-T308-3", "re-bound: walk face GF-095 is the drawn curved B7 corner BM-GF-049 "
                                     "(BAND0049); its plan enters that line as the beam soffit (row R5-BAND0049.*)"),
    "R4-268.GF-093.JOINT_HELD_M2": ("R-T308-3", "with GF-095 bound to B7 (D 0.75) the column COL-GF-15 face beside it "
                                    "is covered: D_ctrl 0.75 - D 0.75 = 0 (r3 joint rule max(0, Dc - D)); the held "
                                    "piece 0 .. 0.117958 does not exist"),
}
WALK_ROWS = {   # walk category -> (r4 row it extends, element, face kind, item)
    "BEAM_SOFFIT": ("GF roof slab (p.4) beam soffits", "BEAM", "BEAM"),
    "BEAM_SIDE": ("GF roof slab (p.4) beam sides below the slab", "BEAM", "BEAM"),
    "EDGE_BAND": ("GF roof slab (p.4) slab-thickness band at every free edge (plate perimeter and openings)",
                  "SLAB_EDGE", "SLAB_EDGE"),
    "BEAM_SIDE_HELD_M2:UNMATCHED": ("GF roof slab (p.4) beam_side faces next to the unbound partition piece GF-112 "
                                    "(0.200 m; its depth is not printed: line BOUNDED_EXPOSURE)", "BEAM", "BEAM"),
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rd(p):
    return list(csv.DictReader(Path(p).open(encoding="utf-8")))


def line_states():
    """{line_id: (state, item_code, element_id, floor, source)} for the current candidate (V3.0.18)."""
    out = {}
    for ln in json.loads(CAND16.read_text(encoding="utf-8"))["lines"]:
        out[ln["line_id"]] = (ln["evidence_state"], ln["item_code"], ln["element_id"], ln["floor"], "V3.0.16")
    n = 0
    for t in T254.read_text(encoding="utf-8").splitlines():
        if not t.startswith("| L-"):
            continue
        c = [x.strip() for x in t.strip().strip("|").split("|")]
        n += 1
        lid, v17, ev = c[0], c[6], c[7]
        st = v17 if v17 in ("BLOCKED_RFI", R.NOT_APPLICABLE) else "SOURCE_DERIVED"
        old = out.get(lid)
        if old is None:
            if lid != BOUNDARY_LINE:
                raise R.Refused(f"T-254 line {lid} unknown and not the added boundary line")
            out[lid] = (st, "STR.CONC.GROUND_BEAM", "T254:GROUND_BEAMS:GROUND:BOUNDARY_GB_NG", "GROUND",
                        f"V3.0.17 ADD ({ev})")
        else:
            out[lid] = (st, old[1], old[2], old[3], f"V3.0.17 {v17} ({ev})")
    if n != 49:
        raise R.Refused(f"T-254 per-line table: {n} rows, expected 49")
    for ln in json.loads(CAND18.read_text(encoding="utf-8"))["lines"]:
        out[ln["line_id"]] = (ln["evidence_state"], ln["item_code"], ln["element_id"], ln["floor"], "V3.0.18")
    return out


def boundary_line_check():
    sys.path.insert(0, str(ROOT))
    from engine.source import arch_v3017 as A, boq_line as BL
    pr = json.loads(CAND16.read_text(encoding="utf-8"))["project"]
    p = A.PIECES["BASIS_CORRECTION"]
    lid = BL.line_id(pr["project_id"], "STR.CONC.GROUND_BEAM", "T254:GROUND_BEAMS:GROUND:BOUNDARY_GB_NG",
                     p["rule_id"], p["rule_version"], "m3")
    if lid != BOUNDARY_LINE:
        raise R.Refused(f"boundary line id recomputed {lid} != {BOUNDARY_LINE}")
    return lid


def part_rows():
    parts = []
    for name, p in PARTS:
        rows = rd(p)
        for r in rows:
            r.setdefault("alternative", "")
            r.setdefault("walk_face", "")
            r.setdefault("held_from", "")
            r["evidence"] = "; ".join(x for x in (r.get("walk_face") and "walk face " + r["walk_face"],
                                                  r.get("basis_note"), r.get("refs"), r.get("revision")) if x)
            if name == "P2" and r["face_id"] in REPLACED_BY_P3:
                r["_replaceable"] = True
            if name == "P2" and r["method"] == "E" and r["element"] == "BEAM" and "T-149 span" in r["basis_note"]:
                span = r["basis_note"].split("T-149 span ")[1].split()[0]
                kind = "soffit" if "soffit" in r["item"] else "side"
                r["span_key"] = f"{r['floor']}|{span}|{kind}"
        parts.append((name, rows))
    return parts


def walk_rows():
    doc = json.loads(WALK.read_text(encoding="utf-8"))
    if doc["schema"] != "T308_WALK_DELTA_V1" or doc["face"] != "GF-095" or doc["member"] != "BM-GF-049":
        raise R.Refused("walk delta: wrong schema / face / member")
    out = []
    for c in doc["changed"]:
        if c["face"] != "GF-095" or c["after_m2"] is None or c["category"] not in WALK_ROWS:
            continue
        item, element, kind = WALK_ROWS[c["category"]]
        held = c["category"].endswith("_HELD_M2:UNMATCHED")
        v = round(c["after_m2"], 6)
        out.append({"face_id": f"R5-BAND0049.GF-095.{c['category']}", "part": "R5",
                    "revision": "T-308 walk delta (r3 walk, GF-095 bound to BM-GF-049, R-T308-3) "
                                "T308_WALK_DELTA_BAND0049.json",
                    "element": element, "floor": "GF", "item": item, "face_kind": kind, "contact": "FORM",
                    "alternative": "", "method": "G", "m2": "" if held else f"{v:.6f}",
                    "lo": "0.000000" if held else "", "hi": f"{v:.6f}" if held else "",
                    "status": R.HELD if held else R.CALC, "status_in": "NOT_IN_R4",
                    "members": "BEAM:BM-GF-049", "walk_face": "GF-095", "tie": R.TIED, "line_id": BAND0049_LINE,
                    "held_from": "", "split_of": "", "rule_new": "R-T308-3", "evidence": "walk face GF-095 (bound)",
                    "basis_note": f"walk face GF-095 {c['category']} (drawn arcs 29F R 1.300 / 2A0 R 1.100, 90 deg, "
                                  f"B7 20 x 75 ST p.10, slab 0.16 ST p.8 note 18)",
                    "tie_reason": "F-T293-P2-02 ruled: BAND0049 has a drawn face (GF-095)"})
    if len(out) != 4:
        raise R.Refused(f"walk delta: {len(out)} GF-095 pieces, expected 4")
    return out, doc


def build():
    states = line_states()
    boundary_line_check()
    parts = part_rows()
    rows = R.union(parts)
    src_tot = {(c["status"], c["alternative"], c["method"]): (c["m2"], c["lo"], c["hi"])
               for c in json.loads((P293 / "summary_t293.json").read_text())["closure"]}
    # R-T308-0: the union reproduces every source row (r4 value of each piece by its r4 status), row by row to
    # 0.0005 m2 (a 3-dp printed row carries its unrounded pieces, T-293 R-FW-P2-1); part 1 lists all 384 source rows
    p1 = defaultdict(list)
    for r in parts[0][1]:
        p1[R.key_of(r)].append(r)
    un = defaultdict(list)
    for r in rows:
        un[R.key_of(r)].append(r)
    if set(p1) != set(un):
        raise R.Refused(f"union keys differ from the source rows: {sorted(set(p1) ^ set(un))[:10]}")
    bad, rounding = [], defaultdict(lambda: [0.0, 0.0, 0.0])
    for k in p1:
        a, b = R.totals(p1[k], R.r4_value), R.totals(un[k], R.r4_value)
        for kk in set(a) | set(b):
            x, y = a.get(kk, [0.0] * 4), b.get(kk, [0.0] * 4)
            for i in range(3):
                if abs(x[i] - y[i]) > R.TOL + 1e-9:
                    bad.append((k, kk, x[:3], y[:3]))
                rounding[kk][i] += y[i] - x[i]
    if bad:
        raise R.Refused(f"union does not reproduce the source rows: {bad[:5]}")
    got = R.totals(rows, R.r4_value)
    for k in set(src_tot) | set(got):
        a = src_tot.get(k, (0.0, 0.0, 0.0))
        b = got.get(k, [0.0, 0.0, 0.0, 0])
        for i in range(3):
            if abs(a[i] - b[i] - (-rounding[k][i])) > 1e-6:
                raise R.Refused(f"{k}: source total {a} vs union {b[:3]} not explained by the row rounding")
    ROUNDING.clear()
    ROUNDING.update({"|".join(k): [round(v, 6) for v in x] for k, x in rounding.items() if any(abs(v) > 1e-9 for v in x)})
    keys = Counter(R.key_of(r) for r in rows)
    new, walkdoc = walk_rows()
    state = {k: v[0] for k, v in states.items()}
    corr = dict(CORRECTIONS)
    out = R.apply(rows + new, state, corrections=corr, retie={"BOUNDARY_GB:": BOUNDARY_LINE})
    for r in out:
        if r.get("rule_new"):
            r["rule"] = r["rule_new"] + (" + " + r["rule"] if r["rule"] else "")
            r["cause"] = r["tie_reason"] + ("; " + r["cause"] if r["cause"] else "")
        if r["face_id"] in CB5_DUP:
            r["cause"] = "F-T293-P2-01 CB5 span 2 (R138) counted twice by the r3 / r4 element method: " + r["cause"]
    return states, rows, out, src_tot, keys, walkdoc


def _f(v, n=6):
    return "" if v is None else f"{v:.{n}f}"


FACE_COLS = ("face_id", "part", "revision", "element", "floor", "item", "face_kind", "contact", "alternative", "method",
             "members", "walk_face", "split_of", "r4_status", "r4_m2", "r4_lo", "r4_hi", "ledger_tie",
             "ledger_status", "ledger_line", "r5_status", "r5_m2", "r5_lo", "r5_hi", "r5_held_from", "r5_tie",
             "r5_line", "r5_line_state", "rule", "cause")


def face_table(out):
    rows = []
    for r in out:
        s, m, lo, hi = R.r4_value(r) if r.get("status_in") != "NOT_IN_R4" else ("NOT_IN_R4", None, None, None)
        rows.append({"face_id": r["face_id"], "part": r["part"], "revision": r["revision"], "element": r["element"],
                     "floor": r["floor"], "item": r["item"], "face_kind": r["face_kind"],
                     "contact": r.get("contact", ""), "alternative": r.get("alternative", ""), "method": r["method"],
                     "members": r["members"], "walk_face": r.get("walk_face", ""), "split_of": r.get("split_of", ""),
                     "r4_status": s, "r4_m2": _f(m) if s in (R.CALC, R.ALT) else "",
                     "r4_lo": _f(lo) if s == R.HELD else "", "r4_hi": _f(hi) if s == R.HELD else "",
                     "ledger_tie": r["tie"], "ledger_status": r["status"], "ledger_line": r.get("line_id", ""),
                     "r5_status": r["r5_status"], "r5_m2": _f(r["r5_m2"]), "r5_lo": _f(r["r5_lo"]),
                     "r5_hi": _f(r["r5_hi"]), "r5_held_from": _f(r["r5_held_from"]), "r5_tie": r["r5_tie"],
                     "r5_line": r["r5_line"], "r5_line_state": r["r5_line_state"], "rule": r["rule"],
                     "cause": r["cause"]})
    return rows


def ledger_value(r):
    """the merged ledgers' own value of a piece (status as the part ledger tied it)."""
    s = r["status"]
    if r.get("status_in") == "NOT_IN_R4":
        return "NOT_IN_R4", 0.0, 0.0, 0.0
    if s in (R.CALC, R.ALT):
        return s, R.num(r.get("m2")) or 0.0, 0.0, 0.0
    if s == R.HELD:
        return s, 0.0, R.num(r.get("lo")) or 0.0, R.num(r.get("hi")) or 0.0
    return s, R.num(r.get("m2")) or 0.0, 0.0, 0.0


def rule_deltas(out):
    """per rule and (status, alternative, method): r5 minus the merged ledgers' tied state, with the row count."""
    d = defaultdict(lambda: [0.0, 0.0, 0.0, 0])
    for r in out:
        if not r["rule"]:
            continue
        a = ledger_value(r)
        b = R.r5_value(r)
        for s, sign, m, lo, hi in ((a[0], -1, a[1], a[2], a[3]), (b[0], 1, b[1], b[2], b[3])):
            if s == R.REMOVED:
                continue
            k = (r["rule"], s, r.get("alternative") or "", r["method"])
            d[k][0] += sign * m
            d[k][1] += sign * lo
            d[k][2] += sign * hi
        d[(r["rule"], "*", "", "*")][3] += 1
    return d


def stair_causes(out):
    """formwork r4 stair rows (part 3) vs r5, by physical cause (F-T293-P3-01)."""
    c = defaultdict(float)
    for r in out:
        if r["part"] != "P3" or r["element"] != "STAIR" or r["face_id"].startswith("T290-"):
            continue
        s, m, _, _ = R.r4_value(r)
        if s != R.CALC:
            continue
        kind = r.get("piece_kind") or ""
        if r["r5_status"] == R.CALC:
            c["r5 drawn faces CALCULATED"] += r["r5_m2"]
        elif r["r5_status"] == R.HELD and r.get("line_id") and r.get("line_state") == "BLOCKED_RFI":
            c["HELD with its held line (R-FW-P3-1: MS1-L, E1 risers)"] += m
        elif r["r5_status"] == R.HELD:
            c["HELD piece of a closable line (column exposures D-16, unmarked layer-5 pairs)"] += m
        else:
            c[{"NO_FACE_INSIDE_MEMBER": "inside another member: no surface",
               "DUPLICATE_IN_SOURCE": "under a member whose own rows hold it (one face once)",
               "RETIRED_IN_SOURCE": "readings the concrete ledger retired",
               "PRINT_ROUNDING": "r4 print rounding"}.get(kind, kind or r["tie"])] += m
        c["r4 printed (CALCULATED rows)"] += m
    return {k: round(v, 6) for k, v in c.items()}


def consumer(out, states):
    lines = defaultdict(list)
    not_tied = []
    for r in out:
        f = {k: r[k] for k in ("face_id", "revision", "element", "floor", "item", "face_kind", "method", "members")}
        f.update(contact=r.get("contact", ""), alternative=r.get("alternative", ""), status=r["r5_status"],
                 status_r4=R.r4_value(r)[0] if r.get("status_in") != "NOT_IN_R4" else "NOT_IN_R4",
                 m2=r["r5_m2"], lo=r["r5_lo"], hi=r["r5_hi"], held_from=r["r5_held_from"], tie=r["r5_tie"],
                 rule=r["rule"], cause=r["cause"], walk_face=r.get("walk_face", ""),
                 basis_note=r.get("basis_note", ""))
        f = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in f.items()}
        if r["r5_tie"] == R.TIED and r["r5_line"]:
            lines[r["r5_line"]].append(f)
        elif r["r5_status"] != R.REMOVED:
            f["tie_reason"] = r.get("tie_reason", "")
            not_tied.append(f)
    removed = [{"face_id": r["face_id"], "rule": r["rule"], "cause": r["cause"],
                "r4_value": [round(x, 6) if isinstance(x, float) else x for x in R.r4_value(r)]}
               for r in out if r["r5_status"] == R.REMOVED]
    ln_out = []
    for lid in sorted(lines):
        st, item, eid, floor, srcv = states[lid]
        tot = defaultdict(lambda: {"m2": 0.0, "lo": 0.0, "hi": 0.0, "faces": 0})
        for f in lines[lid]:
            k = f"{f['status']}|{f['alternative']}|{f['method']}"
            tot[k]["m2"] += f["m2"] or 0.0
            tot[k]["lo"] += f["lo"] or 0.0
            tot[k]["hi"] += f["hi"] or 0.0
            tot[k]["faces"] += 1
        ln_out.append({"concrete_line_id": lid, "item_code": item, "element_id": eid, "floor": floor,
                       "concrete_state": st, "concrete_state_source": srcv, "faces": lines[lid],
                       "totals": {k: {kk: (round(vv, 6) if isinstance(vv, float) else vv) for kk, vv in v.items()}
                                  for k, v in sorted(tot.items())}})
    return {"schema": "T308_FORMWORK_R5_BY_CONCRETE_LINE_V1", "revision": "FORMWORK_R5 (T-308)",
            "candidate": CANDIDATE, "project": json.loads(CAND16.read_text())["project"],
            "rule": "faces never summed across status / alternative / method; HELD blank with held_from, never 0; "
                    "scenario S1 rows are never candidate faces; REMOVED rows are not faces",
            "lines": ln_out, "not_tied": not_tied, "removed_in_r5": removed}


def csv_text(rows, cols):
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in cols})
    return b.getvalue()


LINE_COLS = ("line_id", "item_code", "element_id", "concrete_state", "status", "alternative", "method", "r4_m2",
             "r4_lo", "r4_hi", "r5_m2", "r5_lo", "r5_hi", "r5_held_from", "delta_m2", "rules")


def line_table(out, states):
    rows = []
    for lid, d in sorted(R.by_line(out).items()):
        st = states.get(lid, ("", "", "", "", ""))
        for (s, alt, meth), v in sorted(d.items()):
            if s in ("INFO", "S1_NOT_RELEASED"):
                continue
            rows.append({"line_id": lid, "item_code": st[1], "element_id": st[2], "concrete_state": st[0],
                         "status": s, "alternative": alt, "method": meth, "r4_m2": _f(v[0]), "r4_lo": _f(v[1]),
                         "r4_hi": _f(v[2]), "r5_m2": _f(v[3]), "r5_lo": _f(v[4]), "r5_hi": _f(v[5]),
                         "r5_held_from": _f(v[6]) if s == R.HELD else "", "delta_m2": _f(v[3] - v[0]),
                         "rules": " ".join(sorted(v[7]))})
    return rows


def held_from_totals(out):
    h = defaultdict(float)
    for r in out:
        if r["r5_status"] == R.HELD and r["r5_held_from"] is not None:
            h[f"HELD|{r.get('alternative') or ''}|{r['method']}"] += r["r5_held_from"]
    return {k: round(v, 6) for k, v in sorted(h.items())}


def summary(states, rows, out, src_tot, walkdoc):
    t4 = R.totals(out, R.r4_value)
    tl = R.totals(out, ledger_value)
    t5 = R.totals(out, R.r5_value)
    keys = sorted(set(t4) | set(t5) | set(tl))
    tab = []
    for k in keys:
        a = t4.get(k, [0.0, 0.0, 0.0, 0]); m = tl.get(k, [0.0, 0.0, 0.0, 0]); b = t5.get(k, [0.0, 0.0, 0.0, 0])
        tab.append({"status": k[0], "alternative": k[1], "method": k[2],
                    "r4_m2": round(a[0], 6), "r4_lo": round(a[1], 6), "r4_hi": round(a[2], 6),
                    "ledgers_m2": round(m[0], 6), "ledgers_lo": round(m[1], 6), "ledgers_hi": round(m[2], 6),
                    "r5_m2": round(b[0], 6), "r5_lo": round(b[1], 6), "r5_hi": round(b[2], 6)})
    rd_ = rule_deltas(out)
    deltas = [{"rule": k[0], "status": k[1], "alternative": k[2], "method": k[3], "m2": round(v[0], 6),
               "lo": round(v[1], 6), "hi": round(v[2], 6)} for k, v in sorted(rd_.items()) if k[1] != "*"]
    counts = {k[0]: v[3] for k, v in rd_.items() if k[1] == "*"}
    # closure: r5 = merged ledgers + every rule delta, per (status, alternative, method)
    res = defaultdict(lambda: [0.0, 0.0, 0.0])
    for k, v in tl.items():
        for i in range(3):
            res[k][i] -= v[i]
    for k, v in t5.items():
        if k[0] == R.REMOVED:
            continue
        for i in range(3):
            res[k][i] += v[i]
    for k, v in rd_.items():
        if k[1] == "*":
            continue
        kk = (k[1], k[2], k[3])
        for i in range(3):
            res[kk][i] -= v[i]
    resid = {"|".join(k): [round(x, 9) for x in v] for k, v in res.items() if any(abs(x) > 1e-6 for x in v)}
    if resid:
        raise R.Refused(f"closure residual: {resid}")
    tied5 = {r["r5_line"] for r in out if r["r5_tie"] == R.TIED and r["r5_line"]}
    live = {lid for lid, v in states.items() if v[0] != R.NOT_APPLICABLE and
            (v[1].startswith("STR.CONC.") and v[1] not in ("STR.CONC.BLINDING",))}
    return {"schema": "T308_SUMMARY_V1", "candidate": CANDIDATE,
            "inputs_sha256": {str(p.relative_to(ROOT)): sha(p) for p in
                              [p for _, p in PARTS] + [WALK, CAND16, CAND18, T254, P293 / "summary_t293.json"]},
            "union_rows": len(rows), "r5_rows": len(out),
            "by_r5_status": dict(Counter(r["r5_status"] for r in out)),
            "by_rule": counts, "totals": tab, "rule_deltas": deltas,
            "closure": "r5 = merged ledgers + rule deltas per (status, alternative, method): residual 0 (asserted); "
                       "union r4 values = the 384 source rows (part-1 closure) to 0.0005 m2 (asserted)",
            "stair_r4_vs_r5_by_cause": stair_causes(out),
            "band0049_walk": {k: walkdoc[k] for k in ("face", "member", "band", "face_plan_m2", "band_cover_of_face",
                                                      "unchanged_records", "merged_records")},
            "held_from_r5": held_from_totals(out),
            "union_row_rounding_vs_printed": dict(ROUNDING),
            "lines_with_faces_r5": len(tied5),
            "live_concrete_lines_without_faces": sorted(live - tied5)}


OUTPUTS = ("FORMWORK_R5_BY_FACE_T308.csv", "FORMWORK_R5_BY_LINE_T308.csv", "T199_FORMWORK_BY_LINE_T308.json",
           "summary_t308.json")


def write(states, rows, out, src_tot, walkdoc, outdir=HERE):
    HERE_ = Path(outdir)
    (HERE_ / "FORMWORK_R5_BY_FACE_T308.csv").write_text(csv_text(face_table(out), FACE_COLS), encoding="utf-8")
    (HERE_ / "FORMWORK_R5_BY_LINE_T308.csv").write_text(csv_text(line_table(out, states), LINE_COLS),
                                                      encoding="utf-8")
    (HERE_ / "T199_FORMWORK_BY_LINE_T308.json").write_text(
        json.dumps(consumer(out, states), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (HERE_ / "summary_t308.json").write_text(
        json.dumps(summary(states, rows, out, src_tot, walkdoc), indent=1, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    states, rows, out, src_tot, keys, walkdoc = build()
    s = summary(states, rows, out, src_tot, walkdoc)
    print(json.dumps({k: s[k] for k in ("union_rows", "r5_rows", "by_r5_status", "by_rule", "lines_with_faces_r5",
                                        "stair_r4_vs_r5_by_cause")}, indent=1))
    for t in s["totals"]:
        print(t)
    for d in s["rule_deltas"]:
        print(d)
    print("live lines without faces", len(s["live_concrete_lines_without_faces"]))
    if a.write:
        write(states, rows, out, src_tot, walkdoc)


if __name__ == "__main__":
    main(sys.argv[1:])
