"""T-636 THE 10 NOV TRIAL BOQ (R-T636-1; lane I, non-candidate document, research only).

Reads ARCH_TAKEOFF_V3.0.58 + WIRING MANIFEST V17 (T-641, merged; rebuilt with its own calls and checked against the
committed V17), groups it once by BOQ_FAMILY_MASTER 1.56.0 (T-637, merged) with the T-630 reader (R-T630-1, read only:
aggregate / proof / _out / family_coverage), and writes the trial BOQ: one table per trade B1 .. B13 (+ the UNCODED
register lines, reported apart) and per unit, one row per BOQ line (family x item code x unit) with

  - the released quantity split into three separate columns that re-add exactly to it:
      WIRED IN V3.0.58          the line's state is the candidate's own (no overlay quantity op) and a Checker
                                verdict binds it (VERIFIED / PARTIALLY VERIFIED);
      FIX ROW NOT YET WIRED     an overlay quantity op (a fix row of a MERGED, Checker-verdicted task, R-T631-1 (a))
                                set the line's state and its stamp is a WORKFLOW_CONTROLS s.5 status;
      UNVERIFIED                no Checker binding and no s.5 stamp (T-630 evidence UNKNOWN), whatever its origin;
  - every HELD line with its CAUSE (never blank, never 0) read from the latest committed record that states it, or a
    finding F-T636-1 that lists it by line id when no committed record states one (never dropped);
  - the aggregation proof component -> BOQ line -> family -> trade -> unit (T-630 method, exact Decimal) and the
    three-column re-add per BOQ line, trade and unit;
  - the number of Checker-verified whole lines per trade;
  - section WILL / WILL NOT CONTAIN in plain words; the freelancer reference (scorecard V11, T-620) in its own appendix.

R-T636-1 (every villa on the engine's line-index scheme; the trial BOQ method):
  (a) A HELD LINE CARRIES A CAUSE OR A FINDING. Cause records are collected from every committed source that states
      one for the line; the record of the LATEST task wins (task number; on a tie the overlay op, the wired state);
      the others are listed as 'also stated by'. Sources, by kind: the overlay op that set the line (beside.cause /
      missing / high_open_by_name, else the Checker verdict line), the merged hold censuses (T-638 formwork, T-639
      rebar, T-640 finishes, T-642 P02 / P04 / parapet, T-644 lintels), the T-572 HELD-bound components, an APPLIED
      Checker downgrade of the V3.0.57 index, the T-449 correction registers (held_reason), and the candidate record
      extracts T-297 (V3.0.16 rebar: reasons / rfi / bound basis; used only while its bound equals the line's) and
      T-311 (V3.0.19: rfi head). A material line whose op names its host ('host L-...') and has no own record takes
      its host's cause by name (one step). A line with none of these is F-T636-1, listed, never given a typed cause.
  (b) HELD IS NEVER 0 AND NEVER SUMMED: a HELD line with a measured quantity, or a BOQ line / trade / unit with a HELD
      line that prints a total, is refused (TrialError).
  (c) AN OVERLAY QUANTITY IS NEVER COUNTED AS WIRED: a line any overlay quantity op wrote is never in the WIRED column.
  (d) THE THREE COLUMNS RE-ADD EXACTLY to the released quantity of every BOQ line, family, trade and unit (Decimal).
  (e) MASTER 1.56.0 FAMILIES ONLY: UNCODED (NO_FAMILY) lines are listed as a finding (expected 0); register codes
      (NOT_A_BOQ_LINE) are reported apart, never in a trade figure.
  (f) The freelancer reference is an appendix, never mixed with the engineering columns; no accuracy figure.
Nothing is wired; no candidate, released (V2.9 + route G), rule, knowledge or registry file is written; no drawing is
read. Rebuild through the wrapper: `URBAN_T636_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-636
tests/t636_trial_boq/test_t636.py::test_write_outputs`; check: `... pytest --tree task-T-636 tests/t636_trial_boq`.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (ROOT / "research/agents_t630", ROOT / "research/agents_t641"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import e2e_dry_run as E                    # noqa: E402  (R-T630-1, read only)
import manifest_v17 as M17                 # noqa: E402  (R-T641-1, read only)

OV, M9 = E.OV, E.M9
D, S = E.D, E.S
SCHEMA, RULE = "URBAN_T636_TRIAL_BOQ", "R-T636-1"
OUT_JSON = HERE / "out/TRIAL_BOQ_T636.json"
OUT_MD = HERE / "out/TRIAL_BOQ_T636.md"
OUT_CSV = HERE / "out/TRIAL_BOQ_T636_LINES.csv"
MASTER = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.56.0.json"
SCORECARD = ROOT / "research/agents_t620/out/SCORECARD_T620.json"
V17 = ROOT / "research/agents_t641/out/WIRING_MANIFEST_V17.json"
INDEX57 = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
SRC = {
    "T638": ROOT / "research/agents_t638/out/FORMWORK_HOLD_CENSUS_T638.json",
    "T639": ROOT / "research/agents_t639/out/REBAR_HOLD_CENSUS_T639.json",
    "T640": ROOT / "research/agents_t640/out/HOLD_CENSUS_T640.json",
    "T642": ROOT / "research/agents_t642/out/T642_FIX_ROWS.json",
    "T644": ROOT / "research/agents_t644/out/T644_LINTEL_PIECES.json",
    "T572": ROOT / "research/agents_t572/out/T572_HELD_BOUNDS.json",
    "DG": ROOT / "research/agents_t469/DOWNGRADES_SNAPSHOT.json",
    "T449C": ROOT / "research/agents_t449/out/CORRECTION_REGISTER_CONCRETE_T449.json",
    "T449R": ROOT / "research/agents_t449/round2/out/CORRECTION_REGISTER_REBAR_T449.json",
    "T297": ROOT / "research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json",
    "T311": ROOT / "research/agents_t311/CANDIDATE_V3019_T311.json",
}
WIRED, OVERLAY, UNVERIFIED = "WIRED IN V3.0.58", "FIX ROW NOT YET WIRED (overlay)", "UNVERIFIED"
COLUMNS = (WIRED, OVERLAY, UNVERIFIED)
CHECKER_STATUSES = ("VERIFIED", "PARTIALLY VERIFIED")
ID_RE = re.compile(r"\b(Q-\d+|D-\d+|OQ-\d+|DG-[0-9a-f]{6,}|C-ST-\d+|ORR-\d+|UP-[A-Z]+(?:-[A-Z]+)*-\d{3}|R-T\d+-\d+|"
                   r"F-C-[A-Z0-9]+(?:-[A-Z0-9]+)*|F-T\d+-\d+|FR-T\d+-\d+|T-\d{3})\b")
TASK_RE = re.compile(r"\bT-(\d{3})\b")
HOST_RE = re.compile(r"^host (L-[0-9a-f]{20}|NEW:\S+)$")
MERGED_SINCE_V17 = {"T-637": "master 1.56.0 (the grouping of this BOQ)",
                    "T-642": "P02 / P04 + parapet fix rows (cause source; no line moved in the overlay)",
                    "T-644": "B9-02 lintel pieces (cause source; pieces not wired)"}


# board rows open at claim (2026-11-08T23:00Z) whose scope names the item codes of F-T636-1 lines (pointer only: no
# quantity or cause is taken from an unmerged row)
OPEN_ROWS = (("FIN.STAIR.", "T-645 (READY, not merged)"), ("FIN.MARBLE.RISER", "T-645 (READY, not merged)"),
             ("FIN.MARBLE.TREAD", "T-645 (READY, not merged)"), ("FIN.MARBLE.LANDING", "T-645 (READY, not merged)"),
             ("FIN.ROOF.", "T-646 (TODO)"), ("EXT.FENCE.", "T-646 (TODO, fence plaster / paint / face)"),
             ("STR.REBAR", "T-643 (TODO, 208 unbound rebar lines)"), ("MAS.BLOCK", "T-633 (TODO, blockwork rows)"))


def open_row(code):
    return next((r for p, r in OPEN_ROWS if code.startswith(p)), None)


class TrialError(Exception):
    pass


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def ids_in(text):
    return sorted(set(ID_RE.findall(text or "")))


# ---- the V17 overlay, rebuilt ---------------------------------------------------------------------------------------

def overlay_v17():
    """the T-641 build up to after17 (same calls, same order); checked against the committed V17."""
    M17.pins()
    t628, t638, t639, t640 = (M17._json(M17.IN[k]) for k in ("T628", "T638", "T639", "T640"))
    idx, after15, order16, rul16, after16, rep16, stair, _ = M17.v16_state()
    moves = M17.finish_moves(stair, (M17.GF_PORC, M17.F1_PORC))
    bed, rul_b, _ = M17.bed_rows(after15, after16, order16, moves, source="T-631")
    band, _ = M17.band_row(t628, after16, order16)
    fw, _ = M17.formwork_rows(t638, after16, order16)
    bars, _ = M17.bars_rows(t639, after16, order16)
    fin, fin_ret, _, _ = M17.finish_rows(t640, after16, order16)
    order17 = M17.M15.chain_into(order16, M17.P_RET, fin_ret) + \
        [(M17.P_BED, bed), (M17.P_BAND, [band]), (M17.P_FW, fw), (M17.P_BARS, bars), (M17.P_FIN, fin)]
    after17, rep = OV.apply(idx, order17, list(rul16) + rul_b)
    v17 = _json(V17)
    if len(after17) != v17["overlay"]["lines"]["after_v17"]:
        raise TrialError("STALE_INPUT: the V17 rebuild differs from the committed V17 line count")
    t17 = OV.totals(after17)
    for k, d in v17["overlay"]["v17_vs_v16_totals"].items():
        if t17.get(k) != d["after"]:
            raise TrialError(f"STALE_INPUT: V17 rebuild total {k} differs from the committed V17")
    return idx, order17, after17, rep


def last_ops(order):
    """line_id -> the last quantity op (ADD / SET / RECODE) in package order (R1: one writer package per line)."""
    return E.last_qty_ops(order)


# ---- (a) cause records ----------------------------------------------------------------------------------------------

def _rec(task, label, text, extra=None, kind=None):
    text = " ".join(str(text).split())
    return {"task": task, "source": label, "kind": kind or label, "cause": text, "ids": ids_in(text), **(extra or {})}


def op_cause(op):
    """the cause an overlay op states for the state it sets, or None (a host note or a room id is not a cause)."""
    b = op.get("beside") or {}
    parts = []
    for k in ("cause", "missing"):
        if isinstance(b.get(k), str) and b[k].strip():
            parts.append(b[k])
    if b.get("high_open_by_name"):
        parts.append("high open by name: " + ", ".join(map(str, b["high_open_by_name"])))
    note = op.get("note")
    if isinstance(note, str) and note.strip() and not HOST_RE.match(note.strip()) and re.search(r"[A-Z_]{6,}|\s", note):
        if not re.fullmatch(r"(GF|1F|2F|RF)-\d+", note.strip()):
            parts.append(f"note {note.strip()}")
    vl = (op.get("evidence") or {}).get("verdict_line")
    if not parts and isinstance(vl, str) and vl.strip():
        parts.append(vl)
    if not parts:
        return None
    m = TASK_RE.findall(" ".join(str(op.get(k) or "") for k in ("package", "row", "source")) + " " + (vl or ""))
    task = max((int(x) for x in m), default=0)
    return _rec(task, f"overlay op {op['op_id'][:90]}", "; ".join(parts),
                {"op_status": (op.get("evidence") or {}).get("status")}, "overlay op (V17 manifest row)")


def census_records(src):
    """line_id -> [record] from the committed censuses / registers / extracts (each source read once, pinned by sha)."""
    out = {}

    def put(lid, rec):
        if lid and rec["cause"]:
            out.setdefault(lid, []).append(rec)
    for l in src["T638"]["lines"]:
        put(l["line_id"], _rec(638, "T-638 formwork hold census (merged 175443b8)", l.get("cause") or "", kind="T-638 formwork census"))
    for l in src["T639"]["lines"]:
        put(l["line_id"], _rec(639, "T-639 rebar hold census (merged e31e38b5)", l.get("cause") or l.get("hold_text")
                               or "", {"provenance": l.get("hold_source")}, "T-639 rebar census"))
    for l in src["T640"]["lines"]:
        put(l["line_id"], _rec(640, "T-640 finish hold census (merged 36f53264)", l.get("cause") or "", kind="T-640 finish census"))
    for r in src["T642"]["fix_rows"]:
        if r.get("cause"):
            put(r["line_id"], _rec(642, f"T-642 fix row {r['id']} (merged 1c7411a5)", r["cause"], kind="T-642 fix rows"))
    for k, v in src["T644"]["m3_lines"].items():
        put(v["line_id"], _rec(644, f"T-644 lintel {k} (merged cc7f9a48)", v.get("m3_cause_proposed") or "", kind="T-644 lintel census"))
    for c in src["T572"]["components"]:
        if not c.get("line_id"):
            continue
        lo = c.get("low_item") or c.get("low_basis")
        hi = c.get("high_item") or c.get("high_basis")
        txt = (f"{c['kind']}: " + (lo if lo == hi else f"low {lo}; high {hi}")) if (lo or hi) else ""
        put(c["line_id"], _rec(572, f"T-572 HELD-bound component {c['element_id']}", txt, kind="T-572 HELD-bound components"))
    idx_dg = {d["downgrade_id"]: d for d in src["INDEX"]["downgrades"]}
    applied = {k for k, d in idx_dg.items() if d["status"] == "APPLIED"}
    for d in src["DG"]["downgrades"]:
        if d["downgrade_id"] not in applied:
            continue
        ev = "; ".join(f"{e.get('sheet')}: {e.get('printed_value')}" for e in d.get("evidence") or ())
        txt = f"Checker downgrade {d['downgrade_id']} {d.get('basis_label') or ''}" + (f" ({ev})" if ev else "")
        if not idx_dg[d["downgrade_id"]].get("lines_to_held"):
            txt += " [the downgrade moved no line to HELD: the line was HELD already; the Checker record restates why]"
        for lid in d.get("line_ids") or ():
            put(lid, _rec(469, f"Checker downgrade {d['downgrade_id']} (APPLIED in the V3.0.57 index)", txt,
                          kind="Checker downgrade (APPLIED)"))
    for key in ("T449C", "T449R"):
        for e in src[key]["entries"]:
            if e.get("class") == "SUPERSEDED" or not e.get("line_id"):
                continue
            hr = (e.get("rule_result") or {}).get("held_reason")
            if hr:
                put(e["line_id"], _rec(449, f"T-449 correction register ({e.get('rule')})", hr, kind="T-449 correction register"))
    return out


def extract_records(src, after):
    """candidate record extracts; a T-297 bounded record is used only while its bound equals the line's (else stale)."""
    out, stale = {}, []
    for r in src["T297"]["lines"]:
        lid = r["line_id"]
        a = after.get(lid)
        if a is None or a["class"] != "HELD":
            continue
        br = r.get("bounded_range") or {}
        if r["evidence_state"] == "BOUNDED_EXPOSURE":
            same = a["held_low"] is not None and a["held_high"] is not None and br.get("low") is not None and \
                abs(D(a["held_low"]) - D(br["low"])) <= Decimal("0.001") and \
                abs(D(a["held_high"]) - D(br["high"])) <= Decimal("0.001")
        else:
            same = a["held_low"] is None and a["held_high"] is None
        if not same:
            stale.append(lid)
            continue
        rs = (r.get("inputs") or {}).get("reasons") or []
        rfi = (r.get("rfi") or {}).get("question") if isinstance(r.get("rfi"), dict) else r.get("rfi")
        txt = "; ".join(rs) if rs else (rfi or br.get("basis") or r.get("formula") or "")
        if r.get("rule_id"):
            txt += f" [rule {r['rule_id']}]"
        out.setdefault(lid, []).append(_rec(297, "candidate record V3.0.16 (T-297 extract)", txt, kind="candidate record V3.0.16 (T-297)"))
    for r in src["T311"]["lines"]:
        if r.get("rfi_head") and r["line_id"] in after and after[r["line_id"]]["class"] == "HELD":
            out.setdefault(r["line_id"], []).append(_rec(311, "candidate record V3.0.19 (T-311 extract)", r["rfi_head"], kind="candidate record V3.0.19 (T-311)"))
    return out, stale


