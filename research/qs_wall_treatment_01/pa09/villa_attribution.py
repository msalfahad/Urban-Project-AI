"""Step 2 of the villa blind validation: read what the owner attributed, and establish what it actually is.

Attribution is the owner's to give.  Identity is not: a file is whatever its bytes say it is, and the one thing a
blind validation cannot survive is measuring a project whose answers the system already holds.  So every attributed
file is hashed against the sealed benchmark's own inputs before it is read as a new project, and the title block is
read for project, sheet, level and date rather than trusted from the filename.

This module does not measure anything.  It decides whether a blind measurement is possible at all.
"""

from __future__ import annotations

import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba import blind as QB

OUT = Path(PR.OUT_DIR) / "pa09_villa_blind"
UP = Path("/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240")

# The owner's message carried the placeholder "[LIST THE FILES HERE]" unfilled, and two attachments.  The
# attachments are taken as the list; nothing else in the session is promoted into this project.
ATTRIBUTED = ["aaaf7dd9-BLOCK__1__PLOT_449-rffff.pdf", "dab4c836-qurtoba.dwg"]

# What the sealed benchmark was measured from.  Read from the benchmark's own module so this check cannot drift.
SEALED_INPUTS = {"DWG": QB.DWG, "PDF": QB.PDF, "DECODE": QB.DECODE}

DISCIPLINE_MARKERS = {
    "ARCHITECTURAL": ("floor plan", "plan", "elevation", "section", "arch"),
    "STRUCTURAL": ("structure", "structural", "-str", "column", "foundation", "slab"),
    "MEP": ("electrical", "mechanical", "plumbing", "sanitary", "hvac", "drainage"),
}
# A full villa is not one sheet.  These are the disciplines and sheets a villa takeoff needs before it can start.
VILLA_REQUIREMENT = [
    "architectural plan of every floor - ground, first, second, roof",
    "elevations",
    "sections",
    "structural drawings",
    "MEP drawings",
    "door and window schedule",
    "finishes schedule or written specification",
]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


# ------------------------------------------------------------------ reading a sheet
def pdf_text(p):
    import pypdf
    return (pypdf.PdfReader(str(p)).pages[0].extract_text() or "")


def pdf_paths(p):
    """Every point the sheet draws.  Two revisions of one sheet are compared on this, not on their title blocks."""
    import pypdf
    c = pypdf.PdfReader(str(p)).pages[0].get_contents().get_data().decode("latin-1")
    return [(round(float(m.group(1)), 1), round(float(m.group(2)), 1))
            for m in re.finditer(r"(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(m|l)\b", c)]


TITLE_FIELDS = {
    # the title block's strings run together when the PDF is flattened ("...ALFAHDSECOND FLOOR PLAN"), so the
    # storey word is matched from a known set rather than as "whatever capitals precede FLOOR PLAN"
    "SHEET_TITLE": r"((?:GROUND|FIRST|SECOND|THIRD|FOURTH|BASEMENT|MEZZANINE|TYPICAL)\s+FLOOR\s+PLAN"
                   r"|ROOF\s+PLAN|ELEVATIONS?|SECTIONS?)",
    "LEVEL": r"(LEVEL\s+[A-Z.]+\s*=\s*[\d.]+\s*m)",
    "SCALE": r"(1\s*[:/]\s*\d+)",
    "OWNER_NAME": r"Mr\s*:\s*([A-Z][A-Z ]+?)(?=(?:GROUND|FIRST|SECOND|THIRD|ROOF|SCALE|$))",
    "SOURCE_PATH": r"([A-Z]:\\\\?[^\s]*\.dwg)",
    "SHEET_DATE": r"([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})",
    "ADDRESS": r"(Sabah[^\n]*)",
    "AREA_M2": r"AREA\s*=?\s*([\d.]+)",
}


def title_block(text):
    out = {}
    for k, pat in TITLE_FIELDS.items():
        m = re.search(pat, text)
        out[k] = m.group(1).strip() if m else None
    return out


