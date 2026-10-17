"""Q5 (scratch): re-run each rebuild test that failed in a whole-suite run, ONE AT A TIME, from a pristine worktree
(research/ reset to HEAD before each), under the given interpreter. A failing builder (CalledProcessError) is re-run
directly to capture its own error. usage: python3 -I q5_isolated_loop.py WT PYTHON SUITE_LOG JSON_OUT"""
import json, re, subprocess, sys
WT, PY, LOG, OUT = sys.argv[1:5]
ids = [l.split()[1] for l in open(LOG) if l.startswith("FAILED ")]
res = []


def reset():
    subprocess.run(["git", "-C", WT, "checkout", "--", "research/"], check=True)
    subprocess.run(["git", "-C", WT, "clean", "-fdq", "--", "research/"], check=True)


for nid in ids:
    reset()
    p = subprocess.run([PY, "-m", "pytest", "-p", "no:cacheprovider", "-q", nid], cwd=WT, capture_output=True, text=True)
    out = p.stdout + p.stderr
    r = {"test": nid, "passed": p.returncode == 0}
    m = re.search(r"AssertionError: (\S+)\n", out)
    if m:
        r["first_differing_output"] = m.group(1)
    mods = sorted(set(re.findall(r"No module named '([^']+)'", out)))
    if mods:
        r["missing_modules"] = mods
    c = re.search(r"Command '(\[.*?\])' returned non-zero", out)
    if c:
        cmd = eval(c.group(1), {"__builtins__": {}})          # a list of strings printed by subprocess
        reset()
        q = subprocess.run(cmd, cwd=WT, capture_output=True, text=True)
        tail = [l for l in (q.stderr or "").strip().splitlines() if l.strip()][-1:] if q.returncode else []
        r["builder_error"] = tail[0][:300] if tail else None
    res.append(r)
    print(json.dumps(r)[:400], flush=True)
reset()
json.dump(res, open(OUT, "w"), indent=1)
