#!/usr/bin/env bash
# Lock-ownership probe (owner 2026-10-23 21:00): runs the CURRENT scripts/agent_env.sh of the checkout given as $1
# against a LOCAL bare copy of agents/control (copied locks cleared); never writes to the real board or engine branch.
# Usage: bash docs/agents/dashboard/lock_probe_2026-10-23.sh <main checkout>   (prints one PROBE line per case)
set -uo pipefail
HERE="$1"
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
git clone --quiet -b agents/control "$BARE" "$TMP/w0" && git -C "$TMP/w0" rm --quiet -r --ignore-unmatch docs/agents/locks >/dev/null && git -C "$TMP/w0" -c user.email=t@t -c user.name=t commit --quiet -m "probe: clear copied locks" ; git -C "$TMP/w0" push --quiet origin agents/control
prep "$TMP/a"; prep "$TMP/c"

age_lock() {  # age_lock SLUG MINUTES: move the remote lock's start back by MINUTES (token unchanged)
  rm -rf "$TMP/w"; git clone --quiet -b agents/control "$BARE" "$TMP/w"
  python3 -I - "$TMP/w/docs/agents/locks/$1.lock" "$2" <<'PY'
import json, sys, time
p = sys.argv[1]; d = json.load(open(p)); d["since_epoch"] = time.time() - float(sys.argv[2]) * 60; json.dump(d, open(p, "w"))
PY
  git -C "$TMP/w" -c user.email=t@t -c user.name=t commit --quiet -am "age the lock" && git -C "$TMP/w" push --quiet origin agents/control
}
res() { echo "PROBE $1 | expected: $2 | actual: $3 | $( [[ "$4" == 1 ]] && echo PASS || echo FAIL)"; }

# L1 expiry: holder's lock is past its TTL, nobody has taken it over; holder publishes a verdict
out="$(E "$TMP/a" board log "- $(now) | Verifier | STARTED | run A | probe | x | x" 2>&1)" || fail "A STARTED: $out"
age_lock checker 125
echo "verdict" > "$TMP/a/.work/board/docs/agents/_probe_verdict"
if E "$TMP/a" board commit "verdict after expiry" >/dev/null 2>&1; then res L1 "refused (lock expired)" "published" 0; else res L1 "refused (lock expired)" "refused" 1; fi

# L2 ownership replacement: a new run takes the stale lock over; the old run publishes a verdict, then pushes a merge
out="$(E "$TMP/c" board log "- $(now) | Verifier | STARTED | run C | takeover | x | x" 2>&1)" || fail "takeover: $out"
echo "verdict2" > "$TMP/a/.work/board/docs/agents/_probe_verdict2"
if E "$TMP/a" board commit "stale verdict after takeover" >/dev/null 2>&1; then res L2a "verdict refused after takeover" "published" 0; else res L2a "verdict refused after takeover" "refused (run lock lost)" 1; fi
git -C "$TMP/a/.work/engine" -c user.email=t@t -c user.name=t commit --quiet --allow-empty -m "probe merge"
if git -C "$TMP/a/.work/engine" push --quiet origin HEAD:refs/heads/probe-engine 2>/dev/null; then res L2b "merge push refused after takeover" "pushed (no lock check on the engine push)" 0; else res L2b "merge push refused after takeover" "refused" 1; fi

# L3 near-expiry window: lock valid but 1 min from expiry; holder checks then publishes (no margin)
E "$TMP/c" board log "- $(now) | Verifier | SUCCESS | none | probe | none" >/dev/null || fail "C final"
E "$TMP/a" board log "- $(now) | Lead | STARTED | run A2 | probe | x | x" >/dev/null || fail "A2 STARTED"
age_lock lead 119
echo "v3" > "$TMP/a/.work/board/docs/agents/_probe_verdict3"
if E "$TMP/a" board commit "verdict 1 min before expiry" >/dev/null 2>&1; then res L3 "refused when less than a safety margin of validity remains" "published" 0; else res L3 "refused within the margin" "refused" 1; fi
echo "PROBES DONE"
