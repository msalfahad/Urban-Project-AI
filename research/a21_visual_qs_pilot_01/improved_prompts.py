"""Build the improved-run prompts FROM the frozen baseline prompt bytes.

The rules are not retyped and not reworded. They are read out of the
frozen baseline prompt files and carried across unchanged, so "the rules
were not tuned in response to the baseline answers" is something the diff
proves rather than something I assert.

Exactly ONE edit is permitted, and it is recorded: the sandbox path,
because it is a different directory. Nothing else moves - not the rules,
not the height hierarchy, not the defaults, not the refusal codes, not
the schema, and not even the sentence telling the reader to look at the
images. The description of how the packet is laid out lives in TASK.json,
where the baseline's packet description also lived, so the prompt itself
is byte-identical apart from a path.

(Pass 2 adds one sentence forbidding a read of a previous run's output,
exactly as the baseline's pass 2 did.)

    python3 -m research.a21_visual_qs_pilot_01.improved_prompts
"""

from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path

from research.a21_visual_qs_pilot_01 import improved_protocol as IP

OUT = Path("data/experiments/A21_VISUAL_QS_PILOT_01")
BASE = OUT / "prompts"
DEST = OUT / "prompts_improved"

BASELINE_PROMPT_SHA256 = {
    "GROUP_A_CASES_1_3.txt":
        "9369c49d4d298eee04dbcabbbb1d93f3ec70319c76564553e31909af28ff36c1",
    "GROUP_B_CASES_4_6.txt":
        "6d6f42a164799a3cb88e5645048935a55231e809783653106bab0e449cfb7cb9",
}

OLD_BASE = ("/home/user/Urban-Project-AI/data/experiments/"
            "A21_VISUAL_QS_PILOT_01/a21_sandbox/")
NEW_BASE = ("/home/user/Urban-Project-AI/data/experiments/"
            "A21_VISUAL_QS_PILOT_01/a21_sandbox_improved/")

# The reading sentence differs between the two baseline prompts and BOTH
# are left exactly as they are. How the packet is laid out is stated in
# TASK.json, not here.


def build(pass_no: int) -> dict:
    DEST.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, expected in BASELINE_PROMPT_SHA256.items():
        raw = (BASE / name).read_bytes()
        got = hashlib.sha256(raw).hexdigest()
        if got != expected:
            raise SystemExit(f"the frozen baseline prompt {name} has moved")
        text = raw.decode("utf-8")

        assert OLD_BASE in text, name
        new = text.replace(OLD_BASE, NEW_BASE)

        # CASE-6 gains SECTION_B_B: that is in TASK.json, not the prompt,
        # so group B's prompt needs no case-specific edit.
        if pass_no == 2:
            new = new.replace(
                "Do NOT read any other directory,",
                "Do NOT read any other directory, do NOT read anything "
                "under a previous run's output directory,")

        dest = DEST / f"PASS{pass_no}_{name}"
        dest.write_text(new, encoding="utf-8")
        diff = [ln for ln in difflib.unified_diff(
            text.splitlines(), new.splitlines(), lineterm="", n=0)
            if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---"))]
        out[dest.name] = {
            "BUILT_FROM": name,
            "BASELINE_SHA256": expected,
            "SHA256": hashlib.sha256(dest.read_bytes()).hexdigest(),
            "CHANGED_LINES": len(diff) // 2,
            "DECLARED_DELTAS": diff,
        }
    return out


def main() -> int:
    IP.assert_baseline_intact()
    records = {1: build(1), 2: build(2)}
    # every reader-visible prompt byte must survive the feedback screen
    leaks = []
    for p in sorted(DEST.glob("*.txt")):
        t = p.read_text("utf-8")
        for bad in IP.FEEDBACK_SCREEN:
            if bad in t:
                leaks.append({"file": p.name, "carries": bad})
    if leaks:
        raise SystemExit(f"a prompt carries a baseline result: {leaks}")

    rec = OUT / "IMPROVED_PROMPT_RECORD.json"
    body = {
        "RUN_ID": IP.RUN_ID,
        "PROMPTS_ARE_NOT_TUNED": IP.PROMPTS_ARE_NOT_TUNED,
        "HOW_THIS_IS_PROVED": (
            "each improved prompt is generated FROM the frozen baseline "
            "prompt bytes, whose hash is checked first. The unified diff "
            "of every edit is recorded below. One line differs per "
            "prompt - the sandbox path - plus pass 2's isolation "
            "sentence. The QS rules, the height hierarchy, the default "
            "policy, the refusal codes and the output schema appear in "
            "no diff line"),
        "PASSES": {str(k): v for k, v in records.items()},
        "NO_BASELINE_RESULT_IS_IN_ANY_PROMPT": True,
    }
    rec.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(json.dumps({
        "PROMPT_RECORD_SHA256": hashlib.sha256(rec.read_bytes()).hexdigest(),
        "files": {k: v["SHA256"] for p in records.values()
                  for k, v in p.items()},
        "changed_lines_per_file": {k: v["CHANGED_LINES"]
                                   for p in records.values()
                                   for k, v in p.items()},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
