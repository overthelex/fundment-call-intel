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

`eval/questions.yaml` has 30 annotated questions: single-call lookups, cross-call themes, call-kind
filters, name mismatches, ambiguous questions, unanswerable and near-miss questions, and vendor
contradictions. Each has the gold calls, the evidence locations (call + timestamp) and whether the
system should abstain, plus a rubric for the judge:

- **required facts**, each split into a *core* claim and supporting *details*; for enumerations
  ("which companies…") covering k of n details counts as full coverage;
- **bonus facts**, credited when present but never required;
- **penalties**, statements a correct answer must not make (e.g. attributing a customer's figure to
  the vendor, or naming SAP as Kestrel's ERP).

One question (q30, a two-step inference) is marked as a bonus and kept out of the headline numbers.
`eval/GOLD_NOTES.md` lists the dataset's traps found while annotating.

| metric | what it tells you | how |
|---|---|---|
| context recall | did retrieval/routing put the right calls in front of the model? | gold calls ∩ context calls |
| cited recall | did the answer actually use them? | gold calls ∩ calls with a verified citation |
| citation validity | are the quotes real and correctly attributed? | code check against the transcript |
| correct (yes / partly / no) | is the main point right? | LLM judge against the rubric |
| core / atomic fact recall | how complete is it? | LLM judge, per core and per detail |
| penalties | did it make a statement the gold set rules out? | LLM judge |
| abstention | does it say "not in the data" when, and only when, it should? | LLM judge (`declines`) |
| tokens, latency | what does it cost? | API usage per question |

The metrics separate the failure points. Low context recall means retrieval or routing failed. High
context recall with low cited recall means the answer step ignored evidence. Low citation validity
means invented or misattributed quotes. Low fact recall with good citations means the answer is
incomplete despite good sources.

### Results

`gpt-5.4-mini` answering. The judge is Claude Opus (a different vendor from the answering model, see
Setup). The pipeline was run three times with identical code and the full-context baseline once; all
four sets of answers were then re-checked and re-judged against the reviewed gold set without
regenerating them (`--regrade`). Files in `eval/results/`: `*-auto.*` / `*-full.*` are the original
runs, `*-regraded.*` the numbers below, `comparison.md` the per-question comparison.

Headline over 29 questions (q30 excluded):

| | pipeline (`auto`), 3 runs | whole dataset in prompt (`full`), 1 run |
|---|---|---|
| context recall | 1.00 / 1.00 / 1.00 | 1.00 (by construction) |
| cited recall | 0.91 / 0.91 / 0.89 | 0.90 |
| citation validity | **1.00 / 1.00 / 0.96** | 0.94 |
| failed citations: not found · wrong call · wrong speaker | 1·0·0 / 0·0·0 / 1·2·3 | 3·6·1 |
| answer correct: yes / partly / no | 14/14/1 in each run | 8 / 20 / 1 |
| core fact recall | 0.62 / 0.65 / 0.62 | 0.58 |
| atomic fact recall (cores + details) | 0.51 / 0.51 / 0.48 | 0.48 |
| compound fact recall (old scoring) | 0.42 / 0.46 / 0.44 | 0.42 |
| penalties hit | 0 / 0 / 0 | 0 |
| correct abstention on unanswerable | 5/5 in every run | 5 / 5 |
| false abstention on answerable | 1 / 0 / 1 (of 24) | 0 / 24 |
| prompt tokens / question | **~13K** | 122K |
| latency / question | 13-14 s | 13 s |

**How reliable is the judge?** Before reading the table: re-judging the *same* answers of one run
with the same Claude judge moved 6 of 30 verdicts, all between yes and partly (14/14/1 became
8/20/1). Claude and `gpt-5.4` agree on 22 of 30 for the same answers. So the yes/partly boundary is
noise of about ±6 questions, and the identical 14/14/1 in the three runs is partly luck. The
yes-vs-no line, the abstentions and the deterministic metrics are stable. Repeating the judge and
taking the majority would cut this noise; the judge has not been calibrated against human grades
(see below).

How I read the numbers:

- **Routing and retrieval are not the bottleneck.** Every gold call reaches the model in every run.
  Where cited recall drops (q02 Salesforce, q05 capabilities), the calls were in context but the answer
  stopped after a few examples.
- **The pipeline is at least as good as the brute-force baseline at ~1/9 of the input tokens.** The
  baseline was generated once and its own noise is not measured; the gap in "yes" (14 vs 8) is within
  the judge noise above, so the honest claim is "no worse", not "better". Per question
  (`comparison.md`) the baseline is ahead on the two hardest cross-call questions, q11 and q30, where
  it sees everything, and behind on q21, where it took Oakhill's figure for Verity's.
- **Quotes are more reliable with less context**: 0.96-1.00 citation validity for the pipeline vs 0.94
  for the baseline, and the baseline's failures are mostly *wrong call* (6): real quotes attached to the
  wrong customer. In q21 ("How much was Verity paying?") it supported its answer with Oakhill's
  "twenty-one and a half thousand a year", labelled as CALL-014. Wrong-call and not-found are reported
  separately because they are different failures (attribution vs invention); both count as errors.
- **The checker catches real errors, not only typos**: an invented quote, vendor words credited to the
  customer, one speaker's words credited to a colleague, the right quote in the wrong call. Each is
  shown to the user as ✗, with a pointer to where the words actually are when they exist elsewhere.
- **Unanswerable and near-miss questions work** in all runs, e.g. "Which ERP does Kestrel use?" (they
  decline to say), ISO 27001 (only SOC 2 is mentioned), and an Enterprise price (always "custom").
- **Completeness depends on how you count.** Scoring each multi-part fact as one item with partial
  credit (the original scoring) gives 0.42-0.46; counting atoms gives about 0.5; counting only the core
  claims gives about 0.62. The answers usually get the points and drop supporting detail.

Where it fails (all visible in the per-question tables):

- **q11 "Has anyone from the vendor given inconsistent answers?"**: wrong in every pipeline run; it
  concludes that no clear product contradiction exists. The contradictions (a rep saying SSO is on all
  plans vs. Enterprise-only elsewhere; "completely no-code" vs. "we don't claim every workflow is
  no-code") sit in single turns of different calls. Retrieval by question similarity does not find
  "statements that disagree". The baseline partly finds them.
- **q24 "Is SSO on Growth?"**: the pipeline finds both sides but says it cannot conclude, although eight
  statements say Enterprise-only against one hesitant rep who backs off. That is false balance and is
  graded partly (not as a decline).
- **q30 (bonus, two-step: "which prospect did Maya mean?")**: needs the Verity call to set up the
  question and the Juniper call to answer it. The planner routes to Verity only, so the pipeline
  declines; the baseline answers it.
- **Long cross-call lists (q02, q05)**: the right calls are in context, but the answer stops early.

What changed because of the eval (in order): the judge got partial credit and a separate `correct`
verdict; the planner stopped narrowing product questions to "prospect" calls (that cut out the renewal
call holding the SSO answer); calls not named in the question each get one excerpt even for narrow
questions; figures that differ across statements must go into `conflicts`; header metadata became
citable; abstention scoring moved from a heuristic to the judge; and after an audit of the results,
the checker started verifying the speaker and the call, because one run credited Sarah's words to Maya.

**Where the gold set comes from.** The questions and facts were drafted by an LLM agent that read all
20 transcripts. Every cited line was then checked against the source and every "not in the data" was
checked with grep. The disputed interpretations (19 points) were reviewed by a second model (Claude),
and a human decided each one; the decisions are in `eval/review/reviews_2026-10-19.json`. They changed
the rubric, not the system: three apparent conflicts (Verity's "hundred thousand", "you weren't there
in February", Greenline's "two and a half thousand") turned out to be readings of normal speech and
became bonus facts or penalties; q11 now requires the two product contradictions and treats commercial
concessions as optional; q07 is graded by tiers, not order; facts were split into core and details.
The choice of what counts as the main point in the undisputed questions has not been reviewed by a
human. That review is not a calibration of the judge: the planned calibration is 10 answers, stratified
by verdict and question type, graded blind by a human, with the raw agreement rate and every
disagreement explained.

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
- **The gold set is small (30) and LLM-drafted** (see "Where the gold set comes from"). The judge is
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
