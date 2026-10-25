"""SCOREBOARD / CENSUS SEALED-INPUT GUARD (T-275): the scoreboard (tools/scoreboard_v2.py), the scoreboard key map
(tools/alsenan_keymap.py) and coverage census V2 (engine/source/coverage_census_v2.py) run only on PINNED runs and
never on a sealed input. A read-only wrapper: tools/scoreboard_v2.py, tools/alsenan_keymap.py and the census are
called unchanged, so an accepted run writes byte-identical outputs to a direct call; nothing in engine/ or tools/
imports this module (rollback: delete it). It computes, changes and approves no quantity.

    python3 -I tools/scoreboard_guarded.py scoreboard --run RUN_DIR --label L --reference R.json --key-map K.json
            --verdicts V.json [--candidate-lines C.json --candidate-label CL --candidate-manifest CM.json]
            --out OUT.json [--markdown OUT.md] [--heading H] [--layout v2|five] [--min-accuracy-scope X]
            [--sealed-registry REG.json] [--guard-record GUARD.json]
    python3 -I tools/scoreboard_guarded.py keymap <every tools/alsenan_keymap.py option, v1 / v2 / --set-bindings>
            [--candidate-manifest CM.json] [--sealed-registry REG.json] [--guard-record GUARD.json]
    python3 -I tools/scoreboard_guarded.py census --released RUN_DIR [...] [--candidate LINES.json MANIFEST.json ...]
            --out DIR [--sealed-registry REG.json]

Rules (each is a test in tests/t275_scoreboard_guard/; refusal = exit 2, every reason printed as
`SCOREBOARD REFUSED [CODE]: ...`, NOTHING written, the scorer never called):

1 PINNED RUN. A scored or censused run folder must hold the baseline runner's BASELINE_MANIFEST.json
  (URBAN_BASELINE_MANIFEST_V1, T-165) with status REPRODUCED or RUN_NO_EXPECTED_FIGURES and at least one pinned
  drawing (MANIFEST_MISSING / MANIFEST_INVALID). Every run output the call reads that the manifest hashes
  (BOQ_LINES.json always; MATERIAL_RESULTS.json and COVERAGE.json for the census) must have the manifest's sha256
  (MANIFEST_MISMATCH: a drifted or foreign run). Run files the manifest does not hash (BOQ_RELEASE_REPORT.json,
  structural/FAMILY_COVERAGE.csv) are read as the run wrote them and listed in the guard record as NOT PINNED with
  their sha256 (research/agents_t275: the runner should hash them; a written proposal, that runner is not touched).
2 PINNED CANDIDATE. Candidate lines need their candidate manifest (URBAN_CANDIDATE_MANIFEST_V1 from
  tools/v30_gate_b_v2.py `manifest`): lines sha256 and line count are the manifest's (MANIFEST_MISMATCH).
3 IDENTITY BY DRAWING sha256, NEVER BY LABEL (tools/v30_gate_b_v2.py check_side, unchanged): every line's revision
  set must be the revision set of a subset of its side's pinned drawings (REVISION_MIX: a line of an unpinned drawing,
  or a line without an identity, is refused whatever project id it prints), its project id the manifest's or a
  declared route label (PROJECT_MIX).
4 ONE PROJECT. All sides of one call are one project: two sides with two (non-null) project ids are PROJECT_MIX; the
  same drawing role or file name pinned with two sha256s is DRAWING_MISMATCH; a candidate scored beside a run's
  release report must pin every drawing that run pins (DRAWING_MISMATCH: another villa or another revision).
5 SEALED (owner 2026-10-23 19:45, research/agents_t168/SEALED_REGISTRY.json through tools/v30_gate_b_v2.py
  guard_inputs / guard_projects, unchanged): every input file is hashed and refused when its sha256 is a sealed
  file's, whatever its name, or when its name is a sealed name (refused unopened); every pinned drawing whose sha256
  or file name is sealed; every project id (manifests and line labels) that is a SEALED_PROJECT.
6 GUARD RECORD (optional --guard-record, census: always GUARD_RECORD.json in --out): schema
  URBAN_SCOREBOARD_GUARD_RECORD_V1, the command, the sealed registry sha256, every input by role / file name / sha256,
  each side (kind, spec id, manifest sha256, project id, identities, pinned drawings by role / file / sha256) and the
  NOT PINNED files. No timestamp and no path: two accepted calls on the same inputs write byte-identical records.
7 Freelancer and benchmark figures are never a guard parameter; the guard decides only WHICH files may be scored.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import v30_gate_b_v2 as G  # noqa: E402

DEFAULT_GUARD_CLASS = "TOOLING"        # T-212: a read-only check tool; it produces no quantity

RECORD_SCHEMA = "URBAN_SCOREBOARD_GUARD_RECORD_V1"
RUN_MANIFEST = "BASELINE_MANIFEST.json"          # the T-165 baseline runner's MANIFEST_NAME
LINES = "BOQ_LINES.json"
RELEASE_REPORT = "BOQ_RELEASE_REPORT.json"
CENSUS_PINNED = (LINES, "MATERIAL_RESULTS.json", "COVERAGE.json")
FAMILY_COVERAGE = Path("structural") / "FAMILY_COVERAGE.csv"
Refused = G.Refused


# ------------------------------------------------------------------------------------------------------------ pins
def _load_json(path):
    b = Path(path).read_bytes()
    try:
        return json.loads(b.decode("utf-8")), G.sha256_bytes(b)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise Refused([("INPUT_INVALID", f"{Path(path).name} is not valid JSON")]) from None


def sealed_drawings(view, reg, side):
    """SEALED problems for every drawing a manifest pins whose sha256 or file name is a sealed file's."""
    by_sha = {e["sha256"]: e for e in reg["entries"] if e.get("sha256")}
    names = G.sealed_names(reg)
    out = []
    for d in view["drawings"]:
        if d.get("sha256") in by_sha:
            out.append(("SEALED", f"{side}: pinned drawing {d.get('role')} has the sha256 of the sealed "
                                  f"{by_sha[d['sha256']].get('label')} (refused whatever its name)"))
        elif d.get("file") in names:
            out.append(("SEALED", f"{side}: pinned drawing {d.get('role')} {d.get('file')} is a sealed name"))
    return out


