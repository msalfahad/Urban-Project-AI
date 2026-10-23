"""ALSENAN KEY MAP (task T-001b) - turns one engine run (canonical BOQ_LINES.json + BOQ_RELEASE_REPORT.json) and the
freelancer's normalised rows into the scorer's rows through an explicit key map, then scores them with
tools/alsenan_scoreboard.py. Reads only; writes only the files named by --out / --markdown.

Release class of a canonical line (the rule the engine's own release report applies, UP-QTY-STATUS-001,
tools/urban_boq_m9.py `_release_report`):
- evidence_state in QUANTITY_STATES (MEASURED / SOURCE_DERIVED / PROVISIONAL) with a measured_net -> RELEASED, qty;
- NOT_APPLICABLE_WITH_EVIDENCE / EXCLUDED_WITH_REASON -> not an answer (the engine states the item has no scope in
  that place); counted per key in "excluded", never turned into a quantity;
- anything else (BLOCKED_RFI, BOUNDED_EXPOSURE, a quantity state without measured_net, an unknown state) -> HELD with
  qty None: a range or a missing number never becomes a released quantity, and missing never becomes 0.
- every CONDITIONAL scenario set of the release report that carries a keyed item answers that key once as HELD
  (qty None): the quantity of a space under review sits in no line, so comparing the lines alone would understate.

Key map (URBAN_ALSENAN_KEY_MAP_V1, tests/alsenan/T001B_KEY_MAP.json): keys -> {trade, reference_id, item_codes,
conditional_items?, reference_unit?}. An item code in two keys, a key without its reference row, or a reference id
used twice is an error. Lines whose item code no key names stay UNMAPPED (listed, never false positives).

CLI: python3 -I tools/alsenan_keymap.py --run RUN_DIR --reference BENCHMARK_NORMALISED.json --key-map KEY_MAP.json
     --out OUT.json [--markdown OUT.md] [--set-bindings SET_BINDINGS.json (T-216 opt-in, see below)]
T-181 (opt-in, doors and windows in pcs AND m2, URBAN_ALSENAN_OPENINGS_KEY_MAP_V1):
     python3 -I tools/alsenan_keymap.py --openings-register OPENINGS.csv --openings-raw FREELANCER_RAW_ROWS.json
     --openings-key-map T181_OPENINGS_KEY_MAP.json --openings-out OUT.json [--openings-markdown OUT.md]
     [--openings-engine-run RUN_DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import alsenan_scoreboard as S  # noqa: E402

QUANTITY_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")   # engine/source/boq_line.py QUANTITY_STATES
EXCLUDED_STATES = ("NOT_APPLICABLE_WITH_EVIDENCE", "EXCLUDED_WITH_REASON")


def load_key_map(doc):
    """Validated key map: {item_code: key entry}, {key: entry}."""
    by_item, by_key, refs = {}, {}, set()
    for k in doc["keys"]:
        key = k["key"]
        if key in by_key:
            raise ValueError(f"key {key!r} repeated")
        if k["reference_id"] in refs:
            raise ValueError(f"reference {k['reference_id']!r} used by two keys")
        refs.add(k["reference_id"])
        by_key[key] = k
        for code in k["item_codes"]:
            if code in by_item:
                raise ValueError(f"item code {code!r} answers two keys")
            by_item[code] = k
    return by_item, by_key


def line_status(ln):
    """(status for the scorer, qty) of one canonical line, or None when the line is an exclusion."""
    ev = ln.get("evidence_state")
    if ev in EXCLUDED_STATES:
        return None
    if ev in QUANTITY_STATES and ln.get("measured_net") is not None:
        return "RELEASED", float(ln["measured_net"])
    return "HELD", None


def engine_rows(lines, release_report, key_map_doc):
    """Scorer engine rows + an adapter report (excluded / unmapped counts per item code)."""
    by_item, by_key = load_key_map(key_map_doc)
    sb = load_set_bindings(key_map_doc.get("set_bindings"))     # T-216 opt-in; None keeps every output unchanged
    rows, excluded, unmapped = [], {}, {}
    for ln in lines:
        code = ln["item_code"]
        k = by_item.get(code)
        st = line_status(ln)
        if st is None:
            if k is not None:
                excluded[k["key"]] = excluded.get(k["key"], 0) + 1
            continue
        status, qty = st
        loc = ln.get("location") or {}
        rows.append({"id": ln["line_id"], "trade": k["trade"] if k else ln.get("trade"), "unit": ln["unit"],
                     "qty": qty, "status": status, "key": k["key"] if k else None,
                     "surface": loc.get("element_id")})
        if k is None:
            unmapped[(code, ln["unit"])] = unmapped.get((code, ln["unit"]), 0) + 1
    conditional = {}
    for key, k in by_key.items():
        items = set(k.get("conditional_items") or ())
        if not items:
            continue
        for s in (release_report or {}).get("categories", {}).get("CONDITIONAL", {}).get("scenario_sets", []):
            hit = any(items & set(v) for v in (s.get("by_scenario") or {}).values())
            if hit:
                unit = S.norm_unit(sorted(items)[0].rsplit("[", 1)[1].rstrip("]"))
                row = {"id": f"COND:{s['set_id']}:{key}", "trade": k["trade"], "unit": unit, "qty": None,
                       "status": "HELD", "key": key, "surface": f"COND:{s['set_id']}"}
                if sb is not None:
                    row = bound_set_row(row, s, key, items, sb)
                rows.append(row)
                conditional[key] = conditional.get(key, 0) + 1
    report = {"excluded_lines_by_key": excluded, "conditional_sets_by_key": conditional,
              "unmapped_by_item": [{"item_code": c, "unit": u, "lines": n} for (c, u), n in sorted(unmapped.items())]}
    if sb is not None:
        report["set_bindings"] = set_binding_report(rows, sb)
    return rows, report


def reference_rows(normalised_doc, key_map_doc):
    """One scorer reference row per key from the normalised freelancer records (any row kind the map names)."""
    _, by_key = load_key_map(key_map_doc)
    recs = {r["id"]: r for r in normalised_doc["records"]}
    kinds = set(key_map_doc.get("reference_row_kinds") or ())
    rows = []
    for key, k in by_key.items():
        rec = recs.get(k["reference_id"])
        if rec is None:
            raise ValueError(f"key {key!r}: reference {k['reference_id']!r} not found")
        if kinds and rec.get("row_kind") not in kinds:
            raise ValueError(f"key {key!r}: reference {k['reference_id']!r} is a {rec.get('row_kind')} row")
        unit = rec.get("unit")
        if not str(unit or "").strip() and k.get("reference_unit"):
            if not str(k.get("reference_unit_source") or "").strip():
                raise ValueError(f"key {key!r}: a reference unit needs its source")
            unit = k["reference_unit"]
        rows.append({"id": rec["id"], "trade": k["trade"], "unit": unit, "qty": rec.get("qty"), "key": key})
    return rows


def run(run_dir, normalised_doc, key_map_doc):
    run_dir = Path(run_dir)
    lines = json.loads((run_dir / "BOQ_LINES.json").read_text(encoding="utf-8"))
    rel_path = run_dir / "BOQ_RELEASE_REPORT.json"
    rel = json.loads(rel_path.read_text(encoding="utf-8")) if rel_path.exists() else None
    eng, report = engine_rows(lines, rel, key_map_doc)
    ref = reference_rows(normalised_doc, key_map_doc)
    result = S.score(eng, ref)
    result["adapter"] = dict(report, release_report_present=rel is not None, boq_lines=len(lines))
    return result


# ---- T-216: review-set bindings as an opt-in key-map path (URBAN_SCORER_SET_BINDINGS_V1) ----
#
# Opt-in only: `--set-bindings FILE` puts the file into the key map document in memory under "set_bindings"; without
# it nothing above changes and every v1 / v2 / v2.1 output stays byte-identical. A binding file settles CONDITIONAL
# review sets of a run (REVIEW_SET_BINDING_V1, research/agents_t208/review_sets.py) for the keys it names, each through
# an ANSWERED owner rule and a checker verdict commit. Rules (each is a test in tests/t216_set_bindings):
# - a bound set answers its key with the bound scenario's key items, status ASSUMED — OWNER-APPROVED
#   (WORKFLOW_CONTROLS s.4), reported apart from the released lines in adapter["set_bindings"]; the scorer sees a
#   quantity (class RELEASED, status COMPUTED) so the line can be compared, never a DRAWING-CONFIRMED or VERIFIED one;
# - a set the file does not bind, or binds HELD, keeps its HELD row: the line stays HELD (never a partial sum, never 0);
# - refused: a wrong schema, an unknown or unanswered rule, a bound set without a verdict commit and source or without
#   its evidence (fixture symbol and printed size), a set of another kind than REVIEW_CLASSIFICATION, a bound
#   scenario that still carries a closure-strip item of a space with a door closure (one physical strip, one line: the
#   opening's threshold line holds it), and a binding whose quantities are not this run's scenario (stale binding);
# - a bound scenario that holds none of the key's items keeps the set HELD for that key (missing is never 0).

SET_BINDINGS_SCHEMA = "URBAN_SCORER_SET_BINDINGS_V1"
SB_ASSUMED, SB_HELD = "ASSUMED_OWNER_APPROVED", "HELD"
SB_KIND = "REVIEW_CLASSIFICATION"
SB_SCORER_STATUS = "COMPUTED"         # scorer class RELEASED = "answers with a quantity"; the evidence is kept apart
_SB_QTY_TOL = 1e-6


def _hexsha(v):
    s = str(v or "").strip().lower()
    return 7 <= len(s) <= 40 and all(c in "0123456789abcdef" for c in s)


def load_set_bindings(doc):
    """Validated binding file ({set_id: record} + keys, rules, strip items), or None when no file is given."""
    if doc is None:
        return None
    if doc.get("SCHEMA") != SET_BINDINGS_SCHEMA:
        raise ValueError(f"set binding schema {doc.get('SCHEMA')!r} is not {SET_BINDINGS_SCHEMA}")
    keys = list(doc.get("keys") or ())
    if not keys:
        raise ValueError("a set binding file names the keys it settles")
    rules = dict(doc.get("approved_rules") or {})
    for rid, src in rules.items():
        if not str(src or "").strip():
            raise ValueError(f"approved rule {rid!r} has no answered-owner source")
    strips = tuple(doc.get("closure_strip_items") or ())
    sets = {}
    for b in doc.get("sets") or ():
        sid = b.get("set_id")
        where = f"binding {sid!r}"
        if not sid or sid in sets:
            raise ValueError(f"{where}: set id missing or repeated")
        if b.get("kind") != SB_KIND:
            raise ValueError(f"{where}: a {b.get('kind')!r} set is not a wet / dry review set; only {SB_KIND} binds")
        st = b.get("status")
        if st == SB_HELD:
            if not str(b.get("reason") or "").strip():
                raise ValueError(f"{where}: a HELD binding needs its reason")
        elif st == SB_ASSUMED:
            if b.get("rule_id") not in rules:
                raise ValueError(f"{where}: rule {b.get('rule_id')!r} is not an approved answered owner rule")
            if not str(b.get("scenario") or "").strip():
                raise ValueError(f"{where}: no scenario")
            ev = b.get("evidence") or {}
            for f in ("fixture_symbol", "printed_size"):
                if not str(ev.get(f) or "").strip():
                    raise ValueError(f"{where}: evidence {f} missing")
            v = b.get("verdict") or {}
            if not _hexsha(v.get("commit")) or not str(v.get("source") or "").strip():
                raise ValueError(f"{where}: a binding without a checker verdict commit and its source is refused")
            q = b.get("quantities")
            if not isinstance(q, dict) or not q:
                raise ValueError(f"{where}: no bound quantities")
            for item, x in q.items():
                S._qty(x, f"{where} {item}")
            if int(b.get("door_closures") or 0) > 0 and any(i in q for i in strips):
                raise ValueError(f"{where}: the bound scenario still carries a closure strip of a space with a door "
                                 "closure; the opening's threshold line holds it (one strip, one line)")
            cs = b.get("closure_strip")
            if cs is not None and (cs.get("item") not in strips or cs.get("m2") is None):
                raise ValueError(f"{where}: closure strip {cs!r} is not a declared strip item with its m2")
        else:
            raise ValueError(f"{where}: status {st!r} is not {SB_ASSUMED} or {SB_HELD}")
        sets[sid] = b
    return {"doc": doc, "keys": keys, "sets": sets, "strips": strips, "used": set()}


def bound_set_row(row, scenario_set, key, key_items, sb):
    """The scorer row of one CONDITIONAL set holding `key` under a binding file (the HELD row when not bound)."""
    sid = scenario_set.get("set_id")
    if key not in sb["keys"]:
        return row
    b = sb["sets"].get(sid)
    if b is None:
        return dict(row, binding="UNBOUND", binding_reason="no binding for this set: HELD, never dry by default")
    sb["used"].add(sid)
    if scenario_set.get("kind") != SB_KIND:
        raise ValueError(f"binding {sid!r}: the run's set is a {scenario_set.get('kind')!r} set, not {SB_KIND}")
    if b["status"] == SB_HELD:
        return dict(row, binding=SB_HELD, binding_reason=b["reason"])
    run_q = (scenario_set.get("by_scenario") or {}).get(b["scenario"])
    if run_q is None:
        raise ValueError(f"binding {sid!r}: the run's set has no {b['scenario']} scenario")
    want = dict(run_q)
    cs = b.get("closure_strip")
    if cs is not None:
        if abs(float(want.pop(cs["item"], float("nan"))) - float(cs["m2"])) > _SB_QTY_TOL:
            raise ValueError(f"binding {sid!r}: closure strip {cs['m2']} is not this run's {cs['item']}")
    q = b["quantities"]
    if set(q) != set(want) or any(abs(float(q[i]) - float(want[i])) > _SB_QTY_TOL for i in q):
        raise ValueError(f"binding {sid!r}: bound quantities are not this run's {b['scenario']} scenario "
                         "(a stale or foreign binding)")
    present = sorted(i for i in key_items if i in q)
    if not present:
        return dict(row, binding=SB_HELD, binding_reason=f"the bound {b['scenario']} scenario holds none of the key's "
                                                         "items: HELD, never 0")
    qty = round(sum(float(q[i]) for i in present), 6)
    return dict(row, qty=qty, status=SB_SCORER_STATUS, evidence="ASSUMED — OWNER-APPROVED", binding=SB_ASSUMED,
                rule_id=b["rule_id"], verdict_commit=b["verdict"]["commit"], scenario=b["scenario"],
                closure_strip_m2=None if cs is None else float(cs["m2"]),
                geometry_status=b.get("geometry_status"))


def set_binding_report(rows, sb):
    """Per bound key: released lines, ASSUMED — OWNER-APPROVED sets, held sets / lines, the line total (None while
    anything holding the key is held), and bindings this run never used."""
    out = {"schema": SET_BINDINGS_SCHEMA, "task": sb["doc"].get("task"), "keys": {}}
    for key in sb["keys"]:
        mine = [r for r in rows if r.get("key") == key]
        rel = [r for r in mine if not str(r["id"]).startswith("COND:") and r["status"] == "RELEASED"
               and r["qty"] is not None]
        held_lines = [r["id"] for r in mine if not str(r["id"]).startswith("COND:") and r not in rel]
        bound = [r for r in mine if r.get("binding") == SB_ASSUMED]
        held_sets = [{"set": r["surface"], "reason": r.get("binding_reason") or "HELD"}
                     for r in mine if str(r["id"]).startswith("COND:") and r.get("binding") != SB_ASSUMED]
        r_q = round(sum(r["qty"] for r in rel), 6)
        a_q = round(sum(r["qty"] for r in bound), 6)
        out["keys"][key] = {
            "released_lines": len(rel), "released_m2": r_q, "held_lines": held_lines,
            "assumed_owner_approved_m2": a_q,
            "bound_sets": [{"set": r["surface"], "qty": r["qty"], "rule_id": r["rule_id"],
                            "verdict_commit": r["verdict_commit"], "scenario": r["scenario"],
                            "geometry_status": r.get("geometry_status"),
                            "closure_strip_not_in_key_m2": r.get("closure_strip_m2")} for r in bound],
            "held_sets": held_sets,
            "line_total": None if (held_lines or held_sets) else round(r_q + a_q, 6)}
    out["unused_bindings"] = sorted(set(sb["sets"]) - sb["used"])
    return out


def set_bindings_markdown(sides):
    """The binding column table: [(side label, adapter dict)] -> markdown (released and assumed never merged)."""
    out = ["", "### Review-set bindings (opt-in; ASSUMED — OWNER-APPROVED kept apart from released lines)", "",
           "| Side | Key | Released lines | Binding: ASSUMED — OWNER-APPROVED | Bound sets (rule, verdict commit) | "
           "Held sets / lines | Line total |", "|---|---|---|---|---|---|---|"]
    for label, ad in sides:
        rep = (ad or {}).get("set_bindings")
        if rep is None:
            continue
        for key, k in rep["keys"].items():
            bs = ", ".join(f"{b['set']} {b['qty']:.4f} ({b['rule_id']}, {b['verdict_commit']})"
                           for b in k["bound_sets"]) or "-"
            hs = [f"{h['set']} ({h['reason']})" for h in k["held_sets"]]
            if k["held_lines"]:
                hs.append(f"{len(k['held_lines'])} held engine line{'s' if len(k['held_lines']) != 1 else ''}")
            tot = "HELD (not a partial sum)" if k["line_total"] is None else f"{k['line_total']:.4f}"
            out.append(f"| {label} | {key} | {k['released_m2']:.4f} on {k['released_lines']} | "
                       f"{k['assumed_owner_approved_m2']:.4f} on {len(k['bound_sets'])} | {bs} | "
                       f"{'; '.join(hs) or '-'} | {tot} |")
        if rep["unused_bindings"]:
            out.append(f"| {label} | unused bindings | {', '.join(rep['unused_bindings'])} | | | | |")
    return "\n".join(out) + "\n"


def with_set_bindings(key_map_doc, bindings_doc):
    """The key map document carrying the binding file in memory (the --set-bindings opt-in)."""
    load_set_bindings(bindings_doc)
    return dict(key_map_doc, set_bindings=bindings_doc)


# ---- T-181: doors and windows like for like, pcs AND m2 (URBAN_ALSENAN_OPENINGS_KEY_MAP_V1) ----
#
# Opt-in path; nothing above changes. Input 1: an opening register, one row per physical opening (the T-150 r2 layout,
# research/agents_t150/OPENINGS_T150.csv: ID, KIND, BOQ_LINE, CLASS_STATUS, WIDTH_M, WIDTH_LO_M, HEIGHT_M,
# HEIGHT_STATUS, HEIGHT_SOURCE, FREELANCER_KEY, VERDICT, HOLD_CAUSE). Input 2: the freelancer's raw workbook rows
# (FREELANCER_RAW_ROWS.json). Input 3: the openings key map, which names per opening class the register BOQ lines,
# the engine item codes (pcs side of an engine run) and the reference rows, and maps the register's scope labels to
# his rows. Rules (each is a test in tests/t181_openings_like_for_like):
# - pcs and m2 are separate keys (CLASS[nr], CLASS[m2]); a unit is never converted into the other.
# - a reference row's count / width / height / area come from its own cells; area must equal count x width x height
#   (his formula) and the class's rows must re-add to the cover total, else refused.
# - per opening: pcs 1 when the class is settled and no hold cause questions the opening; m2 = width x height only
#   when the height is PRINTED (DRAWING-CONFIRMED) or ASSUMED with an owner-approved source (ASSUMED — OWNER-APPROVED,
#   WORKFLOW_CONTROLS s.4); a held height, a width range, a missing width or a hold cause -> HELD (candidate kept),
#   never 0. A class-held opening answers every class the key map lists as its candidates once as HELD.
# - a class with no reference row is NOT COMPARABLE (a reference-set gap): listed, never a false positive.
# - each of his rows is tied to the openings it covers (scope table); a register label the map does not know is an
#   error; a label ending in "?" is an uncertain tie, listed and never counted.

OPENINGS_SCHEMA = "URBAN_ALSENAN_OPENINGS_KEY_MAP_V1"
OPENINGS_RESULT_SCHEMA = "URBAN_ALSENAN_OPENINGS_LIKE_FOR_LIKE_V1"
EV_CONFIRMED, EV_ASSUMED, EV_HELD, EV_UNKNOWN = ("DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN")
_AREA_TOL = 1e-6


def _num(v, where):
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise ValueError(f"{where}: {v!r} is not a number") from None
    if not x == x or x in (float("inf"), float("-inf")) or x < 0:
        raise ValueError(f"{where}: {v!r} is not a finite non-negative number")
    return x


def load_openings_key_map(doc):
    """Validated openings key map: classes by name, register BOQ line -> class, scope label -> reference id."""
    if doc.get("SCHEMA") != OPENINGS_SCHEMA:
        raise ValueError(f"openings key map schema {doc.get('SCHEMA')!r} is not {OPENINGS_SCHEMA}")
    classes, by_line, by_code, used_refs = {}, {}, {}, set()
    for c in doc["classes"]:
        name = c["class"]
        if name in classes:
            raise ValueError(f"class {name!r} repeated")
        classes[name] = c
        for ln in c["register_boq_lines"]:
            if ln in by_line:
                raise ValueError(f"register line {ln!r} answers two classes")
            by_line[ln] = name
        for code in c.get("engine_item_codes") or ():
            if code in by_code:
                raise ValueError(f"engine item code {code!r} answers two classes")
            by_code[code] = name
        for rid in c.get("reference_rows") or ():
            if rid in used_refs:
                raise ValueError(f"reference row {rid!r} used by two classes")
            used_refs.add(rid)
        if not c.get("reference_rows") and not str(c.get("not_comparable_reason") or "").strip():
            raise ValueError(f"class {name!r} has no reference row and no not-comparable reason")
    labels = dict(doc.get("scope_labels") or {})
    for lab, rid in labels.items():
        if rid not in used_refs:
            raise ValueError(f"scope label {lab!r} -> {rid!r}: not a reference row of any class")
    held = {}
    for oid, h in (doc.get("held_class_candidates") or {}).items():
        bad = [x for x in h["classes"] if x not in classes]
        if bad or not str(h.get("source") or "").strip():
            raise ValueError(f"held-class candidates of {oid!r}: unknown class {bad} or no source")
        held[oid] = h
    return {"classes": classes, "by_line": by_line, "by_code": by_code, "labels": labels, "held": held,
            "approved_assumption_sources": tuple(doc.get("approved_assumption_sources") or ())}


def _raw_index(raw_doc):
    out = {}
    for r in raw_doc["rows"]:
        out[f"{r['file']}:{r['sheet']}:{r['row']}"] = r
    return out


def reference_opening_rows(raw_doc, km):
    """Per reference row: count, width, height, area from its own cells (key map 'cells'); checks area = count x
    width x height and the class sums against the cover totals. Returns {ref_id: row} and per-class sums."""
    cells = km["doc"]["reference_cells"]
    idx = _raw_index(raw_doc)
    rows, per_class = {}, {}
    for name, c in km["classes"].items():
        pcs = m2 = 0.0
        for rid in c.get("reference_rows") or ():
            raw = idx.get(rid)
            if raw is None:
                raise ValueError(f"reference row {rid!r} not in the raw rows")
            n = raw["row"]
            got = {}
            for field in ("count", "width", "height", "area"):
                cell = raw["cells"].get(f"{cells[field]}{n}")
                got[field] = _num(None if cell is None else cell.get("v"), f"{rid} {field}")
                if got[field] is None:
                    raise ValueError(f"{rid}: {field} cell {cells[field]}{n} is empty")
            if abs(got["count"] * got["width"] * got["height"] - got["area"]) > _AREA_TOL:
                raise ValueError(f"{rid}: area {got['area']} != count x width x height")
            rows[rid] = dict(got, ref_id=rid, cls=name, label=None)
            pcs += got["count"]
            m2 += got["area"]
        cover = c.get("cover_total")
        if cover is not None and abs(cover["m2"] - m2) > _AREA_TOL:
            raise ValueError(f"class {name!r}: rows sum {m2} m2 != cover total {cover['m2']} ({cover['ref_id']})")
        per_class[name] = {"nr": pcs if c.get("reference_rows") else None,
                           "m2": m2 if c.get("reference_rows") else None}
    return rows, per_class


def opening_quantities(reg_row, km):
    """(class or None, pcs (status, qty, evidence), m2 (status, qty, evidence, candidate)) of one register row."""
    oid = reg_row["ID"]
    cls = km["by_line"].get(reg_row["BOQ_LINE"])
    cause = str(reg_row.get("HOLD_CAUSE") or "").strip()
    class_settled = cls is not None and reg_row.get("CLASS_STATUS") == EV_CONFIRMED
    width = _num(reg_row.get("WIDTH_M"), f"{oid} width")
    width_lo = _num(reg_row.get("WIDTH_LO_M"), f"{oid} width low")
    height = _num(reg_row.get("HEIGHT_M"), f"{oid} height")
    hs = str(reg_row.get("HEIGHT_STATUS") or "").strip().upper()
    if hs not in ("PRINTED", "ASSUMED", "HELD"):
        raise ValueError(f"{oid}: height status {hs!r} is not PRINTED / ASSUMED / HELD")
    if hs == "ASSUMED":
        src = str(reg_row.get("HEIGHT_SOURCE") or "")
        if not any(s in src for s in km["approved_assumption_sources"]):
            raise ValueError(f"{oid}: ASSUMED height without an owner-approved source ({src!r})")
    if hs in ("PRINTED", "ASSUMED") and height is None:
        raise ValueError(f"{oid}: height status {hs} without a height")
    why = []
    if cause:
        why.append("hold cause: " + cause[:120])
    if not class_settled:
        why.append("class not settled")
    pcs = ("RELEASED", 1.0, EV_CONFIRMED) if not why else ("HELD", None, EV_HELD)
    cand = None
    if width is not None and width_lo is not None:
        why.append(f"width range {width_lo:.2f} .. {width:.2f}")
        if height is not None:
            cand = (round(width_lo * height, 6), round(width * height, 6))
    if width is None:
        why.append("width not established")
    if hs == "HELD":
        why.append("height HELD")
    if height is not None and width is not None and cand is None:
        cand = (round(width * height, 6),) * 2
    if why:
        m2 = ("HELD", None, EV_HELD, cand, "; ".join(why))
    else:
        m2 = ("RELEASED", round(width * height, 6), EV_CONFIRMED if hs == "PRINTED" else EV_ASSUMED, cand, "")
    return cls, pcs, m2


def openings_like_for_like(register_rows, raw_doc, okm_doc, engine_lines=None):
    """Doors and windows compared like for like (pcs vs pcs, m2 vs m2) per opening class; JSON-ready dict."""
    km = load_openings_key_map(okm_doc)
    km["doc"] = okm_doc
    ref_rows, ref_sums = reference_opening_rows(raw_doc, km)
    label_of = {}
    for lab, rid in km["labels"].items():
        ref_rows[rid]["label"] = lab
        label_of[rid] = lab
    seen, per_open = set(), []
    for r in register_rows:
        oid = r["ID"]
        if oid in seen:
            raise ValueError(f"opening {oid!r} repeated in the register")
        seen.add(oid)
        cls, pcs, m2 = opening_quantities(r, km)
        lab = str(r.get("FREELANCER_KEY") or "").strip()
        uncertain = lab.endswith("?")
        if lab and lab.lower() != "none" and lab.rstrip("?") not in km["labels"]:
            raise ValueError(f"{oid}: freelancer label {lab!r} is not in the key map's scope labels")
        per_open.append({"id": oid, "kind": r.get("KIND"), "floor": r.get("FLOOR"), "register_line": r["BOQ_LINE"],
                         "class": cls, "pcs_status": pcs[0], "pcs": pcs[1], "pcs_evidence": pcs[2],
                         "m2_status": m2[0], "m2": m2[1], "m2_evidence": m2[2], "m2_candidate": m2[3],
                         "held_why": m2[4], "ref_id": None if not lab or lab.lower() == "none" or uncertain
                         else km["labels"][lab], "uncertain_ref_id": km["labels"][lab.rstrip("?")] if uncertain
                         else None, "register_verdict": r.get("VERDICT")})
    eng, ref, not_comparable = [], [], {}
    for name, c in km["classes"].items():
        for unit in ("nr", "m2"):
            key = f"{name}[{unit}]"
            if c.get("reference_rows"):
                ref.append({"id": f"REF:{key}", "trade": c["trade"], "unit": unit, "qty": ref_sums[name][unit],
                            "key": key})
    for o in per_open:
        if o["id"] in km["held"]:
            if o["class"] is not None:
                raise ValueError(f"{o['id']}: held-class candidates given for an opening whose class is settled")
            targets = list(km["held"][o["id"]]["classes"])
        else:
            targets = [o["class"]] if o["class"] else []
        for name in targets:
            c = km["classes"][name]
            held_class = o["class"] != name
            for unit, st, q in (("nr", o["pcs_status"], o["pcs"]), ("m2", o["m2_status"], o["m2"])):
                if held_class:
                    st, q = "HELD", None
                row = {"id": f"{o['id']}:{name}[{unit}]", "trade": c["trade"], "unit": unit, "qty": q,
                       "status": st, "key": f"{name}[{unit}]", "surface": o["id"]}
                if c.get("reference_rows"):
                    eng.append(row)
                else:
                    not_comparable.setdefault(name, []).append(row)
    unclassed = [o["id"] for o in per_open if o["class"] is None and o["id"] not in km["held"]]
    scored = S.score(eng, ref)
    classes = []
    for name, c in km["classes"].items():
        mine = [o for o in per_open if o["class"] == name]
        held_in = [o["id"] for o in per_open if name in km["held"].get(o["id"], {}).get("classes", ())]
        conf = [o for o in mine if o["m2_status"] == "RELEASED" and o["m2_evidence"] == EV_CONFIRMED]
        assu = [o for o in mine if o["m2_status"] == "RELEASED" and o["m2_evidence"] == EV_ASSUMED]
        heldm = [o for o in mine if o["m2_status"] == "HELD"]
        entry = {"class": name, "trade": c["trade"], "comparable": bool(c.get("reference_rows")),
                 "not_comparable_reason": c.get("not_comparable_reason"),
                 "pcs_settled": sum(1 for o in mine if o["pcs_status"] == "RELEASED"),
                 "pcs_held": [o["id"] for o in mine if o["pcs_status"] == "HELD"], "class_held_candidates": held_in,
                 "m2_confirmed": round(sum(o["m2"] for o in conf), 6), "m2_confirmed_n": len(conf),
                 "m2_assumed_owner_approved": round(sum(o["m2"] for o in assu), 6), "m2_assumed_n": len(assu),
                 "m2_held": [o["id"] for o in heldm],
                 "m2_held_candidates_known": [o["m2_candidate"] for o in heldm if o["m2_candidate"]],
                 "reference": ref_sums.get(name), "lines": {}}
        for ln in scored["lines"]:
            if ln["key"].startswith(name + "["):
                entry["lines"][ln["unit"]] = {k: ln[k] for k in ("outcome", "engine_qty", "reference_qty",
                                                                  "signed_error", "abs_error", "engine_ids")}
        # same openings both sides: openings whose m2 this side releases and that one of his rows covers
        same = [o for o in mine if o["m2_status"] == "RELEASED" and o["ref_id"]]
        if same and c.get("reference_rows"):
            e = sum(o["m2"] for o in same)
            f = sum(ref_rows[o["ref_id"]]["width"] * ref_rows[o["ref_id"]]["height"] for o in same)
            entry["same_openings_m2"] = {"openings": [o["id"] for o in same], "engine": round(e, 6),
                                         "freelancer": round(f, 6), "diff": round(e - f, 6),
                                         "pct": None if not f else round(100.0 * (e - f) / f, 3)}
        classes.append(entry)
    scope = []
    for rid, rr in sorted(ref_rows.items(), key=lambda kv: (kv[1]["cls"], kv[0])):
        cov = [o for o in per_open if o["ref_id"] == rid]
        unc = [o["id"] for o in per_open if o["uncertain_ref_id"] == rid]
        n_cov = len(cov)
        e_m2 = None if any(o["m2_status"] != "RELEASED" for o in cov) or not cov else round(sum(o["m2"] for o in cov), 6)
        wrong_class = [o["id"] for o in cov if o["class"] != rr["cls"]]
        scope.append({"ref_id": rid, "label": rr["label"], "class": rr["cls"], "his_count": rr["count"],
                      "his_width": rr["width"], "his_height": rr["height"], "his_m2": rr["area"],
                      "openings": [o["id"] for o in cov], "uncertain_openings": unc,
                      "openings_pcs_settled": sum(1 for o in cov if o["pcs_status"] == "RELEASED"),
                      "engine_m2": e_m2, "class_mismatch": wrong_class,
                      "scope": "DIFFERS" if n_cov != rr["count"] or wrong_class else
                      "AGREES" if all(o["pcs_status"] == "RELEASED" for o in cov) else "COUNT HELD"})
    engine_side = None
    if engine_lines is not None:
        erows = []
        for ln in engine_lines:
            name = km["by_code"].get(ln["item_code"])
            if name is None or not km["classes"][name].get("reference_rows"):
                continue
            st = line_status(ln)
            if st is None:
                continue
            u = S.norm_unit(ln["unit"])
            erows.append({"id": ln["line_id"], "trade": km["classes"][name]["trade"], "unit": u, "qty": st[1],
                          "status": st[0], "key": f"{name}[{u}]", "surface": (ln.get("location") or {}).get("element_id")})
        es = S.score(erows, ref)
        engine_side = {"lines": [{k: ln[k] for k in ("key", "unit", "outcome", "engine_qty", "reference_qty",
                                                      "signed_error")} for ln in es["lines"]],
                       "false_positives": es["false_positives"]}
    return {"SCHEMA": OPENINGS_RESULT_SCHEMA, "key_map": okm_doc.get("SCHEMA"),
            "side": okm_doc.get("register_side_label", "opening register"), "classes": classes,
            "scored": {"buckets": scored["buckets"], "lines": scored["lines"],
                       "false_positives": scored["false_positives"], "duplicates": scored["duplicates"]},
            "not_comparable": {k: [{"id": r["id"], "unit": r["unit"], "qty": r["qty"], "status": r["status"]}
                                   for r in v] for k, v in not_comparable.items()},
            "not_a_supply_class": unclassed, "scope_rows": scope, "openings": per_open,
            "engine_run_pcs": engine_side,
            "rule": "pcs vs pcs and m2 vs m2 only; held never 0; ASSUMED — OWNER-APPROVED kept apart from "
                    "DRAWING-CONFIRMED; no reference row = NOT COMPARABLE, never a false positive"}


def _f(x, nd=3):
    return "HELD" if x is None else f"{x:.{nd}f}"


def openings_markdown(res):
    out = [f"Side: {res['side']}. pcs and m2 never converted; HELD is never 0.", "",
           "| Class | Unit | This side | Evidence split | Held | Freelancer | Outcome | Diff | % |",
           "|---|---|---|---|---|---|---|---|---|"]
    for c in res["classes"]:
        ref = c["reference"] or {}
        for unit in ("nr", "m2"):
            ln = c["lines"].get(unit)
            if unit == "nr":
                this = f"{c['pcs_settled']} settled"
                split = EV_CONFIRMED
                held = ", ".join(c["pcs_held"] + [f"{x} (class)" for x in c["class_held_candidates"]]) or "-"
            else:
                tot = c["m2_confirmed"] + c["m2_assumed_owner_approved"]
                this = f"{tot:.3f} on {c['m2_confirmed_n'] + c['m2_assumed_n']}"
                split = f"confirmed {c['m2_confirmed']:.3f} ({c['m2_confirmed_n']}); assumed {c['m2_assumed_owner_approved']:.3f} ({c['m2_assumed_n']})"
                held = f"{len(c['m2_held'])} openings" + (f" + {len(c['class_held_candidates'])} class held"
                                                         if c["class_held_candidates"] else "")
            if not c["comparable"]:
                out.append(f"| {c['class']} | {unit} | {this} | {split} | {held} | none | NOT COMPARABLE | - | - |")
                continue
            r = ref.get(unit)
            d = ln.get("signed_error") if ln else None
            pct = "-" if d is None or not r else f"{100.0 * d / r:+.2f} %"
            out.append(f"| {c['class']} | {unit} | {this} | {split} | {held} | {_f(r)} | {ln['outcome'] if ln else '-'} | "
                       f"{'-' if d is None else f'{d:+.3f}'} | {pct} |")
        s = c.get("same_openings_m2")
        if s:
            out.append(f"| {c['class']} same openings | m2 | {s['engine']:.3f} on {len(s['openings'])} | - | - | "
                       f"{s['freelancer']:.3f} | DIAGNOSTIC | {s['diff']:+.3f} | {s['pct']:+.2f} % |")
    out += ["", "| His row | Label | Class | His count x W x H = m2 | Openings covered | Settled pcs | m2 this side | Scope |",
            "|---|---|---|---|---|---|---|---|"]
    for s in res["scope_rows"]:
        unc = f" (+? {', '.join(s['uncertain_openings'])})" if s["uncertain_openings"] else ""
        out.append(f"| {s['ref_id']} | {s['label']} | {s['class']} | {s['his_count']:g} x {s['his_width']:g} x "
                   f"{s['his_height']:g} = {s['his_m2']:.3f} | {', '.join(s['openings']) or '-'}{unc} | "
                   f"{s['openings_pcs_settled']} | {_f(s['engine_m2'])} | {s['scope']} |")
    if res.get("engine_run_pcs"):
        out += ["", "Engine run (released BOQ lines only; no engine door / window m2 line exists):", "",
                "| Key | Outcome | Engine | Freelancer | Diff |", "|---|---|---|---|---|"]
        for ln in res["engine_run_pcs"]["lines"]:
            d = ln["signed_error"]
            eq = "no line" if ln["outcome"] == S.OUT_SILENT else _f(ln["engine_qty"])
            out.append(f"| {ln['key']} | {ln['outcome']} | {eq} | {_f(ln['reference_qty'])} | "
                       f"{'-' if d is None else f'{d:+.3f}'} |")
    return "\n".join(out) + "\n"


def _read_register(path):
    import csv
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main_openings(argv):
    ap = argparse.ArgumentParser(description="T-181 doors and windows like for like (pcs and m2)")
    ap.add_argument("--openings-register", required=True, help="opening register CSV (T-150 r2 layout)")
    ap.add_argument("--openings-raw", required=True, help="FREELANCER_RAW_ROWS.json")
    ap.add_argument("--openings-key-map", required=True, help=OPENINGS_SCHEMA + " file")
    ap.add_argument("--openings-engine-run", help="run dir with BOQ_LINES.json: the engine's own pcs lines beside")
    ap.add_argument("--openings-out", required=True)
    ap.add_argument("--openings-markdown")
    a = ap.parse_args(argv)
    lines = None
    if a.openings_engine_run:
        lines = json.loads((Path(a.openings_engine_run) / "BOQ_LINES.json").read_text(encoding="utf-8"))
    res = openings_like_for_like(_read_register(a.openings_register),
                                 json.loads(Path(a.openings_raw).read_text(encoding="utf-8")),
                                 json.loads(Path(a.openings_key_map).read_text(encoding="utf-8")), lines)
    Path(a.openings_out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    md = openings_markdown(res)
    if a.openings_markdown:
        Path(a.openings_markdown).write_text(md, encoding="utf-8")
    print(md, end="")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if "--openings-register" in argv:          # T-181 opt-in path; the v1 / v2 CLI below is unchanged
        return main_openings(argv)
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True)
    ap.add_argument("--reference", required=True)
    ap.add_argument("--key-map", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown")
    # T-177 opt-in: the SCOREBOARD v2 table (tools/scoreboard_v2.py) in the same call; without --v2-out nothing below
    # runs and the outputs above stay byte-identical
    ap.add_argument("--v2-out", help="SCOREBOARD v2 JSON (tools/scoreboard_v2.py)")
    ap.add_argument("--v2-markdown")
    ap.add_argument("--v2-label", help="Baseline cell of the --run side")
    ap.add_argument("--v2-verdicts", help="checker verdict file URBAN_SCOREBOARD_CHECKER_VERDICTS_V1")
    ap.add_argument("--v2-candidate-lines", help="a candidate's V3_0_x_BOQ_LINES.json, scored beside --run's "
                                                 "release report")
    ap.add_argument("--v2-candidate-label")
    ap.add_argument("--v2-heading", help="UTC date time for the '## SCOREBOARD v2' heading")
    # T-182 opt-in: the five-measures table (## SCOREBOARD v2.1); without it the v2 output is unchanged
    ap.add_argument("--v2-five-measures", action="store_true", help="T-182 five-measures layout")
    ap.add_argument("--v2-min-accuracy-scope", type=float, help="minimum scope share for the accuracy column")
    # T-216 opt-in: review-set bindings (URBAN_SCORER_SET_BINDINGS_V1); without it every output stays byte-identical
    ap.add_argument("--set-bindings", help=SET_BINDINGS_SCHEMA + " file: bound review sets answer their key "
                                           "ASSUMED — OWNER-APPROVED, reported apart")
    a = ap.parse_args(argv)
    v2 = [a.v2_markdown, a.v2_label, a.v2_verdicts, a.v2_candidate_lines, a.v2_candidate_label, a.v2_heading,
          a.v2_five_measures or None, a.v2_min_accuracy_scope]
    if a.v2_min_accuracy_scope is not None and not a.v2_five_measures:
        ap.error("--v2-min-accuracy-scope needs --v2-five-measures")
    if a.v2_out is None and any(x is not None for x in v2):
        ap.error("the --v2-* options need --v2-out")
    if a.v2_out is not None and (a.v2_label is None or a.v2_verdicts is None):
        ap.error("--v2-out needs --v2-label and --v2-verdicts")
    km_doc = json.loads(Path(a.key_map).read_text(encoding="utf-8"))
    if a.set_bindings:
        km_doc = with_set_bindings(km_doc, json.loads(Path(a.set_bindings).read_text(encoding="utf-8")))
    result = run(a.run, json.loads(Path(a.reference).read_text(encoding="utf-8")), km_doc)
    Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    md = S.markdown(result)
    if a.set_bindings:
        md += set_bindings_markdown([(Path(a.run).name, result["adapter"])])
    if a.markdown:
        Path(a.markdown).write_text(md, encoding="utf-8")
    print(md, end="")
    if a.v2_out is not None:
        from tools import scoreboard_v2 as V2
        five = {} if not a.v2_five_measures else {"layout": V2.LAYOUT_FIVE, "min_scope": (
            V2.MIN_ACCURACY_SCOPE if a.v2_min_accuracy_scope is None else a.v2_min_accuracy_scope)}
        res2 = V2.build(a.run, a.v2_label, json.loads(Path(a.reference).read_text(encoding="utf-8")),
                        km_doc,
                        json.loads(Path(a.v2_verdicts).read_text(encoding="utf-8")),
                        a.v2_candidate_lines, a.v2_candidate_label, **five)
        md2 = V2.write(res2, a.v2_out, a.v2_markdown, a.v2_heading)
        if a.set_bindings:
            md2 += set_bindings_markdown([(s["label"], s["adapter"]) for s in res2["sides"]])
            if a.v2_markdown:
                Path(a.v2_markdown).write_text(md2, encoding="utf-8")
        print(md2, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
