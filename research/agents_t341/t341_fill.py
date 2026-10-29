"""T-341 CANONICAL-DEDUCTION FILL TABLE (research, read-only; imported by nothing in engine/). Every villa.

For every line the T-330 check (tools/t330_deductions_check.py, reused read-only) does not pass, it states WHICH
openings / elements the line's net already deducted, each by id, with its amount in the line's unit, so that

    gross_used - sum(deductions) + sum(additions) = measured_net      (tolerance 0.0005, boq_export_v1.QTY_MATCH_TOL)

It re-measures nothing and changes no line: the amounts come from the line's own fields (canonical list,
calculation.inputs) and, for skirting, from the merged per-opening ledger research/agents_t296 (T-296 MERGED 57c31ae4).
A net that no opening set explains stays a named residual (status UNEXPLAINED), never forced to fit.

Sources, per line, in this order:
  CANONICAL   an item of the line's 'deductions' list that already names an id
  SHADOW      calculation.inputs.<..>.deductions (owner-method list: opening + face + m2)
  LEDGER      an aggregate canonical item ('door / passage openings', 'glazing edge ...') split by opening id from a
              per-opening ledger (rows with listed=True and the same 'what'); a signed negative ledger row becomes an
              ADDITION (it restores length the aggregate over-deducts), never a negative deduction
  UNLISTED    ledger rows with listed=False (the F-17 threshold halves): deducted from the net but not listed
  ELEMENT     a canonical item with no id and no ledger: named by the line's element + the item's own text
  FLOOR_SCOPE a floor-scope record in calculation.inputs (part moved to another line, split-out landing, pieces)
Statuses: RECONCILED (sum closes, every row has an id), RECONCILED_GROSS_RESTATED (closes only from the face gross
that the line's own inputs state, not the 'gross' field: the field must be restated), UNEXPLAINED (residual named),
REFUSED (a row listed twice, a row in another unit, a negative row).

    python3 -I research/agents_t341/t341_fill.py --lines V3_0_22_BOQ_LINES.json --ledger <T-296 csv> --out DIR
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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import t330_deductions_check as C   # noqa: E402  (read only)

DEFAULT_GUARD_CLASS = "TOOLING"
TOL = C.TOL
DEC = 6
UNIT_KEYS = ("m2", "lm", "m3", "m", "kg", "nr")
FILL_COLUMNS = ("line_id", "item_code", "floor", "element_id", "unit", "role", "opening_id", "census_id", "face",
                "amount", "source", "note")
LINE_COLUMNS = ("line_id", "item_code", "floor", "element_id", "unit", "t330_issues", "status", "gross_field",
                "gross_used", "measured_net", "deductions_sum", "additions_sum", "residual", "rows", "cause")


class FillError(ValueError):
    pass


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _amount(d, unit):
    """(amount, stated unit) of one deduction dict; unit keys state their unit."""
    for k in C.QTY_KEYS:
        if _num(d.get(k)):
            return float(d[k]), d.get("unit") or unit
    for k in UNIT_KEYS:
        if _num(d.get(k)):
            return float(d[k]), k
    return None, None


def _id(d):
    return next((str(d[k]) for k in C.ID_KEYS if d.get(k) not in (None, "")), None)


def load_ledger(path):
    """T-296 per-opening ledger csv -> {line_id: [rows]} (length_m float, listed bool)."""
    out = defaultdict(list)
    if not path:
        return out
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            r = dict(r)
            r["length_m"] = float(r["length_m"])
            r["listed"] = r["listed"].strip() == "True"
            out[r["line_id"]].append(r)
    return out


def _shadow_lists(ln):
    found = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "deductions" and isinstance(v, list) and v:
                    found.append((path + "." + k, v))
                else:
                    walk(v, path + "." + k)
    walk((ln.get("calculation") or {}).get("inputs") or {}, "calculation.inputs")
    return found


def _row(ln, role, oid, amount, source, unit=None, census="", face="", note=""):
    loc = ln.get("location") or {}
    return {"line_id": ln["line_id"], "item_code": ln.get("item_code"), "floor": loc.get("floor"),
            "element_id": loc.get("element_id"), "unit": unit or ln.get("unit"), "role": role, "opening_id": oid,
            "census_id": census, "face": face, "amount": round(float(amount), DEC), "source": source, "note": note}


def _from_ledger(ln, item, what, ledger_rows):
    """split one aggregate canonical item by opening id; None when the ledger does not close it."""
    rows = [r for r in ledger_rows if r["listed"] and r["listed_as"] == what]
    if not rows:
        return None
    total, _u = _amount(item, ln["unit"])
    if abs(sum(r["length_m"] for r in rows) - total) > TOL:
        return None
    out = []
    for r in rows:
        oid = r["opening_id"] or f"{r['kind']}:{ln['location'].get('element_id')}"
        role = "ADDITION" if r["length_m"] < 0 else "DEDUCTION"
        note = r.get("cause", "") or ""
        if role == "ADDITION":
            note = ("signed ledger row kept as an addition (" + note + "): the aggregate deducts the whole band "
                    "passage, the boundary carries less")
        out.append(_row(ln, role, oid, abs(r["length_m"]), f"LEDGER {what}", census=r.get("census_id", ""),
                        note=note))
    return out


def _floor_scope(ln):
    """FLOOR_SCOPE rows + the face gross the line's own inputs state, or (rows, None)."""
    fs = ((ln.get("calculation") or {}).get("inputs") or {}).get("floor_scope_v3014") or {}
    rows = []
    if fs.get("kind") == "TO_WET" and _num(fs.get("area_m2")):
        rows.append(_row(ln, "DEDUCTION", fs.get("record") or "FLOOR_SCOPE_PART", fs["area_m2"],
                         "FLOOR_SCOPE moved to the wet floor line (calculation.inputs.floor_scope_v3014)",
                         note=str(fs.get("area_basis", ""))[:160]))
    so = fs.get("split_out") or {}
    if _num(so.get("area_m2")):
        rows.append(_row(ln, "DEDUCTION", f"{fs.get('record', 'FLOOR_SCOPE')}:{so.get('part', 'split')}",
                         so["area_m2"], "FLOOR_SCOPE split_out (calculation.inputs.floor_scope_v3014)",
                         note=str(so.get("decision", ""))[:160]))
    for p in fs.get("pieces") or []:
        if p.get("to") == "NOT_FLOOR" and _num(p.get("area_m2")):
            rows.append(_row(ln, "DEDUCTION", p.get("piece"), p["area_m2"], "FLOOR_SCOPE piece NOT_FLOOR",
                             note=str(p.get("why", ""))[:160]))
    return rows


