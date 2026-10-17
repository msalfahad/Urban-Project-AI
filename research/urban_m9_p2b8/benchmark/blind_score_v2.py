"""URBAN BLIND TEST SCORER V2 (protocol URBAN_BLIND_V2) - sealed before any second-villa drawing is run.

Scores a frozen ARCH_TAKEOFF_V2.7.1 / V2.7 run against an independent reference, per category and metric of
URBAN_BLIND_V2_PROTOCOL.json. Stdlib only; reads the published run files. It never changes a prediction, never
scores an UNSUPPORTED metric (it is reported UNSUPPORTED with the reference total, never as zero) and refuses a
reference that is not independent of the engine.

    python3 blind_score_v2.py seal   [--dir DIR]                       write SEAL.json (sha256 of the sealed files)
    python3 blind_score_v2.py commit --reference REF.json --salt S     the custodian's commitment record
    python3 blind_score_v2.py score  --reference REF.json --commitment C.json --salt S --run OUT [--out SCORE.json]

    verify_seal(dir)                  -> refusals ([] when the protocol, scorer and template are the sealed ones)
    check_reference(ref, protocol)    -> refusals of the reference itself
    commitment(path, salt, protocol)  -> the commitment record; check_commitment(...) -> refusals
    export_run(out_dir)               -> the prediction (rooms, lines, openings, doors, method, drawing)
    score(ref, pred, protocol)        -> per category / metric results (outcomes as URBAN_BLIND_V1 section 7)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOCOL = "URBAN_BLIND_V2"
SEALED = ("URBAN_BLIND_V2_PROTOCOL.json", "URBAN_BLIND_V2_PROTOCOL.md", "blind_score_v2.py", "REFERENCE_TEMPLATE.json")
DOOR_CLASS = {"DOOR.INTERNAL.PVC": "PVC", "DOOR.EXTERNAL.ALUMINIUM": "ALU", "DOOR.MAIN_ENTRANCE": "MAIN"}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_protocol(d=HERE):
    return json.loads((Path(d) / "URBAN_BLIND_V2_PROTOCOL.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------ seal and commitment
def seal(d=HERE):
    rec = {"protocol": PROTOCOL, "files": {n: _sha(Path(d) / n) for n in SEALED},
           "meaning": "the files of the protocol as sealed before any second-villa run; a change voids the round"}
    (Path(d) / "SEAL.json").write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return rec


def verify_seal(d=HERE):
    p = Path(d) / "SEAL.json"
    if not p.exists():
        return [{"code": "PROTOCOL_NOT_SEALED", "detail": "no SEAL.json"}]
    files = json.loads(p.read_text(encoding="utf-8")).get("files") or {}
    bad = [n for n in SEALED if files.get(n) != (_sha(Path(d) / n) if (Path(d) / n).exists() else None)]
    return [{"code": "PROTOCOL_NOT_SEALED", "detail": f"changed since the seal: {', '.join(bad)}"}] if bad else []


def protocol_sha(d=HERE):
    return _sha(Path(d) / "URBAN_BLIND_V2_PROTOCOL.json")


def commitment(ref_path, salt, d=HERE):
    ref = json.loads(Path(ref_path).read_text(encoding="utf-8"))
    return {"protocol": PROTOCOL, "protocol_sha256": protocol_sha(d),
            "reference_commitment": hashlib.sha256(salt.encode("utf-8") + Path(ref_path).read_bytes()).hexdigest(),
            "drawing_set": sorted(x["sha256"] for x in ref.get("drawing_set") or ())}


def check_commitment(ref_path, rec, salt, d=HERE):
    out = []
    if hashlib.sha256(salt.encode("utf-8") + Path(ref_path).read_bytes()).hexdigest() != rec.get("reference_commitment"):
        out.append({"code": "COMMITMENT_MISMATCH", "detail": "sha256(salt + reference) differs from the commitment"})
    if rec.get("protocol_sha256") != protocol_sha(d):
        out.append({"code": "COMMITMENT_MISMATCH", "detail": "the commitment names another protocol"})
    return out


# ------------------------------------------------------------------------------------------ the reference
def _strings(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield str(k)
            yield from _strings(v)
    elif isinstance(x, (list, tuple)):
        for v in x:
            yield from _strings(v)
    elif isinstance(x, str):
        yield x


def check_reference(ref, protocol, d=HERE):
    R = protocol["reference"]
    out = []
    if ref.get("schema") != R["schema"] or ref.get("protocol") != PROTOCOL:
        out.append({"code": "REFERENCE_SCHEMA", "detail": f"schema {ref.get('schema')}, protocol {ref.get('protocol')}"})
    if ref.get("protocol_sha256") != protocol_sha(d):
        out.append({"code": "REFERENCE_PROTOCOL_MISMATCH", "detail": "the reference was prepared for another protocol"})
    prep = ref.get("prepared") or {}
    if prep.get("method") not in R["allowed_methods"]:
        out.append({"code": "REFERENCE_METHOD_NOT_ALLOWED", "detail": str(prep.get("method"))})
    if prep.get("engine_outputs_consulted") is not False:
        out.append({"code": "REFERENCE_ENGINE_DERIVED", "detail": "engine_outputs_consulted is not false"})
    body = {k: v for k, v in ref.items() if k not in ("schema", "protocol", "protocol_sha256")}  # its own identity
    hits = sorted({m for s in _strings(body) for m in R["leakage_markers"] if re.search(m, s)})
    if hits:
        out.append({"code": "REFERENCE_LEAKAGE_MARKER", "detail": hits})
    return out


# ------------------------------------------------------------------------------------------ the prediction
def _load(d, name, default=None):
    p = Path(d) / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def export_run(out_dir):
    out_dir = Path(out_dir)
    rooms = _load(out_dir, "ARCH_ROOMS.json", {}) or {}
    run = rooms.get("run") or {}                      # every method's room file carries the run record
    man = _load(out_dir, "OUTPUT_MANIFEST.json", {}) or {}
    ds = _load(out_dir, "DOOR_SCHEDULE.json", {}) or {}
    recon = _load(out_dir, "DOOR_STANDARD_RECONCILIATION.json", {}) or {}
    rs = _load(out_dir, "REVIEW_SPACES.json", {}) or {}
    cond = defaultdict(set)
    for s in rs.get("spaces") or ():
        for entries in (s.get("conditional") or {}).values():
            for c in entries:
                if c.get("room_id") == s["room_id"]:
                    cond[s["room_id"]].add(c["item_code"])
    return {"method": man.get("method") or run.get("method"),
            "drawing_sha256": (run.get("drawing") or {}).get("sha256"),
            "rooms": rooms.get("rooms") or [],
            "lines": _load(out_dir, "BOQ_LINES.json", []) or [],
            "openings": (_load(out_dir, "ARCH_OPENINGS.json", {}) or {}).get("openings") or [],
            "door_elements": (ds.get("doors") or {}).get("elements") or [],
            "door_leaves": {d.get("opening_id"): d.get("door_leaf_m") for d in recon.get("doors") or ()},
            "conditional": {k: sorted(v) for k, v in cond.items()}}


def check_run(pred, ref, protocol):
    out = []
    if pred["method"] not in protocol["methods_frozen"]:
        out.append({"code": "RUN_METHOD_NOT_FROZEN", "detail": str(pred["method"])})
    if pred["drawing_sha256"] not in {x.get("sha256") for x in ref.get("drawing_set") or ()}:
        out.append({"code": "RUN_DRAWING_NOT_IN_SET", "detail": str(pred["drawing_sha256"])})
    return out


# ------------------------------------------------------------------------------------------ matching
def _inside(pt, poly):
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def _area(poly):
    return abs(sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))) / 2


def room_at(pred, floor, pt):
    hit = [r for r in pred["rooms"] if r.get("floor") == floor and len(r.get("polygon_m") or ()) >= 3 and
           _inside(pt, r["polygon_m"])]
    return min(hit, key=lambda r: _area(r["polygon_m"])) if hit else None


def _match_elements(pred, refs, kind, reach):
    """reference element ref_id -> engine opening (nearest of the floor within reach, each used once)."""
    pool = [o for o in pred["openings"] if o["kind"] == kind and (o.get("position") or {}).get("centre_m")]
    pairs = sorted(((math.dist(e["ref_xy_m"], o["position"]["centre_m"]), e["ref_id"], i)
                    for e in refs for i, o in enumerate(pool) if o["floor"] == e["floor"]), key=lambda x: x[0])
    used, out = set(), {}
    for dist, rid, i in pairs:
        if dist > reach or rid in out or i in used:
            continue
        out[rid] = pool[i]
        used.add(i)
    return out, [o for i, o in enumerate(pool) if i not in used]


# ------------------------------------------------------------------------------------------ engine values
def _state(protocol, ev):
    return protocol["status_of"].get(ev, "FLAGGED")


def _lines_at(pred, room_id, items):
    return [ln for ln in pred["lines"] if (ln.get("location") or {}).get("room_id") == room_id and
            ln["item_code"] in items]


def _from_lines(protocol, lines):
    """-> (outcome, value): RELEASED (sum of released values) / NOT_APPLICABLE / FLAGGED (value or None) / SILENT."""
    if not lines:
        return "SILENT", None
    rel = [ln for ln in lines if _state(protocol, ln["evidence_state"]) == "RELEASED" and
           ln.get("measured_net") is not None]
    if rel:
        return "RELEASED", sum(ln["measured_net"] for ln in rel)
    if all(_state(protocol, ln["evidence_state"]) == "NOT_APPLICABLE" for ln in lines):
        return "NOT_APPLICABLE", 0.0
    prov = [ln for ln in lines if _state(protocol, ln["evidence_state"]) == "PROVISIONAL" and
            ln.get("measured_net") is not None]
    if prov:
        return "PROVISIONAL", sum(ln["measured_net"] for ln in prov)
    return "FLAGGED", None


def engine_value(pred, protocol, met, level, ref_item, ctx):
    eng = met.get("engine") or {}
    src = eng.get("source")
    if level in ("ROOM", "STAIR"):
        rm = ctx["room"]
        if rm is None:
            return "SILENT", None
        if src == "ROOM":
            v = rm.get(eng["field"])
            return ("RELEASED", float(v or 0.0)) if v is not None else ("SILENT", None)
        if src == "TREADS":
            ls = _lines_at(pred, rm["room_id"], {"FIN.MARBLE.TREAD"})
            if not ls:
                return "SILENT", None
            n = sum(((ln.get("calculation") or {}).get("inputs") or {}).get("treads") or 0 for ln in ls)
            return "RELEASED", float(n)
        out = _from_lines(protocol, _lines_at(pred, rm["room_id"], set(eng["items"])))
        if out[0] == "SILENT" and set(eng["items"]) & set(pred["conditional"].get(rm["room_id"]) or ()):
            return "FLAGGED", None                     # a review space: conditional scenario quantities only
        return out
    if level == "FLOOR":
        fl = ref_item["floor"]
        if src == "OPENINGS":
            return "RELEASED", float(sum(1 for o in pred["openings"] if o["floor"] == fl))
        ls = [ln for ln in pred["lines"] if (ln.get("location") or {}).get("floor") == fl and
              ln["item_code"] in set(eng["items"])]
        if met["unit"] == "count":
            rel = [ln for ln in ls if _state(protocol, ln["evidence_state"]) == "RELEASED"]
            return ("RELEASED", float(len(rel))) if rel or not ls else ("PROVISIONAL", float(len(ls)))
        return _from_lines(protocol, ls)
    if level == "FLOOR_CLASS":
        fl, cls = ref_item["floor"], ref_item["class"]
        ls = [ln for ln in pred["lines"] if (ln.get("location") or {}).get("floor") == fl and
              DOOR_CLASS.get(ln["item_code"]) == cls]
        rel = [ln for ln in ls if _state(protocol, ln["evidence_state"]) == "RELEASED"]
        return "RELEASED", float(len(rel))
    if level in ("DOOR", "WINDOW"):
        o = ctx["opening"]
        if o is None:
            return "SILENT", None
        if src == "OPENING":
            return "RELEASED", float(o["width_m"])
        if src == "DOOR_LEAF":
            leaf = pred["door_leaves"].get(o["opening_id"])
            if leaf is None:
                el = next((e for e in pred["door_elements"] if e.get("opening_id") == o["opening_id"]), {})
                leaf = el.get("nominal_leaf_width_m")
            return ("RELEASED", float(sum(leaf))) if leaf else ("FLAGGED", None)
        if src == "DOOR_CLASS":
            el = next((e for e in pred["door_elements"] if e.get("opening_id") == o["opening_id"]), None)
            if el is None:
                return "SILENT", None
            cls = DOOR_CLASS.get(el.get("boq_class") or el.get("class"))
            return ("RELEASED", cls) if cls else ("FLAGGED", el.get("class"))
    return "SILENT", None


# ------------------------------------------------------------------------------------------ scoring
def _within(protocol, unit, eng, ref):
    if unit == "class":
        return eng == ref
    t = protocol["tolerances"][unit]
    return abs(eng - ref) <= max(t["abs"], t["rel"] * abs(ref)) + 1e-9


def _decimals(v):
    s = repr(float(v))
    return len(s.split(".")[1].rstrip("0")) if "." in s and "e" not in s else 0


def _ref_items(ref, level):
    if level == "ROOM":
        return ref.get("rooms") or []
    if level == "STAIR":
        return ref.get("stairs") or []
    if level == "DOOR":
        return ref.get("doors") or []
    if level == "WINDOW":
        return ref.get("windows") or []
    if level == "FLOOR":
        return [dict(f, ref_id=f.get("ref_id") or f["floor"]) for f in ref.get("floors") or ()]
    if level == "FLOOR_CLASS":
        return [{"ref_id": f"{f['floor']}:{c}", "floor": f["floor"], "class": c,
                 "quantities": {"DOOR_COUNT": n}}
                for f in ref.get("floors") or () for c, n in sorted(((f.get("quantities") or {})
                                                                      .get("DOOR_COUNT") or {}).items())]
    return []


def score(ref, pred, protocol):
    rooms_of = {}
    for lvl in ("ROOM", "STAIR"):
        for it in _ref_items(ref, lvl):
            rooms_of[(lvl, it["ref_id"])] = room_at(pred, it["floor"], it["ref_xy_m"])
    doors, extra_doors = _match_elements(pred, ref.get("doors") or [], "DOOR", protocol["matching"]["DOOR"]["reach_m"])
    wins, extra_wins = _match_elements(pred, ref.get("windows") or [], "WINDOW",
                                       protocol["matching"]["WINDOW"]["reach_m"])
    acc = protocol["acceptance"]
    digits = {"items": 0, "identical": 0}
    cats = []
    for cat in protocol["categories"]:
        mets = []
        for met in cat["metrics"]:
            level, name, unit = met["level"], met["metric"], met["unit"]
            items = [it for it in _ref_items(ref, level) if name in (it.get("quantities") or {})]
            if met["support"] == "UNSUPPORTED":
                vals = [it["quantities"][name] for it in items if isinstance(it["quantities"][name], (int, float))]
                mets.append({"metric": name, "unit": unit, "support": "UNSUPPORTED", "status": "UNSUPPORTED",
                             "reference_items": len(items), "reference_total": round(sum(vals), 6) if vals else None,
                             "why": met.get("note"), "never": "scored as zero"})
                continue
            rows = []
            merged = defaultdict(list)
            for it in items:
                ctx = {"room": rooms_of.get((level, it["ref_id"])),
                       "opening": doors.get(it["ref_id"]) if level == "DOOR" else wins.get(it["ref_id"])}
                if level in ("ROOM", "STAIR") and ctx["room"] is not None:
                    merged[ctx["room"]["room_id"]].append(it["ref_id"])
                outcome, ev = engine_value(pred, protocol, met, level, it, ctx)
                rv = it["quantities"][name]
                row = {"ref_id": it["ref_id"], "floor": it.get("floor"), "reference": rv, "engine": ev,
                       "outcome": outcome}
                if outcome == "RELEASED" and unit != "class":
                    row["error"] = round(ev - rv, 6)
                    row["within_tolerance"] = _within(protocol, unit, ev, rv)
                    if _decimals(rv) >= protocol["reference"]["digit_identity"]["min_decimals"]:
                        digits["items"] += 1
                        digits["identical"] += abs(ev - rv) <= 1e-9
                elif outcome == "RELEASED":
                    row["within_tolerance"] = _within(protocol, unit, ev, rv)
                elif outcome == "PROVISIONAL" and unit != "class":
                    row["provisional_error"] = round(ev - rv, 6)
                    row["provisional_within_tolerance"] = _within(protocol, unit, ev, rv)
                rows.append(row)
            # two reference rooms in one engine room: MERGED, scored once on their sum
            if level in ("ROOM", "STAIR") and unit != "class":
                for rid, refs in merged.items():
                    if len(refs) > 1:
                        grp = [r for r in rows if r["ref_id"] in refs]
                        for r in grp:
                            r["merged_with"] = sorted(refs)
                        if grp and grp[0]["outcome"] == "RELEASED":
                            tot = sum(r["reference"] for r in grp)
                            grp[0].update(reference_merged=tot, error=round(grp[0]["engine"] - tot, 6),
                                          within_tolerance=_within(protocol, unit, grp[0]["engine"], tot))
                            for r in grp[1:]:
                                r.update(outcome="MERGED", engine=None, error=None, within_tolerance=None)
            fp = []
            if level in ("ROOM",) and (met.get("engine") or {}).get("source") == "LINES":
                matched = {r["room_id"] for r in (rooms_of.get(("ROOM", it["ref_id"])) for it in items) if r}
                for ln in pred["lines"]:
                    rid = (ln.get("location") or {}).get("room_id")
                    if ln["item_code"] in set(met["engine"]["items"]) and rid not in matched and \
                            any(r["room_id"] == rid for r in pred["rooms"]) and \
                            _state(protocol, ln["evidence_state"]) == "RELEASED" and ln.get("measured_net"):
                        fp.append(ln["measured_net"])
            if level in ("DOOR", "WINDOW") and name in ("DOOR_OPENING_WIDTH", "WINDOW_WIDTH"):
                fp = [o["width_m"] for o in (extra_doors if level == "DOOR" else extra_wins)]
            mets.append(_aggregate(name, unit, met, rows, fp, acc))
        cats.append({"category": cat["category"], "metrics": mets})
    return {"protocol": PROTOCOL, "method": pred["method"], "categories": cats,
            "digit_identity": digits, "acceptance_status": acc["status"],
            "never": protocol["never"]}


def _aggregate(name, unit, met, rows, fp, acc):
    rel = [r for r in rows if r["outcome"] == "RELEASED"]
    out = {"metric": name, "unit": unit, "support": met["support"], "status": "SCORED", "modes": met["modes"],
           "reference_items": len(rows),
           "outcomes": {k: sum(r["outcome"] == k for r in rows)
                        for k in ("RELEASED", "PROVISIONAL", "FLAGGED", "SILENT", "NOT_APPLICABLE", "MERGED")},
           "within_tolerance": sum(bool(r.get("within_tolerance")) for r in rel),
           "rows": rows}
    if unit == "class":
        out["within_tolerance_share"] = round(out["within_tolerance"] / len(rel), 6) if rel else None
        return out
    tot = sum(r.get("reference_merged", r["reference"]) for r in rows if r["outcome"] != "MERGED")
    rtot = sum(r.get("reference_merged", r["reference"]) for r in rel)
    out.update(reference_total=round(tot, 6),
               coverage_qty=round(rtot / tot, 6) if tot else None,
               wape_released=round(sum(abs(r["error"]) for r in rel) / rtot, 6) if rtot else None,
               within_tolerance_share=round(out["within_tolerance"] / len(rel), 6) if rel else None,
               total_error_pct=round(100 * (sum(r["engine"] for r in rel) + sum(fp) - tot) / tot, 4) if tot else None,
               false_positive_items=len(fp), false_positive_qty=round(sum(fp), 6),
               fp_share=round(sum(fp) / tot, 6) if tot else None,
               provisional_values=sum(1 for r in rows if "provisional_error" in r),
               provisional_within_tolerance=sum(bool(r.get("provisional_within_tolerance")) for r in rows),
               coverage_qty_incl_provisional=round(sum(r.get("reference_merged", r["reference"]) for r in rows
                                                       if r["outcome"] in ("RELEASED", "PROVISIONAL")) / tot, 6)
               if tot else None)
    c = acc["per_metric"]
    ok = (out["coverage_qty"] or 0) >= c["coverage_qty_min"] and \
        (out["within_tolerance_share"] or 0) >= c["within_tolerance_share_min"] and \
        out["total_error_pct"] is not None and abs(out["total_error_pct"]) <= c["abs_total_error_pct_max"] and \
        out["outcomes"]["SILENT"] <= c["silent_omissions_max"] and (out["fp_share"] or 0) <= c["fp_share_max"]
    out["acceptance"] = ("PROPOSED_PASS" if ok else "PROPOSED_FAIL") if acc["status"].startswith("PROPOSED") else \
        ("PASS" if ok else "FAIL")
    return out


def run_score(ref_path, commit_path, salt, run_dir, d=HERE):
    protocol = load_protocol(d)
    ref = json.loads(Path(ref_path).read_text(encoding="utf-8"))
    refusals = verify_seal(d) + check_reference(ref, protocol, d)
    refusals += check_commitment(ref_path, json.loads(Path(commit_path).read_text(encoding="utf-8")), salt, d)
    pred = export_run(run_dir)
    refusals += check_run(pred, ref, protocol)
    if refusals:
        return {"protocol": PROTOCOL, "refused": refusals}
    rep = score(ref, pred, protocol)
    di, lim = rep["digit_identity"], protocol["reference"]["digit_identity"]
    if di["identical"] >= lim["min_items"] and di["identical"] >= lim["max_share"] * max(di["items"], 1):
        return {"protocol": PROTOCOL, "refused": [{"code": "REFERENCE_MATCHES_ENGINE_DIGITS", "detail": di}]}
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seal")
    s.add_argument("--dir", default=str(HERE))
    c = sub.add_parser("commit")
    c.add_argument("--reference", required=True)
    c.add_argument("--salt", required=True)
    c.add_argument("--dir", default=str(HERE))
    c.add_argument("--out")
    r = sub.add_parser("score")
    for k in ("--reference", "--commitment", "--salt", "--run"):
        r.add_argument(k, required=True)
    r.add_argument("--dir", default=str(HERE))
    r.add_argument("--out")
    a = ap.parse_args(argv)
    if a.cmd == "seal":
        print(json.dumps(seal(a.dir), indent=1, sort_keys=True))
        return 0
    if a.cmd == "commit":
        rec = commitment(a.reference, a.salt, a.dir)
        txt = json.dumps(rec, indent=1, sort_keys=True)
        if a.out:
            Path(a.out).write_text(txt + "\n", encoding="utf-8")
        print(txt)
        return 0
    rep = run_score(a.reference, a.commitment, a.salt, a.run, a.dir)
    txt = json.dumps(rep, indent=1, sort_keys=True, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(txt + "\n", encoding="utf-8")
    print(json.dumps(rep.get("refused") or [{"category": c["category"],
                                            "metrics": {m["metric"]: m.get("acceptance", m["status"])
                                                        for m in c["metrics"]}} for c in rep["categories"]],
                     sort_keys=True))
    return 2 if rep.get("refused") else 0


if __name__ == "__main__":
    sys.exit(main())