def resolve_causes(after, ops, records):
    """(a): line_id -> chosen cause record (latest task wins, op on a tie) or None; host chain one step."""
    chosen = {}
    for lid, l in after.items():
        if l["class"] != "HELD":
            continue
        recs = list(records.get(lid, ()))
        op = ops.get(lid)
        oc = op_cause(op) if op else None
        if oc:
            recs.append(dict(oc, _op=1))
        if not recs:
            chosen[lid] = None
            continue
        best = max(recs, key=lambda r: (r["task"], r.get("_op", 0)))
        also = sorted({r["source"] for r in recs if r is not best})
        chosen[lid] = {k: v for k, v in best.items() if k != "_op"} | {"also_stated_by": also}
    for lid, c in list(chosen.items()):
        if c is not None:
            continue
        op = ops.get(lid)
        m = HOST_RE.match(str((op or {}).get("note") or "").strip())
        if m and m.group(1) in after:
            host = after[m.group(1)]
            hc = chosen.get(m.group(1))
            if host["class"] == "HELD" and hc:
                chosen[lid] = _rec(hc["task"], f"host work line {m.group(1)} (material follows its host, one step)",
                                   f"host {host['item_code']} line HELD: {hc['cause']}", {"also_stated_by": []}, "host work line (one step)")
    return chosen


