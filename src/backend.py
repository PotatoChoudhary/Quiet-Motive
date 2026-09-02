"""Async OpenAI-compatible backend with reasoning-trace extraction.

Works against local vLLM (`--reasoning-parser qwen3`) or any hosted
OpenAI-compatible endpoint. Handles three ways a model can hand back its
chain of thought:
  1. vLLM's `reasoning_content` field (preferred)
  2. inline <think>...</think> in the content
  3. no separate trace at all (then reasoning is empty and you must say so)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

from openai import AsyncOpenAI

THINK_RE = re.compile(r"<think>(.*?)</think>", re.S | re.I)
ACTION_RE = re.compile(r"<action>\s*([a-z_]+)\s*</action>", re.I)


@dataclass
class Completion:
    reasoning: str
    content: str
    action: Optional[str]
    raw_finish_reason: str = ""
    usage: dict = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class Backend:
    def __init__(self, cfg: dict):
        b = cfg["backend"]
        self.cfg = b
        key = os.environ.get(b.get("api_key_env", "OPENAI_API_KEY"), "") or "EMPTY"
        self.client = AsyncOpenAI(
            base_url=b["base_url"],
            api_key=key,
            timeout=b.get("request_timeout", 300),
            max_retries=0,  # we do our own, with backoff
        )
        self.sem = asyncio.Semaphore(b.get("max_concurrency", 16))
        self.max_retries = b.get("max_retries", 3)

    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 1.0,
        top_p: float = 0.95,
        max_tokens: int = 2048,
        enable_thinking: bool = True,
        seed: Optional[int] = None,
        parse_action: bool = True,
    ) -> Completion:
        model = model or self.cfg["subject_model"]
        kwargs: dict[str, Any] = dict(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
        if seed is not None:
            kwargs["seed"] = seed
        # vLLM passes chat-template kwargs through `extra_body`; hosted APIs
        # ignore unknown keys or 400. We degrade gracefully on the 400.
        extra = {"chat_template_kwargs": {"enable_thinking": bool(enable_thinking)}}

        last_err = ""
        for attempt in range(self.max_retries):
            try:
                async with self.sem:
                    try:
                        resp = await self.client.chat.completions.create(
                            **kwargs, extra_body=extra
                        )
                    except Exception as e:  # endpoint rejected extra_body
                        if "chat_template_kwargs" in str(e) or "extra" in str(e).lower():
                            resp = await self.client.chat.completions.create(**kwargs)
                        else:
                            raise
                return self._parse(resp, parse_action)
            except Exception as e:  # noqa: BLE001 - we want everything
                last_err = f"{type(e).__name__}: {e}"
                await asyncio.sleep(min(2 ** attempt, 20))
        return Completion(reasoning="", content="", action=None, error=last_err)

    @staticmethod
    def _parse(resp, parse_action: bool) -> Completion:
        choice = resp.choices[0]
        msg = choice.message
        reasoning = (getattr(msg, "reasoning_content", None) or "").strip()
        content = (msg.content or "").strip()

        if not reasoning:
            m = THINK_RE.search(content)
            if m:
                reasoning = m.group(1).strip()
                content = (content[: m.start()] + content[m.end():]).strip()

        action = None
        if parse_action:
            m = ACTION_RE.search(content)
            if m:
                action = m.group(1).lower()

        usage = {}
        if getattr(resp, "usage", None):
            usage = {
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
            }
        return Completion(
            reasoning=reasoning,
            content=content,
            action=action,
            raw_finish_reason=choice.finish_reason or "",
            usage=usage,
        )


# ---------------------------------------------------------------- utilities

def load_config(path: str = "config.yaml") -> dict:
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def append_jsonl(path: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def read_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


async def gather_with_progress(coros: list, label: str = "") -> list:
    """asyncio.gather with a one-line progress counter on stderr."""
    import sys
    total = len(coros)
    done = 0
    results: list = [None] * total

    async def _run(i, c):
        nonlocal done
        results[i] = await c
        done += 1
        if done % max(1, total // 50) == 0 or done == total:
            sys.stderr.write(f"\r  {label} {done}/{total}")
            sys.stderr.flush()

    await asyncio.gather(*[_run(i, c) for i, c in enumerate(coros)])
    import sys as _s
    _s.stderr.write("\n")
    return results
