"""CONSULTANT QUESTION GENERATOR + USER HELP MODE (generic).

Both outputs are built only from the flag and its source context (source_a / source_b, source_refs, answer options,
interpretation). Nothing project-specific is written here: the glossary explains generic structural terms in plain
language for a reviewer who is not a structural engineer, and the AutoCAD search hints are derived from the source
references the flag carries (text, layer, handle, sheet title, page).

Stdlib only.
"""

from __future__ import annotations

import re

POLICY_ID = "QUESTION_HELPER_V1"

# plain-language glossary (generic); matched as whole words / phrases in the flag text
GLOSSARY = {
    "tie": "A closed loop of thin steel bar that wraps the main vertical bars of a column (also called a link or "
           "stirrup). Ties stop the main bars buckling; their number decides how much small-diameter steel is needed.",
    "stirrup": "A closed loop of thin bar around the main bars of a beam or column (same idea as a tie).",
    "schedule": "A table on the drawings that defines each member type once (size and bars). The plan then shows "
                "where each type occurs. The schedule alone never tells you how many there are.",
    "tag": "The short type mark printed next to a member on a plan (for example a column or beam mark).",
    "footing": "The concrete pad under a column that spreads its load into the ground.",
    "strap beam": "A ground-level beam that ties two footings together.",
    "ground beam": "A beam at ground level, usually under walls, between footings or columns.",
    "continuous beam": "One beam that runs over several supports with spans defined together in its schedule row.",
    "span": "The length of a beam between two supports.",
    "slab": "A flat concrete floor or roof plate.",
    "temperature steel": "Light bars placed in a slab to control cracking from shrinkage and temperature changes.",
    "t&b": "Top and bottom - the same bars are placed in both the upper and the lower layer.",
    "boxed": "A footing note describing an extra cage or box of bars; its meaning must come from the engineer.",
    "neck column": "A short column stub between a footing and the ground beam, below the first floor.",
    "planted column": "A column that starts on a beam or slab instead of continuing from a column below.",
    "band": "A range in a detailing rule (for example 'column long side between 50 and 80 cm').",
    "section": "The cross-section size of a member (width x depth).",
    "lift": "Elevator.",
    "pit": "The pit below the lowest stop of an elevator.",
    "cover": "The concrete thickness outside the outermost bar.",
    "per metre": "A bar count given for each metre of length (e.g. 6 ties per metre of column).",
}

ISSUE_PLAIN = {
    "SOURCE_CONFLICT": "Two places on the drawings say different things about the same thing.",
    "RULE_GAP": "A drawing rule does not cover this exact case (for example a value sits exactly on a limit).",
    "MISSING_DIMENSION": "A size or length needed to measure this is not given.",
    "MISSING_SCHEDULE": "This member has no schedule row, so its size and bars are not defined.",
    "UNBOUND_OCCURRENCE": "A member drawn on the plan cannot be tied to one type mark with certainty.",
    "AMBIGUOUS_APPLICABILITY": "A rule or note exists but it is not clear where or how it applies.",
    "MISSING_DETAIL": "Something is required by a note or rule but is not drawn or detailed.",
    "UNIT_CONFLICT": "Two sources use different units for the same value.",
    "REVISION_CONFLICT": "Two drawing revisions disagree.",
    "ENGINEERING_METHOD_REQUIRED": "The drawings give the requirement but not the method to measure it; the "
                                   "engineer must state the method.",
}
WHY_PLAIN = {
    "BLOCKED": "Until this is answered the affected part of the quantity is held back (not counted in totals).",
    "AUDIT_ONLY": "The affected quantity is shown for checking but not counted in totals.",
    "LOWER_BOUND": "Only the part that is certain is counted; the total is a minimum until this is answered.",
    "PROVISIONAL": "The quantity uses the engine's current interpretation; an answer may change it.",
    "NO_QUANTITY_IMPACT": "No quantity changes with the answer; it is recorded for completeness.",
    "VERIFIED": "No quantity is held back.",
}


