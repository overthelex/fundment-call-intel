# Sales Call QA

Ask questions across the 20 OrbitFlow sales-call transcripts and get an answer you can check.
Every claim comes with a verbatim quote, the call, timestamp, speaker, and a `file:line` link.
Each quote is then matched against the transcript in code, not taken on trust.

```
$ uv run callqa ask "What did Acme Corp say about their current workflow?"

Answer  (confidence: high)
Acme said its current workflow is fragmented across systems, with handoffs handled in spreadsheets
and Slack rather than a single workflow layer. ...

Evidence
  1. Their current workflow is spread across systems, and handoffs are managed through spreadsheets ...
    ✓ CALL-001 [01:51] Rachel Morgan (VP Revenue Operations, Acme Logistics): "All of that is managed through spreadsheets and Slack reminders."
       data/calls/call-001_acme_logistics.txt:31
  ...
Notes
  - 'Acme Corp' appears to refer to Acme Logistics in the catalogue.

[full: 1 calls, 4,999 words in context · 2 API calls · 9,266 in / 1,156 out tokens · 7.3s]
```

## Setup and run

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env        # then set LLM_API_KEY (an OpenAI key works as is)
uv run callqa index         # embeds the transcripts once (~343 chunks, cached in .cache/)
uv run callqa ask "Which competitors were mentioned, and in what context?"
uv run callqa ask "..." --mode full     # baseline: whole dataset in the prompt
uv run callqa ask "..." --json          # raw result, including the plan and every citation check
uv run callqa                           # interactive prompt
uv run pytest                           # offline unit tests (parser, chunking, citation checker)
```

The client speaks the OpenAI API. With a plain OpenAI key, set only `LLM_API_KEY`. For Azure AI Foundry
(what I ran on), also set `LLM_BASE_URL=https://<resource>.openai.azure.com/openai/v1/`; model names
are then deployment names. Defaults: `CHAT_MODEL=gpt-5.4-mini`, `JUDGE_MODEL=gpt-5.4`,
`EMBED_MODEL=text-embedding-3-small`.

## Evaluation

Details, the full results table and three worked examples: [`eval/EVALUATION.md`](eval/EVALUATION.md).

### Run it

```bash
uv run python eval/run_eval.py                    # pipeline, all 30 questions
uv run python eval/run_eval.py --mode full        # baseline: whole dataset in the prompt
uv run python eval/run_eval.py --only q11,q24     # a subset
uv run python eval/run_eval.py --regrade eval/results/<run>.json   # re-check and re-judge saved answers, no generation
uv run python eval/compare.py --auto A1.json A2.json A3.json --full F.json   # per-question comparison
```

Each run writes `eval/results/<timestamp>-<mode>.json` (every answer, plan, citation check and
verdict) and a `.md` summary. The judge defaults to `JUDGE_MODEL` on the same API, so an OpenAI key is
enough. The results below used Claude Opus as the judge (`JUDGE_BACKEND=claude-cli`, through a local
`claude` CLI), a different vendor from the answering model.

### What it measures and why

30 annotated questions (`eval/questions.yaml`) covering the cases the task warns about: single-call
lookups, cross-call themes, call-kind filters, name mismatches, ambiguous, unanswerable and near-miss
questions, and vendor contradictions. Each has its gold calls, required facts (core + details), bonus
facts, penalties, and whether the system should abstain.

The metrics are chosen to say *which step* failed, deterministic ones first:

- **context recall**: did routing/retrieval put the gold calls in front of the model? (code)
- **citation validity**: is each quote really in that call, said by that speaker? (code)
- **correct** yes / partly / no, **fact recall**, **penalties**: is the answer right and complete? (LLM judge)
- **abstention**: does it say "not in the data" exactly when it should? (LLM judge)
- **tokens and latency**, against a baseline that puts all 20 transcripts in the prompt

### Results

29 headline questions, `gpt-5.4-mini` answering, pipeline run 3 times, baseline once:

| | pipeline (`auto`) | whole dataset in prompt (`full`) |
|---|---|---|
| context recall | 1.00 in every run | 1.00 (by construction) |
| citation validity | 1.00 / 1.00 / 0.96 | 0.94 (6 quotes attached to the wrong call) |
| correct: yes / partly / no | 14 / 14 / 1 in every run | 8 / 20 / 1 |
| core fact recall | 0.62–0.65 | 0.58 |
| abstention: right on unanswerable / false on answerable | 5/5 · 0–1 of 24 | 5/5 · 0 of 24 |
| prompt tokens per question | ~13K | 122K |

What I take from it:

- **Retrieval is not the bottleneck**: every gold call reaches the model in every run. Misses happen
  in the answer step (long lists stop early) or in questions about *relationships between calls*.
