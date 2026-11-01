"""T-246: the URBAN_V3036_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.36 (engine.source.arch_v3036), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build). Every figure and id is READ from those
files; the only typed text is the binding state of each line (read from the same ledgers) and the physical-check words.

  research/agents_t341/FILL_TABLE_T341.csv / FILL_LINES_T341.csv  T-341 (MERGED 5fbf8677, Verifier 2026-10-29 15:46 UTC
      Gate A PASS): the canonical fill of 41 lines by opening / element id on V3.0.22 (owner-method lists, the T-296
      per-opening skirting ledger, the base-ownership and floor-scope records); its one UNEXPLAINED line is NOT taken
      from here;
  research/agents_t345/TRACE_ROWS_T345.csv / TRACE_LINES_T345.csv  T-345 (MERGED f2225238, Verifier 2026-10-29 19:02 UTC
      Gate A PASS): the 1F porcelain line TRACED (face 75.983002, 22 rows, residual 0);
  research/agents_t296/WINDOW_CAUSES_T296.csv  T-296 (MERGED 57c31ae4, Verifier 2026-10-25 16:08 UTC Gate A PASS, own
      re-measure 1F-01 15.900 lm): the physical reading of each window whose threshold half is deducted.

The module binds each line as the ledger read it (item, element, state, gross field, net); the lines the V3.0.32 ceiling
fill restated since V3.0.22 no longer bind and are NOT taken (named in SKIPPED by the run, never forced).

    python3 -I research/agents_t246/t246_inputs.py [project_id]      # prints the line count per family
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FT = ROOT / "research/agents_t341/FILL_TABLE_T341.csv"
FL = ROOT / "research/agents_t341/FILL_LINES_T341.csv"
TR = ROOT / "research/agents_t345/TRACE_ROWS_T345.csv"
TL = ROOT / "research/agents_t345/TRACE_LINES_T345.csv"
WC = ROOT / "research/agents_t296/WINDOW_CAUSES_T296.csv"
PINS = {FT: "9df19a7efb7409bce005b74c55a32fa4f2c7ac4018d74f402d4cb9fd439f78f2",
        FL: "a9b2632f0b60114e34318ddd2bfbc3866e0a1b821b47c8e784b1085f253bdd68",
        TR: "476c7a6b9dc46ec6da34ec06328ea35c94130300a0fd85129076aca83d749c13",
        TL: "ccf4f51b848bef2dceef36cb679d7c91337c33ec8dc63da7888704360b2f05b1",
        WC: "4ed39b9617faf5176ad619e34afcf345e38271ce8188d7c10a018ea9c98b6716"}


def _rel(p):
    return str(p.relative_to(ROOT))


SOURCES = {
    "T-341": {"task": "T-341", "file": f"{_rel(FT)}; {_rel(FL)}", "sha256": f"{PINS[FT]}; {PINS[FL]}",
              "merge_commit": "5fbf8677c052b55c656d25a79b2fadb85628be8e",
              "checker_run": "Verifier 2026-10-29 15:46 UTC (Gate A PASS; T-319 + T-341 note; fill 41 FLAG -> 1 FLAG "
                             "on copies, one UNEXPLAINED line left to T-345)"},
    "T-345": {"task": "T-345", "file": f"{_rel(TR)}; {_rel(TL)}", "sha256": f"{PINS[TR]}; {PINS[TL]}",
              "merge_commit": "f2225238d955f9dffdf7c766c4ddf30f4229e780",
              "checker_run": "Verifier 2026-10-29 19:02 UTC session_01E6cPndQ8P3psQLivrqh7iu (Gate A PASS; 5.890817 m2 "
                             "traced, residual 0)"},
    "T-296": {"task": "T-296", "file": _rel(WC), "sha256": PINS[WC],
              "merge_commit": "57c31ae4b590dc9b710eeb445d37ffb7c1789c16",
              "checker_run": "Verifier 2026-10-25 16:08 UTC (Gate A PASS a-h; own re-measure 1F-01 L-c021ae79 15.900 "
                             "lm and W14 sill AGREE)"},
}
# T-296 window reading -> physical check of a deducted threshold / glazing half (flag only, nothing applied)
PHYS = {"SKIRTED": ("UNRESOLVED", "sill above the floor: the wall base continues under the window, so this "
                                  "threshold deduction is physically questioned (T-296 SKIRTED); not applied here"),
        "NOT_SKIRTED": ("CONSISTENT", "no skirting at this window base (T-296 NOT_SKIRTED)"),
        "HELD": ("UNRESOLVED", "window sill / base owner not established (T-296 HELD)")}


def _read(p):
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    if h != PINS[p]:
        raise SystemExit(f"{_rel(p)}: sha256 {h[:12]} is not the merged {PINS[p][:12]} (an edited ledger stops)")
    return list(csv.DictReader(b.decode("utf-8").splitlines()))


def _f(x):
    return None if x in (None, "") else float(x)


def _windows():
    """(line_id, census window id) -> (physical_check, why)."""
    out = {}
    for r in _read(WC):
        chk, why = PHYS[r["reading"]]
        out[(r["line_id"], r["census_id"])] = (chk, f"{why}; {r['why']}"[:300])
    return out


def _phys(line_id, it, win):
    oid = it["id"]
    if "#threshold-half" in oid or "#glazing-half" in oid:
        k = (line_id, it.get("census_id"))
        if k not in win:
            raise SystemExit(f"{line_id} {oid}: a window half with no T-296 reading")
        return win[k]
    return None, None


# lines the T-341 fill read on V3.0.22 that a later merged package restated (they no longer bind; never forced): the
# V3.0.32 ceiling fill (T-284) re-netted both ceiling faces from their still-held items. Their lists wait a follow-up.
SET_ASIDE = {
    "L-eb3be58fc760b39f0e38": "FIN.CEILING GF open plan: net 110.922696 (V3.0.22) restated to 101.137092 by V3.0.32 "
                              "(T-284 ceiling fill): the list must name its still-held stair zones by id",
    "L-fc116bb666b184740090": "FIN.CEILING 1F open plan: held by V3.0.32 (T-284), no measured_net: nothing to list",
}


def build(project_id=None, states=None):
    """states (optional): {line_id: evidence_state}; without it the module checks the line is in a valued state.
    The lines in SET_ASIDE are not taken (named in the inputs, never forced)."""
    win = _windows()
    fl = {r["line_id"]: r for r in _read(FL)}
    ft = _read(FT)
    tl = {r["line_id"]: r for r in _read(TL)}
    tr = _read(TR)
    lines = []
    for lid, L in fl.items():
        if lid in SET_ASIDE:
            continue
        if L["status"] == "UNEXPLAINED":
            if lid not in tl or tl[lid]["status"] != "TRACED":
                raise SystemExit(f"{lid}: UNEXPLAINED in T-341 and not TRACED by T-345")
            T = tl[lid]
            items = [{"role": r["role"], "id": r["item_id"], "qty": float(r["amount"]), "face": r["category"],
                      "source": r["source"], "note": r["note"]} for r in tr if r["line_id"] == lid]
            src, gross_after, status = ["T-345"], float(T["gross_used"]), T["status"]
        else:
            items = []
            for r in ft:
                if r["line_id"] != lid:
                    continue
                it = {"role": r["role"], "id": r["opening_id"], "census_id": r["census_id"], "face": r["face"],
                      "qty": float(r["amount"]), "source": r["source"], "note": r["note"]}
                chk, why = _phys(lid, it, win)
                if chk:
                    it["physical_check"], it["physical_why"] = chk, why
                items.append(it)
            src = ["T-341"] + (["T-296"] if any(i.get("physical_check") for i in items) else [])
            gross_after, status = _f(L["gross_used"]), L["status"]
        g = float(L["gross_field"])
        restate = abs(gross_after - g) > 1e-9
        row = {"action": "GROSS_RESTATE" if restate else "LIST_FILL", "line_id": lid, "status": status,
               "expect": {"item_code": L["item_code"], "element_id": L["element_id"], "unit": L["unit"],
                          "evidence_state": (states or {}).get(lid), "gross": g,
                          "measured_net": float(L["measured_net"])},
               "items": items, "source_tasks": src}
        if restate:
            row["gross_after"] = gross_after
        lines.append(row)
    return {"schema": "URBAN_V3036_INPUTS_V1", "project_id": project_id, "sources": list(SOURCES.values()),
            "lines": lines, "set_aside": [{"line_id": k, "why": v} for k, v in sorted(SET_ASIDE.items())]}


def bind(doc, candidate_lines):
    """the runner's step: fill expect.evidence_state from the candidate and set aside every line that no longer stands
    as the ledger read it (gross field / net / element moved since V3.0.22). -> (doc, skipped [(line_id, why)])."""
    by = {ln["line_id"]: ln for ln in candidate_lines}
    keep, skipped = [], []
    for r in doc["lines"]:
        b, e = by.get(r["line_id"]), r["expect"]
        if b is None:
            skipped.append((r["line_id"], "not in the candidate"))
            continue
        same = (b["item_code"] == e["item_code"] and (b.get("location") or {}).get("element_id") == e["element_id"]
                and isinstance(b.get("gross"), (int, float)) and abs(b["gross"] - e["gross"]) <= 1e-6
                and b.get("measured_net") is not None and abs(b["measured_net"] - e["measured_net"]) <= 1e-6)
        if not same:
            skipped.append((r["line_id"], f"{b['item_code']} gross {b.get('gross')} net {b.get('measured_net')} "
                                          f"!= ledger gross {e['gross']} net {e['measured_net']} (restated since)"))
            continue
        keep.append(dict(r, expect=dict(e, evidence_state=b["evidence_state"])))
    return dict(doc, lines=keep), skipped


if __name__ == "__main__":
    d = build(sys.argv[1] if len(sys.argv) > 1 else None)
    fam = {}
    for r in d["lines"]:
        fam[r["expect"]["item_code"]] = fam.get(r["expect"]["item_code"], 0) + 1
    print(json.dumps({"lines": len(d["lines"]), "by_family": fam}, indent=1, sort_keys=True))
