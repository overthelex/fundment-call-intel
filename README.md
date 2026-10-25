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
rm -rf .cache && uv run callqa index   # optional: ingest everything from scratch (2–4 min)
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
                                    a call its own verdict counts but the answer drops → answered once more
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

## Data model

What is stored, and what passes between the steps (pydantic models and dataclasses in `callqa/`):

```
transcript  Call (header metadata, participants, kind) → Turn (call_id, idx, ts, speaker, side, text, file line)
index       Chunk: ~180 words of consecutive turns of one call, 343 of them · BM25, in memory
            chunk vectors: .cache/embeddings-<digest>.npy, 343 × 1536
store       .cache/callqa.db (SQLite)
              calls  (call_id, digest, company, category, stage, date)              20 rows
              claims (call_id, turn_idx, topic, statement, speaker, quote)          749 rows, 12 topics
              notes  (call_id, turn_idx, field, point, speaker, quote, vector)    1,441 rows, 10 fields
question    Plan → Context → Answer → CitationCheck for each quote → Result
eval        questions.yaml (gold calls, facts as core + details, evidence turns) → Judgement per fact
```

- **The turn is the unit of evidence.** Every stored record points at `(call_id, turn_idx)`, and the
  turn's file line gives the `file:line` link. Header metadata are turns too, so a company size can be
  cited and checked like speech.
- **What the model writes is not what is stored.** Every reader returns timestamp, speaker and a
  verbatim quote; the citation checker resolves them to a turn, and the record is kept with its
  `turn_idx` only if the quote is in that turn: notes (`CallNote` → `StoredNote`), vendor claims
  (`VendorClaim` → `StoredClaim`), per-call verdicts (`CallVerdict` → `Finding`) and contradictions
  (`TopicConflict` → `FoundConflict`, dropped if either side is left without a verified quote).
- **`digest`** hashes the call's text, both model names and the prompt versions, so re-indexing reads
  only what changed, and each call's rows are replaced in one transaction.
- **Notes choose turns; the answer sees turns.** Questions across calls filter notes by the planner's
  fields and rank them by similarity (each note embedded as `"field: point"`), up to 250 distinct
  turns. The answer step gets those turns from the transcript, not the notes, so what it quotes is
  what was said.
- **`Plan`**: call ids, call kinds, specific or across, search queries, notes on names, and the
  routing flags (vendor consistency, product topics, note fields, a verdict per call, counting across
  calls). **`Context`**: the mode and every turn the answer saw; the eval saves it, which is what
  evidence recall and `--replay` use.
- **`Answer`**: `relevant_turns` (call and timestamp only, written first), `summary`, `claims` with
  citations, `conflicts` with the better-supported side and why, `not_found`, `confidence`.
  **`CitationCheck`**: exact, shifted, fuzzy, wrong_speaker, wrong_call, not_found or unknown_call.
  **`Result`** adds the plan, context, warnings, and seconds and tokens per step (`--json`).

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
   context only for questions about the vendor's consistency. One pass over all ~550 statements stops
   after the clearest contradictions, so each of the 12 topics is checked by its own small call, twice
   in parallel (one check finds a given contradiction about 7 times in 10), and the pairs are merged
   (`callqa/conflicts.py`); the answer step weighs what they found.
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
| run | `…-211125-auto-final` | `…-211257-auto-final` | `…-094601-full-fresh-clone` |
| correct: yes / partly / no | **19 / 10 / 0** | **19 / 10 / 0** | 13 / 14 / 2 |
| core / atomic fact recall | 0.78 / 0.68 | 0.76 / 0.66 | 0.73 / 0.61 |
| context recall · evidence recall | 1.00 · 0.90 | 1.00 · 0.90 | 1.00 · 1.00 (by construction) |
| citation validity | 0.99 | 1.00 | 0.97 |
| failed citations: not found · wrong call · wrong speaker | 1 · 4 · 2 | 0 · 1 · 1 | 4 · 10 · 3 |
| abstention: right on unanswerable · false on answerable | 4/5 · 0 of 24 | 4/5 · 0 of 24 | 5/5 · 0 of 24 |
| penalties hit | 0 | 0 | 3 |
| prompt tokens per question (from the prompt cache) | 33K (23%) | 37K (34%) | 123K |
| latency mean / p95, 4 questions in parallel | 10.4 / 23.1 s | 10.7 / 22.9 s | 11.3 / 38.5 s |
| first failed step | retrieval 5, answer 4, attribution 1, abstention 1 | answer 6, retrieval 4, attribution 1, abstention 1 | answer 15, attribution 4 |

Per question (`eval/results/comparison.md`): the two runs disagree on 6 of 30 (q03, q08, q09, q16,
q24, q26), all on the yes/partly line; earlier runs of nearly the same code gave between 15 and 20
"yes", which is the judge and answer noise this eval measures, so compare per question, not totals.
The baseline is worse than both runs on q07, q11, q12, q15 and q19 and better on q17 and q30 (the
bonus, where it sees every call). The two abstention misses (q29 in run 1, q26 in run 2) are judged
"yes" and do say the data has no answer; the judge's abstention flag disagrees with its own verdict.

