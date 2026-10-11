"""DETAIL EVIDENCE (M3) - typical-detail evidence read from a drawing PDF, in one schema for machine reads (native
text, OCR) and manual transcription (generic, stdlib).

A typical detail (a ground-beam class section, an exterior beam, a lintel) is often only in a PDF whose text is vector
glyphs. tools/pdf_evidence.py reads it (native text first, then the vector check, then optional local OCR) and writes
records in this schema; a person can write the same records by hand (MANUAL_TRANSCRIPTION). This module holds the
rules, never the reader:

    parse_notation(text)    one bar notation token -> count / diameter / spacing, or UNPARSED / AMBIGUOUS. OCR reads
                            the diameter sign as 6, 0, 9, 8, ¢, % or o; a token is accepted only when exactly one split
                            gives a plausible count (1-20) and a standard bar diameter. A spacing must be 5-40 cm.
    agree(a, b)             two independent reads (different scale and page segmentation) give the same parse
    caption_of(text)        a detail caption -> member family and span condition ("more than 5m length" -> min 5 m,
                            "less than 2.5m" -> max 2.5 m, "exterior" -> EXTERIOR), with qualifiers kept
    assemble(tokens, captions)
                            every accepted bar token is given to the first caption BELOW it whose width spans it (a
                            detail is drawn above its title); roles come from the vertical order inside one detail:
                            the top count -> TOP, counts under it -> BOTTOM (layers summed), Ø/spacing -> LINKS,
                            count Ø/spacing -> SIDE. A detail with one count only has no defensible TOP / BOTTOM split
                            and is left ROLE_UNRESOLVED.
    redact(text)            owner / title-block text never enters a record: the hygiene pattern and any project
                            redaction pattern drop the token, and only the count of dropped tokens is kept.

States: NATIVE_TEXT (a text layer), OCR_UNREVIEWED (two OCR reads agree), OCR_REJECTED_AMBIGUOUS / _UNPARSED /
_DISAGREE, MANUALLY_CONFIRMED (a person transcribed or confirmed it). OCR-derived values are never promoted to
verified: a quantity built on them is PROVISIONAL, confidence LOW, blocker OCR_DERIVED_UNREVIEWED, until a person
confirms the record (state MANUALLY_CONFIRMED, with who and when).
"""

from __future__ import annotations

import re

POLICY_ID = "DETAIL_EVIDENCE_V1"
SCHEMA = "URBAN_DETAIL_EVIDENCE_V1"
STANDARD_DIAMETERS_MM = (6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32)
DIA_GLYPHS = "Ø6098¢%$oOc"           # what OCR prints for the diameter sign (8 only when followed by 2 digits)
STATES = ("NATIVE_TEXT", "OCR_UNREVIEWED", "OCR_REJECTED_AMBIGUOUS", "OCR_REJECTED_UNPARSED",
          "OCR_REJECTED_DISAGREE", "MANUALLY_CONFIRMED")
USABLE = ("NATIVE_TEXT", "OCR_UNREVIEWED", "MANUALLY_CONFIRMED")
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
PATHLIKE = re.compile(r"\\|/[A-Za-z]|\.(dwg|dxf|pdf)\b", re.I)
MEMBER_WORDS = (("GROUND_BEAM", r"GROUND\s*BEAMS?|TIE\s*BEAMS?|G\.?\s*B\b"), ("STRAP_BEAM", r"STRAP"),
                ("LINTEL", r"LINTEL|LNTEL"), ("FOOTING", r"FOOTING"), ("COLUMN", r"COLUMN"),
                ("BEAM", r"\bBEAMS?\b"), ("SLAB", r"SLAB"), ("STAIR", r"STAIR"))


def redact(text, extra=None):
    """True when the token must not be recorded (owner / title-block / file-path text)."""
    t = text or ""
    if HYGIENE.search(t) or PATHLIKE.search(t):
        return True
    return any(re.search(p, t) for p in (extra or ()))


def _spacing(s):
    m = re.fullmatch(r"(\d{1,2})(?:CM|EM|C|M)?\.?", s, re.I)     # OCR prints 'cm' as 'em' too
    if not m:
        return None
    v = int(m.group(1))
    return v / 100.0 if 5 <= v <= 40 else None