def _side_record(side, view, ident, pinned_files):
    return {"side": side, "kind": view["kind"], "spec_id": view["spec_id"], "manifest_sha256": view["manifest_sha256"],
            "project_id": view["project_id"], "boq_lines_sha256": view["boq_lines_sha256"],
            "line_count": view["line_count"], "identities": ident["identities"],
            "drawings": [{"role": d.get("role"), "file": d.get("file"), "sha256": d.get("sha256")}
                         for d in view["drawings"]],
            "pinned_files_sha256": dict(sorted(pinned_files.items()))}


def pin_run(run_dir, reg, *, side="run", need=(LINES,)):
    """-> (side record, view). Refused unless run_dir is a pinned baseline run whose files `need` are the manifest's."""
    run_dir = Path(run_dir)
    man = run_dir / RUN_MANIFEST
    if not man.is_file():
        raise Refused([("MANIFEST_MISSING", f"{side}: {run_dir.name} has no {RUN_MANIFEST}: only a pinned baseline run "
                                            "is scored or censused (an unpinned run is refused)")])
    m, msha = _load_json(man)
    view = G.manifest_view(m, msha, side)
    if view["kind"] != "RELEASE":
        raise Refused([("MANIFEST_INVALID", f"{side}: {RUN_MANIFEST} is not a baseline run manifest")])
    outs = ((m.get("run") or {}).get("outputs_sha256")) or {}
    problems, files = [], {}
    for n in need:
        p = run_dir / n
        if not p.is_file():
            problems.append(("INPUT_INVALID", f"{side}: {n} missing in {run_dir.name}"))
            continue
        s = G.sha256_file(p)
        if outs.get(n) != s:
            problems.append(("MANIFEST_MISMATCH", f"{side}: {n} sha256 {s[:12]} is not the manifest's "
                                                  f"{str(outs.get(n))[:12]} (a drifted or foreign run)"))
        files[n] = s
    if problems:
        raise Refused(problems)
    lines, lsha = G.read_lines(run_dir / LINES)
    ident = G.check_side(lines, view, side, lsha)
    problems = sealed_drawings(view, reg, side)
    if problems:
        raise Refused(problems)
    return _side_record(side, view, ident, files), view


def pin_candidate(lines_path, manifest_path, reg, *, side="candidate"):
    if manifest_path is None:
        raise Refused([("MANIFEST_MISSING", f"{side}: {Path(lines_path).name} has no candidate manifest "
                                            "(--candidate-manifest): unpinned candidate lines are refused")])
    m, msha = _load_json(manifest_path)
    view = G.manifest_view(m, msha, side)
    if view["kind"] != "CANDIDATE":
        raise Refused([("MANIFEST_INVALID", f"{side}: {Path(manifest_path).name} is not a candidate manifest")])
    lines, lsha = G.read_lines(lines_path)
    ident = G.check_side(lines, view, side, lsha)
    problems = sealed_drawings(view, reg, side)
    if problems:
        raise Refused(problems)
    return _side_record(side, view, ident, {Path(lines_path).name: lsha}), view


