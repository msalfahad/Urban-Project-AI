"""Phase 2B-5 Stage D: the repo-local Urban skills (.claude/skills/urban-*). Each has its frontmatter (name = folder,
a description), the eight sections (purpose, trigger, inputs, tools, safety, outputs, tests, escalation), and every
repository path it cites exists; none carries a private path or a credential, and each states its privacy rule."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ("urban-cad-audit", "urban-boq-proof", "urban-mcp-benchmark", "urban-floorplan-vision-review",
          "urban-freeze-integrity", "urban-rule-reconciliation")
SECTIONS = ("Purpose", "Trigger", "Inputs", "Tools", "Safety", "Outputs", "Tests", "Escalation")
PATH = re.compile(r"`((?:tests|tools|engine|research|knowledge|rules)/[^`\s:]+)")


@pytest.mark.parametrize("name", SKILLS)
def test_a_skill_is_complete(name):
    text = (ROOT / ".claude" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
    head = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", text)
    assert head and head.group(1).strip() == name and len(head.group(2)) > 60
    for s in SECTIONS:
        assert re.search(rf"^## {s}\b", text, re.M), (name, s)
    for p in PATH.findall(text):
        assert (ROOT / p).exists(), (name, p)
    private = ("scratchpad", "restore_zip", "P77" + "57", r"BEGIN [A-Z ]*PRIVATE KEY", r"api[_-]?key\s*=")
    assert not re.search("|".join(private), text, re.I)        # the project code split: the source never spells it
    safety = text.split("## Safety", 1)[1].split("\n## ", 1)[0].lower()
    assert "private" in safety or "frozen" in safety
