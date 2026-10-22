"""T-167: the route G profile restricted to owner Q-17 A (spec C = V29_ROUTEG_Q17A).

Input (both tracked, both left untouched):
  research/urban_engine_m4_correctness/profile_st7757_m4.json         the typed M4 profile (17 values)
  research/urban_engine_m4_correctness/project_data_st7757_t064.json  the controlled project data file (T-064, merged
      8ceeeb2; URBAN_PROJECT_DATA_FILE_V1, owner Q-17 A): 13 DRAWING-VERIFIED + 1 INFERRED (NECK_TOP_LEVEL_M) usable,
      3 HELD (FOUNDING_DEPTH_M: owner Q-21 C; CB_SUPPORT_BAR_EXTENT_FRAC: T-044 DIFFERENT; CB_SUPPORT_BAR_SPAN_BASIS:
      T-044 NOT_PRINTED)
Output: research/agents_t167/profile_st7757_q17a.json = the M4 profile with ONLY the values the data file makes usable,
each checked against its data-file record by engine.source.arch_v304.check_profile (value, unit, range ends = the record
value or a usable printed alternative). Every other field is copied unchanged.

    python3 -I research/agents_t167/build_q17a_profile.py           # rewrite
    python3 -I research/agents_t167/build_q17a_profile.py --check   # exit 1 if the committed file differs
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v304 as A304          # noqa: E402
from engine.source import project_data_file as PDF   # noqa: E402

M4 = ROOT / "research/urban_engine_m4_correctness/profile_st7757_m4.json"
DATA = ROOT / "research/urban_engine_m4_correctness/project_data_st7757_t064.json"
OUT = Path(__file__).resolve().parent / "profile_st7757_q17a.json"


def build():
    prof = json.loads(M4.read_text(encoding="utf-8"))
    df = json.loads(DATA.read_text(encoding="utf-8"))
    pdf = PDF.load(df)
    usable = set(pdf.summary()["usable"])
    held = sorted(set(c["id"] for c in prof["conventions"]) - usable)
    inp = {"schema": A304.INPUTS_SCHEMA, "project": None,
           "data_file": {"file": DATA.name, "sha256": "-", "doc": df},
           "runs": [{"id": A304.RESTRICTED, "removed_keys": held, "profile_sha256": "-",
                     "lines_sha256": A304.lines_sha256([]), "lines": []}]}
    chk = A304.check_profile(A304.load_inputs(inp), prof)          # refuses on any value / unit / range mismatch
    out = dict(prof, profile=prof["profile"] + "_Q17A",
               confirmed_by="T-167: the ST7757_M4 profile restricted to the values the owner Q-17 A project data file "
                            f"({DATA.name}) makes usable (DRAWING-VERIFIED / INFERRED); removed: {', '.join(held)}",
               manual_inputs=len(chk["usable"]),
               conventions=[c for c in prof["conventions"] if c["id"] in usable])
    return json.dumps(out, ensure_ascii=False, indent=1) + "\n", chk


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    text, chk = build()
    if "--check" in argv:
        same = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("profile_st7757_q17a.json", "UP TO DATE" if same else "DIFFERS")
        return 0 if same else 1
    OUT.write_text(text, encoding="utf-8")
    print(json.dumps({"usable": chk["usable"], "removed": chk["not_usable"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
