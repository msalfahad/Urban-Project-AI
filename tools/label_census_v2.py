"""LABEL CENSUS V2 (T-344): the label census read with the compound room vocabulary and the merged label binding.

Read-only diagnostic (UP-QTY-STATUS-001: every labelled space is reported once). Nothing is measured here and no engine
output changes. tools/label_census.py (URBAN_LABEL_CENSUS_V1, the ARCH_TAKEOFF_V2.9 census) is not changed: this tool
calls it and adds two things on top.

1. VOCABULARY ROOM_VOCAB_V2 (engine/source/room_vocab.py, R-T342-BIND-1 step 1): every text is typed with compound
   phrases before bare words ('swimming pool' is a POOL, not a BATHROOM by its first word). A label V1 types but V2 holds
   (a compound naming no room type, e.g. car wash) stays in the census as HELD (cause VOCAB_V2_HELD_COMPOUND): a label is
   never dropped because the vocabulary changed. Each label records its V1 code and, when they differ, RETYPED.
2. BINDING (a merged label-binding ledger, R-T342-BIND-1, e.g. research/agents_t342 LABEL_BINDING_T342.csv +
   SCOPES_T342.csv on its candidate extract). A label the V1 logic leaves SILENT_OMISSION becomes ACCOUNTED_BY_BINDING
   only when its ledger row passes every check below; otherwise it stays SILENT_OMISSION and the refusal is printed:
     - the row exists, names a face, and its floor and code equal the census label's (code read with V2);
     - the face has scopes; the row's binding equals the one its scopes give (all NOT_APPLICABLE -> NOT_APPLICABLE;
       all BOUND / NOT_APPLICABLE -> BOUND; some BOUND, some MISSING -> PARTIAL; none BOUND -> MISSING);
     - a BOUND scope names lines; a NOT_APPLICABLE scope carries drawing evidence; a MISSING scope names its unit and a
       quantity or a bound, never 0 (missing is never zero);
     - the row's lines are exactly its BOUND scopes' lines (a line no BOUND scope carries was bound by name only:
       REFUSED_NAME_ONLY); every line exists in the candidate extract (REFUSED_UNKNOWN_LINE), was bound through its own
       source and not only by citing the label (candidate source empty: REFUSED_NAME_ONLY), and is not a 0 line
       (REFUSED_ZERO_LINE); a line a scope lists as refused never binds;
     - a DUPLICATE_OF row points to a first label of the SAME face whose own row passes (the space is counted once).
   A label with no ledger row, or a MISSING_NO_FACE row, stays SILENT_OMISSION.

    census_v2(texts, regions, rooms, coverage, unresolved=(), ledger=None, lines=None) -> {"labels", "unread", "summary"}
    rebind(census_v1_out, ledger=None, lines=None)   the same two steps on a saved V1 census (labels with their text);
        a MEASURED / HELD / UNSUPPORTED label whose code V2 changes cannot be re-checked against its room there and is
        SILENT_OMISSION (cause CODE_CHANGED_BY_VOCAB_V2) until a drawing run re-reads it
    load_ledger(rows_csv, scopes_csv) / load_lines(candidate_json)

CLI (one architectural run; the V1 census of the same run is written beside, byte-for-byte the V1 tool's output):
    python3 -I tools/label_census_v2.py DRAWING.dxf --out census_v2.json [--v1-out census_v1.json]
        [--method ARCH_TAKEOFF_V2.9] [--binding-rows ROWS.csv --binding-scopes SCOPES.csv --lines CANDIDATE.json]
General: no layer, room, project or label id is coded here.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import label_census as V1  # noqa: E402

POLICY = "URBAN_LABEL_CENSUS_V2"
RULE = "UP-QTY-STATUS-001"
BIND_RULE = "R-T342-BIND-1"
VOCAB = "ROOM_VOCAB_V2"
STATUSES = ("MEASURED", "HELD", "UNSUPPORTED", "ACCOUNTED_BY_BINDING", "SILENT_OMISSION")
BINDINGS = ("BOUND", "PARTIAL", "MISSING", "NOT_APPLICABLE")
ROW_BINDINGS = BINDINGS + ("DUPLICATE_OF", "MISSING_NO_FACE")
SCOPE_STATUS = ("BOUND", "NOT_APPLICABLE", "MISSING")


# ---- vocabulary --------------------------------------------------------------------------------------------------
def _v1_word(text):
    from engine.source import arch_rooms as AR
    return AR.room_word(text or "")


def type_label(text):
    """-> (census code, v1 code, vocab status): the V2 code; a label V1 types and V2 holds keeps its V1 code for the
    census lookup with status HELD_COMPOUND (it is reported HELD, never dropped)."""
    from engine.source import room_vocab as RV
    v1 = _v1_word(text)[0]
    cls = RV.classify(text or "")
    if cls["status"] == "TYPED":
        return cls["code"], v1, "TYPED"
    if cls["status"] == "HELD_COMPOUND" and v1:
        return v1, v1, "HELD_COMPOUND"
    return None, v1, cls["status"]


def _word(text):
    code = type_label(text)[0]
    return (code, None) if code else (None, None)


# ---- ledger ------------------------------------------------------------------------------------------------------
def _cell(v):
    if v is None:
        return None
    v = v.strip()
    if v == "":
        return None
    if v[:1] in "[{":
        return json.loads(v)
    return v


def _num(v):
    v = _cell(v) if isinstance(v, str) else v
    return None if v is None else float(v)


def load_ledger(rows_csv, scopes_csv):
    """the merged binding ledger (R-T342-BIND-1 CSV pair) -> {"rows": {text_id: row}, "scopes": {face_id: [scope]}}."""
    rows, scopes = {}, {}
    with open(rows_csv, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            rows[r["text_id"]] = {"text_id": r["text_id"], "floor": _cell(r.get("floor")), "code": _cell(r.get("code")),
                                  "face_id": _cell(r.get("face_id")), "binding": _cell(r.get("binding")),
                                  "duplicate_of": _cell(r.get("duplicate_of")), "lines": _cell(r.get("lines")) or []}
    with open(scopes_csv, encoding="utf-8", newline="") as fh:
        for s in csv.DictReader(fh):
            scopes.setdefault(s["face_id"], []).append(
                {"scope": _cell(s.get("scope")), "status": _cell(s.get("status")), "lines": _cell(s.get("lines")) or [],
                 "refused": _cell(s.get("refused")) or [], "quantity": _num(s.get("quantity")),
                 "bound": _cell(s.get("bound")), "unit": _cell(s.get("unit")),
                 "evidence_status": _cell(s.get("evidence_status")), "evidence": _cell(s.get("evidence"))})
    return {"rows": rows, "scopes": scopes}


def ledger_of(bind_out):
    """a binding result {"rows": [...], "scopes": [...]} (research/agents_t342 bind()) -> the ledger form."""
    rows = {r["text_id"]: dict(r) for r in bind_out.get("rows") or ()}
    scopes = {}
    for s in bind_out.get("scopes") or ():
        scopes.setdefault(s["face_id"], []).append(dict(s))
    return {"rows": rows, "scopes": scopes}


def load_lines(candidate_json):
    """candidate extract {"lines": [{"line_id", "item_code", "quantity", "source", "cites", ...}]} -> {line_id: line}."""
    d = json.loads(Path(candidate_json).read_text(encoding="utf-8"))
    d = d["lines"] if isinstance(d, dict) else d
    return {ln["line_id"]: ln for ln in d}


def _binding_of_scopes(sc):
    st = [s.get("status") for s in sc]
    if all(s == "NOT_APPLICABLE" for s in st):
        return "NOT_APPLICABLE"
    if all(s in ("BOUND", "NOT_APPLICABLE") for s in st):
        return "BOUND"
    if any(s == "BOUND" for s in st):
        return "PARTIAL"
    return "MISSING"


def _check_scopes(sc):
    for s in sc:
        st, name = s.get("status"), s.get("scope") or "?"
        if st not in SCOPE_STATUS:
            return f"REFUSED_SCOPE_STATE {name}: {st}"
        if st == "BOUND" and not s.get("lines"):
            return f"REFUSED_BOUND_WITHOUT_LINE {name}"
        if st == "NOT_APPLICABLE" and not s.get("evidence"):
            return f"REFUSED_NOT_APPLICABLE_WITHOUT_EVIDENCE {name}"
        if st == "MISSING":
            q, b = s.get("quantity"), s.get("bound")
            if q in (0, 0.0) or (b and all(x in (0, 0.0) for x in b)):
                return f"REFUSED_MISSING_AS_ZERO {name}"
            if q is None and not b:
                return f"REFUSED_MISSING_UNQUANTIFIED {name}"
            if not s.get("unit"):
                return f"REFUSED_MISSING_NO_UNIT {name}"
    return None


def check_row(text_id, floor, code, ledger, lines, _depth=0, census=None):
    """-> (binding, duplicate_of, lines, reason): binding None and a reason when the ledger row is refused.
    census: {text_id: (floor, code)} of the census labels; a duplicate's first label that is itself a census label is
    checked with ITS census floor and code (a first label the census refuses refuses its duplicates)."""
    row = (ledger or {}).get("rows", {}).get(text_id)
    if row is None:
        return None, None, [], "NO_BINDING_ROW"
    b = row.get("binding")
    if b not in ROW_BINDINGS:
        return None, None, [], f"REFUSED_BINDING_STATE {b}"
    if b == "MISSING_NO_FACE" or not row.get("face_id"):
        return None, None, [], "REFUSED_NO_FACE"
    if floor is not None and row.get("floor") is not None and str(row["floor"]) != str(floor):
        return None, None, [], f"REFUSED_FLOOR {row['floor']} vs census {floor}"
    if code is not None and row.get("code") != code:
        return None, None, [], f"REFUSED_CODE ledger {row.get('code')} vs census {code}"
    if b == "DUPLICATE_OF":
        first = (ledger or {}).get("rows", {}).get(row.get("duplicate_of"))
        if _depth or first is None or first.get("binding") == "DUPLICATE_OF":
            return None, None, [], f"REFUSED_DUPLICATE_TARGET {row.get('duplicate_of')}"
        if first.get("face_id") != row["face_id"]:
            return None, None, [], f"REFUSED_DUPLICATE_OTHER_FACE {first.get('face_id')} vs {row['face_id']}"
        if first.get("code") != row.get("code"):
            return None, None, [], f"REFUSED_DUPLICATE_OTHER_CODE {first.get('code')} vs {row.get('code')}"
        ff, fc = (census or {}).get(first["text_id"], (first.get("floor"), first.get("code")))
        fb, _, fl, why = check_row(first["text_id"], ff, fc, ledger, lines, 1)
        if fb is None:
            return None, None, [], f"REFUSED_DUPLICATE_TARGET_REFUSED {first['text_id']}: {why}"
        return fb, first["text_id"], fl, None
    sc = (ledger or {}).get("scopes", {}).get(row["face_id"]) or []
    if not sc:
        return None, None, [], f"REFUSED_NO_SCOPE {row['face_id']}"
    why = _check_scopes(sc)
    if why:
        return None, None, [], why
    want = _binding_of_scopes(sc)
    if want != b:
        return None, None, [], f"REFUSED_BINDING_INCONSISTENT row {b} vs scopes {want}"
    bound = {x for s in sc if s.get("status") == "BOUND" for x in s.get("lines") or ()}
    refused = {(x[0] if isinstance(x, (list, tuple)) else x) for s in sc for x in s.get("refused") or ()}
    rl = set(row.get("lines") or ())
    for ln in sorted(rl - bound):
        return None, None, [], f"REFUSED_NAME_ONLY {ln} (no BOUND scope of the face carries it)"
    for ln in sorted(bound - rl):
        return None, None, [], f"REFUSED_BINDING_INCONSISTENT {ln} bound by a scope, not on the row"
    for ln in sorted(bound & refused):
        return None, None, [], f"REFUSED_LINE_REFUSED_BY_SCOPE {ln}"
    if bound and lines is None:
        return None, None, [], "REFUSED_NO_CANDIDATE (bound lines cannot be checked)"
    for ln in sorted(bound):
        rec = (lines or {}).get(ln)
        if rec is None:
            return None, None, [], f"REFUSED_UNKNOWN_LINE {ln}"
        if not rec.get("source"):
            return None, None, [], f"REFUSED_NAME_ONLY {ln} (its own inputs name no entity of the face)"
        if rec.get("quantity") in (0, 0.0):
            return None, None, [], f"REFUSED_ZERO_LINE {ln}"
    return b, None, sorted(bound), None


def _apply(rec, ledger, lines, census=None):
    rec.setdefault("binding", None)
    rec.setdefault("duplicate_of", None)
    rec.setdefault("lines", [])
    rec.setdefault("binding_refused", None)
    if rec["status"] != "SILENT_OMISSION" or ledger is None:
        return rec
    b, dup, ls, why = check_row(rec["text_id"], rec.get("floor"), rec["code"], ledger, lines, census=census)
    if b is None:
        rec["binding_refused"] = why
        return rec
    face = ledger["rows"][rec["text_id"]]["face_id"]
    rec.update(status="ACCOUNTED_BY_BINDING", binding=b, duplicate_of=dup, lines=ls, face_id=face,
               cause=f"{BIND_RULE}:{('DUPLICATE_OF ' + dup + ' ') if dup else ''}{b}",
               open_scopes=[{"scope": s["scope"], "quantity": s.get("quantity"), "bound": s.get("bound"),
                             "unit": s.get("unit"), "evidence_status": s.get("evidence_status")}
                            for s in ledger["scopes"].get(face) or () if s.get("status") == "MISSING"])
    return rec


def _apply_all(labels, ledger, lines):
    census = {r["text_id"]: (r.get("floor"), r["code"]) for r in labels}
    return [_apply(r, ledger, lines, census) for r in labels]


def _summary(labels, unread, ledger):
    by_floor = {}
    for rec in labels:
        by_floor.setdefault(rec["floor"], Counter())[rec["status"]] += 1
    for u in unread:
        by_floor.setdefault(u["floor"], Counter())["UNREAD_SHX"] += 1
    acc = [r for r in labels if r["status"] == "ACCOUNTED_BY_BINDING"]
    return {"policy": POLICY, "rule": RULE, "vocabulary": VOCAB, "binding_rule": BIND_RULE if ledger else None,
            "labels": len(labels),
            "by_status": {s: sum(1 for r in labels if r["status"] == s) for s in STATUSES},
            "by_binding": {b: sum(1 for r in acc if r["binding"] == b and not r["duplicate_of"]) for b in BINDINGS},
            "duplicates_counted_once": sum(1 for r in acc if r["duplicate_of"]),
            "open_scopes": {r["text_id"]: [f"{s['scope']}: " + (f"{s['quantity']} {s['unit']}" if s["quantity"]
                                           is not None else f"blank, bound {s['bound']} {s['unit']}")
                                           for s in r["open_scopes"]]
                            for r in acc if r.get("open_scopes") and not r["duplicate_of"]},
            "retyped": sorted(r["text_id"] for r in labels if r.get("retype")),
            "binding_refused": {r["text_id"]: r["binding_refused"] for r in labels if r.get("binding_refused")
                                and r["binding_refused"] != "NO_BINDING_ROW"},
            "unread_shx": len(unread),
            "silent_by_cause": dict(Counter(r["cause"] for r in labels if r["status"] == "SILENT_OMISSION")),
            "by_floor": {str(k): dict(v) for k, v in sorted(by_floor.items(), key=lambda kv: str(kv[0]))}}


def _vocab_fields(rec, text):
    code, v1, vst = type_label(text)
    rec["v1_code"] = v1
    rec["vocab_status"] = vst
    rec["retype"] = f"RETYPED {v1} -> {code} ({VOCAB}: compound phrase before the bare word)" \
        if (v1 and code and v1 != code) else (f"NEW_LABEL ({VOCAB} types it, V1 did not)" if not v1 else None)
    if vst == "HELD_COMPOUND":
        rec["retype"] = f"HELD_COMPOUND ({VOCAB}: a compound naming no room type; V1 read {v1})"
        if rec["status"] != "HELD":
            rec["census_v1_status"] = rec["status"]
            rec["status"], rec["cause"] = "HELD", "VOCAB_V2_HELD_COMPOUND"
    return rec


def census_v2(texts, regions, rooms, coverage, unresolved=(), ledger=None, lines=None):
    base = V1.census(texts, regions, rooms, coverage, unresolved, word=_word)
    labels = _apply_all([_vocab_fields(dict(r), r.get("text")) for r in base["labels"]], ledger, lines)
    return {"labels": labels, "unread": base["unread"], "summary": _summary(labels, base["unread"], ledger)}


def rebind(census_v1_out, ledger=None, lines=None):
    """V2 vocabulary + binding on a saved V1 census (its labels carry their text). Only V1-typed labels are there: a
    text V2 alone would type is not seen (summary 'v2_only_labels': NOT_READ)."""
    labels = []
    for r in census_v1_out["labels"]:
        rec = dict(r)
        code, v1, vst = type_label(r.get("text"))
        if code is None:
            code = r["code"]
        if code != r["code"] and vst != "HELD_COMPOUND":
            rec["code"] = code
            if r["status"] != "SILENT_OMISSION" or r.get("cause") != "NO_ROOM":
                rec["census_v1_status"] = r["status"]
                rec["status"], rec["cause"] = "SILENT_OMISSION", "CODE_CHANGED_BY_VOCAB_V2"
        labels.append(_vocab_fields(rec, r.get("text")))
    labels = _apply_all(labels, ledger, lines)
    unread = census_v1_out.get("unread")
    if unread is None:                       # a saved census holding only its summary: the UNREAD_SHX counts per floor
        unread = [{"floor": f, "status": "UNREAD_SHX"}
                  for f, c in (census_v1_out.get("summary", {}).get("by_floor") or {}).items()
                  for _ in range(c.get("UNREAD_SHX", 0))]
    s = _summary(labels, unread, ledger)
    s["v2_only_labels"] = "NOT_READ (a saved V1 census holds only V1-typed labels; run on the drawing)"
    return {"labels": labels, "unread": unread, "summary": s}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    ap.add_argument("--v1-out")
    ap.add_argument("--method", default="ARCH_TAKEOFF_V2.9")
    ap.add_argument("--binding-rows")
    ap.add_argument("--binding-scopes")
    ap.add_argument("--lines")
    a = ap.parse_args(argv)
    if bool(a.binding_rows) != bool(a.binding_scopes):
        ap.error("--binding-rows and --binding-scopes go together")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools import urban_boq_m9 as M
    run = M.arch_compute(a.drawing, method=a.method)
    if a.v1_out:
        v1 = V1.census_of_run(run)
        v1["summary"]["method"] = a.method
        Path(a.v1_out).write_text(json.dumps(v1, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    boq, arch, intake = run
    ledger = load_ledger(a.binding_rows, a.binding_scopes) if a.binding_rows else None
    lines = load_lines(a.lines) if a.lines else None
    out = census_v2(intake.get("texts") or (), arch.get("regions") or (), arch.get("rooms") or (),
                    arch.get("coverage") or (), boq.get("unresolved") or (), ledger, lines)
    out["summary"]["method"] = a.method
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(out["summary"], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
