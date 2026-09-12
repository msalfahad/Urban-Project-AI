"""Shared agent framework.

Every agent is the same shape (load prompt, call the model, validate the output,
hand it back), so that shape lives here once and each agent stays a thin file.

The model call is a single injectable seam:

- In production, `anthropic_model` calls the Claude API.
- In tests, a stub function is passed instead, so the whole roster runs offline
  with no API key and no network.

The one rule holds here too: this module moves text in and structured records
out. It never computes a total or applies a rate — that is the engine's job.

## Model policy

Three tiers, chosen by what a mistake costs:

- `BEST` (Claude Fable 5.1) for the work where a wrong number costs thousands —
  reading drawings (A1, A2) and writing the client's quotation or contract
  (A7). Always, never escalated to: a plausible wrong dimension passes every
  validator, so "try cheap first" cannot protect this work.
- `CHEAP` (Claude Haiku 4.5) for everything else, at a tenth of the price.
- `REASONING` (Claude Sonnet 5) as the automatic second try when the cheap
  model's output fails to parse or validate — `ladder()` does this, so an
  agent pays for the stronger model only on the calls that turned out hard.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Sequence

# A model function takes (system_prompt, user_text) and returns raw text.
ModelFn = Callable[[str, str], str]

CHEAP = "claude-haiku-4-5"
REASONING = "claude-sonnet-5"
BEST = "claude-fable-5-1"

DEFAULT_MODEL = CHEAP


class ModelRefused(RuntimeError):
    """The model declined the request (stop_reason 'refusal') — not an empty answer."""


def anthropic_model(
    system: str,
    user: str,
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 16000,
    effort: str | None = None,
) -> str:
    """Call Claude and return the concatenated text of the response.

    Imported lazily so the package imports (and tests run) without the
    `anthropic` library or an API key present. Credentials resolve from the
    environment (`ANTHROPIC_API_KEY` or an `ant auth login` profile) — never
    hard-code a key.
    """
    import anthropic  # lazy: only needed when actually calling the API

    client = anthropic.Anthropic()
    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    if effort:
        kwargs["output_config"] = {"effort": effort}

    # Large output budgets must stream (the SDK refuses non-streaming calls that
    # could exceed ~10 minutes). Collect the text the same way either path.
    def _call(kw: dict[str, Any]):
        if kw.get("max_tokens", 0) > 20000:
            with client.messages.stream(**kw) as stream:
                resp = stream.get_final_message()
        else:
            resp = client.messages.create(**kw)
        if resp.stop_reason == "refusal":
            details = getattr(resp, "stop_details", None)
            raise ModelRefused(f"{model} refused: {getattr(details, 'category', None)}")
        return "".join(b.text for b in resp.content if b.type == "text")

    try:
        return _call(kwargs)
    except anthropic.BadRequestError as exc:
        # The cheap tier does not accept output_config effort. Retry once
        # without it rather than forcing every caller to know which models
        # support the knob — the text-in/records-out contract is unchanged.
        if "output_config" in kwargs and "effort" in str(exc).lower():
            kwargs.pop("output_config", None)
            return _call(kwargs)
        raise


def tiered(model: str, *, effort: str | None = None, max_tokens: int = 16000) -> ModelFn:
    """A ModelFn bound to one tier."""
    return lambda system, user: anthropic_model(
        system, user, model=model, max_tokens=max_tokens, effort=effort)


def ladder(*, max_tokens: int = 16000) -> list[ModelFn]:
    """Cheap first; the reasoning tier only if the cheap output is unusable."""
    return [
        tiered(CHEAP, max_tokens=max_tokens),
        tiered(REASONING, effort="medium", max_tokens=max_tokens),
    ]


def best(*, effort: str = "high", max_tokens: int = 16000) -> ModelFn:
    """The strongest model, for work where a wrong number costs real money."""
    return tiered(BEST, effort=effort, max_tokens=max_tokens)


def extract_json(raw: str) -> Any:
    """Pull a JSON value out of a model response.

    Models are asked to return pure JSON, but they sometimes wrap it in prose or
    a ```json fence. This tries the tolerant paths in order and raises a clear
    error if none yield valid JSON — a bad response must fail loudly, never be
    half-parsed into a wrong number.
    """
    text = raw.strip()

    # 1. The whole thing is JSON.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. A fenced ```json ... ``` block.
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. The first balanced object or array in the text.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue

    raise ValueError(f"model did not return parseable JSON:\n{raw[:500]}")


def run_json_agent(
    prompt_path: str | Path,
    user_text: str,
    parse: Callable[[Any], Any],
    model: ModelFn | Sequence[ModelFn] | None = None,
) -> Any:
    """The shared agent loop: prompt in, validated structured output out.

    `parse` turns the raw JSON into the agent's typed Output and validates it,
    raising if the model returned something malformed. `model` is one function
    (injected in tests) or a ladder of them: each is tried in turn, and the
    next only runs if the previous answer failed to parse or validate. The
    default ladder is cheap-then-reasoning.
    """
    system = Path(prompt_path).read_text(encoding="utf-8")
    models: Sequence[ModelFn]
    if model is None:
        models = ladder()
    elif callable(model):
        models = [model]
    else:
        models = list(model)
    if not models:
        raise ValueError("run_json_agent needs at least one model")

    last: Exception | None = None
    for fn in models:
        raw = fn(system, user_text)
        try:
            return parse(extract_json(raw))
        except ValueError as exc:
            last = exc
    assert last is not None
    raise last
