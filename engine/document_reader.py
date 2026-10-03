"""E89 — read what the drawing SAYS, and keep it away from the geometry.

§7 of the hybrid round: start document understanding. The localiser
(`glyph_text`) has already found WHERE the text is; this module turns those
places into OBSERVATIONS with a raw string, a normalised interpretation, an
anchor, a source, a confidence, an evidence family and an independence
class.

Three rules that the whole round depends on:

  1. AN OBSERVATION IS NOT A MEASUREMENT. A printed "1850" is evidence about
     a size. It is not 1850 mm of wall, and it may never become a released
     millimetre. §18 compares it against the vector measurement and reports
     AGREE / DISAGREE / AMBIGUOUS / NOT_PRESENT — and never averages them.

  2. A DIMENSION MAY NOT LIFT AN IDENTITY. `document_observations` already
     fixes this: a printed 3.50 matching a measured 3497 proves the SIZE is
     right and says nothing about WHICH ROOM it is, because a bedroom and a
     bathroom can both be 3.50 m wide. That is the WSH-01 error in a new
     costume, and `require_use` raises on it.

  3. THE MODEL IS A READER, NOT A SURVEYOR. It is shown a crop and asked
     what characters are in it. It is never asked how big anything is, where
     a wall runs, or which room it is looking at — questions whose answers
     would arrive as confident prose with no evidence behind them.

Every call is cached on the crop's own bytes, so a re-run reads from disk
and costs nothing. The seam is injectable: tests pass a stub and the whole
module runs offline.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from engine.document_observations import (
    DOOR_SCHEDULE_ENTRY, GLYPH_OUTLINE, PRINTED_DIMENSION, ROOM_LABEL,
    PrintedDimensionObservation, TextObservation)

# Where a reading came from, and whether it is independent of the drawing.
# The raster of a sheet and the sheet's own glyphs are the SAME DRAWING: a
# vision pass over this PDF corroborates nothing about the building, it only
# tells us what is written on this one document.
INDEPENDENCE_SAME_DRAWING = "SAME_DRAWING"
INDEPENDENCE_SAME_DOCUMENT_SET = "SAME_DOCUMENT_SET"
INDEPENDENCE_INDEPENDENT = "INDEPENDENT_OF_THE_DRAWING"

FAMILY_DOCUMENT = "DOCUMENT"

SYSTEM = """\
You are reading a small crop of an architectural drawing. Report ONLY the \
characters you can actually see.

Return JSON: {"items": [{"text": "...", "kind": "...", "confidence": 0.0-1.0}]}

kind is one of:
  DIMENSION   a bare number that dimensions something (e.g. 1850, 4.25)
  ROOM_LABEL  a room name (in any language, e.g. BED ROOM, حمام)
  TAG         a short code or reference (e.g. D1, W3, AR-00)
  NOTE        any other text (titles, addresses, phone numbers, notes)

