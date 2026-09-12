# A7 references — how the writer learns the house style

Two things shape what A7 writes, and both are files in this folder:

| File | What it is | Who edits it |
|------|-----------|--------------|
| `clauses_ar.md` | Urban's standard clauses, grouped by scope (`site_setup`, `black_structure`, `basement_waterproofing`, `plumbing`, …). A7 selects the sections for the requested scopes and adapts them. | The owner, as the standard wording evolves. |
| `examples/*.md` | Earlier Urban quotations and contracts, one per file, as plain Markdown. Every file here is appended to A7's prompt as a worked example. | Drop a file in; nothing else to change. |

## Adding an example contract

1. Convert the document to Markdown (text only — the letterhead, barcode and
   tables are rendered by code and need no example).
2. Remove any other company's name; the documents are Urban Projects' alone
   and the validator rejects output that names one.
3. Save it as `examples/<short-name>.md`, e.g. `examples/khaitan-villa-black-structure.md`.
4. Run the offline tests: `python -m pytest agents/a7_quotation`.

Client names and amounts inside an example are fine to keep for style, but
remember this folder is committed — if a document is confidential, distil its
clauses into `clauses_ar.md` instead and keep the original under `data/`,
which git ignores.

## What A7 never writes

Money, dates and durations. Those come from the approved BOQ and the
programme through `engine/documents.py` and the renderer, so a figure in an
example is context, never something A7 copies.
