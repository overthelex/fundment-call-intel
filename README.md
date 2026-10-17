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

### Evaluation

```bash
uv run python eval/run_eval.py               # the system as shipped
uv run python eval/run_eval.py --mode full   # baseline: all transcripts in context
uv run python eval/run_eval.py --only q01,q05
```

Results are written to `eval/results/<timestamp>-<mode>.{md,json}`. One run of 30 questions uses about
0.4M prompt tokens in `auto` mode and 3.7M in `full` mode (judge included). The JSON holds every answer,
citation check and judge verdict, for manual review.

## Approach

```
question
  │
  ├─ 1. plan (LLM, structured)      which calls? (named companies, call kinds) · specific vs across · search queries
  │                                 · name mismatches ("Acme Corp" → Acme Logistics, flagged)
  ├─ 2. context                     candidate calls fit in 12K words? → send whole transcripts
  │                                 otherwise → hybrid retrieval (BM25 + embeddings, RRF) with a per-call quota
  ├─ 3. answer (LLM, structured)    summary · claims[] each with verbatim quotes · conflicts[] · not_found[]
  │                                 · confidence (high / medium / low / insufficient) + reason
  └─ 4. verify (code)               each quote looked up in the parsed transcript → exact / shifted / fuzzy / not found
                                    unverifiable claims flagged; if none verify, confidence is lowered
```

- **Parsing** (`callqa/parse.py`): header + `[MM:SS] Speaker: text` turns; each turn keeps its file
  line number and its side (vendor / customer, taken from the participant list). The call kind
  (prospect / renewal / churn / cold call) is derived from `STAGE`, because the manifest's `call_type`
  only separates prospects from existing customers.
- **Chunks** (`callqa/index.py`): windows of consecutive turns (~180 words, 2-turn overlap) within one
  call, each with a header naming the call, company, and kind. People talk in fragments, so a window keeps a
  question with its answer.
- **Retrieval**: BM25 catches exact names (Salesforce, Workato, SOC 2); embeddings catch paraphrase
  ("we're nervous about the price" ≈ pricing concern). The two are merged with reciprocal-rank fusion
  over the original question plus the planner's rewrites. For questions about the whole dataset, every
  candidate call also gets its best 2 chunks. Without that quota, long calls crowd short ones out of the
  top-k.
- **Answering** (`callqa/prompts.py`): the model sees whose side each speaker is on. It is told that a
  vendor's product statement is a claim, not a fact. It is told to report contradictions instead of
  picking one side. When it only saw excerpts, it must say "not found in the retrieved excerpts", not
  "never said".

## Key decisions

1. **Whole calls when they fit, retrieval when they don't.** One call is at most ~5K words, and all 20
   are ~51K words. If the question names a company or a call kind (cold calls are ~4K words in total;
   renewals ~7.5K), chunking only loses context. So those questions get whole transcripts. Retrieval is
   used when the candidate set is large (all prospects, the whole dataset). The 12K-word budget is one
   constant (`FULL_TEXT_WORD_BUDGET`).
2. **Structured output and a verifier in code, not "please cite your sources".** Citations are data
   (call, timestamp, speaker, quote), so they can be checked. The checker allows small timestamp
   slips (`shifted`) and punctuation and casing differences, but rejects invented quotes. That gives an
   objective grounding metric for the eval and a live warning for the user.
3. **The planner sees a catalogue, not the data.** 20 lines of call metadata are enough to resolve
   "Acme Corp", "customers who left" (= churn) or "renewals vs new business" to the right calls. A
   question about something absent from the catalogue (an unknown company) is flagged up front.
4. **Confidence is part of the answer contract.** `insufficient` is an expected output, not a failure.
   The verifier can lower confidence but never raise it.
5. **The baseline is in the code (`--mode full`).** At this dataset size, the whole corpus fits in one
   prompt. The eval compares the pipeline with that brute-force option, so retrieval has to earn its
   place in quality, cost and latency. It is not assumed to help.
6. **One OpenAI-compatible client.** It runs on OpenAI or Azure by changing env vars; no framework.

## Assumptions

- Transcripts are the source of truth; the manifest/header is metadata and can be wrong. Speaker
  attribution is correct (stated in the dataset README), so the speaker's side comes from the participant list.
- Users are sales managers. They want a short answer plus the quotes to check it, more than a long essay.
- English only, a few dozen calls, questions one at a time (no chat history).

## Evaluation

`eval/questions.yaml` has 30 annotated questions, each with gold calls, gold facts, the evidence
location (call + timestamp), and whether the system should abstain. `eval/GOLD_NOTES.md` lists the
dataset's traps found while annotating (contradictions, header-vs-body mismatches, name collisions). They cover single-call lookups, cross-call themes,
call-kind filters, name mismatch, unanswerable and near-miss questions, and contradictions. Each
question is scored on:

| metric | what it tells you | how |
|---|---|---|
| context recall | did retrieval/routing put the right calls in front of the model? | gold calls ∩ context calls |
| cited recall | did the answer actually use them? | gold calls ∩ calls with a verified citation |
| citation validity | are the quotes real? | code check against the transcript |
| fact recall | is the answer right and complete? | LLM judge (a stronger model than the answerer) per gold fact |
| abstention | does it say "not in the data" when, and only when, it should? | confidence = insufficient or no claims |
| tokens, latency | what does it cost? | API usage per question |

