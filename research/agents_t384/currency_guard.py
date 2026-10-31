"""T-384: currency-figure guard for the PUBLIC repository (research/, tests/, docs/).

The freelancer's workbooks and the client's commercial documents are private. Workers may quote a freelancer QUANTITY
for comparison, never his RATE or AMOUNT. This module finds every line that carries a figure in a currency unit
(Kuwaiti dinar / fils, English or Arabic) so that:

* the sweep (``python3 -I research/agents_t384/currency_guard.py``) lists each hit by file:line and token kind only,
  never the figure itself;
* ``tests/t384_currency_guard`` refuses a currency figure in any research / tests / docs file that is not in the
  classified baseline ``CURRENCY_BASELINE_T384.json`` (files carrying such a figure at the T-384 commit, each with its
  source class and the action taken).

A figure is a number written directly before or after a currency token (KWD, KD, K.D., fils, or the Arabic dinar /
fils words and abbreviation) or a number assigned to a currency-named key (a key ending in _kwd, _kd or _fils). A
currency word without a number (an f-string "{rate} KWD/m3", the column name KWD) is not a figure. Tokens are case-sensitive on purpose: identifiers such as ``kd3`` or a temporary
folder name ending in ``hkd`` are not currency.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CURRENCY_BASELINE_T384.json")
SCOPES = ("research", "tests", "docs")
TEXT_EXT = {".py", ".md", ".txt", ".json", ".jsonl", ".csv", ".tsv", ".html", ".htm", ".svg", ".yaml", ".yml", ".toml",
            ".xml", ".ini", ".cfg", ".rst"}

_NUM = r"\d[\d,]*(?:\.\d+)?"
_TOK = r"(?:KWD|K\.D\.?|KD|[Ff]ils|د\.ك|دينار|دنانير|فلس)"
_PATTERNS = (
    ("NUMBER_THEN_TOKEN", re.compile(rf"(?<![\w.]){_NUM}\s*{_TOK}(?![A-Za-z_])")),
    ("TOKEN_THEN_NUMBER", re.compile(rf"(?<![A-Za-z_]){_TOK}\s*{_NUM}")),
    ("CURRENCY_KEY_VALUE", re.compile(rf"\w*_(?:kwd|KWD|kd|KD|fils)\"?\s*[:=]\s*-?{_NUM}")),
)


def scan_text(text):
    """Return [(line_no, kind)] for every line carrying a currency figure (first match per line). No figure is returned."""
    hits = []
    for no, line in enumerate(text.splitlines(), 1):
        for kind, pat in _PATTERNS:
            if pat.search(line):
                hits.append((no, kind))
                break
    return hits


def scan_file(path):
    if os.path.splitext(path)[1].lower() not in TEXT_EXT:
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except (UnicodeDecodeError, OSError):
        return []
    return scan_text(text)


def scan_tree(root=ROOT, scopes=SCOPES):
    """{relative path: [(line, kind)]} for every text file under the scopes that carries a currency figure."""
    out = {}
    for scope in scopes:
        base = os.path.join(root, scope)
        for dp, dn, fn in os.walk(base):
            dn[:] = sorted(d for d in dn if d not in ("__pycache__", ".pytest_cache"))
            for f in sorted(fn):
                p = os.path.join(dp, f)
                hits = scan_file(p)
                if hits:
                    out[os.path.relpath(p, root).replace(os.sep, "/")] = hits
    return out


def load_baseline(path=BASELINE):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def unlisted(found, baseline):
    """Files carrying a currency figure that the classified baseline does not list."""
    listed = set(baseline["files"])
    return sorted(p for p in found if p not in listed)


if __name__ == "__main__":
    found = scan_tree()
    for path, hits in sorted(found.items()):
        for no, kind in hits:
            print(f"{path}:{no}\t{kind}")
    print(f"{sum(len(h) for h in found.values())} lines in {len(found)} files", file=sys.stderr)
