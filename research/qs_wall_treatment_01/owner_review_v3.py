"""OWNER REVIEW v3 - v2 plus the owner-verified plan layer: what the
verification resolved, what it changed forward, the SALOON card, and the
residual decisions.

    python3 -m research.qs_wall_treatment_01.owner_review_v3
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P
from research.qs_wall_treatment_01.owner_review_v2 import build as build_v2

OUT = Path(P.OUT_DIR)


def build() -> str:
    oe = json.loads((OUT / "OWNER_EVIDENCE_RECONCILIATION.json").read_text("utf-8"))
    est = json.loads((OUT / "P7757_WALL_TREATMENT_ESTIMATE_v3.json").read_text("utf-8"))
    dual = json.loads((OUT / "DUAL_BASIS_v3.json").read_text("utf-8"))
    ag = est["AGGREGATES"]
    L = ["# P7757 wall treatment - owner review v3 (owner-verified plan layer)", "",
         "The owner's manual plan verification is a new evidence layer "
         "(SOURCE = ARCHITECTURAL_PLAN, INTERPRETATION = OWNER_VERIFIED_DIMENSION_OWNERSHIP). "
         "No frozen output was rewritten; the forward reconciliation and estimate v3 rest on it.",
         "", "## WHAT THE VERIFICATION SETTLED", "",
         "| printed | owner role | authored span (DWG) | text | CAD endpoints |", "|---|---|---|---|---|"]
    for s in oe["PRINTED_SEGMENTS_VS_AUTHORED"]:
        L.append(f"| {s['ID']} | {s['WHAT']} | {s['AUTHORED_SPAN_M']} | {s['DIMENSION_TEXT_CORRECTNESS']} | "
                 f"{s['CAD_OBJECT_CORRESPONDENCE']} |")
    L += ["", "- 90 + 633 + 90 is the exterior setting-out chain; the 20 beside it is wall thickness "
              "(DIMENSION_CHAIN_SEGMENT != WALL_THICKNESS). Both 90s are corroborated to the "
              "millimetre by authored lines: the lower from the neighbour wall's outer face to the "
              "glazing start, the upper from the glazing end to a door-layer line 0.232 past the "
              "return wall. Neither is an exposed plaster face.",
          "- The previous statement that the upper 90 'matches no authored span' is withdrawn.",
          "- 40 + 452 + 45 is corroborated as the next exterior sequence (door-layer jamb marks) and "
          "kept distinct.",
          "- 515 runs from the sea-view wall line to the return line at the column before the GARDEN "
          "(5.1499 authored). It is the SALOON-side face run; 0.70 of it is a column-bonding "
          "candidate (S-COL.BON hatch in the wall) - a trade split, not additive.",
          "", "## PRINTED DIMENSION vs CAD FACE vs PLASTER FACE", "",
          "| printed object | CAD face object | plaster-contributing face | ownership |", "|---|---|---|---|"]
    for o in oe["PLASTER_FACE_OWNERSHIP"]:
        pf = o["PLASTER_CONTRIBUTING_FACE"]
        pf_s = ("none (glazing)" if pf is None else ", ".join(
            f"{k} {v.get('LENGTH_M')}" for k, v in pf.items()))
        L.append(f"| {o['PRINTED_DIMENSION_OBJECT']} | {o['CAD_FACE_OBJECT']} | {pf_s} | {o['PLASTER_FACE_OWNERSHIP']} |")
    L += ["", f"Card: `{oe['SALOON_CARD']['IMAGE']}` - blue spans are setting-out only, green faces "
              "contribute plaster, the 20 is thickness.",
          "", "## ESTIMATE v3 (established subtotals, never totals)", "",
          "| trade | established m2 | provisional m2 (apart) |", "|---|---|---|"]
    for k, v in ag["BY_TRADE"].items():
        if v["ESTABLISHED_SUBTOTAL_M2"] or v["PROVISIONAL_SUBTOTAL_M2"]:
            L.append(f"| {k} | {v['ESTABLISHED_SUBTOTAL_M2']} | {v['PROVISIONAL_SUBTOTAL_M2']} |")
    L += [f"| project (traced subset) | {ag['PROJECT']['ESTABLISHED_SUBTOTAL_M2']} | "
          f"{ag['PROJECT']['PROVISIONAL_SUBTOTAL_M2']} |",
          "", f"Contractor basis on the same established faces: "
              f"{dual['PROJECT']['CONTRACTOR_ON_THE_SAME_FACES_M2']} m2; the delta "
              f"{dual['PROJECT']['DELTA_ON_COMPARABLE_FACES_M2']} m2 is entirely HEIGHT (3.20 vs 3.60).",
          "", "## DECISION D2 UPDATED", "",
          f"- {oe['D2_UPDATE']}. Option B (a return wall of 1.45 m ending in a column, plasterable on "
          "the SALOON side) is now the technically supported reading; the height of that return "
          "and whether it is full height or a low wall remains the owner's call.",
          "", "---", "", "# Appendix: review v2 (unchanged)", ""]
    return "\n".join(L) + "\n" + build_v2()


if __name__ == "__main__":
    p = OUT / "OWNER_REVIEW_V3.md"
    p.write_text(build(), encoding="utf-8")
    print(json.dumps({"OWNER_REVIEW_V3_SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}))