The metrics separate the failure points. Low context recall means retrieval or routing failed. High
context recall with low cited recall means the answer step ignored evidence. Low citation validity
means hallucinated quotes. Low fact recall with good citations means the answer is wrong or incomplete
despite good sources.

### Results

30 questions, `gpt-5.4-mini` answering, `gpt-5.4` judging. The final runs are
`eval/results/20261017-153225-auto.*` (the pipeline) and `eval/results/20261017-153737-full.*` (all 20
transcripts in one prompt).

| | pipeline (`auto`) | whole dataset in prompt (`full`) |
|---|---|---|
| context recall | 0.98 | 1.00 (by construction) |
| cited recall | 0.84 | 0.90 |
| citation validity | **1.00** | 0.98 |
| answer correct: yes / partly / no | 8 / 21 / 1 | 8 / 22 / 0 |
| fact recall (completeness) | 0.42 | 0.46 |
| correct abstention on unanswerable | 5 / 5 | 5 / 5 |
| false abstention on answerable | 2 / 25 | 1 / 25 |
| prompt tokens / question | **13K** | 122K |
| latency / question | 11 s | 14 s |

How I read the numbers:

- **Routing and retrieval are good, not the bottleneck.** 98% of gold calls reach the model. Where cited
  recall drops (q02 Salesforce, q05 capabilities), the calls were in context but the answer stopped
  after a few examples.
- **The pipeline matches the brute-force baseline on quality at ~1/9 of the input tokens.** At 20 calls
  the baseline is a reasonable product. At 2,000 it no longer fits, which is why the pipeline exists.
- **Grounding holds.** Every quote in the final pipeline run was found in the transcripts. Earlier runs
  caught a real fabricated quote (q03, an invented "twenty-one thousand vs Zapier for two thousand"
  line) and two checker gaps (header metadata, "Name (Role)" speakers), which are fixed now.
- **Unanswerable and near-miss questions work** in both modes, e.g. "Which ERP does Kestrel use?"
  (they decline to say), ISO 27001 (only SOC 2 is mentioned), and an Enterprise price (always "custom").
- **"Partly" dominates for a mundane reason.** The gold facts are deliberately detailed, and answers
  stay short. The judge's `correct` verdict ("is the main point right?") separates *wrong* from
  *incomplete*. Only one answer is wrong.
- **Run-to-run noise is about ±2 questions.** Across four full runs, the "yes" count ranged from 6 to 8
  with no code change, so differences that small are not signal. With 30 questions, this eval catches
  regressions, not fine-grained improvements.

Where it fails (all visible in the per-question table):

- **q11 "Has anyone from the vendor given inconsistent answers?"**: the hardest question, and the
  pipeline answers it wrongly. The contradictions (a rep saying SSO is on all plans vs. Enterprise-only
  elsewhere, a "non-negotiable" 7% uplift waived for another customer) sit in single turns of different
  calls. Retrieval by question similarity does not find "statements that disagree". The full-context
  baseline only partly finds them.
- **q30 (two-step: "which prospect did Maya mean?")**: needs the Verity call to set up the question and
  the Juniper call to answer it. The planner routes to Verity only, so the model guesses within that
  call. The baseline gets it right because it sees everything.
- **Long cross-call lists (q02, q05)**: the right calls are in context, but the answer stops early.

What changed because of the eval (in order): the judge got partial credit and a separate `correct`
verdict (all-or-nothing scoring of multi-part facts made every answer look bad); the planner stopped
narrowing product questions to "prospect" calls (that cut out the renewal call holding the SSO answer);
calls not named in the question each get one excerpt even for narrow questions; figures that differ
across statements must go into `conflicts` (q21: £80K vs "a hundred thousand a year"); and header
metadata became citable. Abstention scoring moved from a heuristic to the judge, after the heuristic
penalised a correct, confident "they declined to name it".

## Known limitations

- **Questions about relationships between calls** (contradictions, "who else said X", two-step
  questions like q30) are the weak spot: retrieval finds passages similar to the question, not passages
  that disagree with each other.
- **Exhaustive lists**: "which customers mentioned X" can miss a call that mentions X once in passing
  if that excerpt ranks low, or if the answer stops early. The answer cannot say "this list is complete".
- **Judgement questions** ("most likely to buy") are only as good as one model's read of excerpts; the
  answer cites signals but there is no scoring rubric behind it.
- **The checker verifies that a quote exists, not that it supports the claim.** A real quote attached to
  an overstated claim passes. The judge catches some of this in evaluation, but nothing does at runtime.
- **Header vs body disagreements** (e.g. Greenline: 2,300 employees in the header, "two and a half
  thousand" in the call) are only surfaced when the question touches them.
- **The gold set is small (30) and written by one annotator** (an LLM agent reading all transcripts,
  spot-checked by me). The LLM judge is a different, stronger model, but it is still an LLM. Its
  verdicts were spot-checked, not calibrated against human grades.
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
5. **Better eval**: atomic gold facts (split the multi-part ones), 3–5 repeats per question to measure
   variance, a human-graded subset to calibrate the judge, and separate retrieval-only tests that need
   no LLM.

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
