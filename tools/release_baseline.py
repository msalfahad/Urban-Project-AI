"""RELEASE BASELINE RUNNER (T-165): one pinned definition of a baseline run of the released architectural method + route
G, so that every Gate B diff, coverage census and scoreboard can name exactly which run it compares against.

    python3 -I tools/release_baseline.py run SPEC.json --plan PLAN.dxf [--structural ST.dxf] --out DIR
    python3 -I tools/release_baseline.py compare A/BASELINE_MANIFEST.json B/BASELINE_MANIFEST.json [--out DIFF.json]

SPEC (URBAN_BASELINE_SPEC_V1) pins every input of the run by sha256; nothing is defaulted. Every key below is required
(null is written out, never left away, so "no profile" is a stated choice):

    baseline_id   short name (written into the manifest)
    method        one of tools/urban_boq_m9.py ARCH_METHODS (the opt-in candidates have their own runners)
    python        "3.11": the major.minor the run must use (frozen rebuilds differ by one ulp on 3.13)
    inputs        {"plan": {"sha256", "size"?}, "structural": {"sha256", "size"?} | null}: the drawings, given on the
                  command line (they are private and stay outside the repository); only their sha256 is pinned
    conventions   {"path", "sha256"} | null   route G conventions profile (--conventions)
    profile       {"path", "sha256"} | null   route G drawing profile (--profile)
    facts         {"path", "sha256"} | null   project facts (--facts)
    project       str | null                  project id (--project): it enters every line_id hash, so two runs with
                                              different ids pair no line by id
    as_of         "YYYY-MM-DD"                the structural report date (--as-of; its default is today's date)
    options       {"no_svg": bool, "no_m9_xlsx": bool, "no_completeness": bool}
    description   optional free text; expected: optional {"line_count": int, "boq_lines_csv_sha256": str}

A relative path is read from the repository root; an absolute path as given. The runner REFUSES (exit 2, nothing run,
nothing written) when the spec is malformed, a pinned file is missing, any sha256 differs, a drawing is given that the
spec does not pin (or the reverse), the interpreter is not the pinned major.minor, or --out exists and is not empty.

After the run it writes BASELINE_MANIFEST.json (URBAN_BASELINE_MANIFEST_V1) beside the run's outputs: the spec and its
sha256, the engine commit and whether engine / tools / rules / knowledge / data had uncommitted changes, the inputs
(file name, size, sha256; never a path), the method, the line count and evidence-state counts, the sha256 of
BOQ_LINES.csv / BOQ_LINES.json / MATERIAL_RESULTS.json / COVERAGE.json, and one figure set per item code and unit:
lines, released lines and their quantity (evidence state MEASURED / SOURCE_DERIVED / PROVISIONAL with a measured_net,
UP-QTY-STATUS-001), held lines (every other state except the two exclusions) with their bounded low / high where the
line gives one, and excluded lines. A held line never carries a quantity and an absent figure is null, never 0; units
are never mixed. Two runs of one spec on one commit give byte-identical manifests (no timestamp, no path).
Exit: 0 run done (and the expected figures matched, when given); 3 the expected figures did not match; 4 the engine
exited non-zero (the manifest records it).

compare prints the pinned-configuration differences of two manifests (method, inputs, conventions, profile, facts,
project, options), every item code / unit whose figures differ (the side-by-side table of two baselines), whether the
hashed outputs are identical and whether the engine commit is the same. A reproduction on another commit (e.g. the
Checker's merge) is: 0 configuration differences, 0 figure differences, identical hashed outputs.

Reads the engine; computes, changes and approves no quantity; nothing imports this module (rollback: delete it).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SPEC_SCHEMA = "URBAN_BASELINE_SPEC_V1"
MANIFEST_SCHEMA = "URBAN_BASELINE_MANIFEST_V1"
MANIFEST_NAME = "BASELINE_MANIFEST.json"
REQUIRED_KEYS = ("schema", "baseline_id", "method", "python", "inputs", "conventions", "profile", "facts", "project",
                 "as_of", "options")
OPTIONAL_KEYS = ("description", "expected")
PINNED_FILES = ("conventions", "profile", "facts")
OPTION_FLAGS = {"no_svg": "--no-svg", "no_m9_xlsx": "--no-m9-xlsx", "no_completeness": "--no-completeness"}
HASHED_OUTPUTS = ("BOQ_LINES.csv", "BOQ_LINES.json", "MATERIAL_RESULTS.json", "COVERAGE.json")
QUANTITY_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")      # engine/source/boq_line.py QUANTITY_STATES
EXCLUDED_STATES = ("EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE")
TRACKED_DIRS = ("engine", "tools", "rules", "knowledge", "data")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class Refused(Exception):
    """the run is refused before anything is run or written; .problems lists every reason found."""

    def __init__(self, problems):
        self.problems = list(problems)
        super().__init__("; ".join(self.problems))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _arch_methods():
    from tools import urban_boq_m9 as M
    return tuple(M.ARCH_METHODS)


def validate_spec(spec, methods=None):
    """the list of problems of a spec (empty = valid). Never fills a missing key."""
    p = []
    if not isinstance(spec, dict):
        return ["spec is not a JSON object"]
    if spec.get("schema") != SPEC_SCHEMA:
        p.append(f"schema must be {SPEC_SCHEMA}")
    for k in REQUIRED_KEYS:
        if k not in spec:
            p.append(f"key '{k}' missing (write null to state 'none')")
    for k in spec:
        if k not in REQUIRED_KEYS + OPTIONAL_KEYS:
            p.append(f"unknown key '{k}'")
    if not isinstance(spec.get("baseline_id"), str) or not spec.get("baseline_id"):
        p.append("baseline_id must be a non-empty string")
    methods = methods if methods is not None else _arch_methods()
    if spec.get("method") not in methods:
        p.append(f"method {spec.get('method')!r} is not one of tools/urban_boq_m9.py ARCH_METHODS")
    if not isinstance(spec.get("python"), str) or not re.match(r"^\d+\.\d+$", spec.get("python") or ""):
        p.append("python must be 'major.minor', e.g. '3.11'")
    inp = spec.get("inputs")
    if not isinstance(inp, dict) or set(inp) != {"plan", "structural"}:
        p.append("inputs must be {'plan': {...}, 'structural': {...} | null}")
    else:
        for role in ("plan", "structural"):
            e = inp[role]
            if e is None and role == "structural":
                continue
            if not isinstance(e, dict) or not SHA_RE.match(str(e.get("sha256", ""))) or \
                    set(e) - {"sha256", "size"} or ("size" in e and not isinstance(e["size"], int)):
                p.append(f"inputs.{role} must be {{'sha256': 64 hex, 'size'?: int}}")
    for k in PINNED_FILES:
        e = spec.get(k)
        if e is None:
            continue
        if not isinstance(e, dict) or set(e) != {"path", "sha256"} or not isinstance(e["path"], str) or \
                not SHA_RE.match(str(e["sha256"])):
            p.append(f"{k} must be {{'path': str, 'sha256': 64 hex}} or null")
    if isinstance(inp, dict) and inp.get("structural") is None and any(spec.get(k) for k in ("conventions", "profile")):
        p.append("conventions / profile need a structural input")
    if spec.get("project") is not None and (not isinstance(spec["project"], str) or not spec["project"]):
        p.append("project must be a non-empty string or null")
    if not isinstance(spec.get("as_of"), str) or not DATE_RE.match(spec.get("as_of") or ""):
        p.append("as_of must be 'YYYY-MM-DD'")
    opt = spec.get("options")
    if not isinstance(opt, dict) or set(opt) != set(OPTION_FLAGS) or not all(isinstance(v, bool) for v in opt.values()):
        p.append(f"options must give every one of {sorted(OPTION_FLAGS)} as true / false")
    exp = spec.get("expected")
    if exp is not None:
        if not isinstance(exp, dict) or not exp or set(exp) - {"line_count", "boq_lines_csv_sha256"}:
            p.append("expected must be {'line_count'?: int, 'boq_lines_csv_sha256'?: 64 hex}")
        else:
            if "line_count" in exp and (not isinstance(exp["line_count"], int) or isinstance(exp["line_count"], bool)):
                p.append("expected.line_count must be an int")
            if "boq_lines_csv_sha256" in exp and not SHA_RE.match(str(exp["boq_lines_csv_sha256"])):
                p.append("expected.boq_lines_csv_sha256 must be 64 hex")
    return p


def _resolve(path):
    q = Path(path)
    return q if q.is_absolute() else ROOT / q


def _shown(path):
    """a pinned file as the manifest shows it: repository-relative inside the repository, else its file name only."""
    q = _resolve(path).resolve()
    try:
        return q.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return q.name


def check_pinned(spec, plan, structural, *, python_version=None):
    """every pinned item against what is on disk; raises Refused with every problem; returns the input records."""
    p = []
    ver = python_version or f"{sys.version_info.major}.{sys.version_info.minor}"
    if ver != spec["python"]:
        p.append(f"interpreter is Python {ver}, the spec pins {spec['python']}")
    given = {"plan": plan, "structural": structural}
    records = []
    for role in ("plan", "structural"):
        pin, f = spec["inputs"][role], given[role]
        if pin is None and f is None:
            continue
        if pin is None:
            p.append(f"--{role} given but the spec pins no {role} drawing")
            continue
        if f is None:
            p.append(f"the spec pins a {role} drawing but --{role} is not given")
            continue
        f = Path(f)
        if not f.is_file():
            p.append(f"{role} drawing missing: {f.name}")
            continue
        sha, size = sha256_file(f), f.stat().st_size
        if sha != pin["sha256"]:
            p.append(f"{role} drawing sha256 {sha} differs from the pinned {pin['sha256']}")
        if "size" in pin and size != pin["size"]:
            p.append(f"{role} drawing size {size} differs from the pinned {pin['size']}")
        records.append({"role": role, "file": f.name, "size": size, "sha256": sha})
    for k in PINNED_FILES:
        e = spec[k]
        if e is None:
            continue
        f = _resolve(e["path"])
        if not f.is_file():
            p.append(f"{k} file missing: {e['path']}")
            continue
        sha = sha256_file(f)
        if sha != e["sha256"]:
            p.append(f"{k} file sha256 {sha} differs from the pinned {e['sha256']} ({e['path']})")
    if p:
        raise Refused(p)
    return records


def engine_argv(spec, plan, structural, out):
    a = ["arch", "--drawings", str(plan), "--out", str(out), "--method", spec["method"], "--as-of", spec["as_of"]]
    if structural is not None:
        a += ["--structural", str(structural)]
    for k, flag in (("conventions", "--conventions"), ("profile", "--profile"), ("facts", "--facts")):
        if spec[k] is not None:
            a += [flag, str(_resolve(spec[k]["path"]))]
    if spec["project"] is not None:
        a += ["--project", spec["project"]]
    a += [flag for k, flag in OPTION_FLAGS.items() if spec["options"][k]]
    return a


def per_code(lines):
    """one figure set per (item_code, unit), sorted; a held line never carries a quantity, an absent figure is None."""
    acc = {}
    for ln in lines:
        k = (ln["item_code"], ln["unit"])
        o = acc.setdefault(k, {"item_code": k[0], "unit": k[1], "lines": 0, "released_lines": 0, "released_qty": 0.0,
                               "held_lines": 0, "held_bounded_lines": 0, "held_low": 0.0, "held_high": 0.0,
                               "excluded_lines": 0, "states": {}})
        o["lines"] += 1
        s = ln.get("evidence_state")
        o["states"][s] = o["states"].get(s, 0) + 1
        if s in QUANTITY_STATES and ln.get("measured_net") is not None:
            o["released_lines"] += 1
            o["released_qty"] += ln["measured_net"]
        elif s in EXCLUDED_STATES:
            o["excluded_lines"] += 1
        else:
            o["held_lines"] += 1
            b = ln.get("bounded_range") or {}
            if b.get("low") is not None and b.get("high") is not None:
                o["held_bounded_lines"] += 1
                o["held_low"] += b["low"]
                o["held_high"] += b["high"]
    out = []
    for k in sorted(acc):
        o = acc[k]
        o["released_qty"] = round(o["released_qty"], 3) if o["released_lines"] else None
        if o["held_bounded_lines"]:
            o["held_low"], o["held_high"] = round(o["held_low"], 3), round(o["held_high"], 3)
        else:
            o["held_low"] = o["held_high"] = None
        o["held_unbounded_lines"] = o["held_lines"] - o["held_bounded_lines"]
        o["states"] = dict(sorted(o["states"].items()))
        out.append(o)
    return out


def engine_identity():
    def git(*a):
        try:
            r = subprocess.run(["git", "-C", str(ROOT)] + list(a), capture_output=True, text=True, timeout=60)
            return r.stdout.strip() if r.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None
    head = git("rev-parse", "HEAD")
    status = git("status", "--porcelain", "--untracked-files=all", "--", *TRACKED_DIRS)
    return {"commit": head or "UNKNOWN",
            "tracked_dirs": list(TRACKED_DIRS),
            "tree": "UNKNOWN" if status is None else ("CLEAN" if status == "" else "MODIFIED"),
            "modified_files": sorted(x[3:] for x in status.splitlines()) if status else []}


def build_manifest(spec, spec_sha, inputs, out, exit_code, identity):
    out = Path(out)
    lines_p = out / "BOQ_LINES.json"
    lines = None
    if lines_p.is_file():
        raw = json.loads(lines_p.read_text(encoding="utf-8"))
        lines = raw["lines"] if isinstance(raw, dict) else raw
    states = {}
    for ln in lines or ():
        states[ln.get("evidence_state")] = states.get(ln.get("evidence_state"), 0) + 1
    files = {n: (sha256_file(out / n) if (out / n).is_file() else None) for n in HASHED_OUTPUTS}
    got = {"line_count": None if lines is None else len(lines), "boq_lines_csv_sha256": files["BOQ_LINES.csv"]}
    exp = spec.get("expected")
    check = None
    if exp:
        check = {k: {"expected": v, "got": got[k], "match": v == got[k]} for k, v in sorted(exp.items())}
    if exit_code != 0:
        status = "ENGINE_EXIT_NONZERO"
    elif check is None:
        status = "RUN_NO_EXPECTED_FIGURES"
    else:
        status = "REPRODUCED" if all(c["match"] for c in check.values()) else "NOT_REPRODUCED"
    pinned = {k: (None if spec[k] is None else {"file": _shown(spec[k]["path"]), "sha256": spec[k]["sha256"]})
              for k in PINNED_FILES}
    shown_spec = json.loads(json.dumps(spec))
    for k in PINNED_FILES:
        if shown_spec[k] is not None:
            shown_spec[k]["path"] = _shown(shown_spec[k]["path"])
    return {"schema": MANIFEST_SCHEMA, "baseline_id": spec["baseline_id"], "status": status,
            "spec": shown_spec, "spec_sha256": spec_sha,
            "engine": identity, "python": spec["python"], "method": spec["method"],
            "inputs": inputs, "pinned_files": pinned, "project": spec["project"], "as_of": spec["as_of"],
            "options": spec["options"],
            "run": {"exit_code": exit_code, "line_count": got["line_count"],
                    "evidence_states": dict(sorted((str(k), v) for k, v in states.items())), "outputs_sha256": files},
            "expected_check": check,
            "per_code": None if lines is None else per_code(lines),
            "rule": "released = MEASURED / SOURCE_DERIVED / PROVISIONAL with measured_net (UP-QTY-STATUS-001); "
                    "held carries no quantity (bounded low / high only where the line gives both); null is "
                    "'no figure', never 0; units never mixed"}


def dumps(manifest):
    return json.dumps(manifest, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def _default_engine(argv):
    from tools import urban_boq_m9 as M
    try:
        r = M.main(argv)
    except SystemExit as ex:
        r = ex.code if isinstance(ex.code, int) else 1
    return 0 if r is None else int(r)


def run(spec_path, plan, structural, out, *, engine=None, python_version=None):
    """(exit code, manifest or None). Refused -> raises Refused before anything is run or written."""
    spec_path = Path(spec_path)
    if not spec_path.is_file():
        raise Refused([f"spec missing: {spec_path.name}"])
    spec_bytes = spec_path.read_bytes()
    try:
        spec = json.loads(spec_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as ex:
        raise Refused([f"spec is not valid JSON: {ex}"]) from None
    problems = validate_spec(spec)
    if problems:
        raise Refused(problems)
    out = Path(out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise Refused([f"--out {out.name} exists and is not empty (a baseline is written into an empty folder)"])
    inputs = check_pinned(spec, plan, structural, python_version=python_version)
    identity = engine_identity()
    out.mkdir(parents=True, exist_ok=True)
    code = (engine or _default_engine)(engine_argv(spec, Path(plan), None if structural is None else Path(structural),
                                                   out))
    m = build_manifest(spec, hashlib.sha256(spec_bytes).hexdigest(), inputs, out, code, identity)
    (out / MANIFEST_NAME).write_text(dumps(m), encoding="utf-8")
    return {"REPRODUCED": 0, "RUN_NO_EXPECTED_FIGURES": 0, "NOT_REPRODUCED": 3}.get(m["status"], 4), m


CONFIG_FIELDS = ("method", "python", "inputs", "pinned_files", "project", "as_of", "options")
FIGURES = ("lines", "released_lines", "released_qty", "held_lines", "held_bounded_lines", "held_low", "held_high",
           "held_unbounded_lines", "excluded_lines", "states")


def compare(a, b):
    """configuration differences and per item code / unit figure differences of two manifests."""
    cfg = [{"field": f, "a": a.get(f), "b": b.get(f)} for f in CONFIG_FIELDS if a.get(f) != b.get(f)]
    ia = {(r["item_code"], r["unit"]): r for r in a.get("per_code") or ()}
    ib = {(r["item_code"], r["unit"]): r for r in b.get("per_code") or ()}
    rows = []
    for k in sorted(set(ia) | set(ib)):
        ra, rb = ia.get(k), ib.get(k)
        diff = [f for f in FIGURES if (ra or {}).get(f) != (rb or {}).get(f)] if ra and rb else ["*"]
        if diff:
            rows.append({"item_code": k[0], "unit": k[1], "differs": diff,
                         "a": None if ra is None else {f: ra[f] for f in FIGURES},
                         "b": None if rb is None else {f: rb[f] for f in FIGURES}})
    return {"a": {"baseline_id": a.get("baseline_id"), "line_count": (a.get("run") or {}).get("line_count"),
                  "boq_lines_csv_sha256": ((a.get("run") or {}).get("outputs_sha256") or {}).get("BOQ_LINES.csv")},
            "b": {"baseline_id": b.get("baseline_id"), "line_count": (b.get("run") or {}).get("line_count"),
                  "boq_lines_csv_sha256": ((b.get("run") or {}).get("outputs_sha256") or {}).get("BOQ_LINES.csv")},
            "config_differences": cfg, "codes_compared": len(set(ia) | set(ib)), "codes_differing": len(rows),
            "same_outputs": (a.get("run") or {}).get("outputs_sha256") == (b.get("run") or {}).get("outputs_sha256"),
            "same_engine_commit": (a.get("engine") or {}).get("commit") == (b.get("engine") or {}).get("commit"),
            "rows": rows}


def _fmt(r):
    if r is None:
        return "absent"
    q = "-" if r["released_qty"] is None else f"{r['released_qty']:.3f}"
    h = f"held {r['held_lines']}"
    if r["held_bounded_lines"]:
        h += f" ({r['held_bounded_lines']} bounded {r['held_low']:.3f} .. {r['held_high']:.3f})"
    return f"{r['lines']} lines, released {r['released_lines']} = {q}, {h}, excluded {r['excluded_lines']}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("spec")
    r.add_argument("--plan", required=True)
    r.add_argument("--structural")
    r.add_argument("--out", required=True)
    c = sub.add_parser("compare")
    c.add_argument("a")
    c.add_argument("b")
    c.add_argument("--out")
    a = ap.parse_args(argv)
    if a.cmd == "run":
        try:
            code, m = run(a.spec, a.plan, a.structural, a.out)
        except Refused as ex:
            for x in ex.problems:
                print(f"BASELINE REFUSED: {x}", file=sys.stderr)
            return 2
        print(f"{m['baseline_id']}: {m['status']}, {m['run']['line_count']} lines, BOQ_LINES.csv "
              f"{m['run']['outputs_sha256']['BOQ_LINES.csv']}, engine {m['engine']['commit'][:12]} "
              f"({m['engine']['tree']}) -> {Path(a.out) / MANIFEST_NAME}")
        return code
    ma = json.loads(Path(a.a).read_text(encoding="utf-8"))
    mb = json.loads(Path(a.b).read_text(encoding="utf-8"))
    for m, n in ((ma, a.a), (mb, a.b)):
        if m.get("schema") != MANIFEST_SCHEMA:
            print(f"COMPARE REFUSED: {Path(n).name} is not a {MANIFEST_SCHEMA}", file=sys.stderr)
            return 2
    d = compare(ma, mb)
    if a.out:
        Path(a.out).write_text(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"A {d['a']['baseline_id']} ({d['a']['line_count']} lines) vs B {d['b']['baseline_id']} "
          f"({d['b']['line_count']} lines): {len(d['config_differences'])} configuration differences, "
          f"{d['codes_differing']} of {d['codes_compared']} item code / unit figure sets differ; hashed outputs "
          f"{'identical' if d['same_outputs'] else 'DIFFER'}; engine commit "
          f"{'same' if d['same_engine_commit'] else 'DIFFERS'}")
    for x in d["config_differences"]:
        print(f"  config {x['field']}: A {json.dumps(x['a'], sort_keys=True)} | B {json.dumps(x['b'], sort_keys=True)}")
    for x in d["rows"]:
        print(f"  {x['item_code']} {x['unit']}: A {_fmt(x['a'])} | B {_fmt(x['b'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
