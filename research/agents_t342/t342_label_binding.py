"""T-342 census binding (R-T342-BIND-1): every room label the label census reports with no room (NO_ROOM) is bound to
the candidate lines that measure its PHYSICAL space, or reported NOT_APPLICABLE with drawing evidence, or MISSING with
the BOQ scope it leaves open. Research code, read-only: no engine module, candidate line or released line changes.

    bind(labels, faces, lines, scopes, word=None) -> {"rows": [...], "scopes": [...], "summary": {...}}

    labels   census rows {"text_id", "text", "code", "floor", "status", "cause"} (tools/label_census.py output)
    faces    the physical spaces round the labels, each {"face_id", "floor", "code", "labels": [text ids inside],
             "source": [drawing entity handles that bound it], "area_m2", "evidence"}: one face per physical space
             (several labels may lie in one face: a bilingual pair, a label repeated on a large court); optional
             "corresponds": [{"element", "face_m2", "element_m2", "face_lm", "element_lm", "evidence"}]: the same
             space measured on ANOTHER drawing (a structural pool shell), accepted only when area and perimeter
             agree within CORR_TOL (accepted_elements); a correspondence by name alone is refused
    lines    candidate lines {"line_id", "item_code", "floor", "element_id", "unit", "state", "quantity",
             "source": [entity handles / face ids the line's own inputs name], "cites": [text ids the line names]}
    scopes   the BOQ scopes each physical code needs, per face: {face_id: [{"scope", "item_codes": [...],
             "status": "BOUND" | "NOT_APPLICABLE" | "MISSING", "evidence", "quantity", "bound", "unit",
             "evidence_status", "integration"}]}; a scope's line set is FOUND here, never given
    word     a room-vocabulary function text -> code (compound phrases before bare words, ROOM_VOCAB_V2); None keeps
             the census code

Binding (general, every villa):
  1. RE-TYPE: the label text is re-read with the compound vocabulary first; a label the census typed by a bare word
     inside a compound phrase (an Arabic 'bathroom' word inside 'swimming pool') takes the compound's code, and the
     scope it needs is that of the compound (RETYPED, census code kept for the record). A label is never given wet-room
     scope on a bare-word reading the compound contradicts.
  2. FACE: the label belongs to the face whose label list holds it; a label in no face is MISSING_NO_FACE (HELD, its
     scope unknown, never 0). A second label in a face already holding another label is DUPLICATE_OF that label: the
     space is counted once.
  3. LINES BY SOURCE ENTITIES: a line binds to a scope of a face only when the line's item code is one of the scope's
     item codes AND its own source names an entity handle or face id of that face. A line that only CITES the label
     (by text id) or only shares a word with it is refused (REFUSED_NAME_ONLY), and a line whose item code is not
     the scope's (a court bound to an interior floor-tile line) is refused (REFUSED_WRONG_TRADE).
  4. A scope given BOUND that finds no line is downgraded to MISSING; a MISSING or HELD scope never carries 0: its
     quantity is a measured research figure with its evidence status, or None with a bound, and a candidate line of
     quantity 0 on a scope that is not NOT_APPLICABLE is refused (REFUSED_ZERO_FOR_HELD).
  5. A label's binding: BOUND (every scope BOUND or NOT_APPLICABLE), PARTIAL (some scope MISSING), MISSING (no scope
     bound), NOT_APPLICABLE (every scope NOT_APPLICABLE, with evidence).
"""

from __future__ import annotations

POLICY = "URBAN_LABEL_BINDING_T342"
RULE = "R-T342-BIND-1"
SCOPE_STATUS = ("BOUND", "NOT_APPLICABLE", "MISSING")
LABEL_BINDING = ("BOUND", "PARTIAL", "MISSING", "NOT_APPLICABLE", "DUPLICATE_OF", "MISSING_NO_FACE")


def _retype(label, word):
    if word is None:
        return label["code"], None
    code = word(label.get("text") or "")
    if isinstance(code, tuple):                     # engine room_word contract: (code, matched)
        code = code[0]
    if code and code != label["code"]:
        return code, f"RETYPED {label['code']} -> {code} (compound phrase read before the bare word)"
    return label["code"], None


def _face_of(tid, faces):
    hit = [f for f in faces if tid in (f.get("labels") or ())]
    return hit[0] if len(hit) == 1 else (None if not hit else "AMBIGUOUS")


CORR_TOL = 0.005      # relative: a face and an element of another drawing are one space only when area AND perimeter agree


def accepted_elements(face, tol=CORR_TOL):
    """-> (element ids the face is geometrically the same space as, refused [(element, reason)]). A correspondence
    across drawings is accepted only on measured geometry: face and element area agree within tol AND, when both are
    given, their perimeters too; a correspondence by name (no figures) is refused (CORR_NAME_ONLY)."""
    ok, bad = [], []
    for c in face.get("corresponds") or ():
        fa, ea = c.get("face_m2"), c.get("element_m2")
        if fa is None or ea is None or ea <= 0:
            bad.append((c["element"], "CORR_NAME_ONLY"))
            continue
        if abs(fa - ea) / ea > tol:
            bad.append((c["element"], f"CORR_AREA_DIFFERS {fa} vs {ea}"))
            continue
        fl, el = c.get("face_lm"), c.get("element_lm")
        if fl is not None and el is not None and abs(fl - el) / el > tol:
            bad.append((c["element"], f"CORR_PERIMETER_DIFFERS {fl} vs {el}"))
            continue
        ok.append(c["element"])
    return ok, bad


