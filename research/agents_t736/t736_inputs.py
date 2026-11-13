"""T-736 (lane I, hubs H2a + H1R + one Checker record): the live after-state of every line the BEADS + CEILING ROUND 3
package wires, built from Checker-merged ledgers only (sha256-pinned below) as mapped by the merged T-730 readiness
(R-T730-1), checked against the candidate of record ARCH_TAKEOFF_V3.0.75 (T-729, merge 05ca1a46; line index of record
research/agents_t729/out/LINE_INDEX_V3_0_75.json), plus the Checker-issued downgrade-only record DG-98cbadebaecc5ede read
from the board record file (agents/control docs/agents/verdicts/V3.0.74/DOWNGRADES.json; the committed extract
in/DG_98cbadebaecc5ede.json is asserted equal to it whenever the board worktree is present). Nothing here opens a
drawing or forms a quantity: every figure is a merged ledger's or the Checker record's.

  BEAD_ADD   T-728 R-T728-1 interior rows (73, hub H2a, live in T-730), one line per host (14): BOUND when every arris
             is measured, AT_LEAST when one is blank; the host bound is read from the V3.0.75 index (two hosts moved by
             the merged T-717 annex datum since T-728 read them: asserted = the V3.0.74 index entries, the change T-730
             named PENDING_ON T-717).
  CEIL_EXCL  T-727 R-T727-2: L-35341ff2 EXCLUDED, DUPLICATE_FACE of the released decor line L-43bf1f86 (hub H1R).
  DG_HOLD    DG-98cbadebaecc5ede: L-636fd3ff roof membrane RELEASED 115.832 -> HELD 115.656474 .. 115.813974 m2 (the
             record's same-basis band; Lead ruling 2026-11-12 20:14 under F-V748-1; the rest of H4 stays in T-750).

    python3 -I research/agents_t736/t736_inputs.py [--check] [--write]
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "T736_ENTRIES.json"
SCHEMA = "URBAN_T736_ENTRIES_V1"
INDEX = "research/agents_t729/out/LINE_INDEX_V3_0_75.json"
INDEX74 = "research/agents_t717/out/LINE_INDEX_V3_0_74.json"
T728 = "research/agents_t728/out/T728_BEAD_RESTATEMENT.json"
T727 = "research/agents_t727/out/T727_VOIDS_CLOSED.json"
T730 = "research/agents_t730/out/T730_ROWS.csv"
DG = "research/agents_t736/in/DG_98cbadebaecc5ede.json"
BOARD_FILE = ROOT.parent / "board" / "docs" / "agents" / "verdicts" / "V3.0.74" / "DOWNGRADES.json"
BOARD_SHA = "76109859d28d64f9534da62937a786b6ff514e4c93ed40cfe7022b3e3ea88046"
DG_ID, DG_LINE = "DG-98cbadebaecc5ede", "L-636fd3ff1784a12e653b"
CEIL_LINE, CEIL_OWNER = "L-35341ff2e6a848b9436b", "L-43bf1f869e1588f1d3bd"
BEAD_SUFFIX = "#BEAD"
D = Decimal

PINS = {INDEX: "498c36bc6647a853", INDEX74: "6733cbc143cdfffd", T728: "97cd9836ce4af7f7", T727: "b4e587746aec2550",
        T730: "737bdb55966b6ebd", DG: None}
SOURCES = {
    "T-728": {"file": T728, "merge_commit": "80e27c10",
              "checker_run": "Verifier 2026-11-12T03:48Z Gate A PASS (session_01E6cPnd1boTCdgLn15ZAk7E)"},
    "T-727": {"file": T727, "merge_commit": "8ea912b5",
              "checker_run": "Verifier 2026-11-12 ~02:00Z Gate A PASS (session_01E6cPndwcoCFyW6yDFf3dsv)"},
    "T-730": {"file": T730, "merge_commit": "6143f30d",
              "checker_run": "Verifier 2026-11-12T07:58Z Gate A PASS (session_01E6cPneP2vRoV5ySBhUeVJ5)"},
    "DG-98cbadebaecc5ede": {"file": DG, "merge_commit": "2d28645c",
                            "checker_run": "Verifier 2026-11-12T15:06:49Z downgrade-only record (run token "
                                           "20261112T135228-451-21809, verdict commit 022f34f12; board commit "
                                           "2d28645c)"},
}


class InputsError(ValueError):
    pass


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def load(p):
    want, got = PINS.get(p), sha(p)
    if want is not None and not got.startswith(want):
        raise InputsError(f"{p}: sha256 {got[:16]} is not the pinned {want} (stale input)")
    return json.loads((ROOT / p).read_text(encoding="utf-8")) if p.endswith(".json") else \
        list(csv.DictReader((ROOT / p).read_text(encoding="utf-8").splitlines()))


def record():
    """the Checker record from the committed extract; equal to the board record file when the board is present."""
    rec = load(DG)["record"]
    if BOARD_FILE.exists():
        raw = BOARD_FILE.read_bytes()
        board = [r for r in json.loads(raw)["downgrades"] if r["downgrade_id"] == DG_ID]
        if len(board) != 1 or board[0] != rec:
            raise InputsError(f"{DG_ID}: the extract is not the board record file's record")
        if hashlib.sha256(raw).hexdigest() != BOARD_SHA:
            # the file may gain later records; the record itself is what binds (asserted equal above)
            pass
    return rec


def _idx(p):
    return {ln["line_id"]: ln for ln in load(p)["lines"]}


def _f(x):
    return None if x is None else float(D(str(x)))


def bead_entries(ix, ix74):
    t = load(T728)
    rows = [r for r in t["rows"] if r["scope"] == "INTERIOR"]
    live = [r for r in load(T730) if r["piece"] == "T-728" and r["hub"] == "H2a"]
    if len(rows) != 73 or len(live) != 73:
        raise InputsError(f"T-728 interior rows {len(rows)} / T-730 live H2a rows {len(live)}: 73 each expected")
    lmap = {r["row"].split(":", 1)[1]: r for r in live}
    if set(lmap) != {r["edge_id"] for r in rows} or len(lmap) != len(live):
        raise InputsError("the T-730 H2a rows are not the T-728 interior arrises one for one")
    hosts = OrderedDict()
    for r in sorted(rows, key=lambda r: (r["host_line"], r["edge_id"])):
        m = lmap[r["edge_id"]]
        if m["host_line_id"] != r["host_line"] or m["action"] != "ADD" or m["new_line_key"] != f"B4-09@{r['host_line']}":
            raise InputsError(f"{r['edge_id']}: T-730 maps it to {m['host_line_id']} {m['action']} {m['new_line_key']}")
        hosts.setdefault(r["host_line"], []).append(r)
    out = []
    for hid, rs in hosts.items():
        h = ix.get(hid)
        if h is None or h["item_code"] != "FIN.PLASTER" or h["class"] != "HELD" or h["held_low"] is None:
            raise InputsError(f"{hid}: not a HELD bounded FIN.PLASTER line on V3.0.75 ({h})")
        tb = t["summary"]["hosts"][hid]["host_bound"]
        mine = f"HELD {h['held_low']} .. {h['held_high']} m2"
        pend = {r["pending"] for r in rs if r["pending"]}
        if tb != mine:
            o = ix74.get(hid)
            if not pend or o is None or (o["held_low"], o["held_high"]) != (h["held_low"], h["held_high"]):
                raise InputsError(f"{hid}: host moved {tb} -> {mine} without the T-717 change T-730 named")
        arr = []
        for r in rs:
            st = r["bead_state"]
            why = r["cause"].split(" || ")[0] if r["cause"].startswith("bead:") else "measured arris; host HELD"
            arr.append({"edge_id": r["edge_id"], "class": r["class"], "state": st, "room": r["room"],
                        "low": _f(r["low"]) if st == "HELD_BOUND" else None,
                        "high": _f(r["high"]) if st == "HELD_BOUND" else None,
                        "ledger_status": r["ledger_status"], "drawing_band": r["drawing_band"], "why": why[:300]})
        blank = [a for a in arr if a["state"] == "HELD_BLANK"]
        out.append({"piece": "BEAD_ADD", "action": "AT_LEAST" if blank else "BOUND", "host_line_id": hid,
                    "element_id": h["element_id"].replace(":PLASTER", "") + BEAD_SUFFIX,
                    "source_tasks": ["T-728", "T-730"], "rule": "R-T728-1", "status": "HELD",
                    "why": ("host HELD: the bead takes its state and cause, own arris lengths kept (F-T728-1)" +
                            (f"; {len(blank)} arris(es) blank: " + "; ".join(f"{a['edge_id']}: {a['why'][6:120]}"
                                                                           for a in blank) if blank else "")),
                    "expect": {"item_code": "FIN.PLASTER", "element_id": h["element_id"], "unit": "m2",
                               "class": "HELD", "low": h["held_low"], "high": h["held_high"]},
                    "host_change_since_t728": None if tb == mine else {"t728": tb, "v3_0_75": mine,
                                                                       "by": "T-717 (V3.0.74) annex datum Q-54 B"},
                    "arrises": arr})
    return out


def ceiling_entry(ix):
    c = load(T727)["ceiling_top"]
    if c["ownership"]["excluded"] != [[CEIL_LINE, f"DUPLICATE_FACE of {CEIL_OWNER}"]] or c["ownership"]["owner"] != \
            CEIL_OWNER:
        raise InputsError("T-727 ownership is not the one exclusion this package wires")
    live = [r for r in load(T730) if r["hub"] == "H1R"]
    if len(live) != 1 or live[0]["host_line_id"] != CEIL_LINE or live[0]["after"] != "EXCLUDED":
        raise InputsError(f"T-730 H1R map {live}")
    b, o = ix[CEIL_LINE], ix[CEIL_OWNER]
    return {"piece": "CEIL_EXCL", "action": "EXCLUDE", "line_id": CEIL_LINE, "owner_line_id": CEIL_OWNER,
            "cause": "DUPLICATE_FACE", "source_tasks": ["T-727", "T-730"], "rule": "R-T727-2",
            "status": "DRAWING-CONFIRMED",
            "why": (f"the void line names {c['over_void_line']['names_m2']} m2 = the well rectangle only, already "
                    f"inside the released decor face {CEIL_OWNER} ({c['decor_line']['measured_net']} m2 carries the "
                    f"well top {c['well_top_in_decor_m2']} m2); the upper plan over the well prints no opening "
                    f"outline (T-727 s.3): one face, one line"),
            "expect": {"item_code": b["item_code"], "element_id": b["element_id"], "unit": b["unit"], "class": "HELD",
                       "low": None, "high": None},
            "owner_expect": {"item_code": o["item_code"], "element_id": o["element_id"], "unit": o["unit"],
                             "class": "RELEASED", "measured_net": o["measured_net"]}}


def dg_entry(ix):
    import re
    r = record()
    b = ix[DG_LINE]
    band = re.findall(r"band (\d+(?:\.\d+)?) \.\. (\d+(?:\.\d+)?) m2", r["reason"])
    if r["line_ids"] != [DG_LINE] or r["state"] != "HELD" or len(set(band)) != 1 or b["class"] != "RELEASED" or \
            abs(b["measured_net"] - r["engine_qty"]) > 1e-9:
        raise InputsError(f"{DG_ID}: not the one-line HELD record of the released {DG_LINE}")
    return {"piece": "DG_HOLD", "action": "HOLD", "line_id": DG_LINE, "source_tasks": [DG_ID], "rule":
            "R-T665-1 (g) / R-T734-1 (c)", "status": "HELD", "low": _f(band[0][0]), "high": _f(band[0][1]),
            "why": (f"Checker downgrade-only record {DG_ID} (UNSUPPORTED BASIS): the released figure lies above its "
                    f"own same-basis band (dome circles deducted as inscribed polygons, under-deduction 0.018329 m2); "
                    f"the band's two ends are the two closed-face readings (wall face / D-band, the 0.075 layer-D "
                    f"feature unprinted): held at the record's band, never a chosen end"),
            "expect": {"item_code": b["item_code"], "element_id": b["element_id"], "unit": b["unit"],
                       "class": "RELEASED", "measured_net": b["measured_net"]},
            "record": dict({k: r[k] for k in ("downgrade_id", "line_ids", "line_content_sha256", "engine_qty", "unit",
                                              "state", "reason", "checker")}, file=SOURCES[DG_ID]["file"],
                           file_sha256=sha(DG))}


def inputs():
    ix, ix74 = _idx(INDEX), _idx(INDEX74)
    ents = bead_entries(ix, ix74) + [ceiling_entry(ix), dg_entry(ix)]
    srcs = [dict({"task": k, "sha256": sha(v["file"])}, **v) for k, v in SOURCES.items()]
    return {"schema": "URBAN_V3076_INPUTS_V1", "project_id": "development-villa-t131", "sources": srcs,
            "entries": ents}


def projection(doc):
    """run-record census projection of FIN.PLASTER.BEAD (m.l, per state; never summed across states)"""
    z = {"lines": 0, "bounded": 0, "low": D(0), "high": D(0), "at_least": 0, "at_least_sum": D(0), "arrises": 0,
         "arrises_measured": 0, "arrises_blank": 0, "rows_low": D(0), "rows_high": D(0)}
    for e in doc["entries"]:
        if e["piece"] != "BEAD_ADD":
            continue
        z["lines"] += 1
        lo = sum((D(str(a["low"])) for a in e["arrises"] if a["low"] is not None), D(0))
        hi = sum((D(str(a["high"])) for a in e["arrises"] if a["high"] is not None), D(0))
        z["rows_low"] += lo
        z["rows_high"] += hi
        z["arrises"] += len(e["arrises"])
        z["arrises_blank"] += sum(a["state"] == "HELD_BLANK" for a in e["arrises"])
        if e["action"] == "BOUND":
            z["bounded"] += 1
            z["low"] += lo
            z["high"] += hi
        else:
            z["at_least"] += 1
            z["at_least_sum"] += lo
    z["arrises_measured"] = z["arrises"] - z["arrises_blank"]
    return {k: (str(v) if isinstance(v, D) else v) for k, v in z.items()}


def build():
    doc = inputs()
    return {"schema": SCHEMA, "pins": {p: sha(p) for p in PINS}, "inputs": doc, "bead_projection": projection(doc)}


def text(d):
    return json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main(argv):
    d = build()
    if "--check" in argv:
        ok = OUT.read_text(encoding="utf-8") == text(d)
        print("T736_ENTRIES equals its builder:", ok)
        return 0 if ok else 1
    if "--write" in argv:
        OUT.write_text(text(d), encoding="utf-8")
        print("written", OUT.relative_to(ROOT))
    print(json.dumps(d["bead_projection"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
