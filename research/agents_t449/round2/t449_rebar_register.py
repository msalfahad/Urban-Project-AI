"""T-449 round 2 (REINFORCEMENT): the A1 correction register of every per-project input that reaches a reinforcement
(STR.REBAR) line of the candidate of record.

Owner follow-up directive 2026-11-02 (MISSION.md, A1): every project-specific correction is
  (A) a DRAWING-DERIVED RULE (reusable logic with tests),
  (B) a DECLARED PROJECT FACT (per-project config, URBAN_PROJECT_CONFIG_V1, engine/project_config.py), or
  (C) an UNEXPLAINED PATCH (made only to match the freelancer or an earlier engine result): removed.

Census: every project-input builder the candidate run feeds (research/agents_t442/v3042_run.py, V3.0.2 .. V3.0.42) is
built and scanned; a builder REACHES a reinforcement line when its method creates or changes STR.REBAR lines from it:
  V3.0.2  footing_rebar      the footing reinforcement facts (schedule size unit, cover, end treatment)
  V3.0.3  ledgers            column / ground-system / beam steel hand ledgers (T-148, T-138 + T-141, T-149)
  V3.0.5  ledgers            suspended-slab and stair / pool / tank steel ledgers (T-152, T-166); DOME_RING is concrete
  V3.0.24 unit_mass + fixes  REBAR_FORMULA text of the 350 released lines (count x length x kg/m = net)
  V3.0.27 lines              196 suspended-slab DEVELOPMENT / TOP lines re-based by support class (T-307, T-316)
Every other builder that names reinforcement does so in text only (a 'beside' list, a held note, guard evidence):
listed with the reason. The A1 directive names the V3.0.16+ inputs; the V3.0.2 .. V3.0.5 entries are classed too,
because they are the inputs that carry the quantities V3.0.24 / V3.0.27 re-state.

For every entry: version, line id (when the input names it or the V3.0.24 findings ledger maps it), state, patch,
class, rule, the rule's result from the declared facts (research/agents_t449/round2/*.rebar_facts.json) plus the
Checker-merged drawing readings, the residual named:
  A-REPRODUCED   the generic rule + declared facts give the patch's state and quantity (residual named)
  A-SPECIFIED    drawing-derived and Checker-verified, rule named, its generic code not written / not reproducing
  B              the entry is itself a declared project fact
  C              its basis is a freelancer / benchmark / earlier engine figure: removed (none found)

Read-only: imports the merged builders (each pins its own ledgers by sha256), writes only where it is told to.

    python3 -I research/agents_t449/round2/t449_rebar_register.py [out_dir] [--facts-out FILE]
"""

from __future__ import annotations

import csv
import hashlib
import importlib
import importlib.util
import io
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.project_config import parse_project_config, load_project_config  # noqa: E402
from engine.source import rebar_basis_rules_v1 as R  # noqa: E402

RUN = ROOT / "research/agents_t442/v3042_run.py"
FACTS = HERE / "DEVELOPMENT-VILLA-T131.rebar_facts.json"
T334 = ROOT / "research/agents_t334/V3_0_21_LINE_STATE_FINDINGS.csv"
T306 = ROOT / "research/agents_t306/SLAB_SPREAD_DECOMPOSITION_T306.csv"
T307_DETAIL = ROOT / "research/agents_t307/BAR_END_DETAIL_T307.csv"
T316_DETAIL = ROOT / "research/agents_t316/TOP_END_DETAIL_T316.csv"
PINS = {T334: "8988238e3653a731810bc052e6807e7e988922603dfbb9effa0c7e0e8d549bce"}
PID = "development-villa-t131"
NET_TOL = 0.0005          # the lines print kg to 3 decimals (export tolerance)
LEN_PRINT = 0.00005       # the ledgers print length_m to 4 decimals
POP_TOL = 0.005           # acceptance: +-0.5 % per bar population in t
C_WORDS = re.compile(r"freelancer|workbook|benchmark|reference boq|to match", re.I)
REBAR_TEXT = re.compile(r"STR\.REBAR|rebar|reinforc", re.I)

REACH = {   # version -> (input section, why it reaches STR.REBAR lines)
    "ARCH_TAKEOFF_V3.0.2": ("footing_rebar", "arch_v302 footing reinforcement lines from the p.9 schedule"),
    "ARCH_TAKEOFF_V3.0.3": ("ledgers", "arch_v303 one STR.REBAR line per ledger record (route G steel superseded)"),
    "ARCH_TAKEOFF_V3.0.5": ("ledgers[STR.REBAR]", "arch_v305 slab and stair / pool / tank steel lines"),
    "ARCH_TAKEOFF_V3.0.24": ("unit_mass + fixes[REBAR_FORMULA]", "arch_v3024 REBAR_FORMULA text of released lines"),
    "ARCH_TAKEOFF_V3.0.27": ("lines", "arch_v3027 slab DEVELOPMENT / TOP lines re-based by support class"),
}
TEXT_ONLY = {   # version -> why a reinforcement word in its input reaches no line
    "ARCH_TAKEOFF_V3.0.7": "dome / pool steel listed 'beside' only (arch_v307 makes no STR.REBAR line)",
    "ARCH_TAKEOFF_V3.0.23": "parapet reinforcement named HELD in text (arch_v3023 PARAPET_REBAR: no rebar change)",
}
SLAB_STATE = {"NOT_APPLICABLE_WITH_EVIDENCE": R.NOT_APPLICABLE, "BOUND_PART_WITH_HELD": R.BOUND_PART_WITH_HELD,
              "HELD": R.HELD}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _rows(p):
    return list(csv.DictReader(io.StringIO(Path(p).read_text(encoding="utf-8"))))


