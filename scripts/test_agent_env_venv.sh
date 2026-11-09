#!/usr/bin/env bash
# Test: the venv counts as ready only after a finished install whose packages import (owner 2026-11-09, 'No module
# named pytest' in about half of the runs). Builds a throw-away fake checkout with a local bare origin and a fake `uv`
# on PATH; touches nothing real and needs no network. Run by the owner's main chat: bash scripts/test_agent_env_venv.sh
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
fail() { echo "TEST FAIL: $*"; exit 1; }
ok() { echo "TEST OK: $*"; }
export CLAUDE_CODE_REMOTE=true GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t

# local bare origin with the engine and board branches (setup fetches both)
BARE="$TMP/remote/msalfahad/Urban-Project-AI.git"; mkdir -p "$(dirname "$BARE")"; git init --quiet --bare "$BARE"
SEED="$TMP/seed"; git init --quiet "$SEED"; git -C "$SEED" commit --quiet --allow-empty -m seed
for b in claude/access-permissions-setup-ii24ws agents/control main; do git -C "$SEED" push --quiet "$BARE" "HEAD:refs/heads/$b"; done

R="$TMP/checkout"; mkdir -p "$R/scripts"; cp "$HERE/scripts/agent_env.sh" "$R/scripts/"
git -C "$R" init --quiet && git -C "$R" remote add origin "$BARE"
E="$R/.work/engine"; B="$R/.work/board/docs/agents"; mkdir -p "$E/tools" "$E/research/freeze_integrity" "$E/tests/t061_room_label_guard" "$E/engine" "$E/agents" "$B"
touch "$E/CLAUDE.md" "$E/tools/codemap.py" "$E/tools/freeze_verify.py" "$E/tools/alsenan_scoreboard.py" \
      "$E/research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl" "$E/agents/README.md"
echo "pytest==9.1.1" > "$E/requirements.txt"
for f in BOARD.md RUN_LOG.md MISSION.md OWNER_QUESTIONS.md; do touch "$B/$f"; done

# fake uv: `venv` makes bin/python (python3 with the venv's own site folder); `pip install` writes stub packages, or
# with FAKE_UV_DIE=1 dies half-way (python present, no packages), like a SessionStart hook cut off by its timeout
mkdir -p "$TMP/bin"; echo 0 > "$TMP/uv_calls"
cat > "$TMP/bin/uv" <<'EOF'
#!/usr/bin/env bash
echo $(( $(cat "$FAKE_UV_CALLS") + 1 )) > "$FAKE_UV_CALLS"
venv="${@: -1}"
if [[ "$1" == venv ]]; then
  mkdir -p "$venv/bin" "$venv/site"
  printf '#!/usr/bin/env bash\nPYTHONPATH="%s/site" exec python3 "$@"\n' "$venv" > "$venv/bin/python"; chmod +x "$venv/bin/python"
elif [[ "$1" == pip ]]; then
  py="$5"; site="$(dirname "$(dirname "$py")")/site"
  [[ "${FAKE_UV_DIE:-0}" == 1 ]] && exit 1
  for m in pytest ezdxf shapely; do mkdir -p "$site/$m"; touch "$site/$m/__init__.py"; done
fi
EOF
chmod +x "$TMP/bin/uv"; export PATH="$TMP/bin:$PATH" FAKE_UV_CALLS="$TMP/uv_calls"
env_sh() { (cd "$R" && bash scripts/agent_env.sh "$@" 2>&1); }
calls() { cat "$TMP/uv_calls"; }

# 1. install cut off half-way: setup fails and leaves no ready marker; a command run while the install still fails is
# REFUSED (the old code took bin/python alone as prepared and ran pytest into 'No module named pytest')
out="$(FAKE_UV_DIE=1 env_sh setup)" && fail "interrupted install reported success: $out"
[[ -x "$R/.work/venv/bin/python" && ! -f "$R/.work/venv/.req_hash" ]] || fail "half-built venv not as expected"
out="$(FAKE_UV_DIE=1 env_sh pytest tests/t061_room_label_guard)" && fail "command ran on a half-built venv: $out"
grep -q "running setup automatically" <<<"$out" || fail "half-built venv taken as prepared: $out"
[[ ! -f "$R/.work/venv/.req_hash" ]] || fail "ready marker written after a failed install"
ok "an interrupted install leaves no ready marker; commands refuse instead of running without pytest"

# 2. the next agent command repairs it by itself (automatic setup), and pytest then imports
before="$(calls)"; out="$(env_sh status)"
grep -q "running setup automatically" <<<"$out" || fail "no automatic repair: $out"
grep -q "venv incomplete or outdated: reinstalling" <<<"$out" || fail "setup did not reinstall: $out"
grep -q "venv INCOMPLETE" <<<"$out" && fail "still incomplete after repair: $out"
"$R/.work/venv/bin/python" -c 'import pytest' || fail "pytest does not import after repair"
(( $(calls) > before )) || fail "uv not called for the repair"
ok "the next command reinstalled the venv automatically; pytest imports"

# 3. marker present but a package deleted: treated as not ready and reinstalled
rm -rf "$R/.work/venv/site/pytest"
out="$(env_sh status)"
grep -q "running setup automatically" <<<"$out" || fail "missing package not detected: $out"
"$R/.work/venv/bin/python" -c 'import pytest' || fail "pytest not restored"
ok "a missing package with a stale marker is detected and reinstalled"

# 4. a healthy venv is left alone: no uv call, no new setup
before="$(calls)"; lines="$(wc -l < "$R/.work/setup.log")"
out="$(env_sh status)"
grep -q "running setup automatically" <<<"$out" && fail "setup ran on a healthy venv: $out"
[[ "$(calls)" == "$before" && "$(wc -l < "$R/.work/setup.log")" == "$lines" ]] || fail "healthy venv was touched"
ok "a healthy venv is left as it is"

# 5. a changed requirements.txt triggers a reinstall
echo "ezdxf==1.4.4" >> "$E/requirements.txt"; before="$(calls)"
out="$(env_sh setup)" || fail "setup after requirements change failed: $out"
(( $(calls) > before )) || fail "requirements change did not reinstall"
ok "a requirements change reinstalls the venv"
echo "ALL VENV TESTS PASSED"
