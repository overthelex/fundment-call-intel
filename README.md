# Sales Call QA

Ask questions across the 20 OrbitFlow sales-call transcripts and get an answer you can check.
Every claim comes with a verbatim quote, the call, timestamp, speaker, and a `file:line` link.
Each quote is then matched against the transcript in code, not taken on trust.

```
$ uv run callqa ask "What did Acme Corp say about their current workflow?"

Answer  (confidence: high)
Taking "Acme Corp" to mean Acme Logistics, they said their current workflow is spread across systems:
sales, onboarding and customer success handoffs are managed through spreadsheets and Slack reminders ...

Notes on names
  - "Acme Corp" appears to refer to Acme Logistics in CALL-001.

Evidence
  1. Their current workflow is spread across systems, and handoffs are managed through spreadsheets ...
    ✓ CALL-001 [01:51] Rachel Morgan (VP Revenue Operations, Acme Logistics): "All of that is managed through spreadsheets and Slack reminders."
       data/calls/call-001_acme_logistics.txt:31
  ...

[full: 1 calls, 4,999 words in context · 2 API calls · 9,266 in / 1,156 out tokens · 7.3s]
```

## Setup and run

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env        # then set LLM_API_KEY (an OpenAI key works as is)
uv run callqa index         # once: embeds the transcripts and extracts vendor claims (~4 min, cached in .cache/)
uv run callqa ask "Which competitors were mentioned, and in what context?"
uv run callqa ask "..." --mode full     # baseline: whole dataset in the prompt
uv run callqa ask "..." --json          # raw result, including the plan and every citation check
uv run callqa                           # interactive prompt
uv run pytest                           # offline unit tests (parser, chunking, citation checker)
```

The client speaks the OpenAI API. With a plain OpenAI key, set only `LLM_API_KEY`. For Azure AI Foundry
(what I ran on), also set `LLM_BASE_URL=https://<resource>.openai.azure.com/openai/v1/`; model names
are then deployment names. Defaults: `CHAT_MODEL=gpt-5.4-mini`, `EMBED_MODEL=text-embedding-3-small`.

## Approach

