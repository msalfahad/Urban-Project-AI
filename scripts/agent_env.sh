#!/usr/bin/env bash
# Urban-Project-AI scheduled-agent environment (lives on main; owner-approved configuration only).
#
# A scheduled task clones this repository at main, which holds no engine code. This script, run by the
# SessionStart hook in .claude/settings.json, prepares the real work trees beside it and runs the project's own
# checks with a fixed set of subcommands. It never clones, never adds a remote, never resets or deletes existing
# work and never touches another repository. Its only push is `board`: files under docs/agents/ of the board
# worktree, to origin agents/control, never forced.
#
#   .work/engine     detached worktree of origin/claude/access-permissions-setup-ii24ws (engine, tests, tools)
#   .work/board      worktree of local branch agents/control (docs/agents: board, RUN_LOG)
#   .work/task-<ID>  worktree of branch agents/task-<ID>, created on request
#   .work/venv       Python 3.11 virtual environment from the engine's pinned requirements.txt
#   .work/private    private Drive copies (mode 700); outside every worktree and git-excluded, never committed
#
# Usage: bash scripts/agent_env.sh <command> [args]
#   setup                         prepare worktrees and venv (idempotent); every other command runs it by
#                                 itself when the work trees are missing (cloud sessions only), so a session
#                                 whose SessionStart hook did not run still prepares itself
#   status                        repository, branches, worktrees and venv facts, and who prepared them
#   selfcheck [--tree T]          codemap check, pytest tests/t061_room_label_guard, freeze check
#   codemap [--tree T] route|impact|check|build [args...]
#   freeze [--tree T]             tools/freeze_verify.py check against the frozen baseline index
#   pytest [--tree T] PATH...     PATH must be under tests/ or agents/; no options are passed through
#   run [--tree T] SCRIPT [args]  SCRIPT is tools/alsenan_scoreboard.py or tools/alsenan_keymap.py
#   task ID                       create or reuse .work/task-ID on branch agents/task-ID
#   decode SRC NAME               base64-decode SRC into .work/private/NAME (unzipped when NAME ends in .zip)
#   board pull                    git pull --rebase of the board worktree
#   board log "LINE"              put LINE at the top of the "## Entries" list of docs/agents/RUN_LOG.md, commit, push
#   board commit "MESSAGE"        commit every change under docs/agents/ of the board worktree and push agents/control
#   board check                   pull, then docs/agents/dashboard/queue_check.py: every actionable task has an agent, a
#                                 queue place and a reason; exit 1 when a row is flagged
#   lock check [--margin N]       exit 0 only if this session holds its run lock on the remote board, unexpired, with at
#                                 least N minutes (default 10) of validity left
#   engine push                   lock check, then push .work/engine HEAD to the engine branch (never forced); the
#                                 Verifier's only merge-publication path
# RUN LOCK (owner 2026-10-23, pilot): one run per agent at a time. `board log` with a STARTED line of the Lead, a Worker
# or the Verifier atomically takes docs/agents/locks/<agent>.lock on agents/control (the lock file and the STARTED line
# are one commit; a concurrent run's push conflicts on the same file and that run re-checks). A held lock younger than
# the agent's TTL makes the second run write an IDLE final line and exit 3 ("AGENT_ENV LOCKED"). An older lock is stale
# and is taken over the same way (the STARTED line says so). The run's final line releases its own lock. `task` and
# `board commit` refuse to run without the lock this session holds (a run that lost a stale lock cannot claim or merge).
# LOCK SAFETY (owner 2026-10-23 21:30): every publication re-checks ownership AND validity against the remote lock just
# before it pushes: token equal, not expired, and at least LOCK_MARGIN_MIN (10) minutes left (a takeover needs an expired
# lock, so a passing check leaves that much time; this is a margin, not an atomic fence). Guarded paths: `board commit`
# (before every push attempt), `board log` final lines (SUCCESS refused after the lock is lost or expired: write
# INCOMPLETE), `task`, `engine push`, and a git pre-push hook installed in this checkout that refuses raw pushes of the
# engine branch and of agents/task-* without a valid lock, and raw pushes of agents/control by a session that holds a
# lock record but no longer a valid lock (1-minute margin at push time). Only `board log` pushes (STARTED and final
# lines) are marked internal; they do their own checks. This is a margin, not a fence (see the residual risk note).
# T is "engine" (default) or "task-<ID>".
set -euo pipefail

