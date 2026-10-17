"""Thin wrapper over an OpenAI-compatible endpoint (OpenAI or Azure AI Foundry).

Configuration comes from the environment (or `.env`):
  LLM_API_KEY / OPENAI_API_KEY   API key
  LLM_BASE_URL                   optional, e.g. https://<resource>.openai.azure.com/openai/v1/
  CHAT_MODEL                     model used for planning and answering
  JUDGE_MODEL                    model used by the evaluator
  EMBED_MODEL                    embedding model
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from typing import TypeVar

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

T = TypeVar("T", bound=BaseModel)


@dataclass
class Usage:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    embed_tokens: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add(self, prompt: int = 0, completion: int = 0, embed: int = 0) -> None:
        with self._lock:
            self.calls += 1
            self.prompt_tokens += prompt
            self.completion_tokens += completion
            self.embed_tokens += embed

    def snapshot(self) -> dict:
        return {
            "calls": self.calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "embed_tokens": self.embed_tokens,
        }


class LLM:
    def __init__(self) -> None:
        api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise SystemExit("Set LLM_API_KEY (or OPENAI_API_KEY); see README.")
        self.client = OpenAI(api_key=api_key, base_url=os.environ.get("LLM_BASE_URL") or None)
        self.chat_model = os.environ.get("CHAT_MODEL", "gpt-5.4-mini")
        self.judge_model = os.environ.get("JUDGE_MODEL", "gpt-5.4")
        self.embed_model = os.environ.get("EMBED_MODEL", "text-embedding-3-small")
        self.usage = Usage()

    def structured(
        self,
        system: str,
        user: str,
        schema: type[T],
        model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> T:
        """One chat call whose output is validated against a pydantic schema."""
        kwargs = {}
        if reasoning_effort:
            kwargs["reasoning_effort"] = reasoning_effort
        resp = self.client.chat.completions.parse(
            model=model or self.chat_model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format=schema,
            **kwargs,
        )
        if resp.usage:
            self.usage.add(resp.usage.prompt_tokens, resp.usage.completion_tokens)
        msg = resp.choices[0].message
        if msg.parsed is None:
            raise RuntimeError(f"model returned no parseable output (refusal={msg.refusal!r})")
        return msg.parsed

    def embed(self, texts: list[str], batch_size: int = 128) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            resp = self.client.embeddings.create(model=self.embed_model, input=texts[i : i + batch_size])
            self.usage.add(embed=resp.usage.total_tokens)
            out.extend(d.embedding for d in resp.data)
        return out