def one_project(pinned, reg):
    """section 4 over [(record, view)] + the SEALED_PROJECT check of every project id and line label."""
    problems = []
    pids = sorted({r["project_id"] for r, _ in pinned if r["project_id"] is not None})
    if len(pids) > 1:
        problems.append(("PROJECT_MIX", f"sides of {len(pids)} project ids {pids}: one scoreboard / census is one "
                                        "project"))
    dprob, _ = G.drawing_conflicts([(r["side"], v) for r, v in pinned])
    problems += dprob
    runs = [(r, v) for r, v in pinned if v["kind"] == "RELEASE"]
    for rc, vc in pinned:
        if vc["kind"] != "CANDIDATE":
            continue
        have = {d["sha256"] for d in vc["drawings"]}
        for rr, vr in runs:
            for d in vr["drawings"]:
                if d["sha256"] not in have:
                    problems.append(("DRAWING_MISMATCH", f"{rr['side']} drawing {d.get('role')} "
                                                         f"{str(d['sha256'])[:12]} is not pinned by {rc['side']} "
                                                         "(another villa or another revision)"))
    labels = {i["line_project_id"] for r, _ in pinned for i in r["identities"]} | set(pids)
    try:
        G.guard_projects(labels, reg, "manifests / lines")
    except Refused as ex:
        problems += ex.problems
    if problems:
        raise Refused(problems)


def guard(*, runs=(), candidates=(), files=None, registry=None, census=False):
    """every check before anything is scored or written. runs = [(side, dir)], candidates = [(side, lines, manifest)],
    files = {role: path} of every other input. -> the guard record (section 6)."""
    reg = G.load_sealed_registry(registry)
    roles = dict(files or {})
    for side, d in runs:
        d = Path(d)
        roles[f"{side}:{RUN_MANIFEST}"] = d / RUN_MANIFEST if (d / RUN_MANIFEST).exists() else None
        for n in (CENSUS_PINNED if census else (LINES,)):
            roles[f"{side}:{n}"] = d / n if (d / n).exists() else None
    for side, lines, man in candidates:
        roles[f"{side}:lines"] = lines
        roles[f"{side}:manifest"] = man
    shas = G.guard_inputs({k: v for k, v in roles.items() if v is not None}, reg)
    pinned = []
    problems = []
    for side, d in runs:
        try:
            pinned.append(pin_run(d, reg, side=side, need=CENSUS_PINNED if census else (LINES,)))
        except Refused as ex:
            problems += ex.problems
    for side, lines, man in candidates:
        try:
            pinned.append(pin_candidate(lines, man, reg, side=side))
        except Refused as ex:
            problems += ex.problems
    if problems:
        raise Refused(problems)
    one_project(pinned, reg)
    unpinned = []
    for side, d in runs:
        d = Path(d)
        extra = [FAMILY_COVERAGE] if census else [Path(RELEASE_REPORT)]
        for rel in extra:
            p = d / rel
            if p.is_file():
                unpinned.append({"role": f"{side}:{rel.as_posix()}", "file": p.name, "sha256": G.sha256_file(p),
                                 "reason": "read from the pinned run folder; the baseline manifest does not hash it"})
    for side, lines, _ in candidates if census else ():
        d = Path(lines).parent
        for rel in ("MATERIAL_RESULTS.json", FAMILY_COVERAGE.as_posix()):
            p = d / rel
            if p.is_file():
                unpinned.append({"role": f"{side}:{rel}", "file": p.name, "sha256": G.sha256_file(p),
                                 "reason": "read beside the candidate lines; the candidate manifest does not hash it"})
    reg_path = Path(registry) if registry else G.DEFAULT_SEALED_REGISTRY
    return {"schema": RECORD_SCHEMA, "sealed_registry": {"file": reg_path.name,
                                                         "sha256": G.sha256_file(reg_path)} if not isinstance(
        registry, dict) else None,
            "inputs": [{"role": k, "file": Path(roles[k]).name, "sha256": v} for k, v in sorted(shas.items())],
            "sides": [r for r, _ in pinned], "not_pinned": sorted(unpinned, key=lambda x: x["role"]),
            "rule": "scored / censused only on pinned runs and candidates, identity by drawing sha256, one project, "
                    "no sealed input (sha256, name, project id); outputs are the unguarded tools' own, byte-identical"}


