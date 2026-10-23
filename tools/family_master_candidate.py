"""FAMILY MASTER CANDIDATE STATES (T-203): check the candidate-level state of every BOQ family in a family master that
carries one (rules/coverage/BOQ_FAMILY_MASTER_1.2.0.json and later versions).

    python3 -I tools/family_master_candidate.py check [MASTER.json]     exit 0 = no problem, 1 = problems (printed)

Why a candidate-level state: the registry's capability states are defined against the RELEASED configuration
(ARCH_TAKEOFF_V2.9 + route G). While that stays released, an integration into the opt-in candidate ARCH_TAKEOFF_V3.0.x
can never raise them, so the registry showed nothing of what the candidate integrates and tests (pilot 2026-10-23,
prerequisite 6). The candidate state answers that question on its own, beside the unchanged released states:

    INTEGRATED_IN_CANDIDATE_AND_TESTED  a merged candidate package wired a checker-verified piece into this family's
                                        candidate lines, under that package's tests and checker verdict; HELD /
                                        UNKNOWN lines may remain and are named in 'open' (never counted as correct)
    HELD_IN_CANDIDATE                   a merged candidate package changed this family's candidate lines, and the
                                        candidate releases no quantity of the family: every named line is held,
                                        blocked or a placeholder ('released_in_candidate' = "none")
    IN_CANDIDATE_BASE_LINES             the candidate emits the family's lines as its base run gives them; no package
                                        changed them (each Gate B since asserted them byte-identical: regression,
                                        not verification)
    NOT_IN_CANDIDATE                    the candidate emits no line of the family

Rules checked (every one refuses, none repairs):
  - the vocabulary is exactly the four states above, each with a definition; counts equal the families;
  - every package in 'candidate_packages' carries a task id, a method version of the candidate, a module that exists,
    a 40-hex merge commit, a checker verdict that starts with MERGED and names the verifier and a UTC time, the input
    tasks it integrates and at least one test folder that exists; when git is given, the merge commit must be an
    ancestor of the checked head (a READY or rejected package is never a merged package);
  - the candidate's method version is the newest package's method version;
  - every family carries 'candidate' with a state, the candidate method version and 'as_of_package' naming a merged
    package; the two package-backed states name at least one package of their own; IN_CANDIDATE_BASE_LINES and
    NOT_IN_CANDIDATE name none; a named package must be at or below the candidate version (no future package);
  - 'in_v3_0_candidate' agrees with the state (yes for the first three, no for NOT_IN_CANDIDATE);
  - HELD_IN_CANDIDATE says released_in_candidate "none"; INTEGRATED_IN_CANDIDATE_AND_TESTED names what changed and
    what stays open;
  - (r2, from the T-203 r1 rejection) a package may say which families it took to "no quantity released" ('holds')
    or released a quantity of again ('releases'); each named family must name that package, and a family whose last
    such event (in version order) is 'releases' can never be HELD_IN_CANDIDATE;
  - (r2) the head carries no candidate module newer than the registry's candidate: an engine/source/arch_v30*.py whose
    version is above candidate.method_version means a newer package merged and the registry's as_of is stale
    (scan_head=False only for synthetic registries checked outside this repository's head);
  - (r3, T-231) a package cannot name its own merge commit before the Checker merges it, so a registry version may
    declare 'pending_packages': a candidate package handed in for Gate B (task, method_version above the candidate's,
    its module, the 40-hex task commit that adds the module, status READY_FOR_GATE_B, the tasks it integrates, its test
    folders). A pending package is never a merged package: no family state may name it, it is not in
    candidate_packages, and it raises no candidate state. A newer module on the head is not stale when THIS registry
    declares it pending, or when a NEWER registry version on the head (rules/coverage/BOQ_FAMILY_MASTER_x.y.z.json)
    accounts for it (merged or pending): a superseded version is not the registry of record. The next registry
    version after the merge moves the package to candidate_packages with its merge commit and verdict.

Read by no engine method and by no run: it changes no quantity, no release state and no default.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.3.0.json"   # T-231: the registry of record
# T-212 default-guard property: registry check only, read by no method or run, emits no BOQ quantity of its own
DEFAULT_GUARD_CLASS = "TOOLING"

STATES = ("INTEGRATED_IN_CANDIDATE_AND_TESTED", "HELD_IN_CANDIDATE", "IN_CANDIDATE_BASE_LINES", "NOT_IN_CANDIDATE")
PACKAGE_BACKED = STATES[:2]
SHA40 = re.compile(r"^[0-9a-f]{40}$")
TASK = re.compile(r"^T-\d{3}[a-z]?$")
VERDICT = re.compile(r"^MERGED\b.*\b(?:verifier|Verifier|checker|Checker)\b.*\b20\d\d-\d\d-\d\d \d\d:\d\d UTC\b")
VERSION = re.compile(r"^ARCH_TAKEOFF_V3\.0(?:\.(\d+))?$")
MODULE = re.compile(r"^arch_v30(\d*)\.py$")


def version_key(v):
    """ARCH_TAKEOFF_V3.0 -> 0, ARCH_TAKEOFF_V3.0.6 -> 6; None when the text is not a candidate version."""
    m = VERSION.match(v or "")
    return None if not m else int(m.group(1) or 0)


def head_candidate_modules(root=ROOT):
    """{version number: path} of every candidate module engine/source/arch_v30[N].py on the tree at root."""
    out = {}
    d = Path(root) / "engine/source"
    for f in sorted(d.glob("arch_v30*.py")) if d.is_dir() else []:
        m = MODULE.match(f.name)
        if m:
            out[int(m.group(1) or 0)] = f"engine/source/{f.name}"
    return out


def git_is_ancestor(commit, head="HEAD", root=ROOT):
    """True when commit is an ancestor of head in the repository at root (git merge-base --is-ancestor)."""
    r = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", commit, head],
                       capture_output=True, text=True)
    return r.returncode == 0


def _semver(v):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except ValueError:
        return None


def newer_registry_modules(doc, root=ROOT):
    """{module path: registry version} accounted for (merged or pending) by every registry version on the tree at root
    that is newer than doc's version."""
    out = {}
    mine = _semver(doc.get("version"))
    d = Path(root) / "rules/coverage"
    for f in sorted(d.glob("BOQ_FAMILY_MASTER_*.json")) if d.is_dir() and mine else []:
        try:
            other = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        ov = _semver(other.get("version"))
        if ov is None or ov <= mine:
            continue
        for p in list(other.get("candidate_packages") or []) + list(other.get("pending_packages") or []):
            if p.get("module"):
                out[p["module"]] = other.get("version")
    return out


