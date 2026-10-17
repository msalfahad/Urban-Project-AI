"""Source conservation (R8.2 §21) — nothing silently disappears.

Two equations, both checked, both route-neutral:

 1. SOURCE LEVEL (every raw entity row the route read)
        RAW_ENTITY_ROWS = MODEL_OBSERVATIONS + BLOCK_DEFINITION_OBSERVATIONS
                        + ATTACHED_ATTRIBUTES + OTHER_LAYOUT + UNPLACED + DELIMITERS

 2. OBSERVATION LEVEL (every observation gets exactly one status)
        OBSERVATIONS = REALISED + CARRIED + HIDDEN + FINDING + UNPLACED
                     + OTHER_LAYOUT + UNREFERENCED_DEFINITION

    An observation realised in one instance and hidden or carried in
    another is REALISED (it produced geometry); the mix is reported. A block
    entity no INSERT reaches is UNREFERENCED_DEFINITION — retained, not lost.

Visits (per instance) are conserved separately by the kernel:
sum(dispositions) == visits.
"""

from __future__ import annotations

from collections import Counter

STATUS_ORDER = ("REALISED", "CARRIED", "HIDDEN", "FINDING", "UNPLACED", "OTHER_LAYOUT")


def _status(counter):
    for s in STATUS_ORDER:
        if counter.get(s):
            return s
    return None


def conservation(document, realised, raw_entity_rows: int | None = None) -> dict:
    notes = dict(document.notes or {})
    raw = raw_entity_rows if raw_entity_rows is not None else notes.get("raw_entity_rows")
    model = list(document.entities)
    block_obs = [o for b in document.blocks.values() for o in b.entities]
    attached = sum(len(o.geometry.attributes) for o in model + block_obs
                   if hasattr(o.geometry, "attributes") and o.geometry.attributes)
    delimiters = sum(v for k, v in notes.items() if k.startswith("delimiter_"))
    source_terms = {"MODEL_OBSERVATIONS": len(model), "BLOCK_DEFINITION_OBSERVATIONS": len(block_obs),
                    "ATTACHED_ATTRIBUTES": attached, "OTHER_LAYOUT": len(document.other_layouts),
                    "UNPLACED": len(document.unplaced), "DELIMITERS": delimiters}
    accounted = sum(source_terms.values())

    per_obs = realised.obs_dispositions
    status = Counter()
    mixed = 0
    all_obs = model + block_obs + [u.observation for u in document.unplaced] + [o for _, o in document.other_layouts]
    for o in all_obs:
        c = per_obs.get(o.obs_id)
        if not c:
            status["UNREFERENCED_DEFINITION"] += 1
            continue
        status[_status(c)] += 1
        mixed += len([k for k in c if c[k]]) > 1
    obs_total = len(all_obs)
    return {
        "source_level": {"RAW_ENTITY_ROWS": raw, **source_terms, "ACCOUNTED": accounted,
                         "BALANCED": raw is not None and raw == accounted},
        "observation_level": {"OBSERVATIONS": obs_total, **{k: status.get(k, 0) for k in STATUS_ORDER},
                              "UNREFERENCED_DEFINITION": status.get("UNREFERENCED_DEFINITION", 0),
                              "MIXED_DISPOSITION_OBSERVATIONS": mixed,
                              "BALANCED": obs_total == sum(status.values())},
        "visit_level": {"VISITS": realised.visits, **dict(realised.dispositions),
                        "BALANCED": realised.visits == sum(realised.dispositions.values())},
        "findings": len(realised.findings),
        "unique_obs_ids": len({o.obs_id for o in all_obs}) == len(all_obs),
    }