def _terms(text):
    t = (text or "").lower()
    return {k: v for k, v in GLOSSARY.items() if re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", t)}


def _ref_text(r):
    parts = [r.get("drawing"), f"p.{r['page']}" if r.get("page") else None, r.get("sheet_title"),
             f"layer {r['layer']}" if r.get("layer") else None, f"handle {r['handle']}" if r.get("handle") else None,
             f"'{_display(r['text'])}'" if r.get("text") else None]
    return ", ".join(p for p in parts if p)


def _display(text):
    """DXF control codes as AutoCAD displays them (FIND matches the displayed text)."""
    return (text.replace("%%c", "Ø").replace("%%C", "Ø").replace("%%d", "°").replace("%%D", "°")
            .replace("%%p", "±").replace("%%P", "±").replace("%%u", "").replace("%%U", ""))


def autocad_hints(source_refs):
    """Concrete AutoCAD steps derived from the source references."""
    out = []
    for r in source_refs:
        if r.get("sheet_title"):
            out.append(f"Open the sheet titled \"{r['sheet_title']}\"" + (f" (PDF page {r['page']})" if r.get("page")
                                                                          else ""))
        if r.get("text"):
            out.append(f"FIND (Ctrl+F) the text \"{_display(r['text'])}\" - match whole word")
        if r.get("handle"):
            out.append(f"Select by handle: type (command \"_.SELECT\" (handent \"{r['handle']}\") \"\") then ZOOM "
                       f"Object, or use the 'Handle' field in Quick Properties")
        if r.get("layer"):
            out.append(f"LAYISO the layer \"{r['layer']}\" to see only that information (LAYUNISO to restore)")
        if r.get("xy_mm"):
            out.append(f"ZOOM to about X={r['xy_mm'][0]:.0f}, Y={r['xy_mm'][1]:.0f} (sheet-local mm"
                       + (f", add the sheet origin {r['sheet_origin']}" if r.get("sheet_origin") else "") + ")")
    seen, uniq = set(), []
    for h in out:
        if h not in seen:
            seen.add(h)
            uniq.append(h)
    return uniq


def consultant_question(flag):
    """The block sent to the engineering office."""
    a, b = flag.get("source_a") or {}, flag.get("source_b") or {}
    said = [f"{x.get('description')}: {x.get('value')}" + (f" ({_ref_text(x['source_ref'])})"
                                                           if x.get("source_ref") else "")
            for x in (a, b) if x]
    q = {"flag_id": flag["flag_id"], "flag_key": flag["flag_key"],
         "PLAIN_LANGUAGE_ISSUE": flag["issue_summary"],
         "WHY_IT_MATTERS": f"{ISSUE_PLAIN[flag['issue_type']]} {WHY_PLAIN.get(flag['release_effect'], '')}".strip()
                           + (f" Affected: {flag['quantity_affected']} {flag['unit']} "
                              f"({', '.join(flag['trade'])})." if flag.get("quantity_affected") is not None else ""),
         "WHERE_TO_LOOK": flag.get("where_to_check") or "; ".join(_ref_text(r) for r in flag["source_refs"]),
         "WHAT_THE_DRAWING_SAYS": said,
         "ENGINE_CURRENT_INTERPRETATION": f"{flag.get('current_interpretation') or 'none - held back'}"
                                          + (f" (authority: {flag['interpretation_authority']})"
                                             if flag.get("interpretation_authority") else ""),
         "QUESTION_TO_CONSULTANT": flag["question_for_engineer"],
         "QUANTITY_BOQ_IMPACT": {"release_effect": flag["release_effect"], "trades": flag["trade"],
                                 "elements": flag["element_ids"], "quantity_affected": flag.get("quantity_affected"),
                                 "unit": flag.get("unit")}}
    return q


def help_mode(flag):
    """The block for the reviewer (no structural vocabulary assumed)."""
    text = " ".join(str(x) for x in (flag["issue_summary"], flag["question_for_engineer"], flag["element_type"],
                                     flag.get("current_interpretation"),
                                     (flag.get("source_a") or {}).get("description"),
                                     (flag.get("source_b") or {}).get("description")))
    opts = [{"if_the_answer_is": o["answer"], "then": o["effect"]} for o in flag["answer_options"]]
    return {"flag_id": flag["flag_id"], "flag_key": flag["flag_key"],
            "WHAT_DOES_THIS_MEAN": f"{ISSUE_PLAIN[flag['issue_type']]} {flag['issue_summary']}",
            "TERMS_EXPLAINED": _terms(text),
            "WHY_DOES_IT_MATTER": WHY_PLAIN.get(flag["release_effect"], ""),
            "WHERE_SHOULD_I_LOOK": [_ref_text(r) for r in flag["source_refs"]] or [flag.get("where_to_check")],
            "WHAT_TO_SEARCH_IN_AUTOCAD": autocad_hints(flag["source_refs"]),
            "WHAT_WOULD_EACH_ANSWER_CHANGE": opts,
            "WHAT_TO_ASK_THE_ENGINEERING_OFFICE": flag["question_for_engineer"]}


def schema():
    return {"schema": "QUESTION_HELPER_SCHEMA", "policy_id": POLICY_ID,
            "consultant_block": ["PLAIN_LANGUAGE_ISSUE", "WHY_IT_MATTERS", "WHERE_TO_LOOK", "WHAT_THE_DRAWING_SAYS",
                                 "ENGINE_CURRENT_INTERPRETATION", "QUESTION_TO_CONSULTANT", "QUANTITY_BOQ_IMPACT"],
            "help_block": ["WHAT_DOES_THIS_MEAN", "TERMS_EXPLAINED", "WHY_DOES_IT_MATTER", "WHERE_SHOULD_I_LOOK",
                           "WHAT_TO_SEARCH_IN_AUTOCAD", "WHAT_WOULD_EACH_ANSWER_CHANGE",
                           "WHAT_TO_ASK_THE_ENGINEERING_OFFICE"],
            "source_ref_fields": ["drawing", "page", "sheet_title", "layer", "handle", "text", "xy_mm",
                                  "sheet_origin"],
            "glossary_terms": sorted(GLOSSARY), "issue_plain_language": ISSUE_PLAIN,
            "rules": ["generated only from the flag and its source references", "no structural vocabulary assumed: "
                      "every glossary term found in the flag text is explained", "AutoCAD steps come from the "
                      "references (text, handle, layer, coordinates)"]}