Rules:
- Transcribe exactly what is printed, including the original language. Do \
not translate, expand, correct or complete anything.
- If a crop contains several separate strings, return one item per string.
- If the crop contains no readable text (it is a symbol, a wall, hatching or \
blank), return {"items": []}. An empty answer is a correct answer.
- Never guess a character you cannot see. Never infer a dimension from how \
long something looks: you are reading text, not measuring.
- Do not say which room a label belongs to, how big anything is, or what \
any symbol means.
"""

USER = ("Transcribe the text in this crop of an architectural drawing. "
        "Return the JSON described in the system prompt and nothing else.")

# What a dimension string may look like on a Kuwaiti architectural sheet.
_MM = re.compile(r"^\s*(\d{2,5})\s*$")
_METRES = re.compile(r"^\s*(\d{1,2})[.,](\d{1,3})\s*$")
_PAIR = re.compile(r"^\s*(\d{2,5})\s*[x×X]\s*(\d{2,5})\s*$")


@dataclass
class Report:
    dimensions: list = field(default_factory=list)
    labels: list = field(default_factory=list)
    other: list = field(default_factory=list)
    runs_read: int = 0
    runs_empty: int = 0
    calls_made: int = 0
    calls_cached: int = 0
    failures: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def record(self, *, limit: int = 300) -> dict:
        parsed = [d for d in self.dimensions if d.is_parsed]
        return {
            "runs_read": self.runs_read,
            "runs_with_no_readable_text": self.runs_empty,
            "model_calls_made": self.calls_made,
            "model_calls_served_from_cache": self.calls_cached,
            "printed_dimensions": len(self.dimensions),
            "printed_dimensions_parsed": len(parsed),
            "room_labels": len(self.labels),
            "other_text": len(self.other),
            "by_label_text": dict(Counter(
                o.raw_text.strip().upper() for o in self.labels).most_common(
                    40)),
            "dimension_rows": [o.record() for o in self.dimensions[:limit]],
            "label_rows": [o.record() for o in self.labels[:limit]],
            "other_rows": [o.record() for o in self.other[:80]],
            "read_failures": list(self.failures),
            "evidence_discipline": {
                "a_printed_dimension_is": (
                    "SIZE evidence about the drawing. It is NOT a released "
                    "millimetre and it may not lift a room's identity: a "
                    "bedroom and a bathroom can both be 3.50 m wide"),
                "a_room_label_is": (
                    "IDENTITY evidence. It says nothing about size and "
                    "cannot close a wall"),
                "independence": (
                    "every observation here is SAME_DRAWING. Reading this "
                    "sheet's own glyphs — by vision or any other means — "
                    "corroborates nothing about the building: it tells us "
                    "what is written on one document"),
                "the_model_was_asked": (
                    "what characters are in a crop. It was NOT asked how "
                    "big anything is, where a wall runs, or which room it "
                    "is looking at"),
            },
            "notes": dict(self.notes),
        }


def read_runs(pdf: str, runs, *, reader=None, cache_dir: str = "",
              drawing_id: str = "", revision: str = "", dpi: int = 600,
              limit: int | None = None) -> Report:
    """Transcribe each located text run into observations.

    `reader` is a VisionFn (system, user, images) -> raw text. Omit it and
    nothing is read: the report says so rather than inventing an empty
    result, because "no text found" and "nobody looked" are different
    facts.
    """
    from engine import glyph_text as gt

    rep = Report()
    chosen = list(runs)[:limit] if limit else list(runs)
    cache = Path(cache_dir) if cache_dir else None
    if cache:
        cache.mkdir(parents=True, exist_ok=True)

    if reader is None and cache is None:
        rep.notes["status"] = "NOT_READ_NO_READER_SUPPLIED"
        rep.notes["why"] = (
            "no vision reader and no cache were supplied, so no run was "
            "transcribed. That is not the same as a drawing with no text: "
            f"{len(chosen)} runs were located and none was read")
        return rep

    n = 0
    for run in chosen:
        png = gt.render_crop(pdf, run, dpi=dpi)
        key = hashlib.sha256(png).hexdigest()[:32]
        hit = cache / f"{key}.json" if cache else None

        if hit is not None and hit.exists():
            payload = json.loads(hit.read_text())
            rep.calls_cached += 1
        elif reader is None:
            continue
        else:
            try:
                raw = reader(SYSTEM, USER, [("image/png", png)])
            except Exception as exc:                     # noqa: BLE001
                rep.failures.append({"run_id": run.run_id,
                                     "error": type(exc).__name__,
                                     "detail": str(exc)[:200]})
                continue
            payload = _parse(raw)
            rep.calls_made += 1
            if hit is not None:
                hit.write_text(json.dumps(payload, ensure_ascii=False,
                                          indent=1))

        rep.runs_read += 1
        items = payload.get("items") or []
        if not items:
            rep.runs_empty += 1
        for item in items:
            n += 1
            _store(rep, run, item, n, drawing_id, revision)

    rep.notes.setdefault("status", "READ")
    rep.notes["runs_offered"] = len(chosen)
    rep.notes["dpi"] = dpi
    rep.notes["cache_dir"] = str(cache) if cache else ""
    return rep


def _parse(raw: str) -> dict:
    """Tolerantly pull the JSON out; a bad answer is a failure, not a guess."""
    from agents.base import extract_json

    try:
        got = extract_json(raw)
    except ValueError:
        return {"items": []}
    if isinstance(got, list):
        return {"items": got}
    return got if isinstance(got, dict) else {"items": []}


def _store(rep: Report, run, item: dict, n: int, drawing_id: str,
           revision: str) -> None:
    text = str(item.get("text") or "").strip()
    if not text:
        return
    kind = str(item.get("kind") or "NOTE").upper()
    conf = item.get("confidence")
    conf = float(conf) if isinstance(conf, (int, float)) else None
    oid = f"DO-{n:05d}"

    if kind == "DIMENSION":
        value, unit, note = _parse_dimension(text)
        rep.dimensions.append(PrintedDimensionObservation(
            observation_id=oid, raw_text=text, parsed_value_mm=value,
            unit_as_printed=unit,
            orientation=run.orientation,
            anchor_mm=run.centre_mm, text_source=GLYPH_OUTLINE,
            drawing_id=drawing_id, drawing_revision=revision,
            confidence=conf, parse_note=note))
        return

    if kind == "ROOM_LABEL":
        rep.labels.append(TextObservation(
            observation_id=oid, kind=ROOM_LABEL, raw_text=text,
            anchor_mm=run.centre_mm, text_source=GLYPH_OUTLINE,
            drawing_id=drawing_id, drawing_revision=revision,
            confidence=conf,
            fields={"normalised": text.strip().upper(),
                    "run_id": run.run_id,
                    "evidence_family": FAMILY_DOCUMENT,
                    "source_independence_class": INDEPENDENCE_SAME_DRAWING}))
        return

    rep.other.append(TextObservation(
        observation_id=oid,
        kind=DOOR_SCHEDULE_ENTRY if kind == "TAG" else ROOM_LABEL,
        raw_text=text, anchor_mm=run.centre_mm, text_source=GLYPH_OUTLINE,
        drawing_id=drawing_id, drawing_revision=revision, confidence=conf,
        fields={"read_as": kind, "run_id": run.run_id,
                "evidence_family": FAMILY_DOCUMENT,
                "source_independence_class": INDEPENDENCE_SAME_DRAWING,
                "note": ("stored as read. A TAG is opening/reference "
                         "evidence and a NOTE is neither size nor "
                         "identity evidence until something says so")}))


def _parse_dimension(text: str) -> tuple:
    """Turn a printed string into millimetres, or refuse.

    None is not zero: an unparsed dimension is an observation whose value is
    unknown, which is a different thing from a dimension of zero.
    """
    m = _MM.match(text)
    if m:
        return float(m.group(1)), "mm", "bare integer read as millimetres"
    m = _METRES.match(text)
    if m:
        whole, frac = m.group(1), m.group(2)
        val = float(f"{whole}.{frac}") * 1000.0
        return val, "m", (f"decimal read as metres ({whole}.{frac} m) "
                          "because an architectural sheet prints metres "
                          "with a separator and millimetres without")
    m = _PAIR.match(text)
    if m:
        return None, "mm", (f"a PAIR of dimensions ({m.group(1)} x "
                            f"{m.group(2)}). Not parsed to one value: which "
                            "side is which is not established by the text")
    return None, "", ("not a dimension this parser recognises. Left "
                      "unparsed rather than coerced")
