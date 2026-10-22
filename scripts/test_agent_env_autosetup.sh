#!/usr/bin/env bash
# Test: an unattended cloud session prepares itself even when the SessionStart hook did not run, keeps existing work,
# and a non-cloud shell is left untouched. Run by the owner's main chat, not by scheduled agents (it clones into a
# temporary folder). Usage: bash scripts/test_agent_env_autosetup.sh
# It clones main from GitHub, overlays THIS working copy's scripts/agent_env.sh and .claude/settings.json, and deletes
# the temporary folder at the end.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
URL="https://github.com/msalfahad/Urban-Project-AI.git"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
fail() { echo "TEST FAIL: $*"; exit 1; }
ok() { echo "TEST OK: $*"; }

prep_clone() {  # a scheduled task's checkout: main only, with the files under test
  git clone --quiet --depth 1 -b main "$URL" "$1"
  cp "$HERE/scripts/agent_env.sh" "$1/scripts/agent_env.sh"
  cp "$HERE/.claude/settings.json" "$1/.claude/settings.json"
}

# 1. unattended cloud session, hook never ran: the first agent command (status) must prepare everything itself
prep_clone "$TMP/a"
out="$(CLAUDE_CODE_REMOTE=true bash "$TMP/a/scripts/agent_env.sh" status 2>&1)" || fail "status exited non-zero: $out"
grep -q "running setup automatically" <<<"$out" || fail "no automatic setup: $out"
[[ -d "$TMP/a/.work/engine" && -d "$TMP/a/.work/board" && -x "$TMP/a/.work/venv/bin/python" ]] || fail "trees or venv missing"
grep -q "setup by auto" "$TMP/a/.work/setup.log" || fail "setup.log does not record the automatic setup"
grep -q "prepared: .*setup by auto" <<<"$out" || fail "status does not report who prepared the session"
ok "status prepared the session automatically (hook absent)"

# 2. existing work is never lost: a marker file and a task worktree survive further commands
echo keep > "$TMP/a/.work/board/docs/agents/_autosetup_test_marker"
CLAUDE_CODE_REMOTE=true bash "$TMP/a/scripts/agent_env.sh" task TESTAUTO >/dev/null
echo work > "$TMP/a/.work/task-TESTAUTO/_task_marker"
out="$(CLAUDE_CODE_REMOTE=true bash "$TMP/a/scripts/agent_env.sh" status 2>&1)"
grep -q "running setup automatically" <<<"$out" && fail "setup ran again on a prepared session"
[[ "$(wc -l < "$TMP/a/.work/setup.log")" -eq 1 ]] || fail "setup.log grew without a setup"
[[ -f "$TMP/a/.work/board/docs/agents/_autosetup_test_marker" && -f "$TMP/a/.work/task-TESTAUTO/_task_marker" ]] || fail "existing work lost"
ok "prepared session left as it was; board and task work kept"

# 3. the hook path: an explicit hook setup is idempotent and recorded as 'hook'
out="$(CLAUDE_CODE_REMOTE=true AGENT_ENV_SETUP_BY=hook bash "$TMP/a/scripts/agent_env.sh" setup 2>&1)" || fail "hook setup failed: $out"
grep -q "engine worktree exists; left as it is" <<<"$out" || fail "hook setup did not leave the engine tree"
tail -1 "$TMP/a/.work/setup.log" | grep -q "setup by hook" || fail "hook setup not recorded"
[[ -f "$TMP/a/.work/board/docs/agents/_autosetup_test_marker" ]] || fail "hook setup lost the board marker"
python3 -I -c "import json,sys; h=json.load(open(sys.argv[1]))['hooks']['SessionStart'][0]; assert 'matcher' not in h, h; assert 'AGENT_ENV_SETUP_BY=hook' in h['hooks'][0]['command']" "$TMP/a/.claude/settings.json" || fail "settings hook not as expected"
ok "hook setup idempotent, recorded, runs on every session start"

# 4. a non-cloud shell never prepares anything
prep_clone "$TMP/b"
out="$(env -u CLAUDE_CODE_REMOTE -u AGENT_ENV_FORCE bash "$TMP/b/scripts/agent_env.sh" status 2>&1)" || fail "non-cloud status failed: $out"
[[ ! -e "$TMP/b/.work" ]] || fail "non-cloud shell created .work"
grep -q "NOT PREPARED" <<<"$out" || fail "non-cloud status does not say NOT PREPARED"
ok "non-cloud shell untouched"
echo "ALL AUTOSETUP TESTS PASSED"