def dwg_text(decode):
    d = json.loads(Path(decode).read_text("utf-8"))
    out = []
    for o in d["OBJECTS"]:
        if o.get("entity") in ("TEXT", "MTEXT"):
            s = o.get("text_value") or o.get("text") or ""
            s = re.sub(r"\{\\f[^;]*;", "", s).replace("\\P", " ").replace("}", "").strip()
            if s:
                out.append(s)
    return "\n".join(out)


def discipline_of(name, text):
    low = (name + " " + text).lower()
    hits = [k for k, ms in DISCIPLINE_MARKERS.items() if any(m in low for m in ms)]
    # STRUCTURE in a file path is where the sheet was stored, not what the sheet is.  A sheet that says FLOOR PLAN
    # and carries room names is architectural whatever folder it came out of.
    if "ARCHITECTURAL" in hits:
        return "ARCHITECTURAL", hits
    return (hits[0] if hits else "UNCLASSIFIED"), hits


# ------------------------------------------------------------------ identity against the sealed benchmark
def identity(path, digest):
    for role, sealed in SEALED_INPUTS.items():
        sp = Path(sealed)
        if sp.exists() and sha(sp) == digest:
            return {"IS_A_SEALED_BENCHMARK_INPUT": True, "SEALED_ROLE": role, "SEALED_PATH": str(sp),
                    "HOW": "byte-identical to the file the frozen Qortuba benchmark was measured from"}
    return {"IS_A_SEALED_BENCHMARK_INPUT": False, "SEALED_ROLE": None, "SEALED_PATH": None, "HOW": None}