- **The pipeline is no worse than the brute-force baseline at ~1/9 of the tokens, and its quotes are
  more reliable.** Not "better": re-judging the same answers with the same judge moved 6 of 30
  verdicts between yes and partly, and two judges (Claude, `gpt-5.4`) agree on 22 of 30. The
  deterministic metrics and the yes-vs-no line are stable; the yes/partly split is not.
- **Unanswerable and near-miss questions work** in all runs (Kestrel's ERP, ISO 27001, Enterprise price).
- **Known failures**: q11 ("has the vendor given inconsistent answers?") is wrong in every run: the two
  sides of each contradiction sit in different calls and similarity search does not find
  disagreement. q24 finds both sides of the SSO question but will not weigh them. q30 (bonus) needs a
  second retrieval hop.

The gold set was drafted by an LLM, every citation checked against the source, and the 19 disputed
points decided by a human (`eval/review/`). The judge itself is not yet calibrated against human
grades; the plan for that is in `eval/EVALUATION.md`.

## Known limitations

- **Questions about relationships between calls** (contradictions, "who else said X", two-step
  questions like q30) are the weak spot: retrieval finds passages similar to the question, not passages
  that disagree with each other.
- **Exhaustive lists**: "which customers mentioned X" can miss a call that mentions X once in passing
  if that excerpt ranks low, or if the answer stops early. The answer cannot say "this list is complete".
- **Judgement questions** ("most likely to buy") are only as good as one model's read of excerpts; the
  answer cites signals but there is no scoring rubric behind it.
- **The checker verifies that the quote exists and that the cited person said it, not that it supports
  the claim.** A real, correctly attributed quote attached to an overstated claim passes. The judge catches some of this in evaluation, but nothing does at runtime.
- **Header vs body disagreements** are only surfaced when the question touches them.
- **The gold set is small (30) and LLM-drafted** (see `eval/EVALUATION.md`). The judge is
  from a different vendor than the answering model, but it is still an LLM, it is noisy on the
  yes/partly boundary, and it has not been calibrated against human grades.
- Single-turn, English, no auth. The transcripts are sent to an external LLM API.

## With more time

With another day:

1. **Per-call structured notes at index time.** Run one extraction pass per call (cheap, cacheable,
   incremental): participants and roles, competitors, integrations, pricing reactions, objections,
   buying signals, outcome/next step, and **vendor claims by topic** (SSO, billing, pricing, no-code,
   services), each with a turn reference. Cross-call questions (q11, "which customers…", "what did
   successful cold calls have in common") then become queries over notes, not hoping similarity search
   surfaces every relevant turn. Contradictions become a group-by on `vendor_claims.topic`.
2. **A map step for "across" questions**: ask each candidate call "what does this call say about X?"
   in parallel (small model, ~20 calls), then synthesise. This trades tokens for recall on exhaustive
   lists, and gives an explicit "no mention" per call, which makes "this list is complete" a claim the
   system can back.
3. **A second retrieval hop**: let the answer step request more context ("need: the call where an
   engineer reviewed an exported definition") before answering; this fixes q30-type questions.
4. **Entailment check on citations**: a small model checks that each quote supports its claim, not just
   that it exists.
5. **Better eval**: a majority of 3 judge passes per answer (the judge alone moves ~6 of 30 verdicts),
   3–5 repeats of the baseline too, a blind human-graded subset to calibrate the judge, and separate
   retrieval-only tests that need no LLM.

For production:

- **Ingestion**: new calls arrive as events; parse → chunk → embed → extract notes per call,
  idempotent by call id + content hash (the embedding cache already works this way). A proper store
  (Postgres + pgvector or a vector DB) replaces in-memory numpy/BM25, with metadata filters (date,
  segment, rep, stage) in the query.
- **Scale**: at thousands of calls, the planner cannot see a catalogue in its prompt; it becomes a
  structured filter step over call metadata plus notes. Per-call quotas need a cap (top-N calls by
  relevance first). The full-context mode stops being an option.
- **Security and privacy**: transcripts hold customer PII and commercial terms. That means
  tenant/role-based access applied as a retrieval filter (a rep sees their own accounts, a manager
  their team's), a region-pinned LLM endpoint with no training on data and zero/limited retention,
  PII redaction where the use case allows, audit logs of questions and the turns they surfaced, and
  prompt-injection hygiene (transcripts are untrusted input: a customer can say "ignore previous
  instructions" on a call).
- **Operations**: run the eval in CI on prompt/model changes, log every question with its plan,
  context and citation checks, collect user feedback (thumbs down + "wrong citation"), and watch
  citation validity and abstention rate as live quality signals.
- **Cost/latency**: cache the planner output and embeddings; route simple single-call questions to a
  smaller model; stream the answer.
