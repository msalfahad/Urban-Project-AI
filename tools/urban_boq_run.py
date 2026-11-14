"""URBAN BOQ RUN (T-772 skeleton) - ONE manifest-driven command: drawings + approved rules + the project inputs sheet
-> BOQ workbook(s) + an exceptions list. A read-only orchestrator, NOT a method version: it computes no quantity of
its own and changes no engine line. General: no project name, item code or element id is written in this module.

    python3 -I tools/urban_boq_run.py --manifest RUN_MANIFEST.json --out OUT_DIR

Stages (each one an existing engine part, reused unchanged):
  1. manifest check: drawings by role (plan required, structural optional), rule set, project files; every missing
     input becomes an EXCEPTION, never a default and never a 0;
  2. geometry: tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V2.13 (+ route G on the structural drawing): the
     drawing-derived base every candidate starts from; the history replay (the arch_v30xx chain) stays under its own
     entry point and is not called here;
  3. data objects (ACCURACY_PLAN A-E: inputs sheet, opening table, room table, wall band, schedule tables): called
     only when present AND a reader is registered in PLUGINS; a present object without a reader is an exception
     (PRESENT_NOT_WIRED), an absent one is an exception (ABSENT); neither changes a line;
  4. export: tools/boq_export_v1.py once per drawing identity (one BOQ = one project id + one revision set); a quantity
     line the exporter refuses as "a zero with no producing input" is exported HELD (BLOCKED_RFI, blank quantity) on
     the export copy only and named in the exceptions list (HELD is never 0);
  5. reach (optional, manifest "compare"): every line of a committed candidate index (LINE_INDEX_V3_0_x.json) is
     classed GEOMETRY_DIRECT / GEOMETRY_RESTATED / FILL_RESTATED / OVERLAY_ONLY / FILL_ONLY against this run, counted
     per BOQ family of the family master; the lines the geometry run does not reach, grouped by (item code, element
     group), are the GENERALISE backlog.

Outputs in OUT_DIR: geometry/ (the m9 run), export/<identity>/ (BOQ.xlsx, BOQ.csv, EXPORT_MANIFEST.json),
EXCEPTIONS.json / EXCEPTIONS.csv, REACH_BY_FAMILY.json / .csv and GENERALISE_BACKLOG.json / .csv (with "compare"),
RUN_RECORD.json (input and output sha256). Exit 0 = the command ran end to end (exceptions may exist); 2 = refused
before geometry (a FATAL exception, nothing measured).
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import copy
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MANIFEST_SCHEMA = "URBAN_RUN_MANIFEST_V1"
RECORD_SCHEMA = "URBAN_RUN_RECORD_V1"
EXCEPTIONS_SCHEMA = "URBAN_RUN_EXCEPTIONS_V1"
REACH_SCHEMA = "URBAN_RUN_REACH_V1"
GEOMETRY_METHOD = "ARCH_TAKEOFF_V2.13"
DEFAULT_CONVENTIONS = "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
DATA_OBJECTS = ("inputs_sheet", "opening_table", "room_table", "wall_band", "schedule_tables")
# data object -> "module:function" reading it (T-781 / T-782 / T-783 / T-784 register theirs here); empty today
PLUGINS: dict = {}
FATAL, ACTION, INFO = "FATAL", "ACTION", "INFO"
REACH_CLASSES = ("GEOMETRY_DIRECT", "GEOMETRY_RESTATED", "FILL_RESTATED", "OVERLAY_ONLY", "FILL_ONLY")
NOT_REACHED = ("GEOMETRY_RESTATED", "FILL_RESTATED", "OVERLAY_ONLY", "FILL_ONLY")


class ManifestError(ValueError):
    pass


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _exc(level, code, what, **kw):
    return dict({"level": level, "code": code, "what": what}, **kw)


# ---- 1. manifest -----------------------------------------------------------------------------------------------------

def load_manifest(path):
    """-> (manifest with absolute paths, exceptions). Paths resolve against the manifest's folder."""
    path = Path(path).resolve()
    m = json.loads(path.read_text(encoding="utf-8"))
    if m.get("schema") != MANIFEST_SCHEMA:
        raise ManifestError(f"schema {m.get('schema')!r} is not {MANIFEST_SCHEMA}")
    if not str(m.get("project_id") or "").strip():
        raise ManifestError("project_id is required (one BOQ = one project)")
    base = path.parent

    def p(v):
        if v in (None, ""):
            return None
        q = Path(v)
        return str(q if q.is_absolute() else (base / q).resolve())

    d = m.get("drawings") or {}
    out = {"schema": MANIFEST_SCHEMA, "project_id": str(m["project_id"]).strip(),
           "drawings": {"plan": p(d.get("plan")), "structural": p(d.get("structural"))},
           "rules": {"conventions": p((m.get("rules") or {}).get("conventions")) or str(ROOT / DEFAULT_CONVENTIONS),
                     "profile": p((m.get("rules") or {}).get("profile")),
                     "facts": p((m.get("rules") or {}).get("facts"))},
           "data_objects": {k: p((m.get("data_objects") or {}).get(k)) for k in DATA_OBJECTS},
           "compare": {k: p((m.get("compare") or {}).get(k)) for k in ("candidate_index", "family_master")}}
    if (m.get("data_objects") or {}).keys() - set(DATA_OBJECTS):
        raise ManifestError(f"unknown data objects {sorted((m.get('data_objects') or {}).keys() - set(DATA_OBJECTS))}")
    return out, check_inputs(out)