# ---- (b)/(c)/(d) columns and guards ---------------------------------------------------------------------------------

def column_of(lid, line, op, evidence):
    if line["class"] != "RELEASED":
        return None
    if evidence == "UNKNOWN" or evidence is None:
        return UNVERIFIED
    if op is not None:
        return OVERLAY
    if evidence not in CHECKER_STATUSES:
        raise TrialError(f"{lid}: a base line with status {evidence!r} and no op (no Checker binding, no stamp)")
    return WIRED


def guard_held(after):
    for lid, l in after.items():
        if l["class"] == "HELD" and l.get("measured_net") is not None:
            raise TrialError(f"{lid}: a HELD line carries a measured quantity (HELD is never 0, never a value)")


def guard_columns(per_line, ops):
    for p in per_line:
        if p["column"] == WIRED and p["line_id"] in ops:
            raise TrialError(f"{p['line_id']}: an overlay quantity counted as WIRED IN V3.0.58")


def _cacc():
    return {c: Decimal(0) for c in COLUMNS} | {"n": {c: 0 for c in COLUMNS}, "vw": 0}


def columns(per_line):
    """per (group, family, code, unit) / (group, family, unit) / (group, unit) / unit: the three released columns."""
    acc = {"item": {}, "fam": {}, "grp": {}, "unit": {}}
    for p in per_line:
        keys = {"item": (p["group"], p["family"], p["item_code"], p["unit"]),
                "fam": (p["group"], p["family"], p["unit"]), "grp": (p["group"], p["unit"]), "unit": p["unit"]}
        for lvl, k in keys.items():
            a = acc[lvl].setdefault(k, _cacc())
            if p["column"]:
                a[p["column"]] += D(p["measured_net"])
                a["n"][p["column"]] += 1
            if p["evidence"] == "VERIFIED":
                a["vw"] += 1
    return acc