What I take from it:

- **The pipeline is at least as good as the brute-force baseline, at about a quarter of the
  tokens.** The gap in "yes" is about the size of the judge's own noise (re-judging the same answers
  moved 6 of 30 verdicts), so "at least as good" is the safe claim. Two differences are not noise: the
  baseline attaches far more quotes to the wrong call or speaker (17 failed citations vs 2–7), and on q24 ("Is SSO
  on Growth?") it concluded "yes, all plans" from one AE against nine calls that say Enterprise, the
  error the vendor-statement table and the weighing rules exist to prevent (example 1 in
  `eval/EVALUATION.md`).
- **Two bottlenecks.** Questions about one or a few calls get whole transcripts, evidence recall is
  ~1.0, and the misses are details the answer leaves out (q13–q15, q18). Questions across all calls
  get the notes written at ingestion, which reach about three quarters of the evidence turns (q05
  lowest, ~0.4), and a pattern that only shows across calls is not in any one call's notes.
- **One pass over many calls or statements drops one; small parallel checks do not.** A single answer
  step over five cold calls said "all five" produced a follow-up (q10), left Acme out of the likely
  buyers (q07), listed calls that never mentioned Salesforce (q02), and found only some of the vendor's
  contradictions (q11). Hence a verdict per call, a check per claim topic, and a coverage check in
  code; q02, q10, q11 and q28 are "yes" in nearly every run.
- **Unanswerable and near-miss questions work**: Kestrel's ERP, ISO 27001, the Enterprise list price.
- **Open**: q05 ("which capabilities matter most?") is a count over calls that note similarity
  ranks poorly; `--across map` closes it (evidence recall 1.0) at ~45 s and ~150K tokens, so it is
  an option, not the default. q07 ("most likely to buy?") is a judgement with no scoring rubric
  behind it, "yes" in about half the runs. q09 ("renewals vs new business") has its evidence (0.93)
  but the answer stays general in some runs. q30 (bonus) needs a second retrieval hop and is declined.
  What was tried for each, including what did not hold up in live runs, is in `eval/EVALUATION.md`.

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
| ingestion of all 20 calls from scratch (`rm -rf .cache && callqa index`) | 80–260 s |
| across a few whole calls, a verdict per call + answer ("Which cold calls produced a follow-up?") | 13–16 s |
| a verdict on each of 10–20 calls + notes ("Which prospects seem most likely to purchase?") | 10–31 s |
| comparison: small kinds of call whole + notes ("How do renewals differ from new business?") | ~15–20 s |
| vendor contradictions, 12 topics checked twice + answer ("Has the vendor given inconsistent answers?") | 15–37 s |
| the task's 11 example questions, one at a time (`…-205327-auto-examples-low`): mean / median / slowest | 15.7 / 14.4 / 22.3 s |
| full eval, 4 in parallel (`…-211125/211257-auto-final`): mean / p50 / p95 | 10.4–10.7 / 8.0–9.8 / ~23 s |

What keeps it there:

- **Low reasoning in the answer step** (`ANSWER_EFFORT`, default `low`). The inventory of relevant
  turns, written before the answer, does the work extra reasoning would do: `medium` is ~4× slower on
  the 11 example questions (63.8 s mean) with no better verdicts (7 / 4 / 0 against 8 / 3 / 0).
- **The inventory is call and timestamp only**: every token in it is generated before the answer.
- **Calls are read at ingestion**, so a question across calls selects notes instead of reading calls.
- **Static text first, the question last** in every prompt, so the provider's prefix cache serves
  the shared part (23–40% of prompt tokens in a full eval, billed at a discount): a call read for several
  questions, like the 10 prospect calls behind q02, q07 and q28, is paid in full once.
- **A duplicate for a request the provider never answers** (~4% of them): a planner or answer call
  with no answer after 45 s (answer p99 21 s), a per-call verdict or topic check after 20 s (max 7.9 s
  and 13.6 s), is sent again and the first answer wins, instead of waiting out the 120 s timeout.
- **Ingestion in parts, in parallel**: every call is split into parts of ~1,700 words, and every
  part of every call is read at once (claims at low reasoning, notes at medium). One request over a
  whole ~5K-word call took 1.5–3 min; parts take 20–100 s, and a fresh ingestion of all 20 calls
  80–260 s (`eval/bench_ingest.py`; 80–130 s on 24.10 and 190–260 s on 25.10, with the same code).
  The client uses a plain `ssl` context, because the default one (`truststore`) shakes hands one
  connection at a time under one lock, and an extraction with no answer after 60 s gets a duplicate. The benchmark, and how both were found: `eval/EVALUATION.md`,
  *Engineering notes*.
- **Progress on screen**: the CLI prints each step as it starts (`planning` → `plan: across question
  over all calls; note fields: …` → `context: notes, 10 calls …; writing the answer`), so the first
  output arrives in well under 2 s even when the answer takes 15 s.

**Cost**, at list prices for `gpt-5.4-mini` ($0.75 / $4.50 per 1M input / output tokens, cached input
at a tenth): ~$0.03 for a typical question, $0.11–0.14 for one that reads 10–20 calls on their own
(q02, q07, q11), ~$0.07 mean over the 11 example questions; the baseline with every transcript in
the prompt is ~$0.10 for any question.

Not done yet, in order of expected gain: stream the answer and check each citation as it arrives
(the summary on screen in ~6 s instead of ~11 s; the total does not change, since the answer's own
output tokens set it); run the planner on a smaller model (~1 s per question; none is deployed on the
Azure resource used here); cache answers by normalised question and data version; provisioned
throughput, since the spread under load is the provider's.

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
  reach about three quarters of the supporting turns on the cross-call questions (evidence recall,
  q05 lowest at ~0.4); a call that mentions X once, in passing, can have no note on it. The answer is shown which calls have no
  notes in the relevant fields, but "this list is complete" is still only as good as the notes.
  `--across map` reads every candidate call for the question and reaches ~0.9, at ~5× the tokens.
- **Judgement questions** ("most likely to buy") get a verdict per call, each call read whole on its
  own, but there is no scoring rubric behind the ranking: it is one model's read of the signals, and
  q07 is "yes" in about half the runs and "partly" or "no" in the rest.
- **The checker verifies that the quote exists and that the cited person said it, not that it supports
  the claim.** A real, correctly attributed quote attached to an overstated claim passes. The judge catches some of this in evaluation, but nothing does at runtime.
- **Header vs body disagreements** are only surfaced when the question touches them.
- **Ingestion is not deterministic.** Fresh indexes of the same 20 calls differ, and a single claims
  pass can miss a statement ("That's fine, it's completely no-code"). Claims are extracted twice and
  merged (14 or 15 of the 15 vendor statements behind the gold contradictions in every fresh index), an
  empty extraction is retried, and the index behind the headline runs is committed, so a fresh clone
  answers from the same claims and notes (inspectable in `.cache/callqa.db`).
- **The gold set is small (30) and LLM-drafted** (see `eval/EVALUATION.md`). The judge is
  from a different vendor than the answering model, but it is still an LLM and it is noisy on the
  yes/partly boundary.
- Single-turn, English, no auth. The transcripts are sent to an external LLM API.

## With more time

With another day:

1. **A product-fact table at ingestion**: vendor claims clustered by topic and subject with counts
   (people, calls, last date, hedged), and conflicts recorded when a call arrives. q11 and q24 then
   read a table instead of putting every claim on a topic into the prompt (design sketch below).
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

### Design sketch: the product-fact table

Not built: at 20 calls q11 and q24 are already "yes" in nearly every run, and the table pays off when
the vendor's statements no longer fit one check per topic. How it would work:

- **Rows.** A fact is (topic, subject, value): ("SSO, SCIM and identity", "SAML SSO", "Enterprise
  only"). Each fact keeps its statements (call, turn, speaker, quote, date), so its counts are derived:
  calls, distinct vendor staff, last date, and whether a later statement by the same person hedged or
  corrected it.
- **Update when a call is ingested.** Each new vendor claim is matched against the facts on its
  topic: same subject and value adds a statement; same subject, different value adds a fact and
  records a conflict between the two; a new subject adds a fact. Matching is an embedding shortlist
  plus one small LLM call per claim ("same subject? same value?"), so the work per call is constant
  however many calls came before. The quotes go through the citation checker, as now.
- **Reads.** q11 reads the recorded conflicts instead of checking every statement on every topic:
  "SAML SSO: Enterprise only, 9 calls / 3 staff; all plans, 1 call (Alastair, later 'fairly sure, I'll
  confirm')". q24 reads the facts on one subject, and weighing becomes counting. Both stay cited,
  since every count points at its statements.
- **Risks.** Two facts merged that are not the same (SSO vs SAML SSO), or one fact split in two so a
  conflict is never recorded; matching is non-deterministic, as the per-topic checks were (7 of 10
  for one check). Guard: rebuild the table from the stored claims and compare, and keep the per-topic
  check as an audit that runs nightly, not per question.

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
- **A service, not a CLI**: an HTTP API with the answer streamed and each claim's citation check sent
  as it lands, behind the company's SSO; a UI where every quote opens the call recording at that
  second, since a checkable quote is the product.
- **Transcript quality at the door**: real transcripts come from speech recognition, with misheard
  words and swapped speakers. The side of a speaker (vendor or customer) decides whether a sentence
  is a vendor claim, so ingestion should flag calls whose speaker labels look wrong (a vendor name on
  the customer side, one speaker for most of the call) before they feed the claims and notes.
- **A second provider and pinned models**: a fallback model or provider when the first fails or
  stops answering (here ~4% of requests went unanswered), a pinned model version, and a model upgrade
  only after the eval passes; a prompt change re-reads the calls in the background, which the digest
  of prompt versions in `Store` already triggers.