def check_inputs(m):
    """every missing or unusable input -> one exception; a FATAL one stops the run before geometry."""
    ex = []
    plan, st = m["drawings"]["plan"], m["drawings"]["structural"]
    if not plan:
        ex.append(_exc(FATAL, "PLAN_DRAWING_NOT_GIVEN", "no architectural plan drawing in the manifest: nothing is "
                       "measured (no line, no 0)"))
    elif not Path(plan).is_file():
        ex.append(_exc(FATAL, "PLAN_DRAWING_MISSING", "the architectural plan drawing is not on disk", path=plan))
    elif Path(plan).suffix.lower() != ".dxf":
        ex.append(_exc(FATAL, "PLAN_NOT_DXF", "the plan must be a DXF (a DWG goes through tools/dwg_adapter.py "
                       "first)", path=plan))
    if not st:
        ex.append(_exc(ACTION, "STRUCTURAL_DRAWING_NOT_GIVEN", "no structural drawing: route G does not run; every "
                       "structural family stays unmeasured (HELD by absence, never 0)"))
    elif not Path(st).is_file():
        ex.append(_exc(FATAL, "STRUCTURAL_DRAWING_MISSING", "the structural drawing named in the manifest is not on "
                       "disk", path=st))
    elif plan and Path(plan).is_file() and sha256_file(plan) == sha256_file(st):
        ex.append(_exc(FATAL, "SAME_DRAWING_TWICE", "the plan and the structural drawing are the same file"))
    if not Path(m["rules"]["conventions"]).is_file():
        ex.append(_exc(FATAL, "RULE_SET_MISSING", "the conventions (rule set) file is not on disk",
                       path=m["rules"]["conventions"]))
    if st and not m["rules"]["profile"]:
        ex.append(_exc(ACTION, "STRUCTURAL_PROFILE_NOT_GIVEN", "no route G drawing profile: storey heights are not "
                       "read from a profile; the column pieces that need them stay HELD"))
    for k in ("profile", "facts"):
        v = m["rules"][k]
        if v and not Path(v).is_file():
            ex.append(_exc(FATAL, f"{k.upper()}_MISSING", f"the {k} file named in the manifest is not on disk", path=v))
    if not m["rules"]["facts"]:
        ex.append(_exc(ACTION, "PROJECT_FACTS_NOT_GIVEN", "no project facts file (heights, finishes, sanitary "
                       "reading): the lines that need them stay HELD"))
    for k in DATA_OBJECTS:
        v = m["data_objects"][k]
        if not v:
            ex.append(_exc(ACTION if k == "inputs_sheet" else INFO, f"{k.upper()}_ABSENT",
                           f"data object {k} not given: nothing of it is applied (its lines keep the geometry run's "
                           "state)"))
        elif not Path(v).is_file():
            ex.append(_exc(FATAL, f"{k.upper()}_MISSING", f"data object {k} named in the manifest is not on disk",
                           path=v))
        elif k not in PLUGINS:
            ex.append(_exc(ACTION, f"{k.upper()}_PRESENT_NOT_WIRED", f"data object {k} is given but no reader is "
                           "registered in this command yet: recorded by sha256, not applied", sha256=sha256_file(v)))
    for k, v in m["compare"].items():
        if v and not Path(v).is_file():
            ex.append(_exc(FATAL, f"COMPARE_{k.upper()}_MISSING", f"compare file {k} is not on disk", path=v))
    if bool(m["compare"]["candidate_index"]) != bool(m["compare"]["family_master"]):
        ex.append(_exc(FATAL, "COMPARE_INCOMPLETE", "compare needs both candidate_index and family_master"))
    return ex