def _cout(a):
    return {"wired": S(a[WIRED]), "overlay": S(a[OVERLAY]), "unverified": S(a[UNVERIFIED]),
            "wired_n": a["n"][WIRED], "overlay_n": a["n"][OVERLAY], "unverified_n": a["n"][UNVERIFIED],
            "verified_whole_lines": a["vw"]}


def column_proof(col, item_acc, fam_acc, grp_acc, unit_acc):
    """(d): wired + overlay + unverified == released at every level, exactly."""
    out = []
    for lvl, ref in (("item", item_acc), ("fam", fam_acc), ("grp", grp_acc), ("unit", unit_acc)):
        for k, a in ref.items():
            c = col[lvl].get(k, _cacc())
            s = c[WIRED] + c[OVERLAY] + c[UNVERIFIED]
            if s != a["released"] or sum(c["n"].values()) != a["released_n"]:
                raise TrialError(f"COLUMN BREAK {lvl} {k}: {s} vs released {a['released']}")
        out.append({"level": lvl, "rows": len(ref), "re_add_exact": True})
    return out


def guard_totals(trades):
    for t in trades:
        for o in [t["subtotal"]] + t["families"] + [i for f in t["families"] for i in f["boq_lines"]]:
            if o["held_n"] and o["total"] is not None:
                raise TrialError(f"{t['trade']} {t['unit']}: a total printed over a HELD line")


