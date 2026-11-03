"""T-492: when is a pending package MERGED? (Lead ruling F-C-T443-1, Checker finding on the T-443 r2 verdict)

The stale-pending guard of T-485 (tests/t485_registry_promotion) asked "is the task commit an ancestor of HEAD?". On a
READY package's own branch its own pending entry is always an ancestor of HEAD, so every candidate package failed the
guard by construction. The ruling: a package is merged only when its task commit has reached the WORKING BRANCH, never
because it is on its own task head.

make_merged()(commit) is True when either
  (1) the commit is an ancestor of the working-branch tip W (origin/<working branch>, else the local branch of that
      name), i.e. the Verifier's merge (or a fast-forward) published it; or
  (2) HEAD is the working branch itself checked out (HEAD -> refs/heads/<working branch>), ahead of W with W on its
      first-parent chain, and the commit is one of the first-parent commits of that segment W..HEAD: committed directly
      on the local working line, not yet pushed. A task branch or a detached head never uses (2): by the graph alone a
      fresh task branch cut from W is indistinguishable from the working line ahead of W, and its own commit would
      count as merged (the T-485 defect again).
A commit brought in only by a merge on the segment above W (a trial merge of a READY package, or a task branch that
merged another unmerged task branch) is NOT merged: nothing has published it to the working branch yet, so its pending
entry is legitimate and the guard must not name it.
If neither ref resolves the question cannot be answered: WorkingBranchUnavailable is raised, never a silent False (a
guard that always says "not merged" would pass every stale registry).
Ancestry goes through tools/family_master_candidate.git_is_ancestor, which keeps the T-463 shallow-clone rules.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

WORKING_BRANCH = "claude/access-permissions-setup-ii24ws"


class WorkingBranchUnavailable(RuntimeError):
    pass


def _git(root, *a):
    return subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True)


def working_tip(root=_ROOT, branch=WORKING_BRANCH):
    """the commit of origin/<branch>, else of the local <branch>; WorkingBranchUnavailable when neither resolves"""
    for ref in (f"refs/remotes/origin/{branch}", f"refs/heads/{branch}"):
        r = _git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    raise WorkingBranchUnavailable(f"neither origin/{branch} nor {branch} resolves in {root}: cannot tell a merged "
                                   f"package from a pending one")


def direct_working_commits(root=_ROOT, head="HEAD", tip=None, branch=WORKING_BRANCH):
    """first-parent commits of HEAD above W when W is on HEAD's first-parent chain (HEAD on the working line), else
    an empty set (HEAD is a task branch, a detached head or a side line)"""
    tip = tip or working_tip(root, branch)
    if head == "HEAD":
        sym = _git(root, "symbolic-ref", "--quiet", "HEAD").stdout.strip()
        if sym != f"refs/heads/{branch}":
            return set()
    elif head != f"refs/heads/{branch}":
        return set()
    seg = _git(root, "rev-list", "--first-parent", f"{tip}..{head}").stdout.split()
    if not seg:
        return set()                                     # HEAD == W, or HEAD behind W: W itself answers
    first_parent_of_last = _git(root, "rev-parse", f"{seg[-1]}^1").stdout.strip()
    return set(seg) if first_parent_of_last == tip else set()


def make_merged(root=_ROOT, head="HEAD", branch=WORKING_BRANCH):
    """-> merged(commit) predicate for build_master_1_43_0.stale_pending; resolves W once (raises when it cannot)"""
    tip = working_tip(root, branch)
    direct = direct_working_commits(root, head, tip, branch)

    def merged(commit):
        full = _git(root, "rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}").stdout.strip()
        if full and full in direct:
            return True
        return FMC.git_is_ancestor(commit, tip, root=root)

    return merged
