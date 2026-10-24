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

[full: 1 calls, 5,009 words in context · 2 API calls · 10,881 in / 1,900 out tokens · 9.7s]
[plan 2.0s (176 out) · context 0.0s · answer 7.7s (1,724 out) · check 0.0s]
```

## Setup and run

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env        # then set LLM_API_KEY (an OpenAI key works as is)
uv run callqa index         # checks the index, which is committed (.cache/callqa.db: vendor claims and
                            # per-call notes; .cache/embeddings-*.npy: chunk vectors): seconds; it
                            # re-reads only new or changed calls, or all of them if CHAT_MODEL or
                            # EMBED_MODEL differ from gpt-5.4-mini / text-embedding-3-small
rm -rf .cache && uv run callqa index   # optional: ingest everything from scratch (~2 min)
uv run callqa ask "Which competitors were mentioned, and in what context?"
uv run callqa ask "..." --mode full     # baseline: whole dataset in the prompt
uv run callqa ask "..." --json          # raw result, including the plan and every citation check
uv run callqa ask "..." --across map    # questions across calls: read each call and count (slower)
uv run callqa                           # interactive prompt
uv run pytest                           # offline unit tests (parser, chunking, citation checker, store,
                                        # claims, topic and per-call checks, eval)
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
  │                                 · across calls? which note fields hold the answer?
  │                                 · does it rank or classify the calls ("which prospects…", "which customers…")?
  ├─ 2. context                     vendor-consistency question? → every vendor claim, grouped by topic,
  │                                   + contradictions found by checking each topic on its own (in parallel)
  │                                 candidate calls fit in 12K words? → send whole transcripts
  │                                   (across several calls: + a verdict from reading each call on its own)
  │                                 question across calls? → the turns behind the notes written at ingestion
  │                                   in those fields (+ retrieved excerpts), and the calls with none;
  │                                   comparing kinds of call: the small kinds whole, within 12K words
  │                                 otherwise → hybrid retrieval (BM25 + embeddings, RRF) with a per-call quota
  │                                 product fact? → plus every vendor statement on that topic, from all calls
  │                                 ranks or classifies calls? → plus a verdict from reading each call (≤25)
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
- **Ingestion** (`callqa/store.py`): each call is read once when it is ingested, and the results go
  into one SQLite file. The handler is idempotent by call id and a digest of content, model and prompt
  versions, so an unchanged call costs nothing and a changed one is replaced in one transaction. A
  call is read in parts of ~1,700 words (1–3 per call, overlapping by two turns), all in parallel,
  with two kinds of read per part, every quote checked by the citation checker:
  - **vendor claims** (`callqa/claims.py`): what OrbitFlow staff assert about the product under 12
    topics, kept only if said by vendor staff (749 in the committed index, one per turn and topic, merged
    from two extraction passes at low reasoning; see *Known limitations*). Used whole for consistency questions, by
    topic for product-fact questions ("Is SSO on Growth?");
  - **notes** (`callqa/notes.py`): the call's points under 10 fields (needs, pains, objections,
    competitors, integrations, pricing, decision process, buying signals, outcome, how the team ran
    the call), each tied to a turn and embedded (1,441 notes, medium reasoning). Questions across calls
    select notes by field and similarity, up to 250 turns, instead of reading the calls.
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
   the question, so similarity search cannot find it. Putting
   every vendor statement on a topic side by side makes a contradiction visible: "SSO is on all plans"
   (one AE) next to statements in nine other calls that SAML SSO is Enterprise. The planner switches to this
   context only for questions about the vendor's consistency. Comparing ~550 statements in one pass
   was not reliable with low reasoning (the "completely no-code" contradiction was found in 3 of 5
   replays on the same context), so each of the 12 topics is first checked for contradictions by its
   own small call, in parallel (`callqa/conflicts.py`, ~5 s), and the answer step weighs what they
   found: 5 of 5 asks found it, 3 of 3 judged "yes".
   The same table answers product-fact questions: retrieval gives the passages most similar to the
   question, so a fact stated in nine calls and contradicted in one can reach the model as one statement
   against one, and it cannot weigh what it does not see. For a question on one to three product topics
   the answer step also gets every vendor statement on them. A conflict is then reported with both
   sides cited *and* with the better-supported side and the reason, or "cannot tell"; confidence stays
   at most medium.
7. **Read calls when they arrive, not when a question is asked.** Questions across calls need turns
   from every call, and retrieval reached about half of them. Reading every candidate call per
   question (a map step, available as `--across map`) does that too, but costs ~139K tokens per such
   question at 20 calls and grows with every call. Notes written at ingestion keep most of the gain
   for ~26K tokens, and the cost per question does not grow with the corpus.
8. **One OpenAI-compatible client.** It runs on OpenAI or Azure by changing env vars; no framework.

## Assumptions

- Transcripts are the source of truth; the manifest/header is metadata and can be wrong. Speaker
  attribution is correct (stated in the dataset README), so the speaker's side comes from the participant list.
- Users are sales managers. They want a short answer plus the quotes to check it, more than a long essay.
- English only, a few dozen calls, questions one at a time (no chat history).

## Evaluation

Details, the full results table and three worked examples: [`eval/EVALUATION.md`](eval/EVALUATION.md).

### Run it

```bash
uv run python eval/run_eval.py                    # pipeline, all 30 questions (~2 min)
uv run python eval/run_eval.py --mode full        # baseline: whole dataset in the prompt
uv run python eval/run_eval.py --only q11,q24     # a subset
uv run python eval/run_eval.py --regrade eval/results/<run>.json   # re-check and re-judge saved answers, no generation
uv run python eval/run_eval.py --no-judge         # deterministic metrics only, no Claude Code needed
uv run python eval/run_eval.py --replay eval/results/<run>.json --only q05   # new answer on the saved context
uv run python eval/compare.py --auto A1.json A2.json A3.json --full F.json   # per-question comparison
uv run python eval/bench_ingest.py                # ingestion: one call read whole vs in parts
```

Questions are answered 4 at a time (`--workers`; the latency reported is under that load) and judged
8 at a time in a separate pool (`--judge-workers`), so answering does not wait for the judge.

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

The current code, 29 headline questions (q30 is a bonus), `gpt-5.4-mini` answering, Claude Opus
judging, 24.10. Both pipeline runs used the index committed to the repo, so
`uv run python eval/run_eval.py` on a fresh clone starts from the same claims and notes.
Which file in `eval/results/` is which: [`eval/results/README.md`](eval/results/README.md).

| | pipeline, run 1 | pipeline, run 2 | whole dataset in prompt (`full`) |
|---|---|---|---|
| run | `…-154829-auto-parts` | `…-154956-auto-parts` | `…-094601-full-fresh-clone` |
| correct: yes / partly / no | **16 / 13 / 0** | **17 / 12 / 0** | 13 / 14 / 2 |
| core / atomic fact recall | 0.77 / 0.66 | 0.79 / 0.67 | 0.73 / 0.61 |
| context recall · evidence recall | 1.00 · 0.89 | 1.00 · 0.90 | 1.00 · 1.00 (by construction) |
| citation validity | 1.00 | 0.99 | 0.97 |
| failed citations: not found · wrong call · wrong speaker | 0 · 1 · 1 | 0 · 4 · 0 | 4 · 10 · 3 |
| abstention: right on unanswerable · false on answerable | 5/5 · 0 of 24 | 5/5 · 0 of 24 | 5/5 · 0 of 24 |
| penalties hit | 1 | 0 | 3 |
| prompt tokens per question | 34K | 34K | 123K |
| latency mean / p95, 4 questions in parallel | 9.9 / 23.7 s | 10.2 / 22.6 s | 11.3 / 38.5 s |
| first failed step | answer 7, retrieval 5 | answer 8, retrieval 3, attribution 2 | answer 15, attribution 4 |

Per question (`eval/results/comparison.md`): the two pipeline runs disagree on 7 of 30, all on the
yes/partly line. Two runs of the same code on the previous index gave 20 and 15 "yes": that spread
is the judge and answer noise this eval measures, so compare per question, not the totals. The
baseline is worse than both runs on q07 and q11 and better on q30, where it sees every call.

What I take from it:

- **The pipeline is ahead of the brute-force baseline at about 1/4 of the tokens.** The yes/partly
  gap (16–17 vs 13) is about the size of the judge's own noise (re-judging the same answers moved
  6 of 30 verdicts), so the safe claim is "at least as good". Two differences are not noise: the
  baseline attaches far more quotes to the wrong call or speaker (17 failed citations vs 2–4), and
  on q24 ("Is SSO on Growth?") it concluded "yes, all plans" from one AE against nine calls that say
  Enterprise, the error the vendor-statement table and the weighing rules exist to prevent (example 1
  in `eval/EVALUATION.md`).
- **Two different bottlenecks.** Questions about one or a few calls get whole transcripts, evidence
  recall is ~1.0, and the misses are in the answer step (details left out: q13–q15, q18). Questions
  across all calls get the notes written at ingestion, which reach 0.75–0.77 of the evidence turns on
  the 7 such questions (from ~0.4 on q05 to 0.93 on q09), and a pattern that only shows across calls is not in
  any one call's notes.
- **Unanswerable and near-miss questions work**: Kestrel's ERP, ISO 27001, the Enterprise list price.
- **Fixed by splitting one pass into small parallel checks.** One pass of the answer step over many
  calls or statements dropped a call or a case. q11 (vendor contradictions) found only some of them;
  a check per claim topic makes it "yes" in both runs. q10 ("which cold calls produced a follow-up?")
  said "all five" although Trafford's Yvonne said "I won't read it"; q07 ("which prospects seem most
  likely to purchase?") left Acme out and put BrightPath on top without its BAA gate; q02 listed
  BrightPath and Greenline among the Salesforce customers. A verdict per call, read on its own, makes
  q10, q02 and q28 "yes" in both runs and q07 "yes" in 6 of the 13 runs since (it was "partly" or
  "no" before).
- **Improved, not fixed**: q09 ("how do renewals differ from new business?") had a third of its
  evidence in context, because one note field was chosen and the renewal calls were seen only as
  notes. The planner now takes every field an answer can sit in, and a comparison sends the small
  kinds of call whole (the 3 renewals and 5 cold calls, ~11.5K words): evidence recall 0.93, core
  recall 0.2 → 0.4–1.0, "yes" in one of the two current runs; when "partly", the answer stays general
  (the 7% uplift, the jointly written pilot criteria). q05 ("which capabilities matter most to prospects?") missed customer
  questions such as "Can we export audit logs to our own SIEM?", which the notes did not record; the
  notes prompt now records them as needs (10 of the 14 missed turns are noted now, 0 before):
  evidence recall 0.42 → 0.38–0.54 (it moves with the index and the fields the planner picks);
  "partly" in every full run (core recall 0.5–0.67) and in the latest run of the 11 example
  questions, "yes" in the two before. Of its missed turns, most are noted but ranked below the budget:
  "Can the queue be owned by a team?", asked in 5 of 10 calls, is not similar to the abstract
  question. Ranking notes by the planner's search queries too, with a budget of 350 turns, raised its
  evidence recall on saved plans (0.43 → 0.72) but not in live runs (0.33–0.50), because the
  planner's queries differ from run to run, and q07 fell to "no" twice (`…-query-rank`); not kept.
  A bonus for points that recur across calls did not help either. What does work is reading each
  call for the question and counting across calls (`--across map`, below): evidence recall 1.0 and
  core recall 0.50–0.83 on q05, "yes" in 1 of 3 runs, but ~45 s and ~150K tokens against 15–18 s and
  ~25K, so it is an option, not the default (`…-q05-map-tally`).
- **Known failures**: q18 ("are the lead scores reliable?") once concluded flatly that they are not,
  from one person's impression. q21 once took Sarah's rhetorical "costs a hundred thousand a year" over the £80K account value, a
  trap noted in `eval/GOLD_NOTES.md`. q30 (bonus) needs a second retrieval hop and is declined.

### Options for questions across calls

`--across` picks how a question across calls is answered; measured on the same eval, with
`ANSWER_EFFORT=medium` (the retrieval run was also without the turn inventory):

| | `retrieval` | `map` (read each call per question) | `notes` (default, read at ingestion) |
|---|---|---|---|
| run | `…-214420-auto-diagnostics` | `…-224354-auto-map` | `…-231007-auto-notes` |
| yes / partly / no (29) | 14 / 15 / 0 | 20 / 9 / 0 | 16 / 13 / 0 |
| the 7 cross-call questions: "yes" | 3 | 4 | 5 |
| evidence recall: all / the 7 | 0.82 / 0.48 | 0.94 / 0.89 | 0.86 / 0.65 |
| core fact recall: all / the 7 | 0.70 / 0.66 | 0.81 / 0.84 | 0.78 / 0.75 |
| prompt tokens per question: mean / the 7 | 14.5K / 18K | 47K / 139K | 17K / 26K |

For questions about what matters most or comes up most across calls (the planner's
`pooled_across_calls`), `map` also counts: one small call groups the points found in each call into
items with the calls behind them, and the answer gets them ordered by the number of calls ("raised in
5 of 10 calls"), counted in code. The calls are read in parts, all at once (~35 s for 10 calls). The
grouping is still coarser than asked ("security, compliance and access controls" rather than "export
audit logs to our own SIEM"), which is what q05 loses on when it is "partly".

The map step reaches the most evidence but reads every candidate call on every question, so it is
capped at 25 calls (*Scaling to thousands of calls*). Notes keep most of the gain at a fifth of the
tokens, and their cost does not grow with the corpus.

The gold set was drafted by an LLM, every citation checked against the source, and the 19 disputed
points decided by a human (`eval/review/`).

## Speed

Targets for a sales manager waiting on an answer with evidence: something on screen in under 2 s,
a question about one call in ≤ 8 s, a question across calls in ≤ 20 s, p95 ≤ 30 s.

Latency follows the tokens the model *generates* in the answer step, at roughly 180 tokens/s;
context size, retrieval, note selection and citation checks are each under a second. The breakdown
is printed under every answer (`[plan 2.0s (176 out) · context 0.0s · answer 7.7s (1,724 out) · check
0.0s]`), is in `--json` → `steps`, and the eval reports p50/p95 and the answer step's output tokens.

| one question at a time | latency |
|---|---|
| one call, whole transcript ("What was Verity paying?") | 5.5 s |
| product fact, excerpts + vendor statements ("SSO on Growth?") | 10.2 s |
| across calls, ingestion notes ("Why do prospects hesitate?") | 18.9 s |
| ingestion of all 20 calls from scratch (`rm -rf .cache && callqa index`) | 80–130 s |
| across a few whole calls, a verdict per call + answer ("Which cold calls produced a follow-up?") | 13–16 s |
| a verdict on each of 10–20 calls + notes ("Which prospects seem most likely to purchase?") | 10–31 s |
| comparison: small kinds of call whole + notes ("How do renewals differ from new business?") | ~15–20 s |
| vendor contradictions, 12 topic checks + answer ("Has the vendor given inconsistent answers?") | 15–23 s |
| the task's 11 example questions, one at a time (`…-172455-auto-examples-low`): mean / median / slowest | 15.0 / 15.2 / 21.1 s |
| full eval, 4 in parallel (`…-154829/154956-auto-parts`): mean / p50 / p95 | 9.9–10.2 / 7.7–8.4 / 22.6–23.7 s |

What keeps it there:

- **Low reasoning in the answer step** (`ANSWER_EFFORT`, default `low`). The inventory of relevant
  turns, written before the answer, does the work extra reasoning would do. `ANSWER_EFFORT=medium`
  is ~4× slower (63.8 s mean on the 11 examples, slowest 197 s, `…-144652-auto-examples-medium`)
  with no better verdicts: 7 / 4 / 0 against 8 / 3 / 0 at `low` on the same (previous) index; 9 / 2 / 0
  at `low` on the current one. q07, q08 and q09 are "partly" at
  both, so what they miss is not fixed by more reasoning.
- **The inventory is call and timestamp only**: every token in it is generated before the answer.
- **Calls are read at ingestion**, so a question across calls selects notes instead of reading calls.
- **Static text first, the question last**, in every prompt (system prompt, then the catalogue, the
  transcript or the topic's statements, then the question), so the provider's prefix cache serves the
  shared part: 40% of all prompt tokens in a full eval came from the cache
  (`…-180924-auto-prompt-cache`), billed at a discount. A call read for several questions (per-call
  verdicts on the same 10 prospect calls for q02, q07, q28) is paid in full once.
- **A duplicate for a lost request at question time**: a planner, verdict, topic-check or answer call
  with no answer after 45 s (answer step p99 21 s, maximum 28 s over 101 answers) is sent again and
  the first answer wins, so a request the provider never answers does not hold the question for the
  120 s timeout (one question took 135 s instead of 12). Off for `ANSWER_EFFORT=medium`, whose
  answers take a minute.
- **Ingestion in parts, in parallel**: every call is split into parts of ~1,700 words and every
  part of every call is read at once (two claims passes and a notes pass each, ≤180 requests, well
  under the deployment's 1M tokens and 1,000 requests a minute). Ingestion waits for its slowest
  request, and one request over a whole ~5K-word call generated up to 40K tokens, took 1.5–3 min and
  sometimes hung (12.8 min for one fresh ingestion on 24.10). Parts finish in 20–100 s. Two causes
  of the hangs, found with a request log and thread dumps over repeated ingestions (`callqa/llm.py`):
  - **TLS handshakes one at a time.** The HTTP client's default SSL context (`truststore`) holds one
    lock for a whole handshake, network round trips included, so the ~180 connections opened at once
    shook hands in turn: connections queued for ~10 s were closed by the server, and one stalled
    handshake held every other thread (100+ threads waiting, sockets in CLOSE_WAIT, 13 min). A plain
    `ssl` context with `certifi` shakes hands in parallel: 0 handshake failures since, against 30–70
    per ingestion.
  - **Requests the provider never answers**, ~4% of them (also with separate clients and tiny
    prompts): no response until the read timeout. An extraction with no answer after 60 s gets a
    duplicate and the first answer wins; embeddings, which answer in under 2 s, time out after 20 s.

  Four fresh ingestions with both fixes: 80–129 s (before: 92–413 s). Timeouts: 180 s for ingestion
  calls, 120 s for question-time calls.

  Measured on the longest call (CALL-004, 4,904 words, 3 parts), 2 repeats, variants interleaved
  (`uv run python eval/bench_ingest.py`):

  | read | reasoning: claims / notes | requests | time for the call | output tokens | claims | notes |
  |---|---|---|---|---|---|---|
  | whole call | medium / medium | 3 | 98–116 s | 41K | 38–41 | 60–93 |
  | parts | low / low | 9 | 21–24 s | 21K | 46–47 | 105–117 |
  | **parts (used)** | **low / medium** | 9 | 63–79 s | 48K | 52–54 | 111–121 |

  All-low is the fastest, but its notes, though more numerous, rank worse against questions: on the
  7 questions across calls the answer got 0.74 of the evidence turns from an all-low index, 0.79
  with notes at medium, 0.77 from the whole-call index (same saved plans, `NOTE_BUDGET` 250 turns).
  Claims lose nothing at low (14–15 of the 15 vendor statements behind the gold contradictions in
  every index). Over all 20 calls: 80–130 s from scratch, against ~2–3 min for whole calls when no
  request hangs. The eval verdicts are within noise of the whole-call index (16 / 13 / 0 and
  17 / 12 / 0, against 20 / 9 / 0 and 15 / 13 / 1).
- **Progress on screen**: the CLI prints each step as it starts (`planning` → `plan: across question
  over all calls; note fields: …` → `context: notes, 10 calls …; writing the answer`), so the first
  output arrives in well under 2 s even when the answer takes 15 s.

Not done yet, in order of expected gain: stream the answer text and check each citation as it
arrives (the first claim on screen in 2–3 s instead of ~13 s on questions across calls; the total
does not change: the answer's own output tokens set it, reasoning at `low` is 20–30 tokens); run the
planner on a smaller model (~1 s per question; no smaller model is deployed on the Azure resource
used here) and embed the question while it plans; cache answers by normalised question and data
version; and
provisioned throughput, since the spread under load (8 s alone vs up to 21 s p95 with 4 in parallel)
is the provider's.

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
- **Exhaustive lists**: "which customers mentioned X" uses the notes written at ingestion, which
  reach 0.75–0.77 of the supporting turns on the cross-call questions (evidence recall, q05 lowest
  at ~0.4); a call that mentions X once, in passing, can have no note on it. The answer is shown which calls have no
  notes in the relevant fields, but "this list is complete" is still only as good as the notes.
  `--across map` reads every candidate call for the question and reaches ~0.9, at ~5× the tokens.
- **Judgement questions** ("most likely to buy") get a verdict per call, each call read whole on its
  own, but there is no scoring rubric behind the ranking: it is one model's read of the signals, and
  q07 is "yes" in 6 of 13 runs and "partly" in the rest.
- **The checker verifies that the quote exists and that the cited person said it, not that it supports
  the claim.** A real, correctly attributed quote attached to an overstated claim passes. The judge catches some of this in evaluation, but nothing does at runtime.
- **Header vs body disagreements** are only surfaced when the question touches them.
- **Ingestion is not deterministic.** Fresh indexes of the same 20 calls differ: in one, a single
  claims pass left out "That's fine, it's completely no-code", so q11 could not find that
  contradiction on that index. Claims are now extracted twice and merged (14 or 15 of the 15 vendor
  statements behind the contradictions in `eval/GOLD_NOTES.md` across three fresh indexes, against 13
  with one pass; the usual miss is Leo offering enablement free), an empty extraction is retried, and the index behind the headline runs is committed, so a fresh clone
  answers from the same claims and notes (inspectable in `.cache/callqa.db`).
- **The gold set is small (30) and LLM-drafted** (see `eval/EVALUATION.md`). The judge is
  from a different vendor than the answering model, but it is still an LLM and it is noisy on the
  yes/partly boundary.
- Single-turn, English, no auth. The transcripts are sent to an external LLM API.

## With more time

With another day:

1. **A product-fact table at ingestion**: vendor claims clustered by topic and subject with counts
   (people, calls, last date, hedged), and conflicts recorded when a call arrives. q11 and q24 then
   read a table instead of putting every claim on a topic into the prompt (see the scaling table).
2. **A full-context control for the map step**: the same 7 cross-call questions with all transcripts in
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
| map step (read each candidate call) | ~139K tokens per cross-call question | ~6K tokens × every call: millions of tokens, minutes | **done**: notes at ingestion (default, ~26K tokens per cross-call question, most of the map step's gain); map kept as `--across map`, capped at 25 calls |
| verdict per call, for questions that rank or classify calls (q02, q07, q28) | 100–150K tokens per such question at 10–20 calls | linear in the number of candidate calls | capped at 25 candidates; at scale, shortlist calls by their notes first and read only those |
| notes at ingestion | ~1,400 notes, the 250 best turns by field and similarity | grows with calls; the answer still gets ≤250 turns | add metadata filters and a shortlist of calls before ranking notes |
| all vendor claims, checked topic by topic in 12 parallel calls (q11) | ~550 claims, ~45 per topic on average | tens of thousands, a topic no longer fits one call | a product-fact table: claims clustered by topic and subject with counts (people, calls, last date, hedged); conflicts recorded when a new call is ingested |
| every vendor statement on a topic (q24) | 9 calls on SSO | hundreds per topic | the same table: "SAML SSO: Enterprise, 9 calls / 3 reps; all plans, 1 call, later hedged"; weighing becomes counting |
| catalogue in the planner prompt | 20 lines | does not fit | metadata filters plus fuzzy search over companies and people |
| per-call excerpt quota | 20 calls | thousands of excerpts | quota after filtering, on the top-N calls |
| name check over all transcripts | ms | slow | a name index built at ingestion |
| claim extraction, embeddings | once per call | once per call, incremental | fine as is: cached by content hash |
| citation check, inventory, eval | per answer | per answer | fine as is |

### Production

- **Ingestion**: new calls arrive as events and trigger `Store.ingest`, which is already idempotent
  by call id + content hash and writes each call in one transaction. At scale the SQLite file becomes
  Postgres + pgvector (same tables), the chunk embeddings (now an `.npy` cache) and BM25 (now
  rebuilt in memory at start-up) move into it, and queries get metadata filters (date, segment, rep, stage).
- **Security and privacy**: transcripts hold customer PII and commercial terms. That means
  tenant/role-based access applied as a retrieval filter (a rep sees their own accounts, a manager
  their team's), a region-pinned LLM endpoint with no training on data and zero/limited retention,
  PII redaction where the use case allows, audit logs of questions and the turns they surfaced, and
  prompt-injection hygiene (transcripts are untrusted input: a customer can say "ignore previous
  instructions" on a call).
- **Operations**: run the eval in CI on prompt/model changes, log every question with its plan,
  context and citation checks, collect user feedback (thumbs down + "wrong citation"), and watch
  citation validity and abstention rate as live quality signals.
- **Cost/latency**: see *Speed*; in production also per-tenant rate limits and a latency budget per
  step, alerting on p95.