def fill_line(ln, ledger_rows=(), face_gross=None):
    """-> (line record, fill rows). face_gross: the room face area another line of the same element states
    (the ceiling line of the same engine face), used only to corroborate / restate a porcelain gross."""
    unit, gross, net = ln.get("unit"), ln.get("gross"), ln.get("measured_net")
    res = C.check_line(ln)
    rows, cause = [], []
    canon = ln.get("deductions") or []
    for d in canon:
        what = d.get("what", "") if isinstance(d, dict) else ""
        i = _id(d) if isinstance(d, dict) else None
        q, u = _amount(d, unit) if isinstance(d, dict) else (float(d), unit)
        if i:
            rows.append(_row(ln, "DEDUCTION", i, q, "CANONICAL", unit=u, face=d.get("face", ""), note=what[:160]))
            continue
        split = _from_ledger(ln, d, what, ledger_rows) if ledger_rows else None
        if split is not None:
            rows += split
            continue
        faces = (((ln.get("calculation") or {}).get("inputs") or {}).get("base_ownership_v3021") or {}).get(
            "on_tiled_faces") or []
        if what.startswith("ARCH_TAKEOFF_V3.0.21") and faces and abs(sum(f["qty"] for f in faces) - q) <= TOL:
            for f in faces:
                rows.append(_row(ln, "DEDUCTION", f"{f['face_id']}#{f['entity']}", f["qty"],
                                 "CANONICAL split by calculation.inputs.base_ownership_v3021.on_tiled_faces",
                                 face=f["face_id"], note=f.get("role", "")))
            continue
        rows.append(_row(ln, "DEDUCTION", f"{ln['location'].get('element_id')}:{what.split(' (')[0][:60]}", q,
                         "ELEMENT (no opening ledger)", unit=u, note=what[:160]))
        cause.append("an aggregate deduction named by element, not split by opening id")
    if not canon:
        sh = _shadow_lists(ln)
        if sh:
            path, items = sh[0]
            for d in items:
                q, u = _amount(d, unit)
                op = d.get("opening") or _id(d) or ""
                rows.append(_row(ln, "DEDUCTION", op, q if q is not None else float("nan"), f"SHADOW {path}",
                                 unit=u, face=d.get("face", ""), note=str(d.get("basis", ""))[:160]))
    for r in ledger_rows:
        if not r["listed"]:
            rows.append(_row(ln, "DEDUCTION", r["opening_id"], r["length_m"], "UNLISTED (T-296 ledger)",
                             census=r.get("census_id", ""), note=(r.get("cause") or "") +
                             "; held whole in the room's BOUNDED_EXPOSURE range line"))
    rows += _floor_scope(ln)

    # checks
    status, refused = None, []
    keys = Counter((r["opening_id"], r["face"], r["role"]) for r in rows)
    dup = sorted(k for k, n in keys.items() if n > 1)
    if dup:
        refused.append(f"listed twice: {dup}")
    if any(r["unit"] != unit for r in rows):
        refused.append("a row in another unit: " + ", ".join(sorted({r['unit'] for r in rows if r['unit'] != unit})))
    if any(not (r["amount"] >= 0) for r in rows):
        refused.append("a negative / non-numeric row")
    if any(not r["opening_id"] for r in rows):
        refused.append("a row with no id")
    dsum = sum(r["amount"] for r in rows if r["role"] == "DEDUCTION" and r["amount"] == r["amount"])
    asum = sum(r["amount"] for r in rows if r["role"] == "ADDITION")
    gross_used = gross
    fs_rows = [r for r in rows if r["source"].startswith("FLOOR_SCOPE")]
    if fs_rows and _num(net) and _num(gross) and abs(gross - net) <= TOL:
        gross_used = None                      # the gross field was written equal to the net: restate from the face
        if face_gross is not None:
            gross_used = face_gross
            cause.append(f"gross field {gross:.6f} = net; face area {face_gross:.6f} from the same engine face's "
                         "ceiling line")
    residual = None if not (_num(gross_used) and _num(net)) else gross_used - dsum + asum - net
    if refused:
        status = "REFUSED"
        cause += refused
    elif residual is None:
        status = "UNEXPLAINED"
        cause.append("no face gross stated: the gross field equals the net while deductions are listed")
    elif abs(residual) > TOL:
        status = "UNEXPLAINED"
        cause.append(f"residual {residual:.6f} {unit}: no listed opening / element explains it")
    elif gross_used != gross:
        status = "RECONCILED_GROSS_RESTATED"
    else:
        status = "RECONCILED" if not any(r["source"].startswith("ELEMENT") for r in rows) else "RECONCILED_BY_ELEMENT"
    loc = ln.get("location") or {}
    rec = {"line_id": ln["line_id"], "item_code": ln.get("item_code"), "floor": loc.get("floor"),
           "element_id": loc.get("element_id"), "unit": unit, "t330_issues": res.get("issues", ""), "status": status,
           "gross_field": gross, "gross_used": None if gross_used is None else round(gross_used, DEC),
           "measured_net": net, "deductions_sum": round(dsum, DEC), "additions_sum": round(asum, DEC),
           "residual": None if residual is None else round(residual, DEC), "rows": len(rows),
           "cause": "; ".join(cause)}
    return rec, rows


