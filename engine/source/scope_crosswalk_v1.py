"""SCOPE CROSSWALK V1 (T-196; residential review R7, PROJECT_UNDERSTANDING_ASSESSMENT s.6): BOQ scope against the
drawings, in both directions. A pure check module: it reads plain dicts, writes nothing, moves no quantity and is
wired into no method.

    crosswalk(elements, rows, row_map, lines, line_links, rulings=(), documents=())  -> report dict

Inputs (all plain data; no drawing is read here):
  elements    drawn elements, one dict each: id, kind, floor, label (printed mark or None), source (where the element
              comes from: ELEMENT_REGISTER_V0, or a merged ledger such as "T-183"), refs (sheet references).
              build_elements(register, extra) joins an element_register_v0 register and ledger elements.
  rows        a reference BOQ's rows (the freelancer): row_id, trade, unit, qty, row_kind (DETAIL / SUBTOTAL /
              COVER_TOTAL). Only DETAIL rows are crosswalked; totals are sums of rows, not scope of their own.
  row_map     row_id -> entry. An entry names its elements either as ids ("elements": [id or {"id", "component"}]) or
              by a selector ("select": {"kind", "label_base", "floor"}: every element of that kind whose label is
              label_base or label_base.<n>, optionally on one floor), or declares
              {"status": "NOT_DRAWN", "searched": [sheet references]}   (scope on no drawing; the search is required)
              {"status": "SCOPE_UNKNOWN", "reason": ...}                  (scope cannot be established yet)
              {"status": "NOT_MAPPED", "reason": ...}                     (drawn kind, element join still pending)
              A drawn entry may also list "not_drawn_parts": [{part, searched, qty, discipline, element}] for a part
              of the row that one discipline does not draw (a dome the architecture shows with no structure): the
              row keeps its DRAWN / AGGREGATE status and the part is reported as NOT_DRAWN_PART, never dropped.
  lines       the candidate BOQ lines (boq_line schema: line_id, item_code, unit, evidence_state, location).
  line_links  line_id -> [element ids] for lines already joined (element_register_v0 links, ledger links). Every other
              line is UNLINKED with the reason given in "unlinked_reasons" (line_id -> text) or "no element named".
  rulings     cross-trade ownership rulings of the element register: {"element", "carried_by" (element id whose
              lines carry it), "basis"}. A carried element is not MISSING_LINE when its carrier has a line.
  documents   the document register's required-sheet list (T-195 MISSING list): {"item", "status" PRESENT /
              NOT_IN_SET, "families": [item-code prefixes], "trades": [reference trades], "row_ids": [extra rows]}.

Statuses
  rows    DRAWN (one element) / AGGREGATE (several elements; listed) / NOT_DRAWN (searched, on no drawing) /
          SCOPE_UNKNOWN (with reason) / NOT_MAPPED (no entry in the map yet: listed, never treated as any of the
          others). A map entry whose ids or selector find no element is SCOPE_UNKNOWN with reason MAP_MISS.
  lines   LINKED / UNLINKED (with reason).
  elements HAS_LINE / CARRIED_BY_RULING / MISSING_LINE. Drawn elements only: an element is never invented here.
  documents NOT_ISSUED: a required sheet that is not in the set is a DESIGNER item; the candidate lines and the
          reference rows of the families it feeds are listed with their quantities UNKNOWN, never 0.

Findings: DUPLICATE_ROW (two DETAIL rows on the same element, component and trade: possible double count in the
reference BOQ; rows on DIFFERENT components of one element are an aggregate of that element, counted once), RULING_
CARRIER_WITHOUT_LINE, ROW_WITHOUT_LINE (an element the reference BOQ prices but no candidate line measures),
NOT_DRAWN_SCOPE (reference quantity on no drawing, per unit), NOT_DRAWN_PART (one per undrawn part of a drawn row).

Quantities are carried only to state impact in units; nothing is summed into a BOQ, nothing becomes 0.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict

SCHEMA = "URBAN_SCOPE_CROSSWALK_V1"
ROW_STATUSES = ("DRAWN", "AGGREGATE", "NOT_DRAWN", "SCOPE_UNKNOWN", "NOT_MAPPED")
LINE_STATUSES = ("LINKED", "UNLINKED")
ELEMENT_STATUSES = ("HAS_LINE", "CARRIED_BY_RULING", "MISSING_LINE")
QUANTITY_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")   # engine/source/boq_line.py QUANTITY_STATES


def build_elements(register=None, extra=()):
    """drawn elements from an element_register_v0 register (its elements) plus ledger elements (extra). Ids must be
    unique: a ledger element that repeats a register id is refused (one element, one id)."""
    out = {}
    for e in (register or {}).get("elements") or []:
        out[e["id"]] = {"id": e["id"], "kind": e["kind"], "floor": e.get("floor"), "label": e.get("label"),
                        "source": "ELEMENT_REGISTER_V0", "refs": [], "status": e.get("status")}
    for e in extra:
        if e["id"] in out:
            raise ValueError(f"element id {e['id']!r} given twice")
        out[e["id"]] = {"id": e["id"], "kind": e["kind"], "floor": e.get("floor"), "label": e.get("label"),
                        "source": e.get("source") or "LEDGER", "refs": list(e.get("refs") or []),
                        "status": e.get("status")}
    return [out[k] for k in sorted(out)]


def register_links(register):
    """(line_id -> [element ids], line_id -> unlinked reason) of an element_register_v0 register. HOST links (the room
    around an opening or a flight) are not the element the line measures and are left out."""
    links, reasons = defaultdict(list), {}
    for e in register.get("elements") or []:
        for b in e.get("boq_lines") or []:
            if b.get("role") != "HOST" and e["id"] not in links[b["line_id"]]:
                links[b["line_id"]].append(e["id"])
    for u in register.get("unlinked_lines") or []:
        reasons[u["line_id"]] = u["reason"]
    return dict(links), reasons


def _label_base(label):
    return re.sub(r"\.\d+$", "", label or "")


def _select(sel, elements):
    hit = []
    for e in elements:
        if e["kind"] != sel.get("kind"):
            continue
        if sel.get("floor") is not None and e.get("floor") != sel["floor"]:
            continue
        if "label_base" in sel and _label_base(e.get("label")) != sel["label_base"]:
            continue
        hit.append(e["id"])
    return sorted(hit)


def _row_refs(entry, elements, by_id):
    """[(element id, component)] named by a map entry, and the ids that exist in no element."""
    refs, missing = [], []
    for x in entry.get("elements") or []:
        eid, comp = (x, None) if isinstance(x, str) else (x["id"], x.get("component"))
        (refs if eid in by_id else missing).append((eid, comp))
    if entry.get("select"):
        refs += [(i, entry.get("component")) for i in _select(entry["select"], elements)]
    return refs, missing


def classify_rows(rows, row_map, elements):
    by_id = {e["id"]: e for e in elements}
    out = []
    for r in rows:
        if r.get("row_kind", "DETAIL") != "DETAIL":
            continue
        base = {"row_id": r["row_id"], "trade": r.get("trade"), "unit": r.get("unit"), "qty": r.get("qty"),
                "floor": r.get("floor")}
        entry = row_map.get(r["row_id"])
        if entry is None:
            out.append(dict(base, status="NOT_MAPPED", elements=[], reason="no crosswalk entry yet"))
            continue
        st = entry.get("status")
        if st == "NOT_DRAWN":
            if not entry.get("searched"):
                raise ValueError(f"{r['row_id']}: NOT_DRAWN needs the sheets searched")
            out.append(dict(base, status="NOT_DRAWN", elements=[], searched=list(entry["searched"]),
                            reason=entry.get("basis") or "on no drawing of the set"))
            continue
        if st == "NOT_MAPPED":                              # the join is pending, with its reason (not a scope verdict)
            out.append(dict(base, status="NOT_MAPPED", elements=[], reason=entry.get("reason") or "join pending"))
            continue
        if st == "SCOPE_UNKNOWN":
            out.append(dict(base, status="SCOPE_UNKNOWN", elements=[], reason=entry.get("reason") or "not established"))
            continue
        refs, missing = _row_refs(entry, elements, by_id)
        if missing or not refs:
            out.append(dict(base, status="SCOPE_UNKNOWN", elements=[e for e, _c in refs],
                            reason="MAP_MISS: " + (", ".join(m for m, _c in missing) if missing
                                                   else f"selector {entry.get('select')} found no element")))
            continue
        ids = sorted({e for e, _c in refs})
        parts = []
        for p in entry.get("not_drawn_parts") or []:       # e.g. one of three domes with no structural drawing
            if not p.get("searched"):
                raise ValueError(f"{r['row_id']}: a NOT_DRAWN part needs the sheets searched")
            parts.append({"part": p["part"], "discipline": p.get("discipline"), "element": p.get("element"),
                          "searched": list(p["searched"]), "reference_qty": p.get("qty")})
        out.append(dict(base, status="DRAWN" if len(ids) == 1 else "AGGREGATE", elements=ids,
                        components=sorted({c for _e, c in refs if c}), basis=entry.get("basis"),
                        not_drawn_parts=parts))
    return out


def classify_lines(lines, line_links, elements, unlinked_reasons=None):
    known = {e["id"] for e in elements}
    unlinked_reasons = unlinked_reasons or {}
    out = []
    for ln in lines:
        ids = sorted(i for i in line_links.get(ln["line_id"], []) if i in known)
        loc = ln.get("location") or {}
        rec = {"line_id": ln["line_id"], "item_code": ln["item_code"], "unit": ln["unit"],
               "evidence_state": ln.get("evidence_state"), "measured_net": ln.get("measured_net"),
               "element_key": loc.get("element_id"), "floor": loc.get("floor")}
        if ids:
            out.append(dict(rec, status="LINKED", elements=ids))
        else:
            out.append(dict(rec, status="UNLINKED", elements=[],
                            reason=unlinked_reasons.get(ln["line_id"]) or "no element named"))
    return out


def classify_elements(elements, line_recs, row_recs, rulings=()):
    lines_of, rows_of = defaultdict(list), defaultdict(list)
    for ln in line_recs:
        for e in ln["elements"]:
            lines_of[e].append(ln["line_id"])
    for r in row_recs:
        for e in r["elements"]:
            if r["status"] in ("DRAWN", "AGGREGATE"):
                rows_of[e].append(r["row_id"])
    carried = {}
    for ru in rulings:
        carried.setdefault(ru["element"], []).append(ru)
    out, findings = [], []
    for e in elements:
        rec = {"id": e["id"], "kind": e["kind"], "floor": e.get("floor"), "source": e.get("source"),
               "lines": sorted(lines_of.get(e["id"], [])), "reference_rows": sorted(rows_of.get(e["id"], []))}
        if rec["lines"]:
            rec["status"] = "HAS_LINE"
        elif any(lines_of.get(ru["carried_by"]) for ru in carried.get(e["id"], [])):
            ru = next(ru for ru in carried[e["id"]] if lines_of.get(ru["carried_by"]))
            rec.update(status="CARRIED_BY_RULING", carried_by=ru["carried_by"], basis=ru.get("basis"))
        else:
            rec["status"] = "MISSING_LINE"
            for ru in carried.get(e["id"], []):
                findings.append({"finding": "RULING_CARRIER_WITHOUT_LINE", "element": e["id"],
                                 "carried_by": ru["carried_by"]})
            if rec["reference_rows"]:
                findings.append({"finding": "ROW_WITHOUT_LINE", "element": e["id"], "rows": rec["reference_rows"]})
        out.append(rec)
    return out, findings


def documents_not_issued(documents, line_recs, row_recs):
    out = []
    for d in documents:
        if d.get("status") != "NOT_IN_SET":
            continue
        fam = tuple(d.get("families") or ())
        trades = set(d.get("trades") or ())
        lines = sorted(ln["line_id"] for ln in line_recs if fam and ln["item_code"].startswith(fam))
        named = set(d.get("row_ids") or ())
        rows = sorted(r["row_id"] for r in row_recs if r.get("trade") in trades or r["row_id"] in named)
        out.append({"item": d["item"], "status": "NOT_ISSUED", "designer_item": True, "families": list(fam),
                    "trades": sorted(trades), "candidate_lines": lines, "reference_rows": rows,
                    "quantity_status": "UNKNOWN (sheet not issued; never 0)"})
    return out


def _duplicates(row_recs, rows_by_id):
    """two or more DETAIL rows on the same element, component and trade; one finding per group of rows (an aggregate
    row pair over many elements is ONE finding listing the elements)."""
    seen = defaultdict(list)
    for r in row_recs:
        if r["status"] not in ("DRAWN", "AGGREGATE"):
            continue
        comps = r.get("components") or [None]
        for e in r["elements"]:
            for c in comps:
                seen[(e, c, rows_by_id[r["row_id"]].get("trade"))].append(r["row_id"])
    groups = defaultdict(list)
    for (e, c, t), rs in seen.items():
        if len(rs) > 1:
            groups[(tuple(sorted(rs)), c, t)].append(e)
    return [{"finding": "DUPLICATE_ROW", "rows": list(k[0]), "component": k[1], "trade": k[2], "elements": sorted(v)}
            for k, v in sorted(groups.items(), key=lambda t: (t[0][0], str(t[0][1]), str(t[0][2])))]


def crosswalk(elements, rows, row_map, lines, line_links, rulings=(), documents=(), unlinked_reasons=None):
    elements = sorted(elements, key=lambda e: e["id"])
    if len({e["id"] for e in elements}) != len(elements):
        raise ValueError("element ids repeat")
    rows_by_id = {r["row_id"]: r for r in rows}
    if len(rows_by_id) != len(rows):
        raise ValueError("row ids repeat")
    unknown = sorted(set(row_map) - set(rows_by_id))
    if unknown:
        raise ValueError(f"row map names rows that do not exist: {unknown[:5]}")
    row_recs = classify_rows(rows, row_map, elements)
    line_recs = classify_lines(lines, line_links, elements, unlinked_reasons)
    el_recs, findings = classify_elements(elements, line_recs, row_recs, rulings)
    findings = _duplicates(row_recs, rows_by_id) + findings
    nd = defaultdict(float)
    for r in row_recs:
        if r["status"] == "NOT_DRAWN" and r.get("qty") is not None:
            nd[r.get("unit")] += float(r["qty"])
    for unit, q in sorted(nd.items(), key=lambda t: str(t[0])):
        findings.append({"finding": "NOT_DRAWN_SCOPE", "unit": unit, "reference_qty": round(q, 6),
                         "rows": sorted(r["row_id"] for r in row_recs if r["status"] == "NOT_DRAWN"
                                        and r.get("unit") == unit)})
    for r in row_recs:                                   # a drawn row with an undrawn part: the part stays visible
        for p in r.get("not_drawn_parts") or []:
            findings.append({"finding": "NOT_DRAWN_PART", "row_id": r["row_id"], "part": p["part"],
                             "discipline": p["discipline"], "element": p["element"], "unit": r.get("unit"),
                             "reference_qty": p["reference_qty"]})
    docs = documents_not_issued(documents, line_recs, row_recs)
    rep = {"schema": SCHEMA, "rows": row_recs, "lines": line_recs, "elements": el_recs, "not_issued": docs,
           "findings": findings}
    rep["summary"] = summary(rep, rows)
    return rep


def summary(rep, rows=()):
    detail = sum(1 for r in rows if r.get("row_kind", "DETAIL") == "DETAIL")
    s = {"rows": dict(Counter(r["status"] for r in rep["rows"])),
         "rows_by_trade": {t: dict(c) for t, c in sorted(_by(rep["rows"], "trade").items(), key=lambda t: str(t[0]))},
         "lines": dict(Counter(ln["status"] for ln in rep["lines"])),
         "lines_unlinked_by_reason": dict(Counter(ln.get("reason") for ln in rep["lines"]
                                                  if ln["status"] == "UNLINKED")),
         "elements": dict(Counter(e["status"] for e in rep["elements"])),
         "elements_missing_by_kind": dict(Counter(e["kind"] for e in rep["elements"]
                                                  if e["status"] == "MISSING_LINE")),
         "not_issued": len(rep["not_issued"]),
         "findings": dict(Counter(f["finding"] for f in rep["findings"]))}
    s["all_rows_accounted"] = detail == len(rep["rows"])
    return s


def _by(recs, key):
    out = defaultdict(Counter)
    for r in recs:
        out[r.get(key)][r["status"]] += 1
    return out
