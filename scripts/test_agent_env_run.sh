#!/usr/bin/env bash
# Test: `agent_env.sh run` (owner 2026-11-07). Allowed: the two scoreboard tools and research/agents_t*/*.py, a regular
# file directly in that folder of a .work tree, run with python -I. Refused: '..', symlinks (file, folder, research/,
# tree), sub-folders, other paths, a tree outside .work. Builds a throw-away fake checkout; touches nothing real.
# Run by the owner's main chat: bash scripts/test_agent_env_run.sh
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
fail() { echo "TEST FAIL: $*"; exit 1; }
ok() { echo "TEST OK: $*"; }

R="$TMP/msalfahad/Urban-Project-AI"; mkdir -p "$R/scripts"
cp "$HERE/scripts/agent_env.sh" "$R/scripts/agent_env.sh"
git -C "$R" init --quiet && git -C "$R" remote add origin "https://github.com/msalfahad/Urban-Project-AI.git"
mkdir -p "$R/.work/board" "$R/.work/venv/bin" "$R/.work/engine/research/agents_t999/sub" "$TMP/outside/research/agents_t998"
ln -s "$(command -v python3)" "$R/.work/venv/bin/python"
E="$R/.work/engine/research"
printf 'import sys\nprint("RAN", sys.flags.isolated, *sys.argv[1:])\n' > "$E/agents_t999/hello.py"
cp "$E/agents_t999/hello.py" "$E/agents_t999/sub/deep.py"
cp "$E/agents_t999/hello.py" "$TMP/outside/research/agents_t998/evil.py"
ln -s "$TMP/outside/research/agents_t998/evil.py" "$E/agents_t999/link.py"
ln -s "$TMP/outside/research/agents_t998" "$E/agents_t997"
run() { (cd "$R" && bash scripts/agent_env.sh run "$@" 2>&1); }

# allowed: a regular research script runs, isolated (-I), with its arguments
out="$(run research/agents_t999/hello.py a b)" || fail "allowed script refused: $out"
[[ "$out" == "RAN 1 a b" ]] || fail "unexpected output: $out"
ok "research/agents_t999/hello.py ran with python -I and its arguments"

refused() {  # $1 label, rest the run arguments
  local label="$1"; shift; local o
  o="$(run "$@")" && fail "$label was NOT refused: $o"
  grep -q "AGENT_ENV FAIL" <<<"$o" || fail "$label: no refusal text: $o"
  ok "refused: $label -> $(grep -o "AGENT_ENV FAIL.*" <<<"$o" | head -1)"
}
refused "'..' in the path"            research/agents_t999/../agents_t999/hello.py
refused "'..' escaping the tree"       research/agents_t999/../../../outside/research/agents_t998/evil.py
refused "symlinked script file"        research/agents_t999/link.py
refused "symlinked agents folder"      research/agents_t997/evil.py
refused "sub-folder"                   research/agents_t999/sub/deep.py
refused "absolute path"                "$E/agents_t999/hello.py"
refused "other folder"                 tools/other.py
refused "not agents_t<digit>"          research/agents_x/hello.py
refused "missing script"               research/agents_t999/none.py

# a tree that is a symlink out of .work is refused
mkdir -p "$TMP/outside/tree/research/agents_t999"; cp "$E/agents_t999/hello.py" "$TMP/outside/tree/research/agents_t999/"
ln -s "$TMP/outside/tree" "$R/.work/task-T1"
refused "tree outside .work (symlinked task tree)" --tree task-T1 research/agents_t999/hello.py

echo "ALL RUN-WRAPPER TESTS PASSED"