# ---- build ----------------------------------------------------------------------------------------------------------

def load_sources():
    src = {k: _json(p) for k, p in SRC.items()}
    src["INDEX"] = _json(INDEX57)
    return src


def trade_tables(item_acc, fam_acc, grp_acc, col, per_line, causes):
    held_by_item = {}
    for p in per_line:
        if p["class"] == "HELD":
            k = (p["group"], p["family"], p["item_code"], p["unit"])
            c = causes.get(p["line_id"])
            h = held_by_item.setdefault(k, {"with_cause": 0, "finding": 0, "by_source": {}})
            if c is None:
                h["finding"] += 1
            else:
                h["with_cause"] += 1
                s = c["kind"]
                h["by_source"][s] = h["by_source"].get(s, 0) + 1
    trades = []
    for grp in list(E.GROUPS) + [E.UNCODED_NO_FAMILY, E.UNCODED_NOT_A_LINE]:
        for unit in sorted(u for (g, u) in grp_acc if g == grp):
            rb = grp == "B11"
            fams = []
            for f in sorted(f for (g, f, u) in fam_acc if g == grp and u == unit):
                lines = []
                for c in sorted(c for (g2, f2, c, u2) in item_acc if (g2, f2, u2) == (grp, f, unit)):
                    k = (grp, f, c, unit)
                    lines.append(dict(item_code=c, **E._out(item_acc[k], unit, rb), **_cout(col["item"][k]),
                                      held_causes=held_by_item.get(k, {"with_cause": 0, "finding": 0, "by_source": {}})))
                fams.append(dict(family=f, **E._out(fam_acc[(grp, f, unit)], unit, rb),
                                 **_cout(col["fam"][(grp, f, unit)]), boq_lines=lines))
            trades.append({"trade": grp, "unit": unit, "subtotal": dict(E._out(grp_acc[(grp, unit)], unit, rb),
                                                                         **_cout(col["grp"][(grp, unit)])),
                           "families": fams})
    return trades


def build(after=None, order=None, master=None, bound=None, src=None, base_ids=None):
    """the trial BOQ; arguments are for the synthetic fixture (defaults: the training-villa overlay V17)."""
    real = after is None
    if real:
        master, src = _json(MASTER), load_sources()
        if master.get("version") != "1.56.0":
            raise TrialError("STALE_INPUT: BOQ_FAMILY_MASTER is not 1.56.0")
        idx, order, after, rep = overlay_v17()
        bound, base_ids = E.bindings(), set(idx)
    guard_held(after)
    ops = last_ops(order)
    owner, item_acc, fam_acc, grp_acc, unit_acc, per_line, uncoded = E.aggregate(after, bound, order, master)
    checks = E.proof(after, item_acc, fam_acc, grp_acc, unit_acc) if real else None
    recs = census_records(src) if real else src.get("records", {})
    stale = []
    if real:
        ext, stale = extract_records(src, after)
        for k, v in ext.items():
            recs.setdefault(k, []).extend(v)
    causes = resolve_causes(after, ops, recs)
    for p in per_line:
        p["column"] = column_of(p["line_id"], after[p["line_id"]], ops.get(p["line_id"]), p["evidence"])
        p["origin"] = "overlay op" if p["line_id"] in ops else "candidate V3.0.58"
        if p["class"] == "HELD":
            c = causes.get(p["line_id"])
            p["cause"] = None if c is None else c["cause"]
            p["cause_source"] = None if c is None else c["source"]
            p["cause_kind"] = None if c is None else c["kind"]
            p["cause_ids"] = [] if c is None else c["ids"]
            p["cause_also_stated_by"] = [] if c is None else c.get("also_stated_by", [])
            p["finding"] = "F-T636-1" if c is None else None
    guard_columns(per_line, ops)
    col = columns(per_line)
    cproof = column_proof(col, item_acc, fam_acc, grp_acc, unit_acc)
    trades = trade_tables(item_acc, fam_acc, grp_acc, col, per_line, causes)
    guard_totals(trades)
    held = [p for p in per_line if p["class"] == "HELD"]
    no_cause = [p for p in held if p["cause"] is None]
    out = {"trades": trades, "per_line": per_line, "column_proof": cproof, "aggregation_proof": checks,
           "unit_grand": {u: dict(E._out(a, u), **_cout(col["unit"][u])) for u, a in sorted(unit_acc.items())},
           "held": {"lines": len(held), "with_cause": len(held) - len(no_cause), "finding_F_T636_1": len(no_cause)},
           "uncoded": [{"bucket": b, "item_code": c, "unit": u, "lines": n} for (b, c, u), n in sorted(uncoded.items())],
           "t297_stale_lines": sorted(stale)}
    if not real:
        return out
    return finish(out, master, src, after, order, rep, fam_acc, base_ids)


