"""T-468: writes research/agents_t468/STATUS_VOCABULARY_V1.md from engine/source/status_vocabulary_v1.markdown().

    python3 -I research/agents_t468/build_status_table.py [--check]

--check exits 1 when the committed table differs from the module (tests/t468_status_vocabulary pins the same)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import status_vocabulary_v1 as SV  # noqa: E402

OUT = ROOT / "research" / "agents_t468" / "STATUS_VOCABULARY_V1.md"

if __name__ == "__main__":
    text = SV.markdown()
    if "--check" in sys.argv[1:]:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("STATUS_VOCABULARY_V1.md " + ("current" if ok else "STALE"))
        sys.exit(0 if ok else 1)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(SV.table_rows())} mapped words)")