# ---- 2. geometry -----------------------------------------------------------------------------------------------------

def run_geometry(m, out):
    """the unchanged m9 arch run (V2.13 + route G); its stdout goes to geometry/M9_STDOUT.txt."""
    from tools import urban_boq_m9 as M9
    gdir = out / "geometry"
    argv = ["arch", "--drawings", m["drawings"]["plan"], "--out", str(gdir), "--method", GEOMETRY_METHOD,
            "--project", m["project_id"], "--no-svg"]
    if m["drawings"]["structural"]:
        argv += ["--structural", m["drawings"]["structural"], "--conventions", m["rules"]["conventions"]]
        if m["rules"]["profile"]:
            argv += ["--profile", m["rules"]["profile"]]
    if m["rules"]["facts"]:
        argv += ["--facts", m["rules"]["facts"]]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = M9.main(argv)
    gdir.mkdir(parents=True, exist_ok=True)
    (gdir / "M9_STDOUT.txt").write_text(buf.getvalue(), encoding="utf-8")
    lines_p = gdir / "BOQ_LINES.json"
    lines = json.loads(lines_p.read_text(encoding="utf-8")) if lines_p.is_file() else None
    return rc, lines, argv


# ---- 4. export -------------------------------------------------------------------------------------------------------

def held_copy(ln, why):
    """the export copy of a refused zero: BLOCKED_RFI, blank quantity, the reason named (the engine line unchanged)."""
    c = copy.deepcopy(ln)
    c["evidence_state"] = "BLOCKED_RFI"
    c["measured_net"] = None
    c["bounded_range"] = None
    c["rfi"] = dict(c.get("rfi") or {}, question=why)
    c["notes"] = ((c.get("notes") or "") + " | " + why).strip(" |")
    return c


