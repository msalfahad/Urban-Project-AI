"""T-474 part 1 on the development villa: the formwork PIECE CENSUS and the LINE MAP of every candidate STR.FORMWORK /
STR.FORMWORK.STAIR line, built ONLY from Checker-merged files pinned by sha256 (an edited file stops the build):

  research/agents_t332/FORMWORK_T332_BY_FACE.csv + T199_FILL_T332.csv + CANDIDATE_V3021_CONCRETE_LINES.json (T-332 r2,
      MERGED 61d5597e): every formwork face (r5 = T-163 r3 + T-264 r4 + T-293 + T-308), its element class, contact,
      status and the concrete line it is bound to;
  research/agents_t352/STAIR_FORMWORK_T352_BY_FACE.csv (T-352, MERGED b12e10de): the stair side faces;
  research/agents_t199/t199_inputs.py (T-199 Gate B, MERGED e29f3724): the V3.0.30 formwork line set (element ids and
      line ids are deterministic: boq_line.line_id(project, item, element id, R-T199-1, T-199, m2));
  research/agents_t469/VERDICT_V2_SET_V3_0_40_SNAPSHOT.json (T-469, MERGED): the Checker VERIFIED records
      (V2-0c71eb8f0ae7dae0 suspended slabs 60.280 m3, 75 lines; V2-66ef133c13150687 ring ground beam BAND0043).

Optional --lines <V3_0_43_BOQ_LINES.json of a run>: the live state and m2 of each formwork line on the candidate of
record (lines changed since V3.0.30 by V3.0.33 DEPENDENT_HELD are named). Outputs carry line ids, face ids, item
codes, states and m2 only (no coordinates, no names):

    python3 -I research/agents_t474/t474_alsenan.py [--lines V3_0_43_BOQ_LINES.json] [--out DIR]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t199", Path(__file__).resolve().parent):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t199_inputs as T199                       # noqa: E402
import t474_rules as R                           # noqa: E402
from engine.source import boq_line as BL         # noqa: E402

PROJECT = "development-villa-t131"
FACE = ROOT / "research/agents_t332/FORMWORK_T332_BY_FACE.csv"
SFACE = ROOT / "research/agents_t352/STAIR_FORMWORK_T352_BY_FACE.csv"
CONC = ROOT / "research/agents_t332/CANDIDATE_V3021_CONCRETE_LINES.json"
VERD = ROOT / "research/agents_t469/VERDICT_V2_SET_V3_0_40_SNAPSHOT.json"
PINS = {FACE: T199.PINS[T199.FACE], SFACE: T199.PINS[T199.SFACE], CONC: T199.PINS[T199.CONC],
        VERD: "96f73f4c2a441906d1527aed6c6f46741082cda8b2c3d80482d2e9f11619e1ac"}
FW_CODE, FW_STAIR = "STR.FORMWORK", "STR.FORMWORK.STAIR"
RULE_ID, RULE_VERSION = "R-T199-1", "T-199"
VALUED = ("SOURCE_DERIVED", "PROVISIONAL", "MEASURED")
CLASS_OF_ITEM = {"STR.CONC.BEAM": "BEAM", "STR.CONC.SLAB": "SLAB", "STR.CONC.COLUMN": "COLUMN",
                 "STR.CONC.GROUND_BEAM": "GROUND_BEAM", "STR.CONC.FOOTING": "FOOTING", "STR.CONC.STAIR": "STAIR",
                 "STR.CONC.STRAP": "STRAP", "STR.CONC.POOL": "POOL", "STR.CONC.DOME": "DOME",
                 "STR.CONC.BOUNDARY_WALL": "BOUNDARY"}


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _pinned(p):
    h = _sha(p)
    if PINS[p] != "PINNED_AT_BUILD" and h != PINS[p]:
        raise T199.PinError(f"{p.name}: sha256 {h[:12]} is not the merged {PINS[p][:12]}")
    return h


def verified_records():
    _pinned(VERD)
    out = {}
    for v in json.loads(VERD.read_text())["verdicts"]:
        for lid in v["line_ids"]:
            out[lid] = {"verdict_id": v["verdict_id"], "unit": v["unit"], "scope": v["scope"]}
    return out


def fw_line_id(code, eid):
    return BL.line_id(PROJECT, code, eid, RULE_ID, RULE_VERSION, "m2")


def build(lines=None):
    for p in (FACE, SFACE, CONC):
        _pinned(p)
    doc = T199.build(PROJECT)
    faces = {r["face_id"]: r for r in csv.DictReader(FACE.read_text().splitlines())}
    sfaces = {r["face_id"]: r for r in csv.DictReader(SFACE.read_text().splitlines())}
    conc = {c["line_id"]: c for c in json.loads(CONC.read_text())["lines"]}
    ver = verified_records()

    def cls_of(fid):
        if fid in sfaces:
            return "STAIR", sfaces[fid]["kind"]
        f = faces[fid]
        return f["element"], f["face_kind"]

    def code_of(item):
        return FW_STAIR if item == "STR.CONC.STAIR" else FW_CODE

    rows = []

    def add(eid, code, kind, cl, ids, m2, status, bounds=None, note=""):
        c = conc.get(cl) if cl else None
        cls = Counter(cls_of(f) for f in ids)
        basis = ""
        if status == "CALCULATED":
            v = ver.get(cl)
            slab_ok = (c is not None and c["item_code"] == "STR.CONC.SLAB" and v is not None and
                       all(cls_of(f) == ("SLAB", "SLAB") for f in ids) and
                       abs(((c.get("dimensions") or {}).get("area_m2") or -1) - (m2 or 0)) <= R.TOL_GEOM)
            res = (m2 or 0) - ((c.get("dimensions") or {}).get("area_m2") or 0) if slab_ok else 0.0
            basis = (f"VERIFIED_GEOMETRY {v['verdict_id']} (soffit = verified net panel area"
                     + (f"; ledger rounding residual {res:+.4f} m2" if abs(res) > R.TOL else "") + ")" if slab_ok else
                     f"CALCULATED on a VERIFIED concrete line {v['verdict_id']} (face geometry not in the verdict)"
                     if v else f"CALCULATED ({c['evidence_state'] if c else '-'})")
        elif status == "NOT_APPLICABLE":
            basis = "NOT_APPLICABLE (evidence on the line)"
        else:
            reason = (f"concrete line {c['evidence_state']}" if c and c["evidence_state"] not in VALUED else
                      f"faces {status}")
            basis = f"HELD: {reason}" + (f"; {note}" if note else "")
        rows.append({"line_id": fw_line_id(code, eid), "item_code": code, "element_id": eid, "line_kind": kind,
                     "concrete_line": cl or "", "concrete_item": c["item_code"] if c else "",
                     "concrete_state_v3021": c["evidence_state"] if c else "",
                     "concrete_verdict": (ver.get(cl) or {}).get("verdict_id", "") if cl else "",
                     "classes": " ".join(f"{a}/{b}:{n}" for (a, b), n in sorted(cls.items())),
                     "faces": len(ids), "face_ids": " ".join(ids), "status_v3030": status,
                     "m2_v3030": "" if m2 is None else f"{m2:.6f}",
                     "bounds": json.dumps(bounds, sort_keys=True) if bounds else "", "basis": basis})

    for r in doc["formwork"]:
        b = {k: r[k] for k in ("lo", "hi", "held_from") if r.get(k) is not None}
        eid = f"FW:{r['line_id']}:FACES:{r['status']}:{r['alternative'] or '-'}:{r['method'] or 'G'}"
        add(eid, code_of(r["item_code"]), "FACES", r["line_id"], r["face_ids"], r["m2"] if r["status"] ==
            "CALCULATED" else None, r["status"], b)
    for a in doc["alternatives"]:
        ids = sorted(sum((x["face_ids"] for x in a["alternatives"].values()), []))
        fm = (a["alternatives"].get("OQ10_FORMED") or {}).get("m2")
        add(f"FW:{a['line_id']}:OQ10:{a['method']}", code_of(a["item_code"]), "OQ10", a["line_id"], ids, None,
            "ALTERNATIVE", {"OQ10_FORMED": fm, "OQ10_EARTH_CAST": (a["alternatives"].get("OQ10_EARTH_CAST") or {})
                            .get("m2")}, "OQ-10 FORMED / EARTH_CAST open (owner)")
    for r in doc["not_applicable"]:
        add(f"FW:{r['line_id']}:FACES:NOT_APPLICABLE:-:{r['method'] or 'G'}", code_of(r["item_code"]), "NA",
            r["line_id"], r["face_ids"], None, "NOT_APPLICABLE")
    for r in doc["stair_sides"]:
        b = {k: r[k] for k in ("lo", "hi") if r.get(k) is not None}
        add(f"FW:{r['line_id']}:SIDE:{r['status']}:-:G", FW_STAIR, "STAIR_SIDE", r["line_id"], r["face_ids"],
            r["m2"] if r["status"] == "CALCULATED" else None, r["status"], b)
    for u in doc["untied"]:
        b = {k: u[k] for k in ("lo", "hi", "held_from") if u.get(k) is not None}
        add(f"FW:FACE:{u['face_id']}", FW_STAIR if u["element"] == "STAIR" else FW_CODE, "UNTIED", None,
            [u["face_id"]], None, "HELD", b, f"{u['tie']}: {u['reason']}"[:160])

    live = {}
    if lines is not None:
        by = {ln["line_id"]: ln for ln in lines}
        cand_fw = {ln["line_id"] for ln in lines if ln["item_code"] in (FW_CODE, FW_STAIR)}
        mine = {r["line_id"] for r in rows}
        if cand_fw != mine:
            raise ValueError(f"line map: {len(cand_fw - mine)} candidate formwork lines not mapped, "
                             f"{len(mine - cand_fw)} mapped ids not in the candidate")
        for r in rows:
            ln = by[r["line_id"]]
            r["state_live"] = ln["evidence_state"]
            r["m2_live"] = "" if ln.get("measured_net") is None else f"{ln['measured_net']:.6f}"
            cl = by.get(r["concrete_line"]) if r["concrete_line"] else None
            r["concrete_state_live"] = cl["evidence_state"] if cl else ""
            if r["status_v3030"] == "CALCULATED" and ln["evidence_state"] not in VALUED:
                r["basis"] = f"HELD: DEPENDENT_HELD (concrete line now {r['concrete_state_live']}); was {r['basis']}"
            live[r["line_id"]] = ln["evidence_state"]
            if cl is not None:
                b = conc[r["concrete_line"]]
                q0, q1 = b.get("measured_net"), cl.get("measured_net")
                moved_q = (q0 is None) != (q1 is None) or (q0 is not None and abs(q0 - q1) > R.TOL)
                if moved_q or b["evidence_state"] != cl["evidence_state"]:
                    r["binding_drift"] = (f"{b['evidence_state']} {q0} -> {cl['evidence_state']} {q1}"
                                          if moved_q else f"{b['evidence_state']} -> {cl['evidence_state']}")
                    if r["m2_live"]:
                        r["basis"] += "; STALE BINDING: concrete line restated since the face ledger (re-derive)"
    summ = summarize(rows, faces, sfaces, conc, ver, lines is not None)
    if lines is not None:
        dr = [r for r in rows if r.get("binding_drift")]
        summ["binding_drift"] = {
            "formwork_lines": len(dr),
            "valued_on_restated_concrete": sorted([r["line_id"], r["concrete_line"], r["m2_live"], r["binding_drift"]]
                                                  for r in dr if r["m2_live"]),
            "dependent_held": sorted([r["line_id"], r["concrete_line"], r["m2_v3030"], r["concrete_state_live"]]
                                     for r in rows if r["status_v3030"] == "CALCULATED" and not r["m2_live"]),
            "dependent_held_m2": round(sum(float(r["m2_v3030"]) for r in rows
                                           if r["status_v3030"] == "CALCULATED" and not r["m2_live"]), 6)}
        for r in rows:
            r.setdefault("binding_drift", "")
    return rows, summ


def summarize(rows, faces, sfaces, conc, ver, have_live):
    def val(r):
        if have_live:
            return float(r["m2_live"]) if r.get("m2_live") else None
        return float(r["m2_v3030"]) if r["m2_v3030"] else None
    s = {"schema": "T474_FORMWORK_LINE_MAP_V1", "project": PROJECT, "lines": len(rows),
         "by_code": {}, "by_basis": {}, "by_class_valued_m2": {}, "live_state": "V3.0.43 run" if have_live else
         "V3.0.30 (no --lines)"}
    for r in rows:
        k = r["item_code"]
        d = s["by_code"].setdefault(k, {"lines": 0, "valued": 0, "valued_m2": 0.0, "blank": 0})
        d["lines"] += 1
        v = val(r)
        if v is None:
            d["blank"] += 1
        else:
            d["valued"] += 1
            d["valued_m2"] = round(d["valued_m2"] + v, 6)
        bk = r["basis"].split(" ")[0].rstrip(":")
        e = s["by_basis"].setdefault(bk, {"lines": 0, "m2": 0.0})
        e["lines"] += 1
        if v is not None:
            e["m2"] = round(e["m2"] + v, 6)
            for c in r["classes"].split():
                cl = c.split(":")[0]
                # a line's faces share one class in the ledger except mixed beam lines; attribute by face m2
            ids = r["face_ids"].split()
            tot = 0.0
            for f in ids:
                if f in faces and faces[f]["m2"]:
                    tot += float(faces[f]["m2"])
                elif f in sfaces and sfaces[f]["m2"]:
                    tot += float(sfaces[f]["m2"])
            for f in ids:
                fm = float(faces[f]["m2"]) if f in faces and faces[f]["m2"] else (
                    float(sfaces[f]["m2"]) if f in sfaces and sfaces[f]["m2"] else 0.0)
                key = "/".join((faces[f]["element"], faces[f]["face_kind"])) if f in faces else \
                    f"STAIR/{sfaces[f]['kind']}"
                share = v * fm / tot if tot else 0.0
                s["by_class_valued_m2"][key] = round(s["by_class_valued_m2"].get(key, 0.0) + share, 6)
    s["by_class_valued_m2"] = dict(sorted(s["by_class_valued_m2"].items()))
    s["by_basis"] = dict(sorted(s["by_basis"].items()))
    return s


def class_census(faces, sfaces):
    """piece census per element class / face kind from the face ledgers (every face, every status)."""
    c = {}
    for r in list(faces.values()):
        k = (r["element"], r["face_kind"])
        R.PIECE_CLASSES[r["element"]][r["face_kind"]]       # R-T474-1: an unknown face kind stops the build
        d = c.setdefault(k, Counter())
        d[r["status"]] += 1
        if r["status"] == "CALCULATED" and r["method"] in ("G", "E=G") and r["m2"]:
            d["calc_m2_G"] = round(d.get("calc_m2_G", 0) + float(r["m2"]), 6)
    for r in sfaces.values():
        R.PIECE_CLASSES["STAIR"][r["kind"]]
        d = c.setdefault(("STAIR", r["kind"]), Counter())
        d[r["status"]] += 1
        if r["status"] == "CALCULATED" and r["m2"]:
            d["calc_m2_G"] = round(d.get("calc_m2_G", 0) + float(r["m2"]), 6)
    return {f"{a}/{b}": dict(v) for (a, b), v in sorted(c.items())}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    lines = None
    if a.lines:
        lines = json.loads(Path(a.lines).read_text())
        lines = lines["lines"] if isinstance(lines, dict) else lines
    rows, summ = build(lines)
    faces = {r["face_id"]: r for r in csv.DictReader(FACE.read_text().splitlines())}
    sfaces = {r["face_id"]: r for r in csv.DictReader(SFACE.read_text().splitlines())}
    summ["class_census"] = class_census(faces, sfaces)
    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        cols = list(rows[0].keys())
        with open(out / "FORMWORK_LINE_MAP_T474.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            for r in sorted(rows, key=lambda x: (x["item_code"], x["line_id"])):
                w.writerow(r)
        (out / "summary_t474.json").write_text(json.dumps(summ, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: summ[k] for k in ("lines", "by_code", "by_basis", "live_state")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
