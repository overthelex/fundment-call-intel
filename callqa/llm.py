"""Thin wrapper over an OpenAI-compatible endpoint (OpenAI or Azure AI Foundry).

Configuration comes from the environment (or `.env`):
  LLM_API_KEY / OPENAI_API_KEY   API key
  LLM_BASE_URL                   optional, e.g. https://<resource>.openai.azure.com/openai/v1/
  CHAT_MODEL                     model used for planning and answering
  EMBED_MODEL                    embedding model
"""

from __future__ import annotations

import os
import ssl
import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from typing import TypeVar

import certifi
from dotenv import load_dotenv
from openai import DefaultHttpx2Client, OpenAI
from pydantic import BaseModel

load_dotenv()

T = TypeVar("T", bound=BaseModel)


@dataclass
class Usage:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    embed_tokens: int = 0
    cached_tokens: int = 0  # prompt tokens served from the provider's prefix cache (billed at a discount)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add(self, prompt: int = 0, completion: int = 0, embed: int = 0, cached: int = 0) -> None:
        with self._lock:
            self.calls += 1
            self.prompt_tokens += prompt
            self.completion_tokens += completion
            self.embed_tokens += embed
            self.cached_tokens += cached

    def snapshot(self) -> dict:
        return {
            "calls": self.calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "embed_tokens": self.embed_tokens,
            "cached_tokens": self.cached_tokens,
        }


# A call made while someone waits for an answer finishes in well under a minute; one that hangs at the
# provider is cut off and retried instead of holding the answer (or the whole eval) for minutes.
QUESTION_TIMEOUT = 120
# Ingestion reads each call in parts of ~1,700 words (store.py): a part finishes in 5-100 s.
INGEST_TIMEOUT = 180
# About 4% of requests are accepted by the provider and never answered: no headers, no error, until the
# client's read timeout (measured on Azure, 24.10: 24 of ~550 requests in four ingestions; also 4 of 120
# requests sent at once from separate clients). Each one held ingestion for a full timeout, twice when
# the retry was lost too. A request with no answer after `hedge_after` seconds, longer than almost every
# normal one (p90 42 s, p99 86 s), gets a duplicate, and the first answer wins.
# An embedding request answers in under 2 s; one whose response body never arrived held ingestion for
# the full question timeout (120 s), so it gets a short one and is retried.
EMBED_TIMEOUT = 20
INGEST_HEDGE_AFTER = 60  # p90 of ingestion requests 42 s, p99 86 s
# Question-time calls at low reasoning: the answer step's p99 is 21 s and its maximum 28 s (101 answers);
# a lost request otherwise holds the question for the full 120 s timeout (one took 135 s instead of 12).
QUESTION_HEDGE_AFTER = 45
_hedges = ThreadPoolExecutor(512, thread_name_prefix="hedge")


class LLM:
    def __init__(self) -> None:
        api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise SystemExit("Set LLM_API_KEY (or OPENAI_API_KEY); see README.")
        # A plain ssl context, not the HTTP client's default (truststore 0.10): truststore holds one lock
        # per context for a whole TLS handshake, network round trips included, so the ~180 connections
        # ingestion opens at once shook hands one at a time. Connections queued for ~10 s were closed by
        # the server (SSLEOFError), and one stalled handshake held every other thread, for up to 13 min.
        tls = ssl.create_default_context(cafile=certifi.where())
        self.client = OpenAI(
            api_key=api_key, base_url=os.environ.get("LLM_BASE_URL") or None, max_retries=8, timeout=QUESTION_TIMEOUT,
            http_client=DefaultHttpx2Client(verify=tls),
        )
        self.chat_model = os.environ.get("CHAT_MODEL", "gpt-5.4-mini")
        self.embed_model = os.environ.get("EMBED_MODEL", "text-embedding-3-small")
        self.usage = Usage()

    def structured(
        self,
        system: str,
        user: str,
        schema: type[T],
        model: str | None = None,
        reasoning_effort: str | None = None,
        usage: Usage | None = None,
        timeout: float | None = None,
        hedge_after: float | None = None,
    ) -> T:
        """One chat call whose output is validated against a pydantic schema.

        With `hedge_after`, a duplicate is sent if the first request has not answered by then; the first
        answer is returned (both count in usage if both complete)."""
        def once() -> T:
            return self._structured(system, user, schema, model, reasoning_effort, usage, timeout)

        if not hedge_after:
            return once()
        first = _hedges.submit(once)
        try:
            return first.result(timeout=hedge_after)
        except FutureTimeout:
            pending = {first, _hedges.submit(once)}
        while True:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for f in done:
                if f.exception() is None or not pending:
                    return f.result()  # the first success, or the last failure

    def _structured(self, system, user, schema, model, reasoning_effort, usage, timeout):
        kwargs = {}
        if reasoning_effort:
            kwargs["reasoning_effort"] = reasoning_effort
        client = self.client.with_options(timeout=timeout) if timeout else self.client
        resp = client.chat.completions.parse(
            model=model or self.chat_model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format=schema,
            **kwargs,
        )
        if resp.usage:
            for u in (self.usage, usage):
                if u is not None:
                    details = getattr(resp.usage, "prompt_tokens_details", None)
                    u.add(resp.usage.prompt_tokens, resp.usage.completion_tokens,
                          cached=getattr(details, "cached_tokens", 0) or 0)
        msg = resp.choices[0].message
        if msg.parsed is None:
            raise RuntimeError(f"model returned no parseable output (refusal={msg.refusal!r})")
        return msg.parsed

    def embed(self, texts: list[str], batch_size: int = 128, usage: Usage | None = None) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            resp = self.client.with_options(timeout=EMBED_TIMEOUT).embeddings.create(
                model=self.embed_model, input=texts[i : i + batch_size])
            for u in (self.usage, usage):
                if u is not None:
                    u.add(embed=resp.usage.total_tokens)
            out.extend(d.embedding for d in resp.data)
        return out
