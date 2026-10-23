#!/usr/bin/env bash
# Test: the run lock in scripts/agent_env.sh (owner 2026-10-23, pilot prerequisite): one run per agent at a time,
# atomic under a real push race, idle exit for the second run, task / board commit refused without the lock, release
# on the final line, stale-lock recovery, and a run that lost its stale lock refused. Run by the owner's main chat, not
# by scheduled agents. Usage: bash scripts/test_agent_env_runlock.sh
# Two checkouts of main (with THIS working copy's agent_env.sh) are prepared from GitHub, then both are pointed at a
# LOCAL bare copy of agents/control: the test never writes to the real board. The temporary folder is deleted at the end.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
URL="https://github.com/msalfahad/Urban-Project-AI.git"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
BARE="$TMP/remote/msalfahad/Urban-Project-AI.git"   # path ends like the real repo, so check_repo accepts it
export CLAUDE_CODE_REMOTE=true
fail() { echo "TEST FAIL: $*"; exit 1; }
ok() { echo "TEST OK: $*"; }
now() { date -u +%Y-%m-%dT%H:%MZ; }

prep() {  # checkout $1, prepared, then pointed at the local bare board
  git clone --quiet --depth 1 -b main "$URL" "$1"
  cp "$HERE/scripts/agent_env.sh" "$1/scripts/agent_env.sh"
  bash "$1/scripts/agent_env.sh" setup >/dev/null 2>&1 || fail "setup failed in $1"
  git -C "$1" remote set-url origin "$BARE"
  git -C "$1/.work/board" fetch --quiet origin agents/control || fail "fetch from bare failed"
}
remote_has() { git --git-dir="$BARE" show "agents/control:$1" >/dev/null 2>&1; }
remote_log_top() { git --git-dir="$BARE" show agents/control:docs/agents/RUN_LOG.md > "$TMP/log"; grep -m1 -E '^- [0-9]{4}-' "$TMP/log"; }
E() { bash "$1/scripts/agent_env.sh" "${@:2}"; }

mkdir -p "$(dirname "$BARE")"
git clone --quiet --bare --single-branch -b agents/control "$URL" "$BARE" || fail "bare clone"
prep "$TMP/a"; prep "$TMP/c"

# 1. first run takes the lock (lock file and STARTED line in one pushed commit)
E "$TMP/a" board log "- $(now) | Worker 1 | STARTED | run A | test | x | x" >/dev/null || fail "a STARTED"
remote_has docs/agents/locks/worker-1.lock || fail "no lock file on the remote"
[[ -f "$TMP/a/.work/agent_lock" ]] || fail "a holds no local lock record"
ok "first run took the lock atomically with its STARTED line"

# 2. a second run of the same agent exits idle (exit 3) and writes an IDLE line, no lock
E "$TMP/c" board log "- $(now) | Worker 1 | STARTED | run C | test | x | x" >/dev/null; rc=$?
[[ $rc -eq 3 ]] || fail "second run exit $rc, expected 3"
grep -q "| Worker 1 | IDLE |" <<<"$(remote_log_top)" || fail "no IDLE line: $(remote_log_top)"
[[ ! -f "$TMP/c/.work/agent_lock" ]] || fail "second run recorded a lock"
ok "second run of the same agent: IDLE final line, exit 3"

# 3. without the lock, task and board commit are refused
out="$(E "$TMP/c" task TESTLOCK 2>&1)" && fail "task ran without lock"
grep -q "no run lock held" <<<"$out" || fail "task refusal text: $out"
echo x >> "$TMP/c/.work/board/docs/agents/_lock_test"
out="$(E "$TMP/c" board commit "should be refused" 2>&1)" && fail "board commit ran without lock"
grep -q "no run lock held" <<<"$out" || fail "commit refusal text: $out"
rm -f "$TMP/c/.work/board/docs/agents/_lock_test"
ok "task and board commit refused without the lock"

# 4. another agent is not blocked; the holder can commit; its final line releases the lock
E "$TMP/c" board log "- $(now) | Worker 2 | STARTED | run C2 | test | x | x" >/dev/null || fail "worker 2 blocked by worker 1"
remote_has docs/agents/locks/worker-2.lock || fail "worker 2 lock missing"
E "$TMP/c" board log "- $(now) | Worker 2 | SUCCESS | none | test | none" >/dev/null || fail "worker 2 final"
remote_has docs/agents/locks/worker-2.lock && fail "worker 2 lock not released"
echo y > "$TMP/a/.work/board/docs/agents/_lock_test"
E "$TMP/a" board commit "lock holder commit" >/dev/null || fail "holder commit refused"
E "$TMP/a" board log "- $(now) | Worker 1 | SUCCESS | none | test | none" >/dev/null || fail "a final"
remote_has docs/agents/locks/worker-1.lock && fail "worker 1 lock not released"
[[ ! -f "$TMP/a/.work/agent_lock" ]] || fail "a still records the lock"
ok "agents lock independently; holder commits; final line releases"

# 5. a real race: two runs of the same agent start at the same moment; exactly one gets the lock
( E "$TMP/a" board log "- $(now) | Verifier | STARTED | run A3 | race | x | x" >/dev/null 2>&1; echo $? > "$TMP/ra" ) &
( E "$TMP/c" board log "- $(now) | Verifier | STARTED | run C3 | race | x | x" >/dev/null 2>&1; echo $? > "$TMP/rc" ) &
wait
ra="$(cat "$TMP/ra")"; rc="$(cat "$TMP/rc")"
[[ "$ra$rc" == "03" || "$ra$rc" == "30" ]] || fail "race exits a=$ra c=$rc (want one 0 and one 3)"
n=$(( $( [[ -f "$TMP/a/.work/agent_lock" ]] && echo 1 || echo 0 ) + $( [[ -f "$TMP/c/.work/agent_lock" ]] && echo 1 || echo 0 ) ))
[[ $n -eq 1 ]] || fail "race: $n local lock records"
ok "concurrent start: exactly one run holds the lock (exits $ra / $rc)"
winner="$TMP/a"; loser="$TMP/c"; [[ "$ra" == "3" ]] && { winner="$TMP/c"; loser="$TMP/a"; }

# 6. stale lock: the holder's lock is aged past its TTL; a new run takes it over and the old run is refused
git clone --quiet -b agents/control "$BARE" "$TMP/w"
python3 -I - "$TMP/w/docs/agents/locks/checker.lock" <<'PY'
import json, sys, time
p = sys.argv[1]; d = json.load(open(p)); d["since_epoch"] = time.time() - 121 * 60; json.dump(d, open(p, "w"))
PY
git -C "$TMP/w" -c user.email=t@t -c user.name=t commit --quiet -am "age the lock" && git -C "$TMP/w" push --quiet origin agents/control
out="$(E "$loser" board log "- $(now) | Verifier | STARTED | run L | stale | x | x" 2>&1)" || fail "stale takeover failed: $out"
grep -q "stale run lock of run" <<<"$(remote_log_top)" || fail "takeover not recorded: $(remote_log_top)"
echo z > "$winner/.work/board/docs/agents/_lock_test"
out="$(E "$winner" board commit "old holder" 2>&1)" && fail "old holder committed after losing the lock"
grep -q "run lock lost" <<<"$out" || fail "lost-lock refusal text: $out"
ok "stale lock recovered by a new run; the old run is refused"
echo "ALL RUN-LOCK TESTS PASSED"
