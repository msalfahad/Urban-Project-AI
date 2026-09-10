"""Shared agent framework.

Every agent is the same shape (load prompt, call the model, validate the output,
hand it back), so that shape lives here once and each agent stays a thin file.

The model call is a single injectable seam:

- In production, `anthropic_model` calls the Claude API.
- In tests, a stub function is passed instead, so the whole roster runs offline
  with no API key and no network.

The one rule holds here too: this module moves text in and structured records
out. It never computes a total or applies a rate — that is the engine's job.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

# A model function takes (system_prompt, user_text) and returns raw text.
ModelFn = Callable[[str, str], str]

# Default model for every agent. Per-agent files may override via MODEL.
# See docs: default to claude-opus-5 unless a specific agent needs otherwise.
DEFAULT_MODEL = "claude-opus-5"


def anthropic_model(
    system: str,
    user: str,
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 16000,
    effort: str | None = "high",
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
                text = "".join(stream.text_stream)
            return text
        resp = client.messages.create(**kw)
        return "".join(b.text for b in resp.content if b.type == "text")

    try:
        return _call(kwargs)
    except anthropic.BadRequestError as exc:
        # Cheaper/faster models (e.g. Haiku) don't accept output_config effort.
        # Retry once without it rather than forcing every caller to know which
        # models support the knob — the text-in/records-out contract is unchanged.
        if "output_config" in kwargs and "effort" in str(exc).lower():
            kwargs.pop("output_config", None)
            return _call(kwargs)
        raise


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
    model: ModelFn | None = None,
) -> Any:
    """The shared agent loop: prompt in, validated structured output out.

    `parse` turns the raw JSON into the agent's typed Output and validates it,
    raising if the model returned something malformed. `model` defaults to the
    real Anthropic call but is injected in tests.
    """
    system = Path(prompt_path).read_text(encoding="utf-8")
    model = model or anthropic_model
    raw = model(system, user_text)
    data = extract_json(raw)
    return parse(data)