ENGINE_BRANCH="claude/access-permissions-setup-ii24ws"
BOARD_BRANCH="agents/control"
# GitHub owner/repo names are case-insensitive; the attached checkout's origin can be lower case.
EXPECTED_REPO_RE='(^|[/:])msalfahad/urban-project-ai(\.git)?/?$'

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$ROOT/.work"
VENV="$WORK/venv"
PRIVATE="$WORK/private"
PY="$VENV/bin/python"

die() { echo "AGENT_ENV FAIL: $*" >&2; exit 1; }
say() { echo "AGENT_ENV: $*"; }

check_repo() {
  local url
  url="$(git -C "$ROOT" remote get-url origin 2>/dev/null)" || die "no origin remote in $ROOT"
  [[ "${url,,}" =~ $EXPECTED_REPO_RE ]] || die "origin is not msalfahad/Urban-Project-AI: $url"
}

tree_dir() {  # map a tree name to its directory
  case "$1" in
    engine) echo "$WORK/engine" ;;
    task-*) [[ "$1" =~ ^task-[A-Za-z0-9._-]+$ ]] || die "bad tree name: $1"; echo "$WORK/$1" ;;
    *) die "unknown tree: $1 (use engine or task-<ID>)" ;;
  esac
}

add_refspec() {  # a scheduled clone may be single-branch (main only); let origin also map the agents' branches
  local spec="+refs/heads/$1:refs/remotes/origin/$1"
  git -C "$ROOT" config --get-all remote.origin.fetch | grep -qxF "$spec" || git -C "$ROOT" config --add remote.origin.fetch "$spec"
}

set_upstream() {  # track origin/<branch> so that pull and push need no arguments
  git -C "$ROOT" config "branch.$1.remote" origin
  git -C "$ROOT" config "branch.$1.merge" "refs/heads/$1"
}

need_venv() { [[ -x "$PY" ]] || die "venv missing; run: bash scripts/agent_env.sh setup"; }

is_cloud() { [[ "${CLAUDE_CODE_REMOTE:-}" == "true" || "${AGENT_ENV_FORCE:-}" == "1" ]]; }
prepared() { [[ -d "$WORK/engine" && -d "$WORK/board" && -x "$PY" ]]; }

ensure_prepared() {  # self-healing: a session whose SessionStart hook did not run prepares itself here
  prepared && { install_push_guard; return 0; }
  is_cloud || return 0
  [[ -n "${AGENT_ENV_IN_SETUP:-}" ]] && return 0
  say "work trees missing: running setup automatically"
  AGENT_ENV_SETUP_BY="${AGENT_ENV_SETUP_BY:-auto}" cmd_setup >&2
}

