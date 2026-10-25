"""T-298 part (2) (F-REC-01, Verifier 2026-10-25 11:28): the slab completeness join BY PANEL ID on the current candidate
grain, replacing the T-236 COUNT join for CONCRETE.SLAB. General (no project name, sheet, handle or coordinate here).

Why. T-236 joined slab lines to the independent panel inventory by COUNT per storey ('how many faces, never which'):
the k-th line of a storey took key SLAB#k. On a grain where some slab lines are retired (NOT_APPLICABLE_WITH_EVIDENCE:
a face the drawing classes as beam / not concrete, its home named) the retired lines still took SLAB#k slots, so live
panels lost their keys and the surplus keys read REGISTER_ONLY, and the retired elements stayed in the export's element
scope (the line group 75 elements vs the inventory 62). A count join also cannot see a WRONG line: one panel missing
and one extra face on the same storey cancel.

Rule R-T298-SLAB-JOIN-1 (PROJECT-INDEPENDENT; provenance T-236 / T-234 / Verifier 11:28 F-REC-01):
  1. Only live quantity lines join (MEASURED / SOURCE_DERIVED / PROVISIONAL); a held line joins nothing by quantity
     (it is linked by the caller only if it names its panel); a NOT_APPLICABLE_WITH_EVIDENCE line is not a slab
     element: the caller links it to its own EXCLUDED key, never to a panel.
  2. Per storey, each inventory panel takes the NEAREST unused line by volume within TOL_M3 (panels in ascending
     volume, then panel id; ties by line id). A pair is
       EXACT           the panel has exactly one line within TOL_M3 and that line has exactly one panel within TOL_M3;
       INTERCHANGEABLE every line within TOL_M3 of the panel carries the SAME volume (|diff| <= 1e-9 m3): which of the
                       equal lines is which panel is not established and changes no count or sum; the group is named;
       AMBIGUOUS       otherwise: the panel stays unlinked (MISSING in the report) and its line unmatched.
  3. A line no panel takes is UNMATCHED: the caller gives it a key no inventory carries (REGISTER_ONLY: a measured
     face the independent inventory does not find is a disagreement, never silently a panel). A panel no line takes
     is MISSING.
  TOL_M3 = 0.0002 m3: the panel ledger rounds areas to 4 dp (<= 0.00001 m3 at t <= 0.20 m) and curved panels
  (circle sectors) differ between the ledger's arc and the engine's polygon by up to 0.000128 m3 per piece on the
  development villa (named in the T-298 report); two panels of one storey closer than TOL_M3 that do not carry equal
  line volumes stay AMBIGUOUS (never picked).
"""

from __future__ import annotations

from collections import defaultdict

TOL_M3 = 0.0002
EQ_M3 = 1e-9
QUANTITY_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")


def join(panels, lines, tol=TOL_M3):
    """panels: [{"floor", "panel", "m3"}]; lines: [{"line_id", "floor", "m3"}] (live quantity lines only).
    -> {"pairs": [{floor, panel, panel_m3, line_id, line_m3, diff_m3, join, group}], "unmatched_lines": [...],
        "missing_panels": [...]} (deterministic)."""
    seen = set()
    for p in panels:
        k = (p["floor"], p["panel"])
        if k in seen:
            raise ValueError(f"panel {p['floor']}:{p['panel']} listed twice")
        seen.add(k)
    ids = [ln["line_id"] for ln in lines]
    if len(set(ids)) != len(ids):
        raise ValueError("one line id twice")
    for x in list(panels) + list(lines):
        if not isinstance(x.get("m3"), (int, float)) or isinstance(x.get("m3"), bool):
            raise ValueError(f"{x.get('panel') or x.get('line_id')}: volume {x.get('m3')!r} is not a number (a held "
                             "or missing quantity never joins by volume)")
    pairs, unmatched, missing = [], [], []
    for fl in sorted({p["floor"] for p in panels} | {ln["floor"] for ln in lines}):
        P = sorted((p for p in panels if p["floor"] == fl), key=lambda p: (p["m3"], p["panel"]))
        L = sorted((ln for ln in lines if ln["floor"] == fl), key=lambda ln: (ln["m3"], ln["line_id"]))
        near_p = {p["panel"]: [ln for ln in L if abs(ln["m3"] - p["m3"]) <= tol] for p in P}
        near_l = {ln["line_id"]: [p for p in P if abs(ln["m3"] - p["m3"]) <= tol] for ln in L}
        used = set()
        for p in P:
            cands = near_p[p["panel"]]
            free = sorted((ln for ln in cands if ln["line_id"] not in used),
                          key=lambda ln: (abs(ln["m3"] - p["m3"]), ln["line_id"]))
            if not free:
                missing.append({"floor": fl, "panel": p["panel"], "panel_m3": p["m3"],
                                "why": "no live slab line within tolerance" if not cands else
                                       "every line within tolerance is taken by another panel"})
                continue
            ln = free[0]
            vols = {round(c["m3"], 9) for c in cands}
            if len(cands) == 1 and len(near_l[ln["line_id"]]) == 1:
                how, grp = "EXACT", ""
            elif max(c["m3"] for c in cands) - min(c["m3"] for c in cands) <= EQ_M3:
                how = "INTERCHANGEABLE"
                gp = sorted({q["panel"] for c in cands for q in near_l[c["line_id"]]})
                gl = {c["line_id"] for q in gp for c in near_p[q]}
                grp = "|".join(gp)
                # every panel of the group sees only equal lines, and there are as many equal lines as panels
                # (one line within tolerance of two panels is AMBIGUOUS, never given to the first one)
                if any({round(c["m3"], 9) for c in near_p[q]} != vols for q in gp) or len(gl) != len(gp):
                    how = "AMBIGUOUS"
            else:
                how = "AMBIGUOUS"
            if how == "AMBIGUOUS":
                missing.append({"floor": fl, "panel": p["panel"], "panel_m3": p["m3"],
                                "why": "AMBIGUOUS: lines of different volumes within tolerance "
                                       f"({', '.join(c['line_id'] for c in cands)})"})
                continue
            used.add(ln["line_id"])
            pairs.append({"floor": fl, "panel": p["panel"], "panel_m3": p["m3"], "line_id": ln["line_id"],
                          "line_m3": ln["m3"], "diff_m3": round(ln["m3"] - p["m3"], 9), "join": how, "group": grp})
        for ln in L:
            if ln["line_id"] not in used:
                unmatched.append({"floor": fl, "line_id": ln["line_id"], "line_m3": ln["m3"],
                                  "why": "no inventory panel within tolerance (or its panel is ambiguous)"})
    return {"pairs": pairs, "unmatched_lines": unmatched, "missing_panels": missing, "tol_m3": tol}


def floor_residuals(result, panels, lines):
    """per storey: inventory m3, joined line m3, panel m3 joined, residual (line - panel) over the pairs."""
    out = defaultdict(lambda: {"panels": 0, "panel_m3": 0.0, "lines": 0, "line_m3": 0.0, "pairs": 0,
                               "pair_residual_m3": 0.0})
    for p in panels:
        out[p["floor"]]["panels"] += 1
        out[p["floor"]]["panel_m3"] += p["m3"]
    for ln in lines:
        out[ln["floor"]]["lines"] += 1
        out[ln["floor"]]["line_m3"] += ln["m3"]
    for x in result["pairs"]:
        out[x["floor"]]["pairs"] += 1
        out[x["floor"]]["pair_residual_m3"] += x["line_m3"] - x["panel_m3"]
    return {fl: {k: (round(v, 6) if isinstance(v, float) else v) for k, v in d.items()} for fl, d in sorted(out.items())}
