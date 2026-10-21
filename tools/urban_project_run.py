"""URBAN PROJECT RUN (M7) - one manifest per project; the blind protocol enforced by the tool, not remembered.

    python3 -I tools/urban_project_run.py init MANIFEST.json --project ID --structural S.dxf [--architectural A.dxf]
                                               [--profile P.json] [--reference-boq REF.csv] [--rate 26.5]
    python3 -I tools/urban_project_run.py run MANIFEST.json OUT        # BLIND: the reference is never opened
    python3 -I tools/urban_project_run.py check MANIFEST.json OUT      # rebuild in memory, byte-for-byte equality
    python3 -I tools/urban_project_run.py compare MANIFEST.json OUT    # only after the freeze; never edits OUT

MANIFEST (URBAN_PROJECT_MANIFEST_V1): project_id; drawings [{path, sha256, discipline STRUCTURAL / ARCHITECTURAL,
revision}]; profile; conventions (default engine/profiles/URBAN_M7_GENERIC_CONVENTIONS_V5.json); evidence;
evidence_review; decisions (engineer decisions, engine.source.quantity_release); ocr_ledger; reference_boq
{path, sha256, format GENERIC_BOQ_CSV_V1} (declared, NOT opened by run); unit_rate_per_m3 (a reporting input only).

run      every drawing's sha256 must equal the manifest's (a different revision is a different project run); the
         JSON inputs pass engine.benchmark_protection.assert_blind; route G with completeness; per-item independent
         checks (tools/m7_independent); the release register (engine.source.quantity_release); outputs written as
         text and hashed into RUN_FREEZE.json together with the engine sources' sha256 and the git commit. Nothing in
         a run reads the reference BOQ.
check    the same run in memory; every output must equal the frozen file byte for byte (determinism).
compare  refuses unless RUN_FREEZE.json exists and every frozen output is unchanged; then (and only then) reads the
         reference, verifies its sha256, and writes RECONCILIATION.csv / .json and COMPARE_RECORD.json beside the
         run - the run's own files are never rewritten.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import benchmark_protection as bp            # noqa: E402
from engine.source import boq_reconcile as BR             # noqa: E402
from engine.source import quantity_release as QR          # noqa: E402
from tools import m7_independent as IC                    # noqa: E402
from tools import urban_boq_m2 as CLI                     # noqa: E402

MANIFEST_VERSION = "URBAN_PROJECT_MANIFEST_V1"
DEFAULT_CONVENTIONS = "engine/profiles/URBAN_M7_GENERIC_CONVENTIONS_V5.json"
ENGINE_FILES = ("tools/urban_intake.py", "tools/urban_boq_m2.py", "tools/m7_independent.py",
                "tools/urban_project_run.py", "engine/source/drawing_model.py", "engine/source/generic_route.py",
                "engine/source/member_detection.py", "engine/source/slab_engine.py", "engine/source/topology.py",
                "engine/source/schedule_reader.py", "engine/source/provisional_estimate.py",
                "engine/source/concrete_completeness.py", "engine/source/quantity_release.py",
                "engine/source/boq_reconcile.py", "engine/source/cad_heal.py")
ITEM_FIELDS = ("item_id", "trade", "family", "storey", "category", "unit", "low", "base", "high", "exposure_low",
               "exposure_high", "support", "confidence", "blocker", "assumptions", "source")
RELEASE_FIELDS = ("ITEM_ID", "TRADE", "FAMILY", "STOREY", "CATEGORY", "UNIT", "BASE", "LOW", "HIGH", "EXPOSURE_LOW",
                  "EXPOSURE_HIGH", "SUPPORT", "MACHINE_RUNG", "STATE", "REASONS", "CHECK", "CHECK_METHOD",
                  "DECISION", "INVALIDATED_DECISIONS", "REJECTED_OCR", "NEXT_REQUIREMENT", "FINGERPRINT",
                  "SOURCE_FILE", "SOURCE_SHA256")
CHECK_FIELDS = ("item_id", "result", "method", "shared", "engine", "independent", "tolerance", "note")
FINDING_FIELDS = ("FINDING_ID", "SEVERITY", "KIND", "FAMILY", "CONFIDENCE", "SHEET", "STOREY", "BOX_M", "EVIDENCE",
                  "MAGNITUDE", "VOLUME_LOW_M3", "VOLUME_HIGH_M3", "VOLUME_BASIS", "ITEMS", "REFS", "ACTION")


class ProtocolError(RuntimeError):
    pass


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha_text(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def _path(manifest_path, p):
    """a manifest path: absolute, or relative to the manifest's folder, or (failing that) to the repository."""
    if p is None:
        return None
    q = Path(p)
    if q.is_absolute():
        return q
    near = Path(manifest_path).resolve().parent / q
    return near.resolve() if near.exists() else (ROOT / q).resolve()