cmd_setup() {
  if ! is_cloud; then
    say "not a cloud session; setup skipped"; return 0
  fi
  local AGENT_ENV_IN_SETUP=1
  check_repo
  mkdir -p "$WORK"
  local exclude="$ROOT/.git/info/exclude"
  [[ -d "$ROOT/.git" ]] && { grep -qxF '.work/' "$exclude" 2>/dev/null || echo '.work/' >> "$exclude"; }

  add_refspec "$ENGINE_BRANCH"; add_refspec "$BOARD_BRANCH"; add_refspec "agents/task-*"
  git -C "$ROOT" fetch --quiet --no-tags origin \
    "+refs/heads/$ENGINE_BRANCH:refs/remotes/origin/$ENGINE_BRANCH" \
    "+refs/heads/$BOARD_BRANCH:refs/remotes/origin/$BOARD_BRANCH"

  if [[ -e "$WORK/engine" ]]; then
    say "engine worktree exists; left as it is"
  else
    git -C "$ROOT" worktree add --quiet --detach "$WORK/engine" "origin/$ENGINE_BRANCH"
  fi
  if [[ -e "$WORK/board" ]]; then
    say "board worktree exists; left as it is"
  elif git -C "$ROOT" show-ref --verify --quiet "refs/heads/$BOARD_BRANCH"; then
    git -C "$ROOT" worktree add --quiet "$WORK/board" "$BOARD_BRANCH"
  else
    git -C "$ROOT" worktree add --quiet -b "$BOARD_BRANCH" "$WORK/board" "origin/$BOARD_BRANCH"
    set_upstream "$BOARD_BRANCH"
  fi

  local f missing=()
  for f in CLAUDE.md requirements.txt tools/codemap.py tools/freeze_verify.py tools/alsenan_scoreboard.py \
           research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl tests/t061_room_label_guard engine agents/README.md; do
    [[ -e "$WORK/engine/$f" ]] || missing+=("engine:$f")
  done
  for f in BOARD.md RUN_LOG.md MISSION.md OWNER_QUESTIONS.md; do
    [[ -e "$WORK/board/docs/agents/$f" ]] || missing+=("board:docs/agents/$f")
  done
  (( ${#missing[@]} == 0 )) || die "expected files missing: ${missing[*]}"

  local req_hash
  req_hash="$(sha256sum "$WORK/engine/requirements.txt" | cut -c1-16)"
  if [[ -x "$PY" && "$(cat "$VENV/.req_hash" 2>/dev/null)" == "$req_hash" ]]; then
    say "venv up to date"
  else
    uv venv --quiet --allow-existing -p python3.11 "$VENV"
    uv pip install --quiet -p "$PY" -r "$WORK/engine/requirements.txt"
    echo "$req_hash" > "$VENV/.req_hash"
  fi

  install_push_guard
  mkdir -p "$PRIVATE" && chmod 700 "$PRIVATE"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) setup by ${AGENT_ENV_SETUP_BY:-manual}" >> "$WORK/setup.log"
  cmd_status
}

cmd_status() {
  check_repo
  [[ -n "${AGENT_ENV_IN_SETUP:-}" ]] || ensure_prepared
  say "repo $(git -C "$ROOT" remote get-url origin | sed -E 's#.*[/:](msalfahad/urban-project-ai).*#\1#I')"
  say "session checkout $(git -C "$ROOT" rev-parse --abbrev-ref HEAD) @ $(git -C "$ROOT" rev-parse --short HEAD)"
  [[ -d "$WORK/engine" ]] && say "engine $WORK/engine @ $(git -C "$WORK/engine" rev-parse --short HEAD) (origin/$ENGINE_BRANCH)"
  [[ -d "$WORK/board" ]] && say "board $WORK/board on $(git -C "$WORK/board" rev-parse --abbrev-ref HEAD) @ $(git -C "$WORK/board" rev-parse --short HEAD)"
  [[ -x "$PY" ]] && say "venv $("$PY" --version 2>&1) at $VENV"
  [[ -d "$PRIVATE" ]] && say "private drawings go only to $PRIVATE (git-excluded, outside every worktree)"
  [[ -f "$WORK/setup.log" ]] && say "prepared: $(tail -1 "$WORK/setup.log")"
  prepared || say "NOT PREPARED (not a cloud session, or setup failed above)"
  return 0
}

parse_tree() {  # sets TREE_DIR, leaves remaining args in ARGS
  TREE_DIR="$(tree_dir engine)"; ARGS=("$@")
  if [[ "${1:-}" == "--tree" ]]; then
    [[ $# -ge 2 ]] || die "--tree needs a name"
    TREE_DIR="$(tree_dir "$2")"; ARGS=("${@:3}")
  fi
  [[ -d "$TREE_DIR" ]] || die "tree not prepared: $TREE_DIR"
}

in_tree() { (cd "$TREE_DIR" && PYTHONDONTWRITEBYTECODE=1 "$@"); }

cmd_codemap() {
  parse_tree "$@"; need_venv
  case "${ARGS[0]:-}" in route|impact|check|build) ;; *) die "codemap subcommand must be route, impact, check or build";; esac
  in_tree "$PY" -I tools/codemap.py "${ARGS[@]}"
}

cmd_freeze() {
  parse_tree "$@"; need_venv
  (( ${#ARGS[@]} == 0 )) || die "freeze takes no arguments"
  in_tree "$PY" -I tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl
}

cmd_pytest() {
  parse_tree "$@"; need_venv
  (( ${#ARGS[@]} > 0 )) || die "pytest needs at least one path"
  local p
  for p in "${ARGS[@]}"; do
    [[ "$p" =~ ^(tests|agents)/[A-Za-z0-9_./-]*$ && "$p" != *..* ]] || die "pytest path must be under tests/ or agents/: $p"
    [[ -e "$TREE_DIR/${p%%::*}" ]] || die "no such test path in tree: $p"
  done
  in_tree "$PY" -m pytest -p no:cacheprovider -q "${ARGS[@]}"
}

cmd_run() {
  parse_tree "$@"; need_venv
  local script="${ARGS[0]:-}"
  case "$script" in tools/alsenan_scoreboard.py|tools/alsenan_keymap.py) ;; *) die "run allows only tools/alsenan_scoreboard.py or tools/alsenan_keymap.py";; esac
  in_tree "$PY" -I "${ARGS[@]}"
}

cmd_selfcheck() {
  parse_tree "$@"; need_venv
  local rc=0 out
  if out="$(cmd_codemap --tree "$(basename "$TREE_DIR")" check 2>&1)"; then say "selfcheck codemap check PASS"; else say "selfcheck codemap check FAIL"; rc=1; fi
  echo "$out" | tail -3
  if out="$(cmd_pytest --tree "$(basename "$TREE_DIR")" tests/t061_room_label_guard 2>&1)"; then say "selfcheck pytest t061 PASS"; else say "selfcheck pytest t061 FAIL"; rc=1; fi
  echo "$out" | tail -3
  if out="$(cmd_freeze --tree "$(basename "$TREE_DIR")" 2>&1)" && grep -q 'frozen artefacts differing from the index: 0' <<<"$out"; then
    say "selfcheck freeze PASS"; else say "selfcheck freeze FAIL"; rc=1; fi
  echo "$out" | tail -3
  return $rc
}

cmd_task() {
  check_repo
  local id="${1:-}"
  [[ "$id" =~ ^[A-Za-z0-9._-]+$ ]] || die "task ID must be letters, digits, . _ -"
  local dir="$WORK/task-$id" br="agents/task-$id"
  require_lock
  if [[ -e "$dir" ]]; then say "task worktree exists: $dir"; return 0; fi
  git -C "$ROOT" fetch --quiet --no-tags origin "+refs/heads/$ENGINE_BRANCH:refs/remotes/origin/$ENGINE_BRANCH"
  if git -C "$ROOT" show-ref --verify --quiet "refs/heads/$br"; then
    git -C "$ROOT" worktree add --quiet "$dir" "$br"
  elif git -C "$ROOT" fetch --quiet --no-tags origin "+refs/heads/$br:refs/remotes/origin/$br" 2>/dev/null; then
    git -C "$ROOT" worktree add --quiet -b "$br" "$dir" "origin/$br"
    set_upstream "$br"
  else
    git -C "$ROOT" worktree add --quiet -b "$br" "$dir" "origin/$ENGINE_BRANCH"
  fi
  say "task worktree $dir on $br @ $(git -C "$dir" rev-parse --short HEAD)"
}

cmd_decode() {
  local src="${1:-}" name="${2:-}"
  [[ $# -eq 2 ]] || die "decode needs SRC and NAME"
  [[ -f "$src" ]] || die "no such file: $src"
  [[ "$name" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || die "NAME must be a plain file name"
  mkdir -p "$PRIVATE" && chmod 700 "$PRIVATE"
  # The Drive connector saves large downloads as JSON ({"content": <base64>, ...}); accept both forms.
  python3 -I -c 'import base64,json,sys
raw=open(sys.argv[1],"rb").read()
if raw.lstrip()[:1]==b"{": raw=json.loads(raw)["content"].encode()
open(sys.argv[2],"wb").write(base64.b64decode(raw))' "$src" "$PRIVATE/$name" || die "base64 decode failed"
  if [[ "$name" == *.zip ]]; then
    local entries dest="$PRIVATE/${name%.zip}"
    entries="$(unzip -Z1 "$PRIVATE/$name")" || die "not a zip archive"
    if grep -qE '(^/|(^|/)\.\.(/|$))' <<<"$entries"; then die "zip entry path escapes the private folder"; fi
    mkdir -p "$dest" && unzip -q -o "$PRIVATE/$name" -d "$dest"
    say "decoded and unzipped into $dest ($(wc -l <<<"$entries") entries)"
  else
    say "decoded into $PRIVATE/$name ($(stat -c %s "$PRIVATE/$name") bytes)"
  fi
}

board_push() {  # push agents/control; on rejection rebase once and push again; the lock is re-checked before each push
  local b="$WORK/board"
  require_lock; test_pause                     # the pre-push hook re-checks the lock at push time (not internal)
  git -C "$b" push --quiet origin "HEAD:refs/heads/$BOARD_BRANCH" 2>/dev/null && return 0
  require_lock   # a refused push may be the hook: re-check first so a lost lock dies here, not as a rebase
  git -C "$b" pull --quiet --rebase origin "$BOARD_BRANCH" || die "board rebase failed"
  require_lock
  git -C "$b" push --quiet origin "HEAD:refs/heads/$BOARD_BRANCH" || die "board push rejected twice"
}

LOCK_DIR="docs/agents/locks"
LOCK_MARGIN_MIN=10
lock_slug() {  # agent name in a run-log line -> lock slug and TTL in minutes (empty: agent not locked)
  case "$1" in
    "Lead") echo "lead 120" ;;
    "Worker 1") echo "worker-1 120" ;;
    "Worker 2") echo "worker-2 120" ;;
    "Worker 3") echo "worker-3 180" ;;
    "Verifier"|"Checker") echo "checker 120" ;;
    *) echo "" ;;
  esac
}

lock_py() {  # lock_py MODE FILE [TOKEN TTL AGENT]: decide / write / release a lock file; prints the decision
  python3 -I - "$@" <<'LOCKPY'
import json, sys, time
from datetime import datetime, timezone
mode, path = sys.argv[1], sys.argv[2]
now = time.time()
try:
    cur = json.load(open(path, encoding="utf-8"))
except (OSError, ValueError):
    cur = None
if mode == "check":                      # FREE | BUSY <token> <since> | STALE <token> <since>
    if not cur:
        print("FREE"); sys.exit()
    age_min = (now - cur["since_epoch"]) / 60
    print(("STALE" if age_min >= cur["ttl_min"] else "BUSY"), cur["token"], cur["since"])
elif mode == "take":
    token, ttl, agent = sys.argv[3], int(sys.argv[4]), sys.argv[5]
    json.dump({"agent": agent, "token": token, "since_epoch": now, "ttl_min": ttl,
               "since": datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%dT%H:%MZ")},
              open(path, "w", encoding="utf-8"), indent=1)
    print("TAKEN")
elif mode == "holder":                   # token of the current holder, or NONE
    print(cur["token"] if cur else "NONE")
LOCKPY
}

log_insert() {  # put LINE at the top of the "## Entries" list of RUN_LOG.md
  LINE="$2" python3 -I -c 'import os,sys
p=sys.argv[1]; s=open(p,encoding="utf-8").read(); h="## Entries"; i=s.index(h)+len(h)
j=s.index("\n",i)+1
while s[j:j+1]=="\n": j+=1
open(p,"w",encoding="utf-8").write(s[:j]+os.environ["LINE"]+"\n"+s[j:])' "$1"
}

board_sync() {  # fetch agents/control and move the board worktree to it, keeping uncommitted edits (never discards them)
  local b="$WORK/board"
  git -C "$b" fetch --quiet origin "$BOARD_BRANCH"
  git -C "$b" reset --quiet --keep "origin/$BOARD_BRANCH" || die "board has local commits or edits that block a sync"
}

lock_state() {  # lock_state MARGIN -> "OK <min left>" | "NOLOCK" | "LOST <holder>" | "EXPIRED" | "MARGIN <min left>"
  local held="$WORK/agent_lock" margin="${1:-$LOCK_MARGIN_MIN}"
  [[ -f "$held" ]] || { echo "NOLOCK"; return 0; }
  local slug token
  read -r slug token < "$held"
  git -C "$WORK/board" fetch --quiet origin "$BOARD_BRANCH" || { echo "LOST unreadable"; return 0; }
  git -C "$WORK/board" show "origin/$BOARD_BRANCH:$LOCK_DIR/$slug.lock" 2>/dev/null | python3 -I -c 'import json,sys,time
tok, margin = sys.argv[1], float(sys.argv[2])
try: d = json.load(sys.stdin)
except Exception: print("LOST NONE"); sys.exit()
if d.get("token") != tok: print("LOST", d.get("token")); sys.exit()
left = (d["since_epoch"] + d["ttl_min"] * 60 - time.time()) / 60
print("EXPIRED" if left <= 0 else ("MARGIN %.1f" % left if left < margin else "OK %.1f" % left))' "$token" "$margin"
}

require_lock() {  # require_lock [MARGIN]: the session must hold its agent lock, unexpired, with MARGIN minutes left
  is_cloud || return 0
  local st
  st="$(lock_state "${1:-$LOCK_MARGIN_MIN}")"
  case "$st" in
    OK*) return 0 ;;
    NOLOCK) die "no run lock held: write the STARTED line with board log first (owner 2026-10-23 run lock)" ;;
    LOST*) die "run lock lost (held by ${st#LOST }); this run may not claim, merge or commit: end it" ;;
    EXPIRED) die "run lock expired; publish nothing: write the final line INCOMPLETE and end" ;;
    MARGIN*) die "run lock within ${1:-$LOCK_MARGIN_MIN} min of expiry (${st#MARGIN } min left); publish nothing: write the final line INCOMPLETE and end" ;;
  esac
}

