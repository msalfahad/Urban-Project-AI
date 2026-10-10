# A18 input isolation — the contract, the manifest, and the judgement calls

Owner directive, 2026-09-17: *"The purpose is to test whether A18 can SEE
and INTERPRET the drawing, not whether it can retrieve an answer already
present elsewhere in the repository."*

A18 does not exist in this codebase yet. The contract does, so that it is
in force the moment a blind pass runs, and so that the input side of that
pass can be sealed and hashed **before** the pass sees anything.

## What is in force

| | |
|---|---|
| `engine/blind_input_contract.py` | the contract: six gates, the run, the manifest |
| `tools/a18_input_set.py` | assembles a blind input set and writes the manifest |
| `tests/test_blind_input_contract.py` | 27 tests |
| Invariant §99 | the rule in prose |
| `UP-QA-002` | the rule in the library (v1.4.0) |

## The gates

`DECLARED` → `KIND` → `PATH` → `CROP_BASIS` → `EXISTS` → `CONTENT`.

The path is checked **as well as** the declared kind, so relabelling a
reconciliation file as sheet metadata does not get it through — and the
path is answered before the file is looked for on disk, so a prohibited
file is refused as what it is rather than as a typo. An **undeclared kind
is refused**: a missing rule is not a permissive rule.

Nothing prohibited is ever opened. The path gate answers before the
content gate, which is the only gate that reads.

## Two things the directive implies but does not say

**A crop drawn around the answer is the answer.** A crop box chosen from a
known target dimension hands the pass the reading it was meant to find,
in a form no content scan can catch. So every crop declares what decided
its box — a uniform tiling of the sheet, coordinates read off the drawing,
or the agent asking to look there — and a crop with no basis is refused.

**A specification about the space under test is not a specification.** The
directive allows "project specifications that would normally be available
on a real project". A surveyor on site has the spec. But the P7757 spec
contains the block that says the pantry is an open American pantry
opening toward the dining, saloon and living area — which is a large part
of what a ground-floor open-zone reading has to establish. So the spec is
projected: the blocks that name a space under test are withheld, the rest
(stair, elevator, sources) stay, and the withheld block ids are in the
manifest. If the owner judges that the pantry openness rule is ordinary
project information a blind pass should have, removing `PANTRY` from the
subject terms restores it, on the record.

## Refusal is not contamination

An input refused **at the door** never reached the agent: the refusal is
recorded and the run stays `BLIND_RUN_VALID`. Prohibited information
found **in the context** — pasted into a prompt, carried in a previous
turn, read from a file nobody screened — ends the run:
`BLIND_TEST_INVALID`, `stopped = true`, and every further offer raises
`BlindTestInvalid`. There is no partial credit; a pass that has seen the
answer cannot un-see it.

`BlindRun.check_context(payload)` scans an assembled context before it
goes out, and invalidates the run rather than quietly redacting it.

## The first sealed input set — A18-GF-001

`python -m tools.a18_input_set --source data/golden/7757/inputs/P7757_DRAWINGS.pdf …`

`data/runs/7757/blind/A18_INPUT_MANIFEST.json` —
`pass_state: INPUTS_SEALED_PASS_NOT_YET_RUN`, 17 offered, 13 admitted,
4 refused, 0 violations.

Admitted: ten page images extracted at the resolution they were scanned
at (4672 × 6624 px each, `RAW_FILE_SHA256` per page); `META-01`, what the
drawing file says about its own sheets; `RULES-01`, 42 approved general
rules; `SPEC-01`, the project specification minus the pantry block.

Refused on the record, by offering the real files deliberately:

| offered as | refused by | it would have been |
|---|---|---|
| the sealed area take-off, as a drawing | `PATH_GATE` | `A_KNOWN_TARGET_AREA` |
| the open-zone reconciliation, as sheet metadata | `PATH_GATE` | `A_RECONCILIATION_FILE` |
| the owner rule requests, as a specification | `PATH_GATE` | `AN_OWNER_RULE_REQUEST_THAT_REVEALS_GEOMETRY` |
| the Round 6E-A export manifest, as a specification | `PATH_GATE` | `A_PREVIOUS_AGENT_ANSWER` |

Two rules were withheld from the rule book itself: `UP-QA-001` (benchmark
anchoring) and `UP-QA-002` (this contract). The rules describing how the
blind test works are not for the agent under test.

## What the drawing does not establish

This set carries **no text layer**. The floor of each page is
`NOT_ESTABLISHED_FROM_THE_DRAWING`, and the metadata says so rather than
supplying it from the supervised floor assignment. Identifying the
ground-floor sheet from its title block is part of what A18 is being
asked to do.

## Conservative where the directive is narrow

The directive prohibits "OWNER_RULE_REQUEST content that reveals expected
geometry". The path gate refuses `OWNER_RULE_REQUESTS.json` **whole**,
rather than trying to sort revealing questions from harmless ones. If the
owner wants specific requests admitted, they can be projected the way the
rules and the spec are — named, hashed, and on the record.