def _cell(v):
    if isinstance(v, float):
        return f"{v:.6f}".rstrip("0").rstrip(".") if v == v else ""
    if isinstance(v, (list, tuple)):
        return ";".join(str(x) for x in v)
    if isinstance(v, dict):
        return json.dumps(v, sort_keys=True, ensure_ascii=True)
    return "" if v is None else str(v)


def csv_text(rows, fields):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(fields)
    for r in rows:
        w.writerow([_cell(r.get(f)) for f in fields])
    return buf.getvalue()


def load_manifest(path):
    m = json.loads(Path(path).read_text(encoding="utf-8"))
    if m.get("manifest_version") != MANIFEST_VERSION:
        raise ProtocolError(f"not a {MANIFEST_VERSION} manifest")
    if not m.get("drawings") or not any(d.get("discipline") == "STRUCTURAL" for d in m["drawings"]):
        raise ProtocolError("a manifest needs at least one STRUCTURAL drawing")
    return m


def init(path, *, project, structural, architectural=(), profile=None, reference=None, rate=None, revision="?"):
    drawings = [{"path": str(s), "sha256": sha256_file(s), "discipline": "STRUCTURAL", "revision": revision}
                for s in structural]
    drawings += [{"path": str(a), "sha256": sha256_file(a), "discipline": "ARCHITECTURAL", "revision": revision}
                 for a in architectural]
    m = {"manifest_version": MANIFEST_VERSION, "project_id": project, "drawings": drawings,
         "profile": str(profile) if profile else None, "conventions": DEFAULT_CONVENTIONS, "evidence": None,
         "evidence_review": None, "decisions": None, "ocr_ledger": None,
         # the reference is declared by path and hash only: `run` never opens it
         "reference_boq": {"path": str(reference), "sha256": sha256_file(reference), "format": BR.FORMAT}
         if reference else None,
         "unit_rate_per_m3": rate}
    Path(path).write_text(json.dumps(m, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return m


def engine_record():
    try:
        commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True,
                                check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", *ENGINE_FILES],
                               capture_output=True, text=True, check=True).stdout.split("\n")
        dirty = sorted(x[3:] for x in dirty if x.strip())
    except (OSError, subprocess.CalledProcessError):
        commit, dirty = None, None
    return {"git_commit": commit, "engine_files_modified_since_commit": dirty,
            "files_sha256": {f: sha256_file(ROOT / f) for f in ENGINE_FILES if (ROOT / f).exists()}}


def compute(manifest_path):
    """the run itself (pure: returns {file name: text}); verifies the drawings' revision and the blind inputs."""
    m = load_manifest(manifest_path)
    drawings = []
    for d in m["drawings"]:
        p = _path(manifest_path, d["path"])
        got = sha256_file(p)
        if got != d["sha256"]:
            raise ProtocolError(f"{Path(d['path']).name}: sha256 {got[:12]} is not the manifest's "
                                f"{d['sha256'][:12]} - a new revision needs its own manifest")
        drawings.append((d, p))
    side = {}
    for k in ("profile", "evidence", "evidence_review", "decisions", "ocr_ledger"):
        if m.get(k):
            p = _path(manifest_path, m[k])
            doc = json.loads(p.read_text(encoding="utf-8"))
            bp.assert_blind(doc)                        # nothing benchmark-shaped reaches a blind pass
            side[k] = (p, doc)
    conv = _path(manifest_path, m.get("conventions") or DEFAULT_CONVENTIONS)
    struct = [str(p) for d, p in drawings if d["discipline"] == "STRUCTURAL"]
    arch = [str(p) for d, p in drawings if d["discipline"] == "ARCHITECTURAL"] or None
    R = CLI.compute(struct, profile=str(side["profile"][0]) if "profile" in side else None, route="G",
                    conventions=str(conv), evidence=str(side["evidence"][0]) if "evidence" in side else None,
                    arch=arch, evidence_review=str(side["evidence_review"][0]) if "evidence_review" in side
                    else None, completeness=True)
    items = R["items"]
    checks = IC.item_checks(R["generic"]["D"], items)
    sources = {Path(p).name: d["sha256"] for d, p in drawings}
    decisions = side["decisions"][1].get("decisions", []) if "decisions" in side else []
    ledger = QR.OcrLedger(side["ocr_ledger"][1].get("entries", [])) if "ocr_ledger" in side else None
    reg = QR.register(items, sources=sources, checks=checks, decisions=decisions, ocr_ledger=ledger)
    CR = R["generic"].get("completeness") or {"findings": []}
    fam = {}
    for i in items:
        if i["trade"] != "CONCRETE":
            continue
        k = f"{i['family']}|{i.get('storey')}"
        f = fam.setdefault(k, {"measured_m3": 0.0, "n_measured": 0, "unresolved_low_m3": 0.0,
                               "unresolved_high_m3": 0.0, "n_unresolved": 0})
        if i["category"] in ("PROVISIONAL", "VERIFIED"):
            f["measured_m3"] += i.get("base") or 0.0
            f["n_measured"] += 1
        elif i["category"] == "UNRESOLVED":
            f["unresolved_low_m3"] += i.get("exposure_low") or 0.0
            f["unresolved_high_m3"] += i.get("exposure_high") or 0.0
            f["n_unresolved"] += 1
    summary = {"project_id": m["project_id"], "manifest_version": MANIFEST_VERSION,
               "conventions_set": json.loads(conv.read_text(encoding="utf-8")).get("set"),
               "detect_options": R["generic"]["D"].get("options"),
               "drawings": [{"file": Path(p).name, "sha256": d["sha256"], "discipline": d["discipline"],
                             "revision": d.get("revision")} for d, p in drawings],
               "concrete_by_family_storey": {k: {kk: round(vv, 4) if isinstance(vv, float) else vv
                                                 for kk, vv in v.items()} for k, v in sorted(fam.items())},
               "release_totals": reg["totals"], "independent_checks": IC.summary(checks),
               "completeness_findings": len(CR["findings"]),
               "decisions": {"given": len(decisions), "invalidated": reg["invalidated"],
                             "refused": [d.get("decision_id") for d in reg["refused"]]},
               "reference_opened": False,
               "unit_rate_per_m3": m.get("unit_rate_per_m3"),
               "note": "measured = PROVISIONAL + VERIFIED base; unresolved = exposure range, never added; released "
                       "= ENGINEER_APPROVED only"}
    out = {"ITEMS.csv": csv_text(items, ITEM_FIELDS),
           "RELEASE_REGISTER.csv": csv_text(reg["rows"], RELEASE_FIELDS),
           "INDEPENDENT_CHECKS.csv": csv_text([dict(v, item_id=k) for k, v in sorted(checks.items())], CHECK_FIELDS),
           "COMPLETENESS_FINDINGS.csv": csv_text(CR["findings"], FINDING_FIELDS),
           "SUMMARY.json": json.dumps(summary, indent=1, sort_keys=True, default=str) + "\n"}
    return m, out


def run(manifest_path, out_dir):
    m, out = compute(manifest_path)
    od = Path(out_dir)
    if (od / "RUN_FREEZE.json").exists():
        raise ProtocolError(f"{od} already holds a frozen run; a new run goes to a new folder")
    od.mkdir(parents=True, exist_ok=True)
    for name, text in out.items():
        (od / name).write_text(text, encoding="utf-8")
    payload = {"project_id": m["project_id"], "outputs_sha256": {k: _sha_text(v) for k, v in sorted(out.items())}}
    frozen = bp.freeze(payload)
    rec = {"phase": bp.BLIND, "then": frozen["phase"], "CANDIDATE_GEOMETRY_HASH": frozen["CANDIDATE_GEOMETRY_HASH"],
           "project_id": m["project_id"], "manifest_sha256": sha256_file(manifest_path),
           "drawings": [{"file": Path(d["path"]).name, "sha256": d["sha256"], "revision": d.get("revision")}
                        for d in m["drawings"]],
           "engine": engine_record(), "outputs_sha256": payload["outputs_sha256"],
           "reference_boq_declared_sha256": (m.get("reference_boq") or {}).get("sha256"),
           "reference_opened_before_freeze": False}
    (od / "RUN_FREEZE.json").write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return rec


def check(manifest_path, out_dir):
    _, out = compute(manifest_path)
    od = Path(out_dir)
    return {name: (od / name).exists() and (od / name).read_text(encoding="utf-8") == text
            for name, text in out.items()}


def compare(manifest_path, out_dir):
    m = load_manifest(manifest_path)
    od = Path(out_dir)
    fz = od / "RUN_FREEZE.json"
    if not fz.exists():
        raise ProtocolError("no RUN_FREEZE.json: the run must be frozen before the reference is opened")
    rec = json.loads(fz.read_text(encoding="utf-8"))
    if not bp.may_reconcile(rec):
        raise ProtocolError("the freeze record carries no candidate hash")
    for name, h in rec["outputs_sha256"].items():
        if not (od / name).exists() or _sha_text((od / name).read_text(encoding="utf-8")) != h:
            raise ProtocolError(f"{name} changed after the freeze: reconciliation refused")
    ref = m.get("reference_boq")
    if not ref:
        raise ProtocolError("the manifest declares no reference BOQ")
    rp = _path(manifest_path, ref["path"])
    if sha256_file(rp) != ref["sha256"] or ref["sha256"] != rec.get("reference_boq_declared_sha256"):
        raise ProtocolError("the reference BOQ is not the one declared before the run")
    if ref.get("format", BR.FORMAT) != BR.FORMAT:
        raise ProtocolError(f"reference format {ref.get('format')} is not {BR.FORMAT}")
    items = list(csv.DictReader(io.StringIO((od / "ITEMS.csv").read_text(encoding="utf-8"))))
    for i in items:                                           # the frozen run's own numbers, nothing recomputed
        for k in ("low", "base", "high", "exposure_low", "exposure_high"):
            i[k] = float(i[k]) if i.get(k) not in (None, "") else None
    res = BR.reconcile(items, BR.read_reference(rp.read_text(encoding="utf-8")), rate=m.get("unit_rate_per_m3"))
    cols = ("FAMILY", "STOREY", "ENGINE_BASE_M3", "ENGINE_UNRESOLVED_LOW_M3", "ENGINE_UNRESOLVED_HIGH_M3",
            "REFERENCE_M3", "REFERENCE_ROWS", "DIFF_REF_MINUS_ENGINE_M3", "STATE", "DIFF_VALUE_AT_RATE")
    files = {"RECONCILIATION.csv": csv_text(res["rows"], cols),
             "RECONCILIATION.json": json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1,
                                               sort_keys=True) + "\n"}
    for name, text in files.items():
        (od / name).write_text(text, encoding="utf-8")
    cr = {"phase": bp.RECONCILIATION, "run_freeze_hash": rec["CANDIDATE_GEOMETRY_HASH"],
          "reference_sha256": ref["sha256"], "files_sha256": {k: _sha_text(v) for k, v in sorted(files.items())},
          "run_outputs_unchanged": True,
          "rule": "a reconciliation state is a lead for investigation on the drawing; no engine value was changed"}
    (od / "COMPARE_RECORD.json").write_text(json.dumps(cr, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return res


def main(argv):
    if not argv or argv[0] not in ("init", "run", "check", "compare"):
        print(__doc__)
        return 2
    cmd, args = argv[0], [a for a in argv[1:] if not a.startswith("--")]
    opt = {}
    k = 1
    while k < len(argv):
        if argv[k].startswith("--"):
            opt.setdefault(argv[k], []).append(argv[k + 1] if k + 1 < len(argv) else None)
            k += 2
        else:
            k += 1
    flat = {v for vs in opt.values() for v in vs}
    args = [a for a in args if a not in flat]
    if cmd == "init":
        m = init(args[0], project=opt["--project"][0], structural=opt["--structural"],
                 architectural=opt.get("--architectural", ()), profile=(opt.get("--profile") or [None])[0],
                 reference=(opt.get("--reference-boq") or [None])[0],
                 rate=float(opt["--rate"][0]) if "--rate" in opt else None)
        print(json.dumps({"project_id": m["project_id"], "drawings": len(m["drawings"])}))
    elif cmd == "run":
        rec = run(args[0], args[1])
        print(json.dumps({"frozen": rec["CANDIDATE_GEOMETRY_HASH"], "outputs": len(rec["outputs_sha256"])}))
    elif cmd == "check":
        r = check(args[0], args[1])
        print(json.dumps(r, indent=1))
        return 0 if all(r.values()) else 1
    else:
        res = compare(args[0], args[1])
        print(json.dumps(res["totals"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
