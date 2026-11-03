"""T-383: the export-side COMPLETENESS JOIN for the waterproofing families, inside the T-471 framework (owner answer
2026-11-02: 'waterproofing completeness check WITHIN the T-471 framework (its schema and states); T-310 consumes it for
export. No duplicate implementation'). General: no project, sheet, layer or coordinate is named here.

Why. The T-236 / T-298 join (tools/boq_export_v1.completeness_from_report) states completeness per PRINCIPAL TRADE. The
WATERPROOFING trade spans many BOQ lines (one per item code and unit), so every WP line reads 'TRADE WATERPROOFING SPANS
n BOQ LINES' and no WP line can count WHOLE, whatever its inventory says. The merged T-301 inventory
(research/agents_t301/t301_wp_inventory) already accounts for every drawn face per item code and unit (IN_LINE /
NOT_APPLICABLE with evidence / MISSING blank). This module reads that inventory join ONE BOQ LINE AT A TIME and writes,
per WP line (trade + item + unit), the export's own URBAN_LINE_COMPLETENESS_V1 record, so the export's unchanged rule
(boq_export_v1.completeness_passes: inventory = element scope, missing 0, duplicated 0, held 0, no blocker) decides.
Nothing new decides VERIFIED: a WHOLE V2 Checker verdict is still required.

Rule R-T383-WP-WHOLE-1 (PROJECT-INDEPENDENT; provenance T-236 / T-298 (R-T298-SLAB-JOIN-1 pattern) / T-301
(R-T301-WP-INVENTORY-1) / T-471 states; owner single whole-line definition 2026-10-25 04:38):
  1. A WP line's completeness is read against the inventory elements of ITS item code and unit only.
  2. Its record passes only when: the T-301 join is not refused (a face in two lines, NOT_APPLICABLE without evidence or
     carried by a line, MISSING given as 0 are refused, and then NO WP line passes); the item has an inventory (an item
     with lines but no inventory element is blocked: an absent inventory is never 'nothing missing'); MISSING 0; no
     face on a held line; no line of the item without an inventory face (UNLINKED) and no line key the inventory does
     not carry (REGISTER_ONLY); the released quantity closes on the inventory quantity (residual 0 within 1e-6 in the
     unit); no NOT_APPLICABLE line without evidence.
  3. Counts are in the export's units: inventory_count = scope elements (line element ids) that carry at least one
     IN_LINE face + MISSING faces; element_scope_count = the export's own scope_split of the line's elements. The face
     counts (in line / NA / missing / held) are stated beside them.
  4. Per T-471 component (C-B8-xx): the T-471 state and gate of its lines (t471_completeness.state_of_kinds, unchanged)
     are kept, except that a component the line classes would read VERIFIED is APPLICABLE_HELD / HELD while its
     inventory is ABSENT or INCOMPLETE (a verified line set is not a verified family without its inventory); a
     NOT_APPLICABLE component with an applicable inventory face is reported (NA_WITH_INVENTORY_FACES), never resolved.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "research" / "agents_t301", ROOT / "research" / "agents_t471"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import t301_wp_inventory as W  # noqa: E402  (the merged T-301 inventory join; read only)
import t471_completeness as T471  # noqa: E402  (the T-471 states; read only)
from engine.source import trade_completeness_v1 as TC  # noqa: E402  (line_trade only)
from tools import boq_export_v1 as X  # noqa: E402  (COMPLETENESS_SCHEMA, scope_split, completeness_passes; read only)

SCHEMA = X.WP_COMPLETENESS_SCHEMA            # "URBAN_T383_WP_COMPLETENESS_V1"
RULE_ID = "R-T383-WP-WHOLE-1"
TRADE = W.TRADE
TOL = W.TOL
INVENTORY_STATUS = ("ABSENT", "INCOMPLETE", "COMPLETE")


def _eid(ln):
    return str((ln.get("location") or {}).get("element_id"))


def wp_groups(lines):
    """the export's WP line groups (trade, item, unit) -> [lines], for every line whose principal trade is
    WATERPROOFING (the export's own TC.line_trade)."""
    g = defaultdict(list)
    for ln in lines:
        if TC.line_trade(ln) == TRADE:
            g[(str(ln["trade"]), ln["item_code"], ln["unit"])].append(ln)
    return dict(sorted(g.items()))


def _join_lines(lines):
    return [{"line_id": ln["line_id"], "item_code": ln["item_code"], "unit": ln["unit"],
             "evidence_state": ln["evidence_state"], "measured_net": ln.get("measured_net")} for ln in lines]


def records(elements, lines, links, ident):
    """elements: T-301 inventory rows; lines: canonical BOQ lines (every trade; only WP lines are read); links:
    line_id -> [T-301 element keys]; ident: (project_id, revision_set_sha256, ...). -> (doc, {group: record})."""
    pid, rev = ident[0], ident[1]
    groups = wp_groups(lines)
    wl = [ln for ls in groups.values() for ln in ls]
    wl_ids = {ln["line_id"] for ln in wl}
    refused, rep = None, None
    try:
        foreign = sorted(set(links) - wl_ids)
        if foreign:
            raise W.InventoryError(f"link names {len(foreign)} line(s) that are not WP lines of this BOQ "
                                   f"(e.g. {foreign[0]})")
        rep = W.join(elements, _join_lines(wl), {k: v for k, v in links.items() if v})
    except W.InventoryError as e:
        refused = str(e)
    fam = {}
    if rep:
        for f in rep["families"]:
            k = (f["item_code"], f["unit"])
            if k in fam:
                refused = refused or f"item {k[0]} {k[1]} in two WP families ({fam[k]['family']}, {f['family']})"
            fam[k] = f
    els_by_line = defaultdict(list)
    if rep:
        for r in rep["elements"]:
            if r["status"] == "IN_LINE":
                els_by_line[r["line_id"]].append(r)
        reg_only = defaultdict(int)
        for x in rep["register_only"]:
            reg_only[x["line_id"]] += 1
    out = {}
    for g, ls in groups.items():
        code, unit = g[1], g[2]
        sc, na_ev, na_bad, na_lines = X.scope_split(ls, sorted({_eid(ln) for ln in ls}))
        rec = {"schema": X.COMPLETENESS_SCHEMA, "source": SCHEMA, "rule_id": RULE_ID, "project_id": pid,
               "revision_set_sha256": rev, "trade": g[0], "item_code": code, "unit": unit,
               "principal_trade": TRADE, "element_scope_count": len(sc), "inventory_count": None,
               "missing": None, "duplicated": None, "held": None}
        blockers = []
        if na_ev:
            rec["not_applicable_out_of_scope"] = len(na_ev)
        if na_bad:
            blockers.append(f"NOT_APPLICABLE WITHOUT EVIDENCE {len(na_bad)}")
        f = fam.get((code, unit))
        if refused is not None:
            blockers.append(f"WP INVENTORY JOIN REFUSED: {refused}")
        elif f is None:
            blockers.append("NO WP INVENTORY FOR THIS ITEM (its family inventory is absent: an absent inventory is "
                            "never 'nothing missing')")
        else:
            live = [ln for ln in ls if ln["line_id"] not in na_lines]
            carrying = sorted({_eid(ln) for ln in live if els_by_line.get(ln["line_id"])})
            unl = sorted(ln["line_id"] for ln in live if not els_by_line.get(ln["line_id"]))
            ro = sum(reg_only.get(ln["line_id"], 0) for ln in ls)
            rec.update(inventory_count=len(carrying) + f["missing"], missing=f["missing"], duplicated=0,
                       held=f["in_line_held"], inventory_faces={"in_line": f["in_line"],
                                                                "not_applicable": f["not_applicable"],
                                                                "missing": f["missing"], "held": f["in_line_held"]},
                       inventory_qty_in_line=f["inventory_qty_in_line"], line_qty=f["line_qty"],
                       residual=f["residual"])
            if f["missing"]:
                blockers.append(f"MISSING {f['missing']}")
            if f["in_line_held"]:
                blockers.append(f"HELD {f['in_line_held']}")
            if unl:
                blockers.append(f"UNLINKED LINES {len(unl)}")
            if ro:
                blockers.append(f"REGISTER_ONLY {ro}")
            if f["residual"] is not None and abs(f["residual"]) > TOL:
                blockers.append(f"RESIDUAL {f['residual']:+.6f} {unit} (inventory - line)")
            if not f["whole_line_countable"] and not blockers:
                blockers.append("INVENTORY DOES NOT CLOSE ON THE LINE (T-301 whole_line_countable false)")
        rec["blockers"] = blockers
        # the export's own rule decides (same scope the export computes for a group of lines only)
        rec["t383_passes"] = X.completeness_passes(rec, (pid, rev, None, None), g, sc)
        out[g] = rec
    passing = sorted(g for g, r in out.items() if r["t383_passes"])
    doc = {"schema": SCHEMA, "rule_id": RULE_ID, "project_id": pid, "revision_set_sha256": rev,
           "refused": refused, "wp_lines": len(wl), "wp_groups": len(groups),
           "groups_passing": [list(g) for g in passing],
           "inventory_counts": rep["counts"] if rep else None,
           "records": [out[g] for g in sorted(out)]}
    return doc, out


def components(register, lines, classes, recs, elements):
    """T-471 framework rows for the register components that carry a WP item code (a line of the WP trade or an
    inventory element). -> [row]."""
    wp_codes = {g[1] for g in recs} | {e["item_code"] for e in elements}
    by_code = defaultdict(list)
    for g, r in recs.items():
        by_code[g[1]].append(r)
    rows = []
    for c in register.get("components") or ():
        codes = set(c.get("item_codes") or ())
        if not codes & wp_codes:
            continue
        sel = [ln for ln in lines if T471._selects(c, ln)]
        st, gate, reason, conflict = T471.state_of_kinds(c, [classes[ln["line_id"]] for ln in sel])
        inv = [e for e in elements if e["item_code"] in codes]
        rs = [r for code in sorted(codes) for r in by_code.get(code, ())]
        if not inv:
            istat = "ABSENT"
        elif any(not r["t383_passes"] for r in rs) or any(
                e["applicability"] == "APPLICABLE" and e["item_code"] not in by_code for e in inv):
            istat = "INCOMPLETE"
        else:
            istat = "COMPLETE"
        if c.get("applicability") == "NOT_APPLICABLE" and any(e["applicability"] == "APPLICABLE" for e in inv):
            conflict = conflict or "NA_WITH_INVENTORY_FACES"
        if gate == "VERIFIED" and istat != "COMPLETE":
            st, gate, reason = "APPLICABLE_HELD", "HELD", f"every line verified but the WP inventory is {istat}"
        rows.append({"component_id": c.get("component_id"), "family": c.get("family"),
                     "applicability": c.get("applicability"), "state": st, "gate": gate, "reason": reason,
                     "conflict": conflict, "wp_inventory": istat, "inventory_elements": len(inv),
                     "lines": len(sel), "whole_countable_items": sorted(
                         f"{r['item_code']}[{r['unit']}]" for r in rs if r["t383_passes"])})
    return rows


def whole_lines(recs, groups, v2_whole, ident):
    """groups that count as WHOLE verified BOQ lines: a WHOLE V2 record binds the group AND its record passes.
    v2_whole: {group: verdict id}. -> sorted [(group, verdict id)]; a WHOLE record on a failing group is listed apart."""
    ok, not_ok = [], []
    for g, vid in sorted(v2_whole.items()):
        sc = X.scope_split(groups[g], sorted({_eid(x) for x in groups[g]}))[0] if g in groups else []
        (ok if X.completeness_passes(recs.get(g), (ident[0], ident[1], None, None), g, sc) else not_ok).append(
            (g, vid))
    return ok, not_ok


def dump(doc):
    return json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


__all__ = ["SCHEMA", "RULE_ID", "wp_groups", "records", "components", "whole_lines", "dump"]