def export_all(lines, m, out):
    """one boq_export_v1 run per drawing identity -> ([export records], [exceptions])."""
    from tools import boq_export_v1 as X
    groups = collections.OrderedDict()
    for ln in lines:
        pr = ln.get("project") or {}
        groups.setdefault((str(pr.get("project_id")), str(pr.get("revision_set_sha256"))), []).append(ln)
    recs, ex = [], []
    if len(groups) > 1:
        ex.append(_exc(INFO, "TWO_DRAWING_IDENTITIES", f"{len(groups)} drawing identities (project id + revision set) "
                       "in one run: exported once each (one BOQ = one identity); a combined workbook waits for the "
                       "project inputs sheet to name one identity"))
    for i, ((pid, rev), gl) in enumerate(groups.items()):
        label = "architectural" if pid == m["project_id"] else (
            "structural" if m["drawings"]["structural"] and len(groups) == 2 else f"identity{i}")
        refused = []
        rows = []
        for ln in gl:
            try:
                X.check_zero(ln)
                rows.append(ln)
            except X.ExportError:
                refused.append(ln["line_id"])
                rows.append(held_copy(ln, "T-772 export: a quantity line at 0 with no producing input; HELD on the "
                                          "export copy (never 0) until its geometry is read"))
        if refused:
            ex.append(_exc(ACTION, "ZERO_WITHOUT_INPUT_HELD", f"{len(refused)} line(s) at 0 with no producing input: "
                           "exported HELD, engine line unchanged", identity=label, line_ids=sorted(refused)))
        d = out / "export" / label
        d.mkdir(parents=True, exist_ok=True)
        src = d / "LINES_EXPORTED.json"
        src.write_text(json.dumps(rows, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = X.main(["--lines", str(src), "--candidate-version", GEOMETRY_METHOD, "--out", str(d)])
        except X.ExportError as e:
            rc = None
            ex.append(_exc(ACTION, "EXPORT_REFUSED", str(e)[:400], identity=label))
        man = d / "EXPORT_MANIFEST.json"
        rc_doc = json.loads(man.read_text(encoding="utf-8")) if man.is_file() else {}
        recs.append({"identity": label, "project_id": pid, "revision_set_sha256": rev, "lines": len(gl),
                     "exit": rc, "row_counts": rc_doc.get("row_counts"),
                     "xlsx": str((d / "BOQ.xlsx").relative_to(out)) if (d / "BOQ.xlsx").is_file() else None})
    return recs, ex


def held_summary(lines):
    """one INFO exception per item code with lines the geometry run leaves without a figure."""
    from engine.source import arch_v3081 as A
    c = collections.Counter()
    for ln in lines:
        if A.line_class(ln) == "HELD":
            c[(ln["item_code"], ln.get("unit") or "")] += 1
    return [_exc(INFO, "HELD_BY_GEOMETRY", "lines without a figure after the geometry run", item_code=k[0], unit=k[1],
                 lines=n) for k, n in sorted(c.items())]


# ---- 5. reach --------------------------------------------------------------------------------------------------------

_HEX = re.compile(r"L-[0-9a-f]{12,}")
_FLOOR = re.compile(r"^(GF|1F|2F|3F|RF|ROOF|BF|B1|MZ)-")


def element_group(element_id):
    """the element group of an element id: its first two ':' fields, line ids and floor prefixes generalised."""
    parts = str(element_id or "").split(":")[:2]
    parts = [_FLOOR.sub("<FLOOR>-", _HEX.sub("L-*", x)) for x in parts]
    return ":".join(parts)


def reach(geometry_lines, index, master):
    """-> (per-line rows, per-family rows, backlog rows). Compares the CLASS and the released figure only."""
    from engine.source import arch_v3081 as A
    g = {ln["line_id"]: ln for ln in geometry_lines}
    fam_of = {c: f["code"] for f in master["families"] for c in f.get("item_codes", [])}
    fam_name = {f["code"]: f.get("item_en") or "" for f in master["families"]}
    rows = []
    for x in index["lines"]:
        gl = g.get(x["line_id"])
        filled = bool(x.get("method_label"))
        if gl is None:
            k = "FILL_ONLY" if filled else "OVERLAY_ONLY"
        else:
            cg = A.line_class(gl)
            same = cg == x["class"] and (cg != "RELEASED" or abs(float(gl["measured_net"]) -
                                                                 float(x["measured_net"])) <= 1e-6)
            k = "GEOMETRY_DIRECT" if same and not filled else ("FILL_RESTATED" if filled else
                                                                ("GEOMETRY_DIRECT" if same else "GEOMETRY_RESTATED"))
        rows.append({"line_id": x["line_id"], "item_code": x["item_code"], "unit": x["unit"],
                     "family": fam_of.get(x["item_code"], "NO_FAMILY"), "class": x["class"], "reach": k,
                     "element_group": element_group(x.get("element_id")), "method_label": x.get("method_label"),
                     "candidate_net": x["measured_net"] if x["class"] == "RELEASED" else None,
                     "geometry_net": gl["measured_net"] if gl is not None and A.line_class(gl) == "RELEASED" else None})
    fams = collections.OrderedDict()
    for r in sorted(rows, key=lambda r: (r["family"], r["item_code"])):
        f = fams.setdefault(r["family"], dict({"family": r["family"], "item_en": fam_name.get(r["family"], ""),
                                               "lines": 0, "excluded": 0}, **{c: 0 for c in REACH_CLASSES}))
        if r["class"] == "EXCLUDED":
            f["excluded"] += 1
            continue
        f["lines"] += 1
        f[r["reach"]] += 1
    for f in fams.values():
        f["reached_share"] = round(f["GEOMETRY_DIRECT"] / f["lines"], 4) if f["lines"] else None
    back = collections.OrderedDict()
    for r in rows:
        if r["class"] == "EXCLUDED" or r["reach"] not in NOT_REACHED:
            continue
        key = (r["family"], r["item_code"], r["unit"], r["element_group"], r["reach"])
        b = back.setdefault(key, {"family": r["family"], "item_code": r["item_code"], "unit": r["unit"],
                                  "element_group": r["element_group"], "reach": r["reach"], "lines": 0,
                                  "released_lines": 0, "candidate_released_qty": 0.0, "geometry_released_qty": 0.0,
                                  "labels": set()})
        b["lines"] += 1
        if r["candidate_net"] is not None:
            b["released_lines"] += 1
            b["candidate_released_qty"] += float(r["candidate_net"])
        if r["geometry_net"] is not None:
            b["geometry_released_qty"] += float(r["geometry_net"])
        if r["method_label"]:
            b["labels"].add(r["method_label"])
    blist = []
    for b in back.values():
        b["candidate_released_qty"] = round(b["candidate_released_qty"], 3)
        b["geometry_released_qty"] = round(b["geometry_released_qty"], 3)
        b["labels"] = sorted(b["labels"])
        blist.append(b)
    blist.sort(key=lambda b: (b["family"], b["item_code"], b["element_group"], b["reach"]))
    not_in_index = sorted(set(g) - {x["line_id"] for x in index["lines"]})
    return rows, list(fams.values()), blist, not_in_index


def backlog_by_item(back):
    """the backlog one row per (family, item code, unit): the rule each GENERALISE row writes and tests."""
    agg = collections.OrderedDict()
    for b in back:
        k = (b["family"], b["item_code"], b["unit"])
        a = agg.setdefault(k, dict({"family": k[0], "item_code": k[1], "unit": k[2], "lines": 0, "element_groups": 0,
                                    "candidate_released_qty": 0.0, "geometry_released_qty": 0.0},
                                   **{c: 0 for c in NOT_REACHED}))
        a["lines"] += b["lines"]
        a["element_groups"] += 1
        a[b["reach"]] += b["lines"]
        a["candidate_released_qty"] = round(a["candidate_released_qty"] + b["candidate_released_qty"], 3)
        a["geometry_released_qty"] = round(a["geometry_released_qty"] + b["geometry_released_qty"], 3)
    return sorted(agg.values(), key=lambda a: (a["family"], a["item_code"], a["unit"]))


# ---- the command -----------------------------------------------------------------------------------------------------

def _csv(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (";".join(v) if isinstance(v, list) else v) for k, v in r.items()})


def run(manifest_path, out):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    m, ex = load_manifest(manifest_path)
    record = {"schema": RECORD_SCHEMA, "project_id": m["project_id"], "geometry_method": GEOMETRY_METHOD,
              "released_default": False, "changes_engine_lines": False,
              "inputs": {}, "outputs": {}, "exports": [], "reach": None}
    for grp in ("drawings", "rules", "data_objects", "compare"):
        for k, v in m[grp].items():
            if v and Path(v).is_file():
                record["inputs"][f"{grp}.{k}"] = {"name": Path(v).name, "sha256": sha256_file(v)}
    if any(e["level"] == FATAL for e in ex):
        return _finish(out, record, ex, rc=2)
    rc, lines, argv = run_geometry(m, out)
    record["geometry"] = {"exit": rc, "argv_method": GEOMETRY_METHOD, "lines": None if lines is None else len(lines)}
    if rc != 0 or lines is None:
        ex.append(_exc(FATAL, "GEOMETRY_STOPPED", f"the geometry run stopped (exit {rc}); see geometry/ for its "
                       "admission findings: nothing measured"))
        return _finish(out, record, ex, rc=2)
    ex += held_summary(lines)
    recs, ex2 = export_all(lines, m, out)
    record["exports"] = recs
    ex += ex2
    if m["compare"]["candidate_index"]:
        index = json.loads(Path(m["compare"]["candidate_index"]).read_text(encoding="utf-8"))
        master = json.loads(Path(m["compare"]["family_master"]).read_text(encoding="utf-8"))
        rows, fams, back, not_in_index = reach(lines, index, master)
        totals = collections.Counter(r["reach"] for r in rows if r["class"] != "EXCLUDED")
        record["reach"] = {"candidate_version": index.get("candidate_version"), "candidate_lines": len(rows),
                           "by_reach": dict(sorted(totals.items())), "geometry_lines_not_in_candidate":
                           len(not_in_index), "backlog_groups": len(back)}
        doc = {"schema": REACH_SCHEMA, "candidate_version": index.get("candidate_version"),
               "family_master": master.get("version"), "by_family": fams, "geometry_lines_not_in_candidate":
               not_in_index}
        (out / "REACH_BY_FAMILY.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        _csv(out / "REACH_BY_FAMILY.csv", fams, ["family", "item_en", "lines", "excluded", *REACH_CLASSES,
                                                 "reached_share"])
        (out / "GENERALISE_BACKLOG.json").write_text(json.dumps({"schema": REACH_SCHEMA + "_BACKLOG", "groups": back},
                                                                ensure_ascii=False, indent=1), encoding="utf-8")
        _csv(out / "GENERALISE_BACKLOG_BY_ITEM.csv", backlog_by_item(back), ["family", "item_code", "unit", "lines",
                                                                             "element_groups", *NOT_REACHED,
                                                                             "candidate_released_qty",
                                                                             "geometry_released_qty"])
        _csv(out / "GENERALISE_BACKLOG.csv", back, ["family", "item_code", "unit", "element_group", "reach", "lines",
                                                    "released_lines", "candidate_released_qty",
                                                    "geometry_released_qty", "labels"])
    return _finish(out, record, ex, rc=0)


