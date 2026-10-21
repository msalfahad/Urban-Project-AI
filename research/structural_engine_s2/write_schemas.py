"""Write the five generic S2 schemas (project-independent) from the engine modules.

    python research/structural_engine_s2/write_schemas.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from engine.source import engineering_flags, project_claims, question_helper, rule_promotion, structural_authority  # noqa

for mod in (engineering_flags, structural_authority, project_claims, question_helper, rule_promotion):
    s = mod.schema()
    (HERE / f"{s['schema']}.json").write_text(json.dumps(s, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                             encoding="utf-8")
    print(s["schema"])
