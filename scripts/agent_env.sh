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
#   setup                         prepare worktrees and venv (idempotent)
#   status                        repository, branches, worktrees and venv facts
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
# T is "engine" (default) or "task-<ID>".
set -euo pipefail

ENGINE_BRANCH="claude/access-permissions-setup-ii24ws"
BOARD_BRANCH="agents/control"
EXPECTED_REPO_RE='(^|[/:])msalfahad/Urban-Project-AI(\.git)?/?$'

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
  [[ "$url" =~ $EXPECTED_REPO_RE ]] || die "origin is not msalfahad/Urban-Project-AI: $url"
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

cmd_setup() {
  if [[ "${CLAUDE_CODE_REMOTE:-}" != "true" && "${AGENT_ENV_FORCE:-}" != "1" ]]; then
    say "not a cloud session; setup skipped"; return 0
  fi
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

  mkdir -p "$PRIVATE" && chmod 700 "$PRIVATE"
  cmd_status
}

cmd_status() {
  check_repo
  say "repo $(git -C "$ROOT" remote get-url origin | sed -E 's#.*[/:](msalfahad/Urban-Project-AI).*#\1#')"
  say "session checkout $(git -C "$ROOT" rev-parse --abbrev-ref HEAD) @ $(git -C "$ROOT" rev-parse --short HEAD)"
  [[ -d "$WORK/engine" ]] && say "engine $WORK/engine @ $(git -C "$WORK/engine" rev-parse --short HEAD) (origin/$ENGINE_BRANCH)"
  [[ -d "$WORK/board" ]] && say "board $WORK/board on $(git -C "$WORK/board" rev-parse --abbrev-ref HEAD) @ $(git -C "$WORK/board" rev-parse --short HEAD)"
  [[ -x "$PY" ]] && say "venv $("$PY" --version 2>&1) at $VENV"
  [[ -d "$PRIVATE" ]] && say "private drawings go only to $PRIVATE (git-excluded, outside every worktree)"
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

board_push() {  # push agents/control; on rejection rebase once and push again
  local b="$WORK/board"
  git -C "$b" push --quiet origin "HEAD:refs/heads/$BOARD_BRANCH" 2>/dev/null && return 0
  git -C "$b" pull --quiet --rebase origin "$BOARD_BRANCH" || die "board rebase failed"
  git -C "$b" push --quiet origin "HEAD:refs/heads/$BOARD_BRANCH" || die "board push rejected twice"
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
      git -C "$b" pull --quiet --rebase origin "$BOARD_BRANCH"
      local f="$b/docs/agents/RUN_LOG.md"
      grep -q '^## Entries' "$f" || die "RUN_LOG.md has no \"## Entries\" heading"
      LINE="$1" python3 -I -c 'import os,sys
p=sys.argv[1]; s=open(p,encoding="utf-8").read(); h="## Entries"; i=s.index(h)+len(h)
j=s.index("\n",i)+1
while s[j:j+1]=="\n": j+=1
open(p,"w",encoding="utf-8").write(s[:j]+os.environ["LINE"]+"\n"+s[j:])' "$f"
      git -C "$b" add docs/agents/RUN_LOG.md
      git -C "$b" commit --quiet -m "Run log: ${1:2:60}"
      board_push; say "run-log line pushed @ $(git -C "$b" rev-parse --short HEAD)" ;;
    commit)
      [[ $# -eq 1 && -n "$1" ]] || die "board commit needs one MESSAGE"
      local outside
      outside="$(git -C "$b" status --porcelain --untracked-files=all | awk '{print $NF}' | grep -v '^docs/agents/' || true)"
      [[ -z "$outside" ]] || die "changes outside docs/agents/ refused: $outside"
      git -C "$b" add -A docs/agents
      git -C "$b" diff --cached --quiet && { say "nothing to commit"; return 0; }
      git -C "$b" commit --quiet -m "$1"
      board_push; say "board pushed @ $(git -C "$b" rev-parse --short HEAD)" ;;
    *) die "board needs pull, log or commit" ;;
  esac
}

main() {
  local c="${1:-}"; shift || true
  case "$c" in
    setup) cmd_setup "$@" ;;
    status) cmd_status "$@" ;;
    selfcheck) cmd_selfcheck "$@" ;;
    codemap) cmd_codemap "$@" ;;
    freeze) cmd_freeze "$@" ;;
    pytest) cmd_pytest "$@" ;;
    run) cmd_run "$@" ;;
    task) cmd_task "$@" ;;
    decode) cmd_decode "$@" ;;
    board) cmd_board "$@" ;;
    *) sed -n '2,31p' "${BASH_SOURCE[0]}"; [[ -z "$c" ]] || exit 2 ;;
  esac
}
main "$@"