install_push_guard() {  # git pre-push hook for raw pushes from any worktree of this checkout (idempotent)
  is_cloud || return 0
  [[ -d "$ROOT/.git" ]] || return 0
  local hooks hook mark="# URBAN AGENT_ENV PUSH GUARD"
  hooks="$(git -C "$ROOT" rev-parse --path-format=absolute --git-common-dir)/hooks"; hook="$hooks/pre-push"
  [[ "$(git -C "$ROOT" config --get core.hooksPath || true)" == "" ]] || die "core.hooksPath is set; the push guard cannot be installed"
  if [[ -f "$hook" ]] && ! grep -qF "$mark" "$hook"; then die "a foreign pre-push hook exists; the push guard cannot be installed"; fi
  mkdir -p "$hooks"
  local want
  want="$(cat <<HOOK
#!/usr/bin/env bash
$mark (installed by scripts/agent_env.sh; owner 2026-10-23 lock safety)
[[ "\${AGENT_ENV_INTERNAL_PUSH:-}" == "1" ]] && exit 0
AE="$ROOT/scripts/agent_env.sh"
while read -r lref lsha rref rsha; do
  case "\$rref" in
    refs/heads/$ENGINE_BRANCH|refs/heads/agents/task-*)
      bash "\$AE" lock check >&2 || { echo "AGENT_ENV FAIL: push of \$rref refused: no valid run lock" >&2; exit 1; } ;;
    refs/heads/$BOARD_BRANCH)
      if [[ -f "$WORK/agent_lock" ]]; then
        bash "\$AE" lock check --margin 1 >&2 || { echo "AGENT_ENV FAIL: board push refused: run lock lost, expired or within 1 min of expiry" >&2; exit 1; }
      fi ;;
  esac