def cause_census(per_line):
    by_src, by_trade = {}, {}
    for p in per_line:
        if p["class"] != "HELD":
            continue
        s = "F-T636-1 (no committed record)" if p["cause"] is None else p["cause_kind"]
        by_src[s] = by_src.get(s, 0) + 1
        t = by_trade.setdefault(p["group"], {"held": 0, "with_cause": 0, "finding": 0})
        t["held"] += 1
        t["with_cause" if p["cause"] is not None else "finding"] += 1
    return dict(sorted(by_src.items(), key=lambda x: -x[1])), dict(sorted(by_trade.items()))


def findings_of(out, cov):
    nc = [p for p in out["per_line"] if p["class"] == "HELD" and p["cause"] is None]
    by_code, codes = {}, {}
    for p in nc:
        k = f"{p['group']} {p['item_code']} ({p['unit']})"
        by_code.setdefault(k, []).append(p["line_id"])
        codes[k] = p["item_code"]
    stale = set(out["t297_stale_lines"])
    nofam = [u for u in out["uncoded"] if u["bucket"] == E.UNCODED_NO_FAMILY]
    missing = [c for c in cov if c["overlay_state"].startswith("MISSING")]
    return {
        "F-T636-1": {"what": "HELD lines whose cause no committed record states (listed by line id, never dropped, "
                             "never given a typed cause); the full candidate line records (rfi / notes / rule of each "
                             "line) are a private-run output (V3_0_58_BOQ_LINES.json, not committed): the causes here "
                             "are read from the committed overlay ops, censuses, registers and extracts only",
                     "lines": len(nc), "by_item_code": {k: {"n": len(v), "line_ids": sorted(v), "open_board_row": open_row(codes[k]),
                                                            "stale_v3_0_16_record": len(stale & set(v))}
                                                        for k, v in sorted(by_code.items(), key=lambda x: -len(x[1]))}},
        "F-T636-2": {"what": "UNCODED (NO_FAMILY) lines under master 1.56.0 (expected 0)",
                     "lines": sum(u["lines"] for u in nofam), "codes": nofam},
        "F-T636-3": {"what": "T-297 V3.0.16 rebar records not used as a cause because the line's bound moved since "
                             "(stale extract)", "lines": len(out["t297_stale_lines"])},
        "F-T636-5": {"what": "RELEASED lines whose overlay op stamps the s.5 status HELD (a released low end whose "
                             "companion line carries the HELD part, R-T638-1 / T-625 pattern): placed in the OVERLAY "
                             "column as the merged fix row states; the stamp should name the released part's status",
                     "lines": len(bad := [p["line_id"] for p in out["per_line"]
                                          if p["class"] == "RELEASED" and p["evidence"] == "HELD"]),
                     "line_ids": sorted(bad)},
        "F-T636-4": {"what": "master families with no line in the overlay (no source, no method, or not wired)",
                     "families": [f"{c['family']} {c['item']} [{c['capability']}]" for c in missing]},
    }


def contains_of(out, cov, by_trade):
    tr = out["trades"]
    rel = [f"{t['trade']} {t['unit']} {t['subtotal']['released_n']} released lines" for t in tr
           if t["subtotal"]["released_n"] and not t["trade"].startswith("UNCODED")]
    held = [f"{t['trade']} {t['unit']} {t['subtotal']['held_n']}" for t in tr
            if t["subtotal"]["held_n"] and not t["trade"].startswith("UNCODED")]
    totals = [f"{t['trade']} {t['unit']} {t['subtotal']['total']}" for t in tr
              if t["subtotal"]["total"] is not None and not t["trade"].startswith("UNCODED")]
    miss_groups = sorted({c["group"] for c in cov} - {t["trade"] for t in tr})
    return [
        "WILL contain, for every trade that has lines: each BOQ line with its released quantity split into WIRED IN "
        "V3.0.58 / FIX ROW NOT YET WIRED (overlay) / UNVERIFIED, and its HELD lines counted with their cause: "
        + "; ".join(rel) + ".",
        "WILL show HELD lines as HELD with a cause or with finding F-T636-1 by line id, never as 0 and never summed: "
        + "; ".join(held) + f". Causes found for {out['held']['with_cause']} of {out['held']['lines']} HELD lines.",
        "WILL print a trade x unit TOTAL only where every component is valued: " + (", ".join(totals) or "none") + ".",
        "will NOT contain any line for trade group(s) " + (", ".join(miss_groups) or "none") + " (no family carries a "
        "line), nor for the families listed in F-T636-4.",
        "will NOT be a complete BOQ: it is NOT called complete while any trade is missing or carries HELD lines; "
        "no unit grand is a total; the document is a non-candidate trial built on the V3.0.58 candidate + overlay V17; "
        "the released default (V2.9 + route G) is unchanged and only Gate B merges move the candidate.",
        "will NOT mix the freelancer reference with engineering verification: it is the appendix (scorecard V11 "
        "sections beside, their own trade labels); no accuracy figure.",
    ]