def _bind_scope(face, sc, lines, other_codes=()):
    src = set(face.get("source") or ()) | {face["face_id"]} | set(accepted_elements(face)[0])
    tids = set(face.get("labels") or ())
    codes = set(sc.get("item_codes") or ())
    bound, refused = [], []
    for ln in lines:
        if ln.get("item_code") in other_codes and ln.get("item_code") not in codes:
            continue                                 # another scope of the same face owns this trade
        lsrc = set(ln.get("source") or ())
        on_face = bool(lsrc & src)
        cites = bool(set(ln.get("cites") or ()) & tids)
        right_trade = ln.get("item_code") in codes
        if on_face and right_trade:
            if (ln.get("quantity") in (0, 0.0)) and sc["status"] != "NOT_APPLICABLE":
                refused.append((ln["line_id"], "REFUSED_ZERO_FOR_HELD"))
            else:
                bound.append(ln["line_id"])
        elif cites and right_trade and not on_face:
            refused.append((ln["line_id"], "REFUSED_NAME_ONLY"))
        elif on_face and not right_trade and codes and (ln.get("item_code") or "").split(".")[0] in \
                {c.split(".")[0] for c in codes}:
            refused.append((ln["line_id"], "REFUSED_WRONG_TRADE"))
        elif cites and not right_trade:
            refused.append((ln["line_id"], "REFUSED_WRONG_TRADE"))
    status = sc["status"]
    note = None
    if status == "BOUND" and not bound:
        status, note = "MISSING", "given BOUND but no line's own source covers the face: MISSING"
    if status in ("MISSING",) and sc.get("quantity") in (0, 0.0):
        raise ValueError(f"{face['face_id']} {sc['scope']}: a MISSING scope never carries 0")
    if status == "NOT_APPLICABLE" and not sc.get("evidence"):
        raise ValueError(f"{face['face_id']} {sc['scope']}: NOT_APPLICABLE needs drawing evidence")
    return {"face_id": face["face_id"], "scope": sc["scope"], "status": status, "lines": sorted(bound),
            "refused": sorted(refused), "quantity": sc.get("quantity"), "bound": sc.get("bound"),
            "unit": sc.get("unit"), "evidence_status": sc.get("evidence_status"), "evidence": sc.get("evidence"),
            "integration": sc.get("integration"), "note": note}


def bind(labels, faces, lines, scopes, word=None):
    rows, out_scopes, first_in_face = [], [], {}
    done = {}
    for lab in labels:
        tid = lab["text_id"]
        code, retype = _retype(lab, word)
        face = _face_of(tid, faces)
        row = {"text_id": tid, "floor": lab.get("floor"), "census_code": lab["code"], "code": code,
               "retype": retype, "census_status": lab.get("status"), "face_id": None, "binding": None,
               "lines": [], "scopes": [], "duplicate_of": None}
        if face is None or face == "AMBIGUOUS":
            row["binding"] = "MISSING_NO_FACE"
            rows.append(row)
            continue
        row["face_id"] = face["face_id"]
        if face["face_id"] in first_in_face:
            row["binding"], row["duplicate_of"] = "DUPLICATE_OF", first_in_face[face["face_id"]]
            row["lines"] = done[face["face_id"]]["lines"]
            row["scopes"] = done[face["face_id"]]["scopes"]
            rows.append(row)
            continue
        first_in_face[face["face_id"]] = tid
        row["elements"], row["elements_refused"] = accepted_elements(face)
        if face.get("code") and face["code"] != code:
            raise ValueError(f"{tid}: label code {code} differs from its face's physical code {face['code']}")
        fsc = scopes.get(face["face_id"], ())
        allc = {c for sc in fsc for c in sc.get("item_codes") or ()}
        sc_rows = [_bind_scope(face, sc, lines, allc) for sc in fsc]
        if not sc_rows:
            row["binding"] = "MISSING"
        else:
            st = [s["status"] for s in sc_rows]
            if all(s == "NOT_APPLICABLE" for s in st):
                row["binding"] = "NOT_APPLICABLE"
            elif all(s in ("BOUND", "NOT_APPLICABLE") for s in st):
                row["binding"] = "BOUND"
            elif any(s == "BOUND" for s in st):
                row["binding"] = "PARTIAL"
            else:
                row["binding"] = "MISSING"
        row["lines"] = sorted({x for s in sc_rows for x in s["lines"]})
        row["scopes"] = [s["scope"] + ":" + s["status"] for s in sc_rows]
        done[face["face_id"]] = {"lines": row["lines"], "scopes": row["scopes"]}
        out_scopes.extend(sc_rows)
        rows.append(row)
    from collections import Counter
    summary = {"policy": POLICY, "rule": RULE, "labels": len(rows),
               "by_binding": dict(Counter(r["binding"] for r in rows)),
               "retyped": [r["text_id"] for r in rows if r["retype"]],
               "scopes": dict(Counter(s["status"] for s in out_scopes)),
               "refused": sum(len(s["refused"]) for s in out_scopes)}
    return {"rows": rows, "scopes": out_scopes, "summary": summary}
