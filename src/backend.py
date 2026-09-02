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
        actions: tuple = (),
        debug_raw: bool = False,
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
                if debug_raw:
                    import json as _json
                    try:
                        print("\n--- RAW RESPONSE ---")
                        print(_json.dumps(resp.model_dump(), indent=2)[:4000])
                        print("--- END RAW ---\n")
                    except Exception as _e:
                        print("raw dump failed:", _e)
                return self._parse(resp, parse_action, actions)
            except Exception as e:  # noqa: BLE001 - we want everything
                last_err = f"{type(e).__name__}: {e}"
                await asyncio.sleep(min(2 ** attempt, 20))
        return Completion(reasoning="", content="", action=None, error=last_err)

    @staticmethod
    def _reasoning_of(msg) -> str:
        """vLLM puts the CoT in `reasoning_content`. Depending on SDK version it
        lands as an attribute, in model_extra, or only in the raw dict. Try all
        of them rather than trusting one."""
        candidates = []
        for name in ("reasoning_content", "reasoning"):
            candidates.append(getattr(msg, name, None))
        extra = getattr(msg, "model_extra", None)
        if isinstance(extra, dict):
            candidates += [extra.get("reasoning_content"), extra.get("reasoning")]
        dump = None
        try:
            dump = msg.model_dump()
        except Exception:
            dump = getattr(msg, "__dict__", None)
        if isinstance(dump, dict):
            candidates += [dump.get("reasoning_content"), dump.get("reasoning")]
        for c in candidates:
            if isinstance(c, str) and c.strip():
                return c.strip()
        return ""

    @staticmethod
    def _parse(resp, parse_action: bool, actions: tuple = ()) -> Completion:
        choice = resp.choices[0]
        msg = choice.message
        reasoning = Backend._reasoning_of(msg)
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
            elif actions:
                # fallback: the model named an action without the tag
                tail = content[-400:].lower()
                hits = [a for a in actions if a.lower() in tail]
                if len(hits) == 1:
                    action = hits[0]

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