def parse_notation(text):
    """'3Ø16' / OCR '3616' -> {count 3, dia 16}; 'Ø8/15cm' / '08/15cm' -> {dia 8, spacing 0.15};
    '2Ø12/30cm' / '2612/30cm' -> {count 2, dia 12, spacing 0.30}. Returns state PARSED / AMBIGUOUS / UNPARSED."""
    raw = (text or "").strip().replace(" ", "")
    t = raw.rstrip(".,;:|")
    if not t or len(t) > 14:
        return {"state": "UNPARSED", "raw": raw}
    head, _, tail = t.partition("/")
    sp, per_m = None, False
    if tail.upper() == "M":
        per_m = True                               # '5Ø8/M': five per metre
    elif tail:
        sp = _spacing(tail)
        if sp is None:
            return {"state": "UNPARSED", "raw": raw}
    head = head.replace("@", "")
    cands = set()
    # count + glyph + diameter, or glyph + diameter (links / bars by spacing)
    for k in range(0, 3):
        cnt = head[:k]
        if k and not cnt.isdigit():
            continue
        rest = head[k:]
        if not rest or rest[0] not in DIA_GLYPHS:
            continue
        dia = rest[1:]
        if not dia.isdigit() or len(dia) > 2:
            continue
        d = int(dia)
        if d not in STANDARD_DIAMETERS_MM:
            continue
        if rest[0] == "8" and len(dia) != 2:
            continue                               # '88' is never 'Ø8'; an 8 read as Ø needs two diameter digits
        n = int(cnt) if cnt else None
        if n is not None and not (1 <= n <= 20):
            continue
        if n is None and (sp is None or per_m):
            continue                               # a bare diameter is not a bar notation
        cands.add((n, d))
    if not cands:
        return {"state": "UNPARSED", "raw": raw}
    if len(cands) > 1:
        return {"state": "AMBIGUOUS", "raw": raw, "candidates": sorted(cands, key=lambda c: (c[0] or 0, c[1]))}
    n, d = cands.pop()
    if per_m:
        return {"state": "PARSED", "raw": raw, "count": None, "dia_mm": d, "spacing_m": round(1.0 / n, 4),
                "per_m": n, "kind": "LINKS"}
    return {"state": "PARSED", "raw": raw, "count": n, "dia_mm": d, "spacing_m": sp,
            "kind": ("LINKS" if n is None else "BARS_AT_SPACING" if sp else "BARS")}


def agree(a, b):
    keys = ("count", "dia_mm", "spacing_m")
    return a.get("state") == b.get("state") == "PARSED" and all(a.get(k) == b.get(k) for k in keys)


def caption_of(text):
    """caption text -> {family, condition, min_span_m, max_span_m, qualifiers} or None when it is no caption."""
    u = re.sub(r"\s+", " ", (text or "").upper())
    fam = next((f for f, rx in MEMBER_WORDS if re.search(rx, u)), None)
    scale = re.search(r"\(1\s*:\s*(\d+)\)", u)
    if fam is None:
        return None
    out = {"family": fam, "scale": int(scale.group(1)) if scale else None, "condition": "TYPICAL",
           "min_span_m": None, "max_span_m": None, "qualifiers": []}
    m = re.search(r"(MORE|GREATER|OVER|LESS|SHORTER|UNDER)\s+THAN\s+(\d+(?:\.\d+)?)\s*M\b", u) or \
        re.search(r"([<>])\s*(\d+(?:\.\d+)?)\s*M\b", u)
    if m:
        v = float(m.group(2))
        if m.group(1) in ("MORE", "GREATER", "OVER", ">"):
            out.update(condition="SPAN_MIN", min_span_m=v)
        else:
            out.update(condition="SPAN_MAX", max_span_m=v)
    if re.search(r"EXTERIOR|EXTERNAL|OUTER\s+WALL", u):
        out["condition"] = "EXTERIOR"
    for q, rx in (("WITHOUT_CONCENTRATED_LOAD", r"WITHOUT\s+CONCENTRATED"), ("WITH_CONCENTRATED_LOAD",
                                                                              r"(?<!OUT )\bWITH\s+CONCENTRATED")):
        if re.search(rx, u):
            out["qualifiers"].append(q)
    return out


