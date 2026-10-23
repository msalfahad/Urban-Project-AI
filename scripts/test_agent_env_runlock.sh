#!/usr/bin/env bash
# Test: the run lock in scripts/agent_env.sh (owner 2026-10-23, pilot prerequisite): one run per agent at a time,
# atomic under a real push race, idle exit for the second run, task / board commit refused without the lock, release
# on the final line, stale-lock recovery, and a run that lost its stale lock refused. Cases 7-13 (owner 2026-10-23
# 21:30, lock safety): valid publication, replaced ownership, near-expiry margin, expiry during a long run, takeover
# between publications, a pause after the lock check (board commit and engine push), raw git pushes stopped by the
# pre-push hook, and SUCCESS final lines refused after the lock is lost; board publication and engine pushes both. Run by the owner's main chat, not
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
git clone --quiet -b agents/control "$BARE" "$TMP/w0" || fail "clear clone"   # the copy carries live locks: clear them
if [[ -d "$TMP/w0/docs/agents/locks" ]]; then
  git -C "$TMP/w0" rm --quiet -r docs/agents/locks && git -C "$TMP/w0" -c user.email=t@t -c user.name=t commit --quiet -m "test: clear copied locks" && git -C "$TMP/w0" push --quiet origin agents/control || fail "clear locks"
fi
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

# ---- lock safety (owner 2026-10-23 21:30) ------------------------------------------------------------------------
ENG="claude/access-permissions-setup-ii24ws"
age_lock() {  # age_lock SLUG MINUTES: the remote lock started MINUTES ago (token unchanged)
  rm -rf "$TMP/w"; git clone --quiet -b agents/control "$BARE" "$TMP/w"
  python3 -I - "$TMP/w/docs/agents/locks/$1.lock" "$2" <<'PY'
import json, sys, time
p = sys.argv[1]; d = json.load(open(p)); d["since_epoch"] = time.time() - float(sys.argv[2]) * 60; json.dump(d, open(p, "w"))
PY
  git -C "$TMP/w" -c user.email=t@t -c user.name=t commit --quiet -am "age the lock" && git -C "$TMP/w" push --quiet origin agents/control
}
publish() {  # publish DIR TAG: a board verdict commit; exit status of board commit
  echo "$2" > "$1/.work/board/docs/agents/_lock_test_$2"
  E "$1" board commit "verdict $2" >"$TMP/out" 2>&1; local rc=$?
  rm -f "$1/.work/board/docs/agents/_lock_test_$2"; git -C "$1/.work/board" checkout --quiet -- . 2>/dev/null; return $rc
}
mk_merge() {  # a merge commit on top of the remote engine head (fast-forward, as the Verifier's real merges are)
  if git -C "$1/.work/engine" fetch --quiet origin "refs/heads/$ENG" 2>/dev/null; then git -C "$1/.work/engine" checkout --quiet --detach FETCH_HEAD; fi
  git -C "$1/.work/engine" -c user.email=t@t -c user.name=t commit --quiet --allow-empty -m "test merge $2"
}
raw_push() { git -C "$1/.work/engine" push --quiet origin "HEAD:refs/heads/$2" >"$TMP/out" 2>&1; }
remote_ref() { git --git-dir="$BARE" rev-parse --verify --quiet "refs/heads/$1" || echo none; }
for d in "$winner" "$loser"; do [[ -x "$d/.git/hooks/pre-push" ]] || fail "push guard hook not installed in $d"; done
[[ ! -e "$HERE/.git/hooks/pre-push" ]] || fail "push guard written outside the checkout"
ok "pre-push guard installed by setup"

# 7. valid publication: the holder (loser of case 5, now holding the Verifier lock) publishes a verdict, an engine merge
#    through 'engine push', and a raw task-branch push
publish "$loser" v7 || fail "valid verdict refused: $(cat "$TMP/out")"
mk_merge "$loser" 7; E "$loser" engine push >"$TMP/out" 2>&1 || fail "valid engine push refused: $(cat "$TMP/out")"
[[ "$(remote_ref "$ENG")" == "$(git -C "$loser/.work/engine" rev-parse HEAD)" ]] || fail "engine push did not land"
raw_push "$loser" agents/task-LOCKTEST || fail "valid task push refused: $(cat "$TMP/out")"
ok "valid holder: verdict, engine push and task push published"

# 8. replaced ownership: the old run (winner of case 5, whose lock was taken over in case 6) tries every path
mk_merge "$winner" 8; before="$(remote_ref "$ENG")"
publish "$winner" v8 && fail "verdict published after takeover"; grep -q "run lock lost" "$TMP/out" || fail "verdict text: $(cat "$TMP/out")"
E "$winner" engine push >"$TMP/out" 2>&1 && fail "engine push after takeover"; grep -q "run lock lost" "$TMP/out" || fail "engine text: $(cat "$TMP/out")"
raw_push "$winner" "$ENG" && fail "raw engine push after takeover"; grep -q "push of refs/heads/$ENG refused" "$TMP/out" || fail "hook text: $(cat "$TMP/out")"
raw_push "$winner" agents/task-LOCKTEST2 && fail "raw task push after takeover"
[[ "$(remote_ref "$ENG")" == "$before" && "$(remote_ref agents/task-LOCKTEST2)" == none ]] || fail "a refused push landed"
E "$winner" board log "- $(now) | Verifier | SUCCESS | x | after takeover | none" >"$TMP/out" 2>&1 && fail "SUCCESS final line after takeover"
E "$winner" board log "- $(now) | Verifier | INCOMPLETE | none | lock lost | run lock lost" >/dev/null || fail "INCOMPLETE final line refused"
remote_has docs/agents/locks/checker.lock || fail "the old run released the new holder's lock"
ok "replaced ownership: verdict, engine push, raw engine and task pushes and SUCCESS refused; INCOMPLETE written"