PENDING_STATUS = "READY_FOR_GATE_B"


def check_pending(doc, by_task, mv, root=ROOT, is_ancestor=None):
    """r3: the pending packages of a registry version. -> (problems, {module: version number})"""
    bad, mods = [], {}
    pend = doc.get("pending_packages")
    if pend is None:
        return bad, mods
    if not isinstance(pend, list):
        return ["pending_packages must be a list"], mods
    seen = set()
    for p in pend:
        t = p.get("task", "?")
        if not TASK.match(str(t)):
            bad.append(f"pending package {t}: task id is not T-nnn")
        if t in by_task:
            bad.append(f"pending package {t}: also a merged package (a package is pending or merged, never both)")
        if t in seen:
            bad.append(f"pending package {t}: listed twice")
        seen.add(t)
        vk = version_key(p.get("method_version"))
        if vk is None:
            bad.append(f"pending package {t}: method_version {p.get('method_version')!r} is not a candidate version")
        elif version_key(mv) is not None and vk <= version_key(mv):
            bad.append(f"pending package {t}: {p.get('method_version')} is not above the candidate {mv}")
        mod = p.get("module")
        m = MODULE.match(Path(str(mod)).name) if mod else None
        if not mod or not (root / mod).is_file() or not m:
            bad.append(f"pending package {t}: module {mod!r} does not exist or is not a candidate module")
        elif vk is not None and int(m.group(1) or 0) != vk:
            bad.append(f"pending package {t}: module {mod} is not the module of {p.get('method_version')}")
        else:
            mods[mod] = vk
        tc = p.get("task_commit", "")
        if not SHA40.match(str(tc)):
            bad.append(f"pending package {t}: task_commit {tc!r} is not a full 40-hex sha")
        elif is_ancestor is not None and not is_ancestor(tc):
            bad.append(f"pending package {t}: task_commit {tc[:10]} is not on the checked head")
        if p.get("status") != PENDING_STATUS:
            bad.append(f"pending package {t}: status must be {PENDING_STATUS} (a pending package is never merged)")
        if "verdict" in p or "merge_commit" in p:
            bad.append(f"pending package {t}: carries a verdict / merge commit: a merged package goes to "
                       "candidate_packages in the next registry version")
        if not p.get("integrates") or not all(TASK.match(str(x)) for x in p["integrates"]):
            bad.append(f"pending package {t}: 'integrates' must list the merged input tasks")
        tests = p.get("tests") or []
        if not tests:
            bad.append(f"pending package {t}: no test folder")
        for d in tests:
            if not (root / d).is_dir():
                bad.append(f"pending package {t}: test folder {d} does not exist")
    for f in doc.get("families", []):
        named = (f.get("candidate") or {}).get("packages") or []
        for t in named:
            if t in seen:
                bad.append(f"{f.get('code')}: names the pending package {t} (a candidate state needs a merged verdict)")
    return bad, mods


