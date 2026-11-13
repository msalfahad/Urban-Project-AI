"""T-755 (B): concrete HELD-tail measurability sweep on ARCH_TAKEOFF_V3.0.77 (research only; nothing wired).

    bash scripts/agent_env.sh run --tree task-T-755 research/agents_t755/t755_concrete_sweep.py

Reads research/agents_t755/out/T755_CENSUS.json (the per-line cause of every HELD STR.CONC.* line of V3.0.77 and its
index state) and the drawing reads of this task (READS below: DXF handles and lengths only, own decode of the Drive
copies). Every line gets STILL_HELD with the drawing fact named, or MEASURABLE_NOW with the drawn dimension and m3 by
hand. Writes research/agents_t755/out/T755_CONCRETE_SWEEP.json and .md. No coordinates, no names, no cause text.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t755_rules as R  # noqa: E402

CENSUS = HERE / "out" / "T755_CENSUS.json"

# What holds each cause bucket of the concrete tail, as the drawings stand (own re-read this task where marked READ;
# otherwise the merged, Checker-verified piece that last read it). 'item' = the Lead's list item or the proposal.
BUCKET_FACT = {
    "D-02": ("beam width: schedule vs drawn differ (CB10 kind)", "1"),
    "D-03": ("two marks on one beam", "1"),
    "D-04": ("unlabelled beam piece: no mark, depth row not printed", "1"),
    "D-27": ("beam width: schedule vs drawn differ", "1"),
    "D-05+D-26": ("edge projection: no section / mark / bars / material printed (T-660 / T-721)", "1 (propose: add D-05, D-26)"),
    "D-26": ("edge projection: no section / mark / bars / material printed (T-660 / T-721)", "1 (propose: add D-26)"),
    "D-28": ("east dome-opening ring: no mark, depth 'AS PER ARCH' (T-721 / T-724)", "1 (propose: add D-28)"),
    "D-16": ("column C8: schedule section vs drawn outline differ", "3"),
    "D-66": ("column band: schedule section vs drawn outline differ (13 columns; live cause D-66 = RFI-S20 since "
             "V3.0.42 F-T433-2; the retired D-63 is not read, R-T755-1 v2)", "3"),
    "D-39+D-66": ("column section conflict + roof slab top not printed", "3, 5"),
    "D-44": ("B15 up / down-stand on the tank columns", "1, 3"),
    "D-44+D-66": ("B15 up / down-stand + tank column section conflict", "1, 3"),
    "D-33": ("ground beam carrying a landing / framing beam: section not printed", "4"),
    "D-34": ("ground-beam title by span: no precedence printed", "4"),
    "D-35": ("exterior / annex / court ground-beam depth: 'FOLLOW ARCH.', levels not printed", "4"),
    "D-39": ("roof slab top not printed (finished marks only); parapet build-up / height", "5"),
    "D-43": ("lift pit raft depth 'as per lift manufacturer'; tie-beam section not printed. Pit walls L-684fcad3: live "
             "rfi (V3.0.73) cites D-43 for the supplier pit depth although V3.0.42 F-T433-1 retired D-43 from it "
             "(register: D-43 = GF lift tie-beam size): finding F-T755-5", "6"),
    "D-45": ("opening head not drawn on any sheet (lift landing doors, P-GF-01)", "2, 12"),
    "D-08": ("ST-02 round stair: curved treads / helicoid soffit not dimensioned", "7"),
    "D-56": ("ST-03 E1 waist not drawn (D-56 is OUT of the package: re-state under D-67 / D-68)", "7"),
    "D-14": ("blinding projection past the plot line", "none (propose: add D-14)"),
    "Q-28": ("owner question Q-28 (boundary band section / founding level)", "owner, not designer"),
    "Q-31": ("owner question Q-31 (one outline, two footing tags)", "owner, not designer"),
    "Q-51": ("owner question Q-51 (stair reading)", "owner, not designer"),
    "Q-55": ("owner rule Q-55 C fallback door head (existence / spare)", "owner rule, not designer"),
    "Q-67": ("owner question Q-67 side-passage FFL", "owner, not designer"),
    "RFI-S04": ("boundary pad count / spacing not printed (old RFI code)", "none (propose: restate as D-id)"),
    "RFI-S08+RFI-S23": ("lift raft blinding projection (old RFI codes)", "6 (propose: restate as D-id)"),
    "NO_SINGLE_VALUE": ("neck: founding level not printed (minimum 1.50 m below EG only)", "none (propose: new D-id 'founding level per footing')"),
    "DESIGNER_TAG": ("named designer datum with no D-number (lintel bearings MIN 40 cm, neck founding level, dome-ring soffit, sill / head, pool steps, strap / blinding)", "none (propose: D-ids, L-T716-1)"),
    "STRAP_BLINDING_NOT_PRINTED": ("strap blinding not printed", "none (propose: D-id)"),
    "FOOTING_DETAIL_CHOICE_OPEN": ("footing blinding: governing detail choice open", "none (propose: D-id)"),
    "NOT_PRINTED": ("boundary pad count not printed ('SEE ARCH PLAN', none drawn)", "none (propose: D-id)"),
    "SILENT_OMISSION": ("DOME-3 tower dome: no structural drawing (D-21 in T-647; the line text lost the id)", "none (propose: add D-21, restate the line)"),
    "NAMED_TEXT": ("see READS (the only line: D-GF-14 lintel)", "-"),
}

# Own drawing reads this task (Drive 'Alsenan chalet project' / 'P7757_DXF_COMPRESSED.zip' inner P7757.dxf ab54dd55 and
# 'ST7757 dxf.dxf' 9f9d1179, decoded by the wrapper into the private folder). Handles and lengths only.
READS = {
    "L-17953d7882899d43473f": {
        "member": "lintel over door D-GF-14 in wall GF-W30 (0.15 black block, horizontal run)",
        "was": "T-699: MEASURABLE NOW (no jamb evidence; 'a read of the GF-W30 run, pieces, both jamb stoppers')",
        "read": ("P7757 GF plan: wall faces 2E5 (N) / 2E7 (S) end at the door; 2E6 / 2E8 restart after it; door frame "
                 "lines 32D / 32E and 32B / 32C (layer D, 0.050 frame each side), leaf arc 334 r 0.690: masonry clear "
                 "gap 0.800 m (hand run T-103 0.797). West pier 0.2787 m (N face, to the diagonal wall face 325) .. "
                 "0.3727 m (S face, to 319): ends on a WALL JUNCTION. East pier 0.0392 m (2E6 / 2E8) to the face of "
                 "the crossing wall WB-FL0059-FL0060 (2DD / 2DE, 0.150): ends on a WALL JUNCTION."),
        "result": "STILL_HELD",
        "cause_now": ("METHOD GAP: both ends are wall junctions = R-T678-3 OPEN ends (no recorded stopper), the same "
                      "junction-END ruling as D-GF-04 / D-1F-06 (Lead / Checker, not an owner question). Both drawn "
                      "piers are below the printed MIN 0.40 bearing (deficit on any ruling). Existence OPEN (head "
                      "basis Q-55 C 2.20 ASSUMED - OWNER-APPROVED). Conditional lo unchanged 0.15 x 0.20 x 0.800 = "
                      "0.024 m3 (if REQUIRED); no AT_MOST until the junction-END ruling."),
        "if_junction_is_end_of_masonry": ("hi = 0.15 x 0.20 x (0.800 + 0.3727 + 0.0392) = 0.036357 m3 (S face, "
                                          "largest pier) - NOT a bound: stated so the ruling's effect is known"),
        "m3_by_hand": None,
    },
    "L-d5401fa8986900c66c37": {
        "member": "DOME-3 tower dome shell over the 2F maid room",
        "was": "SILENT_OMISSION reason code only (T-647 had it as D-21)",
        "read": ("ST7757 DXF: one dome detail title only ('DETAIL OF DOME', text 1A18), the detail T-193 used for the two "
                 "terrace domes (VERIFIED); no dome / ring / opening drawn on the 2F roof slab of the structural set "
                 "(T-287 G3, T-647)."),
        "result": "STILL_HELD",
        "cause_now": "D-21 (no structural drawing of the third dome); the line should cite D-21; D-21 is in no list item",
        "m3_by_hand": None,
    },
}


def build() -> dict:
    s = json.loads(CENSUS.read_text(encoding="utf-8"))
    rows = []
    for r in s["concrete_held"]:
        rd = READS.get(r["line_id"])
        fact, item = BUCKET_FACT.get(r["bucket"], (None, None))
        if fact is None:
            raise SystemExit(f"{r['line_id']}: bucket {r['bucket']} has no named drawing fact")
        rows.append(dict(r, result=(rd or {}).get("result", "STILL_HELD"), fact=fact, list_item=item,
                         read=bool(rd)))
    by = defaultdict(lambda: Counter())
    vals = defaultdict(lambda: {"range_low": 0.0, "range_high": 0.0})
    for r in rows:
        k = (r["item_code"], r["bucket"])
        by[k][r["side"]] += 1
        if r["side"] == "RANGE":
            vals[k]["range_low"] += r["low"]
            vals[k]["range_high"] += r["high"]
    groups = [{"item_code": c, "bucket": b, "sides": dict(sorted(n.items())), "lines": sum(n.values()),
               "range_low": round(vals[(c, b)]["range_low"], 6), "range_high": round(vals[(c, b)]["range_high"], 6),
               "fact": BUCKET_FACT[b][0], "list_item": BUCKET_FACT[b][1]}
              for (c, b), n in sorted(by.items())]
    res = Counter(r["result"] for r in rows)
    assert sum(g["lines"] for g in groups) == len(rows)
    return {"schema": "URBAN_T755_CONCRETE_SWEEP_V1", "candidate": s["candidate"], "lines": len(rows),
            "result": dict(res), "measurable_now": [r["line_id"] for r in rows if r["result"] == "MEASURABLE_NOW"],
            "groups": groups, "reads": READS, "rows": rows}


def markdown(x: dict) -> str:
    o = [f"# T-755 (B) concrete HELD tail of {x['candidate']}: STILL_HELD or MEASURABLE_NOW", "",
         f"{x['lines']} HELD STR.CONC.* lines (m3). Result: {x['result']}. MEASURABLE_NOW: "
         f"{', '.join(x['measurable_now']) or 'none'}. Per family and cause; a RANGE is the sum of its bounded lines "
         "only; blank lines are counted, never 0; one-sided bounds beside a blank line are in the line records.", "",
         "| family | cause bucket | lines | sides | bounded low .. high m3 | drawing fact that holds it | list item |",
         "|---|---|---|---|---|---|---|"]
    for g in x["groups"]:
        rng = f"{g['range_low']:.6g} .. {g['range_high']:.6g}" if g["sides"].get("RANGE") else "-"
        o.append(f"| {g['item_code'][9:]} | {g['bucket']} | {g['lines']} | "
                 + ", ".join(f"{k} {v}" for k, v in g["sides"].items()) + f" | {rng} | {g['fact']} | {g['list_item']} |")
    o += ["", "## Own drawing reads", ""]
    for lid, rd in x["reads"].items():
        o.append(f"- **{lid}** {rd['member']}. Was: {rd['was']}. Read: {rd['read']} Result: {rd['result']}: "
                 f"{rd['cause_now']}" + (f" ({rd['if_junction_is_end_of_masonry']})"
                                         if rd.get("if_junction_is_end_of_masonry") else ""))
    return "\n".join(o) + "\n"


def main(argv):
    x = build()
    (HERE / "out" / "T755_CONCRETE_SWEEP.json").write_bytes(R.canonical(x))
    (HERE / "out" / "T755_CONCRETE_SWEEP.md").write_text(markdown(x), encoding="utf-8")
    print(x["lines"], x["result"], "measurable_now", x["measurable_now"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