def finish(out, master, src, after, order, rep, fam_acc, base_ids):
    cov = E.family_coverage(master, fam_acc)
    cov_count = {}
    for c in cov:
        k = c["overlay_state"].split(" ")[0]
        cov_count[k] = cov_count.get(k, 0) + 1
    by_src, by_trade = cause_census(out["per_line"])
    st = {s: sum(1 for l in out["per_line"] if l["evidence"] == s) for s in E.STATUSES}
    trade_counts = {}
    for t in out["trades"]:
        s = t["subtotal"]
        trade_counts[f"{t['trade']}|{t['unit']}"] = {
            "live": s["live_lines"], "released": s["released_n"], "wired": s["wired_n"], "overlay": s["overlay_n"],
            "unverified": s["unverified_n"], "held": s["held_n"], "verified_whole_lines": s["verified_whole_lines"]}
    out.update({
        "schema": SCHEMA, "rule": RULE, "task": "T-636",
        "candidate": M9.T580.CANDIDATE, "overlay": "WIRING MANIFEST V17 (T-641, merged, engine 57620ab8)",
        "master": "BOQ_FAMILY_MASTER 1.56.0 (T-637, merged deb7b86a)",
        "merged_since_v17_not_in_overlay": MERGED_SINCE_V17,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in (MASTER, SCORECARD, V17, INDEX57, *SRC.values())},
        "not_claimed": "development villa trial BOQ; nothing wired, nothing released (V3.0.58 NOT RELEASED; V2.9 + "
                       "route G unchanged); no accuracy figure; freelancer agreement is never proof",
        "lines": {"base_v3_0_58": len(base_ids), "after_v17": len(after),
                  "released": sum(1 for l in out["per_line"] if l["class"] == "RELEASED"),
                  "held": out["held"]["lines"], "excluded": sum(1 for l in out["per_line"] if l["class"] == "EXCLUDED")},
        "evidence_lines": st, "verified_whole_lines": st["VERIFIED"],
        "trade_counts": trade_counts, "held_cause_by_source": by_src, "held_cause_by_trade": by_trade,
        "family_coverage": cov, "family_coverage_count": dict(sorted(cov_count.items())),
        "overlay_flagged_ops": [r for r in rep["rows"] if r["status"] != "APPLIED"],
        "appendix_freelancer_reference_v11": E.scorecard_beside(_json(SCORECARD)),
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    })
    out["findings"] = findings_of(out, cov)
    out["contains"] = contains_of(out, cov, by_trade)
    return out


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n"


# ---- report ---------------------------------------------------------------------------------------------------------

def _rng(o):
    return "" if not o["held_bounded_n"] else f"{o['held_low']} .. {'OPEN' if o['held_high'] is None else o['held_high']}"


def _tot(o):
    return o["total"] if o["total"] is not None else o["total_state"]