def check(doc, root=ROOT, is_ancestor=None, scan_head=True):
    """Return a list of problems (empty = the candidate states hold). is_ancestor(commit) -> bool, optional.
    scan_head: refuse when the tree at root carries a candidate module newer than the registry's candidate that neither
    this registry declares pending nor a newer registry version on the tree accounts for."""
    bad = []
    states = doc.get("candidate_states")
    if tuple(states or ()) != STATES:
        bad.append(f"candidate_states must be exactly {list(STATES)}, got {states}")
    defs = doc.get("candidate_state_definitions") or {}
    if set(defs) != set(STATES) or not all(isinstance(defs[s], str) and defs[s].strip() for s in defs):
        bad.append("candidate_state_definitions must define every candidate state")

    pkgs = doc.get("candidate_packages")
    by_task = {}
    if not isinstance(pkgs, list) or not pkgs:
        bad.append("candidate_packages missing or empty")
        pkgs = []
    for p in pkgs:
        t = p.get("task", "?")
        if not TASK.match(str(t)):
            bad.append(f"package {t}: task id is not T-nnn")
        if t in by_task:
            bad.append(f"package {t}: listed twice")
        by_task[t] = p
        if version_key(p.get("method_version")) is None:
            bad.append(f"package {t}: method_version {p.get('method_version')!r} is not an ARCH_TAKEOFF_V3.0.x candidate")
        mod = p.get("module")
        if not mod or not (root / mod).is_file():
            bad.append(f"package {t}: module {mod!r} does not exist")
        mc = p.get("merge_commit", "")
        if not SHA40.match(str(mc)):
            bad.append(f"package {t}: merge_commit {mc!r} is not a full 40-hex sha (a package without a merge is not merged)")
        elif is_ancestor is not None and not is_ancestor(mc):
            bad.append(f"package {t}: merge_commit {mc[:10]} is not on the checked head (not merged)")
        if not VERDICT.match(str(p.get("verdict", ""))):
            bad.append(f"package {t}: no checker verdict (must start with MERGED and name the verifier and a UTC time)")
        if not p.get("integrates") or not all(TASK.match(str(x)) for x in p["integrates"]):
            bad.append(f"package {t}: 'integrates' must list the merged input tasks")
        tests = p.get("tests") or []
        if not tests:
            bad.append(f"package {t}: no test folder")
        for d in tests:
            if not (root / d).is_dir():
                bad.append(f"package {t}: test folder {d} does not exist")
    newest = max((version_key(p.get("method_version")) or 0 for p in pkgs), default=None)

    cand = doc.get("candidate") or {}
    mv = cand.get("method_version")
    if version_key(mv) is None:
        bad.append(f"candidate.method_version {mv!r} is not a candidate version")
    elif newest is not None and version_key(mv) != newest:
        bad.append(f"candidate.method_version {mv} is not the newest merged package's version")
    if cand.get("as_of_package") not in by_task:
        bad.append(f"candidate.as_of_package {cand.get('as_of_package')!r} is not a listed merged package")
    elif version_key(by_task[cand["as_of_package"]].get("method_version")) != version_key(mv):
        bad.append(f"candidate.as_of_package {cand['as_of_package']} is not the package of {mv}")
    pbad, pending = check_pending(doc, by_task, mv, root, is_ancestor)
    bad += pbad
    if scan_head and version_key(mv) is not None:
        newer = newer_registry_modules(doc, root)
        for n, path in sorted(head_candidate_modules(root).items()):
            if n > version_key(mv) and pending.get(path) != n and path not in newer:
                bad.append(f"the head carries {path} (ARCH_TAKEOFF_V3.0.{n}), newer than the registry's candidate {mv}: "
                           "a newer package merged and the registry's as_of is stale")

    # holds / releases trace, in version order: the last event decides whether HELD_IN_CANDIDATE is still possible
    fam_by_code = {f.get("code"): f for f in doc.get("families", [])}
    last_event = {}
    for p in sorted(pkgs, key=lambda q: version_key(q.get("method_version")) or 0):
        for ev in ("holds", "releases"):
            codes = p.get(ev, [])
            if not isinstance(codes, list):
                bad.append(f"package {p.get('task')}: '{ev}' must be a list of family codes")
                continue
            for code in codes:
                f = fam_by_code.get(code)
                if f is None:
                    bad.append(f"package {p.get('task')}: '{ev}' names {code!r}, not a family of this registry")
                    continue
                if p.get("task") not in ((f.get("candidate") or {}).get("packages") or []):
                    bad.append(f"{code}: package {p.get('task')} {ev} it, but its candidate block does not name that package")
                last_event[code] = (ev, p.get("task"))
    for code, (ev, t) in last_event.items():
        c = fam_by_code[code].get("candidate") or {}
        if ev == "releases" and c.get("state") == "HELD_IN_CANDIDATE":
            bad.append(f"{code}: HELD_IN_CANDIDATE, but package {t} released a quantity of the family (stale state)")

    counts = {s: 0 for s in STATES}
    yes_no = {"yes": 0, "no": 0}
    for f in doc.get("families", []):
        code = f.get("code", "?")
        c = f.get("candidate")
        if not isinstance(c, dict):
            bad.append(f"{code}: no candidate block")
            continue
        s = c.get("state")
        if s not in STATES:
            bad.append(f"{code}: candidate state {s!r} not in the vocabulary")
            continue
        counts[s] += 1
        if c.get("method_version") != mv:
            bad.append(f"{code}: candidate method_version {c.get('method_version')!r} != {mv}")
        if c.get("as_of_package") not in by_task:
            bad.append(f"{code}: as_of_package {c.get('as_of_package')!r} is not a merged package")
        named = c.get("packages")
        if not isinstance(named, list):
            bad.append(f"{code}: 'packages' must be a list")
            named = []
        for t in named:
            if t not in by_task:
                bad.append(f"{code}: state {s} names package {t}, which is not a merged package (claimed without a verdict)")
            elif version_key(by_task[t].get("method_version")) is not None and version_key(mv) is not None \
                    and version_key(by_task[t]["method_version"]) > version_key(mv):
                bad.append(f"{code}: package {t} is newer than the candidate version")
        if s in PACKAGE_BACKED and not named:
            bad.append(f"{code}: state {s} names no package (a candidate state is claimed only with a merged verdict)")
        if s not in PACKAGE_BACKED and named:
            bad.append(f"{code}: state {s} must name no package of its own")
        want = "no" if s == "NOT_IN_CANDIDATE" else "yes"
        if f.get("in_v3_0_candidate") != want:
            bad.append(f"{code}: in_v3_0_candidate {f.get('in_v3_0_candidate')!r} disagrees with state {s}")
        else:
            yes_no[want] += 1
        if s == "HELD_IN_CANDIDATE" and c.get("released_in_candidate") != "none":
            bad.append(f"{code}: HELD_IN_CANDIDATE needs released_in_candidate 'none'")
        if s == "INTEGRATED_IN_CANDIDATE_AND_TESTED":
            for k in ("changed", "open"):
                if not str(c.get(k, "")).strip():
                    bad.append(f"{code}: {s} must say what '{k}'")
        if s in PACKAGE_BACKED and not str(c.get("changed", "")).strip():
            bad.append(f"{code}: {s} must say what changed")
    if doc.get("candidate_state_counts") != counts:
        bad.append(f"candidate_state_counts {doc.get('candidate_state_counts')} != families {counts}")
    if doc.get("in_v3_0_candidate_counts") != yes_no:
        bad.append(f"in_v3_0_candidate_counts {doc.get('in_v3_0_candidate_counts')} != families {yes_no}")
    return bad


def main(argv):
    if len(argv) < 2 or argv[1] != "check":
        print(__doc__)
        return 2
    path = Path(argv[2]) if len(argv) > 2 else DEFAULT
    doc = json.loads(path.read_text(encoding="utf-8"))
    bad = check(doc, root=ROOT, is_ancestor=git_is_ancestor)
    for b in bad:
        print("PROBLEM", b)
    print(f"{path.name}: {len(bad)} problem(s); states {doc.get('candidate_state_counts')}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