def _finish(out, record, ex, rc):
    order = {FATAL: 0, ACTION: 1, INFO: 2}
    ex = sorted(ex, key=lambda e: (order[e["level"]], e["code"], json.dumps(e, sort_keys=True)))
    (out / "EXCEPTIONS.json").write_text(json.dumps({"schema": EXCEPTIONS_SCHEMA, "exceptions": ex},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    _csv(out / "EXCEPTIONS.csv", ex, ["level", "code", "what", "identity", "item_code", "unit", "lines", "path"])
    record["exit"] = rc
    record["exceptions"] = dict(sorted(collections.Counter(e["level"] for e in ex).items()))
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.parent == out and p.name != "RUN_RECORD.json":
            record["outputs"][p.name] = sha256_file(p)
    (out / "RUN_RECORD.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    return rc


def main(argv=None):
    ap = argparse.ArgumentParser(prog="urban_boq_run", description=__doc__.split("\n\n")[0])
    ap.add_argument("--manifest", required=True, help=f"a {MANIFEST_SCHEMA} JSON file")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        rc = run(a.manifest, a.out)
    except ManifestError as e:
        print(f"MANIFEST REFUSED: {e}", file=sys.stderr)
        return 2
    rec = json.loads((Path(a.out) / "RUN_RECORD.json").read_text(encoding="utf-8"))
    print(json.dumps({k: rec.get(k) for k in ("exit", "geometry", "exports", "reach", "exceptions")}, indent=1))
    return rc


if __name__ == "__main__":
    sys.exit(main())