def _f(v):
    return None if v in ("", None) else float(v)


def _slug(s):   # = engine/source/arch_v303._slug (element ids of the V3.0.3 lines)
    return re.sub(r"[^A-Za-z0-9]+", "_", str(s)).strip("_").upper()[:48] or "X"


def _builders():
    """version -> (module name, function) as the candidate run calls them."""
    src = RUN.read_text(encoding="utf-8")
    for m in re.findall(r'ROOT / "research" / "(agents_t\d+)"', src) + ["agents_t442"]:
        p = str(ROOT / "research" / m)
        if p not in sys.path:
            sys.path.insert(0, p)
    imps = dict((b, a) for a, b in re.findall(r"import (\w+) as (L\d+)", src))
    out = {"ARCH_TAKEOFF_V3.0.2": ("v302_run", "INPUTS", False),
           "ARCH_TAKEOFF_V3.0.3": ("t151_ledgers", "inputs", True),
           "ARCH_TAKEOFF_V3.0.5": ("t179_ledgers", "inputs", True)}
    for v, L, fn, arg in re.findall(r'"v(30\d+)_inputs.json"\)\.write_text\(json\.dumps\((L\d+)\.(\w+)\((\w*)', src):
        ver = "ARCH_TAKEOFF_V3.0." + v[2:]
        out.setdefault(ver, (imps[L], fn, bool(arg)))
    return dict(sorted(out.items(), key=lambda kv: int(kv[0].rsplit(".", 1)[1])))


def _build(mod, fn, with_pid):
    """the builder called exactly as the candidate run calls it (with the project id or without)."""
    f = getattr(importlib.import_module(mod), fn)
    if not callable(f):
        return f
    return f(PID) if with_pid else f()


def census():
    rows, docs = [], {}
    for ver, (mod, fn, with_pid) in _builders().items():
        d = _build(mod, fn, with_pid)
        docs[ver] = d
        txt = json.dumps(d, ensure_ascii=False, sort_keys=True)
        words = len(REBAR_TEXT.findall(txt))
        if ver in REACH:
            reach, why = "REACHES", REACH[ver][1]
        elif ver in TEXT_ONLY:
            reach, why = "TEXT_ONLY", TEXT_ONLY[ver]
        elif words:
            reach, why = "TEXT_ONLY", ("reinforcement named only in the default-guard section (generic convention ids "
                                       "of engine/source/default_guard.py; printed CB bar values: see guard entries)")
        else:
            reach, why = "NONE", "no reinforcement in the input"
        rows.append({"version": ver, "builder": f"{mod}.{fn}", "schema": d.get("schema") if isinstance(d, dict)
                     else None, "rebar_words": words, "reach": reach, "why": why,
                     "section": REACH.get(ver, ("",))[0]})
    return rows, docs


def _entry(version, line_id, element, action, patch, cls, rule, **kw):
    e = {"version": version, "line_id": line_id, "element_id": element, "action": action, "patch": patch,
         "class": cls, "rule": rule}
    e.update(kw)
    return e


def _res(res):
    return {"state": res.state, "value": res.value, "low": res.low, "high": res.high, "formula": res.formula,
            "facts_used": list(res.facts_used), "held_reason": res.held_reason}