```
question
  │
  ├─ 1. plan (LLM, structured)      which calls? (named companies, call kinds) · specific vs across · search queries
  │                                 · name mismatches ("Acme Corp" → Acme Logistics, flagged)
  │                                 · ambiguous first names, checked in code ("Priya": who speaks, who is only mentioned)
  │                                 · does it ask whether the vendor contradicts itself?
  │                                 · is it about a product fact? which of 12 topics?
  ├─ 2. context                     vendor-consistency question? → every vendor claim, grouped by topic
  │                                 candidate calls fit in 12K words? → send whole transcripts
  │                                 question across calls, ≤25 candidates? → map step: each call read in full
  │                                   by a cheap pass, relevant turns kept (+ retrieved excerpts)
  │                                 otherwise → hybrid retrieval (BM25 + embeddings, RRF) with a per-call quota
  │                                 product fact? → plus every vendor statement on that topic, from all calls
  ├─ 3. answer (LLM, structured)    first an inventory of every relevant turn, then the answer from it:
  │                                 summary · claims[] each with verbatim quotes · conflicts[] · not_found[]
  │                                 · each conflict weighed: better-supported side + why, or "cannot tell"
  │                                 · confidence (high / medium / low / insufficient) + reason
  └─ 4. verify (code)               each quote looked up in the parsed transcript → exact / shifted / fuzzy
                                    / wrong speaker / wrong call / not found
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
- **Vendor claims** (`callqa/claims.py`): at index time, one extraction pass per call lists what
  OrbitFlow staff assert about the product (plans, SSO, pricing, no-code, limits, support…) under 12
  fixed topics, each with a verbatim quote. Every quote is run through the citation checker and kept
  only if it verifies and was said by vendor staff (587 claims). Cached per call content. Used whole
  for consistency questions, and by topic for product-fact questions ("Is SSO on Growth?").
- **Answering** (`callqa/prompts.py`): the model sees whose side each speaker is on. It is told that a
  vendor's product statement is a claim, not a fact. It is told to report contradictions instead of
  picking one side silently, and then to weigh them on fixed criteria: how many people say each side,
  how specific each is, whether its speaker later hedged or corrected it, who said it, and recency. When it only saw excerpts, it must say "not found in the retrieved excerpts", not
  "never said".

## Key decisions

1. **Whole calls when they fit, retrieval when they don't.** One call is at most ~5K words, and all 20
   are ~51K words. If the question names a company or a call kind (cold calls are ~4K words in total;
   renewals ~7.5K), chunking only loses context. So those questions get whole transcripts. Retrieval is
   used when the candidate set is large (all prospects, the whole dataset). The 12K-word budget is one
   constant (`FULL_TEXT_WORD_BUDGET`).
2. **Structured output and a verifier in code, not "please cite your sources".** Citations are data
   (call, timestamp, speaker, quote), so they can be checked. The checker allows small timestamp
   slips (`shifted`) and punctuation and casing differences, but rejects invented quotes, words said
   by someone else (`wrong_speaker`) and quotes from another call (`wrong_call`, with a pointer to the
   real one). That gives an objective grounding metric for the eval and a live warning for the user.
3. **The planner sees a catalogue, not the data.** 20 lines of call metadata are enough to resolve
   "Acme Corp", "customers who left" (= churn) or "renewals vs new business" to the right calls. A
   question about something absent from the catalogue (an unknown company) is flagged up front.
   The catalogue lists only participants, so first names are also checked in code against every
   transcript (`callqa/names.py`): "Priya" is Priya Shah, the only Priya who speaks on a call, but a
   Priya Menon (Beacon) and a Priya at Juniper are mentioned. Both kinds of note are printed right
   under the answer, and the answer is told to open with the reading it chose.
4. **Confidence is part of the answer contract.** `insufficient` is an expected output, not a failure.
   The verifier can lower confidence but never raise it.
5. **The baseline is in the code (`--mode full`).** At this dataset size, the whole corpus fits in one
   prompt. The eval compares the pipeline with that brute-force option, so retrieval has to earn its
   place in quality, cost and latency. It is not assumed to help.
6. **Contradictions get their own context, not better retrieval.** "Has the vendor given inconsistent
   answers?" is about a relationship between two turns in different calls, and neither turn looks like
   the question, so similarity search cannot find it (the first version failed it in every run). Putting
   every vendor statement on a topic side by side makes a contradiction visible: "SSO is on all plans"
   (one AE) next to statements in nine other calls that SAML SSO is Enterprise. The planner switches to this
   context only for questions about the vendor's consistency.
   The same table answers product-fact questions: retrieval gives the passages most similar to the
   question, so a fact stated in nine calls and contradicted in one can reach the model as one statement
   against one, and it cannot weigh what it does not see. For a question on one to three product topics
   the answer step also gets every vendor statement on them. A conflict is then reported with both
   sides cited *and* with the better-supported side and the reason, or "cannot tell"; confidence stays
   at most medium.
7. **One OpenAI-compatible client.** It runs on OpenAI or Azure by changing env vars; no framework.

## Assumptions

- Transcripts are the source of truth; the manifest/header is metadata and can be wrong. Speaker
  attribution is correct (stated in the dataset README), so the speaker's side comes from the participant list.
- Users are sales managers. They want a short answer plus the quotes to check it, more than a long essay.
- English only, a few dozen calls, questions one at a time (no chat history).

## Evaluation

Details, the full results table and three worked examples: [`eval/EVALUATION.md`](eval/EVALUATION.md).

### Run it

```bash
uv run python eval/run_eval.py                    # pipeline, all 30 questions
uv run python eval/run_eval.py --mode full        # baseline: whole dataset in the prompt
uv run python eval/run_eval.py --only q11,q24     # a subset
uv run python eval/run_eval.py --regrade eval/results/<run>.json   # re-check and re-judge saved answers, no generation
uv run python eval/run_eval.py --no-judge         # deterministic metrics only, no Claude Code needed
uv run python eval/run_eval.py --replay eval/results/<run>.json --only q05   # new answer on the saved context
uv run python eval/compare.py --auto A1.json A2.json A3.json --full F.json   # per-question comparison
```

Each run writes `eval/results/<timestamp>-<mode>.json` (every answer, plan, the exact context the
answer step saw, citation checks and verdicts) and a `.md` summary that names the judge and labels
each failed question with the step that failed.

The judge is Claude Opus, a different vendor from the answering model, so it does not grade its own
blind spots. It runs through a local, logged-in [Claude Code](https://claude.com/claude-code)
(`claude -p`, tools disabled, structured output), so it needs `claude` on the PATH and no extra key.
Without it, `run_eval.py` stops before generating any answers; `--no-judge` still runs everything and
reports the metrics computed by code (context and cited recall, citation validity, tokens, latency),
marking the judged ones "not judged". The pipeline itself (`callqa ask`) needs only the OpenAI key.

### What it measures and why

30 annotated questions (`eval/questions.yaml`) covering the cases the task warns about: single-call
lookups, cross-call themes, call-kind filters, name mismatches, ambiguous, unanswerable and near-miss
questions, and vendor contradictions. Each has its gold calls, required facts (core + details), bonus
facts, penalties, and whether the system should abstain.

The metrics are chosen to say *which step* failed, deterministic ones first:

- **context recall**: did routing put the gold calls in front of the model? (code)
- **evidence recall**: did retrieval put the gold *turns* in front of the model? (code, from the
  timestamps in the gold evidence). Call-level recall alone is misleading: every candidate call gets
  at least one excerpt, so the call is "in context" even when the turn that answers is not.
- **citation validity**: is each quote really in that call, said by that speaker? (code)
- **correct** yes / partly / no, **fact recall**, **penalties**: is the answer right and complete? (LLM judge)
- **abstention**: does it say "not in the data" exactly when it should? (LLM judge)
- **tokens and latency**, against a baseline that puts all 20 transcripts in the prompt
- **first failed step** per question (code, from the above): retrieval, answer, attribution or abstention

### Results

29 headline questions, `gpt-5.4-mini` answering, pipeline run 3 times, baseline once. These runs
(17.10) predate the vendor-claims context, conflict weighing and name checks; the runs of the
current code are the paragraphs after the table.
Which file in `eval/results/` is which: [`eval/results/README.md`](eval/results/README.md).

| | pipeline (`auto`) | whole dataset in prompt (`full`) |
|---|---|---|
| context recall | 1.00 in every run | 1.00 (by construction) |
| citation validity | 1.00 / 1.00 / 0.96 | 0.94 (6 quotes attached to the wrong call) |
| correct: yes / partly / no | 14 / 14 / 1 in every run | 8 / 20 / 1 |
| core fact recall | 0.62–0.65 | 0.58 |
| abstention: right on unanswerable / false on answerable | 5/5 · 0–1 of 24 | 5/5 · 0 of 24 |
| prompt tokens per question | ~13K | 122K |

A fourth run from a fresh clone of this repo on 23.10, following this README
(`eval/results/20261023-120606-auto-fresh-clone.md`, 3 min): yes / partly / no 12 / 16 / 1, context
recall 1.00, one citation attached to the wrong call (caught by the checker), abstention 5/5 with no
false abstentions, ~13K prompt tokens, and the same failures (q11, q30).

**After adding the vendor-claims context (23.10)**, q11 is answered correctly: both contradictions
(SSO on all plans vs Enterprise-only, "completely no-code" vs "we don't claim every workflow is
no-code"), in 4 of 4 manual runs and in the eval run (`eval/results/20261023-122047-auto-vendor-claims.md`:
13 / 15 / 1 overall, citation validity 1.00, abstention 5/5). Only q11 is routed to the new context;
the one "no" in that run is q05, a long list that stopped early, which was "partly" before.

**After weighing conflicts (23.10)**, q24 ("Is SSO on Growth?") is answered correctly for the first
time: it reports the conflict, then says Enterprise-only is better supported because nine calls and
three reps say so, while the single "all plans" came from one AE who later said he was only "fairly
sure". Run `eval/results/20261023-204145-auto-weighing.md`: yes / partly / no **15 / 14 / 0**, citation
validity 1.00 with no failed citations, abstention 5/5 with no false abstentions, ~14.5K prompt tokens.
Within the judge noise band, but q11 and q24 are now both "yes".

**After the name checks (23.10)**, q06 ("Acme Corp") is "yes" for the first time: the answer opens
with "Taking Acme Corp to mean Acme Logistics", and the note sits under the answer, where the judge
now sees it too. For q16 ("Priya") the required mention of the other Priyas is now met by the note,
from code; the answer still leaves out that her figures were from memory, so it stays "partly". Run
`eval/results/20261023-210435-auto-names.md`: 14 / 14 / 1. The changes do not touch q05, q11 and
q29, which moved anyway: q05 is the long list that stops early, q11 found only the SSO contradiction
this time (both in the previous runs), and q29 was judged as not declining although it says
"no Enterprise list price, custom priced". That is the noise this eval measures: compare per question,
not the totals.

**With turn-level evidence recall (23.10)**, run `eval/results/20261023-214420-auto-diagnostics.md`:
14 / 15 / 0, abstention 5/5, citation validity 1.00. Context recall is 1.00 but evidence recall is
**0.82**, and it splits by context mode: **0.96** when whole calls are sent (15 questions) and **0.54**
when excerpts are retrieved (8 cross-call questions; q05 0.08, q01 0.32, q09 0.36, q04 0.41). First
failed step: answer 7, retrieval 6, attribution 1.

**With the map step and the turn inventory (23.10)**, run `eval/results/20261023-224354-auto-map.md`:
**20 / 9 / 0**, the first result clearly outside the judge noise band (14–15 "yes" before). Evidence
recall 0.94 (cross-call questions 0.89, was 0.54), core fact recall 0.81 (was 0.70), abstention 5/5.
The costs are real: mean prompt tokens 47K per question (was 14.5K; a mapped question reads every
candidate call, ~139K tokens, about the same as the whole-dataset baseline at 20 calls), mean latency
42 s under the eval's 4 parallel questions (mapped ones ~90 s), and 6 failed citations instead of 1
(three quotes from Ember's Noah Williams attached to other calls in mapped answers, three in whole-call
answers), all caught and marked ✗ by the checker. The inventory alone, replayed on the 7 questions that
failed in the answer step, raised core recall 0.64 → 0.69 and atomic 0.48 → 0.56 (two replays each),
without changing verdicts: the facts it still misses are context around a correct direct answer.
The map step is capped at 25 candidate calls; why it does not scale and what replaces it is in
*Scaling to thousands of calls*.

What I take from it:

- **Two different bottlenecks.** Questions about one or a few calls get whole transcripts, so
  everything reaches the model and the misses are in the answer step (details left out). Questions
  across all calls get retrieved excerpts, and there retrieval is the bottleneck: about half the
  supporting turns never reach the model. Earlier versions of this README said "retrieval is not the
  bottleneck", based on call-level recall only; turn-level recall showed that was wrong for
  cross-call questions. The map step closes most of that gap (0.54 → 0.89), at query-time cost.
- **The pipeline is no worse than the brute-force baseline at ~1/9 of the tokens, and its quotes are
  more reliable.** Not "better": re-judging the same answers with the same judge moved 6 of 30
  verdicts between yes and partly. The deterministic metrics and the yes-vs-no line are stable; the yes/partly split is not.
- **Unanswerable and near-miss questions work** in all runs (Kestrel's ERP, ISO 27001, Enterprise price).
- **Known failures**: q11 ("has the vendor given inconsistent answers?") was wrong in every run of the
  first version: the two sides of each contradiction sit in different calls and similarity search
  does not find disagreement. It is fixed by the vendor-claims context (above). q24 found both sides
  of the SSO question but would not weigh them; fixed by weighing (above). q30 (bonus) needs a second
  retrieval hop.

The gold set was drafted by an LLM, every citation checked against the source, and the 19 disputed
points decided by a human (`eval/review/`).

## Diagnosing a bad answer

Each step leaves a record, so a wrong answer can be traced to the step that failed:

1. **Plan**: `callqa ask "..." --json` → `plan`. Wrong `call_ids`, a call-kind filter the question did
   not ask for, a missed name (`entity_notes`), or product topics on a question about customers.
2. **Context**: `--json` → `context` holds the mode, the calls, and every turn and line of text the
   answer step saw. Is the turn that answers the question there? In the eval this is
   `evidence recall`, and `failure` says `retrieval (n evidence turns not in context)`.
3. **Answer**: if the evidence was in context but the answer misses it (`failure: answer`), re-run only
   the answer step on the same context: `run_eval.py --replay <run>.json --only q05`. If a prompt
   change fixes it on replay, it was the answer step; retrieval noise is out of the picture.
4. **Citations**: every quote shows ✓ / ✗ with the reason (`wrong_speaker`, `wrong_call` with where
   the words really are, `not found`); `failure: attribution`.
5. **Judge**: if the answer looks right, read `correct_reason` and the per-fact verdicts in the results
   JSON, and re-judge with `--regrade`. The judge moves about 6 of 30 verdicts between yes and partly.

## Known limitations

- **Questions about relationships between calls** are the weak spot. Vendor contradictions are
  handled by the claims table, but only for statements by OrbitFlow staff and only as well as the
  extraction pass caught them; "who else said X" and two-step questions like q30 still rely on
  retrieval, which finds passages similar to the question, not passages that relate to each other.
- **Exhaustive lists**: "which customers mentioned X" can miss a call that mentions X once in passing
  if that excerpt ranks low, or if the answer stops early. The answer cannot say "this list is complete".
- **Judgement questions** ("most likely to buy") are only as good as one model's read of excerpts; the
  answer cites signals but there is no scoring rubric behind it.
- **The checker verifies that the quote exists and that the cited person said it, not that it supports
  the claim.** A real, correctly attributed quote attached to an overstated claim passes. The judge catches some of this in evaluation, but nothing does at runtime.
- **Header vs body disagreements** are only surfaced when the question touches them.
- **The gold set is small (30) and LLM-drafted** (see `eval/EVALUATION.md`). The judge is
  from a different vendor than the answering model, but it is still an LLM and it is noisy on the
  yes/partly boundary.
- Single-turn, English, no auth. The transcripts are sent to an external LLM API.

## With more time

With another day:

1. **Per-call notes at index time instead of the map step.** The map step proves the point (evidence
   recall on cross-call questions 0.54 → 0.87) but pays for it on every question. Vendor claims are
   already extracted once per call; the same pass could list competitors, integrations, pricing
   reactions, objections, buying signals and the outcome, each with a turn reference. "Which
   customers…" then becomes a query over notes, at the cost of retrieval, not of reading every call.
2. **A full-context control for the map step**: the same 8 cross-call questions with all transcripts in
   the prompt (same token cost at 20 calls), to show whether reading call by call beats one big prompt
   on completeness and misattribution, not only on evidence recall.
3. **A second retrieval hop**: let the answer step request more context ("need: the call where an
   engineer reviewed an exported definition") before answering; this fixes q30-type questions.
4. **Entailment check on citations**: a small model checks that each quote supports its claim, not just
   that it exists.
5. **Better eval**: a majority of 3 judge passes per answer (the judge alone moves ~6 of 30 verdicts),
   3–5 repeats of the baseline too, and a blind human-graded subset (about 10 answers, stratified by
   verdict and question type) to measure how often the judge agrees with a person.

### Scaling to thousands of calls

The rule: reading calls is paid for once, at ingestion, not on every question; a question should
cost the same at 20 calls as at 20,000. Measured on the current 20 calls, per question:

| part | now | at thousands of calls | what to do instead |
|---|---|---|---|
| map step (read each candidate call) | ~120K tokens, ~80 s | ~6K tokens × every call: millions of tokens, minutes | per-call notes at ingestion, queried with filters; map only over a shortlist of 20–50 calls (already capped at 25) |
| all vendor claims in one prompt (q11) | 587 claims | tens of thousands, does not fit | a product-fact table: claims clustered by topic and subject with counts (people, calls, last date, hedged); conflicts recorded when a new call is ingested |
| every vendor statement on a topic (q24) | 9 calls on SSO | hundreds per topic | the same table: "SAML SSO: Enterprise, 9 calls / 3 reps; all plans, 1 call, later hedged"; weighing becomes counting |
| catalogue in the planner prompt | 20 lines | does not fit | metadata filters plus fuzzy search over companies and people |
| per-call excerpt quota | 20 calls | thousands of excerpts | quota after filtering, on the top-N calls |
| name check over all transcripts | ms | slow | a name index built at ingestion |
| claim extraction, embeddings | once per call | once per call, incremental | fine as is: cached by content hash |
| citation check, inventory, eval | per answer | per answer | fine as is |

### Production

- **Ingestion**: new calls arrive as events; parse → chunk → embed → extract notes per call,
  idempotent by call id + content hash (the embedding cache already works this way). A proper store
  (Postgres + pgvector or a vector DB) replaces in-memory numpy/BM25, with metadata filters (date,
  segment, rep, stage) in the query.
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