# 9. near expiry: 115 of 120 minutes used (5 left, margin 10)
age_lock checker 115; mk_merge "$loser" 9; before="$(remote_ref "$ENG")"
publish "$loser" v9 && fail "verdict inside the margin"; grep -q "within 10 min of expiry" "$TMP/out" || fail "margin text: $(cat "$TMP/out")"
E "$loser" engine push >"$TMP/out" 2>&1 && fail "engine push inside the margin"
raw_push "$loser" "$ENG" && fail "raw engine push inside the margin"
[[ "$(remote_ref "$ENG")" == "$before" ]] || fail "a push inside the margin landed"
ok "near-expiry lock: verdict, engine push and raw push refused (10-minute margin)"

# 10. expiry during a long run: the same run, now past its TTL
age_lock checker 125
publish "$loser" v10 && fail "verdict after expiry"; grep -q "run lock expired" "$TMP/out" || fail "expiry text: $(cat "$TMP/out")"
E "$loser" engine push >"$TMP/out" 2>&1 && fail "engine push after expiry"
E "$loser" board log "- $(now) | Verifier | SUCCESS | x | expired | none" >/dev/null 2>&1 && fail "SUCCESS after expiry"
E "$loser" board log "- $(now) | Verifier | INCOMPLETE | none | lock expired | run lock expired" >/dev/null || fail "INCOMPLETE refused"
remote_has docs/agents/locks/checker.lock && fail "expired own lock not released by the INCOMPLETE line"
ok "expiry during a long run: publication refused, INCOMPLETE final line releases the lock"

# 11. takeover between two publications (Worker 3): first verdict publishes, a takeover follows, the second is refused
E "$loser" board log "- $(now) | Worker 3 | STARTED | run D1 | test | x | x" >/dev/null || fail "D1 STARTED"
publish "$loser" v11a || fail "first verdict refused: $(cat "$TMP/out")"
age_lock worker-3 185
E "$winner" board log "- $(now) | Worker 3 | STARTED | run D2 | takeover | x | x" >/dev/null || fail "D2 takeover"
publish "$loser" v11b && fail "second verdict after takeover"; grep -q "run lock lost" "$TMP/out" || fail "text: $(cat "$TMP/out")"
ok "takeover between publications: second verdict refused"

# 12. pause after the initial lock check: the check passes, the lock is taken over during the pause, the push is refused
#     by the pre-push hook at push time (engine push and board commit)
mk_merge "$winner" 12; before="$(remote_ref "$ENG")"
( AGENT_ENV_TEST_PAUSE_S=25 E "$winner" engine push >"$TMP/p1" 2>&1; echo $? > "$TMP/p1rc" ) &
sleep 8; age_lock worker-3 185; E "$loser" board log "- $(now) | Worker 3 | STARTED | run D3 | takeover in pause | x | x" >/dev/null || fail "D3"
wait
[[ "$(cat "$TMP/p1rc")" != 0 ]] || fail "engine push after a pause published: $(cat "$TMP/p1")"
[[ "$(remote_ref "$ENG")" == "$before" ]] || fail "paused engine push landed"
age_lock worker-3 0   # D3 (the loser) holds the Worker 3 lock, fresh again
echo v12 > "$loser/.work/board/docs/agents/_lock_test_v12"
( AGENT_ENV_TEST_PAUSE_S=25 E "$loser" board commit "verdict v12 paused" >"$TMP/p2" 2>&1; echo $? > "$TMP/p2rc" ) &
sleep 8; age_lock worker-3 185; E "$winner" board log "- $(now) | Worker 3 | STARTED | run D4 | takeover in pause | x | x" >/dev/null || fail "D4"
wait
[[ "$(cat "$TMP/p2rc")" != 0 ]] || fail "board commit after a pause published: $(cat "$TMP/p2")"
git --git-dir="$BARE" show agents/control:docs/agents/_lock_test_v12 >/dev/null 2>&1 && fail "paused verdict landed on the board"
rm -f "$winner/.work/board/docs/agents/_lock_test_v12" "$loser/.work/board/docs/agents/_lock_test_v12"
ok "pause after the lock check: engine push and board verdict refused at push time"

# 13. a session that never held a lock cannot push the engine branch raw
mk_merge "$TMP/c" 13 2>/dev/null || true
c_fresh="$TMP/c"; [[ -f "$c_fresh/.work/agent_lock" ]] && rm -f "$c_fresh/.work/agent_lock"
raw_push "$c_fresh" "$ENG" && fail "raw engine push without any lock"
ok "no lock record: raw engine push refused"
echo "ALL RUN-LOCK TESTS PASSED"