def revision_compare(a, b):
    """Where two revisions of one sheet differ, and whether the difference is inside the drawing or in its frame."""
    pa, pb = set(pdf_paths(a)), set(pdf_paths(b))
    only_a, only_b, both = pa - pb, pb - pa, pa & pb

    def where(s):
        c = collections.Counter((int(x // 1000) * 1000, int(y // 1000) * 1000) for x, y in s)
        return [{"CELL_X": gx, "CELL_Y": gy, "POINTS": n} for (gx, gy), n in c.most_common(6)]

    # the sheet's frame and title strip sit against x = 0; the plan body is drawn out at x >= 2000
    body = lambda s: sum(1 for x, _y in s if x >= 2000)
    return {
        "A": Path(a).name, "B": Path(b).name,
        "POINTS_A": len(pa), "POINTS_B": len(pb), "SHARED": len(both),
        "ONLY_IN_A": len(only_a), "ONLY_IN_B": len(only_b),
        "ONLY_IN_A_INSIDE_PLAN_BODY": body(only_a), "ONLY_IN_B_INSIDE_PLAN_BODY": body(only_b),
        "WHERE_A_DIFFERS": where(only_a), "WHERE_B_DIFFERS": where(only_b),
        "VERDICT": "MATERIAL_REVISION" if body(only_a) > 200 and body(only_b) > 200 else "TITLE_BLOCK_ONLY",
        "MEANING": "the two sheets are not the same drawing re-plotted: each draws several thousand points the "
                   "other does not, and the differences sit inside the plan body rather than in the title strip",
    }


# ------------------------------------------------------------------ the register
def build():
    rows = []
    for name in ATTRIBUTED:
        p = UP / name
        digest = sha(p)
        ext = p.suffix.lower()
        if ext == ".pdf":
            text = pdf_text(p)
        elif ext == ".dwg":
            ident0 = identity(p, digest)
            # the decode of a byte-identical DWG is the decode of this DWG; nothing is re-decoded
            text = dwg_text(SEALED_INPUTS["DECODE"]) if ident0["IS_A_SEALED_BENCHMARK_INPUT"] else ""
        else:
            text = ""
        tb = title_block(text)
        disc, hits = discipline_of(name, text)
        rows.append({
            "SOURCE": name, "EXT": ext, "SIZE_BYTES": p.stat().st_size, "SHA256": digest,
            "DISCIPLINE": disc, "DISCIPLINE_EVIDENCE": hits,
            "TITLE_BLOCK": tb,
            "IDENTITY": identity(p, digest),
            "READ": bool(text), "TEXT_CHARS": len(text),
        })

    rev = revision_compare(SEALED_INPUTS["PDF"], UP / "aaaf7dd9-BLOCK__1__PLOT_449-rffff.pdf")

    sheets = {r["TITLE_BLOCK"].get("SHEET_TITLE") for r in rows if r["TITLE_BLOCK"].get("SHEET_TITLE")}
    disciplines = sorted({r["DISCIPLINE"] for r in rows})
    sealed_hits = [r for r in rows if r["IDENTITY"]["IS_A_SEALED_BENCHMARK_INPUT"]]

    rec = {
        "ARTIFACT": "FULL_VILLA_BLIND_ATTRIBUTED_SOURCES",
        "PHASE_ID": "FULL_VILLA_BLIND_VALIDATION_01",
        "STEP": "2 - inventory the attributed set, identify disciplines and revisions",
        "OWNER_FILE_LIST_PLACEHOLDER_WAS_FILLED_IN": False,
        "HOW_THE_SET_WAS_DETERMINED": "the owner's list placeholder was left unfilled; the two attached files are "
                                      "taken as the attributed set and nothing else is promoted into the project",
        "ROWS": rows, "COUNT": len(rows),

        # 2 - disciplines and revisions
        "DISCIPLINES_PRESENT": disciplines,
        "SHEETS_PRESENT": sorted(sheets),
        "REVISION_COMPARISON": rev,

        # 3 - what is genuinely missing
        "VILLA_REQUIREMENT": VILLA_REQUIREMENT,
        "DISCIPLINES_MISSING": ["STRUCTURAL", "MEP", "SCHEDULES", "SPECIFICATIONS"],
        "FLOORS_MISSING": ["ground floor", "first floor", "roof plan", "elevations", "sections"],

        # the finding that decides the phase
        "BLIND_MEASUREMENT_POSSIBLE": len(sealed_hits) == 0,
        "SEALED_BENCHMARK_INPUTS_IN_THE_ATTRIBUTED_SET": [r["SOURCE"] for r in sealed_hits],
        "WHY": "a blind validation measures a project whose answers this system does not hold.  The attributed set "
               "is the sealed benchmark's own second-floor sheet: one file is byte-identical to the DWG the frozen "
               "Qortuba takeoff was measured from, and the other is an earlier revision of that same sheet.  "
               "Measuring it would reproduce a known answer and prove nothing about the engine",
        "WHAT_WAS_NOT_DONE": ["no takeoff was produced from these sources",
                              "no Qortuba quantity, rule or comparison result was touched",
                              "no sealed spreadsheet, BOQ, quotation or rate was opened"],
        "GIT_HEAD": _git("rev-parse", "--short", "HEAD"),
    }
    rec["DIGEST"] = hashlib.sha256(
        json.dumps(rec["ROWS"], sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]
    return rec


# ------------------------------------------------------------------ the one consolidated batch
def questions(rec):
    """One batch, in words the owner can answer without opening anything."""
    q = [
        {"NO": "V-01", "KIND": "SOURCE_ATTRIBUTION", "BLOCKS": "the whole phase",
         "ASK": "Both files you attributed are the SECOND FLOOR PLAN of Block 1 / Plot 449 - the flat already "
                "frozen as the benchmark. The DWG is byte-for-byte the file the benchmark was measured from. "
                "Did you mean to send the rest of the villa - ground floor, first floor, roof, elevations, "
                "sections - or a different building altogether?",
         "WHY_IT_MATTERS": "measuring the benchmark's own sheet cannot validate anything; the answer is already in "
                           "the system"},
        {"NO": "V-02", "KIND": "SCOPE", "BLOCKS": "what the villa takeoff covers",
         "ASK": "When you say FULL VILLA, do you mean the whole building at Plot 449 - every floor including the "
                "second-floor flat already measured - or only the floors that have never been taken off?",
         "WHY_IT_MATTERS": "if the second floor is inside the scope, that floor is not blind and has to be scored "
                           "separately from the rest"},
        {"NO": "V-03", "KIND": "REVISION", "BLOCKS": "nothing yet; it flags a risk to the frozen benchmark",
         "ASK": "The PDF you just sent is an EARLIER revision of the benchmark sheet - dated Oct 13 2024, level "
                "S.F = 4.20 m - while the benchmark was measured from the Apr 14 2025 revision at R.F = 4.00 m. "
                "The two drawings genuinely differ inside the plan, not just in the title block. Which revision is "
                "the built one?",
         "WHY_IT_MATTERS": "if the older sheet is the built one, the frozen Qortuba takeoff was measured from a "
                           "superseded drawing. I have not touched the benchmark; reopening it is your call"},
        {"NO": "V-04", "KIND": "SOURCE_ATTRIBUTION", "BLOCKS": "step 1 of the previous turn, still open",
         "ASK": "Six drawings in this session name no project: 20230331-STR.dwg, an Arabic-named R_01 PDF, two "
                "identical .dwf files dated 2026-05-06, a file that looks like the Urban Projects logo, and a "
                "PDF named 7f381d98-...251122_120119. Do any of these belong to the villa?",
         "WHY_IT_MATTERS": "attribution is yours to give; I will not guess a project from a filename"},
    ]
    return {"ARTIFACT": "FULL_VILLA_BLIND_OWNER_QUESTIONS_BATCH_01", "PHASE_ID": rec["PHASE_ID"],
            "BATCH": 1, "COUNT": len(q), "QUESTIONS": q,
            "NUMBERING": "V-nn is a new namespace for this project.  Qortuba's numbers are sealed with Qortuba and "
                         "are never continued into another project",
            "NOTE": "asked as one batch after the complete read of the attributed set, as instructed"}


def finish():
    rec = build()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "FULL_VILLA_BLIND_ATTRIBUTED_SOURCES.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False, default=str), "utf-8")
    qs = questions(rec)
    (OUT / "FULL_VILLA_BLIND_OWNER_QUESTIONS_BATCH_01.json").write_text(
        json.dumps(qs, indent=1, ensure_ascii=False, default=str), "utf-8")
    return rec, qs


if __name__ == "__main__":
    r, q = finish()
    print(f"{r['COUNT']} attributed sources  |  digest {r['DIGEST']}")
    for row in r["ROWS"]:
        i = row["IDENTITY"]
        print(f"   {row['SOURCE'][:46]:46s} {row['DISCIPLINE']:14s} "
              f"{'SEALED_BENCHMARK_INPUT(' + str(i['SEALED_ROLE']) + ')' if i['IS_A_SEALED_BENCHMARK_INPUT'] else 'not a sealed input'}")
        tb = row["TITLE_BLOCK"]
        print(f"      sheet={tb['SHEET_TITLE']}  level={tb['LEVEL']}  date={tb['SHEET_DATE']}  area={tb['AREA_M2']}")
    rv = r["REVISION_COMPARISON"]
    print(f"\n   revision: {rv['VERDICT']}  shared {rv['SHARED']}  "
          f"only-A {rv['ONLY_IN_A']} ({rv['ONLY_IN_A_INSIDE_PLAN_BODY']} in plan)  "
          f"only-B {rv['ONLY_IN_B']} ({rv['ONLY_IN_B_INSIDE_PLAN_BODY']} in plan)")
    print(f"\n   blind measurement possible: {r['BLIND_MEASUREMENT_POSSIBLE']}")
    print(f"   owner questions: {q['COUNT']} in one batch")