def apply_fill(lines, records, rows):
    """what T-246 does with the table, on COPIES: each RECONCILED* line gets the canonical list (id + 'qty' the export
    reads + unit + face + source) and its additions; a restated gross replaces the gross field. UNEXPLAINED / REFUSED
    lines are left as they are. Returns new lines; the input is not modified."""
    by = defaultdict(list)
    for r in rows:
        by[r["line_id"]].append(r)
    ok = {r["line_id"]: r for r in records if r["status"].startswith("RECONCILED")}
    out = []
    for ln in lines:
        if ln["line_id"] not in ok:
            out.append(ln)
            continue
        n = json.loads(json.dumps(ln))
        rr = by[ln["line_id"]]
        mk = lambda r: {"id": r["opening_id"], "qty": r["amount"], "unit": r["unit"], "face": r["face"],
                        "source": r["source"], "what": r["note"]}
        n["deductions"] = [mk(r) for r in rr if r["role"] == "DEDUCTION"]
        n["additions"] = [mk(r) for r in rr if r["role"] == "ADDITION"]
        if ok[ln["line_id"]]["gross_used"] is not None:
            n["gross"] = ok[ln["line_id"]]["gross_used"]
        out.append(n)
    return out


def _face_gross_index(lines):
    """engine face -> the ceiling line gross of that face (same polygon); used only to restate a floor gross."""
    idx = {}
    for ln in lines:
        eid = (ln.get("location") or {}).get("element_id") or ""
        if ln.get("item_code", "").startswith("FIN.CEILING") and eid.endswith(":ceiling") and _num(ln.get("gross")):
            idx[eid.rsplit(":", 1)[0]] = float(ln["gross"])
    return idx