def _centre(b):
    return (b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0


def _caption_below(box, captions, pad_frac):
    cx, _ = _centre(box)
    best = None
    for c in captions:
        x0, y0, x1, y1 = c["box"]
        pad = (x1 - x0) * pad_frac
        if not (x0 - pad <= cx <= x1 + pad) or y0 < box[3]:
            continue
        if best is None or y0 < best[0]:
            best = (y0, c["caption_id"])
    return best[1] if best else None


def assemble(tokens, captions, *, rejected=(), pad_frac=0.1):
    """tokens: [{record_id, box (x0, y0, x1, y1) in page units with y DOWN, parsed}] (accepted reads only);
    captions: [{caption_id, box, caption (caption_of)}]; rejected: [{record_id, box}] notation reads that failed the
    checks - a detail that owns one is incomplete, and the role it would have filled is missing, never zero.
    -> details [{detail_id, caption_id, caption, bars, state, rejected_records}]."""
    owner, rej = {}, {}
    for t in tokens:
        cid = _caption_below(t["box"], captions, pad_frac)
        if cid:
            owner.setdefault(cid, []).append(t)
    for t in rejected:
        cid = _caption_below(t["box"], captions, pad_frac)
        if cid:
            rej.setdefault(cid, []).append(t["record_id"])
    out = []
    for c in captions:
        ts = sorted(owner.get(c["caption_id"], []), key=lambda t: _centre(t["box"])[1])
        bars, state = [], "ASSEMBLED"
        counts = [t for t in ts if t["parsed"]["kind"] == "BARS"]
        for t in ts:
            p = t["parsed"]
            role = {"LINKS": "LINKS", "BARS_AT_SPACING": "SIDE"}.get(p["kind"])
            if role is None:
                if len(counts) < 2:
                    role = "UNRESOLVED"
                else:
                    role = "TOP" if t is counts[0] else "BOTTOM"
            bars.append({"role": role, "count": p["count"], "dia_mm": p["dia_mm"], "spacing_m": p["spacing_m"],
                         "record_id": t["record_id"], "role_basis": "VERTICAL_ORDER_IN_DETAIL"})
        if not bars:
            state = "NO_BARS"
        elif any(b["role"] == "UNRESOLVED" for b in bars):
            state = "ROLE_UNRESOLVED"
        out.append({"detail_id": "DET-" + c["caption_id"], "caption_id": c["caption_id"], "caption": c["caption"],
                    "bars": bars, "state": state, "rejected_records": rej.get(c["caption_id"], [])})
    return out


def summarize_bars(bars):
    """role -> [(count, dia, spacing)] with BOTTOM layers summed per diameter (3+3 Ø16 -> 6 Ø16)."""
    out = {}
    for b in bars:
        r = b["role"]
        if r in ("TOP", "BOTTOM"):
            prev = next((x for x in out.get(r, []) if x[1] == b["dia_mm"]), None)
            if prev:
                out[r] = [(x[0] + b["count"], x[1], x[2]) if x is prev else x for x in out[r]]
                continue
        out.setdefault(r, []).append((b["count"], b["dia_mm"], b["spacing_m"]))
    return out


def glyph_votes(observations, *, min_votes=3, share=0.7):
    """observations: [(glyph_class, char)] from every OCR word whose glyph count equals its length (a whole page).
    -> class -> char. A vector-glyph PDF draws one character with one shape, so a shape OCR reads as '3' eight times
    and '5' twice is a '3'. A class whose votes spread over the diameter-sign misreads (0 / 6 / 9 / ¢ ...) with no
    clear winner is the diameter sign. Classes without a clear majority stay unknown (None)."""
    by = {}
    for cls, ch in observations:
        by.setdefault(cls, []).append(ch)
    out = {}
    for cls, chs in by.items():
        top = max(set(chs), key=lambda c: (chs.count(c), c))
        n = chs.count(top)
        if n >= min_votes and n >= share * len(chs):
            out[cls] = top
        elif len(chs) >= min_votes and sum(1 for c in chs if c in DIA_GLYPHS) >= 0.8 * len(chs):
            out[cls] = "Ø"
        else:
            out[cls] = None
    return out


def glyph_check(read, classes, glyph_chars):
    """a read against the token's vector glyphs: VERIFIED when the glyph count equals the read length, every glyph a
    count / diameter / spacing digit sits on has a known character and each one equals the read (the diameter sign
    matches any of its misreads); CONTRADICTED when a known glyph differs; UNCHECKED otherwise."""
    t = (read or "").replace(" ", "")
    if not classes or len(classes) != len(t):
        return "UNCHECKED"
    p = parse_notation(t)
    if p["state"] != "PARSED":
        return "UNCHECKED"
    known_all = True
    for ch, cls in zip(t, classes):
        g = glyph_chars.get(cls)
        if g is None:
            if ch.isdigit():
                known_all = False
            continue
        if g == "Ø":
            if ch not in DIA_GLYPHS:
                return "CONTRADICTED"
        elif g != ch:
            return "CONTRADICTED"
    return "VERIFIED" if known_all else "UNCHECKED"


def manual_record(record_id, *, page, region, text, parsed=None, by, on, note=""):
    """A transcription by a person, in the same schema (the structured fallback when OCR is absent or rejected)."""
    p = parsed or parse_notation(text)
    return {"record_id": record_id, "page": page, "region_pt": list(region), "method": "MANUAL_TRANSCRIPTION",
            "raw_text": text, "confidence": None, "reads": [], "parsed": p,
            "state": "MANUALLY_CONFIRMED" if p.get("state") == "PARSED" else "OCR_REJECTED_UNPARSED",
            "confirmed_by": by, "confirmed_on": on, "note": note}


def manual_detail(detail_id, caption_text, bars, *, page):
    """A detail written by a person: bars = [(role, record)] with records from manual_record. Same schema as an
    assembled machine detail, so the engine treats both alike (and never as OCR)."""
    out = []
    for role, r in bars:
        p = r["parsed"]
        out.append({"role": role, "count": p.get("count"), "dia_mm": p.get("dia_mm"), "spacing_m": p.get("spacing_m"),
                    "record_id": r["record_id"], "role_basis": "MANUAL_TRANSCRIPTION"})
    return {"detail_id": detail_id, "caption_id": detail_id, "caption": caption_of(caption_text), "bars": out,
            "state": "ASSEMBLED", "rejected_records": [], "page": page}


def validate(ev):
    """schema check of an evidence document (machine or manual); returns a list of problems (empty = valid)."""
    bad = []
    if ev.get("schema") != SCHEMA:
        bad.append("schema")
    ids = set()
    for r in ev.get("records", []):
        for k in ("record_id", "page", "method", "state", "parsed"):
            if k not in r:
                bad.append(f"{r.get('record_id')}: {k} missing")
        if r.get("state") not in STATES:
            bad.append(f"{r.get('record_id')}: state {r.get('state')}")
        if r.get("method", "").startswith("OCR") and r.get("state") == "OCR_UNREVIEWED" and len(r.get("reads", [])) < 2:
            bad.append(f"{r.get('record_id')}: an accepted OCR record needs two agreeing reads")
        if r.get("state") == "MANUALLY_CONFIRMED" and not (r.get("confirmed_by") and r.get("confirmed_on")):
            bad.append(f"{r.get('record_id')}: a confirmation names who and when")
        if r.get("raw_text") and redact(r["raw_text"], ev.get("redact_patterns")):
            bad.append(f"{r.get('record_id')}: raw text matches a redaction pattern")
        ids.add(r.get("record_id"))
    for d in ev.get("details", []):
        for b in d.get("bars", []):
            if b.get("record_id") not in ids:
                bad.append(f"{d.get('detail_id')}: bar from unknown record {b.get('record_id')}")
    return bad


def ground_beam_details(ev):
    """the usable ground-beam details of an evidence document: [{condition, min/max span, bars (summarized), state,
    method, records}] - a detail is usable only when every bar record it uses is in a USABLE state."""
    recs = {r["record_id"]: r for r in (ev or {}).get("records", [])}
    out = []
    for d in (ev or {}).get("details", []):
        cap = d.get("caption") or {}
        if cap.get("family") != "GROUND_BEAM" or d.get("state") != "ASSEMBLED":
            continue
        used = [recs.get(b["record_id"]) for b in d["bars"]]
        if not used or any(r is None or r["state"] not in USABLE for r in used):
            continue
        out.append({"detail_id": d["detail_id"], "condition": cap["condition"], "min_span_m": cap.get("min_span_m"),
                    "max_span_m": cap.get("max_span_m"), "qualifiers": cap.get("qualifiers", []),
                    "bars": summarize_bars(d["bars"]), "rejected_records": d.get("rejected_records", []),
                    "ocr": any(r["method"].startswith("OCR") and r["state"] != "MANUALLY_CONFIRMED" for r in used),
                    "records": [r["record_id"] for r in used], "page": used[0]["page"]})
    return out


def match_class(details, cls, classes):
    """the ground-beam detail for a typical class {max_span_m} of an ascending class table: a SPAN_MAX caption with
    the same bound, or the SPAN_MIN caption whose bound is the previous class's maximum (the open-ended class)."""
    if cls.get("max_span_m") is not None:
        hit = [d for d in details if d["condition"] == "SPAN_MAX" and d["max_span_m"] == cls["max_span_m"]]
    else:
        prev = max((c["max_span_m"] for c in classes if c.get("max_span_m") is not None), default=None)
        hit = [d for d in details if d["condition"] == "SPAN_MIN" and d["min_span_m"] == prev]
    return hit[0] if len(hit) == 1 else None


def policy_record():
    return {"policy": POLICY_ID, "schema": SCHEMA, "states": list(STATES), "usable": list(USABLE),
            "rule": "OCR-derived values are PROVISIONAL / LOW / OCR_DERIVED_UNREVIEWED until a person confirms them; "
                    "a token is accepted only when two independent reads give the same unique parse"}
