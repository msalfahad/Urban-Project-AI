# Urban-Project-AI: scheduled-agent operating rules (main branch)

This repository belongs to the owner (msalfahad). Its scheduled agents (Lead, three Workers, Verifier) work only in this
repository. `main` holds no engine code: it holds this file, `.claude/settings.json` and `scripts/agent_env.sh`.

## Where the work is

At session start the hook runs `bash scripts/agent_env.sh setup`, which prepares, inside this checkout:

| Path | What it is |
|---|---|
| `.work/engine` | worktree of `claude/access-permissions-setup-ii24ws`: the BOQ engine, tests, tools. Read `.work/engine/CLAUDE.md` before any engine work; its rules govern the engine. |
| `.work/board` | worktree of `agents/control`: the board under `docs/agents/` (BOARD, RUN_LOG, OWNER_QUESTIONS). |
| `.work/task-<ID>` | worktree of `agents/task-<ID>`, made by `bash scripts/agent_env.sh task <ID>`. |
| `.work/venv` | Python 3.11 venv from the engine's pinned `requirements.txt`. |
| `.work/private` | private Drive copies, mode 700, git-excluded, outside every worktree. |

If setup printed `AGENT_ENV FAIL`, record the run as BLOCKED with that line and stop code work.

## How to run things

Run every command from this checkout's root. The project's checks go through the fixed wrapper, which is the only
pre-approved command:

- `bash scripts/agent_env.sh selfcheck [--tree T]`: codemap check, `pytest tests/t061_room_label_guard`, freeze check
- `bash scripts/agent_env.sh codemap [--tree T] route|impact|check|build ...`
- `bash scripts/agent_env.sh pytest [--tree T] tests/<folder or file> ...`
- `bash scripts/agent_env.sh freeze [--tree T]`
- `bash scripts/agent_env.sh run [--tree T] tools/alsenan_scoreboard.py|tools/alsenan_keymap.py ...`
- `bash scripts/agent_env.sh task <ID>` and `bash scripts/agent_env.sh decode <SRC> <NAME>`

Git work happens in the worktrees with `git -C .work/<tree> ...`, against `origin` only: commits, `git pull --rebase`,
and normal pushes of `agents/control` (board files under `docs/agents/` only) and of the agent's own `agents/task-<ID>`
branch. The Verifier alone also pushes a verified merge to `claude/access-permissions-setup-ii24ws`.

## Never

- Clone, fetch from, attach (add_repo) or push to any other repository. This repository is the only one.
- Push to `main`, force-push, rewrite published history, delete branches, or change remotes.
- Create, change or fire scheduled tasks or sessions.
- Write to Google Drive. Drive is read-only.
- Edit frozen engine methods or existing rule / knowledge version files, or release an unverified quantity.

## Private client drawings

The client drawings and the freelancer workbooks on Google Drive are the owner's private project data, which these
agents are meant to read. The intended and only flow:

1. Download with the Google Drive connector (read tools only).
2. Decode with `bash scripts/agent_env.sh decode <downloaded file> <name>`, which writes only into `.work/private`.
3. Read them there with the engine's own tools.

This repository is PUBLIC. Never copy a drawing, a workbook, their contents, client names or personal data into any
tracked file, commit, branch, board text, test or log. Refer to a file only by its Drive folder and title.

## Run records

- Every run writes a `STARTED` line at the top of `## Entries` in `.work/board/docs/agents/RUN_LOG.md` before it claims
  a task. It ends with one final line: SUCCESS, BLOCKED, FAILED or INCOMPLETE, with the exact text of any refused command.
- A scheduler "succeeded" is not a successful run, and a successful run is not an engineering verification.
- Engineering verification is recorded only by the Verifier, on the board.