def _close(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


# ================================================================================================ V3.0.3 / V3.0.5
def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _print_tol(x):
    """half a unit of the last printed decimal of a ledger figure (at least the 3 dp kg tolerance)."""
    dec = len(repr(float(x)).split(".")[1].rstrip("0")) if "." in repr(float(x)) else 0
    return max(0.5 * 10 ** -dec, NET_TOL) + 1e-9


T138_CSV = ROOT / "research/agents_t138/T138_MEMBERS.csv"
_T138_SECTIONS = None


def _sections():
    """the p.13 ground-beam section table as the merged T-138 ledger reads it (detail -> printed bar groups)."""
    global _T138_SECTIONS
    if _T138_SECTIONS is None:
        spec = importlib.util.spec_from_file_location("t138_hand_ledger_t449", ROOT / "research/agents_t138/"
                                                      "t138_hand_ledger.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _T138_SECTIONS = {k: (None if v is None else [(n, d) for _, n, d in v["bars"]]) for k, v in m.DETAILS.items()}
    return _T138_SECTIONS


def _section_candidates(r):
    """a ground-beam span's bar-end record held over p.13 section candidates -> (ends, {detail: bar groups or None}):
    the printed bar ends of its BAR ENDS row and the candidate details of its longitudinal rows (T-138 ledger);
    None when the merged ledger does not name them."""
    rows = [x for x in _rows(T138_CSV) if x["member"] == r["element"]]
    be = next((x for x in rows if x["component"].startswith("BAR ENDS")), None)
    lon = next((x for x in rows if x["component"] in ("TOP", "BOTTOM", "BOTTOM_ROW_1") and x["detail"]), None)
    m = re.match(r"\s*(\d+) ends?", (be or {}).get("count") or "")
    if not m or lon is None or int(m.group(1)) == 0:
        return None
    secs = _sections()
    return int(m.group(1)), {c: secs.get(c) for c in lon["detail"].split("/")}


def ledger_entries(cfg, ver, doc, t334, superseded=None):
    superseded = superseded or {}
    out = []
    for lg in doc["ledgers"]:
        if lg.get("item_code", "STR.REBAR") != "STR.REBAR" or lg.get("unit", "kg") != "kg":
            continue
        piece = lg["piece"]
        for r in lg["records"]:
            st = r["state"]
            eid = f"HL:{piece}:{r['element']}:{_slug(r['component'])}" + (f":{_slug(r['part'])}" if r.get("part")
                                                                            else "")
            lid = t334.get(eid, {}).get("line_id")
            base = dict(piece=piece, floor=r.get("floor"), component=r["component"], dia_mm=r.get("dia_mm"),
                        count=r.get("count"), length_m=r.get("length_m"))
            if C_WORDS.search(json.dumps(r, ensure_ascii=False)):
                out.append(_entry(ver, lid, eid, st, r.get("kg"), "C", None, **base))
                continue
            if st == "RELEASED":
                res = R.bar_population(cfg, count=r.get("count"), length=r.get("length_m"), d_mm=r.get("dia_mm"),
                                       schedule_row=r.get("schedule_row"))
                net = _f(t334.get(eid, {}).get("measured_net"))
                u = R.unit_mass(cfg, r.get("dia_mm"))[0] if r.get("dia_mm") else None
                tol = NET_TOL + (r.get("count") or 0) * (u or 0.0) * LEN_PRINT   # 3 dp kg + 4 dp length print
                ok = res.state == R.VALUED and _close(res.value, r["kg"], tol) and _close(res.value, net, tol)
                e = _entry(ver, lid, eid, st, {"kg": r["kg"], "line_net": net}, "A-REPRODUCED" if ok else "A-SPECIFIED",
                           res.rule, rule_result=_res(res), tol_kg=round(tol, 6), **base)
                if res.value is not None:
                    e["rule_minus_patch_kg"] = round(res.value - r["kg"], 6)
                if not ok:
                    e["not_reproduced"] = f"rule {res.value} vs ledger {r['kg']} / line {net} (tol {tol:.6f})"
                out.append(e)
            elif st == "HELD_RANGE" and (piece, r["element"], r["component"].split(" ")[0].upper(),
                                         r.get("part")) in superseded:
                succ = superseded[(piece, r["element"], r["component"].split(" ")[0].upper(), r.get("part"))]
                out.append(_entry(ver, succ["line_id"], eid, st, {"low": r["low"], "high": r["high"]}, "SUPERSEDED",
                                  succ["rule"], superseded_by=f"{succ['version']} {succ['line_id']} ({succ['class']})",
                                  why="the line was re-based end by end by a later version: this input's range no "
                                      "longer reaches the candidate; the line is classed at its successor", **base))
                continue
            elif st == "HELD_RANGE":
                rd = r.get("readings") or {}
                txt = (r["component"] + " " + (r.get("range_basis") or "")).lower().replace(" ", "")
                info = dict(r.get("info") or {}, **{k: v for k, v in rd.items() if k in ("count_A", "count_B")})
                if rd and "candidate marks" in (r.get("range_basis") or ""):
                    res = R.candidates_range({k: tuple(v) for k, v in rd.items()})
                elif rd and not ("counta" in txt and "countb" in txt):
                    res = R.readings_range(rd if ver.endswith("V3.0.3") else
                                           {k: v for k, v in rd.items() if k.endswith("_kg")})
                elif "counta" in txt and "countb" in txt and _num(info.get("count_A")) and _num(info.get("count_B")):
                    # each end takes its own count reading: A x 2 ends x 40 d .. B x 2 ends x 70 d
                    lo_r = R.development_range(cfg, count=2 * info["count_A"], d_mm=r.get("dia_mm"), k_low=40,
                                               k_high=70)
                    hi_r = R.development_range(cfg, count=2 * info["count_B"], d_mm=r.get("dia_mm"), k_low=40,
                                               k_high=70)
                    res = R.RuleResult(lo_r.rule, R.HELD, None, low=lo_r.low, high=hi_r.high,
                                       formula=f"count A {info['count_A']:g} x 2 ends x 40 d .. count B "
                                               f"{info['count_B']:g} x 2 ends x 70 d", facts_used=lo_r.facts_used,
                                       held_reason=lo_r.held_reason)
                elif "40d..70d" in txt:
                    n, d = r.get("count"), r.get("dia_mm")
                    if n is None and piece == "GROUND_SYSTEM_STEEL" and _section_candidates(r):
                        ends, cands = _section_candidates(r)
                        res = R.candidates_range({c: (None if g is None else (lambda x: (x.low, x.high))(
                            R.development_range_groups(cfg, g, ends=ends, k_low=40, k_high=70)))
                            for c, g in cands.items()})
                    else:
                        res = R.development_range(cfg, count=n, d_mm=d, k_low=40, k_high=70)
                else:
                    res = R.readings_range(None)
                ok = (res.state == R.HELD and _close(res.low, r["low"], _print_tol(r["low"]))
                      and _close(res.high, r["high"], _print_tol(r["high"])))
                e = _entry(ver, lid, eid, st, {"low": r["low"], "high": r["high"]},
                           "A-REPRODUCED" if ok else "A-SPECIFIED", res.rule, rule_result=_res(res),
                           range_basis=r.get("range_basis"), **base)
                if not ok:
                    e["not_reproduced"] = (f"rule {res.low} .. {res.high} vs ledger {r['low']} .. {r['high']}"
                                           f" ({res.held_reason or 'basis outside this rule version'})")
                out.append(e)
            else:   # HELD_DEFINED / HELD_LOWER_BOUND / UNQUANTIFIED: the rule keeps the line HELD, no value
                res = R.bar_population(cfg, count=None, length=None, d_mm=None, schedule_row=st)
                e = _entry(ver, lid, eid, st, {k: r[k] for k in ("kg", "low") if k in r}, "A-REPRODUCED", res.rule,
                           rule_result=_res(res), shown_not_added=True, **base)
                out.append(e)
    return out


# ================================================================================================ V3.0.2
def footing_entries(doc):
    fr = doc["footing_rebar"]
    out = []
    for key in ("size_unit", "cover", "end_treatment"):
        out.append(_entry("ARCH_TAKEOFF_V3.0.2", None, f"footing_rebar.{key}", "DECLARE", fr[key], "B", None,
                          fact_status="NOT_YET_IN_CONFIG",
                          why=("a drawing-read project fact (p.9 schedule header / p.8 note 22 / end treatment); the "
                               "config refuses a fact without the line ids it moves, and the footing reinforcement "
                               "line ids come from a candidate run: declared at the wiring row")))
    return out


# ================================================================================================ guard evidence
GUARD_REBAR_PARAMS = ("CB_BOTTOM_EXTENSION_M", "CB_SUPPORT_BAR_EXTENT_FRAC")


def guard_entries(docs):
    """printed values in the default-guard evidence that concern reinforcement conventions (route G continuous-beam
    steel). The guard holds a line's STATE when a default convention has no printed value; it never sets a quantity.
    The route G continuous-beam steel lines are superseded on the candidate by the V3.0.3 BEAM_STEEL ledger (scope
    GF / 1F / 2F beams, NOT_APPLICABLE_WITH_EVIDENCE), so these values reach no live reinforcement quantity."""
    first = None
    for ver, d in docs.items():
        ev = ((d.get("guard") or {}).get("evidence") or {}) if isinstance(d, dict) else {}
        if any(p.get("param") in GUARD_REBAR_PARAMS for p in ev.get("printed") or ()):
            first = (ver, ev)
            break
    if first is None:
        return []
    ver, ev = first
    return [_entry(ver, None, p["id"], "GUARD_EVIDENCE", {"param": p["param"], "value": p["value"], "unit": p["unit"]},
                   "B", None, fact_status="NOT_YET_IN_CONFIG", reach="STATE_ONLY (superseded route G lines)",
                   why="a printed value (p.11 / p.12 typical continuous-beam detail) the default guard cites; it moves "
                       "no live quantity (route G CB steel superseded by V3.0.3); declared with the guard's own "
                       "wiring decision (F-T449-4)", basis=p.get("basis"), doc=p.get("doc"))
            for p in ev["printed"] if p.get("param") in GUARD_REBAR_PARAMS]


# ================================================================================================ V3.0.24
def formula_entries(doc, t334_by_line, ledger_by_line):
    out = []
    um = doc["unit_mass"]
    out.append(_entry("ARCH_TAKEOFF_V3.0.24", None, "unit_mass.method", "DECLARE", um["method"], "B", None,
                      fact_id=R.F_UNIT_MASS, fact_status="DECLARED"))
    out.append(_entry("ARCH_TAKEOFF_V3.0.24", None, "unit_mass.length_decimals", "TOLERANCE",
                      um["length_decimals"], "A-REPRODUCED", "R-REBAR-POPULATION-1",
                      why="a print property of the merged ledgers (length_m to 4 decimals), not a project fact: it is "
                          "the reproduction tolerance count x kg/m x 0.5e-4 of this register"))
    for f in doc["fixes"]:
        row = t334_by_line.get(f["line_id"], {})
        if row.get("item_code") != "STR.REBAR":
            continue
        led = ledger_by_line.get(f["line_id"])
        ok = led is not None and led["class"] == "A-REPRODUCED"
        out.append(_entry("ARCH_TAKEOFF_V3.0.24", f["line_id"], row.get("element_id"), f["kind"],
                          {"net": _f(row.get("measured_net"))}, "A-REPRODUCED" if ok else "A-SPECIFIED",
                          "R-REBAR-POPULATION-1",
                          why="text only: the printed 'count x length x kg/m = net' is the rule's own formula; "
                              "reproduced when the rule gives the line's net from its record",
                          ledger_entry_class=None if led is None else led["class"]))
    return out


# ================================================================================================ V3.0.27
def slab_entries(cfg, doc):
    t306 = {r["line_id"]: r for r in _rows(T306)}
    dev, top = defaultdict(list), defaultdict(list)
    for r in _rows(T307_DETAIL):
        dev[r["line_id"]].append(R.BarEnd(r["reading"], r["support"], _f(r["width_m"]), _f(r["seg_len_m"]), None,
                                          int(r["bar"]), int(r["segment"]), r["end"]))
    for r in _rows(T316_DETAIL):
        s, w = r["support"], _f(r["width_m"])
        if s == "CONTINUOUS" and w is None:          # T-316: the band gap stands for an unmarked band's width
            w = _f(r["t152_gap_m"])
        oth = _f(r["t152_other_chord_m"]) if s == "CONTINUOUS" else None   # T-316 records it for CONTINUOUS only
        top[r["line_id"]].append(R.BarEnd(r["reading"], s, w, _f(r["seg_len_m"]), oth, int(r["bar"]),
                                          int(r["segment"]), r["end"]))
    out = []
    for x in doc["lines"]:
        lid, t = x["line_id"], t306[x["line_id"]]
        if C_WORDS.search(json.dumps(x, ensure_ascii=False)):
            out.append(_entry("ARCH_TAKEOFF_V3.0.27", lid, x["element"], x["status"], None, "C", None))
            continue
        if x["population"].startswith("DEVELOPMENT"):
            res = R.slab_development_line(cfg, dev[lid], float(t["d_mm"]))
            want = x.get("valued")
            ok = res.state == SLAB_STATE[x["status"]] and (
                want is None or (_close(res.low, want["low"], NET_TOL) and _close(res.high, want["high"], NET_TOL)))
            e = _entry("ARCH_TAKEOFF_V3.0.27", lid, x["element"], x["status"],
                       {"valued": want, "before": x["before"]}, "A-REPRODUCED" if ok else "A-SPECIFIED",
                       res.rule, rule_result=_res(res), population=x["population"], label_status=t["label_status"])
            if not ok:
                e["not_reproduced"] = (f"rule {res.state} {res.low} .. {res.high} vs patch {x['status']} {want}; "
                                       + ("bare label read as 'n bars in all' widens the bound (T-306 F-04): a "
                                          "label-meaning reading outside this rule version"
                                          if t["label_status"] == "HELD_LABEL" else "cause not named"))
        else:
            res = R.slab_top_line(cfg, top[lid], full_top_mesh=int(t["layers"]) == 2)
            want = x.get("p15_valued")
            if want is None:
                ok = (x["status"] == "HELD" and res.state == R.HELD) or (
                    x["status"] == "UNRESOLVED_TB_PANEL" and res.state == R.UNRESOLVED)
            else:
                ok = _close(res.low, want["low"], NET_TOL) and _close(res.high, want["high"], NET_TOL)
            e = _entry("ARCH_TAKEOFF_V3.0.27", lid, x["element"], x["status"],
                       {"p15_valued": want, "before": x["before"]}, "A-REPRODUCED" if ok else "A-SPECIFIED",
                       res.rule, rule_result=_res(res), population=x["population"], printed=t["printed"],
                       line_d_mm=float(t["d_mm"]))
            if not ok:
                e["not_reproduced"] = f"rule {res.state} {res.low} .. {res.high} vs patch {x['status']} {want}"
        out.append(e)
    return out


# ================================================================================================ facts
def _fact(fid, kind, value, unit, src_kind, ref, by, date, lines, note):
    return {"fact_id": fid, "version": 1, "quantity_kind": kind, "value": value, "unit": unit,
            "source": {"kind": src_kind, "reference": ref},
            "approval": {"status": "APPROVED", "by": by, "date": date},
            "affected_lines": sorted(lines), "confidence": "CONFIRMED", "note": note}


def declared_facts(usage):
    """the class-B facts of the training villa, each with exactly the lines the register uses it for."""
    rev = "structural set revision UNCONFIRMED (D-61): a DRAWING-CONFIRMED reading of the printed set, not a " \
          "designer approval (Checker F-C-T449-1); the reading is Checker-merged"
    facts = [
        _fact(R.F_UNIT_MASS, "CATEGORY", "D2_OVER_162", "none", "OWNER_DECISION",
              "Urban rule URBAN-REBAR-NET-AND-PROCUREMENT@v1 (kg = count x length x kg/m); OWNER_RULE_REBAR_2026-10-24 "
              "s.2 (kg = total x d^2 / 162); the method of the merged ledgers T-148 / T-138 / T-149 / T-152 / T-166 "
              "and of the V3.0.24 inputs", "PROJECT_OWNER", "2026-10-24", usage[R.F_UNIT_MASS],
              "kg/m = d^2 / 162, d in mm"),
        _fact(R.F_BOQ_UNIT, "CATEGORY", "t", "none", "OWNER_DECISION",
              "OWNER_RULE_REBAR_2026-10-24 s.1: every reinforcement quantity of the final BOQ in metric tons; kg "
              "internal, converted once at the BOQ boundary", "PROJECT_OWNER", "2026-10-24", usage[R.F_BOQ_UNIT],
              "applies to every reinforcement line; lines listed = the lines this register reproduces"),
        _fact(R.F_END_COVER, "LENGTH", 40, "mm", "DRAWING",
              "ST p.15 TYP. SLAB ON BEAMS DETAIL '40 CL.' at the non-continuous support (T-307 R307-3, T-316 R316-3; "
              "Checker-merged c48f7062 / ebe99ecf)", "DESIGNER", "2026-10-26", usage[R.F_END_COVER], rev),
        _fact(R.F_TOP_CONT, "RATIO", 0.30, "ratio", "DRAWING",
              "ST p.15 '.30 L1 OR .30 L2 WHICHEVER LARGER' from the support face (T-316 R316-2; Checker-merged "
              "ebe99ecf)", "DESIGNER", "2026-10-28", usage[R.F_TOP_CONT], rev),
        _fact(R.F_TOP_END, "RATIO", 0.25, "ratio", "DRAWING",
              "ST p.15 '.25 L1' at a non-continuous support (T-316 R316-3; Checker-merged ebe99ecf)", "DESIGNER",
              "2026-10-28", usage[R.F_TOP_END], rev),
        _fact(R.F_TOP_DIA, "LENGTH", 10, "mm", "DRAWING",
              "ST p.4 / p.5 / p.6 plan note 2: top bars 5 o 10 per metre over the beams (T-152 / T-316 NOTE2_D; "
              "Checker-merged ebe99ecf)", "DESIGNER", "2026-10-28", usage[R.F_TOP_DIA], rev),
    ]
    return {"schema": "URBAN_PROJECT_CONFIG_V1", "project_id": "DEVELOPMENT-VILLA-T131", "config_version": "1.0.0",
            "note": "T-449 round 2 (reinforcement): declared facts of the training villa's reinforcement lines; "
                    "lap splices and Q-71 link counting are not declared (they move no line of this villa).",
            "facts": facts}


def fact_usage(entries):
    use = defaultdict(set)
    for e in entries:
        if e["class"] != "A-REPRODUCED" or not e.get("line_id"):
            continue
        rr = e.get("rule_result") or {}
        live = rr.get("state") in (R.VALUED, R.BOUND, R.BOUND_PART_WITH_HELD)
        if live or (rr.get("state") == R.HELD and rr.get("low") is not None):
            for f in rr.get("facts_used", []):
                use[f].add(e["line_id"])
            use[R.F_BOQ_UNIT].add(e["line_id"])
    return {k: sorted(v) for k, v in use.items()}


# ================================================================================================ build
def _boot_cfg():
    """the facts as the register first needs them (no line lists yet): used only to compute the usage."""
    lines = ["L-BOOT"]
    d = declared_facts(defaultdict(lambda: lines))
    return parse_project_config(d)


def populations(entries):
    """released kg per bar population (piece, floor, component class), in t, rule vs ledger."""
    pop = defaultdict(lambda: [0.0, 0.0, 0])
    for e in entries:
        if e["version"] == "ARCH_TAKEOFF_V3.0.3" and e["action"] == "RELEASED":
            comp = re.sub(r"\s+\(.*$|\s+net$", "", e["component"].strip()).upper()
            k = f"{e['piece']} | {e['floor']} | {comp} | d{e['dia_mm']:g}"
            p = pop[k]
            p[0] += e["rule_result"]["value"] or 0.0
            p[1] += e["patch"]["kg"]
            p[2] += 1
    out = {}
    for k, (rule, led, n) in sorted(pop.items()):
        diff = (rule - led) / led if led else (0.0 if rule == 0 else math.inf)
        out[k] = {"lines": n, "rule_t": round(rule / 1000.0, 6), "ledger_t": round(led / 1000.0, 6),
                  "diff_pct": round(diff * 100.0, 4), "within_0_5_pct": abs(diff) <= POP_TOL}
    return out


PENDING = (   # (test on the entry, rule named, why its generic code is not in REBAR_BASIS_RULES_V1)
    (lambda e: "candidate marks" in (e.get("range_basis") or ""), "R-REBAR-CANDIDATE-MARKS-1",
     "a span held over several schedule marks (T-149): min .. max over each candidate mark's populations; the "
     "candidates' own populations are not on the record (the input carries the summed range only)"),
    (lambda e: e.get("piece") == "GROUND_SYSTEM_STEEL" and "LAPS" in (e.get("component") or ""),
     "R-REBAR-LAP-COUNT (T-459)",
     "procurement laps of a continuous ground-beam run over the 12 m stock (runs 13.77 m and 18.57 m: 1 lap each by "
     "the frozen ceil(L / 12) - 1 and by the owner formula ceil((L - 12) / (12 - lap)) alike), held 40 d .. 70 d; "
     "lap counting is T-459's rule, not this version's"),
    (lambda e: e.get("piece") == "GROUND_SYSTEM_STEEL" and str(e.get("element_id", "")).split(":")[2].startswith(
        "SB"), "R-REBAR-DEV-RANGE-1 x Q-74 / D-38",
     "strap bar ends over the owner Q-74 strap-length readings and the SB2 schedule-row conflict (designer D-38): "
     "the strap's bar groups per reading are not on the record"),
    (lambda e: "Ln range" in (e.get("component") or ""), "R-BEAM-TOP-LN-RANGE-1",
     "a beam top bar printed as a fraction of the clear span Ln with Ln itself a range (T-149): the span readings are "
     "not on the record"),
    (lambda e: e.get("label_status") == "HELD_LABEL", "R-SLAB-BAR-END-1 + R-LABEL-MEANING (T-306 F-04)",
     "a bare slab label ('5 o 10' with no '/m') read as 'n bars in all' widens the bound: a label-meaning reading the "
     "rule version does not implement"),
)


def _pending(e):
    for test, rule, why in PENDING:
        if test(e):
            return {"rule": rule, "why": why}
    return {"rule": e.get("rule"), "why": "not classified: " + (e.get("not_reproduced") or "")}


def docs_dir(docs, line_id):
    """the bar direction of a V3.0.27 line, as the V3.0.5 record's part ('x' / 'y')."""
    for x in docs["ARCH_TAKEOFF_V3.0.27"]["lines"]:
        if x["line_id"] == line_id:
            return x["direction"]
    raise KeyError(line_id)


def build(cfg=None):
    for p, h in PINS.items():
        if _sha(p) != h:
            raise SystemExit(f"{p.relative_to(ROOT)} differs from the merged file")
    cens, docs = census()
    t334_rows = _rows(T334)
    t334 = {r["element_id"]: r for r in t334_rows if r["item_code"] == "STR.REBAR"}
    t334_by_line = {r["line_id"]: r for r in t334_rows}
    cfg = cfg or (load_project_config(FACTS) if FACTS.exists() else _boot_cfg())
    entries = []
    entries += footing_entries(docs["ARCH_TAKEOFF_V3.0.2"])
    entries += guard_entries(docs)
    slab = slab_entries(cfg, docs["ARCH_TAKEOFF_V3.0.27"])
    succ = {("SLAB_STEEL", e["element_id"], e["population"].split(" ")[0].upper(),
             docs_dir(docs, e["line_id"])): e for e in slab}
    entries += ledger_entries(cfg, "ARCH_TAKEOFF_V3.0.3", docs["ARCH_TAKEOFF_V3.0.3"], t334)
    entries += ledger_entries(cfg, "ARCH_TAKEOFF_V3.0.5", docs["ARCH_TAKEOFF_V3.0.5"], t334, succ)
    by_line = {e["line_id"]: e for e in entries if e.get("line_id") and e["class"] != "SUPERSEDED"}
    entries += formula_entries(docs["ARCH_TAKEOFF_V3.0.24"], t334_by_line, by_line)
    entries += slab
    n_sup = sum(e["class"] == "SUPERSEDED" for e in entries)
    if n_sup != len(slab):
        raise ValueError(f"{n_sup} V3.0.5 slab records superseded vs {len(slab)} V3.0.27 lines (mapping incomplete)")
    for e in entries:
        if e["class"] == "A-SPECIFIED":
            e["rule_pending"] = _pending(e)
    counts, by_ver = defaultdict(int), defaultdict(lambda: defaultdict(int))
    for e in entries:
        counts[e["class"]] += 1
        by_ver[e["version"]][e["class"]] += 1
    rel = [e for e in entries if e["version"] == "ARCH_TAKEOFF_V3.0.3" and e["action"] == "RELEASED"]
    pops = populations(entries)
    return {
        "schema": "T449_CORRECTION_REGISTER_V1", "round": "2 REINFORCEMENT",
        "candidate_of_record": "ARCH_TAKEOFF_V3.0.42 (inputs as research/agents_t442/v3042_run.py)",
        "project_config": {"file": str(FACTS.relative_to(ROOT)), "project_id": cfg.project_id,
                           "config_version": cfg.config_version, "content_sha256": cfg.content_sha256},
        "rules_module": {"file": "engine/source/rebar_basis_rules_v1.py", "version": R.RULE_VERSION},
        "census": cens,
        "counts": dict(sorted(counts.items())),
        "by_version": {k: dict(sorted(v.items())) for k, v in sorted(by_ver.items())},
        "released": {"lines": len(rel), "ledger_kg": round(math.fsum(e["patch"]["kg"] for e in rel), 6),
                     "line_net_kg": round(math.fsum(e["patch"]["line_net"] or 0.0 for e in rel), 6),
                     "rule_kg": round(math.fsum(e["rule_result"]["value"] or 0.0 for e in rel), 6),
                     "rule_t": R.to_tonnes(cfg, [e["rule_result"]["value"] for e in rel
                                                 if e["rule_result"]["value"] is not None]).value,
                     "populations": len(pops),
                     "populations_within_0_5_pct": sum(p["within_0_5_pct"] for p in pops.values())},
        "populations": pops,
        "fact_usage": fact_usage(entries),
        "not_declared": {
            "REBAR.LAP.*": "owner 40 d / 60 d convention (OWNER_RULE_REBAR_2026-10-24 s.2 / s.4, owner directive C4): "
                           "moves no line of this villa (no bar run over the 12 m stock; T-273 assessment 0.000 kg); "
                           "the lap-count formula is T-459's",
            "REBAR.LINK.FIRST_OFFSET": "Q-71 (owner 2026-10-25: drawing-based counting, 7.5 cm first-link offset "
                                       "where the governing detail applies): the villa's link lines stay HELD over "
                                       "their readings A / B / C; no candidate line counts links by it yet",
            "footing_rebar.*": "V3.0.2 facts: class B, declared at the wiring row with their footing line ids"},
        "out_of_scope": {
            "ARCH_TAKEOFF_V3.0.4": "its inputs are the T-167 profile-audit run files "
                                   "(URBAN_V304_PROFILE_AUDIT_FILES_V1); arch_v304 makes no STR.REBAR line",
            "route G profile / conventions": "the released-route drawing profile (research/urban_engine_m4_correctness/"
                                             "profile_st7757_m4.json) and the generic conventions file are inputs of "
                                             "the released route G, not V3.0.x correction inputs; route G's "
                                             "provisional steel of the ledger scopes is superseded on the candidate "
                                             "(V3.0.3 / V3.0.5)"},
        "entries": entries,
    }


CSV_COLS = ("version", "line_id", "element_id", "action", "class", "rule", "patch", "rule_state", "rule_value",
            "rule_low", "rule_high", "rule_minus_patch_kg", "facts_used", "not_reproduced")


def to_csv(reg):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_COLS)
    for e in reg["entries"]:
        rr = e.get("rule_result") or {}
        w.writerow([e["version"], e.get("line_id") or "", e.get("element_id") or "", e["action"], e["class"],
                    e.get("rule") or "", json.dumps(e["patch"], ensure_ascii=False, sort_keys=True),
                    rr.get("state", ""), rr.get("value", ""), rr.get("low", ""), rr.get("high", ""),
                    e.get("rule_minus_patch_kg", ""), ";".join(rr.get("facts_used", [])),
                    e.get("not_reproduced", "")])
    return buf.getvalue()


def write_facts(path):
    """the facts file from the register's own usage (two passes: usage first with a boot config)."""
    reg = build(cfg=_boot_cfg())
    usage = defaultdict(list, reg["fact_usage"])
    data = declared_facts(usage)
    parse_project_config(data)
    Path(path).write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--facts-out" in args:
        i = args.index("--facts-out")
        write_facts(args[i + 1])
        del args[i:i + 2]
    reg = build()
    if args:
        out = Path(args[0])
        out.mkdir(parents=True, exist_ok=True)
        (out / "CORRECTION_REGISTER_REBAR_T449.json").write_text(
            json.dumps(reg, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        (out / "CORRECTION_REGISTER_REBAR_T449.csv").write_text(to_csv(reg), encoding="utf-8")
    print(json.dumps({k: reg[k] for k in ("counts", "by_version", "released")}, indent=1))