done
exit 0
HOOK
)"
  [[ -f "$hook" && "$(cat "$hook")" == "$want" ]] && return 0
  printf '%s\n' "$want" > "$hook.tmp.$$" && chmod +x "$hook.tmp.$$" && mv -f "$hook.tmp.$$" "$hook"   # rename: a running hook keeps its file
}

test_pause() {  # test seam: AGENT_ENV_TEST_PAUSE_S=<seconds> sleeps between the lock check and the push (tests only)
  [[ "${AGENT_ENV_TEST_PAUSE_S:-}" =~ ^[0-9]+$ ]] && sleep "$AGENT_ENV_TEST_PAUSE_S"
  return 0
}

cmd_lock() {
  [[ "${1:-}" == "check" ]] || die "lock needs: check [--margin N]"
  shift
  local margin="$LOCK_MARGIN_MIN"
  if [[ "${1:-}" == "--margin" ]]; then
    [[ "${2:-}" =~ ^[0-9]+$ ]] || die "--margin needs whole minutes"; margin="$2"
  fi
  is_cloud || { say "not a cloud session; no run lock"; return 0; }
  local st; st="$(lock_state "$margin")"
  [[ "$st" == OK* ]] || die "run lock not valid: $st"
  say "run lock valid (${st#OK } min left)"
}

