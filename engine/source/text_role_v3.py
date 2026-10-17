"""TEXT ROLE V3 - text_role (TEXT_ROLE_POLICY_V2) with tag families scoped to the SOURCE revision.

text_role.classify establishes a room tag by repeated family use (TR-03: the same tag composition used for at least
two different room names) and extends it to every tag of that composition (TR-04), "same source". It is called with
one plan region at a time, so a family that spans floors is invisible on a floor with few tags: a second-floor tag
of the same composition as twenty ground- and first-floor room tags stays a ROOM_LABEL_CANDIDATE and its site goes to
semantic review. V3 runs the same policy on the texts of ALL regions of the same source revision (one drawing) and
returns the roles of the requested region. Nothing else changes: same vocabulary, same document words, same rules.

Legacy Arabic tag texts (legacy_text) are not words for the vocabulary test; they follow the role of their tag
occurrence, and their decoded value is reported (decoded_labels) for the bilingual room name and corroboration.

TR-V3-B (BILINGUAL CORROBORATION): a tag occurrence left ROOM_LABEL_CANDIDATE (TR-06) whose English text carries
room vocabulary AND whose legacy-Arabic twin text in the SAME occurrence decodes (font from the text style) to the
Arabic term of that room word (legacy_text.corroborate = CORROBORATED) is ROOM_LABEL_ESTABLISHED: two texts in two
scripts, written independently by the author, name the same room. Needs font_of_handle (the adapter reads text
styles from the source drawing); without it the rule is not applied.

classify(inp, family_inputs, frame_insert=None, claims=()) -> {text key: TextRole}
Project-agnostic.
"""

from __future__ import annotations

import dataclasses

from . import legacy_text as LT
from . import text_role as TX

POLICY_ID = "TEXT_ROLE_POLICY_V3_SOURCE_SCOPED_FAMILIES"


BILINGUAL_RULE = "TR-V3-B"


def classify(inp, family_inputs, *, frame_insert=None, claims=(), font_of_handle=None) -> dict:
    same = [f for f in family_inputs if f.revision.revision_id == inp.revision.revision_id]
    if inp not in same:
        same = [inp] + same
    seen_t, seen_p, texts, parts = set(), set(), [], []
    for f in same:
        for t in f.texts:
            if t.identity.key not in seen_t:
                seen_t.add(t.identity.key)
                texts.append(t)
        for p in f.parts:
            if p.identity.key not in seen_p:
                seen_p.add(p.identity.key)
                parts.append(p)
    merged = dataclasses.replace(inp, texts=tuple(texts), parts=tuple(parts))
    roles = TX.classify(merged, frame_insert=frame_insert, claims=claims)
    mine = {t.identity.key for t in inp.texts}
    out = {k: v for k, v in roles.items() if k in mine}
    if font_of_handle:
        out = _bilingual(inp, out, font_of_handle)
    return out


def _bilingual(inp, roles, font_of_handle) -> dict:
    by_occ = {}
    for t in inp.texts:
        r = roles.get(t.identity.key)
        if r is None or not t.identity.instance_handles:
            continue
        by_occ.setdefault(t.identity.instance_handles[0], []).append(t)
    out = dict(roles)
    for occ, ts in sorted(by_occ.items()):
        if any(roles[t.identity.key].role != TX.ROOM_LABEL_CANDIDATE or roles[t.identity.key].rule_id != "TR-06"
               for t in ts):
            continue
        en, ar = [], []
        for t in ts:
            fam = LT.font_family(font_of_handle.get(t.identity.source_handle, ""))
            (ar if fam else en).append((t, fam))
        english = " ".join(t.value for t, _ in en if t.value)
        if not ar or not (TX._words(english) & set(TX.ROOM_WORDS)):
            continue
        arabic = " ".join(LT.decode(t.value, fam)["text"] for t, fam in ar)
        c = LT.corroborate(english, arabic)
        if c["state"] != "CORROBORATED":
            continue
        for t in ts:
            old = roles[t.identity.key]
            out[t.identity.key] = TX.TextRole(t.identity.key, TX.ROOM_LABEL_ESTABLISHED, BILINGUAL_RULE,
                                              dict(old.evidence, why="bilingual corroboration: " + english + " / "
                                                   + arabic, superseded_rule=old.rule_id, matched=c["matched"]))
    return out


def decoded_labels(inp, roles, font_of_handle) -> list:
    """Every ROOM_LABEL_ESTABLISHED tag occurrence of the region: its texts, the legacy Arabic decode and the
    bilingual corroboration. font_of_handle: {text source handle: font file of its text style} (the canonical text
    record carries no style; the adapter reads it from the source drawing)."""
    by_occ = {}
    for t in inp.texts:
        r = roles.get(t.identity.key)
        if r is None or r.role != TX.ROOM_LABEL_ESTABLISHED:
            continue
        occ = (t.identity.instance_handles or (t.identity.key,))[0]
        by_occ.setdefault(occ, []).append(t)
    out = []
    for occ, ts in sorted(by_occ.items()):
        en, ar = [], []
        for t in ts:
            fam = LT.font_family(font_of_handle.get(t.identity.source_handle, ""))
            if fam:
                ar.append(dict(LT.decode(t.value, fam), source=t.value))
            else:
                en.append(t.value.strip())
        english = " ".join(x for x in en if x)
        arabic = " ".join(d["text"] for d in ar)
        out.append({"occurrence": occ, "english": english, "arabic": arabic, "decodes": ar,
                    "corroboration": LT.corroborate(english, arabic) if ar else {"state": "NO_ARABIC_TEXT"},
                    "x": sum(t.x for t in ts) / len(ts), "y": sum(t.y for t in ts) / len(ts),
                    "text_keys": sorted(t.identity.key for t in ts)})
    return out


def policy_record() -> dict:
    return {"id": POLICY_ID, "base": TX.POLICY_ID, "change": "tag families (TR-03 / TR-04) counted over all regions of "
            "the same source revision; roles returned for the requested region only", "legacy_text": LT.POLICY_ID,
            "bilingual_rule": BILINGUAL_RULE + ": a TR-06 room-word tag whose legacy-Arabic twin decodes to the Arabic "
                              "term of that room word is established"}
