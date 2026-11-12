"""T-740: build rules/rulebook/URBAN_COMPANY_RULEBOOK_1.2.0.json = 1.1.0 byte-for-byte record by record + the new owner
rule UP-FIN-PAINT-002 1.0.0 (paint area = plaster area of the same faces; owner 2026-11-12). 1.0.0 and 1.1.0 are never
edited; engine/source/company_rulebook_v1.py keeps reading 1.0.0 (no released or candidate method reads 1.2.0).

    python3 -I research/agents_t740/build_rulebook_1_2_0.py           # write the 1.2.0 file
    python3 -I research/agents_t740/build_rulebook_1_2_0.py --check   # exit 1 when the committed file differs
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.1.0.json"
OUT = ROOT / "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.2.0.json"

OWNER_WORDS = ("Paint, technically would be close enough to plastering (inside the building) outside will also should be "
               "the same, the difference is with the corners outside maybe only and lm for windows doors and corners, "
               "so the Area is the same.")

RECORD = {
    "rule_id": "UP-FIN-PAINT-002",
    "version": "1.0.0",
    "supersedes_in_scope": "UP-FIN-PAINT-001@1.0.0 (knowledge registry 1.0.0 .. 1.7.0, 'No paint over full-height "
                           "porcelain; one finish per face'): kept unchanged and still true; this record states the "
                           "paint AREA of every plastered face, of which the porcelain case is one term",
    "title": "Paint area = plaster area of the same faces, less the band above a false ceiling and the tiled part",
    "trade": "FINISHES",
    "level": 3,
    "basis": "OWNER CONFIRMED COMPANY RULE",
    "status": "OWNER_CONFIRMED",
    "scope": "every villa; every plastered face inside and outside (walls, stair shafts, reveals / returns, external "
             "elevations, fences, soffits where plastered); external paint (Sigma) follows the external plaster face "
             "by face",
    "params": {
        "paint_face": {
            "value": "PLASTER_FACE_MINUS_CEILING_BAND_MINUS_TILED",
            "unit": "m2",
            "note": "paint m2 = plaster m2 of the same face - the band between the finished (false) ceiling and the "
                    "plaster top (Q-72: plaster to the structural soffit, paint to the finished ceiling) - the tiled "
                    "part of the face (no paint on tiles); nothing else"
        },
        "ceiling_band": {
            "value": "FACE_LM_X_(PLASTER_TOP_MINUS_PAINT_TOP)_LESS_DEDUCTION_PARTS_IN_THE_BAND",
            "unit": "m2",
            "note": "an opening deducts width x its overlap with the band; a beam end deducts width x min(depth below "
                    "the soffit, band height); the part of a beam end deeper than the band is in the painted zone and "
                    "is a paint deduction too; no false ceiling (void / double height, stair shaft) = no band"
        },
        "edges": {
            "value": "LM_ITEMS_NOT_AREA",
            "unit": "lm",
            "note": "outside corners, beads and window / door edges are lm lines beside the m2, never extra paint area"
        },
        "held": {
            "value": "HELD_STAYS_HELD",
            "unit": "-",
            "note": "a HELD plaster face gives a HELD paint face (never 0); an unknown band or tile part gives an "
                    "AT_MOST paint face; ends of a held range are paired by scenario (low with low)"
        }
    },
    "method": [
        "per face: plaster m2 (both ends) -> band above the false ceiling (R-T740-2) -> tiled part -> paint m2",
        "a face wholly tiled (wet-wall render under full-height porcelain) has no paint face: 0 by the rule, a "
        "determined zero",
        "the engine paint line of a face is checked against the rule; any difference is named per ledger item "
        "(R-T740-3), never absorbed",
    ],
    "code": ["research/agents_t740/t740_rules.py::paint_face", "research/agents_t740/t740_rules.py::paint_faces",
             "research/agents_t740/t740_rules.py::band", "research/agents_t740/t740_rules.py::allocate"],
    "tests": ["tests/t740_paint_area_rule/test_t740.py"],
    "source": "owner 2026-11-12 (main chat), verbatim: '" + OWNER_WORDS + "'; confirmed in the same session: paint "
              "stops at the false ceiling (Q-72 kept) and tiled faces get no paint (agents/control BOARD top note "
              "'OWNER RULE 2026-11-12 (main chat; PAINT)', AGENT_BRIEF 'Paint area'); task T-740",
    "not_given": ["whether a door / window reveal (return) is priced as m2 paint like its plaster m2 (owner words: "
                  "'the Area is the same') or as an lm item (board paraphrase 'reveals' among the lm lines): both "
                  "readings shown, HELD for the Checker / Lead reading; no quantity released either way"],
}


def build():
    base_text = BASE.read_text(encoding="utf-8")
    d = json.loads(base_text)
    if d.get("version") != "1.1.0":
        raise SystemExit("base is not 1.1.0")
    out = copy.deepcopy(d)
    out["version"] = "1.2.0"
    out["supersedes"] = "1.1.0"
    out["provenance"] = (d["provenance"] + "; 1.2.0 (task T-740): new record UP-FIN-PAINT-002 1.0.0 from the owner "
                         "rule 2026-11-12 (main chat, verbatim in the record's source); every other record is "
                         "byte-for-byte the 1.1.0 record (base sha256 " + hashlib.sha256(base_text.encode("utf-8"))
                         .hexdigest()[:16] + ")")
    if any(r["rule_id"] == RECORD["rule_id"] for r in d["records"]):
        raise SystemExit("record already present")
    out["records"] = d["records"] + [RECORD]
    return json.dumps(out, indent=1, ensure_ascii=False) + "\n"


def main(argv):
    text = build()
    if "--check" in argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("rulebook 1.2.0 " + ("matches" if ok else "DIFFERS"))
        return 0 if ok else 1
    if OUT.exists():
        raise SystemExit("1.2.0 exists: a version file is never rewritten (use --check)")
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