def build(lines, ledger):
    rep = C.check_lines(lines)
    flagged = {f["line_id"] for f in rep["findings"]}
    face = _face_gross_index(lines)
    recs, rows = [], []
    for ln in lines:
        if ln["line_id"] not in flagged:
            continue
        eid = ((ln.get("location") or {}).get("element_id") or "").rsplit(":", 1)[0]
        rec, rr = fill_line(ln, ledger.get(ln["line_id"], []), face.get(eid))
        recs.append(rec)
        rows += rr
    return rep, recs, rows


def _csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.{DEC}f}" if isinstance(r[k], float) else r[k]))
                    for k in cols})
    return buf.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", required=True)
    ap.add_argument("--ledger")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    raw = Path(a.lines).read_bytes()
    lines = json.loads(raw)
    lines = lines if isinstance(lines, list) else lines["lines"]
    rep, recs, rows = build(lines, load_ledger(a.ledger))
    after = C.check_lines(apply_fill(lines, recs, rows))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "FILL_TABLE_T341.csv").write_text(_csv(rows, FILL_COLUMNS), encoding="utf-8")
    (out / "FILL_LINES_T341.csv").write_text(_csv(recs, LINE_COLUMNS), encoding="utf-8")
    fam = defaultdict(lambda: Counter())
    for r in recs:
        fam[f"{r['item_code']} ({r['unit']})"][r["status"]] += 1
    summ = {"task": "T-341", "lines_sha256_8": hashlib.sha256(raw).hexdigest()[:8], "lines": len(lines),
            "t330_before": {"flagged": rep["flagged"], "refused": rep["refused"]},
            "fill_lines": len(recs), "fill_rows": len(rows),
            "status": dict(Counter(r["status"] for r in recs)),
            "by_family": {k: dict(v) for k, v in sorted(fam.items())},
            "t330_after_fill_applied_in_memory": {"flagged": after["flagged"], "refused": after["refused"],
                                                  "remaining": sorted(f["line_id"] for f in after["findings"])}}
    (out / "summary.json").write_text(json.dumps(summ, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps(summ, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