def render_md(b):
    L = ["# T-636 the 10 Nov trial BOQ (generated; R-T636-1)", "",
         f"Candidate {b['candidate']}; overlay {b['overlay']}; grouping {b['master']}. {b['not_claimed']}.", "",
         "Columns: WIRED = in the V3.0.58 candidate with a Checker binding; OVERLAY = a merged fix row the overlay "
         "carries, not yet wired; UNVERIFIED = no Checker binding and no s.5 stamp. The three re-add exactly to the "
         "released quantity. HELD lines are never 0 and never summed; a total is printed only where every component "
         "is valued. Rebar: kg computed, t displayed (OWNER_RULE_REBAR s.1).", "",
         "## 1. Headline", "",
         f"- Lines after V17: {b['lines']['after_v17']} (base V3.0.58 {b['lines']['base_v3_0_58']}): released "
         f"{b['lines']['released']}, HELD {b['lines']['held']}, excluded {b['lines']['excluded']} (not BOQ lines).",
         f"- HELD lines with a recorded cause: {b['held']['with_cause']} / {b['held']['lines']}; finding F-T636-1 "
         f"(no committed record): {b['held']['finding_F_T636_1']} lines, listed by id in the JSON.",
         "- Cause sources: " + ", ".join(f"{k} {v}" for k, v in b["held_cause_by_source"].items()) + ".",
         "- Evidence per live line (WORKFLOW_CONTROLS s.5): " + ", ".join(f"{k} {v}" for k, v in
                                                                         b["evidence_lines"].items() if v) + ".",
         f"- Checker-verified whole lines: {b['verified_whole_lines']}. No trade subtotal is VERIFIED.",
         "- Families (master 1.56.0): " + ", ".join(f"{k} {v}" for k, v in b["family_coverage_count"].items()) + ".",
         "", "## 2. Trade tables (trade x unit)", "",
         "A trade x unit figure re-adds different items: it is the arithmetic proof line, not a physical quantity.", "",
         "| Trade | Unit | Live | Released n | Released | WIRED | OVERLAY | UNVERIFIED | VW lines | HELD blank | "
         "HELD bounded (low .. high) | Total state | HELD with cause / F-T636-1 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    ht = b["held_cause_by_trade"]
    for t in b["trades"]:
        o = t["subtotal"]
        h = ht.get(t["trade"], {})
        L.append(f"| {t['trade']} | {t['unit']} | {o['live_lines']} | {o['released_n']} | {o['released']} | "
                 f"{o['wired']} | {o['overlay']} | {o['unverified']} | {o['verified_whole_lines']} | "
                 f"{o['held_blank_n']} | {o['held_bounded_n']} {_rng(o)} | {_tot(o)} | "
                 f"{h.get('with_cause', 0)} / {h.get('finding', 0)} (trade, all units) |")
    L += ["", "Rebar display: " + "; ".join(
        f"{t['trade']} released {t['subtotal']['released']} kg = {t['subtotal']['released_t_display']} t (released part "
        f"only; {t['subtotal']['total_state']})" for t in b["trades"] if "released_t_display" in t["subtotal"]) + ".",
          "", "## 3. BOQ lines (family x item code x unit)", "",
          "| Trade | Family | Item code | Unit | Live | Released | WIRED | OVERLAY | UNVERIFIED | HELD blank | "
          "HELD bounded | BOQ line total | HELD cause (sources) / F-T636-1 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in b["trades"]:
        for f in t["families"]:
            for i in f["boq_lines"]:
                hc = i["held_causes"]
                src = ", ".join(f"{k} {v}" for k, v in sorted(hc["by_source"].items()))
                L.append(f"| {t['trade']} | {f['family']} | {i['item_code']} | {t['unit']} | {i['live_lines']} | "
                         f"{i['released']} | {i['wired']} | {i['overlay']} | {i['unverified']} | {i['held_blank_n']} | "
                         f"{i['held_bounded_n']} {_rng(i)} | {_tot(i)} | "
                         + (f"{hc['with_cause']} ({src}) / {hc['finding']}" if i["held_n"] else "-") + " |")
    L += ["", "## 4. Aggregation proof", "",
          "| Unit | Lines | Released lines | BOQ lines | Families | Trades | Unit grand | Overlay totals | HELD | Re-adds |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for c in b["aggregation_proof"]:
        L.append(f"| {c['unit']} | {c['lines']} | {c['released_lines_sum']} | {c['boq_lines_sum']} | {c['families_sum']}"
                 f" | {c['trades_sum']} | {c['unit_grand']} | {c['overlay_totals_sum']} | {c['held_n']} | "
                 f"{'EXACT' if c['re_adds_exactly'] else 'BREAK'} |")
    L += ["", "Three-column re-add (WIRED + OVERLAY + UNVERIFIED = released): " + ", ".join(
        f"{c['level']} {c['rows']} rows EXACT" for c in b["column_proof"]) + ". No unit grand is a total (each unit "
          "carries HELD lines).", "",
          "| Unit | Released | WIRED | OVERLAY | UNVERIFIED | VW lines | State |", "|---|---|---|---|---|---|---|"]
    for u, o in b["unit_grand"].items():
        L.append(f"| {u} | {o['released']} | {o['wired']} | {o['overlay']} | {o['unverified']} | "
                 f"{o['verified_whole_lines']} | {_tot(o)} |")
    L += ["", "## 5. Findings", ""]
    for k, v in b["findings"].items():
        extra = ""
        if k == "F-T636-1":
            extra = f" {v['lines']} lines. By code: " + "; ".join(
                f"{c} {x['n']}" + (f" [{x['open_board_row']}]" if x["open_board_row"] else "") +
                (f" ({x['stale_v3_0_16_record']} with a stale V3.0.16 record)" if x["stale_v3_0_16_record"] else "")
                for c, x in v["by_item_code"].items()) + "."
        elif k == "F-T636-4":
            extra = " " + "; ".join(v["families"]) + "."
        elif "lines" in v:
            extra = f" Lines: {v['lines']}."
        L.append(f"- {k}: {v['what']}.{extra}")
    L += ["", "## 6. What this trial BOQ WILL and WILL NOT contain", ""] + [f"- {x}" for x in b["contains"]]
    L += ["", "## Appendix: freelancer reference (scorecard V11 sections, own trade labels; never engineering proof)", "",
          "| Section | Trade label | Unit | Status | Reference | Engine valued | Difference |",
          "|---|---|---|---|---|---|---|"]
    for r in b["appendix_freelancer_reference_v11"]:
        L.append(f"| {r['section']} | {r['trade_label']} | {r['unit']} | {r['line_status']} | {r['reference_total']} | "
                 f"{r['engine_valued']} | {r['difference']} |")
    L.append("")
    return "\n".join(L)


CSV_FIELDS = ("trade", "family", "item_code", "unit", "live_lines", "released_n", "released", "wired", "overlay",
              "unverified", "verified_whole_lines", "held_n", "held_blank_n", "held_bounded_n", "held_low", "held_high",
              "total", "total_state", "held_with_cause", "held_finding")


def render_csv(b):
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=CSV_FIELDS, lineterminator="\n")
    w.writeheader()
    for t in b["trades"]:
        for f in t["families"]:
            for i in f["boq_lines"]:
                w.writerow({**{k: i.get(k) for k in CSV_FIELDS if k in i}, "trade": t["trade"], "family": f["family"],
                            "unit": t["unit"], "held_with_cause": i["held_causes"]["with_cause"],
                            "held_finding": i["held_causes"]["finding"]})
    return s.getvalue()


def write_outputs():
    b = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    OUT_MD.write_text(render_md(b), encoding="utf-8")
    OUT_CSV.write_text(render_csv(b), encoding="utf-8")
    return b
