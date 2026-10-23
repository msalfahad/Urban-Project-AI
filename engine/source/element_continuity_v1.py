"""ELEMENT_CONTINUITY_V1 (T-188, residential review R2 + R3): element inventory across disciplines and storey continuity.

A pure CHECK, NOT wired into any method version (ARCH_TAKEOFF_V2.9 .. V3.0.x and route G are unchanged): it writes
finding rows, never a BOQ quantity. Standard library only; imports no engine module. Any villa.

Why (PROJECT_UNDERSTANDING_ASSESSMENT s.6 R2 / R3; ENGINEERING_REASONING_STANDARD s.2 step 1, s.3): on the development
villa four element-level failures were found by hand, one at a time: a staircase's whole upper storey folded away by the
structural pass (the stair drawn at the same place on two slab plans taken as one drawing, D-T184-1); a dome outline
typed as a winder stair from its radial lines; a third dome drawn only in the architecture, with no structural drawing;
a pump room priced by the reference BOQ that no drawing shows. Each is an INVENTORY question (which physical elements
exist, in which discipline, on which storey, and which BOQ line carries each) asked before any quantity. This module
asks it for every element at once.

R2 (cross-discipline join). For every element kind (stair, pool, tank, dome, lift, ramp, parapet, shaft, void, column)
the architectural record is joined to its structural counterpart and to the BOQ lines of its owner trade (the element
register rulings), and the reverse: every line bound to an element, every reference-BOQ row to a drawn element.
R3 (storey continuity). For every element that spans storeys (stair, lift, shaft, void, column) each storey it occupies
is listed with the drawings that show it there, and a storey with no drawing or (where the kind needs one) no BOQ line
is flagged. A stair that correctly ends at a floor is NOT flagged when the end is evidenced (R-STAIR-CONT-1).

Absence is never inferred from silence: a "not drawn in discipline X" finding needs X to be declared SEARCHED (with the
sheets searched); otherwise the finding is NOT_SEARCHED (status UNKNOWN). A missing item is never 0: every finding row
carries no quantity, and the lines it names keep their own state.

Input (`check(project)`):
  {"storeys": ["FDN", "GF", "1F", ...]            bottom to top (required; unique),
   "place_tol_m": number                           required only when any presence carries "xy" (metres),
   "elements": [{"id", "kind" (KINDS), "place" (words),
       "occupies": [storey, ...]                   the storeys whose height zone the element physically occupies, from
                                                   its levels (a stair GF +1.00 -> 1F +5.50 occupies GF; a lift pit
                                                   occupies FDN); optional: when absent it is the storeys it is DRAWN on,
       "occupies_ref": str                          the levels / section that fix "occupies" (required with it),
       "presence": [{"storey", "discipline": ARCH | STRUCT, "ref", "what": DRAWN | SEEN_BELOW | ARRIVAL,
                     "xy": [x, y] (optional, metres, the element's plan place on that sheet, in one frame)}],
                                                   SEEN_BELOW (flights seen through an opening) and ARRIVAL (a stair's
                                                   top arriving on the floor above) never make a storey occupied,
       "searched": {"ARCH": ref, "STRUCT": ref}     disciplines whose sheets were searched for this element,
       "detail": {"state": PROJECT | TYPICAL | NONE, "ref"}   its structural detail (kinds that need one),
       "components": [{"name", "state": DRAWN | HELD | NOT_DRAWN, "ref", "note"}],
       "ends": {"ref"}                              evidence that the element ends at its top occupied storey}],
   "lines": [{"line_id", "item", "kind" (the element kind the line claims to measure), "storey", "trade", "state",
              "element": id | None, "element_any": [ids] (bound to one of these, not yet resolved), "ref"}],
   "reference_rows": [{"row_id", "kind", "element": id | None, "component", "ref"}]}

Finding codes (each row: code, status HELD | UNKNOWN | REVIEW | CONFLICT | NOT_DRAWN, element, storey, lines, refs, why):
  R2  NO_STRUCTURAL_COUNTERPART, NO_ARCHITECTURAL_COUNTERPART, NOT_SEARCHED, NO_STRUCTURAL_DETAIL, TYPICAL_DETAIL_ONLY,
      MISSING_COMPONENT, COMPONENT_HELD, COMPONENT_NOT_DRAWN, NO_BOQ_LINE, KIND_MISMATCH, TRADE_NOT_ALLOWED,
      UNBOUND_LINE, BINDING_AMBIGUOUS, NOT_DRAWN (a reference row on no drawn element)
  R3  STOREY_NOT_DRAWN, STOREY_WITHOUT_LINE, DRAWN_OUTSIDE_SPAN, PLACE_MISMATCH, END_NOT_EVIDENCED, SPAN_UNDETERMINED

Guards (ValueError: a wrong input never becomes a finding): unknown kind / discipline / what / state / storey;
duplicate element id; presence, component, detail or occupies without ref; xy without place_tol_m; a line bound both
to "element" and "element_any".
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict

METHOD = "ELEMENT_CONTINUITY_V1"
RULES = ("ENGINEERING_REASONING_STANDARD.md s.2 step 1 (define the physical element first), s.3 (scope before numbers)",
         "R-STAIR-ID-1 / R-STAIR-STACK-1 / R-STAIR-CONT-1 / R-STAIR-TYP-1 (T-184, proposed)",
         "lessons register 2026-10-23: an element is typed from its drawing evidence, never from a shape heuristic",
         "owner 2026-10-22 16:45: 'not drawn' is an absence of evidence, never a verified zero",
         "ELEMENT_REGISTER.md rulings: owner trade per element kind (stair concrete STRUCTURE, marble / handrails lane A, "
         "shaft walls WALL elements of lane A, railings METALWORK, domes STRUCTURE)")

DISCIPLINES = ("ARCH", "STRUCT")
WHATS = ("DRAWN", "SEEN_BELOW", "ARRIVAL")
DETAIL_STATES = ("PROJECT", "TYPICAL", "NONE")
COMPONENT_STATES = ("DRAWN", "HELD", "NOT_DRAWN")

# kind -> rule set. spans: R3 applies; struct: a structural counterpart is required; arch: the architecture must draw
# it (a kind a plan / elevation shows); detail: a structural detail is required for its geometry; components: required
# components; line: "PER_STOREY" (a line of the owner trade on every occupied storey), "ANY" (at least one line of the
# owner trade) or None (no line of its own: a void is measured as deductions of other elements); owner: the trade whose
# line is required; trades: the trades whose lines may bind to the element (ELEMENT_REGISTER rulings).
KINDS = {
    "STAIR":   {"spans": True,  "struct": True,  "arch": True,  "detail": True,  "components": (),
                "line": "PER_STOREY", "owner": "STRUCTURE",
                "trades": ("STRUCTURE", "FORMWORK", "BAR_STEEL", "FINISHES", "METALWORK")},
    "LIFT":    {"spans": True,  "struct": True,  "arch": True,  "detail": False, "components": ("PIT",),
                "line": "ANY", "owner": "STRUCTURE", "trades": ("STRUCTURE", "FORMWORK", "BAR_STEEL", "WATERPROOFING")},
    "SHAFT":   {"spans": True,  "struct": False, "arch": True,  "detail": False, "components": (),
                "line": "PER_STOREY", "owner": "BLOCKWORK", "trades": ("BLOCKWORK", "FINISHES", "STRUCTURE")},
    "VOID":    {"spans": True,  "struct": True,  "arch": True,  "detail": False, "components": (),
                "line": None, "owner": None, "trades": ("FINISHES", "METALWORK")},
    "COLUMN":  {"spans": True,  "struct": True,  "arch": False, "detail": False, "components": (),
                "line": "PER_STOREY", "owner": "STRUCTURE", "trades": ("STRUCTURE", "FORMWORK", "BAR_STEEL", "FINISHES")},
    "POOL":    {"spans": False, "struct": True,  "arch": True,  "detail": True,  "components": ("BASE", "WALLS"),
                "line": "ANY", "owner": "STRUCTURE",
                "trades": ("STRUCTURE", "FORMWORK", "BAR_STEEL", "WATERPROOFING", "FINISHES")},
    "TANK":    {"spans": False, "struct": True,  "arch": False, "detail": True,  "components": (),
                "line": "ANY", "owner": "STRUCTURE", "trades": ("STRUCTURE", "FORMWORK", "BAR_STEEL", "WATERPROOFING")},
    "DOME":    {"spans": False, "struct": True,  "arch": True,  "detail": True,  "components": (),
                "line": "ANY", "owner": "STRUCTURE",
                "trades": ("STRUCTURE", "FORMWORK", "BAR_STEEL", "WATERPROOFING", "FINISHES")},
    "RAMP":    {"spans": False, "struct": True,  "arch": True,  "detail": False, "components": (),
                "line": "ANY", "owner": "STRUCTURE", "trades": ("STRUCTURE", "FORMWORK", "BAR_STEEL", "FINISHES")},
    "PARAPET": {"spans": False, "struct": False, "arch": True,  "detail": False, "components": (),
                "line": "ANY", "owner": "BLOCKWORK", "trades": ("BLOCKWORK", "STRUCTURE", "FINISHES", "FACADE",
                                                                "WATERPROOFING")},
}
STATUS = {"NO_STRUCTURAL_COUNTERPART": "HELD", "NO_ARCHITECTURAL_COUNTERPART": "REVIEW", "NOT_SEARCHED": "UNKNOWN",
          "NO_STRUCTURAL_DETAIL": "HELD", "TYPICAL_DETAIL_ONLY": "REVIEW", "MISSING_COMPONENT": "HELD",
          "COMPONENT_HELD": "HELD", "COMPONENT_NOT_DRAWN": "NOT_DRAWN", "NO_BOQ_LINE": "HELD",
          "KIND_MISMATCH": "HELD", "TRADE_NOT_ALLOWED": "REVIEW", "UNBOUND_LINE": "REVIEW",
          "BINDING_AMBIGUOUS": "REVIEW", "NOT_DRAWN": "NOT_DRAWN", "STOREY_NOT_DRAWN": "HELD",
          "STOREY_WITHOUT_LINE": "HELD", "DRAWN_OUTSIDE_SPAN": "CONFLICT", "PLACE_MISMATCH": "CONFLICT",
          "END_NOT_EVIDENCED": "REVIEW", "SPAN_UNDETERMINED": "HELD"}
REVIEW_OF = {c: ("R3" if c.startswith(("STOREY_", "DRAWN_OUTSIDE", "PLACE_", "END_", "SPAN_")) else "R2")
             for c in STATUS}


def _need(cond, msg):
    if not cond:
        raise ValueError(msg)


def _validate(p):
    st = p.get("storeys")
    _need(isinstance(st, list) and st and len(set(st)) == len(st), "storeys: a non-empty list of unique names")
    ids = Counter(e.get("id") for e in p.get("elements") or [])
    _need(all(i for i in ids), "element without id")
    dup = sorted(i for i, n in ids.items() if n > 1)
    _need(not dup, f"duplicate element id {dup}")
    any_xy = False
    for e in p.get("elements") or []:
        _need(e.get("kind") in KINDS, f"{e['id']}: unknown kind {e.get('kind')!r}")
        if e.get("occupies") is not None:
            _need(all(s in st for s in e["occupies"]), f"{e['id']}: occupies an unknown storey")
            _need(e.get("occupies_ref"), f"{e['id']}: occupies without occupies_ref")
        for pr in e.get("presence") or []:
            _need(pr.get("storey") in st, f"{e['id']}: presence on unknown storey {pr.get('storey')!r}")
            _need(pr.get("discipline") in DISCIPLINES, f"{e['id']}: unknown discipline {pr.get('discipline')!r}")
            _need(pr.get("what", "DRAWN") in WHATS, f"{e['id']}: unknown presence kind {pr.get('what')!r}")
            _need(pr.get("ref"), f"{e['id']}: presence without ref")
            if pr.get("xy") is not None:
                any_xy = True
                _need(len(pr["xy"]) == 2 and all(isinstance(v, (int, float)) for v in pr["xy"]),
                      f"{e['id']}: xy must be [x, y]")
        for d in (e.get("searched") or {}):
            _need(d in DISCIPLINES, f"{e['id']}: searched in unknown discipline {d!r}")
        det = e.get("detail")
        if det is not None:
            _need(det.get("state") in DETAIL_STATES, f"{e['id']}: unknown detail state {det.get('state')!r}")
            _need(det.get("ref"), f"{e['id']}: detail without ref")
        for c in e.get("components") or []:
            _need(c.get("state") in COMPONENT_STATES, f"{e['id']}: unknown component state {c.get('state')!r}")
            _need(c.get("name") and c.get("ref"), f"{e['id']}: component without name or ref")
        if e.get("ends") is not None:
            _need(e["ends"].get("ref"), f"{e['id']}: ends without ref")
    if any_xy:
        tol = p.get("place_tol_m")
        _need(isinstance(tol, (int, float)) and tol > 0, "xy given: place_tol_m (metres, > 0) is required")
    for ln in p.get("lines") or []:
        _need(ln.get("line_id"), "line without line_id")
        _need(not (ln.get("element") and ln.get("element_any")), f"{ln['line_id']}: element and element_any both set")
        if ln.get("kind") is not None:
            _need(ln["kind"] in KINDS, f"{ln['line_id']}: unknown kind {ln['kind']!r}")


def _occupied(e):
    if e.get("occupies") is not None:
        return list(e["occupies"]), "LEVELS"
    drawn = [pr["storey"] for pr in e.get("presence") or [] if pr.get("what", "DRAWN") == "DRAWN"]
    return sorted(set(drawn), key=drawn.index), "DRAWN"


def check(project):
    """-> {"method", "elements": [per-element inventory rows], "findings": [...], "summary"}; reads only its input."""
    _validate(project)
    storeys = project["storeys"]
    order = {s: i for i, s in enumerate(storeys)}
    els = {e["id"]: e for e in project.get("elements") or []}
    lines = project.get("lines") or []
    out = []

    def f(code, el=None, storey=None, lines_=(), refs=(), why=""):
        out.append({"review": REVIEW_OF[code], "code": code, "status": STATUS[code], "element": el,
                    "kind": els[el]["kind"] if el in els else None, "storey": storey, "lines": sorted(lines_),
                    "refs": [r for r in refs if r], "why": why})

    by_el = defaultdict(list)                         # element -> [(line, binding)]
    for ln in lines:
        if ln.get("element"):
            if ln["element"] in els:
                by_el[ln["element"]].append((ln, "BOUND"))
            else:
                f("UNBOUND_LINE", lines_=[ln["line_id"]], refs=[ln.get("ref")],
                  why=f"line names element {ln['element']!r}, which is not in the inventory")
        elif ln.get("element_any"):
            known = [i for i in ln["element_any"] if i in els]
            for i in known:
                by_el[i].append((ln, "CANDIDATE"))
            f("BINDING_AMBIGUOUS", lines_=[ln["line_id"]], refs=[ln.get("ref")],
              why=f"line is one of {', '.join(sorted(known)) or 'no known element'}; which one is not established")
        else:
            f("UNBOUND_LINE", lines_=[ln["line_id"]], refs=[ln.get("ref")],
              why="line names no physical element (no ledger or register ruling binds it)")

    inventory = []
    for eid in sorted(els):
        e = els[eid]
        rule = KINDS[e["kind"]]
        pres = e.get("presence") or []
        drawn = [p for p in pres if p.get("what", "DRAWN") == "DRAWN"]
        disc = {d: [p for p in drawn if p["discipline"] == d] for d in DISCIPLINES}
        searched = e.get("searched") or {}
        bound = by_el.get(eid, [])
        # --- R2: line kind / trade
        for ln, how in bound:
            if ln.get("kind") and ln["kind"] != e["kind"]:
                f("KIND_MISMATCH", eid, ln.get("storey"), [ln["line_id"]], [ln.get("ref")],
                  f"line claims a {ln['kind']} but sits on {e['kind']} {eid} (state {ln.get('state')}): "
                  "held as a misread, never relabelled into the element's own line")
            elif ln.get("trade") and ln["trade"] not in rule["trades"]:
                f("TRADE_NOT_ALLOWED", eid, ln.get("storey"), [ln["line_id"]], [ln.get("ref")],
                  f"trade {ln['trade']} is not an owner trade of a {e['kind']} ({', '.join(rule['trades'])})")
        own = [(ln, how) for ln, how in bound if (not ln.get("kind") or ln["kind"] == e["kind"])
               and ln.get("trade") == rule["owner"]]
        # --- R2: disciplines
        for d, need in (("STRUCT", rule["struct"]), ("ARCH", rule["arch"])):
            if not need or disc[d]:
                continue
            if d == "STRUCT" and (e.get("detail") or {}).get("state") == "PROJECT":
                continue                              # a project detail is a structural drawing of the element
            if d in searched:
                f("NO_STRUCTURAL_COUNTERPART" if d == "STRUCT" else "NO_ARCHITECTURAL_COUNTERPART", eid,
                  refs=[searched[d]] + [p["ref"] for p in drawn],
                  why=f"drawn in {'the architecture' if d == 'STRUCT' else 'the structure'} only; "
                      f"{'structural' if d == 'STRUCT' else 'architectural'} sheets searched: {searched[d]}")
            else:
                f("NOT_SEARCHED", eid, refs=[p["ref"] for p in drawn],
                  why=f"no {d} drawing recorded and the {d} sheets are not declared searched: absence not established")
        if rule["detail"]:
            det = e.get("detail") or {}
            if det.get("state") == "TYPICAL":
                f("TYPICAL_DETAIL_ONLY", eid, refs=[det["ref"]],
                  why="only a typical (N.T.S.) detail: bar arrangement, never a project dimension (R-STAIR-TYP-1)")
            elif det.get("state") == "NONE":
                f("NO_STRUCTURAL_DETAIL", eid, refs=[det["ref"]],
                  why="no structural detail fixes its geometry: the concrete / steel stays HELD (designer item)")
            elif not det:
                f("NOT_SEARCHED", eid, why="structural detail not recorded (state PROJECT / TYPICAL / NONE needed)")
        comps = {c["name"]: c for c in e.get("components") or []}
        for name in rule["components"]:
            if name not in comps:
                f("MISSING_COMPONENT", eid, refs=[searched.get("STRUCT")],
                  why=f"a {e['kind']} needs a {name}; none is recorded on any drawing")
        for name, c in sorted(comps.items()):
            if c["state"] == "NOT_DRAWN":
                code = "MISSING_COMPONENT" if name in rule["components"] else "COMPONENT_NOT_DRAWN"
                f(code, eid, refs=[c["ref"]], why=f"{name}: not drawn ({c.get('note') or 'no drawing shows it'}); "
                                                  "an absence of evidence, not a verified zero")
            elif c["state"] == "HELD":
                f("COMPONENT_HELD", eid, refs=[c["ref"]], why=f"{name}: drawn, {c.get('note') or 'not dimensioned'}")
        if rule["line"] == "ANY" and not own:
            f("NO_BOQ_LINE", eid, refs=[p["ref"] for p in drawn],
              why=f"drawn, but no {rule['owner']} line carries it: held, never 0")
        # --- R3: storeys
        occ, basis = _occupied(e)
        storey_rows = []
        if rule["spans"]:
            if not occ:
                f("SPAN_UNDETERMINED", eid, why="no levels and no drawing fix the storeys it occupies")
            for s in occ:
                here = [p for p in drawn if p["storey"] == s]
                lns = sorted({ln["line_id"] for ln, how in own if ln.get("storey") == s})
                if not here:
                    f("STOREY_NOT_DRAWN", eid, s, refs=[e.get("occupies_ref")],
                      why=f"occupies {s} by its levels, but no plan, slab plan or section of {s} draws it")
                if rule["line"] == "PER_STOREY" and not lns:
                    f("STOREY_WITHOUT_LINE", eid, s, refs=[p["ref"] for p in here],
                      why=f"drawn on {s} ({len(here)} drawing(s)) but no {rule['owner']} line of {s} carries it: "
                          "the storey is HELD, never folded into another storey")
                storey_rows.append({"storey": s, "drawn": sorted(p["ref"] for p in here), "lines": lns})
            outside = [p for p in drawn if p["storey"] not in occ]
            for p in outside:
                f("DRAWN_OUTSIDE_SPAN", eid, p["storey"], refs=[p["ref"], e.get("occupies_ref")],
                  why=f"drawn on {p['storey']}, outside the storeys its levels give ({', '.join(occ)}): "
                      "another element at the same place, or a level conflict")
            xy = [p for p in drawn if p.get("xy") is not None]
            if len(xy) > 1:
                tol = float(project["place_tol_m"])
                x0 = xy[0]["xy"]
                for p in xy[1:]:
                    dist = math.hypot(p["xy"][0] - x0[0], p["xy"][1] - x0[1])
                    if dist > tol:
                        f("PLACE_MISMATCH", eid, p["storey"], refs=[xy[0]["ref"], p["ref"]],
                          why=f"plan place {dist:.3f} m from the place on {xy[0]['storey']} (tolerance {tol} m): "
                              "not the same stacked element")
            if occ:
                top = max(occ, key=order.get)
                above = [s for s in storeys if order[s] > order[top]]
                if above and not e.get("ends"):
                    f("END_NOT_EVIDENCED", eid, top,
                      refs=[p["ref"] for p in pres if p["storey"] in above],
                      why=f"occupies up to {top}; no drawing is cited showing that it does not continue to "
                          f"{above[0]} (a lower plan never implies continuation, nor its end)")
        inventory.append({"element": eid, "kind": e["kind"], "place": e.get("place"),
                          "disciplines": {d: sorted(p["ref"] for p in disc[d]) for d in DISCIPLINES},
                          "detail": (e.get("detail") or {}).get("state"), "occupies": occ, "occupies_basis": basis,
                          "ends": (e.get("ends") or {}).get("ref"), "storeys": storey_rows,
                          "lines": sorted({ln["line_id"] for ln, how in bound}),
                          "owner_lines": sorted({ln["line_id"] for ln, how in own})})
    # --- R2 reverse: reference rows to drawn elements
    for r in project.get("reference_rows") or []:
        if not r.get("element") or r["element"] not in els:
            f("NOT_DRAWN", r.get("element"), refs=[r.get("ref")], lines_=[r["row_id"]],
              why=f"reference row {r['row_id']} ({r.get('kind') or '?'}{' ' + r['component'] if r.get('component') else ''}) "
                  "names an element no drawing shows: listed NOT DRAWN, no quantity, never 0")
    out.sort(key=lambda x: (x["review"], x["element"] or "", x["code"], x["storey"] or "", x["lines"]))
    cnt = Counter((x["code"], x["status"]) for x in out)
    return {"method": METHOD, "rules": list(RULES), "storeys": storeys, "elements": inventory, "findings": out,
            "summary": {"elements": len(inventory), "lines": len(lines),
                        "reference_rows": len(project.get("reference_rows") or []),
                        "findings": len(out), "by_code": {f"{k[0]} {k[1]}": n for k, n in sorted(cnt.items())},
                        "by_status": dict(sorted(Counter(x["status"] for x in out).items()))}}


def mirror(project, axis="x"):
    """the same project with every xy mirrored (a mirrored plan set): findings must not change."""
    p = json.loads(json.dumps(project))
    i = 0 if axis == "x" else 1
    for e in p.get("elements") or []:
        for pr in e.get("presence") or []:
            if pr.get("xy") is not None:
                pr["xy"][i] = -pr["xy"][i]
    return p


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="element inventory across disciplines and storey continuity (check only)")
    ap.add_argument("project_json")
    ap.add_argument("--json", help="write the full result here")
    a = ap.parse_args(argv)
    with open(a.project_json, encoding="utf-8") as fh:
        res = check(json.load(fh))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
    print(json.dumps(res["summary"], indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