def _record_text(rec, command):
    return json.dumps({"command": command} | rec, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


# ------------------------------------------------------------------------------------------------------ commands
def cmd_scoreboard(argv):
    ap = argparse.ArgumentParser(prog="scoreboard_guarded.py scoreboard")
    for o in ("--run", "--label", "--reference", "--key-map", "--verdicts", "--out"):
        ap.add_argument(o, required=True)
    for o in ("--candidate-lines", "--candidate-label", "--markdown", "--heading", "--layout",
              "--min-accuracy-scope", "--candidate-manifest", "--sealed-registry", "--guard-record"):
        ap.add_argument(o)
    a = ap.parse_args(argv)
    if a.candidate_manifest and not a.candidate_lines:
        raise Refused([("INPUT_INVALID", "--candidate-manifest without --candidate-lines")])
    rec = guard(runs=[("run", a.run)],
                candidates=[("candidate", a.candidate_lines, a.candidate_manifest)] if a.candidate_lines else [],
                files={"reference": a.reference, "key_map": a.key_map, "verdicts": a.verdicts,
                       f"run:{RELEASE_REPORT}": Path(a.run) / RELEASE_REPORT
                       if (Path(a.run) / RELEASE_REPORT).exists() else None},
                registry=a.sealed_registry)
    from tools import scoreboard_v2 as V2
    v2 = [x for o, val in (("--run", a.run), ("--label", a.label), ("--reference", a.reference),
                           ("--key-map", a.key_map), ("--verdicts", a.verdicts),
                           ("--candidate-lines", a.candidate_lines), ("--candidate-label", a.candidate_label),
                           ("--out", a.out), ("--markdown", a.markdown), ("--heading", a.heading),
                           ("--layout", a.layout), ("--min-accuracy-scope", a.min_accuracy_scope))
          if val is not None for x in (o, val)]
    code = V2.main(v2)
    if a.guard_record:
        Path(a.guard_record).write_text(_record_text(rec, "scoreboard"), encoding="utf-8")
    return code


KEYMAP_GUARDED = ("--run", "--reference", "--key-map", "--set-bindings", "--v2-verdicts", "--v2-candidate-lines")
OWN = ("--candidate-manifest", "--sealed-registry", "--guard-record")


def cmd_keymap(argv):
    if "--openings-register" in argv:
        raise Refused([("INPUT_INVALID", "the openings path of tools/alsenan_keymap.py is not run through this guard")])
    own, rest, i = {}, [], 0
    argv = list(argv)
    while i < len(argv):
        x = argv[i]
        name, eq, val = x.partition("=")
        if name in OWN:
            if eq:
                own[name] = val
                i += 1
            else:
                if i + 1 >= len(argv):
                    raise Refused([("INPUT_INVALID", f"{name} needs a value")])
                own[name] = argv[i + 1]
                i += 2
            continue
        rest.append(x)
        i += 1
    ap = argparse.ArgumentParser(prog="scoreboard_guarded.py keymap", add_help=False)
    for o in KEYMAP_GUARDED:
        ap.add_argument(o)
    a, _ = ap.parse_known_args(rest)
    if a.run is None:
        raise Refused([("INPUT_INVALID", "--run is required")])
    cand = own.get("--candidate-manifest")
    if cand and not a.v2_candidate_lines:
        raise Refused([("INPUT_INVALID", "--candidate-manifest without --v2-candidate-lines")])
    rec = guard(runs=[("run", a.run)],
                candidates=[("candidate", a.v2_candidate_lines, cand)] if a.v2_candidate_lines else [],
                files={"reference": a.reference, "key_map": a.key_map, "set_bindings": a.set_bindings,
                       "v2_verdicts": a.v2_verdicts,
                       f"run:{RELEASE_REPORT}": Path(a.run) / RELEASE_REPORT
                       if (Path(a.run) / RELEASE_REPORT).exists() else None},
                registry=own.get("--sealed-registry"))
    from tools import alsenan_keymap as K
    code = K.main(rest)
    if own.get("--guard-record"):
        Path(own["--guard-record"]).write_text(_record_text(rec, "keymap"), encoding="utf-8")
    return code


def census_rows(lines, run_dir, run_kind, master):
    """census V2 of one side exactly as research/agents_t140/census_run.py calls it (lines, the run's material
    results and route G family coverage)."""
    from engine.source import coverage_census_v2 as CS2
    run_dir = Path(run_dir)
    mp = run_dir / "MATERIAL_RESULTS.json"
    mats = json.loads(mp.read_text(encoding="utf-8"))["results"] if mp.is_file() else ()
    fc = run_dir / FAMILY_COVERAGE
    cov = list(csv.DictReader(fc.open(encoding="utf-8"))) if fc.is_file() else None
    rows, meta = CS2.census(lines, master=master, family_coverage=cov, material_results=mats, run_kind=run_kind)
    return rows, meta, CS2.summary(rows, meta)


def _units(by_unit):
    parts = []
    for u, c in by_unit.items():
        s = f"{u}: " + (f"found {c['found_lines']} = {c['found_qty']:.3f}" if c["found_lines"] else "found 0")
        if c["held_lines"]:
            r = c["held_range"]
            s += f"; held {c['held_lines']} UNKNOWN" + (
                f" (bounded {c['held_bounded_lines']}: {r['low']:.3f} .. {r['high']:.3f}"
                f"{'' if r['complete'] else ', +' + str(c['held_unbounded_lines']) + ' unbounded'})" if r else
                f" ({c['held_unbounded_lines']} unbounded)")
        if c["excluded_lines"]:
            s += f"; excluded {c['excluded_lines']}"
        if c["not_summed_lines"]:
            s += f"; not summed {c['not_summed_lines']}"
        parts.append(s)
    return " | ".join(parts) or "-"


def cmd_census(argv):
    ap = argparse.ArgumentParser(prog="scoreboard_guarded.py census")
    ap.add_argument("--released", action="append", default=[], help="a pinned baseline run folder")
    ap.add_argument("--candidate", action="append", nargs=2, default=[], metavar=("LINES", "MANIFEST"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--sealed-registry")
    a = ap.parse_args(argv)
    if not a.released and not a.candidate:
        raise Refused([("INPUT_INVALID", "nothing to census (--released / --candidate)")])
    out = Path(a.out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise Refused([("INPUT_INVALID", f"--out {out.name} exists and is not empty")])
    runs = [(f"released:{Path(d).name}", d) for d in a.released]
    cands = [(f"candidate:{Path(ln).stem}", ln, m) for ln, m in a.candidate]
    names = [s for s, _ in runs] + [s for s, _, _ in cands]
    if len(set(names)) != len(names):
        raise Refused([("INPUT_INVALID", "two census sides with one name")])
    rec = guard(runs=runs, candidates=cands, registry=a.sealed_registry, census=True)
    from engine.source import coverage_census_v2 as CS2
    master = CS2.load_master()
    results = []
    for side, d in runs:
        results.append((side, G.read_lines(Path(d) / LINES)[0], d, "released"))
    for side, ln, _ in cands:
        results.append((side, G.read_lines(ln)[0], Path(ln).parent, "candidate"))
    out.mkdir(parents=True, exist_ok=True)
    for side, lines, d, kind in results:
        rows, meta, summ = census_rows(lines, d, kind, master)
        name = side.split(":", 1)[1]
        res = {"side": side, "run_kind": kind, "lines": len(lines), "meta": meta, "summary_v2": summ, "rows": rows,
               "pinned_by": next(r for r in rec["sides"] if r["side"] == side)["manifest_sha256"]}
        (out / f"{name}_CENSUS_V2.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True)
                                                    + "\n", encoding="utf-8")
        md = [f"# census V2 of {name} ({kind}): {len(lines)} lines; pinned by manifest {res['pinned_by'][:12]}", "",
              f"V2 {summ['by_run_state']}", "", "| family | unit | capability | V2 state (lines) | quantity per unit "
              "| flags |", "|---|---|---|---|---|---|"]
        md += [f"| {r['code']} | {r['family_unit']} | {r['capability']} | {r['run_state']} ({r['lines']}) | "
               f"{_units(r['by_unit'])} | {'; '.join(r['flags']) or '-'} |" for r in rows]
        (out / f"{name}_CENSUS_V2.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print(name, kind, len(lines), summ["by_run_state"])
    (out / "GUARD_RECORD.json").write_text(_record_text(rec, "census"), encoding="utf-8")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if not argv or argv[0] not in ("scoreboard", "keymap", "census"):
        print("usage: scoreboard_guarded.py scoreboard|keymap|census ...", file=sys.stderr)
        return 2
    try:
        return {"scoreboard": cmd_scoreboard, "keymap": cmd_keymap, "census": cmd_census}[argv[0]](argv[1:])
    except Refused as ex:
        for code, text in ex.problems:
            print(f"SCOREBOARD REFUSED [{code}]: {text}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