cmd_engine() {
  [[ "${1:-}" == "push" && $# -eq 1 ]] || die "engine needs: push"
  require_lock; test_pause                     # the pre-push hook re-checks the lock at push time
  git -C "$WORK/engine" push --quiet origin "HEAD:refs/heads/$ENGINE_BRANCH" || die "engine push refused or rejected (never forced)"
  local st; st="$(lock_state 0)"
  if [[ "$st" != OK* ]]; then
    echo "AGENT_ENV INCIDENT: engine push completed but the run lock is now $st; report it in the final line (INCOMPLETE)" >&2
    exit 4
  fi
  say "engine pushed @ $(git -C "$WORK/engine" rev-parse --short HEAD); run lock still valid (${st#OK } min left)"
}

cmd_board() {
  check_repo
  local b="$WORK/board" sub="${1:-}"; shift || true
  [[ -d "$b" ]] || die "no board worktree; run setup"
  [[ "$(git -C "$b" rev-parse --abbrev-ref HEAD)" == "$BOARD_BRANCH" ]] || die "board worktree is not on $BOARD_BRANCH"
  case "$sub" in
    pull) git -C "$b" pull --quiet --rebase origin "$BOARD_BRANCH"; say "board @ $(git -C "$b" rev-parse --short HEAD)" ;;
    log)
      [[ $# -eq 1 && "$1" == "- "* && "$1" != *$'\n'* ]] || die 'board log needs ONE line starting with "- "'
      local f="$b/docs/agents/RUN_LOG.md" line="$1" agent word slug ttl
      agent="$(cut -d'|' -f2 <<<"$line" | sed 's/^ *//; s/ *$//')"
      word="$(cut -d'|' -f3 <<<"$line" | awk '{print toupper($1)}')"
      read -r slug ttl <<<"$(lock_slug "$agent")"
      local attempt lf="$b/$LOCK_DIR/${slug:-none}.lock" held="$WORK/agent_lock"
      if [[ -n "$slug" && "$word" == "SUCCESS" && -f "$held" ]] && is_cloud; then   # a SUCCESS claim needs a valid lock
        local fst; fst="$(lock_state 0)"
        [[ "$fst" == OK* ]] || die "run lock $fst: a SUCCESS final line is refused; write the final line INCOMPLETE (lock $fst) and end"
      fi
      for attempt in 1 2 3 4; do
        board_sync
        grep -q '^## Entries' "$f" || die "RUN_LOG.md has no \"## Entries\" heading"
        local msg="$line" lockop=""
        if [[ -n "$slug" && "$word" == "STARTED" ]] && is_cloud; then
          mkdir -p "$b/$LOCK_DIR"
          local dec tok since
          read -r dec tok since <<<"$(lock_py check "$lf")"
          if [[ "$dec" == "BUSY" ]]; then
            msg="- $(date -u +%Y-%m-%dT%H:%MZ) | $agent | IDLE | none (run lock held by run $tok since $since) | overlap lock: another $agent run is active; no claim, no change, no quantity | lock"
            log_insert "$f" "$msg"; git -C "$b" add docs/agents/RUN_LOG.md
            git -C "$b" commit --quiet -m "Run log: $agent idle (run lock held)"
            if AGENT_ENV_INTERNAL_PUSH=1 git -C "$b" push --quiet origin "HEAD:refs/heads/$BOARD_BRANCH" 2>/dev/null; then
              echo "AGENT_ENV LOCKED: another $agent run holds the run lock since $since; an IDLE final line was written; end this run now"
              exit 3
            fi
            continue
          fi
          local newtok="$(date -u +%Y%m%dT%H%M%S)-$$-$RANDOM"
          lock_py take "$lf" "$newtok" "$ttl" "$agent" >/dev/null
          [[ "$dec" == "STALE" ]] && msg="$msg | stale run lock of run $tok since $since recovered"
          git -C "$b" add "$LOCK_DIR/$slug.lock"; lockop="take $newtok"
        elif [[ -n "$slug" && "$word" != "STARTED" && -f "$held" ]]; then
          local hslug htok
          read -r hslug htok < "$held"
          if [[ "$hslug" == "$slug" && "$(lock_py holder "$lf")" == "$htok" ]]; then
            git -C "$b" rm --quiet "$LOCK_DIR/$slug.lock"; lockop="release"
          fi
        fi
        log_insert "$f" "$msg"
        git -C "$b" add docs/agents/RUN_LOG.md
        git -C "$b" commit --quiet -m "Run log: ${msg:2:60}"
        if AGENT_ENV_INTERNAL_PUSH=1 git -C "$b" push --quiet origin "HEAD:refs/heads/$BOARD_BRANCH" 2>/dev/null; then
          case "$lockop" in
            take*) echo "$slug ${lockop#take }" > "$held"; say "run lock $slug taken" ;;
            release) rm -f "$held"; say "run lock $slug released" ;;
          esac
          say "run-log line pushed @ $(git -C "$b" rev-parse --short HEAD)"; return 0
        fi
        git -C "$b" reset --quiet --keep HEAD~1   # drop only our unpushed commit (never other edits); re-sync, decide again
      done
      die "board log: push rejected four times" ;;
    commit)
      [[ $# -eq 1 && -n "$1" ]] || die "board commit needs one MESSAGE"
      require_lock
      local outside
      outside="$(git -C "$b" status --porcelain --untracked-files=all | awk '{print $NF}' | grep -v '^docs/agents/' || true)"
      [[ -z "$outside" ]] || die "changes outside docs/agents/ refused: $outside"
      git -C "$b" add -A docs/agents
      git -C "$b" diff --cached --quiet && { say "nothing to commit"; return 0; }
      git -C "$b" commit --quiet -m "$1"
      board_push; say "board pushed @ $(git -C "$b" rev-parse --short HEAD)" ;;
    check)
      git -C "$b" pull --quiet --rebase origin "$BOARD_BRANCH"
      local q="$b/docs/agents/dashboard/queue_check.py"
      [[ -f "$q" ]] || die "no queue_check.py on the board"
      python3 -I "$q" "$b/docs/agents" ;;
    *) die "board needs pull, log, commit or check" ;;
  esac
}

main() {
  local c="${1:-}"; shift || true
  case "$c" in
    setup) cmd_setup "$@" ;;
    status) cmd_status "$@" ;;
    selfcheck) check_repo; ensure_prepared; cmd_selfcheck "$@" ;;
    codemap) check_repo; ensure_prepared; cmd_codemap "$@" ;;
    freeze) check_repo; ensure_prepared; cmd_freeze "$@" ;;
    pytest) check_repo; ensure_prepared; cmd_pytest "$@" ;;
    run) check_repo; ensure_prepared; cmd_run "$@" ;;
    task) check_repo; ensure_prepared; cmd_task "$@" ;;
    decode) check_repo; ensure_prepared; cmd_decode "$@" ;;
    board) check_repo; ensure_prepared; cmd_board "$@" ;;
    lock) check_repo; ensure_prepared; cmd_lock "$@" ;;
    engine) check_repo; ensure_prepared; cmd_engine "$@" ;;
    *) sed -n '2,/^set -euo pipefail/{/^set -euo/!p}' "${BASH_SOURCE[0]}"; [[ -z "$c" ]] || exit 2 ;;
  esac
}
main "$@"
